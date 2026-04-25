FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System libs needed by psycopg2-binary at runtime + curl for healthcheck.
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        curl ca-certificates libpq5 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application code.
COPY backend/ ./backend/
# Seed assets — read on first boot when DB is empty.
COPY data/pep_watchlist.json ./data/pep_watchlist.json
COPY data/lots_parsed.json ./data/lots_parsed.json

# Storage strategy:
#   - Postgres (recommended): set DATABASE_URL=postgresql://... via Railway add-on.
#   - SQLite (single-instance only): mount Railway Volume at /app/data via dashboard.
# Do NOT use Dockerfile `VOLUME` — Railway rejects it.

ENV DATABASE_URL="" \
    ALLOWED_ORIGINS="*" \
    AUTOSEED=1 \
    PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://127.0.0.1:${PORT}/healthz || exit 1

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
