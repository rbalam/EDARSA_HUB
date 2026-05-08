# FASE 15 - PROPUESTA
## Consolidación Final y Compatibilidad Legacy

**Versión:** 1.0  
**Fecha:** Diciembre 2025  
**Estado:** PROPUESTA PENDIENTE DE APROBACIÓN  
**Autor:** Agente Arquitecto  
**Tipo:** Documentación y Definición de Reglas (SIN IMPLEMENTACIÓN)

---

## 1. RESUMEN EJECUTIVO

Esta propuesta documenta el estado actual de convivencia entre el sistema RBAC nuevo y el sistema legacy, establece reglas definitivas de prioridad, y define qué campos deben considerarse "congelados" vs "activos".

**OBJETIVO DE ESTA FASE:** Documentar, no implementar. Cerrar ambiguedades conceptuales antes de cualquier rollout a módulos operativos.

**LO QUE NO SE HARÁ EN ESTA FASE:**
- NO se modificará código
- NO se aplicará filtrado de alcance a módulos operativos
- NO se migrará ningún campo legacy
- NO se eliminará ninguna funcionalidad existente

---

## 2. DIAGNÓSTICO DEL ESTADO ACTUAL

### 2.1 Colecciones RBAC (Fuentes de Verdad Nuevas)

| Colección | Documentos | Estado |
|-----------|------------|--------|
| `sec_roles` | 5 | OPERATIVO - Define roles RBAC con permisos |
| `sec_perfiles` | 5 | OPERATIVO - Atajos de asignación de roles |
| `sec_bitacora_admin` | 54+ | OPERATIVO - Auditoría de operaciones RBAC |

### 2.2 Campos RBAC en Usuarios

| Campo | Propósito | Estado Actual |
|-------|-----------|---------------|
| `sec_permisos` | Permisos directos granulares | OPERATIVO (Fase 4) |
| `sec_rol` | Rol único (compatibilidad) | OPERATIVO (Fase 5) |
| `sec_roles` | Array de múltiples roles | OPERATIVO - FUENTE DE VERDAD (Fase 6) |
| `sec_perfil` | Perfil predefinido | METADATO (Fase 13) |
| `sec_roles_alcance` | Alcance por rol | METADATO (Fase 14) - NO FILTRA AÚN |

### 2.3 Campos Legacy en Usuarios

| Campo | Propósito | Estado Actual |
|-------|-----------|---------------|
| `role` | Rol principal legacy | ACTIVO - Usado en `_can_manage_user()` y fallbacks |
| `rbac_role` | (No encontrado en uso activo) | INACTIVO/OBSOLETO |
| `allowed_servers` | Servidores permitidos | ACTIVO - Usado en módulos operativos |
| `allowed_sucursales` | Sucursales por servidor | ACTIVO - Usado en módulos operativos |
| `allowed_warehouses` | Almacenes por servidor | ACTIVO - Usado en módulos operativos |
| `sucursales` | (Modelo antiguo) | POSIBLEMENTE OBSOLETO |

### 2.4 Usuario SuperAdministrador Actual

```
Email: ricardo@edarsa.com.mx
role: SuperAdministrador
sec_permisos: []
sec_roles: []
sec_perfil: None
sec_roles_alcance: {}
allowed_servers: []
```

**OBSERVACIÓN CRÍTICA:** El SuperAdministrador opera exclusivamente vía campo legacy `role`. No tiene campos RBAC asignados porque la función `verificar_permiso_rbac()` en `rbac_helper.py` siempre retorna `True` para `role == 'SuperAdministrador'` (Capa 4).

---

## 3. ESTADO ACTUAL CONSOLIDADO DEL RBAC

### 3.1 Resolución de Permisos (rbac_helper.py)

La función `verificar_permiso_rbac()` resuelve permisos en 4 capas ordenadas:

```
CAPA 1: sec_permisos (array) → Permisos directos
CAPA 2: sec_roles (array) → Permisos heredados de roles
CAPA 3: sec_rol (string) → Compatibilidad con rol único
CAPA 4: role == 'SuperAdministrador' → Acceso total
```

