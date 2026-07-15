"""Pure helpers for composing the Comercial router without duplicate routes."""

from __future__ import annotations

from typing import Any, Iterable, List


CANONICAL_DETAIL_PATH = "/comercial/detalle-movimientos/{server_id}"


def is_detail_get_route(route: Any) -> bool:
    """Return True for the legacy GET route replaced by the canonical handler."""

    methods = getattr(route, "methods", set()) or set()
    return (
        getattr(route, "path", None) == CANONICAL_DETAIL_PATH
        and "GET" in methods
    )


def without_legacy_detail_route(routes: Iterable[Any]) -> List[Any]:
    """Return legacy routes excluding the duplicated daily-detail GET route."""

    return [route for route in routes if not is_detail_get_route(route)]
