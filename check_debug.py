import sqlite3
import pandas as pd

conn = sqlite3.connect('C:/Users/ninof/.gemini/antigravity/scratch/genech_data_performance/genech_performance.db')
c = conn.cursor()

print("--- ALL TEAMS IN match_lineups ---")
for row in c.execute("SELECT equipe, count(*) FROM match_lineups GROUP BY equipe").fetchall():
    print(row)

print("\n--- ALL DISTINCT PLAYERS WITH GENECH ES ---")
genech_players = [r[0] for r in c.execute("SELECT DISTINCT joueur_nom FROM match_lineups WHERE equipe LIKE '%GENECH%' ORDER BY joueur_nom").fetchall()]
print(f"Total Genech players: {len(genech_players)}")
for p in genech_players:
    print(" ", p)

print("\n--- ALL DISTINCT PLAYERS IN ENTIRE TABLE ---")
all_players = [r[0] for r in c.execute("SELECT DISTINCT joueur_nom FROM match_lineups ORDER BY joueur_nom").fetchall()]
print(f"Total all players in table: {len(all_players)}")

print("\n--- ELIO IN match_lineups ---")
for r in c.execute("SELECT id, match_id, equipe, numero, joueur_nom, role FROM match_lineups WHERE UPPER(joueur_nom) LIKE '%ELIO%' OR UPPER(joueur_nom) LIKE '%DELCROIX%'").fetchall():
    print(r)

print("\n--- ELIO IN match_events ---")
for r in c.execute("SELECT id, match_id, type_event, minute, acteur_principal, acteur_secondaire FROM match_events WHERE UPPER(acteur_principal) LIKE '%ELIO%' OR UPPER(acteur_principal) LIKE '%DELCROIX%' OR UPPER(acteur_secondaire) LIKE '%ELIO%' OR UPPER(acteur_secondaire) LIKE '%DELCROIX%'").fetchall():
    print(r)

print("\n--- CHECK EXPORTS_POWERBI CSVs ---")
import os
csv_path = 'C:/Users/ninof/.gemini/antigravity/scratch/genech_data_performance/exports_powerbi/dim_joueurs_stats.csv'
if os.path.exists(csv_path):
    df_csv = pd.read_csv(csv_path)
    print("dim_joueurs_stats.csv len:", len(df_csv))
    print("dim_joueurs_stats.csv players:")
    for p in df_csv['joueur_nom'].tolist() if 'joueur_nom' in df_csv.columns else df_csv.iloc[:, 0].tolist():
        if 'ELIO' in str(p).upper() or 'DELCROIX' in str(p).upper():
            print("  CSV match:", p)
