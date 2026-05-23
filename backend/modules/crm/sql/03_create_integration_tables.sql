-- ============================================================================
-- EDARSA HUB - CRM Enterprise: Tablas de Integración Universal
-- Fase 5: Staging tables para sync bidireccional con CRMs externos
-- ============================================================================

-- A) TABLA DE CONECTORES REGISTRADOS
-- ============================================================================
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Integracion_Conectores')
BEGIN
    CREATE TABLE dbo.CRM_Integracion_Conectores (
        ConectorID INT IDENTITY(1,1) PRIMARY KEY,
        EmpresaID UNIQUEIDENTIFIER NOT NULL,
        
        -- Identificación
        Codigo NVARCHAR(50) NOT NULL,                -- 'VTIGER', 'SALESFORCE', 'HUBSPOT', 'ZOHO'
        Nombre NVARCHAR(100) NOT NULL,
        Descripcion NVARCHAR(500) NULL,
        TipoConector NVARCHAR(50) NOT NULL,          -- 'REST_API', 'OAUTH2', 'SOAP', 'WEBHOOK'
        
        -- Configuración de conexión (encriptada)
        ConfiguracionJSON NVARCHAR(MAX) NULL,        -- URL, credenciales, etc.
        
        -- Estado
        Activo BIT DEFAULT 1,
        EsPrincipal BIT DEFAULT 0,                   -- Si es el CRM principal
        UltimaSincronizacion DATETIME NULL,
        EstadoConexion NVARCHAR(50) DEFAULT 'PENDIENTE', -- CONECTADO, ERROR, PENDIENTE
        MensajeError NVARCHAR(MAX) NULL,
        
        -- Mapeo de campos
        MapeoLeadsJSON NVARCHAR(MAX) NULL,
        MapeoOportunidadesJSON NVARCHAR(MAX) NULL,
        MapeoCuentasJSON NVARCHAR(MAX) NULL,
        MapeoContactosJSON NVARCHAR(MAX) NULL,
        
        -- Auditoría
        CreatedAt DATETIME DEFAULT GETDATE(),
        CreatedBy UNIQUEIDENTIFIER NULL,
        UpdatedAt DATETIME DEFAULT GETDATE(),
        UpdatedBy UNIQUEIDENTIFIER NULL,
        
        CONSTRAINT UQ_CRM_Conector_Empresa_Codigo UNIQUE (EmpresaID, Codigo)
    );
    PRINT '✓ Tabla CRM_Integracion_Conectores creada';
END
GO

-- B) STAGING TABLE: LEADS EXTERNOS
-- ============================================================================
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Staging_Leads')
BEGIN
    CREATE TABLE dbo.CRM_Staging_Leads (
        StagingID BIGINT IDENTITY(1,1) PRIMARY KEY,
        ConectorID INT NOT NULL,
        
        -- ID externo y local
        ExternalID NVARCHAR(100) NOT NULL,           -- ID en el CRM externo
        LocalLeadID UNIQUEIDENTIFIER NULL,           -- ID en CRM_Leads (si existe)
        
        -- Datos del Lead (campos comunes normalizados)
        NombreContacto NVARCHAR(100) NULL,
        ApellidoPaterno NVARCHAR(100) NULL,
        ApellidoMaterno NVARCHAR(100) NULL,
        NombreEmpresa NVARCHAR(200) NULL,
        Email NVARCHAR(150) NULL,
        Telefono NVARCHAR(50) NULL,
        TelefonoMovil NVARCHAR(50) NULL,
        Puesto NVARCHAR(100) NULL,
        Descripcion NVARCHAR(MAX) NULL,
        Origen NVARCHAR(100) NULL,
        Estatus NVARCHAR(100) NULL,
        
        -- JSON con datos adicionales del CRM externo
        DatosExternosJSON NVARCHAR(MAX) NULL,
        
        -- Control de sincronización
        DireccionSync NVARCHAR(20) NOT NULL,         -- 'ENTRANTE', 'SALIENTE', 'BIDIRECCIONAL'
        EstadoSync NVARCHAR(50) DEFAULT 'PENDIENTE', -- PENDIENTE, SINCRONIZADO, ERROR, CONFLICTO
        FechaExterna DATETIME NULL,                  -- Última modificación en CRM externo
        FechaLocal DATETIME NULL,                    -- Última modificación local
        FechaProcesado DATETIME NULL,
        Intentos INT DEFAULT 0,
        MensajeError NVARCHAR(MAX) NULL,
        
        -- Auditoría
        CreatedAt DATETIME DEFAULT GETDATE(),
        UpdatedAt DATETIME DEFAULT GETDATE(),
        
        CONSTRAINT FK_Staging_Leads_Conector FOREIGN KEY (ConectorID) 
            REFERENCES CRM_Integracion_Conectores(ConectorID),
        CONSTRAINT UQ_Staging_Lead_External UNIQUE (ConectorID, ExternalID)
    );
    
    CREATE INDEX IX_Staging_Leads_Estado ON CRM_Staging_Leads(EstadoSync, ConectorID);
    CREATE INDEX IX_Staging_Leads_LocalID ON CRM_Staging_Leads(LocalLeadID) WHERE LocalLeadID IS NOT NULL;
    PRINT '✓ Tabla CRM_Staging_Leads creada';
