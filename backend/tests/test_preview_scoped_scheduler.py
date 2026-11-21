from pathlib import Path

import pytest

from modules.scheduler_runtime import policy
from modules.scheduler_runtime import preview_scoped_scheduler as scoped


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server.py"
MANAGER = ROOT / "core" / "scheduler" / "scheduler_manager.py"


_ENV_KEYS = (
    "EDARSA_ENV",
    "APP_ENV",
    "ENVIRONMENT",
    "EDARSA_RUNTIME_ROLE",
)


def _clear(monkeypatch):
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_preview_web_is_eligible(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PREVIEW")
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE", policy.PREVIEW_WEB)

    assert scoped.preview_scoped_scheduler_eligible() is True


@pytest.mark.parametrize(
    "role",
    [policy.PRODUCTION_WEB, policy.PRODUCTION_SCHEDULER],
)
def test_production_roles_are_never_eligible(monkeypatch, role):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PRODUCTION")
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE", role)

    assert scoped.preview_scoped_scheduler_eligible() is False


def test_commercial_jobs_have_external_owners():
    assert scoped.EXTERNAL_OWNER_JOB_IDS == {
        "sync_comercial_abiertas_v2",
        "sync_comercial_v2",
    }


def test_scoped_scheduler_uses_canonical_scheduler_with_exclusions():
    source = (
        ROOT
        / "modules"
        / "scheduler_runtime"
        / "preview_scoped_scheduler.py"
    ).read_text(encoding="utf-8")

    assert "start_scheduler(" in source
    assert "exclude_job_ids=EXTERNAL_OWNER_JOB_IDS" in source
    assert "run_job_now(" not in source


def test_scheduler_manager_supports_runtime_exclusions_without_flag_changes():
    source = MANAGER.read_text(encoding="utf-8")

    assert "async def start(self, exclude_job_ids=None):" in source
    assert "self._scheduler.remove_job(job_id)" in source
    assert "self._jobs.pop(job_id, None)" in source
    assert "SchedulerPersistentStateRepository.get_paused_job_ids()" in source


def test_server_starts_commercial_wakes_and_scoped_scheduler():
    source = SERVER.read_text(encoding="utf-8")

    assert "start_preview_sales_wake(db)" in source
    assert "start_preview_closed_sales_wake(db)" in source
    assert "await start_preview_scoped_scheduler(db)" in source
    assert "if should_start_embedded_scheduler():" in source


def test_disabled_jobs_remain_controlled_by_canonical_config():
    config = (ROOT / "core" / "scheduler" / "config.py").read_text(
        encoding="utf-8"
    )
    source = (
        ROOT
        / "modules"
        / "scheduler_runtime"
        / "preview_scoped_scheduler.py"
    ).read_text(encoding="utf-8")

    assert "config.py" not in source
    assert "SCHEDULER_" not in source
    assert "notifications_dispatcher" not in source
    assert "crm_sync" not in source
    assert "sync_short_comercial" not in source
    assert 'enabled=notif_enabled' in config
