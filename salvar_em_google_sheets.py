import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import traceback
import os
from dotenv import load_dotenv
from zoneinfo import ZoneInfo  # ⬅ fuso horário

# 🔁 Carregar variáveis do .env
load_dotenv()

# ✅ Padronize para a MESMA variável usada no registrar_historico.py
CAMINHO_CREDENCIAL = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")
SHEET_ID = '1Xke33HzOXW78CjX7sVm9O0RZmw7dvUN2YzjBXcVQ0II'
NOME_ABA = 'Página1'

# Fuso de São Paulo
TZ_SP = ZoneInfo("America/Sao_Paulo")
def agora_sp():
    return datetime.now(TZ_SP)

def salvar_em_google_sheets(numero, nome, interesse='-', data=None):
    # Mantém apenas a data (como já era), mas gerada no fuso de SP
    if data is None:
        data = agora_sp().strftime('%d/%m/%Y')

    try:
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(CAMINHO_CREDENCIAL, scopes=SCOPES)
        client = gspread.authorize(creds)
        planilha = client.open_by_key(SHEET_ID)
        aba = planilha.worksheet(NOME_ABA)

        numeros_existentes = [n.strip() for n in aba.col_values(1)]
        if numero.strip() in numeros_existentes:
            print("📌 Número já registrado.")
            return

        print(f"🟡 Tentando gravar: {numero}, {nome}, {interesse}, {data}")
        aba.append_row([numero, nome, interesse, data], value_input_option="USER_ENTERED")
        print("✅ Contato salvo com sucesso no Google Sheets.")
    except Exception as e:
        print("❌ Erro ao salvar no Google Sheets:")
        traceback.print_exc()
