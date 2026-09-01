import os
import random
import requests
import unicodedata
import re
import smtplib
import ssl
import time
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

def _enviar_mensagem_com_status(numero: str, texto: str) -> bool:
    """
    Variante de enviar_mensagem() que informa se o envio teve sucesso.
    Usada só na notificação de lead ao vendedor (Fase 3.1D) — ali
    precisamos saber se a transferência realmente aconteceu antes de
    confirmar isso ao cliente. enviar_mensagem() não é alterada.
    """
    try:
        url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
        payload = {"messaging_product": "whatsapp", "to": numero, "text": {"preview_url": True, "body": texto}}
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        print("🟢 Meta message (lead vendedor):", r.status_code, r.text)
        return 200 <= r.status_code < 300
    except Exception as e:
        print("❌ Erro ao enviar mensagem ao vendedor:", e)
        return False

def _telefone_para_template(numero: str) -> str:
    """
    Formata o telefone do cliente para a variável {{2}} do template
    novo_lead_vendedor, no padrão do exemplo aprovado na Meta (sem "+" e
    sem o código do país "55"). Não altera o número usado internamente
    pelo restante do sistema — só o valor enviado nessa variável.
    """
    n = (numero or "").strip()
    if n.startswith("55") and len(n) > 11:
        return n[2:]
    return n

def _sanitizar_parametro_template(texto: str) -> str:
    """
    Sanitiza um valor antes de enviá-lo como variável de corpo de um
    template da Meta: quebras de linha/tabs não são aceitas em parâmetros
    de template, então são colapsadas em espaço único; o tamanho também é
    limitado a um valor seguro.
    """
    if not texto:
        return ""
    t = re.sub(r"\s+", " ", str(texto)).strip()
    return t[:1024]

def _enviar_template_novo_lead_vendedor(
    numero_vendedor: str,
    nome_cliente: str,
    telefone_cliente: str,
    veiculo: str,
    resumo: str,
    visita_texto: str,
) -> bool:
    """
    Envia o template aprovado na Meta "novo_lead_vendedor" (Utilidade,
    pt_BR, 5 variáveis de corpo, sem cabeçalho) para o vendedor, abrindo
    ou reabrindo a janela de conversa antes do texto livre com o resumo
    completo. Falha aqui NUNCA deve quebrar a transferência — ver
    _processar_transferencia_vendedor(), que só loga e segue com o
    mecanismo de texto livre já existente.
    """
    try:
        url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
        payload = {
            "messaging_product": "whatsapp",
            "to": numero_vendedor,
            "type": "template",
            "template": {
                "name": "novo_lead_vendedor",
                "language": {"code": "pt_BR"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": _sanitizar_parametro_template(nome_cliente)},
                            {"type": "text", "text": _sanitizar_parametro_template(telefone_cliente)},
                            {"type": "text", "text": _sanitizar_parametro_template(veiculo)},
                            {"type": "text", "text": _sanitizar_parametro_template(resumo)},
                            {"type": "text", "text": _sanitizar_parametro_template(visita_texto)},
                        ],
                    }
                ],
            },
        }
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        print("🟢 Meta template novo_lead_vendedor:", r.status_code, r.text)
        return 200 <= r.status_code < 300
    except Exception as e:
        print("❌ Erro ao enviar template novo_lead_vendedor:", e)
        return False

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
_HIST_IA: dict = {}
_HIST_TTL = 3600

def _get_hist_ia(numero):
    h = _HIST_IA.get(numero, {})
    if time.time() - h.get("ts", 0) > _HIST_TTL:
        return []
    return list(h.get("msgs", []))

def _add_hist_ia(numero, user_msg, assistant_msg):
    h = _HIST_IA.get(numero, {})
    msgs = list(h.get("msgs", []))
    msgs.append({"role": "user", "content": user_msg})
    msgs.append({"role": "assistant", "content": assistant_msg})
    _HIST_IA[numero] = {"msgs": msgs[-10:], "ts": time.time()}

_HANDOFF_NUMERO = "5511988780161"
_GATILHOS_HANDOFF = ["atendente", "falar com humano", "falar com pessoa", "quero falar com alguem", "quero falar com alguem"]

def _enviar_alerta_handoff(numero_cliente, nome_cliente):
    try:
        url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
        msg = (
            f"🔔 *Solicitação de Atendimento Humano*\n\n"
            f"Cliente: {nome_cliente}\n"
            f"WhatsApp: +{numero_cliente}\n"
            f"Via: ChatBot Sullato\n\n"
            "Por favor, entre em contato!"
        )
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
        payload = {"messaging_product": "whatsapp", "to": _HANDOFF_NUMERO, "text": {"body": msg}}
        requests.post(url, headers=headers, json=payload, timeout=10)
        print("🔔 Alerta handoff Sullato enviado")
    except Exception as e:
        print("❌ Erro alerta handoff:", e)

