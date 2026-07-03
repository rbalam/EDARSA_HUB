# EDARSAHUB SQL Runner Report

- Fecha: 2026-07-03T03:54:00.874432
- Modo: `validate`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/tmp/validate_usuario_menu_favoritos_indexes.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecución completada.

### Batch 1
- Tipo: SELECT
- Columnas: index_name, is_unique
- Filas: 3
- Preview (primeras 20 filas):
```
  {'index_name': 'IX_UsuarioMenuFavoritos_Usuario_Activo_Orden', 'is_unique': False}
  {'index_name': 'PK__Usuario___CF13F666DF89F4A8', 'is_unique': True}
  {'index_name': 'UX_UsuarioMenuFavoritos_Usuario_Ruta', 'is_unique': True}
```


## SQL ejecutado / revisado
```sql
SELECT
    i.name AS index_name,
    i.is_unique
FROM sys.indexes i
WHERE i.object_id = OBJECT_ID('dbo.Usuario_MenuFavoritos')
ORDER BY i.name;

```