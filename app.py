from flask import Flask, request

app = Flask(__name__)

def processar_mensagem(mensagem):
    mensagem = mensagem.lower()

    if "bom dia" in mensagem or "boa tarde" in mensagem or "boa noite" in mensagem or "oi" in mensagem:
        return "Olá! Seja bem-vindo à Sullato Micros e Vans 🚐. Como posso te ajudar hoje?"

    elif "compra" in mensagem:
        return "Ótimo! Está procurando um veículo de passageiro ou de carga?"

    elif "passageiro" in mensagem:
        return "Legal! Quer algo convencional, escolar ou executivo?"

    elif "carga" in mensagem:
        return "Beleza. Você busca um furgão, baú ou carroceria?"

    elif "baú" in mensagem or "carroceria" in mensagem:
        return "Temos opções incríveis prontas pra te atender. Quer ver os modelos disponíveis?"

    else:
        return "Desculpe, não entendi muito bem. Pode repetir de outra forma, por favor?"

@app.route("/")
def index():
    return "Chatbot Sullato está online!"

@app.route("/responder", methods=["POST"])
def responder():
    dados = request.get_json()
    mensagem = dados.get("mensagem", "")
    resposta = processar_mensagem(mensagem)
    return {"resposta": resposta}

if __name__ == "__main__":
    app.run(debug=True)