VENDEDORES_PASSEIO_BASE = [
    ("👨🏻‍💼 Alexandre", "https://wa.me/5511988628961"),
    ("👨🏻‍💼 Jeferson",  "https://wa.me/5511941006862"),
    ("👨🏻‍💼 Pedro",     "https://wa.me/5511996564815"),
    ("👨🏻‍💼 Thiago",    "https://wa.me/5511986122905"),
    ("👨🏻‍💼 Vinicius",  "https://wa.me/5511911260469"),
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

# Formatação em linguagem natural do dia/período coletados, usada só na
# confirmação ao CLIENTE (o valor bruto gravado no estado e enviado ao
# vendedor no resumo não muda).
_DIAS_SEMANA_NATURAL = {
    "segunda": "segunda-feira", "terca": "terça-feira", "quarta": "quarta-feira",
    "quinta": "quinta-feira", "sexta": "sexta-feira", "sabado": "sábado",
    "domingo": "domingo", "hoje": "hoje", "amanha": "amanhã",
}
_PERIODOS_NATURAL = {"manha": "de manhã", "tarde": "à tarde", "noite": "à noite"}

def _formatar_dia_natural(dia: str) -> str:
    return _DIAS_SEMANA_NATURAL.get(dia, dia)

def _formatar_periodo_natural(periodo: str) -> str:
    return _PERIODOS_NATURAL.get(periodo, f"às {periodo}")

# ===== Fase 3.1D: fechamento do lead comercial (backend seleciona o vendedor) =====
def _processar_transferencia_vendedor(numero: str, nome_cliente: str, estado_comercial: Dict[str, Any]) -> None:
    """
    Quando o cliente sinaliza intenção clara de avançar (assistente_comercial
    já marcou qualificado=True), seleciona UM vendedor pelo rodízio já
    existente, envia o resumo do lead a ele e só então informa esse MESMO
    vendedor ao cliente. Idempotente por telefone: se já existe vendedor no
    estado, não faz nada; se o envio ao vendedor falhar, não confirma nada
    ao cliente e a próxima mensagem tenta de novo (vendedor continua None).
    """
    if not estado_comercial or not estado_comercial.get("qualificado"):
        return
    if estado_comercial.get("vendedor"):
        return  # já transferido nesta sessão — não seleciona nem envia de novo

    try:
        import assistente_comercial
    except Exception:
        return

    try:
        categoria = estado_comercial.get("categoria") or "passeio"
        lista = vendedores_util() if categoria == "utilitario" else vendedores_passeio()
        if not lista:
            return
        vendedor_nome, vendedor_link = lista[0]

        try:
            from responder_ia import gerar_resumo_lead
        except Exception:
            gerar_resumo_lead = None

        resumo = None
        if gerar_resumo_lead:
            try:
                resumo = gerar_resumo_lead(_get_hist_ia(numero), estado_comercial)
            except Exception as e:
                print("⚠️ Falha ao gerar resumo do lead:", e)
        if not resumo:
            resumo = "Sem resumo detalhado disponível — cliente demonstrou interesse e intenção de avançar."

        texto_lead = (
            "🔔 NOVO LEAD QUALIFICADO — CHATBOT SULLATO\n\n"
            f"Cliente: {nome_cliente}\n"
            f"Telefone: +{numero}\n\n"
            f"Veículo de interesse:\n{estado_comercial.get('veiculo') or 'não especificado'}\n"
        )
        if estado_comercial.get("url"):
            texto_lead += f"\nURL do anúncio:\n{estado_comercial['url']}\n"
        texto_lead += f"\nOrigem: {estado_comercial.get('origem') or 'não identificada'}\n"
        if estado_comercial.get("data_visita") or estado_comercial.get("horario_visita"):
            texto_lead += (
                f"\nVisita:\n"
                f"Dia: {estado_comercial.get('data_visita') or 'não informado'}\n"
                f"Período: {estado_comercial.get('horario_visita') or 'não informado'}\n"
            )
        texto_lead += (
            f"\nRESUMO DA IA:\n{resumo}\n\n"
            f"Intenção/urgência do cliente:\n{estado_comercial.get('intencao_visita') or 'não especificada'}\n\n"
            "Status: LEAD QUALIFICADO / CONTATO COMERCIAL"
        )

        numero_vendedor = vendedor_link.replace("https://wa.me/", "").strip()

        # Template aprovado na Meta (Utilidade, pt_BR) — abre/reabre a janela
        # de conversa com o vendedor antes do texto livre com o resumo
        # completo. Falha aqui é só logada; NUNCA bloqueia a transferência.
        dia_tpl = estado_comercial.get("data_visita")
        periodo_tpl = estado_comercial.get("horario_visita")
        if dia_tpl and periodo_tpl:
            visita_texto = f"{_formatar_dia_natural(dia_tpl)} {_formatar_periodo_natural(periodo_tpl)}"
        elif dia_tpl:
            visita_texto = _formatar_dia_natural(dia_tpl)
        elif periodo_tpl:
            visita_texto = _formatar_periodo_natural(periodo_tpl)
        else:
            visita_texto = "Não informada"

        try:
            template_ok = _enviar_template_novo_lead_vendedor(
                numero_vendedor,
                nome_cliente,
                _telefone_para_template(numero),
                estado_comercial.get("veiculo") or "não especificado",
                resumo,
                visita_texto,
            )
            if not template_ok:
                print(f"⚠️ Falha ao enviar template novo_lead_vendedor para {vendedor_nome} — seguindo com o texto livre (mecanismo já existente).")
        except Exception as e:
            print("⚠️ Erro inesperado ao enviar template novo_lead_vendedor (ignorado, seguindo com texto livre):", e)

        enviado_ok = _enviar_mensagem_com_status(numero_vendedor, texto_lead)
        if not enviado_ok:
            print(f"⚠️ Falha ao notificar vendedor {vendedor_nome} — transferência NÃO concluída, tentará de novo na próxima mensagem.")
            return

        assistente_comercial.definir_vendedor(numero, vendedor_nome, vendedor_link)
        assistente_comercial.marcar_transferencia_concluida(numero)

        dia = estado_comercial.get("data_visita")
        periodo = estado_comercial.get("horario_visita")
        linha_visita = ""
        if dia and periodo:
            linha_visita = f"Vou deixar sua visita organizada para {_formatar_dia_natural(dia)} {_formatar_periodo_natural(periodo)}.\n\n"
        elif dia:
            linha_visita = f"Vou deixar sua visita organizada para {_formatar_dia_natural(dia)}.\n\n"
        elif periodo:
            linha_visita = f"Vou deixar sua visita organizada {_formatar_periodo_natural(periodo)}.\n\n"

        enviar_mensagem(
            numero,
            f"Perfeito! 👍\n\n"
            f"{linha_visita}"
            f"Vou deixar seu atendimento com {vendedor_nome}, da nossa equipe.\n\n"
            f"📱 {vendedor_nome}: {vendedor_link}\n\n"
            "Já vou passar para ele(a) as informações da nossa conversa, para você não precisar explicar tudo de novo."
        )
    except Exception as e:
        print("⚠️ Falha ao processar transferência de vendedor (ignorada):", e)

# ===== Blocos fixos =====
BLOCOS = {
    "1.3": """*Endereço e Site*

🌐 Site: www.sullato.com.br – https://www.sullato.com.br
📸 Instagram: @sullatomicrosevans – https://www.instagram.com/sullatomicrosevans
📸 Instagram: @sullato.veiculos – https://www.instagram.com/sullato.veiculos
📸 Instagram: @tssullatoautoservice – https://www.instagram.com/tssullatoautoservice/

🏢 Loja 01: Av. São Miguel, 7900 – cep. 08070-001 - SP
📞 (11) 2030-5081 | (11) 2031-5081

🏢 Loja 02: Av. São Miguel, 4049 – cep. 03871-000 - SP
📞 (11) 2542-3332 | (11) 2542-3333

🏢 Loja 03: Av. São Miguel, 4084 – cep. 03871-000 - SP
📞 (11) 2045-2753""",

    "2.1": """*Oficina e Peças*

📲 Atendimento centralizado pelo WhatsApp oficial da Oficina Sullato:

👉 https://wa.me/5511917027705

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

👉 https://wa.me/5511917027705""",

    "3.2.2": """*Oficina e Peças – Utilitário*

📲 Atendimento pelo WhatsApp oficial da Oficina Sullato:

👉 https://wa.me/5511917027705""",

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
    try:
        import assistente_comercial
    except Exception:
        assistente_comercial = None

    # Extrai ID/Texto e normaliza
    id_recebido = _extrair_id_ou_texto(mensagem)
    id_normalizado = normalizar_id(id_recebido)

    # Nome
    nome_digitado = detectar_nome_digitado(id_recebido) if isinstance(id_recebido, str) else None
    nome_final = normalizar_nome(nome_digitado or nome_contato or "Cliente")
    primeiro_nome = extrair_primeiro_nome_exibicao(nome_final)

    # Registros básicos
    try:
        # ==============================
        # 🔥 ENVIA PARA GOOGLE SHEETS (Página1 - DINÂMICO)
        # ==============================
        origem_evento = id_normalizado if id_normalizado else "entrada"

        # evita poluir a planilha com textos muito grandes
        if len(origem_evento) > 50:
            origem_evento = "texto_livre"

        enviar_para_google_sheets(numero, nome_final, origem_evento)

        # ==============================
        # 📇 SALVA NA MALA DIRETA (gatilhos iniciais)
        # ==============================
        if id_normalizado in ["oi", "olá", "ola", "menu", "inicio", "início"]:
            salvar_em_mala_direta(numero, nome_final)

        # ==============================
        # 🧠 COMANDOS CONHECIDOS
        # ==============================
        comandos_conhecidos = {
            "1","2","3","4.1","4.2","1.1","1.2","1.3","2.1","2.2","3.2.1","3.2.2",
            "passeio","utilitario","utilitário","comprar","mais1","mais2","mais3",
            "btn-oficina","btn-pos-venda","btn-trabalhe","btn-endereco",
            "venda direta","venda-direta","governamental","governamentais",
            "garantia","menu","endereco oficina","endereço oficina"
        }

        # ==============================
        # 📊 REGISTRO DE INTERAÇÃO
        # ==============================
        if id_recebido and id_normalizado in comandos_conhecidos:
            registrar_interacao(numero, nome_final, id_normalizado)

    except Exception as e:
        print("⚠️ Falha em algum registro inicial:", e)

    # HANDOFF — detectar antes de qualquer outra lógica
    if _is_text_payload(mensagem) and any(g in id_normalizado for g in _GATILHOS_HANDOFF):
        _enviar_alerta_handoff(numero, nome_final)
        enviar_mensagem(
            numero,
            f"Entendido, {primeiro_nome}! 👍 Já avisamos nossa equipe.\n\n"
            "Em breve um consultor vai entrar em contato com você.\n\n"
            "Se preferir, pode chamar agora:\n"
            "👉 https://wa.me/5511988780161"
        )
        return

    # Menu gatilho
    if _tem_trigger_menu(id_normalizado) or id_normalizado == "menu":
        enviar_botoes(
            numero,
            (
                f"Olá, {primeiro_nome}! 😃 Seja bem-vindo ao atendimento virtual do Grupo Sullato.\n\n"
                "Como posso te ajudar?\n\n"
                "💬 Você também pode escrever sua dúvida ou enviar um áudio explicando o que precisa."
            ),
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
            registrar_interacao(numero, nome_final, "Texto livre → IA conversacional")
            atualizar_interesse(numero, "Texto livre → IA")
        except Exception:
            pass

        # ===== Fase 3.1C: camada comercial (aditiva, controlada por feature flag) =====
        estado_comercial = None
        if assistente_comercial is not None:
            try:
                if assistente_comercial.assistente_comercial_ativo():
                    _hist_atual = _get_hist_ia(numero)
                    _ultima_ia = next(
                        (m.get("content") for m in reversed(_hist_atual) if m.get("role") == "assistant"),
                        None,
                    )
                    estado_comercial = assistente_comercial.processar_mensagem(
                        numero, id_recebido, ultima_mensagem_ia=_ultima_ia
                    )
            except Exception as e:
                print("⚠️ Falha no assistente comercial (ignorada):", e)
                estado_comercial = None

        contexto_comercial_ativo = bool(estado_comercial and estado_comercial.get("ativo"))

        # ===== Fase 3.1D: sinal de transferência já detectado nesta mensagem
        # (assistente_comercial.processar_mensagem já rodou acima) — o
        # backend assume o controle ANTES de deixar a IA responder
        # livremente, para ela não "enrolar" quando o cliente já pediu
        # vendedor/contato explicitamente.
        if (
            contexto_comercial_ativo
            and estado_comercial.get("qualificado")
            and not estado_comercial.get("vendedor")
        ):
            _processar_transferencia_vendedor(numero, nome_final, estado_comercial)
            return

        resposta_ia = None
        try:
            hist = _get_hist_ia(numero)
            resposta_ia = responder_com_ia(
                id_recebido,
                primeiro_nome,
                historico=hist,
                contexto_comercial=estado_comercial if contexto_comercial_ativo else None,
            )
        except Exception:
            pass

        if resposta_ia:
            _add_hist_ia(numero, id_recebido, resposta_ia)
            enviar_mensagem(numero, resposta_ia)
            if not contexto_comercial_ativo:
                enviar_botoes(numero, "Posso ajudar com algo mais?", BOTOES_MENU_INICIAL)
        else:
            enviar_mensagem(
                numero,
                f"Não entendi sua mensagem, {primeiro_nome}. Posso te ajudar por aqui 👇"
            )
            enviar_botoes(numero, "Escolha uma opção:", BOTOES_MENU_INICIAL)
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
