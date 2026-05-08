# FASE 8 - PROPUESTA: EXPANSIÓN CONTROLADA DE WHITELIST
## Arquitectura de Seguridad EDARSA HUB

**Versión:** 1.0  
**Fecha:** Diciembre 2025  
**Estado:** PENDIENTE APROBACIÓN  
**Requisitos previos:** FASE 1 ✅ | FASE 2 ✅ | FASE 3 ✅ | FASE 4 ✅ | FASE 5 ✅ | FASE 6 ✅ | FASE 7 ✅

---

## 1. RESUMEN EJECUTIVO

Este documento propone la **expansión mínima y controlada** de la whitelist del piloto RBAC, agregando un número muy pequeño de nuevos permisos y roles que permitan validar el crecimiento ordenado del sistema sin convertirlo todavía en un RBAC general.

### Estado actual del piloto:

| Elemento | Valor actual |
|----------|--------------|
| Permisos en whitelist | 1 (`SISTEMA_ESTRUCTURA_VER`) |
| Roles en whitelist | 2 (`VISOR_ESTRUCTURA`, `VISOR_SISTEMA`) |
| Permisos en catálogo | 90 |
| Endpoints protegidos | 1 (`GET /api/sistema/estructura-organizacional`) |
| UI de administración | ✅ Funcional (FASE 7) |

### Objetivo FASE 8:

Expandir la whitelist de forma **mínima** para validar:
1. Que el sistema soporta **múltiples permisos** en whitelist
2. Que el sistema soporta **roles con múltiples permisos**
3. Que la **resolución de 4 capas** funciona correctamente con más elementos
4. Que la **UI de FASE 7** escala sin cambios

---

## 2. DIAGNÓSTICO DEL MEJOR PUNTO DE EXPANSIÓN

### 2.1 Criterios de selección

| Criterio | Peso | Descripción |
|----------|------|-------------|
| Bajo riesgo | CRÍTICO | No tocar módulos productivos sensibles |
| Ya existente en catálogo | ALTO | Permiso ya definido en `sec_permisos_catalogo` |
| Solo lectura | ALTO | Preferir permisos de visualización |
| Validación simple | ALTO | Endpoint fácil de proteger y probar |
| No requiere cambios en UI | ALTO | Evitar rediseño de pantallas |

### 2.2 Análisis de candidatos

| Permiso candidato | Módulo | Tipo | Riesgo | Endpoint existente |
|-------------------|--------|------|--------|-------------------|
| `SISTEMA_USUARIOS_VER` | Sistema | VER | BAJO | GET /api/users |
| `SISTEMA_ROLES_VER` | Sistema | VER | BAJO | GET /api/roles |
| `COMERCIAL_TABLERO_VER` | Comercial | VER | MEDIO | GET /comercial/tablero-ejecutivo |
| `SISTEMA_ALERTAS_VER` | Sistema | VER | BAJO | GET /api/centro-control/alertas |
| `REPORTES_VER` | Reportes | VER | BAJO | Varios |

### 2.3 Recomendación de punto de expansión

**Módulo Sistema** (ya probado en FASE 7 con `SISTEMA_USUARIOS_VER` en rol `VISOR_SISTEMA`)

**Justificación:**
1. El permiso `SISTEMA_USUARIOS_VER` ya está asignado al rol `VISOR_SISTEMA`
2. La infraestructura ya existe
3. El riesgo es mínimo porque es solo lectura
4. No requiere cambios en UI operativa
5. Permite validar la expansión de whitelist en un entorno controlado

---

## 3. OPCIÓN A: EXPANSIÓN MÍNIMA - 2 PERMISOS NUEVOS (MENOR RIESGO)

### 3.1 Descripción

Agregar **solo 2 permisos nuevos** a la whitelist, todos de tipo "VER" (solo lectura), del módulo Sistema que ya está probado.

### 3.2 Permisos propuestos

| Permiso | Descripción | Endpoint a proteger |
|---------|-------------|---------------------|
| `SISTEMA_USUARIOS_VER` | Ver lista de usuarios | GET /api/users (ya existe) |
| `SISTEMA_ROLES_VER` | Ver lista de roles | GET /api/roles (ya existe) |

