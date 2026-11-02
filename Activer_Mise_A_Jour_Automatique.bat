@echo off
chcp 65001 > nul
title MatchDay - Activation Automatisation Windows

echo ======================================================================
echo   ⚙️ MATCHDAY ANALYTICS - ACTIVATION PLANIFICATEUR DE TACHES
echo ======================================================================
echo.
echo Ce script configure l'execution 100%% automatique des mises a jour :
echo   - Chaque LUNDI a 08h00 : Debrief J+1, scores du dimanche, classements & stats
echo   - Chaque JEUDI a 08h00 : Designations CRA arbitres & briefing match du week-end
echo.
echo Configuration dans le Planificateur Windows en cours...

schtasks /create /tn "MatchDay_Synchronisation_Automatique" /tr "\"%~dp0Mettre_a_jour_MatchDay.bat\"" /sc weekly /d MON,THU /st 08:00 /f

if %ERRORLEVEL% equ 0 (
  echo.
  echo ======================================================================
  echo   ✅ AUTOMATISATION ACTIVEE AVEC SUCCES !
  echo   La tache planifiee s'executera automatiquement chaque lundi et jeudi.
  echo   Vos donnees seront toujours a jour sans aucune action de votre part.
  echo ======================================================================
) else (
  echo.
  echo ❌ Erreur lors de la creation de la tache planifiee.
)
echo.
pause
