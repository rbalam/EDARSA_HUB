import importlib.util
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GUARD_PATH = ROOT / "tools/repository_safety/destructive_diff_guard.py"


def load_guard():
    spec = importlib.util.spec_from_file_location(
        "destructive_diff_guard_runtime_contract",
        GUARD_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_runtime_auth_files_remain_critical():
    guard = load_guard()

    assert guard.critical("backend/modules/auth/service.py")
    assert guard.critical("backend/modules/auth/repository.py")
    assert guard.critical("backend/modules/auth/routes.py")
    assert guard.critical("backend/modules/auth/lockout_repository.py")
    assert guard.critical("backend/modules/auth/context_service.py")


def test_historical_auth_backups_are_not_critical():
    guard = load_guard()

    assert not guard.critical(
        "backend/modules/auth/service.py.bak_20260607_063008"
    )
    assert not guard.critical(
        "backend/modules/auth/repository.py.backup_20260607_063008"
    )
    assert not guard.critical(
        "backend/modules/auth/service.py.bak"
    )
    assert not guard.critical(
        "backend/modules/auth/repository.py.backup"
    )


def test_server_and_core_security_are_critical():
    guard = load_guard()

    assert guard.critical("backend/server.py")
    assert guard.critical("backend/core/security.py")


def test_sync_and_bootstrap_are_critical():
    guard = load_guard()

    assert guard.critical("tools/mirror_sync/apply_remote_update.sh")
    assert guard.critical("tools/bootstrap/example.sh")


def test_binary_file_at_is_utf8_decode_safe(monkeypatch):
    guard = load_guard()

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout=b"\xba\xffbinary\n",
            stderr=b"",
        )

    monkeypatch.setattr(guard.subprocess, "run", fake_run)

    value = guard.file_at("HEAD", "backend/server.py")

    assert isinstance(value, str)
    assert "binary" in value


def test_noncritical_binary_path_is_not_read(monkeypatch):
    guard = load_guard()

    def fail_file_at(*args, **kwargs):
        raise AssertionError("file_at must not run for non-critical paths")

    monkeypatch.setattr(guard, "file_at", fail_file_at)

    assert guard.validate_file_loss(
        "BASE",
        "HEAD",
        "exports/example.bson",
    ) == []
