"""
Module de Scraping FFF Fiabilisé (Fail-Gracefully & Modulaire) - MatchDay
Résistant aux pannes FFF, 404, timeouts, et changements de structure HTML.
Isolation stricte des étapes : Score, Buts, Cartons, Compositions, Classement.
"""

import os
import re
import sys
import logging
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from playwright.sync_api import sync_playwright

from data_cleaner import anonymize_player_name, is_first_team_eligible

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Configuration du logging structuré
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("MatchDayScraper")

DB_PATH = os.path.join(os.path.dirname(__file__), "genech_performance.db")


def get_quart_heure(minute: int) -> str:
    """Détermine la tranche temporelle d'un événement."""
    if minute <= 15:   return "01-15'"
    elif minute <= 30: return "16-30'"
    elif minute <= 45: return "31-45+'"
    elif minute <= 60: return "46-60'"
    elif minute <= 75: return "61-75'"
    else:              return "76-90+'"


def launch_browser(p):
    """Lance Chrome si dispo (local Windows), sinon Chromium standard (GitHub Actions)."""
    args = ['--disable-blink-features=AutomationControlled', '--no-sandbox']
    try:
        return p.chromium.launch(channel="chrome", headless=True, args=args)
    except Exception:
        return p.chromium.launch(headless=True, args=args)


# -----------------------------------------------------------------------------
# 1. NAVIGATION SÉCURISÉE AVEC GESTION DES TIMEOUTS ET ERREURS RESEAU
# -----------------------------------------------------------------------------

def safe_navigate_page(page, url: str, timeout_ms: int = 25000) -> Optional[List[str]]:
    """
    Charge une page FFF de façon sécurisée avec gestion des timeouts, 404/503.
    Retourne les lignes de texte du DOM ou None en cas d'échec (Fail-Gracefully).
    """
    try:
        response = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        if response and response.status >= 400:
            logger.warning(f"HTTP {response.status} sur l'URL : {url} (Donnée FFF indisponible)")
            return None

        # Gestion bannière cookies Didomi si présente
        try:
            page.locator("#didomi-notice-agree-button").click(timeout=1500)
        except Exception:
            pass

        page.wait_for_timeout(1500)
        body_text = page.inner_text("body")
        lines = [l.strip() for l in body_text.split("\n") if l.strip()]
        return lines

    except Exception as e:
        logger.warning(f"Timeout ou erreur de navigation sur {url} : {e} -> Passage en mode repli.")
        return None


# -----------------------------------------------------------------------------
# 2. BLOCS D'EXTRACTION MODULAIRES AVEC VALEURS DE REPLI (FALLBACK)
# -----------------------------------------------------------------------------

def extract_score_and_status(lines: Optional[List[str]], current_statut: str = "A_VENIR") -> Tuple[Optional[int], Optional[int], str]:
    """
    Module A : Extraction sécurisée du score et du statut du match.
    En cas d'échec : retourne (None, None, current_statut).
    """
    if not lines:
        return None, None, current_statut

    try:
        for idx, l in enumerate(lines[:45]):
            if any(team in l.upper() for team in ['GENECH', 'TATINGHEM', 'ANICHE', 'MAUBEUGE', 'GUESNAIN', 'BONDUES', 'CHANTILLY', 'LYS', 'SAINGHIN', 'DUNKERQUE']):
                if idx + 2 < len(lines):
                    # Cas d'un match joué avec score affiché
                    if lines[idx+1].isdigit() and lines[idx+2].isdigit():
                        return int(lines[idx+1]), int(lines[idx+2]), "TERMINE"
                    # Cas d'un horaire (ex: "15:00")
                    elif re.match(r"^\d{1,2}:\d{2}$", lines[idx+1]):
                        return None, None, "A_VENIR"

        return None, None, current_statut

    except Exception as e:
        logger.warning(f"Erreur extraction score/statut : {e} -> Valeurs de repli assignées.")
        return None, None, "Donnée FFF indisponible"


