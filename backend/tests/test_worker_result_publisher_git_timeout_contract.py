import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUBLISHER = ROOT / "tools/mirror_sync/universal_job_result_publisher.py"


def load_publisher():
    spec = importlib.util.spec_from_file_location(
        "result_publisher_git_timeout_contract",
        PUBLISHER,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_git_timeout_contract_present():
    text = PUBLISHER.read_text(encoding="utf-8")

    assert "GIT_TIMEOUT_SECONDS" in text
    assert "EDARSAHUB_RESULT_GIT_TIMEOUT_SECONDS" in text
    assert "timeout=GIT_TIMEOUT_SECONDS" in text
    assert "GIT_TERMINAL_PROMPT" in text
    assert "GIT_TIMEOUT:" in text


def test_git_timeout_becomes_bounded_runtime_error(monkeypatch):
    module = load_publisher()

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd=["git", "fetch", "origin", "worker/results"],
            timeout=30,
        )

    monkeypatch.setattr(module, "run", fake_run)

    try:
        module.git("fetch", "origin", "worker/results")
    except RuntimeError as exc:
        message = str(exc)
        assert "GIT_TIMEOUT:fetch origin worker/results" in message
        assert "timeout=30s" in message
    else:
        raise AssertionError("Expected bounded RuntimeError")


def test_result_branch_isolation_remains_active():
    text = PUBLISHER.read_text(encoding="utf-8")

    assert '"worker/results"' in text
    assert "RESULT_BRANCH" in text
    assert 'refs/heads/{RESULT_BRANCH}' in text
    assert 'refs/heads/{QUEUE_BRANCH}' not in text


def test_single_writer_lock_remains_flock_based():
    text = PUBLISHER.read_text(encoding="utf-8")

    assert "fcntl.flock" in text
    assert "LOCK_EX | fcntl.LOCK_NB" in text
