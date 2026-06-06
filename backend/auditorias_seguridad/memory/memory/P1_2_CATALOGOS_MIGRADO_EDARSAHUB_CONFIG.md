# P1.2 — MIGRACIÓN catalogos/repository.py A EDARSAHUB_CONFIG

**Fecha:** 2025-12-13
**Estado:** ✅ CERRADO

---

## OBJETIVO

Eliminar la dependencia funcional de MongoDB `db.servers` en el módulo de Catálogos.

---

## ARCHIVO MODIFICADO

`/app/backend/modules/catalogos/repository.py`

---

## CAMBIO IMPLEMENTADO

### ANTES (MongoDB)

```python
from core.db import execute_sql_query

EDARSA_HUB_SERVER_ID = "bea40259-35f1-4693-bda2-d2d10e13e56a"

async def get_edarsa_hub_connection(db) -> Dict:
    """Obtiene las credenciales del servidor EDARSA HUB desde MongoDB."""
    server = await db.servers.find_one({"id": EDARSA_HUB_SERVER_ID, "active": True})
    if not server:
        raise Exception("Servidor EDARSA HUB no configurado")
    return server
```

### DESPUÉS (EDARSAHUB_CONFIG)

```python
from core.db import execute_sql_query
from core.server_registry import EDARSAHUB_CONFIG

# ID del servidor EDARSA HUB (legacy - ya no se usa para conexión)
EDARSA_HUB_SERVER_ID = "bea40259-35f1-4693-bda2-d2d10e13e56a"

async def get_edarsa_hub_connection(db=None) -> Dict:
    """
    Obtiene las credenciales del servidor EDARSA HUB.
    
    FASE P1.2 (Dic 2025): Migrado de MongoDB db.servers a server_registry.EDARSAHUB_CONFIG.
    El parámetro `db` se mantiene por compatibilidad pero ya no se usa.
    
    FUENTE: core.server_registry.EDARSAHUB_CONFIG (variables de entorno)
    NO FUENTE: MongoDB db.servers
    """
    return {
        'host': EDARSAHUB_CONFIG['host'],
        'port': EDARSAHUB_CONFIG['port'],
        'database': EDARSAHUB_CONFIG['database'],
        'username': EDARSAHUB_CONFIG['username'],
        'password': EDARSAHUB_CONFIG['password'],
    }
```

---

## GREP ANTES/DESPUÉS

### ANTES
```
/app/backend/modules/catalogos/repository.py:31:    server = await db.servers.find_one({"id": EDARSA_HUB_SERVER_ID, "active": True})
```

### DESPUÉS
```
(0 referencias funcionales a db.servers)
```

---

## VALIDACIONES

### Endpoints de Catálogos
- ✅ `GET /api/catalogos/dominios` - 10 dominios
- ✅ `GET /api/catalogos/tabla/Global_Cat_Bancos` - 5 registros

### No Regresión
- ✅ `GET /api/comercial/tablero-ejecutivo` - 5 unidades
- ✅ `GET /api/finanzas/tesoreria/sucursales` - 4 sucursales

---

## CONFIRMACIONES

- ✅ MongoDB eliminado de catalogos/repository.py
- ✅ Conexión viene de `core.server_registry.EDARSAHUB_CONFIG`
- ✅ No se tocó frontend
- ✅ No se ejecutó SQL DDL
- ✅ No se modificaron datos
- ✅ Compatibilidad mantenida (parámetro `db` opcional)

---

## MÁXIMAS CUMPLIDAS

1. ✅ EDARSAHUB SQL es el cerebro del sistema
2. ✅ server_registry.py es la capa central
3. ✅ No se usa MongoDB para conexión
4. ✅ Cambio mínimo y quirúrgico

---

## SIGUIENTE FASE

**P1.3: Migrar `universal_query/routes.py`** a `server_registry`
