@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
start "" cmd /k "ngrok start --all"
python webhook.py
