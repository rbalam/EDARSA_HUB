# FASE 11 - PROPUESTA: PROTECCIÓN REAL DE ENDPOINTS POST (CREAR)
## Arquitectura de Seguridad EDARSA HUB

**Versión:** 1.0  
**Fecha:** Diciembre 2025  
**Estado:** PENDIENTE APROBACIÓN  
**Requisitos previos:** FASE 1-10 ✅

---

## 1. RESUMEN EJECUTIVO

Este documento propone la **protección real de endpoints POST** del módulo Sistema para crear usuarios y roles.

### Diagnóstico actual:

| Endpoint | Estado actual | Protección |
|----------|---------------|------------|
| `POST /auth/register` | Existe | **PÚBLICO** (auto-registro) |
| `POST /api/users` | **NO EXISTE** | N/A |
| `POST /api/roles` | Existe | `role_level >= 3` |

### Hallazgo importante:

**No existe un endpoint `POST /api/users` para crear usuarios desde administración.**

El único endpoint de creación de usuarios es `POST /auth/register`, que es **público** y permite auto-registro.

### Implicación:

FASE 11 tiene dos opciones:
1. **OPCIÓN A**: Solo proteger `POST /api/roles` (lo que existe)
2. **OPCIÓN B**: Crear endpoint `POST /api/users` + proteger ambos

---

## 2. DIAGNÓSTICO DETALLADO

### 2.1 Endpoint POST /auth/register

```python
# routes.py línea 42
@router.post("/auth/register")
async def register(user_data: UserCreate):
    return await service.register_user(user_data)
```

**Características:**
- Es **público** (no requiere autenticación)
- Permite que cualquiera cree una cuenta
- Usa `UserCreate` schema con rol por defecto
- Retorna token JWT automáticamente

**Problema potencial:**
- Si el sistema no debe permitir auto-registro, este endpoint es un riesgo de seguridad
- Si debe permitir auto-registro, no debería estar bajo RBAC

### 2.2 Endpoint POST /api/roles

```python
# service.py línea 325
async def create_role(role_data: Dict, current_user: Dict) -> Dict:
    current_level = _get_role_level(current_user.get('role', ''))
    if current_level < 3:  # Mínimo Administrador
        raise HTTPException(status_code=403, detail="No autorizado")
```

**Características:**
- Requiere autenticación (`current_user`)
- Protegido por `role_level >= 3` (legacy)
- Listo para agregar verificación RBAC

### 2.3 Permisos en catálogo

| Permiso | Existe en catálogo |
|---------|-------------------|
| `SISTEMA_USUARIOS_CREAR` | ✅ Sí |
| `SISTEMA_ROLES_CREAR` | ✅ Sí |

---

## 3. OPCIÓN A: SOLO PROTEGER POST /api/roles (MENOR RIESGO)

### 3.1 Descripción

Proteger **únicamente** el endpoint que ya existe: `POST /api/roles`.

No tocar `POST /auth/register` ni crear endpoint nuevo.

### 3.2 Cambios propuestos

| Elemento | Cambio |
|----------|--------|
| Permiso nuevo en whitelist | `SISTEMA_ROLES_CREAR` |
| service.py | Agregar verificación RBAC en `create_role()` |
| Rol ADMIN_USUARIOS | NO se modifica |

### 3.3 Whitelist actualizada

```python
PERMISOS_FASE_11_WHITELIST = [
    # ... permisos anteriores ...
    "SISTEMA_ROLES_CREAR"  # FASE 11
]
```

### 3.4 Archivos a modificar

| Archivo | Cambio | Líneas |
|---------|--------|--------|
| `/app/backend/server.py` | Whitelist +1 permiso | +1 |
| `/app/backend/core/rbac_helper.py` | Whitelist +1 permiso | +1 |
| `/app/backend/modules/auth/service.py` | Verificación RBAC en `create_role()` | +10 |
| `/app/frontend/src/pages/Usuarios.js` | Constante actualizada | +1 |

### 3.5 Rollback

```
TIEMPO: 2 minutos
```

### 3.6 Ventajas

- Mínimo riesgo
- No toca auto-registro
- Completa CRUD de roles

### 3.7 Desventajas

