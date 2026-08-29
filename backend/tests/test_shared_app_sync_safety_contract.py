from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SCRIPTS = [
    ROOT / "tools/mirror_sync/apply_remote_update.sh",
    ROOT / "tools/mirror_sync/mirror_sync_worker.sh",
    ROOT / "tools/mirror_sync/mirror_sync_supervisor_entrypoint.sh",
]

FORBIDDEN = [
    "git reset ",
    "git reset\t",
    "git stash ",
    "git clean ",
    "git checkout .",
    "git restore ",
]

def test_sync_scripts_have_no_destructive_shared_app_git():
    for script in SCRIPTS:
        if not script.exists():
            continue

        text = script.read_text(encoding="utf-8")

        for token in FORBIDDEN:
            assert token not in text, f"{script}: forbidden {token!r}"


def test_sync_scripts_use_shared_safety_guard():
    for script in SCRIPTS:
        if not script.exists():
            continue

        text = script.read_text(encoding="utf-8")

        assert "shared_app_safety_guard.sh" in text
        assert "edarsahub_require_sync_enabled" in text
        assert "edarsahub_require_clean_shared_app" in text


def test_worker_control_plane_has_no_stash_or_reset():
    path = ROOT / "tools/mirror_sync/worker_control_plane.py"
    text = path.read_text(encoding="utf-8")

    forbidden = [
        "stash push",
        "reset --hard",
        "reset --mixed",
        "checkout .",
        "restore .",
        "git clean",
    ]

    for token in forbidden:
        assert token not in text


def test_pause_file_contract_exists():
    guard = ROOT / "tools/mirror_sync/shared_app_safety_guard.sh"
    text = guard.read_text(encoding="utf-8")

    assert "EDARSAHUB_SYNC_PAUSED" in text
    assert "EDARSAHUB_SYNC_PAUSE_FILE" in text
    assert "DECISION=SYNC_PAUSED" in text
    assert "DECISION=DEFERRED_LOCAL_DIRTY" in text
