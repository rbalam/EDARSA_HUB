"""
Benchmark Sectorial - Servicio de agregacion (SOLO LECTURA, NO-LIVE)
=====================================================================
Genera el reporte de Benchmark Sectorial a partir de tablas canonicas
existentes en EDARSAHUB (sin hardcodear datos, sin consultas en vivo):

Fuentes:
- Nuestros precios de venta: dbo.Sync_Productos (PrecioVenta, CategoriaNombre)
  vinculados a la empresa comercial via dbo.Sistema_EmpresasServidores
  (EmpresaID int -> ServidorID GUID -> Sync_Productos.ServerID).
- Precios de competencia: dbo.Comercial_CompetidoresMenuItems
  (Precio, CategoriaCompetidor) JOIN dbo.Comercial_Competidores
  (TipoRestaurante = giro, SegmentoPrecio = segmento, ZonaComercial).

Vistas:
- A "vs_sector": nuestra unidad vs promedio del sector (todos los competidores).
- B "interno": comparativa entre nuestras propias unidades (empresas comerciales).
- C "por_segmento": nuestra unidad vs promedio por segmento de precio.

Metrica principal: % de desviacion del precio propio vs el promedio sectorial,
por categoria de producto. Estados honestos cuando no hay datos suficientes.
"""

from typing import Optional, List, Dict, Any, Tuple
import logging

from core.db import execute_sql_query_params
from core.server_registry import EDARSAHUB_CONFIG

logger = logging.getLogger(__name__)


def _conn() -> Tuple:
    return (
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password'],
    )


def _q(query: str, params: tuple = ()) -> List[Dict]:
    return execute_sql_query_params(*_conn(), query, params)


def _desviacion(propio: Optional[float], referencia: Optional[float]) -> Optional[float]:
    """% desviacion del precio propio respecto a la referencia sectorial."""
    if propio is None or referencia is None or referencia == 0:
        return None
    return round((propio - referencia) / referencia * 100.0, 1)


def _semaforo(desviacion_pct: Optional[float], umbral_pct: float) -> Dict[str, Any]:
    """Clasifica la oportunidad de precio por categoria segun la desviacion vs sector.

    - desviacion > +umbral  -> CARO (por encima del sector; candidato a revisar/bajar)
    - desviacion < -umbral  -> BARATO (por debajo del sector; oportunidad de subir precio)
    - en el rango           -> ALINEADO
    """
    if desviacion_pct is None:
        return {"oportunidad": "SIN_DATO", "semaforo": "gris", "accion_sugerida": None}
    if desviacion_pct > umbral_pct:
        return {"oportunidad": "CARO", "semaforo": "rojo",
                "accion_sugerida": "Revisar: tu precio esta por encima del sector"}
    if desviacion_pct < -umbral_pct:
        return {"oportunidad": "BARATO", "semaforo": "verde",
                "accion_sugerida": "Oportunidad: podrias subir precio hacia el sector"}
    return {"oportunidad": "ALINEADO", "semaforo": "ambar" if abs(desviacion_pct) > umbral_pct / 2 else "verde",
            "accion_sugerida": None}


# ---------------------------------------------------------------------------
# Catalogos / mapeos canonicos (derivados, sin hardcode)
# ---------------------------------------------------------------------------

def _mapa_empresas() -> Dict[int, str]:
    """EmpresaID (comercial) -> nombre de la unidad/sucursal canonica."""
    rows = _q(
        """
        SELECT EmpresaID, MAX(NombreSucursalSistema) AS nombre
        FROM Sistema_EmpresasServidores
        WHERE Activo = 1 AND RolConexion = 'PRINCIPAL_SQL'
        GROUP BY EmpresaID
        ORDER BY EmpresaID
        """
    )
    return {int(r['EmpresaID']): (r.get('nombre') or f"Empresa {r['EmpresaID']}") for r in rows}


def _nuestros_precios_por_categoria(empresa_id: int) -> List[Dict]:
    """Promedio de PrecioVenta por categoria para una empresa comercial."""
    return _q(
        """
        SELECT UPPER(LTRIM(RTRIM(sp.CategoriaNombre))) AS categoria,
               AVG(CAST(sp.PrecioVenta AS FLOAT)) AS precio_prom,
               MIN(CAST(sp.PrecioVenta AS FLOAT)) AS precio_min,
               MAX(CAST(sp.PrecioVenta AS FLOAT)) AS precio_max,
               COUNT(*) AS n_productos
        FROM Sync_Productos sp
        JOIN Sistema_EmpresasServidores ses ON sp.ServerID = ses.ServidorID
        WHERE ses.EmpresaID = %s AND ses.RolConexion = 'PRINCIPAL_SQL' AND ses.Activo = 1
          AND sp.EsVendible = 1 AND sp.Activo = 1 AND sp.PrecioVenta > 0
          AND sp.CategoriaNombre IS NOT NULL AND LTRIM(RTRIM(sp.CategoriaNombre)) <> ''
        GROUP BY UPPER(LTRIM(RTRIM(sp.CategoriaNombre)))
        """,
        (empresa_id,),
    )


