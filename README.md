# ChatbotSullato

Este projeto é um Webhook em Flask para integração com a API do WhatsApp Business (Meta), criado para atender clientes da Sullato Micros e Vans de forma automatizada.

## ✅ Funcionalidades

- Recebe verificações da Meta via GET
- Valida o token de segurança
- Imprime o conteúdo das mensagens recebidas (POST)
- Pronto para evolução futura com IA e NLP

## 🚀 Como executar

1. Crie e ative o ambiente virtual:
# ChatbotSullato

Este projeto é um Webhook em Flask para integração com a API do WhatsApp Business (Meta), criado para atender clientes da Sullato Micros e Vans de forma automatizada.

## ✅ Funcionalidades

- Recebe verificações da Meta via GET
- Valida o token de segurança
- Imprime o conteúdo das mensagens recebidas (POST)
- Pronto para evolução futura com IA e NLP

## 🚀 Como executar

1. Crie e ative o ambiente virtual:
python -m venv venv
.\venv\Scripts\activate

2. Instale as dependências:
pip install flask

3. Execute o servidor:
python webhook.py

2. Instale as dependências:
pip install flask

3. Execute o servidor:
python webhook.py

4. Acesse via navegador ou Postman:
http://127.0.0.1:5000/webhook?hub.mode=subscribe&hub.challenge=12345&hub.verify_token=sullato_token_seguro

