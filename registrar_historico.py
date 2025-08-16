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

# Carregar .env
load_dotenv()

# Fallbacks de nome de variável para o caminho das credenciais
CAMINHO_CREDENCIAL = (
    os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")
    or os.getenv("GOOGLE_SHEETS_CREDENCIALS_PATH")
    or os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    or os.getenv("GOOGLE_SHEETS_JSON")
)

SHEET_ID = '1Xke33HzOXW78CjX7sVm9O0RZmw7dvUN2YzjBXcVQ0II'
NOME_ABA_HISTORICO = 'Historico'

def _configurar_planilha(planilha: gspread.Spreadsheet, aba: gspread.Worksheet):
    """Garante timezone do arquivo e formato da coluna D (Data/Hora)."""
    try:
        # 1) Ajusta timezone do arquivo
        planilha.batch_update({
            "requests": [{
                "updateSpreadsheetProperties": {
                    "properties": {"timeZone": "America/Sao_Paulo"},
                    "fields": "timeZone"
                }
            }]
        })
        # 2) Aplica formato dd/MM/yyyy HH:mm:ss na coluna D
        sheet_id = aba._properties.get("sheetId")
        if sheet_id is not None:
            planilha.batch_update({
                "requests": [{
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startColumnIndex": 3,  # D (0=A)
                            "endColumnIndex": 4
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "numberFormat": {
                                    "type": "DATE_TIME",
                                    "pattern": "dd/MM/yyyy HH:mm:ss"
                                }
                            }
                        },
                        "fields": "userEnteredFormat.numberFormat"
                    }
                }]
            })
    except Exception:
        traceback.print_exc()  # Não derruba o fluxo

def registrar_interacao(numero, nome, interesse='-', datahora=None):
    try:
        if datahora is None:
            datahora = agora_sp().strftime('%d/%m/%Y %H:%M:%S')

        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(CAMINHO_CREDENCIAL, scopes=SCOPES)
        client = gspread.authorize(creds)
        planilha = client.open_by_key(SHEET_ID)

        try:
            aba = planilha.worksheet(NOME_ABA_HISTORICO)
        except gspread.exceptions.WorksheetNotFound:
            aba = planilha.add_worksheet(title=NOME_ABA_HISTORICO, rows=1000, cols=5)
            aba.append_row(["Número", "Nome", "Interesse", "Data/Hora"], value_input_option="USER_ENTERED")

        # Garante timezone e formato antes de gravar
        _configurar_planilha(planilha, aba)

        # Grava a linha
        aba.append_row([numero, nome, interesse, datahora], value_input_option="USER_ENTERED")
        print(f"📌 Interação registrada: {numero}, {nome}, {interesse}, {datahora}")
    except Exception:
        print("❌ Erro ao registrar histórico no Google Sheets:")
        traceback.print_exc()
