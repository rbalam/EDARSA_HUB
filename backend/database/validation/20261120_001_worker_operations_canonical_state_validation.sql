/*
  EDARSAHUB BOS — GATE-M1: Validacion Read-Only (HRLectura)
*/
SET NOCOUNT ON;

SELECT
    @@SERVERNAME AS server_name,
    DB_NAME() AS db_name,
    SUSER_SNAME() AS login_name,
    USER_NAME() AS db_user;

SELECT
    s.name AS schema_name,
    t.name AS table_name
FROM sys.tables t
INNER JOIN sys.schemas s ON s.schema_id = t.schema_id
WHERE s.name = N'dbo'
  AND t.name IN (
      N'Sys_Worker_Jobs',
      N'Sys_Worker_Incidents',
      N'Sys_Worker_RecoveryEvents',
      N'Sys_Worker_Capabilities'
  )
ORDER BY t.name;

SELECT
    s.name AS schema_name,
    p.name AS procedure_name
FROM sys.procedures p
INNER JOIN sys.schemas s ON s.schema_id = p.schema_id
WHERE s.name = N'dbo'
  AND p.name IN (
      N'sp_Worker_UpsertJobState',
      N'sp_Worker_UpsertIncident',
      N'sp_Worker_RecordRecoveryEvent',
      N'sp_Worker_UpsertCapability'
  )
ORDER BY p.name;

SELECT
    obj.object_name,
    HAS_PERMS_BY_NAME(N'dbo.' + obj.object_name, 'OBJECT', 'EXECUTE') AS can_execute
FROM (
    VALUES
        (N'sp_Worker_UpsertJobState'),
        (N'sp_Worker_UpsertIncident'),
        (N'sp_Worker_RecordRecoveryEvent'),
        (N'sp_Worker_UpsertCapability')
) AS obj(object_name)
ORDER BY obj.object_name;

SELECT
    t.name AS table_name,
    SUM(p.rows) AS row_count
FROM sys.tables t
INNER JOIN sys.schemas s ON s.schema_id = t.schema_id
INNER JOIN sys.partitions p ON p.object_id = t.object_id AND p.index_id IN (0, 1)
WHERE s.name = N'dbo'
  AND t.name IN (
      N'Sys_Worker_Jobs',
      N'Sys_Worker_Incidents',
      N'Sys_Worker_RecoveryEvents',
      N'Sys_Worker_Capabilities'
  )
GROUP BY t.name
ORDER BY t.name;
