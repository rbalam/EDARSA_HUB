"""
EMPRESA RESOLVER - Read-Only Component
=======================================

Componente centralizado para resolver empresas, aliases, servidores, 
tipos de sistema, roles de conexión y sucursales desde EDARSAHUB SQL.

FUENTE AUTORITATIVA: EDARSAHUB SQL Server
NO CONSULTA: MongoDB

Tablas consultadas:
- Sistema_Empresas
- Sistema_EmpresasAlias
- Sistema_EmpresasServidores
- Sistema_Tipos
- Servidores_Conexiones

FASE 4 - Implementación Read-Only
Fecha: 2026-05-16
"""

import unicodedata
import re
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from core.db import execute_sql_query

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURACIÓN EDARSAHUB
# =============================================================================

EDARSAHUB_CONFIG = {
    'host': '54.39.104.176',
    'port': 1433,
    'database': 'EDARSAHUB',
    'username': 'HRLectura',
    'password': 'National09$'
}


def _execute_query(query: str, params: dict = None) -> List[Dict]:
    """Ejecuta una query en EDARSAHUB y retorna resultados"""
    try:
        result = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query
        )
        return result or []
    except Exception as e:
        logger.error(f"Error ejecutando query EDARSAHUB EmpresaResolver: {e}")
        raise


# =============================================================================
# DATACLASSES PARA RESPUESTAS ESTRUCTURADAS
# =============================================================================

@dataclass
class EmpresaInfo:
    """Información básica de una empresa"""
    empresa_id: int
    codigo_empresa: str
    nombre_comercial: str
    nombre_empresa: str
    activo: bool


@dataclass
class ConnectionInfo:
    """Información de una conexión empresa-servidor"""
    empresa_servidor_id: int
    empresa_id: int
    servidor_id: str
    nombre_servidor: str
    sistema_tipo: Optional[str]
    rol_conexion: str
    numero_sucursal_sistema: Optional[int]
    codigo_sucursal_sistema: Optional[str]
    nombre_sucursal_sistema: Optional[str]
    prioridad: int
    es_principal: bool
    activo: bool


@dataclass
class SystemBranchContext:
    """Contexto completo de empresa-servidor-sucursal"""
    empresa_id: int
    codigo_empresa: str
    nombre_comercial: str
    servidor_id: str
    nombre_servidor: str
    sistema_tipo: Optional[str]
    rol_conexion: str
    numero_sucursal_sistema: Optional[int]
    codigo_sucursal_sistema: Optional[str]
    nombre_sucursal_sistema: Optional[str]


@dataclass
class HealthCheckResult:
    """Resultado del health check del resolver"""
    status: str  # OK, WARNING, ERROR
    empresas_count: int
    aliases_count: int
    servidores_count: int
    relaciones_count: int
    origen_ok: bool
    qro_ok: bool
    mid_ok: bool
    cienfuegos_ok: bool
    estelar_ok: bool
    errors: List[str]


# =============================================================================
# FUNCIÓN 1: NORMALIZAR ALIAS
# =============================================================================

def normalize_alias(texto: str) -> str:
    """
    Normaliza un alias para búsqueda en Sistema_EmpresasAlias.
    
    Transformaciones:
    1. Convertir a MAYÚSCULAS
    2. Quitar acentos (Á→A, É→E, Í→I, Ó→O, Ú→U, Ñ→N)
    3. Quitar símbolo °
    4. Reemplazar guión medio (-) y guión bajo (_) por espacio
    5. Quitar puntos y comas
    6. Normalizar espacios múltiples a uno solo
    7. TRIM
    
    Args:
        texto: Alias a normalizar
        
    Returns:
        Alias normalizado en mayúsculas sin caracteres especiales
    """
    if not texto:
        return ""
    
    # 1. Convertir a mayúsculas
    resultado = texto.upper()
    
    # 2. Quitar acentos usando NFD y filtrando marcas diacríticas
    resultado = unicodedata.normalize('NFD', resultado)
    resultado = ''.join(c for c in resultado if unicodedata.category(c) != 'Mn')
    
    # 3. Quitar símbolo °
    resultado = resultado.replace('°', '')
    
    # 4. Reemplazar guión medio y bajo por espacio
    resultado = resultado.replace('-', ' ')
    resultado = resultado.replace('_', ' ')
    
    # 5. Quitar puntos y comas
    resultado = resultado.replace('.', '')
    resultado = resultado.replace(',', '')
    
    # 6. Normalizar espacios múltiples
    resultado = re.sub(r'\s+', ' ', resultado)
    
    # 7. TRIM
    resultado = resultado.strip()
    
    # Caso especial: quitar espacios para comparación con AliasNormalizado almacenado
    # Los AliasNormalizado en BD no tienen espacios (ej: 130QRO, 130QUERETARO, LAESTELAR)
    resultado_sin_espacios = resultado.replace(' ', '')
    
    return resultado_sin_espacios


