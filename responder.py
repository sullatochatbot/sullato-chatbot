import requests
import os
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

def enviar_mensagem(numero, texto):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }
    resposta = requests.post(url, headers=headers, json=payload)
    print("➡️ Resposta da Meta:", resposta.status_code, resposta.text)

def enviar_botoes(numero, texto, botoes):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": texto},
            "action": {"buttons": botoes}
        }
    }
    resposta = requests.post(url, headers=headers, json=payload)
    print("🟢 Botões enviados:", resposta.status_code, resposta.text)

def gerar_resposta(mensagem, numero):
    texto = mensagem.lower().strip()

    # BLOCO COMPLETO (já está no topo)

    botoes_menu = [
        {"type": "reply", "reply": {"id": "1", "title": "🛒 Comprar/Vender"}},
        {"type": "reply", "reply": {"id": "2", "title": "🔧 Oficina/Peças"}},
        {"type": "reply", "reply": {"id": "mais1", "title": "➕ Mais opções"}}
    ]

    if texto in ["oi", "olá", "menu", "início", "bom dia", "boa tarde", "boa noite"]:
        enviar_botoes(numero, "Olá! 👋 Eu sou o atendimento virtual da *Sullato*. Como posso te ajudar?", botoes_menu)
        return

    if texto == "1":
        botoes1 = [
            {"type": "reply", "reply": {"id": "1.1", "title": "🚘 Passeio"}},
            {"type": "reply", "reply": {"id": "1.2", "title": "🚐 Utilitário"}},
            {"type": "reply", "reply": {"id": "1.3", "title": "📍 Endereço"}}
        ]
        enviar_botoes(numero, "Escolha uma opção de compra/venda:", botoes1)
        return

    if texto == "2":
        botoes2 = [
            {"type": "reply", "reply": {"id": "2.1", "title": "🔧 Oficina"}},
            {"type": "reply", "reply": {"id": "2.2", "title": "📍 Endereço Oficina"}}
        ]
        enviar_botoes(numero, "Escolha uma opção sobre oficina/peças:", botoes2)
        return

    if texto == "2.1":
        enviar_mensagem(numero, blocos["2.1"])
        return

    if texto == "2.2":
        enviar_mensagem(numero, blocos["2.2"])
        return

    if texto == "mais1":
        botoes_mais1 = [
            {"type": "reply", "reply": {"id": "3", "title": "💳 Crédito"}},
            {"type": "reply", "reply": {"id": "4", "title": "🔁 Pós-venda"}},
            {"type": "reply", "reply": {"id": "mais2", "title": "➕ Mais opções"}}
        ]
        enviar_botoes(numero, "Mais opções disponíveis:", botoes_mais1)
        return

    if texto == "3":
        enviar_mensagem(numero, blocos["3.1"])
        return

    if texto == "4":
        botoes4 = [
            {"type": "reply", "reply": {"id": "3.2.1", "title": "🚘 Pós-venda Passeio"}},
            {"type": "reply", "reply": {"id": "3.2.2", "title": "🚐 Pós-venda Utilitário"}}
        ]
        enviar_botoes(numero, "Escolha uma opção de pós-venda:", botoes4)
        return

    if texto == "3.2.1":
        enviar_mensagem(numero, blocos["3.2.1"])
        return

    if texto == "3.2.2":
        enviar_mensagem(numero, blocos["3.2.2"])
        return

    if texto == "mais2":
        botoes_mais2 = [
            {"type": "reply", "reply": {"id": "4.1", "title": "🏛️ Governamentais"}},
            {"type": "reply", "reply": {"id": "4.2", "title": "📃 Assinatura"}},
            {"type": "reply", "reply": {"id": "menu", "title": "🔙 Voltar ao início"}}
        ]
        enviar_botoes(numero, "Outras opções:", botoes_mais2)
        return

    if texto in blocos:
        enviar_mensagem(numero, blocos[texto])
        return

    enviar_botoes(numero, "Desculpe, não entendi 🤔. Veja abaixo algumas opções:", botoes_menu)
