-- =============================================================================
-- SCRIPT: FACT TABLES - VENTAS CONSOLIDADAS Y CONFIGURACIÓN HORARIOS
-- OBJETIVO: Estructura de agregación diaria Multi-Tenant para análisis BI
-- =============================================================================

-- Tabla: Fact_Ventas_Consolidadas
-- Almacena la agregación diaria de comandas siguiendo el patrón Multi-Tenant
CREATE TABLE [dbo].[Fact_Ventas_Consolidadas] (
    [Id] INT IDENTITY(1,1) PRIMARY KEY,
    [TenantID] INT NOT NULL, -- ID de la empresa/sucursal
    [Fecha] DATE NOT NULL,
    [Periodo] NVARCHAR(20), -- Desayuno, Comida, Cena
    [IdProducto] INT NOT NULL,
    [Cantidad] DECIMAL(18,2),
    [ImporteNeto] DECIMAL(18,2),
    [Propina] DECIMAL(18,2),
    [Pax] INT,
    [IdAreaVenta] INT,
    [IdFormaCobro] INT,
    CONSTRAINT [FK_Ventas_Empresa] FOREIGN KEY ([TenantID]) REFERENCES [dbo].[Companies]([Id])
);

-- Tabla de Configuración de Horarios
CREATE TABLE [dbo].[Config_Horarios] (
    [Id] INT IDENTITY(1,1) PRIMARY KEY,
    [TenantID] INT NOT NULL,
    [NombrePeriodo] NVARCHAR(50), 
    [HoraInicio] TIME,
    [HoraFin] TIME
);

-- Ampliación del Catálogo de Productos existente
ALTER TABLE [dbo].[Products] ADD 
    [Casa] NVARCHAR(100),
    [PorcentajeAlcohol] DECIMAL(5,2),
    [URL_Imagen] NVARCHAR(500);
