"""
Reportes ISCAM - Portal de Inteligencia Comercial
==================================================
4 reportes de explotación de ventas, 100% sobre tablas CANÓNICAS de EDARSAHUB
(NO-LIVE, sin hardcode, sin duplicar):

  1. Ventas a 12 periodos        -> KPIsCanonicosService.acumulado_cerrado (misma base que Ejecutivo)
  2. Resumen de cuentas          -> dbo.Sync_Sales  (drill: cuenta -> productos)
  3. Comandas de venta           -> dbo.Sync_Sales.items (OPENJSON)
  4. Ventas por formas de pago   -> dbo.Finanzas_CortesCaja  (REUTILIZADA del módulo Finanzas)

El scoping por unidad de negocio para usuarios EXTERNOS lo aplica `intel_portal_guard`
(montado al incluir este router en server.py). `unidad` = CÓDIGO de unidad de negocio.
"""
import calendar
import logging
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Query, HTTPException

from core.kpis_canonicos import KPIsCanonicosService
from core.sql_first.db import get_sql_connection
from core.unidades_service import UnidadesService

logger = logging.getLogger(__name__)

iscam_router = APIRouter(prefix="/inteligencia/iscam", tags=["Reportes ISCAM"])

# Detalle de productos embebido como JSON en Sync_Sales.items
_OPENJSON_ITEMS = (
    "CROSS APPLY OPENJSON("
    "CASE WHEN ISJSON(s.items) = 1 THEN s.items ELSE N'[]' END"
    ") WITH ("
    "  prod_id NVARCHAR(60) '$.id',"
    "  prod_name NVARCHAR(250) '$.name',"
    "  cantidad DECIMAL(18,3) '$.quantity',"
    "  precio DECIMAL(18,4) '$.price',"
    "  importe DECIMAL(18,4) '$.total'"
    ") j"
)


def _q(sql: str, params: tuple = ()):
    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)
    cur.execute(sql, params)
    rows = list(cur.fetchall())
    cur.close()
    conn.close()
    return rows


def _nombre_unidad(codigo: str) -> Optional[str]:
    """Resuelve el NOMBRE de unidad (como aparece en Finanzas_CortesCaja) desde el código."""
    try:
        for u in UnidadesService.get_all():
            if u.get("codigo") == codigo or u.get("unidad_negocio_codigo") == codigo:
                return u.get("nombre") or u.get("unidad_negocio_nombre")
    except Exception as e:
        logger.error(f"[ISCAM] resolver nombre unidad: {e}")
    return None


def _f(v):
    return float(v) if v is not None else 0.0


def _iso(v):
    """ISO seguro: acepta datetime o string."""
    if v is None:
        return None
    return v.isoformat() if hasattr(v, "isoformat") else str(v)


def _period_sql(col: str, group_by: Optional[str]) -> str:
    """Expresión SQL FORMAT para agrupar por año / mes / día."""
    g = (group_by or "mes").lower()
    if g == "anio":
        return f"FORMAT({col},'yyyy')"
    if g == "dia":
        return f"FORMAT({col},'yyyy-MM-dd')"
    return f"FORMAT({col},'yyyy-MM')"  # mes (default)


def _shift_months(value: datetime, months: int) -> datetime:
    """Replica DATEADD(MONTH, ...) sin depender de SQL para el rango por defecto."""
    month_index = value.year * 12 + (value.month - 1) + months
    year, month_zero = divmod(month_index, 12)
    month = month_zero + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def _period_floor(value: datetime, group_by: str) -> datetime:
    if group_by == "anio":
        return value.replace(month=1, day=1)
    if group_by == "dia":
        return value
    return value.replace(day=1)


def _period_next(value: datetime, group_by: str) -> datetime:
    if group_by == "anio":
        return value.replace(year=value.year + 1, month=1, day=1)
    if group_by == "dia":
        return value + timedelta(days=1)
    return _shift_months(value, 1).replace(day=1)


def _period_label(value: datetime, group_by: str) -> str:
    if group_by == "anio":
        return value.strftime("%Y")
    if group_by == "dia":
        return value.strftime("%Y-%m-%d")
    return value.strftime("%Y-%m")


