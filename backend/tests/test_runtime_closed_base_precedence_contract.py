from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "database/migrations/20261016_001_runtime_closed_base_precedence.sql"
VALIDATION = ROOT / "database/validation/20261016_001_runtime_closed_base_precedence_validation.sql"


def test_runtime_snapshot_is_ranked_per_unit_not_global_date():
    text = MIGRATION.read_text(encoding="utf-8")
    assert "PARTITION BY a.unidad_negocio_id" in text
    assert "ORDER BY\n                a.fecha_operacion DESC" in text
    assert "snapshot_fecha AS" not in text


def test_closed_snapshot_cannot_override_materialized_base():
    text = MIGRATION.read_text(encoding="utf-8")
    assert "AND ISNULL(s.ventas_abiertas, 0) > 0" in text
    assert "snapshot_only AS" in text
    assert "NOT EXISTS (" in text


def test_validation_fails_closed_on_base_runtime_difference():
    text = VALIDATION.read_text(encoding="utf-8")
    assert "RUNTIME_CLOSED_BASE_PRECEDENCE_VIOLATION" in text
    assert "ISNULL(s.ventas_abiertas,0)=0" in text
    assert "runtime_ventas" in text
    assert "runtime_tickets" in text
    assert "runtime_pax" in text


def test_fix_does_not_touch_protected_synchronizers():
    text = MIGRATION.read_text(encoding="utf-8").lower()
    assert "sync_comercial_abiertas_v2" not in text
    assert "sync_softrestaurant_ventas_cerradas" not in text
    assert "sync_mpro_ventas_cerradas" not in text
