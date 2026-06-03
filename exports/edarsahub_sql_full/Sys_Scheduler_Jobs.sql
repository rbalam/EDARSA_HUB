-- Sys_Scheduler_Jobs - 6 registros
INSERT INTO [Sys_Scheduler_Jobs] ([JobID], [JobName], [CronExpression], [JobType], [Status], [LastRunDate]) VALUES (N'backup-db', N'Respaldo Completo EDARSAHUB', N'0 2 * * 0', N'Sys', N'activo', NULL);
INSERT INTO [Sys_Scheduler_Jobs] ([JobID], [JobName], [CronExpression], [JobType], [Status], [LastRunDate]) VALUES (N'recalc-kpis', N'Recálculo de KPIs Globales', N'*/30 * * * *', N'App', N'activo', NULL);
INSERT INTO [Sys_Scheduler_Jobs] ([JobID], [JobName], [CronExpression], [JobType], [Status], [LastRunDate]) VALUES (N'sync-inteligencia', N'Actualizar Vista Inteligencia', N'0 */6 * * *', N'DB', N'activo', NULL);
INSERT INTO [Sys_Scheduler_Jobs] ([JobID], [JobName], [CronExpression], [JobType], [Status], [LastRunDate]) VALUES (N'SYNC-INTELIGENCIA-01', N'inteligencia_comercial_sync', N'0 * * * *', N'DATA_SYNC', N'ACTIVE', N'2026-06-02T17:00:03.010000');
INSERT INTO [Sys_Scheduler_Jobs] ([JobID], [JobName], [CronExpression], [JobType], [Status], [LastRunDate]) VALUES (N'sync-sales', N'Sincronización de Ventas SQL', N'0 * * * *', N'DB', N'activo', N'2026-06-01T16:21:19.863000');
INSERT INTO [Sys_Scheduler_Jobs] ([JobID], [JobName], [CronExpression], [JobType], [Status], [LastRunDate]) VALUES (N'sync-vtiger', N'Importación Vtiger CRM', N'0 0 * * *', N'API', N'activo', NULL);
