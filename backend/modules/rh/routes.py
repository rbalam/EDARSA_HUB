"""
EDARSA HUB - RH Routes
======================
Endpoints del módulo de Recursos Humanos.

FASE 6B DEL REFACTOR MODULAR (Diciembre 2025):
Catálogos migrados desde server.py:
- GET    /rrhh/catalogos/puestos
- POST   /rrhh/catalogos/puestos
- PUT    /rrhh/catalogos/puestos/{puesto_id}
- DELETE /rrhh/catalogos/puestos/{puesto_id}
- GET    /rrhh/catalogos/sucursales
- GET    /rrhh/catalogos/tipos-incidencias
- POST   /rrhh/catalogos/tipos-incidencias
- PUT    /rrhh/catalogos/tipos-incidencias/{tipo_id}
- DELETE /rrhh/catalogos/tipos-incidencias/{tipo_id}
- GET    /rrhh/catalogos/script-inicializacion

FASE 6C-B DEL REFACTOR MODULAR (Diciembre 2025):
Colaboradores migrados desde server.py:
- GET    /rrhh/colaboradores
- GET    /rrhh/colaboradores/{colaborador_id}
- POST   /rrhh/colaboradores
- PUT    /rrhh/colaboradores/{colaborador_id}
- DELETE /rrhh/colaboradores/{colaborador_id}

FASE 6D-B DEL REFACTOR MODULAR (Diciembre 2025):
Incidencias migradas desde server.py:
- GET    /rrhh/incidencias
- POST   /rrhh/incidencias
- POST   /rrhh/incidencias/importar-excel
- GET    /rrhh/incidencias/plantilla-excel

FASE 6E-B DEL REFACTOR MODULAR (Diciembre 2025):
Asistencia migrada desde server.py:
- GET    /rrhh/asistencia
- POST   /rrhh/asistencia
- PUT    /rrhh/asistencia/{check_id}/validar

FASE 6F-B DEL REFACTOR MODULAR (Diciembre 2025):
Flujo Nómina migrado desde server.py:
- GET    /rrhh/nominas/flujo
- POST   /rrhh/nominas/flujo
- PUT    /rrhh/nominas/flujo/{flujo_id}/enviar-rh
- PUT    /rrhh/nominas/flujo/{flujo_id}/validar-gerente
- PUT    /rrhh/nominas/flujo/{flujo_id}/autorizar-dg
- PUT    /rrhh/nominas/flujo/{flujo_id}/enviar-tesoreria
- PUT    /rrhh/nominas/flujo/{flujo_id}/marcar-pagado

CONTRATOS MANTENIDOS:
- Prefijo: /rrhh/ (NO /rh/)
- Formatos de respuesta idénticos a los originales
- Compatibilidad total con frontend existente

SEGURIDAD:
- Validación de datos con Pydantic
- Validación de tipos de incidencia contra catálogo RH_Cat_Tipos_Incidencias
- Validación de tipo_registro de asistencia (Entrada/Salida)
- Validación de transiciones de estado en flujo de nómina
- Queries parametrizados nativos en repository
"""

from fastapi import APIRouter, Depends, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Dict, Optional
from io import BytesIO

from core.security import get_current_user
from modules.rh.service import rh_catalogos_service, rh_colaboradores_service, rh_incidencias_service
from modules.rh.schemas import (
    PuestoCreate,
    PuestoUpdate,
    TipoIncidenciaCreate,
    TipoIncidenciaUpdate,
    PuestosListResponse,
    SucursalesListResponse,
    TiposIncidenciasListResponse,
    SuccessResponse,
    SuccessWithIdResponse,
    ScriptInicializacionResponse,
    ColaboradorCreate,
    ColaboradorUpdate,
    ColaboradoresListResponse,
    ColaboradorDetalleResponse,
    IncidenciaCreate,
    IncidenciasListResponse,
    ImportacionExcelResponse,
)


# Router con prefijo /rrhh para mantener compatibilidad
router = APIRouter(prefix="/rrhh", tags=["Recursos Humanos"])


# ============================================================================
# ENDPOINTS DE PUESTOS
# ============================================================================

