# ARQUITECTURA DE SEGURIDAD EDARSA HUB
## Diagnóstico, Diseño y Plan de Migración

**Versión:** 1.0  
**Fecha:** Diciembre 2025  
**Autor:** Arquitecto de Software Senior  
**Estado:** PENDIENTE APROBACIÓN

---

## TABLA DE CONTENIDOS

1. [Diagnóstico del Sistema Actual](#1-diagnóstico-del-sistema-actual)
2. [Gap Analysis](#2-gap-analysis)
3. [Modelo Objetivo (Diseño)](#3-modelo-objetivo-diseño)
4. [Plan de Migración](#4-plan-de-migración)
5. [Riesgos y Mitigaciones](#5-riesgos-y-mitigaciones)
6. [Checklist de No Regresión](#6-checklist-de-no-regresión)
7. [Diseño de UI](#7-diseño-de-ui)
8. [Aprobación Requerida](#8-aprobación-requerida)

---

## 1. DIAGNÓSTICO DEL SISTEMA ACTUAL

### 1.1 Colecciones de Seguridad en MongoDB

| Colección | Documentos | Propósito | Estado |
|-----------|------------|-----------|--------|
| `users` | 16 | Usuarios del sistema | ACTIVA |
| `roles` | 4 | Roles básicos (legacy) | ACTIVA |
| `rbac_roles` | 6 | Roles RBAC v2 | PARCIAL |
| `rbac_permisos` | 43 | Permisos granulares | PARCIAL |
| `rbac_usuarios_roles` | 0 | Asignación usuario-rol RBAC | NO USADO |
| `rbac_audit_log` | 370 | Auditoría de accesos | ACTIVA |
| `permisos_catalogos` | 2 | Permisos específicos catálogos | ACTIVA |

### 1.2 Modelo de Usuario Actual

```javascript
// Estructura actual de usuario (colección: users)
{
  id: "uuid",
  email: "string",
  name: "string",
  role: "string",           // UN solo rol (legacy)
  sucursales: [],           // Deprecado
  allowed_servers: [],      // Servidores permitidos
  allowed_sucursales: {},   // {server_id: [sucursal_ids]}
  allowed_warehouses: {},   // {server_id: [almacen_ids]}
  active: true,
  created_at: "ISO date"
}
```

**Problemas identificados:**
- Solo permite UN rol por usuario
- No hay relación formal con empresas/unidades de negocio
- Permisos dispersos en múltiples campos
- No existe concepto de perfil reutilizable
- No hay topes de autorización

### 1.3 Modelo de Roles Actual

```javascript
// Colección: roles (legacy)
{
  id: "uuid",
  nombre: "Administrador|Supervisor|Usuario|SuperAdministrador",
  descripcion: "string",
  permisos: ["tablero_ejecutivo", "comercial", ...],  // Permisos de módulo
  es_sistema: true,
  created_at: "ISO date"
}

// Colección: rbac_roles (v2 - parcialmente implementado)
{
  nombre: "ADMIN|DIRECCION|GERENTE_OPS|SUPERVISOR|OPERADOR|AUDITOR",
  descripcion: "string",
  permisos: ["CARGOS_VER", "CARGOS_CREAR", ...],  // Permisos granulares
  nivel_jerarquia: 100|80|60|40|20|30,
  es_sistema: true,
  activo: true
}
```

**Coexisten DOS sistemas de roles:**
1. `roles`: Sistema legacy con permisos de módulo
2. `rbac_roles`: Sistema v2 con permisos granulares (parcialmente usado)

### 1.4 Permisos Actuales por Módulo

| Módulo | Permisos RBAC v2 | Usado en Backend |
|--------|------------------|------------------|
| cargos | CARGOS_VER, CARGOS_CREAR, CARGOS_AUTORIZAR, CARGOS_APLICAR, CARGOS_RECHAZAR, CARGOS_REVERTIR, CARGOS_CANCELAR | SÍ |
| responsabilidad | RESPONSABILIDAD_VER, RESPONSABILIDAD_CALCULAR, RESPONSABILIDAD_PROPONER, etc. | SÍ |
| auditorias | AUDITORIA_VER, AUDITORIA_PROGRAMAR, AUDITORIA_GESTIONAR | SÍ |
| auth | USUARIOS_VER, USUARIOS_GESTIONAR, ROLES_VER, ROLES_GESTIONAR, RBAC_ADMIN | SÍ |
| workflow | WORKFLOW_VER, WORKFLOW_CREAR, WORKFLOW_GESTIONAR, WORKFLOW_CERRAR | SÍ |
| scheduler | SCHEDULER_VER, SCHEDULER_GESTIONAR, SCHEDULER_ADMIN | SÍ |
| reportes | REPORTES_VER, REPORTES_EXPORTAR | PARCIAL |
| operativo | TAREAS_VER, TAREAS_CREAR, TAREAS_ASIGNAR, TAREAS_COMPLETAR | PARCIAL |
| notificaciones | NOTIFICACIONES_VER, NOTIFICACIONES_ENVIAR, NOTIFICACIONES_CONFIGURAR | PARCIAL |
| sla | SLA_VER, SLA_CONFIGURAR | PARCIAL |
| configuracion | CONFIG_VER, CONFIG_EDITAR | PARCIAL |

### 1.5 Middleware de Autorización en Backend

**Archivo:** `/app/backend/core/security.py`

```python
# Funciones principales de autorización:

def user_has_server_access(user, server_id) -> bool:
    # SuperAdministrador y Administrador tienen acceso full
    if user.get('role') in ['SuperAdministrador', 'Administrador']:
        return True
    allowed = user.get('allowed_servers', [])
    return server_id in allowed

def filter_servers_by_permissions(servers, user) -> List:
    # SuperAdmin/Admin ven todo
    if user.get('role') in ['SuperAdministrador', 'Administrador']:
        return servers
    allowed = user.get('allowed_servers', [])
    return [s for s in servers if s.get('id') in allowed]
```

**Jerarquía de roles implementada:**
```python
ROLE_HIERARCHY = {
    'Usuario': 1,
    'Supervisor': 2,
    'Administrador': 3,
    'SuperAdministrador': 100
}
```

### 1.6 Validaciones de Seguridad Identificadas

| Archivo | Línea | Tipo de Validación | Roles Permitidos |
|---------|-------|-------------------|------------------|
| `auth/service.py` | 270 | Gestión usuarios | Administrador, SuperAdmin (nivel >= 3) |
| `auth/service.py` | 265 | Ver roles | Administrador, SuperAdmin (nivel >= 3) |
| `comercial/routes.py` | 137 | Acceso servidor | Verificación `user_has_server_access()` |
| `comercial/routes.py` | 307 | Filtros especiales | Administrador |
| `fase2_operativo/.../routes.py` | 100-102 | Detector compras | Administrador, Gerente, Director |
| `fase2_operativo/.../service.py` | 297 | Autorización cargos | Gerente, Director, Administrador |
| `fase2_operativo/.../service.py` | 361 | Autorización tesorería | Tesoreria, Director, Administrador |

### 1.7 Lógica de Visibilidad en Frontend

**Archivo:** `/app/frontend/src/pages/Layout.js`

```javascript
// Menús definidos estáticamente con roles permitidos
const modulos = [
  { name: 'Tablero Ejecutivo', href: '/tablero', 
    roles: ['Usuario', 'Supervisor', 'Administrador'], permiso: 'tablero_ejecutivo' },
  { name: 'Comercial', href: '/comercial', 
    roles: ['Usuario', 'Supervisor', 'Administrador'], permiso: 'comercial' },
  // ...
];

// Filtrado de menús
const hasAccess = (item) => {
  if (item.roles?.includes(user?.role)) return true;
  if (item.permiso && userPermissions.includes(item.permiso)) return true;
  if (user?.role?.includes('admin') || user?.role?.includes('super')) return true;
  return false;
};
```

**Problemas:**
- Validación en frontend NO es seguridad real
- Roles hardcodeados en arrays
- Lógica dispersa y poco mantenible

### 1.8 Distribución de Usuarios por Rol

| Rol | Cantidad | Descripción |
|-----|----------|-------------|
| SuperAdministrador | 1 | Rol máximo (Ricardo) |
| Administrador | 5 | Acceso total |
| Supervisor | 3 | Acceso limitado |
| Usuario | 5 | Acceso básico |
| Admin (legacy) | 1 | Rol inconsistente |

### 1.9 Dependencias entre Módulos

```
MÓDULOS QUE DEPENDEN DE SEGURIDAD:
├── Comercial
│   └── Valida: allowed_servers, role
├── Compras
│   └── Valida: role (Gerente, Director, Administrador)
├── Operativo (Fase2)
│   └── Valida: RBAC v2 permisos granulares
├── Finanzas
│   ├── Cargos Económicos → RBAC v2
│   └── Responsabilidad → RBAC v2
├── RH
│   └── Valida: role (Administrador)
├── Catálogos
│   └── Valida: permisos_catalogos collection
└── Servidores
    └── Valida: allowed_servers, tipo_conexion (CORE/DATA_SOURCE)
```

---

## 2. GAP ANALYSIS

### 2.1 Funcionalidades Ausentes

| Requerimiento | Estado Actual | Gap |
|---------------|---------------|-----|
| Múltiples roles por usuario | 1 rol único | CRÍTICO |
| Perfiles reutilizables | No existe | CRÍTICO |
| Permisos por menú/tab/acción | Parcial en RBAC v2 | ALTO |
| Alcance por empresa/unidad | Solo por servidor | ALTO |
| Topes de autorización | No existe | MEDIO |
| Overrides por usuario | No existe | MEDIO |
| Auditoría completa | Solo en RBAC v2 | ALTO |
| Sesiones activas | No existe | BAJO |

### 2.2 Inconsistencias Detectadas

1. **Dos sistemas de roles paralelos:** `roles` vs `rbac_roles`
2. **Permisos legacy vs granulares:** Sin migración completa
3. **Frontend valida sin backend:** Riesgo de seguridad
4. **Roles hardcodeados:** En múltiples archivos
5. **Eje de seguridad incorrecto:** Basado en `server_id` en lugar de `empresa_id`

### 2.3 Riesgos de Seguridad

| Riesgo | Severidad | Descripción |
|--------|-----------|-------------|
| Frontend como control | CRÍTICO | UI oculta pero endpoint accesible |
| Sin auditoría completa | ALTO | Solo RBAC v2 tiene logs |
| Roles inconsistentes | MEDIO | "Admin" vs "Administrador" |
| Sin timeout de sesión | MEDIO | JWT de 72 horas |

---

## 3. MODELO OBJETIVO (DISEÑO)

### 3.1 Arquitectura de Colecciones

```
COLECCIONES DE SEGURIDAD (OBJETIVO):
├── sec_usuarios (migrar de users)
├── sec_roles
├── sec_perfiles_acceso (NUEVO)
├── sec_permisos
├── sec_roles_permisos
├── sec_perfiles_permisos (NUEVO)
├── sec_usuarios_roles
├── sec_usuarios_perfiles (NUEVO)
├── sec_usuarios_permisos_override (NUEVO)
├── sec_usuarios_contexto_acceso (NUEVO)
├── sec_usuarios_limites_autorizacion (NUEVO)
├── sec_modulos_sistema
├── sec_pantallas_sistema
├── sec_tabs_sistema (NUEVO)
├── sec_acciones_sistema
├── sec_bitacora
└── sec_sesiones (NUEVO)
```

### 3.2 Modelo de Datos Objetivo

#### sec_usuarios
```javascript
{
  id: "uuid",
  email: "string",
  nombre: "string",
  password_hash: "string",
  activo: true,
  bloqueado: false,
  intentos_fallidos: 0,
  ultimo_login: "ISO date",
  created_at: "ISO date",
  updated_at: "ISO date",
  created_by: "uuid"
}
```

#### sec_roles
```javascript
{
  id: "uuid",
  codigo: "SUPER_ADMIN|ADMIN|GERENTE|SUPERVISOR|OPERADOR|AUDITOR",
  nombre: "string",
  descripcion: "string",
  nivel_jerarquia: 100,  // Mayor = más privilegios
  es_sistema: true,      // No editable/eliminable
  activo: true,
  created_at: "ISO date"
}
```

#### sec_perfiles_acceso (NUEVO)
```javascript
{
  id: "uuid",
  codigo: "PERFIL_COMERCIAL|PERFIL_COMPRAS|PERFIL_FINANZAS|...",
  nombre: "string",
  descripcion: "string",
  es_sistema: false,
  activo: true,
  created_at: "ISO date"
}
```

#### sec_permisos
```javascript
{
  id: "uuid",
  codigo: "MODULO_PANTALLA_TAB_ACCION",
  modulo: "comercial|compras|finanzas|...",
  pantalla: "dashboard|listado|detalle|...",
  tab: "general|detalle|historial|...",  // nullable
  accion: "ver|crear|editar|eliminar|autorizar|...",
  descripcion: "string",
  es_sistema: true,
  activo: true
}
```

#### sec_usuarios_contexto_acceso (NUEVO)
```javascript
{
  id: "uuid",
  usuario_id: "uuid",
  tipo_contexto: "empresa|unidad_negocio|sucursal|almacen",
  contexto_id: "uuid",
  activo: true,
  created_at: "ISO date",
  created_by: "uuid"
}
```

#### sec_usuarios_limites_autorizacion (NUEVO)
```javascript
{
  id: "uuid",
  usuario_id: "uuid",
  tipo_limite: "monto_maximo|cantidad_maxima|nivel_aprobacion",
  valor: 50000.00,
  moneda: "MXN",
  contexto: "cargos_economicos|ordenes_compra|...",
  activo: true,
  created_at: "ISO date"
}
```

#### sec_bitacora
```javascript
{
  id: "uuid",
  usuario_id: "uuid",
  usuario_email: "string",
  accion: "LOGIN|LOGOUT|PERMISO_DENEGADO|CAMBIO_ROL|...",
  permiso_requerido: "string",
  resultado: "PERMITIDO|DENEGADO",
  endpoint: "string",
  metodo_http: "GET|POST|PUT|DELETE",
  ip_address: "string",
  user_agent: "string",
  detalles: {},
  fecha: "ISO date"
}
```

#### sec_sesiones (NUEVO)
```javascript
{
  id: "uuid",
  usuario_id: "uuid",
  token_hash: "string",
  ip_address: "string",
  user_agent: "string",
  created_at: "ISO date",
  expires_at: "ISO date",
  activa: true,
  cerrada_por: "LOGOUT|TIMEOUT|ADMIN|OTRO_LOGIN"
}
```

### 3.3 Reglas de Negocio

```
ACUMULACIÓN DE PERMISOS:
├── Usuario hereda permisos de todos sus roles
├── Usuario hereda permisos de todos sus perfiles
├── Permisos se ACUMULAN (union)
├── Override DENY tiene prioridad sobre ALLOW
└── SuperAdministrador SIEMPRE tiene acceso total

JERARQUÍA DE CONTEXTO:
├── Grupo Empresarial (nivel 0)
│   ├── Empresa (nivel 1)
│   │   ├── Unidad de Negocio (nivel 2)
│   │   │   ├── Sucursal (nivel 3)
│   │   │   │   └── Almacén (nivel 4)

VALIDACIÓN DE ACCESO:
1. Verificar sesión activa
2. Verificar usuario activo y no bloqueado
3. Verificar permiso requerido
4. Verificar contexto (empresa/sucursal)
5. Verificar límites de autorización (si aplica)
6. Registrar en bitácora
```

### 3.4 Permisos por Módulo (Diseño Completo)

#### Módulo: Comercial
```
COMERCIAL_DASHBOARD_VER
COMERCIAL_METAS_VER
COMERCIAL_METAS_EDITAR
COMERCIAL_TICKET_PERFECTO_VER
COMERCIAL_VENTAS_VER
COMERCIAL_VENTAS_EXPORTAR
COMERCIAL_PAX_VER
COMERCIAL_MESAS_VER
COMERCIAL_DETALLE_MOVIMIENTOS_VER
COMERCIAL_PRECIOS_CONSTANTES_VER
```

#### Módulo: Compras
```
COMPRAS_DASHBOARD_VER
COMPRAS_AUTOMATIZACION_VER
COMPRAS_AUTOMATIZACION_EJECUTAR
COMPRAS_TAREAS_VER
COMPRAS_TAREAS_CREAR
COMPRAS_TAREAS_ASIGNAR
COMPRAS_TAREAS_COMPLETAR
COMPRAS_GERENCIA_AUTORIZAR
COMPRAS_TESORERIA_AUTORIZAR
COMPRAS_PARAMETROS_EDITAR
```

#### Módulo: Inventarios
```
INVENTARIOS_DASHBOARD_VER
INVENTARIOS_ANALISIS_VER
INVENTARIOS_ANALISIS_EJECUTAR
INVENTARIOS_DIFERENCIAS_VER
INVENTARIOS_JUSTIFICACIONES_VER
INVENTARIOS_JUSTIFICACIONES_CREAR
INVENTARIOS_EXPORTAR
```

#### Módulo: Finanzas
```
FINANZAS_DASHBOARD_VER
FINANZAS_CARGOS_VER
FINANZAS_CARGOS_CREAR
FINANZAS_CARGOS_AUTORIZAR
FINANZAS_CARGOS_APLICAR
FINANZAS_CARGOS_RECHAZAR
FINANZAS_CARGOS_REVERTIR
FINANZAS_RESPONSABILIDAD_VER
FINANZAS_RESPONSABILIDAD_CALCULAR
FINANZAS_RESPONSABILIDAD_APROBAR
FINANZAS_RESPONSABILIDAD_EXONERAR
FINANZAS_PROPINAS_VER
FINANZAS_PROPINAS_EDITAR
```

#### Módulo: Operativo
```
OPERATIVO_TAREAS_VER
OPERATIVO_TAREAS_CREAR
OPERATIVO_TAREAS_ASIGNAR
OPERATIVO_TAREAS_COMPLETAR
OPERATIVO_SLA_VER
OPERATIVO_SLA_CONFIGURAR
OPERATIVO_WORKFLOW_VER
OPERATIVO_WORKFLOW_CREAR
OPERATIVO_WORKFLOW_CERRAR
```

#### Módulo: RH
```
RH_NOMINA_VER
RH_NOMINA_IMPORTAR
RH_NOMINA_APROBAR
RH_CATALOGOS_VER
RH_CATALOGOS_EDITAR
RH_EMPLEADOS_VER
RH_EMPLEADOS_EDITAR
```

#### Módulo: Sistema
```
SISTEMA_USUARIOS_VER
SISTEMA_USUARIOS_CREAR
SISTEMA_USUARIOS_EDITAR
SISTEMA_USUARIOS_ELIMINAR
SISTEMA_ROLES_VER
SISTEMA_ROLES_CREAR
SISTEMA_ROLES_EDITAR
SISTEMA_ROLES_ELIMINAR
SISTEMA_PERFILES_VER
SISTEMA_PERFILES_CREAR
SISTEMA_PERFILES_EDITAR
SISTEMA_PERFILES_ELIMINAR
SISTEMA_SERVIDORES_VER
SISTEMA_SERVIDORES_CREAR
SISTEMA_SERVIDORES_EDITAR
SISTEMA_SERVIDORES_ELIMINAR
SISTEMA_ALERTAS_VER
SISTEMA_ALERTAS_CREAR
SISTEMA_AUDITORIA_VER
SISTEMA_SESIONES_VER
SISTEMA_SESIONES_CERRAR
```

---

## 4. PLAN DE MIGRACIÓN

### 4.1 Fases de Implementación

```
FASE 1: PREPARACIÓN (Semana 1-2)
├── Crear colecciones sec_* vacías
├── Crear índices necesarios
├── Implementar funciones de compatibilidad
└── NO afectar sistema actual

FASE 2: CAPA DE COMPATIBILIDAD (Semana 3-4)
├── Crear middleware que consulte AMBOS sistemas
├── Migrar permisos existentes a nueva estructura
├── Mantener sistema legacy funcionando
└── Logs de comparación (nuevo vs legacy)

FASE 3: MIGRACIÓN DE DATOS (Semana 5)
├── Migrar usuarios a sec_usuarios
├── Crear roles en sec_roles
├── Crear perfiles base en sec_perfiles_acceso
├── Asignar usuarios a roles
└── Preservar allowed_servers → contexto_acceso

FASE 4: PILOTO (Semana 6-7)
├── Activar nuevo sistema en módulo FINANZAS
├── Validar cargos económicos con RBAC nuevo
├── Validar responsabilidad económica
├── Monitorear bitácora
└── Rollback si hay problemas

FASE 5: EXPANSIÓN (Semana 8-10)
├── Activar en COMPRAS
├── Activar en OPERATIVO
├── Activar en COMERCIAL
├── Activar en RH
└── Desactivar sistema legacy

FASE 6: LIMPIEZA (Semana 11-12)
├── Remover código legacy
├── Remover colecciones obsoletas
├── Documentar sistema final
└── Capacitación usuarios
```

### 4.2 Scripts de Migración (Conceptual)

```javascript
// Fase 3: Migración de usuarios
async function migrateUsers() {
  const users = await db.users.find({}).toArray();
  
  for (const user of users) {
    // Crear en nueva colección
    await db.sec_usuarios.insertOne({
      id: user.id,
      email: user.email,
      nombre: user.name,
      password_hash: user.password,
      activo: user.active,
      // ... campos adicionales
    });
    
    // Migrar rol a asignación
    const roleMap = {
      'SuperAdministrador': 'SUPER_ADMIN',
      'Administrador': 'ADMIN',
      'Supervisor': 'SUPERVISOR',
      'Usuario': 'OPERADOR'
    };
    
    const newRoleCode = roleMap[user.role] || 'OPERADOR';
    const role = await db.sec_roles.findOne({ codigo: newRoleCode });
    
    await db.sec_usuarios_roles.insertOne({
      usuario_id: user.id,
      rol_id: role.id,
      activo: true
    });
    
    // Migrar allowed_servers a contexto
    for (const serverId of (user.allowed_servers || [])) {
      await db.sec_usuarios_contexto_acceso.insertOne({
        usuario_id: user.id,
        tipo_contexto: 'servidor',  // Temporal, migrar a empresa después
        contexto_id: serverId,
        activo: true
      });
    }
  }
}
```

---

## 5. RIESGOS Y MITIGACIONES

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|--------|--------------|---------|------------|
| 1 | Romper dashboards existentes | MEDIA | CRÍTICO | Feature flags, rollback inmediato |
| 2 | Perder accesos actuales | BAJA | CRÍTICO | Migración con preservación total |
| 3 | Inconsistencia durante migración | ALTA | MEDIO | Capa de compatibilidad |
| 4 | Performance degradado | MEDIA | MEDIO | Índices, cache |
| 5 | Usuarios confundidos | MEDIA | BAJO | Capacitación, documentación |

### 5.1 Estrategia de Rollback

```
CADA FASE tiene rollback independiente:

Fase 1: Eliminar colecciones sec_* (sin impacto)
Fase 2: Desactivar middleware nuevo (instantáneo)
Fase 3: Restaurar backup de MongoDB
Fase 4: Revertir feature flag
Fase 5: Revertir feature flags por módulo
```

---

## 6. CHECKLIST DE NO REGRESIÓN

### 6.1 Antes de Cada Cambio

- [ ] Backup completo de MongoDB
- [ ] Listar endpoints afectados
- [ ] Simular con usuario de cada rol
- [ ] Verificar logs de auditoría

### 6.2 Después de Cada Cambio

- [ ] Dashboard Comercial funciona
- [ ] Dashboard Compras funciona
- [ ] Dashboard Finanzas funciona
- [ ] Dashboard Inventarios funciona
- [ ] Filtros por sucursal funcionan
- [ ] Ventas se calculan correctamente
- [ ] Metas se muestran correctamente
- [ ] Usuarios existentes pueden loguearse
- [ ] SuperAdmin tiene acceso total
- [ ] Administradores ven todos los servidores
- [ ] Usuarios solo ven sus servidores asignados

### 6.3 Validación de Endpoints Críticos

```
/api/comercial/dashboard/{server_id} → Verificar acceso por rol
/api/comercial/metas/{server_id} → Verificar cálculos
/api/servers → Verificar filtrado por permisos
/api/auth/login → Verificar generación JWT
/api/users → Verificar CRUD usuarios
/api/roles → Verificar CRUD roles
/api/finanzas/cargos → Verificar autorizaciones
/api/compras/automatizacion → Verificar permisos
```

---

## 7. DISEÑO DE UI

### 7.1 Pantallas Requeridas

1. **Gestión de Usuarios**
   - Listado con filtros
   - Formulario crear/editar
   - Asignación de roles múltiples
   - Asignación de perfiles
   - Configuración de contexto (empresas/sucursales)
   - Límites de autorización

2. **Gestión de Roles**
   - Listado con jerarquía visual
   - Formulario crear/editar
   - Asignación de permisos (matriz)
   - Visualización de usuarios asignados

3. **Gestión de Perfiles**
   - Listado de perfiles
   - Formulario crear/editar
   - Asignación de permisos
   - Clonación de perfiles

4. **Matriz de Permisos**
   - Vista por módulo
   - Vista por rol
   - Vista por perfil
   - Edición en línea

5. **Alcance Organizacional**
   - Árbol de empresas/sucursales
   - Asignación a usuarios
   - Vista de cobertura

6. **Auditoría**
   - Logs de acceso
   - Logs de cambios
   - Filtros avanzados
   - Exportación

7. **Sesiones Activas**
   - Listado de sesiones
   - Forzar cierre
   - Estadísticas

---

## 8. APROBACIÓN REQUERIDA

### 8.1 Puntos de Decisión

| # | Decisión | Opciones | Recomendación |
|---|----------|----------|---------------|
| 1 | ¿Migrar a nuevo eje (empresa) o mantener servidor? | A) Empresa, B) Servidor | A) Empresa (largo plazo) |
| 2 | ¿Big bang o por fases? | A) Todo, B) Fases | B) Fases |
| 3 | ¿Prioridad de módulo piloto? | A) Finanzas, B) Compras, C) Comercial | A) Finanzas (ya tiene RBAC v2) |
| 4 | ¿Eliminar sistema legacy inmediatamente? | A) Sí, B) Coexistencia temporal | B) Coexistencia |
| 5 | ¿Implementar sesiones? | A) Ahora, B) Después | B) Después |

