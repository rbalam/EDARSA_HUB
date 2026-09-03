from datetime import date
from modules.comercial_v2 import sync_comercial_edarsahub as sync_module

def test_estelar_uses_official_aggregate_contract():
    query = sync_module.build_softrestaurant_ventas_cerradas_query({"empresa_id": "EST"}, date(2026, 8, 31), date(2026, 8, 31))
    for fragment in (
        "SUM(total) AS ventas_total",
        "SUM(propina) AS propinas",
        "SUM(nopersonas) AS num_personas",
        "COUNT(folio) AS num_cheques",
        "WHERE idempresa = 'EST'",
        "apertura BETWEEN '2026-08-31 09:00:00' AND '2026-09-01 08:59:59'",
        "AND cierre IS NOT NULL",
        "AND cancelado = 0",
    ):
        assert fragment in query
    assert "JOIN turnos" not in query
    assert "ch.folio AS folio" not in query
