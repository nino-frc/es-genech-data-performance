import sqlite3

conn = sqlite3.connect('C:/Users/ninof/.gemini/antigravity/scratch/genech_data_performance/genech_performance.db')
c = conn.cursor()

print("Events with REMI:")
for r in c.execute("SELECT * FROM match_events WHERE acteur_principal LIKE '%REMI%' OR acteur_secondaire LIKE '%REMI%'").fetchall():
    print(r)

print("\nLineups with DELOBEL:")
for r in c.execute("SELECT * FROM match_lineups WHERE joueur_nom LIKE '%DELOBEL%'").fetchall():
    print(r)

conn.close()
