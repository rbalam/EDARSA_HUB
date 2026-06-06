# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-02T16:17:28.980053
- Modo: `diagnostic`
- Servidor: `<REDACTED_EDARSAHUB_SQL_HOST>`
- Base de datos: `EDARSAHUB`
- Script: `/app/backend/database/diagnostics/016_verificar_datos_rbac.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecución completada.

### Batch 1
- Tipo: SELECT
- Columnas: status
- Filas: 1
- Preview (primeras 20 filas):
```
  {'status': 'Usuario_Modulos EXISTE'}
```


## SQL ejecutado / revisado
```sql
/* ============================================================
   DIAGNÓSTICO DATOS EXISTENTES EN TABLAS RBAC CANÓNICO
   ============================================================ */

-- Verificar si Usuario_Modulos existe y tiene datos
IF OBJECT_ID('dbo.Usuario_Modulos', 'U') IS NOT NULL
BEGIN
    SELECT 'Usuario_Modulos EXISTE' AS status;
    SELECT COUNT(*) AS total_registros FROM Usuario_Modulos;
    SELECT TOP 20 * FROM Usuario_Modulos ORDER BY ModuloID;
END
ELSE
BEGIN
    SELECT 'Usuario_Modulos NO EXISTE' AS status;
END

-- Verificar si Usuario_Roles existe y tiene datos
IF OBJECT_ID('dbo.Usuario_Roles', 'U') IS NOT NULL
BEGIN
    SELECT 'Usuario_Roles EXISTE' AS status;
    SELECT COUNT(*) AS total_registros FROM Usuario_Roles;
    SELECT TOP 20 * FROM Usuario_Roles ORDER BY RolID;
END
ELSE
BEGIN
    SELECT 'Usuario_Roles NO EXISTE' AS status;
END

-- Verificar si Usuario_Acciones existe y tiene datos
IF OBJECT_ID('dbo.Usuario_Acciones', 'U') IS NOT NULL
BEGIN
    SELECT 'Usuario_Acciones EXISTE' AS status;
    SELECT COUNT(*) AS total_registros FROM Usuario_Acciones;
    SELECT TOP 20 * FROM Usuario_Acciones ORDER BY AccionID;
END
ELSE
BEGIN
    SELECT 'Usuario_Acciones NO EXISTE' AS status;
END

-- Verificar Sistema_RBAC_* (transicionales)
SELECT 
    TABLE_NAME AS tabla_transicional
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME LIKE 'Sistema_RBAC_%'
ORDER BY TABLE_NAME;

```