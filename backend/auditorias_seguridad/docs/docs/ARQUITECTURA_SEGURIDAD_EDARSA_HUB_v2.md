# ARQUITECTURA DE SEGURIDAD EDARSA HUB
## VERSIÓN REFINADA - Respuesta a Observaciones Obligatorias

**Versión:** 2.0  
**Fecha:** Diciembre 2025  
**Estado:** PENDIENTE APROBACIÓN FINAL  
**Documento anterior:** v1.0 (rechazado para ajustes)

---

## ÍNDICE

1. [Justificación de Colecciones Propuestas](#1-justificación-de-colecciones-propuestas)
2. [Alcance Exacto de Fase 1](#2-alcance-exacto-de-fase-1)
3. [Mapa de Impacto Transversal](#3-mapa-de-impacto-transversal)
4. [Aclaración: Empresa vs Servidor](#4-aclaración-empresa-vs-servidor)
5. [Detalle: Frontend Valida Sin Backend](#5-detalle-frontend-valida-sin-backend)
6. [Piloto en Finanzas: Análisis Detallado](#6-piloto-en-finanzas-análisis-detallado)
7. [Tabla de Compatibilidad Legacy](#7-tabla-de-compatibilidad-legacy)
8. [Checklist de No Regresión](#8-checklist-de-no-regresión)

---

## 1. JUSTIFICACIÓN DE COLECCIONES PROPUESTAS

### Análisis: ¿16 colecciones son necesarias?

**RESPUESTA: NO TODAS SON INDISPENSABLES PARA FASE 1**

He reducido y clasificado las colecciones en tres categorías:

### 1.1 COLECCIONES INDISPENSABLES (Fase 1 - Estructura vacía)

| # | Colección | Propósito | Impacto Transversal | Activación |
|---|-----------|-----------|---------------------|------------|
| 1 | `sec_permisos_catalogo` | Catálogo maestro de permisos disponibles | NINGUNO (solo datos) | Fase 1: crear vacía, poblar catálogo |
| 2 | `sec_modulos_sistema` | Catálogo de módulos del sistema | NINGUNO (solo datos) | Fase 1: crear vacía, poblar catálogo |
| 3 | `sec_bitacora_acceso` | Logs de acceso (ya existe parcialmente como rbac_audit_log) | NINGUNO si solo se escribe | Fase 1: crear, comenzar a escribir |

**Total Fase 1: 3 colecciones nuevas** (solo catálogos y logs, sin afectar lógica)

### 1.2 COLECCIONES NECESARIAS (Fase 2+ - Requieren aprobación separada)

| # | Colección | Propósito | Por qué diferir |
|---|-----------|-----------|-----------------|
| 4 | `sec_roles_v2` | Roles con jerarquía | Requiere migración de `roles` actual |
| 5 | `sec_roles_permisos` | Relación roles-permisos | Depende de sec_roles_v2 |
| 6 | `sec_usuarios_roles` | Múltiples roles por usuario | CAMBIO TRANSVERSAL - requiere validación extensa |
| 7 | `sec_usuarios_contexto` | Acceso por empresa/sucursal | CAMBIO DE EJE - requiere plan específico |

### 1.3 COLECCIONES DIFERIDAS (Fase 3+ - Evaluar necesidad real)

| # | Colección | Propósito | Decisión |
|---|-----------|-----------|----------|
| 8 | `sec_perfiles_acceso` | Perfiles reutilizables | DIFERIR - evaluar si realmente se necesita |
| 9 | `sec_perfiles_permisos` | Permisos por perfil | DIFERIR - depende de 8 |
| 10 | `sec_usuarios_perfiles` | Asignación usuario-perfil | DIFERIR - depende de 8 |
| 11 | `sec_usuarios_override` | Permisos individuales | DIFERIR - complejidad alta |
| 12 | `sec_limites_autorizacion` | Topes de montos | DIFERIR - módulo específico |
| 13 | `sec_pantallas_sistema` | Catálogo pantallas | DIFERIR - no crítico |
| 14 | `sec_tabs_sistema` | Catálogo tabs | DIFERIR - no crítico |
| 15 | `sec_acciones_sistema` | Catálogo acciones | DIFERIR - incluir en sec_permisos_catalogo |
| 16 | `sec_sesiones` | Control de sesiones | DIFERIR - no crítico ahora |

### 1.4 CONCLUSIÓN SOBRE COLECCIONES

**PROPUESTA REVISADA PARA FASE 1:**
- Crear SOLO 3 colecciones (catálogos + bitácora)
- NO activar ninguna lógica nueva
- NO afectar middleware existente
- NO migrar datos de usuarios/roles

---

## 2. ALCANCE EXACTO DE FASE 1

### 2.1 LO QUE SÍ HARÁ FASE 1

| Acción | Descripción | Riesgo |
|--------|-------------|--------|
| Crear colección `sec_permisos_catalogo` | Vacía, índices básicos | CERO |
| Crear colección `sec_modulos_sistema` | Vacía, índices básicos | CERO |
| Crear colección `sec_bitacora_acceso` | Para logs nuevos | CERO |
| Poblar catálogo de permisos | INSERT de datos estáticos | CERO |
| Poblar catálogo de módulos | INSERT de datos estáticos | CERO |
| Documentar permisos actuales | Solo documentación | CERO |
| Crear funciones helper (no activadas) | Código muerto temporal | CERO |

### 2.2 LO QUE NO HARÁ FASE 1 (CONFIRMACIÓN EXPLÍCITA)

| Elemento | Confirmación |
|----------|--------------|
| **Dashboards** | ❌ NO SE TOCARÁN |
| **Filtros por sucursal/empresa** | ❌ NO SE TOCARÁN |
| **Ventas (cálculos, reportes)** | ❌ NO SE TOCARÁN |
| **Integraciones SQL** | ❌ NO SE TOCARÁN |
| **Integraciones API** | ❌ NO SE TOCARÁN |
| **Permisos actualmente operativos** | ❌ NO SE TOCARÁN |
| **Colección `users`** | ❌ NO SE MODIFICARÁ |
| **Colección `roles`** | ❌ NO SE MODIFICARÁ |
| **Colección `rbac_roles`** | ❌ NO SE MODIFICARÁ |
| **Middleware `get_current_user`** | ❌ NO SE MODIFICARÁ |
| **Función `filter_servers_by_permissions`** | ❌ NO SE MODIFICARÁ |
| **Función `user_has_server_access`** | ❌ NO SE MODIFICARÁ |
| **Frontend Layout.js** | ❌ NO SE MODIFICARÁ |
| **Módulo Comercial** | ❌ NO SE TOCARÁ |
| **Módulo Compras** | ❌ NO SE TOCARÁ |
| **Módulo Finanzas** | ❌ NO SE TOCARÁ |
| **Módulo Operativo** | ❌ NO SE TOCARÁ |
| **Módulo RH** | ❌ NO SE TOCARÁ |

### 2.3 ENTREGABLES DE FASE 1

1. ✅ 3 colecciones creadas (vacías o con catálogos)
2. ✅ Catálogo de 80+ permisos documentados
3. ✅ Catálogo de módulos documentado
4. ✅ Documento de mapeo legacy → nuevo
5. ✅ Funciones helper (sin activar)
6. ✅ Tests unitarios (sin ejecutar en producción)

---

## 3. MAPA DE IMPACTO TRANSVERSAL

### 3.1 FASE 1: IMPACTO CERO (Confirmado)

```
MÓDULOS AFECTADOS EN FASE 1:
├── Comercial          → NINGUNO
├── Compras            → NINGUNO
├── Finanzas           → NINGUNO
├── Operativo          → NINGUNO
├── RH                 → NINGUNO
├── Inventarios        → NINGUNO
├── Sistema            → NINGUNO
└── Auth               → NINGUNO (solo se agrega escritura a bitácora opcional)

ENDPOINTS AFECTADOS EN FASE 1:
└── NINGUNO

MIDDLEWARE AFECTADO EN FASE 1:
└── NINGUNO

COMPONENTES FRONTEND AFECTADOS EN FASE 1:
└── NINGUNO

COLECCIONES MODIFICADAS EN FASE 1:
└── NINGUNA existente (solo se crean nuevas vacías)

MENÚS/TABS AFECTADOS EN FASE 1:
└── NINGUNO
```

### 3.2 DEPENDENCIAS IDENTIFICADAS (Para fases futuras)

```
ÁRBOL DE DEPENDENCIAS:

core/security.py (CRÍTICO - NO TOCAR EN FASE 1)
├── get_current_user() → Usado por 183+ endpoints
├── user_has_server_access() → Usado por módulos Comercial, Compras
├── filter_servers_by_permissions() → Usado por /api/servers
└── filter_sucursales_by_permissions() → Usado por filtros

modules/auth/service.py (CRÍTICO - NO TOCAR EN FASE 1)
├── login_user() → Autenticación
├── get_users() → Listado usuarios
├── update_user() → Edición usuarios
└── get_roles() → Listado roles

frontend/Layout.js (CRÍTICO - NO TOCAR EN FASE 1)
├── hasAccess() → Controla visibilidad de menús
├── modulos[] → Lista de módulos con roles
└── sistema[] → Lista de opciones sistema

MÓDULOS CON VALIDACIÓN DE ROL:
├── comercial/routes.py → user_has_server_access(), role == 'Administrador'
├── fase2_operativo/*/routes.py → role in ['Administrador', 'Gerente', 'Director']
├── finanzas/cargos_routes.py → RBAC v2 (rbac_permisos)
├── finanzas/responsabilidad_routes.py → RBAC v2 (rbac_permisos)
└── auth/routes.py → role verification via service
```

### 3.3 QUÉ NO SE TOCARÁ EN NINGUNA FASE SIN APROBACIÓN EXPLÍCITA

| Componente | Razón |
|------------|-------|
| Cálculo de ventas | Crítico para negocio |
| Cálculo de inventarios | Crítico para operaciones |
| Filtros por sucursal existentes | Funcionan correctamente |
| Lógica de metas comerciales | Ya validada |
| Integración con SoftRestaurant | Estable |
| Integración con MPRO | Estable |
| Dashboard Tablero Ejecutivo | En uso activo |

---

## 4. ACLARACIÓN: EMPRESA VS SERVIDOR

### 4.1 PROPUESTA REVISADA

**ACEPTO la definición del usuario:**

| Concepto | Rol en el sistema | Cambio propuesto |
|----------|-------------------|------------------|
| **Empresa/Unidad/Sucursal** | Eje funcional del acceso | Implementar gradualmente |
| **Servidor** | Dimensión técnica de conectividad | MANTENER como está |

### 4.2 PLAN DE COEXISTENCIA

```
ESTADO ACTUAL (se mantiene):
Usuario → allowed_servers[] → Servidor → Datos

ESTADO FUTURO (coexistencia):
Usuario → allowed_servers[] → Servidor → Datos  (LEGACY - sigue funcionando)
Usuario → empresas_permitidas[] → Empresa → Sucursales → Datos  (NUEVO - opcional)

TRADUCCIÓN AUTOMÁTICA (cuando se active):
empresas_permitidas → sucursales → server_sucursales_config → servers
```

### 4.3 CONFIRMACIÓN

- ❌ NO eliminaré `allowed_servers` de users
- ❌ NO desactivaré lógica de servidor
- ❌ NO forzaré migración a empresa
- ✅ SÍ prepararé estructura para futuro
- ✅ SÍ documentaré equivalencias

---

## 5. DETALLE: FRONTEND VALIDA SIN BACKEND

### 5.1 MENÚS QUE SOLO VALIDAN EN FRONTEND

| Menú | Roles en Frontend | Backend Valida? | Criticidad |
|------|-------------------|-----------------|------------|
| Tablero Ejecutivo | Usuario, Supervisor, Administrador | ⚠️ Solo `user_has_server_access` | MEDIA |
| Comercial | Usuario, Supervisor, Administrador | ⚠️ Solo `user_has_server_access` | MEDIA |
| Compras | Supervisor, Administrador | ⚠️ Parcial (algunas acciones sí) | MEDIA |
| Operaciones | Supervisor, Administrador | ⚠️ Solo `user_has_server_access` | MEDIA |
| Finanzas | Supervisor, Administrador | ✅ RBAC v2 en cargos/responsabilidad | BAJA |
| Producción | Supervisor, Administrador | ⚠️ Sin validación específica | MEDIA |
| Recursos Humanos | Supervisor, Administrador | ⚠️ Parcial | MEDIA |
| Centro de Control | Administrador, Supervisor, Director | ⚠️ Sin validación específica | MEDIA |
| Servidores | Administrador | ✅ Verificación CORE/DATA_SOURCE | BAJA |
| Catálogo SQL | Supervisor, Administrador | ⚠️ Sin validación específica | BAJA |
| Explorador BD | Administrador | ✅ Verificación de permisos | BAJA |
| Usuarios | Administrador | ✅ `_get_role_level` | BAJA |

### 5.2 TABS SIN VALIDACIÓN BACKEND

| Pantalla | Tab | Backend Valida? | Criticidad |
|----------|-----|-----------------|------------|
| Compras | Análisis | ⚠️ NO | MEDIA |
| Compras | Auditoría | ⚠️ NO | MEDIA |
| Compras | Calculadora | ⚠️ NO | BAJA |
| RH | Nóminas | ⚠️ NO | MEDIA |
| RH | Reclutamiento | ⚠️ NO | BAJA |
| Finanzas | Dashboard | ⚠️ NO | MEDIA |
| Finanzas | Presupuestos | ⚠️ NO | BAJA |

### 5.3 ACCIONES SIN VALIDACIÓN BACKEND

| Módulo | Acción | Backend Valida? | Criticidad |
|--------|--------|-----------------|------------|
| Compras | Ejecutar detector | ✅ SÍ (role check) | N/A |
| Compras | Autorizar gerencia | ✅ SÍ (role check) | N/A |
| Compras | Autorizar tesorería | ✅ SÍ (role check) | N/A |
| Finanzas | Crear cargo | ✅ SÍ (RBAC v2) | N/A |
| Finanzas | Autorizar cargo | ✅ SÍ (RBAC v2) | N/A |
| RH | Aprobar nómina | ⚠️ NO explícito | ALTA |
| RH | Autorizar DG | ⚠️ NO explícito | ALTA |
| Inventarios | Exportar | ⚠️ NO | MEDIA |
| Reportes | Generar PDF | ⚠️ NO | BAJA |
| Alertas | Crear/Editar/Eliminar | ⚠️ NO | MEDIA |

### 5.4 ENDPOINTS SIN VALIDACIÓN EXPLÍCITA (122 identificados)

**ALTA CRITICIDAD (requieren atención):**
```
/rrhh/nominas/flujo/{flujo_id}/autorizar-dg
/rrhh/nominas/flujo/{flujo_id}/validar-gerente
/rrhh/nominas/flujo/{flujo_id}/marcar-pagado
/compras/parametros (edición)
/finanzas/presupuestos (CRUD)
/alerts (CRUD)
```

**MEDIA CRITICIDAD:**
```
/compras/dashboard/{server_id}
/compras/analisis
/compras/auditoria-operativa
/rrhh/dashboard
/rrhh/catalogos/* (edición)
/reports/* (exportaciones)
```

**BAJA CRITICIDAD:**
```
/debug/*
/sistema/sql-health
/test-api-connection
/dashboard/metrics (solo lectura)
```

---

## 6. PILOTO EN FINANZAS: ANÁLISIS DETALLADO

### 6.1 ESTADO ACTUAL DE FINANZAS

**YA TIENE RBAC v2 PARCIALMENTE IMPLEMENTADO:**
- Cargos Económicos: ✅ Usa `rbac_permisos`
- Responsabilidad Económica: ✅ Usa `rbac_permisos`
- Dashboard Finanzas: ⚠️ NO tiene validación
- Presupuestos: ⚠️ NO tiene validación
- Propinas: ⚠️ NO tiene validación

### 6.2 POR QUÉ FINANZAS NO ES BUEN PILOTO AMPLIO

| Razón | Explicación |
|-------|-------------|
| Módulo crítico | Afecta flujo de dinero |
| Ya tiene RBAC parcial | Mezclaría dos sistemas |
| Dependencias complejas | Interactúa con RH (nóminas) |
| Alto riesgo de regresión | Cargos económicos ya funcionan |

### 6.3 PROPUESTA ALTERNATIVA DE PILOTO

**OPCIÓN A: Piloto en módulo NO CRÍTICO**
- Candidato: **Alertas** o **Catálogo SQL**
- Razón: Bajo impacto si falla
- Alcance: Solo lectura/escritura de configuraciones

**OPCIÓN B: Piloto en submódulo aislado de Finanzas**
- Candidato: **Presupuestos** (actualmente sin validación)
- Razón: No afecta cargos económicos ya funcionando
- Alcance: Solo CRUD de presupuestos

**OPCIÓN C: No hacer piloto todavía**
- Esperar a que Fase 1 esté validada
- Definir piloto cuando haya más claridad

### 6.4 ALCANCE SI SE ELIGE OPCIÓN B (Presupuestos)

```
PANTALLA: /finanzas (tab Presupuestos)

ENDPOINTS AFECTADOS:
├── GET /api/finanzas/presupuestos
├── POST /api/finanzas/presupuestos
├── PUT /api/finanzas/presupuestos/{id}
└── DELETE /api/finanzas/presupuestos/{id}

MIDDLEWARE AFECTADO:
└── Agregar verificación de permiso FINANZAS_PRESUPUESTOS_*

ROLLBACK:
└── Remover verificación, volver a estado actual (sin validación)

RIESGO:
└── BAJO - actualmente no tiene validación, cualquier cambio es mejora
```

---

## 7. TABLA DE COMPATIBILIDAD LEGACY

### 7.1 MAPEO DE ROLES

| Rol Legacy (`roles`) | Rol RBAC v2 (`rbac_roles`) | Rol Propuesto (`sec_roles_v2`) | Nivel |
|---------------------|---------------------------|-------------------------------|-------|
| SuperAdministrador | ADMIN | SUPER_ADMIN | 100 |
| Administrador | ADMIN | ADMIN | 90 |
| - | DIRECCION | DIRECCION | 80 |
| - | GERENTE_OPS | GERENTE | 70 |
| Supervisor | SUPERVISOR | SUPERVISOR | 50 |
| - | AUDITOR | AUDITOR | 40 |
| Usuario | OPERADOR | OPERADOR | 30 |
| - | - | CONSULTA | 10 |

### 7.2 MAPEO DE PERMISOS

| Permiso Legacy (`roles.permisos`) | Permiso RBAC v2 (`rbac_permisos`) | Permiso Propuesto |
|----------------------------------|-----------------------------------|-------------------|
| tablero_ejecutivo | - | COMERCIAL_TABLERO_VER |
| comercial | - | COMERCIAL_* |
| compras | - | COMPRAS_* |
| inventarios | - | INVENTARIOS_* |
| finanzas | CARGOS_VER, etc. | FINANZAS_* |
| recursos_humanos | - | RH_* |
| usuarios | USUARIOS_VER, USUARIOS_GESTIONAR | SISTEMA_USUARIOS_* |
| servidores | - | SISTEMA_SERVIDORES_* |
| catalogo_sql | - | SISTEMA_CATALOGO_SQL_* |
| explorador_bd | - | SISTEMA_EXPLORADOR_BD_* |
| alertas | - | SISTEMA_ALERTAS_* |
| - | CARGOS_CREAR | FINANZAS_CARGOS_CREAR |
| - | CARGOS_AUTORIZAR | FINANZAS_CARGOS_AUTORIZAR |
| - | CARGOS_APLICAR | FINANZAS_CARGOS_APLICAR |
| - | RESPONSABILIDAD_VER | FINANZAS_RESPONSABILIDAD_VER |
| - | WORKFLOW_VER | OPERATIVO_WORKFLOW_VER |
| - | TAREAS_VER | OPERATIVO_TAREAS_VER |

### 7.3 ESTRATEGIA DE COEXISTENCIA

```
DURANTE MIGRACIÓN (Fases 2-4):

1. Usuario hace login
2. Sistema carga:
   - user.role (legacy)
   - user.allowed_servers (legacy)
   - sec_usuarios_roles (nuevo, si existe)
   - sec_usuarios_contexto (nuevo, si existe)
   
3. Middleware verifica:
   - PRIMERO: sistema legacy (garantiza compatibilidad)
   - SEGUNDO: sistema nuevo (si está activo para ese módulo)
   
4. Regla: Si legacy permite, se permite
         Si legacy niega, verificar nuevo
         Si nuevo permite, se permite
         Si ambos niegan, se niega

5. Bitácora registra ambas verificaciones
```

---

## 8. CHECKLIST DE NO REGRESIÓN

### 8.1 PRE-CAMBIO (Obligatorio antes de cualquier modificación)

- [ ] Backup completo de MongoDB
- [ ] Snapshot de colecciones: users, roles, rbac_roles, rbac_permisos
- [ ] Documentar estado actual de permisos de 3 usuarios de prueba
- [ ] Verificar acceso de SuperAdministrador a todos los módulos
- [ ] Verificar acceso de Usuario a sus servidores asignados
- [ ] Capturar screenshot de menús visibles por rol

### 8.2 POST-CAMBIO (Obligatorio después de cualquier modificación)

#### A. Autenticación
- [ ] Login con SuperAdministrador funciona
- [ ] Login con Administrador funciona
- [ ] Login con Supervisor funciona
- [ ] Login con Usuario funciona
- [ ] Token JWT se genera correctamente
- [ ] Token expira según configuración

#### B. Menús y Navegación
- [ ] SuperAdmin ve todos los menús
- [ ] Administrador ve menús según permisos
- [ ] Supervisor ve menús según permisos
- [ ] Usuario ve menús según permisos
- [ ] No hay menús duplicados
- [ ] No hay menús rotos

#### C. Dashboards
- [ ] Tablero Ejecutivo carga datos
- [ ] Dashboard Comercial carga datos
- [ ] Dashboard Compras carga datos
- [ ] Dashboard Finanzas carga datos
- [ ] Dashboard Inventarios carga datos
- [ ] Dashboard RH carga datos

#### D. Filtros
- [ ] Filtro por servidor funciona
- [ ] Filtro por sucursal funciona
- [ ] Filtro por fecha funciona
- [ ] Filtro por categoría funciona
- [ ] Usuario solo ve sus servidores asignados

#### E. Operaciones Críticas
- [ ] Crear cargo económico funciona
- [ ] Autorizar cargo funciona
- [ ] Crear tarea funciona
- [ ] Completar tarea funciona
- [ ] Ejecutar detector de compras funciona
- [ ] Exportar a Excel funciona
- [ ] Exportar a PDF funciona

#### F. Integraciones
- [ ] Conexión a SoftRestaurant funciona
- [ ] Conexión a MPRO funciona
- [ ] Consultas SQL ejecutan correctamente
- [ ] No hay timeouts nuevos

### 8.3 CRITERIOS DE ROLLBACK INMEDIATO

Si cualquiera de estos falla, DETENER y hacer rollback:

1. ❌ Login no funciona para ningún rol
2. ❌ Dashboard principal muestra error
3. ❌ Cálculo de ventas da resultados diferentes
4. ❌ Usuario admin no puede ver todos los servidores
5. ❌ Queries SQL fallan masivamente
6. ❌ Más de 3 endpoints retornan 500
7. ❌ Frontend muestra pantalla en blanco

---

## 9. DECISIÓN SOLICITADA

### 9.1 APROBACIÓN DE FASE 1 RESTRINGIDA

**SOLICITO APROBACIÓN PARA:**

| Item | Acción | Riesgo |
|------|--------|--------|
| 1 | Crear colección `sec_permisos_catalogo` (vacía) | CERO |
| 2 | Crear colección `sec_modulos_sistema` (vacía) | CERO |
| 3 | Crear colección `sec_bitacora_acceso` (vacía) | CERO |
| 4 | Poblar catálogo de permisos (INSERT datos) | CERO |
| 5 | Poblar catálogo de módulos (INSERT datos) | CERO |
| 6 | Crear funciones helper SIN ACTIVAR | CERO |
| 7 | Documentar mapeo legacy → nuevo | CERO |

**NO SOLICITO APROBACIÓN PARA (queda diferido):**
- Migrar usuarios
- Modificar middleware
- Activar lógica nueva
- Tocar módulos existentes
- Piloto en Finanzas
- Cualquier cambio transversal

### 9.2 SIGUIENTE PASO PROPUESTO

Si Fase 1 se aprueba y ejecuta exitosamente:
1. Validar que no hubo regresiones
2. Documentar resultado
3. Solicitar aprobación para Fase 2 con plan detallado específico

---

## ANEXO: ESTRUCTURA DE COLECCIONES FASE 1

### sec_permisos_catalogo
```javascript
{
  _id: ObjectId,
  codigo: "COMERCIAL_DASHBOARD_VER",
  modulo: "comercial",
  submodulo: "dashboard",
  accion: "ver",
  descripcion: "Ver dashboard comercial",
  activo: true,
  created_at: ISODate
}
// Índices: codigo (unique), modulo, activo
```

### sec_modulos_sistema
```javascript
{
  _id: ObjectId,
  codigo: "comercial",
  nombre: "Comercial",
  descripcion: "Módulo de gestión comercial",
  icono: "TrendingUp",
  orden: 1,
  activo: true,
  created_at: ISODate
}
// Índices: codigo (unique), activo
```

### sec_bitacora_acceso
```javascript
{
  _id: ObjectId,
  timestamp: ISODate,
  usuario_id: "uuid",
  usuario_email: "string",
  accion: "LOGIN|ACCESO_ENDPOINT|PERMISO_DENEGADO",
  recurso: "/api/comercial/dashboard/xxx",
  metodo: "GET",
  resultado: "PERMITIDO|DENEGADO",
  ip: "string",
  detalles: {},
  sistema_verificacion: "LEGACY|NUEVO|AMBOS"
}
// Índices: timestamp, usuario_id, accion, resultado
// TTL: 90 días (configurable)
```

---

**FIN DEL DOCUMENTO v2.0**

*Esperando aprobación para proceder con Fase 1 Restringida.*
