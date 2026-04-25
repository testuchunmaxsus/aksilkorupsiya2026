FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir aiogram==3.27.0 httpx==0.28.1 python-dotenv==1.0.1

COPY bot/ ./bot/

CMD ["python", "-u", "bot/main.py"]
