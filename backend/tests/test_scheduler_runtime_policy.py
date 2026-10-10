import pytest

from modules.scheduler_runtime import policy


_ENV_KEYS = (
    "EDARSA_ENV",
    "APP_ENV",
    "ENVIRONMENT",
    "EDARSA_RUNTIME_ROLE",
    "EDARSA_RUNTIME_ROLE_REQUIRED",
    "SCHEDULER_ENABLED",
)


def _clear(monkeypatch):
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_legacy_default_is_preserved_only_during_staged_cutover(monkeypatch):
    _clear(monkeypatch)

    snapshot = policy.runtime_policy_snapshot()

    assert snapshot["role"] == policy.LEGACY_EMBEDDED
    assert snapshot["legacy_fallback_active"] is True
    assert policy.should_start_embedded_scheduler() is True


def test_required_role_fails_closed_when_missing(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE_REQUIRED", "1")

    assert policy.should_start_embedded_scheduler() is False


@pytest.mark.parametrize("role", [policy.PREVIEW_WEB, policy.PRODUCTION_WEB])
def test_web_roles_never_start_embedded_scheduler(monkeypatch, role):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE", role)
    monkeypatch.setenv("SCHEDULER_ENABLED", "true")

    assert policy.should_start_embedded_scheduler() is False


def test_production_scheduler_role_never_starts_inside_web_backend(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PRODUCTION")
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE", policy.PRODUCTION_SCHEDULER)

    assert policy.should_start_embedded_scheduler() is False


def test_standalone_scheduler_requires_production_and_explicit_role(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PRODUCTION")
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE", policy.PRODUCTION_SCHEDULER)
    monkeypatch.setenv("SCHEDULER_ENABLED", "true")

    snapshot = policy.require_standalone_production_scheduler()

    assert snapshot["environment"] == "PRODUCTION"
    assert snapshot["role"] == policy.PRODUCTION_SCHEDULER
    assert snapshot["role_explicit"] is True


def test_standalone_scheduler_rejects_preview(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PREVIEW")
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE", policy.PRODUCTION_SCHEDULER)

    with pytest.raises(
        RuntimeError,
        match="PRODUCTION_SCHEDULER_REQUIRES_PRODUCTION_ENVIRONMENT",
    ):
        policy.require_standalone_production_scheduler()


def test_standalone_scheduler_rejects_disabled_scheduler(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_ENV", "PRODUCTION")
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE", policy.PRODUCTION_SCHEDULER)
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")

    with pytest.raises(RuntimeError, match="PRODUCTION_SCHEDULER_DISABLED"):
        policy.require_standalone_production_scheduler()


def test_invalid_runtime_role_fails_closed(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("EDARSA_RUNTIME_ROLE", "SOMETHING_ELSE")

    with pytest.raises(RuntimeError, match="INVALID_EDARSA_RUNTIME_ROLE"):
        policy.runtime_role()
