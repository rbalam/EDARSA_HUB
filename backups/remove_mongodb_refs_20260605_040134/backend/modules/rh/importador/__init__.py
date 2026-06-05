"""
EDARSA HUB - Módulo de Importación RH
=====================================
Importación controlada de empleados desde fuentes externas hacia EDARSA HUB.

FLUJO OBLIGATORIO:
1. Cargar a staging
2. Validar
3. Detectar duplicados
4. Clasificar (nuevos / actualizar / revisar manualmente)
5. Aprobar
6. Insertar/actualizar en tablas maestras

FUENTES AUTORIZADAS:
- Excel Cienfuegos (nómina semanal)
- MPro Origen (pendiente mapeo)
- MPro Querétaro (pendiente mapeo)

Autor: Arquitecto de Software - EDARSA HUB
Fecha: Diciembre 2025
"""

from .schemas import (
    ImportacionStagingCreate,
    ImportacionStagingResponse,
    ImportacionBitacoraResponse,
    ClasificacionRegistro,
    PreviewImportacion,
    ResultadoValidacion,
    CLASIFICACION_NUEVO,
    CLASIFICACION_ACTUALIZAR,
    CLASIFICACION_DUPLICADO_PROBABLE,
    CLASIFICACION_INCOMPLETO,
    CLASIFICACION_RECHAZADO,
)

from .repository import (
    init_importador_repository,
    crear_tablas_importacion,
    insertar_staging,
    listar_staging,
    actualizar_estado_staging,
    insertar_bitacora,
    listar_bitacora,
)

from .service import (
    ImportadorExcelService,
)

__all__ = [
    # Schemas
    "ImportacionStagingCreate",
    "ImportacionStagingResponse",
    "ImportacionBitacoraResponse",
    "ClasificacionRegistro",
    "PreviewImportacion",
    "ResultadoValidacion",
    "CLASIFICACION_NUEVO",
    "CLASIFICACION_ACTUALIZAR",
    "CLASIFICACION_DUPLICADO_PROBABLE",
    "CLASIFICACION_INCOMPLETO",
    "CLASIFICACION_RECHAZADO",
    # Repository
    "init_importador_repository",
    "crear_tablas_importacion",
    "insertar_staging",
    "listar_staging",
    "actualizar_estado_staging",
    "insertar_bitacora",
    "listar_bitacora",
    # Service
    "ImportadorExcelService",
]
