"""
Repositorio read-only para resolver metadata de unidad y servidor.

La conexion se recibe por inyeccion. Este modulo no conoce credenciales,
no abre conexiones externas y no consulta campos secretos.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Dict


EXPECTED_DATABASE = "EDARSAHUB"
EXPECTED_LOGIN = "HRLectura"
EXPECTED_USER = "HRLectura"


class ReadOnlyRepositoryError(RuntimeError):
    """Error base del repositorio read-only."""


class InvalidConnectionFactory(ReadOnlyRepositoryError):
    """La fabrica de conexiones no es valida."""


class DatabaseIdentityMismatch(ReadOnlyRepositoryError):
    """La conexion no corresponde a la identidad SQL autorizada."""


class UnitCodeRequired(ReadOnlyRepositoryError):
    """No se proporciono un codigo de unidad valido."""


class UnitServerMappingNotFound(ReadOnlyRepositoryError):
    """No existe una relacion canonica activa unidad-servidor."""


IDENTITY_SQL = """
SELECT
    DB_NAME() AS database_name,
    SUSER_SNAME() AS login_name,
    USER_NAME() AS database_user
"""

UNIT_SERVER_METADATA_SQL = """
SELECT TOP 1
    u.codigo AS unidad_negocio_codigo,
    u.nombre AS unidad_negocio_nombre,
    CONVERT(varchar(36), u.id) AS unidad_negocio_pk,
    CONVERT(varchar(36), u.server_id) AS server_id,
    u.sucursal_origen_id,
    u.system_type AS unidad_system_type,
    u.activo AS unidad_activo,
    s.nombre AS servidor_nombre,
    s.host,
    s.port,
    s.database_name,
    s.username,
    s.system_type AS servidor_system_type,
    s.activo AS servidor_activo,
    s.visible_en_operaciones,
    CONVERT(varchar(36), s.empresa_id) AS empresa_id
FROM dbo.Unidades_Negocio AS u
INNER JOIN dbo.Servidores_Conexiones AS s
    ON s.id = u.server_id
WHERE UPPER(LTRIM(RTRIM(u.codigo))) = UPPER(%s)
  AND u.activo = 1
  AND s.activo = 1
"""


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _row_to_dict(cursor: Any, row: Any) -> Dict[str, Any]:
    if row is None:
        return {}

    if isinstance(row, Mapping):
        return dict(row)

    description = getattr(cursor, "description", None) or []
    columns = []

    for item in description:
        if isinstance(item, (list, tuple)) and item:
            columns.append(str(item[0]))
        else:
            columns.append(str(getattr(item, "name", "")))

    if not columns or len(columns) != len(row):
        raise ReadOnlyRepositoryError(
            "No se pudo interpretar la fila SQL"
        )

    return dict(zip(columns, row))


def _validate_identity(identity: Mapping[str, Any]) -> None:
    database_name = _normalize_text(
        identity.get("database_name")
    )
    login_name = _normalize_text(
        identity.get("login_name")
    )
    database_user = _normalize_text(
        identity.get("database_user")
    )

    valid = (
        database_name == EXPECTED_DATABASE
        and login_name == EXPECTED_LOGIN
        and database_user == EXPECTED_USER
    )

    if not valid:
        raise DatabaseIdentityMismatch(
            "Identidad SQL no autorizada: "
            f"database={database_name!r}, "
            f"login={login_name!r}, "
            f"user={database_user!r}"
        )


def validate_readonly_identity(connection: Any) -> Dict[str, Any]:
    """
    Valida la identidad SQL antes de permitir consultas de metadata.
    """

    if connection is None:
        raise InvalidConnectionFactory(
            "Conexion SQL requerida"
        )

    cursor = connection.cursor()
    cursor.execute(IDENTITY_SQL)
    identity = _row_to_dict(cursor, cursor.fetchone())

    if not identity:
        raise DatabaseIdentityMismatch(
            "La consulta de identidad no devolvio resultados"
        )

    _validate_identity(identity)
    return identity


def get_unit_server_metadata_readonly(
    *,
    unidad_codigo: str,
    connection_factory: Callable[[], Any],
) -> Dict[str, Any]:
    """
    Obtiene metadata no secreta mediante la relacion canonica unidad-servidor.

    La validacion de identidad se ejecuta antes de consultar tablas.
    """

    normalized_code = _normalize_text(unidad_codigo).upper()

    if not normalized_code:
        raise UnitCodeRequired(
            "Codigo de unidad requerido"
        )

    if not callable(connection_factory):
        raise InvalidConnectionFactory(
            "Fabrica de conexiones requerida"
        )

    connection = connection_factory()

    if connection is None:
        raise InvalidConnectionFactory(
            "La fabrica no devolvio una conexion"
        )

    try:
        validate_readonly_identity(connection)

        cursor = connection.cursor()
        cursor.execute(
            UNIT_SERVER_METADATA_SQL,
            (normalized_code,),
        )

        row = _row_to_dict(cursor, cursor.fetchone())

        if not row:
            raise UnitServerMappingNotFound(
                "Unidad o servidor canonico no encontrado"
            )

        if not _normalize_text(row.get("server_id")):
            raise UnitServerMappingNotFound(
                "La unidad no tiene server_id canonico"
            )

        if row.get("unidad_activo") is False:
            raise UnitServerMappingNotFound(
                "Unidad de negocio inactiva"
            )

        if row.get("servidor_activo") is False:
            raise UnitServerMappingNotFound(
                "Servidor asociado inactivo"
            )

        return {
            "unidad_negocio_codigo": row.get(
                "unidad_negocio_codigo"
            ),
            "unidad_negocio_nombre": row.get(
                "unidad_negocio_nombre"
            ),
            "unidad_negocio_pk": row.get(
                "unidad_negocio_pk"
            ),
            "server_id": row.get("server_id"),
            "sucursal_origen_id": row.get(
                "sucursal_origen_id"
            ),
            "unidad_system_type": row.get(
                "unidad_system_type"
            ),
            "unidad_activo": bool(
                row.get("unidad_activo")
            ),
            "servidor_nombre": row.get(
                "servidor_nombre"
            ),
            "host": row.get("host"),
            "port": row.get("port"),
            "database_name": row.get(
                "database_name"
            ),
            "username": row.get("username"),
            "servidor_system_type": row.get(
                "servidor_system_type"
            ),
            "servidor_activo": bool(
                row.get("servidor_activo")
            ),
            "visible_en_operaciones": bool(
                row.get("visible_en_operaciones")
            ),
            "empresa_id": row.get("empresa_id"),
            "config_origin": "EDARSAHUB_SQL_HRLECTURA",
            "secrets_exposed": False,
        }
    finally:
        connection.close()

UNIT_SCOPE_METADATA_SQL = """
WITH candidates AS (
    SELECT
        CONVERT(varchar(36), u.id)
            AS unidad_negocio_pk,
        u.codigo AS unidad_negocio_codigo,
        u.nombre AS unidad_negocio_nombre,
        CONVERT(varchar(36), u.server_id)
            AS server_id,
        u.sucursal_origen_id,
        u.system_type,
        u.activo AS unidad_activo,
        s.activo AS servidor_activo,
        CONVERT(varchar(36), s.empresa_id)
            AS empresa_id,
        s.visible_en_operaciones
    FROM dbo.Unidades_Negocio AS u
    INNER JOIN dbo.Servidores_Conexiones AS s
        ON s.id = u.server_id
    WHERE
        UPPER(LTRIM(RTRIM(u.codigo))) = UPPER(%s)
        OR CONVERT(varchar(36), u.id) = %s
)
SELECT
    c.unidad_negocio_pk,
    c.unidad_negocio_codigo,
    c.unidad_negocio_nombre,
    c.server_id,
    c.sucursal_origen_id,
    c.system_type,
    c.unidad_activo,
    c.servidor_activo,
    c.empresa_id,
    c.visible_en_operaciones,
    (
        SELECT COUNT_BIG(*)
        FROM dbo.Unidades_Negocio AS sibling
        WHERE sibling.server_id = c.server_id
          AND ISNULL(sibling.activo, 0) = 1
    ) AS active_units_on_server
