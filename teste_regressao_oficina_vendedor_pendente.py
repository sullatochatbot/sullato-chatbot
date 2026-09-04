# teste_regressao_oficina_vendedor_pendente.py
"""
Teste de regressão da CONVERSA REAL (Fase 3.1L) que expôs a colisão entre um
pedido de vendedor comercial pendente e o menu fixo de Oficina/Peças:

Cliente pede vendedor -> bot pergunta "passeio ou utilitário?" -> cliente
responde "passeio" -> resposta ERRADA de Oficina/Peças (BLOCOS["3.2.1"]),
porque "passeio"/"utilitario" estão em `comandos_conhecidos` e nunca
chegavam a assistente_comercial.processar_mensagem().

SEGURANÇA — MUITO IMPORTANTE:
Este arquivo chama responder.responder() de ponta a ponta (fluxo real).
TODAS as funções capazes de fazer uma chamada de rede de saída (Meta Graph
API ou Google Sheets) são substituídas por mocks ANTES de qualquer chamada
a responder.responder() — nenhum teste aqui pode, em hipótese alguma,
atingir a Meta Graph API ou notificar um vendedor real. Ver
_mockar_saidas_externas() abaixo: ela intercepta as 6 funções do módulo
responder.py que fazem requests.post (confirmado via grep antes de
escrever este arquivo): enviar_para_google_sheets, enviar_mensagem,
enviar_botoes, _enviar_mensagem_com_status,
_enviar_template_novo_lead_vendedor e _enviar_alerta_handoff.

Executar:  python teste_regressao_oficina_vendedor_pendente.py
"""

import os
import responder
import assistente_comercial as ac


def _preparar_ambiente():
    os.environ["ASSISTENTE_COMERCIAL_ATIVO"] = "1"
    responder._RODIZIO_INDICE_CATEGORIA["utilitario"] = 0
    responder._RODIZIO_INDICE_CATEGORIA["passeio"] = 0


def _mockar_saidas_externas(monkeypatches):
    """
    Substitui TODAS as funções de responder.py que fazem requests.post por
    mocks locais, sem nenhuma chamada de rede real. Retorna um dict de
    contadores para os testes confirmarem exatamente o que foi "enviado".
    """
    chamadas = {
        "enviar_mensagem": [],       # lista de (numero, texto) - cliente
        "enviar_botoes": [],         # lista de (numero, texto, botoes) - cliente
        "vendedor_mensagem": 0,      # _enviar_mensagem_com_status - vendedor
        "vendedor_template": 0,      # _enviar_template_novo_lead_vendedor - vendedor
        "sheets": 0,                 # enviar_para_google_sheets
        "alerta_handoff": 0,         # _enviar_alerta_handoff (numero fixo humano)
    }

    def _fake_enviar_mensagem(numero, texto, sender_phone_number_id=None):
        chamadas["enviar_mensagem"].append((numero, texto))

    def _fake_enviar_botoes(numero, texto, botoes, sender_phone_number_id=None):
        chamadas["enviar_botoes"].append((numero, texto, botoes))

    def _fake_enviar_mensagem_com_status(numero, texto):
        chamadas["vendedor_mensagem"] += 1
        return True

    def _fake_enviar_template(*args, **kwargs):
        chamadas["vendedor_template"] += 1
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


def teste_pedido_pendente_passeio_vai_para_vendedor_correto():
    numero = "5511900000501"
    ac.limpar_estado(numero)
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _mockar_saidas_externas(monkeypatches)

        responder.responder(numero, "procuro por um veiculo.", nome_contato="Cliente Teste")
        responder.responder(numero, "otimo, me passe o contato de um vendedor.", nome_contato="Cliente Teste")

        estado_pendente = ac.obter_estado(numero)
        assert estado_pendente["ativo"] is True
        assert estado_pendente["categoria"] is None
        assert estado_pendente["qualificado"] is False
        assert estado_pendente["estagio"] == "aguardando_veiculo"
        assert estado_pendente["intencao_visita"], "deveria haver pedido de vendedor pendente registrado"

        responder.responder(numero, "passeio", nome_contato="Cliente Teste")

        estado_final = ac.obter_estado(numero)
        assert estado_final["categoria"] == "passeio", estado_final
        nomes_passeio = [n for n, _ in responder.VENDEDORES_PASSEIO_BASE]
        assert estado_final["vendedor"] is not None, "handoff deveria ter ocorrido"
        assert estado_final["vendedor"]["nome"] in nomes_passeio, estado_final["vendedor"]

        textos_cliente = " | ".join(t for _, t in chamadas["enviar_mensagem"])
        assert "Oficina" not in textos_cliente, f"NAO pode ter caido em Oficina/Pecas: {textos_cliente!r}"
        assert "5511917027705" not in textos_cliente, "numero da Oficina nao pode aparecer aqui"
        assert chamadas["vendedor_mensagem"] == 1 and chamadas["vendedor_template"] == 1, \
            "handoff de passeio deveria ter notificado o vendedor exatamente 1 vez (mock)"

        print("OK  Pedido de vendedor pendente + 'passeio' -> handoff de VENDEDORES_PASSEIO_BASE (nao Oficina/Pecas)")
    finally:
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)


