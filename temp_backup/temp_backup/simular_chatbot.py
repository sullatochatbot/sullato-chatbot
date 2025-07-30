from responder import gerar_resposta
from datetime import datetime

print("🔁 Simulador do Chatbot Sullato")
print("Digite 'sair' para encerrar.\n")

def registrar_conversa(mensagem_cliente):
    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    with open("log_conversas.txt", "a", encoding="utf-8") as log:
        log.write(f"[{data_hora}] Cliente: {mensagem_cliente}\n")

# Número fixo de teste (simula número do cliente)
numero_teste = "5511940123456"

while True:
    mensagem = input("Cliente: ")
    if mensagem.lower() in ["sair", "exit", "quit"]:
        print("👋 Encerrando o simulador. Até logo!")
        break

    gerar_resposta(mensagem, numero_teste)
    registrar_conversa(mensagem)
