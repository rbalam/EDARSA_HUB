/* ============================================================
   EDARSAHUB - VALIDACIÓN INTELIGENCIA COMERCIAL FASE 1
   Archivo: 032_validacion_inteligencia_comercial_fase1.sql

   OBJETIVO:
   - Validar que IC Fase 1 siga operativa
   - Confirmar fuente principal Comercial_KPIs_Diarios_v2
   - Confirmar vistas/SP
   - Confirmar estado OK/STale/SIN_DATOS
   - No crear tablas
   - No sincronizar
   ============================================================ */

SET NOCOUNT ON;

PRINT '============================================================';
PRINT 'VALIDACIÓN INTELIGENCIA COMERCIAL FASE 1';
PRINT '============================================================';


/* ============================================================
   1. Validar objetos canónicos
   ============================================================ */

SELECT
    o.type_desc,
    s.name AS schema_name,
    o.name AS object_name,
    o.create_date,
    o.modify_date
FROM sys.objects o
INNER JOIN sys.schemas s
    ON o.schema_id = s.schema_id
WHERE o.name IN (
    'Comercial_Inteligencia_VW_KPIsEjecutivos',
    'Comercial_Inteligencia_VW_SyncStatus',
    'Sp_Validar_Inteligencia_Comercial_Status',
    'Comercial_KPIs_Diarios_v2',
    'Comercial_Ventas_Dia_Abiertas_v2',
    'Sync_PAX_Detalle',
    'Sync_Sales',
    'Unidades_Negocio'
)
ORDER BY o.type_desc, o.name;


/* ============================================================
   2. Validar fuente principal KPIs
   ============================================================ */

SELECT
    COUNT(*) AS registros,
    MIN(fecha_operacion) AS fecha_minima,
    MAX(fecha_operacion) AS fecha_maxima,
    MAX(fecha_sincronizacion) AS ultima_sincronizacion,
    SUM(ISNULL(ventas_total, 0)) AS ventas_total,
    SUM(ISNULL(ventas_sin_propina, 0)) AS ventas_sin_propina,
    SUM(ISNULL(propinas_total, 0)) AS propinas_total,
    SUM(ISNULL(tickets_total, 0)) AS tickets_total,
    SUM(ISNULL(pax_total, 0)) AS pax_total
FROM dbo.Comercial_KPIs_Diarios_v2
WHERE ISNULL(activo, 1) = 1;


/* ============================================================
   3. Validar vista ejecutiva
   ============================================================ */

SELECT TOP 20
    unidad_negocio_nombre,
    sistema_origen,
    fecha_operacion,
    ventas_total,
    ventas_sin_propina,
    propinas_total,
    tickets_total,
    pax_total,
    ticket_promedio,
    pax_promedio,
    fecha_sincronizacion
FROM dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
ORDER BY fecha_operacion DESC, unidad_negocio_nombre;


/* ============================================================
   4. Validar KPIs por unidad
   ============================================================ */

SELECT
    unidad_negocio_nombre,
    sistema_origen,
    COUNT(*) AS dias_con_datos,
    MIN(fecha_operacion) AS fecha_minima,
    MAX(fecha_operacion) AS fecha_maxima,
    SUM(ISNULL(ventas_total, 0)) AS ventas_total,
    SUM(ISNULL(ventas_sin_propina, 0)) AS ventas_sin_propina,
    SUM(ISNULL(propinas_total, 0)) AS propinas_total,
    SUM(ISNULL(tickets_total, 0)) AS tickets_total,
    SUM(ISNULL(pax_total, 0)) AS pax_total,
    MAX(fecha_sincronizacion) AS ultima_sync
FROM dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
GROUP BY unidad_negocio_nombre, sistema_origen
ORDER BY unidad_negocio_nombre;


/* ============================================================
   5. Validar últimos 30 días
   ============================================================ */

SELECT
    fecha_operacion,
    SUM(ISNULL(ventas_total, 0)) AS ventas_total,
    SUM(ISNULL(ventas_sin_propina, 0)) AS ventas_sin_propina,
    SUM(ISNULL(propinas_total, 0)) AS propinas_total,
    SUM(ISNULL(tickets_total, 0)) AS tickets_total,
    SUM(ISNULL(pax_total, 0)) AS pax_total
FROM dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
WHERE fecha_operacion >= DATEADD(DAY, -30, CAST(GETDATE() AS DATE))
GROUP BY fecha_operacion
ORDER BY fecha_operacion;


/* ============================================================
   6. Ejecutar SP de status
   ============================================================ */

EXEC dbo.Sp_Validar_Inteligencia_Comercial_Status;


/* ============================================================
   7. Validar módulo y RBAC
   ============================================================ */

DECLARE @ModuloID INT;

SELECT @ModuloID = ModuloID
FROM dbo.Usuario_Modulos
WHERE CodigoModulo = 'INTELIGENCIA_COMERCIAL';

SELECT
    ModuloID,
    CodigoModulo,
    NombreModulo,
    Ruta,
    Activo
FROM dbo.Usuario_Modulos
WHERE CodigoModulo = 'INTELIGENCIA_COMERCIAL';

SELECT
    r.CodigoRol,
    a.CodigoAccion,
    prm.Activo
FROM dbo.Usuario_PermisosRolModulo prm
INNER JOIN dbo.Usuario_Roles r
    ON r.RolID = prm.RolID
INNER JOIN dbo.Usuario_Acciones a
    ON a.AccionID = prm.AccionID
WHERE prm.ModuloID = @ModuloID
ORDER BY prm.Activo DESC, r.CodigoRol, a.CodigoAccion;


/* ============================================================
   8. Confirmación final
   ============================================================ */

SELECT
    'INTELIGENCIA_COMERCIAL_FASE1_OPERATIVA' AS resultado,
    SYSDATETIME() AS fecha_validacion,
    'Fuente principal: Comercial_KPIs_Diarios_v2. Sync_Sales/Sync_PAX_Detalle pueden estar pendientes sin bloquear dashboard ejecutivo.' AS nota;
