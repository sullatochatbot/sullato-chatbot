# teste_regressao_utilitario_para_passeio_real.py
"""
Teste de regressão da CONVERSA REAL (Fase 3.1K) que expôs:

Causa A — _detectar_categoria_mencionada usava prioridade fixa (utilitário
sempre vencia por ser checado primeiro), ignorando a intenção real quando a
mensagem menciona as duas categorias na mesma frase (ex.: "de van, ok, mas
nos carros de passeio..."). Corrigido para escolher pela POSIÇÃO da menção
mais à direita no texto.

Causa B — _PADROES_TRANSFERENCIA não reconhecia "vendedores" no plural nem
palavras soltas entre o artigo e o substantivo (ex.: "um DESSES
vendedores"), nem "quem atende [categoria]?" sem a palavra "vendedor".

100% local: sem rede, sem WhatsApp, sem Claude/API externa, sem Google
Sheets. Envio ao vendedor e template Meta são stubados em responder.py.
Executar:  python teste_regressao_utilitario_para_passeio_real.py
"""

import os
import assistente_comercial as ac
import responder


def _preparar_ambiente():
    os.environ["ASSISTENTE_COMERCIAL_ATIVO"] = "1"
    responder._RODIZIO_INDICE_CATEGORIA["utilitario"] = 0
    responder._RODIZIO_INDICE_CATEGORIA["passeio"] = 0


def _stub_envio(monkeypatches, sucesso=True):
    chamadas = {"mensagem": 0, "template": 0, "mensagem_cliente": 0}

    def _fake_enviar_mensagem_com_status(numero, texto):
        chamadas["mensagem"] += 1
        return sucesso

    def _fake_enviar_template(*args, **kwargs):
        chamadas["template"] += 1
        return sucesso

    def _fake_enviar_mensagem(numero, texto, sender_phone_number_id=None):
        chamadas["mensagem_cliente"] += 1

    original_msg = responder._enviar_mensagem_com_status
    original_tpl = responder._enviar_template_novo_lead_vendedor
    original_cli = responder.enviar_mensagem
    responder._enviar_mensagem_com_status = _fake_enviar_mensagem_com_status
    responder._enviar_template_novo_lead_vendedor = _fake_enviar_template
    responder.enviar_mensagem = _fake_enviar_mensagem
    monkeypatches.append((responder, "_enviar_mensagem_com_status", original_msg))
    monkeypatches.append((responder, "_enviar_template_novo_lead_vendedor", original_tpl))
    monkeypatches.append((responder, "enviar_mensagem", original_cli))
    return chamadas


def _restaurar(monkeypatches):
    for obj, nome, original in monkeypatches:
        setattr(obj, nome, original)


def _passo(numero, texto):
    estado = ac.processar_mensagem(numero, texto)
    if estado and estado.get("qualificado") and not estado.get("vendedor"):
        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)
        estado = ac.obter_estado(numero)
    return estado


def _handoff_utilitario_ja_concluido(numero):
    """Reproduz a Parte 1, já homologada: interesse -> utilitario -> escolar
    -> troca de van -> hesitacao sobre financiar/trocar -> pedido de
    vendedor -> handoff para Magali."""
    _passo(numero, "ola, tenho interesse em comprar um veiculo")
    _passo(numero, "procuro um utilitario")
    _passo(numero, "escolar")
    _passo(numero, "ja trabalho, preciso trocar de van.")
    _passo(numero, "talvez, preciso realmente ver o que pode ser melhor, talvez de na troca, talvez so financie...")
    return _passo(numero, "sim, vc pode me passar o contato de algum vendedor ou falo com vc mesmo.")


