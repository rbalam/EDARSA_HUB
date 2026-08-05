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
from fastapi import APIRouter, Query, HTTPException, Depends, Request
from pydantic import BaseModel
import pymssql
import os
from core.config.edarsahub_config import get_edarsahub_sql_config
from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
from core.sql_first.db import get_sql_connection
from core.kpis_canonicos.service import KPIsCanonicosService
from core.rbac import require_explicit_permission_dual
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


class InteligenciaSQLSourceError(HTTPException):
    """Una falla SQL no equivale a una consulta vacía."""

    def __init__(self):
        super().__init__(
            status_code=503,
            detail={
                "code": "INTELIGENCIA_SQL_UNAVAILABLE",
                "message": (
                    "La fuente SQL de Inteligencia "
                    "Comercial no está disponible."
                ),
            },
        )


class InteligenciaNoDataError(HTTPException):
    """No existe fecha_operacion sincronizada."""

    def __init__(self, unidad=None):
        super().__init__(
            status_code=503,
            detail={
                "code": "INTELIGENCIA_NO_SYNC_DATA",
                "message": (
                    "No existe fecha_operacion "
                    "sincronizada para el alcance."
                ),
                "unidad": (
                    str(unidad)
                    if unidad
                    else None
                ),
            },
        )


def execute_query(
    sql: str,
    params: tuple = None,
) -> List[Dict]:
    """Distingue cero filas de una falla SQL."""
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(as_dict=True)

        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)

        return list(cursor.fetchall())

    except HTTPException:
        raise

    except Exception as exc:
        logger.error(
            "[INTELIGENCIA] Falla SQL controlada type=%s",
            type(exc).__name__,
        )
        raise InteligenciaSQLSourceError() from exc

    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass

        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def execute_write(sql: str, params: tuple = None) -> int:
    """Ejecuta INSERT/UPDATE/DELETE con commit. Retorna filas afectadas."""
    conn = get_connection()
    cursor = conn.cursor()
    if params:
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)
    affected = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return affected


async def require_admin(
    current_user: Dict[str, Any] = Depends(
        require_explicit_permission_dual(
            "INTELIGENCIA_COMERCIAL_GESTIONAR"
        )
    ),
) -> Dict[str, Any]:
    """Exige permiso efectivo SQL para gestionar catálogos."""
    return current_user


