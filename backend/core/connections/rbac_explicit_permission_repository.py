"""
Consulta estricta de permisos efectivos para flujos sensibles.

La conexión es inyectada y su identidad se valida antes de consultar RBAC.
Este módulo no administra roles, no escribe y no maneja secretos.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from core.connections.edarsahub_readonly_repository import (
    validate_readonly_identity,
)


PERMISSION_CONNECTIONS_VIEW = "CONEXIONES_VER"

EXPLICIT_PERMISSION_SQL = """
SELECT TOP 1
    1 AS permiso_concedido
FROM dbo.Usuario_Catalogo AS u
INNER JOIN dbo.Usuario_RolesAsignacion AS ura
    ON ura.UsuarioID = u.UsuarioID
    AND ura.Activo = 1
INNER JOIN dbo.Usuario_Roles AS r
    ON r.RolID = ura.RolID
    AND r.Activo = 1
INNER JOIN dbo.Usuario_PermisosRolModulo AS prm
    ON prm.RolID = r.RolID
    AND prm.Activo = 1
    AND prm.Permitido = 1
INNER JOIN dbo.Usuario_Modulos AS m
    ON m.ModuloID = prm.ModuloID
    AND m.Activo = 1
INNER JOIN dbo.Usuario_Acciones AS a
    ON a.AccionID = prm.AccionID
    AND a.Activo = 1
WHERE u.Activo = 1
  AND LOWER(LTRIM(RTRIM(u.Email))) =
      LOWER(LTRIM(RTRIM(%s)))
  AND (
        UPPER(
            CONCAT(
                LTRIM(RTRIM(m.CodigoModulo)),
                '_',
                LTRIM(RTRIM(a.CodigoAccion))
            )
        ) = UPPER(LTRIM(RTRIM(%s)))
     OR LOWER(
            CONCAT(
                LTRIM(RTRIM(m.CodigoModulo)),
                '.',
                LTRIM(RTRIM(a.CodigoAccion))
            )
        ) = LOWER(LTRIM(RTRIM(%s)))
  )
"""


class ExplicitPermissionRepositoryError(RuntimeError):
    """Error base del repositorio de permisos explícitos."""


class InvalidPermissionConnectionFactory(
    ExplicitPermissionRepositoryError
):
    """La dependencia para abrir la conexión no es válida."""


class AuthenticatedEmailRequired(
    ExplicitPermissionRepositoryError
):
    """No se recibió un usuario autenticado con email."""


class PermissionCodeRequired(
    ExplicitPermissionRepositoryError
):
    """No se recibió un código de permiso."""


class PermissionConnectionNotCreated(
    ExplicitPermissionRepositoryError
):
    """La factory no devolvió una conexión."""


def _authenticated_email(user: Any) -> str:
    if not isinstance(user, Mapping):
        raise AuthenticatedEmailRequired(
            "Se requiere un usuario autenticado"
        )

    email = str(user.get("email") or "").strip()

    if not email:
        raise AuthenticatedEmailRequired(
            "Se requiere email del usuario autenticado"
        )

    return email


def _permission_code(permission: Any) -> str:
    value = str(permission or "").strip()

    if not value:
        raise PermissionCodeRequired(
            "Se requiere código de permiso"
        )

    return value


def has_explicit_permission_readonly(
    *,
    user: Mapping[str, Any],
    permission: str,
    connection_factory: Callable[[], Any],
) -> bool:
    """
    Comprueba un permiso efectivo sin bypass por rol.

    Orden obligatorio:
    1. Validar entradas.
    2. Abrir la conexión inyectada.
    3. Validar identidad SQL canónica.
    4. Consultar el permiso mediante parámetros.
    5. Cerrar cursor y conexión.
    """

    if not callable(connection_factory):
        raise InvalidPermissionConnectionFactory(
            "connection_factory debe ser invocable"
        )

    email = _authenticated_email(user)
    permission_code = _permission_code(permission)

    connection = connection_factory()

    if connection is None:
        raise PermissionConnectionNotCreated(
            "No se obtuvo una conexión SQL"
        )

    cursor = None

    try:
        validate_readonly_identity(connection)

        cursor = connection.cursor()
        cursor.execute(
            EXPLICIT_PERMISSION_SQL,
            (
                email,
                permission_code,
                permission_code,
            ),
        )

        return cursor.fetchone() is not None

    finally:
        if cursor is not None:
            close_cursor = getattr(cursor, "close", None)
            if callable(close_cursor):
                close_cursor()

        close_connection = getattr(connection, "close", None)
        if callable(close_connection):
            close_connection()
