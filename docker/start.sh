#!/bin/sh
set -eu

cd /app
export PYTHONPATH="/app:${PYTHONPATH:-}"

DB_URL="${DATABASE_URL:?DATABASE_URL must be set}"
REDIS_URL="${REDIS_URL:?REDIS_URL must be set}"
JWT_SECRET_VALUE="${JWT_SECRET:?JWT_SECRET must be set}"

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
