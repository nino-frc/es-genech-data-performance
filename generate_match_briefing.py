import sqlite3
import os
import re
import base64
import pandas as pd
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "genech_performance.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "briefings_coach")
LOGO_PATH = os.path.join(BASE_DIR, "logo_genech_transparent.png")
os.makedirs(OUTPUT_DIR, exist_ok=True)

from discipline_monitor import analyze_discipline
from weather_pitch import get_match_weather
from referee_scout import scout_referee

def launch_browser(p):
    args = ['--disable-blink-features=AutomationControlled', '--no-sandbox']
    try:
        return p.chromium.launch(channel="chrome", headless=True, args=args)
    except Exception:
        return p.chromium.launch(headless=True, args=args)

def generate_mobile_briefing():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    df_matchs = pd.read_sql_query("SELECT * FROM matchs", conn)
    df_events = pd.read_sql_query("SELECT * FROM match_events", conn)

    # Encode logo
    logo_b64 = ""
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode("utf-8")

    # 1. MATCH PRÉCÉDENT (DERNIER MATCH TERMINÉ)
    s_term = df_matchs[
        (df_matchs['statut'] == 'TERMINE') & 
        ((df_matchs['equipe_domicile'].str.contains('GENECH', case=False, na=False)) |
         (df_matchs['equipe_exterieur'].str.contains('GENECH', case=False, na=False)))
    ].sort_values(by='date_heure', ascending=False)

    if not s_term.empty:
        last_match = s_term.iloc[0]
        last_comp = "Coupe de France" if last_match['competition_id'] == 'cdf_2026' else "Régional 3"
        last_tour = last_match['tour_ou_journee']
        last_dom = last_match['equipe_domicile']
        last_ext = last_match['equipe_exterieur']
        s_dom = int(last_match['score_domicile']) if pd.notnull(last_match['score_domicile']) else 0
        s_ext = int(last_match['score_exterieur']) if pd.notnull(last_match['score_exterieur']) else 0
        
        is_dom = "GENECH" in last_dom.upper()
        genech_score = s_dom if is_dom else s_ext
        opp_score = s_ext if is_dom else s_dom
        
        if genech_score > opp_score:
            res_tag = "VICTOIRE"
            res_color = "#15803d"
        elif genech_score == opp_score:
            res_tag = "MATCH NUL"
            res_color = "#ebb837"
        else:
            res_tag = "DÉFAITE"
            res_color = "#b91c1c"

        # Buteurs du dernier match
        last_events = df_events[(df_events['match_id'] == last_match['id']) & (df_events['type_event'] == 'BUT')]
        buteurs_genech = last_events[last_events['equipe'].str.contains('GENECH', case=False, na=False)]['acteur_principal'].tolist()
        buteurs_txt = ", ".join(buteurs_genech) if buteurs_genech else "Aucun buteur ESG"
    else:
        last_comp, last_tour, last_dom, last_ext = "Régional 3", "-", "GENECH ES", "-", 0, 0
        s_dom, s_ext = 0, 0
        res_tag, res_color, buteurs_txt = "EN COURS", "#ebb837", "-"

    # 2. PROCHAIN ADVERSAIRE (PROCHAIN MATCH À VENIR)
    s_avenir = df_matchs[
        (df_matchs['statut'] == 'A_VENIR') & 
        ((df_matchs['equipe_domicile'].str.contains('GENECH', case=False, na=False)) |
         (df_matchs['equipe_exterieur'].str.contains('GENECH', case=False, na=False)))
    ].sort_values(by='date_heure', ascending=True)

    if not s_avenir.empty:
        next_match = s_avenir.iloc[0]
        next_comp = "Coupe de France" if next_match['competition_id'] == 'cdf_2026' else "Régional 3 (Poule D)"
        next_tour = next_match['tour_ou_journee']
        next_dom = next_match['equipe_domicile']
        next_ext = next_match['equipe_exterieur']
        next_date = next_match['date_heure']
        is_next_dom = "GENECH" in next_dom.upper()
        opp_name = next_ext if is_next_dom else next_dom
    else:
        next_comp, next_tour = "Régional 3 (Poule D)", "Prochaine Journée"
        next_dom, next_ext = "GENECH ES", "ADVERSAIRE"
        next_date = "À déterminer"
        opp_name = "ADVERSAIRE"

    # Calcul des scores réels officiels DE GENECH UNIQUEMENT
    s_term_all = s_term.copy()
    s_term_all['is_dom'] = s_term_all['equipe_domicile'].str.contains('GENECH', case=False, na=False)
    s_term_all['buts_pour'] = s_term_all.apply(lambda r: r['score_domicile'] if r['is_dom'] else r['score_exterieur'], axis=1)
    s_term_all['buts_contre'] = s_term_all.apply(lambda r: r['score_exterieur'] if r['is_dom'] else r['score_domicile'], axis=1)

    total_buts_marques = int(s_term_all['buts_pour'].sum())
    total_buts_encaisses = int(s_term_all['buts_contre'].sum())

    # Cartons Genech
    cartons_genech = df_events[(df_events['type_event'] == 'AVERTISSEMENT') & (df_events['equipe'].str.contains('GENECH', case=False, na=False))]
    cartons_count = len(cartons_genech)
    cartons_anstaing_derby = len(cartons_genech[cartons_genech['match_id'].str.contains('anstaing', case=False, na=False)])

    is_tatinghem = "TATINGHEM" in opp_name.upper()
    is_aniche = "ANICHE" in opp_name.upper()

    weather_info = get_match_weather(next_dom, next_date)
    ref_target = "LOUIS LAURENT" if is_tatinghem else "Désignation FFF"
    referee_info = scout_referee(ref_target)

    _, alerts_disc = analyze_discipline()
    alert_sursis_txt = alerts_disc[0] if alerts_disc else "Aucun joueur sous le coup d'une suspension immédiate. Discipline maîtrisée."

    # Quarts d'Heure Genech
    df_buts = df_events[df_events['type_event'] == 'BUT'].copy()
    df_buts['is_genech'] = df_buts['equipe'].str.contains('GENECH', case=False, na=False)

    tranches = ["01-15'", "16-30'", "31-45+'", "46-60'", "61-75'", "76-90+'"]
    buts_pour = []
    buts_contre = []
    for t in tranches:
        buts_pour.append(len(df_buts[(df_buts['tranche_quart_heure'] == t) & (df_buts['is_genech'])]))
        buts_contre.append(len(df_buts[(df_buts['tranche_quart_heure'] == t) & (~df_buts['is_genech'])]))

    # Récupération ou génération du scouting de l'adversaire
    is_tatinghem = "TATINGHEM" in opp_name.upper()
    is_aniche = "ANICHE" in opp_name.upper()

    if is_tatinghem:
        scout_badge = "R3 Côte d'Opale"
        scout_alert_title = "🚨 ALERTE SUSPENSION : MOUAAD MADRI (ATT. VEDETTE ADVERSE)"
        scout_alert_desc = "3 cartons jaunes reçus en moins de 3 mois (CDF T2 88', R3 J3 27', CDF T5 48'). En vertu de l'art. 226 des Règlements FFF, sa suspension prend effet le 19/10/2026.<br/>👉 <strong>CONSIGNE STAFF :</strong> S'il est inscrit sur la feuille FMI, <strong>poser une réserve d'avant-match immédiate (victoire sur tapis vert possible)</strong>."
        scout_box1_title = "⚡ Démarrage Canon & Profil"
        scout_box1_desc = "Attaque prolifique (14 buts en 4 matchs). Ils pressent très haut dès le coup d'envoi et marquent souvent d'entrée (5' vs Neufchâtel, 39' vs Mouvaux). Être ultra-vigilant sur les 15 premières minutes."
        scout_box2_title = "⚠️ Faille Physique en Fin de Match"
        scout_box2_desc = "<strong>Baisse de régime après la 70e :</strong> 2 buts concédés face à Neufchâtel (74' et 90'). Équipe agressive (4 cartons au 5e Tour) qui commet des fautes sous la fatigue."
        h2h_opp_form = "V - V - N - V (10 pts)"
        h2h_opp_att = "14 Buts (3.5 / m)"
        h2h_opp_def = "3 Buts (Fébrile en fin de match)"
    elif is_aniche:
        scout_badge = "R3 Poule D • 2e Ex-Aequo"
        scout_alert_title = "⚔️ CHOC DU HAUT DE TABLEAU : ANICHE SC (8 PTS)"
        scout_alert_desc = "Aniche partage la 2e place avec Genech (8 pts, 2V 2N 0D). Équipe extrêmement hermétique (seulement 3 buts concédés en 4 matchs).<br/>👉 <strong>ENJEU :</strong> Le vainqueur s'empare seul de la place de dauphin direct de Beuvry."
        scout_box1_title = "🛡️ Solidité Défensive Élite"
        scout_box1_desc = "Bloc très compact en 4-4-2 ou 5-3-2. Seulement 3 buts encaissés (0.75 b/m). Deux clean sheets déjà réalisés cette saison (0-2 à Guesnain)."
        scout_box2_title = "⚡ Jeu de Transition Rapide"
        scout_box2_desc = "Peu de possession stérile : ils procèdent par attaques rapides dès la récupération au milieu. Attention aux pertes de balle dans nos 30 mètres."
        h2h_opp_form = "V - V - N - N (8 pts • Invaincu)"
        h2h_opp_att = "6 Buts (1.5 / m)"
        h2h_opp_def = "3 Buts (0.75 / m • 2 Clean Sheets)"
    else:
        scout_badge = "R3 Poule D"
        scout_alert_title = f"🎯 FOCUS ADVERSAIRE : {opp_name}"
        scout_alert_desc = "Analyse tactique automatisée basée sur les résultats de la poule."
        scout_box1_title = "📊 Profil & Dynamique"
        scout_box1_desc = "Données issues du classement et des feuilles de match FFF."
        scout_box2_title = "⚠️ Vigilance Tactique"
        scout_box2_desc = "Rester attentif sur les phases arrêtées et les entames de mi-temps."
        h2h_opp_form = "En cours"
        h2h_opp_att = "Données FFF"
        h2h_opp_def = "Données FFF"

    # HTML Template
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>ES Genech - Mobile Matchday & Scouting</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800;900&family=Oswald:wght@600;700&display=swap');

            * {{
                box-sizing: border-box;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            body {{
                font-family: 'Montserrat', sans-serif;
                margin: 0;
                padding: 24px 28px;
                background-color: #ede8d8;
                color: #0a1728;
                width: 1080px;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }}

            /* Header Mobile */
            .header {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                background: #0a1728;
                border-radius: 16px;
                padding: 12px 20px;
                color: white;
                box-shadow: 0 6px 18px rgba(10, 23, 40, 0.15);
                border: 2px solid #ebb837;
            }}
            .header-left {{
                display: flex;
                align-items: center;
                gap: 14px;
            }}
            .club-logo {{
                width: 58px;
                height: 58px;
                border-radius: 50%;
                border: 3px solid #ebb837;
                padding: 2px;
                background: #0a1728;
            }}
            .club-title h1 {{
                font-family: 'Oswald', sans-serif;
                font-size: 25px;
                font-weight: 700;
                margin: 0;
                letter-spacing: 1px;
                text-transform: uppercase;
                color: #ffffff;
            }}
            .club-title h1 span {{ color: #ebb837; }}
            .club-title p {{
                margin: 2px 0 0 0;
                font-size: 11px;
                font-weight: 700;
                color: #cbd5e1;
                text-transform: uppercase;
            }}
            .header-badge {{
                background: #ebb837;
                color: #0a1728;
                padding: 7px 13px;
                border-radius: 10px;
                text-align: center;
                font-weight: 800;
            }}
            .header-badge .comp {{
                font-family: 'Oswald', sans-serif;
                font-size: 11px;
                text-transform: uppercase;
            }}
            .header-badge .tour {{
                font-size: 13px;
                font-weight: 900;
            }}

            /* NOUVEAU BANNER : DERNIER MATCH DISPUTÉ */
            .last-match-banner {{
                background: white;
                border-radius: 12px;
                padding: 9px 16px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                border-left: 6px solid {res_color};
                box-shadow: 0 4px 10px rgba(10, 23, 40, 0.05);
            }}
            .last-match-left {{
                display: flex;
                flex-direction: column;
                gap: 2px;
            }}
            .last-match-tag {{
                font-size: 9px;
                font-weight: 800;
                color: #64748b;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .last-match-score {{
                font-family: 'Oswald', sans-serif;
                font-size: 17px;
                font-weight: 700;
                color: #0a1728;
                text-transform: uppercase;
            }}
            .last-match-buteurs {{
                font-size: 9px;
                color: #475569;
                font-weight: 600;
            }}
            .last-match-pill {{
                background: {res_color};
                color: white;
                font-size: 10px;
                font-weight: 900;
                padding: 4px 10px;
                border-radius: 6px;
                text-transform: uppercase;
            }}

            /* Hero Matchday */
            .match-hero {{
                background: #0a1728;
                border-radius: 14px;
                padding: 10px 18px;
                color: white;
                text-align: center;
                border-bottom: 4px solid #e8590c;
            }}
            .hero-tag {{
                display: inline-block;
                background: #e8590c;
                color: white;
                font-size: 9.5px;
                font-weight: 800;
                padding: 2px 10px;
                border-radius: 20px;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 4px;
            }}
            .hero-teams {{
                font-family: 'Oswald', sans-serif;
                font-size: 24px;
                font-weight: 700;
                text-transform: uppercase;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 12px;
            }}
            .hero-teams .vs {{ color: #ebb837; font-size: 17px; }}

            /* Conditions Météo & Arbitre */
            .env-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px;
            }}
            .env-box {{
                background: #0a1728;
                border-radius: 10px;
                padding: 7px 11px;
                color: white;
                border-left: 4px solid #ebb837;
            }}
            .env-box.referee {{
                border-left-color: #e8590c;
            }}
            .env-box-title {{
                font-family: 'Oswald', sans-serif;
                font-size: 11px;
                font-weight: 700;
                color: #ebb837;
                text-transform: uppercase;
                margin-bottom: 2px;
            }}
            .env-box.referee .env-box-title {{
                color: #f87171;
            }}
            .env-box-body {{
                font-size: 8px;
                line-height: 1.35;
                color: #e2e8f0;
            }}

            /* 4 KPIs */
            .kpi-grid {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 10px;
            }}
            .kpi-card {{
                background: white;
                border-radius: 12px;
                padding: 9px 12px;
                border-left: 5px solid #0a1728;
                box-shadow: 0 4px 10px rgba(10, 23, 40, 0.05);
            }}
            .kpi-card.gold {{ border-left-color: #ebb837; }}
            .kpi-card.orange {{ border-left-color: #e8590c; }}
            .kpi-label {{
                font-size: 8.5px;
                font-weight: 800;
                text-transform: uppercase;
                color: #64748b;
            }}
            .kpi-val {{
                font-family: 'Oswald', sans-serif;
                font-size: 22px;
                font-weight: 700;
                color: #0a1728;
                margin: 2px 0;
            }}
            .kpi-sub {{
                font-size: 8px;
                color: #475569;
                font-weight: 600;
            }}

            /* Face-à-face Statistique */
            .h2h-card {{
                background: white;
                border-radius: 12px;
                padding: 10px 14px;
                box-shadow: 0 4px 10px rgba(10, 23, 40, 0.05);
                border: 1px solid #cbd5e1;
            }}
            .h2h-title {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-family: 'Oswald', sans-serif;
                font-size: 13px;
                font-weight: 700;
                color: #0a1728;
                text-transform: uppercase;
                border-bottom: 2px solid #ebb837;
                padding-bottom: 3px;
                margin-bottom: 6px;
            }}
            .h2h-grid {{
                display: grid;
                grid-template-columns: 1fr 1.2fr 1fr;
                gap: 5px;
                font-size: 9px;
                align-items: center;
                text-align: center;
            }}
            .h2h-team-name {{
                font-weight: 800;
                font-size: 10px;
                text-transform: uppercase;
            }}
            .h2h-stat-label {{
                color: #64748b;
                font-size: 8px;
                font-weight: 700;
                text-transform: uppercase;
            }}
            .h2h-stat-val {{
                font-weight: 800;
                font-size: 9.5px;
            }}

            /* Benchmark Saisons R3 */
            .benchmark-card {{
                background: white;
                border-radius: 12px;
                padding: 9px 14px;
                box-shadow: 0 4px 10px rgba(10, 23, 40, 0.05);
                border-left: 5px solid #004687;
            }}
            .benchmark-title {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-family: 'Oswald', sans-serif;
                font-size: 13px;
                font-weight: 700;
                color: #004687;
                text-transform: uppercase;
                border-bottom: 2px solid #004687;
                padding-bottom: 3px;
                margin-bottom: 5px;
            }}
            .benchmark-table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 8.5px;
                text-align: center;
            }}
            .benchmark-table th {{
                background: #f8fafc;
                color: #475569;
                padding: 4px;
                font-weight: 800;
                text-transform: uppercase;
            }}
            .benchmark-table td {{
                padding: 4px 5px;
                border-bottom: 1px solid #f1f5f9;
            }}
            .benchmark-table tr.current {{
                background: #fef3c7;
                font-weight: 800;
            }}

            /* Scouting Opposant Card */
            .scouting-card {{
                background: #0a1728;
                color: white;
                border-radius: 14px;
                padding: 10px 14px;
                border: 2px solid #e8590c;
            }}
            .scouting-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1.5px solid #e8590c;
                padding-bottom: 4px;
                margin-bottom: 6px;
            }}
            .scouting-title {{
                font-family: 'Oswald', sans-serif;
                font-size: 14px;
                font-weight: 700;
                color: #ffffff;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .scouting-badge {{
                background: #e8590c;
                color: white;
                font-size: 8px;
                font-weight: 800;
                padding: 2px 7px;
                border-radius: 5px;
                text-transform: uppercase;
            }}

            /* ALERTE SUSPENSION / ENJEU */
            .alert-suspension {{
                background: #b91c1c;
                border-radius: 8px;
                padding: 7px 10px;
                margin-bottom: 6px;
                border-left: 4px solid #fef08a;
            }}
            .alert-suspension-title {{
                font-family: 'Oswald', sans-serif;
                font-size: 11.5px;
                font-weight: 700;
                color: #fef08a;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .alert-suspension-desc {{
                font-size: 8.5px;
                line-height: 1.35;
                color: #fef2f2;
                margin-top: 2px;
            }}

            .scouting-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px;
            }}
            .scout-box {{
                background: rgba(255, 255, 255, 0.06);
                border-radius: 8px;
                padding: 6px 9px;
            }}
            .scout-box-title {{
                font-size: 8.5px;
                font-weight: 800;
                color: #ebb837;
                text-transform: uppercase;
                margin-bottom: 2px;
            }}

            /* Alerte Discipline Interne ESG */
            .esg-disc-card {{
                background: white;
                border-radius: 10px;
                padding: 8px 12px;
                border-left: 5px solid #e8590c;
                box-shadow: 0 4px 10px rgba(10, 23, 40, 0.05);
            }}
            .esg-disc-header {{
                font-family: 'Oswald', sans-serif;
                font-size: 11px;
                font-weight: 700;
                color: #b91c1c;
                text-transform: uppercase;
                margin-bottom: 2px;
            }}
            .esg-disc-text {{
                font-size: 8.5px;
                color: #334155;
                line-height: 1.35;
            }}
            .section-card {{
                background: white;
                border-radius: 12px;
                padding: 9px 14px;
                box-shadow: 0 4px 10px rgba(10, 23, 40, 0.05);
            }}
            .section-title {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-family: 'Oswald', sans-serif;
                font-size: 13px;
                font-weight: 700;
                color: #0a1728;
                text-transform: uppercase;
                border-bottom: 2px solid #ebb837;
                padding-bottom: 3px;
                margin-bottom: 5px;
            }}
            .tranche-table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 8.5px;
            }}
            .tranche-table th {{
                text-align: left;
                padding: 3px 6px;
                color: #64748b;
                font-weight: 800;
                text-transform: uppercase;
                border-bottom: 1.5px solid #e2e8f0;
            }}
            .tranche-table td {{
                padding: 4px 6px;
                border-bottom: 1px solid #f1f5f9;
            }}
            .bar-pour {{
                background: #0a1728;
                height: 9px;
                border-radius: 2px;
                display: inline-block;
                border-left: 3px solid #ebb837;
            }}
            .bar-contre {{
                background: #e8590c;
                height: 9px;
                border-radius: 2px;
                display: inline-block;
            }}

            /* Causerie Coach */
            .briefing-box {{
                background: #0a1728;
                color: white;
                border-radius: 12px;
                padding: 8px 14px;
                border-left: 5px solid #ebb837;
            }}
            .briefing-title {{
                font-family: 'Oswald', sans-serif;
                font-size: 11.5px;
                font-weight: 700;
                color: #ebb837;
                text-transform: uppercase;
                margin-bottom: 3px;
            }}
            .briefing-box ul {{
                margin: 0;
                padding-left: 14px;
                font-size: 8.5px;
                line-height: 1.35;
                color: #e2e8f0;
            }}
            .briefing-box li {{ margin-bottom: 2px; }}
            .briefing-box strong {{ color: #ebb837; }}

            /* Footer Mobile ESG */
            .footer {{
                background: #ebb837;
                border-radius: 12px;
                padding: 8px 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                color: #0a1728;
                font-weight: 800;
            }}
            .footer .slogan {{
                font-family: 'Oswald', sans-serif;
                font-size: 13px;
                letter-spacing: 1px;
                text-transform: uppercase;
            }}
            .footer .tag {{ font-size: 8px; font-weight: 800; }}
        </style>
    </head>
    <body>

        <!-- Header -->
        <div class="header">
            <div class="header-left">
                <img class="club-logo" src="data:image/png;base64,{logo_b64}" alt="Logo ES Genech">
                <div class="club-title">
                    <h1>ES <span>GENECH</span></h1>
                    <p>Cellule Performance • Staff Senior 1</p>
                </div>
            </div>
            <div class="header-badge">
                <div class="comp">{next_comp}</div>
                <div class="tour">{next_tour}</div>
            </div>
        </div>

        <!-- 1. BANNER SCORE DU MATCH PRÉCÉDENT -->
        <div class="last-match-banner">
            <div class="last-match-left">
                <div class="last-match-tag">⏮️ RÉSULTAT DU MATCH PRÉCÉDENT • {last_comp} ({last_tour})</div>
                <div class="last-match-score">{last_dom} {s_dom} - {s_ext} {last_ext}</div>
                <div class="last-match-buteurs">Buteurs ESG : {buteurs_txt}</div>
            </div>
            <div class="last-match-pill">{res_tag}</div>
        </div>

        <!-- 2. HERO PROCHAIN MATCH -->
        <div class="match-hero">
            <div class="hero-tag">Affiche Officielle • {next_date}</div>
            <div class="hero-teams">
                {next_dom} <span class="vs">VS</span> {next_ext}
            </div>
        </div>

        <!-- Conditions Météo & Arbitre Officiel -->
        <div class="env-grid">
            <div class="env-box">
                <div class="env-box-title">🌦️ Météo & Terrain • {weather_info['lieu']}</div>
                <div class="env-box-body">
                    <strong>{weather_info['temperature']}</strong> • Vent : {weather_info['vent']} • Pluie : {weather_info['pluie']}<br/>
                    <span style="color:#cbd5e1;">Surface : {weather_info['surface']} — {weather_info['consigne_tactique']}</span>
                </div>
            </div>
            <div class="env-box referee">
                <div class="env-box-title">👨‍⚖️ Arbitre Officiel • {referee_info['nom_arbitre']}</div>
                <div class="env-box-body">
                    Sévérité : <strong style="color:#f87171;">{referee_info['severite']}</strong> ({referee_info['moyenne_jaunes']} J / match)<br/>
                    <span style="color:#cbd5e1;">{referee_info['consigne_coach']}</span>
                </div>
            </div>
        </div>

        <!-- 3. 4 Cartes KPIs Re-filtrées -->
        <div class="kpi-grid">
            <div class="kpi-card gold">
                <div class="kpi-label">Invincibilité ESG</div>
                <div class="kpi-val">8 Matchs</div>
                <div class="kpi-sub">0 défaite TCC cette saison</div>
            </div>
            <div class="kpi-card orange">
                <div class="kpi-label">Clean Sheets</div>
                <div class="kpi-val">5 / 8</div>
                <div class="kpi-sub">4 en Coupe + 1 en R3 (vs Maubeuge)</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Attaque ESG</div>
                <div class="kpi-val">{total_buts_marques} Buts</div>
                <div class="kpi-sub">Scores FFF : 6 en R3 + 4 en CDF</div>
            </div>
            <div class="kpi-card orange">
                <div class="kpi-label">Cartons Jaunes</div>
                <div class="kpi-val">{cartons_count} J</div>
                <div class="kpi-sub">Dont {cartons_anstaing_derby} lors du derby vs Anstaing</div>
            </div>
        </div>

        <!-- 4. FACE-A-FACE STATISTIQUE AVANT-MATCH -->
        <div class="h2h-card">
            <div class="h2h-title">
                <span>⚔️ Le Face-à-Face : {opp_name} vs ES Genech</span>
                <span style="font-size: 8.5px; color:#64748b;">Statistiques Officielles 2026/2027</span>
            </div>
            <div class="h2h-grid">
                <div class="h2h-team-name" style="color: #0a1728;">{opp_name}</div>
                <div class="h2h-stat-label">DYNAMIQUE RÉCENTE</div>
                <div class="h2h-team-name" style="color: #0a1728;">ES GENECH</div>

                <div class="h2h-stat-val" style="color: #15803d;">{h2h_opp_form}</div>
                <div class="h2h-stat-label">FORME OFFICIELLE</div>
                <div class="h2h-stat-val" style="color: #15803d;">V - V - N - N (8 pts • Invaincu)</div>

                <div class="h2h-stat-val">{h2h_opp_att}</div>
                <div class="h2h-stat-label">ATTAQUE RÉCENTE</div>
                <div class="h2h-stat-val" style="color: #004687;">6 Buts (1.5 / m)</div>

                <div class="h2h-stat-val" style="color: #b91c1c;">{h2h_opp_def}</div>
                <div class="h2h-stat-label">DÉFENSE & CLEAN SHEETS</div>
                <div class="h2h-stat-val" style="color: #15803d;">0.75 b/m en R3 (0 en Coupe)</div>
            </div>
        </div>

        <!-- 5. TABLEAU COMPARATIF DES SAISONS EN R3 -->
        <div class="benchmark-card">
            <div class="benchmark-title">
                <span>📈 Repères de Performance : Comparatif des Saisons en R3</span>
                <span style="font-size: 8.5px; color: #64748b;">Source : Archives LFHF</span>
            </div>
            <table class="benchmark-table">
                <thead>
                    <tr>
                        <th>Saison</th>
                        <th>Niveau</th>
                        <th>Points / Match</th>
                        <th>Défense (Buts / Match)</th>
                        <th>Parcours Coupe de France</th>
                        <th>Statut Défaites</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>2023-2024</strong></td>
                        <td>Régional 3 (Hauts-de-France)</td>
                        <td>1.95 PPM</td>
                        <td>0.90 but / match</td>
                        <td>Élimination Tour 3</td>
                        <td>5 défaites</td>
                    </tr>
                    <tr>
                        <td><strong>2024-2025</strong></td>
                        <td>R3 Poule E (<strong>Champion & Montée</strong>)</td>
                        <td>2.09 PPM (46 pts / 22 J)</td>
                        <td><strong>0.68 but / match</strong> (15 buts pris)</td>
                        <td>Élimination Tour 4</td>
                        <td>4 défaites</td>
                    </tr>
                    <tr class="current">
                        <td><strong>2026-2027</strong></td>
                        <td>R3 Poule D (<strong>Saison en cours</strong>)</td>
                        <td><strong>2.00 PPM</strong> (8 pts / 4 J)</td>
                        <td><strong>0.75 but / match</strong> (3 buts pris)</td>
                        <td><strong>🔥 6e Tour (0 but pris • Invaincu)</strong></td>
                        <td><strong>0 DÉFAITE (Invaincue)</strong></td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- 6. BLOC SCOUTING ADVERSAIRE + ALERTE JURIDIQUE / TACTIQUE -->
        <div class="scouting-card">
            <div class="scouting-header">
                <div class="scouting-title">🎯 Espionnage Tactique : {opp_name}</div>
                <div class="scouting-badge">{scout_badge}</div>
            </div>

            <!-- ENCADRÉ ROUGE ALERTE -->
            <div class="alert-suspension">
                <div class="alert-suspension-title">{scout_alert_title}</div>
                <div class="alert-suspension-desc">{scout_alert_desc}</div>
            </div>

            <div class="scouting-grid">
                <div class="scout-box">
                    <div class="scout-box-title">{scout_box1_title}</div>
                    <div style="font-size:8.5px; color:#cbd5e1; line-height:1.35;">
                        {scout_box1_desc}
                    </div>
                </div>
                <div class="scout-box">
                    <div class="scout-box-title">{scout_box2_title}</div>
                    <div style="font-size:8.5px; color:#cbd5e1; line-height:1.35;">
                        {scout_box2_desc}
                    </div>
                </div>
            </div>
        </div>

        <!-- 7. Quarts d'Heure Genech -->
        <div class="section-card">
            <div class="section-title">
                <span>⏱️ Efficacité par Quart d'Heure (ESG)</span>
                <span style="font-size: 8.5px; color:#64748b;">ESG (Bleu) vs Adv (Orange)</span>
            </div>
            <table class="tranche-table">
                <thead>
                    <tr>
                        <th>Minute</th>
                        <th>Pour (ESG)</th>
                        <th>Contre</th>
                        <th>Constat Tactique</th>
                    </tr>
                </thead>
                <tbody>
    """

    constats = [
        "Départ prudent • Prise de repères défensifs",
        "Pression progressive au milieu",
        "Accélération avant pause • 2 buts clés",
        "Entame de 2e mi-temps percutante",
        "Temps fort ESG • 3 buts marqués",
        "Money time géré avec rigueur (1 seul but pris)"
    ]

    for i, t in enumerate(tranches):
        w_p = buts_pour[i] * 38
        w_c = buts_contre[i] * 38
        bar_p = f'<div class="bar-pour" style="width: {w_p}px;"></div> {buts_pour[i]}' if buts_pour[i] > 0 else '0'
        bar_c = f'<div class="bar-contre" style="width: {w_c}px;"></div> {buts_contre[i]}' if buts_contre[i] > 0 else '0'

        html_content += f"""
                    <tr>
                        <td><strong>{t}</strong></td>
                        <td>{bar_p}</td>
                        <td>{bar_c}</td>
                        <td style="color:#475569;">{constats[i]}</td>
                    </tr>
        """

    html_content += f"""
                </tbody>
            </table>
        </div>

        <!-- Veille Disciplinaire Interne ESG -->
        <div class="esg-disc-card">
            <div class="esg-disc-header">⚖️ Veille Disciplinaire Interne (Règle FFF Art. 226)</div>
            <div class="esg-disc-text">{alert_sursis_txt}</div>
        </div>

        <!-- 8. Causerie Coach Callout & Facteurs Clés -->
        <div class="briefing-box">
            <div class="briefing-title">📋 3 Facteurs Clés de Victoire pour le Match</div>
            <ul>
                <li><strong>Premier But Capital (100 % Victoires) :</strong> Dès que Genech ouvre le score (3/3), l'équipe gagne systématiquement. Imposer un pressing haut d'entrée.</li>
                <li><strong>Puissance en 2nde Mi-Temps :</strong> 75 % de nos buts sont inscrits après la pause. Maintenir une intensité maximale pour faire craquer l'adversaire après la 60e.</li>
                <li><strong>Maîtrise & Sang-Froid (+1 pt / match) :</strong> Genech tourne à 2.60 PPM avec ≤ 1 carton vs 1.67 PPM avec ≥ 2 cartons. Zéro contestation avec le corps arbitral.</li>
            </ul>
        </div>

        <!-- Footer -->
        <div class="footer">
            <div class="slogan">TOUJOURS ENSEMBLE • ALLEZ L'ESG</div>
            <div class="tag">Cellule Performance • Auto-Update Lundi/Vendredi</div>
        </div>

    </body>
    </html>
    """

    # Rendu PDF et PNG avec Playwright
    with sync_playwright() as p:
        browser = launch_browser(p)
        page = browser.new_page(viewport={"width": 1080, "height": 1920})
        page.set_content(html_content, wait_until="networkidle")

        # Sortie standard toujours à jour
        latest_png = os.path.join(OUTPUT_DIR, "briefing_match_latest.png")
        latest_pdf = os.path.join(OUTPUT_DIR, "briefing_match_latest.pdf")
        
        # Sortie spécifique
        slug = re.sub(r'[^a-zA-Z0-9]', '_', opp_name.lower()).strip('_')
        specific_png = os.path.join(OUTPUT_DIR, f"briefing_match_{slug}.png")
        specific_pdf = os.path.join(OUTPUT_DIR, f"briefing_match_{slug}.pdf")

        page.screenshot(path=latest_png, full_page=True)
        page.screenshot(path=specific_png, full_page=True)
        page.pdf(path=latest_pdf, print_background=True, width="1080px", height="1920px")
        page.pdf(path=specific_pdf, print_background=True, width="1080px", height="1920px")

        browser.close()

    conn.close()
    print(f"Fiche Mobile Dynamique générée avec succès pour le prochain match : {opp_name} !")
    print(f"Dernier match intégré : {last_dom} {s_dom} - {s_ext} {last_ext} ({res_tag})")

if __name__ == "__main__":
    generate_mobile_briefing()
