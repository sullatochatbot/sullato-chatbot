import requests
import json
import time

mensagens = [
    "Olá, vocês têm van escolar?",
    "Quero financiar mesmo com nome sujo.",
    "Aceita meu carro na troca?",
    "Preciso de uma van pra transporte de carga refrigerada.",
    "Vocês ficam onde?",
    "Tem van com troco?",
    "Qual o horário de atendimento?",
    "Quero começar como motorista de transporte escolar. O que vocês recomendam?",
    "Quero vender minha Kombi e pegar uma com baú."
]

url = "http://localhost:5000/webhook"
headers = {
    "Content-Type": "application/json"
}

for msg in mensagens:
    data = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "5511988780161",
                                    "text": { "body": msg }
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    print(f"\n📤 Enviando: {msg}")
    response = requests.post(url, headers=headers, data=json.dumps(data, ensure_ascii=False))
    print("📥 Resposta do servidor:", response.status_code, response.text)
    time.sleep(2)
