from decimal import Decimal

import pytest

from core.scheduler.jobs.sync_comercial_v2_job import _resolve_estatus_general
from scripts.poblar_ventas_detalle_producto_canonico import (SOFT_AJUSTE_FRANQUICIA_CERO, _runtime_metrics, _soft_add_ticket_adjustments)

def _row(name, amount, header='0', ticket='SOFT:25202', discount='0'):
    return {'id_transaccion':ticket,'numero_ticket':'25202','importe_neto_ticket':Decimal(header),'descuento_ticket':Decimal(discount),'importe_neto':Decimal(amount),'importe_bruto':Decimal(amount),'producto_codigo_fuente':name,'producto_nombre':name,'cantidad':Decimal('1'),'precio_unitario':Decimal(amount)}

def test_estelar_ticket_25202_franchise_closes_exactly_at_zero():
    out=_soft_add_ticket_adjustments([_row('A PISTACHES','45'),_row('A CACAHUATE JAPONES','35'),_row('FRANQUICIA GERENTE','-81')])
    assert out[-1]['producto_codigo_fuente']==SOFT_AJUSTE_FRANQUICIA_CERO
    assert out[-1]['importe_neto']==Decimal('1')
    assert sum(r['importe_neto'] for r in out)==Decimal('0')

def test_zero_ticket_without_negative_franchise_still_fails_closed():
    with pytest.raises(RuntimeError,match='diferencia no explicada'):
        _soft_add_ticket_adjustments([_row('OTRO AJUSTE','-1')])

def test_closed_overlay_zero_open_sales_is_not_open():
    metrics=_runtime_metrics({'ventas_total':Decimal('28329.75'),'tickets_total':22,'pax_total':46,'ventas_abiertas':Decimal('0'),'es_venta_abierta':False,'es_corte_cerrado':True,'fuente_original':'Comercial_Ventas_Dia_Abiertas_v2'})
    assert metrics['es_abierta'] is False

def test_detail_failures_make_scheduler_partial():
    assert _resolve_estatus_general({'unidades_fallidas':0,'unidades_exitosas':5,'detalle_producto_fallidos':8})=='PARCIAL'

def test_clean_scheduler_run_is_completed():
    assert _resolve_estatus_general({'unidades_fallidas':0,'unidades_exitosas':5,'detalle_producto_fallidos':0})=='COMPLETADO'
