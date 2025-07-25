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

    blocos = {
        "1": """📍 *Informações da Sullato*...

🌐 Site: www.sullato.com.br
📸 Instagram:
@sullatomicrosevans – https://www.instagram.com/sullatomicrosevans
@sullato.veiculos – https://www.instagram.com/sullato.veiculos
🏢 Endereços: Sullato Micros e Vans / Sullato Veículos""",

        "2.1": "🚗 *Compra – Veículo de Passeio*...",
        "2.2": "🚐 *Compra – Veículo Utilitário*...",
        "3.1": "🔁 *Venda – Veículo de Passeio*...",
        "3.2": "🔁 *Venda – Veículo Utilitário*...",
        "4": "💰 *Crédito / Financiamento*...",
        "5": "🔧 *Oficina / Peças*...",
        "6": "🏛️ *Venda Direta (Governo/ONG)*...",
        "7.1": "🛡️ *Garantia – Veículo de Passeio*...",
        "7.2": "🛡️ *Garantia – Veículo Utilitário*..."
    }

    # === Menu Principal
    botoes_menu = [
        {"type": "reply", "reply": {"id": "2", "title": "🚗 Comprar"}},
        {"type": "reply", "reply": {"id": "3", "title": "📤 Vender"}},
        {"type": "reply", "reply": {"id": "mais1", "title": "➕ Mais opções"}}
    ]

    # === Menu Mais1
    if texto == "mais1":
        botoes_mais1 = [
            {"type": "reply", "reply": {"id": "1", "title": "📍 Endereço"}},
            {"type": "reply", "reply": {"id": "6", "title": "🏛️ Venda Direta"}},
            {"type": "reply", "reply": {"id": "mais2", "title": "➕ Mais opções"}}
        ]
        enviar_botoes(numero, "Outras opções disponíveis:", botoes_mais1)
        return

    # === Menu Mais2
    if texto == "mais2":
        botoes_mais2 = [
            {"type": "reply", "reply": {"id": "7", "title": "🛡️ Garantia"}},
            {"type": "reply", "reply": {"id": "5", "title": "🔧 Oficina"}},
            {"type": "reply", "reply": {"id": "menu", "title": "🔙 Voltar ao início"}}
        ]
        enviar_botoes(numero, "Mais opções:", botoes_mais2)
        return

    # === Voltar ao menu
    if texto in ["menu", "início", "oi", "olá", "bom dia", "boa tarde", "boa noite"]:
        enviar_botoes(numero, "Olá! 👋 Eu sou o atendimento virtual da *Sullato*.\nComo posso te ajudar?", botoes_menu)
        return

    # === Compra
    if texto == "2":
        botoes_sub = [
            {"type": "reply", "reply": {"id": "2.1", "title": "🚘 Passeio"}},
            {"type": "reply", "reply": {"id": "2.2", "title": "🚐 Utilitário"}}
        ]
        enviar_botoes(numero, "Qual tipo de veículo você quer comprar?", botoes_sub)
        return

    # === Venda
    if texto == "3":
        botoes_sub = [
            {"type": "reply", "reply": {"id": "3.1", "title": "🚘 Vender Passeio"}},
            {"type": "reply", "reply": {"id": "3.2", "title": "🚐 Vender Utilitário"}}
        ]
        enviar_botoes(numero, "Qual tipo de veículo deseja vender?", botoes_sub)
        return

    # === Garantia
    if texto == "7":
        botoes_sub = [
            {"type": "reply", "reply": {"id": "7.1", "title": "✅ Garantia Passeio"}},
            {"type": "reply", "reply": {"id": "7.2", "title": "✅ Garantia Utilitário"}}
        ]
        enviar_botoes(numero, "Para qual tipo de veículo é a garantia?", botoes_sub)
        return

    # === Blocos finais (respostas diretas)
    if texto in blocos:
        enviar_mensagem(numero, blocos[texto])
        return

    # === Fallback
    enviar_botoes(numero, "Desculpe, não entendi 🤔. Tente uma das opções abaixo:", botoes_menu)
