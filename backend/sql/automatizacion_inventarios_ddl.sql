-- =============================================================================
-- =============================================================================
--
--                    EDARSA HUB - SCRIPT DDL
--                    CAB-003: AUTOMATIZACIÓN DE ANÁLISIS DE INVENTARIOS
--                    FASE 0: INFRAESTRUCTURA BASE
--
-- =============================================================================
-- =============================================================================
--
-- OBJETIVO:
-- ---------
-- Crear las 6 tablas base para el módulo de automatización de análisis de
-- inventarios. Este módulo detectará nuevos inventarios capturados en sistemas
-- origen (SoftRestaurant/MPRO) y enviará análisis automáticamente.
--
-- ALCANCE:
-- --------
-- - Fase 0 únicamente (infraestructura desacoplada)
-- - No activa procesos automáticos
-- - No conecta a sistemas origen
-- - No modifica tablas existentes
--
-- TABLAS QUE CREA:
-- ----------------
-- 1. automatizacion_inventarios_config          - Configuración por servidor/sucursal/almacén
-- 2. automatizacion_inventarios_destinatarios   - Emails/WhatsApp destino
-- 3. automatizacion_inventarios_folios_procesados - Control de duplicados (clave única 6 campos)
-- 4. automatizacion_inventarios_ejecuciones     - Bitácora del scheduler
-- 5. automatizacion_inventarios_envios          - Registro de envíos
-- 6. automatizacion_inventarios_ultimo_folio_conocido - Marca de agua incremental
--
-- =============================================================================
--
--                              ⚠️  ADVERTENCIA  ⚠️
--
--     ESTE SCRIPT SOLO DEBE EJECUTARSE EN LA BASE DE DATOS EDARSA HUB
--
--     ❌ NO ejecutar en SoftRestaurant
--     ❌ NO ejecutar en MPRO
--     ❌ NO ejecutar en ningún sistema origen
--
--     Antes de ejecutar, verificar que está conectado a EDARSA HUB.
--
-- =============================================================================
--
-- Versión: 1.0
-- Fecha: Diciembre 2025
-- Autor: Equipo EDARSA HUB
-- Estado: Aprobado para ejecución manual
--
-- =============================================================================


-- =============================================================================
-- SECCIÓN 1: CREACIÓN DE TABLAS
-- =============================================================================

PRINT '=============================================================================';
PRINT 'INICIO - Creación de tablas Fase 0 - Automatización de Inventarios';
PRINT '=============================================================================';
PRINT '';


-- -----------------------------------------------------------------------------
-- TABLA 1: automatizacion_inventarios_config
-- Propósito: Configuración general por servidor/sucursal/almacén
-- -----------------------------------------------------------------------------

PRINT 'Creando tabla 1 de 6: automatizacion_inventarios_config...';

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[automatizacion_inventarios_config]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[automatizacion_inventarios_config] (
        -- Identificador
        [config_id]             UNIQUEIDENTIFIER    NOT NULL    DEFAULT NEWID(),
        
        -- Jerarquía de aplicación
        [server_id]             NVARCHAR(50)        NOT NULL,
        [sucursal_id]           NVARCHAR(20)        NULL,
        [almacen_id]            NVARCHAR(20)        NULL,
        
        -- Configuración de ejecución
        [intervalo_minutos]     INT                 NOT NULL    DEFAULT 15,
        [hora_inicio]           TIME                NULL,
        [hora_fin]              TIME                NULL,
        
        -- Feature flag por registro
        [activo]                BIT                 NOT NULL    DEFAULT 0,
        
        -- Campos de auditoría
        [created_at]            DATETIME            NOT NULL    DEFAULT GETUTCDATE(),
        [updated_at]            DATETIME            NULL,
        [created_by]            NVARCHAR(100)       NULL,
        [updated_by]            NVARCHAR(100)       NULL,
        
        CONSTRAINT [PK_automatizacion_config] PRIMARY KEY CLUSTERED ([config_id])
    );
    
    CREATE NONCLUSTERED INDEX [IX_config_servidor] 
        ON [dbo].[automatizacion_inventarios_config] ([server_id], [sucursal_id], [almacen_id]);
    
    PRINT '   ✓ Tabla automatizacion_inventarios_config creada.';
