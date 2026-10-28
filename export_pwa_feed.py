"""
Générateur du flux de données certifiées PWA MatchDay
Strictement filtré sur l'équipe fanion (SENIOR_M1) et le club GENECH ES :
- Exclusion des cartons adverses
- Détail nominatif complet des cartons rouges (qui a pris un rouge, quel match, minute, purgé ou non)
- Détail nominatif des sursis (2 cartons jaunes)
- Calcul propre du Score ESG sur le référentiel des 9 matchs fanion
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

    # 1. Dernier match officiel de l'Équipe Fanion
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

    # 3. Matchs & KPIs de la saison Fanion
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

    # 4. Détail nominatif des Cartons Rouges reçus par Genech
    query_red_cards = """
    SELECT me.id, me.match_id, me.acteur_principal, me.minute, m.date_heure, m.equipe_domicile, m.equipe_exterieur, m.tour_ou_journee
    FROM match_events me
    JOIN matchs m ON m.id = me.match_id
    WHERE me.type_event = 'EXPULSION'
      AND m.equipe_club_id = 'SENIOR_M1'
      AND (me.equipe LIKE '%GENECH%' OR me.equipe = '')
    ORDER BY m.date_heure DESC;
    """
    red_cards_rows = conn.execute(query_red_cards).fetchall()
    red_cards_list = []
    
    # Évaluation de la purge des rouges
    total_matches = len(genech_matches)
    for r in red_cards_rows:
        anon_name = anonymize_player_name(r["acteur_principal"])
        # Matchs joués après ce carton
        matches_after = genech_matches[genech_matches["date_heure"] > r["date_heure"]]
        is_purged = len(matches_after) > 0
        purge_status = "Purgé (Suspension effectuée)" if is_purged else "🚨 EN COURS (Suspendu)"

        is_dom = "GENECH" in r["equipe_domicile"].upper()
        opp = r["equipe_exterieur"] if is_dom else r["equipe_domicile"]

        red_cards_list.append({
            "joueur": anon_name,
            "minute": r["minute"],
            "date": r["date_heure"].split(" ")[0],
            "adversaire": opp,
            "match_label": f"{r['tour_ou_journee']} vs {opp}",
            "statut_purge": purge_status,
            "est_suspendu": not is_purged
        })

    # 5. Décompte global des cartons Genech (strictement joueurs Genech)
    query_cards_totals = """
    SELECT me.type_event, COUNT(*) as cnt
    FROM match_events me
    JOIN matchs m ON m.id = me.match_id
    WHERE me.type_event IN ('AVERTISSEMENT', 'EXPULSION')
      AND m.equipe_club_id = 'SENIOR_M1'
      AND (me.equipe LIKE '%GENECH%' OR me.equipe = '')
    GROUP BY me.type_event;
    """
    counts = dict(conn.execute(query_cards_totals).fetchall())
    total_jaunes = counts.get("AVERTISSEMENT", 0)
    total_rouges = counts.get("EXPULSION", 0)

    # 6. Ratings ESG Réels (filtrés SENIOR_M1)
    df_ratings = calculate_player_ratings()
    players_list = []
    total_minutes_cumulees = 0

    if not df_ratings.empty:
        top_players = df_ratings.sort_values(by="esg_impact_score", ascending=False)
        for rank, (_, row) in enumerate(top_players.iterrows(), start=1):
            if row["matchs_joues"] > 0:
                anon_name = anonymize_player_name(row["joueur"])
                min_est = int(row["minutes_estimees"]) if pd.notnull(row["minutes_estimees"]) else 0
                total_minutes_cumulees += min_est
                j = int(row["cartons_jaunes"]) if pd.notnull(row["cartons_jaunes"]) else 0
                r = int(row["cartons_rouges"]) if pd.notnull(row["cartons_rouges"]) else 0

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

    # 7. Sursis réglementaires (Art. 226 FFF)
    df_discipline, _ = analyze_discipline()
    sursis_list = []
    if not df_discipline.empty:
        sursis_players = df_discipline[df_discipline["statut_juridique_fff"].str.contains("SURSIS", case=False, na=False)]
        for _, s in sursis_players.iterrows():
            anon_name = anonymize_player_name(s["joueur"])
            sursis_list.append({
                "joueur": anon_name,
                "jaunes_90j": int(s["cartons_jaunes_90j"]),
                "dates": s["dates_cartons_recents"],
                "expiration": s["expiration_sursis"],
                "message": f"2 cartons reçus ({s['dates_cartons_recents']}). Prochain jaune = 1 match de suspension ferme."
            })

    # 8. Classement R3 Poule D
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
        "cartons_rouges_details": red_cards_list,
        "sursis_details": sursis_list,
        "effectif_esg": players_list,
        "classement": standings
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write("window.MATCHDAY_DATA = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n")

    print(f"Export certifié terminé :")
    print(f" - Cartons Rouges Genech : {len(red_cards_list)}")
    print(f" - Joueurs sous sursis (2 Jaunes) : {len(sursis_list)}")
    print(f" - Joueurs analysés : {len(players_list)}")

if __name__ == "__main__":
    export_real_pwa_feed()
