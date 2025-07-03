import requests

ACCESS_TOKEN = "EACPL2cB7rI8BO6JDjf5fk22JSVvKCZAcUnK0MqCIMQ9iGWMpE3tx3PyRZBSH7N604BDTAXIJM3JbJAvCtxMqLUD42b8TZAeNwqOZCNF5E9B3JgFVyRFxnxeUnItO4uzisciOR8huyqzhZAZBLjGGmZBuC5X1ptps2YZCbyPI6cm3ix4EtusOoM837XxWqKQhMU4WC9EywNUHKmYsg4jqp0ps9KMHLwv2ZA9c7vdvygurZBmneNQrwwDqABG3YZD"
PHONE_NUMBER_ID = "684523561413203"

def enviar_mensagem(telefone, mensagem):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
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
    response = requests.post(url, headers=headers, json=payload)
    print("Resposta da API:", response.status_code, response.text)
