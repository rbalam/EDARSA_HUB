from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
Router SQL-First para Administración de Usuarios, Roles y Permisos
==================================================================

ARQUITECTURA: SQL-FIRST desde EDARSAHUB_SQL
TABLAS FUENTE:
  - Usuario_Catalogo
  - Usuario_Roles
  - Usuario_RolesAsignacion
  - Usuario_Modulos
  - Usuario_ServidoresAsignacion
  - Usuario_SucursalesAsignacion
  - Servidores_Conexiones

FECHA: Junio 2026
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from core.security import get_current_user
from core.config.edarsahub_sql import get_edarsahub_connection
from modules.admin_sql import rbac_pilot_service
import logging

router = APIRouter(prefix="/api/admin-sql", tags=["Admin SQL"])


def is_admin(user: Dict[str, Any]) -> bool:
    """Verifica si el usuario es administrador."""
    role = str(user.get("role") or user.get("rol") or "").upper()
    email = str(user.get("email") or "").lower()
    return (
        "ADMIN" in role
        or "SUPER" in role
        or email in ["admin@edarsa.com", "ricardo@edarsa.com.mx"]
    )


def require_admin(user: Dict[str, Any]) -> None:
    """Lanza excepción si el usuario no es admin."""
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="No autorizado - Se requiere rol de administrador")


