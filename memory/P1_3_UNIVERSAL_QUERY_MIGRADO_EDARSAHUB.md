# P1.3 — MIGRACIÓN universal_query/routes.py A EDARSAHUB SQL

**Fecha:** 2025-12-13
**Estado:** ✅ CERRADO

---

## OBJETIVO

Eliminar las 2 referencias funcionales a MongoDB `db.servers` en Universal Query y resolver conexiones desde EDARSAHUB SQL via server_registry.

---

## ARCHIVOS MODIFICADOS

### 1. `/app/backend/core/server_registry.py`

**Función agregada:** `get_server_connection_info_with_secrets(server_id)`

```python
def get_server_connection_info_with_secrets(server_id: str) -> Optional[Dict]:
    """
    USO INTERNO BACKEND - Obtiene configuración completa de conexión 
    incluyendo credenciales.
    
    FUENTE: EDARSAHUB.dbo.Servidores_Conexiones
    NO FUENTE: MongoDB db.servers
    
    SEGURIDAD:
    - NO exponer como endpoint público
    - NO imprimir password en logs
    - NO devolver password al frontend
    - Solo usar internamente para ejecutar conexión SQL
    """
```

### 2. `/app/backend/modules/universal_query/routes.py`

**Cambio 1 (línea ~164):** `get_server_and_validate()`
```python
# ANTES:
server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})

# DESPUÉS:
from core.server_registry import get_server_connection_info_with_secrets
server = get_server_connection_info_with_secrets(server_id)
```

**Cambio 2 (línea ~253):** `execute_universal_query_test()`
```python
# ANTES:
from server import db, decrypt_server_secrets, get_current_user
server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})

# DESPUÉS:
from server import decrypt_server_secrets, get_current_user
from core.server_registry import get_server_connection_info_with_secrets
server = get_server_connection_info_with_secrets(server_id)
```

---

## GREP ANTES/DESPUÉS

### ANTES
```
/app/backend/modules/universal_query/routes.py:164:    server = await db.servers.find_one(...)
/app/backend/modules/universal_query/routes.py:253:    server = await db.servers.find_one(...)
```

### DESPUÉS
```
(0 referencias funcionales a db.servers)
```

---

## VALIDACIONES

### Endpoint Universal Query
- ✅ `POST /api/servers/{id}/universal-query-test` con `test_type=conexion` - Server: 130° MERIDA
- ✅ `test_type=sql_libre` con SELECT simple - 1 row, success=true
- ✅ Query bloqueada (DROP TABLE) - status=blocked, error_code=BLOCKED_OPERATION
- ✅ Password NO expuesto en respuesta

### No Regresión
- ✅ Tablero Ejecutivo - 5 unidades
- ✅ Finanzas Tesorería - 4 sucursales
- ✅ Catálogos - Funcionando

---

## CONFIRMACIONES

- ✅ MongoDB eliminado de universal_query/routes.py
- ✅ Conexión viene de `EDARSAHUB.dbo.Servidores_Conexiones` via server_registry
- ✅ Función pública controlada creada (no depende de función privada)
- ✅ No se tocó frontend
- ✅ No se ejecutó SQL DDL
- ✅ No se modificaron datos
- ✅ Seguridad SQL mantenida (solo SELECT, keywords bloqueados)

---

## MÁXIMAS CUMPLIDAS

1. ✅ EDARSAHUB SQL es el cerebro del sistema
2. ✅ Servidores_Conexiones es fuente de conexiones
3. ✅ server_registry.py es la capa central
4. ✅ No se usa MongoDB
5. ✅ Password no expuesto al frontend

---

## SIGUIENTE FASE

**P1.4: Migrar Configuración/Servidores** a EDARSAHUB-first

---

## PENDIENTES SECURITY-P1

Ver documento: `/app/memory/SECURITY_P1_UNIVERSAL_QUERY.md`
