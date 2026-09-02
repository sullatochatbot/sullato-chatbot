# assistente_comercial.py
"""
Fundação da camada comercial (Fase 3.1B) — ChatbotSullato.

Módulo isolado: não importa nem é importado por responder.py, webhook.py,
responder_ia.py ou pela lógica de vendedores/rodízio. Sem I/O de rede, sem
WhatsApp, sem Google Sheets, sem chamada de IA externa.

Mantém, em memória, um estado comercial por telefone (mesmo padrão já usado
no projeto para o histórico de IA em responder.py), com expiração alinhada
à mesma janela de sessão (1h).
"""

import os
import re
import time
import unicodedata
from typing import Optional, Dict, Any

# ============================================================
# Configuração / constantes
# ============================================================

_ESTADO_TTL = 3600  # 1h — mesmo TTL do histórico de IA (_HIST_IA) em responder.py
_ESTADOS: Dict[str, Dict[str, Any]] = {}

_URL_RE = re.compile(r"https?://\S+")
_ANO_RE = re.compile(r"\b(19|20)\d{2}\b")

# Linhas que começam assim são tratadas como introdução/saudação, não como
# descrição de veículo (usado só quando nenhuma linha tem ano detectável).
_INTROS_IGNORAVEIS = (
    "quero", "gostaria", "ola", "bom dia", "boa tarde", "boa noite", "oi",
)

# Gatilhos de entrada comercial genérica (redes sociais / anúncio), sem veículo
# ainda identificado — cenário B.
_GATILHOS_INTERESSE_GENERICO = [
    "saiba mais",
    "tenho interesse",
    "quero saber mais",
    "gostaria de saber mais",
    "gostaria de mais informacoes",
    "mais informacoes sobre esse veiculo",
    "mais informacoes sobre este veiculo",
]

# Palavras de negação que, aparecendo logo antes de um gatilho de interesse,
# invalidam a ativação (proteção conservadora contra falso positivo óbvio —
# não é uma análise semântica, só olha as poucas palavras imediatamente
# anteriores ao gatilho encontrado).
_NEGACOES = ("nao", "num", "nunca", "jamais")
_JANELA_NEGACAO = 3  # nº de palavras antes do gatilho a inspecionar

# Respostas negativas/indefinidas: quando o estágio é "aguardando_veiculo",
# NÃO devem fazer o estado avançar para "veiculo_identificado".
_PADROES_INDEFINIDOS = [
    r"nao sei",
    r"nao decidi",
    r"nao tenho certeza",
    r"sem certeza",
    r"\btalvez\b",
    r"pesquisando",
    r"\bpesquisar\b",
    r"ver opcoes",
    r"voces (tem|possuem)",
    r"me ajuda(m)? a escolher",
    r"me ajude a escolher",
    r"qualquer (um|uma|carro|veiculo)",
    r"nao faz diferenca",
    r"tanto faz",
]

# Respostas curtas que não carregam nenhuma informação de veículo.
_RESPOSTAS_CURTAS_SEM_INFO = {
    "oi", "ola", "ok", "sim", "nao", "blz", "certo", "entendi",
    "obrigado", "obrigada", "valeu", "?",
}


# ============================================================
# Utilitários internos
# ============================================================

def _normalizar(texto: str) -> str:
    if not texto:
        return ""
    t = texto.strip().lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"\s+", " ", t)
    return t


def _tem_negacao_antes(texto_norm: str, gatilho: str) -> bool:
    """True se uma palavra de negação aparece nas _JANELA_NEGACAO palavras
    imediatamente antes do gatilho encontrado em texto_norm."""
    idx = texto_norm.find(gatilho)
    if idx == -1:
        return False
    palavras_antes = texto_norm[:idx].split()[-_JANELA_NEGACAO:]
    return any(p in _NEGACOES for p in palavras_antes)


def _eh_interesse_generico(texto_norm: str) -> bool:
    for gatilho in _GATILHOS_INTERESSE_GENERICO:
        if gatilho in texto_norm and not _tem_negacao_antes(texto_norm, gatilho):
            return True
    return False


# Frases do CTA "Simular" do site atreladas a um veículo específico. Cobre o
# caso real em que a mensagem descreve o veículo (com ano) mas a URL não é
# reconhecida por detectar_url (ex.: link não veio embutido no texto).
_GATILHOS_SIMULACAO_VEICULO = (
    "simulacao desse carro",
    "simulacao deste carro",
    "simulacao desse veiculo",
    "simulacao deste veiculo",
    "quero fazer a simulacao desse carro",
    "quero fazer a simulacao deste carro",
    "fazer a simulacao desse carro",
    "fazer a simulacao deste carro",
)


def _eh_entrada_forte_veiculo(texto_norm: str) -> bool:
    """
    Sinal forte de entrada vinda de anúncio/site com veículo específico, mesmo
    sem URL detectada no texto. Conservador: frase de simulação atrelada a
    "esse/este carro/veículo", OU ano de veículo (####) junto com marcador de
    preço ("r$") na mesma mensagem — combinação característica de descrição
    de anúncio colada no WhatsApp, dificilmente digitada por acaso.
    """
    if any(g in texto_norm for g in _GATILHOS_SIMULACAO_VEICULO):
        return True
    return bool(_ANO_RE.search(texto_norm) and "r$" in texto_norm)


