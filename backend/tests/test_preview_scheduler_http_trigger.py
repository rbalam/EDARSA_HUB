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


def _valid_claims():
    return {
        "repository": routes.EXPECTED_REPOSITORY,
        "ref": routes.EXPECTED_REF,
        "workflow_ref": routes.EXPECTED_WORKFLOW_REF,
        "event_name": "workflow_dispatch",
        "sub": f"repo:{routes.EXPECTED_REPOSITORY}:ref:{routes.EXPECTED_REF}",
        "run_id": "12345",
    }


def test_trigger_fails_closed_outside_preview(monkeypatch):
    _preview_enabled(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PRODUCTION")

    with pytest.raises(HTTPException) as exc:
        routes._authorize_trigger("Bearer token")

    assert exc.value.status_code == 403
    assert exc.value.detail == "PREVIEW_SCHEDULER_TRIGGER_PREVIEW_ONLY"


def test_trigger_requires_preview_web_role(monkeypatch):
    _preview_enabled(monkeypatch)
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE", "PRODUCTION_WEB")

    with pytest.raises(HTTPException) as exc:
        routes._authorize_trigger("Bearer token")

    assert exc.value.status_code == 403
    assert exc.value.detail == "PREVIEW_SCHEDULER_TRIGGER_PREVIEW_WEB_ONLY"


def test_trigger_kill_switch_can_disable(monkeypatch):
    _preview_enabled(monkeypatch)
    monkeypatch.setenv(
        "EDARSA_PREVIEW_SCHEDULER_TRIGGER_ENABLED",
        "false",
    )

    with pytest.raises(HTTPException) as exc:
        routes._authorize_trigger("Bearer token")

    assert exc.value.status_code == 503
    assert exc.value.detail == "PREVIEW_SCHEDULER_TRIGGER_DISABLED"


def test_trigger_requires_bearer_oidc(monkeypatch):
    _preview_enabled(monkeypatch)

    with pytest.raises(HTTPException) as exc:
        routes._authorize_trigger(None)

    assert exc.value.status_code == 401
    assert exc.value.detail == "PREVIEW_SCHEDULER_TRIGGER_OIDC_REQUIRED"


def test_authorize_accepts_expected_github_oidc(monkeypatch):
    _preview_enabled(monkeypatch)
    monkeypatch.setattr(
        routes,
        "_decode_github_oidc",
        lambda token: _valid_claims(),
    )

    result = routes._authorize_trigger("Bearer unit-test-oidc")

    assert result["environment"] == "PREVIEW"
    assert result["role"] == "PREVIEW_WEB"
    assert result["oidc_repository"] == routes.EXPECTED_REPOSITORY
    assert result["oidc_ref"] == routes.EXPECTED_REF
    assert result["oidc_event_name"] == "workflow_dispatch"


def test_decode_rejects_wrong_repository(monkeypatch):
    claims = _valid_claims()
    claims["repository"] = "other/repo"

    class FakeKey:
        key = "fake"

    monkeypatch.setattr(
        routes._jwks_client,
        "get_signing_key_from_jwt",
        lambda token: FakeKey(),
    )
    monkeypatch.setattr(
        routes.jwt,
        "decode",
        lambda *args, **kwargs: claims,
    )

    with pytest.raises(HTTPException) as exc:
        routes._decode_github_oidc("token")

    assert exc.value.status_code == 403
    assert exc.value.detail == "PREVIEW_SCHEDULER_TRIGGER_WRONG_REPOSITORY"


def test_decode_rejects_wrong_ref(monkeypatch):
    claims = _valid_claims()
    claims["ref"] = "refs/heads/other"

    class FakeKey:
        key = "fake"

    monkeypatch.setattr(
        routes._jwks_client,
        "get_signing_key_from_jwt",
        lambda token: FakeKey(),
    )
    monkeypatch.setattr(
        routes.jwt,
        "decode",
        lambda *args, **kwargs: claims,
    )

    with pytest.raises(HTTPException) as exc:
        routes._decode_github_oidc("token")

    assert exc.value.status_code == 403
    assert exc.value.detail == "PREVIEW_SCHEDULER_TRIGGER_WRONG_REF"


def test_decode_rejects_wrong_workflow(monkeypatch):
    claims = _valid_claims()
    claims["workflow_ref"] = "rbalam/EDARSA_HUB/.github/workflows/other.yml@refs/heads/Edarsahub_Desarrollo"

    class FakeKey:
        key = "fake"

    monkeypatch.setattr(
        routes._jwks_client,
        "get_signing_key_from_jwt",
        lambda token: FakeKey(),
    )
    monkeypatch.setattr(
        routes.jwt,
        "decode",
        lambda *args, **kwargs: claims,
    )

    with pytest.raises(HTTPException) as exc:
        routes._decode_github_oidc("token")

    assert exc.value.status_code == 403
    assert exc.value.detail == "PREVIEW_SCHEDULER_TRIGGER_WRONG_WORKFLOW"


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
    monkeypatch.setattr(
        routes,
        "_decode_github_oidc",
        lambda token: _valid_claims(),
    )

    async def fake_acquire(*args, **kwargs):
        return None

    monkeypatch.setattr(routes, "_acquire_owner_lock", fake_acquire)

    result = asyncio.run(
        routes.trigger_sync_comercial_abiertas_v2(
            authorization="Bearer unit-test-oidc",
        )
    )

    assert result["status"] == "owner_active"
    assert result["execution_observed"] is False
    assert result["job_id"] == "sync_comercial_abiertas_v2"
    assert result["auth"] == "github_oidc"


def test_open_sales_trigger_invokes_only_canonical_job(monkeypatch):
    _preview_enabled(monkeypatch)
    monkeypatch.setattr(
        routes,
        "_decode_github_oidc",
        lambda token: _valid_claims(),
    )

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
            authorization="Bearer unit-test-oidc",
        )
    )

    assert calls == ["sync_comercial_abiertas_v2"]
    assert result["status"] == "executed"
    assert result["execution_observed"] is True
    assert result["auth"] == "github_oidc"


def test_closed_sales_trigger_preserves_administrative_pause(monkeypatch):
    _preview_enabled(monkeypatch)
    monkeypatch.setattr(
        routes,
        "_decode_github_oidc",
        lambda token: _valid_claims(),
    )

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
            authorization="Bearer unit-test-oidc",
        )
    )

    assert result["status"] == "administratively_paused"
    assert result["execution_observed"] is False


def test_trigger_module_does_not_import_business_jobs_directly():
    source = Path(routes.__file__).read_text(encoding="utf-8")

    assert "core.scheduler.jobs.sync_comercial_abiertas_v2_job" not in source
    assert "core.scheduler.jobs.sync_comercial_v2_job" not in source
    assert "EDARSA_PREVIEW_SCHEDULER_TRIGGER_KEY" not in source


def test_decode_accepts_push_event(monkeypatch):
    claims = _valid_claims()
    claims["event_name"] = "push"

    class FakeKey:
        key = "fake"

    monkeypatch.setattr(
        routes._jwks_client,
        "get_signing_key_from_jwt",
        lambda token: FakeKey(),
    )
    monkeypatch.setattr(
        routes.jwt,
        "decode",
        lambda *args, **kwargs: claims,
    )

    decoded = routes._decode_github_oidc("token")

    assert decoded["event_name"] == "push"
    assert "push" in routes.ALLOWED_EVENTS
