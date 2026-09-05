# teste_regressao_classificacao_gov_link.py
"""
Teste de regressao dos 3 ajustes controlados desta fase (correcao pontual,
sem nova arquitetura):

A/B) Classificacao comercial UTILITARIO x PASSEIO mais ampla e robusta em
     assistente_comercial.py (_PALAVRAS_UTILITARIO / _PALAVRAS_PASSEIO_EXPLICITA),
     sem tocar em VENDEDORES_UTIL_BASE, VENDEDORES_PASSEIO_BASE nem no rodizio.
C)   Vendas Governamentais/licitacao reconhecido tambem em texto livre,
     reaproveitando o MESMO bloco/fluxo ja existente (BLOCOS["4.1"], botao
     4.1), sem entrar no rodizio comercial comum.
D)   Link clicavel do WhatsApp do cliente no resumo enviado ao vendedor
     (texto_lead) e na variavel de telefone do template aprovado
     novo_lead_vendedor (mesmo conteudo, sem alterar estrutura/quantidade/
     ordem das variaveis do template).
E)   Nao-regressao: atendimento independente U->P->U continua com vendedores
     independentes por categoria.
F)   Nao-regressao: resposta institucional ("quem criou esse chatbot?")
     continua funcionando e nao interfere no vendedor comercial.

SEGURANCA - MUITO IMPORTANTE:
Este arquivo NUNCA atinge a Meta Graph API, o Claude/Anthropic ou o Google
Sheets. Todas as funcoes de rede de responder.py usadas nos testes de ponta a
ponta (C e D) sao substituidas por mocks locais antes de qualquer chamada a
responder.responder()/_processar_transferencia_vendedor(); os testes A/B/E/F
chamam funcoes puras (sem I/O) de assistente_comercial.py/responder_ia.py.

Executar:  python teste_regressao_classificacao_gov_link.py
"""

import os
import re

import assistente_comercial as ac
import responder
import responder_ia


def _preparar_ambiente():
    os.environ["ASSISTENTE_COMERCIAL_ATIVO"] = "1"
    responder._RODIZIO_INDICE_CATEGORIA["utilitario"] = 0
    responder._RODIZIO_INDICE_CATEGORIA["passeio"] = 0


