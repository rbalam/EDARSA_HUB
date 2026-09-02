import importlib.util
import sys
from pathlib import Path


DISPATCHER = Path("/app/tools/mirror_sync/universal_job_dispatcher.py")


def _load():
    spec = importlib.util.spec_from_file_location(
        "dispatcher_real_venv_contract",
        DISPATCHER,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_resolver_requires_real_repo_venv():
    source = DISPATCHER.read_text(encoding="utf-8")

    resolver = source.split(
        "def resolve_canonical_python()",
        1,
    )[1].split(
        "PYTHON_BIN =",
        1,
    )[0]

    assert 'ROOT / ".venv" / "bin" / "python"' in resolver
    assert 'ROOT / ".venv" / "pyvenv.cfg"' in resolver
    assert "RUNTIME_PYTHON" in resolver
    assert "sys.executable" in resolver


def test_fake_app_venv_is_not_selected():
    module = _load()

    repo_python = Path("/app/.venv/bin/python")
    repo_cfg = Path("/app/.venv/pyvenv.cfg")

    assert repo_python.exists()
    assert not repo_cfg.is_file()

    assert module.resolve_canonical_python() == "/root/.venv/bin/python"


def test_runtime_python_contract_is_preserved():
    module = _load()

    assert str(module.RUNTIME_PYTHON) == "/root/.venv/bin/python"
    assert module.PYTHON_BIN == "/root/.venv/bin/python"


def test_sys_executable_remains_final_fallback(monkeypatch):
    module = _load()

    class MissingPath:
        def is_file(self):
            return False

    monkeypatch.setattr(module, "RUNTIME_PYTHON", MissingPath())

    original_root = module.ROOT
    module.ROOT = Path("/definitely/missing")
    try:
        assert module.resolve_canonical_python() == sys.executable
    finally:
        module.ROOT = original_root
