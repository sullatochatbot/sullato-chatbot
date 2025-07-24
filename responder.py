def gerar_resposta(mensagem):
    texto = mensagem.lower()

    # ITEM 1 - Informações da loja
    if any(p in texto for p in ["endereço", "site", "redes sociais", "instagram", "localização", "loja"]):
        return """📍 Informações da Sullato:

🌐 Site: www.sullato.com.br  
📸 Instagram:  
@sullatomicrosevans  
@sullato.veiculos

🏪 Lojas:  
➡️ Sullato Micros e Vans  
Av. São Miguel, 7900 – SP  
📞 (11) 2030-5081 / (11) 2031-5081

➡️ Sullato Veículos  
Av. São Miguel, 4049 / 4084 – SP  
📞 (11) 2542-3332 / (11) 2542-3333"""

    # ITEM 2 - Comprar veículo
    elif "comprar" in texto or "quero comprar" in texto or "interesse" in texto:
        if "passeio" in texto:
            return """🚗 Veículos de Passeio

Entre em contato com um de nossos consultores:  
Alexandre: (11) 91215-5673  
Jeferson: (11) 94100-6862  
Marcela: (11) 91215-5673  
Pedro: (11) 95270-4363  
Thiago: (11) 98612-2905  
Vinicius: (11) 91126-0469"""
        elif "utilitário" in texto or "van" in texto or "carga" in texto:
            return """🚐 Veículos Utilitários

Entre em contato com um de nossos consultores:  
Magali: (11) 94021-5082  
Silvano: (11) 98859-8736  
Thiago: (11) 98612-2902"""

    # ITEM 3 - Vender veículo
    elif "vender" in texto:
        if "passeio" in texto:
            return """🔁 Venda de Veículo de Passeio

Fale com nossos consultores:  
Alexandre: (11) 91215-5673  
Jeferson: (11) 94100-6862  
Marcela: (11) 91215-5673  
Pedro: (11) 95270-4363  
Thiago: (11) 98612-2905  
Vinicius: (11) 91126-0469"""
        elif "utilitário" in texto or "van" in texto:
            return """🔁 Venda de Veículo Utilitário

Fale com nossos consultores:  
Magali: (11) 94021-5082  
Silvano: (11) 98859-8736  
Thiago: (11) 98612-2902"""

    # ITEM 4 - Crédito e Financiamento
    elif "financiamento" in texto or "refinanciamento" in texto or "credito" in texto or "score" in texto:
        return """💰 Crédito / Financiamento

Fale com nossos especialistas:  
Magali: (11) 94021-5082  
Patricia: (11) 94021-5081"""

    # ITEM 5 - Oficina e peças
    elif "oficina" in texto or "peças" in texto:
        return """🔧 Oficina / Peças

Entre em contato com nosso time:  
📞 (11) 2542-3332 / (11) 2542-3333  
Erico: (11) 94049-7678  
Leandro: (11) 94044-3566"""

    # ITEM 6 - Vendas ao Governo
    elif "governo" in texto or "prefeitura" in texto or "ong" in texto:
        return """🏛️ Vendas ao Governo

Lucas, Natan ou Leon  
📞 (11) 2031-5081 / (11) 2030-5081  
📧 vendasdireta@sullato.com.br"""

    # ITEM 7 - Garantia / Pós-venda
    elif "garantia" in texto or "pós-venda" in texto or "pos venda" in texto:
        if "passeio" in texto:
            return """🛠️ Garantia Veículo de Passeio

Fale com nossos consultores:  
Alexandre: (11) 91215-5673  
Jeferson: (11) 94100-6862  
Marcela: (11) 91215-5673  
Pedro: (11) 95270-4363  
Thiago: (11) 98612-2905  
Vinicius: (11) 91126-0469"""
        elif "utilitário" in texto:
            return """🛠️ Garantia Veículo Utilitário

Fale com nossos consultores:  
Magali: (11) 94021-5082  
Silvano: (11) 98859-8736  
Thiago: (11) 98612-2902"""

    # Saudação padrão
    elif any(p in texto for p in ["oi", "olá", "bom dia", "boa tarde", "boa noite"]):
        return """Olá! 👋  
Eu sou o atendimento virtual da Sullato.  
Me diga com o que você precisa de ajuda:  
🔹 Comprar  
🔹 Vender  
🔹 Financiamento  
🔹 Oficina  
🔹 Garantia  
🔹 Endereço  
🔹 Governo"""

    # Caso não entenda a mensagem
    else:
        return "Desculpe, não entendi sua mensagem. Poderia reformular ou escolher uma das opções: Comprar, Vender, Financiamento, Oficina, Garantia, Endereço ou Governo."