def _period_windows(desde: str, hasta_exclusivo: str, group_by: str):
    """Divide [desde, hasta) sin salir del rango solicitado."""
    start = datetime.strptime(desde, "%Y-%m-%d")
    end = datetime.strptime(hasta_exclusivo, "%Y-%m-%d")
    cursor = start
    windows = []
    while cursor < end:
        anchor = _period_floor(cursor, group_by)
        boundary = min(end, _period_next(anchor, group_by))
        windows.append((_period_label(anchor, group_by), cursor, boundary))
        cursor = boundary
    return windows


# ============================================================================
# 1) VENTAS POR PERIODOS (agrupable por Año / Mes)
# ============================================================================
@iscam_router.get("/ventas-periodos")
async def ventas_periodos(unidad: str = Query(...), desde: Optional[str] = None, hasta: Optional[str] = None,
                          group_by: str = Query("mes"), meses: int = Query(12, ge=1, le=36)):
    """Ventas cerradas con el MISMO contrato canónico del Dashboard Ejecutivo."""
    gb = group_by if group_by in ("anio", "mes", "dia") else "mes"
    unidad_pk = UnidadesService.resolver_pk(unidad)
    if not unidad_pk:
        raise HTTPException(status_code=404, detail=f"Unidad no encontrada: {unidad}")

    if desde or hasta:
        d, h = _rango_fechas(desde, hasta)
    else:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        d = _shift_months(today, -int(meses)).strftime("%Y-%m-%d")
        h = (today + timedelta(days=1)).strftime("%Y-%m-%d")

    data = []
    for periodo, inicio, fin in _period_windows(d, h, gb):
        desglose = KPIsCanonicosService.resumen_periodo_desglosado(
            inicio.strftime("%Y-%m-%d"),
            fin.strftime("%Y-%m-%d"),
            unidad_pks=[str(unidad_pk)],
        )
        acumulado = desglose.get("acumulado_cerrado") or {}
        metricas = acumulado.get("metricas") or {}
        venta = _f(metricas.get("ventas"))
        propinas = _f(metricas.get("propinas"))
        cheques = int(round(_f(metricas.get("cheques"))))
        clientes = int(round(_f(metricas.get("pax"))))

        if not any((venta, propinas, cheques, clientes)):
            continue

        data.append({
            "periodo": periodo,
            "venta_total": round(venta, 2),
            "propinas": round(propinas, 2),
            "cheques": cheques,
            "clientes": clientes,
            "cheque_promedio": round(_f(metricas.get("cheque_promedio")), 2),
            "consumo_promedio": round(
                _f(metricas.get("consumo_promedio_pax") or metricas.get("pax_promedio")),
                2,
            ),
        })

    data.reverse()
    return {
        "success": True,
        "source": "KPIsCanonicosService.resumen_periodo_desglosado.acumulado_cerrado",
        "contrato_acumulado": "CERRADO_SIN_DIA_OPERATIVO_ACTUAL",
        "unidad": unidad,
        "group_by": gb,
        "periodos": data,
    }


@iscam_router.get("/ventas-periodos/productos")
async def ventas_periodos_productos(unidad: str = Query(...), periodo: str = Query(...),
                                    group_by: str = Query("mes")):
    unidad_pk = UnidadesService.resolver_codigo(unidad)
    if not unidad_pk:
        raise HTTPException(status_code=404, detail=f"Unidad no encontrada: {unidad}")
    pexpr = _period_sql("fecha_operacion", group_by)
    rows = _q(
        f"""
        SELECT producto_codigo_fuente AS codigo, MAX(producto_nombre) AS producto,
               SUM(ISNULL(cantidad,0)) AS cantidad, SUM(ISNULL(importe_neto,0)) AS importe,
               COUNT(DISTINCT id_transaccion) AS tickets
        FROM dbo.Comercial_Inteligencia_VentasDetalleProducto
        WHERE unidad_negocio_id = %s AND ISNULL(activo,1)=1 AND ISNULL(es_kpi_valido,1)=1
          AND {pexpr} = %s
        GROUP BY producto_codigo_fuente
        ORDER BY importe DESC
        """,
        (str(unidad_pk), periodo),
    )
    return {"success": True, "source": "Comercial_Inteligencia_VentasDetalleProducto",
            "unidad": unidad, "periodo": periodo,
            "productos": [{"codigo": r["codigo"], "producto": r["producto"],
                           "cantidad": _f(r["cantidad"]), "importe": round(_f(r["importe"]), 2),
                           "tickets": int(r["tickets"] or 0)} for r in rows]}


