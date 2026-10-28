"""
Module de démonstration Multi-Club : Scraping US LESQUIN (500426)
- Niveau ciblé : Seniors Régional 2 (Senior A)
- Données 100% isolées dans lesquin_performance.db
"""

import os
import sys
import re
import sqlite3
import urllib.request
from datetime import datetime
from playwright.sync_api import sync_playwright

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "lesquin_performance.db")
LOGO_PATH_ROOT = os.path.join(BASE_DIR, "logo_lesquin.jpg")
LOGO_PATH_PUBLIC = os.path.join(BASE_DIR, "public", "logos", "logo_lesquin.jpg")

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

def download_logo():
    url = "https://cdn-transverse.azureedge.net/phlogos/BC500426.jpg"
    print(f"Téléchargement du logo officiel US Lesquin depuis {url}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            with open(LOGO_PATH_ROOT, 'wb') as f:
                f.write(data)
            os.makedirs(os.path.dirname(LOGO_PATH_PUBLIC), exist_ok=True)
            with open(LOGO_PATH_PUBLIC, 'wb') as f:
                f.write(data)
        print("  -> Logo enregistré : logo_lesquin.jpg et public/logos/logo_lesquin.jpg")
    except Exception as e:
        print(f"  -> Erreur téléchargement logo : {e}")

def scrape_lesquin():
    init_db()
    download_logo()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO club_info VALUES ('500426', 'U.S. LESQUINOISE', 'US LESQUIN', 'Ligue des Hauts-de-France', 'District des Flandres', 'Seniors Régional 2')
    """)
    conn.commit()

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=True, args=['--disable-blink-features=AutomationControlled'])
        except Exception:
            browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()

        # Navigation initiale pour cookies
        page.goto("https://epreuves.fff.fr/competition/club/500426-u-s-lesquinoise/equipe/2026_511_SEM_1/calendrier_resultats", timeout=30000)
        page.wait_for_timeout(3000)
        try:
            page.locator('#didomi-notice-agree-button').click(timeout=1000)
        except: pass

        # 1. Scraping Classement Régional 2
        print("\n1. Scraping du Classement Régional 2...")
        page.goto("https://epreuves.fff.fr/competition/club/500426-u-s-lesquinoise/equipe/2026_511_SEM_1/classement", timeout=30000)
        page.wait_for_timeout(3000)

        cur.execute("DELETE FROM classement")
        lines = [l.strip() for l in page.inner_text('body').split('\n') if l.strip()]
        for i, l in enumerate(lines):
            if l.isdigit() and i + 2 < len(lines):
                try:
                    rang = int(l)
                    team_idx = i + 2 if lines[i+1].isdigit() else i + 1
                    team_name = lines[team_idx]
                    stats_line = lines[team_idx + 1] if team_idx + 1 < len(lines) else ""
                    parts = stats_line.split('\t')
                    if len(parts) >= 8 and (team_name.isupper() or "FC" in team_name or "US" in team_name or "FIC" in team_name or "IC" in team_name):
                        pts = int(parts[0])
                        j = int(parts[1])
                        g = int(parts[2])
                        n = int(parts[3])
                        p_loss = int(parts[4])
                        bp = int(parts[7])
                        bc = int(parts[8])
                        diff = int(parts[9])
                        cur.execute("INSERT INTO classement VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                    (rang, team_name, pts, j, g, n, p_loss, bp, bc, diff))
                        print(f"  {rang}. {team_name} - {pts} pts ({j}j, {g}V {n}N {p_loss}D, {bp}-{bc})")
                except:
                    pass
        conn.commit()

        # 2. Scraping Calendrier & Matchs US Lesquin Senior 1
        print("\n2. Scraping des Matchs Senior 1 (Régional 2 & Coupes)...")
        page.goto("https://epreuves.fff.fr/competition/club/500426-u-s-lesquinoise/equipe/2026_511_SEM_1/calendrier_resultats", timeout=30000)
        page.wait_for_timeout(3000)
        links = page.locator('a[href*="/competition/match/"]').all()
        match_urls = []
        for l in links:
            href = l.get_attribute('href') or ''
            full_url = f"https://epreuves.fff.fr{href}" if href.startswith('/') else href
            if full_url not in match_urls:
                match_urls.append(full_url)

        print(f"  -> {len(match_urls)} matchs trouvés pour US Lesquin Senior 1")

        date_pattern = re.compile(r"^(LUN|MAR|MER|JEU|VEN|SAM|DIM)\s+(\d{1,2})\s+([A-ZÉÛ]+)\s+(\d{4})\s*-\s*(\d{1,2}H\d{2})$", re.IGNORECASE)

        for m_url in match_urls:
            raw_id = m_url.split('/match/')[-1].split('?')[0].split('-')[0]
            m_id = "lesquin_" + raw_id
            print(f"Scraping match : {m_url}...")
            try:
                page.goto(m_url, timeout=25000)
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
            comp = "Seniors Régional 2"
            tour_ou_j = "Journée"

            for idx, l in enumerate(m_lines[:35]):
                if date_pattern.match(l):
                    date_m = parse_date_to_iso(l)
                    if idx + 1 < len(m_lines):
                        nxt = m_lines[idx+1]
                        if "Régional" in nxt or "Coupe" in nxt or "Tour" in nxt or "Journée" in nxt:
                            comp = nxt
                            if " - " in nxt:
                                parts = nxt.split(" - ")
                                comp = parts[0].strip()
                                tour_ou_j = parts[1].strip()
                    if idx + 2 < len(m_lines):
                        dom = m_lines[idx + 2]
                    if idx + 3 < len(m_lines) and m_lines[idx + 3].isdigit():
                        s_dom = int(m_lines[idx + 3])
                    if idx + 4 < len(m_lines) and m_lines[idx + 4].isdigit():
                        s_ext = int(m_lines[idx + 4])
                    if idx + 5 < len(m_lines):
                        ext = m_lines[idx + 5]
                    elif idx + 3 < len(m_lines) and ":" in m_lines[idx + 3]:
                        # Match à venir
                        if idx + 4 < len(m_lines):
                            ext = m_lines[idx + 4]
                    break

            if not dom:
                continue

            statut = "TERMINE" if s_dom is not None else "A_VENIR"
            if ext == "RECHERCHE" or not ext:
                ext = "US LESQUIN" if "LESQUIN" not in dom.upper() else "ADVERSAIRE"

            cur.execute("""
            INSERT OR REPLACE INTO matchs (id, equipe_club_id, competition_id, tour_ou_journee, date_heure, equipe_domicile, equipe_exterieur, score_domicile, score_exterieur, statut, url)
            VALUES (?, 'SENIOR_M1', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (m_id, comp, tour_ou_j, date_m, dom, ext, s_dom, s_ext, statut, m_url))

            # Parser compos & événements
            current_sec = "RESUME"
            current_role = "TITULAIRE"
            curr_team = dom
            p_cnt = 0

            # Supprimer anciens events/lineups pour ce match
            cur.execute("DELETE FROM match_lineups WHERE match_id = ?", (m_id,))
            cur.execute("DELETE FROM match_events WHERE match_id = ?", (m_id,))

            for j, line in enumerate(m_lines):
                if line == "COMPOSITION":
                    current_sec = "COMPOSITION"
                    continue
                elif line in ["TITULAIRES", "TITULAIRE"]:
                    current_role = "TITULAIRE"
                    continue
                elif line in ["REMPLAÇANTS", "REMPLACANTS"]:
                    current_role = "REMPLACANT"
                    continue
                elif line in ["OFFICIELS", "ARBITRES", "LIEU DE LA RENCONTRE"]:
                    current_sec = "FIN"
                    continue

                if current_sec == "RESUME":
                    if "But pour" in line:
                        eq_b = line.replace("But pour", "").strip()
                        min_b = 0
                        if j - 1 >= 0 and re.match(r"^\d+’?", m_lines[j-1]):
                            min_b = int(m_lines[j-1].replace("’", "").strip())
                        buteur = m_lines[j + 2] if j + 2 < len(m_lines) and m_lines[j+1] == "inscrit par" else ""
                        if buteur:
                            cur.execute("INSERT INTO match_events (match_id, minute, type_event, equipe, acteur_principal, detail) VALUES (?, ?, 'BUT', ?, ?, 'But FFF')",
                                        (m_id, min_b, eq_b, buteur))
                    elif "Avertissement pour" in line:
                        eq_c = line.replace("Avertissement pour", "").strip()
                        min_c = 0
                        if j - 1 >= 0 and re.match(r"^\d+’?", m_lines[j-1]):
                            min_c = int(m_lines[j-1].replace("’", "").strip())
                        joueur_c = m_lines[j + 1] if j + 1 < len(m_lines) else ""
                        if joueur_c:
                            cur.execute("INSERT INTO match_events (match_id, minute, type_event, equipe, acteur_principal, detail) VALUES (?, ?, 'AVERTISSEMENT', ?, ?, 'Carton jaune')",
                                        (m_id, min_c, eq_c, joueur_c))
                    elif "Expulsion pour" in line:
                        eq_r = line.replace("Expulsion pour", "").strip()
                        min_r = 0
                        if j - 1 >= 0 and re.match(r"^\d+’?", m_lines[j-1]):
                            min_r = int(m_lines[j-1].replace("’", "").strip())
                        joueur_r = m_lines[j + 1] if j + 1 < len(m_lines) else ""
                        if joueur_r:
                            cur.execute("INSERT INTO match_events (match_id, minute, type_event, equipe, acteur_principal, detail) VALUES (?, ?, 'EXPULSION', ?, ?, 'Carton rouge')",
                                        (m_id, min_r, eq_r, joueur_r))

                elif current_sec == "COMPOSITION":
                    if "LESQUIN" in line.upper():
                        curr_team = "US LESQUIN"
                    elif dom.upper() in line.upper():
                        curr_team = dom
                    elif ext.upper() in line.upper():
                        curr_team = ext
                    elif line.isdigit() and j + 1 < len(m_lines):
                        num = int(line)
                        pname = m_lines[j + 1]
                        if not pname.isdigit() and pname not in ["TITULAIRES", "REMPLAÇANTS", "OFFICIELS", "ARBITRES", "LIEU DE LA RENCONTRE"]:
                            cur.execute("INSERT INTO match_lineups (match_id, equipe, numero, joueur_nom, role) VALUES (?, ?, ?, ?, ?)",
                                        (m_id, curr_team, num, pname, current_role))
                            if curr_team == "US LESQUIN":
                                p_cnt += 1

            conn.commit()
            print(f"  -> {dom} {s_dom} - {s_ext} {ext} ({p_cnt} joueurs Lesquin enregistrés)")

        conn.close()
        browser.close()
        print("\n✅ US Lesquin prêt à 100% dans lesquin_performance.db !")

if __name__ == "__main__":
    scrape_lesquin()
