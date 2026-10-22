import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "genech_performance.db")

CLUB_TEAMS = [
    # POLE SENIORS MASCULINS
    {
        "id": "SENIOR_M1",
        "code_fff": "SENIOR M1",
        "nom_affiche": "Séniors 1 (Équipe A)",
        "pole": "Séniors Masculins",
        "categorie": "Senior",
        "format_jeu": "Foot à 11",
        "championnat": "Seniors Régional 3 - POULE D",
        "niveau_data": "HAUTE_INTENSITE",
        "url_fff": "https://epreuves.fff.fr/competition/club/525674-ent-s-de-genech/equipe/2026_10330_SEM_1"
    },
    {
        "id": "SENIOR_M2",
        "code_fff": "SENIOR M2",
        "nom_affiche": "Séniors 2 (Coupe / District)",
        "pole": "Séniors Masculins",
        "categorie": "Senior",
        "format_jeu": "Foot à 11",
        "championnat": "Coupes District / Flandres",
        "niveau_data": "STANDARD",
        "url_fff": "https://epreuves.fff.fr/competition/club/525674-ent-s-de-genech/equipe/2026_10330_SEM_4"
    },
    {
        "id": "SENIOR_M3",
        "code_fff": "SENIOR M3",
        "nom_affiche": "Séniors 3 (Équipe Réserve D2)",
        "pole": "Séniors Masculins",
        "categorie": "Senior",
        "format_jeu": "Foot à 11",
        "championnat": "Seniors D2 - POULE C - PHASE 1",
        "niveau_data": "HAUTE_INTENSITE",
        "url_fff": "https://epreuves.fff.fr/competition/engagement/457579-seniors-d2/phase/1/3"
    },
    # POLE FEMININ
    {
        "id": "SENIOR_F1",
        "code_fff": "SENIOR F1",
        "nom_affiche": "Séniors Féminines 1 (Coupe HDF)",
        "pole": "Pôle Féminin",
        "categorie": "Féminine",
        "format_jeu": "Foot à 11",
        "championnat": "Coupe Hauts-De-France Féminine - POULE UNIQUE",
        "niveau_data": "STANDARD",
        "url_fff": "https://epreuves.fff.fr/competition/club/525674-ent-s-de-genech/equipe/2026_10330_SEF_15"
    },
    {
        "id": "SENIOR_F2",
        "code_fff": "SENIOR F2",
        "nom_affiche": "Séniors Féminines 2 (Interdistricts)",
        "pole": "Pôle Féminin",
        "categorie": "Féminine",
        "format_jeu": "Foot à 11",
        "championnat": "Interdistricts Féminin Niveau 1 - POULE C",
        "niveau_data": "HAUTE_INTENSITE",
        "url_fff": "https://epreuves.fff.fr/competition/club/525674-ent-s-de-genech/equipe/2026_10330_SEF_3"
    },
    # POLE FORMATION JEUNES
    {
        "id": "U19_M1",
        "code_fff": "U19 M1",
        "nom_affiche": "U19 M1 (Coupe des Flandres)",
        "pole": "Formation Jeunes",
        "categorie": "U19",
        "format_jeu": "Foot à 11",
        "championnat": "Coupe des Flandres U18 U19 - POULE A",
        "niveau_data": "STANDARD",
        "url_fff": "https://epreuves.fff.fr/competition/club/525674-ent-s-de-genech/equipe/2026_10330_U19_2"
    },
    {
        "id": "U18_M1",
        "code_fff": "U18 M1",
        "nom_affiche": "U18 M1 (18 19 D1 District)",
        "pole": "Formation Jeunes",
        "categorie": "U18",
        "format_jeu": "Foot à 11",
        "championnat": "18 19 D1 - POULE 0 - PHASE 1",
        "niveau_data": "HAUTE_INTENSITE",
        "url_fff": "https://epreuves.fff.fr/competition/engagement/457570-18-19-d1/phase/1/1"
    },
    {
        "id": "U14_M1",
        "code_fff": "U14 M1",
        "nom_affiche": "U14 M1 (14 D2 District)",
        "pole": "Formation Jeunes",
        "categorie": "U14",
        "format_jeu": "Foot à 11",
        "championnat": "14 D2 - POULE 0 - PHASE 1",
        "niveau_data": "STANDARD",
        "url_fff": "https://epreuves.fff.fr/competition/engagement/457577-14-d2/phase/1/1"
    },
    # POLE ECOLE DE FOOT (U10 - U13)
    {
        "id": "U13_M1",
        "code_fff": "U13 M1",
        "nom_affiche": "U13 M1 (Niveau 2)",
        "pole": "École de Foot",
        "categorie": "U13",
        "format_jeu": "Foot à 8",
        "championnat": "U13 Niveau 2 - POULE J - PHASE 1",
        "niveau_data": "RESULTATS_SEULS",
        "url_fff": "https://epreuves.fff.fr/competition/club/525674-ent-s-de-genech/equipe/2026_10330_U13_9"
    },
    {
        "id": "U13_M2",
        "code_fff": "U13 M2",
        "nom_affiche": "U13 M2 (Niveau 1)",
        "pole": "École de Foot",
        "categorie": "U13",
        "format_jeu": "Foot à 8",
        "championnat": "U13 Niv 1 - POULE 0 - PHASE 1",
        "niveau_data": "RESULTATS_SEULS",
        "url_fff": "https://epreuves.fff.fr/competition/club/525674-ent-s-de-genech/equipe/2026_10330_U13_11"
    },
    {
        "id": "U12_M1",
        "code_fff": "U12 M1",
        "nom_affiche": "U12 M1 (Niveau 1)",
        "pole": "École de Foot",
        "categorie": "U12",
        "format_jeu": "Foot à 8",
        "championnat": "U12 Niveau 1 - POULE O - PHASE 1",
        "niveau_data": "RESULTATS_SEULS",
        "url_fff": "https://epreuves.fff.fr/competition/club/525674-ent-s-de-genech/equipe/2026_10330_U13_8"
    },
    {
        "id": "U11_M1",
        "code_fff": "U11 M1",
        "nom_affiche": "U11 M1 (Niveau 3)",
        "pole": "École de Foot",
        "categorie": "U11",
        "format_jeu": "Foot à 8",
        "championnat": "U11 Niveau 3 - POULE H - PHASE 1",
        "niveau_data": "RESULTATS_SEULS",
        "url_fff": "https://epreuves.fff.fr/competition/club/525674-ent-s-de-genech/equipe/2026_10330_FA_7"
    },
    {
        "id": "U11_M2",
        "code_fff": "U11 M2",
        "nom_affiche": "U11 M2 (Niveau 1)",
        "pole": "École de Foot",
        "categorie": "U11",
        "format_jeu": "Foot à 8",
        "championnat": "U11 Niveau 1 - POULE K - PHASE 1",
        "niveau_data": "RESULTATS_SEULS",
        "url_fff": "https://epreuves.fff.fr/competition/club/525674-ent-s-de-genech/equipe/2026_10330_FA_6"
    },
    {
        "id": "U10_M1",
        "code_fff": "U10 M1",
        "nom_affiche": "U10 M1 (Niveau 2)",
        "pole": "École de Foot",
        "categorie": "U10",
        "format_jeu": "Foot à 8",
        "championnat": "U10 Niveau 2 - POULE Q - PHASE 1",
        "niveau_data": "RESULTATS_SEULS",
        "url_fff": "https://epreuves.fff.fr/competition/club/525674-ent-s-de-genech/equipe/2026_10330_FA_5"
    },
    # POLE VETERANS & LOISIRS
    {
        "id": "VETERAN_M1",
        "code_fff": "VETERAN M1",
        "nom_affiche": "Vétérans M1 (Niveau 2)",
        "pole": "Loisir & Vétérans",
        "categorie": "Vétéran",
        "format_jeu": "Foot à 11",
        "championnat": "Veterans A11 Niv2 - POULE B - PHASE 1",
        "niveau_data": "STANDARD",
        "url_fff": "https://epreuves.fff.fr/competition/club/525674-ent-s-de-genech/equipe/2026_10330_SEM_13"
    },
    {
        "id": "LOISIR_M1",
        "code_fff": "LOISIR M1",
        "nom_affiche": "Foot Loisirs M1",
        "pole": "Loisir & Vétérans",
        "categorie": "Loisir",
        "format_jeu": "Foot à 8",
        "championnat": "Foot Loisirs - POULE F - PHASE 1",
        "niveau_data": "RESULTATS_SEULS",
        "url_fff": "https://epreuves.fff.fr/competition/club/525674-ent-s-de-genech/equipe/2026_10330_FL_14"
    }
]

