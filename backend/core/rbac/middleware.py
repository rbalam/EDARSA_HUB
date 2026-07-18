from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
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
from core.rbac_helper_sql import es_admin

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

def _get_db():
    return None




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
            # En caso de error de DB, permitir si es admin legacy (canónico ADMIN/SUPERADMIN)
            if es_admin(user):
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
            if es_admin(user):
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
            if es_admin(user):
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

class RBACExplicitDependency:
    """
    Dependency estricta: exige permiso efectivo SQL explicito.

    Diferencia contra RBACDependency / require_permission:
    - No permite bypass por ADMIN legacy.
    - No usa RBACService.check_permission(), porque ese motor conserva bypass legacy.
    - Consulta EDARSAHUB SQL canónico por email y permiso.
    """

    def __init__(
        self,
        permiso: str,
        mensaje_error: Optional[str] = None
    ):
        self.permiso = permiso
        self.mensaje_error = mensaje_error or f"Se requiere permiso SQL explícito: {permiso}"

    async def __call__(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ):
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail="Token de autenticación requerido"
            )

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

        email = user.get("email")
        if not email:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "PERMISO_DENEGADO",
                    "mensaje": self.mensaje_error,
                    "permiso_requerido": self.permiso,
                }
            )

        from core.sql_first.db import get_sql_connection

        conn = get_sql_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT TOP 1 1
                FROM dbo.Usuario_Catalogo u
                INNER JOIN dbo.Usuario_RolesAsignacion ura
                    ON ura.UsuarioID = u.UsuarioID
                    AND ura.Activo = 1
                INNER JOIN dbo.Usuario_Roles r
                    ON r.RolID = ura.RolID
                    AND r.Activo = 1
                INNER JOIN dbo.Usuario_PermisosRolModulo prm
                    ON prm.RolID = r.RolID
                    AND prm.Activo = 1
                    AND prm.Permitido = 1
                INNER JOIN dbo.Usuario_Modulos m
                    ON m.ModuloID = prm.ModuloID
                    AND m.Activo = 1
                INNER JOIN dbo.Usuario_Acciones a
                    ON a.AccionID = prm.AccionID
                    AND a.Activo = 1
                WHERE u.Activo = 1
                  AND LOWER(u.Email) = LOWER(%s)
                  AND (
                        UPPER(CONCAT(m.CodigoModulo, '_', a.CodigoAccion)) = UPPER(%s)
                     OR LOWER(CONCAT(m.CodigoModulo, '.', a.CodigoAccion)) = LOWER(%s)
                  )
            """, (email, self.permiso, self.permiso))
            row = cur.fetchone()
        finally:
            conn.close()

        if not row:
            logger.warning(
                "RBAC EXPLICITO DENEGADO: %s -> %s en %s %s",
                email,
                self.permiso,
                request.method,
                request.url.path,
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "PERMISO_DENEGADO",
                    "mensaje": self.mensaje_error,
                    "permiso_requerido": self.permiso,
                }
            )

        return user


class RBACExplicitDualDependency:
    """Permiso SQL explícito con autenticación Header/Cookie."""

    def __init__(
        self,
        permiso: str,
        mensaje_error: Optional[str] = None,
    ):
        self.permiso = permiso
        self.mensaje_error = mensaje_error
        self._delegate = RBACExplicitDependency(
            permiso,
            mensaje_error,
        )

    async def __call__(self, request: Request):
        from core.security import (
            AUTH_COOKIE_NAME,
            get_current_user_dual,
        )

        await get_current_user_dual(request)

        token = None
        auth_header = request.headers.get(
            "authorization",
            "",
        )

        if auth_header.startswith("Bearer "):
            candidate = auth_header.replace(
                "Bearer ",
                "",
            ).strip()

            if candidate not in (
                "",
                "null",
                "undefined",
            ):
                token = candidate

        if not token:
            token = request.cookies.get(
                AUTH_COOKIE_NAME
            )

        if not token:
            raise HTTPException(
                status_code=401,
                detail="Token de autenticación requerido",
            )

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        )

        return await self._delegate(
            request,
            credentials,
        )


# =============================================================================
# FUNCIONES DE ATAJO
# =============================================================================

def require_explicit_permission(permiso: str, mensaje: Optional[str] = None):
    """
    Crea dependency estricta que requiere permiso efectivo SQL explícito.
    No permite bypass por ADMIN legacy.
    """
    return RBACExplicitDependency(permiso, mensaje)


def require_explicit_permission_dual(
    permiso: str,
    mensaje: Optional[str] = None,
):
    """Dependency SQL explícita compatible con Header/Cookie."""
    return RBACExplicitDualDependency(
        permiso,
        mensaje,
    )


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
            "es_admin": es_admin(user),
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
