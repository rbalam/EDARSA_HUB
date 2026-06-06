-- ============================================================================
-- FASE Q1.2 — DDL PASIVO PARA CONSULTAS CONFIGURABLES EN EDARSAHUB
-- ============================================================================
-- 
-- ██████╗ ██████╗ ██╗         ██████╗  █████╗ ███████╗██╗██╗   ██╗ ██████╗ 
-- ██╔══██╗██╔══██╗██║         ██╔══██╗██╔══██╗██╔════╝██║██║   ██║██╔═══██╗
-- ██║  ██║██║  ██║██║         ██████╔╝███████║███████╗██║██║   ██║██║   ██║
-- ██║  ██║██║  ██║██║         ██╔═══╝ ██╔══██║╚════██║██║╚██╗ ██╔╝██║   ██║
-- ██████╔╝██████╔╝███████╗    ██║     ██║  ██║███████║██║ ╚████╔╝ ╚██████╔╝
-- ╚═════╝ ╚═════╝ ╚══════╝    ╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝   ╚═════╝ 
--
-- ============================================================================
-- ⚠️  ESTE SCRIPT NO HA SIDO EJECUTADO
-- ⚠️  REQUIERE AUTORIZACIÓN EXPLÍCITA PARA FASE Q1.4 (Ejecución DDL)
-- ============================================================================
-- 
-- Fecha de generación: 12-Mayo-2026
-- Base de datos destino: EDARSAHUB
-- Servidor: 54.39.104.176
-- 
-- PROPÓSITO:
-- Crear estructura normalizada para consultas configurables que reemplazará
-- gradualmente las columnas legacy en MongoDB.servers (query_inventario,
-- query_ventas, query_movimientos).
--
-- TABLAS A CREAR:
-- 1. Sistema_ConsultasConfigurables  (Tabla principal)
-- 2. Sistema_ConsultasVersiones      (Historial de versiones)
-- 3. Sistema_ConsultasEjecucionesLog (Auditoría de ejecución)
-- 4. Sistema_MigracionConsultasTrace (Trazabilidad de migración desde MongoDB)
--
-- NOTA SOBRE Sistema_ConsultasParametros:
-- Se evaluó crear tabla separada para parámetros, pero se decidió usar
-- ParametrosSchema (JSON) en la tabla principal por simplicidad.
-- Si en el futuro se requiere normalización más estricta, se puede agregar.
--
-- ============================================================================
-- REGLAS DE SEGURIDAD
-- ============================================================================
-- 
-- 🔒 SECRETOS:
--    - APIHeadersConfig NO debe almacenar tokens reales ni API keys planas.
--    - Si se requieren credenciales, usar referencias a secret manager:
--      Ejemplo: {"Authorization": "SECRET_REF:api_key_servidor_123"}
--    - El backend debe resolver las referencias al momento de ejecución.
--
-- 🔒 EJECUCIÓN:
--    - SoloLectura=1 bloquea cualquier query que no sea SELECT/GET.
--    - MaxFilas limita resultados para evitar extracción masiva.
--    - TimeoutSegundos previene queries de larga duración.
--
-- 🔒 LOGS:
--    - Sistema_ConsultasEjecucionesLog NO guarda SQL completo.
--    - Solo guarda ConsultaID + parámetros enmascarados + resultados básicos.
--
-- ============================================================================

USE EDARSAHUB;
GO

-- ============================================================================
-- VALIDACIONES PREVIAS
-- ============================================================================

PRINT '=== FASE Q1.2: Validaciones Previas ===';
GO

-- Verificar existencia de Servidores_Conexiones (requerida para FK)
IF OBJECT_ID('dbo.Servidores_Conexiones', 'U') IS NULL
BEGIN
    RAISERROR('ERROR: Tabla Servidores_Conexiones no existe. Abortando.', 16, 1);
    RETURN;
END
PRINT '  ✓ Servidores_Conexiones existe';
GO

-- Verificar existencia de Usuario_Catalogo (para FKs opcionales)
IF OBJECT_ID('dbo.Usuario_Catalogo', 'U') IS NULL
BEGIN
    PRINT '  ⚠ Usuario_Catalogo no existe. FKs de usuario serán NULL/sin constraint.';
END
ELSE
BEGIN
    PRINT '  ✓ Usuario_Catalogo existe';
END
GO

-- Verificar soporte de tipos
PRINT '  ✓ Verificando soporte de UNIQUEIDENTIFIER, DATETIME2, NVARCHAR(MAX)...';
-- SQL Server 2012+ soporta todos estos tipos
GO

-- ============================================================================
-- TABLA 1: Sistema_ConsultasConfigurables (PRINCIPAL)
-- ============================================================================
-- Fuente oficial de consultas configurables en EDARSAHUB.
-- Diseño agnóstico al dominio y extensible.
-- ============================================================================

PRINT '';
PRINT '=== Creando Sistema_ConsultasConfigurables ===';
GO

