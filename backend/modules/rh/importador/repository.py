from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - Repository de Importación RH
=========================================
Acceso a datos para el proceso de importación controlada.

TABLAS GESTIONADAS:
- RH_Importacion_Staging: Registros pendientes de validación/aprobación
- RH_Importacion_Bitacora: Historial de importaciones ejecutadas

SEGURIDAD:
- Queries parametrizados para prevenir SQL Injection
- Escape de strings donde el driver no soporte parámetros
"""

from typing import Dict, List, Optional, Any
import logging
import json
from datetime import datetime

from core.db import execute_sql_query
from core.config.edarsahub_config import get_edarsahub_sql_config

# ============================================================================
# CONFIGURACION CANONICA EDARSAHUB
# ============================================================================

_edarsa_cfg = get_edarsahub_sql_config()

EDARSAHUB_CONFIG = {
    'host': _edarsa_cfg.host,
    'port': _edarsa_cfg.port,
    'database': _edarsa_cfg.database,
    'username': _edarsa_cfg.user,
    'password': _edarsa_cfg.password,
}

_server_cache = None


def init_importador_repository(database) -> None:
    """Compatibilidad de inicializacion; el importador ya no depende de MongoDB."""
    logging.info("Importador Repository inicializado con configuracion SQL-first")


# ============================================================================
# UTILIDADES
# ============================================================================

def escape_sql_string(value: str) -> str:
    """Escapa una cadena para uso seguro en SQL Server."""
    if value is None:
        return ""
    return str(value).replace("'", "''")


async def get_edarsa_hub_server() -> Optional[Dict]:
    """Obtiene la configuracion SQL-first canonica de EDARSAHUB."""
    global _server_cache
    if _server_cache is not None:
        return _server_cache

    if not EDARSAHUB_CONFIG.get('host') or not EDARSAHUB_CONFIG.get('database'):
        logging.error("EDARSAHUB_CONFIG incompleto: falta host o database")
        return None

    _server_cache = EDARSAHUB_CONFIG
    return _server_cache


def execute_hub_query(server: Dict, query: str) -> List[Dict]:
    """Ejecuta una query en el servidor EDARSA HUB."""
    return execute_sql_query(
        server['host'],
        server['port'],
        server['database'],
        server['username'],
        server['password'],
        query
    )


# ============================================================================
# SCRIPTS DDL - CREACIÓN DE TABLAS
# ============================================================================

SCRIPT_CREAR_STAGING = """
-- ============================================================================
-- TABLA: RH_Importacion_Staging
-- Propósito: Almacena registros de importación pendientes de validación/aprobación
-- Autor: EDARSA HUB - Arquitecto de Software
-- Fecha: Diciembre 2025
-- ============================================================================

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'RH_Importacion_Staging')
BEGIN
    CREATE TABLE RH_Importacion_Staging (
        -- PK
        StagingID INT IDENTITY(1,1) PRIMARY KEY,
        
        -- Datos del empleado (campos principales)
        Nombre_Completo NVARCHAR(200) NOT NULL,
        CURP CHAR(18) NULL,
        RFC VARCHAR(13) NULL,
        CLABE_Bancaria CHAR(18) NULL,
        Numero_Empleado_Externo VARCHAR(50) NULL,
        
        -- Datos de catálogo (texto original + ID resuelto)
        Sucursal_Nombre NVARCHAR(100) NULL,
        SucursalID INT NULL,
        Puesto_Nombre NVARCHAR(100) NULL,
        PuestoID INT NULL,
        Area_Departamento NVARCHAR(100) NULL,
        
        -- Datos adicionales del origen
        Sexo CHAR(1) NULL,
        Edad INT NULL,
        Antiguedad NVARCHAR(50) NULL,
        Sueldo_Diario DECIMAL(10,2) NULL,
        Metodo_Pago NVARCHAR(50) NULL,
        
        -- TRAZABILIDAD OBLIGATORIA (metadatos de importación)
        Fuente VARCHAR(50) NOT NULL,              -- 'Excel_CF', 'MPro_Origen', 'MPro_QRO'
        Archivo_Origen NVARCHAR(255) NULL,        -- Nombre del archivo/query
        Linea_Origen INT NULL,                    -- Línea en Excel o ID en BD origen
        Fecha_Importacion DATETIME DEFAULT GETDATE(),
        Usuario_Importador NVARCHAR(100) NULL,
        
        -- Estado del procesamiento
        Estado VARCHAR(20) DEFAULT 'Pendiente',   -- Pendiente, Validado, Aprobado, Procesado, Error, Rechazado
        Clasificacion VARCHAR(30) NULL,           -- nuevo, actualizar, duplicado_probable, incompleto, rechazado
        Nivel_Confianza VARCHAR(20) NULL,         -- alta, media, baja, muy_baja, revision
        Accion_Realizada VARCHAR(20) NULL,        -- INSERT, UPDATE, SKIP, ERROR
        
        -- Referencias a registros existentes
        ColaboradorID_Destino INT NULL,           -- FK al registro creado/actualizado
        ColaboradorID_Match INT NULL,             -- FK al posible duplicado encontrado
        
        -- Resultado y observaciones
        Mensaje_Error NVARCHAR(500) NULL,
        Observaciones NVARCHAR(MAX) NULL,
        
        -- Auditoría de aprobación
        Usuario_Aprobador NVARCHAR(100) NULL,
        Fecha_Aprobacion DATETIME NULL,
        Fecha_Procesamiento DATETIME NULL,
        
        -- Índices para deduplicación y búsqueda rápida
        INDEX IX_Staging_CURP NONCLUSTERED (CURP),
        INDEX IX_Staging_RFC NONCLUSTERED (RFC),
        INDEX IX_Staging_NumEmpleado NONCLUSTERED (Numero_Empleado_Externo),
        INDEX IX_Staging_Estado NONCLUSTERED (Estado),
        INDEX IX_Staging_Clasificacion NONCLUSTERED (Clasificacion),
        INDEX IX_Staging_Fuente NONCLUSTERED (Fuente),
        INDEX IX_Staging_Fecha NONCLUSTERED (Fecha_Importacion DESC)
    );
    
    PRINT 'Tabla RH_Importacion_Staging creada exitosamente';
