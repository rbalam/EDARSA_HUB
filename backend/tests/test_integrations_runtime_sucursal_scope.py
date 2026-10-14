from backend.modules.integrations_runtime.sucursal_scope import (
    SucursalScopeConflict,
    ensure_sucursal_server_mapping,
)


SERVER_ID = "11111111-1111-1111-1111-111111111111"


class FakeCursor:
    def __init__(
        self,
        *,
        server_exists=True,
        branch_exists=True,
        by_origin=None,
        by_branch=None,
        inserted_id=99,
    ):
        self.server_exists = server_exists
        self.branch_exists = branch_exists
        self.by_origin = list(by_origin or [])
        self.by_branch = list(by_branch or [])
        self.inserted_id = inserted_id
        self.last_kind = None
        self.executions = []

    def execute(self, sql, params):
        normalized = " ".join(sql.split())
        self.executions.append((normalized, params))
        if "FROM dbo.Servidores_Conexiones" in normalized:
            self.last_kind = "server"
        elif "FROM dbo.Sistema_Sucursales" in normalized:
            self.last_kind = "branch"
        elif "SucursalOrigenID=%s" in normalized:
            self.last_kind = "origin"
        elif "SucursalID=%s" in normalized and "Sistema_SucursalServidorMapeo" in normalized:
            self.last_kind = "mapping_branch"
        elif "INSERT INTO dbo.Sistema_SucursalServidorMapeo" in normalized:
            self.last_kind = "insert"
        else:
            self.last_kind = "other"

    def fetchone(self):
        if self.last_kind == "server":
            return (SERVER_ID,) if self.server_exists else None
        if self.last_kind == "branch":
            return (7,) if self.branch_exists else None
        if self.last_kind == "insert":
            return (self.inserted_id,)
        return None

    def fetchall(self):
        if self.last_kind == "origin":
            return self.by_origin
        if self.last_kind == "mapping_branch":
            return self.by_branch
        return []


def test_idempotent_existing_mapping_returns_same_id():
    cursor = FakeCursor(by_origin=[(12, 7, True)])
    result = ensure_sucursal_server_mapping(
        cursor,
        servidor_id=SERVER_ID,
        sucursal_id=7,
        sucursal_origen_id="NORTE",
    )
    assert result == 12
    assert not any("INSERT INTO" in sql for sql, _ in cursor.executions)


def test_origin_reassignment_fails_closed():
    cursor = FakeCursor(by_origin=[(12, 8, True)])
    try:
        ensure_sucursal_server_mapping(
            cursor,
            servidor_id=SERVER_ID,
            sucursal_id=7,
            sucursal_origen_id="NORTE",
        )
    except SucursalScopeConflict:
        pass
    else:
        raise AssertionError("expected SucursalScopeConflict")


def test_branch_reassignment_fails_closed():
    cursor = FakeCursor(by_branch=[(12, "CENTRO", True)])
    try:
        ensure_sucursal_server_mapping(
            cursor,
            servidor_id=SERVER_ID,
            sucursal_id=7,
            sucursal_origen_id="NORTE",
        )
    except SucursalScopeConflict:
        pass
    else:
        raise AssertionError("expected SucursalScopeConflict")


def test_duplicate_origin_fails_closed():
    cursor = FakeCursor(by_origin=[(12, 7, True), (13, 7, True)])
    try:
        ensure_sucursal_server_mapping(
            cursor,
            servidor_id=SERVER_ID,
            sucursal_id=7,
            sucursal_origen_id="NORTE",
        )
    except SucursalScopeConflict:
        pass
    else:
        raise AssertionError("expected SucursalScopeConflict")


def test_new_mapping_uses_locking_hints_and_inserts():
    cursor = FakeCursor(inserted_id=88)
    result = ensure_sucursal_server_mapping(
        cursor,
        servidor_id=SERVER_ID,
        sucursal_id=7,
        sucursal_origen_id="NORTE",
        created_by="worker",
    )
    assert result == 88
    mapping_selects = [
        sql for sql, _ in cursor.executions
        if "Sistema_SucursalServidorMapeo" in sql and "SELECT" in sql
    ]
    assert mapping_selects
    assert all("UPDLOCK, HOLDLOCK" in sql for sql in mapping_selects)
    assert any("INSERT INTO dbo.Sistema_SucursalServidorMapeo" in sql for sql, _ in cursor.executions)


def test_missing_canonical_server_is_rejected():
    cursor = FakeCursor(server_exists=False)
    try:
        ensure_sucursal_server_mapping(
            cursor,
            servidor_id=SERVER_ID,
            sucursal_id=7,
            sucursal_origen_id="NORTE",
        )
    except ValueError as exc:
        assert "ServidorID" in str(exc)
    else:
        raise AssertionError("expected ValueError")
