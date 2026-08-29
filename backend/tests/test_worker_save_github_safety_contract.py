from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISPATCHER = ROOT / "tools" / "mirror_sync" / "universal_job_dispatcher.py"
PUBLISHER = ROOT / "tools" / "mirror_sync" / "universal_job_result_publisher.py"


def test_existing_write_requires_hash_and_blocks_large_shrink():
    source = DISPATCHER.read_text(encoding="utf-8")
    assert "WRITE_EXISTING_REQUIRES_EXPECTED_SHA256" in source
    assert "WRITE_FILE_LARGE_SHRINK_BLOCKED" in source
    assert "current_size >= 4096" in source
    assert "new_size < int(current_size * 0.75)" in source


def test_result_publisher_is_single_writer():
    source = PUBLISHER.read_text(encoding="utf-8")
    assert "import fcntl" in source
    assert 'PUBLISH_LOCK = STATE / "result_publisher.lock"' in source
    assert "fcntl.LOCK_EX | fcntl.LOCK_NB" in source
    assert "UNIVERSAL_RESULT_PUBLISHER_SINGLE_WRITER=BUSY" in source


def test_safety_job_does_not_touch_application_runtime():
    protected = {"backend/server.py", "backend/modules/auth/routes.py"}
    changed = {
        "tools/mirror_sync/universal_job_dispatcher.py",
        "tools/mirror_sync/universal_job_result_publisher.py",
        "backend/tests/test_worker_save_github_safety_contract.py",
    }
    assert protected.isdisjoint(changed)
