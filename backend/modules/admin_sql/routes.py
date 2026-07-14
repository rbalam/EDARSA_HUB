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

from core.sql_first.connection_factory import get_edarsahub_pymssql_connection
from fastapi import APIRouter, Depends, HTTPException
import re
from typing import Dict, Any, List
from core.security import get_current_user
from core.rbac_helper_sql import es_admin
from core.config.edarsahub_sql import get_edarsahub_connection
from modules.admin_sql import rbac_pilot_service
import logging

router = APIRouter(prefix="/api/admin-sql", tags=["Admin SQL"])


def is_admin(user: Dict[str, Any]) -> bool:
    """True para ADMIN o SUPERADMIN según resolución RBAC canónica."""
    return es_admin(user)


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


def execute_write(sql: str, params: tuple = (), fetch: bool = False) -> List[Dict[str, Any]]:
    """Ejecuta una sentencia de escritura (UPDATE/INSERT/DELETE) con commit.

    Args:
        fetch: True si la sentencia devuelve resultset (p.ej. OUTPUT INSERTED.*).
    """
    cn = get_edarsahub_connection()
    try:
        cur = cn.cursor(as_dict=True)
        cur.execute(sql, params)
        rows = cur.fetchall() if fetch else []
        cn.commit()
        return rows
    except Exception as e:
        logging.error(f"[ADMIN_SQL] Error en escritura: {e}")
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")
    finally:
        cn.close()