def extract_events_and_sanctions(lines: Optional[List[str]], match_id: str, comp_name: str) -> List[Dict[str, Any]]:
    """
    Module B : Extraction sécurisée des événements de jeu et des sanctions.
    Isole les erreurs de parsing d'un événement pour ne pas faire planter les autres.
    Applique le filtrage strict des rôles (exclusion banc/staff) et des catégories.
    """
    if not lines:
        return []

    events = []
    try:
        i = 0
        while i < len(lines):
            line = lines[i]

            if line == "COMPOSITION":
                break  # Fin de la section résumé de match

            m = re.match(r"^(\d+)’(?:\+(\d+))?$", line)
            if m and i + 1 < len(lines):
                try:
                    min_val = int(m.group(1))
                    extra_val = int(m.group(2)) if m.group(2) else 0
                    tranche = get_quart_heure(min_val)
                    desc = lines[i + 1]

                    type_event = "AUTRE"
                    equipe = ""
                    actor = ""
                    second_actor = ""
                    detail = desc

                    if "But pour" in desc:
                        type_event = "BUT"
                        equipe = desc.replace("But pour", "").strip()
                        actor = lines[i + 3] if i + 3 < len(lines) and lines[i+2] == "inscrit par" else (lines[i+2] if i+2 < len(lines) else "")
                        detail = f"But inscrit par {actor}"

                    elif "Avertissement pour" in desc:
                        type_event = "AVERTISSEMENT"
                        equipe = desc.replace("Avertissement pour", "").strip()
                        actor = lines[i + 2] if i + 2 < len(lines) else ""
                        detail = "Carton jaune"

                    elif "Expulsion pour" in desc or "Exclusion pour" in desc:
                        type_event = "EXPULSION"
                        equipe = desc.replace("Expulsion pour", "").replace("Exclusion pour", "").strip()
                        actor = lines[i + 2] if i + 2 < len(lines) else ""
                        detail = "Carton rouge"

                    elif "Changement pour" in desc:
                        type_event = "CHANGEMENT"
                        equipe = desc.replace("Changement pour", "").strip()
                        actor = lines[i + 2] if i + 2 < len(lines) else ""
                        second_actor = lines[i + 4] if i + 4 < len(lines) and lines[i+3] == "remplace" else ""
                        detail = f"{actor} remplace {second_actor}"

                    # Si événement reconnu et acteur renseigné
                    if type_event != "AUTRE":
                        # Filtrage de sécurité via data_cleaner pour les sanctions
                        if type_event in ["AVERTISSEMENT", "EXPULSION"]:
                            event_info = {
                                "competition_nom": comp_name,
                                "equipe": equipe,
                                "role_acteur": "JOUEUR",
                                "acteur_principal": actor,
                                "detail": detail
                            }
                            is_eligible, _ = is_first_team_eligible(event_info)
                            if not is_eligible:
                                # Marquage explicite ou exclusion
                                detail = f"{detail} (Banc/Staff exclu)"

                        events.append({
                            "minute": min_val,
                            "temps_additionnel": extra_val,
                            "tranche_quart_heure": tranche,
                            "type_event": type_event,
                            "equipe": equipe,
                            "acteur_principal": anonymize_player_name(actor),
                            "acteur_secondaire": anonymize_player_name(second_actor) if second_actor else "",
                            "detail": detail
                        })

                except Exception as ev_err:
                    logger.warning(f"Erreur parsing ligne d'événement {i} sur match {match_id} : {ev_err} -> Ignoré.")

            i += 1

    except Exception as e:
        logger.warning(f"Erreur globale dans le bloc d'événements pour {match_id} : {e} -> Fallback liste vide.")
        return []

    return events


