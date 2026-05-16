-- =============================================================================
-- EDARSA HUB - CATÁLOGO MAESTRO DE SISTEMAS Y CAPACIDADES
-- DDL FASE 2: Creación de Tablas SQL-First
-- =============================================================================
-- 
-- OBJETIVO: Crear infraestructura SQL para motor de capacidades por sistema.
-- REGLAS: IF NOT EXISTS, idempotente, no destructivo.
-- FUENTE: EDARSAHUB SQL Server
--
-- FECHA: 2025-12-XX
-- AUTOR: Arquitecto DBA
-- =============================================================================

USE EDARSAHUB;
GO

-- =============================================================================
-- TABLA 1: Sistema_Capacidades
-- Almacena las capacidades disponibles por tipo de sistema.
-- =============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Sistema_Capacidades')
BEGIN
    CREATE TABLE Sistema_Capacidades (
        SistemaCapacidadID INT IDENTITY(1,1) PRIMARY KEY,
        
        -- FK a Sistema_Tipos existente
        SistemaTipoID INT NOT NULL,
        
        -- Identificador único de la capacidad
        CodigoCapacidad VARCHAR(50) NOT NULL,
        
        -- Descripción legible
        Descripcion NVARCHAR(200) NULL,
        
        -- Requisitos técnicos
        RequiereApiLocal BIT DEFAULT 0,
        RequiereSqlDirecto BIT DEFAULT 1,
        
        -- Configuración específica en JSON (query, parámetros, etc.)
        ConfiguracionJSON NVARCHAR(MAX) NULL,
        
        -- Metadatos
        Activo BIT DEFAULT 1,
        CreatedAt DATETIME DEFAULT GETDATE(),
        UpdatedAt DATETIME DEFAULT GETDATE(),
        
        -- Constraints
        CONSTRAINT FK_SistemaCapacidades_SistemaTipos 
            FOREIGN KEY (SistemaTipoID) REFERENCES Sistema_Tipos(SistemaTipoID),
        CONSTRAINT UQ_SistemaCapacidades_TipoCapacidad 
            UNIQUE (SistemaTipoID, CodigoCapacidad)
    );
    
    PRINT 'Tabla Sistema_Capacidades creada exitosamente.';
END
ELSE
BEGIN
    PRINT 'Tabla Sistema_Capacidades ya existe. Omitiendo creación.';
END
GO

-- Índices para Sistema_Capacidades
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_SistemaCapacidades_Codigo')
BEGIN
    CREATE INDEX IX_SistemaCapacidades_Codigo 
    ON Sistema_Capacidades(CodigoCapacidad) 
    WHERE Activo = 1;
    PRINT 'Índice IX_SistemaCapacidades_Codigo creado.';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_SistemaCapacidades_SistemaTipo')
BEGIN
    CREATE INDEX IX_SistemaCapacidades_SistemaTipo 
    ON Sistema_Capacidades(SistemaTipoID) 
    WHERE Activo = 1;
    PRINT 'Índice IX_SistemaCapacidades_SistemaTipo creado.';
END
GO


-- =============================================================================
-- TABLA 2: Sistema_ModulosVisibilidad
-- Define en qué módulos/menús aparece cada tipo de sistema.
-- =============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Sistema_ModulosVisibilidad')
BEGIN
    CREATE TABLE Sistema_ModulosVisibilidad (
        ModuloVisibilidadID INT IDENTITY(1,1) PRIMARY KEY,
        
        -- FK a Sistema_Tipos existente
        SistemaTipoID INT NOT NULL,
        
        -- Código del módulo (EXPLORADOR_BD, COMERCIAL, FINANZAS, etc.)
        CodigoModulo VARCHAR(50) NOT NULL,
        
        -- Descripción del módulo
        DescripcionModulo NVARCHAR(100) NULL,
        
        -- Visibilidad
        Visible BIT DEFAULT 1,
        
        -- Orden en menú/filtro
        OrdenMenu INT DEFAULT 0,
        
        -- Configuración específica (labels, iconos, etc.)
        ConfiguracionJSON NVARCHAR(MAX) NULL,
        
        -- Metadatos
        Activo BIT DEFAULT 1,
        CreatedAt DATETIME DEFAULT GETDATE(),
        
        -- Constraints
        CONSTRAINT FK_SistemaModulos_SistemaTipos 
            FOREIGN KEY (SistemaTipoID) REFERENCES Sistema_Tipos(SistemaTipoID),
        CONSTRAINT UQ_SistemaModulos_TipoModulo 
            UNIQUE (SistemaTipoID, CodigoModulo)
    );
    
    PRINT 'Tabla Sistema_ModulosVisibilidad creada exitosamente.';
