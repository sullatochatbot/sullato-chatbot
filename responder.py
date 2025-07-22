import requests
import os

# === Carregando variáveis do ambiente ===
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# === Envio de mensagem de texto comum ===
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
        "text": { "body": mensagem }
    }
    response = requests.post(url, headers=headers, json=payload)
    print(f"[TEXTO] Para: {numero} | Status: {response.status_code} | Resposta: {response.text}")

# === Envio de template "boas_vindas" ===
def enviar_template_boas_vindas(numero):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "template",
        "template": {
            "name": "boas_vindas",
            "language": { "code": "pt_BR" },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        { "type": "text", "text": "cliente" }
                    ]
                }
            ]
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    print(f"[TEMPLATE] Para: {numero} | Status: {response.status_code} | Resposta: {response.text}")

# === Função principal que interpreta a mensagem recebida ===
def gerar_resposta(mensagem, numero):
    print(f"\n📩 Mensagem recebida: '{mensagem}' de {numero}")
    texto = mensagem.lower()

    if any(p in texto for p in ["oi", "olá", "bom dia", "boa tarde", "boa noite"]):
        print("➡️ Palavra-chave detectada: saudação")
        enviar_template_boas_vindas(numero)

    elif any(p in texto for p in ["van", "vans", "veículo", "veiculos", "carro", "frota"]):
        resposta = "🚐 Temos vans escolares, de carga e executivas à pronta entrega! Deseja ver nosso catálogo completo?"
        enviar_mensagem(numero, resposta)

    elif any(p in texto for p in ["catálogo", "modelos", "estoque", "ofertas"]):
        resposta = "📘 Você pode acessar nosso catálogo atualizado aqui: [link_do_catalogo]. Qual modelo deseja conhecer melhor?"
        enviar_mensagem(numero, resposta)

    elif any(p in texto for p in ["financiamento", "financeira", "crédito", "score", "entrada"]):
        resposta = "💰 Trabalhamos com aprovação facilitada, mesmo com score baixo! Posso te passar uma simulação sem compromisso?"
        enviar_mensagem(numero, resposta)

    elif any(p in texto for p in ["local", "endereço", "onde fica", "localização", "mapa"]):
        resposta = "📍 Estamos na *Av. Exemplo, 123 - São Paulo/SP*. Deseja receber o link direto do Google Maps?"
        enviar_mensagem(numero, resposta)

    elif any(p in texto for p in ["whatsapp", "vendedor", "atendente", "falar com alguém"]):
        resposta = "📲 Um de nossos especialistas vai te chamar em instantes para atendimento personalizado!"
        enviar_mensagem(numero, resposta)

    elif any(p in texto for p in ["obrigado", "valeu", "agradecido"]):
        resposta = "🙏 Nós que agradecemos! Qualquer dúvida, estamos sempre à disposição."
        enviar_mensagem(numero, resposta)

    else:
        resposta = "📨 Recebemos sua mensagem! Em breve, um dos nossos atendentes entrará em contato para te ajudar melhor."
        enviar_mensagem(numero, resposta)
