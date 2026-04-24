FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    python-dotenv \
    websockets \
    requests \
    sqlalchemy \
    asyncpg \
    psycopg2-binary \
    structlog

COPY backend/ /app/backend/
COPY frontend/dist/ /app/frontend/dist/
COPY .env /app/.env
COPY launcher.py /app/launcher.py

EXPOSE 8000

CMD ["python3", "launcher.py"]