import sqlite3
import pandas as pd
from player_rating import calculate_player_ratings

DB_PATH = r"C:\Users\ninof\.gemini\antigravity\scratch\genech_data_performance\genech_performance.db"
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("Total match_lineups :", cur.execute("SELECT count(*) FROM match_lineups").fetchone()[0])
print("Equipe='GENECH ES' :", cur.execute("SELECT count(*) FROM match_lineups WHERE equipe = 'GENECH ES'").fetchone()[0])
print("Distinct equipe in match_lineups :", cur.execute("SELECT distinct equipe FROM match_lineups").fetchall())

rdf = calculate_player_ratings()
print("Total rows in calculate_player_ratings() :", len(rdf))
print("Joueurs in calculate_player_ratings() :")
for j in rdf['joueur'].tolist():
    print(" -", j)

conn.close()
