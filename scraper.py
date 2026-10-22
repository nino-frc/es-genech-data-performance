import os
import re
import sys
import sqlite3
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = os.path.join(os.path.dirname(__file__), "genech_performance.db")

def get_quart_heure(minute: int) -> str:
    if minute <= 15:   return "01-15'"
    elif minute <= 30: return "16-30'"
    elif minute <= 45: return "31-45+'"
    elif minute <= 60: return "46-60'"
    elif minute <= 75: return "61-75'"
    else:              return "76-90+'"

def launch_browser(p):
    """Lance Chrome si dispo (Windows local), sinon Chromium standard (GitHub Actions Linux)."""
    args = ['--disable-blink-features=AutomationControlled', '--no-sandbox']
    try:
        return p.chromium.launch(channel="chrome", headless=True, args=args)
    except Exception:
        return p.chromium.launch(headless=True, args=args)

def parse_match_details(page, match_url: str):
    page.goto(match_url, wait_until="domcontentloaded", timeout=25000)
    try:
        page.locator("#didomi-notice-agree-button").click(timeout=1500)
    except Exception:
        pass
    page.wait_for_timeout(2000)

    lines = [l.strip() for l in page.inner_text("body").split("\n") if l.strip()]

    events = []
    lineups = []
    score_dom = None
    score_ext = None
    statut = "A_VENIR"

    # Détection automatique du score et du statut (TERMINE ou A_VENIR)
    for idx, l in enumerate(lines[:35]):
        if any(team in l.upper() for team in ['GENECH', 'TATINGHEM', 'ANICHE', 'MAUBEUGE', 'GUESNAIN', 'BONDUES', 'CHANTILLY']) and idx + 3 < len(lines):
            if lines[idx+1].isdigit() and lines[idx+2].isdigit():
                score_dom = int(lines[idx+1])
                score_ext = int(lines[idx+2])
                statut = "TERMINE"
                break
            elif re.match(r"^\d{1,2}:\d{2}$", lines[idx+1]):
                statut = "A_VENIR"
                break
    
    current_section = "RESUME"
    current_role = "TITULAIRE"
    
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

        if current_section == "RESUME":
            m = re.match(r"^(\d+)’(?:\+(\d+))?$", line)
            if m:
                min_val = int(m.group(1))
                extra_val = int(m.group(2)) if m.group(2) else 0
                tranche = get_quart_heure(min_val)

                if i + 1 < len(lines):
                    desc = lines[i + 1]
                    equipe = ""
                    type_event = "AUTRE"

                    if "But pour" in desc:
                        type_event = "BUT"
                        equipe = desc.replace("But pour", "").strip()
                        actor = lines[i + 3] if i + 3 < len(lines) and lines[i+2] == "inscrit par" else (lines[i+2] if i+2 < len(lines) else "")
                        events.append({
                            "minute": min_val,
                            "temps_additionnel": extra_val,
                            "tranche_quart_heure": tranche,
                            "type_event": type_event,
                            "equipe": equipe,
                            "acteur_principal": actor,
                            "acteur_secondaire": "",
                            "detail": desc
                        })
                    elif "Avertissement pour" in desc:
                        type_event = "AVERTISSEMENT"
                        equipe = desc.replace("Avertissement pour", "").strip()
                        actor = lines[i + 2] if i + 2 < len(lines) else ""
                        events.append({
                            "minute": min_val,
                            "temps_additionnel": extra_val,
                            "tranche_quart_heure": tranche,
                            "type_event": type_event,
                            "equipe": equipe,
                            "acteur_principal": actor,
                            "acteur_secondaire": "",
                            "detail": "Carton jaune"
                        })
                    elif "Expulsion pour" in desc or "Exclusion pour" in desc:
                        type_event = "EXPULSION"
                        equipe = desc.replace("Expulsion pour", "").replace("Exclusion pour", "").strip()
                        actor = lines[i + 2] if i + 2 < len(lines) else ""
                        events.append({
                            "minute": min_val,
                            "temps_additionnel": extra_val,
                            "tranche_quart_heure": tranche,
                            "type_event": type_event,
                            "equipe": equipe,
                            "acteur_principal": actor,
                            "acteur_secondaire": "",
                            "detail": "Carton rouge"
                        })
                    elif "Changement pour" in desc:
                        type_event = "CHANGEMENT"
                        equipe = desc.replace("Changement pour", "").strip()
                        entrant = lines[i + 2] if i + 2 < len(lines) else ""
                        sortant = lines[i + 4] if i + 4 < len(lines) and lines[i+3] == "remplace" else ""
                        events.append({
                            "minute": min_val,
                            "temps_additionnel": extra_val,
                            "tranche_quart_heure": tranche,
                            "type_event": type_event,
                            "equipe": equipe,
                            "acteur_principal": entrant,
                            "acteur_secondaire": sortant,
                            "detail": f"{entrant} remplace {sortant}"
                        })

        elif current_section == "COMPOSITION":
            if line.isdigit() and i + 1 < len(lines):
                num = int(line)
                name = lines[i + 1]
                if not name.isdigit() and name not in ["TITULAIRES", "REMPLAÇANTS", "REMPLACANTS", "DIRIGEANTS", "OFFICIELS", "ARBITRES"]:
                    team = "GENECH ES"
                    lineups.append({
                        "equipe": team,
                        "numero": num,
                        "joueur_nom": name,
                        "role": current_role
                    })
                    i += 1

        i += 1

    return events, lineups, score_dom, score_ext, statut

