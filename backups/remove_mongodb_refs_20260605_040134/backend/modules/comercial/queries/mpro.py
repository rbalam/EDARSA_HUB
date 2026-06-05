"""
EDARSA HUB - Queries Base para MPRO (ManagementPro)
===================================================

PROPÓSITO:
Centralizar las queries SQL homologadas para servidores MPRO.
Estas funciones son la ÚNICA FUENTE DE VERDAD para las métricas base.

TABLAS PRINCIPALES MPRO:
- Venta_Encabezado (VE): Ventas (folio, fecha, totales)
- Comanda (C): Información de comensales (Co_Personas)
- Sucursal (S): Catálogo de sucursales
- Almacen (A): Catálogo de almacenes
- Requisicion_Compra: Requisiciones de compra
- Fisico: Inventarios físicos

FUNCIONES A IMPLEMENTAR (Bloques siguientes):
- query_ventas_periodo_mpro: Ventas totales, PAX, cheques para un período
- query_ventas_sin_corte_mpro: Ventas del día sin cierre
- query_ventas_por_sucursal_mpro: Ventas desglosadas por sucursal

CONVENCIONES:
- Todas las funciones reciben server: Dict con configuración SQL
- Todas retornan SafeQueryResult del core/db.py
- Fechas en formato YYYY-MM-DD, se convierten a YYYYMMDD para SQL
- Usar ISNULL() para manejar NULL consistentemente
- Usar CONVERT(varchar, fecha, 112) para comparar fechas
- Filtrar ISNULL(VE.Es_Cve_Estado, '') <> 'CA' para excluir cancelados

DIFERENCIAS CON SOFTRESTAURANT:
- Campo de ventas: Vn_Precio_Neto_Importe (no 'total')
- Campo de PAX: Co_Personas en tabla Comanda (LEFT JOIN)
- Sucursal: Sc_Cve_Sucursal / Sc_Descripcion
- Sin concepto de "turno" - usa fecha directa

CONSUMIDORES:
- get_kpis_mpro() en service.py
- /comercial/tablero-ejecutivo
- /comercial/dashboard/{server_id}
- SYNC-S scheduler

Fecha creación: 2026-04-23
Estado: BLOQUE_1 - Estructura preparada, sin implementación
FASE 3A.3: Migrado a helpers centralizados de system_type
FASE 5C: Integración con EmpresaResolver para resolución canónica
"""

from typing import Dict, Optional, List
from dataclasses import dataclass
import logging

# Import de la función de ejecución SQL existente
from core.db import execute_sql_query

# FASE 3A.3: Import de helpers centralizados de system_type
from core.system_type_utils import is_mpro_system

# =============================================================================
# FASE 5C: INTEGRACIÓN CON EmpresaResolver (Mayo 2026)
# =============================================================================
# Importar EmpresaResolver para resolución canónica de sucursales MPRO
try:
    from core.empresa_resolver import (
        resolve_empresa_by_alias,
        get_connection_for_role,
        normalize_alias,
        EMPRESA_RESOLVER_AVAILABLE
    )
    _EMPRESA_RESOLVER_OK = True
except ImportError as e:
    logging.warning(f"[MPRO] EmpresaResolver no disponible: {e}. Usando fallback.")
    _EMPRESA_RESOLVER_OK = False
    EMPRESA_RESOLVER_AVAILABLE = False

# =============================================================================
# CONSTANTES
# =============================================================================

# Tablas conocidas de MPRO para validación
MPRO_KNOWN_TABLES = [
    'Venta_Encabezado',
    'Comanda',
    'Sucursal',
    'Almacen',
    'Requisicion_Compra',
    'Fisico',
    'Producto',
    'Proveedor',
]

# Nombre del módulo para logging
MODULE_NAME = "COMERCIAL_QUERIES_MPRO"


# =============================================================================
# RESULTADO HOMOLOGADO (igual que SoftRestaurant para consistencia)
# =============================================================================

@dataclass
class VentasPeriodoResult:
    """
    Resultado homologado de query de ventas por período.
    Estructura idéntica a softrestaurant.py para consistencia.
    """
    success: bool
    total_venta: float = 0.0
    pax: int = 0
    cheques: int = 0
    error: Optional[str] = None
    source: str = "SQL_LIVE"  # SQL_LIVE, CACHE, HUB


