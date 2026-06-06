# FASE 9 - PROPUESTA: PROTECCIÓN REAL DE ENDPOINTS
## Arquitectura de Seguridad EDARSA HUB

**Versión:** 1.0  
**Fecha:** Diciembre 2025  
**Estado:** PENDIENTE APROBACIÓN  
**Requisitos previos:** FASE 1-8 ✅

---

## 1. RESUMEN EJECUTIVO

Este documento propone la **activación de protección real** en backend para los permisos aprobados en FASE 8:

- `SISTEMA_USUARIOS_VER` → Protege `GET /api/users`
- `SISTEMA_ROLES_VER` → Protege `GET /api/roles`

### Estado actual:

| Endpoint | Protección actual | Protección propuesta |
|----------|-------------------|---------------------|
| `GET /api/users` | `role_level >= 3` (Administrador+) | Permiso granular + fallback legacy |
| `GET /api/roles` | `role_level >= 3` (Administrador+) | Permiso granular + fallback legacy |

### Objetivo:

Validar que el sistema RBAC puede **controlar acceso real** a endpoints sin romper el funcionamiento existente, manteniendo fallback para usuarios legacy.

---

## 2. DIAGNÓSTICO DEL MEJOR PUNTO DE PROTECCIÓN

### 2.1 Análisis de endpoints candidatos

| Endpoint | Archivo | Función | Riesgo de modificación |
|----------|---------|---------|------------------------|
| `GET /api/users` | `/modules/auth/service.py` | `get_users()` | BAJO |
| `GET /api/roles` | `/modules/auth/service.py` | `get_roles()` | BAJO |

### 2.2 Protección actual (legacy)

```python
# service.py línea 148
current_level = _get_role_level(current_user.get('role', ''))
if current_level < 3:  # Mínimo Administrador
    raise HTTPException(status_code=403, detail="No autorizado")
```

**Roles con acceso actual:**
- SuperAdministrador (level 100) ✅
- Administrador (level 3) ✅
- Supervisor (level 2) ❌
- Usuario (level 1) ❌

### 2.3 Helper existente

Ya existe `verificar_permiso_v6()` en `server.py` que implementa la resolución de 4 capas:
1. Permisos directos (`sec_permisos`)
2. Múltiples roles (`sec_roles` array)
3. Rol único (`sec_rol` string)
4. Fallback legacy (SuperAdmin)

### 2.4 Estrategia recomendada

**Agregar verificación RBAC ANTES del check legacy**, permitiendo que:
1. Si tiene permiso RBAC → ACCESO ✅
2. Si NO tiene permiso RBAC → Evaluar fallback legacy (level >= 3)

Esto garantiza **compatibilidad total** con usuarios existentes mientras permite control granular para usuarios piloto.

---

## 3. OPCIÓN A: PROTEGER SOLO GET /api/users (MENOR RIESGO)

### 3.1 Descripción

Proteger **solo un endpoint** para validar el mecanismo antes de expandir.

### 3.2 Cambio propuesto

```python
# service.py - get_users()
async def get_users(current_user: Dict) -> List[Dict]:
    # FASE 9: Verificar permiso granular RBAC
    tiene_permiso_rbac = await verificar_permiso_v6(current_user, 'SISTEMA_USUARIOS_VER')
    
    if not tiene_permiso_rbac:
        # Fallback legacy: verificar nivel de rol
        current_level = _get_role_level(current_user.get('role', ''))
        if current_level < 3:
            raise HTTPException(status_code=403, detail="No autorizado")
    
    return await repo.get_all_users()
```

### 3.3 Archivos a modificar

| Archivo | Cambio | Líneas |
|---------|--------|--------|
| `/app/backend/modules/auth/service.py` | Agregar verificación RBAC | +8 líneas |

### 3.4 Importación necesaria

```python
# Al inicio de service.py
from server import verificar_permiso_v6
```

**PROBLEMA**: Importar desde `server.py` crea dependencia circular.

### 3.5 Solución: Mover helper a módulo común