def _mockar_saidas_externas(monkeypatches):
    """Substitui as funcoes de responder.py que fazem requests.post (Meta) e
    o registro em Sheets/mala direta por mocks locais. Mesmo padrao ja usado
    em teste_regressao_oficina_vendedor_pendente.py."""
    chamadas = {
        "enviar_mensagem": [],       # (numero, texto) - cliente
        "enviar_botoes": [],         # (numero, texto, botoes) - cliente
        "vendedor_mensagem": [],     # lista de (numero, texto) - _enviar_mensagem_com_status
        "vendedor_template": [],     # lista de kwargs/args - _enviar_template_novo_lead_vendedor
        "sheets": 0,
        "alerta_handoff": 0,
    }

    def _fake_enviar_mensagem(numero, texto, sender_phone_number_id=None):
        chamadas["enviar_mensagem"].append((numero, texto))

    def _fake_enviar_botoes(numero, texto, botoes, sender_phone_number_id=None):
        chamadas["enviar_botoes"].append((numero, texto, botoes))

    def _fake_enviar_mensagem_com_status(numero, texto):
        chamadas["vendedor_mensagem"].append((numero, texto))
        return True

    def _fake_enviar_template(numero_vendedor, nome_cliente, telefone_cliente, veiculo, resumo, visita_texto):
        chamadas["vendedor_template"].append({
            "numero_vendedor": numero_vendedor,
            "telefone_cliente": telefone_cliente,
        })
        return True

    def _fake_enviar_para_google_sheets(*args, **kwargs):
        chamadas["sheets"] += 1

    def _fake_enviar_alerta_handoff(*args, **kwargs):
        chamadas["alerta_handoff"] += 1

    alvos = [
        ("enviar_mensagem", _fake_enviar_mensagem),
        ("enviar_botoes", _fake_enviar_botoes),
        ("_enviar_mensagem_com_status", _fake_enviar_mensagem_com_status),
        ("_enviar_template_novo_lead_vendedor", _fake_enviar_template),
        ("enviar_para_google_sheets", _fake_enviar_para_google_sheets),
        ("_enviar_alerta_handoff", _fake_enviar_alerta_handoff),
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
    """Reproduz um turno real (mesmo padrao de teste_regressao_van_passeio_real.py):
    processa a mensagem e, se ficou qualificado sem vendedor, executa a
    transferencia."""
    estado = ac.processar_mensagem(numero, texto)
    if estado and estado.get("qualificado") and not estado.get("vendedor"):
        responder._processar_transferencia_vendedor(numero, "Cliente Teste", estado)
        estado = ac.obter_estado(numero)
    return estado


# ============================================================
# A/B — Classificacao UTILITARIO x PASSEIO ampla (frases naturais)
# ============================================================

FRASES_UTILITARIO = [
    "quero falar com vendedor de vans",
    "procuro uma van escolar",
    "preciso de veiculo para transporte de passageiros",
    "preciso de um veiculo de carga",
    "quero um furgao",
    "estou procurando uma Sprinter",
    "quero uma Master",
    "procuro uma Ducato",
    "quero uma Boxer escolar",
]

FRASES_PASSEIO = [
    "quero um carro para minha filha",
    "procuro um veiculo de passeio",
    "quero um SUV",
    "quero uma moto",
    "procuro uma moto eletrica",
]

FRASES_AMBIGUAS = [
    "oi, tudo bem?",
    "quero saber mais sobre financiamento",
    "voces tem desconto?",
    "qual o horario de funcionamento?",
]


def teste_classificacao_utilitario_frases_naturais():
    for frase in FRASES_UTILITARIO:
        resultado = ac._categoria_com_sinal_no_texto(ac._normalizar(frase))
        assert resultado == "utilitario", f"{frase!r} deveria classificar UTILITARIO, veio {resultado!r}"
    print("OK  Frases naturais de UTILITARIO (van/escolar/carga/passageiros/furgao/Sprinter/Master/Ducato/Boxer)")


def teste_classificacao_passeio_frases_naturais():
    for frase in FRASES_PASSEIO:
        resultado = ac._categoria_com_sinal_no_texto(ac._normalizar(frase))
        assert resultado == "passeio", f"{frase!r} deveria classificar PASSEIO, veio {resultado!r}"
    print("OK  Frases naturais de PASSEIO (carro/veiculo de passeio/SUV/moto/moto eletrica)")


def teste_categoria_ambigua_nao_vira_passeio():
    for frase in FRASES_AMBIGUAS:
        resultado = ac._categoria_com_sinal_no_texto(ac._normalizar(frase))
        assert resultado is None, f"{frase!r} deveria ficar AMBIGUA (None), veio {resultado!r} (passeio nunca pode ser fallback)"
    print("OK  Termos ambiguos/desconhecidos NAO viram passeio automaticamente")


# ============================================================
# A) VAN/UTILITARIO -> vendedor somente de VENDEDORES_UTIL_BASE
# ============================================================

def teste_A_van_utilitario_vendedor_correto():
    nomes_util = {n for n, _ in responder.VENDEDORES_UTIL_BASE}
    nomes_passeio = {n for n, _ in responder.VENDEDORES_PASSEIO_BASE}

    casos = [
        "5511900000301",
        "5511900000302",
        "5511900000303",
    ]
    frases = [
        "quero falar com vendedor de vans",
        "estou procurando uma Sprinter, pode me passar um vendedor?",
        "preciso de um veiculo de carga, me passa o contato do vendedor",
    ]
    _preparar_ambiente()
    for numero, frase in zip(casos, frases):
        ac.limpar_estado(numero)
        monkeypatches = []
        try:
            _mockar_saidas_externas(monkeypatches)
            estado = _passo(numero, frase)
            assert estado is not None and estado.get("categoria") == "utilitario", (frase, estado)
            assert estado["vendedor"]["nome"] in nomes_util, (frase, estado)
            assert estado["vendedor"]["nome"] not in nomes_passeio, (frase, estado)
        finally:
            _restaurar(monkeypatches)
    print("OK  A) Pedido de van/Sprinter/carga -> vendedor somente de VENDEDORES_UTIL_BASE")


# ============================================================
# B) PASSEIO/MOTO -> vendedor somente de VENDEDORES_PASSEIO_BASE
# ============================================================

def teste_B_passeio_moto_vendedor_correto():
    nomes_util = {n for n, _ in responder.VENDEDORES_UTIL_BASE}
    nomes_passeio = {n for n, _ in responder.VENDEDORES_PASSEIO_BASE}

    casos = [
        "5511900000311",
        "5511900000312",
    ]
    frases = [
        "quero um SUV, pode me passar um vendedor?",
        "quero uma moto eletrica, me passa o contato de um consultor",
    ]
    _preparar_ambiente()
    for numero, frase in zip(casos, frases):
        ac.limpar_estado(numero)
        monkeypatches = []
        try:
            _mockar_saidas_externas(monkeypatches)
            estado = _passo(numero, frase)
            assert estado is not None and estado.get("categoria") == "passeio", (frase, estado)
            assert estado["vendedor"]["nome"] in nomes_passeio, (frase, estado)
            assert estado["vendedor"]["nome"] not in nomes_util, (frase, estado)
        finally:
            _restaurar(monkeypatches)
    print("OK  B) Pedido de SUV/moto eletrica -> vendedor somente de VENDEDORES_PASSEIO_BASE")


# ============================================================
# C) GOVERNAMENTAL — texto livre reconhece a mesma intencao do botao 4.1,
#    nunca entra no rodizio comercial comum
# ============================================================

FRASES_GOVERNAMENTAIS = [
    "voces trabalham com licitacao publica?",
    "quero comprar para uma prefeitura",
    "voces vendem para governo?",
    "preciso falar com alguem de vendas governamentais",
    "participam de pregao eletronico?",
    "quero comprar veiculos para um orgao publico",
]


def teste_C_governamental_heuristica_texto_livre():
    for frase in FRASES_GOVERNAMENTAIS:
        intencao = responder.detectar_intencao_basica(frase)
        assert intencao == "governamentais", f"{frase!r} deveria detectar intencao governamentais, veio {intencao!r}"
    print("OK  C.1) detectar_intencao_basica reconhece as 6 frases governamentais em texto livre")


def teste_C_governamental_fluxo_completo_nao_entra_rodizio():
    _preparar_ambiente()
    numero = "5511900000321"
    ac.limpar_estado(numero)
    monkeypatches = []
    try:
        chamadas = _mockar_saidas_externas(monkeypatches)
        responder.responder(numero, "quero comprar veiculos para um orgao publico", nome_contato="Prefeitura Teste")

        # Cliente recebe exatamente o bloco governamental ja existente (4.1)
        assert len(chamadas["enviar_mensagem"]) == 1, chamadas["enviar_mensagem"]
        _, texto_enviado = chamadas["enviar_mensagem"][0]
        assert texto_enviado == responder.BLOCOS["4.1"], "deveria reusar o MESMO bloco do botao 4.1, sem novo texto paralelo"
        assert "Solange" in texto_enviado and "Lucas" in texto_enviado, texto_enviado
        assert "https://wa.me/5511989536141" in texto_enviado, texto_enviado
        assert "https://wa.me/5511940457215" in texto_enviado, texto_enviado
        assert "Medeiros e Sullato" in texto_enviado and "Galego" in texto_enviado and "Carloca" in texto_enviado, texto_enviado

        # Nao entrou no assistente comercial nem no rodizio de vendedores
        assert not ac.tem_contexto_comercial(numero), "pedido governamental nao pode abrir sessao comercial"
        assert chamadas["vendedor_mensagem"] == [], "nao pode notificar vendedor comercial comum"
        assert chamadas["vendedor_template"] == [], "nao pode disparar template de lead comercial"
    finally:
        _restaurar(monkeypatches)
    print("OK  C.2) Fluxo completo: texto livre governamental reusa BLOCOS['4.1'], nao cria lead comercial nem notifica vendedor comum")


def teste_C_governamental_botao_4_1_continua_funcionando():
    """O botao/ID 4.1 (clique direto) continua funcionando exatamente como antes."""
    _preparar_ambiente()
    numero = "5511900000322"
    monkeypatches = []
    try:
        chamadas = _mockar_saidas_externas(monkeypatches)
        responder.responder(numero, {"type": "interactive", "interactive": {"type": "button", "button_reply": {"id": "4.1", "title": "Governamentais"}}}, nome_contato="Cliente Teste")
        assert len(chamadas["enviar_mensagem"]) == 1, chamadas["enviar_mensagem"]
        assert chamadas["enviar_mensagem"][0][1] == responder.BLOCOS["4.1"]
    finally:
        _restaurar(monkeypatches)
    print("OK  C.3) Botao/ID 4.1 (clique) continua funcionando e usa o mesmo bloco atualizado")


# ============================================================
# D) Link do WhatsApp do cliente no resumo ao vendedor (texto livre e
#    variavel do template aprovado)
# ============================================================

def teste_D_link_cliente_no_resumo_vendedor():
    _preparar_ambiente()
    numero = "5511987654321"
    ac.limpar_estado(numero)
    monkeypatches = []
    try:
        chamadas = _mockar_saidas_externas(monkeypatches)
        estado = _passo(numero, "quero falar com vendedor de vans")
        assert estado["vendedor"] is not None, estado

        assert len(chamadas["vendedor_mensagem"]) == 1, chamadas["vendedor_mensagem"]
        _, texto_lead = chamadas["vendedor_mensagem"][0]
        link_esperado = f"https://wa.me/{numero}"
        assert link_esperado in texto_lead, texto_lead
        assert re.search(r"WhatsApp do cliente:\s*\n?\s*" + re.escape(link_esperado), texto_lead), texto_lead

        # Variavel de telefone do template aprovado tambem traz o link
        # clicavel (mesma estrutura/quantidade/ordem de variaveis do
        # template — so o CONTEUDO da variavel telefone mudou).
        assert len(chamadas["vendedor_template"]) == 1, chamadas["vendedor_template"]
        assert chamadas["vendedor_template"][0]["telefone_cliente"] == link_esperado, chamadas["vendedor_template"][0]
    finally:
        _restaurar(monkeypatches)
    print("OK  D) texto_lead E variavel de telefone do template contem https://wa.me/<numero normalizado do cliente>")


# ============================================================
# E) Nao-regressao: U->P->U com vendedores independentes por categoria
# ============================================================

def teste_E_up_u_nao_regressao():
    nomes_util = {n for n, _ in responder.VENDEDORES_UTIL_BASE}
    nomes_passeio = {n for n, _ in responder.VENDEDORES_PASSEIO_BASE}
    _preparar_ambiente()
    numero = "5511900000331"
    ac.limpar_estado(numero)
    monkeypatches = []
    try:
        _mockar_saidas_externas(monkeypatches)

        estado = _passo(numero, "quero falar com vendedor de vans")
        assert estado["categoria"] == "utilitario"
        vendedor_util = estado["vendedor"]["nome"]
        assert vendedor_util in nomes_util

        estado = _passo(numero, "na verdade tambem quero um veiculo de passeio, pode me passar um vendedor?")
        assert estado["categoria"] == "passeio", estado
        vendedor_passeio = estado["vendedor"]["nome"]
        assert vendedor_passeio in nomes_passeio
        assert vendedor_passeio != vendedor_util

        estado = _passo(numero, "voltando a van, pode me passar o vendedor de novo?")
        assert estado["categoria"] == "utilitario", estado
        assert estado["vendedor"]["nome"] == vendedor_util, "deve recuperar o MESMO vendedor de utilitario, sem sortear outro"
    finally:
        _restaurar(monkeypatches)
    print("OK  E) U->P->U preserva vendedores independentes por categoria (nao-regressao)")


# ============================================================
# F) Nao-regressao: resposta institucional nao interfere no vendedor
# ============================================================

def teste_F_institucional_nao_interfere():
    assert responder_ia._eh_pergunta_sobre_criador("quem criou esse chatbot?") is True

    prompt_sem_contexto = responder_ia._montar_system_prompt(mensagem="quem criou esse chatbot?")
    assert responder_ia._BLOCO_INSTITUCIONAL_CRIADOR.strip() in prompt_sem_contexto

    _preparar_ambiente()
    numero = "5511900000341"
    ac.limpar_estado(numero)
    monkeypatches = []
    try:
        _mockar_saidas_externas(monkeypatches)
        estado = _passo(numero, "quero falar com vendedor de vans")
        vendedor_nome = estado["vendedor"]["nome"]

        prompt_com_contexto = responder_ia._montar_system_prompt(
            contexto_comercial=estado, mensagem="quem criou esse chatbot?"
        )
        assert responder_ia._BLOCO_INSTITUCIONAL_CRIADOR.strip() in prompt_com_contexto, \
            "pergunta institucional deve continuar funcionando com negociacao comercial ativa"
        assert vendedor_nome in prompt_com_contexto, "vendedor real deve continuar presente no prompt"

        estado_depois = ac.obter_estado(numero)
        assert estado_depois["vendedor"]["nome"] == vendedor_nome, "pergunta institucional nao pode alterar o vendedor"
        assert estado_depois["categoria"] == "utilitario"
    finally:
        _restaurar(monkeypatches)
    print("OK  F) Resposta institucional preservada e nao interfere no vendedor comercial (nao-regressao)")


if __name__ == "__main__":
    teste_classificacao_utilitario_frases_naturais()
    teste_classificacao_passeio_frases_naturais()
    teste_categoria_ambigua_nao_vira_passeio()
    teste_A_van_utilitario_vendedor_correto()
    teste_B_passeio_moto_vendedor_correto()
    teste_C_governamental_heuristica_texto_livre()
    teste_C_governamental_fluxo_completo_nao_entra_rodizio()
    teste_C_governamental_botao_4_1_continua_funcionando()
    teste_D_link_cliente_no_resumo_vendedor()
    teste_E_up_u_nao_regressao()
    teste_F_institucional_nao_interfere()
    print("\nTODOS OS TESTES DESTA FASE PASSARAM. ZERO mensagens reais enviadas.")
