from responder import responder
from datetime import datetime

print("🔁 Simulador do Chatbot Sullato")
print("Digite 'sair' para encerrar.\n")

def registrar_conversa(mensagem_cliente, resposta_bot):
    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    with open("log_conversas.txt", "a", encoding="utf-8") as log:
        log.write(f"[{data_hora}] Cliente: {mensagem_cliente}\n")
        log.write(f"[{data_hora}] SullatoBot: {resposta_bot}\n\n")

while True:
    mensagem = input("Cliente: ")
    if mensagem.lower() in ["sair", "exit", "quit"]:
        print("👋 Encerrando o simulador. Até logo!")
        break
    resposta = responder(mensagem)
    print("SullatoBot:", resposta)
    registrar_conversa(mensagem, resposta)
