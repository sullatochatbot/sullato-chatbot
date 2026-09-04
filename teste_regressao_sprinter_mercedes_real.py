# teste_regressao_sprinter_mercedes_real.py
"""
Teste de regressão da CONVERSA REAL (Fase 3.1J) que expôs:

1. Categoria travada em "passeio" (palpite de "Uma Mercedes") mesmo depois
   do cliente esclarecer "Sprinter escolar" (utilitário).
2. "Me passe pra um vendedor..." não reconhecido como pedido de vendedor
   (preposição "pra" entre o verbo e o objeto).
3. Menu genérico podendo sequestrar uma negociação comercial ativa.
4. Dados institucionais do Anderson (telefone/e-mail) vazando para dentro
   de uma conversa comercial.

100% local: sem rede, sem WhatsApp, sem Claude/API externa, sem Google
Sheets. Envio ao vendedor e template Meta são stubados em responder.py.
Executar:  python teste_regressao_sprinter_mercedes_real.py
"""

import os
import assistente_comercial as ac
import responder
import responder_ia


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
    """Reproduz um turno real: processa a mensagem e, se ficou qualificado
    sem vendedor, executa a transferência — igual ao que responder.py faz."""
    estado = ac.processar_mensagem(numero, texto)
    if estado and estado.get("qualificado") and not estado.get("vendedor"):
        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)
        estado = ac.obter_estado(numero)
    return estado


def teste_conversa_real_mercedes_sprinter_vendedor():
    numero = "5511900000301"
    ac.limpar_estado(numero)
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _stub_envio(monkeypatches)

        # 1) interesse genérico, sem veículo ainda.
        estado = _passo(numero, "Tenho muito interesse em adquirir um veículo")
        assert estado["categoria"] is None, estado
        assert estado["qualificado"] is False

        # 2) "Uma Mercedes" — ambíguo (Mercedes faz van E carro de passeio).
        estado = _passo(numero, "Uma Mercedes")
        assert estado["vendedor"] is None, "nao pode transferir so com 'Uma Mercedes'"
        assert chamadas["mensagem"] == 0 and chamadas["template"] == 0

        # 3) esclarecimento: Sprinter escolar -> DEVE virar utilitario, mesmo
        # depois do palpite anterior ter sido "passeio" (ou None).
        estado = _passo(numero, "Sprinter escolar")
        assert estado["categoria"] == "utilitario", f"Sprinter deveria ser UTILITARIO, veio {estado['categoria']!r}"
        assert estado["vendedor"] is None, "nao pode transferir so por identificar o veiculo"

        # 4) detalhe de capacidade — nao pode mudar a categoria nem transferir.
        estado = _passo(numero, "Tem de 30 lugares, certeza, nunca ouvi falar")
        assert estado["categoria"] == "utilitario", estado
        assert estado["vendedor"] is None

        # 5) condicao comercial (nova + entrada + financiamento) — sozinha,
        # NAO pode disparar transferencia nem mudar categoria.
        estado = _passo(numero, "Uma nova, melhor com entrada mais financiamento")
        assert estado["categoria"] == "utilitario", estado
        assert estado["vendedor"] is None, "financiamento/entrada nao podem disparar handoff sozinhos"

        # 6) nome do cliente — nao pode confundir a categoria (mesmo
        # coincidindo com o primeiro nome de uma vendedora real).
        estado = _passo(numero, "Solange Medeiros")
        assert estado["categoria"] == "utilitario", estado
        assert estado["vendedor"] is None

        # 7) pedido real de vendedor, com a preposicao "pra" que antes
        # quebrava o reconhecimento.
        estado = _passo(numero, "Me passe pra um vendedor ou vc mesmo vai me receber")
        assert estado["qualificado"] is True, "deveria ter qualificado e executado o handoff"
        assert estado["categoria"] == "utilitario", estado
        nomes_util = [n for n, _ in responder.VENDEDORES_UTIL_BASE]
        assert estado["vendedor"] is not None, "handoff deterministico nao executou"
        assert estado["vendedor"]["nome"] in nomes_util, f"vendedor {estado['vendedor']} nao pertence a lista de UTILITARIOS"
        assert estado["vendedor"]["nome"] != "👨🏻‍💼 Jeferson", "Jeferson e exclusivamente PASSEIO"
        assert chamadas["mensagem"] == 1 and chamadas["template"] == 1, "handoff deveria ocorrer exatamente 1 vez"

        # Repetir a mesma mensagem (idempotencia) nao pode duplicar handoff.
        estado2 = _passo(numero, "Me passe pra um vendedor ou vc mesmo vai me receber")
        assert chamadas["mensagem"] == 1 and chamadas["template"] == 1, "nao pode duplicar handoff"
        assert estado2["vendedor"]["nome"] == estado["vendedor"]["nome"]

        # Nenhum prompt gerado durante toda a conversa pode conter os dados
        # institucionais do Anderson.
        prompt_final = responder_ia._montar_system_prompt(estado, "Me passe pra um vendedor ou vc mesmo vai me receber")
        assert "98878" not in prompt_final, "telefone do Anderson vazou no prompt comercial"
        assert "anderson@sullato.com.br" not in prompt_final, "email do Anderson vazou no prompt comercial"
        assert "Jeferson" not in prompt_final, "Jeferson (passeio) nao pode aparecer numa conversa de utilitario"

        print("OK  Conversa real (Mercedes -> Sprinter escolar -> ... -> pedido de vendedor com 'pra') tratada corretamente")
    finally:
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)


