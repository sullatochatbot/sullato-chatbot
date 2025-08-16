import os
import random
import requests
import unicodedata
import re
import smtplib
import ssl
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any, Tuple

from zoneinfo import ZoneInfo

# Fuso horário de São Paulo
TZ_SP = ZoneInfo("America/Sao_Paulo")

def agora_sp():
    return datetime.now(TZ_SP)

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
    if not txt: return ""
    nfkd_form = unicodedata.normalize("NFKD", txt)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def normalizar_id(texto: str) -> str:
    if not texto: return ""
    t = texto.strip()
    t = remover_acentos(t).lower()
    t = re.sub(r"\s+", " ", t)
    return t

def extrair_primeiro_nome_exibicao(nome: Optional[str]) -> str:
    if not nome: return "Cliente"
    nome = nome.strip()
    if not nome: return "Cliente"
    partes = nome.split()
    if len(partes) == 0: return "Cliente"
    primeiro = partes[0]
    # Evita coisas tipo "11 9 9999-9999"
    if re.fullmatch(r"\d[\d\s\-()+]*", primeiro or ""):
        return "Cliente"
    return primeiro.capitalize()

def detectar_nome_digitado(texto: str) -> Optional[str]:
    if not texto: return None
    texto = texto.strip()
    padroes = [
        r"meu nome e ([a-zA-ZÀ-ÿ\s]+)",
        r"meu nome é ([a-zA-ZÀ-ÿ\s]+)",
        r"me chamo ([a-zA-ZÀ-ÿ\s]+)",
        r"sou o ([a-zA-ZÀ-ÿ\s]+)",
        r"sou a ([a-zA-ZÀ-ÿ\s]+)",
        r"nome e ([a-zA-ZÀ-ÿ\s]+)",
    ]
    for p in padroes:
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
    """Envia e-mail via SMTP (TLS). Retorna True se OK."""
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
    """Extrai ID de botão ou texto do payload, em vários formatos que a Meta envia."""
    try:
        if isinstance(msg, str):
            return msg
        if isinstance(msg, dict):
            # interactive → button
            inter = msg.get("interactive") or {}
            if inter.get("type") == "button":
                return inter.get("button_reply", {}).get("id") or inter.get("nfm_reply", {}).get("id") or ""
            # text
            if "text" in msg and isinstance(msg["text"], dict):
                return msg["text"].get("body", "")
            # type message
            if "type" in msg and msg["type"] == "text" and "text" in msg:
                return msg["text"].get("body", "")
        return ""
    except Exception:
        return ""

def _tem_trigger_menu(id_normalizado: str) -> bool:
    t = f" {id_normalizado} "
    return re.search(r"\b(oi|ola|menu|inicio|start|ajuda|help|voltar|voltar ao inicio)\b", t) is not None

# =============================
# Rodízio diário de vendedores (1.1 e 1.2)
# =============================

# =============================
# Rodízio de vendedores (varia a cada 6 horas, por fuso de São Paulo)
# =============================
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
    """
    Embaralhamento determinístico por janela de horas.
    Ex.: horas_janela=6 => novas posições em 00:00, 06:00, 12:00, 18:00 (fuso SP).
    """
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

# =============================
# Blocos fixos (folhas)
# =============================
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

📍 Av. São Miguel, 7900 – São Paulo/SP (Loja 01)
⏱️ Atendimento: Segunda a Sexta, 08:00 às 18:00

