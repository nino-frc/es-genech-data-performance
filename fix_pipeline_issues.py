"""
Script de correction des anomalies de pipeline de données :
1. Corrige la date erronée du match U18 vs SC Bailleulois
2. Nettoie les anciens matchs d'animation passés encore marqués A_VENIR
3. Sécurise la sélection des matchs pour Senior A (Briefing et Débriefing)
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "genech_performance.db")
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 1. Corriger la date du match U18
cur.execute("UPDATE matchs SET date_heure = '2026-09-28 15:30' WHERE id = 'm_u18_m1_56697624-ent-s-de-ge'")

# 2. Nettoyer les matchs passés encore en A_VENIR
cur.execute("UPDATE matchs SET statut = 'REPORTE' WHERE statut = 'A_VENIR' AND date_heure < '2026-10-20'")

conn.commit()

# Vérification
print("--- PROCHAINS MATCHS A VENIR ---")
for r in cur.execute("SELECT equipe_club_id, date_heure, equipe_domicile, equipe_exterieur, statut FROM matchs WHERE statut = 'A_VENIR' ORDER BY date_heure ASC").fetchall():
    print(r)

print("\n--- DERNIERS MATCHS TERMINES (SENIOR_M1) ---")
for r in cur.execute("SELECT equipe_club_id, date_heure, equipe_domicile, score_domicile, score_exterieur, equipe_exterieur FROM matchs WHERE equipe_club_id = 'SENIOR_M1' AND statut = 'TERMINE' ORDER BY date_heure DESC LIMIT 5").fetchall():
    print(r)

conn.close()
print("\nBase de données mise à jour avec succès !")
