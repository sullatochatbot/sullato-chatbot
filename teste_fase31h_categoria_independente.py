# teste_fase31h_categoria_independente.py
"""
Testes locais da Fase 3.1H — atendimento comercial independente por
categoria (troca UTILITARIO <-> PASSEIO na mesma conversa, sem apagar o
atendimento anterior nem duplicar transferencia).

100% local: sem rede, sem WhatsApp, sem Claude/API externa, sem Google
Sheets. Envio ao vendedor e template Meta são stubados em responder.py.
Executar:  python teste_fase31h_categoria_independente.py
"""

import os
import assistente_comercial as ac
import responder


def _preparar_ambiente():
    os.environ["ASSISTENTE_COMERCIAL_ATIVO"] = "1"
    # Rodízio determinístico: sempre começa do índice 0 em cada categoria.
    responder._RODIZIO_INDICE_CATEGORIA["utilitario"] = 0
    responder._RODIZIO_INDICE_CATEGORIA["passeio"] = 0


def _stub_envio(monkeypatches, sucesso=True, chamadas=None):
    """Substitui os envios reais (WhatsApp texto + template Meta) por stubs
    que não tocam rede nenhuma, e registram quantas vezes foram chamados."""
    if chamadas is None:
        chamadas = {"mensagem": 0, "template": 0}

    def _fake_enviar_mensagem_com_status(numero, texto):
        chamadas["mensagem"] += 1
        return sucesso

    def _fake_enviar_template(*args, **kwargs):
        chamadas["template"] += 1
        return sucesso

    def _fake_enviar_mensagem(numero, texto):
        chamadas["mensagem_cliente"] = chamadas.get("mensagem_cliente", 0) + 1

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


def _qualificar_utilitario(numero):
    """Reproduz o fluxo real em 2 passos: veiculo identificado (categoria
    utilitario) e, só depois, pedido explicito de vendedor (Rota E)."""
    ac.processar_mensagem(numero, "Saiba mais")
    ac.processar_mensagem(numero, "Estou procurando uma Renault Master 2027.")
    return ac.processar_mensagem(numero, "quero falar com um vendedor")


def _qualificar_passeio(numero):
    ac.processar_mensagem(numero, "Saiba mais")
    ac.processar_mensagem(numero, "quero um carro de passeio")
    return ac.processar_mensagem(numero, "quero falar com um vendedor")


def teste_utilitario_para_passeio_novo_vendedor():
    """UTILITARIO -> vendedor utilitario; depois PASSEIO -> novo vendedor de passeio."""
    numero = "5511900000101"
    ac.limpar_estado(numero)
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _stub_envio(monkeypatches)

        # 1) Cliente trata da Renault Master (utilitário) e pede vendedor.
        estado = _qualificar_utilitario(numero)
        assert estado["categoria"] == "utilitario", estado
        assert estado["qualificado"] is True, estado

        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)
        estado = ac.obter_estado(numero)
        assert estado["vendedor"]["nome"] == "👩🏻‍💼 Magali", estado
        assert estado["transferencia_concluida"] is True
        assert chamadas["mensagem"] == 1 and chamadas["template"] == 1

        # 2) Novo assunto: passeio, carro para a filha — pedido explícito.
        estado = ac.processar_mensagem(
            numero, "outra pergunta, sobre veiculos de passeio, me passe um vendedor"
        )
        assert estado["categoria"] == "passeio", estado
        assert estado["vendedor"] is None, "vendedor do utilitario vazou para o passeio"
        assert estado["qualificado"] is True
        assert estado["transferencia_concluida"] is False

        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)
        estado = ac.obter_estado(numero)
        assert estado["vendedor"]["nome"] == "👨🏻‍💼 Alexandre", estado
        assert estado["transferencia_concluida"] is True
        assert chamadas["mensagem"] == 2 and chamadas["template"] == 2, "handoff real do passeio nao ocorreu"

        # 3) Atendimento anterior (utilitario/Magali) deve continuar preservado.
        assert estado["atendimentos"]["utilitario"]["vendedor"]["nome"] == "👩🏻‍💼 Magali"
        assert estado["atendimentos"]["utilitario"]["transferencia_concluida"] is True

        print("OK  UTILITARIO -> PASSEIO: vendedores distintos, atendimento anterior preservado")
    finally:
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)


