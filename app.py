from flask import Flask, request
import requests
import json

app = Flask(__name__)

VERIFY_TOKEN = "sullato_verifica_teste123"
ACCESS_TOKEN = "EAAxfFUMZAvBQBPNDsJ2obmCUPcVkOePuSpLGRP2JtAhhgPxjWHA7digp2kiDMsPiEFrgMdkOufOZBaTQHFryNZBU44WrUjhiaK53DPPcuX3WqlpSIxPJyPIinmhIyIFbZA2Nm2Hhvs3YFKstBEoakMZCnNhP8bgpKDn2x9iZApOYIYdRZBVM00IB33qjJg1zAZDZD"
PHONE_NUMBER_ID = "681607758375737"

@app.route("/", methods=["GET"])
def home():
    return "Sullato Chatbot online"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        print("📥 Requisição GET recebida")
        print("🔐 Token recebido:", repr(token))
        print("✅ Token esperado:", repr(VERIFY_TOKEN))

        if token == VERIFY_TOKEN:
            print("🔓 Token válido. Enviando challenge.")
            return challenge, 200, {'Content-Type': 'text/plain'}

        print("❌ Token inválido!")
        return "Token de verificação inválido", 403

    if request.method == "POST":
        data = request.get_json()
        print("📨 Mensagem recebida:", json.dumps(data, indent=2))

        try:
            entry = data["entry"][0]
            changes = entry["changes"][0]
            message = changes["value"]["messages"][0]
            phone_number = message["from"]
            msg_text = message["text"]["body"]

            print(f"📲 De: {phone_number} | Mensagem: {msg_text}")

            enviar_resposta(PHONE_NUMBER_ID, phone_number, "Olá, a Sullato agradece o seu contato. Em que posso te ajudar?")
        except Exception as e:
            print("❗ Erro ao processar mensagem:", e)

        return "EVENT_RECEIVED", 200

def enviar_resposta(phone_number_id, to, mensagem):
    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": { "body": mensagem }
    }
    response = requests.post(url, headers=headers, json=payload)
    print("📤 Resposta enviada:", response.status_code, response.text)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