END
ELSE
BEGIN
    PRINT '   ⚠ Tabla automatizacion_inventarios_config ya existe. Saltando.';
END
GO


-- -----------------------------------------------------------------------------
-- TABLA 2: automatizacion_inventarios_destinatarios
-- Propósito: Emails/WhatsApp destino por nivel jerárquico
-- -----------------------------------------------------------------------------

PRINT 'Creando tabla 2 de 6: automatizacion_inventarios_destinatarios...';

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[automatizacion_inventarios_destinatarios]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[automatizacion_inventarios_destinatarios] (
        -- Identificador
        [destinatario_id]       UNIQUEIDENTIFIER    NOT NULL    DEFAULT NEWID(),
        
        -- Jerarquía de aplicación
        [server_id]             NVARCHAR(50)        NOT NULL,
        [sucursal_id]           NVARCHAR(20)        NULL,
        [almacen_id]            NVARCHAR(20)        NULL,
        [nivel_origen]          NVARCHAR(20)        NOT NULL,
        
        -- Canal y tipo
        [canal]                 NVARCHAR(20)        NOT NULL    DEFAULT 'EMAIL',
        [tipo_destinatario]     NVARCHAR(10)        NOT NULL    DEFAULT 'TO',
        
        -- Datos de contacto
        [email]                 NVARCHAR(255)       NULL,
        [telefono]              NVARCHAR(20)        NULL,
        [nombre_contacto]       NVARCHAR(100)       NULL,
        
        -- Estado
        [activo]                BIT                 NOT NULL    DEFAULT 1,
        
        -- Campos de auditoría
        [created_at]            DATETIME            NOT NULL    DEFAULT GETUTCDATE(),
        [updated_at]            DATETIME            NULL,
        [created_by]            NVARCHAR(100)       NULL,
        [updated_by]            NVARCHAR(100)       NULL,
        
        CONSTRAINT [PK_automatizacion_destinatarios] PRIMARY KEY CLUSTERED ([destinatario_id]),
        CONSTRAINT [CK_destinatarios_nivel] CHECK ([nivel_origen] IN ('SERVER', 'SUCURSAL', 'ALMACEN')),
        CONSTRAINT [CK_destinatarios_canal] CHECK ([canal] IN ('EMAIL', 'WHATSAPP', 'AMBOS')),
        CONSTRAINT [CK_destinatarios_tipo] CHECK ([tipo_destinatario] IN ('TO', 'CC', 'BCC'))
    );
    
    CREATE NONCLUSTERED INDEX [IX_destinatarios_jerarquia] 
        ON [dbo].[automatizacion_inventarios_destinatarios] ([server_id], [sucursal_id], [almacen_id], [canal], [activo]);
    
    PRINT '   ✓ Tabla automatizacion_inventarios_destinatarios creada.';
END
ELSE
BEGIN
    PRINT '   ⚠ Tabla automatizacion_inventarios_destinatarios ya existe. Saltando.';
END
GO


-- -----------------------------------------------------------------------------
-- TABLA 3: automatizacion_inventarios_folios_procesados
-- Propósito: Control de duplicados con clave única de 6 componentes
-- CRÍTICO: Esta tabla tiene la constraint UNIQUE principal del sistema
-- -----------------------------------------------------------------------------

