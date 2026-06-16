#!/usr/bin/env bash
# Run from repo root or services/api — starts the Celery worker with the API venv.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -x .venv/bin/celery ]]; then
  echo "Missing .venv — run: python -m venv .venv && pip install -r requirements.txt" >&2
  exit 1
fi

POOL_ARGS=()
if [[ "$(uname -s)" == "Darwin" ]]; then
  POOL_ARGS=(--pool=solo --concurrency=1)
fi

exec .venv/bin/celery -A app.celery_app worker -l info "${POOL_ARGS[@]}" "$@"
