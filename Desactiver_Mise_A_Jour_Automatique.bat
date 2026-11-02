@echo off
chcp 65001 > nul
title MatchDay - Desactivation Automatisation Windows

echo Desactivation de la tache planifiee MatchDay...
schtasks /delete /tn "MatchDay_Synchronisation_Automatique" /f

if %ERRORLEVEL% equ 0 (
  echo.
  echo ✅ Automatisation desactivee avec succes.
) else (
  echo.
  echo ℹ️ Aucune tache active a supprimer.
)
echo.
pause
