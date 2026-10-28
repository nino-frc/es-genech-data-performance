@echo off
chcp 65001 > nul
echo ========================================================
echo   SYNCHRONISATION DU REGISTRE DES APPAREILS MATCHDAY
echo ========================================================
echo.
echo Connexion au serveur cloud et verification des nouveaux appareils...
python sync_devices_to_excel.py
echo.
echo Le fichier registre_appareils_connectes.xlsx est a jour !
echo ========================================================
pause
