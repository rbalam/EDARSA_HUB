# PLAN LOTE 2 — CONEXIONES-SQL-EDARSAHUB-01 / SUBFASE C.2-PLAN
## Definición de Lote 2 Quirúrgico

**Fecha:** 2025-12-19  
**Estado:** PROPUESTA PENDIENTE AUTORIZACIÓN  
**Autor:** Agente E1  
**Revisión requerida:** Usuario

---

## 1. RESUMEN

Este documento propone el **Lote 2** de migraciones de bypasses `db.servers.find_one()` hacia `server_registry.get_server_connection_info()`.

- **Bypasses restantes categoría A:** 40
- **Propuesta inicial:** 10 candidatos evaluados
- **Selección final Lote 2:** 5 cambios (máximo autorizado)

---

## 2. LISTA DE 10 CAMBIOS CANDIDATOS (EVALUACIÓN COMPLETA)

### Candidato #1: test_server_connection / ping_server

| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea aproximada** | 1315 |
| **Endpoint/Función** | `GET /servers/{server_id}/ping` → `ping_server()` |
| **Módulo afectado** | Configuración de Servidores |
| **Bypass actual** | `db.servers.find_one({"id": server_id})` |
| **Dato tomado de MongoDB** | host, port, database, username, password, name |
| **Llamada propuesta** | `get_server_connection_info(server_id, db=db)` |
| **Riesgo** | BAJO - Endpoint de diagnóstico aislado |
| **Impacto** | MEDIO - Usado por panel de administración para verificar conexiones |
| **Pruebas necesarias** | `GET /api/servers/{id}/ping` debe retornar status=connected |
| **Rollback** | Revertir función `ping_server()` |

---

### Candidato #2: validate_server_query

| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea aproximada** | 1531 |
| **Endpoint/Función** | `POST /servers/{server_id}/queries/validate` → `validate_server_query()` |
| **Módulo afectado** | Configuración de Servidores |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
| **Dato tomado de MongoDB** | host, port, database, username, password |
| **Llamada propuesta** | `get_server_connection_info(server_id, db=db)` |
| **Riesgo** | BAJO - Endpoint de configuración |
| **Impacto** | BAJO - Solo usado al configurar queries de servidor |
| **Pruebas necesarias** | Validar query SQL en panel de configuración |
| **Rollback** | Revertir función `validate_server_query()` |

---

### Candidato #3: save_server_query

| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea aproximada** | 1622, 1642 |
| **Endpoint/Función** | `POST /servers/{server_id}/queries` → `save_server_query()` |
| **Módulo afectado** | Configuración de Servidores |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` y lectura post-update |
| **Dato tomado de MongoDB** | Verificación de existencia + lectura de config queries |
| **Llamada propuesta** | `get_server_connection_info(server_id, db=db)` para verificar existencia |
| **Riesgo** | MEDIO - Función de escritura, tiene 2 lecturas |
| **Impacto** | BAJO - Solo usado al guardar queries |
| **Pruebas necesarias** | Guardar query en panel de configuración |
| **Rollback** | Revertir función `save_server_query()` |
| **NOTA** | Esta función también escribe a `db.servers.update_one()` - clasificada como C (REVISAR) |

---

### Candidato #4: get_server_queries

| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea aproximada** | 1667 |
| **Endpoint/Función** | `GET /servers/{server_id}/queries` → `get_server_queries()` |
| **Módulo afectado** | Configuración de Servidores |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
| **Dato tomado de MongoDB** | name, system_type, queries_configured, query_inventario, query_ventas, query_movimientos |
| **Llamada propuesta** | Requiere acceso a campos de config queries que podrían no estar en registry |
| **Riesgo** | MEDIO - Depende de campos que pueden no estar en EDARSAHUB |
| **Impacto** | BAJO - Solo usado en panel de configuración |
| **Pruebas necesarias** | Ver estado de queries en panel de configuración |
| **Rollback** | Revertir función `get_server_queries()` |
| **ALERTA** | ⚠️ Campos `query_*` se almacenan en MongoDB, no en EDARSAHUB. Requiere análisis adicional. |

---

### Candidato #5: delete_server_query

| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea aproximada** | 1721 |
| **Endpoint/Función** | `DELETE /servers/{server_id}/queries/{query_type}` → `delete_server_query()` |
| **Módulo afectado** | Configuración de Servidores |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
| **Dato tomado de MongoDB** | Verificación de existencia |
| **Llamada propuesta** | `get_server_connection_info(server_id, db=db)` |
| **Riesgo** | BAJO - Solo verifica existencia |
| **Impacto** | BAJO - Solo usado al eliminar queries |
| **Pruebas necesarias** | Eliminar query en panel de configuración |
| **Rollback** | Revertir función `delete_server_query()` |

---

### Candidato #6: get_categorias

| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea aproximada** | 1796 |
| **Endpoint/Función** | `GET /servers/{server_id}/categorias` → `get_categorias()` |
| **Módulo afectado** | Catálogos - Inventarios |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
| **Dato tomado de MongoDB** | host, port, database, username, password, system_type |
| **Llamada propuesta** | `get_server_connection_info(server_id, db=db)` |
| **Riesgo** | BAJO - Patrón idéntico a Lote 1 |
| **Impacto** | ALTO - Catálogo usado en filtros de Inventarios |
| **Pruebas necesarias** | Filtro de categorías en módulo Inventarios |
| **Rollback** | Revertir función `get_categorias()` |

---

### Candidato #7: get_departamentos

| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea aproximada** | 1838 |
| **Endpoint/Función** | `GET /servers/{server_id}/departamentos` → `get_departamentos()` |
| **Módulo afectado** | Catálogos - Inventarios/Operaciones |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
| **Dato tomado de MongoDB** | host, port, database, username, password, system_type |
| **Llamada propuesta** | `get_server_connection_info(server_id, db=db)` |
| **Riesgo** | BAJO - Patrón idéntico a Lote 1 |
| **Impacto** | ALTO - Catálogo usado en filtros de Inventarios/Operaciones |
| **Pruebas necesarias** | Filtro de departamentos en módulo Inventarios |
| **Rollback** | Revertir función `get_departamentos()` |

---

### Candidato #8: get_sucursales_config

| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea aproximada** | 2129 |
| **Endpoint/Función** | `GET /servers/{server_id}/sucursales-config` → `get_sucursales_config()` |
| **Módulo afectado** | Configuración de Sucursales |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
| **Dato tomado de MongoDB** | name (para respuesta), verificación de existencia |
| **Llamada propuesta** | `get_server_connection_info(server_id, db=db)` |
| **Riesgo** | BAJO - Solo lee nombre del servidor |
| **Impacto** | MEDIO - Configuración de visibilidad de sucursales |
| **Pruebas necesarias** | Panel de configuración de sucursales |
| **Rollback** | Revertir función `get_sucursales_config()` |

---

### Candidato #9: sync_sucursales_config

| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea aproximada** | 2157 |
| **Endpoint/Función** | `POST /servers/{server_id}/sucursales-config/sync` → `sync_sucursales_config()` |
| **Módulo afectado** | Configuración de Sucursales |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True})` |
| **Dato tomado de MongoDB** | host, port, database, username, password, system_type, name |
| **Llamada propuesta** | `get_server_connection_info(server_id, db=db)` |
| **Riesgo** | BAJO - Patrón idéntico a Lote 1 |
| **Impacto** | MEDIO - Sincronización de sucursales |
| **Pruebas necesarias** | Botón "Sincronizar" en panel de configuración |
| **Rollback** | Revertir función `sync_sucursales_config()` |

---

### Candidato #10: generate_inventory_report

| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea aproximada** | 2859 |
| **Endpoint/Función** | `POST /reports/inventory` → `generate_inventory_report()` |
| **Módulo afectado** | Inventarios/Operaciones |
| **Bypass actual** | `db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})` |
| **Dato tomado de MongoDB** | host, port, database, username, password, system_type |
| **Llamada propuesta** | `get_server_connection_info(server_id, db=db)` |
| **Riesgo** | MEDIO - Endpoint de reportes crítico |
| **Impacto** | ALTO - Genera reportes de inventario |
| **Pruebas necesarias** | Generar reporte de inventario en módulo Operaciones |
| **Rollback** | Revertir función `generate_inventory_report()` |

---

## 3. SELECCIÓN FINAL: LOTE 2 (5 CAMBIOS)

