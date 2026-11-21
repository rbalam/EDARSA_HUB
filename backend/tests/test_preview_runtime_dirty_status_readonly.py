import subprocess


def test_preview_runtime_dirty_status_readonly():
    proc = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd="/app",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    status = (proc.stdout or "").strip()
    assert proc.returncode == 0, f"RUNTIME_GIT_STATUS_FAILED:{status}"
    assert not status, "RUNTIME_DIRTY_FILES:\n" + status
