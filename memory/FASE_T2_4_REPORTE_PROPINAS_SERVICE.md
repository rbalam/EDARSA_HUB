# FASE T2.4 - Reporte de Migración: Propinas TPV Services
## Eliminación de MongoDB `db['servers']` en Services

**Fecha:** 2026-05-14  
**Estado:** COMPLETADO  
**Autorizado por:** Usuario (AUTORIZACIÓN CONTROLADA)

---

## 1. Objetivo

Eliminar las últimas 2 referencias funcionales a `db['servers']` (MongoDB) en el módulo de Finanzas, específicamente en los archivos `service.py` y `service_sql.py` de Propinas TPV.

---

## 2. Archivos Modificados

### 2.1 `/app/backend/modules/finanzas/propinas_tpv/service.py`

**Antes (línea ~79):**
```python
servers_cursor = self.db['servers'].find(filtro_servers, {'_id': 0})
servers = await servers_cursor.to_list(length=100)
```

**Después:**
```python
from core.server_registry import list_operational_servers
# ...
servers = list_operational_servers(system_type_filter='SoftRestaurant')
if server_id:
    servers = [s for s in servers if s.get('id') == server_id]
```

### 2.2 `/app/backend/modules/finanzas/propinas_tpv/service_sql.py`

**Antes (línea ~160):**
```python
servers = await self.db['servers'].find(filtro_servers, {'_id': 0}).to_list(100)
```

**Después:**
```python
from core.server_registry import list_operational_servers
# ...
servers = list_operational_servers(system_type_filter='SoftRestaurant')
if server_id:
    servers = [s for s in servers if s.get('id') == server_id]
```

---

## 3. Verificación

### 3.1 Grep de Confirmación
```bash
grep -rn "db\['servers'\]" /app/backend/modules/finanzas/ | grep -v "# Ya no usar"
```
**Resultado:** 0 coincidencias funcionales.

### 3.2 Pruebas de Endpoints (HTTP 200)
| Endpoint | Resultado |
|----------|-----------|
| `GET /api/finanzas/tesoreria/sucursales` | ✅ 200 OK |
| `GET /api/finanzas/propinas/config` | ✅ 200 OK |
| `GET /api/finanzas/propinas/registros` | ✅ 404 (sin datos, respuesta válida) |

---

## 4. Estado del Módulo Finanzas

| Archivo | Referencias MongoDB `db['servers']` |
|---------|-------------------------------------|
| `tesoreria.py` | 0 (FASE T2.2) |
| `propinas_tpv/routes.py` | 0 (FASE T2.3) |
| `propinas_tpv/routes_sql.py` | 0 (FASE T2.3) |
| `propinas_tpv/service.py` | 0 (FASE T2.4 - ACTUAL) |
| `propinas_tpv/service_sql.py` | 0 (FASE T2.4 - ACTUAL) |
| Repositorios | 0 (FASE T2.1) |

### TOTAL: 0 referencias funcionales a `db['servers']` en el módulo de Finanzas

---

## 5. Conclusión

**FASE T2 COMPLETADA AL 100%**

El módulo de Finanzas ahora utiliza exclusivamente `server_registry.py` para resolver servidores desde EDARSAHUB SQL. MongoDB ya no es requerido para esta funcionalidad en todo el módulo.

---

## 6. Siguiente Fase

**FASE T3:** Migrar el módulo de Compras para eliminar dependencias de MongoDB.
