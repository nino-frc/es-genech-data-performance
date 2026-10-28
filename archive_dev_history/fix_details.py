import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "genech_performance.db")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 1. Corriger les adversaires mal détectés sur les pages FFF
cur.execute("UPDATE matchs SET equipe_exterieur = 'GENECH ES' WHERE id = 'm_senior_f2_78809066-lille-e-s-l'")
cur.execute("UPDATE matchs SET equipe_exterieur = 'GENECH ES' WHERE id = 'm_u18_m1_79497787-et-am-c-cys'")
cur.execute("UPDATE matchs SET equipe_exterieur = 'SC BAILLEULOIS' WHERE id = 'm_u18_m1_56697624-ent-s-de-ge'")

# 2. Harmoniser les noms abrégés U18 vers les noms complets officiels
name_mapping = {
    'ANTOINE M.': 'ANTOINE MERVAILLE',
    'BAPTISTE D.': 'BAPTISTE DESCARPENTRIES',
    'ELIO B.': 'ELIO BOTTIN',
    'MARCEAU U.': 'MARCEAU URBANIAK',
    'NAEL R.': 'NAEL REDJEMI',
    'NATANAEL B.': 'NATANAEL BUFFART',
    'NATHAN L.': 'NATHAN LANGLET',
    'RAPHAEL D.': 'RAPHAEL DEVAUX',
    'RAPHAEL L.': 'RAPHAEL LEFEBVRE',
    'ROBIN C.': 'ROBIN CASTELAIN',
    'RUBENS S.': 'RUBENS SUNNOMAN',
    'VIANNEY D.': 'VIANNEY DESMARESCAUX'
}

for abbr, full in name_mapping.items():
    cur.execute("UPDATE match_lineups SET joueur_nom = ? WHERE joueur_nom = ? AND match_id LIKE 'm_u18_m1_%'", (full, abbr))
    cur.execute("UPDATE match_events SET acteur_principal = ? WHERE acteur_principal = ? AND match_id LIKE 'm_u18_m1_%'", (full, abbr))

conn.commit()

# Vérification
print("--- VÉRIFICATION MATCHS F2 ---")
for r in cur.execute("SELECT id, date_heure, equipe_domicile, score_domicile, score_exterieur, equipe_exterieur, statut FROM matchs WHERE equipe_club_id = 'SENIOR_F2' ORDER BY date_heure ASC").fetchall():
    print(r)

print("\n--- VÉRIFICATION MATCHS U18 ---")
for r in cur.execute("SELECT id, date_heure, equipe_domicile, score_domicile, score_exterieur, equipe_exterieur, statut FROM matchs WHERE equipe_club_id = 'U18_M1' ORDER BY date_heure ASC").fetchall():
    print(r)

print("\n--- EFFECTIF U18 (JOUEURS DISTINCTS & CONVOCATIONS) ---")
for r in cur.execute("""
    SELECT ml.joueur_nom, count(DISTINCT ml.match_id) as matchs,
           sum(case when ml.role = 'TITULAIRE' then 1 else 0 end) as tit
    FROM match_lineups ml
    JOIN matchs m ON ml.match_id = m.id
    WHERE m.equipe_club_id = 'U18_M1' AND ml.equipe LIKE '%GENECH%'
    GROUP BY ml.joueur_nom
    ORDER BY matchs DESC, tit DESC
""").fetchall():
    print(f"  {r[0]:25} : {r[1]} matchs ({r[2]} tit)")

print("\n--- EFFECTIF F2 (JOUEUSES DISTINCTES & CONVOCATIONS) ---")
for r in cur.execute("""
    SELECT ml.joueur_nom, count(DISTINCT ml.match_id) as matchs,
           sum(case when ml.role = 'TITULAIRE' then 1 else 0 end) as tit
    FROM match_lineups ml
    JOIN matchs m ON ml.match_id = m.id
    WHERE m.equipe_club_id = 'SENIOR_F2' AND ml.equipe LIKE '%GENECH%'
    GROUP BY ml.joueur_nom
    ORDER BY matchs DESC, tit DESC
""").fetchall():
    print(f"  {r[0]:25} : {r[1]} matchs ({r[2]} tit)")

conn.close()
