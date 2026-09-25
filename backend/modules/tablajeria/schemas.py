from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - Tablajería Schemas
===============================
Modelos Pydantic para el módulo de Tablajería.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


# ============================================================
# ENUMS
# ============================================================

class OrigenPlantilla(str, Enum):
    LEGACY_CIENFUEGOS_TABLAJERIA = "LEGACY_CIENFUEGOS_TABLAJERIA"
    LEGACY_MPRO_TABLAJERIA = "LEGACY_MPRO_TABLAJERIA"
    LEGACY_130_MERIDA_TABLAJERIA = "LEGACY_130_MERIDA_TABLAJERIA"
    CAPTURA_DIRECTA_EDARSAHUB = "CAPTURA_DIRECTA_EDARSAHUB"
    IMPORTACION_EXCEL = "IMPORTACION_EXCEL"
    API_EXTERNA = "API_EXTERNA"


class EstatusPlantilla(str, Enum):
    BORRADOR = "BORRADOR"
    SINCRONIZADA = "SINCRONIZADA"
    PENDIENTE_VALIDACION = "PENDIENTE_VALIDACION"
    VALIDADA = "VALIDADA"
    PUBLICADA = "PUBLICADA"
    OBSERVADA = "OBSERVADA"
    INACTIVA = "INACTIVA"
    REEMPLAZADA = "REEMPLAZADA"


class TipoDerivado(str, Enum):
    PRINCIPAL = "PRINCIPAL"
    SUBPRODUCTO = "SUBPRODUCTO"
    MERMA = "MERMA"
    DESPERDICIO = "DESPERDICIO"


class EstatusOrden(str, Enum):
    BORRADOR = "BORRADOR"
    PLANEADA = "PLANEADA"
    EN_EJECUCION = "EN_EJECUCION"
    PENDIENTE_AUTORIZACION = "PENDIENTE_AUTORIZACION"
    CERRADA = "CERRADA"
    CANCELADA = "CANCELADA"
    REVERTIDA = "REVERTIDA"


class TipoMerma(str, Enum):
    HUESO = "HUESO"
    GRASA = "GRASA"
    DESPERDICIO = "DESPERDICIO"
    EVAPORACION = "EVAPORACION"
    OTRO = "OTRO"


class ReglaCosteo(str, Enum):
    PROPORCIONAL = "PROPORCIONAL"
    FIJO = "FIJO"
    RESIDUAL = "RESIDUAL"


# ============================================================
# PLANTILLAS
# ============================================================

class PlantillaDetalleBase(BaseModel):
    producto_derivado_codigo: Optional[str] = None
    producto_derivado_nombre: str
    tipo_derivado: TipoDerivado = TipoDerivado.PRINCIPAL
    unidad_derivado_codigo: Optional[str] = None
    sku_kg_codigo: Optional[str] = None
    sku_pieza_codigo: Optional[str] = None
    gramaje_pieza_g: Optional[Decimal] = None
    captura_por_piezas: bool = False
    costo_fijo: bool = False
    costo_fijo_unitario: Optional[Decimal] = None
    prorratea_costo: bool = True
    cantidad_esperada: Decimal
    porcentaje_rendimiento_esperado: Optional[Decimal] = None
    porcentaje_costo_asignado: Optional[Decimal] = None
    es_merma: bool = False
    es_subproducto: bool = False
    es_producto_vendible: bool = True
    es_inventariable: bool = True
    orden_visual: int = 0
    observaciones: Optional[str] = None


class PlantillaDetalleCreate(PlantillaDetalleBase):
    pass


class PlantillaDetalle(PlantillaDetalleBase):
    plantilla_detalle_id: str
    plantilla_id: str
    producto_derivado_id: Optional[int] = None
    activo: bool = True

    class Config:
        from_attributes = True


