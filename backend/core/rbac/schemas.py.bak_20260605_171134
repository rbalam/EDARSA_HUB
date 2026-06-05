"""
EDARSA HUB - RBAC Schemas
=========================
Modelos Pydantic para el sistema RBAC avanzado.

Colecciones MongoDB:
- rbac_permisos: Catálogo de permisos del sistema
- rbac_roles: Roles con sus permisos asignados
- rbac_usuarios_roles: Asignación de roles a usuarios
- rbac_audit_log: Auditoría de verificaciones de permisos
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class ModuloSistema(str, Enum):
    """Módulos del sistema para agrupar permisos."""
    OPERATIVO = "operativo"
    SLA = "sla"
    CARGOS = "cargos"
    RESPONSABILIDAD = "responsabilidad"
    NOTIFICACIONES = "notificaciones"
    SCHEDULER = "scheduler"
    WORKFLOW = "workflow"
    AUTH = "auth"
    REPORTES = "reportes"
    CONFIGURACION = "configuracion"


class AccionPermiso(str, Enum):
    """Acciones posibles sobre recursos."""
    VER = "ver"
    CREAR = "crear"
    EDITAR = "editar"
    ELIMINAR = "eliminar"
    AUTORIZAR = "autorizar"
    APLICAR = "aplicar"
    REVERTIR = "revertir"
    CONFIGURAR = "configurar"
    ENVIAR = "enviar"
    GESTIONAR = "gestionar"
    ADMIN = "admin"


# =============================================================================
# PERMISOS
# =============================================================================

class Permiso(BaseModel):
    """Modelo de permiso del sistema."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    codigo: str = Field(..., description="Código único del permiso (ej: CARGOS_APLICAR)")
    modulo: ModuloSistema
    accion: AccionPermiso
    descripcion: str
    es_sistema: bool = Field(default=True, description="Permiso del sistema (no eliminable)")
    activo: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PermisoCreate(BaseModel):
    """Modelo para crear un permiso."""
    codigo: str
    modulo: ModuloSistema
    accion: AccionPermiso
    descripcion: str


class PermisoResponse(BaseModel):
    """Respuesta de permiso."""
    id: str
    codigo: str
    modulo: str
    accion: str
    descripcion: str
    activo: bool


# =============================================================================
# ROLES RBAC
# =============================================================================

class RolRBAC(BaseModel):
    """Modelo de rol RBAC."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nombre: str = Field(..., description="Nombre único del rol")
    descripcion: str = ""
    permisos: List[str] = Field(default=[], description="Lista de códigos de permisos")
    es_sistema: bool = Field(default=False, description="Rol del sistema (no eliminable)")
    nivel_jerarquia: int = Field(default=0, description="Nivel jerárquico (mayor = más autoridad)")
    activo: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RolRBACCreate(BaseModel):
    """Modelo para crear un rol."""
    nombre: str
    descripcion: str = ""
    permisos: List[str] = []
    nivel_jerarquia: int = 0


class RolRBACUpdate(BaseModel):
    """Modelo para actualizar un rol."""
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    permisos: Optional[List[str]] = None
    nivel_jerarquia: Optional[int] = None
    activo: Optional[bool] = None


class RolRBACResponse(BaseModel):
    """Respuesta de rol."""
    id: str
    nombre: str
    descripcion: str
    permisos: List[str]
    nivel_jerarquia: int
    es_sistema: bool
    activo: bool


# =============================================================================
# ASIGNACIÓN DE ROLES A USUARIOS
# =============================================================================

class AsignacionRol(BaseModel):
    """Asignación de un rol a un usuario."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    rol_id: str
    rol_nombre: str = ""  # Desnormalizado para consultas rápidas
    sucursal_id: Optional[str] = Field(None, description="Si es None, es global")
    activo: bool = True
    asignado_por: str = ""
    fecha_asignacion: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    fecha_expiracion: Optional[datetime] = None


class AsignacionRolCreate(BaseModel):
    """Modelo para asignar un rol a un usuario."""
    user_id: str
    rol_id: str
    sucursal_id: Optional[str] = None
    fecha_expiracion: Optional[datetime] = None


class AsignacionRolResponse(BaseModel):
    """Respuesta de asignación de rol."""
    id: str
    user_id: str
    rol_id: str
    rol_nombre: str
    sucursal_id: Optional[str]
    activo: bool
    fecha_asignacion: datetime


# =============================================================================
# RESPUESTAS DE CONSULTA
# =============================================================================