# ============================================================================
# ENDPOINT: Dashboard Principal (KPIs)
# Fuente: vw_Comercial_KPIs_Diarios_v2_Runtime
# ============================================================================
_MESES_ES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def _ultimo_dia_con_datos(unidad_db: Optional[str]) -> date:
    """Ancla NO-LIVE: último día con DETALLE de ventas. Se usa el detalle
    (Comercial_Inteligencia_VentasDetalleProducto) y no la vista KPI porque las
    tarjetas (horario/productos/casas/familias) se nutren del detalle; anclando
    aquí se evita que 'Día' caiga en una fecha con KPI pero sin detalle (vacío)."""
    where = "ISNULL(activo,1)=1"
    params = ()
    unidad_codigo = _unidad_codigo_filtro(unidad_db)
    if unidad_codigo:
        where += " AND unidad_negocio_id = %s"
        params = (unidad_codigo,)
    rows = execute_query(
        f"SELECT MAX(fecha_operacion) AS m FROM Comercial_Inteligencia_VentasDetalleProducto WHERE {where}",
        params,
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
    raise InteligenciaNoDataError(unidad_db)



def _sql_literal(value):
    return str(value or "").replace("'", "''")


def _kpi_num(row, *keys, default=0):
    """Lee un valor numérico de un dict canónico aceptando alias legacy."""
    for k in keys:
        if isinstance(row, dict) and k in row and row.get(k) is not None:
            return row.get(k)
    return default


def _kpi_int(row, *keys):
    try:
        return int(_kpi_num(row, *keys, default=0) or 0)
    except Exception:
        return 0


def _kpi_float(row, *keys):
    try:
        return float(_kpi_num(row, *keys, default=0) or 0)
    except Exception:
        return 0.0


def _normalizar_resumen_kpi_portal(row):
    """Convierte KPIsCanonicosService al contrato legacy del portal.

    Estructura real:
    - row["metricas"] contiene KPIs canónicos y ratios.
    - row["atomos"] contiene agregados base.
    """
    row = row or {}
    metricas = row.get("metricas") if isinstance(row.get("metricas"), dict) else {}
    atomos = row.get("atomos") if isinstance(row.get("atomos"), dict) else {}

    base = {}
    base.update(atomos)
    base.update(metricas)
    base.update(row)

    return {
        "ventas_totales": round(_kpi_float(base, "ventas_total", "ventas", "ventas_totales"), 2),
        "pax_total": _kpi_int(base, "pax", "pax_total"),
        "cheques_total": _kpi_int(base, "cheques", "tickets", "tickets_total", "cheques_total"),
        "propinas_total": round(_kpi_float(base, "propinas", "propinas_total"), 2),
        "ticket_promedio": round(_kpi_float(base, "ticket_promedio", "cheque_promedio"), 2),
        "cheque_promedio": round(_kpi_float(base, "cheque_promedio", "ticket_promedio"), 2),
        "pax_promedio": round(_kpi_float(base, "pax_promedio", "consumo_promedio_pax"), 2),
    }


def _kpi_cero_portal():
    return {
        "ventas_totales": 0.0,
        "pax_total": 0,
        "cheques_total": 0,
        "propinas_total": 0.0,
        "ticket_promedio": 0.0,
        "cheque_promedio": 0.0,
        "pax_promedio": 0.0,
    }


def _unidad_pks_canonicas_portal(unidad_db=None):
    """Resuelve una unidad del portal a su PK mediante servicios canónicos."""
    if not unidad_db:
        return None

    unidad_pk = _resolver_unidad_pk_runtime(unidad_db)
    return [str(unidad_pk)] if unidad_pk else []


def _fecha_fin_exclusiva(fecha_fin):
    """Convierte fecha_fin inclusiva del endpoint a hasta exclusivo del servicio canónico."""
    if isinstance(fecha_fin, date):
        return (fecha_fin + timedelta(days=1)).strftime("%Y-%m-%d")
    return (datetime.strptime(str(fecha_fin)[:10], "%Y-%m-%d").date() + timedelta(days=1)).strftime("%Y-%m-%d")


def _desglose_periodo_canonico_portal(fecha_inicio, fecha_fin, unidad_db=None):
    """Contrato KPI único para acumulado cerrado, día actual y total informativo."""
    unidad_pks = _unidad_pks_canonicas_portal(unidad_db)
    if unidad_db and not unidad_pks:
        raise HTTPException(status_code=400, detail="Unidad de negocio inválida o inactiva.")
    return KPIsCanonicosService.resumen_periodo_desglosado(
        str(fecha_inicio)[:10],
        _fecha_fin_exclusiva(fecha_fin),
        unidad_pks,
    )


def _resumen_periodo_canonico_portal(fecha_inicio, fecha_fin, unidad_db=None):
    desglose = _desglose_periodo_canonico_portal(fecha_inicio, fecha_fin, unidad_db)
    return _normalizar_resumen_kpi_portal(desglose.get("acumulado_cerrado") or {})


def _ventas_por_unidad_desde_resumen(resumen):
    salida = []
    for item in (resumen or {}).get("por_unidad") or []:
        kpi = _normalizar_resumen_kpi_portal(item)
        salida.append({
            "unidad": item.get("unidad_nombre") or item.get("unidad_codigo"),
            "unidad_codigo": item.get("unidad_codigo"),
            "ventas": kpi["ventas_totales"],
            "pax_total": kpi["pax_total"],
            "tickets": kpi["cheques_total"],
            "propinas": kpi["propinas_total"],
            "ticket_promedio": kpi["ticket_promedio"],
            "cheque_promedio": kpi["cheque_promedio"],
            "pax_promedio": kpi["pax_promedio"],
        })
    salida.sort(key=lambda row: float(row.get("ventas") or 0), reverse=True)
    return salida

def _series_periodo_canonico_portal(fecha_inicio, fecha_fin, unidad_db=None):
    """Serie diaria desde KPIsCanonicosService."""
    hasta_excl = _fecha_fin_exclusiva(fecha_fin)

    try:
        rows = KPIsCanonicosService.series_periodo(
            desde=fecha_inicio,
            hasta=hasta_excl,
            nivel="dia",
            unidad_nombre=unidad_db
        )
    except TypeError:
        rows = KPIsCanonicosService.series_periodo(
            fecha_inicio,
            hasta_excl,
            "dia",
            unidad_db
        )

    out = []
    for r in rows or []:
        k = _normalizar_resumen_kpi_portal(r or {})
        out.append({
            "fecha": str(_kpi_num(
                r,
                "fecha",
                "fecha_operacion",
                "dia",
                "periodo",
                "bucket",
                "fecha_inicio",
                default=""
            )),
            "ventas": k["ventas_totales"],
            "pax": k["pax_total"],
            "tickets": k["cheques_total"],
            "propinas": k["propinas_total"],
            "cheque_promedio": k["cheque_promedio"],
        })
    return out


def _ventas_por_unidad_canonico_portal(fecha_inicio, fecha_fin):
    desglose = _desglose_periodo_canonico_portal(fecha_inicio, fecha_fin)
    return _ventas_por_unidad_desde_resumen(desglose.get("acumulado_cerrado") or {})

def _trend_pct(cur, prv):
    try:
        cur, prv = float(cur or 0), float(prv or 0)
        if prv <= 0:
            return None
        return round((cur - prv) / prv * 100, 1)
    except Exception:
        return None


def _ultimo_dia_con_kpis(unidad_db: Optional[str], periodo: Optional[str] = None) -> date:
    """Ancla canónica para KPI principal desde dbo.vw_Comercial_KPIs_Diarios_v2_Runtime."""
    where = "1=1"
    params = ()
    unidad_pk = _unidad_pk_filtro(unidad_db)
    if unidad_pk:
        where += " AND CONVERT(varchar(36), unidad_negocio_pk) = %s"
        params = (unidad_pk,)

    sql = f"""
        SELECT MAX(fecha_operacion) AS m
        FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime
        WHERE {where}
    """

    rows = execute_query(sql, params)
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

    return _ultimo_dia_con_datos(unidad_db)


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


def _get_franjas_canonicas():
    """Franjas horarias canónicas (Desayuno/Comida/Cena) LEÍDAS de
    Sistema_TurnosOperativosUnidad (NO-LIVE, sin hardcode). Una franja por
    turno_codigo, representativa entre unidades (las franjas son uniformes).
    Devuelve [] si no hay config (el caller usa un safety net)."""
    sql = """
        SELECT turno_codigo,
               MIN(turno_nombre) AS nombre,
               MIN(DATEPART(hour, hora_inicio)) AS h_ini,
               MAX(DATEPART(hour, hora_fin)) AS h_fin,
               MAX(DATEPART(minute, hora_fin)) AS m_fin,
               MIN(CONVERT(VARCHAR(5), hora_inicio, 108)) AS ini_str,
               MAX(CONVERT(VARCHAR(5), hora_fin, 108)) AS fin_str,
               MAX(CAST(cruza_medianoche AS INT)) AS cruza,
               MIN(orden) AS orden
        FROM Sistema_TurnosOperativosUnidad
        WHERE activo = 1 AND aplica_ventas_dia = 1
        GROUP BY turno_codigo
        ORDER BY MIN(orden)
    """
    try:
        franjas = []
        for r in execute_query(sql):
            franjas.append({
                "codigo": r["turno_codigo"],
                "nombre": r["nombre"],
                "h_ini": int(r["h_ini"]),
                "h_fin": int(r["h_fin"]),
                "m_fin": int(r["m_fin"] or 0),
                "ini_str": r["ini_str"],
                "fin_str": r["fin_str"],
                "cruza": bool(r["cruza"]),
                "orden": int(r["orden"] or 0),
            })
        return franjas
    except Exception as e:
        logger.error(f"[INTELIGENCIA] Error leyendo franjas canónicas: {e}")
        return []


def _label_rango_personalizado(fi, ff):
    """Etiqueta legible para un rango de fechas personalizado (sin periodo)."""
    try:
        d1 = datetime.strptime(fi, "%Y-%m-%d").date()
        d2 = datetime.strptime(ff, "%Y-%m-%d").date()
        if d1 == d2:
            return f"{d1.day} de {_MESES_ES[d1.month]} {d1.year}"
        return f"{d1.day} {_MESES_ES[d1.month]} – {d2.day} {_MESES_ES[d2.month]} {d2.year}"
    except Exception:
        return f"{fi} a {ff}"


# ============================================================================
# BLOQUES REALES (NO-LIVE) desde Comercial_Inteligencia_VentasDetalleProducto
# Reemplazan los antiguos bloques con porcentajes/productos HARDCODEADOS.
# Medida de ventas: importe_neto (neto de línea). Donde NO hay detalle real
# (p.ej. casa NULL aún no sincronizada) se devuelve VACÍO para que el frontend
# muestre SIN_DATOS_SYNC; nunca se inventa.
# ============================================================================
_DETALLE_TABLA = "Comercial_Inteligencia_VentasDetalleProducto"
_ENRIQ_TABLA = "Comercial_Productos_Enriquecidos"   # casa/distribuidor, alcohol (NO-LIVE)
_SYNC_PROD = "Sync_Productos"                        # clasificación macro canónica (CategoriaNombre)
_CLAS_TABLA = "Comercial_ClasificacionesProducto"    # catálogo controlado de clasificación comercial


def _unidad_pk_filtro(unidad_db: Optional[str]) -> Optional[str]:
    if not unidad_db:
        return None
    unidad_pk = _resolver_unidad_pk_runtime(unidad_db)
    if not unidad_pk:
        raise HTTPException(status_code=400, detail="Unidad de negocio inválida o inactiva.")
    return str(unidad_pk)


def _unidad_codigo_filtro(unidad_db: Optional[str]) -> Optional[str]:
    """Traduce la PK/código/nombre canónico al código usado por el detalle legacy."""
    if not unidad_db:
        return None
    unidad_codigo = _resolver_unidad_codigo_runtime(unidad_db)
    if not unidad_codigo:
        raise HTTPException(status_code=400, detail="Unidad de negocio inválida o inactiva.")
    return str(unidad_codigo)


def _detalle_where(unidad_db: Optional[str], fecha_inicio: str, fecha_fin: str, alias: str = ""):
    a = (alias + ".") if alias else ""
    parts = [f"ISNULL({a}activo,1)=1",
             f"{a}fecha_operacion BETWEEN %s AND %s"]
    params = [fecha_inicio, fecha_fin]
    unidad_codigo = _unidad_codigo_filtro(unidad_db)
    if unidad_codigo:
        parts.append(f"{a}unidad_negocio_id = %s")
        params.append(unidad_codigo)
    return " AND ".join(parts), tuple(params)


def _resolver_rango(unidad_db, periodo, fecha_inicio, fecha_fin):
    """Resolución canónica del rango (idéntica al dashboard): anclada al último
    día con datos cuando se pasa `periodo`, sin inventar fechas. Compartida por
    todas las pantallas para que el filtro de fecha sea ÚNICO/canónico."""
    periodo_label = None
    prev_inicio = prev_fin = None
    if periodo and not (fecha_inicio and fecha_fin):
        anchor = _ultimo_dia_con_datos(unidad_db)
        ini, fin, prev_inicio, prev_fin, periodo_label = _periodo_rango(periodo, anchor)
        fecha_inicio = ini.strftime("%Y-%m-%d")
        fecha_fin = fin.strftime("%Y-%m-%d")
    if not fecha_inicio:
        fecha_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not fecha_fin:
        fecha_fin = datetime.now().strftime("%Y-%m-%d")
    if periodo_label is None:
        periodo_label = _label_rango_personalizado(fecha_inicio, fecha_fin)
    return fecha_inicio, fecha_fin, prev_inicio, prev_fin, periodo_label


def _real_detalle_total(unidad_db, fecha_inicio, fecha_fin) -> float:
    where, params = _detalle_where(unidad_db, fecha_inicio, fecha_fin)
    rows = execute_query(
        f"SELECT SUM(importe_neto) AS t FROM {_DETALLE_TABLA} "
        f"WHERE {where}", params)
    return float(rows[0]["t"] or 0) if rows and rows[0].get("t") is not None else 0.0


def _real_top_productos(unidad_db, fecha_inicio, fecha_fin, limit=7):
    where, params = _detalle_where(unidad_db, fecha_inicio, fecha_fin)
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
        WHERE {where}
          AND producto_nombre IS NOT NULL AND producto_nombre <> ''
        GROUP BY producto_nombre
        ORDER BY SUM(importe_neto) DESC
    """
    out = []
    for i, r in enumerate(execute_query(sql, params)):
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
    where, params = _detalle_where(unidad_db, fecha_inicio, fecha_fin)
    sql = f"""
        SELECT TOP {int(limit)} familia_nombre AS familia, SUM(importe_neto) AS ventas
        FROM {_DETALLE_TABLA}
        WHERE {where}
          AND familia_nombre IS NOT NULL AND familia_nombre <> ''
        GROUP BY familia_nombre
        ORDER BY SUM(importe_neto) DESC
    """
    rows = execute_query(sql, params)
    base = total_ventas if total_ventas else (sum(float(r["ventas"] or 0) for r in rows) or 1)
    return [{"familia": (r["familia"] or "").strip(),
             "ventas": round(float(r["ventas"] or 0), 2),
             "participacion": round(float(r["ventas"] or 0) / base * 100, 2)} for r in rows]


def _real_familias_nested(unidad_db, fecha_inicio, fecha_fin, limit_fam=20):
    where, params = _detalle_where(unidad_db, fecha_inicio, fecha_fin)
    """Familias con sus subfamilias (datos reales). Para la pantalla Familia/Subfamilia."""
    sql = f"""
        SELECT familia_nombre AS familia,
               ISNULL(NULLIF(LTRIM(RTRIM(subfamilia_nombre)), ''), '(Sin subfamilia)') AS subfamilia,
               SUM(importe_neto) AS ventas, SUM(cantidad) AS cantidad
        FROM {_DETALLE_TABLA}
        WHERE {where}
          AND familia_nombre IS NOT NULL AND familia_nombre <> ''
        GROUP BY familia_nombre,
                 ISNULL(NULLIF(LTRIM(RTRIM(subfamilia_nombre)), ''), '(Sin subfamilia)')
    """
    fam_map = {}
    for r in execute_query(sql, params):
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
    # Casa/distribuidor = grupo_comercial del Catálogo Enriquecido (Diageo, Pernod
    # Ricard, etc.), unido por producto_id. NO-LIVE (ambas tablas en EDARSAHUB).
    # Productos sin enriquecer (alimentos, etc.) quedan fuera (correcto: solo bebidas
    # tienen casa distribuidora).
    where_d, params = _detalle_where(unidad_db, fecha_inicio, fecha_fin, alias="d")
    sql = f"""
        SELECT TOP {int(limit)} e.grupo_comercial AS casa,
               SUM(d.importe_neto) AS ventas, SUM(d.cantidad) AS cantidad
        FROM {_DETALLE_TABLA} d
        JOIN {_ENRIQ_TABLA} e ON e.producto_id = d.producto_id
        WHERE {where_d}
          AND e.grupo_comercial IS NOT NULL AND LTRIM(RTRIM(e.grupo_comercial)) <> ''
        GROUP BY e.grupo_comercial
        ORDER BY SUM(d.importe_neto) DESC
    """
    rows = execute_query(sql, params)
    base = total_ventas if total_ventas else (sum(float(r["ventas"] or 0) for r in rows) or 1)
    return [{"casa": (r["casa"] or "").strip(),
             "ventas": round(float(r["ventas"] or 0), 2),
             "cantidad": round(float(r.get("cantidad") or 0), 2),
             "participacion": round(float(r["ventas"] or 0) / base * 100, 2)} for r in rows]


def _real_clasificacion_nested(unidad_db, fecha_inicio, fecha_fin):
    """Jerarquía REAL Clasificación → Familia → Subfamilia. La clasificación macro
    (ALIMENTOS/BEBIDAS/OTROS/PENDIENTE_CLASIFICACION) es DATO CANÓNICO del producto:
    se lee de Sync_Productos.ClasificacionProductoID → Comercial_ClasificacionesProducto
    (catálogo controlado), unido por producto_id. SIN CASE en el endpoint."""
    where_d, params = _detalle_where(unidad_db, fecha_inicio, fecha_fin, alias="d")
    sql = f"""
        SELECT ISNULL(cc.Codigo, 'PENDIENTE_CLASIFICACION') AS clasificacion,
               ISNULL(NULLIF(LTRIM(RTRIM(d.familia_nombre)), ''), '(Sin familia)') AS familia,
               ISNULL(NULLIF(LTRIM(RTRIM(d.subfamilia_nombre)), ''), '(Sin subfamilia)') AS subfamilia,
               SUM(d.importe_neto) AS ventas, SUM(d.cantidad) AS cantidad
        FROM {_DETALLE_TABLA} d
        LEFT JOIN {_SYNC_PROD} p ON p.ProductoID = d.producto_id
        LEFT JOIN {_CLAS_TABLA} cc ON cc.ClasificacionProductoID = p.ClasificacionProductoID
        WHERE {where_d}
        GROUP BY ISNULL(cc.Codigo, 'PENDIENTE_CLASIFICACION'),
                 ISNULL(NULLIF(LTRIM(RTRIM(d.familia_nombre)), ''), '(Sin familia)'),
                 ISNULL(NULLIF(LTRIM(RTRIM(d.subfamilia_nombre)), ''), '(Sin subfamilia)')
    """
    # Agregados por familia (para decidir clasificación dominante y subfamilias)
    fam_cat_ventas = {}   # familia -> {clasificacion: ventas}
    fam_subs = {}         # familia -> {subfamilia: {ventas, cantidad}}
    fam_tot = {}          # familia -> {ventas, cantidad}
    for r in execute_query(sql, params):
        clas = r["clasificacion"]
        fam = r["familia"]
        sub = r["subfamilia"]
        v = float(r["ventas"] or 0)
        c = float(r["cantidad"] or 0)
        fam_cat_ventas.setdefault(fam, {}).setdefault(clas, 0.0)
        fam_cat_ventas[fam][clas] += v
        sd = fam_subs.setdefault(fam, {}).setdefault(sub, {"ventas": 0.0, "cantidad": 0.0})
        sd["ventas"] += v
        sd["cantidad"] += c
        ft = fam_tot.setdefault(fam, {"ventas": 0.0, "cantidad": 0.0})
        ft["ventas"] += v
        ft["cantidad"] += c

    # Construir clasificación → familias (cada familia bajo su categoría dominante)
    clas_map = {}
    for fam, tot in fam_tot.items():
        dom = max(fam_cat_ventas[fam].items(), key=lambda kv: kv[1])[0]
        cd = clas_map.setdefault(dom, {"clasificacion": dom, "ventas": 0.0, "cantidad": 0.0, "fams": []})
        cd["ventas"] += tot["ventas"]
        cd["cantidad"] += tot["cantidad"]
        fv = tot["ventas"] or 1
        subs = sorted(
            [{"nombre": s, "ventas": round(d["ventas"], 2), "cantidad": round(d["cantidad"], 2),
              "porcentaje": round(d["ventas"] / fv * 100, 1)} for s, d in fam_subs[fam].items()],
            key=lambda x: x["ventas"], reverse=True)
        cd["fams"].append({"familia": fam, "ventas": round(tot["ventas"], 2),
                           "cantidad": round(tot["cantidad"], 2), "subfamilias": subs})

    total = sum(cd["ventas"] for cd in clas_map.values()) or 1
    out = []
    for cd in sorted(clas_map.values(), key=lambda x: x["ventas"], reverse=True):
        cv = cd["ventas"] or 1
        familias = sorted(cd["fams"], key=lambda x: x["ventas"], reverse=True)
        for f in familias:
            f["porcentaje"] = round(f["ventas"] / cv * 100, 1)
        out.append({"clasificacion": cd["clasificacion"], "ventas": round(cd["ventas"], 2),
                    "cantidad": round(cd["cantidad"], 2),
                    "porcentaje": round(cd["ventas"] / total * 100, 1),
                    "familias": familias})
    return out


_GRADO_BUCKETS = [(0, 0, "Sin alcohol (0°)"), (0.1, 15, "1–15°"),
                  (15, 30, "15–30°"), (30, 40, "30–40°"), (40, 999, "40°+")]


def _real_alcohol(unidad_db, fecha_inicio, fecha_fin):
    """Reporte de bebidas: con/sin alcohol y por grado, desde el Catálogo
    Enriquecido (es_alcoholico/grado_alcohol), unido por producto_id. NO-LIVE."""
    where_d, params = _detalle_where(unidad_db, fecha_inicio, fecha_fin, alias="d")
    sql = f"""
        SELECT e.es_alcoholico AS es_alcoholico, e.grado_alcohol AS grado,
               SUM(d.importe_neto) AS ventas, SUM(d.cantidad) AS cantidad
        FROM {_DETALLE_TABLA} d
        JOIN {_ENRIQ_TABLA} e ON e.producto_id = d.producto_id
        WHERE {where_d}
        GROUP BY e.es_alcoholico, e.grado_alcohol
    """
    rows = execute_query(sql, params)
    con = {"label": "Con alcohol", "ventas": 0.0, "cantidad": 0.0}
    sin = {"label": "Sin alcohol", "ventas": 0.0, "cantidad": 0.0}
    grados = {b[2]: {"rango": b[2], "ventas": 0.0, "cantidad": 0.0} for b in _GRADO_BUCKETS}
    for r in rows:
        v = float(r["ventas"] or 0)
        c = float(r["cantidad"] or 0)
        es_alc = bool(r.get("es_alcoholico"))
        g = r.get("grado")
        g = float(g) if g is not None else None
        (con if es_alc else sin)["ventas"] += v
        (con if es_alc else sin)["cantidad"] += c
        if es_alc and g is not None:
            for lo, hi, label in _GRADO_BUCKETS:
                if (lo == 0 and hi == 0 and g == 0) or (lo <= g <= hi and not (lo == 0 and hi == 0)):
                    grados[label]["ventas"] += v
                    grados[label]["cantidad"] += c
                    break
    total = (con["ventas"] + sin["ventas"]) or 1
    for d in (con, sin):
        d["ventas"] = round(d["ventas"], 2)
        d["cantidad"] = round(d["cantidad"], 2)
        d["participacion"] = round(d["ventas"] / total * 100, 2)
    grados_out = [{"rango": g["rango"], "ventas": round(g["ventas"], 2),
                   "cantidad": round(g["cantidad"], 2),
                   "participacion": round(g["ventas"] / (con["ventas"] or 1) * 100, 2)}
                  for g in grados.values() if g["ventas"] > 0]
    return {"con_alcohol": con, "sin_alcohol": sin, "por_grado": grados_out,
            "total": round(total, 2)}


def _real_tickets(unidad_db, fecha_inicio, fecha_fin, limit=200):
    """Lista de tickets (cuentas) reconstruidos desde el detalle — nivel cuenta."""
    where_d, params = _detalle_where(unidad_db, fecha_inicio, fecha_fin)
    sql = f"""
        SELECT TOP {int(limit)} unidad_negocio_nombre AS unidad, sucursal_nombre AS sucursal,
               fecha_operacion, numero_ticket, MIN(fecha_hora) AS fh, MAX(pax) AS pax,
               COUNT(*) AS lineas, SUM(importe_neto) AS ventas, SUM(propina) AS propina
        FROM {_DETALLE_TABLA}
        WHERE {where_d} AND numero_ticket IS NOT NULL
        GROUP BY unidad_negocio_nombre, sucursal_nombre, fecha_operacion, numero_ticket
        ORDER BY MIN(fecha_hora) DESC, SUM(importe_neto) DESC
    """
    out = []
    for r in execute_query(sql, params):
        out.append({
            "unidad": r["unidad"], "sucursal": r.get("sucursal"),
            "fecha": str(r["fecha_operacion"])[:10], "numero_ticket": r["numero_ticket"],
            "hora": str(r["fh"])[11:16] if r.get("fh") else "",
            "pax": int(r["pax"] or 0), "lineas": int(r["lineas"] or 0),
            "ventas": round(float(r["ventas"] or 0), 2),
            "propina": round(float(r["propina"] or 0), 2),
        })
    return out


def _real_ticket_lineas(unidad_db, fecha, numero_ticket):
    """Líneas (productos) de un ticket — el nivel más bajo (reconstrucción)."""
    where = ["ISNULL(d.activo,1)=1", "d.numero_ticket = %s"]
    params = [numero_ticket]
    if fecha:
        where.append("d.fecha_operacion = %s")
        params.append(fecha)
    unidad_codigo = _unidad_codigo_filtro(unidad_db)
    if unidad_codigo:
        where.append("d.unidad_negocio_id = %s")
        params.append(unidad_codigo)
    sql = f"""
        SELECT d.producto_codigo_fuente AS codigo, d.producto_nombre AS producto,
               d.familia_nombre AS familia, d.subfamilia_nombre AS subfamilia,
               ISNULL(cc.Codigo, 'PENDIENTE_CLASIFICACION') AS clasificacion,
               e.grupo_comercial AS casa,
               e.marca, e.grado_alcohol AS grado_alcohol, e.es_alcoholico AS es_alcoholico,
               d.cantidad, d.precio_unitario, d.importe_neto AS importe, d.propina, d.pax,
               d.fecha_hora
        FROM {_DETALLE_TABLA} d
        LEFT JOIN {_SYNC_PROD} p ON p.ProductoID = d.producto_id
        LEFT JOIN {_CLAS_TABLA} cc ON cc.ClasificacionProductoID = p.ClasificacionProductoID
        LEFT JOIN {_ENRIQ_TABLA} e ON e.producto_id = d.producto_id
        WHERE {' AND '.join(where)}
        ORDER BY d.importe_neto DESC
    """
    rows = execute_query(sql, tuple(params))
    out = []
    for r in rows:
        out.append({
            "codigo": r.get("codigo") or "", "producto": r.get("producto") or "",
            "familia": (r.get("familia") or "").strip(),
            "subfamilia": (r.get("subfamilia") or "").strip(),
            "clasificacion": (r.get("clasificacion") or "").strip(),
            "casa": (r.get("casa") or "").strip(), "marca": (r.get("marca") or "").strip(),
            "grado_alcohol": round(float(r["grado_alcohol"]), 1) if r.get("grado_alcohol") is not None else None,
            "es_alcoholico": bool(r.get("es_alcoholico")),
            "cantidad": round(float(r.get("cantidad") or 0), 2),
            "precio_unitario": round(float(r.get("precio_unitario") or 0), 2),
            "importe": round(float(r.get("importe") or 0), 2),
            "propina": round(float(r.get("propina") or 0), 2),
            "pax": int(r.get("pax") or 0),
        })
    return out


def _real_horario(unidad_db, fecha_inicio, fecha_fin):
    # Agrega a nivel ticket (pax/cheques correctos) y clasifica por hora de apertura.
    # CENTRALIZADO (2026-06-10): las franjas (Desayuno/Comida/Cena) se LEEN de
    # Sistema_TurnosOperativosUnidad (NO-LIVE, sin hardcode). Una sola fuente de
    # verdad: lo que se configure en "Configuración Operativa" rige este reporte.
    franjas = _get_franjas_canonicas()
    if franjas:
        # El turno que cruza medianoche (o el último por orden) es el catch-all (ELSE).
        catch = next((f for f in franjas if f["cruza"]), franjas[-1])
        whens, rango_map = [], {}
        for f in franjas:
            if f is catch and f["cruza"]:
                rango_map[f["nombre"]] = f"{f['ini_str']} – madrugada"
            else:
                rango_map[f["nombre"]] = f"{f['ini_str']} - {f['fin_str']}"
            if f is catch:
                continue
            # hora_fin '13:00' (m=0) cubre hasta las 12:59 → bucket de hora = h_fin-1.
            h_fin_bucket = f["h_fin"] - 1 if f["m_fin"] == 0 else f["h_fin"]
            nombre = f["nombre"].replace("'", "''")
            whens.append(f"WHEN DATEPART(hour, fh) BETWEEN {f['h_ini']} AND {h_fin_bucket} THEN '{nombre}'")
        catch_nombre = catch["nombre"].replace("'", "''")
        case_expr = "CASE " + " ".join(whens) + f" ELSE '{catch_nombre}' END"
        orden_map = {f["nombre"]: i for i, f in enumerate(franjas)}
    else:
        # Safety net (la config no debería faltar): comportamiento previo conocido.
        case_expr = ("CASE WHEN DATEPART(hour, fh) BETWEEN 7 AND 12 THEN 'Desayuno' "
                     "WHEN DATEPART(hour, fh) BETWEEN 13 AND 18 THEN 'Comida' ELSE 'Cena' END")
        orden_map = {"Desayuno": 0, "Comida": 1, "Cena": 2}
        rango_map = {}
    where_d, params = _detalle_where(unidad_db, fecha_inicio, fecha_fin)
    sql = f"""
        WITH tk AS (
            SELECT unidad_negocio_nombre, fecha_operacion, numero_ticket,
                   MIN(fecha_hora) AS fh, MAX(pax) AS pax,
                   SUM(importe_neto) AS ventas, SUM(propina) AS propinas
            FROM {_DETALLE_TABLA}
            WHERE {where_d}
            GROUP BY unidad_negocio_nombre, fecha_operacion, numero_ticket
        )
        SELECT {case_expr} AS horario,
               SUM(ventas) AS ventas, SUM(pax) AS pax,
               COUNT(*) AS cheques, SUM(propinas) AS propinas
        FROM tk
        GROUP BY {case_expr}
    """
    out = []
    for r in execute_query(sql, params):
        ventas = round(float(r["ventas"] or 0), 2)
        cheques = int(r["cheques"] or 0)
        pax = int(r["pax"] or 0)
        ticket_promedio = round(ventas / cheques, 2) if cheques else 0
        pax_promedio = round(ventas / pax, 2) if pax else 0

        out.append({"horario": r["horario"], "ventas": ventas,
                    "pax": pax, "cheques": cheques,
                    "propinas": round(float(r["propinas"] or 0), 2),
                    "ticket_promedio": ticket_promedio,
                    "cheque_promedio": ticket_promedio,
                    "pax_promedio": pax_promedio,
                    "rango": rango_map.get(r["horario"], "")})
    out.sort(key=lambda x: orden_map.get(x["horario"], 9))
    return out



@router.get("/dashboard")
async def get_dashboard_data(
    unidad: Optional[str] = Query(None, description="Unidad de negocio (130MID, CIENFUEGOS, etc.)"),
    periodo: Optional[str] = Query(None, description="Periodo: dia | semana | mes | anio/año"),
    fecha_inicio: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)")
):
    """Dashboard principal con acumulado cerrado y operación vigente separada."""
    unidad_db = normalizar_unidad(unidad) if unidad and unidad.lower() != "todas" else None

    periodo_label = None
    prev_inicio = prev_fin = None

    if periodo and not (fecha_inicio and fecha_fin):
        anchor = _ultimo_dia_con_kpis(unidad_db, periodo)
        ini, fin, prev_inicio, prev_fin, periodo_label = _periodo_rango(periodo, anchor)
        fecha_inicio = ini.strftime("%Y-%m-%d")
        fecha_fin = fin.strftime("%Y-%m-%d")

    if not fecha_inicio:
        fecha_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not fecha_fin:
        fecha_fin = datetime.now().strftime("%Y-%m-%d")
    if periodo_label is None:
        periodo_label = _label_rango_personalizado(fecha_inicio, fecha_fin)

    try:
        desglose = _desglose_periodo_canonico_portal(fecha_inicio, fecha_fin, unidad_db)
        acumulado = desglose.get("acumulado_cerrado") or {}
        dia_actual = desglose.get("dia_actual") or {}
        total_con_dia = desglose.get("total_incluyendo_dia") or {}
        kpi_data = _normalizar_resumen_kpi_portal(acumulado)
        kpi_dia = _normalizar_resumen_kpi_portal(dia_actual)
        kpi_total = _normalizar_resumen_kpi_portal(total_con_dia)

        kpis_trends = {}
        if prev_inicio and prev_fin:
            prev = _resumen_periodo_canonico_portal(
                prev_inicio.strftime("%Y-%m-%d") if hasattr(prev_inicio, "strftime") else str(prev_inicio),
                prev_fin.strftime("%Y-%m-%d") if hasattr(prev_fin, "strftime") else str(prev_fin),
                unidad_db,
            )
            kpis_trends = {
                "ventas_totales": _trend_pct(kpi_data.get("ventas_totales"), prev.get("ventas_totales")),
                "pax_total": _trend_pct(kpi_data.get("pax_total"), prev.get("pax_total")),
                "cheques_total": _trend_pct(kpi_data.get("cheques_total"), prev.get("cheques_total")),
                "propinas_total": _trend_pct(kpi_data.get("propinas_total"), prev.get("propinas_total")),
            }

        ventas_por_unidad = []
        ventas_dia_por_unidad = []
        if not unidad_db:
            ventas_por_unidad = _ventas_por_unidad_desde_resumen(acumulado)
            ventas_dia_por_unidad = _ventas_por_unidad_desde_resumen(dia_actual)

        total_ventas = float(kpi_data.get("ventas_totales", 0)) or 1

        fecha_fin_detalle = fecha_fin
        if int((dia_actual.get("atomos") or {}).get("dias") or 0) > 0:
            fecha_operativa = _ultimo_dia_con_kpis(unidad_db)
            if date.fromisoformat(str(fecha_inicio)[:10]) <= fecha_operativa <= date.fromisoformat(str(fecha_fin)[:10]):
                fecha_fin_detalle = (fecha_operativa - timedelta(days=1)).isoformat()

        det_total = _real_detalle_total(unidad_db, fecha_inicio, fecha_fin_detalle)
        ventas_horario = _real_horario(unidad_db, fecha_inicio, fecha_fin_detalle)
        top_productos = _real_top_productos(unidad_db, fecha_inicio, fecha_fin_detalle, limit=7)
        casas_distribuidoras = _real_casas(unidad_db, fecha_inicio, fecha_fin_detalle, total_ventas=det_total)
        ventas_familia = _real_familias(unidad_db, fecha_inicio, fecha_fin_detalle, total_ventas=det_total)
        ventas_clasificacion = _real_clasificacion_nested(unidad_db, fecha_inicio, fecha_fin_detalle)

        response = {
            "success": True,
            "_source": "KPIS_CANONICOS_SERVICE",
            "_blocks_source": _DETALLE_TABLA,
            "_detalle_total": round(det_total, 2),
            "_unidad": unidad_db or "TODAS",
            "timestamp": datetime.utcnow().isoformat(),
            "contrato_periodo": desglose.get("contrato") or {},
            "filtros": {
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "fecha_fin_acumulado_cerrado": fecha_fin_detalle,
                "unidad": unidad_db or "TODAS",
                "periodo": periodo or None,
                "periodo_label": periodo_label,
            },
            "kpis_trends": kpis_trends,
            "kpis": kpi_data,
            "ventas_por_unidad": [
                {
                    "unidad": u["unidad"],
                    "ventas": round(float(u["ventas"] or 0), 2),
                    "pax": int(u["pax_total"] or 0),
                    "tickets": int(u["tickets"] or 0),
                    "propinas": round(float(u["propinas"] or 0), 2),
                    "ticket_promedio": round(float(u["ticket_promedio"] or 0), 2),
                    "cheque_promedio": round(float(u["cheque_promedio"] or 0), 2),
                    "pax_promedio": round(float(u["pax_promedio"] or 0), 2),
                    "participacion": round((float(u["ventas"] or 0) / total_ventas) * 100, 2),
                }
                for u in ventas_por_unidad
            ] if ventas_por_unidad else [],
            "ventas_dia_actual": {
                "kpis": kpi_dia,
                "ventas_por_unidad": ventas_dia_por_unidad,
            },
            "total_incluyendo_dia_actual": {"kpis": kpi_total},
            "ventas_horario": ventas_horario,
            "top_productos": top_productos,
            "casas_distribuidoras": casas_distribuidoras,
            "ventas_familia": ventas_familia,
            "ventas_clasificacion": ventas_clasificacion,
        }

        logger.info(
            "[INTELIGENCIA] Dashboard OK acumulado cerrado - %s - $%s",
            unidad_db or "TODAS",
            f"{float(kpi_data.get('ventas_totales') or 0):,.2f}",
        )
        return response

    except Exception as e:
        logger.error(f"[INTELIGENCIA] Error dashboard: {e}")
        return {
            "success": False,
            "_source": "ERROR",
            "_error": str(e),
            "kpis": _kpi_cero_portal(),
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
    Tendencia diaria para gráficos.
    Fuente KPI principal: KPIsCanonicosService / dbo.Comercial_KPIs_Diarios_v2.
    """
    unidad_db = normalizar_unidad(unidad) if unidad and unidad.lower() != "todas" else None

    if not fecha_inicio:
        fecha_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not fecha_fin:
        fecha_fin = datetime.now().strftime("%Y-%m-%d")

    try:
        datos_diarios = _series_periodo_canonico_portal(fecha_inicio, fecha_fin, unidad_db)

        return {
            "success": True,
            "_source": "KPIS_CANONICOS_SERVICE",
            "_unidad": unidad_db or "TODAS",
            "total_dias": len(datos_diarios),
            "datos_diarios": datos_diarios
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

    Fuente única:
    - Comercial_Inteligencia_VentasDetalleProducto
    - Sistema_TurnosOperativosUnidad para rangos operativos

    Sin fallback proporcional, sin datos inventados, sin cortes hardcodeados.
    """
    unidad_db = normalizar_unidad(unidad) if unidad and unidad.lower() != "todas" else None

    if not fecha_inicio or not fecha_fin:
        anchor = _ultimo_dia_con_kpis(unidad_db)
        ini, fin, _, _, _ = _periodo_rango("mes", anchor)
        fecha_inicio = fecha_inicio or ini.strftime("%Y-%m-%d")
        fecha_fin = fecha_fin or fin.strftime("%Y-%m-%d")

    try:
        datos = _real_horario(unidad_db, fecha_inicio, fecha_fin)

        return {
            "success": True,
            "_source": "Comercial_Inteligencia_VentasDetalleProducto",
            "_config_source": "Sistema_TurnosOperativosUnidad",
            "_unidad": unidad_db or "TODAS",
            "_sin_fallback_proporcional": True,
            "ventas_horario": [
                {
                    "horario": d.get("horario"),
                    "ventas": round(float(d.get("ventas") or 0), 2),
                    "pax": int(d.get("pax") or 0),
                    "cheques": int(d.get("cheques") or 0),
                    "mesas": int(d.get("cheques") or 0),
                    "propinas": round(float(d.get("propinas") or 0), 2),
                    "ticket_promedio": round(float(d.get("ticket_promedio") or 0), 2),
                    "consumo_promedio": round(float(d.get("ticket_promedio") or 0), 2),
                    "rango": d.get("rango") or ""
                }
                for d in datos
            ]
        }
    except Exception as e:
        logger.error(f"[INTELIGENCIA] Error horarios canonicos: {e}")
        return {
            "success": False,
            "_source": "ERROR",
            "_error": str(e),
            "_sin_fallback_proporcional": True,
            "ventas_horario": []
        }


@router.get("/dashboard/pax")
async def get_analisis_pax(
    unidad: Optional[str] = Query(None, description="Unidad de negocio"),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None)
):
    raise HTTPException(
        status_code=410,
        detail={
            "success": False,
            "status": "deprecated",
            "code": "INTELIGENCIA_PAX_ENDPOINT_DEPRECATED",
            "message": (
                "Endpoint deshabilitado: dependía de una fuente "
                "paralela Sync_PAX_Detalle sin contrato canónico "
                "completo para TiempoMesa y Turno."
            ),
        },
    )

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
    periodo: Optional[str] = Query(None, description="dia | semana | mes | anio"),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500)
):
    """
    Top productos vendidos (NO-LIVE, datos reales por línea).
    Fuente: Comercial_Inteligencia_VentasDetalleProducto.
    """
    unidad_db = normalizar_unidad(unidad) if unidad and unidad.lower() != "todas" else None
    fecha_inicio, fecha_fin, _, _, periodo_label = _resolver_rango(unidad_db, periodo, fecha_inicio, fecha_fin)

    try:
        productos = _real_top_productos(unidad_db, fecha_inicio, fecha_fin, limit=limit)
        return {
            "success": True,
            "_source": _DETALLE_TABLA,
            "_unidad": unidad_db or "TODAS",
            "filtros": {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin,
                        "periodo": periodo or None, "periodo_label": periodo_label},
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
    periodo: Optional[str] = Query(None, description="dia | semana | mes | anio"),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None)
):
    """
    Ventas por familia (NO-LIVE) + jerarquía Clasificación(Alimentos/Bebidas/Otros)
    → Familia → Subfamilia. Clasificación macro canónica desde Sync_Productos.
    Fuente: Comercial_Inteligencia_VentasDetalleProducto.
    """
    unidad_db = normalizar_unidad(unidad) if unidad and unidad.lower() != "todas" else None
    fecha_inicio, fecha_fin, _, _, periodo_label = _resolver_rango(unidad_db, periodo, fecha_inicio, fecha_fin)

    try:
        det_total = _real_detalle_total(unidad_db, fecha_inicio, fecha_fin)
        familias = _real_familias_nested(unidad_db, fecha_inicio, fecha_fin)
        clasificaciones = _real_clasificacion_nested(unidad_db, fecha_inicio, fecha_fin)
        return {
            "success": True,
            "_source": _DETALLE_TABLA,
            "_unidad": unidad_db or "TODAS",
            "_detalle_total": round(det_total, 2),
            "filtros": {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin,
                        "periodo": periodo or None, "periodo_label": periodo_label},
            "ventas_familia": familias,
            "ventas_clasificacion": clasificaciones,
        }
    except Exception as e:
        logger.error(f"[INTELIGENCIA] Error familias: {e}")
        return {"success": False, "_error": str(e), "ventas_familia": [], "ventas_clasificacion": []}


@router.get("/alcohol")
async def get_reporte_alcohol(
    unidad: Optional[str] = Query(None),
    periodo: Optional[str] = Query(None, description="dia | semana | mes | anio"),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None)
):
    """
    Reporte de bebidas: con/sin alcohol y por grado de alcohol (NO-LIVE).
    Fuente: detalle + Catálogo Enriquecido (es_alcoholico/grado_alcohol).
    """
    unidad_db = normalizar_unidad(unidad) if unidad and unidad.lower() != "todas" else None
    fecha_inicio, fecha_fin, _, _, periodo_label = _resolver_rango(unidad_db, periodo, fecha_inicio, fecha_fin)
    try:
        rep = _real_alcohol(unidad_db, fecha_inicio, fecha_fin)
        return {
            "success": True,
            "_source": f"{_DETALLE_TABLA} + {_ENRIQ_TABLA}",
            "_unidad": unidad_db or "TODAS",
            "filtros": {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin,
                        "periodo": periodo or None, "periodo_label": periodo_label},
            **rep,
        }
    except Exception as e:
        logger.error(f"[INTELIGENCIA] Error alcohol: {e}")
        return {"success": False, "_error": str(e), "con_alcohol": None, "sin_alcohol": None, "por_grado": []}


@router.get("/casas")
async def get_ventas_casas(
    unidad: Optional[str] = Query(None),
    periodo: Optional[str] = Query(None, description="dia | semana | mes | anio"),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None)
):
    """
    Ventas por Casa/Distribuidor (NO-LIVE). Fuente: detalle + Catálogo Enriquecido
    (grupo_comercial). Mismo cálculo canónico que el bloque del dashboard, expuesto
    como endpoint dedicado para la pantalla Casas/Distribuidores.
    """
    unidad_db = normalizar_unidad(unidad) if unidad and unidad.lower() != "todas" else None
    fecha_inicio, fecha_fin, _, _, periodo_label = _resolver_rango(unidad_db, periodo, fecha_inicio, fecha_fin)
    try:
        det_total = _real_detalle_total(unidad_db, fecha_inicio, fecha_fin)
        casas = _real_casas(unidad_db, fecha_inicio, fecha_fin, total_ventas=det_total)
        return {
            "success": True,
            "_source": f"{_DETALLE_TABLA} + {_ENRIQ_TABLA}",
            "_unidad": unidad_db or "TODAS",
            "_detalle_total": round(det_total, 2),
            "filtros": {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin,
                        "periodo": periodo or None, "periodo_label": periodo_label},
            "casas_distribuidoras": casas,
        }
    except Exception as e:
        logger.error(f"[INTELIGENCIA] Error casas: {e}")
        return {"success": False, "_error": str(e), "casas_distribuidoras": []}


@router.get("/tickets")
async def get_tickets(
    unidad: Optional[str] = Query(None),
    periodo: Optional[str] = Query(None, description="dia | semana | mes | anio"),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=1000)
):
    """Lista de tickets/cuentas reconstruidos (drill-down nivel cuenta). NO-LIVE."""
    unidad_db = normalizar_unidad(unidad) if unidad and unidad.lower() != "todas" else None
    fecha_inicio, fecha_fin, _, _, periodo_label = _resolver_rango(unidad_db, periodo, fecha_inicio, fecha_fin)
    try:
        tickets = _real_tickets(unidad_db, fecha_inicio, fecha_fin, limit=limit)
        return {
            "success": True, "_source": _DETALLE_TABLA, "_unidad": unidad_db or "TODAS",
            "filtros": {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin,
                        "periodo": periodo or None, "periodo_label": periodo_label},
            "total": len(tickets), "tickets": tickets,
        }
    except Exception as e:
        logger.error(f"[INTELIGENCIA] Error tickets: {e}")
        return {"success": False, "_error": str(e), "tickets": []}


@router.get("/ticket-detalle")
async def get_ticket_detalle(
    numero_ticket: str = Query(..., description="Número de ticket/cuenta"),
    unidad: Optional[str] = Query(None),
    fecha: Optional[str] = Query(None, description="Fecha operación YYYY-MM-DD (desambigua)")
):
    """Líneas de un ticket — el nivel más bajo (máxima profundidad). NO-LIVE."""
    unidad_db = normalizar_unidad(unidad) if unidad and unidad.lower() != "todas" else None
    try:
        lineas = _real_ticket_lineas(unidad_db, fecha, numero_ticket)
        total = round(sum(l["importe"] for l in lineas), 2)
        propina = round(sum(l["propina"] for l in lineas), 2)
        return {
            "success": True, "_source": _DETALLE_TABLA, "numero_ticket": numero_ticket,
            "unidad": unidad_db or "TODAS", "fecha": fecha,
            "total": total, "propina": propina, "lineas": lineas, "n_lineas": len(lineas),
        }
    except Exception as e:
        logger.error(f"[INTELIGENCIA] Error ticket-detalle: {e}")
        return {"success": False, "_error": str(e), "lineas": []}


# ============================================================================
# ENDPOINT: Ventas por Casa/Distribuidor
# Fuente: Products con fallback proporcional
# ============================================================================
def _real_productos_subfamilia(unidad_db, fi, ff, familia, subfamilia, limit=200):
    """Productos de venta dentro de una familia/subfamilia (nivel más bajo del
    reporte Familia→Subfamilia→Producto). Maneja los marcadores '(Sin familia)'
    y '(Sin subfamilia)' como NULL/vacío en la fuente."""
    detalle_where, detalle_params = _detalle_where(unidad_db, fi, ff)
    where, params = [detalle_where], list(detalle_params)
    if familia == "(Sin familia)":
        where.append("(familia_nombre IS NULL OR LTRIM(RTRIM(familia_nombre))='')")
    else:
        where.append("LTRIM(RTRIM(familia_nombre)) = %s")
        params.append(familia.strip())
    if subfamilia == "(Sin subfamilia)":
        where.append("(subfamilia_nombre IS NULL OR LTRIM(RTRIM(subfamilia_nombre))='')")
    else:
        where.append("LTRIM(RTRIM(subfamilia_nombre)) = %s")
        params.append(subfamilia.strip())
    sql = f"""
        SELECT TOP {int(limit)} producto_nombre AS producto, producto_codigo_fuente AS codigo,
               SUM(importe_neto) AS ventas, SUM(cantidad) AS cantidad
        FROM {_DETALLE_TABLA}
        WHERE {' AND '.join(where)}
        GROUP BY producto_nombre, producto_codigo_fuente
        ORDER BY SUM(importe_neto) DESC
    """
    rows = execute_query(sql, tuple(params))
    total = sum(float(r["ventas"] or 0) for r in rows) or 1
    return [{"producto": r["producto"] or "", "codigo": r.get("codigo") or "",
             "ventas": round(float(r["ventas"] or 0), 2),
             "cantidad": round(float(r.get("cantidad") or 0), 2),
             "porcentaje": round(float(r["ventas"] or 0) / total * 100, 1)} for r in rows]


@router.get("/productos-subfamilia")
async def get_productos_subfamilia(
    familia: str = Query(...),
    subfamilia: str = Query(...),
    unidad: Optional[str] = Query(None),
    periodo: Optional[str] = Query(None),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
):
    """Productos de venta de una familia/subfamilia (drill-down del reporte Familias)."""
    unidad_db = normalizar_unidad(unidad) if unidad and unidad.lower() != "todas" else None
    fi, ff, _, _, _ = _resolver_rango(unidad_db, periodo, fecha_inicio, fecha_fin)
    try:
        productos = _real_productos_subfamilia(unidad_db, fi, ff, familia, subfamilia)
        return {"success": True, "_source": _DETALLE_TABLA, "familia": familia,
                "subfamilia": subfamilia, "total": len(productos), "productos": productos}
    except Exception as e:
        logger.error(f"[INTELIGENCIA] Error productos-subfamilia: {e}")
        return {"success": False, "_error": str(e), "productos": []}
async def get_ventas_casas(
    unidad: Optional[str] = Query(None),
    periodo: Optional[str] = Query(None, description="dia | semana | mes | anio"),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None)
):
    """
    Ventas por casa/distribuidor (NO-LIVE). Casa = grupo_comercial del Catálogo
    Enriquecido (Diageo, Pernod Ricard, etc.), unido por producto_id.
    """
    unidad_db = normalizar_unidad(unidad) if unidad and unidad.lower() != "todas" else None
    fecha_inicio, fecha_fin, _, _, periodo_label = _resolver_rango(unidad_db, periodo, fecha_inicio, fecha_fin)

    try:
        det_total = _real_detalle_total(unidad_db, fecha_inicio, fecha_fin)
        casas = _real_casas(unidad_db, fecha_inicio, fecha_fin, total_ventas=det_total, limit=50)
        return {
            "success": True,
            "_source": f"{_DETALLE_TABLA} + {_ENRIQ_TABLA}",
            "_unidad": unidad_db or "TODAS",
            "filtros": {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin,
                        "periodo": periodo or None, "periodo_label": periodo_label},
            "casas_distribuidoras": casas,
        }
    except Exception as e:
        logger.error(f"[INTELIGENCIA] Error casas: {e}")
        return {"success": False, "_error": str(e), "casas_distribuidoras": []}


# ============================================================================
# ENDPOINT: Unidades de Negocio disponibles
# ============================================================================
@router.get("/unidades")
async def get_unidades_negocio(request: Request):
    """Lista de unidades de negocio activas.
    Si el llamante es un usuario EXTERNO del portal de inteligencia, se devuelven
    SOLO las unidades asignadas a su cuenta (scoping)."""
    # Scoping para usuarios externos (intel_portal_guard fija request.state.intel_unidades)
    allowed = getattr(request.state, "intel_unidades", None)
    try:
        # P1 REFACTORIZADO: Usar UnidadesService (SQL-First)
        unidades = _pic_unidades_activas()
        lista = [
            {
                "unidad_negocio_pk": str(u.get("unidad_negocio_pk") or ""),
                "codigo": u.get("codigo"),
                "nombre": u.get("nombre"),
                "sistema": u.get("system_type", "N/A")
            }
            for u in unidades
        ]
        if allowed is not None:
            lista = [
                u for u in lista
                if str(u.get("unidad_negocio_pk") or "") in allowed
            ]
        return {"success": True, "unidades": lista}
    except Exception as e:
        logger.error(f"[INTELIGENCIA] Error unidades: {e}")
        # Fallback también usa UnidadesService (cache interno)
        try:
            from core.unidades_service import UnidadesService
            unidades = UnidadesService.get_all()
            lista = [
                {
                    "unidad_negocio_pk": str(u.get("unidad_negocio_pk") or ""),
                    "codigo": u.get("codigo"),
                    "nombre": u.get("nombre"),
                    "sistema": u.get("system_type", "N/A"),
                }
                for u in unidades
            ]
            if allowed is not None:
                lista = [
                    u for u in lista
                    if str(u.get("unidad_negocio_pk") or "") in allowed
                ]
            return {"success": True, "_source": "FALLBACK_UNIDADES_SERVICE", "unidades": lista}
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



# ============================================================================
# ADMIN: Clasificación Comercial de Producto (catálogo canónico)
# Fuente: Sync_Productos + Comercial_ClasificacionesProducto
# La regla A/B (SoftRestaurant) solo se aplicó en el backfill; aquí el admin
# resuelve los PENDIENTE_CLASIFICACION asignando una clasificación MANUAL.
# ============================================================================

class ClasificarRequest(BaseModel):
    clasificacion_id: int
    producto_ids: Optional[List[str]] = None          # UUIDs de Sync_Productos.ProductoID
    familia_nombre: Optional[str] = None              # alternativa: clasificar familia completa
    system_type: Optional[str] = None                 # opcional para acotar la familia


@router.get("/clasificaciones")
async def get_catalogo_clasificaciones():
    """Catálogo controlado de clasificaciones comerciales (activo)."""
    rows = execute_query(
        f"SELECT ClasificacionProductoID AS id, Codigo AS codigo, Nombre AS nombre, Orden AS orden "
        f"FROM {_CLAS_TABLA} WHERE Activo=1 ORDER BY Orden"
    )
    return {"success": True, "clasificaciones": rows}


@router.get("/admin/productos-clasificacion")
async def admin_listar_productos(
    q: Optional[str] = Query(None, description="Busca por nombre/familia"),
    system_type: Optional[str] = Query(None),
    estado: Optional[str] = Query(None, description="pendientes | clasificados | todos"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: Dict = Depends(require_admin),
):
    """Lista productos del catálogo con su clasificación actual (paginado)."""
    where = ["1=1"]
    params: list = []
    if q:
        where.append("(sp.Nombre LIKE %s OR sp.FamiliaNombre LIKE %s)")
        params += [f"%{q}%", f"%{q}%"]
    if system_type:
        where.append("sp.SystemType = %s")
        params.append(system_type)
    if estado == "pendientes":
        where.append("(cc.Codigo IS NULL OR cc.Codigo = 'PENDIENTE_CLASIFICACION')")
    elif estado == "clasificados":
        where.append("cc.Codigo IS NOT NULL AND cc.Codigo <> 'PENDIENTE_CLASIFICACION'")
    wsql = " AND ".join(where)
    offset = (page - 1) * page_size

    total = execute_query(
        f"SELECT COUNT(*) AS n FROM {_SYNC_PROD} sp "
        f"LEFT JOIN {_CLAS_TABLA} cc ON cc.ClasificacionProductoID = sp.ClasificacionProductoID "
        f"WHERE {wsql}", tuple(params))
    total_n = total[0]["n"] if total else 0

    rows = execute_query(
        f"SELECT sp.ProductoID AS producto_id, sp.Nombre AS nombre, sp.FamiliaNombre AS familia, "
        f"sp.SubFamiliaNombre AS subfamilia, sp.SystemType AS system_type, "
        f"sp.CategoriaNombre AS categoria_pos, "
        f"cc.ClasificacionProductoID AS clasificacion_id, "
        f"ISNULL(cc.Codigo,'PENDIENTE_CLASIFICACION') AS clasificacion, "
        f"sp.ClasificacionOrigen AS origen, sp.ClasificacionFecha AS fecha "
        f"FROM {_SYNC_PROD} sp "
        f"LEFT JOIN {_CLAS_TABLA} cc ON cc.ClasificacionProductoID = sp.ClasificacionProductoID "
        f"WHERE {wsql} ORDER BY sp.FamiliaNombre, sp.Nombre "
        f"OFFSET {offset} ROWS FETCH NEXT {page_size} ROWS ONLY", tuple(params))
    for r in rows:
        r["producto_id"] = str(r["producto_id"])
        r["fecha"] = str(r["fecha"])[:19] if r.get("fecha") else None
    return {"success": True, "total": total_n, "page": page, "page_size": page_size, "productos": rows}


@router.get("/admin/familias-pendientes")
async def admin_familias_pendientes(_: Dict = Depends(require_admin)):
    """Familias con productos PENDIENTE_CLASIFICACION (para clasificar en bloque)."""
    rows = execute_query(
        f"SELECT sp.SystemType AS system_type, sp.FamiliaNombre AS familia, COUNT(*) AS pendientes "
        f"FROM {_SYNC_PROD} sp "
        f"LEFT JOIN {_CLAS_TABLA} cc ON cc.ClasificacionProductoID = sp.ClasificacionProductoID "
        f"WHERE cc.Codigo IS NULL OR cc.Codigo = 'PENDIENTE_CLASIFICACION' "
        f"GROUP BY sp.SystemType, sp.FamiliaNombre ORDER BY COUNT(*) DESC")
    return {"success": True, "total": len(rows), "familias": rows}


@router.post("/admin/clasificar")
async def admin_clasificar(body: ClasificarRequest, _: Dict = Depends(require_admin)):
    """Asigna clasificación MANUAL a productos (por IDs) o a una familia completa.
    Trazabilidad: ClasificacionOrigen='MANUAL', ClasificacionFecha=now."""
    cat = execute_query(
        f"SELECT ClasificacionProductoID AS id, Codigo FROM {_CLAS_TABLA} WHERE ClasificacionProductoID=%s",
        (body.clasificacion_id,))
    if not cat:
        raise HTTPException(status_code=400, detail="clasificacion_id inválido")

    if body.producto_ids:
        marks = ",".join(["%s"] * len(body.producto_ids))
        sql = (f"UPDATE {_SYNC_PROD} SET ClasificacionProductoID=%s, ClasificacionOrigen='MANUAL', "
               f"ClasificacionFecha=SYSDATETIME() WHERE ProductoID IN ({marks})")
        affected = execute_write(sql, tuple([body.clasificacion_id] + body.producto_ids))
    elif body.familia_nombre:
        conds = ["FamiliaNombre=%s"]
        params = [body.clasificacion_id, body.familia_nombre]
        if body.system_type:
            conds.append("SystemType=%s")
            params.append(body.system_type)
        sql = (f"UPDATE {_SYNC_PROD} SET ClasificacionProductoID=%s, ClasificacionOrigen='MANUAL', "
               f"ClasificacionFecha=SYSDATETIME() WHERE {' AND '.join(conds)}")
        affected = execute_write(sql, tuple(params))
    else:
        raise HTTPException(status_code=400, detail="Indica producto_ids o familia_nombre")

    return {"success": True, "actualizados": affected, "clasificacion": cat[0]["Codigo"]}
