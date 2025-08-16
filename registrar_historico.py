import os
import traceback
from datetime import datetime, timezone, timedelta

import gspread
from google.oauth2.service_account import Credentials

# ====== Horário SP (com fallback, sem depender do sistema) ======
def _agora_sp():
    try:
        from zoneinfo import ZoneInfo  # Python 3.9+
        return datetime.now(ZoneInfo("America/Sao_Paulo"))
    except Exception:
        # Fallback UTC-3 fixo (serve para exibir certo no Brasil)
        return datetime.now(timezone(timedelta(hours=-3)))

# ====== CONFIG - usa exatamente as VARS que estão no Render ======
# (conforme seu print: SHEETS_CREDENTIALS_PATH=credenciais_sheets.json)
SHEETS_CREDENTIALS_PATH = os.getenv("SHEETS_CREDENTIALS_PATH", "credenciais_sheets.json")
SHEET_ID = os.getenv("PLANILHA_ID", "1Xke33HzOXW78CjX7sVm9O0RZmw7dvUN2YzjBXcVQ0II")
ABA = os.getenv("SHEET_TAB_HISTORICO", "Historico")

def _carregar_client():
    """Carrega credenciais sem derrubar o bot se faltar arquivo."""
    try:
        if not os.path.exists(SHEETS_CREDENTIALS_PATH):
            print(f"⚠️ Credencial não encontrada: {SHEETS_CREDENTIALS_PATH}")
            return None
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(SHEETS_CREDENTIALS_PATH, scopes=scopes)
        return gspread.authorize(creds)
    except Exception:
        print("❌ Falha ao carregar credenciais/autorizar:")
        traceback.print_exc()
        return None

def registrar_interacao(numero: str, nome: str, interesse: str = "-", datahora: str | None = None):
    """
    Escreve uma linha em Historico. À prova de falhas:
    - Se o Google falhar, NÃO derruba o fluxo do bot.
    - Grava a hora local de Brasília como TEXTO (com apóstrofo) para evitar +3h.
    Colunas: [Número, Nome, Interesse, Data/Hora]
    """
    try:
        if datahora is None:
            # TEXTO literal para o Sheets não reinterpretar fuso
            datahora = "'" + _agora_sp().strftime("%d/%m/%Y %H:%M:%S")

        client = _carregar_client()
        if not client:
            print("⚠️ registrar_interacao: sem client; pulando gravação.")
            return

        sh = client.open_by_key(SHEET_ID)
        try:
            ws = sh.worksheet(ABA)
        except gspread.exceptions.WorksheetNotFound:
            ws = sh.add_worksheet(title=ABA, rows=1000, cols=4)
            ws.append_row(["Número", "Nome", "Interesse", "Data/Hora"], value_input_option="USER_ENTERED")

        ws.append_row([numero, nome, interesse, datahora], value_input_option="USER_ENTERED")
        print(f"📌 Histórico ok: {numero}, {nome}, {interesse}, {datahora}")
    except Exception:
        print("❌ registrar_interacao: erro (ignorado para não derrubar o bot):")
        traceback.print_exc()
