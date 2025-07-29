import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

CAMINHO_CREDENCIAL = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")
SHEET_ID = '1Xke33HzOXW78CjX7sVm9OORZmw7dvUN2YzjBXcVQ0II'
NOME_ABA = 'Página1'

def atualizar_interesse_google_sheets(numero, novo_interesse):
    try:
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(CAMINHO_CREDENCIAL, scopes=SCOPES)
        client = gspread.authorize(creds)
        planilha = client.open_by_key(SHEET_ID)
        aba = planilha.worksheet(NOME_ABA)

        col_numeros = aba.col_values(1)

        for idx, num in enumerate(col_numeros[1:], start=2):  # pula o cabeçalho
            if num.strip() == numero:
                aba.update_cell(idx, 3, novo_interesse)  # coluna 3 = interesse
                print(f"✏️ Interesse atualizado no Google Sheets: {numero} -> {novo_interesse}")
                return
        print(f"⚠️ Número não encontrado na planilha: {numero}")

    except Exception as e:
        print("❌ Erro ao atualizar interesse no Google Sheets:", e)
