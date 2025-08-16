import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta
import traceback
import os
from dotenv import load_dotenv

# ===== Fuso SP robusto =====
def _agora_sp_factory():
    try:
        from zoneinfo import ZoneInfo  # type: ignore
        try:
            tz = ZoneInfo("America/Sao_Paulo")
            return lambda: datetime.now(tz)
        except Exception:
            pass
        try:
            import tzdata  # noqa: F401
            tz = ZoneInfo("America/Sao_Paulo")
            return lambda: datetime.now(tz)
        except Exception:
            pass
    except Exception:
        pass
    tz_fallback = timezone(timedelta(hours=-3))
    return lambda: datetime.now(tz_fallback)

agora_sp = _agora_sp_factory()

# 🔁 Carregar variáveis do .env
load_dotenv()

# Fallbacks de nome de variável para o caminho das credenciais
CAMINHO_CREDENCIAL = (
    os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")
    or os.getenv("GOOGLE_SHEETS_CREDENCIALS_PATH")
    or os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    or os.getenv("GOOGLE_SHEETS_JSON")
)

SHEET_ID = '1Xke33HzOXW78CjX7sVm9O0RZmw7dvUN2YzjBXcVQ0II'
NOME_ABA = 'Página1'

def salvar_em_google_sheets(numero, nome, interesse='-', data=None):
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
    except Exception:
        print("❌ Erro ao salvar no Google Sheets:")
        traceback.print_exc()
