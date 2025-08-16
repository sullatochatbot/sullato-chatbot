@echo off
setlocal enabledelayedexpansion

REM === CONFIG ===
set REPO_DIR=C:\Projetos\ChatbotSullato
set BRANCH=main
REM Coloque o ID/URL exato do seu serviço no Render (vi no print: srv-d1u5kgc9c44c73cl8bc0)
set RENDER_EVENTS_URL=https://dashboard.render.com/web/srv-d1u5kgc9c44c73cl8bc0/events

REM === GO ===
cd /d "%REPO_DIR%" || (echo ❌ Nao foi possivel acessar %REPO_DIR% & pause & exit /b 1)

echo.
echo 🔄 Atualizando repo...
git fetch origin
git checkout %BRANCH% || (echo ❌ Branch %BRANCH% nao existe & pause & exit /b 1)
git pull --rebase origin %BRANCH%

echo.
echo ➕ Adicionando changes...
git add .

REM Se nao houver alteracao, nao comita
git diff --cached --quiet && (
  echo 🟡 Nao ha alteracoes para commit.
) || (
  for /f "tokens=1-3 delims=/ " %%a in ("%date%") do set DATA=%%a-%%b-%%c
  for /f "tokens=1-2 delims=:." %%a in ("%time%") do set HORA=%%a-%%b
  git commit -m "Deploy: ajustes (%DATA% %HORA%)"
)

echo.
echo ⬆️ Enviando para origin/%BRANCH%...
git push origin %BRANCH% || (echo ❌ Falha no push & pause & exit /b 1)

echo.
echo ✅ Push feito. Abrindo pagina do Render para acionar o Manual Deploy...
start "" "%RENDER_EVENTS_URL%"

echo ----------------------------------
echo Se a pagina abrir, clique em: Manual Deploy -> Deploy latest commit
echo (Se nao aparecer o commit novo: Settings -> Clear build cache & deploy)
echo ----------------------------------
pause
