"""
MÓDULO: Inteligencia Comercial IA - EDARSAHUB
=============================================
Endpoints para el Portal de Inteligencia Comercial.

Fuentes de datos:
- KPIs Dashboard: vw_Comercial_KPIs_Diarios_v2_Runtime (pre-calculada)
- Ventas/Productos: Sync_Sales + Products (JOIN)
- PAX/Demográficos: Sync_PAX_Detalle
- Vista consolidada: View_Inteligencia_Comercial

Unidades de Negocio válidas:
- 130MID (130° MERIDA)
- 130QRO (130° QUERETARO)
- CIENFUEGOS
- ESTELAR (LA ESTELAR)
- ORIGEN
"""

import logging
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException
import pymssql
import os
from core.config.edarsahub_config import get_edarsahub_sql_config
from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
from core.sql_first.db import get_sql_connection
_edarsa_cfg = get_edarsahub_sql_config()


logger = logging.getLogger(__name__)

# ============================================================
# P1 - Helpers centralizados de unidades (refactorizado 2026-06-05)
# Regla: No usar nombres/códigos hardcodeados como llave operativa.
# Unidades se resuelven desde SQL mediante UnidadesService.
# ============================================================

def _pic_unidades_activas():
    """Obtiene todas las unidades activas desde SQL."""
    return UnidadesService.get_all()

def _pic_codigos_activos():
    """Obtiene lista de códigos canónicos activos."""
    return UnidadesService.get_codigos()

def _pic_codigo_to_nombre(codigo):
    """Resuelve código a nombre display."""
    return UnidadesService.get_nombre(codigo)

def _pic_mapeo_codigo_nombre():
    """Obtiene diccionario codigo -> nombre para display."""
    return UnidadesService.get_mapeo_codigo_nombre()



# ============================================================
# P2-02 - Runtime filters centralizados
# ============================================================

def _resolver_unidad_pk_runtime(valor):
    """Resolver PK usando servicios centralizados"""
    try:
        from core.corporate_filters.service import CorporateFilterService
        return CorporateFilterService.resolver_unidad(valor).get("pk")
    except Exception:
        try:
            from core.unidades_service import UnidadesService
            return UnidadesService.resolver_pk(valor)
        except Exception:
            return None

def _resolver_unidad_codigo_runtime(valor):
    """Resolver código usando servicios centralizados"""
    try:
        from core.corporate_filters.service import CorporateFilterService
        return CorporateFilterService.resolver_unidad(valor).get("codigo")
    except Exception:
        try:
            from core.unidades_service import UnidadesService
            return UnidadesService.resolver_codigo(valor)
        except Exception:
            return None



router = APIRouter(prefix="/inteligencia", tags=["Inteligencia Comercial"])

# ============================================================================
# CONFIGURACIÓN DE CONEXIÓN A EDARSAHUB
# ============================================================================
EDARSAHUB_CONFIG = {
    "host": _edarsa_cfg.host,
    "port": _edarsa_cfg.port,
    "database": _edarsa_cfg.database,
    "user": _edarsa_cfg.user,
    "password": _edarsa_cfg.password,
}

# ============================================================================
# MAPEO DE UNIDADES DE NEGOCIO - REFACTORIZADO P1 (2026-06-05)
# Ahora se construye dinámicamente desde UnidadesService
# ============================================================================

def _build_unidades_validas():
    """Construye mapeo de aliases a nombres desde SQL."""
    mapeo = {"todas": None}
    for u in UnidadesService.get_all():
        codigo = u.get("codigo", "").lower()
        nombre = u.get("nombre", "")
        if codigo and nombre:
            mapeo[codigo] = nombre
            # Agregar variantes comunes
            mapeo[codigo.replace("°", "")] = nombre
            nombre_lower = nombre.lower().replace("°", "").replace(" ", "")
            mapeo[nombre_lower] = nombre
    return mapeo

def _build_unidad_to_sucursal():
    """Construye mapeo nombre -> sucursal (identidad para compatibilidad)."""
    return {u.get("nombre"): u.get("nombre") for u in UnidadesService.get_all() if u.get("nombre")}

# Cache dinámico (se recarga con UnidadesService.get_all que tiene TTL)
UNIDADES_VALIDAS = _build_unidades_validas()
UNIDAD_TO_SUCURSAL = _build_unidad_to_sucursal()


def normalizar_unidad(unidad: str) -> Optional[str]:
    """Normaliza el código de unidad al nombre real en BD."""
    if not unidad:
        return None
    # Primero intentar resolver via UnidadesService
    nombre = UnidadesService.get_nombre(unidad)
    if nombre:
        return nombre
    # Fallback a mapeo local
    key = unidad.lower().replace("°", "").replace(" ", "")
    return UNIDADES_VALIDAS.get(key)


def get_connection():
    """Obtiene conexión a EDARSAHUB SQL Server."""
    return get_sql_connection()


def execute_query(sql: str, params: tuple = None) -> List[Dict]:
    """Ejecuta query y retorna lista de diccionarios."""
    try:
        conn = get_connection()
        cursor = conn.cursor(as_dict=True)
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except Exception as e:
        logger.error(f"[INTELIGENCIA] Error SQL: {e}")
        return []


