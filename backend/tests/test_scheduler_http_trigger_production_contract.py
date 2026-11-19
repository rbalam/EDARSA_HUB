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
    "EDARSA_SCHEDULER_TRIGGER_ENABLED",
    "EDARSA_SCHEDULER_TRIGGER_KEY",
)


def _clear(monkeypatch):
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def _production_web_enabled(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PRODUCTION")
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE", "PRODUCTION_WEB")
    monkeypatch.setenv("EDARSA_SCHEDULER_TRIGGER_ENABLED", "true")
    monkeypatch.setenv("EDARSA_SCHEDULER_TRIGGER_KEY", "unit-test-secret")


def test_trigger_fails_closed_outside_production(monkeypatch):
    _production_web_enabled(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PREVIEW")
    with pytest.raises(HTTPException) as exc:
        routes._authorize_trigger("Bearer unit-test-secret", None)
    assert exc.value.status_code == 403
    assert exc.value.detail == "SCHEDULER_TRIGGER_PRODUCTION_ONLY"


def test_trigger_requires_production_web_role(monkeypatch):
    _production_web_enabled(monkeypatch)
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE", "PRODUCTION_SCHEDULER")
    with pytest.raises(HTTPException) as exc:
        routes._authorize_trigger("Bearer unit-test-secret", None)
    assert exc.value.status_code == 403
    assert exc.value.detail == "SCHEDULER_TRIGGER_PRODUCTION_WEB_ONLY"


def test_trigger_is_disabled_by_default(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PRODUCTION")
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE", "PRODUCTION_WEB")
    monkeypatch.setenv("EDARSA_SCHEDULER_TRIGGER_KEY", "unit-test-secret")
    with pytest.raises(HTTPException) as exc:
        routes._authorize_trigger("Bearer unit-test-secret", None)
    assert exc.value.status_code == 503
    assert exc.value.detail == "SCHEDULER_TRIGGER_DISABLED"


def test_trigger_requires_dedicated_secret(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PRODUCTION")
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE", "PRODUCTION_WEB")
    monkeypatch.setenv("EDARSA_SCHEDULER_TRIGGER_ENABLED", "true")
    with pytest.raises(HTTPException) as exc:
        routes._authorize_trigger("Bearer anything", None)
    assert exc.value.status_code == 503
    assert exc.value.detail == "SCHEDULER_TRIGGER_NOT_CONFIGURED"


def test_trigger_rejects_wrong_secret(monkeypatch):
    _production_web_enabled(monkeypatch)
    with pytest.raises(HTTPException) as exc:
        routes._authorize_trigger("Bearer wrong", None)
    assert exc.value.status_code == 401
    assert exc.value.detail == "SCHEDULER_TRIGGER_UNAUTHORIZED"


def test_trigger_accepts_bearer_and_dedicated_header(monkeypatch):
    _production_web_enabled(monkeypatch)
    bearer = routes._authorize_trigger("Bearer unit-test-secret", None)
    dedicated = routes._authorize_trigger(None, "unit-test-secret")
    assert bearer["environment"] == "PRODUCTION"
    assert bearer["role"] == "PRODUCTION_WEB"
    assert dedicated["role"] == "PRODUCTION_WEB"


def test_trigger_invokes_only_canonical_protected_job(monkeypatch):
    _production_web_enabled(monkeypatch)
    calls = []

    class FakeManager:
        async def run_job_now(self, job_id):
            calls.append(job_id)
            return {"status": "executed", "job_id": job_id}

    fake_scheduler = ModuleType("core.scheduler")
    fake_scheduler.get_scheduler_manager = lambda _db: FakeManager()
    monkeypatch.setitem(sys.modules, "core.scheduler", fake_scheduler)

    result = asyncio.run(
        routes.trigger_sync_comercial_abiertas_v2(
            authorization="Bearer unit-test-secret",
            x_edarsa_scheduler_key=None,
        )
    )

    assert calls == ["sync_comercial_abiertas_v2"]
    assert result["job_id"] == "sync_comercial_abiertas_v2"
    assert result["runtime_role"] == "PRODUCTION_WEB"


def test_trigger_has_no_temporary_secret_fingerprint_logging():
    source = Path(routes.__file__).read_text(encoding="utf-8")
    assert "SCHEDULER_TRIGGER_SECRET_DIAG" not in source
    assert "_log_trigger_secret_fingerprint" not in source
    assert "core.scheduler.jobs.sync_comercial_abiertas_v2_job" not in source
