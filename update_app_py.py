with open('C:/Users/ninof/.gemini/antigravity/scratch/genech_data_performance/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add reload at top
top_code = """import os
import sys
import sqlite3
import importlib
import pandas as pd
import streamlit as st
from datetime import datetime

import player_rating
import discipline_monitor
importlib.reload(discipline_monitor)
importlib.reload(player_rating)
"""

content = content.replace("""import os
import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime""", top_code)

# 2. Update tab_perf with search and count
old_tab_perf = """    with tab_perf:
        if selected_option == "SENIOR_M1":
            from player_rating import calculate_player_ratings
            ratings_df = calculate_player_ratings()
            st.markdown("#### 🏆 Ratings FM / FIFA & ESG Impact Scores (Senior A)")
            st.dataframe(ratings_df[["joueur", "esg_impact_score", "badge_tactique", "matchs_joues", "titularisations", "minutes_estimees", "buts", "clean_sheets_participees", "cartons_jaunes", "cartons_rouges"]], use_container_width=True)"""

new_tab_perf = """    with tab_perf:
        if selected_option == "SENIOR_M1":
            importlib.reload(player_rating)
            ratings_df = player_rating.calculate_player_ratings()
            st.markdown(f"#### 🏆 Ratings FM / FIFA & ESG Impact Scores • Effectif Senior A ({len(ratings_df)} Joueurs Officiels)")
            st.caption("Données certifiées feuilles de match officielles FFF (R3 Poule D & Coupe de France)")
            
            search_query = st.text_input("🔍 Rechercher un joueur (ex: Elio, Devernay, Herve...)", key="search_player")
            df_display = ratings_df.copy()
            if search_query:
                df_display = df_display[df_display["joueur"].str.contains(search_query.strip(), case=False, na=False)]
            
            st.dataframe(df_display[["joueur", "esg_impact_score", "badge_tactique", "matchs_joues", "titularisations", "minutes_estimees", "buts", "clean_sheets_participees", "cartons_jaunes", "cartons_rouges"]], use_container_width=True)"""

content = content.replace(old_tab_perf, new_tab_perf)

# 3. Add cartes profil joueurs download button in tab_docs
old_tab_docs = """        if selected_option == "SENIOR_M1":
            st.markdown("#### 📄 Téléchargement des Livrables Staff (Senior A)")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                b_pdf = os.path.join(OUTPUT_DIR, "briefing_match_latest.pdf")
                if os.path.exists(b_pdf):
                    with open(b_pdf, "rb") as f:
                        st.download_button("📥 Télécharger le Briefing PDF (Avant-Match)", f, file_name="briefing_es_genech.pdf", mime="application/pdf")
                b_png = os.path.join(OUTPUT_DIR, "briefing_match_latest.png")
                if os.path.exists(b_png):
                    st.image(b_png, caption="Aperçu du Briefing d'Avant-Match", width=380)

            with col_d2:
                d_pdf = os.path.join(OUTPUT_DIR, "debrief_match_latest.pdf")
                if os.path.exists(d_pdf):
                    with open(d_pdf, "rb") as f:
                        st.download_button("📥 Télécharger le Débrief 90' PDF (Post-Match)", f, file_name="debrief_postmatch_genech.pdf", mime="application/pdf")
                d_png = os.path.join(OUTPUT_DIR, "debrief_match_latest.png")
                if os.path.exists(d_png):
                    st.image(d_png, caption="Aperçu du Débrief Post-Match", width=380)"""

new_tab_docs = """        if selected_option == "SENIOR_M1":
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
                    st.image(c_png, caption="Aperçu Cartes FM / FIFA", use_container_width=True)"""

content = content.replace(old_tab_docs, new_tab_docs)

with open('C:/Users/ninof/.gemini/antigravity/scratch/genech_data_performance/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated app.py successfully!")
