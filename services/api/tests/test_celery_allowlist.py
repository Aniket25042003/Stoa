"""Celery task allowlist must cover all registered tasks and beat schedule entries."""

from __future__ import annotations

from app.celery_app import celery_app
from app.services.task_context import ALLOWED_CELERY_TASKS


def test_beat_schedule_tasks_are_allowlisted() -> None:
    beat_tasks = {entry["task"] for entry in celery_app.conf.beat_schedule.values()}
    missing = beat_tasks - ALLOWED_CELERY_TASKS
    assert not missing, f"Beat tasks missing from allowlist: {sorted(missing)}"


def test_registered_task_names_are_allowlisted() -> None:
    registered = {name for name in celery_app.tasks if not name.startswith("celery.")}
    # Tasks imported only via API routers may not register until worker include list loads them.
    included_missing = {
        "enrichment.enrich_company",
        "enrichment.seed_competitors_from_onboarding",
        "enrichment.schedule_competitor_rescans",
        "enrichment.cleanup_stale_jobs",
    }
    for task_name in included_missing:
        assert task_name in ALLOWED_CELERY_TASKS
