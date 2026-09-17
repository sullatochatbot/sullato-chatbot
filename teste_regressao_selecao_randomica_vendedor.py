# teste_regressao_selecao_randomica_vendedor.py
"""
Teste de regressão da Fase 3.1V — regra oficial do Grupo Sullato:
SELEÇÃO RANDÔMICA PURA por categoria (não rodízio sequencial, não índice,
não persistência entre restarts/deploys).

Contexto: a tentativa anterior (Fase 3.1U) de tornar o rodízio sequencial
persistente entre restarts foi descartada — Anderson definiu que a regra
correta nunca foi rodízio sequencial, e sim sorteio aleatório puro entre
os vendedores elegíveis da categoria, com exclusão apenas do vendedor
IMEDIATAMENTE recusado numa troca explícita. _RODIZIO_INDICE_CATEGORIA e
_avancar_rodizio foram removidos por completo de responder.py.

Cobre: seleção só entre vendedores da categoria correta (nunca mistura
utilitário com passeio), uso real de random.choice() (provado mockando-o),
exclusão correta na troca explícita, ausência de qualquer favorecimento
do primeiro vendedor da lista após "restart" (não há mais índice para
resetar), rodízio compartilhado entre os dois phone_number_id, e handoff
continuando normal.

100% local, ZERO rede: requests.post bloqueado explicitamente; envio ao
vendedor/cliente sempre mockado.

Executar:  python teste_regressao_selecao_randomica_vendedor.py
"""

import os
import requests
import responder

os.environ["ASSISTENTE_COMERCIAL_ATIVO"] = "1"

NOMES_UTIL = [n for n, _ in responder.VENDEDORES_UTIL_BASE]
NOMES_PASSEIO = [n for n, _ in responder.VENDEDORES_PASSEIO_BASE]


def _bloquear_rede():
    def _post_bloqueado(*args, **kwargs):
        raise AssertionError(f"BLOQUEADO: requests.post real chamado com args={args} kwargs={kwargs}")
    requests.post = _post_bloqueado


def _mockar_envio_vendedor(monkeypatches):
    def _fake_template(*a, **k):
        return True

    def _fake_texto(numero, texto):
        return True

    def _fake_enviar_mensagem(numero, texto, sender_phone_number_id=None):
        pass

    original_tpl = responder._enviar_template_novo_lead_vendedor
    original_txt = responder._enviar_mensagem_com_status
    original_cli = responder.enviar_mensagem
    responder._enviar_template_novo_lead_vendedor = _fake_template
    responder._enviar_mensagem_com_status = _fake_texto
    responder.enviar_mensagem = _fake_enviar_mensagem
    monkeypatches.append((responder, "_enviar_template_novo_lead_vendedor", original_tpl))
    monkeypatches.append((responder, "_enviar_mensagem_com_status", original_txt))
    monkeypatches.append((responder, "enviar_mensagem", original_cli))


def _restaurar(monkeypatches):
    for obj, nome, original in monkeypatches:
        setattr(obj, nome, original)


def _estado_qualificado(categoria="utilitario", vendedor=None, transferencia_concluida=False):
    return {
        "ativo": True,
        "qualificado": True,
        "categoria": categoria,
        "veiculo": "Renault Master 2027",
        "vendedor": vendedor,
        "transferencia_concluida": transferencia_concluida,
        "vendedor_excluido_na_troca": None,
        "atendimentos": {},
    }


# ============================================================
# A) Utilitário: em múltiplos sorteios, só Magali/Silvano/Solange aparecem
# ============================================================
def teste_A_utilitario_so_vendedores_cadastrados():
    vistos = set()
    for _ in range(200):
        vendedor = responder._vendedor_da_vez("utilitario")
        assert vendedor[0] in NOMES_UTIL, f"vendedor fora da lista de utilitário: {vendedor}"
        vistos.add(vendedor[0])
    assert vistos == set(NOMES_UTIL), f"nem todos os vendedores de utilitário apareceram em 200 sorteios: {vistos}"
    print(f"OK  A) 200 sorteios de utilitário -> só {sorted(vistos)} apareceram (todos e só os cadastrados)")


