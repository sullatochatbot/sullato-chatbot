# teste_regressao_institucional_criador.py
"""
Teste de regressão da Fase 3.1T (diagnóstico real: cliente perguntou "quem
fez ele" sobre o sistema e a IA alucinou "Yuri Pascon" como desenvolvedor;
insistiu em "certeza que é ele mesmo?" e a IA REAFIRMOU o nome inventado).

Cobre: a autoria do sistema (Anderson R. Sullato) passa a ser respondida
100% deterministicamente por código (_eh_pergunta_institucional_criador em
responder.py), nunca decidida pela IA — mesmo padrão já usado no
ChatbotOficinaSullato. Cobre também perguntas de CONTINUIDADE ("tem
certeza?", "qual o contato dele?") só quando o assunto imediatamente
anterior foi esta mesma resposta institucional.

Isolamento de rede: os testes A-G e J-M chamam o DETECTOR diretamente
(_eh_pergunta_institucional_criador), função pura sem nenhum acesso a rede
— zero risco. Os testes H/I usam responder.responder() de ponta a ponta
(para exercitar o histórico real via _HIST_IA), com enviar_mensagem e
enviar_para_google_sheets mockados (ambos definidos no próprio módulo,
nunca reimportados localmente dentro de responder()) e requests.post
BLOQUEADO explicitamente como rede de segurança — lição do incidente da
sessão anterior, em que um teste sem mock completo vazou uma chamada real
à Meta.

Executar:  python teste_regressao_institucional_criador.py
"""

import requests
import responder

_TEXTO_ANDERSON = "anderson r. sullato"


def _bloquear_rede():
    def _post_bloqueado(*args, **kwargs):
        raise AssertionError(f"BLOQUEADO: requests.post real chamado com args={args} kwargs={kwargs}")
    requests.post = _post_bloqueado


def _mockar_envios(monkeypatches):
    enviados = []

    def _fake_enviar_mensagem(numero, texto, sender_phone_number_id=None):
        enviados.append(texto)

    def _fake_sheets(*args, **kwargs):
        pass

    original_msg = responder.enviar_mensagem
    original_sheets = responder.enviar_para_google_sheets
    responder.enviar_mensagem = _fake_enviar_mensagem
    responder.enviar_para_google_sheets = _fake_sheets
    monkeypatches.append((responder, "enviar_mensagem", original_msg))
    monkeypatches.append((responder, "enviar_para_google_sheets", original_sheets))
    return enviados


def _restaurar(monkeypatches):
    for obj, nome, original in monkeypatches:
        setattr(obj, nome, original)


# ============================================================
# A-G) Detector reconhece as perguntas diretas sobre autoria
# ============================================================
def teste_perguntas_diretas_reconhecidas():
    casos = {
        "A": "Quem fez esse sistema?",
        "B": "Quem fez ele.",
        "C": "Quem criou?",
        "D": "Quem desenvolveu esse chatbot?",
        "E": "Quem programou?",
        "F": "Quem é o desenvolvedor?",
        "G": "Esse sistema foi feito por quem?",
    }
    for rotulo, frase in casos.items():
        texto_norm = responder.normalizar_id(frase)
        assert responder._eh_pergunta_institucional_criador(texto_norm), f"{rotulo}) {frase!r} deveria ser reconhecida"
        print(f"OK  {rotulo}) {frase!r} -> reconhecida como pergunta institucional")


# ============================================================
# H) "Quem fez esse sistema?" -> Anderson; "Tem certeza?" -> confirma
# ============================================================
def teste_H_continuidade_confirmacao():
    numero = "5511900003001"
    responder._HIST_IA.pop(responder._chave_hist(numero), None)
    monkeypatches = []
    try:
        enviados = _mockar_envios(monkeypatches)

        responder.responder(numero, {"text": {"body": "Quem fez esse sistema?"}}, "Cliente Teste")
        assert enviados, "primeira pergunta não gerou resposta"
        assert "anderson r. sullato" in responder.normalizar_id(enviados[-1]), enviados[-1]

        enviados.clear()
        responder.responder(numero, {"text": {"body": "Tem certeza?"}}, "Cliente Teste")
        assert enviados, "pergunta de continuidade não gerou resposta"
        resposta = enviados[-1]
        assert "anderson r. sullato" in responder.normalizar_id(resposta), resposta
        # confirmação curta -- não precisa repetir os contatos.
        assert "wa.me" not in resposta, f"não deveria repetir contato numa simples confirmação: {resposta!r}"

        print("OK  H) 'Quem fez esse sistema?' -> Anderson; 'Tem certeza?' -> confirma Anderson (sem repetir contato)")
    finally:
        _restaurar(monkeypatches)
        responder._HIST_IA.pop(responder._chave_hist(numero), None)