PRINT 'Creando tabla 3 de 6: automatizacion_inventarios_folios_procesados...';

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[automatizacion_inventarios_folios_procesados]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[automatizacion_inventarios_folios_procesados] (
        -- Identificador (FK referenciable en Fase 1.5)
        [procesado_id]          UNIQUEIDENTIFIER    NOT NULL    DEFAULT NEWID(),
        
        -- CLAVE ÚNICA DE 6 COMPONENTES
        [sistema_origen]        NVARCHAR(20)        NOT NULL,
        [server_id]             NVARCHAR(50)        NOT NULL,
        [sucursal_id]           NVARCHAR(20)        NOT NULL,
        [almacen_id]            NVARCHAR(20)        NOT NULL,
        [folio_inventario]      NVARCHAR(50)        NOT NULL,
        [fecha_inventario]      DATE                NOT NULL,
        
        -- Hash de verificación
        [hash_verificacion]     NVARCHAR(64)        NOT NULL,
        
        -- Estado y control de concurrencia
        [estado]                NVARCHAR(20)        NOT NULL    DEFAULT 'EN_PROCESO',
        [heartbeat_at]          DATETIME            NULL,
        
        -- Resultado del procesamiento
        [fecha_procesado]       DATETIME            NULL,
        [error_detalle]         NVARCHAR(MAX)       NULL,
        [ruta_archivo_excel]    NVARCHAR(500)       NULL,
        
        -- Campos de auditoría
        [created_at]            DATETIME            NOT NULL    DEFAULT GETUTCDATE(),
        [updated_at]            DATETIME            NULL,
        [created_by]            NVARCHAR(100)       NULL,
        [updated_by]            NVARCHAR(100)       NULL,
        
        CONSTRAINT [PK_automatizacion_folios] PRIMARY KEY CLUSTERED ([procesado_id]),
        CONSTRAINT [CK_folios_sistema] CHECK ([sistema_origen] IN ('SOFTRESTAURANT', 'MPRO')),
        CONSTRAINT [CK_folios_estado] CHECK ([estado] IN ('EN_PROCESO', 'EXITOSO', 'ERROR')),
        
        -- *** CONSTRAINT UNIQUE PRINCIPAL: Clave de 6 componentes ***
        CONSTRAINT [UQ_folios_clave_unica] UNIQUE (
            [sistema_origen],
            [server_id],
            [sucursal_id],
            [almacen_id],
            [folio_inventario],
            [fecha_inventario]
        )
    );
    
    CREATE NONCLUSTERED INDEX [IX_folios_hash] 
        ON [dbo].[automatizacion_inventarios_folios_procesados] ([hash_verificacion]);
    
    CREATE NONCLUSTERED INDEX [IX_folios_estado_heartbeat] 
        ON [dbo].[automatizacion_inventarios_folios_procesados] ([estado], [heartbeat_at])
        WHERE [estado] = 'EN_PROCESO';
    
    PRINT '   ✓ Tabla automatizacion_inventarios_folios_procesados creada.';
    PRINT '   ✓ Constraint UQ_folios_clave_unica creada (6 campos).';
END
ELSE
BEGIN
    PRINT '   ⚠ Tabla automatizacion_inventarios_folios_procesados ya existe. Saltando.';
END
GO


-- -----------------------------------------------------------------------------
-- TABLA 4: automatizacion_inventarios_ejecuciones
-- Propósito: Bitácora de cada ciclo del scheduler
-- -----------------------------------------------------------------------------

PRINT 'Creando tabla 4 de 6: automatizacion_inventarios_ejecuciones...';

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[automatizacion_inventarios_ejecuciones]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[automatizacion_inventarios_ejecuciones] (
        -- Identificador
        [ejecucion_id]          UNIQUEIDENTIFIER    NOT NULL    DEFAULT NEWID(),
        
        -- Tiempos de ejecución
        [fecha_inicio]          DATETIME            NOT NULL,
        [fecha_fin]             DATETIME            NULL,
        
        -- Estado y métricas
        [estado]                NVARCHAR(20)        NOT NULL    DEFAULT 'INICIADO',
        [servidores_escaneados] INT                 NULL,
        [folios_detectados]     INT                 NULL,
        [folios_procesados]     INT                 NULL,
        [folios_error]          INT                 NULL,
        [detalle_errores]       NVARCHAR(MAX)       NULL,
        
        -- Campos de auditoría
        [created_at]            DATETIME            NOT NULL    DEFAULT GETUTCDATE(),
        [updated_at]            DATETIME            NULL,
        
        CONSTRAINT [PK_automatizacion_ejecuciones] PRIMARY KEY CLUSTERED ([ejecucion_id]),
        CONSTRAINT [CK_ejecuciones_estado] CHECK ([estado] IN ('INICIADO', 'COMPLETADO', 'ERROR'))
    );
    
    CREATE NONCLUSTERED INDEX [IX_ejecuciones_fecha] 
        ON [dbo].[automatizacion_inventarios_ejecuciones] ([fecha_inicio] DESC);
    
    PRINT '   ✓ Tabla automatizacion_inventarios_ejecuciones creada.';
