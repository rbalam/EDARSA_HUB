from typing import Dict

from .repository_comercial_edarsahub import _execute_query


def soft_deactivate_kpi_diario(unidad_codigo: str, fecha_operacion: str, motivo: str) -> Dict[str, object]:
    unidad_codigo = str(unidad_codigo or '').strip()
    fecha_operacion = str(fecha_operacion or '').strip()
    motivo = str(motivo or '').strip()
    if not unidad_codigo or not fecha_operacion or not motivo:
        raise ValueError('unidad_codigo, fecha_operacion y motivo son obligatorios')

    rows = _execute_query(f"""
        SELECT id, activo
        FROM dbo.Comercial_KPIs_Diarios_v2
        WHERE unidad_negocio_id = '{unidad_codigo}'
          AND fecha_operacion = '{fecha_operacion}'
          AND ISNULL(activo,1)=1
    """)
    if len(rows) != 1:
        raise RuntimeError(f'Guard de fila activa fallo para {unidad_codigo}/{fecha_operacion}: {len(rows)}')

    row_id = str(rows[0]['id'])
    _execute_query(f"""
        UPDATE dbo.Comercial_KPIs_Diarios_v2
           SET activo = 0,
               fecha_ultima_actualizacion = SYSUTCDATETIME()
         WHERE id = '{row_id}'
           AND ISNULL(activo,1)=1
    """)

    after = _execute_query(f"""
        SELECT COUNT(*) AS activos
        FROM dbo.Comercial_KPIs_Diarios_v2
        WHERE unidad_negocio_id = '{unidad_codigo}'
          AND fecha_operacion = '{fecha_operacion}'
          AND ISNULL(activo,1)=1
    """)
    activos = int((after[0] or {}).get('activos') or 0) if after else 0
    if activos != 0:
        raise RuntimeError(f'Soft deactivate no se confirmo para {unidad_codigo}/{fecha_operacion}')
    return {'unidad': unidad_codigo, 'fecha': fecha_operacion, 'activo': False, 'motivo': motivo}
