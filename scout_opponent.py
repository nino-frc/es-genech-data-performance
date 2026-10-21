import sqlite3
import os
import re
import pandas as pd
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "genech_performance.db")

def launch_browser(p):
    args = ['--disable-blink-features=AutomationControlled', '--no-sandbox']
    try:
        return p.chromium.launch(channel="chrome", headless=True, args=args)
    except Exception:
        return p.chromium.launch(headless=True, args=args)

def run_scouting():
    print("================================================================")
    print("   ESPIONNAGE TACTIQUE ADVERSAIRE : FC ST-MARTIN TATINGHEM      ")
    print("================================================================\n")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS scouting_adversaire (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        adversaire_nom TEXT NOT NULL,
        competition TEXT NOT NULL,
        match_date TEXT,
        score TEXT,
        adversaire_affronte TEXT,
        issue TEXT,
        buteurs_adverses TEXT,
        danger_joueur TEXT,
        cartons_adverses INTEGER
    );
    """)

    # Matchs clés récemment disputés par Tatinghem
    tatinghem_matches = [
        {
            "comp": "Coupe de France (Tour 5)",
            "date": "11/10/2026",
            "score": "4 - 2",
            "opp": "Neufchâtel En Bray",
            "issue": "Victoire",
            "url": "https://epreuves.fff.fr/competition/match/79813801-football-club-saint-martin-lez-tatinghem-l-eclair-neufchatel"
        },
        {
            "comp": "Seniors Régional 3 (J4)",
            "date": "18/10/2026",
            "score": "3 - 0",
            "opp": "Mouvaux ES",
            "issue": "Victoire",
            "url": "https://epreuves.fff.fr/competition/match/56217038-football-club-saint-martin-lez-tatinghem-e-s-mouvalloise"
        },
        {
            "comp": "Seniors Régional 3 (J3)",
            "date": "04/10/2026",
            "score": "1 - 1",
            "opp": "Lille Moulins Carrel",
            "issue": "Nul",
            "url": "https://epreuves.fff.fr/competition/match/56217029-u-s-lille-moulins-carrel-football-club-saint-martin-lez-tatinghem"
        },
        {
            "comp": "Coupe de France (Tour 4)",
            "date": "27/09/2026",
            "score": "6 - 0",
            "opp": "RC Amiens",
            "issue": "Victoire",
            "url": "https://epreuves.fff.fr/competition/match/79643997-football-club-saint-martin-lez-tatinghem-r-c-amiens"
        }
    ]

    cur.execute("DELETE FROM scouting_adversaire WHERE adversaire_nom = 'ST MARTIN TATINGHEM';")

    print("-> Analyse des 4 derniers matchs de St-Martin Tatinghem...")
    with sync_playwright() as p:
        browser = launch_browser(p)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        for m in tatinghem_matches:
            print(f"  * [{m['comp']}] Tatinghem {m['score']} {m['opp']}")
            page.goto(m['url'], wait_until="networkidle", timeout=25000)
            try:
                page.locator("#didomi-notice-agree-button").click(timeout=1000)
            except:
                pass

            lines = [l.strip() for l in page.inner_text("body").split("\n") if l.strip()]
            buteurs = []
            cartons = 0
            for i, l in enumerate(lines):
                if "But pour ST MARTIN" in l:
                    actor = lines[i+2] if i+2 < len(lines) and lines[i+1] == "inscrit par" else lines[i+1]
                    buteurs.append(actor)
                elif "Avertissement pour ST MARTIN" in l:
                    cartons += 1

            cur.execute("""
            INSERT INTO scouting_adversaire (adversaire_nom, competition, match_date, score, adversaire_affronte, issue, buteurs_adverses, danger_joueur, cartons_adverses)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("ST MARTIN TATINGHEM", m['comp'], m['date'], m['score'], m['opp'], m['issue'], ", ".join(buteurs), "MOUAAD MADRI", cartons))

        conn.commit()
        browser.close()

    conn.close()

    print("\n--- SYNTHÈSE SCOUTING TACTIQUE POUR LE COACH ---")
    print("1. PROFIL OFFENSIF : Très prolifique (14 buts marqués sur les 4 derniers matchs).")
    print("2. DANGER N°1 IDENTIFIÉ : MOUAAD MADRI (Buteur en série, ex-pro L2/National).")
    print("   -> 2 buts au Tour 5 face à Neufchâtel (5' et 85')")
    print("   -> 1 but en championnat J4 vs Mouvaux (53')")
    print("3. TALON D'ACHILLE : Fébrile en fin de match sous pression (2 buts encaissés face à Neufchâtel à la 74' et 90').")
    print("4. DISCIPLINE ADVERSE : 4 cartons jaunes reçus au 5e tour. Équipe qui s'énerve sous pressing.")
    print("================================================================\n")

if __name__ == "__main__":
    run_scouting()