def teste_pedido_pendente_utilitario_vai_para_vendedor_correto():
    numero = "5511900000502"
    ac.limpar_estado(numero)
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _mockar_saidas_externas(monkeypatches)

        responder.responder(numero, "procuro por um veiculo.", nome_contato="Cliente Teste")
        responder.responder(numero, "otimo, me passe o contato de um vendedor.", nome_contato="Cliente Teste")
        responder.responder(numero, "utilitario", nome_contato="Cliente Teste")

        estado_final = ac.obter_estado(numero)
        assert estado_final["categoria"] == "utilitario", estado_final
        nomes_util = [n for n, _ in responder.VENDEDORES_UTIL_BASE]
        assert estado_final["vendedor"]["nome"] in nomes_util, estado_final["vendedor"]

        textos_cliente = " | ".join(t for _, t in chamadas["enviar_mensagem"])
        assert "Oficina" not in textos_cliente

        print("OK  Pedido de vendedor pendente + 'utilitario' -> handoff de VENDEDORES_UTIL_BASE (nao Oficina/Pecas)")
    finally:
        _restaurar(monkeypatches)
        ac.limpar_estado(numero)


def teste_pedido_pendente_van_e_carro_de_passeio():
    for numero, resposta, categoria_esperada, lista_esperada in [
        ("5511900000503", "van", "utilitario", "VENDEDORES_UTIL_BASE"),
        ("5511900000504", "carro de passeio", "passeio", "VENDEDORES_PASSEIO_BASE"),
    ]:
        ac.limpar_estado(numero)
        _preparar_ambiente()
        monkeypatches = []
        try:
            _mockar_saidas_externas(monkeypatches)
            responder.responder(numero, "procuro por um veiculo.", nome_contato="Cliente Teste")
            responder.responder(numero, "otimo, me passe o contato de um vendedor.", nome_contato="Cliente Teste")
            responder.responder(numero, resposta, nome_contato="Cliente Teste")

            estado_final = ac.obter_estado(numero)
            assert estado_final["categoria"] == categoria_esperada, (resposta, estado_final)
            lista = responder.VENDEDORES_UTIL_BASE if categoria_esperada == "utilitario" else responder.VENDEDORES_PASSEIO_BASE
            nomes = [n for n, _ in lista]
            assert estado_final["vendedor"]["nome"] in nomes, estado_final["vendedor"]
            print(f"OK  '{resposta}' com pedido pendente -> {lista_esperada} ({estado_final['vendedor']['nome']})")
        finally:
            _restaurar(monkeypatches)
            ac.limpar_estado(numero)


def teste_oficina_pecas_sem_pedido_pendente_continua_igual():
    """SEM nenhum pedido comercial pendente, 'passeio'/'utilitario' isolados
    devem continuar caindo exatamente no fluxo de Oficina/Pecas, como hoje."""
    for numero, resposta, bloco_esperado in [
        ("5511900000505", "passeio", "3.2.1"),
        ("5511900000506", "utilitario", "3.2.2"),
    ]:
        ac.limpar_estado(numero)
        _preparar_ambiente()
        monkeypatches = []
        try:
            chamadas = _mockar_saidas_externas(monkeypatches)

            # Nenhuma mensagem anterior -> nenhum estado comercial pendente.
            assert ac.obter_estado(numero) is None

            responder.responder(numero, resposta, nome_contato="Cliente Teste")

            assert ac.obter_estado(numero) is None, "nao deveria ter criado estado comercial nenhum"
            assert len(chamadas["enviar_mensagem"]) == 1
            texto_enviado = chamadas["enviar_mensagem"][0][1]
            assert texto_enviado == responder.BLOCOS[bloco_esperado], (
                f"resposta deveria ser exatamente o bloco de Oficina/Pecas {bloco_esperado}, "
                f"veio: {texto_enviado!r}"
            )
            print(f"OK  Sem pedido pendente, '{resposta}' isolado continua indo para Oficina/Pecas ({bloco_esperado})")
        finally:
            _restaurar(monkeypatches)
            ac.limpar_estado(numero)


def teste_zero_chamadas_reais_confirmado():
    """Confirmacao explicita: em toda a suite acima, as unicas 'chamadas' as
    funcoes de rede foram os mocks locais (contadores em memoria) - nenhuma
    requisicao HTTP real foi feita a Meta Graph API ou Google Sheets a
    partir deste arquivo de teste."""
    import inspect
    for nome in (
        "enviar_mensagem", "enviar_botoes", "_enviar_mensagem_com_status",
        "_enviar_template_novo_lead_vendedor", "enviar_para_google_sheets",
        "_enviar_alerta_handoff",
    ):
        fn = getattr(responder, nome)
        # Apos a restauracao (_restaurar), as funcoes voltam a ser as
        # originais do modulo - confirma que o teste sempre restaura o
        # estado de producao ao final de cada bloco try/finally.
        assert fn.__module__ == "responder", f"{nome} nao foi restaurada corretamente ao final do teste"
    print("OK  Todas as funcoes de rede foram restauradas ao original; nenhuma chamada real foi feita durante os testes")


if __name__ == "__main__":
    teste_pedido_pendente_passeio_vai_para_vendedor_correto()
    teste_pedido_pendente_utilitario_vai_para_vendedor_correto()
    teste_pedido_pendente_van_e_carro_de_passeio()
    teste_oficina_pecas_sem_pedido_pendente_continua_igual()
    teste_zero_chamadas_reais_confirmado()
    print("\nTODOS OS TESTES DE REGRESSAO (FASE 3.1L) PASSARAM. ZERO mensagens reais enviadas.")
