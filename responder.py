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

    # === Score Baixo / Crédito
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

    # === Compra / Interesse em veículos
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

    # === Menu inicial genérico
    elif any(p in texto for p in ["menu", "começar", "opções", "ajuda", "começo", "ola", "oi", "bom dia", "boa noite", "boa tarde"]):
        resposta = (
            "👋 Olá! Seja bem-vindo à Sullato Micros e Vans.\n\n"
            "Escolha uma das opções abaixo para continuar:\n"
            "1️⃣ Comprar um veículo\n"
            "2️⃣ Vender ou consignar um veículo\n"
            "3️⃣ Tenho score baixo e preciso de ajuda\n\n"
            "Ou escreva com suas palavras o que você procura 😉"
        )
        enviar_mensagem(numero, resposta)

    # === Caso não identifique
    else:
        resposta = (
            "🤖 Não entendi exatamente o que você deseja, mas posso te ajudar com:\n"
            "👉 Comprar, vender, financiar, trabalhar ou saber sobre a loja.\n"
            "Me diga com outras palavras e vamos conversar! 😉"
        )
        enviar_mensagem(numero, resposta)
