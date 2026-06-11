"""
Reportes ISCAM - Portal de Inteligencia Comercial
==================================================
4 reportes de explotación de ventas, 100% sobre tablas CANÓNICAS de EDARSAHUB
(NO-LIVE, sin hardcode, sin duplicar):

  1. Ventas a 12 periodos        -> dbo.Sync_Sales  (drill: mes -> productos -> tickets)
  2. Resumen de cuentas          -> dbo.Sync_Sales  (drill: cuenta -> productos)
  3. Comandas de venta           -> dbo.Sync_Sales.items (OPENJSON)
  4. Ventas por formas de pago   -> dbo.Finanzas_CortesCaja  (REUTILIZADA del módulo Finanzas)

El scoping por unidad de negocio para usuarios EXTERNOS lo aplica `intel_portal_guard`
(montado al incluir este router en server.py). `unidad` = CÓDIGO de unidad de negocio.
"""
import logging
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Query, HTTPException

from core.sql_first.db import get_sql_connection
from core.unidades_service import UnidadesService

logger = logging.getLogger(__name__)

iscam_router = APIRouter(prefix="/inteligencia/iscam", tags=["Reportes ISCAM"])

# Detalle de productos embebido como JSON en Sync_Sales.items
_OPENJSON_ITEMS = (
    "CROSS APPLY OPENJSON(s.items) WITH ("
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


# ============================================================================
# 1) VENTAS A 12 PERIODOS
# ============================================================================
@iscam_router.get("/ventas-periodos")
async def ventas_periodos(unidad: str = Query(...), meses: int = Query(12, ge=1, le=36)):
    rows = _q(
        """
        SELECT FORMAT(s.FechaHora,'yyyy-MM') AS periodo,
               SUM(s.MontoTotal) AS venta_total,
               COUNT(*)          AS cheques,
               SUM(s.Pax)        AS clientes
        FROM dbo.Sync_Sales s
        WHERE s.UnidadNegocio = %s AND s.status = 'COMPLETED'
          AND s.FechaHora >= DATEADD(MONTH, %s, CAST(GETDATE() AS DATE))
        GROUP BY FORMAT(s.FechaHora,'yyyy-MM')
        ORDER BY periodo DESC
        """,
        (unidad, -int(meses)),
    )
    data = []
    for r in rows:
        venta = _f(r["venta_total"]); cheques = int(r["cheques"] or 0); cli = int(r["clientes"] or 0)
        data.append({
            "periodo": r["periodo"],
            "venta_total": round(venta, 2),
            "cheques": cheques,
            "clientes": cli,
            "cheque_promedio": round(venta / cheques, 2) if cheques else 0,
            "consumo_promedio": round(venta / cli, 2) if cli else 0,
        })
    return {"success": True, "source": "Sync_Sales (canónica)", "unidad": unidad, "periodos": data}


@iscam_router.get("/ventas-periodos/productos")
async def ventas_periodos_productos(unidad: str = Query(...), periodo: str = Query(..., description="YYYY-MM")):
    rows = _q(
        f"""
        SELECT j.prod_id AS codigo, MAX(j.prod_name) AS producto,
               SUM(j.cantidad) AS cantidad, SUM(j.importe) AS importe,
               COUNT(DISTINCT s.id) AS tickets
        FROM dbo.Sync_Sales s {_OPENJSON_ITEMS}
        WHERE s.UnidadNegocio = %s AND s.status = 'COMPLETED'
          AND FORMAT(s.FechaHora,'yyyy-MM') = %s
        GROUP BY j.prod_id
        ORDER BY importe DESC
        """,
        (unidad, periodo),
    )
    return {"success": True, "unidad": unidad, "periodo": periodo,
            "productos": [{"codigo": r["codigo"], "producto": r["producto"],
                           "cantidad": _f(r["cantidad"]), "importe": round(_f(r["importe"]), 2),
                           "tickets": int(r["tickets"] or 0)} for r in rows]}


@iscam_router.get("/ventas-periodos/tickets")
async def ventas_periodos_tickets(unidad: str = Query(...), periodo: str = Query(...), producto: str = Query(...)):
    rows = _q(
        f"""
        SELECT s.NumeroTicket AS folio, s.FechaHora AS fecha, s.MontoTotal AS importe_ticket,
               s.Pax AS personas, j.cantidad AS cantidad, j.importe AS importe_producto
        FROM dbo.Sync_Sales s {_OPENJSON_ITEMS}
        WHERE s.UnidadNegocio = %s AND s.status = 'COMPLETED'
          AND FORMAT(s.FechaHora,'yyyy-MM') = %s AND j.prod_id = %s
        ORDER BY s.FechaHora DESC
        """,
        (unidad, periodo, producto),
    )
    return {"success": True, "tickets": [{
        "folio": r["folio"], "fecha": r["fecha"].isoformat() if r["fecha"] else None,
        "importe_ticket": round(_f(r["importe_ticket"]), 2), "personas": int(r["personas"] or 0),
        "cantidad": _f(r["cantidad"]), "importe_producto": round(_f(r["importe_producto"]), 2)} for r in rows]}


# ============================================================================
# 2) RESUMEN DE CUENTAS
# ============================================================================
@iscam_router.get("/cuentas")
async def resumen_cuentas(unidad: str = Query(...), desde: Optional[str] = None, hasta: Optional[str] = None,
                          limit: int = Query(500, ge=1, le=2000)):
    d, h = _rango_fechas(desde, hasta)
    rows = _q(
        """
        SELECT TOP (%s) s.NumeroTicket AS folio, s.FechaHora AS fecha, s.MontoTotal AS importe,
               s.Pax AS personas, s.status AS estado, s.id AS cuenta_id
        FROM dbo.Sync_Sales s
        WHERE s.UnidadNegocio = %s AND s.FechaHora >= %s AND s.FechaHora < %s
        ORDER BY s.FechaHora DESC
        """,
        (limit, unidad, d, h),
    )
    return {"success": True, "unidad": unidad, "desde": d, "hasta": h,
            "cuentas": [{"folio": r["folio"], "fecha": r["fecha"].isoformat() if r["fecha"] else None,
                         "importe": round(_f(r["importe"]), 2), "personas": int(r["personas"] or 0),
                         "estado": r["estado"], "cuenta_id": r["cuenta_id"]} for r in rows]}


@iscam_router.get("/cuentas/detalle")
async def cuenta_detalle(unidad: str = Query(...), folio: str = Query(...)):
    rows = _q(
        f"""
        SELECT j.prod_id AS codigo, j.prod_name AS producto, j.cantidad AS cantidad,
               j.precio AS precio, j.importe AS importe
        FROM dbo.Sync_Sales s {_OPENJSON_ITEMS}
        WHERE s.UnidadNegocio = %s AND s.NumeroTicket = %s
        ORDER BY j.importe DESC
        """,
        (unidad, folio),
    )
    return {"success": True, "folio": folio,
            "productos": [{"codigo": r["codigo"], "producto": r["producto"], "cantidad": _f(r["cantidad"]),
                           "precio": round(_f(r["precio"]), 2), "importe": round(_f(r["importe"]), 2)} for r in rows]}


# ============================================================================
# 3) COMANDAS DE VENTA
# ============================================================================
@iscam_router.get("/comandas")
async def comandas_venta(unidad: str = Query(...), desde: Optional[str] = None, hasta: Optional[str] = None,
                         limit: int = Query(1000, ge=1, le=5000)):
    d, h = _rango_fechas(desde, hasta)
    rows = _q(
        f"""
        SELECT TOP (%s) s.NumeroTicket AS folio_cuenta, s.FechaHora AS fecha,
               j.prod_id AS clave, j.prod_name AS descripcion, j.cantidad AS cantidad,
               j.precio AS precio, j.importe AS importe
        FROM dbo.Sync_Sales s {_OPENJSON_ITEMS}
        WHERE s.UnidadNegocio = %s AND s.status = 'COMPLETED'
          AND s.FechaHora >= %s AND s.FechaHora < %s
        ORDER BY s.FechaHora DESC
        """,
        (limit, unidad, d, h),
    )
    return {"success": True, "unidad": unidad, "desde": d, "hasta": h,
            "comandas": [{"folio_cuenta": r["folio_cuenta"], "fecha": r["fecha"].isoformat() if r["fecha"] else None,
                          "clave": r["clave"], "descripcion": r["descripcion"], "cantidad": _f(r["cantidad"]),
                          "precio": round(_f(r["precio"]), 2), "importe": round(_f(r["importe"]), 2)} for r in rows]}


# ============================================================================
# 4) VENTAS POR FORMAS DE PAGO  (REUTILIZA dbo.Finanzas_CortesCaja)
# ============================================================================
@iscam_router.get("/formas-pago")
async def ventas_formas_pago(unidad: str = Query(...), desde: Optional[str] = None, hasta: Optional[str] = None,
                             limit: int = Query(1000, ge=1, le=5000)):
    nombre = _nombre_unidad(unidad)
    if not nombre:
        raise HTTPException(status_code=404, detail=f"No se pudo resolver la unidad '{unidad}'")
    d, h = _rango_fechas(desde, hasta)
    rows = _q(
        """
        SELECT TOP (%s) FolioCorte AS folio, FechaCierre AS fecha, TotalVenta AS total,
               TotalEfectivo AS efectivo, TotalTarjetaDebito AS tarjeta_debito,
               TotalTarjetaCredito AS tarjeta_credito, TotalAmex AS amex,
               TotalInternacional AS internacional, TotalVales AS vales, TotalOtros AS otros,
               Propinas AS propina,
               (ISNULL(ComisionDebito,0)+ISNULL(ComisionCredito,0)+ISNULL(ComisionAmex,0)+ISNULL(ComisionInternacional,0)) AS comision,
               CajaNombre AS caja
        FROM dbo.Finanzas_CortesCaja
        WHERE UnidadNegocioNombre = %s AND ISNULL(Activo,1)=1
          AND FechaCierre >= %s AND FechaCierre < %s
        ORDER BY FechaCierre DESC
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
            "totales": {k: round(v, 2) for k, v in tot.items()}, "cortes": cortes}


# ============================================================================
# 4b) FORMAS DE PAGO POR TICKET  (NO-LIVE desde dbo.Finanzas_CortesCaja_DetallePagos)
#     Granularidad TICKET (enriquecida por el job de sync). 1 fila = 1 pago.
# ============================================================================
@iscam_router.get("/formas-pago/por-ticket")
async def formas_pago_por_ticket(unidad: str = Query(...), desde: Optional[str] = None,
                                 hasta: Optional[str] = None, limit: int = Query(2000, ge=1, le=10000)):
    d, h = _rango_fechas(desde, hasta)
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
    # Detalle por pago (limitado)
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
async def ventas_periodos_tipos_servicio(unidad: str = Query(...), periodo: str = Query(..., description="YYYY-MM")):
    rows = _q(
        """
        SELECT ISNULL(s.TipoServicio, ISNULL(s.TipoServicioID, 'SIN_DATOS')) AS tipo,
               s.TipoServicioID AS tipo_id,
               SUM(s.MontoTotal) AS venta_total, COUNT(*) AS cheques, SUM(s.Pax) AS clientes
        FROM dbo.Sync_Sales s
        WHERE s.UnidadNegocio = %s AND s.status = 'COMPLETED'
          AND FORMAT(s.FechaHora,'yyyy-MM') = %s
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
