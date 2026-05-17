import os
from typing import Optional

def responder_com_ia(mensagem: str, nome: Optional[str] = None) -> Optional[str]:
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        sistema = (
            "Você é o assistente virtual do Grupo Sullato, concessionária de veículos em São Paulo. "
            "Trabalha com veículos de passeio e utilitários (vans, pickups, furgões). "
            "Lojas: Sullato Micros e Vans (Av. São Miguel, 7900), Sullato Veículos (Av. São Miguel, 4049/4084), "
            "Sullato Oficina e Peças (Av. Amador Bueno da Veiga, 4222). "
            "Serviços oferecidos: compra, venda, crédito e financiamento, oficina, peças e pós-venda. "
            "Responda sempre em português brasileiro, com tom simpático, profissional e direto, em 1 a 3 frases. "
            "Nunca invente preços, estoque ou condições específicas — oriente o cliente a falar com um consultor ou usar o menu. "
            "Quando fizer sentido, sugira que o cliente escolha uma opção no menu."
        )

        usuario = mensagem if not nome else f"[Cliente: {nome}]\n{mensagem}"

        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=sistema,
            messages=[{"role": "user", "content": usuario}],
        )
        texto = (resp.content[0].text or "").strip()
        return texto if texto else None

    except Exception as e:
        print("⚠️ Claude indisponível:", e)
        return None
