from flask import Flask, request
import requests
import json
import responder
import os
from dotenv import load_dotenv

# === Carrega variáveis do .env ===
load_dotenv()

# === Inicializa o Flask ===
app = Flask(__name__)

# === Tokens e variáveis ===
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# === Verificação inicial do Webhook (GET) ===
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    print("📥 Verificação recebida:", mode)
    print("🔐 Token recebido:", token)

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verificado com sucesso!")
        return challenge, 200
    else:
        print("❌ Token inválido recebido:", token)
        return "Token inválido", 403

# === Recebimento de mensagens (POST) ===
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        print("📩 JSON recebido:", json.dumps(data, indent=2))

        if not data:
            print("⚠️ Nenhum dado recebido.")
            return "ok", 200

        # Estrutura simples validada
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})

        if "messages" in value:
            message_data = value["messages"][0]
            print("🔍 message_data:", json.dumps(message_data, indent=2))

            phone_number = message_data.get("from")
            text_obj = message_data.get("text")
            text = text_obj.get("body") if text_obj else None

            print(f"📨 Mensagem recebida de {phone_number}: {text}")

            if phone_number and text:
                print("✅ Chamando responder.gerar_resposta()")
                responder.gerar_resposta(text, phone_number)
            else:
                print("⚠️ Número ou texto não encontrados.")
        else:
            print("⚠️ Nenhuma mensagem presente em 'value'.")

    except Exception as e:
        print("❌ Erro no webhook:", str(e))

    return "ok", 200

# === Envio manual (caso queira usar) ===
def send_text_message(phone_number, message):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": message}
    }

    print("📤 Enviando mensagem manual via API...")
    print("📦 Payload:", json.dumps(payload, indent=2))

    try:
        response = requests.post(url, headers=headers, json=payload)
        print("📬 Status:", response.status_code)
        print("📨 Resposta:", response.text)
    except Exception as e:
        print("❌ Erro ao enviar mensagem:", str(e))

# === Inicializa o servidor ===
if __name__ == "__main__":
    print("🚀 Servidor Flask iniciado em http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000)
