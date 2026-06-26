#!/usr/bin/env bash
set -euo pipefail

celery -A app.celery_app beat -l info
