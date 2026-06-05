from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - Service de Aprobación de Colaboradores
====================================================
Lógica de negocio para aprobar registros de staging hacia el maestro.

REGLAS OBLIGATORIAS:
1. Solo MPro_CENTRAL2020 es fuente válida
2. Estado != 'Excluido' para ser candidato
3. Clasificacion != 'incompleto' para aprobar
4. CURP/RFC deben ser únicos en maestro (o UPDATE)
5. Toda acción debe quedar en bitácora
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import pymssql

logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTES
# ============================================================================

FUENTE_VALIDA = "MPro_CENTRAL2020"
FUENTES_EXCLUIDAS = ["MPro_HR2020"]

ESTADO_PENDIENTE = "Pendiente"
ESTADO_APROBADO = "Aprobado"
ESTADO_PROCESADO = "Procesado"
ESTADO_RECHAZADO = "Rechazado"
ESTADO_OBSERVADO = "Observado"
ESTADO_EXCLUIDO = "Excluido"
ESTADO_ERROR = "Error"

ACCION_INSERT = "INSERT"
ACCION_UPDATE = "UPDATE"
ACCION_SKIP = "SKIP"
ACCION_REJECTED = "REJECTED"

# ============================================================================
# CONEXIÓN DIRECTA
# ============================================================================

def get_hub_connection(server: Dict):
    """Obtiene conexión directa a EDARSA HUB con autocommit."""
    return pymssql.connect(
        server=server['host'],
        port=server['port'],
        database=server['database'],
        user=server['username'],
        password=server['password'],
        login_timeout=30,
        autocommit=True
    )

def escape_sql(value) -> str:
    """Escapa una cadena para SQL Server."""
    if value is None:
        return ""
    return str(value).replace("'", "''").strip()[:200]


# ============================================================================
# CONSULTAS DE STAGING
# ============================================================================

def obtener_estadisticas_staging(server: Dict) -> Dict:
    """Obtiene estadísticas del staging por estado y fuente."""
    conn = get_hub_connection(server)
    cursor = conn.cursor(as_dict=True)
    
    # Total por estado (excluyendo HR2020)
    cursor.execute("""
        SELECT 
            Estado,
            COUNT(*) as cantidad
        FROM RH_Importacion_Staging
        WHERE Fuente != 'MPro_HR2020'
        GROUP BY Estado
    """)
    por_estado = {r['Estado']: r['cantidad'] for r in cursor.fetchall()}
    
    # Total por fuente
    cursor.execute("""
        SELECT 
            Fuente,
            COUNT(*) as cantidad,
            SUM(CASE WHEN Clasificacion = 'nuevo' AND Estado = 'Pendiente' THEN 1 ELSE 0 END) as candidatos
        FROM RH_Importacion_Staging
        WHERE Estado != 'Excluido'
        GROUP BY Fuente
    """)
    por_fuente = {}
    for r in cursor.fetchall():
        por_fuente[r['Fuente']] = {
            'total': r['cantidad'],
            'candidatos': r['candidatos']
        }
    
    # Total por empresa (solo CENTRAL2020)
    cursor.execute("""
        SELECT 
            Sucursal_Nombre as empresa,
            COUNT(*) as total,
            SUM(CASE WHEN Clasificacion = 'nuevo' AND Estado = 'Pendiente' THEN 1 ELSE 0 END) as candidatos,
            SUM(CASE WHEN Estado = 'Procesado' THEN 1 ELSE 0 END) as procesados
        FROM RH_Importacion_Staging
        WHERE Fuente = 'MPro_CENTRAL2020'
        GROUP BY Sucursal_Nombre
        ORDER BY total DESC
    """)
    por_empresa = []
    for r in cursor.fetchall():
        por_empresa.append({
            'empresa': r['empresa'] or '(Sin empresa)',
            'total': r['total'],
            'candidatos': r['candidatos'],
            'procesados': r['procesados']
        })
    
    conn.close()
    
    return {
        'por_estado': por_estado,
        'por_fuente': por_fuente,
        'por_empresa': por_empresa,
        'resumen': {
            'total_valido': sum(v['total'] for v in por_fuente.values() if 'MPro_HR2020' not in str(v)),
            'candidatos_aprobacion': sum(v.get('candidatos', 0) for k, v in por_fuente.items() if k == FUENTE_VALIDA),
            'ya_procesados': por_estado.get('Procesado', 0),
            'excluidos': por_estado.get('Excluido', 0)
        }
    }


