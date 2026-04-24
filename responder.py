import os
import random
import requests
import unicodedata
import re
import smtplib
import ssl
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any

# ✅ CARREGA .ENV
load_dotenv()

# ✅ CONFIG SHEETS
SHEETS_WEBHOOK_URL = os.getenv("SHEETS_WEBHOOK_URL")
SHEETS_SECRET = os.getenv("SHEETS_SECRET")

def enviar_para_google_sheets(numero, nome, origem="chatbot"):
    try:
        if not SHEETS_WEBHOOK_URL:
            print("⚠️ SHEETS_WEBHOOK_URL não configurado")
            return

        payload = {
            "route": "chatbot",
            "secret": SHEETS_SECRET,
            "numero": numero,
            "nome": nome,
            "origem": origem
        }

        r = requests.post(SHEETS_WEBHOOK_URL, json=payload, timeout=10)

        print("📤 Sheets:", r.status_code, r.text)

    except Exception as e:
        print("❌ Erro ao enviar para Sheets:", e)

# ===== Fuso horário SP robusto (com fallback) =====
def _agora_sp_factory():
    try:
        from zoneinfo import ZoneInfo  # type: ignore
        try:
            tz = ZoneInfo("America/Sao_Paulo")
            return lambda: datetime.now(tz)
        except Exception:
            pass
        try:
            import tzdata  # noqa: F401
            tz = ZoneInfo("America/Sao_Paulo")
            return lambda: datetime.now(tz)
        except Exception:
            pass
    except Exception:
        pass
    tz_fallback = timezone(timedelta(hours=-3))
    return lambda: datetime.now(tz_fallback)

agora_sp = _agora_sp_factory()

# =============================
# Imports de módulos do projeto
# =============================
try:
    from interpretar_ia import interpretar_mensagem
except Exception:
    def interpretar_mensagem(_texto: str):
        return None

try:
    from normalizar_nomes import normalizar_nome
except Exception:
    def normalizar_nome(nome: str) -> str:
        try:
            n = unicodedata.normalize("NFKD", nome)
            n = "".join(ch for ch in n if not unicodedata.combining(ch))
            n = re.sub(r"[^a-zA-Z0-9\s]", "", n).strip()
            n = re.sub(r"\s+", " ", n)
            return n if n else "Cliente"
        except Exception:
            return "Cliente"

# =============================
# Tokens e IDs (ambiente)
# =============================
load_dotenv()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# =============================
# SMTP (Trabalhe Conosco)
# =============================
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER or "no-reply@sullato.com.br")
SMTP_TO_DEFAULT = os.getenv("SMTP_TO", "anderson@sullato.com.br")

# =============================
# Utilitários
# =============================
def remover_acentos(txt: str) -> str:
    if not txt:
        return ""
    nfkd_form = unicodedata.normalize("NFKD", txt)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def normalizar_id(texto: str) -> str:
    if not texto:
        return ""
    t = texto.strip()
    t = remover_acentos(t).lower()
    t = re.sub(r"\s+", " ", t)
    return t

def extrair_primeiro_nome_exibicao(nome: Optional[str]) -> str:
    if not nome:
        return "Cliente"
    nome = nome.strip()
    if not nome:
        return "Cliente"
    partes = nome.split()
    if len(partes) == 0:
        return "Cliente"
    primeiro = partes[0]
    if re.fullmatch(r"\d[\d\s\-()+]*", primeiro or ""):
        return "Cliente"
    return primeiro.capitalize()

def detectar_nome_digitado(texto: str) -> Optional[str]:
    if not texto:
        return None
    texto = texto.strip()
    for p in [
        r"meu nome e ([a-zA-ZÀ-ÿ\s]+)",
        r"meu nome é ([a-zA-ZÀ-ÿ\s]+)",
        r"me chamo ([a-zA-ZÀ-ÿ\s]+)",
        r"sou o ([a-zA-ZÀ-ÿ\s]+)",
        r"sou a ([a-zA-ZÀ-ÿ\s]+)",
        r"nome e ([a-zA-ZÀ-ÿ\s]+)",
    ]:
        m = re.search(p, texto)
        if m:
            return m.group(1).strip()
    return None

def atualizar_interesse(numero: str, interesse: str) -> None:
    try:
        from atualizar_google_sheets import atualizar_interesse_google_sheets
        atualizar_interesse_google_sheets(numero, interesse)
    except Exception as e:
        print("⚠️ Falha ao atualizar interesse na planilha:", e)

