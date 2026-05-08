# FASE 13 - PROPUESTA: PERFILES PREDEFINIDOS RBAC
## Arquitectura de Seguridad EDARSA HUB

**Versión:** 1.0  
**Fecha:** Diciembre 2025  
**Estado:** PENDIENTE APROBACIÓN  
**Requisitos previos:** FASE 1-12 ✅

---

## 1. RESUMEN EJECUTIVO

Esta propuesta define la implementación de **perfiles predefinidos RBAC** que permitan asignar conjuntos de roles de forma estandarizada a usuarios, simplificando la gestión de permisos.

### Concepto de "Perfil"

Un **perfil** es una plantilla que agrupa uno o más roles RBAC existentes. Al asignar un perfil a un usuario, este hereda automáticamente todos los roles (y por ende permisos) del perfil.

```
Perfil → contiene → [Rol1, Rol2, ...]
Usuario ← se le asigna ← Perfil
Usuario ← hereda ← [Rol1, Rol2, ...] → [Permiso1, Permiso2, ...]
```

### Fuera de alcance:
- Rollout masivo a módulos operativos
- Cambios en auth global o middleware
- Sustitución de roles legacy
- Dashboard de perfiles

---

## 2. DIAGNÓSTICO ACTUAL

### 2.1 Roles RBAC Existentes (sec_roles)

| Rol | Permisos | Fase |
|-----|----------|------|
| VISOR_ESTRUCTURA | 1 | FASE_5 |
| VISOR_SISTEMA | 1 | FASE_6 |
| VISOR_ADMIN | 3 | FASE_8 |
| ADMIN_USUARIOS | 3 | FASE_10 |
| GESTOR_SISTEMA | 8 | FASE_11 |

**Total:** 5 roles, hasta 8 permisos únicos del módulo Sistema

### 2.2 Usuarios con RBAC

| Métrica | Valor |
|---------|-------|
| Usuarios con sec_roles asignados | 0 |
| Usuarios con sec_permisos directos | ~1 (test@edarsa.com) |
| Total usuarios activos | ~30 |

### 2.3 Roles Legacy en Uso

| Rol Legacy | Usuarios |
|------------|----------|
| SuperAdministrador | 1 |
| Administrador | 3 |
| Supervisor | 8 |
| Usuario | 16 |
| Admin/admin | 2 |

---

## 3. PROPÓSITO DE LOS PERFILES

### 3.1 Problema Actual

Actualmente, para dar acceso RBAC a un usuario:
1. Se asignan permisos directos uno por uno (`sec_permisos`)
2. O se asignan roles uno por uno (`sec_roles`)

Esto es tedioso y propenso a inconsistencias cuando se quiere replicar el mismo conjunto de accesos para múltiples usuarios.

### 3.2 Solución Propuesta

Crear **perfiles predefinidos** que agrupen roles coherentes:

| Perfil | Roles Incluidos | Caso de Uso |
|--------|-----------------|-------------|
| `PERFIL_VISOR_BASICO` | VISOR_ESTRUCTURA | Ver solo estructura organizacional |
| `PERFIL_VISOR_SISTEMA` | VISOR_ESTRUCTURA, VISOR_SISTEMA | Ver estructura + lista usuarios |
| `PERFIL_VISOR_COMPLETO` | VISOR_ADMIN | Ver todo el módulo Sistema (lectura) |
| `PERFIL_ADMIN_USUARIOS` | VISOR_ADMIN, ADMIN_USUARIOS | Gestionar usuarios (sin crear roles) |
| `PERFIL_GESTOR_SISTEMA` | GESTOR_SISTEMA | Gestión completa del módulo Sistema |

### 3.3 Beneficios

1. **Estandarización**: Mismos permisos para usuarios del mismo perfil
2. **Simplicidad**: Una asignación en lugar de múltiples
3. **Mantenibilidad**: Cambiar el perfil actualiza a todos los usuarios con ese perfil
4. **Auditoría**: Saber qué perfil tiene cada usuario

---

## 4. OPCIONES DE IMPLEMENTACIÓN

### 4.1 OPCIÓN A: PERFILES COMO METADATO (Menor riesgo)

**Descripción:** Los perfiles son un campo informativo en el usuario que referencia qué roles tiene. La asignación de perfil expande automáticamente los roles.

| Elemento | Cambio |
|----------|--------|
| Backend | +1 endpoint asignar perfil, +1 endpoint listar perfiles |
| Frontend | +1 selector de perfil en UI de usuario |
| MongoDB | +colección `sec_perfiles`, +campo `sec_perfil` en users |
| Riesgo | MÍNIMO |
| Rollback | 5 minutos |

**Flujo:**
```
POST /api/admin/perfiles/asignar
{
  "usuario_email": "...",
  "perfil": "PERFIL_VISOR_COMPLETO"
}

→ Backend expande perfil a roles
→ Actualiza users.sec_roles = [VISOR_ADMIN]
→ Actualiza users.sec_perfil = "PERFIL_VISOR_COMPLETO"
```

