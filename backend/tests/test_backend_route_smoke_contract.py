from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SMOKE = ROOT / "tools/repository_safety/backend_route_smoke.py"


def test_smoke_uses_openapi():
    text = SMOKE.read_text(encoding="utf-8")
    assert "app.openapi()" in text


def test_login_is_required():
    text = SMOKE.read_text(encoding="utf-8")
    assert "/api/auth/login" in text


def test_health_is_required():
    text = SMOKE.read_text(encoding="utf-8")
    assert "/api/health" in text


def test_smoke_exposes_repository_root_for_worker_tooling():
    text = SMOKE.read_text(encoding="utf-8")
    assert "str(ROOT)" in text
    assert "str(BACKEND)" in text