def teste_volta_ao_utilitario_mantem_vendedor_original():
    """UTILITARIO -> PASSEIO -> volta ao UTILITARIO: mantem Magali, sem novo sorteio nem novo envio."""
    numero = "5511900000102"
    ac.limpar_estado(numero)
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _stub_envio(monkeypatches)

        estado = _qualificar_utilitario(numero)
        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)
        estado = ac.obter_estado(numero)
        vendedor_utilitario_original = estado["vendedor"]["nome"]

        estado = ac.processar_mensagem(numero, "sobre veiculos de passeio, me passe um vendedor")
        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)
        estado = ac.obter_estado(numero)
        assert chamadas["mensagem"] == 2 and chamadas["template"] == 2

        # Volta a falar do utilitario explicitamente.
        estado = ac.processar_mensagem(numero, "quero falar de novo com o vendedor do utilitario")
        assert estado["categoria"] == "utilitario", estado
        assert estado["vendedor"]["nome"] == vendedor_utilitario_original, estado
        assert estado["transferencia_concluida"] is True

        # Idempotencia: chamar de novo NAO deve reenviar nem resortear.
        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)
        assert chamadas["mensagem"] == 2 and chamadas["template"] == 2, "duplicou envio ao voltar para categoria ja atendida"
        estado_final = ac.obter_estado(numero)
        assert estado_final["vendedor"]["nome"] == vendedor_utilitario_original

        print("OK  UTILITARIO -> PASSEIO -> UTILITARIO: mantem vendedor original, sem duplicar envio")
    finally:
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)


def teste_passeio_para_utilitario_ordem_inversa():
    """PASSEIO -> UTILITARIO: cada categoria recebe o vendedor correto da sua propria lista."""
    numero = "5511900000103"
    ac.limpar_estado(numero)
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _stub_envio(monkeypatches)

        estado = _qualificar_passeio(numero)
        assert estado["categoria"] == "passeio", estado
        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)
        estado = ac.obter_estado(numero)
        assert estado["vendedor"]["nome"] == "👨🏻‍💼 Alexandre", estado

        estado = ac.processar_mensagem(numero, "quero falar com vendedor de utilitario")
        assert estado["categoria"] == "utilitario", estado
        assert estado["vendedor"] is None
        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)
        estado = ac.obter_estado(numero)
        assert estado["vendedor"]["nome"] == "👩🏻‍💼 Magali", estado

        assert estado["atendimentos"]["passeio"]["vendedor"]["nome"] == "👨🏻‍💼 Alexandre"
        assert chamadas["mensagem"] == 2 and chamadas["template"] == 2

        print("OK  PASSEIO -> UTILITARIO: vendedor correto de cada categoria (ordem inversa)")
    finally:
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)


def teste_pedido_direto_vendedor_passeio():
    """Pedido direto: 'quero falar com vendedor de passeio' apos ja qualificado no utilitario."""
    numero = "5511900000104"
    ac.limpar_estado(numero)
    _preparar_ambiente()
    monkeypatches = []
    try:
        _stub_envio(monkeypatches)

        estado = _qualificar_utilitario(numero)
        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)

        estado = ac.processar_mensagem(numero, "quero falar com vendedor de passeio")
        assert estado["categoria"] == "passeio", estado
        assert estado["vendedor"] is None
        assert estado["qualificado"] is True

        print("OK  Pedido direto 'quero falar com vendedor de passeio' troca categoria corretamente")
    finally:
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)


