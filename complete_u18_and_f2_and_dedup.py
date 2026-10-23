"""
Script d'enrichissement U18, Féminines F2 et Déduplication Globale
1. Nettoie les 19 matchs en double (anciens IDs club_...)
2. Scrape l'intégralité des 7 matchs U18 et des 4 matchs Féminines F2
3. Insère les compositions, joueuses/joueurs et buteurs officiels FFF
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

def cleanup_duplicates():
    print("--- 1. NETTOYAGE DES DOUBLONS DE MATCHS ---")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Trouver les doublons basés sur (date_heure, equipe_domicile, equipe_exterieur)
    # Si on a un match 'm_...' et un match 'club_...', on garde 'm_...' (qui contient les compos)
    dups = cur.execute("""
        SELECT date_heure, equipe_domicile, equipe_exterieur, count(*) 
        FROM matchs 
        GROUP BY date_heure, equipe_domicile, equipe_exterieur 
        HAVING count(*) > 1
    """).fetchall()

    deleted_count = 0
    for d in dups:
        date_h, dom, ext, cnt = d
        rows = cur.execute("SELECT id FROM matchs WHERE date_heure = ? AND equipe_domicile = ? AND equipe_exterieur = ?", (date_h, dom, ext)).fetchall()
        row_ids = [r[0] for r in rows]
        # Garder celui qui a des compositions ou celui qui commence par 'm_'
        keep_id = None
        for r_id in row_ids:
            lineups_cnt = cur.execute("SELECT count(*) FROM match_lineups WHERE match_id = ?", (r_id,)).fetchone()[0]
            if lineups_cnt > 0:
                keep_id = r_id
                break
        if not keep_id:
            # Garder le premier qui commence par m_
            for r_id in row_ids:
                if r_id.startswith('m_'):
                    keep_id = r_id
                    break
        if not keep_id:
            keep_id = row_ids[0]

        # Supprimer les autres
        for r_id in row_ids:
            if r_id != keep_id:
                cur.execute("DELETE FROM matchs WHERE id = ?", (r_id,))
                cur.execute("DELETE FROM match_lineups WHERE match_id = ?", (r_id,))
                cur.execute("DELETE FROM match_events WHERE match_id = ?", (r_id,))
                deleted_count += 1

    conn.commit()
    print(f"✅ {deleted_count} matchs en double supprimés avec succès !")
    conn.close()

def scrape_match_page(page, m_url, eq_club_id, comp_name, conn):
    cur = conn.cursor()
    m_id_part = m_url.split('/match/')[-1].split('?')[0]
    match_id = f"m_{eq_club_id.lower()}_{m_id_part[:20]}"

    print(f"Scraping [{eq_club_id}] {m_url}...")
    try:
        page.goto(m_url, wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(2500)
        try:
            page.locator('#didomi-notice-agree-button').click(timeout=1000)
        except: pass
        lines = [l.strip() for l in page.inner_text('body').split('\n') if l.strip()]
    except Exception as e:
        print(f"  Erreur accès {m_url}: {e}")
        return

    date_match = ""
    dom = ""
    ext = ""
    s_dom = None
    s_ext = None
    date_pattern = re.compile(r"^(LUN|MAR|MER|JEU|VEN|SAM|DIM)\s+(\d{1,2})\s+([A-ZÉÛ]+)\s+(\d{4})\s*-\s*(\d{1,2}H\d{2})$", re.IGNORECASE)

    for idx, l in enumerate(lines[:35]):
        if date_pattern.match(l):
            date_match = parse_date_to_iso(l)
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
        # Essayer un autre format pour les matchs à venir (13:00 au lieu de score)
        for idx, l in enumerate(lines[:35]):
            if date_pattern.match(l):
                date_match = parse_date_to_iso(l)
                if idx + 2 < len(lines):
                    dom = lines[idx + 2]
                if idx + 3 < len(lines) and ":" in lines[idx + 3]:
                    # Match à venir
                    s_dom = None
                    s_ext = None
                    if idx + 4 < len(lines):
                        ext = lines[idx + 4]
                break

    if not dom or not ext:
        print(f"  Impossible d'extraire dom/ext pour {m_url}")
        return

    statut = "TERMINE" if s_dom is not None else "A_VENIR"

    # Supprimer d'abord si existant
    cur.execute("DELETE FROM matchs WHERE id = ?", (match_id,))
    cur.execute("DELETE FROM match_lineups WHERE match_id = ?", (match_id,))
    cur.execute("DELETE FROM match_events WHERE match_id = ?", (match_id,))

    cur.execute("""
    INSERT OR REPLACE INTO matchs (id, equipe_club_id, competition_id, tour_ou_journee, date_heure, equipe_domicile, equipe_exterieur, score_domicile, score_exterieur, statut, url)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (match_id, eq_club_id, comp_name, "Championnat", date_match, dom, ext, s_dom, s_ext, statut, m_url))

    # Parser compositions & événements
    current_section = "RESUME"
    current_role = "TITULAIRE"
    current_team = dom

    i = 0
    p_count = 0
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
                    if "GENECH" in team.upper():
                        cur.execute("""
                        INSERT INTO match_lineups (match_id, equipe, numero, joueur_nom, role)
                        VALUES (?, 'GENECH ES', ?, ?, ?)
                        """, (match_id, num, name, current_role))
                        p_count += 1
                    i += 1

        i += 1

    conn.commit()
    print(f"  -> Enregistré : {dom} {s_dom} - {s_ext} {ext} ({p_count} joueurs)")

