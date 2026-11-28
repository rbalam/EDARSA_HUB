#!/usr/bin/env python3
"""Entrypoint cerrado del Worker Universal para un job padre historico."""
from __future__ import annotations

import argparse
import json
import sys

from modules.sync_historicos.parent_executor import execute_parent_job


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-sync-control-id", type=int, required=True)
    args = parser.parse_args()

    if args.parent_sync_control_id < 1:
        raise SystemExit("PARENT_SYNC_CONTROL_ID_INVALID")

    result = execute_parent_job(args.parent_sync_control_id)
    print(
        json.dumps(
            {"event": "sync_historical_parent_summary", **result},
            ensure_ascii=False,
            default=str,
        ),
        flush=True,
    )
    return 0 if result.get("success") else 2


if __name__ == "__main__":
    sys.exit(main())