# Sinais inequívocos de intenção de avançar para atendimento humano.
# Urgência isolada ("tenho pressa", "preciso trabalhar") NÃO entra aqui —
# só ajuda na qualificação, nunca dispara sozinha a transferência (decisão
# explícita de Anderson).
_GATILHOS_VISITA = (
    "quero visitar", "posso visitar", "posso ir ai", "posso ir na loja",
    "quero ir ai", "quero ir na loja", "vou ai", "vou passar ai",
    "posso passar ai", "quero conhecer o carro pessoalmente",
    "quero ver o carro pessoalmente", "aceito visitar",
)
_GATILHOS_FALAR_VENDEDOR = (
    "falar com vendedor", "falar com consultor", "falar com um vendedor",
    "falar com o vendedor", "quero falar com vendedor", "quero falar com consultor",
    "quero falar com alguem", "passar pro vendedor", "passar para o vendedor",
    "me passa pro vendedor", "me passa um vendedor",
)
_GATILHOS_QUEM_ATENDE = (
    "quem vai me atender", "quem me atende", "quem e o vendedor",
    "quem vai cuidar do meu", "quem vai cuidar de mim", "quem que vai me atender",
    "com quem eu falo", "quem vai falar comigo", "quem eu procuro", "quem procuro",
    "qual vendedor", "quem e meu consultor", "quem pode me atender",
)
_GATILHOS_CONTATO_RESPONSAVEL = (
    "telefone do vendedor", "telefone do responsavel", "contato do vendedor",
    "numero do vendedor", "contato do responsavel", "nome do vendedor",
    "pode me passar o contato", "me passa o contato",
    "pode me passar o telefone do vendedor", "vendedor especifico",
    "vendedor em especifico", "consultor especifico", "tem algum vendedor",
)
_GATILHOS_ACEITA_CONTINUIDADE = (
    "pode passar meu contato", "pode passar meu numero", "pode passar para ele",
    "pode passar para ela", "tudo bem alguem da equipe continuar",
    "aceito que a equipe entre em contato", "pode me colocar em contato com o vendedor",
)

# Pedido explícito de desconto/negociação — mesma camada de contato humano
# direto (rota E): quem pede desconto/melhor preço quer negociar com uma
# pessoa, não continuar sendo entrevistado pela IA. A IA nunca inventa ou
# promete desconto; isso é responsabilidade do vendedor.
_GATILHOS_DESCONTO_NEGOCIACAO = (
    "quero desconto", "tem desconto", "consegue desconto", "algum desconto",
    "qual o melhor preco", "faz um preco melhor", "melhor condicao a vista",
    "tem negociacao", "consegue melhorar o valor", "consegue melhorar o preco",
    "consegue fazer um preco melhor", "condicao diferenciada", "condicao especial",
    "uma condicao melhor",
)

# Reconhecimento por co-ocorrência (mais tolerante a variações de frase do
# que as listas acima): "vendedor"/"consultor" + palavra de pergunta na
# mesma mensagem — cobre formas não previstas exatamente (ex.: "tem um
# vendedor em específico pra me mandar?"), continuando conservador por
# exigir as duas partes juntas.
_PALAVRA_VENDEDOR_CONSULTOR = ("vendedor", "consultor")
_PALAVRAS_PERGUNTA_IDENTIFICACAO = ("quem", "qual", "nome", "especifico", "tem algum", "tem um")


def _eh_pedido_identificacao_vendedor(texto_norm: str) -> bool:
    tem_vendedor = any(p in texto_norm for p in _PALAVRA_VENDEDOR_CONSULTOR)
    tem_pergunta = any(p in texto_norm for p in _PALAVRAS_PERGUNTA_IDENTIFICACAO)
    return tem_vendedor and tem_pergunta


# Co-ocorrência tolerante a erro de digitação na preposição (ex.: "falar
# ocm um vendedor"): exige "vendedor"/"consultor" + um verbo de contato
# ("falar"/"conversar"), sem depender de acertar "com" literalmente.
_PALAVRAS_VERBO_CONTATO = ("falar", "conversar")


def _eh_pedido_falar_com_vendedor_tolerante(texto_norm: str) -> bool:
    tem_vendedor = any(p in texto_norm for p in _PALAVRA_VENDEDOR_CONSULTOR)
    tem_verbo = any(p in texto_norm for p in _PALAVRAS_VERBO_CONTATO)
    return tem_vendedor and tem_verbo
_PALAVRAS_DIA_DISPONIBILIDADE = (
    "hoje", "amanha", "segunda", "terca", "quarta", "quinta", "sexta",
    "sabado", "domingo", "essa semana", "neste fim de semana",
)
_PALAVRAS_IR_LOJA = ("ir", "passar", "visitar", "loja", "aparecer", "chegar")


def _eh_disponibilidade_para_visita(texto_norm: str) -> bool:
    """Dia/horário + verbo de comparecer na mesma mensagem (ex.: 'posso ir amanha')."""
    tem_dia = any(p in texto_norm for p in _PALAVRAS_DIA_DISPONIBILIDADE)
    tem_ida = any(p in texto_norm for p in _PALAVRAS_IR_LOJA)
    return tem_dia and tem_ida


# Padrões (regex) para reconhecer variações naturais de intenção comercial
# forte (contato humano, visita, proposta/fechamento) além das frases
# literais das listas acima — tolera pequenas variações (artigo, verbo
# sinônimo) sem virar análise semântica. Cada padrão continua exigindo a
# combinação de palavras-chave específica do domínio (vendedor/consultor,
# visita, proposta/oferta, comprar/fechar) — não dispara com interesse ou
# dúvida comercial comuns (ex.: "quero saber mais", "qual o valor?").
_PADROES_TRANSFERENCIA = (
    r"falar com (um |uma |o |a )?(vendedor|consultor|alguem)\b",
    r"conversar com (um |uma |o |a )?(vendedor|consultor|alguem)\b",
    r"com quem (eu )?(posso |devo |vou )?(falar|conversar)",
    r"me (passa|passar|passe|manda|indica) (o |um )?(vendedor|consultor|contato|telefone|numero)",
    r"tem algum vendedor",
    r"quero (ir )?(ver|conhecer) (o |esse |este )?carro\b",
    r"\b(agendar|marcar) (uma )?visita\b",
    r"\bquero agendar\b",
    r"fazer (uma )?(proposta|oferta)\b",
    r"\bquero fechar\b",
    r"\bquero comprar\b",
)


