import json
import subprocess
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi import BackgroundTasks

from api.admin_scheduler_resync import ResyncExecuteRequest, ejecutar_resync
from modules.sistema.menu_service import MenuService

BASE_SHA = '4be080543ee671889f3c7633d0813aa460b7989e'
EVIDENCE = Path('tests/estelar_2026_historical_resync_real_r1_evidence.json')
EMAIL = 'carlosruz@edarsa.com.mx'


def _head():
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()


def _chunks(start: date, end: date, max_days: int = 30):
    cursor = start
    while cursor <= end:
        chunk_end = min(end, cursor + timedelta(days=max_days - 1))
        yield cursor, chunk_end
        cursor = chunk_end + timedelta(days=1)


def _as_dict(resp):
    if hasattr(resp, 'model_dump'):
        return resp.model_dump()
    if hasattr(resp, 'dict'):
        return resp.dict()
    if isinstance(resp, dict):
        return resp
    return {'repr': repr(resp)}


def _write(payload):
    EVIDENCE.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')


@pytest.mark.asyncio
async def test_estelar_2026_historical_resync_real_once():
    if _head() != BASE_SHA:
        pytest.skip('one-shot REAL resync already consumed or branch moved')

    menu = MenuService()
    current_user = {'email': EMAIL, 'correo': EMAIL, 'username': EMAIL}
    usuario_id = menu.resolver_usuario_id_canonico(current_user)
    permisos = menu.obtener_permisos_usuario(usuario_id)
    autorizado = any(
        str(p.get('CodigoModulo') or '').strip().upper() == 'SCHEDULER'
        and str(p.get('CodigoAccion') or '').strip().upper() == 'ADMIN'
        and bool(p.get('Permitido', True))
        for p in permisos
    )
    assert autorizado, f'RBAC canonical denied SCHEDULER_ADMIN for {EMAIL} usuario_id={usuario_id}'

    current_user['UsuarioID'] = usuario_id
    evidence = {
        'status': 'RUNNING',
        'job_id': 'EDARSAHUB-ESTELAR-2026-HISTORICAL-RESYNC-REAL-R1-CARLOS-20260905T042500Z',
        'requester_email': EMAIL,
        'usuario_id': usuario_id,
        'rbac_scheduler_admin': True,
        'production_touched': False,
        'blocks': [],
    }
    _write(evidence)

    for start, end in _chunks(date(2026, 1, 1), date(2026, 9, 4)):
        req = ResyncExecuteRequest(
            tipo_sync='comercial_ventas_cerradas',
            unidad_negocio_id='ESTELAR',
            fecha_inicio=start,
            fecha_fin=end,
            motivo='Resync REAL historico 2026 LA ESTELAR para conciliar Reportes ISCAM contra Reporte Ejecutivo usando fecha operativa por apertura',
            dry_run=False,
        )
        resp = await ejecutar_resync(
            request=req,
            background_tasks=BackgroundTasks(),
            current_user=current_user,
        )
        data = _as_dict(resp)
        evidence['blocks'].append({
            'fecha_inicio': start.isoformat(),
            'fecha_fin': end.isoformat(),
            'response': data,
        })
        _write(evidence)
        assert bool(data.get('success')), f'REAL resync fallo para {start}..{end}: {data}'
        assert str(data.get('modo') or '').upper() == 'REAL', f'Modo inesperado: {data}'

    evidence['status'] = 'PASS'
    evidence['blocks_completed'] = len(evidence['blocks'])
    _write(evidence)
    assert evidence['blocks_completed'] == 9
