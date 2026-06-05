-- ============================================================================
-- EDARSA HUB - CRM ENTERPRISE - SCRIPT 01: TABLAS PRINCIPALES
-- ============================================================================
-- Fecha: 2026-05-23
-- Autor: E1 Agent
-- Descripción: Script idempotente para crear tablas CRM sin duplicar existentes
-- MÁXIMA: Cliente_Catalogo se EXTIENDE, no se duplica
-- ============================================================================

-- ============================================================================
-- A. EXTENSIÓN DE TABLA EXISTENTE: Cliente_Catalogo
-- ============================================================================

-- Agregar campos CRM a Cliente_Catalogo (solo si no existen)
IF COL_LENGTH('dbo.Cliente_Catalogo', 'EjecutivoPrincipalUserID') IS NULL
BEGIN
    ALTER TABLE dbo.Cliente_Catalogo ADD EjecutivoPrincipalUserID UNIQUEIDENTIFIER NULL;
    PRINT 'Columna EjecutivoPrincipalUserID agregada a Cliente_Catalogo';
END

IF COL_LENGTH('dbo.Cliente_Catalogo', 'GerenteComercialUserID') IS NULL
BEGIN
    ALTER TABLE dbo.Cliente_Catalogo ADD GerenteComercialUserID UNIQUEIDENTIFIER NULL;
    PRINT 'Columna GerenteComercialUserID agregada a Cliente_Catalogo';
END

IF COL_LENGTH('dbo.Cliente_Catalogo', 'CustomerSuccessUserID') IS NULL
BEGIN
    ALTER TABLE dbo.Cliente_Catalogo ADD CustomerSuccessUserID UNIQUEIDENTIFIER NULL;
    PRINT 'Columna CustomerSuccessUserID agregada a Cliente_Catalogo';
END

IF COL_LENGTH('dbo.Cliente_Catalogo', 'SectorID') IS NULL
BEGIN
    ALTER TABLE dbo.Cliente_Catalogo ADD SectorID INT NULL;
    PRINT 'Columna SectorID agregada a Cliente_Catalogo';
END

IF COL_LENGTH('dbo.Cliente_Catalogo', 'SubsectorID') IS NULL
BEGIN
    ALTER TABLE dbo.Cliente_Catalogo ADD SubsectorID INT NULL;
    PRINT 'Columna SubsectorID agregada a Cliente_Catalogo';
END

IF COL_LENGTH('dbo.Cliente_Catalogo', 'TamanoClienteID') IS NULL
BEGIN
    ALTER TABLE dbo.Cliente_Catalogo ADD TamanoClienteID INT NULL;
    PRINT 'Columna TamanoClienteID agregada a Cliente_Catalogo';
END

IF COL_LENGTH('dbo.Cliente_Catalogo', 'RiesgoCuentaID') IS NULL
BEGIN
    ALTER TABLE dbo.Cliente_Catalogo ADD RiesgoCuentaID INT NULL;
    PRINT 'Columna RiesgoCuentaID agregada a Cliente_Catalogo';
END

IF COL_LENGTH('dbo.Cliente_Catalogo', 'EsProspecto') IS NULL
BEGIN
    ALTER TABLE dbo.Cliente_Catalogo ADD EsProspecto BIT DEFAULT 0;
    PRINT 'Columna EsProspecto agregada a Cliente_Catalogo';
END

IF COL_LENGTH('dbo.Cliente_Catalogo', 'EsPartner') IS NULL
BEGIN
    ALTER TABLE dbo.Cliente_Catalogo ADD EsPartner BIT DEFAULT 0;
    PRINT 'Columna EsPartner agregada a Cliente_Catalogo';
END

IF COL_LENGTH('dbo.Cliente_Catalogo', 'EsCuentaEstrategica') IS NULL
BEGIN
    ALTER TABLE dbo.Cliente_Catalogo ADD EsCuentaEstrategica BIT DEFAULT 0;
    PRINT 'Columna EsCuentaEstrategica agregada a Cliente_Catalogo';
END

IF COL_LENGTH('dbo.Cliente_Catalogo', 'FechaUltimaInteraccion') IS NULL
BEGIN
    ALTER TABLE dbo.Cliente_Catalogo ADD FechaUltimaInteraccion DATETIME NULL;
    PRINT 'Columna FechaUltimaInteraccion agregada a Cliente_Catalogo';
END

