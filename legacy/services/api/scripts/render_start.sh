#!/usr/bin/env bash
# Free Render: one Web service runs API + Celery (no paid Background Worker).
# Solo pool keeps memory predictable on small instances.
set -euo pipefail

celery -A app.celery_app worker -l info --pool=solo --concurrency=1 &
CELERY_PID=$!

cleanup() {
  if kill -0 "$CELERY_PID" 2>/dev/null; then
    kill -TERM "$CELERY_PID" 2>/dev/null || true
    wait "$CELERY_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
