# FASE T3.1 — Reporte de Migración: Repository Base de Compras
## Eliminación de MongoDB `db.servers` en Repositories

**Fecha:** 14-Mayo-2026  
**Estado:** COMPLETADO  
**Autorizado por:** Usuario (AUTORIZACIÓN CONTROLADA)

---

## 1. Archivos Modificados

| Archivo | Línea | Acción |
|---------|-------|--------|
| `/app/backend/modules/compras/repository.py` | 105-116 | Migrado a `server_registry.get_server_connection_info()` |
| `/app/backend/modules/compras/historical_kpis_repository.py` | 28-40 | Migrado a `EDARSAHUB_CONFIG` |

---

## 2. Referencias MongoDB Eliminadas

### 2.1 `repository.py` (línea 111)

**ANTES:**
```python
async def get_server_by_id(server_id: str) -> Optional[Dict]:
    """Obtiene un servidor activo por ID."""
    server = await get_db().servers.find_one({"id": server_id, "active": True}, {"_id": 0})
    return _decrypt_server_password(server)
```

**DESPUÉS:**
```python
async def get_server_by_id(server_id: str) -> Optional[Dict]:
    """
    FASE T3.1: Migrado de MongoDB db.servers a server_registry (EDARSAHUB).
    """
    from core.server_registry import get_server_connection_info
    server = await get_server_connection_info(server_id, db=get_db())
    return server
```

### 2.2 `historical_kpis_repository.py` (línea 37)

**ANTES:**
```python
def get_edarsahub_server():
    """Obtiene configuración del servidor EDARSAHUB desde MongoDB."""
    client = MongoClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    srv = db.servers.find_one({'name': 'EDARSA HUB', 'active': True})
    if not srv:
        raise ValueError("Servidor EDARSA HUB no encontrado en MongoDB")
    # ... descifrado password ...
    return {...}
```

**DESPUÉS:**
```python
def get_edarsahub_server():
    """
    FASE T3.1: Migrado de MongoDB db.servers a EDARSAHUB_CONFIG de server_registry.
    """
    from core.server_registry import EDARSAHUB_CONFIG
    return {
        "host": EDARSAHUB_CONFIG['host'],
        "port": EDARSAHUB_CONFIG['port'],
        "database": EDARSAHUB_CONFIG['database'],
        "username": EDARSAHUB_CONFIG['username'],
        "password": EDARSAHUB_CONFIG['password'],
    }
```

---

## 3. Funciones `server_registry.py` Usadas

| Archivo | Función |
|---------|---------|
| `repository.py` | `get_server_connection_info(server_id, db)` |
| `historical_kpis_repository.py` | `EDARSAHUB_CONFIG` (constante) |

---

## 4. Endpoints Probados

| Endpoint | Resultado |
|----------|-----------|
| `GET /api/finanzas/tesoreria/sucursales` | ✅ HTTP 200 |
| `GET /api/compras/inventarios-fisicos/{server_id}` | ✅ HTTP 200 (datos de inventarios) |
| `GET /api/v2/comercial/dashboard` | ✅ HTTP 422 (requiere parámetros, no error 500) |

---

## 5. Confirmación de No Cambios

- ✅ **NO se modificó** `/app/backend/server.py`
- ✅ **NO se modificaron** endpoints críticos (auditoria-operativa, analisis, etc.)
- ✅ **NO se modificó** lógica de negocio
- ✅ **NO se modificaron** queries SQL
- ✅ **NO se tocó** Finanzas
- ✅ **NO se tocó** Comercial
- ✅ **NO se tocó** Auth/RBAC
- ✅ **NO se tocó** Frontend
- ✅ **NO se ejecutó** ningún script SQL

---

## 6. Referencias `db.servers` Restantes en Compras

### En módulo `/modules/compras/`:
**CERO** referencias funcionales (solo comentarios de documentación).

### En `server.py` (endpoints compras):
| Línea | Endpoint | Estado |
|-------|----------|--------|
| 7323 | `POST /compras/productos-para-captura` | ⏸️ Pendiente T3.2+ |
| 7438 | `POST /compras/auditoria-operativa` | ⏸️ Pendiente T3.4 |
| 8142 | `POST /compras/detalle-movimientos` | ⏸️ Pendiente T3.2 |
| 8319 | `POST /compras/detalle-consumos` | ⏸️ Pendiente T3.2 |
| 8746 | `POST /compras/analisis` | ⏸️ Pendiente T3.3 |
| 8893 | `GET /compras/facturas-proveedor` | ⏸️ Pendiente T3.2 |
| 8958 | `GET /compras/detalle-factura` | ⏸️ Pendiente T3.2 |

**Total restante en server.py:** 7 referencias

---

## 7. Recomendación para FASE T3.2

**Próximos endpoints a migrar (riesgo bajo/medio):**

1. `GET /compras/facturas-proveedor/{server_id}` (línea 8893) — ~65 líneas, query simple
2. `GET /compras/detalle-factura/{server_id}/{folio}` (línea 8958) — ~40 líneas, query simple
3. `POST /compras/detalle-movimientos` (línea 8142) — ~80 líneas
4. `POST /compras/detalle-consumos` (línea 8319) — ~90 líneas

**Razón:** Son endpoints con lógica simple y lineal, fáciles de validar con curl.

---

## 8. Resumen

| Métrica | Antes T3.1 | Después T3.1 |
|---------|------------|--------------|
| Referencias MongoDB en `/modules/compras/` | 2 | 0 |
| Referencias MongoDB en `server.py` (compras) | 7 | 7 (sin cambios) |
| **Total módulo Compras** | 9 | 7 |

**FASE T3.1 COMPLETADA:** Repository base de Compras migrado exitosamente a EDARSAHUB.

---

**Reporte generado:** 14-Mayo-2026  
**Autor:** Agente E1  
**Pendiente:** Autorización para FASE T3.2 (endpoints riesgo bajo/medio)
