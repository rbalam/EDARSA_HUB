"""
KPIsCanonicosService — definición única de los KPIs comerciales.
Ver glosario en core/kpis_canonicos/__init__.py
"""
import logging
from typing import Dict, List, Optional, Iterable

from core.db import execute_sql_query_params
from core.server_registry import EDARSAHUB_CONFIG
from core.unidades_service import UnidadesService

logger = logging.getLogger(__name__)


def _conn():
    c = EDARSAHUB_CONFIG
    return (c['host'], c['port'], c['database'], c['username'], c['password'])


# ---------------------------------------------------------------------------
# GLOSARIO CANÓNICO DE MÉTRICAS (única fuente de verdad de las fórmulas)
# Cada métrica se calcula a partir de los agregados base: ventas, cheques, pax.
# `sinonimos` permite que distintos menús usen su nombre histórico sin duplicar.
# ---------------------------------------------------------------------------
METRICAS_CANONICAS: Dict[str, Dict] = {
    "ventas": {
        "label": "Ventas (neto)",
        "sinonimos": ["venta_neta", "venta_total", "ventas_total"],
        "formato": "moneda",
        "fn": lambda a: a["ventas"],
    },
    "cheques": {
        "label": "Cheques",
        "sinonimos": ["tickets", "comandas", "cuentas", "tickets_total"],
        "formato": "entero",
        "fn": lambda a: a["cheques"],
    },
    "cheque_promedio": {
        "label": "Cheque promedio",
        "sinonimos": ["ticket_promedio", "ticket_medio", "cheque_medio"],
        "formato": "moneda",
        "fn": lambda a: (a["ventas"] / a["cheques"]) if a["cheques"] else None,
    },
    "pax": {
        "label": "PAX (comensales)",
        "sinonimos": ["comensales", "pax_total"],
        "formato": "entero",
        "fn": lambda a: a["pax"],
    },
    "venta_por_pax": {
        "label": "Venta por PAX",
        "sinonimos": ["consumo_per_capita", "venta_pax"],
        "formato": "moneda",
        "fn": lambda a: (a["ventas"] / a["pax"]) if a["pax"] else None,
    },
    "cheques_por_pax": {
        "label": "Cheques por PAX",
        "sinonimos": ["rotacion_por_comensal"],
        "formato": "decimal",
        "fn": lambda a: (a["cheques"] / a["pax"]) if a["pax"] else None,
    },
}

# Índice inverso sinónimo -> métrica canónica
_SINONIMOS = {}
for _canon, _meta in METRICAS_CANONICAS.items():
    _SINONIMOS[_canon] = _canon
    for _s in _meta["sinonimos"]:
        _SINONIMOS[_s] = _canon


def resolver_metrica(nombre: str) -> str:
    """Devuelve el nombre canónico de una métrica a partir de cualquier sinónimo."""
    key = (nombre or "").strip().lower()
    if key not in _SINONIMOS:
        raise ValueError(f"Métrica no canónica/desconocida: {nombre}")
    return _SINONIMOS[key]


class KPIsCanonicosService:
    """Lee y agrega los KPIs canónicos por unidad (NO-LIVE, SQL-first)."""

    @staticmethod
    def metricas_disponibles() -> List[Dict]:
        """Glosario público (para selectores de frontend, sin duplicar fórmulas)."""
        return [
            {"id": k, "label": v["label"], "formato": v["formato"], "sinonimos": v["sinonimos"]}
            for k, v in METRICAS_CANONICAS.items()
        ]

    @staticmethod
    def _identidad(pk: Optional[str]) -> Optional[Dict]:
        u = UnidadesService.get_by_pk(pk) if pk else None
        if not u:
            return None
        return {
            "unidad_pk": u.get("unidad_negocio_pk"),
            "unidad_codigo": u.get("codigo"),
            "unidad_nombre": u.get("nombre"),
            "server_id": str(u.get("server_id") or "").lower() or None,
        }

    @staticmethod
    def agregados_por_unidad(desde: str, hasta: str,
                             unidad_pks: Optional[Iterable[str]] = None) -> List[Dict]:
        """
        Agregados base canónicos por unidad en [desde, hasta):
        {unidad_pk, unidad_codigo, unidad_nombre, server_id, ventas, cheques, pax, dias}
        Identidad resuelta SIEMPRE desde el catálogo canónico (UnidadesService).
        """
        sql = """
            SELECT CONVERT(varchar(36), unidad_negocio_pk) AS unidad_pk,
                   SUM(CAST(ventas_total AS float))  AS ventas,
                   SUM(CAST(tickets_total AS float)) AS cheques,
                   SUM(CAST(pax_total AS float))     AS pax,
                   COUNT(DISTINCT fecha_operacion)   AS dias
            FROM dbo.Comercial_KPIs_Diarios_v2
            WHERE ISNULL(activo,1)=1 AND ISNULL(es_demo,0)=0
              AND unidad_negocio_pk IS NOT NULL
              AND fecha_operacion >= %s AND fecha_operacion < %s
            GROUP BY CONVERT(varchar(36), unidad_negocio_pk)
            HAVING SUM(CAST(tickets_total AS float)) > 0
        """
        rows = execute_sql_query_params(*_conn(), sql, (desde, hasta))
        pk_filter = {str(p) for p in unidad_pks} if unidad_pks else None
        out = []
        for r in rows:
            if pk_filter and str(r["unidad_pk"]) not in pk_filter:
                continue
            ident = KPIsCanonicosService._identidad(r["unidad_pk"])
            if not ident:
                logger.warning("[KPI-CANON] PK %s no está en catálogo; omitida", r["unidad_pk"])
                continue
            out.append({**ident,
                        "ventas": float(r.get("ventas") or 0),
                        "cheques": float(r.get("cheques") or 0),
                        "pax": float(r.get("pax") or 0),
                        "dias": r.get("dias")})
        return out

    @staticmethod
    def calcular_metrica(agregado: Dict, metrica: str) -> Optional[float]:
        """Aplica la fórmula canónica de `metrica` (o sinónimo) a un agregado base."""
        canon = resolver_metrica(metrica)
        return METRICAS_CANONICAS[canon]["fn"](agregado)

    @staticmethod
    def kpis_por_unidad(desde: str, hasta: str,
                        unidad_pks: Optional[Iterable[str]] = None) -> List[Dict]:
        """Agregados + TODAS las métricas canónicas calculadas, por unidad."""
        base = KPIsCanonicosService.agregados_por_unidad(desde, hasta, unidad_pks)
        for a in base:
            a["metricas"] = {k: METRICAS_CANONICAS[k]["fn"](a) for k in METRICAS_CANONICAS}
        return base
