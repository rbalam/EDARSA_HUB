"""GitHub-hosted external owner for EDARSAHUB SoftRestaurant inventory sync.

Reuses the canonical sync_compras job. It does not implement business logic.
Production execution is explicitly forbidden.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any, Dict

from core.scheduler.jobs.sync_compras_job import run_sync_compras_job


def _assert_safe_environment() -> str:
    value = str(
        os.environ.get("EDARSA_ENV")
        or os.environ.get("ENVIRONMENT")
        or ""
    ).strip().upper()
    if "PROD" in value:
        raise RuntimeError("GITHUB_INVENTORY_OWNER_PRODUCTION_FORBIDDEN")
    return value or "UNKNOWN"


async def _run() -> Dict[str, Any]:
    environment = _assert_safe_environment()
    result = await run_sync_compras_job(dry_run=False)
    payload = dict(result or {})
    payload.setdefault("status", "ERROR")
    payload["executor"] = "github_actions"
    payload["environment"] = environment
    payload["production_touched"] = False
    payload["system_filter"] = str(
        os.environ.get("SYNC_COMPRAS_SYSTEM_FILTER") or ""
    )
    return payload


def main() -> int:
    try:
        payload = asyncio.run(_run())
    except Exception as exc:
        payload = {
            "status": "ERROR",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "executor": "github_actions",
            "production_touched": False,
        }
        print(json.dumps(payload, ensure_ascii=False, default=str))
        return 1

    print(json.dumps(payload, ensure_ascii=False, default=str))

    status = str(payload.get("status") or "").upper()
    if status in {"SUCCESS", "PARTIAL", "SKIPPED"}:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
