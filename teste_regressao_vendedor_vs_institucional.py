# teste_regressao_vendedor_vs_institucional.py
"""
Teste de regressão da CONVERSA REAL (Fase 3.1M) que expôs:

Causa 1 — histórico da IA (_HIST_IA, responder.py) nunca é corrigido pelo
estado determinístico: um nome de vendedor mencionado livremente pela IA
em qualquer troca anterior (real ou alucinado) continua sendo reenviado ao
Claude nas próximas 5 trocas, mesmo depois do backend já ter atribuído (ou
trocado) o vendedor de verdade — a confirmação determinística do handoff
nunca é adicionada a esse histórico. Corrigido reforçando
_REGRA_VENDEDOR_SEM_INVENCAO em responder_ia.py para instruir a IA a
ignorar qualquer nome de vendedor do histórico que não bata com o vendedor
informado no bloco de transferência concluída deste prompt.

Causa 2 — o bloco institucional (dados do criador do chatbot) tinha sido
bloqueado por completo sempre que havia contexto comercial ativo (Fase
3.1J). Confirmado explicitamente por Anderson que isso é restritivo demais:
a resposta institucional deve continuar funcionando mesmo no meio de uma
negociação comercial, sem apagar/trocar vendedor, categoria ou
transferencia_concluida. _montar_system_prompt() agora libera o bloco
institucional só por intenção explícita detectada na mensagem atual
(_eh_pergunta_sobre_criador), independente de contexto comercial ativo.

Fase 3.1N (barreira de CÓDIGO, adicionada depois da Fase 3.1M ter deixado
a proteção só como instrução de prompt): quando a pergunta é sobre "quem é
o vendedor atual" (assistente_comercial.resposta_vendedor_determinada),
o backend responde direto a partir do estado — sem passar pela IA — para
essa pergunta específica nunca depender do modelo citar o nome certo.

SEGURANÇA — MUITO IMPORTANTE: todas as 6 funções de responder.py capazes
de fazer requests.post (Meta Graph API ou Google Sheets) são mockadas
ANTES de qualquer chamada a responder.responder()/_processar_transferencia_vendedor
neste arquivo. Nenhuma mensagem real pode ser enviada a nenhum vendedor ou
cliente durante estes testes.

Executar:  python teste_regressao_vendedor_vs_institucional.py
"""

import os
import assistente_comercial as ac
import responder
import responder_ia


def _preparar_ambiente():
    os.environ["ASSISTENTE_COMERCIAL_ATIVO"] = "1"
    responder._RODIZIO_INDICE_CATEGORIA["utilitario"] = 0
    responder._RODIZIO_INDICE_CATEGORIA["passeio"] = 0


def _mockar_saidas_externas(monkeypatches):
    """Substitui TODAS as funções de responder.py que fazem requests.post
    por mocks locais — nenhuma chamada de rede real em nenhum teste aqui."""
    chamadas = {"vendedor_mensagem": 0, "vendedor_template": 0, "sheets": 0, "alerta_handoff": 0}

    def _fake_mensagem_status(numero, texto):
        chamadas["vendedor_mensagem"] += 1
        return True

    def _fake_template(*args, **kwargs):
        chamadas["vendedor_template"] += 1
        return True

    def _fake_sheets(*args, **kwargs):
        chamadas["sheets"] += 1

    def _fake_alerta(*args, **kwargs):
        chamadas["alerta_handoff"] += 1

    alvos = [
        ("enviar_mensagem", lambda n, t: None),
        ("enviar_botoes", lambda n, t, b: None),
        ("_enviar_mensagem_com_status", _fake_mensagem_status),
        ("_enviar_template_novo_lead_vendedor", _fake_template),
        ("enviar_para_google_sheets", _fake_sheets),
        ("_enviar_alerta_handoff", _fake_alerta),
    ]
    for nome, fake in alvos:
        original = getattr(responder, nome)
        setattr(responder, nome, fake)
        monkeypatches.append((responder, nome, original))

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


