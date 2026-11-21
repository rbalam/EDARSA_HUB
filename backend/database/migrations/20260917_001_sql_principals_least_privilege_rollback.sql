SET NOCOUNT ON;
SET XACT_ABORT ON;
BEGIN TRY
 BEGIN TRANSACTION;

 IF USER_ID(N'HRLectura') IS NULL THROW 51010, 'HRLECTURA_DATABASE_USER_NOT_FOUND', 1;
 IF USER_ID(N'ChatGPT_Escritura') IS NULL THROW 51011, 'CHATGPT_ESCRITURA_DATABASE_USER_NOT_FOUND', 1;

 ALTER ROLE [db_accessadmin] ADD MEMBER [HRLectura];
 ALTER ROLE [db_backupoperator] ADD MEMBER [HRLectura];
 ALTER ROLE [db_datareader] ADD MEMBER [HRLectura];
 ALTER ROLE [db_datawriter] ADD MEMBER [HRLectura];
 ALTER ROLE [db_ddladmin] ADD MEMBER [HRLectura];
 ALTER ROLE [db_securityadmin] ADD MEMBER [HRLectura];
 ALTER ROLE [db_owner] ADD MEMBER [HRLectura];

 ALTER ROLE [db_accessadmin] ADD MEMBER [ChatGPT_Escritura];
 ALTER ROLE [db_datawriter] ADD MEMBER [ChatGPT_Escritura];
 ALTER ROLE [db_ddladmin] ADD MEMBER [ChatGPT_Escritura];
 ALTER ROLE [db_securityadmin] ADD MEMBER [ChatGPT_Escritura];
 ALTER ROLE [db_owner] ADD MEMBER [ChatGPT_Escritura];

 REVOKE CREATE TABLE FROM [ChatGPT_Escritura];
 REVOKE ALTER ON SCHEMA::[dbo] FROM [ChatGPT_Escritura];
 REVOKE SELECT, INSERT, UPDATE ON OBJECT::dbo.Sistema_RBAC_Permisos FROM [ChatGPT_Escritura];
 REVOKE SELECT ON OBJECT::dbo.Sistema_RBAC_Roles FROM [ChatGPT_Escritura];
 REVOKE SELECT, INSERT ON OBJECT::dbo.Sistema_RBAC_RolesPermisos FROM [ChatGPT_Escritura];

 COMMIT TRANSACTION;
END TRY
BEGIN CATCH
 IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
 THROW;
END CATCH;