# =============================================================================
# FUNCIONES BASE IMPLEMENTADAS
# =============================================================================

def query_ventas_periodo_mpro(
    server: Dict,
    fecha_ini: str,  # YYYY-MM-DD
    fecha_fin: str,   # YYYY-MM-DD
    sucursal_id: Optional[str] = None
) -> VentasPeriodoResult:
    """
    Query base ÚNICA de ventas para MPRO.
    
    ORIGEN: Extraída de service.py líneas 871-884 (get_kpis_mpro_por_sucursal)
    FECHA EXTRACCIÓN: 2026-04-23
    
    MÉTRICAS RETORNADAS:
    - total_venta: SUM(VE.Vn_Precio_Neto_Importe) - Venta total en pesos
    - pax: SUM(C.Co_Personas) - Total de comensales desde tabla Comanda
    - cheques: COUNT(DISTINCT VE.Vn_Folio) - Número de tickets/folios
    
    DIFERENCIAS VS SOFTRESTAURANT:
    - Usa tabla Venta_Encabezado (no cheques)
    - PAX viene de tabla Comanda con LEFT JOIN (no existe campo directo)
    - Filtro de cancelados: ISNULL(Es_Cve_Estado, '') <> 'CA'
    - Sucursal: Sc_Cve_Sucursal (código) o Sc_Descripcion (nombre)
    
    LÓGICA DE PAX:
    - Si PAX real (Comanda.Co_Personas) es 0 pero hay cheques, estima PAX = cheques
    - Esto replica el comportamiento de service.py línea 915-916
    
    CONSUMIDORES PREVISTOS:
    - get_kpis_mpro_por_sucursal() en service.py (migración Bloque 4)
    - /comercial/tablero-ejecutivo para servidores MPRO
    - SYNC-S scheduler
    
    Args:
        server: Dict con configuración SQL (host, port, database, username, password)
        fecha_ini: Fecha inicio en formato YYYY-MM-DD
        fecha_fin: Fecha fin en formato YYYY-MM-DD
        sucursal_id: Código de sucursal (opcional, None = todas consolidadas)
        
    Returns:
        VentasPeriodoResult con métricas o error
    """
    # FASE 3A.3: Migrado a helper centralizado
    system_type = server.get('system_type', '')
    if not is_mpro_system(system_type):
        return VentasPeriodoResult(
            success=False,
            error=f"Server {server.get('name')} no es MPRO (es {system_type})"
        )
    
    # Validar configuración mínima
    required_fields = ['host', 'port', 'database', 'username', 'password']
    missing = [f for f in required_fields if not server.get(f)]
    if missing:
        return VentasPeriodoResult(
            success=False,
            error=f"Configuración incompleta: faltan {missing}"
        )
    
    # Convertir fechas a formato YYYYMMDD para SQL Server
    fi = _format_fecha_mpro(fecha_ini, es_fin=False)
    ff = _format_fecha_mpro(fecha_fin, es_fin=True)
    
    # Construir filtro de sucursal
    filtro_suc = _build_sucursal_filter_mpro(sucursal_id, alias="VE")
    
    # Query SQL - Basada en service.py líneas 871-884
    # NOTA: Esta query consolida TODAS las sucursales si no se especifica filtro
    # A diferencia del original que agrupa por sucursal, aquí consolidamos
    # BLINDAJE: Usar CONVERT para formato de fecha explícito
    query = f"""
SELECT 
    COUNT(DISTINCT VE.Vn_Folio) as cheques,
    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas,
    ISNULL(SUM(C.Co_Personas), 0) as pax
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Vn_Fecha >= CONVERT(datetime, '{fi}', 120) AND VE.Vn_Fecha <= CONVERT(datetime, '{ff}', 120)
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  {filtro_suc}
"""
    
    try:
        result = execute_sql_query(
            server['host'], 
            server['port'], 
            server['database'],
            server['username'], 
            server['password'], 
            query
        )
        
        if result and len(result) > 0:
            ventas = float(result[0].get('ventas') or 0)
            cheques = int(result[0].get('cheques') or 0)
            pax = int(result[0].get('pax') or 0)
            
            # Lógica de estimación PAX (service.py líneas 914-916)
            # Si PAX es 0 pero hay cheques, estimamos PAX = cheques
            if pax == 0 and cheques > 0:
                pax = cheques
                logging.debug(f"[{MODULE_NAME}] PAX estimado como cheques para {server.get('name')}")
            
            return VentasPeriodoResult(
                success=True,
                total_venta=ventas,
                pax=pax,
                cheques=cheques,
                source="SQL_LIVE"
            )
        else:
            # Query exitosa pero sin resultados
            return VentasPeriodoResult(
                success=True,
                total_venta=0.0,
                pax=0,
                cheques=0,
                source="SQL_LIVE"
            )
            
    except Exception as e:
        logging.warning(f"[{MODULE_NAME}] Error en query_ventas_periodo_mpro para {server.get('name')}: {e}")
        return VentasPeriodoResult(
            success=False,
            error=str(e)
        )