def _fluxo_ate_dois_vendedores(numero, veiculo_util, veiculo_passeio):
    """Reproduz: UTILITARIO -> vendedor U, pergunta de endereco, PASSEIO ->
    vendedor P. Retorna (vendedor_U_nome, vendedor_P_nome)."""
    _passo(numero, "tenho interesse")
    _passo(numero, veiculo_util)
    estado = _passo(numero, "quero falar com um vendedor")
    vendedor_u = estado["vendedor"]["nome"]

    # pergunta de endereco -- nao deve mudar nada.
    ac.processar_mensagem(numero, "qual o endereco de voces?")

    estado = _passo(numero, f"sobre {veiculo_passeio}, me passe um vendedor")
    vendedor_p = estado["vendedor"]["nome"]
    return vendedor_u, vendedor_p


def teste_pergunta_institucional_no_meio_da_negociacao_nao_troca_vendedor():
    numero = "5511900000601"
    ac.limpar_estado(numero)
    responder._HIST_IA.pop(numero, None)
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _mockar_saidas_externas(monkeypatches)
        enviados = []
        original_enviar_mensagem = responder.enviar_mensagem
        responder.enviar_mensagem = lambda n, t: enviados.append(t)
        monkeypatches.append((responder, "enviar_mensagem", original_enviar_mensagem))
        responder.enviar_botoes = lambda n, t, b: None

        vendedor_u, vendedor_p = _fluxo_ate_dois_vendedores(numero, "Master", "carro de passeio")
        assert vendedor_u in [n for n, _ in responder.VENDEDORES_UTIL_BASE]
        assert vendedor_p in [n for n, _ in responder.VENDEDORES_PASSEIO_BASE]
        assert vendedor_u != vendedor_p

        estado_antes = ac.obter_estado(numero)

        # 5) pergunta institucional -- deve responder corretamente E nao
        # pode mexer em nada do estado comercial.
        prompt_institucional = responder_ia._montar_system_prompt(estado_antes, "quem criou esse chatbot?")
        assert "98878" in prompt_institucional and "anderson@sullato.com.br" in prompt_institucional, (
            "resposta institucional deveria continuar funcionando durante negociacao ativa"
        )

        estado_depois = ac.processar_mensagem(numero, "quem criou esse chatbot?")
        assert estado_depois["categoria"] == estado_antes["categoria"]
        assert estado_depois["vendedor"]["nome"] == estado_antes["vendedor"]["nome"]
        assert estado_depois["transferencia_concluida"] == estado_antes["transferencia_concluida"]
        assert chamadas["vendedor_mensagem"] == 2 and chamadas["vendedor_template"] == 2, (
            "pergunta institucional nao pode disparar nenhum handoff novo"
        )

        # 6) "quem esta cuidando da minha van?" via responder.responder()
        # de ponta a ponta -- exercita a barreira de CODIGO (Fase 3.1N):
        # deve responder com vendedor_u, SEM mudar a categoria ativa
        # (continua passeio) nem o vendedor ativo (continua vendedor_p).
        enviados.clear()
        responder.responder(numero, "quem esta cuidando da minha van?", nome_contato="Cliente Teste")
        assert len(enviados) == 1, enviados
        assert vendedor_u in enviados[0], f"resposta deveria citar {vendedor_u!r}, veio: {enviados[0]!r}"
        assert vendedor_p not in enviados[0]
        estado_apos_van = ac.obter_estado(numero)
        assert estado_apos_van["categoria"] == "passeio", "pergunta informativa nao pode trocar a categoria ativa"
        assert estado_apos_van["vendedor"]["nome"] == vendedor_p
        assert estado_apos_van["atendimentos"]["utilitario"]["vendedor"]["nome"] == vendedor_u
        assert chamadas["vendedor_mensagem"] == 2 and chamadas["vendedor_template"] == 2, (
            "pergunta informativa sobre vendedor nao pode disparar handoff novo"
        )

        # 7) "e meu carro de passeio?" -> continua vendedor_p (categoria
        # ativa nunca mudou).
        enviados.clear()
        responder.responder(numero, "quem esta cuidando do meu carro de passeio?", nome_contato="Cliente Teste")
        assert len(enviados) == 1, enviados
        assert vendedor_p in enviados[0]
        assert vendedor_u not in enviados[0]
        estado_final = ac.obter_estado(numero)
        assert estado_final["categoria"] == "passeio"
        assert estado_final["vendedor"]["nome"] == vendedor_p
        assert chamadas["vendedor_mensagem"] == 2 and chamadas["vendedor_template"] == 2, (
            "nenhum handoff novo deveria ter ocorrido so por perguntar sobre o carro ja atribuido"
        )

        print(f"OK  Pergunta institucional + perguntas de vendedor (barreira de codigo) preservam U={vendedor_u} e P={vendedor_p}, sem terceiro vendedor")
    finally:
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)
        responder._HIST_IA.pop(numero, None)


