"""
EDARSA HUB - Tablajería Dashboard Service
==========================================
Servicio para análisis de rendimientos, KPIs y reportes de tablajería.

Ubicación ERP: 06. Tablajería / Producción y Transformación / Dashboard
Fuente de verdad: EDARSAHUB SQL Server
"""

import pymssql
import os
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class TablajeriaDashboardService:
    """Servicio de dashboard y analytics para Tablajería."""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
    
    def _get_connection(self):
        return pymssql.connect(
            server=self.db_config.get('host'),
            port=self.db_config.get('port', 1433),
            database=self.db_config.get('database'),
            user=self.db_config.get('username'),
            password=self.db_config.get('password'),
            autocommit=False
        )
    
    def get_kpis_generales(self, empresa_id: Optional[str] = None, 
                           fecha_inicio: Optional[str] = None,
                           fecha_fin: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene KPIs generales de tablajería.
        
        Returns:
            Dict con KPIs: órdenes, rendimientos, mermas, costos
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            # Filtros de fecha
            where_fecha = ""
            params = []
            if fecha_inicio and fecha_fin:
                where_fecha = "AND FechaOperacionMexico BETWEEN %s AND %s"
                params = [fecha_inicio, fecha_fin]
            elif fecha_inicio:
                where_fecha = "AND FechaOperacionMexico >= %s"
                params = [fecha_inicio]
            
            # KPIs de órdenes
            query_ordenes = f"""
                SELECT 
                    COUNT(*) as total_ordenes,
                    COUNT(CASE WHEN EstatusOrden = 'CERRADA' THEN 1 END) as ordenes_cerradas,
                    COUNT(CASE WHEN EstatusOrden = 'EN_EJECUCION' THEN 1 END) as ordenes_en_proceso,
                    COUNT(CASE WHEN EstatusOrden = 'BORRADOR' THEN 1 END) as ordenes_borrador,
                    COUNT(CASE WHEN EstatusOrden = 'PENDIENTE_AUTORIZACION' THEN 1 END) as ordenes_pendientes,
                    COUNT(CASE WHEN EstatusOrden = 'CANCELADA' THEN 1 END) as ordenes_canceladas,
                    AVG(CASE WHEN EstatusOrden = 'CERRADA' THEN RendimientoRealPorcentaje END) as rendimiento_promedio,
                    AVG(CASE WHEN EstatusOrden = 'CERRADA' THEN DesviacionRendimiento END) as desviacion_promedio,
                    SUM(CASE WHEN EstatusOrden = 'CERRADA' THEN CantidadBasePlaneada END) as kg_procesados_planeados,
                    SUM(CASE WHEN EstatusOrden = 'CERRADA' THEN CantidadBaseReal END) as kg_procesados_reales
                FROM Operaciones_Tablaje_Ordenes
                WHERE 1=1 {where_fecha}
            """
            
            cursor.execute(query_ordenes, params)
            kpis_ordenes = cursor.fetchone()
            
            # KPIs de mermas (de detalles con TipoDerivado = 'MERMA')
            query_mermas = f"""
                SELECT 
                    SUM(d.CantidadReal) as total_merma_kg,
                    AVG(d.PorcentajeReal) as porcentaje_merma_promedio
                FROM Operaciones_Tablaje_OrdenesDetalle d
                INNER JOIN Operaciones_Tablaje_Ordenes o ON d.OrdenID = o.OrdenID
                WHERE d.TipoDerivado = 'MERMA' 
                AND o.EstatusOrden = 'CERRADA'
                {where_fecha.replace('FechaOperacionMexico', 'o.FechaOperacionMexico')}
            """
            cursor.execute(query_mermas, params)
            kpis_mermas = cursor.fetchone()
            
            # KPIs de costeo
            query_costeo = f"""
                SELECT 
                    COUNT(*) as total_costeos,
                    SUM(CostoTotalProduccion) as costo_total_produccion,
                    AVG(CostoUnitarioPromedio) as costo_unitario_promedio
                FROM Tablajeria_CosteoProduccion
                WHERE 1=1
            """
            cursor.execute(query_costeo)
            kpis_costeo = cursor.fetchone()
            
            return {
                "ordenes": {
                    "total": kpis_ordenes['total_ordenes'] or 0,
                    "cerradas": kpis_ordenes['ordenes_cerradas'] or 0,
                    "en_proceso": kpis_ordenes['ordenes_en_proceso'] or 0,
                    "borrador": kpis_ordenes['ordenes_borrador'] or 0,
                    "pendientes_autorizacion": kpis_ordenes['ordenes_pendientes'] or 0,
                    "canceladas": kpis_ordenes['ordenes_canceladas'] or 0
                },
                "rendimiento": {
                    "promedio_porcentaje": float(kpis_ordenes['rendimiento_promedio'] or 0),
                    "desviacion_promedio": float(kpis_ordenes['desviacion_promedio'] or 0),
                    "kg_planeados": float(kpis_ordenes['kg_procesados_planeados'] or 0),
                    "kg_reales": float(kpis_ordenes['kg_procesados_reales'] or 0)
                },
                "mermas": {
                    "total_kg": float(kpis_mermas['total_merma_kg'] or 0),
                    "porcentaje_promedio": float(kpis_mermas['porcentaje_merma_promedio'] or 0)
                },
                "costeo": {
                    "total_costeos": kpis_costeo['total_costeos'] or 0,
                    "costo_total": float(kpis_costeo['costo_total_produccion'] or 0),
                    "costo_unitario_promedio": float(kpis_costeo['costo_unitario_promedio'] or 0)
                }
            }
            
        finally:
            conn.close()
    
    def get_rendimientos_por_plantilla(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Obtiene análisis de rendimientos agrupados por plantilla.
        
        Returns:
            Lista de plantillas con sus métricas de rendimiento
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute("""
                SELECT 
                    p.PlantillaID,
                    p.NombrePlantilla,
                    p.InsumoBaseNombre,
                    p.RendimientoEsperadoPorcentaje as rendimiento_esperado,
                    COUNT(o.OrdenID) as total_ordenes,
                    AVG(o.RendimientoRealPorcentaje) as rendimiento_real_promedio,
                    MIN(o.RendimientoRealPorcentaje) as rendimiento_minimo,
                    MAX(o.RendimientoRealPorcentaje) as rendimiento_maximo,
                    STDEV(o.RendimientoRealPorcentaje) as desviacion_estandar,
                    SUM(o.CantidadBaseReal) as kg_procesados
                FROM Operaciones_Tablaje_Plantillas p
                LEFT JOIN Operaciones_Tablaje_Ordenes o ON p.PlantillaID = o.PlantillaID
                    AND o.EstatusOrden = 'CERRADA'
                WHERE p.Activo = 1
                GROUP BY p.PlantillaID, p.NombrePlantilla, p.InsumoBaseNombre, 
                         p.RendimientoEsperadoPorcentaje
                HAVING COUNT(o.OrdenID) > 0
                ORDER BY COUNT(o.OrdenID) DESC
                OFFSET 0 ROWS FETCH NEXT %s ROWS ONLY
            """, (limit,))
            
            resultados = []
            for row in cursor.fetchall():
                rendimiento_esperado = float(row['rendimiento_esperado'] or 0)
                rendimiento_real = float(row['rendimiento_real_promedio'] or 0)
                desviacion = rendimiento_real - rendimiento_esperado if rendimiento_esperado > 0 else 0
                
                resultados.append({
                    "plantilla_id": str(row['PlantillaID']),
                    "nombre_plantilla": row['NombrePlantilla'],
                    "insumo_base": row['InsumoBaseNombre'],
                    "rendimiento_esperado": rendimiento_esperado,
                    "rendimiento_real_promedio": rendimiento_real,
                    "desviacion": desviacion,
                    "rendimiento_minimo": float(row['rendimiento_minimo'] or 0),
                    "rendimiento_maximo": float(row['rendimiento_maximo'] or 0),
                    "desviacion_estandar": float(row['desviacion_estandar'] or 0),
                    "total_ordenes": row['total_ordenes'],
                    "kg_procesados": float(row['kg_procesados'] or 0),
                    "estado": "OPTIMO" if abs(desviacion) <= 5 else ("ALERTA" if abs(desviacion) <= 10 else "CRITICO")
                })
            
            return resultados
            
        finally:
            conn.close()
    
    def get_tendencia_rendimientos(self, dias: int = 30) -> List[Dict[str, Any]]:
        """
        Obtiene tendencia de rendimientos en los últimos N días.
        
        Returns:
            Lista de puntos de datos para gráfico de tendencia
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute("""
                SELECT 
                    CAST(FechaOperacionMexico AS DATE) as fecha,
                    COUNT(*) as ordenes,
                    AVG(RendimientoRealPorcentaje) as rendimiento_promedio,
                    SUM(CantidadBaseReal) as kg_procesados,
                    AVG(DesviacionRendimiento) as desviacion_promedio
                FROM Operaciones_Tablaje_Ordenes
                WHERE EstatusOrden = 'CERRADA'
                AND FechaOperacionMexico >= DATEADD(DAY, -%s, GETDATE())
                GROUP BY CAST(FechaOperacionMexico AS DATE)
                ORDER BY fecha
            """, (dias,))
            
            resultados = []
            for row in cursor.fetchall():
                resultados.append({
                    "fecha": row['fecha'].strftime('%Y-%m-%d') if row['fecha'] else None,
                    "ordenes": row['ordenes'],
                    "rendimiento_promedio": float(row['rendimiento_promedio'] or 0),
                    "kg_procesados": float(row['kg_procesados'] or 0),
                    "desviacion_promedio": float(row['desviacion_promedio'] or 0)
                })
            
            return resultados
            
        finally:
            conn.close()
    
    def get_top_mermas(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene los productos derivados con mayor merma.
        
        Returns:
            Lista de productos con análisis de mermas
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute("""
                SELECT 
                    d.ProductoDerivadoNombre,
                    d.ProductoDerivadoCodigo,
                    COUNT(*) as ocurrencias,
                    SUM(d.CantidadReal) as total_kg,
                    AVG(d.PorcentajeReal) as porcentaje_promedio,
                    AVG(d.CantidadEsperada - d.CantidadReal) as diferencia_promedio
                FROM Operaciones_Tablaje_OrdenesDetalle d
                INNER JOIN Operaciones_Tablaje_Ordenes o ON d.OrdenID = o.OrdenID
                WHERE d.TipoDerivado = 'MERMA'
                AND o.EstatusOrden = 'CERRADA'
                GROUP BY d.ProductoDerivadoNombre, d.ProductoDerivadoCodigo
                ORDER BY SUM(d.CantidadReal) DESC
                OFFSET 0 ROWS FETCH NEXT %s ROWS ONLY
            """, (limit,))
            
            return [{
                "producto": row['ProductoDerivadoNombre'],
                "codigo": row['ProductoDerivadoCodigo'],
                "ocurrencias": row['ocurrencias'],
                "total_kg": float(row['total_kg'] or 0),
                "porcentaje_promedio": float(row['porcentaje_promedio'] or 0),
                "diferencia_promedio_kg": float(row['diferencia_promedio'] or 0)
            } for row in cursor.fetchall()]
            
        finally:
            conn.close()
    
    def get_alertas_rendimiento(self, umbral_desviacion: float = 5.0) -> List[Dict[str, Any]]:
        """
        Obtiene órdenes con desviaciones fuera de umbral.
        
        Args:
            umbral_desviacion: Porcentaje de desviación para generar alerta
            
        Returns:
            Lista de alertas de rendimiento
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute("""
                SELECT 
                    o.OrdenID,
                    o.FolioOrden,
                    o.InsumoBaseNombre,
                    o.FechaOperacionMexico,
                    o.RendimientoEsperadoPorcentaje,
                    o.RendimientoRealPorcentaje,
                    o.DesviacionRendimiento,
                    o.EstatusOrden,
                    p.NombrePlantilla
                FROM Operaciones_Tablaje_Ordenes o
                LEFT JOIN Operaciones_Tablaje_Plantillas p ON o.PlantillaID = p.PlantillaID
                WHERE ABS(o.DesviacionRendimiento) > %s
                AND o.EstatusOrden IN ('CERRADA', 'PENDIENTE_AUTORIZACION')
                ORDER BY ABS(o.DesviacionRendimiento) DESC
            """, (umbral_desviacion,))
            
            alertas = []
            for row in cursor.fetchall():
                desviacion = float(row['DesviacionRendimiento'] or 0)
                severidad = "ALTA" if abs(desviacion) > 15 else ("MEDIA" if abs(desviacion) > 10 else "BAJA")
                
                alertas.append({
                    "orden_id": str(row['OrdenID']),
                    "folio": row['FolioOrden'],
                    "insumo": row['InsumoBaseNombre'],
                    "plantilla": row['NombrePlantilla'],
                    "fecha": row['FechaOperacionMexico'].strftime('%Y-%m-%d') if row['FechaOperacionMexico'] else None,
                    "rendimiento_esperado": float(row['RendimientoEsperadoPorcentaje'] or 0),
                    "rendimiento_real": float(row['RendimientoRealPorcentaje'] or 0),
                    "desviacion": desviacion,
                    "estatus": row['EstatusOrden'],
                    "severidad": severidad,
                    "tipo": "BAJO_RENDIMIENTO" if desviacion < 0 else "SOBRE_RENDIMIENTO"
                })
            
            return alertas
            
        finally:
            conn.close()
    
    def get_resumen_costeo(self, fecha_inicio: Optional[str] = None,
                           fecha_fin: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene resumen de costeo de producción.
        
        Returns:
            Dict con métricas de costeo
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_costeos,
                    SUM(CostoTotalInsumo) as total_costo_insumo,
                    SUM(CostoManoObra) as total_costo_mano_obra,
                    SUM(CostoIndirectos) as total_costo_indirectos,
                    SUM(CostoEnergia) as total_costo_energia,
                    SUM(OtrosCostos) as total_otros_costos,
                    SUM(CostoTotalProduccion) as total_costo,
                    AVG(CostoUnitarioPromedio) as costo_unitario_promedio,
                    SUM(CantidadInsumoConsumida) as total_kg_producidos
                FROM Tablajeria_CosteoProduccion
            """)
            
            row = cursor.fetchone()
            
            total_costo = float(row['total_costo'] or 0)
            
            return {
                "total_costeos": row['total_costeos'] or 0,
                "desglose": {
                    "insumos": float(row['total_costo_insumo'] or 0),
                    "mano_obra": float(row['total_costo_mano_obra'] or 0),
                    "indirectos": float(row['total_costo_indirectos'] or 0),
                    "energia": float(row['total_costo_energia'] or 0),
                    "otros": float(row['total_otros_costos'] or 0)
                },
                "totales": {
                    "costo_total": total_costo,
                    "costo_unitario_promedio": float(row['costo_unitario_promedio'] or 0),
                    "kg_producidos": float(row['total_kg_producidos'] or 0)
                },
                "porcentajes": {
                    "insumos": (float(row['total_costo_insumo'] or 0) / total_costo * 100) if total_costo > 0 else 0,
                    "mano_obra": (float(row['total_costo_mano_obra'] or 0) / total_costo * 100) if total_costo > 0 else 0,
                    "indirectos": (float(row['total_costo_indirectos'] or 0) / total_costo * 100) if total_costo > 0 else 0,
                    "energia": (float(row['total_costo_energia'] or 0) / total_costo * 100) if total_costo > 0 else 0,
                    "otros": (float(row['total_otros_costos'] or 0) / total_costo * 100) if total_costo > 0 else 0
                }
            }
            
        finally:
            conn.close()


def get_tablajeria_dashboard_service() -> TablajeriaDashboardService:
    """Factory para obtener instancia del servicio."""
    db_config = {
        'host': os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
        'port': int(os.environ.get('EDARSAHUB_PORT', '1433')),
        'database': os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
        'username': os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
        'password': os.environ.get('EDARSAHUB_PASSWORD', '')
    }
    return TablajeriaDashboardService(db_config)
