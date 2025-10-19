from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    OPENAI_API_KEY: str
    MODEL_NAME: str = "gpt-5"
    STT_MODEL: str = "whisper-1"

    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_PRICE_WEEKLY: str  # price_...

    BASE_URL: str  # https://...
    DATABASE_URL: str = "sqlite+aiosqlite:///./data.db"

    FREE_TRIAL_ANALYSES: int = 1
    PREMIUM_WEEKLY_PRICE_EUR: float = 4.99

    BRAND_NAME: str = "AI‑Психолог"
    SHARE_WATERMARK: str = "@AIpsihologProBot"

    ADMIN_PASSWORD: str = "changeme"

settings = Settings()
