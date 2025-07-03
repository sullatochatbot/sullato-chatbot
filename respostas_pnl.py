def gerar_resposta(mensagem):
    msg = mensagem.lower()

    if any(p in msg for p in ["troca", "trocar", "pegar outro", "aceita meu carro"]):
        return ("Aceitamos sim seu veículo na troca, e ainda conseguimos oferecer troco se precisar! "
                "Me manda fotos e o modelo que você procura pra eu te ajudar agora mesmo.")

    elif any(p in msg for p in ["financia", "financiamento", "nome sujo", "score", "aprovação"]):
        return ("Financiamos mesmo com score baixo! Trabalhamos com bancos que facilitam a aprovação. "
                "Se quiser, já posso simular: me manda seu nome completo e CPF.")

    elif any(p in msg for p in ["escolar", "vans escolar", "perua escolar", "aluno", "transporte escolar"]):
        return ("Temos vans escolares prontas pra rodar, com documentação atualizada. "
                "Me diz sua cidade e se precisa com adaptação que te mostro os modelos ideais.")

    elif any(p in msg for p in ["baú", "carga", "furgão", "seco", "refrigerado"]):
        return ("Trabalhamos com vans de carga seca, baú e refrigeradas. Qual tipo de carga você transporta? "
                "Me conta pra eu te indicar as melhores opções!")

    elif any(p in msg for p in ["comprar", "quero uma van", "vender para mim", "vocês tem van"]):
        return ("Temos sim! Vans escolares, de carga e também para transporte executivo. "
                "Me diz o uso que você pretende que eu já te mando as melhores sugestões.")

    elif any(p in msg for p in ["onde fica", "endereço", "localização", "como chegar", "maps"]):
        return ("Estamos em São Paulo, fácil acesso pela Marginal Tietê. "
                "Quer que eu te mande o link direto do Maps ou prefere agendar uma visita?")

    elif any(p in msg for p in ["horário", "atendimento", "funcionamento", "que horas"]):
        return ("Nosso horário de atendimento é de segunda a sábado, das 8h às 18h. "
                "Pode nos chamar aqui sempre que precisar!")

    elif any(p in msg for p in ["olá", "bom dia", "boa tarde", "oi", "e aí"]):
        return ("Oi, tudo bem? Seja muito bem-vindo à Sullato Micros e Vans. Posso te ajudar com compra, venda ou financiamento?")

    elif any(p in msg for p in ["obrigado", "valeu", "até mais", "gratidão"]):
        return ("Eu que agradeço pelo contato! Quando quiser, estamos aqui pra te ajudar com o que precisar. Forte abraço!")

    else:
        return ("Recebi sua mensagem! Pra te ajudar melhor, me diz se está querendo comprar, vender ou financiar um veículo.")
