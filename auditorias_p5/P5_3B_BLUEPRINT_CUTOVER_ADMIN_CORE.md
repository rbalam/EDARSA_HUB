# P5-3B — Blueprint Cutover SQL-First Admin CORE (NO-MONGO)

Fecha auditoría: 2026-06-07 (FASE 14). Read-only, contrato congelado.

## Contrato HTTP a preservar (baseline)
| Endpoint | OK | Error |
|----------|----|----|
| `GET /api/admin/core-connections` | 200 `{status:SUCCESS, data:[...], meta}` | — |
| `GET /api/admin/core-connections/{id}` | 200 `{status, data:{...}, meta}` | 404 `{"detail":"Conexión CORE no encontrada"}` |
| `POST /api/admin/core-connections/{id}/test` | 200 `{status, message, name, server_id, duration_ms, safe_error}` | 404 idem |

DATA_KEYS (list/item): `activo, api_key_configured, api_key_encrypted, api_url, config_origin, connection_type, created_at, database_name, host, id, name, password_configured, password_encrypted, port, system_type, system_type_normalized, tipo_conexion, updated_at, username, warnings`

## Estado real
- Los `GET` y `POST /test` YA son SQL-First (`execute_sql_query` sobre `dbo.Servidores_Conexiones`).
- Único residual Mongo (ya no-op vía `mongo_compat.get_mongo_db()→None`):
  1. `db.auditoria_core_admin.insert_one(log_data)` (función `_log_audit`, ~línea 114-116).
  2. `db.servidores_conexiones.find_one({'id':...})` → `mongodb_id`/`mongo_synced` (formateo item, ~línea 249-253).

## Tabla SQL destino auditoría: `dbo.Servidores_Conexiones_Log`
Columnas: `log_id (bigint, PK auto), servidor_id (uniqueidentifier), accion (nvarchar), datos_anteriores (nvarchar), datos_nuevos (nvarchar), usuario (nvarchar), fecha (datetime), ip_origen (nvarchar)`.

## Plan de cutover (bajo riesgo)
1. **Auditoría → SQL:** reescribir el insert Mongo de auditoría a `INSERT INTO dbo.Servidores_Conexiones_Log (servidor_id, accion, datos_nuevos, usuario, fecha) VALUES (...)`. Mapear `action`→`accion`, `log_data`→`datos_nuevos` (JSON), usuario actual→`usuario`, `GETDATE()`→`fecha`. Mantener try/except no-bloqueante.
2. **mongodb_id/mongo_synced:** dejar de consultar Mongo; leer `mongodb_id` de la fila SQL ya cargada (columna existe). `mongo_synced = mongodb_id is not None`. (O retirar ambos campos si el frontend no los usa — verificar primero.)
3. **Retirar `get_mongo_db`** del archivo una vez removidos (1) y (2).
4. **Validación:** re-correr snapshot FASE 14 y comparar contra contrato congelado (mismos status codes y DATA_KEYS). Guardrails `test_admin_core_*` + NO-MONGO deben seguir verdes.
5. **api_connections/repository.py** (lote separado): caché `api_connections_cache` y `api_health_logs` → tablas SQL o retirar (evaluar si el frontend depende de ellas; init ya es None).
6. **Retirar `core/mongo_compat`** solo cuando no queden consumidores vivos (grep `get_mongo_db|mongo_compat`).