@iscam_router.get("/ventas-periodos/tickets")
async def ventas_periodos_tickets(unidad: str = Query(...), periodo: str = Query(...),
                                  producto: str = Query(...), group_by: str = Query("mes")):
    unidad_pk = UnidadesService.resolver_codigo(unidad)
    if not unidad_pk:
        raise HTTPException(status_code=404, detail=f"Unidad no encontrada: {unidad}")
    pexpr = _period_sql("fecha_operacion", group_by)
    rows = _q(
        f"""
        WITH base AS (
            SELECT *
            FROM dbo.Comercial_Inteligencia_VentasDetalleProducto
            WHERE unidad_negocio_id = %s AND ISNULL(activo,1)=1 AND ISNULL(es_kpi_valido,1)=1
              AND {pexpr} = %s
        ),
        tickets AS (
            SELECT id_transaccion, numero_ticket, MIN(fecha_hora) AS fecha,
                   SUM(ISNULL(importe_neto,0)) AS importe_ticket, MAX(ISNULL(pax,0)) AS personas
            FROM base
            GROUP BY id_transaccion, numero_ticket
        ),
        producto_ticket AS (
            SELECT id_transaccion, numero_ticket, SUM(ISNULL(cantidad,0)) AS cantidad,
                   SUM(ISNULL(importe_neto,0)) AS importe_producto
            FROM base
            WHERE producto_codigo_fuente = %s
            GROUP BY id_transaccion, numero_ticket
        )
        SELECT t.numero_ticket AS folio, t.fecha, t.importe_ticket, t.personas,
               p.cantidad, p.importe_producto
        FROM tickets t
        INNER JOIN producto_ticket p ON p.id_transaccion=t.id_transaccion AND p.numero_ticket=t.numero_ticket
        ORDER BY t.fecha DESC
        """,
        (str(unidad_pk), periodo, producto),
    )
    return {"success": True, "source": "Comercial_Inteligencia_VentasDetalleProducto",
            "tickets": [{
        "folio": r["folio"], "fecha": r["fecha"].isoformat() if r["fecha"] else None,
        "importe_ticket": round(_f(r["importe_ticket"]), 2), "personas": int(r["personas"] or 0),
        "cantidad": _f(r["cantidad"]), "importe_producto": round(_f(r["importe_producto"]), 2)} for r in rows]}


