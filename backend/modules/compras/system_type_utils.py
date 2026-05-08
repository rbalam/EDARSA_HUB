"""
EDARSA HUB - Compras System Type Utilities
==========================================
FASE 3A.1: Las utilidades ahora están centralizadas en /app/backend/core/system_type_utils.py
Este archivo re-exporta las funciones para mantener compatibilidad con código existente.

NOTA: Para nuevas implementaciones, preferir importar directamente de core.system_type_utils
"""

# Re-exportar desde core para mantener compatibilidad
from core.system_type_utils import (
    # Constantes
    SystemType,
    SYSTEM_TYPE_MAP,
    SYSTEM_TYPE_LABELS,
    # Funciones de normalización
    normalize_system_type,
    is_mpro_system,
    is_softrestaurant_system,
    is_api_system,
    is_supported_system_type,
    is_unknown_system,
    get_system_type_label,
    # Respuestas estándar
    get_unsupported_system_response,
    get_not_available_response,
    # Logging
    log_system_type_normalized,
    log_system_type_check,
    # Cache
    build_cache_key_with_system_type,
)

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging


# ============================================================================
# ESTADOS DE RESPUESTA ESPECÍFICOS DE COMPRAS
# ============================================================================

class ComprasStatus(str, Enum):
    """Estados de respuesta para endpoints de Compras."""
    SUCCESS = "SUCCESS"
    NO_DATA = "NO_DATA"
    PARTIAL = "PARTIAL"
    SOURCE_UNREACHABLE = "SOURCE_UNREACHABLE"
    QUERY_ERROR = "QUERY_ERROR"
    FIELD_MAPPING_ERROR = "FIELD_MAPPING_ERROR"
    CONFIGURATION_MISSING = "CONFIGURATION_MISSING"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INACTIVE_SOURCE = "INACTIVE_SOURCE"
    UNSUPPORTED_SYSTEM_TYPE = "UNSUPPORTED_SYSTEM_TYPE"
    NOT_AVAILABLE_FOR_SYSTEM = "NOT_AVAILABLE_FOR_SYSTEM"


# ============================================================================
# ENVELOPE DE RESPUESTA DE COMPRAS
# ============================================================================

@dataclass
class ComprasResponse:
    """Envelope estándar de respuesta para endpoints de Compras."""
    status: str
    data: List[Dict] = field(default_factory=list)
    meta: Dict = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    error: Optional[Dict] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "status": self.status,
            "data": self.data,
            "meta": self.meta,
            "warnings": self.warnings
        }
        if self.error:
            result["error"] = self.error
        return result
    
    @classmethod
    def success(cls, data: List[Dict], meta: Dict = None, warnings: List[str] = None) -> "ComprasResponse":
        _meta = meta or {}
        _meta["row_count"] = len(data)
        return cls(status=ComprasStatus.SUCCESS.value, data=data, meta=_meta, warnings=warnings or [])
    
    @classmethod
    def no_data(cls, meta: Dict = None, message: str = "No hay datos para los filtros seleccionados") -> "ComprasResponse":
        _meta = meta or {}
        _meta["row_count"] = 0
        return cls(status=ComprasStatus.NO_DATA.value, data=[], meta=_meta, warnings=[message])
    
    @classmethod
    def unsupported_system(cls, system_type: str, meta: Dict = None, endpoint: str = "") -> "ComprasResponse":
        return cls(
            status=ComprasStatus.UNSUPPORTED_SYSTEM_TYPE.value,
            data=[],
            meta=meta or {},
            warnings=[],
            error=get_unsupported_system_response(system_type, endpoint).get("error")
        )
    
    @classmethod
    def not_available(cls, system_type: str, feature: str, meta: Dict = None) -> "ComprasResponse":
        return cls(
            status=ComprasStatus.NOT_AVAILABLE_FOR_SYSTEM.value,
            data=[],
            meta=meta or {},
            warnings=[f"'{feature}' no está disponible para {system_type}"],
            error=get_not_available_response(system_type, feature).get("error")
        )
    
    @classmethod
    def source_unreachable(cls, meta: Dict = None, error_detail: str = None) -> "ComprasResponse":
        return cls(
            status=ComprasStatus.SOURCE_UNREACHABLE.value,
            data=[],
            meta=meta or {},
            warnings=[],
            error={
                "code": "SOURCE_UNREACHABLE",
                "message": "No fue posible conectar con el servidor origen",
                "technical_detail": error_detail[:200] if error_detail else None
            }
        )
    
    @classmethod
    def query_error(cls, meta: Dict = None, error_detail: str = None) -> "ComprasResponse":
        return cls(
            status=ComprasStatus.QUERY_ERROR.value,
            data=[],
            meta=meta or {},
            warnings=[],
            error={
                "code": "QUERY_ERROR",
                "message": "La consulta falló por incompatibilidad de estructura o error SQL",
                "technical_detail": error_detail[:200] if error_detail else None
            }
        )
    
    @classmethod
    def configuration_missing(cls, meta: Dict = None, detail: str = None) -> "ComprasResponse":
        return cls(
            status=ComprasStatus.CONFIGURATION_MISSING.value,
            data=[],
            meta=meta or {},
            warnings=[],
            error={
                "code": "CONFIGURATION_MISSING",
                "message": "La configuración de esta unidad no está completa",
                "technical_detail": detail
            }
        )


# ============================================================================
# LOGGING HELPERS ESPECÍFICOS DE COMPRAS
# ============================================================================

def log_compras_adapter_selected(
    endpoint: str,
    server_id: str,
    system_type: str,
    adapter: str,
    sucursal_id: str = None,
    unidad_negocio_id: str = None
) -> None:
    """Log para selección de adapter de Compras."""
    logging.info(
        f"[COMPRAS][ADAPTER_SELECTED] endpoint={endpoint} "
        f"server_id={server_id} "
        f"system_type={system_type} "
        f"system_type_normalized={normalize_system_type(system_type)} "
        f"adapter={adapter} "
        f"sucursal_id={sucursal_id or 'N/A'}"
    )


def log_compras_query_result(
    endpoint: str,
    server_id: str,
    status: str,
    row_count: int = 0,
    duration_ms: float = None
) -> None:
    """Log para resultado de query de Compras."""
    duration_str = f"duration_ms={duration_ms:.2f}" if duration_ms else ""
    logging.info(
        f"[COMPRAS][QUERY_RESULT] endpoint={endpoint} "
        f"server_id={server_id} status={status} "
        f"row_count={row_count} {duration_str}"
    )


def log_compras_error(
    endpoint: str,
    server_id: str,
    error_code: str,
    error_message: str,
    system_type: str = None
) -> None:
    """Log para errores de Compras."""
    logging.error(
        f"[COMPRAS][ERROR] endpoint={endpoint} "
        f"server_id={server_id} "
        f"system_type={system_type or 'N/A'} "
        f"error_code={error_code} "
        f"error_message={error_message[:200]}"
    )


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Re-exportados de core
    'SystemType',
    'normalize_system_type',
    'is_mpro_system',
    'is_softrestaurant_system',
    'is_api_system',
    'is_supported_system_type',
    'is_unknown_system',
    'get_system_type_label',
    'get_unsupported_system_response',
    'get_not_available_response',
    'build_cache_key_with_system_type',
    # Específicos de Compras
    'ComprasStatus',
    'ComprasResponse',
    'log_compras_adapter_selected',
    'log_compras_query_result',
    'log_compras_error',
]
