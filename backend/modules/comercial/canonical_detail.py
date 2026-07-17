"""Canonical SQL-first helpers for Comercial daily KPI drill-down.

This module is connection-agnostic. It does not open database connections,
access MongoDB, call POS systems, or contain unit-specific mappings. Callers
must supply the existing EDARSAHUB parameterized query executor.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Iterable, Mapping, Sequence


CANONICAL_RUNTIME_VIEW = "dbo.vw_Comercial_KPIs_Diarios_v2_Runtime"
CANONICAL_UNITS_TABLE = "dbo.Unidades_Negocio"
_GENERIC_SELECTORS = frozenset({"", "all", "default", "todas", "todos"})


class CanonicalUnitResolutionError(RuntimeError):
    """Raised when a server/sucursal cannot resolve to exactly one unit."""


class CanonicalDailyDuplicateError(RuntimeError):
    """Raised when Runtime contains multiple rows for one unit/date."""


class CanonicalUnitAccessError(RuntimeError):
    """Raised when the resolved unit is outside the user's canonical scope."""


@dataclass(frozen=True)
class CanonicalUnit:
    """Canonical commercial identity from dbo.Unidades_Negocio."""

    unidad_negocio_pk: str
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

    A specific selector may match the canonical code or source branch ID.
    Generic selectors never guess: cardinality is enforced by the resolver.
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
        WHERE activo = 1
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
    unidad_negocio_pk = _clean(row.get("unidad_negocio_pk"))
    codigo = _clean(row.get("codigo"))
    nombre = _clean(row.get("nombre"))
    resolved_server_id = _clean(row.get("server_id"))

    if not unidad_negocio_pk or not codigo or not nombre or not resolved_server_id:
        raise CanonicalUnitResolutionError(
            "Canonical unit row is missing id, codigo, nombre, or server_id"
        )

    return CanonicalUnit(
        unidad_negocio_pk=unidad_negocio_pk,
        codigo=codigo,
        nombre=nombre,
        server_id=resolved_server_id,
        sucursal_origen_id=_clean(row.get("sucursal_origen_id")) or None,
        system_type=_clean(row.get("system_type")) or None,
    )


def resolve_allowed_canonical_unit_pks(
    assigned_units: Sequence[Mapping[str, Any]],
    canonical_units: Sequence[Mapping[str, Any]],
) -> frozenset[str]:
    """Translate assigned legacy unit codes to canonical business-unit PKs."""

    canonical_by_code: dict[str, set[str]] = {}
    canonical_pks: set[str] = set()
    for row in canonical_units:
        code = _clean(row.get("codigo")).casefold()
        canonical_pk = _clean(row.get("unidad_negocio_pk")).casefold()
        if not code or not canonical_pk:
            continue
        canonical_by_code.setdefault(code, set()).add(canonical_pk)
        canonical_pks.add(canonical_pk)

    allowed_pks: set[str] = set()
    for row in assigned_units:
        explicit_pk = _clean(row.get("unidad_negocio_pk"))
        if explicit_pk.casefold() in canonical_pks:
            allowed_pks.add(explicit_pk.casefold())

        code = _clean(row.get("codigo")).casefold()
        code_matches = canonical_by_code.get(code, set())
        if len(code_matches) == 1:
            allowed_pks.update(code_matches)

    return frozenset(allowed_pks)


def assert_canonical_unit_access(
    unit: CanonicalUnit,
    allowed_unit_pks: Iterable[str],
    *,
    allowed_source_branch_ids: Iterable[str] = (),
    has_global_access: bool = False,
) -> None:
    """Fail closed unless the exact canonical PK or source branch is in scope."""

    if has_global_access:
        return

    allowed_pks = {
        _clean(value).casefold()
        for value in allowed_unit_pks
        if _clean(value)
    }
    if unit.unidad_negocio_pk.casefold() in allowed_pks:
        return

    allowed_branches = {
        _clean(value).casefold()
        for value in allowed_source_branch_ids
        if _clean(value)
    }
    resolved_branch = _clean(unit.sucursal_origen_id).casefold()
    if resolved_branch and resolved_branch in allowed_branches:
        return

    raise CanonicalUnitAccessError(
        "Resolved canonical unit is outside the effective user scope"
    )


def build_daily_kpi_total_query(
    unit_code: str,
    date_from: date | str,
    date_to: date | str,
) -> SqlQuery:
    """Build canonical totals for one unit and operation-date range."""

    code = _clean(unit_code)
    if not code:
        raise ValueError("unit_code is required")

    return SqlQuery(
        statement=f"""
            SELECT
                ISNULL(SUM(ventas_total), 0) AS venta_total,
                ISNULL(SUM(tickets_total), 0) AS cheques_total,
                ISNULL(SUM(pax_total), 0) AS pax_total,
                COUNT_BIG(*) AS total,
                COUNT_BIG(DISTINCT fecha_operacion) AS dias_distintos
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
    """Build canonical paginated daily detail for one unit."""

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


def assert_one_row_per_operation_date(summary: Mapping[str, Any]) -> None:
    """Fail closed when one canonical unit contains duplicated daily rows."""

    total = int(summary.get("total") or 0)
    distinct_days = int(summary.get("dias_distintos") or 0)
    if total != distinct_days:
        raise CanonicalDailyDuplicateError(
            "Canonical Runtime violates unit/date uniqueness: "
            f"rows={total}, distinct_days={distinct_days}"
        )


def build_daily_folio(unit_code: str, operation_date: date | str) -> str:
    """Return a stable unique folio for one canonical unit/day."""

    code = _clean(unit_code)
    day = (
        operation_date.isoformat()
        if isinstance(operation_date, date)
        else _clean(operation_date)[:10]
    )

    if not code or not day:
        raise ValueError("unit_code and operation_date are required")

    return f"DIA-{day}-{code}"
