# teste_assistente_comercial.py
"""
Testes locais da Fase 3.1B — assistente_comercial.py

100% local: sem rede, sem WhatsApp, sem Claude/API externa, sem Google Sheets.
Executar:  python teste_assistente_comercial.py
"""

import time
import assistente_comercial as ac


def teste_cenario_a_site():
    numero = "5511900000001"
    ac.limpar_estado(numero)
    texto = (
        "Quero fazer a simulação desse carro Sullato Micros e Vans:\n"
        "KIA BONGO 2011 - 2.5 K-2500 4X2 CS TURBO DIESEL 2P MANUAL\n"
        "https://sullatomicrosevans.com.br/Veiculo/123/detalhes"
    )
    estado = ac.processar_mensagem(numero, texto)
    assert estado is not None
    assert estado["ativo"] is True
    assert estado["origem"] == "site"
    assert estado["url"] == "https://sullatomicrosevans.com.br/Veiculo/123/detalhes"
    assert estado["veiculo"] and "BONGO" in estado["veiculo"].upper()
    assert estado["estagio"] == "veiculo_identificado"
    print("OK  Cenario A (site + veiculo via URL):", estado)
    return estado


def teste_cenario_b_saiba_mais():
    numero = "5511900000002"
    ac.limpar_estado(numero)
    estado = ac.processar_mensagem(numero, "Saiba mais")
    assert estado is not None
    assert estado["ativo"] is True
    assert estado["veiculo"] is None
    assert estado["estagio"] == "aguardando_veiculo"
    print("OK  Cenario B ('Saiba mais'):", estado)
    return estado


def teste_cenario_b_tenho_interesse():
    numero = "5511900000003"
    ac.limpar_estado(numero)
    estado = ac.processar_mensagem(numero, "Tenho interesse")
    assert estado is not None
    assert estado["ativo"] is True
    assert estado["veiculo"] is None
    assert estado["estagio"] == "aguardando_veiculo"
    print("OK  Cenario B ('Tenho interesse'):", estado)
    return estado


def teste_cenario_c_ola_isolado():
    numero = "5511900000004"
    ac.limpar_estado(numero)
    estado = ac.processar_mensagem(numero, "Olá")
    assert estado is None
    assert ac.obter_estado(numero) is None
    print("OK  Cenario C ('Ola' isolado): nenhum estado criado")
    return estado


def teste_cenario_d_sequencia():
    numero = "5511900000005"
    ac.limpar_estado(numero)
    e1 = ac.processar_mensagem(numero, "Saiba mais")
    assert e1["estagio"] == "aguardando_veiculo"

    e2 = ac.processar_mensagem(numero, "Estou procurando uma Master escolar de 20 lugares.")
    assert e2["estagio"] == "veiculo_identificado"
    assert e2["veiculo"] and "master" in e2["veiculo"].lower()
    print("OK  Cenario D (sequencia 'saiba mais' -> veiculo informado):", e2)
    return e2


def teste_respostas_indefinidas_mantem_aguardando():
    numero = "5511900000006"
    respostas_indefinidas = [
        "não sei",
        "ainda não sei",
        "estou pesquisando",
        "quero ver opções",
        "qual vocês têm?",
        "me ajuda a escolher",
    ]
    for resposta in respostas_indefinidas:
        ac.limpar_estado(numero)
        ac.processar_mensagem(numero, "Saiba mais")
        estado = ac.processar_mensagem(numero, resposta)
        assert estado["estagio"] == "aguardando_veiculo", f"Falhou para: {resposta!r} -> {estado}"
        assert estado["veiculo"] is None, f"Falhou para: {resposta!r} -> {estado}"
    print("OK  Respostas indefinidas/negativas mantem 'aguardando_veiculo':", respostas_indefinidas)