def scrape_fff():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Initialisation des compétitions
    cur.execute("""
    INSERT OR REPLACE INTO competitions (id, nom, type, saison, url)
    VALUES 
    ('r3_poule_d', 'Seniors Régional 3 (Poule D)', 'CHAMPIONNAT', '2026-2027', 'https://epreuves.fff.fr/competition/engagement/452056-seniors-regional-3/phase/1/4'),
    ('cdf_2026', 'Coupe de France', 'COUPE_DE_FRANCE', '2026-2027', 'https://epreuves.fff.fr/competition/engagement/451733-coupe-de-france/phase/1');
    """)
    conn.commit()

    with sync_playwright() as p:
        browser = launch_browser(p)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()

        print("--- Scraping Classement R3 Poule D ---")
        try:
            page.goto("https://epreuves.fff.fr/competition/engagement/452056-seniors-regional-3/phase/1/4", wait_until="networkidle", timeout=30000)
            try:
                page.locator("#didomi-notice-agree-button").click(timeout=1500)
            except Exception:
                pass
            page.wait_for_timeout(2000)

            lines = [l.strip() for l in page.inner_text("body").split("\n") if l.strip()]
            cur.execute("DELETE FROM classement_poule WHERE competition_id = 'r3_poule_d';")
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
                        cur.execute("""
                        INSERT INTO classement_poule (competition_id, rang, equipe_nom, points, joues, victoires, nuls, defaites, buts_pour, buts_contre, diff)
                        VALUES (?, ?, ?, ?, ?, 0, 0, 0, 0, 0, 0)
                        """, ('r3_poule_d', rang, team_name, pts, joues))
                        rang += 1
            conn.commit()
            print(f"Classement inséré : {rang - 1} équipes.")
        except Exception as e:
            print(f"Erreur scraping classement : {e}")

        # Liste complète et ordonnée des matchs clés (Passés et Futurs)
        matches_to_scrape = [
            {"id": "r3_j1_bondues_genech", "competition_id": "r3_poule_d", "tour_ou_journee": "Journée 1", "date_heure": "2026-09-06 15:00", "equipe_domicile": "BONDUES FC 2", "equipe_exterieur": "GENECH ES", "score_domicile": 1, "score_exterieur": 2, "statut": "TERMINE", "url": "https://epreuves.fff.fr/competition/match/56216887-bondues-football-club-ent-s-de-genech"},
            {"id": "r3_j2_genech_maubeuge", "competition_id": "r3_poule_d", "tour_ou_journee": "Journée 2", "date_heure": "2026-09-20 15:00", "equipe_domicile": "GENECH ES", "equipe_exterieur": "MAUBEUGE US 2", "score_domicile": 2, "score_exterieur": 0, "statut": "TERMINE", "url": "https://epreuves.fff.fr/competition/match/56216893-ent-s-de-genech-u-s-maubeuge"},
            {"id": "r3_j3_guesnain_genech", "competition_id": "r3_poule_d", "tour_ou_journee": "Journée 3", "date_heure": "2026-10-04 15:00", "equipe_domicile": "GUESNAIN SC", "equipe_exterieur": "GENECH ES", "score_domicile": 1, "score_exterieur": 1, "statut": "TERMINE", "url": "https://epreuves.fff.fr/competition/match/56216902-s-c-guesnain-ent-s-de-genech"},
            {"id": "r3_j4_genech_anstaing", "competition_id": "r3_poule_d", "tour_ou_journee": "Journée 4", "date_heure": "2026-10-18 15:00", "equipe_domicile": "GENECH ES", "equipe_exterieur": "ANSTAING CHERENG EC", "score_domicile": 1, "score_exterieur": 1, "statut": "TERMINE", "url": "https://epreuves.fff.fr/competition/match/56216904-ent-s-de-genech-et-c-anstaing-chereng"},
            {"id": "r3_j4_bavay_aniche", "competition_id": "r3_poule_d", "tour_ou_journee": "Journée 4", "date_heure": "2026-10-18 15:00", "equipe_domicile": "BAVAY US", "equipe_exterieur": "ANICHE SC", "score_domicile": 1, "score_exterieur": 1, "statut": "TERMINE", "url": "https://epreuves.fff.fr/competition/match/56216903-u-s-bavay-s-c-aniche"},
            {"id": "r3_j4_beuvry_guesnain", "competition_id": "r3_poule_d", "tour_ou_journee": "Journée 4", "date_heure": "2026-10-18 15:00", "equipe_domicile": "BEUVRY LA FORET AS", "equipe_exterieur": "GUESNAIN SC", "score_domicile": 2, "score_exterieur": 1, "statut": "TERMINE", "url": "https://epreuves.fff.fr/competition/match/56216905-a-s-beuvry-la-foret-s-c-guesnain"},
            {"id": "cdf_t2_lys_genech", "competition_id": "cdf_2026", "tour_ou_journee": "Tour 2", "date_heure": "2026-08-30 15:00", "equipe_domicile": "LYS L/LANNOY STELLA", "equipe_exterieur": "GENECH ES", "score_domicile": 0, "score_exterieur": 0, "statut": "TERMINE", "url": "https://epreuves.fff.fr/competition/match/79044919-lys-lez-lannoy-stella-ent-s-de-genech"},
            {"id": "cdf_t3_sainghin_genech", "competition_id": "cdf_2026", "tour_ou_journee": "Tour 3", "date_heure": "2026-09-13 15:00", "equipe_domicile": "SAINGHIN WEPPES AO", "equipe_exterieur": "GENECH ES", "score_domicile": 0, "score_exterieur": 1, "statut": "TERMINE", "url": "https://epreuves.fff.fr/competition/match/79190037-a-o-sainghin-en-weppes-ent-s-de-genech"},
            {"id": "cdf_t4_genech_dunkerque", "competition_id": "cdf_2026", "tour_ou_journee": "Tour 4", "date_heure": "2026-09-27 15:00", "equipe_domicile": "GENECH ES", "equipe_exterieur": "DUNKERQUE MALO FC", "score_domicile": 2, "score_exterieur": 0, "statut": "TERMINE", "url": "https://epreuves.fff.fr/competition/match/79646320-ent-s-de-genech-f-c-dunkerque-malo-plage"},
            {"id": "cdf_t5_genech_chantilly", "competition_id": "cdf_2026", "tour_ou_journee": "Tour 5", "date_heure": "2026-10-11 15:00", "equipe_domicile": "GENECH ES", "equipe_exterieur": "CHANTILLY US", "score_domicile": 1, "score_exterieur": 0, "statut": "TERMINE", "url": "https://epreuves.fff.fr/competition/match/79813375-ent-s-de-genech-u-s-de-chantilly"},
            {"id": "cdf_t6_tatinghem_genech", "competition_id": "cdf_2026", "tour_ou_journee": "Tour 6 (Finale Régionale)", "date_heure": "2026-10-25 15:00", "equipe_domicile": "ST MARTIN TATINGHEM", "equipe_exterieur": "GENECH ES", "score_domicile": None, "score_exterieur": None, "statut": "A_VENIR", "url": "https://epreuves.fff.fr/competition/match/80499782-football-club-saint-martin-lez-tatinghem-ent-s-de-genech"},
            {"id": "r3_j5_aniche_genech", "competition_id": "r3_poule_d", "tour_ou_journee": "Journée 5", "date_heure": "2026-11-08 14:30", "equipe_domicile": "ANICHE SC", "equipe_exterieur": "GENECH ES", "score_domicile": None, "score_exterieur": None, "statut": "A_VENIR", "url": "https://epreuves.fff.fr/competition/match/56216911-s-c-aniche-ent-s-de-genech"}
        ]

        cur.execute("DELETE FROM match_events;")
        cur.execute("DELETE FROM match_lineups;")

        for m in matches_to_scrape:
            # Vérification dynamique sur la page FFF si le match est joué ou à venir
            s_dom = m["score_domicile"]
            s_ext = m["score_exterieur"]
            statut = m["statut"]
            
            try:
                events, lineups, parsed_s_dom, parsed_s_ext, parsed_statut = parse_match_details(page, m["url"])
                # Si la FFF affiche désormais un score final, on met à jour automatiquement
                if parsed_statut == "TERMINE" and parsed_s_dom is not None:
                    s_dom = parsed_s_dom
                    s_ext = parsed_s_ext
                    statut = "TERMINE"
                
                cur.execute("""
                INSERT OR REPLACE INTO matchs (id, competition_id, tour_ou_journee, date_heure, equipe_domicile, equipe_exterieur, score_domicile, score_exterieur, statut, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (m["id"], m["competition_id"], m["tour_ou_journee"], m["date_heure"], m["equipe_domicile"], m["equipe_exterieur"], s_dom, s_ext, statut, m["url"]))

                if statut == "TERMINE":
                    for ev in events:
                        cur.execute("""
                        INSERT INTO match_events (match_id, minute, temps_additionnel, tranche_quart_heure, type_event, equipe, acteur_principal, acteur_secondaire, detail)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (m["id"], ev["minute"], ev["temps_additionnel"], ev["tranche_quart_heure"], ev["type_event"], ev["equipe"], ev["acteur_principal"], ev["acteur_secondaire"], ev["detail"]))

                    for lp in lineups:
                        cur.execute("""
                        INSERT INTO match_lineups (match_id, equipe, numero, joueur_nom, role)
                        VALUES (?, ?, ?, ?, ?)
                        """, (m["id"], lp["equipe"], lp["numero"], lp["joueur_nom"], lp["role"]))
            except Exception as e:
                print(f"Erreur scraping {m['id']}: {e}")

        conn.commit()
        browser.close()

    conn.close()
    print("Pipeline de scraping exécuté avec succès.")

if __name__ == "__main__":
    from database import init_db
    init_db()
    scrape_fff()
