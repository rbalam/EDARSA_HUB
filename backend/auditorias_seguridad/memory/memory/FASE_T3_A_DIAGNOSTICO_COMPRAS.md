# FASE T3-A — Diagnóstico Pasivo del Módulo Compras
## Migración de MongoDB `db.servers` a `server_registry.py` / EDARSAHUB

**Fecha:** 14-Mayo-2026  
**Estado:** DIAGNÓSTICO COMPLETADO  
**Tipo:** Análisis de dependencias MongoDB  
**Próximo paso:** Pendiente autorización para FASE T3.1

---

## 1. Archivos Compras Revisados

| Archivo | Propósito |
|---------|-----------|
| `/app/backend/modules/compras/__init__.py` | Inicialización módulo |
| `/app/backend/modules/compras/repository.py` | Acceso a datos (MongoDB + SQL) |
| `/app/backend/modules/compras/service.py` | Lógica de negocio |
| `/app/backend/modules/compras/routes.py` | Router (desactivado) |
| `/app/backend/modules/compras/schemas.py` | Modelos Pydantic |
| `/app/backend/modules/compras/system_type_utils.py` | Normalización system_type |
| `/app/backend/modules/compras/historical_kpis_repository.py` | KPIs históricos EDARSAHUB |
| `/app/backend/server.py` (líneas 6451-8958) | Endpoints compras en producción |

---

## 2. Lista Exacta de Referencias a MongoDB `db.servers`

### 2.1 Módulo `/modules/compras/`

| # | Archivo | Línea | Código | Dato Obtenido |
|---|---------|-------|--------|---------------|
| 1 | `repository.py` | 111 | `await get_db().servers.find_one({"id": server_id, "active": True}, {"_id": 0})` | Conexión completa (host, port, database, username, password, system_type) |
| 2 | `historical_kpis_repository.py` | 37 | `db.servers.find_one({'name': 'EDARSA HUB', 'active': True})` | Conexión EDARSAHUB por nombre |

### 2.2 Endpoints en `server.py`

| # | Línea | Endpoint | Código |
|---|-------|----------|--------|
| 3 | 7323 | `POST /compras/productos-para-captura` | `db.servers.find_one({"id": request.server_id...})` |
| 4 | 7438 | `POST /compras/auditoria-operativa` | `db.servers.find_one({"id": request.server_id...})` |
| 5 | 8142 | `POST /compras/detalle-movimientos` | `db.servers.find_one({"id": request.server_id...})` |
| 6 | 8319 | `POST /compras/detalle-consumos` | `db.servers.find_one({"id": request.server_id...})` |
| 7 | 8746 | `POST /compras/analisis` | `db.servers.find_one({"id": request.server_id...})` |
| 8 | 8893 | `GET /compras/facturas-proveedor/{server_id}` | `db.servers.find_one({"id": server_id...})` |
| 9 | 8958 | `GET /compras/detalle-factura/{server_id}/{folio}` | `db.servers.find_one({"id": server_id...})` |

**Total: 9 referencias funcionales a MongoDB `db.servers` en Compras**

---

## 3. Endpoints YA Migrados (usan `validate_server_access_by_empresa`)

Los siguientes endpoints **YA NO usan** `db.servers` directamente porque llaman a `validate_server_access_by_empresa()` que internamente usa `server_registry.get_server_connection_info()`:

| Endpoint | Línea | Estado |
|----------|-------|--------|
| `GET /compras/inventarios-fisicos/{server_id}` | 6451 | ✅ MIGRADO |
| `GET /compras/pedidos-vigentes/{server_id}` | 6572 | ✅ MIGRADO |
| `GET /compras/detalle-pedido-manual/{server_id}` | 6646 | ✅ MIGRADO |
| `GET /compras/detalle-movimientos/{server_id}` | 6701 | ✅ MIGRADO |
| `GET /compras/detalle-consumos/{server_id}` | 6738 | ✅ MIGRADO |
| `GET /compras/detalle-pedido/{server_id}/{folio}` | 6773 | ✅ MIGRADO |
| `POST /compras/calculo-pedido` | 6820 | ✅ MIGRADO |
| `GET /compras/dashboard/{server_id}` | 8420 | ✅ MIGRADO |

---

## 4. Detalle de Datos Obtenidos de MongoDB

| Referencia | Datos | Uso |
|------------|-------|-----|
| `repository.py:111` | host, port, database, username, password, system_type | Conexión SQL para queries MPRO/SR |
| `historical_kpis_repository.py:37` | host, port, database, username, password | Conexión EDARSAHUB (por nombre 'EDARSA HUB') |
| Endpoints server.py | host, port, database, username, password, system_type, name | Conexión SQL + identificación servidor |

