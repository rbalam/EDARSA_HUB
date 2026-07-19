import os


os.environ.setdefault("EDARSAHUB_SQL_HOST", "localhost")
os.environ.setdefault("EDARSAHUB_SQL_DATABASE", "EDARSAHUB")
os.environ.setdefault("EDARSAHUB_SQL_USER", "test")
os.environ.setdefault("EDARSAHUB_SQL_PASSWORD", "test")


def _server(system_type="SOFTRESTAURANT_PRO"):
    return {
        "id": "server-1",
        "host": "localhost",
        "port": 1433,
        "database": "soft",
        "username": "user",
        "password": "password",
        "system_type": system_type,
    }


def _unidad():
    return {
        "id": "unidad-1",
        "codigo": "ESTELAR",
        "nombre": "LA ESTELAR",
    }


def test_sync_softrestaurant_query_uses_inventory_warehouse_id():
    from modules.compras.sync_service import sync_inventarios_fisicos_from_server

    captured = {}

    def fake_execute(host, port, database, username, password, query):
        captured["query"] = query
        return []

    result = sync_inventarios_fisicos_from_server(_server(), _unidad(), fake_execute)

    assert result["status"] == "OK"
    assert "CAST(INV.idalmacen1 AS VARCHAR(50)) as almacen_id" in captured["query"]
    assert "CAST(A.\n)" not in captured["query"]
    assert "ISNULL(INV.cancelado, 0) = 0" in captured["query"]


def test_sync_source_query_none_is_error_not_empty_success():
    from modules.compras.sync_service import sync_inventarios_fisicos_from_server

    def fake_execute(host, port, database, username, password, query):
        return None

    result = sync_inventarios_fisicos_from_server(_server(), _unidad(), fake_execute)

    assert result["status"] == "ERROR"
    assert result["records_synced"] == 0


def test_sync_headers_without_detail_is_error_before_writing(monkeypatch):
    from modules.compras import sync_service

    calls = []

    def fake_execute(host, port, database, username, password, query):
        calls.append(query)
        if len(calls) == 1:
            return [{
                "folio": "3844",
                "fecha": "2026-07-13",
                "almacen": "BARRA",
                "almacen_id": "2",
                "sucursal": "",
                "sucursal_id": "",
                "tipo": "FISICO",
                "estatus": "CERRADO",
                "total_productos": 1,
                "comentario": "",
            }]
        return []

    def fail_write_connection():
        raise AssertionError("No debe abrir conexión EDARSAHUB si falta detalle")

    monkeypatch.setattr(sync_service, "get_edarsahub_connection", fail_write_connection)

    result = sync_service.sync_inventarios_fisicos_from_server(
        _server(),
        _unidad(),
        fake_execute,
    )

    assert result["status"] == "ERROR"
    assert result["records_synced"] == 0
    assert result["details_synced"] == 0
    assert result["details_updated"] == 0
    assert result["detail_errors"] == 1
    assert "sin detalle origen" in result["error"]
    assert len(calls) == 2