@router.get("/users")
async def get_users(
    incluir_inactivos: bool = False,
    current_user: dict = Depends(get_current_user),
):
    """
    Lista todos los usuarios del sistema desde EDARSAHUB SQL.

    Incluye:
    - Datos básicos del usuario
    - Rol principal asignado (deduplicado: 1 fila por usuario)
    - Servidores asignados
    - Sucursales asignadas

    Args:
        incluir_inactivos: si True, también devuelve usuarios con Activo=0
                           (para poder reactivarlos desde la pantalla Usuarios).
    """
    require_admin(current_user)

    # Filtro de estado: por defecto solo activos (comportamiento legacy).
    where_estado = "" if incluir_inactivos else "WHERE ISNULL(u.Activo, 1) = 1"

    # OUTER APPLY TOP 1 → evita filas duplicadas cuando un usuario tiene
    # más de una asignación de rol principal activa.
    users = execute_query(f"""
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
    OUTER APPLY (
        SELECT TOP 1 ura.RolID
        FROM Usuario_RolesAsignacion ura
        WHERE ura.UsuarioID = u.UsuarioID
          AND ISNULL(ura.Activo, 1) = 1
          AND ISNULL(ura.EsPrincipal, 1) = 1
        ORDER BY ura.RolID
    ) ra
    LEFT JOIN Usuario_Roles r
        ON r.RolID = ra.RolID
    {where_estado}
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

    # Mapear sucursales por usuario y servidor.
    # El PUT /users/{id}/permissions espera:
    # allowed_sucursales = { servidor_id: [sucursal_codigo, ...] }
    map_suc = {}
    for s in sucursales:
        uid = str(s.get("UsuarioID", "") or "")
        sid = str(s.get("ServidorID", "") or "")
        codigo = str(s.get("SucursalCodigo", "") or "")
        if uid and sid and codigo:
            map_suc.setdefault(uid, {}).setdefault(sid, [])
            if codigo not in map_suc[uid][sid]:
                map_suc[uid][sid].append(codigo)

    # Enriquecer usuarios con asignaciones
    rbac_map = rbac_pilot_service.get_rbac_map()
    for u in users:
        uid = str(u.get("UsuarioID", ""))
        # Normalizar estado: el frontend lee `active` (booleano). Antes solo
        # existía `activo` → todos se mostraban "Inactivo". Exponemos ambos.
        u["active"] = bool(u.get("activo"))
        u["allowed_servers"] = map_serv.get(uid, [])
        allowed_sucursales = map_suc.get(uid, {})
        u["allowed_sucursales"] = allowed_sucursales
        u["allowed_warehouses"] = {}
        u["sucursales"] = [
            codigo
            for codigos in allowed_sucursales.values()
            for codigo in codigos
        ]
        rbac = rbac_map.get(uid, {})
        u["sec_perfil"] = rbac.get("sec_perfil")
        u["sec_roles"] = rbac.get("sec_roles", [])
        u["sec_permisos"] = rbac.get("sec_permisos", [])

    return users


@router.patch("/users/{user_id}/toggle-activo")
async def toggle_user_activo(user_id: str, current_user: dict = Depends(get_current_user)):
    """
    Activa/Inactiva un usuario (Usuario_Catalogo.Activo).

    - Al INACTIVAR, además se revocan todas sus sesiones activas
      (no podrá seguir usando el sistema; el refresh token deja de servir).
    - No se permite que un admin se inactive a sí mismo.
    """
    require_admin(current_user)

    # Obtener estado y PublicUUID actuales
    rows = execute_query(
        "SELECT CAST(UsuarioID AS NVARCHAR(100)) AS UsuarioID, PublicUUID, "
        "ISNULL(Activo, 1) AS activo, Email FROM Usuario_Catalogo WHERE UsuarioID = %s",
        (user_id,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    u = rows[0]
    actual = bool(u.get("activo"))
    nuevo = 0 if actual else 1

    # Evitar auto-inactivación
    if nuevo == 0:
        me = str(current_user.get("id") or current_user.get("_id") or "")
        if str(u.get("UsuarioID")) == me or str(u.get("PublicUUID")) == me:
            raise HTTPException(status_code=400, detail="No puedes inactivar tu propio usuario")

    # Actualizar estado
    execute_write(
        "UPDATE Usuario_Catalogo SET Activo = %s WHERE UsuarioID = %s",
        (nuevo, user_id),
    )

    sesiones_revocadas = 0
    if nuevo == 0:
        # Revocar sesiones activas (la sesión guarda UsuarioID = PublicUUID;
        # se incluye también el id numérico por compatibilidad con sesiones antiguas).
        public_uuid = str(u.get("PublicUUID") or "")
        try:
            res = execute_write(
                "UPDATE Sesiones SET EstaActiva = 0, FechaRevocacion = GETUTCDATE(), "
                "MotivoRevocacion = 'user_deactivated', FechaModificacion = GETUTCDATE() "
                "OUTPUT INSERTED.SesionID "
                "WHERE EstaActiva = 1 AND UsuarioID IN (%s, %s)",
                (public_uuid, str(user_id)),
                fetch=True,
            )
            sesiones_revocadas = len(res or [])
        except Exception as e:
            logging.warning(f"[ADMIN_SQL] No se pudieron revocar sesiones de {user_id}: {e}")

    return {
        "success": True,
        "id": str(user_id),
        "email": u.get("Email"),
        "activo": bool(nuevo),
        "active": bool(nuevo),
        "sesiones_revocadas": sesiones_revocadas,
    }


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

    # Mapear permisos por rol sin duplicar ModuloID.
    # Un rol puede tener varias acciones por modulo; la UI de roles trabaja a nivel modulo.
    pmap = {}
    for p in permisos:
        rid = p.get("RolID")
        modulo_id = p.get("modulo_id")
        if rid and modulo_id:
            pmap.setdefault(rid, set()).add(str(modulo_id))

    # Enriquecer roles con permisos deduplicados y orden estable
    for r in roles:
        permisos_rol = pmap.get(r.get("RolID"), set())
        r["permisos"] = sorted(permisos_rol, key=lambda x: int(x) if str(x).isdigit() else str(x))

    return roles


@router.get("/roles/modulos")
async def get_modulos(current_user: dict = Depends(get_current_user)):
    """
    Lista todos los módulos del sistema desde EDARSAHUB SQL.
    Devuelve jerarquía RBAC para que la UI trate MODULO como grupo y SUBMODULO como permiso.
    """
    require_admin(current_user)

    return execute_query("""
      SELECT
          CAST(m.ModuloID AS NVARCHAR(100)) AS id,
          m.ModuloID,
          CAST(m.ModuloPadreID AS NVARCHAR(100)) AS modulo_padre_id,
          m.ModuloPadreID,
          p.CodigoModulo AS padre_codigo,
          p.NombreModulo AS padre_nombre,
          m.CodigoModulo AS codigo,
          m.NombreModulo AS name,
          m.NombreModulo AS nombre,
          m.Descripcion AS descripcion,
          m.TipoModulo AS tipo_modulo,
          m.TipoModulo,
          m.Ruta AS ruta,
          m.Icono AS icono,
          m.OrdenMenu AS orden,
          ISNULL(m.EsVisibleMenu, 1) AS visible,
          ISNULL(m.Activo, 1) AS activo,
          CASE
              WHEN EXISTS (
                  SELECT 1
                  FROM dbo.Usuario_Modulos h
                  WHERE h.ModuloPadreID = m.ModuloID
                    AND ISNULL(h.Activo, 1) = 1
              ) THEN 1 ELSE 0
          END AS tiene_hijos,
          CASE
              WHEN EXISTS (
                  SELECT 1
                  FROM dbo.Sistema_Modulos sm
                  INNER JOIN dbo.Sistema_ModulosMenus smm
                      ON smm.ModuloID = sm.ModuloID
                  WHERE ISNULL(sm.Activo, 1) = 1
                    AND ISNULL(smm.Activo, 1) = 1
                    AND LOWER(LTRIM(RTRIM(smm.RequierePermiso))) = LOWER(LTRIM(RTRIM(m.CodigoModulo)))
              ) THEN 1 ELSE 0
          END AS tiene_permiso_menu_propio
      FROM dbo.Usuario_Modulos m
      LEFT JOIN dbo.Usuario_Modulos p
          ON p.ModuloID = m.ModuloPadreID
      WHERE ISNULL(m.Activo, 1) = 1
      ORDER BY
          COALESCE(p.OrdenMenu, m.OrdenMenu),
          CASE WHEN m.ModuloPadreID IS NULL THEN 0 ELSE 1 END,
          m.OrdenMenu,
          m.NombreModulo
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
    Lista usuarios asignables para permisos de catálogos desde EDARSAHUB SQL.
    Usa Sistema_CatalogosPermisos como fuente canónica de permisos por catálogo.
    """
    require_admin(current_user)

    conn = get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)
    cur = conn.cursor(as_dict=True)
    try:
        cur.execute("""
            SELECT
                CAST(u.UsuarioID AS NVARCHAR(100)) AS id,
                u.UsuarioID AS usuario_id,
                ISNULL(NULLIF(LTRIM(RTRIM(u.NombreCompleto)), ''), u.Email) AS name,
                u.Email AS email,
                ISNULL(rol.NombreRol, 'Sin rol') AS role,
                CAST(ISNULL(f.PuedeSolicitar, 0) AS bit) AS puede_solicitar,
                CAST(ISNULL(f.PuedeAutorizar, 0) AS bit) AS puede_autorizar,
                CAST(ISNULL(f.PuedeLiberar, 0) AS bit) AS puede_liberar,
                pc.permisos_catalogos_csv
            FROM dbo.Usuario_Catalogo u
            OUTER APPLY (
                SELECT TOP 1 r.NombreRol
                FROM dbo.Usuario_RolesAsignacion ura
                INNER JOIN dbo.Usuario_Roles r
                    ON r.RolID = ura.RolID
                WHERE ura.UsuarioID = u.UsuarioID
                  AND ISNULL(ura.Activo, 1) = 1
                ORDER BY ISNULL(r.EsRolSistema, 0) DESC, r.NombreRol
            ) rol
            LEFT JOIN dbo.Usuario_PermisosCatalogosFlujo f
                ON f.UsuarioID = u.UsuarioID
               AND ISNULL(f.Activo, 1) = 1
            OUTER APPLY (
                SELECT STUFF((
                    SELECT '|' + p.CodigoCatalogo
                    FROM dbo.Sistema_CatalogosPermisos p
                    WHERE p.UsuarioID = u.UsuarioID
                      AND ISNULL(p.Activo, 1) = 1
                      AND ISNULL(p.PuedeVer, 0) = 1
                    ORDER BY p.CodigoCatalogo
                    FOR XML PATH(''), TYPE
                ).value('.', 'nvarchar(max)'), 1, 1, '') AS permisos_catalogos_csv
            ) pc
            WHERE ISNULL(u.Activo, 1) = 1
            ORDER BY ISNULL(NULLIF(LTRIM(RTRIM(u.NombreCompleto)), ''), u.Email)
        """)

        result = []
        for row in cur.fetchall():
            csv = row.pop("permisos_catalogos_csv", None)
            row["permisos_catalogos"] = [
                item.strip()
                for item in str(csv or "").split("|")
                if item and item.strip()
            ]
            result.append(row)

        return result
    finally:
        conn.close()

@router.get("/catalogos-disponibles")
async def get_catalogos_disponibles(current_user: dict = Depends(get_current_user)):
    """
    Lista catálogos funcionales desde fuentes canónicas SQL.
    No usa Usuario_Modulos porque esa tabla pertenece a RBAC/menú.
    """
    require_admin(current_user)

    return execute_query("""
        WITH CatalogosCanonicos AS (
            SELECT
                LTRIM(RTRIM(CodigoCatalogo)) AS CodigoCatalogo,
                NULLIF(LTRIM(RTRIM(NombreCatalogo)), '') AS NombreCatalogo,
                NULLIF(LTRIM(RTRIM(Descripcion)), '') AS Descripcion,
                TipoConfiguracion,
                ConfigJSON
            FROM dbo.Sistema_CatalogosConfig
            WHERE ISNULL(Activo, 1) = 1
              AND NULLIF(LTRIM(RTRIM(CodigoCatalogo)), '') IS NOT NULL

            UNION ALL

            SELECT DISTINCT
                LTRIM(RTRIM(CodigoCatalogo)) AS CodigoCatalogo,
                LTRIM(RTRIM(CodigoCatalogo)) AS NombreCatalogo,
                NULL AS Descripcion,
                'PERMISOS' AS TipoConfiguracion,
                N'{}' AS ConfigJSON
            FROM dbo.Sistema_CatalogosPermisos
            WHERE ISNULL(Activo, 1) = 1
              AND NULLIF(LTRIM(RTRIM(CodigoCatalogo)), '') IS NOT NULL

            UNION ALL

            SELECT DISTINCT
                LTRIM(RTRIM(CodigoCatalogo)) AS CodigoCatalogo,
                LTRIM(RTRIM(CodigoCatalogo)) AS NombreCatalogo,
                NULL AS Descripcion,
                'SOLICITUDES' AS TipoConfiguracion,
                N'{}' AS ConfigJSON
            FROM dbo.Sistema_CatalogosSolicitudes
            WHERE NULLIF(LTRIM(RTRIM(CodigoCatalogo)), '') IS NOT NULL
        )
        SELECT
            CodigoCatalogo AS id,
            CodigoCatalogo AS codigo,
            COALESCE(MAX(NombreCatalogo), CodigoCatalogo) AS name,
            COALESCE(MAX(NombreCatalogo), CodigoCatalogo) AS nombre,
            MAX(Descripcion) AS descripcion,
            'Catálogos Workflow' AS modulo,
            'CATALOGOS_WORKFLOW' AS tipo_configuracion,
            COALESCE(
                MAX(CASE
                    WHEN ISJSON(ConfigJSON) = 1
                    THEN TRY_CONVERT(INT, JSON_VALUE(ConfigJSON, '$.niveles_aprobacion'))
                    ELSE NULL
                END),
                1
            ) AS niveles_aprobacion
        FROM CatalogosCanonicos
        GROUP BY CodigoCatalogo
        ORDER BY nombre
    """)


@router.post("/permisos-catalogos")
async def save_permisos_catalogos(payload: dict, current_user: dict = Depends(get_current_user)):
    """
    Guarda permisos de catálogos en fuentes canónicas SQL.
    - Usuario_PermisosCatalogosFlujo: flags globales del flujo.
    - Sistema_CatalogosPermisos: permisos por CodigoCatalogo.
    """
    require_admin(current_user)

    raw_user_id = str(payload.get("user_id") or payload.get("usuario_id") or "").strip()
    if not raw_user_id:
        raise HTTPException(status_code=400, detail="user_id requerido")

    catalogos = payload.get("catalogos_permitidos") or []
    if not isinstance(catalogos, list):
        raise HTTPException(status_code=400, detail="catalogos_permitidos debe ser lista")

    puede_solicitar = 1 if payload.get("puede_solicitar") else 0
    puede_autorizar = 1 if payload.get("puede_autorizar") else 0
    puede_liberar = 1 if payload.get("puede_liberar") else 0
    puede_aprobar = 1 if (puede_autorizar or puede_liberar) else 0
    actor = current_user.get("email") or current_user.get("username") or "admin-sql"

    conn = get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)
    cur = conn.cursor(as_dict=True)

    try:
        cur.execute("""
            SELECT TOP 1 UsuarioID
            FROM dbo.Usuario_Catalogo
            WHERE UsuarioID = TRY_CONVERT(INT, %s)
               OR LOWER(CAST(PublicUUID AS NVARCHAR(36))) = LOWER(%s)
               OR LOWER(ISNULL(MongoLegacyID, '')) = LOWER(%s)
        """, (raw_user_id, raw_user_id, raw_user_id))

        usuario = cur.fetchone()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        usuario_id = usuario["UsuarioID"]

        cur.execute("""
            UPDATE dbo.Usuario_PermisosCatalogosFlujo
            SET PuedeSolicitar = %s,
                PuedeAutorizar = %s,
                PuedeLiberar = %s,
                Activo = 1,
                FechaModificacion = SYSUTCDATETIME(),
                ModifiedBy = %s
            WHERE UsuarioID = %s
        """, (puede_solicitar, puede_autorizar, puede_liberar, actor, usuario_id))

        if cur.rowcount == 0:
            cur.execute("""
                INSERT INTO dbo.Usuario_PermisosCatalogosFlujo
                (UsuarioID, PuedeSolicitar, PuedeAutorizar, PuedeLiberar, Activo, CreatedBy)
                VALUES (%s, %s, %s, %s, 1, %s)
            """, (usuario_id, puede_solicitar, puede_autorizar, puede_liberar, actor))

        cur.execute("""
            UPDATE dbo.Sistema_CatalogosPermisos
            SET PuedeVer = 0,
                PuedeCrear = 0,
                PuedeEditar = 0,
                PuedeEliminar = 0,
                PuedeAprobar = 0,
                Activo = 0,
                UpdatedAt = SYSUTCDATETIME(),
                UpdatedBy = %s
            WHERE UsuarioID = %s
              AND RolID IS NULL
              AND EmpresaID IS NULL
              AND UnidadNegocioID IS NULL
              AND SucursalID IS NULL
        """, (actor, usuario_id))

        guardados = []

        for raw in catalogos:
            codigo = str(raw or "").strip().upper()
            if not codigo:
                continue

            cur.execute("""
                WITH CatalogosCanonicos AS (
                    SELECT LTRIM(RTRIM(CodigoCatalogo)) AS CodigoCatalogo
                    FROM dbo.Sistema_CatalogosConfig
                    WHERE ISNULL(Activo, 1) = 1

                    UNION

                    SELECT LTRIM(RTRIM(CodigoCatalogo)) AS CodigoCatalogo
                    FROM dbo.Sistema_CatalogosPermisos

                    UNION

                    SELECT LTRIM(RTRIM(CodigoCatalogo)) AS CodigoCatalogo
                    FROM dbo.Sistema_CatalogosSolicitudes
                )
                SELECT TOP 1 CodigoCatalogo
                FROM CatalogosCanonicos
                WHERE UPPER(LTRIM(RTRIM(CodigoCatalogo))) = %s
            """, (codigo,))

            row = cur.fetchone()
            if not row:
                continue

            codigo_catalogo = row["CodigoCatalogo"]
            guardados.append(codigo_catalogo)

            cur.execute("""
                UPDATE dbo.Sistema_CatalogosPermisos
                SET PuedeVer = 1,
                    PuedeCrear = %s,
                    PuedeEditar = 0,
                    PuedeEliminar = 0,
                    PuedeAprobar = %s,
                    Activo = 1,
                    UpdatedAt = SYSUTCDATETIME(),
                    UpdatedBy = %s
                WHERE CodigoCatalogo = %s
                  AND UsuarioID = %s
                  AND RolID IS NULL
                  AND EmpresaID IS NULL
                  AND UnidadNegocioID IS NULL
                  AND SucursalID IS NULL
            """, (puede_solicitar, puede_aprobar, actor, codigo_catalogo, usuario_id))

            if cur.rowcount == 0:
                cur.execute("""
                    INSERT INTO dbo.Sistema_CatalogosPermisos
                    (
                        CodigoCatalogo,
                        UsuarioID,
                        RolID,
                        PuedeVer,
                        PuedeCrear,
                        PuedeEditar,
                        PuedeEliminar,
                        PuedeAprobar,
                        EmpresaID,
                        UnidadNegocioID,
                        SucursalID,
                        Activo,
                        CreatedAt,
                        CreatedBy
                    )
                    VALUES
                    (
                        %s, %s, NULL,
                        1, %s, 0, 0, %s,
                        NULL, NULL, NULL,
                        1, SYSUTCDATETIME(), %s
                    )
                """, (codigo_catalogo, usuario_id, puede_solicitar, puede_aprobar, actor))

        conn.commit()

        return {
            "success": True,
            "source": "EDARSAHUB_SQL_CANONICAL",
            "message": "Permisos guardados correctamente",
            "usuario_id": usuario_id,
            "catalogos_guardados": guardados,
            "puede_solicitar": bool(puede_solicitar),
            "puede_autorizar": bool(puede_autorizar),
            "puede_liberar": bool(puede_liberar),
        }

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error guardando permisos de catálogos: {e}")
    finally:
        conn.close()

@router.put("/roles/{role_id}")
async def update_role_sql(role_id: str, role_data: dict, current_user: dict = Depends(get_current_user)):
    """
    Actualiza rol y permisos en EDARSAHUB SQL.
    Fuente única: Usuario_Roles + Usuario_PermisosRolModulo.
    """
    require_admin(current_user)

    nombre = role_data.get("nombre")
    descripcion = role_data.get("descripcion")
    permisos = role_data.get("permisos", [])

    conn = get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)
    cur = conn.cursor(as_dict=True)
    try:
        cur.execute("""
            SELECT RolID, EsRolSistema
            FROM dbo.Usuario_Roles
            WHERE RolID = %s AND Activo = 1
        """, (role_id,))
        rol = cur.fetchone()
        if not rol:
            raise HTTPException(status_code=404, detail="Rol no encontrado")

        rol_id_sql = rol["RolID"]

        if descripcion is not None:
            cur.execute("""
                UPDATE dbo.Usuario_Roles
                SET Descripcion = %s, FechaModificacion = GETDATE()
                WHERE RolID = %s
            """, (descripcion, rol_id_sql))

        if nombre and not rol.get("EsRolSistema"):
            cur.execute("""
                UPDATE dbo.Usuario_Roles
                SET NombreRol = %s, CodigoRol = UPPER(REPLACE(%s, ' ', '_')), FechaModificacion = GETDATE()
                WHERE RolID = %s
            """, (nombre, nombre, rol_id_sql))

        if isinstance(permisos, list):
            cur.execute("""
                UPDATE dbo.Usuario_PermisosRolModulo
                SET Activo = 0, Permitido = 0, FechaModificacion = GETDATE(), ModifiedBy = 'admin-sql'
                WHERE RolID = %s
            """, (rol_id_sql,))

            for p in permisos:
                modulo_id = None
                accion_id = None

                if isinstance(p, dict):
                    modulo_id = p.get("modulo_id") or p.get("ModuloID") or p.get("id")
                    accion_id = p.get("accion_id") or p.get("AccionID")
                    accion_codigo = p.get("accion_codigo") or p.get("accion") or "VER"
                else:
                    modulo_id = p
                    accion_codigo = "VER"

                if accion_id is None:
                    cur.execute("""
                        SELECT AccionID
                        FROM dbo.Usuario_Acciones
                        WHERE CodigoAccion = %s AND Activo = 1
                    """, (str(accion_codigo).upper(),))
                    acc = cur.fetchone()
                    if not acc:
                        continue
                    accion_id = acc["AccionID"]

                cur.execute("""
                    SELECT ModuloID
                    FROM dbo.Usuario_Modulos
                    WHERE ModuloID = TRY_CONVERT(INT, %s) AND Activo = 1
                """, (str(modulo_id),))
                mod = cur.fetchone()
                if not mod:
                    continue

                cur.execute("""
                    UPDATE dbo.Usuario_PermisosRolModulo
                    SET Activo = 1, Permitido = 1, FechaModificacion = GETDATE(), ModifiedBy = 'admin-sql'
                    WHERE RolID = %s AND ModuloID = %s AND AccionID = %s
                """, (rol_id_sql, mod["ModuloID"], accion_id))

                if cur.rowcount == 0:
                    cur.execute("""
                        INSERT INTO dbo.Usuario_PermisosRolModulo
                        (RolID, ModuloID, AccionID, Permitido, RestriccionPropietario,
                         RestriccionSucursal, RequiereAutorizacion, Activo, FechaAlta, CreatedBy)
                        VALUES (%s, %s, %s, 1, 0, 0, 0, 1, GETDATE(), 'admin-sql')
                    """, (rol_id_sql, mod["ModuloID"], accion_id))

        conn.commit()
        return {"ok": True, "message": "Rol y permisos actualizados", "rol_id": rol_id_sql}

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error guardando permisos del rol: {e}")
    finally:
        conn.close()


@router.post("/roles")
async def create_role_sql(role_data: dict, current_user: dict = Depends(get_current_user)):
    require_admin(current_user)

    nombre = role_data.get("nombre")
    descripcion = role_data.get("descripcion") or nombre or ""
    if not nombre:
        raise HTTPException(status_code=400, detail="Nombre requerido")

    conn = get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)
    cur = conn.cursor(as_dict=True)
    try:
        codigo = nombre.upper().replace(" ", "_")
        cur.execute("""
            INSERT INTO dbo.Usuario_Roles
            (CodigoRol, NombreRol, Descripcion, EsRolSistema, Activo, FechaAlta, NivelJerarquia)
            VALUES (%s, %s, %s, 0, 1, GETDATE(), 0)
        """, (codigo, nombre, descripcion))

        cur.execute("SELECT SCOPE_IDENTITY() AS RolID")
        rol_id = int(cur.fetchone()["RolID"])
        conn.commit()
        return await update_role_sql(str(rol_id), role_data, current_user)

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error creando rol: {e}")
    finally:
        conn.close()


@router.delete("/roles/{role_id}")
async def delete_role_sql(role_id: str, current_user: dict = Depends(get_current_user)):
    require_admin(current_user)
    execute_query("""
        UPDATE dbo.Usuario_Roles
        SET Activo = 0, FechaModificacion = GETDATE()
        WHERE RolID = %s AND ISNULL(EsRolSistema, 0) = 0
    """, (role_id,))
    return {"ok": True, "message": "Rol desactivado"}