# ============================================================================
# 2) RESUMEN DE CUENTAS
# ============================================================================
@iscam_router.get("/cuentas")
async def resumen_cuentas(unidad: str = Query(...), desde: Optional[str] = None, hasta: Optional[str] = None,
                          group_by: str = Query("none"), limit: int = Query(2000, ge=1, le=5000),
                          export_all: bool = Query(False)):
    d, h = _rango_fechas(desde, hasta)
    if group_by in ("anio", "mes", "dia"):
        unidad_pk = UnidadesService.resolver_pk(unidad)
        if not unidad_pk:
            raise HTTPException(status_code=404, detail=f"Unidad no encontrada: {unidad}")
        agrupado = []
        for periodo, inicio, fin in _period_windows(d, h, group_by):
            desglose = KPIsCanonicosService.resumen_periodo_desglosado(
                inicio.strftime("%Y-%m-%d"), fin.strftime("%Y-%m-%d"), unidad_pks=[str(unidad_pk)]
            )
            metricas = ((desglose.get("acumulado_cerrado") or {}).get("metricas") or {})
            imp = _f(metricas.get("ventas")); cu = int(round(_f(metricas.get("cheques")))); pax = int(round(_f(metricas.get("pax"))))
            if not any((imp, cu, pax)):
                continue
            agrupado.append({"periodo": periodo, "cuentas": cu, "importe": round(imp, 2), "personas": pax,
                             "cuenta_promedio": round(_f(metricas.get("cheque_promedio")), 2),
                             "consumo_promedio": round(_f(metricas.get("consumo_promedio_pax") or metricas.get("pax_promedio")), 2)})
        agrupado.reverse()
        return {"success": True, "source": "KPIsCanonicosService.resumen_periodo_desglosado.acumulado_cerrado",
                "contrato_acumulado": "CERRADO_SIN_DIA_OPERATIVO_ACTUAL", "unidad": unidad, "desde": d, "hasta": h,
                "group_by": group_by, "agrupado": agrupado}
    unidad_pk = UnidadesService.resolver_codigo(unidad)
    if not unidad_pk:
        raise HTTPException(status_code=404, detail=f"Unidad no encontrada: {unidad}")
    if export_all:
        rows = _q(
            """
            WITH tickets AS (SELECT id_transaccion AS cuenta_id, numero_ticket AS folio, MIN(fecha_hora) AS fecha,
                 SUM(ISNULL(importe_neto,0)) AS importe, MAX(ISNULL(pax,0)) AS personas
                 FROM dbo.Comercial_Inteligencia_VentasDetalleProducto
                 WHERE unidad_negocio_id=%s AND ISNULL(activo,1)=1 AND ISNULL(es_kpi_valido,1)=1
                   AND fecha_operacion >= %s AND fecha_operacion < %s
                 GROUP BY id_transaccion, numero_ticket)
            SELECT folio, fecha, importe, personas, 'COMPLETED' AS estado, cuenta_id FROM tickets ORDER BY fecha DESC
            """, (str(unidad_pk), d, h))
    else:
        rows = _q(
            """
            WITH tickets AS (SELECT id_transaccion AS cuenta_id, numero_ticket AS folio, MIN(fecha_hora) AS fecha,
                 SUM(ISNULL(importe_neto,0)) AS importe, MAX(ISNULL(pax,0)) AS personas
                 FROM dbo.Comercial_Inteligencia_VentasDetalleProducto
                 WHERE unidad_negocio_id=%s AND ISNULL(activo,1)=1 AND ISNULL(es_kpi_valido,1)=1
                   AND fecha_operacion >= %s AND fecha_operacion < %s
                 GROUP BY id_transaccion, numero_ticket)
            SELECT TOP (%s) folio, fecha, importe, personas, 'COMPLETED' AS estado, cuenta_id FROM tickets ORDER BY fecha DESC
            """, (str(unidad_pk), d, h, limit))
    return {"success": True, "source": "Comercial_Inteligencia_VentasDetalleProducto", "unidad": unidad, "desde": d, "hasta": h, "group_by": "none",
            "export_all": export_all, "limited": not export_all, "limit": None if export_all else limit,
            "cuentas": [{"folio": r["folio"], "fecha": r["fecha"].isoformat() if r["fecha"] else None,
                         "importe": round(_f(r["importe"]), 2), "personas": int(r["personas"] or 0),
                         "estado": r["estado"], "cuenta_id": r["cuenta_id"]} for r in rows]}


@iscam_router.get("/cuentas/detalle")
async def cuenta_detalle(unidad: str = Query(...), folio: str = Query(...)):
    unidad_pk = UnidadesService.resolver_codigo(unidad)
    if not unidad_pk:
        raise HTTPException(status_code=404, detail=f"Unidad no encontrada: {unidad}")
    rows = _q(
        f"""
        SELECT producto_codigo_fuente AS codigo, MAX(producto_nombre) AS producto, SUM(ISNULL(cantidad,0)) AS cantidad,
               CASE WHEN SUM(ISNULL(cantidad,0)) <> 0 THEN SUM(ISNULL(importe_neto,0))/SUM(ISNULL(cantidad,0)) ELSE MAX(ISNULL(precio_unitario,0)) END AS precio,
               SUM(ISNULL(importe_neto,0)) AS importe
        FROM dbo.Comercial_Inteligencia_VentasDetalleProducto
        WHERE unidad_negocio_id=%s AND numero_ticket=%s AND ISNULL(activo,1)=1 AND ISNULL(es_kpi_valido,1)=1
        GROUP BY producto_codigo_fuente
        ORDER BY importe DESC
        """,
        (str(unidad_pk), folio),
    )
    return {"success": True, "folio": folio,
            "productos": [{"codigo": r["codigo"], "producto": r["producto"], "cantidad": _f(r["cantidad"]),
                           "precio": round(_f(r["precio"]), 2), "importe": round(_f(r["importe"]), 2)} for r in rows]}


