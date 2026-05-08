# FASE 14 - PROPUESTA: ALCANCE ORGANIZACIONAL RBAC
## Arquitectura de Seguridad EDARSA HUB

**Versión:** 1.0  
**Fecha:** Diciembre 2025  
**Estado:** PENDIENTE APROBACIÓN  
**Requisitos previos:** FASE 1-13 ✅

---

## 1. RESUMEN EJECUTIVO

Esta propuesta define la implementación de **alcance organizacional real** en el sistema RBAC, permitiendo que los permisos y roles se limiten por:
- Empresa
- Unidad de Negocio
- Sucursal
- Almacén (opcional)

### Objetivo

Actualmente los permisos RBAC son **globales** (aplican a todo el sistema). Esta fase introduce **alcance acotado** para que un usuario con permiso `SISTEMA_USUARIOS_VER` solo pueda ver usuarios de su(s) sucursal(es) asignada(s).

### Fuera de alcance:
- Rollout a módulos operativos (Comercial, Compras, etc.)
- Migración masiva de usuarios
- Sustitución del sistema legacy de `allowed_servers`
- Dashboard de alcance

---

## 2. DIAGNÓSTICO ACTUAL

### 2.1 Estructura Organizacional Existente

| Colección | Registros | Descripción |
|-----------|-----------|-------------|
| `sec_empresas` | 1 | EDARSA |
| `sec_unidades_negocio` | 7 | ManagementPro, Cienfuegos, La Estelar, etc. |
| `sec_sucursales` | 7 | Una por unidad de negocio |
| `servers` | 10 | Servidores SQL externos |

**Jerarquía identificada:**
```
EDARSA (empresa)
├── ManagementPro (unidad)
│   └── SUC_MANAGMENTPRO (sucursal)
├── Cienfuegos (unidad)
│   └── SUC_CIENFUEGOS (sucursal)
├── La Estelar (unidad)
│   └── SUC_LA_ESTELAR (sucursal)
└── ...
```

### 2.2 Sistema Legacy de Alcance (en users)

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| `allowed_servers` | Lista de IDs de servidores SQL | `['1b230a06...', '6d053c22...']` |
| `allowed_sucursales` | Dict server_id → [sucursal_ids] | `{'1b230a06...': ['0023', '0021']}` |
| `allowed_warehouses` | Dict server_id → [warehouse_codes] | `{'1b230a06...': ['0002', '0003']}` |

**Usuarios con alcance legacy:** 7 de ~30

### 2.3 Estructura RBAC Existente (rbac_usuarios_roles)

La colección `rbac_usuarios_roles` ya tiene campos para alcance:
```json
{
  "id": "...",
  "user_id": "f648dd3f...",
  "rol_id": "757bddd6...",
  "empresa_id": "31784356...",     // ← YA EXISTE
  "sucursales_ids": [],            // ← YA EXISTE
  "activo": true,
  "created_at": "...",
  "created_by": "..."
}
```

**Registros existentes:** ~5 (pruebas anteriores)

### 2.4 Sistema RBAC Actual (FASE 1-13)

| Campo en users | Uso |
|----------------|-----|
| `sec_permisos` | Permisos directos globales |
| `sec_rol` | Rol único global (compatibilidad) |
| `sec_roles` | Múltiples roles globales |
| `sec_perfil` | Perfil predefinido (metadato) |

**Alcance actual:** GLOBAL (sin restricción organizacional)

---

## 3. PROBLEMA A RESOLVER

### 3.1 Situación Actual

Un usuario con `SISTEMA_USUARIOS_VER`:
- ✅ Puede ver la lista de usuarios
- ❌ Ve TODOS los usuarios del sistema
- ❌ No hay restricción por sucursal/unidad/empresa

### 3.2 Situación Deseada

Un usuario con `SISTEMA_USUARIOS_VER` + alcance `SUC_CIENFUEGOS`:
- ✅ Puede ver la lista de usuarios
- ✅ Solo ve usuarios de la sucursal Cienfuegos
- ✅ Respeta jerarquía organizacional

---

