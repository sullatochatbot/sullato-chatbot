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

# =============================
# Imports de módulos do projeto
# =============================
try:
    from interpretar_ia import interpretar_mensagem
except Exception:
    try:
        from interpretador_ia import interpretar_mensagem  # compatibilidade se existir
    except Exception:
        def interpretar_mensagem(_msg: str):
            return None

from salvar_em_google_sheets import salvar_em_google_sheets
from atualizar_google_sheets import atualizar_interesse_google_sheets
from registrar_historico import registrar_interacao
from salvar_em_mala_direta import salvar_em_mala_direta

try:
    from responder_ia import responder_com_ia
except Exception:
    def responder_com_ia(_msg: str, _nome: Optional[str] = None):
        return None

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
def _normalize(texto: str) -> str:
    if not isinstance(texto, str):
        return ""
    texto = texto.strip().lower()
    texto = unicodedata.normalize('NFD', texto)
    return ''.join(c for c in texto if unicodedata.category(c) != 'Mn')

def _safe_title(nome: Optional[str]) -> str:
    try:
        return (nome or "Desconhecido").title()
    except Exception:
        return "Desconhecido"

def extrair_nome(texto: str) -> Optional[str]:
    texto = (texto or "").lower()
    padroes = [
        r"meu nome e ([a-zA-ZÀ-ÿ\s]+)",
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
        )
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo(); server.starttls(context=context); server.ehlo()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_FROM, [to_addr], msg.encode('utf-8'))
        print("📧 E-mail enviado para", to_addr)
        return True
    except Exception as e:
        print("❌ Erro ao enviar e-mail:", e)
        return False

def enviar_mensagem(numero: str, texto: str) -> None:
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": numero, "type": "text", "text": {"body": texto}}
    try:
        r = requests.post(url, headers=headers, json=payload)
        print("➡️ Meta texto:", r.status_code, r.text)
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
            inter = msg.get("interactive")
            if isinstance(inter, dict):
                br = inter.get("button_reply") or inter.get("list_reply")
                if isinstance(br, dict):
                    return br.get("id") or br.get("title") or ""
            t = msg.get("text")
            if isinstance(t, dict) and "body" in t:
                return t.get("body") or ""
            t2 = msg.get("message")
            if isinstance(t2, dict) and "text" in t2 and isinstance(t2["text"], dict):
                return t2["text"].get("body") or ""
            msgs = msg.get("messages")
            if isinstance(msgs, list) and msgs:
                return _extrair_id_ou_texto(msgs[0])
        return str(msg or "")
    except Exception:
        return str(msg or "")

def _tem_trigger_menu(texto: str) -> bool:
    """True se o usuário pedir o menu (oi/ola/menu/inicio/ajuda/voltar)."""
    t = _normalize(texto)
    return re.search(r"\b(oi|ola|menu|inicio|start|ajuda|help|voltar|voltar ao inicio)\b", t) is not None

# =============================
# Rodízio diário de vendedores (1.1 e 1.2)
# =============================
random.seed(datetime.now().strftime('%Y%m%d'))
VENDEDORES_PASSEIO: List[Tuple[str, str]] = [
    ("👨🏻‍💼 Alexandre", "https://wa.me/5511940559880"),
    ("👨🏻‍💼 Jeferson",  "https://wa.me/5511941006862"),
    ("👩🏻‍💼 Marcela",   "https://wa.me/5511912115673"),
    ("👨🏻‍💼 Pedro",     "https://wa.me/5511992037103"),
    ("👨🏻‍💼 Thiago",    "https://wa.me/5511986122905"),
    ("👩🏻‍💼 Vanessa",   "https://wa.me/5511947954378"),
    ("👨🏻‍💼 Vinicius",  "https://wa.me/5511911260469"),
]
random.shuffle(VENDEDORES_PASSEIO)

VENDEDORES_UTIL: List[Tuple[str, str]] = [
    ("👩🏻‍💼 Magali",  "https://wa.me/5511940215082"),
    ("👨🏻‍💼 Silvano", "https://wa.me/5511988598736"),
    ("👨🏻‍💼 Thiago",  "https://wa.me/5511986122905"),
]
random.shuffle(VENDEDORES_UTIL)

def _bloco_vendedores(lista: List[Tuple[str, str]]) -> str:
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

