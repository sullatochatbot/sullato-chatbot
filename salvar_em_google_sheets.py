import os
import traceback
from datetime import datetime, timezone, timedelta

import gspread
from google.oauth2.service_account import Credentials

# ====== Horário SP (com fallback) ======
def _agora_sp():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/Sao_Paulo"))
    except Exception:
        return datetime.now(timezone(timedelta(hours=-3)))

# ====== CONFIG - mesmas VARS do Render ======
SHEETS_CREDENTIALS_PATH = os.getenv("SHEETS_CREDENTIALS_PATH", "credenciais_sheets.json")
SHEET_ID = os.getenv("PLANILHA_ID", "1Xke33HzOXW78CjX7sVm9O0RZmw7dvUN2YzjBXcVQ0II")
ABA = os.getenv("SHEET_TAB_PAGINA1", "Página1")

def _carregar_client():
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

def salvar_em_google_sheets(numero: str, nome: str, interesse: str = "-", data: str | None = None):
    """
    Registra o contato na aba Página1. À prova de falhas:
    - Se já existir o número, não duplica.
    - Se algo falhar, apenas loga e segue (não quebra o bot).
    Colunas: [Número, Nome, Interesse, Data]
    """
    try:
        if data is None:
            data = _agora_sp().strftime("%d/%m/%Y")  # só data

        client = _carregar_client()
        if not client:
            print("⚠️ salvar_em_google_sheets: sem client; pulando gravação.")
            return

        sh = client.open_by_key(SHEET_ID)
        try:
            ws = sh.worksheet(ABA)
        except gspread.exceptions.WorksheetNotFound:
            ws = sh.add_worksheet(title=ABA, rows=1000, cols=4)
            ws.append_row(["numero", "nome", "interesse", "data"], value_input_option="USER_ENTERED")

        # evita duplicado por número
        numeros = [n.strip() for n in ws.col_values(1)]
        if numero.strip() in numeros:
            print("📎 Número já existente na Página1.")
            return

        ws.append_row([numero, nome, interesse, data], value_input_option="USER_ENTERED")
        print(f"✅ Página1 ok: {numero}, {nome}, {interesse}, {data}")
    except Exception:
        print("❌ salvar_em_google_sheets: erro (ignorado):")
        traceback.print_exc()

def atualizar_interesse_google_sheets(numero: str, interesse: str):
    """
    Atualiza a coluna 'interesse' (coluna 3) da Página1, se o número existir.
    """
    try:
        client = _carregar_client()
        if not client:
            print("⚠️ atualizar_interesse: sem client; pulando.")
            return

        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet(ABA)

        cel = ws.find(numero)
        if cel:
            ws.update_cell(cel.row, 3, interesse)
            print(f"✏️ Interesse atualizado para {numero}: {interesse}")
        else:
            print("ℹ️ Número não encontrado para update de interesse.")
    except Exception:
        print("❌ atualizar_interesse_google_sheets: erro (ignorado):")
        traceback.print_exc()
