from pathlib import Path

import pytest

from modules.scheduler_runtime import policy
from modules.scheduler_runtime import preview_sales_wake as wake


_ENV_KEYS = (
    "EDARSA_ENV",
    "APP_ENV",
    "ENVIRONMENT",
    "EDARSA_RUNTIME_ROLE",
    "EDARSA_RUNTIME_ROLE_REQUIRED",
    "SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_ENABLED",
    "SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_INTERVAL_SECONDS",
)


def _clear(monkeypatch):
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_preview_web_restores_only_daily_sales_wake(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PREVIEW")
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE", policy.PREVIEW_WEB)

    assert wake.preview_sales_wake_eligible() is True
    assert wake.wake_interval_seconds() == 300


@pytest.mark.parametrize(
    "role",
    [policy.PRODUCTION_WEB, policy.PRODUCTION_SCHEDULER],
)
def test_production_roles_can_never_start_preview_wake(monkeypatch, role):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PRODUCTION")
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE", role)
    monkeypatch.setenv(
        "SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_ENABLED",
        "true",
    )

    assert wake.preview_sales_wake_eligible() is False


def test_preview_wake_respects_existing_job_disable_flag(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PREVIEW")
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE", policy.PREVIEW_WEB)
    monkeypatch.setenv(
        "SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_ENABLED",
        "false",
    )

    assert wake.preview_sales_wake_eligible() is False


def test_preview_wake_uses_canonical_job_wrapper_not_direct_job_source():
    source = (
        Path(__file__).resolve().parents[1]
        / "modules"
        / "scheduler_runtime"
        / "preview_sales_wake.py"
    ).read_text(encoding="utf-8")

    assert 'JOB_ID = "sync_comercial_abiertas_v2"' in source
    assert "manager.run_job_now(JOB_ID)" in source
    assert "run_sync_comercial_abiertas_v2_manual" not in source
    assert (
        'OWNER_LOCK_ID = "preview_sync_comercial_abiertas_v2_wake_owner"'
        in source
    )


def test_server_wires_preview_wake_without_reenabling_full_scheduler():
    server = (
        Path(__file__).resolve().parents[1]
        / "server.py"
    ).read_text(encoding="utf-8")

    assert "start_preview_sales_wake(db)" in server
    assert "await stop_preview_sales_wake()" in server
    assert "if should_start_embedded_scheduler():" in server
