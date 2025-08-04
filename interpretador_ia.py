def interpretar_mensagem(texto):
    texto = texto.lower()

    if any(p in texto for p in ["crédito", "financiamento", "score", "aprovação"]):
        return "credito"
    elif any(p in texto for p in ["endereço", "local", "fica onde", "como chegar"]):
        return "endereco"
    elif any(p in texto for p in ["comprar", "venda", "tenho interesse", "ver veículos"]):
        return "comprar"
    elif any(p in texto for p in ["vender", "consignar", "quero anunciar", "quero vender"]):
        return "vender"
    elif any(p in texto for p in ["oficina", "conserto", "peças"]):
        return "oficina"
    elif any(p in texto for p in ["garantia", "problema", "defeito", "troca"]):
        return "garantia"
    else:
        return "desconhecido"
