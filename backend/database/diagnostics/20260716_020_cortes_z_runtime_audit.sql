SET NOCOUNT ON;

SELECT
    DB_NAME() AS database_name,
    SUSER_SNAME() AS login_name,
    USER_NAME() AS database_user,
    SYSUTCDATETIME() AS audit_utc;
GO

SELECT
    OBJECT_ID(N'dbo.Finanzas_CortesCaja', N'U') AS cortes_table_object_id,
    OBJECT_ID(N'dbo.Finanzas_CortesCaja_SyncLog', N'U') AS cortes_sync_log_object_id,
    OBJECT_ID(N'dbo.Scheduler_BitacoraJobs', N'U') AS scheduler_log_object_id,
    OBJECT_ID(N'dbo.Unidades_Negocio', N'U') AS unidades_object_id,
    OBJECT_ID(N'dbo.Servidores_Conexiones', N'U') AS servidores_object_id;
GO

IF OBJECT_ID(N'dbo.Finanzas_CortesCaja', N'U') IS NOT NULL
BEGIN
    SELECT
        COUNT_BIG(*) AS total_rows,
        SUM(CASE WHEN Activo = 1 THEN 1 ELSE 0 END) AS active_rows,
        MIN(FechaCorte) AS min_fecha_corte,
        MAX(FechaCorte) AS max_fecha_corte,
        MAX(FechaSincronizacion) AS last_sync_at,
        SUM(CASE WHEN FechaCorte >= CONVERT(date, '2026-07-09')
                  AND FechaCorte < CONVERT(date, '2026-07-17')
                  AND Activo = 1 THEN 1 ELSE 0 END) AS rows_20260709_20260716
    FROM dbo.Finanzas_CortesCaja;
END
ELSE
BEGIN
    SELECT CAST('MISSING_TABLE: dbo.Finanzas_CortesCaja' AS nvarchar(200)) AS audit_error;
END;
GO

IF OBJECT_ID(N'dbo.Finanzas_CortesCaja', N'U') IS NOT NULL
BEGIN
    SELECT
        COALESCE(UnidadNegocioNombre, N'<NULL>') AS unidad_nombre,
        CONVERT(nvarchar(100), UnidadNegocioID) AS unidad_negocio_id,
        CONVERT(nvarchar(100), ServerID) AS server_id,
        COALESCE(SistemaOrigen, N'<NULL>') AS sistema_origen,
        COUNT_BIG(*) AS total_rows,
        SUM(CASE WHEN Activo = 1 THEN 1 ELSE 0 END) AS active_rows,
        MIN(FechaCorte) AS min_fecha_corte,
        MAX(FechaCorte) AS max_fecha_corte,
        MAX(FechaSincronizacion) AS last_sync_at
    FROM dbo.Finanzas_CortesCaja
    GROUP BY UnidadNegocioNombre, UnidadNegocioID, ServerID, SistemaOrigen
    ORDER BY unidad_nombre, sistema_origen;
END;
GO

IF OBJECT_ID(N'dbo.Finanzas_CortesCaja', N'U') IS NOT NULL
BEGIN
    SELECT
        COALESCE(UnidadNegocioNombre, N'<NULL>') AS unidad_nombre,
        CONVERT(nvarchar(100), UnidadNegocioID) AS unidad_negocio_id,
        CONVERT(nvarchar(100), ServerID) AS server_id,
        COALESCE(SistemaOrigen, N'<NULL>') AS sistema_origen,
        COUNT_BIG(*) AS rows_in_ui_range,
        MIN(FechaCorte) AS min_fecha_corte,
        MAX(FechaCorte) AS max_fecha_corte,
        MAX(FechaSincronizacion) AS last_sync_at
    FROM dbo.Finanzas_CortesCaja
    WHERE Activo = 1
      AND FechaCorte >= CONVERT(date, '2026-07-09')
      AND FechaCorte < CONVERT(date, '2026-07-17')
    GROUP BY UnidadNegocioNombre, UnidadNegocioID, ServerID, SistemaOrigen
    ORDER BY unidad_nombre, sistema_origen;
END;
GO

IF OBJECT_ID(N'dbo.Finanzas_CortesCaja', N'U') IS NOT NULL
BEGIN
    SELECT TOP (20)
        CorteCajaID,
        FolioCorte,
        FechaCorte,
        CONVERT(nvarchar(100), UnidadNegocioID) AS unidad_negocio_id,
        UnidadNegocioNombre,
        CONVERT(nvarchar(100), ServerID) AS server_id,
        SistemaOrigen,
        TotalEfectivo,
        TotalVenta,
        Activo,
        FechaSincronizacion
    FROM dbo.Finanzas_CortesCaja
    ORDER BY FechaCorte DESC, CorteCajaID DESC;
