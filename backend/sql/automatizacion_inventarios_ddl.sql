-- =============================================================================
-- DDL: Automatización de Análisis de Inventarios
-- CAB-003 - Fase 0: Infraestructura Base
-- =============================================================================
-- 
-- FUENTE MAESTRA DE VERDAD PARA ESTRUCTURA DE TABLAS
-- Cualquier cambio de estructura debe hacerse primero aquí.
-- 
-- Base de datos destino: EDARSA HUB (SQL Server)
-- Fecha: Diciembre 2025
-- Estado: Fase 0 - Infraestructura desacoplada
-- 
-- NOTAS:
-- - Todas las tablas incluyen campos de auditoría estándar
-- - Feature flags controlan activación (todo apagado por defecto)
-- - Estas tablas NO afectan sistemas origen (SOFT/MPRO)
-- - Rollback: DROP en orden inverso al de creación
-- =============================================================================


-- =============================================================================
-- TABLA 1: automatizacion_inventarios_config
-- Propósito: Configuración general por servidor/sucursal/almacén
-- =============================================================================

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[automatizacion_inventarios_config]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[automatizacion_inventarios_config] (
        -- Identificador
        [config_id]             UNIQUEIDENTIFIER    NOT NULL    DEFAULT NEWID(),
        
        -- Jerarquía de aplicación
        [server_id]             NVARCHAR(50)        NOT NULL,
        [sucursal_id]           NVARCHAR(20)        NULL,       -- NULL = aplica a todo el server
        [almacen_id]            NVARCHAR(20)        NULL,       -- NULL = aplica a toda la sucursal
        
        -- Configuración de ejecución
        [intervalo_minutos]     INT                 NOT NULL    DEFAULT 15,
        [hora_inicio]           TIME                NULL,       -- Ventana de operación inicio
        [hora_fin]              TIME                NULL,       -- Ventana de operación fin
        
        -- Feature flag por registro
        [activo]                BIT                 NOT NULL    DEFAULT 0,  -- Apagado por defecto
        
        -- Campos de auditoría
        [created_at]            DATETIME            NOT NULL    DEFAULT GETUTCDATE(),
        [updated_at]            DATETIME            NULL,
        [created_by]            NVARCHAR(100)       NULL,
        [updated_by]            NVARCHAR(100)       NULL,
        
        -- Constraints
        CONSTRAINT [PK_automatizacion_config] PRIMARY KEY CLUSTERED ([config_id])
    );
    
    -- Índice para búsqueda por jerarquía
    CREATE NONCLUSTERED INDEX [IX_config_servidor] 
        ON [dbo].[automatizacion_inventarios_config] ([server_id], [sucursal_id], [almacen_id]);
    
    PRINT 'Tabla automatizacion_inventarios_config creada exitosamente.';
END
ELSE
BEGIN
    PRINT 'Tabla automatizacion_inventarios_config ya existe.';
END
GO


-- =============================================================================
-- TABLA 2: automatizacion_inventarios_destinatarios
-- Propósito: Emails/WhatsApp destino por nivel jerárquico
-- =============================================================================

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[automatizacion_inventarios_destinatarios]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[automatizacion_inventarios_destinatarios] (
        -- Identificador
        [destinatario_id]       UNIQUEIDENTIFIER    NOT NULL    DEFAULT NEWID(),
        
        -- Jerarquía de aplicación
        [server_id]             NVARCHAR(50)        NOT NULL,
        [sucursal_id]           NVARCHAR(20)        NULL,       -- NULL = nivel servidor
        [almacen_id]            NVARCHAR(20)        NULL,       -- NULL = nivel sucursal
        [nivel_origen]          NVARCHAR(20)        NOT NULL,   -- 'SERVER' / 'SUCURSAL' / 'ALMACEN'
        
        -- Canal y tipo
        [canal]                 NVARCHAR(20)        NOT NULL    DEFAULT 'EMAIL',  -- 'EMAIL' / 'WHATSAPP' / 'AMBOS'
        [tipo_destinatario]     NVARCHAR(10)        NOT NULL    DEFAULT 'TO',     -- 'TO' / 'CC' / 'BCC'
        
        -- Datos de contacto
        [email]                 NVARCHAR(255)       NULL,
        [telefono]              NVARCHAR(20)        NULL,       -- Para WhatsApp (Fase 2)
        [nombre_contacto]       NVARCHAR(100)       NULL,
        
        -- Estado
        [activo]                BIT                 NOT NULL    DEFAULT 1,
        
        -- Campos de auditoría
        [created_at]            DATETIME            NOT NULL    DEFAULT GETUTCDATE(),
        [updated_at]            DATETIME            NULL,
        [created_by]            NVARCHAR(100)       NULL,
        [updated_by]            NVARCHAR(100)       NULL,
        
        -- Constraints
        CONSTRAINT [PK_automatizacion_destinatarios] PRIMARY KEY CLUSTERED ([destinatario_id]),
        CONSTRAINT [CK_destinatarios_nivel] CHECK ([nivel_origen] IN ('SERVER', 'SUCURSAL', 'ALMACEN')),
        CONSTRAINT [CK_destinatarios_canal] CHECK ([canal] IN ('EMAIL', 'WHATSAPP', 'AMBOS')),
        CONSTRAINT [CK_destinatarios_tipo] CHECK ([tipo_destinatario] IN ('TO', 'CC', 'BCC'))
    );
    
    -- Índice para búsqueda por jerarquía y canal
    CREATE NONCLUSTERED INDEX [IX_destinatarios_jerarquia] 
        ON [dbo].[automatizacion_inventarios_destinatarios] ([server_id], [sucursal_id], [almacen_id], [canal], [activo]);
    
    PRINT 'Tabla automatizacion_inventarios_destinatarios creada exitosamente.';