# ============================================================================
# ENDPOINT: Dashboard Principal (KPIs)
# Fuente: vw_Comercial_KPIs_Diarios_v2_Runtime
# ============================================================================
_MESES_ES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def _ultimo_dia_con_datos(unidad_db: Optional[str]) -> date:
    """Ancla NO-LIVE: último día con datos en la vista (evita rangos vacíos
    al seleccionar 'Día' cuando hoy aún no tiene ventas)."""
    where = "ventas_sin_propina > 0"
    if unidad_db:
        where += f" AND unidad_negocio_nombre = '{unidad_db}'"
    rows = execute_query(
        f"SELECT MAX(fecha_operacion) AS m FROM vw_Comercial_KPIs_Diarios_v2_Runtime WHERE {where}"
    )
    m = rows[0].get("m") if rows else None
    if isinstance(m, datetime):
        return m.date()
    if isinstance(m, date):
        return m
    if isinstance(m, str) and len(m) >= 10:
        try:
            return datetime.strptime(m[:10], "%Y-%m-%d").date()
        except ValueError:
            pass
    return date.today()


def _periodo_rango(periodo: str, anchor: date):
    """Resuelve (inicio, fin, prev_inicio, prev_fin, etiqueta) para el periodo
    seleccionado, anclado al último día con datos. 'prev_*' = periodo anterior
    equivalente para calcular tendencias reales."""
    import calendar
    p = (periodo or "mes").strip().lower()
    if p in ("año", "ano", "anio", "anual", "year"):
        ini, fin = date(anchor.year, 1, 1), anchor
        d_prev = 28 if (anchor.month == 2 and anchor.day == 29) else anchor.day
        prev_ini = date(anchor.year - 1, 1, 1)
        prev_fin = date(anchor.year - 1, anchor.month, d_prev)
        label = f"Año {anchor.year}"
    elif p in ("semana", "week"):
        ini, fin = anchor - timedelta(days=6), anchor
        prev_ini, prev_fin = anchor - timedelta(days=13), anchor - timedelta(days=7)
        label = f"Semana {ini.day} {_MESES_ES[ini.month]} – {fin.day} {_MESES_ES[fin.month]} {fin.year}"
    elif p in ("dia", "día", "day"):
        ini = fin = anchor
        prev_ini = prev_fin = anchor - timedelta(days=1)
        label = f"{anchor.day} de {_MESES_ES[anchor.month]} {anchor.year}"
    else:  # mes
        ini, fin = date(anchor.year, anchor.month, 1), anchor
        py, pm = (anchor.year - 1, 12) if anchor.month == 1 else (anchor.year, anchor.month - 1)
        last_prev = calendar.monthrange(py, pm)[1]
        prev_ini = date(py, pm, 1)
        prev_fin = date(py, pm, min(anchor.day, last_prev))
        label = f"{_MESES_ES[anchor.month]} {anchor.year}"
    return ini, fin, prev_ini, prev_fin, label


# ============================================================================
# BLOQUES REALES (NO-LIVE) desde Comercial_Inteligencia_VentasDetalleProducto
# Reemplazan los antiguos bloques con porcentajes/productos HARDCODEADOS.
# Medida de ventas: importe_neto (neto de línea). Donde NO hay detalle real
# (p.ej. casa NULL aún no sincronizada) se devuelve VACÍO para que el frontend
# muestre SIN_DATOS_SYNC; nunca se inventa.
# ============================================================================
_DETALLE_TABLA = "Comercial_Inteligencia_VentasDetalleProducto"


def _detalle_where(unidad_db: Optional[str], fecha_inicio: str, fecha_fin: str) -> str:
    parts = ["ISNULL(activo,1)=1",
             f"fecha_operacion BETWEEN '{fecha_inicio}' AND '{fecha_fin}'"]
    if unidad_db:
        parts.append(f"unidad_negocio_nombre = '{unidad_db}'")
    return " AND ".join(parts)


def _real_detalle_total(unidad_db, fecha_inicio, fecha_fin) -> float:
    rows = execute_query(
        f"SELECT SUM(importe_neto) AS t FROM {_DETALLE_TABLA} "
        f"WHERE {_detalle_where(unidad_db, fecha_inicio, fecha_fin)}")
    return float(rows[0]["t"] or 0) if rows and rows[0].get("t") is not None else 0.0


def _real_top_productos(unidad_db, fecha_inicio, fecha_fin, limit=7):
    sql = f"""
        SELECT TOP {int(limit)}
               producto_nombre AS nombre,
               MAX(producto_codigo_fuente) AS codigo,
               MAX(familia_nombre) AS familia,
               MAX(subfamilia_nombre) AS subfamilia,
               MAX(ISNULL(casa, '')) AS casa,
               MAX(porcentaje_alcohol) AS alcohol,
               SUM(cantidad) AS cantidad,
               SUM(importe_neto) AS ventas,
               SUM(propina) AS propina
        FROM {_DETALLE_TABLA}
        WHERE {_detalle_where(unidad_db, fecha_inicio, fecha_fin)}
          AND producto_nombre IS NOT NULL AND producto_nombre <> ''
        GROUP BY producto_nombre
        ORDER BY SUM(importe_neto) DESC
    """
    out = []
    for i, r in enumerate(execute_query(sql)):
        out.append({
            "id": i + 1,
            "producto": r["nombre"],
            "nombre": r["nombre"],
            "codigo": r.get("codigo") or "",
            "familia": (r.get("familia") or "").strip(),
            "subfamilia": (r.get("subfamilia") or "").strip(),
            "casa": (r.get("casa") or "").strip(),
            "alcohol": round(float(r.get("alcohol") or 0), 1),
            "cantidad": round(float(r.get("cantidad") or 0), 2),
            "ventas": round(float(r.get("ventas") or 0), 2),
            "propina": round(float(r.get("propina") or 0), 2),
        })
    return out


