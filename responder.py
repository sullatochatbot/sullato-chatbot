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
    print("\U0001F4EC Resposta da Meta:", resposta.status_code, resposta.text)

def gerar_resposta(mensagem, numero):
    texto = mensagem.lower().strip()

    if texto in ["1", "endereco", "endereço", "site", "instagram", "rede social"]:
        resposta = """\U0001F4CD *Endereços e Contatos Sullato*

\U0001F310 *Site:* https://www.sullato.com.br
\U0001F4F7 *Instagram:* 
@sullatomicrosevans – https://www.instagram.com/sullatomicrosevans
@sullato.veiculos – https://www.instagram.com/sullato.veiculos

\U0001F3EA *Lojas:*
\u27a1️ *Sullato Micros e Vans* – Av. São Miguel, 7900 – SP  
\u260e️ (11) 2030-5081 / (11) 2031-5081

\u27a1️ *Sullato Veículos* – Av. São Miguel, 4049 / 4084 – SP  
\u260e️ (11) 2542-3332 / (11) 2542-3333"""
        enviar_mensagem(numero, resposta)
        return

    elif texto == "2":
        resposta = """*2 – Comprar Veículo*
Digite:
- 2.1 para *veículo de passeio*  
- 2.2 para *veículo utilitário*"""
        enviar_mensagem(numero, resposta)
        return

    elif texto == "2.1":
        resposta = """\U0001F697 *Compra – Veículo de Passeio*

Entre em contato com um de nossos consultores:

👨‍💼 *Alexandre* – [📲 WhatsApp](https://wa.me/5511912155673)
👨‍💼 *Jeferson* – [📲 WhatsApp](https://wa.me/5511941006862)
👩‍💼 *Marcela* – [📲 WhatsApp](https://wa.me/5511912155673)
👨‍💼 *Pedro* – [📲 WhatsApp](https://wa.me/5511952704363)
👨‍💼 *Thiago* – [📲 WhatsApp](https://wa.me/5511986122905)
👨‍💼 *Vinicius* – [📲 WhatsApp](https://wa.me/5511911260469)"""
        enviar_mensagem(numero, resposta)
        return

    elif texto == "2.2":
        resposta = """\U0001F69A *Compra – Veículo Utilitário*

Fale com nossos consultores:

👩‍💼 *Magali* – [📲 WhatsApp](https://wa.me/5511940215082)
👨‍💼 *Silvano* – [📲 WhatsApp](https://wa.me/5511988598736)
👨‍💼 *Thiago* – [📲 WhatsApp](https://wa.me/5511986122902)"""
        enviar_mensagem(numero, resposta)
        return

    # Continuarei a partir do item 3 (venda), 4 (crédito), etc., no mesmo padrão
    # Quando quiser, posso completar do 3 ao 7.2 com todos os contatos no mesmo estilo

    elif texto in ["oi", "olá", "bom dia", "boa tarde", "boa noite"]:
        resposta = """Olá, aqui quem responde é o atendimento virtual do Grupo Sullato.

Digite o número da opção desejada:
1 – Endereço das lojas, site, redes sociais
2 – Comprar
3 – Vender
4 – Crédito / Financiamento
5 – Oficina e Peças
6 – Vendas ao Governo
7 – Pós-venda / Garantia"""
        enviar_mensagem(numero, resposta)
        return

    else:
        resposta = "Desculpe, não entendi. Por favor, digite um número entre 1 e 7 para que eu possa te ajudar."
        enviar_mensagem(numero, resposta)
