import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Caminho para o seu arquivo JSON de credenciais
CAMINHO_CREDENCIAL = "virtual-silo-406112-250b56a16195.json"

# ID da planilha (copiado da URL do Google Sheets)
PLANILHA_ID = "1Xke33HzOXW78CjX7sVm9O0RZmw7dvUN2YzjBXcVQ0II"

def salvar_em_planilha_google(numero, nome, interesse=""):
    try:
        escopo = ["https://www.googleapis.com/auth/spreadsheets"]
        credenciais = Credentials.from_service_account_file(CAMINHO_CREDENCIAL, scopes=escopo)
        cliente = gspread.authorize(credenciais)

        planilha = cliente.open_by_key(PLANILHA_ID)
        aba = planilha.sheet1

        data = datetime.now().strftime("%d/%m/%Y")

        aba.append_row([numero, nome, interesse, data])
        print(f"✅ Contato salvo no Google Sheets: {numero}, {nome}, {interesse}, {data}")

    except Exception as e:
        print(f"❌ Erro ao salvar no Google Sheets: {e}")
        
if __name__ == "__main__":
    salvar_em_planilha_google("5511940123456", "Anderson", "Teste via Google Sheets")
