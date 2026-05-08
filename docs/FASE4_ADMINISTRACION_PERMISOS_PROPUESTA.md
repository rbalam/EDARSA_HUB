# FASE 4 - PROPUESTA: ADMINISTRACIÓN DE PERMISOS Y ROLES
## Arquitectura de Seguridad EDARSA HUB

**Versión:** 1.0  
**Fecha:** Diciembre 2025  
**Estado:** PENDIENTE APROBACIÓN  
**Requisitos previos:** FASE 1 ✅ | FASE 2 ✅ | FASE 3 ✅

---

## 1. RESUMEN EJECUTIVO

Este documento propone 3 opciones para la FASE 4 del sistema RBAC, enfocada en la **administración real de permisos**, pasando del piloto de FASE 3 (un permiso activo) a un sistema donde se pueden:

- Asignar permisos a usuarios
- Retirar permisos
- Consultar permisos efectivos
- Auditar cambios de permisos
- Sentar las bases para herencia por rol

### Estado actual del sistema de seguridad:

| Colección | Propósito | Estado |
|-----------|-----------|--------|
| `roles` | Roles legacy (Administrador, Supervisor, Usuario) | ✅ Activo - 4 roles |
| `rbac_roles` | Roles de finanzas/cargos (ADMIN, DIRECCION, etc.) | ✅ Activo - 7 roles |
| `sec_permisos_catalogo` | Catálogo de permisos granulares | ✅ 89 permisos |
| `users.role` | Rol legacy del usuario | ✅ En uso |
| `users.rbac_role` | Rol de finanzas (opcional) | ⚠️ Parcial |
| `users.sec_permisos` | Permisos granulares nuevos | ✅ Piloto (1 usuario) |
| `sec_bitacora_acceso` | Auditoría de accesos | ✅ 13 registros |

### Usuario piloto actual:

| Usuario | Rol Legacy | sec_permisos |
|---------|------------|--------------|
| admin@edarsa.com | Supervisor | `["SISTEMA_ESTRUCTURA_VER"]` |
| ricardo@edarsa.com.mx | SuperAdministrador | (usa fallback) |

---

## 2. DIAGNÓSTICO DEL PUNTO DE ENTRADA

### 2.1 Análisis de opciones

| Criterio | Peso | Mejor opción |
|----------|------|--------------|
| Mínimo impacto | ALTO | Endpoint aislado de administración |
| Reutiliza piloto existente | ALTO | Administrar SISTEMA_ESTRUCTURA_VER |
| No toca auth global | CRÍTICO | Endpoints nuevos sin modificar `get_current_user` |
| Permite auditoría | ALTO | Nueva colección `sec_bitacora_admin` |
| Compatibilidad legacy | CRÍTICO | Coexiste sin reemplazar |

### 2.2 Arquitectura de permisos propuesta (3 capas)

```
┌─────────────────────────────────────────────────────────────────┐
│                    PERMISOS EFECTIVOS                           │
│  (Lo que el usuario PUEDE hacer)                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. PERMISOS DIRECTOS (users.sec_permisos)                     │
│     └─ Asignados explícitamente al usuario                     │
│                                                                 │
│  2. PERMISOS POR ROL NUEVO (sec_roles.permisos) [FUTURO]       │
│     └─ Heredados del rol sec_* asignado                        │
│                                                                 │
│  3. FALLBACK LEGACY (users.role)                               │
│     └─ SuperAdmin tiene todo, otros según mapeo                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Colecciones a usar en FASE 4

| Colección | Operación | Propósito |
|-----------|-----------|-----------|
| `users` | READ/WRITE | Leer/escribir `sec_permisos` |
| `sec_permisos_catalogo` | READ | Validar que permiso existe |
| `sec_bitacora_admin` | WRITE | **NUEVA** - Auditoría de administración |

---

## 3. OPCIÓN A: ENDPOINT DE ASIGNACIÓN SIMPLE (MENOR RIESGO)

### 3.1 Descripción

Crear un único endpoint para asignar/retirar permisos a usuarios, con auditoría completa. Se administra únicamente el permiso piloto `SISTEMA_ESTRUCTURA_VER`.

### 3.2 Alcance exacto

| Elemento | Valor |
|----------|-------|
| **Endpoint nuevo** | `POST /api/admin/permisos/asignar` |
| **Permisos administrables** | Solo `SISTEMA_ESTRUCTURA_VER` (whitelist) |
| **Quién puede administrar** | Solo SuperAdministrador |
| **Auditoría** | Nueva colección `sec_bitacora_admin` |
| **UI** | Sin cambios de UI en esta opción |

### 3.3 Contrato del endpoint

```json
POST /api/admin/permisos/asignar
{
  "usuario_email": "admin@edarsa.com",
  "permiso": "SISTEMA_ESTRUCTURA_VER",
  "accion": "ASIGNAR" | "RETIRAR"
}

