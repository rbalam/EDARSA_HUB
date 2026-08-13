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


def test_sync_skips_headers_without_matching_detail(monkeypatch):
    from modules.compras import sync_service

    calls = []

    def fake_execute(host, port, database, username, password, query):
        calls.append(query)
        if len(calls) == 1:
            return [
                {
                    "folio": "3844",
                    "fecha": "2026-07-13",
                    "almacen": "BARRA",
                    "almacen_id": "2",
                    "sucursal": "",
                    "sucursal_id": "",
                    "tipo": "FISICO",
                    "estatus": "CERRADO",
                    "total_productos": 0,
                    "comentario": "",
                },
                {
                    "folio": "3865",
                    "fecha": "2026-07-14",
                    "almacen": "BARRA",
                    "almacen_id": "2",
                    "sucursal": "",
                    "sucursal_id": "",
                    "tipo": "FISICO",
                    "estatus": "CERRADO",
                    "total_productos": 0,
                    "comentario": "",
                },
            ]
        return [{
            "folio": "3844",
            "codigo_producto": "INS-1",
            "nombre_producto": "Insumo 1",
            "unidad": "PZA",
            "existencia_fisica": 3,
            "rendimiento": 1,
            "costo_unitario": 10,
            "almacen": "BARRA",
            "almacen_id": "2",
        }]

    class FakeCursor:
        def __init__(self):
            self.rowcount = 0
            self._rows = []
            self.header_folios = []

        def execute(self, query, params=None):
            if "INFORMATION_SCHEMA.COLUMNS" in query:
                self._rows = [
                    (name,)
                    for name in [
                        "unidad_negocio_id",
                        "unidad_negocio_codigo",
                        "server_id",
                        "system_type",
                        "folio",
                        "codigo_producto",
                        "nombre_producto",
                        "unidad",
                        "existencia_fisica",
                        "rendimiento",
                        "costo_unitario",
                        "almacen",
                        "almacen_id",
                        "sync_source",
                        "sync_timestamp",
                        "sync_status",
                    ]
                ]
                return
            self._rows = []
            self.rowcount = 1
            if "INSERT INTO Compras_Inventarios_Fisicos_Sync" in query:
                self.header_folios.append(params[4])

        def fetchall(self):
            return self._rows

    class FakeConnection:
        def __init__(self):
            self.cursor_obj = FakeCursor()

        def cursor(self):
            return self.cursor_obj

        def commit(self):
            pass

        def close(self):
            pass

    fake_conn = FakeConnection()
    monkeypatch.setattr(sync_service, "get_edarsahub_connection", lambda: fake_conn)

    result = sync_service.sync_inventarios_fisicos_from_server(
        _server(),
        _unidad(),
        fake_execute,
    )

    assert result["status"] == "ERROR"
    assert result["records_synced"] == 0
    assert result["detail_errors"] == 1
    assert "sin detalle coincidente" in result["error"]
    assert "Snapshot anterior preservado" in result["error"]
    assert fake_conn.cursor_obj.header_folios == []