# =============================================================================
# FUNCIÓN 2: RESOLVER EMPRESA POR ALIAS
# =============================================================================

def resolve_empresa_by_alias(alias: str) -> Optional[EmpresaInfo]:
    """
    Busca un alias en Sistema_EmpresasAlias y retorna la empresa asociada.
    
    Estrategia de búsqueda:
    1. Normalizar el alias de entrada
    2. Buscar en Sistema_EmpresasAlias.AliasNormalizado
    3. Si no encuentra, buscar CodigoEmpresa exacto en Sistema_Empresas
    
    Args:
        alias: Alias a buscar (puede ser cualquier variante)
        
    Returns:
        EmpresaInfo si encuentra, None si no existe
    """
    if not alias:
        return None
    
    alias_normalizado = normalize_alias(alias)
    
    # Estrategia 1: Buscar en Sistema_EmpresasAlias
    query = """
    SELECT 
        e.EmpresaID,
        e.CodigoEmpresa,
        e.NombreComercial,
        e.NombreEmpresa,
        e.Activo
    FROM Sistema_EmpresasAlias ea
    JOIN Sistema_Empresas e ON ea.EmpresaID = e.EmpresaID
    WHERE ea.AliasNormalizado = %s
      AND ea.Activo = 1
      AND e.Activo = 1
    """
    
    try:
        rows = _execute_query(query % f"'{alias_normalizado}'")
        if rows:
            row = rows[0]
            return EmpresaInfo(
                empresa_id=row['EmpresaID'],
                codigo_empresa=row['CodigoEmpresa'].strip() if row['CodigoEmpresa'] else '',
                nombre_comercial=row['NombreComercial'].strip() if row['NombreComercial'] else '',
                nombre_empresa=row['NombreEmpresa'].strip() if row['NombreEmpresa'] else '',
                activo=bool(row['Activo'])
            )
    except Exception as e:
        logger.warning(f"Error buscando alias '{alias}' normalizado como '{alias_normalizado}': {e}")
    
    # Estrategia 2: Buscar CodigoEmpresa exacto en Sistema_Empresas
    query_empresa = """
    SELECT 
        EmpresaID,
        CodigoEmpresa,
        NombreComercial,
        NombreEmpresa,
        Activo
    FROM Sistema_Empresas
    WHERE UPPER(LTRIM(RTRIM(CodigoEmpresa))) = %s
      AND Activo = 1
    """
    
    try:
        rows = _execute_query(query_empresa % f"'{alias_normalizado}'")
        if rows:
            row = rows[0]
            return EmpresaInfo(
                empresa_id=row['EmpresaID'],
                codigo_empresa=row['CodigoEmpresa'].strip() if row['CodigoEmpresa'] else '',
                nombre_comercial=row['NombreComercial'].strip() if row['NombreComercial'] else '',
                nombre_empresa=row['NombreEmpresa'].strip() if row['NombreEmpresa'] else '',
                activo=bool(row['Activo'])
            )
    except Exception as e:
        logger.warning(f"Error buscando código empresa '{alias_normalizado}': {e}")
    
    return None


# =============================================================================
# FUNCIÓN 3: RESOLVER EMPRESA POR ID
# =============================================================================

