"""
Regresión: canonicidad de rol en AuthRepository._normalize_user.

Contexto del bug: el `role` que viaja en current_user/JWT pasó a ser el CodigoRol
canónico ('SUPERADMIN'), pero ~185 guards de backend y ~47 del frontend comparan
por igualdad contra el NombreRol legacy ('SuperAdministrador'). Con CodigoRol, esos
endpoints negaban acceso al SuperAdministrador (p.ej. /api/config-asignaciones -> 403).

Fix (punto único): _normalize_user expone `role` = NombreRol legacy (lo que esperan
los guards y el frontend) y conserva el CodigoRol canónico en `role_code` /
`_sql_rol_codigo` para el código RBAC canónico-aware.

Equivalencia que debe respetar el backend:
    SUPERADMIN  <-> SuperAdministrador
    ADMIN       <-> Administrador
    SUPERVISOR  <-> Supervisor
    USUARIO     <-> Usuario
    VISOR       <-> Visor
"""
from modules.auth.repository import AuthRepository


def _norm(codigo, nombre):
    return AuthRepository._normalize_user({
        "UsuarioID": 8,
        "Email": "ricardo@edarsa.com.mx",
        "Username": "ricardo",
        "Nombre": "Ricardo",
        "Activo": True,
        "PublicUUID": "uuid-ricardo",
        "CodigoRol": codigo,
        "NombreRol": nombre,
    })


def test_role_es_nombre_legacy_no_codigo():
    u = _norm("SUPERADMIN", "SuperAdministrador")
    assert u["role"] == "SuperAdministrador"  # lo que esperan los guards legacy
    assert u["role_code"] == "SUPERADMIN"      # canónico preservado
    assert u["_sql_rol_codigo"] == "SUPERADMIN"


def test_equivalencias_completas():
    tabla = {
        "SUPERADMIN": "SuperAdministrador",
        "ADMIN": "Administrador",
        "SUPERVISOR": "Supervisor",
        "USUARIO": "Usuario",
        "VISOR": "Visor",
    }
    for codigo, nombre in tabla.items():
        u = _norm(codigo, nombre)
        assert u["role"] == nombre
        assert u["role_code"] == codigo


def test_fallback_sin_nombre_usa_codigo():
    u = _norm("ADMIN", None)
    assert u["role"] == "ADMIN"
    assert u["role_code"] == "ADMIN"


def test_fallback_sin_rol_usa_usuario():
    u = _norm(None, None)
    assert u["role"] == "Usuario"
    assert u["role_code"] == ""
