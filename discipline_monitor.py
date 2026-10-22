"""
Module de Veille Disciplinaire Interne - ES Genech
Application des règlements officiels FFF (Article 226 des Règlements Généraux)
Règle : 3 cartons jaunes en moins de 3 mois (90 jours) = 1 match de suspension automatique
Gestion précise de la purge des suspensions après les matchs disputés.
"""

import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

DB_PATH = os.path.join(os.path.dirname(__file__), "genech_performance.db")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "exports_powerbi")
os.makedirs(OUTPUT_DIR, exist_ok=True)

NAME_MAPPING = {
    "ELIO D.": "ELIO DELCROIX",
    "MATHYS H.": "MATHYS HERVE",
    "GASPARD D.": "GASPARD DROUPSY",
    "AUGUSTIN D.": "AUGUSTIN DROUPSY",
    "HUGO H.": "HUGO HERVE",
    "JULIEN D.": "JULIEN DEVERNAY",
    "JULIEN N.": "JULIEN NISSE",
    "MAXIME P.": "MAXIME PETIT",
    "MAXIME PETITPREZ": "MAXIME PETIT",
    "REMI D.": "REMI DELOBEL",
    "GIOVANY C.": "GIOVANY CALON",
    "GIOVANY CLERY": "GIOVANY CALON",
    "CLEMENT D.": "CLEMENT DURIEZ",
    "CLEMENT DELELIS": "CLEMENT DURIEZ",
    "TIM L.": "TIM LACOTE",
    "TIM LECLERCQ": "TIM LACOTE",
    "THOMAS L.": "THOMAS LEONARD",
    "ARTHUR C.": "ARTHUR CLIQUE",
    "JEAN PAUL B.": "JEAN PAUL BANGALA TOFIFI",
    "DANY D.": "DANY DE FREITAS",
    "JULES D.": "JULES DIVERCHY",
    "MATEO S.": "MATEO SURMONT",
    "ROMAIN R.": "ROMAIN RAPAILLE",
    "CORENTIN D.": "CORENTIN DELOOR"
}

def normalize_player_name(raw_name: str) -> str:
    name = raw_name.strip().upper()
    return NAME_MAPPING.get(name, name)

