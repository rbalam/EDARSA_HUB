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
    
    Formatos soportados:
      1. "[XXXX] TYYYY NOMBRE" donde T es A, B o X → "[0406] B0406 CONVENIO CERVECERIA"
      2. "TXXX NOMBRE" donde T es A, B o X → "A1269 COMERCIALIZADORA CHOBI"
      3. "(XXX) T NOMBRE" 
    
    Returns:
        'A' = Alimentos
        'B' = Bebidas
        'X' = Otros
    """
    if not nombre_proveedor:
        return 'X'
    
    nombre = nombre_proveedor.strip()
    
    # Formato 1: "[XXXX] TYYYY" donde T es la letra de tipo
    if nombre.startswith('['):
        idx = nombre.find('] ')
        if idx > 0 and len(nombre) > idx + 2:
            tipo_letra = nombre[idx + 2].upper()
            if tipo_letra == 'A':
                return 'A'
            elif tipo_letra == 'B':
                return 'B'
            else:
                return 'X'
    
    # Formato 2: "TXXX NOMBRE" donde T es A, B o X (ej: "A1269 COMERCIALIZADORA")
    if len(nombre) >= 2:
        primera_letra = nombre[0].upper()
        segunda_char = nombre[1] if len(nombre) > 1 else ''
        # Verificar que empieza con A, B o X seguido de un número
        if primera_letra in ('A', 'B', 'X') and segunda_char.isdigit():
            if primera_letra == 'A':
                return 'A'
            elif primera_letra == 'B':
                return 'B'
            else:
                return 'X'
    
    # Formato 3: "(XXX) T NOMBRE"
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
        
        ABRIL 2026: Modificado para usar tabla 'compras' directamente
        y obtener campos detallados (folio, factura, vencimiento, referencia).
        
        Args:
            sucursal_id: Clave de sucursal (CIENFUEGOS, ESTELAR, 130MID)
            tipo_proveedor: A=Alimentos, B=Bebidas, X=Otros
            limit: Máximo de registros
        
        Returns:
            Lista de CxP con tipo de proveedor, antigüedad y detalle de documentos
        """
        all_results = []
        
        # Determinar qué servidores consultar
        servers_to_query = [sucursal_id] if sucursal_id and sucursal_id in SOFTRESTAURANT_SERVERS else list(SOFTRESTAURANT_SERVERS.keys())
        
        for server_key in servers_to_query:
            srv = SOFTRESTAURANT_SERVERS.get(server_key)
            if not srv:
                continue
            
            # Query detallada desde tabla compras con campos completos
            query = f"""
                SELECT TOP {limit}
                    c.idcompra,
                    c.folio AS folio_entrada,
                    c.foliofactura AS folio_factura,
                    c.fechaaplicacion AS fecha_entrada,
                    c.fechavencimiento AS fecha_vencimiento,
                    c.referencia,
                    c.total AS importe_original,
                    p.idproveedor,
                    p.nombre AS proveedor_nombre,
                    p.rfc AS proveedor_rfc,
                    ISNULL((SELECT SUM(pp.abono) FROM pagosproveedores pp WHERE pp.foliocompra = c.idcompra), 0) AS pagos,
                    c.total - ISNULL((SELECT SUM(pp.abono) FROM pagosproveedores pp WHERE pp.foliocompra = c.idcompra), 0) AS saldo,
                    DATEDIFF(day, c.fechavencimiento, GETDATE()) AS dias_vencido
                FROM compras c
                INNER JOIN proveedores p ON c.idproveedor = p.idproveedor
                WHERE (c.cancelado IS NULL OR c.cancelado = 0)
                  AND (c.total - ISNULL((SELECT SUM(pp.abono) FROM pagosproveedores pp WHERE pp.foliocompra = c.idcompra), 0)) > 1
                ORDER BY c.fechaaplicacion DESC
            """
            
            results = self._execute_query(server_key, query)
            
            for r in results:
                proveedor_nombre = r.get('proveedor_nombre', '')
                tipo = get_tipo_proveedor(proveedor_nombre)
                
                # Filtrar por tipo si se especificó
                if tipo_proveedor and tipo != tipo_proveedor:
                    continue
                
                saldo = float(r.get('saldo', 0) or 0)
                if saldo <= 0:
                    continue
                
                dias_vencido = int(r.get('dias_vencido', 0) or 0)
                if dias_vencido < 0:
                    dias_vencido = 0  # No vencido aún
                
                importe_original = float(r.get('importe_original', 0) or 0)
                
                # Calcular rangos de antigüedad
                por_vencer = saldo if dias_vencido <= 0 else 0
                venc_1_30 = saldo if 1 <= dias_vencido <= 30 else 0
                venc_31_60 = saldo if 31 <= dias_vencido <= 60 else 0
                venc_61_90 = saldo if 61 <= dias_vencido <= 90 else 0
                venc_91_plus = saldo if dias_vencido > 90 else 0
                
                # Formatear fecha de vencimiento
                fecha_venc = r.get('fecha_vencimiento')
                fecha_venc_str = fecha_venc.strftime('%Y-%m-%d') if fecha_venc else None
                
                fecha_entrada = r.get('fecha_entrada')
                
                all_results.append({
                    "CuentaPorPagarID": f"{server_key}_{r.get('idcompra')}",
                    "SucursalID": server_key,
                    "SucursalNombre": srv['name'],
                    "ProveedorID": r.get('idproveedor', 'N/A'),
                    "ProveedorNombre": proveedor_nombre,
                    "ProveedorRFC": r.get('proveedor_rfc', ''),
                    "TipoProveedor": tipo,
                    "TipoProveedorNombre": get_nombre_tipo(tipo),
                    "FolioEntrada": r.get('folio_entrada') or None,
                    "FolioFactura": r.get('folio_factura') or None,
                    "FechaEntrada": fecha_entrada,
                    "FechaVencimiento": fecha_venc_str,
                    "Referencia": r.get('referencia') or None,
                    "MontoOriginal": importe_original,
                    "Saldo": saldo,
                    "PorVencer": por_vencer,
                    "Venc1_30": venc_1_30,
                    "Venc31_60": venc_31_60,
                    "Venc61_90": venc_61_90,
                    "Venc91Plus": venc_91_plus,
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
