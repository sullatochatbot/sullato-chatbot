# teste_regressao_consulta_vendedor_atual.py
"""
Teste de regressão da Fase 3.1S (diagnóstico real: "Quem vai entrar em
contato" caiu na IA, que respondeu como se não soubesse o vendedor, mesmo
com o vendedor corretamente armazenado no estado comercial).

Cobre: perguntas naturais sobre o vendedor/contato ATUAL já atribuído
devem ser respondidas deterministicamente por
assistente_comercial.resposta_vendedor_determinada() (nome + link REAIS do
estado), sem depender da IA — e sem interferir no fluxo de TROCA de
vendedor já implementado (Fase 3.1R), que continua tendo prioridade sempre
que a intenção for de troca ("quero outro vendedor", "não quero falar com
a Magali").

100% local, ZERO rede: assistente_comercial.py não importa `requests` em
nenhum ponto (confirmado por leitura do arquivo) — as funções testadas
aqui (resposta_vendedor_determinada/processar_mensagem) nunca tocam a API
da Meta/Sheets. Mesmo assim, `requests.post` é bloqueado explicitamente
neste arquivo como rede de segurança extra, depois do incidente da sessão
anterior (chamada real escapou de um script de diagnóstico por falta de
mock em enviar_botoes) — qualquer chamada de rede real aqui vira erro
imediato.

Executar:  python teste_regressao_consulta_vendedor_atual.py
"""

import os
import requests
import assistente_comercial as ac

os.environ["ASSISTENTE_COMERCIAL_ATIVO"] = "1"


def _bloquear_rede():
    """Qualquer requests.post real vira erro imediato — nenhuma chamada de
    rede pode escapar durante estes testes."""
    def _post_bloqueado(*args, **kwargs):
        raise AssertionError(f"BLOQUEADO: requests.post real chamado com args={args} kwargs={kwargs}")
    requests.post = _post_bloqueado


def _vendedor_magali():
    return {"nome": "👩🏻‍💼 Magali", "link": "https://wa.me/5511940215082"}


def _estado_com_vendedor(categoria="utilitario"):
    return {
        "ativo": True,
        "qualificado": True,
        "categoria": categoria,
        "veiculo": "Renault Master 2027",
        "vendedor": _vendedor_magali(),
        "transferencia_concluida": True,
        "atendimentos": {},
    }


# ============================================================
# A-E) Perguntas de CONSULTA ao vendedor atual -- resposta determinística
# ============================================================
def teste_A_quem_vai_entrar_em_contato():
    estado = _estado_com_vendedor()
    resultado = ac.resposta_vendedor_determinada(estado, "Quem vai entrar em contato?")
    assert resultado == _vendedor_magali(), resultado
    print("OK  A) 'Quem vai entrar em contato?' -> vendedor atual (nome+link corretos)")


def teste_B_quem_vai_falar_comigo():
    estado = _estado_com_vendedor()
    resultado = ac.resposta_vendedor_determinada(estado, "Quem vai falar comigo?")
    assert resultado == _vendedor_magali(), resultado
    print("OK  B) 'Quem vai falar comigo?' -> vendedor atual")


def teste_C_qual_o_nome_do_vendedor():
    estado = _estado_com_vendedor()
    resultado = ac.resposta_vendedor_determinada(estado, "Qual o nome do vendedor?")
    assert resultado == _vendedor_magali(), resultado
    print("OK  C) 'Qual o nome do vendedor?' -> vendedor atual")


def teste_D_qual_o_contato_do_vendedor():
    estado = _estado_com_vendedor()
    resultado = ac.resposta_vendedor_determinada(estado, "Qual o contato do vendedor?")
    assert resultado == _vendedor_magali(), resultado
    assert resultado["link"] == "https://wa.me/5511940215082"
    print("OK  D) 'Qual o contato do vendedor?' -> vendedor atual + link")


def teste_E_me_passa_o_contato_dele():
    estado = _estado_com_vendedor()
    resultado = ac.resposta_vendedor_determinada(estado, "Me passa o contato dele")
    assert resultado == _vendedor_magali(), resultado
    print("OK  E) 'Me passa o contato dele' -> vendedor atual + link")


def teste_variacoes_extras():
    """Cobertura adicional das demais frases pedidas no diagnóstico."""
    estado = _estado_com_vendedor()
    frases = [
        "Quem é o vendedor?",
        "Qual vendedor vai me atender?",
        "Quem ficou com meu atendimento?",
        "Quem está me atendendo?",
        "Me passa o número dele",
        "Qual o WhatsApp dele?",
        "Cadê o contato do vendedor?",
    ]
    for frase in frases:
        resultado = ac.resposta_vendedor_determinada(estado, frase)
        assert resultado == _vendedor_magali(), f"{frase!r} -> {resultado}"
    print(f"OK  Variações extras ({len(frases)} frases) -> vendedor atual em todas")


