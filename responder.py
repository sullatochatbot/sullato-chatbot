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

def gerar_resposta(mensagem):
    texto = mensagem.lower().strip()

    saudacoes = ["oi", "olá", "ola", "van", "utilitário", "leve", "passeio", "carro", "interesse", "comprar", "vender", "score", "financiamento", "refinanciamento", "credito", "peças", "oficina", "sullato"]
    if any(p in texto for p in saudacoes):
        return (
            "Olá, aqui quem responde é o atendimento virtual do Grupo Sullato.\n\n"
            "Digite o número da opção desejada:\n"
            "1 – Endereço das lojas, site, redes sociais\n"
            "2 – Comprar\n"
            "3 – Vender\n"
            "4 – Crédito / Financiamento\n"
            "5 – Oficina e Peças\n"
            "6 – Vendas ao Governo\n"
            "7 – Pós-venda / Garantia"
        )

    if texto == "1":
        return (
            "📍 *Endereços e Contatos Sullato*\n\n"
            "🔗 *Site:* https://www.sullato.com.br\n"
            "📸 *Instagram:*\n"
            "@sullatomicrosevans – https://www.instagram.com/sullatomicrosevans\n"
            "@sullato.veiculos – https://www.instagram.com/sullato.veiculos\n\n"
            "🏢 *Lojas:*\n"
            "Sullato Micros e Vans – Av. São Miguel, 7900 – SP\n"
            "(11) 2030-5081 / (11) 2031-5081\n\n"
            "Sullato Veículos – Av. São Miguel, 4049 / 4084 – SP\n"
            "(11) 2542-3332 / (11) 2542-3333"
        )

    if texto == "2":
        return "2 – Comprar Veículo\nDigite:\n- 2.1 para *veículo de passeio*\n- 2.2 para *veículo utilitário*"
    if texto == "2.1":
        return (
            "🚗 *Compra – Veículo de Passeio*\nEntre em contato com:\n\n"
            "Alexandre – https://wa.me/5511912155673\n"
            "Jeferson – https://wa.me/5511941006862\n"
            "Marcela – https://wa.me/5511912155673\n"
            "Pedro – https://wa.me/5511952704363\n"
            "Thiago – https://wa.me/5511986122905\n"
            "Vinicius – https://wa.me/5511911260469"
        )
    if texto == "2.2":
        return (
            "🚐 *Compra – Veículo Utilitário*\nFale com:\n\n"
            "Magali – https://wa.me/5511940215082\n"
            "Silvano – https://wa.me/5511988598736\n"
            "Thiago – https://wa.me/5511986122902"
        )

    if texto == "3":
        return "3 – Vender Veículo\nDigite:\n- 3.1 para *veículo de passeio*\n- 3.2 para *veículo utilitário*"
    if texto == "3.1":
        return (
            "📤 *Venda – Veículo de Passeio*\nFale com:\n\n"
            "Alexandre – https://wa.me/5511912155673\n"
            "Jeferson – https://wa.me/5511941006862\n"
            "Marcela – https://wa.me/5511912155673\n"
            "Pedro – https://wa.me/5511952704363\n"
            "Thiago – https://wa.me/5511986122905\n"
            "Vinicius – https://wa.me/5511911260469"
        )
    if texto == "3.2":
        return (
            "📤 *Venda – Veículo Utilitário*\nFale com:\n\n"
            "Magali – https://wa.me/5511940215082\n"
            "Silvano – https://wa.me/5511988598736\n"
            "Thiago – https://wa.me/5511986122902"
        )

    if texto == "4":
        return (
            "💳 *Crédito / Financiamento*\nFale com:\n\n"
            "Magali – https://wa.me/5511940215082\n"
            "Patricia – https://wa.me/5511940215081"
        )

    if texto == "5":
        return (
            "🛠️ *Oficina e Peças*\nFale com:\n\n"
            "(11) 2542-3332 / (11) 2542-3333\n"
            "Érico – https://wa.me/5511940497678\n"
            "Leandro – https://wa.me/5511940443566"
        )

    if texto == "6":
        return (
            "🏛️ *Vendas ao Governo*\nFale com:\n\n"
            "Lucas / Natan / Leon – (11) 2031-5081 / (11) 2030-5081\n"
            "📧 vendasdireta@sullato.com.br"
        )

    if texto == "7":
        return "7 – Pós-venda / Garantia\nDigite:\n- 7.1 para *veículo de passeio*\n- 7.2 para *veículo utilitário*"
    if texto == "7.1":
        return (
            "🛡️ *Garantia – Veículo de Passeio*\nFale com:\n\n"
            "Alexandre – https://wa.me/5511912155673\n"
            "Jeferson – https://wa.me/5511941006862\n"
            "Marcela – https://wa.me/5511912155673\n"
            "Pedro – https://wa.me/5511952704363\n"
            "Thiago – https://wa.me/5511986122905\n"
            "Vinicius – https://wa.me/5511911260469"
        )
    if texto == "7.2":
        return (
            "🛡️ *Garantia – Veículo Utilitário*\nFale com:\n\n"
            "Magali – https://wa.me/5511940215082\n"
            "Silvano – https://wa.me/5511988598736\n"
            "Thiago – https://wa.me/5511986122902"
        )

    return "❌ Desculpe, não entendi. Por favor, digite um número válido entre 1 e 7."

# 👇 ESTA PARTE É FUNDAMENTAL PARA FUNCIONAR
def responder(numero, mensagem):
    resposta = gerar_resposta(mensagem)
    enviar_mensagem(numero, resposta)
