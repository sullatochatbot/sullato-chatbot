# responder_ia.py
import os

def responder_com_ia(mensagem: str, nome: str | None = None) -> str | None:
    """
    Gera resposta curta usando OpenAI se configurado.
    Compatível com responder_com_ia(msg) e responder_com_ia(msg, nome).
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    # Tratar chave ausente ou em espera
    if not api_key or api_key.strip().upper() == "EM_ESPERA":
        return _fallback_resposta(mensagem, nome)

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        sistema = (
            "Você é o assistente da Sullato Micros e Vans. "
            "Seja educado, objetivo e útil. "
            "Direcione para botões do menu quando fizer sentido. "
            "Responda em 1 a 3 frases."
        )
        usuario = mensagem if not nome else f"Cliente: {nome}\nMensagem: {mensagem}"

        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": sistema},
                {"role": "user", "content": usuario},
            ],
            temperature=0.4,
            max_tokens=220,
        )
        texto = (resp.choices[0].message.content or "").strip()
        return texto or _fallback_resposta(mensagem, nome)
    except Exception as e:
        print("⚠️ IA indisponível, usando fallback. Detalhe:", e)
        return _fallback_resposta(mensagem, nome)

def _fallback_resposta(mensagem: str, nome: str | None = None) -> str:
    saud = (nome or "tudo bem").title()
    return (
        f"{saud}? Para agilizar, me diga se você quer *comprar*, *vender*, saber *endereço*, "
        f"falar sobre *crédito* ou *oficina*. Se preferir, posso te mostrar o *menu* com botões."
    )
