"""
Script d'ingestion officielle du 6e Tour de Coupe de France :
ST MARTIN TATINGHEM 2 - 0 GENECH ES (Dimanche 25 Octobre 2026)
Enregistre la feuille de match FMI certifiée, les compositions, les remplacements et les buts.
"""

import os
import sqlite3

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "genech_performance.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

match_id = "cdf_t6_tatinghem_genech"

# 1. Mise à jour de la rencontre dans matchs
cur.execute("""
INSERT OR REPLACE INTO matchs (
    id, equipe_club_id, competition_id, tour_ou_journee, date_heure, 
    equipe_domicile, equipe_exterieur, score_domicile, score_exterieur, statut, url
) VALUES (
    ?, 'SENIOR_M1', 'cdf_2026', 'Tour 6 (Finale Régionale)', '2026-10-25 15:00',
    'ST MARTIN TATINGHEM', 'GENECH ES', 2, 0, 'TERMINE',
    'https://epreuves.fff.fr/competition/match/80499782-football-club-saint-martin-lez-tatinghem-ent-s-de-genech'
)
""", (match_id,))

# Supprimer les anciens événements et compos de ce match si existants
cur.execute("DELETE FROM match_events WHERE match_id = ?", (match_id,))
cur.execute("DELETE FROM match_lineups WHERE match_id = ?", (match_id,))

# 2. Ingestion des événements officiels
events = [
    (match_id, 43, 0, '31-45+\'', 'AVERTISSEMENT', 'ST MARTIN TATINGHEM', 'ETHAN TREHOUX', '', 'Carton jaune'),
    (match_id, 44, 0, '31-45+\'', 'BUT', 'ST MARTIN TATINGHEM', 'ANTHONE SOTOMSKI', '', 'But officiel FFF (1-0)'),
    (match_id, 46, 0, '46-60\'', 'REMPLACEMENT', 'ST MARTIN TATINGHEM', 'STEVEN CARPENTIER', 'KEVIN SCHRIVE', 'Remplacement'),
    (match_id, 48, 0, '46-60\'', 'REMPLACEMENT', 'GENECH ES', 'THOMAS LEONARD', 'JULIEN NISSE', 'Remplacement'),
    (match_id, 58, 0, '46-60\'', 'REMPLACEMENT', 'ST MARTIN TATINGHEM', 'AKE SEKOU CISSE', 'STEVEN CARPENTIER', 'Remplacement'),
    (match_id, 62, 0, '61-75\'', 'REMPLACEMENT', 'ST MARTIN TATINGHEM', 'FLORIAN DELATTRE', 'ETHAN TREHOUX', 'Remplacement'),
    (match_id, 62, 0, '61-75\'', 'REMPLACEMENT', 'GENECH ES', 'DANY DE FREITAS', 'GIOVANY CALON', 'Remplacement'),
    (match_id, 62, 0, '61-75\'', 'REMPLACEMENT', 'GENECH ES', 'JULES DIVERCHY', 'HUGO HERVE', 'Remplacement'),
    (match_id, 69, 0, '61-75\'', 'REMPLACEMENT', 'GENECH ES', 'ELIO DELCROIX', 'THOMAS LEONARD', 'Remplacement'),
    (match_id, 73, 0, '61-75\'', 'REMPLACEMENT', 'ST MARTIN TATINGHEM', 'ADAMA NIANE', 'ANTHONE SOTOMSKI', 'Remplacement'),
    (match_id, 83, 0, '76-90+\'', 'BUT', 'ST MARTIN TATINGHEM', 'AARON HUYSMAN', '', 'But officiel FFF (2-0)'),
    (match_id, 90, 0, '76-90+\'', 'AVERTISSEMENT', 'ST MARTIN TATINGHEM', 'FLORIAN DELATTRE', '', 'Carton jaune')
]

cur.executemany("""
INSERT INTO match_events (match_id, minute, temps_additionnel, tranche_quart_heure, type_event, equipe, acteur_principal, acteur_secondaire, detail)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", events)

# 3. Ingestion des compositions Genech ES
lineups = [
    (match_id, 'GENECH ES', 1, 'TIM LACOTE', 'TITULAIRE'),
    (match_id, 'GENECH ES', 2, 'JULIEN DEVERNAY', 'TITULAIRE'),
    (match_id, 'GENECH ES', 3, 'CLEMENT DURIEZ', 'TITULAIRE'),
    (match_id, 'GENECH ES', 4, 'MAXIME PETITPREZ', 'TITULAIRE'),
    (match_id, 'GENECH ES', 5, 'REMI DEFENIN', 'TITULAIRE'),
    (match_id, 'GENECH ES', 6, 'HUGO HERVE', 'TITULAIRE'),
    (match_id, 'GENECH ES', 7, 'JEAN PAUL BANGALA TOFIFI', 'TITULAIRE'),
    (match_id, 'GENECH ES', 8, 'MATHYS HERVE', 'TITULAIRE'),
    (match_id, 'GENECH ES', 9, 'JULIEN NISSE', 'TITULAIRE'),
    (match_id, 'GENECH ES', 10, 'GIOVANY CALON', 'TITULAIRE'),
    (match_id, 'GENECH ES', 11, 'AUGUSTIN DROUPSY', 'TITULAIRE'),
    (match_id, 'GENECH ES', 12, 'DANY DE FREITAS', 'REMPLACANT'),
    (match_id, 'GENECH ES', 13, 'ELIO DELCROIX', 'REMPLACANT'),
    (match_id, 'GENECH ES', 14, 'JULES DIVERCHY', 'REMPLACANT'),
    (match_id, 'GENECH ES', 15, 'THOMAS LEONARD', 'REMPLACANT'),
]

cur.executemany("""
INSERT INTO match_lineups (match_id, equipe, numero, joueur_nom, role)
VALUES (?, ?, ?, ?, ?)
""", lineups)

conn.commit()
print("✅ Match ST MARTIN TATINGHEM 2 - 0 GENECH ES enregistré avec succès dans la base !")
conn.close()
