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
        "1.1": """🛒 *Veículos de Passeio*\n\nAlexandre: [011 940559880](https://wa.me/5511940559880)\n📧 alexandre@sullato.com.br\nJeferson: [011 941006862](https://wa.me/5511941006862)\n📧 jeferson@sullato.com.br\nMarcela: [011 953816822](https://wa.me/5511953816822)\n📧 marcela@sullato.com.br\nPedro: [011 952704363](https://wa.me/5511952704363)\n📧 pedro@sullato.com.br\nThiago: [011 986122905](https://wa.me/5511986122905)\n📧 thiago@sullato.com.br\nVanessa: [011 947954378](https://wa.me/5511947954378)\n📧 vanessa@sullato.com.br\nVinicius: [011 911260469](https://wa.me/5511911260469)\n📧 vinicius@sullato.com.br\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br""",

        "1.2": """🚐 *Veículos Utilitários*\n\nMagali: [011 940215082](https://wa.me/5511940215082)\n📧 magali@sullato.com.br\nSilvano: [011 988598736](https://wa.me/5511988598736)\n📧 silvano@sullato.com.br\nThiago: [011 986122905](https://wa.me/5511986122905)\n📧 thiago@sullato.com.br\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br""",

        "1.3": """📍 *Endereço e Site*\n\n🌐 Site: [www.sullato.com.br](https://www.sullato.com.br)\n📸 Instagram: [@sullatomicrosevans](https://www.instagram.com/sullatomicrosevans) | [@sullato.veiculos](https://www.instagram.com/sullato.veiculos)\n\n🏢 Loja 01: Av. São Miguel, 7900 – SP\n📞 (11) 20305081 / (11) 20315081\n\n🏢 Loja 02/03: Av. São Miguel, 4049/4084 – SP\n📞 (11) 25423332 / (11) 25423333\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br""",

        "3.1": """💳 *Crédito e Financiamento*\n\nMagali: [011 940215082](https://wa.me/5511940215082)\n📧 magali@sullato.com.br\nPatrícia: [011 940215081](https://wa.me/5511940215081)\n📧 patricia@sullato.com.br\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br""",

        "3.2.1": """📦 *Pós-venda – Passeio*\n\n📞 (11) 25423332 / (11) 25423333\nLeandro: [011 940443566](https://wa.me/5511940443566)\n📧 sullatopecas@sullato.com.br\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br""",

        "3.2.2": """📦 *Pós-venda – Utilitário*\n\n📞 (11) 25423332 / (11) 25423333\nErico: [011 940497678](https://wa.me/5511940497678)\n📧 erico@sullato.com.br\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br""",

        "4.1": """🏛️ *Vendas Governamentais*\n\n📞 (11) 20315081 / (11) 20305081\nSolange: [011 989536141](https://wa.me/5511989536141)\n📧 sol@sullato.com.br\n📧 vendasdireta@sullato.com.br\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br""",

        "4.2": """📃 *Veículo por Assinatura*\n\nAlexsander: [011 996371559](https://wa.me/5511996371559)\n📧 alex@sullato.com.br\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br"""
    }

    # (continua igual o restante do código)

    if texto in blocos:
        enviar_mensagem(numero, blocos[texto])
        return

    enviar_botoes(numero, "Desculpe, não entendi 🤔. Veja abaixo algumas opções:", botoes_menu)
