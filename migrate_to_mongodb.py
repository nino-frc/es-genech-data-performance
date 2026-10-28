"""
Script de Synchronisation et Protection MongoDB Atlas - MatchDay Analytics
Architecture Résiliente (Fail-Safe & Upsert Intelligent) :
- Élimination des drop() destructifs
- Contrôle de cohérence : Ne synchronise JAMAIS si le scraping a produit des données vides/anormales
- Mode Upsert sélectif : Les champs 'None' ou 'Donnée FFF indisponible' n'écrasent JAMAIS les données saines précédentes
"""

import os
import json
import sqlite3
import hashlib
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

from data_cleaner import anonymize_player_name, is_first_team_eligible

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("AtlasSyncProtection")

BASE_DIR = os.path.dirname(__file__)
GENECH_DB = os.path.join(BASE_DIR, "genech_performance.db")
EXPORT_DIR = os.path.join(BASE_DIR, "exports_mongodb")
os.makedirs(EXPORT_DIR, exist_ok=True)

MONGODB_URI = os.getenv("MONGODB_URI", "")
DB_NAME = os.getenv("MONGODB_DB_NAME", "matchday_db")

def generate_hash_id(value: str) -> str:
    """Génère un identifiant unique déterministe."""
    return hashlib.md5(value.encode('utf-8')).hexdigest()[:24]

def clean_doc_for_upsert(doc: dict) -> dict:
    """
    Filtre les champs 'None' ou 'Donnée FFF indisponible' pour le $set MongoDB.
    Garantit qu'une indisponibilité temporaire n'écrase pas une donnée saine déjà en base.
    """
    cleaned = {}
    for k, v in doc.items():
        if k == "_id":
            continue
        if v is None or v == "Donnée FFF indisponible":
            continue
        if isinstance(v, dict):
            sub_cleaned = clean_doc_for_upsert(v)
            if sub_cleaned:
                cleaned[k] = sub_cleaned
        else:
            cleaned[k] = v
    return cleaned