## 4. OPCIONES DE IMPLEMENTACIÓN

### 4.1 OPCIÓN A: ALCANCE EN sec_roles EXISTENTE (Menor riesgo)

**Descripción:** Agregar campos de alcance a los roles ya asignados en `sec_roles`. Modificar la asignación de roles para incluir alcance.

**Nuevo modelo en users:**
```json
{
  "sec_roles": ["VISOR_ADMIN"],
  "sec_roles_alcance": {
    "VISOR_ADMIN": {
      "empresa_id": "62786c07...",
      "unidades_ids": ["c9d9696e...", "1a1768a7..."],
      "sucursales_ids": ["SUC_MANAGMENTPRO", "SUC_CIENFUEGOS"]
    }
  }
}
```

| Pros | Contras |
|------|---------|
| Mínimo impacto | Duplica estructura de alcance |
| Compatible con sec_roles | Complejiza asignación |
| No toca rbac_helper.py (resolución) | Requiere nuevo endpoint |

**Riesgo:** BAJO

### 4.2 OPCIÓN B: USAR rbac_usuarios_roles EXISTENTE (Riesgo medio)

**Descripción:** Activar y usar la colección `rbac_usuarios_roles` que ya tiene campos de alcance (`empresa_id`, `sucursales_ids`).

**Modelo existente:**
```json
{
  "user_id": "...",
  "rol_id": "...",
  "empresa_id": "...",
  "sucursales_ids": [],
  "activo": true
}
```

| Pros | Contras |
|------|---------|
| Infraestructura ya existe | Requiere modificar resolución |
| Modelo normalizado | Toca rbac_helper.py |
| Flexible para futuro | Mayor complejidad |

**Riesgo:** MEDIO (requiere modificar rbac_helper.py)

### 4.3 OPCIÓN C: ALCANCE SOLO EN PERFIL (Riesgo mínimo)

**Descripción:** Agregar alcance solo al perfil predefinido. El perfil define tanto roles como alcance.

**Nuevo modelo:**
```json
{
  "sec_perfil": "PERFIL_ADMIN_USUARIOS",
  "sec_perfil_alcance": {
    "empresa_id": "62786c07...",
    "sucursales_ids": ["SUC_CIENFUEGOS"]
  }
}
```

| Pros | Contras |
|------|---------|
| Muy simple | Limita flexibilidad |
| No toca resolución | Solo funciona con perfiles |
| Fácil rollback | No soporta alcance por rol individual |

**Riesgo:** MÍNIMO

---

## 5. RECOMENDACIÓN

### Opción recomendada: **OPCIÓN A - ALCANCE EN sec_roles EXISTENTE**

| Criterio | Evaluación |
|----------|------------|
| Mínimo impacto | ✅ No modifica rbac_helper.py |
| Compatibilidad | ✅ Mantiene sec_roles como fuente de verdad |
| Flexibilidad | ✅ Alcance por rol individual |
| Rollback | ✅ Fácil de revertir |
| No rompe FASE 1-13 | ✅ Extensión, no reemplazo |

### Justificación

1. **NO modifica rbac_helper.py** en esta fase - la resolución de acceso a endpoint sigue igual
2. El alcance se aplicará **en la lógica de negocio** de cada endpoint (filtrar datos por alcance)
3. Mantiene compatibilidad con todo lo construido en FASE 1-13
4. Es una **extensión** del modelo existente, no un reemplazo

---

## 6. ALCANCE EXACTO (OPCIÓN A)

### 6.1 Campo Nuevo en users

```json
{
  "sec_roles": ["VISOR_ADMIN", "ADMIN_USUARIOS"],
  "sec_roles_alcance": {
    "VISOR_ADMIN": {
      "tipo": "SUCURSAL",  // EMPRESA | UNIDAD | SUCURSAL | ALMACEN
      "empresa_id": "62786c07-4475-4b06-860d-7af6e56bd867",
      "unidades_ids": [],
      "sucursales_ids": ["SUC_CIENFUEGOS"],
      "almacenes_ids": []
    },
    "ADMIN_USUARIOS": {
      "tipo": "GLOBAL",  // Sin restricción
      "empresa_id": null,
      "unidades_ids": [],
      "sucursales_ids": [],
      "almacenes_ids": []
    }
  }
}
```

