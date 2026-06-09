"""
InsumosService - Servicio CANÓNICO de Insumos (NO-LIVE)
=======================================================
Fuente única: dbo.Sync_Productos_Insumos (insumos sincronizados de EDARSAHUB).
Centraliza el acceso a insumos usado en recetas, costos, auditoría de compras
y análisis de inventarios (regla de centralización).

NO-LIVE: lee EXCLUSIVAMENTE de EDARSAHUB SQL.
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
        CONVERT(varchar(36), InsumoID) AS insumo_id,
        CONVERT(varchar(36), ServerID) AS server_id,
        SystemType AS system_type,
        CodigoFuente AS codigo_fuente,
        Nombre AS nombre,
        Descripcion AS descripcion,
        GrupoInsumoCodigoFuente AS grupo_insumo_codigo,
        GrupoInsumoNombre AS grupo_insumo_nombre,
        UnidadMedida AS unidad_medida,
        Costo AS costo,
        CostoPromedio AS costo_promedio,
        UltimoCosto AS ultimo_costo,
        EsElaborado AS es_elaborado,
        RendimientoElaborado AS rendimiento_elaborado,
        MermaPorcentaje AS merma_porcentaje,
        Activo AS activo
"""


class InsumosService:
    """Acceso canónico de solo-lectura al catálogo de insumos."""

    @staticmethod
    def get_by_id(insumo_id) -> Optional[Dict]:
        if not insumo_id:
            return None
        sql = f"SELECT {_COLS} FROM dbo.Sync_Productos_Insumos WHERE CAST(InsumoID AS char(36)) = %s"
        rows = execute_sql_query_params(*_conn(), sql, (str(insumo_id),))
        return rows[0] if rows else None

    @staticmethod
    def get_by_codigo(server_id, codigo_fuente) -> Optional[Dict]:
        if not (server_id and codigo_fuente):
            return None
        sql = (f"SELECT {_COLS} FROM dbo.Sync_Productos_Insumos "
               "WHERE CAST(ServerID AS char(36)) = %s AND CodigoFuente = %s")
        rows = execute_sql_query_params(*_conn(), sql, (str(server_id), str(codigo_fuente)))
        return rows[0] if rows else None

    @staticmethod
    def listar(
        server_ids: Optional[List[str]] = None,
        busqueda: Optional[str] = None,
        grupo: Optional[str] = None,
        activo: Optional[bool] = True,
        limit: Optional[int] = None,
    ) -> List[Dict]:
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
        if grupo:
            where.append("GrupoInsumoNombre LIKE %s")
            params.append(f"%{grupo}%")
        top = f"TOP {int(limit)} " if limit else ""
        where_sql = (" WHERE " + " AND ".join(where)) if where else ""
        sql = f"SELECT {top}{_COLS} FROM dbo.Sync_Productos_Insumos{where_sql} ORDER BY Nombre"
        try:
            return execute_sql_query_params(*_conn(), sql, tuple(params))
        except Exception as e:
            logger.error(f"[INSUMOS_SERVICE] Error en listar: {e}")
            return []
