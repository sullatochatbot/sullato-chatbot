import os
import shutil
import zipfile
from datetime import datetime

# Nome do arquivo de backup
agora = datetime.now().strftime("ChatbotSullato_Backup_%Y-%m-%d_%H-%M")
backup_zip = os.path.join("C:/Backups_Chatbot", f"{agora}.zip")
exclusoes = {".env", "credenciais_sheets.json"}

# Criar pasta temporária
temp_dir = "temp_backup"
if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir)
os.makedirs(temp_dir)

# Copiar arquivos (exceto os sensíveis)
for root, dirs, files in os.walk("."):
    if root.startswith("./temp_backup") or ".git" in root:
        continue
    for file in files:
        if file in exclusoes or file.endswith(".zip"):
            continue
        origem = os.path.join(root, file)
        destino = os.path.join(temp_dir, os.path.relpath(origem, "."))
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        shutil.copy2(origem, destino)

# Compactar
with zipfile.ZipFile(backup_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
    for folder, _, files in os.walk(temp_dir):
        for file in files:
            path = os.path.join(folder, file)
            zipf.write(path, os.path.relpath(path, temp_dir))

# Limpar temporários
shutil.rmtree(temp_dir)

print(f"✅ Backup criado com sucesso: {backup_zip}")
