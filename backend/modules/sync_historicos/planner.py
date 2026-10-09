"""Planner canónico para Sincronización Histórica de Tablas.

Fase 3 del contrato atómico:
- no ejecuta sincronizaciones;
- no toca POS;
- no conoce proveedores por hardcode;
- recibe metadata ya resuelta desde fuentes canónicas;
- produce job padre + unidades atómicas deterministas.

La ejecución real pertenece al WORKER UNIVERSAL V1.2.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence
from uuid import UUID, uuid4


class HistoricalPlanError(ValueError):
    """Error de preflight/planning que debe fallar cerrado."""


@dataclass(frozen=True)
class HistoricalBlock:
    start: date
    end: date
    ordinal: int


@dataclass(frozen=True)
class AtomicHistoricalUnit:
    atomic_key: str
    system_id: int
    system_code: str
    unit_id: str
    unit_code: str
    connection_id: str
    system_version_id: Optional[str]
    branch_id: Optional[int]
    branch_origin_id: Optional[str]
    company_id: Optional[int]
    category_key: str
    entity_key: str
    capability_key: str
    handler: str
    date_field: str
    business_key: Sequence[str]
    block_start: date
    block_end: date
    block_ordinal: int
    execution_order: int
    max_attempts: int
    supports_resume: bool
    supports_safe_stop: bool
    metadata: Mapping[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["block_start"] = self.block_start.isoformat()
        value["block_end"] = self.block_end.isoformat()
        return value


@dataclass(frozen=True)
class HistoricalPlan:
    correlation_id: str
    start: date
    end: date
    atomic_units: Sequence[AtomicHistoricalUnit]
    selected_systems: Sequence[str]
    selected_units: Sequence[str]
    selected_capabilities: Sequence[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "correlation_id": self.correlation_id,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "selected_systems": list(self.selected_systems),
            "selected_units": list(self.selected_units),
            "selected_capabilities": list(self.selected_capabilities),
            "total_atomic_units": len(self.atomic_units),
            "atomic_units": [item.to_dict() for item in self.atomic_units],
        }


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _uuid(value: Any, field: str) -> str:
    raw = _clean(value)
    try:
        return str(UUID(raw))
    except (ValueError, TypeError, AttributeError) as exc:
        raise HistoricalPlanError(f"{field}_INVALID") from exc


def _positive_int(value: Any, field: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise HistoricalPlanError(f"{field}_INVALID") from exc
    if parsed < 1:
        raise HistoricalPlanError(f"{field}_INVALID")
    return parsed


def _month_end(value: date) -> date:
    if value.month == 12:
        return date(value.year, 12, 31)
    return date(value.year, value.month + 1, 1) - timedelta(days=1)


def partition_range(start: date, end: date, metadata: Mapping[str, Any]) -> List[HistoricalBlock]:
    """Parte un rango usando estrategia declarada en metadata.

    No existe fallback implícito. Si el capability no declara estrategia,
    el planner falla cerrado para evitar una política hardcodeada.
    """
    if end < start:
        raise HistoricalPlanError("DATE_RANGE_INVALID")

    strategy = _clean(metadata.get("chunk_unit")).lower()
    if strategy not in {"day", "week", "month", "days"}:
        raise HistoricalPlanError("CHUNK_STRATEGY_MISSING_OR_UNSUPPORTED")

    blocks: List[HistoricalBlock] = []
    cursor = start
    ordinal = 1

    if strategy == "days":
        span = _positive_int(metadata.get("chunk_days"), "CHUNK_DAYS")
    else:
        span = 0

    while cursor <= end:
        if strategy == "day":
            block_end = cursor
        elif strategy == "week":
            block_end = min(cursor + timedelta(days=6), end)
        elif strategy == "month":
            block_end = min(_month_end(cursor), end)
        else:
            block_end = min(cursor + timedelta(days=span - 1), end)

        blocks.append(HistoricalBlock(cursor, block_end, ordinal))
        ordinal += 1
        cursor = block_end + timedelta(days=1)

    return blocks


def _registry_by_system(
    registry: Iterable[Mapping[str, Any]],
) -> Dict[tuple[str, str], Mapping[str, Any]]:
    result: Dict[tuple[str, str], Mapping[str, Any]] = {}
    for item in registry:
        if not item.get("eligible_for_historical"):
            continue
        system_code = _clean(item.get("system_code")).upper()
        capability = _clean(item.get("capability_key"))
        if not system_code or not capability:
            continue
        result[(system_code, capability)] = item
    return result


def _expand_dependencies(
    system_code: str,
    selected: Sequence[str],
    registry_map: Mapping[tuple[str, str], Mapping[str, Any]],
) -> List[Mapping[str, Any]]:
    resolved: Dict[str, Mapping[str, Any]] = {}
    visiting: set[str] = set()

    def visit(capability_key: str) -> None:
        if capability_key in resolved:
            return
        if capability_key in visiting:
            raise HistoricalPlanError(
                f"DEPENDENCY_CYCLE:{system_code}:{capability_key}"
            )

        item = registry_map.get((system_code, capability_key))
        if not item:
            raise HistoricalPlanError(
                f"CAPABILITY_NOT_ELIGIBLE:{system_code}:{capability_key}"
            )

        visiting.add(capability_key)
        for dependency in item.get("dependencias") or []:
            dep_code = _clean(
                dependency.get("codigo")
                if isinstance(dependency, Mapping)
                else dependency
            )
            if not dep_code:
                continue
            visit(dep_code)
        visiting.remove(capability_key)
        resolved[capability_key] = item

    for capability_key in selected:
        visit(capability_key)

    return sorted(
        resolved.values(),
        key=lambda item: (
            int(item.get("execution_order") or item.get("orden") or 100),
            _clean(item.get("capability_key")),
        ),
    )


def _atomic_key(
    *,
    system_code: str,
    unit_id: str,
    connection_id: str,
    capability_key: str,
    start: date,
    end: date,
    version: Any,
) -> str:
    canonical = "|".join(
        [
            system_code.upper(),
            unit_id.lower(),
            connection_id.lower(),
            capability_key,
            start.isoformat(),
            end.isoformat(),
            _clean(version),
        ]
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"historical:{digest}"


def _normalize_requested(values: Sequence[str], field: str) -> List[str]:
    result: List[str] = []
    for raw in values:
        value = _clean(raw)
        if not value:
            continue
        if value not in result:
            result.append(value)
    if not result:
        raise HistoricalPlanError(f"{field}_REQUIRED")
    return result


def build_historical_plan(
    *,
    start: date,
    end: date,
    selected_systems: Sequence[str],
    selected_units: Sequence[str],
    selected_capabilities: Sequence[str],
    registry: Sequence[Mapping[str, Any]],
    unit_contexts: Sequence[Mapping[str, Any]],
    correlation_id: Optional[str] = None,
) -> HistoricalPlan:
    """Construye un plan transversal sin ejecutar trabajo real."""
    systems = [x.upper() for x in _normalize_requested(selected_systems, "SYSTEM")]
    units = _normalize_requested(selected_units, "UNIT")
    capabilities = _normalize_requested(selected_capabilities, "CAPABILITY")
    if end < start:
        raise HistoricalPlanError("DATE_RANGE_INVALID")

    corr = str(UUID(correlation_id)) if correlation_id else str(uuid4())
    registry_map = _registry_by_system(registry)

    contexts: Dict[str, Mapping[str, Any]] = {}
    for ctx in unit_contexts:
        unit_code = _clean(ctx.get("unit_code") or ctx.get("codigo"))
        if unit_code:
            contexts[unit_code.upper()] = ctx

    atomic: List[AtomicHistoricalUnit] = []

    for unit_code in units:
        context = contexts.get(unit_code.upper())
        if not context:
            raise HistoricalPlanError(f"UNIT_NOT_RESOLVED:{unit_code}")

        system_code = _clean(
            context.get("system_code") or context.get("codigo_sistema")
        ).upper()
        if system_code not in systems:
            raise HistoricalPlanError(
                f"UNIT_SYSTEM_NOT_SELECTED:{unit_code}:{system_code}"
            )

        unit_id = _uuid(
            context.get("unit_id") or context.get("unidad_negocio_id"),
            "UNIT_ID",
        )
        connection_id = _uuid(
            context.get("connection_id") or context.get("conexion_id"),
            "CONNECTION_ID",
        )
        system_id = _positive_int(
            context.get("system_id") or context.get("sistema_tipo_id"),
            "SYSTEM_ID",
        )

        expanded = _expand_dependencies(system_code, capabilities, registry_map)
        for capability in expanded:
            category_key = _clean(capability.get("category_key"))
            entity_key = _clean(capability.get("entity_key"))
            capability_key = _clean(capability.get("capability_key"))
            handler = _clean(capability.get("handler"))
            date_field = _clean(capability.get("date_field"))
            business_key = tuple(capability.get("business_key") or ())
            metadata = dict(capability.get("metadata") or {})

            if not all(
                [category_key, entity_key, capability_key, handler, date_field]
            ):
                raise HistoricalPlanError(
                    f"CAPABILITY_METADATA_INCOMPLETE:{system_code}:{capability_key}"
                )
            if not business_key:
                raise HistoricalPlanError(
                    f"BUSINESS_KEY_MISSING:{system_code}:{capability_key}"
                )

            blocks = partition_range(start, end, metadata)
            max_attempts = _positive_int(
                metadata.get("max_attempts"),
                "MAX_ATTEMPTS",
            )

            for block in blocks:
                atomic.append(
                    AtomicHistoricalUnit(
                        atomic_key=_atomic_key(
                            system_code=system_code,
                            unit_id=unit_id,
                            connection_id=connection_id,
                            capability_key=capability_key,
                            start=block.start,
                            end=block.end,
                            version=capability.get("version"),
                        ),
                        system_id=system_id,
                        system_code=system_code,
                        unit_id=unit_id,
                        unit_code=unit_code.upper(),
                        connection_id=connection_id,
                        system_version_id=(
                            _uuid(context.get("system_version_id"), "SYSTEM_VERSION_ID")
                            if context.get("system_version_id")
                            else None
                        ),
                        branch_id=(
                            int(context["branch_id"])
                            if context.get("branch_id") is not None
                            else None
                        ),
                        branch_origin_id=(
                            _clean(context.get("branch_origin_id")) or None
                        ),
                        company_id=(
                            int(context["company_id"])
                            if context.get("company_id") is not None
                            else None
                        ),
                        category_key=category_key,
                        entity_key=entity_key,
                        capability_key=capability_key,
                        handler=handler,
                        date_field=date_field,
                        business_key=business_key,
                        block_start=block.start,
                        block_end=block.end,
                        block_ordinal=block.ordinal,
                        execution_order=int(
                            capability.get("execution_order")
                            or capability.get("orden")
                            or 100
                        ),
                        max_attempts=max_attempts,
                        supports_resume=bool(capability.get("supports_resume")),
                        supports_safe_stop=bool(
                            capability.get("supports_safe_stop")
                        ),
                        metadata=metadata,
                    )
                )

    atomic.sort(
        key=lambda item: (
            item.execution_order,
            item.system_code,
            item.unit_code,
            item.capability_key,
            item.block_start,
            item.block_ordinal,
        )
    )

    if not atomic:
        raise HistoricalPlanError("PLAN_EMPTY")

    keys = [item.atomic_key for item in atomic]
    if len(keys) != len(set(keys)):
        raise HistoricalPlanError("PLAN_DUPLICATE_ATOMIC_KEY")

    return HistoricalPlan(
        correlation_id=corr,
        start=start,
        end=end,
        atomic_units=tuple(atomic),
        selected_systems=tuple(systems),
        selected_units=tuple(unit.upper() for unit in units),
        selected_capabilities=tuple(capabilities),
    )


def plan_json(plan: HistoricalPlan) -> str:
    return json.dumps(
        plan.to_dict(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
