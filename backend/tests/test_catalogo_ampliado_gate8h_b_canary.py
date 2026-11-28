from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVICE = ROOT / "backend/modules/catalogo_ampliado/canary_delivery.py"


def test_gate8h_b_canary_service_is_bounded_and_fail_closed():
    text = SERVICE.read_text(encoding="utf-8")
    assert 'ALLOWED_ENVIRONMENTS = {"DEVELOPMENT", "PREVIEW"}' in text
    assert "runtime_environment" in text
    assert "process_queue(" not in text
    assert "lock_item(queue_id" in text
    assert "dispatcher._process_item(item)" in text
    assert '("smtp", email)' in text
    assert '("twilio", whatsapp)' in text
    assert "check_duplicate" in text
    assert "production_touched" in text


def test_gate8h_b_canary_has_no_hardcoded_recipient():
    text = SERVICE.read_text(encoding="utf-8")
    assert "rbalam@edarsa.com.mx" not in text
    assert "9999003386" not in text