# =============================================================================
# FUNCIÓN PARA DASHBOARD MPRO CON FILTRO FLEXIBLE
# =============================================================================

def query_ventas_periodo_mpro_con_filtro_flexible(
    server: Dict,
    fecha_ini: str,           # YYYY-MM-DD
    fecha_fin: str,           # YYYY-MM-DD
    sucursal: Optional[str] = None,
    excluir_cancelados: bool = True
) -> VentasPeriodoResult:
    """
    Query de ventas MPRO con filtro flexible de sucursal.
    
    ORIGEN: Extraída de routes.py endpoint /comercial/dashboard/{server_id}
    FECHA EXTRACCIÓN: 2026-04-23
    
    A diferencia de query_ventas_periodo_mpro():
    - Soporta filtro por código exacto (isdigit o patrón 0XXX)
    - Soporta filtro por nombre parcial (LIKE en Sc_Descripcion)
    - Incluye JOIN condicional con tabla Sucursal cuando filtra por nombre
    - Usa la misma lógica que el endpoint dashboard MPRO
    
    LÓGICA DE FILTRO (copiada de routes.py líneas 3140-3146):
    - Si sucursal es None, 'all', 'default' o igual al nombre del servidor: sin filtro
    - Si sucursal.isdigit() o es código tipo '0XXX': filtro por VE.Sc_Cve_Sucursal
    - Si sucursal es texto: JOIN Sucursal + LIKE en Sc_Descripcion
    
    MÉTRICAS:
    - ventas: SUM(VE.Vn_Precio_Neto_Importe)
    - pax: SUM(C.Co_Personas) desde Comanda
    - cheques: COUNT(DISTINCT VE.Vn_Folio)
    
    CONSUMIDORES PREVISTOS:
    - /comercial/dashboard/{server_id} (sección MPRO)
    - Reemplaza queries SQL directas en routes.py
    
    Args:
        server: Dict con configuración SQL
        fecha_ini: Fecha inicio en formato YYYY-MM-DD
        fecha_fin: Fecha fin en formato YYYY-MM-DD
        sucursal: Código o nombre de sucursal (opcional)
        excluir_cancelados: Si True, excluye Es_Cve_Estado = 'CA' (default: True)
        
    Returns:
        VentasPeriodoResult con métricas o error
    """
    # FASE 3A.3: Migrado a helper centralizado
    system_type = server.get('system_type', '')
    if not is_mpro_system(system_type):
        return VentasPeriodoResult(
            success=False,
            error=f"Server {server.get('name')} no es MPRO (es {system_type})"
        )
    
    # Validar configuración mínima
    required_fields = ['host', 'port', 'database', 'username', 'password']
    missing = [f for f in required_fields if not server.get(f)]
    if missing:
        return VentasPeriodoResult(
            success=False,
            error=f"Configuración incompleta: faltan {missing}"
        )
    
    # Convertir fechas a formato con hora para SQL Server
    fi = _format_fecha_mpro(fecha_ini, es_fin=False)
    ff = _format_fecha_mpro(fecha_fin, es_fin=True)
    
    # ==========================================================================
    # FASE 5C: RESOLUCIÓN CANÓNICA CON EmpresaResolver
    # Reemplaza LIKE '%{sucursal}%' por filtro con CodigoSucursalSistema
    # ==========================================================================
    sucursal_join = ""
    sucursal_filter = ""
    
    nombre_servidor = server.get('name', '').lower()
    sucursal_lower = (sucursal or '').lower()
    
    # Determinar si se debe aplicar filtro
    skip_sucursal_filter = (
        not sucursal or 
        sucursal == 'all' or 
        sucursal_lower == 'default' or 
        sucursal_lower == nombre_servidor
    )
    
    if not skip_sucursal_filter:
        # FASE 5C: Intentar resolver con EmpresaResolver primero
        codigo_sucursal_resuelto = _resolver_codigo_sucursal_mpro(sucursal)
        
        if codigo_sucursal_resuelto:
            # Resuelto por EmpresaResolver - usar código exacto
            sucursal_join = ""
            sucursal_filter = f" AND VE.Sc_Cve_Sucursal = '{codigo_sucursal_resuelto}'"
            logging.info(f"[MPRO] Filtro resuelto por EmpresaResolver: '{sucursal}' -> '{codigo_sucursal_resuelto}'")
        else:
            # Fallback: Detectar tipo de filtro por formato
            es_codigo = sucursal.isdigit() or (len(sucursal) == 4 and sucursal[0] == '0')
            
            if es_codigo:
                # Filtro por código exacto (sin JOIN adicional)
                sucursal_join = ""
                sucursal_filter = f" AND VE.Sc_Cve_Sucursal = '{sucursal}'"
            else:
                # FALLBACK LEGACY: Filtro por nombre (requiere JOIN con tabla Sucursal)
                # NOTA: Este path solo se usa si EmpresaResolver no tiene el alias
                sucursal_join = "INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal"
                sucursal_filter = f" AND S.Sc_Descripcion LIKE '%{sucursal}%'"
                logging.warning(f"[MPRO] Filtro LIKE legacy para '{sucursal}' - considerar agregar alias a EmpresaResolver")
    
    # ==========================================================================
    # FILTRO DE CANCELADOS
    # ==========================================================================
    filtro_cancelados = ""
    if excluir_cancelados:
        filtro_cancelados = "AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'"
    
    # ==========================================================================
    # QUERY SQL - Basada en routes.py dashboard MPRO
    # BLINDAJE: Usar CONVERT para formato de fecha explícito
    # ==========================================================================
    query = f"""
SELECT 
    COUNT(DISTINCT VE.Vn_Folio) as cheques,
    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas,
    ISNULL(SUM(C.Co_Personas), 0) as pax
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
{sucursal_join}
WHERE VE.Vn_Fecha >= CONVERT(datetime, '{fi}', 120) AND VE.Vn_Fecha <= CONVERT(datetime, '{ff}', 120)
  {filtro_cancelados}
  {sucursal_filter}
"""
    
    try:
        print(f"*** [MPRO Query] Ejecutando query para {server.get('name')} sucursal={sucursal} ***")
        result = execute_sql_query(
            server['host'], 
            server['port'], 
            server['database'],
            server['username'], 
            server['password'], 
            query
        )
        
        print(f"*** [MPRO Query] Resultado: {result[:1] if result else 'None/Empty'} ***")
        
        if result and len(result) > 0:
            ventas = float(result[0].get('ventas') or 0)
            cheques = int(result[0].get('cheques') or 0)
            pax = int(result[0].get('pax') or 0)
            
            print(f"*** [MPRO Query] Ventas={ventas:,.2f}, PAX={pax}, Cheques={cheques} ***")
            
            # Lógica de estimación PAX (igual que query_ventas_periodo_mpro)
            if pax == 0 and cheques > 0:
                pax = cheques
                logging.debug(f"[{MODULE_NAME}] PAX estimado como cheques para {server.get('name')} (filtro flexible)")
            
            logging.info(f"[{MODULE_NAME}] query_ventas_periodo_mpro_con_filtro_flexible: "
                        f"Ventas={ventas:,.2f}, PAX={pax}, Cheques={cheques} "
                        f"para {server.get('name')} sucursal={sucursal}")
            
            return VentasPeriodoResult(
                success=True,
                total_venta=ventas,
                pax=pax,
                cheques=cheques,
                source="SQL_LIVE"
            )
        else:
            # Query exitosa pero sin resultados
            logging.info(f"[{MODULE_NAME}] query_ventas_periodo_mpro_con_filtro_flexible: "
                        f"Sin datos para {server.get('name')} sucursal={sucursal}")
            return VentasPeriodoResult(
                success=True,
                total_venta=0.0,
                pax=0,
                cheques=0,
                source="SQL_LIVE"
            )
            
    except Exception as e:
        logging.warning(f"[{MODULE_NAME}] Error en query_ventas_periodo_mpro_con_filtro_flexible "
                       f"para {server.get('name')}: {e}")
        return VentasPeriodoResult(
            success=False,
            error=str(e)
        )