def _real_familias(unidad_db, fecha_inicio, fecha_fin, total_ventas=None, limit=12):
    sql = f"""
        SELECT TOP {int(limit)} familia_nombre AS familia, SUM(importe_neto) AS ventas
        FROM {_DETALLE_TABLA}
        WHERE {_detalle_where(unidad_db, fecha_inicio, fecha_fin)}
          AND familia_nombre IS NOT NULL AND familia_nombre <> ''
        GROUP BY familia_nombre
        ORDER BY SUM(importe_neto) DESC
    """
    rows = execute_query(sql)
    base = total_ventas if total_ventas else (sum(float(r["ventas"] or 0) for r in rows) or 1)
    return [{"familia": (r["familia"] or "").strip(),
             "ventas": round(float(r["ventas"] or 0), 2),
             "participacion": round(float(r["ventas"] or 0) / base * 100, 2)} for r in rows]


def _real_familias_nested(unidad_db, fecha_inicio, fecha_fin, limit_fam=20):
    """Familias con sus subfamilias (datos reales). Para la pantalla Familia/Subfamilia."""
    sql = f"""
        SELECT familia_nombre AS familia,
               ISNULL(NULLIF(LTRIM(RTRIM(subfamilia_nombre)), ''), '(Sin subfamilia)') AS subfamilia,
               SUM(importe_neto) AS ventas, SUM(cantidad) AS cantidad
        FROM {_DETALLE_TABLA}
        WHERE {_detalle_where(unidad_db, fecha_inicio, fecha_fin)}
          AND familia_nombre IS NOT NULL AND familia_nombre <> ''
        GROUP BY familia_nombre,
                 ISNULL(NULLIF(LTRIM(RTRIM(subfamilia_nombre)), ''), '(Sin subfamilia)')
    """
    fam_map = {}
    for r in execute_query(sql):
        fam = (r["familia"] or "").strip()
        v = float(r["ventas"] or 0)
        c = float(r["cantidad"] or 0)
        d = fam_map.setdefault(fam, {"familia": fam, "ventas": 0.0, "cantidad": 0.0, "subs": []})
        d["ventas"] += v
        d["cantidad"] += c
        d["subs"].append({"nombre": r["subfamilia"], "ventas": round(v, 2), "cantidad": round(c, 2)})
    familias = sorted(fam_map.values(), key=lambda x: x["ventas"], reverse=True)[:limit_fam]
    total = sum(f["ventas"] for f in familias) or 1
    out = []
    for f in familias:
        fv = f["ventas"] or 1
        subs = sorted(f["subs"], key=lambda s: s["ventas"], reverse=True)
        for s in subs:
            s["porcentaje"] = round(s["ventas"] / fv * 100, 1)
        out.append({
            "familia": f["familia"],
            "ventas": round(f["ventas"], 2),
            "cantidad": round(f["cantidad"], 2),
            "porcentaje": round(f["ventas"] / total * 100, 1),
            "subfamilias": subs,
        })
    return out


def _real_casas(unidad_db, fecha_inicio, fecha_fin, total_ventas=None, limit=12):
    # casa puede venir NULL (aún no sincronizada): se EXCLUYE → si no hay ninguna,
    # el bloque queda vacío y el frontend muestra SIN_DATOS_SYNC.
    sql = f"""
        SELECT TOP {int(limit)} casa, SUM(importe_neto) AS ventas
        FROM {_DETALLE_TABLA}
        WHERE {_detalle_where(unidad_db, fecha_inicio, fecha_fin)}
          AND casa IS NOT NULL AND LTRIM(RTRIM(casa)) <> ''
        GROUP BY casa
        ORDER BY SUM(importe_neto) DESC
    """
    rows = execute_query(sql)
    base = total_ventas if total_ventas else (sum(float(r["ventas"] or 0) for r in rows) or 1)
    return [{"casa": r["casa"].strip(),
             "ventas": round(float(r["ventas"] or 0), 2),
             "participacion": round(float(r["ventas"] or 0) / base * 100, 2)} for r in rows]


