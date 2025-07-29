import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import csv
import unicodedata
import re  # necessário para capturar nome com regex
from salvar_em_google_sheets import salvar_em_google_sheets
from atualizar_google_sheets import atualizar_interesse_google_sheets  
            # from mala_direta import salvar_em_mala_direta         
from registrar_historico import registrar_interacao
from salvar_em_mala_direta import salvar_em_mala_direta

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# 🧠 Função para capturar nome do cliente em frases comuns
def extrair_nome(texto):
    texto = texto.lower()
    padroes = [
        r"meu nome é ([a-zA-ZÀ-ÿ\s]+)",
        r"me chamo ([a-zA-ZÀ-ÿ\s]+)",
        r"sou o ([a-zA-ZÀ-ÿ\s]+)",
        r"sou a ([a-zA-ZÀ-ÿ\s]+)",
        r"nome é ([a-zA-ZÀ-ÿ\s]+)"
    ]
    for padrao in padroes:
        match = re.search(padrao, texto)
        if match:
            nome_extraido = match.group(1).strip()
            return nome_extraido
    return None

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
    try:
        resposta = requests.post(url, headers=headers, json=payload)
        print("➡️ Resposta da Meta:", resposta.status_code, resposta.text)
    except Exception as e:
        print("❌ Erro ao enviar mensagem de texto:", e)

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
    try:
        resposta = requests.post(url, headers=headers, json=payload)
        print("🟢 Botões enviados:", resposta.status_code, resposta.text)
    except Exception as e:
        print("❌ Erro ao enviar botões:", e)

