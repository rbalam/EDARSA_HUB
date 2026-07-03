# EDARSAHUB SQL Runner Report

- Fecha: 2026-07-03T03:44:01.329277
- Modo: `validate`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/tmp/validate_usuario_menu_favoritos_full.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecución completada.

### Batch 1
- Tipo: SELECT
- Columnas: tipo, nombre, valor
- Filas: 13
- Preview (primeras 20 filas):
```
  {'tipo': 'COLUMNA', 'nombre': 'Activo', 'valor': 'bit|nullable=NO'}
  {'tipo': 'COLUMNA', 'nombre': 'CreatedBy', 'valor': 'nvarchar|nullable=YES'}
  {'tipo': 'COLUMNA', 'nombre': 'FechaAlta', 'valor': 'datetime2|nullable=NO'}
  {'tipo': 'COLUMNA', 'nombre': 'FechaModificacion', 'valor': 'datetime2|nullable=YES'}
  {'tipo': 'COLUMNA', 'nombre': 'ModifiedBy', 'valor': 'nvarchar|nullable=YES'}
  {'tipo': 'COLUMNA', 'nombre': 'Orden', 'valor': 'int|nullable=NO'}
  {'tipo': 'COLUMNA', 'nombre': 'Ruta', 'valor': 'nvarchar|nullable=NO'}
  {'tipo': 'COLUMNA', 'nombre': 'UsuarioID', 'valor': 'int|nullable=NO'}
  {'tipo': 'COLUMNA', 'nombre': 'UsuarioMenuFavoritoID', 'valor': 'int|nullable=NO'}
  {'tipo': 'INDICE', 'nombre': 'IX_UsuarioMenuFavoritos_Usuario_Activo_Orden', 'valor': 'is_unique=0'}
```


## SQL ejecutado / revisado
```sql
SELECT
    'TABLA' AS tipo,
    'Usuario_MenuFavoritos' AS nombre,
    CAST(CASE WHEN OBJECT_ID('dbo.Usuario_MenuFavoritos', 'U') IS NULL THEN 0 ELSE 1 END AS NVARCHAR(100)) AS valor

UNION ALL

SELECT
    'COLUMNA' AS tipo,
    COLUMN_NAME AS nombre,
    CONCAT(DATA_TYPE, '|nullable=', IS_NULLABLE) AS valor
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'dbo'
  AND TABLE_NAME = 'Usuario_MenuFavoritos'

UNION ALL

SELECT
    'INDICE' AS tipo,
    i.name AS nombre,
    CONCAT('is_unique=', i.is_unique) AS valor
FROM sys.indexes i
WHERE i.object_id = OBJECT_ID('dbo.Usuario_MenuFavoritos')

ORDER BY tipo, nombre;

```