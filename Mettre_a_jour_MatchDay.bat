@echo off
chcp 65001 > nul
title MatchDay - Mise a jour automatique des donnees
cd /d "%~dp0"

echo ======================================================================
echo   ⚡ MATCHDAY ANALYTICS - SYNCHRONISATION MULTI-CLUBS EN DIRECT
echo ======================================================================
echo.
echo [1/4] Scraping FFF ES Genech (Seniors R3, D2, Fem, U18)...
python scraper.py
echo.
echo [2/4] Scraping FFF FC Seclin (Regional 2)...
python scrape_seclin_r2.py
echo.
echo [3/4] Scraping FFF US Lesquin (Regional 2)...
python scrape_lesquin_r2.py
echo.
echo [4/4] Regeneration des flux PWA et calculs disciplinaires...
python export_pwa_feed.py
echo.
echo 🚀 Deploiement automatique sur Vercel...
git add genech_performance.db seclin_performance.db lesquin_performance.db public/data.js public/data_feed.json public/app.js public/index.html exports_powerbi/ briefings_coach/
git diff-index --quiet HEAD || (
  git commit -m "chore(auto): mise a jour hebdomadaire officielle FFF [skip ci]"
  git push origin main
)
echo.
echo ======================================================================
echo   ✅ SYNCHRONISATION TERMINEE AVEC SUCCES !
echo   L'application est en direct sur : https://matchday-performance.vercel.app/
echo ======================================================================
timeout /t 8