def _eh_sinal_transferencia_regex(texto_norm: str) -> bool:
    return any(re.search(p, texto_norm) for p in _PADROES_TRANSFERENCIA)


# Sinais especificamente de VISITA (rota D) — precisam de dia+período antes
# de transferir. Distinto de contato humano direto (rota E: "quero falar com
# vendedor", "me passa o contato" etc.), que continua transferindo na hora,
# sem passar por essa coleta — aprovado por Anderson.
_PADROES_VISITA = (
    r"quero (ir )?(ver|conhecer) (o |esse |este )?carro\b",
    r"\b(agendar|marcar) (uma )?visita\b",
    r"\bquero agendar\b",
    r"quando (eu )?(posso|devo) (ir|passar)\b",
    r"que dia (eu )?(posso|devo) (ir|passar)\b",
    r"quando (eu )?for\b",
)


def _eh_sinal_visita(texto_norm: str) -> bool:
    if any(g in texto_norm for g in _GATILHOS_VISITA):
        return True
    if any(re.search(p, texto_norm) for p in _PADROES_VISITA):
        return True
    return _eh_disponibilidade_para_visita(texto_norm)


# Resposta afirmativa curta ("sim", "quero") só conta como aceite de visita
# quando a ÚLTIMA mensagem da própria IA claramente convidou o cliente a
# conhecer o veículo na loja — evita presumir isso de um "sim" isolado
# respondendo a qualquer outra pergunta.
_RESPOSTAS_AFIRMATIVAS_CURTAS = {
    "sim", "quero", "quero sim", "claro", "pode ser", "vamos",
    "bora", "com certeza", "isso", "isso mesmo",
}
_SINAIS_CONVITE_VISITA_IA = (
    ("conhecer", "pessoalmente"),
    ("conhecer", "loja"),
    ("visitar", "loja"),
    ("vir", "loja"),
)


def _eh_resposta_afirmativa_curta(texto_norm: str) -> bool:
    return texto_norm.strip() in _RESPOSTAS_AFIRMATIVAS_CURTAS


def _ia_convidou_para_visita(ultima_mensagem_ia: Optional[str]) -> bool:
    if not ultima_mensagem_ia:
        return False
    t = _normalizar(ultima_mensagem_ia)
    return any(p1 in t and p2 in t for p1, p2 in _SINAIS_CONVITE_VISITA_IA)


# Extração leve de dia/período informados pelo cliente (texto literal, sem
# resolver para uma data de calendário real — fora de escopo por decisão de
# Anderson, ver REGRA "AGENDAMENTO"). Mesmo estilo conservador das outras
# heurísticas deste módulo.
_DIAS_SEMANA = (
    "hoje", "amanha", "segunda", "terca", "quarta", "quinta", "sexta",
    "sabado", "domingo",
)
_EXPRESSOES_DIA_EXTRA = ("essa semana", "neste fim de semana", "fim de semana")
_DATA_RE = re.compile(r"\b(\d{1,2})[/\-](\d{1,2})\b")

_PERIODOS = ("manha", "tarde", "noite")
_PERIODOS_RE = tuple(re.compile(rf"\b{p}\b") for p in _PERIODOS)
_HORARIO_RE = re.compile(r"\b([01]?\d|2[0-3])[:h](\d{2})?\b")


def _extrair_dia(texto_norm: str) -> Optional[str]:
    """Extrai dia da semana, 'hoje'/'amanha' ou data numérica (ex.: 15/09)."""
    m = _DATA_RE.search(texto_norm)
    if m:
        return m.group(0)
    for palavra in _DIAS_SEMANA + _EXPRESSOES_DIA_EXTRA:
        if palavra in texto_norm:
            return palavra
    return None


def _extrair_periodo(texto_norm: str) -> Optional[str]:
    """
    Extrai período (manhã/tarde/noite) ou horário específico (ex.: 10h, 14:30).
    Usa fronteira de palavra (\\b) para não confundir "manha" com a
    substring dentro de "amanha".
    """
    m = _HORARIO_RE.search(texto_norm)
    if m:
        return m.group(0)
    for p, regex in zip(_PERIODOS, _PERIODOS_RE):
        if regex.search(texto_norm):
            return p
    return None


def _proximo_estagio_visita(estado: Dict[str, Any]) -> str:
    tem_dia = bool(estado.get("data_visita"))
    tem_periodo = bool(estado.get("horario_visita"))
    if tem_dia and tem_periodo:
        return "completo"
    if tem_dia:
        return "aguardando_periodo"
    return "aguardando_dia"


# Horário de funcionamento por operação (abre, fecha), em hora cheia.
# "oficina" está aqui por completude/documentação, mas HOJE não é
# alcançável: _classificar_categoria() só produz "utilitario"/"passeio" —
# o atendimento de oficina/peças roda por um fluxo de menu totalmente
# separado (BLOCOS "2.1"/"2.2"/"3.2.1"/"3.2.2" em responder.py), que não
# passa pela coleta de visita (estagio_visita) do assistente comercial.
# Ver observação no relatório antes de qualquer tentativa de ligar isso.
_HORARIOS_OPERACAO = {
    "utilitario": {"semana": (9, 18), "sabado": (9, 14)},
    "passeio":    {"semana": (9, 18), "sabado": (9, 17)},
    "oficina":    {"semana": (9, 18), "sabado": (9, 13)},
}
_DIAS_UTEIS = ("segunda", "terca", "quarta", "quinta", "sexta")


def _tipo_dia_semana(dia: Optional[str]) -> Optional[str]:
    """
    Classifica um dia já extraído (_extrair_dia) como 'semana' ou 'sabado'
    para validar horário de funcionamento. "domingo" e referências
    relativas ("hoje", "amanha", "essa semana", data numérica) retornam
    None — não resolvido para uma data de calendário real (fora de
    escopo), então não é possível validar com segurança nesses casos.
    """
    if dia in _DIAS_UTEIS:
        return "semana"
    if dia == "sabado":
        return "sabado"
    return None


