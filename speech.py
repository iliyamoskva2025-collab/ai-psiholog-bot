import httpx
from openai import OpenAI
from settings import settings

async def stt_audio_url_to_text(file_url: str) -> str:
    async with httpx.AsyncClient() as client:
        audio_bytes = (await client.get(file_url)).content
        oai = OpenAI(api_key=settings.OPENAI_API_KEY)
        trans = oai.audio.transcriptions.create(
            model=settings.STT_MODEL,
            file=("audio.ogg", audio_bytes)
        )
        return trans.text.strip()
