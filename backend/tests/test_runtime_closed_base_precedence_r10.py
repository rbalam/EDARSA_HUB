from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / 'backend/database/migrations/20261020_001_runtime_closed_base_precedence_apply.sql'
PROTECTED = (
    ROOT / 'backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py',
    ROOT / 'backend/modules/comercial_v2/sync_comercial_edarsahub.py',
    ROOT / 'backend/core/scheduler/jobs/sync_comercial_v2_job.py',
)


def test_runtime_closed_base_precedence_contract():
    sql = MIGRATION.read_text(encoding='utf-8')
    assert 'PARTITION BY a.unidad_negocio_id' in sql
    assert 'AND ISNULL(s.ventas_abiertas, 0) > 0' in sql
    assert 'ISNULL(k.es_corte_cerrado, 0) = 1' in sql
    assert 'ISNULL(k.es_venta_abierta, 0) = 0' in sql
    assert 'ABS(ISNULL(k.ventas_total, 0)) > 0.0001' in sql
    assert 'OR ISNULL(k.tickets_total, 0) > 0' in sql
    assert 'OR ISNULL(k.pax_total, 0) > 0' in sql
    assert 'AND NOT (' in sql
    assert 'WHERE NOT EXISTS (' in sql
    assert 'FROM dbo.Comercial_KPIs_Diarios_v2 AS k' in sql
    assert 'SELECT MAX(fecha_operacion)' not in sql


def test_migration_does_not_reference_protected_synchronizers():
    sql = MIGRATION.read_text(encoding='utf-8')
    for path in PROTECTED:
        assert path.name not in sql