# ============================================================================
# 3) COMANDAS DE VENTA
# ============================================================================
@iscam_router.get("/comandas")
async def comandas_venta(unidad: str = Query(...), desde: Optional[str] = None, hasta: Optional[str] = None,
                         group_by: str = Query("none"), limit: int = Query(1000, ge=1, le=5000),
                         export_all: bool = Query(False)):
    d, h = _rango_fechas(desde, hasta)
    unidad_pk = UnidadesService.resolver_codigo(unidad)
    if not unidad_pk:
        raise HTTPException(status_code=404, detail=f"Unidad no encontrada: {unidad}")
    if group_by in ("anio", "mes", "dia"):
        pexpr = _period_sql("fecha_operacion", group_by)
        rows = _q(
            f"""
            SELECT {pexpr} AS periodo, COUNT(*) AS lineas, COUNT(DISTINCT id_transaccion) AS tickets,
                   SUM(ISNULL(cantidad,0)) AS cantidad, SUM(ISNULL(importe_neto,0)) AS importe
            FROM dbo.Comercial_Inteligencia_VentasDetalleProducto
            WHERE unidad_negocio_id=%s AND ISNULL(activo,1)=1 AND ISNULL(es_kpi_valido,1)=1
              AND fecha_operacion >= %s AND fecha_operacion < %s
            GROUP BY {pexpr}
            ORDER BY periodo DESC
            """, (str(unidad_pk), d, h))
        return {"success": True, "unidad": unidad, "desde": d, "hasta": h, "group_by": group_by,
                "agrupado": [{"periodo": r["periodo"], "lineas": int(r["lineas"] or 0),
                              "tickets": int(r["tickets"] or 0), "cantidad": _f(r["cantidad"]),
                              "importe": round(_f(r["importe"]), 2)} for r in rows]}
    if export_all:
        rows = _q(
            """
            SELECT numero_ticket AS folio_cuenta, fecha_hora AS fecha, producto_codigo_fuente AS clave,
                   producto_nombre AS descripcion, cantidad, precio_unitario AS precio, importe_neto AS importe
            FROM dbo.Comercial_Inteligencia_VentasDetalleProducto
            WHERE unidad_negocio_id=%s AND ISNULL(activo,1)=1 AND ISNULL(es_kpi_valido,1)=1
              AND fecha_operacion >= %s AND fecha_operacion < %s
            ORDER BY fecha_operacion DESC, fecha_hora DESC, numero_ticket DESC
            """, (str(unidad_pk), d, h))
    else:
        rows = _q(
            """
            SELECT TOP (%s) numero_ticket AS folio_cuenta, fecha_hora AS fecha, producto_codigo_fuente AS clave,
                   producto_nombre AS descripcion, cantidad, precio_unitario AS precio, importe_neto AS importe
            FROM dbo.Comercial_Inteligencia_VentasDetalleProducto
            WHERE unidad_negocio_id=%s AND ISNULL(activo,1)=1 AND ISNULL(es_kpi_valido,1)=1
              AND fecha_operacion >= %s AND fecha_operacion < %s
            ORDER BY fecha_operacion DESC, fecha_hora DESC, numero_ticket DESC
            """, (limit, str(unidad_pk), d, h))
    return {"success": True, "unidad": unidad, "desde": d, "hasta": h, "group_by": "none",
            "export_all": export_all, "limited": not export_all, "limit": None if export_all else limit,
            "comandas": [{"folio_cuenta": r["folio_cuenta"], "fecha": _iso(r["fecha"]),
                          "clave": r["clave"], "descripcion": r["descripcion"], "cantidad": _f(r["cantidad"]),
                          "precio": round(_f(r["precio"]), 2), "importe": round(_f(r["importe"]), 2)} for r in rows]}


