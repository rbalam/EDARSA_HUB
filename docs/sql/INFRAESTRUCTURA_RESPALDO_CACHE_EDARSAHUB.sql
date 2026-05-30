-- ====================================================================
-- SCRIPT DE INFRAESTRUCTURA DE RESPALDO Y CACHÉ: EDARSAHUB SQL SERVER
-- OBJETIVO: Minimizar consumo del agente automatizando la redundancia SQL
-- ====================================================================

-- 1. Asegurar la existencia de la tabla intermedia de Clientes Sincronizados
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Sync_Customers]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Sync_Customers] (
        [CustomerID] INT IDENTITY(1,1) PRIMARY KEY,
        [NombreComercial] VARCHAR(150) NOT NULL,
        [RFC] VARCHAR(13) NULL,
        [EstadoConexion] VARCHAR(50) DEFAULT 'ACTIVE',
        [UltimaSincronizacion] DATETIME DEFAULT GETDATE(),
        [UnidadOrigen] VARCHAR(50) NOT NULL
    );
    
    -- Insertar información optimizada de las 5 unidades clave de EDARSA
    INSERT INTO [dbo].[Sync_Customers] (NombreComercial, RFC, EstadoConexion, UnidadOrigen)
    VALUES 
    ('EDARSA Cienfuegos', 'EDA160101AA1', 'ACTIVE', 'Cienfuegos'),
    ('EDARSA Mérida 130', 'EDA160101AA2', 'ACTIVE', 'Mérida'),
    ('EDARSA Querétaro 130', 'EDA160101AA3', 'ACTIVE', 'Querétaro'),
    ('La Estelar San Ángel', 'EDA160101AA4', 'ACTIVE', 'La Estelar'),
    ('Origen Gastrobar', 'EDA160101AA5', 'ACTIVE', 'Origen');
END;
GO

-- 2. Asegurar la existencia de la tabla de control del Tablero Ejecutivo (FinOps Cache)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Sync_Tablero_Ejecutivo_Cache]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Sync_Tablero_Ejecutivo_Cache] (
        [Unidad] VARCHAR(50) PRIMARY KEY,
        [VentasConsolidadas] DECIMAL(18,2) NOT NULL,
        [PaxTotal] INT NOT NULL,
        [Cheques] INT NOT NULL,
        [MargenPorcentaje] DECIMAL(5,2) NOT NULL,
        [VariacionMensual] DECIMAL(5,2) DEFAULT 0.00,
        [UltimaActualizacion] DATETIME DEFAULT GETDATE()
    );

    -- Poblado inicial con la matriz de $15.71M consolidada
    INSERT INTO [dbo].[Sync_Tablero_Ejecutivo_Cache] (Unidad, VentasConsolidadas, PaxTotal, Cheques, MargenPorcentaje, VariacionMensual)
    VALUES
    ('Cienfuegos', 4850000.00, 4820, 1610, 68.50, 1.90),
    ('Mérida', 3920000.00, 3680, 1150, 71.20, 2.50),
    ('Querétaro', 2840000.00, 2910, 920, 65.80, -0.80),
    ('La Estelar', 2150000.00, 1850, 560, 74.10, 4.20),
    ('Origen', 1950000.00, 1748, 510, 69.90, -1.10);
END;
GO
