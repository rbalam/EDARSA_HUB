# FASE T2.3: REPORTE DE MIGRACIÓN PROPINAS TPV ROUTES
**Fecha:** 2026-05-13
**Estado:** ✅ COMPLETADO

---

## 1. RESUMEN EJECUTIVO

| Aspecto | Resultado |
|---------|-----------|
| **Archivos modificados** | 2 |
| **Referencias db.servers eliminadas** | 6 |
| **MongoDB utilizado** | NO |
| **Tablero Ejecutivo** | ✅ Sin regresión |
| **Tesorería Sucursales** | ✅ 4 sucursales |

---

## 2. ARCHIVOS MODIFICADOS

### 2.1 `/app/backend/modules/finanzas/propinas_tpv/routes.py`

**Referencias eliminadas:** 3
- Línea 222: `db.servers.find_one({'id': server_id})`
- Línea 262: `db.servers.find({'system_type': 'SoftRestaurant'})`
- Línea 358: `db.servers.find(filtro)`

**Funciones helper agregadas:**
- `_get_server_from_registry(server_id)` - Reemplaza find_one
- `_list_softrestaurant_servers()` - Reemplaza find

---

### 2.2 `/app/backend/modules/finanzas/propinas_tpv/routes_sql.py`

**Referencias eliminadas:** 3
- Línea 408: `db.servers.find_one({'id': server_id})`
- Línea 440: `db.servers.find({'system_type': 'SoftRestaurant'})`
- Línea 516: `db.servers.find(filtro)`

**Funciones helper agregadas:**
- `_get_server_from_registry(server_id)` - Reemplaza find_one
- `_list_softrestaurant_servers()` - Reemplaza find

---

## 3. FUNCIONES DE SERVER_REGISTRY USADAS

| Función | Propósito |
|---------|-----------|
| `get_server_by_id(server_id)` | Obtener servidor específico |
| `list_operational_servers()` | Listar servidores activos |

---

## 4. PATRÓN DE REEMPLAZO

### Código Anterior (MongoDB)
```python
server = await db.servers.find_one({'id': server_id}, {'_id': 0})
servers = await db.servers.find({'system_type': 'SoftRestaurant'}, {'_id': 0}).to_list(100)
```

### Código Nuevo (server_registry)
```python
server = _get_server_from_registry(server_id)
servers = _list_softrestaurant_servers()
```

### Helper Functions
```python
def _get_server_from_registry(server_id: str) -> Optional[Dict]:
    server = get_server_by_id(server_id)
    if not server:
        return None
    return {
        'id': server.get('id'),
        'name': server.get('name'),
        'host': server.get('host'),
        # ... campos adaptados para compatibilidad
        '_source': 'EDARSAHUB'
    }

def _list_softrestaurant_servers() -> List[Dict]:
    all_servers = list_operational_servers()
    sr_servers = []
    for s in all_servers:
        system_type = (s.get('system_type') or '').upper()
        if system_type in ['SOFTRESTAURANT', 'SR']:
            sr_servers.append({...})
    return sr_servers
```

---

## 5. CONFIRMACIONES

| Confirmación | Estado |
|--------------|--------|
| routes.py sin db.servers | ✅ CONFIRMADO |
| routes_sql.py sin db.servers | ✅ CONFIRMADO |
| No se tocó service.py | ✅ CONFIRMADO |
| No se tocó sql_repository.py | ✅ CONFIRMADO |
| Contrato API sin cambios | ✅ CONFIRMADO |
| Tesorería funciona | ✅ 4 sucursales |
| Tablero Ejecutivo sin regresión | ✅ 5 unidades |
| No se usó MongoDB | ✅ CONFIRMADO |

---

## 6. REFERENCIAS db.servers RESTANTES EN FINANZAS

Después de FASE T2.3, quedan **2 referencias** en Propinas TPV Service:

| Archivo | Línea | Propósito | Fase |
|---------|-------|-----------|------|
| `propinas_tpv/service.py` | 79 | Listar servidores SR | T2.4 |
| `propinas_tpv/service_sql.py` | 160 | Listar servidores SR | T2.4 |

---

## 7. RECOMENDACIÓN PARA FASE T2.4

**Siguiente módulo:** Propinas TPV Service (`service.py` y `service_sql.py`)

**Razón:**
- Solo 2 referencias restantes
- Ambas para listar servidores SoftRestaurant
- Mismo patrón que T2.3
- Riesgo MEDIO-ALTO (afecta sincronización)

**Con T2.4 completado, Finanzas quedará 100% libre de MongoDB db.servers**

---

**Generado:** 2026-05-13
**Fase:** T2.3 — Migrar Propinas TPV Routes