def obtener_pendientes_aprobacion(
    server: Dict,
    empresa: Optional[str] = None,
    limite: int = 100,
    offset: int = 0
) -> List[Dict]:
    """Obtiene registros candidatos a aprobación."""
    conn = get_hub_connection(server)
    cursor = conn.cursor(as_dict=True)
    
    where_empresa = f"AND Sucursal_Nombre = '{escape_sql(empresa)}'" if empresa else ""
    
    cursor.execute(f"""
        SELECT 
            StagingID,
            Nombre_Completo,
            CURP,
            RFC,
            Numero_Empleado_Externo,
            Sucursal_Nombre,
            Area_Departamento,
            Puesto_Nombre,
            Sexo,
            Fuente,
            Estado,
            Clasificacion,
            Nivel_Confianza,
            Observaciones,
            Fecha_Importacion
        FROM RH_Importacion_Staging
        WHERE Fuente = '{FUENTE_VALIDA}'
          AND Estado = 'Pendiente'
          AND Clasificacion = 'nuevo'
          {where_empresa}
        ORDER BY Sucursal_Nombre, Nombre_Completo
        OFFSET {offset} ROWS FETCH NEXT {limite} ROWS ONLY
    """)
    
    result = cursor.fetchall()
    conn.close()
    return result


def obtener_incompletos(server: Dict, limite: int = 100) -> List[Dict]:
    """Obtiene registros incompletos (sin CURP/RFC)."""
    conn = get_hub_connection(server)
    cursor = conn.cursor(as_dict=True)
    
    cursor.execute(f"""
        SELECT 
            StagingID,
            Nombre_Completo,
            CURP,
            RFC,
            Sucursal_Nombre,
            Fuente,
            Estado,
            Clasificacion,
            Observaciones
        FROM RH_Importacion_Staging
        WHERE Clasificacion = 'incompleto'
          AND Estado NOT IN ('Excluido', 'Procesado')
        ORDER BY Fuente, Nombre_Completo
        OFFSET 0 ROWS FETCH NEXT {limite} ROWS ONLY
    """)
    
    result = cursor.fetchall()
    conn.close()
    return result


def obtener_excluidos(server: Dict, limite: int = 100) -> List[Dict]:
    """Obtiene registros excluidos (para auditoría)."""
    conn = get_hub_connection(server)
    cursor = conn.cursor(as_dict=True)
    
    cursor.execute(f"""
        SELECT 
            StagingID,
            Nombre_Completo,
            CURP,
            RFC,
            Sucursal_Nombre,
            Fuente,
            Estado,
            Observaciones
        FROM RH_Importacion_Staging
        WHERE Estado = 'Excluido'
        ORDER BY Fuente, Nombre_Completo
        OFFSET 0 ROWS FETCH NEXT {limite} ROWS ONLY
    """)
    
    result = cursor.fetchall()
    conn.close()
    return result


def obtener_registro_staging(server: Dict, staging_id: int) -> Optional[Dict]:
    """Obtiene un registro específico del staging."""
    conn = get_hub_connection(server)
    cursor = conn.cursor(as_dict=True)
    
    cursor.execute(f"""
        SELECT *
        FROM RH_Importacion_Staging
        WHERE StagingID = {staging_id}
    """)
    
    result = cursor.fetchone()
    conn.close()
    return result


# ============================================================================
# VALIDACIONES PRE-APROBACIÓN
# ============================================================================

