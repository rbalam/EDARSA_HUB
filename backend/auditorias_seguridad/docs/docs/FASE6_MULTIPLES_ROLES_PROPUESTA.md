# FASE 6 - PROPUESTA: MÚLTIPLES ROLES POR USUARIO
## Arquitectura de Seguridad EDARSA HUB

**Versión:** 1.0  
**Fecha:** Diciembre 2025  
**Estado:** PENDIENTE APROBACIÓN  
**Requisitos previos:** FASE 1 ✅ | FASE 2 ✅ | FASE 3 ✅ | FASE 4 ✅ | FASE 5 ✅

---

## 1. RESUMEN EJECUTIVO

Este documento propone 3 opciones para la FASE 6 del sistema RBAC, enfocada en permitir que un usuario tenga **múltiples roles** (`sec_roles` como array) en lugar de un único rol (`sec_rol` como string), unificando los permisos heredados de todos sus roles.

### Estado actual del sistema:

| Elemento | Estado FASE 5 |
|----------|---------------|
| `users.sec_permisos` | Array de permisos directos | ✅ |
| `users.sec_rol` | String - UN solo rol | ✅ |
| `sec_roles` | Colección con 1 rol piloto | ✅ |
| Resolución de permisos | 3 capas | ✅ |

### Objetivo FASE 6:

Permitir que un usuario herede permisos de **múltiples roles** simultáneamente, combinando sus permisos.

```
FASE 5 (actual):
users.sec_rol = "VISOR_ESTRUCTURA"  → hereda ["SISTEMA_ESTRUCTURA_VER"]

FASE 6 (propuesto):
users.sec_roles = ["VISOR_ESTRUCTURA", "VISOR_SISTEMA"]
→ hereda unión de permisos de ambos roles
```

---

## 2. DIAGNÓSTICO DEL PUNTO DE ENTRADA

### 2.1 Análisis de opciones

| Criterio | Peso | Mejor opción |
|----------|------|--------------|
| Mínimo cambio estructural | ALTO | Migrar sec_rol → sec_roles (array) |
| Compatibilidad FASE 5 | ALTO | Mantener soporte para sec_rol string |
| No tocar frontend | CRÍTICO | Solo backend |
| Probar con 1-2 roles | ALTO | Crear segundo rol piloto |
| Auditoría | ALTO | Reutilizar sec_bitacora_admin |

### 2.2 Arquitectura propuesta (4 capas)

