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

def _parece_detalhe_trabalho(texto: str) -> bool:
    if not texto:
        return False
    texto_l = texto.lower()
    chaves = [
        "curriculo", "currículo", "experiencia", "experiência", "emprego", "trabalhar",
        "vaga", "vagas", "rh", "salario", "salário", "contratacao", "contratação",
    ]
    if any(c in texto_l for c in chaves): return True
    if re.search(r"[\w\.-]+@[\w\.-]+", texto, re.I): return True
    if sum(ch.isdigit() for ch in texto) >= 8: return True
    if len(texto.strip()) >= 120: return True
    return False

# === Helpers p/ WhatsApp ===
def _extrair_id_ou_texto(msg) -> str:
    """Extrai ID de botão ou texto do payload, cobrindo os formatos comuns da Meta."""
    try:
        if isinstance(msg, str):
            return msg
        if isinstance(msg, dict):
            inter = msg.get("interactive") or {}
            if inter.get("type") == "button":
                # button_reply.title/id, nfm_reply.id (algumas contas)
                br = inter.get("button_reply") or inter.get("nfm_reply") or {}
                return br.get("id") or br.get("title") or ""
            # mensagens de texto padrão
            if "text" in msg and isinstance(msg["text"], dict):
                return msg["text"].get("body", "")
            if "type" in msg and msg["type"] == "text" and "text" in msg:
                return msg["text"].get("body", "")
            # variações aninhadas
            if "messages" in msg and isinstance(msg["messages"], list) and msg["messages"]:
                return _extrair_id_ou_texto(msg["messages"][0])
        return ""
    except Exception:
        return ""

def _tem_trigger_menu(id_norm: str) -> bool:
    return re.search(r"\b(oi|ola|menu|inicio|start|ajuda|help|voltar|voltar ao inicio)\b", f" {id_norm} ") is not None