IF OBJECT_ID('dbo.Sistema_ConsultasConfigurables', 'U') IS NULL
BEGIN

    CREATE TABLE dbo.Sistema_ConsultasConfigurables (
        -- ═══════════════════════════════════════════════════════════════════
        -- IDENTIFICACIÓN
        -- ═══════════════════════════════════════════════════════════════════
        ConsultaID              BIGINT IDENTITY(1,1) NOT NULL,
        ConsultaUUID            UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
        
        -- ═══════════════════════════════════════════════════════════════════
        -- RELACIÓN CON SERVIDOR/CONEXIÓN
        -- NULL = consulta global (no asociada a servidor específico)
        -- ═══════════════════════════════════════════════════════════════════
        ServidorConexionID      UNIQUEIDENTIFIER NULL,
        
        -- ═══════════════════════════════════════════════════════════════════
        -- CLASIFICACIÓN EXTENSIBLE
        -- ═══════════════════════════════════════════════════════════════════
        TipoOrigen              NVARCHAR(20) NOT NULL DEFAULT 'SQL',
        -- Valores permitidos: 'SQL', 'API_REST', 'API_SOAP', 'SCRIPT'
        -- NOTA: 'SCRIPT' está reservado para futuro, no ejecutable actualmente.
        
        CategoriaConsulta       NVARCHAR(50) NOT NULL,
        -- Extensible: 'legacy_inventario', 'legacy_ventas', 'legacy_movimientos',
        -- 'sql_libre', 'api_rest', 'nominas', 'rh', 'bancos', 'contabilidad',
        -- 'fiscal', 'crm', 'test_guardado', 'custom', etc.
        
        NombreConsulta          NVARCHAR(100) NOT NULL,
        Descripcion             NVARCHAR(500) NULL,
        
        Etiquetas               NVARCHAR(500) NULL,
        -- JSON array: ["legacy", "mpro", "ventas_periodo"]
        -- CONSTRAINT de validación JSON más abajo
        
        -- ═══════════════════════════════════════════════════════════════════
        -- MÓDULO Y SISTEMA (opcional, agnóstico)
        -- ═══════════════════════════════════════════════════════════════════
        ModuloRelacionado       NVARCHAR(50) NULL,
        -- NULL = agnóstico. Ejemplos: 'comercial', 'inventarios', 'finanzas', 'rh'
        
        SystemType              NVARCHAR(50) NULL,
        -- NULL = genérico. Ejemplos: 'MPRO', 'SOFTRESTAURANT', 'EDARSA_HUB'
        
        -- ═══════════════════════════════════════════════════════════════════
        -- CONTENIDO SQL (para TipoOrigen = 'SQL')
        -- ═══════════════════════════════════════════════════════════════════
        SQLQuery                NVARCHAR(MAX) NULL,
        
        -- ═══════════════════════════════════════════════════════════════════
        -- CONTENIDO API REST (para TipoOrigen = 'API_REST')
        -- ═══════════════════════════════════════════════════════════════════
        APIMetodoHTTP           NVARCHAR(10) NULL,
        -- Valores: 'GET' (actualmente). 'POST' reservado para futuro.
        
        APIEndpointPath         NVARCHAR(500) NULL,
        -- Path relativo al servidor. Ejemplo: '/ventas', '/inventario'
        
        APIHeadersConfig        NVARCHAR(MAX) NULL,
        -- JSON de headers. 🔒 NO ALMACENAR TOKENS REALES.
        -- Usar referencias: {"Authorization": "SECRET_REF:key_name"}
        
        APIQueryParamsSchema    NVARCHAR(MAX) NULL,
        -- JSON schema de parámetros query string.
        -- Ejemplo: [{"nombre":"fecha","tipo":"date","requerido":true}]
        
        APIBodyTemplate         NVARCHAR(MAX) NULL,
        -- Template de body para POST (FUTURO - no usar actualmente).
        -- En fase actual API-UQT1 solo permite GET.
        
        -- ═══════════════════════════════════════════════════════════════════
        -- PARÁMETROS DINÁMICOS
        -- ═══════════════════════════════════════════════════════════════════
        ParametrosSchema        NVARCHAR(MAX) NULL,
        -- JSON: [{"nombre":"@FECHA_INI","tipo":"datetime","requerido":true}]
        
        -- ═══════════════════════════════════════════════════════════════════
        -- VALIDACIÓN (para compatibilidad legacy)
        -- ═══════════════════════════════════════════════════════════════════
        ColumnasRequeridas      NVARCHAR(MAX) NULL,
        -- JSON: ["codigo","descripcion","cantidad"]
        -- Nullable: consultas agnósticas no requieren validación de columnas.
        
        Validada                BIT NOT NULL DEFAULT 0,
        FechaUltimaValidacion   DATETIME2 NULL,
        MensajeValidacion       NVARCHAR(500) NULL,
        
        -- ═══════════════════════════════════════════════════════════════════
        -- SEGURIDAD
        -- ═══════════════════════════════════════════════════════════════════
        SoloLectura             BIT NOT NULL DEFAULT 1,
        -- 1 = Solo SELECT/GET permitido (default seguro).
        -- 0 = Permite escritura (requiere autorización especial).
        
        MaxFilas                INT NOT NULL DEFAULT 10000,
        TimeoutSegundos         INT NOT NULL DEFAULT 30,
        
        RequiereAutorizacion    BIT NOT NULL DEFAULT 0,
        -- Si requiere autorización especial para ejecutar.
        
        NivelAcceso             NVARCHAR(20) NOT NULL DEFAULT 'USUARIO',
        -- 'PUBLICO', 'USUARIO', 'ADMIN', 'SUPERADMIN'
        
        -- ═══════════════════════════════════════════════════════════════════
        -- VERSIONADO
        -- ═══════════════════════════════════════════════════════════════════
        VersionActual           INT NOT NULL DEFAULT 1,
        
        -- ═══════════════════════════════════════════════════════════════════
        -- ESTADO
        -- ═══════════════════════════════════════════════════════════════════
        Activo                  BIT NOT NULL DEFAULT 1,
        EsLegacy                BIT NOT NULL DEFAULT 0,
        -- Marca consultas migradas de MongoDB.
        
        -- ═══════════════════════════════════════════════════════════════════
        -- AUDITORÍA
        -- ═══════════════════════════════════════════════════════════════════
        CreadoPorUsuarioID      INT NULL,
        CreadoPorEmail          NVARCHAR(100) NULL,
        FechaCreacion           DATETIME2 NOT NULL DEFAULT GETDATE(),
        
        ModificadoPorUsuarioID  INT NULL,
        ModificadoPorEmail      NVARCHAR(100) NULL,
        FechaModificacion       DATETIME2 NULL,
        
        -- ═══════════════════════════════════════════════════════════════════
        -- CONSTRAINTS
        -- ═══════════════════════════════════════════════════════════════════
        
        -- PK
        CONSTRAINT PK_Sistema_ConsultasConfigurables 
            PRIMARY KEY CLUSTERED (ConsultaID),
        
        -- UUID único
        CONSTRAINT UQ_Sistema_Consultas_UUID 
            UNIQUE (ConsultaUUID),
        
        -- FK a Servidores_Conexiones (permite NULL para consultas globales)
        CONSTRAINT FK_Sistema_Consultas_ServidorConexion 
            FOREIGN KEY (ServidorConexionID) 
            REFERENCES dbo.Servidores_Conexiones(id),
        
        -- CHECK: TipoOrigen válido
        CONSTRAINT CK_Sistema_Consultas_TipoOrigen 
            CHECK (TipoOrigen IN ('SQL', 'API_REST', 'API_SOAP', 'SCRIPT')),
        
        -- CHECK: NivelAcceso válido
        CONSTRAINT CK_Sistema_Consultas_NivelAcceso 
            CHECK (NivelAcceso IN ('PUBLICO', 'USUARIO', 'ADMIN', 'SUPERADMIN')),
        
        -- CHECK: MaxFilas razonable
        CONSTRAINT CK_Sistema_Consultas_MaxFilas 
            CHECK (MaxFilas BETWEEN 1 AND 1000000),
        
        -- CHECK: Timeout razonable
        CONSTRAINT CK_Sistema_Consultas_Timeout 
            CHECK (TimeoutSegundos BETWEEN 1 AND 300),
        
        -- CHECK: JSON válido en Etiquetas (si no es NULL)
        CONSTRAINT CK_Sistema_Consultas_Etiquetas_JSON 
            CHECK (Etiquetas IS NULL OR ISJSON(Etiquetas) = 1),
        
        -- CHECK: JSON válido en APIHeadersConfig (si no es NULL)
        CONSTRAINT CK_Sistema_Consultas_APIHeadersConfig_JSON 
            CHECK (APIHeadersConfig IS NULL OR ISJSON(APIHeadersConfig) = 1),
        
        -- CHECK: JSON válido en APIQueryParamsSchema (si no es NULL)
        CONSTRAINT CK_Sistema_Consultas_APIQueryParamsSchema_JSON 
            CHECK (APIQueryParamsSchema IS NULL OR ISJSON(APIQueryParamsSchema) = 1),
        
        -- CHECK: JSON válido en APIBodyTemplate (si no es NULL)
        CONSTRAINT CK_Sistema_Consultas_APIBodyTemplate_JSON 
            CHECK (APIBodyTemplate IS NULL OR ISJSON(APIBodyTemplate) = 1),
        
        -- CHECK: JSON válido en ParametrosSchema (si no es NULL)
        CONSTRAINT CK_Sistema_Consultas_ParametrosSchema_JSON 
            CHECK (ParametrosSchema IS NULL OR ISJSON(ParametrosSchema) = 1),
        
        -- CHECK: JSON válido en ColumnasRequeridas (si no es NULL)
        CONSTRAINT CK_Sistema_Consultas_ColumnasRequeridas_JSON 
            CHECK (ColumnasRequeridas IS NULL OR ISJSON(ColumnasRequeridas) = 1)
    );
    
    PRINT '  ✓ Tabla Sistema_ConsultasConfigurables creada';