IF COL_LENGTH('dbo.Cliente_Catalogo', 'ScoreCuenta') IS NULL
BEGIN
    ALTER TABLE dbo.Cliente_Catalogo ADD ScoreCuenta INT NULL;
    PRINT 'Columna ScoreCuenta agregada a Cliente_Catalogo';
END

IF COL_LENGTH('dbo.Cliente_Catalogo', 'OrigenCuentaID') IS NULL
BEGIN
    ALTER TABLE dbo.Cliente_Catalogo ADD OrigenCuentaID INT NULL;
    PRINT 'Columna OrigenCuentaID agregada a Cliente_Catalogo';
END

-- ============================================================================
-- B. TABLA: CRM_Leads
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Leads')
BEGIN
    CREATE TABLE dbo.CRM_Leads (
        LeadID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        EmpresaID UNIQUEIDENTIFIER NOT NULL,
        SucursalID UNIQUEIDENTIFIER NULL,
        FolioLead NVARCHAR(20) NULL,
        
        -- Datos del Lead
        NombreContacto NVARCHAR(100) NOT NULL,
        ApellidoPaterno NVARCHAR(100) NULL,
        ApellidoMaterno NVARCHAR(100) NULL,
        NombreEmpresa NVARCHAR(200) NULL,
        Puesto NVARCHAR(100) NULL,
        Email NVARCHAR(150) NULL,
        Telefono NVARCHAR(50) NULL,
        TelefonoMovil NVARCHAR(50) NULL,
        
        -- Clasificación
        OrigenLeadID INT NULL,
        EstatusLeadID INT NOT NULL DEFAULT 1,
        PrioridadID INT NULL,
        CalificacionLeadID INT NULL,
        
        -- Asignación
        EjecutivoAsignadoUserID UNIQUEIDENTIFIER NULL,
        FechaAsignacion DATETIME NULL,
        
        -- Información adicional
        Descripcion NVARCHAR(MAX) NULL,
        Presupuesto DECIMAL(18,2) NULL,
        MonedaID INT NULL,
        FechaEstimadaCierre DATETIME NULL,
        
        -- Conversión
        ConvertidoACuenta BIT DEFAULT 0,
        CuentaConvertidaID UNIQUEIDENTIFIER NULL,
        ContactoConvertidoID UNIQUEIDENTIFIER NULL,
        OportunidadConvertidaID UNIQUEIDENTIFIER NULL,
        FechaConversion DATETIME NULL,
        
        -- Descalificación
        Descalificado BIT DEFAULT 0,
        MotivoDescalificacionID INT NULL,
        FechaDescalificacion DATETIME NULL,
        NotasDescalificacion NVARCHAR(500) NULL,
        
        -- Auditoría
        Activo BIT DEFAULT 1,
        CreatedBy UNIQUEIDENTIFIER NULL,
        UpdatedBy UNIQUEIDENTIFIER NULL,
        CreatedAt DATETIME DEFAULT GETDATE(),
        UpdatedAt DATETIME DEFAULT GETDATE(),
        DeletedAt DATETIME NULL
    );
    PRINT 'Tabla CRM_Leads creada';
    
    CREATE INDEX IX_CRM_Leads_Empresa ON dbo.CRM_Leads(EmpresaID);
    CREATE INDEX IX_CRM_Leads_Estatus ON dbo.CRM_Leads(EstatusLeadID);
    CREATE INDEX IX_CRM_Leads_Ejecutivo ON dbo.CRM_Leads(EjecutivoAsignadoUserID);
    CREATE INDEX IX_CRM_Leads_CreatedAt ON dbo.CRM_Leads(CreatedAt);
END

