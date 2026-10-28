"""
Générateur du flux de données réelles pour la PWA MatchDay
Strictement filtré sur l'équipe fanion (SENIOR_M1) :
- Zéro mélange avec les jeunes (U18, U14...) ou vétérans
- 10 buts marqués en 9 matchs officiels (R3 + Coupe de France)
- 5 clean sheets
- Notations Joueurs ESG réelles (player_rating.py)
- Alertes disciplinaires réelles (discipline_monitor.py)
- Classement officiel FFF (R3 Poule D)
"""

import os
import json
import sqlite3
import pandas as pd
from datetime import datetime

from data_cleaner import anonymize_player_name
from player_rating import calculate_player_ratings
from discipline_monitor import analyze_discipline

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "genech_performance.db")
OUTPUT_JSON = os.path.join(BASE_DIR, "public", "data_feed.json")
OUTPUT_JS = os.path.join(BASE_DIR, "public", "data.js")

def export_real_pwa_feed():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # 1. Dernier match officiel joué par l'Équipe Fanion (SENIOR_M1)
    query_last_match = """
    SELECT * FROM matchs 
    WHERE statut = 'TERMINE' AND equipe_club_id = 'SENIOR_M1'
    ORDER BY date_heure DESC LIMIT 1;
    """
    last_match_row = conn.execute(query_last_match).fetchone()
    
    last_match = {}
    if last_match_row:
        last_match = {
            "id": last_match_row["id"],
            "competition": "Coupe de France (Tour 6)" if "cdf" in last_match_row["competition_id"] else "Seniors Régional 3",
            "domicile": last_match_row["equipe_domicile"],
            "exterieur": last_match_row["equipe_exterieur"],
            "score_domicile": last_match_row["score_domicile"],
            "score_exterieur": last_match_row["score_exterieur"],
            "date_heure": last_match_row["date_heure"],
            "statut": last_match_row["statut"]
        }

    # 2. Chronologie des événements du dernier match
    events_rows = []
    if last_match:
        query_events = "SELECT minute, type_event, equipe, acteur_principal, detail FROM match_events WHERE match_id = ? ORDER BY minute ASC"
        for ev in conn.execute(query_events, (last_match["id"],)).fetchall():
            events_rows.append({
                "minute": ev["minute"],
                "type": ev["type_event"],
                "equipe": ev["equipe"],
                "acteur": anonymize_player_name(ev["acteur_principal"]),
                "detail": ev["detail"]
            })

    # 3. KPIs réels de saison strictement pour l'Équipe Fanion (SENIOR_M1)
    genech_matches = pd.read_sql_query("""
        SELECT * FROM matchs 
        WHERE statut = 'TERMINE' AND equipe_club_id = 'SENIOR_M1'
        ORDER BY date_heure ASC
    """, conn)

    total_buts_marques = 0
    total_clean_sheets = 0
    for _, m in genech_matches.iterrows():
        is_dom = "GENECH" in m['equipe_domicile'].upper()
        s_g = m['score_domicile'] if is_dom else m['score_exterieur']
        s_opp = m['score_exterieur'] if is_dom else m['score_domicile']
        if pd.notnull(s_g):
            total_buts_marques += int(s_g)
        if pd.notnull(s_opp) and int(s_opp) == 0:
            total_clean_sheets += 1

    # 4. Ratings ESG Réels (depuis player_rating.py, filtré sur SENIOR_M1)
    df_ratings = calculate_player_ratings()
    players_list = []
    total_minutes_cumulees = 0
    total_jaunes = 0
    total_rouges = 0

    if not df_ratings.empty:
        top_players = df_ratings.sort_values(by="esg_impact_score", ascending=False)
        for rank, (_, row) in enumerate(top_players.iterrows(), start=1):
            if row["matchs_joues"] > 0:
                anon_name = anonymize_player_name(row["joueur"])
                min_est = int(row["minutes_estimees"]) if pd.notnull(row["minutes_estimees"]) else 0
                total_minutes_cumulees += min_est
                j = int(row["cartons_jaunes"]) if pd.notnull(row["cartons_jaunes"]) else 0
                r = int(row["cartons_rouges"]) if pd.notnull(row["cartons_rouges"]) else 0
                total_jaunes += j
                total_rouges += r

                if rank <= 25:
                    players_list.append({
                        "rang": rank,
                        "nom": anon_name,
                        "badge": row["badge_tactique"],
                        "matchs": int(row["matchs_joues"]),
                        "minutes": min_est,
                        "clean_sheets": int(row["clean_sheets_participees"]),
                        "buts": int(row["buts"]),
                        "cartons_j": j,
                        "cartons_r": r,
                        "esg_score": round(float(row["esg_impact_score"]), 1)
                    })

    # 5. Alertes disciplinaires réelles
    _, alerts_disc = analyze_discipline()
    clean_alerts = []
    for a in alerts_disc:
        clean_msg = a
        for p in players_list:
            clean_msg = clean_msg.replace(p["nom"].upper(), p["nom"])
        clean_alerts.append(clean_msg)

    # 6. Classement R3 Poule D
    query_standings = "SELECT rang, equipe_nom, points, joues FROM classement_poule WHERE competition_id = 'r3_poule_d' ORDER BY rang ASC"
    standings = []
    for st in conn.execute(query_standings).fetchall():
        standings.append({
            "rang": st["rang"],
            "equipe": st["equipe_nom"],
            "points": st["points"],
            "joues": st["joues"]
        })

    conn.close()

    payload = {
        "equipe_active": {
            "club_id": "525674",
            "nom": "ES Genech",
            "categorie": "Seniors Régional 3",
            "poule": "Poule D",
            "derniere_maj": datetime.now().strftime("%d/%m/%Y à %H:%M")
        },
        "dernier_match": last_match,
        "evenements_dernier_match": events_rows,
        "kpis_saison": {
            "buts_marques": total_buts_marques,
            "clean_sheets": total_clean_sheets,
            "minutes_cumulees": total_minutes_cumulees,
            "cartons_jaunes": total_jaunes,
            "cartons_rouges": total_rouges
        },
        "effectif_esg": players_list,
        "alertes_discipline": clean_alerts,
        "classement": standings
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write("window.MATCHDAY_DATA = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n")

    print(f"Export certifié SENIOR_M1 terminé :")
    print(f" - Matchs analysés : {len(genech_matches)}")
    print(f" - Buts inscrits Fanion : {total_buts_marques}")
    print(f" - Clean sheets Fanion : {total_clean_sheets}")
    print(f" - Cartons Fanion : {total_jaunes} Jaunes / {total_rouges} Rouges")
    print(f" - Joueurs analysés : {len(players_list)}")

if __name__ == "__main__":
    export_real_pwa_feed()