def teste_respostas_uteis_avancam_estagio():
    numero = "5511900000007"
    respostas_uteis = [
        "Bongo",
        "Master",
        "Master escolar",
        "van de 20 lugares",
        "utilitário para entrega",
        "carro de passeio",
    ]
    for resposta in respostas_uteis:
        ac.limpar_estado(numero)
        ac.processar_mensagem(numero, "Saiba mais")
        estado = ac.processar_mensagem(numero, resposta)
        assert estado["estagio"] == "veiculo_identificado", f"Falhou para: {resposta!r} -> {estado}"
        assert estado["veiculo"], f"Falhou para: {resposta!r} -> {estado}"
    print("OK  Respostas com informacao minima avancam para 'veiculo_identificado':", respostas_uteis)


def teste_interesse_generico_positivos():
    positivos = [
        "tenho interesse",
        "saiba mais",
        "quero saber mais",
        "gostaria de saber mais",
    ]
    for msg in positivos:
        numero = "5511900000009"
        ac.limpar_estado(numero)
        estado = ac.processar_mensagem(numero, msg)
        assert estado is not None, f"Falhou (deveria ativar) para: {msg!r}"
        assert estado["ativo"] is True, f"Falhou (deveria ativar) para: {msg!r}"
        assert estado["estagio"] == "aguardando_veiculo", f"Falhou para: {msg!r} -> {estado}"
    print("OK  Interesse generico positivo ativa contexto comercial:", positivos)


def teste_interesse_generico_negativos():
    negativos = [
        "não tenho interesse",
        "nao tenho interesse",
        "não quero saber mais",
        "não quero",
    ]
    for msg in negativos:
        numero = "5511900000010"
        ac.limpar_estado(numero)
        estado = ac.processar_mensagem(numero, msg)
        assert estado is None, f"Falhou (nao deveria ativar) para: {msg!r} -> {estado}"
        assert ac.obter_estado(numero) is None, f"Falhou (nao deveria persistir estado) para: {msg!r}"
    print("OK  Negacao antes do gatilho NAO ativa contexto comercial:", negativos)


def teste_expiracao_estado():
    numero = "5511900000008"
    ac.limpar_estado(numero)
    ac.processar_mensagem(numero, "Saiba mais")
    assert ac.tem_contexto_comercial(numero) is True

    # Força expiração manipulando diretamente o timestamp interno do estado
    # (acesso direto às estruturas privadas é aceitável aqui: é um teste do
    # próprio módulo, não código de produção).
    estado_interno = ac._ESTADOS[numero]
    estado_interno["ultima_atualizacao"] = time.time() - (ac._ESTADO_TTL + 1)

    assert ac.obter_estado(numero) is None
    assert ac.tem_contexto_comercial(numero) is False
    assert numero not in ac._ESTADOS  # removido automaticamente ao expirar
    print("OK  Expiracao de estado (TTL) limpa o estado automaticamente")


def teste_feature_flag_default_conservador():
    import os
    valor_original = os.environ.get("ASSISTENTE_COMERCIAL_ATIVO")
    try:
        os.environ.pop("ASSISTENTE_COMERCIAL_ATIVO", None)
        assert ac.assistente_comercial_ativo() is False

        os.environ["ASSISTENTE_COMERCIAL_ATIVO"] = "true"
        assert ac.assistente_comercial_ativo() is True

        os.environ["ASSISTENTE_COMERCIAL_ATIVO"] = "0"
        assert ac.assistente_comercial_ativo() is False
    finally:
        if valor_original is None:
            os.environ.pop("ASSISTENTE_COMERCIAL_ATIVO", None)
        else:
            os.environ["ASSISTENTE_COMERCIAL_ATIVO"] = valor_original
    print("OK  Feature flag ASSISTENTE_COMERCIAL_ATIVO (default False, leitura segura)")


if __name__ == "__main__":
    teste_cenario_a_site()
    teste_cenario_b_saiba_mais()
    teste_cenario_b_tenho_interesse()
    teste_cenario_c_ola_isolado()
    teste_cenario_d_sequencia()
    teste_respostas_indefinidas_mantem_aguardando()
    teste_respostas_uteis_avancam_estagio()
    teste_interesse_generico_positivos()
    teste_interesse_generico_negativos()
    teste_expiracao_estado()
    teste_feature_flag_default_conservador()
    print("\nTODOS OS TESTES LOCAIS PASSARAM.")
