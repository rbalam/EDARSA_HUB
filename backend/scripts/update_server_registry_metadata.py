#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from core.server_registry import _get_server_by_id_from_sql, update_server

UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
DB_RE = re.compile(r"^[A-Za-z0-9_]{1,128}$")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-id", required=True)
    parser.add_argument("--database-name", required=True)
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()

    server_id = args.server_id.strip()
    database_name = args.database_name.strip()
    if not UUID_RE.fullmatch(server_id):
        print(json.dumps({"status": "FAIL", "error": "SERVER_ID_INVALID"}))
        return 2
    if not DB_RE.fullmatch(database_name):
        print(json.dumps({"status": "FAIL", "error": "DATABASE_NAME_INVALID"}))
        return 2
    if not args.confirm:
        print(json.dumps({"status": "FAIL", "error": "CONFIRMATION_REQUIRED"}))
        return 2

    before = _get_server_by_id_from_sql(server_id, include_inactive=True)
    if not before:
        print(json.dumps({"status": "FAIL", "error": "SERVER_NOT_FOUND"}))
        return 3

    before_active = bool(before.get("activo"))
    before_database = before.get("database_name")
    result = asyncio.run(update_server(server_id, {"database_name": database_name}))
    if not result.get("success"):
        print(json.dumps({"status": "FAIL", "error": str(result.get("sync_status") or "UPDATE_FAILED")}))
        return 4

    after = _get_server_by_id_from_sql(server_id, include_inactive=True)
    if not after:
        print(json.dumps({"status": "FAIL", "error": "POST_UPDATE_SERVER_NOT_FOUND"}))
        return 5
    if str(after.get("database_name") or "") != database_name:
        print(json.dumps({"status": "FAIL", "error": "POST_UPDATE_DATABASE_MISMATCH"}))
        return 6
    if bool(after.get("activo")) != before_active:
        print(json.dumps({"status": "FAIL", "error": "ACTIVE_STATE_CHANGED"}))
        return 7

    print(json.dumps({
        "status": "PASS",
        "server_id": server_id,
        "database_name_before": before_database,
        "database_name_after": after.get("database_name"),
        "active_preserved": True,
        "sync_status": result.get("sync_status"),
        "secrets_exposed": False
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