```
┌─────────────────────────────────────────────────────────────────┐
│                    PERMISOS EFECTIVOS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. PERMISOS DIRECTOS (users.sec_permisos)                     │
│     └─ FASE 4: Ya implementado                                 │
│                                                                 │
│  2. PERMISOS POR ROLES (users.sec_roles → sec_roles)           │
│     └─ FASE 6: UNIÓN de permisos de múltiples roles            │
│                                                                 │
│  3. PERMISOS POR ROL ÚNICO (users.sec_rol) [LEGACY FASE 5]     │
│     └─ Mantener compatibilidad                                 │
│                                                                 │
│  4. FALLBACK LEGACY (users.role)                               │
│     └─ FASE 3: SuperAdmin tiene todo                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. OPCIÓN A: ARRAY DE ROLES (MENOR RIESGO)

### 3.1 Descripción

Agregar campo `sec_roles` (array) en usuarios, manteniendo compatibilidad con `sec_rol` (string) de FASE 5. La resolución busca primero en array, luego en string (fallback).

### 3.2 Alcance exacto

| Elemento | Valor |
|----------|-------|
| **Campo nuevo en users** | `sec_roles` (array, opcional) |
| **Compatibilidad** | Mantener `sec_rol` (string) como fallback |
| **Rol piloto adicional** | `VISOR_SISTEMA` |
| **Permisos del nuevo rol** | `["SISTEMA_USUARIOS_VER"]` |
| **Endpoint modificado** | `POST /api/admin/roles/asignar` (soporta múltiples) |
| **Whitelist** | `["VISOR_ESTRUCTURA", "VISOR_SISTEMA"]` |

### 3.3 Nuevo rol piloto

```json
{
  "codigo": "VISOR_SISTEMA",
  "nombre": "Visor del Sistema",
  "descripcion": "Rol piloto FASE 6 - puede ver usuarios del sistema",
  "permisos": ["SISTEMA_USUARIOS_VER"],
  "activo": true,
  "es_sistema": true,
  "fase": "FASE_6"
}
```

### 3.4 Resolución de permisos actualizada

```python
async def tiene_permiso_v6(user: dict, permiso: str) -> bool:
    """
    FASE 6: Resolución con múltiples roles.
    
    Orden:
    1. Permisos directos (sec_permisos)
    2. Permisos de múltiples roles (sec_roles array)
    3. Permiso de rol único (sec_rol string) [compatibilidad FASE 5]
    4. Fallback legacy (SuperAdmin)
    """
    # 1. Permisos directos
    if permiso in user.get('sec_permisos', []):
        return True
    
    # 2. Permisos de múltiples roles (FASE 6)
    sec_roles = user.get('sec_roles', [])
    for rol_codigo in sec_roles:
        if rol_codigo in ROLES_FASE_6_WHITELIST:
            rol_doc = await db.sec_roles.find_one({"codigo": rol_codigo, "activo": True})
            if rol_doc and permiso in rol_doc.get('permisos', []):
                return True
    
    # 3. Compatibilidad FASE 5 - rol único
    sec_rol = user.get('sec_rol')
    if sec_rol and sec_rol in ROLES_FASE_6_WHITELIST:
        rol_doc = await db.sec_roles.find_one({"codigo": sec_rol, "activo": True})
        if rol_doc and permiso in rol_doc.get('permisos', []):
            return True
    
    # 4. Fallback legacy
    if user.get('role') == 'SuperAdministrador':
        return True
    
    return False
```

### 3.5 Endpoint actualizado

```python
@api_router.post("/admin/roles/asignar")
async def admin_asignar_rol_v6(request, current_user):
    """
    FASE 6: Asigna o retira roles de un usuario.
    Soporta múltiples roles en array sec_roles.
    """
    # Validaciones...
    
    # Obtener roles actuales
    roles_actuales = usuario.get('sec_roles', [])
    
    if accion == "ASIGNAR":
        if request.rol not in roles_actuales:
            roles_actuales.append(request.rol)
    elif accion == "RETIRAR":
        if request.rol in roles_actuales:
            roles_actuales.remove(request.rol)
    
    # Actualizar usuario
    await db.users.update_one(
        {"email": request.usuario_email},
        {"$set": {"sec_roles": roles_actuales}}
    )
```

### 3.6 Archivos a modificar

| Archivo | Cambio | Líneas aprox. |
|---------|--------|---------------|
| `/app/backend/server.py` | Actualizar endpoint y helper | +80 líneas (modificación) |

### 3.7 Colecciones

| Colección | Operación |
|-----------|-----------|
| `sec_roles` | INSERT (nuevo rol piloto), READ |
| `users` | UPDATE (campo `sec_roles`) |
| `sec_bitacora_admin` | INSERT (auditoría) |

### 3.8 Whitelist FASE 6

```python
ROLES_FASE_6_WHITELIST = ["VISOR_ESTRUCTURA", "VISOR_SISTEMA"]
```

### 3.9 Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Conflicto sec_rol vs sec_roles | BAJA | BAJO | sec_roles tiene prioridad |
| Unión de permisos incorrecta | BAJA | BAJO | Tests exhaustivos |
| Complejidad de resolución | BAJA | BAJO | Orden claro de precedencia |

### 3.10 Compatibilidad con FASE 5

| Escenario | Comportamiento |
|-----------|---------------|
| Usuario con `sec_rol` (sin `sec_roles`) | Usa `sec_rol` (compatibilidad) |
| Usuario con `sec_roles` array | Usa `sec_roles` (FASE 6) |
| Usuario con ambos | `sec_roles` tiene prioridad |
| Usuario sin ninguno | Usa permisos directos o fallback |

### 3.11 Rollback

```
TIEMPO: 4 minutos
1. Revertir endpoint a versión FASE 5
2. Revertir helper a versión FASE 5
3. Opcional: db.users.updateMany({}, {$unset: {sec_roles: 1}})
4. sec_rol de FASE 5 sigue funcionando
```

---

## 4. OPCIÓN B: PERFILES PREDEFINIDOS (RIESGO MEDIO)

### 4.1 Descripción

Crear concepto de "Perfiles" - conjuntos predefinidos de roles que se asignan como unidad. Un usuario tiene un perfil que contiene múltiples roles.

### 4.2 Estructura

```json
// Colección sec_perfiles
{
  "codigo": "VISOR_OPERATIVO",
  "nombre": "Visor Operativo",
  "roles": ["VISOR_ESTRUCTURA", "VISOR_SISTEMA"],
  "descripcion": "Perfil de solo lectura para operadores"
}