def extract_lineups(lines: Optional[List[str]], match_id: str, default_team: str = "GENECH ES") -> List[Dict[str, Any]]:
    """
    Module C : Extraction sécurisée des compositions officielles (FMI).
    Anonymise automatiquement chaque joueur au format 'Prénom N.'.
    """
    if not lines:
        return []

    lineups = []
    try:
        current_section = "RESUME"
        current_role = "TITULAIRE"
        current_team = default_team

        i = 0
        while i < len(lines):
            line = lines[i]

            if line == "COMPOSITION":
                current_section = "COMPOSITION"
                i += 1
                continue
            elif line in ["TITULAIRES", "TITULAIRE"]:
                current_role = "TITULAIRE"
                i += 1
                continue
            elif line in ["REMPLAÇANTS", "REMPLACANTS", "REMPLAÇANT"]:
                current_role = "REMPLACANT"
                i += 1
                continue
            elif line in ["OFFICIELS", "ARBITRES", "DIRIGEANTS", "DETAIL DE L'INSTALLATION", "LA FEDERATION"]:
                current_section = "FIN"

            if current_section == "COMPOSITION":
                # Détection d'un nom d'équipe au-dessus des titulaires
                if line not in ["TITULAIRES", "REMPLAÇANTS", "COMPOSITION"] and not line.isdigit() and len(line) > 3:
                    if i + 1 < len(lines) and lines[i + 1] in ["TITULAIRES", "TITULAIRE", "REMPLAÇANTS"]:
                        current_team = line.strip().upper()

                # Détection du numéro de maillot suivi du nom
                if line.isdigit() and i + 1 < len(lines):
                    num = int(line)
                    name = lines[i + 1]
                    if not name.isdigit() and name not in ["TITULAIRES", "REMPLAÇANTS", "REMPLACANTS", "DIRIGEANTS", "OFFICIELS", "ARBITRES"]:
                        anon_name = anonymize_player_name(name)
                        lineups.append({
                            "equipe": current_team,
                            "numero": num,
                            "joueur_nom": anon_name,
                            "role": current_role
                        })
                        i += 1

            i += 1

    except Exception as e:
        logger.warning(f"Erreur globale dans le bloc de composition pour {match_id} : {e} -> Fallback liste vide.")
        return []

    return lineups


# -----------------------------------------------------------------------------
# 3. EXTRACTION DU CLASSEMENT AVEC PROTECTION CONTRE L'ÉCRASEMENT VIDE
# -----------------------------------------------------------------------------

def scrape_standings_safely(page, cur, conn) -> int:
    """
    Module D : Scraping sécurisé du classement R3 Poule D.
    Protection : Ne supprime JAMAIS l'ancien classement si le scraping échoue ou renvoie < 8 équipes.
    """
    url = "https://epreuves.fff.fr/competition/engagement/452056-seniors-regional-3/phase/1/4"
    logger.info("--- Scraping Sécurisé Classement R3 Poule D ---")

    lines = safe_navigate_page(page, url, timeout_ms=25000)
    if not lines:
        logger.warning("[FALLBACK] Impossible d'accéder au classement FFF. Ancien classement préservé.")
        return 0

    try:
        new_standings = []
        in_classement = False
        rang = 1

        for i, l in enumerate(lines):
            if l == "CLASSEMENT":
                in_classement = True
                continue
            if in_classement and l == "VOIR LE CLASSEMENT DÉTAILLÉ":
                break
            if in_classement and l.isdigit() and int(l) == rang and i + 2 < len(lines):
                team_name = lines[i + 1]
                parts = lines[i + 2].split()
                if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                    pts, joues = int(parts[0]), int(parts[1])
                    new_standings.append((rang, team_name, pts, joues))
                    rang += 1

        # Règle de protection : Si moins de 8 équipes trouvées, le DOM a changé ou page incomplète
        if len(new_standings) < 8:
            logger.warning(f"[FALLBACK] Seulement {len(new_standings)} équipes extraites. Risque d'incohérence. Ancien classement préservé.")
            return 0

        # Mise à jour atomique uniquement si les données sont complètes
        cur.execute("DELETE FROM classement_poule WHERE competition_id = 'r3_poule_d';")
        for st in new_standings:
            cur.execute("""
            INSERT INTO classement_poule (competition_id, rang, equipe_nom, points, joues, victoires, nuls, defaites, buts_pour, buts_contre, diff)
            VALUES (?, ?, ?, ?, ?, 0, 0, 0, 0, 0, 0)
            """, ('r3_poule_d', st[0], st[1], st[2], st[3]))
        conn.commit()
        logger.info(f"Classement mis à jour avec succès : {len(new_standings)} équipes.")
        return len(new_standings)

    except Exception as e:
        logger.warning(f"[FALLBACK] Erreur lors du parsing du classement : {e}. Ancien classement préservé.")
        return 0


