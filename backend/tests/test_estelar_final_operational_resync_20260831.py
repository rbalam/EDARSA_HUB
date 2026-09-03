import asyncio
import json
from datetime import date

from api.admin_scheduler_resync import (
    _get_unidad_config,
    _ejecutar_dry_run,
    _ejecutar_sync_real,
    _execute_edarsahub_query,
)


def test_estelar_final_dryrun_then_real_resync_20260831():
    fecha = date(2026, 8, 31)
    unidad = _get_unidad_config('ESTELAR')
    assert unidad, 'ESTELAR no encontrada en catalogo canonico'
    assert unidad.get('server_id') == 'a5ff0e25-f029-43db-b634-d4ac814c904f'
    assert unidad.get('sistema') == 'SOFTRESTAURANT'

    dry = asyncio.run(_ejecutar_dry_run('ESTELAR', unidad, fecha, fecha))
    print('ESTELAR_DRY_RUN=' + json.dumps(dry, default=str, ensure_ascii=False))
    assert dry.get('success') is True, dry
    detalle = dry.get('detalle') or []
    assert len(detalle) == 1, dry
    row = detalle[0]
    assert round(float(row.get('ventas_total') or 0), 2) == 22345.00, row
    assert round(float(row.get('propinas_total') or 0), 2) == 2232.50, row
    assert int(row.get('pax_total') or 0) == 48, row
    assert int(row.get('tickets_total') or 0) == 22, row

    real = asyncio.run(_ejecutar_sync_real(
        'ESTELAR', unidad, fecha, fecha,
        'CHATGPT-ESTELAR-FINAL-20260831-20260903',
    ))
    print('ESTELAR_REAL_RESYNC=' + json.dumps(real, default=str, ensure_ascii=False))
    assert real.get('success') is True, real

    final_rows = _execute_edarsahub_query("""
        SELECT
            COUNT(*) AS registros_activos,
            SUM(ISNULL(ventas_total, 0)) AS ventas_total,
            SUM(ISNULL(propinas_total, 0)) AS propinas_total,
            SUM(ISNULL(tickets_total, 0)) AS tickets_total,
            SUM(ISNULL(pax_total, 0)) AS pax_total
        FROM dbo.Comercial_KPIs_Diarios_v2
        WHERE unidad_negocio_id = 'ESTELAR'
          AND fecha_operacion = '2026-08-31'
          AND ISNULL(activo, 1) = 1
    """)
    assert final_rows, 'Sin fila final en EDARSAHUB'
    final = final_rows[0]
    print('ESTELAR_EDARSAHUB_FINAL=' + json.dumps(final, default=str, ensure_ascii=False))
    assert int(final.get('registros_activos') or 0) == 1, final
    assert round(float(final.get('ventas_total') or 0), 2) == 22345.00, final
    assert round(float(final.get('propinas_total') or 0), 2) == 2232.50, final
    assert int(final.get('pax_total') or 0) == 48, final
    assert int(final.get('tickets_total') or 0) == 22, final
