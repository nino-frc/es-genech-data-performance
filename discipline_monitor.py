"""
Module de Veille Disciplinaire Interne - ES Genech
Application des règlements officiels FFF (Article 226 des Règlements Généraux)
Règle : 3 cartons jaunes en moins de 3 mois (90 jours) = 1 match de suspension automatique
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

# Dictionnaire de réconciliation des noms (FFF Coupe de France = complet, R3 = prénom + initiale)
NAME_MAPPING = {
    "MATHYS H.": "MATHYS HERVE",
    "GASPARD D.": "GASPARD DROUPSY",
    "AUGUSTIN D.": "AUGUSTIN DROUPSY",
    "HUGO H.": "HUGO HERVE",
    "JULIEN D.": "JULIEN DEVERNAY",
    "JULIEN N.": "JULIEN NISSE",
    "MAXIME P.": "MAXIME PETIT",
    "REMI D.": "REMI DELOBEL",
    "GIOVANY C.": "GIOVANY CLERY",
    "CLEMENT D.": "CLEMENT DELELIS",
    "TIM L.": "TIM LECLERCQ",
    "THOMAS L.": "THOMAS LEONARD"
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
    cur = conn.cursor()

    query = """
    SELECT me.id, me.match_id, m.competition_id, m.tour_ou_journee, m.date_heure, 
           me.type_event, me.acteur_principal, me.minute
    FROM match_events me
    JOIN matchs m ON m.id = me.match_id
    WHERE me.type_event IN ('AVERTISSEMENT', 'EXPULSION')
      AND (me.equipe LIKE '%GENECH%' OR me.equipe = '')
    ORDER BY m.date_heure ASC;
    """
    df_cards = pd.read_sql_query(query, conn)
    conn.close()

    if df_cards.empty:
        print("Aucun carton enregistré.")
        return pd.DataFrame(), []

    df_cards['player_norm'] = df_cards['acteur_principal'].apply(normalize_player_name)
    df_cards['date_match'] = pd.to_datetime(df_cards['date_heure'])

    # Fenêtre glissante de 90 jours (3 mois)
    window_start = reference_date - timedelta(days=90)

    discipline_records = []
    alerts = []

    unique_players = df_cards['player_norm'].unique()

    for player in unique_players:
        p_cards = df_cards[df_cards['player_norm'] == player].sort_values(by='date_match')
        
        # Cartons dans les 90 derniers jours
        recent_yellows = p_cards[(p_cards['date_match'] >= window_start) & (p_cards['type_event'] == 'AVERTISSEMENT')]
        total_recent_j = len(recent_yellows)
        total_recent_r = len(p_cards[(p_cards['date_match'] >= window_start) & (p_cards['type_event'] == 'EXPULSION')])

        dates_cartons = [d.strftime('%d/%m') for d in recent_yellows['date_match']]
        dates_str = ", ".join(dates_cartons) if dates_cartons else "-"

        # Évaluation du statut juridique FFF
        if total_recent_r > 0 or total_recent_j >= 3:
            statut_disciplinaire = "SUSPENDU / COMMISSION FFF"
            gravite = "ROUGE"
            expiration_sursis = "-"
            alerte_staff = f"🚨 {player} : 3e carton reçu ({dates_str}). Suspension automatique active ou en cours d'application."
            alerts.append(alerte_staff)
        elif total_recent_j == 2:
            statut_disciplinaire = "SOUS SURSIS IMMÉDIAT"
            gravite = "ORANGE"
            # Date d'expiration = 90 jours après le 1er carton du cycle
            first_card_date = recent_yellows['date_match'].iloc[0]
            exp_date = first_card_date + timedelta(days=90)
            expiration_sursis = exp_date.strftime('%d/%m/%Y')
            alerte_staff = f"⚠️ {player} : 2 cartons ({dates_str}). Prochain carton jaune = 1 match de suspension automatique ! (Sursis jusqu'au {expiration_sursis})."
            alerts.append(alerte_staff)
        elif total_recent_j == 1:
            statut_disciplinaire = "AVERTI (1 JAUNE)"
            gravite = "JAUNE"
            first_card_date = recent_yellows['date_match'].iloc[0]
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
    # Tri : les plus à risque en premier
    sort_order = {"ROUGE": 0, "ORANGE": 1, "JAUNE": 2, "VERT": 3}
    df_discipline['sort_key'] = df_discipline['niveau_alerte'].map(sort_order)
    df_discipline = df_discipline.sort_values(by=['sort_key', 'cartons_jaunes_90j'], ascending=[True, False]).drop(columns=['sort_key'])

    # Export CSV pour Power BI
    output_csv = os.path.join(OUTPUT_DIR, "dim_discipline_genech.csv")
    df_discipline.to_csv(output_csv, index=False, encoding="utf-8-sig")

    print("\n" + "="*70)
    print("⚖️ TABLEAU DE VEILLE DISCIPLINAIRE ES GENECH (ART. 226 FFF)")
    print("="*70)
    print(df_discipline.to_string(index=False))
    print("\n--- CONSIGNES TACTIQUES / STAFF : ---")
    for a in alerts:
        print(f"  {a}")
    print("="*70 + "\n")

    return df_discipline, alerts

if __name__ == "__main__":
    analyze_discipline()