def run_enrichment():
    cleanup_duplicates()

    print("\n--- 2. SCRAPING COMPLET FÉMININES F2 & U18 ---")
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

        conn = sqlite3.connect(DB_PATH)

        # 1. Matches Féminines F2
        f2_matches = [
            "https://epreuves.fff.fr/competition/match/78809049-ent-s-de-genech-summer-c-valenciennes",
            "https://epreuves.fff.fr/competition/match/78809056-u-s-municipale-marly-ent-s-de-genech",
            "https://epreuves.fff.fr/competition/match/78809061-ent-s-de-genech-u-s-de-phalempin",
            "https://epreuves.fff.fr/competition/match/78809066-lille-e-s-louviere-pellevoisin-ent-s-de-genech"
        ]
        print(f"\nCollecte des {len(f2_matches)} matchs Féminines F2 (Interdistricts)...")
        for url in f2_matches:
            scrape_match_page(page, url, "SENIOR_F2", "Interdistricts Féminin Niveau 1", conn)

        # 2. Matches U18
        u18_matches = [
            "https://epreuves.fff.fr/competition/match/79494778-ent-s-de-genech-marquette-football-flandres",
            "https://epreuves.fff.fr/competition/match/79496282-et-c-anstaing-chereng-ent-s-de-genech",
            "https://epreuves.fff.fr/competition/match/79395742-ent-s-de-genech-f-c-linsellois",
            "https://epreuves.fff.fr/competition/match/79493649-ent-s-de-genech-pevele-football-club",
            "https://epreuves.fff.fr/competition/match/79494364-u-s-antillais-lille-metropole-ent-s-de-genech",
            "https://epreuves.fff.fr/competition/match/56697624-ent-s-de-genech-s-c-bailleulois",
            "https://epreuves.fff.fr/competition/match/79497787-et-am-c-cysoing-wannehain-bourgh-ent-s-de-genech"
        ]
        print(f"\nCollecte des {len(u18_matches)} matchs U18...")
        for url in u18_matches:
            scrape_match_page(page, url, "U18_M1", "18 19 D1 - District", conn)

        conn.close()
        browser.close()
        print("\n✅ Enrichissement terminé avec succès !")

if __name__ == "__main__":
    run_enrichment()