### 3.3 Rol nuevo propuesto

```json
{
  "codigo": "VISOR_ADMIN",
  "nombre": "Visor de Administración",
  "descripcion": "Rol piloto FASE 8 - puede ver usuarios, roles y estructura",
  "permisos": [
    "SISTEMA_ESTRUCTURA_VER",
    "SISTEMA_USUARIOS_VER",
    "SISTEMA_ROLES_VER"
  ],
  "activo": true,
  "es_sistema": true,
  "fase": "FASE_8"
}
```

### 3.4 Cambios en whitelists

```python
# ANTES
PERMISOS_FASE_4_WHITELIST = ["SISTEMA_ESTRUCTURA_VER"]
ROLES_FASE_6_WHITELIST = ["VISOR_ESTRUCTURA", "VISOR_SISTEMA"]

# DESPUÉS (FASE 8)
PERMISOS_FASE_8_WHITELIST = [
    "SISTEMA_ESTRUCTURA_VER",
    "SISTEMA_USUARIOS_VER", 
    "SISTEMA_ROLES_VER"
]
ROLES_FASE_8_WHITELIST = [
    "VISOR_ESTRUCTURA", 
    "VISOR_SISTEMA",
    "VISOR_ADMIN"
]
```

### 3.5 Validación propuesta

| Caso de prueba | Resultado esperado |
|----------------|-------------------|
| Usuario con `SISTEMA_USUARIOS_VER` directo | ✅ Puede ver usuarios |
| Usuario con `VISOR_ADMIN` (hereda permiso) | ✅ Puede ver usuarios, roles y estructura |
| Usuario sin permiso | ❌ No puede ver (403) |
| Asignar/retirar desde UI FASE 7 | ✅ Funciona sin cambios |

### 3.6 Archivos a modificar

| Archivo | Cambio | Líneas |
|---------|--------|--------|
| `/app/backend/server.py` | Actualizar whitelists | +4 líneas |
| `/app/frontend/src/pages/Usuarios.js` | Actualizar constantes | +3 líneas |

### 3.7 Rollback

```
TIEMPO: 2 minutos
1. Revertir whitelists a valores FASE 7
2. Opcional: db.sec_roles.deleteOne({codigo: "VISOR_ADMIN"})
3. Sistema vuelve a estado FASE 7
```

---

## 4. OPCIÓN B: EXPANSIÓN MODERADA - 4 PERMISOS NUEVOS (RIESGO BAJO)

### 4.1 Descripción

Agregar **4 permisos nuevos** incluyendo un permiso de escritura controlada (`SISTEMA_ALERTAS_VER`).

### 4.2 Permisos propuestos

| Permiso | Descripción | Tipo |
|---------|-------------|------|
| `SISTEMA_USUARIOS_VER` | Ver usuarios | VER |
| `SISTEMA_ROLES_VER` | Ver roles | VER |
| `SISTEMA_SERVIDORES_VER` | Ver servidores | VER |
| `SISTEMA_ALERTAS_VER` | Ver alertas | VER |

### 4.3 Roles nuevos propuestos

```json
[
  {
    "codigo": "VISOR_ADMIN",
    "permisos": ["SISTEMA_ESTRUCTURA_VER", "SISTEMA_USUARIOS_VER", "SISTEMA_ROLES_VER"]
  },
  {
    "codigo": "VISOR_INFRAESTRUCTURA",
    "permisos": ["SISTEMA_SERVIDORES_VER", "SISTEMA_ALERTAS_VER"]
  }
]
```

### 4.4 Por qué NO es recomendado

- Agrega más elementos de los necesarios para validar
- `SISTEMA_SERVIDORES_VER` podría exponer información sensible
- Mayor superficie de prueba sin beneficio claro

---

## 5. OPCIÓN C: EXPANSIÓN A MÓDULO COMERCIAL (RIESGO MEDIO)

### 5.1 Descripción

Agregar permisos del módulo **Comercial** para validar que el RBAC funciona en un módulo operativo real.

### 5.2 Permisos propuestos

