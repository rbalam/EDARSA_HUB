# FASE 7 - PROPUESTA: UI MÍNIMA DE ADMINISTRACIÓN RBAC
## Arquitectura de Seguridad EDARSA HUB

**Versión:** 1.0  
**Fecha:** Diciembre 2025  
**Estado:** PENDIENTE APROBACIÓN  
**Requisitos previos:** FASE 1 ✅ | FASE 2 ✅ | FASE 3 ✅ | FASE 4 ✅ | FASE 5 ✅ | FASE 6 ✅

---

## 1. RESUMEN EJECUTIVO

Este documento propone 3 opciones para implementar una **UI mínima de administración** del piloto RBAC existente, permitiendo que SuperAdministrador gestione visualmente:

- Permisos directos (`sec_permisos`)
- Roles piloto (`sec_roles`)
- Auditoría de operaciones RBAC

### Alcance estricto:

| Elemento | Valor fijo |
|----------|------------|
| Permiso administrable | `SISTEMA_ESTRUCTURA_VER` (único) |
| Roles administrables | `VISOR_ESTRUCTURA`, `VISOR_SISTEMA` (únicos) |
| Actor autorizado | Solo `SuperAdministrador` |
| Ubicación UI | Dentro de `/usuarios` |

### Lo que NO incluye esta fase:
- Perfiles predefinidos
- Expansión de whitelist
- Nuevos permisos o roles
- CRUD general de seguridad
- Migración masiva
- Cambios en auth global

---

## 2. DIAGNÓSTICO DEL PUNTO DE ENTRADA UI

### 2.1 Análisis de `/app/frontend/src/pages/Usuarios.js`

| Característica | Estado actual |
|----------------|---------------|
| Líneas de código | 1,453 |
| Tabs existentes | Usuarios, Roles, Permisos, Proveedores, Estructura |
| Condición tab "Estructura" | `canViewEstructura()` (verifica `SuperAdministrador` o `Administrador`) |
| Patrón de carga | `useCallback` + `useEffect` inicial |
| Patrón de modal | `Dialog` de shadcn/ui |

### 2.2 Endpoints backend existentes

| Endpoint | Método | Descripción | Estado |
|----------|--------|-------------|--------|
| `POST /api/admin/permisos/asignar` | POST | Asignar/retirar permiso directo | ✅ FASE 4 |
| `POST /api/admin/roles/asignar` | POST | Asignar/retirar rol | ✅ FASE 6 |
| `GET /api/users` | GET | Lista usuarios con `sec_permisos`, `sec_rol`, `sec_roles` | ✅ Existente |

### 2.3 Endpoints faltantes para UI

| Endpoint propuesto | Método | Descripción | Necesidad |
|--------------------|--------|-------------|-----------|
| `GET /api/admin/sec/bitacora/{email}` | GET | Auditoría RBAC de un usuario | OPCIONAL |
| `GET /api/admin/sec/roles-catalogo` | GET | Lista roles piloto disponibles | OPCIONAL |

### 2.4 Mejor punto de entrada

**Recomendación:** Agregar **sección colapsable** dentro de la tarjeta de usuario existente (NO crear nuevo tab).

**Justificación:**
1. Mínimo impacto en estructura actual
2. Contexto inmediato del usuario seleccionado
3. No requiere navegación adicional
4. Reutiliza patrones de UI existentes

---

## 3. OPCIÓN A: SECCIÓN COLAPSABLE EN TARJETA DE USUARIO (MENOR RIESGO)

### 3.1 Descripción

Agregar un acordeón/sección expandible dentro de cada tarjeta de usuario en el tab "Usuarios", visible **solo para SuperAdministrador** y **solo para usuarios que NO sean SuperAdministrador**.

### 3.2 Wireframe conceptual