**WHITELIST ACTUAL (NO EXPANDIR SIN AUTORIZACIÓN):**
- Permisos: `SISTEMA_ESTRUCTURA_VER`, `SISTEMA_USUARIOS_VER`, `SISTEMA_USUARIOS_CREAR`, `SISTEMA_USUARIOS_EDITAR`, `SISTEMA_USUARIOS_ELIMINAR`, `SISTEMA_ROLES_VER`, `SISTEMA_ROLES_CREAR`, `SISTEMA_ROLES_EDITAR`, `SISTEMA_ROLES_ELIMINAR`
- Roles: `VISOR_ESTRUCTURA`, `VISOR_SISTEMA`, `VISOR_ADMIN`, `ADMIN_USUARIOS`, `GESTOR_SISTEMA`

### 3.2 Endpoints Protegidos con RBAC

| Endpoint | Permiso RBAC | Fallback Legacy |
|----------|--------------|-----------------|
| `GET /api/users` | SISTEMA_USUARIOS_VER | role_level >= 3 |
| `PUT /api/users/{id}` | SISTEMA_USUARIOS_EDITAR | role_level >= 3 |
| `DELETE /api/users/{id}` | SISTEMA_USUARIOS_ELIMINAR | role_level >= 3 |
| `POST /api/users` | SISTEMA_USUARIOS_CREAR | role_level >= 3 |
| `GET /api/roles` | SISTEMA_ROLES_VER | role_level >= 3 |
| `POST /api/roles` | SISTEMA_ROLES_CREAR | role_level >= 3 |
| `PUT /api/roles/{id}` | SISTEMA_ROLES_EDITAR | role_level >= 3 |
| `DELETE /api/roles/{id}` | SISTEMA_ROLES_ELIMINAR | role_level >= 3 |

### 3.3 Jerarquía de Roles Legacy (ROLE_HIERARCHY)

```python
ROLE_HIERARCHY = {
    'Usuario': 1,
    'Supervisor': 2,
    'Administrador': 3,
    'SuperAdministrador': 100
}
```

**REGLA INMODIFICABLE:** `_can_manage_user()` impide que cualquier usuario modifique a un SuperAdministrador excepto otro SuperAdministrador.

---

## 4. ESTADO ACTUAL CONSOLIDADO DEL SISTEMA LEGACY

### 4.1 Campos Legacy que SIGUEN ACTIVOS

| Campo | Dónde se usa | Por qué sigue activo |
|-------|--------------|----------------------|
| `role` | `auth/service.py`, `server.py`, `_can_manage_user()`, `_get_role_level()`, Login token | Define jerarquía administrativa. SuperAdministrador depende de esto. |
| `allowed_servers` | Módulos operativos (Comercial, Compras, Inventarios, etc.) | Filtrado real de datos por servidor |
| `allowed_sucursales` | Módulos operativos | Filtrado real de datos por sucursal |
| `allowed_warehouses` | Módulos operativos | Filtrado real de datos por almacén |

### 4.2 Campos Legacy POSIBLEMENTE OBSOLETOS

| Campo | Evidencia | Recomendación |
|-------|-----------|---------------|
| `rbac_role` | No encontrado en código activo | CANDIDATO A DEPRECACIÓN |
| `sucursales` (array) | Posiblemente reemplazado por `allowed_sucursales` | REQUIERE VERIFICACIÓN |

### 4.3 Colecciones Legacy

| Colección | Estado |
|-----------|--------|
| `roles` | ACTIVA - Catálogo de roles legacy |
| `rbac_roles` | REQUIERE VERIFICACIÓN - Posible duplicado |

---

## 5. MATRIZ DE CONVIVENCIA RBAC vs LEGACY

### 5.1 Decisiones de Autorización por Área

