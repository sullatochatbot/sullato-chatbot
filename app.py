from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = "sullatotoken123"
TOKEN_META = "EAAxfFUMZAvBQBPNDsJ2obmCUPcVkOePuSpLGRP2JtAhhgPxjWHA7digp2kiDMsPiEFrgMdkOufOZBaTQHFryNZBU44WrUjhiaK53DPPcuX3WqlpSIxPJyPIinmhIyIFbZA2Nm2Hhvs3YFKstBEoakMZCnNhP8bgpKDn2x9iZApOYIYdRZBVM00IB33qjJg1zAZDZD"

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
        return "Evento recebido", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
