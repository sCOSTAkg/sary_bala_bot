@echo off
echo ==========================================
echo       SARY BALA BOT - GITHUB DEPLOY
echo ==========================================
echo.
echo 1. Autentification on GitHub...
"C:\Program Files\GitHub CLI\gh.exe" auth login --web --git-protocol https --hostname github.com

echo.
echo 2. Creating Repository...
"C:\Program Files\GitHub CLI\gh.exe" repo create sary_bala_bot --public --source=. --remote=origin

echo.
echo 3. Pushing Code...
git push -u origin main

echo.
echo ==========================================
echo             DEPLOY COMPLETE!
echo ==========================================
pause