| Área | Sistema Primario | Sistema Secundario | Notas |
|------|------------------|-------------------|-------|
| **Gestión de Usuarios** | RBAC (`verificar_permiso_rbac`) | Legacy (`role_level >= 3`) | Fallback activo |
| **Gestión de Roles** | RBAC | Legacy | Fallback activo |
| **Bitácora RBAC** | RBAC | - | Solo SuperAdmin UI |
| **Filtrado de Datos Operativos** | Legacy (`allowed_*`) | - | RBAC no implementado aún |
| **Jerarquía Administrativa** | Legacy (`ROLE_HIERARCHY`) | - | `_can_manage_user()` |
| **Token JWT** | Legacy (`role`) | - | Se genera con `role` legacy |

### 5.2 Regla de Prioridad Actual (Implementada)

```
PARA VERIFICACIÓN DE PERMISOS ADMINISTRATIVOS:
1. Verificar RBAC (sec_permisos → sec_roles → sec_rol → SuperAdmin)
2. SI RBAC deniega → Verificar fallback legacy (role_level >= 3)
3. SI ambos deniegan → HTTP 403

PARA FILTRADO DE DATOS OPERATIVOS:
1. Usar exclusivamente allowed_servers/allowed_sucursales/allowed_warehouses
2. sec_roles_alcance NO SE APLICA (es solo metadato)
```

---

## 6. REGLAS DEFINITIVAS DE PRIORIDAD PROPUESTAS

### 6.1 Prioridad de Campos para Resolución de Permisos Administrativos

```
ORDEN DE EVALUACIÓN (PROPUESTA PARA CONSOLIDACIÓN):
1. role == 'SuperAdministrador' → ACCESO TOTAL (inmutable)
2. sec_permisos (array) → Permisos directos explícitos
3. sec_roles (array) → Permisos heredados de roles RBAC
4. sec_rol (string) → Compatibilidad (CONGELAR después de consolidación)
5. Fallback: role_level >= 3 (Administrador+) → Permitir (MANTENER TEMPORAL)
```

### 6.2 Prioridad de Campos para Filtrado de Datos Operativos

```
ESTADO ACTUAL (SIN CAMBIOS EN FASE 15):
- allowed_servers → Servidores autorizados
- allowed_sucursales → Sucursales por servidor
- allowed_warehouses → Almacenes por servidor

ESTADO FUTURO (FASES POSTERIORES):
- sec_roles_alcance reemplazará a allowed_* gradualmente
- Requiere implementación por módulo individual
```

---

## 7. CAMPOS QUE DEBEN QUEDAR CONGELADOS FUNCIONALMENTE

### 7.1 Campos a CONGELAR (no eliminar, no expandir)

| Campo | Razón | Acción Propuesta |
|-------|-------|------------------|
| `sec_rol` (string) | Redundante con `sec_roles` (array) | CONGELAR - No asignar nuevos valores |
| `rbac_role` | No se usa activamente | DEPRECAR - Marcar para eliminación futura |

### 7.2 Campos que NO DEBEN TOCARSE TODAVÍA

| Campo | Razón |
|-------|-------|
| `role` | SuperAdministrador depende de esto. Sin migración hasta que RBAC tenga rol equivalente |
| `allowed_servers` | Filtrado real de módulos operativos |
| `allowed_sucursales` | Filtrado real de módulos operativos |
| `allowed_warehouses` | Filtrado real de módulos operativos |

---

## 8. COMPONENTES RBAC QUE YA SON FUENTE DE VERDAD

| Componente | Fuente de Verdad Para | Desde Fase |
|------------|----------------------|------------|
| `sec_roles` (array) | Roles RBAC asignados al usuario | FASE 6 |
| `sec_permisos` (array) | Permisos directos del usuario | FASE 4 |
| `sec_roles` (colección) | Definición de roles con permisos | FASE 5 |
| `sec_perfiles` (colección) | Atajos de asignación de roles | FASE 13 |
| `sec_bitacora_admin` | Auditoría de operaciones RBAC | FASE 12 |

---

## 9. COMPONENTES QUE SIGUEN SIENDO SOLO COMPATIBILIDAD/METADATO

| Componente | Propósito Actual | Estado |
|------------|------------------|--------|
| `sec_rol` (string) | Compatibilidad FASE 5 | CONGELAR |
| `sec_perfil` (string) | Metadato de perfil | METADATO |
| `sec_roles_alcance` (dict) | Metadato de alcance | METADATO - NO FILTRA |

