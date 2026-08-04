from typing import List, Optional

from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
from fastapi import APIRouter, Depends, HTTPException, Query
from core.security import get_current_user
from core.config.edarsahub_sql import get_edarsahub_connection
from core.kpis_canonicos import KPIsCanonicosService
from modules.comercial_v2.routes import get_unidades_permitidas_v2
from datetime import date, timedelta

router = APIRouter(prefix="/api/dashboard-ejecutivo", tags=["Dashboard Ejecutivo"])

def q(sql, params=()):
    cn = get_edarsahub_connection()
    cur = cn.cursor(as_dict=True)
    try:
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cn.close()


def _parse_iso_date(value: str, field_name: str) -> date:
    try:
        return date.fromisoformat(str(value or "").strip())
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"{field_name} debe usar formato YYYY-MM-DD",
        ) from exc


def _resolver_unidad_pk(value: str) -> Optional[str]:
    raw = str(value or "").strip()
    if not raw:
        return None

    try:
        resolved = CorporateFilterService.resolver_unidad(raw) or {}
        pk = resolved.get("pk") or resolved.get("unidad_negocio_pk")
        if pk:
            return str(pk)
    except Exception:
        pass

    try:
        pk = UnidadesService.resolver_pk(raw)
        return str(pk) if pk else None
    except Exception:
        return None


async def _resolver_scope_unidades(
    current_user: dict,
    unidades_solicitadas: Optional[List[str]],
) -> List[str]:
    unidades_permitidas = await get_unidades_permitidas_v2(current_user)

    permitidas_pks = set()
    for value in unidades_permitidas or []:
        pk = _resolver_unidad_pk(value)
        if pk:
            permitidas_pks.add(pk)

    if not permitidas_pks:
        raise HTTPException(
            status_code=403,
            detail="El usuario no tiene unidades permitidas",
        )

    solicitadas = [
        str(value).strip()
        for value in (unidades_solicitadas or [])
        if str(value or "").strip()
    ]

    if not solicitadas:
        return sorted(permitidas_pks)

    solicitadas_pks = set()
    desconocidas = []

    for value in solicitadas:
        pk = _resolver_unidad_pk(value)
        if not pk:
            desconocidas.append(value)
        else:
            solicitadas_pks.add(pk)

    if desconocidas:
        raise HTTPException(
            status_code=422,
            detail={
                "mensaje": "Existen unidades desconocidas",
                "unidades": sorted(set(desconocidas)),
            },
        )

    no_permitidas = solicitadas_pks - permitidas_pks
    if no_permitidas:
        raise HTTPException(
            status_code=403,
            detail="No tiene acceso a una o más unidades solicitadas",
        )

    return sorted(solicitadas_pks)


@router.get("/resumen")
async def resumen(
    fecha_inicio: str = Query(...),
    fecha_fin: str = Query(...),
    unidades: Optional[List[str]] = Query(default=None),
    current_user: dict = Depends(get_current_user),
):
    """KPIs canónicos por fecha_operacion y alcance RBAC de unidades."""
    inicio = _parse_iso_date(fecha_inicio, "fecha_inicio")
    fin = _parse_iso_date(fecha_fin, "fecha_fin")

    if inicio > fin:
        raise HTTPException(
            status_code=422,
            detail="fecha_inicio no puede ser posterior a fecha_fin",
        )

    unidad_pks = await _resolver_scope_unidades(
        current_user,
        unidades,
    )

    hasta_excl = (fin + timedelta(days=1)).isoformat()

    desglose = KPIsCanonicosService.resumen_periodo_desglosado(
        inicio.isoformat(),
        hasta_excl,
        unidad_pks=unidad_pks,
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
            "inicio": inicio.isoformat(),
            "fin": fin.isoformat(),
            "hasta_exclusivo": hasta_excl,
            "contrato_acumulado": "CERRADO_SIN_DIA_OPERATIVO_ACTUAL",
        },
        "scope": {
            "unidad_pks": unidad_pks,
            "cantidad_unidades": len(unidad_pks),
            "rbac_aplicado": True,
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
