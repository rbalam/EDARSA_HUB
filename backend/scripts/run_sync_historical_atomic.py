#!/usr/bin/env python3
"""Entrypoint cerrado del Worker Universal para una unidad historica atomica."""
from __future__ import annotations

import argparse
import json
import sys

from modules.sync_historicos.atomic_executor import execute_atomic_unit_sync


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sync-control-id", type=int, required=True)
    args = parser.parse_args()

    if args.sync_control_id < 1:
        raise SystemExit("SYNC_CONTROL_ID_INVALID")

    result = execute_atomic_unit_sync(args.sync_control_id)
    print(
        json.dumps(
            {
                "event": "sync_historical_atomic_summary",
                **result,
            },
            ensure_ascii=False,
            default=str,
        ),
        flush=True,
    )
    return 0 if result.get("success") else 2


if __name__ == "__main__":
    sys.exit(main())