---

## 10. RIESGOS ACTUALES DE CONVIVENCIA AMBIGUA

### 10.1 Riesgos Identificados

| # | Riesgo | Severidad | Mitigación Actual |
|---|--------|-----------|-------------------|
| R1 | SuperAdmin sin campos RBAC asignados | BAJO | `verificar_permiso_rbac()` tiene fallback para `role == 'SuperAdministrador'` |
| R2 | Doble fuente de verdad para filtrado (allowed_* vs sec_roles_alcance) | MEDIO | `sec_roles_alcance` es solo metadato, no filtra |
| R3 | Fallback legacy puede permitir acceso a quien no tiene RBAC | MEDIO | Intencional para compatibilidad. Documentado. |
| R4 | `sec_rol` y `sec_roles` pueden tener valores inconsistentes | BAJO | `sec_roles` es fuente de verdad. `sec_rol` ignorar para nuevos flujos. |

### 10.2 Riesgos NO Presentes

- NO hay riesgo de que un usuario sin RBAC ni legacy acceda a endpoints protegidos (doble verificación)
- NO hay riesgo de modificar SuperAdministrador por usuarios no autorizados (`_can_manage_user` protege)

---

## 11. RECOMENDACIÓN EXACTA DE CONSOLIDACIÓN

### 11.1 Acciones Recomendadas para FASE 15 (DOCUMENTACIÓN SOLAMENTE)

| # | Acción | Tipo |
|---|--------|------|
| A1 | Crear este documento como referencia oficial | DOCUMENTACIÓN |
| A2 | Agregar comentarios en `rbac_helper.py` documentando las 4 capas | DOCUMENTACIÓN |
| A3 | Agregar comentarios en `auth/service.py` documentando el patrón RBAC+Fallback | DOCUMENTACIÓN |
| A4 | Crear diagrama de flujo de resolución de permisos | DOCUMENTACIÓN |
| A5 | **Establecer regla: todo módulo nuevo nace con RBAC integrado** | POLÍTICA |

### 11.2 Acciones que NO se ejecutan en FASE 15

| # | Acción | Por qué NO |
|---|--------|-----------|
| B1 | Eliminar campo `rbac_role` | Requiere verificación de uso en producción |
| B2 | Congelar `sec_rol` en código | Requiere fase de implementación separada |
| B3 | Aplicar `sec_roles_alcance` en filtrado | Requiere rollout por módulo individual |
| B4 | Migrar `allowed_*` a `sec_roles_alcance` | Requiere fase de migración separada |
| B5 | Modificar `get_current_user()` | Alto riesgo, archivo transversal |

---

## 12. LO QUE NO DEBE IMPLEMENTARSE TODAVÍA

### 12.1 Implementaciones Prohibidas en FASE 15

1. **Filtrado real por `sec_roles_alcance`** - Solo metadato hasta fases posteriores
2. **Modificación de `rbac_helper.py`** - Congelado desde FASE 9
3. **Modificación de `get_current_user()`** - Archivo transversal crítico
4. **Eliminación de campos legacy** - Sin plan de migración aprobado
5. **Expansión de PERMISOS_WHITELIST** - Solo con autorización explícita
6. **Cambios en ROLE_HIERARCHY** - Regla de negocio crítica

### 12.2 Implementaciones que Requieren Fases Futuras Separadas

| Implementación | Fase Sugerida | Dependencias |
|----------------|---------------|--------------|
| Aplicar alcance en GET /api/users | FASE 16 | Fase 15 aprobada |
| Aplicar alcance en módulo Comercial | FASE 17+ | Fase 16 exitosa |
| Migrar SuperAdmin a RBAC puro | FASE 20+ | Todas las anteriores |
| Deprecar `allowed_*` | FASE 25+ | Todos los módulos migrados |

---

## 13. PLAN DE ROLLBACK CONCEPTUAL

### 13.1 Si en el futuro se consolida y algo falla