// Usuario
{
  "sec_perfil": "VISOR_OPERATIVO"
}
```

### 4.3 Por qué NO es recomendado para FASE 6

- Agrega una capa de abstracción adicional
- Mayor complejidad sin beneficio inmediato
- Mejor dejarlo para FASE 7+ una vez que múltiples roles funcione

---

## 5. OPCIÓN C: MIGRACIÓN COMPLETA A ARRAY (RIESGO MEDIO-ALTO)

### 5.1 Descripción

Eliminar `sec_rol` (string) y migrar todos los usuarios a `sec_roles` (array).

### 5.2 Por qué NO es recomendado para FASE 6

- Requiere migración de datos
- Rompe compatibilidad con FASE 5
- Viola máxima de "no migrar masivamente"

---

## 6. RECOMENDACIÓN

### 6.1 Opción recomendada: **OPCIÓN A - Array de Roles**

| Criterio | Evaluación |
|----------|------------|
| Mínimo riesgo | ✅ Mantiene compatibilidad FASE 5 |
| Prueba múltiples roles | ✅ 2 roles piloto |
| No migra usuarios | ✅ Campo nuevo opcional |
| No toca frontend | ✅ Solo backend |
| Rollback trivial | ✅ 4 minutos |
| Base para FASE 7 | ✅ Expandible a perfiles |

### 6.2 Justificación

1. **Compatibilidad total** - `sec_rol` de FASE 5 sigue funcionando
2. **Dos roles piloto** - Permite probar unión de permisos
3. **Sin migración** - Campo `sec_roles` es opcional
4. **Incremento mínimo** - Solo cambia endpoint y helper

---

## 7. ALCANCE EXACTO RECOMENDADO (OPCIÓN A)

### 7.1 Nuevo rol piloto

```javascript
db.sec_roles.insertOne({
  id: UUID().toString(),
  codigo: "VISOR_SISTEMA",
  nombre: "Visor del Sistema",
  descripcion: "Rol piloto FASE 6 - puede ver usuarios del sistema",
  permisos: ["SISTEMA_USUARIOS_VER"],
  activo: true,
  es_sistema: true,
  nivel_jerarquia: 15,
  fase: "FASE_6",
  created_at: new Date().toISOString()
})
```

### 7.2 Helper actualizado

```python
async def verificar_permiso_estructura_v6(user: dict) -> bool:
    """
    FASE 6: Verifica permiso con múltiples roles.
    """
    permiso = 'SISTEMA_ESTRUCTURA_VER'
    
    # 1. Permisos directos
    if permiso in user.get('sec_permisos', []):
        return True
    
    # 2. Múltiples roles (FASE 6)
    for rol_codigo in user.get('sec_roles', []):
        if rol_codigo in ROLES_FASE_6_WHITELIST:
            rol_doc = await db.sec_roles.find_one({"codigo": rol_codigo, "activo": True})
            if rol_doc and permiso in rol_doc.get('permisos', []):
                return True
    
    # 3. Rol único (compatibilidad FASE 5)
    sec_rol = user.get('sec_rol')
    if sec_rol and sec_rol in ROLES_FASE_6_WHITELIST:
        rol_doc = await db.sec_roles.find_one({"codigo": sec_rol, "activo": True})
        if rol_doc and permiso in rol_doc.get('permisos', []):
            return True
    
    # 4. Fallback
    if user.get('role') == 'SuperAdministrador':
        return True
    
    return False
