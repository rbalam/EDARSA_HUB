import asyncio
from pathlib import Path
import sys
from types import ModuleType

import pytest
from fastapi import HTTPException

from modules.scheduler_trigger_preview import routes


_ENV_KEYS = (
    "EDARSA_ENV",
    "APP_ENV",
    "ENVIRONMENT",
    "EDARSA_RUNTIME_ROLE",
    "EDARSA_RUNTIME_ROLE_REQUIRED",
    "EDARSA_PREVIEW_SCHEDULER_TRIGGER_ENABLED",
    "EDARSA_PREVIEW_SCHEDULER_TRIGGER_KEY",
)


def _clear(monkeypatch):
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def _preview_enabled(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PREVIEW")
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE", "PREVIEW_WEB")
    monkeypatch.setenv(
        "EDARSA_PREVIEW_SCHEDULER_TRIGGER_ENABLED",
        "true",
    )
    monkeypatch.setenv(
        "EDARSA_PREVIEW_SCHEDULER_TRIGGER_KEY",
        "unit-test-secret",
    )


def test_trigger_fails_closed_outside_preview(monkeypatch):
    _preview_enabled(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PRODUCTION")

    with pytest.raises(HTTPException) as exc:
        routes._authorize_trigger(
            "Bearer unit-test-secret",
            None,
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "PREVIEW_SCHEDULER_TRIGGER_PREVIEW_ONLY"


def test_trigger_requires_preview_web_role(monkeypatch):
    _preview_enabled(monkeypatch)
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE", "PRODUCTION_WEB")

    with pytest.raises(HTTPException) as exc:
        routes._authorize_trigger(
            "Bearer unit-test-secret",
            None,
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "PREVIEW_SCHEDULER_TRIGGER_PREVIEW_WEB_ONLY"


def test_trigger_is_disabled_by_default(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PREVIEW")
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE", "PREVIEW_WEB")
    monkeypatch.setenv(
        "EDARSA_PREVIEW_SCHEDULER_TRIGGER_KEY",
        "unit-test-secret",
    )

    with pytest.raises(HTTPException) as exc:
        routes._authorize_trigger(
            "Bearer unit-test-secret",
            None,
        )

    assert exc.value.status_code == 503
    assert exc.value.detail == "PREVIEW_SCHEDULER_TRIGGER_DISABLED"


def test_trigger_requires_dedicated_secret(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PREVIEW")
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE", "PREVIEW_WEB")
    monkeypatch.setenv(
        "EDARSA_PREVIEW_SCHEDULER_TRIGGER_ENABLED",
        "true",
    )

    with pytest.raises(HTTPException) as exc:
        routes._authorize_trigger("Bearer anything", None)

    assert exc.value.status_code == 503
    assert exc.value.detail == "PREVIEW_SCHEDULER_TRIGGER_NOT_CONFIGURED"


def test_trigger_rejects_wrong_secret(monkeypatch):
    _preview_enabled(monkeypatch)

    with pytest.raises(HTTPException) as exc:
        routes._authorize_trigger("Bearer wrong", None)

    assert exc.value.status_code == 401
    assert exc.value.detail == "PREVIEW_SCHEDULER_TRIGGER_UNAUTHORIZED"


def test_trigger_uses_existing_owner_contracts():
    assert (
        routes.OPEN_OWNER_LOCK_ID
        == "preview_sync_comercial_abiertas_v2_wake_owner"
    )
    assert (
        routes.CLOSED_OWNER_LOCK_ID
        == "preview_sync_comercial_v2_wake_owner"
    )
    assert routes.OPEN_JOB_ID == "sync_comercial_abiertas_v2"
    assert routes.CLOSED_JOB_ID == "sync_comercial_v2"


def test_busy_owner_skips_external_execution(monkeypatch):
    _preview_enabled(monkeypatch)

    async def fake_acquire(*args, **kwargs):
        return None

    monkeypatch.setattr(routes, "_acquire_owner_lock", fake_acquire)

    result = asyncio.run(
        routes.trigger_sync_comercial_abiertas_v2(
            authorization="Bearer unit-test-secret",
            x_edarsa_scheduler_key=None,
        )
    )

    assert result["status"] == "owner_active"
    assert result["execution_observed"] is False
    assert result["job_id"] == "sync_comercial_abiertas_v2"


def test_open_sales_trigger_invokes_only_canonical_job(monkeypatch):
    _preview_enabled(monkeypatch)

    calls = []

    class FakeLock:
        async def release(self):
            return True

    async def fake_acquire(*args, **kwargs):
        return FakeLock()

    class FakeManager:
        async def run_job_now(self, job_id):
            calls.append(job_id)
            return {"status": "executed", "job_id": job_id}

    fake_scheduler = ModuleType("core.scheduler")
    fake_scheduler.get_scheduler_manager = lambda db=None: FakeManager()

    fake_mongo_stub = ModuleType("core.mongo_stub")
    fake_mongo_stub.get_stub_database = lambda: object()

    monkeypatch.setattr(routes, "_acquire_owner_lock", fake_acquire)
    monkeypatch.setitem(sys.modules, "core.scheduler", fake_scheduler)
    monkeypatch.setitem(sys.modules, "core.mongo_stub", fake_mongo_stub)

    result = asyncio.run(
        routes.trigger_sync_comercial_abiertas_v2(
            authorization="Bearer unit-test-secret",
            x_edarsa_scheduler_key=None,
        )
    )

    assert calls == ["sync_comercial_abiertas_v2"]
    assert result["status"] == "executed"
    assert result["execution_observed"] is True


def test_closed_sales_trigger_preserves_administrative_pause(monkeypatch):
    _preview_enabled(monkeypatch)

    class FakeLock:
        async def release(self):
            return True

    async def fake_acquire(*args, **kwargs):
        return FakeLock()

    monkeypatch.setattr(routes, "_acquire_owner_lock", fake_acquire)
    monkeypatch.setattr(
        routes,
        "_closed_sales_administratively_paused",
        lambda: True,
    )

    result = asyncio.run(
        routes.trigger_sync_comercial_v2(
            authorization="Bearer unit-test-secret",
            x_edarsa_scheduler_key=None,
        )
    )

    assert result["status"] == "administratively_paused"
    assert result["execution_observed"] is False


def test_trigger_module_does_not_import_business_jobs_directly():
    source = Path(routes.__file__).read_text(encoding="utf-8")

    assert "core.scheduler.jobs.sync_comercial_abiertas_v2_job" not in source
    assert "core.scheduler.jobs.sync_comercial_v2_job" not in source