class PlantillaBase(BaseModel):
    codigo_plantilla: str
    nombre_plantilla: str
    descripcion: Optional[str] = None
    tipo_transformacion: Optional[str] = "TABLAJERIA"
    insumo_base_codigo: Optional[str] = None
    insumo_base_nombre: Optional[str] = None
    unidad_base_codigo: Optional[str] = None
    cantidad_base_estandar: Decimal = Decimal("1")
    rendimiento_esperado_porcentaje: Optional[Decimal] = None
    merma_esperada_porcentaje: Optional[Decimal] = None
    tolerancia_rendimiento: Optional[Decimal] = Decimal("5.00")
    regla_costeo: ReglaCosteo = ReglaCosteo.PROPORCIONAL


class PlantillaCreate(PlantillaBase):
    empresa_id: str
    unidad_negocio_pk: Optional[str] = None
    sucursal_id: Optional[int] = None
    detalles: List[PlantillaDetalleCreate] = []


class PlantillaUpdate(BaseModel):
    nombre_plantilla: Optional[str] = None
    descripcion: Optional[str] = None
    rendimiento_esperado_porcentaje: Optional[Decimal] = None
    merma_esperada_porcentaje: Optional[Decimal] = None
    tolerancia_rendimiento: Optional[Decimal] = None
    regla_costeo: Optional[ReglaCosteo] = None
    estatus: Optional[EstatusPlantilla] = None
    detalles: Optional[List[PlantillaDetalleCreate]] = None


class PlantillaDuplicateRequest(BaseModel):
    codigo_plantilla: Optional[str] = None
    nombre_plantilla: Optional[str] = None
    descripcion: Optional[str] = None
    motivo_version: Optional[str] = None


class Plantilla(PlantillaBase):
    plantilla_id: str
    empresa_id: str
    unidad_negocio_pk: Optional[str] = None
    sucursal_id: Optional[int] = None
    origen_plantilla: OrigenPlantilla = OrigenPlantilla.CAPTURA_DIRECTA_EDARSAHUB
    sistema_origen: Optional[str] = None
    servidor_origen_id: Optional[str] = None
    id_legacy_plantilla: Optional[str] = None
    hash_origen: Optional[str] = None
    version_actual: int = 1
    estatus: EstatusPlantilla = EstatusPlantilla.BORRADOR
    activo: bool = True
    fecha_alta_utc: datetime
    fecha_operacion_mexico: date
    detalles: List[PlantillaDetalle] = []

    class Config:
        from_attributes = True


# ============================================================
# ÓRDENES
# ============================================================

class OrdenDetalleBase(BaseModel):
    producto_derivado_codigo: Optional[str] = None
    producto_derivado_nombre: str
    tipo_derivado: TipoDerivado
    cantidad_esperada: Optional[Decimal] = None
    porcentaje_esperado: Optional[Decimal] = None
    cantidad_real: Optional[Decimal] = None
    peso_real_kg: Optional[Decimal] = None
    piezas_reales: Optional[Decimal] = None
    sku_kg_codigo: Optional[str] = None
    sku_pieza_codigo: Optional[str] = None
    gramaje_pieza_g: Optional[Decimal] = None
    costo_fijo: bool = False
    costo_fijo_unitario: Optional[Decimal] = None
    prorratea_costo: bool = True
    observaciones: Optional[str] = None


class OrdenDetalleCreate(OrdenDetalleBase):
    pass


class OrdenDetalle(OrdenDetalleBase):
    orden_detalle_id: str
    orden_id: str
    porcentaje_real: Optional[Decimal] = None
    desviacion_cantidad: Optional[Decimal] = None
    desviacion_porcentaje: Optional[Decimal] = None
    costo_unitario: Optional[Decimal] = None
    costo_total: Optional[Decimal] = None

    class Config:
        from_attributes = True


class OrdenCreate(BaseModel):
    empresa_id: str
    unidad_negocio_pk: Optional[str] = None
    sucursal_id: Optional[int] = None
    plantilla_id: str
    fecha_operacion_mexico: date
    fecha_programada: Optional[date] = None
    cantidad_base_planeada: Decimal
    lote_insumo: Optional[str] = None
    almacen_origen_id: Optional[str] = None
    almacen_destino_id: Optional[str] = None
    lonja_id: Optional[str] = None
    lonja_codigo: Optional[str] = None
    lonja_nombre: Optional[str] = None
    lonja_peso_kg: Optional[Decimal] = None
    lonja_costo_total: Optional[Decimal] = None
    observaciones: Optional[str] = None


