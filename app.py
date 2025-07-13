from flask import Flask, request
import requests
import json

app = Flask(__name__)

VERIFY_TOKEN = "sullato_token_verificacao"
ACCESS_TOKEN = "EAAxfFUMZAvBQBPNDsJ2obmCUPcVkOePusLhGRP2JtAhhgPxjWHA7digp2kiDMsPiEFRgMdKoufOZBaTQHFryNZBU44WrVUhjakS3DPPcuX3WqlpSIXpJyP1nmhIyIFbZA2Nlm2hHvS3YFKStEBoakMZcNMhP88gpKDn2x9iZAPOYtYdRZBW00tI83JqJg1zAZDZD"

@app.route("/", methods=["GET"])
def home():
    return "Sullato Chatbot online"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if token == VERIFY_TOKEN:
            return challenge, 200, {'Content-Type': 'text/plain'}
        return "Token inválido", 403

    if request.method == "POST":
        data = request.get_json()
        print("Mensagem recebida:", data)
        return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

