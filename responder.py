import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import csv
import unicodedata
import re  # necessário para capturar nome com regex
from interpretador_ia import interpretar_mensagem
from salvar_em_google_sheets import salvar_em_google_sheets
from atualizar_google_sheets import atualizar_interesse_google_sheets  
from registrar_historico import registrar_interacao
from salvar_em_mala_direta import salvar_em_mala_direta

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

def registrar_primeiro_interesse(numero, nome, interesse):
    atualizar_interesse_google_sheets(numero, interesse)

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
    nome_capturado = None

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

    nome_final = nome_cliente.title() if nome_cliente else "Desconhecido"
    salvar_em_google_sheets(numero, nome_final, interesse="Primeiro contato")
    registrar_interacao(numero, nome_final, interesse="Primeiro contato")
    salvar_em_mala_direta(numero, nome_final)

    # Interpretação inteligente da mensagem digitada
    if nome_cliente and not id_recebido:
        intencao = interpretar_mensagem(mensagem)

        if intencao == "credito":
            enviar_mensagem(numero, "💰 Aqui na Sullato temos opções de crédito facilitado! Me chama que explico como funciona.")
            atualizar_interesse(numero, "Interesse - Crédito")
            registrar_interacao(numero, nome_cliente, "Interesse - Crédito")
            return

        elif intencao == "endereco":
            enviar_mensagem(numero, "📍 Estamos em dois endereços: Av. São Miguel, 7900 e 4049/4084 – São Paulo.")
            atualizar_interesse(numero, "Interesse - Endereço Loja")
            registrar_interacao(numero, nome_cliente, "Interesse - Endereço Loja")
            return

        elif intencao == "comprar":
            enviar_mensagem(numero, "🚗 Temos vans, utilitários e veículos de passeio esperando por você!")
            atualizar_interesse(numero, "Interesse - Comprar")
            registrar_interacao(numero, nome_cliente, "Interesse - Comprar")
            return

        elif intencao == "vender":
            enviar_mensagem(numero, "📢 Estamos prontos pra ajudar você a vender seu veículo com segurança e agilidade.")
            atualizar_interesse(numero, "Interesse - Vender")
            registrar_interacao(numero, nome_cliente, "Interesse - Vender")
            return

        elif intencao == "oficina":
            enviar_mensagem(numero, "🔧 Nossa oficina especializada está pronta pra te atender! Quer agendar uma visita?")
            atualizar_interesse(numero, "Interesse - Oficina")
            registrar_interacao(numero, nome_cliente, "Interesse - Oficina")
            return

        elif intencao == "garantia":
            enviar_mensagem(numero, "🛡️ Conte com nosso suporte! Fale conosco e vamos verificar sua garantia.")
            atualizar_interesse(numero, "Interesse - Garantia")
            registrar_interacao(numero, nome_cliente, "Interesse - Garantia")
            return

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
        registrar_primeiro_interesse(numero, nome_final, "Menu - Compra/Venda")
        registrar_interacao(numero, nome_final, "Menu - Compra/Venda")
        enviar_botoes(numero, "Escolha uma opção de compra/venda:", [
            {"type": "reply", "reply": {"id": "1.1", "title": "Passeio"}},
            {"type": "reply", "reply": {"id": "1.2", "title": "Utilitário"}},
            {"type": "reply", "reply": {"id": "1.3", "title": "Endereço"}}
        ])
        return

    if id_recebido == "2":
        registrar_primeiro_interesse(numero, nome_final, "Menu - Oficina/Peças")
        registrar_interacao(numero, nome_final, "Menu - Oficina/Peças")
        enviar_botoes(numero, "Escolha uma opção sobre oficina/peças:", [
            {"type": "reply", "reply": {"id": "2.1", "title": "Oficina e Peças"}},
            {"type": "reply", "reply": {"id": "2.2", "title": "Endereço Oficina"}}
        ])
        return

    if id_recebido == "mais1":
        registrar_primeiro_interesse(numero, nome_final, "Menu - Mais opções")
        registrar_interacao(numero, nome_final, "Menu - Mais opções")
        enviar_botoes(numero, "Mais opções disponíveis:", [
            {"type": "reply", "reply": {"id": "3", "title": "Crédito"}},
            {"type": "reply", "reply": {"id": "btn-pos-venda", "title": "Pós-venda"}},
            {"type": "reply", "reply": {"id": "mais2", "title": "Mais opções"}}
        ])
        return

    if id_recebido == "mais2":
        registrar_primeiro_interesse(numero, nome_final, "Menu - Outras opções")
        registrar_interacao(numero, nome_final, "Menu - Outras opções")
        enviar_botoes(numero, "Outras opções:", [
            {"type": "reply", "reply": {"id": "4.1", "title": "Governamentais"}},
            {"type": "reply", "reply": {"id": "4.2", "title": "Assinatura"}},
            {"type": "reply", "reply": {"id": "menu", "title": "Voltar ao início"}}
        ])
        return

    if id_recebido == "btn-pos-venda":
        registrar_primeiro_interesse(numero, nome_final, "Menu - Pós-venda")
        registrar_interacao(numero, nome_final, "Menu - Pós-venda")
        enviar_botoes(numero, "Pós-venda Sullato - Escolha uma das opções abaixo:", [
            {"type": "reply", "reply": {"id": "3.2.1", "title": "Passeio"}},
            {"type": "reply", "reply": {"id": "3.2.2", "title": "Utilitário"}},
            {"type": "reply", "reply": {"id": "menu", "title": "Voltar ao início"}}
        ])
        return

    if id_recebido == "1.1":
        registrar_primeiro_interesse(numero, nome_final, "Interesse - Passeio")
        registrar_interacao(numero, nome_final, "Interesse - Passeio")
        enviar_mensagem(numero, blocos["1.1"])
        return

    if id_recebido == "1.2":
        registrar_primeiro_interesse(numero, nome_final, "Interesse - Utilitário")
        registrar_interacao(numero, nome_final, "Interesse - Utilitário")
        enviar_mensagem(numero, blocos["1.2"])
        return

    if id_recebido == "1.3":
        registrar_primeiro_interesse(numero, nome_final, "Interesse - Endereço Loja")
        registrar_interacao(numero, nome_final, "Interesse - Endereço Loja")
        enviar_mensagem(numero, blocos["1.3"])
        return

    if id_recebido == "2.1":
        registrar_primeiro_interesse(numero, nome_final, "Interesse - Oficina e Peças")
        registrar_interacao(numero, nome_final, "Interesse - Oficina e Peças")
        enviar_mensagem(numero, blocos["2.1"])
        return

    if id_recebido == "2.2":
        registrar_primeiro_interesse(numero, nome_final, "Interesse - Endereço Oficina")
        registrar_interacao(numero, nome_final, "Interesse - Endereço Oficina")
        enviar_mensagem(numero, blocos["2.2"])
        return

    if id_recebido == "3":
        registrar_primeiro_interesse(numero, nome_final, "Interesse - Crédito")
        registrar_interacao(numero, nome_final, "Interesse - Crédito")
        enviar_mensagem(numero, blocos["3"])
        return

    if id_recebido == "3.2.1":
        registrar_primeiro_interesse(numero, nome_final, "Interesse - Pós-venda Passeio")
        registrar_interacao(numero, nome_final, "Interesse - Pós-venda Passeio")
        enviar_mensagem(numero, blocos["3.2.1"])
        return

    if id_recebido == "3.2.2":
        registrar_primeiro_interesse(numero, nome_final, "Interesse - Pós-venda Utilitário")
        registrar_interacao(numero, nome_final, "Interesse - Pós-venda Utilitário")
        enviar_mensagem(numero, blocos["3.2.2"])
        return

    if id_recebido == "4.1":
        registrar_primeiro_interesse(numero, nome_final, "Interesse - Governamentais")
        registrar_interacao(numero, nome_final, "Interesse - Governamentais")
        enviar_mensagem(numero, blocos["4.1"])
        return

    if id_recebido == "4.2":
        registrar_primeiro_interesse(numero, nome_final, "Interesse - Assinatura")
        registrar_interacao(numero, nome_final, "Interesse - Assinatura")
        enviar_mensagem(numero, blocos["4.2"])
        return

    enviar_botoes(numero, "Desculpe, não entendi. Escolha uma das opções abaixo:", botoes_menu)
    return