```

### 7.3 Endpoint actualizado

El endpoint `POST /api/admin/roles/asignar` se actualiza para:
- Trabajar con `sec_roles` (array) en lugar de `sec_rol` (string)
- Permitir agregar múltiples roles a un usuario
- Mantener auditoría detallada

---

## 8. ARCHIVOS / ENDPOINTS / COLECCIONES

### 8.1 Archivo a modificar

| Archivo | Tipo de cambio | Líneas estimadas |
|---------|----------------|------------------|
| `/app/backend/server.py` | Actualizar endpoint y helper | +60 líneas (modificación) |

### 8.2 Endpoints

| Método | Endpoint | Cambio |
|--------|----------|--------|
| POST | `/api/admin/roles/asignar` | Soporta sec_roles (array) |

### 8.3 Colecciones

| Colección | Operación |
|-----------|-----------|
| `sec_roles` | INSERT (nuevo rol), READ |
| `users` | UPDATE (campo `sec_roles`) |
| `sec_bitacora_admin` | INSERT (auditoría) |

---

## 9. COMPATIBILIDAD LEGACY

### 9.1 Coexistencia de campos

```
LEGACY (NO TOCAR)                    FASE 5 (MANTENER)        FASE 6 (NUEVO)
────────────────────────────         ──────────────────       ─────────────────
users.role                           users.sec_rol            users.sec_roles
users.rbac_role                      
roles                                sec_roles                
rbac_roles                           
```

### 9.2 Orden de resolución final

```
1. Permisos directos (sec_permisos) → FASE 4
2. Múltiples roles (sec_roles array) → FASE 6
3. Rol único (sec_rol string) → FASE 5
4. Fallback legacy (SuperAdmin) → FASE 3
```

---

## 10. AUDITORÍA PROPUESTA

### 10.1 Nuevos tipos de auditoría

```json
{
  "tipo": "ASIGNAR_ROL_MULTIPLE",
  "rol": "VISOR_SISTEMA",
  "roles_anteriores": [],
  "roles_nuevos": ["VISOR_ESTRUCTURA", "VISOR_SISTEMA"],
  "fase": "FASE_6"
}
```

---

## 11. RIESGOS Y MITIGACIONES

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|--------|--------------|---------|------------|
| 1 | Conflicto sec_rol vs sec_roles | BAJA | BAJO | sec_roles tiene prioridad |
| 2 | Unión incorrecta de permisos | BAJA | BAJO | Tests de unión |
| 3 | Complejidad de debugging | BAJA | BAJO | Logs claros |
| 4 | FASE 5 rompe | MUY BAJA | BAJO | Compatibilidad explícita |

---

## 12. QUÉ NO SE TOCARÁ

| Elemento | Confirmación |
|----------|--------------|
| `get_current_user()` | ❌ NO SE MODIFICA |
| `Layout.js` | ❌ NO SE MODIFICA |
| Frontend (cualquier archivo) | ❌ NO SE MODIFICA |
| Colección `roles` | ❌ NO SE MODIFICA |
| Colección `rbac_roles` | ❌ NO SE MODIFICA |
| Campo `users.role` | ❌ NO SE MODIFICA |
| Campo `users.rbac_role` | ❌ NO SE MODIFICA |
| Campo `users.sec_rol` | ❌ NO SE ELIMINA (compatibilidad) |
| Campo `users.sec_permisos` | ❌ NO SE MODIFICA |
| Endpoint `/api/admin/permisos/asignar` | ❌ NO SE MODIFICA |

---

## 13. ROLLBACK

### 13.1 Pasos de rollback

```
TIEMPO TOTAL: 4 minutos