END;
GO

IF OBJECT_ID(N'dbo.Finanzas_CortesCaja_SyncLog', N'U') IS NOT NULL
BEGIN
    SELECT TOP (30)
        FechaInicio,
        FechaFin,
        CONVERT(nvarchar(100), UnidadNegocioID) AS unidad_negocio_id,
        CONVERT(nvarchar(100), ServerID) AS server_id,
        SistemaOrigen,
        FechaDesde,
        FechaHasta,
        RegistrosLeidos,
        RegistrosInsertados,
        RegistrosActualizados,
        RegistrosOmitidos,
        RegistrosError,
        Estatus,
        LEFT(COALESCE(ErrorMensaje, N''), 500) AS error_mensaje,
        TipoEjecucion
    FROM dbo.Finanzas_CortesCaja_SyncLog
    ORDER BY FechaInicio DESC;
END
ELSE
BEGIN
    SELECT CAST('MISSING_TABLE: dbo.Finanzas_CortesCaja_SyncLog' AS nvarchar(200)) AS audit_error;
END;
GO

IF OBJECT_ID(N'dbo.Scheduler_BitacoraJobs', N'U') IS NOT NULL
BEGIN
    SELECT TOP (30)
        JobName,
        RunID,
        Accion,
        FechaAccion,
        CONVERT(nvarchar(100), ServerID) AS server_id,
        Exito,
        LEFT(COALESCE(MensajeError, N''), 500) AS mensaje_error,
        LEFT(COALESCE(DetallesJSON, N''), 1500) AS detalles_json
    FROM dbo.Scheduler_BitacoraJobs
    WHERE JobName = N'sync_ingresos_incremental'
    ORDER BY FechaAccion DESC;
END
ELSE
BEGIN
    SELECT CAST('MISSING_TABLE: dbo.Scheduler_BitacoraJobs' AS nvarchar(200)) AS audit_error;
END;
GO

IF OBJECT_ID(N'dbo.Unidades_Negocio', N'U') IS NOT NULL
   AND OBJECT_ID(N'dbo.Servidores_Conexiones', N'U') IS NOT NULL
BEGIN
    SELECT
        CONVERT(nvarchar(100), u.id) AS unidad_negocio_id,
        u.codigo AS unidad_codigo,
        u.nombre AS unidad_nombre,
        CONVERT(nvarchar(100), u.server_id) AS unidad_server_id,
        CONVERT(nvarchar(100), s.id) AS servidor_id,
        s.nombre AS servidor_nombre,
        s.system_type,
        s.database_name
    FROM dbo.Unidades_Negocio AS u
    LEFT JOIN dbo.Servidores_Conexiones AS s
      ON CONVERT(nvarchar(100), u.server_id) = CONVERT(nvarchar(100), s.id)
    WHERE u.activo = 1
      AND (
            UPPER(COALESCE(u.codigo, N'')) IN (N'130MID', N'130QRO', N'CIENFUEGOS', N'ESTELAR', N'ORIGEN')
         OR UPPER(COALESCE(u.nombre, N'')) LIKE N'%MERIDA%'
         OR UPPER(COALESCE(u.nombre, N'')) LIKE N'%QUERETARO%'
         OR UPPER(COALESCE(u.nombre, N'')) LIKE N'%CIENFUEGOS%'
         OR UPPER(COALESCE(u.nombre, N'')) LIKE N'%ESTELAR%'
         OR UPPER(COALESCE(u.nombre, N'')) LIKE N'%ORIGEN%'
      )
    ORDER BY u.nombre;
END;
GO

IF OBJECT_ID(N'dbo.Finanzas_CortesCaja', N'U') IS NOT NULL
BEGIN
    SELECT
        SUM(CASE WHEN UnidadNegocioID IS NULL THEN 1 ELSE 0 END) AS null_unidad_negocio_id,
        SUM(CASE WHEN ServerID IS NULL THEN 1 ELSE 0 END) AS null_server_id,
        SUM(CASE WHEN UnidadNegocioNombre IS NULL OR LTRIM(RTRIM(UnidadNegocioNombre)) = N'' THEN 1 ELSE 0 END) AS blank_unidad_nombre,
        SUM(CASE WHEN FechaCorte IS NULL THEN 1 ELSE 0 END) AS null_fecha_corte,
        SUM(CASE WHEN FechaSincronizacion IS NULL THEN 1 ELSE 0 END) AS null_fecha_sincronizacion
    FROM dbo.Finanzas_CortesCaja;
END;
GO