def teste_pedido_contextual_vendedor_passeio():
    """Pedido contextual: 'sobre veiculos de passeio, me passe um vendedor'."""
    numero = "5511900000105"
    ac.limpar_estado(numero)
    _preparar_ambiente()
    monkeypatches = []
    try:
        _stub_envio(monkeypatches)

        estado = _qualificar_utilitario(numero)
        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)

        estado = ac.processar_mensagem(numero, "sobre veiculos de passeio, me passe um vendedor")
        assert estado["categoria"] == "passeio", estado
        assert estado["vendedor"] is None

        print("OK  Pedido contextual 'sobre veiculos de passeio, me passe um vendedor' troca categoria corretamente")
    finally:
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)


def teste_prompt_ia_nao_afirma_handoff_sem_evidencia():
    """responder_ia nao pode afirmar handoff concluido sem transferencia_concluida=True,
    e nao pode atribuir vendedor de uma categoria a outra."""
    import responder_ia

    # Caso 1: vendedor presente mas transferencia NAO concluida (estado
    # inconsistente hipotetico) -> bloco de handoff NAO deve aparecer.
    contexto_sem_evidencia = {
        "ativo": True,
        "origem": "site",
        "veiculo": "Renault Master 2027",
        "categoria": "utilitario",
        "estagio": "veiculo_identificado",
        "vendedor": {"nome": "👩🏻‍💼 Magali", "link": "https://wa.me/5511940215082"},
        "transferencia_concluida": False,
    }
    prompt = responder_ia._montar_system_prompt(contexto_sem_evidencia)
    assert "TRANSFERÊNCIA JÁ REALIZADA" not in prompt, "afirmou handoff sem transferencia_concluida=True"
    assert "Magali" not in prompt, "nome do vendedor vazou no prompt sem handoff confirmado"

    # Caso 2: passeio com vendedor proprio e transferencia concluida ->
    # bloco deve aparecer, citando o vendedor CORRETO (Alexandre), nunca Magali.
    contexto_passeio_ok = {
        "ativo": True,
        "origem": "social",
        "veiculo": None,
        "categoria": "passeio",
        "estagio": "veiculo_identificado",
        "vendedor": {"nome": "👨🏻‍💼 Alexandre", "link": "https://wa.me/5511988628961"},
        "transferencia_concluida": True,
    }
    prompt2 = responder_ia._montar_system_prompt(contexto_passeio_ok)
    assert "TRANSFERÊNCIA JÁ REALIZADA" in prompt2
    assert "Alexandre" in prompt2
    assert "Magali" not in prompt2

    print("OK  responder_ia so afirma handoff concluido com transferencia_concluida=True, sem cruzar vendedor entre categorias")


def teste_gatilho_passar_vendedor():
    """Correção do residual: forma verbal 'passar' (infinitivo) deve ser
    reconhecida como sinal de transferência, junto com o que já era
    reconhecido antes ('passa'/'passe'), e sem transferir por frases
    comerciais comuns que não pedem vendedor explicitamente."""
    positivos = [
        "vc pode me passar um vendedor",
        "pode me passar um vendedor de passeio",
        "me passa um vendedor",
        "me passe um vendedor",
        "quero falar com um vendedor",
    ]
    for msg in positivos:
        texto_norm = ac._normalizar(msg)
        assert ac._eh_sinal_transferencia(texto_norm), f"deveria reconhecer sinal de transferencia: {msg!r}"

    negativos = [
        "quero financiar",
        "tenho 50% de entrada",
    ]
    for msg in negativos:
        texto_norm = ac._normalizar(msg)
        assert not ac._eh_sinal_transferencia(texto_norm), f"NAO deveria transferir so por: {msg!r}"

    print("OK  Gatilho 'passar/passa/passe um vendedor' reconhecido; falsos positivos continuam sem disparar")


if __name__ == "__main__":
    teste_utilitario_para_passeio_novo_vendedor()
    teste_volta_ao_utilitario_mantem_vendedor_original()
    teste_passeio_para_utilitario_ordem_inversa()
    teste_pedido_direto_vendedor_passeio()
    teste_pedido_contextual_vendedor_passeio()
    teste_prompt_ia_nao_afirma_handoff_sem_evidencia()
    teste_gatilho_passar_vendedor()
    print("\nTODOS OS TESTES DA FASE 3.1H PASSARAM.")