-- ============================================================================
-- C. TABLA: CRM_Oportunidades
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Oportunidades')
BEGIN
    CREATE TABLE dbo.CRM_Oportunidades (
        OportunidadID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        EmpresaID UNIQUEIDENTIFIER NOT NULL,
        SucursalID UNIQUEIDENTIFIER NULL,
        FolioOportunidad NVARCHAR(20) NULL,
        
        -- Relaciones
        CuentaID UNIQUEIDENTIFIER NULL,
        ContactoPrincipalID UNIQUEIDENTIFIER NULL,
        LeadOrigenID UNIQUEIDENTIFIER NULL,
        
        -- Información principal
        NombreOportunidad NVARCHAR(200) NOT NULL,
        DescripcionOportunidad NVARCHAR(MAX) NULL,
        
        -- Pipeline y etapa
        PipelineID INT NOT NULL DEFAULT 1,
        EtapaActualID INT NOT NULL DEFAULT 1,
        ProbabilidadActual INT DEFAULT 10,
        DiasEnEtapaActual INT DEFAULT 0,
        
        -- Montos
        MontoEstimado DECIMAL(18,2) NULL,
        MonedaID INT DEFAULT 1,
        IngresoRecurrenteEstimado DECIMAL(18,2) NULL,
        IngresoNoRecurrenteEstimado DECIMAL(18,2) NULL,
        CostoEstimadoImplementacion DECIMAL(18,2) NULL,
        MargenEstimado DECIMAL(18,2) NULL,
        
        -- Descuentos
        RequiereAprobacionDescuento BIT DEFAULT 0,
        PorcentajeDescuento DECIMAL(5,2) NULL,
        MontoDescuento DECIMAL(18,2) NULL,
        
        -- Fechas
        FechaApertura DATETIME DEFAULT GETDATE(),
        FechaEstimadaCierre DATETIME NULL,
        FechaRealCierre DATETIME NULL,
        FechaUltimaActividad DATETIME NULL,
        FechaProximaActividad DATETIME NULL,
        
        -- Responsables
        EjecutivoResponsableUserID UNIQUEIDENTIFIER NULL,
        PreventaResponsableUserID UNIQUEIDENTIFIER NULL,
        GerenteComercialUserID UNIQUEIDENTIFIER NULL,
        CustomerSuccessUserID UNIQUEIDENTIFIER NULL,
        
        -- Competencia
        CompetidorPrincipalID INT NULL,
        
        -- Cierre
        EstatusCierreID INT NULL,
        MotivoGanadaID INT NULL,
        MotivoPerdidaID INT NULL,
        RazonPerdidaTexto NVARCHAR(500) NULL,
        
        -- Riesgo
        RiesgoOportunidadID INT NULL,
        ScoreCierre INT NULL,
        
        -- Flags
        RequiereContrato BIT DEFAULT 0,
        RequiereImplementacion BIT DEFAULT 0,
        RequiereFacturacionProgramada BIT DEFAULT 0,
        
        -- Observaciones
        ObservacionesInternas NVARCHAR(MAX) NULL,
        
        -- Estatus
        EstatusOportunidadID INT NOT NULL DEFAULT 1,
        Activo BIT DEFAULT 1,
        
        -- Auditoría
        CreatedBy UNIQUEIDENTIFIER NULL,
        UpdatedBy UNIQUEIDENTIFIER NULL,
        CreatedAt DATETIME DEFAULT GETDATE(),
        UpdatedAt DATETIME DEFAULT GETDATE(),
        DeletedAt DATETIME NULL
    );
    PRINT 'Tabla CRM_Oportunidades creada';
    
    CREATE INDEX IX_CRM_Oportunidades_Empresa ON dbo.CRM_Oportunidades(EmpresaID);
    CREATE INDEX IX_CRM_Oportunidades_Cuenta ON dbo.CRM_Oportunidades(CuentaID);
    CREATE INDEX IX_CRM_Oportunidades_Pipeline ON dbo.CRM_Oportunidades(PipelineID, EtapaActualID);
    CREATE INDEX IX_CRM_Oportunidades_Ejecutivo ON dbo.CRM_Oportunidades(EjecutivoResponsableUserID);
    CREATE INDEX IX_CRM_Oportunidades_Estatus ON dbo.CRM_Oportunidades(EstatusOportunidadID);
    CREATE INDEX IX_CRM_Oportunidades_FechaCierre ON dbo.CRM_Oportunidades(FechaEstimadaCierre);
END

