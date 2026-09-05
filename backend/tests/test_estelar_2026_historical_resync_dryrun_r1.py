from datetime import date, timedelta

import pytest
from fastapi import BackgroundTasks

from api.admin_scheduler_resync import ResyncExecuteRequest, ejecutar_resync


def _chunks(start: date, end: date, max_days: int = 30):
    cursor = start
    while cursor <= end:
        chunk_end = min(end, cursor + timedelta(days=max_days - 1))
        yield cursor, chunk_end
        cursor = chunk_end + timedelta(days=1)


def _success(resp):
    if hasattr(resp, 'success'):
        return bool(resp.success)
    if isinstance(resp, dict):
        return bool(resp.get('success'))
    return False


@pytest.mark.asyncio
async def test_estelar_2026_historical_resync_dryrun_all_chunks():
    user = {
        'email': 'carlosruz@edarsa.com.mx',
        'correo': 'carlosruz@edarsa.com.mx',
        'username': 'carlosruz@edarsa.com.mx',
        'rol': 'Superadministrador',
        'role': 'Superadministrador',
    }
    completed = []
    for start, end in _chunks(date(2026, 1, 1), date(2026, 9, 4)):
        request = ResyncExecuteRequest(
            tipo_sync='comercial_ventas_cerradas',
            unidad_negocio_id='ESTELAR',
            fecha_inicio=start,
            fecha_fin=end,
            motivo='Conciliar historico 2026 de LA ESTELAR contra Reporte Ejecutivo usando fecha operativa por apertura',
            dry_run=True,
        )
        response = await ejecutar_resync(
            request=request,
            background_tasks=BackgroundTasks(),
            current_user=user,
        )
        assert _success(response), f'DRY_RUN fallo para {start}..{end}: {response}'
        completed.append((start.isoformat(), end.isoformat()))

    assert completed == [
        ('2026-01-01', '2026-01-30'),
        ('2026-01-31', '2026-03-01'),
        ('2026-03-02', '2026-03-31'),
        ('2026-04-01', '2026-04-30'),
        ('2026-05-01', '2026-05-30'),
        ('2026-05-31', '2026-06-29'),
        ('2026-06-30', '2026-07-29'),
        ('2026-07-30', '2026-08-28'),
        ('2026-08-29', '2026-09-04'),
    ]
