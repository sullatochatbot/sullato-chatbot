from flask import Flask, request
import requests
import json
import responder  # Importa nosso módulo de respostas personalizadas

app = Flask(__name__)

# === Configurações ===
VERIFY_TOKEN = "sullato_token_verificacao"
ACCESS_TOKEN = "EAAT6yhis6b8BPETCp493TtGZC5bA7YIf1osyqt65SoMBsCZAwASZAi8Yt4bfUmZBLjMxGtfVF0YFUjFY8Wzn1YYZAvzHEZCwoXQZCffXc8KLgWoDTHmOHHfjZBHafbTsZAY2aWZAjlsTg5rgT7NoiR6qrciAFOb5AnzUnZCNDjLWhLPOozB9gPJaY4FXD45JnrFApNoZBAZDZD"
PHONE_NUMBER_ID = "684523561413203"

# === Webhook de verificação (GET) ===
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    print("📥 Verificação recebida da Meta:", mode)
    print("🔐 Token recebido:", token)

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verificado com sucesso!")
        return challenge, 200
    else:
        print("❌ Token inválido")
        return "Token inválido", 403

# === Recebimento de mensagens (POST) ===
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        print("📩 Dados recebidos:", json.dumps(data, indent=2))

        if not data:
            print("⚠️ Nenhum dado recebido.")
            return "ok", 200

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
                responder.gerar_resposta(text, phone_number)  # <- AQUI AGORA ESTÁ CORRETO
            else:
                print("⚠️ Número ou texto não encontrados.")
        else:
            print("⚠️ Nenhuma mensagem na requisição.")

    except Exception as e:
        print("❌ Erro no processamento:", str(e))

    return "ok", 200

# === Função para envio de mensagem de texto ===
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
        "text": {
            "body": message
        }
    }

    print("📤 Enviando MENSAGEM DE TEXTO via API da Meta")
    print("📦 Payload:", json.dumps(payload, indent=2))

    try:
        response = requests.post(url, headers=headers, json=payload)
        print("📬 Status:", response.status_code)
        print("📨 Resposta:", response.text)
    except Exception as e:
        print("❌ Erro ao enviar mensagem de texto:", str(e))

# === Inicializador do Flask ===
if __name__ == "__main__":
    print("🚀 Servidor Flask iniciado em http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000)
