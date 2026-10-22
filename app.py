"""
ES Genech Data Performance — Application Officielle Multi-Équipes
Application Web & Mobile (PWA) de la cellule Performance de l'ES Genech (FFF #525674)
"""

import os
import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime

# Configuration de la page Streamlit
st.set_page_config(
    page_title="ES Genech • Data Performance Hub",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "genech_performance.db")
LOGO_PATH = os.path.join(BASE_DIR, "logo_genech_transparent.png")
OUTPUT_DIR = os.path.join(BASE_DIR, "briefings_coach")

# Style CSS Club : Identité visuelle #0a1728 (Bleu Nuit), #ebb837 (Or), #f8fafc
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&family=Oswald:wght@600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Montserrat', sans-serif;
    }
    
    .stApp {
        background-color: #f8fafc;
    }

    /* Header Banner */
    .club-header {
        background: linear-gradient(135deg, #0a1728 0%, #152744 100%);
        border-radius: 16px;
        padding: 20px 24px;
        color: white;
        margin-bottom: 24px;
        border-bottom: 4px solid #ebb837;
        box-shadow: 0 8px 20px rgba(10, 23, 40, 0.12);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .club-header h1 {
        font-family: 'Oswald', sans-serif;
        font-size: 28px;
        font-weight: 700;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .club-header h1 span {
        color: #ebb837;
    }
    .club-header p {
        margin: 4px 0 0 0;
        font-size: 13px;
        color: #cbd5e1;
        font-weight: 600;
    }
    .badge-affil {
        background: rgba(235, 184, 55, 0.15);
        border: 1px solid #ebb837;
        color: #ebb837;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 12px;
        letter-spacing: 0.5px;
    }

    /* KPI Cards */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 16px 20px;
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
        color: #64748b;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-family: 'Oswald', sans-serif;
        font-size: 28px;
        font-weight: 700;
        color: #0a1728;
        margin: 4px 0;
    }
    .metric-sub {
        font-size: 11px;
        color: #475569;
        font-weight: 600;
    }

    /* Match Card */
    .match-row {
        background: white;
        border-radius: 10px;
        padding: 12px 18px;
        margin-bottom: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
        display: flex;
        align-items: center;
        justify-content: space-between;
        border: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# Connexion DB
@st.cache_data(ttl=60)
def load_db_data():
    conn = sqlite3.connect(DB_PATH)
    equipes_df = pd.read_sql_query("SELECT * FROM equipes_club ORDER BY id ASC", conn)
    matchs_df = pd.read_sql_query("SELECT * FROM matchs ORDER BY date_heure DESC", conn)
    events_df = pd.read_sql_query("SELECT * FROM match_events", conn)
    classement_df = pd.read_sql_query("SELECT * FROM classement_poule ORDER BY rang ASC", conn)
    conn.close()
    return equipes_df, matchs_df, events_df, classement_df

equipes_df, matchs_df, events_df, classement_df = load_db_data()

# HEADER
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.markdown("""
    <div class="club-header">
        <div>
            <h1>ES <span>GENECH</span> • HUB DATA PERFORMANCE</h1>
            <p>Plateforme Tactique, Analytics & Suivi Multi-Équipes • Club FFF #525674</p>
        </div>
        <div class="badge-affil">
            OFFICIEL FFF #525674
        </div>
    </div>
    """, unsafe_allow_html=True)

# SIDEBAR : SÉLECTEUR MULTI-ÉQUIPES
st.sidebar.image(LOGO_PATH if os.path.exists(LOGO_PATH) else "⚽", width=90)
st.sidebar.title("Navigation Club")

poles = ["🏢 TOUTES LES ÉQUIPES (Vue Globale)"] + list(equipes_df["pole"].unique())
selected_pole = st.sidebar.selectbox("Filtrer par Pôle", poles)

if selected_pole == "🏢 TOUTES LES ÉQUIPES (Vue Globale)":
    selected_team_id = "ALL"
    team_info = None
else:
    filtered_teams = equipes_df[equipes_df["pole"] == selected_pole]
    team_names = filtered_teams["nom_affiche"].tolist()
    selected_team_name = st.sidebar.selectbox("Sélectionner l'Équipe", team_names)
    team_info = filtered_teams[filtered_teams["nom_affiche"] == selected_team_name].iloc[0]
    selected_team_id = team_info["id"]

st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 Navigation Rapide")
st.sidebar.info(
    "💡 **Astuce Smartphone :** Ouvrez ce lien sur Safari ou Chrome et cliquez sur **« Ajouter à l'écran d'accueil »** pour l'avoir en raccourci appli sur votre téléphone."
)

# ONGLET PRINCIPAL
tabs = st.tabs([
    "🏠 Le Grand Récap du Club",
    "👥 Focus Équipe & Résultats",
    "📇 Joueurs & Performance (Senior A)",
    "⚖️ Veille Disciplinaire & Brûlage",
    "📄 Livrables Staff (PDF)"
])

# -------------------------------------------------------------
# TAB 1 : LE GRAND RÉCAP DU CLUB (TOUTES ÉQUIPES)
# -------------------------------------------------------------
with tabs[0]:
    st.markdown("### 📊 Synthèse Globale du Club (Le Bilan du Week-End)")

    # Calcul des métriques globales
    matchs_termines = matchs_df[matchs_df["statut"] == "TERMINE"]
    
    # Calcul des victoires Genech
    victoires_club = 0
    nuls_club = 0
    defaites_club = 0
    buts_marques_club = 0
    buts_encaisses_club = 0

    for _, r in matchs_termines.iterrows():
        is_dom = "GENECH" in r["equipe_domicile"].upper()
        s_g = r["score_domicile"] if is_dom else r["score_exterieur"]
        s_opp = r["score_exterieur"] if is_dom else r["score_domicile"]
        
        if pd.notnull(s_g) and pd.notnull(s_opp):
            buts_marques_club += int(s_g)
            buts_encaisses_club += int(s_opp)
            if s_g > s_opp:
                victoires_club += 1
            elif s_g == s_opp:
                nuls_club += 1
            else:
                defaites_club += 1

    total_joues = victoires_club + nuls_club + defaites_club
    win_rate = (victoires_club / total_joues * 100) if total_joues > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card green">
            <div class="metric-label">Victoires du Club</div>
            <div class="metric-value">{victoires_club}</div>
            <div class="metric-sub">{win_rate:.1f}% de victoires TCC</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card gold">
            <div class="metric-label">Matchs Nuls</div>
            <div class="metric-value">{nuls_club}</div>
            <div class="metric-sub">Points précieux partagés</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card blue">
            <div class="metric-label">Attaque Totale Club</div>
            <div class="metric-value">{buts_marques_club} Buts</div>
            <div class="metric-sub">{buts_marques_club / total_joues:.1f} b/match en moyenne</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        diff_club = buts_marques_club - buts_encaisses_club
        st.markdown(f"""
        <div class="metric-card orange">
            <div class="metric-label">Différence de Buts</div>
            <div class="metric-value">{'+' if diff_club > 0 else ''}{diff_club}</div>
            <div class="metric-sub">{buts_encaisses_club} buts concédés</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🗓️ Dernières Rencontres Disputées (Toutes Équipes)")

    filtre_pole = st.selectbox("Afficher par catégorie", ["Toutes"] + list(equipes_df["pole"].unique()), key="tab1_filter")
    
    df_display = matchs_df.copy()
    if filtre_pole != "Toutes":
        target_eqs = equipes_df[equipes_df["pole"] == filtre_pole]["id"].tolist()
        df_display = df_display[df_display["equipe_club_id"].isin(target_eqs)]

    # Affichage tabulaire propre
    match_table = []
    for _, row in df_display.head(25).iterrows():
        # Trouver le nom de l'équipe club
        eq_meta = equipes_df[equipes_df["id"] == row["equipe_club_id"]]
        eq_nom = eq_meta["nom_affiche"].iloc[0] if not eq_meta.empty else row["equipe_club_id"]
        
        score_txt = f"{int(row['score_domicile'])} - {int(row['score_exterieur'])}" if pd.notnull(row['score_domicile']) else "À VENIR"
        match_table.append({
            "Date": row["date_heure"],
            "Équipe Genech": eq_nom,
            "Compétition": row["competition_id"],
            "Affiche": f"{row['equipe_domicile']} vs {row['equipe_exterieur']}",
            "Score": score_txt,
            "Statut": row["statut"]
        })

    st.dataframe(pd.DataFrame(match_table), use_container_width=True)

# -------------------------------------------------------------
# TAB 2 : FOCUS ÉQUIPE & RÉSULTATS
# -------------------------------------------------------------
with tabs[1]:
    if selected_team_id == "ALL":
        st.info("👈 Veuillez choisir une équipe spécifique dans la barre latérale gauche pour consulter son espace dédié.")
    else:
        st.markdown(f"### 🛡️ Espace Dédié : {team_info['nom_affiche']}")
        st.caption(f"Championnat : **{team_info['championnat']}** • Format : **{team_info['format_jeu']}** • Pôle : **{team_info['pole']}**")

        team_matches = matchs_df[matchs_df["equipe_club_id"] == selected_team_id].sort_values(by="date_heure", ascending=False)
        
        c_left, c_right = st.columns([1, 1])
        
        with c_left:
            st.markdown("####  ⏮️ Dernier Match Disputé")
            last_m = team_matches[team_matches["statut"] == "TERMINE"]
            if not last_m.empty:
                lm = last_m.iloc[0]
                s_d = int(lm['score_domicile']) if pd.notnull(lm['score_domicile']) else 0
                s_e = int(lm['score_exterieur']) if pd.notnull(lm['score_exterieur']) else 0
                is_dom = "GENECH" in lm["equipe_domicile"].upper()
                s_genech = s_d if is_dom else s_e
                s_opp = s_e if is_dom else s_d
                res = "VICTOIRE" if s_genech > s_opp else ("NUL" if s_genech == s_opp else "DÉFAITE")
                color = "#15803d" if res == "VICTOIRE" else ("#ebb837" if res == "NUL" else "#b91c1c")

                st.markdown(f"""
                <div style="background: white; border-radius: 12px; padding: 16px; border-left: 6px solid {color}; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                    <div style="font-size: 11px; font-weight: 800; color: #64748b; text-transform: uppercase;">{lm['date_heure']} • {lm['competition_id']}</div>
                    <div style="font-size: 20px; font-weight: 800; color: #0a1728; margin: 6px 0;">{lm['equipe_domicile']} {s_d} - {s_e} {lm['equipe_exterieur']}</div>
                    <span style="background: {color}; color: white; padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 800;">{res}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.write("Aucun match terminé enregistré pour le moment.")

        with c_right:
            st.markdown("#### ⏭️ Prochain Match au Calendrier")
            next_m = team_matches[team_matches["statut"] == "A_VENIR"]
            if not next_m.empty:
                nm = next_m.iloc[-1]
                st.markdown(f"""
                <div style="background: #0a1728; color: white; border-radius: 12px; padding: 16px; border-bottom: 4px solid #ebb837; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                    <div style="font-size: 11px; font-weight: 800; color: #ebb837; text-transform: uppercase;">PROCHAINE RENCONTRE • {nm['date_heure']}</div>
                    <div style="font-size: 18px; font-weight: 800; margin: 6px 0;">{nm['equipe_domicile']} VS {nm['equipe_exterieur']}</div>
                    <div style="font-size: 12px; color: #cbd5e1;">Compétition : {nm['competition_id']}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.write("Aucune rencontre à venir renseignée.")

        st.markdown("---")
        st.markdown("#### 📅 Calendrier Complet de la Saison")
        st.dataframe(team_matches[["date_heure", "competition_id", "equipe_domicile", "score_domicile", "score_exterieur", "equipe_exterieur", "statut"]], use_container_width=True)

# -------------------------------------------------------------
# TAB 3 : JOUEURS & PERFORMANCE (SENIOR A)
# -------------------------------------------------------------
with tabs[2]:
    st.markdown("### 📇 Cartes Profil & Performance des Joueurs (Senior A)")
    
    # Import du module de player rating
    from player_rating import calculate_player_ratings
    ratings_df = calculate_player_ratings()

    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        top_mvp = ratings_df.iloc[0]
        st.markdown(f"""
        <div class="metric-card gold">
            <div class="metric-label">⭐ MVP Actuel de la Saison</div>
            <div class="metric-value">{top_mvp['joueur']}</div>
            <div class="metric-sub">{top_mvp['esg_impact_score']}/100 ESG Impact Score ({top_mvp['buts']} buts, {top_mvp['clean_sheets_participees']} CS)</div>
        </div>
        """, unsafe_allow_html=True)

    with col_s2:
        top_scorer = ratings_df.sort_values(by="buts", ascending=False).iloc[0]
        st.markdown(f"""
        <div class="metric-card blue">
            <div class="metric-label">🎯 Meilleur Buteur TCC</div>
            <div class="metric-value">{top_scorer['joueur']}</div>
            <div class="metric-sub">{top_scorer['buts']} buts inscrits cette saison</div>
        </div>
        """, unsafe_allow_html=True)

    with col_s3:
        iron_man = ratings_df.sort_values(by="minutes_estimees", ascending=False).iloc[0]
        st.markdown(f"""
        <div class="metric-card green">
            <div class="metric-label">⏱️ Cadre le Plus Utilisé</div>
            <div class="metric-value">{iron_man['joueur']}</div>
            <div class="metric-sub">{iron_man['minutes_estimees']} minutes de jeu (8 titularisations)</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🏆 Classement d'Impact des Joueurs (ESG Impact Score)")
    st.dataframe(
        ratings_df[["joueur", "esg_impact_score", "badge_tactique", "matchs_joues", "titularisations", "minutes_estimees", "buts", "clean_sheets_participees", "cartons_jaunes", "cartons_rouges"]],
        use_container_width=True
    )

# -------------------------------------------------------------
# TAB 4 : VEILLE DISCIPLINAIRE & BRÛLAGE
# -------------------------------------------------------------
with tabs[3]:
    st.markdown("### ⚖️ Veille Disciplinaire & Règle FFF du Brûlage")
    st.caption("Application stricte des Articles 226 (Cumul 3 cartons en 90j) et 167 (Brûlage entre Équipe A et Réserve B).")

    from discipline_monitor import analyze_discipline
    df_disc, alerts_disc = analyze_discipline()

    st.markdown("#### 🚨 Alertes Staff Immédiates")
    for a in alerts_disc:
        st.warning(a)

    st.markdown("#### 📋 Casier Disciplinaire Officiel du Club")
    st.dataframe(df_disc, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 🔒 Surveillance de la Règle du Brûlage (Sénior A ↔ Sénior B)")
    st.info(
        "💡 **Rappel Règlement FFF (Art. 167) :** Un joueur ayant disputé plus de 10 rencontres officielles avec l'équipe première (Sénior A) ne peut plus descendre jouer avec l'équipe réserve (Sénior B/C) lors des 5 dernières journées de championnat."
    )
    
    # Suivi des matchs en A pour la réserve
    brulage_df = ratings_df[ratings_df["matchs_joues"] >= 5][["joueur", "matchs_joues", "titularisations"]].copy()
    brulage_df["statut_brulage"] = brulage_df["matchs_joues"].apply(lambda m: "⚠️ À RISQUE (≥ 8 matchs)" if m >= 8 else "AUTORISÉ EN RÉSERVE")
    st.dataframe(brulage_df, use_container_width=True)

# -------------------------------------------------------------
# TAB 5 : LIVRABLES STAFF (PDF TÉLÉCHARGEABLES)
# -------------------------------------------------------------
with tabs[4]:
    st.markdown("### 📄 Espace Téléchargement des Livrables Staff & Direction")
    st.caption("Tous les documents officiels générés automatiquement chaque semaine, prêts à imprimer ou à envoyer sur WhatsApp.")

    col_doc1, col_doc2 = st.columns(2)

    with col_doc1:
        st.markdown("#### ⚽ Briefing d'Avant-Match (Vendredi)")
        briefing_pdf = os.path.join(OUTPUT_DIR, "briefing_match_latest.pdf")
        briefing_png = os.path.join(OUTPUT_DIR, "briefing_match_latest.png")
        if os.path.exists(briefing_pdf):
            with open(briefing_pdf, "rb") as f:
                st.download_button("📥 Télécharger le Briefing PDF (Format Smartphone)", f, file_name="briefing_match_genech.pdf", mime="application/pdf")
        if os.path.exists(briefing_png):
            st.image(briefing_png, caption="Aperçu du Briefing d'Avant-Match", width=420)

    with col_doc2:
        st.markdown("#### 📊 Débrief Post-Match du Lundi")
        debrief_pdf = os.path.join(OUTPUT_DIR, "debrief_match_latest.pdf")
        debrief_png = os.path.join(OUTPUT_DIR, "debrief_match_latest.png")
        if os.path.exists(debrief_pdf):
            with open(debrief_pdf, "rb") as f:
                st.download_button("📥 Télécharger le Débrief 90' PDF", f, file_name="debrief_postmatch_genech.pdf", mime="application/pdf")
        if os.path.exists(debrief_png):
            st.image(debrief_png, caption="Aperçu du Débrief Post-Match", width=420)
