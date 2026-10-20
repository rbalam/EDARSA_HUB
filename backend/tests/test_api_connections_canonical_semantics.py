from modules.api_connections.repository import _sql_row_to_api_dict


def test_queries_configured_is_derived_from_real_query_fields():
    mapped = _sql_row_to_api_dict({
        "id": "00000000-0000-4000-8000-000000000711",
        "nombre": "API Test",
        "tipo_conexion": "API_LOCAL",
        "queries_configured": True,
        "query_ventas": None,
        "query_inventario": "",
        "query_movimientos": None,
        "solo_ventas_dia": False,
    })
    assert mapped["queries_configured"] is False
    assert mapped["solo_ventas_dia"] is False


def test_role_derived_solo_ventas_is_independent_from_queries():
    mapped = _sql_row_to_api_dict({
        "id": "00000000-0000-4000-8000-000000000712",
        "nombre": "API Test",
        "tipo_conexion": "API_LOCAL",
        "queries_configured": False,
        "query_ventas": "{\"validated\": true}",
        "query_inventario": None,
        "query_movimientos": None,
        "solo_ventas_dia": True,
    })
    assert mapped["queries_configured"] is True
    assert mapped["solo_ventas_dia"] is True
