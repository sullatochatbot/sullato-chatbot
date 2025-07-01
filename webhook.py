from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

VERIFY_TOKEN = "sullato_token"
ACCESS_TOKEN = "EACPL2cB7rI8BO5CCdMuogHJc02LDTOvZAR5y3Y3n74GrOQdxFTrNFxVnV5VG5NPFhO8BlQH5gFZBXoJCOdb6qCFv4ZAJax27vdCBekwmuZBsSO96jOqlVEiorrylZCAqeAStWDIocXeSfmkC2Ry7f6IMNlspgrBp58NBPWpqGs8ZAZBLzixNHGX3tWEYgLKl1erHZA0L2iOZC6DVVRAiRZCv0fPNkFmxvYChCQOGUo0SWpmEHnZCsCmZAKdtlfZC5kpMZD"
PHONE_NUMBER_ID = "684523561413203"

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "Erro de verificação", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("🔔 Mensagem recebida:", data)

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        messages = value.get("messages")
        
        if messages:
            msg = messages[0]
            sender = msg["from"]
            message_text = msg["text"]["body"]

            print(f"📩 De: {sender} | 📥 Texto: {message_text}")

            reply_text = "Olá! 👋 Aqui é a Sullato Micros e Vans. Como posso te ajudar?"

            url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
            headers = {
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": "application/json"
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": sender,
                "type": "text",
                "text": {
                    "body": reply_text
                }
            }

            response = requests.post(url, headers=headers, json=payload)
            print("✅ Resposta enviada:", response.status_code, response.text)

    except Exception as e:
        print("❌ Erro ao processar a mensagem:", e)

    return "ok", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