# =============================
# Menu inicial (3 botões)
# =============================
BOTOES_MENU_INICIAL = [
    {"type": "reply", "reply": {"id": "1",     "title": "Comprar/Vender"}},
    {"type": "reply", "reply": {"id": "2",     "title": "Oficina/Peças"}},
    {"type": "reply", "reply": {"id": "mais1", "title": "Mais opções"}},
]
# =============================
# Lógica principal
# =============================
def gerar_resposta(mensagem, numero: str, nome_cliente: Optional[str] = None):
    numero = ''.join(filter(str.isdigit, str(numero)))

    # Extrai texto/ID de forma robusta
    id_recebido = _extrair_id_ou_texto(mensagem)
    id_normalizado = _normalize(id_recebido)

    # Nome detectado (se digitado no texto)
    if not nome_cliente:
        nome_detectado = extrair_nome(id_normalizado)
        if nome_detectado:
            nome_cliente = nome_detectado
    nome_final = _safe_title(nome_cliente)

    # Registro inicial (planilha, histórico, mala direta)
    try:
        salvar_em_google_sheets(numero, nome_final, "Primeiro contato")
        registrar_interacao(numero, nome_final, "Primeiro contato")
        salvar_em_mala_direta(numero, nome_final)
    except Exception as e:
        print("⚠️ Falha em algum registro inicial:", e)

    # Gatilho de Menu (oi/ola/menu/inicio/ajuda/voltar)
    if _tem_trigger_menu(id_recebido) or id_normalizado == "menu":
        enviar_botoes(
            numero,
            f"Olá, {nome_final}! 😃 Seja bem-vindo ao atendimento virtual do Grupo Sullato. Como posso te ajudar?",
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

    # 2) OFICINA/PEÇAS → submenu com 2.1 e 2.2  (<<< AJUSTADO AQUI)
    if id_normalizado == "2":
        atualizar_interesse(numero, "Menu - Oficina/Peças")
        registrar_interacao(numero, nome_final, "Menu - Oficina/Peças")
        enviar_botoes(numero, "Escolha uma opção sobre oficina/peças:", [
            {"type": "reply", "reply": {"id": "2.1", "title": "Oficina e Peças"}},
            {"type": "reply", "reply": {"id": "2.2", "title": "Endereço Oficina"}},
        ])
        return

    # ===== Cadeia de 'Mais opções' em 3 níveis =====
    # Nível 1: Crédito / Pós-venda / Mais opções
    if id_normalizado == "mais1":
        atualizar_interesse(numero, "Menu - Mais opções (1)")
        registrar_interacao(numero, nome_final, "Menu - Mais opções (1)")
        enviar_botoes(numero, "Mais opções:", [
            {"type": "reply", "reply": {"id": "3",             "title": "Crédito"}},
            {"type": "reply", "reply": {"id": "btn-pos-venda", "title": "Pós-venda"}},
            {"type": "reply", "reply": {"id": "mais2",         "title": "Mais opções"}},
        ])
        return

    # Nível 2: Governamentais / Assinatura / Mais opções
    if id_normalizado == "mais2":
        atualizar_interesse(numero, "Menu - Mais opções (2)")
        registrar_interacao(numero, nome_final, "Menu - Mais opções (2)")
        enviar_botoes(numero, "Outras opções:", [
            {"type": "reply", "reply": {"id": "4.1",  "title": "Governamentais"}},
            {"type": "reply", "reply": {"id": "4.2",  "title": "Assinatura"}},
            {"type": "reply", "reply": {"id": "mais3","title": "Mais opções"}},
        ])
        return

    # Nível 3: Trabalhe / Voltar ao início
    if id_normalizado == "mais3":
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
    # ===== Folhas / Blocos (mantidas) =====
    if id_normalizado == "1.1":
        atualizar_interesse(numero, "Interesse - Passeio")
        registrar_interacao(numero, nome_final, "Interesse - Passeio")
        enviar_mensagem(numero, "*Veículos de Passeio*\n\n" + _bloco_vendedores(VENDEDORES_PASSEIO))
        return

    if id_normalizado == "1.2":
        atualizar_interesse(numero, "Interesse - Utilitário")
        registrar_interacao(numero, nome_final, "Interesse - Utilitário")
        enviar_mensagem(numero, "*Veículos Utilitários*\n\n" + _bloco_vendedores(VENDEDORES_UTIL))
        return

    if id_normalizado in BLOCOS:
        interesse_map = {
            "1.3": "Interesse - Endereço Loja",
            "2.1": "Interesse - Oficina e Peças",
            "2.2": "Interesse - Endereço Oficina",
            "3":   "Interesse - Crédito",
            "3.2.1": "Interesse - Pós-venda Passeio",
            "3.2.2": "Interesse - Pós-venda Utilitário",
            "4.1": "Interesse - Governamentais",
            "4.2": "Interesse - Assinatura",
        }
        tag = interesse_map.get(id_normalizado, "Interesse")
        atualizar_interesse(numero, tag)
        registrar_interacao(numero, nome_final, tag)
        enviar_mensagem(numero, BLOCOS[id_normalizado])
        return

    # ===== Trabalhe Conosco =====
    if id_normalizado == "btn-trabalhe":
        atualizar_interesse(numero, "Interesse - Trabalhe Conosco")
        registrar_interacao(numero, nome_final, "Interesse - Trabalhe Conosco")
        enviar_mensagem(
            numero,
            "Envie seu *nome*, *telefone* e uma *breve descrição* da sua experiência.\n\n"
            "Para *veículos de passeio*:\n"
            "Alex – 📞 011996371559 – https://wa.me/5511996371559 – ✉️ alex@sullato.com.br\n\n"
            "Para *veículos utilitários*:\n"
            "Anderson – 📞 011988780161 – https://wa.me/5511988780161 – ✉️ anderson@sullato.com.br"
        )
        # opcional: aviso por e-mail (não falha se SMTP não estiver configurado)
        enviar_email(
            "Novo interesse - Trabalhe Conosco (Sullato)",
            (
                f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Nome (detectado): {nome_final}\n"
                f"WhatsApp: {numero}\n"
                f"Status: Iniciou fluxo Trabalhe Conosco pelo botão.\n"
            ),
        )
        return

    # Se o usuário enviar dados de candidatura como texto
    if not isinstance(mensagem, dict) and _parece_detalhe_trabalho(id_recebido):
        enviar_email(
            "Detalhes de candidatura - Trabalhe Conosco (Sullato)",
            (
                f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
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
            "credito": ("💰 Aqui na Sullato temos opções de crédito facilitado! Me chama que explico como funciona.", "Interesse - Crédito"),
            "endereco": ("📍 Estamos em dois endereços: Av. São Miguel, 7900 e 4049/4084 – São Paulo.", "Interesse - Endereço Loja"),
            "comprar": ("🚗 Temos vans, utilitários e veículos de passeio esperando por você!", "Interesse - Comprar"),
            "vender": ("📢 Estamos prontos pra ajudar você a vender seu veículo com segurança e agilidade.", "Interesse - Vender"),
            "oficina": ("🔧 Nossa oficina especializada está pronta pra te atender! Quer agendar uma visita?", "Interesse - Oficina"),
            "garantia": ("🛡️ Conte com nosso suporte! Fale conosco e vamos verificar sua garantia.", "Interesse - Garantia"),
        }
        msg, tag = mapa.get(intencao, (None, None))
        if msg:
            enviar_mensagem(numero, msg)
            atualizar_interesse(numero, tag or "Interesse")
            registrar_interacao(numero, nome_final, tag or "Interesse")
            return

    # ===== Resposta livre por IA (fallback) =====
    resposta = None
    try:
        resposta = responder_com_ia(id_normalizado, nome_final)
    except TypeError:
        try:
            resposta = responder_com_ia(id_normalizado)
        except Exception:
            resposta = None
    except Exception as e:
        print("⚠️ Erro responder_com_ia:", e)
        resposta = None

    if resposta:
        enviar_mensagem(numero, resposta)
        registrar_interacao(numero, nome_final, "IA - Resposta livre")
        return

    # ===== Fallback final → Menu =====
    registrar_interacao(numero, nome_final, "Fallback → Menu")
    atualizar_interesse(numero, "Fallback → Menu")
    enviar_botoes(
        numero,
        f"Não entendi. Escolha uma das opções abaixo, {nome_final}:",
        BOTOES_MENU_INICIAL
    )
    return