def enviar_email(assunto: str, corpo: str, destinatario: Optional[str] = None) -> bool:
    to_addr = destinatario or SMTP_TO_DEFAULT
    if not (SMTP_SERVER and SMTP_PORT and SMTP_USER and SMTP_PASS and to_addr):
        print("⚠️ SMTP não configurado corretamente. Pular envio de e-mail.")
        return False
    try:
        msg = (
            f"From: {SMTP_FROM}\r\n"
            f"To: {to_addr}\r\n"
            f"Subject: {assunto}\r\n"
            f"MIME-Version: 1.0\r\n"
            f"Content-Type: text/plain; charset=utf-8\r\n\r\n"
            f"{corpo}"
        ).encode("utf-8")
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_FROM, [to_addr], msg)
        print("✅ E-mail enviado:", assunto)
        return True
    except Exception as e:
        print("❌ Falha ao enviar e-mail:", e)
        return False

def enviar_mensagem(numero: str, texto: str) -> None:
    try:
        url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
        payload = {"messaging_product": "whatsapp", "to": numero, "text": {"preview_url": True, "body": texto}}
        r = requests.post(url, headers=headers, json=payload)
        print("🟢 Meta message:", r.status_code, r.text)
    except Exception as e:
        print("❌ Erro ao enviar mensagem:", e)

def enviar_botoes(numero: str, texto: str, botoes: List[Dict[str, Any]]) -> None:
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "interactive",
        "interactive": {"type": "button", "body": {"text": texto}, "action": {"buttons": botoes}},
    }
    try:
        r = requests.post(url, headers=headers, json=payload)
        print("🟢 Meta botões:", r.status_code, r.text)
    except Exception as e:
        print("❌ Erro ao enviar botões:", e)

# Helpers payload
def _extrair_id_ou_texto(msg) -> str:
    """Extrai ID de botão ou texto do payload, cobrindo os formatos comuns da Meta."""
    try:
        if isinstance(msg, str):
            return msg
        if isinstance(msg, dict):
            inter = msg.get("interactive") or {}
            if inter.get("type") == "button":
                br = inter.get("button_reply") or inter.get("nfm_reply") or {}
                return br.get("id") or br.get("title") or ""
            if "text" in msg and isinstance(msg["text"], dict):
                return msg["text"].get("body", "")
            if msg.get("type") == "text" and "text" in msg:
                return msg["text"].get("body", "")
            if "messages" in msg and isinstance(msg["messages"], list) and msg["messages"]:
                return _extrair_id_ou_texto(msg["messages"][0])
        return ""
    except Exception:
        return ""

def _is_text_payload(msg) -> bool:
    if isinstance(msg, str):
        return True
    if isinstance(msg, dict):
        if msg.get("type") == "text":
            return True
        if isinstance(msg.get("text"), dict) and msg["text"].get("body"):
            return True
    return False

def _tem_trigger_menu(id_norm: str) -> bool:
    return re.search(r"\b(oi|ola|menu|inicio|start|ajuda|help|voltar|voltar ao inicio)\b", f" {id_norm} ") is not None

# ===== Heurística simples de intenção (toque de IA) =====
def detectar_intencao_basica(txt: str) -> Optional[str]:
    if not txt:
        return None
    t = txt.lower()
    grupos = [
        ("credito",      ["credito", "financi", "parcel", "banco", "consorcio", "consórcio"]),
        ("endereco",     ["endereco", "endereço", "loja", "onde fica", "mapa"]),
        ("comprar",      ["comprar", "compra", "quero comprar"]),
        ("vender",       ["vender", "venda", "quero vender"]),
        ("pos_venda",    ["pos venda", "pós-venda", "garantia", "assistencia", "assistência", "suporte"]),
        ("oficina_passeio",   ["oficina passeio", "passeio oficina"]),
        ("oficina_utilitario",["oficina utilitario", "oficina utilitário", "utilitario oficina", "utilitário oficina"]),
        ("governamentais",    ["governamental", "governamentais", "venda direta", "venda-direta"]),
        ("assinatura",        ["assinatura", "subscription", "aluguel longo", "longa duracao", "longa duração"]),
        ("trabalhe",          ["trabalhe", "curriculo", "currículo", "emprego", "vaga", "vagas", "rh"]),
    ]
    for intent, palavras in grupos:
        if any(p in t for p in palavras):
            return intent
    return None

