from pathlib import Path

import pytest

from modules.scheduler_runtime import policy
from modules.scheduler_runtime import preview_closed_sales_wake as wake


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server.py"
WAKE = (
    ROOT
    / "modules"
    / "scheduler_runtime"
    / "preview_closed_sales_wake.py"
)
OPEN_WAKE = (
    ROOT
    / "modules"
    / "scheduler_runtime"
    / "preview_sales_wake.py"
)
CLOSED_JOB = (
    ROOT
    / "core"
    / "scheduler"
    / "jobs"
    / "sync_comercial_v2_job.py"
)


_ENV_KEYS = (
    "EDARSA_ENV",
    "APP_ENV",
    "ENVIRONMENT",
    "EDARSA_RUNTIME_ROLE",
    "EDARSA_RUNTIME_ROLE_REQUIRED",
    "SCHEDULER_SYNC_COMERCIAL_V2_ENABLED",
    "SCHEDULER_SYNC_COMERCIAL_V2_INTERVAL_SECONDS",
)


def _clear(monkeypatch):
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_preview_web_closed_sales_wake_uses_canonical_15_minute_interval(
    monkeypatch,
):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PREVIEW")
    monkeypatch.setenv(
        "EDARSA_RUNTIME_ROLE",
        policy.PREVIEW_WEB,
    )

    assert wake.preview_closed_sales_wake_eligible() is True
    assert wake.wake_interval_seconds() == 900


@pytest.mark.parametrize(
    "role",
    [policy.PRODUCTION_WEB, policy.PRODUCTION_SCHEDULER],
)
def test_production_roles_cannot_start_preview_closed_sales_wake(
    monkeypatch,
    role,
):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PRODUCTION")
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE", role)
    monkeypatch.setenv(
        "SCHEDULER_SYNC_COMERCIAL_V2_ENABLED",
        "true",
    )

    assert wake.preview_closed_sales_wake_eligible() is False


def test_closed_sales_wake_respects_existing_disable_flag(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PREVIEW")
    monkeypatch.setenv(
        "EDARSA_RUNTIME_ROLE",
        policy.PREVIEW_WEB,
    )
    monkeypatch.setenv(
        "SCHEDULER_SYNC_COMERCIAL_V2_ENABLED",
        "false",
    )

    assert wake.preview_closed_sales_wake_eligible() is False


def test_closed_sales_wake_uses_canonical_wrapper_and_persistent_pause():
    source = WAKE.read_text(encoding="utf-8")

    assert 'JOB_ID = "sync_comercial_v2"' in source
    assert "manager.run_job_now(JOB_ID)" in source
    assert "execute_sync_comercial_v2(" not in source
    assert "SchedulerPersistentStateRepository.get_paused_job_ids()" in source
    assert "_administratively_paused()" in source


def test_closed_sales_and_open_sales_have_distinct_owner_locks():
    closed_source = WAKE.read_text(encoding="utf-8")
    open_source = OPEN_WAKE.read_text(encoding="utf-8")

    assert (
        'OWNER_LOCK_ID = "preview_sync_comercial_v2_wake_owner"'
        in closed_source
    )
    assert (
        'OWNER_LOCK_ID = "preview_sync_comercial_abiertas_v2_wake_owner"'
        in open_source
    )
    assert (
        "preview_sync_comercial_abiertas_v2_wake_owner"
        not in closed_source
    )


def test_server_wires_both_scoped_wakes_without_full_preview_scheduler():
    server = SERVER.read_text(encoding="utf-8")

    assert "start_preview_sales_wake(db)" in server
    assert "start_preview_closed_sales_wake(db)" in server
    assert "await stop_preview_sales_wake()" in server
    assert "await stop_preview_closed_sales_wake()" in server
    assert "if should_start_embedded_scheduler():" in server


def test_closed_sales_job_remains_dynamic_and_transversal():
    source = CLOSED_JOB.read_text(encoding="utf-8")

    assert "UnidadesService.get_all()" in source
    assert "if 'SOFTRESTAURANT' in sistema:" in source
    assert "elif 'MPRO' in sistema:" in source
    assert "solo_unidades" in source
    assert "SYNC_INCREMENTAL_DAYS" in source
