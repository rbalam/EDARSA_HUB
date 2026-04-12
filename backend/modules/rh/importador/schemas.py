"""
EDARSA HUB - Schemas de Importación RH
======================================
Modelos Pydantic para el proceso de importación controlada de empleados.

Incluye:
- Modelos para staging
- Modelos para bitácora
- Modelos para clasificación y preview
- Constantes de estados y clasificaciones
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# CONSTANTES DE CLASIFICACIÓN
# ============================================================================

CLASIFICACION_NUEVO = "nuevo"
CLASIFICACION_ACTUALIZAR = "actualizar"
CLASIFICACION_DUPLICADO_PROBABLE = "duplicado_probable"
CLASIFICACION_INCOMPLETO = "incompleto"
CLASIFICACION_RECHAZADO = "rechazado"

CLASIFICACIONES_VALIDAS = [
    CLASIFICACION_NUEVO,
    CLASIFICACION_ACTUALIZAR,
    CLASIFICACION_DUPLICADO_PROBABLE,
    CLASIFICACION_INCOMPLETO,
    CLASIFICACION_RECHAZADO,
]

# Estados del registro en staging
ESTADO_PENDIENTE = "Pendiente"
ESTADO_VALIDADO = "Validado"
ESTADO_APROBADO = "Aprobado"
ESTADO_PROCESADO = "Procesado"
ESTADO_ERROR = "Error"
ESTADO_RECHAZADO = "Rechazado"

ESTADOS_STAGING_VALIDOS = [
    ESTADO_PENDIENTE,
    ESTADO_VALIDADO,
    ESTADO_APROBADO,
    ESTADO_PROCESADO,
    ESTADO_ERROR,
    ESTADO_RECHAZADO,
]

# Acciones realizadas
ACCION_INSERT = "INSERT"
ACCION_UPDATE = "UPDATE"
ACCION_SKIP = "SKIP"
ACCION_ERROR = "ERROR"

# Niveles de confianza para deduplicación
CONFIANZA_ALTA = "alta"       # Match por CURP
CONFIANZA_MEDIA = "media"     # Match por RFC
CONFIANZA_BAJA = "baja"       # Match por Num_Empleado
CONFIANZA_MUY_BAJA = "muy_baja"  # Match por Nombre+Sucursal
CONFIANZA_REVISION = "revision"  # Coincidencia parcial


# ============================================================================
# SCHEMAS DE STAGING
# ============================================================================

class ImportacionStagingCreate(BaseModel):
    """Modelo para crear un registro en staging de importación."""
    
    # Datos del empleado
    nombre_completo: str = Field(..., min_length=2, max_length=200)
    curp: Optional[str] = Field(None, max_length=18)
    rfc: Optional[str] = Field(None, max_length=13)
    clabe_bancaria: Optional[str] = Field(None, max_length=18)
    numero_empleado_externo: Optional[str] = Field(None, max_length=50)
    
    # Datos de catálogo (pueden venir como texto y luego resolverse)
    sucursal_nombre: Optional[str] = Field(None, max_length=100)
    sucursal_id: Optional[int] = None
    puesto_nombre: Optional[str] = Field(None, max_length=100)
    puesto_id: Optional[int] = None
    area_departamento: Optional[str] = Field(None, max_length=100)
    
    # Datos adicionales del Excel
    sexo: Optional[str] = Field(None, max_length=1)
    edad: Optional[int] = None
    antiguedad: Optional[str] = Field(None, max_length=50)
    sueldo_diario: Optional[float] = None
    metodo_pago: Optional[str] = Field(None, max_length=50)
    
    # Metadatos de importación (OBLIGATORIOS para trazabilidad)
    fuente: str = Field(..., description="Origen: Excel_CF, MPro_Origen, MPro_QRO")
    archivo_origen: Optional[str] = Field(None, max_length=255)
    linea_origen: Optional[int] = Field(None, description="Línea en Excel o ID en BD origen")
    
    @field_validator('nombre_completo')
    @classmethod
    def nombre_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('El nombre completo es requerido')
        return v.strip().upper()
    
    @field_validator('curp')
    @classmethod
    def curp_normalize(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == '':
            return None
        return v.strip().upper()
    
    @field_validator('rfc')
    @classmethod
    def rfc_normalize(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == '':
            return None
        return v.strip().upper()
    
    @field_validator('sexo')
    @classmethod
    def sexo_normalize(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == '':
            return None
        v = v.strip().upper()
        if v in ['M', 'MASCULINO', 'HOMBRE', 'H']:
            return 'M'
        if v in ['F', 'FEMENINO', 'MUJER']:
            return 'F'
        return v[0] if v else None


class ImportacionStagingResponse(BaseModel):
    """Respuesta de un registro en staging."""
    
    staging_id: int
    nombre_completo: str
    curp: Optional[str] = None
    rfc: Optional[str] = None
    clabe_bancaria: Optional[str] = None
    numero_empleado_externo: Optional[str] = None
    
    sucursal_nombre: Optional[str] = None
    sucursal_id: Optional[int] = None
    puesto_nombre: Optional[str] = None
    puesto_id: Optional[int] = None
    area_departamento: Optional[str] = None
    
    # Metadatos de importación
    fuente: str
    archivo_origen: Optional[str] = None
    linea_origen: Optional[int] = None
    fecha_importacion: datetime
    usuario_importador: Optional[str] = None
    
    # Estado del procesamiento
    estado: str = ESTADO_PENDIENTE
    clasificacion: Optional[str] = None
    nivel_confianza: Optional[str] = None
    accion_realizada: Optional[str] = None
    colaborador_id_destino: Optional[int] = None
    colaborador_id_match: Optional[int] = None  # ID del posible duplicado
    mensaje_error: Optional[str] = None
    observaciones: Optional[str] = None


class ImportacionStagingUpdate(BaseModel):
    """Modelo para actualizar estado de un registro en staging."""
    
    estado: Optional[str] = None
    clasificacion: Optional[str] = None
    nivel_confianza: Optional[str] = None
    accion_realizada: Optional[str] = None
    colaborador_id_destino: Optional[int] = None
    colaborador_id_match: Optional[int] = None
    mensaje_error: Optional[str] = None
    observaciones: Optional[str] = None
    
    # También permite corregir datos antes de aprobar
    sucursal_id: Optional[int] = None
    puesto_id: Optional[int] = None
    
    @field_validator('estado')
    @classmethod
    def estado_valido(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ESTADOS_STAGING_VALIDOS:
            raise ValueError(f'Estado debe ser uno de: {", ".join(ESTADOS_STAGING_VALIDOS)}')
        return v
    
    @field_validator('clasificacion')
    @classmethod
    def clasificacion_valida(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in CLASIFICACIONES_VALIDAS:
            raise ValueError(f'Clasificación debe ser una de: {", ".join(CLASIFICACIONES_VALIDAS)}')
        return v


# ============================================================================
# SCHEMAS DE BITÁCORA
# ============================================================================

class ImportacionBitacoraCreate(BaseModel):
    """Modelo para crear un registro en la bitácora de importaciones."""
    
    fuente: str
    archivo_origen: Optional[str] = None
    total_registros_leidos: int = 0
    total_insertados: int = 0
    total_actualizados: int = 0
    total_duplicados_omitidos: int = 0
    total_incompletos: int = 0
    total_errores: int = 0
    usuario_ejecutor: Optional[str] = None
    duracion_segundos: Optional[int] = None
    estado: str = "En Proceso"
    detalle_json: Optional[Dict[str, Any]] = None


class ImportacionBitacoraResponse(BaseModel):
    """Respuesta de un registro en la bitácora."""
    
    bitacora_id: int
    fecha_ejecucion: datetime
    fuente: str
    archivo_origen: Optional[str] = None
    total_registros_leidos: int
    total_insertados: int
    total_actualizados: int
    total_duplicados_omitidos: int
    total_incompletos: int
    total_errores: int
    usuario_ejecutor: Optional[str] = None
    duracion_segundos: Optional[int] = None
    estado: str
    detalle_json: Optional[Dict[str, Any]] = None


# ============================================================================
# SCHEMAS DE VALIDACIÓN Y PREVIEW
# ============================================================================

class ResultadoValidacion(BaseModel):
    """Resultado de validación de un campo específico."""
    
    campo: str
    valor_original: Optional[str] = None
    valor_normalizado: Optional[str] = None
    es_valido: bool
    mensaje: Optional[str] = None
    advertencia: Optional[str] = None


class ClasificacionRegistro(BaseModel):
    """Clasificación de un registro para el preview."""
    
    staging_id: Optional[int] = None
    linea_origen: int
    nombre_completo: str
    curp: Optional[str] = None
    rfc: Optional[str] = None
    
    clasificacion: str
    nivel_confianza: Optional[str] = None
    razon: str
    
    # Si hay match existente
    colaborador_existente_id: Optional[int] = None
    colaborador_existente_nombre: Optional[str] = None
    campos_diferentes: Optional[List[str]] = None
    
    # Validaciones
    validaciones: List[ResultadoValidacion] = []
    es_valido_para_carga: bool = False


class PreviewImportacion(BaseModel):
    """Preview completo de una importación antes de confirmar."""
    
    archivo_origen: str
    fuente: str
    fecha_preview: datetime
    usuario: Optional[str] = None
    
    # Contadores por clasificación
    total_registros: int = 0
    total_nuevos: int = 0
    total_actualizar: int = 0
    total_duplicados_probables: int = 0
    total_incompletos: int = 0
    total_rechazados: int = 0
    
    # Detalle de registros
    registros_nuevos: List[ClasificacionRegistro] = []
    registros_actualizar: List[ClasificacionRegistro] = []
    registros_duplicados_probables: List[ClasificacionRegistro] = []
    registros_incompletos: List[ClasificacionRegistro] = []
    registros_rechazados: List[ClasificacionRegistro] = []
    
    # Resumen de validaciones
    errores_globales: List[str] = []
    advertencias_globales: List[str] = []


# ============================================================================
# SCHEMAS DE REQUEST/RESPONSE PARA ENDPOINTS
# ============================================================================

class UploadExcelRequest(BaseModel):
    """Request para subir archivo Excel."""
    
    fuente: str = Field(default="Excel_CF", description="Identificador de la fuente")
    hoja_nombre: Optional[str] = Field(None, description="Nombre de la hoja a procesar")
    fila_inicio: int = Field(default=1, description="Fila donde inician los datos (1-indexed)")


class ConfirmarCargaRequest(BaseModel):
    """Request para confirmar carga de registros en staging."""
    
    staging_ids: List[int] = Field(..., description="IDs de staging a aprobar y cargar")
    usuario_aprobador: str = Field(..., description="Usuario que aprueba la carga")


class ConfirmarCargaResponse(BaseModel):
    """Respuesta de la confirmación de carga."""
    
    total_procesados: int = 0
    total_insertados: int = 0
    total_actualizados: int = 0
    total_errores: int = 0
    errores: List[Dict[str, Any]] = []
    bitacora_id: Optional[int] = None


class FiltrosStaging(BaseModel):
    """Filtros para listar staging."""
    
    estado: Optional[str] = None
    clasificacion: Optional[str] = None
    fuente: Optional[str] = None
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None
    solo_pendientes: bool = False
