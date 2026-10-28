import sqlite3
import pandas as pd
import os

DB_PATH = 'C:/Users/ninof/.gemini/antigravity/scratch/genech_data_performance/genech_performance.db'
OUTPUT_DIR = 'C:/Users/ninof/.gemini/antigravity/scratch/genech_data_performance/exports_powerbi'

NAME_MAPPING = {
    "ELIO D.": "ELIO DELCROIX",
    "MATHYS H.": "MATHYS HERVE",
    "GASPARD D.": "GASPARD DROUPSY",
    "AUGUSTIN D.": "AUGUSTIN DROUPSY",
    "HUGO H.": "HUGO HERVE",
    "JULIEN D.": "JULIEN DEVERNAY",
    "JULIEN N.": "JULIEN NISSE",
    "MAXIME P.": "MAXIME PETIT",
    "MAXIME PETITPREZ": "MAXIME PETIT",
    "REMI D.": "REMI DEFENIN",
    "REMI DELOBEL": "REMI DEFENIN",
    "GIOVANY C.": "GIOVANY CALON",
    "GIOVANY CLERY": "GIOVANY CALON",
    "CLEMENT D.": "CLEMENT DURIEZ",
    "CLEMENT DELELIS": "CLEMENT DURIEZ",
    "TIM L.": "TIM LACOTE",
    "TIM LECLERCQ": "TIM LACOTE",
    "THOMAS L.": "THOMAS LEONARD",
    "ARTHUR C.": "ARTHUR CLIQUE",
    "JEAN PAUL B.": "JEAN PAUL BANGALA TOFIFI",
    "DANY D.": "DANY DE FREITAS",
    "JULES D.": "JULES DIVERCHY",
    "MATEO S.": "MATEO SURMONT",
    "ROMAIN R.": "ROMAIN RAPAILLE",
    "CORENTIN D.": "CORENTIN DELOOR"
}

def normalize_name(name):
    if not name:
        return ""
    n = str(name).strip().upper()
    return NAME_MAPPING.get(n, n)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 1. Mettre à jour match_lineups
for old_name, new_name in NAME_MAPPING.items():
    c.execute("UPDATE match_lineups SET joueur_nom = ? WHERE UPPER(TRIM(joueur_nom)) = ?", (new_name, old_name))
    c.execute("UPDATE match_events SET acteur_principal = ? WHERE UPPER(TRIM(acteur_principal)) = ?", (new_name, old_name))
    c.execute("UPDATE match_events SET acteur_secondaire = ? WHERE UPPER(TRIM(acteur_secondaire)) = ?", (new_name, old_name))

conn.commit()

# Vérification
genech_players = [r[0] for r in c.execute("SELECT DISTINCT joueur_nom FROM match_lineups WHERE equipe = 'GENECH ES' ORDER BY joueur_nom").fetchall()]
print(f"Nombre de joueurs uniques GENECH ES dans match_lineups : {len(genech_players)}")
for i, p in enumerate(genech_players, 1):
    count_m = c.execute("SELECT count(*) FROM match_lineups WHERE equipe = 'GENECH ES' AND joueur_nom = ?", (p,)).fetchone()[0]
    print(f" {i:2d}. {p:<30} ({count_m} convocations)")

# Vérifier Elio
elio_rows = c.execute("SELECT match_id, numero, role FROM match_lineups WHERE joueur_nom = 'ELIO DELCROIX'").fetchall()
print(f"\nConvocations pour ELIO DELCROIX : {len(elio_rows)}")
for r in elio_rows:
    print(f"  Match: {r[0]}, N°{r[1]}, Rôle: {r[2]}")

# Vérifier qu'il ne reste aucun ELIO D.
elio_d_count = c.execute("SELECT count(*) FROM match_lineups WHERE joueur_nom LIKE '%ELIO D%'").fetchone()[0]
print(f"Restes de 'ELIO D.' : {elio_d_count}")

conn.close()
