"""GitHub-hosted external owner for EDARSAHUB commercial jobs.

This adapter does not implement business synchronization logic. It reuses the
certified Preview wake primitives:
- the same distributed owner lock;
- the same administrative pause for closed sales;
- the same SchedulerManager.run_job_now() call.

It is intended for an external runtime such as GitHub Actions so execution does
not depend on PREVIEW_WEB being alive.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Any, Dict

from core.mongo_stub import get_stub_database
from modules.scheduler_runtime import preview_closed_sales_wake
from modules.scheduler_runtime import preview_sales_wake


TARGET_OPEN = "open_sales"
TARGET_CLOSED = "closed_sales"


def _safe_environment() -> str:
    value = str(
        os.environ.get("EDARSA_ENV")
        or os.environ.get("ENVIRONMENT")
        or ""
    ).strip().upper()
    if "PROD" in value:
        raise RuntimeError("GITHUB_COMMERCIAL_OWNER_PRODUCTION_FORBIDDEN")
    return value or "UNKNOWN"


async def _execute_target(target: str) -> Dict[str, Any]:
    _safe_environment()

    if target == TARGET_OPEN:
        wake = preview_sales_wake
    elif target == TARGET_CLOSED:
        wake = preview_closed_sales_wake
    else:
        raise ValueError(f"Unsupported target: {target}")

    if (
        target == TARGET_CLOSED
        and preview_closed_sales_wake._administratively_paused()
    ):
        return {
            "status": "administratively_paused",
            "job_id": wake.JOB_ID,
            "execution_observed": False,
            "owner_lock_id": wake.OWNER_LOCK_ID,
            "executor": "github_actions",
            "production_touched": False,
        }

    owner_lock = await wake._try_acquire_owner_lock()
    if owner_lock is None:
        return {
            "status": "owner_active",
            "job_id": wake.JOB_ID,
            "execution_observed": False,
            "owner_lock_id": wake.OWNER_LOCK_ID,
            "executor": "github_actions",
            "production_touched": False,
        }

    try:
        result = await wake._run_once(get_stub_database())
        payload = dict(result or {})
        payload.setdefault("status", "executed")
        payload.setdefault("job_id", wake.JOB_ID)
        payload["execution_observed"] = payload.get("status") == "executed"
        payload["owner_lock_id"] = wake.OWNER_LOCK_ID
        payload["executor"] = "github_actions"
        payload["production_touched"] = False
        return payload
    finally:
        await owner_lock.release()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "target",
        choices=(TARGET_OPEN, TARGET_CLOSED),
    )
    parser.add_argument(
        "--require-executed",
        action="store_true",
        help="Fail unless SchedulerManager reports status=executed.",
    )
    args = parser.parse_args()

    try:
        payload = asyncio.run(_execute_target(args.target))
    except Exception as exc:
        payload = {
            "status": "error",
            "target": args.target,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "executor": "github_actions",
            "production_touched": False,
        }
        print(json.dumps(payload, ensure_ascii=False, default=str))
        return 1

    print(json.dumps(payload, ensure_ascii=False, default=str))

    if args.require_executed and payload.get("status") != "executed":
        return 2

    return 0 if payload.get("status") in {
        "executed",
        "owner_active",
        "administratively_paused",
    } else 1


if __name__ == "__main__":
    sys.exit(main())