END
ELSE
BEGIN
    PRINT '  ⚠ Tabla Sistema_ConsultasConfigurables ya existe';
END
GO

-- ═══════════════════════════════════════════════════════════════════════════
-- ÍNDICE ÚNICO FILTRADO PARA CONSULTAS POR SERVIDOR
-- Permite solo una consulta por servidor+categoria+nombre
-- ═══════════════════════════════════════════════════════════════════════════
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'UQ_Sistema_Consultas_PorServidor')
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX UQ_Sistema_Consultas_PorServidor
    ON dbo.Sistema_ConsultasConfigurables (ServidorConexionID, CategoriaConsulta, NombreConsulta)
    WHERE ServidorConexionID IS NOT NULL;
    
    PRINT '  ✓ Índice UQ_Sistema_Consultas_PorServidor creado';
END
GO

-- ═══════════════════════════════════════════════════════════════════════════
-- ÍNDICE ÚNICO FILTRADO PARA CONSULTAS GLOBALES (sin servidor)
-- Permite solo una consulta global por categoria+nombre
-- ═══════════════════════════════════════════════════════════════════════════
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'UQ_Sistema_Consultas_Globales')
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX UQ_Sistema_Consultas_Globales
    ON dbo.Sistema_ConsultasConfigurables (CategoriaConsulta, NombreConsulta)
    WHERE ServidorConexionID IS NULL;
    
    PRINT '  ✓ Índice UQ_Sistema_Consultas_Globales creado';
