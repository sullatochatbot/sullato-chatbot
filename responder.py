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

    # MENU PRINCIPAL por número
    if texto == "1":
        resposta = """📍 Informações da Sullato:

🌐 Site: www.sullato.com.br  
📸 Instagram:  
@sullatomicrosevans  
@sullato.veiculos

🏪 Lojas:  
➡️ Sullato Micros e Vans  
Av. São Miguel, 7900 – SP  
📞 (11) 2030-5081 / (11) 2031-5081

➡️ Sullato Veículos  
Av. São Miguel, 4049 / 4084 – SP  
📞 (11) 2542-3332 / (11) 2542-3333"""
        enviar_mensagem(numero, resposta)
        return

    elif texto == "2":
        resposta = "2 – Comprar Veículo\nDigite:\n- 2.1 para *veículo de passeio*\n- 2.2 para *veículo utilitário*"
        enviar_mensagem(numero, resposta)
        return

    elif texto == "2.1":
        resposta = """🚗 Veículos de Passeio

Entre em contato com um de nossos consultores:  
Alexandre: (11) 91215-5673  
Jeferson: (11) 94100-6862  
Marcela: (11) 91215-5673  
Pedro: (11) 95270-4363  
Thiago: (11) 98612-2905  
Vinicius: (11) 91126-0469"""
        enviar_mensagem(numero, resposta)
        return

    elif texto == "2.2":
        resposta = """🚐 Veículos Utilitários

Entre em contato com um de nossos consultores:  
Magali: (11) 94021-5082  
Silvano: (11) 98859-8736  
Thiago: (11) 98612-2902"""
        enviar_mensagem(numero, resposta)
        return

    elif texto == "3":
        resposta = "3 – Vender Veículo\nDigite:\n- 3.1 para *veículo de passeio*\n- 3.2 para *veículo utilitário*"
        enviar_mensagem(numero, resposta)
        return

    elif texto == "3.1":
        resposta = """🔁 Venda de Veículo de Passeio

Fale com nossos consultores:  
Alexandre: (11) 91215-5673  
Jeferson: (11) 94100-6862  
Marcela: (11) 91215-5673  
Pedro: (11) 95270-4363  
Thiago: (11) 98612-2905  
Vinicius: (11) 91126-0469"""
        enviar_mensagem(numero, resposta)
        return

    elif texto == "3.2":
        resposta = """🔁 Venda de Veículo Utilitário

Fale com nossos consultores:  
Magali: (11) 94021-5082  
Silvano: (11) 98859-8736  
Thiago: (11) 98612-2902"""
        enviar_mensagem(numero, resposta)
        return

    elif texto == "4":
        resposta = """💰 Crédito / Financiamento

Fale com nossos especialistas:  
Magali: (11) 94021-5082  
Patricia: (11) 94021-5081"""
        enviar_mensagem(numero, resposta)
        return

    elif texto == "5":
        resposta = """🔧 Oficina / Peças

Entre em contato com nosso time:  
📞 (11) 2542-3332 / (11) 2542-3333  
Erico: (11) 94049-7678  
Leandro: (11) 94044-3566"""
        enviar_mensagem(numero, resposta)
        return

    elif texto == "6":
        resposta = """🏛️ Vendas ao Governo

Lucas, Natan ou Leon  
📞 (11) 2031-5081 / (11) 2030-5081  
📧 vendasdireta@sullato.com.br"""
        enviar_mensagem(numero, resposta)
        return

    elif texto == "7":
        resposta = "7 – Pós-venda / Garantia\nDigite:\n- 7.1 para *veículo de passeio*\n- 7.2 para *veículo utilitário*"
        enviar_mensagem(numero, resposta)
        return

    elif texto == "7.1":
        resposta = """🛠️ Garantia Veículo de Passeio

Fale com nossos consultores:  
Alexandre: (11) 91215-5673  
Jeferson: (11) 94100-6862  
Marcela: (11) 91215-5673  
Pedro: (11) 95270-4363  
Thiago: (11) 98612-2905  
Vinicius: (11) 91126-0469"""
        enviar_mensagem(numero, resposta)
        return

    elif texto == "7.2":
        resposta = """🛠️ Garantia Veículo Utilitário

Fale com nossos consultores:  
Magali: (11) 94021-5082  
Silvano: (11) 98859-8736  
Thiago: (11) 98612-2902"""
        enviar_mensagem(numero, resposta)
        return

    # Gatilhos por PALAVRAS
    elif any(p in texto for p in ["endereço", "site", "redes sociais", "instagram", "localização", "loja"]):
        return gerar_resposta("1", numero)

    elif "comprar" in texto or "quero comprar" in texto or "interesse" in texto:
        if "passeio" in texto:
            return gerar_resposta("2.1", numero)
        elif "utilitário" in texto or "van" in texto or "carga" in texto:
            return gerar_resposta("2.2", numero)
        else:
            resposta = "Você quer comprar um veículo de passeio ou utilitário?"
            enviar_mensagem(numero, resposta)
            return

    elif "vender" in texto:
        if "passeio" in texto:
            return gerar_resposta("3.1", numero)
        elif "utilitário" in texto or "van" in texto:
            return gerar_resposta("3.2", numero)
        else:
            resposta = "Você quer vender um veículo de passeio ou utilitário?"
            enviar_mensagem(numero, resposta)
            return

    elif "financiamento" in texto or "refinanciamento" in texto or "credito" in texto or "score" in texto:
        return gerar_resposta("4", numero)

    elif "oficina" in texto or "peças" in texto:
        return gerar_resposta("5", numero)

    elif "governo" in texto or "prefeitura" in texto or "ong" in texto:
        return gerar_resposta("6", numero)

    elif "garantia" in texto or "pós-venda" in texto or "pos venda" in texto:
        if "passeio" in texto:
            return gerar_resposta("7.1", numero)
        elif "utilitário" in texto:
            return gerar_resposta("7.2", numero)
        else:
            resposta = "Você está com dúvida sobre a garantia de um veículo de passeio ou utilitário?"
            enviar_mensagem(numero, resposta)
            return

    elif any(p in texto for p in ["oi", "olá", "bom dia", "boa tarde", "boa noite"]):
        resposta = """Olá! 👋  
Eu sou o atendimento virtual da Sullato.  
Me diga com o que você precisa de ajuda:  
🔹 Comprar  
🔹 Vender  
🔹 Financiamento  
🔹 Oficina  
🔹 Garantia  
🔹 Endereço  
🔹 Governo"""
        enviar_mensagem(numero, resposta)
        return

    else:
        resposta = "Desculpe, não entendi sua mensagem. Poderia reformular ou escolher uma das opções: Comprar, Vender, Financiamento, Oficina, Garantia, Endereço ou Governo."
        enviar_mensagem(numero, resposta)
        return
