from flask import Flask, request
import requests
import json
import os

app = Flask(__name__)

# === Variáveis de ambiente (Render) ===
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")

# === Verificação do Webhook (GET) ===
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Erro de verificação", 403

# === Recebimento de Mensagem (POST) ===
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if data.get("object") == "whatsapp":
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value")
                messages = value.get("messages")

                if messages:
                    phone_number = messages[0]["from"]
                    text = messages[0]["text"]["body"]

                    print(f"📩 Mensagem de {phone_number}: {text}")

                    try:
                        send_message(phone_number, "Olá! A Sullato agradece o seu contato. Em que posso te ajudar?")
                    except Exception as e:
                        print("⚠️ Erro ao enviar mensagem:", str(e))

    return "ok", 200

# === Envio de Mensagem de Resposta ===
def send_message(phone_number, text):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
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

    response = requests.post(url, headers=headers, json=payload)
    print("📤 Resposta enviada:", response.status_code, response.text)