# =============================================================================
# UTILIDADES INTERNAS (si se requieren en bloques futuros)
# =============================================================================

def _format_fecha_mpro(fecha_iso: str, es_fin: bool = False) -> str:
    """
    Convierte fecha ISO (YYYY-MM-DD) a formato SQL con hora para MPRO.
    
    Args:
        fecha_iso: Fecha en formato YYYY-MM-DD
        es_fin: Si True, usa 23:59:59. Si False, usa 00:00:00
        
    Returns:
        Fecha en formato 'YYYY-MM-DD HH:MM:SS' para comparación SQL
    """
    fecha_base = fecha_iso.replace('-', '')[:8]  # YYYYMMDD
    # Convertir a formato ISO para CONVERT
    fecha_iso_clean = f"{fecha_base[:4]}-{fecha_base[4:6]}-{fecha_base[6:8]}"
    hora = "23:59:59" if es_fin else "00:00:00"
    return f"{fecha_iso_clean} {hora}"


def _build_sucursal_filter_mpro(sucursal_id: Optional[str], alias: str = "VE") -> str:
    """
    Construye filtro SQL para sucursal en MPRO.
    
    Args:
        sucursal_id: Código de sucursal o None para todas
        alias: Alias de la tabla (default: VE para Venta_Encabezado)
        
    Returns:
        String SQL del filtro (vacío si no aplica)
    """
    if sucursal_id and sucursal_id.lower() not in ('all', 'todos', ''):
        return f"AND {alias}.Sc_Cve_Sucursal = '{sucursal_id}'"
    return ""


