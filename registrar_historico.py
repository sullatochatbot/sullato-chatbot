# registrar_historico.py — versão blindada (não derruba o bot)
import os
import json
import traceback
from datetime import datetime, timezone, timedelta

import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# ---------- Fuso SP robusto ----------
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

# ---------- ENV ----------
load_dotenv()

# Aceita vários nomes de variável e JSON inline:
RAW_CRED = (
    os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")
    or os.getenv("GOOGLE_SHEETS_CREDENCIALS_PATH")
    or os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    or os.getenv("GOOGLE_SHEETS_JSON")
    or ""
)

SHEET_ID = "1Xke33HzOXW78CjX7sVm9O0RZmw7dvUN2YzjBXcVQ0II"
NOME_ABA_HISTORICO = "Historico"

def _carregar_credenciais():
    """
    Retorna um objeto Credentials ou None.
    - Se RAW_CRED apontar para um arquivo existente → from_service_account_file
    - Se RAW_CRED for um JSON inline → from_service_account_info
    - Senão → None
    """
    try:
        if not RAW_CRED:
            print("⚠️ Credenciais não configuradas (variável ausente).")
            return None

        # Caminho de arquivo?
        if os.path.exists(RAW_CRED):
            SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
            return Credentials.from_service_account_file(RAW_CRED, scopes=SCOPES)

        # JSON inline?
        if RAW_CRED.strip().startswith("{"):
            info = json.loads(RAW_CRED)
            SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
            return Credentials.from_service_account_info(info, scopes=SCOPES)

        print("⚠️ Credenciais inválidas: nem caminho de arquivo, nem JSON.")
        return None
    except Exception:
        print("❌ Falha ao carregar credenciais:")
        traceback.print_exc()
        return None

def _abrir_planilha(creds):
    try:
        client = gspread.authorize(creds)
        return client.open_by_key(SHEET_ID)
    except Exception:
        print("❌ Erro ao autorizar/abrir planilha:")
        traceback.print_exc()
        return None

def _obter_aba(planilha):
    try:
        try:
            return planilha.worksheet(NOME_ABA_HISTORICO)
        except gspread.exceptions.WorksheetNotFound:
            aba = planilha.add_worksheet(title=NOME_ABA_HISTORICO, rows=1000, cols=5)
            aba.append_row(["Número", "Nome", "Interesse", "Data/Hora"], value_input_option="USER_ENTERED")
            return aba
    except Exception:
        print("❌ Erro ao acessar/criar a aba:")
        traceback.print_exc()
        return None

def registrar_interacao(numero, nome, interesse="-", datahora=None):
    """
    Totalmente segura: se algo falhar, apenas loga e retorna.
    Timestamp vai como TEXTO (com apóstrofo) para evitar +3h de timezone.
    """
    try:
        # 1) Timestamp local SP como TEXTO (literal), evita reinterpretação do Sheets
        if datahora is None:
            datahora = "'" + agora_sp().strftime("%d/%m/%Y %H:%M:%S")

        # 2) Carrega credenciais (se não houver, sai sem erro)
        creds = _carregar_credenciais()
        if not creds:
            print("⚠️ registrar_interacao: sem credenciais → pulando registro.")
            return

        # 3) Abre planilha e aba (se falhar, sai sem erro)
        planilha = _abrir_planilha(creds)
        if not planilha:
            print("⚠️ registrar_interacao: não foi possível abrir a planilha.")
            return

        aba = _obter_aba(planilha)
        if not aba:
            print("⚠️ registrar_interacao: não foi possível obter/ criar a aba.")
            return

        # 4) Grava linha (USER_ENTERED aceita o apóstrofo e mantém literal)
        aba.append_row([numero, nome, interesse, datahora], value_input_option="USER_ENTERED")
        print(f"📌 Interação registrada: {numero}, {nome}, {interesse}, {datahora}")

    except Exception:
        # Nunca derrubar o bot por causa do histórico
        print("❌ registrar_interacao: erro inesperado (ignorando para não derrubar o bot).")
        traceback.print_exc()
        return