-- ============================================================================
-- D. TABLA: CRM_Propuestas
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Propuestas')
BEGIN
    CREATE TABLE dbo.CRM_Propuestas (
        PropuestaID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        EmpresaID UNIQUEIDENTIFIER NOT NULL,
        OportunidadID UNIQUEIDENTIFIER NOT NULL,
        FolioPropuesta NVARCHAR(20) NULL,
        
        -- Información
        NombrePropuesta NVARCHAR(200) NOT NULL,
        DescripcionPropuesta NVARCHAR(MAX) NULL,
        TipoPropuestaID INT NULL,
        VersionActual INT DEFAULT 1,
        
        -- Montos
        MontoTotal DECIMAL(18,2) NULL,
        MonedaID INT DEFAULT 1,
        Descuento DECIMAL(18,2) NULL,
        IVA DECIMAL(18,2) NULL,
        MontoFinal DECIMAL(18,2) NULL,
        
        -- Fechas
        FechaCreacion DATETIME DEFAULT GETDATE(),
        FechaEnvio DATETIME NULL,
        FechaVigencia DATETIME NULL,
        FechaRespuesta DATETIME NULL,
        
        -- Estatus
        EstatusPropuestaID INT NOT NULL DEFAULT 1,
        MotivoRechazoID INT NULL,
        NotasRechazo NVARCHAR(500) NULL,
        
        -- Aprobación
        RequiereAprobacion BIT DEFAULT 0,
        AprobadaPor UNIQUEIDENTIFIER NULL,
        FechaAprobacion DATETIME NULL,
        
        -- Auditoría
        Activo BIT DEFAULT 1,
        CreatedBy UNIQUEIDENTIFIER NULL,
        UpdatedBy UNIQUEIDENTIFIER NULL,
        CreatedAt DATETIME DEFAULT GETDATE(),
        UpdatedAt DATETIME DEFAULT GETDATE()
    );
    PRINT 'Tabla CRM_Propuestas creada';
    
    CREATE INDEX IX_CRM_Propuestas_Oportunidad ON dbo.CRM_Propuestas(OportunidadID);
    CREATE INDEX IX_CRM_Propuestas_Estatus ON dbo.CRM_Propuestas(EstatusPropuestaID);
END

-- ============================================================================
-- E. TABLA: CRM_Contratos
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Contratos')
BEGIN
    CREATE TABLE dbo.CRM_Contratos (
        ContratoID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        EmpresaID UNIQUEIDENTIFIER NOT NULL,
        CuentaID UNIQUEIDENTIFIER NOT NULL,
        OportunidadID UNIQUEIDENTIFIER NULL,
        PropuestaID UNIQUEIDENTIFIER NULL,
        FolioContrato NVARCHAR(30) NULL,
        
        -- Información
        NombreContrato NVARCHAR(200) NOT NULL,
        TipoContratoID INT NULL,
        DescripcionContrato NVARCHAR(MAX) NULL,
        
        -- Montos
        MontoContrato DECIMAL(18,2) NULL,
        MonedaID INT DEFAULT 1,
        
        -- Vigencia
        FechaInicio DATETIME NULL,
        FechaFin DATETIME NULL,
        DuracionMeses INT NULL,
        RenovacionAutomatica BIT DEFAULT 0,
        DiasAvisoRenovacion INT DEFAULT 30,
        
        -- Estatus
        EstatusContratoID INT NOT NULL DEFAULT 1,
        
        -- Auditoría
        Activo BIT DEFAULT 1,
        CreatedBy UNIQUEIDENTIFIER NULL,
        UpdatedBy UNIQUEIDENTIFIER NULL,
        CreatedAt DATETIME DEFAULT GETDATE(),
        UpdatedAt DATETIME DEFAULT GETDATE()
    );
    PRINT 'Tabla CRM_Contratos creada';
    
    CREATE INDEX IX_CRM_Contratos_Cuenta ON dbo.CRM_Contratos(CuentaID);
    CREATE INDEX IX_CRM_Contratos_Estatus ON dbo.CRM_Contratos(EstatusContratoID);
    CREATE INDEX IX_CRM_Contratos_FechaFin ON dbo.CRM_Contratos(FechaFin);
END

-- ============================================================================
-- F. TABLAS DE CONFIGURACIÓN: Pipeline
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Config_Pipelines')
BEGIN
    CREATE TABLE dbo.CRM_Config_Pipelines (
        PipelineID INT IDENTITY(1,1) PRIMARY KEY,
        EmpresaID UNIQUEIDENTIFIER NULL,
        Codigo NVARCHAR(20) NOT NULL,
        Nombre NVARCHAR(100) NOT NULL,
        Descripcion NVARCHAR(500) NULL,
        TipoPipelineID INT DEFAULT 1,
        EsDefault BIT DEFAULT 0,
        Orden INT DEFAULT 0,
        Activo BIT DEFAULT 1,
        CreatedAt DATETIME DEFAULT GETDATE(),
        UpdatedAt DATETIME DEFAULT GETDATE()
    );
    PRINT 'Tabla CRM_Config_Pipelines creada';