def _horario_especifico_para_hora(periodo: Optional[str]) -> Optional[float]:
    """Converte um horário específico já extraído (ex.: '10h', '14:30') em hora decimal."""
    if not periodo:
        return None
    m = _HORARIO_RE.search(periodo)
    if not m:
        return None
    hora = int(m.group(1))
    minuto = int(m.group(2)) if m.group(2) else 0
    return hora + minuto / 60


def _validar_horario_visita(
    categoria: Optional[str], dia: Optional[str], periodo: Optional[str]
) -> Dict[str, Any]:
    """
    Valida dia+período contra o horário de funcionamento conhecido da
    operação (categoria). NÃO resolve calendário real nem inventa
    disponibilidade de agenda — só verifica se está dentro do expediente.
    Quando não é possível validar com segurança (categoria desconhecida,
    ou dia não classificado — "hoje"/"amanhã"/domingo/etc.), retorna
    válido=True para não bloquear o fluxo por engano.
    """
    if dia == "domingo":
        return {"valido": False, "horario_operacao": _mensagem_dia_fechado(categoria)}

    if not categoria or categoria not in _HORARIOS_OPERACAO:
        return {"valido": True}

    tipo_dia = _tipo_dia_semana(dia)
    if tipo_dia is None:
        return {"valido": True}

    abre, fecha = _HORARIOS_OPERACAO[categoria][tipo_dia]
    horario_operacao = f"{abre}h às {fecha}h"

    if not periodo:
        return {"valido": True}

    hora = _horario_especifico_para_hora(periodo)
    if hora is not None:
        if abre <= hora < fecha:
            return {"valido": True}
        return {"valido": False, "horario_operacao": horario_operacao}

    # Período genérico (manhã/tarde/noite): "manhã" sempre cabe (abre às
    # 9h em todas as operações); "noite" nunca cabe (fecham no máximo às
    # 18h); "tarde" só é aceito genericamente se o fechamento permitir
    # uma janela real de tarde (>= 15h) — do contrário pede horário exato.
    if periodo == "noite":
        return {"valido": False, "horario_operacao": horario_operacao}
    if periodo == "tarde" and fecha < 15:
        return {"valido": False, "horario_operacao": horario_operacao}
    return {"valido": True}


def _finalizar_estagio_visita(estado: Dict[str, Any], texto: str) -> None:
    """
    Calcula o próximo estagio_visita e, se completo, valida o horário
    contra o expediente da operação antes de qualificar. Se estiver fora
    do expediente, NÃO qualifica — volta para "aguardando_periodo" e
    grava estado["aviso_horario"] com o expediente correto, para a IA
    informar o cliente e pedir um horário válido.
    """
    novo_estagio = _proximo_estagio_visita(estado)
    if novo_estagio == "completo":
        if not estado.get("categoria"):
            estado["categoria"] = _classificar_categoria(
                estado.get("veiculo"), url=estado.get("url"), texto_bruto=texto
            )
        validacao = _validar_horario_visita(
            estado.get("categoria"), estado.get("data_visita"), estado.get("horario_visita")
        )
        if not validacao.get("valido"):
            estado["aviso_horario"] = validacao.get("horario_operacao")
            estado["horario_visita"] = None
            novo_estagio = "aguardando_periodo"
        else:
            estado["aviso_horario"] = None
            estado["qualificado"] = True
    estado["estagio_visita"] = novo_estagio


# Domingo é fechado nas três operações — nenhuma categoria abre. Rejeitado
# no momento da captura do dia (antes mesmo de gravar em data_visita), não
# só na validação final de horário.
_DIA_FECHADO = "domingo"


def _mensagem_dia_fechado(categoria: Optional[str]) -> str:
    """Mensagem factual do expediente, usada quando o cliente pede domingo
    (fechado) — inclui o sábado da operação quando a categoria é conhecida."""
    if categoria in _HORARIOS_OPERACAO:
        _, fecha_sabado = _HORARIOS_OPERACAO[categoria]["sabado"]
        return f"Domingo não abrimos. Atendemos de segunda a sexta das 9h às 18h e aos sábados das 9h às {fecha_sabado}h."
    return "Domingo não abrimos. Atendemos de segunda a sexta das 9h às 18h."


# Sinal de que o cliente quer MUDAR um dia/período já registrado (não
# confundir com a detecção inicial de intenção de visita, _eh_sinal_visita).
# Exige a palavra de mudança E um novo dia/período reconhecido na mesma
# mensagem — evita disparar em perguntas neutras ("ok", "domingo abre?").
_PALAVRAS_MUDANCA_VISITA = (
    "mudar", "trocar", "troca", "prefiro", "melhor",
    "nao consigo", "ao inves de", "em vez de",
)


def _eh_sinal_mudanca_visita(texto_norm: str, dia_novo: Optional[str], periodo_novo: Optional[str]) -> bool:
    if not (dia_novo or periodo_novo):
        return False
    return any(p in texto_norm for p in _PALAVRAS_MUDANCA_VISITA)


def _capturar_dia(estado: Dict[str, Any], dia: Optional[str]) -> None:
    """
    Grava o dia informado no estado, só quando ainda não há dia
    registrado. Rejeita domingo (fechado nas três operações): não grava
    data_visita e registra aviso_dia, para a IA informar o expediente
    correto e pedir outro dia — a visita continua pendente.
    """
    if not dia or estado.get("data_visita"):
        return
    if dia == _DIA_FECHADO:
        estado["aviso_dia"] = _mensagem_dia_fechado(estado.get("categoria"))
        return
    estado["data_visita"] = dia
    estado["aviso_dia"] = None