def _resolver_codigo_sucursal_mpro(sucursal: str) -> Optional[str]:
    """
    FASE 5C HELPER: Resuelve un alias/nombre de sucursal a CodigoSucursalSistema MPRO.
    
    Usa EmpresaResolver para resolver:
    - Alias de empresa (ORIGEN, QRO, 130-QRO, etc.)
    - Nombre de sucursal
    
    Y devuelve el CodigoSucursalSistema correspondiente (ej: "0023", "0021").
    
    MAPEO CRÍTICO:
    - ORIGEN → EmpresaID=1 → CodigoSucursalSistema=0023
    - 130QRO → EmpresaID=2 → CodigoSucursalSistema=0021
    
    Args:
        sucursal: Alias o nombre de sucursal
        
    Returns:
        CodigoSucursalSistema o None si no se puede resolver
    """
    if not sucursal:
        return None
    
    # Si ya es un código de sucursal (4 dígitos empezando con 0), retornar tal cual
    if len(sucursal) == 4 and sucursal[0] == '0' and sucursal.isdigit():
        return sucursal
    
    if sucursal.isdigit():
        return sucursal
    
    # =========================================================================
    # FASE 5C: Resolver con EmpresaResolver
    # =========================================================================
    if _EMPRESA_RESOLVER_OK and EMPRESA_RESOLVER_AVAILABLE:
        try:
            # Paso 1: Resolver alias a empresa
            empresa = resolve_empresa_by_alias(sucursal)
            
            if empresa:
                logging.debug(f"[MPRO] _resolver_codigo_sucursal_mpro: '{sucursal}' -> EmpresaID={empresa.empresa_id}")
                
                # Paso 2: Obtener conexión PRINCIPAL_SQL para esta empresa
                connection = get_connection_for_role(empresa.empresa_id, 'PRINCIPAL_SQL')
                
                if connection and connection.codigo_sucursal_sistema:
                    logging.info(f"[MPRO] _resolver_codigo_sucursal_mpro: EmpresaID={empresa.empresa_id} -> CodigoSucursal={connection.codigo_sucursal_sistema}")
                    return connection.codigo_sucursal_sistema
                
                # Si no tiene PRINCIPAL_SQL, intentar con VENTAS_DIA_API_LOCAL
                connection_api = get_connection_for_role(empresa.empresa_id, 'VENTAS_DIA_API_LOCAL')
                if connection_api and connection_api.codigo_sucursal_sistema:
                    logging.info(f"[MPRO] _resolver_codigo_sucursal_mpro: EmpresaID={empresa.empresa_id} -> CodigoSucursal={connection_api.codigo_sucursal_sistema} (via API_LOCAL)")
                    return connection_api.codigo_sucursal_sistema
                
        except Exception as e:
            logging.warning(f"[MPRO] Error en _resolver_codigo_sucursal_mpro para '{sucursal}': {e}")
    
    # =========================================================================
    # Fallback: Mapeo hardcodeado para resiliencia
    # =========================================================================
    fallback_map = {
        'ORIGEN': '0023',
        'origen': '0023',
        'QRO': '0021',
        'qro': '0021',
        '130QRO': '0021',
        '130-QRO': '0021',
        '130 QRO': '0021',
        'QUERETARO': '0021',
        '130° QUERETARO': '0021',
    }
    
    codigo = fallback_map.get(sucursal.upper().strip())
    if codigo:
        logging.warning(f"[MPRO] _resolver_codigo_sucursal_mpro: Usando fallback hardcodeado para '{sucursal}' -> '{codigo}'")
        return codigo
    
    return None