### 6.2 Tipos de Alcance

| Tipo | Descripción | Jerarquía |
|------|-------------|-----------|
| `GLOBAL` | Sin restricción | Todo el sistema |
| `EMPRESA` | Limitado a empresa | Ve todo dentro de la empresa |
| `UNIDAD` | Limitado a unidad(es) de negocio | Ve sucursales de esas unidades |
| `SUCURSAL` | Limitado a sucursal(es) | Ve solo esas sucursales |
| `ALMACEN` | Limitado a almacén(es) específico(s) | Más granular |

### 6.3 Endpoints Nuevos

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/admin/alcance/empresas` | GET | Lista empresas disponibles |
| `/api/admin/alcance/unidades` | GET | Lista unidades de una empresa |
| `/api/admin/alcance/sucursales` | GET | Lista sucursales de una unidad |
| `/api/admin/alcance/asignar` | POST | Asigna alcance a un rol de usuario |

### 6.4 Flujo de Asignación

```
1. SuperAdmin selecciona usuario
2. Usuario tiene sec_roles = ["VISOR_ADMIN"]
3. Para VISOR_ADMIN, asigna alcance:
   - Tipo: SUCURSAL
   - Sucursales: ["SUC_CIENFUEGOS", "SUC_LA_ESTELAR"]
4. Backend actualiza sec_roles_alcance
5. Auditoría registra el cambio
```

### 6.5 Aplicación del Alcance (Futuro)

**IMPORTANTE:** En esta fase solo se implementa la **asignación** de alcance. La **aplicación** real del alcance (filtrar datos en endpoints) se hará en fases posteriores cuando se proteja cada módulo operativo.

```python
# Ejemplo futuro (NO en esta fase):
async def get_usuarios_con_alcance(current_user):
    alcance = current_user.get('sec_roles_alcance', {}).get('VISOR_ADMIN', {})
    if alcance.get('tipo') == 'SUCURSAL':
        return await db.users.find({'sucursal_id': {'$in': alcance['sucursales_ids']}})
    return await db.users.find({})  # GLOBAL
