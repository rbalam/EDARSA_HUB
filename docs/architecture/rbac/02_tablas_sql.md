# Tablas SQL RBAC

| Tabla | Existe | Filas | Columnas |
| --- | --- | --- | --- |
| dbo.Usuario_Catalogo | Sí | 22 | UsuarioID, CodigoUsuario, Username, Email, PasswordHash, PasswordHashTexto, Nombre, Apellidos, NombreCompleto, Telefono, Celular, Puesto, Departamento, EsUsuarioPortal, RequiereMFA, PasswordTemporal, DebeCambiarPassword, IntentosFallidos, Bloqueado, FechaBloqueo, MotivoBloqueo, UltimoAcceso, UltimoCambioPassword, FechaExpiracionPassword, ZonaHoraria, Idioma, Activo, FechaAlta, FechaModificacion, CreatedBy, ModifiedBy, MongoLegacyID, PublicUUID |
| dbo.Usuario_Roles | Sí | 33 | RolID, CodigoRol, NombreRol, Descripcion, EsRolSistema, Activo, FechaAlta, FechaModificacion, NivelJerarquia |
| dbo.Usuario_Modulos | Sí | 106 | ModuloID, ModuloPadreID, CodigoModulo, NombreModulo, Descripcion, TipoModulo, Ruta, Icono, OrdenMenu, EsVisibleMenu, RequiereAutorizacion, Activo, FechaAlta, FechaModificacion |
| dbo.Usuario_Acciones | Sí | 26 | AccionID, CodigoAccion, NombreAccion, Descripcion, EsAutorizable, Activo |
| dbo.Usuario_PermisosRolModulo | Sí | 989 | PermisoRolModuloID, RolID, ModuloID, AccionID, Permitido, RestriccionPropietario, RestriccionSucursal, RequiereAutorizacion, NivelAutorizacionRequerido, Activo, FechaAlta, FechaModificacion, CreatedBy, ModifiedBy |
| dbo.Usuario_RBAC_Asignacion | Sí | 25 | AsignacionID, UsuarioID, Tipo, Codigo, AsignadoPor, FechaAsignacion |
| dbo.Usuario_RBAC_Bitacora | Sí | 35 | BitacoraID, EventoUUID, FechaEvento, UsuarioAfectadoID, UsuarioAfectadoEmail, Tipo, Accion, Resultado, Descripcion, Detalles, IP, AdministradorID, AdministradorEmail |
| dbo.Usuario_LogRBACVerificacion | Sí | 5232 | LogID, UsuarioID, PublicUUID, Email, PermisoRequerido, Resultado, Endpoint, MetodoHTTP, IPAddress, DetallesJSON, FechaVerificacion |
