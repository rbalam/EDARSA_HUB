# FASE 2 - DOCUMENTO DE ALCANCE CONTROLADO
## Arquitectura de Seguridad EDARSA HUB

**Versión:** 1.0  
**Fecha:** Diciembre 2025  
**Estado:** PENDIENTE APROBACIÓN  
**Requisito previo:** FASE 1 aprobada y cerrada ✅

---

## ÍNDICE

1. [Alcance Propuesto](#1-alcance-propuesto)
2. [Lista Exacta de Cambios](#2-lista-exacta-de-cambios)
3. [Lista Explícita de Exclusiones](#3-lista-explícita-de-exclusiones)
4. [Naturaleza de FASE 2](#4-naturaleza-de-fase-2)
5. [Definición Exacta del Piloto](#5-definición-exacta-del-piloto)
6. [Estrategia de Compatibilidad](#6-estrategia-de-compatibilidad)
7. [Checklist de No Regresión](#7-checklist-de-no-regresión)
8. [Riesgos Transversales y Mitigaciones](#8-riesgos-transversales-y-mitigaciones)
9. [Criterios de Éxito/Fracaso](#9-criterios-de-éxitofracaso)
10. [Aprobación Requerida](#10-aprobación-requerida)

---

## 1. ALCANCE PROPUESTO

### 1.1 Objetivo de FASE 2

**Implementar capa de compatibilidad PASIVA que permita:**
- Consultar nuevo modelo sin afectar flujos existentes
- Registrar accesos en bitácora nueva (escritura paralela)
- Preparar UI para mostrar estructura organizacional (solo lectura)

**NO implementar en FASE 2:**
- Cambio de middleware de autenticación
- Sustitución de validación de roles
- Migración de permisos de usuarios
- Activación funcional de nuevo sistema

### 1.2 Módulo Piloto Propuesto

**OPCIÓN RECOMENDADA: Módulo Sistema → Alertas**

Justificación:
- Bajo impacto en operaciones críticas
- No afecta finanzas, compras, RH ni comercial
- Fácil rollback
- Permite probar flujo completo sin riesgo

**ALTERNATIVA: Módulo Sistema → Catálogo SQL**
- Igualmente bajo impacto
- Principalmente lectura/consulta

---

## 2. LISTA EXACTA DE CAMBIOS

### 2.1 Archivos que SÍ se modificarían

| Archivo | Cambio Propuesto | Riesgo |
|---------|------------------|--------|
| `/app/backend/core/security_v2_passive.py` | Agregar funciones de consulta a colecciones nuevas | BAJO |
| `/app/backend/server.py` | Agregar 2-3 endpoints NUEVOS de solo lectura | BAJO |
| `/app/frontend/src/pages/Usuarios.js` | Agregar tab "Estructura Organizacional" (solo lectura) | BAJO |

### 2.2 Colecciones que SÍ se modificarían

| Colección | Cambio | Riesgo |
|-----------|--------|--------|
| `sec_bitacora_acceso` | Comenzar a escribir logs (paralelo) | CERO |
| `sec_permisos_catalogo` | Posibles ajustes de catálogo | BAJO |
| `sec_modulos_sistema` | Posibles ajustes de catálogo | BAJO |

### 2.3 Endpoints NUEVOS propuestos

| Endpoint | Método | Propósito | Conectado a Producción |
|----------|--------|-----------|------------------------|
| `/api/sistema/estructura-organizacional` | GET | Ver empresas/unidades/sucursales | NO (solo lectura nueva estructura) |
| `/api/sistema/mapeo-servidor-sucursal` | GET | Ver mapeo servidor↔sucursal | NO (solo lectura) |
| `/api/sistema/permisos-catalogo` | GET | Ver catálogo de permisos v2 | NO (solo lectura) |

### 2.4 Servicios que SÍ se modificarían

| Servicio | Cambio | Riesgo |
|----------|--------|--------|
| Ningún servicio existente | N/A | CERO |
| Nuevo servicio: `estructura_service.py` | Crear servicio aislado para nueva estructura | BAJO |

### 2.5 Middleware que SÍ se modificaría

**NINGUNO**

El middleware actual (`get_current_user`, `filter_servers_by_permissions`, etc.) NO será modificado en FASE 2.

---

## 3. LISTA EXPLÍCITA DE EXCLUSIONES

### 3.1 Archivos que NO se tocarán

| Archivo | Razón |
|---------|-------|
| `/app/backend/core/security.py` | Middleware crítico de autenticación |
| `/app/backend/modules/auth/service.py` | Lógica de login activa |
| `/app/backend/modules/auth/routes.py` | Endpoints de autenticación |
| `/app/backend/modules/comercial/*` | Módulo productivo |
| `/app/backend/modules/compras/*` | Módulo productivo |
| `/app/backend/modules/finanzas/*` | Módulo productivo |
| `/app/backend/modules/fase2_operativo/*` | Módulo productivo |
| `/app/backend/modules/rrhh/*` | Módulo productivo |
| `/app/frontend/src/pages/Comercial.js` | UI productiva |
| `/app/frontend/src/pages/Compras.js` | UI productiva |
| `/app/frontend/src/pages/Finanzas.js` | UI productiva |
| `/app/frontend/src/pages/Layout.js` | Menú principal (no se tocará lógica de permisos) |

### 3.2 Colecciones que NO se tocarán

| Colección | Razón |
|-----------|-------|
| `users` | Colección crítica de usuarios |
| `roles` | Colección legacy activa |
| `rbac_roles` | Sistema RBAC v2 activo (Finanzas) |
| `rbac_permisos` | Permisos RBAC v2 activos |
| `rbac_usuarios_roles` | Asignaciones activas |
| `servers` | Configuración de servidores |
| `permisos_catalogos` | Permisos de catálogos actuales |

### 3.3 Funcionalidades que NO se afectarán

| Funcionalidad | Confirmación |
|---------------|--------------|
| Login/Logout | ❌ NO SE TOCARÁ |
| Validación de roles actual | ❌ NO SE TOCARÁ |
| Filtro por servidor | ❌ NO SE TOCARÁ |
| Filtro por sucursal | ❌ NO SE TOCARÁ |
| Dashboard Comercial | ❌ NO SE TOCARÁ |
| Dashboard Compras | ❌ NO SE TOCARÁ |
| Dashboard Finanzas | ❌ NO SE TOCARÁ |
| Dashboard RH | ❌ NO SE TOCARÁ |
| Cargos económicos | ❌ NO SE TOCARÁ |
| Workflows | ❌ NO SE TOCARÁ |
| Integraciones SQL | ❌ NO SE TOCARÁ |

---

## 4. NATURALEZA DE FASE 2

### 4.1 ¿FASE 2 es pasiva o semiactiva?

**RESPUESTA: SEMIACTIVA CONTROLADA**

| Componente | Estado |
|------------|--------|
| Colecciones nuevas | LECTURA + ESCRITURA (bitácora) |
| Endpoints nuevos | ACTIVOS (solo lectura de nueva estructura) |
| Middleware actual | PASIVO (sin cambios) |
| Validación de permisos | PASIVA (no se activa nuevo sistema) |
| UI nueva (tab) | ACTIVA (solo visualización) |

### 4.2 ¿Qué significa "semiactiva"?

- Los endpoints NUEVOS estarán activos
- La escritura en bitácora estará activa (paralela)
- La UI mostrará información NUEVA
- PERO: No se cambia la lógica de autorización existente
- PERO: No se migran usuarios ni permisos
- PERO: No se sustituye ningún flujo productivo

### 4.3 Diagrama de flujo FASE 2

```
USUARIO HACE LOGIN
    │
    ▼
[Middleware ACTUAL - SIN CAMBIOS]
    │
    ▼
[Validación roles ACTUAL - SIN CAMBIOS]
    │
    ├──────────────────────────────────┐
    │                                  │
    ▼                                  ▼
[Endpoints EXISTENTES]         [Endpoints NUEVOS FASE 2]
    │                                  │
    ▼                                  ▼
[Flujo ACTUAL]                 [Solo lectura nueva estructura]
    │                                  │
    ▼                                  ▼
[Respuesta ACTUAL]             [Respuesta solo información]
                                       │
                                       ▼
                               [Escritura bitácora PARALELA]
```

---

## 5. DEFINICIÓN EXACTA DEL PILOTO

### 5.1 Módulo: Sistema → Visualización de Estructura

**NO es un piloto de "activación de permisos"**
**ES un piloto de "visualización de nueva estructura"**

### 5.2 Pantalla exacta

- **Ruta:** `/usuarios` (tab adicional)
- **Tab nuevo:** "Estructura Organizacional"
- **Funcionalidad:** Solo visualización de empresas/unidades/sucursales

### 5.3 Endpoints exactos

| Endpoint | Descripción |
|----------|-------------|
| `GET /api/sistema/estructura-organizacional` | Lista empresas con unidades y sucursales |
| `GET /api/sistema/mapeo-servidor-sucursal` | Lista mapeo servidor↔sucursal |

### 5.4 Permisos requeridos

**NINGUNO NUEVO**

- Solo usuarios con acceso actual a "Usuarios" verán el tab
- Se usa validación de rol existente (Administrador, SuperAdministrador)
- NO se implementa nueva validación de permisos

### 5.5 Usuarios de prueba

| Usuario | Rol | Debería ver tab |
|---------|-----|-----------------|
| ricardo@edarsa.com.mx | SuperAdministrador | SÍ |
| admin@inventario.com | Administrador | SÍ |
| supervisor@test.com | Supervisor | NO (no tiene acceso a Usuarios) |

### 5.6 Rollback exacto

```
ROLLBACK FASE 2:
1. Eliminar tab "Estructura Organizacional" de Usuarios.js
2. Eliminar endpoints nuevos de server.py
3. Eliminar archivo estructura_service.py (si se creó)
4. NO es necesario eliminar colecciones (ya existían de FASE 1)
5. NO es necesario restaurar nada más (no se tocaron flujos existentes)

Tiempo estimado: 5 minutos
Impacto: CERO (nada productivo fue modificado)
```

---

## 6. ESTRATEGIA DE COMPATIBILIDAD

### 6.1 Coexistencia de sistemas de roles

```
ESTADO ACTUAL:
┌─────────────────┬──────────────────┬─────────────────┐
│ roles (legacy)  │ rbac_roles (v2)  │ sec_* (nuevo)   │
├─────────────────┼──────────────────┼─────────────────┤
│ ACTIVO          │ ACTIVO (Finanzas)│ PASIVO          │
│ Se usa en login │ Se usa en cargos │ Solo lectura    │
│ Se usa en UI    │ Se usa en resp.  │ Solo bitácora   │
└─────────────────┴──────────────────┴─────────────────┘

ESTADO DESPUÉS DE FASE 2:
┌─────────────────┬──────────────────┬─────────────────┐
│ roles (legacy)  │ rbac_roles (v2)  │ sec_* (nuevo)   │
├─────────────────┼──────────────────┼─────────────────┤
│ ACTIVO          │ ACTIVO (Finanzas)│ SEMIACTIVO      │
│ Se usa en login │ Se usa en cargos │ Lectura + UI    │
│ Se usa en UI    │ Se usa en resp.  │ Bitácora        │
│ SIN CAMBIOS     │ SIN CAMBIOS      │ SIN AUTORIZACIÓN│
└─────────────────┴──────────────────┴─────────────────┘
```

### 6.2 Tabla de equivalencia (documentación, no activación)

| Rol Legacy | Rol RBAC v2 | Rol Propuesto | Nivel |
|------------|-------------|---------------|-------|
| SuperAdministrador | ADMIN | SUPER_ADMIN | 100 |
| Administrador | ADMIN | ADMIN | 90 |
| - | DIRECCION | DIRECCION | 80 |
| - | GERENTE_OPS | GERENTE | 70 |
| Supervisor | SUPERVISOR | SUPERVISOR | 50 |
| - | AUDITOR | AUDITOR | 40 |
| Usuario | OPERADOR | OPERADOR | 30 |

**NOTA:** Esta tabla es solo documentación. NO se activa migración en FASE 2.

### 6.3 Regla de coexistencia FASE 2

```
IF usuario accede a endpoint EXISTENTE:
    → Usar sistema de autorización ACTUAL (sin cambios)
    → Opcional: Escribir en bitácora nueva (paralelo)

IF usuario accede a endpoint NUEVO de estructura:
    → Verificar rol con sistema ACTUAL
    → Mostrar datos de estructura NUEVA
    → NO activar nueva validación de permisos
```

---

## 7. CHECKLIST DE NO REGRESIÓN

### 7.1 Pre-ejecución FASE 2

- [ ] Backup de MongoDB
- [ ] Documentar estado actual de usuarios con acceso a "Usuarios"
- [ ] Verificar login funciona
- [ ] Verificar endpoint /api/users funciona
- [ ] Verificar endpoint /api/roles funciona

### 7.2 Durante ejecución FASE 2

- [ ] Crear endpoints nuevos SIN modificar existentes
- [ ] Crear tab nuevo SIN modificar tabs existentes
- [ ] NO importar security_v2_passive en archivos productivos
- [ ] NO modificar get_current_user
- [ ] NO modificar filter_servers_by_permissions

### 7.3 Post-ejecución FASE 2

| Verificación | Criterio |
|--------------|----------|
| Login SuperAdmin | Debe funcionar igual |
| Login Admin | Debe funcionar igual |
| Login Supervisor | Debe funcionar igual |
| GET /api/users | Debe retornar mismos datos |
| GET /api/roles | Debe retornar mismos datos |
| GET /api/servers | Debe retornar mismos datos |
| Dashboard Comercial | Debe cargar igual |
| Dashboard Compras | Debe cargar igual |
| Dashboard Finanzas | Debe cargar igual |
| Dashboard RH | Debe cargar igual |
| Crear usuario | Debe funcionar igual |
| Editar usuario | Debe funcionar igual |
| Crear cargo económico | Debe funcionar igual |
| Nuevo tab visible | Solo para Admin/SuperAdmin |
| Endpoints nuevos | Deben retornar estructura |

### 7.4 Criterios de ROLLBACK inmediato

Si cualquiera de estos falla, hacer rollback:
1. ❌ Login no funciona
2. ❌ Dashboard muestra error
3. ❌ Endpoints existentes fallan
4. ❌ Cargos económicos no funcionan
5. ❌ Usuarios no pueden ver sus módulos asignados

---

## 8. RIESGOS TRANSVERSALES Y MITIGACIONES

### 8.1 Riesgos identificados

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|--------|--------------|---------|------------|
| 1 | Tab nuevo causa error en Usuarios.js | BAJA | MEDIO | Código aislado, fácil remover |
| 2 | Endpoints nuevos afectan performance | MUY BAJA | BAJO | Solo lectura, sin joins complejos |
| 3 | Bitácora paralela llena disco | MUY BAJA | BAJO | TTL de 90 días ya configurado |
| 4 | Import accidental de módulo nuevo | BAJA | MEDIO | Verificación manual pre-merge |

### 8.2 Riesgos NO presentes en FASE 2

| Riesgo | Por qué NO aplica |
|--------|-------------------|
| Romper login | No se toca auth |
| Romper permisos | No se toca validación |
| Romper dashboards | No se tocan módulos |
| Afectar finanzas | No se toca RBAC v2 |
| Afectar comercial | No se toca módulo |
| Cambiar contratos API | Solo endpoints nuevos |

### 8.3 Mitigación general

```
REGLA DE ORO FASE 2:
- Todo código nuevo va en archivos nuevos
- Todo endpoint nuevo tiene prefijo identificable
- Todo cambio de UI es tab adicional, no modificación
- Si surge duda de impacto transversal → DETENER → DOCUMENTAR → PEDIR APROBACIÓN
```

---

## 9. CRITERIOS DE ÉXITO/FRACASO

### 9.1 Criterios de éxito

| # | Criterio | Cómo verificar |
|---|----------|----------------|
| 1 | Tab nuevo visible para Admin/SuperAdmin | Screenshot |
| 2 | Estructura organizacional se muestra | Curl a endpoint nuevo |
| 3 | Bitácora registra accesos | Consulta a sec_bitacora_acceso |
| 4 | Ningún flujo existente afectado | Checklist completo verde |
| 5 | Rollback ejecutable en < 5 minutos | Prueba de rollback |

### 9.2 Criterios de fracaso (detener FASE 2)

| # | Criterio | Acción |
|---|----------|--------|
| 1 | Login falla | ROLLBACK INMEDIATO |
| 2 | Dashboard no carga | ROLLBACK INMEDIATO |
| 3 | Error 500 en endpoint existente | ROLLBACK INMEDIATO |
| 4 | Usuario pierde acceso a módulo | ROLLBACK INMEDIATO |
| 5 | Cualquier regresión detectada | ROLLBACK + ANÁLISIS |

---

## 10. APROBACIÓN REQUERIDA

### 10.1 Resumen de lo que se solicita aprobar

| Item | Descripción |
|------|-------------|
| Crear 2-3 endpoints NUEVOS de solo lectura | Ver estructura organizacional |
| Crear tab NUEVO en Usuarios | Visualizar empresas/unidades/sucursales |
| Activar escritura PARALELA en bitácora | Sin afectar flujos existentes |
| Crear archivo estructura_service.py | Servicio aislado |

### 10.2 Confirmación de restricciones

| Restricción | Confirmada |
|-------------|------------|
| No modificar auth/login | ✅ |
| No modificar middleware | ✅ |
| No modificar validación de permisos | ✅ |
| No migrar usuarios | ✅ |
| No sustituir roles legacy | ✅ |
| No tocar módulos productivos | ✅ |
| Rollback < 5 minutos | ✅ |

### 10.3 Decisión solicitada

**¿Aprueba la ejecución de FASE 2 bajo las condiciones descritas?**

- [ ] SÍ, proceder con FASE 2
- [ ] NO, requiere ajustes (especificar)
- [ ] DIFERIR, no es prioritario ahora

---

**FIN DEL DOCUMENTO DE ALCANCE FASE 2**
