# FASE 16 - PROPUESTA
## Aplicación de Alcance Organizacional Real en GET /api/users (Piloto)

**Versión:** 1.0  
**Fecha:** Diciembre 2025  
**Estado:** PROPUESTA PENDIENTE DE APROBACIÓN  
**Autor:** Agente Arquitecto  
**Tipo:** Implementación Controlada - Módulo Sistema (Piloto)

---

## 1. RESUMEN EJECUTIVO

Esta propuesta implementa el **primer filtrado real** por alcance organizacional (`sec_roles_alcance`) en el endpoint `GET /api/users` como **piloto controlado**.

**OBJETIVO:** Que un usuario con alcance limitado (ej: SUCURSAL CIENFUEGOS) solo vea usuarios de esa sucursal, no todos los usuarios del sistema.

**ALCANCE:** Solo el endpoint `GET /api/users` del módulo Sistema. Ningún otro endpoint ni módulo.

---

## 2. ESTADO ACTUAL (DIAGNÓSTICO)

### 2.1 Endpoint GET /api/users

```python
# /app/backend/modules/auth/service.py - Líneas 143-166
async def get_users(current_user: Dict) -> List[Dict]:
    # FASE 9: Verificar permiso RBAC
    tiene_permiso_rbac = await verificar_permiso_rbac(current_user, 'SISTEMA_USUARIOS_VER')
    
    if not tiene_permiso_rbac:
        # Fallback legacy
        current_level = _get_role_level(current_user.get('role', ''))
        if current_level < 3:
            raise HTTPException(status_code=403, detail="No autorizado")
    
    return await repo.get_all_users()  # ← RETORNA TODOS SIN FILTRAR
```

**PROBLEMA:** El endpoint verifica permiso de acceso, pero NO aplica filtrado por alcance organizacional. Cualquier usuario con `SISTEMA_USUARIOS_VER` ve TODOS los usuarios.

### 2.2 Campos Disponibles para Filtrado

| Campo en Usuario | Propósito | Disponible |
|------------------|-----------|------------|
| `empresa_default_id` | Empresa principal del usuario | ✅ SÍ |
| `empresas_permitidas` | Lista de empresas autorizadas | ✅ SÍ |
| `sucursales` | (Legacy, posiblemente obsoleto) | ⚠️ VACÍO en mayoría |

### 2.3 Estructura de sec_roles_alcance

```json
{
  "sec_roles_alcance": {
    "VISOR_ADMIN": {
      "tipo": "SUCURSAL",
      "empresa_id": "1d91f076-...",
      "sucursales_ids": ["268cee46-..."],
      "unidades_ids": [],
      "almacenes_ids": []
    }
  }
}
```

---

## 3. PROPUESTA DE IMPLEMENTACIÓN

### 3.1 Lógica de Filtrado Propuesta

```
SI usuario tiene role == 'SuperAdministrador':
    → Retornar TODOS los usuarios (sin filtro)

SI usuario tiene sec_roles_alcance con tipo GLOBAL:
    → Retornar TODOS los usuarios (sin filtro)

SI usuario tiene sec_roles_alcance con tipo EMPRESA:
    → Filtrar usuarios donde empresa_default_id IN [empresas del alcance]

SI usuario tiene sec_roles_alcance con tipo UNIDAD:
    → Filtrar usuarios donde empresa_default_id IN [empresas de las unidades del alcance]

SI usuario tiene sec_roles_alcance con tipo SUCURSAL:
    → Filtrar usuarios donde empresa_default_id IN [empresas de las sucursales del alcance]

SI usuario tiene sec_roles_alcance con tipo ALMACEN:
    → Filtrar usuarios donde empresa_default_id IN [empresas de las sucursales de los almacenes]

SI usuario NO tiene sec_roles_alcance (vacío):
    → Aplicar fallback: filtrar por empresas_permitidas del usuario actual
```

### 3.2 Función de Resolución de Alcance

Se creará una función helper que resuelve el alcance del usuario actual:

```python
async def resolver_alcance_usuarios(current_user: Dict) -> Dict:
    """
    Resuelve el alcance organizacional del usuario para filtrar usuarios.
    
    Returns:
        Dict con:
        - tiene_acceso_global: bool
        - empresas_ids: List[str] (empresas a las que tiene acceso)
    """
```

### 3.3 Modificación Propuesta en service.py