def teste_com_outro_par_de_vendedores_prova_ausencia_de_hardcode():
    """Mesma sequencia, mas forcando o rodizio a comecar de outro ponto,
    para garantir que a barreira funciona com QUALQUER vendedor sorteado,
    nao apenas com os nomes vistos na conversa real."""
    numero = "5511900000602"
    ac.limpar_estado(numero)
    responder._HIST_IA.pop(numero, None)
    _preparar_ambiente()
    # Forca indices diferentes dos do teste anterior.
    responder._RODIZIO_INDICE_CATEGORIA["utilitario"] = 1
    responder._RODIZIO_INDICE_CATEGORIA["passeio"] = 2
    monkeypatches = []
    try:
        _mockar_saidas_externas(monkeypatches)

        vendedor_u, vendedor_p = _fluxo_ate_dois_vendedores(numero, "Sprinter", "carro de passeio")
        nomes_util = [n for n, _ in responder.VENDEDORES_UTIL_BASE]
        nomes_passeio = [n for n, _ in responder.VENDEDORES_PASSEIO_BASE]
        assert vendedor_u in nomes_util and vendedor_u != nomes_util[0], (
            "este teste exige comecar de um vendedor DIFERENTE do primeiro da lista, para provar ausencia de hardcode"
        )
        assert vendedor_p in nomes_passeio and vendedor_p != nomes_passeio[0]

        ac.processar_mensagem(numero, "quem criou esse chatbot?")
        estado_van = ac.processar_mensagem(numero, "quem esta cuidando da minha van?")
        assert estado_van["atendimentos"]["utilitario"]["vendedor"]["nome"] == vendedor_u

        estado_passeio = ac.processar_mensagem(numero, "e meu carro de passeio?")
        assert estado_passeio["vendedor"]["nome"] == vendedor_p

        print(f"OK  Sem hardcode: funciona com U={vendedor_u}, P={vendedor_p} (diferentes do primeiro teste)")
    finally:
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)
        responder._HIST_IA.pop(numero, None)


def teste_historico_poluido_nao_substitui_vendedor_real():
    """Historico textual contendo nomes de vendedores antigos/errados nao
    pode virar fonte de verdade -- a regra explicita em
    _REGRA_VENDEDOR_SEM_INVENCAO deve estar presente no prompt para
    instruir a IA a ignorar esses nomes."""
    contexto = {
        "ativo": True, "categoria": "utilitario", "veiculo": "Master",
        "vendedor": {"nome": "Vendedor Real A", "link": "https://wa.me/5511900000001"},
        "transferencia_concluida": True,
    }

    prompt = responder_ia._montar_system_prompt(contexto, "quem esta cuidando da minha van?")

    # A regra explicita contra o historico deve estar presente.
    assert "desatualizado ou incorreto" in prompt, "falta a instrucao contra nomes desatualizados do historico"
    assert "Vendedor Real A" in prompt, "o vendedor real precisa estar claramente informado no prompt"

    # Nomes hipoteticos de outros vendedores que poderiam estar no
    # historico da conversa (simulando "Jeferson vai te ajudar" / "Magali
    # esta cuidando do atendimento") NAO fazem parte do prompt do sistema --
    # so poderiam vir do historico (mensagens), que e onde a nova regra
    # instrui a IA a ignorar qualquer nome divergente do informado aqui.
    for nome_antigo in ("Jeferson", "Magali"):
        assert nome_antigo not in prompt, (
            f"o system prompt nao deveria mencionar {nome_antigo!r} -- "
            "ele so pode vir de _HIST_IA (mensagens), nunca do prompt do sistema"
        )

    print("OK  Regra contra historico poluido presente no prompt; vendedor real explicitamente informado")


