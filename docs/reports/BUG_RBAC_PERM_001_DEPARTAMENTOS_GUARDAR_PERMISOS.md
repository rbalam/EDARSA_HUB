# BUG-RBAC-PERM-001: Departamentos Sin Labels y Error al Guardar Permisos

**Fecha:** 14 de Diciembre de 2025  
**Estado:** ✅ RESUELTO  
**Prioridad:** P0 (Crítico)  
**Régimen:** Autorización Controlada

---

## 1. Causa Raíz - Nombres de Departamentos Vacíos

El endpoint `GET /api/servers/{server_id}/departamentos` devolvía un **array de strings** (`["002", "003"]`) en lugar de un **array de objetos** (`[{codigo: "002", descripcion: "002"}]`).

**Frontend esperaba:**
```javascript
// Usuarios.js línea 1840-1841
<label>{dep.descripcion || dep.codigo}</label>
```

**Backend devolvía:**
```json
["002", "003", "100", "004", "200", "400"]
```

**Resultado:** Checkboxes sin etiqueta visible porque `"002".descripcion` es `undefined`.

---

## 2. Causa Raíz - Error al Guardar Permisos

Después de migrar `get_all_users()` a EDARSAHUB SQL (BUG-AUTH-USERS-001), los IDs de usuario se devolvían en **MAYÚSCULAS** (formato SQL Server):
- **SQL devuelve:** `A5E56ED0-89B2-4D50-92F4-568A2106AB50`
- **MongoDB almacena:** `a5e56ed0-89b2-4d50-92f4-568a2106ab50`

Las funciones `find_user_by_id()` y `update_user()` hacían búsquedas **case-sensitive** en MongoDB, resultando en:
- `find_user_by_id()` → 404 "Usuario no encontrado"
- `update_user()` → Operación silenciosa sin coincidencias

---

## 3. Archivo Frontend Afectado

| Archivo | Líneas | Problema |
|---------|--------|----------|
| `/app/frontend/src/pages/Usuarios.js` | 1833-1843 | Esperaba `dep.codigo` y `dep.descripcion` |

---

## 4. Endpoints Backend Afectados

| Endpoint | Archivo | Problema |
|----------|---------|----------|
| `GET /api/servers/{id}/departamentos` | `server.py:2031-2065` | Devolvía strings en lugar de objetos |
| `PUT /api/users/{id}/permissions` | `routes.py:615-618` | Búsqueda case-sensitive fallaba |

---

## 5. Payload/Respuesta ANTES

**GET /api/servers/{id}/departamentos:**
```json
["002", "003", "100", "004", "200", "400"]
```

**PUT /api/users/A5E56ED0.../permissions:**
```json
{"detail": "Usuario no encontrado"}  // HTTP 404
```

---

## 6. Payload/Respuesta DESPUÉS

**GET /api/servers/{id}/departamentos:**
```json
[
  {"codigo": "002", "descripcion": "002"},
  {"codigo": "003", "descripcion": "003"},
  {"codigo": "100", "descripcion": "100"},
  {"codigo": "004", "descripcion": "004"},
  {"codigo": "200", "descripcion": "200"},
  {"codigo": "400", "descripcion": "400"}
]
```

**PUT /api/users/A5E56ED0.../permissions:**
```json
{"message": "Permisos actualizados"}  // HTTP 200
```

---

## 7. Campos Esperados por Frontend (Departamentos)

| Campo | Tipo | Obligatorio | Notas |
|-------|------|-------------|-------|
| `codigo` | string | ✅ | Usado como key y value |
| `descripcion` | string | ✅ | Usado como label visible |

---

## 8. Referencias MongoDB Encontradas (Deuda Técnica)

Las siguientes funciones aún usan MongoDB para escritura de permisos:

| Función | Archivo | Estado |
|---------|---------|--------|
| `update_user()` | `repository.py` | ✅ Corregido (case-insensitive) |
| `find_user_by_id()` | `repository.py` | ✅ Corregido (case-insensitive) |
| `create_user()` | `repository.py` | ⚠️ Sigue MongoDB |
| `deactivate_user()` | `repository.py` | ⚠️ Sigue MongoDB |

---

## 9. Cambios Realizados

### Archivo: `/app/backend/server.py`

**Función `get_departamentos()` (líneas 2056-2089):**
```python
# ANTES
departamentos = server.get('departamentos', [])
return departamentos  # Devolvía strings

# DESPUÉS
departamentos_raw = server.get('departamentos', [])
departamentos = []
for dep in departamentos_raw:
    if isinstance(dep, dict):
        departamentos.append({
            'codigo': dep.get('codigo') or str(dep),
            'descripcion': dep.get('descripcion') or dep.get('codigo') or str(dep)
        })
    elif isinstance(dep, str):
        departamentos.append({
            'codigo': dep,
            'descripcion': dep
        })
return departamentos  # Devuelve objetos
```

