# teste_regressao_multiplos_numeros_meta.py
"""
Teste de regressão (Fase 3.1O) do suporte a DOIS números de produção do
WhatsApp Cloud API no mesmo chatbot (PHONE_NUMBER_ID e
PHONE_NUMBER_ID_2030).

Regra principal: a conversa deve permanecer no mesmo número pelo qual
entrou — nunca receber por um e responder pelo outro. E o estado de
conversa (assistente_comercial._ESTADOS, responder._HIST_IA) não pode se
misturar quando o MESMO cliente fala com os dois números simultaneamente.

SEGURANÇA — MUITO IMPORTANTE: este arquivo mocka requests.post (o ponto
único por onde toda chamada de rede de saída passa em responder.py —
confirmado por grep antes de escrever este arquivo) ANTES de qualquer
chamada a responder.responder(). Nenhuma chamada de rede real é feita, a
nenhum cliente ou vendedor, em nenhum teste aqui.

Executar:  python teste_regressao_multiplos_numeros_meta.py
"""

import os
import responder
import webhook
import assistente_comercial as ac
import salvar_em_mala_direta as _sed_module

# Valores reais informados por Anderson (usados só para tornar o teste
# concreto e legível — o mecanismo funciona para quaisquer dois IDs).
NUM_1 = "681607758375737"      # PHONE_NUMBER_ID (número original/padrão)
NUM_2 = "1420797457772701"     # PHONE_NUMBER_ID_2030 (número novo)


def _preparar_ambiente():
    os.environ["ASSISTENTE_COMERCIAL_ATIVO"] = "1"
    responder.PHONE_NUMBER_ID = NUM_1  # simula o valor real vindo do .env/Render
    responder._RODIZIO_INDICE_CATEGORIA["utilitario"] = 0
    responder._RODIZIO_INDICE_CATEGORIA["passeio"] = 0


class _FakeResponse:
    status_code = 200
    text = '{"ok": true}'


def _mockar_requests_post(monkeypatches):
    """Substitui requests.post — usado por TODAS as funções de envio de
    responder.py (enviar_mensagem, enviar_botoes, _enviar_mensagem_com_status,
    _enviar_template_novo_lead_vendedor, _enviar_alerta_handoff,
    enviar_para_google_sheets) — por um mock local. Retorna uma lista de
    objetos simples {"url", "to"} para os testes confirmarem qual
    phone_number_id foi usado, E para quem, em cada envio (necessário para
    distinguir mensagem ao CLIENTE de notificação interna a vendedor/
    handoff, que continua propositalmente no número padrão)."""
    chamadas = []

    def _fake_post(url, headers=None, json=None, timeout=None, data=None):
        to = (json or {}).get("to") if isinstance(json, dict) else None
        chamadas.append({"url": url, "to": to})
        return _FakeResponse()

    original = responder.requests.post
    responder.requests.post = _fake_post
    monkeypatches.append((responder.requests, "post", original))
    return chamadas


def _mockar_mala_direta(monkeypatches):
    """salvar_em_mala_direta.py grava de verdade num CSV local (sem
    dependência externa, então nunca cai no fallback de import — os outros
    módulos de Sheets falham por falta de 'gspread' e já caem em no-op
    sozinhos). Mockado aqui para o teste não sujar mala_direta.csv."""
    original = _sed_module.salvar_em_mala_direta
    _sed_module.salvar_em_mala_direta = lambda *a, **k: None
    monkeypatches.append((_sed_module, "salvar_em_mala_direta", original))


def _restaurar(monkeypatches):
    for obj, nome, original in monkeypatches:
        setattr(obj, nome, original)


def _limpar(numero_cliente, sender_phone_number_id=None):
    ac.limpar_estado(numero_cliente, sender_phone_number_id)
    chave_hist = responder._chave_hist(numero_cliente, sender_phone_number_id)
    responder._HIST_IA.pop(chave_hist, None)


def teste_caso_a_resposta_sai_pelo_numero_que_recebeu():
    numero_cliente = "5511900000701"
    _limpar(numero_cliente, NUM_1)
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _mockar_requests_post(monkeypatches)
        _mockar_mala_direta(monkeypatches)

        responder.responder(numero_cliente, "oi", nome_contato="Cliente Teste", sender_phone_number_id=NUM_1)

        chamadas_whatsapp = [c["url"] for c in chamadas if "graph.facebook.com" in c["url"]]
        assert chamadas_whatsapp, "nenhuma chamada à Meta Graph API foi feita"
        assert all(f"/{NUM_1}/messages" in u for u in chamadas_whatsapp), chamadas_whatsapp
        assert not any(NUM_2 in u for u in chamadas_whatsapp)

        print("OK  CASO A: mensagem recebida no PHONE_NUMBER_ID -> resposta sai pelo mesmo numero")
    finally:
        _restaurar(monkeypatches)
        _limpar(numero_cliente, NUM_1)


