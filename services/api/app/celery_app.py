"""
File: services/api/app/celery_app.py
Layer: Application Source
Purpose: Implements celery app behavior for the application source.
Dependencies: Celery, Redis, stoa_core
"""

from __future__ import annotations

import logging

from celery import Celery
from celery.signals import task_prerun

from app.config import get_settings
from app.services.task_context import assert_allowed_task
from stoa_core.redis.security import celery_broker_ssl_config, validate_redis_security

logger = logging.getLogger(__name__)
settings = get_settings()
validate_redis_security(settings)

celery_app = Celery(
    "stoa_api",
    broker=settings.broker_url,
    backend=settings.result_backend,
    include=[
        "app.tasks.ingestion",
        "app.tasks.intelligence",
        "app.tasks.competitive",
        "app.tasks.campaigns",
        "app.tasks.content",
        "app.tasks.knowledge",
        "app.tasks.integrations",
        "app.tasks.enrichment",
    ],
)

_beat_schedule = {
    "competitive-rescan-daily": {
        "task": "enrichment.schedule_competitor_rescans",
        "schedule": 60 * 60 * 24,
        "options": {"expires": 3600},
    },
    "stale-insight-refresh-weekly": {
        "task": "intelligence.schedule_precompute",
        "schedule": 60 * 60 * 24 * 7,
        "options": {"expires": 3600},
    },
    "integration-sync-daily": {
        "task": "integrations.schedule_syncs",
        "schedule": 60 * 60 * 24,
        "options": {"expires": 3600},
    },
    "enrichment-job-cleanup-daily": {
        "task": "enrichment.cleanup_stale_jobs",
        "schedule": 60 * 60 * 24,
        "options": {"expires": 3600},
    },
}

_conf: dict = {
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "UTC",
    "enable_utc": True,
    "task_acks_late": True,
    "task_reject_on_worker_lost": True,
    "worker_prefetch_multiplier": 1,
    "broker_connection_retry_on_startup": True,
    "task_default_queue": "stoa",
    "task_create_missing_queues": True,
    "beat_schedule": _beat_schedule,
}

_ssl = celery_broker_ssl_config(settings)
if _ssl:
    _conf.update(_ssl)

celery_app.conf.update(**_conf)


@task_prerun.connect
def _guard_task_execution(task_id: str, task, *args, **kwargs) -> None:  # noqa: ARG001
    """Handles  guard task execution logic for the surrounding Stoa workflow.

    Args:
        task_id (str): Input value used by this workflow step.
        task (Any): Input value used by this workflow step.
    """
    try:
        assert_allowed_task(task.name)
    except ValueError:
        logger.error("Rejected disallowed task %s (id=%s)", task.name, task_id)
        raise