def _eh_sinal_transferencia(texto_norm: str) -> bool:
    """
    Sinal inequívoco de avançar para atendimento humano: aceitar/agendar
    visita, informar dia/disponibilidade para comparecer, pedir para falar
    com vendedor/consultor, perguntar quem vai atendê-lo, pedir
    telefone/contato do responsável, aceitar que a equipe dê continuidade,
    ou sinalizar intenção de proposta/fechamento/compra. Deliberadamente
    conservador, mesmo estilo das outras heurísticas deste módulo — não
    deve disparar em interesse/dúvida comercial comum.
    """
    grupos = (
        _GATILHOS_VISITA, _GATILHOS_FALAR_VENDEDOR, _GATILHOS_QUEM_ATENDE,
        _GATILHOS_CONTATO_RESPONSAVEL, _GATILHOS_ACEITA_CONTINUIDADE,
        _GATILHOS_DESCONTO_NEGOCIACAO,
    )
    if any(any(g in texto_norm for g in grupo) for grupo in grupos):
        return True
    if _eh_pedido_identificacao_vendedor(texto_norm):
        return True
    if _eh_pedido_falar_com_vendedor_tolerante(texto_norm):
        return True
    if _eh_sinal_transferencia_regex(texto_norm):
        return True
    return _eh_disponibilidade_para_visita(texto_norm)


# Classificação utilitário/passeio. A ORIGEM explícita do lead (domínio do
# link do anúncio, ou nome da loja no texto bruto da mensagem) tem
# prioridade sobre o modelo do veículo — o modelo só decide quando a
# origem não dá nenhum sinal (fallback). Isso evita que extrair_veiculo()
# perder a linha com o nome da loja (quando ela vem separada da linha com
# o ano) resulte em categoria errada.
_DOMINIO_UTILITARIO = "sullatomicrosevans"
_NOMES_LOJA_UTILITARIO = ("sullato micros e vans", "micros e vans")

_PALAVRAS_UTILITARIO = (
    "van", "kombi", "jumper", "jumpy", "boxer", "ducato", "sprinter", "master",
    "furgao", "utilitario", "micro-onibus", "micro onibus", "minibus",
    "micros e vans",
)


def _classificar_categoria(
    veiculo_texto: Optional[str],
    url: Optional[str] = None,
    texto_bruto: Optional[str] = None,
) -> str:
    """
    Classificação utilitário/passeio priorizando a origem explícita do lead
    (domínio do link do anúncio, ou nome da loja no texto bruto da
    mensagem) sobre o modelo do veículo. O modelo (texto já extraído por
    extrair_veiculo) só decide quando a origem não dá nenhum sinal —
    fallback conservador, default "passeio" quando nada é encontrado.
    """
    sinais_origem = _normalizar(f"{url or ''} {texto_bruto or ''}")
    if _DOMINIO_UTILITARIO in sinais_origem or any(n in sinais_origem for n in _NOMES_LOJA_UTILITARIO):
        return "utilitario"

    if not veiculo_texto:
        return "passeio"
    t = _normalizar(veiculo_texto)
    return "utilitario" if any(p in t for p in _PALAVRAS_UTILITARIO) else "passeio"


# ===== Fase 3.1H: atendimento comercial independente por categoria =====
def _detectar_categoria_mencionada(texto_norm: str) -> Optional[str]:
    """
    Detecta menção explícita de categoria (utilitário/passeio) em texto
    livre, usada só para identificar pedido de TROCA de categoria numa
    conversa já qualificada/transferida (ver _trocar_categoria_ativa).
    Diferente de _classificar_categoria: aqui a AUSÊNCIA de sinal deve
    significar "nenhuma categoria mencionada" (retorna None) — não usa o
    fallback default "passeio", que só faz sentido ao classificar um
    veículo já identificado.
    """
    if _DOMINIO_UTILITARIO in texto_norm or any(n in texto_norm for n in _NOMES_LOJA_UTILITARIO):
        return "utilitario"
    if any(p in texto_norm for p in _PALAVRAS_UTILITARIO):
        return "utilitario"
    if "passeio" in texto_norm:
        return "passeio"
    return None


def _trocar_categoria_ativa(estado: Dict[str, Any], nova_categoria: str) -> None:
    """
    Troca a categoria ativa de uma conversa já qualificada (Fase 3.1H):
    salva vendedor/qualificado/transferencia_concluida atuais em
    "atendimentos" sob a categoria antiga (preservando esse atendimento
    sem alteração) e carrega o atendimento da categoria nova — restaurado
    de "atendimentos" se o cliente já tinha passado por ela antes (sem
    novo sorteio de vendedor), ou zerado para permitir uma seleção nova
    quando é a primeira vez que essa categoria aparece na conversa.
    """
    atendimentos = estado.setdefault("atendimentos", {})
    categoria_anterior = estado.get("categoria")
    if categoria_anterior:
        atendimentos[categoria_anterior] = {
            "vendedor": estado.get("vendedor"),
            "qualificado": estado.get("qualificado", False),
            "transferencia_concluida": estado.get("transferencia_concluida", False),
        }

    estado["categoria"] = nova_categoria
    dados = atendimentos.get(nova_categoria)
    if dados:
        estado["vendedor"] = dados.get("vendedor")
        estado["qualificado"] = dados.get("qualificado", False)
        estado["transferencia_concluida"] = dados.get("transferencia_concluida", False)
    else:
        estado["vendedor"] = None
        estado["qualificado"] = True
        estado["transferencia_concluida"] = False


def _eh_resposta_indefinida(texto_norm: str) -> bool:
    """
    True quando a mensagem não traz informação mínima de veículo/interesse
    (resposta vazia, negativa, indefinida ou pergunta genérica de volta).
    Heurística simples e deliberadamente conservadora — não tenta
    interpretação semântica complexa.
    """
    if not texto_norm or len(texto_norm) < 3:
        return True
    if texto_norm in _RESPOSTAS_CURTAS_SEM_INFO:
        return True
    return any(re.search(p, texto_norm) for p in _PADROES_INDEFINIDOS)


