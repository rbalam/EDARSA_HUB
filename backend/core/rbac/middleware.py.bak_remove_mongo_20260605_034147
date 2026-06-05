"""
EDARSA HUB - RBAC Middleware y Decoradores
==========================================
Decoradores y dependencies para proteger endpoints con RBAC.

Uso:
    from core.rbac import require_permission
    
    @router.post("/cargos/{id}/aplicar")
    async def aplicar_cargo(
        id: str,
        current_user: dict = Depends(get_current_user),
        _auth: None = Depends(require_permission("CARGOS_APLICAR"))
    ):
        ...
"""

from typing import Optional, List, Callable, Any
from functools import wraps
import logging

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.security import verify_token
from .service import RBACService, PermisoDenegadoError

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


def _get_db():
    """Obtiene conexión a MongoDB de forma síncrona."""
    import os
    from pymongo import MongoClient
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'edarsahub')
    client = MongoClient(mongo_url)
    return client[db_name]


def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Optional[dict]:
    """Extrae el usuario del token JWT."""
    if not credentials:
        return None
    
    try:
        payload = verify_token(credentials.credentials)
        return {
            "id": payload.get("user_id"),
            "email": payload.get("email"),
            "role": payload.get("role"),
        }
    except Exception as e:
        logger.warning(f"Error decodificando token: {e}")
        return None


class RBACDependency:
    """
    Dependency de FastAPI para verificar permisos RBAC.
    
    Uso:
        @router.get("/endpoint")
        async def my_endpoint(
            _: None = Depends(RBACDependency("PERMISO_REQUERIDO"))
        ):
            ...
    """
    
    def __init__(
        self,
        permiso: str,
        audit: bool = True,
        mensaje_error: Optional[str] = None
    ):
        self.permiso = permiso
        self.audit = audit
        self.mensaje_error = mensaje_error or f"Se requiere permiso: {permiso}"
    
    async def __call__(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ):
        # 1. Verificar que hay token
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail="Token de autenticación requerido"
            )
        
        # 2. Decodificar token
        try:
            payload = verify_token(credentials.credentials)
            user = {
                "id": payload.get("user_id"),
                "email": payload.get("email"),
                "role": payload.get("role"),
            }
        except Exception:
            raise HTTPException(
                status_code=401,
                detail="Token inválido o expirado"
            )
        
        # 3. Obtener DB y servicio RBAC
        try:
            db = _get_db()
            rbac_service = RBACService(db)
        except Exception as e:
            logger.error(f"Error obteniendo DB para RBAC: {e}")
            # En caso de error de DB, permitir si es admin legacy
            if user.get("role") == "Administrador":
                return user
            raise HTTPException(status_code=500, detail="Error interno de autorización")
        
        # 4. Verificar permiso
        ip_address = request.client.host if request.client else None
        endpoint = f"{request.method} {request.url.path}"
        
        tiene_permiso = rbac_service.check_permission(
            user=user,
            permiso_requerido=self.permiso,
            audit=self.audit,
            endpoint=endpoint,
            ip_address=ip_address
        )
        
        if not tiene_permiso:
            logger.warning(f"RBAC DENEGADO: {user.get('email')} -> {self.permiso} en {endpoint}")
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "PERMISO_DENEGADO",
                    "mensaje": self.mensaje_error,
                    "permiso_requerido": self.permiso,
                }
            )
        
        # 5. Retornar usuario para uso posterior si se necesita
        return user


