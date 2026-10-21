import asyncio

import pytest
from fastapi import HTTPException

from modules.scheduler_trigger_inventarios import routes


_ENV_KEYS = (
    "EDARSA_ENV",
    "EDARSA_RUNTIME_ROLE",
    "EDARSA_RUNTIME_ROLE_REQUIRED",
    "EDARSA_INVENTORY_SCHEDULER_TRIGGER_ENABLED",
    "EDARSA_SCHEDULER_TRIGGER_KEY",
    "SCHEDULER_SYNC_COMPRAS_ENABLED",
    "SCHEDULER_SYNC_COMPRAS_EXECUTION_ENABLED",
)


def _clear(monkeypatch):
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def _production_ready(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PRODUCTION")
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE", "PRODUCTION_WEB")
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE_REQUIRED", "1")
    monkeypatch.setenv(
        "EDARSA_INVENTORY_SCHEDULER_TRIGGER_ENABLED",
        "true",
    )
    monkeypatch.setenv("EDARSA_SCHEDULER_TRIGGER_KEY", "secret")
    monkeypatch.setenv("SCHEDULER_SYNC_COMPRAS_ENABLED", "true")
    monkeypatch.setenv(
        "SCHEDULER_SYNC_COMPRAS_EXECUTION_ENABLED",
        "true",
    )


def test_health_requires_production(monkeypatch):
    _production_ready(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PREVIEW")

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            routes.inventory_scheduler_trigger_health(
                authorization=None,
                x_edarsa_scheduler_key="secret",
            )
        )

    assert exc.value.status_code == 403


def test_health_reports_execution_guard(monkeypatch):
    _production_ready(monkeypatch)
    monkeypatch.setenv(
        "SCHEDULER_SYNC_COMPRAS_EXECUTION_ENABLED",
        "false",
    )

    result = asyncio.run(
        routes.inventory_scheduler_trigger_health(
            authorization=None,
            x_edarsa_scheduler_key="secret",
        )
    )

    assert result["status"] == "degraded"
    assert result["job_id"] == "sync_compras"
    assert result["execution_enabled"] is False


def test_trigger_rejects_disabled_execution_guard(monkeypatch):
    _production_ready(monkeypatch)
    monkeypatch.setenv(
        "SCHEDULER_SYNC_COMPRAS_EXECUTION_ENABLED",
        "false",
    )

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            routes.trigger_sync_compras(
                authorization=None,
                x_edarsa_scheduler_key="secret",
            )
        )

    assert exc.value.status_code == 503
    assert exc.value.detail == "SYNC_COMPRAS_EXECUTION_GUARD_DISABLED"


def test_trigger_returns_real_sync_result(monkeypatch):
    _production_ready(monkeypatch)

    class FakeManager:
        async def run_job_now(self, job_id):
            assert job_id == "sync_compras"
            return {
                "job_id": job_id,
                "status": "SUCCESS",
                "total_processed": 15,
                "total_errors": 0,
            }

    import core.scheduler.scheduler_manager as manager_module

    monkeypatch.setattr(
        manager_module,
        "get_scheduler_manager",
        lambda: FakeManager(),
    )

    result = asyncio.run(
        routes.trigger_sync_compras(
            authorization=None,
            x_edarsa_scheduler_key="secret",
        )
    )

    assert result["job_id"] == "sync_compras"
    assert result["status"] == "SUCCESS"
    assert result["total_processed"] == 15
    assert result["total_errors"] == 0
    assert result["environment"] == "PRODUCTION"
    assert result["runtime_role"] == "PRODUCTION_WEB"


def test_trigger_rejects_false_success(monkeypatch):
    _production_ready(monkeypatch)

    class FakeManager:
        async def run_job_now(self, job_id):
            return {
                "job_id": job_id,
                "status": "DISABLED",
                "reason": "execution_guard",
            }

    import core.scheduler.scheduler_manager as manager_module

    monkeypatch.setattr(
        manager_module,
        "get_scheduler_manager",
        lambda: FakeManager(),
    )

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            routes.trigger_sync_compras(
                authorization=None,
                x_edarsa_scheduler_key="secret",
            )
        )

    assert exc.value.status_code == 503
    assert exc.value.detail["code"] == "SYNC_COMPRAS_NOT_HEALTHY"
    assert exc.value.detail["result"]["status"] == "DISABLED"
