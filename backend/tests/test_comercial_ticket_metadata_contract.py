"""Metadata through the canonical row, daily snapshot and both ticket APIs."""
import json
from datetime import date
from pathlib import Path
from unittest.mock import Mock
import pytest
from modules.comercial_v2.ticket_contract import FIELDS, header_from, discount_comment
from modules.comercial_v2.ticket_snapshot import serialize_open_detail_rows


def test_discount_catalog_wins_without_erasing_original():
    row = {'tipo_descuento_id': 'VIP', 'tipo_descuento_descripcion': 'Cliente VIP', 'partida_comentario_descuento': 'Autorizado por gerente'}
    assert discount_comment(row) == 'Cliente VIP'
    assert row['partida_comentario_descuento'] == 'Autorizado por gerente'
    assert discount_comment({**row, 'tipo_descuento_descripcion': None}) == 'Autorizado por gerente'


def test_snapshot_preserves_distinct_partidas_and_unicode():
    base = {'folio': '123', 'producto_codigo': 'P1', 'cliente_nombre': 'José Muñoz', 'cliente_rfc': 'RFC', 'cliente_direccion_1': 'Calle Mérida', 'ticket_comentario_descuento': 'Descuento cuenta', 'cantidad': 1, 'importe_bruto': 100, 'importe_neto_producto': 90}
    rows = [{**base, 'partida_origen_id': str(i), 'partida_comentario_descuento': note} for i, note in [(1, 'Cumpleaños'), (2, 'Promoción')]]
    result = json.loads(serialize_open_detail_rows(rows))
    assert len(result) == 2
    assert [r['partida_origen_id'] for r in result] == ['1', '2']
    assert [r['partida_comentario_descuento'] for r in result] == ['Cumpleaños', 'Promoción']
    assert result[0]['cliente_nombre'] == 'José Muñoz'
    assert header_from(result)['cliente_direccion'] == 'Calle Mérida'
    assert sum(r['importe_neto_producto'] for r in result) == 180


def test_header_refuses_to_mix_clients():
    with pytest.raises(ValueError, match='TICKET_HEADER_CONFLICT:cliente_id'):
        header_from([{'cliente_id': 'A'}, {'cliente_id': 'B'}])
    assert header_from([{'cliente_id': None}, {'cliente_id': 'A'}])['cliente_id'] == 'A'


def test_materialization_and_insert_are_atomic(monkeypatch):
    from scripts import poblar_ventas_detalle_producto_canonico as etl
    base = {'id_transaccion': 'T1', 'numero_ticket': '123', 'sistema_origen': 'SOFTRESTAURANT', 'estado_origen': 'PAGADO', 'cantidad': 1, 'precio_unitario': 100, 'importe_bruto': 100, 'importe_neto': 90, 'producto_codigo_fuente': 'P1', 'pax_ticket': 2, 'propina_ticket': 18, 'cliente_nombre': 'Cliente', 'tipo_descuento_id': 'VIP', 'tipo_descuento_descripcion': 'VIP'}
    rows = etl._materialize_rows({'unidad_codigo': 'TEST'}, date(2026, 10, 6), [{**base, 'partida_origen_id': '1'}, {**base, 'partida_origen_id': '2'}], 'TEST')
    assert len(rows) == 2
    assert rows[0]['hash_origen'] != rows[1]['hash_origen']
    assert sum(r['propina'] for r in rows) == 18
    conn = Mock()
    cursor = conn.cursor.return_value
    monkeypatch.setattr(etl, 'get_sql_connection', lambda: conn)
    assert etl._insert_rows(rows) == 2
    conn.commit.assert_called_once()
    conn.rollback.assert_not_called()
    for call in cursor.execute.call_args_list[1:]:
        sql, values = call.args
        assert sql.count('%s') == len(values)
        columns = sql.split('(', 1)[1].split(')', 1)[0].split(',')
        assert len(columns) == len(values)
        persisted = dict(zip(map(str.strip, columns), values))
        assert set(FIELDS) <= set(persisted)
        assert persisted['tipo_descuento_descripcion'] == 'VIP'
    conn.reset_mock()
    cursor.execute.side_effect = [None, RuntimeError('insert failed')]
    with pytest.raises(RuntimeError, match='insert failed'):
        etl._insert_rows(rows)
    conn.rollback.assert_called_once()
    conn.commit.assert_not_called()


def test_analytics_query_path_returns_same_metadata():
    from modules.comercial_analytics.repository_tickets import get_ticket_detail
    from modules.comercial_analytics.ticket_identity import create_ticket_pk, parse_ticket_pk
    row = {'cliente_id': 'A', 'cliente_nombre': 'Cliente', 'cliente_rfc': 'RFC', 'cliente_direccion_1': 'Calle', 'ticket_comentario_descuento': 'Cuenta', 'partida_comentario_descuento': 'Detalle', 'tipo_descuento_id': 'VIP', 'tipo_descuento_descripcion': 'Cliente VIP', 'partida_origen_id': '1', 'cantidad': 1, 'importe': 90, 'importe_bruto': 100, 'descuento': 10}
    pk = create_ticket_pk(unidad_negocio_id='TEST', fecha_operacion='2026-10-06', numero_ticket='123')
    result = get_ticket_detail(identity=parse_ticket_pk(pk), allowed_unit_codes=['TEST'], query_executor=lambda sql, params: [row])
    assert result['ticket']['cliente_nombre'] == 'Cliente'
    assert result['ticket']['cliente_direccion'] == 'Calle'
    assert result['ticket']['ticket_comentario_descuento'] == 'Cuenta'
    assert result['lines'][0]['comentario_descuento'] == 'Cliente VIP'
    assert result['lines'][0]['partida_comentario_descuento'] == 'Detalle'
    assert result['ticket']['total'] == 90


def test_both_dashboards_import_exact_same_sales_dialog():
    root = Path(__file__).resolve().parents[2]
    comercial = (root/'frontend/src/pages/Comercial.js').read_text()
    executive = (root/'frontend/src/pages/TableroEjecutivo.js').read_text()
    shared = (root/'frontend/src/components/comercial/KpiDrilldownDialog.jsx').read_text()
    assert 'import KpiDrilldownDialog' in comercial
    assert 'import KpiDrilldownDialog' in executive
    assert 'IAContextualLauncher' in shared
    assert "view_id: 'comercial_detalle_ventas'" in shared
    assert 'function TicketVentaModal' not in comercial
    assert 'function TicketVentaModal' not in shared
    assert "import TicketVentaModal from './TicketVentaModal'" in shared


def test_source_projection_aliases_do_not_cross_engines():
    root = Path(__file__).resolve().parents[1]
    text = (root / "scripts/poblar_ventas_detalle_producto_canonico.py").read_text()
    soft = text[text.index('def _extract_soft('):text.index('SOFT_AJUSTE_CHEQUE =')]
    assert 'tdc2.' not in soft
    assert 'cl.Cl_' not in soft
    assert 'td.desc_tipodescuento AS tipo_descuento_descripcion' in soft
    snapshot = (root / "modules/comercial_v2/ticket_snapshot.py").read_text()
    assert 'tcd2.' not in snapshot
    assert 'td.Td_Descripcion AS tipo_descuento_descripcion' in snapshot
