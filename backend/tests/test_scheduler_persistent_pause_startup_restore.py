import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.scheduler.scheduler_manager import SchedulerManager


def build_manager():
    manager = SchedulerManager.__new__(
        SchedulerManager
    )

    manager.config = SimpleNamespace(
        enabled=True,
        timezone="UTC",
        jobs={},
    )

    manager.db = object()
    manager._running = False
    manager._jobs = {}
    manager._scheduler = MagicMock()
    manager.register_jobs = MagicMock()

    return manager


def build_lock_manager():
    lock_manager = MagicMock()

    lock_manager.ensure_indexes = AsyncMock()
    lock_manager.cleanup_expired = AsyncMock()

    return lock_manager


def build_job_logger():
    job_logger = MagicMock()

    job_logger.ensure_indexes = AsyncMock()

    return job_logger


def test_start_restores_persisted_pause_before_scheduler_start():
    manager = build_manager()

    job_a = SimpleNamespace(id="job_a")
    job_b = SimpleNamespace(id="job_b")

    manager._scheduler.get_jobs.return_value = [
        job_a,
        job_b,
    ]

    lock_manager = build_lock_manager()
    job_logger = build_job_logger()

    with (
        patch(
            "core.scheduler.scheduler_manager.get_lock_manager",
            return_value=lock_manager,
        ),
        patch(
            "core.scheduler.scheduler_manager.get_job_logger",
            return_value=job_logger,
        ),
        patch(
            "core.scheduler.scheduler_manager."
            "SchedulerPersistentStateRepository."
            "get_paused_job_ids",
            return_value=["job_b"],
        ),
    ):
        asyncio.run(
            SchedulerManager.start(manager)
        )

    lock_manager.ensure_indexes.assert_awaited_once()
    lock_manager.cleanup_expired.assert_awaited_once()
    job_logger.ensure_indexes.assert_awaited_once()

    manager.register_jobs.assert_called_once_with()

    manager._scheduler.pause_job.assert_called_once_with(
        "job_b"
    )

    manager._scheduler.start.assert_called_once_with()

    assert manager._running is True


def test_start_ignores_unknown_persisted_job():
    manager = build_manager()

    manager._scheduler.get_jobs.return_value = [
        SimpleNamespace(id="job_a"),
    ]

    lock_manager = build_lock_manager()
    job_logger = build_job_logger()

    with (
        patch(
            "core.scheduler.scheduler_manager.get_lock_manager",
            return_value=lock_manager,
        ),
        patch(
            "core.scheduler.scheduler_manager.get_job_logger",
            return_value=job_logger,
        ),
        patch(
            "core.scheduler.scheduler_manager."
            "SchedulerPersistentStateRepository."
            "get_paused_job_ids",
            return_value=["job_missing"],
        ),
    ):
        asyncio.run(
            SchedulerManager.start(manager)
        )

    manager._scheduler.pause_job.assert_not_called()
    manager._scheduler.start.assert_called_once_with()

    assert manager._running is True


def test_start_fails_closed_when_persistent_state_read_fails():
    manager = build_manager()

    manager._scheduler.get_jobs.return_value = [
        SimpleNamespace(id="job_a"),
    ]

    lock_manager = build_lock_manager()
    job_logger = build_job_logger()

    with (
        patch(
            "core.scheduler.scheduler_manager.get_lock_manager",
            return_value=lock_manager,
        ),
        patch(
            "core.scheduler.scheduler_manager.get_job_logger",
            return_value=job_logger,
        ),
        patch(
            "core.scheduler.scheduler_manager."
            "SchedulerPersistentStateRepository."
            "get_paused_job_ids",
            side_effect=RuntimeError(
                "persistent state unavailable"
            ),
        ),
    ):
        with pytest.raises(
            RuntimeError,
            match="persistent state unavailable",
        ):
            asyncio.run(
                SchedulerManager.start(manager)
            )

    manager._scheduler.start.assert_not_called()

    assert manager._running is False


def test_disabled_scheduler_never_reads_persistent_state():
    manager = build_manager()

    manager.config.enabled = False

    with patch(
        "core.scheduler.scheduler_manager."
        "SchedulerPersistentStateRepository."
        "get_paused_job_ids",
    ) as repository:
        asyncio.run(
            SchedulerManager.start(manager)
        )

    repository.assert_not_called()
    manager.register_jobs.assert_not_called()
    manager._scheduler.start.assert_not_called()

    assert manager._running is False