```

---

## 7. ARCHIVOS A TOCAR

| Archivo | Cambio | Líneas estimadas |
|---------|--------|------------------|
| `/app/backend/server.py` | +4 endpoints alcance | +100 |
| `/app/backend/modules/auth/schemas.py` | +campo `sec_roles_alcance` | +5 |
| `/app/frontend/src/pages/Usuarios.js` | +sección alcance en UI | +80 |
| MongoDB users | +campo `sec_roles_alcance` | N/A |

**Total:** 3 archivos, ~185 líneas nuevas

---

## 8. QUÉ NO SE TOCARÁ

| Elemento | Confirmación |
|----------|--------------|
| `rbac_helper.py` | ❌ NO SE MODIFICA |
| `get_current_user()` | ❌ NO SE MODIFICA |
| `Layout.js` | ❌ NO SE MODIFICA |
| Router global | ❌ NO SE MODIFICA |
| Middleware global | ❌ NO SE MODIFICA |
| Auth global | ❌ NO SE MODIFICA |
| Endpoints FASE 1-13 | ❌ NO SE MODIFICAN |
| Resolución de permisos | ❌ NO SE MODIFICA |
| Módulos operativos | ❌ NO SE TOCAN |
| Sistema legacy allowed_* | ❌ NO SE REEMPLAZA |

---

## 9. RIESGOS Y MITIGACIONES

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|--------|--------------|---------|------------|
| 1 | Complejidad en UI | MEDIA | BAJO | UI mínima, solo asignación |
| 2 | Desincronización sec_roles ↔ sec_roles_alcance | BAJA | MEDIO | Validación en asignación |
| 3 | Alcance no aplicado sin modificar endpoints | MEDIA | BAJO | Documentar que es solo metadato |

---

## 10. COMPATIBILIDAD

| Elemento | Compatibilidad |
|----------|---------------|
| `sec_roles` | ✅ Sigue siendo fuente de verdad de roles |
| `sec_permisos` | ✅ Sin cambios |
| `sec_perfil` | ✅ Sin cambios |
| `allowed_servers` (legacy) | ✅ Convive, no se reemplaza |
| Resolución RBAC | ✅ Sin cambios |

---

## 11. ROLLBACK

### Procedimiento

```bash
# 1. Eliminar endpoints de alcance en server.py
# 2. Eliminar campo sec_roles_alcance del schema
# 3. Eliminar sección de alcance en Usuarios.js
# 4. Opcional: Limpiar sec_roles_alcance de usuarios
```

### Tiempo Estimado

**7 minutos**

---

## 12. CHECKLIST DE NO REGRESIÓN

| # | Verificación | Resultado esperado |
|---|--------------|-------------------|
| 1 | Login funciona | ✅ |
| 2 | CRUD usuarios (FASE 9-11) | ✅ |
| 3 | CRUD roles (FASE 9-11) | ✅ |
| 4 | Bitácora RBAC (FASE 12) | ✅ |
| 5 | Perfiles (FASE 13) | ✅ |
| 6 | Dashboards operativos | ✅ |
| 7 | rbac_helper.py no modificado | ✅ |
| 8 | Nuevo campo sec_roles_alcance funciona | ✅ |
| 9 | Asignación de alcance registra auditoría | ✅ |

---

## 13. VALIDACIÓN POST-EJECUCIÓN

Al terminar, documentar con evidencia verificable:

1. Lista de empresas/unidades/sucursales disponibles
2. Asignación de alcance SUCURSAL a un rol de usuario
3. sec_roles_alcance persistido correctamente
4. Auditoría de asignación de alcance
5. FASE 1-13 sigue funcionando
6. rbac_helper.py no modificado
7. Resolución de permisos no modificada
8. Layout.js no modificado

---

## 14. NOTA IMPORTANTE

### Alcance como Metadato (Esta Fase)

En esta fase, el alcance es **solo metadato**. Los endpoints existentes NO filtrarán datos por alcance automáticamente. La **aplicación real** del alcance se implementará cuando se proteja cada módulo operativo.

### Ejemplo de Futuro Uso

```
FASE 14: Asignar alcance a usuarios (METADATO)
FASE 15+: Aplicar alcance en GET /api/users (FILTRADO REAL)
FASE 16+: Aplicar alcance en módulo Comercial
...
```

---

## 15. SOLICITUD DE APROBACIÓN

### 15.1 Resumen de la propuesta

| # | Elemento |
|---|----------|
| 1 | Agregar campo `sec_roles_alcance` en users |
| 2 | Crear endpoint `GET /api/admin/alcance/empresas` |
| 3 | Crear endpoint `GET /api/admin/alcance/unidades` |
| 4 | Crear endpoint `GET /api/admin/alcance/sucursales` |
| 5 | Crear endpoint `POST /api/admin/alcance/asignar` |
| 6 | Agregar sección de alcance en UI de usuario |
| 7 | Registrar auditoría de asignación de alcance |

### 15.2 Modelo de alcance

```json
{
  "sec_roles_alcance": {
    "[ROL]": {
      "tipo": "SUCURSAL",
      "empresa_id": "...",
      "unidades_ids": [],
      "sucursales_ids": ["SUC_CIENFUEGOS"],
      "almacenes_ids": []
    }
  }
}
```

### 15.3 Decisión solicitada

**¿Aprueba FASE 14 con OPCIÓN A (Alcance en sec_roles existente)?**

- [ ] SÍ, proceder con OPCIÓN A
- [ ] NO, requiere ajustes
- [ ] PREFERIR OPCIÓN B (usar rbac_usuarios_roles)
- [ ] PREFERIR OPCIÓN C (alcance solo en perfil)
- [ ] DIFERIR

---

**FIN DEL DOCUMENTO DE PROPUESTA FASE 14**
