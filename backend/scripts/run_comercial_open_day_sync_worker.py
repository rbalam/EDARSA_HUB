#!/usr/bin/env python3
"""Worker entrypoint fijo para forzar Ventas del Dia sin shell arbitrario."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date

from core.scheduler.jobs.sync_comercial_abiertas_v2_job import (
    run_sync_comercial_abiertas_v2_manual,
)


def _safe_detail(row):
    if not isinstance(row, dict):
        return {}
    return {
        "unidad_negocio_id": row.get("unidad_negocio_id"),
        "unidad": row.get("unidad"),
        "sistema": row.get("sistema"),
        "fuente": row.get("fuente"),
        "estatus": row.get("estatus"),
        "source_status": row.get("source_status"),
        "closed_sales_source": row.get("closed_sales_source"),
        "closed_sales_is_provisional": row.get(
            "closed_sales_is_provisional"
        ),
        "fecha_operacion": row.get("fecha_operacion"),
        "ventas_abiertas": row.get("ventas_abiertas"),
        "total_estimado_dia": row.get("total_estimado_dia"),
        "detalle_abiertas_filas": row.get(
            "detalle_abiertas_filas"
        ),
        "mensaje_error": str(
            row.get("mensaje_error") or ""
        )[:300],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fecha", required=True)
    args = parser.parse_args()

    fecha = date.fromisoformat(args.fecha)
    result = run_sync_comercial_abiertas_v2_manual(
        fecha=fecha
    )

    summary = {
        "event": "comercial_open_day_summary",
        "fecha_operacion": fecha.isoformat(),
        "unidades_procesadas": int(
            result.get("unidades_procesadas") or 0
        ),
        "unidades_exitosas": int(
            result.get("unidades_exitosas") or 0
        ),
        "unidades_fallidas": int(
            result.get("unidades_fallidas") or 0
        ),
        "total_ventas_abiertas": float(
            result.get("total_ventas_abiertas") or 0
        ),
        "total_estimado_dia": float(
            result.get("total_estimado_dia") or 0
        ),
        "duracion_segundos": float(
            result.get("duracion_segundos") or 0
        ),
        "detalles_unidades": [
            _safe_detail(row)
            for row in (
                result.get("detalles_unidades") or []
            )
        ],
        "errores": [
            str(value)[:300]
            for value in (result.get("errores") or [])
        ],
    }
    print(
        json.dumps(
            summary,
            ensure_ascii=False,
            default=str,
        )
    )

    ok = (
        summary["unidades_procesadas"] > 0
        and summary["unidades_fallidas"] == 0
        and summary["unidades_exitosas"]
        == summary["unidades_procesadas"]
    )
    return 0 if ok else 5


if __name__ == "__main__":
    sys.exit(main())
