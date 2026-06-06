# P1.4-B: MIGRACIÓN ENDPOINTS QUERIES — COMPLETADO

**Fecha:** 14-Dic-2025  
**Estado:** ✅ COMPLETADO Y VALIDADO  
**Autorizado por:** Usuario (Mensaje 14-Dic-2025)

---

## 1. RESUMEN

Se migraron exitosamente 4 endpoints de configuración de queries SQL de servidores, eliminando la dependencia directa de MongoDB (`db.servers`) y usando `server_registry` (fuente: EDARSAHUB SQL).

---

## 2. ENDPOINTS MIGRADOS

| Endpoint | Función | Antes | Después |
|----------|---------|-------|---------|
| `GET /api/servers/{id}/queries` | Obtener estado de queries | `db.servers.find_one()` | `server_registry.get_server_by_id()` |
| `POST /api/servers/{id}/queries/validate` | Validar query SQL | `db.servers.find_one()` | `server_registry.get_server_connection_info_with_secrets()` |
| `PUT /api/servers/{id}/queries/{type}` | Guardar query configurada | `db.servers.find_one()` + `db.servers.update_one()` | `server_registry.get_server_connection_info_with_secrets()` + `server_registry.update_server()` |
| `DELETE /api/servers/{id}/queries/{type}` | Eliminar query configurada | `db.servers.find_one()` + `db.servers.update_one()` | `server_registry.get_server_connection_info_with_secrets()` + `server_registry.update_server()` |

---

## 3. ARCHIVOS MODIFICADOS

### 3.1 `/app/backend/server.py`

| Sección | Líneas | Cambio |
|---------|--------|--------|
| Modelo `Server` | 596-598 | Corregido `tipos_movimiento`, `categorias`, `departamentos` de `List[str]` a `List[Any]` para aceptar objetos JSON de EDARSAHUB |
| `validate_server_query()` | 1587-1660 | Usa `get_server_connection_info_with_secrets()` |
| `save_server_query()` | 1693-1760 | Usa `get_server_connection_info_with_secrets()` + `update_server()` |
| `get_server_queries()` | 1763-1820 | Usa `get_server_by_id()`, corregido manejo de `None` en queries |
| `delete_server_query()` | 1823-1860 | Usa `get_server_connection_info_with_secrets()` + `update_server()` |

### 3.2 `/app/backend/core/server_registry.py`

| Cambio | Descripción |
|--------|-------------|
| `update_server()` | Agregado soporte para campos `query_inventario`, `query_ventas`, `query_movimientos` y `queries_configured` |

---

## 4. EVIDENCIA DE VALIDACIÓN

### 4.1 Curl Tests

```bash
# TEST 1: GET /api/servers/{id}/queries
✅ 200 OK - Devuelve estado de queries sin usar MongoDB

# TEST 2: POST /api/servers/{id}/queries/validate
✅ 200 OK - Valida query SQL conectando al servidor vía EDARSAHUB

# TEST 3: PUT /api/servers/{id}/queries/inventario
✅ 200 OK - Guarda query vía server_registry.update_server()

# TEST 4: DELETE /api/servers/{id}/queries/inventario
✅ 200 OK - Elimina query vía server_registry.update_server()
```

### 4.2 Validación No Regresión

```bash
# GET /api/servers
✅ 200 OK - Lista 8 servidores

# GET /api/comercial/tablero-ejecutivo
✅ 200 OK - Dashboard comercial funciona

# GET /api/catalogos/dominios
✅ 200 OK - Catálogos desde EDARSAHUB_CONFIG

# GET /api/finanzas/tesoreria/sucursales
✅ 200 OK - 4 sucursales activas
```

### 4.3 Grep Antes/Después

**ANTES (db.servers en endpoints queries):**
```
1607: server = decrypt_server_secrets(await db.servers.find_one(...))
1698: server = decrypt_server_secrets(await db.servers.find_one(...))
1712: await db.servers.update_one(...)
1718: updated_server = decrypt_server_secrets(await db.servers.find_one(...))
1725: await db.servers.update_one(...)
1743: server = decrypt_server_secrets(await db.servers.find_one(...))
```

**DESPUÉS:**
```
Ninguna referencia activa a db.servers en líneas 1590-1900
```

---

## 5. CORRECCIONES COLATERALES

### 5.1 Bug Fix: Modelo Pydantic `Server`

**Problema:** `tipos_movimiento: List[str]` fallaba porque EDARSAHUB guarda objetos `{codigo, descripcion, tipo}`.

**Solución:** Cambiar a `tipos_movimiento: Optional[List[Any]]` para aceptar ambos formatos.

### 5.2 Bug Fix: NoneType en `get_server_queries()`

**Problema:** `server.get("query_inventario", {}).get("validated")` fallaba cuando `query_inventario = None`.

**Solución:** Usar `(server.get("query_inventario") or {}).get("validated")`.

---

## 6. SEGURIDAD VERIFICADA

| Aspecto | Estado |
|---------|--------|
| Password no expuesto en response | ✅ |
| Password no en logs | ✅ |
| MongoDB no usado como fuente | ✅ |
| SQL injection mitigado (queries son para ejecutar en servidor destino, no en EDARSAHUB) | ⚠️ Nota: La responsabilidad de las queries es del usuario configurador |

---

## 7. DEUDA TÉCNICA RESTANTE

Referencias a `db.servers` fuera del alcance de P1.4-B (para fases C-F):

| Línea | Endpoint | Fase |
|-------|----------|------|
| 3155 | `/servers/{id}/analyze-inventory` | P1.4-C |
| 3372 | `/servers/{id}/sucursales-config` | P1.4-D |
| 4667 | `/servers/{id}/inventory-summary` | P1.4-C |
| 4907 | `/servers/{id}/generate-report` | P1.4-C |
| 5465 | `/auditorias` | P1.4-E |

---

## 8. PRÓXIMOS PASOS

| # | Fase | Descripción | Estado |
|---|------|-------------|--------|
| 1 | P1.4-C | Migrar endpoints de Inventario | PENDIENTE |
| 2 | P1.4-D | Migrar Configuración de Sucursales | PENDIENTE |
| 3 | P1.4-E | Migrar Auditorías | PENDIENTE |
| 4 | P1.4-F | Migrar Módulo Configuración | PENDIENTE |

---

**CIERRE:** P1.4-B completado sin regresiones. EDARSAHUB SQL es ahora la fuente para endpoints de queries de servidores.

*Documento generado bajo régimen de Autorización Controlada.*