END

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Config_PipelineEtapas')
BEGIN
    CREATE TABLE dbo.CRM_Config_PipelineEtapas (
        EtapaID INT IDENTITY(1,1) PRIMARY KEY,
        PipelineID INT NOT NULL,
        Codigo NVARCHAR(20) NOT NULL,
        Nombre NVARCHAR(100) NOT NULL,
        Descripcion NVARCHAR(500) NULL,
        ProbabilidadDefault INT DEFAULT 0,
        Orden INT NOT NULL,
        ColorHex NVARCHAR(7) DEFAULT '#6B7280',
        EsEtapaInicial BIT DEFAULT 0,
        EsEtapaCierre BIT DEFAULT 0,
        EsCierreGanado BIT DEFAULT 0,
        EsCierrePerdido BIT DEFAULT 0,
        DiasMaxSLA INT NULL,
        Activo BIT DEFAULT 1,
        CreatedAt DATETIME DEFAULT GETDATE(),
        UpdatedAt DATETIME DEFAULT GETDATE()
    );
    PRINT 'Tabla CRM_Config_PipelineEtapas creada';
    
    CREATE INDEX IX_CRM_PipelineEtapas_Pipeline ON dbo.CRM_Config_PipelineEtapas(PipelineID);
END

-- ============================================================================
-- G. TABLAS DE RELACIÓN
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Oportunidad_Contactos')
BEGIN
    CREATE TABLE dbo.CRM_Oportunidad_Contactos (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        OportunidadID UNIQUEIDENTIFIER NOT NULL,
        ContactoID UNIQUEIDENTIFIER NOT NULL,
        RolContactoID INT NULL,
        EsPrincipal BIT DEFAULT 0,
        Activo BIT DEFAULT 1,
        CreatedAt DATETIME DEFAULT GETDATE()
    );
    PRINT 'Tabla CRM_Oportunidad_Contactos creada';
    
    CREATE INDEX IX_CRM_OportunidadContactos_Opp ON dbo.CRM_Oportunidad_Contactos(OportunidadID);
END

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Oportunidad_Documentos')
BEGIN
    CREATE TABLE dbo.CRM_Oportunidad_Documentos (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        OportunidadID UNIQUEIDENTIFIER NOT NULL,
        TipoDocumentoID INT NULL,
        NombreDocumento NVARCHAR(200) NOT NULL,
        RutaArchivo NVARCHAR(500) NULL,
        Extension NVARCHAR(10) NULL,
        TamanoBytes BIGINT NULL,
        Descripcion NVARCHAR(500) NULL,
        Activo BIT DEFAULT 1,
        CreatedBy UNIQUEIDENTIFIER NULL,
        CreatedAt DATETIME DEFAULT GETDATE()
    );
    PRINT 'Tabla CRM_Oportunidad_Documentos creada';
    
    CREATE INDEX IX_CRM_OportunidadDocs_Opp ON dbo.CRM_Oportunidad_Documentos(OportunidadID);
END

-- ============================================================================
-- H. TABLA DE HISTORIAL DE ETAPAS
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CRM_Oportunidades_HistorialEtapas')
BEGIN
    CREATE TABLE dbo.CRM_Oportunidades_HistorialEtapas (
        HistorialID BIGINT IDENTITY(1,1) PRIMARY KEY,
        OportunidadID UNIQUEIDENTIFIER NOT NULL,
        EtapaAnteriorID INT NULL,
        EtapaNuevaID INT NOT NULL,
        ProbabilidadAnterior INT NULL,
        ProbabilidadNueva INT NULL,
        MontoAnterior DECIMAL(18,2) NULL,
        MontoNuevo DECIMAL(18,2) NULL,
        DiasEnEtapaAnterior INT NULL,
        Comentario NVARCHAR(500) NULL,
        CambiadoPor UNIQUEIDENTIFIER NULL,
        FechaCambio DATETIME DEFAULT GETDATE()
    );
    PRINT 'Tabla CRM_Oportunidades_HistorialEtapas creada';
    
    CREATE INDEX IX_CRM_HistorialEtapas_Opp ON dbo.CRM_Oportunidades_HistorialEtapas(OportunidadID);
    CREATE INDEX IX_CRM_HistorialEtapas_Fecha ON dbo.CRM_Oportunidades_HistorialEtapas(FechaCambio);
END

PRINT '';
PRINT '============================================';
PRINT 'SCRIPT 01 COMPLETADO EXITOSAMENTE';
PRINT '============================================';