# -----------------------------------------------------------------------------
# 4. ORCHESTRATEUR PRINCIPAL AVEC ARCHITECTURE FAIL-GRACEFULLY
# -----------------------------------------------------------------------------

def scrape_fff():
    """
    Exécute l'intégralité du scraping FFF avec isolation totale des erreurs.
    Chaque match et chaque compétition s'exécutent indépendamment.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Initialisation des compétitions si absentes
    try:
        cur.execute("""
        INSERT OR REPLACE INTO competitions (id, nom, type, saison, url)
        VALUES 
        ('r3_poule_d', 'Seniors Régional 3 (Poule D)', 'CHAMPIONNAT', '2026-2027', 'https://epreuves.fff.fr/competition/engagement/452056-seniors-regional-3/phase/1/4'),
        ('cdf_2026', 'Coupe de France', 'COUPE_DE_FRANCE', '2026-2027', 'https://epreuves.fff.fr/competition/engagement/451733-coupe-de-france/phase/1');
        """)
        conn.commit()
    except Exception as e:
        logger.warning(f"Erreur initialisation tables compétitions : {e}")

    matches_to_scrape = [
        {"id": "r3_j1_bondues_genech", "competition_id": "r3_poule_d", "comp_nom": "Seniors Régional 3", "tour_ou_journee": "Journée 1", "date_heure": "2026-09-06 15:00", "equipe_domicile": "BONDUES FC 2", "equipe_exterieur": "GENECH ES", "score_domicile": 1, "score_exterieur": 2, "statut": "TERMINE", "url": "https://epreuves.fff.fr/competition/match/56216887-bondues-football-club-ent-s-de-genech"},
        {"id": "r3_j2_genech_maubeuge", "competition_id": "r3_poule_d", "comp_nom": "Seniors Régional 3", "tour_ou_journee": "Journée 2", "date_heure": "2026-09-20 15:00", "equipe_domicile": "GENECH ES", "equipe_exterieur": "MAUBEUGE US 2", "score_domicile": 2, "score_exterieur": 0, "statut": "TERMINE", "url": "https://epreuves.fff.fr/competition/match/56216893-ent-s-de-genech-u-s-maubeuge"},
        {"id": "r3_j3_guesnain_genech", "competition_id": "r3_poule_d", "comp_nom": "Seniors Régional 3", "tour_ou_journee": "Journée 3", "date_heure": "2026-10-04 15:00", "equipe_domicile": "GUESNAIN SC", "equipe_exterieur": "GENECH ES", "score_domicile": 1, "score_exterieur": 1, "statut": "TERMINE", "url": "https://epreuves.fff.fr/competition/match/56216902-s-c-guesnain-ent-s-de-genech"},
        {"id": "r3_j4_genech_anstaing", "competition_id": "r3_poule_d", "comp_nom": "Seniors Régional 3", "tour_ou_journee": "Journée 4", "date_heure": "2026-10-18 15:00", "equipe_domicile": "GENECH ES", "equipe_exterieur": "ANSTAING CHERENG EC", "score_domicile": 1, "score_exterieur": 1, "statut": "TERMINE", "url": "https://epreuves.fff.fr/competition/match/56216904-ent-s-de-genech-et-c-anstaing-chereng"},
        {"id": "r3_j4_bavay_aniche", "competition_id": "r3_poule_d", "comp_nom": "Seniors Régional 3", "tour_ou_journee": "Journée 4", "date_heure": "2026-10-18 15:00", "equipe_domicile": "BAVAY US", "equipe_exterieur": "ANICHE SC", "score_domicile": 1, "score_exterieur": 1, "statut": "TERMINE", "url": "https://epreuves.fff.fr/competition/match/56216903-u-s-bavay-s-c-aniche"},
        {"id": "r3_j4_beuvry_guesnain", "competition_id": "r3_poule_d", "comp_nom": "Seniors Régional 3", "tour_ou_journee": "Journée 4", "date_heure": "2026-10-18 15:00", "equipe_domicile": "BEUVRY LA FORET AS", "equipe_exterieur": "GUESNAIN SC", "score_domicile": 2, "score_exterieur": 1, "statut": "TERMINE", "url": "https://epreuves.fff.fr/competition/match/56216905-a-s-beuvry-la-foret-s-c-guesnain"},
        {"id": "cdf_t2_lys_genech", "competition_id": "cdf_2026", "comp_nom": "Coupe de France", "tour_ou_journee": "Tour 2", "date_heure": "2026-08-30 15:00", "equipe_domicile": "LYS L/LANNOY STELLA", "equipe_exterieur": "GENECH ES", "score_domicile": 0, "score_exterieur": 0, "statut": "TERMINE", "url": "https://epreuves.fff.fr/competition/match/79044919-lys-lez-lannoy-stella-ent-s-de-genech"},
        {"id": "cdf_t3_sainghin_genech", "competition_id": "cdf_2026", "comp_nom": "Coupe de France", "tour_ou_journee": "Tour 3", "date_heure": "2026-09-13 15:00", "equipe_domicile": "SAINGHIN WEPPES AO", "equipe_exterieur": "GENECH ES", "score_domicile": 0, "score_exterieur": 1, "statut": "TERMINE", "url": "https://epreuves.fff.fr/competition/match/79190037-a-o-sainghin-en-weppes-ent-s-de-genech"},
        {"id": "cdf_t4_genech_dunkerque", "competition_id": "cdf_2026", "comp_nom": "Coupe de France", "tour_ou_journee": "Tour 4", "date_heure": "2026-09-27 15:00", "equipe_domicile": "GENECH ES", "equipe_exterieur": "DUNKERQUE MALO FC", "score_domicile": 2, "score_exterieur": 0, "statut": "TERMINE", "url": "https://epreuves.fff.fr/competition/match/79646320-ent-s-de-genech-f-c-dunkerque-malo-plage"},
        {"id": "cdf_t5_genech_chantilly", "competition_id": "cdf_2026", "comp_nom": "Coupe de France", "tour_ou_journee": "Tour 5", "date_heure": "2026-10-11 15:00", "equipe_domicile": "GENECH ES", "equipe_exterieur": "CHANTILLY US", "score_domicile": 1, "score_exterieur": 0, "statut": "TERMINE", "url": "https://epreuves.fff.fr/competition/match/79813375-ent-s-de-genech-u-s-de-chantilly"},
        {"id": "cdf_t6_tatinghem_genech", "competition_id": "cdf_2026", "comp_nom": "Coupe de France", "tour_ou_journee": "Tour 6", "date_heure": "2026-10-25 15:00", "equipe_domicile": "ST MARTIN TATINGHEM", "equipe_exterieur": "GENECH ES", "score_domicile": 2, "score_exterieur": 0, "statut": "TERMINE", "url": "https://epreuves.fff.fr/competition/match/80499782-football-club-saint-martin-lez-tatinghem-ent-s-de-genech"},
        {"id": "r3_j5_aniche_genech", "competition_id": "r3_poule_d", "comp_nom": "Seniors Régional 3", "tour_ou_journee": "Journée 5", "date_heure": "2026-11-08 14:30", "equipe_domicile": "ANICHE SC", "equipe_exterieur": "GENECH ES", "score_domicile": None, "score_exterieur": None, "statut": "A_VENIR", "url": "https://epreuves.fff.fr/competition/match/56216911-s-c-aniche-ent-s-de-genech"}
    ]

    nb_matches_success = 0
    nb_matches_fallback = 0

    with sync_playwright() as p:
        browser = launch_browser(p)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()

        # 1. Scraping du classement (Non destructif)
        scrape_standings_safely(page, cur, conn)

        # 2. Scraping de chaque match avec isolation totale
        for m in matches_to_scrape:
            match_id = m["id"]
            logger.info(f"Traitement du match : {match_id} ({m['tour_ou_journee']})")

            # Valeurs saines par défaut (issues du référentiel initial)
            s_dom = m["score_domicile"]
            s_ext = m["score_exterieur"]
            statut = m["statut"]

            # Navigation sécurisée
            lines = safe_navigate_page(page, m["url"], timeout_ms=25000)

            if lines is None:
                nb_matches_fallback += 1
                logger.warning(f"[FALLBACK ACTIF] {match_id} : FFF inaccessible. Conservation des scores et détails existants.")
            else:
                nb_matches_success += 1
                
                # Étape A : Score & Statut
                parsed_s_dom, parsed_s_ext, parsed_statut = extract_score_and_status(lines, current_statut=statut)
                if parsed_statut == "TERMINE" and parsed_s_dom is not None:
                    s_dom = parsed_s_dom
                    s_ext = parsed_s_ext
                    statut = "TERMINE"

                # Étape B : Événements & Cartons
                events = extract_events_and_sanctions(lines, match_id, m.get("comp_nom", ""))

                # Étape C : Compositions officielles
                lineups = extract_lineups(lines, match_id)

                # Sauvegarde en base uniquement des sections qui ont abouti (Non-destructif)
                try:
                    if statut == "TERMINE" and len(events) > 0:
                        cur.execute("DELETE FROM match_events WHERE match_id = ?", (match_id,))
                        for ev in events:
                            cur.execute("""
                            INSERT INTO match_events (match_id, minute, temps_additionnel, tranche_quart_heure, type_event, equipe, acteur_principal, acteur_secondaire, detail)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (match_id, ev["minute"], ev["temps_additionnel"], ev["tranche_quart_heure"], ev["type_event"], ev["equipe"], ev["acteur_principal"], ev["acteur_secondaire"], ev["detail"]))

                    if len(lineups) > 0:
                        cur.execute("DELETE FROM match_lineups WHERE match_id = ?", (match_id,))
                        for lp in lineups:
                            cur.execute("""
                            INSERT INTO match_lineups (match_id, equipe, numero, joueur_nom, role)
                            VALUES (?, ?, ?, ?, ?)
                            """, (match_id, lp["equipe"], lp["numero"], lp["joueur_nom"], lp["role"]))

                except Exception as db_err:
                    logger.warning(f"Erreur enregistrement événements/compositions pour {match_id} : {db_err}")

            # Enregistrement garanti du match (score et statut préservés ou mis à jour)
            try:
                cur.execute("""
                INSERT OR REPLACE INTO matchs (id, competition_id, tour_ou_journee, date_heure, equipe_domicile, equipe_exterieur, score_domicile, score_exterieur, statut, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (match_id, m["competition_id"], m["tour_ou_journee"], m["date_heure"], m["equipe_domicile"], m["equipe_exterieur"], s_dom, s_ext, statut, m["url"]))
                conn.commit()
            except Exception as match_save_err:
                logger.error(f"Erreur critique enregistrement statut match {match_id} : {match_save_err}")

        browser.close()

    conn.close()

    logger.info("=" * 60)
    logger.info(f"RÉSUMÉ DU SCRAPING FAIL-GRACEFULLY :")
    logger.info(f" - Matchs scrapés en direct avec succès : {nb_matches_success}")
    logger.info(f" - Matchs protégés en mode Fallback     : {nb_matches_fallback}")
    logger.info("=" * 60)


if __name__ == "__main__":
    from database import init_db
    init_db()
    scrape_fff()