def resolve_empresa_by_id(empresa_id: int) -> Optional[EmpresaInfo]:
    """
    Obtiene datos canónicos de una empresa por su EmpresaID.
    
    Args:
        empresa_id: ID de la empresa
        
    Returns:
        EmpresaInfo si existe, None si no
    """
    if not empresa_id:
        return None
    
    query = """
    SELECT 
        EmpresaID,
        CodigoEmpresa,
        NombreComercial,
        NombreEmpresa,
        Activo
    FROM Sistema_Empresas
    WHERE EmpresaID = %d
    """
    
    try:
        rows = _execute_query(query % empresa_id)
        if rows:
            row = rows[0]
            return EmpresaInfo(
                empresa_id=row['EmpresaID'],
                codigo_empresa=row['CodigoEmpresa'].strip() if row['CodigoEmpresa'] else '',
                nombre_comercial=row['NombreComercial'].strip() if row['NombreComercial'] else '',
                nombre_empresa=row['NombreEmpresa'].strip() if row['NombreEmpresa'] else '',
                activo=bool(row['Activo'])
            )
    except Exception as e:
        logger.error(f"Error obteniendo empresa ID={empresa_id}: {e}")
    
    return None


# =============================================================================
# FUNCIÓN 4: OBTENER CONEXIONES DE EMPRESA
# =============================================================================

def get_empresa_connections(empresa_id: int) -> List[ConnectionInfo]:
    """
    Obtiene todas las relaciones activas de una empresa con servidores.
    
    Args:
        empresa_id: ID de la empresa
        
    Returns:
        Lista de ConnectionInfo con todas las conexiones activas
    """
    if not empresa_id:
        return []
    
    query = """
    SELECT 
        es.EmpresaServidorID,
        es.EmpresaID,
        CONVERT(VARCHAR(36), es.ServidorID) as ServidorID,
        sc.nombre as NombreServidor,
        st.CodigoSistema as SistemaTipo,
        es.RolConexion,
        es.NumeroSucursalSistema,
        es.CodigoSucursalSistema,
        es.NombreSucursalSistema,
        es.Prioridad,
        es.EsPrincipal,
        es.Activo
    FROM Sistema_EmpresasServidores es
    JOIN Servidores_Conexiones sc ON es.ServidorID = sc.id
    LEFT JOIN Sistema_Tipos st ON es.SistemaTipoID = st.SistemaTipoID
    WHERE es.EmpresaID = %d
      AND es.Activo = 1
    ORDER BY es.Prioridad, es.EsPrincipal DESC
    """
    
    connections = []
    try:
        rows = _execute_query(query % empresa_id)
        for row in rows:
            connections.append(ConnectionInfo(
                empresa_servidor_id=row['EmpresaServidorID'],
                empresa_id=row['EmpresaID'],
                servidor_id=row['ServidorID'],
                nombre_servidor=row['NombreServidor'].strip() if row['NombreServidor'] else '',
                sistema_tipo=row['SistemaTipo'].strip() if row['SistemaTipo'] else None,
                rol_conexion=row['RolConexion'].strip() if row['RolConexion'] else '',
                numero_sucursal_sistema=row['NumeroSucursalSistema'],
                codigo_sucursal_sistema=row['CodigoSucursalSistema'].strip() if row['CodigoSucursalSistema'] else None,
                nombre_sucursal_sistema=row['NombreSucursalSistema'].strip() if row['NombreSucursalSistema'] else None,
                prioridad=row['Prioridad'] or 1,
                es_principal=bool(row['EsPrincipal']),
                activo=bool(row['Activo'])
            ))
    except Exception as e:
        logger.error(f"Error obteniendo conexiones para empresa ID={empresa_id}: {e}")
    
    return connections


# =============================================================================
# FUNCIÓN 5: OBTENER CONEXIÓN POR ROL
# =============================================================================

