import sqlite3
import pandas as pd
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

    # 1. Enrichissement DIM_MATCHS
    def enrich_match(row):
        dom = str(row['equipe_domicile']).upper()
        ext = str(row['equipe_exterieur']).upper()
        statut = str(row['statut'])
        s_dom = row['score_domicile']
        s_ext = row['score_exterieur']

        is_genech_dom = 'GENECH' in dom
        is_genech_ext = 'GENECH' in ext

        lieu = "Domicile" if is_genech_dom else ("Extérieur" if is_genech_ext else "Neutre")
        adversaire = row['equipe_exterieur'] if is_genech_dom else (row['equipe_domicile'] if is_genech_ext else "Autre")

        # Clean sheet
        clean_sheet = 0
        if statut == 'TERMINE':
            if is_genech_dom and s_ext == 0: clean_sheet = 1
            elif is_genech_ext and s_dom == 0: clean_sheet = 1

        # Résultat & Points
        points = 0
        if statut != 'TERMINE' or pd.isna(s_dom) or pd.isna(s_ext):
            resultat = "À venir"
            score_str = "À venir"
        else:
            score_str = f"{int(s_dom)} - {int(s_ext)}"
            if is_genech_dom:
                if s_dom > s_ext: 
                    resultat = "Victoire"
                    points = 3
                elif s_dom < s_ext: 
                    resultat = "Défaite"
                    points = 0
                else: 
                    resultat = "Nul"
                    points = 1
            elif is_genech_ext:
                if s_ext > s_dom: 
                    resultat = "Victoire"
                    points = 3
                elif s_ext < s_dom: 
                    resultat = "Défaite"
                    points = 0
                else: 
                    resultat = "Nul"
                    points = 1
            else:
                resultat = "Autre"

        comp_nom = "Coupe de France" if row['competition_id'] == 'cdf_2026' else "Régional 3 (Poule D)"

        return pd.Series([comp_nom, lieu, adversaire, clean_sheet, resultat, score_str, points])

    df_matchs[['competition_nom', 'lieu_genech', 'adversaire', 'is_clean_sheet', 'resultat_genech', 'score_affiche', 'points_obtenus']] = df_matchs.apply(enrich_match, axis=1)
    df_matchs['score_domicile'] = df_matchs['score_domicile'].fillna(-1).astype(int)
    df_matchs['score_exterieur'] = df_matchs['score_exterieur'].fillna(-1).astype(int)

    # 2. Enrichissement FACT_EVENTS
    def enrich_event(row):
        is_genech = 'GENECH' in str(row['equipe']).upper()
        camp = "ES Genech" if is_genech else "Adversaire"
        t_event = str(row['type_event'])
        
        is_but_genech = 1 if (t_event == 'BUT' and is_genech) else 0
        is_but_adverse = 1 if (t_event == 'BUT' and not is_genech) else 0
        is_carton_genech = 1 if (t_event in ['AVERTISSEMENT', 'EXPULSION'] and is_genech) else 0
        is_carton_adverse = 1 if (t_event in ['AVERTISSEMENT', 'EXPULSION'] and not is_genech) else 0
        mi_temps = "1ère Mi-Temps" if row['minute'] <= 45 else "2nde Mi-Temps"

        # Moment clé (ex: Money time 75-90')
        is_money_time = 1 if row['minute'] >= 75 else 0

        return pd.Series([camp, is_but_genech, is_but_adverse, is_carton_genech, is_carton_adverse, mi_temps, is_money_time])

    df_events[['camp_event', 'is_but_genech', 'is_but_adverse', 'is_carton_genech', 'is_carton_adverse', 'mi_temps', 'is_money_time']] = df_events.apply(enrich_event, axis=1)

    # 3. NOUVELLE TABLE : STATS INDIVIDUELLES JOUEURS ES GENECH
    genech_lineups = df_lineups[df_lineups['equipe'].str.contains('GENECH', case=False, na=False)].copy()
    
    # Événements Genech
    genech_events = df_events[df_events['equipe'].str.contains('GENECH', case=False, na=False)].copy()

    joueurs_stats = []
    unique_players = genech_lineups['joueur_nom'].dropna().unique()

    for joueur in unique_players:
        j_lines = genech_lineups[genech_lineups['joueur_nom'] == joueur]
        nb_titulaire = len(j_lines[j_lines['role'] == 'TITULAIRE'])
        nb_remplacant = len(j_lines[j_lines['role'] == 'REMPLACANT'])
        
        # Buts
        j_buts = len(genech_events[(genech_events['type_event'] == 'BUT') & (genech_events['acteur_principal'].str.contains(joueur, case=False, na=False))])
        
        # Cartons
        j_cartons_j = len(genech_events[(genech_events['type_event'] == 'AVERTISSEMENT') & (genech_events['acteur_principal'].str.contains(joueur, case=False, na=False))])
        j_cartons_r = len(genech_events[(genech_events['type_event'] == 'EXPULSION') & (genech_events['acteur_principal'].str.contains(joueur, case=False, na=False))])

        # Remplacements (minutes)
        subs_in = genech_events[(genech_events['type_event'] == 'CHANGEMENT') & (genech_events['acteur_principal'].str.contains(joueur, case=False, na=False))]
        subs_out = genech_events[(genech_events['type_event'] == 'CHANGEMENT') & (genech_events['acteur_secondaire'].str.contains(joueur, case=False, na=False))]
        
        # Estimation temps de jeu
        temps_jeu = (nb_titulaire * 90)
        for _, s in subs_out.iterrows():
            temps_jeu -= (90 - s['minute'])
        for _, s in subs_in.iterrows():
            temps_jeu += (90 - s['minute'])

        # Rôle tactique
        if nb_titulaire >= 4:
            statut = "Pilier / Titulaire indiscutable"
        elif nb_titulaire > 0:
            statut = "Rotation / Titulaire régulier"
        elif len(subs_in) > 0:
            statut = "Impact Player (Super-Sub)"
        else:
            statut = "Groupe élargi"

        joueurs_stats.append({
            "joueur_nom": joueur,
            "statut_tactique": statut,
            "titularisations": nb_titulaire,
            "entrees_en_jeu": len(subs_in),
            "matchs_feuille": nb_titulaire + nb_remplacant,
            "minutes_jouees_estimees": max(temps_jeu, 0),
            "buts": j_buts,
            "cartons_jaunes": j_cartons_j,
            "cartons_rouges": j_cartons_r
        })

    df_joueurs = pd.DataFrame(joueurs_stats).sort_values(by=["buts", "titularisations", "minutes_jouees_estimees"], ascending=False)

    # 4. Exports CSV complets
    df_matchs.to_csv(os.path.join(OUTPUT_DIR, "dim_matchs.csv"), index=False, encoding="utf-8-sig")
    df_events.to_csv(os.path.join(OUTPUT_DIR, "fact_events.csv"), index=False, encoding="utf-8-sig")
    df_classement.to_csv(os.path.join(OUTPUT_DIR, "dim_classement.csv"), index=False, encoding="utf-8-sig")
    df_lineups.to_csv(os.path.join(OUTPUT_DIR, "dim_lineups.csv"), index=False, encoding="utf-8-sig")
    df_joueurs.to_csv(os.path.join(OUTPUT_DIR, "dim_joueurs_stats.csv"), index=False, encoding="utf-8-sig")

    print(f"Exports terminés ! Nouvelle table dim_joueurs_stats.csv générée avec {len(df_joueurs)} joueurs.")

    conn.close()

if __name__ == "__main__":
    generate_analytics()
