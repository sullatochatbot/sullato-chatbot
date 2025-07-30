from flask import Flask, request
import requests
from responder import gerar_resposta  # import corrigido

app = Flask(__name__)

# DADOS DE CONFIGURAÇÃO
VERIFY_TOKEN = "sullato_token"
ACCESS_TOKEN = "EACPL2cB7rI8BO1CC1AAfK9PsOieqKhtSWDGOSioZBFpWGG3SDDWkWV6BH5frQvVeEY92NVKIJau5ZAES9V4aF7ClNnbQdop90ULBEH8wrh42OgwaNUMSiewJlkuXPSbNb198U71XfJAc9fH4RlsXr5BK6udjw1bz4Ck4Dp0JIeke3zgFR0SdMCvRK06ecrZCbbL1FDywDtMp6BZAAd6yeVOaZBa6vCDmu5yEv1TzPYBp7ijRn4SsA6jZBi"
PHONE_NUMBER_ID = "684523561413203"
API_URL = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

# ROTA DE VERIFICAÇÃO (GET)
@app.route("/webhook", methods=["GET"])
def verificar():
    verify_token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if verify_token == VERIFY_TOKEN:
        print("✅ Verificação do webhook confirmada!")
        return str(challenge), 200
    else:
        print("❌ Verificação do webhook falhou.")
        return "Erro de verificação", 403

# ROTA DE MENSAGENS (POST)
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("📩 Evento recebido:", data)

    if data.get("object") == "whatsapp_business_account":
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        messages = value.get("messages")

        if messages:
            message = messages[0]
            phone_number = message["from"]
            text = message["text"]["body"]

            print(f"📨 Mensagem recebida de {phone_number}: {text}")

            # Gera resposta com base na mensagem do usuário
            resposta = gerar_resposta(text)
            send_message(phone_number, resposta)

    return "ok", 200

# FUNÇÃO PARA ENVIAR MENSAGEM
def send_message(phone_number, text):
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": text}
    }

    response = requests.post(API_URL, headers=headers, json=payload)
    print("📤 Resposta da API:", response.status_code, response.text)

# EXECUTA O FLASK
if __name__ == "__main__":
    app.run(port=5000, debug=True)
