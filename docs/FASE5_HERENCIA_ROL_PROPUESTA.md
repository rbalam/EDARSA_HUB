# FASE 5 - PROPUESTA: HERENCIA DE PERMISOS POR ROL
## Arquitectura de Seguridad EDARSA HUB

**Versión:** 1.0  
**Fecha:** Diciembre 2025  
**Estado:** PENDIENTE APROBACIÓN  
**Requisitos previos:** FASE 1 ✅ | FASE 2 ✅ | FASE 3 ✅ | FASE 4 ✅

---

## 1. RESUMEN EJECUTIVO

Este documento propone 3 opciones para la FASE 5 del sistema RBAC, enfocada en implementar **herencia de permisos por rol** de forma controlada, permitiendo que un usuario herede permisos de un rol nuevo (`sec_roles`) además de sus permisos directos (`sec_permisos`).

### Objetivo del piloto FASE 5:

Probar que un usuario puede heredar permisos de un rol nuevo del sistema `sec_*` sin:
- Modificar el sistema legacy (`roles`, `rbac_roles`)
- Afectar el flujo de login
- Tocar `get_current_user()`
- Generar regresiones

### Estado actual de roles:

| Colección | Propósito | Estado |
|-----------|-----------|--------|
| `roles` | Roles legacy por módulo | ✅ 4 roles activos |
| `rbac_roles` | Roles de finanzas (ADMIN, DIRECCION, etc.) | ✅ 7 roles activos |
| `sec_roles` | Roles nuevos con permisos granulares | ❌ **NO EXISTE** |

### Distribución actual de usuarios por rol legacy:

| Rol Legacy | Usuarios |
|------------|----------|
| SuperAdministrador | 1 |
| Administrador | 2 |
| Supervisor | 7 |
| Usuario | 5 |
| Otros (admin, Admin) | 2 |

---

## 2. DIAGNÓSTICO DEL PUNTO DE ENTRADA

### 2.1 Arquitectura de permisos propuesta (3 capas)

```
┌─────────────────────────────────────────────────────────────────┐
│                    PERMISOS EFECTIVOS                           │
│  (Lo que el usuario PUEDE hacer)                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. PERMISOS DIRECTOS (users.sec_permisos)                     │
│     └─ FASE 4: Ya implementado                                 │
│                                                                 │
│  2. PERMISOS POR ROL NUEVO (sec_roles.permisos)                │
│     └─ FASE 5: ESTE PILOTO                                     │
│     └─ Lectura de users.sec_rol → sec_roles.permisos           │
│                                                                 │
│  3. FALLBACK LEGACY (users.role)                               │
│     └─ FASE 3: SuperAdmin tiene todo                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Criterios de selección del piloto

| Criterio | Peso | Mejor opción |
|----------|------|--------------|
| No crear nueva colección compleja | ALTO | Colección simple `sec_roles` |
| No migrar usuarios | CRÍTICO | Campo opcional `sec_rol` |
| No tocar `get_current_user` | CRÍTICO | Helper aislado |
| Probar herencia con 1 rol | ALTO | Crear rol piloto específico |
| Reutilizar permiso existente | ALTO | `SISTEMA_ESTRUCTURA_VER` |

---

## 3. OPCIÓN A: ROL PILOTO AISLADO (MENOR RIESGO)

### 3.1 Descripción

Crear una colección `sec_roles` mínima con UN SOLO ROL piloto que contiene el permiso `SISTEMA_ESTRUCTURA_VER`. Los usuarios pueden recibir este rol vía campo `sec_rol` y heredar sus permisos.

### 3.2 Alcance exacto

| Elemento | Valor |
|----------|-------|
| **Colección nueva** | `sec_roles` (mínima) |
| **Rol piloto** | `VISOR_ESTRUCTURA` |
| **Permisos del rol** | `["SISTEMA_ESTRUCTURA_VER"]` |
| **Campo nuevo en users** | `sec_rol` (string, opcional) |
| **Endpoint nuevo** | `POST /api/admin/roles/asignar` |
| **Quién administra** | Solo SuperAdministrador |

### 3.3 Estructura de sec_roles

```json
{
  "id": "uuid",
  "codigo": "VISOR_ESTRUCTURA",
  "nombre": "Visor de Estructura",
  "descripcion": "Rol piloto FASE 5 - puede ver estructura organizacional",
  "permisos": ["SISTEMA_ESTRUCTURA_VER"],
  "activo": true,
  "es_sistema": true,
  "fase": "FASE_5",
  "created_at": "ISODate"
}
```

### 3.4 Flujo de resolución de permisos (actualizado)

```python
async def tiene_permiso_v5(user: dict, permiso: str) -> bool:
    """
    FASE 5: Resolución de permisos con herencia por rol.
    
    Orden de precedencia:
    1. Permisos directos (sec_permisos)
    2. Permisos heredados por rol (sec_rol → sec_roles.permisos)
    3. Fallback legacy (SuperAdmin tiene todo)
    """
    # 1. Permisos directos (FASE 4)
    permisos_directos = user.get('sec_permisos', [])
    if permiso in permisos_directos:
        return True
    
    # 2. Permisos por rol nuevo (FASE 5)
    sec_rol = user.get('sec_rol')
    if sec_rol:
        rol = await db.sec_roles.find_one({"codigo": sec_rol, "activo": True})
        if rol and permiso in rol.get('permisos', []):
            return True
    
    # 3. Fallback legacy
    if user.get('role') == 'SuperAdministrador':
        return True
    
    return False