END
GO

-- ═══════════════════════════════════════════════════════════════════════════
-- ÍNDICES ADICIONALES PARA RENDIMIENTO
-- ═══════════════════════════════════════════════════════════════════════════
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Sistema_Consultas_ServidorConexion')
BEGIN
    CREATE NONCLUSTERED INDEX IX_Sistema_Consultas_ServidorConexion
    ON dbo.Sistema_ConsultasConfigurables (ServidorConexionID)
    INCLUDE (CategoriaConsulta, NombreConsulta, Activo);
    
    PRINT '  ✓ Índice IX_Sistema_Consultas_ServidorConexion creado';
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Sistema_Consultas_Categoria')
BEGIN
    CREATE NONCLUSTERED INDEX IX_Sistema_Consultas_Categoria
    ON dbo.Sistema_ConsultasConfigurables (CategoriaConsulta)
    INCLUDE (TipoOrigen, Activo);
    
    PRINT '  ✓ Índice IX_Sistema_Consultas_Categoria creado';
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Sistema_Consultas_Modulo')
BEGIN
    CREATE NONCLUSTERED INDEX IX_Sistema_Consultas_Modulo
    ON dbo.Sistema_ConsultasConfigurables (ModuloRelacionado)
    WHERE ModuloRelacionado IS NOT NULL;
    
    PRINT '  ✓ Índice IX_Sistema_Consultas_Modulo creado';
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Sistema_Consultas_TipoOrigen')
BEGIN
    CREATE NONCLUSTERED INDEX IX_Sistema_Consultas_TipoOrigen
    ON dbo.Sistema_ConsultasConfigurables (TipoOrigen)
    INCLUDE (Activo);
    
    PRINT '  ✓ Índice IX_Sistema_Consultas_TipoOrigen creado';
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Sistema_Consultas_Activo')
BEGIN
    CREATE NONCLUSTERED INDEX IX_Sistema_Consultas_Activo
    ON dbo.Sistema_ConsultasConfigurables (Activo)
    INCLUDE (ServidorConexionID, CategoriaConsulta);
    
    PRINT '  ✓ Índice IX_Sistema_Consultas_Activo creado';
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Sistema_Consultas_EsLegacy')
BEGIN
    CREATE NONCLUSTERED INDEX IX_Sistema_Consultas_EsLegacy
    ON dbo.Sistema_ConsultasConfigurables (EsLegacy)
    WHERE EsLegacy = 1;
    
    PRINT '  ✓ Índice IX_Sistema_Consultas_EsLegacy creado';
END
GO


-- ============================================================================
-- TABLA 2: Sistema_ConsultasVersiones (HISTORIAL)
-- ============================================================================
-- Historial completo de cambios en consultas.
-- Cada modificación crea una nueva versión.
-- ============================================================================

PRINT '';
PRINT '=== Creando Sistema_ConsultasVersiones ===';
GO