Response 200:
{
  "success": true,
  "usuario": "admin@edarsa.com",
  "permiso": "SISTEMA_ESTRUCTURA_VER",
  "accion": "ASIGNAR",
  "permisos_actuales": ["SISTEMA_ESTRUCTURA_VER"],
  "auditoria_id": "uuid"
}
```

### 3.4 Archivos a modificar

| Archivo | Cambio | Líneas aprox. |
|---------|--------|---------------|
| `/app/backend/server.py` | Agregar endpoint de administración | +60 líneas |

### 3.5 Colecciones

| Colección | Operación |
|-----------|-----------|
| `users` | UPDATE (solo campo `sec_permisos`) |
| `sec_permisos_catalogo` | READ (validar permiso) |
| `sec_bitacora_admin` | INSERT (nueva) |

### 3.6 Estructura de auditoría propuesta

```json
{
  "id": "uuid",
  "timestamp": "2026-04-21T10:00:00Z",
  "tipo": "ASIGNACION_PERMISO",
  "administrador": {
    "id": "uuid",
    "email": "ricardo@edarsa.com.mx",
    "role": "SuperAdministrador"
  },
  "usuario_afectado": {
    "id": "uuid",
    "email": "admin@edarsa.com"
  },
  "permiso": "SISTEMA_ESTRUCTURA_VER",
  "accion": "ASIGNAR",
  "estado_anterior": [],
  "estado_nuevo": ["SISTEMA_ESTRUCTURA_VER"],
  "origen": "API",
  "ip": "x.x.x.x",
  "fase": "FASE_4"
}
```

### 3.7 Validaciones

1. Solo SuperAdministrador puede ejecutar
2. Permiso debe existir en `sec_permisos_catalogo`
3. Permiso debe estar en whitelist de FASE 4
4. Usuario destino debe existir
5. No permitir auto-asignación (opcional)

### 3.8 Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Asignar permiso inexistente | BAJA | BAJO | Validar contra catálogo |
| Usuario sin permiso pierde acceso | BAJA | BAJO | Whitelist restrictiva |
| Error en auditoría | BAJA | BAJO | try/catch desacoplado |

### 3.9 Rollback

```
TIEMPO: 2 minutos
1. Eliminar endpoint de server.py
2. Opcionalmente limpiar sec_bitacora_admin
3. Permisos ya asignados permanecen (no es problema)
```

---

## 4. OPCIÓN B: ENDPOINT + UI MÍNIMA EN TAB ESTRUCTURA (RIESGO MEDIO)

### 4.1 Descripción

Extender Opción A con una interfaz mínima dentro del tab "Estructura" existente, permitiendo ver y administrar quién tiene el permiso `SISTEMA_ESTRUCTURA_VER`.

### 4.2 Alcance exacto

| Elemento | Valor |
|----------|-------|
| **Endpoints nuevos** | `POST /api/admin/permisos/asignar`, `GET /api/admin/permisos/usuarios/{permiso}` |
| **UI nueva** | Sección "Administración de Acceso" en tab Estructura |
| **Permisos administrables** | Solo `SISTEMA_ESTRUCTURA_VER` |
| **Quién puede administrar** | Solo SuperAdministrador |

### 4.3 Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `/app/backend/server.py` | 2 endpoints nuevos (+80 líneas) |
| `/app/frontend/src/pages/Usuarios.js` | UI en TabsContent estructura (+60 líneas) |

### 4.4 UI propuesta

```
┌─────────────────────────────────────────────────────────────────┐
│  Tab: Estructura                                                │
├─────────────────────────────────────────────────────────────────┤
│  [Árbol organizacional existente...]                           │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  📋 Administración de Acceso (FASE 4 - Piloto)         │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  Permiso: SISTEMA_ESTRUCTURA_VER                        │   │
│  │                                                          │   │
│  │  Usuarios con acceso:                                    │   │
│  │  ┌──────────────────────────────────────────────────┐   │   │
│  │  │ ✓ ricardo@edarsa.com.mx (SuperAdmin - Fallback)  │   │   │
│  │  │ ✓ admin@edarsa.com (Permiso directo) [Retirar]   │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  │                                                          │   │
│  │  [+ Asignar a otro usuario]                             │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 4.5 Riesgos adicionales

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| UI afecta tab Estructura | MEDIA | BAJO | Sección separada al final |
| Complejidad de frontend | MEDIA | BAJO | Componente aislado |

