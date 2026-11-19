import asyncio
from pathlib import Path
import sys
from types import ModuleType

from modules.scheduler_trigger import wake_loop


_ENV_KEYS = (
    "EDARSA_ENV",
    "APP_ENV",
    "ENVIRONMENT",
    "EDARSA_RUNTIME_ROLE",
    "EDARSA_RUNTIME_ROLE_REQUIRED",
    "EDARSA_SCHEDULER_TRIGGER_ENABLED",
    "SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_ENABLED",
    "SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_INTERVAL_SECONDS",
)


def _clear(monkeypatch):
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def _production_web_enabled(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PRODUCTION")
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE", "PRODUCTION_WEB")
    monkeypatch.setenv("EDARSA_SCHEDULER_TRIGGER_ENABLED", "true")
    monkeypatch.setenv(
        "SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_ENABLED",
        "true",
    )


def test_production_wake_is_strictly_runtime_scoped(monkeypatch):
    _production_web_enabled(monkeypatch)
    assert wake_loop.production_wake_eligible() is True

    monkeypatch.setenv("EDARSA_ENV", "PREVIEW")
    assert wake_loop.production_wake_eligible() is False

    monkeypatch.setenv("EDARSA_ENV", "PRODUCTION")
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE", "PREVIEW_WEB")
    assert wake_loop.production_wake_eligible() is False


def test_production_wake_requires_trigger_flag(monkeypatch):
    _production_web_enabled(monkeypatch)
    monkeypatch.setenv("EDARSA_SCHEDULER_TRIGGER_ENABLED", "false")
    assert wake_loop.production_wake_eligible() is False


def test_production_wake_respects_interval(monkeypatch):
    _clear(monkeypatch)
    assert wake_loop.wake_interval_seconds() == 300

    monkeypatch.setenv(
        "SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_INTERVAL_SECONDS",
        "600",
    )
    assert wake_loop.wake_interval_seconds() == 600

    monkeypatch.setenv(
        "SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_INTERVAL_SECONDS",
        "5",
    )
    assert wake_loop.wake_interval_seconds() == 60


def test_production_wake_invokes_only_canonical_job(monkeypatch):
    calls = []

    class FakeManager:
        async def run_job_now(self, job_id):
            calls.append(job_id)
            return {"status": "executed", "job_id": job_id}

    fake_scheduler = ModuleType("core.scheduler")
    fake_scheduler.get_scheduler_manager = lambda _db: FakeManager()
    monkeypatch.setitem(sys.modules, "core.scheduler", fake_scheduler)

    result = asyncio.run(wake_loop._run_once(object()))

    assert calls == ["sync_comercial_abiertas_v2"]
    assert result["status"] == "executed"


def test_production_wake_reuses_distributed_lock_contract():
    source = Path(wake_loop.__file__).read_text(encoding="utf-8")
    assert 'OWNER_LOCK_ID = "sync_comercial_abiertas_v2_wake_owner"' in source
    assert "get_lock_manager" in source
    assert "start_heartbeat_loop" in source
    assert "core.scheduler.jobs.sync_comercial_abiertas_v2_job" not in source
