"""Refresca exclusivamente Sync_Productos_Insumos para servidores SoftRestaurant.

Owner auxiliar de Development. No sincroniza familias, productos de venta,
recetas ni elaborados. Production esta prohibido.
"""

from __future__ import annotations

import json
import os
import sys

from core.server_registry import _get_servers_from_sql
from modules.sync_recetas.sync_recetas import ejecutar_sync_recetas_real


def _assert_development() -> None:
    env = str(
        os.environ.get("EDARSA_ENV")
        or os.environ.get("ENVIRONMENT")
        or ""
    ).strip().upper()
    if "PROD" in env:
        raise RuntimeError("SOFT_INSUMOS_OWNER_PRODUCTION_FORBIDDEN")


def main() -> int:
    _assert_development()

    servers = _get_servers_from_sql(filter_active=True)
    soft_ids = [
        str(s.get("id"))
        for s in servers
        if (
            s.get("id")
            and (
                "SOFT" in str(s.get("system_type") or "").upper()
                or str(s.get("system_type") or "").upper() == "SR"
            )
        )
    ]

    if not soft_ids:
        print(json.dumps({
            "status": "ERROR",
            "reason": "NO_ACTIVE_SOFT_SERVERS",
        }))
        return 1

    result = ejecutar_sync_recetas_real(
        server_ids=soft_ids,
        sync_familias=False,
        sync_productos=False,
        sync_insumos=True,
        sync_recetas=False,
        sync_elaborados=False,
    )

    payload = {
        "status": "SUCCESS" if result.success else "ERROR",
        "sync_run_id": result.sync_run_id,
        "servers": len(soft_ids),
        "server_ids": soft_ids,
        "total_insumos": result.total_insumos,
        "registros_insertados": result.registros_insertados,
        "registros_actualizados": result.registros_actualizados,
        "registros_error": result.registros_error,
        "servidores_exitosos": result.servidores_exitosos,
        "servidores_con_error": result.servidores_con_error,
        "errores": result.errores[:20],
        "warnings": result.warnings[:20],
        "production_touched": False,
    }
    print(json.dumps(payload, ensure_ascii=False, default=str))
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
