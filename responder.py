import requests
import os
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")


def enviar_mensagem(numero, texto):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
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


def gerar_resposta(mensagem, numero):
    texto = mensagem.lower().strip()

    blocos = {
        "1": """📍 *Informações da Sullato*

🌐 Site: [www.sullato.com.br](https://www.sullato.com.br)

📸 Instagram:
@sullatomicrosevans – [Ver perfil](https://www.instagram.com/sullatomicrosevans)  
@sullato.veiculos – [Ver perfil](https://www.instagram.com/sullato.veiculos)

🏢 Lojas:
➡️ Sullato Micros e Vans  
Av. São Miguel, 7900 – São Paulo/SP  
📞 (11) 2030-5081 / (11) 2031-5081

➡️ Sullato Veículos  
Av. São Miguel, 4049 / 4084 – São Paulo/SP  
📞 (11) 2542-3332 / (11) 2542-3333""",

        "2": "Digite 2.1 para *veículo de passeio* ou 2.2 para *utilitário*",

        "2.1": """🚗 *Compra – Veículo de Passeio*
Alexandre: 📲 https://wa.me/5511940559880
Jeferson: 📲 https://wa.me/5511941006862
Marcela: 📲 https://wa.me/5511912115673
Pedro: 📲 https://wa.me/5511952704363
Thiago: 📲 https://wa.me/5511986122905
Vinicius: 📲 https://wa.me/5511911260469""",

        "2.2": """🚐 *Compra – Veículo Utilitário*
Magali: 📲 https://wa.me/5511940215082
Silvano: 📲 https://wa.me/5511988598736
Thiago: 📲 https://wa.me/5511986122902""",

        "3": "Digite 3.1 para *vender veículo de passeio* ou 3.2 para *vender utilitário*",

        "3.1": """🔁 *Venda – Veículo de Passeio*
Alexandre: 📲 https://wa.me/5511940559880
Jeferson: 📲 https://wa.me/5511941006862
Marcela: 📲 https://wa.me/5511912115673
Pedro: 📲 https://wa.me/5511952704363
Thiago: 📲 https://wa.me/5511986122905
Vinicius: 📲 https://wa.me/5511911260469""",

        "3.2": """🔁 *Venda – Veículo Utilitário*
Magali: 📲 https://wa.me/5511940215082
Silvano: 📲 https://wa.me/5511988598736
Thiago: 📲 https://wa.me/5511986122902""",

        "4": """💰 *Crédito / Financiamento*
Magali: 📲 https://wa.me/5511940215082
Patricia: 📲 https://wa.me/5511940215081""",

        "5": """🔧 *Oficina / Peças*
Erico: 📲 https://wa.me/5511940497678
Leandro: 📲 https://wa.me/5511940443566
📞 Fixo: (11) 2542-3332 / (11) 2542-3333""",

        "6": """🏛️ *Vendas ao Governo*
Lucas / Natan / Leon: 📞 (11) 2031-5081 / (11) 2030-5081
📧 vendasdireta@sullato.com.br""",

        "7": "Digite 7.1 para *garantia de passeio* ou 7.2 para *garantia utilitário*",

        "7.1": """🛡️ *Garantia – Veículo de Passeio*
Alexandre: 📲 https://wa.me/5511940559880
Jeferson: 📲 https://wa.me/5511941006862
Marcela: 📲 https://wa.me/5511912115673
Pedro: 📲 https://wa.me/5511952704363
Thiago: 📲 https://wa.me/5511986122905
Vinicius: 📲 https://wa.me/5511911260469""",

        "7.2": """🛡️ *Garantia – Veículo Utilitário*
Magali: 📲 https://wa.me/5511940215082
Silvano: 📲 https://wa.me/5511988598736
Thiago: 📲 https://wa.me/5511986122902"""
    }

    atalhos = {
        "site": "1", "endereço": "1", "instagram": "1", "loja": "1",
        "comprar passeio": "2.1", "comprar utilitário": "2.2",
        "vender passeio": "3.1", "vender utilitário": "3.2",
        "credito": "4", "financiamento": "4", "score": "4",
        "oficina": "5", "peças": "5",
        "venda direta": "6", "prefeitura": "6", "ong": "6",
        "garantia passeio": "7.1", "garantia utilitário": "7.2"
    }

    if texto in blocos:
        enviar_mensagem(numero, blocos[texto])
        return

    for chave, cod in atalhos.items():
        if all(p in texto for p in chave.split()):
            enviar_mensagem(numero, blocos[cod])
            return

    # Se for saudação ou qualquer outro texto não reconhecido, envia o menu
    menu = (
        "Olá! 👋\nEu sou o atendimento virtual da Sullato.\n"
        "Digite o número da opção desejada:\n"
        "1 – Endereço e redes sociais\n"
        "2 – Comprar\n"
        "3 – Vender\n"
        "4 – Crédito\n"
        "5 – Oficina\n"
        "6 – Governo\n"
        "7 – Garantia"
    )
    enviar_mensagem(numero, menu)