def _real_horario(unidad_db, fecha_inicio, fecha_fin):
    # Agrega a nivel ticket (pax/cheques correctos) y clasifica por hora de apertura.
    sql = f"""
        WITH tk AS (
            SELECT unidad_negocio_nombre, fecha_operacion, numero_ticket,
                   MIN(fecha_hora) AS fh, MAX(pax) AS pax,
                   SUM(importe_neto) AS ventas, SUM(propina) AS propinas
            FROM {_DETALLE_TABLA}
            WHERE {_detalle_where(unidad_db, fecha_inicio, fecha_fin)}
            GROUP BY unidad_negocio_nombre, fecha_operacion, numero_ticket
        )
        SELECT CASE WHEN DATEPART(hour, fh) BETWEEN 7 AND 12 THEN 'Desayuno'
                    WHEN DATEPART(hour, fh) BETWEEN 13 AND 18 THEN 'Comida'
                    ELSE 'Cena' END AS horario,
               SUM(ventas) AS ventas, SUM(pax) AS pax,
               COUNT(*) AS cheques, SUM(propinas) AS propinas
        FROM tk
        GROUP BY CASE WHEN DATEPART(hour, fh) BETWEEN 7 AND 12 THEN 'Desayuno'
                      WHEN DATEPART(hour, fh) BETWEEN 13 AND 18 THEN 'Comida'
                      ELSE 'Cena' END
    """
    orden = {"Desayuno": 0, "Comida": 1, "Cena": 2}
    out = []
    for r in execute_query(sql):
        ventas = round(float(r["ventas"] or 0), 2)
        cheques = int(r["cheques"] or 0)
        out.append({"horario": r["horario"], "ventas": ventas,
                    "pax": int(r["pax"] or 0), "cheques": cheques,
                    "propinas": round(float(r["propinas"] or 0), 2),
                    "ticket_promedio": round(ventas / cheques, 2) if cheques else 0})
    out.sort(key=lambda x: orden.get(x["horario"], 9))
    return out



@router.get("/dashboard")
async def get_dashboard_data(
    unidad: Optional[str] = Query(None, description="Unidad de negocio (130MID, CIENFUEGOS, etc.)"),
    periodo: Optional[str] = Query(None, description="Periodo: dia | semana | mes | anio/año"),
    fecha_inicio: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)")
):
    """
    Dashboard principal con KPIs consolidados.
    Fuente: vw_Comercial_KPIs_Diarios_v2_Runtime
    """
    unidad_db = normalizar_unidad(unidad) if unidad and unidad.lower() != "todas" else None

    periodo_label = None
    prev_inicio = prev_fin = None
    # Si se especifica periodo y NO se pasaron fechas explícitas, se resuelve el
    # rango anclado al último día con datos (NO-LIVE, evita rangos vacíos).
    if periodo and not (fecha_inicio and fecha_fin):
        anchor = _ultimo_dia_con_datos(unidad_db)
        ini, fin, prev_inicio, prev_fin, periodo_label = _periodo_rango(periodo, anchor)
        fecha_inicio = ini.strftime("%Y-%m-%d")
        fecha_fin = fin.strftime("%Y-%m-%d")

    # Defaults para fechas (compatibilidad: últimos 30 días)
    if not fecha_inicio:
        fecha_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not fecha_fin:
        fecha_fin = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # WHERE dinámico
        where_parts = [f"fecha_operacion BETWEEN '{fecha_inicio}' AND '{fecha_fin}'"]
        if unidad_db:
            where_parts.append(f"unidad_negocio_nombre = '{unidad_db}'")
        where_sql = " AND ".join(where_parts)
        
        # Query KPIs principales
        kpis_sql = f"""
            SELECT 
                COALESCE(SUM(ventas_sin_propina), 0) AS ventas_totales,
                COALESCE(SUM(pax_total), 0) AS pax_total,
                COALESCE(SUM(tickets_total), 0) AS cheques_total,
                COALESCE(SUM(propinas_total), 0) AS propinas_total,
                CASE WHEN SUM(tickets_total) > 0 
                    THEN SUM(ventas_sin_propina) / SUM(tickets_total) 
                    ELSE 0 END AS cheque_promedio
            FROM vw_Comercial_KPIs_Diarios_v2_Runtime
            WHERE {where_sql}
        """
        kpis = execute_query(kpis_sql)
        kpi_data = kpis[0] if kpis else {}

        # ========== TENDENCIAS REALES vs periodo anterior equivalente ==========
        kpis_trends = {}
        if prev_inicio and prev_fin:
            prev_where = [f"fecha_operacion BETWEEN '{prev_inicio}' AND '{prev_fin}'"]
            if unidad_db:
                prev_where.append(f"unidad_negocio_nombre = '{unidad_db}'")
            prev_sql = f"""
                SELECT
                    COALESCE(SUM(ventas_sin_propina), 0) AS ventas_totales,
                    COALESCE(SUM(pax_total), 0) AS pax_total,
                    COALESCE(SUM(tickets_total), 0) AS cheques_total,
                    COALESCE(SUM(propinas_total), 0) AS propinas_total
                FROM vw_Comercial_KPIs_Diarios_v2_Runtime
                WHERE {' AND '.join(prev_where)}
            """
            prev_rows = execute_query(prev_sql)
            prev = prev_rows[0] if prev_rows else {}

            def _trend(cur, prv):
                try:
                    cur, prv = float(cur or 0), float(prv or 0)
                    if prv <= 0:
                        return None
                    return round((cur - prv) / prv * 100, 1)
                except Exception:
                    return None

            kpis_trends = {
                "ventas_totales": _trend(kpi_data.get("ventas_totales"), prev.get("ventas_totales")),
                "pax_total": _trend(kpi_data.get("pax_total"), prev.get("pax_total")),
                "cheques_total": _trend(kpi_data.get("cheques_total"), prev.get("cheques_total")),
                "propinas_total": _trend(kpi_data.get("propinas_total"), prev.get("propinas_total")),
            }
        
        # Query por unidad (si es consolidado)
        ventas_por_unidad = []
        if not unidad_db:
            unidad_sql = f"""
                SELECT 
                    unidad_negocio_nombre AS unidad,
                    SUM(ventas_sin_propina) AS ventas,
                    SUM(pax_total) AS pax_total,
                    SUM(tickets_total) AS tickets,
                    SUM(propinas_total) AS propinas
                FROM vw_Comercial_KPIs_Diarios_v2_Runtime
                WHERE {where_sql}
                GROUP BY unidad_negocio_nombre
                ORDER BY SUM(ventas_sin_propina) DESC
            """
            ventas_por_unidad = execute_query(unidad_sql)
        
        total_ventas = float(kpi_data.get("ventas_totales", 0)) or 1
        total_pax = int(kpi_data.get("pax_total", 0))
        total_tickets = int(kpi_data.get("cheques_total", 0))
        
        # ========== BLOQUES REALES (NO-LIVE) desde el detalle de ventas ==========
        # Antes: porcentajes/productos HARDCODEADOS. Ahora: agregados reales de
        # Comercial_Inteligencia_VentasDetalleProducto. Bloque vacío => SIN_DATOS_SYNC.
        det_total = _real_detalle_total(unidad_db, fecha_inicio, fecha_fin)
        ventas_horario = _real_horario(unidad_db, fecha_inicio, fecha_fin)
        top_productos = _real_top_productos(unidad_db, fecha_inicio, fecha_fin, limit=7)
        casas_distribuidoras = _real_casas(unidad_db, fecha_inicio, fecha_fin, total_ventas=det_total)
        ventas_familia = _real_familias(unidad_db, fecha_inicio, fecha_fin, total_ventas=det_total)
        
        # Construir respuesta
        response = {
            "success": True,
            "_source": "SQL_COMERCIAL_KPIS_DIARIOS_V2",
            "_blocks_source": _DETALLE_TABLA,
            "_detalle_total": round(det_total, 2),
            "_unidad": unidad_db or "TODAS",
            "timestamp": datetime.utcnow().isoformat(),
            "filtros": {
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "unidad": unidad_db or "TODAS",
                "periodo": periodo or None,
                "periodo_label": periodo_label
            },
            "kpis_trends": kpis_trends,
            "kpis": {
                "ventas_totales": round(float(kpi_data.get("ventas_totales", 0)), 2),
                "pax_total": int(kpi_data.get("pax_total", 0)),
                "cheques_total": int(kpi_data.get("cheques_total", 0)),
                "propinas_total": round(float(kpi_data.get("propinas_total", 0)), 2),
                "cheque_promedio": round(float(kpi_data.get("cheque_promedio", 0)), 2)
            },
            "ventas_por_unidad": [
                {
                    "unidad": u["unidad"],
                    "ventas": round(float(u["ventas"] or 0), 2),
                    "pax": int(u["pax_total"] or 0),
                    "tickets": int(u["tickets"] or 0),
                    "propinas": round(float(u["propinas"] or 0), 2),
                    "participacion": round((float(u["ventas"] or 0) / total_ventas) * 100, 2)
                }
                for u in ventas_por_unidad
            ] if ventas_por_unidad else [],
            "ventas_horario": ventas_horario,
            "top_productos": top_productos,
            "casas_distribuidoras": casas_distribuidoras,
            "ventas_familia": ventas_familia
        }
        
        logger.info(f"[INTELIGENCIA] Dashboard OK - {unidad_db or 'TODAS'} - ${total_ventas:,.2f}")
        return response
        
    except Exception as e:
        logger.error(f"[INTELIGENCIA] Error dashboard: {e}")
        return {
            "success": False,
            "_source": "ERROR",
            "_error": str(e),
            "kpis": {"ventas_totales": 0, "pax_total": 0, "cheques_total": 0, "propinas_total": 0, "cheque_promedio": 0}
        }


