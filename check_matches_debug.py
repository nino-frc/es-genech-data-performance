import sqlite3

conn = sqlite3.connect('C:/Users/ninof/.gemini/antigravity/scratch/genech_data_performance/genech_performance.db')
c = conn.cursor()

print("Total matches in matchs table:", c.execute("SELECT count(*) FROM matchs").fetchone()[0])

print("\nMatches by equipe_club_id:")
for r in c.execute("SELECT equipe_club_id, count(*) FROM matchs GROUP BY equipe_club_id").fetchall():
    print(" ", r)

print("\nMatches where NEITHER team has GENECH:")
non_genech = c.execute("SELECT id, competition_id, equipe_domicile, equipe_exterieur, equipe_club_id FROM matchs WHERE equipe_domicile NOT LIKE '%GENECH%' AND equipe_exterieur NOT LIKE '%GENECH%'").fetchall()
print(f"Total non-Genech matches: {len(non_genech)}")
for r in non_genech[:10]:
    print(" ", r)

print("\nDuplicate matches (same teams & date):")
dups = c.execute("SELECT date_heure, equipe_domicile, equipe_exterieur, count(*) FROM matchs GROUP BY date_heure, equipe_domicile, equipe_exterieur HAVING count(*) > 1").fetchall()
print(f"Total duplicate matches: {len(dups)}")
for r in dups:
    print(" ", r)

conn.close()
