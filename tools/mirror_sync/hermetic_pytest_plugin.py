"""Hermetic READ_ONLY pytest sandbox plugin for EDARSAHUB Universal Worker.

Activated ONLY when the dispatcher runs an opt-in HERMETIC_READONLY pytest
check (EDARSAHUB_PYTEST_HERMETIC=1). Enforces runtime fail-closed isolation:
- Strips real SQL/Mongo/secret/token environment variables and blocks .env loading.
- Injects only inert RFC-2606 non-routable placeholders needed for module-import config parsing.
- Denies all AF_INET/AF_INET6 outbound network sockets (HERMETIC_NETWORK_DENIED).
- Denies pymssql/pyodbc SQL connections (HERMETIC_SQL_DENIED).
- Provides minimal allowlisted env builder and bounded POSIX resource limits.
"""
from __future__ import annotations

import os
import socket
from typing import Callable

HERMETIC_ISOLATION_PROFILE = "HERMETIC_READONLY"
HERMETIC_PYTEST_MAX_SECONDS = 180
HERMETIC_MAX_FSIZE_BYTES = 64 * 1024 * 1024

_SENSITIVE_ENV_TOKENS = (
    "SQL_",
    "MONGO",
    "PASSWORD",
    "SECRET",
    "TOKEN",
    "CREDENTIAL",
    "API_KEY",
    "APIKEY",
    "JWT",
    "AUTH_KEY",
)

HERMETIC_SAFE_PLACEHOLDERS: dict[str, str] = {
    "EDARSAHUB_SQL_HOST": "hermetic-disabled.invalid",
    "EDARSAHUB_SQL_PORT": "0",
    "EDARSAHUB_SQL_DATABASE": "HERMETIC_DISABLED",
    "EDARSAHUB_SQL_USER": "HERMETIC_DISABLED",
    "EDARSAHUB_SQL_PASSWORD": "HERMETIC_DISABLED",
    "JWT_SECRET": "hermetic-disabled-not-a-secret",
}


def build_hermetic_pytest_env(*, pythonpath: str, tmpdir: str, path_env: str = "") -> dict[str, str]:
    """Return a strictly minimal allowlisted environment with zero real credentials."""
    safe_path = path_env.strip() or "/usr/local/bin:/usr/bin:/bin"
    return {
        "PATH": safe_path,
        "HOME": tmpdir,
        "TMPDIR": tmpdir,
        "TEMP": tmpdir,
        "TMP": tmpdir,
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "GIT_TERMINAL_PROMPT": "0",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": pythonpath,
        "EDARSAHUB_PYTEST_HERMETIC": "1",
    }


def make_hermetic_preexec_fn(max_seconds: int = HERMETIC_PYTEST_MAX_SECONDS) -> Callable[[], None] | None:
    """Return a bounded POSIX resource-limit preexec_fn when supported."""
    try:
        import resource
    except Exception:
        return None

    cpu_limit = max(10, min(int(max_seconds), HERMETIC_PYTEST_MAX_SECONDS))

    def _apply_limits() -> None:
        try:
            soft, hard = resource.getrlimit(resource.RLIMIT_CPU)
            target_hard = cpu_limit if hard == resource.RLIM_INFINITY else min(hard, cpu_limit)
            target_soft = min(cpu_limit, target_hard)
            resource.setrlimit(resource.RLIMIT_CPU, (target_soft, target_hard))
        except Exception:
            pass
        try:
            soft, hard = resource.getrlimit(resource.RLIMIT_FSIZE)
            target_hard = (
                HERMETIC_MAX_FSIZE_BYTES
                if hard == resource.RLIM_INFINITY
                else min(hard, HERMETIC_MAX_FSIZE_BYTES)
            )
            target_soft = min(HERMETIC_MAX_FSIZE_BYTES, target_hard)
            resource.setrlimit(resource.RLIMIT_FSIZE, (target_soft, target_hard))
        except Exception:
            pass

    return _apply_limits


def _scrub_sensitive_env() -> None:
    for key in list(os.environ.keys()):
        upper = key.upper()
        if any(tok in upper for tok in _SENSITIVE_ENV_TOKENS):
            os.environ.pop(key, None)


def _block_outbound_network() -> None:
    orig_connect = socket.socket.connect
    orig_connect_ex = socket.socket.connect_ex

    def _guarded_connect(self, address):
        if self.family in (socket.AF_INET, socket.AF_INET6):
            raise PermissionError(f"HERMETIC_NETWORK_DENIED:{address}")
        return orig_connect(self, address)

    def _guarded_connect_ex(self, address):
        if self.family in (socket.AF_INET, socket.AF_INET6):
            raise PermissionError(f"HERMETIC_NETWORK_DENIED:{address}")
        return orig_connect_ex(self, address)

    def _guarded_create_connection(address, *args, **kwargs):
        raise PermissionError(f"HERMETIC_NETWORK_DENIED:{address}")

    socket.socket.connect = _guarded_connect  # type: ignore[method-assign]
    socket.socket.connect_ex = _guarded_connect_ex  # type: ignore[method-assign]
    socket.create_connection = _guarded_create_connection  # type: ignore[assignment]


def _block_sql_and_dotenv() -> None:
    for mod_name in ("pymssql", "pyodbc"):
        try:
            mod = __import__(mod_name)
        except Exception:
            mod = None
        if mod is not None and hasattr(mod, "connect"):
            def _deny_sql(*_args, _mod=mod_name, **_kwargs):
                raise PermissionError(f"HERMETIC_SQL_DENIED:{_mod}")
            setattr(mod, "connect", _deny_sql)
    try:
        import dotenv

        dotenv.load_dotenv = lambda *_args, **_kwargs: False  # type: ignore[assignment]
        dotenv.dotenv_values = lambda *_args, **_kwargs: {}  # type: ignore[assignment]
    except Exception:
        pass


def activate_hermetic_sandbox() -> None:
    """Enforce fail-closed env, dotenv, network, and SQL isolation inside pytest."""
    _scrub_sensitive_env()
    for key, value in HERMETIC_SAFE_PLACEHOLDERS.items():
        os.environ[key] = value
    _block_outbound_network()
    _block_sql_and_dotenv()


def pytest_configure(config) -> None:
    del config
    if os.environ.get("EDARSAHUB_PYTEST_HERMETIC") == "1":
        activate_hermetic_sandbox()