def _build_sucursal_filter_mpro_flexible(
    sucursal: Optional[str], 
    alias_venta: str = "VE",
    alias_sucursal: str = "S"
) -> str:
    """
    Construye filtro SQL flexible para sucursal en MPRO.
    
    FASE 5C: Usa _resolver_codigo_sucursal_mpro() para resolución canónica.
    El LIKE solo se usa como fallback si EmpresaResolver no tiene el alias.
    
    Args:
        sucursal: Código o nombre parcial de sucursal
        alias_venta: Alias de tabla Venta_Encabezado
        alias_sucursal: Alias de tabla Sucursal
        
    Returns:
        String SQL del filtro
    """
    if not sucursal or sucursal.lower() in ('all', 'todos', ''):
        return "1=1"
    
    # FASE 5C: Intentar resolver con EmpresaResolver primero
    codigo_resuelto = _resolver_codigo_sucursal_mpro(sucursal)
    
    if codigo_resuelto:
        # Resuelto por EmpresaResolver - usar código exacto
        return f"{alias_venta}.Sc_Cve_Sucursal = '{codigo_resuelto}'"
    
    # Fallback legacy: Buscar por código exacto O descripción parcial
    return (
        f"({alias_sucursal}.Sc_Cve_Sucursal = '{sucursal}' "
        f"OR {alias_sucursal}.Sc_Descripcion LIKE '%{sucursal}%')"
    )


# =============================================================================
# BLOQUE 4: QUERY POR SUCURSAL (AGRUPADA)
# =============================================================================

@dataclass
class VentasPorSucursalResult:
    """
    Resultado de query de ventas agrupadas por sucursal.
    Retorna lista de sucursales con sus métricas.
    """
    success: bool
    sucursales: List[Dict] = None  # Lista de {sucursal_id, sucursal_nombre, ventas, pax, cheques}
    error: Optional[str] = None
    source: str = "SQL_LIVE"
    
    def __post_init__(self):
        if self.sucursales is None:
            self.sucursales = []


