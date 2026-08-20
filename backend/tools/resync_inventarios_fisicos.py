#!/usr/bin/env python3
"""
Resync manual de inventarios fisicos hacia EDARSAHUB.

Uso seguro:
  python backend/tools/resync_inventarios_fisicos.py --units ESTELAR --execute
  python backend/tools/resync_inventarios_fisicos.py --all --execute

Por default no escribe datos. Requiere --execute para actualizar
Compras_Inventarios_Fisicos_Sync y registrar Compras_Sync_Log.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from core.guards.server_secret_guard import require_server_secret_key
from core.secret_manager import is_encryption_available
from modules.compras.sync_service import (
    INVENTORY_SYNC_MODE_FULL,
    log_sync_operation,
    sync_inventarios_fisicos_from_server,
)


REPORT_DIR = Path("docs/reports/inventarios")


def _load_sync_compras_job_module():
    """Carga solo el archivo del job de compras, sin importar todo el scheduler."""
    module_path = Path(__file__).resolve().parents[1] / "core" / "scheduler" / "jobs" / "sync_compras_job.py"
    spec = importlib.util.spec_from_file_location("sync_compras_job_for_resync", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _normalize_unit(value: str) -> str:
    return str(value or "").strip().upper()


def _select_servers(servers: List[Dict[str, Any]], units: List[str], include_all: bool) -> List[Dict[str, Any]]:
    if include_all:
        return servers

    wanted = {_normalize_unit(unit) for unit in units}
    return [
        server
        for server in servers
        if _normalize_unit(server.get("unidad_codigo")) in wanted
    ]


def _write_report(payload: Dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"{timestamp}_resync_inventarios_fisicos.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Resync manual de inventarios fisicos")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--units", nargs="+", help="Codigos de unidad: ESTELAR CIENFUEGOS 130MID 130QRO ORIGEN")
    target.add_argument("--all", action="store_true", help="Ejecutar para todas las unidades canonicas mapeadas")
    parser.add_argument("--execute", action="store_true", help="Escribe cambios en SQL. Sin esto solo lista objetivos.")
    args = parser.parse_args()

    try:
        require_server_secret_key()
    except Exception as exc:
        payload = {
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "mode": "execute" if args.execute else "dry_run",
            "status": "SERVER_SECRET_KEY_MISSING",
            "error": str(exc),
        }
        report_path = _write_report(payload)
        print("SERVER_SECRET_KEY_MISSING")
        print(str(exc))
        print(f"Reporte: {report_path}")
        return 2

    sync_job = _load_sync_compras_job_module()
    servers = sync_job._get_servers_to_sync()
    selected = _select_servers(servers, args.units or [], args.all)

    payload: Dict[str, Any] = {
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "execute" if args.execute else "dry_run",
        "server_secret_key_available": is_encryption_available(),
        "targets": [
            {
                "unidad": server.get("unidad_codigo"),
                "server": server.get("name"),
                "server_id": server.get("id"),
                "system_type": server.get("system_type"),
                "has_password": bool(server.get("password")),
            }
            for server in selected
        ],
        "results": [],
    }

    if not selected:
        payload["status"] = "NO_TARGETS"
        report_path = _write_report(payload)
        print("NO_TARGETS")
        print(f"Reporte: {report_path}")
        return 2

    if not args.execute:
        payload["status"] = "DRY_RUN"
        report_path = _write_report(payload)
        print("DRY_RUN")
        print(f"Targets: {len(selected)}")
        for target_info in payload["targets"]:
            print(f"- {target_info['unidad']} | {target_info['server']} | {target_info['system_type']} | password={target_info['has_password']}")
        print(f"Reporte: {report_path}")
        return 0

    for server in selected:
        sync_start = datetime.now()
        server_info = {
            "id": server["id"],
            "host": server["host"],
            "port": server["port"],
            "database": server["database"],
            "username": server["username"],
            "password": server["password"],
            "system_type": server["system_type"],
        }
        unidad_info = {
            "id": server["unidad_id"],
            "codigo": server["unidad_codigo"],
            "nombre": server["unidad_nombre"],
            "sucursal_origen_id": server.get("sucursal_origen_id"),
        }

        result = sync_inventarios_fisicos_from_server(
            server_info,
            unidad_info,
            sync_job._execute_sql_with_timeout,
            sync_mode=INVENTORY_SYNC_MODE_FULL,
        )
        sync_end = datetime.now()
        log_sync_operation(
            unidad_negocio_id=unidad_info["id"],
            server_id=server_info["id"],
            sync_type="INVENTARIOS",
            sync_start=sync_start,
            sync_end=sync_end,
            records_synced=int(result.get("records_synced") or 0),
            status=result.get("status", "ERROR"),
            error_message=result.get("error"),
        )
        payload["results"].append({
            "unidad": unidad_info["codigo"],
            "server": server.get("name"),
            "server_id": server_info["id"],
            "system_type": server_info["system_type"],
            "status": result.get("status"),
            "records_synced": result.get("records_synced", 0),
            "details_synced": result.get("details_synced", 0),
            "details_updated": result.get("details_updated", 0),
            "detail_errors": result.get("detail_errors", 0),
            "error": result.get("error"),
        })

    errors = [row for row in payload["results"] if row.get("status") != "OK"]
    payload["status"] = "ERROR" if errors else "OK"
    payload["finished_at"] = datetime.now().isoformat(timespec="seconds")
    report_path = _write_report(payload)

    print(payload["status"])
    for row in payload["results"]:
        print(
            f"- {row['unidad']} | {row['server']} | {row['status']} | "
            f"headers={row['records_synced']} | detalles_insertados={row['details_synced']} | "
            f"detalles_actualizados={row['details_updated']} | errores_detalle={row['detail_errors']} | "
            f"error={row['error'] or ''}"
        )
    print(f"Reporte: {report_path}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