# ============================================================================
# 4) VENTAS POR FORMAS DE PAGO  (REUTILIZA dbo.Finanzas_CortesCaja)
# ============================================================================
@iscam_router.get("/formas-pago")
async def ventas_formas_pago(unidad: str = Query(...), desde: Optional[str] = None, hasta: Optional[str] = None,
                             group_by: str = Query("none"), limit: int = Query(1000, ge=1, le=5000),
                             export_all: bool = Query(False)):
    nombre = _nombre_unidad(unidad)
    if not nombre:
        raise HTTPException(status_code=404, detail=f"No se pudo resolver la unidad '{unidad}'")
    d, h = _rango_fechas(desde, hasta)
    if group_by in ("anio", "mes", "dia"):
        pexpr = _period_sql("FechaApertura", group_by)
        rows = _q(
            f"""
            SELECT {pexpr} AS periodo,
                   SUM(ISNULL(TotalVenta,0)) AS total, SUM(ISNULL(TotalEfectivo,0)) AS efectivo,
                   SUM(ISNULL(TotalTarjetaDebito,0)+ISNULL(TotalTarjetaCredito,0)) AS tarjeta,
                   SUM(ISNULL(TotalAmex,0)) AS amex, SUM(ISNULL(TotalVales,0)) AS vales,
                   SUM(ISNULL(TotalOtros,0)) AS otros, SUM(ISNULL(Propinas,0)) AS propina,
                   SUM(ISNULL(ComisionDebito,0)+ISNULL(ComisionCredito,0)+ISNULL(ComisionAmex,0)+ISNULL(ComisionInternacional,0)) AS comision,
                   COUNT(*) AS cortes
            FROM dbo.Finanzas_CortesCaja
            WHERE UnidadNegocioNombre = %s AND ISNULL(Activo,1)=1
              AND FechaApertura >= %s AND FechaApertura < %s
            GROUP BY {pexpr}
            ORDER BY periodo DESC
            """,
            (nombre, d, h),
        )
        agrupado = [{"periodo": r["periodo"], "cortes": int(r["cortes"] or 0),
                     "total": round(_f(r["total"]), 2), "efectivo": round(_f(r["efectivo"]), 2),
                     "tarjeta": round(_f(r["tarjeta"]), 2), "amex": round(_f(r["amex"]), 2),
                     "vales": round(_f(r["vales"]), 2), "otros": round(_f(r["otros"]), 2),
                     "propina": round(_f(r["propina"]), 2), "comision": round(_f(r["comision"]), 2)} for r in rows]
        tot = {k: round(sum(a[k] for a in agrupado), 2) for k in
               ("total", "efectivo", "tarjeta", "amex", "vales", "otros", "propina", "comision")}
        return {"success": True, "source": "Finanzas_CortesCaja (canónica, compartida)", "unidad": unidad,
                "unidad_nombre": nombre, "desde": d, "hasta": h, "group_by": group_by,
                "totales": tot, "agrupado": agrupado}
    if export_all:
        rows = _q(
            """
            SELECT FolioCorte AS folio, FechaApertura AS fecha, TotalVenta AS total,
                   TotalEfectivo AS efectivo, TotalTarjetaDebito AS tarjeta_debito,
                   TotalTarjetaCredito AS tarjeta_credito, TotalAmex AS amex,
                   TotalInternacional AS internacional, TotalVales AS vales, TotalOtros AS otros,
                   Propinas AS propina,
                   (ISNULL(ComisionDebito,0)+ISNULL(ComisionCredito,0)+ISNULL(ComisionAmex,0)+ISNULL(ComisionInternacional,0)) AS comision,
                   CajaNombre AS caja
            FROM dbo.Finanzas_CortesCaja
            WHERE UnidadNegocioNombre = %s AND ISNULL(Activo,1)=1
              AND FechaApertura >= %s AND FechaApertura < %s
            ORDER BY FechaApertura DESC
            """,
            (nombre, d, h),
        )
    else:
        rows = _q(
            """
            SELECT TOP (%s) FolioCorte AS folio, FechaApertura AS fecha, TotalVenta AS total,
                   TotalEfectivo AS efectivo, TotalTarjetaDebito AS tarjeta_debito,
                   TotalTarjetaCredito AS tarjeta_credito, TotalAmex AS amex,
                   TotalInternacional AS internacional, TotalVales AS vales, TotalOtros AS otros,
                   Propinas AS propina,
                   (ISNULL(ComisionDebito,0)+ISNULL(ComisionCredito,0)+ISNULL(ComisionAmex,0)+ISNULL(ComisionInternacional,0)) AS comision,
                   CajaNombre AS caja
            FROM dbo.Finanzas_CortesCaja
            WHERE UnidadNegocioNombre = %s AND ISNULL(Activo,1)=1
              AND FechaApertura >= %s AND FechaApertura < %s
            ORDER BY FechaApertura DESC
            """,
            (limit, nombre, d, h),
        )
    cortes = []
    tot = {"total": 0, "efectivo": 0, "tarjeta": 0, "amex": 0, "vales": 0, "otros": 0, "propina": 0, "comision": 0}
    for r in rows:
        tarjeta = _f(r["tarjeta_debito"]) + _f(r["tarjeta_credito"])
        cortes.append({
            "folio": r["folio"], "fecha": _iso(r["fecha"]),
            "caja": r["caja"], "total": round(_f(r["total"]), 2), "efectivo": round(_f(r["efectivo"]), 2),
            "tarjeta_debito": round(_f(r["tarjeta_debito"]), 2), "tarjeta_credito": round(_f(r["tarjeta_credito"]), 2),
            "tarjeta": round(tarjeta, 2), "amex": round(_f(r["amex"]), 2),
            "internacional": round(_f(r["internacional"]), 2), "vales": round(_f(r["vales"]), 2),
            "otros": round(_f(r["otros"]), 2), "propina": round(_f(r["propina"]), 2),
            "comision": round(_f(r["comision"]), 2),
        })
        tot["total"] += _f(r["total"]); tot["efectivo"] += _f(r["efectivo"]); tot["tarjeta"] += tarjeta
        tot["amex"] += _f(r["amex"]); tot["vales"] += _f(r["vales"]); tot["otros"] += _f(r["otros"])
        tot["propina"] += _f(r["propina"]); tot["comision"] += _f(r["comision"])
    return {"success": True, "source": "Finanzas_CortesCaja (canónica, compartida)", "unidad": unidad,
            "unidad_nombre": nombre, "desde": d, "hasta": h,
            "export_all": export_all, "limited": not export_all, "limit": None if export_all else limit,
            "totales": {k: round(v, 2) for k, v in tot.items()}, "cortes": cortes}


