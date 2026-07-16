"""Sincronización incremental de Cortes Z hacia EDARSAHUB SQL."""

import logging
import os
from datetime import datetime
from typing import Any, Dict

from modules.finanzas.cortes_z_source_connections import (
    sincronizar_unidad_mpro_canonica,
    sincronizar_unidad_softrestaurant_canonica,
)

logger = logging.getLogger(__name__)
SYNC_INCREMENTAL_DAYS = int(os.environ.get("SYNC_INGRESOS_DAYS", "2"))

UNIDADES = (
    ("130° MERIDA", "SoftRestaurant", sincronizar_unidad_softrestaurant_canonica),
    ("CIENFUEGOS", "SoftRestaurant", sincronizar_unidad_softrestaurant_canonica),
    ("LA ESTELAR", "SoftRestaurant", sincronizar_unidad_softrestaurant_canonica),
    ("130° QUERETARO", "MPRO", sincronizar_unidad_mpro_canonica),
    ("ORIGEN", "MPRO", sincronizar_unidad_mpro_canonica),
)


async def execute_sync_ingresos_incremental(db=None) -> Dict[str, Any]:
    started = datetime.now()
    result = {
        "job_name": "sync_ingresos_incremental",
        "tipo_sync": "INCREMENTAL",
        "dias_atras": SYNC_INCREMENTAL_DAYS,
        "fecha_inicio": started.isoformat(),
        "unidades_procesadas": 0,
        "unidades_exitosas": 0,
        "unidades_fallidas": 0,
        "total_insertados": 0,
        "total_actualizados": 0,
        "total_omitidos": 0,
        "total_errores": 0,
        "detalles_unidades": [],
        "errores": [],
    }

    for nombre, sistema, sincronizador in UNIDADES:
        result["unidades_procesadas"] += 1
        try:
            unit_result = sincronizador(
                unidad_nombre=nombre,
                dias_atras=SYNC_INCREMENTAL_DAYS,
            )
            stats = unit_result.get("stats") or {}
            detail = {
                "unidad": nombre,
                "sistema": sistema,
                "estatus": unit_result.get("estatus", "UNKNOWN"),
                "leidos": stats.get("leidos", 0),
                "insertados": stats.get("insertados", 0),
                "actualizados": stats.get("actualizados", 0),
                "omitidos": stats.get("omitidos", 0),
                "errores": stats.get("errores", 0),
                "error": unit_result.get("error"),
            }
            result["detalles_unidades"].append(detail)
            if detail["estatus"] == "COMPLETADO":
                result["unidades_exitosas"] += 1
                result["total_insertados"] += detail["insertados"]
                result["total_actualizados"] += detail["actualizados"]
                result["total_omitidos"] += detail["omitidos"]
            else:
                result["unidades_fallidas"] += 1
                result["total_errores"] += max(detail["errores"], 1)
                if detail["error"]:
                    result["errores"].append(f"{nombre}: {detail['error']}")
        except Exception as exc:
            error = str(exc)
            logger.error("[SYNC_INGRESOS] %s: %s", nombre, error)
            result["unidades_fallidas"] += 1
            result["total_errores"] += 1
            result["errores"].append(f"{nombre}: {error}")
            result["detalles_unidades"].append({
                "unidad": nombre,
                "sistema": sistema,
                "estatus": "ERROR",
                "error": error,
            })

    finished = datetime.now()
    result["fecha_fin"] = finished.isoformat()
    result["duracion_ms"] = int((finished - started).total_seconds() * 1000)
    result["estatus_general"] = (
        "COMPLETADO" if result["unidades_fallidas"] == 0
        else "PARCIAL" if result["unidades_exitosas"] > 0
        else "FALLIDO"
    )
    return result


__all__ = ["execute_sync_ingresos_incremental"]
