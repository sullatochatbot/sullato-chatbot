import os
import json
import requests
from flask import Flask, request
from responder import responder

app = Flask(__name__)

# Token permanente gerado na Meta
ACCESS_TOKEN = "EAAxfFUMZAvBQBPNDsJ2obmCUPcVkOePuSpLGRP2JtAhhgPxjWHA7digp2kiDMsPiEFrgMdkOufOZBaTQHFryNZBU44WrUjhiaK53DPPcuX3WqlpSIxPJyPIinmhIyIFbZA2Nm2Hhvs3YFKstBEoakMZCnNhP8bgpKDn2x9iZApOYIYdRZBVM00IB33qjJg1zAZDZD"
VERIFY_TOKEN = "sullato_token_verificacao"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # Verificação do webhook pela Meta
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if verify_token == VERIFY_TOKEN:
            return challenge, 200
        return "Token de verificação inválido", 403

    elif request.method == 'POST':
        try:
            payload = request.get_json()
            print("🔔 Mensagem recebida:", json.dumps(payload, indent=2))

            entry = payload.get("entry", [])[0]
            changes = entry.get("changes", [])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [])

            if messages:
                phone_number_id = value["metadata"]["phone_number_id"]
                from_number = messages[0]["from"]
                mensagem = messages[0]["text"]["body"]

                # Gera a resposta com base no conteúdo recebido
                resposta = responder(mensagem)

                # Envia a resposta de volta para o cliente no WhatsApp
                enviar_resposta(phone_number_id, from_number, resposta)

        except Exception as e:
            print(f"❌ Erro ao processar mensagem: {e}")

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
        "text": {
            "body": mensagem
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    print("📤 Resposta enviada:", response.status_code, response.text)

if __name__ == '__main__':
    app.run(port=5000)
