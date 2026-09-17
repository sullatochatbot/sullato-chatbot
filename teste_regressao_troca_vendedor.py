# teste_regressao_troca_vendedor.py
"""
Teste de regressão da Fase 3.1R (diagnóstico real: cliente com Magali já
atribuída pediu "me passa o dado de outro" e o sistema respondeu com uma
alucinação da IA em vez de trocar de vendedor).

Cobre: pedido EXPLÍCITO de outro vendedor (decisão 100% determinística do
backend, nunca da IA), exclusão só do vendedor recém-recusado, preservação
de categoria/veículo/visita, rodízio normal intacto para leads novos, troca
de categoria (Fase 3.1H) e mudança de visita (Fase 3.1F) continuando
intactas, e nenhum segundo POST de texto livre quando o template é aceito
(correção anterior, commit 5c62933 — não pode regredir).

100% local: sem rede, sem WhatsApp, sem Claude/API externa, sem Google
Sheets. Envio ao vendedor e ao cliente são stubados em responder.py.
Executar:  python teste_regressao_troca_vendedor.py
"""

import os
import assistente_comercial as ac
import responder


def _preparar_ambiente():
    os.environ["ASSISTENTE_COMERCIAL_ATIVO"] = "1"
    # Fase 3.1V: seleção agora é random.choice() puro, sem índice/rodízio.
    # Mock determinístico (sempre o 1º elegível) só para este teste poder
    # afirmar QUAL vendedor foi escolhido — o sorteio real de produção é
    # coberto por teste_regressao_selecao_randomica_vendedor.py.
    responder.random.choice = lambda seq: seq[0]


def _stub_envio(monkeypatches):
    """Substitui os envios reais (WhatsApp texto + template Meta, ao
    vendedor e ao cliente) por stubs que não tocam rede nenhuma."""
    chamadas = {"mensagem": 0, "template": 0, "template_args": [], "cliente": []}

    def _fake_enviar_mensagem_com_status(numero, texto):
        chamadas["mensagem"] += 1
        return True

    def _fake_enviar_template(numero_vendedor, nome_cliente, telefone_cliente, veiculo, resumo, visita_texto):
        chamadas["template"] += 1
        chamadas["template_args"].append({"numero_vendedor": numero_vendedor, "nome_cliente": nome_cliente})
        return True

    def _fake_enviar_mensagem(numero, texto, sender_phone_number_id=None):
        chamadas["cliente"].append(texto)

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
    ac.processar_mensagem(numero, "Saiba mais")
    ac.processar_mensagem(numero, "Estou procurando uma Renault Master 2027.")
    return ac.processar_mensagem(numero, "quero falar com um vendedor")


# ============================================================
# A) Lead novo -> rodízio normal continua igual (sem exclusão nenhuma)
# ============================================================
def teste_A_rodizio_normal_sem_regressao():
    numero = "5511900001001"
    ac.limpar_estado(numero)
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _stub_envio(monkeypatches)
        estado = _qualificar_utilitario(numero)
        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)
        estado = ac.obter_estado(numero)
        assert estado["vendedor"]["nome"] == "👩🏻‍💼 Magali", estado
        assert chamadas["template"] == 1 and chamadas["mensagem"] == 0
        print("OK  A) Lead novo -> seleção normal (Magali, via mock determinístico) continua igual, sem exclusão")
    finally:
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)


# ============================================================
# B/C/D) Pedido explícito de outro vendedor, em 3 formas diferentes
# ============================================================
def _cenario_troca(numero, frase_troca, rotulo):
    ac.limpar_estado(numero)
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _stub_envio(monkeypatches)
        estado = _qualificar_utilitario(numero)
        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)
        estado = ac.obter_estado(numero)
        vendedor_original = estado["vendedor"]["nome"]
        assert vendedor_original == "👩🏻‍💼 Magali", estado
        veiculo_antes = estado["veiculo"]

        estado = ac.processar_mensagem(numero, frase_troca)
        assert estado["vendedor"] is None, f"{rotulo}: deveria estar aguardando nova seleção"
        assert estado["troca_vendedor_pendente"] is True, f"{rotulo}: sinal de troca pendente ausente"
        assert estado["vendedor_excluido_na_troca"]["nome"] == vendedor_original, rotulo
        assert estado["categoria"] == "utilitario", f"{rotulo}: categoria não pode mudar"
        assert estado["veiculo"] == veiculo_antes, f"{rotulo}: veículo não pode se perder"

        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)
        estado = ac.obter_estado(numero)

        assert estado["vendedor"] is not None, f"{rotulo}: novo vendedor não foi atribuído"
        assert estado["vendedor"]["nome"] != vendedor_original, f"{rotulo}: repetiu o vendedor recusado"
        assert estado["transferencia_concluida"] is True
        assert estado["troca_vendedor_pendente"] is False, f"{rotulo}: sinal de troca não foi limpo"
        assert estado["vendedor_excluido_na_troca"] is None
        assert estado["categoria"] == "utilitario"
        assert estado["veiculo"] == veiculo_antes

        # G) exatamente 1 template a mais (o da troca), zero texto livre.
        assert chamadas["template"] == 2 and chamadas["mensagem"] == 0, (
            f"{rotulo}: deveria ter só 1 template a mais na troca, sem texto livre — chamadas={chamadas}"
        )

        # H) cliente recebeu o contato do NOVO vendedor (não o antigo).
        assert chamadas["cliente"], f"{rotulo}: cliente não recebeu nenhuma mensagem"
        assert estado["vendedor"]["nome"] in chamadas["cliente"][-1], chamadas["cliente"][-1]
        assert vendedor_original not in chamadas["cliente"][-1]

        print(f"OK  {rotulo}) '{frase_troca}' troca vendedor corretamente, sem repetir {vendedor_original}")
    finally:
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)


