-- =========================================================================
-- SCRIPT: RECONFIGURACIÓN DE JOB Y BARRIDO DE AUDITORÍA DE VENTAS (D-10)
-- INFRAESTRUCTURA: EDARSA_HUB_SQL (SERVIDOR CENTRAL)
-- DETECCIÓN: ELIMINA LA LIMITANTE DE 3 DÍAS DE REPLICACIÓN DE EMERGENT
-- =========================================================================

SET NOCOUNT ON;
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

-- 🔍 PARÁMETRO DE CONTROL DE SOBERANÍA CONTABLE
-- Por diseño táctico se establece en 10 días atrás para capturar reajustes diferidos.
DECLARE @Dias_Barrido_Atras INT = 10; 

DECLARE @Fecha_Limite_Historica DATE = DATEADD(DAY, -@Dias_Barrido_Atras, CAST(GETDATE() AS DATE));
DECLARE @Ayer DATE = DATEADD(DAY, -1, CAST(GETDATE() AS DATE));

PRINT '============= INICIANDO BARRIDO DE AUDITORÍA TRANSACCIONAL =============';
PRINT 'Rango de re-evaluación forzada: ' + CAST(@Fecha_Limite_Historica AS VARCHAR) + ' hasta ' + CAST(@Ayer AS VARCHAR);

BEGIN TRANSACTION;

BEGIN TRY
    -- 1. CAPA TEMPORAL DE CONCILIACIÓN AGRESIVA (RESTRICCIONES FUENTE)
    IF OBJECT_ID('tempdb..#Barrido_Fuente_Tickets') IS NOT NULL DROP TABLE #Barrido_Fuente_Tickets;
    
    CREATE TABLE #Barrido_Fuente_Tickets (
        id_factura VARCHAR(50),
        fecha_corte DATETIME,
        nombre_unidad VARCHAR(50),
        serie_registro VARCHAR(20),
        monto_total DECIMAL(18,4),
        cheques_visual INT
    );

    -- >> BARRIDO HISTÓRICO LOCAL: CIENFUEGOS
    INSERT INTO #Barrido_Fuente_Tickets
    SELECT 
        TRIM(CAST(src.id_ticket AS VARCHAR(50))),
        src.fecha_registro_ticket,
        'CIENFUEGOS',
        TRIM(UPPER(src.serie)),
        src.total_neto,
        1
    FROM [SERVIDO_CIENFUEGOS].BD_Transaccional.dbo.Tickets src
    WHERE src.fecha_registro_ticket BETWEEN @Fecha_Limite_Historica AND DATEADD(SECOND, -1, CAST(CAST(GETDATE() AS DATE) AS DATETIME))
      AND src.status_ticket = 'CERRADO';

    -- >> BARRIDO HISTÓRICO LOCAL: ORIGEN
    INSERT INTO #Barrido_Fuente_Tickets
    SELECT 
        TRIM(CAST(src.id_ticket AS VARCHAR(50))),
        src.fecha_registro_ticket,
        'ORIGEN',
        TRIM(UPPER(src.serie)),
        src.total_neto,
        1
    FROM [SERVIDOR_ORIGEN].BD_Transaccional.dbo.Tickets src
    WHERE src.fecha_registro_ticket BETWEEN @Fecha_Limite_Historica AND DATEADD(SECOND, -1, CAST(CAST(GETDATE() AS DATE) AS DATETIME))
      AND src.status_ticket = 'CERRADO';

    -- [Nota de Ingeniería: El equipo de TI puede añadir aquí el resto de servidores espejo de las demás unidades]

    -- 2. OPERACIÓN UPSERT (MERGE) DE MÁXIMA AUTORIDAD CONTABLE
    -- No importa si el registro ya existía o si fue modificado en la sucursal, el HUB se alinea.
    MERGE EDARSA_HUB_SQL.dbo.Ventas_Consolidadas AS TARGET
    USING #Barrido_Fuente_Tickets AS SOURCE
    ON (TARGET.id_factura = SOURCE.id_factura AND TARGET.nombre_unidad = SOURCE.nombre_unidad)

    -- ESCENARIO 1: El ticket ya existía pero hubo una modificación de venta o reajuste comercial posterior
    WHEN MATCHED AND (TARGET.monto_total <> SOURCE.monto_total OR TARGET.fecha_corte <> SOURCE.fecha_corte) THEN
        UPDATE SET 
            TARGET.monto_total = SOURCE.monto_total,
            TARGET.fecha_corte = SOURCE.fecha_corte,
            TARGET.ultima_sincronizacion = GETDATE(),
            TARGET.comentario_auditoria = '🔄 RE-AUDITADO: Modificación detectada fuera de la ventana de 3 días por barrido ampliado.'

    -- ESCENARIO 2: Registros huérfanos que el viejo Job incremental de 3 días omitió por completo
    WHEN NOT MATCHED BY TARGET THEN
        INSERT (id_factura, fecha_corte, nombre_unidad, serie_registro, monto_total, cheques_visual, ultima_sincronizacion, comentario_auditoria)
        VALUES (SOURCE.id_factura, SOURCE.fecha_corte, SOURCE.nombre_unidad, SOURCE.serie_registro, SOURCE.monto_total, SOURCE.cheques_visual, GETDATE(), '📥 INYECTADO: Recuperado por barrido histórico de seguridad.');

    -- 3. REPORTE TÁCTICO DE ACTUALIZACIONES FORZADAS
    -- Expone de forma inmediata cuántos registros modificados o rezagados estaban ocultos en la ventana ciega.
    SELECT 
        nombre_unidad AS [Unidad de Negocio],
        CASE 
            WHEN comentario_auditoria LIKE '%RE-AUDITADO%' THEN 'Modificaciones Comerciales / Ajustes Posteriores'
            WHEN comentario_auditoria LIKE '%RECOVERY%' OR comentario_auditoria LIKE '%RECONSTITUIDO%' OR comentario_auditoria LIKE '%INYECTADO%' THEN 'Tickets Rezagados Omitidos por Carga de 3 Días'
            ELSE 'Otros Reajustes Contables'
        END AS [Naturaleza del Ajuste Encontrado],
        COUNT(id_factura) AS [Volumen de Transacciones Corregidas],
        SUM(monto_total) AS [Recuperación e Impacto en Tablero ($)]
    FROM EDARSA_HUB_SQL.dbo.Ventas_Consolidadas
    WHERE ultima_sincronizacion >= DATEADD(MINUTE, -5, GETDATE()) -- Filtra solo lo modificado en esta corrida del Job
      AND nombre_unidad IN ('CIENFUEGOS', 'ORIGEN')
    GROUP BY nombre_unidad, comentario_auditoria;

    COMMIT TRANSACTION;
    PRINT '============= ✅ BARRIDO Y ARREGLO DE JOB CONCLUIDO EXITOSAMENTE =============';

END TRY
BEGIN CATCH
    ROLLBACK TRANSACTION;
    PRINT '❌ ERROR CRÍTICO EN REPLICACIÓN AMPLIO DE JOB: ' + ERROR_MESSAGE();
END CATCH;

IF OBJECT_ID('tempdb..#Barrido_Fuente_Tickets') IS NOT NULL DROP TABLE #Barrido_Fuente_Tickets;
