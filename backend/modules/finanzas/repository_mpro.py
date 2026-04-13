"""
EDARSA HUB - Finanzas Repository (MPRO - CENTRAL2020)
======================================================
Repositorio para acceso a datos REALES de Cuentas por Pagar desde MPRO.

TABLAS CONECTADAS:
- Cuenta_X_Pagar: Cuentas por pagar de todas las sucursales
- Proveedor: Catálogo de proveedores
- Sucursal: Catálogo de sucursales

ABRIL 2026: Conexión a datos reales de MPRO CENTRAL2020
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from core.db import execute_sql_query, ResilientConfig

# ID del servidor MPRO en MongoDB
MPRO_SERVER_ID = "1b230a06-ffaf-4c70-bd27-b1be3579dea6"


class FinanzasRepositoryMPRO:
    """
    Repositorio para acceso a datos REALES de Cuentas por Pagar desde MPRO.
    Usa la tabla Cuenta_X_Pagar en CENTRAL2020.
    """
    
    def __init__(self, db):
        """
        Args:
            db: Instancia de MongoDB para obtener configuración del servidor
        """
        self.db = db
        self._server_cache = None
    
    async def _get_server(self) -> Optional[Dict]:
        """Obtiene la configuración del servidor MPRO"""
        if self._server_cache:
            return self._server_cache
        
        self._server_cache = await self.db.servers.find_one({
            "id": MPRO_SERVER_ID,
            "active": True
        })
        return self._server_cache
    
    async def _execute_query(self, query: str, timeout: int = None) -> List[Dict]:
        """Ejecuta una query en MPRO con la lógica resiliente."""
        server = await self._get_server()
        if not server:
            self._server_cache = None
            server = await self._get_server()
            
        if not server:
            logging.error("[FinanzasRepoMPRO] Servidor MPRO no encontrado")
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
            logging.error(f"[FinanzasRepoMPRO] Error ejecutando query: {e}")
            return []
    
    async def get_sucursales(self) -> List[Dict]:
        """Obtiene las sucursales de MPRO"""
        query = """
            SELECT 
                Sc_Cve_Sucursal as SucursalID,
                Sc_Descripcion as Nombre_Sucursal
            FROM Sucursal
            ORDER BY Sc_Descripcion
        """
        return await self._execute_query(query)
    
    async def get_cuentas_por_pagar(
        self,
        sucursal_id: Optional[str] = None,
        proveedor_id: Optional[str] = None,
        solo_vencidas: bool = False,
        fecha_corte: Optional[str] = None,
        limit: int = 500
    ) -> List[Dict]:
        """
        Obtiene cuentas por pagar desde MPRO.
        
        Args:
            sucursal_id: Clave de sucursal (ej: '0027' para CIEN FUEGOS)
            proveedor_id: Clave de proveedor
            solo_vencidas: Solo documentos vencidos
            fecha_corte: Fecha de corte para calcular vencimiento
            limit: Máximo de registros
        
        Returns:
            Lista de cuentas por pagar normalizadas
        """
        where_clauses = [
            "c.Es_Cve_Estado = 'AC'",
            "c.Cxp_Precio_Neto_Saldo > 0"
        ]
        
        if sucursal_id:
            where_clauses.append(f"c.Sc_Cve_Sucursal = '{sucursal_id}'")
        if proveedor_id:
            where_clauses.append(f"c.Pv_Cve_Proveedor = '{proveedor_id}'")
        if solo_vencidas:
            fecha = fecha_corte or datetime.now().strftime('%Y-%m-%d')
            where_clauses.append(f"c.Cxp_Fecha_Vencimiento < '{fecha}'")
        
        where = " AND ".join(where_clauses)
        
        query = f"""
            SELECT TOP {limit}
                c.Cxp_Folio as CuentaPorPagarID,
                c.Cxp_Folio as FolioEntrada,
                c.Cxp_Documento as FolioFactura,
                c.Sc_Cve_Sucursal as SucursalID,
                s.Sc_Descripcion as SucursalNombre,
                c.Pv_Cve_Proveedor as ProveedorID,
                p.Pv_Razon_Social as ProveedorNombre,
                p.Pv_R_F_C as ProveedorRFC,
                c.Cxp_Fecha as FechaEntrada,
                c.Cxp_Fecha_Vencimiento as FechaVencimiento,
                c.Cxp_Precio_Neto_Importe as MontoOriginal,
                c.Cxp_Precio_Neto_Pago as MontoPagado,
                c.Cxp_Precio_Neto_Saldo as Saldo,
                c.Cxp_Referencia as Referencia,
                c.Cxp_Concepto as Concepto,
                DATEDIFF(day, c.Cxp_Fecha_Vencimiento, GETDATE()) as DiasVencido,
                c.Es_Cve_Estado as Estado
            FROM Cuenta_X_Pagar c
            LEFT JOIN Proveedor p ON c.Pv_Cve_Proveedor = p.Pv_Cve_Proveedor
            LEFT JOIN Sucursal s ON c.Sc_Cve_Sucursal = s.Sc_Cve_Sucursal
            WHERE {where}
            ORDER BY c.Cxp_Fecha DESC
        """
        
        return await self._execute_query(query)
    
    async def get_resumen_por_sucursal(self) -> List[Dict]:
        """Obtiene resumen de CxP agrupado por sucursal"""
        query = """
            SELECT 
                c.Sc_Cve_Sucursal as SucursalID,
                s.Sc_Descripcion as SucursalNombre,
                COUNT(*) as CantidadFacturas,
                SUM(c.Cxp_Precio_Neto_Saldo) as SaldoTotal,
                SUM(CASE WHEN c.Cxp_Fecha_Vencimiento < GETDATE() THEN 1 ELSE 0 END) as Vencidas,
                SUM(CASE WHEN c.Cxp_Fecha_Vencimiento < GETDATE() THEN c.Cxp_Precio_Neto_Saldo ELSE 0 END) as SaldoVencido
            FROM Cuenta_X_Pagar c
            LEFT JOIN Sucursal s ON c.Sc_Cve_Sucursal = s.Sc_Cve_Sucursal
            WHERE c.Es_Cve_Estado = 'AC' AND c.Cxp_Precio_Neto_Saldo > 0
            GROUP BY c.Sc_Cve_Sucursal, s.Sc_Descripcion
            ORDER BY SaldoTotal DESC
        """
        return await self._execute_query(query)
    
    async def get_resumen_por_proveedor(self, sucursal_id: Optional[str] = None) -> List[Dict]:
        """Obtiene resumen de CxP agrupado por proveedor"""
        where_clauses = [
            "c.Es_Cve_Estado = 'AC'",
            "c.Cxp_Precio_Neto_Saldo > 0"
        ]
        
        if sucursal_id:
            where_clauses.append(f"c.Sc_Cve_Sucursal = '{sucursal_id}'")
        
        where = " AND ".join(where_clauses)
        
        query = f"""
            SELECT 
                c.Pv_Cve_Proveedor as ProveedorID,
                p.Pv_Razon_Social as ProveedorNombre,
                p.Pv_R_F_C as ProveedorRFC,
                COUNT(*) as CantidadFacturas,
                SUM(c.Cxp_Precio_Neto_Saldo) as SaldoTotal,
                SUM(CASE WHEN c.Cxp_Fecha_Vencimiento < GETDATE() THEN 1 ELSE 0 END) as Vencidas,
                SUM(CASE WHEN c.Cxp_Fecha_Vencimiento < GETDATE() THEN c.Cxp_Precio_Neto_Saldo ELSE 0 END) as SaldoVencido
            FROM Cuenta_X_Pagar c
            LEFT JOIN Proveedor p ON c.Pv_Cve_Proveedor = p.Pv_Cve_Proveedor
            WHERE {where}
            GROUP BY c.Pv_Cve_Proveedor, p.Pv_Razon_Social, p.Pv_R_F_C
            ORDER BY SaldoTotal DESC
        """
        return await self._execute_query(query)
    
    async def get_resumen_antiguedad(self, sucursal_id: Optional[str] = None) -> Dict:
        """Obtiene resumen de antigüedad de saldos"""
        where_clauses = [
            "c.Es_Cve_Estado = 'AC'",
            "c.Cxp_Precio_Neto_Saldo > 0"
        ]
        
        if sucursal_id:
            where_clauses.append(f"c.Sc_Cve_Sucursal = '{sucursal_id}'")
        
        where = " AND ".join(where_clauses)
        
        query = f"""
            SELECT 
                SUM(CASE WHEN DATEDIFF(day, c.Cxp_Fecha_Vencimiento, GETDATE()) <= 0 THEN c.Cxp_Precio_Neto_Saldo ELSE 0 END) as Corriente,
                SUM(CASE WHEN DATEDIFF(day, c.Cxp_Fecha_Vencimiento, GETDATE()) <= 0 THEN 1 ELSE 0 END) as CorrienteCant,
                SUM(CASE WHEN DATEDIFF(day, c.Cxp_Fecha_Vencimiento, GETDATE()) BETWEEN 1 AND 30 THEN c.Cxp_Precio_Neto_Saldo ELSE 0 END) as Vencido1_30,
                SUM(CASE WHEN DATEDIFF(day, c.Cxp_Fecha_Vencimiento, GETDATE()) BETWEEN 1 AND 30 THEN 1 ELSE 0 END) as Vencido1_30Cant,
                SUM(CASE WHEN DATEDIFF(day, c.Cxp_Fecha_Vencimiento, GETDATE()) BETWEEN 31 AND 60 THEN c.Cxp_Precio_Neto_Saldo ELSE 0 END) as Vencido31_60,
                SUM(CASE WHEN DATEDIFF(day, c.Cxp_Fecha_Vencimiento, GETDATE()) BETWEEN 31 AND 60 THEN 1 ELSE 0 END) as Vencido31_60Cant,
                SUM(CASE WHEN DATEDIFF(day, c.Cxp_Fecha_Vencimiento, GETDATE()) BETWEEN 61 AND 90 THEN c.Cxp_Precio_Neto_Saldo ELSE 0 END) as Vencido61_90,
                SUM(CASE WHEN DATEDIFF(day, c.Cxp_Fecha_Vencimiento, GETDATE()) BETWEEN 61 AND 90 THEN 1 ELSE 0 END) as Vencido61_90Cant,
                SUM(CASE WHEN DATEDIFF(day, c.Cxp_Fecha_Vencimiento, GETDATE()) > 90 THEN c.Cxp_Precio_Neto_Saldo ELSE 0 END) as Vencido90Plus,
                SUM(CASE WHEN DATEDIFF(day, c.Cxp_Fecha_Vencimiento, GETDATE()) > 90 THEN 1 ELSE 0 END) as Vencido90PlusCant,
                COUNT(*) as TotalFacturas,
                SUM(c.Cxp_Precio_Neto_Saldo) as TotalSaldo
            FROM Cuenta_X_Pagar c
            WHERE {where}
        """
        
        results = await self._execute_query(query)
        if results:
            r = results[0]
            return {
                "corriente": {
                    "cantidad": int(r.get('CorrienteCant') or 0),
                    "monto": float(r.get('Corriente') or 0)
                },
                "vencidas_1_30": {
                    "cantidad": int(r.get('Vencido1_30Cant') or 0),
                    "monto": float(r.get('Vencido1_30') or 0)
                },
                "vencidas_31_60": {
                    "cantidad": int(r.get('Vencido31_60Cant') or 0),
                    "monto": float(r.get('Vencido31_60') or 0)
                },
                "vencidas_61_90": {
                    "cantidad": int(r.get('Vencido61_90Cant') or 0),
                    "monto": float(r.get('Vencido61_90') or 0)
                },
                "vencidas_90_plus": {
                    "cantidad": int(r.get('Vencido90PlusCant') or 0),
                    "monto": float(r.get('Vencido90Plus') or 0)
                },
                "total_facturas": int(r.get('TotalFacturas') or 0),
                "total_saldo": float(r.get('TotalSaldo') or 0)
            }
        
        return {
            "corriente": {"cantidad": 0, "monto": 0},
            "vencidas_1_30": {"cantidad": 0, "monto": 0},
            "vencidas_31_60": {"cantidad": 0, "monto": 0},
            "vencidas_61_90": {"cantidad": 0, "monto": 0},
            "vencidas_90_plus": {"cantidad": 0, "monto": 0},
            "total_facturas": 0,
            "total_saldo": 0
        }
    
    async def get_proveedores(self) -> List[Dict]:
        """Obtiene catálogo de proveedores con saldo pendiente"""
        query = """
            SELECT DISTINCT
                p.Pv_Cve_Proveedor as ProveedorID,
                p.Pv_Razon_Social as NombreComercial,
                p.Pv_R_F_C as RFC
            FROM Proveedor p
            INNER JOIN Cuenta_X_Pagar c ON p.Pv_Cve_Proveedor = c.Pv_Cve_Proveedor
            WHERE c.Es_Cve_Estado = 'AC' AND c.Cxp_Precio_Neto_Saldo > 0
            ORDER BY p.Pv_Razon_Social
        """
        return await self._execute_query(query)
