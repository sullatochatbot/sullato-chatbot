from flask import Flask, request
import requests
import json

app = Flask(__name__)

VERIFY_TOKEN = "sullato_token_verificacao"
ACCESS_TOKEN = "EAAxfFUMZAvBQBPECCWr33FyZBQZBcrfHZBsQxmaYV5Jff0WXS7bSiCBiGgIW8whQDas90wD8xEd3ZAjPqo6nCBEBheK6QOqD7M8sdBrI8MEX04cHMENW7nb0zrvcGmDWsURoOoyK2op2UmZBTCRODkRWUw24ujPWvU1c0p3YcGS0pTHpQ8FukQK09M1Ddj85bHMwZDZD"
PHONE_NUMBER_ID = "681607758375737"

@app.route("/", methods=["GET"])
def home():
    return "Sullato Chatbot online"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        print(f"🔐 Modo recebido: {mode}")
        print(f"🔐 Token recebido: {token}")
        print(f"✅ Token esperado: {VERIFY_TOKEN}")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200

        return "Token inválido", 403

    if request.method == "POST":
        payload = request.get_json()
        print("📩 Payload recebido:\n", json.dumps(payload, indent=2))
        return "EVENT_RECEIVED", 200

def enviar_resposta(phone_number_id, to, mensagem):
    url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": mensagem}
    }

    response = requests.post(url, headers=headers, json=payload)
    print("📤 Resposta enviada:", response.status_code, response.text)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
