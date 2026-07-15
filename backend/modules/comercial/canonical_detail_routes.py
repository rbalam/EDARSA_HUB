"""Canonical override for Comercial daily movement drill-down.

The route is registered before the legacy Comercial router so FastAPI resolves
this handler for the existing public path. It reads only EDARSAHUB SQL through
the project's canonical configuration and parameterized executor.
"""

from __future__ import annotations

import calendar
import logging
from datetime import datetime, timedelta
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query

from core.config.edarsahub_config import get_edarsahub_sql_config
from core.db import execute_sql_query_params
from core.security import get_current_user
from core.user_access_context import has_server_access, resolve_user_access_context
from modules.comercial.canonical_detail import (
    CanonicalDailyDuplicateError,
    CanonicalUnitResolutionError,
    assert_one_row_per_operation_date,
    build_daily_folio,
    build_daily_kpi_detail_query,
    build_daily_kpi_total_query,
    resolve_canonical_unit,
)
from modules.comercial.repository import get_server_by_id


router = APIRouter(tags=["comercial"])


def _execute_edarsahub_parameterized(statement, params):
    cfg = get_edarsahub_sql_config()
    return execute_sql_query_params(
        cfg.host,
        cfg.port,
        cfg.database,
        cfg.user,
        cfg.password,
        statement,
        tuple(params),
    ) or []


def _resolve_period(meses: str, anios: str) -> tuple[str, str]:
    now = datetime.now()

    years = [int(value.strip()) for value in anios.split(",") if value.strip()]
    months = [int(value.strip()) for value in meses.split(",") if value.strip()]

    if not years:
        years = [now.year]
    if not months:
        months = [now.month]

    if any(month < 1 or month > 12 for month in months):
        raise HTTPException(status_code=422, detail="Mes fuera de rango")

    year = max(years)
    month_start = min(months)
    month_end = max(months)
    date_from = f"{year}-{month_start:02d}-01"

    if year == now.year and month_end == now.month:
        date_to = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        last_day = calendar.monthrange(year, month_end)[1]
        date_to = f"{year}-{month_end:02d}-{last_day:02d}"

    return date_from, date_to


async def _validate_server_scope(current_user: Dict, server_id: str) -> None:
    context = await resolve_user_access_context(current_user)
    if not has_server_access(context, server_id):
        raise HTTPException(status_code=403, detail="No tiene acceso a este servidor")


@router.get("/comercial/detalle-movimientos/{server_id}")
async def comercial_detalle_movimientos_canonical(
    server_id: str,
    sucursal: str = Query(default=""),
    tipo: str = Query(default="ventas"),
    periodo: str = Query(default="mes"),
    meses: str = Query(default=""),
    anios: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: Dict = Depends(get_current_user),
):
    """Return one canonical daily row per selected commercial unit.

    `tipo` and `periodo` remain accepted for API compatibility. Historical
    figures always come from vw_Comercial_KPIs_Diarios_v2_Runtime and are
    filtered by the resolved canonical `unidad_negocio_id`.
    """

    del tipo, periodo

    server = await get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")

    await _validate_server_scope(current_user, server_id)
    date_from, date_to = _resolve_period(meses, anios)
    offset = (page - 1) * limit

    try:
        unit = resolve_canonical_unit(
            _execute_edarsahub_parameterized,
            server_id,
            sucursal,
        )

        total_query = build_daily_kpi_total_query(
            unit.codigo,
            date_from,
            date_to,
        )
        total_rows = _execute_edarsahub_parameterized(
            total_query.statement,
            total_query.params,
        )
        summary = total_rows[0] if total_rows else {}
        assert_one_row_per_operation_date(summary)

        detail_query = build_daily_kpi_detail_query(
            unit.codigo,
            date_from,
            date_to,
            offset=offset,
            limit=limit,
        )
        rows = _execute_edarsahub_parameterized(
            detail_query.statement,
            detail_query.params,
        )

        movements = []
        for row in rows:
            operation_date = row.get("fecha_operacion")
            date_text = (
                operation_date.strftime("%Y-%m-%d")
                if hasattr(operation_date, "strftime")
                else str(operation_date)[:10]
            )
            movements.append(
                {
                    "folio": build_daily_folio(unit.codigo, date_text),
                    "fecha": date_text,
                    "importe": float(row.get("ventas_total") or 0),
                    "pax": int(row.get("pax_total") or 0),
                    "descuento": 0,
                    "propina": 0,
                    "tipo_servicio": row.get("sistema_origen") or "EDARSAHUB",
                    "num_productos": int(row.get("tickets_total") or 0),
                    "unidad_negocio_pk": unit.unidad_negocio_pk,
                    "unidad_negocio_codigo": unit.codigo,
                    "unidad_negocio_nombre": unit.nombre,
                }
            )

        total = int(summary.get("total") or 0)
        logging.info(
            "[DETALLE_CANONICO] server=%s unit=%s range=%s/%s rows=%s",
            server_id,
            unit.codigo,
            date_from,
            date_to,
            len(movements),
        )

        return {
            "source_status": "SUCCESS" if total else "NO_DATA",
            "source_message": "Detalle canónico desde EDARSAHUB SQL",
            "source": "EDARSAHUB_SQL_RUNTIME",
            "movimientos": movements,
            "items": movements,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if total else 0,
            "periodo": {"inicio": date_from, "fin": date_to},
            "servidor": server.get("name"),
            "unidad": {
                "unidad_negocio_pk": unit.unidad_negocio_pk,
                "codigo": unit.codigo,
                "nombre": unit.nombre,
                "server_id": unit.server_id,
                "sucursal_origen_id": unit.sucursal_origen_id,
                "system_type": unit.system_type,
            },
            "resumen": {
                "venta_total": float(summary.get("venta_total") or 0),
                "cheques_total": int(summary.get("cheques_total") or 0),
                "pax_total": int(summary.get("pax_total") or 0),
            },
        }
    except CanonicalUnitResolutionError as exc:
        logging.error("[DETALLE_CANONICO] Resolución de unidad fallida: %s", exc)
        raise HTTPException(
            status_code=409,
            detail={
                "code": "CANONICAL_UNIT_RESOLUTION_FAILED",
                "message": str(exc),
            },
        ) from exc
    except CanonicalDailyDuplicateError as exc:
        logging.error("[DETALLE_CANONICO] Duplicidad Runtime: %s", exc)
        raise HTTPException(
            status_code=409,
            detail={
                "code": "CANONICAL_UNIT_DATE_DUPLICATE",
                "message": str(exc),
            },
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logging.exception("[DETALLE_CANONICO] Error EDARSAHUB SQL")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "EDARSAHUB_CANONICAL_DETAIL_ERROR",
                "message": str(exc)[:180],
            },
        ) from exc
