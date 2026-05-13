# FASE T2.1: REPORTE DE MIGRACIÓN CONEXIÓN EDARSAHUB
**Fecha:** 2026-05-13
**Estado:** ✅ COMPLETADO

---

## 1. RESUMEN EJECUTIVO

| Aspecto | Resultado |
|---------|-----------|
| **Archivos modificados** | 3 |
| **Referencias db.servers eliminadas** | 3 |
| **Endpoints probados** | 4 |
| **MongoDB utilizado** | NO |
| **Tablero Ejecutivo** | ✅ Sin regresión |

---

## 2. ARCHIVOS MODIFICADOS

### 2.1 `/app/backend/modules/finanzas/repository_real.py`

**Referencia eliminada:** `db.servers.find_one({id: EDARSA_HUB_SERVER_ID})`

**Código anterior:**
```python
server = await self.db.servers.find_one({
    "id": EDARSA_HUB_SERVER_ID,
    "active": True
})
```

**Código nuevo:**
```python
from core.server_registry import EDARSAHUB_CONFIG

self._server_cache = {
    'host': EDARSAHUB_CONFIG['host'],
    'port': EDARSAHUB_CONFIG['port'],
    'database': EDARSAHUB_CONFIG['database'],
    'username': EDARSAHUB_CONFIG['username'],
    'password': EDARSAHUB_CONFIG['password'],
    'id': EDARSA_HUB_SERVER_ID,
    'config_origin': 'EDARSAHUB_CONFIG'
}
```

---

### 2.2 `/app/backend/modules/finanzas/historical_kpis_repository.py`

**Referencia eliminada:** `db.servers.find_one({name: 'EDARSA HUB'})`

**Código anterior:**
```python
from pymongo import MongoClient
client = MongoClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]
srv = db.servers.find_one({'name': 'EDARSA HUB', 'active': True})
```

**Código nuevo:**
```python
from core.server_registry import EDARSAHUB_CONFIG

return {
    "host": EDARSAHUB_CONFIG['host'],
    "port": EDARSAHUB_CONFIG['port'],
    "database": EDARSAHUB_CONFIG['database'],
    "username": EDARSAHUB_CONFIG['username'],
    "password": EDARSAHUB_CONFIG['password'],
    "config_origin": "EDARSAHUB_CONFIG"
}
```

---

### 2.3 `/app/backend/modules/finanzas/propinas_tpv/sql_repository.py`

**Referencia eliminada:** `mongo_db.servers.find_one({id: EDARSA_HUB_SERVER_ID})`

**Código anterior:**
```python
server = await self.mongo_db.servers.find_one(
    {"id": EDARSA_HUB_SERVER_ID, "active": True},
    {"_id": 0}
)
```

**Código nuevo:**
```python
from core.server_registry import EDARSAHUB_CONFIG

_server_cache = {
    'host': EDARSAHUB_CONFIG['host'],
    'port': EDARSAHUB_CONFIG['port'],
    'database': EDARSAHUB_CONFIG['database'],
    'username': EDARSAHUB_CONFIG['username'],
    'password': EDARSAHUB_CONFIG['password'],
    'config_origin': 'EDARSAHUB_CONFIG'
}
```

---

## 3. FUNCIÓN DE SERVER_REGISTRY USADA

`EDARSAHUB_CONFIG` desde `/app/backend/core/server_registry.py`

```python
EDARSAHUB_CONFIG = {
    'host': os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
    'port': int(os.environ.get('EDARSAHUB_PORT', 1433)),
    'database': os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
    'username': os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
    'password': os.environ.get('EDARSAHUB_PASSWORD', 'National09$'),
}
```

---

## 4. ENDPOINTS PROBADOS

| # | Endpoint | Resultado |
|---|----------|-----------|
| 1 | `GET /api/finanzas/cuentas-por-pagar/resumen` | ✅ OK |
| 2 | `GET /api/finanzas/tesoreria/sucursales` | ✅ OK (4 sucursales) |
| 3 | `GET /api/v2/comercial/dashboard` | ✅ 5 unidades, sin regresión |
| 4 | Backend startup | ✅ Sin errores de import |

---

## 5. CONFIRMACIONES

| Confirmación | Estado |
|--------------|--------|
| No se cambió lógica de negocio | ✅ CONFIRMADO |
| No se usó MongoDB para conexión EDARSAHUB | ✅ CONFIRMADO |
| No se tocó Tesorería lógica funcional | ✅ CONFIRMADO |
| No se tocó Propinas TPV (otros endpoints) | ✅ CONFIRMADO |
| No se tocó Compras | ✅ CONFIRMADO |
| No se tocó Comercial | ✅ CONFIRMADO |
| No se tocó Auth/RBAC | ✅ CONFIRMADO |
| No se tocó frontend | ✅ CONFIRMADO |
| Tablero Ejecutivo sin regresión | ✅ CONFIRMADO |

---

## 6. REFERENCIAS db.servers RESTANTES EN FINANZAS

Después de FASE T2.1, quedan **9 referencias** en Finanzas (NO para conexión EDARSAHUB):

| Archivo | Propósito | Fase |
|---------|-----------|------|
| `tesoreria.py:636` | Listar servidores operativos | T2.2 |
| `propinas_tpv/service.py:79` | Listar servidores SR | T2.4 |
| `propinas_tpv/routes_sql.py:408,440,516` | Detectar esquema | T2.3 |
| `propinas_tpv/routes.py:222,262,358` | Detectar esquema | T2.3 |

---

## 7. RECOMENDACIÓN PARA FASE T2.2

**Siguiente módulo:** Tesorería (`tesoreria.py`)

**Razón:** 
- Solo 1 referencia a `db.servers`
- Es **fallback** — Ya tiene lógica EDARSAHUB primero
- Función: `_get_servidores_operativos_mongo_fallback()`
- Reemplazar por: `get_visible_servers_for_operaciones()`

**Riesgo:** BAJO

---

**Generado:** 2026-05-13
**Fase:** T2.1 — Migrar Conexión EDARSAHUB
