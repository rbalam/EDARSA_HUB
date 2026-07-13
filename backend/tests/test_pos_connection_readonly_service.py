from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any

import pytest

import core.connections.pos_connection_readonly_service as service_module
from core.connections.pos_connection_readonly_service import (
    InvalidCompositionDependency,
    MetadataRepositoryContractError,
    ResolverContractError,
    build_pos_connection_metadata_service,
)


SAFE_METADATA = {
    "unidad_negocio_codigo": "130MID",
    "unidad_negocio_nombre": "130 Merida",
    "unidad_negocio_pk": "unit-1",
    "server_id": "server-1",
    "servidor_nombre": "POS 130MID",
    "host": "pos.internal",
    "port": 1433,
    "database_name": "POS",
    "username": "reader",
    "servidor_system_type": "SOFTRESTAURANT",
    "unidad_activo": True,
    "servidor_activo": True,
    "visible_en_operaciones": True,
    "empresa_id": "empresa-1",
}


@pytest.mark.asyncio
async def test_composes_permission_scope_and_metadata() -> None:
    events: list[str] = []

    def connection_factory() -> object:
        return object()

    def permission_repository(
        *,
        user: dict[str, Any],
        permission: str,
        connection_factory: Any,
    ) -> bool:
        events.append("permission")
        assert user["email"] == "user@example.com"
        assert permission == "CONEXIONES_VER"
        assert callable(connection_factory)
        return True

    async def unidad_scope_resolver(
        user: dict[str, Any],
        unidad_codigo: str,
    ) -> dict[str, Any]:
        events.append("scope")
        assert user["email"] == "user@example.com"
        assert unidad_codigo == "130MID"

        return {
            "unidad_negocio_codigo": "130MID",
            "server_id": "server-1",
        }

    def metadata_repository(
        *,
        unidad_codigo: str,
        connection_factory: Any,
    ) -> dict[str, Any]:
        events.append("metadata")
        assert unidad_codigo == "130MID"
        assert callable(connection_factory)
        return dict(SAFE_METADATA)

    service = build_pos_connection_metadata_service(
        connection_factory=connection_factory,
        unidad_scope_resolver=unidad_scope_resolver,
        permission_repository=permission_repository,
        metadata_repository=metadata_repository,
    )

    result = await service(
        user={"email": "user@example.com"},
        unidad_codigo=" 130mid ",
    )

    assert events == [
        "permission",
        "scope",
        "metadata",
    ]
    assert result["unidad_negocio_codigo"] == "130MID"
    assert result["server_id"] == "server-1"
    assert result["config_origin"] == (
        "EDARSAHUB_SQL_CANONICAL"
    )
    assert result["secrets_exposed"] is False
    assert result["pos_connection_executed"] is False


@pytest.mark.asyncio
async def test_permission_denial_stops_before_scope_and_metadata(
) -> None:
    events: list[str] = []

    def permission_repository(**kwargs: Any) -> bool:
        events.append("permission")
        return False

    def unidad_scope_resolver(
        user: dict[str, Any],
        unidad_codigo: str,
    ) -> dict[str, Any]:
        events.append("scope")
        return {
            "unidad_negocio_codigo": unidad_codigo,
        }

    def metadata_repository(**kwargs: Any) -> dict[str, Any]:
        events.append("metadata")
        return dict(SAFE_METADATA)

    service = build_pos_connection_metadata_service(
        connection_factory=lambda: object(),
        unidad_scope_resolver=unidad_scope_resolver,
        permission_repository=permission_repository,
        metadata_repository=metadata_repository,
    )

    with pytest.raises(Exception) as error:
        await service(
            user={"email": "user@example.com"},
            unidad_codigo="130MID",
        )

    assert error.value.__class__.__name__ == (
        "ExplicitPermissionRequired"
    )
    assert events == ["permission"]


@pytest.mark.asyncio
async def test_scope_denial_stops_before_metadata() -> None:
    events: list[str] = []

    def permission_repository(**kwargs: Any) -> bool:
        events.append("permission")
        return True

    def unidad_scope_resolver(
        user: dict[str, Any],
        unidad_codigo: str,
    ) -> dict[str, Any]:
        events.append("scope")
        return {
            "unidad_negocio_codigo": "OTRA",
        }

    def metadata_repository(**kwargs: Any) -> dict[str, Any]:
        events.append("metadata")
        return dict(SAFE_METADATA)

    service = build_pos_connection_metadata_service(
        connection_factory=lambda: object(),
        unidad_scope_resolver=unidad_scope_resolver,
        permission_repository=permission_repository,
        metadata_repository=metadata_repository,
    )

    with pytest.raises(Exception) as error:
        await service(
            user={"email": "user@example.com"},
            unidad_codigo="130MID",
        )

    assert error.value.__class__.__name__ == "ScopeDenied"
    assert events == [
        "permission",
        "scope",
    ]


