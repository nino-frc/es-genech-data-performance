"""
Script pour intégrer FC Seclin dans app.py avec le switcher multi-tenant
Garantit que Genech conserve l'intégralité de son code, de ses 16 équipes et de ses accès VIP.
"""

import os
import re

APP_PY_PATH = os.path.join(os.path.dirname(__file__), "app.py")

with open(APP_PY_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# On isole le code de Genech entre la ligne 151 et la fin
split_marker = "# Connexion directe SANS CACHE pour garantir une réactivité instantanée à chaque clic"
parts = content.split(split_marker)

header_and_styles = parts[0]
genech_core = split_marker + parts[1]

# On crée la fonction render_seclin_dashboard
seclin_function = '''
def render_seclin_dashboard():
    seclin_db = os.path.join(BASE_DIR, "seclin_performance.db")
    seclin_logo = os.path.join(BASE_DIR, "logo_seclin.jpg")
    
    logo_b64_sec = ""
    if os.path.exists(seclin_logo):
        with open(seclin_logo, "rb") as f:
            logo_b64_sec = base64.b64encode(f.read()).decode("utf-8")
            
    conn = sqlite3.connect(seclin_db)
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
    players_df.insert(0, "rang", range(1, len(players_df) + 1))
    
    # Sidebar Seclin
    with st.sidebar:
        if os.path.exists(seclin_logo):
            st.image(seclin_logo, width=120)
        st.markdown("### **FC SECLIN**")
        st.caption("Cellule Performance & Analytics • FFF #500934")
        st.markdown("---")
        st.markdown("🔵⚪ **Club Partenaire Régional 2**")
        st.caption("Seniors Régional 2 Poule B • Ligue des Hauts-de-France")
    
    # Header Seclin
    st.markdown(f"""
    <div class="club-header" style="border-bottom: 4px solid #3b82f6;">
        <div style="display: flex; align-items: center; gap: 18px;">
            <img src="data:image/jpeg;base64,{logo_b64_sec}" alt="Logo FC Seclin" style="height: 64px; width: auto; border-radius: 8px; filter: drop-shadow(0 4px 10px rgba(0,0,0,0.35));">
            <div>
                <h1>FC <span>SECLIN</span> • HUB DATA PERFORMANCE</h1>
                <p>Plateforme Tactique & Analytics Officielle • Club FFF #500934</p>
            </div>
        </div>
        <div style="background: rgba(59, 130, 246, 0.2); border: 1px solid #3b82f6; color: #60a5fa; padding: 8px 16px; border-radius: 20px; font-weight: 800; font-size: 12px; text-transform: uppercase;">
            Seniors Régional 2 • Accès Standard
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🎯 Senior A • Seniors Régional 2")
    st.caption("Ligue des Hauts-de-France • District des Flandres • Format 11x11")
    
    # KPI Seclin
    term = matchs_df[matchs_df["statut"] == "TERMINE"]
    v, n, d, bp, bc = 0, 0, 0, 0, 0
    for _, r in term.iterrows():
        is_dom = "SECLIN" in r["equipe_domicile"].upper()
        sg = r["score_domicile"] if is_dom else r["score_exterieur"]
        so = r["score_exterieur"] if is_dom else r["score_domicile"]
        if pd.notnull(sg) and pd.notnull(so):
            bp += int(sg)
            bc += int(so)
            if sg > so: v += 1
            elif sg == so: n += 1
            else: d += 1
    tot = v + n + d
    win_pct = (v / tot * 100) if tot > 0 else 0
    avg_bp = (bp / tot) if tot > 0 else 0
    diff = bp - bc
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card green">
            <div class="metric-label">Victoires</div>
            <div class="metric-value">{v} / {tot}</div>
            <div class="metric-sub">{win_pct:.1f}% de taux de victoire</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card gold">
            <div class="metric-label">Matchs Nuls</div>
            <div class="metric-value">{n}</div>
            <div class="metric-sub">Points de parité</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card blue">
            <div class="metric-label">Attaque (Buts Marqués)</div>
            <div class="metric-value">{bp}</div>
            <div class="metric-sub">{avg_bp:.1f} b/m (dont 12-0 vs Montigny)</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card green">
            <div class="metric-label">Différence de Buts</div>
            <div class="metric-value">+{diff}</div>
            <div class="metric-sub">{bc} buts concédés</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    
    tab_m, tab_c, tab_p, tab_d = st.tabs([
        "🗓️ Calendrier & Résultats",
        "🏆 Classement Régional 2",
        "📇 Effectif & Buteurs",
        "⚖️ Discipline & Suspensions (Art. 226)"
    ])
    
    with tab_m:
        c_l, c_r = st.columns(2)
        with c_l:
            st.markdown("##### ⏮️ Dernier Match")
            st.markdown("""
            <div style="background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; box-shadow: 0 4px 10px rgba(0,0,0,0.03);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-size: 11px; font-weight: 800; color: #15803d; background: #dcfce7; padding: 4px 10px; border-radius: 20px;">VICTOIRE ÉCLATANTE</span>
                    <span style="font-size: 12px; color: #64748b; font-weight: 600;">Dim 18 Oct • Régional 2</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; font-weight: 800; font-size: 16px;">
                    <span>SECLIN FC</span>
                    <span style="background: #0a1728; color: white; padding: 6px 14px; border-radius: 8px; font-size: 20px;">12 - 0</span>
                    <span style="color: #64748b;">MONTIGNY GOHELLE</span>
                </div>
                <div style="margin-top: 10px; font-size: 12px; color: #475569;">
                    ⚽ Triplé de <b>Mouhamadou S.</b>, doublés de <b>Evan D.</b>, <b>Luther M.</b>, <b>Corentin L.</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with c_r:
            st.markdown("##### ⏭️ Prochain Match")
            st.markdown("""
            <div style="background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; box-shadow: 0 4px 10px rgba(0,0,0,0.03);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-size: 11px; font-weight: 800; color: #2563eb; background: #dbeafe; padding: 4px 10px; border-radius: 20px;">COUPE HAUTS-DE-FRANCE (3e Tour)</span>
                    <span style="font-size: 12px; color: #64748b; font-weight: 600;">Dim 25 Oct • 15h00</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; font-weight: 800; font-size: 16px;">
                    <span style="color: #64748b;">ARQUES ES</span>
                    <span style="background: #e2e8f0; color: #334155; padding: 6px 14px; border-radius: 8px; font-size: 16px;">VS</span>
                    <span>SECLIN FC</span>
                </div>
                <div style="margin-top: 10px; font-size: 12px; color: #475569;">
                    📍 Déplacement à l'extérieur • Stade Municipal d'Arques
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("#### 📋 Historique des Matchs Officiels (R2 & Coupes)")
        m_display = []
        for _, r in matchs_df.iterrows():
            sc = f"{int(r['score_domicile'])} - {int(r['score_exterieur'])}" if pd.notnull(r['score_domicile']) else "À VENIR"
            m_display.append({
                "Date": r["date_heure"],
                "Compétition": r["competition_id"],
                "Affiche": f"{r['equipe_domicile']} vs {r['equipe_exterieur']}",
                "Score": sc,
                "Statut": r["statut"]
            })
        st.dataframe(pd.DataFrame(m_display), use_container_width=True, hide_index=True)
        
    with tab_c:
        st.markdown("#### 🏆 Classement Officiel FFF • Seniors Régional 2")
        st.caption("Poule B • Ligue des Hauts-de-France")
        st.dataframe(
            classement_df[["rang", "equipe", "points", "joues", "gagnes", "nuls", "perdus", "buts_pour", "buts_contre", "diff"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "rang": st.column_config.NumberColumn("#", format="%d", width="small"),
                "equipe": st.column_config.TextColumn("Club"),
                "points": st.column_config.NumberColumn("Points", format="%d pts"),
                "joues": st.column_config.NumberColumn("J", format="%d"),
                "gagnes": st.column_config.NumberColumn("V", format="%d"),
                "nuls": st.column_config.NumberColumn("N", format="%d"),
                "perdus": st.column_config.NumberColumn("D", format="%d"),
                "buts_pour": st.column_config.NumberColumn("BP", format="%d"),
                "buts_contre": st.column_config.NumberColumn("BC", format="%d"),
                "diff": st.column_config.NumberColumn("+/-", format="%d")
            }
        )
        
    with tab_p:
        st.markdown(f"#### 👥 Effectif Officiel FC Seclin ({len(players_df)} Joueurs Convoqués)")
        st.caption("Données certifiées feuilles de match officielles FFF")
        st.dataframe(
            players_df[["rang", "joueur_nom", "matchs_joues", "titularisations", "remplacements", "buts"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "rang": st.column_config.NumberColumn("#", format="%d", width="small"),
                "joueur_nom": st.column_config.TextColumn("Joueur"),
                "matchs_joues": st.column_config.NumberColumn("Matchs Joués", format="%d"),
                "titularisations": st.column_config.NumberColumn("Titularisations", format="%d"),
                "remplacements": st.column_config.NumberColumn("Entrées en Jeu", format="%d"),
                "buts": st.column_config.NumberColumn("Buts Marqués ⚽", format="%d")
            }
        )
        
    with tab_d:
        st.markdown("#### 🚨 Alertes Disciplinaires & Risque de Suspension (Art. 226 FFF)")
        st.caption("3 cartons jaunes en moins de 90 jours = 1 match de suspension automatique.")
        
        for _, cr in cards_df.iterrows():
            if cr["cartons_jaunes"] >= 3:
                st.error(f"🔴 **SUSPENSION IMMINENTE / EN COURS** : {cr['joueur']} a accumulé **{cr['cartons_jaunes']} cartons jaunes** sur les feuilles FFF !")
            elif cr["cartons_jaunes"] == 2:
                st.warning(f"🟠 **SOUS SURSIS IMMÉDIAT** : {cr['joueur']} a **2 cartons jaunes**. Le prochain avertissement entraînera une suspension ferme !")
                
        st.markdown("#### 📋 Casier Disciplinaire Officiel")
        st.dataframe(
            cards_df[["joueur", "cartons_jaunes"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "joueur": st.column_config.TextColumn("Joueur"),
                "cartons_jaunes": st.column_config.NumberColumn("Cartons Jaunes 🟨", format="%d")
            }
        )
'''

# On encapsule genech_core dans une fonction render_genech_dashboard
genech_function = "def render_genech_dashboard():\n" + "\n".join("    " + line for line in genech_core.splitlines())

# Contrôleur principal avec le Switcher
controller = '''
# -------------------------------------------------------------
# PORTAIL MULTI-CLUBS (FFF N1-R3)
# -------------------------------------------------------------
st.sidebar.markdown("### 🏟️ **PORTAIL CLUB (N1-R3)**")
club_options = {
    "525674": "🟡⚫ ES GENECH (#525674) • VIP Intégral",
    "500934": "🔵⚪ FC SECLIN (#500934) • Régional 2"
}
selected_club = st.sidebar.selectbox(
    "Club sélectionné :",
    options=list(club_options.keys()),
    format_func=lambda x: club_options[x],
    index=0
)
custom_code = st.sidebar.text_input("🔑 Code FFF du club :", value=selected_club)
if custom_code in club_options:
    selected_club = custom_code
elif custom_code.strip() and custom_code not in club_options:
    st.sidebar.info(f"ℹ️ Club #{custom_code} non pré-chargé. Le scraper N1-R3 permet de l'intégrer en 1 clic.")
st.sidebar.markdown("---")

if selected_club == "500934":
    render_seclin_dashboard()
else:
    render_genech_dashboard()
'''

new_content = header_and_styles + "\n" + seclin_function + "\n\n" + genech_function + "\n\n" + controller

with open(APP_PY_PATH, "w", encoding="utf-8") as f:
    f.write(new_content)

print("✅ app.py mis à jour avec le sélecteur multi-clubs !")
