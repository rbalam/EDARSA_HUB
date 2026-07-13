import asyncio
import inspect
from pathlib import Path

import pytest

from core.connections.pos_connection_resolver import (
    AuthenticationRequired,
    CanonicalMappingError,
    ExplicitPermissionRequired,
    ScopeDenied,
    UnsafeMetadataError,
    resolve_pos_connection_metadata,
)


USER = {
    "id": "user-1",
    "email": "auditor@example.com",
    "role": "SUPERADMIN",
}

CONTEXT = {
    "unidad_negocio_codigo": "130MID",
    "unidad_negocio_pk": "unidad-1",
    "server_id": "server-1",
}

SERVER = {
    "unidad_negocio_codigo": "130MID",
    "unidad_negocio_nombre": "130 Merida",
    "unidad_negocio_pk": "unidad-1",
    "server_id": "server-1",
    "servidor_nombre": "POS Merida",
    "servidor_system_type": "SoftRestaurant",
    "unidad_activo": True,
    "servidor_activo": True,
    "visible_en_operaciones": True,
    "host": "pos.internal",
    "port": 1433,
    "database_name": "SoftRestaurant",
    "username": "readonly",
    "empresa_id": "empresa-1",
}


def run(coro):
    return asyncio.run(coro)


def permission_allowed(user, permission):
    return (
        user["email"] == USER["email"]
        and permission == "CONEXIONES_VER"
    )


def context_allowed(user, unidad_codigo):
    assert user["email"] == USER["email"]
    assert unidad_codigo == "130MID"
    return dict(CONTEXT)


def canonical_server(unidad_codigo):
    assert unidad_codigo == "130MID"
    return dict(SERVER)


def resolve(**overrides):
    params = {
        "user": USER,
        "unidad_codigo": "130MID",
        "permission_checker": permission_allowed,
        "unidad_context_resolver": context_allowed,
        "server_resolver": canonical_server,
    }
    params.update(overrides)

    return run(resolve_pos_connection_metadata(**params))


def test_resuelve_metadata_segura_por_unidad():
    result = resolve()

    assert result["unidad_negocio_codigo"] == "130MID"
    assert result["server_id"] == "server-1"
    assert result["config_origin"] == "EDARSAHUB_SQL_CANONICAL"
    assert result["secrets_exposed"] is False
    assert result["pos_connection_executed"] is False
    assert "password" not in result
    assert "password_encrypted" not in result


def test_exige_usuario_autenticado_con_email():
    with pytest.raises(AuthenticationRequired):
        resolve(user={"id": "user-1"})


def test_exige_permiso_explicito():
    with pytest.raises(ExplicitPermissionRequired):
        resolve(permission_checker=lambda user, permission: False)


def test_deniega_unidad_fuera_de_alcance():
    with pytest.raises(ScopeDenied):
        resolve(
            unidad_context_resolver=lambda user, code: {
                **CONTEXT,
                "unidad_negocio_codigo": "CIENFUEGOS",
            }
        )


def test_deniega_mapeo_de_otra_unidad():
    with pytest.raises(CanonicalMappingError):
        resolve(
            server_resolver=lambda code: {
                **SERVER,
                "unidad_negocio_codigo": "ORIGEN",
            }
        )


def test_deniega_server_id_inconsistente():
    with pytest.raises(CanonicalMappingError):
        resolve(
            server_resolver=lambda code: {
                **SERVER,
                "server_id": "server-2",
            }
        )


def test_deniega_servidor_inactivo():
    with pytest.raises(CanonicalMappingError):
        resolve(
            server_resolver=lambda code: {
                **SERVER,
                "servidor_activo": False,
            }
        )


def test_rechaza_cualquier_campo_secreto():
    with pytest.raises(UnsafeMetadataError):
        resolve(
            server_resolver=lambda code: {
                **SERVER,
                "password_encrypted": "valor-no-permitido",
            }
        )


def test_acepta_adaptadores_asincronos():
    async def permission_async(user, permission):
        return permission == "CONEXIONES_VER"

    async def context_async(user, code):
        return dict(CONTEXT)

    async def server_async(code):
        return dict(SERVER)

    result = resolve(
        permission_checker=permission_async,
        unidad_context_resolver=context_async,
        server_resolver=server_async,
    )

    assert result["server_id"] == "server-1"


def test_api_publica_no_acepta_server_id_directo():
    parameters = inspect.signature(
        resolve_pos_connection_metadata
    ).parameters

    assert "server_id" not in parameters


def test_modulo_no_abre_sql_pos_ni_descifra_secretos():
    module_path = (
        Path(__file__).parents[1]
        / "core"
        / "connections"
        / "pos_connection_resolver.py"
    )
    source = module_path.read_text(
        encoding="utf-8",
        errors="replace",
    ).lower()

    forbidden_runtime_terms = (
        "get_external_sql_connection",
        "pymssql",
        "pyodbc",
        "decrypt_secret",
        "execute_sql_query",
        "get_sql_connection",
    )

    for term in forbidden_runtime_terms:
        assert term not in source

    assert "mongo" not in source
