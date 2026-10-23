import sqlite3
import pandas as pd
import numpy as np
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "genech_performance.db")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "exports_powerbi")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_analytics():
    conn = sqlite3.connect(DB_PATH)

    df_matchs = pd.read_sql_query("SELECT * FROM matchs", conn)
    df_events = pd.read_sql_query("SELECT * FROM match_events", conn)
    df_classement = pd.read_sql_query("SELECT * FROM classement_poule ORDER BY rang ASC", conn)
    df_lineups = pd.read_sql_query("SELECT * FROM match_lineups", conn)

    # 1. Calculs officiels basés sur les scores réels
    if not df_matchs.empty:
        dom = df_matchs['equipe_domicile'].astype(str).str.upper()
        ext = df_matchs['equipe_exterieur'].astype(str).str.upper()
        statut = df_matchs['statut'].astype(str)
        s_dom = pd.to_numeric(df_matchs['score_domicile'], errors='coerce')
        s_ext = pd.to_numeric(df_matchs['score_exterieur'], errors='coerce')

        is_genech_dom = dom.str.contains('GENECH', na=False)
        is_genech_ext = ext.str.contains('GENECH', na=False)

        # Buts réels marqués / encaissés par match pour Genech
        df_matchs['buts_marques_genech'] = np.where(is_genech_dom, s_dom, np.where(is_genech_ext, s_ext, 0))
        df_matchs['buts_encaisses_genech'] = np.where(is_genech_dom, s_ext, np.where(is_genech_ext, s_dom, 0))

        df_matchs['competition_nom'] = np.where(df_matchs['competition_id'] == 'cdf_2026', "Coupe de France", "Régional 3 (Poule D)")
        df_matchs['lieu_genech'] = np.where(is_genech_dom, "Domicile", np.where(is_genech_ext, "Extérieur", "Neutre"))
        df_matchs['adversaire'] = np.where(is_genech_dom, df_matchs['equipe_exterieur'], np.where(is_genech_ext, df_matchs['equipe_domicile'], "Autre"))

        # Clean sheet
        cs_dom = (statut == 'TERMINE') & is_genech_dom & (s_ext == 0)
        cs_ext = (statut == 'TERMINE') & is_genech_ext & (s_dom == 0)
        df_matchs['is_clean_sheet'] = np.where(cs_dom | cs_ext, 1, 0)

        # Résultat & Points
        cond_victoire = (is_genech_dom & (s_dom > s_ext)) | (is_genech_ext & (s_ext > s_dom))
        cond_defaite = (is_genech_dom & (s_dom < s_ext)) | (is_genech_ext & (s_ext < s_dom))
        cond_nul = (s_dom == s_ext) & (statut == 'TERMINE')

        df_matchs['resultat_genech'] = np.where(
            statut != 'TERMINE', "À venir",
            np.where(cond_victoire, "Victoire", np.where(cond_nul, "Nul", np.where(cond_defaite, "Défaite", "Autre")))
        )
        df_matchs['points_obtenus'] = np.where(cond_victoire, 3, np.where(cond_nul, 1, 0))
        df_matchs['score_affiche'] = np.where(
            statut == 'TERMINE', s_dom.fillna(0).astype(int).astype(str) + " - " + s_ext.fillna(0).astype(int).astype(str), "À venir"
        )

    # 2. Fact Events
    if not df_events.empty:
        is_genech = df_events['equipe'].astype(str).str.upper().str.contains('GENECH', na=False)
        t_event = df_events['type_event'].astype(str)
        minute = pd.to_numeric(df_events['minute'], errors='coerce').fillna(0)

        df_events['camp_event'] = np.where(is_genech, "ES Genech", "Adversaire")
        df_events['is_but_genech'] = np.where((t_event == 'BUT') & is_genech, 1, 0)
        df_events['is_but_adverse'] = np.where((t_event == 'BUT') & (~is_genech), 1, 0)
        df_events['is_carton_genech'] = np.where(t_event.isin(['AVERTISSEMENT', 'EXPULSION']) & is_genech, 1, 0)
        df_events['is_carton_adverse'] = np.where(t_event.isin(['AVERTISSEMENT', 'EXPULSION']) & (~is_genech), 1, 0)
        df_events['mi_temps'] = np.where(minute <= 45, "1ère Mi-Temps", "2nde Mi-Temps")
        df_events['is_money_time'] = np.where(minute >= 75, 1, 0)

    # 3. Stats Joueurs
    joueurs_stats = []
    if not df_lineups.empty:
        genech_lineups = df_lineups[df_lineups['equipe'].str.contains('GENECH', case=False, na=False)].copy()
        genech_events = df_events[df_events['equipe'].str.contains('GENECH', case=False, na=False)].copy() if not df_events.empty else pd.DataFrame()
        unique_players = genech_lineups['joueur_nom'].dropna().unique()

        for joueur in unique_players:
            j_lines = genech_lineups[genech_lineups['joueur_nom'] == joueur]
            nb_titulaire = len(j_lines[j_lines['role'] == 'TITULAIRE'])
            nb_remplacant = len(j_lines[j_lines['role'] == 'REMPLACANT'])
            
            j_buts = 0
            j_cartons_j = 0
            j_cartons_r = 0
            subs_in_count = 0
            temps_jeu = nb_titulaire * 90

            if not genech_events.empty:
                j_buts = len(genech_events[(genech_events['type_event'] == 'BUT') & (genech_events['acteur_principal'].str.contains(joueur, case=False, na=False))])
                j_cartons_j = len(genech_events[(genech_events['type_event'] == 'AVERTISSEMENT') & (genech_events['acteur_principal'].str.contains(joueur, case=False, na=False))])
                j_cartons_r = len(genech_events[(genech_events['type_event'] == 'EXPULSION') & (genech_events['acteur_principal'].str.contains(joueur, case=False, na=False))])
                
                subs_in = genech_events[(genech_events['type_event'] == 'CHANGEMENT') & (genech_events['acteur_principal'].str.contains(joueur, case=False, na=False))]
                subs_out = genech_events[(genech_events['type_event'] == 'CHANGEMENT') & (genech_events['acteur_secondaire'].str.contains(joueur, case=False, na=False))]
                subs_in_count = len(subs_in)

                for _, s in subs_out.iterrows(): temps_jeu -= (90 - s['minute'])
                for _, s in subs_in.iterrows(): temps_jeu += (90 - s['minute'])

            if nb_titulaire >= 4: statut_t = "Pilier / Titulaire indiscutable"
            elif nb_titulaire > 0: statut_t = "Rotation / Titulaire régulier"
            elif subs_in_count > 0: statut_t = "Impact Player (Super-Sub)"
            else: statut_t = "Groupe élargi"

            joueurs_stats.append({
                "joueur_nom": joueur,
                "statut_tactique": statut_t,
                "titularisations": nb_titulaire,
                "entrees_en_jeu": subs_in_count,
                "matchs_feuille": nb_titulaire + nb_remplacant,
                "minutes_jouees_estimees": max(temps_jeu, 0),
                "buts": j_buts,
                "cartons_jaunes": j_cartons_j,
                "cartons_rouges": j_cartons_r
            })

    df_joueurs = pd.DataFrame(joueurs_stats) if joueurs_stats else pd.DataFrame()
    if not df_joueurs.empty:
        df_joueurs = df_joueurs.sort_values(by=["buts", "titularisations", "minutes_jouees_estimees"], ascending=False)

    # Exports CSV
    df_matchs.to_csv(os.path.join(OUTPUT_DIR, "dim_matchs.csv"), index=False, encoding="utf-8-sig")
    df_events.to_csv(os.path.join(OUTPUT_DIR, "fact_events.csv"), index=False, encoding="utf-8-sig")
    df_classement.to_csv(os.path.join(OUTPUT_DIR, "dim_classement.csv"), index=False, encoding="utf-8-sig")
    df_lineups.to_csv(os.path.join(OUTPUT_DIR, "dim_lineups_tous_clubs.csv"), index=False, encoding="utf-8-sig")
    df_lineups[df_lineups["equipe"].str.contains("GENECH", case=False, na=False)].to_csv(os.path.join(OUTPUT_DIR, "dim_lineups.csv"), index=False, encoding="utf-8-sig")
    df_joueurs.to_csv(os.path.join(OUTPUT_DIR, "dim_joueurs_stats.csv"), index=False, encoding="utf-8-sig")

    total_buts_reels = int(df_matchs[df_matchs['statut'] == 'TERMINE']['buts_marques_genech'].sum())
    total_buts_encaisses_reels = int(df_matchs[df_matchs['statut'] == 'TERMINE']['buts_encaisses_genech'].sum())
    print(f"Total Buts Réels ESG au tableau d'affichage : {total_buts_reels} marqués, {total_buts_encaisses_reels} encaissés.")

    conn.close()

if __name__ == "__main__":
    generate_analytics()
