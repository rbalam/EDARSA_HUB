from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_worker_runtime_has_no_gh_dependency():
    for rel in (
        "tools/mirror_sync/universal_job_dispatcher.py",
        "tools/mirror_sync/universal_job_result_publisher.py",
        "tools/mirror_sync/universal_job_bridge.py",
        "tools/mirror_sync/runtime_health_publisher.py",
    ):
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        assert "gh auth git-credential" not in text
        assert "/usr/bin/gh" not in text