def validar_candidato_aprobacion(registro: Dict) -> Tuple[bool, str]:
    """
    Valida si un registro es candidato a aprobación.
    Retorna (es_valido, mensaje).
    """
    # 1. Fuente válida
    if registro.get('Fuente') != FUENTE_VALIDA:
        return False, f"Fuente no autorizada: {registro.get('Fuente')}"
    
    # 2. Estado válido
    if registro.get('Estado') == ESTADO_EXCLUIDO:
        return False, "Registro excluido"
    
    if registro.get('Estado') == ESTADO_PROCESADO:
        return False, "Registro ya procesado"
    
    # 3. Clasificación válida
    if registro.get('Clasificacion') == 'incompleto':
        return False, "Registro incompleto (sin CURP/RFC)"
    
    # 4. Nombre obligatorio
    nombre = registro.get('Nombre_Completo', '').strip()
    if not nombre or len(nombre) < 3:
        return False, "Nombre de colaborador vacío o muy corto"
    
    # 5. Al menos un identificador
    curp = registro.get('CURP', '').strip() if registro.get('CURP') else ''
    rfc = registro.get('RFC', '').strip() if registro.get('RFC') else ''
    
    if not curp and not rfc:
        return False, "Sin CURP ni RFC"
    
    return True, "OK"


def verificar_duplicado_en_maestro(server: Dict, curp: Optional[str], rfc: Optional[str]) -> Tuple[bool, Optional[int], str]:
    """
    Verifica si existe un duplicado en RH_Colaboradores_Expediente.
    Retorna (existe_duplicado, colaborador_id_existente, tipo_match).
    """
    conn = get_hub_connection(server)
    cursor = conn.cursor(as_dict=True)
    
    # Buscar por CURP
    if curp and curp.strip():
        cursor.execute(f"""
            SELECT ColaboradorID, Nombre_Completo
            FROM RH_Colaboradores_Expediente
            WHERE CURP = '{escape_sql(CURP)}'
        """)
        result = cursor.fetchone()
        if result:
            conn.close()
            return True, result['ColaboradorID'], f"CURP_MATCH: {result['Nombre_Completo']}"
    
    # Buscar por RFC
    if rfc and rfc.strip():
        cursor.execute(f"""
            SELECT ColaboradorID, Nombre_Completo
            FROM RH_Colaboradores_Expediente
            WHERE RFC = '{escape_sql(RFC)}'
        """)
        result = cursor.fetchone()
        if result:
            conn.close()
            return True, result['ColaboradorID'], f"RFC_MATCH: {result['Nombre_Completo']}"
    
    conn.close()
    return False, None, "NO_MATCH"


# ============================================================================
# OPERACIONES DE APROBACIÓN
# ============================================================================