def teste_reclassificacao_nao_reabre_atendimento_ja_transferido():
    """Depois que o handoff JA ocorreu (qualificado + vendedor setado), uma
    nova descricao de veiculo nao pode mais mudar a categoria por conta
    propria — isso e' responsabilidade exclusiva da troca de categoria
    (Fase 3.1H, que exige sinal de transferencia explicito)."""
    numero = "5511900000302"
    ac.limpar_estado(numero)
    _preparar_ambiente()
    monkeypatches = []
    try:
        _stub_envio(monkeypatches)

        ac.processar_mensagem(numero, "tenho interesse")
        ac.processar_mensagem(numero, "Master 2020")
        estado = _passo(numero, "quero falar com um vendedor")
        assert estado["categoria"] == "utilitario", estado
        assert estado["vendedor"] is not None

        # Mencionar "carro" agora, SEM pedir vendedor, nao deve mexer em nada
        # (o atendimento ja foi concluido para utilitario).
        estado2 = ac.processar_mensagem(numero, "e voces tem carro de passeio tambem?")
        assert estado2["categoria"] == "utilitario", estado2
        assert estado2["vendedor"]["nome"] == estado["vendedor"]["nome"]

        print("OK  Reclassificacao nao mexe em atendimento ja transferido/qualificado")
    finally:
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)


def teste_troca_categoria_independente_preservada():
    """Confirma que a Fase 3.1H (atendimentos independentes por categoria,
    UTILITARIO <-> PASSEIO) continua intacta apos as mudancas da Fase 3.1J."""
    numero = "5511900000303"
    ac.limpar_estado(numero)
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _stub_envio(monkeypatches)

        ac.processar_mensagem(numero, "tenho interesse")
        ac.processar_mensagem(numero, "Sprinter")
        estado = _passo(numero, "quero falar com um vendedor")
        assert estado["categoria"] == "utilitario", estado
        vendedor_util = estado["vendedor"]["nome"]
        assert chamadas["mensagem"] == 1

        estado = ac.processar_mensagem(numero, "na verdade, sobre veiculo de passeio, me passa um vendedor")
        assert estado["categoria"] == "passeio", estado
        assert estado["vendedor"] is None
        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)
        estado = ac.obter_estado(numero)
        vendedor_passeio = estado["vendedor"]["nome"]
        assert vendedor_passeio != vendedor_util
        assert chamadas["mensagem"] == 2

        estado = ac.processar_mensagem(numero, "voltando pro utilitario, me passa o vendedor de novo")
        assert estado["categoria"] == "utilitario", estado
        assert estado["vendedor"]["nome"] == vendedor_util, "deveria recuperar o vendedor original, sem novo sorteio"
        assert chamadas["mensagem"] == 2, "nao pode reenviar ao voltar para categoria ja atendida"

        print("OK  UTILITARIO -> PASSEIO -> UTILITARIO continua preservado apos Fase 3.1J")
    finally:
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)


