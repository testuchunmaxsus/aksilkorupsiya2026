FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for some Python wheels
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application code (Railway builds with backend/ as context root → repo root copied via .dockerignore)
COPY backend/ ./backend/
COPY data/pep_watchlist.json ./data/pep_watchlist.json
COPY data/lots_parsed.json ./data/lots_parsed.json

# NOTE: persistent storage is provided by Railway Volumes (mounted at /app/data via dashboard).
# Do NOT use Docker `VOLUME` here — Railway rejects it.

ENV DATABASE_URL="sqlite:////app/data/auksionwatch.db" \
    ALLOWED_ORIGINS="*" \
    PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://127.0.0.1:${PORT}/healthz || exit 1

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