### 4.6 Rollback

```
TIEMPO: 5 minutos
1. Revertir endpoints en server.py
2. Revertir UI en Usuarios.js
3. Tab Estructura vuelve a estado FASE 3
```

---

## 5. OPCIÓN C: ADMINISTRACIÓN COMPLETA CON MÚLTIPLES PERMISOS (RIESGO MEDIO-ALTO)

### 5.1 Descripción

Implementar administración completa de permisos (no solo `SISTEMA_ESTRUCTURA_VER`), con UI dedicada y posibilidad de agregar más permisos del catálogo `sec_permisos_catalogo`.

### 5.2 Alcance exacto

| Elemento | Valor |
|----------|-------|
| **Endpoints nuevos** | CRUD completo de permisos |
| **UI nueva** | Modal o sección dedicada en tab Usuarios |
| **Permisos administrables** | Todos los de módulo "sistema" |
| **Quién puede administrar** | SuperAdministrador y Administrador |

### 5.3 Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `/app/backend/server.py` | 4+ endpoints (+150 líneas) |
| `/app/frontend/src/pages/Usuarios.js` | UI completa (+200 líneas) |

### 5.4 Riesgos

| Riesgo | Probabilidad | Impacto |
|--------|--------------|---------|
| Complejidad excesiva | ALTA | MEDIO |
| Tocar tab Usuarios (producción) | MEDIA | MEDIO |
| Más superficie de ataque | MEDIA | MEDIO |

### 5.5 Por qué NO es recomendado como FASE 4

- Demasiado alcance para una fase incremental
- Toca UI de producción (tab Usuarios)
- Múltiples endpoints aumentan riesgo
- Mejor dejarlo para FASE 5+

---

## 6. RECOMENDACIÓN

### 6.1 Opción recomendada: **OPCIÓN A - Endpoint Simple**

| Criterio | Evaluación |
|----------|------------|
| Mínimo riesgo | ✅ Solo backend, sin UI |
| Valida administración real | ✅ Asignar/retirar funciona |
| Auditoría completa | ✅ Nueva colección dedicada |
| Compatibilidad legacy | ✅ No toca nada existente |
| Rollback trivial | ✅ 2 minutos |
| Base para FASE 5 | ✅ Endpoint reutilizable |

### 6.2 Justificación

1. **Prueba el concepto mínimo** - ¿Podemos administrar permisos sin romper nada?
2. **Auditoría desde el inicio** - Toda acción queda registrada
3. **Sin cambios de UI** - Cero riesgo de regresión visual
4. **Expandible** - El endpoint puede ampliarse en fases futuras
5. **Testeable por curl** - Fácil validación sin frontend

---

## 7. ALCANCE EXACTO RECOMENDADO (OPCIÓN A)

### 7.1 Endpoint a crear

```python
@api_router.post("/admin/permisos/asignar")
async def admin_asignar_permiso(
    request: PermisoAsignacionRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    FASE 4: Asigna o retira un permiso a un usuario.
    Solo SuperAdministrador puede ejecutar.
    Solo permisos en whitelist FASE 4.
    """
```

### 7.2 Whitelist FASE 4

```python
PERMISOS_FASE_4_WHITELIST = [
    "SISTEMA_ESTRUCTURA_VER"
]
```

### 7.3 Lógica de asignación

