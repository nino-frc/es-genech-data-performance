"""
Module Multi-Club : Scraping US ESQUELBECQ (521813)
- Niveau ciblé : Régional 2 - Poule A (Senior 1)
- Données isolées dans esquelbecq_performance.db (étanchéité totale)
"""

import os
import sys
import re
import sqlite3
import urllib.request
from datetime import datetime
from playwright.sync_api import sync_playwright

try:
    from playwright_stealth import Stealth
    HAS_STEALTH = True
except ImportError:
    HAS_STEALTH = False

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "esquelbecq_performance.db")
LOGO_PATH = os.path.join(BASE_DIR, "logo_esquelbecq.jpg")
PUBLIC_LOGO_PATH = os.path.join(BASE_DIR, "public", "logos", "logo_esquelbecq.jpg")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS club_info (
        code_fff TEXT PRIMARY KEY,
        nom TEXT,
        nom_court TEXT,
        ligue TEXT,
        district TEXT,
        niveau_senior TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS matchs (
        id TEXT PRIMARY KEY,
        equipe_club_id TEXT,
        competition_id TEXT,
        tour_ou_journee TEXT,
        date_heure TEXT,
        equipe_domicile TEXT,
        equipe_exterieur TEXT,
        score_domicile INTEGER,
        score_exterieur INTEGER,
        statut TEXT,
        url TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS match_lineups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id TEXT,
        equipe TEXT,
        numero INTEGER,
        joueur_nom TEXT,
        role TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS match_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id TEXT,
        minute INTEGER,
        type_event TEXT,
        equipe TEXT,
        acteur_principal TEXT,
        detail TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS classement (
        rang INTEGER,
        equipe TEXT,
        points INTEGER,
        joues INTEGER,
        gagnes INTEGER,
        nuls INTEGER,
        perdus INTEGER,
        buts_pour INTEGER,
        buts_contre INTEGER,
        diff INTEGER
    )""")
    conn.commit()
    conn.close()

def parse_date_to_iso(date_text: str) -> str:
    mois_map = {
        "JAN": "01", "FEV": "02", "FÉV": "02", "MAR": "03", "AVR": "04", "MAI": "05", "JUIN": "06",
        "JUIL": "07", "AOU": "08", "AOÛ": "08", "AOÛT": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12", "DÉC": "12"
    }
    m = re.search(r"(\d{1,2})\s+([A-ZÉÛ]{3,4})\s+(\d{4})\s*-\s*(\d{1,2})H(\d{2})", date_text, re.IGNORECASE)
    if m:
        day = f"{int(m.group(1)):02d}"
        month_raw = m.group(2).upper()[:3]
        month = mois_map.get(month_raw, "11")
        year = m.group(3)
        hour = f"{int(m.group(4)):02d}"
        minute = m.group(5)
        return f"{year}-{month}-{day} {hour}:{minute}"
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def download_logo():
    url = "https://cdn-transverse.azureedge.net/phlogos/BC521813.jpg"
    print(f"Téléchargement du logo officiel US Esquelbecq depuis {url}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            with open(LOGO_PATH, 'wb') as f:
                f.write(data)
            os.makedirs(os.path.dirname(PUBLIC_LOGO_PATH), exist_ok=True)
            with open(PUBLIC_LOGO_PATH, 'wb') as f:
                f.write(data)
        print("  -> Logo enregistré : logo_esquelbecq.jpg")
    except Exception as e:
        print(f"  -> Erreur téléchargement logo : {e}")

def scrape_esquelbecq():
    init_db()
    if not os.path.exists(LOGO_PATH):
        download_logo()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO club_info VALUES ('521813', 'U.S. ESQUELBECQ', 'US ESQUELBECQ', 'Ligue de Football des Hauts-de-France', 'District des Flandres', 'Seniors Régional 2')
    """)
    conn.commit()

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=True, args=['--disable-blink-features=AutomationControlled'])
        except Exception:
            browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800},
            locale='fr-FR',
            timezone_id='Europe/Paris'
        )
        if HAS_STEALTH:
            Stealth().apply_stealth_sync(context)
        page = context.new_page()

        # 1. Scraping Classement Régional 2 Poule A
        print("\n1. Scraping du Classement Régional 2 Poule A...")
        try:
            page.goto("https://epreuves.fff.fr/competition/club/521813-u-s-esquelbecq/equipe/2026_1813_SEM_1/classement", timeout=25000)
            page.wait_for_timeout(2500)
            try:
                page.locator('#didomi-notice-agree-button').click(timeout=1000)
            except: pass

            lines = [l.strip() for l in page.inner_text('body').split('\n') if l.strip()]
            new_standings = []
            for i, l in enumerate(lines):
                if l.isdigit() and i + 2 < len(lines):
                    try:
                        rang = int(l)
                        team_idx = i + 2 if lines[i+1].isdigit() else i + 1
                        team_name = lines[team_idx]
                        stats_line = lines[team_idx + 1] if team_idx + 1 < len(lines) else ""
                        parts = stats_line.split('\t')
                        if len(parts) >= 8 and (team_name.isupper() or "FC" in team_name or "US" in team_name or "AS" in team_name or "SC" in team_name or "OS" in team_name or "FAN" in team_name):
                            pts = int(parts[0])
                            j = int(parts[1])
                            g = int(parts[2])
                            n = int(parts[3])
                            p_loss = int(parts[4])
                            bp = int(parts[7])
                            bc = int(parts[8])
                            diff = int(parts[9])
                            new_standings.append((rang, team_name, pts, j, g, n, p_loss, bp, bc, diff))
                    except:
                        pass
            
            if len(new_standings) >= 6:
                cur.execute("DELETE FROM classement")
                for st in new_standings:
                    cur.execute("INSERT INTO classement VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", st)
                    print(f"  {st[0]}. {st[1]} - {st[2]} pts ({st[3]}j, {st[4]}V {st[5]}N {st[6]}D, {st[7]}-{st[8]})")
                conn.commit()
                print(f"Classement Esquelbecq mis à jour ({len(new_standings)} équipes).")
            else:
                print(f"Classement en ligne incomplet ({len(new_standings)} trouvées), classement préservé.")
        except Exception as e:
            print(f"Erreur scraping classement : {e}")

        # 2. Scraping Calendrier & Matchs Senior 1
        print("\n2. Scraping des Matchs Senior 1 (Régional 2 & Coupes)...")
        try:
            page.goto("https://epreuves.fff.fr/competition/club/521813-u-s-esquelbecq/equipe/2026_1813_SEM_1/calendrier_resultats", timeout=25000)
            page.wait_for_timeout(2500)
            links = page.locator('a').all()
            match_urls = []
            for l in links:
                href = l.get_attribute('href') or ''
                if '/competition/match/' in href:
                    full_url = f"https://epreuves.fff.fr{href}" if href.startswith('/') else href
                    if full_url not in match_urls:
                        match_urls.append(full_url)

            print(f"  -> {len(match_urls)} matchs trouvés pour Esquelbecq US Senior 1")

            date_pattern = re.compile(r"^(LUN|MAR|MER|JEU|VEN|SAM|DIM)\s+(\d{1,2})\s+([A-ZÉÛ]+)\s+(\d{4})\s*-\s*(\d{1,2}H\d{2})$", re.IGNORECASE)

            for m_url in match_urls[:8]:
                m_id = "esquelbecq_" + m_url.split('/match/')[-1].split('?')[0].split('-')[0]
                try:
                    page.goto(m_url, timeout=20000)
                    page.wait_for_timeout(2000)
                    m_lines = [l.strip() for l in page.inner_text('body').split('\n') if l.strip()]
                except Exception as e:
                    print(f"  Erreur accès match : {e}")
                    continue

                date_m = ""
                dom = ""
                ext = ""
                s_dom = None
                s_ext = None
                comp = "Seniors Régional 2 (Poule A)"

                for idx, l in enumerate(m_lines[:35]):
                    if date_pattern.match(l):
                        date_m = parse_date_to_iso(l)
                        if idx + 1 < len(m_lines) and ("Régional" in m_lines[idx+1] or "Coupe" in m_lines[idx+1]):
                            comp = m_lines[idx+1]
                        if idx + 2 < len(m_lines):
                            dom = m_lines[idx + 2]
                        if idx + 3 < len(m_lines) and m_lines[idx + 3].isdigit():
                            s_dom = int(m_lines[idx + 3])
                        if idx + 4 < len(m_lines) and m_lines[idx + 4].isdigit():
                            s_ext = int(m_lines[idx + 4])
                        if idx + 5 < len(m_lines):
                            ext = m_lines[idx + 5]
                        elif idx + 3 < len(m_lines) and ":" in m_lines[idx + 3]:
                            if idx + 4 < len(m_lines):
                                ext = m_lines[idx + 4]
                        break

                if not dom:
                    continue

                statut = "TERMINE" if s_dom is not None else "A_VENIR"
                if ext == "RECHERCHE" or not ext:
                    ext = "ESQUELBECQ US" if "ESQUELBECQ" not in dom.upper() else "ADVERSAIRE"

                cur.execute("""
                INSERT OR REPLACE INTO matchs (id, equipe_club_id, competition_id, tour_ou_journee, date_heure, equipe_domicile, equipe_exterieur, score_domicile, score_exterieur, statut, url)
                VALUES (?, '521813_SENIOR_M1', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (m_id, comp, "Régional 2", date_m, dom, ext, s_dom, s_ext, statut, m_url))
                conn.commit()

        except Exception as e:
            print(f"Erreur scraping matchs : {e}")

        browser.close()

    conn.close()
    print("Scraping US Esquelbecq terminé avec succès.")

if __name__ == "__main__":
    scrape_esquelbecq()
