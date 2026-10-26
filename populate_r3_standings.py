"""
Peuple la table classement_poule avec les données officielles FFF certifiées R3 Poule D
"""

import os
import sqlite3

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "genech_performance.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("DELETE FROM classement_poule WHERE competition_id = 'r3_poule_d'")

standings = [
    (1, "BEUVRY LA FORET AS", 10, 4, 3, 1, 0, 9, 6, 3, "509214"),
    (2, "ANICHE SC", 8, 4, 2, 2, 0, 7, 3, 4, "500588"),
    (3, "GENECH ES", 8, 4, 2, 2, 0, 6, 3, 3, "525674"),
    (4, "HENIN BEAUMONT O.", 7, 4, 2, 1, 1, 11, 4, 7, "500472"),
    (5, "ANSTAING CHERENG EC", 6, 4, 1, 3, 0, 8, 3, 5, "500889"),
    (6, "BONDUES FC 2", 6, 4, 2, 0, 2, 11, 8, 3, "500908"),
    (7, "VALENCIENNES SUMMER", 6, 4, 2, 0, 2, 7, 9, -2, "582496"),
    (8, "MAUBEUGE US 2", 5, 4, 1, 2, 1, 6, 6, 0, "500130"),
    (9, "BAVAY US", 3, 4, 0, 3, 1, 1, 3, -2, "500732"),
    (10, "GUESNAIN SC", 2, 4, 0, 2, 2, 2, 5, -3, "500994"),
    (11, "CYSOING WB EAC", 1, 4, 0, 1, 3, 5, 17, -12, "500886"),
    (12, "AUBY US", 0, 4, 0, 1, 3, 4, 10, -6, "500742"),
]

for s in standings:
    rang, eq, pts, j, v, n, d, bp, bc, diff, code_fff = s
    logo_url = f"https://cdn-transverse.azureedge.net/phlogos/BC{code_fff}.jpg"
    cur.execute("""
    INSERT INTO classement_poule (competition_id, rang, equipe_nom, points, joues, victoires, nuls, defaites, buts_pour, buts_contre, diff)
    VALUES ('r3_poule_d', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (rang, eq, pts, j, v, n, d, bp, bc, diff))

conn.commit()
print("Table classement_poule mise à jour avec 12 équipes officielles !")
conn.close()