```
ROLLBACK DE FILTRADO POR ALCANCE (Fases 16+):
1. Revertir queries de módulos a usar allowed_* en lugar de sec_roles_alcance
2. Los datos de sec_roles_alcance permanecen como metadato inerte
3. Tiempo estimado: 15 minutos por módulo

ROLLBACK DE PERFILES (Fase 13):
1. Eliminar selector de perfil en UI
2. Los usuarios conservan sec_roles asignados
3. Tiempo estimado: 7 minutos

ROLLBACK DE RESOLUCIÓN RBAC (Fases 9-11):
1. Eliminar llamadas a verificar_permiso_rbac() en service.py
2. Dejar solo verificación legacy (role_level)
3. Tiempo estimado: 10 minutos
```

---

## 14. CHECKLIST DE NO REGRESIÓN PARA FASE 15 EJECUTABLE

### 14.1 Verificaciones Obligatorias (si se implementara código)

| # | Verificación | Método |
|---|--------------|--------|
| 1 | Login funciona | curl + credenciales |
| 2 | SuperAdmin tiene acceso total | curl endpoints protegidos |
| 3 | Usuario sin permisos obtiene 403 | curl con token limitado |
| 4 | GET /api/users funciona | curl |
| 5 | GET /api/roles funciona | curl |
| 6 | Bitácora registra operaciones | curl GET /api/admin/bitacora |
| 7 | Dashboard Comercial funciona | Screenshot |
| 8 | Módulos operativos no afectados | Screenshot |

### 14.2 Verificaciones de Documentación (Fase 15 actual)

| # | Verificación |
|---|--------------|
| 1 | Documento FASE15_PROPUESTA.md creado |
| 2 | Matriz de convivencia completa |
| 3 | Reglas de prioridad definidas |
| 4 | Riesgos documentados |
| 5 | Plan de rollback conceptual definido |

---

## 15. RESPUESTAS A PREGUNTAS OBLIGATORIAS

### 15.1 ¿Cuál es hoy la prioridad real entre sec_permisos, sec_roles, sec_rol, SuperAdmin, fallback legacy administrativo?

```
PRIORIDAD ACTUAL (Código en rbac_helper.py + auth/service.py):

1. role == 'SuperAdministrador' → ACCESO TOTAL (Capa 4 de rbac_helper)
2. sec_permisos (array) → Si contiene el permiso → ACCESO (Capa 1)
3. sec_roles (array) → Si algún rol tiene el permiso → ACCESO (Capa 2)
4. sec_rol (string) → Si el rol tiene el permiso → ACCESO (Capa 3)
5. Fallback legacy: role_level >= 3 → ACCESO (en service.py, después de RBAC)

SI NINGUNO APLICA → HTTP 403 DENEGADO
```

### 15.2 ¿Qué campos legacy siguen afectando decisiones reales?

| Campo | Afecta Decisiones Reales | Dónde |
|-------|--------------------------|-------|
| `role` | SÍ | Jerarquía (`_can_manage_user`), SuperAdmin check, Token JWT |
| `allowed_servers` | SÍ | Filtrado en módulos operativos |
| `allowed_sucursales` | SÍ | Filtrado en módulos operativos |
| `allowed_warehouses` | SÍ | Filtrado en módulos operativos |
| `rbac_role` | NO | No encontrado en uso activo |
| `sucursales` | POSIBLEMENTE | Requiere verificación |

### 15.3 ¿Qué campos nuevos ya son operativos y cuáles son solo metadato?

| Campo | Operativo | Metadato |
|-------|-----------|----------|
| `sec_permisos` | ✅ SÍ | - |
| `sec_roles` | ✅ SÍ | - |
| `sec_rol` | ✅ SÍ (compat) | - |
| `sec_perfil` | - | ✅ SÍ |
| `sec_roles_alcance` | - | ✅ SÍ |

### 15.4 ¿Dónde existe riesgo de doble fuente de verdad?

| Área | Fuentes | Riesgo | Mitigación |
|------|---------|--------|------------|
| Filtrado de datos | `allowed_*` vs `sec_roles_alcance` | MEDIO | `sec_roles_alcance` es solo metadato |
| Roles asignados | `sec_roles` vs `sec_rol` | BAJO | `sec_roles` es la fuente de verdad |
| Permisos admin | RBAC vs role_level | BAJO | Fallback intencional documentado |

