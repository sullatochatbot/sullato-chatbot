import requests
import os
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

def enviar_template_boas_vindas(numero):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "template",
        "template": {
            "name": "boas_vindas",
            "language": {
                "code": "pt_BR"
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": "Anderson"  # ou qualquer nome para o {{1}} do template
                        }
                    ]
                }
            ]
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    print(f"[TEMPLATE] Para: {numero}")
    print("Status:", response.status_code)
    print("Resposta completa:", response.text)

# Executa o envio para seu número
enviar_template_boas_vindas("5511988780161")