def teste_historico_poluido_fim_a_fim_via_HIST_IA():
    """Constroi um _HIST_IA real com uma mencao antiga de vendedor errado e
    confirma que o ESTADO DETERMINISTICO (fonte de verdade real, nao
    dependente do modelo) permanece correto -- e que o prompt do sistema
    aponta para o vendedor real, nunca para o nome antigo do historico."""
    numero = "5511900000603"
    ac.limpar_estado(numero)
    responder._HIST_IA.pop(numero, None)
    _preparar_ambiente()
    monkeypatches = []
    try:
        _mockar_saidas_externas(monkeypatches)

        # Semeia o historico com nomes de vendedores ERRADOS/antigos, do
        # mesmo jeito que a IA os adicionaria em texto livre (_add_hist_ia).
        responder._add_hist_ia(numero, "quem vai me atender?", "Pode deixar que o Jeferson vai te ajudar!")
        responder._add_hist_ia(numero, "tem certeza?", "Sim, a Magali esta cuidando do seu atendimento tambem.")

        vendedor_u, vendedor_p = _fluxo_ate_dois_vendedores(numero, "Master", "carro de passeio")

        hist = responder._get_hist_ia(numero)
        assert any("Jeferson" in m["content"] for m in hist), "pre-condicao: historico deveria conter o nome antigo"

        estado = ac.obter_estado(numero)
        assert estado["vendedor"]["nome"] == vendedor_p
        assert estado["atendimentos"]["utilitario"]["vendedor"]["nome"] == vendedor_u
        assert "Jeferson" not in (vendedor_u, vendedor_p), "coincidencia improvavel, mas confirma que nao e o vendedor real"

        prompt = responder_ia._montar_system_prompt(estado, "quem esta cuidando da minha van?")
        assert vendedor_p in prompt
        assert "Jeferson" not in prompt and "Magali esta cuidando" not in prompt

        print("OK  Estado determinístico permanece correto mesmo com _HIST_IA poluido; prompt aponta pro vendedor real")
    finally:
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)
        responder._HIST_IA.pop(numero, None)


def teste_sem_vendedor_atribuido_nao_inventa():
    """Fase 3.1N, cenario 4 obrigatorio: sem nenhum vendedor determinado
    ainda, a pergunta 'quem e meu vendedor?' NAO pode ser respondida com um
    nome inventado -- nem pela barreira de codigo (que deve retornar None e
    deixar o fluxo normal seguir) nem, por consequencia, ganhar uma
    resposta de handoff fantasma."""
    numero = "5511900000604"
    ac.limpar_estado(numero)
    responder._HIST_IA.pop(numero, None)
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _mockar_saidas_externas(monkeypatches)
        enviados = []
        original_enviar_mensagem = responder.enviar_mensagem
        responder.enviar_mensagem = lambda n, t: enviados.append(t)
        monkeypatches.append((responder, "enviar_mensagem", original_enviar_mensagem))
        responder.enviar_botoes = lambda n, t, b: None

        # Nenhuma mensagem anterior -- nenhum vendedor atribuido ainda.
        assert ac.obter_estado(numero) is None

        r = ac.resposta_vendedor_determinada(None, "quem e meu vendedor?")
        assert r is None, "sem estado algum, a barreira de codigo nao pode inventar vendedor"

        responder.responder(numero, "quem e meu vendedor?", nome_contato="Cliente Teste")
        assert chamadas["vendedor_mensagem"] == 0 and chamadas["vendedor_template"] == 0, (
            "pergunta sem nenhum contexto comercial nao pode disparar handoff nenhum"
        )
        # Sem ANTHROPIC_API_KEY neste ambiente de teste, a IA nao responde
        # (responder_com_ia retorna None) e o fluxo cai no "nao entendi" +
        # menu -- em nenhum cenario um nome de vendedor pode aparecer aqui.
        for texto in enviados:
            for nome_vendedor, _ in responder.VENDEDORES_UTIL_BASE + responder.VENDEDORES_PASSEIO_BASE:
                assert nome_vendedor not in texto, f"vendedor inventado sem nenhuma atribuicao: {nome_vendedor!r} em {texto!r}"

        print("OK  Sem vendedor atribuido, a pergunta 'quem e meu vendedor?' nao inventa nenhum nome")
    finally:
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)
        responder._HIST_IA.pop(numero, None)


if __name__ == "__main__":
    teste_pergunta_institucional_no_meio_da_negociacao_nao_troca_vendedor()
    teste_com_outro_par_de_vendedores_prova_ausencia_de_hardcode()
    teste_sem_vendedor_atribuido_nao_inventa()
    teste_historico_poluido_nao_substitui_vendedor_real()
    teste_historico_poluido_fim_a_fim_via_HIST_IA()
    print("\nTODOS OS TESTES DE REGRESSAO (FASE 3.1M) PASSARAM. ZERO mensagens reais enviadas.")
