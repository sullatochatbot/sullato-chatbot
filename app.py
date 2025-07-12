from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Chatbot Sullato online com Flask!"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if token == "sullatotoken123":
            return challenge
        return "Token inválido", 403

    if request.method == "POST":
        data = request.get_json()
        print("📥 RECEBIDO DA META:")
        print("➡️ JSON recebido:", data)

        try:
            entry = data['entry'][0]
            message = entry['changes'][0]['value']['messages'][0]['text']['body']
            sender = entry['changes'][0]['value']['messages'][0]['from']
            print(f"✉️ Nova mensagem de {sender}: {message}")
        except Exception as e:
            print("⚠️ Erro ao interpretar mensagem:", e)

        return jsonify({"status": "mensagem recebida"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
