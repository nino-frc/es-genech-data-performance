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

    # HTML Template Mobile avec Encart Alerte Suspension & FMI
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
                padding: 26px 30px 30px 30px;
                background-color: #ede8d8;
                color: #0a1728;
                width: 1080px;
                min-height: 1920px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }}

            /* Header Mobile */
            .header {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                background: #0a1728;
                border-radius: 18px;
                padding: 16px 22px;
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
                width: 70px;
                height: 70px;
                border-radius: 50%;
                border: 3px solid #ebb837;
                padding: 2px;
                background: #0a1728;
            }}
            .club-title h1 {{
                font-family: 'Oswald', sans-serif;
                font-size: 27px;
                font-weight: 700;
                margin: 0;
                letter-spacing: 1px;
                text-transform: uppercase;
                color: #ffffff;
            }}
            .club-title h1 span {{ color: #ebb837; }}
            .club-title p {{
                margin: 2px 0 0 0;
                font-size: 11.5px;
                font-weight: 700;
                color: #cbd5e1;
                text-transform: uppercase;
            }}
            .header-badge {{
                background: #ebb837;
                color: #0a1728;
                padding: 9px 15px;
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
                border-radius: 16px;
                padding: 16px 22px;
                margin-top: 14px;
                color: white;
                text-align: center;
                border-bottom: 5px solid #e8590c;
            }}
            .hero-tag {{
                display: inline-block;
                background: #e8590c;
                color: white;
                font-size: 10.5px;
                font-weight: 800;
                padding: 3px 12px;
                border-radius: 20px;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 6px;
            }}
            .hero-teams {{
                font-family: 'Oswald', sans-serif;
                font-size: 30px;
                font-weight: 700;
                text-transform: uppercase;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 14px;
            }}
            .hero-teams .vs {{ color: #ebb837; font-size: 18px; }}

            /* 4 KPIs */
            .kpi-grid {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 10px;
                margin-top: 12px;
            }}
            .kpi-card {{
                background: white;
                border-radius: 12px;
                padding: 10px 12px;
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
                margin-top: 1px;
            }}
            .kpi-card.gold .kpi-val {{ color: #d97706; }}
            .kpi-card.orange .kpi-val {{ color: #e8590c; }}
            .kpi-sub {{
                font-size: 8px;
                font-weight: 600;
                color: #64748b;
            }}

            /* Scouting Opposant Card */
            .scouting-card {{
                background: #0a1728;
                color: white;
                border-radius: 16px;
                padding: 16px 20px;
                margin-top: 14px;
                border: 2px solid #e8590c;
                box-shadow: 0 6px 18px rgba(232, 89, 12, 0.15);
            }}
            .scouting-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 2px solid #e8590c;
                padding-bottom: 6px;
                margin-bottom: 10px;
            }}
            .scouting-title {{
                font-family: 'Oswald', sans-serif;
                font-size: 18px;
                font-weight: 700;
                color: #ffffff;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .scouting-badge {{
                background: #e8590c;
                color: white;
                font-size: 9.5px;
                font-weight: 800;
                padding: 3px 8px;
                border-radius: 6px;
                text-transform: uppercase;
            }}

            /* ALERTE SUSPENSION SPÉCIALE */
            .alert-suspension {{
                background: #b91c1c;
                border-radius: 10px;
                padding: 10px 14px;
                margin-bottom: 10px;
                border-left: 6px solid #fef08a;
            }}
            .alert-suspension-title {{
                font-family: 'Oswald', sans-serif;
                font-size: 14px;
                font-weight: 700;
                color: #fef08a;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            .alert-suspension-desc {{
                font-size: 9.5px;
                line-height: 1.45;
                color: #fef2f2;
                margin-top: 4px;
            }}
            .alert-suspension-desc strong {{
                color: #ffffff;
                text-decoration: underline;
            }}

            .scouting-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 12px;
            }}
            .scout-box {{
                background: rgba(255, 255, 255, 0.06);
                border-radius: 10px;
                padding: 10px 12px;
            }}
            .scout-box-title {{
                font-size: 9.5px;
                font-weight: 800;
                text-transform: uppercase;
                color: #ebb837;
                margin-bottom: 4px;
            }}

            /* Tableau Quarts d'Heure */
            .section-card {{
                background: white;
                border-radius: 16px;
                padding: 16px 20px;
                margin-top: 12px;
                box-shadow: 0 4px 15px rgba(10, 23, 40, 0.05);
            }}
            .section-title {{
                font-family: 'Oswald', sans-serif;
                font-size: 16px;
                font-weight: 700;
                text-transform: uppercase;
                color: #0a1728;
                border-bottom: 2px solid #ebb837;
                padding-bottom: 5px;
                margin-bottom: 8px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .tranche-table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 10.5px;
            }}
            .tranche-table th {{
                text-align: left;
                padding: 5px 6px;
                background: #f1ede1;
                color: #0a1728;
                font-size: 9px;
                font-weight: 800;
                text-transform: uppercase;
            }}
            .tranche-table td {{
                padding: 6px;
                border-bottom: 1px solid #f1f5f9;
            }}
            .bar-pour {{
                background: #0a1728;
                height: 11px;
                border-radius: 3px;
                display: inline-block;
                border-left: 3px solid #ebb837;
            }}
            .bar-contre {{
                background: #e8590c;
                height: 11px;
                border-radius: 3px;
                display: inline-block;
            }}

            /* Causerie Coach Callout */
            .briefing-box {{
                background: #0a1728;
                color: white;
                border-radius: 14px;
                padding: 12px 16px;
                margin-top: 12px;
                border-left: 5px solid #ebb837;
            }}
            .briefing-title {{
                font-family: 'Oswald', sans-serif;
                font-size: 13.5px;
                font-weight: 700;
                color: #ebb837;
                text-transform: uppercase;
                margin-bottom: 5px;
            }}
            .briefing-box ul {{
                margin: 0;
                padding-left: 16px;
                font-size: 10px;
                line-height: 1.4;
                color: #e2e8f0;
            }}
            .briefing-box li {{ margin-bottom: 3px; }}
            .briefing-box strong {{ color: #ebb837; }}

            /* Footer Mobile ESG */
            .footer {{
                background: #ebb837;
                border-radius: 12px;
                padding: 10px 18px;
                margin-top: 14px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                color: #0a1728;
                font-weight: 800;
            }}
            .footer .slogan {{
                font-family: 'Oswald', sans-serif;
                font-size: 15px;
                letter-spacing: 1px;
                text-transform: uppercase;
            }}
            .footer .tag {{ font-size: 9.5px; font-weight: 800; }}
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

        <!-- BLOC SCOUTING ADVERSAIRE + ALERTE JURIDIQUE OFFICIELLE -->
        <div class="scouting-card">
            <div class="scouting-header">
                <div class="scouting-title">🎯 Espionnage Tactique : St-Martin Tatinghem</div>
                <div class="scouting-badge">R3 Côte d'Opale</div>
            </div>

            <!-- ENCADRÉ ROUGE ALERTE SUSPENSION -->
            <div class="alert-suspension">
                <div class="alert-suspension-title">🚨 ALERTE SUSPENSION : MOUAAD MADRI (ATT. VEDETTE ADVERSE)</div>
                <div class="alert-suspension-desc">
                    L'attaquant vedette adverse a reçu <strong>3 cartons jaunes en moins de 3 mois</strong> : CDF T2 (88'), R3 J3 (27') et CDF T5 (48'). En vertu de l'art. 226 des Règlements FFF, sa suspension automatique prend effet le 19/10/2026 et s'applique <strong>ce dimanche contre Genech</strong>.<br/>
                    👉 <strong>CONSIGNE STAFF :</strong> Vérifier la liste des suspendus sur Footclubs. S'il est aligné dimanche sur la feuille FMI, <strong>poser une réserve d'avant-match immédiate (victoire sur tapis vert possible)</strong>.
                </div>
            </div>

            <div class="scouting-grid">
                <div class="scout-box">
                    <div class="scout-box-title">🔥 Danger n°1 Sportif</div>
                    <div style="font-size:10px; color:#cbd5e1; line-height:1.4;">
                        Ex-pro L2/National. Auteur de 3 buts sur ses 2 derniers matchs (doublé au Tour 5, but en J4). S'il joue, marquage strict à deux dès la relance.
                    </div>
                </div>
                <div class="scout-box">
                    <div class="scout-box-title">⚠️ Faille Majeure Détectée</div>
                    <div style="font-size:10px; color:#cbd5e1; line-height:1.4;">
                        <strong>Défense friable en fin de match :</strong> 2 buts encaissés face à Neufchâtel à la 74' et 90' au Tour 5. Équipe nerveuse (4 cartons jaunes reçus).
                    </div>
                </div>
            </div>
        </div>

        <!-- Quarts d'Heure Genech -->
        <div class="section-card">
            <div class="section-title">
                <span>⏱️ Efficacité par Quart d'Heure (ESG)</span>
                <span style="font-size: 9.5px; color:#64748b;">ESG (Bleu) vs Adv (Orange)</span>
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
                        <td><span class="bar-pour" style="width: {max(buts_pour[0]*22, 4)}px;"></span> 0</td>
                        <td><span class="bar-contre" style="width: {max(buts_contre[0]*22, 4)}px;"></span> 0</td>
                        <td><span style="color:#64748b;">Observation & bloc serré</span></td>
                    </tr>
                    <tr>
                        <td><strong>16-30'</strong></td>
                        <td><span class="bar-pour" style="width: {max(buts_pour[1]*22, 4)}px;"></span> 0</td>
                        <td><span class="bar-contre" style="width: {max(buts_contre[1]*22, 4)}px;"></span> 1</td>
                        <td><span style="color:#64748b;">Temps faible ponctuel</span></td>
                    </tr>
                    <tr>
                        <td><strong>31-45+'</strong></td>
                        <td><span class="bar-pour" style="width: {max(buts_pour[2]*22, 4)}px;"></span> 2</td>
                        <td><span class="bar-contre" style="width: {max(buts_contre[2]*22, 4)}px;"></span> 2</td>
                        <td><span style="color:#e8590c; font-weight:700;">Transition rapide</span></td>
                    </tr>
                    <tr>
                        <td><strong>46-60'</strong></td>
                        <td><span class="bar-pour" style="width: {max(buts_pour[3]*22, 4)}px;"></span> 1</td>
                        <td><span class="bar-contre" style="width: {max(buts_contre[3]*22, 4)}px;"></span> 0</td>
                        <td><span style="color:#0a1728; font-weight:700;">Reprise bien cadenassée</span></td>
                    </tr>
                    <tr>
                        <td><strong>61-75'</strong></td>
                        <td><span class="bar-pour" style="width: {max(buts_pour[4]*22, 4)}px;"></span> 2</td>
                        <td><span class="bar-contre" style="width: {max(buts_contre[4]*22, 4)}px;"></span> 0</td>
                        <td><span style="color:#0a1728; font-weight:700;">Coaching gagnant (Subs)</span></td>
                    </tr>
                    <tr style="background: #fef3c7;">
                        <td><strong>76-90+'</strong></td>
                        <td><span class="bar-pour" style="width: {max(buts_pour[5]*22, 4)}px;"></span> <strong>3</strong></td>
                        <td><span class="bar-contre" style="width: {max(buts_contre[5]*22, 4)}px;"></span> 1</td>
                        <td><strong style="color: #b45309;">🔥 ZONE DE FINITION ESG</strong></td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Causerie Coach -->
        <div class="briefing-box">
            <div class="briefing-title">📋 3 Clés pour la Causerie du Coach</div>
            <ul>
                <li><strong>Gestion de Madri :</strong> S'il est sur le terrain, couper les transmissions. Si la réserve FMI est posée, jouer sans panique : le match se gagne aussi sur le terrain juridique.</li>
                <li><strong>Exploiter leur baisse physique :</strong> Tatinghem concède ses buts après la 70e. Genech y est surpuissant (3 buts inscrits). Garder le rythme.</li>
                <li><strong>Zéro contestation :</strong> Rester irréprochable auprès du corps arbitral. Qualification historique en jeu pour le 7e Tour National.</li>
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
    print(" Fiche Mobile avec Alerte Suspension générée avec succès !")

if __name__ == "__main__":
    generate_mobile_briefing()