# ============================================================
# F/G) Pedido de TROCA continua intacto -- nunca responde com o atual
# ============================================================
def teste_F_quero_outro_vendedor_nao_responde_atual():
    numero = "5511900002001"
    ac.limpar_estado(numero)
    try:
        estado = ac._novo_estado(numero)
        estado.update(_estado_com_vendedor())
        ac._ESTADOS[ac._chave_estado(numero)] = estado

        # resposta_vendedor_determinada isolada NÃO pode responder com o
        # vendedor atual para um pedido de troca.
        resultado_direto = ac.resposta_vendedor_determinada(estado, "quero outro vendedor")
        assert resultado_direto is None, (
            f"'quero outro vendedor' não pode ser tratado como consulta ao vendedor atual: {resultado_direto}"
        )

        # fluxo real: processar_mensagem() entra em troca (vendedor limpo +
        # sinal pendente), nunca retorna o vendedor atual como resposta final.
        estado_pos = ac.processar_mensagem(numero, "quero outro vendedor")
        assert estado_pos["vendedor"] is None, estado_pos
        assert estado_pos["troca_vendedor_pendente"] is True, estado_pos
        assert estado_pos["vendedor_excluido_na_troca"]["nome"] == _vendedor_magali()["nome"]

        print("OK  F) 'Quero outro vendedor' NÃO responde com o vendedor atual -- continua no fluxo de troca")
    finally:
        ac.limpar_estado(numero)


def teste_G_nao_quero_falar_com_a_magali_continua_troca():
    numero = "5511900002002"
    ac.limpar_estado(numero)
    try:
        estado = ac._novo_estado(numero)
        estado.update(_estado_com_vendedor())
        ac._ESTADOS[ac._chave_estado(numero)] = estado

        resultado_direto = ac.resposta_vendedor_determinada(estado, "nao quero falar com a Magali")
        assert resultado_direto is None, resultado_direto

        estado_pos = ac.processar_mensagem(numero, "nao quero falar com a Magali")
        assert estado_pos["vendedor"] is None, estado_pos
        assert estado_pos["troca_vendedor_pendente"] is True, estado_pos

        print("OK  G) 'Não quero falar com a Magali' continua entrando no fluxo de troca (não é tratado como consulta)")
    finally:
        ac.limpar_estado(numero)


# ============================================================
# H) Sem vendedor no estado -- nunca inventa
# ============================================================
def teste_H_sem_vendedor_nao_inventa():
    estado = {
        "ativo": True,
        "categoria": "utilitario",
        "vendedor": None,
        "transferencia_concluida": False,
        "atendimentos": {},
    }
    for frase in ("Quem vai entrar em contato?", "Qual o contato do vendedor?", "Me passa o contato dele"):
        resultado = ac.resposta_vendedor_determinada(estado, frase)
        assert resultado is None, f"{frase!r} não pode inventar vendedor sem estado: {resultado}"
    print("OK  H) Sem vendedor no estado -- nenhuma das perguntas inventa vendedor")


# ============================================================
# I) Troca de categoria (Fase 3.1H) continua intacta
# ============================================================
def teste_I_troca_categoria_continua_intacta():
    numero = "5511900002003"
    ac.limpar_estado(numero)
    try:
        estado = ac._novo_estado(numero)
        estado.update(_estado_com_vendedor(categoria="utilitario"))
        ac._ESTADOS[ac._chave_estado(numero)] = estado

        estado_pos = ac.processar_mensagem(numero, "sobre veiculos de passeio, me passe um vendedor")
        assert estado_pos["categoria"] == "passeio", estado_pos
        assert estado_pos["vendedor"] is None
        assert estado_pos["atendimentos"]["utilitario"]["vendedor"]["nome"] == _vendedor_magali()["nome"]
        print("OK  I) Troca de categoria (Fase 3.1H) continua intacta")
    finally:
        ac.limpar_estado(numero)


# ============================================================
# J) Mudança de dia/período de visita (Fase 3.1F) continua intacta
# ============================================================
def teste_J_mudanca_visita_continua_intacta():
    numero = "5511900002004"
    ac.limpar_estado(numero)
    try:
        estado = ac._novo_estado(numero)
        estado.update(_estado_com_vendedor(categoria="utilitario"))
        estado["data_visita"] = "quarta"
        estado["horario_visita"] = "tarde"
        ac._ESTADOS[ac._chave_estado(numero)] = estado

        estado_pos = ac.processar_mensagem(numero, "prefiro mudar para quinta de manha")
        assert estado_pos is not None
        assert estado_pos["vendedor"]["nome"] == _vendedor_magali()["nome"], "mudança de visita não pode mexer no vendedor"
        print("OK  J) Mudança de dia/período de visita (Fase 3.1F) continua intacta, sem mexer no vendedor")
    finally:
        ac.limpar_estado(numero)


if __name__ == "__main__":
    _bloquear_rede()
    teste_A_quem_vai_entrar_em_contato()
    teste_B_quem_vai_falar_comigo()
    teste_C_qual_o_nome_do_vendedor()
    teste_D_qual_o_contato_do_vendedor()
    teste_E_me_passa_o_contato_dele()
    teste_variacoes_extras()
    teste_F_quero_outro_vendedor_nao_responde_atual()
    teste_G_nao_quero_falar_com_a_magali_continua_troca()
    teste_H_sem_vendedor_nao_inventa()
    teste_I_troca_categoria_continua_intacta()
    teste_J_mudanca_visita_continua_intacta()
    print("\nTODOS OS TESTES DE REGRESSÃO (FASE 3.1S - CONSULTA AO VENDEDOR ATUAL) PASSARAM. ZERO chamadas de rede.")