def _competidor_precios_por_categoria(
    empresa_id: int, unidad_negocio_pk: Optional[int],
    segmento: Optional[str], giro: Optional[str],
) -> List[Dict]:
    """Promedio de precios de competencia por categoria (con filtros opcionales)."""
    where = [
        "c.EmpresaID = %s", "c.Activo = 1", "mi.Activo = 1", "mi.Precio > 0",
        "mi.CategoriaCompetidor IS NOT NULL", "LTRIM(RTRIM(mi.CategoriaCompetidor)) <> ''",
    ]
    params: List[Any] = [empresa_id]
    if unidad_negocio_pk is not None:
        where.append("c.UnidadNegocioID = %s")
        params.append(unidad_negocio_pk)
    if segmento:
        where.append("c.SegmentoPrecio = %s")
        params.append(segmento)
    if giro:
        where.append("c.TipoRestaurante = %s")
        params.append(giro)
    return _q(
        f"""
        SELECT UPPER(LTRIM(RTRIM(mi.CategoriaCompetidor))) AS categoria,
               AVG(CAST(mi.Precio AS FLOAT)) AS precio_prom,
               MIN(CAST(mi.Precio AS FLOAT)) AS precio_min,
               MAX(CAST(mi.Precio AS FLOAT)) AS precio_max,
               COUNT(*) AS n_items,
               COUNT(DISTINCT c.CompetidorID) AS n_competidores
        FROM Comercial_CompetidoresMenuItems mi
        JOIN Comercial_Competidores c ON mi.CompetidorID = c.CompetidorID
        WHERE {' AND '.join(where)}
        GROUP BY UPPER(LTRIM(RTRIM(mi.CategoriaCompetidor)))
        """,
        tuple(params),
    )


# ---------------------------------------------------------------------------
# Vista A: nuestra unidad vs promedio del sector
# ---------------------------------------------------------------------------

def vista_vs_sector(empresa_id: int, unidad_negocio_pk: Optional[int],
                    segmento: Optional[str], giro: Optional[str],
                    umbral_pct: float = 15.0) -> Dict[str, Any]:
    nuestros = {r['categoria']: r for r in _nuestros_precios_por_categoria(empresa_id)}
    comp = {r['categoria']: r for r in _competidor_precios_por_categoria(
        empresa_id, unidad_negocio_pk, segmento, giro)}

    categorias = sorted(set(nuestros) | set(comp))
    filas = []
    for cat in categorias:
        n = nuestros.get(cat)
        c = comp.get(cat)
        mi_prom = round(n['precio_prom'], 2) if n else None
        sector_prom = round(c['precio_prom'], 2) if c else None
        if n and c:
            estado = "COMPARABLE"
        elif n and not c:
            estado = "SIN_DATO_COMPETENCIA"
        else:
            estado = "SIN_PRODUCTO_PROPIO"
        desv = _desviacion(mi_prom, sector_prom)
        sem = _semaforo(desv, umbral_pct) if estado == "COMPARABLE" else {
            "oportunidad": "SIN_DATO", "semaforo": "gris", "accion_sugerida": None}
        filas.append({
            "categoria": cat,
            "mi_precio_prom": mi_prom,
            "n_productos_propios": n['n_productos'] if n else 0,
            "sector_precio_prom": sector_prom,
            "sector_precio_min": round(c['precio_min'], 2) if c else None,
            "sector_precio_max": round(c['precio_max'], 2) if c else None,
            "n_items_competencia": c['n_items'] if c else 0,
            "n_competidores": c['n_competidores'] if c else 0,
            "desviacion_pct": desv,
            "estado": estado,
            **sem,
        })

    comparables = [f for f in filas if f['estado'] == 'COMPARABLE']
    estado_global = "OK" if comparables else ("SIN_DATOS_COMPETENCIA" if nuestros else "SIN_DATOS")
    return {
        "vista": "vs_sector",
        "empresa_id": empresa_id,
        "unidad_negocio_pk": unidad_negocio_pk,
        "filtro_segmento": segmento,
        "filtro_giro": giro,
        "umbral_pct": umbral_pct,
        "fuente": "Sync_Productos + Comercial_CompetidoresMenuItems (NO-LIVE)",
        "estado": estado_global,
        "total_categorias": len(filas),
        "categorias_comparables": len(comparables),
        "oportunidades": {
            "caro": len([f for f in comparables if f['oportunidad'] == 'CARO']),
            "barato": len([f for f in comparables if f['oportunidad'] == 'BARATO']),
            "alineado": len([f for f in comparables if f['oportunidad'] == 'ALINEADO']),
        },
        "filas": filas,
    }


# ---------------------------------------------------------------------------
# Vista B: comparativa interna entre nuestras unidades
# ---------------------------------------------------------------------------

