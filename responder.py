def gerar_resposta(mensagem):
    texto = mensagem.lower()

    if "oi" in texto or "olá" in texto:
        return "Olá! A Sullato agradece o seu contato. Em que posso te ajudar?"
    elif "vans" in texto:
        return "Temos vans escolares, de carga e executivas disponíveis! Deseja ver o catálogo?"
    elif "financeira" in texto or "crédito" in texto:
        return "Trabalhamos com aprovação facilitada mesmo para quem tem score baixo. Quer tentar agora?"
    elif "endereço" in texto or "local" in texto:
        return "Estamos na Av. Exemplo, 123 - SP. Deseja o link do Google Maps?"
    else:
        return "Recebemos sua mensagem! Em instantes um de nossos atendentes entrará em contato."
