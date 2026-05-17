import os
import requests
import tempfile

def transcrever_audio(media_id: str, access_token: str) -> str:
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    if not groq_key:
        print("⚠️ GROQ_API_KEY nao configurada")
        return ""

    try:
        # 1. Obter URL do arquivo na Meta
        headers = {"Authorization": f"Bearer {access_token}"}
        r = requests.get(f"https://graph.facebook.com/v20.0/{media_id}", headers=headers, timeout=10)
        if r.status_code != 200:
            print("⚠️ Erro ao obter info do audio:", r.text)
            return ""
        media_url = r.json().get("url", "")
        if not media_url:
            return ""

        # 2. Baixar o arquivo de audio
        r2 = requests.get(media_url, headers=headers, timeout=30)
        if r2.status_code != 200:
            print("⚠️ Erro ao baixar audio:", r2.status_code)
            return ""

        # 3. Transcrever via Groq Whisper
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp.write(r2.content)
            tmp_path = tmp.name

        from groq import Groq
        client = Groq(api_key=groq_key)
        with open(tmp_path, "rb") as audio_file:
            resultado = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=audio_file,
                language="pt",
                response_format="text"
            )

        os.unlink(tmp_path)
        texto = (resultado or "").strip()
        print(f"🎙️ Transcricao: {texto!r}")
        return texto

    except Exception as e:
        print("❌ Erro na transcricao de audio:", e)
        return ""