# ============================================================================
# ENDPOINT: Tendencia Diaria
# Fuente: vw_Comercial_KPIs_Diarios_v2_Runtime
# ============================================================================
@router.get("/dashboard/tendencia")
async def get_tendencia_diaria(
    unidad: Optional[str] = Query(None, description="Unidad de negocio"),
    fecha_inicio: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)")
):
    """
    Tendencia diaria de ventas para gráficos de línea.
    Fuente: vw_Comercial_KPIs_Diarios_v2_Runtime
    """
    unidad_db = normalizar_unidad(unidad) if unidad and unidad.lower() != "todas" else None
    
    if not fecha_inicio:
        fecha_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not fecha_fin:
        fecha_fin = datetime.now().strftime("%Y-%m-%d")
    
    try:
        where_parts = [f"fecha_operacion BETWEEN '{fecha_inicio}' AND '{fecha_fin}'"]
        if unidad_db:
            where_parts.append(f"unidad_negocio_nombre = '{unidad_db}'")
        where_sql = " AND ".join(where_parts)
        
        sql = f"""
            SELECT 
                fecha_operacion AS fecha,
                SUM(ventas_sin_propina) AS ventas,
                SUM(pax_total) AS pax_total,
                SUM(tickets_total) AS tickets,
                SUM(propinas_total) AS propinas,
                CASE WHEN SUM(tickets_total) > 0 
                    THEN SUM(ventas_sin_propina) / SUM(tickets_total) 
                    ELSE 0 END AS cheque_promedio
            FROM vw_Comercial_KPIs_Diarios_v2_Runtime
            WHERE {where_sql}
            GROUP BY fecha_operacion
            ORDER BY fecha_operacion ASC
        """
        
        datos = execute_query(sql)
        
        return {
            "success": True,
            "_source": "SQL_COMERCIAL_KPIS_DIARIOS_V2",
            "_unidad": unidad_db or "TODAS",
            "total_dias": len(datos),
            "datos_diarios": [
                {
                    "fecha": str(d["fecha"]),
                    "ventas": round(float(d["ventas"] or 0), 2),
                    "pax": int(d["pax"] or 0),
                    "tickets": int(d["tickets"] or 0),
                    "propinas": round(float(d["propinas"] or 0), 2),
                    "cheque_promedio": round(float(d["cheque_promedio"] or 0), 2)
                }
                for d in datos
            ]
        }
    except Exception as e:
        logger.error(f"[INTELIGENCIA] Error tendencia: {e}")
        return {"success": False, "_error": str(e), "datos_diarios": []}


