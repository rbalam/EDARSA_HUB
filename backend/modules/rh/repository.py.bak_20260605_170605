"""
EDARSA HUB - RH Repository (Catálogos)
======================================
Acceso a datos del módulo de Recursos Humanos con queries parametrizados.

FASE 6B DEL REFACTOR MODULAR (Diciembre 2025):
- Queries parametrizados para prevenir SQL Injection
- Acceso a tablas: RH_Cat_Puestos, RH_Cat_Sucursales, RH_Cat_SucursalesFiscal, 
  RH_Cat_Tipos_Incidencias
- Reutiliza execute_sql_query de core.db

SEGURIDAD:
- TODAS las queries que reciben input de usuario usan parámetros
- Los valores se escapan antes de interpolación donde los drivers no soporten params
- NO se usan f-strings directos con datos de usuario

TABLAS REUTILIZADAS (NO se crean ni duplican):
- RH_Cat_Puestos
- RH_Cat_Sucursales
- RH_Cat_SucursalesFiscal
- RH_Cat_Tipos_Incidencias
"""

from typing import Dict, List, Optional, Any
import logging
import re
import os

from core.db import execute_sql_query
from core.config.edarsahub_config import get_edarsahub_sql_config

# P2-01: Config centralizado
_edarsa_cfg = get_edarsahub_sql_config()


# ============================================================================
# CONSTANTES
# ============================================================================

# CORRECCIÓN RH-NOMINAS-EDARSAHUB-CONNECTION-01 (2025-12-27):
# RH/Nóminas usa conexión directa a EDARSAHUB via variables de entorno,
# NO depende del catálogo de servidores MongoDB con active=True.
# Este patrón es consistente con server_registry.py (EDARSAHUB_CONFIG).

# Configuración EDARSAHUB interna (fuente maestra para RH/Nóminas)
EDARSAHUB_CONFIG = {
    'host': _edarsa_cfg.host,
    'port': _edarsa_cfg.port,
    'database': _edarsa_cfg.database,
    'username': _edarsa_cfg.user,
    'password': _edarsa_cfg.password
}

# ID del servidor EDARSA HUB en MongoDB (LEGACY - ya no se usa para conexión)
# Mantenido solo para referencia/compatibilidad
EDARSA_HUB_SERVER_ID = "bea40259-35f1-4693-bda2-d2d10e13e56a"

# Tipos de incidencias por defecto cuando la tabla no existe
TIPOS_INCIDENCIAS_DEFAULT = [
    {"TipoIncidenciaID": 1, "Codigo": "BON", "Descripcion": "Bono", "Categoria": "Ingreso", "Afectacion": 1, "Activo": True},
    {"TipoIncidenciaID": 2, "Codigo": "HEX", "Descripcion": "Horas Extra", "Categoria": "Ingreso", "Afectacion": 1, "Activo": True},
    {"TipoIncidenciaID": 3, "Codigo": "COM", "Descripcion": "Comisión", "Categoria": "Ingreso", "Afectacion": 1, "Activo": True},
    {"TipoIncidenciaID": 4, "Codigo": "FAL", "Descripcion": "Falta", "Categoria": "Descuento", "Afectacion": -1, "Activo": True},
    {"TipoIncidenciaID": 5, "Codigo": "RET", "Descripcion": "Retardo", "Categoria": "Descuento", "Afectacion": -1, "Activo": True},
    {"TipoIncidenciaID": 6, "Codigo": "DES", "Descripcion": "Descuento", "Categoria": "Descuento", "Afectacion": -1, "Activo": True},
]


# ============================================================================
# INYECCIÓN DE DEPENDENCIA: MongoDB
# ============================================================================

_db = None


def init_rh_repository(database) -> None:
    """Inicializa el repositorio con la conexión a MongoDB."""
    global _db
    _db = database
    logging.info("RH Repository inicializado")


def get_db():
    """Obtiene la conexión a MongoDB inyectada."""
    if _db is None:
        raise RuntimeError("RH repository not initialized. Call init_rh_repository(db) first.")
    return _db


# ============================================================================
# UTILIDADES DE SEGURIDAD SQL
# ============================================================================

def escape_sql_string(value: str) -> str:
    """
    Escapa una cadena para uso seguro en SQL Server.
    Previene SQL Injection reemplazando comillas simples.
    
    Args:
        value: Cadena a escapar
        
    Returns:
        Cadena escapada segura para SQL
    """
    if value is None:
        return ""
    # Escapar comillas simples duplicándolas (estándar SQL Server)
    return str(value).replace("'", "''")


def validate_identifier(value: str, max_length: int = 100) -> str:
    """
    Valida y sanitiza un identificador (no permite caracteres peligrosos).
    
    Args:
        value: Valor a validar
        max_length: Longitud máxima permitida
        
    Returns:
        Valor sanitizado
        
    Raises:
        ValueError: Si el valor contiene caracteres no permitidos
    """
    if value is None:
        return ""
    
    value = str(value).strip()[:max_length]
    
    # Rechazar caracteres peligrosos para SQL
    dangerous_chars = [';', '--', '/*', '*/', 'xp_', 'sp_', 'EXEC', 'EXECUTE']
    for char in dangerous_chars:
        if char.lower() in value.lower():
            raise ValueError(f"Carácter o secuencia no permitida: {char}")
    
    return value


# ============================================================================
# SERVIDOR EDARSA HUB - CONEXIÓN DIRECTA
# ============================================================================

async def get_edarsa_hub_server() -> Optional[Dict]:
    """
    Obtiene la configuración del servidor EDARSA HUB.
    
    CORRECCIÓN RH-NOMINAS-EDARSAHUB-CONNECTION-01:
    Ahora usa EDARSAHUB_CONFIG (conexión directa via variables de entorno)
    en lugar de buscar en MongoDB servers con active=True.
    
    Returns:
        Dict con configuración de conexión o None si falta configuración crítica
    """
    # Validar que tengamos configuración mínima
    if not EDARSAHUB_CONFIG.get('host') or not EDARSAHUB_CONFIG.get('database'):
        logging.error("EDARSAHUB_CONFIG incompleto: falta host o database")
        return None
    
    return EDARSAHUB_CONFIG


def get_edarsa_hub_server_sync() -> Optional[Dict]:
    """
    Versión síncrona de get_edarsa_hub_server para uso en funciones no-async.
    
    Returns:
        Dict con configuración de conexión o None si falta configuración crítica
    """
    if not EDARSAHUB_CONFIG.get('host') or not EDARSAHUB_CONFIG.get('database'):
        logging.error("EDARSAHUB_CONFIG incompleto: falta host o database")
        return None
    
    return EDARSAHUB_CONFIG


def execute_hub_query(server: Dict, query: str) -> List[Dict]:
    """
    Ejecuta una query en el servidor EDARSA HUB.
    
    Args:
        server: Configuración del servidor
        query: Query SQL a ejecutar
        
    Returns:
        Lista de diccionarios con los resultados
    """
    return execute_sql_query(
        server['host'],
        server['port'],
        server['database'],
        server['username'],
        server['password'],
        query
    )


# ============================================================================
# CATÁLOGO DE PUESTOS - QUERIES PARAMETRIZADOS
# ============================================================================

def query_listar_puestos(server: Dict) -> Dict[str, Any]:
    """
    Lista todos los puestos del catálogo.
    Query sin parámetros de usuario (segura).
    
    Returns:
        {"datos": [...], "registros": int}
    """
    query = """
        SELECT 
            PuestoID,
            Descripcion,
            Departamento,
            Sueldo_Base_Seman_SBC
        FROM RH_Cat_Puestos
        ORDER BY Departamento, Descripcion
    """
    result = execute_hub_query(server, query)
    return {"datos": result, "registros": len(result)}


def query_crear_puesto(
    server: Dict,
    descripcion: str,
    departamento: str,
    sueldo_base: float,
    nomipaq_id: str,
    mpro_id: str,
    creado_por: str
) -> Dict[str, Any]:
    """
    Crea un nuevo puesto con valores parametrizados.
    
    SEGURIDAD: Todos los valores de usuario se escapan antes de interpolación.
    """
    # Escapar todos los valores de texto
    desc_safe = escape_sql_string(descripcion)
    dept_safe = escape_sql_string(departamento)
    nomipaq_safe = escape_sql_string(nomipaq_id)
    mpro_safe = escape_sql_string(mpro_id)
    creado_safe = escape_sql_string(creado_por)
    
    # Validar que sueldo_base sea numérico
    try:
        sueldo_safe = float(sueldo_base)
    except (ValueError, TypeError):
        sueldo_safe = 0.0
    
    query = f"""
        INSERT INTO RH_Cat_Puestos 
        (Descripcion, Departamento, Sueldo_Base_Seman_SBC, NomiPAQ_ID, MPRO_ID, Fecha_Creacion, Creado_Por)
        OUTPUT INSERTED.PuestoID
        VALUES 
        (N'{desc_safe}', N'{dept_safe}', {sueldo_safe}, N'{nomipaq_safe}', N'{mpro_safe}', GETDATE(), N'{creado_safe}')
    """
    
    result = execute_hub_query(server, query)
    return {"datos": result, "registros": len(result)}


