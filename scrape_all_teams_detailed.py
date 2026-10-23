"""
Scraper Détaillé Multi-Équipes ES Genech
Collecte les matchs, scores, buteurs, cartons et compositions
pour toutes les équipes du club (Seniors D2, U18, U14, Vétérans, etc.)
"""

import os
import sys
import re
import sqlite3
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "genech_performance.db")

MAPPING_COMPETITION_EQUIPE = {
    "Seniors Régional 3": "SENIOR_M1",
    "Coupe de France": "SENIOR_M1",
    "Seniors D2": "SENIOR_M3",
    "Coupe Hauts-de-France Féminine": "SENIOR_F1",
    "Interdistricts Féminin": "SENIOR_F2",
    "18 19 D1": "U18_M1",
    "Coupe des Flandres U18 U19": "U19_M1",
    "14 D2": "U14_M1",
    "U13 NIV 1": "U13_M2",
    "U13 NIVEAU 2": "U13_M1",
    "U12 NIVEAU 1": "U12_M1",
    "U11 NIVEAU 1": "U11_M2",
    "U11 NIVEAU 3": "U11_M1",
    "U10 NIVEAU 2": "U10_M1",
    "VETERANS": "VETERAN_M1",
    "LOISIR": "LOISIR_M1"
}

def detect_equipe_club(comp_str: str) -> str:
    for pattern, eq_id in MAPPING_COMPETITION_EQUIPE.items():
        if pattern.lower() in comp_str.lower():
            return eq_id
    return "SENIOR_M1"

