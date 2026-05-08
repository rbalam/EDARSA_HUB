"""
EDARSA HUB - Excepciones Personalizadas
=======================================
Excepciones del dominio de negocio para manejo consistente de errores.

NOTA: Este archivo es parte del refactor modular.
Las excepciones actuales se manejan directamente en server.py.

USO FUTURO:
    from core.exceptions import NotFoundError, ValidationError, PermissionDenied
    
    raise NotFoundError("Servidor", server_id)
"""

from typing import Optional, Any
from fastapi import HTTPException, status


class EDAError(Exception):
    """Excepción base para EDARSA HUB"""
    
    def __init__(self, message: str, code: str = "EDA_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class NotFoundError(EDAError):
    """Recurso no encontrado"""
    
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} no encontrado: {identifier}",
            code="NOT_FOUND"
        )
        self.resource = resource
        self.identifier = identifier


class ValidationError(EDAError):
    """Error de validación de datos"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR"
        )
        self.field = field


class PermissionDenied(EDAError):
    """Acceso denegado por falta de permisos"""
    
    def __init__(self, action: str, resource: Optional[str] = None):
        msg = f"No tiene permisos para: {action}"
        if resource:
            msg += f" en {resource}"
        super().__init__(
            message=msg,
            code="PERMISSION_DENIED"
        )


class DatabaseError(EDAError):
    """Error de conexión o consulta a base de datos"""
    
    def __init__(self, message: str, db_type: str = "unknown"):
        super().__init__(
            message=f"Error de base de datos ({db_type}): {message}",
            code="DATABASE_ERROR"
        )
        self.db_type = db_type


class ExternalServiceError(EDAError):
    """Error de servicio externo (API local, etc.)"""
    
    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"Error en servicio externo '{service}': {message}",
            code="EXTERNAL_SERVICE_ERROR"
        )
        self.service = service


# Handlers para convertir excepciones de dominio a HTTPException
def handle_eda_exception(exc: EDAError) -> HTTPException:
    """
    Convierte una excepción de dominio en HTTPException.
    
    USO FUTURO (en exception handlers de FastAPI):
        @app.exception_handler(EDAError)
        async def eda_exception_handler(request, exc):
            return handle_eda_exception(exc)
    """
    status_map = {
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "PERMISSION_DENIED": status.HTTP_403_FORBIDDEN,
        "DATABASE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "EXTERNAL_SERVICE_ERROR": status.HTTP_502_BAD_GATEWAY,
    }
    
    return HTTPException(
        status_code=status_map.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR),
        detail={"code": exc.code, "message": exc.message}
    )
