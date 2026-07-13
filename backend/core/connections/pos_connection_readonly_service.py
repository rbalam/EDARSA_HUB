"""
Composición read-only para resolver metadata segura por unidad autorizada.

Todas las dependencias operativas son inyectadas. Este módulo no registra
rutas, no abre conexiones por sí mismo y no administra credenciales.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from inspect import isawaitable
from typing import Any

from core.connections.edarsahub_readonly_repository import (
    get_unit_server_metadata_readonly,
)
from core.connections.pos_connection_resolver import (
    resolve_pos_connection_metadata,
)
from core.connections.rbac_explicit_permission_repository import (
    has_explicit_permission_readonly,
)


class PosConnectionCompositionError(RuntimeError):
    """Error base de la composición read-only."""


class InvalidCompositionDependency(
    PosConnectionCompositionError
):
    """Una dependencia requerida no es invocable."""


class MetadataRepositoryContractError(
    PosConnectionCompositionError
):
    """El repositorio no devolvió una estructura válida."""


class ResolverContractError(
    PosConnectionCompositionError
):
    """El resolvedor final no devolvió una estructura válida."""


def _require_callable(name: str, dependency: Any) -> None:
    if not callable(dependency):
        raise InvalidCompositionDependency(
            f"{name} debe ser invocable"
        )


def build_pos_connection_metadata_service(
    *,
    connection_factory: Callable[[], Any],
    unidad_scope_resolver: Callable[
        [Mapping[str, Any], str],
        Any,
    ],
    permission_repository: Callable[..., Any] = (
        has_explicit_permission_readonly
    ),
    metadata_repository: Callable[..., Any] = (
        get_unit_server_metadata_readonly
    ),
    resolver: Callable[..., Any] = (
        resolve_pos_connection_metadata
    ),
) -> Callable[..., Awaitable[dict[str, Any]]]:
    """
    Construye un servicio por unidad con dependencias fail-closed.

    ``unidad_scope_resolver`` debe validar el alcance efectivo del usuario
    y devolver al menos el código canónico de la unidad autorizada.
    """

    dependencies = {
        "connection_factory": connection_factory,
        "unidad_scope_resolver": unidad_scope_resolver,
        "permission_repository": permission_repository,
        "metadata_repository": metadata_repository,
        "resolver": resolver,
    }

    for name, dependency in dependencies.items():
        _require_callable(name, dependency)

    async def get_metadata(
        *,
        user: Mapping[str, Any],
        unidad_codigo: str,
    ) -> dict[str, Any]:
        metadata_cache: dict[
            str,
            dict[str, Any],
        ] = {}

        def permission_checker(
            candidate_user: Mapping[str, Any],
            permission: str,
        ) -> Any:
            return permission_repository(
                user=candidate_user,
                permission=permission,
                connection_factory=connection_factory,
            )

        def server_resolver(
            requested_code: str,
        ) -> dict[str, Any]:
            normalized_code = str(
                requested_code or ""
            ).strip().upper()

            if normalized_code not in metadata_cache:
                metadata = metadata_repository(
                    unidad_codigo=normalized_code,
                    connection_factory=connection_factory,
                )

                if not isinstance(metadata, Mapping):
                    raise MetadataRepositoryContractError(
                        "El repositorio de metadata debe "
                        "devolver un mapping"
                    )

                metadata_cache[normalized_code] = dict(
                    metadata
                )

            return dict(metadata_cache[normalized_code])

        result = resolver(
            user=user,
            unidad_codigo=unidad_codigo,
            permission_checker=permission_checker,
            unidad_context_resolver=(
                unidad_scope_resolver
            ),
            server_resolver=server_resolver,
        )

        if isawaitable(result):
            result = await result

        if not isinstance(result, Mapping):
            raise ResolverContractError(
                "El resolvedor final debe devolver un mapping"
            )

        return dict(result)

    return get_metadata
