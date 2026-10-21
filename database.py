import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "genech_performance.db")

def init_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS competitions (
        id TEXT PRIMARY KEY,
        nom TEXT NOT NULL,
        type TEXT NOT NULL, -- 'CHAMPIONNAT', 'COUPE_DE_FRANCE', 'AMICAL'
        saison TEXT NOT NULL,
        url TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS equipes (
        id TEXT PRIMARY KEY,
        nom TEXT NOT NULL,
        club_numero TEXT,
        ville TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS matchs (
        id TEXT PRIMARY KEY,
        competition_id TEXT NOT NULL,
        tour_ou_journee TEXT NOT NULL,
        date_heure TEXT,
        equipe_domicile TEXT NOT NULL,
        equipe_exterieur TEXT NOT NULL,
        score_domicile INTEGER,
        score_exterieur INTEGER,
        statut TEXT DEFAULT 'TERMINE', -- 'TERMINE', 'A_VENIR'
        url TEXT,
        FOREIGN KEY (competition_id) REFERENCES competitions(id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS match_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id TEXT NOT NULL,
        minute INTEGER NOT NULL,
        temps_additionnel INTEGER DEFAULT 0,
        tranche_quart_heure TEXT NOT NULL,
        type_event TEXT NOT NULL, -- 'BUT', 'AVERTISSEMENT', 'EXPULSION', 'CHANGEMENT'
        equipe TEXT NOT NULL,
        acteur_principal TEXT NOT NULL,
        acteur_secondaire TEXT,
        detail TEXT,
        FOREIGN KEY (match_id) REFERENCES matchs(id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS match_lineups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id TEXT NOT NULL,
        equipe TEXT NOT NULL,
        numero INTEGER,
        joueur_nom TEXT NOT NULL,
        role TEXT NOT NULL, -- 'TITULAIRE', 'REMPLACANT', 'STAFF'
        FOREIGN KEY (match_id) REFERENCES matchs(id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS classement_poule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        competition_id TEXT NOT NULL,
        rang INTEGER NOT NULL,
        equipe_nom TEXT NOT NULL,
        points INTEGER NOT NULL,
        joues INTEGER NOT NULL,
        victoires INTEGER NOT NULL,
        nuls INTEGER NOT NULL,
        defaites INTEGER NOT NULL,
        buts_pour INTEGER NOT NULL,
        buts_contre INTEGER NOT NULL,
        diff INTEGER NOT NULL,
        FOREIGN KEY (competition_id) REFERENCES competitions(id)
    );
    """)

    conn.commit()
    conn.close()
    print(f"Database initialized at: {db_path}")

if __name__ == "__main__":
    init_db()
