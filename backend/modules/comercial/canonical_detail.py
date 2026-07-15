"""Canonical SQL-first helpers for Comercial daily KPI drill-down.

This module is intentionally connection-agnostic. It does not open database
connections, access MongoDB, call POS systems, or contain unit-specific
mappings. Callers must supply the existing EDARSAHUB query executor.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Mapping, Sequence


CANONICAL_RUNTIME_VIEW = "dbo.vw_Comercial_KPIs_Diarios_v2_Runtime"
CANONICAL_UNITS_TABLE = "dbo.Unidades_Negocio"
_GENERIC_SELECTORS = frozenset({"", "all", "default", "todas", "todos"})


class CanonicalUnitResolutionError(RuntimeError):
    """Raised when a requested server/sucursal cannot resolve to one unit."""


@dataclass(frozen=True)
class CanonicalUnit:
    """Canonical commercial identity from dbo.Unidades_Negocio."""

    codigo: str
    nombre: str
    server_id: str
    sucursal_origen_id: str | None
    system_type: str | None


@dataclass(frozen=True)
class SqlQuery:
    """Parameterized SQL statement and positional parameters."""

    statement: str
    params: tuple[Any, ...]


QueryExecutor = Callable[[str, Sequence[Any]], Sequence[Mapping[str, Any]]]


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _is_generic_selector(value: str) -> bool:
    return value.casefold() in _GENERIC_SELECTORS


def build_canonical_unit_query(server_id: str, sucursal: str = "") -> SqlQuery:
    """Build a parameterized lookup against dbo.Unidades_Negocio.

    A specific selector may match either the canonical unit code or the
    canonical source-branch identifier. Generic selectors deliberately do not
    guess; cardinality is enforced by ``resolve_canonical_unit``.
    """

    server_value = _clean(server_id)
    selector = _clean(sucursal)

    if not server_value:
        raise ValueError("server_id is required")

    statement = f"""
        SELECT
            CAST(id AS NVARCHAR(100)) AS unidad_negocio_pk,
            codigo,
            nombre,
            CAST(server_id AS NVARCHAR(100)) AS server_id,
            CAST(sucursal_origen_id AS NVARCHAR(100)) AS sucursal_origen_id,
            system_type
        FROM {CANONICAL_UNITS_TABLE}
        WHERE Activo = 1
          AND CAST(server_id AS NVARCHAR(100)) = %s
    """
    params: tuple[Any, ...] = (server_value,)

    if selector and not _is_generic_selector(selector):
        statement += """
          AND (
                CAST(sucursal_origen_id AS NVARCHAR(100)) = %s
             OR codigo = %s
          )
        """
        params += (selector, selector)

    statement += " ORDER BY codigo"
    return SqlQuery(statement=statement, params=params)


def resolve_canonical_unit(
    execute_query: QueryExecutor,
    server_id: str,
    sucursal: str = "",
) -> CanonicalUnit:
    """Resolve exactly one active canonical unit, failing closed otherwise."""

    query = build_canonical_unit_query(server_id, sucursal)
    rows = list(execute_query(query.statement, query.params) or [])

    if len(rows) != 1:
        selector = _clean(sucursal) or "<generic>"
        raise CanonicalUnitResolutionError(
            "Expected exactly one active canonical unit for "
            f"server_id={_clean(server_id)!r}, selector={selector!r}; "
            f"found {len(rows)}"
        )

    row = rows[0]
    codigo = _clean(row.get("codigo"))
    nombre = _clean(row.get("nombre"))
    resolved_server_id = _clean(row.get("server_id"))

    if not codigo or not nombre or not resolved_server_id:
        raise CanonicalUnitResolutionError(
            "Canonical unit row is missing codigo, nombre, or server_id"
        )

    sucursal_origen_id = _clean(row.get("sucursal_origen_id")) or None
    system_type = _clean(row.get("system_type")) or None

    return CanonicalUnit(
        codigo=codigo,
        nombre=nombre,
        server_id=resolved_server_id,
        sucursal_origen_id=sucursal_origen_id,
        system_type=system_type,
    )


def build_daily_kpi_total_query(
    unit_code: str,
    date_from: date | str,
    date_to: date | str,
) -> SqlQuery:
    """Build the canonical aggregate query for one unit and date range."""

    code = _clean(unit_code)
    if not code:
        raise ValueError("unit_code is required")

    return SqlQuery(
        statement=f"""
            SELECT
                ISNULL(SUM(ventas_total), 0) AS venta_total,
                ISNULL(SUM(tickets_total), 0) AS cheques_total,
                ISNULL(SUM(pax_total), 0) AS pax_total,
                COUNT_BIG(*) AS total
            FROM {CANONICAL_RUNTIME_VIEW}
            WHERE unidad_negocio_id = %s
              AND fecha_operacion >= %s
              AND fecha_operacion <= %s
              AND ventas_total > 0
        """,
        params=(code, date_from, date_to),
    )


def build_daily_kpi_detail_query(
    unit_code: str,
    date_from: date | str,
    date_to: date | str,
    *,
    offset: int,
    limit: int,
) -> SqlQuery:
    """Build the canonical paginated daily-detail query for one unit."""

    code = _clean(unit_code)
    if not code:
        raise ValueError("unit_code is required")
    if offset < 0:
        raise ValueError("offset must be non-negative")
    if limit < 1 or limit > 200:
        raise ValueError("limit must be between 1 and 200")

    return SqlQuery(
        statement=f"""
            SELECT
                fecha_operacion,
                unidad_negocio_id,
                unidad_negocio_pk,
                unidad_negocio_nombre,
                sistema_origen,
                ventas_total,
                tickets_total,
                pax_total,
                ticket_promedio
            FROM {CANONICAL_RUNTIME_VIEW}
            WHERE unidad_negocio_id = %s
              AND fecha_operacion >= %s
              AND fecha_operacion <= %s
              AND ventas_total > 0
            ORDER BY fecha_operacion DESC, unidad_negocio_id ASC
            OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
        """,
        params=(code, date_from, date_to, offset, limit),
    )


def build_daily_folio(unit_code: str, operation_date: date | str) -> str:
    """Return a stable unique folio for one canonical unit/day."""

    code = _clean(unit_code)
    day = operation_date.isoformat() if isinstance(operation_date, date) else _clean(operation_date)[:10]

    if not code or not day:
        raise ValueError("unit_code and operation_date are required")

    return f"DIA-{day}-{code}"