class RBACAnyDependency:
    """Verifica que el usuario tenga AL MENOS UNO de los permisos."""
    
    def __init__(self, permisos: List[str], audit: bool = True):
        self.permisos = permisos
        self.audit = audit
    
    async def __call__(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ):
        if not credentials:
            raise HTTPException(status_code=401, detail="Token requerido")
        
        try:
            payload = verify_token(credentials.credentials)
            user = {
                "id": payload.get("user_id"),
                "email": payload.get("email"),
                "role": payload.get("role"),
            }
        except Exception:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        try:
            db = _get_db()
            rbac_service = RBACService(db)
        except Exception:
            if user.get("role") == "Administrador":
                return user
            raise HTTPException(status_code=500, detail="Error de autorización")
        
        tiene_alguno = rbac_service.check_any_permission(user, self.permisos, self.audit)
        
        if not tiene_alguno:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "PERMISO_DENEGADO",
                    "mensaje": f"Se requiere al menos uno de: {', '.join(self.permisos)}",
                    "permisos_requeridos": self.permisos,
                }
            )
        
        return user


class RBACAllDependency:
    """Verifica que el usuario tenga TODOS los permisos."""
    
    def __init__(self, permisos: List[str], audit: bool = True):
        self.permisos = permisos
        self.audit = audit
    
    async def __call__(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ):
        if not credentials:
            raise HTTPException(status_code=401, detail="Token requerido")
        
        try:
            payload = verify_token(credentials.credentials)
            user = {
                "id": payload.get("user_id"),
                "email": payload.get("email"),
                "role": payload.get("role"),
            }
        except Exception:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        try:
            db = _get_db()
            rbac_service = RBACService(db)
        except Exception:
            if user.get("role") == "Administrador":
                return user
            raise HTTPException(status_code=500, detail="Error de autorización")
        
        tiene_todos = rbac_service.check_all_permissions(user, self.permisos, self.audit)
        
        if not tiene_todos:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "PERMISO_DENEGADO",
                    "mensaje": f"Se requieren todos: {', '.join(self.permisos)}",
                    "permisos_requeridos": self.permisos,
                }
            )
        
        return user


# =============================================================================
# FUNCIONES DE ATAJO
# =============================================================================

def require_permission(permiso: str, audit: bool = True, mensaje: Optional[str] = None):
    """
    Crea una dependency que requiere un permiso específico.
    
    Uso:
        @router.post("/cargos/{id}/aplicar")
        async def aplicar(
            _: dict = Depends(require_permission("CARGOS_APLICAR"))
        ):
            ...
    """
    return RBACDependency(permiso, audit, mensaje)


def require_any_permission(permisos: List[str], audit: bool = True):
    """Crea dependency que requiere al menos uno de los permisos."""
    return RBACAnyDependency(permisos, audit)


def require_all_permissions(permisos: List[str], audit: bool = True):
    """Crea dependency que requiere todos los permisos."""
    return RBACAllDependency(permisos, audit)


# =============================================================================
# HELPER PARA OBTENER USUARIO ACTUAL CON PERMISOS
# =============================================================================

async def get_current_user_with_permissions(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Obtiene el usuario actual con sus permisos cargados.
    
    Retorna dict con: id, email, role, permisos, nivel_jerarquia, es_admin
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Token requerido")
    
    try:
        payload = verify_token(credentials.credentials)
        user = {
            "id": payload.get("user_id"),
            "email": payload.get("email"),
            "role": payload.get("role"),
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    try:
        db = _get_db()
        rbac_service = RBACService(db)
        permisos_data = rbac_service.get_user_permissions(user)
        
        return {
            **user,
            "permisos": permisos_data.get("permisos", []),
            "roles_rbac": permisos_data.get("roles", []),
            "nivel_jerarquia": permisos_data.get("nivel_jerarquia_max", 0),
            "es_admin": permisos_data.get("es_admin", False),
        }
    except Exception as e:
        logger.error(f"Error cargando permisos: {e}")
        # Fallback: solo datos básicos
        return {
            **user,
            "permisos": [],
            "roles_rbac": [],
            "nivel_jerarquia": 0,
            "es_admin": user.get("role") == "Administrador",
        }


__all__ = [
    'RBACDependency',
    'RBACAnyDependency',
    'RBACAllDependency',
    'require_permission',
    'require_any_permission',
    'require_all_permissions',
    'get_current_user_with_permissions',
    'get_current_user_from_token',
]