```
┌─────────────────────────────────────────────────────────────┐
│  👤 Juan Pérez                                              │
│  juan@edarsa.com                                            │
│  ┌─────────────┐                                            │
│  │ Supervisor  │  Estado: Activo                            │
│  └─────────────┘                                            │
│                                                              │
│  [Editar] [Permisos] [Eliminar]                             │
│                                                              │
│  ▼ Seguridad RBAC (Piloto)  ─────────────────────────────   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Permisos directos:                                    │   │
│  │   ☑ SISTEMA_ESTRUCTURA_VER                           │   │
│  │                                                        │   │
│  │ Roles asignados:                                       │   │
│  │   ☐ VISOR_ESTRUCTURA                                  │   │
│  │   ☑ VISOR_SISTEMA                                     │   │
│  │                                                        │   │
│  │ [Ver auditoría RBAC]                                   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Alcance exacto

| Elemento | Implementación |
|----------|----------------|
| **Componente nuevo** | `SeccionRBACPiloto` (inline, ~80 líneas) |
| **Ubicación** | Dentro de `CardContent` de tarjeta de usuario |
| **Condición de visibilidad** | `currentUser.role === 'SuperAdministrador' && user.role !== 'SuperAdministrador'` |
| **Estados locales** | `rbacExpanded`, `rbacLoading`, `rbacSaving` |
| **Datos mostrados** | `user.sec_permisos`, `user.sec_rol`, `user.sec_roles` |

### 3.4 Interacciones

| Acción | Endpoint | Comportamiento |
|--------|----------|----------------|
| Toggle permiso | `POST /api/admin/permisos/asignar` | Checkbox → request → reload users |
| Toggle rol | `POST /api/admin/roles/asignar` | Checkbox → request → reload users |
| Ver auditoría | Nuevo endpoint o modal con bitácora | Opcional |

### 3.5 Archivos a modificar

| Archivo | Cambio | Líneas estimadas |
|---------|--------|------------------|
| `/app/frontend/src/pages/Usuarios.js` | Agregar sección colapsable en tarjeta | +120 líneas |

### 3.6 Endpoints a reutilizar

| Endpoint | Uso |
|----------|-----|
| `POST /api/admin/permisos/asignar` | Ya existe (FASE 4) |
| `POST /api/admin/roles/asignar` | Ya existe (FASE 6) |
| `GET /api/users` | Ya trae `sec_permisos`, `sec_rol`, `sec_roles` |

### 3.7 Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Romper tarjeta usuario | BAJA | MEDIO | Sección independiente, aislada con condicional |
| Llamadas excesivas a API | BAJA | BAJO | Solo al expandir sección, no en carga inicial |
| UI inconsistente | BAJA | BAJO | Usar componentes shadcn existentes |

### 3.8 Rollback

```
TIEMPO: 3 minutos
1. Eliminar JSX de sección RBAC en Usuarios.js (~120 líneas)
2. Eliminar estados relacionados (~5 líneas)
3. Frontend vuelve a estado FASE 6

IMPACTO: CERO en backend, CERO en lógica existente
```

---

## 4. OPCIÓN B: MODAL DEDICADO DESDE TARJETA (RIESGO BAJO)

### 4.1 Descripción

Agregar botón "RBAC" en tarjeta de usuario que abre un modal dedicado para gestionar permisos/roles del piloto.

### 4.2 Wireframe conceptual

```
Tarjeta usuario:
[Editar] [Permisos] [RBAC] [Eliminar]
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  ✕  Seguridad RBAC - Juan Pérez                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  PERMISOS DIRECTOS (sec_permisos)                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ ☑ SISTEMA_ESTRUCTURA_VER   [Quitar]                    │ │
│  └────────────────────────────────────────────────────────┘ │
│  [+ Asignar permiso]                                        │
│                                                              │
│  ROLES ASIGNADOS (sec_roles)                                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ • VISOR_ESTRUCTURA   [Quitar]                          │ │
│  │ • VISOR_SISTEMA      [Quitar]                          │ │
│  └────────────────────────────────────────────────────────┘ │
│  [+ Asignar rol]                                            │
│                                                              │
│  AUDITORÍA RECIENTE                                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 2025-12-20 10:30 ASIGNAR_ROL_MULTIPLE VISOR_SISTEMA OK │ │
│  │ 2025-12-20 10:25 ASIGNAR_PERMISO SISTEMA_ESTRUCTURA OK │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│                                          [Cerrar]           │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Alcance exacto