---

## 5. Función de `server_registry.py` Recomendada

| Referencia | Función Recomendada | Razón |
|------------|---------------------|-------|
| `repository.py:111` | `get_server_connection_info(server_id, db)` | Obtiene credenciales descifradas con fallback |
| `historical_kpis_repository.py:37` | `EDARSAHUB_CONFIG` (constante) | Ya existe configuración hardcodeada en registry |
| Endpoints server.py | `get_server_connection_info(server_id, db)` | Reemplazo directo compatible |

---

## 6. Clasificación de Riesgo por Endpoint

| Endpoint | Riesgo | Razón |
|----------|--------|-------|
| `POST /compras/auditoria-operativa` | 🔴 CRÍTICO | ~710 líneas, lógica compleja de auditoría |
| `POST /compras/calculo-pedido` | 🔴 CRÍTICO | ~420 líneas, cálculos de pedidos |
| `POST /compras/analisis` | 🟡 ALTO | Análisis de proveedores multiperiodo |
| `POST /compras/productos-para-captura` | 🟡 ALTO | Inicializa captura de inventario |
| `POST /compras/detalle-movimientos` | 🟢 MEDIO | Query de movimientos |
| `POST /compras/detalle-consumos` | 🟢 MEDIO | Query de consumos |
| `GET /compras/facturas-proveedor` | 🟢 MEDIO | Listado de facturas |
| `GET /compras/detalle-factura` | 🟢 BAJO | Detalle de una factura |
| `modules/compras/repository.py` | 🟢 BAJO | Función base, usada por service |
| `historical_kpis_repository.py` | 🟢 BAJO | Conexión EDARSAHUB (ya existe constante) |

---

## 7. Hallazgos por Submódulo

### 7.1 Repository Base (`modules/compras/repository.py`)
- **Referencia:** Línea 111, función `get_server_by_id()`
- **Impacto:** Todos los services que llaman a `repo.get_server_by_id()`
- **Solución:** Importar `get_server_connection_info` de `server_registry.py`

### 7.2 Historical KPIs (`historical_kpis_repository.py`)
- **Referencia:** Línea 37, función `get_edarsahub_server()`
- **Problema:** Busca servidor por NOMBRE ('EDARSA HUB') en MongoDB
- **Solución:** Usar `EDARSAHUB_CONFIG` que ya existe en `server_registry.py`

### 7.3 Inventarios Físicos
- **Estado:** ✅ YA MIGRADO via `validate_server_access_by_empresa()`
- **Endpoint:** `GET /compras/inventarios-fisicos/{server_id}`

### 7.4 Pedidos / Requisiciones
- **Estado:** ✅ PARCIALMENTE MIGRADO
- **Migrados:** `pedidos-vigentes`, `detalle-pedido`, `detalle-pedido-manual`, `calculo-pedido`
- **Pendiente:** Ninguno específico de pedidos

### 7.5 Dashboard Compras
- **Estado:** ✅ YA MIGRADO via `validate_server_access_by_empresa()`
- **Endpoint:** `GET /compras/dashboard/{server_id}`

### 7.6 Auditoría Operativa
- **Estado:** ⚠️ PENDIENTE
- **Endpoint:** `POST /compras/auditoria-operativa` (línea 7424)
- **Riesgo:** CRÍTICO (~710 líneas de lógica)

### 7.7 Facturas Proveedor / Análisis
- **Estado:** ⚠️ PENDIENTE
- **Endpoints:** `facturas-proveedor`, `detalle-factura`, `analisis`
- **Referencias:** Líneas 8746, 8893, 8958

### 7.8 Productos para Captura / Detalle Movimientos/Consumos
- **Estado:** ⚠️ PENDIENTE
- **Endpoints:** `productos-para-captura`, `detalle-movimientos`, `detalle-consumos`
- **Referencias:** Líneas 7323, 8142, 8319

---

## 8. Propuesta de Migración por Subfases

### FASE T3.1 — Conexión EDARSAHUB en Repository Base
**Archivos:**
- `/app/backend/modules/compras/repository.py` (1 cambio)
- `/app/backend/modules/compras/historical_kpis_repository.py` (1 cambio)

**Cambios:**
1. Reemplazar `get_server_by_id()` por import de `server_registry.get_server_connection_info()`
2. Reemplazar `get_edarsahub_server()` por uso de `EDARSAHUB_CONFIG`

**Riesgo:** BAJO
**Pruebas:** Endpoints que usan `service.py` (inventarios, pedidos)

---