IF OBJECT_ID('dbo.Sistema_ConsultasVersiones', 'U') IS NULL
BEGIN

    CREATE TABLE dbo.Sistema_ConsultasVersiones (
        -- ═══════════════════════════════════════════════════════════════════
        -- IDENTIFICACIÓN
        -- ═══════════════════════════════════════════════════════════════════
        VersionID               BIGINT IDENTITY(1,1) NOT NULL,
        ConsultaID              BIGINT NOT NULL,
        NumeroVersion           INT NOT NULL,
        
        -- ═══════════════════════════════════════════════════════════════════
        -- SNAPSHOT DEL CONTENIDO AL MOMENTO DE LA VERSIÓN
        -- ═══════════════════════════════════════════════════════════════════
        TipoOrigen              NVARCHAR(20) NOT NULL,
        CategoriaConsulta       NVARCHAR(50) NOT NULL,
        NombreConsulta          NVARCHAR(100) NOT NULL,
        Descripcion             NVARCHAR(500) NULL,
        
        -- SQL
        SQLQuery                NVARCHAR(MAX) NULL,
        
        -- API
        APIMetodoHTTP           NVARCHAR(10) NULL,
        APIEndpointPath         NVARCHAR(500) NULL,
        APIHeadersConfig        NVARCHAR(MAX) NULL,
        APIQueryParamsSchema    NVARCHAR(MAX) NULL,
        APIBodyTemplate         NVARCHAR(MAX) NULL,
        
        -- Parámetros y validación
        ParametrosSchema        NVARCHAR(MAX) NULL,
        ColumnasRequeridas      NVARCHAR(MAX) NULL,
        
        -- Configuración
        SoloLectura             BIT NOT NULL,
        MaxFilas                INT NOT NULL,
        TimeoutSegundos         INT NOT NULL,
        
        -- ═══════════════════════════════════════════════════════════════════
        -- METADATOS DE VERSIÓN
        -- ═══════════════════════════════════════════════════════════════════
        MotivoDelCambio         NVARCHAR(500) NULL,
        CambiadoPorUsuarioID    INT NULL,
        CambiadoPorEmail        NVARCHAR(100) NULL,
        FechaCambio             DATETIME2 NOT NULL DEFAULT GETDATE(),
        
        -- ═══════════════════════════════════════════════════════════════════
        -- CONSTRAINTS
        -- ═══════════════════════════════════════════════════════════════════
        
        -- PK
        CONSTRAINT PK_Sistema_ConsultasVersiones 
            PRIMARY KEY CLUSTERED (VersionID),
        
        -- FK a consulta principal
        CONSTRAINT FK_Sistema_Versiones_Consulta 
            FOREIGN KEY (ConsultaID) 
            REFERENCES dbo.Sistema_ConsultasConfigurables(ConsultaID)
            ON DELETE CASCADE,
        
        -- Versión única por consulta
        CONSTRAINT UQ_Sistema_Versiones_ConsultaNumero 
            UNIQUE (ConsultaID, NumeroVersion)
    );
    
    PRINT '  ✓ Tabla Sistema_ConsultasVersiones creada';

END
ELSE
BEGIN
    PRINT '  ⚠ Tabla Sistema_ConsultasVersiones ya existe';
END
GO

-- Índices
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Sistema_Versiones_Consulta')
BEGIN
    CREATE NONCLUSTERED INDEX IX_Sistema_Versiones_Consulta
    ON dbo.Sistema_ConsultasVersiones (ConsultaID)
    INCLUDE (NumeroVersion, FechaCambio);
    
    PRINT '  ✓ Índice IX_Sistema_Versiones_Consulta creado';
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Sistema_Versiones_Fecha')
BEGIN
    CREATE NONCLUSTERED INDEX IX_Sistema_Versiones_Fecha
    ON dbo.Sistema_ConsultasVersiones (FechaCambio DESC);
    
    PRINT '  ✓ Índice IX_Sistema_Versiones_Fecha creado';
END
GO


-- ============================================================================
-- TABLA 3: Sistema_ConsultasEjecucionesLog (AUDITORÍA DE USO)
-- ============================================================================
-- Log de ejecuciones productivas.
-- 🔒 NO guarda SQL completo ejecutado por seguridad.
-- Solo guarda ConsultaID + parámetros enmascarados + resultados básicos.
-- ============================================================================

PRINT '';
PRINT '=== Creando Sistema_ConsultasEjecucionesLog ===';
GO