| Permiso | Descripción |
|---------|-------------|
| `COMERCIAL_TABLERO_VER` | Ver tablero ejecutivo comercial |
| `COMERCIAL_DASHBOARD_VER` | Ver dashboard comercial |

### 5.3 Por qué NO es recomendado para FASE 8

- El módulo Comercial es **productivo y sensible**
- Requiere proteger múltiples endpoints
- Podría causar regresiones en flujos de negocio
- Mejor reservar para FASE 9+ cuando el piloto esté consolidado

---

## 6. RECOMENDACIÓN

### 6.1 Opción recomendada: **OPCIÓN A - Expansión Mínima**

| Criterio | Evaluación |
|----------|------------|
| Menor riesgo | ✅ Solo 2 permisos nuevos, todos "VER" |
| Menor impacto | ✅ Solo 2 archivos, ~7 líneas |
| Valida expansión | ✅ Demuestra que whitelist escala |
| No toca módulos críticos | ✅ Solo Sistema (ya probado) |
| UI sin cambios | ✅ FASE 7 soporta múltiples permisos/roles |
| Rollback trivial | ✅ 2 minutos |

### 6.2 Justificación

1. **Suficiente para validar**: 2 permisos nuevos demuestran que el sistema escala
2. **Mismo módulo**: Sistema ya está probado desde FASE 3
3. **Permisos coherentes**: `USUARIOS_VER` y `ROLES_VER` complementan `ESTRUCTURA_VER`
4. **Rol con múltiples permisos**: `VISOR_ADMIN` tiene 3 permisos, valida herencia múltiple
5. **Sin sorpresas**: No toca endpoints nuevos complejos

---

## 7. ALCANCE EXACTO RECOMENDADO

### 7.1 Nuevos permisos en whitelist

```python
PERMISOS_FASE_8_WHITELIST = [
    "SISTEMA_ESTRUCTURA_VER",  # Existente FASE 4
    "SISTEMA_USUARIOS_VER",    # Nuevo FASE 8
    "SISTEMA_ROLES_VER"        # Nuevo FASE 8
]
```

### 7.2 Nuevos roles en whitelist

```python
ROLES_FASE_8_WHITELIST = [
    "VISOR_ESTRUCTURA",  # Existente FASE 5
    "VISOR_SISTEMA",     # Existente FASE 6
    "VISOR_ADMIN"        # Nuevo FASE 8
]
```

### 7.3 Documento del nuevo rol

```json
{
  "id": "uuid",
  "codigo": "VISOR_ADMIN",
  "nombre": "Visor de Administración",
  "descripcion": "Rol piloto FASE 8 - acceso lectura a usuarios, roles y estructura",
  "permisos": [
    "SISTEMA_ESTRUCTURA_VER",
    "SISTEMA_USUARIOS_VER",
    "SISTEMA_ROLES_VER"
  ],
  "activo": true,
  "es_sistema": true,
  "nivel_jerarquia": 20,
  "fase": "FASE_8",
  "created_at": "ISODate"
}
```

---

## 8. PERMISOS Y ROLES NUEVOS PROPUESTOS

### 8.1 Permisos nuevos

| Código | Ya en catálogo | Descripción | Endpoint a proteger |
|--------|----------------|-------------|---------------------|
| `SISTEMA_USUARIOS_VER` | ✅ Sí | Ver lista de usuarios | GET /api/users |
| `SISTEMA_ROLES_VER` | ✅ Sí | Ver lista de roles | GET /api/roles |

**Nota**: Ambos permisos ya existen en `sec_permisos_catalogo`, solo se agregan a la whitelist.

### 8.2 Roles nuevos

| Código | Permisos | Descripción |
|--------|----------|-------------|
| `VISOR_ADMIN` | 3 permisos | Visor completo de administración del sistema |

### 8.3 Por qué estos y no otros

1. **Ya probados en FASE 7**: El rol `VISOR_SISTEMA` ya usa `SISTEMA_USUARIOS_VER`
2. **Coherencia funcional**: Ver usuarios + ver roles + ver estructura = visor de admin
3. **Bajo riesgo**: Solo lectura, no modifican datos
4. **Endpoints simples**: GET sin parámetros complejos
5. **Ya protegidos por rol legacy**: Solo se agrega granularidad

