#!/usr/bin/env bash
set -euo pipefail
celery -A app.celery_app worker -l info --pool=solo &
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