END
ELSE
BEGIN
    PRINT '   ⚠ Tabla automatizacion_inventarios_ejecuciones ya existe. Saltando.';
END
GO


-- -----------------------------------------------------------------------------
-- TABLA 5: automatizacion_inventarios_envios
-- Propósito: Registro de cada email/WhatsApp enviado
-- -----------------------------------------------------------------------------

PRINT 'Creando tabla 5 de 6: automatizacion_inventarios_envios...';

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[automatizacion_inventarios_envios]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[automatizacion_inventarios_envios] (
        -- Identificador
        [envio_id]              UNIQUEIDENTIFIER    NOT NULL    DEFAULT NEWID(),
        
        -- Relación con folio procesado
        [procesado_id]          UNIQUEIDENTIFIER    NOT NULL,
        
        -- Destinatario y canal
        [destinatario_email]    NVARCHAR(255)       NOT NULL,
        [canal]                 NVARCHAR(20)        NOT NULL    DEFAULT 'EMAIL',
        [tipo_destinatario]     NVARCHAR(10)        NOT NULL,
        
        -- Estado del envío
        [fecha_envio]           DATETIME            NULL,
        [estado]                NVARCHAR(20)        NOT NULL    DEFAULT 'PENDIENTE',
        [intentos]              INT                 NOT NULL    DEFAULT 0,
        [error_detalle]         NVARCHAR(MAX)       NULL,
        
        -- Campos de auditoría
        [created_at]            DATETIME            NOT NULL    DEFAULT GETUTCDATE(),
        [updated_at]            DATETIME            NULL,
        
        CONSTRAINT [PK_automatizacion_envios] PRIMARY KEY CLUSTERED ([envio_id]),
        CONSTRAINT [FK_envios_procesado] FOREIGN KEY ([procesado_id]) 
            REFERENCES [dbo].[automatizacion_inventarios_folios_procesados] ([procesado_id]),
        CONSTRAINT [CK_envios_canal] CHECK ([canal] IN ('EMAIL', 'WHATSAPP')),
        CONSTRAINT [CK_envios_tipo] CHECK ([tipo_destinatario] IN ('TO', 'CC', 'BCC')),
        CONSTRAINT [CK_envios_estado] CHECK ([estado] IN ('PENDIENTE', 'ENVIADO', 'ERROR'))
    );
    
    CREATE NONCLUSTERED INDEX [IX_envios_procesado] 
        ON [dbo].[automatizacion_inventarios_envios] ([procesado_id]);
    
    CREATE NONCLUSTERED INDEX [IX_envios_pendientes] 
        ON [dbo].[automatizacion_inventarios_envios] ([estado], [intentos])
        WHERE [estado] IN ('PENDIENTE', 'ERROR');
    
    PRINT '   ✓ Tabla automatizacion_inventarios_envios creada.';
END
ELSE
BEGIN
    PRINT '   ⚠ Tabla automatizacion_inventarios_envios ya existe. Saltando.';
END
GO


-- -----------------------------------------------------------------------------
-- TABLA 6: automatizacion_inventarios_ultimo_folio_conocido
-- Propósito: Marca de agua para detección incremental por almacén
-- -----------------------------------------------------------------------------