def teste_B_quero_outro_vendedor():
    _cenario_troca("5511900001002", "quero outro vendedor", "B")


def teste_C_me_passa_o_dado_de_outro():
    _cenario_troca("5511900001003", "me passa o dado de outro", "C")


def teste_D_nao_quero_falar_com_a_magali():
    _cenario_troca("5511900001004", "nao quero falar com a Magali", "D")


# ============================================================
# E) Troca não perde veículo/visita/demais dados já coletados
# ============================================================
def teste_E_preserva_veiculo_visita_apos_troca():
    numero = "5511900001005"
    ac.limpar_estado(numero)
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _stub_envio(monkeypatches)
        estado = _qualificar_utilitario(numero)
        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)
        estado = ac.obter_estado(numero)
        veiculo_antes = estado["veiculo"]
        categoria_antes = estado["categoria"]

        chave = ac._chave_estado(numero)
        estado["data_visita"] = "quinta"
        estado["horario_visita"] = "manha"
        ac._ESTADOS[chave] = estado

        estado = ac.processar_mensagem(numero, "quero outro vendedor")
        assert estado["veiculo"] == veiculo_antes
        assert estado["categoria"] == categoria_antes
        assert estado["data_visita"] == "quinta"
        assert estado["horario_visita"] == "manha"

        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)
        estado = ac.obter_estado(numero)
        assert estado["veiculo"] == veiculo_antes
        assert estado["data_visita"] == "quinta"
        assert estado["horario_visita"] == "manha"

        print("OK  E) Troca de vendedor preserva veículo/visita/categoria já coletados")
    finally:
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)


# ============================================================
# F) Trocas sucessivas nunca repetem o vendedor IMEDIATAMENTE anterior
# ============================================================
def teste_F_troca_nunca_repete_vendedor_imediatamente_anterior():
    """
    Fase 3.1V (seleção randômica pura): a garantia oficial é só "nunca
    devolver IMEDIATAMENTE quem acabou de ser recusado" (exclusão de um
    único nome por vez, ver _vendedor_da_vez). Isso é diferente da garantia
    mais forte que o antigo rodízio sequencial dava de graça (nunca repetir
    NENHUM vendedor já visto na conversa inteira) — com sorteio aleatório
    real, voltar a um vendedor de 2+ trocas atrás é possível e correto (só
    o passo IMEDIATO é protegido). Este teste prova exatamente essa garantia
    real, passo a passo, em duas trocas sucessivas.
    """
    numero = "5511900001006"
    ac.limpar_estado(numero)
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _stub_envio(monkeypatches)
        estado = _qualificar_utilitario(numero)
        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)
        estado = ac.obter_estado(numero)
        vendedor_anterior = estado["vendedor"]["nome"]

        for _ in range(2):
            estado = ac.processar_mensagem(numero, "quero outro vendedor")
            responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)
            estado = ac.obter_estado(numero)
            assert estado["vendedor"]["nome"] != vendedor_anterior, (
                f"troca devolveu imediatamente o vendedor recusado: {vendedor_anterior}"
            )
            vendedor_anterior = estado["vendedor"]["nome"]

        print("OK  F) Cada troca sucessiva nunca devolve imediatamente o vendedor recém-recusado")
    finally:
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)