def get_connection_for_role(empresa_id: int, rol_conexion: str) -> Optional[ConnectionInfo]:
    """
    Obtiene la conexión activa de una empresa para un rol específico.
    
    Si hay múltiples conexiones para el mismo rol:
    - Prioriza por EsPrincipal=1
    - Luego por Prioridad ASC (menor número = mayor prioridad)
    
    Args:
        empresa_id: ID de la empresa
        rol_conexion: Rol de conexión (PRINCIPAL_SQL, VENTAS_DIA_API_LOCAL, etc.)
        
    Returns:
        ConnectionInfo si existe exactamente una, None si no existe
        
    Raises:
        ValueError: Si hay ambigüedad (múltiples conexiones con misma prioridad)
    """
    if not empresa_id or not rol_conexion:
        return None
    
    query = """
    SELECT 
        es.EmpresaServidorID,
        es.EmpresaID,
        CONVERT(VARCHAR(36), es.ServidorID) as ServidorID,
        sc.nombre as NombreServidor,
        st.CodigoSistema as SistemaTipo,
        es.RolConexion,
        es.NumeroSucursalSistema,
        es.CodigoSucursalSistema,
        es.NombreSucursalSistema,
        es.Prioridad,
        es.EsPrincipal,
        es.Activo
    FROM Sistema_EmpresasServidores es
    JOIN Servidores_Conexiones sc ON es.ServidorID = sc.id
    LEFT JOIN Sistema_Tipos st ON es.SistemaTipoID = st.SistemaTipoID
    WHERE es.EmpresaID = %d
      AND es.RolConexion = '%s'
      AND es.Activo = 1
    ORDER BY es.EsPrincipal DESC, es.Prioridad ASC
    """
    
    try:
        rows = _execute_query(query % (empresa_id, rol_conexion))
        
        if not rows:
            return None
        
        if len(rows) > 1:
            # Verificar si hay ambigüedad real
            first = rows[0]
            second = rows[1]
            if first['EsPrincipal'] == second['EsPrincipal'] and first['Prioridad'] == second['Prioridad']:
                raise ValueError(
                    f"Ambigüedad: Múltiples conexiones para EmpresaID={empresa_id}, "
                    f"RolConexion={rol_conexion} con misma prioridad"
                )
        
        row = rows[0]
        return ConnectionInfo(
            empresa_servidor_id=row['EmpresaServidorID'],
            empresa_id=row['EmpresaID'],
            servidor_id=row['ServidorID'],
            nombre_servidor=row['NombreServidor'].strip() if row['NombreServidor'] else '',
            sistema_tipo=row['SistemaTipo'].strip() if row['SistemaTipo'] else None,
            rol_conexion=row['RolConexion'].strip() if row['RolConexion'] else '',
            numero_sucursal_sistema=row['NumeroSucursalSistema'],
            codigo_sucursal_sistema=row['CodigoSucursalSistema'].strip() if row['CodigoSucursalSistema'] else None,
            nombre_sucursal_sistema=row['NombreSucursalSistema'].strip() if row['NombreSucursalSistema'] else None,
            prioridad=row['Prioridad'] or 1,
            es_principal=bool(row['EsPrincipal']),
            activo=bool(row['Activo'])
        )
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo conexión para empresa ID={empresa_id}, rol={rol_conexion}: {e}")
    
    return None


# =============================================================================
# FUNCIÓN 6: OBTENER CONTEXTO COMPLETO EMPRESA-SERVIDOR-SUCURSAL
# =============================================================================

def get_system_branch_context(empresa_id: int, rol_conexion: str) -> Optional[SystemBranchContext]:
    """
    Obtiene el contexto completo para una empresa y rol de conexión.
    
    Incluye:
    - Datos de la empresa
    - Datos del servidor
    - Tipo de sistema
    - Rol de conexión
    - Datos de sucursal del sistema origen
    
    Args:
        empresa_id: ID de la empresa
        rol_conexion: Rol de conexión
        
    Returns:
        SystemBranchContext con toda la información, None si no existe
    """
    empresa = resolve_empresa_by_id(empresa_id)
    if not empresa:
        return None
    
    connection = get_connection_for_role(empresa_id, rol_conexion)
    if not connection:
        return None
    
    return SystemBranchContext(
        empresa_id=empresa.empresa_id,
        codigo_empresa=empresa.codigo_empresa,
        nombre_comercial=empresa.nombre_comercial,
        servidor_id=connection.servidor_id,
        nombre_servidor=connection.nombre_servidor,
        sistema_tipo=connection.sistema_tipo,
        rol_conexion=connection.rol_conexion,
        numero_sucursal_sistema=connection.numero_sucursal_sistema,
        codigo_sucursal_sistema=connection.codigo_sucursal_sistema,
        nombre_sucursal_sistema=connection.nombre_sucursal_sistema
    )


