"""
Scraper Multi-Équipes Club - ES Genech (FFF #525674)
Récupère les résultats et calendriers de l'ensemble des 16 équipes du club
depuis la plateforme officielle FFF.
"""

import os
import sys
import re
import sqlite3
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
    # Ex: SAM 03 OCT 2026 - 13H00 -> 2026-10-03 13:00
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

def scrape_all_club_teams():
    print("======================================================================")
    print("🌐 SCRAPING GLOBAL CLUB ES GENECH — 16 ÉQUIPES OFFICIELLES (FFF #525674)")
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

        url = "https://www.fff.fr/competition/club/525674-ent-s-de-genech/equipes.html"
        print(f"Connexion à la page FFF du club : {url}...")
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        try:
            page.locator('#didomi-notice-agree-button').click(timeout=1500)
        except Exception:
            pass
        page.wait_for_timeout(2000)

        lines = [l.strip() for l in page.inner_text('body').split('\n') if l.strip()]
        date_pattern = re.compile(r"^(LUN|MAR|MER|JEU|VEN|SAM|DIM)\s+(\d{1,2})\s+([A-ZÉÛ]+)\s+(\d{4})\s*-\s*(\d{1,2}H\d{2})$", re.IGNORECASE)

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        matches_count = 0
        i = 0
        while i < len(lines):
            line = lines[i]
            m_date = date_pattern.match(line)
            if m_date and i + 4 < len(lines):
                raw_date = line
                iso_date = parse_date_to_iso(raw_date)
                champ = lines[i + 1]
                dom = lines[i + 2]
                
                eq_club_id = detect_equipe_club(champ)

                # Cas 1: Match terminé
                if lines[i + 3].isdigit() and i + 5 < len(lines) and lines[i + 4].isdigit():
                    s_dom = int(lines[i + 3])
                    s_ext = int(lines[i + 4])
                    ext = lines[i + 5]
                    statut = "TERMINE"
                    
                    match_id = f"club_{eq_club_id.lower()}_{iso_date[:10].replace('-', '')}_{dom[:3].lower()}_{ext[:3].lower()}"
                    cur.execute("""
                    INSERT OR REPLACE INTO matchs (id, equipe_club_id, competition_id, tour_ou_journee, date_heure, equipe_domicile, equipe_exterieur, score_domicile, score_exterieur, statut, url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (match_id, eq_club_id, champ, "Championnat / Coupe", iso_date, dom, ext, s_dom, s_ext, statut, url))
                    matches_count += 1
                    i += 6
                    continue
                # Cas 2: Match à venir
                elif "VS" in lines[i + 3].upper() and i + 4 < len(lines):
                    ext = lines[i + 4]
                    statut = "A_VENIR"
                    match_id = f"club_{eq_club_id.lower()}_{iso_date[:10].replace('-', '')}_{dom[:3].lower()}_{ext[:3].lower()}"
                    cur.execute("""
                    INSERT OR REPLACE INTO matchs (id, equipe_club_id, competition_id, tour_ou_journee, date_heure, equipe_domicile, equipe_exterieur, score_domicile, score_exterieur, statut, url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (match_id, eq_club_id, champ, "Championnat / Coupe", iso_date, dom, ext, None, None, statut, url))
                    matches_count += 1
                    i += 5
                    continue
                # Cas 3: Forfait
                elif "FORFAIT" in lines[i + 3].upper() and i + 4 < len(lines):
                    ext = lines[i + 5] if i + 5 < len(lines) else lines[i + 4]
                    statut = "FORFAIT"
                    match_id = f"club_{eq_club_id.lower()}_{iso_date[:10].replace('-', '')}_{dom[:3].lower()}_{ext[:3].lower()}"
                    cur.execute("""
                    INSERT OR REPLACE INTO matchs (id, equipe_club_id, competition_id, tour_ou_journee, date_heure, equipe_domicile, equipe_exterieur, score_domicile, score_exterieur, statut, url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (match_id, eq_club_id, champ, "Championnat / Coupe", iso_date, dom, ext, None, None, statut, url))
                    matches_count += 1
                    i += 6
                    continue

            i += 1

        conn.commit()
        conn.close()
        browser.close()
        print(f"✅ Scraping terminé : {matches_count} matchs officiels multi-équipes enregistrés en base !")

if __name__ == "__main__":
    scrape_all_club_teams()