# ============================================================
# B) Passeio: só vendedores cadastrados em VENDEDORES_PASSEIO_BASE
# ============================================================
def teste_B_passeio_so_vendedores_cadastrados():
    vistos = set()
    for _ in range(200):
        vendedor = responder._vendedor_da_vez("passeio")
        assert vendedor[0] in NOMES_PASSEIO, f"vendedor fora da lista de passeio: {vendedor}"
        vistos.add(vendedor[0])
    assert vistos == set(NOMES_PASSEIO), f"nem todos os vendedores de passeio apareceram em 200 sorteios: {vistos}"
    print(f"OK  B) 200 sorteios de passeio -> só {sorted(vistos)} apareceram (todos e só os cadastrados)")


# ============================================================
# C) Nunca mistura vendedor de passeio com utilitário e vice-versa
# ============================================================
def teste_C_nunca_mistura_categorias():
    for _ in range(200):
        v_util = responder._vendedor_da_vez("utilitario")
        v_passeio = responder._vendedor_da_vez("passeio")
        assert v_util[0] not in NOMES_PASSEIO, f"vendedor de utilitário vazou para passeio: {v_util}"
        assert v_passeio[0] not in NOMES_UTIL, f"vendedor de passeio vazou para utilitário: {v_passeio}"
    print("OK  C) 200 pares de sorteios -> nunca houve mistura entre categorias")


# ============================================================
# D/E) Troca: resultado nunca pode ser o vendedor excluído
# ============================================================
def teste_D_troca_magali_nunca_retorna_magali():
    for _ in range(200):
        vendedor = responder._vendedor_da_vez("utilitario", excluir_nome="👩🏻‍💼 Magali")
        assert vendedor[0] != "👩🏻‍💼 Magali", "troca excluindo Magali nao pode devolver Magali"
        assert vendedor[0] in ("👨🏻‍💼 Silvano", "👩🏻‍💼 Solange Ap."), vendedor
    print("OK  D) Magali atual + pedir outro -> nunca retorna Magali (200 sorteios)")


def teste_E_troca_silvano_nunca_retorna_silvano():
    for _ in range(200):
        vendedor = responder._vendedor_da_vez("utilitario", excluir_nome="👨🏻‍💼 Silvano")
        assert vendedor[0] != "👨🏻‍💼 Silvano", "troca excluindo Silvano nao pode devolver Silvano"
        assert vendedor[0] in ("👩🏻‍💼 Magali", "👩🏻‍💼 Solange Ap."), vendedor
    print("OK  E) Silvano atual + pedir outro -> nunca retorna Silvano (200 sorteios)")


# ============================================================
# F) Mock de random.choice prova que _vendedor_da_vez usa sorteio real
# ============================================================
def teste_F_usa_random_choice_de_verdade():
    chamadas = []
    original = responder.random.choice

    def _fake_choice(seq):
        chamadas.append(list(seq))
        return seq[0]

    responder.random.choice = _fake_choice
    try:
        vendedor = responder._vendedor_da_vez("utilitario")
        assert len(chamadas) == 1, "esperava exatamente 1 chamada a random.choice"
        assert set(n for n, _ in chamadas[0]) == set(NOMES_UTIL), chamadas[0]
        assert vendedor == responder.VENDEDORES_UTIL_BASE[0]

        chamadas.clear()
        vendedor_troca = responder._vendedor_da_vez("utilitario", excluir_nome="👩🏻‍💼 Magali")
        assert len(chamadas) == 1
        nomes_oferecidos = set(n for n, _ in chamadas[0])
        assert "👩🏻‍💼 Magali" not in nomes_oferecidos, "Magali excluída não pode nem entrar na lista sorteada"
        assert nomes_oferecidos == {"👨🏻‍💼 Silvano", "👩🏻‍💼 Solange Ap."}

        print("OK  F) _vendedor_da_vez realmente delega a random.choice() -- confirmado via mock")
    finally:
        responder.random.choice = original


