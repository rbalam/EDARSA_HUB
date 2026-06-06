# FASE 3B - Migración / Control de `servers` hacia EDARSAHUB SQL

**Fecha de ejecución:** 2025-12-XX  
**Estado:** COMPLETADO (Consolidación)

---

## 1. Resumen Ejecutivo

La FASE 3B implementó el **Server Registry Central** que convierte EDARSAHUB SQL en la fuente primaria de configuración de servidores, dejando MongoDB como fallback legacy temporal.

**Hallazgo clave:** Los 9 servidores ya estaban sincronizados entre MongoDB y SQL mediante el campo `mongodb_id`. No se requirió migración de datos.

---

## 2. Hallazgo: Servidores Ya Sincronizados

### Tabla de Mapeo MongoDB ↔ SQL

| MongoDB ID | SQL ID | Nombre | system_type | Sync Status |
|------------|--------|--------|-------------|-------------|
| a5547321-1139-4... | a5547321... | 130° MERIDA | SoftRestaurant | ✅ Sincronizado |
| 6d053c22-523e-4... | 6d053c22... | CIENFUEGOS | SoftRestaurant | ✅ Sincronizado |
| 6d859026-710a-4... | 6d859026... | CIENFUEGOS TABLAJERIA | SoftRestaurant | ✅ Sincronizado |
| f8a9049a-96e8-4... | f8a9049a... | EDARSA HUB | EDARSA_HUB | ✅ Sincronizado (CORE) |
| b5175237-5e57-4... | b5175237... | HR2020 ESCRITURA | MPRO | ✅ Sincronizado |
| a5ff0e25-f029-4... | a5ff0e25... | LA ESTELAR | SoftRestaurant | ✅ Sincronizado |
| 1b230a06-ffaf-4... | 1b230a06... | ManagmentPro | MPRO | ✅ Sincronizado |
| d1d8c70f-c3d0-4... | d1d8c70f... | MPRO TABLAJERIA | MPRO | ✅ Sincronizado |
| d8425038-5e57-4... | d8425038... | PRUEBAS SOFTRESTAURANT | SoftRestaurant | ✅ Sincronizado |

**Total SQL:** 9 servidores  
**Total MongoDB:** 9 servidores  
**Estado:** 100% sincronizado - No se requiere migración

---

## 3. Estado Inicial vs Final

| Aspecto | Antes | Después |
|---------|-------|---------|
| Fuente primaria | MongoDB | EDARSAHUB SQL |
| Fuente fallback | N/A | MongoDB (legacy) |
| Endpoint `/api/servers` | Leía MongoDB | Lee SQL via registry |
| Normalización system_type | Parcial | Completa via utils |
| Exposición de secretos | password en respuesta | Solo `password_configured` |
| Campo `config_origin` | No existía | `EDARSAHUB_SQL` o `MONGODB_LEGACY` |

---

## 4. Tabla SQL Detectada

**Nombre:** `Servidores_Conexiones`  
**Base de datos:** `EDARSAHUB`  
**Host:** `<REDACTED_EDARSAHUB_SQL_HOST>`

### Columnas

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | uniqueidentifier | UUID del servidor |
| nombre | varchar | Nombre del servidor |
| system_type | varchar | Tipo de sistema (MPRO, SoftRestaurant, etc.) |
| tipo_conexion | varchar | DATA_SOURCE o CORE |
| host | varchar | Host SQL Server |
| port | int | Puerto (default 1433) |
| database_name | varchar | Nombre de la base de datos |
| username | varchar | Usuario SQL |
| password_encrypted | varchar | Password (encriptado) |
| api_url | varchar | URL de API local |
| api_key_encrypted | varchar | API key (encriptado) |
| activo | bit | Si está activo |
| visible_en_operaciones | bit | Si aparece en dashboards |
| visible_en_listado | bit | Si aparece en menú de servidores |
| es_editable_ui | bit | Si se puede editar desde UI |
| es_eliminable_ui | bit | Si se puede eliminar desde UI |
| empresa_id | uniqueidentifier | Empresa asociada |
| sucursales | nvarchar(max) | JSON con sucursales |
| categorias | nvarchar(max) | JSON con categorías |
| departamentos | nvarchar(max) | JSON con departamentos |
| date_calculation_method | varchar | Método de cálculo de fechas |
| queries_configured | bit | Si tiene queries configurados |
| query_ventas | nvarchar(max) | JSON con query de ventas |
| query_inventario | nvarchar(max) | JSON con query de inventario |
| query_movimientos | nvarchar(max) | JSON con query de movimientos |
| created_at | datetime | Fecha de creación |
| updated_at | datetime | Fecha de actualización |
| created_by | uniqueidentifier | Usuario que creó |
| updated_by | uniqueidentifier | Usuario que actualizó |
| mongodb_id | varchar | UUID original de MongoDB |

