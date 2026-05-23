# CRM ENTERPRISE EDARSA HUB - DIAGNÓSTICO DE NO DUPLICIDAD

**Fecha:** 2026-05-23
**Generado por:** Agente E1 (Fase 0 - Diagnóstico Pasivo Obligatorio)

---

## 1. RESUMEN EJECUTIVO

Se realizó un análisis exhaustivo de la base de datos EDARSAHUB y la estructura del proyecto para identificar tablas existentes que puedan reutilizarse, evitando duplicidad.

### Hallazgos Principales:
- ✅ **Existen tablas de Clientes/Contactos** que pueden servir como base para CRM_Cuentas y CRM_Contactos
- ✅ **Existe sistema RBAC completo** (Usuario_Roles, Usuario_PermisosRolModulo, Usuario_Modulos)
- ✅ **Existe motor de actividades** (Usuario_LogActividades) - reutilizable
- ✅ **Existe módulo CRM parcial** (VTiger integration backend completo)
- ⚠️ **NO existe menú CRM** en frontend
- ⚠️ **NO existen tablas de Leads, Oportunidades, Pipeline** en EDARSAHUB

---

## 2. TABLAS EXISTENTES REVISADAS

### 2.1 Tablas de Clientes (REUTILIZABLES)

| Tabla | Equivalencia CRM | Acción |
|-------|------------------|--------|
| `Cliente_Catalogo` | CRM_Cuentas | **REUTILIZAR** - Tiene estructura base completa |
| `Cliente_Contactos` | CRM_Contactos | **REUTILIZAR** - Tiene campos esenciales |
| `Cliente_Direcciones` | CRM_Cuenta_Direcciones | **REUTILIZAR** |
| `Cliente_Grupos` | CRM_Cat_SegmentosCliente | **REUTILIZAR** |

**Estructura Cliente_Catalogo (30 campos):**
- ClienteID, CodigoCliente, RFC, CURP
- RazonSocial, NombreComercial, TipoPersona
- GrupoClienteID, MonedaID, LimiteCredito, DiasCredito
- EmailPrincipal, TelefonoPrincipal, SitioWeb
- Ciudad, Estado, Pais, CodigoPostalFiscal
- Activo, FechaAlta, FechaModificacion, CreatedBy

**Campos faltantes para CRM que se agregarán:**
- ejecutivo_principal_user_id
- gerente_comercial_user_id
- sector_id, subsector_id
- es_prospecto, es_partner, es_cuenta_estrategica
- fecha_ultima_interaccion
- riesgo_cuenta_id
- tamano_cliente_id

### 2.2 Tablas de Usuarios/Roles (REUTILIZAR 100%)

| Tabla | Uso | Acción |
|-------|-----|--------|
| `Usuario_Catalogo` | Usuarios del sistema | **REUTILIZAR** |
| `Usuario_Roles` | Roles RBAC | **REUTILIZAR** |
| `Usuario_Modulos` | Módulos del menú | **REUTILIZAR** - Agregar módulo CRM aquí |
| `Usuario_PermisosRolModulo` | Permisos RBAC | **REUTILIZAR** - Agregar permisos CRM |
| `Usuario_Acciones` | Acciones RBAC | **REUTILIZAR** |
| `Usuario_LogActividades` | Motor de actividades | **EVALUAR EXTENSIÓN** |

### 2.3 Tablas de Empresas (REUTILIZAR 100%)

| Tabla | Uso | Acción |
|-------|-----|--------|
| `Sistema_Empresas` | Empresas del holding | **REUTILIZAR** |
| `Sistema_Sucursales` | Sucursales | **REUTILIZAR** |
| `Unidades_Negocio` | Unidades operativas | **REUTILIZAR** |

### 2.4 Tablas de RH (CONSUMIR, NO DUPLICAR)

- `RH_Colaboradores` - Para asignación de ejecutivos
- `RH_Cat_Departamentos` - Departamentos
- `RH_Cat_Puestos` - Puestos
- No crear tablas duplicadas de empleados

### 2.5 Tablas de Documentos (EVALUAR REUTILIZACIÓN)

| Tabla | Uso Actual | Para CRM |
|-------|------------|----------|
| `Proveedor_Documentos` | Docs de proveedores | Patrón reutilizable |
| `Proveedor_TipoDocumento` | Catálogo tipos doc | Extender para CRM |
| `Compras_DocumentosFiscales` | CFDIs | Patrón reutilizable |

---

## 3. TABLAS QUE NO EXISTEN Y SE CREARÁN

### 3.1 Tablas Transaccionales CRM (NUEVAS)

| Tabla Nueva | Justificación |
|-------------|---------------|
| `CRM_Leads` | No existe equivalente - CREAR |
| `CRM_Oportunidades` | No existe equivalente - CREAR |
| `CRM_Propuestas` | No existe equivalente - CREAR |
| `CRM_PropuestasVersiones` | Control de versiones - CREAR |
| `CRM_Contratos` | No existe equivalente - CREAR |
| `CRM_Implementaciones` | No existe equivalente - CREAR |
| `CRM_Renovaciones` | No existe equivalente - CREAR |

