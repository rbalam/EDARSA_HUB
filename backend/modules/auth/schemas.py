"""
EDARSA HUB - Auth Module Schemas
================================
Modelos Pydantic para autenticación, usuarios y roles.

FASE 3 DEL REFACTOR MODULAR (Diciembre 2025):
- Migrado desde server.py
- Schemas de User, UserCreate, UserLogin, UserRole
"""

from typing import List, Dict, Optional
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserRole(BaseModel):
    """Modelo de rol de usuario (legacy, no usado actualmente)"""
    name: str  # "Administrador", "Supervisor", "Usuario"
    permissions: List[str]


class User(BaseModel):
    """Modelo de usuario completo"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    role: str
    telefono: Optional[str] = None  # Subfase 2B.5 - Teléfono para WhatsApp (formato E.164)
    sucursales: List[str] = []  # IDs de sucursales asignadas (legacy)
    allowed_servers: List[str] = []  # IDs de servidores permitidos
    allowed_sucursales: Dict[str, List[str]] = {}  # server_id -> [sucursal_ids]
    allowed_warehouses: Dict[str, List[str]] = {}  # server_id -> [warehouse_codes]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    active: bool = True
    # FASE 7: Campos RBAC piloto (solo visualización/administración en UI)
    sec_permisos: List[str] = []  # FASE 4: Permisos directos
    sec_rol: Optional[str] = None  # FASE 5: Rol único (compatibilidad)
    sec_roles: List[str] = []  # FASE 6: Múltiples roles
    sec_perfil: Optional[str] = None  # FASE 13: Perfil predefinido (metadato)
    # FASE 14: Alcance organizacional por rol (METADATO, no filtrado activo)
    sec_roles_alcance: Dict[str, Dict] = {}  # rol_codigo -> {tipo, empresa_id, unidades_ids, sucursales_ids, almacenes_ids}


class UserCreate(BaseModel):
    """Modelo para crear un nuevo usuario"""
    email: EmailStr
    name: str
    password: str
    role: str
    telefono: Optional[str] = None  # Subfase 2B.5 - Teléfono para WhatsApp
    sucursales: List[str] = []
    allowed_servers: List[str] = []
    allowed_sucursales: Dict[str, List[str]] = {}
    allowed_warehouses: Dict[str, List[str]] = {}


class UserLogin(BaseModel):
    """Modelo para login de usuario"""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Modelo para actualizar un usuario"""
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    telefono: Optional[str] = None  # Subfase 2B.5 - Teléfono para WhatsApp
    sucursales: Optional[List[str]] = None
    password: Optional[str] = None


class UserPermissions(BaseModel):
    """Modelo para actualizar permisos de usuario"""
    allowed_servers: Optional[List[str]] = None
    allowed_sucursales: Optional[Dict[str, List[str]]] = None
    allowed_warehouses: Optional[Dict[str, List[str]]] = None


class Role(BaseModel):
    """Modelo de rol del sistema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nombre: str
    descripcion: str = ""
    permisos: List[str] = []
    es_sistema: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RoleCreate(BaseModel):
    """Modelo para crear un nuevo rol"""
    nombre: str
    descripcion: str = ""
    permisos: List[str] = []


class RoleUpdate(BaseModel):
    """Modelo para actualizar un rol"""
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    permisos: Optional[List[str]] = None


# Módulos disponibles para asignar permisos
MODULOS_DISPONIBLES = [
    {"id": "tablero_ejecutivo", "nombre": "Tablero Ejecutivo", "descripcion": "Vista consolidada de todas las unidades"},
    {"id": "comercial", "nombre": "Comercial", "descripcion": "Dashboard de ventas, ticket perfecto, metas"},
    {"id": "compras", "nombre": "Compras", "descripcion": "Dashboard de compras, autorización, análisis"},
    {"id": "inventarios", "nombre": "Inventarios", "descripcion": "Análisis de inventarios, reportes"},
    {"id": "dashboard_inventarios", "nombre": "Dashboard Inventarios", "descripcion": "Gráficas de diferencias de inventario"},
    {"id": "finanzas", "nombre": "Finanzas", "descripcion": "Libro mayor, cuentas, conciliación"},
    {"id": "produccion", "nombre": "Producción", "descripcion": "Órdenes de producción, BOM"},
    {"id": "recursos_humanos", "nombre": "Recursos Humanos", "descripcion": "Nómina, asistencias"},
    {"id": "reportes_bi", "nombre": "Reportes BI", "descripcion": "Análisis predictivo, KPIs avanzados"},
    {"id": "servidores", "nombre": "Servidores", "descripcion": "Configuración de conexiones a BD"},
    {"id": "catalogo_sql", "nombre": "Catálogo SQL", "descripcion": "Consultas SQL personalizadas"},
    {"id": "explorador_bd", "nombre": "Explorador BD", "descripcion": "Explorar estructura de bases de datos"},
    {"id": "alertas", "nombre": "Alertas", "descripcion": "Configuración de alertas del sistema"},
    {"id": "usuarios", "nombre": "Usuarios", "descripcion": "Gestión de usuarios y roles"},
]


# Roles predeterminados del sistema
DEFAULT_ROLES = [
    {
        "nombre": "Administrador",
        "descripcion": "Acceso total al sistema",
        "permisos": [m["id"] for m in MODULOS_DISPONIBLES],
        "es_sistema": True,
    },
    {
        "nombre": "Supervisor",
        "descripcion": "Acceso a módulos operativos y reportes",
        "permisos": ["tablero_ejecutivo", "comercial", "compras", "inventarios", "dashboard_inventarios", "catalogo_sql", "alertas"],
        "es_sistema": True,
    },
    {
        "nombre": "Usuario",
        "descripcion": "Acceso básico de consulta",
        "permisos": ["comercial", "compras", "inventarios", "dashboard_inventarios"],
        "es_sistema": True,
    }
]


__all__ = [
    'UserRole',
    'User',
    'UserCreate',
    'UserLogin',
    'UserUpdate',
    'UserPermissions',
    'Role',
    'RoleCreate',
    'RoleUpdate',
    'MODULOS_DISPONIBLES',
    'DEFAULT_ROLES',
]