```

### 3.5 Endpoint de asignación de rol

```python
@api_router.post("/admin/roles/asignar")
async def admin_asignar_rol(request: RolAsignacionRequest, ...):
    """
    FASE 5: Asigna o retira un rol sec_* a un usuario.
    Solo SuperAdministrador puede ejecutar.
    Solo roles en whitelist FASE 5.
    """
```

### 3.6 Archivos a modificar

| Archivo | Cambio | Líneas aprox. |
|---------|--------|---------------|
| `/app/backend/server.py` | Crear colección, endpoint, helper | +100 líneas |

### 3.7 Colecciones

| Colección | Operación |
|-----------|-----------|
| `sec_roles` | CREATE (nueva), READ |
| `users` | UPDATE (solo campo `sec_rol`) |
| `sec_bitacora_admin` | INSERT (auditoría) |

### 3.8 Whitelist FASE 5

```python
ROLES_FASE_5_WHITELIST = ["VISOR_ESTRUCTURA"]
```

### 3.9 Compatibilidad legacy

| Elemento | Impacto |
|----------|---------|
| `users.role` | ❌ NO SE TOCA |
| `users.rbac_role` | ❌ NO SE TOCA |
| `roles` | ❌ NO SE TOCA |
| `rbac_roles` | ❌ NO SE TOCA |
| `get_current_user()` | ❌ NO SE TOCA |

### 3.10 Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Colisión con roles legacy | MUY BAJA | BAJO | Nombres diferentes, colección separada |
| Usuario pierde acceso | BAJA | BAJO | Fallback a permisos directos y legacy |
| Complejidad de resolución | BAJA | BAJO | Orden de precedencia claro |

### 3.11 Rollback

```
TIEMPO: 3 minutos
1. Eliminar endpoint /api/admin/roles/asignar
2. Eliminar helper tiene_permiso_v5 (o revertir a v4)
3. Opcional: db.sec_roles.drop()
4. Opcional: db.users.updateMany({}, {$unset: {sec_rol: 1}})
```

---

## 4. OPCIÓN B: HERENCIA CON MÚLTIPLES ROLES (RIESGO MEDIO)

### 4.1 Descripción

Similar a Opción A, pero permitiendo que un usuario tenga MÚLTIPLES roles nuevos (array `sec_roles` en lugar de string `sec_rol`).

### 4.2 Diferencias con Opción A

| Aspecto | Opción A | Opción B |
|---------|----------|----------|
| Campo en users | `sec_rol: string` | `sec_roles: [string]` |
| Roles por usuario | 1 | Múltiples |
| Complejidad | Baja | Media |
| Resolución | Simple | Unión de permisos |

### 4.3 Por qué NO es recomendado para FASE 5

- Mayor complejidad sin beneficio inmediato
- El piloto solo necesita 1 rol
- Múltiples roles se puede agregar en FASE 6

---

## 5. OPCIÓN C: MIGRACIÓN PARCIAL DE ROLES LEGACY (RIESGO ALTO)

### 5.1 Descripción

Crear `sec_roles` con equivalentes de los roles legacy (Administrador, Supervisor, Usuario) y comenzar a migrar usuarios gradualmente.

### 5.2 Por qué NO es recomendado para FASE 5

- Alto riesgo de regresión
- Requiere mapeo complejo de permisos
- Viola la máxima de "no migrar usuarios"
- Demasiado alcance para una fase incremental

---

## 6. RECOMENDACIÓN

### 6.1 Opción recomendada: **OPCIÓN A - Rol Piloto Aislado**

| Criterio | Evaluación |
|----------|------------|
| Mínimo riesgo | ✅ Un solo rol piloto |
| Prueba herencia real | ✅ sec_rol → sec_roles.permisos |
| No migra usuarios | ✅ Campo opcional |
| No toca legacy | ✅ Colecciones separadas |
| Rollback trivial | ✅ 3 minutos |
| Base para FASE 6 | ✅ Expandible |

### 6.2 Justificación

1. **Prueba el concepto de herencia** - ¿Un rol puede otorgar permisos?
2. **Mantiene aislamiento** - Colección `sec_roles` separada de `roles`
3. **Un solo rol** - Mínima complejidad
4. **Reutiliza permiso existente** - `SISTEMA_ESTRUCTURA_VER` ya probado
5. **Auditoría desde el inicio** - Reutiliza `sec_bitacora_admin`

---

## 7. ALCANCE EXACTO RECOMENDADO (OPCIÓN A)

### 7.1 Colección sec_roles (a crear)

```javascript
// Documento inicial del rol piloto
{
  "id": "uuid",
  "codigo": "VISOR_ESTRUCTURA",
  "nombre": "Visor de Estructura Organizacional",
  "descripcion": "Rol piloto FASE 5 - permite ver tab Estructura",
  "permisos": ["SISTEMA_ESTRUCTURA_VER"],
  "activo": true,
  "es_sistema": true,
  "nivel_jerarquia": 10,
  "fase": "FASE_5",
  "created_at": "ISODate"
}
```

### 7.2 Actualización de verificar_permiso (FASE 3 → FASE 5)

```python
# ANTES (FASE 3/4)
async def verificar_permiso_estructura_v3(user: dict) -> bool:
    permisos_nuevos = user.get('sec_permisos', [])
    if 'SISTEMA_ESTRUCTURA_VER' in permisos_nuevos:
        return True
    if user.get('role') == 'SuperAdministrador':
        return True
    return False