### 3.2 Tablas de Configuración CRM (NUEVAS)

| Tabla Nueva | Justificación |
|-------------|---------------|
| `CRM_Config_Pipelines` | Pipelines configurables - CREAR |
| `CRM_Config_PipelineEtapas` | Etapas del pipeline - CREAR |
| `CRM_Config_SLA` | SLAs por etapa - CREAR |

### 3.3 Tablas de Relación CRM (NUEVAS)

| Tabla Nueva | Justificación |
|-------------|---------------|
| `CRM_Oportunidad_Contactos` | N:M oportunidad-contactos - CREAR |
| `CRM_Oportunidad_Servicios` | N:M oportunidad-servicios - CREAR |
| `CRM_Oportunidad_Documentos` | Documentos por oportunidad - CREAR |

### 3.4 Catálogos CRM (NUEVOS)

Los siguientes catálogos NO existen y se crearán:

```
CRM_Cat_OrigenLead
CRM_Cat_EstatusLead
CRM_Cat_EstatusOportunidad
CRM_Cat_MotivosPerdida
CRM_Cat_MotivosGanada
CRM_Cat_TiposPipeline
CRM_Cat_Prioridades
CRM_Cat_Sectores
CRM_Cat_TamanosCliente
CRM_Cat_RiesgoCuenta
```

### 3.5 Tablas de Integración Universal (NUEVAS)

| Tabla Nueva | Propósito |
|-------------|-----------|
| `CRM_Integraciones` | Registro de integraciones CRM externas |
| `CRM_IntegracionesCredenciales` | Credenciales (encriptadas) |
| `CRM_IntegracionesMapeoCampos` | Mapeo de campos Hub↔Externo |
| `CRM_IntegracionesSyncLog` | Log de sincronizaciones |
| `CRM_IntegracionesErrores` | Errores de sync |
| `CRM_IntegracionesConflictos` | Conflictos de datos |
| `CRM_Staging_Leads` | Staging para leads externos |
| `CRM_Staging_Cuentas` | Staging para cuentas externas |
| `CRM_Staging_Contactos` | Staging para contactos externos |
| `CRM_Staging_Oportunidades` | Staging para oportunidades externas |

---

## 4. MÓDULO CRM BACKEND EXISTENTE

### 4.1 Archivos Existentes

```
/app/backend/modules/crm/
├── __init__.py          ✅ Existe
├── routes.py            ✅ Existe (290 líneas - VTiger endpoints)
├── service.py           ✅ Existe (servicio VTiger)
└── vtiger_client.py     ✅ Existe (cliente VTiger completo)
```

### 4.2 Endpoints VTiger Existentes

| Endpoint | Método | Estado |
|----------|--------|--------|
| `/api/crm/status` | GET | ✅ Funcional |
| `/api/crm/test-connection` | GET | ✅ Funcional |
| `/api/crm/configure` | POST | ✅ Funcional |
| `/api/crm/contacts` | GET/POST | ✅ Funcional |
| `/api/crm/leads` | GET/POST | ✅ Funcional |
| `/api/crm/accounts` | GET/POST | ✅ Funcional |
| `/api/crm/products` | GET/POST | ✅ Funcional |
| `/api/crm/invoices` | GET | ✅ Funcional |

### 4.3 Lo que falta en Backend

- Endpoints para CRM nativo (no solo VTiger proxy)
- Repository para tablas EDARSAHUB
- Schemas Pydantic para entidades CRM nativas
- Servicios de pipeline y oportunidades
- Capa de integración universal (Salesforce, HubSpot, Zoho, Odoo)

---

## 5. FRONTEND - ESTADO ACTUAL

### 5.1 Menú CRM
- **NO EXISTE** menú CRM en Layout.js
- **NO EXISTEN** páginas CRM en /app/frontend/src/pages/

