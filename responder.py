def gerar_resposta(texto_usuario):
    texto = texto_usuario.strip().lower()

    if "bom dia" in texto:
        return "Bom dia! Que Deus abençoe sua jornada hoje! ☀️🙏"
    elif "boa tarde" in texto:
        return "Boa tarde! Que sua tarde seja produtiva e cheia de boas notícias! ☕🚐"
    elif "vans" in texto or "van escolar" in texto:
        return "Temos várias opções de vans escolares e executivas disponíveis. Quer que eu envie o catálogo? 📚🚐"
    elif "carga" in texto or "fiorino" in texto:
        return "Temos veículos ideais para transporte de carga. Posso te mostrar as opções em estoque? 📦🚚"
    elif "valor" in texto or "preço" in texto:
        return "Os valores variam conforme o modelo e ano. Me diz qual tipo de veículo você procura? 💰"
    elif "sullato" in texto:
        return "A Sullato é referência em vans, utilitários e veículos de passeio. Conte conosco! 🚐✅"
    elif "oi" in texto or "olá" in texto:
        return "Olá! A Sullato agradece o seu contato. Em que posso te ajudar hoje? 👋"
    else:
        return "Recebemos sua mensagem! Um de nossos especialistas vai te responder em instantes. ✅"
