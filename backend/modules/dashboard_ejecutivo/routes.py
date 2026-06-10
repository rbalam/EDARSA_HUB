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
    # Promedios usan ventas_sin_propina (neto) por definición canónica en SQL.
    # El rango del servicio es [desde, hasta); convertimos fecha_fin a límite
    # exclusivo (+1 día) para preservar la semántica inclusiva del endpoint.
    try:
        hasta_excl = (datetime.fromisoformat(fecha_fin) + timedelta(days=1)).date().isoformat()
    except Exception:
        hasta_excl = fecha_fin

    agg = KPIsCanonicosService.agregados_por_unidad(fecha_inicio, hasta_excl)
    agg = sorted(agg, key=lambda x: float(x.get("ventas_sin_propina") or 0), reverse=True)

    ventas = [{
        "server_id": a.get("server_id"),
        "unidad": a.get("unidad_nombre"),
        "unidad_codigo": a.get("unidad_codigo"),
        "dias": a.get("dias"),
        "ventas": float(a.get("ventas_sin_propina") or 0),   # neto (canónico)
        "ventas_brutas": float(a.get("ventas") or 0),         # con propina (referencia)
        "tickets": float(a.get("cheques") or 0),              # alias retrocompatible
        "cheques": float(a.get("cheques") or 0),
        "pax": float(a.get("pax") or 0),
    } for a in agg]

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

    total_ventas = sum(float(x.get("ventas") or 0) for x in ventas)         # neto (sin propina)
    total_ventas_brutas = sum(float(x.get("ventas_brutas") or 0) for x in ventas)
    total_tickets = sum(float(x.get("cheques") or 0) for x in ventas)
    total_pax = sum(float(x.get("pax") or 0) for x in ventas)

    cheque_promedio = total_ventas / total_tickets if total_tickets else 0  # neto / cheques
    ticket_promedio = total_ventas / total_pax if total_pax else 0          # neto / pax (canónico)

    return {
        "success": True,
        "source": "EDARSAHUB_SQL",
        "kpis_origen": "KPIsCanonicosService",
        "periodo": {"inicio": fecha_inicio, "fin": fecha_fin},
        "kpis": {
            "ventas": total_ventas,                    # NETO (canónico, sin propina)
            "ventas_brutas": total_ventas_brutas,      # con propina (referencia)
            "tickets": total_tickets,                  # alias retrocompatible
            "cheques": total_tickets,
            "pax": total_pax,
            "cheque_promedio": cheque_promedio,        # neto / cheques (por cuenta)
            "ticket_promedio": ticket_promedio,        # neto / pax (canónico, por comensal)
            "consumo_promedio_pax": ticket_promedio,   # alias retrocompatible (= ticket_promedio)
            "cheques_por_pax": total_tickets / total_pax if total_pax else 0
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