Mover `verificar_permiso_v6()` a un módulo compartido:
- `/app/backend/core/rbac.py` (nuevo archivo)

### 3.6 Rollback

```
TIEMPO: 2 minutos
1. Revertir service.py a versión anterior
2. Opcional: Eliminar core/rbac.py
```

---

## 4. OPCIÓN B: PROTEGER AMBOS ENDPOINTS (RIESGO BAJO)

### 4.1 Descripción

Proteger **ambos endpoints** (`GET /api/users` y `GET /api/roles`) en una sola iteración.

### 4.2 Cambios propuestos

```python
# service.py - get_users()
async def get_users(current_user: Dict) -> List[Dict]:
    tiene_permiso = await verificar_permiso_usuarios(current_user)
    if not tiene_permiso:
        current_level = _get_role_level(current_user.get('role', ''))
        if current_level < 3:
            raise HTTPException(status_code=403, detail="No autorizado")
    return await repo.get_all_users()

# service.py - get_roles()
async def get_roles(current_user: Dict) -> List[Dict]:
    tiene_permiso = await verificar_permiso_roles(current_user)
    if not tiene_permiso:
        current_level = _get_role_level(current_user.get('role', ''))
        if current_level < 3:
            raise HTTPException(status_code=403, detail="No autorizado")
    return await repo.get_all_roles()
```

### 4.3 Archivos a modificar

| Archivo | Cambio | Líneas |
|---------|--------|--------|
| `/app/backend/modules/auth/service.py` | Verificación RBAC en 2 funciones | +16 líneas |
| `/app/backend/core/rbac.py` | Nuevo archivo con helpers | ~60 líneas |

### 4.4 Rollback

```
TIEMPO: 3 minutos
1. Revertir service.py
2. Eliminar core/rbac.py
```

---

## 5. OPCIÓN C: PROTECCIÓN VÍA DECORATOR (RIESGO MEDIO)

### 5.1 Descripción

Crear un **decorator reutilizable** para proteger endpoints con permisos RBAC.

### 5.2 Implementación propuesta

```python
# core/rbac.py
def requiere_permiso(permiso: str, fallback_level: int = 3):
    """Decorator para proteger endpoints con RBAC + fallback legacy."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, current_user: Dict, **kwargs):
            tiene_permiso = await verificar_permiso_v6(current_user, permiso)
            if not tiene_permiso:
                level = _get_role_level(current_user.get('role', ''))
                if level < fallback_level:
                    raise HTTPException(status_code=403, detail="No autorizado")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Uso:
@requiere_permiso('SISTEMA_USUARIOS_VER')
async def get_users(current_user: Dict) -> List[Dict]:
    return await repo.get_all_users()
```

### 5.3 Por qué NO es recomendado para FASE 9

- Introduce abstracción prematura
- Mayor complejidad de debugging
- Más difícil de revertir
- Riesgo de afectar otros endpoints si se usa mal

---

## 6. RECOMENDACIÓN

### 6.1 Opción recomendada: **OPCIÓN B - Proteger Ambos Endpoints**

| Criterio | Evaluación |
|----------|------------|
| Valida el piloto completo | ✅ Ambos permisos de FASE 8 quedan activos |
| Riesgo controlado | ✅ Solo 2 endpoints del mismo módulo |
| Fallback legacy | ✅ Usuarios existentes siguen funcionando |
| Sin abstracción prematura | ✅ Código inline, fácil de entender |
| Rollback simple | ✅ 3 minutos |

### 6.2 Justificación

1. **Coherencia**: Ambos permisos (`SISTEMA_USUARIOS_VER`, `SISTEMA_ROLES_VER`) son del mismo dominio
2. **Validación completa**: Demuestra que el sistema funciona con múltiples permisos activos
3. **Sin dependencia circular**: Se crea módulo `core/rbac.py` limpio
4. **Fallback garantizado**: Usuarios legacy siguen accediendo normalmente

---

## 7. ALCANCE EXACTO RECOMENDADO

### 7.1 Endpoints a proteger

