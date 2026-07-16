"""Job incremental canónico de Cortes Z hacia EDARSAHUB SQL."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict

from core.connections.pos_runtime_resolver import list_pos_runtime_contexts
from modules.finanzas.cortes_z_runtime_sync import sync_cortes_z_context

logger = logging.getLogger(__name__)
SYNC_INCREMENTAL_DAYS = int(os.environ.get("SYNC_INGRESOS_DAYS", "2"))


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

    contexts = list_pos_runtime_contexts(
        system_types=("SOFTRESTAURANT", "MANAGEMENTPRO")
    )
    if not contexts:
        raise RuntimeError(
            "No existen unidades POS activas con relación canónica unidad-servidor"
        )

    for context in contexts:
        result["unidades_procesadas"] += 1
        unit_result = sync_cortes_z_context(
            context,
            dias_atras=SYNC_INCREMENTAL_DAYS,
            tipo_ejecucion="SCHEDULER",
        )
        stats = unit_result.get("stats") or {}
        detail = {
            "unidad": context.unidad_nombre,
            "unidad_codigo": context.unidad_codigo,
            "sistema": context.system_type,
            "estatus": unit_result.get("estatus", "ERROR"),
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
        else:
            result["unidades_fallidas"] += 1

        result["total_insertados"] += detail["insertados"]
        result["total_actualizados"] += detail["actualizados"]
        result["total_omitidos"] += detail["omitidos"]
        result["total_errores"] += detail["errores"]

        if detail["error"]:
            result["errores"].append(
                f"{context.unidad_codigo}: {detail['error']}"
            )

    finished = datetime.now()
    result["fecha_fin"] = finished.isoformat()
    result["duracion_ms"] = int((finished - started).total_seconds() * 1000)
    result["estatus_general"] = (
        "COMPLETADO"
        if result["unidades_fallidas"] == 0
        else "PARCIAL"
        if result["unidades_exitosas"] > 0
        else "FALLIDO"
    )
    return result


__all__ = ["execute_sync_ingresos_incremental"]
