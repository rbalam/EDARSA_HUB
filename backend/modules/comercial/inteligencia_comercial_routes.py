"""
EDARSA HUB - Portal Inteligencia Comercial Fase 1
=================================================
Endpoints SQL-first para dashboard ejecutivo.

Reglas:
- Lee EDARSAHUB SQL Server EXCLUSIVAMENTE.
- Usa vistas canónicas: Comercial_Inteligencia_VW_KPIsEjecutivos
- Usa SP canónico: Sp_Validar_Inteligencia_Comercial_Status
- No consulta SoftRestaurant/MPRO en vivo desde dashboard.
- No usa MongoDB como fuente de datos comerciales.
- No crea ni modifica datos.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
import logging
import os

import pytds
from fastapi import APIRouter, Depends, HTTPException, Query

from core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/comercial/inteligencia", tags=["comercial-inteligencia"])


# ============================================================
# UTILIDADES
# ============================================================

def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _rows_to_dicts(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{k: _json_safe(v) for k, v in row.items()} for row in rows]


def _get_edarsahub_sql_connection():
    """
    Conexión central a EDARSAHUB SQL usando variables de entorno.
    NO conecta a SoftRestaurant, MPRO, MongoDB ni sistemas externos.
    """
    host = os.environ.get("EDARSAHUB_SQL_HOST") or os.environ.get("EDARSA_HUB_SQL_HOST")
    if not host:
        raise RuntimeError("Falta EDARSAHUB_SQL_HOST")

    port = int(os.environ.get("EDARSAHUB_SQL_PORT") or os.environ.get("EDARSA_HUB_SQL_PORT") or "1433")
    database = os.environ.get("EDARSAHUB_SQL_DATABASE") or os.environ.get("EDARSA_HUB_SQL_DB") or "EDARSAHUB"
    user = os.environ.get("EDARSAHUB_SQL_USER") or os.environ.get("EDARSA_HUB_SQL_USER") or "HRLectura"
    password = os.environ.get("EDARSAHUB_SQL_PASSWORD") or os.environ.get("EDARSA_HUB_SQL_PASS") or ""

    return pytds.connect(
        server=host,
        port=port,
        database=database,
        user=user,
        password=password,
        timeout=30,
        login_timeout=30,
        as_dict=True,
    )


def _query(sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Ejecuta query de solo lectura contra EDARSAHUB SQL."""
    try:
        with _get_edarsahub_sql_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params or {})
                rows = cur.fetchall() or []
                return _rows_to_dicts(rows)
    except Exception as exc:
        logger.exception("Error consultando EDARSAHUB SQL Inteligencia Comercial")
        raise HTTPException(status_code=500, detail=f"Error SQL Inteligencia Comercial: {str(exc)[:300]}")


def _exec_sp(sp_name: str) -> List[Dict[str, Any]]:
    """Ejecuta un Stored Procedure de EDARSAHUB SQL."""
    try:
        with _get_edarsahub_sql_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"EXEC dbo.{sp_name}")
                rows = cur.fetchall() or []
                return _rows_to_dicts(rows)
    except Exception as exc:
        logger.exception(f"Error ejecutando SP {sp_name}")
        raise HTTPException(status_code=500, detail=f"Error SP {sp_name}: {str(exc)[:300]}")


# ============================================================
# RBAC / PERMISOS
# ============================================================

