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
        "3.1": "*Crédito e Financiamento*\n\nEntre em contato conosco pelo WhatsApp para análise de crédito.",
        "3.2.1": "*Pós-venda – Passeio*\n\nLeandro: https://wa.me/5511940443566\nEmail: sullatopecas@sullato.com.br",
        "3.2.2": "*Pós-venda – Utilitário*\n\nErico: https://wa.me/5511940497678\nEmail: erico@sullato.com.br",
        "4.1": "*Vendas Governamentais*\n\nSolange: https://wa.me/5511989536141\nEmail: sol@sullato.com.br",
        "4.2": "*Veículo por Assinatura*\n\nAlexsander: https://wa.me/5511996371559\nEmail: alex@sullato.com.br"
    }

    botoes_menu = [
        {"type": "reply", "reply": {"id": "1", "title": "Comprar/Vender"}},
        {"type": "reply", "reply": {"id": "2", "title": "Oficina/Peças"}},
        {"type": "reply", "reply": {"id": "mais1", "title": "Mais opções"}}
    ]

    if texto in ["oi", "ola", "menu", "inicio", "bom dia", "boa tarde", "boa noite"]:
        enviar_botoes(numero, "Olá! Eu sou o atendimento virtual da Sullato. Como posso te ajudar?", botoes_menu)
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