# ===== Rodízio de vendedores (varia a cada 6h) =====
VENDEDORES_PASSEIO_BASE = [
    ("👨🏻‍💼 Alexandre", "https://wa.me/5511988628961"),
    ("👨🏻‍💼 Jeferson",  "https://wa.me/5511941006862"),
    ("👨🏻‍💼 Pedro",     "https://wa.me/5511992037103"),
    ("👨🏻‍💼 Thiago",    "https://wa.me/5511986122905"),
    ("👩🏻‍💼 Vanessa",   "https://wa.me/5511947954378"),
    ("👨🏻‍💼 Vinicius",  "https://wa.me/5511992419382"),
]
VENDEDORES_UTIL_BASE = [
    ("👩🏻‍💼 Magali",  "https://wa.me/5511940215082"),
    ("👨🏻‍💼 Silvano", "https://wa.me/5511988598736"),
    ("👩🏻‍💼 Solange Ap.",  "https://wa.me/5511974595799"),
]

def _embaralhar_por_janela(lista, dt=None, horas_janela=6):
    dt = dt or agora_sp()
    slot = dt.hour // horas_janela  # 0..3
    seed_val = int(dt.strftime("%Y%m%d")) * 10 + slot
    rng = random.Random(seed_val)
    copia = list(lista)
    rng.shuffle(copia)
    return copia

def vendedores_passeio(dt=None):
    return _embaralhar_por_janela(VENDEDORES_PASSEIO_BASE, dt=dt, horas_janela=6)

def vendedores_util(dt=None):
    return _embaralhar_por_janela(VENDEDORES_UTIL_BASE, dt=dt, horas_janela=6)

def _bloco_vendedores(lista):
    return "\n".join([f"{nome}: {link}" for nome, link in lista])

# ===== Blocos fixos =====
BLOCOS = {
    "1.3": """*Endereço e Site*

🌐 Site: www.sullato.com.br – https://www.sullato.com.br
📸 Instagram: @sullatomicrosevans – https://www.instagram.com/sullatomicrosevans
📸 Instagram: @sullato.veiculos – https://www.instagram.com/sullato.veiculos

🏢 Loja 01: Av. São Miguel, 7900 – cep. 08070-001 - SP
📞 (11) 2030-5081 | (11) 2031-5081

🏢 Loja 02: Av. São Miguel, 4049 – cep. 03871-000 - SP
📞 (11) 2542-3332 | (11) 2542-3333

🏢 Loja 03: Av. São Miguel, 4084 – cep. 03871-000 - SP
📞 (11) 2045-2753""",

    "2.1": """*Oficina e Peças*

📲 Atendimento centralizado pelo WhatsApp oficial da Oficina Sullato:

👉 https://wa.me/5511912115717

Por aqui conseguimos registrar sua solicitação
e direcionar corretamente para o setor responsável.""",

    "2.2": """*Endereço da Oficina*

🏢 Av. Amador Bueno da Veiga, 4222 – cep. 03652-000 - SP
📞 (11) 20922304 | (11) 11994081931""",

    "3": """*Crédito e Financiamento*

✉️ Consulte uma de nossas consultoras.

💰 Magali: https://wa.me/5511940215082
💰 Patrícia: https://wa.me/5511940215081""",

    "3.2.1": """*Oficina e Peças – Passeio*

📲 Atendimento pelo WhatsApp oficial da Oficina Sullato:

👉 https://wa.me/5511912115717""",

    "3.2.2": """*Oficina e Peças – Utilitário*

📲 Atendimento pelo WhatsApp oficial da Oficina Sullato:

👉 https://wa.me/5511912115717""",

    "4.1": """*Vendas Governamentais*

✉️ Consulte nossa consultora.

🏛️ Solange: https://wa.me/5511989536141
📧 E-mail: vendasdireta@sullato.com.br | sol@sullato.com.br""",

    "4.2": """*Veículo por Assinatura*

✉️ Consulte nosso consultor.

📆 Alexsander: https://wa.me/5511996371559
📧 E-mail: alex@sullato.com.br""",
}
# ===== Menus (compatível com as duas versões) =====
BOTOES_MENU_INICIAL = [
    {"type": "reply", "reply": {"id": "1",     "title": "Comprar/Vender"}},
    {"type": "reply", "reply": {"id": "2",     "title": "Oficina/Peças"}},
    {"type": "reply", "reply": {"id": "mais1", "title": "Mais opções"}},
]

