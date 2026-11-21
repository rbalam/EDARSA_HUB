-- Validacion solo lectura GATE-M2 R3: sistema.worker_console en dbo.Sistema_ModulosMenus
SET NOCOUNT ON;

IF DB_NAME() <> N'EDARSAHUB'
    THROW 51100, 'UNEXPECTED_DATABASE_FORBIDDEN', 1;

DECLARE @Count INT;
SELECT @Count = COUNT(*)
FROM dbo.Sistema_ModulosMenus mm
INNER JOIN dbo.Sistema_Modulos m ON m.ModuloID = mm.ModuloID
WHERE m.Codigo = N'SISTEMA'
  AND mm.Codigo = N'sistema.worker_console'
  AND mm.Ruta = N'/worker-console'
  AND mm.RequierePermiso = N'RBAC_ADMIN'
  AND ISNULL(mm.Activo, 0) = 1;

IF @Count <> 1
    THROW 51101, 'WORKER_CONSOLE_ENTERPRISE_MENU_VALIDATION_FAILED', 1;

SELECT
    DB_NAME() AS db_name,
    mm.MenuID,
    mm.ModuloID,
    m.Codigo AS modulo_codigo,
    mm.Codigo AS menu_codigo,
    mm.Nombre,
    mm.Icono,
    mm.Ruta,
    mm.Orden,
    mm.RequierePermiso,
    mm.Activo,
    N'VALIDATION_SUCCESS' AS validation_status
FROM dbo.Sistema_ModulosMenus mm
INNER JOIN dbo.Sistema_Modulos m ON m.ModuloID = mm.ModuloID
WHERE mm.Codigo = N'sistema.worker_console';
