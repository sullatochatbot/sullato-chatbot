import csv
import os
from datetime import datetime
import unicodedata

from sheets_gravador import salvar_em_planilha_google  # ⬅️ integração direta com Google Sheets

def salvar_em_mala_direta(numero, nome, interesse=""):
    print("📥 salvar_em_mala_direta chamada com:", numero, nome, interesse)

    # 🔒 Garante que o número esteja limpo (somente dígitos)
    numero = ''.join(filter(str.isdigit, numero))
    data_hoje = datetime.now().strftime("%d/%m/%Y")

    nome = nome or "Desconhecido"
    nome = ''.join(c for c in unicodedata.normalize('NFD', nome) if unicodedata.category(c) != 'Mn')
    nome = nome.replace("\n", " ").strip()

    # ✅ Salva no Google Sheets
    salvar_em_planilha_google(numero, nome, interesse)

    # (Opcional) Também salva localmente como backup CSV
    caminho_arquivo = "mala_direta.csv"
    linhas_atualizadas = []
    numero_encontrado = False

    if os.path.exists(caminho_arquivo):
        with open(caminho_arquivo, "r", encoding="utf-8") as arquivo:
            linhas = arquivo.readlines()
            for linha in linhas:
                partes = linha.strip().split(",")
                if partes[0] == numero:
                    numero_encontrado = True
                    if partes[1] == "":
                        partes[1] = nome
                    if len(partes) >= 3:
                        partes[2] = interesse or partes[2]
                    linha = ",".join(partes)
                linhas_atualizadas.append(linha)

    if numero_encontrado:
        with open(caminho_arquivo, "w", encoding="utf-8", newline="") as arquivo:
            for linha in linhas_atualizadas:
                arquivo.write(linha + "\n")
        print(f"✏️ Contato atualizado no CSV: {numero}")
    else:
        with open(caminho_arquivo, "a", encoding="utf-8", newline="") as arquivo:
            writer = csv.writer(arquivo)
            writer.writerow([numero, nome, interesse, data_hoje])
            print(f"✅ Contato salvo no CSV: {numero}, {nome}, {interesse}, {data_hoje}")
