import asyncio
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from settings import settings
from db import init_db, SessionLocal, top_referrers
from payments import router as stripe_router
from bot_handlers import dp, bot

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(stripe_router)

@app.on_event("startup")
async def on_startup():
    await init_db()
    asyncio.create_task(dp.start_polling(bot))

@app.get("/success")
async def success(t: str):
    return {"ok": True, "tg": t, "message": "Оплата успешна, вернись в Telegram!"}

@app.get("/cancel")
async def cancel():
    return {"ok": False, "message": "Оплата отменена"}

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    async with SessionLocal() as s:
        users = (await s.execute(text("SELECT COUNT(*) FROM users"))).scalar() or 0
        paid = (await s.execute(text("SELECT COUNT(*) FROM payments WHERE status='paid'"))).scalar() or 0
        total = (await s.execute(text("SELECT COALESCE(SUM(amount_eur),0) FROM payments WHERE status='paid'"))).scalar() or 0
        refs = await top_referrers(s, 10)
    rows = ''.join([f"<tr><td>{i+1}</td><td>{tg}</td><td>{cnt}</td></tr>" for i,(tg,cnt) in enumerate(refs)])
    html = """
    <html><head><meta charset='utf-8'><title>Admin</title>
    <style>body{{font:14px system-ui;padding:24px}} table{{border-collapse:collapse}} td,th{{border:1px solid #ccc;padding:6px 10px}}</style>
    </head><body>
      <h2>{brand} — Админка</h2>
      <div>Пользователей: <b>{{users}}</b></div>
      <div>Оплат: <b>{{paid}}</b></div>
      <div>Доход (EUR): <b>{{total}}</b></div>
      <h3>Топ рефералов</h3>
      <table><tr><th>#</th><th>tg_id</th><th>Рефералов</th></tr>{{rows}}</table>
      <p>Stripe Webhook: <code>{base}/stripe/webhook</code></p>
    </body></html>
""".format(brand=settings.BRAND_NAME, base=settings.BASE_URL)
    html = html.replace("{users}", str(users)).replace("{paid}", str(paid)).replace("{total}", str(total)).replace("{rows}", rows)
    return html
