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
    print("💡 Função gerar_resposta acionada")

    if isinstance(mensagem, dict) and "button_reply" in mensagem:
        id_recebido = mensagem["button_reply"]["id"]
    else:
        id_recebido = mensagem.strip()

    texto = id_recebido.lower().strip()

    import unicodedata
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')

    print("📥 Texto recebido:", repr(texto))
    print("📥 ID recebido:", repr(id_recebido))

    blocos = {
        "1.1": "🛒 *Veículos de Passeio*\n\nAlexandre: https://wa.me/5511940559880\n📧 alexandre@sullato.com.br\nJeferson: https://wa.me/5511941006862\n📧 jeferson@sullato.com.br\nMarcela: https://wa.me/5511953816822\n📧 marcela@sullato.com.br\nPedro: https://wa.me/5511952704363\n📧 pedro@sullato.com.br\nThiago: https://wa.me/5511986122905\n📧 thiago@sullato.com.br\nVanessa: https://wa.me/5511947954378\n📧 vanessa@sullato.com.br\nVinicius: https://wa.me/5511911260469\n📧 vinicius@sullato.com.br\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br",
        "1.2": "🚐 *Veículos Utilitários*\n\nMagali: https://wa.me/5511940215082\n📧 magali@sullato.com.br\nSilvano: https://wa.me/5511988598736\n📧 silvano@sullato.com.br\nThiago: https://wa.me/5511986122905\n📧 thiago@sullato.com.br\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br",
        "1.3": "📍 *Endereço e Site*\n\n🌐 Site: https://www.sullato.com.br\n📸 Instagram: @sullatomicrosevans | @sullato.veiculos\n\n🏢 Loja 01: Av. São Miguel, 7900 – SP\n📞 (11) 20305081 / (11) 20315081\n\n🏢 Loja 02/03: Av. São Miguel, 4049/4084 – SP\n📞 (11) 25423332 / (11) 25423333\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br",
        "2.1": "🔧 *Oficina e Peças*\n\nErico: https://wa.me/5511940497678\n📧 erico@sullato.com.br\nLeandro: https://wa.me/5511940443566\n📧 sullatopecas@sullato.com.br\n📞 (11) 25423332 / (11) 25423333\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br",
        "2.2": "📍 *Endereço da Oficina*\n\n🏢 Loja 02: Av. São Miguel, 4049 – SP\n📞 (11) 25423332 / (11) 25423333\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br",
        "3.1": "💳 *Crédito e Financiamento*\n\nMagali: https://wa.me/5511940215082\n📧 magali@sullato.com.br\nPatrícia: https://wa.me/5511940215081\n📧 patricia@sullato.com.br\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br",
        "3.2.1": "📦 *Pós-venda – Passeio*\n\n📞 (11) 25423332 / (11) 25423333\nLeandro: https://wa.me/5511940443566\n📧 sullatopecas@sullato.com.br\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br",
        "3.2.2": "📦 *Pós-venda – Utilitário*\n\n📞 (11) 25423332 / (11) 25423333\nErico: https://wa.me/5511940497678\n📧 erico@sullato.com.br\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br",
        "4.1": "🏛️ *Vendas Governamentais*\n\n📞 (11) 20315081 / (11) 20305081\nSolange: https://wa.me/5511989536141\n📧 sol@sullato.com.br\n📧 vendasdireta@sullato.com.br\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br",
        "4.2": "📃 *Veículo por Assinatura*\n\nAlexsander: https://wa.me/5511996371559\n📧 alex@sullato.com.br\n\n✉️ Em caso de dúvidas, escreva para: chatbot@sullato.com.br"
    }

    botoes_menu = [
        {"type": "reply", "reply": {"id": "1", "title": "🛒 Comprar/Vender"}},
        {"type": "reply", "reply": {"id": "2", "title": "🔧 Oficina/Peças"}},
        {"type": "reply", "reply": {"id": "mais1", "title": "➕ Mais opções"}}
    ]

    if texto in ["oi", "olá", "menu", "início", "bom dia", "boa tarde", "boa noite"]:
        enviar_botoes(numero, "Olá! 👋 Eu sou o atendimento virtual da *Sullato*. Como posso te ajudar?", botoes_menu)
        return

    if id_recebido == "1":
        botoes1 = [
            {"type": "reply", "reply": {"id": "1.1", "title": "🚘 Passeio"}},
            {"type": "reply", "reply": {"id": "1.2", "title": "🚐 Utilitário"}},
            {"type": "reply", "reply": {"id": "1.3", "title": "📍 Endereço"}}
        ]
        enviar_botoes(numero, "Escolha uma opção de compra/venda:", botoes1)
        return

    if id_recebido == "2":
        botoes2 = [
            {"type": "reply", "reply": {"id": "2.1", "title": "🔧 Oficina"}},
            {"type": "reply", "reply": {"id": "2.2", "title": "📍 Endereço Oficina"}}
        ]
        enviar_botoes(numero, "Escolha uma opção sobre oficina/peças:", botoes2)
        return

    if id_recebido == "mais1":
        botoes_mais1 = [
            {"type": "reply", "reply": {"id": "3", "title": "💳 Crédito"}},
            {"type": "reply", "reply": {"id": "pos-venda", "title": "🔁 Pós-venda"}},
            {"type": "reply", "reply": {"id": "mais2", "title": "➕ Mais opções"}}
        ]
        enviar_botoes(numero, "Mais opções disponíveis:", botoes_mais1)
        return

    if id_recebido == "3":
        enviar_mensagem(numero, blocos["3.1"])
        return

    if "pos" in id_recebido.lower() and "venda" in id_recebido.lower():
        bbotoes_posvenda = [
            {"type": "reply", "reply": {"id": "3.2.1", "title": "🚘 Pós-venda Passeio"}},
            {"type": "reply", "reply": {"id": "3.2.2", "title": "🚐 Pós-venda Utilitário"}},
            {"type": "reply", "reply": {"id": "menu", "title": "🔙 Voltar ao início"}}
        ]
        enviar_botoes(numero, "📦 *Pós-venda Sullato*\n\nEscolha uma das opções abaixo:", botoes_posvenda)
        return

    if id_recebido == "3.2.1":
        enviar_mensagem(numero, blocos["3.2.1"])
        return

    if id_recebido == "3.2.2":
        enviar_mensagem(numero, blocos["3.2.2"])
        return

    if id_recebido == "mais2":
        botoes_mais2 = [
            {"type": "reply", "reply": {"id": "4.1", "title": "🏛️ Governamentais"}},
            {"type": "reply", "reply": {"id": "4.2", "title": "📃 Assinatura"}},
            {"type": "reply", "reply": {"id": "menu", "title": "🔙 Voltar ao início"}}
        ]
        enviar_botoes(numero, "Outras opções:", botoes_mais2)
        return

    if id_recebido in blocos:
        enviar_mensagem(numero, blocos[id_recebido])
        return

    enviar_botoes(numero, "Desculpe, não entendi 🤔. Veja abaixo algumas opções:", botoes_menu)
