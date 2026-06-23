from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - RBAC Service (Motor de Autorización)
=================================================
Motor central de autorización basado en roles.

Funciones principales:
- check_permission: Verifica si un usuario tiene un permiso
- get_user_permissions: Obtiene permisos efectivos de un usuario
- Integración con el sistema de roles existente
"""

from typing import Optional, List, Dict, Any
import logging

from .repository import RBACRepository
from .schemas import PERMISOS_SISTEMA, ROLES_SISTEMA

logger = logging.getLogger(__name__)


class PermisoDenegadoError(Exception):
    """Error cuando un usuario no tiene el permiso requerido."""
    def __init__(self, mensaje: str, permiso: str, user_id: str):
        self.mensaje = mensaje
        self.permiso = permiso
        self.user_id = user_id
        super().__init__(mensaje)


class RBACService:
    """
    Servicio central de RBAC.
    
    Maneja la lógica de autorización, gestión de roles y permisos.
    """
    
    # Mapeo de roles legacy a roles RBAC SQL
    # FASE 4B-RBAC: Actualizado para usar roles SQL con permisos poblados
    LEGACY_ROLE_MAPPING = {
        "SuperAdministrador": "SUPERADMIN",   # Nivel 100, acceso total
        "Administrador": "SUPERADMIN",        # Administrador completo -> SUPERADMIN
        "Supervisor": "SUPERVISOR",           # Nivel 50
        "Usuario": "OPERADOR",                # Nivel 20
        "Gerente": "GERENTE_OPS",             # Nivel 60
        "Director": "DIRECCION",              # Nivel 80
        "Auditor": "AUDITOR",                 # Nivel 30
        "Visor": "OPERADOR",                  # Sin rol específico -> OPERADOR
    }
    
    # FASE AUTH-V2-ALIGN (Capa 2): el seeding RBAC debe ocurrir UNA sola vez por
    # proceso. middleware.py instancia RBACService(db) en cada request; con un flag
    # de instancia el seed corría en CADA petición, abriendo decenas de conexiones
    # a EDARSAHUB (lento ~6s + timeouts intermitentes => 500). Flag a nivel de clase.
    _seeded = False

    def __init__(self, db):
        self.db = db
        self.repo = RBACRepository(db)
    
    async def initialize(self):
        """Inicializa el sistema RBAC, sembrando datos si es necesario."""
        if RBACService._seeded:
            return
        
        # Sembrar permisos del sistema
        permisos_count = self.repo.seed_permisos(PERMISOS_SISTEMA)
        if permisos_count > 0:
            logger.info(f"RBAC: {permisos_count} permisos del sistema sembrados")
        
        # Sembrar roles del sistema
        roles_count = self.repo.seed_roles(ROLES_SISTEMA)
        if roles_count > 0:
            logger.info(f"RBAC: {roles_count} roles del sistema sembrados")
        
        RBACService._seeded = True
        logger.info("RBAC Service inicializado")
    
    def ensure_initialized(self):
        """Asegura que el servicio esté inicializado (sync). Una vez por proceso."""
        if RBACService._seeded:
            return
        
        permisos_count = self.repo.seed_permisos(PERMISOS_SISTEMA)
        roles_count = self.repo.seed_roles(ROLES_SISTEMA)
        
        if permisos_count > 0 or roles_count > 0:
            logger.info(f"RBAC: Sembrados {permisos_count} permisos, {roles_count} roles")
        
        RBACService._seeded = True
    
    # =========================================================================
    # MOTOR DE AUTORIZACIÓN
    # =========================================================================
    
    def check_permission(
        self,
        user: Dict[str, Any],
        permiso_requerido: str,
        audit: bool = True,
        endpoint: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Verifica si un usuario tiene un permiso específico.
        
        Args:
            user: Dict con datos del usuario (debe tener 'id' y opcionalmente 'role')
            permiso_requerido: Código del permiso a verificar
            audit: Si True, registra la verificación en el log
            endpoint: Endpoint que se está accediendo (para auditoría)
            ip_address: IP del cliente (para auditoría)
            
        Returns:
            bool: True si tiene el permiso, False si no
        """
        self.ensure_initialized()
        
        user_id = user.get("id", user.get("user_id", ""))
        user_email = user.get("email")
        user_role_legacy = user.get("role", "")
        
        # BYPASS: SuperAdministrador y Administrador tienen acceso total
        if user_role_legacy in ("SuperAdministrador", "Administrador"):
            if audit:
                self.repo.log_verificacion(
                    user_id=user_id,
                    permiso_requerido=permiso_requerido,
                    resultado="PERMITIDO",
                    user_email=user_email,
                    endpoint=endpoint,
                    ip_address=ip_address,
                    detalles={"bypass": user_role_legacy, "rol_legacy": user_role_legacy}
                )
            logger.debug(f"RBAC: {user_role_legacy} {user_id} BYPASS para {permiso_requerido}")
            return True
        
        # 1. Obtener permisos del usuario desde RBAC
        permisos_usuario = self.repo.get_permisos_usuario(user_id)
        
        # 2. Si no tiene roles RBAC asignados, mapear desde rol legacy
        if not permisos_usuario and user_role_legacy:
            permisos_usuario = self._get_permisos_from_legacy_role(user_role_legacy)
        
        # 3. Verificar permiso
        tiene_permiso = permiso_requerido in permisos_usuario
        
        # 4. Auditar
        if audit:
            self.repo.log_verificacion(
                user_id=user_id,
                permiso_requerido=permiso_requerido,
                resultado="PERMITIDO" if tiene_permiso else "DENEGADO",
                user_email=user_email,
                endpoint=endpoint,
                ip_address=ip_address,
                detalles={
                    "permisos_usuario": permisos_usuario[:10],  # Limitar para no saturar
                    "rol_legacy": user_role_legacy,
                }
            )
        
        if tiene_permiso:
            logger.debug(f"RBAC: Usuario {user_id} PERMITIDO para {permiso_requerido}")
        else:
            logger.warning(f"RBAC: Usuario {user_id} DENEGADO para {permiso_requerido}")
        
        return tiene_permiso
    
    def require_permission(
        self,
        user: Dict[str, Any],
        permiso_requerido: str,
        endpoint: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """
        Verifica permiso y lanza excepción si no lo tiene.
        
        Raises:
            PermisoDenegadoError: Si el usuario no tiene el permiso
        """
        if not self.check_permission(user, permiso_requerido, audit=True, endpoint=endpoint, ip_address=ip_address):
            raise PermisoDenegadoError(
                mensaje=f"No tienes permiso para esta acción. Se requiere: {permiso_requerido}",
                permiso=permiso_requerido,
                user_id=user.get("id", "")
            )
    
    def check_any_permission(
        self,
        user: Dict[str, Any],
        permisos_requeridos: List[str],
        audit: bool = True
    ) -> bool:
        """Verifica si el usuario tiene AL MENOS UNO de los permisos."""
        self.ensure_initialized()
        
        user_id = user.get("id", user.get("user_id", ""))
        permisos_usuario = self.repo.get_permisos_usuario(user_id)
        
        if not permisos_usuario:
            user_role_legacy = user.get("role", "")
            permisos_usuario = self._get_permisos_from_legacy_role(user_role_legacy)
        
        tiene_alguno = any(p in permisos_usuario for p in permisos_requeridos)
        
        if audit:
            self.repo.log_verificacion(
                user_id=user_id,
                permiso_requerido=f"ANY:{','.join(permisos_requeridos)}",
                resultado="PERMITIDO" if tiene_alguno else "DENEGADO",
                user_email=user.get("email"),
            )
        
        return tiene_alguno
    
    def check_all_permissions(
        self,
        user: Dict[str, Any],
        permisos_requeridos: List[str],
        audit: bool = True
    ) -> bool:
        """Verifica si el usuario tiene TODOS los permisos."""
        self.ensure_initialized()
        
        user_id = user.get("id", user.get("user_id", ""))
        permisos_usuario = self.repo.get_permisos_usuario(user_id)
        
        if not permisos_usuario:
            user_role_legacy = user.get("role", "")
            permisos_usuario = self._get_permisos_from_legacy_role(user_role_legacy)
        
        tiene_todos = all(p in permisos_usuario for p in permisos_requeridos)
        
        if audit:
            self.repo.log_verificacion(
                user_id=user_id,
                permiso_requerido=f"ALL:{','.join(permisos_requeridos)}",
                resultado="PERMITIDO" if tiene_todos else "DENEGADO",
                user_email=user.get("email"),
            )
        
        return tiene_todos
    
    def get_user_permissions(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene todos los permisos efectivos de un usuario.
        
        Returns:
            Dict con user_id, roles, permisos, nivel_jerarquia, es_admin
        """
        self.ensure_initialized()
        
        user_id = user.get("id", user.get("user_id", ""))
        user_role_legacy = user.get("role", "")
        
        # Obtener roles asignados
        roles_data = self.repo.get_roles_usuario(user_id)
        
        # Si no tiene roles RBAC, crear uno virtual desde legacy
        if not roles_data and user_role_legacy:
            rol_rbac_nombre = self.LEGACY_ROLE_MAPPING.get(user_role_legacy, "OPERADOR")
            rol_rbac = self.repo.get_rol_by_nombre(rol_rbac_nombre)
            if rol_rbac:
                roles_data = [{"rol": rol_rbac, "sucursal_id": None}]
        
        # Consolidar permisos
        permisos_set = set()
        nivel_max = 0
        roles_response = []
        
        for rd in roles_data:
            rol = rd.get("rol", {})
            roles_response.append({
                "id": rol.get("id"),
                "nombre": rol.get("nombre"),
                "descripcion": rol.get("descripcion", ""),
                "permisos": rol.get("permisos", []),
                "nivel_jerarquia": rol.get("nivel_jerarquia", 0),
                "es_sistema": rol.get("es_sistema", False),
                "activo": rol.get("activo", True),
            })
            
            for permiso in rol.get("permisos", []):
                permisos_set.add(permiso)
            
            nivel_max = max(nivel_max, rol.get("nivel_jerarquia", 0))
        
        return {
            "user_id": user_id,
            "roles": roles_response,
            "permisos": sorted(list(permisos_set)),
            "nivel_jerarquia_max": nivel_max,
            "es_admin": nivel_max >= 100 or "RBAC_ADMIN" in permisos_set,
        }
    
    def _get_permisos_from_legacy_role(self, role_legacy: str) -> List[str]:
        """Mapea un rol legacy a permisos RBAC."""
        rol_rbac_nombre = self.LEGACY_ROLE_MAPPING.get(role_legacy, "OPERADOR")
        rol_rbac = self.repo.get_rol_by_nombre(rol_rbac_nombre)
        
        if rol_rbac:
            return rol_rbac.get("permisos", [])
        
        # Fallback: permisos mínimos
        return ["CARGOS_VER", "RESPONSABILIDAD_VER", "SLA_VER", "WORKFLOW_VER", "TAREAS_VER", "REPORTES_VER"]
    
    # =========================================================================
    # GESTIÓN DE ROLES
    # =========================================================================
    
    def get_all_roles(self) -> List[Dict]:
        """Obtiene todos los roles activos."""
        self.ensure_initialized()
        return self.repo.get_all_roles()
    
    def get_rol(self, rol_id: str) -> Optional[Dict]:
        """Obtiene un rol por ID."""
        return self.repo.get_rol_by_id(rol_id)
    
    def create_rol(self, data: Dict, created_by: str) -> Dict:
        """Crea un nuevo rol."""
        return self.repo.create_rol(data)
    
    def update_rol(self, rol_id: str, data: Dict) -> Optional[Dict]:
        """Actualiza un rol."""
        return self.repo.update_rol(rol_id, data)
    
    def delete_rol(self, rol_id: str) -> bool:
        """Elimina un rol (soft delete)."""
        return self.repo.delete_rol(rol_id)
    
    # =========================================================================
    # GESTIÓN DE PERMISOS
    # =========================================================================
    
    def get_all_permisos(self) -> List[Dict]:
        """Obtiene todos los permisos del sistema."""
        self.ensure_initialized()
        return self.repo.get_all_permisos()
    
    # =========================================================================
    # ASIGNACIÓN DE ROLES
    # =========================================================================
    
    def asignar_rol_a_usuario(
        self,
        user_id: str,
        rol_id: str,
        asignado_por: str,
        sucursal_id: Optional[str] = None
    ) -> Dict:
        """Asigna un rol a un usuario."""
        return self.repo.asignar_rol(user_id, rol_id, asignado_por, sucursal_id)
    
    def revocar_rol_de_usuario(
        self,
        user_id: str,
        rol_id: str,
        sucursal_id: Optional[str] = None
    ) -> bool:
        """Revoca un rol de un usuario."""
        return self.repo.revocar_rol(user_id, rol_id, sucursal_id)
    
    # =========================================================================
    # AUDITORÍA
    # =========================================================================
    
    def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        resultado: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Obtiene logs de auditoría."""
        return self.repo.get_audit_logs(user_id, resultado, limit)


# =============================================================================
# FUNCIONES GLOBALES (ATAJOS)
# =============================================================================

_rbac_service: Optional[RBACService] = None


def get_rbac_service(db) -> RBACService:
    """Obtiene o crea la instancia del servicio RBAC."""
    global _rbac_service
    if _rbac_service is None:
        _rbac_service = RBACService(db)
    return _rbac_service


def check_permission(
    db,
    user: Dict[str, Any],
    permiso: str,
    endpoint: Optional[str] = None,
    ip_address: Optional[str] = None
) -> bool:
    """Función global para verificar permisos."""
    service = get_rbac_service(db)
    return service.check_permission(user, permiso, endpoint=endpoint, ip_address=ip_address)


def get_user_permissions(db, user: Dict[str, Any]) -> Dict[str, Any]:
    """Función global para obtener permisos de usuario."""
    service = get_rbac_service(db)
    return service.get_user_permissions(user)


__all__ = [
    'RBACService',
    'PermisoDenegadoError',
    'get_rbac_service',
    'check_permission',
    'get_user_permissions',
]
