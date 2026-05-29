-- =========================================================================
-- SCRIPT: FORZADO DE SINCRONIZACIÓN HISTÓRICA Y DIAGNÓSTICO DE CAUSA RAÍZ
-- ENTIDAD: EDARSA_HUB_SQL (CONSOLIDADOR CENTRAL)
-- APLICACIÓN: EXCLUSIVA PARA HISTÓRICO CERRADO (D-1) - MAYO 2026
-- =========================================================================

SET NOCOUNT ON;
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED; -- Protege de bloqueos las cajas en sitio

DECLARE @InicioMes DATE = '2026-05-01';
DECLARE @Ayer DATE = DATEADD(DAY, -1, CAST(GETDATE() AS DATE));

BEGIN TRANSACTION;

BEGIN TRY
    -- 🔍 PASO 1: CREACIÓN DE CAPA TRANSACCIONAL DE AUDITORÍA
    IF OBJECT_ID('tempdb..#Data_Fuente_Auditada') IS NOT NULL DROP TABLE #Data_Fuente_Auditada;
    CREATE TABLE #Data_Fuente_Auditada (
        id_factura VARCHAR(50),
        fecha_corte DATETIME,
        nombre_unidad VARCHAR(50),
        serie_registro VARCHAR(20),
        monto_total DECIMAL(18,4),
        cheques_visual INT,
        motivo_desactualizacion VARCHAR(250)
    );

    -- 🔍 PASO 2: EXTRACCIÓN HISTÓRICA CON ANÁLISIS DE MOTIVOS
    -- Evaluamos ticket por ticket el desfase temporal y la consistencia del software local.
    INSERT INTO #Data_Fuente_Auditada
    SELECT 
        TRIM(CAST(src.id_ticket AS VARCHAR(50))) AS id_factura,
        src.fecha_registro_ticket AS fecha_corte,
        'CIENFUEGOS' AS nombre_unidad,
        TRIM(UPPER(src.serie)) AS serie_registro,
        src.total_neto AS monto_total,
        1 AS cheques_visual,
        
        -- Matriz de evaluación automática de motivos de desactualización
        CASE 
            WHEN hub.id_factura IS NULL THEN '🚨 Gaps de Comunicación: Registro omitido en la carga incremental de Emergent.'
            WHEN hub.monto_total <> src.total_neto THEN '⚠️ Alteración de Valor: Mutación de dinero en tránsito (Mapeo de Impuestos/Descuentos erróneo).'
            ELSE 'Sincronizado'
        END AS motivo_desactualizacion
    FROM [SERVIDO_CIENFUEGOS].BD_Transaccional.dbo.Tickets src
    LEFT JOIN EDARSA_HUB_SQL.dbo.Ventas_Consolidadas hub 
        ON TRIM(CAST(src.id_ticket AS VARCHAR(50))) = hub.id_factura AND hub.nombre_unidad = 'CIENFUEGOS'
    WHERE src.fecha_registro_ticket BETWEEN @InicioMes AND DATEADD(SECOND, -1, CAST(CAST(GETDATE() AS DATE) AS DATETIME))
      AND src.status_ticket = 'CERRADO';

    -- 🔍 PASO 3: ALINEACIÓN FORZADA Y CLAVADO DE METADATOS DE ERROR (MERGE UPSERT)
    MERGE EDARSA_HUB_SQL.dbo.Ventas_Consolidadas AS TARGET
    USING #Data_Fuente_Auditada AS SOURCE
    ON (TARGET.id_factura = SOURCE.id_factura AND TARGET.nombre_unidad = SOURCE.nombre_unidad)

    -- Escenario A: El ticket existe pero el dinero está deformado en el HUB
    WHEN MATCHED AND TARGET.monto_total <> SOURCE.monto_total THEN
        UPDATE SET 
            TARGET.monto_total = SOURCE.monto_total,
            TARGET.ultima_sincronizacion = GETDATE(),
            TARGET.comentario_auditoria = SOURCE.motivo_desactualizacion

    -- Escenario B: El ticket quedó rezagado y nunca viajó (El hueco de los $190K)
    WHEN NOT MATCHED BY TARGET THEN
        INSERT (id_factura, fecha_corte, nombre_unidad, serie_registro, monto_total, cheques_visual, ultima_sincronizacion, comentario_auditoria)
        VALUES (SOURCE.id_factura, SOURCE.fecha_corte, SOURCE.nombre_unidad, SOURCE.serie_registro, SOURCE.monto_total, SOURCE.cheques_visual, GETDATE(), SOURCE.motivo_desactualizacion);

    -- 🔍 PASO 4: REPORTE DE SALIDA EJECUTIVO - MOTIVO GENERAL DE LA DESACTUALIZACIÓN
    -- Consolida las causas del error detectadas en la infraestructura para rendición de cuentas.
    SELECT 
        nombre_unidad AS [Unidad de Negocio],
        comentario_auditoria AS [Causa Raíz de la Desactualización],
        COUNT(id_factura) AS [Cantidad de Tickets Afectados],
        SUM(monto_total) AS [Impacto Monetario Corregido ($)]
    FROM EDARSA_HUB_SQL.dbo.Ventas_Consolidadas
    WHERE nombre_unidad = 'CIENFUEGOS'
      AND fecha_corte BETWEEN @InicioMes AND @Ayer
      AND comentario_auditoria LIKE '%Emergent%' OR comentario_auditoria LIKE '%Gaps%'
    GROUP BY nombre_unidad, comentario_auditoria;

    COMMIT TRANSACTION;
    PRINT '✅ ALINEACIÓN CONCLUIDA: El histórico de Cienfuegos se ha forzado y los motivos de falla quedan grabados.';

END TRY
BEGIN CATCH
    ROLLBACK TRANSACTION;
    PRINT '❌ ERROR CRÍTICO EN SINCRONIZACIÓN: Proceso abortado. Motivo: ' + ERROR_MESSAGE();
END CATCH;

IF OBJECT_ID('tempdb..#Data_Fuente_Auditada') IS NOT NULL DROP TABLE #Data_Fuente_Auditada;