END
ELSE
BEGIN
    PRINT 'Tabla automatizacion_inventarios_destinatarios ya existe.';
END
GO


-- =============================================================================
-- TABLA 3: automatizacion_inventarios_folios_procesados
-- Propósito: Control de duplicados y lock con clave única de 6 componentes
-- =============================================================================

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[automatizacion_inventarios_folios_procesados]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[automatizacion_inventarios_folios_procesados] (
        -- Identificador (referenciable desde Fase 1.5: tareas, diferencias)
        [procesado_id]          UNIQUEIDENTIFIER    NOT NULL    DEFAULT NEWID(),
        
        -- CLAVE ÚNICA DE 6 COMPONENTES (aprobada en consolidación)
        [sistema_origen]        NVARCHAR(20)        NOT NULL,   -- 'SOFTRESTAURANT' / 'MPRO'
        [server_id]             NVARCHAR(50)        NOT NULL,
        [sucursal_id]           NVARCHAR(20)        NOT NULL,
        [almacen_id]            NVARCHAR(20)        NOT NULL,
        [folio_inventario]      NVARCHAR(50)        NOT NULL,
        [fecha_inventario]      DATE                NOT NULL,
        
        -- Hash de verificación (SHA256)
        [hash_verificacion]     NVARCHAR(64)        NOT NULL,
        
        -- Estado y control de concurrencia
        [estado]                NVARCHAR(20)        NOT NULL    DEFAULT 'EN_PROCESO',  -- 'EN_PROCESO' / 'EXITOSO' / 'ERROR'
        [heartbeat_at]          DATETIME            NULL,       -- Último heartbeat del lock
        
        -- Resultado del procesamiento
        [fecha_procesado]       DATETIME            NULL,       -- Cuándo se completó
        [error_detalle]         NVARCHAR(MAX)       NULL,       -- Detalle si hubo error
        [ruta_archivo_excel]    NVARCHAR(500)       NULL,       -- Path del Excel generado
        
        -- Campos de auditoría
        [created_at]            DATETIME            NOT NULL    DEFAULT GETUTCDATE(),
        [updated_at]            DATETIME            NULL,
        [created_by]            NVARCHAR(100)       NULL,
        [updated_by]            NVARCHAR(100)       NULL,
        
        -- Constraints
        CONSTRAINT [PK_automatizacion_folios] PRIMARY KEY CLUSTERED ([procesado_id]),
        CONSTRAINT [CK_folios_sistema] CHECK ([sistema_origen] IN ('SOFTRESTAURANT', 'MPRO')),
        CONSTRAINT [CK_folios_estado] CHECK ([estado] IN ('EN_PROCESO', 'EXITOSO', 'ERROR')),
        
        -- CONSTRAINT UNIQUE EXPLÍCITO: Clave de 6 componentes aprobada
        CONSTRAINT [UQ_folios_clave_unica] UNIQUE (
            [sistema_origen],
            [server_id],
            [sucursal_id],
            [almacen_id],
            [folio_inventario],
            [fecha_inventario]
        )
    );
    
    -- Índice para búsqueda por hash (verificación rápida de duplicados)
    CREATE NONCLUSTERED INDEX [IX_folios_hash] 
        ON [dbo].[automatizacion_inventarios_folios_procesados] ([hash_verificacion]);
    
    -- Índice para búsqueda por estado y heartbeat (limpieza de locks huérfanos)
    CREATE NONCLUSTERED INDEX [IX_folios_estado_heartbeat] 
        ON [dbo].[automatizacion_inventarios_folios_procesados] ([estado], [heartbeat_at])
        WHERE [estado] = 'EN_PROCESO';
    
    PRINT 'Tabla automatizacion_inventarios_folios_procesados creada exitosamente.';
