@echo off
cd /d "%~dp0"

:: Ativar ambiente virtual
call venv\Scripts\activate.bat

:: Iniciar webhook (terminal principal)
start "webhook" cmd /k "python webhook.py"

:: Iniciar ngrok com subdomínio fixo
start "ngrok" cmd /k "ngrok http 5000 --domain=sullatochatbot.sa.ngrok.io"
