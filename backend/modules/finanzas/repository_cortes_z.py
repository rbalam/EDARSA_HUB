"""
Repositorio para obtener Cortes Z de SoftRestaurant y MPRO
"""
import logging
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os

# Configuración de conexiones
SOFTREST_SERVERS = {
    'CIENFUEGOS': {
        'host': os.environ.get('SOFTREST_CIENFUEGOS_HOST', '187.188.198.241'),
        'port': int(os.environ.get('SOFTREST_CIENFUEGOS_PORT', '51741')),
        'database': os.environ.get('SOFTREST_CIENFUEGOS_DB', 'Abordo'),
        'user': os.environ.get('SOFTREST_CIENFUEGOS_USER', 'sa'),
        'password': os.environ.get('SOFTREST_CIENFUEGOS_PASS', 'Sr2022$')
    },
    'LA_ESTELAR': {
        'host': os.environ.get('SOFTREST_ESTELAR_HOST', '187.188.198.241'),
        'port': int(os.environ.get('SOFTREST_ESTELAR_PORT', '51742')),
        'database': os.environ.get('SOFTREST_ESTELAR_DB', 'Bordo'),
        'user': os.environ.get('SOFTREST_ESTELAR_USER', 'sa'),
        'password': os.environ.get('SOFTREST_ESTELAR_PASS', 'Sr2022$')
    },
    '130_MERIDA': {
        'host': os.environ.get('SOFTREST_130MID_HOST', '187.188.198.241'),
        'port': int(os.environ.get('SOFTREST_130MID_PORT', '51743')),
        'database': os.environ.get('SOFTREST_130MID_DB', 'Abordo'),
        'user': os.environ.get('SOFTREST_130MID_USER', 'sa'),
        'password': os.environ.get('SOFTREST_130MID_PASS', 'Sr2022$')
    }
}

MPRO_SERVERS = {
    'MPRO_ORIGEN': {
        'host': os.environ.get('MPRO_ORIGEN_HOST', '187.188.198.241'),
        'port': int(os.environ.get('MPRO_ORIGEN_PORT', '1433')),
        'database': os.environ.get('MPRO_ORIGEN_DB', 'CENTRAL2020'),
        'user': os.environ.get('MPRO_ORIGEN_USER', 'sa'),
        'password': os.environ.get('MPRO_ORIGEN_PASS', 'Edarsa2018$')
    },
    'MPRO_QUERETARO': {
        'host': os.environ.get('MPRO_QRO_HOST', '187.188.198.241'),
        'port': int(os.environ.get('MPRO_QRO_PORT', '1433')),
        'database': os.environ.get('MPRO_QRO_DB', 'CENTRAL2020'),
        'user': os.environ.get('MPRO_QRO_USER', 'sa'),
        'password': os.environ.get('MPRO_QRO_PASS', 'Edarsa2018$')
    }
}