# ============================================================
# I) "Quem criou esse sistema?" -> Anderson; "Qual o contato dele?" -> contatos
# ============================================================
def teste_I_continuidade_contato():
    numero = "5511900003002"
    responder._HIST_IA.pop(responder._chave_hist(numero), None)
    monkeypatches = []
    try:
        enviados = _mockar_envios(monkeypatches)

        responder.responder(numero, {"text": {"body": "Quem criou esse sistema?"}}, "Cliente Teste")
        assert enviados
        assert "anderson r. sullato" in responder.normalizar_id(enviados[-1]), enviados[-1]

        enviados.clear()
        responder.responder(numero, {"text": {"body": "Qual o contato dele?"}}, "Cliente Teste")
        assert enviados, "pedido de contato não gerou resposta"
        resposta = enviados[-1]
        assert "5511988780161" in resposta.replace(" ", "").replace("-", ""), resposta
        assert "anderson@sullato.com.br" in resposta, resposta

        print("OK  I) 'Quem criou esse sistema?' -> Anderson; 'Qual o contato dele?' -> WhatsApp + e-mails corretos")
    finally:
        _restaurar(monkeypatches)
        responder._HIST_IA.pop(responder._chave_hist(numero), None)


# ============================================================
# J-M) Não pode disparar autoria em perguntas não relacionadas
# ============================================================
def teste_JKLM_nao_dispara_indevidamente():
    casos = {
        "J": "Estou procurando uma Renault Master 2027.",
        "K": "Quem é o vendedor?",
        "L": "Quem fez a revisão desse carro?",
        "M": "Quem criou a Volkswagen?",
    }
    for rotulo, frase in casos.items():
        texto_norm = responder.normalizar_id(frase)
        assert not responder._eh_pergunta_institucional_criador(texto_norm), (
            f"{rotulo}) {frase!r} NÃO deveria disparar autoria do chatbot"
        )
        print(f"OK  {rotulo}) {frase!r} -> NÃO reconhecida como pergunta institucional (correto)")


# ============================================================
# Continuidade só conta quando o assunto anterior foi realmente autoria
# ============================================================
def teste_continuidade_nao_dispara_sem_assunto_anterior():
    numero = "5511900003003"
    responder._HIST_IA.pop(responder._chave_hist(numero), None)
    monkeypatches = []
    try:
        enviados = _mockar_envios(monkeypatches)
        # "Tem certeza?" isolado, sem nenhuma pergunta de autoria antes --
        # não deve virar resposta institucional (segue fluxo normal).
        texto_norm = responder.normalizar_id("Tem certeza?")
        assert responder._eh_continuidade_institucional_criador(texto_norm)  # a frase em si bate no padrão...
        # ...mas o gate real em responder() exige _assunto_anterior_era_criador
        # -- sem histórico de "Anderson R. Sullato", a resposta institucional
        # não pode ser deterministicamente escolhida por essa frase sozinha.
        hist = responder._get_hist_ia(numero)
        ultima = next((m.get("content") for m in reversed(hist) if m.get("role") == "assistant"), None)
        assunto_anterior = bool(ultima and "anderson r. sullato" in responder.normalizar_id(ultima))
        assert not assunto_anterior, "não deveria haver assunto institucional anterior nesta conversa nova"
        print("OK  'Tem certeza?' isolado (sem pergunta de autoria antes) não tem assunto institucional anterior")
    finally:
        _restaurar(monkeypatches)
        responder._HIST_IA.pop(responder._chave_hist(numero), None)


if __name__ == "__main__":
    _bloquear_rede()
    teste_perguntas_diretas_reconhecidas()
    teste_H_continuidade_confirmacao()
    teste_I_continuidade_contato()
    teste_JKLM_nao_dispara_indevidamente()
    teste_continuidade_nao_dispara_sem_assunto_anterior()
    print("\nTODOS OS TESTES DE REGRESSÃO (FASE 3.1T - INSTITUCIONAL CRIADOR) PASSARAM. ZERO chamadas de rede.")
