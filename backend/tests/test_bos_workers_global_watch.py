"""Read-only global worker observation contract."""
from datetime import datetime, timezone
from pathlib import Path

from core.scheduler.jobs.bos_workers_global_watch_job import inspect_workers
from core.scheduler.config import SchedulerConfig


def test_missing_queue_is_unknown(tmp_path: Path):
    result = inspect_workers(tmp_path)
    assert result["status"] == "UNKNOWN"


def test_queue_observation_and_stale_detection(tmp_path: Path):
    queue = tmp_path / ".git" / "universal-worker-queue"
    for state in ("pending", "processing", "results", "done", "published", "rejected"):
        (queue / state).mkdir(parents=True)
    (queue / "pending" / "job.json").write_text("{}")
    result = inspect_workers(tmp_path, datetime.now(timezone.utc))
    assert result["status"] == "OBSERVED"
    assert result["queue_counts"]["pending"] == 1
    assert result["github_actions"] == "NOT_CONFIGURED"


def test_scheduler_watch_defaults_to_180_seconds_and_disabled(monkeypatch):
    monkeypatch.delenv("SCHEDULER_BOS_WORKERS_WATCH_ENABLED", raising=False)
    config = SchedulerConfig.from_env()
    job = config.jobs["bos_workers_global_watch"]
    assert job.interval_seconds == 180
    assert job.enabled is False
    assert job.max_instances == 1
