"""
ProductosService - Servicio CANÓNICO de Productos (NO-LIVE)
===========================================================
Fuente única: dbo.Sync_Productos (catálogo sincronizado de EDARSAHUB).
Centraliza el acceso al catálogo de productos usado en múltiples menús
(Compras, Auditoría, Análisis, Costos/Márgenes, Precios, Comercial, Inteligencia)
para evitar consultas SQL duplicadas (regla de centralización).

NO-LIVE: nunca consulta POS en vivo. Lee EXCLUSIVAMENTE de EDARSAHUB SQL.
Patrón espejo de core.unidades_service / costos_margenes.repository.
"""
import logging
from typing import Optional, List, Dict

from core.db import execute_sql_query_params
from core.server_registry import EDARSAHUB_CONFIG

logger = logging.getLogger(__name__)


def _conn():
    c = EDARSAHUB_CONFIG
    return (c['host'], c['port'], c['database'], c['username'], c['password'])


_COLS = """
        CONVERT(varchar(36), ProductoID) AS producto_id,
        CONVERT(varchar(36), ServerID) AS server_id,
        SystemType AS system_type,
        CodigoFuente AS codigo_fuente,
        CodigoBarras AS codigo_barras,
        Nombre AS nombre,
        NombreCorto AS nombre_corto,
        CategoriaCodigoFuente AS categoria_codigo,
        CategoriaNombre AS categoria_nombre,
        FamiliaCodigoFuente AS familia_codigo,
        FamiliaNombre AS familia_nombre,
        SubFamiliaCodigoFuente AS subfamilia_codigo,
        SubFamiliaNombre AS subfamilia_nombre,
        TipoProducto AS tipo_producto,
        EsVendible AS es_vendible,
        EsInventariable AS es_inventariable,
        TieneReceta AS tiene_receta,
        PrecioVenta AS precio_venta,
        CostoReceta AS costo_receta,
        Activo AS activo
"""


class ProductosService:
    """Acceso canónico de solo-lectura al catálogo de productos."""

    @staticmethod
    def get_by_id(producto_id) -> Optional[Dict]:
        """Producto por ProductoID (UNIQUEIDENTIFIER canónico)."""
        if not producto_id:
            return None
        sql = f"SELECT {_COLS} FROM dbo.Sync_Productos WHERE CAST(ProductoID AS char(36)) = %s"
        rows = execute_sql_query_params(*_conn(), sql, (str(producto_id),))
        return rows[0] if rows else None

    @staticmethod
    def get_by_codigo(server_id, codigo_fuente) -> Optional[Dict]:
        """Producto por ServerID + CodigoFuente (clave operativa del POS)."""
        if not (server_id and codigo_fuente):
            return None
        sql = (f"SELECT {_COLS} FROM dbo.Sync_Productos "
               "WHERE CAST(ServerID AS char(36)) = %s AND CodigoFuente = %s")
        rows = execute_sql_query_params(*_conn(), sql, (str(server_id), str(codigo_fuente)))
        return rows[0] if rows else None

    @staticmethod
    def listar(
        server_ids: Optional[List[str]] = None,
        busqueda: Optional[str] = None,
        familia: Optional[str] = None,
        subfamilia: Optional[str] = None,
        categoria: Optional[str] = None,
        solo_vendibles: bool = False,
        solo_con_receta: bool = False,
        activo: Optional[bool] = True,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """Lista de productos con filtros canónicos (parametrizados)."""
        where: List[str] = []
        params: List = []
        if activo is True:
            where.append("Activo = 1")
        elif activo is False:
            where.append("Activo = 0")
        if server_ids:
            ph = ",".join(["%s"] * len(server_ids))
            where.append(f"CAST(ServerID AS char(36)) IN ({ph})")
            params += [str(s) for s in server_ids]
        if busqueda:
            where.append("(Nombre LIKE %s OR CodigoFuente LIKE %s)")
            params += [f"%{busqueda}%", f"%{busqueda}%"]
        if familia:
            where.append("FamiliaNombre LIKE %s")
            params.append(f"%{familia}%")
        if subfamilia:
            where.append("SubFamiliaNombre LIKE %s")
            params.append(f"%{subfamilia}%")
        if categoria:
            where.append("CategoriaCodigoFuente = %s")
            params.append(str(categoria))
        if solo_vendibles:
            where.append("EsVendible = 1")
        if solo_con_receta:
            where.append("TieneReceta = 1")

        top = f"TOP {int(limit)} " if limit else ""
        where_sql = (" WHERE " + " AND ".join(where)) if where else ""
        sql = f"SELECT {top}{_COLS} FROM dbo.Sync_Productos{where_sql} ORDER BY Nombre"
        try:
            return execute_sql_query_params(*_conn(), sql, tuple(params))
        except Exception as e:
            logger.error(f"[PRODUCTOS_SERVICE] Error en listar: {e}")
            return []

    @staticmethod
    def contar(server_ids: Optional[List[str]] = None, activo: Optional[bool] = True) -> int:
        """Conteo de productos (para indicadores/validaciones)."""
        where: List[str] = []
        params: List = []
        if activo is True:
            where.append("Activo = 1")
        elif activo is False:
            where.append("Activo = 0")
        if server_ids:
            ph = ",".join(["%s"] * len(server_ids))
            where.append(f"CAST(ServerID AS char(36)) IN ({ph})")
            params += [str(s) for s in server_ids]
        where_sql = (" WHERE " + " AND ".join(where)) if where else ""
        rows = execute_sql_query_params(
            *_conn(), f"SELECT COUNT(*) AS n FROM dbo.Sync_Productos{where_sql}", tuple(params)
        )
        return int(rows[0]["n"]) if rows else 0
