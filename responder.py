import requests
import os

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

def enviar_mensagem(numero, mensagem):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": mensagem}
    }
    response = requests.post(url, headers=headers, json=payload)
    print(f"[TEXTO] Para: {numero} | Status: {response.status_code} | Resposta: {response.text}")

def gerar_resposta(mensagem, numero):
    texto = mensagem.lower().strip()
    print(f"\n📩 Mensagem recebida: '{texto}' de {numero}")

    if any(p in texto for p in ["oi", "olá", "ola", "tenho interesse", "quero comprar", "preciso de financiamento", "score", "vocês estão comprando", "vocês só vendem", "preciso de peças", "ajuda"]):
        resposta = (
            "Olá, aqui quem responde é o atendimento virtual do Grupo Sullato. Se você procura por:\n\n"
            "1 – Endereço das lojas, site, redes sociais\n"
            "2 – Comprar\n"
            "3 – Vender\n"
            "4 – Crédito (financiamento / refinanciamento)\n"
            "5 – Oficina e peças\n"
            "6 – Vendas ao Governo (prefeituras, ONGs)\n"
            "7 – Pós-venda / Garantia\n\n"
            "Digite o número da opção desejada para continuar."
        )

    elif texto == "1":
        resposta = (
            "🌐 Site: www.sullato.com.br\n"
            "📸 Instagram:\n"
            "• Sullato Micros e Vans: @sullatomicrosevans\n"
            "• Sullato Veículos: @sullato.veiculos\n\n"
            "📍 Lojas:\n"
            "• Loja 01: Av. São Miguel, 7900 – SP  (11) 2030-5081 / (11) 2031-5081\n"
            "• Loja 02/03: Av. São Miguel, 4049 / 4084 – SP  (11) 2542-3332 / (11) 2542-3333"
        )

    elif texto == "2":
        resposta = "Você deseja comprar:\n2.1 – Veículo passeio\n2.2 – Veículo utilitário"

    elif texto == "2.1":
        resposta = (
            "🚗 Veículo passeio – Fale com nossos consultores:\n"
            "• Alexandre: (11) 91215-5673\n• Jeferson: (11) 94100-6862\n• Marcela: (11) 91215-5673\n"
            "• Pedro: (11) 95270-4363\n• Thiago: (11) 98612-2905\n• Vinicius: (11) 91126-0469"
        )

    elif texto == "2.2":
        resposta = (
            "🚐 Veículo utilitário – Fale com nossos consultores:\n"
            "• Magali: (11) 94021-5082\n• Silvano: (11) 98859-8736\n• Thiago: (11) 98612-2902"
        )

    elif texto == "3":
        resposta = "Você deseja vender:\n3.1 – Veículo passeio\n3.2 – Veículo utilitário"

    elif texto == "3.1":
        resposta = (
            "📤 Venda de passeio – Fale com nossos consultores:\n"
            "• Alexandre: (11) 91215-5673\n• Jeferson: (11) 94100-6862\n• Marcela: (11) 91215-5673\n"
            "• Pedro: (11) 95270-4363\n• Thiago: (11) 98612-2905\n• Vinicius: (11) 91126-0469"
        )

    elif texto == "3.2":
        resposta = (
            "📤 Venda de utilitário – Fale com nossos consultores:\n"
            "• Magali: (11) 94021-5082\n• Silvano: (11) 98859-8736\n• Thiago: (11) 98612-2902"
        )

    elif texto == "4":
        resposta = (
            "💳 Crédito (financiamento ou refinanciamento):\n"
            "• Magali: (11) 94021-5082\n• Patricia: (11) 94021-5081"
        )

    elif texto == "5":
        resposta = (
            "🔧 Oficina e Peças:\n"
            "• Fone: (11) 2542-3332 / (11) 2542-3333\n"
            "• Érico: (11) 94049-7678\n• Leandro: (11) 94044-3566"
        )

    elif texto == "6":
        resposta = (
            "🏛️ Vendas ao Governo:\n"
            "• Lucas, Natan, Leon: (11) 2031-5081 / (11) 2030-5081\n"
            "• Email: vendasdireta@sullato.com.br"
        )

    elif texto == "7":
        resposta = "Você precisa de pós-venda para:\n5.1 – Veículo passeio\n5.2 – Veículo utilitário"

    elif texto == "5.1":
        resposta = (
            "✅ Pós-venda passeio – Consultores:\n"
            "• Alexandre: (11) 91215-5673\n• Jeferson: (11) 94100-6862\n• Marcela: (11) 91215-5673\n"
            "• Pedro: (11) 95270-4363\n• Thiago: (11) 98612-2905\n• Vinicius: (11) 91126-0469"
        )

    elif texto == "5.2":
        resposta = (
            "✅ Pós-venda utilitário – Consultores:\n"
            "• Magali: (11) 94021-5082\n• Silvano: (11) 98859-8736\n• Thiago: (11) 98612-2902"
        )

    else:
        resposta = (
            "🤖 Não entendi exatamente o que você deseja.\n"
            "Digite 'menu' ou envie o número de uma das opções acima para continuar 😉"
        )

    enviar_mensagem(numero, resposta)
