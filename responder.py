import random

FRASES_INTENCOES = {
    "menu": ["menu", "início", "ola", "oi"],
    "compra": ["comprar", "quero comprar", "ver veículos", "ver carros", "quero adquirir", "interessado em veículo"],
    "venda": ["vender", "consignar", "consignação", "deixar pra vender", "quero deixar um veículo"],
    "credito": ["score baixo", "nome sujo", "negativado", "meu cpf", "crédito", "tenho restrição", "quero financiar", "sem entrada", "preciso trabalhar"],
    "governo": ["governo", "prefeitura", "licitação", "órgão público", "compra institucional", "venda para prefeitura", "setor público"],
    "endereco": ["endereço", "localização", "onde fica", "como chegar", "onde estão", "qual o cep"],
    "filiais": ["tem outras lojas", "filial", "outros estados", "outra unidade", "fora de sp", "lojas em outros lugares"],
    "peças": ["vende peça", "tem peça", "vendem peças", "preciso de peça"],
    "garantia": ["comprei um veículo e está com problema", "problema no veículo", "veículo com defeito", "veículo com problema", "garantia", "pós-venda"],
    "lista_veiculos": ["lista de veículos", "me manda a lista", "o que vocês têm", "veículo disponível", "valor da van", "preço dos veículos"],
    "aluguel": ["vocês alugam", "aluga van", "tem aluguel", "fazem locação"],
    "serviço": ["vocês indicam serviço", "ajudam a trabalhar", "me colocam pra trabalhar", "indicam parceiro"],
    "prontos_trabalhar": ["van escolar", "van de carga", "pra fretamento", "veículo pronto pra trabalhar"],
    "perfil_escolar": ["escolar", "transporte escolar", "van escolar"],
    "perfil_carga": ["carga", "transporte de carga", "fiorino", "baú", "logística"],
    "perfil_executivo": ["executivo", "luxo", "vip", "cliente executivo"],
    "perfil_fretamento": ["fretamento", "viagem", "turismo", "passeio em grupo"],
    "perfil_pessoal": ["uso pessoal", "particular", "carro pra mim"],
    "perfil_autonomo": ["trabalhar por conta", "sair da clt", "começar a trabalhar", "ter minha própria renda"],
    "perfil_passeio": ["carro de passeio", "carro familiar", "uso urbano", "trabalho com app", "uber", "99", "táxi", "motorista de aplicativo"],
    "perfil_utilitario": ["utilitário", "saveiro", "strada", "montana", "trabalho leve", "caminhonete leve"],
    "loja_passeio": ["loja ponte rasa", "loja de passeio", "carros da loja ponte rasa", "loja carro", "loja av. são miguel 4049", "4084", "loja de carro"]
}

VENDEDORES_PASSEIO = [
    "🚗 Alex – 📲 https://wa.me/5511996371559",
    "🚗 Alexandre – 📲 https://wa.me/5511940559880",
    "🚗 Jeferson – 📲 https://wa.me/5511941006862",
    "🚗 Marcela – 📲 https://wa.me/5511912115673",
    "🚗 Pedro – 📲 https://wa.me/5511952704363",
    "🚗 Vinicius – 📲 https://wa.me/5511911260469",
    "🚗 Vanessa – 📲 https://wa.me/5511947954378",
    "🚗 Thiago – 📲 https://wa.me/5511986122905"
]

VENDEDORES_GERAL = [
    "🧑‍💼 Silvano – 📲 https://wa.me/5511988598736",
    "🧑‍💼 Thiago – 📲 https://wa.me/5511986122905",
    "🧑‍💼 Magali – 📲 https://wa.me/5511940215082"
]

def identificar_intencao(mensagem):
    mensagem = mensagem.lower()
    for chave, termos in FRASES_INTENCOES.items():
        for termo in termos:
            if termo in mensagem:
                return chave
    return "desconhecido"