| Endpoint | Permiso requerido | Fallback legacy |
|----------|-------------------|-----------------|
| `GET /api/users` | `SISTEMA_USUARIOS_VER` | `role_level >= 3` |
| `GET /api/roles` | `SISTEMA_ROLES_VER` | `role_level >= 3` |

### 7.2 Lógica de resolución

```
┌─────────────────────────────────────────────────────────────────┐
│            VERIFICACIÓN DE ACCESO (FASE 9)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. ¿Tiene permiso RBAC?                                        │
│     └─ verificar_permiso_v6(user, 'SISTEMA_USUARIOS_VER')       │
│        ├─ sec_permisos contiene permiso? → ACCESO ✅            │
│        ├─ sec_roles hereda permiso? → ACCESO ✅                 │
│        ├─ sec_rol hereda permiso? → ACCESO ✅                   │
│        └─ SuperAdmin? → ACCESO ✅                               │
│                                                                 │
│  2. Si NO tiene permiso RBAC:                                   │
│     └─ Fallback legacy:                                         │
│        ├─ role_level >= 3 (Administrador+)? → ACCESO ✅         │
│        └─ role_level < 3? → DENEGADO ❌                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.3 Matriz de acceso esperada

| Usuario | role | Tiene sec_permisos/roles | Acceso antes | Acceso después |
|---------|------|--------------------------|--------------|----------------|
| SuperAdmin | SuperAdministrador | - | ✅ | ✅ (fallback RBAC) |
| Admin legacy | Administrador | NO | ✅ | ✅ (fallback level) |
| Admin piloto | Administrador | SÍ (SISTEMA_USUARIOS_VER) | ✅ | ✅ (RBAC) |
| Supervisor | Supervisor | NO | ❌ | ❌ |
| Supervisor piloto | Supervisor | SÍ (SISTEMA_USUARIOS_VER) | ❌ | ✅ (RBAC!) |
| Usuario | Usuario | NO | ❌ | ❌ |

**Caso destacado**: Un Supervisor con `SISTEMA_USUARIOS_VER` asignado vía RBAC **ahora podrá ver usuarios**, aunque su rol legacy no lo permitía. Esto es el comportamiento deseado del piloto.

---

## 8. ARCHIVOS A TOCAR

### 8.1 Archivo nuevo

| Archivo | Propósito |
|---------|-----------|
| `/app/backend/core/rbac.py` | Helper `verificar_permiso_v6` movido aquí |

### 8.2 Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `/app/backend/modules/auth/service.py` | Agregar verificación RBAC en `get_users()` y `get_roles()` |
| `/app/backend/server.py` | Importar helper desde `core/rbac.py` |

### 8.3 Archivos NO modificados

| Archivo | Confirmación |
|---------|--------------|
| `/app/backend/modules/auth/routes.py` | ❌ NO SE MODIFICA |
| `Layout.js` | ❌ NO SE MODIFICA |
| Router global | ❌ NO SE MODIFICA |
| Auth global | ❌ NO SE MODIFICA |
| Middleware | ❌ NO SE MODIFICA |
| `get_current_user()` | ❌ NO SE MODIFICA |

---

## 9. CÓMO SE RESOLVERÁ EL PERMISO EN BACKEND

### 9.1 Nuevo módulo `/app/backend/core/rbac.py`

```python
"""
FASE 9: Módulo de verificación RBAC.
Contiene helpers para verificar permisos granulares.
"""

from motor.motor_asyncio import AsyncIOMotorClient
import os

# Conexión a MongoDB
client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
db = client[os.environ.get('DB_NAME', 'edarsa_hub')]

# Whitelist FASE 8
PERMISOS_WHITELIST = ["SISTEMA_ESTRUCTURA_VER", "SISTEMA_USUARIOS_VER", "SISTEMA_ROLES_VER"]
ROLES_WHITELIST = ["VISOR_ESTRUCTURA", "VISOR_SISTEMA", "VISOR_ADMIN"]


