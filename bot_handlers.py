from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.enums import ParseMode
from settings import settings
from db import SessionLocal, get_or_create_user, has_premium, increment_free, log_analysis
from analysis import analyze_text
from letters import make_letter
from speech import stt_audio_url_to_text
from share_image import make_share_card
import httpx

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

BUY_KB = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="💳 Разблокировать Premium", callback_data="buy")]]
)

POST_PREMIUM_KB = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📤 Поделиться результатом", callback_data="share")],
    [InlineKeyboardButton(text="💌 Письмо от моего имени", callback_data="letter")]
])

@dp.message(F.text.startswith("/start"))
async def start(message: Message):
    ref = None
    parts = message.text.split()
    if len(parts) > 1 and parts[1] != message.from_user.id:
        ref = parts[1]
    async with SessionLocal() as session:
        await get_or_create_user(session, str(message.from_user.id), referrer_tg_id=ref)
    await message.answer(
        f"👋 Привет! Я — <b>{settings.BRAND_NAME}</b>.\n"
        "Отправь <b>голос</b> или <b>текст</b> — я скажу, кто ты на самом деле.\n\n"
        f"🎁 Бесплатно: {settings.FREE_TRIAL_ANALYSES} анализ. Дальше — Premium (4.99€/неделя).",
        parse_mode=ParseMode.HTML
    )

@dp.callback_query(F.data == "buy")
async def buy(cb: CallbackQuery):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{settings.BASE_URL}/stripe/create-checkout-session", json={"tg_id": str(cb.from_user.id)})
        url = resp.json().get("url")
    await cb.message.answer(f"Оплата: {url}")
    await cb.answer()

@dp.message(F.voice)
async def handle_voice(message: Message):
    file = await bot.get_file(message.voice.file_id)
    file_url = f"https://api.telegram.org/file/bot{settings.TELEGRAM_BOT_TOKEN}/{file.file_path}"
    text = await stt_audio_url_to_text(file_url)
    await process_analysis(message, text, input_type="voice")

@dp.message(F.text)
async def handle_text(message: Message):
    await process_analysis(message, message.text, input_type="text")

async def process_analysis(message: Message, input_text: str, input_type: str):
    tg_id = str(message.from_user.id)
    async with SessionLocal() as session:
        user = await get_or_create_user(session, tg_id)
        premium = await has_premium(session, user.id)
        if not premium:
            res = await session.get(type(user), user.id)
            used = res.free_used
            if used >= settings.FREE_TRIAL_ANALYSES:
                await message.reply("Бесплатный анализ уже использован. Разблокируй Premium, чтобы продолжить.", reply_markup=BUY_KB)
                return

        await message.reply("🧠 Анализирую… 5–10 сек…")
        try:
            out, t_in, t_out, hook = await analyze_text(input_text, premium=premium)
            await message.answer(out, parse_mode=ParseMode.HTML)
            if not premium:
                await increment_free(session, user.id)
            await log_analysis(session, user.id, input_type, t_in, t_out)
            if premium:
                await message.answer("Готово. Хочешь поделиться или написать письмо от твоего имени?", reply_markup=POST_PREMIUM_KB)
            else:
                await message.answer("Хочешь полный отчёт + совместимость и карту для сторис?", reply_markup=BUY_KB)
            bot.__dict__.setdefault("hooks", {})[tg_id] = hook
        except Exception:
            await message.answer("Упс, не получилось проанализировать. Попробуй ещё раз.")

@dp.callback_query(F.data == "share")
async def share(cb: CallbackQuery):
    tg_id = str(cb.from_user.id)
    hook = bot.__dict__.get("hooks", {}).get(tg_id, "Это зацепило меня. Проверь, что он скажет про тебя.")
    card = make_share_card(hook, watermark=settings.SHARE_WATERMARK)
    await cb.message.answer_photo(BufferedInputFile(card, filename="share.png"),
        caption=f"Проверь себя: @{(await bot.get_me()).username}")
    await cb.answer()

@dp.callback_query(F.data == "letter")
async def letter(cb: CallbackQuery):
    tg_id = str(cb.from_user.id)
    async with SessionLocal() as session:
        user = await get_or_create_user(session, tg_id)
        from db import has_premium
        if not await has_premium(session, user.id):
            await cb.message.answer("Опция доступна в Premium.", reply_markup=BUY_KB)
            await cb.answer()
            return
    await cb.message.answer("💌 О чём написать? Кратко опиши ситуацию одной фразой.")
    bot.__dict__.setdefault("await_letter_ctx", set()).add(tg_id)
    await cb.answer()

@dp.message()
async def letter_context(message: Message):
    tg_id = str(message.from_user.id)
    waiting = bot.__dict__.setdefault("await_letter_ctx", set())
    if tg_id not in waiting:
        return
    waiting.remove(tg_id)
    await message.reply("Пишу письмо… 5–10 сек…")
    txt = await make_letter(message.text)
    await message.answer(txt)
