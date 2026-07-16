"""Resolvedor canónico interno de conexiones POS para jobs controlados.

Resuelve ``Unidades_Negocio.server_id -> Servidores_Conexiones.id`` desde
EDARSAHUB SQL. Los secretos se descifran solo en memoria y este módulo nunca
se expone al frontend.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

from core.db import parse_sql_server_host
from core.secret_manager import decrypt_secret
from core.sql_first.connection_factory import get_edarsahub_pymssql_connection
from core.system_type_utils import normalize_system_type


class PosRuntimeResolverError(RuntimeError):
    """Error base del resolvedor POS interno."""


class PosRuntimeMappingError(PosRuntimeResolverError):
    """La relación canónica unidad-servidor es inválida o incompleta."""


@dataclass(frozen=True)
class PosRuntimeContext:
    unidad_negocio_pk: str
    unidad_codigo: str
    unidad_nombre: str
    empresa_id: Optional[str]
    server_id: str
    sucursal_origen_id: Optional[str]
    sucursal_legacy_id: int
    system_type: str
    host: str
    port: int
    instance: Optional[str]
    database: str
    username: str
    password: str

    def external_connection_config(self, *, as_dict: bool) -> dict:
        if self.database.strip().upper() == "EDARSAHUB":
            raise PosRuntimeMappingError(
                "EDARSAHUB no puede utilizarse como base origen POS"
            )
        server = f"{self.host}\\{self.instance}" if self.instance else self.host
        return {
            "host": server,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "password": self.password,
            "login_timeout": 30,
            "timeout": 30,
            "as_dict": as_dict,
        }


def _normalize_types(values: Optional[Iterable[str]]) -> set[str]:
    normalized = {normalize_system_type(value) for value in values or ()}
    normalized.discard("UNKNOWN")
    return normalized


def _row_to_context(row: dict) -> PosRuntimeContext:
    unit_id = str(row.get("unidad_negocio_pk") or "").strip()
    unit_code = str(row.get("unidad_codigo") or "").strip().upper()
    unit_name = str(row.get("unidad_nombre") or "").strip()
    server_id = str(row.get("server_id") or "").strip()
    system_type = normalize_system_type(row.get("system_type"))
    database = str(row.get("database_name") or "").strip()
    username = str(row.get("username") or "").strip()
    encrypted_password = row.get("password_encrypted")
    host_raw = str(row.get("host") or "").strip()
    default_port = int(row.get("port") or 1433)

    missing = [
        name
        for name, value in (
            ("unidad_negocio_pk", unit_id),
            ("unidad_codigo", unit_code),
            ("unidad_nombre", unit_name),
            ("server_id", server_id),
            ("system_type", None if system_type == "UNKNOWN" else system_type),
            ("host", host_raw),
            ("database_name", database),
            ("username", username),
            ("password_encrypted", encrypted_password),
        )
        if value is None or str(value).strip() == ""
    ]
    if missing:
        raise PosRuntimeMappingError(
            f"Configuración POS incompleta para unidad {unit_code or unit_name}: "
            + ", ".join(missing)
        )
    if database.upper() == "EDARSAHUB":
        raise PosRuntimeMappingError(
            f"La unidad {unit_code} apunta a EDARSAHUB como origen POS"
        )

    hostname, parsed_port, instance = parse_sql_server_host(host_raw, default_port)
    password = decrypt_secret(encrypted_password)
    if not password:
        raise PosRuntimeMappingError(
            f"No se pudo resolver el secreto POS de la unidad {unit_code}"
        )

    return PosRuntimeContext(
        unidad_negocio_pk=unit_id,
        unidad_codigo=unit_code,
        unidad_nombre=unit_name,
        empresa_id=(str(row["empresa_id"]).strip() if row.get("empresa_id") is not None else None),
        server_id=server_id,
        sucursal_origen_id=(str(row["sucursal_origen_id"]).strip() if row.get("sucursal_origen_id") is not None else None),
        sucursal_legacy_id=int(row.get("sucursal_legacy_id") or 0),
        system_type=system_type,
        host=hostname,
        port=int(parsed_port),
        instance=instance,
        database=database,
        username=username,
        password=password,
    )


def list_pos_runtime_contexts(
    *, system_types: Optional[Iterable[str]] = None
) -> list[PosRuntimeContext]:
    """Lista fuentes POS activas desde el catálogo canónico SQL."""
    requested = _normalize_types(system_types)
    connection = get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)
    try:
        cursor = connection.cursor(as_dict=True)
        cursor.execute(
            """
            SELECT
                u.id AS unidad_negocio_pk,
                u.codigo AS unidad_codigo,
                u.nombre AS unidad_nombre,
                u.server_id,
                u.sucursal_origen_id,
                COALESCE(TRY_CONVERT(INT, u.sucursal_origen_id), 0)
                    AS sucursal_legacy_id,
                s.empresa_id,
                s.host,
                s.port,
                s.database_name,
                s.username,
                s.password_encrypted,
                s.system_type
            FROM dbo.Unidades_Negocio AS u
            INNER JOIN dbo.Servidores_Conexiones AS s ON u.server_id = s.id
            WHERE u.activo = 1 AND s.activo = 1
            ORDER BY u.orden, u.codigo
            """
        )
        contexts = [_row_to_context(row) for row in cursor.fetchall()]
    finally:
        connection.close()

    if requested:
        contexts = [item for item in contexts if item.system_type in requested]
    return contexts


def resolve_pos_runtime_context(
    unidad_identifier: str,
    *,
    expected_system_types: Optional[Sequence[str]] = None,
) -> PosRuntimeContext:
    """Resuelve una unidad activa por código canónico o nombre exacto."""
    identifier = str(unidad_identifier or "").strip()
    if not identifier:
        raise PosRuntimeMappingError("Identificador de unidad requerido")
    expected = _normalize_types(expected_system_types)
    matches = [
        context
        for context in list_pos_runtime_contexts(system_types=expected or None)
        if context.unidad_codigo.upper() == identifier.upper()
        or context.unidad_nombre.upper() == identifier.upper()
    ]
    if len(matches) != 1:
        raise PosRuntimeMappingError(
            f"La unidad '{identifier}' no tiene una relación POS canónica única"
        )
    return matches[0]


__all__ = [
    "PosRuntimeContext",
    "PosRuntimeMappingError",
    "PosRuntimeResolverError",
    "list_pos_runtime_contexts",
    "resolve_pos_runtime_context",
]
