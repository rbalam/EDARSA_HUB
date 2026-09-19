from __future__ import annotations

import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PREVIEW_URL = os.environ.get(
    "EDARSAHUB_PREVIEW_URL",
    "https://erp-crm-enterprise-1.preview.emergentagent.com",
).rstrip("/")


def _get(path: str) -> tuple[int, str]:
    request = Request(
        PREVIEW_URL + path,
        headers={
            "User-Agent": "EDARSAHUB-R24F-UAT-PREVIEW-CONTROLLED",
            "Accept": "text/html,application/json,*/*",
        },
    )
    try:
        with urlopen(request, timeout=25) as response:
            body = response.read(500000).decode("utf-8", "replace")
            return int(response.status), body
    except HTTPError as exc:
        body = exc.read(500000).decode("utf-8", "replace")
        return int(exc.code), body
    except URLError as exc:  # pragma: no cover - surfaced as deterministic failure
        raise AssertionError(f"STAGE=PREVIEW_CONNECTIVITY;ERROR={exc}") from exc


def test_preview_spa_route_for_lotes_proveedor_is_served_without_business_calls():
    status, body = _get("/tablajeria/lotes-proveedor")
    assert status == 200, f"STAGE=PREVIEW_ROUTE;STATUS={status}"
    lower = body.lower()
    assert "root" in lower or "script" in lower, "STAGE=PREVIEW_ROUTE;SPA_MARKERS_MISSING"


def test_preview_api_health_is_reachable_without_sql_business_endpoints():
    status, body = _get("/api/health")
    assert status == 200, f"STAGE=PREVIEW_HEALTH;STATUS={status};BODY={body[:300]}"
    lower = body.lower()
    assert "status" in lower or "healthy" in lower or "ok" in lower, "STAGE=PREVIEW_HEALTH;BODY_UNEXPECTED"
