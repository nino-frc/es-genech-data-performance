"""
Script de migration et structuration des collections MongoDB Atlas pour MatchDay.
Génère les 3 collections :
- 'licencies' : Joueurs & membres avec anonymisation 'Prénom N.'
- 'equipes'   : Hiérarchie des équipes par club
- 'sanctions' : Cartons et sanctions qualifiés avec exclusion stricte U18/Banc
"""

import os
import json
import sqlite3
import hashlib
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from data_cleaner import anonymize_player_name, is_first_team_eligible

BASE_DIR = os.path.dirname(__file__)
GENECH_DB = os.path.join(BASE_DIR, "genech_performance.db")
EXPORT_DIR = os.path.join(BASE_DIR, "exports_mongodb")
os.makedirs(EXPORT_DIR, exist_ok=True)

MONGODB_URI = os.getenv("MONGODB_URI", "")
DB_NAME = os.getenv("MONGODB_DB_NAME", "matchday_db")

def generate_hash_id(value: str) -> str:
    """Génère un identifiant unique déterministe."""
    return hashlib.md5(value.encode('utf-8')).hexdigest()[:24]

def run_migration():
    print("=" * 60)
    print("MATCHDAY - Migration vers schéma MongoDB 3 Collections")
    print("=" * 60)

    conn = sqlite3.connect(GENECH_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # -------------------------------------------------------------
    # 1. COLLECTION 'equipes'
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
            "actif": True
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
            "actif": True
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
            "actif": True
        }
    ]

    # -------------------------------------------------------------
    # 2. COLLECTION 'licencies' (Depuis lineups et events avec anonymisation)
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
                "role_principal": "JOUEUR" if "TITULAIRE" in role or "REMPLACANT" in role else "STAFF",
                "categorie_age": "SENIOR",
                "equipes_autorisees": ["SENIOR_M1"]
            }

    licencies = list(licencies_map.values())

    # -------------------------------------------------------------
    # 3. COLLECTION 'sanctions' (Avec filtrage strict U18 et banc)
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

        # Déterminer si le match est un match U18
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
            }
        }

        if is_eligible and not is_u18:
            sanctions.append(doc_sanction)
        else:
            sanctions_exclues.append(doc_sanction)

    conn.close()

    # Sauvegarde locale JSON
    with open(os.path.join(EXPORT_DIR, "equipes.json"), "w", encoding="utf-8") as f:
        json.dump(equipes, f, ensure_ascii=False, indent=2)

    with open(os.path.join(EXPORT_DIR, "licencies.json"), "w", encoding="utf-8") as f:
        json.dump(licencies, f, ensure_ascii=False, indent=2)

    with open(os.path.join(EXPORT_DIR, "sanctions.json"), "w", encoding="utf-8") as f:
        json.dump(sanctions, f, ensure_ascii=False, indent=2)

    with open(os.path.join(EXPORT_DIR, "sanctions_exclues.json"), "w", encoding="utf-8") as f:
        json.dump(sanctions_exclues, f, ensure_ascii=False, indent=2)

    print(f"Extraction terminée avec succès !")
    print(f" - Equipes enregistrées : {len(equipes)}")
    print(f" - Licenciés anonymisés ('Prénom N.') : {len(licencies)}")
    print(f" - Sanctions fanion qualifiées actives : {len(sanctions)}")
    print(f" - Sanctions exclues (U18 / Banc / Staff) : {len(sanctions_exclues)}")

    # Envoi vers MongoDB Atlas si URI présent
    if MONGODB_URI and "mongodb" in MONGODB_URI:
        print("\nConnexion à MongoDB Atlas...")
        try:
            from pymongo import MongoClient
            client = MongoClient(MONGODB_URI)
            db = client[DB_NAME]
            
            # Équipes
            db.equipes.drop()
            if equipes:
                db.equipes.insert_many(equipes)
            
            # Licenciés
            db.licencies.drop()
            if licencies:
                db.licencies.insert_many(licencies)
            db.licencies.create_index([("club_id", 1), ("identite.nom_affiche", 1)])
            
            # Sanctions
            db.sanctions.drop()
            all_sanctions = sanctions + sanctions_exclues
            if all_sanctions:
                db.sanctions.insert_many(all_sanctions)
            db.sanctions.create_index([
                ("equipe_id", 1), 
                ("qualification_reglementaire.est_applicable_equipe_fanion", 1),
                ("cycle_discipline.statut", 1)
            ])
            print("Migration vers MongoDB Atlas complétée avec succès !")
        except Exception as e:
            print(f"Erreur lors de la connexion MongoDB Atlas : {e}")
    else:
        print("\nNote: Variable MONGODB_URI non détectée dans .env.")
        print(f"Les 3 collections ont été exportées au format JSON dans : {EXPORT_DIR}")

if __name__ == "__main__":
    run_migration()