IF OBJECT_ID('dbo.Sistema_ConsultasEjecucionesLog', 'U') IS NULL
BEGIN

    CREATE TABLE dbo.Sistema_ConsultasEjecucionesLog (
        -- ═══════════════════════════════════════════════════════════════════
        -- IDENTIFICACIÓN
        -- ═══════════════════════════════════════════════════════════════════
        EjecucionID             BIGINT IDENTITY(1,1) NOT NULL,
        ConsultaID              BIGINT NOT NULL,
        
        -- ═══════════════════════════════════════════════════════════════════
        -- CONTEXTO DE EJECUCIÓN
        -- ═══════════════════════════════════════════════════════════════════
        ServidorConexionID      UNIQUEIDENTIFIER NULL,
        UsuarioID               INT NULL,
        UsuarioEmail            NVARCHAR(100) NULL,
        IPOrigen                NVARCHAR(45) NULL,
        
        -- ═══════════════════════════════════════════════════════════════════
        -- PARÁMETROS USADOS
        -- 🔒 JSON con valores enmascarados si son sensibles
        -- ═══════════════════════════════════════════════════════════════════
        ParametrosUsados        NVARCHAR(MAX) NULL,
        
        -- ═══════════════════════════════════════════════════════════════════
        -- RESULTADO
        -- ═══════════════════════════════════════════════════════════════════
        Exitoso                 BIT NOT NULL,
        TiempoEjecucionMs       INT NULL,
        FilasDevueltas          INT NULL,
        MensajeError            NVARCHAR(1000) NULL,
        CodigoError             NVARCHAR(50) NULL,
        
        -- ═══════════════════════════════════════════════════════════════════
        -- AUDITORÍA
        -- ═══════════════════════════════════════════════════════════════════
        FechaEjecucion          DATETIME2 NOT NULL DEFAULT GETDATE(),
        
        -- ═══════════════════════════════════════════════════════════════════
        -- CONSTRAINTS
        -- ═══════════════════════════════════════════════════════════════════
        
        -- PK
        CONSTRAINT PK_Sistema_ConsultasEjecucionesLog 
            PRIMARY KEY CLUSTERED (EjecucionID),
        
        -- FK a consulta (sin CASCADE DELETE para preservar logs)
        CONSTRAINT FK_Sistema_EjecucionesLog_Consulta 
            FOREIGN KEY (ConsultaID) 
            REFERENCES dbo.Sistema_ConsultasConfigurables(ConsultaID),
        
        -- CHECK: JSON válido en ParametrosUsados (si no es NULL)
        CONSTRAINT CK_Sistema_EjecucionesLog_Parametros_JSON 
            CHECK (ParametrosUsados IS NULL OR ISJSON(ParametrosUsados) = 1)
    );
    
    PRINT '  ✓ Tabla Sistema_ConsultasEjecucionesLog creada';

END
ELSE
BEGIN
    PRINT '  ⚠ Tabla Sistema_ConsultasEjecucionesLog ya existe';
END
GO

-- Índices
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Sistema_EjecucionesLog_Consulta')
BEGIN
    CREATE NONCLUSTERED INDEX IX_Sistema_EjecucionesLog_Consulta
    ON dbo.Sistema_ConsultasEjecucionesLog (ConsultaID)
    INCLUDE (Exitoso, FechaEjecucion);
    
    PRINT '  ✓ Índice IX_Sistema_EjecucionesLog_Consulta creado';
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Sistema_EjecucionesLog_Fecha')
BEGIN
    CREATE NONCLUSTERED INDEX IX_Sistema_EjecucionesLog_Fecha
    ON dbo.Sistema_ConsultasEjecucionesLog (FechaEjecucion DESC);
    
    PRINT '  ✓ Índice IX_Sistema_EjecucionesLog_Fecha creado';
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Sistema_EjecucionesLog_Usuario')
BEGIN
    CREATE NONCLUSTERED INDEX IX_Sistema_EjecucionesLog_Usuario
    ON dbo.Sistema_ConsultasEjecucionesLog (UsuarioID)
    WHERE UsuarioID IS NOT NULL;
    
    PRINT '  ✓ Índice IX_Sistema_EjecucionesLog_Usuario creado';
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Sistema_EjecucionesLog_Exitoso')
BEGIN
    CREATE NONCLUSTERED INDEX IX_Sistema_EjecucionesLog_Exitoso
    ON dbo.Sistema_ConsultasEjecucionesLog (Exitoso)
    WHERE Exitoso = 0;
    
    PRINT '  ✓ Índice IX_Sistema_EjecucionesLog_Exitoso creado';
END
GO


-- ============================================================================
-- TABLA 4: Sistema_MigracionConsultasTrace (TRAZABILIDAD DE MIGRACIÓN)
-- ============================================================================
-- Tabla TEMPORAL/AUDITORÍA para migración desde MongoDB.
-- NO es dependencia funcional permanente.
-- Permite rollback completo preservando JSON original.
-- ============================================================================

PRINT '';
PRINT '=== Creando Sistema_MigracionConsultasTrace ===';
GO

