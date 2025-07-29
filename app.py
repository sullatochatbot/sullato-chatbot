from flask import Flask, request
import json
import os
from dotenv import load_dotenv
from responder import gerar_resposta

# Carrega variáveis de ambiente do .env
load_dotenv()

app = Flask(__name__)

# === Variáveis da API da Meta ===
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
print("🔁 O app.py foi executado com sucesso!")

# === Webhook de verificação (GET) ===
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    print(f"🧪 VERIFY_TOKEN do ambiente: {VERIFY_TOKEN}")
    print(f"🧪 Token recebido da Meta: {token}")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Token inválido", 403

# === Webhook para receber mensagens (POST) ===
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
            print(f"✅ Chamando gerar_resposta(text, phone_number)")
            gerar_resposta(text, phone_number)

    return "ok", 200

# === Inicialização do servidor Flask ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