END
ELSE
BEGIN
    PRINT 'Tabla RH_Importacion_Staging ya existe';
END
"""

SCRIPT_CREAR_BITACORA = """
-- ============================================================================
-- TABLA: RH_Importacion_Bitacora
-- Propósito: Historial de importaciones ejecutadas con métricas y trazabilidad
-- Autor: EDARSA HUB - Arquitecto de Software
-- Fecha: Diciembre 2025
-- ============================================================================

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'RH_Importacion_Bitacora')
BEGIN
    CREATE TABLE RH_Importacion_Bitacora (
        -- PK
        BitacoraID INT IDENTITY(1,1) PRIMARY KEY,
        
        -- Identificación de la importación
        Fecha_Ejecucion DATETIME DEFAULT GETDATE(),
        Fuente VARCHAR(50) NOT NULL,
        Archivo_Origen NVARCHAR(255) NULL,
        
        -- Métricas de resultado
        Total_Registros_Leidos INT DEFAULT 0,
        Total_Insertados INT DEFAULT 0,
        Total_Actualizados INT DEFAULT 0,
        Total_Duplicados_Omitidos INT DEFAULT 0,
        Total_Incompletos INT DEFAULT 0,
        Total_Errores INT DEFAULT 0,
        
        -- Auditoría
        Usuario_Ejecutor NVARCHAR(100) NULL,
        Duracion_Segundos INT NULL,
        Estado VARCHAR(20) DEFAULT 'En Proceso',  -- En Proceso, Completado, Parcial, Fallido
        
        -- Detalle adicional (JSON para flexibilidad)
        Detalle_JSON NVARCHAR(MAX) NULL,
        
        -- Índices
        INDEX IX_Bitacora_Fecha NONCLUSTERED (Fecha_Ejecucion DESC),
        INDEX IX_Bitacora_Fuente NONCLUSTERED (Fuente),
        INDEX IX_Bitacora_Estado NONCLUSTERED (Estado)
    );
    
    PRINT 'Tabla RH_Importacion_Bitacora creada exitosamente';
END
ELSE
BEGIN
    PRINT 'Tabla RH_Importacion_Bitacora ya existe';
