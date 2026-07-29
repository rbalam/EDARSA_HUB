from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
from fastapi import APIRouter, Depends, Query
from core.security import get_current_user
from core.config.edarsahub_sql import get_edarsahub_connection
from core.sql_first.db import get_sql_connection
from core.kpis_canonicos import KPIsCanonicosService
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/dashboard-ejecutivo", tags=["Dashboard Ejecutivo"])

def q(sql, params=()):
    cn = get_edarsahub_connection()
    cur = cn.cursor(as_dict=True)
    cur.execute(sql, params)
    rows = cur.fetchall()
    cn.close()
    return rows

@router.get("/resumen")
async def resumen(
    fecha_inicio: str = Query(default="2026-06-01"),
    fecha_fin: str = Query(default="2026-06-30"),
    current_user: dict = Depends(get_current_user)
):
    # KPIs comerciales: fuente ÚNICA canónica (KPIsCanonicosService, NO-LIVE).
    # Promedios usan ventas_total con IVA; propinas permanecen separadas.
    # El rango del servicio es [desde, hasta); convertimos fecha_fin a límite
    # exclusivo (+1 día) para preservar la semántica inclusiva del endpoint.
    try:
        hasta_excl = (datetime.fromisoformat(fecha_fin) + timedelta(days=1)).date().isoformat()
    except Exception:
        hasta_excl = fecha_fin

    resumen_kpis = KPIsCanonicosService.resumen_periodo(fecha_inicio, hasta_excl)
    unidades_kpi = sorted(
        resumen_kpis.get("por_unidad", []),
        key=lambda x: float((x.get("metricas") or {}).get("ventas") or 0),
        reverse=True
    )

    ventas = []
    for a in unidades_kpi:
        m = a.get("metricas") or {}
        ventas.append({
            "server_id": a.get("server_id"),
            "unidad": a.get("unidad_nombre"),
            "unidad_codigo": a.get("unidad_codigo"),
            "dias": a.get("dias"),
            "ventas": float(m.get("ventas") or 0),
            "ventas_brutas": float(m.get("ventas_brutas") or 0),
            "propinas": float(m.get("propinas") or 0),
            "propinas_total": float(m.get("propinas") or 0),
            "tickets": float(m.get("tickets") or 0),
            "cheques": float(m.get("cheques") or 0),
            "pax": float(m.get("pax") or 0),
            "cheque_promedio": float(m.get("cheque_promedio") or 0),
            "ticket_promedio": float(m.get("ticket_promedio") or 0),
            "pax_promedio": float(m.get("pax_promedio") or 0),
        })

    precios = q("""
    SELECT
        COUNT(*) AS productos_con_precio,
        COUNT(DISTINCT ServerID) AS servidores_precio,
        AVG(CAST(PrecioFinal AS FLOAT)) AS precio_promedio
    FROM Sync_Precios_Historicos
    """)

    productos = q("""
    SELECT
        COUNT(*) AS productos,
        COUNT(DISTINCT ServerID) AS servidores_producto
    FROM Sync_Productos
    """)

    compras = q("""
    SELECT
        (SELECT COUNT(*) FROM Compras_Pedidos) AS pedidos,
        (SELECT COUNT(*) FROM Compras_PedidosDetalle) AS detalles,
        (SELECT COUNT(*) FROM Compras_Ordenes) AS ordenes,
        (SELECT COUNT(*) FROM Compras_Recepciones) AS recepciones
    """)

    sync = q("""
    SELECT TOP 20
        sync_type,
        status,
        COUNT(*) AS eventos,
        SUM(ISNULL(records_synced,0)) AS registros
    FROM Compras_Sync_Log
    WHERE sync_start >= DATEADD(HOUR,-24,GETDATE())
    GROUP BY sync_type, status
    ORDER BY eventos DESC
    """)

    metricas = resumen_kpis.get("metricas") or {}

    return {
        "success": True,
        "source": "EDARSAHUB_SQL",
        "kpis_origen": "KPIsCanonicosService",
        "periodo": {"inicio": fecha_inicio, "fin": fecha_fin},
        "kpis": {
            "ventas": float(metricas.get("ventas") or 0),
            "ventas_brutas": float(metricas.get("ventas_brutas") or 0),
            "propinas": float(metricas.get("propinas") or 0),
            "propinas_total": float(metricas.get("propinas") or 0),
            "tickets": float(metricas.get("tickets") or 0),
            "cheques": float(metricas.get("cheques") or 0),
            "pax": float(metricas.get("pax") or 0),
            "cheque_promedio": float(metricas.get("cheque_promedio") or 0),
            "ticket_promedio": float(metricas.get("ticket_promedio") or 0),
            "consumo_promedio_pax": float(metricas.get("consumo_promedio_pax") or 0),
            "pax_promedio": float(metricas.get("pax_promedio") or 0),
            "cheques_por_pax": float(metricas.get("cheques_por_pax") or 0)
        },
        "ventas_por_unidad": ventas,
        "precios": precios[0] if precios else {},
        "productos": productos[0] if productos else {},
        "compras": compras[0] if compras else {},
        "sync_24h": sync
    }

@router.get("/rentabilidad-base")
async def rentabilidad_base(
    server_id: str = Query(default=""),
    limite: int = Query(default=100, ge=1, le=500),
    current_user: dict = Depends(get_current_user)
):
    where = ""
    params = []
    if server_id:
        where = "WHERE CAST(p.ServerID AS NVARCHAR(100)) = CAST(%s AS NVARCHAR(100))"
        params.append(server_id)

    rows = q(f"""
    SELECT TOP ({int(limite)})
        p.ServerID,
        s.nombre AS servidor,
        p.ProductoID,
        p.ProductoCodigo,
        p.ProductoNombre,
        CAST(p.PrecioFinal AS FLOAT) AS precio_final,
        CAST(NULL AS FLOAT) AS costo_estimado,
        CAST(NULL AS FLOAT) AS margen_estimado,
        'PENDIENTE_COSTO_RECETA' AS status_margen
    FROM Sync_Precios_Historicos p
    LEFT JOIN Servidores_Conexiones s
        ON CAST(s.id AS NVARCHAR(100)) = CAST(p.ServerID AS NVARCHAR(100))
    {where}
    ORDER BY p.ProductoNombre
    """, tuple(params))

    return {
        "success": True,
        "source": "EDARSAHUB_SQL",
        "modo": "RENTABILIDAD_BASE_SIN_COSTO",
        "total": len(rows),
        "data": rows,
        "nota": "Base lista. Para margen real se requiere tabla/campo de costo receta canónico."
    }