```python
async def asignar_permiso(db, usuario_email, permiso, accion, admin_user):
    # 1. Validar que admin es SuperAdministrador
    if admin_user.get('role') != 'SuperAdministrador':
        raise HTTPException(403, "Solo SuperAdministrador puede administrar permisos")
    
    # 2. Validar que permiso está en whitelist
    if permiso not in PERMISOS_FASE_4_WHITELIST:
        raise HTTPException(400, f"Permiso {permiso} no disponible en FASE 4")
    
    # 3. Validar que permiso existe en catálogo
    existe = await db.sec_permisos_catalogo.find_one({"codigo": permiso})
    if not existe:
        raise HTTPException(400, f"Permiso {permiso} no existe en catálogo")
    
    # 4. Obtener usuario destino
    usuario = await db.users.find_one({"email": usuario_email})
    if not usuario:
        raise HTTPException(404, f"Usuario {usuario_email} no encontrado")
    
    # 5. Obtener permisos actuales
    permisos_actuales = usuario.get('sec_permisos', [])
    estado_anterior = permisos_actuales.copy()
    
    # 6. Aplicar acción
    if accion == "ASIGNAR":
        if permiso not in permisos_actuales:
            permisos_actuales.append(permiso)
    elif accion == "RETIRAR":
        if permiso in permisos_actuales:
            permisos_actuales.remove(permiso)
    
    # 7. Actualizar usuario
    await db.users.update_one(
        {"email": usuario_email},
        {"$set": {"sec_permisos": permisos_actuales}}
    )
    
    # 8. Registrar auditoría
    await registrar_auditoria_admin(
        db, admin_user, usuario, permiso, accion, 
        estado_anterior, permisos_actuales
    )
    
    return {
        "success": True,
        "usuario": usuario_email,
        "permiso": permiso,
        "accion": accion,
        "permisos_actuales": permisos_actuales
    }
```

### 7.4 Función de auditoría

```python
async def registrar_auditoria_admin(db, admin, usuario, permiso, accion, antes, despues):
    """Registra en bitácora de administración (desacoplado)."""
    try:
        await db.sec_bitacora_admin.insert_one({
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc),
            "tipo": "ASIGNACION_PERMISO",
            "administrador": {
                "id": admin.get('id', ''),
                "email": admin.get('email', ''),
                "role": admin.get('role', '')
            },
            "usuario_afectado": {
                "id": usuario.get('id', ''),
                "email": usuario.get('email', '')
            },
            "permiso": permiso,
            "accion": accion,
            "estado_anterior": antes,
            "estado_nuevo": despues,
            "origen": "API",
            "fase": "FASE_4"
        })
    except Exception as e:
        logging.warning(f"Error en auditoría admin (no crítico): {e}")
```

---

## 8. ARCHIVOS / ENDPOINTS / COLECCIONES

### 8.1 Archivos a modificar

| Archivo | Tipo de cambio | Líneas estimadas |
|---------|----------------|------------------|
| `/app/backend/server.py` | Agregar endpoint + helpers | +70 líneas |

### 8.2 Archivos a crear

Ninguno (todo en server.py para minimizar impacto).

### 8.3 Endpoints

| Método | Endpoint | Propósito |
|--------|----------|-----------|
| POST | `/api/admin/permisos/asignar` | Asignar/retirar permiso |

### 8.4 Colecciones

| Colección | Operación | Propósito |
|-----------|-----------|-----------|
| `users` | UPDATE | Modificar `sec_permisos` |
| `sec_permisos_catalogo` | READ | Validar permiso existe |
| `sec_bitacora_admin` | INSERT | **NUEVA** - Auditoría |

---

## 9. COMPATIBILIDAD LEGACY

### 9.1 Coexistencia de sistemas

```
┌──────────────────────────────────────────────────────────────────┐
│                    SISTEMA ACTUAL (LEGACY)                       │
├──────────────────────────────────────────────────────────────────┤
│  users.role          → Administrador, Supervisor, Usuario        │
│  users.rbac_role     → ADMIN, DIRECCION, etc. (Finanzas)        │
│  roles               → Permisos por módulo (tablero, comercial)  │
│  rbac_roles          → Permisos granulares de finanzas          │
└──────────────────────────────────────────────────────────────────┘
                              │
                              │ COEXISTE SIN REEMPLAZAR
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    SISTEMA NUEVO (FASE 4)                        │
├──────────────────────────────────────────────────────────────────┤
│  users.sec_permisos  → Permisos granulares directos             │
│  sec_permisos_catalogo → Catálogo de 89 permisos               │
│  sec_bitacora_admin  → Auditoría de administración              │
└──────────────────────────────────────────────────────────────────┘
```

