"""
Pruebas automatizadas de autorización, aislamiento y regresión para:
JOB: BOS-USUARIOS-RBAC-IMPLEMENTATION-R1-20261020

Cobertura:
1. Identidad SQL canónica dbo.Usuario_Catalogo (usuario_id, public_uuid, fail-closed en inactivos).
2. JWT y current_user con usuario_id y public_uuid (create_token, create_access_token, get_current_user, get_current_user_dual).
3. Roles contextuales dbo.Usuario_RolesContexto y permisos efectivos dbo.Usuario_PermisosRolModulo (fail-closed Permitido=1).
4. Aislamiento por empresa (EmpresaID), unidad de negocio (UnidadNegocioID) y sucursal (SucursalID).
5. Integración del menú Usuarios (GET /api/admin-sql/users y GET /api/sistema/usuarios) con las API SQL existentes.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


# ============================================================================
# 1. IDENTIDAD SQL CANÓNICA (dbo.Usuario_Catalogo)
# ============================================================================

def test_sql_user_identity_resolves_usuario_id_and_public_uuid(monkeypatch):
    from core.auth import sql_user_identity as identity_mod

    class FakeCursor:
        description = [("UsuarioID",), ("PublicUUID",), ("Email",), ("Activo",)]

        def execute(self, sql, params=()):
            self.sql = sql
            self.params = params

        def fetchone(self):
            return (25, "uuid-canon-25", "operador@edarsa.com.mx", 1)

    class FakeConn:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def cursor(self):
            return FakeCursor()

    monkeypatch.setattr(identity_mod, "get_sql_connection", lambda: FakeConn())

    user = {"id": "uuid-canon-25", "email": "operador@edarsa.com.mx", "role": "Operador"}
    enriched = identity_mod.enrich_current_user_with_sql_id(user)

    assert enriched["usuario_id"] == 25
    assert enriched["UsuarioID"] == 25
    assert enriched["public_uuid"] == "uuid-canon-25"
    assert enriched["PublicUUID"] == "uuid-canon-25"


def test_sql_user_identity_fails_closed_for_inactive_user(monkeypatch):
    from core.auth import sql_user_identity as identity_mod

    class FakeCursor:
        description = [("UsuarioID",), ("PublicUUID",), ("Email",), ("Activo",)]

        def execute(self, sql, params=()):
            pass

        def fetchone(self):
            return (99, "uuid-inactivo-99", "baja@edarsa.com.mx", 0)

    class FakeConn:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def cursor(self):
            return FakeCursor()

    monkeypatch.setattr(identity_mod, "get_sql_connection", lambda: FakeConn())

    assert identity_mod.resolve_sql_user_identity({"email": "baja@edarsa.com.mx"}) is None
    assert identity_mod.resolve_sql_usuario_id({"email": "baja@edarsa.com.mx"}) is None


def test_auth_repository_and_user_repo_sql_expose_canonical_identity():
    from modules.auth.repository import AuthRepository
    from modules.auth.schemas import User
    from core.auth.user_repository_sql import AuthRepositorySQL

    normalized = AuthRepository._normalize_user({
        "UsuarioID": 14,
        "PublicUUID": "pub-uuid-14",
        "Email": "admin@edarsa.com.mx",
        "Username": "admin",
        "Nombre": "Admin",
        "Activo": 1,
        "CodigoRol": "ADMIN",
        "NombreRol": "Administrador",
    })
    assert normalized["usuario_id"] == 14
    assert normalized["public_uuid"] == "pub-uuid-14"
    assert normalized["role"] == "Administrador"
    assert normalized["role_code"] == "ADMIN"

    resp = AuthRepository.build_user_response(normalized)
    assert resp["usuario_id"] == 14
    assert resp["public_uuid"] == "pub-uuid-14"

    schema_instance = User(**resp)
    assert schema_instance.usuario_id == 14
    assert schema_instance.public_uuid == "pub-uuid-14"

    sql_repo = AuthRepositorySQL()
    sql_dict = sql_repo._build_user_dict(
        (14, "admin@edarsa.com.mx", "Admin", "hashed-pw", 1, "pub-uuid-14", None),
        {"rol_id": 2, "codigo": "ADMIN", "nombre": "Administrador", "nivel": 90},
        ["emp-1", "emp-2"],
        "emp-1",
    )
    assert sql_dict["usuario_id"] == 14
    assert sql_dict["public_uuid"] == "pub-uuid-14"


# ============================================================================
# 2. JWT Y CURRENT_USER CON USUARIO_ID Y PUBLIC_UUID
# ============================================================================

@pytest.mark.asyncio
async def test_jwt_and_get_current_user_carry_usuario_id_and_public_uuid():
    from core.security import create_token, create_access_token, verify_token, get_current_user
    from modules.auth.repository import AuthRepository

    tok = create_token(
        user_id="pub-uuid-77",
        email="gerente@edarsa.com.mx",
        role="Gerente",
        usuario_id=77,
        public_uuid="pub-uuid-77",
    )
    payload = verify_token(tok)
    assert payload["usuario_id"] == 77
    assert payload["public_uuid"] == "pub-uuid-77"

    tok2 = create_access_token(
        user_id="pub-uuid-77",
        email="gerente@edarsa.com.mx",
        role="Gerente",
        usuario_id=77,
        public_uuid="pub-uuid-77",
    )
    payload2 = verify_token(tok2)
    assert payload2["usuario_id"] == 77
    assert payload2["public_uuid"] == "pub-uuid-77"

    fake_user = {
        "id": "pub-uuid-77",
        "usuario_id": 77,
        "_sql_id": 77,
        "public_uuid": "pub-uuid-77",
        "email": "gerente@edarsa.com.mx",
        "name": "Gerente Test",
        "role": "Gerente",
        "role_code": "GERENTE",
        "active": True,
        "allowed_companies": ["1"],
        "allowed_servers": [],
        "allowed_sucursales": {},
    }

    with patch.object(AuthRepository, "get_user_by_id", return_value=fake_user):
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=tok)
        current = await get_current_user(creds)
        assert current["usuario_id"] == 77
        assert current["UsuarioID"] == 77
        assert current["public_uuid"] == "pub-uuid-77"
        assert current["PublicUUID"] == "pub-uuid-77"


@pytest.mark.asyncio
async def test_get_current_user_rejects_inactive_sql_user_fail_closed():
    from core.security import create_token, get_current_user
    from modules.auth.repository import AuthRepository

    tok = create_token(
        user_id="pub-uuid-88",
        email="inactivo@edarsa.com.mx",
        role="Usuario",
        usuario_id=88,
        public_uuid="pub-uuid-88",
    )
    inactive_user = {
        "id": "pub-uuid-88",
        "usuario_id": 88,
        "public_uuid": "pub-uuid-88",
        "email": "inactivo@edarsa.com.mx",
        "active": False,
    }

    with patch.object(AuthRepository, "get_user_by_id", return_value=inactive_user):
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=tok)
        with pytest.raises(HTTPException) as exc:
            await get_current_user(creds)
        assert exc.value.status_code == 401


# ============================================================================
# 3. ROLES CONTEXTUALES, PERMISOS EFECTIVOS FAIL-CLOSED Y AISLAMIENTO (RBACContextService)
# ============================================================================

def test_rbac_context_service_fail_closed_and_scope_isolation(monkeypatch):
    from modules.rbac_context_sql import context_service as cs_mod
    from modules.rbac_context_sql.context_service import RBACContextService

    class FakeContextCursor:
        def __init__(self):
            self.description = []
            self._one = None
            self._all = []

        def execute(self, sql, params=()):
            if "FROM dbo.Usuario_Catalogo u" in sql:
                uid = params[0]
                self.description = [
                    ("UsuarioID",),
                    ("PublicUUID",),
                    ("Email",),
                    ("NombreCompleto",),
                    ("Activo",),
                    ("FechaAlta",),
                    ("FechaModificacion",),
                ]
                if uid == 999:
                    self._one = (999, "uuid-999", "off@edarsa.com", "Inactivo", 0, None, None)
                else:
                    self._one = (uid, f"uuid-{uid}", "user@edarsa.com", "User Activo", 1, None, None)
            elif "SELECT DISTINCT" in sql and "FROM dbo.Usuario_RolesContexto urc" in sql:
                self.description = [
                    ("UnidadNegocioID",),
                    ("UnidadNegocioNombre",),
                    ("EmpresaID",),
                    ("NombreEmpresa",),
                    ("SucursalID",),
                    ("NombreSucursal",),
                ]
                self._all = [("UN_NORTE", "Unidad Norte", 1, "Empresa Uno", 101, "Sucursal 101")]
            elif "urc.UsuarioRolContextoID" in sql:
                self.description = [
                    ("UsuarioRolContextoID",),
                    ("UsuarioID",),
                    ("RolID",),
                    ("CodigoRol",),
                    ("NombreRol",),
                    ("EmpresaID",),
                    ("UnidadNegocioID",),
                    ("SucursalID",),
                    ("EsRolPrimario",),
                    ("Activo",),
                ]
                self._all = [(1, 10, 3, "GERENTE", "Gerente", 1, "UN_NORTE", 101, 1, 1)]
            elif "FROM dbo.Usuario_RolesContexto urc" in sql and "dbo.Usuario_PermisosRolModulo prm" in sql:
                self.description = [
                    ("RolID",),
                    ("CodigoRol",),
                    ("NombreRol",),
                    ("EmpresaID",),
                    ("UnidadNegocioID",),
                    ("SucursalID",),
                    ("ModuloID",),
                    ("CodigoModulo",),
                    ("NombreModulo",),
                    ("AccionID",),
                    ("CodigoAccion",),
                    ("NombreAccion",),
                    ("Permitido",),
                    ("RestriccionPropietario",),
                    ("RestriccionSucursal",),
                    ("RequiereAutorizacion",),
                ]
                self._all = [
                    (3, "GERENTE", "Gerente", 1, "UN_NORTE", 101, 5, "USUARIOS", "Usuarios", 1, "VER", "Ver", 1, 0, 0, 0),
                    (3, "GERENTE", "Gerente", 1, "UN_NORTE", 101, 5, "USUARIOS", "Usuarios", 2, "ELIMINAR", "Eliminar", 0, 0, 0, 0),
                ]

        def fetchone(self):
            return self._one

        def fetchall(self):
            return list(self._all)

    class FakeContextConn:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def cursor(self):
            return FakeContextCursor()

    monkeypatch.setattr(cs_mod, "get_sql_connection", lambda: FakeContextConn())
    svc = RBACContextService()

    # Usuario inactivo -> fail-closed None
    assert svc.get_user_context(999) is None

    # Contexto válido dentro del alcance -> devuelve permisos con Permitido=1 únicamente
    ctx = svc.get_user_context(
        10,
        unidad_negocio_id="UN_NORTE",
        empresa_id=1,
        sucursal_id=101,
        raise_on_forbidden=True,
    )
    assert ctx is not None
    assert ctx["usuario_id"] == 10
    assert ctx["public_uuid"] == "uuid-10"
    assert len(ctx["permisos_efectivos"]) == 1
    assert ctx["permisos_efectivos"][0]["CodigoPermiso"] == "USUARIOS_VER"

    # Aislamiento por EmpresaID: solicitar empresa 2 (no autorizada) lanza PermissionError
    with pytest.raises(PermissionError):
        svc.get_user_context(10, empresa_id=2, raise_on_forbidden=True)

    # Aislamiento por UnidadNegocioID: solicitar UN_SUR (no autorizada) lanza PermissionError
    with pytest.raises(PermissionError):
        svc.get_user_context(10, unidad_negocio_id="UN_SUR", raise_on_forbidden=True)

    # Aislamiento por SucursalID: solicitar sucursal 202 (no autorizada) lanza PermissionError
    with pytest.raises(PermissionError):
        svc.get_user_context(10, sucursal_id=202, raise_on_forbidden=True)


# ============================================================================
# 4. ENDPOINTS RBAC CONTEXT SQL (AUTORIZACIÓN, AISLAMIENTO Y FAIL-CLOSED)
# ============================================================================

@pytest.mark.asyncio
async def test_rbac_context_routes_enforce_permissions_and_isolation(monkeypatch):
    from modules.rbac_context_sql import routes as rc_routes

    monkeypatch.setattr(
        rc_routes,
        "enrich_current_user_with_sql_id",
        lambda u: {**u, "usuario_id": u.get("usuario_id", 10), "UsuarioID": u.get("usuario_id", 10)},
    )

    # Usuario regular sin permisos administrativos intentando consultar otro usuario -> 403
    monkeypatch.setattr(rc_routes, "_fetch_one", lambda sql, params=(): None)
    monkeypatch.setattr(rc_routes, "_fetch_all", lambda sql, params=(): [])

    with pytest.raises(HTTPException) as exc:
        await rc_routes.listar_roles_contexto_usuario(
            usuario_id=50,
            current_user={"id": "u-10", "usuario_id": 10, "email": "op@edarsa.com", "role": "Operador"},
        )
    assert exc.value.status_code == 403

    # Admin con alcance limitado a EmpresaID=1 intentando crear rol en EmpresaID=2 -> 403
    def scoped_admin_fetch_all(sql, params=()):
        if "FROM dbo.Usuario_RolesContexto" in sql or "FROM dbo.Usuario_EmpresasAsignacion" in sql:
            return [{"EmpresaID": 1, "UnidadNegocioID": "UN_1", "SucursalID": 10}]
        return []

    monkeypatch.setattr(
        rc_routes,
        "_fetch_one",
        lambda sql, params=(): {"UsuarioID": 50, "Activo": 1} if "Usuario_Catalogo" in sql else None,
    )
    monkeypatch.setattr(rc_routes, "_fetch_all", scoped_admin_fetch_all)

    with pytest.raises(HTTPException) as exc_create:
        await rc_routes.crear_rol_contexto_usuario(
            usuario_id=50,
            body={"rol_id": 4, "empresa_id": 2, "unidad_negocio_id": "UN_1", "sucursal_id": 10},
            current_user={"id": "adm-10", "usuario_id": 10, "email": "adm@edarsa.com", "role": "Administrador"},
        )
    assert exc_create.value.status_code == 403
    assert "EmpresaID=2" in str(exc_create.value.detail)

    # Consulta propia de permisos efectivos filtra Permitido=1 (fail-closed)
    def effective_perms_fetch_all(sql, params=()):
        if "Usuario_PermisosRolModulo" in sql:
            return [
                {"UsuarioID": 10, "RolID": 2, "CodigoModulo": "USUARIOS", "CodigoAccion": "VER", "Permitido": 1},
                {"UsuarioID": 10, "RolID": 2, "CodigoModulo": "USUARIOS", "CodigoAccion": "BORRAR", "Permitido": 0},
            ]
        return []

    monkeypatch.setattr(rc_routes, "_fetch_all", effective_perms_fetch_all)
    perms = await rc_routes.obtener_permisos_efectivos_usuario(
        usuario_id=10,
        current_user={"id": "u-10", "usuario_id": 10, "email": "op@edarsa.com", "role": "Operador"},
    )
    assert len(perms) == 1
    assert perms[0]["CodigoAccion"] == "VER"


# ============================================================================
# 5. SISTEMA USERS SQL Y MENÚ USUARIOS (ADMIN SQL) CON AISLAMIENTO E IDENTIDAD
# ============================================================================

@pytest.mark.asyncio
async def test_sistema_users_sql_enforces_rbac_and_scope(monkeypatch):
    from modules.sistema_users_sql import routes as su_routes

    monkeypatch.setattr(
        su_routes,
        "enrich_current_user_with_sql_id",
        lambda u: {**u, "usuario_id": u.get("usuario_id", 20), "UsuarioID": u.get("usuario_id", 20)},
    )
    monkeypatch.setattr(su_routes, "_fetch_one", lambda sql, params=(): None)
    monkeypatch.setattr(su_routes, "_fetch_all", lambda sql, params=(): [])

    # Sin permiso USUARIOS_VER ni rol admin -> 403 fail-closed
    with pytest.raises(HTTPException) as exc:
        await su_routes.listar_usuarios(
            current_user={"id": "u-20", "usuario_id": 20, "email": "visor@edarsa.com", "role": "Visor"},
        )
    assert exc.value.status_code == 403

    # Con rol Administrador y alcance en EmpresaID=1 -> sólo devuelve usuarios de EmpresaID=1
    def fake_fetch_all(sql, params=()):
        if "FROM Usuario_Catalogo u" in sql:
            return [
                {"UsuarioID": 21, "PublicUUID": "uuid-21", "Email": "u21@edarsa.com", "NombreCompleto": "User 21", "Activo": 1},
                {"UsuarioID": 22, "PublicUUID": "uuid-22", "Email": "u22@edarsa.com", "NombreCompleto": "User 22", "Activo": 1},
            ]
        if "FROM dbo.Usuario_RolesContexto" in sql or "FROM dbo.Usuario_EmpresasAsignacion" in sql:
            uid = params[0]
            if uid in (20, 21):
                return [{"UsuarioRolContextoID": 1, "UsuarioID": uid, "RolID": 2, "CodigoRol": "ADMIN", "NombreRol": "Administrador", "EmpresaID": 1, "UnidadNegocioID": "UN1", "SucursalID": 1, "EsRolPrimario": 1, "Activo": 1}]
            if uid == 22:
                return [{"UsuarioRolContextoID": 2, "UsuarioID": 22, "RolID": 3, "CodigoRol": "OPERADOR", "NombreRol": "Operador", "EmpresaID": 2, "UnidadNegocioID": "UN2", "SucursalID": 2, "EsRolPrimario": 1, "Activo": 1}]
        return []

    monkeypatch.setattr(su_routes, "_fetch_all", fake_fetch_all)

    users = await su_routes.listar_usuarios(
        current_user={"id": "u-20", "usuario_id": 20, "email": "admin1@edarsa.com", "role": "Administrador"},
    )
    assert len(users) == 1
    assert users[0]["usuario_id"] == 21
    assert users[0]["public_uuid"] == "uuid-21"
    assert len(users[0]["roles_contexto"]) >= 1


@pytest.mark.asyncio
async def test_admin_sql_get_users_menu_integration_and_isolation(monkeypatch):
    from modules.admin_sql import routes as admin_routes

    monkeypatch.setattr(
        admin_routes,
        "enrich_current_user_with_sql_id",
        lambda u: {**u, "usuario_id": u.get("usuario_id", 1), "UsuarioID": u.get("usuario_id", 1)},
    )
    monkeypatch.setattr(admin_routes.rbac_pilot_service, "get_rbac_map", lambda: {})

    def fake_execute_query(sql, params=()):
        if "FROM Usuario_Catalogo u" in sql:
            return [
                {
                    "id": "1",
                    "UsuarioID": "1",
                    "PublicUUID": "uuid-admin-1",
                    "username": "admin1",
                    "email": "admin1@edarsa.com",
                    "nombre": "Admin Uno",
                    "name": "Admin Uno",
                    "nombre_completo": "Admin Uno",
                    "apellidos": "",
                    "puesto": "Admin",
                    "departamento": "TI",
                    "activo": 1,
                    "bloqueado": 0,
                    "role": "Administrador",
                    "role_code": "ADMIN",
                    "role_level": 90,
                    "RolID": 2,
                },
                {
                    "id": "2",
                    "UsuarioID": "2",
                    "PublicUUID": "uuid-user-2",
                    "username": "user2",
                    "email": "user2@edarsa.com",
                    "nombre": "User Dos",
                    "name": "User Dos",
                    "nombre_completo": "User Dos",
                    "apellidos": "",
                    "puesto": "Analista",
                    "departamento": "Ops",
                    "activo": 1,
                    "bloqueado": 0,
                    "role": "Operador",
                    "role_code": "OPERADOR",
                    "role_level": 20,
                    "RolID": 5,
                },
            ]
        if "FROM dbo.Usuario_RolesContexto urc" in sql:
            return [
                {
                    "UsuarioID": "1",
                    "UsuarioRolContextoID": 10,
                    "RolID": 2,
                    "CodigoRol": "ADMIN",
                    "NombreRol": "Administrador",
                    "EmpresaID": 1,
                    "UnidadNegocioID": "UN_CORP",
                    "SucursalID": 100,
                    "EsRolPrimario": 1,
                    "Activo": 1,
                },
                {
                    "UsuarioID": "2",
                    "UsuarioRolContextoID": 11,
                    "RolID": 5,
                    "CodigoRol": "OPERADOR",
                    "NombreRol": "Operador",
                    "EmpresaID": 2,
                    "UnidadNegocioID": "UN_EXTERNA",
                    "SucursalID": 200,
                    "EsRolPrimario": 1,
                    "Activo": 1,
                },
            ]
        return []

    monkeypatch.setattr(admin_routes, "execute_query", fake_execute_query)

    # Admin con alcance en EmpresaID=1 sólo ve usuarios de EmpresaID=1 y recibe usuario_id, public_uuid y roles_contexto
    res = await admin_routes.get_users(
        incluir_inactivos=False,
        current_user={"id": "uuid-admin-1", "usuario_id": 1, "email": "admin1@edarsa.com", "role": "Administrador"},
    )
    assert len(res) == 1
    assert res[0]["usuario_id"] == 1
    assert res[0]["public_uuid"] == "uuid-admin-1"
    assert res[0]["roles_contexto"][0]["empresa_id"] == 1

    # SuperAdmin global ve todos los usuarios sin restricción de empresa
    res_super = await admin_routes.get_users(
        incluir_inactivos=False,
        current_user={"id": "uuid-super", "usuario_id": 99, "email": "super@edarsa.com", "role": "SuperAdministrador", "role_code": "SUPERADMIN"},
    )
    assert len(res_super) == 2