---

## 9. ARCHIVOS / ENDPOINTS / COLECCIONES IMPACTADAS

### 9.1 Archivos a modificar

| Archivo | Tipo de cambio | Líneas estimadas |
|---------|----------------|------------------|
| `/app/backend/server.py` | Actualizar constantes whitelist | +4 líneas |
| `/app/frontend/src/pages/Usuarios.js` | Actualizar constantes en UI | +3 líneas |

### 9.2 Endpoints involucrados

| Endpoint | Cambio |
|----------|--------|
| `POST /api/admin/permisos/asignar` | Ya soporta (ampliar whitelist) |
| `POST /api/admin/roles/asignar` | Ya soporta (ampliar whitelist) |
| `GET /api/users` | Futuro: proteger con permiso (NO en FASE 8) |
| `GET /api/roles` | Futuro: proteger con permiso (NO en FASE 8) |

**NOTA IMPORTANTE**: En FASE 8 **NO se protegerán los endpoints** con los nuevos permisos. Solo se expande la whitelist para que puedan asignarse. La protección real de endpoints será en FASE 9+.

### 9.3 Colecciones MongoDB

| Colección | Operación |
|-----------|-----------|
| `sec_roles` | INSERT (nuevo rol VISOR_ADMIN) |
| `users` | UPDATE (campo sec_permisos, sec_roles) |
| `sec_bitacora_admin` | INSERT (auditoría) |

---

## 10. COMPATIBILIDAD LEGACY

### 10.1 Coexistencia garantizada

| Campo | Estado FASE 8 |
|-------|---------------|
| `users.role` | ✅ INTACTO |
| `users.rbac_role` | ✅ INTACTO |
| `roles` | ✅ INTACTO |
| `rbac_roles` | ✅ INTACTO |
| `users.sec_permisos` | ✅ Compatible (más opciones) |
| `users.sec_rol` | ✅ Compatible |
| `users.sec_roles` | ✅ Compatible (más opciones) |
| `sec_roles` | ✅ Compatible (+1 rol) |

### 10.2 Orden de resolución (sin cambios)

```
1. Permisos directos (sec_permisos) → FASE 4
2. Múltiples roles (sec_roles array) → FASE 6
3. Rol único (sec_rol string) → FASE 5
4. Fallback legacy (SuperAdmin) → FASE 3
```

---

## 11. RIESGOS Y MITIGACIONES

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|--------|--------------|---------|------------|
| 1 | Confusión de nombres | BAJA | BAJO | Nombres claros: VISOR_ADMIN |
| 2 | UI no escala | MUY BAJA | BAJO | FASE 7 ya soporta arrays |
| 3 | Conflicto con roles legacy | MUY BAJA | BAJO | Whitelist aislada |
| 4 | Auditoría incompleta | BAJA | BAJO | Reutiliza sec_bitacora_admin |
| 5 | Regresión en asignación | BAJA | MEDIO | Tests exhaustivos |

---

## 12. QUÉ NO SE TOCARÁ

| Elemento | Confirmación |
|----------|--------------|
| `get_current_user()` | ❌ NO SE MODIFICA |
| `Layout.js` | ❌ NO SE MODIFICA |
| Router global | ❌ NO SE MODIFICA |
| Auth global | ❌ NO SE MODIFICA |
| Middleware | ❌ NO SE MODIFICA |
| Endpoints de Comercial | ❌ NO SE MODIFICA |
| Endpoints de Compras | ❌ NO SE MODIFICA |
| Endpoints de Finanzas | ❌ NO SE MODIFICA |
| Endpoints de RH | ❌ NO SE MODIFICA |
| Protección de endpoints | ❌ NO EN FASE 8 (solo whitelist) |
| `users.role` | ❌ NO SE MODIFICA |
| `users.rbac_role` | ❌ NO SE MODIFICA |
| Colección `roles` | ❌ NO SE MODIFICA |
| Colección `rbac_roles` | ❌ NO SE MODIFICA |
| UI de módulos operativos | ❌ NO SE MODIFICA |