END
ELSE
BEGIN
    PRINT 'Tabla automatizacion_inventarios_folios_procesados ya existe.';
END
GO


-- =============================================================================
-- TABLA 4: automatizacion_inventarios_ejecuciones
-- Propósito: Bitácora de cada ciclo del scheduler
-- =============================================================================

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[automatizacion_inventarios_ejecuciones]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[automatizacion_inventarios_ejecuciones] (
        -- Identificador
        [ejecucion_id]          UNIQUEIDENTIFIER    NOT NULL    DEFAULT NEWID(),
        
        -- Tiempos de ejecución
        [fecha_inicio]          DATETIME            NOT NULL,
        [fecha_fin]             DATETIME            NULL,
        
        -- Estado y métricas
        [estado]                NVARCHAR(20)        NOT NULL    DEFAULT 'INICIADO',  -- 'INICIADO' / 'COMPLETADO' / 'ERROR'
        [servidores_escaneados] INT                 NULL,
        [folios_detectados]     INT                 NULL,
        [folios_procesados]     INT                 NULL,
        [folios_error]          INT                 NULL,
        [detalle_errores]       NVARCHAR(MAX)       NULL,       -- JSON con errores
        
        -- Campos de auditoría
        [created_at]            DATETIME            NOT NULL    DEFAULT GETUTCDATE(),
        [updated_at]            DATETIME            NULL,
        
        -- Constraints
        CONSTRAINT [PK_automatizacion_ejecuciones] PRIMARY KEY CLUSTERED ([ejecucion_id]),
        CONSTRAINT [CK_ejecuciones_estado] CHECK ([estado] IN ('INICIADO', 'COMPLETADO', 'ERROR'))
    );
    
    -- Índice para búsqueda por fecha (consulta de historial)
    CREATE NONCLUSTERED INDEX [IX_ejecuciones_fecha] 
        ON [dbo].[automatizacion_inventarios_ejecuciones] ([fecha_inicio] DESC);
    
    PRINT 'Tabla automatizacion_inventarios_ejecuciones creada exitosamente.';
END
ELSE
BEGIN
    PRINT 'Tabla automatizacion_inventarios_ejecuciones ya existe.';
END
GO


-- =============================================================================
-- TABLA 5: automatizacion_inventarios_envios
-- Propósito: Registro de cada email/WhatsApp enviado
-- =============================================================================

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[automatizacion_inventarios_envios]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[automatizacion_inventarios_envios] (
        -- Identificador
        [envio_id]              UNIQUEIDENTIFIER    NOT NULL    DEFAULT NEWID(),
        
        -- Relación con folio procesado
        [procesado_id]          UNIQUEIDENTIFIER    NOT NULL,
        
        -- Destinatario y canal
        [destinatario_email]    NVARCHAR(255)       NOT NULL,
        [canal]                 NVARCHAR(20)        NOT NULL    DEFAULT 'EMAIL',  -- 'EMAIL' / 'WHATSAPP'
        [tipo_destinatario]     NVARCHAR(10)        NOT NULL,   -- 'TO' / 'CC' / 'BCC'
        
        -- Estado del envío
        [fecha_envio]           DATETIME            NULL,       -- Cuándo se envió
        [estado]                NVARCHAR(20)        NOT NULL    DEFAULT 'PENDIENTE',  -- 'PENDIENTE' / 'ENVIADO' / 'ERROR'
        [intentos]              INT                 NOT NULL    DEFAULT 0,
        [error_detalle]         NVARCHAR(MAX)       NULL,
        
        -- Campos de auditoría
        [created_at]            DATETIME            NOT NULL    DEFAULT GETUTCDATE(),
        [updated_at]            DATETIME            NULL,
        
        -- Constraints
        CONSTRAINT [PK_automatizacion_envios] PRIMARY KEY CLUSTERED ([envio_id]),
        CONSTRAINT [FK_envios_procesado] FOREIGN KEY ([procesado_id]) 
            REFERENCES [dbo].[automatizacion_inventarios_folios_procesados] ([procesado_id]),
        CONSTRAINT [CK_envios_canal] CHECK ([canal] IN ('EMAIL', 'WHATSAPP')),
        CONSTRAINT [CK_envios_tipo] CHECK ([tipo_destinatario] IN ('TO', 'CC', 'BCC')),
        CONSTRAINT [CK_envios_estado] CHECK ([estado] IN ('PENDIENTE', 'ENVIADO', 'ERROR'))
    );
    
    -- Índice para búsqueda por folio procesado
    CREATE NONCLUSTERED INDEX [IX_envios_procesado] 
        ON [dbo].[automatizacion_inventarios_envios] ([procesado_id]);
    
    -- Índice para reenvíos pendientes
    CREATE NONCLUSTERED INDEX [IX_envios_pendientes] 
        ON [dbo].[automatizacion_inventarios_envios] ([estado], [intentos])
        WHERE [estado] IN ('PENDIENTE', 'ERROR');
    
    PRINT 'Tabla automatizacion_inventarios_envios creada exitosamente.';