def teste_caso_b_resposta_sai_pelo_segundo_numero():
    numero_cliente = "5511900000702"
    _limpar(numero_cliente, NUM_2)
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _mockar_requests_post(monkeypatches)
        _mockar_mala_direta(monkeypatches)

        responder.responder(numero_cliente, "oi", nome_contato="Cliente Teste", sender_phone_number_id=NUM_2)

        chamadas_whatsapp = [c["url"] for c in chamadas if "graph.facebook.com" in c["url"]]
        assert chamadas_whatsapp, "nenhuma chamada à Meta Graph API foi feita"
        assert all(f"/{NUM_2}/messages" in u for u in chamadas_whatsapp), chamadas_whatsapp
        assert not any(NUM_1 in u for u in chamadas_whatsapp)

        print("OK  CASO B: mensagem recebida no PHONE_NUMBER_ID_2030 -> resposta sai pelo mesmo numero")
    finally:
        _restaurar(monkeypatches)
        _limpar(numero_cliente, NUM_2)


def teste_caso_c_sem_sender_usa_fallback_numero_padrao():
    numero_cliente = "5511900000703"
    _limpar(numero_cliente)  # chave antiga (compatibilidade), sem numero
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _mockar_requests_post(monkeypatches)
        _mockar_mala_direta(monkeypatches)

        # Chamada no estilo ANTIGO (3 argumentos, sem sender_phone_number_id)
        # -- precisa continuar funcionando exatamente como antes.
        responder.responder(numero_cliente, "oi", "Cliente Teste")

        chamadas_whatsapp = [c["url"] for c in chamadas if "graph.facebook.com" in c["url"]]
        assert chamadas_whatsapp, "nenhuma chamada à Meta Graph API foi feita"
        assert all(f"/{NUM_1}/messages" in u for u in chamadas_whatsapp), chamadas_whatsapp

        print("OK  CASO C: chamada antiga sem sender_phone_number_id -> fallback usa o numero padrao")
    finally:
        _restaurar(monkeypatches)
        _limpar(numero_cliente)


def teste_caso_d_mesmo_cliente_dois_numeros_nao_se_misturam():
    numero_cliente = "5511900000704"
    _limpar(numero_cliente, NUM_1)
    _limpar(numero_cliente, NUM_2)
    _preparar_ambiente()
    monkeypatches = []
    try:
        _mockar_requests_post(monkeypatches)

        # Cliente fala com o NUMERO 1 sobre um utilitario e pede vendedor.
        responder.responder(numero_cliente, "tenho interesse", nome_contato="Cliente Teste", sender_phone_number_id=NUM_1)
        responder.responder(numero_cliente, "Master", nome_contato="Cliente Teste", sender_phone_number_id=NUM_1)
        responder.responder(numero_cliente, "quero falar com um vendedor", nome_contato="Cliente Teste", sender_phone_number_id=NUM_1)

        estado_num1 = ac.obter_estado(numero_cliente, NUM_1)
        assert estado_num1 is not None, "deveria existir estado comercial isolado para o numero 1"
        assert estado_num1["categoria"] == "utilitario", estado_num1
        assert estado_num1["vendedor"] is not None

        # ANTES de qualquer mensagem pelo numero 2, nao pode existir estado
        # nenhum lá (prova de que nao compartilham a mesma entrada).
        estado_num2_antes = ac.obter_estado(numero_cliente, NUM_2)
        assert estado_num2_antes is None, "o numero 2 nao deveria ter nenhum estado ainda (isolamento)"

        # O MESMO numero de cliente, agora conversando com o NUMERO 2 sobre passeio.
        responder.responder(numero_cliente, "tenho interesse", nome_contato="Cliente Teste", sender_phone_number_id=NUM_2)
        responder.responder(numero_cliente, "quero um carro de passeio", nome_contato="Cliente Teste", sender_phone_number_id=NUM_2)
        responder.responder(numero_cliente, "quero falar com um vendedor", nome_contato="Cliente Teste", sender_phone_number_id=NUM_2)

        estado_num2 = ac.obter_estado(numero_cliente, NUM_2)
        assert estado_num2 is not None, "deveria existir estado comercial isolado para o numero 2"
        assert estado_num2["categoria"] == "passeio", estado_num2
        assert estado_num2["vendedor"] is not None

        # O estado do NUMERO 1 precisa continuar exatamente como estava --
        # nao pode ter sido sobrescrito/contaminado pela conversa do numero 2.
        estado_num1_depois = ac.obter_estado(numero_cliente, NUM_1)
        assert estado_num1_depois["categoria"] == "utilitario"
        assert estado_num1_depois["vendedor"]["nome"] == estado_num1["vendedor"]["nome"]

        # Chaves de histórico de IA tambem isoladas (mesmo numero de cliente,
        # numeros empresariais diferentes -> chaves diferentes).
        chave1 = responder._chave_hist(numero_cliente, NUM_1)
        chave2 = responder._chave_hist(numero_cliente, NUM_2)
        assert chave1 != chave2
        assert chave1 == f"{NUM_1}:{numero_cliente}"
        assert chave2 == f"{NUM_2}:{numero_cliente}"

        print("OK  CASO D: mesmo cliente falando com os dois numeros -> estados comerciais isolados, sem contaminacao")
    finally:
        _restaurar(monkeypatches)
        _limpar(numero_cliente, NUM_1)
        _limpar(numero_cliente, NUM_2)