# ============================================================
# I) Único vendedor elegível -> não entra em loop nem inventa outro
# ============================================================
def teste_I_unico_vendedor_elegivel_nao_troca_nao_inventa():
    numero = "5511900001007"
    ac.limpar_estado(numero)
    _preparar_ambiente()
    monkeypatches = []
    lista_original = list(responder.VENDEDORES_UTIL_BASE)
    try:
        # Simula categoria com só 1 vendedor elegível -- muta a MESMA lista
        # em memória (nunca cria lista paralela), restaurada no finally.
        responder.VENDEDORES_UTIL_BASE.clear()
        responder.VENDEDORES_UTIL_BASE.append(lista_original[0])

        chamadas = _stub_envio(monkeypatches)
        estado = _qualificar_utilitario(numero)
        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)
        estado = ac.obter_estado(numero)
        vendedor_unico = estado["vendedor"]["nome"]
        assert chamadas["template"] == 1

        estado = ac.processar_mensagem(numero, "quero outro vendedor")
        assert estado["vendedor"] is None and estado["troca_vendedor_pendente"] is True

        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)
        estado = ac.obter_estado(numero)

        assert estado["vendedor"]["nome"] == vendedor_unico, "não pode inventar outro vendedor"
        assert estado["transferencia_concluida"] is True
        assert estado["troca_vendedor_pendente"] is False
        assert estado["vendedor_excluido_na_troca"] is None

        # Não reenvia template/texto livre ao vendedor (ele já está
        # cuidando do cliente) -- só a mensagem objetiva ao cliente.
        assert chamadas["template"] == 1, "não deveria reenviar template ao único vendedor"
        assert chamadas["mensagem"] == 0
        assert chamadas["cliente"], "cliente deveria receber uma resposta objetiva"
        assert vendedor_unico in chamadas["cliente"][-1]

        print(f"OK  I) Único vendedor elegível ({vendedor_unico}) -- preserva, não inventa, sem loop")
    finally:
        responder.VENDEDORES_UTIL_BASE.clear()
        responder.VENDEDORES_UTIL_BASE.extend(lista_original)
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)


# ============================================================
# J) Troca de categoria (Fase 3.1H) continua funcionando
# ============================================================
def teste_J_troca_categoria_ainda_funciona_com_novos_campos():
    numero = "5511900001008"
    ac.limpar_estado(numero)
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _stub_envio(monkeypatches)
        estado = _qualificar_utilitario(numero)
        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)

        estado = ac.processar_mensagem(numero, "sobre veiculos de passeio, me passe um vendedor")
        assert estado["categoria"] == "passeio", estado
        assert estado["vendedor"] is None
        assert estado["troca_vendedor_pendente"] is False
        assert estado["vendedor_excluido_na_troca"] is None

        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)
        estado = ac.obter_estado(numero)
        assert estado["vendedor"]["nome"] in [n for n, _ in responder.VENDEDORES_PASSEIO_BASE]
        assert estado["atendimentos"]["utilitario"]["vendedor"] is not None

        print("OK  J) Troca de categoria (Fase 3.1H) continua funcionando com os novos campos de troca de vendedor")
    finally:
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)


# ============================================================
# K) Mudança de dia/período de visita (Fase 3.1F) continua funcionando
# ============================================================
def teste_K_mudanca_visita_ainda_funciona():
    numero = "5511900001009"
    ac.limpar_estado(numero)
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _stub_envio(monkeypatches)
        estado = _qualificar_utilitario(numero)
        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)
        estado = ac.obter_estado(numero)
        vendedor_antes = estado["vendedor"]["nome"]

        chave = ac._chave_estado(numero)
        estado["data_visita"] = "quarta"
        estado["horario_visita"] = "tarde"
        ac._ESTADOS[chave] = estado

        estado = ac.processar_mensagem(numero, "prefiro mudar para quinta de manha")
        assert estado is not None
        assert estado["vendedor"]["nome"] == vendedor_antes, "mudança de visita não pode mexer no vendedor"
        assert estado["transferencia_concluida"] is True

        print("OK  K) Mudança de dia/período de visita (Fase 3.1F) continua funcionando, sem mexer no vendedor")
    finally:
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)


# ============================================================
# L) Conversa institucional continua funcionando com os novos campos
# ============================================================
def teste_L_institucional_convive_com_novos_campos():
    import responder_ia

    contexto = {
        "ativo": True,
        "categoria": "utilitario",
        "veiculo": "Master",
        "vendedor": {"nome": "👩🏻‍💼 Magali", "link": "https://wa.me/5511940215082"},
        "transferencia_concluida": True,
        "troca_vendedor_pendente": False,
        "vendedor_excluido_na_troca": None,
    }
    prompt = responder_ia._montar_system_prompt(contexto, "quem criou esse chatbot?")
    assert "98878" in prompt and "anderson@sullato.com.br" in prompt
    assert "Magali" in prompt
    print("OK  L) Resposta institucional continua funcionando com os novos campos de estado presentes")


if __name__ == "__main__":
    teste_A_rodizio_normal_sem_regressao()
    teste_B_quero_outro_vendedor()
    teste_C_me_passa_o_dado_de_outro()
    teste_D_nao_quero_falar_com_a_magali()
    teste_E_preserva_veiculo_visita_apos_troca()
    teste_F_troca_nunca_repete_vendedor_imediatamente_anterior()
    teste_I_unico_vendedor_elegivel_nao_troca_nao_inventa()
    teste_J_troca_categoria_ainda_funciona_com_novos_campos()
    teste_K_mudanca_visita_ainda_funciona()
    teste_L_institucional_convive_com_novos_campos()
    print("\nTODOS OS TESTES DE REGRESSÃO (FASE 3.1R - TROCA DE VENDEDOR) PASSARAM. ZERO mensagens reais enviadas.")
