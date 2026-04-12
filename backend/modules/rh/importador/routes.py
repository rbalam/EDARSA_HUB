"""
EDARSA HUB - Endpoints API de Importación RH
============================================
Endpoints para importación controlada de empleados desde Excel.

FLUJO DE ENDPOINTS:
1. POST /importar/excel/preview → Preview sin insertar
2. POST /importar/excel/staging → Cargar a staging
3. GET /importar/staging → Listar staging con filtros
4. PUT /importar/staging/{id} → Actualizar clasificación/estado
5. POST /importar/staging/aprobar → Aprobar y cargar a maestro
6. GET /importar/bitacora → Ver historial
7. POST /importar/tablas/crear → Crear tablas de apoyo (solo admin)

RESTRICCIONES:
- NO hay carga directa al maestro sin pasar por staging
- Todos los endpoints requieren autenticación
- Carga al maestro requiere aprobación explícita
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from typing import Optional, List
import logging
from datetime import datetime
import time

from core.security import get_current_user

from .schemas import (
    PreviewImportacion,
    ImportacionStagingResponse,
    ImportacionStagingUpdate,
    ImportacionBitacoraResponse,
    ConfirmarCargaRequest,
    ConfirmarCargaResponse,
    FiltrosStaging,
    ESTADO_APROBADO,
    ESTADO_PROCESADO,
    ESTADO_ERROR,
    ACCION_INSERT,
    ACCION_UPDATE,
    ACCION_SKIP,
    CLASIFICACION_NUEVO,
    CLASIFICACION_ACTUALIZAR,
)

from .repository import (
    get_edarsa_hub_server,
    crear_tablas_importacion,
    listar_staging,
    actualizar_estado_staging,
    insertar_bitacora,
    actualizar_bitacora,
    listar_bitacora,
    execute_hub_query,
    escape_sql_string,
)

from .service import ImportadorExcelService


# ============================================================================
# ROUTER
# ============================================================================

router = APIRouter(prefix="/rrhh/importar", tags=["RH - Importación"])
logger = logging.getLogger(__name__)


# ============================================================================
# ENDPOINTS DE CONFIGURACIÓN
# ============================================================================

@router.post("/tablas/crear", summary="Crear tablas de staging y bitácora")
async def crear_tablas_apoyo(current_user: dict = Depends(get_current_user)):
    """
    Crea las tablas RH_Importacion_Staging y RH_Importacion_Bitacora
    si no existen.
    
    Solo disponible para administradores.
    """
    # Verificar permisos (solo admin)
    if current_user.get('role') not in ['admin', 'superadmin']:
        raise HTTPException(status_code=403, detail="Solo administradores pueden crear tablas")
    
    resultado = await crear_tablas_importacion()
    
    if not resultado.get('success'):
        raise HTTPException(status_code=500, detail=resultado.get('error', 'Error creando tablas'))
    
    return {
        "success": True,
        "mensaje": "Tablas de importación verificadas/creadas",
        "detalle": resultado
    }


@router.get("/tablas/script", summary="Obtener script DDL de tablas")
async def obtener_script_tablas(current_user: dict = Depends(get_current_user)):
    """
    Devuelve los scripts DDL para crear las tablas de importación.
    Útil para revisión o ejecución manual.
    """
    from .repository import SCRIPT_CREAR_STAGING, SCRIPT_CREAR_BITACORA
    
    return {
        "script_staging": SCRIPT_CREAR_STAGING,
        "script_bitacora": SCRIPT_CREAR_BITACORA,
        "instrucciones": [
            "1. Ejecutar script_staging en EDARSA HUB",
            "2. Ejecutar script_bitacora en EDARSA HUB",
            "3. Los scripts verifican si las tablas ya existen antes de crearlas"
        ]
    }


# ============================================================================
# ENDPOINTS DE PREVIEW
# ============================================================================

@router.post("/excel/preview", response_model=PreviewImportacion, summary="Preview de importación Excel")
async def preview_importacion_excel(
    archivo: UploadFile = File(..., description="Archivo Excel (.xlsx)"),
    hoja_nombre: Optional[str] = Query(None, description="Nombre de la hoja a procesar"),
    current_user: dict = Depends(get_current_user)
):
    """
    Genera un preview de la importación SIN insertar nada en base de datos.
    
    Analiza el archivo Excel y clasifica cada registro:
    - **nuevos**: Colaboradores que no existen en el maestro
    - **actualizar**: Colaboradores encontrados por CURP/RFC
    - **duplicados_probables**: Requieren revisión manual
    - **incompletos**: Sin datos suficientes para identificación
    - **rechazados**: Datos inválidos
    
    IMPORTANTE: El Excel de Cienfuegos es de nómina semanal, no un catálogo
    maestro limpio. El preview permite revisar antes de cargar.
    """
    # Validar extensión
    if not archivo.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .xlsx o .xls")
    
    # Leer contenido
    contenido = await archivo.read()
    
    # Generar preview
    servicio = ImportadorExcelService()
    preview = await servicio.generar_preview(
        contenido_archivo=contenido,
        nombre_archivo=archivo.filename,
        usuario=current_user.get('username', 'unknown'),
        hoja_nombre=hoja_nombre
    )
    
    return preview


# ============================================================================
# ENDPOINTS DE STAGING
# ============================================================================

@router.post("/excel/staging", summary="Cargar Excel a staging")
async def cargar_excel_a_staging(
    archivo: UploadFile = File(..., description="Archivo Excel (.xlsx)"),
    hoja_nombre: Optional[str] = Query(None, description="Nombre de la hoja a procesar"),
    solo_validos: bool = Query(True, description="Solo cargar registros válidos"),
    current_user: dict = Depends(get_current_user)
):
    """
    Carga los registros del Excel a la tabla de staging.
    
    NO inserta directamente en el maestro de colaboradores.
    Los registros quedan pendientes de validación y aprobación.
    
    Parámetros:
    - **solo_validos**: Si True, omite registros incompletos/rechazados
    """
    # Validar extensión
    if not archivo.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .xlsx o .xls")
    
    # Leer contenido
    contenido = await archivo.read()
    
    # Cargar a staging
    servicio = ImportadorExcelService()
    resultado = await servicio.cargar_a_staging(
        contenido_archivo=contenido,
        nombre_archivo=archivo.filename,
        usuario=current_user.get('username', 'unknown'),
        hoja_nombre=hoja_nombre,
        solo_validos=solo_validos
    )
    
    if not resultado.get('success'):
        raise HTTPException(status_code=500, detail=resultado.get('error', 'Error en carga'))
    
    return {
        "success": True,
        "mensaje": "Registros cargados a staging para revisión",
        "total_leidos": resultado.get('total_leidos', 0),
        "total_insertados_staging": resultado.get('total_insertados_staging', 0),
        "total_omitidos": resultado.get('total_omitidos', 0),
        "errores": resultado.get('errores', [])
    }


@router.get("/staging", summary="Listar registros en staging")
async def listar_registros_staging(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    clasificacion: Optional[str] = Query(None, description="Filtrar por clasificación"),
    fuente: Optional[str] = Query(None, description="Filtrar por fuente"),
    solo_pendientes: bool = Query(False, description="Solo pendientes de aprobación"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """
    Lista los registros en staging con filtros opcionales.
    
    Permite revisar qué registros están pendientes de aprobación.
    """
    server = await get_edarsa_hub_server()
    if not server:
        raise HTTPException(status_code=503, detail="Servidor EDARSA HUB no disponible")
    
    filtros = {
        'estado': estado,
        'clasificacion': clasificacion,
        'fuente': fuente,
        'solo_pendientes': solo_pendientes
    }
    
    resultado = await listar_staging(server, filtros, limit, offset)
    
    if not resultado.get('success'):
        raise HTTPException(status_code=500, detail=resultado.get('error', 'Error listando staging'))
    
    return resultado


@router.put("/staging/{staging_id}", summary="Actualizar registro en staging")
async def actualizar_registro_staging(
    staging_id: int,
    updates: ImportacionStagingUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Actualiza el estado o clasificación de un registro en staging.
    
    Útil para:
    - Reclasificar un duplicado_probable como nuevo
    - Marcar un registro como rechazado
    - Corregir sucursal_id o puesto_id antes de aprobar
    """
    server = await get_edarsa_hub_server()
    if not server:
        raise HTTPException(status_code=503, detail="Servidor EDARSA HUB no disponible")
    
    resultado = await actualizar_estado_staging(
        server, 
        staging_id, 
        updates.model_dump(exclude_none=True)
    )
    
    if not resultado.get('success'):
        raise HTTPException(status_code=500, detail=resultado.get('error', 'Error actualizando'))
    
    return {"success": True, "mensaje": "Registro actualizado"}


