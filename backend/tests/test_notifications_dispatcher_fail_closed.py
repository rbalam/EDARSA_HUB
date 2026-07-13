import inspect

import pytest

from core.scheduler.config import JobConfig, SchedulerConfig
from core.scheduler.jobs.notifications_job import (
    CANONICAL_NOTIFICATION_QUEUE_TABLE,
    NotificationsDispatcherJob,
)


def _job_config(enabled: bool = True) -> JobConfig:
    return JobConfig(
        job_id="notifications_dispatcher",
        job_name="Notifications Dispatcher",
        description="Despacha notificaciones pendientes de la cola",
        enabled=enabled,
        interval_seconds=120,
        batch_size=50,
        timeout_seconds=180,
    )


def _job() -> NotificationsDispatcherJob:
    job = object.__new__(NotificationsDispatcherJob)
    job.config = _job_config()
    return job


def test_notifications_disabled_by_default(monkeypatch):
    monkeypatch.delenv(
        "SCHEDULER_NOTIFICATIONS_ENABLED",
        raising=False,
    )

    config = SchedulerConfig.from_env()

    assert config.jobs["notifications_dispatcher"].enabled is False


def test_notifications_can_be_enabled_explicitly(monkeypatch):
    monkeypatch.setenv(
        "SCHEDULER_NOTIFICATIONS_ENABLED",
        "true",
    )

    config = SchedulerConfig.from_env()

    assert config.jobs["notifications_dispatcher"].enabled is True


@pytest.mark.asyncio
async def test_notifications_job_fails_closed_without_sql_queue(
    monkeypatch,
):
    job = _job()

    monkeypatch.setattr(
        job,
        "_is_sql_queue_available",
        lambda: False,
    )

    with pytest.raises(
        RuntimeError,
        match="cola SQL canónica requerida",
    ):
        await job.execute()


@pytest.mark.asyncio
async def test_queue_is_checked_before_allowed_hours(
    monkeypatch,
):
    job = _job()

    monkeypatch.setattr(
        job,
        "_is_sql_queue_available",
        lambda: True,
    )

    monkeypatch.setattr(
        job,
        "_is_within_allowed_hours",
        lambda: False,
    )

    result = await job.execute()

    assert result["processed_count"] == 0
    assert result["success_count"] == 0
    assert result["failed_count"] == 0
    assert result["details"]["reason"] == "outside_allowed_hours"


def test_notifications_job_has_no_mongo_count_documents():
    source = inspect.getsource(NotificationsDispatcherJob)

    assert "count_documents" not in source
    assert "_get_pending_count" not in source


def test_canonical_queue_name_is_explicit():
    assert (
        CANONICAL_NOTIFICATION_QUEUE_TABLE
        == "dbo.Operativo_Notificaciones_Queue"
    )