END
ELSE
BEGIN
    PRINT 'Tabla automatizacion_inventarios_envios ya existe.';
END
GO


-- =============================================================================
-- TABLA 6: automatizacion_inventarios_ultimo_folio_conocido
-- Propósito: Marca de agua para detección incremental por almacén
-- =============================================================================

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[automatizacion_inventarios_ultimo_folio_conocido]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[automatizacion_inventarios_ultimo_folio_conocido] (
        -- Identificador
        [id]                    UNIQUEIDENTIFIER    NOT NULL    DEFAULT NEWID(),
        
        -- Clave única por almacén y sistema
        [sistema_origen]        NVARCHAR(20)        NOT NULL,   -- 'SOFTRESTAURANT' / 'MPRO'
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
        
        -- Constraints
        CONSTRAINT [PK_automatizacion_ultimo_folio] PRIMARY KEY CLUSTERED ([id]),
        CONSTRAINT [CK_ultimo_folio_sistema] CHECK ([sistema_origen] IN ('SOFTRESTAURANT', 'MPRO')),
        
        -- CONSTRAINT UNIQUE: Un registro por almacén/sistema
        CONSTRAINT [UQ_ultimo_folio_clave] UNIQUE (
            [sistema_origen],
            [server_id],
            [sucursal_id],
            [almacen_id]
        )
    );
    
    -- Índice para búsqueda por servidor
    CREATE NONCLUSTERED INDEX [IX_ultimo_folio_servidor] 
        ON [dbo].[automatizacion_inventarios_ultimo_folio_conocido] ([server_id], [sistema_origen]);
    
    PRINT 'Tabla automatizacion_inventarios_ultimo_folio_conocido creada exitosamente.';
END
ELSE
BEGIN
    PRINT 'Tabla automatizacion_inventarios_ultimo_folio_conocido ya existe.';
END
GO


-- =============================================================================
-- SCRIPT DE ROLLBACK (para referencia)
-- =============================================================================
/*
-- Ejecutar en orden inverso para rollback completo de Fase 0:

DROP TABLE IF EXISTS [dbo].[automatizacion_inventarios_envios];
DROP TABLE IF EXISTS [dbo].[automatizacion_inventarios_ejecuciones];
DROP TABLE IF EXISTS [dbo].[automatizacion_inventarios_folios_procesados];
DROP TABLE IF EXISTS [dbo].[automatizacion_inventarios_destinatarios];
DROP TABLE IF EXISTS [dbo].[automatizacion_inventarios_ultimo_folio_conocido];
DROP TABLE IF EXISTS [dbo].[automatizacion_inventarios_config];

PRINT 'Rollback Fase 0 completado.';
*/


-- =============================================================================
-- FIN DEL SCRIPT DDL - FASE 0
-- =============================================================================
PRINT '';
PRINT '=============================================================================';
PRINT 'DDL Fase 0 - Automatización de Inventarios';
PRINT 'Total de tablas: 6';
PRINT 'Estado: Infraestructura creada, feature flags apagados';
PRINT '=============================================================================';
GO