Nosso time técnico está pronto para te ajudar!""",
}
# =============================
# Menus (botões)
# =============================
BOTOES_MENU_INICIAL = [
    {"type": "reply", "reply": {"id": "1", "title": "Comprar / Vender"}},
    {"type": "reply", "reply": {"id": "2", "title": "Oficina e Peças"}},
    {"type": "reply", "reply": {"id": "3", "title": "Mais opções"}},
]

BOTOES_MENU_MAIS1 = [
    {"type": "reply", "reply": {"id": "1", "title": "Comprar / Vender"}},
    {"type": "reply", "reply": {"id": "btn-endereco", "title": "Endereço"}},
    {"type": "reply", "reply": {"id": "btn-venda-direta", "title": "Venda Direta"}},
]

BOTOES_MENU_MAIS2 = [
    {"type": "reply", "reply": {"id": "btn-garantia", "title": "Garantia"}},
    {"type": "reply", "reply": {"id": "btn-oficina", "title": "Oficina e Peças"}},
    {"type": "reply", "reply": {"id": "menu", "title": "Voltar ao início"}},
]

# =============================
# Handler principal
# =============================
def responder(numero: str, mensagem: Any, nome_contato: Optional[str] = None) -> None:
    """
    numero: string do WhatsApp em E.164
    mensagem: payload dict da Meta ou texto puro
    nome_contato: nome vindo do webhook quando disponível
    """
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
        def responder_com_ia(_msg: str, _nome: Optional[str] = None):
            return None

    # Extrai ID ou texto digitado
    id_recebido = _extrair_id_ou_texto(mensagem)
    id_normalizado = normalizar_id(id_recebido)

    # Nome preferencial (prioriza nome digitado no texto; senão o de contato)
    nome_digitado = detectar_nome_digitado(id_recebido) if isinstance(id_recebido, str) else None
    nome_final = normalizar_nome(nome_digitado or nome_contato or "Cliente")
    primeiro_nome = extrair_primeiro_nome_exibicao(nome_final)

    # Saudações automáticas / captação de nome (ex.: “oi”, “olá”, “menu” etc.)
    if not id_normalizado:
        id_normalizado = ""

    # Registra contato na base mínima (mala direta)
    try:
        salvar_em_mala_direta(numero, nome_final)
    except Exception as e:
        print("⚠️ Falha ao salvar em mala direta:", e)

    # Gatilho de Menu (oi/ola/menu/inicio/ajuda/voltar)
    if _tem_trigger_menu(id_normalizado) or id_normalizado == "menu":
        enviar_botoes(
            numero,
            f"Olá, {primeiro_nome}! 😃 Seja bem-vindo ao atendimento virtual do Grupo Sullato. Como posso te ajudar?",
            BOTOES_MENU_INICIAL
        )
        return

    # ===== Menus topo =====
    # 1) COMPRAR/VENDER → reutiliza 1.1/1.2/1.3
    if id_normalizado == "1" or id_normalizado == "comprar":
        atualizar_interesse(numero, "Menu - Comprar/Vender")
        registrar_interacao(numero, nome_final, "Menu - Comprar/Vender")
        enviar_botoes(numero, "Escolha uma opção de compra/venda:", [
            {"type": "reply", "reply": {"id": "1.1", "title": "Passeio"}},
            {"type": "reply", "reply": {"id": "1.2", "title": "Utilitário"}},
            {"type": "reply", "reply": {"id": "1.3", "title": "Endereço"}},
        ])
        return

    # 2) OFICINA/PEÇAS → submenu com 2.1 e 2.2
    if id_normalizado == "2":
        atualizar_interesse(numero, "Menu - Oficina/Peças")
        registrar_interacao(numero, nome_final, "Menu - Oficina/Peças")
        enviar_botoes(numero, "Escolha uma opção sobre oficina/peças:", [
            {"type": "reply", "reply": {"id": "2.1", "title": "Oficina e Peças"}},
            {"type": "reply", "reply": {"id": "2.2", "title": "Endereço Oficina"}},
        ])
        return

    # 3) MAIS OPÇÕES (em camadas)
    if id_normalizado == "3":
        atualizar_interesse(numero, "Menu - Mais opções (1)")
        registrar_interacao(numero, nome_final, "Menu - Mais opções (1)")
        enviar_botoes(numero, "Mais opções:", [
            {"type": "reply", "reply": {"id": "btn-endereco", "title": "Endereço"}},
            {"type": "reply", "reply": {"id": "btn-venda-direta", "title": "Venda Direta"}},
            {"type": "reply", "reply": {"id": "btn-mais2", "title": "Mais opções ▶"}},
        ])
        return

    if id_normalizado == "btn-mais2":
        atualizar_interesse(numero, "Menu - Mais opções (2)")
        registrar_interacao(numero, nome_final, "Menu - Mais opções (2)")
        enviar_botoes(numero, "Mais opções:", [
            {"type": "reply", "reply": {"id": "btn-garantia", "title": "Garantia"}},
            {"type": "reply", "reply": {"id": "btn-oficina", "title": "Oficina e Peças"}},
            {"type": "reply", "reply": {"id": "btn-mais3", "title": "Mais opções ▶"}},
        ])
        return

    if id_normalizado == "btn-mais3":
        atualizar_interesse(numero, "Menu - Mais opções (3)")
        registrar_interacao(numero, nome_final, "Menu - Mais opções (3)")
        enviar_botoes(numero, "Mais opções:", [
            {"type": "reply", "reply": {"id": "btn-trabalhe", "title": "Trabalhe conosco"}},
            {"type": "reply", "reply": {"id": "menu",         "title": "Voltar ao início"}},
        ])
        return

    # Pós-venda (mantido)
    if id_normalizado == "btn-pos-venda":
        atualizar_interesse(numero, "Menu - Pós-venda")
        registrar_interacao(numero, nome_final, "Menu - Pós-venda")
        enviar_botoes(numero, "Pós-venda Sullato - Escolha uma das opções abaixo:", [
            {"type": "reply", "reply": {"id": "3.2.1", "title": "Passeio"}},
            {"type": "reply", "reply": {"id": "3.2.2", "title": "Utilitário"}},
            {"type": "reply", "reply": {"id": "menu",  "title": "Voltar ao início"}},
        ])
        return

    # ===== Folhas / Blocos (mantidas/ajustadas) =====
    if id_normalizado == "1.1":
        atualizar_interesse(numero, "Interesse - Passeio")
        registrar_interacao(numero, nome_final, "Interesse - Passeio")
        enviar_mensagem(numero, "*Veículos de Passeio*\n\n" + _bloco_vendedores(vendedores_passeio()))
        return

    if id_normalizado == "1.2":
        atualizar_interesse(numero, "Interesse - Utilitário")
        registrar_interacao(numero, nome_final, "Interesse - Utilitário")
        enviar_mensagem(numero, "*Veículos Utilitários*\n\n" + _bloco_vendedores(vendedores_util()))
        return

    if id_normalizado == "1.3" or id_normalizado == "btn-endereco":
        atualizar_interesse(numero, "Interesse - Endereço Loja")
        registrar_interacao(numero, nome_final, "Interesse - Endereço Loja")
        enviar_mensagem(numero, BLOCOS["1.3"])
        return

    if id_normalizado == "btn-venda-direta":
        atualizar_interesse(numero, "Interesse - Venda Direta")
        registrar_interacao(numero, nome_final, "Interesse - Venda Direta")
        enviar_mensagem(
            numero,
            "*Venda Direta*\n\n"
            "Para veículos direto com a Sullato (CNPJ), fale com nosso time comercial.\n\n"
            + _bloco_vendedores(vendedores_passeio())
        )
        return

    if id_normalizado == "btn-garantia":
        atualizar_interesse(numero, "Interesse - Garantia")
        registrar_interacao(numero, nome_final, "Interesse - Garantia")
        enviar_mensagem(
            numero,
            "*Garantia Sullato*\n\n"
            "Todos os veículos da Sullato contam com garantia legal e suporte do nosso time. "
            "Fale com um consultor para entender os detalhes do seu caso.\n\n"
            + _bloco_vendedores(vendedores_util())
        )
        return

    if id_normalizado == "btn-oficina" or id_normalizado == "2.1":
        atualizar_interesse(numero, "Interesse - Oficina e Peças")
        registrar_interacao(numero, nome_final, "Interesse - Oficina e Peças")
        enviar_mensagem(numero, BLOCOS["2.1"])
        return

    if id_normalizado == "2.2":
        atualizar_interesse(numero, "Interesse - Endereço da Oficina")
        registrar_interacao(numero, nome_final, "Interesse - Endereço da Oficina")
        enviar_mensagem(numero, BLOCOS["2.2"])
        return
    # ===== Trabalhe Conosco =====
    if id_normalizado == "btn-trabalhe":
        atualizar_interesse(numero, "Trabalhe Conosco - Abriu formulário")
        registrar_interacao(numero, nome_final, "Trabalhe Conosco - Abriu formulário")
        enviar_mensagem(
            numero,
            "*Trabalhe Conosco - Grupo Sullato*\n\n"
            "Envie seu nome completo, e-mail e um breve resumo da sua experiência.\n"
            "Se preferir, cole seu currículo (texto)."
        )
        return

    # Se o usuário enviar dados de candidatura como texto
    if not isinstance(mensagem, dict) and _parece_detalhe_trabalho(id_recebido):
        enviar_email(
            "Detalhes de candidatura - Trabalhe Conosco (Sullato)",
            (
                f"Data/Hora: {agora_sp().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Nome (detectado): {nome_final}\n"
                f"WhatsApp: {numero}\n"
                f"Mensagem:\n{id_recebido}\n"
            ),
        )
        enviar_mensagem(numero, "Obrigado! Seus dados foram encaminhados ao nosso RH. Entraremos em contato.")
        registrar_interacao(numero, nome_final, "Trabalhe Conosco - Dados enviados")
        return

    # ===== Classificação por IA (se disponível) =====
    intencao = None
    try:
        intencao = interpretar_mensagem(id_normalizado)
    except Exception as e:
        print("⚠️ Erro interpretar_mensagem:", e)

    if intencao:
        mapa = {
            "credito": (
                "💰 Aqui na Sullato temos opções de crédito flexíveis, mesmo para quem está começando. "
                "Podemos avaliar seu perfil e propor a melhor alternativa. Me chama que explico como funciona.",
                "Interesse - Crédito"
            ),
            "endereco": (
                "📍 Estamos em dois endereços: Av. São Miguel, 7900 e 4049/4084 – São Paulo.",
                "Interesse - Endereço Loja"
            ),
            "comprar": (
                "🚗 Temos vans, utilitários e veículos de passeio esperando por você!",
                "Interesse - Comprar"
            ),
            "vender": (
                "📝 Avaliamos seu veículo e cuidamos de toda a intermediação para vender rapidamente.",
                "Interesse - Vender"
            ),
            "pos_venda": (
                "🔧 Nosso pós-venda está pronto para te atender! Quer suporte agora?",
                "Interesse - Pós-venda"
            ),
        }
        if intencao in mapa:
            texto, label = mapa[intencao]
            enviar_mensagem(numero, texto)
            atualizar_interesse(numero, label)
            registrar_interacao(numero, nome_final, f"IA - {label}")
            return

    # ===== Resposta livre por IA (fallback inteligente) =====
    resposta = None
    try:
        resposta = responder_com_ia(id_recebido, nome_final)
    except Exception as e:
        print("⚠️ Erro responder_com_ia:", e)

    if resposta:
        enviar_mensagem(numero, resposta)
        registrar_interacao(numero, nome_final, "IA - Resposta livre")
        return

    # ===== Fallback final → Menu =====
    registrar_interacao(numero, nome_final, "Fallback → Menu")
    atualizar_interesse(numero, "Fallback → Menu")
    enviar_botoes(
        numero,
        f"Não entendi. Escolha uma das opções abaixo, {primeiro_nome}:",
        BOTOES_MENU_INICIAL
    )
    return