def gerar_resposta(mensagem, numero, nome_cliente=None):
    numero = ''.join(filter(str.isdigit, numero))
    nome_capturado = None  # 🔐 evita erro se nome_cliente já vier preenchido

    print("Função gerar_resposta acionada")
    id_recebido = ""

    if isinstance(mensagem, dict):
        if "interactive" in mensagem and "button_reply" in mensagem["interactive"]:
            id_recebido = mensagem["interactive"]["button_reply"]["id"]
        elif "text" in mensagem:
            id_recebido = mensagem["text"].get("body", "")
    elif isinstance(mensagem, str):
        id_recebido = mensagem.strip()

    id_recebido = unicodedata.normalize('NFD', id_recebido.strip().lower())
    id_recebido = ''.join(c for c in id_recebido if unicodedata.category(c) != 'Mn')

    print("ID recebido:", repr(id_recebido))

    if not nome_cliente:
        nome_capturado = extrair_nome(id_recebido)
        if nome_capturado:
            nome_cliente = nome_capturado
            print("✅ Nome detectado automaticamente:", nome_cliente)

    # 🔒 Sempre grava o primeiro contato apenas uma vez, com nome ou "Desconhecido"
    nome_final = nome_cliente.title() if nome_cliente else "Desconhecido"
    salvar_em_google_sheets(numero, nome_final, interesse="Primeiro contato")
    registrar_interacao(numero, nome_final, interesse="Primeiro contato")
    salvar_em_mala_direta(numero, nome_final)

    # ✅ Se o nome for capturado agora, responder com saudação e botões
    if nome_capturado:
        botoes_menu = [
            {"type": "reply", "reply": {"id": "1", "title": "Comprar/Vender"}},
            {"type": "reply", "reply": {"id": "2", "title": "Oficina/Peças"}},
            {"type": "reply", "reply": {"id": "mais1", "title": "Mais opções"}}
        ]
        enviar_botoes(numero, f"Olá, {nome_cliente.title()}! 😃 Seja bem-vindo ao atendimento virtual do Grupo Sullato. Como posso te ajudar?", botoes_menu)
        return

    botoes_menu = [
        {"type": "reply", "reply": {"id": "1", "title": "Comprar/Vender"}},
        {"type": "reply", "reply": {"id": "2", "title": "Oficina/Peças"}},
        {"type": "reply", "reply": {"id": "mais1", "title": "Mais opções"}}
    ]

    if id_recebido in ["oi", "ola", "menu", "inicio", "bom dia", "boa tarde", "boa noite"]:
        enviar_botoes(numero, f"Olá, {nome_cliente.title()}! 😃 Seja bem-vindo ao atendimento virtual do Grupo Sullato. Como posso te ajudar?", botoes_menu)
        return

    blocos = {
    "1.1": """*Veículos de Passeio*

✉️ Consulte um de nossos consultores.

👨🏻‍💼 Alexandre: https://wa.me/5511940559880
👨🏻‍💼 Jeferson: https://wa.me/5511941006862
👩🏻‍💼 Marcela: https://wa.me/5511912115673
👨🏻‍💼 Pedro: https://wa.me/5511992037103
👨🏻‍💼 Thiago: https://wa.me/5511986122905
👩🏻‍💼 Vanessa: https://wa.me/5511947954378
👨🏻‍💼 Vinicius: https://wa.me/5511911260469""",
    "1.2": """*Veículos Utilitários*

✉️ Consulte um de nossos consultores.

👩🏻‍💼 Magali: https://wa.me/5511940215082
👨🏻‍💼 Silvano: https://wa.me/5511988598736
👨🏻‍💼 Thiago: https://wa.me/5511986122905""",
    "1.3": """*Endereço e Site*

🌐 Site: www.sullato.com.br – https://www.sullato.com.br
📸 Instagram: @sullatomicrosevans – https://www.instagram.com/sullatomicrosevans
📸 Instagram: @sullato.veiculos – https://www.instagram.com/sullato.veiculos

🏢 Loja 01: Av. São Miguel, 7900 – cep. 08070-001 - SP
📞 (11) 2030-5081 | (11) 2031-5081

🏢 Loja 02/03: Av. São Miguel, 4049/4084 – cep. 03871-000 - SP
📞 (11) 2542-3332 | (11) 2542-3333""",
    "2.1": """*Oficina e Peças*

✉️ Consulte um de nossos consultores.

🔧 Erico: https://wa.me/5511940497678
🔧 Leandro: https://wa.me/5511940443566""",
    "2.2": """*Endereço da Oficina*

🏢 Loja 02: Av. São Miguel, 4049 – cep. 03871-000 - SP
📞 (11) 2542-3332 | (11) 2542-3333""",
    "3": """*Crédito e Financiamento*

✉️ Consulte uma de nossas consultoras.

💰 Magali: https://wa.me/5511940215082
💰 Patrícia: https://wa.me/5511940215081""",
    "3.2.1": """*Pós-venda – Passeio*

✉️ Consulte um de nossos consultores.

🔧 Leandro: https://wa.me/5511940443566""",
    "3.2.2": """*Pós-venda – Utilitário*

✉️ Consulte um de nossos consultores.

🔧 Erico: https://wa.me/5511940497678""",
    "4.1": """*Vendas Governamentais*

✉️ Consulte nossa consultora.

🏛️ Solange: https://wa.me/5511989536141""",
    "4.2": """*Veículo por Assinatura*

✉️ Consulte nosso consultor.

📆 Alexsander: https://wa.me/5511996371559"""
}

    if id_recebido == "1":
        atualizar_interesse_google_sheets(numero, "Menu - Compra/Venda")
        enviar_botoes(numero, "Escolha uma opção de compra/venda:", [
            {"type": "reply", "reply": {"id": "1.1", "title": "Passeio"}},
            {"type": "reply", "reply": {"id": "1.2", "title": "Utilitário"}},
            {"type": "reply", "reply": {"id": "1.3", "title": "Endereço"}}
        ])
        return

    if id_recebido == "2":
        atualizar_interesse_google_sheets(numero, "Menu - Oficina/Peças")
        enviar_botoes(numero, "Escolha uma opção sobre oficina/peças:", [
            {"type": "reply", "reply": {"id": "2.1", "title": "Oficina e Peças"}},
            {"type": "reply", "reply": {"id": "2.2", "title": "Endereço Oficina"}}
        ])
        return

    if id_recebido == "mais1":
        atualizar_interesse_google_sheets(numero, "Menu - Mais opções")
        enviar_botoes(numero, "Mais opções disponíveis:", [
            {"type": "reply", "reply": {"id": "3", "title": "Crédito"}},
            {"type": "reply", "reply": {"id": "btn-pos-venda", "title": "Pós-venda"}},
            {"type": "reply", "reply": {"id": "mais2", "title": "Mais opções"}}
        ])
        return

    if id_recebido == "mais2":
        atualizar_interesse_google_sheets(numero, "Menu - Outras opções")
        enviar_botoes(numero, "Outras opções:", [
            {"type": "reply", "reply": {"id": "4.1", "title": "Governamentais"}},
            {"type": "reply", "reply": {"id": "4.2", "title": "Assinatura"}},
            {"type": "reply", "reply": {"id": "menu", "title": "Voltar ao início"}}
        ])
        return

    if id_recebido == "btn-pos-venda":
        atualizar_interesse_google_sheets(numero, "Menu - Pós-venda")
        enviar_botoes(numero, "Pós-venda Sullato - Escolha uma das opções abaixo:", [
            {"type": "reply", "reply": {"id": "3.2.1", "title": "Passeio"}},
            {"type": "reply", "reply": {"id": "3.2.2", "title": "Utilitário"}},
            {"type": "reply", "reply": {"id": "menu", "title": "Voltar ao início"}}
        ])
        return

    if id_recebido == "1.1":
        atualizar_interesse_google_sheets(numero, "Interesse - Passeio")
        enviar_mensagem(numero, blocos["1.1"])
        return

    if id_recebido == "1.2":
        atualizar_interesse_google_sheets(numero, "Interesse - Utilitário")
        enviar_mensagem(numero, blocos["1.2"])
        return

    if id_recebido == "1.3":
        atualizar_interesse_google_sheets(numero, "Interesse - Endereço Loja")
        enviar_mensagem(numero, blocos["1.3"])
        return

    if id_recebido == "2.1":
        atualizar_interesse_google_sheets(numero, "Interesse - Oficina e Peças")
        enviar_mensagem(numero, blocos["2.1"])
        return

    if id_recebido == "2.2":
        atualizar_interesse_google_sheets(numero, "Interesse - Endereço Oficina")
        enviar_mensagem(numero, blocos["2.2"])
        return

    if id_recebido == "3":
        atualizar_interesse_google_sheets(numero, "Interesse - Crédito")
        enviar_mensagem(numero, blocos["3"])
        return

    if id_recebido == "3.2.1":
        atualizar_interesse_google_sheets(numero, "Interesse - Pós-venda Passeio")
        enviar_mensagem(numero, blocos["3.2.1"])
        return

    if id_recebido == "3.2.2":
        atualizar_interesse_google_sheets(numero, "Interesse - Pós-venda Utilitário")
        enviar_mensagem(numero, blocos["3.2.2"])
        return

    if id_recebido == "4.1":
        atualizar_interesse_google_sheets(numero, "Interesse - Governamentais")
        enviar_mensagem(numero, blocos["4.1"])
        return

    if id_recebido == "4.2":
        atualizar_interesse_google_sheets(numero, "Interesse - Assinatura")
        enviar_mensagem(numero, blocos["4.2"])
        return


    enviar_botoes(numero, "Desculpe, não entendi. Escolha uma das opções abaixo:", botoes_menu)
    return