def execute_query(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Ejecuta una consulta SQL y devuelve los resultados como lista de diccionarios."""
    try:
        cn = get_edarsahub_connection()
        cur = cn.cursor(as_dict=True)
        cur.execute(sql, params)
        rows = cur.fetchall()
        cn.close()
        return rows
    except Exception as e:
        logging.error(f"[ADMIN_SQL] Error ejecutando query: {e}")
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")


@router.get("/users")
async def get_users(current_user: dict = Depends(get_current_user)):
    """
    Lista todos los usuarios del sistema desde EDARSAHUB SQL.
    
    Incluye:
    - Datos básicos del usuario
    - Rol principal asignado
    - Servidores asignados
    - Sucursales asignadas
    """
    require_admin(current_user)

    # Obtener usuarios con su rol principal
    users = execute_query("""
    SELECT
        CAST(u.UsuarioID AS NVARCHAR(100)) AS id,
        CAST(u.UsuarioID AS NVARCHAR(100)) AS UsuarioID,
        u.PublicUUID,
        u.Username AS username,
        u.Email AS email,
        u.Nombre AS nombre,
        u.NombreCompleto AS name,
        u.NombreCompleto AS nombre_completo,
        u.Apellidos AS apellidos,
        u.Puesto AS puesto,
        u.Departamento AS departamento,
        ISNULL(u.Activo, 1) AS activo,
        ISNULL(u.Bloqueado, 0) AS bloqueado,
        r.NombreRol AS role,
        r.CodigoRol AS role_code,
        r.RolID
    FROM Usuario_Catalogo u
    LEFT JOIN Usuario_RolesAsignacion ura
        ON ura.UsuarioID = u.UsuarioID
       AND ISNULL(ura.Activo, 1) = 1
       AND ISNULL(ura.EsPrincipal, 1) = 1
    LEFT JOIN Usuario_Roles r
        ON r.RolID = ura.RolID
    WHERE ISNULL(u.Activo, 1) = 1
    ORDER BY u.NombreCompleto, u.Email
    """)

    # Obtener asignaciones de servidores
    servidores = execute_query("""
    SELECT
        CAST(UsuarioID AS NVARCHAR(100)) AS UsuarioID,
        CAST(ServidorID AS NVARCHAR(100)) AS ServidorID
    FROM Usuario_ServidoresAsignacion
    WHERE ISNULL(Activo, 1) = 1
    """)

    # Obtener asignaciones de sucursales
    sucursales = execute_query("""
    SELECT
        CAST(UsuarioID AS NVARCHAR(100)) AS UsuarioID,
        CAST(ServidorID AS NVARCHAR(100)) AS ServidorID,
        SucursalCodigo
    FROM Usuario_SucursalesAsignacion
    WHERE ISNULL(Activo, 1) = 1
    """)

    # Mapear servidores por usuario
    map_serv = {}
    for s in servidores:
        uid = str(s.get("UsuarioID", ""))
        if uid:
            map_serv.setdefault(uid, []).append(str(s.get("ServidorID", "")))

    # Mapear sucursales por usuario
    map_suc = {}
    for s in sucursales:
        uid = str(s.get("UsuarioID", ""))
        if uid:
            map_suc.setdefault(uid, []).append(str(s.get("SucursalCodigo", "")))

    # Enriquecer usuarios con asignaciones
    rbac_map = rbac_pilot_service.get_rbac_map()
    for u in users:
        uid = str(u.get("UsuarioID", ""))
        u["allowed_servers"] = map_serv.get(uid, [])
        u["allowed_sucursales"] = map_suc.get(uid, [])
        u["allowed_warehouses"] = []
        u["sucursales"] = u["allowed_sucursales"]
        rbac = rbac_map.get(uid, {})
        u["sec_perfil"] = rbac.get("sec_perfil")
        u["sec_roles"] = rbac.get("sec_roles", [])
        u["sec_permisos"] = rbac.get("sec_permisos", [])

    return users


@router.get("/roles")
async def get_roles(current_user: dict = Depends(get_current_user)):
    """
    Lista todos los roles del sistema desde EDARSAHUB SQL.
    """
    require_admin(current_user)

    roles = execute_query("""
    SELECT
        CAST(RolID AS NVARCHAR(100)) AS id,
        RolID,
        CodigoRol AS codigo,
        NombreRol AS name,
        NombreRol AS nombre,
        Descripcion AS descripcion,
        ISNULL(EsRolSistema, 0) AS es_sistema,
        ISNULL(Activo, 1) AS activo,
        NivelJerarquia AS nivel
    FROM Usuario_Roles
    WHERE ISNULL(Activo, 1) = 1
    ORDER BY NivelJerarquia, NombreRol
    """)

    # Obtener permisos por rol
    permisos = execute_query("""
    SELECT
        prm.RolID,
        m.ModuloID,
        CAST(m.ModuloID AS NVARCHAR(100)) AS modulo_id,
        m.CodigoModulo AS codigo,
        m.NombreModulo AS nombre,
        a.CodigoAccion AS accion,
        prm.Permitido
    FROM Usuario_PermisosRolModulo prm
    LEFT JOIN Usuario_Modulos m ON m.ModuloID = prm.ModuloID
    LEFT JOIN Usuario_Acciones a ON a.AccionID = prm.AccionID
    WHERE ISNULL(prm.Activo, 1) = 1
      AND ISNULL(prm.Permitido, 1) = 1
    """)

    # Mapear permisos por rol
    pmap = {}
    for p in permisos:
        rid = p.get("RolID")
        if rid:
            pmap.setdefault(rid, []).append(p.get("modulo_id"))

    # Enriquecer roles con permisos
    for r in roles:
        r["permisos"] = pmap.get(r.get("RolID"), [])

    return roles


@router.get("/roles/modulos")
async def get_modulos(current_user: dict = Depends(get_current_user)):
    """
    Lista todos los módulos del sistema desde EDARSAHUB SQL.
    """
    require_admin(current_user)

    return execute_query("""
    SELECT
        CAST(ModuloID AS NVARCHAR(100)) AS id,
        ModuloID,
        CodigoModulo AS codigo,
        NombreModulo AS name,
        NombreModulo AS nombre,
        Descripcion AS descripcion,
        Ruta AS ruta,
        Icono AS icono,
        OrdenMenu AS orden,
        ISNULL(EsVisibleMenu, 1) AS visible,
        ISNULL(Activo, 1) AS activo
    FROM Usuario_Modulos
    WHERE ISNULL(Activo, 1) = 1
    ORDER BY OrdenMenu, NombreModulo
    """)


@router.get("/servers")
async def get_servers(current_user: dict = Depends(get_current_user)):
    """
    Lista todos los servidores configurados desde EDARSAHUB SQL.
    """
    require_admin(current_user)

    return execute_query("""
    SELECT
        CAST(id AS NVARCHAR(100)) AS id,
        nombre AS name,
        nombre,
        system_type,
        tipo_conexion,
        host,
        port,
        database_name,
        EmpresaID,
        ISNULL(activo, 1) AS activo
    FROM Servidores_Conexiones
    WHERE ISNULL(activo, 1) = 1
    ORDER BY nombre
    """)


@router.get("/usuarios-asignables")
async def get_usuarios_asignables(current_user: dict = Depends(get_current_user)):
    """
    Lista usuarios que pueden ser asignados a responsabilidades.
    """
    require_admin(current_user)

    return execute_query("""
    SELECT
        CAST(UsuarioID AS NVARCHAR(100)) AS id,
        Email AS email,
        NombreCompleto AS name,
        NombreCompleto AS nombre,
        Puesto AS puesto,
        ISNULL(Activo, 1) AS activo
    FROM Usuario_Catalogo
    WHERE ISNULL(Activo, 1) = 1
    ORDER BY NombreCompleto, Email
    """)


@router.get("/catalogos-disponibles")
async def get_catalogos_disponibles(current_user: dict = Depends(get_current_user)):
    """
    Lista catálogos/módulos disponibles para configuración de permisos.
    """
    require_admin(current_user)

    return execute_query("""
    SELECT
        CAST(ModuloID AS NVARCHAR(100)) AS id,
        CodigoModulo AS codigo,
        NombreModulo AS name,
        NombreModulo AS nombre,
        Descripcion AS descripcion
    FROM Usuario_Modulos
    WHERE ISNULL(Activo, 1) = 1
    ORDER BY NombreModulo
    """)


@router.post("/permisos-catalogos")
async def save_permisos_catalogos(payload: dict, current_user: dict = Depends(get_current_user)):
    """
    Guarda configuración de permisos de catálogos.
    
    NOTA: Fase inicial - solo recibe y confirma el payload.
    La persistencia granular requiere tablas adicionales.
    """
    require_admin(current_user)

    logging.info(f"[ADMIN_SQL] Permisos recibidos de {current_user.get('email')}: {payload}")

    return {
        "success": True,
        "source": "EDARSAHUB_SQL",
        "message": "Permisos recibidos correctamente",
        "payload": payload
    }