FROM candidates AS c
WHERE (
    SELECT COUNT_BIG(*)
    FROM candidates
) = 1
"""


def get_unit_scope_metadata_readonly(
    *,
    unidad: str,
    connection_factory: Callable[[], Any],
) -> Dict[str, Any]:
    """
    Resuelve una unidad exclusivamente por PK o código canónico.

    No acepta server_id como selector y valida primero la identidad SQL.
    """
    normalized_selector = _normalize_text(unidad)

    if not normalized_selector:
        raise UnitCodeRequired(
            "Unidad canónica requerida"
        )

    if not callable(connection_factory):
        raise InvalidConnectionFactory(
            "Fábrica de conexiones requerida"
        )

    connection = connection_factory()

    if connection is None:
        raise InvalidConnectionFactory(
            "La fábrica no devolvió una conexión"
        )

    try:
        validate_readonly_identity(connection)

        cursor = connection.cursor()
        cursor.execute(
            UNIT_SCOPE_METADATA_SQL,
            (
                normalized_selector,
                normalized_selector,
            ),
        )

        row = _row_to_dict(
            cursor,
            cursor.fetchone(),
        )

        if not row:
            raise UnitServerMappingNotFound(
                "Unidad canónica inexistente o ambigua"
            )

        if not _normalize_text(row.get("server_id")):
            raise UnitServerMappingNotFound(
                "Unidad sin servidor canónico"
            )

        if not bool(row.get("unidad_activo")):
            raise UnitServerMappingNotFound(
                "Unidad de negocio inactiva"
            )

        if not bool(row.get("servidor_activo")):
            raise UnitServerMappingNotFound(
                "Servidor asociado inactivo"
            )

        try:
            active_units_on_server = int(
                row.get("active_units_on_server")
            )
        except (TypeError, ValueError) as exc:
            raise UnitServerMappingNotFound(
                "Topología de servidor inválida"
            ) from exc

        if active_units_on_server < 1:
            raise UnitServerMappingNotFound(
                "Topología de servidor inválida"
            )

        return {
            "unidad_negocio_pk": row.get(
                "unidad_negocio_pk"
            ),
            "unidad_negocio_codigo": row.get(
                "unidad_negocio_codigo"
            ),
            "unidad_negocio_nombre": row.get(
                "unidad_negocio_nombre"
            ),
            "server_id": row.get("server_id"),
            "sucursal_origen_id": row.get(
                "sucursal_origen_id"
            ),
            "system_type": row.get("system_type"),
            "unidad_activo": bool(
                row.get("unidad_activo")
            ),
            "servidor_activo": bool(
                row.get("servidor_activo")
            ),
            "active_units_on_server": (
                active_units_on_server
            ),
            "empresa_id": row.get("empresa_id"),
            "visible_en_operaciones": bool(
                row.get("visible_en_operaciones")
            ),
            "config_origin": (
                "EDARSAHUB_SQL_HRLECTURA"
            ),
            "secrets_exposed": False,
        }
    finally:
        connection.close()
