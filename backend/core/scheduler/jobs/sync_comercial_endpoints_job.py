import os
"""
EDARSA HUB - Sync Comercial Endpoints Job
==========================================
Job para sincronizar datos de endpoints comerciales LIVE a tablas SQL.

TABLAS SINCRONIZADAS:
- Sync_Metas_Comerciales
- Sync_Ticket_Perfecto
- Sync_Mesas
- Sync_Movimientos_Detalle
- Sync_Precios_Historicos
- Sync_PAX_Detalle

ARQUITECTURA NO-LIVE:
- Este job consulta servidores remotos (SoftRestaurant/MPRO)
- Almacena datos en EDARSAHUB SQL
- Los endpoints comerciales consultan SOLO las tablas SQL
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import uuid
import pymssql

import hashlib
from ..config import JobConfig
from core.sql_first.db import get_sql_connection
from core.connections.pos_runtime_resolver import PosRuntimeContext, list_pos_runtime_contexts

logger = logging.getLogger(__name__)

# Configuración de conexión EDARSAHUB
EDARSAHUB_CONFIG = {
    "server": os.getenv('EDARSAHUB_SQL_HOST'),
    "port": 1433,
    "database": "EDARSAHUB",
    "user": os.getenv('EDARSAHUB_SQL_USER'),
    "password": os.getenv('EDARSAHUB_SQL_PASSWORD'),
}


class SyncComercialEndpointsJob:
    """
    Job para sincronizar endpoints comerciales a SQL.
    
    Ejecuta sincronización de:
    1. Metas comerciales
    2. Ticket perfecto
    3. Mesas
    4. Movimientos detalle
    5. Precios históricos
    6. PAX detalle
    """
    
    JOB_ID = "sync_comercial_endpoints"
    
    def __init__(self, db=None, config: JobConfig = None):
        """
        Args:
            db: Dependencia técnica legacy opcional; este job usa SQL directo
            config: Configuración del job
        """
        self.db = db
        self.config = config or JobConfig(
            job_id=self.JOB_ID,
            job_name="Sync Comercial Endpoints",
            description="Sincroniza datos comerciales de endpoints LIVE a tablas SQL",
            enabled=True,
            interval_seconds=3600,  # 1 hora
            timeout_seconds=300
        )
        self.job_name = self.JOB_ID
        self._conn = None
    
    def _get_edarsahub_connection(self):
        """Obtiene conexión a EDARSAHUB."""
        if self._conn is None:
            self._conn = get_sql_connection()
        return self._conn
    
    def _close_connection(self):
        """Cierra conexión."""
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
    
    async def execute(self) -> Dict[str, Any]:
        logger.error(
            "SYNC_COMERCIAL_ENDPOINTS_DISABLED: "
            "job bloqueado para impedir fuentes comerciales paralelas"
        )
        return {
            "success": False,
            "status": "disabled",
            "code": "SYNC_COMERCIAL_ENDPOINTS_DISABLED",
            "message": (
                "Job deshabilitado: Sync_* no puede persistir KPIs "
                "que ya pertenecen a fuentes canónicas comerciales."
            ),
        }

        """
        Ejecuta sincronización de todos los endpoints.
        """
        logger.info(f"[{self.JOB_ID}] Iniciando sincronización")
        
        results = {
            "processed_count": 0,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "details": {}
        }
        
        try:
            # Obtener lista de servidores activos
            contexts = list_pos_runtime_contexts()
            
            if not contexts:
                logger.warning(f"[{self.JOB_ID}] No hay contextos POS activos")
                results["message"] = "No hay contextos POS activos"
                return results
            
            # Sincronizar cada tipo de dato
            sync_methods = [
                ("metas", self._sync_metas_comerciales),
                ("ticket_perfecto", self._sync_ticket_perfecto),
                ("mesas", self._sync_mesas),
                ("pax", self._sync_pax_detalle),
            ]
            
            for sync_name, sync_method in sync_methods:
                try:
                    count = sync_method(contexts)
                    results["details"][sync_name] = {"success": True, "count": count}
                    results["success_count"] += 1
                    results["processed_count"] += count
                except Exception as e:
                    logger.error(f"[{self.JOB_ID}] Error en {sync_name}: {e}")
                    results["details"][sync_name] = {"success": False, "error": str(e)}
                    results["failed_count"] += 1
            
            results["message"] = f"Sincronización completada: {results['processed_count']} registros"
            
        except Exception as e:
            logger.error(f"[{self.JOB_ID}] Error general: {e}")
            results["message"] = f"Error: {e}"
            results["failed_count"] += 1
        finally:
            self._close_connection()
        
        return results
    
    async def run(self) -> Dict[str, Any]:
        """Ejecuta el job."""
        if not self.config.enabled:
            return {"status": "skipped", "reason": "disabled"}
        
        try:
            result = await self.execute()
            return {"status": "success", **result}
        except Exception as e:
            logger.error(f"[{self.JOB_ID}] Error: {e}")
            return {"status": "failed", "error": str(e)}
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    # =========================================================================
    # SYNC: METAS COMERCIALES
    # =========================================================================
    
    def _sync_metas_comerciales(self, contexts: List[PosRuntimeContext]) -> int:
        """
        Sincroniza metas comerciales desde KPIs existentes.
        Genera metas basadas en datos históricos.
        """
        logger.info(f"[{self.JOB_ID}] Sincronizando metas comerciales")
        
        conn = self._get_edarsahub_connection()
        cursor = conn.cursor(as_dict=True)
        
        now = datetime.now(timezone.utc)
        anio = now.year
        mes = now.month
        count = 0
        
        for context in contexts:
            server_id = str(context.server_id)
            suc = {
                "SucursalID": str(
                    context.sucursal_origen_id or "DEFAULT"
                ).strip(),
                "SucursalNombre": context.unidad_nombre,
            }
            try:
                # Obtener ventas actuales del mes desde KPIs (columnas en minúsculas)
                cursor.execute("""
                    SELECT
                        ISNULL(SUM(ventas_total), 0) as VentaBrutaActual,
                        ISNULL(SUM(ventas_sin_propina), 0) as VentaNetaActual,
                        ISNULL(AVG(ticket_promedio), 0) as TicketPromedioActual,
                        ISNULL(SUM(tickets_total), 0) as CuentasActual,
                        ISNULL(SUM(pax_total), 0) as ComensalesActual,
                        COUNT(DISTINCT fecha_operacion) as DiasTranscurridos
                    FROM Comercial_KPIs_Diarios_v2
                    WHERE server_id = %s
                      AND sucursal_id = %s
                      AND anio = %s
                      AND mes = %s
                """, (server_id, suc["SucursalID"], anio, mes))

                row = cursor.fetchone()

                if row:
                    meta_id = f"{server_id}-{suc['SucursalID']}-{anio}-{mes}"

                    # Calcular meta basada en promedio histórico + 10%
                    venta_actual = float(row["VentaBrutaActual"] or 0)
                    dias = int(row["DiasTranscurridos"] or 1)
                    dias_mes = 30  # Aproximado

                    # Proyección simple
                    promedio_diario = venta_actual / dias if dias > 0 else 0
                    proyeccion = promedio_diario * dias_mes
                    meta = proyeccion * 1.10  # Meta = proyección + 10%

                    # Upsert en tabla - simplificado
                    cursor.execute("""
                        IF NOT EXISTS (SELECT 1 FROM Sync_Metas_Comerciales
                                       WHERE ServerID = %s AND SucursalID = %s AND Anio = %s AND Mes = %s)
                            INSERT INTO Sync_Metas_Comerciales
                            (MetaID, ServerID, SucursalID, SucursalNombre, Anio, Mes,
                             MetaVentaBruta, VentaBrutaActual, VentaNetaActual,
                             TicketPromedioActual, CuentasActual, ComensalesActual,
                             DiasTranscurridos, DiasRestantes, ProyeccionMes)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ELSE
                            UPDATE Sync_Metas_Comerciales SET
                                VentaBrutaActual = %s,
                                VentaNetaActual = %s,
                                TicketPromedioActual = %s,
                                CuentasActual = %s,
                                ComensalesActual = %s,
                                DiasTranscurridos = %s,
                                DiasRestantes = %s,
                                ProyeccionMes = %s,
                                FechaSync = GETUTCDATE()
                            WHERE ServerID = %s AND SucursalID = %s AND Anio = %s AND Mes = %s
                    """, (
                        # EXISTS check params
                        server_id, suc["SucursalID"], anio, mes,
                        # INSERT params
                        meta_id, server_id, suc["SucursalID"], suc.get("SucursalNombre", ""),
                        anio, mes, meta, row["VentaBrutaActual"], row["VentaNetaActual"],
                        row["TicketPromedioActual"], row["CuentasActual"],
                        row["ComensalesActual"], dias, dias_mes - dias, proyeccion,
                        # UPDATE params
                        row["VentaBrutaActual"], row["VentaNetaActual"],
                        row["TicketPromedioActual"], row["CuentasActual"],
                        row["ComensalesActual"], dias, dias_mes - dias, proyeccion,
                        server_id, suc["SucursalID"], anio, mes
                    ))
                    conn.commit()
                    count += 1
                        
            except Exception as e:
                logger.warning(f"[{self.JOB_ID}] Error sync metas {suc.get('SucursalID')}: {e}")
                raise

        
        cursor.close()
        logger.info(f"[{self.JOB_ID}] Metas sincronizadas: {count}")
        return count
    
    # =========================================================================
    # SYNC: TICKET PERFECTO
    # =========================================================================
    
    def _sync_ticket_perfecto(self, contexts: List[PosRuntimeContext]) -> int:
        """
        Sincroniza datos de ticket perfecto desde KPIs.
        """
        logger.info(f"[{self.JOB_ID}] Sincronizando ticket perfecto")
        
        conn = self._get_edarsahub_connection()
        cursor = conn.cursor(as_dict=True)
        
        # Sincronizar últimos 7 días
        fecha_inicio = datetime.now(timezone.utc).date() - timedelta(days=7)
        count = 0
        
        for context in contexts:
            server_id = str(context.server_id)
            suc = {
                "SucursalID": str(
                    context.sucursal_origen_id or "DEFAULT"
                ).strip(),
                "SucursalNombre": context.unidad_nombre,
            }
            try:
                cursor.execute("""
                    SELECT
                        fecha_operacion as fecha_operacion,
                        ISNULL(tickets_total, 0) as TotalCuentas,
                        ISNULL(pax_total, 0) as TotalComensales,
                        ISNULL(ventas_total, 0) as VentaTotal,
                        ISNULL(ticket_promedio, 0) as TicketPromedioReal
                    FROM Comercial_KPIs_Diarios_v2
                    WHERE server_id = %s
                      AND sucursal_id = %s
                      AND fecha_operacion >= %s
                """, (server_id, suc["SucursalID"], fecha_inicio))

                for row in cursor.fetchall():
                    ticket_id = f"{server_id}-{suc['SucursalID']}-{row['fecha_operacion']}"

                    # Objetivo de ticket perfecto (configurable, default 350)
                    ticket_objetivo = 350.0
                    ticket_real = float(row["TicketPromedioReal"] or 0)
                    cumplimiento = (ticket_real / ticket_objetivo * 100) if ticket_objetivo > 0 else 0

                    cursor.execute("""
                        IF NOT EXISTS (SELECT 1 FROM Sync_Ticket_Perfecto
                                      WHERE ServerID = %s AND SucursalID = %s AND FechaOperacion = %s)
                            INSERT INTO Sync_Ticket_Perfecto
                            (TicketID, ServerID, SucursalID, SucursalNombre, FechaOperacion,
                             TotalCuentas, TotalComensales, VentaTotal,
                             TicketPromedioReal, TicketPerfectoObjetivo, PorcentajeCumplimiento)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        server_id, suc["SucursalID"], row["fecha_operacion"],
                        ticket_id, server_id, suc["SucursalID"], suc.get("SucursalNombre", ""),
                        row["fecha_operacion"], row["TotalCuentas"], row["TotalComensales"],
                        row["VentaTotal"], ticket_real, ticket_objetivo, cumplimiento
                    ))
                    conn.commit()
                    count += 1
                        
            except Exception as e:
                logger.warning(f"[{self.JOB_ID}] Error sync ticket {suc.get('SucursalID')}: {e}")
                raise

        
        cursor.close()
        logger.info(f"[{self.JOB_ID}] Ticket perfecto sincronizado: {count}")
        return count
    
    # =========================================================================
    # SYNC: MESAS
    # =========================================================================
    
    def _sync_mesas(self, contexts: List[PosRuntimeContext]) -> int:
        """
        Sincroniza estado de mesas desde ventas abiertas.
        """
        logger.info(f"[{self.JOB_ID}] Sincronizando mesas")
        
        conn = self._get_edarsahub_connection()
        cursor = conn.cursor(as_dict=True)
        
        hoy = datetime.now(timezone.utc).date()
        count = 0
        
        for context in contexts:
            server_id = str(context.server_id)
            suc = {
                "SucursalID": str(
                    context.sucursal_origen_id or "DEFAULT"
                ).strip(),
                "SucursalNombre": context.unidad_nombre,
            }
            try:
                # Obtener datos agregados de ventas (las columnas reales son minúsculas)
                cursor.execute("""
                    SELECT
                        sucursal_id,
                        sucursal_nombre,
                        CAST(fecha_operacion as DATE) as FechaOp,
                        ISNULL(SUM(tickets_cerrados_dia), 0) as TotalCuentas,
                        ISNULL(SUM(pax_cerrados_dia), 0) as TotalComensales,
                        ISNULL(SUM(ventas_cerradas_dia), 0) as VentaTotal
                    FROM Comercial_Ventas_Dia_Abiertas_v2
                    WHERE server_id = %s AND sucursal_id = %s
                      AND CAST(fecha_operacion AS DATE) = %s
                    GROUP BY sucursal_id, sucursal_nombre, CAST(fecha_operacion as DATE)
                """, (server_id, suc["SucursalID"], hoy))

                for row in cursor.fetchall():
                    mesa_id = f"{server_id}-{suc['SucursalID']}-{hoy}-resumen"

                    ticket_promedio = (float(row["VentaTotal"] or 0) / int(row["TotalCuentas"] or 1)) if row["TotalCuentas"] else 0

                    cursor.execute("""
                        IF NOT EXISTS (SELECT 1 FROM Sync_Mesas
                                      WHERE ServerID = %s AND SucursalID = %s
                                        AND FechaOperacion = %s AND MesaNumero = %s)
                            INSERT INTO Sync_Mesas
                            (MesaRegistroID, ServerID, SucursalID, SucursalNombre, FechaOperacion,
                             MesaNumero, TotalCuentas, TotalComensales, VentaTotal, TicketPromedio)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        server_id, suc["SucursalID"], hoy, 'TOTAL',
                        mesa_id, server_id, suc["SucursalID"], row.get("sucursal_nombre", ""),
                        hoy, 'TOTAL', row["TotalCuentas"],
                        row["TotalComensales"], row["VentaTotal"], ticket_promedio
                    ))
                    conn.commit()
                    count += 1
                        
            except Exception as e:
                logger.warning(f"[{self.JOB_ID}] Error sync mesas {suc.get('SucursalID')}: {e}")
                raise

        
        cursor.close()
        logger.info(f"[{self.JOB_ID}] Mesas sincronizadas: {count}")
        return count
    
    # =========================================================================
    # SYNC: PAX DETALLE
    # =========================================================================
    
    def _sync_pax_detalle(self, contexts: List[PosRuntimeContext]) -> int:
        """
        Sincroniza detalle de PAX (comensales) desde ventas.
        """
        logger.info(f"[{self.JOB_ID}] Sincronizando PAX detalle")
        
        conn = self._get_edarsahub_connection()
        cursor = conn.cursor(as_dict=True)
        
        # Últimos 7 días
        fecha_inicio = datetime.now(timezone.utc).date() - timedelta(days=7)
        count = 0
        
        for context in contexts:
            server_id = str(context.server_id)
            suc = {
                "SucursalID": str(
                    context.sucursal_origen_id or "DEFAULT"
                ).strip(),
                "SucursalNombre": context.unidad_nombre,
            }
            try:
                cursor.execute("""
                    SELECT
                        CAST(fecha_operacion AS DATE) as FechaOperacion,
                        ISNULL(SUM(pax_cerrados_dia), 0) as TotalComensales,
                        ISNULL(SUM(ventas_cerradas_dia), 0) as VentaTotal,
                        ISNULL(SUM(tickets_cerrados_dia), 0) as TotalCuentas
                    FROM Comercial_Ventas_Dia_Abiertas_v2
                    WHERE server_id = %s AND sucursal_id = %s
                      AND fecha_operacion >= %s
                    GROUP BY CAST(fecha_operacion AS DATE)
                """, (server_id, suc["SucursalID"], fecha_inicio))

                for row in cursor.fetchall():
                    pax_id = hashlib.sha256(
                        f"{server_id}|{suc['SucursalID']}|{row['FechaOperacion']}".encode("utf-8")
                    ).hexdigest()[:50]

                    comensales = int(row["TotalComensales"] or 0)
                    venta = float(row["VentaTotal"] or 0)
                    consumo_pax = venta / comensales if comensales > 0 else 0

                    cursor.execute("""
                        IF NOT EXISTS (SELECT 1 FROM Sync_PAX_Detalle
                                      WHERE ServerID = %s AND SucursalID = %s AND FechaOperacion = %s)
                            INSERT INTO Sync_PAX_Detalle
                            (PAXRegistroID, ServerID, SucursalID, SucursalNombre,
                             FechaOperacion, FechaHora, NumeroComensales,
                             VentaCuenta, ConsumoPromedioPAX)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        server_id, suc["SucursalID"], row["FechaOperacion"],
                        pax_id, server_id, suc["SucursalID"], suc.get("SucursalNombre", ""),
                        row["FechaOperacion"], datetime.now(timezone.utc),
                        comensales, venta, consumo_pax
                    ))
                    conn.commit()
                    count += 1
                        
            except Exception as e:
                logger.warning(f"[{self.JOB_ID}] Error sync PAX {suc.get('SucursalID')}: {e}")
                raise

        
        cursor.close()
        logger.info(f"[{self.JOB_ID}] PAX sincronizado: {count}")
        return count


def get_sync_comercial_endpoints_job(db=None, config: JobConfig = None) -> SyncComercialEndpointsJob:
    """Factory function."""
    return SyncComercialEndpointsJob(db, config)