# ===== Rodízio de vendedores (varia a cada 6h) =====
VENDEDORES_PASSEIO_BASE = [
    ("👨🏻‍💼 Alexandre", "https://wa.me/5511940559880"),
    ("👨🏻‍💼 Jeferson",  "https://wa.me/5511941006862"),
    ("👩🏻‍💼 Marcela",   "https://wa.me/5511912115673"),
    ("👨🏻‍💼 Pedro",     "https://wa.me/5511992037103"),
    ("👨🏻‍💼 Thiago",    "https://wa.me/5511986122905"),
    ("👩🏻‍💼 Vanessa",   "https://wa.me/5511947954378"),
    ("👨🏻‍💼 Vinicius",  "https://wa.me/5511911260469"),
]
VENDEDORES_UTIL_BASE = [
    ("👩🏻‍💼 Magali",  "https://wa.me/5511940215082"),
    ("👨🏻‍💼 Silvano", "https://wa.me/5511988598736"),
    ("👨🏻‍💼 Thiago",  "https://wa.me/5511986122905"),
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

# ===== Blocos fixos (inclui Governamentais / Assinatura / Crédito / Pós-venda) =====
BLOCOS = {
    "1.3": """*Endereço e Site*

🌐 Site: www.sullato.com.br – https://www.sullato.com.br
📸 Instagram: @sullatomicrosevans – https://www.instagram.com/sullatomicrosevans
📸 Instagram: @sullato.veiculos – https://www.instagram.com/sullato.veiculos

🏢 Loja 01: Av. São Miguel, 7900 – cep. 08070-001 - SP
📞 (11) 2030-5081 | (11) 2031-5081

🏢 Loja 02/03: Av. São Miguel, 4049/4084 – cep. 03871-000 - SP
📞 (11) 2542-3332 | (11) 2542-3333""",

    "2.1": """*Oficina e Peças*

✉️ Consulte um de nossos consultores.

🔧 Erico: https://wa.me/5511940497678
🔧 Leandro: https://wa.me/5511940443566""",

    "2.2": """*Endereço da Oficina*

🏢 Loja 02: Av. São Miguel, 4049 – cep. 03871-000 - SP
📞 (11) 2542-3332 | (11) 2542-3333""",

    "3": """*Crédito e Financiamento*

✉️ Consulte uma de nossas consultoras.

💰 Magali: https://wa.me/5511940215082
💰 Patrícia: https://wa.me/5511940215081""",

    "3.2.1": """*Pós-venda – Passeio*

✉️ Consulte um de nossos consultores.

🔧 Leandro: https://wa.me/5511940443566""",

    "3.2.2": """*Pós-venda – Utilitário*

✉️ Consulte um de nossos consultores.

🔧 Erico: https://wa.me/5511940497678""",

    "4.1": """*Vendas Governamentais*

✉️ Consulte nossa consultora.

🏛️ Solange: https://wa.me/5511989536141""",

    "4.2": """*Veículo por Assinatura*

✉️ Consulte nosso consultor.

📆 Alexsander: https://wa.me/5511996371559""",
}

# ===== Menus (compatível com as duas versões) =====
# Menu inicial (3 botões)
BOTOES_MENU_INICIAL = [
    {"type": "reply", "reply": {"id": "1",     "title": "Comprar/Vender"}},
    {"type": "reply", "reply": {"id": "2",     "title": "Oficina/Peças"}},
    {"type": "reply", "reply": {"id": "mais1", "title": "Mais opções"}},
]

# ===== Handler principal =====
def responder(numero: str, mensagem: Any, nome_contato: Optional[str] = None) -> None:
    """Handler unificado: mantém rotação 6h dos vendedores e restaura todos os menus/botões."""
    # Imports tardios (evita crash se módulos não existirem)
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
        salvar_em_mala_direta(numero, nome_final)
        salvar_em_google_sheets(numero, nome_final, "Primeiro contato")
        registrar_interacao(numero, nome_final, "Primeiro contato")
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

    # ===== Menus topo =====
    # 1) COMPRAR/VENDER → 1.1 / 1.2 / 1.3
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

    # 2) OFICINA/PEÇAS → 2.1 / 2.2
    if id_normalizado == "2" or id_normalizado == "btn-oficina":
        try:
            atualizar_interesse(numero, "Menu - Oficina/Peças")
            registrar_interacao(numero, nome_final, "Menu - Oficina/Peças")
        except Exception as e:
            print("⚠️ registro menu 2 falhou:", e)
        enviar_botoes(numero, "Escolha uma opção sobre oficina/peças:", [
            {"type": "reply", "reply": {"id": "2.1", "title": "Oficina e Peças"}},
            {"type": "reply", "reply": {"id": "2.2", "title": "Endereço Oficina"}},
        ])
        return

    # 3) MAIS OPÇÕES (compat: aceita "3" e "mais1")
    if id_normalizado in ("3", "mais1"):
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

    # MAIS OPÇÕES nível 2 (compat: aceita btn-mais2)
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

    # MAIS OPÇÕES nível 3
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

    # Pós-venda (submenu)
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

    if id_normalizado == "3":  # Crédito (folha)
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

    if id_normalizado == "btn-venda-direta":
        try:
            atualizar_interesse(numero, "Interesse - Venda Direta")
            registrar_interacao(numero, nome_final, "Interesse - Venda Direta")
        except Exception as e:
            print("⚠️ registro venda direta falhou:", e)
        enviar_mensagem(
            numero,
            "*Venda Direta*\n\n"
            "Para veículos direto com a Sullato (CNPJ), fale com nosso time comercial.\n\n"
            + _bloco_vendedores(vendedores_passeio())
        )
        return

    # ===== Aliases adicionais (Venda Direta ≡ Governamentais | Garantia ≡ Pós-venda) =====
    # Venda Direta → usar o mesmo conteúdo de Governamentais (4.1)
    if id_normalizado in ("venda direta", "venda-direta", "vendadireta", "btn-venda-direta", "governamental", "governamentais"):
        try:
            atualizar_interesse(numero, "Interesse - Governamentais (via alias)")
            registrar_interacao(numero, nome_final, "Interesse - Governamentais (alias)")
        except Exception as e:
            print("⚠️ registro gov alias falhou:", e)
        enviar_mensagem(numero, BLOCOS["4.1"])  # mesmo bloco das vendas governamentais
        return

    # Garantia → abrir o submenu de Pós-venda
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

    # ===== Trabalhe Conosco =====
    if id_normalizado == "btn-trabalhe":
        try:
            atualizar_interesse(numero, "Trabalhe Conosco - Abriu formulário")
            registrar_interacao(numero, nome_final, "Trabalhe Conosco - Abriu formulário")
        except Exception as e:
            print("⚠️ registro Trabalhe Conosco falhou:", e)
        enviar_mensagem(
            numero,
            "*Trabalhe Conosco - Grupo Sullato*\n\n"
            "Envie seu nome completo, e-mail e um breve resumo da sua experiência.\n"
            "Se preferir, cole seu currículo (texto)."
        )
        return

    # Texto livre com dados de candidatura
    if not isinstance(mensagem, dict) and _parece_detalhe_trabalho(id_recebido):
        enviar_email(
            "Detalhes de candidatura - Trabalhe Conosco (Sullato)",
            (
                f"Data/Hora (SP): {agora_sp().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Nome (detectado): {nome_final}\n"
                f"WhatsApp: {numero}\n"
                f"Mensagem:\n{id_recebido}\n"
            ),
        )
        try:
            registrar_interacao(numero, nome_final, "Trabalhe Conosco - Dados enviados")
        except Exception as e:
            print("⚠️ registrar_interacao falhou:", e)
        enviar_mensagem(numero, "Obrigado! Seus dados foram encaminhados ao nosso RH. Entraremos em contato.")
        return

    # ===== Classificação por IA (se disponível) =====
    try:
        intencao = interpretar_mensagem(id_normalizado)
    except Exception as e:
        print("⚠️ Erro interpretar_mensagem:", e)
        intencao = None

    if intencao:
        mapa = {
            "credito": ("💰 Aqui na Sullato temos opções de crédito flexíveis...", "Interesse - Crédito"),
            "endereco": ("📍 Estamos em dois endereços: Av. São Miguel, 7900 e 4049/4084 – São Paulo.", "Interesse - Endereço Loja"),
            "comprar": ("🚗 Temos vans, utilitários e veículos de passeio esperando por você!", "Interesse - Comprar"),
            "vender": ("📝 Avaliamos seu veículo e cuidamos de toda a intermediação para vender rapidamente.", "Interesse - Vender"),
            "pos_venda": ("🔧 Nosso pós-venda está pronto para te atender! Quer suporte agora?", "Interesse - Pós-venda"),
        }
        if intencao in mapa:
            texto, label = mapa[intencao]
            enviar_mensagem(numero, texto)
            try:
                atualizar_interesse(numero, label)
                registrar_interacao(numero, nome_final, f"IA - {label}")
            except Exception as e:
                print("⚠️ registro IA falhou:", e)
            return

    # ===== Resposta livre por IA (fallback) =====
    try:
        resposta = responder_com_ia(id_recebido, nome_final)
    except Exception as e:
        print("⚠️ Erro responder_com_ia:", e)
        resposta = None

    if resposta:
        enviar_mensagem(numero, resposta)
        try:
            registrar_interacao(numero, nome_final, "IA - Resposta livre")
        except Exception as e:
            print("⚠️ registrar_interacao falhou:", e)
        return

    # ===== Fallback final → Menu =====
    try:
        registrar_interacao(numero, nome_final, "Fallback → Menu")
        atualizar_interesse(numero, "Fallback → Menu")
    except Exception as e:
        print("⚠️ registro fallback falhou:", e)
    enviar_botoes(
        numero,
        f"Não entendi. Escolha uma das opções abaixo, {primeiro_nome}:",
        BOTOES_MENU_INICIAL,
    )
    return
