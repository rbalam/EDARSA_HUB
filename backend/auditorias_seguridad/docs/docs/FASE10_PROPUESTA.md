# FASE 10 - PROPUESTA: PROTECCIÓN REAL ADICIONAL MÓDULO SISTEMA
## Arquitectura de Seguridad EDARSA HUB

**Versión:** 1.0  
**Fecha:** Diciembre 2025  
**Estado:** PENDIENTE APROBACIÓN  
**Requisitos previos:** FASE 1-9 ✅

---

## 1. RESUMEN EJECUTIVO

Este documento propone expandir la **protección real de endpoints** a operaciones de escritura del módulo Sistema, consolidando el piloto RBAC antes de expandir a módulos operativos.

### Estado actual:

| Tipo | Endpoints protegidos |
|------|---------------------|
| Lectura (GET) | 2 (`/api/users`, `/api/roles`) |
| Escritura (PUT/POST/DELETE) | 0 |

### Objetivo FASE 10:

Proteger **operaciones de escritura** sobre usuarios y roles usando permisos ya existentes en el catálogo:

| Permiso existente | Endpoint candidato |
|-------------------|-------------------|
| `SISTEMA_USUARIOS_EDITAR` | `PUT /api/users/{id}` |
| `SISTEMA_USUARIOS_ELIMINAR` | `DELETE /api/users/{id}` |
| `SISTEMA_ROLES_EDITAR` | `PUT /api/roles/{id}` |
| `SISTEMA_ROLES_ELIMINAR` | `DELETE /api/roles/{id}` |

---

## 2. DIAGNÓSTICO DEL MEJOR PUNTO DE EXPANSIÓN

### 2.1 Criterios de selección

| Criterio | Peso | Descripción |
|----------|------|-------------|
| Continuidad | CRÍTICO | Mismo dominio que FASE 9 |
| Permisos existentes | ALTO | Ya en catálogo `sec_permisos_catalogo` |
| Bajo riesgo | ALTO | No toca módulos operativos |
| Coherencia funcional | ALTO | CRUD completo de usuarios/roles |

### 2.2 Análisis de endpoints candidatos

| Endpoint | Permiso requerido | Protección actual | Riesgo |
|----------|-------------------|-------------------|--------|
| `PUT /api/users/{id}` | `SISTEMA_USUARIOS_EDITAR` | `role_level >= 3` | BAJO |
| `DELETE /api/users/{id}` | `SISTEMA_USUARIOS_ELIMINAR` | `role_level >= 3` | BAJO |
| `PUT /api/roles/{id}` | `SISTEMA_ROLES_EDITAR` | `role_level >= 3` | BAJO |
| `DELETE /api/roles/{id}` | `SISTEMA_ROLES_ELIMINAR` | `role_level >= 3` | BAJO |
| `POST /api/users` | `SISTEMA_USUARIOS_CREAR` | N/A (no existe) | N/A |
| `POST /api/roles` | `SISTEMA_ROLES_CREAR` | `role_level >= 3` | BAJO |

### 2.3 Recomendación

Proteger **únicamente las operaciones PUT y DELETE** que ya existen, usando el mismo patrón de FASE 9:
1. Verificar permiso RBAC
2. Si no tiene RBAC → fallback legacy (role_level >= 3)
3. Si no cumple ninguna → 403

---

## 3. OPCIÓN A: PROTEGER SOLO USUARIOS (MENOR RIESGO)

### 3.1 Descripción

Proteger **solo operaciones de escritura sobre usuarios**.

### 3.2 Endpoints a proteger

| Endpoint | Permiso |
|----------|---------|
| `PUT /api/users/{id}` | `SISTEMA_USUARIOS_EDITAR` |
| `DELETE /api/users/{id}` | `SISTEMA_USUARIOS_ELIMINAR` |

### 3.3 Cambios en whitelist

```python
# ANTES (FASE 9)
PERMISOS_FASE_8_WHITELIST = ["SISTEMA_ESTRUCTURA_VER", "SISTEMA_USUARIOS_VER", "SISTEMA_ROLES_VER"]

# DESPUÉS (FASE 10 - OPCIÓN A)
PERMISOS_FASE_10_WHITELIST = [
    "SISTEMA_ESTRUCTURA_VER",
    "SISTEMA_USUARIOS_VER", 
    "SISTEMA_USUARIOS_EDITAR",   # Nuevo
    "SISTEMA_USUARIOS_ELIMINAR", # Nuevo
    "SISTEMA_ROLES_VER"
]
```

### 3.4 Archivos a modificar

| Archivo | Cambio | Líneas |
|---------|--------|--------|
| `/app/backend/server.py` | Actualizar whitelist | +2 líneas |
| `/app/backend/modules/auth/service.py` | Verificación RBAC en `update_user()`, `delete_user()` | +20 líneas |
| `/app/frontend/src/pages/Usuarios.js` | Actualizar constantes UI | +2 líneas |

### 3.5 Rollback

```
TIEMPO: 3 minutos
1. Revertir whitelist
2. Revertir service.py
3. Revertir Usuarios.js
```

