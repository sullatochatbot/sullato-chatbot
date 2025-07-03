from flask import Flask, request, jsonify
import sys

app = Flask(__name__)

# Token de verificação (o mesmo que foi configurado na Meta)
verify_token = 'sullato_token'

# Token de acesso fixo (válido por 2 meses)
access_token = 'EACPL2cB7rI8BOZB2l1B0z2pVmxgTqaYBPZB6XMqjZBMZCHwgnQwEzwZAsvhg94mdjgYBbSoAvszr4taTYGMv0tF60oTSccioP6Rg5gdxSKZCg1WoXQIARyZBytIaE8yunUrZBsZAoZBgHZAl6lXiuJWCCaR8ZBwVhV4YbFD0dNkfRVMsg5NgZCdZAHZAMpfMOlQtB7klMzAJANpzizQqrEZD'

@app.route('/webhook', methods=['GET'])
def verificar_webhook():
    if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.verify_token') == verify_token:
        return request.args.get('hub.challenge')
    return 'Token de verificação inválido', 403

@app.route('/webhook', methods=['POST'])
def receber_mensagem():
    data = request.get_json()
    print("Mensagem recebida:", file=sys.stderr)
    print(data, file=sys.stderr)

    try:
        mensagem = data['entry'][0]['changes'][0]['value']['messages'][0]
        texto = mensagem['text']['body']
        numero = mensagem['from']
        print(f"Mensagem de {numero}: {texto}", file=sys.stderr)
    except Exception as e:
        print(f"Nenhuma mensagem processada: {e}", file=sys.stderr)

    return jsonify(status="recebido"), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)