# ============================================================================
# ENDPOINT: Ventas por Horario
# Fuente: Sync_PAX_Detalle o fallback proporcional
# ============================================================================
@router.get("/dashboard/horarios")
async def get_ventas_horario(
    unidad: Optional[str] = Query(None, description="Unidad de negocio"),
    fecha_inicio: Optional[str] = Query(None, description="Fecha inicio"),
    fecha_fin: Optional[str] = Query(None, description="Fecha fin")
):
    """
    Distribución de ventas por bloque horario.
    Si Sync_PAX_Detalle está vacío, calcula proporciones desde KPIs.
    """
    unidad_db = normalizar_unidad(unidad) if unidad and unidad.lower() != "todas" else None
    
    if not fecha_inicio:
        fecha_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not fecha_fin:
        fecha_fin = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # Primero intenta con Sync_PAX_Detalle
        where_parts = [f"FechaOperacion BETWEEN '{fecha_inicio}' AND '{fecha_fin}'"]
        if unidad_db:
            sucursal = UNIDAD_TO_SUCURSAL.get(unidad_db, unidad_db)
            where_parts.append(f"SucursalNombre = '{sucursal}'")
        where_sql = " AND ".join(where_parts)
        
        sql = f"""
            SELECT 
                CASE 
                    WHEN DATEPART(HOUR, FechaHora) BETWEEN 6 AND 11 THEN 'Desayuno'
                    WHEN DATEPART(HOUR, FechaHora) BETWEEN 12 AND 17 THEN 'Comida'
                    WHEN DATEPART(HOUR, FechaHora) BETWEEN 18 AND 23 THEN 'Cena'
                    ELSE 'Madrugada'
                END AS horario,
                SUM(NumeroComensales) AS pax,
                SUM(VentaCuenta) AS ventas,
                COUNT(*) AS mesas,
                AVG(ConsumoPromedioPAX) AS consumo_promedio
            FROM Sync_PAX_Detalle
            WHERE {where_sql}
            GROUP BY 
                CASE 
                    WHEN DATEPART(HOUR, FechaHora) BETWEEN 6 AND 11 THEN 'Desayuno'
                    WHEN DATEPART(HOUR, FechaHora) BETWEEN 12 AND 17 THEN 'Comida'
                    WHEN DATEPART(HOUR, FechaHora) BETWEEN 18 AND 23 THEN 'Cena'
                    ELSE 'Madrugada'
                END
        """
        
        datos = execute_query(sql)
        
        # Si hay datos reales, usarlos
        if datos and any(d.get("ventas") for d in datos):
            return {
                "success": True,
                "_source": "SQL_SYNC_PAX_DETALLE",
                "_unidad": unidad_db or "TODAS",
                "ventas_horario": [
                    {
                        "horario": d["horario"],
                        "ventas": round(float(d["ventas"] or 0), 2),
                        "pax": int(d["pax"] or 0),
                        "mesas": int(d["mesas"] or 0),
                        "consumo_promedio": round(float(d["consumo_promedio"] or 0), 2)
                    }
                    for d in datos
                ]
            }
        
        # FALLBACK: Calcular desde KPIs con proporciones estándar restaurante
        where_kpi = [f"fecha_operacion BETWEEN '{fecha_inicio}' AND '{fecha_fin}'"]
        if unidad_db:
            where_kpi.append(f"unidad_negocio_nombre = '{unidad_db}'")
        
        kpi_sql = f"""
            SELECT SUM(ventas_sin_propina) AS total, SUM(pax_total) AS pax_total, SUM(tickets_total) AS tickets
            FROM vw_Comercial_KPIs_Diarios_v2_Runtime
            WHERE {" AND ".join(where_kpi)}
        """
        kpis = execute_query(kpi_sql)
        total_ventas = float(kpis[0]["total"] or 0) if kpis else 0
        total_pax = int(kpis[0]["pax"] or 0) if kpis else 0
        total_tickets = int(kpis[0]["tickets"] or 0) if kpis else 0
        
        # Proporciones típicas de restaurante
        return {
            "success": True,
            "_source": "FALLBACK_PROPORCIONAL",
            "_unidad": unidad_db or "TODAS",
            "_nota": "Datos calculados proporcionalmente desde KPIs diarios",
            "ventas_horario": [
                {"horario": "Desayuno", "ventas": round(total_ventas * 0.20, 2), "pax": int(total_pax * 0.20), "mesas": int(total_tickets * 0.20)},
                {"horario": "Comida", "ventas": round(total_ventas * 0.50, 2), "pax": int(total_pax * 0.50), "mesas": int(total_tickets * 0.50)},
                {"horario": "Cena", "ventas": round(total_ventas * 0.30, 2), "pax": int(total_pax * 0.30), "mesas": int(total_tickets * 0.30)},
            ]
        }
    except Exception as e:
        logger.error(f"[INTELIGENCIA] Error horarios: {e}")
        return {"success": False, "_error": str(e), "ventas_horario": []}