def parse_date_to_iso(date_text: str) -> str:
    mois_map = {
        "JAN": "01", "FEV": "02", "MAR": "03", "AVR": "04", "MAI": "05", "JUIN": "06",
        "JUIL": "07", "AOU": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12"
    }
    m = re.search(r"(\d{1,2})\s+([A-ZÉÛ]{3,4})\s+(\d{4})\s*-\s*(\d{1,2})H(\d{2})", date_text, re.IGNORECASE)
    if m:
        day = f"{int(m.group(1)):02d}"
        month_raw = m.group(2).upper()[:3]
        month = mois_map.get(month_raw, "10")
        year = m.group(3)
        hour = f"{int(m.group(4)):02d}"
        minute = m.group(5)
        return f"{year}-{month}-{day} {hour}:{minute}"
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def run():
    print("======================================================================")
    print("🚀 COLLECTE DES DONNÉES JOUEURS & MATCHS MULTI-ÉQUIPES ES GENECH")
    print("======================================================================")

    args = ['--disable-blink-features=AutomationControlled', '--no-sandbox']
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=True, args=args)
        except Exception:
            browser = p.chromium.launch(headless=True, args=args)

        page = browser.new_page(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800}
        )

        url = "https://epreuves.fff.fr/competition/club/525674-ent-s-de-genech/equipes.html"
        print(f"Chargement de la page club : {url}...")
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        try:
            page.locator('#didomi-notice-agree-button').click(timeout=1500)
        except: pass
        page.wait_for_timeout(2000)

        links = page.eval_on_selector_all('a', 'elements => elements.map(e => ({text: e.innerText.trim(), href: e.href}))')
        match_links = [l['href'] for l in links if '/competition/match/' in l['href']]
        # Dédupliquer tout en gardant l'ordre
        match_links = list(dict.fromkeys(match_links))
        print(f"Trouvé {len(match_links)} liens de matchs officiels FFF pour le club !")

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        scraped_matches = 0
        scraped_players = 0

        for m_url in match_links:
            # Si c'est un match déjà scrapé pour Senior 1, on peut le passer si ses compos existent déjà
            m_id_part = m_url.split('/match/')[-1].split('?')[0]
            existing = cur.execute("SELECT count(*) FROM match_lineups WHERE match_id LIKE ?", (f"%{m_id_part[:8]}%",)).fetchone()[0]
            if existing > 0:
                print(f"Match déjà complet ({m_id_part[:20]}), passage...")
                continue

            print(f"\nScraping de la feuille de match : {m_url}...")
            try:
                page.goto(m_url, wait_until="domcontentloaded", timeout=25000)
                page.wait_for_timeout(2500)
                try:
                    page.locator('#didomi-notice-agree-button').click(timeout=1000)
                except: pass
                
                lines = [l.strip() for l in page.inner_text('body').split('\n') if l.strip()]
            except Exception as e:
                print(f"Erreur d'accès à {m_url}: {e}")
                continue

            # Trouver le titre / championnat
            date_match = ""
            champ = ""
            dom = ""
            ext = ""
            s_dom = None
            s_ext = None
            date_pattern = re.compile(r"^(LUN|MAR|MER|JEU|VEN|SAM|DIM)\s+(\d{1,2})\s+([A-ZÉÛ]+)\s+(\d{4})\s*-\s*(\d{1,2}H\d{2})$", re.IGNORECASE)

            for idx, l in enumerate(lines[:30]):
                if date_pattern.match(l):
                    date_match = parse_date_to_iso(l)
                    if idx + 1 < len(lines):
                        champ = lines[idx + 1]
                    if idx + 2 < len(lines):
                        dom = lines[idx + 2]
                    if idx + 3 < len(lines) and lines[idx + 3].isdigit():
                        s_dom = int(lines[idx + 3])
                    if idx + 4 < len(lines) and lines[idx + 4].isdigit():
                        s_ext = int(lines[idx + 4])
                    if idx + 5 < len(lines):
                        ext = lines[idx + 5]
                    break

            if not dom or not ext:
                continue

            # Détecter l'équipe club
            eq_club_id = detect_equipe_club(champ)
            match_id = f"m_{eq_club_id.lower()}_{m_id_part[:20]}"
            statut = "TERMINE" if s_dom is not None else "A_VENIR"

            cur.execute("""
            INSERT OR REPLACE INTO matchs (id, equipe_club_id, competition_id, tour_ou_journee, date_heure, equipe_domicile, equipe_exterieur, score_domicile, score_exterieur, statut, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (match_id, eq_club_id, champ, "Championnat / Coupe", date_match, dom, ext, s_dom, s_ext, statut, m_url))
            scraped_matches += 1

            # Parser les événements & compositions
            current_section = "RESUME"
            current_role = "TITULAIRE"
            current_team = dom

            i = 0
            while i < len(lines):
                l = lines[i]

                if l == "COMPOSITION":
                    current_section = "COMPOSITION"
                    i += 1
                    continue
                elif l in ["TITULAIRES", "TITULAIRE"]:
                    current_role = "TITULAIRE"
                    i += 1
                    continue
                elif l in ["REMPLAÇANTS", "REMPLACANTS", "REMPLAÇANT"]:
                    current_role = "REMPLACANT"
                    i += 1
                    continue

                if current_section == "RESUME":
                    # Buts
                    if "But pour" in l:
                        eq_b = l.replace("But pour", "").strip()
                        minute = 0
                        if i - 1 >= 0 and re.match(r"^\d+’?", lines[i-1]):
                            minute = int(lines[i-1].replace("’", "").strip())
                        buteur = lines[i + 2] if i + 2 < len(lines) and lines[i+1] == "inscrit par" else ""
                        if buteur:
                            cur.execute("""
                            INSERT INTO match_events (match_id, minute, temps_additionnel, tranche_quart_heure, type_event, equipe, acteur_principal, acteur_secondaire, detail)
                            VALUES (?, ?, 0, '90', 'BUT', ?, ?, '', 'But officiel FFF')
                            """, (match_id, minute, eq_b, buteur))
                    # Cartons jaunes
                    elif "Avertissement pour" in l:
                        eq_c = l.replace("Avertissement pour", "").strip()
                        minute = 0
                        if i - 1 >= 0 and re.match(r"^\d+’?", lines[i-1]):
                            minute = int(lines[i-1].replace("’", "").strip())
                        joueur_c = lines[i + 1] if i + 1 < len(lines) else ""
                        if joueur_c:
                            cur.execute("""
                            INSERT INTO match_events (match_id, minute, temps_additionnel, tranche_quart_heure, type_event, equipe, acteur_principal, acteur_secondaire, detail)
                            VALUES (?, ?, 0, '90', 'AVERTISSEMENT', ?, ?, '', 'Carton jaune')
                            """, (match_id, minute, eq_c, joueur_c))
                    # Cartons rouges
                    elif "Expulsion pour" in l or "Exclusion pour" in l:
                        eq_c = l.replace("Expulsion pour", "").replace("Exclusion pour", "").strip()
                        minute = 0
                        if i - 1 >= 0 and re.match(r"^\d+’?", lines[i-1]):
                            minute = int(lines[i-1].replace("’", "").strip())
                        joueur_c = lines[i + 1] if i + 1 < len(lines) else ""
                        if joueur_c:
                            cur.execute("""
                            INSERT INTO match_events (match_id, minute, temps_additionnel, tranche_quart_heure, type_event, equipe, acteur_principal, acteur_secondaire, detail)
                            VALUES (?, ?, 0, '90', 'EXPULSION', ?, ?, '', 'Carton rouge')
                            """, (match_id, minute, eq_c, joueur_c))

                elif current_section == "COMPOSITION":
                    if l in ["LIEU DE LA RENCONTRE", "DÉTAIL DE L'INSTALLATION", "DETAIL DE L'INSTALLATION", "OFFICIELS", "ARBITRES", "LA FÉDÉRATION"]:
                        current_section = "FIN"
                    elif l in [dom, ext] or ("GENECH" in l.upper() and len(l) > 3):
                        current_team = l.strip().upper()
                    elif not l.isdigit() and len(l) > 4 and i + 1 < len(lines) and lines[i+1] in ["TITULAIRES", "REMPLAÇANTS", "REMPLACANTS"]:
                        current_team = l.strip().upper()

                    if l.isdigit() and i + 1 < len(lines):
                        num = int(l)
                        name = lines[i + 1]
                        if not name.isdigit() and name not in ["TITULAIRES", "REMPLAÇANTS", "REMPLACANTS", "DIRIGEANTS", "OFFICIELS", "ARBITRES"]:
                            team = current_team
                            # N'insérer que les joueurs de Genech
                            if "GENECH" in team.upper():
                                cur.execute("""
                                INSERT INTO match_lineups (match_id, equipe, numero, joueur_nom, role)
                                VALUES (?, 'GENECH ES', ?, ?, ?)
                                """, (match_id, num, name, current_role))
                                scraped_players += 1
                            i += 1

                i += 1

            conn.commit()
            print(f" -> Enregistré : {dom} {s_dom} - {s_ext} {ext} ({eq_club_id})")

        conn.close()
        browser.close()
        print(f"\n✅ Scraping terminé avec succès : {scraped_matches} nouveaux matchs et {scraped_players} entrées joueurs enregistrées !")

if __name__ == "__main__":
    run()
