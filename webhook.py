# versão 1.0.9 - rebuild forçado em 19/jul às 17h22
from flask import Flask, request
import requests
import json

app = Flask(__name__)

# === Variáveis fixas ===
VERIFY_TOKEN = "sullato_token_verificacao"
ACCESS_TOKEN = "EAAT6yhis6b8BPETCp493TtGZC5bA7YIf1osyqt65SoMBsCZAwASZAi8Yt4bfUmZBLjMxGtfVF0YFUjFY8Wzn1YYZAvzHEZCwoXQZCffXc8KLgWoDTHmOHHfjZBHafbTsZAY2aWZAjlsTg5rgT7NoiR6qrciAFOb5AnzUnZCNDjLWhLPOozB9gPJaY4FXD45JnrFApNoZBAZDZD"
PHONE_NUMBER_ID = "1300357505048528"

# === Verificação do Webhook (GET) ===
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
    
# === Verificação do Webhook (POST) ===
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

            if phone_number and text:
                print(f"📤 Enviando resposta para: {phone_number}")
                send_message(phone_number, "Olá! A Sullato agradece o seu contato. Em que posso te ajudar?")
            else:
                print("⚠️ Dados incompletos: número ou texto ausente.")
        else:
            print("⚠️ Nenhuma mensagem encontrada no valor.")

        print("⚠️ Erro ao processar mensagem:", str(e))

    return "ok", 200

# === Envio de Mensagem de Resposta ===
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
        "text": {"body": text}
    }

    try:
    response = requests.post(url, headers=headers, json=payload)
    print("📤 Enviando para:", url)
    print("📨 Payload:", json.dumps(payload, indent=2))
    print("📥 Status da resposta:", response.status_code)
    print("📝 Conteúdo:", response.text)
except Exception as e:
    print("❌ Erro ao tentar enviar mensagem:", str(e))