- No aborda creación de usuarios
- `POST /auth/register` sigue público

---

## 4. OPCIÓN B: PROTEGER ROLES + CREAR ENDPOINT USUARIOS (RIESGO BAJO)

### 4.1 Descripción

1. Proteger `POST /api/roles` con RBAC
2. Crear nuevo endpoint `POST /api/users` para creación administrativa
3. Proteger `POST /api/users` con RBAC
4. Mantener `POST /auth/register` como está (análisis separado)

### 4.2 Nuevo endpoint propuesto

```python
# routes.py
@router.post("/users")
async def create_user_admin(
    user_data: UserCreate, 
    current_user: Dict = Depends(get_current_user)
):
    """Crear usuario desde administración (requiere RBAC)"""
    return await service.create_user_admin(user_data, current_user)
```

### 4.3 Nueva función en service.py

```python
async def create_user_admin(user_data: UserCreate, current_user: Dict) -> Dict:
    """
    Crea un usuario desde administración.
    
    FASE 11: Requiere permiso SISTEMA_USUARIOS_CREAR o fallback legacy.
    """
    # RBAC check
    tiene_permiso = await verificar_permiso_rbac(current_user, 'SISTEMA_USUARIOS_CREAR')
    if not tiene_permiso:
        current_level = _get_role_level(current_user.get('role', ''))
        if current_level < 3:
            raise HTTPException(status_code=403, detail="No autorizado")
    
    # ... lógica de creación ...
```

### 4.4 Whitelist actualizada

```python
PERMISOS_FASE_11_WHITELIST = [
    # ... permisos anteriores ...
    "SISTEMA_USUARIOS_CREAR",  # FASE 11
    "SISTEMA_ROLES_CREAR"      # FASE 11
]
```

### 4.5 Nuevo rol propuesto

```json
{
  "codigo": "GESTOR_SISTEMA",
  "nombre": "Gestor de Sistema",
  "permisos": [
    "SISTEMA_USUARIOS_VER",
    "SISTEMA_USUARIOS_CREAR",
    "SISTEMA_USUARIOS_EDITAR",
    "SISTEMA_USUARIOS_ELIMINAR",
    "SISTEMA_ROLES_VER",
    "SISTEMA_ROLES_CREAR",
    "SISTEMA_ROLES_EDITAR",
    "SISTEMA_ROLES_ELIMINAR"
  ],
  "fase": "FASE_11"
}
```

### 4.6 Archivos a modificar

| Archivo | Cambio | Líneas |
|---------|--------|--------|
| `/app/backend/server.py` | Whitelist +2 permisos | +2 |
| `/app/backend/core/rbac_helper.py` | Whitelist +2 permisos | +2 |
| `/app/backend/modules/auth/service.py` | Nueva función + modificar `create_role()` | +30 |
| `/app/backend/modules/auth/routes.py` | Nuevo endpoint | +10 |
| `/app/frontend/src/pages/Usuarios.js` | Constantes actualizadas | +3 |

### 4.7 Rollback

```
TIEMPO: 4 minutos
```

---

## 5. OPCIÓN C: ANÁLISIS COMPLETO DE AUTO-REGISTRO (RIESGO MEDIO)

### 5.1 Descripción

Además de lo anterior, analizar y potencialmente restringir `POST /auth/register`.

### 5.2 Por qué NO es recomendado para FASE 11

- Cambio transversal en flujo de autenticación
- Puede romper funcionalidad existente de onboarding
- Requiere análisis de impacto en UI de login/registro
- Mejor abordar en fase separada con alcance específico

---

## 6. RECOMENDACIÓN

### 6.1 Opción recomendada: **OPCIÓN B - Proteger Roles + Crear Endpoint Usuarios**

| Criterio | Evaluación |
|----------|------------|
| Completa CRUD de Sistema | ✅ Usuarios y Roles |
| No toca auto-registro | ✅ POST /auth/register intacto |
| Coherente con FASE 10 | ✅ Mismo patrón |
| Rol útil | ✅ GESTOR_SISTEMA para administración completa |
| Rollback simple | ✅ 4 minutos |

### 6.2 Justificación