END
"""


async def crear_tablas_importacion() -> Dict[str, Any]:
    """
    Crea las tablas de staging y bitácora si no existen.
    
    Returns:
        Dict con resultado de creación de cada tabla
    """
    server = await get_edarsa_hub_server()
    if not server:
        return {"error": "Servidor EDARSA HUB no disponible", "success": False}
    
    resultados = {
        "staging": {"creada": False, "mensaje": ""},
        "bitacora": {"creada": False, "mensaje": ""},
        "success": True
    }
    
    try:
        # Crear tabla staging
        execute_hub_query(server, SCRIPT_CREAR_STAGING)
        resultados["staging"]["creada"] = True
        resultados["staging"]["mensaje"] = "Tabla RH_Importacion_Staging lista"
    except Exception as e:
        resultados["staging"]["mensaje"] = f"Error: {str(e)}"
        resultados["success"] = False
    
    try:
        # Crear tabla bitácora
        execute_hub_query(server, SCRIPT_CREAR_BITACORA)
        resultados["bitacora"]["creada"] = True
        resultados["bitacora"]["mensaje"] = "Tabla RH_Importacion_Bitacora lista"
    except Exception as e:
        resultados["bitacora"]["mensaje"] = f"Error: {str(e)}"
        resultados["success"] = False
    
    return resultados


# ============================================================================
# QUERIES DE STAGING
# ============================================================================

async def insertar_staging(
    server: Dict,
    registro: Dict[str, Any],
    usuario: str
) -> Dict[str, Any]:
    """
    Inserta un registro en staging.
    
    TRAZABILIDAD: Todos los campos de metadatos son obligatorios.
    """
    # Escapar todos los valores de texto
    nombre = escape_sql_string(registro.get('nombre_completo', ''))
    curp = escape_sql_string(registro.get('curp') or '')
    rfc = escape_sql_string(registro.get('rfc') or '')
    clabe = escape_sql_string(registro.get('clabe_bancaria') or '')
    num_emp = escape_sql_string(registro.get('numero_empleado_externo') or '')
    suc_nombre = escape_sql_string(registro.get('sucursal_nombre') or '')
    puesto_nombre = escape_sql_string(registro.get('puesto_nombre') or '')
    area = escape_sql_string(registro.get('area_departamento') or '')
    sexo = escape_sql_string(registro.get('sexo') or '')
    antiguedad = escape_sql_string(registro.get('antiguedad') or '')
    metodo_pago = escape_sql_string(registro.get('metodo_pago') or '')
    fuente = escape_sql_string(registro.get('fuente', 'Desconocido'))
    archivo = escape_sql_string(registro.get('archivo_origen') or '')
    usuario_safe = escape_sql_string(usuario)
    
    # Valores numéricos (validados)
    suc_id = int(registro['sucursal_id']) if registro.get('sucursal_id') else 'NULL'
    puesto_id = int(registro['puesto_id']) if registro.get('puesto_id') else 'NULL'
    edad = int(registro['edad']) if registro.get('edad') else 'NULL'
    linea = int(registro['linea_origen']) if registro.get('linea_origen') else 'NULL'
    sueldo = float(registro['sueldo_diario']) if registro.get('sueldo_diario') else 'NULL'
    
    query = f"""
        INSERT INTO RH_Importacion_Staging (
            Nombre_Completo, CURP, RFC, CLABE_Bancaria, Numero_Empleado_Externo,
            Sucursal_Nombre, SucursalID, Puesto_Nombre, PuestoID, Area_Departamento,
            Sexo, Edad, Antiguedad, Sueldo_Diario, Metodo_Pago,
            Fuente, Archivo_Origen, Linea_Origen, Usuario_Importador,
            Estado, Fecha_Importacion
        )
        OUTPUT INSERTED.StagingID
        VALUES (
            N'{nombre}',
            {f"'{curp}'" if curp else 'NULL'},
            {f"'{rfc}'" if rfc else 'NULL'},
            {f"'{clabe}'" if clabe else 'NULL'},
            {f"'{num_emp}'" if num_emp else 'NULL'},
            {f"N'{suc_nombre}'" if suc_nombre else 'NULL'},
            {suc_id},
            {f"N'{puesto_nombre}'" if puesto_nombre else 'NULL'},
            {puesto_id},
            {f"N'{area}'" if area else 'NULL'},
            {f"'{sexo}'" if sexo else 'NULL'},
            {edad},
            {f"N'{antiguedad}'" if antiguedad else 'NULL'},
            {sueldo},
            {f"N'{metodo_pago}'" if metodo_pago else 'NULL'},
            '{fuente}',
            {f"N'{archivo}'" if archivo else 'NULL'},
            {linea},
            N'{usuario_safe}',
            'Pendiente',
            GETDATE()
        )
    """
    
    try:
        result = execute_hub_query(server, query)
        if result and len(result) > 0:
            return {"success": True, "staging_id": result[0].get("StagingID")}
        return {"success": False, "error": "No se obtuvo ID de staging"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def listar_staging(
    server: Dict,
    filtros: Optional[Dict] = None,
    limit: int = 100,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Lista registros en staging con filtros opcionales.
    """
    where_clauses = ["1=1"]
    
    if filtros:
        if filtros.get('estado'):
            estado = escape_sql_string(filtros['estado'])
            where_clauses.append(f"Estado = '{estado}'")
        if filtros.get('clasificacion'):
            clasificacion = escape_sql_string(filtros['clasificacion'])
            where_clauses.append(f"Clasificacion = '{clasificacion}'")
        if filtros.get('fuente'):
            fuente = escape_sql_string(filtros['fuente'])
            where_clauses.append(f"Fuente = '{fuente}'")
        if filtros.get('solo_pendientes'):
            where_clauses.append("Estado IN ('Pendiente', 'Validado')")
    
    where_sql = " AND ".join(where_clauses)
    
    query = f"""
        SELECT 
            StagingID as staging_id,
            Nombre_Completo as Nombre_Completo,
            CURP as curp,
            RFC as RFC,
            CLABE_Bancaria as clabe_bancaria,
            Numero_Empleado_Externo as Numero_Empleado_Externo,
            Sucursal_Nombre as Sucursal_Nombre,
            SucursalID as SucursalID,
            Puesto_Nombre as Puesto_Nombre,
            PuestoID as puesto_id,
            Area_Departamento as Area_Departamento,
            Sexo as sexo,
            Edad as Edad,
            Antiguedad as Antiguedad,
            Sueldo_Diario as Sueldo_Diario,
            Metodo_Pago as Metodo_Pago,
            Fuente as Fuente,
            Archivo_Origen as Archivo_Origen,
            Linea_Origen as Linea_Origen,
            Fecha_Importacion as Fecha_Importacion,
            Usuario_Importador as Usuario_Importador,
            Estado as Estado,
            Clasificacion as Clasificacion,
            Nivel_Confianza as Nivel_Confianza,
            Accion_Realizada as Accion_Realizada,
            ColaboradorID_Destino as colaborador_id_destino,
            ColaboradorID_Match as colaborador_id_match,
            Mensaje_Error as Mensaje_Error,
            Observaciones as Observaciones
        FROM RH_Importacion_Staging
        WHERE {where_sql}
        ORDER BY Fecha_Importacion DESC
        OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
    """
    
    # Query para contar total
    count_query = f"""
        SELECT COUNT(*) as total FROM RH_Importacion_Staging WHERE {where_sql}
    """
    
    try:
        datos = execute_hub_query(server, query)
        count_result = execute_hub_query(server, count_query)
        total = count_result[0]['total'] if count_result else 0
        
        return {
            "datos": datos,
            "total": total,
            "limit": limit,
            "offset": offset,
            "success": True
        }
    except Exception as e:
        return {"datos": [], "total": 0, "error": str(e), "success": False}


