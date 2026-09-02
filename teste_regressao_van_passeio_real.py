# teste_regressao_van_passeio_real.py
"""
Teste de regressão da CONVERSA REAL pós-deploy (Fase 3.1I) que expôs 3 bugs:

1. "vans" mencionado na 1a mensagem não classificava como utilitário
   (branch de pedido de vendedor sem sessão prévia só olhava domínio/loja).
2. Fallback silencioso "categoria = ... or 'passeio'" podia mandar o
   cliente para o vendedor errado quando a categoria ainda era desconhecida.
3. Troca de categoria UTILITARIO -> PASSEIO não executava novo handoff
   porque a frase real ("vc pode pedir pra um vendedor me chamar e passar
   o contato dele") não era reconhecida como sinal de transferência.
4. A IA podia afirmar que um vendedor atende as duas categorias.

100% local: sem rede, sem WhatsApp, sem Claude/API externa, sem Google
Sheets. Envio ao vendedor e template Meta são stubados em responder.py.
Executar:  python teste_regressao_van_passeio_real.py
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

    def _fake_enviar_mensagem(numero, texto):
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


def _passo(numero, texto, estado_anterior_vendedor_setado=False):
    """Reproduz um turno real: processa a mensagem e, se ficou qualificado
    sem vendedor, executa a transferência — igual ao que responder.py faz."""
    estado = ac.processar_mensagem(numero, texto)
    if estado and estado.get("qualificado") and not estado.get("vendedor"):
        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)
        estado = ac.obter_estado(numero)
    return estado


def teste_conversa_real_van_para_passeio_e_volta():
    numero = "5511900000201"
    ac.limpar_estado(numero)
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _stub_envio(monkeypatches)

        # 1) "ola, queria falar sobre vans, quem pode me atender."
        estado = _passo(numero, "ola, queria falar sobre vans, quem pode me atender.")
        assert estado["categoria"] == "utilitario", estado
        assert estado["vendedor"]["nome"] == "👩🏻‍💼 Magali", estado
        assert estado["vendedor"]["nome"] not in ("👨🏻‍💼 Alexandre",), "Alexandre (passeio) nao pode receber lead de van"

        # 2) pedido de consultor para transporte de passageiros interestadual.
        estado = _passo(
            numero,
            "pra transporte de passageiros interestadual, vc pode me passar um "
            "consultor pra eu falar com ele ou ele ou ela me chamar.",
        )
        assert estado["categoria"] == "utilitario", estado
        nomes_util = [n for n, _ in responder.VENDEDORES_UTIL_BASE]
        assert estado["vendedor"]["nome"] in nomes_util, estado
        assert chamadas["mensagem"] == 1 and chamadas["template"] == 1, "nao pode duplicar handoff so por reforcar o mesmo pedido"

        # 3) agradecimento — NAO pode reabrir qualificacao nem resetar nada.
        estado = _passo(numero, "otimo, obg")
        assert estado["categoria"] == "utilitario", estado
        assert estado["vendedor"]["nome"] in nomes_util, estado
        assert estado["qualificado"] is True and estado["transferencia_concluida"] is True
        assert chamadas["mensagem"] == 1 and chamadas["template"] == 1, "agradecimento nao pode gerar novo handoff"
        prompt_pos_obrigado = responder_ia._montar_system_prompt(estado)
        assert "NÃO faça nenhuma pergunta de qualificação" in prompt_pos_obrigado, \
            "prompt deveria instruir a IA a nao reabrir qualificacao apos agradecimento"

        # 4) troca explicita para passeio, pedindo vendedor.
        estado = _passo(
            numero,
            "tenho interesse de comprar um veiculo de passeio pra minha filha, "
            "vc pode pedir pra um vendedor me chamar e passar o contato dele.",
        )
        assert estado["categoria"] == "passeio", estado
        nomes_passeio = [n for n, _ in responder.VENDEDORES_PASSEIO_BASE]
        assert estado["vendedor"]["nome"] in nomes_passeio, estado
        assert chamadas["mensagem"] == 2 and chamadas["template"] == 2, "handoff do passeio nao ocorreu"
        vendedor_passeio_1 = estado["vendedor"]["nome"]

        # 5) segue no passeio — mantem o MESMO vendedor, sem duplicar.
        estado = _passo(numero, "um carro pequeno, mas me passe um vendedor pra eu falar com ele ou ele me chamar.")
        assert estado["categoria"] == "passeio", estado
        assert estado["vendedor"]["nome"] == vendedor_passeio_1, "nao pode trocar de vendedor de passeio sem pedido de categoria diferente"
        assert chamadas["mensagem"] == 2 and chamadas["template"] == 2, "nao pode duplicar handoff do passeio"

        # 6) volta a falar da van — recupera o vendedor original, sem sortear outro.
        estado = _passo(numero, "voltando a falar da van, pode me passar o vendedor de novo?")
        assert estado["categoria"] == "utilitario", estado
        assert estado["vendedor"]["nome"] in nomes_util, estado
        assert chamadas["mensagem"] == 2 and chamadas["template"] == 2, "volta a categoria ja atendida nao pode reenviar"

        # prompt final: regra anti-invencao de atribuicao de vendedor deve estar presente.
        prompt_final = responder_ia._montar_system_prompt(estado)
        assert "NUNCA afirme ou sugira que um vendedor atende uma categoria" in prompt_final

        print("OK  Conversa real (van -> consultor -> obrigado -> passeio -> volta a van) tratada corretamente")
    finally:
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)


def teste_categorizacao_isolada_secao_8():
    casos_utilitario = [
        "quero falar com vendedor de van",
        "quero uma Master e quero falar com vendedor",
    ]
    casos_passeio = [
        "quero falar com vendedor de passeio",
        "quero um carro pequeno e falar com vendedor",
    ]

    for msg in casos_utilitario:
        numero = f"55119{abs(hash(msg)) % 10**7:07d}"
        ac.limpar_estado(numero)
        estado = ac.processar_mensagem(numero, msg)
        assert estado and estado.get("categoria") == "utilitario", (msg, estado)
        ac.limpar_estado(numero)

    for msg in casos_passeio:
        numero = f"55119{abs(hash(msg)) % 10**7:07d}"
        ac.limpar_estado(numero)
        estado = ac.processar_mensagem(numero, msg)
        assert estado and estado.get("categoria") == "passeio", (msg, estado)
        ac.limpar_estado(numero)

    # Sem contexto suficiente: NAO pode assumir passeio; deve pedir categoria.
    numero = "5511900000210"
    ac.limpar_estado(numero)
    estado = ac.processar_mensagem(numero, "quero falar com vendedor")
    assert estado is not None, estado
    assert estado.get("categoria") is None, f"nao deveria assumir categoria sem contexto: {estado}"
    assert estado.get("qualificado") is False, f"nao deveria qualificar sem saber a categoria: {estado}"
    assert estado.get("estagio") == "aguardando_veiculo", estado
    ac.limpar_estado(numero)

    # "quero financiar" / "tenho 50% de entrada" isolados nao devem disparar transferencia.
    for msg in ("quero financiar", "tenho 50% de entrada"):
        numero = f"55119{abs(hash(msg)) % 10**7:07d}"
        ac.limpar_estado(numero)
        estado = ac.processar_mensagem(numero, msg)
        assert estado is None, f"nao deveria criar/qualificar sessao comercial so por: {msg!r} -> {estado}"

    print("OK  Testes adicionais da secao 8: categorizacao van/passeio e nao-transferencia por financiamento/entrada")


def teste_fallback_categoria_desconhecida_nao_transfere():
    """Rede de seguranca final: mesmo que um estado 'qualificado' sem
    categoria chegasse (nao deveria mais acontecer), _processar_transferencia_vendedor
    NUNCA pode escolher passeio por padrao."""
    numero = "5511900000211"
    ac.limpar_estado(numero)
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _stub_envio(monkeypatches)
        estado_hipotetico_inconsistente = {
            "numero": numero, "ativo": True, "categoria": None, "qualificado": True,
            "vendedor": None, "transferencia_concluida": False, "veiculo": None,
            "url": None, "origem": None, "data_visita": None, "horario_visita": None,
            "intencao_visita": "quero falar com vendedor",
        }
        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado_hipotetico_inconsistente)
        assert chamadas["mensagem"] == 0 and chamadas["template"] == 0, \
            "nao deveria transferir (nem escolher passeio) sem categoria conhecida"
        print("OK  Fail-safe: categoria desconhecida nunca vira transferencia para PASSEIO por padrao")
    finally:
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)


if __name__ == "__main__":
    teste_conversa_real_van_para_passeio_e_volta()
    teste_categorizacao_isolada_secao_8()
    teste_fallback_categoria_desconhecida_nao_transfere()
    print("\nTODOS OS TESTES DE REGRESSAO DA CONVERSA REAL PASSARAM.")