### FASE T3.2 — Endpoints de Riesgo Bajo/Medio
**Endpoints:**
- `GET /compras/facturas-proveedor/{server_id}` (línea 8893)
- `GET /compras/detalle-factura/{server_id}/{folio}` (línea 8958)
- `POST /compras/detalle-movimientos` (línea 8142)
- `POST /compras/detalle-consumos` (línea 8319)

**Cambios:** Reemplazar `db.servers.find_one()` por `get_server_connection_info()`
**Riesgo:** MEDIO
**Pruebas:** curl a cada endpoint

---

### FASE T3.3 — Endpoints de Riesgo Alto
**Endpoints:**
- `POST /compras/productos-para-captura` (línea 7315)
- `POST /compras/analisis` (línea 8741)

**Riesgo:** ALTO
**Pruebas:** Flujo completo de captura y análisis

---

### FASE T3.4 — Endpoint Crítico: Auditoría Operativa
**Endpoint:**
- `POST /compras/auditoria-operativa` (línea 7424)

**Riesgo:** CRÍTICO (~710 líneas)
**Pruebas:** Auditoría completa en ambiente de prueba

---

### FASE T3.5 — Limpieza Final
**Acciones:**
- Verificar grep cero referencias
- Actualizar documentación
- Crear reporte final

---

## 9. Primer Endpoint Recomendado para Migrar

**Recomendación:** `GET /compras/facturas-proveedor/{server_id}` (línea 8893)

**Razones:**
1. Lógica simple y lineal (~65 líneas)
2. Query de solo lectura (SELECT)
3. No tiene dependencias de estado
4. Fácil de probar con curl
5. Patrón ya probado en otros endpoints migrados

**Segundo candidato:** `GET /compras/detalle-factura/{server_id}/{folio}` (línea 8958) por las mismas razones.

---

## 10. Pruebas de No Regresión Requeridas

| Fase | Prueba |
|------|--------|
| T3.1 | `GET /compras/inventarios-fisicos/{server_id}` devuelve datos |
| T3.1 | `GET /compras/pedidos-vigentes/{server_id}` devuelve datos |
| T3.2 | `GET /compras/facturas-proveedor/{server_id}` devuelve datos |
| T3.2 | `GET /compras/detalle-factura/{server_id}/{folio}` devuelve datos |
| T3.3 | `POST /compras/analisis` devuelve análisis |
| T3.4 | `POST /compras/auditoria-operativa` completa auditoría |
| T3.5 | `grep -r "db.servers" /app/backend/modules/compras/` = 0 resultados |

---

## 11. Rollback Propuesto

**Estrategia:** Cada cambio es atómico y reversible.

```python
# ANTES (MongoDB):
server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))

# DESPUÉS (Registry):
from core.server_registry import get_server_connection_info
server = await get_server_connection_info(server_id, db=db)

# ROLLBACK: Revertir el import y la línea
```

**Nota:** `get_server_connection_info()` ya tiene fallback a MongoDB si SQL falla, por lo que el rollback real es automático.

---

## 12. Confirmación de No Modificación

- ✅ **NO se modificó** ningún archivo
- ✅ **NO se ejecutó** ningún script
- ✅ **NO se tocó** MongoDB
- ✅ **NO se tocó** EDARSAHUB SQL
- ✅ **NO se tocó** Frontend
- ✅ **NO se tocó** Finanzas, Comercial, Auth/RBAC
- ✅ Diagnóstico 100% pasivo (solo lectura de código)

---

## 13. Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| **Referencias MongoDB en Compras** | 9 |
| **Ya migradas** | 8 endpoints (via `validate_server_access_by_empresa`) |
| **Pendientes en server.py** | 7 endpoints |
| **Pendientes en módulo** | 2 archivos (repository.py, historical_kpis_repository.py) |
| **Riesgo total** | MEDIO (mayoría son queries simples) |
| **Endpoint más crítico** | `POST /compras/auditoria-operativa` (~710 líneas) |
| **Endpoint recomendado para iniciar** | `GET /compras/facturas-proveedor/{server_id}` |

---

## 14. Próximos Pasos (Pendiente Autorización)

1. **FASE T3.1:** Migrar `repository.py` y `historical_kpis_repository.py`
2. **FASE T3.2:** Migrar endpoints de riesgo bajo/medio
3. **FASE T3.3:** Migrar endpoints de riesgo alto
4. **FASE T3.4:** Migrar `auditoria-operativa` (crítico)
5. **FASE T3.5:** Limpieza y verificación final

---

**Reporte generado:** 14-Mayo-2026  
**Autor:** Agente E1 (Diagnóstico Pasivo)  
**Pendiente:** Autorización para FASE T3.1