# ===== Handler principal =====
def responder(numero: str, mensagem: Any, nome_contato: Optional[str] = None) -> None:
    """Handler unificado: rotação 6h e menus completos + IA leve para texto digitado."""
    # Imports tardios
    try:
        from salvar_em_google_sheets import salvar_em_google_sheets
    except Exception:
        def salvar_em_google_sheets(*_args, **_kwargs): pass
    try:
        from registrar_historico import registrar_interacao
    except Exception:
        def registrar_interacao(*_args, **_kwargs): pass
    try:
        from salvar_em_mala_direta import salvar_em_mala_direta
    except Exception:
        def salvar_em_mala_direta(*_args, **_kwargs): pass
    try:
        from responder_ia import responder_com_ia
    except Exception:
        def responder_com_ia(_msg: str, _nome: Optional[str] = None): return None

    # Extrai ID/Texto e normaliza
    id_recebido = _extrair_id_ou_texto(mensagem)
    id_normalizado = normalizar_id(id_recebido)

    # Nome
    nome_digitado = detectar_nome_digitado(id_recebido) if isinstance(id_recebido, str) else None
    nome_final = normalizar_nome(nome_digitado or nome_contato or "Cliente")
    primeiro_nome = extrair_primeiro_nome_exibicao(nome_final)

    # Registros básicos
    try:
        # 🔥 ENVIA PARA GOOGLE SHEETS (Página1)
        enviar_para_google_sheets(numero, nome_final, "entrada")

        if id_normalizado in ["oi", "olá", "ola", "menu", "inicio", "início"]:
            salvar_em_mala_direta(numero, nome_final)

        # 🔥 GARANTE QUE comandos_conhecidos EXISTE ANTES DE USAR
        comandos_conhecidos = {
            "1","2","3","4.1","4.2","1.1","1.2","1.3","2.1","2.2","3.2.1","3.2.2",
            "passeio","utilitario","utilitário","comprar","mais1","mais2","mais3",
            "btn-oficina","btn-pos-venda","btn-trabalhe","btn-endereco",
            "venda direta","venda-direta","governamental","governamentais",
            "garantia","menu","endereco oficina","endereço oficina"
        }

        if id_recebido and id_normalizado in comandos_conhecidos:
            registrar_interacao(numero, nome_final, id_normalizado)

    except Exception as e:
        print("⚠️ Falha em algum registro inicial:", e)

    # Menu gatilho
    if _tem_trigger_menu(id_normalizado) or id_normalizado == "menu":
        enviar_botoes(
            numero,
            f"Olá, {primeiro_nome}! 😃 Seja bem-vindo ao atendimento virtual do Grupo Sullato. Como posso te ajudar?",
            BOTOES_MENU_INICIAL,
        )
        return

        # ===== IA RÁPIDA para TEXTO digitado (antes dos menus) =====
    # Se a mensagem é texto "solto" (não clique de botão) e não é comando conhecido, NÃO usamos heurística.
    # Em vez disso, respondemos com "não entendi" e mostramos SEMPRE o menu inicial.
    comandos_conhecidos = {
        "1","2","3","4.1","4.2","1.1","1.2","1.3","2.1","2.2","3.2.1","3.2.2",
        "passeio","utilitario","utilitário","comprar","mais1","mais2","mais3","btn-oficina",
        "btn-pos-venda","btn-trabalhe","btn-endereco","venda direta","venda-direta",
        "governamental","governamentais","garantia","menu","endereco oficina","endereço oficina"
    }

    if _is_text_payload(mensagem) and id_normalizado not in comandos_conhecidos:
        try:
            registrar_interacao(numero, nome_final, "Texto livre → Não entendi + Menu inicial")
            atualizar_interesse(numero, "Texto livre → Menu inicial")
        except Exception:
            pass

        enviar_mensagem(
            numero,
            f"Não entendi sua mensagem, {primeiro_nome}. Posso te ajudar por aqui 👇"
        )
        enviar_botoes(
            numero,
            "Escolha uma opção:",
            BOTOES_MENU_INICIAL,
        )
        return

    # ===== Menus topo (cliques de botões) =====
    if id_normalizado in ("1", "comprar"):
        try:
            atualizar_interesse(numero, "Menu - Comprar/Vender")
            registrar_interacao(numero, nome_final, "Menu - Comprar/Vender")
        except Exception as e:
            print("⚠️ registro menu 1 falhou:", e)
        enviar_botoes(numero, "Escolha uma opção de compra/venda:", [
            {"type": "reply", "reply": {"id": "1.1", "title": "Passeio"}},
            {"type": "reply", "reply": {"id": "1.2", "title": "Utilitário"}},
            {"type": "reply", "reply": {"id": "1.3", "title": "Endereço"}},
        ])
        return

    if id_normalizado == "2" or id_normalizado == "btn-oficina":
        try:
            atualizar_interesse(numero, "Menu - Oficina/Peças")
            registrar_interacao(numero, nome_final, "Menu - Oficina/Peças")
        except Exception as e:
            print("⚠️ registro menu 2 falhou:", e)
        enviar_botoes(numero, "Escolha uma opção sobre oficina/peças:", [
            {"type": "reply", "reply": {"id": "3.2.1", "title": "Passeio"}},
            {"type": "reply", "reply": {"id": "3.2.2", "title": "Utilitário"}},
            {"type": "reply", "reply": {"id": "2.2",   "title": "Endereço Oficina"}},
        ])
        return

    if id_normalizado in ("mais1",):
        try:
            atualizar_interesse(numero, "Menu - Mais opções (1)")
            registrar_interacao(numero, nome_final, "Menu - Mais opções (1)")
        except Exception as e:
            print("⚠️ registro mais1 falhou:", e)
        enviar_botoes(numero, "Mais opções:", [
            {"type": "reply", "reply": {"id": "3",             "title": "Crédito"}},
            {"type": "reply", "reply": {"id": "btn-pos-venda", "title": "Pós-venda"}},
            {"type": "reply", "reply": {"id": "mais2",         "title": "Mais opções ▶"}},
        ])
        return

    if id_normalizado in ("mais2", "btn-mais2"):
        try:
            atualizar_interesse(numero, "Menu - Mais opções (2)")
            registrar_interacao(numero, nome_final, "Menu - Mais opções (2)")
        except Exception as e:
            print("⚠️ registro mais2 falhou:", e)
        enviar_botoes(numero, "Outras opções:", [
            {"type": "reply", "reply": {"id": "4.1",  "title": "Governamentais"}},
            {"type": "reply", "reply": {"id": "4.2",  "title": "Assinatura"}},
            {"type": "reply", "reply": {"id": "mais3", "title": "Mais opções ▶"}},
        ])
        return

    if id_normalizado == "mais3":
        try:
            atualizar_interesse(numero, "Menu - Mais opções (3)")
            registrar_interacao(numero, nome_final, "Menu - Mais opções (3)")
        except Exception as e:
            print("⚠️ registro mais3 falhou:", e)
        enviar_botoes(numero, "Mais opções:", [
            {"type": "reply", "reply": {"id": "btn-trabalhe", "title": "Trabalhe conosco"}},
            {"type": "reply", "reply": {"id": "menu",         "title": "Voltar ao início"}},
        ])
        return

    if id_normalizado == "btn-pos-venda":
        try:
            atualizar_interesse(numero, "Menu - Pós-venda")
            registrar_interacao(numero, nome_final, "Menu - Pós-venda")
        except Exception as e:
            print("⚠️ registro pos-venda falhou:", e)
        enviar_botoes(numero, "Pós-venda Sullato - Escolha uma das opções abaixo:", [
            {"type": "reply", "reply": {"id": "3.2.1", "title": "Passeio"}},
            {"type": "reply", "reply": {"id": "3.2.2", "title": "Utilitário"}},
            {"type": "reply", "reply": {"id": "menu",  "title": "Voltar ao início"}},
        ])
        return
    # ===== Folhas / Blocos =====
    if id_normalizado == "2.1":
        try:
            atualizar_interesse(numero, "Interesse - Oficina e Peças")
            registrar_interacao(numero, nome_final, "Interesse - Oficina e Peças")
        except Exception as e:
            print("⚠️ registro 2.1 falhou:", e)
        enviar_mensagem(numero, BLOCOS["2.1"])
        return

    if id_normalizado in ("2.2", "endereco oficina", "endereço oficina"):
        try:
            atualizar_interesse(numero, "Interesse - Endereço Oficina")
            registrar_interacao(numero, nome_final, "Interesse - Endereço Oficina")
        except Exception as e:
            print("⚠️ registro 2.2 falhou:", e)
        enviar_mensagem(numero, BLOCOS["2.2"])
        return

    # IDs literais dos sub-botões (Oficina/Peças e Pós-venda)
    if id_normalizado in ("3.2.1", "3,2,1", "32.1", "32,1", "oficina-passeio", "p-venda-passeio"):
        try:
            atualizar_interesse(numero, "Interesse - Oficina/Peças - Passeio (ID)")
            registrar_interacao(numero, nome_final, "Interesse - Oficina/Peças - Passeio (ID)")
        except Exception as e:
            print("⚠️ registro passeio(ID) falhou:", e)
        enviar_mensagem(numero, BLOCOS["3.2.1"])
        return

    if id_normalizado in ("3.2.2", "3,2,2", "32.2", "32,2", "oficina-utilitario", "p-venda-utilitario"):
        try:
            atualizar_interesse(numero, "Interesse - Oficina/Peças - Utilitário (ID)")
            registrar_interacao(numero, nome_final, "Interesse - Oficina/Peças - Utilitário (ID)")
        except Exception as e:
            print("⚠️ registro utilitario(ID) falhou:", e)
        enviar_mensagem(numero, BLOCOS["3.2.2"])
        return

    # Quando a Meta manda o TÍTULO do botão
    if id_normalizado in ("passeio",):
        try:
            atualizar_interesse(numero, "Interesse - Oficina/Peças - Passeio")
            registrar_interacao(numero, nome_final, "Interesse - Oficina/Peças - Passeio")
        except Exception as e:
            print("⚠️ registro passeio peças falhou:", e)
        enviar_mensagem(numero, BLOCOS["3.2.1"])
        return

    if id_normalizado in ("utilitario", "utilitário"):
        try:
            atualizar_interesse(numero, "Interesse - Oficina/Peças - Utilitário")
            registrar_interacao(numero, nome_final, "Interesse - Oficina/Peças - Utilitário")
        except Exception as e:
            print("⚠️ registro utilitário peças falhou:", e)
        enviar_mensagem(numero, BLOCOS["3.2.2"])
        return

    # Comprar/Vender (rodízio)
    if id_normalizado == "1.1":
        try:
            atualizar_interesse(numero, "Interesse - Passeio")
            registrar_interacao(numero, nome_final, "Interesse - Passeio")
        except Exception as e:
            print("⚠️ registro passeio falhou:", e)
        enviar_mensagem(numero, "*Veículos de Passeio*\n\n" + _bloco_vendedores(vendedores_passeio()))
        return

    if id_normalizado == "1.2":
        try:
            atualizar_interesse(numero, "Interesse - Utilitário")
            registrar_interacao(numero, nome_final, "Interesse - Utilitário")
        except Exception as e:
            print("⚠️ registro utilitario falhou:", e)
        enviar_mensagem(numero, "*Veículos Utilitários*\n\n" + _bloco_vendedores(vendedores_util()))
        return

    if id_normalizado in ("1.3", "btn-endereco"):
        try:
            atualizar_interesse(numero, "Interesse - Endereço Loja")
            registrar_interacao(numero, nome_final, "Interesse - Endereço Loja")
        except Exception as e:
            print("⚠️ registro endereco falhou:", e)
        enviar_mensagem(numero, BLOCOS["1.3"])
        return

    if id_normalizado == "3":
        try:
            atualizar_interesse(numero, "Interesse - Crédito")
            registrar_interacao(numero, nome_final, "Interesse - Crédito")
        except Exception as e:
            print("⚠️ registro credito falhou:", e)
        enviar_mensagem(numero, BLOCOS["3"])
        return

    if id_normalizado == "4.1":
        try:
            atualizar_interesse(numero, "Interesse - Governamentais")
            registrar_interacao(numero, nome_final, "Interesse - Governamentais")
        except Exception as e:
            print("⚠️ registro gov falhou:", e)
        enviar_mensagem(numero, BLOCOS["4.1"])
        return

    if id_normalizado == "4.2":
        try:
            atualizar_interesse(numero, "Interesse - Assinatura")
            registrar_interacao(numero, nome_final, "Interesse - Assinatura")
        except Exception as e:
            print("⚠️ registro assinatura falhou:", e)
        enviar_mensagem(numero, BLOCOS["4.2"])
        return

    # Aliases
    if id_normalizado in ("venda direta", "venda-direta", "vendadireta", "btn-venda-direta", "governamental", "governamentais"):
        try:
            atualizar_interesse(numero, "Interesse - Governamentais (via alias)")
            registrar_interacao(numero, nome_final, "Interesse - Governamentais (alias)")
        except Exception as e:
            print("⚠️ registro gov alias falhou:", e)
        enviar_mensagem(numero, BLOCOS["4.1"])
        return

    if id_normalizado in ("garantia", "btn-garantia"):
        try:
            atualizar_interesse(numero, "Menu - Pós-venda (via Garantia)")
            registrar_interacao(numero, nome_final, "Menu - Pós-venda (alias Garantia)")
        except Exception as e:
            print("⚠️ registro garantia alias falhou:", e)
        enviar_botoes(numero, "Pós-venda Sullato - Escolha uma das opções abaixo:", [
            {"type": "reply", "reply": {"id": "3.2.1", "title": "Passeio"}},
            {"type": "reply", "reply": {"id": "3.2.2", "title": "Utilitário"}},
            {"type": "reply", "reply": {"id": "menu",  "title": "Voltar ao início"}},
        ])
        return

    # Trabalhe Conosco (links wa.me + e-mails)
    if id_normalizado == "btn-trabalhe":
        try:
            atualizar_interesse(numero, "Interesse - Trabalhe Conosco")
            registrar_interacao(numero, nome_final, "Interesse - Trabalhe Conosco")
        except Exception as e:
            print("⚠️ registro Trabalhe Conosco falhou:", e)
        enviar_mensagem(
            numero,
            "*Trabalhe Conosco – Grupo Sullato*\n\n"
            "Sullato Micros e Vans – Anderson: https://wa.me/5511988780161 | anderson@sullato.com.br\n"
            "Sullato Veículos – Alex: https://wa.me/5511996371559 | alex@sullato.com.br\n"
            "Peças e Oficina – Érico: https://wa.me/5511940497678 | erico@sullato.com.br\n\n"
            "Envie seu nome completo, e-mail e um breve resumo da sua experiência.\n"
            "Se preferir, cole seu currículo (texto)."
        )
        return

    # ===== IA externa + heurística para qualquer outro caso =====
    try:
        intencao = interpretar_mensagem(id_normalizado)
    except Exception as e:
        print("⚠️ Erro interpretar_mensagem:", e)
        intencao = None
    if not intencao:
        intencao = detectar_intencao_basica(id_normalizado)

    if intencao:
        mapa = {
            "credito": (BLOCOS.get("3", "💰 Opções de crédito flexíveis. Fale com nossa equipe."), "Interesse - Crédito"),
            "endereco": (BLOCOS.get("1.3", "📍 Endereços atualizados das lojas."), "Interesse - Endereço Loja"),
            "comprar": ("🚗 Temos vans, utilitários e veículos de passeio esperando por você!", "Interesse - Comprar"),
            "vender": ("📝 Avaliamos seu veículo e cuidamos da intermediação para vender rapidamente.", "Interesse - Vender"),
            "pos_venda": ("🔧 Nosso pós-venda está pronto para te atender! Quer suporte agora?", "Interesse - Pós-venda"),
        }
        if intencao in mapa:
            texto, label = mapa[intencao]
            enviar_mensagem(numero, texto)
            try:
                atualizar_interesse(numero, label)
                registrar_interacao(numero, nome_final, f"IA/Heurística - {label}")
            except Exception as e:
                print("⚠️ registro IA/heurística falhou:", e)
            return

    # ===== Fallback → Quick Menu (garantia de resposta útil) =====
    try:
        registrar_interacao(numero, nome_final, "Fallback → QuickMenu")
        atualizar_interesse(numero, "Fallback → QuickMenu")
    except Exception as e:
        print("⚠️ registro fallback quick falhou:", e)

    enviar_botoes(numero, "Posso te ajudar com algo específico? Escolha abaixo:", [
        {"type": "reply", "reply": {"id": "1", "title": "Comprar/Vender"}},
        {"type": "reply", "reply": {"id": "2", "title": "Oficina/Peças"}},
        {"type": "reply", "reply": {"id": "mais1", "title": "Mais opções"}},
    ])
    return
