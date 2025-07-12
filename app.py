from flask import Flask, request
import requests

app = Flask(__name__)

VERIFY_TOKEN = "sullatotoken123"
TOKEN_META = "EAAxfFUMZAvBQBPNDsJ2obmCUPcVkOePuSpLGRP2JtAhhgPxjWHA7digp2kiDMsPiEFrgMdkOufOZBaTQHFryNZBU44WrUjhiaK53DPPcuX3WqlpSIxPJyPIinmhIyIFbZA2Nm2Hhvs3YFKstBEoakMZCnNhP8bgpKDn2x9iZApOYIYdRZBVM00IB33qjJg1zAZDZD"
ID_WABA = "1300357505048528"

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
        return "Token inválido", 403

    elif request.method == "POST":
        data = request.get_json()
        print("Mensagem recebida:", data)

        try:
            entry = data["entry"][0]
            changes = entry["changes"][0]
            value = changes["value"]

            if "messages" in value:
                message = value["messages"][0]
                number = message["from"]
                text = message["text"]["body"]

                print(f"Número: {number} - Mensagem: {text}")
                enviar_resposta(number, "Olá! A Sullato agradece o seu contato. Em que posso te ajudar?")
        except Exception as e:
            print("Erro ao processar mensagem:", e)

        return "Evento recebido", 200

def enviar_resposta(telefone, mensagem):
    url = f"https://graph.facebook.com/v19.0/{ID_WABA}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN_META}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": telefone,
        "type": "text",
        "text": {
            "body": mensagem
        }
    }

    resposta = requests.post(url, headers=headers, json=payload)
    print("Resposta enviada:", resposta.status_code, resposta.text)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
