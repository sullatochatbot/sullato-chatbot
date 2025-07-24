def gerar_resposta(mensagem):
    texto = mensagem.strip().lower()

    saudacoes = [
        "oi", "olá", "ola", "van", "utilitário", "leve", "passeio",
        "carro", "interesse", "comprar", "vender", "score",
        "financiamento", "refinanciamento", "credito", "peças",
        "oficina", "sullato"
    ]
    
    if any(p in texto for p in saudacoes):
        return (
            "Olá, aqui quem responde é o atendimento virtual do Grupo Sullato.\n\n"
            "Digite o número da opção desejada:\n"
            "1 – Endereço das lojas, site, redes sociais\n"
            "2 – Comprar\n"
            "3 – Vender\n"
            "4 – Crédito / Financiamento\n"
            "5 – Oficina e Peças\n"
            "6 – Vendas ao Governo\n"
            "7 – Pós-venda / Garantia"
        )

    opcoes = {
        "1": "📍 *Endereços e Contatos Sullato*\n\n"
             "🔗 *Site:* https://www.sullato.com.br\n"
             "📸 *Instagram:*\n"
             "@sullatomicrosevans – https://www.instagram.com/sullatomicrosevans\n"
             "@sullato.veiculos – https://www.instagram.com/sullato.veiculos\n\n"
             "🏢 *Lojas:*\n"
             "Sullato Micros e Vans – Av. São Miguel, 7900 – SP\n"
             "(11) 2030-5081 / (11) 2031-5081\n\n"
             "Sullato Veículos – Av. São Miguel, 4049 / 4084 – SP\n"
             "(11) 2542-3332 / (11) 2542-3333",

        "2": "2 – Comprar Veículo\nDigite:\n- 2.1 para *veículo de passeio*\n- 2.2 para *veículo utilitário*",

        "2.1": "🚗 *Compra – Veículo de Passeio*\n"
               "Alexandre – https://wa.me/5511912155673\n"
               "Jeferson – https://wa.me/5511941006862\n"
               "Marcela – https://wa.me/5511912155673\n"
               "Pedro – https://wa.me/5511952704363\n"
               "Thiago – https://wa.me/5511986122905\n"
               "Vinicius – https://wa.me/5511911260469",

        "2.2": "🚐 *Compra – Veículo Utilitário*\n"
               "Magali – https://wa.me/5511940215082\n"
               "Silvano – https://wa.me/5511988598736\n"
               "Thiago – https://wa.me/5511986122902",

        "3": "3 – Vender Veículo\nDigite:\n- 3.1 para *veículo de passeio*\n- 3.2 para *veículo utilitário*",

        "3.1": "📤 *Venda – Veículo de Passeio*\n"
               "Alexandre – https://wa.me/5511912155673\n"
               "Jeferson – https://wa.me/5511941006862\n"
               "Marcela – https://wa.me/5511912155673\n"
               "Pedro – https://wa.me/5511952704363\n"
               "Thiago – https://wa.me/5511986122905\n"
               "Vinicius – https://wa.me/5511911260469",

        "3.2": "📤 *Venda – Veículo Utilitário*\n"
               "Magali – https://wa.me/5511940215082\n"
               "Silvano – https://wa.me/5511988598736\n"
               "Thiago – https://wa.me/5511986122902",

        "4": "💳 *Crédito / Financiamento*\n"
             "Magali – https://wa.me/5511940215082\n"
             "Patricia – https://wa.me/5511940215081",

        "5": "🛠️ *Oficina e Peças*\n"
             "📞 (11) 2542-3332 / (11) 2542-3333\n"
             "Érico – https://wa.me/5511940497678\n"
             "Leandro – https://wa.me/5511940443566",

        "6": "🏛️ *Vendas ao Governo*\n"
             "Lucas, Natan, Leon – (11) 2031-5081 / (11) 2030-5081\n"
             "📧 vendasdireta@sullato.com.br",

        "7": "7 – Pós-venda / Garantia\nDigite:\n- 7.1 para *veículo de passeio*\n- 7.2 para *veículo utilitário*",

        "7.1": "🛡️ *Garantia – Veículo de Passeio*\n"
               "Alexandre – https://wa.me/5511912155673\n"
               "Jeferson – https://wa.me/5511941006862\n"
               "Marcela – https://wa.me/5511912155673\n"
               "Pedro – https://wa.me/5511952704363\n"
               "Thiago – https://wa.me/5511986122905\n"
               "Vinicius – https://wa.me/5511911260469",

        "7.2": "🛡️ *Garantia – Veículo Utilitário*\n"
               "Magali – https://wa.me/5511940215082\n"
               "Silvano – https://wa.me/5511988598736\n"
               "Thiago – https://wa.me/5511986122902"
    }

    if texto in opcoes:
        return opcoes[texto]

    return "❌ Desculpe, não entendi. Por favor, digite um número válido entre 1 e 7 ou uma opção como 2.1, 3.2, etc."