---

## 4. OPCIÓN B: PROTEGER USUARIOS Y ROLES (RIESGO BAJO)

### 4.1 Descripción

Proteger **operaciones de escritura sobre usuarios Y roles** en una sola iteración.

### 4.2 Endpoints a proteger

| Endpoint | Permiso |
|----------|---------|
| `PUT /api/users/{id}` | `SISTEMA_USUARIOS_EDITAR` |
| `DELETE /api/users/{id}` | `SISTEMA_USUARIOS_ELIMINAR` |
| `PUT /api/roles/{id}` | `SISTEMA_ROLES_EDITAR` |
| `DELETE /api/roles/{id}` | `SISTEMA_ROLES_ELIMINAR` |

### 4.3 Cambios en whitelist

```python
PERMISOS_FASE_10_WHITELIST = [
    "SISTEMA_ESTRUCTURA_VER",
    "SISTEMA_USUARIOS_VER", 
    "SISTEMA_USUARIOS_EDITAR",   # Nuevo
    "SISTEMA_USUARIOS_ELIMINAR", # Nuevo
    "SISTEMA_ROLES_VER",
    "SISTEMA_ROLES_EDITAR",      # Nuevo
    "SISTEMA_ROLES_ELIMINAR"     # Nuevo
]
```

### 4.4 Nuevo rol propuesto

```json
{
  "codigo": "ADMIN_USUARIOS",
  "nombre": "Administrador de Usuarios",
  "descripcion": "Rol piloto FASE 10 - CRUD completo de usuarios",
  "permisos": [
    "SISTEMA_USUARIOS_VER",
    "SISTEMA_USUARIOS_EDITAR",
    "SISTEMA_USUARIOS_ELIMINAR"
  ],
  "activo": true,
  "fase": "FASE_10"
}
```

### 4.5 Archivos a modificar

| Archivo | Cambio | Líneas |
|---------|--------|--------|
| `/app/backend/server.py` | Actualizar whitelist | +4 líneas |
| `/app/backend/modules/auth/service.py` | Verificación RBAC en 4 funciones | +40 líneas |
| `/app/frontend/src/pages/Usuarios.js` | Actualizar constantes UI | +4 líneas |

### 4.6 Rollback

```
TIEMPO: 4 minutos
```

---

## 5. OPCIÓN C: PROTEGER CRUD COMPLETO + CREAR (RIESGO MEDIO)

### 5.1 Descripción

Proteger **todas las operaciones CRUD** incluyendo creación.

### 5.2 Endpoints a proteger

| Endpoint | Permiso |
|----------|---------|
| `POST /api/users` | `SISTEMA_USUARIOS_CREAR` |
| `PUT /api/users/{id}` | `SISTEMA_USUARIOS_EDITAR` |
| `DELETE /api/users/{id}` | `SISTEMA_USUARIOS_ELIMINAR` |
| `POST /api/roles` | `SISTEMA_ROLES_CREAR` |
| `PUT /api/roles/{id}` | `SISTEMA_ROLES_EDITAR` |
| `DELETE /api/roles/{id}` | `SISTEMA_ROLES_ELIMINAR` |

### 5.3 Por qué NO es recomendado para FASE 10

- Mayor superficie de cambio (6 endpoints)
- `POST /api/users` tiene lógica compleja de validación
- Riesgo de afectar flujos de onboarding
- Mejor dividir en dos fases

---

## 6. RECOMENDACIÓN

### 6.1 Opción recomendada: **OPCIÓN B - Proteger Usuarios y Roles**

| Criterio | Evaluación |
|----------|------------|
| Coherencia funcional | ✅ CRUD parcial (VER + EDITAR + ELIMINAR) |
| Permisos ya en catálogo | ✅ Los 4 permisos existen |
| Mismo patrón FASE 9 | ✅ Reutiliza helper |
| Rol útil | ✅ ADMIN_USUARIOS para delegación |
| Rollback simple | ✅ 4 minutos |

### 6.2 Justificación

1. **Continuidad**: Mismos endpoints que FASE 9, ahora protegiendo escritura
2. **Delegación**: Permite que un Supervisor con rol ADMIN_USUARIOS gestione usuarios sin ser Administrador completo
3. **Caso de uso real**: Delegar gestión de usuarios a un responsable de área
4. **Sin riesgo de crear**: No toca `POST` que tiene validaciones complejas

---

## 7. ALCANCE EXACTO RECOMENDADO

### 7.1 Permisos a agregar a whitelist

| Permiso | Descripción |
|---------|-------------|
| `SISTEMA_USUARIOS_EDITAR` | Permite `PUT /api/users/{id}` |
| `SISTEMA_USUARIOS_ELIMINAR` | Permite `DELETE /api/users/{id}` |
| `SISTEMA_ROLES_EDITAR` | Permite `PUT /api/roles/{id}` |
| `SISTEMA_ROLES_ELIMINAR` | Permite `DELETE /api/roles/{id}` |

### 7.2 Rol nuevo a crear

