"""
ES Genech Data Performance — Application Officielle Multi-Équipes
Application Web & Mobile (PWA) de la cellule Performance de l'ES Genech (FFF #525674)
"""

import os
import sys
import base64
import sqlite3
import importlib
import pandas as pd
import streamlit as st
from datetime import datetime

# Rechargement dynamique des modules de scoring
import player_rating
import discipline_monitor
importlib.reload(discipline_monitor)
importlib.reload(player_rating)

st.set_page_config(
    page_title="ES Genech • Hub Performance",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "genech_performance.db")
LOGO_PATH = os.path.join(BASE_DIR, "logo_genech_transparent.png")
OUTPUT_DIR = os.path.join(BASE_DIR, "briefings_coach")

# Style CSS Club avec contraste garanti (mode clair & sombre)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&family=Oswald:wght@600;700&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Montserrat', sans-serif;
        background-color: #f8fafc !important;
        color: #0a1728 !important;
    }

    /* En-tête Club Genech */
    .club-header {
        background: linear-gradient(135deg, #0a1728 0%, #152744 100%);
        border-radius: 14px;
        padding: 16px 22px;
        margin-bottom: 20px;
        border-bottom: 4px solid #ebb837;
        box-shadow: 0 6px 16px rgba(10, 23, 40, 0.12);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .club-header h1 {
        font-family: 'Oswald', sans-serif !important;
        font-size: 26px !important;
        font-weight: 700 !important;
        margin: 0 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: white !important;
    }
    .club-header h1 span { color: #ebb837 !important; }
    .club-header p {
        margin: 3px 0 0 0 !important;
        font-size: 12px !important;
        color: #cbd5e1 !important;
        font-weight: 600 !important;
    }

    /* FORCER LE CONTRASTE DE TOUS LES TEXTES ET TITRES STREAMLIT */
    h1, h2, h3, h4, h5, h6, .stMarkdown p, .stMarkdown span, .stMarkdown strong {
        color: #0a1728 !important;
    }
    .stCaption, [data-testid="stCaptionContainer"] p {
        color: #475569 !important;
        font-weight: 600 !important;
    }

    /* ONGLETS STREAMLIT : TEXTE CLAIREMENT LISIBLE À CÔTÉ DES EMOJIS */
    button[data-baseweb="tab"] {
        padding: 10px 18px !important;
        background-color: #ffffff !important;
        border-radius: 8px 8px 0 0 !important;
        margin-right: 4px !important;
        border: 1px solid #e2e8f0 !important;
        border-bottom: none !important;
    }
    button[data-baseweb="tab"] div,
    button[data-baseweb="tab"] p,
    button[data-baseweb="tab"] span {
        color: #334155 !important;
        font-size: 14px !important;
        font-weight: 700 !important;
        opacity: 1 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #0a1728 !important;
        border-bottom: 3px solid #ebb837 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] div,
    button[data-baseweb="tab"][aria-selected="true"] p,
    button[data-baseweb="tab"][aria-selected="true"] span {
        color: #ebb837 !important;
        font-weight: 900 !important;
    }

    /* Cartes Métriques */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 14px 18px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        border-left: 5px solid #0a1728;
    }
    .metric-card.gold { border-left-color: #ebb837; }
    .metric-card.green { border-left-color: #15803d; }
    .metric-card.orange { border-left-color: #e8590c; }
    .metric-card.blue { border-left-color: #004687; }
    .metric-label {
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        color: #64748b !important;
    }
    .metric-value {
        font-family: 'Oswald', sans-serif;
        font-size: 26px;
        font-weight: 700;
        color: #0a1728 !important;
        margin: 3px 0;
    }
    .metric-sub {
        font-size: 11px;
        color: #475569 !important;
        font-weight: 600;
    }

    /* Tableaux Streamlit : index masqué, design moderne */
    [data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #cbd5e1;
        box-shadow: 0 4px 12px rgba(10, 23, 40, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# Connexion directe SANS CACHE pour garantir une réactivité instantanée à chaque clic
def get_db_data():
    conn = sqlite3.connect(DB_PATH)
    equipes_df = pd.read_sql_query("SELECT * FROM equipes_club ORDER BY id ASC", conn)
    matchs_df = pd.read_sql_query("SELECT * FROM matchs WHERE equipe_club_id != 'SCOUTING' AND (equipe_domicile LIKE '%GENECH%' OR equipe_exterieur LIKE '%GENECH%') ORDER BY date_heure DESC", conn)
    events_df = pd.read_sql_query("SELECT * FROM match_events", conn)
    classement_df = pd.read_sql_query("SELECT * FROM classement_poule ORDER BY rang ASC", conn)
    conn.close()
    return equipes_df, matchs_df, events_df, classement_df

equipes_df, matchs_df, events_df, classement_df = get_db_data()

# Logo Base64
logo_b64 = ""
if os.path.exists(LOGO_PATH):
    with open(LOGO_PATH, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode("utf-8")

# Sidebar avec Logo & Identité Club
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=120)
    st.markdown("### **ES GENECH**")
    st.caption("Cellule Performance & Analytics • FFF #525674")
    st.markdown("---")
    st.markdown("🟡⚫ **Club Partenaire Régional**")
    st.caption("Régional 3 Poule D • Ligue des Hauts-de-France")

# HEADER
st.markdown(f"""
<div class="club-header">
    <div style="display: flex; align-items: center; gap: 18px;">
        <img src="data:image/png;base64,{logo_b64}" alt="Logo ES Genech" style="height: 64px; width: auto; filter: drop-shadow(0 4px 10px rgba(0,0,0,0.35));">
        <div>
            <h1>ES <span>GENECH</span> • HUB DATA PERFORMANCE</h1>
            <p>Plateforme Tactique & Analytics Officielle • Club FFF #525674</p>
        </div>
    </div>
    <div style="background: rgba(235, 184, 55, 0.2); border: 1px solid #ebb837; color: #ebb837; padding: 8px 16px; border-radius: 20px; font-weight: 800; font-size: 12px; text-transform: uppercase;">
        16 Équipes Engagées
    </div>
</div>
""", unsafe_allow_html=True)

# SÉLECTEUR PRINCIPAL CENTRAL (Réactif et direct)
equipe_options = [("ALL", "🏢 TOUTES LES ÉQUIPES (Bilan Global Club)")]
for _, row in equipes_df.iterrows():
    equipe_options.append((row["id"], f"{row['pole']} • {row['nom_affiche']}"))

selected_index = 0
selected_option = st.selectbox(
    "👉 SÉLECTIONNEZ UNE ÉQUIPE OU LE CLUB GLOBAL :",
    options=[opt[0] for opt in equipe_options],
    format_func=lambda x: dict(equipe_options)[x],
    index=0
)

is_global = (selected_option == "ALL")

# FILTRAGE DYNAMIQUE IMMÉDIAT DU DATAFRAME
if is_global:
    current_matchs = matchs_df.copy()
    current_title = "Bilan Général de l'ES Genech (Toutes Équipes)"
    current_subtitle = "Statistiques cumulées sur l'ensemble des 16 catégories du club"
else:
    current_matchs = matchs_df[matchs_df["equipe_club_id"] == selected_option].copy()
    current_team_info = equipes_df[equipes_df["id"] == selected_option].iloc[0]
    current_title = f"{current_team_info['nom_affiche']}"
    current_subtitle = f"{current_team_info['championnat']} • {current_team_info['format_jeu']} ({current_team_info['pole']})"

st.markdown(f"### 🎯 {current_title}")
st.caption(current_subtitle)

# CALCUL DYNAMIQUE DES MÉTRIQUES EN FONCTION DU FILTRE SÉLECTIONNÉ
matchs_termines = current_matchs[current_matchs["statut"] == "TERMINE"]

victoires = 0
nuls = 0
defaites = 0
buts_pour = 0
buts_contre = 0

for _, r in matchs_termines.iterrows():
    is_dom = "GENECH" in r["equipe_domicile"].upper()
    s_g = r["score_domicile"] if is_dom else r["score_exterieur"]
    s_opp = r["score_exterieur"] if is_dom else r["score_domicile"]
    
    if pd.notnull(s_g) and pd.notnull(s_opp):
        buts_pour += int(s_g)
        buts_contre += int(s_opp)
        if s_g > s_opp:
            victoires += 1
        elif s_g == s_opp:
            nuls += 1
        else:
            defaites += 1

total_joues = victoires + nuls + defaites
win_pct = (victoires / total_joues * 100) if total_joues > 0 else 0
avg_buts = (buts_pour / total_joues) if total_joues > 0 else 0.0
diff = buts_pour - buts_contre

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class="metric-card green">
        <div class="metric-label">Victoires</div>
        <div class="metric-value">{victoires} / {total_joues}</div>
        <div class="metric-sub">{win_pct:.1f}% de taux de victoire</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card gold">
        <div class="metric-label">Matchs Nuls</div>
        <div class="metric-value">{nuls}</div>
        <div class="metric-sub">Points de parité</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card blue">
        <div class="metric-label">Attaque (Buts Marqués)</div>
        <div class="metric-value">{buts_pour}</div>
        <div class="metric-sub">{avg_buts:.1f} b/m en moyenne</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card {'green' if diff >= 0 else 'orange'}">
        <div class="metric-label">Différence de Buts</div>
        <div class="metric-value">{'+' if diff > 0 else ''}{diff}</div>
        <div class="metric-sub">{buts_contre} buts concédés</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ONGLETS SPÉCIFIQUES
if is_global:
    # VUE GLOBALE
    tab_global_matches, tab_about = st.tabs(["🗓️ Tous les Matchs du Club", "ℹ️ Informations Club"])
    
    with tab_global_matches:
        st.markdown("#### 📋 Liste des Rencontres (Multi-Équipes)")
        
        # Filtre optionnel supplémentaire par pôle
        sub_pole = st.radio("Filtrer l'affichage :", ["Tous les pôles"] + list(equipes_df["pole"].unique()), horizontal=True)
        df_sub = current_matchs.copy()
        if sub_pole != "Tous les pôles":
            target_ids = equipes_df[equipes_df["pole"] == sub_pole]["id"].tolist()
            df_sub = df_sub[df_sub["equipe_club_id"].isin(target_ids)]

        table_rows = []
        for _, row in df_sub.iterrows():
            eq_meta = equipes_df[equipes_df["id"] == row["equipe_club_id"]]
            eq_nom = eq_meta["nom_affiche"].iloc[0] if not eq_meta.empty else row["equipe_club_id"]
            score_txt = f"{int(row['score_domicile'])} - {int(row['score_exterieur'])}" if pd.notnull(row['score_domicile']) else "À VENIR"
            table_rows.append({
                "Date": row["date_heure"],
                "Équipe Genech": eq_nom,
                "Compétition": row["competition_id"],
                "Rencontre": f"{row['equipe_domicile']} vs {row['equipe_exterieur']}",
                "Score": score_txt,
                "Statut": row["statut"]
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

    with tab_about:
        st.markdown("#### ℹ️ Club FFF : Entente Sportive de Genech")
        st.write("Numéro d'affiliation officiel FFF : **#525674**")
        st.write("Nombre total d'équipes enregistrées : **16 catégories**")
        st.dataframe(equipes_df[["nom_affiche", "pole", "championnat", "format_jeu"]], use_container_width=True, hide_index=True)

else:
    # VUE FOCUS ÉQUIPE
    tab_matchs, tab_perf, tab_disc, tab_docs = st.tabs([
        "🗓️ Calendrier & Résultats",
        "📇 Joueurs & Performance",
        "⚖️ Discipline & Brûlage FFF",
        "📥 Documents & PDF Staff"
    ])

    with tab_matchs:
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("##### ⏮️ Dernier Match")
            last_m = current_matchs[current_matchs["statut"] == "TERMINE"]
            if not last_m.empty:
                lm = last_m.iloc[0]
                s_d = int(lm['score_domicile']) if pd.notnull(lm['score_domicile']) else 0
                s_e = int(lm['score_exterieur']) if pd.notnull(lm['score_exterieur']) else 0
                is_dom = "GENECH" in lm["equipe_domicile"].upper()
                s_g = s_d if is_dom else s_e
                s_o = s_e if is_dom else s_d
                tag = "VICTOIRE" if s_g > s_o else ("NUL" if s_g == s_o else "DÉFAITE")
                color = "#15803d" if tag == "VICTOIRE" else ("#ebb837" if tag == "NUL" else "#b91c1c")
                st.markdown(f"""
                <div style="background: white; border-radius: 12px; padding: 14px; border-left: 5px solid {color}; box-shadow: 0 4px 10px rgba(0,0,0,0.04);">
                    <div style="font-size: 11px; font-weight: 800; color: #64748b;">{lm['date_heure']}</div>
                    <div style="font-size: 18px; font-weight: 800; color: #0a1728; margin: 4px 0;">{lm['equipe_domicile']} {s_d} - {s_e} {lm['equipe_exterieur']}</div>
                    <span style="background: {color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 800;">{tag}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Aucun match terminé enregistré.")

        with c_right:
            st.markdown("##### ⏭️ Prochain Match")
            next_m = current_matchs[current_matchs["statut"] == "A_VENIR"]
            if not next_m.empty:
                nm = next_m.iloc[-1]
                st.markdown(f"""
                <div style="background: #0a1728; color: white; border-radius: 12px; padding: 14px; border-bottom: 4px solid #ebb837;">
                    <div style="font-size: 11px; font-weight: 800; color: #ebb837;">AFFICHE • {nm['date_heure']}</div>
                    <div style="font-size: 17px; font-weight: 800; margin: 4px 0;">{nm['equipe_domicile']} VS {nm['equipe_exterieur']}</div>
                    <div style="font-size: 11px; color: #cbd5e1;">{nm['competition_id']}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Aucun match à venir programmé.")

        st.markdown("##### 📅 Calendrier Officiel de la Saison")
        st.dataframe(current_matchs[["date_heure", "competition_id", "equipe_domicile", "score_domicile", "score_exterieur", "equipe_exterieur", "statut"]], use_container_width=True, hide_index=True)

    with tab_perf:
        if selected_option == "SENIOR_M1":
            importlib.reload(player_rating)
            ratings_df = player_rating.calculate_player_ratings()
            
            st.markdown(f"#### 🏆 Classement ESG Impact Score • Effectif Senior A ({len(ratings_df)} Joueurs)")
            st.caption("Données certifiées feuilles de match officielles FFF (Régional 3 Poule D & Coupe de France)")

            search_query = st.text_input("🔍 Rechercher un joueur (ex: Elio, Devernay, Herve...)", key="search_player")
            df_display = ratings_df.copy()
            if search_query:
                df_display = df_display[df_display["joueur"].str.contains(search_query.strip(), case=False, na=False)]

            st.dataframe(
                df_display[["rang", "joueur", "esg_impact_score", "badge_tactique", "matchs_joues", "titularisations", "minutes_estimees", "buts", "clean_sheets_participees", "cartons_jaunes", "cartons_rouges"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "rang": st.column_config.NumberColumn("#", format="%d", width="small"),
                    "joueur": st.column_config.TextColumn("Joueur", width="medium"),
                    "esg_impact_score": st.column_config.NumberColumn("Score ESG", format="%.1f pts"),
                    "badge_tactique": st.column_config.TextColumn("Rôle Tactique"),
                    "matchs_joues": st.column_config.NumberColumn("Matchs", format="%d"),
                    "titularisations": st.column_config.NumberColumn("Tit.", format="%d"),
                    "minutes_estimees": st.column_config.NumberColumn("Minutes", format="%d'"),
                    "buts": st.column_config.NumberColumn("Buts", format="%d"),
                    "clean_sheets_participees": st.column_config.NumberColumn("Clean Sheets", format="%d"),
                    "cartons_jaunes": st.column_config.NumberColumn("🟨", format="%d"),
                    "cartons_rouges": st.column_config.NumberColumn("🟥", format="%d")
                }
            )
        else:
            conn = sqlite3.connect(DB_PATH)
            team_players_df = pd.read_sql_query("""
                SELECT ml.joueur_nom, 
                       count(DISTINCT ml.match_id) as matchs_joues,
                       sum(case when ml.role = 'TITULAIRE' then 1 else 0 end) as titularisations,
                       sum(case when ml.role = 'REMPLACANT' then 1 else 0 end) as remplacements
                FROM match_lineups ml
                JOIN matchs m ON ml.match_id = m.id
                WHERE m.equipe_club_id = ? AND ml.equipe LIKE '%GENECH%'
                GROUP BY ml.joueur_nom
                ORDER BY matchs_joues DESC, titularisations DESC
            """, conn, params=(selected_option,))
            
            team_scorers_df = pd.read_sql_query("""
                SELECT me.acteur_principal as buteur, count(*) as buts
                FROM match_events me
                JOIN matchs m ON me.match_id = m.id
                WHERE m.equipe_club_id = ? AND me.type_event = 'BUT' AND me.equipe LIKE '%GENECH%'
                GROUP BY me.acteur_principal
                ORDER BY buts DESC
            """, conn, params=(selected_option,))
            conn.close()

            if not team_players_df.empty:
                st.markdown(f"#### 👥 Effectif Officiel & Temps de Jeu ({len(team_players_df)} Joueurs Convoqués)")
                st.caption(f"Données officielles feuilles de match FFF • {current_title}")

                if not team_scorers_df.empty:
                    team_players_df = team_players_df.merge(team_scorers_df, left_on="joueur_nom", right_on="buteur", how="left")
                    team_players_df["buts"] = team_players_df["buts"].fillna(0).astype(int)
                else:
                    team_players_df["buts"] = 0

                team_players_df.insert(0, "rang", range(1, len(team_players_df) + 1))
                st.dataframe(
                    team_players_df[["rang", "joueur_nom", "matchs_joues", "titularisations", "remplacements", "buts"]],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "rang": st.column_config.NumberColumn("#", format="%d", width="small"),
                        "joueur_nom": st.column_config.TextColumn("Joueur"),
                        "matchs_joues": st.column_config.NumberColumn("Convocations", format="%d"),
                        "titularisations": st.column_config.NumberColumn("Titularisations", format="%d"),
                        "remplacements": st.column_config.NumberColumn("Entrées en Jeu", format="%d"),
                        "buts": st.column_config.NumberColumn("Buts Marqués ⚽", format="%d")
                    }
                )
            else:
                st.info(f"Pour la catégorie {current_title}, les feuilles de match nominatives informatisées (FMI) sont en cours de saisie par le District. Les résultats d'équipe et scores sont consultables dans l'onglet 'Calendrier & Résultats'.")

    with tab_disc:
        if selected_option in ["SENIOR_M1", "SENIOR_M3"]:
            importlib.reload(discipline_monitor)
            df_disc, alerts_disc = discipline_monitor.analyze_discipline()
            st.markdown("#### 🚨 Alertes de Suspension Active (Art. 226 FFF)")
            for a in alerts_disc:
                st.warning(a)
            st.markdown("#### 📋 Casier Disciplinaire")
            st.dataframe(df_disc, use_container_width=True, hide_index=True)

            if selected_option == "SENIOR_M3":
                st.markdown("#### 🔒 Contrôle du Brûlage pour la Réserve (Art. 167 FFF)")
                st.info("Vérification réglementaire FFF : les joueurs de l'équipe première ayant disputé plus de 10 matchs officiels en R3 sont 'brûlés' et ne peuvent plus descendre en D2.")
        else:
            conn = sqlite3.connect(DB_PATH)
            team_cards = pd.read_sql_query("""
                SELECT me.acteur_principal as joueur, me.type_event as sanction, count(*) as total,
                       group_concat(m.date_heure, ', ') as dates
                FROM match_events me
                JOIN matchs m ON me.match_id = m.id
                WHERE m.equipe_club_id = ? AND me.type_event IN ('AVERTISSEMENT', 'EXPULSION') AND me.equipe LIKE '%GENECH%'
                GROUP BY me.acteur_principal, me.type_event
            """, conn, params=(selected_option,))
            conn.close()

            if not team_cards.empty:
                st.markdown("#### ⚖️ Discipline Officielle de la Catégorie")
                st.dataframe(team_cards, use_container_width=True, hide_index=True)
            else:
                st.success(f"✅ Aucun carton officiel enregistré pour {current_title} sur les feuilles FFF. Fair-play parfait !")

    with tab_docs:
        if selected_option == "SENIOR_M1":
            st.markdown("#### 📄 Téléchargement des Livrables Staff (Senior A)")
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1:
                b_pdf = os.path.join(OUTPUT_DIR, "briefing_match_latest.pdf")
                if os.path.exists(b_pdf):
                    with open(b_pdf, "rb") as f:
                        st.download_button("📥 Briefing Avant-Match (PDF)", f, file_name="briefing_es_genech.pdf", mime="application/pdf")
                b_png = os.path.join(OUTPUT_DIR, "briefing_match_latest.png")
                if os.path.exists(b_png):
                    st.image(b_png, caption="Aperçu Briefing Tactique", use_container_width=True)

            with col_d2:
                d_pdf = os.path.join(OUTPUT_DIR, "debrief_match_latest.pdf")
                if os.path.exists(d_pdf):
                    with open(d_pdf, "rb") as f:
                        st.download_button("📥 Débrief 90' Post-Match (PDF)", f, file_name="debrief_postmatch_genech.pdf", mime="application/pdf")
                d_png = os.path.join(OUTPUT_DIR, "debrief_match_latest.png")
                if os.path.exists(d_png):
                    st.image(d_png, caption="Aperçu Débrief 90'", use_container_width=True)

            with col_d3:
                c_pdf = os.path.join(OUTPUT_DIR, "cartes_profil_joueurs.pdf")
                if os.path.exists(c_pdf):
                    with open(c_pdf, "rb") as f:
                        st.download_button("📥 Cartes Profil Joueurs (PDF)", f, file_name="cartes_profil_joueurs.pdf", mime="application/pdf")
                c_png = os.path.join(OUTPUT_DIR, "cartes_profil_joueurs.png")
                if os.path.exists(c_png):
                    st.image(c_png, caption="Aperçu Cartes FM / FIFA", use_container_width=True)
        else:
            st.info(f"Les fiches tactiques PDF d'avant-match et de débriefing hebdomadaire sont générées pour l'équipe fanion (Senior 1).")