def teste_conversa_real_utilitario_para_passeio():
    numero = "5511900000401"
    ac.limpar_estado(numero)
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _stub_envio(monkeypatches)

        # Parte 1 (ja homologada) — handoff utilitario para Magali.
        estado = _handoff_utilitario_ja_concluido(numero)
        assert estado["categoria"] == "utilitario", estado
        assert estado["vendedor"]["nome"] == "👩🏻‍💼 Magali", estado
        assert estado["transferencia_concluida"] is True
        assert chamadas["mensagem"] == 1 and chamadas["template"] == 1
        vendedor_utilitario = estado["vendedor"]["nome"]

        # 2) pergunta sobre passeio, sem pedido de vendedor -> nao pode mudar nada.
        estado = _passo(numero, "outra coisa, se eu precisar de um carro de passeio vc consegue me atender.")
        assert estado["categoria"] == "utilitario", estado
        assert estado["vendedor"]["nome"] == vendedor_utilitario
        assert chamadas["mensagem"] == 1, "nao pode transferir so por mencionar passeio sem pedir vendedor"

        # 3) pergunta sobre outro vendedor "ou e a mesma magali" -> sem sinal de categoria nem transferencia clara.
        estado = _passo(numero, "que bom, e nesta loja, tem outro vendedor ou e a mesma magali.")
        assert estado["categoria"] == "utilitario", estado
        assert chamadas["mensagem"] == 1

        # 4) MENSAGEM COM AS DUAS CATEGORIAS ("de van... mas... passeio") -
        # Causa A: deve reconhecer PASSEIO (a mais recente/contextual), mas
        # como nao ha pedido de vendedor aqui, so a IA comenta -- backend
        # nao transfere ainda (sem sinal de transferencia nesta frase).
        texto_norm = ac._normalizar("de van, ok, mas nos carros de passeio vai ser ela tambem.")
        assert ac._detectar_categoria_mencionada(texto_norm) == "passeio", \
            "Causa A: deveria reconhecer PASSEIO como categoria mais recente/contextual"
        estado = _passo(numero, "de van, ok, mas nos carros de passeio vai ser ela tambem.")
        assert estado["categoria"] == "utilitario", "sem pedido de vendedor, nao deve trocar sozinho"
        assert chamadas["mensagem"] == 1

        # 5) PEDIDO REAL DE VENDEDOR DE PASSEIO (a mensagem que falhava) —
        # deve disparar handoff determinístico para PASSEIO imediatamente.
        estado = _passo(numero, "ok, me passe um desses vendedores especialistas em veiculos de passeio.")
        assert estado["categoria"] == "passeio", f"deveria ter mudado para PASSEIO, veio {estado['categoria']!r}"
        nomes_passeio = [n for n, _ in responder.VENDEDORES_PASSEIO_BASE]
        assert estado["vendedor"] is not None, "handoff de passeio deveria ter ocorrido"
        assert estado["vendedor"]["nome"] in nomes_passeio, f"vendedor {estado['vendedor']} nao pertence a lista de PASSEIO"
        assert chamadas["mensagem"] == 2 and chamadas["template"] == 2, "handoff de passeio deveria ter ocorrido exatamente 1 vez a mais"

        # Magali continua preservada no atendimento de utilitario.
        assert estado["atendimentos"]["utilitario"]["vendedor"]["nome"] == vendedor_utilitario
        assert estado["atendimentos"]["utilitario"]["transferencia_concluida"] is True

        vendedor_passeio = estado["vendedor"]["nome"]

        # 6) "me passe o vendedor desta loja" -- sem sinal de categoria,
        # mantem PASSEIO (categoria ativa atual), sem duplicar handoff.
        estado = _passo(numero, "me passe o vendedor desta loja.")
        assert estado["categoria"] == "passeio", estado
        assert estado["vendedor"]["nome"] == vendedor_passeio
        assert chamadas["mensagem"] == 2, "nao pode duplicar handoff"

        # 7) volta a falar de van explicitamente -> recupera Magali, sem sortear outro.
        estado = _passo(numero, "ok, sobre van, mas na loja de passeios, com quem eu falo.")
        # Esta frase menciona as duas categorias de novo, mas a ULTIMA
        # mencao/contexto ("na loja de passeios, com quem eu falo") e sobre
        # PASSEIO -- deve continuar no atendimento de passeio ja aberto,
        # sem sortear outro vendedor nem reenviar.
        assert estado["categoria"] == "passeio", estado
        assert estado["vendedor"]["nome"] == vendedor_passeio
        assert chamadas["mensagem"] == 2, "nao pode reenviar handoff de passeio ja concluido"

        print("OK  Conversa real UTILITARIO -> PASSEIO (Magali -> vendedor de passeio) tratada corretamente")
    finally:
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)


