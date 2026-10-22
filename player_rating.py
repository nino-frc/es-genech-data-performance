"""
Modèle de Notation Joueur - ESG Impact Score (0 à 100)
Algorithme propriétaire pour le football régional amateur (R3)
Feature Engineering sur les feuilles de match officielles FFF
"""

import os
import sys
import sqlite3
import pandas as pd
import numpy as np

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

DB_PATH = os.path.join(os.path.dirname(__file__), "genech_performance.db")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "exports_powerbi")
os.makedirs(OUTPUT_DIR, exist_ok=True)

from discipline_monitor import normalize_player_name

def calculate_player_ratings():
    conn = sqlite3.connect(DB_PATH)

    df_matchs = pd.read_sql_query("SELECT * FROM matchs WHERE statut = 'TERMINE'", conn)
    df_lineups = pd.read_sql_query("SELECT * FROM match_lineups WHERE equipe LIKE '%GENECH%'", conn)
    df_events = pd.read_sql_query("SELECT * FROM match_events", conn)
    conn.close()

    if df_lineups.empty or df_matchs.empty:
        print("Données insuffisantes pour calculer les ratings joueurs.")
        return pd.DataFrame()

    df_lineups['player_norm'] = df_lineups['joueur_nom'].apply(normalize_player_name)
    df_events['player_norm'] = df_events['acteur_principal'].apply(normalize_player_name)

    total_matches_played = len(df_matchs[
        (df_matchs['equipe_domicile'].str.contains('GENECH', case=False, na=False)) |
        (df_matchs['equipe_exterieur'].str.contains('GENECH', case=False, na=False))
    ])

    # Clean sheets de Genech
    cs_match_ids = []
    for _, m in df_matchs.iterrows():
        is_dom = "GENECH" in m['equipe_domicile'].upper()
        opp_score = m['score_exterieur'] if is_dom else m['score_domicile']
        if pd.notnull(opp_score) and int(opp_score) == 0:
            cs_match_ids.append(m['id'])

    unique_players = df_lineups['player_norm'].unique()
    ratings_list = []

    for player in unique_players:
        p_lines = df_lineups[df_lineups['player_norm'] == player]
        matchs_convocations = len(p_lines)
        starts = len(p_lines[p_lines['role'] == 'TITULAIRE'])
        subs = len(p_lines[p_lines['role'] == 'REMPLACANT'])

        # Estimation précise des minutes jouées
        # Début à 90 min si titulaire, 0 si remplaçant
        p_matches = p_lines['match_id'].unique()
        minutes_totales = 0
        cs_participees = 0

        for mid in p_matches:
            is_start = len(p_lines[(p_lines['match_id'] == mid) & (p_lines['role'] == 'TITULAIRE')]) > 0
            m_events = df_events[df_events['match_id'] == mid]
            
            # Changements concernant ce joueur
            sub_out = m_events[(m_events['type_event'] == 'CHANGEMENT') & (m_events['acteur_secondaire'].apply(normalize_player_name) == player)]
            sub_in = m_events[(m_events['type_event'] == 'CHANGEMENT') & (m_events['acteur_principal'].apply(normalize_player_name) == player)]

            if is_start:
                min_match = 90
                if not sub_out.empty:
                    min_match = int(sub_out.iloc[0]['minute'])
            else:
                min_match = 0
                if not sub_in.empty:
                    min_match = 90 - int(sub_in.iloc[0]['minute'])

            minutes_totales += max(0, min(90, min_match))

            # Bonus clean sheet si au moins 45 minutes jouées dans un match à clean sheet
            if mid in cs_match_ids and min_match >= 45:
                cs_participees += 1

        # Stats offensives & disciplinaires
        p_events = df_events[df_events['player_norm'] == player]
        buts = len(p_events[p_events['type_event'] == 'BUT'])
        cartons_j = len(p_events[p_events['type_event'] == 'AVERTISSEMENT'])
        cartons_r = len(p_events[p_events['type_event'] == 'EXPULSION'])

        # -----------------------------------------------------------------
        # MODÈLE DE SCORING "ESG IMPACT SCORE" (0 à 100)
        # -----------------------------------------------------------------
        # 1. Volume & Régularité (Max 35 pts)
        max_possible_mins = total_matches_played * 90 if total_matches_played > 0 else 360
        score_volume = min(35.0, (minutes_totales / max_possible_mins) * 35.0)

        # 2. Solidité Défensive & Clean Sheets (Max 30 pts)
        score_defensif = min(30.0, cs_participees * 6.0)

        # 3. Impact Buteur & Clé (Max 35 pts)
        score_offensif = min(35.0, buts * 14.0)

        # 4. Pénalité Disciplinaire
        malus_discipline = (cartons_j * 4.0) + (cartons_r * 12.0)

        # Base fixe de présence (10 pts)
        base_presence = min(10.0, matchs_convocations * 2.5)

        raw_rating = base_presence + score_volume + score_defensif + score_offensif - malus_discipline
        final_rating = round(float(np.clip(raw_rating, 0.0, 99.0)), 1)

        # Attribution du profil tactique
        if final_rating >= 80.0:
            badge = "⭐ MVP / Cadre Incontournable"
        elif buts >= 2:
            badge = "🎯 Buteur d'Élite"
        elif cs_participees >= 3 and starts >= 3:
            badge = "🛡️ Roc Défensif"
        elif starts >= 3:
            badge = "⚙️ Régulateur / Titulaire Cadre"
        elif subs >= 2 and minutes_totales >= 60:
            badge = "⚡ Super-Sub / Impact Player"
        else:
            badge = "🔄 Rotation Effectif"

        ratings_list.append({
            "joueur": player,
            "esg_impact_score": final_rating,
            "badge_tactique": badge,
            "matchs_joues": matchs_convocations,
            "titularisations": starts,
            "minutes_estimees": minutes_totales,
            "clean_sheets_participees": cs_participees,
            "buts": buts,
            "cartons_jaunes": cartons_j,
            "cartons_rouges": cartons_r
        })

    df_ratings = pd.DataFrame(ratings_list).sort_values(by="esg_impact_score", ascending=False)

    # Export CSV pour Power BI
    output_csv = os.path.join(OUTPUT_DIR, "dim_player_ratings.csv")
    df_ratings.to_csv(output_csv, index=False, encoding="utf-8-sig")

    print("\n" + "="*80)
    print("🏆 ESG IMPACT SCORES — CLASSEMENT DE PERFORMANCE DES JOUEURS")
    print("="*80)
    print(df_ratings.to_string(index=False))
    print("="*80 + "\n")

    return df_ratings

if __name__ == "__main__":
    calculate_player_ratings()
