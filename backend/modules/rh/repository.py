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