PRINT 'Creando tabla 6 de 6: automatizacion_inventarios_ultimo_folio_conocido...';

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[automatizacion_inventarios_ultimo_folio_conocido]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[automatizacion_inventarios_ultimo_folio_conocido] (
        -- Identificador
        [id]                    UNIQUEIDENTIFIER    NOT NULL    DEFAULT NEWID(),
        
        -- Clave única por almacén y sistema
        [sistema_origen]        NVARCHAR(20)        NOT NULL,
        [server_id]             NVARCHAR(50)        NOT NULL,
        [sucursal_id]           NVARCHAR(20)        NOT NULL,
        [almacen_id]            NVARCHAR(20)        NOT NULL,
        
        -- Marca de agua
        [ultimo_folio]          NVARCHAR(50)        NOT NULL,
        [fecha_ultimo_folio]    DATE                NOT NULL,
        [fecha_actualizacion]   DATETIME            NOT NULL,
        
        -- Campos de auditoría
        [created_at]            DATETIME            NOT NULL    DEFAULT GETUTCDATE(),
        [updated_at]            DATETIME            NULL,
        [created_by]            NVARCHAR(100)       NULL,
        [updated_by]            NVARCHAR(100)       NULL,
        
        CONSTRAINT [PK_automatizacion_ultimo_folio] PRIMARY KEY CLUSTERED ([id]),
        CONSTRAINT [CK_ultimo_folio_sistema] CHECK ([sistema_origen] IN ('SOFTRESTAURANT', 'MPRO')),
        
        CONSTRAINT [UQ_ultimo_folio_clave] UNIQUE (
            [sistema_origen],
            [server_id],
            [sucursal_id],
            [almacen_id]
        )
    );
    
    CREATE NONCLUSTERED INDEX [IX_ultimo_folio_servidor] 
        ON [dbo].[automatizacion_inventarios_ultimo_folio_conocido] ([server_id], [sistema_origen]);
    
    PRINT '   ✓ Tabla automatizacion_inventarios_ultimo_folio_conocido creada.';
END
ELSE
BEGIN
    PRINT '   ⚠ Tabla automatizacion_inventarios_ultimo_folio_conocido ya existe. Saltando.';
END
GO


PRINT '';
PRINT '=============================================================================';
PRINT 'FIN - Creación de tablas completada';
PRINT '=============================================================================';
PRINT '';


-- =============================================================================
-- SECCIÓN 2: VALIDACIÓN POST-EJECUCIÓN
-- =============================================================================
-- Ejecutar estas consultas después de crear las tablas para verificar
-- que todo quedó correctamente instalado.
-- =============================================================================

PRINT '=============================================================================';
PRINT 'VALIDACIÓN POST-EJECUCIÓN';
PRINT '=============================================================================';
PRINT '';

-- -----------------------------------------------------------------------------
-- VALIDACIÓN 2.1: Verificar que las 6 tablas existen
-- -----------------------------------------------------------------------------

PRINT 'Validación 2.1: Verificando existencia de las 6 tablas...';
PRINT '';

SELECT 
    t.name AS tabla,
    CASE WHEN t.object_id IS NOT NULL THEN '✓ EXISTE' ELSE '✗ NO EXISTE' END AS estado
FROM (VALUES 
    ('automatizacion_inventarios_config'),
    ('automatizacion_inventarios_destinatarios'),
    ('automatizacion_inventarios_folios_procesados'),
    ('automatizacion_inventarios_ejecuciones'),
    ('automatizacion_inventarios_envios'),
    ('automatizacion_inventarios_ultimo_folio_conocido')
) AS tablas_esperadas(name)
LEFT JOIN sys.tables t ON t.name = tablas_esperadas.name
ORDER BY tablas_esperadas.name;

PRINT '';


-- -----------------------------------------------------------------------------
-- VALIDACIÓN 2.2: Verificar índices creados
-- -----------------------------------------------------------------------------

PRINT 'Validación 2.2: Verificando índices...';
PRINT '';

SELECT 
    t.name AS tabla,
    i.name AS indice,
    i.type_desc AS tipo
FROM sys.indexes i
INNER JOIN sys.tables t ON i.object_id = t.object_id
WHERE t.name LIKE 'automatizacion_inventarios_%'
  AND i.name IS NOT NULL
ORDER BY t.name, i.name;

PRINT '';


-- -----------------------------------------------------------------------------
-- VALIDACIÓN 2.3: Verificar constraints (CHECK, UNIQUE, FK)
-- -----------------------------------------------------------------------------