### 4.2 OPCIÓN B: PERFILES COMO CAPA ADICIONAL (Riesgo bajo)

**Descripción:** Los perfiles son una capa adicional de resolución. El usuario tiene `sec_perfil` y el sistema resuelve permisos: permisos directos → roles directos → perfil → roles del perfil.

| Elemento | Cambio |
|----------|--------|
| Backend | Modificar `rbac_helper.py` para resolver perfiles |
| Frontend | +1 selector de perfil |
| MongoDB | +colección `sec_perfiles`, +campo `sec_perfil` en users |
| Riesgo | BAJO |
| Rollback | 7 minutos |

### 4.3 OPCIÓN C: PERFILES SOLO EN CATÁLOGO (Riesgo mínimo)

**Descripción:** Solo crear el catálogo de perfiles sin modificar la asignación. La UI muestra los perfiles disponibles y permite copiar los roles a un usuario manualmente.

| Elemento | Cambio |
|----------|--------|
| Backend | +1 endpoint listar perfiles (solo lectura) |
| Frontend | +1 card informativo de perfiles |
| MongoDB | +colección `sec_perfiles` |
| Riesgo | MÍNIMO |
| Rollback | 3 minutos |

---

## 5. RECOMENDACIÓN

### Opción recomendada: **OPCIÓN A - PERFILES COMO METADATO**

| Criterio | Evaluación |
|----------|------------|
| Simplicidad | ✅ Asignar perfil = asignar roles automáticamente |
| Mínimo impacto | ✅ No modifica resolución de permisos existente |
| Reversibilidad | ✅ El campo sec_perfil es solo informativo |
| Compatibilidad | ✅ sec_roles sigue siendo la fuente de verdad |
| Auditoría | ✅ Se sabe qué perfil tiene cada usuario |

### Justificación

1. **No modifica `rbac_helper.py`**: La resolución de permisos sigue igual (sec_permisos → sec_roles → sec_rol → legacy)
2. **sec_roles sigue siendo la fuente de verdad**: El perfil solo es un atajo para asignar roles
3. **Trazabilidad**: Se puede saber qué perfil se asignó originalmente
4. **Escalable**: Si se modifica el perfil, se puede re-sincronizar usuarios

---

## 6. ALCANCE EXACTO (OPCIÓN A)

### 6.1 Colección Nueva: `sec_perfiles`

```json
{
  "codigo": "PERFIL_VISOR_COMPLETO",
  "nombre": "Visor Completo del Sistema",
  "descripcion": "Acceso de solo lectura a todo el módulo Sistema",
  "roles": ["VISOR_ADMIN"],
  "activo": true,
  "fase": "FASE_13",
  "created_at": "..."
}
```

### 6.2 Campo Nuevo en `users`

```json
{
  "sec_perfil": "PERFIL_VISOR_COMPLETO",  // Nuevo campo (opcional)
  "sec_roles": ["VISOR_ADMIN"],            // Ya existe
  "sec_permisos": [...]                    // Ya existe
}
```

### 6.3 Endpoints Nuevos

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/admin/perfiles` | GET | Lista perfiles disponibles |
| `/api/admin/perfiles/asignar` | POST | Asigna perfil a usuario |
| `/api/admin/perfiles/retirar` | POST | Retira perfil de usuario |

### 6.4 Perfiles Predefinidos a Crear

| Código | Nombre | Roles |
|--------|--------|-------|
| `PERFIL_VISOR_BASICO` | Visor Básico | VISOR_ESTRUCTURA |
| `PERFIL_VISOR_SISTEMA` | Visor Sistema | VISOR_ESTRUCTURA, VISOR_SISTEMA |
| `PERFIL_VISOR_COMPLETO` | Visor Completo | VISOR_ADMIN |
| `PERFIL_ADMIN_USUARIOS` | Admin Usuarios | VISOR_ADMIN, ADMIN_USUARIOS |
| `PERFIL_GESTOR_SISTEMA` | Gestor Sistema | GESTOR_SISTEMA |

---

## 7. ARCHIVOS A TOCAR

| Archivo | Cambio | Líneas estimadas |
|---------|--------|------------------|
| `/app/backend/server.py` | +3 endpoints (GET, POST asignar, POST retirar) | +80 |
| `/app/frontend/src/pages/Usuarios.js` | +selector de perfil en UI tarjeta usuario | +40 |
| MongoDB | +colección `sec_perfiles`, +campo `sec_perfil` en users | N/A |

**Total:** 2 archivos, ~120 líneas nuevas

---

## 8. FLUJO DE ASIGNACIÓN

```
1. SuperAdmin selecciona usuario en /usuarios
2. En sección RBAC, ve nuevo selector "Perfil"
3. Selecciona "PERFIL_ADMIN_USUARIOS"
4. Backend:
   a) Obtiene roles del perfil: [VISOR_ADMIN, ADMIN_USUARIOS]
   b) Actualiza users.sec_roles = [VISOR_ADMIN, ADMIN_USUARIOS]
   c) Actualiza users.sec_perfil = "PERFIL_ADMIN_USUARIOS"
   d) Registra en sec_bitacora_admin
