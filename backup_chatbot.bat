@echo off
:: Corrige hora com espaço e formata data/hora para nome da pasta
set hour=%TIME:~0,2%
if "%hour:~0,1%"==" " set hour=0%hour:~1,1%
set min=%TIME:~3,2%
set sec=%TIME:~6,2%
set date=%DATE:~6,4%-%DATE:~3,2%-%DATE:~0,2%
set datetime=%date%_%hour%%min%%sec%

:: Caminho de destino do backup (ajustado para o C:)
set DESTINO=C:\BackupsSullato\Backup_ChatbotSullato_%datetime%

echo 🔄 Criando backup em: %DESTINO%...
xcopy "C:\Projetos\ChatbotSullato" "%DESTINO%" /E /I /Y
echo ✅ Backup finalizado com sucesso!
pause
