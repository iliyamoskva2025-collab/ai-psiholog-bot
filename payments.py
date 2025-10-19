import stripe
from fastapi import APIRouter, Request, HTTPException
from settings import settings
from db import SessionLocal, get_or_create_user, grant_weekly_premium, create_payment, mark_payment_paid

router = APIRouter(prefix="/stripe", tags=["stripe"])
stripe.api_key = settings.STRIPE_SECRET_KEY

@router.post("/create-checkout-session")
async def create_checkout_session(request: Request):
    data = await request.json()
    tg_id = data.get("tg_id")
    if not tg_id:
        raise HTTPException(400, "tg_id required")
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": settings.STRIPE_PRICE_WEEKLY, "quantity": 1}],
        success_url=f"{settings.BASE_URL}/success?t={tg_id}",
        cancel_url=f"{settings.BASE_URL}/cancel",
        metadata={"tg_id": tg_id},
    )
    async with SessionLocal() as dbs:
        user = await get_or_create_user(dbs, tg_id)
        await create_payment(dbs, user.id, session.id, int(settings.PREMIUM_WEEKLY_PRICE_EUR))
    return {"url": session.url}

@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(400, str(e))
    etype = event.get("type")
    obj = event.get("data", {}).get("object", {})
    if etype == "checkout.session.completed":
        tg_id = obj.get("metadata", {}).get("tg_id")
        if tg_id:
            async with SessionLocal() as dbs:
                user = await get_or_create_user(dbs, tg_id)
                await grant_weekly_premium(dbs, user.id)
                await mark_payment_paid(dbs, obj.get("id"))
    return {"ok": True}