END
ELSE
BEGIN
    PRINT 'Tabla Sistema_ModulosVisibilidad ya existe. Omitiendo creación.';
END
GO

-- Índices para Sistema_ModulosVisibilidad
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_SistemaModulos_Modulo')
BEGIN
    CREATE INDEX IX_SistemaModulos_Modulo 
    ON Sistema_ModulosVisibilidad(CodigoModulo) 
    WHERE Activo = 1 AND Visible = 1;
    PRINT 'Índice IX_SistemaModulos_Modulo creado.';
END
GO


-- =============================================================================
-- TABLA 3: Sistema_TiposVariantes (Opcional - para mapeo de aliases)
-- Permite mapear variantes de nombre a código canónico.
-- =============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Sistema_TiposVariantes')
BEGIN
    CREATE TABLE Sistema_TiposVariantes (
        VarianteID INT IDENTITY(1,1) PRIMARY KEY,
        
        -- FK a Sistema_Tipos
        SistemaTipoID INT NOT NULL,
        
        -- Variante de nombre (MPRO, ManagementPro, MANAGMENT PRO, etc.)
        VarianteNombre VARCHAR(50) NOT NULL,
        
        -- ¿Es el nombre canónico?
        EsCanonico BIT DEFAULT 0,
        
        -- Metadatos
        Activo BIT DEFAULT 1,
        CreatedAt DATETIME DEFAULT GETDATE(),
        
        -- Constraints
        CONSTRAINT FK_SistemaTiposVariantes_SistemaTipos 
            FOREIGN KEY (SistemaTipoID) REFERENCES Sistema_Tipos(SistemaTipoID),
        CONSTRAINT UQ_SistemaTiposVariantes_Nombre 
            UNIQUE (VarianteNombre)
    );
    
    PRINT 'Tabla Sistema_TiposVariantes creada exitosamente.';
END
ELSE
BEGIN
    PRINT 'Tabla Sistema_TiposVariantes ya existe. Omitiendo creación.';
END
GO

-- Índice para búsqueda rápida de variantes
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_SistemaTiposVariantes_Nombre')
BEGIN
    CREATE INDEX IX_SistemaTiposVariantes_Nombre 
    ON Sistema_TiposVariantes(VarianteNombre) 
    WHERE Activo = 1;
    PRINT 'Índice IX_SistemaTiposVariantes_Nombre creado.';
END
GO


-- =============================================================================
-- VERIFICACIÓN POST-CREACIÓN
-- =============================================================================

SELECT 'VERIFICACIÓN DE TABLAS CREADAS' AS Seccion;

SELECT 
    t.name AS Tabla,
    CASE WHEN t.name IS NOT NULL THEN 'EXISTE' ELSE 'NO EXISTE' END AS Estado,
    (SELECT COUNT(*) FROM sys.columns WHERE object_id = t.object_id) AS NumColumnas
FROM sys.tables t
WHERE t.name IN ('Sistema_Capacidades', 'Sistema_ModulosVisibilidad', 'Sistema_TiposVariantes')
ORDER BY t.name;

SELECT 'VERIFICACIÓN DE ÍNDICES CREADOS' AS Seccion;

SELECT 
    i.name AS Indice,
    t.name AS Tabla,
    CASE WHEN i.name IS NOT NULL THEN 'EXISTE' ELSE 'NO EXISTE' END AS Estado
FROM sys.indexes i
JOIN sys.tables t ON i.object_id = t.object_id
WHERE i.name IN (
    'IX_SistemaCapacidades_Codigo',
    'IX_SistemaCapacidades_SistemaTipo',
    'IX_SistemaModulos_Modulo',
    'IX_SistemaTiposVariantes_Nombre'
)
ORDER BY i.name;

PRINT '=============================================================================';
PRINT 'DDL FASE 2 completado. Tablas e índices verificados.';
PRINT 'SIGUIENTE PASO: Ejecutar SEED FASE 3 para cargar datos iniciales.';
PRINT '=============================================================================';
GO
