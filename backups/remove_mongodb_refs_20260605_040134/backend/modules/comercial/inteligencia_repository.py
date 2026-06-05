# backend/modules/comercial/inteligencia_repository.py
"""
Repository para Inteligencia Comercial.
Consume vistas SQL canónicas - NO hace conexiones live a POS.
"""

from typing import Optional, List, Dict, Any
from datetime import date
from sqlalchemy import text
from sqlalchemy.orm import Session


class InteligenciaComercialRepository:
    """
    Repositorio SQL-first para Inteligencia Comercial.
    
    Fuentes:
    - Comercial_Inteligencia_VW_KPIsEjecutivos
    - Comercial_Inteligencia_VW_SyncStatus
    - Sp_Validar_Inteligencia_Comercial_Status
    """
    
    def __init__(self, db: Session):
        self.db = db

    def get_kpis(
        self,
        unidad: Optional[str] = None,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        anio: Optional[int] = None,
        mes: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Obtiene KPIs consolidados desde la vista ejecutiva.
        """
        conditions = ["1=1"]
        params = {}

        if unidad:
            conditions.append("unidad_negocio_nombre = :unidad")
            params["unidad"] = unidad

        if fecha_inicio:
            conditions.append("fecha_operacion >= :fecha_inicio")
            params["fecha_inicio"] = fecha_inicio

        if fecha_fin:
            conditions.append("fecha_operacion <= :fecha_fin")
            params["fecha_fin"] = fecha_fin

        if anio:
            conditions.append("anio = :anio")
            params["anio"] = anio

        if mes:
            conditions.append("mes = :mes")
            params["mes"] = mes

        where_sql = " AND ".join(conditions)

        sql = text(f"""
            SELECT
                SUM(ventas_total) AS ventas_total,
                SUM(ventas_sin_propina) AS ventas_sin_propina,
                SUM(propinas_total) AS propinas_total,
                SUM(tickets_total) AS tickets_total,
                SUM(pax_total) AS pax_total,
                CASE WHEN SUM(tickets_total) > 0
                    THEN SUM(ventas_sin_propina) / SUM(tickets_total)
                    ELSE 0 END AS ticket_promedio,
                CASE WHEN SUM(pax_total) > 0
                    THEN SUM(ventas_sin_propina) / SUM(pax_total)
                    ELSE 0 END AS consumo_promedio_pax,
                SUM(ventas_cerradas) AS ventas_cerradas,
                SUM(ventas_abiertas) AS ventas_abiertas,
                SUM(total_estimado_dia) AS total_estimado_dia,
                MAX(fecha_sincronizacion) AS ultima_sincronizacion
            FROM dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
            WHERE {where_sql}
        """)

        row = self.db.execute(sql, params).mappings().first()
        return dict(row or {})

    def get_kpis_por_unidad(
        self,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Obtiene KPIs desglosados por unidad de negocio.
        """
        conditions = ["1=1"]
        params = {}

        if fecha_inicio:
            conditions.append("fecha_operacion >= :fecha_inicio")
            params["fecha_inicio"] = fecha_inicio

        if fecha_fin:
            conditions.append("fecha_operacion <= :fecha_fin")
            params["fecha_fin"] = fecha_fin

        where_sql = " AND ".join(conditions)

        sql = text(f"""
            SELECT
                unidad_negocio_nombre,
                unidad_negocio_id,
                sistema_origen,
                SUM(ventas_total) AS ventas_total,
                SUM(ventas_sin_propina) AS ventas_sin_propina,
                SUM(propinas_total) AS propinas_total,
                SUM(tickets_total) AS tickets_total,
                SUM(pax_total) AS pax_total,
                CASE WHEN SUM(tickets_total) > 0
                    THEN SUM(ventas_sin_propina) / SUM(tickets_total)
                    ELSE 0 END AS ticket_promedio,
                MAX(fecha_sincronizacion) AS ultima_sincronizacion
            FROM dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
            WHERE {where_sql}
            GROUP BY unidad_negocio_nombre, unidad_negocio_id, sistema_origen
            ORDER BY ventas_total DESC
        """)

        return [dict(r) for r in self.db.execute(sql, params).mappings().all()]

    def get_tendencia_diaria(
        self,
        unidad: Optional[str] = None,
        dias: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Obtiene tendencia diaria de ventas.
        """
        conditions = [f"fecha_operacion >= DATEADD(DAY, -{dias}, GETDATE())"]
        params = {}

        if unidad:
            conditions.append("unidad_negocio_nombre = :unidad")
            params["unidad"] = unidad

        where_sql = " AND ".join(conditions)

        sql = text(f"""
            SELECT
                fecha_operacion,
                SUM(ventas_total) AS ventas_total,
                SUM(tickets_total) AS tickets_total,
                SUM(pax_total) AS pax_total
            FROM dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
            WHERE {where_sql}
            GROUP BY fecha_operacion
            ORDER BY fecha_operacion
        """)

        return [dict(r) for r in self.db.execute(sql, params).mappings().all()]

    def get_sync_status(self) -> List[Dict[str, Any]]:
        """
        Ejecuta el SP de validación de estado de fuentes.
        """
        sql = text("""
            EXEC dbo.Sp_Validar_Inteligencia_Comercial_Status
        """)
        return [dict(r) for r in self.db.execute(sql).mappings().all()]

    def get_unidades_activas(self) -> List[Dict[str, Any]]:
        """
        Lista unidades de negocio con datos activos.
        """
        sql = text("""
            SELECT DISTINCT
                unidad_negocio_nombre,
                unidad_negocio_id,
                sistema_origen,
                MAX(fecha_operacion) AS ultima_fecha,
                COUNT(DISTINCT fecha_operacion) AS dias_con_datos
            FROM dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
            GROUP BY unidad_negocio_nombre, unidad_negocio_id, sistema_origen
            ORDER BY unidad_negocio_nombre
        """)
        return [dict(r) for r in self.db.execute(sql).mappings().all()]

    def get_comparativo_periodos(
        self,
        fecha_inicio_actual: date,
        fecha_fin_actual: date,
        fecha_inicio_anterior: date,
        fecha_fin_anterior: date,
        unidad: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compara KPIs entre dos períodos.
        """
        params = {
            "fi_actual": fecha_inicio_actual,
            "ff_actual": fecha_fin_actual,
            "fi_anterior": fecha_inicio_anterior,
            "ff_anterior": fecha_fin_anterior,
        }
        
        unidad_filter = ""
        if unidad:
            unidad_filter = "AND unidad_negocio_nombre = :unidad"
            params["unidad"] = unidad

        sql = text(f"""
            SELECT
                'actual' AS periodo,
                SUM(ventas_total) AS ventas_total,
                SUM(tickets_total) AS tickets_total,
                SUM(pax_total) AS pax_total
            FROM dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
            WHERE fecha_operacion BETWEEN :fi_actual AND :ff_actual
            {unidad_filter}
            
            UNION ALL
            
            SELECT
                'anterior' AS periodo,
                SUM(ventas_total) AS ventas_total,
                SUM(tickets_total) AS tickets_total,
                SUM(pax_total) AS pax_total
            FROM dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
            WHERE fecha_operacion BETWEEN :fi_anterior AND :ff_anterior
            {unidad_filter}
        """)

        rows = [dict(r) for r in self.db.execute(sql, params).mappings().all()]
        
        result = {"actual": {}, "anterior": {}, "variacion": {}}
        for row in rows:
            periodo = row.pop("periodo")
            result[periodo] = row
        
        # Calcular variaciones
        if result["actual"] and result["anterior"]:
            for key in ["ventas_total", "tickets_total", "pax_total"]:
                actual = result["actual"].get(key) or 0
                anterior = result["anterior"].get(key) or 0
                if anterior > 0:
                    result["variacion"][key] = round(((actual - anterior) / anterior) * 100, 2)
                else:
                    result["variacion"][key] = 0
        
        return result