```json
{
  "codigo": "ADMIN_USUARIOS",
  "nombre": "Administrador de Usuarios",
  "permisos": [
    "SISTEMA_USUARIOS_VER",
    "SISTEMA_USUARIOS_EDITAR",
    "SISTEMA_USUARIOS_ELIMINAR"
  ],
  "fase": "FASE_10"
}
```

### 7.3 Whitelist final FASE 10

```python
# Permisos
PERMISOS_FASE_10_WHITELIST = [
    "SISTEMA_ESTRUCTURA_VER",      # FASE 4
    "SISTEMA_USUARIOS_VER",        # FASE 8
    "SISTEMA_USUARIOS_EDITAR",     # FASE 10
    "SISTEMA_USUARIOS_ELIMINAR",   # FASE 10
    "SISTEMA_ROLES_VER",           # FASE 8
    "SISTEMA_ROLES_EDITAR",        # FASE 10
    "SISTEMA_ROLES_ELIMINAR"       # FASE 10
]

# Roles
ROLES_FASE_10_WHITELIST = [
    "VISOR_ESTRUCTURA",   # FASE 5
    "VISOR_SISTEMA",      # FASE 6
    "VISOR_ADMIN",        # FASE 8
    "ADMIN_USUARIOS"      # FASE 10
]
```

---

## 8. ARCHIVOS A TOCAR

### 8.1 Backend

| Archivo | Cambio | Líneas |
|---------|--------|--------|
| `/app/backend/server.py` | Actualizar whitelists | +5 líneas |
| `/app/backend/modules/auth/service.py` | Verificación RBAC en 4 funciones | +40 líneas |

### 8.2 Frontend

| Archivo | Cambio | Líneas |
|---------|--------|--------|
| `/app/frontend/src/pages/Usuarios.js` | Actualizar constantes | +5 líneas |

### 8.3 MongoDB

| Colección | Operación |
|-----------|-----------|
| `sec_roles` | INSERT (ADMIN_USUARIOS) |

---

## 9. COMPATIBILIDAD LEGACY

| Campo | Estado |
|-------|--------|
| `users.role` | ✅ INTACTO (fallback) |
| `users.rbac_role` | ✅ INTACTO |
| Fallback `role_level >= 3` | ✅ Preservado |

---

## 10. RIESGOS Y MITIGACIONES

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|--------|--------------|---------|------------|
| 1 | Romper edición de usuarios | BAJA | ALTO | Fallback legacy preservado |
| 2 | Romper eliminación de usuarios | BAJA | ALTO | Fallback legacy preservado |
| 3 | Confusión con permisos | BAJA | BAJO | Nombres claros, documentación |

---

## 11. QUÉ NO SE TOCARÁ

| Elemento | Confirmación |
|----------|--------------|
| `POST /api/users` (crear) | ❌ NO EN FASE 10 |
| `POST /api/roles` (crear) | ❌ NO EN FASE 10 |
| `get_current_user()` | ❌ NO SE MODIFICA |
| `Layout.js` | ❌ NO SE MODIFICA |
| Módulos operativos | ❌ NO SE MODIFICA |
| Dashboards | ❌ NO SE MODIFICA |

---

## 12. ROLLBACK

```
TIEMPO: 4 minutos

1. Revertir whitelists en server.py
2. Revertir service.py (4 funciones)
3. Revertir Usuarios.js
4. Opcional: db.sec_roles.deleteOne({codigo: "ADMIN_USUARIOS"})
```

---

## 13. CHECKLIST DE NO REGRESIÓN

### 13.1 Post-implementación

| Verificación | Resultado esperado |
|--------------|-------------------|
| SuperAdmin → PUT /api/users/{id} | ✅ 200 |
| SuperAdmin → DELETE /api/users/{id} | ✅ 200 |
| Administrador legacy → PUT /api/users/{id} | ✅ 200 (fallback) |
| Supervisor sin RBAC → PUT /api/users/{id} | ❌ 403 |
| **Supervisor CON ADMIN_USUARIOS → PUT /api/users/{id}** | ✅ 200 |
| FASE 4-9 | ✅ Sin regresión |
| UI FASE 7 | ✅ Muestra nuevos permisos |

---

## 14. SOLICITUD DE APROBACIÓN

### 14.1 Resumen

| # | Elemento |
|---|----------|
| 1 | Agregar 4 permisos a whitelist |
| 2 | Crear rol ADMIN_USUARIOS |
| 3 | Proteger PUT/DELETE users |
| 4 | Proteger PUT/DELETE roles |

### 14.2 Lo que NO se hace

- ❌ POST (crear) no se protege
- ❌ Módulos operativos no se tocan

### 14.3 Decisión solicitada

**¿Aprueba FASE 10 OPCIÓN B?**

- [ ] SÍ, proceder con OPCIÓN B
- [ ] NO, requiere ajustes
- [ ] PREFERIR OPCIÓN A (solo usuarios)
- [ ] DIFERIR

---

**FIN DEL DOCUMENTO DE PROPUESTA FASE 10**
