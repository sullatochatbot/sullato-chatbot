# 🧠 Documentação do Chatbot Sullato

## ✅ Objetivo Geral

Organizar o código do chatbot para:

* Tornar futuras manutenções mais simples.
* Separar lógicas por responsabilidade.
* Facilitar reuso e escalabilidade.
* Deixar o projeto pronto para clonar e adaptar com facilidade.

---

## 🔢 Estrutura Modular Criada

### `.env`

Contém as variáveis de ambiente sensíveis:

```ini
VERIFY_TOKEN=sullato_token_verificacao
ACCESS_TOKEN=seu_token_do_meta
PHONE_NUMBER_ID=id_do_numero_meta
GOOGLE_SHEETS_CREDENTIALS_PATH=credenciais_sheets.json
```

Motivo: Facilitar a troca de dados sensíveis sem alterar o código.

---

### `responder.py`

Responsável pela lógica de resposta, com funções para:

* Interpretar mensagens recebidas.
* Extrair nomes via regex.
* Enviar mensagens e botões.
* Atualizar o Google Sheets com interesse.
* Registrar primeira interação e salvar em mala direta.

Melhoria: Registro unificado de nome/interesse/data no Sheets e `historico`.

---

### `salvar_em_google_sheets.py`

Função `salvar_em_google_sheets(...)`:

* Grava nome, telefone, interesse e data no Google Sheets (aba principal).
* Evita duplicatas.

Atualização:

* Usa caminho do arquivo JSON via `.env`.

---

### `registrar_historico.py`

Função `registrar_interacao(...)`:

* Grava todo acesso (mesmo repetido) em aba "Historico" do Sheets com data e hora.
* Cria a aba caso não exista.

---

### `atualizar_google_sheets.py`

Função `atualizar_interesse_google_sheets(...)`:

* Atualiza coluna de interesse com base no telefone.
* Usa variáveis do `.env`.

---

### `salvar_em_mala_direta.py` (**novo**)

Função `salvar_em_mala_direta(...)`:

* Exporta os dados também para um `.csv` local.
* Preparado para futuras ações de marketing (ex: e-mail, exportação).

---

### `app.py`

Servidor Flask que:

* Recebe chamadas da API do WhatsApp.
* Valida Webhook.
* Encaminha mensagens para `gerar_resposta()`.

Correto uso do `.env`:

```python
load_dotenv()  # simples e universal
```

---

### `requirements.txt`

Inclui bibliotecas essenciais:

```
flask
requests
python-dotenv
gspread
google-auth
```

---

### `Procfile`

Executa o app correto:

```
web: python app.py
```

---

## 📄 Planilha Google

* Utiliza 2 abas: `Página1` (contatos) e `Historico` (todos os acessos).
* Tudo centralizado e acessível sem alterar código.

---

## ⚠️ Pronto para clonar e adaptar

Para criar um novo chatbot:

1. Clonar pasta.
2. Trocar `.env`.
3. Substituir credenciais.
4. Atualizar a planilha no Google Sheets (se desejar).

Tudo isolado por responsabilidade.
Deploy simples, leve e seguro.
