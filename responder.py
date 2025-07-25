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
        "1": """📍 *Informações da Sullato*

🌐 Site: www.sullato.com.br

📸 Instagram:
@sullatomicrosevans – https://www.instagram.com/sullatomicrosevans  
@sullato.veiculos – https://www.instagram.com/sullato.veiculos

🏢 Lojas:
➡️ Sullato Micros e Vans  
Av. São Miguel, 7900 – São Paulo/SP  
📞 (11) 2030-5081 / (11) 2031-5081

➡️ Sullato Veículos  
Av. São Miguel, 4049 / 4084 – São Paulo/SP  
📞 (11) 2542-3332 / (11) 2542-3333""",

        "2.1": """🚗 *Compra – Veículo de Passeio*
Alexandre: https://wa.me/5511940559880  
Jeferson: https://wa.me/5511941006862  
Marcela: https://wa.me/5511912115673  
Pedro: https://wa.me/5511952704363  
Thiago: https://wa.me/5511986122905  
Vanessa: https://wa.me/5511947954378  
Vinicius: https://wa.me/5511911260469""",

        "2.2": """🚐 *Compra – Veículo Utilitário*
Magali: https://wa.me/5511940215082  
Silvano: https://wa.me/5511988598736  
Thiago: https://wa.me/5511986122905""",

        "3.1": """🔁 *Venda – Veículo de Passeio*
Alexandre: https://wa.me/5511940559880  
Jeferson: https://wa.me/5511941006862  
Marcela: https://wa.me/5511912115673  
Pedro: https://wa.me/5511952704363  
Thiago: https://wa.me/5511986122905  
Vanessa: https://wa.me/5511947954378  
Vinicius: https://wa.me/5511911260469""",

        "3.2": """🔁 *Venda – Veículo Utilitário*
Magali: https://wa.me/5511940215082  
Silvano: https://wa.me/5511988598736  
Thiago: https://wa.me/5511986122905""",

        "4": """💰 *Crédito / Financiamento*
Magali: https://wa.me/5511940215082  
Patricia: https://wa.me/5511940215081""",

        "5": """🔧 *Oficina / Peças*
Erico: https://wa.me/5511940497678  
Leandro: https://wa.me/5511940443566  
📞 (11) 2542-3332 / (11) 2542-3333""",

        "6": """🏛️ *Venda Direta – Governo/ONGs*
Lucas / Natan / Leon: 📞 (11) 2031-5081 / (11) 2030-5081  
📧 vendasdireta@sullato.com.br""",

        "7.1": """🛡️ *Garantia – Veículo de Passeio*
Alexandre, Jeferson, Marcela, Pedro, Thiago, Vanessa, Vinicius  
📲 Contatos nos mesmos links da equipe de vendas.""",

        "7.2": """🛡️ *Garantia – Utilitário*
Magali, Silvano, Thiago  
📲 Contatos nos mesmos links da equipe de vendas."""
    }

    botoes_menu = [
        {"type": "reply", "reply": {"id": "2", "title": "🚗 Comprar"}},
        {"type": "reply", "reply": {"id": "3", "title": "📤 Vender"}},
        {"type": "reply", "reply": {"id": "mais1", "title": "➕ Mais opções"}}
    ]

    if texto in ["oi", "olá", "menu", "início", "bom dia", "boa tarde", "boa noite"]:
        enviar_botoes(numero, "Olá! 👋 Eu sou o atendimento virtual da *Sullato*. Como posso te ajudar?", botoes_menu)
        return

    if texto == "mais1":
        botoes_mais1 = [
            {"type": "reply", "reply": {"id": "1", "title": "📍 Endereço"}},
            {"type": "reply", "reply": {"id": "6", "title": "🏛️ Venda Direta"}},
            {"type": "reply", "reply": {"id": "mais2", "title": "➕ Mais opções"}}
        ]
        enviar_botoes(numero, "Outras opções disponíveis:", botoes_mais1)
        return

    if texto == "mais2":
        botoes_mais2 = [
            {"type": "reply", "reply": {"id": "7", "title": "🛡️ Garantia"}},
            {"type": "reply", "reply": {"id": "5", "title": "🔧 Oficina"}},
            {"type": "reply", "reply": {"id": "menu", "title": "🔙 Voltar ao início"}}
        ]
        enviar_botoes(numero, "Mais opções:", botoes_mais2)
        return

    if texto == "2":
        botoes = [
            {"type": "reply", "reply": {"id": "2.1", "title": "🚘 Passeio"}},
            {"type": "reply", "reply": {"id": "2.2", "title": "🚐 Utilitário"}}
        ]
        enviar_botoes(numero, "Qual tipo de veículo você quer comprar?", botoes)
        return

    if texto == "3":
        botoes = [
            {"type": "reply", "reply": {"id": "3.1", "title": "🚘 Vender Passeio"}},
            {"type": "reply", "reply": {"id": "3.2", "title": "🚐 Vender Utilitário"}}
        ]
        enviar_botoes(numero, "Qual tipo de veículo deseja vender?", botoes)
        return

    if texto == "7":
        botoes = [
            {"type": "reply", "reply": {"id": "7.1", "title": "✅ Garantia Passeio"}},
            {"type": "reply", "reply": {"id": "7.2", "title": "✅ Garantia Utilitário"}}
        ]
        enviar_botoes(numero, "Para qual tipo de veículo é a garantia?", botoes)
        return

    if texto in blocos:
        enviar_mensagem(numero, blocos[texto])
        return

    enviar_botoes(numero, "Desculpe, não entendi 🤔. Veja abaixo algumas opções:", botoes_menu)
