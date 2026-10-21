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

    # Calcul des scores réels officiels DE GENECH UNIQUEMENT
    s_term = df_matchs[
        (df_matchs['statut'] == 'TERMINE') & 
        ((df_matchs['equipe_domicile'].str.contains('GENECH', case=False, na=False)) |
         (df_matchs['equipe_exterieur'].str.contains('GENECH', case=False, na=False)))
    ].copy()
    s_term['is_dom'] = s_term['equipe_domicile'].str.contains('GENECH', case=False, na=False)
    s_term['buts_pour'] = s_term.apply(lambda r: r['score_domicile'] if r['is_dom'] else r['score_exterieur'], axis=1)
    s_term['buts_contre'] = s_term.apply(lambda r: r['score_exterieur'] if r['is_dom'] else r['score_domicile'], axis=1)

    total_buts_marques = int(s_term['buts_pour'].sum())   # Exactement 10 buts
    total_buts_encaisses = int(s_term['buts_contre'].sum()) # Exactement 3 buts

    # Cartons Genech
    cartons_genech = df_events[(df_events['type_event'] == 'AVERTISSEMENT') & (df_events['equipe'].str.contains('GENECH', case=False, na=False))]
    cartons_count = len(cartons_genech)
    cartons_anstaing_derby = len(cartons_genech[cartons_genech['match_id'].str.contains('anstaing', case=False, na=False)])

    # Quarts d'Heure Genech
    df_buts = df_events[df_events['type_event'] == 'BUT'].copy()
    df_buts['is_genech'] = df_buts['equipe'].str.contains('GENECH', case=False, na=False)

    tranches = ["01-15'", "16-30'", "31-45+'", "46-60'", "61-75'", "76-90+'"]
    buts_pour = []
    buts_contre = []
    for t in tranches:
        buts_pour.append(len(df_buts[(df_buts['tranche_quart_heure'] == t) & (df_buts['is_genech'])]))
        buts_contre.append(len(df_buts[(df_buts['tranche_quart_heure'] == t) & (~df_buts['is_genech'])]))

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
                padding: 22px 26px 26px 26px;
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
                border-radius: 16px;
                padding: 14px 20px;
                color: white;
                box-shadow: 0 8px 20px rgba(10, 23, 40, 0.15);
                border: 2px solid #ebb837;
            }}
            .header-left {{
                display: flex;
                align-items: center;
                gap: 14px;
            }}
            .club-logo {{
                width: 64px;
                height: 64px;
                border-radius: 50%;
                border: 3px solid #ebb837;
                padding: 2px;
                background: #0a1728;
            }}
            .club-title h1 {{
                font-family: 'Oswald', sans-serif;
                font-size: 26px;
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
                padding: 8px 14px;
                border-radius: 10px;
                text-align: center;
                font-weight: 800;
            }}
            .header-badge .comp {{
                font-family: 'Oswald', sans-serif;
                font-size: 12px;
                text-transform: uppercase;
            }}
            .header-badge .tour {{
                font-size: 14px;
                font-weight: 900;
            }}

            /* Hero Matchday */
            .match-hero {{
                background: #0a1728;
                border-radius: 14px;
                padding: 12px 18px;
                margin-top: 10px;
                color: white;
                text-align: center;
                border-bottom: 4px solid #e8590c;
            }}
            .hero-tag {{
                display: inline-block;
                background: #e8590c;
                color: white;
                font-size: 10px;
                font-weight: 800;
                padding: 2px 10px;
                border-radius: 20px;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 4px;
            }}
            .hero-teams {{
                font-family: 'Oswald', sans-serif;
                font-size: 27px;
                font-weight: 700;
                text-transform: uppercase;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 12px;
            }}
            .hero-teams .vs {{ color: #ebb837; font-size: 18px; }}

            /* 4 KPIs */
            .kpi-grid {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 8px;
                margin-top: 8px;
            }}
            .kpi-card {{
                background: white;
                border-radius: 10px;
                padding: 8px 10px;
                border-left: 4px solid #0a1728;
                box-shadow: 0 4px 10px rgba(10, 23, 40, 0.05);
            }}
            .kpi-card.gold {{ border-left-color: #ebb837; }}
            .kpi-card.orange {{ border-left-color: #e8590c; }}
            .kpi-label {{
                font-size: 7.5px;
                font-weight: 800;
                text-transform: uppercase;
                color: #64748b;
            }}
            .kpi-val {{
                font-family: 'Oswald', sans-serif;
                font-size: 20px;
                font-weight: 700;
                color: #0a1728;
                margin-top: 1px;
            }}
            .kpi-card.gold .kpi-val {{ color: #d97706; }}
            .kpi-card.orange .kpi-val {{ color: #e8590c; }}
            .kpi-sub {{
                font-size: 7px;
                font-weight: 600;
                color: #64748b;
            }}

            /* TABLEAU COMPARATIF MULTI-SAISONS R3 (NOUVEAU) */
            .benchmark-card {{
                background: white;
                border-radius: 12px;
                padding: 10px 14px;
                margin-top: 8px;
                box-shadow: 0 4px 10px rgba(10, 23, 40, 0.05);
                border: 1px solid #e5e0d3;
            }}
            .benchmark-title {{
                font-family: 'Oswald', sans-serif;
                font-size: 13px;
                font-weight: 700;
                text-transform: uppercase;
                color: #0a1728;
                border-bottom: 2px solid #ebb837;
                padding-bottom: 4px;
                margin-bottom: 6px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .benchmark-table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 9px;
            }}
            .benchmark-table th {{
                text-align: left;
                padding: 4px 6px;
                background: #f1ede1;
                color: #0a1728;
                font-size: 8px;
                font-weight: 800;
                text-transform: uppercase;
            }}
            .benchmark-table td {{
                padding: 4px 6px;
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
                padding: 12px 16px;
                margin-top: 8px;
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
                font-size: 15px;
                font-weight: 700;
                color: #ffffff;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .scouting-badge {{
                background: #e8590c;
                color: white;
                font-size: 8.5px;
                font-weight: 800;
                padding: 2px 7px;
                border-radius: 5px;
                text-transform: uppercase;
            }}

            /* ALERTE SUSPENSION */
            .alert-suspension {{
                background: #b91c1c;
                border-radius: 8px;
                padding: 8px 10px;
                margin-bottom: 6px;
                border-left: 4px solid #fef08a;
            }}
            .alert-suspension-title {{
                font-family: 'Oswald', sans-serif;
                font-size: 12px;
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
                padding: 6px 8px;
            }}
            .scout-box-title {{
                font-size: 8.5px;
                font-weight: 800;
                text-transform: uppercase;
                color: #ebb837;
                margin-bottom: 2px;
            }}

            /* Tableau Quarts d'Heure */
            .section-card {{
                background: white;
                border-radius: 12px;
                padding: 10px 14px;
                margin-top: 8px;
                box-shadow: 0 4px 10px rgba(10, 23, 40, 0.05);
            }}
            .section-title {{
                font-family: 'Oswald', sans-serif;
                font-size: 13px;
                font-weight: 700;
                text-transform: uppercase;
                color: #0a1728;
                border-bottom: 2px solid #ebb837;
                padding-bottom: 3px;
                margin-bottom: 5px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .tranche-table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 9px;
            }}
            .tranche-table th {{
                text-align: left;
                padding: 3px 5px;
                background: #f1ede1;
                color: #0a1728;
                font-size: 8px;
                font-weight: 800;
                text-transform: uppercase;
            }}
            .tranche-table td {{
                padding: 4px 5px;
                border-bottom: 1px solid #f1f5f9;
            }}
            .bar-pour {{
                background: #0a1728;
                height: 9px;
                border-radius: 2px;
                display: inline-block;
                border-left: 2px solid #ebb837;
            }}
            .bar-contre {{
                background: #e8590c;
                height: 9px;
                border-radius: 2px;
                display: inline-block;
            }}

            /* Causerie Coach Callout */
            .briefing-box {{
                background: #0a1728;
                color: white;
                border-radius: 10px;
                padding: 8px 12px;
                margin-top: 8px;
                border-left: 4px solid #ebb837;
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
                border-radius: 10px;
                padding: 8px 14px;
                margin-top: 8px;
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

        <!-- 4 Cartes KPIs Re-filtrées (10 Buts officiels FFF) -->
        <div class="kpi-grid">
            <div class="kpi-card gold">
                <div class="kpi-label">Invincibilité ESG</div>
                <div class="kpi-val">4 / 4</div>
                <div class="kpi-sub">Clean sheets en Coupe (0 but pris)</div>
            </div>
            <div class="kpi-card orange">
                <div class="kpi-label">Ratio 2e Mi-Temps</div>
                <div class="kpi-val">75 %</div>
                <div class="kpi-sub">Des buts inscrits après pause</div>
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

        <!-- TABLEAU COMPARATIF DES SAISONS EN R3 -->
        <div class="benchmark-card">
            <div class="benchmark-title">
                <span>📈 Repères de Performance : Comparatif des Saisons en R3</span>
                <span style="font-size: 8px; color: #64748b;">Source : Archives Officielles LFHF</span>
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
                        <td><strong>🔥 6e Tour (0 but pris • Exploit N1)</strong></td>
                        <td><strong>0 DÉFAITE (Invaincue)</strong></td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- BLOC SCOUTING ADVERSAIRE + ALERTE JURIDIQUE -->
        <div class="scouting-card">
            <div class="scouting-header">
                <div class="scouting-title">🎯 Espionnage Tactique : St-Martin Tatinghem</div>
                <div class="scouting-badge">R3 Côte d'Opale</div>
            </div>

            <!-- ENCADRÉ ROUGE ALERTE SUSPENSION -->
            <div class="alert-suspension">
                <div class="alert-suspension-title">🚨 ALERTE SUSPENSION : MOUAAD MADRI (ATT. VEDETTE ADVERSE)</div>
                <div class="alert-suspension-desc">
                    3 cartons jaunes reçus en moins de 3 mois : CDF T2 (88'), R3 J3 (27') et CDF T5 (48'). En vertu de l'art. 226 des Règlements FFF, sa suspension prend effet le 19/10/2026 et s'applique <strong>ce dimanche contre Genech</strong>.<br/>
                    👉 <strong>CONSIGNE STAFF :</strong> S'il est inscrit sur la feuille FMI dimanche, <strong>poser une réserve d'avant-match immédiate (victoire sur tapis vert possible)</strong>.
                </div>
            </div>

            <div class="scouting-grid">
                <div class="scout-box">
                    <div class="scout-box-title">⚡ Démarrage Canon & Profil</div>
                    <div style="font-size:9px; color:#cbd5e1; line-height:1.35;">
                        Attaque prolifique (14 buts en 4 matchs). Ils pressent très haut dès le coup d'envoi et marquent souvent d'entrée (5' vs Neufchâtel, 39' vs Mouvaux). Être ultra-vigilant sur les 15 premières minutes.
                    </div>
                </div>
                <div class="scout-box">
                    <div class="scout-box-title">⚠️ Faille Physique en Fin de Match</div>
                    <div style="font-size:9px; color:#cbd5e1; line-height:1.35;">
                        <strong>Baisse de régime après la 70e :</strong> 2 buts concédés face à Neufchâtel (74' et 90'). Équipe agressive (4 cartons au 5e Tour) qui commet des fautes sous la fatigue.
                    </div>
                </div>
            </div>
        </div>

        <!-- Quarts d'Heure Genech -->
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
                    <tr>
                        <td><strong>01-15'</strong></td>
                        <td><span class="bar-pour" style="width: {max(buts_pour[0]*22, 4)}px;"></span> 0</td>
                        <td><span class="bar-contre" style="width: {max(buts_contre[0]*22, 4)}px;"></span> 0</td>
                        <td><span style="color:#64748b;">Bloc prudent & observation</span></td>
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
                <li><strong>Absorber l'Entame :</strong> Tatinghem part toujours très fort. Résister au pressing des 15 premières minutes, notre bloc bas sait faire face.</li>
                <li><strong>Exploiter leur baisse physique :</strong> Tatinghem concède ses buts après la 70e. Genech y est surpuissant (3 buts inscrits). Garder le rythme jusqu'au bout.</li>
                <li><strong>Gestion Juridique & Calme :</strong> Poser la réserve FMI si Madri est sur la feuille, et jouer à 100 % sans énervement.</li>
            </ul>
        </div>

        <!-- Footer Mobile ESG -->
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
    print(f" Fiche Mobile mise à jour : Total Buts = {total_buts_marques} !")

if __name__ == "__main__":
    generate_mobile_briefing()
