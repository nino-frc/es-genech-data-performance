import sqlite3

conn = sqlite3.connect('C:/Users/ninof/.gemini/antigravity/scratch/genech_data_performance/genech_performance.db')
c = conn.cursor()

print("Distinct teams in match_lineups:")
for t in c.execute("SELECT equipe, count(*) FROM match_lineups GROUP BY equipe").fetchall():
    print(" ", t)

print("\nMatches and their lineups:")
for m in c.execute("SELECT match_id, count(*) FROM match_lineups GROUP BY match_id").fetchall():
    print(" ", m)

conn.close()