1. **Necesidad real**: No existe forma de crear usuarios desde administración
2. **Separación correcta**: Auto-registro vs creación administrativa
3. **Completa el módulo**: CRUD completo para usuarios y roles
4. **Rol consolidado**: `GESTOR_SISTEMA` agrupa todos los permisos del módulo

---

## 7. ALCANCE EXACTO RECOMENDADO

### 7.1 Permisos a agregar a whitelist

| Permiso | Descripción |
|---------|-------------|
| `SISTEMA_USUARIOS_CREAR` | Permite `POST /api/users` (nuevo) |
| `SISTEMA_ROLES_CREAR` | Permite `POST /api/roles` (existente) |

### 7.2 Nuevo rol

```json
{
  "codigo": "GESTOR_SISTEMA",
  "permisos": ["SISTEMA_USUARIOS_*", "SISTEMA_ROLES_*"]
}
```

### 7.3 Nuevo endpoint

```
POST /api/users
- Requiere autenticación
- Requiere SISTEMA_USUARIOS_CREAR o fallback legacy
- Crea usuario sin generar token (diferencia con register)
```

---

## 8. ARCHIVOS A TOCAR

| Archivo | Cambio |
|---------|--------|
| `/app/backend/server.py` | Whitelist |
| `/app/backend/core/rbac_helper.py` | Whitelist |
| `/app/backend/modules/auth/service.py` | Nueva función + modificar existente |
| `/app/backend/modules/auth/routes.py` | Nuevo endpoint |
| `/app/frontend/src/pages/Usuarios.js` | Constantes |

---

## 9. QUÉ NO SE TOCARÁ

| Elemento | Confirmación |
|----------|--------------|
| `POST /auth/register` | ❌ NO SE MODIFICA |
| `POST /auth/login` | ❌ NO SE MODIFICA |
| `get_current_user()` | ❌ NO SE MODIFICA |
| `Layout.js` | ❌ NO SE MODIFICA |
| Módulos operativos | ❌ NO SE MODIFICAN |
| Dashboards | ❌ NO SE MODIFICAN |

---

## 10. RIESGOS Y MITIGACIONES

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|--------|--------------|---------|------------|
| 1 | Conflicto con register | BAJA | MEDIO | Endpoints separados |
| 2 | Duplicación de lógica | BAJA | BAJO | Reutilizar repo functions |
| 3 | Regresión en CRUD | BAJA | MEDIO | Fallback legacy preservado |

---

## 11. ROLLBACK

```
TIEMPO: 4 minutos

1. Eliminar endpoint POST /api/users de routes.py
2. Eliminar función create_user_admin de service.py
3. Revertir verificación RBAC en create_role
4. Revertir whitelists
5. Opcional: eliminar rol GESTOR_SISTEMA
```

---

## 12. CHECKLIST DE NO REGRESIÓN

| Verificación | Resultado esperado |
|--------------|-------------------|
| POST /auth/register (público) | ✅ Sigue funcionando |
| POST /auth/login | ✅ Sigue funcionando |
| POST /api/users (nuevo, con RBAC) | ✅ 200 con permiso |
| POST /api/users (nuevo, sin permiso) | ❌ 403 |
| POST /api/roles (con RBAC) | ✅ 200 con permiso |
| POST /api/roles (sin permiso) | ❌ 403 |
| FASE 4-10 | ✅ Sin regresión |

---

## 13. SOLICITUD DE APROBACIÓN

### 13.1 Resumen

| # | Elemento |
|---|----------|
| 1 | Crear endpoint `POST /api/users` |
| 2 | Proteger `POST /api/users` con `SISTEMA_USUARIOS_CREAR` |
| 3 | Proteger `POST /api/roles` con `SISTEMA_ROLES_CREAR` |
| 4 | Crear rol `GESTOR_SISTEMA` |
| 5 | NO tocar `POST /auth/register` |

### 13.2 Decisión solicitada

**¿Aprueba FASE 11 OPCIÓN B?**

- [ ] SÍ, proceder con OPCIÓN B (crear endpoint + proteger roles)
- [ ] NO, requiere ajustes
- [ ] PREFERIR OPCIÓN A (solo proteger roles)
- [ ] DIFERIR

---

**FIN DEL DOCUMENTO DE PROPUESTA FASE 11**
