"""
EDARSA HUB - Finanzas Repository (SoftRestaurant Multi-Sucursal)
================================================================
Repositorio para acceso a datos REALES de Cuentas por Pagar desde
servidores SoftRestaurant de cada sucursal.

SUCURSALES CONECTADAS:
- CIENFUEGOS: servercienfuegos.ddns.net:6669 / softrestaurant95pro (Vista: AC_vwSaldoCxp)
- LA ESTELAR: serverestelar.ddns.net:6969 / softrestaurant12 (Vista: AC_vwSaldoCxp)
- 130° MERIDA: 130mid.ddns.net:1433 / softrestaurant10 (Vista: vwSaldoCxp)

AGRUPACIÓN DE PROVEEDORES:
- A = ALIMENTOS
- B = BEBIDAS
- X = OTROS (incluye servicios, préstamos, etc.)

Formato nombre proveedor: "[XXXX] TYYYY NOMBRE" donde T es el tipo (A, B, X)

ABRIL 2026: Conexión directa a SoftRestaurant de cada sucursal
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from decimal import Decimal
import pytds

# Configuración de servidores SoftRestaurant (desde menú de servidores)
SOFTRESTAURANT_SERVERS = {
    "CIENFUEGOS": {
        "id": "CF",
        "name": "CIEN FUEGOS",
        "host": "servercienfuegos.ddns.net",
        "port": 6669,
        "database": "softrestaurant95pro",
        "username": "CFLectura",
        "password": "National09",
        "view": "AC_vwSaldoCxp"
    },
    "ESTELAR": {
        "id": "EST",
        "name": "LA ESTELAR",
        "host": "serverestelar.ddns.net",
        "port": 6969,
        "database": "softrestaurant12",
        "username": "SCedarsa",
        "password": "C0ntr4s3ña#2026",
        "view": "AC_vwSaldoCxp"
    },
    "130MID": {
        "id": "130M",
        "name": "130° MERIDA",
        "host": "130mid.ddns.net",
        "port": 1433,
        "database": "softrestaurant10",
        "username": "SCedarsa",
        "password": "C0ntr4s3ña#2026",
        "view": "vwSaldoCxp"
    }
}


def get_tipo_proveedor(nombre_proveedor: str) -> str:
    """
    Extrae el tipo de proveedor del nombre.
    Formato: "[XXXX] TYYYY NOMBRE" donde T es A, B o X
    Ejemplos:
      - "[0357] X0357 MAGER" → X
      - "[0406] B0406 CONVENIO CERVECERIA" → B
      - "[0015] A0015 CARNES ROJAS" → A
    
    Returns:
        'A' = Alimentos
        'B' = Bebidas
        'X' = Otros
    """
    if not nombre_proveedor:
        return 'X'
    
    nombre = nombre_proveedor.strip()
    
    # Buscar patrón "[XXXX] TYYYY" donde T es la letra de tipo
    if nombre.startswith('['):
        # Encontrar el cierre del corchete
        idx = nombre.find('] ')
        if idx > 0 and len(nombre) > idx + 2:
            tipo_letra = nombre[idx + 2].upper()
            if tipo_letra == 'A':
                return 'A'
            elif tipo_letra == 'B':
                return 'B'
            else:
                return 'X'
    
    # Formato alternativo "(XXX) T NOMBRE"
    if nombre.startswith('('):
        idx = nombre.find(') ')
        if idx > 0 and len(nombre) > idx + 2:
            tipo_letra = nombre[idx + 2].upper()
            if tipo_letra == 'A':
                return 'A'
            elif tipo_letra == 'B':
                return 'B'
    
    return 'X'


def get_nombre_tipo(tipo: str) -> str:
    """Devuelve el nombre descriptivo del tipo"""
    tipos = {
        'A': 'ALIMENTOS',
        'B': 'BEBIDAS',
        'X': 'OTROS'
    }
    return tipos.get(tipo, 'OTROS')


class FinanzasRepositorySoftRestaurant:
    """
    Repositorio para acceso a datos REALES de CxP desde SoftRestaurant.
    Consulta múltiples sucursales y agrupa por tipo de proveedor.
    """
    
    def __init__(self, db=None):
        """
        Args:
            db: Instancia de MongoDB (opcional, para compatibilidad)
        """
        self.db = db
        self._connection_cache = {}
    
    def _get_connection(self, server_key: str):
        """Obtiene conexión a un servidor SoftRestaurant"""
        if server_key not in SOFTRESTAURANT_SERVERS:
            logging.error(f"[SoftRestaurant] Servidor desconocido: {server_key}")
            return None
        
        srv = SOFTRESTAURANT_SERVERS[server_key]
        
        try:
            conn = pytds.connect(
                server=srv['host'],
                port=srv['port'],
                database=srv['database'],
                user=srv['username'],
                password=srv['password'],
                timeout=20,
                login_timeout=15
            )
            return conn
        except Exception as e:
            logging.error(f"[SoftRestaurant] Error conectando a {server_key}: {e}")
            return None
    
    def _execute_query(self, server_key: str, query: str) -> List[Dict]:
        """Ejecuta una query en un servidor específico"""
        conn = self._get_connection(server_key)
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                row_dict = {}
                for i, col in enumerate(columns):
                    val = row[i]
                    # Convertir Decimal a float
                    if isinstance(val, Decimal):
                        val = float(val)
                    row_dict[col] = val
                results.append(row_dict)
            conn.close()
            return results
        except Exception as e:
            logging.error(f"[SoftRestaurant] Error en query {server_key}: {e}")
            try:
                conn.close()
            except:
                pass
            return []
    
    async def get_sucursales(self) -> List[Dict]:
        """Obtiene lista de sucursales configuradas"""
        sucursales = []
        for key, srv in SOFTRESTAURANT_SERVERS.items():
            sucursales.append({
                "SucursalID": key,
                "SucursalCodigo": srv['id'],
                "Nombre_Sucursal": srv['name']
            })
        return sucursales
    
    async def get_cuentas_por_pagar(
        self,
        sucursal_id: Optional[str] = None,
        tipo_proveedor: Optional[str] = None,
        limit: int = 500
    ) -> List[Dict]:
        """
        Obtiene cuentas por pagar desde SoftRestaurant.
        
        Args:
            sucursal_id: Clave de sucursal (CIENFUEGOS, ESTELAR, 130MID)
            tipo_proveedor: A=Alimentos, B=Bebidas, X=Otros
            limit: Máximo de registros
        
        Returns:
            Lista de CxP con tipo de proveedor y antigüedad
        """
        all_results = []
        
        # Determinar qué servidores consultar
        servers_to_query = [sucursal_id] if sucursal_id and sucursal_id in SOFTRESTAURANT_SERVERS else list(SOFTRESTAURANT_SERVERS.keys())
        
        for server_key in servers_to_query:
            srv = SOFTRESTAURANT_SERVERS.get(server_key)
            if not srv:
                continue
            
            # Usar la vista correcta para cada servidor
            view_name = srv.get('view', 'vwSaldoCxp')
            
            query = f"""
                SELECT TOP {limit}
                    PROVEEDOR,
                    [POR VENCER] as PorVencer,
                    [01-15] as Venc1_15,
                    [16-30] as Venc16_30,
                    [31-60] as Venc31_60,
                    [61-90] as Venc61_90,
                    [91-120] as Venc91_120,
                    [121-150] as Venc121_150,
                    [+151] as VencMas151,
                    [Total CXP] as TotalCXP,
                    fechaaplicacion
                FROM {view_name}
                WHERE [Total CXP] > 0
                ORDER BY [Total CXP] DESC
            """
            
            results = self._execute_query(server_key, query)
            
            for r in results:
                proveedor = r.get('PROVEEDOR', '')
                tipo = get_tipo_proveedor(proveedor)
                
                # Filtrar por tipo si se especificó
                if tipo_proveedor and tipo != tipo_proveedor:
                    continue
                
                saldo_total = float(r.get('TotalCXP', 0) or 0)
                if saldo_total <= 0:
                    continue
                
                # Calcular días vencido (aproximado basado en rangos)
                por_vencer = float(r.get('PorVencer', 0) or 0)
                venc_1_15 = float(r.get('Venc1_15', 0) or 0)
                venc_16_30 = float(r.get('Venc16_30', 0) or 0)
                venc_31_60 = float(r.get('Venc31_60', 0) or 0)
                venc_61_90 = float(r.get('Venc61_90', 0) or 0)
                venc_91_120 = float(r.get('Venc91_120', 0) or 0)
                venc_121_150 = float(r.get('Venc121_150', 0) or 0)
                venc_mas_151 = float(r.get('VencMas151', 0) or 0)
                
                # Determinar antigüedad predominante
                if venc_mas_151 > 0:
                    dias_vencido = 180
                elif venc_121_150 > 0:
                    dias_vencido = 135
                elif venc_91_120 > 0:
                    dias_vencido = 105
                elif venc_61_90 > 0:
                    dias_vencido = 75
                elif venc_31_60 > 0:
                    dias_vencido = 45
                elif venc_16_30 > 0:
                    dias_vencido = 23
                elif venc_1_15 > 0:
                    dias_vencido = 8
                else:
                    dias_vencido = 0
                
                all_results.append({
                    "CuentaPorPagarID": f"{server_key}_{proveedor[:20]}",
                    "SucursalID": server_key,
                    "SucursalNombre": srv['name'],
                    "ProveedorID": proveedor[:10] if proveedor else "N/A",
                    "ProveedorNombre": proveedor,
                    "ProveedorRFC": "",
                    "TipoProveedor": tipo,
                    "TipoProveedorNombre": get_nombre_tipo(tipo),
                    "FechaEntrada": r.get('fechaaplicacion'),
                    "MontoOriginal": saldo_total,
                    "Saldo": saldo_total,
                    "PorVencer": por_vencer,
                    "Venc1_30": venc_1_15 + venc_16_30,
                    "Venc31_60": venc_31_60,
                    "Venc61_90": venc_61_90,
                    "Venc91Plus": venc_91_120 + venc_121_150 + venc_mas_151,
                    "DiasVencido": dias_vencido
                })
        
        return all_results
    
    async def get_resumen_antiguedad(self, sucursal_id: Optional[str] = None) -> Dict:
        """Obtiene resumen de antigüedad de saldos"""
        cxp = await self.get_cuentas_por_pagar(sucursal_id=sucursal_id, limit=2000)
        
        totales = {
            "corriente": {"cantidad": 0, "monto": 0.0},
            "vencidas_1_30": {"cantidad": 0, "monto": 0.0},
            "vencidas_31_60": {"cantidad": 0, "monto": 0.0},
            "vencidas_61_90": {"cantidad": 0, "monto": 0.0},
            "vencidas_90_plus": {"cantidad": 0, "monto": 0.0},
            "total_facturas": 0,
            "total_saldo": 0.0
        }
        
        for c in cxp:
            saldo = float(c.get('Saldo', 0) or 0)
            if saldo <= 0:
                continue
            
            totales["total_facturas"] += 1
            totales["total_saldo"] += saldo
            
            por_vencer = float(c.get('PorVencer', 0) or 0)
            venc_1_30 = float(c.get('Venc1_30', 0) or 0)
            venc_31_60 = float(c.get('Venc31_60', 0) or 0)
            venc_61_90 = float(c.get('Venc61_90', 0) or 0)
            venc_91_plus = float(c.get('Venc91Plus', 0) or 0)
            
            if por_vencer > 0:
                totales["corriente"]["cantidad"] += 1
                totales["corriente"]["monto"] += por_vencer
            if venc_1_30 > 0:
                totales["vencidas_1_30"]["cantidad"] += 1
                totales["vencidas_1_30"]["monto"] += venc_1_30
            if venc_31_60 > 0:
                totales["vencidas_31_60"]["cantidad"] += 1
                totales["vencidas_31_60"]["monto"] += venc_31_60
            if venc_61_90 > 0:
                totales["vencidas_61_90"]["cantidad"] += 1
                totales["vencidas_61_90"]["monto"] += venc_61_90
            if venc_91_plus > 0:
                totales["vencidas_90_plus"]["cantidad"] += 1
                totales["vencidas_90_plus"]["monto"] += venc_91_plus
        
        return totales
    
    async def get_resumen_por_tipo(self, sucursal_id: Optional[str] = None) -> List[Dict]:
        """Obtiene resumen agrupado por tipo de proveedor (A, B, X)"""
        cxp = await self.get_cuentas_por_pagar(sucursal_id=sucursal_id, limit=2000)
        
        tipos = {}
        for c in cxp:
            tipo = c.get('TipoProveedor', 'X')
            if tipo not in tipos:
                tipos[tipo] = {
                    "TipoProveedor": tipo,
                    "TipoNombre": get_nombre_tipo(tipo),
                    "CantidadProveedores": 0,
                    "SaldoTotal": 0.0,
                    "Proveedores": set()
                }
            tipos[tipo]["Proveedores"].add(c.get('ProveedorNombre'))
            tipos[tipo]["SaldoTotal"] += float(c.get('Saldo', 0) or 0)
        
        # Convertir sets a conteos
        result = []
        for tipo, data in sorted(tipos.items()):
            result.append({
                "TipoProveedor": data["TipoProveedor"],
                "TipoNombre": data["TipoNombre"],
                "CantidadProveedores": len(data["Proveedores"]),
                "SaldoTotal": round(data["SaldoTotal"], 2)
            })
        
        return result
    
    async def get_resumen_por_sucursal(self) -> List[Dict]:
        """Obtiene resumen por sucursal"""
        result = []
        
        for server_key, srv in SOFTRESTAURANT_SERVERS.items():
            cxp = await self.get_cuentas_por_pagar(sucursal_id=server_key, limit=2000)
            
            total_saldo = sum(float(c.get('Saldo', 0) or 0) for c in cxp)
            
            result.append({
                "SucursalID": server_key,
                "SucursalNombre": srv['name'],
                "CantidadFacturas": len(cxp),
                "SaldoTotal": round(total_saldo, 2)
            })
        
        return sorted(result, key=lambda x: x['SaldoTotal'], reverse=True)