```python
async def get_users(current_user: Dict) -> List[Dict]:
    # FASE 9: Verificar permiso RBAC (SIN CAMBIOS)
    tiene_permiso_rbac = await verificar_permiso_rbac(current_user, 'SISTEMA_USUARIOS_VER')
    
    if not tiene_permiso_rbac:
        current_level = _get_role_level(current_user.get('role', ''))
        if current_level < 3:
            raise HTTPException(status_code=403, detail="No autorizado")
    
    # FASE 16: Aplicar filtrado por alcance organizacional
    alcance = await resolver_alcance_usuarios(current_user)
    
    if alcance['tiene_acceso_global']:
        return await repo.get_all_users()
    
    return await repo.get_users_by_empresas(alcance['empresas_ids'])
```

### 3.4 Nueva Función en repository.py

```python
async def get_users_by_empresas(empresas_ids: List[str]) -> List[Dict]:
    """Obtiene usuarios filtrados por empresas."""
    if not empresas_ids:
        return []
    return await get_db().users.find(
        {"empresa_default_id": {"$in": empresas_ids}},
        {"_id": 0, "password": 0}
    ).to_list(1000)
```

---

## 4. CASOS DE PRUEBA

### 4.1 Matriz de Pruebas

| Usuario | Alcance | Resultado Esperado |
|---------|---------|-------------------|
| `ricardo@edarsa.com.mx` (SuperAdmin) | N/A | Ve TODOS los usuarios |
| Usuario con alcance GLOBAL | GLOBAL | Ve TODOS los usuarios |
| Usuario con alcance EMPRESA: CIENFUEGOS | EMPRESA | Ve solo usuarios de CIENFUEGOS |
| Usuario con alcance SUCURSAL: CIENFUEGOS | SUCURSAL | Ve solo usuarios de empresa CIENFUEGOS |
| Usuario sin sec_roles_alcance | Vacío | Ve usuarios de sus `empresas_permitidas` |
| Usuario sin permisos | N/A | HTTP 403 |

### 4.2 Pruebas de No Regresión

| Prueba | Método |
|--------|--------|
| SuperAdmin ve todos los usuarios | curl + conteo |
| Login sigue funcionando | curl |
| Otros endpoints no afectados | curl GET /api/roles |
| Frontend Usuarios.js funciona | Screenshot |

---

## 5. ARCHIVOS A MODIFICAR

| Archivo | Cambio | Riesgo |
|---------|--------|--------|
| `/app/backend/modules/auth/service.py` | Agregar lógica de filtrado en `get_users()` | BAJO |
| `/app/backend/modules/auth/repository.py` | Agregar función `get_users_by_empresas()` | BAJO |

### 5.1 Archivos que NO se modifican

| Archivo | Razón |
|---------|-------|
| `rbac_helper.py` | Solo resolución de permisos, no alcance |
| `get_current_user()` | Archivo transversal crítico |
| `server.py` | No se toca |
| `Layout.js` | No se toca |
| Frontend `Usuarios.js` | Solo consume el endpoint, no requiere cambios |

---

## 6. FUNCIÓN HELPER PROPUESTA

Se propone crear un archivo nuevo o agregar al existente:

**Opción A:** Agregar a `rbac_helper.py` (riesgo: modificar archivo congelado)

**Opción B (RECOMENDADA):** Crear `/app/backend/core/alcance_helper.py`

```python
"""
FASE 16: Helper de resolución de alcance organizacional.
Resuelve el alcance del usuario para filtrado de datos.
"""

async def resolver_alcance_usuarios(current_user: Dict, db) -> Dict:
    """
    Resuelve el alcance organizacional para filtrado de usuarios.
    
    Orden de resolución:
    1. SuperAdministrador → GLOBAL
    2. sec_roles_alcance con tipo GLOBAL → GLOBAL
    3. sec_roles_alcance con tipo específico → empresas calculadas
    4. Sin alcance → usar empresas_permitidas del usuario
    
    Returns:
        {
            "tiene_acceso_global": bool,
            "empresas_ids": List[str]
        }
    """
```

---

## 7. AUDITORÍA

Se registrará en `sec_bitacora_admin` cuando se active el filtrado:

| Campo | Valor |
|-------|-------|
| tipo | `FILTRADO_ALCANCE_APLICADO` |
| endpoint | `/api/users` |
| usuario | email del solicitante |
| alcance_aplicado | tipo y valores del alcance |
| usuarios_visibles | cantidad de usuarios retornados |