def _payload_meta(phone_number_id, numero_cliente, texto, nome="Cliente Teste"):
    """Monta um payload no formato real que a Meta envia ao /webhook."""
    return {
        "entry": [{
            "changes": [{
                "value": {
                    "metadata": {"phone_number_id": phone_number_id},
                    "contacts": [{"profile": {"name": nome}}],
                    "messages": [{
                        "from": numero_cliente,
                        "type": "text",
                        "text": {"body": texto},
                    }],
                }
            }]
        }]
    }


def teste_ponta_a_ponta_via_webhook_flask_reproduz_teste_real():
    """
    Reproduz o TESTE REAL relatado por Anderson, passando pela rota Flask
    /webhook de verdade (não só por responder.responder diretamente) — o
    mesmo caminho de código que um payload real da Meta percorre: extrai
    metadata.phone_number_id, repassa para responder.responder(), que deve
    responder pelo MESMO phone_number_id recebido.

    Cobre as 4 mensagens reais testadas por Anderson: "oi", "ola",
    "me fale sobre vans", "quero falar com um atendente".
    """
    numero_cliente = "5511999998888"
    _limpar(numero_cliente, NUM_2)
    _preparar_ambiente()
    webhook.PHONE_NUMBER_ID = NUM_1  # simula o default/fallback do ambiente real
    monkeypatches = []
    try:
        chamadas = _mockar_requests_post(monkeypatches)
        _mockar_mala_direta(monkeypatches)
        client = webhook.app.test_client()

        mensagens_reais = ["oi", "ola", "me fale sobre vans", "quero falar com um atendente"]
        for texto in mensagens_reais:
            chamadas.clear()
            payload = _payload_meta(NUM_2, numero_cliente, texto)
            resp = client.post("/webhook", json=payload)
            assert resp.status_code == 200, (texto, resp.status_code, resp.data)

            chamadas_whatsapp = [c for c in chamadas if "graph.facebook.com" in c["url"]]
            assert chamadas_whatsapp, f"nenhuma resposta enviada para {texto!r}"

            # Mensagens dirigidas AO CLIENTE (to == numero_cliente) devem
            # OBRIGATORIAMENTE sair pelo numero 2 (o que recebeu) -- este e
            # o bug real relatado por Anderson.
            chamadas_ao_cliente = [c for c in chamadas_whatsapp if c["to"] == numero_cliente]
            assert chamadas_ao_cliente, f"nenhuma resposta AO CLIENTE para {texto!r}: {chamadas_whatsapp}"
            assert all(f"/{NUM_2}/messages" in c["url"] for c in chamadas_ao_cliente), (
                f"mensagem {texto!r} recebida no numero 2 mas resposta ao CLIENTE saiu por outro numero: {chamadas_ao_cliente}"
            )
            assert not any(NUM_1 in c["url"] for c in chamadas_ao_cliente), (
                f"mensagem {texto!r} vazou para o numero padrao (o bug real relatado): {chamadas_ao_cliente}"
            )
            # "quero falar com um atendente" tambem dispara um alerta INTERNO
            # fixo (_enviar_alerta_handoff, numero de atendimento humano,
            # nunca visto pelo cliente) -- esse, por decisao consciente
            # documentada no codigo, continua saindo pelo numero padrao, e
            # isso e esperado (nao e o bug relatado).
            chamadas_internas = [c for c in chamadas_whatsapp if c["to"] != numero_cliente]
            if chamadas_internas:
                assert all(f"/{NUM_1}/messages" in c["url"] for c in chamadas_internas), chamadas_internas

        print("OK  Ponta-a-ponta via /webhook (Flask): as 4 mensagens reais testadas por Anderson "
              "respondem todas pelo MESMO phone_number_id que recebeu, nunca pelo padrao")
    finally:
        _restaurar(monkeypatches)
        _limpar(numero_cliente, NUM_2)


if __name__ == "__main__":
    teste_caso_a_resposta_sai_pelo_numero_que_recebeu()
    teste_caso_b_resposta_sai_pelo_segundo_numero()
    teste_caso_c_sem_sender_usa_fallback_numero_padrao()
    teste_caso_d_mesmo_cliente_dois_numeros_nao_se_misturam()
    teste_ponta_a_ponta_via_webhook_flask_reproduz_teste_real()
    print("\nTODOS OS TESTES DE REGRESSAO (FASE 3.1O - DOIS NUMEROS META) PASSARAM. ZERO mensagens reais enviadas.")