def aprobar_registro(
    server: Dict,
    staging_id: int,
    usuario: str = "Sistema"
) -> Dict:
    """
    Aprueba un registro de staging y lo inserta/actualiza en el maestro.
    """
    conn = get_hub_connection(server)
    cursor = conn.cursor(as_dict=True)
    
    resultado = {
        'staging_id': staging_id,
        'exito': False,
        'accion': None,
        'colaborador_id': None,
        'mensaje': ''
    }
    
    try:
        # 1. Obtener registro
        registro = obtener_registro_staging(server, staging_id)
        if not registro:
            resultado['mensaje'] = "Registro no encontrado"
            return resultado
        
        # 2. Validar candidato
        es_valido, mensaje_validacion = validar_candidato_aprobacion(registro)
        if not es_valido:
            resultado['mensaje'] = mensaje_validacion
            # Marcar como rechazado
            cursor.execute(f"""
                UPDATE RH_Importacion_Staging
                SET Estado = '{ESTADO_RECHAZADO}',
                    Observaciones = Observaciones + ' | Rechazado auto: {escape_sql(mensaje_validacion)}',
                    Usuario_Aprobador = '{escape_sql(usuario)}',
                    Fecha_Aprobacion = GETDATE()
                WHERE StagingID = {staging_id}
            """)
            return resultado
        
        # 3. Verificar duplicado en maestro
        curp = registro.get('CURP', '').strip() if registro.get('CURP') else ''
        rfc = registro.get('RFC', '').strip() if registro.get('RFC') else ''
        
        existe_dup, colab_id_existente, tipo_match = verificar_duplicado_en_maestro(server, curp, rfc)
        
        # 4. Ejecutar acción
        if existe_dup:
            # UPDATE en maestro
            resultado['accion'] = ACCION_UPDATE
            resultado['colaborador_id'] = colab_id_existente
            
            # Actualizar solo campos no nulos
            update_fields = []
            if registro.get('Nombre_Completo'):
                update_fields.append(f"Nombre_Completo = N'{escape_sql(registro['Nombre_Completo'])}'")
            if registro.get('Sucursal_Nombre'):
                update_fields.append(f"ObservacionesRH = N'Empresa origen: {escape_sql(registro['Sucursal_Nombre'])}'")
            
            if update_fields:
                cursor.execute(f"""
                    UPDATE RH_Colaboradores_Expediente
                    SET {', '.join(update_fields)}
                    WHERE ColaboradorID = {colab_id_existente}
                """)
            
            resultado['exito'] = True
            resultado['mensaje'] = f"Actualizado colaborador existente ({tipo_match})"
            
        else:
            # INSERT en maestro
            resultado['accion'] = ACCION_INSERT
            
            nombre = escape_sql(registro.get('Nombre_Completo', ''))
            curp_val = escape_sql(curp) if curp else ''
            rfc_val = escape_sql(rfc) if rfc else ''
            num_emp = escape_sql(registro.get('Numero_Empleado_Externo', ''))
            sexo = escape_sql((registro.get('Sexo') or '')[:1])
            observaciones = f"Empresa origen: {escape_sql(registro.get('Sucursal_Nombre', ''))}"
            
            # Colaborador_Activo es columna COMPUTED, no se inserta
            cursor.execute(f"""
                INSERT INTO RH_Colaboradores_Expediente (
                    Nombre_Completo, CURP, RFC, NumeroEmpleado,
                    Sexo, Estatus_Laboral, ObservacionesRH
                )
                OUTPUT INSERTED.ColaboradorID
                VALUES (
                    N'{nombre}',
                    {f"'{curp_val}'" if CURP else 'NULL'},
                    {f"'{rfc_val}'" if RFC else 'NULL'},
                    {f"'{num_emp}'" if num_emp else 'NULL'},
                    {f"'{sexo}'" if sexo else 'NULL'},
                    'ACTIVO',
                    N'{observaciones}'
                )
            """)
            
            new_id_result = cursor.fetchone()
            if new_id_result:
                resultado['colaborador_id'] = new_id_result['ColaboradorID']
                resultado['exito'] = True
                resultado['mensaje'] = "Colaborador insertado exitosamente"
            else:
                resultado['mensaje'] = "Error al obtener ID del nuevo colaborador"
        
        # 5. Actualizar staging
        if resultado['exito']:
            cursor.execute(f"""
                UPDATE RH_Importacion_Staging
                SET Estado = '{ESTADO_PROCESADO}',
                    Accion_Realizada = '{resultado['accion']}',
                    ColaboradorID_Destino = {resultado['colaborador_id'] or 'NULL'},
                    Usuario_Aprobador = '{escape_sql(usuario)}',
                    Fecha_Aprobacion = GETDATE(),
                    Observaciones = Observaciones + ' | {resultado['mensaje']}'
                WHERE StagingID = {staging_id}
            """)
        
    except Exception as e:
        resultado['mensaje'] = f"Error: {str(e)[:200]}"
        logger.error(f"Error aprobando registro {staging_id}: {e}")
        
        # Marcar como error
        try:
            cursor.execute(f"""
                UPDATE RH_Importacion_Staging
                SET Estado = '{ESTADO_ERROR}',
                    Mensaje_Error = N'{escape_sql(str(e)[:200])}',
                    Usuario_Aprobador = '{escape_sql(usuario)}',
                    Fecha_Aprobacion = GETDATE()
                WHERE StagingID = {staging_id}
            """)
        except Exception:
            pass
    
    finally:
        conn.close()
    
    return resultado


