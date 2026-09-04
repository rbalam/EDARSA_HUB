import asyncio
from datetime import date

from api.admin_scheduler_resync import _ejecutar_dry_run, _get_unidad_config, _execute_edarsahub_query
from modules.comercial_v2.kpi_cleanup import soft_deactivate_kpi_diario

DATES = ['2026-03-12','2026-03-22']

def is_zero(dry):
    detalle = dry.get('detalle') or []
    if not detalle:
        return True
    assert len(detalle) == 1, dry
    r = detalle[0]
    return float(r.get('ventas_total') or 0)==0 and float(r.get('propinas_total') or 0)==0 and int(r.get('tickets_total') or 0)==0 and int(r.get('pax_total') or 0)==0

def test_close_cf_orphans_r2():
    unidad = _get_unidad_config('CIENFUEGOS')
    assert unidad
    for ds in DATES:
        d = date.fromisoformat(ds)
        dry = asyncio.run(_ejecutar_dry_run('CIENFUEGOS', unidad, d, d))
        assert dry.get('success') is True, dry
        assert is_zero(dry), (ds, dry)
        result = soft_deactivate_kpi_diario('CIENFUEGOS', ds, 'Conciliacion Jan-Ago 2026: fila presente solo en HUB; origen oficial sin movimientos')
        assert result['activo'] is False

    rows = _execute_edarsahub_query("""SELECT CONVERT(varchar(10),fecha_operacion,23) AS fecha_operacion FROM dbo.Comercial_KPIs_Diarios_v2 WHERE unidad_negocio_id='CIENFUEGOS' AND fecha_operacion IN ('2026-03-12','2026-03-22') AND ISNULL(activo,1)=1""")
    assert rows == [], rows