# ============================================================================
# 4b) FORMAS DE PAGO POR TICKET  (NO-LIVE desde dbo.Finanzas_CortesCaja_DetallePagos)
#     Granularidad TICKET (enriquecida por el job de sync). 1 fila = 1 pago.
# ============================================================================
@iscam_router.get("/formas-pago/por-ticket")
async def formas_pago_por_ticket(unidad: str = Query(...), desde: Optional[str] = None,
                                 hasta: Optional[str] = None, group_by: str = Query("none"),
                                 limit: int = Query(2000, ge=1, le=10000),
                                 export_all: bool = Query(False)):
    d, h = _rango_fechas(desde, hasta)
    if group_by in ("anio", "mes", "dia"):
        pexpr = _period_sql("FechaHora", group_by)
        rows = _q(
            f"""
            SELECT {pexpr} AS periodo, FormaPago AS forma, FormaPagoCodigo AS codigo,
                   COUNT(DISTINCT NumeroTicket) AS tickets, COUNT(*) AS pagos,
                   SUM(Importe) AS importe, SUM(ISNULL(Propina,0)) AS propina
            FROM dbo.Finanzas_CortesCaja_DetallePagos
            WHERE UnidadNegocio = %s AND ISNULL(Activo,1)=1
              AND FechaHora >= %s AND FechaHora < %s
            GROUP BY {pexpr}, FormaPago, FormaPagoCodigo
            ORDER BY periodo DESC, importe DESC
            """,
            (unidad, d, h),
        )
        tot_i = sum(_f(r["importe"]) for r in rows); tot_p = sum(_f(r["propina"]) for r in rows)
        return {"success": True, "source": "Finanzas_CortesCaja_DetallePagos (canónica, ticket)",
                "unidad": unidad, "desde": d, "hasta": h, "group_by": group_by,
                "totales": {"importe": round(tot_i, 2), "propina": round(tot_p, 2)},
                "agrupado": [{"periodo": r["periodo"], "forma": r["forma"], "codigo": r["codigo"],
                              "tickets": int(r["tickets"] or 0), "pagos": int(r["pagos"] or 0),
                              "importe": round(_f(r["importe"]), 2), "propina": round(_f(r["propina"]), 2)} for r in rows]}
    # Resumen por forma de pago (totales)
    resumen = _q(
        """
        SELECT FormaPago AS forma, FormaPagoCodigo AS codigo,
               COUNT(*) AS pagos, COUNT(DISTINCT NumeroTicket) AS tickets,
               SUM(Importe) AS importe, SUM(ISNULL(Propina,0)) AS propina
        FROM dbo.Finanzas_CortesCaja_DetallePagos
        WHERE UnidadNegocio = %s AND ISNULL(Activo,1)=1
          AND FechaHora >= %s AND FechaHora < %s
        GROUP BY FormaPago, FormaPagoCodigo
        ORDER BY importe DESC
        """,
        (unidad, d, h),
    )
    # Detalle por pago. En pantalla puede limitarse; export_all entrega el conjunto completo.
    if export_all:
        rows = _q(
            """
            SELECT NumeroTicket AS folio, FechaHora AS fecha, FormaPago AS forma,
                   FormaPagoCodigo AS codigo, Importe AS importe, ISNULL(Propina,0) AS propina,
                   Referencia AS referencia, SistemaOrigen AS sistema
            FROM dbo.Finanzas_CortesCaja_DetallePagos
            WHERE UnidadNegocio = %s AND ISNULL(Activo,1)=1
              AND FechaHora >= %s AND FechaHora < %s
            ORDER BY FechaHora DESC, NumeroTicket DESC
            """,
            (unidad, d, h),
        )
    else:
        rows = _q(
            """
            SELECT TOP (%s) NumeroTicket AS folio, FechaHora AS fecha, FormaPago AS forma,
                   FormaPagoCodigo AS codigo, Importe AS importe, ISNULL(Propina,0) AS propina,
                   Referencia AS referencia, SistemaOrigen AS sistema
            FROM dbo.Finanzas_CortesCaja_DetallePagos
            WHERE UnidadNegocio = %s AND ISNULL(Activo,1)=1
              AND FechaHora >= %s AND FechaHora < %s
            ORDER BY FechaHora DESC, NumeroTicket DESC
            """,
            (limit, unidad, d, h),
        )
    tot_importe = sum(_f(r["importe"]) for r in resumen)
    tot_propina = sum(_f(r["propina"]) for r in resumen)
    return {
        "success": True, "source": "Finanzas_CortesCaja_DetallePagos (canónica, ticket)",
        "unidad": unidad, "desde": d, "hasta": h,
        "export_all": export_all, "limited": not export_all, "limit": None if export_all else limit,
        "resumen_formas": [{"forma": r["forma"], "codigo": r["codigo"], "pagos": int(r["pagos"] or 0),
                            "tickets": int(r["tickets"] or 0), "importe": round(_f(r["importe"]), 2),
                            "propina": round(_f(r["propina"]), 2)} for r in resumen],
        "totales": {"importe": round(tot_importe, 2), "propina": round(tot_propina, 2)},
        "pagos": [{"folio": r["folio"], "fecha": _iso(r["fecha"]), "forma": r["forma"], "codigo": r["codigo"],
                   "importe": round(_f(r["importe"]), 2), "propina": round(_f(r["propina"]), 2),
                   "referencia": r["referencia"], "sistema": r["sistema"]} for r in rows],
    }


