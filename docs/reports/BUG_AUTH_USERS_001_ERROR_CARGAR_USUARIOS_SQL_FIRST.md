# BUG-AUTH-USERS-001: Error al Cargar Usuarios (SQL-First)

**Fecha:** 14 de Diciembre de 2025  
**Estado:** ✅ RESUELTO  
**Prioridad:** P0 (Crítico)  
**Régimen:** Autorización Controlada

---

## 1. Causa Raíz

El endpoint `GET /api/users` fallaba con **HTTP 500** porque la función `get_all_users()` en `/app/backend/modules/auth/repository.py` todavía consultaba MongoDB (`db.users.find()`) después de la migración SQL-first de Auth/RBAC en FASE 2-G.

**Problema específico:**
- `get_current_user()` ya usaba EDARSAHUB SQL (FASE 2-G)
- `get_all_users()` seguía usando MongoDB
- MongoDB retornaba usuarios con campos `allowed_warehouses` conteniendo valores `None`
- El modelo Pydantic `User` (schema) esperaba `Dict[str, List[str]]`, no permitía `None` en las listas
- Resultado: `fastapi.exceptions.ResponseValidationError`

---

## 2. Endpoint Afectado

| Endpoint | Método | Archivo Backend |
|----------|--------|-----------------|
| `/api/users` | GET | `/app/backend/modules/auth/routes.py:597` |

**Ruta del servicio:**  
`routes.py` → `service.py:get_all_users_filtered()` → `repository.py:get_all_users()`

---

## 3. Archivo Frontend Afectado

| Archivo | Función | Línea |
|---------|---------|-------|
| `/app/frontend/src/pages/Usuarios.js` | `loadUsers()` | 107-117 |

```javascript
const loadUsers = useCallback(async () => {
  try {
    const response = await api.get('/users');
    setUsers(Array.isArray(response.data) ? response.data : []);
  } catch (error) {
    toast.error('Error al cargar usuarios');  // <- Este mensaje aparecía
    setUsers([]);
  } finally {
    setLoading(false);
  }
}, []);
```

---

## 4. Archivo Backend Afectado

| Archivo | Función | Estado |
|---------|---------|--------|
| `/app/backend/modules/auth/repository.py` | `get_all_users()` | ✅ Corregido |
| `/app/backend/modules/auth/repository.py` | `get_users_by_empresas()` | ✅ Corregido |

---

## 5. Respuesta ANTES (MongoDB - Error 500)

```json
{
  "detail": "Internal Server Error"
}
```

**Log del servidor:**
```
fastapi.exceptions.ResponseValidationError: 2 validation errors:
  {'type': 'string_type', 'loc': ('response', 2, 'allowed_warehouses', '...', 0), 
   'msg': 'Input should be a valid string', 'input': None}
```

---

## 6. Respuesta DESPUÉS (EDARSAHUB SQL - 200 OK)

```json
[
  {
    "id": "0DA77B7B-FE88-4E23-98BC-9CBF543D5EE3",
    "email": "admin@inventario.com",
    "name": "Administrador",
    "role": "SuperAdministrador",
    "active": true,
    "sucursales": [],
    "allowed_servers": [],
    "allowed_sucursales": {},
    "allowed_warehouses": {},
    "empresas_permitidas": ["31784356-...", "1118f83c-...", ...],
    "empresa_default_id": "31784356-6d0b-47ce-8fe8-c8a442e45a07",
    "_source": "EDARSAHUB_SQL"
  },
  // ... 10 usuarios más
]
```

**Total usuarios:** 11 (todos productivos, ningún @test.com)

---

## 7. Campos Esperados por Frontend

| Campo | Tipo | Obligatorio | Notas |
|-------|------|-------------|-------|
| `id` | string | ✅ | PublicUUID de Usuario_Catalogo |
| `email` | string | ✅ | Email único |
| `name` | string | ✅ | Nombre del usuario |
| `role` | string | ✅ | SuperAdministrador, Administrador, Supervisor, Usuario |
| `active` | boolean | ✅ | Estado activo/inactivo |
| `sucursales` | string[] | ❌ | Legacy, devuelve [] |
| `allowed_servers` | string[] | ❌ | Legacy, devuelve [] |
| `allowed_sucursales` | Dict | ❌ | Legacy, devuelve {} |
| `allowed_warehouses` | Dict | ❌ | Legacy, devuelve {} |
| `empresas_permitidas` | string[] | ❌ | UUIDs de empresas asignadas |
| `empresa_default_id` | string | ❌ | UUID empresa principal |

