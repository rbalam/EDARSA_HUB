from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / "tools/repository_safety/destructive_diff_guard.py"


def test_destructive_guard_exists():
    assert GUARD.exists()


def test_critical_paths_are_protected():
    text = GUARD.read_text(encoding="utf-8")

    assert "backend/server.py" in text
    assert "backend/modules/auth/" in text
    assert "tools/mirror_sync/" in text
    assert "tools/bootstrap/" in text


def test_line_loss_threshold_is_30_percent():
    text = GUARD.read_text(encoding="utf-8")
    assert "MAX_CRITICAL_LINE_LOSS_RATIO = 0.30" in text


def test_server_router_collapse_is_guarded():
    text = GUARD.read_text(encoding="utf-8")
    assert "ROUTER_COUNT_COLLAPSE" in text
    assert "include_router" in text


def test_required_routes_are_guarded():
    text = GUARD.read_text(encoding="utf-8")
    assert "/api/auth/login" in text
    assert "/api/health" in text