def init_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Table des 16 équipes officielles du club
    cur.execute("""
    CREATE TABLE IF NOT EXISTS equipes_club (
        id TEXT PRIMARY KEY,
        code_fff TEXT NOT NULL,
        nom_affiche TEXT NOT NULL,
        pole TEXT NOT NULL,
        categorie TEXT NOT NULL,
        format_jeu TEXT NOT NULL,
        championnat TEXT NOT NULL,
        niveau_data TEXT NOT NULL,
        url_fff TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS competitions (
        id TEXT PRIMARY KEY,
        nom TEXT NOT NULL,
        type TEXT NOT NULL, -- 'CHAMPIONNAT', 'COUPE_DE_FRANCE', 'COUPE_DISTRICT', 'CRITERIUM'
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
        equipe_club_id TEXT DEFAULT 'SENIOR_M1',
        competition_id TEXT NOT NULL,
        tour_ou_journee TEXT NOT NULL,
        date_heure TEXT,
        equipe_domicile TEXT NOT NULL,
        equipe_exterieur TEXT NOT NULL,
        score_domicile INTEGER,
        score_exterieur INTEGER,
        statut TEXT DEFAULT 'TERMINE', -- 'TERMINE', 'A_VENIR'
        url TEXT,
        FOREIGN KEY (equipe_club_id) REFERENCES equipes_club(id),
        FOREIGN KEY (competition_id) REFERENCES competitions(id)
    );
    """)

    # Vérifier si equipe_club_id existe dans matchs (migration transparente)
    cur.execute("PRAGMA table_info(matchs);")
    cols = [c[1] for c in cur.fetchall()]
    if "equipe_club_id" not in cols:
        cur.execute("ALTER TABLE matchs ADD COLUMN equipe_club_id TEXT DEFAULT 'SENIOR_M1';")

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
        equipe_club_id TEXT DEFAULT 'SENIOR_M1',
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
        FOREIGN KEY (equipe_club_id) REFERENCES equipes_club(id),
        FOREIGN KEY (competition_id) REFERENCES competitions(id)
    );
    """)

    # Insertion / mise à jour des 16 équipes officielles
    for t in CLUB_TEAMS:
        cur.execute("""
        INSERT OR REPLACE INTO equipes_club (id, code_fff, nom_affiche, pole, categorie, format_jeu, championnat, niveau_data, url_fff)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (t["id"], t["code_fff"], t["nom_affiche"], t["pole"], t["categorie"], t["format_jeu"], t["championnat"], t["niveau_data"], t["url_fff"]))

    conn.commit()
    conn.close()
    print(f"Base de données multi-équipes initialisée avec succès : {len(CLUB_TEAMS)} équipes enregistrées !")

if __name__ == "__main__":
    init_db()