# =============================================================================
# FUNCIÓN 7: VALIDAR ALIAS NO AMBIGUO
# =============================================================================

def validate_no_ambiguous_alias(alias: str) -> Dict[str, Any]:
    """
    Valida que un alias normalizado no apunte a más de una empresa activa.
    
    Args:
        alias: Alias a validar
        
    Returns:
        Dict con:
        - valid: bool indicando si es válido
        - alias_normalizado: string normalizado
        - empresas_count: número de empresas encontradas
        - empresas: lista de EmpresaID si hay múltiples
        - error: mensaje de error si hay ambigüedad
    """
    alias_normalizado = normalize_alias(alias)
    
    query = """
    SELECT DISTINCT e.EmpresaID, e.CodigoEmpresa
    FROM Sistema_EmpresasAlias ea
    JOIN Sistema_Empresas e ON ea.EmpresaID = e.EmpresaID
    WHERE ea.AliasNormalizado = '%s'
      AND ea.Activo = 1
      AND e.Activo = 1
    """
    
    try:
        rows = _execute_query(query % alias_normalizado)
        
        if len(rows) == 0:
            return {
                'valid': True,
                'alias_normalizado': alias_normalizado,
                'empresas_count': 0,
                'empresas': [],
                'error': None,
                'warning': 'Alias no encontrado en Sistema_EmpresasAlias'
            }
        
        if len(rows) == 1:
            return {
                'valid': True,
                'alias_normalizado': alias_normalizado,
                'empresas_count': 1,
                'empresas': [{'EmpresaID': rows[0]['EmpresaID'], 'CodigoEmpresa': rows[0]['CodigoEmpresa']}],
                'error': None
            }
        
        # Múltiples empresas = ambigüedad
        return {
            'valid': False,
            'alias_normalizado': alias_normalizado,
            'empresas_count': len(rows),
            'empresas': [{'EmpresaID': r['EmpresaID'], 'CodigoEmpresa': r['CodigoEmpresa']} for r in rows],
            'error': f"Alias ambiguo: '{alias}' apunta a {len(rows)} empresas diferentes"
        }
    except Exception as e:
        return {
            'valid': False,
            'alias_normalizado': alias_normalizado,
            'empresas_count': 0,
            'empresas': [],
            'error': f"Error validando alias: {e}"
        }


# =============================================================================
# FUNCIÓN 8: HEALTH CHECK DEL RESOLVER
# =============================================================================