def _expirado(estado: Dict[str, Any]) -> bool:
    return (time.time() - estado.get("ultima_atualizacao", 0)) > _ESTADO_TTL


def _novo_estado(numero: str) -> Dict[str, Any]:
    return {
        "numero": numero,
        "ativo": False,
        "origem": None,             # "site" | "social" | None
        "veiculo": None,
        "url": None,
        "categoria": None,          # não preenchido nesta etapa (fase futura)
        "estagio": "novo",          # "aguardando_veiculo" | "veiculo_identificado"
        "qualificado": False,       # não calculado nesta etapa (fase futura)
        "intencao_visita": None,    # texto bruto que sinalizou a intenção comercial forte
        "estagio_visita": None,     # None | "aguardando_dia" | "aguardando_periodo" | "completo"
        "data_visita": None,        # texto literal do dia informado (ex.: "quarta")
        "horario_visita": None,     # texto literal do período/horário informado (ex.: "manha")
        "aviso_horario": None,      # expediente correto quando o horário pedido está fora (ex.: "9h às 14h")
        "aviso_dia": None,          # mensagem de expediente quando o cliente pede domingo (fechado)
        "vendedor": None,           # {"nome":..., "link":...} quando selecionado pelo backend
        "transferencia_concluida": False,
        "atendimentos": {},         # Fase 3.1H: histórico por categoria — {categoria: {"vendedor", "qualificado", "transferencia_concluida"}}
        "ultima_atualizacao": time.time(),
    }


# ============================================================
# API pública
# ============================================================

def assistente_comercial_ativo() -> bool:
    """
    Lê a variável de ambiente ASSISTENTE_COMERCIAL_ATIVO.
    Default conservador: False (não depende de nenhuma alteração no Render).
    """
    val = os.getenv("ASSISTENTE_COMERCIAL_ATIVO", "").strip().lower()
    return val in ("1", "true", "sim", "yes", "on")


def contem_sinal_comercial(texto: str) -> bool:
    """
    Correção A (Bloco A comercial): verifica se um texto — mesmo com uma
    saudação embutida no início ("Olá, quero falar com um vendedor") — já
    carrega sinal comercial estruturado. Usado por responder.py para não
    deixar uma saudação embutida abrir o menu inicial quando a mesma
    mensagem já é uma intenção comercial. Reaproveita só os detectores já
    existentes; não cria heurística nova.
    """
    texto_norm = _normalizar(texto or "")
    if not texto_norm:
        return False
    if detectar_url(texto):
        return True
    if _eh_entrada_forte_veiculo(texto_norm):
        return True
    if _eh_sinal_visita(texto_norm):
        return True
    if _eh_sinal_transferencia(texto_norm):
        return True
    if _eh_interesse_generico(texto_norm):
        return True
    return False


def detectar_url(texto: str) -> Optional[str]:
    """Extrai a primeira URL http(s) presente no texto, ou None."""
    if not texto:
        return None
    m = _URL_RE.search(texto)
    if not m:
        return None
    return m.group(0).rstrip(".,;)")


def extrair_veiculo(texto: str, url: Optional[str] = None) -> Optional[str]:
    """
    Heurística simples para identificar a descrição do veículo numa mensagem:
    - prioriza a linha que contém um ano de 4 dígitos (padrão comum em
      descrições de veículo, ex.: "KIA BONGO 2011 - ...");
    - senão, ignora a linha da URL e linhas de saudação/introdução e usa a
      primeira linha restante.
    Não tenta normalizar marca/modelo/versão — isso fica para uma fase futura
    de enriquecimento via URL/API.
    """
    if not texto:
        return None
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]
    if url:
        linhas = [l for l in linhas if url not in l]
    if not linhas:
        return None

    com_ano = [l for l in linhas if _ANO_RE.search(l)]
    if com_ano:
        return com_ano[0][:200]

    candidatas = [l for l in linhas if not _normalizar(l).startswith(_INTROS_IGNORAVEIS)]
    escolhida = candidatas[0] if candidatas else linhas[0]
    return escolhida[:200]


def obter_estado(numero: str) -> Optional[Dict[str, Any]]:
    """
    Consulta o estado comercial atual do telefone. Expira e remove
    automaticamente se o TTL tiver vencido. Retorna sempre uma cópia
    (nunca a referência interna).
    """
    estado = _ESTADOS.get(numero)
    if not estado:
        return None
    if _expirado(estado):
        del _ESTADOS[numero]
        return None
    return dict(estado)


def tem_contexto_comercial(numero: str) -> bool:
    """Atalho: existe sessão comercial ativa e não expirada para o telefone?"""
    estado = obter_estado(numero)
    return bool(estado and estado.get("ativo"))


def limpar_estado(numero: str) -> None:
    """Remove o estado comercial do telefone, se existir."""
    _ESTADOS.pop(numero, None)


def definir_vendedor(numero: str, nome: str, link: str) -> bool:
    """
    Grava, no estado do telefone, o vendedor selecionado pelo BACKEND
    (nunca pela IA). Idempotência é responsabilidade de quem chama: só deve
    ser invocada quando estado["vendedor"] ainda estiver None.
    """
    estado = _ESTADOS.get(numero)
    if not estado or _expirado(estado):
        return False
    estado["vendedor"] = {"nome": nome, "link": link}
    estado["ultima_atualizacao"] = time.time()
    return True


def marcar_transferencia_concluida(numero: str) -> bool:
    """Marca a transferência como concluída — só deve ser chamada após o
    envio ao vendedor ter sido confirmado com sucesso."""
    estado = _ESTADOS.get(numero)
    if not estado or _expirado(estado):
        return False
    estado["transferencia_concluida"] = True
    estado["ultima_atualizacao"] = time.time()
    return True


