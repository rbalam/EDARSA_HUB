import logging
from fastapi import HTTPException
from typing import Dict, Any, List, Optional
from core.sql_first.connection_factory import get_edarsahub_pymssql_connection

logger = logging.getLogger(__name__)


class MenuService:
    def _get_connection(self):
        return get_edarsahub_pymssql_connection()

    @staticmethod
    def _norm(value):
        return str(value or "").strip().upper().replace("-", "_").replace(" ", "_")

    def resolver_usuario_id_canonico(self, current_user: Dict[str, Any]) -> str:
        """
        Resuelve el UsuarioID canónico desde dbo.Usuario_Catalogo.
        No usa MongoDB, no usa hardcodes de correos ni roles.
        """
        candidatos = [
            current_user.get("UsuarioID"),
            current_user.get("usuario_id"),
            current_user.get("user_id"),
            current_user.get("id"),
            current_user.get("sub"),
            current_user.get("email"),
            current_user.get("correo"),
            current_user.get("preferred_username"),
            current_user.get("username"),
        ]

        candidatos = [str(x).strip() for x in candidatos if x and str(x).strip()]

        if not candidatos:
            raise HTTPException(status_code=401, detail="Token sin identidad de usuario")

        conn = self._get_connection()
        try:
            cur = conn.cursor(as_dict=True)

            cur.execute("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA='dbo'
                  AND TABLE_NAME='Usuario_Catalogo'
            """)
            cols = {str(r["COLUMN_NAME"]) for r in (cur.fetchall() or [])}

            columnas_preferidas = [
                "UsuarioID",
                "UserID",
                "Id",
                "ID",
                "Email",
                "Correo",
                "CorreoElectronico",
                "Usuario",
                "UserName",
                "Username",
                "Login",
                "AuthUserID",
                "Auth0ID",
                "ExternalID",
                "ExternalUserID",
                "MongoUserID",
                "CodigoUsuario",
            ]

            columnas = [c for c in columnas_preferidas if c in cols]

            if not columnas:
                raise HTTPException(
                    status_code=500,
                    detail="Usuario_Catalogo no tiene columnas candidatas para resolver identidad",
                )

            condiciones = []
            params = []

            for col in columnas:
                for valor in candidatos:
                    condiciones.append(f"LOWER(CONVERT(NVARCHAR(255), [{col}])) = LOWER(%s)")
                    params.append(valor)

            sql = f"""
                SELECT TOP 1 UsuarioID
                FROM dbo.Usuario_Catalogo
                WHERE {" OR ".join(condiciones)}
                ORDER BY UsuarioID
            """

            cur.execute(sql, tuple(params))
            row = cur.fetchone()

            if not row:
                logger.warning(
                    "No se pudo resolver UsuarioID canonico para token. Keys=%s",
                    sorted(current_user.keys()),
                )
                raise HTTPException(status_code=403, detail="Usuario no encontrado en SQL canónico")

            return str(row["UsuarioID"])
        finally:
            conn.close()

    def obtener_roles_usuario(self, usuario_id: str) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cur = conn.cursor(as_dict=True)
            cur.execute("""
                SELECT r.RolID, r.CodigoRol, r.NombreRol, r.NivelJerarquia
                FROM dbo.Usuario_RolesAsignacion ura
                INNER JOIN dbo.Usuario_Roles r ON r.RolID = ura.RolID
                WHERE TRY_CONVERT(NVARCHAR(100), ura.UsuarioID) = %s
                  AND ISNULL(ura.Activo,1)=1
                  AND ISNULL(r.Activo,1)=1
            """, (str(usuario_id),))
            return cur.fetchall() or []
        finally:
            conn.close()

    def es_superadmin(self, usuario_id: str) -> bool:
        for r in self.obtener_roles_usuario(usuario_id):
            code = self._norm(r.get("CodigoRol") or r.get("NombreRol"))
            nivel = int(r.get("NivelJerarquia") or 0)
            if code in {"SUPERADMIN", "SUPERADMINISTRADOR", "SUPER_ADMIN"} or nivel >= 100:
                return True
        return False

    def obtener_permisos_usuario(self, usuario_id: str) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cur = conn.cursor(as_dict=True)

            if self.es_superadmin(usuario_id):
                cur.execute("""
                    SELECT DISTINCT
                        m.ModuloID,
                        m.CodigoModulo,
                        m.NombreModulo,
                        a.AccionID,
                        a.CodigoAccion,
                        a.NombreAccion,
                        CAST(1 AS BIT) AS Permitido
                    FROM dbo.Usuario_Modulos m
                    CROSS JOIN dbo.Usuario_Acciones a
                    WHERE ISNULL(m.Activo,1)=1
                      AND ISNULL(a.Activo,1)=1
                """)
                return cur.fetchall() or []

            cur.execute("""
                SELECT DISTINCT
                    m.ModuloID,
                    m.CodigoModulo,
                    m.NombreModulo,
                    a.AccionID,
                    a.CodigoAccion,
                    a.NombreAccion,
                    prm.Permitido
                FROM dbo.Usuario_RolesAsignacion ura
                INNER JOIN dbo.Usuario_PermisosRolModulo prm ON prm.RolID = ura.RolID
                INNER JOIN dbo.Usuario_Modulos m ON m.ModuloID = prm.ModuloID
                INNER JOIN dbo.Usuario_Acciones a ON a.AccionID = prm.AccionID
                WHERE TRY_CONVERT(NVARCHAR(100), ura.UsuarioID) = %s
                  AND ISNULL(ura.Activo,1)=1
                  AND ISNULL(prm.Activo,1)=1
                  AND ISNULL(prm.Permitido,1)=1
                  AND ISNULL(m.Activo,1)=1
                  AND ISNULL(a.Activo,1)=1
            """, (str(usuario_id),))
            return cur.fetchall() or []
        finally:
            conn.close()

    def obtener_permisos_usuario_por_unidad(self, usuario_id: str, unidad_negocio_id: str) -> List[Dict[str, Any]]:
        """
        Permisos efectivos del usuario EN UNA UNIDAD DE NEGOCIO específica,
        resueltos desde el contexto canónico (Usuario_RolesContexto).
        Sin hardcodes: los roles aplicables salen del contexto activo.
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor(as_dict=True)
            cur.execute("""
                SELECT DISTINCT
                    m.ModuloID,
                    m.CodigoModulo,
                    m.NombreModulo,
                    a.AccionID,
                    a.CodigoAccion,
                    a.NombreAccion,
                    prm.Permitido
                FROM dbo.Usuario_RolesContexto urc
                INNER JOIN dbo.Usuario_PermisosRolModulo prm ON prm.RolID = urc.RolID
                INNER JOIN dbo.Usuario_Modulos m ON m.ModuloID = prm.ModuloID
                INNER JOIN dbo.Usuario_Acciones a ON a.AccionID = prm.AccionID
                WHERE TRY_CONVERT(NVARCHAR(100), urc.UsuarioID) = %s
                  AND ISNULL(urc.Activo,1)=1
                  AND CONVERT(NVARCHAR(100), urc.UnidadNegocioID) = %s
                  AND ISNULL(prm.Activo,1)=1
                  AND ISNULL(prm.Permitido,1)=1
                  AND ISNULL(m.Activo,1)=1
                  AND ISNULL(a.Activo,1)=1
            """, (str(usuario_id), str(unidad_negocio_id)))
            return cur.fetchall() or []
        finally:
            conn.close()

    def obtener_menus_usuario(self, usuario_id: str, unidad_negocio_id: Optional[str] = None) -> List[Dict[str, Any]]:
        superadmin = self.es_superadmin(usuario_id)

        # Menú por CONTEXTO ACTIVO: si llega unidad y NO es superadmin, los módulos
        # visibles se filtran por los roles del usuario en esa unidad de negocio.
        if unidad_negocio_id and not superadmin:
            permisos = self.obtener_permisos_usuario_por_unidad(usuario_id, unidad_negocio_id)
        else:
            permisos = self.obtener_permisos_usuario(usuario_id)

        permisos_modulo = set()
        for p in permisos:
            cod = p.get("CodigoModulo")
            if cod:
                permisos_modulo.add(self._norm(cod))

        conn = self._get_connection()
        try:
            cur = conn.cursor(as_dict=True)

            cur.execute("""
                SELECT
                    ModuloID,
                    Codigo,
                    Nombre,
                    Descripcion,
                    Icono,
                    Orden,
                    EsPrincipal,
                    EsSatelite,
                    EsPortal,
                    URLExterna,
                    Activo
                FROM dbo.Sistema_Modulos
                WHERE ISNULL(Activo,1)=1
                ORDER BY Orden, Nombre
            """)
            modulos = cur.fetchall() or []

            resultado = []

            for modulo in modulos:
                modulo_codigo = self._norm(modulo.get("Codigo"))

                # Si no es superadmin, solo mostrar módulos autorizados por SQL.
                if not superadmin and modulo_codigo not in permisos_modulo:
                    continue

                cur.execute("""
                    SELECT
                        MenuID,
                        ModuloID,
                        MenuPadreID,
                        Codigo,
                        Nombre,
                        Descripcion,
                        Icono,
                        Ruta,
                        Orden,
                        RequierePermiso,
                        Activo
                    FROM dbo.Sistema_ModulosMenus
                    WHERE ModuloID = %s
                      AND ISNULL(Activo,1)=1
                    ORDER BY Orden, Nombre
                """, (modulo["ModuloID"],))
                menus = cur.fetchall() or []

                resultado.append({
                    "id": modulo["ModuloID"],
                    "codigo": modulo.get("Codigo"),
                    "nombre": modulo.get("Nombre"),
                    "descripcion": modulo.get("Descripcion"),
                    "icono": modulo.get("Icono"),
                    "ruta": modulo.get("URLExterna"),
                    "orden": modulo.get("Orden"),
                    "es_principal": modulo.get("EsPrincipal"),
                    "es_satelite": modulo.get("EsSatelite"),
                    "es_portal": modulo.get("EsPortal"),
                    "url_externa": modulo.get("URLExterna"),
                    "visible": True,
                    "menus": [
                        {
                            "id": m.get("MenuID"),
                            "codigo": m.get("Codigo"),
                            "nombre": m.get("Nombre"),
                            "descripcion": m.get("Descripcion"),
                            "icono": m.get("Icono"),
                            "ruta": m.get("Ruta"),
                            "orden": m.get("Orden"),
                            "padre_id": m.get("MenuPadreID"),
                            "requiere_permiso": m.get("RequierePermiso"),
                            "visible": True,
                        }
                        for m in menus
                    ],
                })

            return resultado
        finally:
            conn.close()


_menu_service = None

def get_menu_service() -> MenuService:
    global _menu_service
    if _menu_service is None:
        _menu_service = MenuService()
    return _menu_service
