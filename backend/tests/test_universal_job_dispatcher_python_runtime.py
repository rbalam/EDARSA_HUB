import importlib.util
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
    spec.loader.exec_module(module)
    return module


def test_dispatcher_prefers_repository_virtualenv():
    module = load_dispatcher()

    expected = ROOT / ".venv" / "bin" / "python"

    if expected.is_file() and os.access(expected, os.X_OK):
        assert module.PYTHON_BIN == str(expected)


def test_dispatcher_falls_back_to_sys_executable(
    tmp_path,
    monkeypatch,
):
    module = load_dispatcher()

    monkeypatch.setattr(module, "ROOT", tmp_path)
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

    monkeypatch.setattr(module, "ROOT", tmp_path)
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
        "backend/tests/test_example.py",
    ]


def test_all_internal_python_subprocesses_are_canonical():
    text = DISPATCHER.read_text(encoding="utf-8")

    # sys.executable remains only as resolver fallback.
    assert text.count("sys.executable") == 1

    assert (
        'cmd = [PYTHON_BIN, "-m", '
        '"py_compile", *paths]'
    ) in text

    assert (
        'cmd = [PYTHON_BIN, "-m", '
        '"pytest", "-q", *paths]'
    ) in text

    assert "/usr/bin/python3" not in text
    assert "/usr/local/bin/python3" not in text
