from pathlib import Path

import pytest

from modules.inteligencia_comercial import iscam_routes


def _desglose(ventas=0, propinas=0, cheques=0, pax=0, cheque_promedio=0, pax_promedio=0, dia_actual_ventas=0):
    return {
        'contrato': {
            'acumulado': 'CERRADO_SIN_DIA_OPERATIVO_ACTUAL',
            'dia_actual': 'SEPARADO',
            'total_incluyendo_dia': 'INFORMATIVO',
        },
        'acumulado_cerrado': {
            'metricas': {
                'ventas': ventas,
                'propinas': propinas,
                'cheques': cheques,
                'pax': pax,
                'cheque_promedio': cheque_promedio,
                'consumo_promedio_pax': pax_promedio,
                'pax_promedio': pax_promedio,
            }
        },
        'dia_actual': {'metricas': {'ventas': dia_actual_ventas}},
        'total_incluyendo_dia': {'metricas': {'ventas': ventas + dia_actual_ventas}},
    }


@pytest.mark.asyncio
async def test_iscam_uses_acumulado_cerrado_and_exact_service_metrics(monkeypatch):
    calls = []

    monkeypatch.setattr(iscam_routes.UnidadesService, 'resolver_pk', staticmethod(lambda _valor: 'PK-ESTELAR'))

    def fake_resumen(desde, hasta, unidad_pks=None):
        calls.append((desde, hasta, unidad_pks))
        return _desglose(60110, 5544, 29, 77, 2072.7586, 780.6493, dia_actual_ventas=9999)

    monkeypatch.setattr(
        iscam_routes.KPIsCanonicosService,
        'resumen_periodo_desglosado',
        staticmethod(fake_resumen),
    )

    payload = await iscam_routes.ventas_periodos(
        unidad='ESTELAR',
        desde='2026-09-01',
        hasta='2026-09-01',
        group_by='dia',
        meses=12,
    )

    assert calls == [('2026-09-01', '2026-09-02', ['PK-ESTELAR'])]
    assert payload['contrato_acumulado'] == 'CERRADO_SIN_DIA_OPERATIVO_ACTUAL'
    assert payload['source'] == 'KPIsCanonicosService.resumen_periodo_desglosado.acumulado_cerrado'
    assert payload['periodos'] == [{
        'periodo': '2026-09-01',
        'venta_total': 60110.0,
        'propinas': 5544.0,
        'cheques': 29,
        'clientes': 77,
        'cheque_promedio': 2072.76,
        'consumo_promedio': 780.65,
    }]


@pytest.mark.asyncio
async def test_iscam_never_mixes_dia_actual_into_closed_period(monkeypatch):
    monkeypatch.setattr(iscam_routes.UnidadesService, 'resolver_pk', staticmethod(lambda _valor: 'PK-ESTELAR'))
    monkeypatch.setattr(
        iscam_routes.KPIsCanonicosService,
        'resumen_periodo_desglosado',
        staticmethod(lambda *_args, **_kwargs: _desglose(dia_actual_ventas=25000)),
    )

    payload = await iscam_routes.ventas_periodos(
        unidad='ESTELAR',
        desde='2026-09-04',
        hasta='2026-09-04',
        group_by='dia',
        meses=12,
    )

    assert payload['periodos'] == []


def test_softrestaurant_closed_sales_period_is_assigned_by_apertura_not_cierre():
    text = Path('modules/comercial_v2/sync_comercial_edarsahub.py').read_text(encoding='utf-8')
    block = text.split('QUERY_SOFTRESTAURANT_VENTAS_CERRADAS_DIA =', 1)[1].split('QUERY_SOFTRESTAURANT_VENTAS_ABIERTAS =', 1)[0]
    assert "apertura BETWEEN '{inicio_operativo}' AND '{fin_operativo}'" in block
    assert 'cierre IS NOT NULL' in block
    assert 'cierre BETWEEN' not in block
    assert 'AND cancelado = 0' in block
