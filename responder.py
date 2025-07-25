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
        "1.1": """🛒 *Veículos de Passeio*\n\nAlexandre: 011 940559880\n📧 alexandre@sullato.com.br\nJeferson: 011 941006862\n📧 jeferson@sullato.com.br\nMarcela: 011 953816822\n📧 marcela@sullato.com.br\nPedro: 011 952704363\n📧 pedro@sullato.com.br\nThiago: 011 986122905\n📧 thiago@sullato.com.br\nVanessa: 011 947954378\n📧 vanessa@sullato.com.br\nVinicius: 011 911260469\n📧 vinicius@sullato.com.br\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br""",

        "1.2": """🚐 *Veículos Utilitários*\n\nMagali: 011 940215082\n📧 magali@sullato.com.br\nSilvano: 011 988598736\n📧 silvano@sullato.com.br\nThiago: 011 986122905\n📧 thiago@sullato.com.br\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br""",

        "1.3": """📍 *Endereço e Site*\n\n🌐 Site: www.sullato.com.br\n📸 Instagram: @sullatomicrosevans | @sullato.veiculos\n\n🏢 Loja 01: Av. São Miguel, 7900 – SP\n📞 (11) 20305081 / (11) 20315081\n\n🏢 Loja 02/03: Av. São Miguel, 4049/4084 – SP\n📞 (11) 25423332 / (11) 25423333\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br""",

        "2.1": """🔧 *Oficina / Peças*\n\n📞 (11) 25423332 / (11) 25423333\nErico: 011 940497678\n📧 erico@sullato.com.br\nLeandro: 011 940443566\n📧 sullatopecas@sullato.com.br\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br""",

        "2.2": """📍 *Endereço da Oficina*\n\n🏢 Av. São Miguel, 4049 – SP\n📞 (11) 25423332 / (11) 25423333\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br""",

        "3.1": """💳 *Crédito / Financiamento*\n\nMagali: 011 940215082\n📧 magali@sullato.com.br\nPatrícia: 011 940215081\n📧 patricia@sullato.com.br\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br""",

        "3.2.1": """📦 *Pós-venda – Passeio*\n\n📞 (11) 25423332 / (11) 25423333\nLeandro: 011 940443566\n📧 sullatopecas@sullato.com.br\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br""",

        "3.2.2": """📦 *Pós-venda – Utilitário*\n\n📞 (11) 25423332 / (11) 25423333\nErico: 011 940497678\n📧 erico@sullato.com.br\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br""",

        "4.1": """🏛️ *Vendas Governamentais*\n\n📞 (11) 20315081 / (11) 20305081\nSolange: 011 989536141\n📧 sol@sullato.com.br\n📧 vendasdireta@sullato.com.br\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br""",

        "4.2": """📃 *Veículo por Assinatura*\n\nAlexsander: 011 996371559\n📧 alex@sullato.com.br\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br"""
    }

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
