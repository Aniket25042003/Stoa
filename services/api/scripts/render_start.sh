#!/usr/bin/env bash
set -euo pipefail

# Render runs this service as a non-root user. Bind to $PORT on all interfaces.
# Celery solo pool is used for single-worker deployments; scale workers separately in production.
celery -A app.celery_app worker -l info --pool=solo &
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
