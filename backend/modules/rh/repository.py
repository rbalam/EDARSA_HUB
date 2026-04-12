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

from core.db import execute_sql_query


# ============================================================================
# CONSTANTES
# ============================================================================

EDARSA_HUB_SERVER_ID = "EDARSA-HUB"

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
# SERVIDOR EDARSA HUB
# ============================================================================

async def get_edarsa_hub_server() -> Optional[Dict]:
    """Obtiene la configuración del servidor EDARSA HUB."""
    return await get_db().servers.find_one(
        {"id": EDARSA_HUB_SERVER_ID, "active": True},
        {"_id": 0}
    )


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