### Criterios de selección aplicados:
1. **Prioridad por módulo:** Catálogos > Configuración > Reportes
2. **Riesgo:** Preferir BAJO sobre MEDIO
3. **Impacto:** Preferir ALTO (más beneficio)
4. **Patrón:** Preferir funciones similares a Lote 1
5. **Dependencias:** Evitar funciones con escrituras a MongoDB (categoría C)

### LOTE 2 SELECCIONADO:

| # | ID | Función | Línea | Módulo | Riesgo | Impacto |
|---|-----|---------|-------|--------|--------|---------|
| 1 | C6 | `get_categorias()` | 1796 | Catálogos | BAJO | ALTO |
| 2 | C7 | `get_departamentos()` | 1838 | Catálogos | BAJO | ALTO |
| 3 | C1 | `ping_server()` | 1315 | Configuración | BAJO | MEDIO |
| 4 | C8 | `get_sucursales_config()` | 2129 | Config Sucursales | BAJO | MEDIO |
| 5 | C9 | `sync_sucursales_config()` | 2157 | Config Sucursales | BAJO | MEDIO |

---

## 4. JUSTIFICACIÓN DE SELECCIÓN

### ¿Por qué estos 5 van primero?

1. **get_categorias() y get_departamentos():**
   - Son catálogos fundamentales usados por filtros en módulo Inventarios/Operaciones
   - Patrón idéntico a `get_sucursales()`, `get_almacenes()`, `get_tipos_movimiento()` del Lote 1
   - Completan la migración de catálogos base
   - Riesgo BAJO, impacto ALTO

2. **ping_server():**
   - Endpoint de diagnóstico aislado (no afecta operaciones de negocio)
   - Permite validar que la migración funciona a nivel de conexión
   - Riesgo BAJO

3. **get_sucursales_config() y sync_sucursales_config():**
   - Funciones relacionadas entre sí (agrupar reduce complejidad de pruebas)
   - Afectan la visibilidad de sucursales en módulos principales
   - Patrón similar a Lote 1

### ¿Por qué los otros 5 esperan?

1. **validate_server_query (C2):** Baja frecuencia de uso, solo configuración inicial
2. **save_server_query (C3):** Tiene escrituras a MongoDB - clasificado como categoría C, requiere análisis adicional
3. **get_server_queries (C4):** Lee campos `query_*` que pueden no estar en EDARSAHUB - requiere análisis
4. **delete_server_query (C5):** Baja prioridad, solo configuración
5. **generate_inventory_report (C10):** Riesgo MEDIO, endpoint crítico - mejor validar catálogos primero

---

## 5. MÓDULOS TOCADOS POR LOTE 2

| Módulo | Funciones | Impacto |
|--------|-----------|---------|
| Catálogos | `get_categorias()`, `get_departamentos()` | Filtros de Inventarios |
| Configuración Servidores | `ping_server()` | Panel de administración |
| Configuración Sucursales | `get_sucursales_config()`, `sync_sucursales_config()` | Visibilidad de sucursales |

**No se tocan:** Comercial, Finanzas, Compras (directamente). Los catálogos afectan indirectamente.

---

## 6. RIESGO POR CAMBIO

| # | Función | Riesgo | Descripción |
|---|---------|--------|-------------|
| 1 | `get_categorias()` | BAJO | Lectura de catálogo, patrón probado |
| 2 | `get_departamentos()` | BAJO | Lectura de catálogo, patrón probado |
| 3 | `ping_server()` | BAJO | Endpoint aislado de diagnóstico |
| 4 | `get_sucursales_config()` | BAJO | Solo lectura de nombre |
| 5 | `sync_sucursales_config()` | BAJO | Lectura + escritura a config local |

**Riesgo total del lote:** BAJO

---

## 7. VALIDACIONES OBLIGATORIAS PROPUESTAS PARA LOTE 2

### Después de cada cambio:

| Cambio | Validación |
|--------|------------|
| `get_categorias()` | `GET /api/servers/{id}/categorias` retorna lista |
| `get_departamentos()` | `GET /api/servers/{id}/departamentos` retorna lista |
| `ping_server()` | `GET /api/servers/{id}/ping` retorna status=connected |
| `get_sucursales_config()` | `GET /api/servers/{id}/sucursales-config` retorna configuración |
| `sync_sucursales_config()` | `POST /api/servers/{id}/sucursales-config/sync` sincroniza sin error |

### Validación final del Lote 2:

| Check | Criterio |
|-------|----------|
| Backend levanta | ✅ Sin errores de import |
| Auth funciona | Login + /me retornan datos |
| Inventarios carga | Filtros de categoría/departamento funcionan |
| Configuración carga | Panel de administración muestra servidores |
| Ping funciona | Test de conexión desde panel admin |
| Sucursales config | Configuración de visibilidad funciona |
| No se imprimen credenciales | Logs limpios |
| No se toca frontend | Ningún cambio en /app/frontend |
| No se toca refresh tokens | Módulo intacto |

---

## 8. ROLLBACK POR CAMBIO

### Rollback individual:

| # | Función | Comando |
|---|---------|---------|
| 1 | `get_categorias()` | Copiar código "ANTES" del reporte Lote 2 |
| 2 | `get_departamentos()` | Copiar código "ANTES" del reporte Lote 2 |
| 3 | `ping_server()` | Copiar código "ANTES" del reporte Lote 2 |
| 4 | `get_sucursales_config()` | Copiar código "ANTES" del reporte Lote 2 |
| 5 | `sync_sucursales_config()` | Copiar código "ANTES" del reporte Lote 2 |

### Rollback completo del lote:

```bash
git checkout HEAD~1 -- /app/backend/server.py
sudo supervisorctl restart backend
```

### Pruebas después del rollback:

1. Backend levanta
2. Login funciona
3. Endpoints revertidos responden igual que antes
4. Módulos afectados cargan normalmente

---

## 9. PRUEBAS DETALLADAS POR CAMBIO

### Cambio 1: get_categorias()

```bash
# Test con servidor SoftRestaurant
curl -s -X GET "$API_URL/api/servers/$SR_SERVER_ID/categorias" -H "Authorization: Bearer $TOKEN"
# Esperado: Lista de categorías (códigos + descripciones)

# Test con servidor MPRO
curl -s -X GET "$API_URL/api/servers/$MPRO_SERVER_ID/categorias" -H "Authorization: Bearer $TOKEN"
# Esperado: Lista de categorías de MPRO
```

### Cambio 2: get_departamentos()

```bash
# Test con servidor SoftRestaurant
curl -s -X GET "$API_URL/api/servers/$SR_SERVER_ID/departamentos" -H "Authorization: Bearer $TOKEN"
# Esperado: Lista de departamentos (almacenes en SR)

# Test con servidor MPRO
curl -s -X GET "$API_URL/api/servers/$MPRO_SERVER_ID/departamentos" -H "Authorization: Bearer $TOKEN"
# Esperado: Lista de departamentos de MPRO
```

### Cambio 3: ping_server()

```bash
# Test de ping
curl -s -X GET "$API_URL/api/servers/$SERVER_ID/ping" -H "Authorization: Bearer $TOKEN"
# Esperado: {"status": "connected", "response_time_ms": X, ...}
```

### Cambio 4: get_sucursales_config()

```bash
# Test de configuración de sucursales
curl -s -X GET "$API_URL/api/servers/$SERVER_ID/sucursales-config" -H "Authorization: Bearer $TOKEN"
# Esperado: {"server_id": "...", "sucursales": [...]}
```

### Cambio 5: sync_sucursales_config()

```bash
# Test de sincronización (requiere rol Administrador)
curl -s -X POST "$API_URL/api/servers/$SERVER_ID/sucursales-config/sync" -H "Authorization: Bearer $ADMIN_TOKEN"
# Esperado: {"sincronizadas": X, "nuevas": Y, ...}
```

---

## 10. DICTAMEN

### Estado: PROPUESTA LISTA PARA AUTORIZACIÓN

**Lote 2 propuesto (5 cambios):**
1. `get_categorias()` - Catálogo
2. `get_departamentos()` - Catálogo
3. `ping_server()` - Diagnóstico
4. `get_sucursales_config()` - Configuración
5. `sync_sucursales_config()` - Configuración

**Riesgo total:** BAJO  
**Módulos tocados:** Catálogos, Configuración  
**Frontend:** No se toca  
**Rollback:** Documentado  

**Acción requerida:**  
Usuario debe autorizar Lote 2 para proceder con la implementación.

---

**Documento generado por Agente E1 - EDARSA HUB**  
**Fecha:** 2025-12-19  
**Versión:** 1.0