class LonjaDisponible(BaseModel):
    lonja_id: str
    empresa_id: Optional[str] = None
    unidad_negocio_pk: Optional[str] = None
    sucursal_id: Optional[str] = None
    almacen_origen_id: Optional[str] = None
    almacen_destino_id: Optional[str] = None
    lote_insumo: Optional[str] = None
    insumo_base_codigo: Optional[str] = None
    insumo_base_nombre: Optional[str] = None
    peso_kg: Decimal
    costo_total: Optional[Decimal] = None
    costo_unitario: Optional[Decimal] = None
    procesada: bool = False


class OrdenCapturaDirectaCreate(BaseModel):
    """
    Fase 4: Captura Directa
    Permite crear una orden de tablaje sin plantilla predefinida.
    """
    empresa_id: str
    unidad_negocio_pk: Optional[str] = None
    sucursal_id: Optional[int] = None
    fecha_operacion_mexico: date
    
    # Insumo base (carne a procesar)
    insumo_base_codigo: str
    insumo_base_nombre: str
    unidad_base_codigo: Optional[str] = "KG"
    cantidad_base_planeada: Decimal
    lote_insumo: Optional[str] = None
    
    # Productos derivados esperados
    detalles: List[OrdenDetalleCreate]
    
    # Opcional
    observaciones: Optional[str] = None
    responsable_id: Optional[str] = None


class OrdenUpdate(BaseModel):
    cantidad_base_real: Optional[Decimal] = None
    peso_inicial_kg: Optional[Decimal] = None
    peso_final_kg: Optional[Decimal] = None
    merma_real_kg: Optional[Decimal] = None
    estatus_orden: Optional[EstatusOrden] = None
    observaciones: Optional[str] = None


class Orden(BaseModel):
    orden_id: str
    empresa_id: str
    unidad_negocio_pk: Optional[str] = None
    folio_orden: str
    plantilla_id: str
    plantilla_nombre: Optional[str] = None
    estatus_orden: EstatusOrden
    fecha_operacion_mexico: date
    cantidad_base_planeada: Decimal
    cantidad_base_real: Optional[Decimal] = None
    rendimiento_esperado_porcentaje: Optional[Decimal] = None
    rendimiento_real_porcentaje: Optional[Decimal] = None
    merma_esperada_porcentaje: Optional[Decimal] = None
    merma_real_porcentaje: Optional[Decimal] = None
    costo_total_orden: Optional[Decimal] = None
    fecha_alta_utc: datetime
    detalles: List[OrdenDetalle] = []

    class Config:
        from_attributes = True


# ============================================================
# SINCRONIZACIÓN
# ============================================================

class SyncRequest(BaseModel):
    servidor_id: str
    entidades: List[str] = Field(default=["plantillas"])
    forzar_actualizacion: bool = False


class SyncResult(BaseModel):
    success: bool
    servidor_id: str
    servidor_nombre: Optional[str] = None
    entidades_procesadas: List[str] = []
    registros_leidos: int = 0
    registros_creados: int = 0
    registros_actualizados: int = 0
    registros_sin_cambios: int = 0
    registros_error: int = 0
    duracion_segundos: int = 0
    errores: List[str] = []


# ============================================================
# LEGACY DATA (para mapeo)
# ============================================================

class MPROSubgrupoInsumo(BaseModel):
    """Estructura de subgrupo_insumos en MPRO"""
    idsubgrupo: int
    idunidad: int
    descripcion: str
    idinsumokg: Optional[str] = None
    idinsumopz: Optional[str] = None
    tipoinsumo: str
    rendimiento: Decimal
    costofijo: Decimal
    costeable: bool
    bdempresa: str


class MPROReceta(BaseModel):
    """Estructura de receta en MPRO"""
    idsubgrupobase: int
    idsubgruporesultante: int
    bdempresa: str


class MPROSucursal(BaseModel):
    """Estructura de sucursales en MPRO"""
    idsucursal: int
    bdempresa: str
    nombreempresa: str
    clavesucursal: str
    nombresucursal: str
