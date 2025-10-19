from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, update, select, desc
from datetime import datetime, timedelta
from settings import settings

engine = create_async_engine(settings.DATABASE_URL, future=True, echo=False)
SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    tg_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    free_used = Column(Integer, default=0)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    referrals_count = Column(Integer, default=0)

class Premium(Base):
    __tablename__ = "premium"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    valid_until = Column(DateTime)

class AnalysisLog(Base):
    __tablename__ = "analysis_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    input_type = Column(String)  # text|voice
    tokens_in = Column(Integer, default=0)
    tokens_out = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class PaymentLog(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    stripe_session = Column(String, unique=True)
    amount_eur = Column(Integer)
    status = Column(String)  # created|paid|failed
    created_at = Column(DateTime, default=datetime.utcnow)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_or_create_user(session: AsyncSession, tg_id: str, referrer_tg_id: str | None = None) -> User:
    res = await session.execute(select(User).where(User.tg_id == tg_id))
    user = res.scalar_one_or_none()
    if user:
        return user
    referrer_id = None
    if referrer_tg_id:
        rr = await session.execute(select(User).where(User.tg_id == referrer_tg_id))
        ref = rr.scalar_one_or_none()
        if ref:
            referrer_id = ref.id
            ref.referrals_count = (ref.referrals_count or 0) + 1
    user = User(tg_id=tg_id, referrer_id=referrer_id)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def has_premium(session: AsyncSession, user_id: int) -> bool:
    res = await session.execute(select(Premium.valid_until).where(Premium.user_id == user_id))
    vu = res.scalar_one_or_none()
    return bool(vu and vu > datetime.utcnow())

async def grant_weekly_premium(session: AsyncSession, user_id: int):
    res = await session.execute(select(Premium).where(Premium.user_id == user_id))
    p = res.scalar_one_or_none()
    if p:
        p.valid_until = max(p.valid_until or datetime.utcnow(), datetime.utcnow()) + timedelta(days=7)
    else:
        p = Premium(user_id=user_id, valid_until=datetime.utcnow() + timedelta(days=7))
        session.add(p)
    await session.commit()

async def increment_free(session: AsyncSession, user_id: int):
    await session.execute(update(User).where(User.id == user_id).values(free_used=User.free_used + 1))
    await session.commit()

async def log_analysis(session: AsyncSession, user_id: int, input_type: str, tokens_in: int, tokens_out: int):
    session.add(AnalysisLog(user_id=user_id, input_type=input_type, tokens_in=tokens_in, tokens_out=tokens_out))
    await session.commit()

async def create_payment(session: AsyncSession, user_id: int, stripe_session: str, amount_eur: int):
    session.add(PaymentLog(user_id=user_id, stripe_session=stripe_session, amount_eur=amount_eur, status="created"))
    await session.commit()

async def mark_payment_paid(session: AsyncSession, stripe_session: str):
    await session.execute(update(PaymentLog).where(PaymentLog.stripe_session == stripe_session).values(status="paid"))
    await session.commit()

async def top_referrers(session: AsyncSession, limit: int = 10):
    res = await session.execute(select(User.tg_id, User.referrals_count).order_by(desc(User.referrals_count)).limit(limit))
    return res.all()
