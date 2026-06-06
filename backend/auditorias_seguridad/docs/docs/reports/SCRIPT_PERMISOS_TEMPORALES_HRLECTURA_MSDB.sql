-- ============================================================================
-- SCRIPT PARA OTORGAR PERMISOS TEMPORALES A HRLectura EN msdb
-- ============================================================================
-- Ejecutar con usuario 'sa' en SSMS o herramienta SQL
-- Servidor: ns559627 (54.39.104.176)
-- Fecha: 2025-12-19
-- Propósito: Permitir diagnóstico de SQL Server Agent Jobs
-- ============================================================================

-- PASO 1: Conectar a msdb
USE msdb;
GO

-- PASO 2: Agregar HRLectura al rol SQLAgentReaderRole
-- Este rol permite SOLO LECTURA de jobs, schedules e historial
ALTER ROLE SQLAgentReaderRole ADD MEMBER HRLectura;
GO

-- PASO 3: Verificar que se agregó correctamente
SELECT 
    dp.name AS user_name,
    r.name AS role_name
FROM sys.database_role_members drm
INNER JOIN sys.database_principals dp ON drm.member_principal_id = dp.principal_id
INNER JOIN sys.database_principals r ON drm.role_principal_id = r.principal_id
WHERE dp.name = 'HRLectura';
GO

-- Resultado esperado:
-- user_name    | role_name
-- -------------|------------------
-- HRLectura    | SQLAgentReaderRole

-- ============================================================================
-- NOTA: Después del diagnóstico, para REVOCAR los permisos:
-- ============================================================================
-- USE msdb;
-- ALTER ROLE SQLAgentReaderRole DROP MEMBER HRLectura;
-- GO
-- ============================================================================
