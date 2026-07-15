from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "modules/comercial/router_filter.py"
)
MODULE_NAME = "edarsahub_comercial_router_filter_test"

spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load router_filter.py")

router_filter = importlib.util.module_from_spec(spec)
sys.modules[MODULE_NAME] = router_filter
spec.loader.exec_module(router_filter)


def route(path: str, methods: set[str]):
    return SimpleNamespace(path=path, methods=methods)


def test_filter_removes_only_legacy_detail_get_route():
    detail_get = route(
        "/comercial/detalle-movimientos/{server_id}",
        {"GET"},
    )
    detail_post = route(
        "/comercial/detalle-movimientos/{server_id}",
        {"POST"},
    )
    dashboard_get = route("/comercial/dashboard", {"GET"})

    filtered = router_filter.without_legacy_detail_route(
        [detail_get, detail_post, dashboard_get]
    )

    assert detail_get not in filtered
    assert detail_post in filtered
    assert dashboard_get in filtered


def test_detail_route_predicate_is_exact():
    assert router_filter.is_detail_get_route(
        route(
            "/comercial/detalle-movimientos/{server_id}",
            {"GET"},
        )
    )
    assert not router_filter.is_detail_get_route(
        route(
            "/comercial/detalle-movimientos/{server_id}/extra",
            {"GET"},
        )
    )
    assert not router_filter.is_detail_get_route(
        route(
            "/comercial/detalle-movimientos/{server_id}",
            {"POST"},
        )
    )
