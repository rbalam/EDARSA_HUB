"""
Repositorio SQL-first del Benchmark Interno de Grupo (NO-LIVE).
==============================================================
Lee EXCLUSIVAMENTE de EDARSAHUB:
- Nivel unidad: dbo.Comercial_KPIs_Diarios_v2 (ventas/tickets/pax por día).
- Nivel producto: dbo.Comercial_Inteligencia_VentasDetalleProducto (enriquecido).

MÁXIMA CANÓNICA: la DIMENSIÓN "unidad" se resuelve SIEMPRE desde el catálogo
canónico dbo.Unidades_Negocio vía UnidadesService. Las tablas de hechos solo
aportan la LLAVE (unidad_negocio_pk / unidad_negocio_id=código); el código NO
toma de ellas el nombre/servidor (que pueden estar denormalizados). Así dos
unidades MPRO que comparten server_id NO se colapsan (PK canónica distinta).

El benchmark abarca TODAS las unidades del grupo (EDARSA = grupo provisional).
La restricción RBAC NO filtra el dataset: solo el AnonymizerService decide qué
NOMBRES reales ve el usuario. Parametrizado, sin hardcode.
"""
import logging
from typing import Dict, List, Optional

from core.db import execute_sql_query_params
from core.server_registry import EDARSAHUB_CONFIG
from core.unidades_service import UnidadesService
from core.kpis_canonicos import KPIsCanonicosService, resolver_metrica

logger = logging.getLogger(__name__)


def _conn():
    c = EDARSAHUB_CONFIG
    return (c['host'], c['port'], c['database'], c['username'], c['password'])


def _identidad_por_pk(pk: Optional[str]) -> Optional[Dict]:
    """Identidad CANÓNICA de la unidad desde el catálogo (no denormalizada)."""
    u = UnidadesService.get_by_pk(pk) if pk else None
    if not u:
        return None
    return {
        "unidad_pk": u.get("unidad_negocio_pk"),
        "unidad_codigo": u.get("codigo"),
        "unidad_nombre": u.get("nombre"),
        "server_id": str(u.get("server_id") or "").lower() or None,
    }


def _identidad_por_codigo(codigo: Optional[str]) -> Optional[Dict]:
    u = UnidadesService.get_by_codigo(codigo) if codigo else None
    if not u:
        return None
    return {
        "unidad_pk": u.get("unidad_negocio_pk"),
        "unidad_codigo": u.get("codigo"),
        "unidad_nombre": u.get("nombre"),
        "server_id": str(u.get("server_id") or "").lower() or None,
    }


def agg_unidades(metrica: str, desde: str, hasta: str) -> List[Dict]:
    """Valor de la métrica CANÓNICA por unidad (todas las del grupo) en el período.
    Reutiliza KPIsCanonicosService (única fuente de fórmulas; cheque=ticket, etc.)."""
    canon = resolver_metrica(metrica)
    base = KPIsCanonicosService.agregados_por_unidad(desde, hasta)
    out = []
    for a in base:
        out.append({
            "unidad_pk": a["unidad_pk"], "server_id": a["server_id"],
            "unidad_nombre": a["unidad_nombre"], "unidad_codigo": a["unidad_codigo"],
            "valor": KPIsCanonicosService.calcular_metrica(a, canon),
            "ventas": a["ventas"], "cheques": a["cheques"], "pax": a["pax"], "dias": a["dias"],
        })
    return out


def agg_producto_por_unidad(producto_id: str, metrica: str, desde: str, hasta: str) -> List[Dict]:
    """Valor de un producto (por producto_id) en cada unidad del grupo.
    Identidad de unidad resuelta canónicamente por código (UnidadesService)."""
    col = "SUM(CAST(importe_neto AS float))" if metrica == "ventas" else "SUM(CAST(cantidad AS float))"
    sql = f"""
        SELECT unidad_negocio_id AS codigo, {col} AS valor
        FROM dbo.Comercial_Inteligencia_VentasDetalleProducto
        WHERE ISNULL(activo,1)=1 AND producto_id = %s
          AND fecha_operacion >= %s AND fecha_operacion < %s
        GROUP BY unidad_negocio_id
    """
    rows = execute_sql_query_params(*_conn(), sql, (producto_id, desde, hasta))
    out = []
    for r in rows:
        ident = _identidad_por_codigo(r.get("codigo"))
        if not ident:
            continue
        out.append({**ident, "valor": float(r.get("valor") or 0)})
    return out


def top_productos_unidad(unidad_codigo: str, metrica: str, desde: str, hasta: str, top: int) -> List[Dict]:
    """Top N productos de UNA unidad (por ventas o cantidad) en el período."""
    val = "SUM(CAST(importe_neto AS float))" if metrica == "ventas" else "SUM(CAST(cantidad AS float))"
    sql = f"""
        SELECT TOP ({int(top)})
               CONVERT(varchar(36), producto_id) AS producto_id,
               MAX(producto_nombre) AS producto_nombre,
               MAX(familia_nombre) AS familia_nombre,
               MAX(casa) AS casa,
               MAX(CAST(es_alcohol AS int)) AS es_alcohol,
               {val} AS valor,
               SUM(CAST(cantidad AS float)) AS cantidad
        FROM dbo.Comercial_Inteligencia_VentasDetalleProducto
        WHERE ISNULL(activo,1)=1 AND unidad_negocio_id = %s AND producto_id IS NOT NULL
          AND fecha_operacion >= %s AND fecha_operacion < %s
        GROUP BY producto_id
        ORDER BY {val} DESC
    """
    return execute_sql_query_params(*_conn(), sql, (unidad_codigo, desde, hasta))


def cobertura_detalle() -> Dict:
    """Cobertura de la tabla de detalle (para indicadores/diagnóstico)."""
    sql = """
        SELECT unidad_negocio_id AS unidad, COUNT(*) AS lineas,
               CONVERT(varchar(10), MIN(fecha_operacion), 120) AS desde,
               CONVERT(varchar(10), MAX(fecha_operacion), 120) AS hasta
        FROM dbo.Comercial_Inteligencia_VentasDetalleProducto
        GROUP BY unidad_negocio_id
    """
    return {"unidades": execute_sql_query_params(*_conn(), sql, ())}