class PermisoUsuarioResponse(BaseModel):
    """Permisos efectivos de un usuario."""
    user_id: str
    roles: List[RolRBACResponse]
    permisos: List[str]  # Lista de códigos de permisos únicos
    nivel_jerarquia_max: int
    es_admin: bool


class VerificacionPermisoResponse(BaseModel):
    """Resultado de verificación de permiso."""
    permitido: bool
    user_id: str
    permiso_requerido: str
    permisos_usuario: List[str]
    mensaje: str


# =============================================================================
# AUDITORÍA RBAC
# =============================================================================

class RBACAuditLog(BaseModel):
    """Registro de auditoría de verificaciones de permisos."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_email: Optional[str] = None
    permiso_requerido: str
    resultado: str  # "PERMITIDO" | "DENEGADO"
    endpoint: Optional[str] = None
    metodo_http: Optional[str] = None
    ip_address: Optional[str] = None
    detalles: Optional[Dict[str, Any]] = None
    fecha: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# =============================================================================
# PERMISOS DEL SISTEMA (SEED)
# =============================================================================

PERMISOS_SISTEMA = [
    # === CARGOS ECONÓMICOS ===
    {"codigo": "CARGOS_VER", "modulo": "cargos", "accion": "ver", "descripcion": "Ver cargos económicos"},
    {"codigo": "CARGOS_CREAR", "modulo": "cargos", "accion": "crear", "descripcion": "Crear propuestas de cargo"},
    {"codigo": "CARGOS_AUTORIZAR", "modulo": "cargos", "accion": "autorizar", "descripcion": "Autorizar cargos pendientes"},
    {"codigo": "CARGOS_APLICAR", "modulo": "cargos", "accion": "aplicar", "descripcion": "Aplicar cargos autorizados"},
    {"codigo": "CARGOS_RECHAZAR", "modulo": "cargos", "accion": "editar", "descripcion": "Rechazar cargos"},
    {"codigo": "CARGOS_REVERTIR", "modulo": "cargos", "accion": "revertir", "descripcion": "Revertir cargos aplicados"},
    {"codigo": "CARGOS_CANCELAR", "modulo": "cargos", "accion": "eliminar", "descripcion": "Cancelar cargos"},
    
    # === RESPONSABILIDAD ECONÓMICA ===
    {"codigo": "RESPONSABILIDAD_VER", "modulo": "responsabilidad", "accion": "ver", "descripcion": "Ver responsabilidades económicas"},
    {"codigo": "RESPONSABILIDAD_CALCULAR", "modulo": "responsabilidad", "accion": "crear", "descripcion": "Calcular responsabilidad económica"},
    {"codigo": "RESPONSABILIDAD_PROPONER", "modulo": "responsabilidad", "accion": "crear", "descripcion": "Proponer responsabilidad"},
    {"codigo": "RESPONSABILIDAD_APROBAR", "modulo": "responsabilidad", "accion": "autorizar", "descripcion": "Aprobar responsabilidad"},
    {"codigo": "RESPONSABILIDAD_RECHAZAR", "modulo": "responsabilidad", "accion": "editar", "descripcion": "Rechazar responsabilidad"},
    {"codigo": "RESPONSABILIDAD_EXONERAR", "modulo": "responsabilidad", "accion": "autorizar", "descripcion": "Exonerar responsabilidad"},
    {"codigo": "RESPONSABILIDAD_DISPUTAR", "modulo": "responsabilidad", "accion": "crear", "descripcion": "Disputar responsabilidad"},
    {"codigo": "RESPONSABILIDAD_GESTIONAR", "modulo": "responsabilidad", "accion": "gestionar", "descripcion": "Gestión completa de responsabilidades"},
    
    # === SLA ===
    {"codigo": "SLA_VER", "modulo": "sla", "accion": "ver", "descripcion": "Ver métricas y estado SLA"},
    {"codigo": "SLA_CONFIGURAR", "modulo": "sla", "accion": "configurar", "descripcion": "Configurar umbrales SLA"},
    
    # === WORKFLOWS ===
    {"codigo": "WORKFLOW_VER", "modulo": "workflow", "accion": "ver", "descripcion": "Ver workflows"},
    {"codigo": "WORKFLOW_CREAR", "modulo": "workflow", "accion": "crear", "descripcion": "Crear workflows"},
    {"codigo": "WORKFLOW_GESTIONAR", "modulo": "workflow", "accion": "gestionar", "descripcion": "Gestionar workflows"},
    {"codigo": "WORKFLOW_CERRAR", "modulo": "workflow", "accion": "editar", "descripcion": "Cerrar workflows"},
    
    # === TAREAS ===
    {"codigo": "TAREAS_VER", "modulo": "operativo", "accion": "ver", "descripcion": "Ver tareas"},
    {"codigo": "TAREAS_CREAR", "modulo": "operativo", "accion": "crear", "descripcion": "Crear tareas"},
    {"codigo": "TAREAS_ASIGNAR", "modulo": "operativo", "accion": "editar", "descripcion": "Asignar tareas"},
    {"codigo": "TAREAS_COMPLETAR", "modulo": "operativo", "accion": "editar", "descripcion": "Completar tareas"},
    
    # === NOTIFICACIONES ===
    {"codigo": "NOTIFICACIONES_VER", "modulo": "notificaciones", "accion": "ver", "descripcion": "Ver configuración de notificaciones"},
    {"codigo": "NOTIFICACIONES_ENVIAR", "modulo": "notificaciones", "accion": "enviar", "descripcion": "Enviar notificaciones manuales"},
    {"codigo": "NOTIFICACIONES_CONFIGURAR", "modulo": "notificaciones", "accion": "configurar", "descripcion": "Configurar eventos y templates"},
    
    # === SCHEDULER ===
    {"codigo": "SCHEDULER_VER", "modulo": "scheduler", "accion": "ver", "descripcion": "Ver estado del scheduler"},
    {"codigo": "SCHEDULER_GESTIONAR", "modulo": "scheduler", "accion": "gestionar", "descripcion": "Pausar/reanudar jobs"},
    {"codigo": "SCHEDULER_ADMIN", "modulo": "scheduler", "accion": "admin", "descripcion": "Administración completa del scheduler"},
    
    # === AUDITORÍAS PROGRAMADAS ===
    {"codigo": "AUDITORIA_VER", "modulo": "auditorias", "accion": "ver", "descripcion": "Ver auditorías programadas, historial, KPIs"},
    {"codigo": "AUDITORIA_PROGRAMAR", "modulo": "auditorias", "accion": "programar", "descripcion": "Crear, editar, activar/desactivar auditorías"},
    {"codigo": "AUDITORIA_GESTIONAR", "modulo": "auditorias", "accion": "gestionar", "descripcion": "Ejecutar manualmente, eliminar auditorías"},
    
    # === REPORTES ===
    {"codigo": "REPORTES_VER", "modulo": "reportes", "accion": "ver", "descripcion": "Ver reportes"},
    {"codigo": "REPORTES_EXPORTAR", "modulo": "reportes", "accion": "crear", "descripcion": "Exportar reportes"},
    
    # === CONFIGURACIÓN ===
    {"codigo": "CONFIG_VER", "modulo": "configuracion", "accion": "ver", "descripcion": "Ver configuración del sistema"},
    {"codigo": "CONFIG_EDITAR", "modulo": "configuracion", "accion": "configurar", "descripcion": "Editar configuración del sistema"},
    
    # === AUTH/RBAC ===
    {"codigo": "USUARIOS_VER", "modulo": "auth", "accion": "ver", "descripcion": "Ver usuarios"},
    {"codigo": "USUARIOS_GESTIONAR", "modulo": "auth", "accion": "gestionar", "descripcion": "Gestionar usuarios"},
    {"codigo": "ROLES_VER", "modulo": "auth", "accion": "ver", "descripcion": "Ver roles"},
    {"codigo": "ROLES_GESTIONAR", "modulo": "auth", "accion": "gestionar", "descripcion": "Gestionar roles y permisos"},
    {"codigo": "RBAC_ADMIN", "modulo": "auth", "accion": "admin", "descripcion": "Administración completa RBAC"},
]


# =============================================================================
# ROLES DEL SISTEMA (SEED)
# =============================================================================

ROLES_SISTEMA = [
    {
        "nombre": "ADMIN",
        "descripcion": "Administrador del sistema con acceso total",
        "nivel_jerarquia": 100,
        "es_sistema": True,
        "permisos": [p["codigo"] for p in PERMISOS_SISTEMA],  # Todos los permisos
    },
    {
        "nombre": "DIRECCION",
        "descripcion": "Nivel dirección - autoriza montos altos y reversas",
        "nivel_jerarquia": 80,
        "es_sistema": True,
        "permisos": [
            "CARGOS_VER", "CARGOS_CREAR", "CARGOS_AUTORIZAR", "CARGOS_APLICAR", "CARGOS_RECHAZAR", "CARGOS_REVERTIR", "CARGOS_CANCELAR",
            "RESPONSABILIDAD_VER", "RESPONSABILIDAD_APROBAR", "RESPONSABILIDAD_RECHAZAR", "RESPONSABILIDAD_EXONERAR", "RESPONSABILIDAD_GESTIONAR",
            "SLA_VER", "SLA_CONFIGURAR",
            "WORKFLOW_VER", "WORKFLOW_GESTIONAR", "WORKFLOW_CERRAR",
            "TAREAS_VER", "TAREAS_ASIGNAR",
            "NOTIFICACIONES_VER", "NOTIFICACIONES_CONFIGURAR",
            "SCHEDULER_VER", "SCHEDULER_ADMIN",
            "AUDITORIA_VER", "AUDITORIA_PROGRAMAR", "AUDITORIA_GESTIONAR",
            "REPORTES_VER", "REPORTES_EXPORTAR",
            "USUARIOS_VER", "ROLES_VER",
        ],
    },
    {
        "nombre": "GERENTE_OPS",
        "descripcion": "Gerente de operaciones - autoriza y aplica cargos",
        "nivel_jerarquia": 60,
        "es_sistema": True,
        "permisos": [
            "CARGOS_VER", "CARGOS_CREAR", "CARGOS_AUTORIZAR", "CARGOS_APLICAR", "CARGOS_RECHAZAR", "CARGOS_REVERTIR",
            "RESPONSABILIDAD_VER", "RESPONSABILIDAD_APROBAR", "RESPONSABILIDAD_RECHAZAR", "RESPONSABILIDAD_GESTIONAR",
            "SLA_VER",
            "WORKFLOW_VER", "WORKFLOW_GESTIONAR",
            "TAREAS_VER", "TAREAS_CREAR", "TAREAS_ASIGNAR", "TAREAS_COMPLETAR",
            "NOTIFICACIONES_VER",
            "SCHEDULER_VER", "SCHEDULER_GESTIONAR",
            "AUDITORIA_VER", "AUDITORIA_PROGRAMAR",
            "REPORTES_VER", "REPORTES_EXPORTAR",
        ],
    },
    {
        "nombre": "SUPERVISOR",
        "descripcion": "Supervisor - crea propuestas y gestiona tareas",
        "nivel_jerarquia": 40,
        "es_sistema": True,
        "permisos": [
            "CARGOS_VER", "CARGOS_CREAR", "CARGOS_AUTORIZAR",
            "RESPONSABILIDAD_VER", "RESPONSABILIDAD_CALCULAR", "RESPONSABILIDAD_PROPONER",
            "SLA_VER",
            "WORKFLOW_VER", "WORKFLOW_CREAR",
            "TAREAS_VER", "TAREAS_CREAR", "TAREAS_ASIGNAR", "TAREAS_COMPLETAR",
            "NOTIFICACIONES_VER",
            "SCHEDULER_VER",
            "AUDITORIA_VER",
            "REPORTES_VER",
        ],
    },
    {
        "nombre": "OPERADOR",
        "descripcion": "Operador - ejecuta tareas y registra información",
        "nivel_jerarquia": 20,
        "es_sistema": True,
        "permisos": [
            "CARGOS_VER",
            "RESPONSABILIDAD_VER", "RESPONSABILIDAD_DISPUTAR",
            "SLA_VER",
            "WORKFLOW_VER",
            "TAREAS_VER", "TAREAS_COMPLETAR",
            "REPORTES_VER",
        ],
    },
    {
        "nombre": "AUDITOR",
        "descripcion": "Auditor - solo lectura para fiscalización",
        "nivel_jerarquia": 30,
        "es_sistema": True,
        "permisos": [
            "CARGOS_VER",
            "RESPONSABILIDAD_VER",
            "SLA_VER",
            "WORKFLOW_VER",
            "TAREAS_VER",
            "NOTIFICACIONES_VER",
            "SCHEDULER_VER",
            "AUDITORIA_VER",
            "REPORTES_VER", "REPORTES_EXPORTAR",
            "USUARIOS_VER", "ROLES_VER",
        ],
    },
]


__all__ = [
    'ModuloSistema',
    'AccionPermiso',
    'Permiso',
    'PermisoCreate',
    'PermisoResponse',
    'RolRBAC',
    'RolRBACCreate',
    'RolRBACUpdate',
    'RolRBACResponse',
    'AsignacionRol',
    'AsignacionRolCreate',
    'AsignacionRolResponse',
    'PermisoUsuarioResponse',
    'VerificacionPermisoResponse',
    'RBACAuditLog',
    'PERMISOS_SISTEMA',
    'ROLES_SISTEMA',
]