def _require_permission(current_user: Dict[str, Any], permission: str = "INTELIGENCIA_COMERCIAL_VER") -> None:
    """
    Validador de permisos compatible con RBAC SQL y legacy.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")

    # Superadmin/admin legacy
    role = str(current_user.get("role") or current_user.get("rol") or "").upper()
    if role in {"SUPERADMIN", "ADMIN", "ADMINISTRADOR"}:
        return

    permissions = current_user.get("permissions") or current_user.get("permisos") or []
    if isinstance(permissions, dict):
        permissions = list(permissions.keys())
    permissions = {str(p).upper() for p in permissions}

    if permissions and permission.upper() not in permissions and "INTELIGENCIA_COMERCIAL_ADMIN" not in permissions:
        raise HTTPException(status_code=403, detail=f"Permiso requerido: {permission}")


# ============================================================
# FILTROS
# ============================================================

def _where_kpis(
    unidad_negocio_nombre: Optional[str],
    fecha_inicio: Optional[date],
    fecha_fin: Optional[date],
    anio: Optional[int],
    mes: Optional[int],
) -> tuple[str, Dict[str, Any]]:
    """Construye WHERE con parámetros seguros (no SQL injection)."""
    where = ["1=1"]
    params: Dict[str, Any] = {}

    if unidad_negocio_nombre:
        where.append("unidad_negocio_nombre = %(unidad)s")
        params["unidad"] = unidad_negocio_nombre
    if fecha_inicio:
        where.append("fecha_operacion >= %(fecha_inicio)s")
        params["fecha_inicio"] = fecha_inicio
    if fecha_fin:
        where.append("fecha_operacion <= %(fecha_fin)s")
        params["fecha_fin"] = fecha_fin
    if anio:
        where.append("anio = %(anio)s")
        params["anio"] = anio
    if mes:
        where.append("mes = %(mes)s")
        params["mes"] = mes

    return " AND ".join(where), params


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/kpis")
async def get_inteligencia_kpis(
    unidad_negocio_nombre: Optional[str] = Query(default=None),
    fecha_inicio: Optional[date] = Query(default=None),
    fecha_fin: Optional[date] = Query(default=None),
    anio: Optional[int] = Query(default=None),
    mes: Optional[int] = Query(default=None),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    KPIs consolidados desde vista canónica.
    Fuente: dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
    """
    _require_permission(current_user)
    where_sql, params = _where_kpis(unidad_negocio_nombre, fecha_inicio, fecha_fin, anio, mes)

    sql = f"""
    SELECT
        SUM(ventas_total) AS ventas_total,
        SUM(ventas_sin_propina) AS ventas_sin_propina,
        SUM(propinas_total) AS propinas_total,
        SUM(tickets_total) AS tickets_total,
        SUM(pax_total) AS pax_total,
        CASE WHEN SUM(tickets_total) > 0
             THEN SUM(ventas_sin_propina) / SUM(tickets_total)
             ELSE 0 END AS ticket_promedio,
        CASE WHEN SUM(pax_total) > 0
             THEN SUM(ventas_sin_propina) / SUM(pax_total)
             ELSE 0 END AS consumo_promedio_pax,
        AVG(pax_promedio) AS pax_promedio,
        SUM(ventas_cerradas) AS ventas_cerradas,
        SUM(ventas_abiertas) AS ventas_abiertas,
        SUM(total_estimado_dia) AS total_estimado_dia,
        MIN(fecha_operacion) AS fecha_inicio_real,
        MAX(fecha_operacion) AS fecha_fin_real,
        MAX(fecha_sincronizacion) AS ultima_sincronizacion
    FROM dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
    WHERE {where_sql};
    """
    rows = _query(sql, params)
    return {"source": "Comercial_Inteligencia_VW_KPIsEjecutivos", "data": rows[0] if rows else {}}