async def verificar_permiso(user: dict, permiso: str) -> bool:
    """
    Verifica permiso con resolución de 4 capas.
    """
    # 1. Permisos directos
    if permiso in user.get('sec_permisos', []):
        return True
    
    # 2. Múltiples roles
    for rol_codigo in user.get('sec_roles', []):
        if rol_codigo in ROLES_WHITELIST:
            rol_doc = await db.sec_roles.find_one({"codigo": rol_codigo, "activo": True})
            if rol_doc and permiso in rol_doc.get('permisos', []):
                return True
    
    # 3. Rol único (compatibilidad FASE 5)
    sec_rol = user.get('sec_rol')
    if sec_rol and sec_rol in ROLES_WHITELIST:
        rol_doc = await db.sec_roles.find_one({"codigo": sec_rol, "activo": True})
        if rol_doc and permiso in rol_doc.get('permisos', []):
            return True
    
    # 4. Fallback SuperAdmin
    if user.get('role') == 'SuperAdministrador':
        return True
    
    return False
```

### 9.2 Uso en service.py

```python
from core.rbac import verificar_permiso

async def get_users(current_user: Dict) -> List[Dict]:
    # FASE 9: Verificar permiso RBAC
    tiene_permiso = await verificar_permiso(current_user, 'SISTEMA_USUARIOS_VER')
    
    if not tiene_permiso:
        # Fallback legacy
        current_level = _get_role_level(current_user.get('role', ''))
        if current_level < 3:
            raise HTTPException(status_code=403, detail="No autorizado")
    
    return await repo.get_all_users()
```

---

## 10. COMPATIBILIDAD LEGACY

### 10.1 Comportamiento preservado

| Escenario | Antes | Después | Cambio |
|-----------|-------|---------|--------|
| SuperAdmin sin sec_* | ✅ | ✅ | Ninguno |
| Administrador sin sec_* | ✅ | ✅ | Ninguno |
| Supervisor sin sec_* | ❌ | ❌ | Ninguno |
| Usuario sin sec_* | ❌ | ❌ | Ninguno |

### 10.2 Comportamiento nuevo (piloto)

| Escenario | Antes | Después | Cambio |
|-----------|-------|---------|--------|
| Supervisor con SISTEMA_USUARIOS_VER | ❌ | ✅ | **NUEVO** |
| Usuario con VISOR_ADMIN | ❌ | ✅ | **NUEVO** |

### 10.3 Campos preservados

| Campo | Estado |
|-------|--------|
| `users.role` | ✅ INTACTO (fallback) |
| `users.rbac_role` | ✅ INTACTO |
| `roles` | ✅ INTACTO |
| `rbac_roles` | ✅ INTACTO |

---

## 11. RIESGOS Y MITIGACIONES

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|--------|--------------|---------|------------|
| 1 | Dependencia circular import | BAJA | MEDIO | Módulo `core/rbac.py` aislado |
| 2 | Romper acceso legacy | MUY BAJA | ALTO | Fallback explícito preservado |
| 3 | Usuarios piloto sin acceso esperado | BAJA | BAJO | Verificar asignación previa |
| 4 | Performance (queries adicionales) | BAJA | BAJO | Cache de roles en memoria (futuro) |
| 5 | Regresión en otros endpoints | MUY BAJA | MEDIO | Solo 2 endpoints modificados |

---

## 12. QUÉ NO SE TOCARÁ

| Elemento | Confirmación |
|----------|--------------|
| `get_current_user()` | ❌ NO SE MODIFICA |
| `Layout.js` | ❌ NO SE MODIFICA |
| Router global | ❌ NO SE MODIFICA |
| Auth global | ❌ NO SE MODIFICA |
| Middleware global | ❌ NO SE MODIFICA |
| Endpoints de Comercial | ❌ NO SE MODIFICA |
| Endpoints de Compras | ❌ NO SE MODIFICA |
| Endpoints de Finanzas | ❌ NO SE MODIFICA |
| Endpoints de RH | ❌ NO SE MODIFICA |
| Dashboards | ❌ NO SE MODIFICA |
| PUT/POST/DELETE de users | ❌ NO SE MODIFICA (solo GET) |
| PUT/POST/DELETE de roles | ❌ NO SE MODIFICA (solo GET) |

---

## 13. ROLLBACK

### 13.1 Pasos de rollback

```
TIEMPO TOTAL: 3 minutos

