"""
CATÁLOGO CANÓNICO (CATALOGO-CANONICO-C2)
========================================
Fuente ÚNICA de la clasificación de productos para TODO el ERP
(Análisis, Costos y Márgenes, Inteligencia Comercial, etc.).

- 100% NO-LIVE: lee EXCLUSIVAMENTE de EDARSAHUB (Sync_Productos). NUNCA consulta
  los POS en vivo (a diferencia del viejo /servers/{id}/report-filters que sí lo hacía).
- Jerarquía canónica unificada: Categoría -> Familia -> Subfamilia/Subgrupo.
  Mapeo interno por sistema (MPRO: Categoría/Familia/Subfamilia;
  SoftRestaurant: Clasificación(=Categoría)/Grupo(=Familia)).
- Filtra internamente por unidad de negocio (RBAC vía resolve_unidad_scope),
  pero la presentación al usuario es idéntica.
"""
from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, Query, HTTPException

from core.security import get_current_user
from core.corporate_filters.request_resolver import resolve_unidad_scope
from modules.costos_margenes.repository import _get_edarsahub_connection
from core.db import execute_sql_query

router = APIRouter(prefix="/catalogo", tags=["Catálogo Canónico"])


def _build_server_filter(servidor_id: Optional[str], servidores_ids: Optional[List[str]]) -> str:
    """Construye el filtro WHERE por servidor (NO-LIVE)."""
    if servidor_id:
        return f"AND ServerID = '{servidor_id}'"
    if servidores_ids:
        ids = ",".join(f"'{s}'" for s in servidores_ids)
        return f"AND ServerID IN ({ids})"
    return ""


@router.get("/clasificacion")
async def obtener_clasificacion(
    current_user: dict = Depends(get_current_user),
    unidad: Optional[str] = Query(None, description="CANÓNICO: unidad de negocio (codigo o id)"),
    server_id: Optional[str] = Query(None, description="DEPRECATED: server_id POS directo (transición)"),
    incluir_inactivos: bool = Query(False, description="Incluir productos de baja/inactivos"),
):
    """
    Devuelve la clasificación canónica (NO-LIVE) lista para alimentar filtros.

    Respuesta compatible con el contrato de filtros de Análisis:
    {
      "categorias":  [{"codigo","nombre"}],
      "familias":    [{"codigo","nombre","categoria_codigo"}],
      "subfamilias": [{"codigo","nombre","familia_codigo"}],
      "source_type": "EDARSAHUB_SQL"
    }
    """
    # Resolución canónica de la unidad -> server scope (RBAC incluido)
    servidor_id = None
    scope = await resolve_unidad_scope(
        current_user,
        unidad=unidad,
        server_id_legacy=server_id,
    )
    if scope.access_denied:
        return {
            "categorias": [],
            "familias": [],
            "subfamilias": [],
            "source_type": "EDARSAHUB_SQL",
        }

    servidor_id = scope.server_id
    servidores_ids = None

    if scope.is_global:
        # Lista vacía significa alcance corporativo sin restricción.
        # Una lista poblada limita la consulta a servidores autorizados.
        servidores_ids = scope.effective_server_ids or None

    server_filter = _build_server_filter(servidor_id, servidores_ids)
    activo_filter = "" if incluir_inactivos else "AND Activo = 1"
    conn = _get_edarsahub_connection()

    categorias_q = f"""
        SELECT DISTINCT CategoriaCodigoFuente AS codigo, CategoriaNombre AS nombre
        FROM Sync_Productos
        WHERE CategoriaNombre IS NOT NULL AND CategoriaNombre != '' {server_filter} {activo_filter}
        ORDER BY CategoriaNombre
    """
    familias_q = f"""
        SELECT DISTINCT FamiliaCodigoFuente AS codigo, FamiliaNombre AS nombre,
               MAX(CategoriaCodigoFuente) AS categoria_codigo
        FROM Sync_Productos
        WHERE FamiliaNombre IS NOT NULL AND FamiliaNombre != '' {server_filter} {activo_filter}
        GROUP BY FamiliaCodigoFuente, FamiliaNombre
        ORDER BY FamiliaNombre
    """
    subfamilias_q = f"""
        SELECT DISTINCT SubFamiliaCodigoFuente AS codigo, SubFamiliaNombre AS nombre,
               MAX(FamiliaCodigoFuente) AS familia_codigo
        FROM Sync_Productos
        WHERE SubFamiliaNombre IS NOT NULL AND SubFamiliaNombre != '' {server_filter} {activo_filter}
        GROUP BY SubFamiliaCodigoFuente, SubFamiliaNombre
        ORDER BY SubFamiliaNombre
    """
    try:
        categorias = execute_sql_query(*conn, categorias_q) or []
        familias = execute_sql_query(*conn, familias_q) or []
        subfamilias = execute_sql_query(*conn, subfamilias_q) or []
        return {
            "categorias": categorias,
            "familias": familias,
            "subfamilias": subfamilias,
            "source_type": "EDARSAHUB_SQL",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo clasificación")
