import os
from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
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
DICIEMBRE 2026: Fix encoding - Usa subprocess con locale UTF-8 forzado
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from decimal import Decimal

# Importar helper de subprocess para queries con encoding correcto
from .sql_subprocess_helper import execute_sql_subprocess
from core.sql_first.db import get_sql_connection

# Configuración de servidores SoftRestaurant (desde menú de servidores)
SOFTRESTAURANT_SERVERS = {
    UnidadesService.resolver_codigo("CIENFUEGOS") or "CIENFUEGOS": {
        "id": "CF",
        "name": "CIEN FUEGOS",
        "host": "servercienfuegos.ddns.net",
        "port": 6669,
        "database": "softrestaurant95pro",
        "username": "CFLectura",
        "password": os.getenv('EDARSAHUB_SQL_PASSWORD'),
        "view": "AC_vwSaldoCxp"
    },
    UnidadesService.resolver_codigo("ESTELAR") or "ESTELAR": {
        "id": "EST",
        "name": "LA ESTELAR",
        "host": "serverestelar.ddns.net",
        "port": 6969,
        "database": "softrestaurant12",
        "username": "SCedarsa",
        "password": "C0ntr4s3ña#2026",
        "view": "AC_vwSaldoCxp"
    },
    UnidadesService.resolver_codigo("130MID") or "130MID": {
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
      2. "TXXX NOMBRE" donde T es A, B o X seguido de dígito → "A1269 COMERCIALIZADORA"
      3. "(XXX) T NOMBRE" 
      4. "T NOMBRE" donde T es A, B seguido de espacio → "A COSTCO (ABARROTES)"
      5. "AXXXX NOMBRE" donde A seguido de dígitos y espacio → "A0070 130 GRADOS"
    
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
    
    # Formato 2: "TXXX NOMBRE" donde T es A, B o X seguido de un dígito (ej: "A1269 COMERCIALIZADORA")
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
    
    # Formato 4: "T NOMBRE" donde T es A o B seguido de espacio (ej: "A COSTCO", "B LA EUROPEA")
    if len(nombre) >= 2:
        primera_letra = nombre[0].upper()
        segunda_char = nombre[1]
        # Si empieza con A o B seguido de espacio → clasificar como A o B
        if primera_letra == 'A' and segunda_char == ' ':
            return 'A'
        elif primera_letra == 'B' and segunda_char == ' ':
            return 'B'
    
    # Formato 5: "AXXXX NOMBRE" donde A seguido de dígitos (ej: "A0070 130 GRADOS")
    if len(nombre) >= 5:
        primera_letra = nombre[0].upper()
        if primera_letra in ('A', 'B'):
            # Verificar si los siguientes caracteres son dígitos hasta el espacio
            espacio_idx = nombre.find(' ')
            if espacio_idx > 1:
                codigo = nombre[1:espacio_idx]
                if codigo.isdigit():
                    return primera_letra
    
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
    
    # Mapeo de aliases a server_keys para matching flexible
    SUCURSAL_ALIASES = {
        # CIENFUEGOS aliases
        UnidadesService.resolver_codigo('CIENFUEGOS') or 'CIENFUEGOS': UnidadesService.resolver_codigo('CIENFUEGOS') or 'CIENFUEGOS',
        'CIEN FUEGOS': UnidadesService.resolver_codigo('CIENFUEGOS') or 'CIENFUEGOS',
        'CF': UnidadesService.resolver_codigo('CIENFUEGOS') or 'CIENFUEGOS',
        'CIENFUEGOS_SR': UnidadesService.resolver_codigo('CIENFUEGOS') or 'CIENFUEGOS',
        # ESTELAR aliases
        UnidadesService.resolver_codigo('ESTELAR') or 'ESTELAR': UnidadesService.resolver_codigo('ESTELAR') or 'ESTELAR',
        'LA ESTELAR': UnidadesService.resolver_codigo('ESTELAR') or 'ESTELAR',
        'EST': UnidadesService.resolver_codigo('ESTELAR') or 'ESTELAR',
        'LAESTELAR': UnidadesService.resolver_codigo('ESTELAR') or 'ESTELAR',
        'LA_ESTELAR': UnidadesService.resolver_codigo('ESTELAR') or 'ESTELAR',
        # 130 MERIDA aliases
        UnidadesService.resolver_codigo('130MID') or '130MID': UnidadesService.resolver_codigo('130MID') or '130MID',
        '130 MERIDA': UnidadesService.resolver_codigo('130MID') or '130MID',
        '130° MERIDA': UnidadesService.resolver_codigo('130MID') or '130MID',
        '130_MERIDA': UnidadesService.resolver_codigo('130MID') or '130MID',
        '130M': UnidadesService.resolver_codigo('130MID') or '130MID',
        'MERIDA': UnidadesService.resolver_codigo('130MID') or '130MID',
    }
    
    def __init__(self, db=None):
        """
        Args:
            db: Instancia de MongoDB (opcional, para compatibilidad)
        """
        self.db = db
        self._connection_cache = {}
    
    def _resolve_sucursal_filter(self, sucursal_id: Optional[str]) -> List[str]:
        """
        Resuelve el filtro de sucursal a una lista de server_keys.
        Soporta matching flexible por nombre, código, alias o key exacto.
        
        Args:
            sucursal_id: Identificador de sucursal (key, código, nombre, alias)
            
        Returns:
            Lista de server_keys a consultar
        """
        if not sucursal_id:
            # Sin filtro = todas las sucursales
            return list(SOFTRESTAURANT_SERVERS.keys())
        
        sucursal_upper = sucursal_id.upper().strip()
        
        # 1. Key exacto
        if sucursal_upper in SOFTRESTAURANT_SERVERS:
            return [sucursal_upper]
        
        # 2. Buscar en aliases
        if sucursal_upper in self.SUCURSAL_ALIASES:
            return [self.SUCURSAL_ALIASES[sucursal_upper]]
        
        # 3. Matching parcial por nombre
        for key, srv in SOFTRESTAURANT_SERVERS.items():
            srv_name = srv.get('name', '').upper()
            srv_id = srv.get('id', '').upper()
            
            # Match si el input está contenido en el nombre o viceversa
            if sucursal_upper in srv_name or srv_name in sucursal_upper:
                return [key]
            if sucursal_upper == srv_id:
                return [key]
        
        # 4. Matching aún más flexible (palabras parciales)
        for key, srv in SOFTRESTAURANT_SERVERS.items():
            srv_name = srv.get('name', '').upper()
            # Buscar si alguna palabra del input coincide
            input_words = sucursal_upper.replace('_', ' ').replace('°', '').split()
            for word in input_words:
                if len(word) >= 3 and word in srv_name:
                    return [key]
        
        # 5. Si parece un UUID, no matchea ninguna sucursal SoftRestaurant
        if len(sucursal_id) > 30 and '-' in sucursal_id:
            logging.warning(f"[SoftRestaurant] sucursal_id parece UUID, no es sucursal SR: {sucursal_id}")
            return []  # Retornar vacío, no es una sucursal SoftRestaurant
        
        # 6. Fallback: no matchea nada específico, retornar todas (comportamiento original)
        logging.warning(f"[SoftRestaurant] sucursal_id no reconocido: {sucursal_id}, consultando todas")
        return list(SOFTRESTAURANT_SERVERS.keys())
    
    async def _execute_query_subprocess(self, server_key: str, query: str) -> List[Dict]:
        """
        Ejecuta una query usando subprocess con locale UTF-8 forzado.
        Esto evita problemas de encoding con pytds en ambiente supervisor.
        """
        if server_key not in SOFTRESTAURANT_SERVERS:
            logging.error(f"[SoftRestaurant] Servidor desconocido: {server_key}")
            return []
        
        srv = SOFTRESTAURANT_SERVERS[server_key]
        
        logging.info(f"[SoftRestaurant] Ejecutando query en {server_key} via subprocess...")
        
        result = await execute_sql_subprocess(
            host=srv['host'],
            port=srv['port'],
            database=srv['database'],
            username=srv['username'],
            password=srv['password'],
            query=query,
            timeout=60
        )
        
        logging.warning(f"[SoftRestaurant] *** FIN SUBPROCESS para {server_key}: success={result.get('success')}, count={result.get('count', 0)} ***")
        
        if result.get('success'):
            logging.info(f"[SoftRestaurant] Query exitosa en {server_key}: {result.get('count', 0)} registros")
            return result.get('data', [])
        else:
            logging.error(f"[SoftRestaurant] Error en query {server_key}: {result.get('error')}")
            return []
    
    def _get_connection(self, server_key: str):
        """
        DEPRECATED: Usar _execute_query_subprocess en su lugar.
        Mantiene compatibilidad con código existente.
        """
        logging.warning(f"[SoftRestaurant] _get_connection está deprecado, usar _execute_query_subprocess")
        return None
    
    def _execute_query(self, server_key: str, query: str) -> List[Dict]:
        """
        DEPRECATED: Usar _execute_query_subprocess en su lugar.
        Este método síncrono se mantiene por compatibilidad pero retorna vacío.
        """
        logging.warning(f"[SoftRestaurant] _execute_query síncrono está deprecado")
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
        
        DICIEMBRE 2026 - REFACTOR CRÍTICO:
        - Cada compra es un documento INDIVIDUAL con su propio saldo
        - El saldo se calcula: total - SUM(pagosproveedores.abono)
        - Ordenado por folio de entrada ASCENDENTE
        - Match por folio de compra (único por documento)
        - SIN agrupaciones - cada fila es un documento único
        
        Args:
            sucursal_id: Clave/nombre/código de sucursal
            tipo_proveedor: A=Alimentos, B=Bebidas, X=Otros
            limit: Máximo de registros
        
        Returns:
            Lista de CxP con documentos individuales y saldo calculado
        """
        all_results = []
        
        target_servers = self._resolve_sucursal_filter(sucursal_id)
        logging.info(f"[SoftRestaurant] get_cuentas_por_pagar: sucursal_id={sucursal_id}, target_servers={target_servers}")
        
        if not target_servers:
            logging.info(f"[SoftRestaurant] No hay target servers, retornando vacío")
            return []
        
        for server_key in target_servers:
            srv = SOFTRESTAURANT_SERVERS.get(server_key)
            if not srv:
                continue
            
            logging.warning(f"[SoftRestaurant] *** INICIO SUBPROCESS para {server_key} ***")
            
            # DICIEMBRE 2026: Query principal - Compras con saldo individual calculado
            # Saldo = total - SUM(pagos), ordenado por folio ASC
            # Cada documento es único (folio es PK)
            
            # ABRIL 2026 FIX: Filtrar por cancelado IS NULL OR cancelado = 0
            # SoftRestaurant marca compras como cancelado=1 cuando están cerradas/históricas
            # Solo mostrar compras activas (no canceladas) con saldo pendiente
            query_compras_con_saldo = f"""
                SELECT TOP {limit}
                    c.idcompra,
                    c.folio AS FolioEntrada,
                    c.foliofactura AS FolioFactura,
                    c.fechaaplicacion AS FechaEntrada,
                    c.fechafactura AS FechaFactura,
                    c.fechavencimiento AS FechaVencimiento,
                    c.referencia AS Referencia,
                    c.idproveedor AS ProveedorID,
                    c.total AS MontoOriginal,
                    c.total - ISNULL(SUM(pp.abono), 0) AS Saldo,
                    p.nombre AS ProveedorNombre,
                    p.rfc AS ProveedorRFC
                FROM compras c
                LEFT JOIN proveedores p ON c.idproveedor = p.idproveedor
                LEFT JOIN pagosproveedores pp ON pp.foliocompra = c.idcompra
                WHERE (c.cancelado IS NULL OR c.cancelado = 0)
                GROUP BY c.idcompra, c.folio, c.foliofactura, c.fechaaplicacion, c.fechafactura, 
                         c.fechavencimiento, c.referencia, c.idproveedor, c.total, p.nombre, p.rfc
                HAVING c.total - ISNULL(SUM(pp.abono), 0) > 0
                ORDER BY c.folio ASC
            """
            
            results_compras = await self._execute_query_subprocess(server_key, query_compras_con_saldo)
            
            if not results_compras:
                logging.warning(f"[SoftRestaurant] Sin compras con saldo para {server_key}")
                continue
            
            logging.info(f"[SoftRestaurant] {server_key}: {len(results_compras)} documentos con saldo > 0")
            
            # DICIEMBRE 2026: Procesar cada documento directamente
            # Cada compra es un documento ÚNICO con su propio saldo
            # Ordenado por folio ASC (ya viene ordenado de la query)
            
            for c in results_compras:
                proveedor_nombre = str(c.get('ProveedorNombre', '') or '').strip()
                proveedor_id = str(c.get('ProveedorID', '') or '').strip()
                
                # Determinar tipo de proveedor desde el nombre
                tipo = get_tipo_proveedor(proveedor_nombre)
                if tipo_proveedor and tipo != tipo_proveedor:
                    continue
                
                # Extraer valores
                folio_entrada = str(c.get('FolioEntrada', '') or '').strip()
                folio_factura = str(c.get('FolioFactura', '') or '').strip()
                fecha_entrada = c.get('FechaEntrada')
                fecha_factura = c.get('FechaFactura')
                fecha_vencimiento = c.get('FechaVencimiento')
                referencia = str(c.get('Referencia', '') or '').strip()
                proveedor_rfc = str(c.get('ProveedorRFC', '') or '').strip()
                monto_original = float(c.get('MontoOriginal', 0) or 0)
                saldo = float(c.get('Saldo', 0) or 0)
                
                # Formatear fechas
                if isinstance(fecha_entrada, str) and 'T' in fecha_entrada:
                    fecha_entrada = fecha_entrada.split('T')[0]
                if isinstance(fecha_factura, str) and 'T' in fecha_factura:
                    fecha_factura = fecha_factura.split('T')[0]
                if isinstance(fecha_vencimiento, str) and 'T' in fecha_vencimiento:
                    fecha_vencimiento = fecha_vencimiento.split('T')[0]
                
                # Calcular días vencido desde fecha de vencimiento
                dias_vencido = 0
                if fecha_vencimiento:
                    try:
                        from datetime import datetime
                        if isinstance(fecha_vencimiento, str):
                            fv = datetime.strptime(fecha_vencimiento, '%Y-%m-%d')
                        else:
                            fv = fecha_vencimiento
                        dias_vencido = max(0, (datetime.now() - fv).days)
                    except:
                        pass
                
                # Clasificar antigüedad basado en días vencido
                por_vencer = saldo if dias_vencido <= 0 else 0
                venc_1_30 = saldo if 1 <= dias_vencido <= 30 else 0
                venc_31_60 = saldo if 31 <= dias_vencido <= 60 else 0
                venc_61_90 = saldo if 61 <= dias_vencido <= 90 else 0
                venc_91_plus = saldo if dias_vencido > 90 else 0
                
                # ID único por documento (folio es único)
                cuenta_id = f"{server_key}_{folio_entrada}"
                
                all_results.append({
                    "CuentaPorPagarID": cuenta_id,
                    "SucursalID": server_key,
                    "SucursalNombre": srv['name'],
                    "ProveedorID": proveedor_id,
                    "ProveedorNombre": proveedor_nombre,
                    "ProveedorRFC": proveedor_rfc,
                    "TipoProveedor": tipo,
                    "TipoProveedorNombre": get_nombre_tipo(tipo),
                    "FolioEntrada": folio_entrada or None,
                    "FolioFactura": folio_factura or None,
                    "FechaEntrada": fecha_entrada,
                    "FechaFactura": fecha_factura,
                    "FechaVencimiento": fecha_vencimiento,
                    "Referencia": referencia or None,
                    "MontoOriginal": monto_original,
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