### 5.2 Rutas CRM
- **NO REGISTRADAS** rutas /crm/* en el router

### 5.3 Componentes CRM
- **NO EXISTEN** componentes específicos de CRM

---

## 6. SISTEMA RBAC EXISTENTE

### 6.1 Estructura de Permisos

El sistema ya tiene:
- `Usuario_Modulos` - Registro de módulos
- `Usuario_Acciones` - Acciones (ver, crear, editar, eliminar, etc.)
- `Usuario_PermisosRolModulo` - Matriz rol-módulo-acción

### 6.2 Permisos CRM a Agregar

Se agregarán registros en las tablas existentes:

**Nuevo módulo en Usuario_Modulos:**
- CRM (padre)
  - CRM_Dashboard
  - CRM_Leads
  - CRM_Cuentas
  - CRM_Contactos
  - CRM_Oportunidades
  - CRM_Pipeline
  - CRM_Propuestas
  - CRM_Contratos
  - CRM_Integraciones
  - CRM_KPIs
  - CRM_Configuracion

---

## 7. RIESGOS IDENTIFICADOS

| Riesgo | Nivel | Mitigación |
|--------|-------|------------|
| Duplicar Cliente_Catalogo con CRM_Cuentas | ALTO | Extender tabla existente, no crear nueva |
| Duplicar Usuario_LogActividades | MEDIO | Reutilizar con campo modulo_origen='CRM' |
| Romper menú existente al agregar CRM | BAJO | Usar patrón de módulos existente |
| Inconsistencia de permisos | BAJO | Usar sistema RBAC existente |
| Conflictos con VTiger existente | BAJO | VTiger es proxy externo, CRM nativo es interno |

---

## 8. DEPENDENCIAS CON MÓDULOS EXISTENTES

| Módulo | Tipo de Dependencia | Acción |
|--------|---------------------|--------|
| Autenticación | CONSUMIR | Usar get_current_user existente |
| RBAC | CONSUMIR | Agregar permisos en tablas existentes |
| Usuarios | CONSUMIR | FK a Usuario_Catalogo |
| Empresas | CONSUMIR | FK a Sistema_Empresas |
| RH | CONSUMIR | Consultar empleados para asignación |
| Finanzas | FUTURO | Link oportunidades → ingresos |
| Comercial | NO TOCAR | Módulo blindado |
| Compras | NO TOCAR | Módulo blindado |

---

## 9. PLAN DE IMPLEMENTACIÓN POR FASES

### FASE 1: Infraestructura (Sin romper nada)
1. Crear tablas CRM nuevas (scripts idempotentes)
2. Extender Cliente_Catalogo con campos CRM
3. Crear catálogos CRM
4. Seedear datos iniciales

### FASE 2: Backend CRM Nativo
1. Crear repository CRM
2. Crear schemas Pydantic
3. Crear servicios CRM
4. Crear endpoints CRM nativos
5. Mantener endpoints VTiger existentes

### FASE 3: Permisos y Menú
1. Insertar módulo CRM en Usuario_Modulos
2. Crear permisos CRM en Usuario_PermisosRolModulo
3. Agregar menú CRM en Layout.js
4. Crear rutas CRM en router

### FASE 4: Frontend CRM
1. Crear páginas placeholder
2. Implementar Dashboard CRM
3. Implementar Leads CRUD
4. Implementar Cuentas CRUD
5. Implementar Oportunidades CRUD
6. Implementar Pipeline visual

### FASE 5: Integración Universal
1. Crear capa de conectores base
2. Refactorizar VTiger como conector
3. Crear staging tables
4. Implementar sync bidireccional

---

## 10. ARCHIVOS QUE SE CREARÁN/MODIFICARÁN

### Backend (Crear)
```
/app/backend/modules/crm/
├── sql/
│   ├── 01_create_crm_tables.sql
│   ├── 02_extend_cliente_catalogo.sql
│   ├── 03_seed_crm_catalogs.sql
│   └── 04_seed_crm_permissions.sql
├── models.py
├── schemas.py
├── repository.py
├── services.py (extender)
└── integrations/
    ├── __init__.py
    ├── base_connector.py
    ├── vtiger_connector.py (refactor de vtiger_client.py)
    ├── salesforce_connector.py
    └── hubspot_connector.py
```

### Frontend (Crear)
```
/app/frontend/src/pages/crm/
├── CRMDashboard.jsx
├── Leads.jsx
├── Cuentas.jsx
├── Contactos.jsx
├── Oportunidades.jsx
├── Pipeline.jsx
├── Propuestas.jsx
├── Integraciones.jsx
└── ConfiguracionCRM.jsx
```

### Frontend (Modificar)
```
/app/frontend/src/pages/Layout.js  (agregar menú CRM)
/app/frontend/src/App.js           (agregar rutas CRM)
```

---

## 11. DECISIÓN FINAL

### TABLAS A REUTILIZAR (NO CREAR)
- `Cliente_Catalogo` → Extender con campos CRM
- `Cliente_Contactos` → Usar como está
- `Usuario_Catalogo`, `Usuario_Roles`, `Usuario_PermisosRolModulo` → Usar sistema RBAC existente
- `Usuario_LogActividades` → Usar para actividades CRM
- `Sistema_Empresas`, `Sistema_Sucursales` → FK, no duplicar

### TABLAS A CREAR (NUEVAS)
- `CRM_Leads`
- `CRM_Oportunidades`
- `CRM_Propuestas`
- `CRM_PropuestasVersiones`
- `CRM_Contratos`
- `CRM_Implementaciones`
- `CRM_Renovaciones`
- `CRM_Config_Pipelines`
- `CRM_Config_PipelineEtapas`
- `CRM_Oportunidad_Contactos`
- `CRM_Oportunidad_Servicios`
- `CRM_Oportunidad_Documentos`
- `CRM_Cat_*` (catálogos)
- `CRM_Integraciones*` (integración universal)
- `CRM_Staging_*` (staging para sync)

---

## 12. APROBACIÓN REQUERIDA

Antes de proceder con la implementación:

1. ¿Aprueba extender `Cliente_Catalogo` en lugar de crear `CRM_Cuentas` duplicada?
2. ¿Aprueba usar `Usuario_LogActividades` para actividades CRM?
3. ¿Aprueba el plan de fases propuesto?
4. ¿Hay algún módulo adicional que deba considerarse blindado?

---

**FIN DEL DIAGNÓSTICO**