def teste_menu_nao_sequestra_contexto_comercial_ativo():
    """Fase 3.1J (item 3): com contexto comercial ativo, uma mensagem que
    contem palavra de gatilho de menu (ex.: 'ajuda') nao pode ser tratada
    como saudacao/menu generico."""
    import assistente_comercial

    numero = "5511900000304"
    ac.limpar_estado(numero)
    _preparar_ambiente()
    ac.processar_mensagem(numero, "tenho interesse")
    ac.processar_mensagem(numero, "Sprinter")

    saudacao_com_sinal = False
    if assistente_comercial.assistente_comercial_ativo() and (
        assistente_comercial.contem_sinal_comercial("preciso de ajuda para decidir o modelo")
        or assistente_comercial.tem_contexto_comercial(numero)
    ):
        saudacao_com_sinal = True

    assert saudacao_com_sinal is True, (
        "com contexto comercial ativo, mensagem contendo 'ajuda' nao deveria "
        "poder sequestrar a conversa para o menu generico"
    )
    ac.limpar_estado(numero)
    print("OK  Gate do menu respeita contexto comercial ativo (item 3)")


def teste_dados_institucionais_isolados():
    """Fase 3.1J (item 4) + Fase 3.1M (confirmado por Anderson): dados do
    Anderson so aparecem com intencao explicita de perguntar sobre o
    criador — independente de haver ou nao contexto comercial ativo (a
    Fase 3.1J chegou a bloquear isso por completo durante negociacao
    comercial; a Fase 3.1M relaxou essa restricao a pedido explicito,
    confirmando que a resposta institucional deve continuar funcionando no
    meio de uma negociacao, sem interferir em categoria/vendedor)."""
    # Sem contexto comercial, sem intencao de perguntar sobre o criador.
    prompt = responder_ia._montar_system_prompt(None, "quero comprar um carro")
    assert "98878" not in prompt and "anderson@sullato.com.br" not in prompt

    # Sem contexto comercial, COM intencao explicita -> deve aparecer.
    prompt = responder_ia._montar_system_prompt(None, "quem criou esse chatbot?")
    assert "98878" in prompt and "anderson@sullato.com.br" in prompt

    for pergunta in [
        "quem desenvolveu este sistema",
        "quem fez esse chatbot",
        "quem criou essa inteligencia",
        "como faco para ter um chatbot assim",
        "quero contratar um sistema semelhante",
    ]:
        p = responder_ia._montar_system_prompt(None, pergunta)
        assert "anderson@sullato.com.br" in p, f"deveria reconhecer intencao institucional em: {pergunta!r}"

    # COM contexto comercial ativo, SEM intencao institucional -> nao aparece.
    contexto_comercial_ativo = {
        "ativo": True, "categoria": "utilitario", "veiculo": "Sprinter",
        "vendedor": {"nome": "Vendedor Teste U", "link": "https://wa.me/5511900000000"},
        "transferencia_concluida": True,
    }
    prompt = responder_ia._montar_system_prompt(contexto_comercial_ativo, "quero saber mais sobre a sprinter")
    assert "98878" not in prompt and "anderson@sullato.com.br" not in prompt

    # COM contexto comercial ativo, COM intencao institucional explicita ->
    # DEVE aparecer (Fase 3.1M), e o vendedor comercial continua presente e
    # intacto — os dois contextos coexistem sem se contaminar.
    prompt = responder_ia._montar_system_prompt(contexto_comercial_ativo, "quem criou esse chatbot?")
    assert "98878" in prompt and "anderson@sullato.com.br" in prompt, (
        "resposta institucional deve continuar funcionando mesmo com negociacao comercial ativa (Fase 3.1M)"
    )
    assert "Vendedor Teste U" in prompt, "vendedor comercial nao pode sumir do prompt so por causa da pergunta institucional"

    print("OK  Dados institucionais do Anderson: aparecem so com intencao explicita, com ou sem contexto comercial ativo (Fase 3.1M)")


if __name__ == "__main__":
    teste_conversa_real_mercedes_sprinter_vendedor()
    teste_reclassificacao_nao_reabre_atendimento_ja_transferido()
    teste_troca_categoria_independente_preservada()
    teste_menu_nao_sequestra_contexto_comercial_ativo()
    teste_dados_institucionais_isolados()
    print("\nTODOS OS TESTES DE REGRESSAO (FASE 3.1J) PASSARAM.")
