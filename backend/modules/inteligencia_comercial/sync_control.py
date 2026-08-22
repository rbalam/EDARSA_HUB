"""Control web de conciliación y reparación del detalle de Inteligencia Comercial.

No modifica el rango del scheduler. La validación compara KPI Runtime vs detalle
por fecha; la reparación reutiliza el backfill canónico y solo escribe días que
pasan OK_HEADER_CANONICO contra el POS.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException
from pydantic import BaseModel

from .routes import execute_query, normalizar_unidad, require_admin, router, _unidad_codigo_filtro


class SyncPendientesRequest(BaseModel):
    fecha_inicio: date
    fecha_fin: date
    unidad: Optional[str] = None


def _unidad_scope(unidad: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    if not unidad or str(unidad).strip().lower() == "todas":
        return None, None
    unidad_db = normalizar_unidad(unidad)
    if not unidad_db:
        raise HTTPException(status_code=400, detail="Unidad de negocio inválida o inactiva")
    return unidad_db, _unidad_codigo_filtro(unidad_db)


def _validar_rango(fi: date, ff: date) -> None:
    if ff < fi:
        raise HTTPException(status_code=400, detail="fecha_fin no puede ser menor que fecha_inicio")
    if (ff - fi).days > 62:
        raise HTTPException(status_code=400, detail="El rango máximo de verificación es 63 días")


def _conciliacion(fi: date, ff: date, unidad: Optional[str]) -> Dict[str, Any]:
    _validar_rango(fi, ff)
    unidad_db, unidad_codigo = _unidad_scope(unidad)

    params: List[Any] = [fi, ff, fi, ff]
    kpi_filter = ""
    det_filter = ""
    if unidad_codigo:
        kpi_filter = " AND k.unidad_negocio_id = %s"
        det_filter = " AND d.unidad_negocio_id = %s"
        params = [fi, ff, unidad_codigo, fi, ff, unidad_codigo]

    sql = f"""
    WITH KPI AS (
        SELECT
            k.unidad_negocio_id,
            k.unidad_negocio_nombre,
            k.fecha_operacion,
            SUM(ISNULL(k.ventas_total,0)) AS venta_kpi,
            SUM(ISNULL(k.tickets_total,0)) AS tickets_kpi,
            SUM(ISNULL(k.pax_total,0)) AS pax_kpi
        FROM dbo.Comercial_Inteligencia_VW_KPIsEjecutivos k
        WHERE k.fecha_operacion BETWEEN %s AND %s
          {kpi_filter}
        GROUP BY k.unidad_negocio_id, k.unidad_negocio_nombre, k.fecha_operacion
    ),
    DET AS (
        SELECT
            d.unidad_negocio_id,
            d.unidad_negocio_nombre,
            d.fecha_operacion,
            SUM(ISNULL(d.importe_neto,0)) AS venta_detalle,
            COUNT(DISTINCT d.numero_ticket) AS tickets_detalle,
            COUNT(*) AS lineas_detalle
        FROM dbo.Comercial_Inteligencia_VentasDetalleProducto d
        WHERE d.fecha_operacion BETWEEN %s AND %s
          AND ISNULL(d.activo,1) = 1
          {det_filter}
        GROUP BY d.unidad_negocio_id, d.unidad_negocio_nombre, d.fecha_operacion
    )
    SELECT
        k.unidad_negocio_id AS unidad_codigo,
        k.unidad_negocio_nombre AS sucursal,
        k.fecha_operacion,
        k.venta_kpi,
        ISNULL(d.venta_detalle,0) AS venta_detalle,
        k.venta_kpi - ISNULL(d.venta_detalle,0) AS delta_venta,
        k.tickets_kpi,
        ISNULL(d.tickets_detalle,0) AS tickets_detalle,
        k.tickets_kpi - ISNULL(d.tickets_detalle,0) AS delta_tickets,
        k.pax_kpi,
        ISNULL(d.lineas_detalle,0) AS lineas_detalle,
        CASE
            WHEN d.fecha_operacion IS NULL AND ISNULL(k.venta_kpi,0) > 0
                THEN 'PENDIENTE_SIN_DETALLE'
            WHEN ABS(k.venta_kpi - ISNULL(d.venta_detalle,0)) <= 0.05
                 AND k.tickets_kpi = ISNULL(d.tickets_detalle,0)
                THEN 'SINCRONIZADO'
            ELSE 'NO_CUADRA_REVISAR'
        END AS estado
    FROM KPI k
    LEFT JOIN DET d
      ON d.unidad_negocio_id = k.unidad_negocio_id
     AND d.fecha_operacion = k.fecha_operacion
    ORDER BY k.unidad_negocio_nombre, k.fecha_operacion
    """

    rows = execute_query(sql, tuple(params))
    detalle = []
    resumen: Dict[str, Dict[str, Any]] = {}
    pendientes = 0

    for row in rows:
        estado = str(row.get("estado") or "NO_CUADRA_REVISAR")
        suc = str(row.get("sucursal") or row.get("unidad_codigo") or "")
        item = resumen.setdefault(
            suc,
            {"sucursal": suc, "dias": 0, "sincronizados": 0, "pendientes": 0, "no_cuadra": 0},
        )
        item["dias"] += 1
        if estado == "SINCRONIZADO":
            item["sincronizados"] += 1
        elif estado == "PENDIENTE_SIN_DETALLE":
            item["pendientes"] += 1
            pendientes += 1
        else:
            item["no_cuadra"] += 1
            pendientes += 1

        detalle.append({
            "unidad_codigo": row.get("unidad_codigo"),
            "sucursal": suc,
            "fecha": str(row.get("fecha_operacion"))[:10],
            "estado": estado,
            "venta_kpi": round(float(row.get("venta_kpi") or 0), 2),
            "venta_detalle": round(float(row.get("venta_detalle") or 0), 2),
            "delta_venta": round(float(row.get("delta_venta") or 0), 2),
            "tickets_kpi": int(row.get("tickets_kpi") or 0),
            "tickets_detalle": int(row.get("tickets_detalle") or 0),
            "delta_tickets": int(row.get("delta_tickets") or 0),
            "pax_kpi": int(row.get("pax_kpi") or 0),
            "lineas_detalle": int(row.get("lineas_detalle") or 0),
        })

    return {
        "success": True,
        "unidad": unidad_db or "TODAS",
        "fecha_inicio": fi.isoformat(),
        "fecha_fin": ff.isoformat(),
        "estado_global": "SINCRONIZADO" if pendientes == 0 else "PENDIENTES",
        "filas_evaluadas": len(detalle),
        "problemas": pendientes,
        "resumen": list(resumen.values()),
        "detalle": detalle,
    }


@router.post("/sync/verificar")
async def verificar_sincronizacion(
    body: SyncPendientesRequest,
    _: Dict[str, Any] = Depends(require_admin),
):
    """Compara KPI Runtime contra detalle por unidad y fecha. Solo lectura."""
    return _conciliacion(body.fecha_inicio, body.fecha_fin, body.unidad)


@router.post("/sync/sincronizar-pendientes")
async def sincronizar_pendientes(
    body: SyncPendientesRequest,
    _: Dict[str, Any] = Depends(require_admin),
):
    """Repara únicamente fechas que concilian contra Runtime con el extractor canónico."""
    _validar_rango(body.fecha_inicio, body.fecha_fin)
    _, unidad_codigo = _unidad_scope(body.unidad)

    try:
        from scripts.backfill_detalle_producto_pendientes import ejecutar_backfill

        _, resultado = ejecutar_backfill(
            fecha_inicio=body.fecha_inicio,
            fecha_fin=body.fecha_fin + timedelta(days=1),
            unidades=[unidad_codigo] if unidad_codigo else None,
            commit=True,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo ejecutar el backfill canónico: {str(exc)[:300]}",
        ) from exc

    posterior = _conciliacion(body.fecha_inicio, body.fecha_fin, body.unidad)
    return {
        "success": posterior.get("estado_global") == "SINCRONIZADO",
        "resultado_backfill": resultado,
        "validacion_posterior": posterior,
    }
