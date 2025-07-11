from flask import Flask, request
import requests

app = Flask(__name__)

VERIFY_TOKEN = "sullatotoken123"
ACCESS_TOKEN = "EAAxfFUMZAvBQBPNDsJ2obmCUPcVkOePuSpLGRP2JtAhhgPxjWHA7digp2kiDMsPiEFrgMdkOufOZBaTQHFryNZBU44WrUjhiaK53DPPcuX3WqlpSIxPJyPIinmhIyIFbZA2Nm2Hhvs3YFKstBEoakMZCnNhP8bgpKDn2x9iZApOYIYdRZBVM00IB33qjJg1zAZDZD"

@app.route("/", methods=["GET"])
def home():
    return "Chatbot Sullato online com Flask!"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if token == VERIFY_TOKEN:
            return challenge
        return "Token inválido"

    if request.method == "POST":
        data = request.get_json()
        print("Mensagem recebida:", data)

        try:
            entry = data["entry"][0]
            changes = entry["changes"][0]
            message = changes["value"]["messages"][0]
            phone_number = message["from"]
            msg_text = message["text"]["body"]

            print(f">> De: {phone_number} | Mensagem: {msg_text}")

            responder_para_whatsapp(
                phone_number,
                "Olá, a Sullato agradece o seu contato. Em que posso te ajudar?"
            )

        except Exception as e:
            print("Erro ao processar mensagem:", e)

        return "OK", 200

def responder_para_whatsapp(numero, mensagem):
    url = "https://graph.facebook.com/v19.0/940545704/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {
            "body": mensagem
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    print("Resposta da API:", response.status_code, response.text)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
