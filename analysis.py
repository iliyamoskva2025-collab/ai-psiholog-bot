from openai import OpenAI
from settings import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM = (
    "Ты — AI‑Психолог. Пиши ёмко (120–170 слов), эмоционально‑честно, но бережно. "
    "Структура: 1) Крючок‑цитата (2–3 строки), 2) Сила и уязвимость (по 2 пункта), "
    "3) Как тебя читают окружающие (2 предложения), 4) 3 практичных шага. "
    "Избегай клише, канцелярита и диагнозов."
)

PREMIUM_ADDON = (
    "Если премиум: добавь секцию ‘Совместимость’ — кому с ним легко/сложно и почему (3–5 предложений)."
)

async def analyze_text(user_text: str, premium: bool) -> tuple[str, int, int, str]:
    messages = [
        {"role": "system", "content": SYSTEM + (" " + PREMIUM_ADDON if premium else "")},
        {"role": "user", "content": f"Разбери мой текст/речь:\n{user_text}"}
    ]
    resp = client.chat.completions.create(
        model=settings.MODEL_NAME,
        messages=messages,
        temperature=0.5,
        max_tokens=520,
    )
    out = resp.choices[0].message.content.strip()
    first_lines = out.split("\n")[:2]
    hook = " ".join([l.strip() for l in first_lines if l.strip()])[:160]
    usage = resp.usage or {}
    return out, int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0)), hook
