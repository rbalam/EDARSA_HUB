"""
EDARSA HUB - Finanzas Repository (SQL Server Real)
==================================================
Repositorio para acceso a datos REALES de Finanzas en SQL Server.

TABLAS CONECTADAS:
- Finanzas_CortesCaja: Cortes de caja diarios por sucursal
- Finanzas_CuentasPorPagar: Facturas pendientes de pago
- Finanzas_ConfiguracionTPV_Sucursal: Comisiones TPV por sucursal
- RH_Cat_Sucursales: Catálogo de sucursales

ABRIL 2026: Conexión resiliente a SQL Server EDARSA HUB
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from core.db import execute_sql_query, sql_health_check, ResilientConfig

# ID del servidor EDARSA HUB en MongoDB
EDARSA_HUB_SERVER_ID = "bea40259-35f1-4693-bda2-d2d10e13e56a"


class FinanzasRepositoryReal:
    """
    Repositorio para acceso a datos REALES de Finanzas.
    Usa las tablas ya existentes en SQL Server EDARSA HUB.
    """
    
    def __init__(self, db):
        """
        Args:
            db: Instancia de MongoDB para obtener configuración del servidor
        """
        self.db = db
        self._server_cache = None
    
    async def _get_server(self) -> Optional[Dict]:
        """Obtiene la configuración del servidor EDARSA HUB"""
        if self._server_cache:
            return self._server_cache
        
        self._server_cache = await self.db.servers.find_one({
            "id": EDARSA_HUB_SERVER_ID,
            "active": True
        })
        return self._server_cache
    
    async def _execute_query(self, query: str, timeout: int = None) -> List[Dict]:
        """
        Ejecuta una query en EDARSA HUB con la lógica resiliente.
        
        Args:
            query: Query SQL a ejecutar
            timeout: Timeout en segundos (default: ResilientConfig.QUERY_TIMEOUT)
        
        Returns:
            Lista de diccionarios con resultados
        """
        server = await self._get_server()
        if not server:
            logging.error("[FinanzasRepo] Servidor EDARSA HUB no encontrado")
            return []
        
        timeout = timeout or ResilientConfig.QUERY_TIMEOUT
        
        try:
            results = execute_sql_query(
                host=server['host'],
                port=server['port'],
                database=server['database'],
                username=server['username'],
                password=server['password'],
                query=query,
                timeout_seconds=timeout
            )
            return results if results else []
        except Exception as e:
            logging.error(f"[FinanzasRepo] Error ejecutando query: {e}")
            return []
    
    # =========================================================================
    # CORTES DE CAJA (INGRESOS)
    # =========================================================================
    
    async def get_cortes_caja(
        self,
        sucursal_id: Optional[int] = None,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        estatus_cierre_id: Optional[int] = None,
        solo_pendientes_deposito: bool = False,
        limit: int = 100
    ) -> List[Dict]:
        """
        Obtiene cortes de caja con filtros opcionales.
        
        Args:
            sucursal_id: Filtrar por sucursal específica
            fecha_inicio: Fecha inicio del rango (YYYY-MM-DD)
            fecha_fin: Fecha fin del rango (YYYY-MM-DD)
            estatus_cierre_id: 1=Abierto, 2=Cerrado, 3=Conciliado
            solo_pendientes_deposito: Solo cortes con depósitos pendientes
            limit: Máximo de registros
        
        Returns:
            Lista de cortes de caja
        """
        where_clauses = ["c.Activo = 1"]
        
        if sucursal_id:
            where_clauses.append(f"c.SucursalID = {sucursal_id}")
        if fecha_inicio:
            where_clauses.append(f"c.FechaCorte >= '{fecha_inicio}'")
        if fecha_fin:
            where_clauses.append(f"c.FechaCorte <= '{fecha_fin}'")
        if estatus_cierre_id:
            where_clauses.append(f"c.EstatusCierreID = {estatus_cierre_id}")
        if solo_pendientes_deposito:
            where_clauses.append("""
                (c.DepositadoEfectivo = 0 
                 OR c.DepositadoDebito = 0 
                 OR c.DepositadoCredito = 0 
                 OR c.DepositadoAmex = 0 
                 OR c.DepositadoInternacional = 0)
            """)
        
        where = " AND ".join(where_clauses)
        
        query = f"""
            SELECT TOP {limit}
                c.CorteCajaID,
                c.SucursalID,
                s.Nombre_Sucursal AS SucursalNombre,
                c.FechaCorte,
                c.TurnoID,
                c.TotalEfectivo,
                c.TotalTarjetaDebito,
                c.TotalTarjetaCredito,
                c.TotalAmex,
                c.TotalInternacional,
                c.TotalVales,
                c.TotalOtros,
                c.ComisionDebito,
                c.ComisionCredito,
                c.ComisionAmex,
                c.ComisionInternacional,
                c.FechaDepositoEfectivo,
                c.FechaDepositoDebito,
                c.FechaDepositoCredito,
                c.FechaDepositoAmex,
                c.FechaDepositoInternacional,
                c.DepositadoEfectivo,
                c.DepositadoDebito,
                c.DepositadoCredito,
                c.DepositadoAmex,
                c.DepositadoInternacional,
                c.EstatusCierreID,
                ec.Nombre AS EstatusNombre,
                c.Observaciones,
                c.FechaAlta
            FROM Finanzas_CortesCaja c
            LEFT JOIN RH_Cat_Sucursales s ON c.SucursalID = s.SucursalID
            LEFT JOIN Finanzas_EstatusCierre ec ON c.EstatusCierreID = ec.EstatusCierreID
            WHERE {where}
            ORDER BY c.FechaCorte DESC, c.SucursalID
        """
        
        return await self._execute_query(query)
    
    async def get_resumen_ingresos(
        self,
        sucursal_id: Optional[int] = None,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None
    ) -> Dict:
        """
        Obtiene resumen de ingresos por tipo de pago.
        
        Returns:
            Dict con totales por tipo de pago y comisiones
        """
        where_clauses = ["Activo = 1"]
        
        if sucursal_id:
            where_clauses.append(f"SucursalID = {sucursal_id}")
        if fecha_inicio:
            where_clauses.append(f"FechaCorte >= '{fecha_inicio}'")
        if fecha_fin:
            where_clauses.append(f"FechaCorte <= '{fecha_fin}'")
        
        where = " AND ".join(where_clauses)
        
        query = f"""
            SELECT 
                COUNT(*) AS TotalCortes,
                SUM(TotalEfectivo) AS TotalEfectivo,
                SUM(TotalTarjetaDebito) AS TotalDebito,
                SUM(TotalTarjetaCredito) AS TotalCredito,
                SUM(TotalAmex) AS TotalAmex,
                SUM(TotalInternacional) AS TotalInternacional,
                SUM(TotalVales) AS TotalVales,
                SUM(TotalOtros) AS TotalOtros,
                SUM(ComisionDebito) AS ComisionDebito,
                SUM(ComisionCredito) AS ComisionCredito,
                SUM(ComisionAmex) AS ComisionAmex,
                SUM(ComisionInternacional) AS ComisionInternacional,
                SUM(TotalEfectivo + TotalTarjetaDebito + TotalTarjetaCredito + 
                    TotalAmex + TotalInternacional + TotalVales + TotalOtros) AS TotalGeneral,
                SUM(ComisionDebito + ComisionCredito + ComisionAmex + ComisionInternacional) AS TotalComisiones
            FROM Finanzas_CortesCaja
            WHERE {where}
        """
        
        results = await self._execute_query(query)
        if results:
            return results[0]
        return {
            "TotalCortes": 0,
            "TotalEfectivo": 0,
            "TotalDebito": 0,
            "TotalCredito": 0,
            "TotalAmex": 0,
            "TotalInternacional": 0,
            "TotalVales": 0,
            "TotalOtros": 0,
            "ComisionDebito": 0,
            "ComisionCredito": 0,
            "ComisionAmex": 0,
            "ComisionInternacional": 0,
            "TotalGeneral": 0,
            "TotalComisiones": 0
        }
    
    async def get_pendientes_deposito(self, sucursal_id: Optional[int] = None) -> List[Dict]:
        """
        Obtiene cortes con depósitos pendientes.
        """
        where_clauses = ["Activo = 1"]
        if sucursal_id:
            where_clauses.append(f"SucursalID = {sucursal_id}")
        
        where = " AND ".join(where_clauses)
        
        query = f"""
            SELECT 
                c.CorteCajaID,
                c.SucursalID,
                s.Nombre_Sucursal AS SucursalNombre,
                c.FechaCorte,
                -- Efectivo pendiente
                CASE WHEN c.DepositadoEfectivo = 0 AND c.TotalEfectivo > 0 
                     THEN c.TotalEfectivo ELSE 0 END AS EfectivoPendiente,
                c.FechaDepositoEfectivo,
                -- Débito pendiente
                CASE WHEN c.DepositadoDebito = 0 AND c.TotalTarjetaDebito > 0 
                     THEN c.TotalTarjetaDebito - c.ComisionDebito ELSE 0 END AS DebitoPendiente,
                c.FechaDepositoDebito,
                -- Crédito pendiente
                CASE WHEN c.DepositadoCredito = 0 AND c.TotalTarjetaCredito > 0 
                     THEN c.TotalTarjetaCredito - c.ComisionCredito ELSE 0 END AS CreditoPendiente,
                c.FechaDepositoCredito,
                -- AMEX pendiente
                CASE WHEN c.DepositadoAmex = 0 AND c.TotalAmex > 0 
                     THEN c.TotalAmex - c.ComisionAmex ELSE 0 END AS AmexPendiente,
                c.FechaDepositoAmex,
                -- Internacional pendiente
                CASE WHEN c.DepositadoInternacional = 0 AND c.TotalInternacional > 0 
                     THEN c.TotalInternacional - c.ComisionInternacional ELSE 0 END AS InternacionalPendiente,
                c.FechaDepositoInternacional
            FROM Finanzas_CortesCaja c
            LEFT JOIN RH_Cat_Sucursales s ON c.SucursalID = s.SucursalID
            WHERE {where}
              AND (c.DepositadoEfectivo = 0 
                   OR c.DepositadoDebito = 0 
                   OR c.DepositadoCredito = 0 
                   OR c.DepositadoAmex = 0 
                   OR c.DepositadoInternacional = 0)
            ORDER BY c.FechaCorte DESC
        """
        
        return await self._execute_query(query)
    
    async def marcar_deposito(
        self,
        corte_id: int,
        tipo_deposito: str,  # 'efectivo', 'debito', 'credito', 'amex', 'internacional'
        referencia: Optional[str] = None
    ) -> Dict:
        """Marca un depósito como realizado"""
        campo_map = {
            'efectivo': 'DepositadoEfectivo',
            'debito': 'DepositadoDebito',
            'credito': 'DepositadoCredito',
            'amex': 'DepositadoAmex',
            'internacional': 'DepositadoInternacional'
        }
        
        if tipo_deposito not in campo_map:
            return {"success": False, "error": f"Tipo de depósito inválido: {tipo_deposito}"}
        
        campo = campo_map[tipo_deposito]
        
        query = f"""
            UPDATE Finanzas_CortesCaja
            SET {campo} = 1
            WHERE CorteCajaID = {corte_id}
        """
        
        await self._execute_query(query)
        return {"success": True, "campo_actualizado": campo}
    
    # =========================================================================
    # CUENTAS POR PAGAR
    # =========================================================================
    
    async def get_cuentas_por_pagar(
        self,
        sucursal_id: Optional[int] = None,
        proveedor_id: Optional[int] = None,
        estatus_pago_id: Optional[int] = None,
        solo_vencidas: bool = False,
        fecha_corte: Optional[str] = None,
        limit: int = 200
    ) -> List[Dict]:
        """
        Obtiene cuentas por pagar con filtros.
        
        Args:
            sucursal_id: Filtrar por sucursal
            proveedor_id: Filtrar por proveedor
            estatus_pago_id: 1=Pendiente, 2=Parcial, 3=Pagado, 4=Cancelado, 5=Vencido
            solo_vencidas: Solo documentos vencidos
            fecha_corte: Fecha de corte para calcular vencimiento
            limit: Máximo de registros
        
        Returns:
            Lista de cuentas por pagar
        """
        where_clauses = ["c.Activo = 1"]
        
        if sucursal_id:
            where_clauses.append(f"c.SucursalID = {sucursal_id}")
        if proveedor_id:
            where_clauses.append(f"c.ProveedorID = {proveedor_id}")
        if estatus_pago_id:
            where_clauses.append(f"c.EstatusPagoID = {estatus_pago_id}")
        if solo_vencidas:
            where_clauses.append("c.FechaVencimiento < CAST(GETDATE() AS DATE)")
        if fecha_corte:
            where_clauses.append(f"c.FechaDocumento <= '{fecha_corte}'")
        
        where = " AND ".join(where_clauses)
        
        query = f"""
            SELECT TOP {limit}
                c.CuentaPorPagarID,
                c.DocumentoFiscalID,
                c.ProveedorID,
                c.SucursalID,
                s.Nombre_Sucursal AS SucursalNombre,
                c.NumeroDocumento,
                c.FechaDocumento,
                c.FechaVencimiento,
                c.FechaRecepcion,
                c.MontoOriginal,
                c.MontoPagado,
                c.MontoOriginal - c.MontoPagado AS Saldo,
                c.MonedaID,
                c.TipoCambio,
                c.EstatusPagoID,
                ep.Nombre AS EstatusNombre,
                c.DiasCredito,
                DATEDIFF(DAY, c.FechaVencimiento, GETDATE()) AS DiasVencido,
                c.Observaciones,
                c.FechaAlta,
                c.FechaModificacion
            FROM Finanzas_CuentasPorPagar c
            LEFT JOIN RH_Cat_Sucursales s ON c.SucursalID = s.SucursalID
            LEFT JOIN Finanzas_EstatusPago ep ON c.EstatusPagoID = ep.EstatusPagoID
            WHERE {where}
            ORDER BY c.FechaVencimiento ASC, c.MontoOriginal DESC
        """
        
        return await self._execute_query(query)
    
    async def get_resumen_cxp(
        self,
        sucursal_id: Optional[int] = None,
        fecha_corte: Optional[str] = None
    ) -> Dict:
        """
        Obtiene resumen de cuentas por pagar.
        
        Returns:
            Dict con totales y métricas
        """
        where_clauses = ["Activo = 1"]
        
        if sucursal_id:
            where_clauses.append(f"SucursalID = {sucursal_id}")
        if fecha_corte:
            where_clauses.append(f"FechaDocumento <= '{fecha_corte}'")
        
        where = " AND ".join(where_clauses)
        
        query = f"""
            SELECT 
                COUNT(*) AS TotalDocumentos,
                SUM(MontoOriginal) AS TotalOriginal,
                SUM(MontoPagado) AS TotalPagado,
                SUM(MontoOriginal - MontoPagado) AS TotalPendiente,
                -- Por estatus
                SUM(CASE WHEN EstatusPagoID = 1 THEN MontoOriginal - MontoPagado ELSE 0 END) AS PendientePago,
                SUM(CASE WHEN EstatusPagoID = 2 THEN MontoOriginal - MontoPagado ELSE 0 END) AS PagoParcial,
                SUM(CASE WHEN EstatusPagoID = 3 THEN MontoOriginal ELSE 0 END) AS Pagado,
                -- Vencido
                SUM(CASE WHEN FechaVencimiento < CAST(GETDATE() AS DATE) 
                         AND MontoOriginal > MontoPagado 
                    THEN MontoOriginal - MontoPagado ELSE 0 END) AS TotalVencido,
                COUNT(CASE WHEN FechaVencimiento < CAST(GETDATE() AS DATE) 
                           AND MontoOriginal > MontoPagado THEN 1 END) AS DocsVencidos
            FROM Finanzas_CuentasPorPagar
            WHERE {where}
        """
        
        results = await self._execute_query(query)
        if results:
            return results[0]
        return {
            "TotalDocumentos": 0,
            "TotalOriginal": 0,
            "TotalPagado": 0,
            "TotalPendiente": 0,
            "PendientePago": 0,
            "PagoParcial": 0,
            "Pagado": 0,
            "TotalVencido": 0,
            "DocsVencidos": 0
        }
    
    async def get_cxp_por_proveedor(
        self,
        sucursal_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Obtiene cuentas por pagar agrupadas por proveedor.
        """
        where_clauses = ["c.Activo = 1", "c.MontoOriginal > c.MontoPagado"]
        
        if sucursal_id:
            where_clauses.append(f"c.SucursalID = {sucursal_id}")
        
        where = " AND ".join(where_clauses)
        
        query = f"""
            SELECT 
                c.ProveedorID,
                COUNT(*) AS CantidadDocs,
                SUM(c.MontoOriginal) AS MontoTotal,
                SUM(c.MontoOriginal - c.MontoPagado) AS SaldoPendiente,
                MIN(c.FechaVencimiento) AS VencimientoMasCercano,
                MAX(DATEDIFF(DAY, c.FechaVencimiento, GETDATE())) AS MaxDiasVencido
            FROM Finanzas_CuentasPorPagar c
            WHERE {where}
            GROUP BY c.ProveedorID
            ORDER BY SaldoPendiente DESC
        """
        
        return await self._execute_query(query)
    
    # =========================================================================
    # CONFIGURACIÓN TPV (usa tabla existente)
    # =========================================================================
    
    async def get_config_tpv(self, sucursal_id: Optional[int] = None) -> List[Dict]:
        """
        Obtiene configuración de comisiones TPV desde Finanzas_ConfiguracionTPV_Sucursal.
        """
        where_clauses = ["c.Activo = 1"]
        
        if sucursal_id:
            where_clauses.append(f"c.SucursalID = {sucursal_id}")
        
        where = " AND ".join(where_clauses)
        
        query = f"""
            SELECT 
                c.ConfiguracionTPVID,
                c.SucursalID,
                s.Nombre_Sucursal AS SucursalNombre,
                c.ProveedorTPV,
                c.ComisionDebito,
                c.ComisionCredito,
                c.ComisionAmex,
                c.ComisionInternacional,
                c.DiasDepositoDebito,
                c.DiasDepositoCredito,
                c.DiasDepositoAmex,
                c.DiasDepositoInternacional,
                c.TerminalID
            FROM Finanzas_ConfiguracionTPV_Sucursal c
            LEFT JOIN RH_Cat_Sucursales s ON c.SucursalID = s.SucursalID
            WHERE {where}
            ORDER BY s.Nombre_Sucursal
        """
        
        return await self._execute_query(query)
    
    # =========================================================================
    # SUCURSALES
    # =========================================================================
    
    async def get_sucursales(self) -> List[Dict]:
        """Obtiene lista de sucursales activas"""
        query = """
            SELECT SucursalID, Nombre_Sucursal, Activo
            FROM RH_Cat_Sucursales
            WHERE Activo = 1
            ORDER BY Nombre_Sucursal
        """
        return await self._execute_query(query)
    
    # =========================================================================
    # ESTATUS
    # =========================================================================
    
    async def get_estatus_pago(self) -> List[Dict]:
        """Obtiene catálogo de estatus de pago"""
        query = """
            SELECT EstatusPagoID, Nombre, Descripcion
            FROM Finanzas_EstatusPago
            WHERE Activo = 1
            ORDER BY EstatusPagoID
        """
        return await self._execute_query(query)
    
    async def get_estatus_cierre(self) -> List[Dict]:
        """Obtiene catálogo de estatus de cierre"""
        query = """
            SELECT EstatusCierreID, Nombre, Descripcion
            FROM Finanzas_EstatusCierre
            WHERE Activo = 1
            ORDER BY EstatusCierreID
        """
        return await self._execute_query(query)
