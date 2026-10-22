"""
Matrice d'Impact des Remplaçants - Plus/Minus (+/-)
Évalue mathématiquement l'apport des remplaçants (Super-Subs) lors de leurs entrées en jeu
Différentiel de buts Genech entre la minute d'entrée et le coup de sifflet final
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

def calculate_substitutions_impact():
    conn = sqlite3.connect(DB_PATH)

    df_matchs = pd.read_sql_query("SELECT * FROM matchs WHERE statut = 'TERMINE'", conn)
    df_events = pd.read_sql_query("SELECT * FROM match_events", conn)
    conn.close()

    if df_matchs.empty or df_events.empty:
        print("Données insuffisantes.")
        return pd.DataFrame()

    # Changements concernant Genech
    sub_events = df_events[
        (df_events['type_event'] == 'CHANGEMENT') & 
        (df_events['equipe'].str.contains('GENECH', case=False, na=False))
    ].copy()

    if sub_events.empty:
        print("Aucun remplacement enregistré.")
        return pd.DataFrame()

    sub_impact_records = []

    for _, sub in sub_events.iterrows():
        mid = sub['match_id']
        minute_in = int(sub['minute'])
        entrant = normalize_player_name(sub['acteur_principal'])
        sortant = normalize_player_name(sub['acteur_secondaire'])

        match_row = df_matchs[df_matchs['id'] == mid]
        if match_row.empty:
            continue
        m = match_row.iloc[0]
        is_dom = "GENECH" in m['equipe_domicile'].upper()

        # Buts marqués avant la minute du changement
        events_before = df_events[(df_events['match_id'] == mid) & (df_events['type_event'] == 'BUT') & (df_events['minute'] <= minute_in)]
        buts_g_before = len(events_before[events_before['equipe'].str.contains('GENECH', case=False, na=False)])
        buts_opp_before = len(events_before[~events_before['equipe'].str.contains('GENECH', case=False, na=False)])
        diff_before = buts_g_before - buts_opp_before

        # Buts totaux du match
        events_all = df_events[(df_events['match_id'] == mid) & (df_events['type_event'] == 'BUT')]
        buts_g_total = len(events_all[events_all['equipe'].str.contains('GENECH', case=False, na=False)])
        buts_opp_total = len(events_all[~events_all['equipe'].str.contains('GENECH', case=False, na=False)])
        diff_final = buts_g_total - buts_opp_total

        # Plus/Minus sur la période passée sur le terrain
        plus_minus = diff_final - diff_before
        buts_marques_apres = buts_g_total - buts_g_before
        buts_encaisses_apres = buts_opp_total - buts_opp_before

        sub_impact_records.append({
            "match_id": mid,
            "minute_entree": minute_in,
            "joueur_entrant": entrant,
            "joueur_sortant": sortant,
            "score_a_entree": f"{buts_g_before}-{buts_opp_before}",
            "score_final": f"{buts_g_total}-{buts_opp_total}",
            "buts_pour_apres": buts_marques_apres,
            "buts_contre_apres": buts_encaisses_apres,
            "plus_minus": plus_minus
        })

    df_sub_records = pd.DataFrame(sub_impact_records)

    # Agrégation par joueur
    summary = []
    for player in df_sub_records['joueur_entrant'].unique():
        p_records = df_sub_records[df_sub_records['joueur_entrant'] == player]
        nb_entrees = len(p_records)
        pm_total = int(p_records['plus_minus'].sum())
        pm_moyen = round(float(p_records['plus_minus'].mean()), 2)
        buts_pour = int(p_records['buts_pour_apres'].sum())
        buts_contre = int(p_records['buts_contre_apres'].sum())
        minute_moyenne = round(float(p_records['minute_entree'].mean()), 0)

        if pm_total >= 2:
            profil = "⚡ Super-Sub Décisif (+)"
        elif pm_total >= 0:
            profil = "🛡️ Stabilisateur Neutre/Positif"
        else:
            profil = "⚠️ Baisse de régime"

        summary.append({
            "joueur": player,
            "entrees_en_jeu": nb_entrees,
            "minute_moyenne_entree": f"{int(minute_moyenne)}'",
            "plus_minus_total": pm_total,
            "plus_minus_par_entree": pm_moyen,
            "buts_pour_sur_terrain": buts_pour,
            "buts_contre_sur_terrain": buts_contre,
            "impact_banc": profil
        })

    df_pm_summary = pd.DataFrame(summary).sort_values(by=["plus_minus_total", "plus_minus_par_entree"], ascending=False)

    output_csv = os.path.join(OUTPUT_DIR, "dim_substitutions_impact.csv")
    df_pm_summary.to_csv(output_csv, index=False, encoding="utf-8-sig")

    print("\n" + "="*80)
    print("🔄 MATRICE D'IMPACT DES REMPLAÇANTS (PLUS/MINUS +/-)")
    print("="*80)
    print(df_pm_summary.to_string(index=False))
    print("="*80 + "\n")

    return df_pm_summary

if __name__ == "__main__":
    calculate_substitutions_impact()