def teste_categoria_por_posicao_casos_do_pedido():
    casos = [
        ("de van, ok, mas nos carros de passeio vai ser ela tambem", "passeio"),
        ("ok, sobre van, mas na loja de passeios, com quem eu falo", "passeio"),
        ("carro de passeio eu ja tenho, agora preciso de uma van", "utilitario"),
        ("passeio nao, preciso falar com alguem de utilitarios", "utilitario"),
        ("van nao, quero falar com vendedor de carro de passeio", "passeio"),
    ]
    for texto, esperado in casos:
        n = ac._normalizar(texto)
        resultado = ac._detectar_categoria_mencionada(n)
        assert resultado == esperado, f"{texto!r} -> esperado {esperado!r}, obtido {resultado!r}"
    print("OK  Categoria por posicao (Causa A) bate com todos os 5 exemplos do pedido")


def teste_sinal_transferencia_causa_b():
    positivos = [
        "me passe um desses vendedores especialistas em veiculos de passeio",
        "me passe um vendedor de passeio",
        "me passa um vendedor de passeio",
        "pode me passar um vendedor de passeio",
        "quero falar com um vendedor de passeio",
        "quem atende carros de passeio?",
        "com quem eu falo na loja de passeio?",
        "me passe pra um vendedor",
        "me passe para um vendedor",
    ]
    for msg in positivos:
        n = ac._normalizar(msg)
        assert ac._eh_sinal_transferencia(n), f"deveria reconhecer sinal de transferencia: {msg!r}"

    negativos = ["quero financiar", "tenho 50% de entrada", "quero saber o preço"]
    for msg in negativos:
        n = ac._normalizar(msg)
        assert not ac._eh_sinal_transferencia(n), f"NAO deveria transferir so por: {msg!r}"

    print("OK  Sinal de transferencia (Causa B) reconhece plural/preposicao/'quem atende', sem falsos positivos")


def teste_troca_categoria_independente_ainda_preservada():
    """Confirma mais uma vez, apos a Causa A, que UTILITARIO<->PASSEIO
    independentes continuam intactos (Fase 3.1H nao regrediu)."""
    numero = "5511900000402"
    ac.limpar_estado(numero)
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _stub_envio(monkeypatches)

        _passo(numero, "tenho interesse")
        _passo(numero, "Sprinter")
        estado = _passo(numero, "quero falar com um vendedor")
        assert estado["categoria"] == "utilitario", estado
        vendedor_util = estado["vendedor"]["nome"]

        estado = _passo(numero, "sobre veiculos de passeio, me passe um vendedor")
        assert estado["categoria"] == "passeio", estado
        vendedor_passeio = estado["vendedor"]["nome"]
        assert vendedor_passeio != vendedor_util
        assert chamadas["mensagem"] == 2

        estado = _passo(numero, "quero falar de novo com o vendedor do utilitario")
        assert estado["categoria"] == "utilitario", estado
        assert estado["vendedor"]["nome"] == vendedor_util
        assert chamadas["mensagem"] == 2, "nao pode reenviar ao voltar para categoria ja atendida"

        print("OK  UTILITARIO <-> PASSEIO independentes continuam preservados apos Causa A/B")
    finally:
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)


if __name__ == "__main__":
    teste_categoria_por_posicao_casos_do_pedido()
    teste_sinal_transferencia_causa_b()
    teste_conversa_real_utilitario_para_passeio()
    teste_troca_categoria_independente_ainda_preservada()
    print("\nTODOS OS TESTES DE REGRESSAO (FASE 3.1K) PASSARAM.")
