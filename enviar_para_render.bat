@echo off
cd /d C:\Projetos\ChatbotSullato
echo Enviando responder.py para o Render...
git add .
git commit -m "feat: atualização automática do responder.py"
git push origin main
echo ----------------------------------
echo Código enviado com sucesso!
pause
