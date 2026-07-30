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
    """KPIs cerrados y operación vigente separada desde el contrato canónico."""
    try:
        hasta_excl = (datetime.fromisoformat(fecha_fin) + timedelta(days=1)).date().isoformat()
    except Exception:
        hasta_excl = fecha_fin

    desglose = KPIsCanonicosService.resumen_periodo_desglosado(
        fecha_inicio,
        hasta_excl,
    )
    acumulado = desglose.get("acumulado_cerrado") or {}
    dia_actual = desglose.get("dia_actual") or {}
    total_con_dia = desglose.get("total_incluyendo_dia") or {}

    def metricas_payload(resumen_data):
        metricas = resumen_data.get("metricas") or {}
        return {
            "ventas": float(metricas.get("ventas") or 0),
            "ventas_brutas": float(metricas.get("ventas_brutas") or metricas.get("ventas") or 0),
            "propinas": float(metricas.get("propinas") or 0),
            "propinas_total": float(metricas.get("propinas") or 0),
            "tickets": float(metricas.get("tickets") or 0),
            "cheques": float(metricas.get("cheques") or 0),
            "pax": float(metricas.get("pax") or 0),
            "cheque_promedio": float(metricas.get("cheque_promedio") or 0),
            "ticket_promedio": float(metricas.get("ticket_promedio") or 0),
            "consumo_promedio_pax": float(metricas.get("consumo_promedio_pax") or 0),
            "pax_promedio": float(metricas.get("pax_promedio") or 0),
            "cheques_por_pax": float(metricas.get("cheques_por_pax") or 0),
        }

    def unidades_payload(resumen_data):
        unidades = sorted(
            resumen_data.get("por_unidad", []),
            key=lambda x: float((x.get("metricas") or {}).get("ventas") or 0),
            reverse=True,
        )
        salida = []
        for item in unidades:
            metricas = item.get("metricas") or {}
            salida.append({
                "server_id": item.get("server_id"),
                "unidad": item.get("unidad_nombre"),
                "unidad_codigo": item.get("unidad_codigo"),
                "dias": item.get("dias"),
                "ventas": float(metricas.get("ventas") or 0),
                "ventas_brutas": float(metricas.get("ventas_brutas") or metricas.get("ventas") or 0),
                "propinas": float(metricas.get("propinas") or 0),
                "propinas_total": float(metricas.get("propinas") or 0),
                "tickets": float(metricas.get("tickets") or 0),
                "cheques": float(metricas.get("cheques") or 0),
                "pax": float(metricas.get("pax") or 0),
                "cheque_promedio": float(metricas.get("cheque_promedio") or 0),
                "ticket_promedio": float(metricas.get("ticket_promedio") or 0),
                "pax_promedio": float(metricas.get("pax_promedio") or 0),
            })
        return salida

    ventas = unidades_payload(acumulado)
    ventas_dia = unidades_payload(dia_actual)

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

    return {
        "success": True,
        "source": "EDARSAHUB_SQL",
        "kpis_origen": "KPIsCanonicosService",
        "periodo": {
            "inicio": fecha_inicio,
            "fin": fecha_fin,
            "contrato_acumulado": "CERRADO_SIN_DIA_OPERATIVO_ACTUAL",
        },
        "contrato_periodo": desglose.get("contrato") or {},
        "kpis": metricas_payload(acumulado),
        "ventas_por_unidad": ventas,
        "ventas_dia_actual": {
            "kpis": metricas_payload(dia_actual),
            "ventas_por_unidad": ventas_dia,
        },
        "total_incluyendo_dia_actual": {
            "kpis": metricas_payload(total_con_dia),
        },
        "precios": precios[0] if precios else {},
        "productos": productos[0] if productos else {},
        "compras": compras[0] if compras else {},
        "sync_24h": sync,
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