### 9.2 Reglas de compatibilidad

1. **NO se modifica** `users.role` ni `users.rbac_role`
2. **NO se modifica** `roles` ni `rbac_roles`
3. **NO se cambia** `get_current_user()` - sigue leyendo role legacy
4. **El nuevo sistema es ADITIVO** - agrega capacidades sin quitar

### 9.3 Resolución de permisos (orden de precedencia)

```python
def tiene_permiso(user, permiso):
    # 1. Verificar permisos directos (sec_permisos)
    if permiso in user.get('sec_permisos', []):
        return True
    
    # 2. Fallback: SuperAdmin tiene todo
    if user.get('role') == 'SuperAdministrador':
        return True
    
    # 3. [FUTURO FASE 5+] Verificar por rol nuevo
    # 4. [FUTURO FASE 6+] Verificar por perfil
    
    return False
```

---

## 10. AUDITORÍA PROPUESTA

### 10.1 Nueva colección: `sec_bitacora_admin`

**Propósito:** Registrar todas las acciones de administración de permisos/roles.

**Diferencia con `sec_bitacora_acceso`:**
- `sec_bitacora_acceso` → Registra ACCESOS a recursos
- `sec_bitacora_admin` → Registra CAMBIOS administrativos

### 10.2 Estructura del documento

```json
{
  "id": "uuid",
  "timestamp": "ISODate",
  "tipo": "ASIGNACION_PERMISO | RETIRO_PERMISO | CAMBIO_ROL | ...",
  "administrador": {
    "id": "uuid",
    "email": "string",
    "role": "string"
  },
  "usuario_afectado": {
    "id": "uuid",
    "email": "string"
  },
  "permiso": "string (código)",
  "accion": "ASIGNAR | RETIRAR",
  "estado_anterior": ["array de permisos"],
  "estado_nuevo": ["array de permisos"],
  "origen": "API | UI | SCRIPT",
  "ip": "string (opcional)",
  "fase": "FASE_4",
  "notas": "string (opcional)"
}
```

### 10.3 Índices recomendados

```javascript
db.sec_bitacora_admin.createIndex({ "timestamp": -1 })
db.sec_bitacora_admin.createIndex({ "usuario_afectado.email": 1 })
db.sec_bitacora_admin.createIndex({ "administrador.email": 1 })
db.sec_bitacora_admin.createIndex({ "tipo": 1, "timestamp": -1 })
```

---

## 11. RIESGOS Y MITIGACIONES

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|--------|--------------|---------|------------|
| 1 | Asignar permiso a usuario inexistente | BAJA | BAJO | Validar existencia |
| 2 | Asignar permiso inexistente | BAJA | BAJO | Validar contra catálogo |
| 3 | Admin se auto-retira permisos | BAJA | BAJO | Opcional: bloquear auto-modificación |
| 4 | Auditoría falla | BAJA | BAJO | try/catch desacoplado |
| 5 | Whitelist muy restrictiva | N/A | BAJO | Expandir en fases futuras |
| 6 | Conflicto con legacy | MUY BAJA | BAJO | Sistemas independientes |

---

## 12. QUÉ NO SE TOCARÁ

| Elemento | Confirmación |
|----------|--------------|
| `get_current_user()` | ❌ NO SE MODIFICA |
| `Layout.js` | ❌ NO SE MODIFICA |
| Router global | ❌ NO SE MODIFICA |
| Tab Usuarios UI | ❌ NO SE MODIFICA |
| Tab Roles UI | ❌ NO SE MODIFICA |
| Tab Estructura UI | ❌ NO SE MODIFICA |
| Colección `roles` | ❌ NO SE MODIFICA |
| Colección `rbac_roles` | ❌ NO SE MODIFICA |
| Campo `users.role` | ❌ NO SE MODIFICA |
| Campo `users.rbac_role` | ❌ NO SE MODIFICA |
| Módulos productivos | ❌ NO SE TOCAN |
| Dashboards | ❌ NO SE TOCAN |
| Login | ❌ NO SE TOCA |

