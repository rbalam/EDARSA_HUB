SET NOCOUNT ON;
SET XACT_ABORT ON;
BEGIN TRY
 BEGIN TRANSACTION;
 IF OBJECT_ID('dbo.Operativo_Notificaciones_Queue','U') IS NULL
 BEGIN
  CREATE TABLE dbo.Operativo_Notificaciones_Queue (
   ID uniqueidentifier NOT NULL CONSTRAINT PK_Operativo_Notificaciones_Queue PRIMARY KEY,
   Canal varchar(50) NOT NULL, Modulo varchar(100) NOT NULL, EventoNegocio varchar(100) NOT NULL,
   ReferenciaID varchar(100) NULL, WorkflowID varchar(100) NULL, TareaID varchar(100) NULL,
   Prioridad int NOT NULL CONSTRAINT DF_Operativo_Notificaciones_Queue_Prioridad DEFAULT(3),
   DestinatariosJSON nvarchar(max) NOT NULL, TemplateCodigo varchar(200) NOT NULL, PayloadJSON nvarchar(max) NOT NULL,
   PayloadRenderizado nvarchar(max) NULL, Estado varchar(50) NOT NULL CONSTRAINT DF_Operativo_Notificaciones_Queue_Estado DEFAULT('pendiente'),
   Intentos int NOT NULL CONSTRAINT DF_Operativo_Notificaciones_Queue_Intentos DEFAULT(0), ProximoIntentoUTC datetime2(3) NULL,
   LockedAtUTC datetime2(3) NULL, LockedBy varchar(100) NULL, CreatedAtUTC datetime2(3) NOT NULL CONSTRAINT DF_Operativo_Notificaciones_Queue_Created DEFAULT(SYSUTCDATETIME()),
   UpdatedAtUTC datetime2(3) NULL, ErrorMensaje nvarchar(1000) NULL,
   CONSTRAINT CK_Operativo_Notificaciones_Queue_Prioridad CHECK (Prioridad BETWEEN 1 AND 5),
   CONSTRAINT CK_Operativo_Notificaciones_Queue_Intentos CHECK (Intentos >= 0),
   CONSTRAINT CK_Operativo_Notificaciones_Queue_DestinatariosJSON CHECK (ISJSON(DestinatariosJSON)=1),
   CONSTRAINT CK_Operativo_Notificaciones_Queue_PayloadJSON CHECK (ISJSON(PayloadJSON)=1)
  );
  CREATE INDEX IX_Operativo_Notificaciones_Queue_Pendientes ON dbo.Operativo_Notificaciones_Queue(Estado,ProximoIntentoUTC,Prioridad,CreatedAtUTC);
  CREATE INDEX IX_Operativo_Notificaciones_Queue_Lock ON dbo.Operativo_Notificaciones_Queue(LockedAtUTC,LockedBy);
 END;
 DECLARE @Permisos TABLE(codigo nvarchar(300),nombre nvarchar(400),descripcion nvarchar(1000));
 INSERT INTO @Permisos VALUES
 (N'NOTIFICACIONES_VER',N'Ver comunicaciones y notificaciones',N'Permite consultar configuracion, providers, cola y auditoria de Communications.'),
 (N'NOTIFICACIONES_CONFIGURAR',N'Configurar comunicaciones y notificaciones',N'Permite administrar configuraciones, templates y providers de Communications.'),
 (N'NOTIFICACIONES_ENVIAR',N'Enviar comunicaciones y notificaciones',N'Permite ejecutar pruebas y despachos autorizados de Communications.');
 INSERT INTO dbo.Sistema_RBAC_Permisos(permiso_id,codigo,nombre,modulo,descripcion,activo,fecha_alta,fecha_ultima_actualizacion)
 SELECT NEWID(),p.codigo,p.nombre,N'COMMUNICATIONS',p.descripcion,1,SYSDATETIME(),SYSDATETIME() FROM @Permisos p
 WHERE NOT EXISTS(SELECT 1 FROM dbo.Sistema_RBAC_Permisos x WHERE x.codigo=p.codigo);
 UPDATE x SET nombre=p.nombre,modulo=N'COMMUNICATIONS',descripcion=p.descripcion,activo=1,fecha_ultima_actualizacion=SYSDATETIME() FROM dbo.Sistema_RBAC_Permisos x JOIN @Permisos p ON p.codigo=x.codigo;
 INSERT INTO dbo.Sistema_RBAC_RolesPermisos(rol_permiso_id,rol_id,permiso_id,activo,fecha_alta)
 SELECT NEWID(),r.rol_id,p.permiso_id,1,SYSDATETIME() FROM dbo.Sistema_RBAC_Roles r CROSS JOIN dbo.Sistema_RBAC_Permisos p
 WHERE r.codigo=N'SUPERADMIN' AND r.activo=1 AND p.codigo IN (N'NOTIFICACIONES_VER',N'NOTIFICACIONES_CONFIGURAR',N'NOTIFICACIONES_ENVIAR') AND p.activo=1
 AND NOT EXISTS(SELECT 1 FROM dbo.Sistema_RBAC_RolesPermisos rp WHERE rp.rol_id=r.rol_id AND rp.permiso_id=p.permiso_id);
 COMMIT TRANSACTION;
END TRY
BEGIN CATCH IF @@TRANCOUNT>0 ROLLBACK TRANSACTION; THROW; END CATCH;