def test_detail_sync_bulk_upserts_existing_keys():
    from modules.compras import sync_service

    class FakeCursor:
        def __init__(self):
            self.rowcount = 0
            self._rows = []
            self.updated_params = []
            self.inserted_params = []

        def execute(self, query, params=None):
            if "INFORMATION_SCHEMA.COLUMNS" in query:
                self._rows = [
                    (name,)
                    for name in [
                        "unidad_negocio_id",
                        "unidad_negocio_codigo",
                        "server_id",
                        "system_type",
                        "folio",
                        "codigo_producto",
                        "nombre_producto",
                        "unidad",
                        "existencia_fisica",
                        "rendimiento",
                        "costo_unitario",
                        "almacen",
                        "almacen_id",
                        "sync_source",
                        "sync_timestamp",
                        "sync_status",
                    ]
                ]
                return
            if (
                "SELECT [server_id], [unidad_negocio_id], [folio], "
                "[codigo_producto], [almacen_id]"
            ) in query:
                self._rows = [
                    (
                        "server-1",
                        "unidad-1",
                        "3844",
                        "INS-1",
                        "2",
                    )
                ]
                return
            if "UPDATE target" in query:
                self.updated_params.append(params)
                self._rows = []
                self.rowcount = 1
                return
            if "INSERT INTO dbo.Compras_Inventarios_Fisicos_Detalle_Sync" in query:
                self.inserted_params.append(params)
                self._rows = []
                self.rowcount = 1
                return
            self._rows = []
            self.rowcount = 1

        def executemany(self, query, params):
            if "UPDATE dbo.Compras_Inventarios_Fisicos_Detalle_Sync" in query:
                self.updated_params.extend(params)
            if "INSERT INTO dbo.Compras_Inventarios_Fisicos_Detalle_Sync" in query:
                self.inserted_params.extend(params)
            self.rowcount = len(params)

        def fetchall(self):
            return self._rows

    cursor = FakeCursor()
    result = sync_service._sync_inventarios_fisicos_detalle(
        cursor,
        [
            {
                "folio": "3844",
                "codigo_producto": "INS-1",
                "nombre_producto": "Insumo existente",
                "unidad": "PZA",
                "existencia_fisica": 3,
                "rendimiento": 1,
                "costo_unitario": 10,
                "almacen": "BARRA",
                "almacen_id": "2",
            },
            {
                "folio": "3865",
                "codigo_producto": "INS-2",
                "nombre_producto": "Insumo nuevo",
                "unidad": "PZA",
                "existencia_fisica": 5,
                "rendimiento": 1,
                "costo_unitario": 12,
                "almacen": "BARRA",
                "almacen_id": "2",
            },
        ],
        "server-1",
        "SOFTRESTAURANT_PRO",
        "unidad-1",
        "ESTELAR",
    )

    assert result["status"] == "OK"
    assert result["details_updated"] == 1
    assert result["details_synced"] == 1
    assert result["detail_errors"] == 0
    assert len(cursor.updated_params) == 1
    assert len(cursor.inserted_params) == 1


def test_sync_requisiciones_source_query_none_is_error_not_empty_success(monkeypatch):
    from modules.compras import sync_service

    def fake_execute(host, port, database, username, password, query):
        return None

    def fail_write_connection():
        raise AssertionError("No debe abrir conexión EDARSAHUB si falla origen")

    monkeypatch.setattr(sync_service, "get_edarsahub_connection", fail_write_connection)

    result = sync_service.sync_requisiciones_from_server(
        _server(),
        _unidad(),
        fake_execute,
    )

    assert result["status"] == "ERROR"
    assert result["records_synced"] == 0
    assert "servidor origen" in result["error"]


def test_sync_requisiciones_updates_duplicate_key(monkeypatch):
    from modules.compras import sync_service

    def fake_execute(host, port, database, username, password, query):
        return [{
            "tipo": "ORDEN",
            "folio": "0000025203",
            "fecha": "2026-07-13",
            "fecha_entrega": "2026-07-14",
            "proveedor": "Proveedor 1",
            "proveedor_id": "10",
            "sucursal": "",
            "sucursal_id": "",
            "total_productos": 2,
            "importe": 100,
            "estatus": "PXA",
        }]

    class FakeCursor:
        def __init__(self):
            self.rowcount = 0
            self.updated_params = None

        def execute(self, query, params=None):
            if "INSERT INTO Compras_Requisiciones_Sync" in query:
                raise Exception("duplicate key")
            if "UPDATE Compras_Requisiciones_Sync" in query and "unidad_negocio_id" in query:
                self.updated_params = params
                self.rowcount = 1
                return
            self.rowcount = 1

    class FakeConnection:
        def __init__(self):
            self.cursor_obj = FakeCursor()

        def cursor(self):
            return self.cursor_obj

        def commit(self):
            pass

        def close(self):
            pass

    fake_conn = FakeConnection()
    monkeypatch.setattr(sync_service, "get_edarsahub_connection", lambda: fake_conn)

    result = sync_service.sync_requisiciones_from_server(
        _server(),
        _unidad(),
        fake_execute,
    )

    assert result["status"] == "OK"
    assert result["records_synced"] == 1
    assert result["error"] is None
    assert fake_conn.cursor_obj.updated_params[-3:] == ("server-1", "0000025203", "ORDEN")