---

## 13. ROLLBACK

### 13.1 Pasos de rollback

```
TIEMPO TOTAL: 2 minutos

1. Revertir whitelists en server.py:
   PERMISOS_FASE_8_WHITELIST → PERMISOS_FASE_4_WHITELIST
   ROLES_FASE_8_WHITELIST → ROLES_FASE_6_WHITELIST

2. Revertir constantes en Usuarios.js

3. Opcional (limpieza):
   db.sec_roles.deleteOne({codigo: "VISOR_ADMIN"})
   db.users.updateMany({}, {$pull: {sec_roles: "VISOR_ADMIN"}})

IMPACTO:
- Permisos asignados se vuelven inoperantes (whitelist los bloquea)
- FASE 7 sigue funcionando
- FASE 4/5/6 sin cambios
```

---

## 14. CHECKLIST DE NO REGRESIÓN

### 14.1 Pre-implementación

| Verificación | Método |
|--------------|--------|
| Login SuperAdmin | curl |
| Login otros roles | curl |
| GET /api/users | curl |
| GET /api/roles | curl |
| POST /api/admin/permisos/asignar | curl |
| POST /api/admin/roles/asignar | curl |
| Tab Usuarios funciona | screenshot |
| Tab Estructura funciona | screenshot |
| Sección RBAC visible (FASE 7) | screenshot |

### 14.2 Post-implementación

| Verificación | Resultado esperado |
|--------------|-------------------|
| Login SuperAdmin | ✅ |
| Login Administrador | ✅ |
| GET /api/users | ✅ |
| GET /api/roles | ✅ |
| Asignar SISTEMA_USUARIOS_VER | ✅ |
| Asignar SISTEMA_ROLES_VER | ✅ |
| Asignar VISOR_ADMIN | ✅ |
| Retirar permisos/roles nuevos | ✅ |
| Rol VISOR_ADMIN hereda 3 permisos | ✅ |
| UI FASE 7 muestra nuevos elementos | ✅ |
| Auditoría registra operaciones | ✅ |
| FASE 4 sigue funcionando | ✅ |
| FASE 5 sigue funcionando | ✅ |
| FASE 6 sigue funcionando | ✅ |
| FASE 7 sigue funcionando | ✅ |
| Dashboards sin regresión | ✅ |

---

## 15. SOLICITUD DE APROBACIÓN

### 15.1 Resumen de lo que se solicita aprobar

| # | Elemento | Descripción |
|---|----------|-------------|
| 1 | Expandir whitelist permisos | +2 permisos (`SISTEMA_USUARIOS_VER`, `SISTEMA_ROLES_VER`) |
| 2 | Expandir whitelist roles | +1 rol (`VISOR_ADMIN`) |
| 3 | Crear rol `VISOR_ADMIN` | Con 3 permisos del módulo Sistema |
| 4 | Actualizar constantes UI | Para mostrar nuevos elementos |
| 5 | NO proteger endpoints | Solo whitelist, protección en FASE 9+ |

### 15.2 Lo que NO se hará en FASE 8

| Elemento | Confirmación |
|----------|--------------|
| Perfiles predefinidos | ❌ NO |
| CRUD general | ❌ NO |
| Permisos de escritura | ❌ NO |
| Permisos de módulos operativos | ❌ NO |
| Protección real de endpoints | ❌ NO (solo whitelist) |
| Cambios en auth global | ❌ NO |
| Cambios en Layout.js | ❌ NO |
| Cambios en router | ❌ NO |
| Migración de usuarios | ❌ NO |

### 15.3 Decisión solicitada

**¿Aprueba la ejecución de FASE 8 OPCIÓN A bajo las condiciones descritas?**

- [ ] SÍ, proceder con OPCIÓN A (Expansión Mínima - 2 permisos, 1 rol)
- [ ] NO, requiere ajustes (especificar)
- [ ] PREFERIR OPCIÓN B (4 permisos)
- [ ] DIFERIR esta fase

---

**FIN DEL DOCUMENTO DE PROPUESTA FASE 8**

*Esperando aprobación explícita antes de implementar.*