class RepositoryCortesZ:
    """Repositorio para consultar Cortes Z de múltiples fuentes"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def _execute_query_softrest(self, server_name: str, query: str) -> List[Dict]:
        """Ejecuta query en servidor SoftRestaurant"""
        import pytds
        config = SOFTREST_SERVERS.get(server_name)
        if not config:
            self.logger.error(f"Servidor SoftRestaurant no configurado: {server_name}")
            return []
        
        try:
            with pytds.connect(
                server=config['host'],
                port=config['port'],
                database=config['database'],
                user=config['user'],
                password=config['password'],
                timeout=5,  # Reducido de 30 a 5 segundos
                login_timeout=5,  # Reducido de 15 a 5 segundos
                as_dict=True
            ) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Error conectando a SoftRestaurant {server_name}: {e}")
            return []
    
    async def _execute_query_mpro(self, server_name: str, query: str) -> List[Dict]:
        """Ejecuta query en servidor MPRO"""
        import pytds
        config = MPRO_SERVERS.get(server_name)
        if not config:
            self.logger.error(f"Servidor MPRO no configurado: {server_name}")
            return []
        
        try:
            with pytds.connect(
                server=config['host'],
                port=config['port'],
                database=config['database'],
                user=config['user'],
                password=config['password'],
                timeout=5,  # Reducido de 30 a 5 segundos
                login_timeout=5,  # Reducido de 15 a 5 segundos
                as_dict=True
            ) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Error conectando a MPRO {server_name}: {e}")
            return []
    
    async def get_cortes_z_softrestaurant(
        self, 
        server_name: str,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        folio: Optional[str] = None
    ) -> List[Dict]:
        """
        Obtiene Cortes Z de SoftRestaurant.
        Tablas: movtoscaja, movtoscajadetalles
        """
        # Construir filtros
        where_clauses = ["mc.idtipomovtocaja = 3"]  # 3 = Corte Z
        
        if fecha_inicio:
            where_clauses.append(f"CAST(mc.fecha AS DATE) >= '{fecha_inicio}'")
        if fecha_fin:
            where_clauses.append(f"CAST(mc.fecha AS DATE) <= '{fecha_fin}'")
        if folio:
            where_clauses.append(f"mc.folio = '{folio}'")
        
        where_sql = " AND ".join(where_clauses)
        
        query = f"""
        SELECT 
            mc.idmovtocaja AS CorteID,
            mc.folio AS FolioCorte,
            mc.fecha AS FechaCorte,
            mc.idestacion AS EstacionID,
            e.descripcion AS EstacionNombre,
            ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d 
                    WHERE d.idmovtocaja = mc.idmovtocaja 
                    AND d.idconcepto = 1), 0) AS EfectivoInicial,
            ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d 
                    WHERE d.idmovtocaja = mc.idmovtocaja 
                    AND d.idconcepto = 2), 0) AS EfectivoVentas,
            ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d 
                    WHERE d.idmovtocaja = mc.idmovtocaja 
                    AND d.idconcepto IN (10, 11, 12)), 0) AS Tarjeta,
            ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d 
                    WHERE d.idmovtocaja = mc.idmovtocaja 
                    AND d.idconcepto = 5), 0) AS Vales,
            ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d 
                    WHERE d.idmovtocaja = mc.idmovtocaja 
                    AND d.idconcepto = 6), 0) AS Otros,
            ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d 
                    WHERE d.idmovtocaja = mc.idmovtocaja 
                    AND d.idconcepto = 7), 0) AS DepositosEf,
            ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d 
                    WHERE d.idmovtocaja = mc.idmovtocaja 
                    AND d.idconcepto = 8), 0) AS RetirosEf,
            ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d 
                    WHERE d.idmovtocaja = mc.idmovtocaja 
                    AND d.idconcepto = 9), 0) AS PropinasPagadas,
            mc.saldo AS SaldoFinal,
            mc.efectivo AS EfectivoFinal,
            ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d 
                    WHERE d.idmovtocaja = mc.idmovtocaja), 0) AS TotalVentas
        FROM movtoscaja mc
        LEFT JOIN estaciones e ON mc.idestacion = e.idestacion
        WHERE {where_sql}
        ORDER BY mc.fecha DESC
        """
        
        try:
            results = await self._execute_query_softrest(server_name, query)
            cortes = []
            
            for r in results:
                efectivo_ventas = float(r.get('EfectivoVentas', 0) or 0)
                propinas = float(r.get('PropinasPagadas', 0) or 0)
                
                corte = {
                    'folio_corte': str(r.get('FolioCorte', '')),
                    'fecha_corte': r.get('FechaCorte').isoformat() if r.get('FechaCorte') else None,
                    'sucursal_id': server_name,
                    'sucursal_nombre': server_name.replace('_', ' '),
                    'fuente': 'SOFTRESTAURANT',
                    'efectivo_inicial': float(r.get('EfectivoInicial', 0) or 0),
                    'efectivo_ventas': efectivo_ventas,
                    'tarjeta': float(r.get('Tarjeta', 0) or 0),
                    'vales': float(r.get('Vales', 0) or 0),
                    'otros': float(r.get('Otros', 0) or 0),
                    'depositos_ef': float(r.get('DepositosEf', 0) or 0),
                    'retiros_ef': float(r.get('RetirosEf', 0) or 0),
                    'propinas_pagadas': propinas,
                    'saldo_final': float(r.get('SaldoFinal', 0) or 0),
                    'efectivo_final': float(r.get('EfectivoFinal', 0) or 0),
                    'total_ventas': float(r.get('TotalVentas', 0) or 0),
                    'monto_a_depositar': efectivo_ventas - propinas
                }
                cortes.append(corte)
            
            return cortes
        except Exception as e:
            self.logger.error(f"Error obteniendo Cortes Z de {server_name}: {e}")
            return []
    
    async def get_cortes_z_mpro(
        self, 
        server_name: str,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None
    ) -> List[Dict]:
        """
        Obtiene Cortes Z de MPRO.
        Tablas: caja, pos_control_cajas
        """
        where_clauses = ["c.tipo_movimiento = 'CIERRE'"]
        
        if fecha_inicio:
            where_clauses.append(f"CAST(c.fecha AS DATE) >= '{fecha_inicio}'")
        if fecha_fin:
            where_clauses.append(f"CAST(c.fecha AS DATE) <= '{fecha_fin}'")
        
        where_sql = " AND ".join(where_clauses)
        
        query = f"""
        SELECT 
            c.id_caja AS CorteID,
            c.folio AS FolioCorte,
            c.fecha AS FechaCorte,
            c.id_sucursal AS SucursalID,
            s.nombre AS SucursalNombre,
            ISNULL(c.fondo_inicial, 0) AS EfectivoInicial,
            ISNULL(c.efectivo, 0) AS EfectivoVentas,
            ISNULL(c.tarjeta_credito, 0) + ISNULL(c.tarjeta_debito, 0) AS Tarjeta,
            ISNULL(c.vales, 0) AS Vales,
            ISNULL(c.otros, 0) AS Otros,
            ISNULL(c.depositos, 0) AS DepositosEf,
            ISNULL(c.retiros, 0) AS RetirosEf,
            ISNULL(c.propinas, 0) AS PropinasPagadas,
            ISNULL(c.total, 0) AS SaldoFinal,
            ISNULL(c.efectivo_final, 0) AS EfectivoFinal,
            ISNULL(c.total_ventas, 0) AS TotalVentas
        FROM caja c
        LEFT JOIN sucursales s ON c.id_sucursal = s.id_sucursal
        WHERE {where_sql}
        ORDER BY c.fecha DESC
        """
        
        try:
            results = await self._execute_query_mpro(server_name, query)
            cortes = []
            
            for r in results:
                efectivo_ventas = float(r.get('EfectivoVentas', 0) or 0)
                propinas = float(r.get('PropinasPagadas', 0) or 0)
                
                corte = {
                    'folio_corte': str(r.get('FolioCorte', '')),
                    'fecha_corte': r.get('FechaCorte').isoformat() if r.get('FechaCorte') else None,
                    'sucursal_id': f"{server_name}_{r.get('SucursalID', '')}",
                    'sucursal_nombre': r.get('SucursalNombre', server_name),
                    'fuente': 'MPRO',
                    'efectivo_inicial': float(r.get('EfectivoInicial', 0) or 0),
                    'efectivo_ventas': efectivo_ventas,
                    'tarjeta': float(r.get('Tarjeta', 0) or 0),
                    'vales': float(r.get('Vales', 0) or 0),
                    'otros': float(r.get('Otros', 0) or 0),
                    'depositos_ef': float(r.get('DepositosEf', 0) or 0),
                    'retiros_ef': float(r.get('RetirosEf', 0) or 0),
                    'propinas_pagadas': propinas,
                    'saldo_final': float(r.get('SaldoFinal', 0) or 0),
                    'efectivo_final': float(r.get('EfectivoFinal', 0) or 0),
                    'total_ventas': float(r.get('TotalVentas', 0) or 0),
                    'monto_a_depositar': efectivo_ventas - propinas
                }
                cortes.append(corte)
            
            return cortes
        except Exception as e:
            self.logger.error(f"Error obteniendo Cortes Z de MPRO {server_name}: {e}")
            return []
    
    async def get_all_cortes_z(
        self,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None
    ) -> List[Dict]:
        """Obtiene Cortes Z de todas las fuentes en paralelo"""
        
        # Crear tareas para todas las fuentes
        tasks = []
        
        # SoftRestaurant
        for server_name in SOFTREST_SERVERS.keys():
            tasks.append(self.get_cortes_z_softrestaurant(server_name, fecha_inicio, fecha_fin))
        
        # MPRO
        for server_name in MPRO_SERVERS.keys():
            tasks.append(self.get_cortes_z_mpro(server_name, fecha_inicio, fecha_fin))
        
        # Ejecutar en paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combinar resultados
        all_cortes = []
        for result in results:
            if isinstance(result, list):
                all_cortes.extend(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Error en consulta paralela: {result}")
        
        # Ordenar por fecha descendente
        all_cortes.sort(key=lambda x: x.get('fecha_corte', ''), reverse=True)
        
        return all_cortes


# Singleton
_repository_instance = None

async def get_cortes_z_repository() -> RepositoryCortesZ:
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = RepositoryCortesZ()
    return _repository_instance