1. Revertir service.py:
   - Eliminar imports de core.rbac
   - Eliminar verificación RBAC en get_users()
   - Eliminar verificación RBAC en get_roles()
   - Restaurar lógica original (solo level check)

2. Opcional:
   - Eliminar /app/backend/core/rbac.py

3. Reiniciar backend

IMPACTO:
- Usuarios legacy: Sin cambio
- Usuarios piloto RBAC: Pierden acceso granular, vuelven a depender del role legacy
- Whitelist FASE 8: Sigue existiendo pero sin efecto en estos endpoints
```

---

## 14. CHECKLIST DE NO REGRESIÓN

### 14.1 Pre-implementación

| Verificación | Método |
|--------------|--------|
| Login SuperAdmin | curl |
| Login Administrador | curl |
| Login Supervisor | curl |
| GET /api/users como SuperAdmin | curl → 200 |
| GET /api/users como Administrador | curl → 200 |
| GET /api/users como Supervisor | curl → 403 |
| GET /api/roles como SuperAdmin | curl → 200 |
| GET /api/roles como Administrador | curl → 200 |
| GET /api/roles como Supervisor | curl → 403 |

### 14.2 Post-implementación

| Verificación | Resultado esperado |
|--------------|-------------------|
| SuperAdmin sin sec_* → GET /api/users | ✅ 200 (fallback RBAC) |
| SuperAdmin sin sec_* → GET /api/roles | ✅ 200 (fallback RBAC) |
| Administrador sin sec_* → GET /api/users | ✅ 200 (fallback level) |
| Administrador sin sec_* → GET /api/roles | ✅ 200 (fallback level) |
| Supervisor sin sec_* → GET /api/users | ❌ 403 |
| Supervisor sin sec_* → GET /api/roles | ❌ 403 |
| **Supervisor CON SISTEMA_USUARIOS_VER → GET /api/users** | ✅ 200 (RBAC!) |
| **Usuario CON VISOR_ADMIN → GET /api/users** | ✅ 200 (RBAC!) |
| FASE 4/5/6/7/8 siguen funcionando | ✅ |
| UI administración RBAC | ✅ |
| Dashboards | ✅ |
| Login | ✅ |

---

## 15. SOLICITUD DE APROBACIÓN

### 15.1 Resumen de lo que se solicita aprobar

| # | Elemento | Descripción |
|---|----------|-------------|
| 1 | Crear `/app/backend/core/rbac.py` | Módulo con helper de verificación |
| 2 | Modificar `service.py` | Agregar verificación RBAC en `get_users()` |
| 3 | Modificar `service.py` | Agregar verificación RBAC en `get_roles()` |
| 4 | Preservar fallback legacy | `role_level >= 3` como alternativa |

### 15.2 Lo que NO se hará en FASE 9

| Elemento | Confirmación |
|----------|--------------|
| Perfiles | ❌ NO |
| Rollout masivo | ❌ NO |
| Protección de otros endpoints | ❌ NO |
| Cambios en auth global | ❌ NO |
| Cambios en middleware | ❌ NO |
| Cambios en Layout.js | ❌ NO |
| Decorator reutilizable | ❌ NO (evitar abstracción prematura) |

### 15.3 Decisión solicitada

**¿Aprueba la ejecución de FASE 9 OPCIÓN B bajo las condiciones descritas?**

- [ ] SÍ, proceder con OPCIÓN B (Proteger ambos endpoints)
- [ ] NO, requiere ajustes (especificar)
- [ ] PREFERIR OPCIÓN A (Solo GET /api/users)
- [ ] DIFERIR esta fase

---

**FIN DEL DOCUMENTO DE PROPUESTA FASE 9**

*Esperando aprobación explícita antes de implementar.*
