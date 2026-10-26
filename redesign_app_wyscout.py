"""
Redesign complet de app.py dans l'esprit Wyscout / Transfermarkt :
- Clean Light Mode professionnel (blanc/ardoise/vert pelouse)
- Suppression des gros blocs criards et des emojis excessifs
- Organisation par 4 onglets sobres : Match Center, Classement, Effectif & Performance, Documents Staff
- Prochain match et dernier match mis en avant au premier coup d'œil
- Support multi-clubs (ES Genech VIP & FC Seclin R2)
- Écran de chargement splash screen MatchDay conservé
"""

import os

APP_PY_PATH = os.path.join(os.path.dirname(__file__), "app.py")

new_app_code = '''"""
MatchDay • Football Analytics Platform
Plateforme Professionnelle de Data & Performance pour Clubs Régionaux et Nationaux
"""

import os
import sys
import base64
import sqlite3
import importlib
import pandas as pd
import streamlit as st
from datetime import datetime

# Rechargement des modules de calcul
import player_rating
import discipline_monitor
importlib.reload(discipline_monitor)
importlib.reload(player_rating)

BASE_DIR = os.path.dirname(__file__)
SAAS_LOGO_PATH = os.path.join(BASE_DIR, "logo_app_saas.png")
DB_PATH = os.path.join(BASE_DIR, "genech_performance.db")
SECLIN_DB_PATH = os.path.join(BASE_DIR, "seclin_performance.db")
GENECH_LOGO_PATH = os.path.join(BASE_DIR, "logo_genech_transparent.png")
SECLIN_LOGO_PATH = os.path.join(BASE_DIR, "logo_seclin.jpg")
OUTPUT_DIR = os.path.join(BASE_DIR, "briefings_coach")

st.set_page_config(
    page_title="MatchDay • Football Analytics",
    page_icon=SAAS_LOGO_PATH if os.path.exists(SAAS_LOGO_PATH) else "⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

saas_logo_b64 = ""
if os.path.exists(SAAS_LOGO_PATH):
    with open(SAAS_LOGO_PATH, "rb") as f:
        saas_logo_b64 = base64.b64encode(f.read()).decode("utf-8")

# -------------------------------------------------------------
# ÉCRAN DE CHARGEMENT MATCHDAY (Look PWA Mobile Native)
# -------------------------------------------------------------
if saas_logo_b64 and "splash_shown" not in st.session_state:
    st.session_state["splash_shown"] = True
    st.markdown(f"""
    <div id="matchday-splash">
        <div class="splash-box">
            <img src="data:image/png;base64,{saas_logo_b64}" class="splash-logo" alt="MatchDay Logo">
            <div class="splash-title">MATCH<span>DAY</span></div>
            <div class="splash-sub">FOOTBALL ANALYTICS</div>
            <div class="splash-loader">
                <div class="splash-progress"></div>
            </div>
        </div>
    </div>
    <style>
        #matchday-splash {{
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            background: #070d17 !important;
            z-index: 99999999 !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            animation: splashFadeOut 0.5s cubic-bezier(0.4, 0, 0.2, 1) 2.2s forwards !important;
            pointer-events: none !important;
        }}
        @keyframes splashFadeOut {{
            0% {{ opacity: 1; visibility: visible; }}
            99% {{ opacity: 0; visibility: visible; }}
            100% {{ opacity: 0; visibility: hidden; display: none; }}
        }}
        .splash-box {{
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            text-align: center !important;
        }}
        .splash-logo {{
            width: 120px !important;
            height: 120px !important;
            border-radius: 26px !important;
            box-shadow: 0 10px 35px rgba(0, 0, 0, 0.7) !important;
            animation: splashPulse 1.8s infinite ease-in-out !important;
        }}
        @keyframes splashPulse {{
            0%, 100% {{ transform: scale(1); filter: drop-shadow(0 0 25px rgba(34, 197, 94, 0.45)); }}
            50% {{ transform: scale(1.06); filter: drop-shadow(0 0 45px rgba(34, 197, 94, 0.85)); }}
        }}
        .splash-title {{
            font-family: 'Oswald', sans-serif !important;
            font-size: 38px !important;
            font-weight: 700 !important;
            color: #ffffff !important;
            letter-spacing: 2.5px !important;
            margin-top: 22px !important;
            text-transform: uppercase !important;
        }}
        .splash-title span {{ color: #22c55e !important; }}
        .splash-sub {{
            font-size: 12px !important;
            font-weight: 800 !important;
            color: #94a3b8 !important;
            letter-spacing: 4px !important;
            margin-top: 5px !important;
            text-transform: uppercase !important;
        }}
        .splash-loader {{
            width: 140px !important;
            height: 4px !important;
            background: rgba(255, 255, 255, 0.12) !important;
            border-radius: 4px !important;
            margin-top: 24px !important;
            overflow: hidden !important;
        }}
        .splash-progress {{
            height: 100% !important;
            background: linear-gradient(90deg, #16a34a, #22c55e, #4ade80) !important;
            border-radius: 4px !important;
            animation: progressBar 1.6s cubic-bezier(0.65, 0, 0.35, 1) forwards !important;
        }}
        @keyframes progressBar {{
            0% {{ width: 0%; }}
            100% {{ width: 100%; }}
        }}
    </style>
    """, unsafe_allow_html=True)

# -------------------------------------------------------------
# DESIGN SYSTEM : STYLE WYSCOUT / TRANSFERMARKT (CLEAN LIGHT)
# -------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Oswald:wght@600;700&display=swap');

    /* Fond & Typographie Globale */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #f8fafc !important;
        color: #0f172a !important;
    }

    /* En-tête Pro Sobre */
    .pro-header {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px 24px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .pro-header-left {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .pro-header-title {
        font-family: 'Inter', sans-serif !important;
        font-size: 20px !important;
        font-weight: 800 !important;
        color: #0f172a !important;
        margin: 0 !important;
        letter-spacing: -0.3px;
    }
    .pro-header-sub {
        font-size: 13px !important;
        color: #64748b !important;
        margin: 2px 0 0 0 !important;
        font-weight: 500 !important;
    }
    .pro-badge {
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        color: #334155;
        padding: 6px 14px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .pro-badge.green {
        background: #ecfdf5;
        border-color: #a7f3d0;
        color: #065f46;
    }

    /* Onglets de Navigation Supérieurs Pro */
    button[data-baseweb="tab"] {
        padding: 10px 22px !important;
        background-color: transparent !important;
        border-radius: 6px 6px 0 0 !important;
        margin-right: 6px !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
    }
    button[data-baseweb="tab"] div,
    button[data-baseweb="tab"] p,
    button[data-baseweb="tab"] span {
        color: #64748b !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: transparent !important;
        border-bottom: 2px solid #0f172a !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] div,
    button[data-baseweb="tab"][aria-selected="true"] p,
    button[data-baseweb="tab"][aria-selected="true"] span {
        color: #0f172a !important;
        font-weight: 800 !important;
    }

    /* Cartes Match Center */
    .match-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 20px 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        margin-bottom: 18px;
    }
    .match-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 12px;
        border-bottom: 1px solid #f1f5f9;
        margin-bottom: 16px;
    }
    .match-comp-tag {
        font-size: 12px;
        font-weight: 700;
        color: #0f172a;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .match-date-tag {
        font-size: 12px;
        font-weight: 500;
        color: #64748b;
    }
    .match-clash {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 0;
    }
    .match-team {
        flex: 1;
        font-size: 16px;
        font-weight: 700;
        color: #0f172a;
    }
    .match-team.right {
        text-align: right;
    }
    .match-score-pill {
        background: #0f172a;
        color: #ffffff;
        padding: 6px 16px;
        border-radius: 6px;
        font-size: 18px;
        font-weight: 800;
        letter-spacing: 2px;
    }
    .match-vs-pill {
        background: #f1f5f9;
        color: #475569;
        padding: 6px 16px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 1px;
    }
    .match-meta-footer {
        margin-top: 14px;
        padding-top: 12px;
        border-top: 1px solid #f8fafc;
        display: flex;
        align-items: center;
        gap: 20px;
        font-size: 12px;
        color: #64748b;
    }

    /* Badges de Tableaux */
    .table-badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
    }
    .table-badge.green { background: #dcfce7; color: #166534; }
    .table-badge.blue { background: #e0f2fe; color: #075985; }
    .table-badge.orange { background: #ffedd5; color: #9a3412; }
    .table-badge.gray { background: #f1f5f9; color: #475569; }

    /* Tables Streamlit */
    [data-testid="stDataFrame"] {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        overflow: hidden;
        background: #ffffff;
    }

    /* Téléchargement Card */
    .doc-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .doc-card h5 {
        margin: 0 0 6px 0;
        font-size: 15px;
        font-weight: 700;
        color: #0f172a;
    }
    .doc-card p {
        margin: 0 0 14px 0;
        font-size: 12px;
        color: #64748b;
        line-height: 1.4;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# SIDEBAR : IDENTITÉ MATCHDAY & CHOIX DU CLUB
# -------------------------------------------------------------
with st.sidebar:
    if saas_logo_b64:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px; padding-bottom: 14px; border-bottom: 1px solid #e2e8f0;">
            <img src="data:image/png;base64,{saas_logo_b64}" style="width: 40px; height: 40px; border-radius: 10px;">
            <div>
                <div style="font-size: 18px; font-weight: 800; color: #0f172a; line-height: 1.1;">MATCH<span style="color: #16a34a;">DAY</span></div>
                <div style="font-size: 10px; font-weight: 700; color: #64748b; letter-spacing: 0.5px;">FOOTBALL ANALYTICS</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<p style='font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-bottom: 6px;'>Club Actif</p>", unsafe_allow_html=True)
    club_options = {
        "525674": "ES Genech (Régional 3)",
        "500934": "FC Seclin (Régional 2)"
    }
    selected_club = st.selectbox(
        "Club :",
        options=list(club_options.keys()),
        format_func=lambda x: club_options[x],
        label_visibility="collapsed",
        index=0
    )

    custom_code = st.text_input("Rechercher un code FFF :", placeholder="Ex: 500123", label_visibility="collapsed")
    if custom_code in club_options:
        selected_club = custom_code
    elif custom_code.strip():
        st.caption(f"Club #{custom_code} non synchronisé (SaaS N1-R3).")

    st.markdown("---")
    if st.button("Revoir le Splash Screen", use_container_width=True):
        st.session_state.pop("splash_shown", None)
        st.rerun()

# -------------------------------------------------------------
# LOGIQUE CLUB : ES GENECH OU FC SECLIN
# -------------------------------------------------------------
is_seclin = (selected_club == "500934")

if is_seclin:
    # CLUB FC SECLIN (RÉGIONAL 2)
    club_name = "FC Seclin"
    club_code = "500934"
    club_div = "Seniors Régional 2 • Poule B"
    active_db = SECLIN_DB_PATH
    club_logo = SECLIN_LOGO_PATH
    
    conn = sqlite3.connect(active_db)
    matchs_df = pd.read_sql_query("SELECT * FROM matchs ORDER BY date_heure DESC", conn)
    classement_df = pd.read_sql_query("SELECT * FROM classement ORDER BY rang ASC", conn)
    players_df = pd.read_sql_query("""
        SELECT ml.joueur_nom, 
               count(DISTINCT ml.match_id) as matchs_joues,
               sum(case when ml.role = 'TITULAIRE' then 1 else 0 end) as titularisations,
               sum(case when ml.role = 'REMPLACANT' then 1 else 0 end) as remplacements
        FROM match_lineups ml
        WHERE ml.equipe LIKE '%SECLIN%'
        GROUP BY ml.joueur_nom
        ORDER BY matchs_joues DESC, titularisations DESC
    """, conn)
    scorers_df = pd.read_sql_query("""
        SELECT acteur_principal as joueur_nom, count(*) as buts
        FROM match_events
        WHERE type_event = 'BUT' AND equipe LIKE '%SECLIN%'
        GROUP BY acteur_principal
        ORDER BY buts DESC
    """, conn)
    cards_df = pd.read_sql_query("""
        SELECT acteur_principal as joueur, count(*) as cartons_jaunes
        FROM match_events
        WHERE type_event LIKE '%AVERTISSEMENT%' AND equipe LIKE '%SECLIN%'
        GROUP BY acteur_principal
        ORDER BY cartons_jaunes DESC
    """, conn)
    conn.close()

    if not scorers_df.empty:
        players_df = players_df.merge(scorers_df, on="joueur_nom", how="left")
        players_df["buts"] = players_df["buts"].fillna(0).astype(int)
    else:
        players_df["buts"] = 0

else:
    # CLUB ES GENECH (VIP R3 & TOUTES CATÉGORIES)
    club_name = "ES Genech"
    club_code = "525674"
    club_div = "Seniors Régional 3 • Poule D"
    active_db = DB_PATH
    club_logo = GENECH_LOGO_PATH
    
    conn = sqlite3.connect(active_db)
    equipes_df = pd.read_sql_query("SELECT * FROM equipes_club ORDER BY id ASC", conn)
    matchs_df = pd.read_sql_query("SELECT * FROM matchs WHERE equipe_club_id != 'SCOUTING' ORDER BY date_heure DESC", conn)
    classement_df = pd.read_sql_query("SELECT * FROM classement_poule WHERE competition_id = 'r3_poule_d' ORDER BY rang ASC", conn)
    conn.close()

# Logo club en base64
club_logo_b64 = ""
if os.path.exists(club_logo):
    with open(club_logo, "rb") as f:
        club_logo_b64 = base64.b64encode(f.read()).decode("utf-8")

# EN-TÊTE PRO DE L'APPLICATION
st.markdown(f"""
<div class="pro-header">
    <div class="pro-header-left">
        <img src="data:image/png;base64,{club_logo_b64}" style="height: 48px; width: auto; object-fit: contain;">
        <div>
            <h1 class="pro-header-title">{club_name} • Performance Center</h1>
            <p class="pro-header-sub">Affiliation FFF #{club_code} • {club_div}</p>
        </div>
    </div>
    <div class="pro-badge green">
        Plateforme Certifiée FFF
    </div>
</div>
""", unsafe_allow_html=True)

# SÉLECTEUR D'ÉQUIPE (SOBRE DANS GENECH)
selected_team_id = "SENIOR_M1"
if not is_seclin:
    equipe_map = {row["id"]: f"{row['nom_affiche']} ({row['championnat']})" for _, row in equipes_df.iterrows()}
    # Mettre Senior A en premier
    equipe_keys = ["SENIOR_M1"] + [k for k in equipe_map.keys() if k != "SENIOR_M1"]
    
    col_sel, col_stat = st.columns([2, 3])
    with col_sel:
        selected_team_id = st.selectbox(
            "Catégorie analysée :",
            options=equipe_keys,
            format_func=lambda x: equipe_map.get(x, x),
            index=0
        )
    with col_stat:
        # Bilan express discret
        team_m = matchs_df[matchs_df["equipe_club_id"] == selected_team_id]
        term = team_m[team_m["statut"] == "TERMINE"]
        v, n, d = 0, 0, 0
        for _, r in term.iterrows():
            is_dom = "GENECH" in r["equipe_domicile"].upper()
            sg = r["score_domicile"] if is_dom else r["score_exterieur"]
            so = r["score_exterieur"] if is_dom else r["score_domicile"]
            if pd.notnull(sg) and pd.notnull(so):
                if sg > so: v += 1
                elif sg == so: n += 1
                else: d += 1
        st.markdown(f"""
        <div style="padding-top: 28px; font-size: 13px; color: #64748b;">
            Bilan officiel : <strong style="color: #0f172a;">{v}V - {n}N - {d}D</strong> ({len(term)} matchs disputés)
        </div>
        """, unsafe_allow_html=True)

# -------------------------------------------------------------
# LES 4 ONGLETS PRO MATCHDAY
# -------------------------------------------------------------
tab_match_center, tab_classement, tab_effectif, tab_docs = st.tabs([
    "Match Center",
    "Classement",
    "Effectif & Performance",
    "Documents Staff"
])

# -------------------------------------------------------------
# 1. MATCH CENTER (Prochain match en avant + Dernier résultat + Calendrier)
# -------------------------------------------------------------
with tab_match_center:
    c_next, c_last = st.columns(2)

    with c_next:
        st.markdown("#### Prochain Match")
        if not is_seclin:
            if selected_team_id == "SENIOR_M1":
                st.markdown("""
                <div class="match-card">
                    <div class="match-card-header">
                        <span class="match-comp-tag">Régional 3 (Poule D) • Journée 5</span>
                        <span class="match-date-tag">Dimanche 8 Novembre 2026 • 14h30</span>
                    </div>
                    <div class="match-clash">
                        <div class="match-team">ANICHE SC</div>
                        <div class="match-vs-pill">VS</div>
                        <div class="match-team right">GENECH ES</div>
                    </div>
                    <div class="match-meta-footer">
                        <span>📍 Stade Jean Wanquet, Aniche</span>
                        <span>⚔️ <strong>Choc du haut de tableau</strong> (2e vs 3e, 8 pts)</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                next_spec = matchs_df[(matchs_df["equipe_club_id"] == selected_team_id) & (matchs_df["statut"] == "A_VENIR")]
                if not next_spec.empty:
                    nm = next_spec.iloc[0]
                    st.markdown(f"""
                    <div class="match-card">
                        <div class="match-card-header">
                            <span class="match-comp-tag">{nm['competition_id']}</span>
                            <span class="match-date-tag">{nm['date_heure']}</span>
                        </div>
                        <div class="match-clash">
                            <div class="match-team">{nm['equipe_domicile']}</div>
                            <div class="match-vs-pill">VS</div>
                            <div class="match-team right">{nm['equipe_exterieur']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("Aucun match à venir programmé sur le calendrier FFF.")
        else:
            st.markdown("""
            <div class="match-card">
                <div class="match-card-header">
                    <span class="match-comp-tag">Coupe Hauts-de-France • 3e Tour</span>
                    <span class="match-date-tag">Dimanche 25 Octobre • 15h00</span>
                </div>
                <div class="match-clash">
                    <div class="match-team">ARQUES ES</div>
                    <div class="match-vs-pill">VS</div>
                    <div class="match-team right">SECLIN FC</div>
                </div>
                <div class="match-meta-footer">
                    <span>📍 Stade Municipal d'Arques</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with c_last:
        st.markdown("#### Dernier Résultat")
        if not is_seclin:
            if selected_team_id == "SENIOR_M1":
                st.markdown("""
                <div class="match-card">
                    <div class="match-card-header">
                        <span class="match-comp-tag">Coupe de France • 6e Tour (Finale Régionale)</span>
                        <span class="match-date-tag">Dimanche 25 Octobre 2026</span>
                    </div>
                    <div class="match-clash">
                        <div class="match-team">ST MARTIN TATINGHEM</div>
                        <div class="match-score-pill">2 - 0</div>
                        <div class="match-team right">GENECH ES</div>
                    </div>
                    <div class="match-meta-footer">
                        <span>Fin du parcours en Coupe de France • 0 carton reçu</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                last_spec = matchs_df[(matchs_df["equipe_club_id"] == selected_team_id) & (matchs_df["statut"] == "TERMINE")]
                if not last_spec.empty:
                    lm = last_spec.iloc[0]
                    st.markdown(f"""
                    <div class="match-card">
                        <div class="match-card-header">
                            <span class="match-comp-tag">{lm['competition_id']}</span>
                            <span class="match-date-tag">{lm['date_heure']}</span>
                        </div>
                        <div class="match-clash">
                            <div class="match-team">{lm['equipe_domicile']}</div>
                            <div class="match-score-pill">{int(lm['score_domicile'])} - {int(lm['score_exterieur'])}</div>
                            <div class="match-team right">{lm['equipe_exterieur']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="match-card">
                <div class="match-card-header">
                    <span class="match-comp-tag">Régional 2 (Poule B) • Journée 4</span>
                    <span class="match-date-tag">Dimanche 18 Octobre</span>
                </div>
                <div class="match-clash">
                    <div class="match-team">SECLIN FC</div>
                    <div class="match-score-pill">12 - 0</div>
                    <div class="match-team right">MONTIGNY GOHELLE</div>
                </div>
                <div class="match-meta-footer">
                    <span>Triplé de Mouhamadou S., doublés de Corentin L., Luther M., Evan D.</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### Calendrier Officiel & Résultats FFF")
    
    current_m_df = matchs_df[matchs_df["equipe_club_id"] == selected_team_id] if not is_seclin else matchs_df
    cal_rows = []
    for _, r in current_m_df.iterrows():
        sc = f"{int(r['score_domicile'])} - {int(r['score_exterieur'])}" if pd.notnull(r['score_domicile']) else "À venir"
        cal_rows.append({
            "Date": r["date_heure"],
            "Compétition": r["competition_id"],
            "Domicile": r["equipe_domicile"],
            "Score": sc,
            "Extérieur": r["equipe_exterieur"],
            "Statut": r["statut"]
        })
    st.dataframe(pd.DataFrame(cal_rows), use_container_width=True, hide_index=True)

# -------------------------------------------------------------
# 2. CLASSEMENT OFFICIEL
# -------------------------------------------------------------
with tab_classement:
    st.markdown(f"#### Classement Officiel • {club_div}")
    st.caption("Données certifiées de la Ligue des Hauts-de-France")
    
    if not classement_df.empty:
        st.dataframe(
            classement_df[["rang", "equipe" if is_seclin else "equipe_nom", "points", "joues", "victoires" if not is_seclin else "gagnes", "nuls", "defaites" if not is_seclin else "perdus", "buts_pour", "buts_contre", "diff"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "rang": st.column_config.NumberColumn("#", format="%d", width="small"),
                "equipe_nom": st.column_config.TextColumn("Club"),
                "equipe": st.column_config.TextColumn("Club"),
                "points": st.column_config.NumberColumn("Points", format="%d pts"),
                "joues": st.column_config.NumberColumn("J", format="%d"),
                "victoires": st.column_config.NumberColumn("V", format="%d"),
                "gagnes": st.column_config.NumberColumn("V", format="%d"),
                "nuls": st.column_config.NumberColumn("N", format="%d"),
                "defaites": st.column_config.NumberColumn("D", format="%d"),
                "perdus": st.column_config.NumberColumn("D", format="%d"),
                "buts_pour": st.column_config.NumberColumn("BP", format="%d"),
                "buts_contre": st.column_config.NumberColumn("BC", format="%d"),
                "diff": st.column_config.NumberColumn("+/-", format="%d")
            }
        )
    else:
        st.info("Classement en attente de synchronisation pour cette catégorie.")

# -------------------------------------------------------------
# 3. EFFECTIF & PERFORMANCE (Style Wyscout Épuré)
# -------------------------------------------------------------
with tab_effectif:
    if not is_seclin and selected_team_id == "SENIOR_M1":
        importlib.reload(player_rating)
        ratings_df = player_rating.calculate_player_ratings()

        st.markdown(f"#### Effectif Senior A & Évaluations de Performance ({len(ratings_df)} Joueurs Convoqués)")
        st.caption("Notes d'impact ESG Impact Scores (0-100) basées sur les feuilles de match officielles")

        # Recherche de joueur sobre
        search = st.text_input("Filtrer par nom :", placeholder="Ex: Devernay, Nisse, Delcroix...", label_visibility="collapsed")
        df_disp = ratings_df.copy()
        if search:
            df_disp = df_disp[df_disp["joueur"].str.contains(search.strip(), case=False, na=False)]

        # Nettoyage des badges tactiques pour supprimer les emojis excessifs
        df_disp["badge_tactique"] = df_disp["badge_tactique"].str.replace(r"[^a-zA-Z0-9éèàê /\\-\\+]", "", regex=True).str.strip()

        st.dataframe(
            df_disp[["rang", "joueur", "esg_impact_score", "badge_tactique", "matchs_joues", "titularisations", "minutes_estimees", "buts", "cartons_jaunes", "cartons_rouges"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "rang": st.column_config.NumberColumn("#", format="%d", width="small"),
                "joueur": st.column_config.TextColumn("Joueur"),
                "esg_impact_score": st.column_config.NumberColumn("Score ESG", format="%.1f pts"),
                "badge_tactique": st.column_config.TextColumn("Rôle Tactique"),
                "matchs_joues": st.column_config.NumberColumn("Matchs", format="%d"),
                "titularisations": st.column_config.NumberColumn("Tit.", format="%d"),
                "minutes_estimees": st.column_config.NumberColumn("Temps de Jeu", format="%d min"),
                "buts": st.column_config.NumberColumn("Buts", format="%d"),
                "cartons_jaunes": st.column_config.NumberColumn("Jaunes", format="%d"),
                "cartons_rouges": st.column_config.NumberColumn("Rouges", format="%d")
            }
        )

        st.markdown("---")
        st.markdown("#### Veille Disciplinaire & Risques de Suspension (Art. 226 FFF)")
        st.caption("Surveillance réglementaire officielle : 3 avertissements en moins de 90 jours = 1 match ferme.")

        importlib.reload(discipline_monitor)
        df_disc, alerts_disc = discipline_monitor.analyze_discipline()
        
        # Affichage sobre des alertes
        col_al1, col_al2 = st.columns([1, 1])
        with col_al1:
            st.markdown("##### Statuts Règlementaires Actifs")
            for a in alerts_disc:
                st.warning(a.replace("⚠️", "").strip())
        with col_al2:
            st.markdown("##### Casier Disciplinaire Officiel")
            st.dataframe(
                df_disc[["joueur", "cartons_jaunes_90j", "statut_juridique_fff", "expiration_sursis"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "joueur": st.column_config.TextColumn("Joueur"),
                    "cartons_jaunes_90j": st.column_config.NumberColumn("Cartons Jaunes (90j)", format="%d"),
                    "statut_juridique_fff": st.column_config.TextColumn("Statut FFF"),
                    "expiration_sursis": st.column_config.TextColumn("Expiration Sursis")
                }
            )

    elif is_seclin:
        st.markdown(f"#### Effectif FC Seclin ({len(players_df)} Joueurs Convoqués)")
        st.caption("Données officielles FFF • Seniors Régional 2")
        st.dataframe(
            players_df[["joueur_nom", "matchs_joues", "titularisations", "remplacements", "buts"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "joueur_nom": st.column_config.TextColumn("Joueur"),
                "matchs_joues": st.column_config.NumberColumn("Convocations", format="%d"),
                "titularisations": st.column_config.NumberColumn("Titularisations", format="%d"),
                "remplacements": st.column_config.NumberColumn("Remplacements", format="%d"),
                "buts": st.column_config.NumberColumn("Buts Marqués", format="%d")
            }
        )
        st.markdown("---")
        st.markdown("#### Veille Disciplinaire (Art. 226 FFF)")
        st.dataframe(cards_df[["joueur", "cartons_jaunes"]], use_container_width=True, hide_index=True)

    else:
        conn = sqlite3.connect(active_db)
        team_p = pd.read_sql_query("""
            SELECT ml.joueur_nom, 
                   count(DISTINCT ml.match_id) as matchs_joues,
                   sum(case when ml.role = 'TITULAIRE' then 1 else 0 end) as titularisations,
                   sum(case when ml.role = 'REMPLACANT' then 1 else 0 end) as remplacements
            FROM match_lineups ml
            JOIN matchs m ON ml.match_id = m.id
            WHERE m.equipe_club_id = ? AND ml.equipe LIKE '%GENECH%'
            GROUP BY ml.joueur_nom
            ORDER BY matchs_joues DESC, titularisations DESC
        """, conn, params=(selected_team_id,))
        conn.close()

        if not team_p.empty:
            st.markdown(f"#### Effectif Officiel ({len(team_p)} Joueurs)")
            st.dataframe(team_p, use_container_width=True, hide_index=True)
        else:
            st.info("Feuilles de match informatisées en cours de synchronisation par le District.")

# -------------------------------------------------------------
# 4. DOCUMENTS STAFF (Téléchargements PDF 1-Clic)
# -------------------------------------------------------------
with tab_docs:
    st.markdown("#### Livrables Staff & Rapports Techniques")
    st.caption("Documents haute définition prêts à imprimer ou partager sur WhatsApp / Telegram")

    col_doc1, col_doc2 = st.columns(2)

    with col_doc1:
        st.markdown("""
        <div class="doc-card">
            <h5>Briefing Tactique Avant-Match</h5>
            <p>Analyse de l'adversaire (Aniche SC), points forts, faiblesses, météo terrain et profil de l'arbitre.</p>
        </div>
        """, unsafe_allow_html=True)
        b_pdf = os.path.join(OUTPUT_DIR, "briefing_match_latest.pdf")
        if os.path.exists(b_pdf):
            with open(b_pdf, "rb") as f:
                st.download_button("Télécharger le Briefing Avant-Match (PDF)", f, file_name="briefing_avant_match.pdf", mime="application/pdf", use_container_width=True)

        st.markdown("""
        <div class="doc-card" style="margin-top: 14px;">
            <h5>Fiches Profils Joueurs (ESG Impact Scores)</h5>
            <p>Cartes individuelles de performance (0-100), temps de jeu, rôle tactique et indicateurs clés.</p>
        </div>
        """, unsafe_allow_html=True)
        c_pdf = os.path.join(OUTPUT_DIR, "cartes_profil_joueurs.pdf")
        if os.path.exists(c_pdf):
            with open(c_pdf, "rb") as f:
                st.download_button("Télécharger les Cartes Joueurs (PDF)", f, file_name="cartes_profil_joueurs.pdf", mime="application/pdf", use_container_width=True)

    with col_doc2:
        st.markdown("""
        <div class="doc-card">
            <h5>Débriefing 90' Post-Match (Tatinghem vs Genech)</h5>
            <p>Déroulé minute par minute du 6e Tour de Coupe de France, faits de jeu, remplacements et analyse du banc.</p>
        </div>
        """, unsafe_allow_html=True)
        d_pdf = os.path.join(OUTPUT_DIR, "debrief_match_latest.pdf")
        if os.path.exists(d_pdf):
            with open(d_pdf, "rb") as f:
                st.download_button("Télécharger le Débriefing 90' Post-Match (PDF)", f, file_name="debrief_tatinghem_genech.pdf", mime="application/pdf", use_container_width=True)

        st.markdown("""
        <div class="doc-card" style="margin-top: 14px;">
            <h5>Rapport Exécutif Mensuel (Comité Directeur)</h5>
            <p>Synthèse stratégique mensuelle destinée au Président et au Comité de Direction.</p>
        </div>
        """, unsafe_allow_html=True)
        r_pdf = os.path.join(OUTPUT_DIR, "rapport_executif_mensuel.pdf")
        if os.path.exists(r_pdf):
            with open(r_pdf, "rb") as f:
                st.download_button("Télécharger le Rapport Exécutif (PDF)", f, file_name="rapport_executif_mensuel.pdf", mime="application/pdf", use_container_width=True)
'''

with open(APP_PY_PATH, "w", encoding="utf-8") as f:
    f.write(new_app_code)

print("✅ app.py entièrement refondu dans le style Wyscout / Transfermarkt !")
