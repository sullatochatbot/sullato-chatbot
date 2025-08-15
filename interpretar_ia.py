# interpretar_ia.py
from typing import Optional
import unicodedata
import re

def _normalize(s: str) -> str:
    s = (s or "").strip().lower()
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")

def interpretar_mensagem(texto: str) -> Optional[str]:
    """
    Retorna uma intenção simples:
      "credito", "endereco", "comprar", "vender", "oficina", "garantia"
    ou None se não detectar nada.
    """
    t = _normalize(texto)
    if not t or len(t) < 2:
        return None

    intents = {
        "credito":  ["credito", "financi", "taxa", "parcel", "score", "aprovacao", "aprovação"],
        "endereco": ["endereco", "endereço", "onde fica", "local", "loja", "mapa"],
        "comprar":  ["comprar", "compro", "preco", "preço", "quero um carro", "quero uma van", "interesse"],
        "vender":   ["vender", "vendo", "avaliacao", "avaliação", "consignacao", "consignação", "compram"],
        "oficina":  ["oficina", "peca", "peça", "manutencao", "manutenção", "revisao", "revisão", "conserto", "agendar"],
        "garantia": ["garantia", "pos venda", "pós venda", "defeito", "problema", "assistencia", "assistência"],
    }

    for intent, kws in intents.items():
        if any(kw in t for kw in kws):
            return intent

    mapa_curto = {
        r"^end[erçc]": "endereco",
        r"^finan": "credito",
        r"^compr": "comprar",
        r"^vend": "vender",
        r"^ofi": "oficina",
        r"^garant": "garantia",
    }
    for rx, intent in mapa_curto.items():
        if re.search(rx, t):
            return intent

    return None