def responder(mensagem):
    intencao = identificar_intencao(mensagem)

    if intencao == "menu":
        return menu_inicial()
    elif intencao == "compra":
        return resposta_compra()
    elif intencao == "venda":
        return resposta_venda()
    elif intencao == "credito":
        return resposta_score_baixo()
    elif intencao == "governo":
        return resposta_governo()
    elif intencao == "endereco":
        return resposta_endereco()
    elif intencao == "filiais":
        return resposta_filiais()
    elif intencao == "peças":
        return resposta_pecas()
    elif intencao == "garantia":
        return resposta_garantia()
    elif intencao == "lista_veiculos":
        return resposta_lista_veiculos()
    elif intencao == "aluguel":
        return resposta_aluguel()
    elif intencao == "serviço":
        return resposta_servico()
    elif intencao == "prontos_trabalhar":
        return resposta_prontos_trabalhar()
    elif intencao == "loja_passeio":
        return resposta_lojas_passeio()
    elif intencao.startswith("perfil_"):
        perfil = intencao.replace("perfil_", "")
        return resposta_por_perfil(perfil)
    else:
        return resposta_padrao()

# === RESPOSTAS ===

def menu_inicial():
    return (
        "👋 Olá! Seja bem-vindo à Sullato Micros e Vans.\n"
        "Escolha uma das opções abaixo para continuar:\n\n"
        "1️⃣ Comprar um veículo\n"
        "2️⃣ Vender ou consignar um veículo\n"
        "3️⃣ Tenho score baixo e preciso de ajuda\n\n"
        "Ou escreva com suas palavras o que você procura 😉"
    )

def resposta_compra():
    return resposta_por_perfil("geral")

def resposta_venda():
    vendedores = embaralhar_vendedores("geral")
    return (
        "📣 Trabalhamos com *consignação inteligente*.\n"
        "Você deixa o veículo conosco e cuidamos de tudo:\n"
        "✅ Divulgação\n✅ Segurança\n✅ Agilidade\n\n"
        "Nos envie modelo, ano e fotos!\n\n"
        "Fale agora com nosso *Departamento de Vendas*:\n" +
        "\n".join(vendedores)
    )

def resposta_score_baixo():
    return (
        "💳 Mesmo com score baixo, conseguimos analisar seu perfil!\n"
        "Trabalhamos com bancos parceiros que consideram mais do que apenas o score.\n\n"
        "🔍 Para começar a análise, por favor envie:\n"
        "• Nome completo\n"
        "• CPF\n"
        "• Possui CNH? (sim ou não)\n"
        "• Categoria da CNH\n"
        "• Data de nascimento\n"
        "• Possui entrada disponível?\n\n"
        "Se você tem restrição no nome ou está sem entrada:\n"
        "🙏 Nós entendemos. Muitas pessoas começam exatamente assim.\n"
        "Vamos juntos encontrar uma solução pra te ajudar a trabalhar com dignidade!\n\n"
        "Fale direto com o *Departamento de Crédito*:\n"
        "👩‍💼 Patrícia – 📲 https://wa.me/5511940215081"
    )

def resposta_governo():
    return (
        "🏛️ Atendemos prefeituras, secretarias e compras públicas em geral.\n"
        "Temos veículos homologados, documentação completa e suporte para licitações.\n"
        "Saiba mais:\n"
        "🌐 https://www.sullato.com.br/governo\n\n"
        "Fale direto com o *Departamento de Vendas ao Governo*:\n"
        "👩‍💼 Solange – 📲 https://wa.me/5511989536141"
    )

def resposta_endereco():
    return (
        "📍 Nossa loja principal fica na Av. São Miguel, 7900 – CEP 08070-001 – Vila Norma – SP.\n"
        "🕒 Atendimento da matriz:\n"
        "• Segunda a sexta: 9h às 18h\n"
        "• Sábados e feriados: 9h às 14h"
    )

