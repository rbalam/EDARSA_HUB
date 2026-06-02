/* ============================================================
   MIGRACIÓN: Vista Pública de Servidores_Conexiones (v2)
   Script: 006_crear_vista_servidores_conexiones_publico.sql
   Modo: migrate
   
   REGLA DE SEGURIDAD: El frontend NUNCA debe leer:
   ❌ password_encrypted
   ❌ api_key_encrypted  
   ❌ username
   ❌ query_ventas (SQL sensible)
   ❌ query_inventario (SQL sensible)
   ❌ query_movimientos (SQL sensible)
   ❌ api_url (puede contener tokens)
   ============================================================ */

CREATE OR ALTER VIEW dbo.Sistema_VW_Servidores_Conexiones_Publico
AS
SELECT
    -- Identificación
    id,
    nombre,
    system_type,
    tipo_conexion,
    
    -- Conexión (sin credenciales)
    host,
    port,
    database_name,
    
    -- Estado y visibilidad
    activo,
    visible_en_operaciones,
    visible_en_listado,
    es_editable_ui,
    es_eliminable_ui,
    
    -- Relaciones
    empresa_id,
    EmpresaID,
    sucursales,
    categorias,
    departamentos,
    tipos_movimiento,
    
    -- Configuración
    date_calculation_method,
    queries_configured,
    
    -- Sincronización
    fecha_ultima_sincronizacion,
    source_status,
    ultimo_error_sync,
    
    -- Auditoría
    created_at,
    updated_at,
    created_by,
    updated_by,
    
    -- Legacy
    mongodb_id
    
    -- EXCLUIDOS POR SEGURIDAD:
    -- password_encrypted
    -- api_key_encrypted
    -- username
    -- api_url
    -- query_ventas
    -- query_inventario
    -- query_movimientos
    
FROM dbo.Servidores_Conexiones;
GO