### 15.5 ¿Qué piezas deben quedar congeladas y por qué?

| Pieza | Razón para Congelar |
|-------|---------------------|
| `sec_rol` (string) | Redundante con `sec_roles` (array). No asignar nuevos valores. |
| `rbac_helper.py` | Estabilidad del sistema. Solo modificar con autorización explícita. |
| `ROLE_HIERARCHY` | Regla de negocio crítica. SuperAdministrador = 100 es inmutable. |
| `_can_manage_user()` | Protección de SuperAdministrador. No modificar. |

### 15.6 ¿Qué piezas no deben migrarse todavía y por qué?

| Pieza | Razón para NO Migrar |
|-------|---------------------|
| `role` | SuperAdministrador depende de este campo |
| `allowed_*` | Módulos operativos dependen de estos campos para filtrado real |
| Token JWT | Incluye `role` legacy. Cambiar afectaría todas las sesiones |

---

## 16. SOLICITUD DE APROBACIÓN

### Alcance Solicitado

Esta propuesta solicita aprobación para:

1. ✅ Adoptar este documento como referencia oficial de convivencia RBAC/Legacy
2. ✅ Considerar `sec_rol` (string) como CONGELADO conceptualmente
3. ✅ Considerar `rbac_role` como CANDIDATO A DEPRECACIÓN
4. ✅ Mantener `sec_roles_alcance` como METADATO hasta fases futuras
5. ✅ NO implementar ningún cambio de código en FASE 15
6. ✅ **Establecer como regla obligatoria: todo módulo nuevo debe incluir su paquete RBAC completo**

### Entregables de FASE 15

| Entregable | Formato |
|------------|---------|
| Este documento (FASE15_PROPUESTA.md) | Markdown |
| Evidencia de aprobación | Comentario del usuario |

### Siguiente Fase Sugerida

**FASE 16:** Aplicación de `sec_roles_alcance` en filtrado de `GET /api/users` (primer módulo piloto de alcance real)

---

## 17. REGLA ARQUITECTÓNICA OBLIGATORIA: RBAC NATIVO EN TODO DESARROLLO NUEVO

### 17.1 Política de Desarrollo con RBAC Integrado

A partir de la consolidación de FASE 15, **ningún módulo, submódulo, tab, pantalla, endpoint o proceso nuevo** puede considerarse terminado sin entregar su paquete RBAC completo.

### 17.2 Checklist Obligatorio para Todo Desarrollo Nuevo

| # | Paso | Entregable |
|---|------|------------|
| 1 | Definir permisos nuevos | Códigos de permiso (ej: `MODULO_X_VER`, `MODULO_X_EDITAR`) |
| 2 | Definir roles y perfiles que lo usan | Actualización de `sec_roles` y `sec_perfiles` |
| 3 | Definir alcance organizacional aplicable | Tipo: GLOBAL / EMPRESA / UNIDAD / SUCURSAL / ALMACÉN |
| 4 | Proteger backend | Llamadas a `verificar_permiso_rbac()` en endpoints |
| 5 | Reflejar permisos en frontend | Condicionales de visibilidad basados en permisos |
| 6 | Registrar auditoría | Eventos en `sec_bitacora_admin` |
| 7 | Validar acceso/denegación | Pruebas con usuarios autorizados y no autorizados |
| 8 | Documentar matriz RBAC | Actualización de matriz de permisos |

### 17.3 Entregables Obligatorios por Módulo Nuevo

```
PAQUETE RBAC MÍNIMO:
├── Catálogo de permisos nuevos (códigos + descripción)
├── Endpoints protegidos (lista con método HTTP)
├── Roles/perfiles actualizados (qué roles tienen qué permisos)
├── Alcance organizacional definido (matriz de alcance)
├── Evidencia de pruebas (curl/screenshots)
└── Verificación de no regresión (checklist ejecutado)
```

### 17.4 Proceso Formal de Actualización RBAC

