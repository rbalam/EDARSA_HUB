# EDARSAHUB – Mongo Sunset / SQL-First
## Cierre P4 Communications parcial – 23-Jun-2026

## Estado validado

- Repository, dispatcher, service, dedup, template service y audit service quedaron sin runtime Mongo operativo en los bloques migrados.
- `SERVER_IMPORT_OK` = OK.
- `python3 -m py_compile` = OK.
- SQL columnas:
  - `dbo.Operativo_Notificaciones_Log` = OK.
  - `dbo.Usuario_Catalogo` = OK.
- SQL queries:
  - `Operativo_Notificaciones_Log` = OK, 0 filas.
  - `Usuario_Catalogo` = OK, 1+ fila.
- Frontend build = OK con warnings ESLint existentes.

## Pendiente

- Confirmar montaje/ruta real de endpoints communications; `/api/communications/config` y `/providers` respondieron 404.
- Revisar scripts/routes restantes de communications antes de declarar P4 total cerrado.