---

## 8. ROLLBACK

### Procedimiento de Rollback

```bash
# 1. Revertir service.py a llamar repo.get_all_users() directamente
# 2. Eliminar función get_users_by_empresas() de repository.py
# 3. Eliminar alcance_helper.py si se creó
```

**Tiempo estimado:** 5 minutos

### Condiciones para Rollback

- Si SuperAdmin deja de ver todos los usuarios
- Si el filtrado es incorrecto
- Si hay regresión en otros endpoints

---

## 9. REGLA RBAC NATIVO (FASE 15)

### 9.1 Checklist Obligatorio

| # | Paso | Cumplimiento |
|---|------|--------------|
| 1 | Definir permisos nuevos | ✅ Usa existente: `SISTEMA_USUARIOS_VER` |
| 2 | Definir roles/perfiles | ✅ Sin cambios, usa existentes |
| 3 | Definir alcance organizacional | ✅ Usa `sec_roles_alcance` existente |
| 4 | Proteger backend | ✅ Ya protegido (FASE 9), agrega filtrado |
| 5 | Reflejar en frontend | ✅ No requiere cambios (endpoint devuelve filtrado) |
| 6 | Registrar auditoría | ✅ Se registrará filtrado aplicado |
| 7 | Validar acceso/denegación | ✅ Plan de pruebas incluido |
| 8 | Documentar matriz | ✅ Este documento |

### 9.2 Entregables

| Entregable | Estado |
|------------|--------|
| Catálogo de permisos | ✅ Existente |
| Endpoint protegido | ✅ `GET /api/users` |
| Alcance definido | ✅ `sec_roles_alcance` |
| Evidencia de pruebas | Pendiente implementación |
| No regresión | Pendiente implementación |

---

## 10. RIESGOS Y MITIGACIÓN

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| SuperAdmin pierde acceso global | BAJA | CRÍTICO | Check explícito para SuperAdmin primero |
| Usuarios sin alcance no ven nada | MEDIA | ALTO | Fallback a `empresas_permitidas` |
| Regresión en otros endpoints | BAJA | MEDIO | Solo se modifica `get_users()` |
| Frontend rompe | MUY BAJA | BAJO | El endpoint solo cambia qué usuarios devuelve |

---

## 11. COMPATIBILIDAD

### 11.1 Con Sistema Legacy

| Elemento Legacy | Impacto |
|-----------------|---------|
| `role` | ✅ Sin cambios, SuperAdmin sigue funcionando |
| `allowed_servers` | ✅ No se usa en este endpoint |
| `allowed_sucursales` | ✅ No se usa en este endpoint |
| `empresas_permitidas` | ✅ Se usa como fallback |

### 11.2 Con RBAC Existente

| Elemento RBAC | Impacto |
|---------------|---------|
| `sec_permisos` | ✅ Sin cambios |
| `sec_roles` | ✅ Sin cambios |
| `sec_roles_alcance` | ✅ AHORA SE APLICA REALMENTE |
| Verificación de permisos | ✅ Sin cambios en `rbac_helper.py` |

---

## 12. LO QUE NO SE IMPLEMENTA EN ESTA FASE

| Elemento | Razón |
|----------|-------|
| Filtrado en PUT /api/users | Fase separada |
| Filtrado en DELETE /api/users | Fase separada |
| Filtrado en POST /api/users | Fase separada |
| Filtrado en otros módulos | Fase separada |
| Modificación de `rbac_helper.py` | Congelado |
| Modificación de UI | No requerido |

---

## 13. SOLICITUD DE APROBACIÓN

### Alcance Solicitado

Esta propuesta solicita aprobación para:

1. ✅ Crear `/app/backend/core/alcance_helper.py` con función `resolver_alcance_usuarios()`
2. ✅ Modificar `get_users()` en `/app/backend/modules/auth/service.py` para aplicar filtrado
3. ✅ Agregar `get_users_by_empresas()` en `/app/backend/modules/auth/repository.py`
4. ✅ Registrar auditoría de filtrado aplicado
5. ✅ Ejecutar pruebas de validación

### Archivos que NO se modifican

- `rbac_helper.py`
- `get_current_user()`
- `server.py`
- `Layout.js`
- Frontend

### Tiempo Estimado de Implementación

**30-45 minutos**

---

**FIN DE LA PROPUESTA FASE 16**