def vista_interno() -> Dict[str, Any]:
    empresas = _mapa_empresas()
    # precios por categoria de cada empresa comercial
    por_cat: Dict[str, Dict[int, Dict]] = {}
    for emp_id in empresas:
        for r in _nuestros_precios_por_categoria(emp_id):
            cat = r['categoria']
            por_cat.setdefault(cat, {})[emp_id] = r

    filas = []
    for cat in sorted(por_cat):
        unidades_data = por_cat[cat]
        precios = [d['precio_prom'] for d in unidades_data.values() if d['precio_prom'] is not None]
        if not precios:
            continue
        promedio_interno = round(sum(precios) / len(precios), 2)
        unidades = []
        for emp_id, d in sorted(unidades_data.items()):
            p = round(d['precio_prom'], 2)
            unidades.append({
                "empresa_id": emp_id,
                "unidad": empresas.get(emp_id, f"Empresa {emp_id}"),
                "precio_prom": p,
                "n_productos": d['n_productos'],
                "desviacion_vs_interno_pct": _desviacion(p, promedio_interno),
            })
        filas.append({
            "categoria": cat,
            "promedio_interno": promedio_interno,
            "precio_min": round(min(precios), 2),
            "precio_max": round(max(precios), 2),
            "n_unidades": len(unidades),
            "unidades": unidades,
        })

    return {
        "vista": "interno",
        "fuente": "Sync_Productos via Sistema_EmpresasServidores (NO-LIVE)",
        "estado": "OK" if filas else "SIN_DATOS",
        "unidades_evaluadas": [{"empresa_id": k, "unidad": v} for k, v in empresas.items()],
        "total_categorias": len(filas),
        "filas": filas,
    }


# ---------------------------------------------------------------------------
# Vista C: nuestra unidad vs promedio por segmento de precio
# ---------------------------------------------------------------------------

def vista_por_segmento(empresa_id: int, unidad_negocio_pk: Optional[int]) -> Dict[str, Any]:
    nuestros = {r['categoria']: r for r in _nuestros_precios_por_categoria(empresa_id)}

    # segmentos disponibles para esa empresa
    seg_rows = _q(
        """
        SELECT DISTINCT c.SegmentoPrecio AS segmento
        FROM Comercial_Competidores c
        WHERE c.EmpresaID = %s AND c.Activo = 1 AND c.SegmentoPrecio IS NOT NULL
        """,
        (empresa_id,),
    )
    segmentos = sorted([r['segmento'] for r in seg_rows if r.get('segmento')])

    # precio competencia por categoria y segmento
    comp_seg: Dict[str, Dict[str, Dict]] = {}  # segmento -> categoria -> row
    for seg in segmentos:
        comp_seg[seg] = {r['categoria']: r for r in _competidor_precios_por_categoria(
            empresa_id, unidad_negocio_pk, seg, None)}

    categorias = sorted(set(nuestros) | {cat for seg in comp_seg.values() for cat in seg})
    filas = []
    for cat in categorias:
        n = nuestros.get(cat)
        mi_prom = round(n['precio_prom'], 2) if n else None
        por_segmento = []
        for seg in segmentos:
            c = comp_seg[seg].get(cat)
            sector_prom = round(c['precio_prom'], 2) if c else None
            por_segmento.append({
                "segmento": seg,
                "sector_precio_prom": sector_prom,
                "n_items": c['n_items'] if c else 0,
                "desviacion_pct": _desviacion(mi_prom, sector_prom),
            })
        filas.append({
            "categoria": cat,
            "mi_precio_prom": mi_prom,
            "n_productos_propios": n['n_productos'] if n else 0,
            "por_segmento": por_segmento,
        })

    return {
        "vista": "por_segmento",
        "empresa_id": empresa_id,
        "unidad_negocio_pk": unidad_negocio_pk,
        "fuente": "Sync_Productos + Comercial_CompetidoresMenuItems por SegmentoPrecio (NO-LIVE)",
        "estado": "OK" if (segmentos and nuestros) else "SIN_DATOS",
        "segmentos": segmentos,
        "total_categorias": len(filas),
        "filas": filas,
    }


# ---------------------------------------------------------------------------
# Catalogo de sectores disponibles (para los filtros del frontend)
# ---------------------------------------------------------------------------

def sectores_disponibles(empresa_id: int) -> Dict[str, Any]:
    rows = _q(
        """
        SELECT c.TipoRestaurante AS giro, c.SegmentoPrecio AS segmento,
               c.ZonaComercial AS zona, COUNT(*) AS n
        FROM Comercial_Competidores c
        WHERE c.EmpresaID = %s AND c.Activo = 1
        GROUP BY c.TipoRestaurante, c.SegmentoPrecio, c.ZonaComercial
        """,
        (empresa_id,),
    )
    giros = sorted({r['giro'] for r in rows if r.get('giro')})
    segmentos = sorted({r['segmento'] for r in rows if r.get('segmento')})
    zonas = sorted({r['zona'] for r in rows if r.get('zona')})
    total_competidores = _q(
        "SELECT COUNT(*) AS n FROM Comercial_Competidores WHERE EmpresaID = %s AND Activo = 1",
        (empresa_id,),
    )
    return {
        "empresa_id": empresa_id,
        "giros": giros,
        "segmentos": segmentos,
        "zonas": zonas,
        "total_competidores": (total_competidores[0]['n'] if total_competidores else 0),
    }