| Elemento | Implementación |
|----------|----------------|
| **Componente nuevo** | `ModalRBACUsuario` (~150 líneas) |
| **Estado adicional** | `rbacModalOpen`, `rbacUsuarioSeleccionado`, `rbacBitacora` |
| **Endpoint nuevo** | `GET /api/admin/sec/bitacora/{email}` (opcional) |

### 4.4 Archivos a modificar

| Archivo | Cambio | Líneas estimadas |
|---------|--------|------------------|
| `/app/frontend/src/pages/Usuarios.js` | Modal + botón + estados | +180 líneas |
| `/app/backend/server.py` | Endpoint bitácora (opcional) | +40 líneas |

### 4.5 Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Modal interfiere con otros modales | BAJA | BAJO | z-index correcto |
| Complejidad de estado | MEDIA | BAJO | Estados aislados |
| Endpoint nuevo rompe algo | MUY BAJA | BAJO | Endpoint GET aislado |

### 4.6 Rollback

```
TIEMPO: 4 minutos
1. Eliminar modal y estados en Usuarios.js (~180 líneas)
2. Eliminar endpoint bitácora si fue agregado (~40 líneas)
3. Sistema vuelve a estado FASE 6
```

---

## 5. OPCIÓN C: NUEVO TAB "RBAC PILOTO" (RIESGO MEDIO)

### 5.1 Descripción

Crear un nuevo tab "RBAC Piloto" en la página de Usuarios, con vista de tabla que muestre todos los usuarios y su estado RBAC.

### 5.2 Wireframe conceptual

```
[Usuarios] [Roles] [Permisos] [Proveedores] [Estructura] [RBAC Piloto]
                                                              │
                                                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ADMINISTRACIÓN RBAC (PILOTO)                                        │
│  Solo visible para SuperAdministrador                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌───────────────────────────────────────────────────────────────┐   │
│  │ Usuario          │ sec_permisos │ sec_roles │ sec_rol │ Acciones │
│  ├───────────────────────────────────────────────────────────────┤   │
│  │ juan@edarsa.com  │ 1            │ 2         │ VISOR.. │ [Editar] │
│  │ test@edarsa.com  │ 0            │ 1         │ -       │ [Editar] │
│  │ admin@edarsa.com │ 0            │ 0         │ VISOR.. │ [Editar] │
│  └───────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  Whitelist activa:                                                    │
│  • Permiso: SISTEMA_ESTRUCTURA_VER                                   │
│  • Roles: VISOR_ESTRUCTURA, VISOR_SISTEMA                            │
│                                                                       │
│  ⚠️ FASE 7 PILOTO: Solo administra elementos ya aprobados.           │
│     No expande el modelo de seguridad.                               │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.3 Alcance exacto

| Elemento | Implementación |
|----------|----------------|
| **Tab nuevo** | `TabsContent value="rbac-piloto"` |
| **Componente nuevo** | `TabRBACPiloto` (~250 líneas) |
| **Vista** | Tabla con todos los usuarios y su estado RBAC |
| **Condición visibilidad** | `currentUser.role === 'SuperAdministrador'` |

### 5.4 Archivos a modificar

| Archivo | Cambio | Líneas estimadas |
|---------|--------|------------------|
| `/app/frontend/src/pages/Usuarios.js` | Tab + componente + estados | +280 líneas |

### 5.5 Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Confusión con tab "Roles" existente | MEDIA | BAJO | Nombre claro "RBAC Piloto" |
| Sobrecarga de tabs | MEDIA | BAJO | Solo visible para SuperAdmin |
| Complejidad de mantenimiento | MEDIA | MEDIO | Componente autocontenido |

### 5.6 Rollback

```
TIEMPO: 5 minutos
1. Eliminar tab y componente en Usuarios.js (~280 líneas)
2. Sistema vuelve a estado FASE 6
```

---

## 6. RECOMENDACIÓN

### 6.1 Opción recomendada: **OPCIÓN A - Sección Colapsable**

| Criterio | Evaluación |
|----------|------------|
| Mínimo riesgo | ✅ No crea nuevos tabs ni modales complejos |
| Mínimo impacto | ✅ ~120 líneas, aisladas en condicional |
| Contexto inmediato | ✅ Administra RBAC sin salir de la tarjeta del usuario |
| No requiere endpoints nuevos | ✅ Reutiliza 100% endpoints existentes |
| Rollback trivial | ✅ 3 minutos |
| Coherencia UX | ✅ Misma tarjeta, información expandible |

### 6.2 Justificación

1. **Principio de mínimo impacto**: No agrega tabs, modales ni navegación nueva
2. **Contexto**: El administrador ve los datos RBAC en el mismo lugar donde ve los datos generales del usuario
3. **Aislamiento**: La sección solo aparece si se cumplen dos condiciones (SuperAdmin + usuario no-SuperAdmin)
4. **Sin backend nuevo**: Todos los endpoints ya existen y están probados

---

## 7. ALCANCE EXACTO RECOMENDADO (OPCIÓN A)

### 7.1 Visibilidad de la sección

```javascript
// Solo visible si:
// 1. El usuario logueado es SuperAdministrador
// 2. El usuario de la tarjeta NO es SuperAdministrador
const showRBACSection = currentUser?.role === 'SuperAdministrador' && 
                        user.role !== 'SuperAdministrador';
