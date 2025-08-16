# webhook.py
import os
import json
import requests
from flask import Flask, request, jsonify
import responder  # seu módulo principal de respostas

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "sullato_token_verificacao")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

app = Flask(__name__)

def _send_text(phone_number: str, message: str) -> None:
    """Fallback: envia texto direto pela API da Meta."""
    try:
        url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": message},
        }
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        print("📤 Meta message:", r.status_code, r.text)
    except Exception as e:
        print("❌ Falha no _send_text:", e)

def _extract_incoming_text(msg: dict) -> str:
    """Extrai texto de mensagem normal e de botões (interactive)."""
    if not isinstance(msg, dict):
        return ""
    # texto simples
    t = (msg.get("text") or {}).get("body")
    if t:
        return t
    # botões
    inter = msg.get("interactive") or {}
    btn = inter.get("button_reply") or {}
    if isinstance(btn, dict):
        return btn.get("id") or btn.get("title") or ""
    # outros tipos (nfm_reply)
    nfm = inter.get("nfm_reply") or {}
    if isinstance(nfm, dict):
        return nfm.get("response_json") or nfm.get("id") or ""
    return ""

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # Verificação (Meta)
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        print("📥 Verify:", mode, token)
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ WEBHOOK VERIFIED")
            return challenge, 200
        return "forbidden", 403

    # Mensagens
    try:
        data = request.get_json(silent=True) or {}
        print("➡️  Incoming:", json.dumps(data, ensure_ascii=False))

        entry = (data.get("entry") or [{}])[0]
        changes = (entry.get("changes") or [{}])[0]
        value = changes.get("value") or {}

        messages = value.get("messages") or []
        if not messages:
            print("ℹ️  Evento sem 'messages' (status/ack).")
            return jsonify({"status": "ok"}), 200

        msg = messages[0]
        phone = msg.get("from") or msg.get("wa_id") or ""
        contacts = value.get("contacts") or []
        name = (contacts[0].get("profile", {}).get("name") if contacts else None) or "Cliente"

        text = _extract_incoming_text(msg)
        print(f"👤 {phone} | {name} → {text!r}")

        # Chama seu motor de respostas (duas assinaturas possíveis)
        try:
            if hasattr(responder, "gerar_resposta"):
                responder.gerar_resposta(msg, phone, name)
            else:
                responder.responder(phone, {"text": {"body": text}}, name)
        except Exception as e:
            print("❌ CRASH dentro do responder:", e)
            _send_text(phone, "Tive um erro momentâneo, mas estou online. Digite *menu*.")

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("❌ ERRO no webhook:", e)
        # responder 200 evita reentrega em loop pelo WhatsApp
        return jsonify({"status": "error"}), 200

if __name__ == "__main__":
    print("🚀 Servidor Flask iniciado em http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000)
