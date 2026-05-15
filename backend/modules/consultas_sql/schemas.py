"""
EDARSA HUB - Consultas SQL: Schemas Request/Response
=====================================================
FASE 4: Schemas Pydantic para endpoints /api/consultas-sql/*

SEGURIDAD:
- No exponer SQL completo a usuarios normales
- No exponer credenciales
- Respuestas controladas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class CatalogoFiltrosRequest(BaseModel):
    """Filtros para listar consultas del catálogo."""
    sistema: Optional[str] = Field(None, description="Sistema: SOFTRESTAURANT, MPRO")
    modulo: Optional[str] = Field(None, description="Módulo: Ventas, Compras, etc.")
    activo: Optional[bool] = Field(True, description="Solo consultas activas")
    solo_lectura: Optional[bool] = Field(True, description="Solo consultas de solo lectura")
    buscar: Optional[str] = Field(None, description="Texto de búsqueda", max_length=100)
    limit: int = Field(100, ge=1, le=500, description="Límite de resultados")


class ValidarConsultaRequest(BaseModel):
    """Request para validar una consulta."""
    codigo_consulta: Optional[str] = Field(None, description="Código de la consulta")
    consulta_id: Optional[int] = Field(None, description="ID de la consulta")
    parametros: Optional[Dict[str, Any]] = Field(None, description="Parámetros a validar")


class EjecutarConsultaRequest(BaseModel):
    """Request para ejecutar una consulta."""
    codigo_consulta: Optional[str] = Field(None, description="Código de la consulta")
    consulta_id: Optional[int] = Field(None, description="ID de la consulta")
    servidor_id: str = Field(..., description="UUID del servidor destino")
    parametros: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Parámetros")
    limit: int = Field(1000, ge=1, le=10000, description="Límite de filas")


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class ConsultaCatalogoItem(BaseModel):
    """Item de consulta para listado del catálogo."""
    consulta_id: int
    codigo_consulta: str
    nombre: str
    descripcion: Optional[str] = None
    sistema: str
    sistema_tipo_id: int
    modulo: str
    activo: bool
    solo_lectura: bool
    version: int
    requiere_parametros: bool
    count_parametros: int
    permite_ejecucion_manual: bool
    fecha_actualizacion: Optional[str] = None


class ConsultaCatalogoListResponse(BaseModel):
    """Response para listado del catálogo."""
    success: bool
    total: int
    consultas: List[ConsultaCatalogoItem]
    filtros_aplicados: Dict[str, Any]


class ParametroDetalle(BaseModel):
    """Detalle de un parámetro."""
    nombre: str
    nombre_mostrar: Optional[str] = None
    tipo_dato: str
    requerido: bool
    valor_default: Optional[str] = None
    regex_validacion: Optional[str] = None
    valor_minimo: Optional[str] = None
    valor_maximo: Optional[str] = None
    orden: int


class ConsultaDetalleResponse(BaseModel):
    """Response para detalle de una consulta."""
    success: bool
    consulta_id: int
    codigo_consulta: str
    nombre: str
    descripcion: Optional[str] = None
    sistema: str
    modulo: str
    activo: bool
    solo_lectura: bool
    version: int
    parametros: List[ParametroDetalle]
    requiere_parametros: bool
    permite_ejecucion_manual: bool
    validacion_estado: str  # VALIDA, INVALIDA, PENDIENTE
    # SQL solo si tiene permiso especial (se omite por defecto)
    sql: Optional[str] = None  # Solo para administradores con permiso


class ValidacionResponse(BaseModel):
    """Response para validación de consulta."""
    success: bool
    is_valid: bool
    codigo_consulta: Optional[str] = None
    consulta_id: Optional[int] = None
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    parametros_detectados: List[str] = []
    timestamp: str


class EjecucionSource(BaseModel):
    """Información de origen de la ejecución."""
    type: str = "EDARSAHUB_SQL_CATALOGO"
    codigo_consulta: str
    servidor_id: str
    system_type: str
    generated_at: str


class EjecucionResponse(BaseModel):
    """Response para ejecución de consulta."""
    success: bool
    status: str  # SUCCESS, ERROR, VALIDATION_FAILED, PERMISSION_DENIED
    source: Optional[EjecucionSource] = None
    columns: List[str] = []
    rows: List[Dict[str, Any]] = []
    row_count: int = 0
    elapsed_ms: int = 0
    warnings: List[str] = []
    errors: List[str] = []


class SistemaItem(BaseModel):
    """Item de sistema."""
    sistema_tipo_id: int
    codigo: str
    nombre: str
    count_consultas: int


class SistemasResponse(BaseModel):
    """Response para listado de sistemas."""
    success: bool
    sistemas: List[SistemaItem]


class ModuloItem(BaseModel):
    """Item de módulo."""
    nombre: str
    count_consultas: int


class ModulosResponse(BaseModel):
    """Response para listado de módulos."""
    success: bool
    modulos: List[ModuloItem]


class ErrorResponse(BaseModel):
    """Response de error controlado."""
    success: bool = False
    error: str
    error_code: str
    details: Optional[Dict[str, Any]] = None


# ============================================================================
# FASE 4B: Schemas adicionales
# ============================================================================

class ValidarTextoRequest(BaseModel):
    """Request para validar texto SQL libre (solo Admin/SuperAdmin)."""
    sql_texto: str = Field(..., description="Texto SQL a validar", min_length=1, max_length=10000)


class ValidarTextoResponse(BaseModel):
    """Response para validación de texto SQL."""
    success: bool
    is_valid: bool
    sql_analizado: bool = True
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    parametros_detectados: List[str] = []
    timestamp: str


class VersionItem(BaseModel):
    """Item de versión de consulta."""
    version_id: int
    version: int
    motivo_cambio: Optional[str] = None
    fecha_creacion: str
    usuario_creacion: Optional[str] = None
    # SQL solo para SuperAdmin
    sql: Optional[str] = None


class VersionesResponse(BaseModel):
    """Response para listado de versiones."""
    success: bool
    codigo_consulta: str
    consulta_id: int
    total_versiones: int
    versiones: List[VersionItem]


class ServidorAsociadoItem(BaseModel):
    """Item de servidor asociado (sin datos sensibles)."""
    consulta_servidor_id: int
    servidor_id: str
    servidor_nombre: Optional[str] = None
    sistema_tipo: Optional[str] = None
    empresa_nombre: Optional[str] = None
    activo: bool
    prioridad: int


class ServidoresAsociadosResponse(BaseModel):
    """Response para listado de servidores asociados."""
    success: bool
    codigo_consulta: str
    consulta_id: int
    total_servidores: int
    servidores: List[ServidorAsociadoItem]