```
PROHIBIDO:
- Actualizar RBAC "a mano" sin documentación
- Agregar permisos de forma improvisada
- Modificar roles sin registro en bitácora
- Crear endpoints sin protección RBAC

OBLIGATORIO:
- Proceso formal centralizado en EDARSA HUB
- Backend como autoridad única de permisos
- Documentación obligatoria en cada cambio
- Aprobación antes de implementación
```

### 17.5 Flujo de Desarrollo con RBAC Integrado

```
┌─────────────────────────────────────────────────────────────┐
│              DESARROLLO DE MÓDULO NUEVO                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ PASO 1: PROPUESTA DE MÓDULO                                 │
│ - Incluir sección "RBAC REQUERIDO"                          │
│ - Definir permisos, roles, alcance                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ PASO 2: APROBACIÓN                                          │
│ - Revisión de propuesta RBAC                                │
│ - Confirmación de permisos y alcance                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ PASO 3: IMPLEMENTACIÓN                                      │
│ - Backend: endpoints + verificar_permiso_rbac()             │
│ - Frontend: condicionales de visibilidad                    │
│ - MongoDB: permisos en sec_roles, actualizar sec_perfiles   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ PASO 4: VALIDACIÓN                                          │
│ - Test con SuperAdmin (acceso total)                        │
│ - Test con usuario autorizado (acceso)                      │
│ - Test con usuario NO autorizado (HTTP 403)                 │
│ - Verificar auditoría registrada                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ PASO 5: DOCUMENTACIÓN                                       │
│ - Matriz RBAC actualizada                                   │
│ - Evidencia de pruebas                                      │
│ - No regresión verificada                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              MÓDULO COMPLETADO ✅                            │
│        (Con paquete RBAC integrado)                         │
└─────────────────────────────────────────────────────────────┘
```

### 17.6 Ejemplo de Paquete RBAC para Módulo Nuevo

```markdown
## RBAC - Módulo [NOMBRE]

### Permisos Nuevos
| Código | Descripción |
|--------|-------------|
| MODULO_X_VER | Ver datos del módulo X |
| MODULO_X_CREAR | Crear registros en módulo X |
| MODULO_X_EDITAR | Editar registros en módulo X |
| MODULO_X_ELIMINAR | Eliminar registros en módulo X |

### Alcance Organizacional
| Permiso | Alcance Aplicable |
|---------|-------------------|
| MODULO_X_VER | SUCURSAL |
| MODULO_X_CREAR | UNIDAD |
| MODULO_X_EDITAR | SUCURSAL |
| MODULO_X_ELIMINAR | EMPRESA |

### Roles que Incluyen Permisos
| Rol | Permisos |
|-----|----------|
| GESTOR_MODULO_X | Todos |
| VISOR_MODULO_X | Solo VER |

### Perfiles Actualizados
| Perfil | Roles Agregados |
|--------|-----------------|
| PERFIL_OPERADOR | VISOR_MODULO_X |

### Endpoints Protegidos
| Endpoint | Método | Permiso Requerido |
|----------|--------|-------------------|
| /api/modulo-x | GET | MODULO_X_VER |
| /api/modulo-x | POST | MODULO_X_CREAR |
| /api/modulo-x/{id} | PUT | MODULO_X_EDITAR |
| /api/modulo-x/{id} | DELETE | MODULO_X_ELIMINAR |

### Evidencia de Pruebas
- [ ] SuperAdmin accede a todos los endpoints
- [ ] Usuario con VISOR_MODULO_X solo puede GET
- [ ] Usuario sin permisos obtiene 403
- [ ] Auditoría registra operaciones CRUD
```

### 17.7 Consecuencia de Incumplimiento

**Un módulo que no incluya su paquete RBAC completo NO se considera terminado y NO debe desplegarse a producción.**

---

**FIN DE LA PROPUESTA FASE 15**

---

## APÉNDICE A: DIAGRAMA DE FLUJO DE RESOLUCIÓN DE PERMISOS

