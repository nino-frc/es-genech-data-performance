"""
Générateur de Rapport Post-Match Automatique (Débrief du Lundi Matin)
Fiche mobile haute résolution (1080x1920) : Timeline des 90', Ratings joueurs & Alerte Discipline
Projet ES Genech Data Performance - Portfolio SportTech
"""

import os
import sys
import base64
import sqlite3
import pandas as pd
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

from discipline_monitor import analyze_discipline, normalize_player_name
from player_rating import calculate_player_ratings

def launch_browser(p):
    args = ['--disable-blink-features=AutomationControlled', '--no-sandbox']
    try:
        return p.chromium.launch(channel="chrome", headless=True, args=args)
    except Exception:
        return p.chromium.launch(headless=True, args=args)

def generate_postmatch_debrief():
    conn = sqlite3.connect(DB_PATH)

    df_matchs = pd.read_sql_query("SELECT * FROM matchs WHERE statut = 'TERMINE'", conn)
    df_events = pd.read_sql_query("SELECT * FROM match_events", conn)
    df_lineups = pd.read_sql_query("SELECT * FROM match_lineups", conn)
    df_classement = pd.read_sql_query("SELECT * FROM classement_poule ORDER BY rang ASC", conn)
    conn.close()

    # Trouver le dernier match disputé par Genech
    is_genech = (df_matchs['equipe_domicile'].str.contains('GENECH', case=False, na=False)) | \
                (df_matchs['equipe_exterieur'].str.contains('GENECH', case=False, na=False))
    genech_matches = df_matchs[is_genech].sort_values(by='date_heure', ascending=False)

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

    # HTML Content
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

            /* Hero Scoreboard */
            .score-hero {{
                background: #0a1728;
                border-radius: 14px;
                padding: 12px 20px;
                color: white;
                text-align: center;
                border-bottom: 5px solid {issue_color};
                box-shadow: 0 4px 12px rgba(10, 23, 40, 0.12);
            }}
            .score-tag {{
                display: inline-block;
                background: {issue_color};
                color: white;
                font-size: 10px;
                font-weight: 900;
                padding: 3px 12px;
                border-radius: 20px;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 4px;
            }}
            .score-display {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 24px;
                margin: 4px 0;
            }}
            .team-name {{
                font-family: 'Oswald', sans-serif;
                font-size: 22px;
                font-weight: 700;
                text-transform: uppercase;
                width: 38%;
            }}
            .team-name.highlight {{ color: #ebb837; }}
            .score-numbers {{
                font-family: 'Oswald', sans-serif;
                font-size: 38px;
                font-weight: 900;
                color: white;
                background: rgba(255, 255, 255, 0.1);
                padding: 2px 18px;
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            .score-sub {{
                font-size: 9px;
                color: #cbd5e1;
                font-weight: 600;
            }}

            /* Timeline Chronologique 90 min */
            .timeline-card {{
                background: white;
                border-radius: 12px;
                padding: 10px 14px;
                box-shadow: 0 4px 10px rgba(10, 23, 40, 0.05);
                border: 1px solid #cbd5e1;
            }}
            .card-title {{
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
            .timeline-list {{
                display: flex;
                flex-direction: column;
                gap: 4px;
            }}
            .timeline-item {{
                display: flex;
                align-items: center;
                font-size: 9px;
                padding: 4px 8px;
                border-radius: 6px;
                background: #f8fafc;
            }}
            .timeline-item.genech {{
                background: #eff6ff;
                border-left: 3px solid #004687;
            }}
            .timeline-item.adverse {{
                background: #fff7ed;
                border-left: 3px solid #e8590c;
            }}
            .timeline-minute {{
                font-weight: 900;
                width: 42px;
                color: #0a1728;
            }}
            .timeline-icon {{
                margin-right: 8px;
                font-size: 11px;
            }}
            .timeline-text {{
                flex: 1;
                font-weight: 600;
            }}

            /* Top Performers ESG Impact Scores */
            .performers-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
            }}
            .performer-card {{
                background: white;
                border-radius: 12px;
                padding: 9px 12px;
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
                font-size: 13px;
                font-weight: 700;
                color: #0a1728;
                text-transform: uppercase;
            }}
            .performer-score {{
                background: #0a1728;
                color: #ebb837;
                font-family: 'Oswald', sans-serif;
                font-size: 13px;
                font-weight: 800;
                padding: 2px 7px;
                border-radius: 6px;
            }}
            .performer-badge {{
                font-size: 8px;
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
                padding: 9px 14px;
                border-left: 5px solid #e8590c;
            }}
            .discipline-title {{
                font-family: 'Oswald', sans-serif;
                font-size: 12px;
                font-weight: 700;
                color: #ebb837;
                text-transform: uppercase;
                margin-bottom: 4px;
            }}
            .discipline-list {{
                margin: 0;
                padding-left: 14px;
                font-size: 8.5px;
                line-height: 1.35;
                color: #e2e8f0;
            }}
            .discipline-list li {{ margin-bottom: 2px; }}

            /* Footer */
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
            t = ev['type_event']
            is_g = "GENECH" in ev['equipe'].upper()
            classe = "genech" if is_g else "adverse"
            minute = f"{ev['minute']}’"

            if t == "BUT":
                icon = "⚽"
                text = f"<strong>BUT pour {ev['equipe']}</strong> marqué par <strong>{ev['acteur_principal']}</strong>"
            elif t == "AVERTISSEMENT":
                icon = "🟨"
                text = f"Carton jaune : {ev['acteur_principal']} ({ev['equipe']})"
            elif t == "EXPULSION":
                icon = "🟥"
                text = f"<strong>EXPULSION : {ev['acteur_principal']} ({ev['equipe']})</strong>"
            elif t == "CHANGEMENT":
                icon = "🔄"
                text = f"Remplacement : {ev['acteur_principal']} entre à la place de {ev['acteur_secondaire']}"
            else:
                icon = "📌"
                text = f"{ev['detail']}"

            html += f"""
                <div class="timeline-item {classe}">
                    <span class="timeline-minute">{minute}</span>
                    <span class="timeline-icon">{icon}</span>
                    <span class="timeline-text">{text}</span>
                </div>
            """
    else:
        html += """<div style="font-size:9px; padding:6px; color:#64748b;">Aucun événement particulier noté sur la feuille officielle.</div>"""

    # Top 2 joueurs ESG Impact Scores
    top_players = df_ratings.head(4)
    p1 = top_players.iloc[0] if len(top_players) > 0 else None
    p2 = top_players.iloc[1] if len(top_players) > 1 else None

    html += f"""
            </div>
        </div>

        <!-- Top Performers ESG Impact Scores -->
        <div class="performers-grid">
    """

    if p1 is not None:
        html += f"""
            <div class="performer-card gold">
                <div class="performer-header">
                    <span class="performer-name">{p1['joueur']}</span>
                    <span class="performer-score">{p1['esg_impact_score']} / 100</span>
                </div>
                <div class="performer-badge">{p1['badge_tactique']}</div>
                <div style="font-size:8.5px; color:#475569;">
                    {p1['minutes_estimees']} min jouées • {p1['buts']} but(s) • {p1['clean_sheets_participees']} clean sheet(s)
                </div>
            </div>
        """
    if p2 is not None:
        html += f"""
            <div class="performer-card">
                <div class="performer-header">
                    <span class="performer-name">{p2['joueur']}</span>
                    <span class="performer-score">{p2['esg_impact_score']} / 100</span>
                </div>
                <div class="performer-badge">{p2['badge_tactique']}</div>
                <div style="font-size:8.5px; color:#475569;">
                    {p2['minutes_estimees']} min jouées • {p2['buts']} but(s) • {p2['clean_sheets_participees']} clean sheet(s)
                </div>
            </div>
        """

    html += f"""
        </div>

        <!-- Alerte Disciplinaire Sortante (FFF Art. 226) -->
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

    # Rendu PDF et PNG
    with sync_playwright() as p:
        browser = launch_browser(p)
        page = browser.new_page(viewport={"width": 1080, "height": 1920})
        page.set_content(html, wait_until="networkidle")

        latest_png = os.path.join(OUTPUT_DIR, "debrief_match_latest.png")
        latest_pdf = os.path.join(OUTPUT_DIR, "debrief_match_latest.pdf")

        page.screenshot(path=latest_png, full_page=True)
        page.pdf(path=latest_pdf, print_background=True, width="1080px", height="1920px")
        browser.close()

    print("Rapport Post-Match (Débrief du Lundi) généré avec succès en PNG et PDF !")

if __name__ == "__main__":
    generate_postmatch_debrief()