@router.post("/staging/aprobar", response_model=ConfirmarCargaResponse, summary="Aprobar y cargar al maestro")
async def aprobar_y_cargar_maestro(
    request: ConfirmarCargaRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Aprueba los registros seleccionados y los carga al maestro de colaboradores.
    
    FLUJO OBLIGATORIO:
    1. Marcar registros como "Aprobado"
    2. Ejecutar INSERT o UPDATE según clasificación
    3. Actualizar staging con resultado
    4. Registrar en bitácora
    
    Solo se procesan registros con estado 'Pendiente' o 'Validado'.
    """
    server = await get_edarsa_hub_server()
    if not server:
        raise HTTPException(status_code=503, detail="Servidor EDARSA HUB no disponible")
    
    inicio = time.time()
    
    # Crear entrada en bitácora
    bitacora_data = {
        'fuente': 'Excel_CF',
        'archivo_origen': 'Aprobación manual',
        'usuario_ejecutor': request.usuario_aprobador,
        'estado': 'En Proceso'
    }
    bitacora_result = await insertar_bitacora(server, bitacora_data)
    bitacora_id = bitacora_result.get('bitacora_id')
    
    resultado = ConfirmarCargaResponse(bitacora_id=bitacora_id)
    
    for staging_id in request.staging_ids:
        try:
            # Obtener el registro específico
            query_registro = f"""
                SELECT * FROM RH_Importacion_Staging WHERE StagingID = {int(staging_id)}
            """
            registros = execute_hub_query(server, query_registro)
            
            if not registros:
                resultado.errores.append({
                    'staging_id': staging_id,
                    'error': 'Registro no encontrado'
                })
                resultado.total_errores += 1
                continue
            
            reg = registros[0]
            clasificacion = reg.get('Clasificacion', CLASIFICACION_NUEVO)
            
            # Marcar como aprobado
            await actualizar_estado_staging(server, staging_id, {
                'estado': ESTADO_APROBADO,
                'usuario_aprobador': request.usuario_aprobador
            })
            
            # Ejecutar INSERT o UPDATE según clasificación
            if clasificacion == CLASIFICACION_NUEVO:
                # INSERT en maestro
                nombre = escape_sql_string(reg.get('Nombre_Completo', ''))
                curp = escape_sql_string(reg.get('CURP') or '')
                rfc = escape_sql_string(reg.get('RFC') or '')
                clabe = escape_sql_string(reg.get('CLABE_Bancaria') or '')
                suc_id = reg.get('SucursalID') or 'NULL'
                puesto_id = reg.get('PuestoID') or 'NULL'
                
                insert_query = f"""
                    INSERT INTO RH_Colaboradores_Expediente 
                    (Nombre_Completo, CURP, RFC, CLABE_Bancaria, SucursalID, PuestoID, 
                     Colaborador_Activo, Fecha_Alta, Estatus_Laboral)
                    OUTPUT INSERTED.ColaboradorID
                    VALUES (
                        N'{nombre}',
                        {f"'{curp}'" if curp else 'NULL'},
                        {f"'{rfc}'" if rfc else 'NULL'},
                        {f"'{clabe}'" if clabe else 'NULL'},
                        {suc_id},
                        {puesto_id},
                        1, GETDATE(), N'Activo'
                    )
                """
                
                insert_result = execute_hub_query(server, insert_query)
                
                if insert_result:
                    colab_id = insert_result[0].get('ColaboradorID')
                    await actualizar_estado_staging(server, staging_id, {
                        'estado': ESTADO_PROCESADO,
                        'accion_realizada': ACCION_INSERT,
                        'colaborador_id_destino': colab_id
                    })
                    resultado.total_insertados += 1
                else:
                    raise Exception("INSERT no retornó ID")
                    
            elif clasificacion == CLASIFICACION_ACTUALIZAR:
                # UPDATE en maestro
                colab_match = reg.get('ColaboradorID_Match')
                if not colab_match:
                    raise Exception("No hay ColaboradorID_Match para actualizar")
                
                # Solo actualizar campos no vacíos
                set_parts = []
                if reg.get('CURP'):
                    set_parts.append(f"CURP = '{escape_sql_string(reg['CURP'])}'")
                if reg.get('RFC'):
                    set_parts.append(f"RFC = '{escape_sql_string(reg['RFC'])}'")
                if reg.get('CLABE_Bancaria'):
                    set_parts.append(f"CLABE_Bancaria = '{escape_sql_string(reg['CLABE_Bancaria'])}'")
                if reg.get('SucursalID'):
                    set_parts.append(f"SucursalID = {int(reg['SucursalID'])}")
                if reg.get('PuestoID'):
                    set_parts.append(f"PuestoID = {int(reg['PuestoID'])}")
                
                if set_parts:
                    update_query = f"""
                        UPDATE RH_Colaboradores_Expediente
                        SET {', '.join(set_parts)}
                        WHERE ColaboradorID = {int(colab_match)}
                    """
                    execute_hub_query(server, update_query)
                
                await actualizar_estado_staging(server, staging_id, {
                    'estado': ESTADO_PROCESADO,
                    'accion_realizada': ACCION_UPDATE,
                    'colaborador_id_destino': colab_match
                })
                resultado.total_actualizados += 1
                
            else:
                # Clasificación no procesable automáticamente
                await actualizar_estado_staging(server, staging_id, {
                    'estado': ESTADO_ERROR,
                    'accion_realizada': ACCION_SKIP,
                    'mensaje_error': f'Clasificación {clasificacion} no procesable automáticamente'
                })
                resultado.total_errores += 1
            
            resultado.total_procesados += 1
            
        except Exception as e:
            logger.error(f"Error procesando staging_id {staging_id}: {e}")
            resultado.errores.append({
                'staging_id': staging_id,
                'error': str(e)
            })
            resultado.total_errores += 1
            
            # Marcar como error en staging
            await actualizar_estado_staging(server, staging_id, {
                'estado': ESTADO_ERROR,
                'mensaje_error': str(e)
            })
    
    # Actualizar bitácora con resultados finales
    duracion = int(time.time() - inicio)
    await actualizar_bitacora(server, bitacora_id, {
        'total_registros_leidos': len(request.staging_ids),
        'total_insertados': resultado.total_insertados,
        'total_actualizados': resultado.total_actualizados,
        'total_errores': resultado.total_errores,
        'duracion_segundos': duracion,
        'estado': 'Completado' if resultado.total_errores == 0 else 'Parcial'
    })
    
    return resultado


# ============================================================================
# ENDPOINTS DE BITÁCORA
# ============================================================================

@router.get("/bitacora", summary="Ver historial de importaciones")
async def ver_bitacora(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """
    Lista el historial de importaciones ejecutadas con métricas.
    """
    server = await get_edarsa_hub_server()
    if not server:
        raise HTTPException(status_code=503, detail="Servidor EDARSA HUB no disponible")
    
    resultado = await listar_bitacora(server, limit, offset)
    
    if not resultado.get('success'):
        raise HTTPException(status_code=500, detail=resultado.get('error', 'Error listando bitácora'))
    
    return resultado