@router.get("/catalogos/puestos")
async def rrhh_listar_puestos(
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista catálogo de puestos desde RH_Cat_Puestos.
    
    Requiere autenticación.
    """
    return await rh_catalogos_service.listar_puestos()


@router.post("/catalogos/puestos", response_model=SuccessResponse)
async def rrhh_crear_puesto(
    body: PuestoCreate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Crea un nuevo puesto en el catálogo.
    
    Requiere rol: Administrador
    """
    return await rh_catalogos_service.crear_puesto(body, current_user)


@router.put("/catalogos/puestos/{puesto_id}", response_model=SuccessResponse)
async def rrhh_actualizar_puesto(
    puesto_id: int,
    body: PuestoUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Actualiza un puesto existente.
    
    Requiere rol: Administrador
    """
    return await rh_catalogos_service.actualizar_puesto(puesto_id, body, current_user)


@router.delete("/catalogos/puestos/{puesto_id}", response_model=SuccessResponse)
async def rrhh_eliminar_puesto(
    puesto_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """
    Elimina un puesto del catálogo.
    
    Requiere rol: Administrador.
    Falla si hay colaboradores asignados al puesto.
    """
    return await rh_catalogos_service.eliminar_puesto(puesto_id, current_user)


# ============================================================================
# ENDPOINTS DE SUCURSALES
# ============================================================================

@router.get("/catalogos/sucursales")
async def rrhh_listar_sucursales(
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista catálogo de sucursales desde RH_Cat_Sucursales.
    
    Incluye datos fiscales de RH_Cat_SucursalesFiscal.
    Requiere autenticación.
    """
    return await rh_catalogos_service.listar_sucursales()


# ============================================================================
# ENDPOINTS DE TIPOS DE INCIDENCIAS
# ============================================================================

@router.get("/catalogos/tipos-incidencias")
async def rrhh_listar_tipos_incidencias(
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista catálogo de tipos de incidencias activos.
    
    Si la tabla no existe, retorna tipos por defecto con nota explicativa.
    Requiere autenticación.
    """
    return await rh_catalogos_service.listar_tipos_incidencias()


@router.post("/catalogos/tipos-incidencias", response_model=SuccessResponse)
async def rrhh_crear_tipo_incidencia(
    body: TipoIncidenciaCreate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Crea un nuevo tipo de incidencia.
    
    Requiere rol: Administrador
    """
    return await rh_catalogos_service.crear_tipo_incidencia(body, current_user)


@router.put("/catalogos/tipos-incidencias/{tipo_id}", response_model=SuccessResponse)
async def rrhh_actualizar_tipo_incidencia(
    tipo_id: int,
    body: TipoIncidenciaUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Actualiza un tipo de incidencia existente.
    
    Requiere rol: Administrador
    """
    return await rh_catalogos_service.actualizar_tipo_incidencia(tipo_id, body, current_user)


@router.delete("/catalogos/tipos-incidencias/{tipo_id}", response_model=SuccessResponse)
async def rrhh_eliminar_tipo_incidencia(
    tipo_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """
    Desactiva un tipo de incidencia (soft delete para mantener histórico).
    
    Requiere rol: Administrador
    """
    return await rh_catalogos_service.eliminar_tipo_incidencia(tipo_id, current_user)


# ============================================================================
# ENDPOINT DE UTILIDAD - SCRIPT INICIALIZACIÓN
# ============================================================================

@router.get("/catalogos/script-inicializacion")
async def rrhh_catalogos_script(
    current_user: Dict = Depends(get_current_user)
):
    """
    Retorna el script SQL para crear/actualizar las tablas de catálogos RRHH.
    
    Incluye instrucciones de uso y compatibilidad con NomiPAQ, MPRO y Excel.
    Requiere autenticación.
    """
    return rh_catalogos_service.obtener_script_inicializacion()


# ============================================================================
# ENDPOINTS DE COLABORADORES (FASE 6C-B)
# ============================================================================

@router.get("/colaboradores")
async def rrhh_listar_colaboradores(
    sucursal_id: Optional[int] = None,
    puesto_id: Optional[int] = None,
    estatus: Optional[str] = None,
    buscar: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista colaboradores con filtros opcionales y paginación.
    
    Parámetros de filtro:
    - sucursal_id: Filtrar por sucursal
    - puesto_id: Filtrar por puesto
    - estatus: Filtrar por estatus laboral (Activo, Baja, Vacaciones, etc.)
    - buscar: Búsqueda por nombre, RFC o CURP
    
    Paginación:
    - page: Número de página (default 1)
    - limit: Registros por página (default 50, max 200)
    
    Requiere autenticación.
    """
    return await rh_colaboradores_service.listar_colaboradores(
        sucursal_id=sucursal_id,
        puesto_id=puesto_id,
        estatus=estatus,
        buscar=buscar,
        page=page,
        limit=limit
    )


@router.get("/colaboradores/{colaborador_id}")
async def rrhh_obtener_colaborador(
    colaborador_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene detalle de un colaborador con incidencias, asistencias y auditoría.
    
    Incluye:
    - Datos del colaborador
    - Últimas 20 incidencias
    - Últimos 30 registros de asistencia
    - Últimas 10 auditorías fiscales
    
    Requiere autenticación.
    """
    return await rh_colaboradores_service.obtener_colaborador_detalle(colaborador_id)


@router.post("/colaboradores", response_model=SuccessWithIdResponse)
async def rrhh_crear_colaborador(
    body: ColaboradorCreate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Crea un nuevo colaborador.
    
    Campos requeridos:
    - nombre_completo: Nombre del colaborador
    - sucursal_id: ID de sucursal asignada
    - puesto_id: ID de puesto asignado
    
    Campos opcionales con validación:
    - curp: 18 caracteres, formato CURP válido
    - rfc: 12-13 caracteres, formato RFC válido
    - clabe_bancaria: 18 dígitos
    - estatus_laboral: Activo, Baja, Vacaciones, Incapacidad, Permiso, Suspendido
    
    Requiere autenticación.
    """
    return await rh_colaboradores_service.crear_colaborador(body)


@router.put("/colaboradores/{colaborador_id}", response_model=SuccessResponse)
async def rrhh_actualizar_colaborador(
    colaborador_id: int,
    body: ColaboradorUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Actualiza datos de un colaborador existente.
    
    Todos los campos son opcionales. Solo se actualizan los proporcionados.
    Se aplican las mismas validaciones que en creación.
    
    Requiere autenticación.
    """
    return await rh_colaboradores_service.actualizar_colaborador(colaborador_id, body)


@router.delete("/colaboradores/{colaborador_id}", response_model=SuccessResponse)
async def rrhh_dar_baja_colaborador(
    colaborador_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """
    Da de baja lógica a un colaborador.
    
    Establece Colaborador_Activo = 0 y Estatus_Laboral = 'Baja'.
    No elimina el registro (soft delete para mantener histórico).
    
    Requiere autenticación.
    """
    return await rh_colaboradores_service.dar_baja_colaborador(colaborador_id)



# ============================================================================
# ENDPOINTS DE INCIDENCIAS (FASE 6D-B)
# ============================================================================

@router.get("/incidencias")
async def rrhh_listar_incidencias(
    colaborador_id: Optional[int] = None,
    tipo: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    sucursal_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista incidencias con filtros opcionales y paginación.
    
    Parámetros de filtro:
    - colaborador_id: Filtrar por colaborador
    - tipo: Filtrar por tipo de incidencia
    - fecha_desde: Fecha inicial (YYYY-MM-DD)
    - fecha_hasta: Fecha final (YYYY-MM-DD)
    - sucursal_id: Filtrar por sucursal del colaborador
    
    Paginación:
    - page: Número de página (default 1)
    - limit: Registros por página (default 50, max 200)
    
    Requiere autenticación.
    """
    return await rh_incidencias_service.listar_incidencias(
        colaborador_id=colaborador_id,
        tipo=tipo,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        sucursal_id=sucursal_id,
        page=page,
        limit=limit
    )


@router.post("/incidencias")
async def rrhh_crear_incidencia(
    body: IncidenciaCreate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Crea una nueva incidencia.
    
    Campos requeridos:
    - colaborador_id: ID del colaborador
    - tipo_incidencia: Tipo (validado contra catálogo RH_Cat_Tipos_Incidencias)
    - fecha_incidencia: Fecha (YYYY-MM-DD)
    
    Campos opcionales:
    - monto: Monto de la incidencia (>= 0)
    - unidades: Unidades (horas, días, etc.) (>= 0)
    
    Requiere autenticación.
    """
    return await rh_incidencias_service.crear_incidencia(body, current_user)


@router.post("/incidencias/importar-excel", response_model=ImportacionExcelResponse)
async def rrhh_importar_incidencias_excel(
    file: UploadFile = File(...),
    current_user: Dict = Depends(get_current_user)
):
    """
    Importa incidencias desde un archivo Excel.
    
    COMPORTAMIENTO DOCUMENTADO:
    - La importación es PARCIAL, NO transaccional
    - Si una fila falla, las anteriores ya fueron insertadas
    - La respuesta incluye lista de errores (max 20) y total de errores
    
    Formato esperado del Excel:
    - Columna A: RFC o ColaboradorID
    - Columna B: Tipo de Incidencia (validado contra catálogo)
    - Columna C: Fecha (YYYY-MM-DD o DD/MM/YYYY)
    - Columna D: Monto (opcional)
    - Columna E: Unidades (opcional)
    
    Requiere autenticación.
    """
    contents = await file.read()
    return await rh_incidencias_service.importar_desde_excel(contents, file.filename)


@router.get("/incidencias/plantilla-excel")
async def rrhh_plantilla_incidencias_excel(
    current_user: Dict = Depends(get_current_user)
):
    """
    Descarga una plantilla Excel para importar incidencias.
    
    La plantilla incluye:
    - Hoja 'Incidencias': Estructura de datos con ejemplos
    - Hoja 'Tipos Válidos': Lista de tipos de incidencia aceptados
    
    Requiere autenticación.
    """
    excel_bytes = rh_incidencias_service.generar_plantilla_excel()
    
    return StreamingResponse(
        BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=plantilla_incidencias.xlsx"
        }
    )


# ============================================================================
# ENDPOINTS DE ASISTENCIA (FASE 6E-B)
# ============================================================================
# Migrados desde server.py manteniendo el mismo contrato de API.
#
# TABLAS REUTILIZADAS:
# - RH_Reloj_Checador
# - RH_Colaboradores_Expediente
# - RH_Cat_Sucursales
# - RH_Cat_Puestos
#
# LÓGICA DE NEGOCIO INTACTA:
# - NO se validan duplicados de entrada/salida en el mismo día
# - Geolocalización opcional sin formato forzado
# ============================================================================

from modules.rh.service import rh_asistencia_service
from modules.rh.schemas import (
    AsistenciaCreate,
    AsistenciasListResponse,
)


@router.get("/asistencia")
async def rrhh_listar_asistencias(
    colaborador_id: Optional[int] = None,
    sucursal_id: Optional[int] = None,
    fecha: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500),
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista registros del reloj checador con filtros opcionales y paginación.
    
    Parámetros de filtro:
    - colaborador_id: Filtrar por colaborador
    - sucursal_id: Filtrar por sucursal
    - fecha: Fecha específica (YYYY-MM-DD)
    - fecha_desde: Fecha inicial (YYYY-MM-DD)
    - fecha_hasta: Fecha final (YYYY-MM-DD)
    
    Paginación:
    - page: Número de página (default 1)
    - limit: Registros por página (default 100, max 500)
    
    Requiere autenticación.
    """
    return await rh_asistencia_service.listar_asistencias(
        colaborador_id=colaborador_id,
        sucursal_id=sucursal_id,
        fecha=fecha,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        page=page,
        limit=limit
    )


@router.post("/asistencia")
async def rrhh_registrar_asistencia(
    body: AsistenciaCreate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Registra una entrada o salida.
    
    Campos requeridos:
    - colaborador_id: ID del colaborador
    - tipo_registro: "Entrada" o "Salida" (validado)
    
    Campos opcionales:
    - geolocalizacion: Coordenadas GPS (sin formato forzado)
    
    LÓGICA DE NEGOCIO:
    - NO se validan duplicados de entrada/salida en el mismo día
    - Validado_Gerencia se inicializa en 0 (pendiente)
    
    Requiere autenticación.
    """
    return await rh_asistencia_service.registrar_asistencia(body)


@router.put("/asistencia/{check_id}/validar")
async def rrhh_validar_asistencia(
    check_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """
    Valida un registro de asistencia (gerencia).
    
    Establece Validado_Gerencia = 1 para el registro especificado.
    
    Requiere autenticación.
    """
    return await rh_asistencia_service.validar_asistencia(check_id)



# ============================================================================
# ENDPOINTS DE FLUJO NÓMINA (FASE 6F-B)
# ============================================================================
# Migrados desde server.py manteniendo el mismo contrato de API.
#
# TABLAS REUTILIZADAS:
# - RH_Flujo_Nomina_Sucursal
# - RH_Cat_Sucursales
#
# VALIDACIÓN DE TRANSICIONES:
# - Se valida que la transición de estado sea permitida
# - Previene saltos de estado absurdos (ej: Captura → Pagado)
#
# FLUJO DE ESTADOS:
# Captura → Enviado_RH → Validacion_Gerente → Autorizacion_DG → Enviado_Tesoreria → Pagado
#                  ↓
#            Rechazado_Gerente (puede reenviar)
# ============================================================================

from modules.rh.service import rh_flujo_nomina_service
from modules.rh.schemas import (
    FlujoNominaCreate,
    FlujoNominaListResponse,
    ValidacionGerenteRequest,
    ESTATUS_FLUJO_NOMINA,
)


@router.get("/nominas/flujo")
async def rrhh_listar_flujos_nomina(
    sucursal_id: Optional[int] = None,
    semana_anio: Optional[int] = None,
    estatus: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista flujos de nómina por sucursal con filtros opcionales.
    
    Parámetros de filtro:
    - sucursal_id: Filtrar por sucursal
    - semana_anio: Filtrar por semana/año (formato YYYYWW, ej: 202614)
    - estatus: Filtrar por estatus del flujo
    
    Estatus válidos:
    - Captura, Enviado_RH, Validacion_Gerente, Rechazado_Gerente,
      Autorizacion_DG, Enviado_Tesoreria, Pagado
    
    Requiere autenticación.
    """
    return await rh_flujo_nomina_service.listar_flujos(
        sucursal_id=sucursal_id,
        semana_anio=semana_anio,
        estatus=estatus
    )


@router.post("/nominas/flujo")
async def rrhh_crear_flujo_nomina(
    body: FlujoNominaCreate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Crea un nuevo periodo de nómina para una sucursal.
    
    Campos requeridos:
    - sucursal_id: ID de la sucursal
    - semana_anio: Semana y año en formato YYYYWW (ej: 202614)
    
    Validaciones:
    - No permite crear duplicados para la misma sucursal+semana
    - El flujo se crea en estatus 'Captura'
    
    Requiere autenticación.
    """
    return await rh_flujo_nomina_service.crear_flujo(body)


@router.put("/nominas/flujo/{flujo_id}/enviar-rh")
async def rrhh_enviar_nomina_rh(
    flujo_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """
    Marca la nómina como enviada a RH.
    
    Transiciones permitidas:
    - Captura → Enviado_RH
    - Rechazado_Gerente → Enviado_RH (reenvío después de corrección)
    
    Requiere autenticación.
    """
    return await rh_flujo_nomina_service.enviar_a_rh(flujo_id)


@router.put("/nominas/flujo/{flujo_id}/validar-gerente")
async def rrhh_validar_nomina_gerente(
    flujo_id: int,
    body: ValidacionGerenteRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Validación o rechazo de nómina por gerente.
    
    Campos:
    - aprobado: True para aprobar, False para rechazar
    - motivo_rechazo: Obligatorio si aprobado=False
    
    Transiciones:
    - Si aprobado=True: Enviado_RH → Validacion_Gerente
    - Si aprobado=False: Enviado_RH → Rechazado_Gerente (incrementa intentos)
    
    Requiere autenticación.
    """
    return await rh_flujo_nomina_service.validar_gerente(flujo_id, body)


@router.put("/nominas/flujo/{flujo_id}/autorizar-dg")
async def rrhh_autorizar_nomina_dg(
    flujo_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """
    Autorización de nómina por Dirección General.
    
    Transición: Validacion_Gerente → Autorizacion_DG
    
    Requiere autenticación.
    """
    return await rh_flujo_nomina_service.autorizar_dg(flujo_id)


@router.put("/nominas/flujo/{flujo_id}/enviar-tesoreria")
async def rrhh_enviar_nomina_tesoreria(
    flujo_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """
    Envía nómina a tesorería para pago.
    
    Transición: Autorizacion_DG → Enviado_Tesoreria
    
    Requiere autenticación.
    """
    return await rh_flujo_nomina_service.enviar_tesoreria(flujo_id)


@router.put("/nominas/flujo/{flujo_id}/marcar-pagado")
async def rrhh_marcar_nomina_pagada(
    flujo_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """
    Marca la nómina como pagada.
    
    Transición: Enviado_Tesoreria → Pagado (estado final)
    
    Requiere autenticación.
    """
    return await rh_flujo_nomina_service.marcar_pagado(flujo_id)