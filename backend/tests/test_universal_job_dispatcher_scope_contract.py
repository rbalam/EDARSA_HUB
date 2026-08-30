import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DISPATCHER = ROOT / "tools/mirror_sync/universal_job_dispatcher.py"


def load_dispatcher():
    spec = importlib.util.spec_from_file_location(
        "dispatcher_scope_contract",
        DISPATCHER,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_changed_files_reports_exact_untracked_file(tmp_path):
    module = load_dispatcher()

    import subprocess

    subprocess.run(
        ["git", "init"],
        cwd=tmp_path,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path,
        check=True,
    )

    tracked = tmp_path / "tracked.txt"
    tracked.write_text("base\n", encoding="utf-8")

    subprocess.run(
        ["git", "add", "tracked.txt"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "base"],
        cwd=tmp_path,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    base = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()

    canary = tmp_path / "worker_queue" / "e2e_canaries" / "example.txt"
    canary.parent.mkdir(parents=True)
    canary.write_text("STEP=1\n", encoding="utf-8")

    changed = module.changed_files(tmp_path, base)

    assert changed == [
        "worker_queue/e2e_canaries/example.txt"
    ]


def test_dispatcher_uses_untracked_files_all():
    text = DISPATCHER.read_text(encoding="utf-8")

    assert '"--untracked-files=all"' in text
