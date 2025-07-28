@echo off
cd /d "C:\Users\Anderson\Documents\chatbotSullato"
echo Salvando e enviando para o GitHub...

set hour=%time:~0,2%
if "%hour:~0,1%"==" " set hour=0%hour:~1,1%
set timestamp=%date:/=-%_%hour%-%time:~3,2%

git add .
git commit -m "Deploy automático em %timestamp%"
git push origin main

echo Deploy enviado com sucesso!
pause