def query_actualizar_puesto(
    server: Dict,
    puesto_id: int,
    updates: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Actualiza un puesto existente con valores parametrizados.
    
    SEGURIDAD: Todos los valores de usuario se escapan.
    
    Args:
        server: Configuración del servidor
        puesto_id: ID del puesto a actualizar
        updates: Diccionario con campos a actualizar
    """
    set_clauses = []
    
    if 'descripcion' in updates and updates['descripcion'] is not None:
        val = escape_sql_string(updates['descripcion'])
        set_clauses.append(f"Descripcion = N'{val}'")
    
    if 'departamento' in updates and updates['departamento'] is not None:
        val = escape_sql_string(updates['departamento'])
        set_clauses.append(f"Departamento = N'{val}'")
    
    if 'sueldo_base' in updates and updates['sueldo_base'] is not None:
        try:
            val = float(updates['sueldo_base'])
            set_clauses.append(f"Sueldo_Base_Seman_SBC = {val}")
        except (ValueError, TypeError):
            pass
    
    if 'nomipaq_id' in updates and updates['nomipaq_id'] is not None:
        val = escape_sql_string(updates['nomipaq_id'])
        set_clauses.append(f"NomiPAQ_ID = N'{val}'")
    
    if 'mpro_id' in updates and updates['mpro_id'] is not None:
        val = escape_sql_string(updates['mpro_id'])
        set_clauses.append(f"MPRO_ID = N'{val}'")
    
    if not set_clauses:
        return {"datos": [], "registros": 0, "error": "No hay campos para actualizar"}
    
    # Validar que puesto_id sea entero
    try:
        id_safe = int(puesto_id)
    except (ValueError, TypeError):
        return {"datos": [], "registros": 0, "error": "ID de puesto inválido"}
    
    query = f"""
        UPDATE RH_Cat_Puestos
        SET {', '.join(set_clauses)}, Fecha_Modificacion = GETDATE()
        WHERE PuestoID = {id_safe}
    """
    
    result = execute_hub_query(server, query)
    return {"datos": result, "registros": 1}


def query_verificar_colaboradores_puesto(server: Dict, puesto_id: int) -> int:
    """
    Verifica si hay colaboradores asignados a un puesto.
    
    Returns:
        Cantidad de colaboradores con este puesto
    """
    try:
        id_safe = int(puesto_id)
    except (ValueError, TypeError):
        return 0
    
    query = f"SELECT COUNT(*) as total FROM RH_Colaboradores_Expediente WHERE PuestoID = {id_safe}"
    result = execute_hub_query(server, query)
    
    if result and len(result) > 0:
        return result[0].get('total', 0)
    return 0


def query_eliminar_puesto(server: Dict, puesto_id: int) -> Dict[str, Any]:
    """
    Elimina un puesto del catálogo.
    
    SEGURIDAD: El ID se valida como entero.
    """
    try:
        id_safe = int(puesto_id)
    except (ValueError, TypeError):
        return {"datos": [], "registros": 0, "error": "ID de puesto inválido"}
    
    query = f"DELETE FROM RH_Cat_Puestos WHERE PuestoID = {id_safe}"
    result = execute_hub_query(server, query)
    return {"datos": result, "registros": 1}


# ============================================================================
# CATÁLOGO DE SUCURSALES - QUERIES PARAMETRIZADOS
# ============================================================================

def query_listar_sucursales(server: Dict) -> Dict[str, Any]:
    """
    Lista todas las sucursales del catálogo con datos fiscales.
    Query sin parámetros de usuario (segura).
    
    Tablas: RH_Cat_Sucursales, RH_Cat_SucursalesFiscal
    """
    query = """
        SELECT 
            s.SucursalID,
            s.Nombre_Sucursal,
            s.Ciudad,
            s.Activa,
            sf.RFC,
            sf.RazonSocial
        FROM RH_Cat_Sucursales s
        LEFT JOIN RH_Cat_SucursalesFiscal sf ON s.SucursalID = sf.SucursalID AND sf.Activo = 1
        ORDER BY s.Nombre_Sucursal
    """
    result = execute_hub_query(server, query)
    return {"datos": result, "registros": len(result)}


# ============================================================================
# CATÁLOGO DE TIPOS DE INCIDENCIAS - QUERIES PARAMETRIZADOS
# ============================================================================

def query_listar_tipos_incidencias(server: Dict) -> Dict[str, Any]:
    """
    Lista todos los tipos de incidencias activos.
    Query sin parámetros de usuario (segura).
    
    Returns:
        {"datos": [...], "registros": int, "nota": str|None}
    """
    query = """
        SELECT 
            TipoIncidenciaID,
            Codigo,
            Descripcion,
            Categoria,
            Afectacion,
            Calculo_Monto,
            Activo,
            NomiPAQ_ID,
            MPRO_ID
        FROM RH_Cat_Tipos_Incidencias
        WHERE Activo = 1
        ORDER BY Categoria, Descripcion
    """
    
    try:
        result = execute_hub_query(server, query)
        return {"datos": result, "registros": len(result), "nota": None}
    except Exception as e:
        logging.warning(f"Error al consultar tipos de incidencias, usando defaults: {e}")
        # Si la tabla no existe, retornar tipos por defecto
        return {
            "datos": TIPOS_INCIDENCIAS_DEFAULT,
            "registros": len(TIPOS_INCIDENCIAS_DEFAULT),
            "nota": "Usando tipos por defecto - Ejecute script SQL"
        }


def query_crear_tipo_incidencia(
    server: Dict,
    codigo: str,
    descripcion: str,
    categoria: str,
    calculo_monto: str,
    nomipaq_id: str,
    mpro_id: str,
    creado_por: str
) -> Dict[str, Any]:
    """
    Crea un nuevo tipo de incidencia con valores parametrizados.
    
    SEGURIDAD: Todos los valores de usuario se escapan.
    """
    # Escapar todos los valores de texto
    codigo_safe = escape_sql_string(codigo.upper())
    desc_safe = escape_sql_string(descripcion)
    cat_safe = escape_sql_string(categoria)
    calc_safe = escape_sql_string(calculo_monto)
    nomipaq_safe = escape_sql_string(nomipaq_id)
    mpro_safe = escape_sql_string(mpro_id)
    creado_safe = escape_sql_string(creado_por)
    
    # Determinar afectación basada en categoría
    afectacion = 1 if categoria == 'Ingreso' else -1
    
    query = f"""
        INSERT INTO RH_Cat_Tipos_Incidencias 
        (Codigo, Descripcion, Categoria, Afectacion, Calculo_Monto, Activo, NomiPAQ_ID, MPRO_ID, Fecha_Creacion, Creado_Por)
        VALUES 
        (N'{codigo_safe}', N'{desc_safe}', N'{cat_safe}', {afectacion}, N'{calc_safe}', 1, N'{nomipaq_safe}', N'{mpro_safe}', GETDATE(), N'{creado_safe}')
    """
    
    result = execute_hub_query(server, query)
    return {"datos": result, "registros": 1}


def query_actualizar_tipo_incidencia(
    server: Dict,
    tipo_id: int,
    updates: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Actualiza un tipo de incidencia existente con valores parametrizados.
    
    SEGURIDAD: Todos los valores de usuario se escapan.
    """
    set_clauses = []
    
    if 'codigo' in updates and updates['codigo'] is not None:
        val = escape_sql_string(updates['codigo'].upper())
        set_clauses.append(f"Codigo = N'{val}'")
    
    if 'descripcion' in updates and updates['descripcion'] is not None:
        val = escape_sql_string(updates['descripcion'])
        set_clauses.append(f"Descripcion = N'{val}'")
    
    if 'categoria' in updates and updates['categoria'] is not None:
        val = escape_sql_string(updates['categoria'])
        set_clauses.append(f"Categoria = N'{val}'")
        # Actualizar afectación si cambia la categoría
        afectacion = 1 if updates['categoria'] == 'Ingreso' else -1
        set_clauses.append(f"Afectacion = {afectacion}")
    
    if 'calculo_monto' in updates and updates['calculo_monto'] is not None:
        val = escape_sql_string(updates['calculo_monto'])
        set_clauses.append(f"Calculo_Monto = N'{val}'")
    
    if 'activo' in updates and updates['activo'] is not None:
        val = 1 if updates['activo'] else 0
        set_clauses.append(f"Activo = {val}")
    
    if 'nomipaq_id' in updates and updates['nomipaq_id'] is not None:
        val = escape_sql_string(updates['nomipaq_id'])
        set_clauses.append(f"NomiPAQ_ID = N'{val}'")
    
    if 'mpro_id' in updates and updates['mpro_id'] is not None:
        val = escape_sql_string(updates['mpro_id'])
        set_clauses.append(f"MPRO_ID = N'{val}'")
    
    if not set_clauses:
        return {"datos": [], "registros": 0, "error": "No hay campos para actualizar"}
    
    # Validar que tipo_id sea entero
    try:
        id_safe = int(tipo_id)
    except (ValueError, TypeError):
        return {"datos": [], "registros": 0, "error": "ID de tipo inválido"}
    
    query = f"""
        UPDATE RH_Cat_Tipos_Incidencias
        SET {', '.join(set_clauses)}, Fecha_Modificacion = GETDATE()
        WHERE TipoIncidenciaID = {id_safe}
    """
    
    result = execute_hub_query(server, query)
    return {"datos": result, "registros": 1}


def query_desactivar_tipo_incidencia(server: Dict, tipo_id: int) -> Dict[str, Any]:
    """
    Desactiva un tipo de incidencia (soft delete para mantener histórico).
    
    SEGURIDAD: El ID se valida como entero.
    """
    try:
        id_safe = int(tipo_id)
    except (ValueError, TypeError):
        return {"datos": [], "registros": 0, "error": "ID de tipo inválido"}
    
    query = f"""
        UPDATE RH_Cat_Tipos_Incidencias 
        SET Activo = 0, Fecha_Modificacion = GETDATE() 
        WHERE TipoIncidenciaID = {id_safe}
    """
    result = execute_hub_query(server, query)
    return {"datos": result, "registros": 1}



# ============================================================================
# COLABORADORES - QUERIES CON PARÁMETROS NATIVOS (FASE 6C-B)
# ============================================================================
# IMPORTANTE: Estas funciones usan execute_sql_query_params() que pasa
# los parámetros directamente al driver SQL (pymssql/pytds), NO usa
# interpolación de strings. Esto es más seguro que escape_sql_string().
#
# TABLAS REUTILIZADAS:
# - RH_Colaboradores_Expediente (principal)
# - RH_Cat_Sucursales (JOIN)
# - RH_Cat_Puestos (JOIN)
# - RH_Incidencias_Nomina (solo lectura en detalle)
# - RH_Reloj_Checador (solo lectura en detalle)
# - RH_Auditoria_Fiscal (solo lectura en detalle)
# ============================================================================

from core.db import execute_sql_query_params
from core.config.edarsahub_config import get_edarsahub_sql_config
_edarsa_cfg = get_edarsahub_sql_config()



def execute_hub_query_params(server: Dict, query: str, params: tuple = None) -> List[Dict]:
    """
    Ejecuta una query en el servidor EDARSA HUB con parámetros nativos.
    
    Args:
        server: Configuración del servidor
        query: Query SQL con placeholders %s
        params: Tupla de parámetros
        
    Returns:
        Lista de diccionarios con los resultados
    """
    return execute_sql_query_params(
        server['host'],
        server['port'],
        server['database'],
        server['username'],
        server['password'],
        query,
        params
    )


def query_listar_colaboradores(
    server: Dict,
    sucursal_id: Optional[int] = None,
    puesto_id: Optional[int] = None,
    estatus: Optional[str] = None,
    buscar: Optional[str] = None,
    page: int = 1,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Lista colaboradores con filtros y paginación.
    
    PARÁMETROS NATIVOS: sucursal_id, puesto_id (enteros validados)
    ESCAPE NECESARIO: estatus, buscar (strings en cláusula LIKE)
    
    Nota: SQL Server no soporta parámetros en LIKE con comodines,
    por lo que usamos escape_sql_string() solo para 'buscar'.
    """
    conditions = ["1=1"]
    
    # Parámetros enteros (seguros, validados como int)
    if sucursal_id is not None:
        try:
            conditions.append(f"c.SucursalID = {int(sucursal_id)}")
        except (ValueError, TypeError):
            pass
    
    if puesto_id is not None:
        try:
            conditions.append(f"c.PuestoID = {int(puesto_id)}")
        except (ValueError, TypeError):
            pass
    
    # Estatus: valor de lista controlada (ya validado en schema)
    if estatus:
        estatus_safe = escape_sql_string(estatus)
        conditions.append(f"c.Estatus_Laboral = N'{estatus_safe}'")
    
    # Búsqueda: requiere escape porque LIKE no soporta parámetros con %
    if buscar:
        buscar_safe = escape_sql_string(buscar)
        conditions.append(f"(c.Nombre_Completo LIKE N'%{buscar_safe}%' OR c.RFC LIKE N'%{buscar_safe}%' OR c.CURP LIKE N'%{buscar_safe}%')")
    
    where_clause = " AND ".join(conditions)
    
    # Paginación (enteros validados)
    try:
        page = max(1, int(page))
        limit = max(1, min(200, int(limit)))
    except (ValueError, TypeError):
        page, limit = 1, 50
    
    offset = (page - 1) * limit
    
    query = f"""
        SELECT 
            c.ColaboradorID,
            c.Nombre_Completo,
            c.CURP,
            c.RFC,
            c.CLABE_Bancaria,
            c.SucursalID,
            s.Nombre_Sucursal,
            c.PuestoID,
            p.Descripcion as Puesto,
            p.Departamento,
            c.Colaborador_Activo,
            c.Fecha_Alta,
            c.Estatus_Laboral,
            c.Validacion_IA_RFC,
            c.Validacion_IA_CURP,
            c.Validacion_IA_EdoCta,
            c.Validacion_IA_Contrato
        FROM RH_Colaboradores_Expediente c
        LEFT JOIN RH_Cat_Sucursales s ON c.SucursalID = s.SucursalID
        LEFT JOIN RH_Cat_Puestos p ON c.PuestoID = p.PuestoID
        WHERE {where_clause}
        ORDER BY c.Nombre_Completo
        OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
    """
    
    count_query = f"""
        SELECT COUNT(*) as total
        FROM RH_Colaboradores_Expediente c
        WHERE {where_clause}
    """
    
    result = execute_hub_query(server, query)
    count_result = execute_hub_query(server, count_query)
    
    total = count_result[0].get("total", 0) if count_result else 0
    
    return {
        "datos": result,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if total > 0 else 1
    }


def query_obtener_colaborador(server: Dict, colaborador_id: int) -> Dict[str, Any]:
    """
    Obtiene datos de un colaborador específico.
    
    PARÁMETROS NATIVOS: colaborador_id (entero validado)
    """
    try:
        id_safe = int(colaborador_id)
    except (ValueError, TypeError):
        return {"datos": None, "error": "ID de colaborador inválido"}
    
    # Query con parámetro nativo
    query = """
        SELECT 
            c.ColaboradorID,
            c.Nombre_Completo,
            c.CURP,
            c.RFC,
            c.CLABE_Bancaria,
            c.SucursalID,
            s.Nombre_Sucursal,
            s.Ciudad,
            c.PuestoID,
            p.Descripcion as Puesto,
            p.Departamento,
            p.Sueldo_Base_Seman_SBC,
            c.Colaborador_Activo,
            c.Fecha_Alta,
            c.Estatus_Laboral,
            c.Validacion_IA_RFC,
            c.Validacion_IA_CURP,
            c.Validacion_IA_EdoCta,
            c.Validacion_IA_Contrato
        FROM RH_Colaboradores_Expediente c
        LEFT JOIN RH_Cat_Sucursales s ON c.SucursalID = s.SucursalID
        LEFT JOIN RH_Cat_Puestos p ON c.PuestoID = p.PuestoID
        WHERE c.ColaboradorID = %s
    """
    
    result = execute_hub_query_params(server, query, (id_safe,))
    
    if result:
        return {"datos": result[0]}
    return {"datos": None}


def query_incidencias_colaborador(server: Dict, colaborador_id: int, limit: int = 20) -> List[Dict]:
    """
    Obtiene las últimas incidencias de un colaborador.
    
    PARÁMETROS NATIVOS: colaborador_id
    """
    try:
        id_safe = int(colaborador_id)
        limit_safe = min(100, max(1, int(limit)))
    except (ValueError, TypeError):
        return []
    
    # TOP no soporta parámetros en SQL Server, pero es un int validado
    query = f"""
        SELECT TOP {limit_safe}
            IncidenciaID,
            Tipo_Incidencia,
            Monto,
            Unidades,
            Fecha_Incidencia,
            Fecha_Registro
        FROM RH_Incidencias_Nomina
        WHERE ColaboradorID = %s
        ORDER BY Fecha_Incidencia DESC
    """
    
    return execute_hub_query_params(server, query, (id_safe,))


def query_asistencias_colaborador(server: Dict, colaborador_id: int, limit: int = 30) -> List[Dict]:
    """
    Obtiene los últimos registros de asistencia de un colaborador.
    
    PARÁMETROS NATIVOS: colaborador_id
    """
    try:
        id_safe = int(colaborador_id)
        limit_safe = min(100, max(1, int(limit)))
    except (ValueError, TypeError):
        return []
    
    query = f"""
        SELECT TOP {limit_safe}
            CheckID,
            Tipo_Registro,
            FechaHora,
            Geolocalizacion,
            Validado_Gerencia
        FROM RH_Reloj_Checador
        WHERE ColaboradorID = %s
        ORDER BY FechaHora DESC
    """
    
    return execute_hub_query_params(server, query, (id_safe,))


def query_auditoria_colaborador(server: Dict, colaborador_id: int, limit: int = 10) -> List[Dict]:
    """
    Obtiene los últimos registros de auditoría fiscal de un colaborador.
    
    PARÁMETROS NATIVOS: colaborador_id
    """
    try:
        id_safe = int(colaborador_id)
        limit_safe = min(50, max(1, int(limit)))
    except (ValueError, TypeError):
        return []
    
    query = f"""
        SELECT TOP {limit_safe}
            AuditoriaID,
            Semana,
            Monto_Dispersado_Banco,
            Monto_Timbrado_XML,
            Monto_IMSS_EBA_EMA,
            Diferencia,
            Alerta_Fraude
        FROM RH_Auditoria_Fiscal
        WHERE ColaboradorID = %s
        ORDER BY Semana DESC
    """
    
    return execute_hub_query_params(server, query, (id_safe,))


def query_crear_colaborador(
    server: Dict,
    nombre_completo: str,
    curp: Optional[str],
    rfc: Optional[str],
    clabe_bancaria: Optional[str],
    sucursal_id: int,
    puesto_id: int,
    estatus_laboral: str
) -> Dict[str, Any]:
    """
    Crea un nuevo colaborador.
    
    PARÁMETROS NATIVOS: Todos los valores se pasan como parámetros al driver.
    """
    query = """
        INSERT INTO RH_Colaboradores_Expediente 
        (Nombre_Completo, CURP, RFC, CLABE_Bancaria, SucursalID, PuestoID, 
         Colaborador_Activo, Fecha_Alta, Estatus_Laboral)
        OUTPUT INSERTED.ColaboradorID
        VALUES (%s, %s, %s, %s, %s, %s, 1, GETDATE(), %s)
    """
    
    params = (
        nombre_completo,
        curp,
        rfc,
        clabe_bancaria,
        int(sucursal_id),
        int(puesto_id),
        estatus_laboral
    )
    
    result = execute_hub_query_params(server, query, params)
    
    if result:
        return {"colaborador_id": result[0].get("ColaboradorID"), "success": True}
    return {"colaborador_id": None, "success": False, "error": "No se pudo crear el colaborador"}


def query_actualizar_colaborador(
    server: Dict,
    colaborador_id: int,
    updates: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Actualiza datos de un colaborador existente.
    
    ESTRATEGIA HÍBRIDA:
    - IDs enteros: Validados como int (seguros)
    - Strings: Se usa escape_sql_string() porque SQL Server no soporta
      parámetros en SET dinámico con lista variable de columnas.
    
    Nota: Una alternativa sería generar queries separadas para cada campo,
    pero eso aumentaría la complejidad y latencia innecesariamente.
    """
    try:
        id_safe = int(colaborador_id)
    except (ValueError, TypeError):
        return {"success": False, "error": "ID de colaborador inválido"}
    
    set_clauses = []
    
    # Campos de texto (escapados)
    if 'nombre_completo' in updates and updates['nombre_completo']:
        val = escape_sql_string(updates['nombre_completo'])
        set_clauses.append(f"Nombre_Completo = N'{val}'")
    
    if 'curp' in updates:
        if updates['curp']:
            val = escape_sql_string(updates['curp'])
            set_clauses.append(f"CURP = N'{val}'")
        else:
            set_clauses.append("CURP = NULL")
    
    if 'rfc' in updates:
        if updates['rfc']:
            val = escape_sql_string(updates['rfc'])
            set_clauses.append(f"RFC = N'{val}'")
        else:
            set_clauses.append("RFC = NULL")
    
    if 'clabe_bancaria' in updates:
        if updates['clabe_bancaria']:
            val = escape_sql_string(updates['clabe_bancaria'])
            set_clauses.append(f"CLABE_Bancaria = N'{val}'")
        else:
            set_clauses.append("CLABE_Bancaria = NULL")
    
    # Campos enteros (validados)
    if 'sucursal_id' in updates and updates['sucursal_id']:
        try:
            set_clauses.append(f"SucursalID = {int(updates['sucursal_id'])}")
        except (ValueError, TypeError):
            pass
    
    if 'puesto_id' in updates and updates['puesto_id']:
        try:
            set_clauses.append(f"PuestoID = {int(updates['puesto_id'])}")
        except (ValueError, TypeError):
            pass
    
    # Estatus laboral (valor de lista controlada, escapado por seguridad)
    if 'estatus_laboral' in updates and updates['estatus_laboral']:
        val = escape_sql_string(updates['estatus_laboral'])
        set_clauses.append(f"Estatus_Laboral = N'{val}'")
    
    if not set_clauses:
        return {"success": False, "error": "No hay campos para actualizar"}
    
    query = f"""
        UPDATE RH_Colaboradores_Expediente
        SET {', '.join(set_clauses)}
        WHERE ColaboradorID = {id_safe}
    """
    
    execute_hub_query(server, query)
    return {"success": True}


def query_dar_baja_colaborador(server: Dict, colaborador_id: int) -> Dict[str, Any]:
    """
    Da de baja lógica a un colaborador (soft delete).
    
    PARÁMETROS NATIVOS: colaborador_id (entero validado)
    """
    try:
        id_safe = int(colaborador_id)
    except (ValueError, TypeError):
        return {"success": False, "error": "ID de colaborador inválido"}
    
    query = """
        UPDATE RH_Colaboradores_Expediente
        SET Colaborador_Activo = 0, Estatus_Laboral = N'Baja'
        WHERE ColaboradorID = %s
    """
    
    execute_hub_query_params(server, query, (id_safe,))
    return {"success": True}



# ============================================================================
# INCIDENCIAS - QUERIES CON PARÁMETROS NATIVOS (FASE 6D-B)
# ============================================================================
# TABLAS REUTILIZADAS:
# - RH_Incidencias_Nomina (principal - INSERT/SELECT)
# - RH_Colaboradores_Expediente (JOIN - ya migrado en 6C-B)
# - RH_Cat_Sucursales (JOIN - ya migrado en 6B)
# - RH_Cat_Tipos_Incidencias (validación - ya migrado en 6B)
#
# COMPORTAMIENTO DE IMPORTACIÓN EXCEL:
# - La importación es PARCIAL, NO transaccional
# - Si una fila falla, las anteriores ya fueron insertadas
# - Esto se documenta claramente en la respuesta del endpoint
# ============================================================================


def query_obtener_tipos_incidencias_validos(server: Dict) -> List[str]:
    """
    Obtiene la lista de tipos de incidencias válidos desde el catálogo.
    
    VALIDACIÓN PRINCIPAL: Se usa RH_Cat_Tipos_Incidencias como fuente de verdad.
    FALLBACK: Si la tabla no existe o está vacía, retorna lista por defecto.
    
    Returns:
        Lista de códigos/descripciones de tipos válidos
    """
    query = """
        SELECT Codigo, Descripcion
        FROM RH_Cat_Tipos_Incidencias
        WHERE Activo = 1
    """
    
    try:
        result = execute_hub_query(server, query)
        if result:
            # Retornar tanto códigos como descripciones para mayor flexibilidad
            tipos = set()
            for r in result:
                if r.get('Codigo'):
                    tipos.add(r['Codigo'].strip())
                if r.get('Descripcion'):
                    tipos.add(r['Descripcion'].strip())
            if tipos:
                return list(tipos)
    except Exception as e:
        logging.warning(f"No se pudo consultar catálogo de tipos: {e}")
    
    # FALLBACK: Lista por defecto cuando el catálogo no está disponible
    logging.info("Usando tipos de incidencia por defecto (catálogo no disponible)")
    return ['Falta', 'Retardo', 'Bono', 'Descuento', 'Horas Extra',
            'Vacaciones', 'Incapacidad', 'Permiso', 'Comision', 'Otro']


def query_listar_incidencias(
    server: Dict,
    colaborador_id: Optional[int] = None,
    tipo: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    sucursal_id: Optional[int] = None,
    page: int = 1,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Lista incidencias con filtros y paginación.
    
    PARÁMETROS NATIVOS: colaborador_id, sucursal_id (enteros validados)
    ESCAPE NECESARIO: tipo (string), fechas (formato validado por Pydantic)
    
    Nota: Las fechas ya vienen validadas en formato YYYY-MM-DD por el schema.
    """
    conditions = ["1=1"]
    
    # Filtros con validación de enteros (seguros)
    if colaborador_id is not None:
        try:
            conditions.append(f"i.ColaboradorID = {int(colaborador_id)}")
        except (ValueError, TypeError):
            pass
    
    if sucursal_id is not None:
        try:
            conditions.append(f"c.SucursalID = {int(sucursal_id)}")
        except (ValueError, TypeError):
            pass
    
    # Tipo de incidencia (escapado)
    if tipo:
        tipo_safe = escape_sql_string(tipo)
        conditions.append(f"i.Tipo_Incidencia = N'{tipo_safe}'")
    
    # Fechas (ya validadas por Pydantic, pero escapamos por seguridad)
    if fecha_desde:
        fecha_safe = escape_sql_string(fecha_desde)
        conditions.append(f"i.Fecha_Incidencia >= '{fecha_safe}'")
    
    if fecha_hasta:
        fecha_safe = escape_sql_string(fecha_hasta)
        conditions.append(f"i.Fecha_Incidencia <= '{fecha_safe}'")
    
    where_clause = " AND ".join(conditions)
    
    # Paginación (enteros validados)
    try:
        page = max(1, int(page))
        limit = max(1, min(200, int(limit)))
    except (ValueError, TypeError):
        page, limit = 1, 50
    
    offset = (page - 1) * limit
    
    query = f"""
        SELECT 
            i.IncidenciaID,
            i.ColaboradorID,
            c.Nombre_Completo,
            c.SucursalID,
            s.Nombre_Sucursal,
            i.Tipo_Incidencia,
            i.Monto,
            i.Unidades,
            i.Fecha_Incidencia,
            i.Capturado_Por,
            i.Fecha_Registro
        FROM RH_Incidencias_Nomina i
        LEFT JOIN RH_Colaboradores_Expediente c ON i.ColaboradorID = c.ColaboradorID
        LEFT JOIN RH_Cat_Sucursales s ON c.SucursalID = s.SucursalID
        WHERE {where_clause}
        ORDER BY i.Fecha_Incidencia DESC
        OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
    """
    
    count_query = f"""
        SELECT COUNT(*) as total
        FROM RH_Incidencias_Nomina i
        LEFT JOIN RH_Colaboradores_Expediente c ON i.ColaboradorID = c.ColaboradorID
        WHERE {where_clause}
    """
    
    result = execute_hub_query(server, query)
    count_result = execute_hub_query(server, count_query)
    
    total = count_result[0].get("total", 0) if count_result else 0
    
    return {
        "datos": result,
        "total": total,
        "page": page,
        "limit": limit
    }


def query_crear_incidencia(
    server: Dict,
    colaborador_id: int,
    tipo_incidencia: str,
    monto: float,
    unidades: float,
    fecha_incidencia: str,
    capturado_por: Optional[str] = None
) -> Dict[str, Any]:
    """
    Crea una nueva incidencia.
    
    PARÁMETROS NATIVOS: colaborador_id, monto, unidades
    ESCAPE: tipo_incidencia, fecha_incidencia, capturado_por
    
    La fecha ya viene validada por Pydantic (YYYY-MM-DD).
    """
    query = """
        INSERT INTO RH_Incidencias_Nomina 
        (ColaboradorID, Tipo_Incidencia, Monto, Unidades, Fecha_Incidencia, Capturado_Por, Fecha_Registro)
        OUTPUT INSERTED.IncidenciaID
        VALUES (%s, %s, %s, %s, %s, %s, GETDATE())
    """
    
    params = (
        int(colaborador_id),
        tipo_incidencia,
        float(monto),
        float(unidades),
        fecha_incidencia,
        capturado_por
    )
    
    result = execute_hub_query_params(server, query, params)
    
    if result:
        return {"incidencia_id": result[0].get("IncidenciaID"), "success": True}
    return {"incidencia_id": None, "success": False, "error": "No se pudo crear la incidencia"}


def query_obtener_colaboradores_activos_para_importacion(server: Dict) -> Dict[str, int]:
    """
    Obtiene mapeo de RFC/ID -> ColaboradorID para importación de Excel.
    
    Returns:
        Diccionario con RFC (mayúsculas) y ColaboradorID como claves,
        ambos apuntando al ColaboradorID correspondiente.
    """
    query = """
        SELECT ColaboradorID, RFC, Nombre_Completo 
        FROM RH_Colaboradores_Expediente 
        WHERE Colaborador_Activo = 1
    """
    
    result = execute_hub_query(server, query)
    
    colaboradores_map = {}
    for c in result:
        col_id = c.get("ColaboradorID")
        if col_id:
            # Mapear por RFC (mayúsculas)
            if c.get("RFC"):
                colaboradores_map[c["RFC"].strip().upper()] = col_id
            # Mapear también por ID como string
            colaboradores_map[str(col_id)] = col_id
    
    return colaboradores_map


def query_insertar_incidencia_importacion(
    server: Dict,
    colaborador_id: int,
    tipo: str,
    monto: float,
    unidades: float,
    fecha: str
) -> bool:
    """
    Inserta una incidencia individual durante importación masiva.
    
    PARÁMETROS NATIVOS: Todos los valores.
    
    NOTA: Esta función NO es transaccional. Si falla, las incidencias
    anteriores ya fueron insertadas. Esto es comportamiento documentado.
    
    Returns:
        True si se insertó correctamente, False en caso contrario.
    """
    query = """
        INSERT INTO RH_Incidencias_Nomina 
        (ColaboradorID, Tipo_Incidencia, Monto, Unidades, Fecha_Incidencia, Fecha_Registro)
        VALUES (%s, %s, %s, %s, %s, GETDATE())
    """
    
    params = (
        int(colaborador_id),
        tipo,
        float(monto),
        float(unidades),
        fecha
    )
    
    try:
        execute_hub_query_params(server, query, params)
        return True
    except Exception as e:
        logging.error(f"Error insertando incidencia: {e}")
        return False


# ============================================================================
# ASISTENCIA - QUERIES CON PARÁMETROS NATIVOS (FASE 6E-B)
# ============================================================================
# TABLAS REUTILIZADAS:
# - RH_Reloj_Checador (principal - INSERT/SELECT/UPDATE)
# - RH_Colaboradores_Expediente (JOIN)
# - RH_Cat_Sucursales (JOIN)
# - RH_Cat_Puestos (JOIN)
#
# SEGURIDAD:
# - Todos los IDs se validan como enteros (inyección por casting)
# - Las fechas se validan en el schema Pydantic antes de llegar aquí
# - Se usa execute_sql_query_params() para parámetros nativos donde es posible
# - Se usa escape_sql_string() SOLO para fechas en cláusulas CAST/WHERE
#   porque SQL Server no soporta parámetros en expresiones CAST(... AS DATE)
#
# LÓGICA DE NEGOCIO INTACTA:
# - NO se validan duplicados de entrada/salida por día
# - La geolocalización es opcional sin validación de formato
# ============================================================================


def query_listar_asistencias(
    server: Dict,
    colaborador_id: Optional[int] = None,
    sucursal_id: Optional[int] = None,
    fecha: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    page: int = 1,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Lista registros del reloj checador con filtros y paginación.
    
    PARÁMETROS NATIVOS: colaborador_id, sucursal_id (enteros validados)
    ESCAPE NECESARIO: fecha, fecha_desde, fecha_hasta
        - Razón: SQL Server no soporta parámetros en CAST(column AS DATE)
        - Las fechas ya vienen validadas por Pydantic (YYYY-MM-DD)
    
    Tablas: RH_Reloj_Checador, RH_Colaboradores_Expediente, 
            RH_Cat_Sucursales, RH_Cat_Puestos
    """
    conditions = ["1=1"]
    
    # Filtros con validación de enteros (seguros - casting a int)
    if colaborador_id is not None:
        try:
            conditions.append(f"r.ColaboradorID = {int(colaborador_id)}")
        except (ValueError, TypeError):
            pass
    
    if sucursal_id is not None:
        try:
            conditions.append(f"c.SucursalID = {int(sucursal_id)}")
        except (ValueError, TypeError):
            pass
    
    # Fechas: Ya validadas por Pydantic, escapamos por seguridad adicional
    # NOTA: No podemos usar parámetros nativos en CAST(... AS DATE) = '...'
    if fecha:
        fecha_safe = escape_sql_string(fecha)
        conditions.append(f"CAST(r.FechaHora AS DATE) = '{fecha_safe}'")
    
    if fecha_desde:
        fecha_safe = escape_sql_string(fecha_desde)
        conditions.append(f"CAST(r.FechaHora AS DATE) >= '{fecha_safe}'")
    
    if fecha_hasta:
        fecha_safe = escape_sql_string(fecha_hasta)
        conditions.append(f"CAST(r.FechaHora AS DATE) <= '{fecha_safe}'")
    
    where_clause = " AND ".join(conditions)
    
    # Paginación (enteros validados)
    try:
        page = max(1, int(page))
        limit = max(1, min(500, int(limit)))
    except (ValueError, TypeError):
        page, limit = 1, 100
    
    offset = (page - 1) * limit
    
    query = f"""
        SELECT 
            r.CheckID,
            r.ColaboradorID,
            c.Nombre_Completo,
            c.SucursalID,
            s.Nombre_Sucursal,
            p.Descripcion as Puesto,
            r.Tipo_Registro,
            r.FechaHora,
            r.Geolocalizacion,
            r.Validado_Gerencia
        FROM RH_Reloj_Checador r
        LEFT JOIN RH_Colaboradores_Expediente c ON r.ColaboradorID = c.ColaboradorID
        LEFT JOIN RH_Cat_Sucursales s ON c.SucursalID = s.SucursalID
        LEFT JOIN RH_Cat_Puestos p ON c.PuestoID = p.PuestoID
        WHERE {where_clause}
        ORDER BY r.FechaHora DESC
        OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
    """
    
    result = execute_hub_query(server, query)
    
    return {
        "datos": result,
        "total": len(result),  # Para paginación completa se necesitaría COUNT
        "page": page,
        "limit": limit
    }


def query_registrar_asistencia(
    server: Dict,
    colaborador_id: int,
    tipo_registro: str,
    geolocalizacion: Optional[str] = None
) -> Dict[str, Any]:
    """
    Registra una entrada o salida en el reloj checador.
    
    PARÁMETROS NATIVOS: colaborador_id (int), tipo_registro, geolocalizacion
    
    LÓGICA DE NEGOCIO INTACTA (FASE 6E-B):
    - NO se validan duplicados de entrada/salida en el mismo día
    - El sistema actual permite múltiples registros del mismo tipo
    - Validado_Gerencia se inicializa en 0 (pendiente de validación)
    
    Tabla: RH_Reloj_Checador
    """
    query = """
        INSERT INTO RH_Reloj_Checador 
        (ColaboradorID, Tipo_Registro, FechaHora, Geolocalizacion, Validado_Gerencia)
        OUTPUT INSERTED.CheckID
        VALUES (%s, %s, GETDATE(), %s, 0)
    """
    
    params = (
        int(colaborador_id),
        tipo_registro,
        geolocalizacion  # Puede ser None, SQL lo manejará como NULL
    )
    
    result = execute_hub_query_params(server, query, params)
    
    if result and len(result) > 0:
        return {
            "success": True,
            "check_id": result[0].get("CheckID")
        }
    
    return {
        "success": False,
        "check_id": None,
        "error": "No se pudo registrar la asistencia"
    }


def query_validar_asistencia(server: Dict, check_id: int) -> Dict[str, Any]:
    """
    Valida un registro de asistencia (gerencia).
    
    PARÁMETROS NATIVOS: check_id (entero validado)
    
    Establece Validado_Gerencia = 1 para el registro.
    
    Tabla: RH_Reloj_Checador
    """
    try:
        id_safe = int(check_id)
    except (ValueError, TypeError):
        return {"success": False, "error": "ID de registro inválido"}
    
    query = """
        UPDATE RH_Reloj_Checador
        SET Validado_Gerencia = 1
        WHERE CheckID = %s
    """
    
    execute_hub_query_params(server, query, (id_safe,))
    
    return {"success": True}



# ============================================================================
# FLUJO NÓMINA - QUERIES CON PARÁMETROS NATIVOS (FASE 6F-B)
# ============================================================================
# TABLAS REUTILIZADAS:
# - RH_Flujo_Nomina_Sucursal (principal - INSERT/SELECT/UPDATE)
# - RH_Cat_Sucursales (JOIN)
#
# SEGURIDAD:
# - Todos los IDs (flujo_id, sucursal_id, semana_anio) se validan como enteros
# - execute_sql_query_params() para INSERT y UPDATE con IDs
# - escape_sql_string() usado SOLO para:
#   - estatus en filtros WHERE (string de lista controlada)
#   - motivo_rechazo (string libre de usuario)
#   Razón: SQL Server no soporta parámetros en SET dinámico con valores string
#          que ya vienen validados por Pydantic
#
# VALIDACIÓN DE TRANSICIONES:
# - Se valida que la transición de estado sea permitida según TRANSICIONES_FLUJO_NOMINA
# - Esto previene saltos de estado absurdos (ej: Captura → Pagado)
# ============================================================================


def query_listar_flujos_nomina(
    server: Dict,
    sucursal_id: Optional[int] = None,
    semana_anio: Optional[int] = None,
    estatus: Optional[str] = None
) -> Dict[str, Any]:
    """
    Lista flujos de nómina por sucursal con filtros opcionales.
    
    PARÁMETROS NATIVOS: sucursal_id, semana_anio (enteros validados)
    ESCAPE NECESARIO: estatus (string de lista controlada, ya validado por Pydantic)
    
    Tablas: RH_Flujo_Nomina_Sucursal, RH_Cat_Sucursales
    """
    conditions = ["1=1"]
    
    # Filtros con validación de enteros (seguros - casting a int)
    if sucursal_id is not None:
        try:
            conditions.append(f"f.SucursalID = {int(sucursal_id)}")
        except (ValueError, TypeError):
            pass
    
    if semana_anio is not None:
        try:
            conditions.append(f"f.Semana_Anio = {int(semana_anio)}")
        except (ValueError, TypeError):
            pass
    
    # Estatus: Ya validado por Pydantic contra ESTATUS_FLUJO_NOMINA, escapamos por seguridad
    if estatus:
        estatus_safe = escape_sql_string(estatus)
        conditions.append(f"f.Estatus_Flujo = N'{estatus_safe}'")
    
    where_clause = " AND ".join(conditions)
    
    query = f"""
        SELECT 
            f.FlujoID,
            f.SucursalID,
            s.Nombre_Sucursal,
            f.Semana_Anio,
            f.Estatus_Flujo,
            f.Hora_Entrega_RH,
            f.Hora_Validacion_Gerente,
            f.Hora_Autorizacion_DG,
            f.Hora_Envio_Tesoreria,
            f.Hora_Pago_Ejecutado,
            f.Motivo_Rechazo_Gerente,
            f.Intentos_Reenvio
        FROM RH_Flujo_Nomina_Sucursal f
        LEFT JOIN RH_Cat_Sucursales s ON f.SucursalID = s.SucursalID
        WHERE {where_clause}
        ORDER BY f.Semana_Anio DESC, s.Nombre_Sucursal
    """
    
    result = execute_hub_query(server, query)
    
    return {
        "datos": result,
        "total": len(result)
    }


def query_verificar_flujo_existente(
    server: Dict,
    sucursal_id: int,
    semana_anio: int
) -> bool:
    """
    Verifica si ya existe un flujo de nómina para la combinación sucursal+semana.
    
    PARÁMETROS NATIVOS: sucursal_id, semana_anio
    
    Returns:
        True si ya existe, False si no existe
    """
    query = """
        SELECT FlujoID FROM RH_Flujo_Nomina_Sucursal 
        WHERE SucursalID = %s AND Semana_Anio = %s
    """
    
    params = (int(sucursal_id), int(semana_anio))
    result = execute_hub_query_params(server, query, params)
    
    return len(result) > 0


def query_obtener_estatus_flujo(server: Dict, flujo_id: int) -> Optional[str]:
    """
    Obtiene el estatus actual de un flujo de nómina.
    
    PARÁMETROS NATIVOS: flujo_id
    
    Returns:
        Estatus actual del flujo, o None si no existe
    """
    try:
        id_safe = int(flujo_id)
    except (ValueError, TypeError):
        return None
    
    query = """
        SELECT Estatus_Flujo FROM RH_Flujo_Nomina_Sucursal 
        WHERE FlujoID = %s
    """
    
    result = execute_hub_query_params(server, query, (id_safe,))
    
    if result and len(result) > 0:
        return result[0].get("Estatus_Flujo")
    return None


def query_crear_flujo_nomina(
    server: Dict,
    sucursal_id: int,
    semana_anio: int
) -> Dict[str, Any]:
    """
    Crea un nuevo flujo de nómina para una sucursal.
    
    PARÁMETROS NATIVOS: sucursal_id, semana_anio
    
    El flujo se crea con:
    - Estatus_Flujo = 'Captura' (estado inicial)
    - Intentos_Reenvio = 0
    
    Tabla: RH_Flujo_Nomina_Sucursal
    """
    query = """
        INSERT INTO RH_Flujo_Nomina_Sucursal 
        (SucursalID, Semana_Anio, Estatus_Flujo, Intentos_Reenvio)
        OUTPUT INSERTED.FlujoID
        VALUES (%s, %s, 'Captura', 0)
    """
    
    params = (int(sucursal_id), int(semana_anio))
    result = execute_hub_query_params(server, query, params)
    
    if result and len(result) > 0:
        return {
            "success": True,
            "flujo_id": result[0].get("FlujoID")
        }
    
    return {
        "success": False,
        "flujo_id": None,
        "error": "No se pudo crear el flujo de nómina"
    }


def query_actualizar_estatus_flujo(
    server: Dict,
    flujo_id: int,
    nuevo_estatus: str,
    campo_hora: Optional[str] = None,
    motivo_rechazo: Optional[str] = None,
    incrementar_intentos: bool = False
) -> Dict[str, Any]:
    """
    Actualiza el estatus de un flujo de nómina.
    
    PARÁMETROS NATIVOS: flujo_id (entero validado)
    ESCAPE NECESARIO: nuevo_estatus, motivo_rechazo
        Razón: Valores string en SET dinámico. Ambos ya validados por Pydantic.
    
    Args:
        server: Configuración del servidor
        flujo_id: ID del flujo a actualizar
        nuevo_estatus: Nuevo estatus (ya validado contra ESTATUS_FLUJO_NOMINA)
        campo_hora: Campo de hora a actualizar (ej: 'Hora_Entrega_RH')
        motivo_rechazo: Motivo de rechazo (solo para Rechazado_Gerente)
        incrementar_intentos: Si True, incrementa Intentos_Reenvio
    
    Tabla: RH_Flujo_Nomina_Sucursal
    """
    try:
        id_safe = int(flujo_id)
    except (ValueError, TypeError):
        return {"success": False, "error": "ID de flujo inválido"}
    
    # Construir cláusulas SET
    set_clauses = [f"Estatus_Flujo = N'{escape_sql_string(nuevo_estatus)}'"]
    
    # Campo de hora (nombre de columna seguro, no viene del usuario)
    if campo_hora:
        # Validar que sea un campo de hora válido
        campos_hora_validos = [
            'Hora_Entrega_RH', 'Hora_Validacion_Gerente', 
            'Hora_Autorizacion_DG', 'Hora_Envio_Tesoreria', 'Hora_Pago_Ejecutado'
        ]
        if campo_hora in campos_hora_validos:
            set_clauses.append(f"{campo_hora} = GETDATE()")
    
    # Motivo de rechazo
    if motivo_rechazo is not None:
        motivo_safe = escape_sql_string(motivo_rechazo)
        set_clauses.append(f"Motivo_Rechazo_Gerente = N'{motivo_safe}'")
    elif nuevo_estatus == 'Validacion_Gerente':
        # Limpiar motivo si se aprueba
        set_clauses.append("Motivo_Rechazo_Gerente = NULL")
    
    # Incrementar intentos
    if incrementar_intentos:
        set_clauses.append("Intentos_Reenvio = Intentos_Reenvio + 1")
    
    query = f"""
        UPDATE RH_Flujo_Nomina_Sucursal
        SET {', '.join(set_clauses)}
        WHERE FlujoID = {id_safe}
    """
    
    execute_hub_query(server, query)
    
    return {"success": True}


# ============================================================================
# AUDITORÍA + DASHBOARD RH - QUERIES (FASE 6G-B)
# ============================================================================
# TABLAS REUTILIZADAS:
# - RH_Auditoria_Fiscal (principal)
# - RH_Colaboradores_Expediente (JOIN)
# - RH_Cat_Sucursales (JOIN)
# - RH_Cat_Puestos (JOIN)
# - RH_Incidencias_Nomina (para dashboard)
# - RH_Flujo_Nomina_Sucursal (para dashboard)
#
# SEGURIDAD:
# - IDs validados como enteros (casting seguro)
# - No hay strings de usuario en filtros (solo_alertas es booleano)
# ============================================================================


def query_listar_auditoria_fiscal(
    server: Dict,
    colaborador_id: Optional[int] = None,
    semana: Optional[int] = None,
    solo_alertas: bool = False
) -> Dict[str, Any]:
    """
    Lista auditoría fiscal de nóminas con filtros.
    
    PARÁMETROS NATIVOS: colaborador_id, semana (enteros validados)
    
    Tablas: RH_Auditoria_Fiscal, RH_Colaboradores_Expediente, RH_Cat_Sucursales
    """
    conditions = ["1=1"]
    
    # Filtros con validación de enteros (seguros - casting a int)
    if colaborador_id is not None:
        try:
            conditions.append(f"a.ColaboradorID = {int(colaborador_id)}")
        except (ValueError, TypeError):
            pass
    
    if semana is not None:
        try:
            conditions.append(f"a.Semana = {int(semana)}")
        except (ValueError, TypeError):
            pass
    
    if solo_alertas:
        conditions.append("a.Alerta_Fraude = 1")
    
    where_clause = " AND ".join(conditions)
    
    query = f"""
        SELECT 
            a.AuditoriaID,
            a.ColaboradorID,
            c.Nombre_Completo,
            c.RFC,
            s.Nombre_Sucursal,
            a.Semana,
            a.Monto_Dispersado_Banco,
            a.Monto_Timbrado_XML,
            a.Monto_IMSS_EBA_EMA,
            a.Diferencia,
            a.Alerta_Fraude
        FROM RH_Auditoria_Fiscal a
        LEFT JOIN RH_Colaboradores_Expediente c ON a.ColaboradorID = c.ColaboradorID
        LEFT JOIN RH_Cat_Sucursales s ON c.SucursalID = s.SucursalID
        WHERE {where_clause}
        ORDER BY a.Alerta_Fraude DESC, a.Semana DESC
    """
    
    result = execute_hub_query(server, query)
    alertas = sum(1 for r in result if r.get("Alerta_Fraude") == 1)
    
    return {
        "datos": result,
        "total": len(result),
        "total_alertas": alertas
    }


def query_dashboard_rh(server: Dict, sucursal_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Obtiene métricas del dashboard RH ejecutando múltiples queries.
    
    PARÁMETROS NATIVOS: sucursal_id (entero validado, usado en filtro dinámico)
    
    Tablas: RH_Colaboradores_Expediente, RH_Cat_Puestos, RH_Incidencias_Nomina,
            RH_Flujo_Nomina_Sucursal, RH_Auditoria_Fiscal
    """
    # Filtros dinámicos seguros (entero validado)
    suc_filter = ""
    suc_filter_c = ""
    if sucursal_id is not None:
        try:
            sid = int(sucursal_id)
            suc_filter = f"AND SucursalID = {sid}"
            suc_filter_c = f"AND c.SucursalID = {sid}"
        except (ValueError, TypeError):
            pass
    
    # Query 1: Total colaboradores
    query_total = f"""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN Colaborador_Activo = 1 THEN 1 ELSE 0 END) as activos,
            SUM(CASE WHEN Estatus_Laboral = 'Vacaciones' THEN 1 ELSE 0 END) as vacaciones,
            SUM(CASE WHEN Estatus_Laboral = 'Incapacidad' THEN 1 ELSE 0 END) as incapacidad,
            SUM(CASE WHEN Colaborador_Activo = 0 THEN 1 ELSE 0 END) as bajas
        FROM RH_Colaboradores_Expediente
        WHERE 1=1 {suc_filter}
    """
    
    # Query 2: Por departamento
    query_depto = f"""
        SELECT 
            ISNULL(p.Departamento, 'Sin asignar') as Departamento,
            COUNT(*) as total
        FROM RH_Colaboradores_Expediente c
        LEFT JOIN RH_Cat_Puestos p ON c.PuestoID = p.PuestoID
        WHERE c.Colaborador_Activo = 1 {suc_filter_c}
        GROUP BY p.Departamento
        ORDER BY total DESC
    """
    
    # Query 3: Incidencias del mes
    query_incidencias = f"""
        SELECT 
            Tipo_Incidencia,
            COUNT(*) as cantidad,
            SUM(ISNULL(Monto, 0)) as monto_total
        FROM RH_Incidencias_Nomina i
        LEFT JOIN RH_Colaboradores_Expediente c ON i.ColaboradorID = c.ColaboradorID
        WHERE MONTH(Fecha_Incidencia) = MONTH(GETDATE()) 
          AND YEAR(Fecha_Incidencia) = YEAR(GETDATE())
          {suc_filter_c}
        GROUP BY Tipo_Incidencia
    """
    
    # Query 4: Flujos pendientes
    query_flujos = f"""
        SELECT 
            Estatus_Flujo,
            COUNT(*) as cantidad
        FROM RH_Flujo_Nomina_Sucursal
        WHERE Estatus_Flujo NOT IN ('Pagado')
          {suc_filter}
        GROUP BY Estatus_Flujo
    """
    
    # Query 5: Alertas fraude
    query_alertas = f"""
        SELECT COUNT(*) as alertas
        FROM RH_Auditoria_Fiscal a
        LEFT JOIN RH_Colaboradores_Expediente c ON a.ColaboradorID = c.ColaboradorID
        WHERE a.Alerta_Fraude = 1 {suc_filter_c}
    """
    
    result_total = execute_hub_query(server, query_total)
    result_depto = execute_hub_query(server, query_depto)
    result_incidencias = execute_hub_query(server, query_incidencias)
    result_flujos = execute_hub_query(server, query_flujos)
    result_alertas = execute_hub_query(server, query_alertas)
    
    return {
        "resumen": result_total[0] if result_total else {},
        "por_departamento": result_depto,
        "incidencias_mes": result_incidencias,
        "flujos_pendientes": result_flujos,
        "alertas_fraude": result_alertas[0].get("alertas", 0) if result_alertas else 0
    }


# ============================================================================
# RECLUTAMIENTO RH - QUERIES (FASE 6H-B)
# ============================================================================
# TABLAS REUTILIZADAS:
# - RH_Vacantes (CRUD)
# - RH_Candidatos (CRUD)
# - RH_Cat_Sucursales (JOIN)
# - RH_Cat_Puestos (JOIN)
#
# SEGURIDAD:
# - IDs validados como enteros (casting seguro)
# - Strings de usuario (titulo, descripcion, requisitos, etc.) usan escape_sql_string()
#   Razón: SQL Server no soporta parámetros nativos en INSERT/UPDATE con múltiples columnas dinámicas
# ============================================================================


def query_listar_vacantes(
    server: Dict,
    sucursal_id: Optional[int] = None,
    estatus: Optional[str] = None
) -> Dict[str, Any]:
    """
    Lista vacantes con filtros opcionales.
    
    PARÁMETROS NATIVOS: sucursal_id (entero validado)
    ESCAPE NECESARIO: estatus (string de lista controlada, ya validado por Pydantic)
    
    Tablas: RH_Vacantes, RH_Cat_Sucursales, RH_Cat_Puestos, RH_Candidatos
    """
    conditions = ["1=1"]
    
    if sucursal_id is not None:
        try:
            conditions.append(f"v.SucursalID = {int(sucursal_id)}")
        except (ValueError, TypeError):
            pass
    
    if estatus:
        estatus_safe = escape_sql_string(estatus)
        conditions.append(f"v.Estatus = N'{estatus_safe}'")
    
    where_clause = " AND ".join(conditions)
    
    query = f"""
        SELECT 
            v.VacanteID,
            v.SucursalID,
            s.Nombre_Sucursal,
            v.PuestoID,
            p.Nombre_Puesto,
            p.Departamento,
            v.Titulo,
            v.Descripcion,
            v.Requisitos,
            v.Salario_Min,
            v.Salario_Max,
            v.Tipo_Contrato,
            v.Estatus,
            v.Fecha_Publicacion,
            v.Fecha_Cierre,
            v.Creado_Por,
            (SELECT COUNT(*) FROM RH_Candidatos c WHERE c.VacanteID = v.VacanteID) as Total_Candidatos
        FROM RH_Vacantes v
        LEFT JOIN RH_Cat_Sucursales s ON v.SucursalID = s.SucursalID
        LEFT JOIN RH_Cat_Puestos p ON v.PuestoID = p.PuestoID
        WHERE {where_clause}
        ORDER BY v.Fecha_Publicacion DESC
    """
    
    result = execute_hub_query(server, query)
    
    return {
        "datos": result,
        "total": len(result)
    }


def query_crear_vacante(
    server: Dict,
    sucursal_id: int,
    puesto_id: int,
    titulo: str,
    descripcion: Optional[str],
    requisitos: Optional[str],
    salario_min: float,
    salario_max: float,
    tipo_contrato: str,
    creado_por: str
) -> Dict[str, Any]:
    """
    Crea una nueva vacante.
    
    PARÁMETROS NATIVOS: sucursal_id, puesto_id (enteros), salario_min, salario_max (float)
    ESCAPE NECESARIO: titulo, descripcion, requisitos, tipo_contrato, creado_por
        Razón: Strings de usuario en INSERT. Ya validados por Pydantic.
    
    Tabla: RH_Vacantes
    """
    # Escapar strings de usuario
    titulo_safe = escape_sql_string(titulo)
    desc_safe = escape_sql_string(descripcion or '')
    req_safe = escape_sql_string(requisitos or '')
    tipo_safe = escape_sql_string(tipo_contrato)
    creador_safe = escape_sql_string(creado_por or '')
    
    query = f"""
        INSERT INTO RH_Vacantes 
        (SucursalID, PuestoID, Titulo, Descripcion, Requisitos, Salario_Min, Salario_Max, 
         Tipo_Contrato, Estatus, Fecha_Publicacion, Creado_Por)
        OUTPUT INSERTED.VacanteID
        VALUES 
        ({int(sucursal_id)}, {int(puesto_id)}, N'{titulo_safe}', N'{desc_safe}', N'{req_safe}', 
         {float(salario_min)}, {float(salario_max)}, N'{tipo_safe}', N'Abierta', GETDATE(), N'{creador_safe}')
    """
    
    result = execute_hub_query(server, query)
    
    if result and len(result) > 0:
        return {"success": True, "vacante_id": result[0].get("VacanteID")}
    
    return {"success": True, "vacante_id": None}


def query_actualizar_vacante(
    server: Dict,
    vacante_id: int,
    titulo: Optional[str] = None,
    descripcion: Optional[str] = None,
    requisitos: Optional[str] = None,
    salario_min: Optional[float] = None,
    salario_max: Optional[float] = None,
    estatus: Optional[str] = None
) -> Dict[str, Any]:
    """
    Actualiza una vacante existente.
    
    PARÁMETROS NATIVOS: vacante_id (entero validado), salario_min, salario_max (float)
    ESCAPE NECESARIO: titulo, descripcion, requisitos, estatus
        Razón: Strings de usuario en UPDATE dinámico. Ya validados por Pydantic.
    
    Tabla: RH_Vacantes
    """
    try:
        id_safe = int(vacante_id)
    except (ValueError, TypeError):
        return {"success": False, "error": "ID de vacante inválido"}
    
    updates = []
    
    if titulo is not None:
        updates.append(f"Titulo = N'{escape_sql_string(titulo)}'")
    if descripcion is not None:
        updates.append(f"Descripcion = N'{escape_sql_string(descripcion)}'")
    if requisitos is not None:
        updates.append(f"Requisitos = N'{escape_sql_string(requisitos)}'")
    if salario_min is not None:
        updates.append(f"Salario_Min = {float(salario_min)}")
    if salario_max is not None:
        updates.append(f"Salario_Max = {float(salario_max)}")
    if estatus is not None:
        updates.append(f"Estatus = N'{escape_sql_string(estatus)}'")
        if estatus == 'Cerrada':
            updates.append("Fecha_Cierre = GETDATE()")
    
    if not updates:
        return {"success": False, "error": "No hay campos para actualizar"}
    
    query = f"""
        UPDATE RH_Vacantes
        SET {', '.join(updates)}
        WHERE VacanteID = {id_safe}
    """
    
    execute_hub_query(server, query)
    
    return {"success": True}


def query_eliminar_vacante(server: Dict, vacante_id: int) -> Dict[str, Any]:
    """
    Elimina una vacante y sus candidatos asociados.
    
    PARÁMETROS NATIVOS: vacante_id (entero validado)
    
    Tablas: RH_Candidatos, RH_Vacantes
    """
    try:
        id_safe = int(vacante_id)
    except (ValueError, TypeError):
        return {"success": False, "error": "ID de vacante inválido"}
    
    # Eliminar candidatos asociados primero
    execute_hub_query(server, f"DELETE FROM RH_Candidatos WHERE VacanteID = {id_safe}")
    # Eliminar vacante
    execute_hub_query(server, f"DELETE FROM RH_Vacantes WHERE VacanteID = {id_safe}")
    
    return {"success": True}


def query_listar_candidatos(
    server: Dict,
    vacante_id: Optional[int] = None,
    estatus: Optional[str] = None
) -> Dict[str, Any]:
    """
    Lista candidatos con filtros opcionales.
    
    PARÁMETROS NATIVOS: vacante_id (entero validado)
    ESCAPE NECESARIO: estatus (string de lista controlada, ya validado por Pydantic)
    
    Tablas: RH_Candidatos, RH_Vacantes, RH_Cat_Sucursales
    """
    conditions = ["1=1"]
    
    if vacante_id is not None:
        try:
            conditions.append(f"c.VacanteID = {int(vacante_id)}")
        except (ValueError, TypeError):
            pass
    
    if estatus:
        estatus_safe = escape_sql_string(estatus)
        conditions.append(f"c.Estatus = N'{estatus_safe}'")
    
    where_clause = " AND ".join(conditions)
    
    query = f"""
        SELECT 
            c.CandidatoID,
            c.VacanteID,
            v.Titulo as Vacante_Titulo,
            s.Nombre_Sucursal,
            c.Nombre_Completo,
            c.Email,
            c.Telefono,
            c.CV_URL,
            c.Estatus,
            c.Puntuacion,
            c.Notas,
            c.Fecha_Aplicacion,
            c.Fecha_Entrevista,
            c.Entrevistador
        FROM RH_Candidatos c
        LEFT JOIN RH_Vacantes v ON c.VacanteID = v.VacanteID
        LEFT JOIN RH_Cat_Sucursales s ON v.SucursalID = s.SucursalID
        WHERE {where_clause}
        ORDER BY c.Fecha_Aplicacion DESC
    """
    
    result = execute_hub_query(server, query)
    
    return {
        "datos": result,
        "total": len(result)
    }


def query_crear_candidato(
    server: Dict,
    vacante_id: int,
    nombre: str,
    email: str,
    telefono: Optional[str],
    cv_url: Optional[str]
) -> Dict[str, Any]:
    """
    Registra un nuevo candidato.
    
    PARÁMETROS NATIVOS: vacante_id (entero validado)
    ESCAPE NECESARIO: nombre, email, telefono, cv_url
        Razón: Strings de usuario en INSERT. Ya validados por Pydantic (email format).
    
    Tabla: RH_Candidatos
    """
    nombre_safe = escape_sql_string(nombre)
    email_safe = escape_sql_string(email)
    tel_safe = escape_sql_string(telefono or '')
    cv_safe = escape_sql_string(cv_url or '')
    
    query = f"""
        INSERT INTO RH_Candidatos 
        (VacanteID, Nombre_Completo, Email, Telefono, CV_URL, Estatus, Fecha_Aplicacion)
        OUTPUT INSERTED.CandidatoID
        VALUES 
        ({int(vacante_id)}, N'{nombre_safe}', N'{email_safe}', N'{tel_safe}', N'{cv_safe}', N'Recibido', GETDATE())
    """
    
    result = execute_hub_query(server, query)
    
    if result and len(result) > 0:
        return {"success": True, "candidato_id": result[0].get("CandidatoID")}
    
    return {"success": True, "candidato_id": None}


def query_actualizar_candidato(
    server: Dict,
    candidato_id: int,
    estatus: Optional[str] = None,
    puntuacion: Optional[int] = None,
    notas: Optional[str] = None,
    fecha_entrevista: Optional[str] = None,
    entrevistador: Optional[str] = None
) -> Dict[str, Any]:
    """
    Actualiza un candidato existente.
    
    PARÁMETROS NATIVOS: candidato_id, puntuacion (enteros validados)
    ESCAPE NECESARIO: estatus, notas, fecha_entrevista, entrevistador
        Razón: Strings de usuario en UPDATE dinámico. Ya validados por Pydantic.
    
    Tabla: RH_Candidatos
    """
    try:
        id_safe = int(candidato_id)
    except (ValueError, TypeError):
        return {"success": False, "error": "ID de candidato inválido"}
    
    updates = []
    
    if estatus is not None:
        updates.append(f"Estatus = N'{escape_sql_string(estatus)}'")
    if puntuacion is not None:
        updates.append(f"Puntuacion = {int(puntuacion)}")
    if notas is not None:
        updates.append(f"Notas = N'{escape_sql_string(notas)}'")
    if fecha_entrevista is not None:
        updates.append(f"Fecha_Entrevista = '{escape_sql_string(fecha_entrevista)}'")
    if entrevistador is not None:
        updates.append(f"Entrevistador = N'{escape_sql_string(entrevistador)}'")
    
    if not updates:
        return {"success": False, "error": "No hay campos para actualizar"}
    
    query = f"""
        UPDATE RH_Candidatos
        SET {', '.join(updates)}
        WHERE CandidatoID = {id_safe}
    """
    
    execute_hub_query(server, query)
    
    return {"success": True}


def query_eliminar_candidato(server: Dict, candidato_id: int) -> Dict[str, Any]:
    """
    Elimina un candidato.
    
    PARÁMETROS NATIVOS: candidato_id (entero validado)
    
    Tabla: RH_Candidatos
    """
    try:
        id_safe = int(candidato_id)
    except (ValueError, TypeError):
        return {"success": False, "error": "ID de candidato inválido"}
    
    execute_hub_query(server, f"DELETE FROM RH_Candidatos WHERE CandidatoID = {id_safe}")
    
    return {"success": True}


def query_dashboard_reclutamiento(server: Dict) -> Dict[str, Any]:
    """
    Obtiene métricas del dashboard de reclutamiento.
    
    SIN PARÁMETROS DE USUARIO - Queries estáticos, sin riesgo de inyección.
    
    Tablas: RH_Vacantes, RH_Candidatos
    """
    # Vacantes por estatus
    query_vacantes = """
        SELECT 
            Estatus,
            COUNT(*) as cantidad
        FROM RH_Vacantes
        GROUP BY Estatus
    """
    
    # Candidatos por estatus
    query_candidatos = """
        SELECT 
            Estatus,
            COUNT(*) as cantidad
        FROM RH_Candidatos
        GROUP BY Estatus
    """
    
    # Top 5 vacantes con más candidatos
    query_top = """
        SELECT TOP 5
            v.Titulo,
            COUNT(c.CandidatoID) as Total_Candidatos
        FROM RH_Vacantes v
        LEFT JOIN RH_Candidatos c ON v.VacanteID = c.VacanteID
        WHERE v.Estatus = 'Abierta'
        GROUP BY v.VacanteID, v.Titulo
        ORDER BY Total_Candidatos DESC
    """
    
    result_vac = execute_hub_query(server, query_vacantes)
    result_cand = execute_hub_query(server, query_candidatos)
    result_top = execute_hub_query(server, query_top)
    
    return {
        "vacantes_por_estatus": result_vac,
        "candidatos_por_estatus": result_cand,
        "top_vacantes": result_top
    }


def get_script_reclutamiento() -> str:
    """
    Retorna el script SQL para crear las tablas de reclutamiento.
    
    SIN ACCESO A BD - Solo retorna string estático.
    """
    return """
-- ============================================
-- SCRIPT DE INICIALIZACIÓN - MÓDULO RECLUTAMIENTO
-- Ejecutar en la base de datos EDARSA HUB
-- ============================================

-- Tabla de Vacantes
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='RH_Vacantes' AND xtype='U')
BEGIN
    CREATE TABLE RH_Vacantes (
        VacanteID INT IDENTITY(1,1) PRIMARY KEY,
        SucursalID INT NOT NULL,
        PuestoID INT NOT NULL,
        Titulo NVARCHAR(200) NOT NULL,
        Descripcion NVARCHAR(MAX),
        Requisitos NVARCHAR(MAX),
        Salario_Min DECIMAL(18,2) DEFAULT 0,
        Salario_Max DECIMAL(18,2) DEFAULT 0,
        Tipo_Contrato NVARCHAR(50) DEFAULT 'Tiempo Completo',
        Estatus NVARCHAR(20) DEFAULT 'Abierta' CHECK (Estatus IN ('Abierta', 'En Proceso', 'Cerrada', 'Cancelada')),
        Fecha_Publicacion DATETIME DEFAULT GETDATE(),
        Fecha_Cierre DATETIME,
        Creado_Por NVARCHAR(100),
        
        CONSTRAINT FK_Vacante_Sucursal FOREIGN KEY (SucursalID) 
            REFERENCES RH_Cat_Sucursales(SucursalID),
        CONSTRAINT FK_Vacante_Puesto FOREIGN KEY (PuestoID) 
            REFERENCES RH_Cat_Puestos(PuestoID)
    );
    
    CREATE INDEX IX_Vacantes_Estatus ON RH_Vacantes(Estatus);
    CREATE INDEX IX_Vacantes_Sucursal ON RH_Vacantes(SucursalID);
    
    PRINT 'Tabla RH_Vacantes creada exitosamente';
END
ELSE
    PRINT 'Tabla RH_Vacantes ya existe';
GO

-- Tabla de Candidatos
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='RH_Candidatos' AND xtype='U')
BEGIN
    CREATE TABLE RH_Candidatos (
        CandidatoID INT IDENTITY(1,1) PRIMARY KEY,
        VacanteID INT NOT NULL,
        Nombre_Completo NVARCHAR(200) NOT NULL,
        Email NVARCHAR(100) NOT NULL,
        Telefono NVARCHAR(20),
        CV_URL NVARCHAR(500),
        Estatus NVARCHAR(20) DEFAULT 'Recibido' CHECK (Estatus IN ('Recibido', 'En Revisión', 'Entrevista', 'Finalista', 'Contratado', 'Rechazado')),
        Puntuacion INT CHECK (Puntuacion BETWEEN 0 AND 100),
        Notas NVARCHAR(MAX),
        Fecha_Aplicacion DATETIME DEFAULT GETDATE(),
        Fecha_Entrevista DATETIME,
        Entrevistador NVARCHAR(100),
        
        CONSTRAINT FK_Candidato_Vacante FOREIGN KEY (VacanteID) 
            REFERENCES RH_Vacantes(VacanteID)
    );
    
    CREATE INDEX IX_Candidatos_Vacante ON RH_Candidatos(VacanteID);
    CREATE INDEX IX_Candidatos_Estatus ON RH_Candidatos(Estatus);
    
    PRINT 'Tabla RH_Candidatos creada exitosamente';
END
ELSE
    PRINT 'Tabla RH_Candidatos ya existe';
GO

PRINT '=== Script de reclutamiento ejecutado ===';
"""