PRINT 'Validación 2.3: Verificando constraints...';
PRINT '';

-- CHECK constraints
SELECT 
    t.name AS tabla,
    cc.name AS constraint_check,
    cc.definition AS definicion
FROM sys.check_constraints cc
INNER JOIN sys.tables t ON cc.parent_object_id = t.object_id
WHERE t.name LIKE 'automatizacion_inventarios_%'
ORDER BY t.name, cc.name;

PRINT '';

-- UNIQUE constraints
SELECT 
    t.name AS tabla,
    i.name AS constraint_unique,
    STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) AS columnas
FROM sys.indexes i
INNER JOIN sys.tables t ON i.object_id = t.object_id
INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE t.name LIKE 'automatizacion_inventarios_%'
  AND i.is_unique_constraint = 1
GROUP BY t.name, i.name
ORDER BY t.name;

PRINT '';

-- Foreign Key constraints
SELECT 
    OBJECT_NAME(fk.parent_object_id) AS tabla_origen,
    fk.name AS constraint_fk,
    OBJECT_NAME(fk.referenced_object_id) AS tabla_referenciada
FROM sys.foreign_keys fk
WHERE OBJECT_NAME(fk.parent_object_id) LIKE 'automatizacion_inventarios_%'
ORDER BY tabla_origen;

PRINT '';


-- -----------------------------------------------------------------------------
-- VALIDACIÓN 2.4: Verificar constraint UNIQUE crítica de folios_procesados
-- -----------------------------------------------------------------------------

PRINT 'Validación 2.4: Verificando constraint UQ_folios_clave_unica (CRÍTICA)...';
PRINT '';

IF EXISTS (
    SELECT 1 
    FROM sys.indexes i 
    INNER JOIN sys.tables t ON i.object_id = t.object_id 
    WHERE t.name = 'automatizacion_inventarios_folios_procesados' 
      AND i.name = 'UQ_folios_clave_unica'
      AND i.is_unique_constraint = 1
)
BEGIN
    PRINT '   ✓ Constraint UQ_folios_clave_unica EXISTE';
    
    -- Mostrar las columnas de la constraint
    SELECT 
        '   Columna ' + CAST(ic.key_ordinal AS VARCHAR) + ': ' + c.name AS detalle
    FROM sys.indexes i
    INNER JOIN sys.tables t ON i.object_id = t.object_id
    INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
    INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
    WHERE t.name = 'automatizacion_inventarios_folios_procesados'
      AND i.name = 'UQ_folios_clave_unica'
    ORDER BY ic.key_ordinal;
END
ELSE
BEGIN
    PRINT '   ✗ ERROR: Constraint UQ_folios_clave_unica NO EXISTE';
END

PRINT '';


-- -----------------------------------------------------------------------------
-- VALIDACIÓN 2.5: Resumen final
-- -----------------------------------------------------------------------------

PRINT '=============================================================================';
PRINT 'RESUMEN DE VALIDACIÓN';
PRINT '=============================================================================';

DECLARE @tablas_creadas INT;
DECLARE @indices_creados INT;
DECLARE @constraints_check INT;
DECLARE @constraints_unique INT;
DECLARE @constraints_fk INT;

SELECT @tablas_creadas = COUNT(*) FROM sys.tables WHERE name LIKE 'automatizacion_inventarios_%';
SELECT @indices_creados = COUNT(*) FROM sys.indexes i INNER JOIN sys.tables t ON i.object_id = t.object_id WHERE t.name LIKE 'automatizacion_inventarios_%' AND i.name IS NOT NULL AND i.is_primary_key = 0;
SELECT @constraints_check = COUNT(*) FROM sys.check_constraints cc INNER JOIN sys.tables t ON cc.parent_object_id = t.object_id WHERE t.name LIKE 'automatizacion_inventarios_%';
SELECT @constraints_unique = COUNT(*) FROM sys.indexes i INNER JOIN sys.tables t ON i.object_id = t.object_id WHERE t.name LIKE 'automatizacion_inventarios_%' AND i.is_unique_constraint = 1;
SELECT @constraints_fk = COUNT(*) FROM sys.foreign_keys fk WHERE OBJECT_NAME(fk.parent_object_id) LIKE 'automatizacion_inventarios_%';

