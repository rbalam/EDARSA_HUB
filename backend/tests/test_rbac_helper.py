"""
Regresión P0-2: RBAC helper SQL-First.
Valida bypass admin (sin SQL) y firma async. No requiere conexión live
porque el bypass por rol ocurre antes de cualquier query.
"""
import asyncio
from core.rbac_helper import verificar_permiso_rbac, _extract_role, BYPASS_ROLES


def test_es_async():
    coro = verificar_permiso_rbac({"role": "SUPERADMIN"}, "USUARIOS")
    assert asyncio.iscoroutine(coro)
    coro.close()


def test_bypass_superadmin():
    r = asyncio.run(verificar_permiso_rbac({"role": "SUPERADMIN", "UsuarioID": 22}, "SISTEMA_USUARIOS_VER"))
    assert r is True


def test_bypass_admin_por_nombre():
    # role = NombreRol 'Administrador' -> 'ADMINISTRADOR' en BYPASS_ROLES
    r = asyncio.run(verificar_permiso_rbac({"role": "Administrador", "UsuarioID": 1}, "SISTEMA_USUARIOS_VER"))
    assert r is True


def test_sin_usuario_es_false():
    r = asyncio.run(verificar_permiso_rbac(None, "SISTEMA_USUARIOS_VER"))
    assert r is False


def test_extract_role_codigorol():
    assert _extract_role({"role": "SuperAdministrador"}) == "SUPERADMINISTRADOR"
    assert "SUPERADMINISTRADOR" in BYPASS_ROLES