1. Revertir endpoint a versión FASE 5
2. Revertir helper a versión FASE 5
3. Opcional: db.sec_roles.deleteOne({codigo: "VISOR_SISTEMA"})
4. Opcional: db.users.updateMany({}, {$unset: {sec_roles: 1}})

IMPACTO: 
- sec_rol de FASE 5 sigue funcionando
- sec_permisos de FASE 4 sigue funcionando
```

---

## 14. CHECKLIST DE NO REGRESIÓN

### 14.1 Pre-cambio

- [ ] FASE 4 funciona (permisos directos)
- [ ] FASE 5 funciona (rol único)
- [ ] Login funciona
- [ ] Tab Estructura visible para SuperAdmin

### 14.2 Post-cambio

| Verificación | Resultado esperado |
|--------------|-------------------|
| Usuario con sec_permisos directo | ✅ Funciona (FASE 4) |
| Usuario con sec_rol único | ✅ Funciona (FASE 5) |
| Usuario con sec_roles array | ✅ Funciona (FASE 6) |
| Usuario con ambos sec_rol y sec_roles | ✅ sec_roles tiene prioridad |
| Unión de permisos de múltiples roles | ✅ Funciona |
| POST /api/admin/permisos/asignar | ✅ Sin cambios |
| GET /api/users | ✅ Funciona |
| GET /api/roles | ✅ Funciona |
| Login | ✅ Funciona |
| Dashboards | ✅ Sin cambios |

---

## 15. EVIDENCIA ESPERADA

1. **Crear segundo rol piloto** `VISOR_SISTEMA`
2. **Asignar múltiples roles** a un usuario
3. **Verificar unión de permisos** - usuario hereda de ambos roles
4. **Verificar compatibilidad FASE 5** - sec_rol sigue funcionando
5. **Verificar compatibilidad FASE 4** - sec_permisos sigue funcionando
6. **Auditoría registrada** con roles_anteriores/roles_nuevos

---

## 16. SOLICITUD DE APROBACIÓN

### 16.1 Resumen de lo que se solicita aprobar

| # | Elemento | Descripción |
|---|----------|-------------|
| 1 | Crear rol piloto `VISOR_SISTEMA` | Con permiso `SISTEMA_USUARIOS_VER` |
| 2 | Agregar campo `sec_roles` (array) | En usuarios |
| 3 | Actualizar endpoint roles | Soportar múltiples roles |
| 4 | Actualizar helper de verificación | 4 capas de resolución |
| 5 | Ampliar whitelist | `["VISOR_ESTRUCTURA", "VISOR_SISTEMA"]` |
| 6 | Auditoría roles múltiples | Registrar array antes/después |

### 16.2 Lo que NO se hará en FASE 6

| Elemento | Confirmación |
|----------|--------------|
| Perfiles | ❌ NO |
| Migrar sec_rol → sec_roles | ❌ NO |
| Eliminar sec_rol | ❌ NO |
| Tocar frontend | ❌ NO |
| Tocar roles legacy | ❌ NO |
| UI de administración | ❌ NO |

### 16.3 Decisión solicitada

**¿Aprueba la ejecución de FASE 6 OPCIÓN A bajo las condiciones descritas?**

- [ ] SÍ, proceder con OPCIÓN A (Array de Roles)
- [ ] NO, requiere ajustes (especificar)
- [ ] PREFERIR OPCIÓN B (Perfiles)
- [ ] DIFERIR esta fase

---

**FIN DEL DOCUMENTO DE PROPUESTA FASE 6**

*Esperando aprobación explícita antes de implementar.*
