# FASE T3.2 — Reporte de Migración: 4 Endpoints Compras en server.py
## Eliminación de MongoDB `db.servers` en Endpoints de Riesgo Bajo/Medio

**Fecha:** 14-Mayo-2026  
**Estado:** COMPLETADO  
**Autorizado por:** Usuario (AUTORIZACIÓN CONTROLADA)

---

## 1. Archivo Modificado

- `/app/backend/server.py`

---

## 2. Endpoints Modificados

| # | Endpoint | Línea | Función server_registry |
|---|----------|-------|-------------------------|
| 1 | `GET /compras/facturas-proveedor/{server_id}` | 8888 | `get_server_connection_info()` |
| 2 | `GET /compras/detalle-factura/{server_id}/{folio}` | 8953 | `get_server_connection_info()` |
| 3 | `POST /compras/detalle-movimientos` | 8136 | `get_server_connection_info()` |
| 4 | `POST /compras/detalle-consumos` | 8313 | `get_server_connection_info()` |

---

## 3. Referencias MongoDB Eliminadas

### Código ANTES:
```python
server = decrypt_server_secrets(await db.servers.find_one({"id": server_id, "active": True}))
```

### Código DESPUÉS:
```python
# FASE T3.2: Migrado de db.servers a server_registry (EDARSAHUB)
from core.server_registry import get_server_connection_info
server = await get_server_connection_info(server_id, db=db)
```

---

## 4. Pruebas Realizadas

| Endpoint | Método | HTTP Code | Resultado |
|----------|--------|-----------|-----------|
| `/api/compras/facturas-proveedor/{server_id}` | GET | 200 | ✅ `[]` (sin datos de prueba) |
| `/api/compras/detalle-factura/{server_id}/{folio}` | GET | 200 | ✅ `[]` (sin datos de prueba) |
| `/api/compras/detalle-movimientos` | POST | 200 | ✅ `{"movimientos":[],"totales":{...}}` |
| `/api/compras/detalle-consumos` | POST | 200 | ✅ `{"consumos":[],"totales":{...}}` |

---

## 5. Confirmaciones

- ✅ **NO se modificaron** endpoints críticos (`auditoria-operativa`, `analisis`, `productos-para-captura`)
- ✅ **NO se modificó** lógica de negocio
- ✅ **NO se modificaron** queries SQL
- ✅ **NO se tocó** Finanzas (verificado: `tesoreria/sucursales` HTTP 200)
- ✅ **NO se tocó** Comercial
- ✅ **NO se tocó** Auth/RBAC
- ✅ **NO se tocó** Frontend
- ✅ Contrato API sin cambios

---

## 6. No Regresión

| Área | Endpoint | Estado |
|------|----------|--------|
| Finanzas | `GET /api/finanzas/tesoreria/sucursales` | ✅ HTTP 200, 4 sucursales |
| Compras | `GET /api/compras/inventarios-fisicos/{server_id}` | ✅ HTTP 200, datos reales |
| Auth | `POST /api/auth/login` | ✅ HTTP 200, token válido |

---

## 7. Referencias `db.servers` Restantes en Compras

### En `server.py` (sección 7300-9000):

| Línea | Endpoint | Fase Pendiente |
|-------|----------|----------------|
| 7323 | `POST /compras/productos-para-captura` | T3.3 (ALTO) |
| 7438 | `POST /compras/auditoria-operativa` | T3.4 (CRÍTICO) |
| 8750 | `POST /compras/analisis` | T3.3 (ALTO) |

**Total restante en Compras:** 3 referencias (de 7 original antes de T3.2)

### Progreso T3:

| Fase | Referencias Migradas | Restantes |
|------|---------------------|-----------|
| T3.1 (repository) | 2 | 0 |
| T3.2 (endpoints bajo/medio) | 4 | 0 |
| T3.3 (endpoints alto) | 0 | 2 |
| T3.4 (crítico) | 0 | 1 |
| **TOTAL** | 6 | 3 |

---

## 8. Recomendación para T3.3

**Próximos endpoints a migrar (riesgo ALTO):**

1. `POST /compras/productos-para-captura` (línea 7315)
   - ~100 líneas
   - Inicializa captura de inventario
   - Requiere prueba funcional completa

2. `POST /compras/analisis` (línea 8741)
   - ~150 líneas
   - Análisis de proveedores multiperiodo
   - Requiere prueba con datos reales

**Nota:** Estos endpoints tienen lógica más compleja que los de T3.2.

---

## 9. Resumen

| Métrica | Antes T3.2 | Después T3.2 |
|---------|------------|--------------|
| Referencias en Compras (total) | 7 | 3 |
| Endpoints migrados | 0 | 4 |
| Pruebas pasadas | - | 4/4 |

**FASE T3.2 COMPLETADA:** 4 endpoints de riesgo bajo/medio migrados exitosamente.

---

**Reporte generado:** 14-Mayo-2026  
**Autor:** Agente E1  
**Pendiente:** Autorización para FASE T3.3 (endpoints riesgo ALTO)