def query_ventas_por_sucursal_mpro(
    server: Dict,
    fecha_ini: str,  # YYYY-MM-DD
    fecha_fin: str   # YYYY-MM-DD
) -> VentasPorSucursalResult:
    """
    Query base de ventas AGRUPADAS POR SUCURSAL para MPRO.
    
    ORIGEN: Extraída de service.py líneas 862-884 (get_kpis_mpro_por_sucursal)
    FECHA EXTRACCIÓN: 2026-04-23
    
    DIFERENCIA CON query_ventas_periodo_mpro():
    - Esta función AGRUPA por sucursal (GROUP BY)
    - Incluye JOIN a tabla Sucursal para nombres
    - Ordena por ventas DESC
    - Retorna lista de sucursales, no consolidado
    
    MÉTRICAS POR SUCURSAL:
    - sucursal_id: Código de sucursal (Sc_Cve_Sucursal)
    - sucursal_nombre: Nombre de sucursal (Sc_Descripcion)
    - ventas: SUM(VE.Vn_Precio_Neto_Importe)
    - pax: SUM(C.Co_Personas) desde Comanda
    - cheques: COUNT(DISTINCT VE.Vn_Folio)
    
    LÓGICA DE PAX:
    - LEFT JOIN a Comanda para obtener Co_Personas
    - Si PAX es 0 pero hay cheques, el consumidor debe estimar PAX = cheques
    
    CONSUMIDORES PREVISTOS:
    - get_kpis_mpro_por_sucursal() en service.py (migración Bloque 4)
    - Reemplaza query SQL directa líneas 862-884
    
    Args:
        server: Dict con configuración SQL
        fecha_ini: Fecha inicio en formato YYYY-MM-DD
        fecha_fin: Fecha fin en formato YYYY-MM-DD
        
    Returns:
        VentasPorSucursalResult con lista de sucursales o error
    """
    # FASE 3A.3: Migrado a helper centralizado
    system_type = server.get('system_type', '')
    if not is_mpro_system(system_type):
        return VentasPorSucursalResult(
            success=False,
            error=f"Server {server.get('name')} no es MPRO (es {system_type})"
        )
    
    # Validar configuración mínima
    required_fields = ['host', 'port', 'database', 'username', 'password']
    missing = [f for f in required_fields if not server.get(f)]
    if missing:
        return VentasPorSucursalResult(
            success=False,
            error=f"Configuración incompleta: faltan {missing}"
        )
    
    # Convertir fechas a formato YYYYMMDD
    fi = _format_fecha_mpro(fecha_ini, es_fin=False)
    ff = _format_fecha_mpro(fecha_fin, es_fin=True)
    
    # Query SQL - EXACTAMENTE igual a service.py líneas 862-875
    # NOTA: No incluye filtro Es_Cve_Estado <> 'CA' porque la original no lo tiene
    # en la query principal (solo en query_ultimo_dia)
    # BLINDAJE: Usar CONVERT para formato de fecha explícito
    query = f"""
SELECT 
    S.Sc_Cve_Sucursal as sucursal_id,
    S.Sc_Descripcion as sucursal_nombre,
    COUNT(DISTINCT VE.Vn_Folio) as cheques,
    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas,
    ISNULL(SUM(C.Co_Personas), 0) as pax
FROM Venta_Encabezado VE
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Vn_Fecha >= CONVERT(datetime, '{fi}', 120) AND VE.Vn_Fecha <= CONVERT(datetime, '{ff}', 120)
GROUP BY S.Sc_Cve_Sucursal, S.Sc_Descripcion
ORDER BY SUM(VE.Vn_Precio_Neto_Importe) DESC
"""
    
    try:
        result = execute_sql_query(
            server['host'], 
            server['port'], 
            server['database'],
            server['username'], 
            server['password'], 
            query
        )
        
        if result and len(result) > 0:
            sucursales = []
            for row in result:
                sucursales.append({
                    "sucursal_id": row.get('sucursal_id', ''),
                    "sucursal_nombre": row.get('sucursal_nombre', 'Sin nombre'),
                    "ventas": float(row.get('ventas') or 0),
                    "pax": int(row.get('pax') or 0),
                    "cheques": int(row.get('cheques') or 0)
                })
            
            logging.info(f"[{MODULE_NAME}] query_ventas_por_sucursal_mpro: {len(sucursales)} sucursales para {server.get('name')}")
            return VentasPorSucursalResult(
                success=True,
                sucursales=sucursales,
                source="SQL_LIVE"
            )
        else:
            # Query exitosa pero sin resultados
            logging.info(f"[{MODULE_NAME}] query_ventas_por_sucursal_mpro: Sin sucursales con ventas para {server.get('name')}")
            return VentasPorSucursalResult(
                success=True,
                sucursales=[],
                source="SQL_LIVE"
            )
            
    except Exception as e:
        logging.warning(f"[{MODULE_NAME}] Error en query_ventas_por_sucursal_mpro para {server.get('name')}: {e}")
        return VentasPorSucursalResult(
            success=False,
            error=str(e)
        )
