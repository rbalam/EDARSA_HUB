-- =====================================================================
-- EDARSA HUB - DDL Tablas Sincronización Vtiger CRM
-- =====================================================================
-- Ejecutar en EDARSAHUB SQL Server
-- Tablas para almacenar datos sincronizados desde Vtiger
-- =====================================================================

-- Tabla: Sync_Vtiger_Leads
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Sync_Vtiger_Leads]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Sync_Vtiger_Leads] (
        SyncID UNIQUEIDENTIFIER DEFAULT NEWID() PRIMARY KEY,
        VtigerID VARCHAR(50) NOT NULL UNIQUE,
        LeadNo VARCHAR(50),
        Nombre NVARCHAR(200),
        Apellido NVARCHAR(200),
        Empresa NVARCHAR(500),
        Email NVARCHAR(200),
        Telefono VARCHAR(50),
        Celular VARCHAR(50),
        Website NVARCHAR(500),
        Industria NVARCHAR(100),
        FuenteLead NVARCHAR(100),
        Estatus NVARCHAR(50),
        IngresoAnual DECIMAL(18,2),
        NumEmpleados INT,
        Descripcion NVARCHAR(MAX),
        Ciudad NVARCHAR(100),
        Estado NVARCHAR(100),
        Pais NVARCHAR(100),
        UsuarioAsignadoVtiger VARCHAR(50),
        FechaCreacionVtiger DATETIME,
        FechaModificacionVtiger DATETIME,
        FechaCreacionLocal DATETIME DEFAULT GETDATE(),
        FechaUltimaSync DATETIME DEFAULT GETDATE(),
        SincronizadoALocal BIT DEFAULT 0,
        LocalID UNIQUEIDENTIFIER NULL,
        INDEX IX_Vtiger_Leads_Email (Email),
        INDEX IX_Vtiger_Leads_Empresa (Empresa),
        INDEX IX_Vtiger_Leads_Estatus (Estatus)
    );
    PRINT 'Tabla Sync_Vtiger_Leads creada';
END
GO

-- Tabla: Sync_Vtiger_Contactos
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Sync_Vtiger_Contactos]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Sync_Vtiger_Contactos] (
        SyncID UNIQUEIDENTIFIER DEFAULT NEWID() PRIMARY KEY,
        VtigerID VARCHAR(50) NOT NULL UNIQUE,
        ContactoNo VARCHAR(50),
        Nombre NVARCHAR(200),
        Apellido NVARCHAR(200),
        Email NVARCHAR(200),
        Telefono VARCHAR(50),
        Celular VARCHAR(50),
        Titulo NVARCHAR(200),
        Departamento NVARCHAR(200),
        CuentaVtigerID VARCHAR(50),
        Descripcion NVARCHAR(MAX),
        Ciudad NVARCHAR(100),
        Estado NVARCHAR(100),
        Pais NVARCHAR(100),
        UsuarioAsignadoVtiger VARCHAR(50),
        FechaCreacionVtiger DATETIME,
        FechaModificacionVtiger DATETIME,
        FechaCreacionLocal DATETIME DEFAULT GETDATE(),
        FechaUltimaSync DATETIME DEFAULT GETDATE(),
        SincronizadoALocal BIT DEFAULT 0,
        LocalID UNIQUEIDENTIFIER NULL,
        INDEX IX_Vtiger_Contactos_Email (Email),
        INDEX IX_Vtiger_Contactos_Cuenta (CuentaVtigerID)
    );
    PRINT 'Tabla Sync_Vtiger_Contactos creada';
END
GO

-- Tabla: Sync_Vtiger_Cuentas
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Sync_Vtiger_Cuentas]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Sync_Vtiger_Cuentas] (
        SyncID UNIQUEIDENTIFIER DEFAULT NEWID() PRIMARY KEY,
        VtigerID VARCHAR(50) NOT NULL UNIQUE,
        CuentaNo VARCHAR(50),
        NombreCuenta NVARCHAR(500),
        Website NVARCHAR(500),
        Telefono VARCHAR(50),
        Fax VARCHAR(50),
        Email NVARCHAR(200),
        Industria NVARCHAR(100),
        TipoCuenta NVARCHAR(100),
        IngresoAnual DECIMAL(18,2),
        NumEmpleados INT,
        Descripcion NVARCHAR(MAX),
        Ciudad NVARCHAR(100),
        Estado NVARCHAR(100),
        Pais NVARCHAR(100),
        UsuarioAsignadoVtiger VARCHAR(50),
        FechaCreacionVtiger DATETIME,
        FechaModificacionVtiger DATETIME,
        FechaCreacionLocal DATETIME DEFAULT GETDATE(),
        FechaUltimaSync DATETIME DEFAULT GETDATE(),
        SincronizadoALocal BIT DEFAULT 0,
        LocalID UNIQUEIDENTIFIER NULL,
        INDEX IX_Vtiger_Cuentas_Nombre (NombreCuenta),
        INDEX IX_Vtiger_Cuentas_Industria (Industria)
    );
    PRINT 'Tabla Sync_Vtiger_Cuentas creada';
