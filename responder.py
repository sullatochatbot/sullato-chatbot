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

    # === Detecção por intenção (palavras-chave)
    if any(p in texto for p in ["score", "negativado", "nome sujo", "crédito", "credito", "preciso de ajuda", "será que consigo"]):
        resposta = (
            "📑 Mesmo com score baixo, conseguimos analisar seu perfil!\n"
            "Trabalhamos com bancos parceiros que consideram mais do que apenas o score.\n\n"
            "📌 Para começar a análise, por favor envie:\n"
            "• Nome completo\n• CPF\n• Possui CNH? (sim ou não)\n• Categoria da CNH\n"
            "• Data de nascimento\n• Possui entrada disponível?\n\n"
            "Se você tem restrição no nome ou está sem entrada:\n"
            "🙏 Nós entendemos. Muitas pessoas começam exatamente assim.\n"
            "Vamos juntos encontrar uma solução pra te ajudar a trabalhar com dignidade!\n\n"
            "Fale direto com o *Departamento de Crédito*:\n"
            "🧾 Patrícia – 📲 https://wa.me/5511940215081"
        )
        enviar_mensagem(numero, resposta)

    elif any(p in texto for p in ["comprar", "entrada", "financiamento", "carro", "van", "utilitário", "passeio", "executiva", "escolar", "trabalhar com transporte"]):
        resposta = (
            "🚗 Show! Vamos te ajudar a escolher o veículo ideal. Temos vans, carros de passeio, escolares, executivos e para carga.\n\n"
            "❓ Qual o ano e faixa de valor que você procura?\n"
            "💵 Vai pagar à vista ou precisa de financiamento?\n"
            "🚘 Tem entrada em dinheiro ou veículo na troca?\n\n"
            "🌐 Acesse nosso site: https://www.sullato.com.br\n"
            "📸 Instagram: @sullatomicrosevans\n\n"
            "Fale agora com nosso *Departamento de Vendas*:\n"
            "🧑‍💼 Vinícius – 📲 https://wa.me/5511911260469\n"
            "🧑‍💼 Pedro – 📲 https://wa.me/5511952704363\n"
            "🧑‍💼 Alexandre – 📲 https://wa.me/5511940559880\n"
            "🧑‍💼 Marcela – 📲 https://wa.me/5511912155673\n"
            "🧑‍💼 Vanessa – 📲 https://wa.me/5511973454378\n"
            "🧑‍💼 Alex – 📲 https://wa.me/5511996371559\n"
            "🧑‍💼 Thiago – 📲 https://wa.me/5511986122905\n"
            "🧑‍💼 Jeferson – 📲 https://wa.me/5511941006862"
        )
        enviar_mensagem(numero, resposta)

    # === Menu inicial
    elif any(p in texto for p in ["menu", "começar", "opções", "ajuda", "começo", "ola", "oi", "bom dia", "boa noite", "boa tarde", "saiba mais"]):
        resposta = (
            "👋 Olá, aqui quem responde é o atendimento virtual do Grupo Sullato.\n"
            "Se você procura por:\n\n"
            "1 – Endereço das lojas, site, redes sociais\n"
            "2 – Comprar\n"
            "3 – Vender\n"
            "4 – Crédito (financiamento / refinanciamento)\n"
            "5 – Oficina e peças\n"
            "6 – Vendas ao Governo (prefeituras, ONGs)\n"
            "7 – Pós-venda / Garantia\n\n"
            "Por favor, envie o número da opção desejada."
        )
        enviar_mensagem(numero, resposta)

    # === Menu numérico detalhado
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
        resposta = "Você deseja comprar:\n1 – Veículo de passeio\n2 – Veículo utilitário"

    elif texto in ["2.1", "1 - passeio"]:
        resposta = (
            "🚗 Compra de veículo passeio:\n"
            "• Alexandre: (11) 91215-5673\n• Jeferson: (11) 94100-6862\n"
            "• Marcela: (11) 91215-5673\n• Pedro: (11) 95270-4363\n"
            "• Thiago: (11) 98612-2905\n• Vinicius: (11) 91126-0469"
        )

    elif texto in ["2.2", "2 - utilitário"]:
        resposta = (
            "🚐 Compra de utilitário:\n"
            "• Magali: (11) 94021-5082\n• Silvano: (11) 98859-8736\n• Thiago: (11) 98612-2902"
        )

    elif texto == "3":
        resposta = "Você deseja vender:\n1 – Veículo de passeio\n2 – Veículo utilitário"

    elif texto == "3.1":
        resposta = (
            "📤 Venda de passeio:\n"
            "• Alexandre: (11) 91215-5673\n• Jeferson: (11) 94100-6862\n"
            "• Marcela: (11) 91215-5673\n• Pedro: (11) 95270-4363\n"
            "• Thiago: (11) 98612-2905\n• Vinicius: (11) 91126-0469"
        )

    elif texto == "3.2":
        resposta = (
            "📤 Venda de utilitário:\n"
            "• Magali: (11) 94021-5082\n• Silvano: (11) 98859-8736\n• Thiago: (11) 98612-2902"
        )

    elif texto == "4":
        resposta = (
            "💳 Crédito / financiamento:\n"
            "• Magali: (11) 94021-5082\n• Patricia: (11) 94021-5081"
        )

    elif texto == "5":
        resposta = (
            "🔧 Oficina e peças:\n"
            "• Fone: (11) 2542-3332 / (11) 2542-3333\n"
            "• Érico: (11) 94049-7678\n• Leandro: (11) 94044-3566"
        )

    elif texto == "6":
        resposta = (
            "🏛️ Vendas ao Governo:\n"
            "• Sandra: (11) 2031-5081 / (11) 2030-5081\n"
            "• Email: vendasdireta@sullato.com.br"
        )

    elif texto == "7":
        resposta = "Você precisa de pós-venda para:\n1 – Veículo de passeio\n2 – Veículo utilitário"

    elif texto == "7.1":
        resposta = (
            "✅ Pós-venda passeio:\n"
            "• Alexandre: (11) 91215-5673\n• Jeferson: (11) 94100-6862\n"
            "• Marcela: (11) 91215-5673\n• Pedro: (11) 95270-4363\n"
            "• Thiago: (11) 98612-2905\n• Vinicius: (11) 91126-0469"
        )

    elif texto == "7.2":
        resposta = (
            "✅ Pós-venda utilitário:\n"
            "• Magali: (11) 94021-5082\n• Silvano: (11) 98859-8736\n• Thiago: (11) 98612-2902"
        )

    else:
        resposta = (
            "🤖 Não entendi exatamente o que você deseja.\n"
            "Digite 'menu' para ver as opções ou envie com outras palavras. 😉"
        )

    enviar_mensagem(numero, resposta)
