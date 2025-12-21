@echo off
echo ==========================================
echo       SARY BALA BOT - RAILWAY DEPLOY
echo ==========================================
echo.
echo 1. Logging into Railway (Check your browser!)...
railway login

echo.
echo 2. Deploying to Cloud...
railway up --detach

echo.
echo ==========================================
echo             DEPLOY STARTED!
echo ==========================================
pause