@router.get("/ventas-comparativo")
async def get_ventas_comparativo(
    unidad_negocio_nombre: Optional[str] = Query(default=None),
    nivel: str = Query(default="dia", pattern="^(dia|mes|anio)$"),
    fecha_inicio: Optional[date] = Query(default=None),
    fecha_fin: Optional[date] = Query(default=None),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Comparativo de ventas por período.
    Fuente: dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
    """
    _require_permission(current_user)
    fecha_inicio = fecha_inicio or (date.today() - timedelta(days=30))
    fecha_fin = fecha_fin or date.today()

    params: Dict[str, Any] = {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin}
    where = ["fecha_operacion >= %(fecha_inicio)s", "fecha_operacion <= %(fecha_fin)s"]
    if unidad_negocio_nombre:
        where.append("unidad_negocio_nombre = %(unidad)s")
        params["unidad"] = unidad_negocio_nombre

    if nivel == "dia":
        periodo_expr = "CONVERT(VARCHAR(10), fecha_operacion, 120)"
        order_expr = "MIN(fecha_operacion)"
    elif nivel == "mes":
        periodo_expr = "CONCAT(anio, '-', RIGHT('0' + CAST(mes AS VARCHAR(2)), 2))"
        order_expr = "MIN(fecha_operacion)"
    else:
        periodo_expr = "CAST(anio AS VARCHAR(4))"
        order_expr = "MIN(fecha_operacion)"

    sql = f"""
    SELECT
        {periodo_expr} AS periodo,
        SUM(ventas_total) AS ventas_total,
        SUM(ventas_sin_propina) AS ventas_sin_propina,
        SUM(propinas_total) AS propinas_total,
        SUM(tickets_total) AS tickets_total,
        SUM(pax_total) AS pax_total,
        CASE WHEN SUM(tickets_total) > 0
             THEN SUM(ventas_sin_propina) / SUM(tickets_total) ELSE 0 END AS ticket_promedio,
        CASE WHEN SUM(pax_total) > 0
             THEN SUM(ventas_sin_propina) / SUM(pax_total) ELSE 0 END AS consumo_promedio_pax,
        MAX(fecha_sincronizacion) AS ultima_sincronizacion
    FROM dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
    WHERE {' AND '.join(where)}
    GROUP BY {periodo_expr}
    ORDER BY {order_expr};
    """
    return {"source": "Comercial_Inteligencia_VW_KPIsEjecutivos", "nivel": nivel, "data": _query(sql, params)}


@router.get("/pax")
async def get_pax_inteligencia(
    sucursal_nombre: Optional[str] = Query(default=None),
    fecha_inicio: Optional[date] = Query(default=None),
    fecha_fin: Optional[date] = Query(default=None),
    detalle_mesero: bool = Query(default=False),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Detalle de PAX (comensales).
    Fuente: dbo.Sync_PAX_Detalle (tabla sincronizada)
    """
    _require_permission(current_user)
    fecha_inicio = fecha_inicio or (date.today() - timedelta(days=30))
    fecha_fin = fecha_fin or date.today()

    params: Dict[str, Any] = {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin}
    where = ["FechaOperacion >= %(fecha_inicio)s", "FechaOperacion <= %(fecha_fin)s"]
    if sucursal_nombre:
        where.append("SucursalNombre = %(sucursal)s")
        params["sucursal"] = sucursal_nombre

    group_cols = "SucursalNombre, Turno, DiaSemana"
    select_mesero = ""
    if detalle_mesero:
        group_cols += ", MeseroID, MeseroNombre"
        select_mesero = ", MeseroID, MeseroNombre"

    sql = f"""
    SELECT
        SucursalNombre,
        Turno,
        DiaSemana
        {select_mesero},
        SUM(ISNULL(NumeroComensales, 0)) AS numero_comensales,
        SUM(ISNULL(VentaCuenta, 0)) AS venta_cuenta,
        CASE WHEN SUM(ISNULL(NumeroComensales, 0)) > 0
             THEN SUM(ISNULL(VentaCuenta, 0)) / SUM(ISNULL(NumeroComensales, 0)) ELSE 0 END AS consumo_promedio_pax,
        AVG(CAST(ISNULL(TiempoMesa, 0) AS FLOAT)) AS tiempo_mesa_promedio,
        MAX(FechaSync) AS ultima_sync
    FROM dbo.Sync_PAX_Detalle
    WHERE {' AND '.join(where)}
    GROUP BY {group_cols}
    ORDER BY SucursalNombre, Turno, DiaSemana;
    """
    return {"source": "Sync_PAX_Detalle", "data": _query(sql, params)}


@router.get("/unidades")
async def get_unidades_inteligencia(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Lista de unidades de negocio activas.
    Fuente: dbo.Unidades_Negocio
    """
    _require_permission(current_user)
    sql = """
    SELECT
        codigo,
        nombre,
        system_type,
        server_id,
        activo,
        orden
    FROM dbo.Unidades_Negocio
    WHERE ISNULL(activo, 1) = 1
    ORDER BY ISNULL(orden, 999), nombre;
    """
    return {"source": "Unidades_Negocio", "data": _query(sql)}


@router.get("/sync-status")
async def get_sync_status_inteligencia(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Estado de sincronización de fuentes de datos.
    Fuente: dbo.Sp_Validar_Inteligencia_Comercial_Status (SP canónico)
    """
    _require_permission(current_user)
    
    # Usar el SP canónico
    rows = _exec_sp("Sp_Validar_Inteligencia_Comercial_Status")
    
    return {
        "source": "Sp_Validar_Inteligencia_Comercial_Status",
        "data": rows
    }


@router.get("/tendencia")
async def get_tendencia_diaria(
    unidad_negocio_nombre: Optional[str] = Query(default=None),
    dias: int = Query(default=30, ge=1, le=365),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Tendencia diaria de ventas.
    Fuente: dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
    """
    _require_permission(current_user)
    
    params: Dict[str, Any] = {"dias": dias}
    where = [f"fecha_operacion >= DATEADD(DAY, -%(dias)s, GETDATE())"]
    
    if unidad_negocio_nombre:
        where.append("unidad_negocio_nombre = %(unidad)s")
        params["unidad"] = unidad_negocio_nombre

    sql = f"""
    SELECT
        fecha_operacion,
        SUM(ventas_total) AS ventas_total,
        SUM(tickets_total) AS tickets_total,
        SUM(pax_total) AS pax_total,
        CASE WHEN SUM(tickets_total) > 0
             THEN SUM(ventas_total) / SUM(tickets_total) ELSE 0 END AS ticket_promedio
    FROM dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
    WHERE {' AND '.join(where)}
    GROUP BY fecha_operacion
    ORDER BY fecha_operacion;
    """
    return {"source": "Comercial_Inteligencia_VW_KPIsEjecutivos", "data": _query(sql, params)}


@router.get("/kpis-por-unidad")
async def get_kpis_por_unidad(
    fecha_inicio: Optional[date] = Query(default=None),
    fecha_fin: Optional[date] = Query(default=None),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    KPIs desglosados por unidad de negocio.
    Fuente: dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
    """
    _require_permission(current_user)
    
    fecha_inicio = fecha_inicio or (date.today() - timedelta(days=30))
    fecha_fin = fecha_fin or date.today()
    
    params: Dict[str, Any] = {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin}

    sql = """
    SELECT
        unidad_negocio_nombre,
        unidad_negocio_id,
        sistema_origen,
        SUM(ventas_total) AS ventas_total,
        SUM(ventas_sin_propina) AS ventas_sin_propina,
        SUM(propinas_total) AS propinas_total,
        SUM(tickets_total) AS tickets_total,
        SUM(pax_total) AS pax_total,
        CASE WHEN SUM(tickets_total) > 0
             THEN SUM(ventas_sin_propina) / SUM(tickets_total) ELSE 0 END AS ticket_promedio,
        MAX(fecha_sincronizacion) AS ultima_sincronizacion
    FROM dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
    WHERE fecha_operacion >= %(fecha_inicio)s AND fecha_operacion <= %(fecha_fin)s
    GROUP BY unidad_negocio_nombre, unidad_negocio_id, sistema_origen
    ORDER BY ventas_total DESC;
    """
    return {"source": "Comercial_Inteligencia_VW_KPIsEjecutivos", "data": _query(sql, params)}
