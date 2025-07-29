import csv
from datetime import datetime
import os

ARQUIVO_CSV = "mala_direta.csv"

def salvar_em_mala_direta(numero, nome):
    try:
        # Verifica se o arquivo já existe
        ja_existe = False
        if os.path.exists(ARQUIVO_CSV):
            with open(ARQUIVO_CSV, mode="r", encoding="utf-8") as file:
                leitor = csv.reader(file)
                for linha in leitor:
                    if linha and linha[0].strip() == numero:
                        ja_existe = True
                        break

        if ja_existe:
            print(f"⚠️ Número já está na mala direta: {numero}")
            return

        # Se não existir, adiciona ao CSV
        adicionar_cabecalho = not os.path.exists(ARQUIVO_CSV)
        with open(ARQUIVO_CSV, mode="a", newline='', encoding="utf-8") as file:
            writer = csv.writer(file)
            if adicionar_cabecalho:
                writer.writerow(["Número", "Nome", "Data/Hora"])
            writer.writerow([numero, nome, datetime.now().strftime("%d/%m/%Y %H:%M:%S")])

        print(f"📨 Contato salvo na mala direta: {numero}, {nome}")

    except Exception as e:
        print("❌ Erro ao salvar na mala direta:", e)
