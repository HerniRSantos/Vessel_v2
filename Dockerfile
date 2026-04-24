FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Python deps
RUN pip install --no-cache-dir fastapi uvicorn python-dotenv websockets requests

# Copy app
COPY backend/ /app/backend/
COPY frontend/dist/ /app/frontend/dist/
COPY .env /app/.env
COPY launcher.py /app/launcher.py

EXPOSE 8000

CMD ["python3", "launcher.py"]