def analyze_discipline(reference_date=None):
    if reference_date is None:
        reference_date = datetime.now()
    elif isinstance(reference_date, str):
        reference_date = datetime.strptime(reference_date, "%Y-%m-%d")

    conn = sqlite3.connect(DB_PATH)

    # Récupération de tous les matchs terminés de Genech pour évaluer les purges
    query_matchs = """
    SELECT id, date_heure, tour_ou_journee, competition_id 
    FROM matchs 
    WHERE statut = 'TERMINE' AND (equipe_domicile LIKE '%GENECH%' OR equipe_exterieur LIKE '%GENECH%')
    ORDER BY date_heure ASC;
    """
    df_matchs = pd.read_sql_query(query_matchs, conn)
    df_matchs['date_match'] = pd.to_datetime(df_matchs['date_heure'])

    query_cards = """
    SELECT me.id, me.match_id, m.competition_id, m.tour_ou_journee, m.date_heure, 
           me.type_event, me.acteur_principal, me.minute
    FROM match_events me
    JOIN matchs m ON m.id = me.match_id
    WHERE me.type_event IN ('AVERTISSEMENT', 'EXPULSION')
      AND (me.equipe LIKE '%GENECH%' OR me.equipe = '')
    ORDER BY m.date_heure ASC;
    """
    df_cards = pd.read_sql_query(query_cards, conn)
    conn.close()

    if df_cards.empty:
        return pd.DataFrame(), []

    df_cards['player_norm'] = df_cards['acteur_principal'].apply(normalize_player_name)
    df_cards['date_match'] = pd.to_datetime(df_cards['date_heure'])

    window_start = reference_date - timedelta(days=90)

    discipline_records = []
    alerts_active = []
    alerts_sursis = []

    unique_players = df_cards['player_norm'].unique()

    for player in unique_players:
        p_cards = df_cards[df_cards['player_norm'] == player].sort_values(by='date_match')

        # Identifier les expulsions
        red_cards = p_cards[p_cards['type_event'] == 'EXPULSION']
        matches_with_red = red_cards['match_id'].unique()

        # Cartons jaunes isolés (non absorbés) dans les 90 jours
        isolated_yellows = p_cards[
            (p_cards['date_match'] >= window_start) & 
            (p_cards['type_event'] == 'AVERTISSEMENT') & 
            (~p_cards['match_id'].isin(matches_with_red))
        ]

        total_recent_j = len(isolated_yellows)
        total_recent_r = len(red_cards)

        dates_cartons = [d.strftime('%d/%m') for d in isolated_yellows['date_match']]
        dates_str = ", ".join(dates_cartons) if dates_cartons else "-"

        # Vérifier si le joueur a une expulsion NON PURGÉE
        is_red_active = False
        if not red_cards.empty:
            last_red = red_cards.iloc[-1]
            last_red_date = last_red['date_match']
            # Nombre de matchs officiels joués par Genech APRÈS cette expulsion
            matches_after_red = df_matchs[df_matchs['date_match'] > last_red_date]
            if len(matches_after_red) == 0:
                # Expulsion lors du tout dernier match : SUSPENSION FERME ACTIVE !
                is_red_active = True
                statut_disciplinaire = "SUSPENDU (CARTON ROUGE)"
                gravite = "ROUGE"
                expiration_sursis = "-"
                alerte = f"🚨 {player} : Suspendu 1 match ferme ce week-end (Exclusion le {last_red_date.strftime('%d/%m')} vs Anstaing)."
                alerts_active.append(alerte)
            else:
                # La suspension a déjà été purgée lors d'un match précédent
                pass

        if not is_red_active:
            if total_recent_j >= 3:
                # Vérifier si le 3e jaune a déjà été purgé
                third_yellow_date = isolated_yellows['date_match'].iloc[2]
                matches_after_3rd = df_matchs[df_matchs['date_match'] > third_yellow_date]
                if len(matches_after_3rd) == 0:
                    statut_disciplinaire = "SUSPENDU (3 JAUNES)"
                    gravite = "ROUGE"
                    expiration_sursis = "-"
                    alerte = f"🚨 {player} : 3e carton jaune reçu ({dates_str}). Suspension automatique de 1 match ferme."
                    alerts_active.append(alerte)
                else:
                    statut_disciplinaire = "PURGÉ (COMPTEUR RÉINITIALISÉ)"
                    gravite = "VERT"
                    expiration_sursis = "-"
            elif total_recent_j == 2:
                statut_disciplinaire = "SOUS SURSIS IMMÉDIAT"
                gravite = "ORANGE"
                first_card_date = isolated_yellows['date_match'].iloc[0]
                exp_date = first_card_date + timedelta(days=90)
                expiration_sursis = exp_date.strftime('%d/%m/%Y')
                alerte = f"⚠️ {player} : 2 cartons ({dates_str}). Prochain carton = suspension automatique (Sursis jusqu'au {expiration_sursis})."
                alerts_sursis.append(alerte)
            elif total_recent_j == 1:
                statut_disciplinaire = "AVERTI (1 JAUNE)"
                gravite = "JAUNE"
                first_card_date = isolated_yellows['date_match'].iloc[0]
                exp_date = first_card_date + timedelta(days=90)
                expiration_sursis = exp_date.strftime('%d/%m/%Y')
            else:
                statut_disciplinaire = "CASIER VIERGE"
                gravite = "VERT"
                expiration_sursis = "-"

        discipline_records.append({
            "joueur": player,
            "cartons_jaunes_90j": total_recent_j,
            "cartons_rouges_90j": total_recent_r,
            "dates_cartons_recents": dates_str,
            "statut_juridique_fff": statut_disciplinaire,
            "niveau_alerte": gravite,
            "expiration_sursis": expiration_sursis
        })

    df_discipline = pd.DataFrame(discipline_records)
    sort_order = {"ROUGE": 0, "ORANGE": 1, "JAUNE": 2, "VERT": 3}
    df_discipline['sort_key'] = df_discipline['niveau_alerte'].map(sort_order)
    df_discipline = df_discipline.sort_values(by=['sort_key', 'cartons_jaunes_90j'], ascending=[True, False]).drop(columns=['sort_key'])

    output_csv = os.path.join(OUTPUT_DIR, "dim_discipline_genech.csv")
    df_discipline.to_csv(output_csv, index=False, encoding="utf-8-sig")

    all_alerts = alerts_active + alerts_sursis
    print("\n" + "="*70)
    print("⚖️ TABLEAU DE VEILLE DISCIPLINAIRE ES GENECH (ART. 226 FFF)")
    print("="*70)
    print(df_discipline.to_string(index=False))
    print("\n--- CONSIGNES TACTIQUES / STAFF : ---")
    for a in all_alerts:
        print(f"  {a}")
    print("="*70 + "\n")

    return df_discipline, all_alerts

if __name__ == "__main__":
    analyze_discipline()