async def actualizar_estado_staging(
    server: Dict,
    staging_id: int,
    updates: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Actualiza el estado y clasificación de un registro en staging.
    """
    try:
        id_safe = int(staging_id)
    except (ValueError, TypeError):
        return {"success": False, "error": "ID de staging inválido"}
    
    set_clauses = []
    
    # Campos de texto
    campos_texto = ['estado', 'clasificacion', 'nivel_confianza', 'accion_realizada', 
                    'mensaje_error', 'observaciones', 'usuario_aprobador']
    for campo in campos_texto:
        if campo in updates and updates[campo] is not None:
            val = escape_sql_string(str(updates[campo]))
            # Mapeo de nombres Python a SQL
            col_map = {
                'estado': 'Estado',
                'clasificacion': 'Clasificacion',
                'nivel_confianza': 'Nivel_Confianza',
                'accion_realizada': 'Accion_Realizada',
                'mensaje_error': 'Mensaje_Error',
                'observaciones': 'Observaciones',
                'usuario_aprobador': 'Usuario_Aprobador'
            }
            set_clauses.append(f"{col_map[campo]} = N'{val}'")
    
    # Campos enteros
    campos_int = ['colaborador_id_destino', 'colaborador_id_match', 'sucursal_id', 'puesto_id']
    for campo in campos_int:
        if campo in updates and updates[campo] is not None:
            col_map = {
                'colaborador_id_destino': 'ColaboradorID_Destino',
                'colaborador_id_match': 'ColaboradorID_Match',
                'sucursal_id': 'SucursalID',
                'puesto_id': 'PuestoID'
            }
            try:
                set_clauses.append(f"{col_map[campo]} = {int(updates[campo])}")
            except (ValueError, TypeError):
                pass
    
    # Fechas automáticas según estado
    if updates.get('estado') == 'Aprobado':
        set_clauses.append("Fecha_Aprobacion = GETDATE()")
    if updates.get('estado') == 'Procesado':
        set_clauses.append("Fecha_Procesamiento = GETDATE()")
    
    if not set_clauses:
        return {"success": False, "error": "No hay campos para actualizar"}
    
    query = f"""
        UPDATE RH_Importacion_Staging
        SET {', '.join(set_clauses)}
        WHERE StagingID = {id_safe}
    """
    
    try:
        execute_hub_query(server, query)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# QUERIES DE BITÁCORA
# ============================================================================

async def insertar_bitacora(
    server: Dict,
    datos: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Inserta un registro en la bitácora de importaciones.
    """
    fuente = escape_sql_string(datos.get('fuente', 'Desconocido'))
    archivo = escape_sql_string(datos.get('archivo_origen') or '')
    usuario = escape_sql_string(datos.get('usuario_ejecutor') or '')
    estado = escape_sql_string(datos.get('estado', 'En Proceso'))
    
    # JSON para detalle
    detalle = datos.get('detalle_json')
    detalle_str = escape_sql_string(json.dumps(detalle)) if detalle else ''
    
    query = f"""
        INSERT INTO RH_Importacion_Bitacora (
            Fuente, Archivo_Origen,
            Total_Registros_Leidos, Total_Insertados, Total_Actualizados,
            Total_Duplicados_Omitidos, Total_Incompletos, Total_Errores,
            Usuario_Ejecutor, Duracion_Segundos, Estado, Detalle_JSON
        )
        OUTPUT INSERTED.BitacoraID
        VALUES (
            '{fuente}',
            {f"N'{archivo}'" if archivo else 'NULL'},
            {int(datos.get('Total_Registros_Leidos', 0))},
            {int(datos.get('Total_Insertados', 0))},
            {int(datos.get('Total_Actualizados', 0))},
            {int(datos.get('Total_Duplicados_Omitidos', 0))},
            {int(datos.get('Total_Incompletos', 0))},
            {int(datos.get('Total_Errores', 0))},
            {f"N'{usuario}'" if usuario else 'NULL'},
            {int(datos.get('Duracion_Segundos')) if datos.get('Duracion_Segundos') else 'NULL'},
            '{estado}',
            {f"N'{detalle_str}'" if detalle_str else 'NULL'}
        )
    """
    
    try:
        result = execute_hub_query(server, query)
        if result and len(result) > 0:
            return {"success": True, "bitacora_id": result[0].get("BitacoraID")}
        return {"success": False, "error": "No se obtuvo ID de bitácora"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def actualizar_bitacora(
    server: Dict,
    bitacora_id: int,
    datos: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Actualiza métricas de una entrada en la bitácora.
    """
    try:
        id_safe = int(bitacora_id)
    except (ValueError, TypeError):
        return {"success": False, "error": "ID de bitácora inválido"}
    
    set_clauses = []
    
    # Campos numéricos
    campos_num = ['total_registros_leidos', 'total_insertados', 'total_actualizados',
                  'total_duplicados_omitidos', 'total_incompletos', 'total_errores',
                  'duracion_segundos']
    for campo in campos_num:
        if campo in datos and datos[campo] is not None:
            col_map = {
                'total_registros_leidos': 'Total_Registros_Leidos',
                'total_insertados': 'Total_Insertados',
                'total_actualizados': 'Total_Actualizados',
                'total_duplicados_omitidos': 'Total_Duplicados_Omitidos',
                'total_incompletos': 'Total_Incompletos',
                'total_errores': 'Total_Errores',
                'duracion_segundos': 'Duracion_Segundos'
            }
            set_clauses.append(f"{col_map[campo]} = {int(datos[campo])}")
    
    # Estado
    if 'estado' in datos:
        estado = escape_sql_string(datos['estado'])
        set_clauses.append(f"Estado = '{estado}'")
    
    # JSON detalle
    if 'detalle_json' in datos:
        detalle = escape_sql_string(json.dumps(datos['detalle_json']))
        set_clauses.append(f"Detalle_JSON = N'{detalle}'")
    
    if not set_clauses:
        return {"success": False, "error": "No hay campos para actualizar"}
    
    query = f"""
        UPDATE RH_Importacion_Bitacora
        SET {', '.join(set_clauses)}
        WHERE BitacoraID = {id_safe}
    """
    
    try:
        execute_hub_query(server, query)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def listar_bitacora(
    server: Dict,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Lista el historial de importaciones.
    """
    query = f"""
        SELECT 
            BitacoraID as bitacora_id,
            Fecha_Ejecucion as Fecha_Ejecucion,
            Fuente as Fuente,
            Archivo_Origen as Archivo_Origen,
            Total_Registros_Leidos as Total_Registros_Leidos,
            Total_Insertados as Total_Insertados,
            Total_Actualizados as Total_Actualizados,
            Total_Duplicados_Omitidos as Total_Duplicados_Omitidos,
            Total_Incompletos as Total_Incompletos,
            Total_Errores as Total_Errores,
            Usuario_Ejecutor as Usuario_Ejecutor,
            Duracion_Segundos as Duracion_Segundos,
            Estado as Estado
        FROM RH_Importacion_Bitacora
        ORDER BY Fecha_Ejecucion DESC
        OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
    """
    
    try:
        datos = execute_hub_query(server, query)
        return {"datos": datos, "success": True}
    except Exception as e:
        return {"datos": [], "error": str(e), "success": False}


# ============================================================================
# QUERIES DE DEDUPLICACIÓN
# ============================================================================

async def buscar_duplicados_por_curp(server: Dict, curp: str) -> List[Dict]:
    """Busca colaboradores existentes por CURP (confianza ALTA)."""
    curp_safe = escape_sql_string(curp.strip().upper())
    query = f"""
        SELECT ColaboradorID, Nombre_Completo, CURP, RFC, SucursalID, PuestoID
        FROM RH_Colaboradores_Expediente
        WHERE CURP = '{curp_safe}' AND Colaborador_Activo = 1
    """
    return execute_hub_query(server, query)


async def buscar_duplicados_por_rfc(server: Dict, rfc: str) -> List[Dict]:
    """Busca colaboradores existentes por RFC (confianza MEDIA)."""
    rfc_safe = escape_sql_string(rfc.strip().upper())
    query = f"""
        SELECT ColaboradorID, Nombre_Completo, CURP, RFC, SucursalID, PuestoID
        FROM RH_Colaboradores_Expediente
        WHERE RFC = '{rfc_safe}' AND Colaborador_Activo = 1
    """
    return execute_hub_query(server, query)


async def buscar_duplicados_por_nombre_sucursal(
    server: Dict, 
    nombre: str, 
    sucursal_id: int
) -> List[Dict]:
    """Busca colaboradores por nombre + sucursal (confianza MUY_BAJA)."""
    nombre_safe = escape_sql_string(nombre.strip().upper())
    query = f"""
        SELECT ColaboradorID, Nombre_Completo, CURP, RFC, SucursalID, PuestoID
        FROM RH_Colaboradores_Expediente
        WHERE UPPER(Nombre_Completo) = '{nombre_safe}' 
          AND SucursalID = {int(sucursal_id)}
          AND Colaborador_Activo = 1
    """
    return execute_hub_query(server, query)


async def buscar_coincidencias_parciales(server: Dict, nombre: str) -> List[Dict]:
    """Busca coincidencias parciales por nombre (requiere revisión manual)."""
    # Usar SOUNDEX o LIKE para coincidencias aproximadas
    palabras = nombre.strip().upper().split()
    if len(palabras) < 2:
        return []
    
    primer_apellido = escape_sql_string(palabras[0])
    query = f"""
        SELECT ColaboradorID, Nombre_Completo, CURP, RFC, SucursalID, PuestoID
        FROM RH_Colaboradores_Expediente
        WHERE UPPER(Nombre_Completo) LIKE '%{primer_apellido}%'
          AND Colaborador_Activo = 1
    """
    return execute_hub_query(server, query)