# ============================================================================
# ENDPOINT: Análisis PAX (Demográficos)
# Fuente: Sync_PAX_Detalle
# ============================================================================
@router.get("/dashboard/pax")
async def get_analisis_pax(
    unidad: Optional[str] = Query(None, description="Unidad de negocio"),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None)
):
    """
    Análisis detallado de PAX/Comensales.
    Fuente: Sync_PAX_Detalle
    """
    unidad_db = normalizar_unidad(unidad) if unidad and unidad.lower() != "todas" else None
    
    if not fecha_inicio:
        fecha_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not fecha_fin:
        fecha_fin = datetime.now().strftime("%Y-%m-%d")
    
    try:
        where_parts = [f"FechaOperacion BETWEEN '{fecha_inicio}' AND '{fecha_fin}'"]
        if unidad_db:
            sucursal = UNIDAD_TO_SUCURSAL.get(unidad_db, unidad_db)
            where_parts.append(f"SucursalNombre = '{sucursal}'")
        where_sql = " AND ".join(where_parts)
        
        # Resumen general
        resumen_sql = f"""
            SELECT 
                SUM(NumeroComensales) AS pax_total,
                SUM(VentaCuenta) AS ventas_total,
                COUNT(*) AS total_mesas,
                AVG(ConsumoPromedioPAX) AS consumo_promedio,
                AVG(TiempoMesa) AS tiempo_promedio_mesa
            FROM Sync_PAX_Detalle
            WHERE {where_sql}
        """
        resumen = execute_query(resumen_sql)
        resumen_data = resumen[0] if resumen else {}
        
        # Por turno
        turno_sql = f"""
            SELECT 
                Turno,
                SUM(NumeroComensales) AS pax,
                SUM(VentaCuenta) AS ventas,
                COUNT(*) AS mesas,
                AVG(ConsumoPromedioPAX) AS consumo_promedio
            FROM Sync_PAX_Detalle
            WHERE {where_sql} AND Turno IS NOT NULL
            GROUP BY Turno
            ORDER BY SUM(VentaCuenta) DESC
        """
        por_turno = execute_query(turno_sql)
        
        # Por día de semana
        dia_sql = f"""
            SELECT 
                DiaSemana,
                SUM(NumeroComensales) AS pax,
                SUM(VentaCuenta) AS ventas,
                COUNT(*) AS mesas
            FROM Sync_PAX_Detalle
            WHERE {where_sql} AND DiaSemana IS NOT NULL
            GROUP BY DiaSemana
            ORDER BY SUM(VentaCuenta) DESC
        """
        por_dia = execute_query(dia_sql)
        
        # Top meseros
        mesero_sql = f"""
            SELECT TOP 10
                MeseroNombre,
                SUM(NumeroComensales) AS pax_atendidos,
                SUM(VentaCuenta) AS ventas,
                COUNT(*) AS mesas_atendidas,
                AVG(ConsumoPromedioPAX) AS ticket_promedio
            FROM Sync_PAX_Detalle
            WHERE {where_sql} AND MeseroNombre IS NOT NULL
            GROUP BY MeseroNombre
            ORDER BY SUM(VentaCuenta) DESC
        """
        top_meseros = execute_query(mesero_sql)
        
        return {
            "success": True,
            "_source": "SQL_SYNC_PAX_DETALLE",
            "_unidad": unidad_db or "TODAS",
            "resumen": {
                "pax_total": int(resumen_data.get("pax_total", 0) or 0),
                "ventas_total": round(float(resumen_data.get("ventas_total", 0) or 0), 2),
                "total_mesas": int(resumen_data.get("total_mesas", 0) or 0),
                "consumo_promedio": round(float(resumen_data.get("consumo_promedio", 0) or 0), 2),
                "tiempo_promedio_mesa": int(resumen_data.get("tiempo_promedio_mesa", 0) or 0)
            },
            "por_turno": [
                {
                    "turno": t["Turno"],
                    "pax": int(t["pax"] or 0),
                    "ventas": round(float(t["ventas"] or 0), 2),
                    "mesas": int(t["mesas"] or 0)
                }
                for t in por_turno
            ],
            "por_dia_semana": [
                {
                    "dia": d["DiaSemana"],
                    "pax": int(d["pax"] or 0),
                    "ventas": round(float(d["ventas"] or 0), 2),
                    "mesas": int(d["mesas"] or 0)
                }
                for d in por_dia
            ],
            "top_meseros": [
                {
                    "mesero": m["MeseroNombre"],
                    "pax_atendidos": int(m["pax_atendidos"] or 0),
                    "ventas": round(float(m["ventas"] or 0), 2),
                    "mesas": int(m["mesas_atendidas"] or 0),
                    "ticket_promedio": round(float(m["ticket_promedio"] or 0), 2)
                }
                for m in top_meseros
            ]
        }
    except Exception as e:
        logger.error(f"[INTELIGENCIA] Error PAX: {e}")
        return {"success": False, "_error": str(e)}


