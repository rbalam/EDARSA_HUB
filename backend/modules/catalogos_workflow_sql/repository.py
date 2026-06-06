from core.sql_first.db import get_sql_connection

class CatalogosWorkflowSQLRepository:
    # =========================================================
    # CONFIG / CATALOGOS
    # =========================================================
    def get_catalogos_disponibles(self):
        sql = """
        SELECT
            CatalogoConfigID,
            CodigoCatalogo,
            NombreCatalogo,
            Descripcion,
            TipoConfiguracion,
            EmpresaID,
            UnidadNegocioID,
            SucursalID,
            ConfigJSON,
            Activo,
            CreatedAt,
            CreatedBy,
            UpdatedAt,
            UpdatedBy
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

    # =========================================================
    # PERMISOS
    # =========================================================
    def get_permisos_catalogo_usuario(self, user_id):
        sql = """
        SELECT
            p.CatalogoPermisoID,
            p.CodigoCatalogo,
            p.UsuarioID,
            p.RolID,
            p.PuedeVer,
            p.PuedeCrear,
            p.PuedeEditar,
            p.PuedeEliminar,
            p.PuedeAprobar,
            p.EmpresaID,
            p.UnidadNegocioID,
            p.SucursalID,
            p.Activo,
            p.CreatedAt,
            p.CreatedBy,
            p.UpdatedAt,
            p.UpdatedBy
        FROM Sistema_CatalogosPermisos p
        WHERE p.UsuarioID = %s AND p.Activo = 1
        ORDER BY p.CodigoCatalogo
        """
        with get_sql_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (user_id,))
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]

    def get_mis_permisos_catalogos(self, current_user_id):
        return self.get_permisos_catalogo_usuario(current_user_id)

    def upsert_permisos_catalogo(self, body, current_user):
        sql_check = """
        SELECT TOP 1 CatalogoPermisoID
        FROM Sistema_CatalogosPermisos
        WHERE CodigoCatalogo = %s
          AND ISNULL(UsuarioID, -1) = ISNULL(%s, -1)
          AND ISNULL(RolID, -1) = ISNULL(%s, -1)
          AND ISNULL(EmpresaID, -1) = ISNULL(%s, -1)
          AND ISNULL(SucursalID, -1) = ISNULL(%s, -1)
          AND Activo = 1
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

    def listar_usuarios_asignables(self):
        sql = """
        SELECT
            u.UsuarioID,
            u.NombreCompleto,
            u.Email,
            r.NombreRol
        FROM Usuario_Catalogo u
        LEFT JOIN Usuario_RolesAsignacion ura
            ON u.UsuarioID = ura.UsuarioID AND ura.Activo = 1
        LEFT JOIN Usuario_Roles r
            ON ura.RolID = r.RolID
        WHERE u.Activo = 1
        ORDER BY u.NombreCompleto
        """
        with get_sql_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]

    # =========================================================
    # SOLICITUDES
    # =========================================================
    def crear_solicitud_catalogo(self, body, current_user):
        with get_sql_connection() as conn:
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO Sistema_CatalogosSolicitudes (
                    CodigoSolicitud, CodigoCatalogo, TipoSolicitud, EstadoSolicitud, Prioridad,
                    EmpresaID, UnidadNegocioID, SucursalID, RegistroObjetivoID,
                    DatosSolicitudJSON, Comentarios, SolicitadoPorUsuarioID, FechaSolicitud,
                    NivelAprobacionActual, TotalNivelesAprobacion,
                    CreatedAt, CreatedBy
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, GETDATE(), %s, %s, GETDATE(), %s)
            """, (
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
                body.get("nivel_aprobacion_actual"),
                body.get("total_niveles_aprobacion"),
                current_user.get("email") or str(current_user.get("id"))
            ))

            cur.execute("SELECT @@IDENTITY")
            solicitud_id = int(cur.fetchone()[0])

            cur.execute("""
                INSERT INTO Sistema_CatalogosSolicitudesHistorial (
                    CatalogoSolicitudID, EstadoAnterior, EstadoNuevo, EventoTipo, Observaciones, UsuarioID, CreatedBy
                )
                VALUES (%s, NULL, %s, 'CREACION', %s, %s, %s)
            """, (
                solicitud_id,
                body.get("estado_solicitud", "PENDIENTE"),
                body.get("comentarios"),
                current_user.get("id"),
                current_user.get("email") or str(current_user.get("id"))
            ))

            if body.get("asignado_a_usuario_id"):
                cur.execute("""
                    INSERT INTO Sistema_Tareas (
                        CodigoTarea, TipoTarea, EstadoTarea, Prioridad, TituloTarea, Descripcion,
                        Modulo, EntidadTipo, EntidadID, CatalogoSolicitudID,
                        EmpresaID, UnidadNegocioID, SucursalID,
                        AsignadoAUsuarioID, CreadoPorUsuarioID, FechaLimite, MetadataJSON,
                        CreatedAt, CreatedBy
                    )
                    VALUES (%s, 'SOLICITUD_CATALOGO', 'PENDIENTE', %s, %s, %s, 'CATALOGOS_WORKFLOW',
                            'SOLICITUD_CATALOGO', %s, %s, %s, %s, %s, %s, %s, %s, GETDATE(), %s)
                """, (
                    body.get("codigo_tarea"),
                    body.get("prioridad"),
                    body.get("titulo_tarea") or f"Solicitud {body.get('codigo_catalogo')}",
                    body.get("descripcion_tarea") or body.get("comentarios"),
                    str(solicitud_id),
                    solicitud_id,
                    body.get("empresa_id"),
                    body.get("unidad_negocio_id"),
                    body.get("sucursal_id"),
                    body.get("asignado_a_usuario_id"),
                    current_user.get("id"),
                    body.get("fecha_limite"),
                    body.get("metadata_tarea_json"),
                    current_user.get("email") or str(current_user.get("id"))
                ))

            conn.commit()
            return solicitud_id

    def listar_solicitudes_catalogo(self):
        sql = """
        SELECT *
        FROM Sistema_CatalogosSolicitudes
        ORDER BY CreatedAt DESC
        """
        with get_sql_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]

    def get_solicitud_catalogo(self, solicitud_id):
        sql = """
        SELECT TOP 1 *
        FROM Sistema_CatalogosSolicitudes
        WHERE CatalogoSolicitudID = %s
        """
        with get_sql_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (solicitud_id,))
            row = cur.fetchone()
            if not row:
                return None
            cols = [c[0] for c in cur.description]
            return dict(zip(cols, row))

    def get_historial_solicitud_catalogo(self, solicitud_id):
        sql = """
        SELECT *
        FROM Sistema_CatalogosSolicitudesHistorial
        WHERE CatalogoSolicitudID = %s
        ORDER BY FechaEvento DESC
        """
        with get_sql_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (solicitud_id,))
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]

    def aprobar_solicitud(self, solicitud_id, body, current_user):
        with get_sql_connection() as conn:
            cur = conn.cursor()

            cur.execute("""
                SELECT EstadoSolicitud, NivelAprobacionActual, TotalNivelesAprobacion
                FROM Sistema_CatalogosSolicitudes
                WHERE CatalogoSolicitudID = %s
            """, (solicitud_id,))
            row = cur.fetchone()
            if not row:
                return 0

            estado_anterior, nivel_actual, total_niveles = row
            nivel_actual = nivel_actual or 0
            total_niveles = total_niveles or 1

            nuevo_nivel = nivel_actual + 1
            estado_nuevo = 'APROBADO' if nuevo_nivel >= total_niveles else 'EN_REVISION'

            cur.execute("""
                UPDATE Sistema_CatalogosSolicitudes
                SET EstadoSolicitud = %s,
                    NivelAprobacionActual = %s,
                    AprobadoPorUsuarioID = %s,
                    AprobacionMetadataJSON = %s,
                    FechaResolucion = CASE WHEN %s = 'APROBADO' THEN GETDATE() ELSE FechaResolucion END,
                    UpdatedAt = GETDATE(),
                    UpdatedBy = %s
                WHERE CatalogoSolicitudID = %s
            """, (
                estado_nuevo,
                nuevo_nivel,
                current_user.get("id"),
                body.get("metadata_json"),
                estado_nuevo,
                current_user.get("email") or str(current_user.get("id")),
                solicitud_id
            ))

            cur.execute("""
                INSERT INTO Sistema_CatalogosSolicitudesHistorial (
                    CatalogoSolicitudID, EstadoAnterior, EstadoNuevo, EventoTipo, Observaciones, UsuarioID, CreatedBy
                )
                VALUES (%s, %s, %s, 'APROBACION', %s, %s, %s)
            """, (
                solicitud_id,
                estado_anterior,
                estado_nuevo,
                body.get("comentarios"),
                current_user.get("id"),
                current_user.get("email") or str(current_user.get("id"))
            ))

            if estado_nuevo == 'APROBADO':
                cur.execute("""
                    UPDATE Sistema_Tareas
                    SET EstadoTarea = 'CERRADA',
                        FechaCierre = GETDATE(),
                        UpdatedAt = GETDATE(),
                        UpdatedBy = %s
                    WHERE CatalogoSolicitudID = %s
                      AND EstadoTarea IN ('PENDIENTE','EN_PROCESO')
                """, (current_user.get("email") or str(current_user.get("id")), solicitud_id))

            conn.commit()
            return 1

    def rechazar_solicitud(self, solicitud_id, body, current_user):
        with get_sql_connection() as conn:
            cur = conn.cursor()

            cur.execute("SELECT EstadoSolicitud FROM Sistema_CatalogosSolicitudes WHERE CatalogoSolicitudID = %s", (solicitud_id,))
            row = cur.fetchone()
            if not row:
                return 0

            estado_anterior = row[0]

            cur.execute("""
                UPDATE Sistema_CatalogosSolicitudes
                SET EstadoSolicitud = 'RECHAZADA',
                    MotivoRechazo = %s,
                    RevisadoPorUsuarioID = %s,
                    FechaResolucion = GETDATE(),
                    UpdatedAt = GETDATE(),
                    UpdatedBy = %s
                WHERE CatalogoSolicitudID = %s
            """, (
                body.get("motivo_rechazo") or body.get("comentarios"),
                current_user.get("id"),
                current_user.get("email") or str(current_user.get("id")),
                solicitud_id
            ))

            cur.execute("""
                INSERT INTO Sistema_CatalogosSolicitudesHistorial (
                    CatalogoSolicitudID, EstadoAnterior, EstadoNuevo, EventoTipo, Observaciones, UsuarioID, CreatedBy
                )
                VALUES (%s, %s, 'RECHAZADA', 'RECHAZO', %s, %s, %s)
            """, (
                solicitud_id,
                estado_anterior,
                body.get("motivo_rechazo") or body.get("comentarios"),
                current_user.get("id"),
                current_user.get("email") or str(current_user.get("id"))
            ))

            cur.execute("""
                UPDATE Sistema_Tareas
                SET EstadoTarea = 'CERRADA',
                    FechaCierre = GETDATE(),
                    UpdatedAt = GETDATE(),
                    UpdatedBy = %s
                WHERE CatalogoSolicitudID = %s
                  AND EstadoTarea IN ('PENDIENTE','EN_PROCESO')
            """, (current_user.get("email") or str(current_user.get("id")), solicitud_id))

            conn.commit()
            return 1

    def corregir_solicitud(self, solicitud_id, body, current_user):
        with get_sql_connection() as conn:
            cur = conn.cursor()

            cur.execute("SELECT EstadoSolicitud FROM Sistema_CatalogosSolicitudes WHERE CatalogoSolicitudID = %s", (solicitud_id,))
            row = cur.fetchone()
            if not row:
                return 0

            estado_anterior = row[0]

            cur.execute("""
                UPDATE Sistema_CatalogosSolicitudes
                SET EstadoSolicitud = 'CORREGIDA',
                    MotivoCorreccion = %s,
                    CorregidoPorUsuarioID = %s,
                    DatosSolicitudJSON = %s,
                    Comentarios = %s,
                    UpdatedAt = GETDATE(),
                    UpdatedBy = %s
                WHERE CatalogoSolicitudID = %s
            """, (
                body.get("motivo_correccion"),
                current_user.get("id"),
                body.get("datos_solicitud_json"),
                body.get("comentarios"),
                current_user.get("email") or str(current_user.get("id")),
                solicitud_id
            ))

            cur.execute("""
                INSERT INTO Sistema_CatalogosSolicitudesHistorial (
                    CatalogoSolicitudID, EstadoAnterior, EstadoNuevo, EventoTipo, Observaciones, UsuarioID, CreatedBy
                )
                VALUES (%s, %s, 'CORREGIDA', 'CORRECCION', %s, %s, %s)
            """, (
                solicitud_id,
                estado_anterior,
                body.get("motivo_correccion") or body.get("comentarios"),
                current_user.get("id"),
                current_user.get("email") or str(current_user.get("id"))
            ))

            conn.commit()
            return 1

    # =========================================================
    # TAREAS
    # =========================================================
    def crear_tarea(self, body, current_user):
        sql = """
        INSERT INTO Sistema_Tareas (
            CodigoTarea, TipoTarea, EstadoTarea, Prioridad, TituloTarea, Descripcion,
            Modulo, EntidadTipo, EntidadID, CatalogoSolicitudID,
            EmpresaID, UnidadNegocioID, SucursalID,
            AsignadoAUsuarioID, CreadoPorUsuarioID, FechaLimite, MetadataJSON,
            CreatedAt, CreatedBy
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, GETDATE(), %s)
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
                body.get("catalogo_solicitud_id"),
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

    def listar_tareas(self):
        sql = """
        SELECT *
        FROM Sistema_Tareas
        ORDER BY CreatedAt DESC
        """
        with get_sql_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]

    def listar_mis_tareas(self, user_id):
        sql = """
        SELECT *
        FROM Sistema_Tareas
        WHERE AsignadoAUsuarioID = %s
          AND EstadoTarea IN ('PENDIENTE','EN_PROCESO')
        ORDER BY CreatedAt DESC
        """
        with get_sql_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (user_id,))
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