---

## 13. ROLLBACK

### 13.1 Pasos de rollback

```
TIEMPO TOTAL: 2-3 minutos

Paso 1: Eliminar endpoint (1 minuto)
- Quitar bloque de código del endpoint /api/admin/permisos/asignar
- Quitar funciones helper asociadas

Paso 2: Opcional - Limpiar colección
- db.sec_bitacora_admin.drop() (solo si se desea)

Paso 3: Permisos asignados
- Los permisos ya asignados a usuarios permanecen
- Funcionan igual que en FASE 3 (piloto)
- NO es necesario revertirlos

IMPACTO: CERO en funcionalidades existentes
```

### 13.2 Criterios de rollback automático

Si cualquiera de estos ocurre:

1. ❌ Login deja de funcionar
2. ❌ Tab Usuarios no carga
3. ❌ Error 500 en endpoint nuevo
4. ❌ Permisos legacy afectados

---

## 14. CHECKLIST DE NO REGRESIÓN

### 14.1 Pre-cambio

- [ ] Login funciona (SuperAdmin, Admin, Supervisor, Usuario)
- [ ] Tab Usuarios carga
- [ ] Tab Roles carga
- [ ] Tab Estructura carga (SuperAdmin)
- [ ] Dashboards funcionan

### 14.2 Post-cambio

| Verificación | Resultado esperado |
|--------------|-------------------|
| Login SuperAdmin | ✅ Funciona |
| Login Admin | ✅ Funciona |
| Login Supervisor | ✅ Funciona |
| Tab Usuarios | ✅ Sin cambios |
| Tab Roles | ✅ Sin cambios |
| Tab Estructura (SuperAdmin) | ✅ Visible |
| GET /api/users | ✅ Funciona |
| GET /api/roles | ✅ Funciona |
| POST /api/admin/permisos/asignar (SuperAdmin) | ✅ 200 OK |
| POST /api/admin/permisos/asignar (Admin) | ✅ 403 Forbidden |
| Auditoría registrada | ✅ Existe en sec_bitacora_admin |
| Dashboards | ✅ Sin cambios |

---

## 15. EVIDENCIA ESPERADA

Para dar por válida la FASE 4:

1. **curl asignar permiso** → HTTP 200, permiso agregado
2. **curl retirar permiso** → HTTP 200, permiso removido
3. **curl como no-SuperAdmin** → HTTP 403
4. **Consulta MongoDB** → Auditoría registrada en `sec_bitacora_admin`
5. **Tab Estructura** → Usuario con permiso puede ver, sin permiso no puede
6. **Screenshots** → Login, tabs, dashboards funcionando

---

## 16. SOLICITUD DE APROBACIÓN

### 16.1 Resumen de lo que se solicita aprobar

| # | Elemento | Descripción |
|---|----------|-------------|
| 1 | Crear endpoint `POST /api/admin/permisos/asignar` | Backend |
| 2 | Crear colección `sec_bitacora_admin` | MongoDB |
| 3 | Whitelist FASE 4: Solo `SISTEMA_ESTRUCTURA_VER` | Restricción |
| 4 | Solo SuperAdministrador puede administrar | Seguridad |
| 5 | Auditoría completa de cada acción | Trazabilidad |

### 16.2 Lo que NO se hará en FASE 4

| Elemento | Confirmación |
|----------|--------------|
| Crear UI de administración | ❌ NO |
| Modificar tabs existentes | ❌ NO |
| Expandir a múltiples permisos | ❌ NO |
| Tocar auth global | ❌ NO |
| Migrar usuarios | ❌ NO |
| Reemplazar roles legacy | ❌ NO |

### 16.3 Decisión solicitada

**¿Aprueba la ejecución de FASE 4 OPCIÓN A bajo las condiciones descritas?**

- [ ] SÍ, proceder con OPCIÓN A (Endpoint simple)
- [ ] NO, requiere ajustes (especificar)
- [ ] PREFERIR OPCIÓN B (Endpoint + UI mínima)
- [ ] DIFERIR esta fase

---

**FIN DEL DOCUMENTO DE PROPUESTA FASE 4**

*Esperando aprobación explícita antes de implementar.*
