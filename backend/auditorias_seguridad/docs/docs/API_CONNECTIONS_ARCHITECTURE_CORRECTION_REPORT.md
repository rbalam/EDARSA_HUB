# Corrección Arquitectónica: Conexiones API

## Fecha: 2026-04-29

## Resumen
Se corrigió la arquitectura del módulo de conexiones API para que EDARSAHUB SQL sea la fuente primaria de verdad.

## Arquitectura Implementada

### Fuente Primaria (Autoritativa)
- **EDARSAHUB SQL** (tabla `Servidores_Conexiones`)
- Todas las operaciones CRUD van primero a SQL
- Si SQL falla, la operación falla completamente

### Caché/Auxiliar (No Autoritativo)
- **MongoDB** (colección `api_connections_cache`)
- Solo se usa para:
  - Caché de lecturas
  - Logs de health checks
  - Estado temporal
- Si MongoDB falla, la operación no se bloquea

### Flujo de Sincronización
```
EDARSAHUB SQL → MongoDB (caché)
```
**NUNCA** al revés.

## Archivos Modificados

### Backend
| Archivo | Descripción |
|---------|-------------|
| `/app/backend/modules/api_connections/__init__.py` | Exportaciones actualizadas |
| `/app/backend/modules/api_connections/repository.py` | **Reescrito completamente** - Lee/escribe primero en EDARSAHUB SQL |
| `/app/backend/modules/api_connections/routes.py` | **Reescrito** - Manejo correcto de errores SQL vs MongoDB |
| `/app/backend/modules/comercial/adapters.py` | Actualizado para leer de EDARSAHUB SQL vía `get_api_connections_for_adapters()` |

### Funciones Clave en repository.py
| Función | Descripción |
|---------|-------------|
| `list_api_connections_sql()` | Lee conexiones desde SQL (fuente primaria) |
| `get_api_connection_sql()` | Obtiene una conexión por ID desde SQL |
| `create_api_connection()` | INSERT en SQL → Log → Caché MongoDB |
| `update_api_connection()` | UPDATE en SQL → Log → Caché MongoDB |
| `delete_api_connection()` | Soft delete en SQL → Log → Elimina caché |
| `_log_operation()` | Registra en `Servidores_Conexiones_Log` |
| `check_duplicate_api()` | Evita duplicados por nombre/URL |
| `get_api_connections_for_adapters()` | Para uso en adapters.py |

## Reglas Implementadas

1. ✅ **EDARSAHUB SQL es fuente primaria**
2. ✅ **MongoDB solo como caché/log/estado auxiliar**
3. ✅ **Crear/Editar/Eliminar escribe primero en SQL**
4. ✅ **Después de SQL, opcionalmente actualiza MongoDB caché**
5. ✅ **Si MongoDB falla, no impide guardar en SQL**
6. ✅ **Si SQL falla, no guarda en MongoDB**
7. ✅ **Bitácora de cambios** (Servidores_Conexiones_Log)
8. ✅ **Evita duplicados** (por nombre y URL)
9. ⚠️ **Usuarios/roles/alcance**: Pendiente integrar con RBAC completo
10. ✅ **Documentación de cambios**

## Pruebas Realizadas

### Backend (curl)
```bash
# Listar (lee de SQL)
GET /api/api-connections → 200 OK, source: EDARSAHUB_SQL

# Crear (escribe en SQL, luego caché)
POST /api/api-connections → 200 OK, source: EDARSAHUB_SQL

# Actualizar
PUT /api/api-connections/{id} → 200 OK, source: EDARSAHUB_SQL

# Eliminar (soft delete en SQL)
DELETE /api/api-connections/{id} → 200 OK, source: EDARSAHUB_SQL
```

### Verificación SQL Directa
```sql
-- Conexiones API en EDARSAHUB SQL
SELECT * FROM Servidores_Conexiones WHERE tipo_conexion = 'API_LOCAL'
-- Resultado: 2 conexiones (130° QRO LOCAL, ORIGEN LOCAL)

-- Bitácora
SELECT TOP 5 * FROM Servidores_Conexiones_Log ORDER BY fecha DESC
-- Resultado: Registros de CREATE para ambas conexiones
```

### Sincronización SQL → MongoDB
```bash
POST /api/api-connections/sync-cache
# Resultado: {"synced": 2, "errors": 0, "total": 2}
```

### Verificación MongoDB Caché
```javascript
db.api_connections_cache.find()
// Resultado: 2 docs con source: "SYNC_FROM_SQL"
```

## Datos Migrados a EDARSAHUB SQL

| Conexión | URL | Estado |
|----------|-----|--------|
| 130° QRO LOCAL | http://<REDACTED_EDARSAHUB_SQL_HOST>:8001/query | ✅ Activa |
| ORIGEN LOCAL | http://<REDACTED_EDARSAHUB_SQL_HOST>:8000/query | ✅ Activa |

## Endpoints Disponibles

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/api-connections | Lista conexiones (SQL) |
| GET | /api/api-connections/{id} | Obtiene una conexión (SQL) |
| POST | /api/api-connections | Crea conexión (SQL → Caché) |
| PUT | /api/api-connections/{id} | Actualiza conexión (SQL → Caché) |
| DELETE | /api/api-connections/{id} | Soft delete (SQL) |
| POST | /api/api-connections/test | Prueba URL nueva |
| POST | /api/api-connections/{id}/test | Prueba conexión existente |
| POST | /api/api-connections/sync-cache | Sincroniza SQL → MongoDB |
| GET | /api/api-connections/check-duplicate | Verifica duplicados |

## No Regresión

- Frontend sigue consumiendo `/api/api-connections` sin cambios
- adapters.py lee conexiones API usando `get_api_connections_for_adapters()`
- Tablero ejecutivo no afectado
- Módulo de servidores SQL no afectado