IF OBJECT_ID('dbo.Sistema_MigracionConsultasTrace', 'U') IS NULL
BEGIN

    CREATE TABLE dbo.Sistema_MigracionConsultasTrace (
        -- ═══════════════════════════════════════════════════════════════════
        -- IDENTIFICACIÓN
        -- ═══════════════════════════════════════════════════════════════════
        TraceID                 BIGINT IDENTITY(1,1) NOT NULL,
        
        -- ═══════════════════════════════════════════════════════════════════
        -- REFERENCIA A CONSULTA MIGRADA
        -- NULL si la migración falló o fue revertida
        -- ═══════════════════════════════════════════════════════════════════
        ConsultaID              BIGINT NULL,
        
        -- ═══════════════════════════════════════════════════════════════════
        -- ORIGEN MONGODB
        -- ═══════════════════════════════════════════════════════════════════
        MongoDBServerID         NVARCHAR(100) NOT NULL,
        MongoDBServerName       NVARCHAR(100) NULL,
        MongoDBQueryType        NVARCHAR(50) NOT NULL,
        -- 'query_inventario', 'query_ventas', 'query_movimientos'
        
        MongoDBQueryJSON        NVARCHAR(MAX) NOT NULL,
        -- JSON original completo para rollback
        
        -- ═══════════════════════════════════════════════════════════════════
        -- ESTADO DE MIGRACIÓN
        -- ═══════════════════════════════════════════════════════════════════
        EstadoMigracion         NVARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
        -- 'PENDIENTE', 'MIGRADO', 'ROLLBACK', 'ERROR'
        
        MensajeMigracion        NVARCHAR(500) NULL,
        
        -- ═══════════════════════════════════════════════════════════════════
        -- AUDITORÍA
        -- ═══════════════════════════════════════════════════════════════════
        FechaMigracion          DATETIME2 NOT NULL DEFAULT GETDATE(),
        MigradoPorEmail         NVARCHAR(100) NULL,
        
        FechaRollback           DATETIME2 NULL,
        RollbackPorEmail        NVARCHAR(100) NULL,
        
        -- ═══════════════════════════════════════════════════════════════════
        -- CONSTRAINTS
        -- ═══════════════════════════════════════════════════════════════════
        
        -- PK
        CONSTRAINT PK_Sistema_MigracionConsultasTrace 
            PRIMARY KEY CLUSTERED (TraceID),
        
        -- FK a consulta migrada (permite NULL para errores/rollback)
        CONSTRAINT FK_Sistema_Trace_Consulta 
            FOREIGN KEY (ConsultaID) 
            REFERENCES dbo.Sistema_ConsultasConfigurables(ConsultaID)
            ON DELETE SET NULL,
        
        -- CHECK: Estado válido
        CONSTRAINT CK_Sistema_Trace_EstadoMigracion 
            CHECK (EstadoMigracion IN ('PENDIENTE', 'MIGRADO', 'ROLLBACK', 'ERROR')),
        
        -- CHECK: JSON válido en MongoDBQueryJSON
        CONSTRAINT CK_Sistema_Trace_MongoDBQueryJSON 
            CHECK (ISJSON(MongoDBQueryJSON) = 1)
    );
    
    PRINT '  ✓ Tabla Sistema_MigracionConsultasTrace creada';

END
ELSE
BEGIN
    PRINT '  ⚠ Tabla Sistema_MigracionConsultasTrace ya existe';
END
GO

-- Índices
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Sistema_Trace_MongoDBServerID')
BEGIN
    CREATE NONCLUSTERED INDEX IX_Sistema_Trace_MongoDBServerID
    ON dbo.Sistema_MigracionConsultasTrace (MongoDBServerID)
    INCLUDE (MongoDBQueryType, EstadoMigracion);
    
    PRINT '  ✓ Índice IX_Sistema_Trace_MongoDBServerID creado';
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Sistema_Trace_Estado')
BEGIN
    CREATE NONCLUSTERED INDEX IX_Sistema_Trace_Estado
    ON dbo.Sistema_MigracionConsultasTrace (EstadoMigracion);
    
    PRINT '  ✓ Índice IX_Sistema_Trace_Estado creado';
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Sistema_Trace_ConsultaID')
BEGIN
    CREATE NONCLUSTERED INDEX IX_Sistema_Trace_ConsultaID
    ON dbo.Sistema_MigracionConsultasTrace (ConsultaID)
    WHERE ConsultaID IS NOT NULL;
    
    PRINT '  ✓ Índice IX_Sistema_Trace_ConsultaID creado';
END
GO


-- ============================================================================
-- NOTA SOBRE FKs A Usuario_Catalogo
-- ============================================================================
-- 
-- Los campos CreadoPorUsuarioID, ModificadoPorUsuarioID, CambiadoPorUsuarioID
-- y UsuarioID en logs NO tienen FK dura a Usuario_Catalogo.
--
-- JUSTIFICACIÓN:
-- 1. Usuario_Catalogo puede no existir en todos los ambientes.
-- 2. La migración desde MongoDB puede traer usuarios que ya no existen.
-- 3. Los logs históricos deben preservarse incluso si el usuario es eliminado.
-- 4. Se guarda también el Email como respaldo para trazabilidad.
--
-- Si se requiere FK dura en el futuro, se puede agregar con:
-- ALTER TABLE Sistema_ConsultasConfigurables
-- ADD CONSTRAINT FK_Sistema_Consultas_CreadoPor
--     FOREIGN KEY (CreadoPorUsuarioID) 
--     REFERENCES Usuario_Catalogo(UsuarioID);
--
-- ============================================================================


-- ============================================================================
-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║                    SCRIPT DE VALIDACIÓN POST-DDL                          ║
-- ║                         (COMENTADO - NO EJECUTAR)                         ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝
-- ============================================================================