### Archivo: `/app/backend/modules/auth/repository.py`

**Función `find_user_by_id()` (líneas 53-75):**
```python
# ANTES
return await get_db().users.find_one({"id": user_id}, projection)

# DESPUÉS
user = await get_db().users.find_one({"id": user_id}, projection)
if not user:
    user = await get_db().users.find_one({"id": user_id.lower()}, projection)
if not user:
    user = await get_db().users.find_one({"id": user_id.upper()}, projection)
return user
```

**Función `update_user()` (líneas 215-230):**
```python
# ANTES
await get_db().users.update_one({"id": user_id}, {"$set": update_data})

# DESPUÉS (case-insensitive)
result = await get_db().users.update_one({"id": user_id}, {"$set": update_data})
if result.matched_count == 0:
    result = await get_db().users.update_one({"id": user_id.lower()}, {"$set": update_data})
if result.matched_count == 0:
    await get_db().users.update_one({"id": user_id.upper()}, {"$set": update_data})
```

**Función `get_all_users()` (líneas 78-172):**
- Enriquecimiento de permisos legacy (`allowed_servers`, `allowed_sucursales`, `allowed_warehouses`) desde MongoDB
- Limpieza de valores `None` en `allowed_warehouses`
- Preserva datos base de EDARSAHUB SQL

---

## 10. Confirmación EDARSAHUB SQL como Fuente

| Componente | Fuente | Notas |
|------------|--------|-------|
| Datos base de usuarios | ✅ EDARSAHUB SQL | Via `AuthRepositorySQL.list_all_users_sql()` |
| Roles | ✅ EDARSAHUB SQL | Via `Usuario_RolesAsignacion` |
| Empresas | ✅ EDARSAHUB SQL | Via `Usuario_EmpresasAsignacion` |
| Permisos legacy | ⚠️ MongoDB (temporal) | `allowed_servers`, `allowed_sucursales`, `allowed_warehouses` |
| Departamentos | ✅ EDARSAHUB SQL | Via `Servidores_Conexiones.departamentos` |

---

## 11. Confirmación No Regresión

| # | Validación | Resultado |
|---|------------|-----------|
| 1 | Login funciona | ✅ OK |
| 2 | /api/users (11 usuarios) | ✅ OK |
| 3 | /api/servers (8 servidores) | ✅ OK |
| 4 | Departamentos con {codigo, descripcion} | ✅ OK (6 departamentos CIENFUEGOS) |
| 5 | PUT permisos con UUID mayúsculas | ✅ HTTP 200 |
| 6 | Permisos persistidos en MongoDB | ✅ OK |
| 7 | Permisos devueltos via API | ✅ OK |
| 8 | No se exponen hashes/secrets | ✅ OK |
| 9 | SUPERADMIN acceso global | ✅ 5 empresas |
| 10 | Tarjetas muestran "X servidor(es) asignado(s)" | ✅ OK |

---

## 12. Evidencia Visual y Pruebas

**Prueba curl departamentos:**
```bash
$ curl /api/servers/6d053c22.../departamentos
[{"codigo":"002","descripcion":"002"},{"codigo":"003","descripcion":"003"},...]
```

**Prueba curl guardado permisos:**
```bash
$ curl -X PUT /api/users/A5E56ED0.../permissions \
  -d '{"allowed_warehouses":{"6d053c22...":["003","004"]}}'
{"message":"Permisos actualizados"}  # HTTP 200

# Verificación MongoDB
allowed_warehouses: {'6d053c22...': ['003', '004']}
```

**Screenshot:** Las tarjetas de usuarios muestran correctamente "X servidor(es) asignado(s)" con los permisos cargados desde MongoDB enriqueciendo datos SQL.

---

## Conclusión

**BUG-RBAC-PERM-001 RESUELTO.**

El modal de permisos ahora:
1. ✅ Muestra los nombres de departamentos (código como descripción si no hay más datos)
2. ✅ Guarda permisos correctamente con búsqueda case-insensitive
3. ✅ Persiste permisos después de recargar
4. ✅ EDARSAHUB SQL sigue siendo la fuente primaria de datos de usuario
5. ✅ Permisos legacy se leen/escriben en MongoDB (deuda técnica documentada)

---

**Validado por:** Agente E1  
**Fecha validación:** 14 de Diciembre de 2025  
