# EDARSAHUB – Mongo Sunset / SQL-First
## Cierre P2B Fase2 Operativo restante – 23-Jun-2026

## Estado validado

- Se eliminaron accesos Mongo runtime restantes en:
  - `backend/modules/fase2_operativo/routes/notificaciones_routes.py`
  - `backend/modules/fase2_operativo/routes/documentos_routes.py`
  - `backend/modules/fase2_operativo/routes/sla_routes.py`

## Migraciones realizadas

- `db.tareas_inventario` → `dbo.Tareas_Inventario`
- `db.notificaciones_log` → `dbo.Operativo_Notificaciones_Log`
- `db.documentos_generados` → `dbo.Operativo_DocumentosGenerados`
- `db.users` → `dbo.Usuario_Catalogo`

## Validación

- `python3 -m py_compile` en los 3 archivos = OK.
- Runtime Mongo en `backend/modules/fase2_operativo/routes` = 0, excluyendo backups/comentarios.

## Reglas conservadas

- Sin tablas nuevas.
- SQL Server como fuente operativa.
- Cambios quirúrgicos por archivo.
- Backups locales fuera de Git.