def health_check_empresa_resolver() -> HealthCheckResult:
    """
    Valida el estado del EmpresaResolver y las tablas canónicas.
    
    Validaciones:
    - Conteos mínimos de tablas
    - Las 5 empresas canónicas existen y resuelven correctamente
    - Conexiones principales configuradas
    
    Returns:
        HealthCheckResult con el estado completo
    """
    errors = []
    
    # Conteos
    try:
        empresas_rows = _execute_query("SELECT COUNT(*) as c FROM Sistema_Empresas WHERE Activo = 1")
        empresas_count = empresas_rows[0]['c'] if empresas_rows else 0
    except:
        empresas_count = 0
        errors.append("No se pudo contar Sistema_Empresas")
    
    try:
        aliases_rows = _execute_query("SELECT COUNT(*) as c FROM Sistema_EmpresasAlias WHERE Activo = 1")
        aliases_count = aliases_rows[0]['c'] if aliases_rows else 0
    except:
        aliases_count = 0
        errors.append("No se pudo contar Sistema_EmpresasAlias")
    
    try:
        servidores_rows = _execute_query("SELECT COUNT(*) as c FROM Servidores_Conexiones WHERE activo = 1")
        servidores_count = servidores_rows[0]['c'] if servidores_rows else 0
    except:
        servidores_count = 0
        errors.append("No se pudo contar Servidores_Conexiones")
    
    try:
        relaciones_rows = _execute_query("SELECT COUNT(*) as c FROM Sistema_EmpresasServidores WHERE Activo = 1")
        relaciones_count = relaciones_rows[0]['c'] if relaciones_rows else 0
    except:
        relaciones_count = 0
        errors.append("No se pudo contar Sistema_EmpresasServidores")
    
    # Validar empresas canónicas
    origen_ok = resolve_empresa_by_alias('ORIGEN') is not None
    qro_ok = resolve_empresa_by_alias('130QRO') is not None
    mid_ok = resolve_empresa_by_alias('130MID') is not None
    cienfuegos_ok = resolve_empresa_by_alias('CIENFUEGOS') is not None
    estelar_ok = resolve_empresa_by_alias('ESTELAR') is not None
    
    if not origen_ok:
        errors.append("ORIGEN no resuelve correctamente")
    if not qro_ok:
        errors.append("130QRO no resuelve correctamente")
    if not mid_ok:
        errors.append("130MID no resuelve correctamente")
    if not cienfuegos_ok:
        errors.append("CIENFUEGOS no resuelve correctamente")
    if not estelar_ok:
        errors.append("ESTELAR no resuelve correctamente")
    
    # Determinar status
    if errors:
        status = "ERROR" if len(errors) > 2 else "WARNING"
    else:
        status = "OK"
    
    return HealthCheckResult(
        status=status,
        empresas_count=empresas_count,
        aliases_count=aliases_count,
        servidores_count=servidores_count,
        relaciones_count=relaciones_count,
        origen_ok=origen_ok,
        qro_ok=qro_ok,
        mid_ok=mid_ok,
        cienfuegos_ok=cienfuegos_ok,
        estelar_ok=estelar_ok,
        errors=errors
    )


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def get_all_empresas() -> List[EmpresaInfo]:
    """Obtiene todas las empresas activas"""
    query = """
    SELECT EmpresaID, CodigoEmpresa, NombreComercial, NombreEmpresa, Activo
    FROM Sistema_Empresas
    WHERE Activo = 1
    ORDER BY EmpresaID
    """
    
    empresas = []
    try:
        rows = _execute_query(query)
        for row in rows:
            empresas.append(EmpresaInfo(
                empresa_id=row['EmpresaID'],
                codigo_empresa=row['CodigoEmpresa'].strip() if row['CodigoEmpresa'] else '',
                nombre_comercial=row['NombreComercial'].strip() if row['NombreComercial'] else '',
                nombre_empresa=row['NombreEmpresa'].strip() if row['NombreEmpresa'] else '',
                activo=bool(row['Activo'])
            ))
    except Exception as e:
        logger.error(f"Error obteniendo todas las empresas: {e}")
    
    return empresas


def get_all_aliases_for_empresa(empresa_id: int) -> List[Dict[str, str]]:
    """Obtiene todos los aliases activos para una empresa"""
    query = """
    SELECT Alias, AliasNormalizado, OrigenAlias
    FROM Sistema_EmpresasAlias
    WHERE EmpresaID = %d
      AND Activo = 1
    ORDER BY OrigenAlias, Alias
    """
    
    aliases = []
    try:
        rows = _execute_query(query % empresa_id)
        for row in rows:
            aliases.append({
                'alias': row['Alias'].strip() if row['Alias'] else '',
                'alias_normalizado': row['AliasNormalizado'].strip() if row['AliasNormalizado'] else '',
                'origen': row['OrigenAlias'].strip() if row['OrigenAlias'] else ''
            })
    except Exception as e:
        logger.error(f"Error obteniendo aliases para empresa ID={empresa_id}: {e}")
    
    return aliases


def get_sistema_tipos() -> List[Dict[str, Any]]:
    """Obtiene todos los tipos de sistema activos"""
    query = """
    SELECT SistemaTipoID, CodigoSistema, NombreSistema, Descripcion
    FROM Sistema_Tipos
    WHERE Activo = 1
    ORDER BY SistemaTipoID
    """
    
    tipos = []
    try:
        rows = _execute_query(query)
        for row in rows:
            tipos.append({
                'sistema_tipo_id': row['SistemaTipoID'],
                'codigo': row['CodigoSistema'].strip() if row['CodigoSistema'] else '',
                'nombre': row['NombreSistema'].strip() if row['NombreSistema'] else '',
                'descripcion': row['Descripcion'].strip() if row['Descripcion'] else ''
            })
    except Exception as e:
        logger.error(f"Error obteniendo tipos de sistema: {e}")
    
    return tipos