END
GO

-- C) STAGING TABLE: OPORTUNIDADES EXTERNAS
-- ============================================================================
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Staging_Oportunidades')
BEGIN
    CREATE TABLE dbo.CRM_Staging_Oportunidades (
        StagingID BIGINT IDENTITY(1,1) PRIMARY KEY,
        ConectorID INT NOT NULL,
        
        -- ID externo y local
        ExternalID NVARCHAR(100) NOT NULL,
        LocalOportunidadID UNIQUEIDENTIFIER NULL,
        
        -- Datos normalizados
        NombreOportunidad NVARCHAR(200) NULL,
        Descripcion NVARCHAR(MAX) NULL,
        MontoEstimado DECIMAL(18,2) NULL,
        Moneda NVARCHAR(10) DEFAULT 'MXN',
        FechaEstimadaCierre DATE NULL,
        Etapa NVARCHAR(100) NULL,
        Probabilidad INT NULL,
        Estatus NVARCHAR(100) NULL,
        
        -- Referencias externas
        ExternalCuentaID NVARCHAR(100) NULL,
        ExternalContactoID NVARCHAR(100) NULL,
        ExternalLeadID NVARCHAR(100) NULL,
        
        -- JSON con datos adicionales
        DatosExternosJSON NVARCHAR(MAX) NULL,
        
        -- Control de sincronización
        DireccionSync NVARCHAR(20) NOT NULL,
        EstadoSync NVARCHAR(50) DEFAULT 'PENDIENTE',
        FechaExterna DATETIME NULL,
        FechaLocal DATETIME NULL,
        FechaProcesado DATETIME NULL,
        Intentos INT DEFAULT 0,
        MensajeError NVARCHAR(MAX) NULL,
        
        -- Auditoría
        CreatedAt DATETIME DEFAULT GETDATE(),
        UpdatedAt DATETIME DEFAULT GETDATE(),
        
        CONSTRAINT FK_Staging_Oportunidades_Conector FOREIGN KEY (ConectorID) 
            REFERENCES CRM_Integracion_Conectores(ConectorID),
        CONSTRAINT UQ_Staging_Oportunidad_External UNIQUE (ConectorID, ExternalID)
    );
    
    CREATE INDEX IX_Staging_Oportunidades_Estado ON CRM_Staging_Oportunidades(EstadoSync, ConectorID);
    PRINT '✓ Tabla CRM_Staging_Oportunidades creada';
END
GO

-- D) STAGING TABLE: CUENTAS/CLIENTES EXTERNOS
-- ============================================================================
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Staging_Cuentas')
BEGIN
    CREATE TABLE dbo.CRM_Staging_Cuentas (
        StagingID BIGINT IDENTITY(1,1) PRIMARY KEY,
        ConectorID INT NOT NULL,
        
        -- ID externo y local
        ExternalID NVARCHAR(100) NOT NULL,
        LocalCuentaID UNIQUEIDENTIFIER NULL,         -- PublicUUID de Cliente_Catalogo
        
        -- Datos normalizados
        RazonSocial NVARCHAR(200) NULL,
        NombreComercial NVARCHAR(200) NULL,
        RFC NVARCHAR(20) NULL,
        Industria NVARCHAR(100) NULL,
        Sitio Web NVARCHAR(200) NULL,
        EmailPrincipal NVARCHAR(150) NULL,
        TelefonoPrincipal NVARCHAR(50) NULL,
        Direccion NVARCHAR(500) NULL,
        
        -- JSON con datos adicionales
        DatosExternosJSON NVARCHAR(MAX) NULL,
        
        -- Control de sincronización
        DireccionSync NVARCHAR(20) NOT NULL,
        EstadoSync NVARCHAR(50) DEFAULT 'PENDIENTE',
        FechaExterna DATETIME NULL,
        FechaLocal DATETIME NULL,
        FechaProcesado DATETIME NULL,
        Intentos INT DEFAULT 0,
        MensajeError NVARCHAR(MAX) NULL,
        
        -- Auditoría
        CreatedAt DATETIME DEFAULT GETDATE(),
        UpdatedAt DATETIME DEFAULT GETDATE(),
        
        CONSTRAINT FK_Staging_Cuentas_Conector FOREIGN KEY (ConectorID) 
            REFERENCES CRM_Integracion_Conectores(ConectorID),
        CONSTRAINT UQ_Staging_Cuenta_External UNIQUE (ConectorID, ExternalID)
    );
    
    CREATE INDEX IX_Staging_Cuentas_Estado ON CRM_Staging_Cuentas(EstadoSync, ConectorID);
    PRINT '✓ Tabla CRM_Staging_Cuentas creada';