# ============================================================================
# 1b) DESGLOSE POR TIPO DE SERVICIO  (drill del Reporte 1, desde Sync_Sales)
# ============================================================================
@iscam_router.get("/ventas-periodos/tipos-servicio")
async def ventas_periodos_tipos_servicio(unidad: str = Query(...), periodo: str = Query(...),
                                         group_by: str = Query("mes")):
    pexpr = _period_sql("s.FechaHora", group_by)
    rows = _q(
        f"""
        SELECT ISNULL(s.TipoServicio, ISNULL(s.TipoServicioID, 'SIN_DATOS')) AS tipo,
               s.TipoServicioID AS tipo_id,
               SUM(s.MontoTotal) AS venta_total, COUNT(*) AS cheques, SUM(s.Pax) AS clientes
        FROM dbo.Sync_Sales s
        WHERE s.UnidadNegocio = %s AND s.status = 'COMPLETED'
          AND {pexpr} = %s
        GROUP BY s.TipoServicio, s.TipoServicioID
        ORDER BY venta_total DESC
        """,
        (unidad, periodo),
    )
    data = []
    for r in rows:
        venta = _f(r["venta_total"]); cheques = int(r["cheques"] or 0)
        data.append({"tipo": r["tipo"], "tipo_id": r["tipo_id"], "venta_total": round(venta, 2),
                     "cheques": cheques, "clientes": int(r["clientes"] or 0),
                     "cheque_promedio": round(venta / cheques, 2) if cheques else 0})
    return {"success": True, "unidad": unidad, "periodo": periodo, "tipos_servicio": data}



# ============================================================================
def _rango_fechas(desde: Optional[str], hasta: Optional[str]):
    """Normaliza rango. Por defecto: últimos 30 días. `hasta` es exclusivo (+1 día)."""
    try:
        d = datetime.strptime(desde, "%Y-%m-%d") if desde else datetime.now() - timedelta(days=30)
    except Exception:
        d = datetime.now() - timedelta(days=30)
    try:
        h = (datetime.strptime(hasta, "%Y-%m-%d") + timedelta(days=1)) if hasta else datetime.now() + timedelta(days=1)
    except Exception:
        h = datetime.now() + timedelta(days=1)
    return d.strftime("%Y-%m-%d"), h.strftime("%Y-%m-%d")
