import os

APP_PY_PATH = os.path.join(os.path.dirname(__file__), "app.py")

with open(APP_PY_PATH, "r", encoding="utf-8") as f:
    code = f.read()

target = """saas_logo_b64 = ""
if os.path.exists(SAAS_LOGO_PATH):
    with open(SAAS_LOGO_PATH, "rb") as f:
        saas_logo_b64 = base64.b64encode(f.read()).decode("utf-8")"""

replacement = """saas_logo_b64 = ""
if os.path.exists(SAAS_LOGO_PATH):
    with open(SAAS_LOGO_PATH, "rb") as f:
        saas_logo_b64 = base64.b64encode(f.read()).decode("utf-8")

# -------------------------------------------------------------
# ÉCRAN DE CHARGEMENT SPLASH SCREEN MATCHDAY (Look PWA Mobile)
# -------------------------------------------------------------
if saas_logo_b64 and "splash_shown" not in st.session_state:
    st.session_state["splash_shown"] = True
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
            animation: splashFadeOut 0.6s cubic-bezier(0.4, 0, 0.2, 1) 2.0s forwards !important;
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
            width: 125px !important;
            height: 125px !important;
            border-radius: 28px !important;
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

        .splash-title span {{
            color: #22c55e !important;
        }}

        .splash-sub {{
            font-size: 12px !important;
            font-weight: 800 !important;
            color: #94a3b8 !important;
            letter-spacing: 4.5px !important;
            margin-top: 5px !important;
            text-transform: uppercase !important;
        }}

        .splash-loader {{
            width: 150px !important;
            height: 4px !important;
            background: rgba(255, 255, 255, 0.12) !important;
            border-radius: 4px !important;
            margin-top: 26px !important;
            overflow: hidden !important;
        }}

        .splash-progress {{
            height: 100% !important;
            background: linear-gradient(90deg, #16a34a, #22c55e, #4ade80) !important;
            border-radius: 4px !important;
            animation: progressBar 1.5s cubic-bezier(0.65, 0, 0.35, 1) forwards !important;
        }}

        @keyframes progressBar {{
            0% {{ width: 0%; }}
            100% {{ width: 100%; }}
        }}
    </style>
    \"\"\", unsafe_allow_html=True)"""

assert target in code, "Target not found in app.py"
code = code.replace(target, replacement)

with open(APP_PY_PATH, "w", encoding="utf-8") as f:
    f.write(code)

print("Splash Screen injecté avec succès dans app.py !")