```

### 7.2 Elementos de la sección

```
▼ Seguridad RBAC (Piloto)
├── Permisos directos (sec_permisos)
│   └── ☑/☐ SISTEMA_ESTRUCTURA_VER  [toggle]
│
├── Roles asignados (sec_roles)
│   ├── ☑/☐ VISOR_ESTRUCTURA  [toggle]
│   └── ☑/☐ VISOR_SISTEMA     [toggle]
│
└── Rol único legacy (sec_rol): {valor actual}  [solo lectura]
```

### 7.3 Comportamiento de toggles

| Acción | Request | Respuesta esperada |
|--------|---------|-------------------|
| Marcar permiso | `POST /api/admin/permisos/asignar {accion: "ASIGNAR"}` | `{success: true}` → reload |
| Desmarcar permiso | `POST /api/admin/permisos/asignar {accion: "RETIRAR"}` | `{success: true}` → reload |
| Marcar rol | `POST /api/admin/roles/asignar {accion: "ASIGNAR"}` | `{success: true}` → reload |
| Desmarcar rol | `POST /api/admin/roles/asignar {accion: "RETIRAR"}` | `{success: true}` → reload |

### 7.4 Información de solo lectura

| Campo | Descripción |
|-------|-------------|
| `sec_rol` | Mostrar valor actual (compatibilidad FASE 5), sin opción de editar |

---

## 8. ARCHIVOS A TOCAR

### 8.1 Frontend

| Archivo | Tipo de cambio | Líneas estimadas |
|---------|----------------|------------------|
| `/app/frontend/src/pages/Usuarios.js` | Agregar sección colapsable | +120 líneas |

### 8.2 Backend

| Archivo | Tipo de cambio | Líneas estimadas |
|---------|----------------|------------------|
| Ninguno | - | 0 |

---

## 9. ENDPOINTS A REUTILIZAR O CREAR

### 9.1 Endpoints existentes (reutilizar)

| Endpoint | Estado |
|----------|--------|
| `POST /api/admin/permisos/asignar` | ✅ FASE 4 |
| `POST /api/admin/roles/asignar` | ✅ FASE 6 |
| `GET /api/users` | ✅ Ya trae sec_permisos, sec_rol, sec_roles |

### 9.2 Endpoints nuevos

**Ninguno requerido para OPCIÓN A.**

(Opcional para futuro: endpoint de bitácora por usuario)

---

## 10. RIESGOS Y MITIGACIONES

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|--------|--------------|---------|------------|
| 1 | Romper tarjeta de usuario | BAJA | MEDIO | Sección condicional aislada |
| 2 | Conflicto con permisos legacy | MUY BAJA | BAJO | Solo administra sec_* (piloto) |
| 3 | Toggle lento | BAJA | BAJO | Feedback visual inmediato + reload |
| 4 | Usuario se confunde | BAJA | BAJO | Badge "(Piloto)" + nota explicativa |
| 5 | Regresión en tabs existentes | MUY BAJA | MEDIO | Código aislado, sin modificar tabs |

---

## 11. QUÉ NO SE TOCARÁ

| Elemento | Confirmación |
|----------|--------------|
| `get_current_user()` | ❌ NO SE MODIFICA |
| `Layout.js` | ❌ NO SE MODIFICA |
| Router global | ❌ NO SE MODIFICA |
| Auth global | ❌ NO SE MODIFICA |
| Middleware | ❌ NO SE MODIFICA |
| Tab "Usuarios" (estructura) | ❌ NO SE MODIFICA (solo se agrega contenido dentro de tarjeta) |
| Tab "Roles" | ❌ NO SE MODIFICA |
| Tab "Permisos" | ❌ NO SE MODIFICA |
| Tab "Proveedores" | ❌ NO SE MODIFICA |
| Tab "Estructura" | ❌ NO SE MODIFICA |
| `users.role` | ❌ NO SE MODIFICA |
| `users.rbac_role` | ❌ NO SE MODIFICA |
| Endpoints `POST /api/admin/*` | ❌ NO SE MODIFICAN (solo se consumen) |
| Colecciones MongoDB | ❌ NO SE MODIFICAN |
| Whitelist RBAC | ❌ NO SE EXPANDE |

---

## 12. COMPATIBILIDAD LEGACY

### 12.1 Coexistencia de campos en UI

```
LEGACY (mostrar, no editar)           PILOTO (mostrar y editar)
────────────────────────────          ─────────────────────────
users.role                            users.sec_permisos  ← EDITABLE
users.rbac_role                       users.sec_roles     ← EDITABLE
                                      users.sec_rol       ← SOLO LECTURA
```

### 12.2 Regla de visualización

| Campo | Dónde se muestra | Editable en FASE 7 |
|-------|------------------|-------------------|
| `role` | Badge en tarjeta (ya existe) | NO |
| `rbac_role` | No mostrado actualmente | NO |
| `sec_permisos` | Nueva sección RBAC | SÍ (toggle) |
| `sec_roles` | Nueva sección RBAC | SÍ (toggle) |
| `sec_rol` | Nueva sección RBAC | NO (solo lectura) |

---

## 13. ROLLBACK

### 13.1 Pasos de rollback

```
TIEMPO TOTAL: 3 minutos

1. Abrir /app/frontend/src/pages/Usuarios.js
2. Eliminar sección JSX de "Seguridad RBAC (Piloto)" (~100 líneas)
3. Eliminar estados: rbacExpanded, rbacLoading, rbacSaving (~5 líneas)
4. Eliminar funciones: handleTogglePermiso, handleToggleRol (~15 líneas)
5. Guardar archivo
6. Frontend vuelve automáticamente por hot reload

IMPACTO:
- Backend: CERO cambios (no se tocó)
- Endpoints: Siguen funcionando
- Base de datos: INTACTA
- Usuarios: Sin afectación
```

---

## 14. CHECKLIST DE NO REGRESIÓN

### 14.1 Pre-implementación

| Verificación | Método |
|--------------|--------|
| Login SuperAdmin | curl + screenshot |
| Login Administrador | curl + screenshot |
| Login Usuario normal | curl |
| Tab Usuarios visible | screenshot |
| Tab Roles funciona | screenshot |
| Tab Estructura funciona | screenshot |
| Crear usuario funciona | curl |
| Editar usuario funciona | curl |
| Eliminar usuario funciona | curl |

### 14.2 Post-implementación

| Verificación | Resultado esperado |
|--------------|-------------------|
| Login SuperAdmin | ✅ Funciona |
| Login Administrador | ✅ Funciona |
| Login Usuario | ✅ Funciona |
| Tab Usuarios muestra tarjetas | ✅ Sin cambios visuales para no-SuperAdmin |
| Sección RBAC visible para SuperAdmin | ✅ Solo en usuarios no-SuperAdmin |
| Toggle permiso funciona | ✅ Cambia sec_permisos |
| Toggle rol funciona | ✅ Cambia sec_roles |
| sec_rol se muestra (solo lectura) | ✅ No editable |
| Tabs Roles, Permisos, Proveedores | ✅ Sin cambios |
| Tab Estructura | ✅ Sin cambios |
| Dashboards | ✅ Sin regresión |

---

## 15. EVIDENCIA ESPERADA

1. **Screenshot** de tarjeta de usuario con sección RBAC colapsada
2. **Screenshot** de tarjeta de usuario con sección RBAC expandida
3. **Prueba curl** de toggle permiso → verificar cambio en BD
4. **Prueba curl** de toggle rol → verificar cambio en BD
5. **Screenshot** verificando que usuario no-SuperAdmin NO ve la sección
6. **Screenshot** verificando que SuperAdmin NO ve sección en su propia tarjeta
7. **Verificación** de que endpoints FASE 4 y FASE 6 siguen funcionando

---

## 16. SOLICITUD DE APROBACIÓN

### 16.1 Resumen de lo que se solicita aprobar

| # | Elemento | Descripción |
|---|----------|-------------|
| 1 | Implementar OPCIÓN A | Sección colapsable en tarjeta de usuario |
| 2 | Modificar solo `Usuarios.js` | ~120 líneas nuevas, aisladas |
| 3 | Reutilizar endpoints existentes | Sin cambios en backend |
| 4 | Visibilidad condicional | Solo SuperAdmin + usuario no-SuperAdmin |
| 5 | Elementos administrables | Solo whitelist actual (1 permiso, 2 roles) |

### 16.2 Lo que NO se hará en FASE 7

| Elemento | Confirmación |
|----------|--------------|
| Perfiles predefinidos | ❌ NO |
| Expansión de whitelist | ❌ NO |
| Nuevos permisos | ❌ NO |
| Nuevos roles | ❌ NO |
| CRUD general de seguridad | ❌ NO |
| Migración masiva | ❌ NO |
| Cambios en auth global | ❌ NO |
| Cambios en Layout.js | ❌ NO |
| Cambios en router | ❌ NO |
| Nuevo tab | ❌ NO (OPCIÓN A no lo requiere) |
| Nuevo modal | ❌ NO (OPCIÓN A no lo requiere) |
| Endpoints nuevos | ❌ NO |

### 16.3 Decisión solicitada

**¿Aprueba la ejecución de FASE 7 OPCIÓN A bajo las condiciones descritas?**

- [ ] SÍ, proceder con OPCIÓN A (Sección Colapsable)
- [ ] NO, requiere ajustes (especificar)
- [ ] PREFERIR OPCIÓN B (Modal Dedicado)
- [ ] PREFERIR OPCIÓN C (Nuevo Tab)
- [ ] DIFERIR esta fase

---

**FIN DEL DOCUMENTO DE PROPUESTA FASE 7**

*Esperando aprobación explícita antes de implementar.*