@pytest.mark.asyncio
async def test_metadata_cache_is_request_scoped() -> None:
    metadata_calls: list[str] = []

    def metadata_repository(
        *,
        unidad_codigo: str,
        connection_factory: Any,
    ) -> dict[str, Any]:
        metadata_calls.append(unidad_codigo)
        return dict(SAFE_METADATA)

    async def resolver(
        **dependencies: Any,
    ) -> dict[str, Any]:
        server_resolver = dependencies["server_resolver"]

        first = server_resolver("130MID")
        second = server_resolver("130mid")

        assert first == second

        return {
            "unidad_negocio_codigo": "130MID",
            "server_id": "server-1",
        }

    service = build_pos_connection_metadata_service(
        connection_factory=lambda: object(),
        unidad_scope_resolver=lambda user, code: {
            "unidad_negocio_codigo": code,
        },
        metadata_repository=metadata_repository,
        resolver=resolver,
    )

    await service(
        user={"email": "user@example.com"},
        unidad_codigo="130MID",
    )

    assert metadata_calls == ["130MID"]

    await service(
        user={"email": "user@example.com"},
        unidad_codigo="130MID",
    )

    assert metadata_calls == [
        "130MID",
        "130MID",
    ]


@pytest.mark.parametrize(
    "dependency_name",
    [
        "connection_factory",
        "unidad_scope_resolver",
        "permission_repository",
        "metadata_repository",
        "resolver",
    ],
)
def test_requires_callable_dependencies(
    dependency_name: str,
) -> None:
    dependencies: dict[str, Any] = {
        "connection_factory": lambda: object(),
        "unidad_scope_resolver": lambda user, code: {},
        "permission_repository": lambda **kwargs: True,
        "metadata_repository": lambda **kwargs: {},
        "resolver": lambda **kwargs: {},
    }

    dependencies[dependency_name] = object()

    with pytest.raises(
        InvalidCompositionDependency,
        match=dependency_name,
    ):
        build_pos_connection_metadata_service(
            **dependencies,
        )


@pytest.mark.asyncio
async def test_rejects_non_mapping_metadata() -> None:
    service = build_pos_connection_metadata_service(
        connection_factory=lambda: object(),
        unidad_scope_resolver=lambda user, code: {
            "unidad_negocio_codigo": code,
        },
        permission_repository=lambda **kwargs: True,
        metadata_repository=lambda **kwargs: None,
    )

    with pytest.raises(
        MetadataRepositoryContractError,
    ):
        await service(
            user={"email": "user@example.com"},
            unidad_codigo="130MID",
        )


@pytest.mark.asyncio
async def test_rejects_non_mapping_resolver_result() -> None:
    service = build_pos_connection_metadata_service(
        connection_factory=lambda: object(),
        unidad_scope_resolver=lambda user, code: {
            "unidad_negocio_codigo": code,
        },
        resolver=lambda **kwargs: 123,
    )

    with pytest.raises(ResolverContractError):
        await service(
            user={"email": "user@example.com"},
            unidad_codigo="130MID",
        )


def test_public_api_and_runtime_dependencies() -> None:
    builder_signature = inspect.signature(
        build_pos_connection_metadata_service
    )

    assert "server_id" not in builder_signature.parameters

    service = build_pos_connection_metadata_service(
        connection_factory=lambda: object(),
        unidad_scope_resolver=lambda user, code: {},
    )

    service_signature = inspect.signature(service)

    assert "server_id" not in service_signature.parameters

    path = Path(service_module.__file__)
    source = path.read_text(encoding="utf-8").casefold()

    forbidden_tokens = (
        "pymssql",
        "pyodbc",
        "pymongo",
        "motor",
        "mongodb",
        "mongodb_id",
        "get_sql_connection",
        "server_registry",
        "core.context_resolver",
        "user_access_context",
        "repository_sql",
        "rbac.middleware",
        "load_dotenv",
        "os.getenv",
    )

    for token in forbidden_tokens:
        assert token not in source
