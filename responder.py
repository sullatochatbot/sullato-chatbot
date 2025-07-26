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

    saudacao = "\n\n✉️ Em caso de dúvidas, consulte um de nossos consultores."

    blocos = {
        "1.1": """*Veículos de Passeio*
📍 Alexandre: https://wa.me/5511940559880 | 📧 alexandre@sullato.com.br
📍 Jeferson: https://wa.me/5511941006862 | 📧 jeferson@sullato.com.br
📍 Marcela: https://wa.me/5511953816822 | 📧 marcela@sullato.com.br
📍 Pedro: https://wa.me/5511952704363 | 📧 pedro@sullato.com.br
📍 Thiago: https://wa.me/5511986122905 | 📧 thiago@sullato.com.br
📍 Vanessa: https://wa.me/5511947954378 | 📧 vanessa@sullato.com.br
📍 Vinicius: https://wa.me/5511911260469 | 📧 vinicius@sullato.com.br""" + saudacao,

        "1.2": """*Veículos Utilitários*
📍 Magali: https://wa.me/5511940215082 | 📧 magali@sullato.com.br
📍 Silvano: https://wa.me/5511988598736 | 📧 silvano@sullato.com.br
📍 Thiago: https://wa.me/5511986122905 | 📧 thiago@sullato.com.br""" + saudacao,

        "1.3": """*Endereço e Site*
🌐 Site: https://www.sullato.com.br
📸 Instagram: @sullatomicrosevans | @sullato.veiculos

🏢 Loja 01: Av. São Miguel, 7900 – SP
📞 (11) 2030-5081 | (11) 2031-5081

🏢 Loja 02/03: Av. São Miguel, 4049/4084 – SP
📞 (11) 2542-3332 | (11) 2542-3333""" + saudacao,

        "2.1": """*Oficina e Peças*
🔧 Erico: https://wa.me/5511940497678 | 📧 erico@sullato.com.br
🔧 Leandro: https://wa.me/5511940443566 | 📧 sullatopecas@sullato.com.br""" + saudacao,

        "2.2": """*Endereço da Oficina*
🏢 Loja 02: Av. São Miguel, 4049 – SP
📞 (11) 2542-3332 | (11) 2542-3333""" + saudacao,

        "3.1": """*Crédito e Financiamento*
💰 Magali: https://wa.me/5511940215082 | 📧 magali@sullato.com.br
💰 Patrícia: https://wa.me/5511940215081 | 📧 patricia@sullato.com.br""" + saudacao,

        "3.2.1": """*Pós-venda – Passeio*
🔧 Leandro: https://wa.me/5511940443566 | 📧 sullatopecas@sullato.com.br""" + saudacao,

        "3.2.2": """*Pós-venda – Utilitário*
🔧 Erico: https://wa.me/5511940497678 | 📧 erico@sullato.com.br""" + saudacao,

        "4.1": """*Vendas Governamentais*
🏛️ Solange: https://wa.me/5511989536141 | 📧 sol@sullato.com.br""" + saudacao,

        "4.2": """*Veículo por Assinatura*
📆 Alexsander: https://wa.me/5511996371559 | 📧 alex@sullato.com.br""" + saudacao
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
            {"type": "reply", "reply": {"id": "2.1", "title": "Oficina"}},
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
