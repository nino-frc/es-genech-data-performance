import sqlite3
import os
import base64
import pandas as pd
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "genech_performance.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "briefings_coach")
LOGO_PATH = os.path.join(BASE_DIR, "logo_genech_transparent.png")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def launch_browser(p):
    args = ['--disable-blink-features=AutomationControlled', '--no-sandbox']
    try:
        return p.chromium.launch(channel="chrome", headless=True, args=args)
    except Exception:
        return p.chromium.launch(headless=True, args=args)

def generate_mobile_briefing():
    conn = sqlite3.connect(DB_PATH)

    df_matchs = pd.read_sql_query("SELECT * FROM matchs", conn)
    df_events = pd.read_sql_query("SELECT * FROM match_events", conn)
    df_scouting = pd.read_sql_query("SELECT * FROM scouting_adversaire", conn) if 'scouting_adversaire' in [t[0] for t in conn.cursor().execute("SELECT name FROM sqlite_master WHERE type='table'")] else pd.DataFrame()

    # Encode logo
    logo_b64 = ""
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode("utf-8")

    # Calculs Quarts d'Heure Genech
    df_buts = df_events[df_events['type_event'] == 'BUT'].copy()
    df_buts['is_genech'] = df_buts['equipe'].str.contains('GENECH', case=False, na=False)

    tranches = ["01-15'", "16-30'", "31-45+'", "46-60'", "61-75'", "76-90+'"]
    buts_pour = []
    buts_contre = []
    for t in tranches:
        buts_pour.append(len(df_buts[(df_buts['tranche_quart_heure'] == t) & (df_buts['is_genech'])]))
        buts_contre.append(len(df_buts[(df_buts['tranche_quart_heure'] == t) & (~df_buts['is_genech'])]))

    cartons_count = len(df_events[(df_events['type_event'].isin(['AVERTISSEMENT', 'EXPULSION'])) & (df_events['equipe'].str.contains('GENECH', case=False, na=False))])

    # HTML Template Mobile avec Encart Scouting Opposant
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
                padding: 28px 32px 32px 32px;
                background-color: #ede8d8;
                color: #0a1728;
                width: 1080px;
                min-height: 1920px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }}

            /* Header Mobile avec Logo */
            .header {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                background: #0a1728;
                border-radius: 18px;
                padding: 18px 24px;
                color: white;
                box-shadow: 0 8px 20px rgba(10, 23, 40, 0.15);
                border: 2px solid #ebb837;
            }}
            .header-left {{
                display: flex;
                align-items: center;
                gap: 16px;
            }}
            .club-logo {{
                width: 74px;
                height: 74px;
                border-radius: 50%;
                border: 3px solid #ebb837;
                padding: 2px;
                background: #0a1728;
            }}
            .club-title h1 {{
                font-family: 'Oswald', sans-serif;
                font-size: 28px;
                font-weight: 700;
                margin: 0;
                letter-spacing: 1px;
                text-transform: uppercase;
                color: #ffffff;
            }}
            .club-title h1 span {{ color: #ebb837; }}
            .club-title p {{
                margin: 3px 0 0 0;
                font-size: 12px;
                font-weight: 700;
                color: #cbd5e1;
                text-transform: uppercase;
            }}
            .header-badge {{
                background: #ebb837;
                color: #0a1728;
                padding: 10px 16px;
                border-radius: 12px;
                text-align: center;
                font-weight: 800;
            }}
            .header-badge .comp {{
                font-family: 'Oswald', sans-serif;
                font-size: 13px;
                text-transform: uppercase;
            }}
            .header-badge .tour {{
                font-size: 15px;
                font-weight: 900;
            }}

            /* Hero Matchday */
            .match-hero {{
                background: #0a1728;
                border-radius: 18px;
                padding: 18px 24px;
                margin-top: 16px;
                color: white;
                text-align: center;
                border-bottom: 5px solid #e8590c;
            }}
            .hero-tag {{
                display: inline-block;
                background: #e8590c;
                color: white;
                font-size: 11px;
                font-weight: 800;
                padding: 3px 12px;
                border-radius: 20px;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 8px;
            }}
            .hero-teams {{
                font-family: 'Oswald', sans-serif;
                font-size: 32px;
                font-weight: 700;
                text-transform: uppercase;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 14px;
            }}
            .hero-teams .vs {{ color: #ebb837; font-size: 20px; }}

            /* 4 KPIs */
            .kpi-grid {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 10px;
                margin-top: 14px;
            }}
            .kpi-card {{
                background: white;
                border-radius: 12px;
                padding: 12px 14px;
                border-left: 5px solid #0a1728;
                box-shadow: 0 4px 10px rgba(10, 23, 40, 0.05);
            }}
            .kpi-card.gold {{ border-left-color: #ebb837; }}
            .kpi-card.orange {{ border-left-color: #e8590c; }}
            .kpi-label {{
                font-size: 9px;
                font-weight: 800;
                text-transform: uppercase;
                color: #64748b;
            }}
            .kpi-val {{
                font-family: 'Oswald', sans-serif;
                font-size: 24px;
                font-weight: 700;
                color: #0a1728;
                margin-top: 2px;
            }}
            .kpi-card.gold .kpi-val {{ color: #d97706; }}
            .kpi-card.orange .kpi-val {{ color: #e8590c; }}
            .kpi-sub {{
                font-size: 8.5px;
                font-weight: 600;
                color: #64748b;
            }}

            /* Scouting Opposant Card (Brique Pro) */
            .scouting-card {{
                background: #0a1728;
                color: white;
                border-radius: 18px;
                padding: 18px 24px;
                margin-top: 16px;
                border: 2px solid #e8590c;
                box-shadow: 0 6px 18px rgba(232, 89, 12, 0.2);
            }}
            .scouting-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 2px solid #e8590c;
                padding-bottom: 8px;
                margin-bottom: 12px;
            }}
            .scouting-title {{
                font-family: 'Oswald', sans-serif;
                font-size: 19px;
                font-weight: 700;
                color: #ffffff;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .scouting-badge {{
                background: #e8590c;
                color: white;
                font-size: 10px;
                font-weight: 800;
                padding: 3px 10px;
                border-radius: 6px;
                text-transform: uppercase;
            }}
            .scouting-grid {{
                display: grid;
                grid-template-columns: 1.1fr 0.9fr;
                gap: 16px;
            }}
            .scout-box {{
                background: rgba(255, 255, 255, 0.06);
                border-radius: 10px;
                padding: 12px 14px;
            }}
            .scout-box-title {{
                font-size: 10px;
                font-weight: 800;
                text-transform: uppercase;
                color: #ebb837;
                margin-bottom: 6px;
            }}
            .danger-player {{
                display: flex;
                align-items: center;
                gap: 10px;
                background: rgba(232, 89, 12, 0.2);
                border-left: 3px solid #e8590c;
                padding: 8px 10px;
                border-radius: 6px;
                margin-top: 6px;
            }}
            .danger-name {{
                font-family: 'Oswald', sans-serif;
                font-size: 15px;
                font-weight: 700;
                color: #f97316;
            }}
            .danger-desc {{
                font-size: 9.5px;
                color: #cbd5e1;
            }}

            /* Tableau Quarts d'Heure */
            .section-card {{
                background: white;
                border-radius: 18px;
                padding: 18px 22px;
                margin-top: 14px;
                box-shadow: 0 4px 15px rgba(10, 23, 40, 0.05);
            }}
            .section-title {{
                font-family: 'Oswald', sans-serif;
                font-size: 17px;
                font-weight: 700;
                text-transform: uppercase;
                color: #0a1728;
                border-bottom: 2px solid #ebb837;
                padding-bottom: 6px;
                margin-bottom: 10px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .tranche-table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 11px;
            }}
            .tranche-table th {{
                text-align: left;
                padding: 6px 8px;
                background: #f1ede1;
                color: #0a1728;
                font-size: 9.5px;
                font-weight: 800;
                text-transform: uppercase;
            }}
            .tranche-table td {{
                padding: 7px 8px;
                border-bottom: 1px solid #f1f5f9;
            }}
            .bar-pour {{
                background: #0a1728;
                height: 12px;
                border-radius: 3px;
                display: inline-block;
                border-left: 3px solid #ebb837;
            }}
            .bar-contre {{
                background: #e8590c;
                height: 12px;
                border-radius: 3px;
                display: inline-block;
            }}

            /* Causerie Coach Callout */
            .briefing-box {{
                background: #0a1728;
                color: white;
                border-radius: 14px;
                padding: 14px 18px;
                margin-top: 14px;
                border-left: 5px solid #ebb837;
            }}
            .briefing-title {{
                font-family: 'Oswald', sans-serif;
                font-size: 14px;
                font-weight: 700;
                color: #ebb837;
                text-transform: uppercase;
                margin-bottom: 6px;
            }}
            .briefing-box ul {{
                margin: 0;
                padding-left: 18px;
                font-size: 11px;
                line-height: 1.45;
                color: #e2e8f0;
            }}
            .briefing-box li {{ margin-bottom: 4px; }}
            .briefing-box strong {{ color: #ebb837; }}

            /* Footer Mobile ESG */
            .footer {{
                background: #ebb837;
                border-radius: 14px;
                padding: 12px 20px;
                margin-top: 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                color: #0a1728;
                font-weight: 800;
            }}
            .footer .slogan {{
                font-family: 'Oswald', sans-serif;
                font-size: 16px;
                letter-spacing: 1px;
                text-transform: uppercase;
            }}
            .footer .tag {{ font-size: 10px; font-weight: 800; }}
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
                <div class="comp">Coupe de France</div>
                <div class="tour">6e TOUR</div>
            </div>
        </div>

        <!-- Hero Matchday -->
        <div class="match-hero">
            <div class="hero-tag">Finale Régionale • Dimanche 25 Octobre • 15H00</div>
            <div class="hero-teams">
                ST MARTIN TATINGHEM <span class="vs">VS</span> ES GENECH
            </div>
        </div>

        <!-- 4 Cartes KPIs -->
        <div class="kpi-grid">
            <div class="kpi-card gold">
                <div class="kpi-label">Invincibilité ESG</div>
                <div class="kpi-val">4 / 4</div>
                <div class="kpi-sub">Clean sheets en Coupe</div>
            </div>
            <div class="kpi-card orange">
                <div class="kpi-label">Ratio 2e Mi-Temps</div>
                <div class="kpi-val">75 %</div>
                <div class="kpi-sub">Buts marqués après pause</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Attaque ESG</div>
                <div class="kpi-val">8 Buts</div>
                <div class="kpi-sub">Moyenne 1.6 / match</div>
            </div>
            <div class="kpi-card orange">
                <div class="kpi-label">Cartons Pris (R3)</div>
                <div class="kpi-val">{cartons_count} Jaunes</div>
                <div class="kpi-sub">Alerte (76-90+')</div>
            </div>
        </div>

        <!-- NOUVEAU BLOC : SCOUTING ADVERSAIRE OFFICIEL -->
        <div class="scouting-card">
            <div class="scouting-header">
                <div class="scouting-title">🎯 Espionnage Tactique : St-Martin Tatinghem</div>
                <div class="scouting-badge">Régional 3 (District Côte d'Opale)</div>
            </div>
            <div class="scouting-grid">
                <div class="scout-box">
                    <div class="scout-box-title">🔥 Danger n°1 Identifié</div>
                    <div class="danger-player">
                        <div>
                            <div class="danger-name">MOUAAD MADRI</div>
                            <div class="danger-desc">Attaquant vedette (Ex-Pro L2/National). Auteur de 3 buts lors des 2 derniers matchs (doublé au Tour 5, but en J4). À marquer de très près dès la relance.</div>
                        </div>
                    </div>
                </div>
                <div class="scout-box">
                    <div class="scout-box-title">⚠️ Vulnérabilités Détectées</div>
                    <ul style="margin:0; padding-left:14px; font-size:10px; color:#cbd5e1; line-height:1.45;">
                        <li><strong>Défense friable :</strong> 2 buts encaissés au Tour 5 face à Neufchâtel dans le dernier quart d'heure (74' et 90').</li>
                        <li><strong>Nervosité :</strong> 4 cartons jaunes reçus au 5e tour sous pression adverse.</li>
                    </ul>
                </div>
            </div>
        </div>

        <!-- Quarts d'Heure Genech -->
        <div class="section-card">
            <div class="section-title">
                <span>⏱️ Efficacité par Quart d'Heure (ESG)</span>
                <span style="font-size: 10px; color:#64748b;">ESG (Bleu) vs Adv (Orange)</span>
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
                    <tr>
                        <td><strong>01-15'</strong></td>
                        <td><span class="bar-pour" style="width: {max(buts_pour[0]*25, 4)}px;"></span> 0</td>
                        <td><span class="bar-contre" style="width: {max(buts_contre[0]*25, 4)}px;"></span> 0</td>
                        <td><span style="color:#64748b;">Observation & bloc serré</span></td>
                    </tr>
                    <tr>
                        <td><strong>16-30'</strong></td>
                        <td><span class="bar-pour" style="width: {max(buts_pour[1]*25, 4)}px;"></span> 0</td>
                        <td><span class="bar-contre" style="width: {max(buts_contre[1]*25, 4)}px;"></span> 1</td>
                        <td><span style="color:#64748b;">Temps faible ponctuel</span></td>
                    </tr>
                    <tr>
                        <td><strong>31-45+'</strong></td>
                        <td><span class="bar-pour" style="width: {max(buts_pour[2]*25, 4)}px;"></span> 2</td>
                        <td><span class="bar-contre" style="width: {max(buts_contre[2]*25, 4)}px;"></span> 2</td>
                        <td><span style="color:#e8590c; font-weight:700;">Transition rapide</span></td>
                    </tr>
                    <tr>
                        <td><strong>46-60'</strong></td>
                        <td><span class="bar-pour" style="width: {max(buts_pour[3]*25, 4)}px;"></span> 1</td>
                        <td><span class="bar-contre" style="width: {max(buts_contre[3]*25, 4)}px;"></span> 0</td>
                        <td><span style="color:#0a1728; font-weight:700;">Reprise bien cadenassée</span></td>
                    </tr>
                    <tr>
                        <td><strong>61-75'</strong></td>
                        <td><span class="bar-pour" style="width: {max(buts_pour[4]*25, 4)}px;"></span> 2</td>
                        <td><span class="bar-contre" style="width: {max(buts_contre[4]*25, 4)}px;"></span> 0</td>
                        <td><span style="color:#0a1728; font-weight:700;">Coaching gagnant (Subs)</span></td>
                    </tr>
                    <tr style="background: #fef3c7;">
                        <td><strong>76-90+'</strong></td>
                        <td><span class="bar-pour" style="width: {max(buts_pour[5]*25, 4)}px;"></span> <strong>3</strong></td>
                        <td><span class="bar-contre" style="width: {max(buts_contre[5]*25, 4)}px;"></span> 1</td>
                        <td><strong style="color: #b45309;">🔥 ZONE DE FINITION ESG</strong></td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Causerie Coach -->
        <div class="briefing-box">
            <div class="briefing-title">📋 Plan de Jeu Recommandé pour la Causerie</div>
            <ul>
                <li><strong>Neutraliser Madri :</strong> Couper impérativement les lignes de passe vers Mouaad Madri, véritable métronome offensif adverse.</li>
                <li><strong>Tirer profit du dernier quart d'heure :</strong> Tatinghem a concédé 2 buts à la 74' et 90' au Tour 5. C'est exactement là que Genech est le plus dangereux (3 buts inscrits).</li>
                <li><strong>Discipline totale :</strong> L'arbitre sanctionnera la moindre faute de frustration. Rester calme à 11 contre 11.</li>
            </ul>
        </div>

        <!-- Footer -->
        <div class="footer">
            <div class="slogan">TOUJOURS ENSEMBLE • ALLEZ L'ESG</div>
            <div class="tag">Cellule Data & Performance • Saison 2026/2027</div>
        </div>

    </body>
    </html>
    """

    pdf_out = os.path.join(OUTPUT_DIR, "briefing_match_tatinghem.pdf")
    png_out = os.path.join(OUTPUT_DIR, "briefing_match_tatinghem.png")

    with sync_playwright() as p:
        browser = launch_browser(p)
        page = browser.new_page(viewport={"width": 1080, "height": 1920})
        page.set_content(html_content, wait_until="networkidle")

        page.screenshot(path=png_out, full_page=True)
        page.pdf(
            path=pdf_out, 
            width="1080px", 
            height="1920px", 
            print_background=True, 
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"}
        )

        browser.close()

    conn.close()
    print(" Fiche Mobile avec Bloc Scouting Adversaire générée avec succès !")

if __name__ == "__main__":
    generate_mobile_briefing()
