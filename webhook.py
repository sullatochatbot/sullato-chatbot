from flask import Flask, request
import requests
import json

app = Flask(__name__)

VERIFY_TOKEN = "sullato_token_verificacao"
ACCESS_TOKEN = "EAAxfFUMZAvBQBPNDsJ2obmCUPcVkOePuSpLGRP2JtAhhgPxjWHA7digp2kiDMsPiEFrgMdkOufOZBaTQHFryNZBU44WrUjhiaK53DPPcuX3WqlpSIxPJyPIinmhIyIFbZA2Nm2Hhvs3YFKstBEoakMZCnNhP8bgpKDn2x9iZApOYIYdRZBVM00IB33qjJg1zAZDZD"

@app.route("/webhook", methods=["GET"])
def verificar():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == VERIFY_TOKEN:
        return challenge
    return "Token de verificação inválido.", 403

@app.route("/webhook", methods=["POST"])
def receber_mensagem():
    payload = request.get_json()
    print("📥 Payload recebido:", json.dumps(payload, indent=2))
    try:
        entry = payload.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if messages:
            phone_number_id = value["metadata"]["phone_number_id"]
            from_number = messages[0]["from"]
            if "text" in messages[0]:
                msg = messages[0]["text"]["body"]
                resposta = f"Olá! Recebemos sua mensagem: '{msg}'. Em que posso ajudar?"
                enviar_resposta(phone_number_id, from_number, resposta)
            else:
                print("❌ Mensagem recebida não é de texto.")
    except Exception as e:
        print(f"❗ Erro ao processar mensagem: {e}")
    return "OK", 200

def enviar_resposta(phone_id, to, texto):
    url = f"https://graph.facebook.com/v19.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": { "body": texto }
    }
    resposta = requests.post(url, headers=headers, json=payload)
    print("📤 Resposta enviada:", resposta.status_code, resposta.text)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