PRINT '';
PRINT '   Tablas creadas:        ' + CAST(@tablas_creadas AS VARCHAR) + ' de 6 esperadas';
PRINT '   Índices creados:       ' + CAST(@indices_creados AS VARCHAR);
PRINT '   Constraints CHECK:     ' + CAST(@constraints_check AS VARCHAR);
PRINT '   Constraints UNIQUE:    ' + CAST(@constraints_unique AS VARCHAR) + ' (esperadas: 2)';
PRINT '   Constraints FK:        ' + CAST(@constraints_fk AS VARCHAR) + ' (esperada: 1)';
PRINT '';

IF @tablas_creadas = 6 AND @constraints_unique >= 2 AND @constraints_fk >= 1
BEGIN
    PRINT '   ════════════════════════════════════════════════════════════════';
    PRINT '   ✓ VALIDACIÓN EXITOSA - Fase 0 instalada correctamente';
    PRINT '   ════════════════════════════════════════════════════════════════';
END
ELSE
BEGIN
    PRINT '   ════════════════════════════════════════════════════════════════';
    PRINT '   ✗ VALIDACIÓN FALLIDA - Revisar errores arriba';
    PRINT '   ════════════════════════════════════════════════════════════════';
END

PRINT '';
GO


-- =============================================================================
-- SECCIÓN 3: SCRIPT DE ROLLBACK
-- =============================================================================
-- USAR SOLO SI ES NECESARIO REVERTIR LA INSTALACIÓN DE FASE 0
-- Ejecutar en orden inverso para respetar las foreign keys
-- =============================================================================

/*
-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║                           ⚠️  ROLLBACK  ⚠️                                ║
-- ║                                                                           ║
-- ║  Descomenta y ejecuta este bloque SOLO si necesitas revertir Fase 0      ║
-- ║  Esto eliminará TODAS las tablas y sus datos permanentemente             ║
-- ║                                                                           ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

PRINT '=============================================================================';
PRINT 'ROLLBACK - Eliminando tablas de Fase 0';
PRINT '=============================================================================';
PRINT '';

-- Orden inverso por dependencias FK
PRINT 'Eliminando tabla 5: automatizacion_inventarios_envios...';
DROP TABLE IF EXISTS [dbo].[automatizacion_inventarios_envios];
PRINT '   ✓ Eliminada';

PRINT 'Eliminando tabla 4: automatizacion_inventarios_ejecuciones...';
DROP TABLE IF EXISTS [dbo].[automatizacion_inventarios_ejecuciones];
PRINT '   ✓ Eliminada';

PRINT 'Eliminando tabla 3: automatizacion_inventarios_folios_procesados...';
DROP TABLE IF EXISTS [dbo].[automatizacion_inventarios_folios_procesados];
PRINT '   ✓ Eliminada';

PRINT 'Eliminando tabla 2: automatizacion_inventarios_destinatarios...';
DROP TABLE IF EXISTS [dbo].[automatizacion_inventarios_destinatarios];
PRINT '   ✓ Eliminada';

PRINT 'Eliminando tabla 6: automatizacion_inventarios_ultimo_folio_conocido...';
DROP TABLE IF EXISTS [dbo].[automatizacion_inventarios_ultimo_folio_conocido];
PRINT '   ✓ Eliminada';

PRINT 'Eliminando tabla 1: automatizacion_inventarios_config...';
DROP TABLE IF EXISTS [dbo].[automatizacion_inventarios_config];
PRINT '   ✓ Eliminada';

PRINT '';
PRINT '=============================================================================';
PRINT 'ROLLBACK COMPLETADO - Fase 0 eliminada';
PRINT '=============================================================================';

*/


-- =============================================================================
-- FIN DEL SCRIPT DDL - FASE 0
-- =============================================================================