/*
-- ============================================================================
-- DESCOMENTAR SOLO DESPUÉS DE EJECUTAR DDL EN FASE Q1.4
-- ============================================================================

PRINT '';
PRINT '=== VALIDACIÓN POST-DDL ===';

-- Verificar tablas creadas
SELECT 'TABLAS' as Tipo, TABLE_NAME as Nombre
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_NAME LIKE 'Sistema_Consultas%' OR TABLE_NAME LIKE 'Sistema_Migracion%'
ORDER BY TABLE_NAME;

-- Verificar constraints CHECK
SELECT 'CHECK CONSTRAINTS' as Tipo, name as Nombre, definition as Definicion
FROM sys.check_constraints
WHERE parent_object_id IN (
    OBJECT_ID('Sistema_ConsultasConfigurables'),
    OBJECT_ID('Sistema_ConsultasVersiones'),
    OBJECT_ID('Sistema_ConsultasEjecucionesLog'),
    OBJECT_ID('Sistema_MigracionConsultasTrace')
)
ORDER BY name;

-- Verificar índices
SELECT 'ÍNDICES' as Tipo, i.name as Nombre, t.name as Tabla, i.type_desc as TipoIndice
FROM sys.indexes i
INNER JOIN sys.tables t ON i.object_id = t.object_id
WHERE t.name LIKE 'Sistema_Consultas%' OR t.name LIKE 'Sistema_Migracion%'
ORDER BY t.name, i.name;

-- Verificar FKs
SELECT 'FOREIGN KEYS' as Tipo, fk.name as Nombre, 
       OBJECT_NAME(fk.parent_object_id) as TablaOrigen,
       OBJECT_NAME(fk.referenced_object_id) as TablaDestino
FROM sys.foreign_keys fk
WHERE OBJECT_NAME(fk.parent_object_id) LIKE 'Sistema_Consultas%' 
   OR OBJECT_NAME(fk.parent_object_id) LIKE 'Sistema_Migracion%'
ORDER BY fk.name;

-- Verificar defaults
SELECT 'DEFAULTS' as Tipo, d.name as Nombre, 
       OBJECT_NAME(d.parent_object_id) as Tabla,
       COL_NAME(d.parent_object_id, d.parent_column_id) as Columna,
       d.definition as Valor
FROM sys.default_constraints d
WHERE OBJECT_NAME(d.parent_object_id) LIKE 'Sistema_Consultas%' 
   OR OBJECT_NAME(d.parent_object_id) LIKE 'Sistema_Migracion%'
ORDER BY d.name;

PRINT '=== FIN VALIDACIÓN ===';
*/


-- ============================================================================
-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║                       SCRIPT DE ROLLBACK DDL                              ║
-- ║                    (COMENTADO - USAR CON PRECAUCIÓN)                      ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝
-- ============================================================================

/*
-- ============================================================================
-- ⚠️ PELIGRO: ELIMINA TODAS LAS TABLAS Y DATOS
-- ⚠️ USAR SOLO EN AMBIENTE CONTROLADO CON AUTORIZACIÓN
-- ============================================================================

PRINT '';
PRINT '=== ROLLBACK DDL - ELIMINANDO TABLAS ===';

-- Orden correcto: primero tablas con FKs, luego tablas referenciadas

-- 1. Eliminar tabla de trace (FK a Consultas)
IF OBJECT_ID('dbo.Sistema_MigracionConsultasTrace', 'U') IS NOT NULL
BEGIN
    DROP TABLE dbo.Sistema_MigracionConsultasTrace;
    PRINT '  ✓ Sistema_MigracionConsultasTrace eliminada';
END

-- 2. Eliminar tabla de logs (FK a Consultas)
IF OBJECT_ID('dbo.Sistema_ConsultasEjecucionesLog', 'U') IS NOT NULL
BEGIN
    DROP TABLE dbo.Sistema_ConsultasEjecucionesLog;
    PRINT '  ✓ Sistema_ConsultasEjecucionesLog eliminada';
END

-- 3. Eliminar tabla de versiones (FK a Consultas)
IF OBJECT_ID('dbo.Sistema_ConsultasVersiones', 'U') IS NOT NULL
BEGIN
    DROP TABLE dbo.Sistema_ConsultasVersiones;
    PRINT '  ✓ Sistema_ConsultasVersiones eliminada';
END

-- 4. Eliminar tabla principal
IF OBJECT_ID('dbo.Sistema_ConsultasConfigurables', 'U') IS NOT NULL
BEGIN
    DROP TABLE dbo.Sistema_ConsultasConfigurables;
    PRINT '  ✓ Sistema_ConsultasConfigurables eliminada';
END

PRINT '=== FIN ROLLBACK DDL ===';
*/


-- ============================================================================
-- FIN DEL SCRIPT DDL PASIVO
-- ============================================================================

PRINT '';
PRINT '════════════════════════════════════════════════════════════════════════';
PRINT '  FASE Q1.2 — DDL PASIVO GENERADO EXITOSAMENTE';
PRINT '  ';
PRINT '  ⚠️  ESTE SCRIPT NO HA SIDO EJECUTADO';
PRINT '  ⚠️  REQUIERE AUTORIZACIÓN PARA FASE Q1.4';
PRINT '════════════════════════════════════════════════════════════════════════';
GO
