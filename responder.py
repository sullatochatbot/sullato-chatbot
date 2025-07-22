import requests
import os

# Pegando dados de ambiente (já devem estar no .env ou no sistema)
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# Função para enviar a mensagem para o WhatsApp do cliente
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
    print("Resposta da Meta:", response.status_code, response.text)

# Função principal do responder.py
def gerar_resposta(mensagem, numero):
    texto = mensagem.lower()

    if any(palavra in texto for palavra in ["oi", "olá", "bom dia", "boa tarde", "boa noite"]):
        resposta = "👋 Olá! A *Sullato Micros e Vans* agradece o seu contato. Em que podemos te ajudar hoje?"
        enviar_mensagem(numero, resposta)

    elif any(palavra in texto for palavra in ["van", "vans", "veículo", "veiculos", "carro", "frota"]):
        resposta = "🚐 Temos vans escolares, de carga e executivas à pronta entrega! Deseja ver nosso catálogo completo?"
        enviar_mensagem(numero, resposta)

    elif any(palavra in texto for palavra in ["catálogo", "modelos", "estoque", "ofertas"]):
        resposta = "📘 Você pode acessar nosso catálogo atualizado aqui: [link_do_catalogo]. Qual modelo deseja conhecer melhor?"
        enviar_mensagem(numero, resposta)

    elif any(palavra in texto for palavra in ["financiamento", "financeira", "crédito", "score", "entrada"]):
        resposta = "💰 Trabalhamos com aprovação facilitada, mesmo com score baixo! Posso te passar uma simulação sem compromisso?"
        enviar_mensagem(numero, resposta)

    elif any(palavra in texto for palavra in ["local", "endereço", "onde fica", "localização", "mapa"]):
        resposta = "📍 Estamos na *Av. Exemplo, 123 - São Paulo/SP*. Deseja receber o link direto do Google Maps?"
        enviar_mensagem(numero, resposta)

    elif any(palavra in texto for palavra in ["whatsapp", "vendedor", "atendente", "falar com alguém"]):
        resposta = "📲 Um de nossos especialistas vai te chamar em instantes para atendimento personalizado!"
        enviar_mensagem(numero, resposta)

    elif any(palavra in texto for palavra in ["obrigado", "valeu", "agradecido"]):
        resposta = "🙏 Nós que agradecemos! Qualquer dúvida, estamos sempre à disposição."
        enviar_mensagem(numero, resposta)

    else:
        resposta = "📨 Recebemos sua mensagem! Em breve, um dos nossos atendentes entrará em contato para te ajudar melhor."
        enviar_mensagem(numero, resposta)
