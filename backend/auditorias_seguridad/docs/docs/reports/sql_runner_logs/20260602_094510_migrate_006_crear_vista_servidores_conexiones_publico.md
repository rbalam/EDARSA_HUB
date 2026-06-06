# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-02T09:45:10.496774
- Modo: `migrate`
- Servidor: `<REDACTED_EDARSAHUB_SQL_HOST>`
- Base de datos: `EDARSAHUB`
- Script: `/app/backend/database/migrations/006_crear_vista_servidores_conexiones_publico.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecución completada.

### Batch 1
- Tipo: Comando
- Filas afectadas: -1


## SQL ejecutado / revisado
```sql
/* ============================================================
   MIGRACIÓN: Vista Pública de Servidores_Conexiones
   Script: 006_crear_vista_servidores_conexiones_publico.sql
   Modo: migrate
   
   REGLA DE SEGURIDAD: El frontend NUNCA debe leer:
   - password_encrypted
   - api_key_encrypted
   - username (si no es necesario)
   - query_ventas (si contiene SQL sensible)
   - query_inventario (si contiene SQL sensible)
   ============================================================ */

CREATE OR ALTER VIEW dbo.Sistema_VW_Servidores_Conexiones_Publico
AS
SELECT
    id,
    nombre,
    system_type,
    tipo_conexion,
    host,
    port,
    database_name,
    activo,
    visible_en_operaciones,
    visible_en_listado,
    es_editable_ui,
    es_eliminable_ui,
    empresa_id,
    EmpresaID,
    sucursales,
    categorias,
    departamentos,
    date_calculation_method,
    queries_configured,
    fecha_ultima_sincronizacion,
    source_status,
    ultimo_error_sync,
    created_at,
    updated_at,
    created_by,
    updated_by
FROM dbo.Servidores_Conexiones;
GO

```