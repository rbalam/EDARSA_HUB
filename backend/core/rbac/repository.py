"""
EDARSA HUB - RBAC Repository
============================
Acceso a datos para el sistema RBAC.

Colecciones:
- rbac_permisos
- rbac_roles
- rbac_usuarios_roles
- rbac_audit_log
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger(__name__)


class RBACRepository:
    """Repository para operaciones RBAC en MongoDB."""
    
    def __init__(self, db):
        self.db = db
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Crea índices necesarios."""
        try:
            # Permisos
            self.db.rbac_permisos.create_index("codigo", unique=True)
            self.db.rbac_permisos.create_index("modulo")
            
            # Roles
            self.db.rbac_roles.create_index("nombre", unique=True)
            self.db.rbac_roles.create_index("activo")
            
            # Asignaciones usuario-rol
            self.db.rbac_usuarios_roles.create_index("user_id")
            self.db.rbac_usuarios_roles.create_index("rol_id")
            self.db.rbac_usuarios_roles.create_index([("user_id", 1), ("rol_id", 1), ("sucursal_id", 1)], unique=True)
            
            # Audit log
            self.db.rbac_audit_log.create_index("user_id")
            self.db.rbac_audit_log.create_index("fecha")
            self.db.rbac_audit_log.create_index([("fecha", -1)])
            
            logger.info("Índices RBAC creados/verificados")
        except Exception as e:
            logger.warning(f"Error creando índices RBAC: {e}")
    
    # =========================================================================
    # PERMISOS
    # =========================================================================
    
    def get_all_permisos(self, activos_only: bool = True) -> List[Dict]:
        """Obtiene todos los permisos."""
        filtro = {"activo": True} if activos_only else {}
        return list(self.db.rbac_permisos.find(filtro, {"_id": 0}))
    
    def get_permiso_by_codigo(self, codigo: str) -> Optional[Dict]:
        """Obtiene un permiso por su código."""
        return self.db.rbac_permisos.find_one({"codigo": codigo}, {"_id": 0})
    
    def create_permiso(self, permiso: Dict) -> Dict:
        """Crea un nuevo permiso."""
        permiso["id"] = permiso.get("id") or str(uuid.uuid4())
        permiso["created_at"] = datetime.now(timezone.utc)
        permiso["activo"] = True
        permiso["es_sistema"] = permiso.get("es_sistema", False)
        self.db.rbac_permisos.insert_one(permiso)
        return {k: v for k, v in permiso.items() if k != "_id"}
    
    def seed_permisos(self, permisos: List[Dict]) -> int:
        """Siembra permisos del sistema si no existen."""
        count = 0
        for p in permisos:
            existing = self.db.rbac_permisos.find_one({"codigo": p["codigo"]})
            if not existing:
                self.create_permiso({
                    "codigo": p["codigo"],
                    "modulo": p["modulo"],
                    "accion": p["accion"],
                    "descripcion": p["descripcion"],
                    "es_sistema": True,
                })
                count += 1
        return count
    
    # =========================================================================
    # ROLES
    # =========================================================================
    
    def get_all_roles(self, activos_only: bool = True) -> List[Dict]:
        """Obtiene todos los roles."""
        filtro = {"activo": True} if activos_only else {}
        return list(self.db.rbac_roles.find(filtro, {"_id": 0}))
    
    def get_rol_by_id(self, rol_id: str) -> Optional[Dict]:
        """Obtiene un rol por ID."""
        return self.db.rbac_roles.find_one({"id": rol_id}, {"_id": 0})
    
    def get_rol_by_nombre(self, nombre: str) -> Optional[Dict]:
        """Obtiene un rol por nombre."""
        return self.db.rbac_roles.find_one({"nombre": nombre}, {"_id": 0})
    
    def create_rol(self, rol: Dict) -> Dict:
        """Crea un nuevo rol."""
        now = datetime.now(timezone.utc)
        rol["id"] = rol.get("id") or str(uuid.uuid4())
        rol["created_at"] = now
        rol["updated_at"] = now
        rol["activo"] = True
        rol["es_sistema"] = rol.get("es_sistema", False)
        rol["nivel_jerarquia"] = rol.get("nivel_jerarquia", 0)
        self.db.rbac_roles.insert_one(rol)
        return {k: v for k, v in rol.items() if k != "_id"}
    
    def update_rol(self, rol_id: str, data: Dict) -> Optional[Dict]:
        """Actualiza un rol."""
        data["updated_at"] = datetime.now(timezone.utc)
        result = self.db.rbac_roles.find_one_and_update(
            {"id": rol_id},
            {"$set": data},
            return_document=True
        )
        return {k: v for k, v in result.items() if k != "_id"} if result else None
    
    def delete_rol(self, rol_id: str) -> bool:
        """Elimina un rol (soft delete)."""
        result = self.db.rbac_roles.update_one(
            {"id": rol_id, "es_sistema": False},
            {"$set": {"activo": False, "updated_at": datetime.now(timezone.utc)}}
        )
        return result.modified_count > 0
    
    def seed_roles(self, roles: List[Dict]) -> int:
        """Siembra roles del sistema si no existen."""
        count = 0
        for r in roles:
            existing = self.db.rbac_roles.find_one({"nombre": r["nombre"]})
            if not existing:
                self.create_rol({
                    "nombre": r["nombre"],
                    "descripcion": r["descripcion"],
                    "permisos": r["permisos"],
                    "nivel_jerarquia": r["nivel_jerarquia"],
                    "es_sistema": r.get("es_sistema", True),
                })
                count += 1
        return count
    
    # =========================================================================
    # ASIGNACIONES USUARIO-ROL
    # =========================================================================
    
    def get_roles_usuario(self, user_id: str, activos_only: bool = True) -> List[Dict]:
        """Obtiene los roles asignados a un usuario."""
        filtro = {"user_id": user_id}
        if activos_only:
            filtro["activo"] = True
        
        asignaciones = list(self.db.rbac_usuarios_roles.find(filtro, {"_id": 0}))
        
        # Enriquecer con datos del rol
        roles = []
        for asig in asignaciones:
            rol = self.get_rol_by_id(asig["rol_id"])
            if rol and rol.get("activo"):
                roles.append({
                    "asignacion_id": asig["id"],
                    "rol": rol,
                    "sucursal_id": asig.get("sucursal_id"),
                    "fecha_asignacion": asig.get("fecha_asignacion"),
                })
        
        return roles
    
    def asignar_rol(self, user_id: str, rol_id: str, asignado_por: str, sucursal_id: Optional[str] = None) -> Dict:
        """Asigna un rol a un usuario."""
        # Verificar si ya existe
        existing = self.db.rbac_usuarios_roles.find_one({
            "user_id": user_id,
            "rol_id": rol_id,
            "sucursal_id": sucursal_id
        })
        
        if existing:
            # Reactivar si estaba inactivo
            if not existing.get("activo"):
                self.db.rbac_usuarios_roles.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {"activo": True, "asignado_por": asignado_por, "fecha_asignacion": datetime.now(timezone.utc)}}
                )
            return {k: v for k, v in existing.items() if k != "_id"}
        
        # Obtener nombre del rol para desnormalizar
        rol = self.get_rol_by_id(rol_id)
        rol_nombre = rol["nombre"] if rol else ""
        
        asignacion = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "rol_id": rol_id,
            "rol_nombre": rol_nombre,
            "sucursal_id": sucursal_id,
            "activo": True,
            "asignado_por": asignado_por,
            "fecha_asignacion": datetime.now(timezone.utc),
        }
        
        self.db.rbac_usuarios_roles.insert_one(asignacion)
        return {k: v for k, v in asignacion.items() if k != "_id"}
    
    def revocar_rol(self, user_id: str, rol_id: str, sucursal_id: Optional[str] = None) -> bool:
        """Revoca un rol de un usuario."""
        result = self.db.rbac_usuarios_roles.update_one(
            {"user_id": user_id, "rol_id": rol_id, "sucursal_id": sucursal_id},
            {"$set": {"activo": False}}
        )
        return result.modified_count > 0
    
    def get_permisos_usuario(self, user_id: str) -> List[str]:
        """Obtiene todos los permisos efectivos de un usuario."""
        roles_data = self.get_roles_usuario(user_id)
        
        permisos_set = set()
        for rd in roles_data:
            rol = rd.get("rol", {})
            for permiso in rol.get("permisos", []):
                permisos_set.add(permiso)
        
        return list(permisos_set)
    
    def get_nivel_jerarquia_usuario(self, user_id: str) -> int:
        """Obtiene el nivel jerárquico máximo del usuario."""
        roles_data = self.get_roles_usuario(user_id)
        if not roles_data:
            return 0
        return max(rd.get("rol", {}).get("nivel_jerarquia", 0) for rd in roles_data)
    
    # =========================================================================
    # AUDITORÍA
    # =========================================================================
    
    def log_verificacion(
        self,
        user_id: str,
        permiso_requerido: str,
        resultado: str,
        user_email: Optional[str] = None,
        endpoint: Optional[str] = None,
        metodo_http: Optional[str] = None,
        ip_address: Optional[str] = None,
        detalles: Optional[Dict] = None
    ) -> str:
        """Registra una verificación de permiso en el log de auditoría."""
        log_entry = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "user_email": user_email,
            "permiso_requerido": permiso_requerido,
            "resultado": resultado,
            "endpoint": endpoint,
            "metodo_http": metodo_http,
            "ip_address": ip_address,
            "detalles": detalles,
            "fecha": datetime.now(timezone.utc),
        }
        self.db.rbac_audit_log.insert_one(log_entry)
        return log_entry["id"]
    
    def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        resultado: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Obtiene logs de auditoría."""
        filtro = {}
        if user_id:
            filtro["user_id"] = user_id
        if resultado:
            filtro["resultado"] = resultado
        
        return list(
            self.db.rbac_audit_log.find(filtro, {"_id": 0})
            .sort("fecha", -1)
            .limit(limit)
        )


__all__ = ['RBACRepository']