---

## 8. Referencias MongoDB Encontradas (Eliminadas)

```python
# ANTES (repository.py línea 61-63):
async def get_all_users() -> List[Dict]:
    """Obtiene todos los usuarios sin contraseña."""
    return await get_db().users.find({}, {"_id": 0, "password": 0}).to_list(1000)

# ANTES (repository.py línea 80-83):
async def get_users_by_empresas(empresas_ids: List[str]) -> List[Dict]:
    return await get_db().users.find(
        {"empresa_default_id": {"$in": empresas_ids}},
        {"_id": 0, "password": 0}
    ).to_list(1000)
```

---

## 9. Cambios Realizados

### Archivo: `/app/backend/modules/auth/repository.py`

**Función `get_all_users()` (líneas 61-105):**
- Eliminada consulta a MongoDB `db.users.find()`
- Importa `AuthRepositorySQL` de `core.auth.user_repository_sql`
- Llama `repo_sql.list_all_users_sql()` para obtener usuarios de EDARSAHUB
- Mapea respuesta a estructura compatible con Pydantic `User` schema
- NO hace fallback a MongoDB si falla SQL

**Función `get_users_by_empresas()` (líneas 108-137):**
- Eliminada consulta a MongoDB
- Reutiliza `get_all_users()` (SQL)
- Filtra por `empresa_default_id` o `empresas_permitidas`

---

## 10. Validación No Regresión

| # | Validación | Resultado |
|---|------------|-----------|
| 1 | Login funciona | ✅ OK |
| 2 | Usuarios/Roles → pestaña Usuarios carga | ✅ OK (11 usuarios) |
| 3 | Muestra 11 usuarios productivos SQL | ✅ OK |
| 4 | No aparecen usuarios @test.com | ✅ OK (0 encontrados) |
| 5 | Roles tab funciona | ✅ OK (4 roles) |
| 6 | Permisos Catálogos tab funciona | ✅ Visible |
| 7 | Estructura tab funciona | ✅ Visible |
| 8 | Bitácora RBAC tab funciona | ✅ Visible |
| 9 | /api/servers devuelve 8 | ✅ OK |
| 10 | Tablero Ejecutivo | ✅ Accesible (menú) |
| 11 | Comercial V2 | ✅ Accesible (menú) |
| 12 | Finanzas | ✅ Accesible (menú) |
| 13 | Inventarios/Catálogos | ✅ Accesible (menú) |
| 14 | No se exponen hashes/secretos | ✅ OK |
| 15 | No se reactivó MongoDB | ✅ Confirmado |

---

## 11. Riesgos Residuales

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| Campos legacy (`allowed_servers`, `allowed_sucursales`, `allowed_warehouses`) devuelven vacíos | **Baja** | Estos campos eran heredados de MongoDB y no están migrados a SQL. El frontend los maneja como opcionales. |
| `create_user()`, `update_user()`, `deactivate_user()` siguen usando MongoDB | **Media** | Fuera del alcance de este bug fix. Operaciones de escritura de usuarios deben migrarse en fase futura. |
| `find_user_by_email()` y `find_user_by_id()` siguen usando MongoDB (para login) | **Media** | Login usa MongoDB para validación de password. Migración pendiente pero no bloquea este fix. |

---

## Conclusión

**BUG-AUTH-USERS-001 RESUELTO.**

La pestaña "Usuarios y Roles" → "Usuarios" ahora carga correctamente 11 usuarios productivos desde EDARSAHUB SQL sin exponer información sensible y sin reactivar MongoDB como fuente primaria de datos de usuarios.

---

**Validado por:** Agente E1  
**Fecha validación:** 14 de Diciembre de 2025  
**Screenshot:** La pantalla muestra "11 usuario(s) registrado(s)" con todos los usuarios visibles y funcionales.