---

## 5. Archivos Creados

| Archivo | Propósito |
|---------|-----------|
| `/app/backend/core/server_registry.py` | Registry central para resolución de servidores |

### Funciones exportadas por `server_registry.py`

| Función | Propósito |
|---------|-----------|
| `get_server_by_id(server_id, db, prefer_sql, allow_mongo_fallback, mask_secrets)` | Obtiene un servidor por ID |
| `list_servers(db, user, prefer_sql, allow_mongo_fallback, ...)` | Lista servidores con filtros |
| `get_server_sucursales(server_id, db, prefer_sql, allow_mongo_fallback)` | Obtiene sucursales de un servidor |
| `filter_servers_by_user_permissions(servers, user)` | Filtra por permisos RBAC |
| `resolve_server_context(server_id, sucursal_id, ...)` | Resuelve contexto completo |
| `normalize_server_record(record, source)` | Normaliza registro con campos legacy |
| `mask_sensitive_fields(server)` | Enmascara passwords y api_keys |
| `normalize_system_type(system_type)` | Normaliza system_type |

---

## 6. Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `/app/backend/server.py` | Endpoints `/api/servers` y `/api/servers/{server_id}` actualizados para usar registry |
| `/app/backend/server.py` | Modelo `Server` actualizado con campos `system_type_normalized`, `config_origin`, `password_configured`, `api_key_configured`, `warnings` |

---

## 7. Endpoints Actualizados

### GET /api/servers

**Antes:** Leía directamente de MongoDB  
**Ahora:** Usa `server_registry.list_servers()` con SQL primero, fallback a MongoDB

**Campos nuevos en respuesta:**
- `system_type_normalized`: system_type normalizado (MANAGEMENTPRO, SOFTRESTAURANT, etc.)
- `config_origin`: Fuente de la configuración (EDARSAHUB_SQL o MONGODB_LEGACY)
- `password_configured`: true/false (sin exponer el valor real)
- `api_key_configured`: true/false (sin exponer el valor real)
- `warnings`: Array de warnings (ej: "Migrar a EDARSAHUB SQL")

### GET /api/servers/{server_id}

**Antes:** Leía directamente de MongoDB  
**Ahora:** Usa `server_registry.get_server_by_id()` con SQL primero, fallback a MongoDB

---

## 8. Fallback MongoDB

El fallback a MongoDB se activa automáticamente cuando:
1. SQL no tiene el servidor solicitado
2. SQL no está disponible (timeout, error de conexión)
3. El flag `USE_SQL_FOR_SERVERS=false` está configurado

**Logs generados:**
- `[SERVER_REGISTRY][SQL_HIT]`: Servidor obtenido de SQL
- `[SERVER_REGISTRY][SQL_MISS]`: Servidor no encontrado en SQL
- `[SERVER_REGISTRY][MONGODB_FALLBACK_USED]`: Se usó MongoDB como fallback

**Warning en respuesta:**
```json
{
  "config_origin": "MONGODB_LEGACY",
  "warnings": ["Servidor obtenido desde MongoDB legacy; migrar a EDARSAHUB SQL."]
}
```

---

## 9. RBAC

El filtro de permisos se mantiene sin cambios:

| Rol | Comportamiento |
|-----|----------------|
| SuperAdmin | Ve todos los servidores |
| Administrador | Ve todos los servidores |
| Otros | Solo ve servidores en `allowed_servers` |

---

## 10. Seguridad de Secretos

**Nunca se exponen:**
- `password`
- `password_encrypted`
- `api_key`
- `api_key_encrypted`

**Se devuelven flags:**
- `password_configured: true/false`
- `api_key_configured: true/false`

---

## 11. Validación Realizada

| Validación | Resultado |
|------------|-----------|
| `python -m py_compile server_registry.py` | ✅ OK |
| `python -m compileall /app/backend` | ✅ OK |
| Backend arranca (supervisor) | ✅ RUNNING |
| Login `/api/auth/login` | ✅ OK |
| `/api/servers` responde | ✅ 8 servidores |
| `/api/servers` incluye `config_origin` | ✅ EDARSAHUB_SQL |
| `/api/servers` incluye `system_type_normalized` | ✅ SOFTRESTAURANT, MANAGEMENTPRO |
| `/api/servers` no expone passwords | ✅ Solo `password_configured` |

---

## 12. Módulos Consumidores (Integración)

| Módulo | Estado | Notas |
|--------|--------|-------|
| Comercial | ✅ Ya usaba SQL (repository.py) | Sin cambios necesarios |
| Compras | ⏳ Pendiente | Usa `server.py` directamente |
| Finanzas | ⏳ Pendiente | Usa `server.py` directamente |
| Operaciones/Inventarios | ⏳ Pendiente | Usa `server.py` directamente |
| Auth | ✅ Compatible | Usa `allowed_servers` sin cambios |

---

## 13. Riesgos Residuales

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| Módulos que aún leen MongoDB directamente | MEDIO | Migrar gradualmente usando registry |
| Escritura a MongoDB aún activa | BAJO | POST/PUT/DELETE aún escriben a MongoDB; sincronizar manualmente |
| Cache de servidores | BAJO | No hay cache a nivel de registry; cada request consulta SQL |

---

## 14. Próximos Pasos (FASE 3B.1)

1. **Migrar endpoints de escritura** (POST, PUT, DELETE) para sincronizar SQL + MongoDB
2. **Migrar otros módulos** para usar `server_registry` en lugar de MongoDB directo
3. **Crear script de sincronización bidireccional** MongoDB ↔ SQL
4. **Agregar cache a nivel de registry** para reducir queries SQL

---

## 15. Flags de Control

| Flag | Default | Descripción |
|------|---------|-------------|
| `USE_SQL_FOR_SERVERS` | `true` | Si es `false`, usa MongoDB directamente (rollback rápido) |

---

## 16. Responsable

Agente E1 - Emergent Labs  
Fase: 3B - Migración servers a EDARSAHUB SQL

---

## FASE 3B.1 — Escritura SQL-first y sincronización legacy MongoDB

**Fecha:** 2025-12-XX  
**Estado:** COMPLETADO

### Resumen

Los endpoints de escritura de servidores ahora usan SQL-first:

| Endpoint | Antes | Ahora |
|----------|-------|-------|
| POST /api/servers | Solo MongoDB | SQL primero, sync MongoDB |
| PUT /api/servers/{id} | Solo MongoDB | SQL primero, sync MongoDB |
| DELETE /api/servers/{id} | Solo MongoDB | SQL primero, sync MongoDB |

### Funciones agregadas a server_registry.py

- `create_server()` - Crea en SQL, sincroniza a MongoDB
- `update_server()` - Actualiza en SQL, sincroniza a MongoDB
- `delete_server()` - Soft delete en SQL, sincroniza a MongoDB
- `sync_server_to_mongo()` - Sincroniza servidor específico
- `validate_server_payload()` - Valida payload

### Sync Status

- `SYNCED`: SQL + MongoDB actualizados
- `PARTIAL_SYNC`: SQL OK, MongoDB falló
- `SQL_ERROR`: SQL falló, MongoDB no se tocó

### Documento detallado

Ver: `/app/docs/FASE_3B1_SERVERS_WRITE_SYNC.md`
