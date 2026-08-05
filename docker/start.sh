#!/bin/sh
set -eu

cd /app
export PYTHONPATH="/app:${PYTHONPATH:-}"

DB_URL="${DATABASE_URL:?DATABASE_URL must be set}"
REDIS_URL="${REDIS_URL:?REDIS_URL must be set}"
JWT_SECRET_VALUE="${JWT_SECRET:?JWT_SECRET must be set}"
APP_ENV_VALUE="${APP_ENV:-${ENVIRONMENT:-development}}"

if [ "$APP_ENV_VALUE" = "production" ]; then
  if [ "$JWT_SECRET_VALUE" = "change-me-in-prod-at-least-32-characters-long" ]; then
    echo "Refusing to start production with the default JWT_SECRET." >&2
    exit 1
  fi
  if [ -z "${IDENTITY_BASE_URL:-}" ] && [ -z "${IDENTITY_JWKS_URL:-}" ]; then
    echo "Refusing to start production without IDENTITY_BASE_URL or IDENTITY_JWKS_URL." >&2
    exit 1
  fi
  if [ -z "${DIDDIMAP_BASE_URL:-}" ]; then
    echo "Refusing to start production without DIDDIMAP_BASE_URL." >&2
    exit 1
  fi
  if [ "${PUSH_ENABLED:-false}" = "true" ]; then
    if [ -z "${FCM_PROJECT_ID:-}" ]; then
      echo "Refusing to start production push without FCM_PROJECT_ID." >&2
      exit 1
    fi
    if [ -z "${FCM_SERVICE_ACCOUNT_JSON:-}" ] && [ -z "${FCM_SERVICE_ACCOUNT_FILE:-}" ]; then
      echo "Refusing to start production push without FCM service account credentials." >&2
      exit 1
    fi
  fi
fi

python - <<'PY'
import asyncio
import os
import time

from sqlalchemy.ext.asyncio import create_async_engine

url = os.environ["DATABASE_URL"]


async def ping_once() -> None:
    engine = create_async_engine(url, pool_pre_ping=True)
    try:
        async with engine.connect():
            return
    finally:
        await engine.dispose()


for attempt in range(60):
    try:
        asyncio.run(ping_once())
        break
    except Exception:
        if attempt == 59:
            raise
        time.sleep(2)
PY

python -c "import app_base"
python -m alembic -c /app/alembic.ini upgrade head
exec uvicorn app_base.main:app --host 0.0.0.0 --port 8000
