import importlib.util
import os
import sys
import os
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
DISPATCHER = ROOT / "tools/mirror_sync/universal_job_dispatcher.py"


def load_dispatcher():
    spec = importlib.util.spec_from_file_location(
        "universal_job_dispatcher_runtime_test",
        DISPATCHER,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    mirror_sync_dir = str(DISPATCHER.parent)
    inserted = mirror_sync_dir not in sys.path
    if inserted:
        sys.path.insert(0, mirror_sync_dir)
    try:
        spec.loader.exec_module(module)
    finally:
        if inserted:
            sys.path.remove(mirror_sync_dir)
    return module


def test_dispatcher_prefers_runtime_virtualenv():
    module = load_dispatcher()

    expected = Path("/root/.venv/bin/python")

    if expected.is_file() and os.access(expected, os.X_OK):
        assert module.PYTHON_BIN == str(expected)


def test_dispatcher_falls_back_to_sys_executable(
    tmp_path,
    monkeypatch,
):
    module = load_dispatcher()

    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(
        module,
        "RUNTIME_PYTHON",
        tmp_path / "missing-runtime-python",
    )
    monkeypatch.setattr(
        module.sys,
        "executable",
        "/fallback/python",
    )

    assert (
        module.resolve_canonical_python()
        == "/fallback/python"
    )


def test_dispatcher_prefers_executable_repo_python(
    tmp_path,
    monkeypatch,
):
    module = load_dispatcher()

    repo_python = (
        tmp_path / ".venv" / "bin" / "python"
    )
    repo_python.parent.mkdir(parents=True)

    repo_python.write_text(
        "#!/bin/sh\nexit 0\n",
        encoding="utf-8",
    )
    repo_python.chmod(0o755)

    (tmp_path / ".venv" / "pyvenv.cfg").write_text(
        "home = /usr/local/bin\n"
        "include-system-site-packages = false\n"
        "version = 3.11.16\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(
        module,
        "RUNTIME_PYTHON",
        tmp_path / "missing-runtime-python",
    )
    monkeypatch.setattr(
        module.sys,
        "executable",
        "/fallback/python",
    )

    assert (
        module.resolve_canonical_python()
        == str(repo_python)
    )


def test_py_compile_uses_canonical_python(
    tmp_path,
    monkeypatch,
):
    module = load_dispatcher()
    calls = []

    def fake_run(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(
            returncode=0,
            stdout="ok",
        )

    monkeypatch.setattr(module, "run", fake_run)
    monkeypatch.setattr(
        module,
        "PYTHON_BIN",
        "/canonical/python",
    )

    result = module.run_check(
        tmp_path,
        {
            "type": "py_compile",
            "paths": ["backend/example.py"],
        },
    )

    assert calls[0][0] == [
        "/canonical/python",
        "-m",
        "py_compile",
        "backend/example.py",
    ]


def test_pytest_uses_canonical_python(
    tmp_path,
    monkeypatch,
):
    module = load_dispatcher()
    calls = []

    def fake_run(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(
            returncode=0,
            stdout="ok",
        )

    monkeypatch.setattr(module, "run", fake_run)
    monkeypatch.setattr(
        module,
        "PYTHON_BIN",
        "/canonical/python",
    )

    (tmp_path / "backend").mkdir()

    result = module.run_check(
        tmp_path,
        {
            "type": "pytest",
            "paths": [
                "backend/tests/test_example.py"
            ],
        },
    )

    assert calls[0][0] == [
        "/canonical/python",
        "-m",
        "pytest",
        "-q",
        "tests/test_example.py",
    ]


def test_all_internal_python_subprocesses_are_canonical():
    text = DISPATCHER.read_text(encoding="utf-8")

    # sys.executable remains only as resolver fallback.
    assert text.count("sys.executable") == 1

    assert (
        'cmd = [PYTHON_BIN, "-m", '
        '"py_compile", *paths]'
    ) in text

    assert 'pytest_args = ["-q"]' in text
    assert 'pytest_args.extend(["-p", "no:cacheprovider"])' in text
    assert 'cmd = [PYTHON_BIN, "-m", "pytest", *pytest_args, *paths]' in text

    assert "/usr/bin/python3" not in text
    assert "/usr/local/bin/python3" not in text


def test_pytest_loads_missing_backend_runtime_env(tmp_path, monkeypatch):
    module = load_dispatcher()
    calls = []

    backend = tmp_path / "backend"
    backend.mkdir()
    (backend / ".env").write_text(
        "EDARSAHUB_SQL_HOST=db.example\n"
        "EDARSAHUB_SQL_PORT=1433\n"
        "EDARSAHUB_SQL_DATABASE=EDARSAHUB\n"
        "EDARSAHUB_SQL_USER=worker\n"
        "EDARSAHUB_SQL_PASSWORD=value with spaces\n",
        encoding="utf-8",
    )

    def fake_run(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout="ok")

    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "run", fake_run)
    monkeypatch.delenv("EDARSAHUB_SQL_HOST", raising=False)
    monkeypatch.delenv("EDARSAHUB_SQL_PORT", raising=False)
    monkeypatch.delenv("EDARSAHUB_SQL_DATABASE", raising=False)
    monkeypatch.delenv("EDARSAHUB_SQL_USER", raising=False)
    monkeypatch.delenv("EDARSAHUB_SQL_PASSWORD", raising=False)

    module.run_check(
        tmp_path,
        {"type": "pytest", "paths": ["backend/tests/test_example.py"]},
    )

    env_extra = calls[0][1]["env_extra"]
    assert env_extra["PYTHONPATH"] == os.pathsep.join(
        (
            str(backend),
            str(tmp_path),
        )
    )
    assert env_extra["EDARSAHUB_SQL_HOST"] == "db.example"
    assert env_extra["EDARSAHUB_SQL_PORT"] == "1433"
    assert env_extra["EDARSAHUB_SQL_DATABASE"] == "EDARSAHUB"
    assert env_extra["EDARSAHUB_SQL_USER"] == "worker"
    assert env_extra["EDARSAHUB_SQL_PASSWORD"] == "value with spaces"


def test_backend_runtime_env_does_not_override_process_env(tmp_path, monkeypatch):
    module = load_dispatcher()
    backend = tmp_path / "backend"
    backend.mkdir()
    (backend / ".env").write_text(
        "EDARSAHUB_SQL_HOST=file-host\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setenv("EDARSAHUB_SQL_HOST", "process-host")

    loaded = module.load_backend_runtime_env()

    assert "EDARSAHUB_SQL_HOST" not in loaded


def test_frontend_build_reuses_canonical_frontend_toolchain(tmp_path, monkeypatch):
    module = load_dispatcher()
    calls = []

    frontend = tmp_path / "frontend"
    frontend.mkdir()
    canonical_modules = tmp_path / "canonical-frontend" / "node_modules"
    canonical_bin = canonical_modules / ".bin"
    canonical_bin.mkdir(parents=True)

    def fake_run(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout="ok")

    monkeypatch.setattr(module, "ROOT", tmp_path / "canonical-root")
    module.ROOT.mkdir()
    (module.ROOT / "frontend").mkdir()
    monkeypatch.setattr(module, "run", fake_run)
    monkeypatch.setenv("PATH", "/usr/bin")

    real_modules = module.ROOT / "frontend" / "node_modules"
    real_bin = real_modules / ".bin"
    real_bin.mkdir(parents=True)

    result = module.run_check(
        tmp_path,
        {"type": "frontend_build", "directory": "frontend"},
    )

    assert result["status"] == "PASS"
    assert calls[0][0] == ["yarn", "build"]
    env_extra = calls[0][1]["env_extra"]
    assert env_extra["NODE_PATH"] == str(real_modules)
    assert env_extra["PATH"].startswith(str(real_bin) + ":")


def test_integrate_push_uses_only_repository_local_credential_helper():
    text = DISPATCHER.read_text(encoding="utf-8")

    assert 'git("config", "--local", "--get", "credential.helper", cwd=ROOT, check=False)' in text
    assert '"credential.helper="' in text
    assert 'f"credential.helper={credential_helper}"' in text
    assert '"push",REMOTE' in text
    assert "gh auth git-credential" not in text