def resposta_filiais():
    return (
        "🏢 Temos também lojas dedicadas a veículos de passeio:\n"
        "📍 Av. São Miguel, 4049 – Ponte Rasa – CEP 03878-001 – SP\n"
        "📍 Av. São Miguel, 4084 – Ponte Rasa – CEP 03878-001 – SP\n"
        "🕒 Atendimento da linha de passeio:\n"
        "• Segunda a sexta: 9h às 19h\n"
        "• Sábados e feriados: 9h às 17h"
    )

def resposta_pecas():
    return "🛠️ Para peças, entre em contato com nosso setor pelo telefone: (11) 2542-3332."

def resposta_garantia():
    return "📞 Para assuntos de garantia ou pós-venda, fale com nosso setor especializado: (11) 2542-3332."

def resposta_lista_veiculos():
    return "📋 Consulte nossa lista de veículos atualizada no site oficial: https://www.sullato.com.br"

def resposta_aluguel():
    return "🚐 Por enquanto não alugamos vans, mas em breve teremos essa opção disponível. Fique de olho! 😉"

def resposta_servico():
    return "🤝 Sim! Após a compra, indicamos parceiros para te ajudar a começar a trabalhar com o veículo."

def resposta_prontos_trabalhar():
    return "✅ Temos vans escolares, de carga e para fretamento – todas prontas pra rodar com documentação em dia."

def resposta_lojas_passeio():
    return (
        "📍 Lojas de veículos de passeio:\n"
        "• Av. São Miguel, 4049 – Ponte Rasa – CEP 03878-001 – SP\n"
        "• Av. São Miguel, 4084 – Ponte Rasa – CEP 03878-001 – SP\n"
        "🕒 Atendimento:\n"
        "• Segunda a sexta: 9h às 19h\n"
        "• Sábados e feriados: 9h às 17h"
    )

def resposta_por_perfil(perfil):
    vendedores = embaralhar_vendedores("passeio" if perfil == "passeio" else "geral")
    descricoes = {
        "escolar": "🚌 Temos veículos ideais para transporte escolar, com conforto e documentação em dia.",
        "carga": "📦 Temos vans e furgões para transporte de carga leve e média, prontas pra trabalhar.",
        "executivo": "💼 Modelos de alto padrão para transporte executivo, viagens ou serviços VIP.",
        "fretamento": "🧳 Opções completas para fretamento contínuo ou turismo.",
        "pessoal": "🚗 Veículos ideais para uso familiar ou pessoal, com economia e conforto.",
        "autonomo": "🚀 Está começando por conta própria? Um veículo pode ser seu primeiro passo pra independência!",
        "passeio": "🚗 Temos carros ideais para uso familiar e também para trabalhar com aplicativos como Uber, 99 e táxi.",
        "utilitario": "🔧 Veículos utilitários prontos para o trabalho pesado com resistência, economia e ótimo custo-benefício.",
        "geral": "🚗 Show! Vamos te ajudar a escolher o veículo ideal. Temos vans, carros de passeio, escolares, executivos e para carga."
    }
    texto = descricoes.get(perfil, descricoes["geral"])
    return (
        f"{texto}\n\n"
        "📌 Qual o ano e faixa de valor que você procura?\n"
        "💰 Vai pagar à vista ou precisa de financiamento?\n"
        "🚗 Tem entrada em dinheiro ou veículo na troca?\n\n"
        "🌐 Acesse nosso site: https://www.sullato.com.br\n"
        "📸 Instagram: @sullatomicrosevans\n\n"
        "Fale agora com nosso *Departamento de Vendas*:\n" +
        "\n".join(vendedores)
    )

def resposta_padrao():
    return (
        "🤖 Não entendi exatamente o que você deseja, mas posso te ajudar com:\n"
        "👉 Comprar, vender, financiar, trabalhar ou saber sobre a loja.\n"
        "Me diga com outras palavras e vamos conversar! 😉"
    )

def embaralhar_vendedores(tipo):
    lista = VENDEDORES_PASSEIO.copy() if tipo == "passeio" else VENDEDORES_GERAL.copy()
    random.shuffle(lista)
    return lista
