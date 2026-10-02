SET NOCOUNT ON;
SET XACT_ABORT ON;
BEGIN TRY
 BEGIN TRANSACTION;

 IF USER_ID(N'HRLectura') IS NULL THROW 51000, 'HRLECTURA_DATABASE_USER_NOT_FOUND', 1;
 IF USER_ID(N'HUB_Escritura') IS NULL THROW 51001, 'HUB_ESCRITURA_DATABASE_USER_NOT_FOUND', 1;
 IF OBJECT_ID(N'dbo.Sistema_RBAC_Permisos', N'U') IS NULL THROW 51002, 'RBAC_PERMISOS_NOT_FOUND', 1;
 IF OBJECT_ID(N'dbo.Sistema_RBAC_Roles', N'U') IS NULL THROW 51003, 'RBAC_ROLES_NOT_FOUND', 1;
 IF OBJECT_ID(N'dbo.Sistema_RBAC_RolesPermisos', N'U') IS NULL THROW 51004, 'RBAC_ROLESPERMISOS_NOT_FOUND', 1;

 GRANT CONNECT TO [HUB_Escritura];
 GRANT CREATE TABLE TO [HUB_Escritura];
 GRANT ALTER ON SCHEMA::[dbo] TO [HUB_Escritura];
 GRANT SELECT, INSERT, UPDATE ON OBJECT::dbo.Sistema_RBAC_Permisos TO [HUB_Escritura];
 GRANT SELECT ON OBJECT::dbo.Sistema_RBAC_Roles TO [HUB_Escritura];
 GRANT SELECT, INSERT ON OBJECT::dbo.Sistema_RBAC_RolesPermisos TO [HUB_Escritura];

 IF IS_ROLEMEMBER(N'db_accessadmin', N'HRLectura') = 1 ALTER ROLE [db_accessadmin] DROP MEMBER [HRLectura];
 IF IS_ROLEMEMBER(N'db_backupoperator', N'HRLectura') = 1 ALTER ROLE [db_backupoperator] DROP MEMBER [HRLectura];
 IF IS_ROLEMEMBER(N'db_datawriter', N'HRLectura') = 1 ALTER ROLE [db_datawriter] DROP MEMBER [HRLectura];
 IF IS_ROLEMEMBER(N'db_ddladmin', N'HRLectura') = 1 ALTER ROLE [db_ddladmin] DROP MEMBER [HRLectura];
 IF IS_ROLEMEMBER(N'db_securityadmin', N'HRLectura') = 1 ALTER ROLE [db_securityadmin] DROP MEMBER [HRLectura];
 IF IS_ROLEMEMBER(N'db_owner', N'HRLectura') = 1 ALTER ROLE [db_owner] DROP MEMBER [HRLectura];
 IF IS_ROLEMEMBER(N'db_datareader', N'HRLectura') <> 1 ALTER ROLE [db_datareader] ADD MEMBER [HRLectura];
 GRANT CONNECT TO [HRLectura];

 IF IS_ROLEMEMBER(N'db_accessadmin', N'HUB_Escritura') = 1 ALTER ROLE [db_accessadmin] DROP MEMBER [HUB_Escritura];
 IF IS_ROLEMEMBER(N'db_datawriter', N'HUB_Escritura') = 1 ALTER ROLE [db_datawriter] DROP MEMBER [HUB_Escritura];
 IF IS_ROLEMEMBER(N'db_ddladmin', N'HUB_Escritura') = 1 ALTER ROLE [db_ddladmin] DROP MEMBER [HUB_Escritura];
 IF IS_ROLEMEMBER(N'db_securityadmin', N'HUB_Escritura') = 1 ALTER ROLE [db_securityadmin] DROP MEMBER [HUB_Escritura];
 IF IS_ROLEMEMBER(N'db_owner', N'HUB_Escritura') = 1 ALTER ROLE [db_owner] DROP MEMBER [HUB_Escritura];

 COMMIT TRANSACTION;
END TRY
BEGIN CATCH
 IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
 THROW;
END CATCH;
