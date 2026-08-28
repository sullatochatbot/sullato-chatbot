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
        "intencao_visita": None,    # não preenchido nesta etapa
        "data_visita": None,        # não preenchido nesta etapa
        "horario_visita": None,     # não preenchido nesta etapa
        "vendedor": None,           # não preenchido nesta etapa
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


def processar_mensagem(numero: str, texto: str) -> Optional[Dict[str, Any]]:
    """
    Processa uma mensagem recebida e cria/atualiza o estado comercial do
    telefone. Retorna uma cópia do estado atualizado, ou None quando a
    mensagem não tem relação comercial e não existe sessão aberta
    (ex.: um "Olá" isolado — cenário C, não deve virar lead).
    """
    texto = texto or ""
    texto_norm = _normalizar(texto)

    estado_existente = obter_estado(numero)  # já expira/limpa sozinho se vencido

    # Continuação de uma sessão que está aguardando o veículo (cenário D)
    if estado_existente and estado_existente.get("estagio") == "aguardando_veiculo":
        url_msg = detectar_url(texto)
        if url_msg and not estado_existente.get("url"):
            estado_existente["url"] = url_msg
            if not estado_existente.get("origem"):
                estado_existente["origem"] = "site"

        if not _eh_resposta_indefinida(texto_norm):
            veiculo = extrair_veiculo(texto, url=url_msg) or texto.strip()[:200]
            estado_existente["veiculo"] = veiculo
            estado_existente["estagio"] = "veiculo_identificado"
        # resposta indefinida/negativa: mantém estagio "aguardando_veiculo"

        estado_existente["ultima_atualizacao"] = time.time()
        _ESTADOS[numero] = estado_existente
        return dict(estado_existente)

    # Entrada comercial vinda de site/anúncio com URL (cenário A)
    url = detectar_url(texto)
    if url:
        estado = estado_existente or _novo_estado(numero)
        estado["ativo"] = True
        estado["origem"] = "site"
        estado["url"] = url
        veiculo = extrair_veiculo(texto, url=url)
        if veiculo:
            estado["veiculo"] = veiculo
            estado["estagio"] = "veiculo_identificado"
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

    # Nenhum sinal comercial nesta mensagem
    if estado_existente:
        # Sessão já ativa (ex.: veículo já identificado) — preserva como está
        return dict(estado_existente)

    # Sem sessão e sem sinal comercial (ex.: "Olá" isolado) — cenário C
    return None
