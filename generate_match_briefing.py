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

    # Encode logo
    logo_b64 = ""
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode("utf-8")

    # Calculs Quarts d'Heure
    df_buts = df_events[df_events['type_event'] == 'BUT'].copy()
    df_buts['is_genech'] = df_buts['equipe'].str.contains('GENECH', case=False, na=False)

    tranches = ["01-15'", "16-30'", "31-45+'", "46-60'", "61-75'", "76-90+'"]
    buts_pour = []
    buts_contre = []
    for t in tranches:
        buts_pour.append(len(df_buts[(df_buts['tranche_quart_heure'] == t) & (df_buts['is_genech'])]))
        buts_contre.append(len(df_buts[(df_buts['tranche_quart_heure'] == t) & (~df_buts['is_genech'])]))

    # Top Buteurs Genech
    buteurs_series = df_events[(df_events['type_event'] == 'BUT') & (df_events['equipe'].str.contains('GENECH', case=False, na=False))]['acteur_principal'].value_counts()
    top_buteurs = [{"nom": k, "buts": v} for k, v in buteurs_series.head(4).items()]

    cartons_count = len(df_events[(df_events['type_event'].isin(['AVERTISSEMENT', 'EXPULSION'])) & (df_events['equipe'].str.contains('GENECH', case=False, na=False))])

    # HTML Template Format Téléphone (Mobile-First 1080x1920) avec fond #ede8d8
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>ES Genech - Mobile Matchday</title>
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
                padding: 32px 36px 36px 36px;
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
                border-radius: 20px;
                padding: 22px 28px;
                color: white;
                box-shadow: 0 10px 25px rgba(10, 23, 40, 0.15);
                border: 2px solid #ebb837;
            }}
            .header-left {{
                display: flex;
                align-items: center;
                gap: 20px;
            }}
            .club-logo {{
                width: 82px;
                height: 82px;
                border-radius: 50%;
                border: 3px solid #ebb837;
                padding: 3px;
                background: #0a1728;
            }}
            .club-title h1 {{
                font-family: 'Oswald', sans-serif;
                font-size: 32px;
                font-weight: 700;
                margin: 0;
                letter-spacing: 1px;
                text-transform: uppercase;
                color: #ffffff;
            }}
            .club-title h1 span {{
                color: #ebb837;
            }}
            .club-title p {{
                margin: 4px 0 0 0;
                font-size: 13.5px;
                font-weight: 700;
                letter-spacing: 0.5px;
                color: #cbd5e1;
                text-transform: uppercase;
            }}
            .header-badge {{
                background: #ebb837;
                color: #0a1728;
                padding: 12px 18px;
                border-radius: 14px;
                text-align: center;
                font-weight: 800;
            }}
            .header-badge .comp {{
                font-family: 'Oswald', sans-serif;
                font-size: 14px;
                text-transform: uppercase;
            }}
            .header-badge .tour {{
                font-size: 17px;
                font-weight: 900;
                margin-top: 1px;
            }}

            /* Carte Prochain Match (Format Hero) */
            .match-hero {{
                background: #0a1728;
                border-radius: 20px;
                padding: 24px 30px;
                margin-top: 20px;
                color: white;
                text-align: center;
                box-shadow: 0 8px 20px rgba(10, 23, 40, 0.12);
                border-bottom: 6px solid #e8590c;
            }}
            .hero-tag {{
                display: inline-block;
                background: #e8590c;
                color: white;
                font-size: 12px;
                font-weight: 800;
                padding: 4px 14px;
                border-radius: 20px;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 12px;
            }}
            .hero-teams {{
                font-family: 'Oswald', sans-serif;
                font-size: 36px;
                font-weight: 700;
                letter-spacing: 1px;
                text-transform: uppercase;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 16px;
            }}
            .hero-teams .vs {{
                color: #ebb837;
                font-size: 24px;
            }}
            .hero-info {{
                font-size: 14px;
                font-weight: 700;
                color: #cbd5e1;
                margin-top: 8px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}

            /* Grille 4 KPIs adaptée mobile */
            .kpi-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 16px;
                margin-top: 20px;
            }}
            .kpi-card {{
                background: white;
                border-radius: 16px;
                padding: 16px 20px;
                border-left: 6px solid #0a1728;
                box-shadow: 0 4px 12px rgba(10, 23, 40, 0.06);
            }}
            .kpi-card.gold {{
                border-left-color: #ebb837;
            }}
            .kpi-card.orange {{
                border-left-color: #e8590c;
            }}
            .kpi-label {{
                font-size: 12px;
                font-weight: 800;
                text-transform: uppercase;
                color: #64748b;
                letter-spacing: 0.5px;
            }}
            .kpi-val {{
                font-family: 'Oswald', sans-serif;
                font-size: 34px;
                font-weight: 700;
                color: #0a1728;
                margin-top: 2px;
            }}
            .kpi-card.gold .kpi-val {{
                color: #d97706;
            }}
            .kpi-card.orange .kpi-val {{
                color: #e8590c;
            }}
            .kpi-sub {{
                font-size: 11.5px;
                font-weight: 600;
                color: #475569;
                margin-top: 2px;
            }}

            /* Carte Quarts d'Heure Mobile */
            .section-card {{
                background: white;
                border-radius: 20px;
                padding: 22px 26px;
                margin-top: 20px;
                box-shadow: 0 4px 15px rgba(10, 23, 40, 0.06);
            }}
            .section-title {{
                font-family: 'Oswald', sans-serif;
                font-size: 20px;
                font-weight: 700;
                text-transform: uppercase;
                color: #0a1728;
                border-bottom: 2px solid #ebb837;
                padding-bottom: 8px;
                margin-bottom: 14px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}

            /* Tableau Quarts d'heure */
            .tranche-table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 13.5px;
            }}
            .tranche-table th {{
                text-align: left;
                padding: 8px 10px;
                background: #f1ede1;
                color: #0a1728;
                font-size: 11.5px;
                font-weight: 800;
                text-transform: uppercase;
            }}
            .tranche-table td {{
                padding: 9px 10px;
                border-bottom: 1px solid #f1f5f9;
            }}
            .bar-pour {{
                background: #0a1728;
                height: 16px;
                border-radius: 4px;
                display: inline-block;
                border-left: 4px solid #ebb837;
            }}
            .bar-contre {{
                background: #e8590c;
                height: 16px;
                border-radius: 4px;
                display: inline-block;
            }}

            /* Causerie Coach Callout */
            .briefing-box {{
                background: #0a1728;
                color: white;
                border-radius: 16px;
                padding: 18px 22px;
                margin-top: 20px;
                border-left: 6px solid #ebb837;
            }}
            .briefing-title {{
                font-family: 'Oswald', sans-serif;
                font-size: 17px;
                font-weight: 700;
                color: #ebb837;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 10px;
            }}
            .briefing-box ul {{
                margin: 0;
                padding-left: 20px;
                font-size: 13px;
                line-height: 1.5;
                color: #e2e8f0;
            }}
            .briefing-box li {{
                margin-bottom: 6px;
            }}
            .briefing-box strong {{
                color: #ebb837;
            }}

            /* Coupe de France Grid */
            .cdf-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
                margin-top: 12px;
            }}
            .cdf-item {{
                background: #f8fafc;
                border-left: 4px solid #0a1728;
                border-radius: 10px;
                padding: 10px 14px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .cdf-item.hero {{
                background: #fef3c7;
                border-left-color: #e8590c;
                grid-column: span 2;
            }}
            .cdf-tour {{
                font-size: 11px;
                font-weight: 800;
                color: #64748b;
                text-transform: uppercase;
            }}
            .cdf-item.hero .cdf-tour {{
                color: #b45309;
            }}
            .cdf-match {{
                font-size: 13px;
                font-weight: 700;
                color: #0a1728;
            }}
            .cdf-score {{
                background: #0a1728;
                color: #ebb837;
                font-family: 'Oswald', sans-serif;
                font-size: 15px;
                font-weight: 700;
                padding: 3px 10px;
                border-radius: 6px;
            }}

            /* Footer Mobile ESG */
            .footer {{
                background: #ebb837;
                border-radius: 16px;
                padding: 16px 24px;
                margin-top: 24px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                color: #0a1728;
                font-weight: 800;
            }}
            .footer .slogan {{
                font-family: 'Oswald', sans-serif;
                font-size: 20px;
                letter-spacing: 1px;
                text-transform: uppercase;
            }}
            .footer .tag {{
                font-size: 12px;
                font-weight: 800;
            }}
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
            <div class="hero-info">Match à élimination directe pour le 7e Tour National</div>
        </div>

        <!-- 4 Cartes KPIs -->
        <div class="kpi-grid">
            <div class="kpi-card gold">
                <div class="kpi-label">Invincibilité Coupe</div>
                <div class="kpi-val">4 / 4</div>
                <div class="kpi-sub">Clean sheets consécutifs (0 but pris)</div>
            </div>
            <div class="kpi-card orange">
                <div class="kpi-label">Ratio 2nde Mi-Temps</div>
                <div class="kpi-val">75 %</div>
                <div class="kpi-sub">Des buts marqués après la pause</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Attaque ESG</div>
                <div class="kpi-val">8 Buts</div>
                <div class="kpi-sub">Moyenne 1.6 but / match</div>
            </div>
            <div class="kpi-card orange">
                <div class="kpi-label">Cartons Pris (R3)</div>
                <div class="kpi-val">{cartons_count} Jaunes</div>
                <div class="kpi-sub">Pic d'engagement (76-90+')</div>
            </div>
        </div>

        <!-- Section 1 : Quarts d'Heure -->
        <div class="section-card">
            <div class="section-title">
                <span>⏱️ Efficacité par Quart d'Heure</span>
                <span style="font-size: 11px; color:#64748b;">ESG (Bleu) vs Adv (Orange)</span>
            </div>
            <table class="tranche-table">
                <thead>
                    <tr>
                        <th>Minute</th>
                        <th>Pour (ESG)</th>
                        <th>Contre</th>
                        <th>Analyse Staff</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>01-15'</strong></td>
                        <td><span class="bar-pour" style="width: {max(buts_pour[0]*32, 6)}px;"></span> 0</td>
                        <td><span class="bar-contre" style="width: {max(buts_contre[0]*32, 6)}px;"></span> 0</td>
                        <td><span style="color:#64748b;">Observation & bloc serré</span></td>
                    </tr>
                    <tr>
                        <td><strong>16-30'</strong></td>
                        <td><span class="bar-pour" style="width: {max(buts_pour[1]*32, 6)}px;"></span> 0</td>
                        <td><span class="bar-contre" style="width: {max(buts_contre[1]*32, 6)}px;"></span> 1</td>
                        <td><span style="color:#64748b;">Temps faible ponctuel</span></td>
                    </tr>
                    <tr>
                        <td><strong>31-45+'</strong></td>
                        <td><span class="bar-pour" style="width: {max(buts_pour[2]*32, 6)}px;"></span> 2</td>
                        <td><span class="bar-contre" style="width: {max(buts_contre[2]*32, 6)}px;"></span> 2</td>
                        <td><span style="color:#e8590c; font-weight:700;">Transition rapide</span></td>
                    </tr>
                    <tr>
                        <td><strong>46-60'</strong></td>
                        <td><span class="bar-pour" style="width: {max(buts_pour[3]*32, 6)}px;"></span> 1</td>
                        <td><span class="bar-contre" style="width: {max(buts_contre[3]*32, 6)}px;"></span> 0</td>
                        <td><span style="color:#0a1728; font-weight:700;">Reprise bien maîtrisée</span></td>
                    </tr>
                    <tr>
                        <td><strong>61-75'</strong></td>
                        <td><span class="bar-pour" style="width: {max(buts_pour[4]*32, 6)}px;"></span> 2</td>
                        <td><span class="bar-contre" style="width: {max(buts_contre[4]*32, 6)}px;"></span> 0</td>
                        <td><span style="color:#0a1728; font-weight:700;">Impact des remplaçants</span></td>
                    </tr>
                    <tr style="background: #fef3c7;">
                        <td><strong>76-90+'</strong></td>
                        <td><span class="bar-pour" style="width: {max(buts_pour[5]*32, 6)}px;"></span> <strong>3</strong></td>
                        <td><span class="bar-contre" style="width: {max(buts_contre[5]*32, 6)}px;"></span> 1</td>
                        <td><strong style="color: #b45309;">🔥 ZONE DE FINITION ESG</strong></td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Section 2 : Parcours Coupe de France -->
        <div class="section-card">
            <div class="section-title">
                <span>🏆 Parcours Coupe de France</span>
                <span style="font-size: 12px; color: #b45309; font-weight:800;">4 MATCHS • 0 BUT PRIS</span>
            </div>
            <div class="cdf-grid">
                <div class="cdf-item">
                    <div>
                        <div class="cdf-tour">Tour 2</div>
                        <div class="cdf-match">Lys Lez Lannoy</div>
                    </div>
                    <div class="cdf-score">0-0 (tab)</div>
                </div>
                <div class="cdf-item">
                    <div>
                        <div class="cdf-tour">Tour 3</div>
                        <div class="cdf-match">Sainghin Weppes</div>
                    </div>
                    <div class="cdf-score">0-1</div>
                </div>
                <div class="cdf-item">
                    <div>
                        <div class="cdf-tour">Tour 4</div>
                        <div class="cdf-match">Dunkerque Malo</div>
                    </div>
                    <div class="cdf-score">2-0</div>
                </div>
                <div class="cdf-item">
                    <div>
                        <div class="cdf-tour">Top Buteur Coupe</div>
                        <div class="cdf-match">J. Nisse / G. Calon</div>
                    </div>
                    <div class="cdf-score">1 BUT</div>
                </div>
                <div class="cdf-item hero">
                    <div>
                        <div class="cdf-tour">Tour 5 • L'Exploit National 1</div>
                        <div class="cdf-match">ES GENECH vs US CHANTILLY (N1)</div>
                    </div>
                    <div class="cdf-score" style="background:#e8590c; color:white;">1 - 0 (77')</div>
                </div>
            </div>
        </div>

        <!-- Section 3 : Causerie Coach -->
        <div class="briefing-box">
            <div class="briefing-title">📋 3 Clés pour la Causerie du Coach</div>
            <ul>
                <li><strong>Discipline du Bloc Bas :</strong> Répliquer la performance héroïque du 5e tour face à Chantilly : lignes serrées, coulissement latéral sans jamais se jeter.</li>
                <li><strong>Patience & Usure :</strong> Ne pas douter si le score est nul à la pause : 75% de nos buts sont inscrits en 2e mi-temps grâce à notre fraîcheur physique.</li>
                <li><strong>Garder son Sang-Froid :</strong> 26 cartons pris dans le money-time en championnat. Aucune contestation auprès de l'arbitre, la qualification se joue à 11 contre 11.</li>
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
        # Mobile viewport 1080 x 1920 (ratio 9:16)
        page = browser.new_page(viewport={"width": 1080, "height": 1920})
        page.set_content(html_content, wait_until="networkidle")

        # Capture PNG plein format téléphone haute résolution
        page.screenshot(path=png_out, full_page=True)

        # Export PDF format mobile
        page.pdf(
            path=pdf_out, 
            width="1080px", 
            height="1920px", 
            print_background=True, 
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"}
        )

        browser.close()

    conn.close()
    print(f" Format Téléphone généré :")
    print(f" -> PDF Mobile : {pdf_out}")
    print(f" -> Image PNG WhatsApp : {png_out}")

if __name__ == "__main__":
    generate_mobile_briefing()
