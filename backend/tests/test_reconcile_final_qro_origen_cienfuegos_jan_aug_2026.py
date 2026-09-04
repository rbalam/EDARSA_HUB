import asyncio
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from api.admin_scheduler_resync import (
    _ejecutar_dry_run,
    _ejecutar_sync_real,
    _execute_edarsahub_query,
    _get_unidad_config,
)

QRO = {
    '2026-07-31': ('184693.00','21982.00',37,99),
    '2026-08-01': ('219346.00','21324.00',41,134),
    '2026-08-02': ('131995.00','14521.00',20,77),
    '2026-08-03': ('84671.00','6981.00',15,51),
    '2026-08-05': ('231170.00','26994.00',31,118),
    '2026-08-06': ('125268.00','11270.00',21,70),
    '2026-08-07': ('221365.00','21074.00',40,109),
    '2026-08-08': ('233021.00','22707.00',57,159),
    '2026-08-09': ('52487.00','5236.00',12,35),
    '2026-08-12': ('131806.00','11783.00',23,65),
    '2026-08-19': ('109697.00','12852.00',20,56),
    '2026-08-20': ('265328.00','23350.00',47,118),
    '2026-08-25': ('93896.00','10929.00',18,52),
    '2026-08-27': ('159978.00','14397.00',32,85),
}

ORIGEN = {
    '2026-07-31': ('91503.88','7141.94',42,100),
    '2026-08-01': ('71628.69','5455.40',39,95),
    '2026-08-02': ('33904.43','2761.80',19,53),
    '2026-08-03': ('24941.51','1849.35',17,41),
    '2026-08-05': ('71810.55','9120.48',30,115),
    '2026-08-06': ('38595.99','4590.00',20,57),
    '2026-08-07': ('55420.45','5258.65',30,81),
    '2026-08-08': ('45294.23','3019.35',33,80),
    '2026-08-09': ('24963.01','1996.70',18,49),
    '2026-08-12': ('37087.08','3267.60',18,54),
    '2026-08-19': ('106657.43','7076.60',27,84),
    '2026-08-20': ('34191.99','4027.20',13,41),
    '2026-08-25': ('39699.10','3164.55',21,57),
    '2026-08-27': ('86192.88','5342.40',29,71),
    '2026-08-28': ('152948.71','14422.25',43,147),
}

CF = {
    '2026-07-31': ('139104.00','11288.59',36,129),
}

def money(v):
    return Decimal(str(v or 0)).quantize(Decimal('0.01'))

def expected_tuple(v):
    return (money(v[0]), money(v[1]), int(v[2]), int(v[3]))

def metrics_row(row):
    return (money(row.get('ventas_total')), money(row.get('propinas_total')), int(row.get('tickets_total') or 0), int(row.get('pax_total') or 0))

def read_final(codigo, fecha):
    rows = _execute_edarsahub_query(f"""
        SELECT COUNT(*) AS registros_activos,
               SUM(ISNULL(ventas_total,0)) AS ventas_total,
               SUM(ISNULL(propinas_total,0)) AS propinas_total,
               SUM(ISNULL(tickets_total,0)) AS tickets_total,
               SUM(ISNULL(pax_total,0)) AS pax_total
        FROM dbo.Comercial_KPIs_Diarios_v2
        WHERE unidad_negocio_id = '{codigo}'
          AND fecha_operacion = '{fecha}'
          AND ISNULL(activo,1)=1
    """)
    assert rows, (codigo, fecha, 'sin lectura final')
    r = rows[0]
    return {'registros_activos':int(r.get('registros_activos') or 0),'ventas_total':str(money(r.get('ventas_total'))),'propinas_total':str(money(r.get('propinas_total'))),'tickets_total':int(r.get('tickets_total') or 0),'pax_total':int(r.get('pax_total') or 0)}

def sync_one(codigo, fecha_str, exp, evidence):
    fecha = date.fromisoformat(fecha_str)
    unidad = _get_unidad_config(codigo)
    assert unidad, (codigo, fecha_str, 'unidad no encontrada')
    dry = asyncio.run(_ejecutar_dry_run(codigo, unidad, fecha, fecha))
    assert dry.get('success') is True, (codigo, fecha_str, 'dry failed', dry)
    detalle = dry.get('detalle') or []
    assert len(detalle) == 1, (codigo, fecha_str, 'dry rows', dry)
    got_dry = metrics_row(detalle[0])
    assert got_dry == expected_tuple(exp), (codigo, fecha_str, 'dry mismatch', got_dry, expected_tuple(exp), dry)
    run_id = f"CHATGPT-RECON-FINAL-2026-{codigo}-{fecha.strftime('%Y%m%d')}"
    real = asyncio.run(_ejecutar_sync_real(codigo, unidad, fecha, fecha, run_id))
    assert real.get('success') is True, (codigo, fecha_str, 'real failed', real)
    final = read_final(codigo, fecha_str)
    assert final['registros_activos'] == 1, (codigo, fecha_str, final)
    final_tuple = (money(final['ventas_total']), money(final['propinas_total']), final['tickets_total'], final['pax_total'])
    assert final_tuple == expected_tuple(exp), (codigo, fecha_str, 'final mismatch', final, exp)
    evidence.append({'unidad':codigo,'fecha':fecha_str,'dry_run':{'ventas_total':str(got_dry[0]),'propinas_total':str(got_dry[1]),'tickets_total':got_dry[2],'pax_total':got_dry[3],'query_source':dry.get('query_source'),'contract':dry.get('backend_contract_version')},'real':real,'final':final})

def test_reconcile_final_qro_origen_cienfuegos_jan_aug_2026():
    evidence = []
    for fecha_str, exp in QRO.items():
        sync_one('130QRO', fecha_str, exp, evidence)
    for fecha_str, exp in ORIGEN.items():
        sync_one('ORIGEN', fecha_str, exp, evidence)
    for fecha_str, exp in CF.items():
        sync_one('CIENFUEGOS', fecha_str, exp, evidence)
    assert len(evidence) == 30
    Path('tests/reconcile_final_qro_origen_cienfuegos_jan_aug_2026_evidence.json').write_text(json.dumps({'status':'PASS','operaciones':evidence}, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
