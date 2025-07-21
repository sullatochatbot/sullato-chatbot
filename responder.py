def gerar_resposta(mensagem):
    texto = mensagem.lower()

    if any(palavra in texto for palavra in ["oi", "olá", "bom dia", "boa tarde", "boa noite"]):
        return "👋 Olá! A *Sullato Micros e Vans* agradece o seu contato. Em que podemos te ajudar hoje?"

    elif any(palavra in texto for palavra in ["van", "vans", "veículo", "veiculos", "carro", "frota"]):
        return "🚐 Temos vans escolares, de carga e executivas à pronta entrega! Deseja ver nosso catálogo completo?"

    elif any(palavra in texto for palavra in ["catálogo", "modelos", "estoque", "ofertas"]):
        return "📘 Você pode acessar nosso catálogo atualizado aqui: [link_do_catalogo]. Qual modelo deseja conhecer melhor?"

    elif any(palavra in texto for palavra in ["financiamento", "financeira", "crédito", "score", "entrada"]):
        return "💰 Trabalhamos com aprovação facilitada, mesmo com score baixo! Posso te passar uma simulação sem compromisso?"

    elif any(palavra in texto for palavra in ["local", "endereço", "onde fica", "localização", "mapa"]):
        return "📍 Estamos na *Av. Exemplo, 123 - São Paulo/SP*. Deseja receber o link direto do Google Maps?"

    elif any(palavra in texto for palavra in ["whatsapp", "vendedor", "atendente", "falar com alguém"]):
        return "📲 Um de nossos especialistas vai te chamar em instantes para atendimento personalizado!"

    elif any(palavra in texto for palavra in ["obrigado", "valeu", "agradecido"]):
        return "🙏 Nós que agradecemos! Qualquer dúvida, estamos sempre à disposição."

    else:
        return "📨 Recebemos sua mensagem! Em breve, um dos nossos atendentes entrará em contato para te ajudar melhor."