END
GO

-- Tabla: Sync_Vtiger_Oportunidades
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Sync_Vtiger_Oportunidades]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Sync_Vtiger_Oportunidades] (
        SyncID UNIQUEIDENTIFIER DEFAULT NEWID() PRIMARY KEY,
        VtigerID VARCHAR(50) NOT NULL UNIQUE,
        OportunidadNo VARCHAR(50),
        NombreOportunidad NVARCHAR(500),
        Monto DECIMAL(18,2),
        CuentaVtigerID VARCHAR(50),
        ContactoVtigerID VARCHAR(50),
        FechaCierre DATE,
        EtapaVenta NVARCHAR(100),
        Probabilidad INT,
        FuenteLead NVARCHAR(100),
        SiguientePaso NVARCHAR(500),
        Descripcion NVARCHAR(MAX),
        UsuarioAsignadoVtiger VARCHAR(50),
        FechaCreacionVtiger DATETIME,
        FechaModificacionVtiger DATETIME,
        FechaCreacionLocal DATETIME DEFAULT GETDATE(),
        FechaUltimaSync DATETIME DEFAULT GETDATE(),
        SincronizadoALocal BIT DEFAULT 0,
        LocalID UNIQUEIDENTIFIER NULL,
        INDEX IX_Vtiger_Oportunidades_Cuenta (CuentaVtigerID),
        INDEX IX_Vtiger_Oportunidades_Etapa (EtapaVenta),
        INDEX IX_Vtiger_Oportunidades_FechaCierre (FechaCierre)
    );
    PRINT 'Tabla Sync_Vtiger_Oportunidades creada';
END
GO

-- Tabla: Sync_Vtiger_Log (Historial de sincronizaciones)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Sync_Vtiger_Log]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Sync_Vtiger_Log] (
        LogID UNIQUEIDENTIFIER DEFAULT NEWID() PRIMARY KEY,
        RunID VARCHAR(50) NOT NULL,
        FechaInicio DATETIME NOT NULL,
        FechaFin DATETIME,
        TotalObtenidos INT DEFAULT 0,
        TotalInsertados INT DEFAULT 0,
        TotalActualizados INT DEFAULT 0,
        Errores INT DEFAULT 0,
        ResultadoJSON NVARCHAR(MAX),
        INDEX IX_Vtiger_Log_RunID (RunID),
        INDEX IX_Vtiger_Log_Fecha (FechaInicio DESC)
    );
    PRINT 'Tabla Sync_Vtiger_Log creada';
END
GO

-- Tabla: Sync_Vtiger_Config (Configuración de sincronización)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Sync_Vtiger_Config]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Sync_Vtiger_Config] (
        ConfigID UNIQUEIDENTIFIER DEFAULT NEWID() PRIMARY KEY,
        ConexionID VARCHAR(50) NOT NULL,
        ModulosActivos NVARCHAR(500) DEFAULT 'Leads,Contacts,Accounts,Potentials',
        IntervaloMinutos INT DEFAULT 15,
        DireccionSync VARCHAR(20) DEFAULT 'bidirectional',
        Activo BIT DEFAULT 1,
        UltimaEjecucion DATETIME,
        ProximaEjecucion DATETIME,
        FechaCreacion DATETIME DEFAULT GETDATE(),
        FechaModificacion DATETIME DEFAULT GETDATE()
    );
    PRINT 'Tabla Sync_Vtiger_Config creada';
    
    -- Insertar configuración por defecto
    INSERT INTO Sync_Vtiger_Config (ConexionID, ModulosActivos, IntervaloMinutos, DireccionSync, Activo)
    VALUES ('vtiger_env', 'Leads,Contacts,Accounts,Potentials', 15, 'bidirectional', 1);
    PRINT 'Configuración por defecto insertada';
END
GO

PRINT '=== DDL Vtiger Sync completado ===';
