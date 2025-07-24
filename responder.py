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
    print("📬 Resposta da Meta:", resposta.status_code, resposta.text)

def gerar_resposta(mensagem, numero):
    texto = mensagem.lower()

    if any(p in texto for p in ["oi", "olá", "bom dia", "boa tarde", "boa noite", "tenho interesse", "estou interessado", "me atende"]):
        resposta = """Olá, aqui quem responde é o atendimento virtual do Grupo Sullato.  
Se você procura por:

1️⃣ Endereço das lojas / site / rede social  
2️⃣ Comprar veículo  
3️⃣ Vender veículo  
4️⃣ Crédito (financiamento ou refinanciamento)  
5️⃣ Oficina ou peças  
6️⃣ Vendas ao governo (prefeituras ou ONGs)  
7️⃣ Pós-venda / Garantia  

Digite uma palavra-chave como: comprar, vender, crédito, garantia, etc."""
        enviar_mensagem(numero, resposta)
        return

    # Item 1 - Endereço
    if any(p in texto for p in ["endereço", "site", "rede social", "instagram", "localização", "loja"]):
        resposta = """📍 Informações da Sullato:

🌐 Site: www.sullato.com.br  
📸 Instagram:  
@sullatomicrosevans  
@sullato.veiculos

🏪 Lojas:  
➡️ Av. São Miguel, 7900 – SP | ☎️ (11) 2030-5081 / (11) 2031-5081  
➡️ Av. São Miguel, 4049 / 4084 – SP | ☎️ (11) 2542-3332 / (11) 2542-3333"""
        enviar_mensagem(numero, resposta)
        return

    # Item 2 - Comprar
    elif "comprar" in texto:
        resposta = "Você deseja comprar um veículo de passeio ou utilitário? Responda com: passeio ou utilitário."
        enviar_mensagem(numero, resposta)
        return

    elif "passeio" in texto and "comprar" in texto or texto.strip() == "passeio":
        resposta = """🚗 Veículos de Passeio

Entre em contato com um de nossos consultores:  
- Alexandre: (11) 91215-5673  
- Jeferson: (11) 94100-6862  
- Marcela: (11) 91215-5673  
- Pedro: (11) 95270-4363  
- Thiago: (11) 98612-2905  
- Vinicius: (11) 91126-0469"""
        enviar_mensagem(numero, resposta)
        return

    elif "utilitário" in texto and "comprar" in texto or texto.strip() == "utilitário":
        resposta = """🚐 Veículos Utilitários

Fale com nossos consultores:  
- Magali: (11) 94021-5082  
- Silvano: (11) 98859-8736  
- Thiago: (11) 98612-2902"""
        enviar_mensagem(numero, resposta)
        return

    # Item 3 - Vender
    elif "vender" in texto:
        resposta = "Você quer vender um veículo de passeio ou utilitário? Responda com: passeio ou utilitário."
        enviar_mensagem(numero, resposta)
        return

    elif "passeio" in texto and "vender" in texto:
        resposta = """🔁 Venda de Veículo de Passeio

Fale com nossos consultores:  
- Alexandre, Jeferson, Marcela, Pedro, Thiago ou Vinicius  
☎️ Mesmos contatos do item 2.1"""
        enviar_mensagem(numero, resposta)
        return

    elif "utilitário" in texto and "vender" in texto:
        resposta = """🔁 Venda de Veículo Utilitário

Fale com nossos consultores:  
- Magali, Silvano ou Thiago  
☎️ Mesmos contatos do item 2.2"""
        enviar_mensagem(numero, resposta)
        return

    # Item 4 - Crédito
    elif any(p in texto for p in ["financiamento", "refinanciamento", "crédito", "score"]):
        resposta = """💰 Crédito / Financiamento

Fale com nosso time de especialistas:  
- Magali: (11) 94021-5082  
- Patricia: (11) 94021-5081"""
        enviar_mensagem(numero, resposta)
        return

    # Item 5 - Oficina e peças
    elif any(p in texto for p in ["oficina", "peças", "mecânica", "conserto"]):
        resposta = """🔧 Oficina e Peças

Entre em contato com nosso time:  
☎️ (11) 2542-3332 / (11) 2542-3333  
- Erico: (11) 94049-7678  
- Leandro: (11) 94044-3566"""
        enviar_mensagem(numero, resposta)
        return

    # Item 6 - Governo
    elif any(p in texto for p in ["governo", "prefeitura", "ong", "entidade", "instituição"]):
        resposta = """🏛️ Vendas ao Governo

Fale com: Lucas, Natan ou Leon  
☎️ (11) 2031-5081 / (11) 2030-5081  
📧 vendasdireta@sullato.com.br"""
        enviar_mensagem(numero, resposta)
        return

    # Item 7 - Pós-venda / Garantia
    elif "garantia" in texto or "pós-venda" in texto or "pos venda" in texto:
        resposta = "Você precisa de garantia para veículo de passeio ou utilitário? Responda com: passeio ou utilitário."
        enviar_mensagem(numero, resposta)
        return

    elif "garantia" in texto and "passeio" in texto or texto.strip() == "passeio":
        resposta = """🛠️ Garantia - Veículo de Passeio

Fale com: Alexandre, Jeferson, Marcela, Pedro, Thiago ou Vinicius  
☎️ Mesmos contatos do item 2.1"""
        enviar_mensagem(numero, resposta)
        return

    elif "garantia" in texto and "utilitário" in texto or texto.strip() == "utilitário":
        resposta = """🛠️ Garantia - Veículo Utilitário

Fale com: Magali, Silvano ou Thiago  
☎️ Mesmos contatos do item 2.2"""
        enviar_mensagem(numero, resposta)
        return

    # Default
    else:
        resposta = """Desculpe, não entendi sua mensagem.  
Por favor, digite uma das palavras-chave abaixo:

- comprar  
- vender  
- crédito  
- oficina  
- endereço  
- garantia  
- governo"""
        enviar_mensagem(numero, resposta)
