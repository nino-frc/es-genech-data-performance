"""
Intégration de l'identité de marque MatchDay et de l'écran de chargement Splash Screen dans app.py
"""

import os
import re

APP_PY_PATH = os.path.join(os.path.dirname(__file__), "app.py")

with open(APP_PY_PATH, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Config et Logo SaaS
old_config = """st.set_page_config(
    page_title="ES Genech • Hub Performance",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "genech_performance.db")
LOGO_PATH = os.path.join(BASE_DIR, "logo_genech_transparent.png")
OUTPUT_DIR = os.path.join(BASE_DIR, "briefings_coach")"""

new_config = """BASE_DIR = os.path.dirname(__file__)
SAAS_LOGO_PATH = os.path.join(BASE_DIR, "logo_app_saas.png")
DB_PATH = os.path.join(BASE_DIR, "genech_performance.db")
LOGO_PATH = os.path.join(BASE_DIR, "logo_genech_transparent.png")
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
        saas_logo_b64 = base64.b64encode(f.read()).decode("utf-8")"""

assert old_config in code, "old_config not found"
code = code.replace(old_config, new_config)

# 2. Ajout du CSS Splash Screen et de la balise HTML Splash Screen
splash_css = """
    /* ÉCRAN DE CHARGEMENT SPLASH SCREEN MATCHDAY */
    #matchday-splash {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: #070d17;
        z-index: 9999999;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        animation: splashFadeOut 0.5s cubic-bezier(0.4, 0, 0.2, 1) 1.2s forwards;
        pointer-events: none;
    }

    @keyframes splashFadeOut {
        0% { opacity: 1; visibility: visible; }
        99% { opacity: 0; visibility: visible; }
        100% { opacity: 0; visibility: hidden; display: none; }
    }

    .splash-box {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
    }

    .splash-logo {
        width: 105px;
        height: 105px;
        border-radius: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        animation: splashPulse 1.8s infinite ease-in-out;
    }

    @keyframes splashPulse {
        0%, 100% { transform: scale(1); filter: drop-shadow(0 0 20px rgba(34, 197, 94, 0.35)); }
        50% { transform: scale(1.05); filter: drop-shadow(0 0 35px rgba(34, 197, 94, 0.7)); }
    }

    .splash-title {
        font-family: 'Oswald', sans-serif !important;
        font-size: 34px !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        letter-spacing: 2px !important;
        margin-top: 18px !important;
        text-transform: uppercase !important;
    }

    .splash-title span {
        color: #22c55e !important;
    }

    .splash-sub {
        font-size: 11px !important;
        font-weight: 700 !important;
        color: #94a3b8 !important;
        letter-spacing: 3.5px !important;
        margin-top: 4px !important;
        text-transform: uppercase !important;
    }

    .splash-loader {
        width: 130px;
        height: 3px;
        background: rgba(255, 255, 255, 0.12);
        border-radius: 4px;
        margin-top: 22px;
        overflow: hidden;
    }

    .splash-progress {
        height: 100%;
        background: linear-gradient(90deg, #16a34a, #22c55e, #4ade80);
        border-radius: 4px;
        animation: progressBar 1.1s cubic-bezier(0.65, 0, 0.35, 1) forwards;
    }

    @keyframes progressBar {
        0% { width: 0%; }
        100% { width: 100%; }
    }
</style>
"""

code = code.replace("</style>\n\"\"\", unsafe_allow_html=True)", splash_css + "\"\"\", unsafe_allow_html=True)")

# Injection du HTML Splash Screen juste après le CSS
splash_html_injection = """
# Rendu du Splash Screen de chargement MatchDay
if saas_logo_b64:
    st.markdown(f\"\"\"
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
    \"\"\", unsafe_allow_html=True)
"""

code = code.replace('unsafe_allow_html=True)\n\ndef render_seclin_dashboard():', 'unsafe_allow_html=True)\n' + splash_html_injection + '\ndef render_seclin_dashboard():')

# 3. Branding MatchDay au sommet de la Sidebar
old_sidebar_portal = """# -------------------------------------------------------------
# PORTAIL MULTI-CLUBS (FFF N1-R3)
# -------------------------------------------------------------
st.sidebar.markdown("### 🏟️ **PORTAIL CLUB (N1-R3)**")"""

new_sidebar_portal = """# -------------------------------------------------------------
# BRANDING MATCHDAY & PORTAIL MULTI-CLUBS
# -------------------------------------------------------------
with st.sidebar:
    if saas_logo_b64:
        st.markdown(f\"\"\"
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px; padding-bottom: 14px; border-bottom: 1px solid #e2e8f0;">
            <img src="data:image/png;base64,{saas_logo_b64}" style="width: 44px; height: 44px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
            <div>
                <div style="font-family: 'Oswald', sans-serif; font-size: 22px; font-weight: 700; color: #0a1728; line-height: 1.1; letter-spacing: 0.5px;">MATCH<span style="color: #22c55e;">DAY</span></div>
                <div style="font-size: 10px; font-weight: 800; color: #64748b; letter-spacing: 1px; text-transform: uppercase;">Football Analytics</div>
            </div>
        </div>
        \"\"\", unsafe_allow_html=True)
    st.markdown("### 🏟️ **PORTAIL CLUB (N1-R3)**")"""

assert old_sidebar_portal in code, "old_sidebar_portal not found"
code = code.replace(old_sidebar_portal, new_sidebar_portal)

with open(APP_PY_PATH, "w", encoding="utf-8") as f:
    f.write(code)

print("MatchDay branding et Splash Screen intégrés dans app.py avec succès !")
