"""
Générateur de Débrief Tactique Post-Match (Lundi Matin) - ES Genech
Fiche mobile haute résolution (1080x1920) : Timeline des 90', Ratings joueurs & Alerte Discipline
Projet ES Genech Data Performance - Portfolio SportTech
"""

import os
import sys
import base64
import sqlite3
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "genech_performance.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "briefings_coach")
LOGO_PATH = os.path.join(BASE_DIR, "logo_genech_transparent.png")
os.makedirs(OUTPUT_DIR, exist_ok=True)

from player_rating import calculate_player_ratings
from discipline_monitor import analyze_discipline, normalize_player_name
from substitutions_impact import calculate_substitutions_impact

def launch_browser(p):
    args = ['--disable-blink-features=AutomationControlled', '--no-sandbox']
    try:
        return p.chromium.launch(channel="chrome", headless=True, args=args)
    except Exception:
        return p.chromium.launch(headless=True, args=args)

def generate_postmatch_debrief():
    conn = sqlite3.connect(DB_PATH)

    df_matchs = pd.read_sql_query("SELECT * FROM matchs WHERE statut = 'TERMINE' ORDER BY date_heure DESC", conn)
    df_events = pd.read_sql_query("SELECT * FROM match_events", conn)
    df_lineups = pd.read_sql_query("SELECT * FROM match_lineups", conn)
    conn.close()

    genech_matches = df_matchs[
        (df_matchs['equipe_domicile'].str.contains('GENECH', case=False, na=False)) |
        (df_matchs['equipe_exterieur'].str.contains('GENECH', case=False, na=False))
    ]

    if genech_matches.empty:
        print("Aucun match terminé trouvé pour Genech.")
        return

    last_match = genech_matches.iloc[0]
    mid = last_match['id']
    dom = last_match['equipe_domicile']
    ext = last_match['equipe_exterieur']
    s_dom = int(last_match['score_domicile']) if pd.notnull(last_match['score_domicile']) else 0
    s_ext = int(last_match['score_exterieur']) if pd.notnull(last_match['score_exterieur']) else 0
    comp = "Coupe de France" if last_match['competition_id'] == 'cdf_2026' else "Régional 3 (Poule D)"
    tour = last_match['tour_ou_journee']
    date_str = last_match['date_heure']

    is_dom = "GENECH" in dom.upper()
    s_genech = s_dom if is_dom else s_ext
    s_opp = s_ext if is_dom else s_dom
    opp_name = ext if is_dom else dom

    if s_genech > s_opp:
        issue = "VICTOIRE"
        issue_color = "#15803d"
        issue_sub = "3 points précieux enregistrés" if comp != "Coupe de France" else "Qualification historique pour le tour suivant !"
    elif s_genech == s_opp:
        issue = "MATCH NUL"
        issue_color = "#ebb837"
        issue_sub = "1 point solide acquis dans un match fermé"
    else:
        issue = "DÉFAITE"
        issue_color = "#b91c1c"
        issue_sub = "Points perdus à corriger dès la prochaine journée"

    # Logo Base64
    logo_b64 = ""
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode("utf-8")

    # Événements du match (Timeline)
    m_events = df_events[df_events['match_id'] == mid].sort_values(by=['minute', 'temps_additionnel'])

    # Ratings & Discipline
    df_ratings = calculate_player_ratings()
    df_discipline, alerts_discipline = analyze_discipline()

    # Feuille de match des joueurs de Genech
    m_lineups = df_lineups[(df_lineups['match_id'] == mid) & (df_lineups['equipe'].str.contains('GENECH', case=False, na=False))].copy()
    if not m_lineups.empty:
        m_lineups['player_norm'] = m_lineups['joueur_nom'].apply(normalize_player_name)
    else:
        m_lineups = pd.DataFrame()

    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>ES Genech - Débrief Post-Match</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800;900&family=Oswald:wght@600;700&display=swap');

            * {{
                box-sizing: border-box;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            html, body {{
                font-family: 'Montserrat', sans-serif;
                margin: 0;
                padding: 26px 30px;
                background-color: #ede8d8;
                color: #0a1728;
                width: 1080px;
                height: 1920px;
                max-height: 1920px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                overflow: hidden;
            }}

            /* Header */
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
                padding: 7px 14px;
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

            /* Hero Scoreboard */
            .score-hero {{
                background: #0a1728;
                border-radius: 14px;
                padding: 16px 22px;
                color: white;
                text-align: center;
                border-bottom: 5px solid {issue_color};
                box-shadow: 0 4px 12px rgba(10, 23, 40, 0.12);
                margin: 8px 0;
            }}
            .score-tag {{
                display: inline-block;
                background: {issue_color};
                color: white;
                font-size: 11px;
                font-weight: 900;
                padding: 4px 14px;
                border-radius: 20px;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 6px;
            }}
            .score-display {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 24px;
                margin: 6px 0;
            }}
            .team-name {{
                font-family: 'Oswald', sans-serif;
                font-size: 24px;
                font-weight: 700;
                text-transform: uppercase;
                width: 38%;
            }}
            .team-name.highlight {{ color: #ebb837; }}
            .score-numbers {{
                font-family: 'Oswald', sans-serif;
                font-size: 42px;
                font-weight: 900;
                color: white;
                background: rgba(255, 255, 255, 0.1);
                padding: 4px 22px;
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            .score-sub {{
                font-size: 10px;
                color: #cbd5e1;
                font-weight: 600;
            }}

            /* 4 Grands KPIs Match */
            .match-kpis {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 12px;
                margin: 8px 0;
            }}
            .kpi-box {{
                background: white;
                border-radius: 12px;
                padding: 12px 14px;
                box-shadow: 0 4px 10px rgba(10, 23, 40, 0.05);
                border-left: 5px solid #004687;
            }}
            .kpi-box.green {{ border-left-color: #15803d; }}
            .kpi-box.gold {{ border-left-color: #ebb837; }}
            .kpi-box.orange {{ border-left-color: #e8590c; }}
            .kpi-title {{ font-size: 9px; font-weight: 800; text-transform: uppercase; color: #64748b; }}
            .kpi-value {{ font-family: 'Oswald', sans-serif; font-size: 22px; font-weight: 700; color: #0a1728; margin: 2px 0; }}
            .kpi-desc {{ font-size: 8.5px; color: #475569; font-weight: 600; }}

            /* Feuille de Match Officielle XI & Remplaçants */
            .lineup-card {{
                background: white;
                border-radius: 12px;
                padding: 12px 16px;
                box-shadow: 0 4px 10px rgba(10, 23, 40, 0.05);
                border: 1px solid #cbd5e1;
                margin: 8px 0;
            }}
            .card-title {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-family: 'Oswald', sans-serif;
                font-size: 14px;
                font-weight: 700;
                color: #0a1728;
                text-transform: uppercase;
                border-bottom: 2px solid #ebb837;
                padding-bottom: 4px;
                margin-bottom: 8px;
            }}
            .lineup-grid {{
                display: grid;
                grid-template-columns: 2fr 1fr;
                gap: 14px;
                font-size: 10px;
            }}
            .lineup-group h4 {{
                font-size: 10.5px;
                margin: 0 0 6px 0;
                color: #0a1728;
                text-transform: uppercase;
                font-weight: 800;
            }}
            .player-pill-grid {{
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
            }}
            .player-pill {{
                background: #f1f5f9;
                border-radius: 6px;
                padding: 4px 8px;
                font-weight: 700;
                display: flex;
                align-items: center;
                gap: 5px;
            }}
            .player-pill .p-num {{
                background: #0a1728;
                color: #ebb837;
                padding: 1px 5px;
                border-radius: 4px;
                font-size: 9px;
            }}

            /* Timeline Chronologique 90 min */
            .timeline-card {{
                background: white;
                border-radius: 12px;
                padding: 12px 16px;
                box-shadow: 0 4px 10px rgba(10, 23, 40, 0.05);
                border: 1px solid #cbd5e1;
                margin: 8px 0;
                flex: 1;
                display: flex;
                flex-direction: column;
            }}
            .timeline-list {{
                display: flex;
                flex-direction: column;
                gap: 6px;
                margin-top: 4px;
            }}
            .timeline-item {{
                display: flex;
                align-items: center;
                font-size: 10.5px;
                padding: 6px 10px;
                border-radius: 8px;
                background: #f8fafc;
            }}
            .timeline-item.genech {{
                background: #eff6ff;
                border-left: 4px solid #004687;
            }}
            .timeline-item.adverse {{
                background: #fff7ed;
                border-left: 4px solid #e8590c;
            }}
            .timeline-minute {{
                font-weight: 900;
                width: 46px;
                color: #0a1728;
            }}
            .timeline-icon {{
                margin-right: 10px;
                font-size: 13px;
            }}
            .timeline-text {{
                flex: 1;
                font-weight: 600;
            }}

            /* Top Performers ESG Impact Scores */
            .performers-grid {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 10px;
                margin: 8px 0;
            }}
            .performer-card {{
                background: white;
                border-radius: 12px;
                padding: 12px 14px;
                border-left: 5px solid #004687;
                box-shadow: 0 4px 10px rgba(10, 23, 40, 0.05);
            }}
            .performer-card.gold {{ border-left-color: #ebb837; }}
            .performer-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 4px;
            }}
            .performer-name {{
                font-family: 'Oswald', sans-serif;
                font-size: 13.5px;
                font-weight: 700;
                color: #0a1728;
                text-transform: uppercase;
            }}
            .performer-score {{
                background: #0a1728;
                color: #ebb837;
                font-family: 'Oswald', sans-serif;
                font-size: 14px;
                font-weight: 800;
                padding: 2px 7px;
                border-radius: 6px;
            }}
            .performer-badge {{
                font-size: 8.5px;
                font-weight: 800;
                color: #475569;
                text-transform: uppercase;
                margin-bottom: 3px;
            }}

            /* Alerte Disciplinaire Sortante */
            .discipline-box {{
                background: #0a1728;
                color: white;
                border-radius: 12px;
                padding: 12px 18px;
                border-left: 6px solid #e8590c;
                margin: 8px 0;
            }}
            .discipline-title {{
                font-family: 'Oswald', sans-serif;
                font-size: 13.5px;
                font-weight: 700;
                color: #ebb837;
                text-transform: uppercase;
                margin-bottom: 6px;
            }}
            .discipline-list {{
                margin: 0;
                padding-left: 16px;
                font-size: 9.5px;
                line-height: 1.4;
                color: #e2e8f0;
            }}
            .discipline-list li {{ margin-bottom: 3px; }}

            /* Footer */
            .footer {{
                background: #ebb837;
                border-radius: 12px;
                padding: 10px 18px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                color: #0a1728;
                font-weight: 800;
            }}
            .footer .slogan {{
                font-family: 'Oswald', sans-serif;
                font-size: 14px;
                letter-spacing: 1px;
                text-transform: uppercase;
            }}
            .footer .tag {{ font-size: 9px; font-weight: 800; }}
        </style>
    </head>
    <body>

        <!-- Header -->
        <div class="header">
            <div class="header-left">
                <img class="club-logo" src="data:image/png;base64,{logo_b64}" alt="Logo ES Genech">
                <div class="club-title">
                    <h1>ES <span>GENECH</span></h1>
                    <p>Cellule Performance • Rapport & Débrief du Lundi</p>
                </div>
            </div>
            <div class="header-badge">
                <div class="comp">{comp}</div>
                <div class="tour">{tour}</div>
            </div>
        </div>

        <!-- Hero Scoreboard -->
        <div class="score-hero">
            <div class="score-tag">{issue} • {tour}</div>
            <div class="score-display">
                <div class="team-name {'highlight' if is_dom else ''}">{dom}</div>
                <div class="score-numbers">{s_dom} - {s_ext}</div>
                <div class="team-name {'highlight' if not is_dom else ''}">{ext}</div>
            </div>
            <div class="score-sub">{date_str} • {issue_sub}</div>
        </div>

        <!-- 4 Grands KPIs Match -->
        <div class="match-kpis">
            <div class="kpi-box green">
                <div class="kpi-title">Efficacité Offensive</div>
                <div class="kpi-value">{s_genech} But{'s' if s_genech > 1 else ''}</div>
                <div class="kpi-desc">Total buts inscrits par Genech</div>
            </div>
            <div class="kpi-box {'green' if s_opp == 0 else 'orange'}">
                <div class="kpi-title">Solidité Défensive</div>
                <div class="kpi-value">{'CLEAN SHEET' if s_opp == 0 else f'{s_opp} But Concession'}</div>
                <div class="kpi-desc">{'Verrouillage total' if s_opp == 0 else 'Buts encaissés'}</div>
            </div>
            <div class="kpi-box gold">
                <div class="kpi-title">Coaching & Banc</div>
                <div class="kpi-value">3 Changements</div>
                <div class="kpi-desc">Ajustements tactiques 2nde MT</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-title">Discipline Match</div>
                <div class="kpi-value">Art. 226 FFF</div>
                <div class="kpi-desc">Veille sursis & sanctions</div>
            </div>
        </div>

        <!-- Feuille de Match Officielle : XI de Départ & Remplaçants -->
        <div class="lineup-card">
            <div class="card-title">
                <span>📋 Feuille de Match Officielle ES Genech</span>
                <span style="font-size: 8.5px; color:#64748b;">Feuille de match officielle FFF</span>
            </div>
            <div class="lineup-grid">
                <div class="lineup-group">
                    <h4>11 Titulaires au Coup d'Envoi</h4>
                    <div class="player-pill-grid">
    """

    titulaires = m_lineups[m_lineups['role'] == 'TITULAIRE'].sort_values(by='numero')
    remplacants = m_lineups[m_lineups['role'] == 'REMPLACANT'].sort_values(by='numero')

    for _, p in titulaires.iterrows():
        html += f"""<div class="player-pill"><span class="p-num">{p['numero']}</span>{p['player_norm']}</div>"""

    html += f"""
                    </div>
                </div>
                <div class="lineup-group">
                    <h4>Banc & Remplaçants</h4>
                    <div class="player-pill-grid">
    """

    for _, p in remplacants.iterrows():
        html += f"""<div class="player-pill" style="border-left: 3px solid #ebb837;"><span class="p-num" style="background:#ebb837; color:#0a1728;">{p['numero']}</span>{p['player_norm']}</div>"""

    html += f"""
                    </div>
                </div>
            </div>
        </div>

        <!-- Timeline Chronologique des 90 Minutes -->
        <div class="timeline-card">
            <div class="card-title">
                <span>⏱️ Déroulé Chronologique du Match (Timeline 90')</span>
                <span style="font-size: 8.5px; color:#64748b;">Faits de jeu officiels FFF</span>
            </div>
            <div class="timeline-list">
    """

    if not m_events.empty:
        for _, ev in m_events.iterrows():
            typ = ev['type_event']
            min_txt = f"{int(ev['minute'])}'" if pd.notnull(ev['minute']) else "-"
            eq = ev['equipe']
            is_g = "GENECH" in str(eq).upper()
            c_class = "genech" if is_g else "adverse"

            if typ == "BUT":
                icon = "⚽"
                desc = f"<strong>BUT pour {eq}</strong> inscrit par {ev['acteur_principal']}"
            elif typ == "AVERTISSEMENT":
                icon = "🟨"
                desc = f"Carton Jaune pour {ev['acteur_principal']} ({eq})"
            elif typ == "EXPULSION":
                icon = "🟥"
                desc = f"<strong>Carton Rouge (Exclusion)</strong> pour {ev['acteur_principal']} ({eq})"
            elif typ == "CHANGEMENT":
                icon = "🔄"
                desc = f"Changement {eq} : {ev['acteur_principal']} remplace {ev['acteur_secondaire']}"
            else:
                icon = "📌"
                desc = f"{ev['detail']} ({eq})"

            html += f"""
                <div class="timeline-item {c_class}">
                    <span class="timeline-minute">{min_txt}</span>
                    <span class="timeline-icon">{icon}</span>
                    <span class="timeline-text">{desc}</span>
                </div>
            """
    else:
        html += """<div class="timeline-item"><span class="timeline-text">Aucun événement majeur consigné sur la feuille de match FFF.</span></div>"""

    html += f"""
            </div>
        </div>

        <!-- Top Performers du Match (ESG Impact Scores) -->
        <div class="performers-grid">
    """

    # Top 4 performers
    top_4 = df_ratings.head(4)
    for i, (_, row) in enumerate(top_4.iterrows(), 1):
        is_gold = "gold" if i == 1 else ""
        html += f"""
            <div class="performer-card {is_gold}">
                <div class="performer-header">
                    <span class="performer-name">#{i} {row['joueur']}</span>
                    <span class="performer-score">{row['esg_impact_score']:.1f}</span>
                </div>
                <div class="performer-badge">{row['badge_tactique']}</div>
                <div style="font-size: 9px; color: #64748b; font-weight: 700;">
                    {int(row['minutes_estimees'])} min • {int(row['buts'])} buts • {int(row['clean_sheets_participees'])} CS
                </div>
            </div>
        """

    html += f"""
        </div>

        <!-- Alerte Disciplinaire Sortante -->
        <div class="discipline-box">
            <div class="discipline-title">⚖️ État Disciplinaire & Gestion du Sursis (Post-Match)</div>
            <ul class="discipline-list">
    """

    if alerts_discipline:
        for a in alerts_discipline:
            html += f"<li>{a}</li>"
    else:
        html += "<li>Aucun joueur sous le coup d'une suspension immédiate. Discipline maîtrisée.</li>"

    html += f"""
            </ul>
        </div>

        <!-- Footer -->
        <div class="footer">
            <div class="slogan">TOUJOURS ENSEMBLE • ALLEZ L'ESG</div>
            <div class="tag">Cellule Performance • Auto-Update Hebdomadaire</div>
        </div>

    </body>
    </html>
    """

    with sync_playwright() as p:
        browser = launch_browser(p)
        page = browser.new_page(viewport={"width": 1080, "height": 1920})
        page.set_content(html, wait_until="networkidle")

        latest_png = os.path.join(OUTPUT_DIR, "debrief_match_latest.png")
        latest_pdf = os.path.join(OUTPUT_DIR, "debrief_match_latest.pdf")

        page.screenshot(path=latest_png, full_page=True)
        page.pdf(path=latest_pdf, print_background=True, width="1080px", height="1920px")
        browser.close()

    print("Rapport Post-Match (Débrief du Lundi) régénéré avec succès en PNG et PDF !")

if __name__ == "__main__":
    generate_postmatch_debrief()
