# Cavas Corporativas - SQL Migration Channel

Canal externo al Universal Worker para ejecutar la migracion certificada `backend/database/migrations/20260907_cavas_corporativas_core.sql`.

## Guardas
- Solo push en `Edarsahub_Desarrollo`.
- `Edarsahub_Produccion` no participa.
- Migration blob SHA fijado a `072153e91c8721cbfa09cf6a0bb770ffab814494`.
- Preflight SQL con `HRLectura`.
- La ejecucion exige `EDARSAHUB_SQL_MIGRATION_USER` y `EDARSAHUB_SQL_MIGRATION_PASSWORD` en el environment/repository secrets de GitHub; `HRLectura` esta prohibido como writer.
- Usa `backend/tools/edarsahub_sql_runner.py --mode migrate` con `EDARSAHUB_ALLOW_MIGRATIONS=true`.
- Post-check vuelve a `HRLectura`, verifica 8 tablas, 8 PK, indices requeridos, cero FK externa y cero filas sembradas.
- Publica artifact de evidencia con preflight, salida de migracion, reporte del runner y postcheck.

## Trigger
La presencia/cambio de `ops/migrations/requests/CAVAS-CORPORATIVAS-CORE-20260907.execute` en Development dispara el workflow una sola vez por push.