def sync_to_mongodb():
    logger.info("=" * 60)
    logger.info("MATCHDAY - Synchronisation & Protection MongoDB Atlas")
    logger.info("=" * 60)

    if not os.path.exists(GENECH_DB):
        logger.error(f"Base locale SQLite introuvable : {GENECH_DB}. Synchronisation annulée.")
        return False

    conn = sqlite3.connect(GENECH_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # -------------------------------------------------------------
    # 1. ÉQUIPES DU CLUB
    # -------------------------------------------------------------
    equipes = [
        {
            "_id": "525674_SENIOR_M1",
            "club_id": "525674",
            "code_equipe": "SENIOR_M1",
            "nom_officiel": "GENECH E.S. 1",
            "nom_affiche": "ES Genech (Équipe Fanion)",
            "categorie": "SENIOR",
            "rang": "FANION",
            "competition_actuelle": {
                "nom": "Seniors Régional 3",
                "poule": "Poule D",
                "saison": "2026-2027"
            },
            "actif": True,
            "derniere_synchro": datetime.now(timezone.utc).isoformat()
        },
        {
            "_id": "525674_SENIOR_M2",
            "club_id": "525674",
            "code_equipe": "SENIOR_M2",
            "nom_officiel": "GENECH E.S. 2",
            "nom_affiche": "ES Genech (Séniors Réserve)",
            "categorie": "SENIOR",
            "rang": "RESERVE",
            "competition_actuelle": {
                "nom": "Seniors Départemental 2",
                "poule": "Poule B",
                "saison": "2026-2027"
            },
            "actif": True,
            "derniere_synchro": datetime.now(timezone.utc).isoformat()
        },
        {
            "_id": "525674_U18_M1",
            "club_id": "525674",
            "code_equipe": "U18_M1",
            "nom_officiel": "GENECH E.S. U18",
            "nom_affiche": "ES Genech (U18 D1)",
            "categorie": "U18",
            "rang": "JEUNES",
            "competition_actuelle": {
                "nom": "U18 D1 / Gambardella",
                "poule": "Poule Unique",
                "saison": "2026-2027"
            },
            "actif": True,
            "derniere_synchro": datetime.now(timezone.utc).isoformat()
        }
    ]

    # -------------------------------------------------------------
    # 2. LICENCIÉS ANONYMISÉS
    # -------------------------------------------------------------
    cur.execute("SELECT DISTINCT joueur_nom, equipe, role FROM match_lineups;")
    raw_lineups = cur.fetchall()

    licencies_map = {}
    for row in raw_lineups:
        raw_name = row["joueur_nom"]
        if not raw_name or len(raw_name.strip()) < 2:
            continue

        anon_name = anonymize_player_name(raw_name)
        licencie_id = generate_hash_id(f"525674_{anon_name}")
        role = row["role"] or "JOUEUR"

        if licencie_id not in licencies_map:
            parts = anon_name.split(' ')
            prenom = parts[0]
            initiale = parts[1] if len(parts) > 1 else "X."

            licencies_map[licencie_id] = {
                "_id": licencie_id,
                "club_id": "525674",
                "identite": {
                    "nom_affiche": anon_name,
                    "prenom": prenom,
                    "initiale_nom": initiale,
                    "anonymise": True
                },
                "statut": "ACTIF",
                "role_principal": "JOUEUR" if ("TITULAIRE" in role or "REMPLACANT" in role) else "STAFF",
                "categorie_age": "SENIOR",
                "equipes_autorisees": ["SENIOR_M1"],
                "derniere_synchro": datetime.now(timezone.utc).isoformat()
            }

    licencies = list(licencies_map.values())

    # -------------------------------------------------------------
    # 3. SANCTIONS QUALIFIÉES (AVEC EXCLUSION STRICTE U18 / STAFF)
    # -------------------------------------------------------------
    query_events = """
    SELECT me.id, me.match_id, me.minute, me.type_event, me.acteur_principal, me.detail,
           m.date_heure, m.competition_id, c.nom as comp_nom, me.equipe
    FROM match_events me
    JOIN matchs m ON m.id = me.match_id
    LEFT JOIN competitions c ON c.id = m.competition_id
    WHERE me.type_event IN ('AVERTISSEMENT', 'EXPULSION')
      AND (me.equipe LIKE '%GENECH%' OR me.equipe = '');
    """
    cur.execute(query_events)
    raw_sanctions = cur.fetchall()

    sanctions = []
    sanctions_exclues = []

    for s in raw_sanctions:
        raw_name = s["acteur_principal"]
        anon_name = anonymize_player_name(raw_name)
        licencie_id = generate_hash_id(f"525674_{anon_name}")

        event_data = {
            "competition_nom": s["comp_nom"] or "",
            "equipe": s["equipe"] or "",
            "role_acteur": "JOUEUR",
            "acteur_principal": raw_name,
            "detail": s["detail"] or ""
        }

        is_eligible, raison = is_first_team_eligible(event_data)
        is_u18 = "U18" in str(s["comp_nom"]).upper() or "GAMBARDELLA" in str(s["comp_nom"]).upper()
        equipe_id = "525674_U18_M1" if is_u18 else "525674_SENIOR_M1"

        doc_sanction = {
            "_id": generate_hash_id(f"sanction_{s['id']}_{s['match_id']}_{raw_name}_{s['minute']}_{s['type_event']}"),
            "licencie_id": licencie_id,
            "nom_affiche": anon_name,
            "equipe_id": equipe_id,
            "match_id": s["match_id"],
            "date_match": s["date_heure"],
            "minute": s["minute"],
            "type_sanction": s["type_event"],
            "role_au_moment_faute": "TITULAIRE" if is_eligible else "DIRIGEANT_BANC",
            "competition": {
                "nom": s["comp_nom"] or "Compétition Régionale",
                "categorie": "U18" if is_u18 else "SENIOR"
            },
            "qualification_reglementaire": {
                "est_joueur_actif": is_eligible,
                "est_applicable_equipe_fanion": is_eligible and not is_u18,
                "motif_exclusion": raison if not (is_eligible and not is_u18) else None
            },
            "cycle_discipline": {
                "statut": "ACTIF" if (is_eligible and not is_u18) else "EXCLU_CALCUL_FANION"
            },
            "derniere_synchro": datetime.now(timezone.utc).isoformat()
        }

        if is_eligible and not is_u18:
            sanctions.append(doc_sanction)
        else:
            sanctions_exclues.append(doc_sanction)

    conn.close()

    # -------------------------------------------------------------
    # 4. GARDE-FOUS DE SÉCURITÉ (FAIL-SAFE CHECK)
    # -------------------------------------------------------------
    # Si le scraping a échoué (ex: 0 licenciés trouvés), on INTERDIT la mise à jour
    if len(licencies) < 15:
        logger.warning(
            f"[ALERTE PROTECTION] Volume anormalement faible ({len(licencies)} licenciés extraits). "
            f"Possible maintenance FFF ou erreur de scraping. SYNCHRONISATION ANNULÉE POUR PRÉSERVER ATLAS."
        )
        return False

    # Sauvegarde locale JSON d'archive
    try:
        with open(os.path.join(EXPORT_DIR, "equipes.json"), "w", encoding="utf-8") as f:
            json.dump(equipes, f, ensure_ascii=False, indent=2)
        with open(os.path.join(EXPORT_DIR, "licencies.json"), "w", encoding="utf-8") as f:
            json.dump(licencies, f, ensure_ascii=False, indent=2)
        with open(os.path.join(EXPORT_DIR, "sanctions.json"), "w", encoding="utf-8") as f:
            json.dump(sanctions, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Erreur sauvegarde JSON locale : {e}")

    logger.info(f"Vérification des volumes de données :")
    logger.info(f" - Équipes configurées     : {len(equipes)}")
    logger.info(f" - Licenciés anonymisés    : {len(licencies)}")
    logger.info(f" - Sanctions fanion actives: {len(sanctions)}")

    # -------------------------------------------------------------
    # 5. SYNCHRONISATION ATLAS NON-DESTRUCTIVE (UPSERT UNIQUEMENT)
    # -------------------------------------------------------------
    if not MONGODB_URI or "mongodb" not in MONGODB_URI:
        logger.info("[INFO] MONGODB_URI absent. Export JSON local terminé sans écriture distante.")
        return True

    logger.info("Connexion à MongoDB Atlas pour synchronisation sécurisée (Upsert)...")
    try:
        from pymongo import MongoClient, UpdateOne
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]

        # A. Équipes : Upsert
        equipes_ops = [
            UpdateOne({"_id": eq["_id"]}, {"$set": clean_doc_for_upsert(eq)}, upsert=True)
            for eq in equipes
        ]
        if equipes_ops:
            db.equipes.bulk_write(equipes_ops, ordered=False)

        # B. Licenciés : Upsert (Préserve les fiches si un joueur n'apparaît pas ce week-end)
        licencies_ops = [
            UpdateOne({"_id": lic["_id"]}, {"$set": clean_doc_for_upsert(lic)}, upsert=True)
            for lic in licencies
        ]
        if licencies_ops:
            db.licencies.bulk_write(licencies_ops, ordered=False)
            db.licencies.create_index([("club_id", 1), ("identite.nom_affiche", 1)])

        # C. Sanctions : Upsert (Ne supprime JAMAIS l'historique des sanctions précédentes)
        all_sanctions = sanctions + sanctions_exclues
        sanctions_ops = [
            UpdateOne({"_id": s["_id"]}, {"$set": clean_doc_for_upsert(s)}, upsert=True)
            for s in all_sanctions
        ]
        if sanctions_ops:
            db.sanctions.bulk_write(sanctions_ops, ordered=False)
            db.sanctions.create_index([
                ("equipe_id", 1),
                ("qualification_reglementaire.est_applicable_equipe_fanion", 1),
                ("cycle_discipline.statut", 1)
            ])

        logger.info(">>> [SUCCÈS] Base MongoDB Atlas synchronisée sans écrasement destructif !")
        return True

    except Exception as e:
        logger.error(f"[ERREUR ATLAS] Échec de synchronisation MongoDB Atlas : {e}")
        return False

if __name__ == "__main__":
    sync_to_mongodb()
