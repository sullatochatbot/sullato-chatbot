# versão 2.1.0 – Código final corrigido para envio de template via webhook POST

from flask import Flask, request
import requests
import json

app = Flask(__name__)

# === Configurações fixas ===
VERIFY_TOKEN = "sullato_token_verificacao"
ACCESS_TOKEN = "EAAT6yhis6b8BPETCp493TtGZC5bA7YIf1osyqt65SoMBsCZAwASZAi8Yt4bfUmZBLjMxGtfVF0YFUjFY8Wzn1YYZAvzHEZCwoXQZCffXc8KLgWoDTHmOHHfjZBHafbTsZAY2aWZAjlsTg5rgT7NoiR6qrciAFOb5AnzUnZCNDjLWhLPOozB9gPJaY4FXD45JnrFApNoZBAZDZD"
PHONE_NUMBER_ID = "684523561413203"

# === Webhook de verificação (GET) ===
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    print("📥 Recebido do Meta:", mode)
    print("🔐 Token esperado:", VERIFY_TOKEN)

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verificado com sucesso!")
        return challenge, 200
    else:
        print("❌ Token de verificação inválido")
        return "Token inválido", 403

# === Webhook de recebimento de mensagens (POST) ===
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("📩 Dados recebidos:", json.dumps(data, indent=2))

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" in value:
            message_data = value["messages"][0]
            print("🔍 message_data:", json.dumps(message_data, indent=2))

            phone_number = message_data.get("from")
            text_obj = message_data.get("text")
            text = text_obj.get("body") if text_obj else None

            print(f"📨 Mensagem recebida de {phone_number}: {text}")

            if phone_number:
                print(f"📤 Enviando template 'boas_vindas' para: {phone_number}")
                send_template(phone_number)
            else:
                print("⚠️ Número de telefone não identificado.")
        else:
            print("⚠️ Nenhuma mensagem recebida.")

    except Exception as e:
        print("❌ Erro ao processar mensagem:", str(e))

    return "ok", 200

# === Função para envio do template boas_vindas ===
def send_template(phone_number):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "template",
        "template": {
            "name": "boas_vindas",
            "language": {
                "code": "pt_BR"
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": "Anderson"
                        }
                    ]
                }
            ]
        }
    }

    print("📤 Enviando TEMPLATE via API oficial da Meta")
    print("📌 URL:", url)
    print("📎 Token:", ACCESS_TOKEN[:40] + "...")
    print("📱 ID do telefone:", PHONE_NUMBER_ID)
    print("📦 Payload:", json.dumps(payload, indent=2))

    try:
        response = requests.post(url, headers=headers, json=payload)
        print("📬 Status da resposta:", response.status_code)
        print("📨 Conteúdo:", response.text)
    except Exception as e:
        print("❌ Erro ao enviar template:", str(e))

# === Inicialização do servidor Flask ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
