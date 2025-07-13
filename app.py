from flask import Flask, request
import requests
import json

app = Flask(__name__)

VERIFY_TOKEN = "sullato_token_verificacao"
ACCESS_TOKEN = "EAAxfFUMZAvBQDPNDsJ2obmCUPcVkOePUslGRP2JtAhhgPxjWHA7digp2kiDMsPiEFrgMdkOufOZBaTQHFryNZBU44WrUjhiaK53DPPcuX3WqlpSIxPJyPIinmhIyIFbZA2Nm2Hhvs3YFKstBEoakMZCnNhP8bgpKDn2x9iZApOYIYdRZBVM00IB33qjJg1zAZDZD"
PHONE_NUMBER_ID = "681607758375737"

@app.route("/", methods=["GET"])
def home():
    return "Sullato Chatbot online"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if token == VERIFY_TOKEN:
            return challenge, 200
        return "Token inválido", 403

    if request.method == "POST":
        payload = request.get_json()
        print("📩 Payload recebido:\n", json.dumps(payload, indent=2))
        return "EVENT_RECEIVED", 200

