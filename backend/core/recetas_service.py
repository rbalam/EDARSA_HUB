"""
RecetasService - Servicio CANÓNICO de Recetas / Explosión de Insumos (NO-LIVE)
==============================================================================
Fuente única: dbo.Sync_Productos_Recetas (receta ya aplanada a NivelExplosion=1
por el proceso de sincronización; cada fila = un componente INSUMO con su
Cantidad por unidad de producto vendido).

Centraliza el acceso a la composición de productos usado en Costos/Márgenes,
Auditoría de compras, Análisis de inventarios e Inteligencia comercial
(regla de centralización: una sola verdad de receta/costo).

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
        CONVERT(varchar(36), RecetaDetalleID) AS receta_detalle_id,
        CONVERT(varchar(36), ProductoID) AS producto_id,
        CONVERT(varchar(36), ServerID) AS server_id,
        SystemType AS system_type,
        ProductoCodigoFuente AS producto_codigo_fuente,
        CONVERT(varchar(36), InsumoID) AS insumo_id,
        CONVERT(varchar(36), SubRecetaProductoID) AS subreceta_producto_id,
        ComponenteCodigoFuente AS componente_codigo_fuente,
        ComponenteNombre AS componente_nombre,
        TipoComponente AS tipo_componente,
        Cantidad AS cantidad,
        UnidadMedida AS unidad_medida,
        CostoUnitario AS costo_unitario,
        CostoTotal AS costo_total,
        NivelExplosion AS nivel_explosion,
        EsElaborado AS es_elaborado,
        RendimientoElaborado AS rendimiento_elaborado
"""


class RecetasService:
    """Acceso canónico de solo-lectura a la composición (receta) de productos."""

    @staticmethod
    def get_componentes(server_id, producto_codigo_fuente) -> List[Dict]:
        """Componentes de la receta por ServerID + CodigoFuente del producto."""
        if not (server_id and producto_codigo_fuente):
            return []
        sql = (f"SELECT {_COLS} FROM dbo.Sync_Productos_Recetas "
               "WHERE CAST(ServerID AS char(36)) = %s AND ProductoCodigoFuente = %s "
               "AND ISNULL(Activo, 1) = 1 ORDER BY OrdenVisual")
        try:
            return execute_sql_query_params(
                *_conn(), sql, (str(server_id), str(producto_codigo_fuente))
            )
        except Exception as e:
            logger.error(f"[RECETAS_SERVICE] Error get_componentes: {e}")
            return []

    @staticmethod
    def get_componentes_bulk(
        server_id,
        producto_codigos_fuente: List[str],
        chunk_size: int = 400,
    ) -> List[Dict]:
        """
        Componentes de varias recetas en lecturas acotadas.

        Mantiene la misma fuente canónica que get_componentes(), pero evita
        N round-trips cuando un análisis necesita explotar cientos de ventas.
        """
        server_id = str(server_id or "").strip()
        codigos = list(dict.fromkeys(
            str(code or "").strip()
            for code in (producto_codigos_fuente or [])
            if str(code or "").strip()
        ))
        if not server_id or not codigos:
            return []

        size = max(1, min(int(chunk_size or 400), 800))
        rows: List[Dict] = []

        for offset in range(0, len(codigos), size):
            chunk = codigos[offset:offset + size]
            placeholders = ",".join(["%s"] * len(chunk))
            sql = (
                f"SELECT {_COLS} FROM dbo.Sync_Productos_Recetas "
                "WHERE CAST(ServerID AS char(36)) = %s "
                f"AND ProductoCodigoFuente IN ({placeholders}) "
                "AND ISNULL(Activo, 1) = 1 "
                "ORDER BY ProductoCodigoFuente, OrdenVisual"
            )
            try:
                rows.extend(
                    execute_sql_query_params(
                        *_conn(),
                        sql,
                        tuple([server_id, *chunk]),
                    )
                    or []
                )
            except Exception as exc:
                logger.error(
                    "[RECETAS_SERVICE] Error get_componentes_bulk: %s",
                    exc,
                )
                return []

        return rows

    @staticmethod
    def get_componentes_by_producto_id(producto_id) -> List[Dict]:
        """Componentes de la receta por ProductoID (UNIQUEIDENTIFIER)."""
        if not producto_id:
            return []
        sql = (f"SELECT {_COLS} FROM dbo.Sync_Productos_Recetas "
               "WHERE CAST(ProductoID AS char(36)) = %s AND ISNULL(Activo, 1) = 1 "
               "ORDER BY OrdenVisual")
        try:
            return execute_sql_query_params(*_conn(), sql, (str(producto_id),))
        except Exception as e:
            logger.error(f"[RECETAS_SERVICE] Error get_componentes_by_producto_id: {e}")
            return []

    @staticmethod
    def get_costo_total(server_id, producto_codigo_fuente) -> float:
        """Costo total de la receta = SUM(CostoTotal) de sus componentes.

        Es la fuente canónica de costo de receta (la misma que usa Costos/Márgenes),
        preferida sobre Sync_Productos.CostoReceta cuando hay receta cargada.
        """
        if not (server_id and producto_codigo_fuente):
            return 0.0
        sql = ("SELECT SUM(CostoTotal) AS costo FROM dbo.Sync_Productos_Recetas "
               "WHERE CAST(ServerID AS char(36)) = %s AND ProductoCodigoFuente = %s "
               "AND ISNULL(Activo, 1) = 1")
        try:
            rows = execute_sql_query_params(
                *_conn(), sql, (str(server_id), str(producto_codigo_fuente))
            )
            val = rows[0]["costo"] if rows else None
            return float(val) if val is not None else 0.0
        except Exception as e:
            logger.error(f"[RECETAS_SERVICE] Error get_costo_total: {e}")
            return 0.0