```
┌─────────────────────────────────────────────────────────────┐
│                    SOLICITUD DE ACCESO                       │
│              (Endpoint protegido RBAC)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              verificar_permiso_rbac(user, permiso)          │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
    ┌───────────┐       ┌───────────┐       ┌───────────┐
    │ CAPA 1:   │  NO   │ CAPA 2:   │  NO   │ CAPA 3:   │
    │sec_permisos│──────▶│ sec_roles │──────▶│ sec_rol   │
    │ contiene? │       │tiene permiso│      │tiene perm?│
    └───────────┘       └───────────┘       └───────────┘
          │ SÍ                │ SÍ                │ SÍ
          │                   │                   │
          ▼                   ▼                   ▼
    ┌───────────────────────────────────────────────────┐
    │                   ACCESO PERMITIDO                │
    └───────────────────────────────────────────────────┘
                              │ NO
                              ▼
                    ┌───────────────┐
                    │ CAPA 4:       │
                    │ role ==       │
                    │SuperAdministrador│
                    └───────────────┘
                         │ SÍ    │ NO
                         ▼       ▼
                    ┌────────┐ ┌────────────────────────┐
                    │PERMITIDO│ │RBAC DENIEGA           │
                    └────────┘ │Ir a fallback legacy... │
                               └────────────────────────┘
                                          │
                                          ▼
                    ┌─────────────────────────────────────┐
                    │    FALLBACK LEGACY (service.py)     │
                    │    role_level >= 3 (Administrador+) │
                    └─────────────────────────────────────┘
                              │ SÍ        │ NO
                              ▼           ▼
                         ┌────────┐  ┌────────┐
                         │PERMITIDO│  │HTTP 403│
                         └────────┘  └────────┘
```

---

## APÉNDICE B: MUESTRA DE DATOS REALES (DIAGNÓSTICO)

### Usuario SuperAdministrador
```json
{
  "email": "ricardo@edarsa.com.mx",
  "role": "SuperAdministrador",
  "sec_permisos": [],
  "sec_roles": [],
  "sec_rol": null,
  "sec_perfil": null,
  "sec_roles_alcance": {},
  "allowed_servers": []
}
```

### Usuario con RBAC + Legacy (test@edarsa.com)
```json
{
  "email": "test@edarsa.com",
  "role": "Supervisor",
  "sec_permisos": ["SISTEMA_ESTRUCTURA_VER", "SISTEMA_ROLES_VER", "SISTEMA_USUARIOS_VER", "SISTEMA_USUARIOS_EDITAR"],
  "sec_roles": ["VISOR_ADMIN"],
  "sec_rol": "VISOR_SISTEMA",
  "sec_perfil": "PERFIL_VISOR_COMPLETO",
  "sec_roles_alcance": {},
  "allowed_servers": ["1b230a06-...", "6d053c22-...", "a5ff0e25-...", "a5547321-..."]
}
```

### Roles RBAC Definidos
```
VISOR_ESTRUCTURA → permisos: ['SISTEMA_ESTRUCTURA_VER']
VISOR_SISTEMA → permisos: ['SISTEMA_USUARIOS_VER']
VISOR_ADMIN → permisos: ['SISTEMA_ESTRUCTURA_VER', 'SISTEMA_USUARIOS_VER', 'SISTEMA_ROLES_VER']
ADMIN_USUARIOS → permisos: ['SISTEMA_USUARIOS_VER', 'SISTEMA_USUARIOS_EDITAR', 'SISTEMA_USUARIOS_ELIMINAR']
GESTOR_SISTEMA → permisos: ['SISTEMA_USUARIOS_VER', 'SISTEMA_USUARIOS_CREAR', 'SISTEMA_USUARIOS_EDITAR', ...]
```

### Perfiles Predefinidos
```
PERFIL_VISOR_BASICO → roles: ['VISOR_ESTRUCTURA']
PERFIL_VISOR_SISTEMA → roles: ['VISOR_ESTRUCTURA', 'VISOR_SISTEMA']
PERFIL_VISOR_COMPLETO → roles: ['VISOR_ADMIN']
PERFIL_ADMIN_USUARIOS → roles: ['VISOR_ADMIN', 'ADMIN_USUARIOS']
PERFIL_GESTOR_SISTEMA → roles: ['GESTOR_SISTEMA']
```