def processar_mensagem(
    numero: str, texto: str, ultima_mensagem_ia: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Processa uma mensagem recebida e cria/atualiza o estado comercial do
    telefone. Retorna uma cópia do estado atualizado, ou None quando a
    mensagem não tem relação comercial e não existe sessão aberta
    (ex.: um "Olá" isolado — cenário C, não deve virar lead).

    ultima_mensagem_ia (opcional): último texto da própria IA nesta
    conversa (já existe em _HIST_IA, responder.py). Usado só para
    interpretar uma resposta afirmativa curta ("sim") como aceite de
    visita quando a IA acabou de convidar o cliente a conhecer o veículo
    na loja — nunca presumido de um "sim" isolado sem esse contexto.
    """
    texto = texto or ""
    texto_norm = _normalizar(texto)

    estado_existente = obter_estado(numero)  # já expira/limpa sozinho se vencido

    # Fase 3.1E — fluxo de VISITA (rota D): dia + período antes de transferir.
    # Continuação de uma coleta já em andamento tem prioridade sobre qualquer
    # nova detecção de sinal nesta mensagem.
    if (
        estado_existente
        and estado_existente.get("ativo")
        and not estado_existente.get("qualificado")
        and estado_existente.get("estagio_visita") in ("aguardando_dia", "aguardando_periodo")
    ):
        dia = _extrair_dia(texto_norm)
        periodo = _extrair_periodo(texto_norm)
        _capturar_dia(estado_existente, dia)
        if periodo and not estado_existente.get("horario_visita"):
            estado_existente["horario_visita"] = periodo
        _finalizar_estagio_visita(estado_existente, texto)
        estado_existente["ultima_atualizacao"] = time.time()
        _ESTADOS[numero] = estado_existente
        return dict(estado_existente)

    # Sinal inequívoco de avançar para atendimento humano (aprovado por
    # Anderson: urgência isolada não entra aqui). Só roda enquanto ainda não
    # qualificado — depois disso a seleção de vendedor cuida da idempotência.
    if estado_existente and estado_existente.get("ativo") and not estado_existente.get("qualificado"):
        # Rota D (visita): entra na coleta de dia/período em vez de
        # transferir na hora — pode já vir com dia e/ou período na mesma
        # mensagem (ex.: "posso ir quarta de manha"), sem forçar formulário.
        if _eh_sinal_visita(texto_norm) or (
            _eh_resposta_afirmativa_curta(texto_norm) and _ia_convidou_para_visita(ultima_mensagem_ia)
        ):
            dia = _extrair_dia(texto_norm)
            periodo = _extrair_periodo(texto_norm)
            _capturar_dia(estado_existente, dia)
            if periodo:
                estado_existente["horario_visita"] = periodo
            estado_existente["intencao_visita"] = texto.strip()[:200]
            _finalizar_estagio_visita(estado_existente, texto)
            estado_existente["ultima_atualizacao"] = time.time()
            _ESTADOS[numero] = estado_existente
            return dict(estado_existente)

        # Rota E (contato humano direto): transfere imediatamente, sem
        # passar pela coleta de dia/período — comportamento já aprovado e
        # testado anteriormente, preservado sem mudança.
        if _eh_sinal_transferencia(texto_norm):
            estado_existente["qualificado"] = True
            estado_existente["intencao_visita"] = texto.strip()[:200]
            if not estado_existente.get("categoria"):
                estado_existente["categoria"] = _classificar_categoria(
                    estado_existente.get("veiculo"), url=estado_existente.get("url"), texto_bruto=texto
                )
            estado_existente["ultima_atualizacao"] = time.time()
            _ESTADOS[numero] = estado_existente
            return dict(estado_existente)

    # Fase 3.1F — pedido explícito de mudar dia/período de uma visita já
    # qualificada (inclusive após transferência concluída). Atualiza só a
    # visita — NUNCA reabre seleção de vendedor nem retransfere (isso é
    # responsabilidade de responder.py, que só transfere quando ainda não
    # há vendedor gravado no estado). Mensagens neutras ("ok", perguntas
    # factuais como "domingo abre?") não disparam isso — exige palavra de
    # mudança explícita junto com um dia/período novo reconhecido.
    if estado_existente and estado_existente.get("ativo") and estado_existente.get("qualificado"):
        # Fase 3.1H — pedido explícito de vendedor para uma CATEGORIA
        # diferente da já qualificada/transferida nesta conversa (ex.:
        # cliente já tem vendedor no utilitário e passa a perguntar sobre
        # passeio). Abre um atendimento independente para a categoria nova
        # sem apagar nem sobrescrever o atendimento anterior — ver
        # _trocar_categoria_ativa. Exige sinal de categoria E sinal de
        # transferência juntos, para não disparar em menção incidental.
        categoria_mencionada = _detectar_categoria_mencionada(texto_norm)
        if (
            categoria_mencionada
            and categoria_mencionada != estado_existente.get("categoria")
            and _eh_sinal_transferencia(texto_norm)
        ):
            _trocar_categoria_ativa(estado_existente, categoria_mencionada)
            estado_existente["intencao_visita"] = texto.strip()[:200]
            estado_existente["ultima_atualizacao"] = time.time()
            _ESTADOS[numero] = estado_existente
            return dict(estado_existente)

        dia_novo = _extrair_dia(texto_norm)
        periodo_novo = _extrair_periodo(texto_norm)
        if _eh_sinal_mudanca_visita(texto_norm, dia_novo, periodo_novo):
            if dia_novo == _DIA_FECHADO:
                estado_existente["aviso_dia"] = _mensagem_dia_fechado(estado_existente.get("categoria"))
            else:
                dia_candidato = dia_novo or estado_existente.get("data_visita")
                periodo_candidato = periodo_novo or estado_existente.get("horario_visita")
                validacao = _validar_horario_visita(
                    estado_existente.get("categoria"), dia_candidato, periodo_candidato
                )
                if validacao.get("valido"):
                    if dia_novo:
                        estado_existente["data_visita"] = dia_novo
                    if periodo_novo:
                        estado_existente["horario_visita"] = periodo_novo
                    estado_existente["aviso_horario"] = None
                    estado_existente["aviso_dia"] = None
                else:
                    estado_existente["aviso_horario"] = validacao.get("horario_operacao")
            estado_existente["ultima_atualizacao"] = time.time()
            _ESTADOS[numero] = estado_existente
            return dict(estado_existente)

    # Continuação de uma sessão que está aguardando o veículo (cenário D)
    if estado_existente and estado_existente.get("estagio") == "aguardando_veiculo":
        url_msg = detectar_url(texto)
        if url_msg and not estado_existente.get("url"):
            estado_existente["url"] = url_msg
            if not estado_existente.get("origem"):
                estado_existente["origem"] = "site"

        if not _eh_resposta_indefinida(texto_norm):
            # Preserva o veículo já identificado deterministicamente pelo
            # anúncio/site — uma mensagem de texto livre posterior NUNCA
            # sobrescreve um veículo já capturado, só preenche quando ainda
            # está vazio.
            if not estado_existente.get("veiculo"):
                veiculo = extrair_veiculo(texto, url=url_msg) or texto.strip()[:200]
                estado_existente["veiculo"] = veiculo
            estado_existente["estagio"] = "veiculo_identificado"
            estado_existente["categoria"] = _classificar_categoria(
                estado_existente.get("veiculo"), url=url_msg or estado_existente.get("url"), texto_bruto=texto
            )
            # Fecha o loop da Correção B: se o cliente já tinha pedido
            # vendedor explicitamente (sem saber ainda a categoria), agora
            # que a categoria é conhecida, qualifica direto — sem perguntar
            # de novo se ele quer falar com alguém.
            if estado_existente.get("intencao_visita") and not estado_existente.get("qualificado"):
                estado_existente["qualificado"] = True
        # resposta indefinida/negativa: mantém estagio "aguardando_veiculo"

        estado_existente["ultima_atualizacao"] = time.time()
        _ESTADOS[numero] = estado_existente
        return dict(estado_existente)

    # Entrada comercial vinda de site/anúncio, com URL ou sinal forte de
    # veículo mesmo sem URL reconhecida (cenário A)
    url = detectar_url(texto)
    if url or _eh_entrada_forte_veiculo(texto_norm):
        estado = estado_existente or _novo_estado(numero)
        estado["ativo"] = True
        estado["origem"] = "site"
        if url:
            estado["url"] = url
        veiculo = extrair_veiculo(texto, url=url)
        if veiculo:
            estado["veiculo"] = veiculo
            estado["estagio"] = "veiculo_identificado"
            estado["categoria"] = _classificar_categoria(veiculo, url=url, texto_bruto=texto)
        else:
            estado["estagio"] = "aguardando_veiculo"
        estado["ultima_atualizacao"] = time.time()
        _ESTADOS[numero] = estado
        return dict(estado)

    # Entrada comercial genérica, sem veículo identificado ainda (cenário B)
    if _eh_interesse_generico(texto_norm):
        estado = estado_existente or _novo_estado(numero)
        estado["ativo"] = True
        if not estado.get("origem"):
            estado["origem"] = "social"
        estado["estagio"] = "aguardando_veiculo"
        estado["ultima_atualizacao"] = time.time()
        _ESTADOS[numero] = estado
        return dict(estado)

    # Correção B (Bloco A comercial): pedido explícito de vendedor/contato
    # direto SEM sessão comercial prévia — não exige veículo/URL mencionado
    # antes. Não transfere cegamente: se a própria mensagem não permitir
    # determinar a categoria (utilitário/passeio) com segurança, entra no
    # fluxo comercial pedindo o veículo primeiro (mesmo padrão do cenário
    # B acima), guardando a intenção já expressa em intencao_visita — assim
    # que a categoria for conhecida (cenário D), qualifica direto, sem
    # pedir de novo. Nunca usa vendedor de categoria errada.
    if estado_existente is None and _eh_sinal_transferencia(texto_norm):
        estado = _novo_estado(numero)
        estado["ativo"] = True
        estado["origem"] = "social"
        estado["intencao_visita"] = texto.strip()[:200]

        categoria_conhecida = None
        if _DOMINIO_UTILITARIO in texto_norm or any(n in texto_norm for n in _NOMES_LOJA_UTILITARIO):
            categoria_conhecida = "utilitario"

        if categoria_conhecida:
            estado["categoria"] = categoria_conhecida
            estado["estagio"] = "veiculo_identificado"
            estado["qualificado"] = True
        else:
            estado["estagio"] = "aguardando_veiculo"

        estado["ultima_atualizacao"] = time.time()
        _ESTADOS[numero] = estado
        return dict(estado)

    # Nenhum sinal comercial nesta mensagem
    if estado_existente:
        # Sessão já ativa (ex.: veículo já identificado) — preserva como está,
        # mas renova o TTL (Item 4 do diagnóstico Bloco A): sem isso, uma
        # sequência de mensagens neutras/factuais pós-transferência ("ok",
        # "domingo abre?") nunca tocava ultima_atualizacao, podendo expirar
        # o estado (inclusive o vendedor já atribuído) com a conversa real
        # ainda em andamento.
        estado_existente["ultima_atualizacao"] = time.time()
        _ESTADOS[numero] = estado_existente
        return dict(estado_existente)

    # Sem sessão e sem sinal comercial (ex.: "Olá" isolado) — cenário C
    return None
