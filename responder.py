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
    print("Função gerar_resposta acionada")

    if isinstance(mensagem, dict) and "button_reply" in mensagem:
        id_recebido = mensagem["button_reply"]["id"]
    else:
        id_recebido = mensagem.strip()

    texto = id_recebido.lower().strip()

    import unicodedata
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')

    print("Texto recebido:", repr(texto))
    print("ID recebido:", repr(id_recebido))

    blocos = {
        "1.1": """*Veículos de Passeio*

✉️ Em caso de dúvidas, consulte um de nossos consultores.

👨🏻‍💼 Alexandre: https://wa.me/5511940559880  
👨🏻‍💼 Jeferson: https://wa.me/5511941006862  
👩🏻‍💼 Marcela: https://wa.me/5511953816822  
👨🏻‍💼 Pedro: https://wa.me/5511952704363  
👨🏻‍💼 Thiago: https://wa.me/5511986122905  
👩🏻‍💼 Vanessa: https://wa.me/5511947954378  
👨🏻‍💼 Vinicius: https://wa.me/5511911260469""",

        "1.2": """*Veículos Utilitários*

✉️ Em caso de dúvidas, consulte um de nossos consultores.

👩🏻‍💼 Magali: https://wa.me/5511940215082  
👨🏻‍💼 Silvano: https://wa.me/5511988598736  
👨🏻‍💼 Thiago: https://wa.me/5511986122905""",

        "1.3": """*Endereço e Site*

🌐 Site: [www.sullato.com.br](https://www.sullato.com.br)  
📸 Instagram: [@sullatomicrosevans](https://www.instagram.com/sullatomicrosevans) | [@sullato.veiculos](https://www.instagram.com/sullato.veiculos)

🏢 Loja 01: Av. São Miguel, 7900 – SP  
📞 (11) 2030-5081 | (11) 2031-5081  
🏷️ CEP: 08070-001

🏢 Loja 02/03: Av. São Miguel, 4049/4084 – SP  
📞 (11) 2542-3332 | (11) 2542-3333  
🏷️ CEP: 03871-000""",

        "2.1": """*Oficina e Peças*

✉️ Em caso de dúvidas, consulte um de nossos consultores.

🔧 Erico: https://wa.me/5511940497678  
🔧 Leandro: https://wa.me/5511940443566""",

        "2.2": """*Endereço da Oficina*

🏢 Loja 02: Av. São Miguel, 4049 – SP  
📞 (11) 2542-3332 | (11) 2542-3333  
🏷️ CEP: 03871-000""",

        "3.1": """*Crédito e Financiamento*

✉️ Em caso de dúvidas, consulte um de nossos consultores.

💰 Magali: https://wa.me/5511940215082  
💰 Patrícia: https://wa.me/5511940215081""",

        "3.2.1": """*Pós-venda – Passeio*

✉️ Em caso de dúvidas, consulte um de nossos consultores.

🔧 Leandro: https://wa.me/5511940443566""",

        "3.2.2": """*Pós-venda – Utilitário*

✉️ Em caso de dúvidas, consulte um de nossos consultores.

🔧 Erico: https://wa.me/5511940497678""",

        "4.1": """*Vendas Governamentais*

✉️ Em caso de dúvidas, consulte um de nossos consultores.

🏛️ Solange: https://wa.me/5511989536141""",

        "4.2": """*Veículo por Assinatura*

✉️ Em caso de dúvidas, consulte um de nossos consultores.

📆 Alexsander: https://wa.me/5511996371559"""
    }

    botoes_menu = [
        {"type": "reply", "reply": {"id": "1", "title": "Comprar/Vender"}},
        {"type": "reply", "reply": {"id": "2", "title": "Oficina/Peças"}},
        {"type": "reply", "reply": {"id": "mais1", "title": "Mais opções"}}
    ]

    if texto in ["oi", "ola", "menu", "inicio", "bom dia", "boa tarde", "boa noite"]:
        enviar_botoes(numero, "Olá! Eu sou o atendimento virtual da Sullato. Como posso te ajudar?", botoes_menu)
        return

    if id_recebido == "1":
        botoes1 = [
            {"type": "reply", "reply": {"id": "1.1", "title": "Passeio"}},
            {"type": "reply", "reply": {"id": "1.2", "title": "Utilitário"}},
            {"type": "reply", "reply": {"id": "1.3", "title": "Endereço"}}
        ]
        enviar_botoes(numero, "Escolha uma opção de compra/venda:", botoes1)
        return

    if id_recebido == "2":
        botoes2 = [
            {"type": "reply", "reply": {"id": "2.1", "title": "Oficina e Peças"}},
            {"type": "reply", "reply": {"id": "2.2", "title": "Endereço Oficina"}}
        ]
        enviar_botoes(numero, "Escolha uma opção sobre oficina/peças:", botoes2)
        return

    if id_recebido == "mais1":
        botoes_mais1 = [
            {"type": "reply", "reply": {"id": "3", "title": "Crédito"}},
            {"type": "reply", "reply": {"id": "btn-pos-venda", "title": "Pós-venda"}},
            {"type": "reply", "reply": {"id": "mais2", "title": "Mais opções"}}
        ]
        enviar_botoes(numero, "Mais opções disponíveis:", botoes_mais1)
        return

    if id_recebido == "3":
        enviar_mensagem(numero, blocos["3.1"])
        return

    if id_recebido == "btn-pos-venda":
        print("Botão Pós-venda DETECTADO com ID corrigido")
        botoes_posvenda = [
            {"type": "reply", "reply": {"id": "3.2.1", "title": "Passeio"}},
            {"type": "reply", "reply": {"id": "3.2.2", "title": "Utilitário"}},
            {"type": "reply", "reply": {"id": "menu", "title": "Voltar ao início"}}
        ]
        enviar_botoes(numero, "Pós-venda Sullato - Escolha uma das opções abaixo:", botoes_posvenda)
        return

    if id_recebido == "3.2.1":
        enviar_mensagem(numero, blocos["3.2.1"])
        return

    if id_recebido == "3.2.2":
        enviar_mensagem(numero, blocos["3.2.2"])
        return

    if id_recebido == "mais2":
        botoes_mais2 = [
            {"type": "reply", "reply": {"id": "4.1", "title": "Governamentais"}},
            {"type": "reply", "reply": {"id": "4.2", "title": "Assinatura"}},
            {"type": "reply", "reply": {"id": "menu", "title": "Voltar ao início"}}
        ]
        enviar_botoes(numero, "Outras opções:", botoes_mais2)
        return

    if id_recebido in blocos:
        enviar_mensagem(numero, blocos[id_recebido])
        return

    enviar_botoes(numero, "Desculpe, não entendi. Veja abaixo algumas opções:", botoes_menu)
