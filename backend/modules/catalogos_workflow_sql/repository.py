from core.sql_first.db import get_sql_connection

class CatalogosWorkflowSQLRepository:
    def get_catalogos_disponibles(self):
        sql = """
        SELECT CatalogoConfigID, CodigoCatalogo, NombreCatalogo, Descripcion, TipoConfiguracion, ConfigJSON,
               EmpresaID, UnidadNegocioID, SucursalID, Activo
        FROM Sistema_CatalogosConfig
        WHERE Activo = 1
        ORDER BY CodigoCatalogo, NombreCatalogo
        """
        with get_sql_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]

    def upsert_niveles_catalogo(self, catalogo_id, body, current_user):
        sql_check = """
        SELECT TOP 1 CatalogoConfigID
        FROM Sistema_CatalogosConfig
        WHERE CodigoCatalogo = %s AND TipoConfiguracion = 'NIVELES_APROBACION'
        """
        sql_insert = """
        INSERT INTO Sistema_CatalogosConfig (
            CodigoCatalogo, NombreCatalogo, Descripcion, TipoConfiguracion,
            EmpresaID, UnidadNegocioID, SucursalID, ConfigJSON,
            Activo, CreatedAt, CreatedBy
        )
        VALUES (%s, %s, %s, 'NIVELES_APROBACION', %s, %s, %s, %s, 1, GETDATE(), %s)
        """
        sql_update = """
        UPDATE Sistema_CatalogosConfig
        SET ConfigJSON = %s, UpdatedAt = GETDATE(), UpdatedBy = %s
        WHERE CatalogoConfigID = %s
        """
        with get_sql_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql_check, (catalogo_id,))
            row = cur.fetchone()
            if row:
                cur.execute(sql_update, (
                    body.get("config_json"),
                    current_user.get("email") or str(current_user.get("id")),
                    row[0]
                ))
            else:
                cur.execute(sql_insert, (
                    catalogo_id,
                    body.get("nombre_catalogo") or catalogo_id,
                    body.get("descripcion"),
                    body.get("empresa_id"),
                    body.get("unidad_negocio_id"),
                    body.get("sucursal_id"),
                    body.get("config_json"),
                    current_user.get("email") or str(current_user.get("id"))
                ))
            conn.commit()
            return 1

    def get_permisos_catalogo_usuario(self, user_id):
        sql = """
        SELECT CatalogoPermisoID, CodigoCatalogo, UsuarioID, RolID,
               PuedeVer, PuedeCrear, PuedeEditar, PuedeEliminar, PuedeAprobar,
               EmpresaID, UnidadNegocioID, SucursalID, Activo
        FROM Sistema_CatalogosPermisos
        WHERE UsuarioID = %s AND Activo = 1
        ORDER BY CodigoCatalogo
        """
        with get_sql_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (user_id,))
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]

    def upsert_permisos_catalogo(self, body, current_user):
        sql_check = """
        SELECT TOP 1 CatalogoPermisoID
        FROM Sistema_CatalogosPermisos
        WHERE CodigoCatalogo = %s
          AND ISNULL(UsuarioID, -1) = ISNULL(%s, -1)
          AND ISNULL(RolID, -1) = ISNULL(%s, -1)
          AND ISNULL(EmpresaID, -1) = ISNULL(%s, -1)
          AND ISNULL(SucursalID, -1) = ISNULL(%s, -1)
        """
        sql_insert = """
        INSERT INTO Sistema_CatalogosPermisos (
            CodigoCatalogo, UsuarioID, RolID,
            PuedeVer, PuedeCrear, PuedeEditar, PuedeEliminar, PuedeAprobar,
            EmpresaID, UnidadNegocioID, SucursalID,
            Activo, CreatedAt, CreatedBy
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, GETDATE(), %s)
        """
        sql_update = """
        UPDATE Sistema_CatalogosPermisos
        SET PuedeVer = %s, PuedeCrear = %s, PuedeEditar = %s, PuedeEliminar = %s, PuedeAprobar = %s,
            UpdatedAt = GETDATE(), UpdatedBy = %s
        WHERE CatalogoPermisoID = %s
        """
        with get_sql_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql_check, (
                body.get("codigo_catalogo"),
                body.get("usuario_id"),
                body.get("rol_id"),
                body.get("empresa_id"),
                body.get("sucursal_id"),
            ))
            row = cur.fetchone()
            if row:
                cur.execute(sql_update, (
                    body.get("puede_ver", True),
                    body.get("puede_crear", False),
                    body.get("puede_editar", False),
                    body.get("puede_eliminar", False),
                    body.get("puede_aprobar", False),
                    current_user.get("email") or str(current_user.get("id")),
                    row[0]
                ))
            else:
                cur.execute(sql_insert, (
                    body.get("codigo_catalogo"),
                    body.get("usuario_id"),
                    body.get("rol_id"),
                    body.get("puede_ver", True),
                    body.get("puede_crear", False),
                    body.get("puede_editar", False),
                    body.get("puede_eliminar", False),
                    body.get("puede_aprobar", False),
                    body.get("empresa_id"),
                    body.get("unidad_negocio_id"),
                    body.get("sucursal_id"),
                    current_user.get("email") or str(current_user.get("id"))
                ))
            conn.commit()
            return 1

    def crear_solicitud_catalogo(self, body, current_user):
        sql = """
        INSERT INTO Sistema_CatalogosSolicitudes (
            CodigoSolicitud, CodigoCatalogo, TipoSolicitud, EstadoSolicitud, Prioridad,
            EmpresaID, UnidadNegocioID, SucursalID, RegistroObjetivoID,
            DatosSolicitudJSON, Comentarios, SolicitadoPorUsuarioID, FechaSolicitud,
            CreatedAt, CreatedBy
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, GETDATE(), GETDATE(), %s)
        """
        with get_sql_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (
                body.get("codigo_solicitud"),
                body.get("codigo_catalogo"),
                body.get("tipo_solicitud"),
                body.get("estado_solicitud", "PENDIENTE"),
                body.get("prioridad"),
                body.get("empresa_id"),
                body.get("unidad_negocio_id"),
                body.get("sucursal_id"),
                body.get("registro_objetivo_id"),
                body.get("datos_solicitud_json"),
                body.get("comentarios"),
                current_user.get("id"),
                current_user.get("email") or str(current_user.get("id"))
            ))
            conn.commit()
            return 1

    def listar_solicitudes_catalogo(self, limit=100):
        sql = f"""
        SELECT TOP {limit} CatalogoSolicitudID, CodigoSolicitud, CodigoCatalogo, TipoSolicitud,
               EstadoSolicitud, Prioridad, EmpresaID, UnidadNegocioID, SucursalID,
               RegistroObjetivoID, DatosSolicitudJSON, Comentarios,
               SolicitadoPorUsuarioID, RevisadoPorUsuarioID, AprobadoPorUsuarioID,
               FechaSolicitud, FechaResolucion, CreatedAt
        FROM Sistema_CatalogosSolicitudes
        ORDER BY CreatedAt DESC
        """
        with get_sql_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]

    def actualizar_estado_solicitud(self, solicitud_id, body, current_user):
        with get_sql_connection() as conn:
            cur = conn.cursor()

            cur.execute("SELECT EstadoSolicitud FROM Sistema_CatalogosSolicitudes WHERE CatalogoSolicitudID = %s", (solicitud_id,))
            row = cur.fetchone()
            if not row:
                return 0

            estado_anterior = row[0]
            estado_nuevo = body.get("estado_nuevo")

            cur.execute("""
                UPDATE Sistema_CatalogosSolicitudes
                SET EstadoSolicitud = %s, Comentarios = %s, RevisadoPorUsuarioID = %s, FechaResolucion = GETDATE(),
                    UpdatedAt = GETDATE(), UpdatedBy = %s
                WHERE CatalogoSolicitudID = %s
            """, (
                estado_nuevo,
                body.get("comentarios"),
                current_user.get("id"),
                current_user.get("email") or str(current_user.get("id")),
                solicitud_id
            ))

            cur.execute("""
                INSERT INTO Sistema_CatalogosSolicitudesHistorial (
                    CatalogoSolicitudID, EstadoAnterior, EstadoNuevo, EventoTipo, Observaciones, UsuarioID, CreatedBy
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                solicitud_id,
                estado_anterior,
                estado_nuevo,
                body.get("evento_tipo", "CAMBIO_ESTADO"),
                body.get("comentarios"),
                current_user.get("id"),
                current_user.get("email") or str(current_user.get("id"))
            ))

            conn.commit()
            return 1

    def crear_tarea(self, body, current_user):
        sql = """
        INSERT INTO Sistema_Tareas (
            CodigoTarea, TipoTarea, EstadoTarea, Prioridad, TituloTarea, Descripcion,
            Modulo, EntidadTipo, EntidadID, EmpresaID, UnidadNegocioID, SucursalID,
            AsignadoAUsuarioID, CreadoPorUsuarioID, FechaLimite, MetadataJSON,
            CreatedAt, CreatedBy
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, GETDATE(), %s)
        """
        with get_sql_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (
                body.get("codigo_tarea"),
                body.get("tipo_tarea"),
                body.get("estado_tarea", "PENDIENTE"),
                body.get("prioridad"),
                body.get("titulo_tarea"),
                body.get("descripcion"),
                body.get("modulo"),
                body.get("entidad_tipo"),
                body.get("entidad_id"),
                body.get("empresa_id"),
                body.get("unidad_negocio_id"),
                body.get("sucursal_id"),
                body.get("asignado_a_usuario_id"),
                current_user.get("id"),
                body.get("fecha_limite"),
                body.get("metadata_json"),
                current_user.get("email") or str(current_user.get("id"))
            ))
            conn.commit()
            return 1

    def listar_tareas(self, limit=100):
        sql = f"""
        SELECT TOP {limit} TareaSistemaID, CodigoTarea, TipoTarea, EstadoTarea, Prioridad,
               TituloTarea, Descripcion, Modulo, EntidadTipo, EntidadID,
               EmpresaID, UnidadNegocioID, SucursalID,
               AsignadoAUsuarioID, CreadoPorUsuarioID, FechaLimite, FechaCierre,
               MetadataJSON, CreatedAt
        FROM Sistema_Tareas
        ORDER BY CreatedAt DESC
        """
        with get_sql_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
