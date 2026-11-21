from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SERVICE = ROOT / "backend" / "modules" / "tablajeria" / "fase6_service.py"


def _source() -> str:
    return SERVICE.read_text(encoding="utf-8")


def test_fase6_idempotency_helpers_are_present_without_sql_runtime():
    text = _source()
    assert "def _fetch_existing_inventory_movements" in text
    assert "def _fetch_existing_costeo" in text
    assert "def _fetch_existing_poliza" in text
    assert "MovimientoInventarioGenerado" in text
    assert "idempotente" in text


def test_fase6_uses_canonical_merma_and_keeps_compatibility():
    text = _source()
    assert 'MERMA = "MERMA"' in text
    assert 'SALIDA_MERMA = "MERMA"' in text
    assert "TipoMovimiento.MERMA.value" in text


def test_fase6_poliza_has_balance_guard_and_no_hardcoded_merma_cost():
    text = _source()
    assert "def _validar_balance_asientos" in text
    assert "DEBE_HABER_DESCUADRADO" in text
    assert "costo_merma_dec" in text
    assert "* 10  # Estimado merma" not in text