# DESPUÉS (FASE 5) - Agregar capa de herencia
async def verificar_permiso_estructura_v5(user: dict) -> bool:
    # 1. Permisos directos (FASE 4)
    permisos_directos = user.get('sec_permisos', [])
    if 'SISTEMA_ESTRUCTURA_VER' in permisos_directos:
        return True
    
    # 2. Permisos por rol nuevo (FASE 5)
    sec_rol = user.get('sec_rol')
    if sec_rol and sec_rol in ROLES_FASE_5_WHITELIST:
        rol = await db.sec_roles.find_one({"codigo": sec_rol, "activo": True})
        if rol and 'SISTEMA_ESTRUCTURA_VER' in rol.get('permisos', []):
            return True
    
    # 3. Fallback legacy
    if user.get('role') == 'SuperAdministrador':
        return True
    
    return False
```

### 7.3 Endpoint de asignación de rol

```python
ROLES_FASE_5_WHITELIST = ["VISOR_ESTRUCTURA"]

class RolAsignacionRequest(BaseModel):
    usuario_email: str
    rol: str
    accion: str  # "ASIGNAR" o "RETIRAR"

@api_router.post("/admin/roles/asignar")
async def admin_asignar_rol(
    request: RolAsignacionRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    FASE 5: Asigna o retira un rol sec_* a un usuario.
    Solo SuperAdministrador puede ejecutar.
    Solo roles en whitelist FASE 5.
    """
    # Validaciones similares a FASE 4...
```

---

## 8. ARCHIVOS / ENDPOINTS / COLECCIONES

### 8.1 Archivo a modificar

| Archivo | Tipo de cambio | Líneas estimadas |
|---------|----------------|------------------|
| `/app/backend/server.py` | Colección, endpoint, helper actualizado | +120 líneas |

### 8.2 Endpoints

| Método | Endpoint | Propósito |
|--------|----------|-----------|
| POST | `/api/admin/roles/asignar` | Asignar/retirar rol |

### 8.3 Colecciones

| Colección | Operación |
|-----------|-----------|
| `sec_roles` | CREATE (nueva), READ |
| `users` | UPDATE (campo `sec_rol`) |
| `sec_bitacora_admin` | INSERT (auditoría) |

---

## 9. COMPATIBILIDAD LEGACY

### 9.1 Coexistencia de sistemas

```
LEGACY (NO TOCAR)                    NUEVO (FASE 5)
────────────────────────────         ────────────────────────────
users.role                           users.sec_rol (NUEVO)
users.rbac_role                      users.sec_permisos (FASE 4)
roles                                sec_roles (NUEVA)
rbac_roles                           sec_bitacora_admin (FASE 4)
```

### 9.2 Resolución de permisos (orden de precedencia)

```
1. Permisos directos (sec_permisos) → FASE 4
2. Permisos por rol nuevo (sec_rol → sec_roles) → FASE 5
3. Fallback legacy (SuperAdmin) → FASE 3
4. [FUTURO] Permisos por perfil → FASE 6+
```

### 9.3 Lo que NO se modifica

- ❌ `users.role` - Intacto
- ❌ `users.rbac_role` - Intacto
- ❌ Colección `roles` - Intacta
- ❌ Colección `rbac_roles` - Intacta
- ❌ `get_current_user()` - Intacto
- ❌ `Layout.js` - Intacto
- ❌ Login - Intacto

---

## 10. AUDITORÍA PROPUESTA

### 10.1 Reutilizar sec_bitacora_admin

Se reutiliza la colección creada en FASE 4 con nuevos tipos:

```json
{
  "tipo": "ASIGNAR_ROL" | "RETIRAR_ROL",
  "administrador": {...},
  "usuario_afectado": {...},
  "rol": "VISOR_ESTRUCTURA",
  "accion": "ASIGNAR" | "RETIRAR",
  "estado_anterior": null | "VISOR_ESTRUCTURA",
  "estado_nuevo": "VISOR_ESTRUCTURA" | null,
  "resultado": "OK" | "SIN_CAMBIO" | "RECHAZADO",
  "fase": "FASE_5"
}
```

---

## 11. RIESGOS Y MITIGACIONES

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|--------|--------------|---------|------------|
| 1 | Rol inexistente asignado | BAJA | BAJO | Validar contra sec_roles |
| 2 | Conflicto de nombres con legacy | MUY BAJA | BAJO | Nombres distintos |
| 3 | Usuario pierde acceso | BAJA | BAJO | Fallback a permisos directos |
| 4 | Complejidad de debugging | BAJA | BAJO | Logs claros en cada capa |
| 5 | Rendimiento por consulta extra | MUY BAJA | BAJO | Consulta simple por código |

---

## 12. QUÉ NO SE TOCARÁ

| Elemento | Confirmación |
|----------|--------------|
| `get_current_user()` | ❌ NO SE MODIFICA |
| `Layout.js` | ❌ NO SE MODIFICA |
| Router global | ❌ NO SE MODIFICA |
| Frontend (cualquier archivo) | ❌ NO SE MODIFICA |
| Colección `roles` | ❌ NO SE MODIFICA |
| Colección `rbac_roles` | ❌ NO SE MODIFICA |
| Campo `users.role` | ❌ NO SE MODIFICA |
| Campo `users.rbac_role` | ❌ NO SE MODIFICA |
| Endpoint `/api/admin/permisos/asignar` | ❌ NO SE MODIFICA |
| Módulos productivos | ❌ NO SE TOCAN |
| Dashboards | ❌ NO SE TOCAN |
| Login | ❌ NO SE TOCA |

---

## 13. ROLLBACK

### 13.1 Pasos de rollback

```
TIEMPO TOTAL: 3-4 minutos

Paso 1: Eliminar endpoint (1 minuto)
- Quitar bloque /api/admin/roles/asignar

Paso 2: Revertir helper (1 minuto)
- Volver a verificar_permiso_estructura_v3 (sin capa de rol)

Paso 3: Opcional - Limpiar datos
- db.sec_roles.drop()
- db.users.updateMany({}, {$unset: {sec_rol: 1}})

IMPACTO: CERO en funcionalidades existentes
Permisos directos (FASE 4) siguen funcionando
```

---

## 14. CHECKLIST DE NO REGRESIÓN

### 14.1 Pre-cambio

- [ ] Login funciona
- [ ] Tab Estructura visible para SuperAdmin
- [ ] Tab Estructura visible para usuario con sec_permisos
- [ ] GET /api/users funciona
- [ ] GET /api/roles funciona
- [ ] POST /api/admin/permisos/asignar funciona

### 14.2 Post-cambio

| Verificación | Resultado esperado |
|--------------|-------------------|
| Login | ✅ Funciona |
| SuperAdmin ve Estructura (fallback) | ✅ Sí |
| Usuario con sec_permisos directo | ✅ Ve Estructura |
| Usuario con sec_rol asignado | ✅ Ve Estructura (herencia) |
| Usuario sin nada | ✅ NO ve Estructura |
| POST /api/admin/roles/asignar (SuperAdmin) | ✅ 200 OK |
| POST /api/admin/roles/asignar (otro) | ✅ 403 |
| Rol fuera de whitelist | ✅ 400 |
| Auditoría registrada | ✅ Existe |
| GET /api/users | ✅ Funciona |
| GET /api/roles | ✅ Funciona |
| Dashboards | ✅ Sin cambios |

---

## 15. EVIDENCIA ESPERADA

Para dar por válida la FASE 5:

1. **Colección sec_roles creada** con rol piloto
2. **curl asignar rol** → HTTP 200, rol asignado
3. **curl retirar rol** → HTTP 200, rol removido
4. **Usuario con rol hereda permiso** → Puede ver tab Estructura
5. **Usuario sin rol ni permiso directo** → NO puede ver tab Estructura
6. **Auditoría en sec_bitacora_admin** con tipo ASIGNAR_ROL/RETIRAR_ROL
7. **No regresión** en login, users, roles, dashboards

---

## 16. SOLICITUD DE APROBACIÓN

### 16.1 Resumen de lo que se solicita aprobar

| # | Elemento | Descripción |
|---|----------|-------------|
| 1 | Crear colección `sec_roles` | Nueva, mínima |
| 2 | Crear rol piloto `VISOR_ESTRUCTURA` | Único rol en whitelist |
| 3 | Agregar campo `sec_rol` en users | Opcional, string |
| 4 | Crear endpoint `/api/admin/roles/asignar` | Solo SuperAdmin |
| 5 | Actualizar helper de verificación de permisos | Agregar capa de herencia |
| 6 | Auditoría en `sec_bitacora_admin` | Tipos ASIGNAR_ROL, RETIRAR_ROL |

### 16.2 Lo que NO se hará en FASE 5

| Elemento | Confirmación |
|----------|--------------|
| Múltiples roles por usuario | ❌ NO |
| Migrar usuarios | ❌ NO |
| Tocar colección `roles` | ❌ NO |
| Tocar colección `rbac_roles` | ❌ NO |
| Modificar `get_current_user()` | ❌ NO |
| Modificar UI | ❌ NO |
| Expandir whitelist | ❌ NO |

### 16.3 Decisión solicitada

**¿Aprueba la ejecución de FASE 5 OPCIÓN A bajo las condiciones descritas?**

- [ ] SÍ, proceder con OPCIÓN A (Rol piloto aislado)
- [ ] NO, requiere ajustes (especificar)
- [ ] PREFERIR OPCIÓN B (Múltiples roles)
- [ ] DIFERIR esta fase

---

**FIN DEL DOCUMENTO DE PROPUESTA FASE 5**

*Esperando aprobación explícita antes de implementar.*