5. Usuario ahora tiene los permisos heredados de ambos roles
```

---

## 9. QUÉ NO SE TOCARÁ

| Elemento | Confirmación |
|----------|--------------|
| `rbac_helper.py` | ❌ NO SE MODIFICA (resolución de permisos igual) |
| `get_current_user()` | ❌ NO SE MODIFICA |
| `Layout.js` | ❌ NO SE MODIFICA |
| Router global | ❌ NO SE MODIFICA |
| Middleware global | ❌ NO SE MODIFICA |
| Auth global | ❌ NO SE MODIFICA |
| Endpoints FASE 1-12 | ❌ NO SE MODIFICAN |
| Resolución de permisos | ❌ NO SE MODIFICA (sec_roles sigue siendo fuente de verdad) |

---

## 10. RIESGOS Y MITIGACIONES

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|--------|--------------|---------|------------|
| 1 | Confusión perfil vs roles directos | BAJA | BAJO | Documentar que perfil es atajo, roles es fuente de verdad |
| 2 | Desincronización perfil-roles | BAJA | BAJO | Al asignar perfil, se sobrescriben roles |
| 3 | Regresión en /usuarios | BAJA | MEDIO | Cambio mínimo en UI (solo selector) |

---

## 11. COMPATIBILIDAD

| Elemento | Compatibilidad |
|----------|---------------|
| `sec_roles` | ✅ Sigue siendo la fuente de verdad |
| `sec_permisos` | ✅ Sin cambios |
| Resolución de permisos | ✅ Sin cambios en rbac_helper.py |
| Roles legacy | ✅ Sin cambios |
| FASE 1-12 | ✅ Sin cambios |

---

## 12. ROLLBACK

### Procedimiento

```bash
# 1. Eliminar endpoints de perfiles en server.py
# 2. Eliminar selector de perfil en Usuarios.js
# 3. Limpiar campo sec_perfil de usuarios (opcional)
# 4. Eliminar colección sec_perfiles (opcional)
```

### Tiempo Estimado

**5 minutos**

---

## 13. CHECKLIST DE NO REGRESIÓN

| # | Verificación | Resultado esperado |
|---|--------------|-------------------|
| 1 | Login funciona | ✅ |
| 2 | Tabs usuarios/roles/estructura/bitácora | ✅ |
| 3 | Asignación de permisos directos (FASE 4) | ✅ |
| 4 | Asignación de roles directos (FASE 6) | ✅ |
| 5 | CRUD usuarios (FASE 9-11) | ✅ |
| 6 | CRUD roles (FASE 9-11) | ✅ |
| 7 | Bitácora RBAC (FASE 12) | ✅ |
| 8 | Nueva asignación de perfil funciona | ✅ |
| 9 | Perfil expande roles correctamente | ✅ |
| 10 | Auditoría de asignación de perfil | ✅ |

---

## 14. VALIDACIÓN POST-EJECUCIÓN

Al terminar, documentar con evidencia verificable:

1. Lista de perfiles disponibles en GET /api/admin/perfiles
2. Asignación de perfil actualiza sec_roles correctamente
3. Asignación de perfil registra en sec_bitacora_admin
4. Retiro de perfil limpia sec_roles y sec_perfil
5. UI muestra selector de perfil funcional
6. FASE 1-12 sigue funcionando
7. Resolución de permisos sigue igual (no se tocó rbac_helper)
8. Layout.js no modificado
9. get_current_user() no modificado

---

## 15. SOLICITUD DE APROBACIÓN

### 15.1 Resumen de la propuesta

| # | Elemento |
|---|----------|
| 1 | Crear colección `sec_perfiles` con 5 perfiles predefinidos |
| 2 | Crear endpoint `GET /api/admin/perfiles` |
| 3 | Crear endpoint `POST /api/admin/perfiles/asignar` |
| 4 | Crear endpoint `POST /api/admin/perfiles/retirar` |
| 5 | Agregar selector de perfil en UI de usuario |
| 6 | Agregar campo `sec_perfil` en users (informativo) |

### 15.2 Perfiles a crear

1. PERFIL_VISOR_BASICO → [VISOR_ESTRUCTURA]
2. PERFIL_VISOR_SISTEMA → [VISOR_ESTRUCTURA, VISOR_SISTEMA]
3. PERFIL_VISOR_COMPLETO → [VISOR_ADMIN]
4. PERFIL_ADMIN_USUARIOS → [VISOR_ADMIN, ADMIN_USUARIOS]
5. PERFIL_GESTOR_SISTEMA → [GESTOR_SISTEMA]

### 15.3 Decisión solicitada

**¿Aprueba FASE 13 con OPCIÓN A (Perfiles como Metadato)?**

- [ ] SÍ, proceder con OPCIÓN A
- [ ] NO, requiere ajustes
- [ ] PREFERIR OPCIÓN B (Perfiles como capa adicional)
- [ ] PREFERIR OPCIÓN C (Solo catálogo)
- [ ] DIFERIR

---

**FIN DEL DOCUMENTO DE PROPUESTA FASE 13**
