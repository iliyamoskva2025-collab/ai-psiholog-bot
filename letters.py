from openai import OpenAI
from settings import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

async def make_letter(context: str, tone: str = "искренний, тёплый, кинематографичный") -> str:
    messages = [
        {"role": "system", "content": "Ты — автор сильных личных писем. Максимум эмоции, минимум воды."},
        {"role": "user", "content": f"Напиши письмо от моего имени. Тон: {tone}. Вдохновляйся, но не копируй.\nКонтекст:\n{context}"}
    ]
    resp = client.chat.completions.create(
        model=settings.MODEL_NAME,
        messages=messages,
        temperature=0.7,
        max_tokens=700,
    )
    return resp.choices[0].message.content.strip()
