from __future__ import annotations

from collections.abc import Iterable

from .priority_contracts import (
    ExecutivePriorityAggregate,
    ExecutivePriorityItem,
    PriorityBand,
)


_BAND_ORDER = {
    PriorityBand.CRITICA: 0,
    PriorityBand.ALTA: 1,
    PriorityBand.MEDIA: 2,
    PriorityBand.BAJA: 3,
    PriorityBand.SIN_PRIORIDAD: 4,
}


def _sort_key(item: ExecutivePriorityItem) -> tuple[int, int, str, str, str]:
    due_missing = 1 if not item.due_at else 0
    due_at = item.due_at or ""
    return (
        _BAND_ORDER[item.priority_band],
        due_missing,
        due_at,
        item.source_domain,
        item.source_object_ref,
    )


def aggregate_priorities(
    items: Iterable[ExecutivePriorityItem | None],
) -> ExecutivePriorityAggregate:
    accepted = tuple(item for item in items if item is not None)
    deduplicated: dict[tuple[str, str], ExecutivePriorityItem] = {}

    for item in accepted:
        key = (item.source_domain, item.source_object_ref)
        current = deduplicated.get(key)
        if current is None or _sort_key(item) < _sort_key(current):
            deduplicated[key] = item

    ordered = tuple(sorted(deduplicated.values(), key=_sort_key))
    domains = tuple(sorted({item.source_domain for item in ordered}))

    return ExecutivePriorityAggregate(
        items=ordered,
        total=len(ordered),
        domains=domains,
        stale=any(item.stale for item in ordered),
    )
