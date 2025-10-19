# Базовый образ с Python 3.11 и системными зависимостями
FROM python:3.11-slim

# Системные пакеты (на будущее: Pillow, aiohttp и пр. будут ставиться без сюрпризов)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Обновим pip и установим зависимости заранее
COPY requirements.txt .
RUN pip install -U pip setuptools wheel && pip install -r requirements.txt

# Копируем код
COPY . .

# Uvicorn запустит FastAPI, Render подставит $PORT
ENV PORT=10000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
