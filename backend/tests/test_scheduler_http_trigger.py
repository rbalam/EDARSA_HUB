import asyncio
from pathlib import Path
import sys
from types import ModuleType

import pytest
from fastapi import HTTPException

from modules.scheduler_trigger import routes


_ENV_KEYS = (
    "EDARSA_ENV",
    "APP_ENV",
    "ENVIRONMENT",
    "EDARSA_RUNTIME_ROLE",
    "EDARSA_RUNTIME_ROLE_REQUIRED",
    "SCHEDULER_ENABLED",
    "EDARSA_SCHEDULER_TRIGGER_ENABLED",
    "EDARSA_SCHEDULER_TRIGGER_KEY",
)


def _clear(monkeypatch):
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def _production_enabled(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PRODUCTION")
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE", "LEGACY_EMBEDDED")
    monkeypatch.setenv("EDARSA_SCHEDULER_TRIGGER_ENABLED", "true")
    monkeypatch.setenv("EDARSA_SCHEDULER_TRIGGER_KEY", "unit-test-secret")


def test_trigger_fails_closed_outside_production(monkeypatch):
    _production_enabled(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PREVIEW")

    with pytest.raises(HTTPException) as exc:
        routes._authorize_trigger(
            "Bearer unit-test-secret",
            None,
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "SCHEDULER_TRIGGER_PRODUCTION_ONLY"


def test_trigger_is_disabled_by_default(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PRODUCTION")
    monkeypatch.setenv("EDARSA_SCHEDULER_TRIGGER_KEY", "unit-test-secret")

    with pytest.raises(HTTPException) as exc:
        routes._authorize_trigger(
            "Bearer unit-test-secret",
            None,
        )

    assert exc.value.status_code == 503
    assert exc.value.detail == "SCHEDULER_TRIGGER_DISABLED"


def test_trigger_requires_dedicated_secret(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PRODUCTION")
    monkeypatch.setenv("EDARSA_SCHEDULER_TRIGGER_ENABLED", "true")

    with pytest.raises(HTTPException) as exc:
        routes._authorize_trigger("Bearer anything", None)

    assert exc.value.status_code == 503
    assert exc.value.detail == "SCHEDULER_TRIGGER_NOT_CONFIGURED"


def test_trigger_rejects_wrong_secret(monkeypatch):
    _production_enabled(monkeypatch)

    with pytest.raises(HTTPException) as exc:
        routes._authorize_trigger("Bearer wrong", None)

    assert exc.value.status_code == 401
    assert exc.value.detail == "SCHEDULER_TRIGGER_UNAUTHORIZED"


def test_trigger_accepts_bearer_and_dedicated_header(monkeypatch):
    _production_enabled(monkeypatch)

    bearer = routes._authorize_trigger(
        "Bearer unit-test-secret",
        None,
    )
    dedicated = routes._authorize_trigger(
        None,
        "unit-test-secret",
    )

    assert bearer["environment"] == "PRODUCTION"
    assert dedicated["environment"] == "PRODUCTION"


def test_trigger_invokes_only_canonical_protected_job(monkeypatch):
    _production_enabled(monkeypatch)

    calls = []

    class FakeManager:
        async def run_job_now(self, job_id):
            calls.append(job_id)
            return {"status": "executed", "job_id": job_id}

    events = iter(
        [
            {
                "run_id": "old-run",
                "accion": "FINISH",
                "fecha_accion": "2026-10-10T20:00:00Z",
                "exito": True,
            },
            {
                "run_id": "new-run",
                "accion": "FINISH",
                "fecha_accion": "2026-10-10T20:05:00Z",
                "exito": True,
            },
        ]
    )

    async def fake_latest_event():
        return next(events)

    fake_scheduler_manager = ModuleType(
        "core.scheduler.scheduler_manager"
    )
    fake_scheduler_manager.get_scheduler_manager = (
        lambda: FakeManager()
    )
    monkeypatch.setitem(
        sys.modules,
        "core.scheduler.scheduler_manager",
        fake_scheduler_manager,
    )
    monkeypatch.setattr(
        routes,
        "_latest_event",
        fake_latest_event,
    )

    result = asyncio.run(
        routes.trigger_sync_comercial_abiertas_v2(
            authorization="Bearer unit-test-secret",
            x_edarsa_scheduler_key=None,
        )
    )

    assert calls == ["sync_comercial_abiertas_v2"]
    assert result["job_id"] == "sync_comercial_abiertas_v2"
    assert result["execution_observed"] is True
    assert result["last_event"]["run_id"] == "new-run"


def test_trigger_module_does_not_import_protected_job_directly():
    source = Path(routes.__file__).read_text(encoding="utf-8")
    assert "core.scheduler.jobs.sync_comercial_abiertas_v2_job" not in source
