# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-02T16:17:05.156218
- Modo: `diagnostic`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/app/backend/database/diagnostics/015_diagnostico_completo_rbac_canonico.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecución completada.

### Batch 1
- Tipo: SELECT
- Columnas: diagnostico, esquema, tabla, tipo
- Filas: 23
- Preview (primeras 20 filas):
```
  {'diagnostico': 'TABLAS_EXISTENTES', 'esquema': 'dbo', 'tabla': 'Usuario_Acciones', 'tipo': 'BASE TABLE'}
  {'diagnostico': 'TABLAS_EXISTENTES', 'esquema': 'dbo', 'tabla': 'Usuario_AlmacenesAsignacion', 'tipo': 'BASE TABLE'}
  {'diagnostico': 'TABLAS_EXISTENTES', 'esquema': 'dbo', 'tabla': 'Usuario_Autorizaciones', 'tipo': 'BASE TABLE'}
  {'diagnostico': 'TABLAS_EXISTENTES', 'esquema': 'dbo', 'tabla': 'Usuario_AutorizacionesDetalle', 'tipo': 'BASE TABLE'}
  {'diagnostico': 'TABLAS_EXISTENTES', 'esquema': 'dbo', 'tabla': 'Usuario_Catalogo', 'tipo': 'BASE TABLE'}
  {'diagnostico': 'TABLAS_EXISTENTES', 'esquema': 'dbo', 'tabla': 'Usuario_EmpresasAsignacion', 'tipo': 'BASE TABLE'}
  {'diagnostico': 'TABLAS_EXISTENTES', 'esquema': 'dbo', 'tabla': 'Usuario_LogAccesos', 'tipo': 'BASE TABLE'}
  {'diagnostico': 'TABLAS_EXISTENTES', 'esquema': 'dbo', 'tabla': 'Usuario_LogActividades', 'tipo': 'BASE TABLE'}
  {'diagnostico': 'TABLAS_EXISTENTES', 'esquema': 'dbo', 'tabla': 'Usuario_LogRBACVerificacion', 'tipo': 'BASE TABLE'}
  {'diagnostico': 'TABLAS_EXISTENTES', 'esquema': 'dbo', 'tabla': 'Usuario_LogRecuperacion', 'tipo': 'BASE TABLE'}
```


## SQL ejecutado / revisado
```sql
/* ============================================================
   DIAGNÓSTICO COMPLETO TABLAS RBAC CANONICO (Usuario_*)
   Verifica existencia de tablas, estructura y datos existentes.
   No modifica datos.
   ============================================================ */

-- 1. Verificar qué tablas Usuario_* existen
SELECT 
    'TABLAS_EXISTENTES' AS diagnostico,
    TABLE_SCHEMA AS esquema,
    TABLE_NAME AS tabla,
    TABLE_TYPE AS tipo
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME LIKE 'Usuario_%'
ORDER BY TABLE_NAME;

-- 2. Verificar qué tablas Sistema_RBAC_* existen (transicionales)
SELECT 
    'TABLAS_TRANSICIONALES' AS diagnostico,
    TABLE_SCHEMA AS esquema,
    TABLE_NAME AS tabla,
    TABLE_TYPE AS tipo
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME LIKE 'Sistema_RBAC_%'
ORDER BY TABLE_NAME;

-- 3. Estructura detallada de Usuario_Modulos (si existe)
SELECT
    'Usuario_Modulos' AS tabla,
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Usuario_Modulos'
ORDER BY ORDINAL_POSITION;

-- 4. Estructura detallada de Usuario_Roles (si existe)
SELECT
    'Usuario_Roles' AS tabla,
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Usuario_Roles'
ORDER BY ORDINAL_POSITION;

-- 5. Estructura detallada de Usuario_Acciones (si existe)
SELECT
    'Usuario_Acciones' AS tabla,
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Usuario_Acciones'
ORDER BY ORDINAL_POSITION;

-- 6. Datos existentes en Usuario_Modulos
SELECT TOP 50 * FROM Usuario_Modulos;

-- 7. Datos existentes en Usuario_Roles
SELECT TOP 50 * FROM Usuario_Roles;

-- 8. Datos existentes en Usuario_Acciones
SELECT TOP 50 * FROM Usuario_Acciones;

-- 9. Datos existentes en Usuario_PermisosRolModulo
SELECT TOP 50 * FROM Usuario_PermisosRolModulo;

```