"""
Générateur de Fiches & Cartes Individuelles Joueurs ("Profil Football Manager / FIFA")
Rendu mobile haute résolution (1080x1920) : Jauges de compétences, Impact Scores & État de Sursis
Projet ES Genech Data Performance - Portfolio SportTech
"""

import os
import sys
import base64
import pandas as pd
from playwright.sync_api import sync_playwright

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(BASE_DIR, "briefings_coach")
LOGO_PATH = os.path.join(BASE_DIR, "logo_genech_transparent.png")
os.makedirs(OUTPUT_DIR, exist_ok=True)

from player_rating import calculate_player_ratings
from discipline_monitor import analyze_discipline
from substitutions_impact import calculate_substitutions_impact

def launch_browser(p):
    args = ['--disable-blink-features=AutomationControlled', '--no-sandbox']
    try:
        return p.chromium.launch(channel="chrome", headless=True, args=args)
    except Exception:
        return p.chromium.launch(headless=True, args=args)

def generate_player_cards():
    df_ratings = calculate_player_ratings()
    df_discipline, _ = analyze_discipline()
    df_subs = calculate_substitutions_impact()

    if df_ratings.empty:
        print("Aucune donnée joueur.")
        return

    # Fusion avec la discipline et les remplacements
    df_merged = df_ratings.merge(df_discipline[['joueur', 'statut_juridique_fff', 'niveau_alerte', 'expiration_sursis']], on='joueur', how='left')
    df_merged = df_merged.merge(df_subs[['joueur', 'plus_minus_total', 'impact_banc']], on='joueur', how='left')

    logo_b64 = ""
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode("utf-8")

    # Sélection des 6 joueurs les plus représentatifs de l'effectif
    top_players = df_merged.head(6)

    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>ES Genech - Cartes Individuelles Joueurs</title>
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
                padding: 22px 26px;
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

            /* Grille de 6 Cartes Joueurs */
            .cards-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
            }}

            .player-card {{
                background: white;
                border-radius: 14px;
                padding: 12px 14px;
                box-shadow: 0 4px 12px rgba(10, 23, 40, 0.06);
                border: 1px solid #cbd5e1;
                border-top: 4px solid #004687;
                display: flex;
                flex-direction: column;
                gap: 6px;
            }}
            .player-card.gold {{ border-top-color: #ebb837; }}
            .player-card.orange {{ border-top-color: #e8590c; }}

            .card-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .player-name {{
                font-family: 'Oswald', sans-serif;
                font-size: 16px;
                font-weight: 700;
                text-transform: uppercase;
                color: #0a1728;
            }}
            .player-score {{
                background: #0a1728;
                color: #ebb837;
                font-family: 'Oswald', sans-serif;
                font-size: 16px;
                font-weight: 900;
                padding: 2px 9px;
                border-radius: 8px;
            }}
            .badge-tactique {{
                font-size: 8.5px;
                font-weight: 800;
                color: #475569;
                text-transform: uppercase;
            }}

            /* Jauges */
            .gauge-group {{
                display: flex;
                flex-direction: column;
                gap: 4px;
                margin: 4px 0;
            }}
            .gauge-item {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                font-size: 8px;
                font-weight: 700;
            }}
            .gauge-label {{
                width: 85px;
                color: #64748b;
                text-transform: uppercase;
            }}
            .gauge-bar-bg {{
                flex: 1;
                height: 7px;
                background: #e2e8f0;
                border-radius: 4px;
                margin: 0 8px;
                overflow: hidden;
            }}
            .gauge-bar-fill {{
                height: 100%;
                border-radius: 4px;
                background: #004687;
            }}
            .gauge-bar-fill.gold {{ background: #ebb837; }}
            .gauge-bar-fill.orange {{ background: #e8590c; }}
            .gauge-val {{
                width: 32px;
                text-align: right;
                font-weight: 800;
                color: #0a1728;
            }}

            /* Statut Juridique FFF */
            .status-pill {{
                font-size: 8px;
                font-weight: 800;
                padding: 4px 8px;
                border-radius: 6px;
                text-align: center;
                text-transform: uppercase;
                margin-top: 2px;
            }}
            .status-pill.VERT {{ background: #dcfce7; color: #15803d; }}
            .status-pill.JAUNE {{ background: #fef9c3; color: #854d0e; }}
            .status-pill.ORANGE {{ background: #ffedd5; color: #c2410c; border: 1px solid #f97316; }}
            .status-pill.ROUGE {{ background: #fee2e2; color: #b91c1c; border: 1px solid #ef4444; }}

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
                    <p>Cellule Performance • Fiches Individuelles Joueurs</p>
                </div>
            </div>
            <div class="header-badge">
                <div class="comp">Saison 2026-2027</div>
                <div class="tour">EFFECTIF CADRE</div>
            </div>
        </div>

        <!-- Grille 6 Cartes Joueurs -->
        <div class="cards-grid">
    """

    for idx, p in top_players.iterrows():
        name = p['joueur']
        score = p['esg_impact_score']
        badge = p['badge_tactique']
        mins = p['minutes_estimees']
        cs = p['clean_sheets_participees']
        buts = p['buts']
        cj = p['cartons_jaunes']
        statut_fff = p['statut_juridique_fff'] if pd.notnull(p['statut_juridique_fff']) else "CASIER VIERGE"
        gravite = p['niveau_alerte'] if pd.notnull(p['niveau_alerte']) else "VERT"
        
        # Jauges normalisées sur 100
        vol_pct = min(100, int((mins / 720) * 100))
        def_pct = min(100, int((cs / 5) * 100))
        att_pct = min(100, int((buts / 2) * 100)) if buts > 0 else 10
        disc_pct = max(10, 100 - (cj * 25))

        top_color_class = "gold" if score >= 80 else ("orange" if "Buteur" in badge else "")

        html += f"""
            <div class="player-card {top_color_class}">
                <div class="card-header">
                    <div>
                        <div class="player-name">{name}</div>
                        <div class="badge-tactique">{badge}</div>
                    </div>
                    <div class="player-score">{score}</div>
                </div>

                <div class="gauge-group">
                    <div class="gauge-item">
                        <span class="gauge-label">Volume (Mins)</span>
                        <div class="gauge-bar-bg"><div class="gauge-bar-fill gold" style="width: {vol_pct}%;"></div></div>
                        <span class="gauge-val">{mins}'</span>
                    </div>
                    <div class="gauge-item">
                        <span class="gauge-label">Défense (CS)</span>
                        <div class="gauge-bar-bg"><div class="gauge-bar-fill" style="width: {def_pct}%;"></div></div>
                        <span class="gauge-val">{cs} CS</span>
                    </div>
                    <div class="gauge-item">
                        <span class="gauge-label">Attaque (Buts)</span>
                        <div class="gauge-bar-bg"><div class="gauge-bar-fill orange" style="width: {att_pct}%;"></div></div>
                        <span class="gauge-val">{buts} B</span>
                    </div>
                    <div class="gauge-item">
                        <span class="gauge-label">Discipline</span>
                        <div class="gauge-bar-bg"><div class="gauge-bar-fill" style="width: {disc_pct}%; background:#15803d;"></div></div>
                        <span class="gauge-val">{cj} J</span>
                    </div>
                </div>

                <div class="status-pill {gravite}">
                    FFF : {statut_fff}
                </div>
            </div>
        """

    html += f"""
        </div>

        <!-- Footer -->
        <div class="footer">
            <div class="slogan">TOUJOURS ENSEMBLE • ALLEZ L'ESG</div>
            <div class="tag">Cellule Performance • Suivi Individuel Staff</div>
        </div>

    </body>
    </html>
    """

    with sync_playwright() as p:
        browser = launch_browser(p)
        page = browser.new_page(viewport={"width": 1080, "height": 1920})
        page.set_content(html, wait_until="networkidle")

        out_png = os.path.join(OUTPUT_DIR, "cartes_profil_joueurs.png")
        out_pdf = os.path.join(OUTPUT_DIR, "cartes_profil_joueurs.pdf")

        page.screenshot(path=out_png, full_page=True)
        page.pdf(path=out_pdf, print_background=True, width="1080px", height="1920px")
        browser.close()

    print("Cartes de profil joueurs générées avec succès (PNG & PDF) !")

if __name__ == "__main__":
    generate_player_cards()
