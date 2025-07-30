def gerar_resposta(texto_usuario):
    texto = texto_usuario.lower()

    if "escolar" in texto:
        return "Temos vans escolares prontas para rodar! Quer saber sobre modelos, ano ou parcelas?"
    elif "carga" in texto:
        return "Sim! Temos vans para transporte de carga leve e pesada. Me diz o tipo que você busca."
    elif "executiva" in texto or "luxo" in texto:
        return "Temos vans executivas com alto padrão de conforto. Posso te mandar fotos ou ficha técnica?"
    elif "passeio" in texto:
        return "Claro! Trabalhamos também com vans para passeio e turismo. Vai usar com a família ou para viagens?"
    elif "qual carro" in texto or "tem disponível" in texto:
        return "Temos várias opções em estoque! Quer ver vans escolares, de carga, executiva ou passeio?"
    elif "oi" in texto or "olá" in texto or "bom dia" in texto or "boa tarde" in texto or "boa noite" in texto:
        return "Olá! 👋 Aqui é da Sullato Micros e Vans. Como posso te ajudar hoje?"
    else:
        return "Pode me contar o que está procurando? Temos vans escolares, de carga, executivas e de passeio."
