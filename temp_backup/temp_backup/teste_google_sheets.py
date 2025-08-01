import gspread
from google.oauth2.service_account import Credentials

CAMINHO_CREDENCIAL = 'credenciais_sheets.json'
SHEET_ID = '1Xke33HzOXW78CjX7sVm9O0RZmw7dvUN2YzjBXcVQ0II'
NOME_ABA = 'Página1'

try:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(CAMINHO_CREDENCIAL, scopes=SCOPES)
    client = gspread.authorize(creds)
    
    print("✅ Autenticação feita com sucesso.")
    
    planilha = client.open_by_key(SHEET_ID)
    print("✅ Planilha aberta com sucesso.")

    aba = planilha.worksheet(NOME_ABA)
    print("✅ Aba acessada com sucesso:", aba.title)

    aba.append_row(['teste_numero', 'teste_nome', 'teste_interesse', '28/07/2025'], value_input_option="USER_ENTERED")
    print("✅ Linha adicionada com sucesso.")

except Exception as e:
    import traceback
    print("❌ Ocorreu um erro:")
    traceback.print_exc()