def rechazar_registro(
    server: Dict,
    staging_id: int,
    motivo: str,
    usuario: str = "Sistema"
) -> Dict:
    """Rechaza un registro con motivo."""
    conn = get_hub_connection(server)
    cursor = conn.cursor(as_dict=True)
    
    resultado = {
        'staging_id': staging_id,
        'exito': False,
        'mensaje': ''
    }
    
    try:
        cursor.execute(f"""
            UPDATE RH_Importacion_Staging
            SET Estado = '{ESTADO_RECHAZADO}',
                Observaciones = Observaciones + ' | RECHAZADO: {escape_sql(motivo)}',
                Usuario_Aprobador = '{escape_sql(usuario)}',
                Fecha_Aprobacion = GETDATE()
            WHERE StagingID = {staging_id}
              AND Estado NOT IN ('{ESTADO_PROCESADO}', '{ESTADO_EXCLUIDO}')
        """)
        
        resultado['exito'] = True
        resultado['mensaje'] = f"Registro rechazado: {motivo}"
        
    except Exception as e:
        resultado['mensaje'] = f"Error: {str(e)}"
    
    finally:
        conn.close()
    
    return resultado


def observar_registro(
    server: Dict,
    staging_id: int,
    observacion: str,
    usuario: str = "Sistema"
) -> Dict:
    """Marca un registro como observado (requiere revisión)."""
    conn = get_hub_connection(server)
    cursor = conn.cursor(as_dict=True)
    
    resultado = {
        'staging_id': staging_id,
        'exito': False,
        'mensaje': ''
    }
    
    try:
        cursor.execute(f"""
            UPDATE RH_Importacion_Staging
            SET Estado = '{ESTADO_OBSERVADO}',
                Observaciones = Observaciones + ' | OBSERVADO: {escape_sql(observacion)}',
                Usuario_Aprobador = '{escape_sql(usuario)}',
                Fecha_Aprobacion = GETDATE()
            WHERE StagingID = {staging_id}
              AND Estado NOT IN ('{ESTADO_PROCESADO}', '{ESTADO_EXCLUIDO}')
        """)
        
        resultado['exito'] = True
        resultado['mensaje'] = f"Registro observado: {observacion}"
        
    except Exception as e:
        resultado['mensaje'] = f"Error: {str(e)}"
    
    finally:
        conn.close()
    
    return resultado


def aprobar_lote(
    server: Dict,
    empresa: Optional[str] = None,
    limite: int = 100,
    usuario: str = "Sistema"
) -> Dict:
    """
    Aprueba múltiples registros en lote.
    Solo aprueba candidatos válidos de MPro_CENTRAL2020.
    """
    resultado = {
        'total_procesados': 0,
        'exitosos': 0,
        'fallidos': 0,
        'detalle': []
    }
    
    # Obtener candidatos
    pendientes = obtener_pendientes_aprobacion(server, empresa=empresa, limite=limite)
    
    for registro in pendientes:
        staging_id = registro['StagingID']
        res = aprobar_registro(server, staging_id, usuario)
        
        resultado['total_procesados'] += 1
        if res['exito']:
            resultado['exitosos'] += 1
        else:
            resultado['fallidos'] += 1
        
        resultado['detalle'].append({
            'staging_id': staging_id,
            'nombre': registro.get('Nombre_Completo', '')[:50],
            'resultado': res
        })
    
    # Registrar en bitácora
    registrar_bitacora_aprobacion(
        server,
        f"Aprobación en lote - Empresa: {empresa or 'TODAS'}",
        resultado['total_procesados'],
        resultado['exitosos'],
        resultado['fallidos'],
        usuario
    )
    
    return resultado


def registrar_bitacora_aprobacion(
    server: Dict,
    descripcion: str,
    total: int,
    exitosos: int,
    fallidos: int,
    usuario: str
):
    """Registra una entrada en la bitácora de importación."""
    conn = get_hub_connection(server)
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"""
            INSERT INTO RH_Importacion_Bitacora (
                Fuente, Archivo_Origen, Usuario_Ejecutor,
                Total_Registros_Leidos, Total_Insertados, Total_Errores,
                Estado, Detalle_JSON
            ) VALUES (
                'APROBACION_LOTE',
                N'{escape_sql(descripcion)}',
                '{escape_sql(usuario)}',
                {total},
                {exitosos},
                {fallidos},
                'Completado',
                '{{"total": {total}, "exitosos": {exitosos}, "fallidos": {fallidos}}}'
            )
        """)
    except Exception as e:
        logger.error(f"Error registrando bitácora: {e}")
    finally:
        conn.close()
