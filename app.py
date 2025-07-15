from flask import Flask, request
import requests
import json
import os

app = Flask(__name__)

# === Variáveis de ambiente ===
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
print("🔁 O app.py foi executado com sucesso!")

# === Rota para verificação do Webhook (GET) ===
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Token inválido", 403

# === Rota para receber mensagens (POST) ===
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("📩 Dados recebidos:", json.dumps(data, indent=2))

    if data and data.get("object") == "whatsapp":
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if messages:
            phone_number = messages[0]["from"]
            text = messages[0]["text"]["body"]
            send_message(phone_number, text)

    return "ok", 200

# === Função para enviar resposta ===
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
        "text": {
            "body": text
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    print("📤 Resposta enviada:", response.status_code, response.text)

# === Inicialização do Servidor Flask ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