# ============================================================
# G) Sem estado de índice que possa favorecer Magali/Alexandre no restart
# ============================================================
def teste_G_sem_estado_de_indice_apos_restart():
    assert not hasattr(responder, "_RODIZIO_INDICE_CATEGORIA"), (
        "não pode mais existir índice de rodízio -- seleção é randômica pura"
    )
    assert not hasattr(responder, "_avancar_rodizio"), (
        "não pode mais existir função de avançar rodízio -- não há índice para avançar"
    )
    # "Restart" = novo processo = nada para carregar; o próximo sorteio
    # já é livre, sem nenhum viés de posição.
    vistos = {responder._vendedor_da_vez("utilitario")[0] for _ in range(100)}
    assert len(vistos) > 1, "100 sorteios só produziram 1 vendedor -- não parece randômico"
    print("OK  G) Nenhum estado de índice existe mais -- nada para 'resetar' após restart/deploy")


# ============================================================
# H) Dois phone_number_id continuam usando a MESMA regra randômica
# ============================================================
def teste_H_dois_numeros_mesma_regra_sem_influencia():
    import inspect
    assinatura = inspect.signature(responder._vendedor_da_vez)
    assert "sender_phone_number_id" not in assinatura.parameters, (
        "_vendedor_da_vez não pode receber phone_number_id -- número não pode influenciar a escolha"
    )
    # Sorteio mockado deterministicamente: mesmo resultado nos dois "números"
    # (a função nem tem como saber qual número está chamando).
    original = responder.random.choice
    responder.random.choice = lambda seq: seq[0]
    try:
        v1 = responder._vendedor_da_vez("utilitario")  # simula chamada vinda do numero 1
        v2 = responder._vendedor_da_vez("utilitario")  # simula chamada vinda do numero 2
        assert v1 == v2, "mesmo mock, resultado deveria ser idêntico independente do número empresarial"
    finally:
        responder.random.choice = original
    print("OK  H) _vendedor_da_vez não recebe/depende de phone_number_id -- regra idêntica nos dois números")


# ============================================================
# I) Handoff continua sendo enviado normalmente ao vendedor selecionado
# ============================================================
def teste_I_handoff_continua_funcionando():
    import assistente_comercial as ac

    numero = "5511900005001"
    ac.limpar_estado(numero)
    monkeypatches = []
    try:
        _mockar_envio_vendedor(monkeypatches)

        chamadas_template = []
        original_tpl = responder._enviar_template_novo_lead_vendedor

        def _fake_template_captura(numero_vendedor, *a, **k):
            chamadas_template.append(numero_vendedor)
            return True

        responder._enviar_template_novo_lead_vendedor = _fake_template_captura
        monkeypatches.append((responder, "_enviar_template_novo_lead_vendedor", original_tpl))

        ac.processar_mensagem(numero, "Saiba mais")
        ac.processar_mensagem(numero, "Estou procurando uma Renault Master 2027.")
        estado = ac.processar_mensagem(numero, "quero falar com um vendedor")
        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)

        estado = ac.obter_estado(numero)
        assert estado["vendedor"] is not None, "handoff deveria ter selecionado um vendedor"
        assert estado["vendedor"]["nome"] in NOMES_UTIL
        assert estado["transferencia_concluida"] is True
        assert len(chamadas_template) == 1, "template deveria ter sido enviado exatamente 1 vez"

        numero_esperado = estado["vendedor"]["link"].replace("https://wa.me/", "").strip()
        assert chamadas_template[0] == numero_esperado, "template não foi enviado ao vendedor certo"

        print(f"OK  I) Handoff continua funcionando normalmente (vendedor sorteado: {estado['vendedor']['nome']})")
    finally:
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)


if __name__ == "__main__":
    _bloquear_rede()
    teste_A_utilitario_so_vendedores_cadastrados()
    teste_B_passeio_so_vendedores_cadastrados()
    teste_C_nunca_mistura_categorias()
    teste_D_troca_magali_nunca_retorna_magali()
    teste_E_troca_silvano_nunca_retorna_silvano()
    teste_F_usa_random_choice_de_verdade()
    teste_G_sem_estado_de_indice_apos_restart()
    teste_H_dois_numeros_mesma_regra_sem_influencia()
    teste_I_handoff_continua_funcionando()
    print("\nTODOS OS TESTES DE REGRESSÃO (FASE 3.1V - SELEÇÃO RANDÔMICA) PASSARAM. ZERO chamadas de rede.")
