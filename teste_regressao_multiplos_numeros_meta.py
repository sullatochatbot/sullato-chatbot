# teste_regressao_multiplos_numeros_meta.py
"""
Teste de regressão (Fase 3.1O/3.1P) do suporte a MÚLTIPLOS números de
produção do WhatsApp Cloud API no MESMO chatbot — hoje três:
PHONE_NUMBER_ID (94054), PHONE_NUMBER_ID_2030 (2030) e
PHONE_NUMBER_ID_2542 (2542).

Regra principal: a conversa deve permanecer no mesmo número pelo qual
entrou — nunca receber por um e responder pelo outro. E o estado de
conversa (assistente_comercial._ESTADOS, responder._HIST_IA) não pode se
misturar quando o MESMO cliente fala com números diferentes.

Fase 3.1P (terceiro número, 2542): nenhuma linha de código de produção
precisou mudar para o terceiro número entrar em funcionamento — o
roteamento já era genérico, baseado inteiramente no valor real de
metadata.phone_number_id vindo do webhook da Meta, sem nenhuma lista/
comparação fixa de números no código. Este arquivo prova isso testando um
NUM_3 que nunca apareceu em nenhuma linha de responder.py/webhook.py/
assistente_comercial.py.

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
# concreto e legível — o mecanismo funciona para quaisquer N IDs; nenhum
# deles aparece em responder.py/webhook.py/assistente_comercial.py).
NUM_1 = "681607758375737"      # PHONE_NUMBER_ID (94054 — número original/padrão)
NUM_2 = "1420797457772701"     # PHONE_NUMBER_ID_2030 (2030)
NUM_3 = "1259771500558028"     # PHONE_NUMBER_ID_2542 (2542 — terceiro número, Fase 3.1P)


def _preparar_ambiente():
    os.environ["ASSISTENTE_COMERCIAL_ATIVO"] = "1"
    responder.PHONE_NUMBER_ID = NUM_1  # simula o valor real vindo do .env/Render
    responder._RODIZIO_INDICE_CATEGORIA["utilitario"] = 0
    responder._RODIZIO_INDICE_CATEGORIA["passeio"] = 0


class _FakeResponse:
    status_code = 200
    text = '{"ok": true}'


def _extrair_corpo(json_payload):
    """Extrai um texto pesquisável do payload da Meta, cobrindo os 3
    formatos usados pelo projeto: texto simples, botões interativos e
    template (parâmetros de corpo, como novo_lead_vendedor)."""
    if not isinstance(json_payload, dict):
        return ""
    if isinstance(json_payload.get("text"), dict):
        return json_payload["text"].get("body", "") or ""
    if json_payload.get("type") == "interactive":
        return ((json_payload.get("interactive") or {}).get("body") or {}).get("text", "") or ""
    if json_payload.get("type") == "template":
        params = ((json_payload.get("template") or {}).get("components") or [{}])[0].get("parameters", [])
        return " | ".join(p.get("text", "") for p in params if isinstance(p, dict))
    return ""


def _mockar_requests_post(monkeypatches):
    """Substitui requests.post — usado por TODAS as funções de envio de
    responder.py (enviar_mensagem, enviar_botoes, _enviar_mensagem_com_status,
    _enviar_template_novo_lead_vendedor, _enviar_alerta_handoff,
    enviar_para_google_sheets) — por um mock local. Retorna uma lista de
    objetos simples {"url", "to", "body"} para os testes confirmarem qual
    phone_number_id foi usado, para quem, e o conteúdo enviado em cada
    envio (necessário para distinguir mensagem ao CLIENTE de notificação
    interna a vendedor/handoff, e para confirmar consistência de nome de
    vendedor entre a mensagem ao cliente e o lead ao vendedor)."""
    chamadas = []

    def _fake_post(url, headers=None, json=None, timeout=None, data=None):
        to = (json or {}).get("to") if isinstance(json, dict) else None
        chamadas.append({"url": url, "to": to, "body": _extrair_corpo(json)})
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


def _somente_url_para_cliente(chamadas, numero_cliente):
    return [c["url"] for c in chamadas if "graph.facebook.com" in c["url"] and c["to"] == numero_cliente]


def teste_caso_a_94054_recebe_94054_responde():
    numero_cliente = "5511900000701"
    _limpar(numero_cliente, NUM_1)
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _mockar_requests_post(monkeypatches)
        _mockar_mala_direta(monkeypatches)

        responder.responder(numero_cliente, "oi", nome_contato="Cliente Teste", sender_phone_number_id=NUM_1)

        urls_cliente = _somente_url_para_cliente(chamadas, numero_cliente)
        assert urls_cliente, "nenhuma resposta ao cliente foi enviada"
        assert all(f"/{NUM_1}/messages" in u for u in urls_cliente), urls_cliente
        assert not any(NUM_2 in u or NUM_3 in u for u in urls_cliente)

        print("OK  CASO A: 94054 recebe -> 94054 responde")
    finally:
        _restaurar(monkeypatches)
        _limpar(numero_cliente, NUM_1)


def teste_caso_b_2030_recebe_2030_responde():
    numero_cliente = "5511900000702"
    _limpar(numero_cliente, NUM_2)
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _mockar_requests_post(monkeypatches)
        _mockar_mala_direta(monkeypatches)

        responder.responder(numero_cliente, "oi", nome_contato="Cliente Teste", sender_phone_number_id=NUM_2)

        urls_cliente = _somente_url_para_cliente(chamadas, numero_cliente)
        assert urls_cliente, "nenhuma resposta ao cliente foi enviada"
        assert all(f"/{NUM_2}/messages" in u for u in urls_cliente), urls_cliente
        assert not any(NUM_1 in u or NUM_3 in u for u in urls_cliente)

        print("OK  CASO B: 2030 recebe -> 2030 responde")
    finally:
        _restaurar(monkeypatches)
        _limpar(numero_cliente, NUM_2)


def teste_caso_c_2542_recebe_2542_responde():
    """Terceiro número (Fase 3.1P) — NUM_3 nunca aparece em nenhuma linha
    de código de produção; se este teste passar, é a prova de que o
    roteamento genérico por metadata.phone_number_id funciona para
    qualquer número novo, sem exigir alteração de código."""
    numero_cliente = "5511900000705"
    _limpar(numero_cliente, NUM_3)
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _mockar_requests_post(monkeypatches)
        _mockar_mala_direta(monkeypatches)

        responder.responder(numero_cliente, "oi", nome_contato="Cliente Teste", sender_phone_number_id=NUM_3)

        urls_cliente = _somente_url_para_cliente(chamadas, numero_cliente)
        assert urls_cliente, "nenhuma resposta ao cliente foi enviada"
        assert all(f"/{NUM_3}/messages" in u for u in urls_cliente), urls_cliente
        assert not any(NUM_1 in u or NUM_2 in u for u in urls_cliente)

        print("OK  CASO C: 2542 (terceiro numero, sem nenhuma linha de codigo dedicada) recebe -> 2542 responde")
    finally:
        _restaurar(monkeypatches)
        _limpar(numero_cliente, NUM_3)


def teste_caso_d_mesmo_cliente_tres_numeros_nao_se_misturam():
    numero_cliente = "5511900000704"
    _limpar(numero_cliente, NUM_1)
    _limpar(numero_cliente, NUM_2)
    _limpar(numero_cliente, NUM_3)
    _preparar_ambiente()
    monkeypatches = []
    try:
        _mockar_requests_post(monkeypatches)

        # Cliente fala com o NUMERO 1 (94054) sobre um utilitario e pede vendedor.
        responder.responder(numero_cliente, "tenho interesse", nome_contato="Cliente Teste", sender_phone_number_id=NUM_1)
        responder.responder(numero_cliente, "Master", nome_contato="Cliente Teste", sender_phone_number_id=NUM_1)
        responder.responder(numero_cliente, "quero falar com um vendedor", nome_contato="Cliente Teste", sender_phone_number_id=NUM_1)

        estado_num1 = ac.obter_estado(numero_cliente, NUM_1)
        assert estado_num1 is not None, "deveria existir estado comercial isolado para o numero 1 (94054)"
        assert estado_num1["categoria"] == "utilitario", estado_num1
        assert estado_num1["vendedor"] is not None

        # ANTES de qualquer mensagem pelos numeros 2 e 3, nao pode existir
        # estado nenhum lá (prova de que nao compartilham a mesma entrada).
        assert ac.obter_estado(numero_cliente, NUM_2) is None, "numero 2 (2030) nao deveria ter estado ainda"
        assert ac.obter_estado(numero_cliente, NUM_3) is None, "numero 3 (2542) nao deveria ter estado ainda"

        # O MESMO numero de cliente, agora conversando com o NUMERO 2 (2030) sobre passeio.
        responder.responder(numero_cliente, "tenho interesse", nome_contato="Cliente Teste", sender_phone_number_id=NUM_2)
        responder.responder(numero_cliente, "quero um carro de passeio", nome_contato="Cliente Teste", sender_phone_number_id=NUM_2)
        responder.responder(numero_cliente, "quero falar com um vendedor", nome_contato="Cliente Teste", sender_phone_number_id=NUM_2)

        estado_num2 = ac.obter_estado(numero_cliente, NUM_2)
        assert estado_num2 is not None, "deveria existir estado comercial isolado para o numero 2 (2030)"
        assert estado_num2["categoria"] == "passeio", estado_num2
        assert estado_num2["vendedor"] is not None

        # E o MESMO numero de cliente, agora conversando com o NUMERO 3 (2542)
        # sobre um assunto ainda diferente (van, mas sem chegar a pedir vendedor).
        responder.responder(numero_cliente, "tenho interesse", nome_contato="Cliente Teste", sender_phone_number_id=NUM_3)
        responder.responder(numero_cliente, "Sprinter", nome_contato="Cliente Teste", sender_phone_number_id=NUM_3)

        estado_num3 = ac.obter_estado(numero_cliente, NUM_3)
        assert estado_num3 is not None, "deveria existir estado comercial isolado para o numero 3 (2542)"
        assert estado_num3["categoria"] == "utilitario", estado_num3
        assert estado_num3["vendedor"] is None, "este numero nao pediu vendedor ainda -- nao pode ter sido preenchido"

        # Os estados 1 e 2 precisam continuar EXATAMENTE como estavam --
        # nao podem ter sido sobrescritos/contaminados pela conversa do numero 3.
        estado_num1_depois = ac.obter_estado(numero_cliente, NUM_1)
        assert estado_num1_depois["categoria"] == "utilitario"
        assert estado_num1_depois["vendedor"]["nome"] == estado_num1["vendedor"]["nome"]

        estado_num2_depois = ac.obter_estado(numero_cliente, NUM_2)
        assert estado_num2_depois["categoria"] == "passeio"
        assert estado_num2_depois["vendedor"]["nome"] == estado_num2["vendedor"]["nome"]

        # Chaves de histórico de IA tambem isoladas entre os tres numeros
        # (mesmo numero de cliente, numeros empresariais diferentes ->
        # chaves diferentes).
        chave1 = responder._chave_hist(numero_cliente, NUM_1)
        chave2 = responder._chave_hist(numero_cliente, NUM_2)
        chave3 = responder._chave_hist(numero_cliente, NUM_3)
        assert len({chave1, chave2, chave3}) == 3, "as tres chaves de historico deveriam ser distintas"
        assert chave1 == f"{NUM_1}:{numero_cliente}"
        assert chave2 == f"{NUM_2}:{numero_cliente}"
        assert chave3 == f"{NUM_3}:{numero_cliente}"

        print("OK  CASO D: mesmo cliente falando com os TRES numeros -> estados comerciais isolados, sem contaminacao")
    finally:
        _restaurar(monkeypatches)
        _limpar(numero_cliente, NUM_1)
        _limpar(numero_cliente, NUM_2)
        _limpar(numero_cliente, NUM_3)


def teste_caso_e_sem_sender_usa_fallback_numero_padrao():
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

        urls_cliente = _somente_url_para_cliente(chamadas, numero_cliente)
        assert urls_cliente, "nenhuma resposta ao cliente foi enviada"
        assert all(f"/{NUM_1}/messages" in u for u in urls_cliente), urls_cliente

        print("OK  CASO E: chamada antiga sem sender_phone_number_id -> fallback usa o numero padrao (94054)")
    finally:
        _restaurar(monkeypatches)
        _limpar(numero_cliente)


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


def teste_ponta_a_ponta_via_webhook_flask_tres_numeros():
    """
    Reproduz o fluxo real passando pela rota Flask /webhook de verdade (não
    só por responder.responder diretamente) — o mesmo caminho de código
    que um payload real da Meta percorre: extrai metadata.phone_number_id,
    repassa para responder.responder(), que deve responder pelo MESMO
    phone_number_id recebido. Roda as mesmas 4 mensagens reais já testadas
    por Anderson, desta vez também para o TERCEIRO número (2542), provando
    que a genericidade do roteamento vale para um número novo sem
    nenhuma alteração de código.
    """
    numero_cliente = "5511999998888"
    _preparar_ambiente()
    webhook.PHONE_NUMBER_ID = NUM_1  # simula o default/fallback do ambiente real
    monkeypatches = []
    try:
        chamadas = _mockar_requests_post(monkeypatches)
        _mockar_mala_direta(monkeypatches)
        client = webhook.app.test_client()

        mensagens_reais = ["oi", "ola", "me fale sobre vans", "quero falar com um atendente"]
        for numero_receptor, apelido in ((NUM_2, "2030"), (NUM_3, "2542")):
            _limpar(numero_cliente, numero_receptor)
            for texto in mensagens_reais:
                chamadas.clear()
                payload = _payload_meta(numero_receptor, numero_cliente, texto)
                resp = client.post("/webhook", json=payload)
                assert resp.status_code == 200, (apelido, texto, resp.status_code, resp.data)

                chamadas_whatsapp = [c for c in chamadas if "graph.facebook.com" in c["url"]]
                assert chamadas_whatsapp, f"nenhuma resposta enviada para {texto!r} via {apelido}"

                # Mensagens dirigidas AO CLIENTE (to == numero_cliente) devem
                # OBRIGATORIAMENTE sair pelo numero que recebeu.
                chamadas_ao_cliente = [c for c in chamadas_whatsapp if c["to"] == numero_cliente]
                assert chamadas_ao_cliente, f"nenhuma resposta AO CLIENTE para {texto!r} via {apelido}: {chamadas_whatsapp}"
                assert all(f"/{numero_receptor}/messages" in c["url"] for c in chamadas_ao_cliente), (
                    f"[{apelido}] mensagem {texto!r} recebida no numero {apelido} mas resposta ao "
                    f"CLIENTE saiu por outro numero: {chamadas_ao_cliente}"
                )
                outros_numeros = {NUM_1, NUM_2, NUM_3} - {numero_receptor}
                assert not any(any(outro in c["url"] for outro in outros_numeros) for c in chamadas_ao_cliente), (
                    f"[{apelido}] mensagem {texto!r} vazou para outro numero: {chamadas_ao_cliente}"
                )
                # "quero falar com um atendente" tambem dispara um alerta INTERNO
                # fixo (_enviar_alerta_handoff, numero de atendimento humano,
                # nunca visto pelo cliente) -- esse, por decisao consciente
                # documentada no codigo, continua saindo pelo numero padrao (94054).
                chamadas_internas = [c for c in chamadas_whatsapp if c["to"] != numero_cliente]
                if chamadas_internas:
                    assert all(f"/{NUM_1}/messages" in c["url"] for c in chamadas_internas), chamadas_internas
            _limpar(numero_cliente, numero_receptor)

        print("OK  Ponta-a-ponta via /webhook (Flask), TRES numeros: 4 mensagens reais respondem "
              "sempre pelo MESMO phone_number_id que recebeu, inclusive no terceiro numero (2542) sem alteracao de codigo")
    finally:
        _restaurar(monkeypatches)


def teste_caso_f_ciclo_comercial_completo_consistente_tres_numeros_concorrente():
    """
    Valida o CICLO COMERCIAL COMPLETO de ponta a ponta nos três números,
    com as conversas ENTRELAÇADAS mensagem a mensagem (não sequenciais —
    passo 1 dos três clientes, depois passo 2 dos três, etc.) para expor
    qualquer contaminação de estado que uma execução puramente sequencial
    poderia mascarar:

        entrada -> categoria -> seleção de vendedor (rodízio real) ->
        persistência do vendedor na sessão -> contato do vendedor enviado
        AO CLIENTE -> lead/resumo enviado AO MESMO VENDEDOR.

    Cliente A -> 94054 -> utilitário
    Cliente B -> 2030   -> passeio
    Cliente C -> 2542   -> utilitário (categoria repetida em número
                            diferente, para provar que o rodízio real e a
                            seleção de vendedor não dependem do número)
    """
    numero_a, numero_b, numero_c = "5511900000801", "5511900000802", "5511900000803"
    for num, sender in ((numero_a, NUM_1), (numero_b, NUM_2), (numero_c, NUM_3)):
        _limpar(num, sender)
    _preparar_ambiente()
    monkeypatches = []
    try:
        chamadas = _mockar_requests_post(monkeypatches)
        _mockar_mala_direta(monkeypatches)

        # Passo 1 dos três (entrelaçado, não sequencial por cliente).
        responder.responder(numero_a, "tenho interesse", nome_contato="Cliente A", sender_phone_number_id=NUM_1)
        responder.responder(numero_b, "tenho interesse", nome_contato="Cliente B", sender_phone_number_id=NUM_2)
        responder.responder(numero_c, "tenho interesse", nome_contato="Cliente C", sender_phone_number_id=NUM_3)

        # Passo 2 dos três.
        responder.responder(numero_a, "Master", nome_contato="Cliente A", sender_phone_number_id=NUM_1)
        responder.responder(numero_b, "quero um carro de passeio", nome_contato="Cliente B", sender_phone_number_id=NUM_2)
        responder.responder(numero_c, "Sprinter", nome_contato="Cliente C", sender_phone_number_id=NUM_3)

        # Passo 3 dos três -- pedido de vendedor, disparando o handoff real.
        chamadas.clear()
        responder.responder(numero_a, "quero falar com um vendedor", nome_contato="Cliente A", sender_phone_number_id=NUM_1)
        responder.responder(numero_b, "quero falar com um vendedor", nome_contato="Cliente B", sender_phone_number_id=NUM_2)
        responder.responder(numero_c, "quero falar com um vendedor", nome_contato="Cliente C", sender_phone_number_id=NUM_3)

        nomes_util = [n for n, _ in responder.VENDEDORES_UTIL_BASE]
        nomes_passeio = [n for n, _ in responder.VENDEDORES_PASSEIO_BASE]

        estado_a = ac.obter_estado(numero_a, NUM_1)
        estado_b = ac.obter_estado(numero_b, NUM_2)
        estado_c = ac.obter_estado(numero_c, NUM_3)

        # 1) Categoria identificada corretamente pela conversa, independente do número.
        assert estado_a["categoria"] == "utilitario", estado_a
        assert estado_b["categoria"] == "passeio", estado_b
        assert estado_c["categoria"] == "utilitario", estado_c

        # 2) Vendedor selecionado pertence à lista/rodízio real da categoria correta.
        assert estado_a["vendedor"] is not None and estado_a["vendedor"]["nome"] in nomes_util, estado_a.get("vendedor")
        assert estado_b["vendedor"] is not None and estado_b["vendedor"]["nome"] in nomes_passeio, estado_b.get("vendedor")
        assert estado_c["vendedor"] is not None and estado_c["vendedor"]["nome"] in nomes_util, estado_c.get("vendedor")

        # Mesma categoria (utilitário) em dois números diferentes (A e C) ->
        # o rodízio real (compartilhado, único, como já era antes dos múltiplos
        # números) deve ter avançado normalmente e dado vendedores DIFERENTES,
        # provando que não há sorteio duplicado nem número influenciando a escolha.
        assert estado_a["vendedor"]["nome"] != estado_c["vendedor"]["nome"], (
            "A e C sao ambos utilitario -- deveriam ter recebido vendedores "
            f"diferentes pelo rodizio real: A={estado_a['vendedor']} C={estado_c['vendedor']}"
        )

        # 3) Consistência cliente<->vendedor<->lead, para os TRÊS números.
        for numero_cliente, sender, estado in (
            (numero_a, NUM_1, estado_a),
            (numero_b, NUM_2, estado_b),
            (numero_c, NUM_3, estado_c),
        ):
            vendedor_nome = estado["vendedor"]["nome"]
            vendedor_numero = estado["vendedor"]["link"].replace("https://wa.me/", "").strip()

            # 3a) resposta AO CLIENTE sai pelo numero empresarial correto e
            # contém o nome/contato do vendedor.
            msgs_ao_cliente = [
                c for c in chamadas
                if "graph.facebook.com" in c["url"] and c["to"] == numero_cliente
            ]
            assert msgs_ao_cliente, f"nenhuma mensagem ao cliente {numero_cliente}"
            assert all(f"/{sender}/messages" in c["url"] for c in msgs_ao_cliente), (
                f"resposta ao cliente {numero_cliente} nao saiu pelo numero correto ({sender}): {msgs_ao_cliente}"
            )
            assert any(vendedor_nome in c["body"] for c in msgs_ao_cliente), (
                f"cliente {numero_cliente} nao recebeu o nome do vendedor {vendedor_nome} na resposta: {msgs_ao_cliente}"
            )

            # 3b) lead/resumo (template + texto livre) enviado ao MESMO
            # número de vendedor informado ao cliente -- nunca a outro.
            msgs_ao_vendedor = [
                c for c in chamadas
                if "graph.facebook.com" in c["url"] and c["to"] == vendedor_numero
            ]
            assert msgs_ao_vendedor, (
                f"nenhum lead/resumo chegou ao vendedor {vendedor_nome} ({vendedor_numero}) "
                f"informado ao cliente {numero_cliente} -- possível inconsistência cliente!=lead"
            )
            assert any("NOVO LEAD QUALIFICADO" in c["body"] for c in msgs_ao_vendedor), (
                f"nenhuma mensagem de lead completa encontrada para {vendedor_nome}: {msgs_ao_vendedor}"
            )

        # 4) Isolamento cruzado: nenhum vendedor de A apareceu na mensagem
        # ao cliente B ou C, e vice-versa (categoria/estado não vazou).
        nome_vendedor_a = estado_a["vendedor"]["nome"]
        nome_vendedor_b = estado_b["vendedor"]["nome"]
        nome_vendedor_c = estado_c["vendedor"]["nome"]
        msgs_cliente_b = [c for c in chamadas if c["to"] == numero_b]
        msgs_cliente_c = [c for c in chamadas if c["to"] == numero_c]
        assert not any(nome_vendedor_a in c["body"] for c in msgs_cliente_b)
        assert not any(nome_vendedor_a in c["body"] for c in msgs_cliente_c)
        assert not any(nome_vendedor_b in c["body"] for c in (msgs_cliente_c))

        print("OK  CASO F: ciclo comercial completo (categoria -> vendedor -> cliente -> lead) "
              "consistente e isolado nos TRES numeros, com conversas entrelacadas/concorrentes")
    finally:
        _restaurar(monkeypatches)
        for num, sender in ((numero_a, NUM_1), (numero_b, NUM_2), (numero_c, NUM_3)):
            _limpar(num, sender)


# Casos determinísticos (não dependem de Claude/IA — comparáveis byte a
# byte): menus, blocos institucionais (endereço, oficina, crédito,
# governamentais, assinatura, trabalhe conosco), handoff de atendente e
# listas de veículos por categoria. Cada item é (id_da_mensagem, rótulo).
_CASOS_DETERMINISTICOS_PARIDADE = [
    ("menu", "saudação/menu inicial"),
    ("1", "menu comprar/vender"),
    ("2", "menu oficina/peças"),
    ("2.1", "bloco oficina/peças (texto)"),
    ("2.2", "bloco endereço oficina"),
    ("endereco oficina", "endereço oficina (alias texto)"),
    ("3.2.1", "oficina/peças — passeio"),
    ("3.2.2", "oficina/peças — utilitário"),
    ("1.3", "bloco endereço loja"),
    ("btn-endereco", "endereço loja (alias)"),
    ("3", "bloco crédito"),
    ("4.1", "bloco governamentais"),
    ("4.2", "bloco assinatura"),
    ("governamental", "governamentais (alias)"),
    ("garantia", "pós-venda via garantia (botões)"),
    ("btn-trabalhe", "trabalhe conosco"),
    ("mais1", "mais opções (1)"),
    ("mais2", "mais opções (2)"),
    ("mais3", "mais opções (3)"),
    ("btn-pos-venda", "pós-venda (botões)"),
    ("atendente", "handoff atendente — mensagem ao cliente"),
    ("1.1", "lista de veículos de passeio"),
    ("1.2", "lista de veículos utilitários"),
]


def teste_caso_g_paridade_deterministica_tres_numeros():
    """
    Confirma que TODAS as respostas determinísticas (menus, blocos
    institucionais, listas de veículos, handoff de atendente) são
    IDÊNTICAS byte a byte nos três números — sender_phone_number_id nunca
    pode alterar conteúdo, só a origem do envio.
    """
    resultados = {}  # rotulo -> {apelido: [corpos]}
    for numero_empresarial, apelido in ((NUM_1, "94054"), (NUM_2, "2030"), (NUM_3, "2542")):
        numero_cliente = f"5511900002{apelido}"
        _limpar(numero_cliente, numero_empresarial)
        _preparar_ambiente()
        monkeypatches = []
        try:
            chamadas = _mockar_requests_post(monkeypatches)
            _mockar_mala_direta(monkeypatches)

            for id_msg, rotulo in _CASOS_DETERMINISTICOS_PARIDADE:
                chamadas.clear()
                responder.responder(numero_cliente, id_msg, nome_contato="Cliente Teste", sender_phone_number_id=numero_empresarial)
                corpos = [
                    c["body"] for c in chamadas
                    if "graph.facebook.com" in c["url"] and c["to"] == numero_cliente
                ]
                resultados.setdefault(rotulo, {})[apelido] = corpos
        finally:
            _restaurar(monkeypatches)
            _limpar(numero_cliente, numero_empresarial)

    divergencias = []
    for rotulo, por_numero in resultados.items():
        valores = list(por_numero.values())
        if not all(v == valores[0] for v in valores):
            divergencias.append((rotulo, por_numero))

    assert not divergencias, f"Divergência de conteúdo entre números: {divergencias}"
    print(f"OK  CASO G: {len(_CASOS_DETERMINISTICOS_PARIDADE)} respostas determinísticas idênticas "
          "(byte a byte) nos três números")


def teste_caso_h_ia_recebe_mesmo_contexto_tres_numeros():
    """
    Para uma pergunta institucional livre ("Quem criou esse chatbot?"),
    numa conversa fresca (sem contexto comercial prévio) em cada número,
    confirma que responder_ia.responder_com_ia() é chamado com EXATAMENTE
    os mesmos argumentos (mensagem, histórico vazio, contexto_comercial
    None) independente do número empresarial receptor — ou seja, a IA
    recebe o mesmo conhecimento/instruções nos três números. Não chama a
    API real da Anthropic — responder_com_ia é mockado.
    """
    import responder_ia

    chamadas_ia = []

    def _fake_responder_com_ia(mensagem, nome=None, historico=None, contexto_comercial=None):
        chamadas_ia.append({
            "mensagem": mensagem,
            "historico": historico,
            "contexto_comercial": contexto_comercial,
        })
        return "resposta simulada da IA (nao e chamada real)"

    original_ia = responder_ia.responder_com_ia
    responder_ia.responder_com_ia = _fake_responder_com_ia
    monkeypatches = [(responder_ia, "responder_com_ia", original_ia)]
    try:
        _mockar_requests_post(monkeypatches)
        _mockar_mala_direta(monkeypatches)

        pergunta = "Quem criou esse chatbot?"
        for numero_empresarial, apelido in ((NUM_1, "94054"), (NUM_2, "2030"), (NUM_3, "2542")):
            numero_cliente = f"5511900003{apelido}"
            _limpar(numero_cliente, numero_empresarial)
            chamadas_ia.clear()

            responder.responder(numero_cliente, pergunta, nome_contato="Cliente Teste", sender_phone_number_id=numero_empresarial)

            assert len(chamadas_ia) == 1, f"[{apelido}] esperava 1 chamada a IA, veio {chamadas_ia}"
            assert chamadas_ia[0]["mensagem"] == pergunta, chamadas_ia[0]
            assert chamadas_ia[0]["historico"] == [], f"[{apelido}] historico deveria ser vazio numa conversa fresca: {chamadas_ia[0]}"
            assert chamadas_ia[0]["contexto_comercial"] is None, f"[{apelido}] sem sinal comercial, contexto deveria ser None: {chamadas_ia[0]}"

            _limpar(numero_cliente, numero_empresarial)

        print("OK  CASO H: pergunta institucional livre chega com mensagem/histórico/contexto "
              "IDÊNTICOS à IA nos três números (mesmo conhecimento/instruções)")
    finally:
        _restaurar(monkeypatches)


if __name__ == "__main__":
    teste_caso_a_94054_recebe_94054_responde()
    teste_caso_b_2030_recebe_2030_responde()
    teste_caso_c_2542_recebe_2542_responde()
    teste_caso_d_mesmo_cliente_tres_numeros_nao_se_misturam()
    teste_caso_e_sem_sender_usa_fallback_numero_padrao()
    teste_ponta_a_ponta_via_webhook_flask_tres_numeros()
    teste_caso_f_ciclo_comercial_completo_consistente_tres_numeros_concorrente()
    teste_caso_g_paridade_deterministica_tres_numeros()
    teste_caso_h_ia_recebe_mesmo_contexto_tres_numeros()
    print("\nTODOS OS TESTES DE REGRESSAO (FASE 3.1P - TRES NUMEROS META) PASSARAM. ZERO mensagens reais enviadas.")
