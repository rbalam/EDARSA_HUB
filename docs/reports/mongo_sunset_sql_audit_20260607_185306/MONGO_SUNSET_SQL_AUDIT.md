# Mongo Sunset Fase 5 — Registro SQL de lista blanca

Fecha: 2026-06-07T18:53:09

## Estado

✅ Registro SQL completado en modo NO destructivo. No se borró Mongo ni se tocó runtime.

## Conexión

- Modo: `core.db.execute_sql_query` (pool autocommit=True)
- ODBC/pyodbc: NO USADO
- Usuario SQL: `HRLectura` (rol db_owner verificado)

## Fuente

- Lista blanca: `/app/docs/reports/mongo_delete_whitelist_20260607_183030/MONGO_DELETE_WHITELIST_20260607_183030.json`

## Tabla de auditoría

- `dbo.Sistema_MongoSunset_Auditoria` (creada idempotente)

## Resultado

- BatchID: `92BEF962-9F88-4C2E-87E0-D5080727E553`
- Filas lista blanca: **31**
- Insertadas nuevas: **31**
- Ya existentes/omitidas: **0**
- Total filas en tabla: **31**

## Resumen acumulado SQL

| Estado | AprobarBorrado | Recomendación | Registros |
|---|---|---|---:|
| PENDIENTE_AUTORIZACION | NO | BASE_DE_PRUEBAS_CANDIDATA_A_BORRADO | 24 |
| PENDIENTE_AUTORIZACION | NO | CANDIDATA_A_BORRADO_POSTERIOR | 7 |

## Siguiente paso

Usuario marca `aprobar_borrado=SI` en el CSV editable solo donde autorice. El script de borrado futuro (con re-respaldo) actualizará Estado/AutorizadoPor en esta tabla y registrará el resultado del drop.
