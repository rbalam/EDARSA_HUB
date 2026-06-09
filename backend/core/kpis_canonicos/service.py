"""
KPIsCanonicosService — definición ÚNICA de los KPIs comerciales.

Las DEFINICIONES viven en SQL (dbo.Comercial_Metricas_Canonicas + _Sinonimos):
administrables, documentables, auditables y versionables. Este servicio solo
INTERPRETA la definición declarativa (operacion='campo'|'ratio') sobre los
átomos base agregados desde dbo.Comercial_KPIs_Diarios_v2:
  ventas, ventas_sin_propina, propinas, cheques, pax.

Ver glosario en core/kpis_canonicos/__init__.py
"""
import logging
import threading
from typing import Dict, List, Optional, Iterable

from core.db import execute_sql_query_params
from core.server_registry import EDARSAHUB_CONFIG
from core.unidades_service import UnidadesService

logger = logging.getLogger(__name__)


def _conn():
    c = EDARSAHUB_CONFIG
    return (c['host'], c['port'], c['database'], c['username'], c['password'])


# Átomos base disponibles (provienen de agregados_por_unidad)
ATOMOS = {"ventas", "ventas_sin_propina", "propinas", "cheques", "pax"}


def _safe_div(n, d):
    return (n / d) if d else None


def aplicar_definicion(agg: Dict, definicion: Dict) -> Optional[float]:
    """Intérprete PURO (testable sin BD): aplica una definición declarativa
    de métrica a un agregado base."""
    op = (definicion.get("operacion") or "").lower()
    if op == "campo":
        return agg.get(definicion["campo_base"])
    if op == "ratio":
        return _safe_div(agg.get(definicion["numerador"]), agg.get(definicion["denominador"]))
    raise ValueError(f"Operación de métrica no soportada: {op}")


# ---------------------------------------------------------------------------
# Catálogo de métricas cargado desde SQL (caché en memoria)
# ---------------------------------------------------------------------------
class _Catalogo:
    _lock = threading.Lock()
    _defs: Optional[Dict[str, Dict]] = None      # codigo -> definición
    _sinonimos: Optional[Dict[str, str]] = None  # alias/codigo -> codigo

    @classmethod
    def cargar(cls, force: bool = False):
        if cls._defs is not None and not force:
            return
        with cls._lock:
            if cls._defs is not None and not force:
                return
            defs = {}
            rows = execute_sql_query_params(
                *_conn(),
                """SELECT codigo, label, descripcion, formato, operacion, campo_base,
                          numerador, denominador, orden, version
                   FROM dbo.Comercial_Metricas_Canonicas WHERE activo=1 ORDER BY orden""",
                (),
            )
            for r in rows:
                defs[r["codigo"]] = dict(r)
            sin = {c: c for c in defs}  # el código es su propio "sinónimo"
            srows = execute_sql_query_params(
                *_conn(),
                "SELECT metrica_codigo, sinonimo FROM dbo.Comercial_Metricas_Sinonimos WHERE activo=1",
                (),
            )
            for r in srows:
                if r["metrica_codigo"] in defs:
                    sin[r["sinonimo"].strip().lower()] = r["metrica_codigo"]
            cls._defs, cls._sinonimos = defs, sin
            logger.info("[KPI-CANON] catálogo cargado: %d métricas, %d sinónimos",
                        len(defs), len(sin))

    @classmethod
    def refrescar(cls):
        cls.cargar(force=True)

    @classmethod
    def defs(cls) -> Dict[str, Dict]:
        cls.cargar()
        return cls._defs

    @classmethod
    def sinonimos(cls) -> Dict[str, str]:
        cls.cargar()
        return cls._sinonimos


def resolver_metrica(nombre: str) -> str:
    """Nombre canónico a partir de cualquier sinónimo (definido en SQL)."""
    key = (nombre or "").strip().lower()
    sin = _Catalogo.sinonimos()
    if key not in sin:
        raise ValueError(f"Métrica no canónica/desconocida: {nombre}")
    return sin[key]


class KPIsCanonicosService:
    """Lee y agrega los KPIs canónicos por unidad (NO-LIVE, SQL-first)."""

    refrescar_catalogo = staticmethod(_Catalogo.refrescar)

    @staticmethod
    def metricas_disponibles() -> List[Dict]:
        """Glosario público desde SQL (para selectores de frontend)."""
        sin = _Catalogo.sinonimos()
        out = []
        for codigo, d in _Catalogo.defs().items():
            alias = sorted([s for s, c in sin.items() if c == codigo and s != codigo])
            out.append({"id": codigo, "label": d["label"], "descripcion": d.get("descripcion"),
                        "formato": d["formato"], "sinonimos": alias})
        return out

    @staticmethod
    def definicion(metrica: str) -> Dict:
        return _Catalogo.defs()[resolver_metrica(metrica)]

    @staticmethod
    def calcular_metrica(agregado: Dict, metrica: str) -> Optional[float]:
        """Aplica la fórmula CANÓNICA (definida en SQL) de `metrica` (o sinónimo)."""
        return aplicar_definicion(agregado, KPIsCanonicosService.definicion(metrica))

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
        Átomos base canónicos por unidad en [desde, hasta):
        {unidad_pk, unidad_codigo, unidad_nombre, server_id,
         ventas, ventas_sin_propina, propinas, cheques, pax, dias}
        Identidad resuelta SIEMPRE desde el catálogo canónico (UnidadesService).
        """
        sql = """
            SELECT CONVERT(varchar(36), unidad_negocio_pk) AS unidad_pk,
                   SUM(CAST(ventas_total AS float))       AS ventas,
                   SUM(CAST(ventas_sin_propina AS float)) AS ventas_sin_propina,
                   SUM(CAST(propinas_total AS float))     AS propinas,
                   SUM(CAST(tickets_total AS float))      AS cheques,
                   SUM(CAST(pax_total AS float))          AS pax,
                   COUNT(DISTINCT fecha_operacion)        AS dias
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
                        "ventas_sin_propina": float(r.get("ventas_sin_propina") or 0),
                        "propinas": float(r.get("propinas") or 0),
                        "cheques": float(r.get("cheques") or 0),
                        "pax": float(r.get("pax") or 0),
                        "dias": r.get("dias")})
        return out

    @staticmethod
    def kpis_por_unidad(desde: str, hasta: str,
                        unidad_pks: Optional[Iterable[str]] = None) -> List[Dict]:
        """Agregados + TODAS las métricas canónicas calculadas, por unidad."""
        base = KPIsCanonicosService.agregados_por_unidad(desde, hasta, unidad_pks)
        defs = _Catalogo.defs()
        for a in base:
            a["metricas"] = {cod: aplicar_definicion(a, d) for cod, d in defs.items()}
        return base
