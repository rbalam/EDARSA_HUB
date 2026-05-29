-- =============================================================================
-- SCRIPT: EXTENSION TABLA ROLES - CONTROL DE ACCESO A MÓDULOS
-- OBJETIVO: Habilitar permisos granulares por rol para menús del sistema
-- =============================================================================

-- Extensión de la tabla Roles para control de acceso
ALTER TABLE [dbo].[Roles] ADD [ModuleAccess] BIT DEFAULT 0;

-- Habilitar acceso al Menú Comercial para el rol analista
UPDATE [dbo].[Roles] 
SET [ModuleAccess] = 1 
WHERE [NombreRol] = 'Analista Comercial';