# ============================================================================
# ENDPOINT: Top Productos
# Fuente: View_Inteligencia_Comercial (Sync_Sales + Products)
# ============================================================================
@router.get("/productos")
async def get_top_productos(
    unidad: Optional[str] = Query(None),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Top productos vendidos (NO-LIVE, datos reales por línea).
    Fuente: Comercial_Inteligencia_VentasDetalleProducto.
    """
    unidad_db = normalizar_unidad(unidad) if unidad and unidad.lower() != "todas" else None

    if not fecha_inicio:
        fecha_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not fecha_fin:
        fecha_fin = datetime.now().strftime("%Y-%m-%d")

    try:
        productos = _real_top_productos(unidad_db, fecha_inicio, fecha_fin, limit=limit)
        return {
            "success": True,
            "_source": _DETALLE_TABLA,
            "_unidad": unidad_db or "TODAS",
            "total": len(productos),
            "productos": productos,
        }
    except Exception as e:
        logger.error(f"[INTELIGENCIA] Error productos: {e}")
        return {"success": False, "_error": str(e), "productos": []}


# ============================================================================
# ENDPOINT: Ventas por Familia
# Fuente: Sync_Productos con fallback proporcional
# ============================================================================
@router.get("/familias")
async def get_ventas_familia(
    unidad: Optional[str] = Query(None),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None)
):
    """
    Ventas agrupadas por familia de producto (NO-LIVE, datos reales).
    Fuente: Comercial_Inteligencia_VentasDetalleProducto.
    """
    unidad_db = normalizar_unidad(unidad) if unidad and unidad.lower() != "todas" else None

    if not fecha_inicio:
        fecha_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not fecha_fin:
        fecha_fin = datetime.now().strftime("%Y-%m-%d")

    try:
        det_total = _real_detalle_total(unidad_db, fecha_inicio, fecha_fin)
        familias = _real_familias_nested(unidad_db, fecha_inicio, fecha_fin)
        return {
            "success": True,
            "_source": _DETALLE_TABLA,
            "_unidad": unidad_db or "TODAS",
            "_detalle_total": round(det_total, 2),
            "ventas_familia": familias,
        }
    except Exception as e:
        logger.error(f"[INTELIGENCIA] Error familias: {e}")
        return {"success": False, "_error": str(e), "ventas_familia": []}


# ============================================================================
# ENDPOINT: Ventas por Casa/Distribuidor
# Fuente: Products con fallback proporcional
# ============================================================================
@router.get("/casas")
async def get_ventas_casas(
    unidad: Optional[str] = Query(None),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None)
):
    """
    Ventas agrupadas por casa distribuidora (NO-LIVE, datos reales).
    Fuente: Comercial_Inteligencia_VentasDetalleProducto. Si la casa no está
    sincronizada (NULL) el bloque queda vacío → el frontend muestra SIN_DATOS_SYNC.
    """
    unidad_db = normalizar_unidad(unidad) if unidad and unidad.lower() != "todas" else None

    if not fecha_inicio:
        fecha_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not fecha_fin:
        fecha_fin = datetime.now().strftime("%Y-%m-%d")

    try:
        det_total = _real_detalle_total(unidad_db, fecha_inicio, fecha_fin)
        casas = _real_casas(unidad_db, fecha_inicio, fecha_fin, total_ventas=det_total)
        return {
            "success": True,
            "_source": _DETALLE_TABLA,
            "_unidad": unidad_db or "TODAS",
            "casas_distribuidoras": casas,
        }
    except Exception as e:
        logger.error(f"[INTELIGENCIA] Error casas: {e}")
        return {"success": False, "_error": str(e), "casas_distribuidoras": []}


# ============================================================================
# ENDPOINT: Unidades de Negocio disponibles
# ============================================================================
@router.get("/unidades")
async def get_unidades_negocio():
    """Lista de unidades de negocio activas."""
    try:
        # P1 REFACTORIZADO: Usar UnidadesService (SQL-First)
        unidades = _pic_unidades_activas()
        
        return {
            "success": True,
            "unidades": [
                {
                    "codigo": u.get("codigo"),
                    "nombre": u.get("nombre"),
                    "sistema": u.get("system_type", "N/A")
                }
                for u in unidades
            ]
        }
    except Exception as e:
        logger.error(f"[INTELIGENCIA] Error unidades: {e}")
        # Fallback también usa UnidadesService (cache interno)
        try:
            from core.unidades_service import UnidadesService
            unidades = UnidadesService.get_all()
            return {
                "success": True,
                "_source": "FALLBACK_UNIDADES_SERVICE",
                "unidades": [
                    {"codigo": u.get("codigo"), "nombre": u.get("nombre"), "sistema": u.get("system_type", "N/A")}
                    for u in unidades
                ]
            }
        except:
            return {"success": False, "unidades": [], "error": str(e)}


# ============================================================================
# ENDPOINT: Health Check
# ============================================================================
@router.get("/health")
async def health_check():
    """Verifica conectividad con EDARSAHUB."""
    try:
        result = execute_query("SELECT 1 AS ok")
        return {
            "status": "ok",
            "database": "EDARSAHUB",
            "connected": bool(result)
        }
    except Exception as e:
        return {
            "status": "error",
            "database": "EDARSAHUB",
            "error": str(e)
        }