### 8.2 Autorización

**ANTES de proceder con cualquier implementación, se requiere:**

1. [ ] Aprobación del diseño de colecciones
2. [ ] Aprobación del plan de migración por fases
3. [ ] Confirmación del módulo piloto
4. [ ] Confirmación de recursos/tiempo disponible
5. [ ] Aprobación de riesgos aceptados

---

## ANEXOS

### A. Mapeo de Permisos Legacy → Nuevo

| Permiso Legacy | Nuevo Código | Módulo |
|----------------|--------------|--------|
| tablero_ejecutivo | COMERCIAL_DASHBOARD_VER | comercial |
| comercial | COMERCIAL_* | comercial |
| compras | COMPRAS_* | compras |
| inventarios | INVENTARIOS_* | inventarios |
| finanzas | FINANZAS_* | finanzas |
| recursos_humanos | RH_* | rh |
| usuarios | SISTEMA_USUARIOS_* | sistema |
| servidores | SISTEMA_SERVIDORES_* | sistema |

### B. Roles Predefinidos Propuestos

| Rol | Nivel | Permisos Incluidos |
|-----|-------|-------------------|
| SUPER_ADMIN | 100 | TODOS |
| ADMIN | 90 | Todos excepto config sistema core |
| DIRECTOR | 80 | Ver todo, autorizar alto nivel |
| GERENTE | 70 | Ver operaciones, autorizar medio |
| SUPERVISOR | 50 | Ver operaciones propias, validar |
| OPERADOR | 30 | Ver/crear en módulos asignados |
| AUDITOR | 40 | Ver todo, no editar |
| CONSULTA | 10 | Solo lectura |

---

**FIN DEL DOCUMENTO**

*Este documento requiere aprobación antes de cualquier implementación.*