END
GO

-- E) LOG DE SINCRONIZACIÓN
-- ============================================================================
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Integracion_SyncLog')
BEGIN
    CREATE TABLE dbo.CRM_Integracion_SyncLog (
        LogID BIGINT IDENTITY(1,1) PRIMARY KEY,
        ConectorID INT NOT NULL,
        
        -- Información del proceso
        TipoEntidad NVARCHAR(50) NOT NULL,           -- 'LEAD', 'OPORTUNIDAD', 'CUENTA', 'CONTACTO'
        Operacion NVARCHAR(50) NOT NULL,             -- 'PULL', 'PUSH', 'SYNC_FULL'
        FechaInicio DATETIME NOT NULL,
        FechaFin DATETIME NULL,
        Duracion INT NULL,                           -- Segundos
        
        -- Resultados
        RegistrosProcesados INT DEFAULT 0,
        RegistrosCreados INT DEFAULT 0,
        RegistrosActualizados INT DEFAULT 0,
        RegistrosError INT DEFAULT 0,
        RegistrosConflicto INT DEFAULT 0,
        
        -- Estado
        Estado NVARCHAR(50) NOT NULL,                -- 'EN_PROCESO', 'COMPLETADO', 'ERROR', 'PARCIAL'
        MensajeError NVARCHAR(MAX) NULL,
        DetallesJSON NVARCHAR(MAX) NULL,
        
        -- Auditoría
        EjecutadoPor UNIQUEIDENTIFIER NULL,
        
        CONSTRAINT FK_SyncLog_Conector FOREIGN KEY (ConectorID) 
            REFERENCES CRM_Integracion_Conectores(ConectorID)
    );
    
    CREATE INDEX IX_SyncLog_Conector_Fecha ON CRM_Integracion_SyncLog(ConectorID, FechaInicio DESC);
    PRINT '✓ Tabla CRM_Integracion_SyncLog creada';
END
GO

-- F) MAPEO DE ETAPAS ENTRE SISTEMAS
-- ============================================================================
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Integracion_MapeoEtapas')
BEGIN
    CREATE TABLE dbo.CRM_Integracion_MapeoEtapas (
        MapeoID INT IDENTITY(1,1) PRIMARY KEY,
        ConectorID INT NOT NULL,
        
        -- Mapeo
        EtapaExterna NVARCHAR(100) NOT NULL,         -- Nombre/código en CRM externo
        EtapaLocalID INT NULL,                       -- ID en CRM_Config_PipelineEtapas
        EtapaLocalNombre NVARCHAR(100) NULL,
        
        -- Dirección del mapeo
        MapeoActivo BIT DEFAULT 1,
        EsDefault BIT DEFAULT 0,                     -- Etapa por defecto si no hay match
        
        CreatedAt DATETIME DEFAULT GETDATE(),
        
        CONSTRAINT FK_MapeoEtapas_Conector FOREIGN KEY (ConectorID) 
            REFERENCES CRM_Integracion_Conectores(ConectorID),
        CONSTRAINT UQ_MapeoEtapas UNIQUE (ConectorID, EtapaExterna)
    );
    PRINT '✓ Tabla CRM_Integracion_MapeoEtapas creada';
END
GO

-- G) INSERTAR CONECTOR VTIGER COMO EJEMPLO
-- ============================================================================
IF NOT EXISTS (SELECT 1 FROM CRM_Integracion_Conectores WHERE Codigo = 'VTIGER')
BEGIN
    INSERT INTO CRM_Integracion_Conectores (
        EmpresaID, Codigo, Nombre, Descripcion, TipoConector, 
        Activo, EsPrincipal, EstadoConexion
    ) VALUES (
        '00000000-0000-0000-0000-000000000001',
        'VTIGER',
        'VTiger CRM',
        'Integración con VTiger CRM Open Source/Cloud',
        'REST_API',
        1, 0, 'PENDIENTE'
    );
    PRINT '✓ Conector VTiger registrado';
END
GO

PRINT '';
PRINT '============================================================';
PRINT '  CRM Integración Universal - Tablas creadas exitosamente';
PRINT '============================================================';
