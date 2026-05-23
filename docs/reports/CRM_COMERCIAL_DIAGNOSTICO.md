# CRM COMERCIAL ENTERPRISE - DIAGNÓSTICO COMPLETO
## EDARSA HUB - Fecha: 2026-05-23

---

## 1. RESUMEN EJECUTIVO

### Estado Actual
El CRM de EDARSA HUB tiene una **base sólida** implementada pero **incompleta** para operación comercial enterprise.

| Componente | Estado | Observación |
|------------|--------|-------------|
| Leads | ✅ Implementado | 12 registros, CRUD completo |
| Oportunidades | ✅ Implementado | 3 registros, Pipeline Kanban |
| **Cuentas CRM** | ❌ NO EXISTE | Solo staging (2 registros) |
| **Clientes** | ⚠️ MAESTRO EXISTE | `Cliente_Catalogo` (2 registros) |
| **Solicitudes Alta** | ❌ NO EXISTE | Tabla y flujo faltante |
| Cotizaciones | ⚠️ TABLA EXISTE | 0 registros, sin enlace CRM |
| Pedidos | ⚠️ TABLA EXISTE | 0 registros, sin enlace CRM |
| **Remisiones** | ❌ NO EXISTE | Tabla faltante |
| Contratos | ⚠️ TABLA EXISTE | `CRM_Contratos` vacía |
| Actividades | ❌ NO EXISTE | Solo `Usuario_LogActividades` |
| RBAC CRM | ❌ NO EXISTE | 0 permisos crm.* |

---

## 2. TABLAS EXISTENTES (NO DUPLICAR)

### 2.1 Cliente Maestro (CANÓNICO)
```
Cliente_Catalogo: 2 registros ✅
├── ClienteID (int, PK)
├── CodigoCliente
├── RFC
├── RazonSocial
├── NombreComercial
├── TipoPersona
├── MonedaID
├── LimiteCredito
├── DiasCredito
├── EmailPrincipal
├── Activo
└── ... (44 columnas total)

Cliente_Contactos: 0 registros
Cliente_Direcciones: 0 registros
Cliente_Grupos: 0 registros
```

### 2.2 CRM Existente
```
CRM_Leads: 12 registros ✅
├── LeadID (uniqueidentifier, PK)
├── EmpresaID
├── NombreContacto
├── Email
├── EstatusLeadID
├── EjecutivoAsignadoUserID
├── ConvertidoACuenta
├── CuentaConvertidaID (FK → ¿CRM_Cuentas? NO EXISTE)
└── ... (37 columnas)

CRM_Oportunidades: 3 registros ✅
├── OportunidadID (uniqueidentifier, PK)
├── EmpresaID
├── CuentaID (FK → ¿CRM_Cuentas? NO EXISTE)
├── LeadOrigenID
├── PipelineID
├── EtapaActualID
├── MontoEstimado
├── EjecutivoResponsableUserID
└── ... (49 columnas)

CRM_Config_Pipelines: 1 registro ✅
CRM_Config_PipelineEtapas: 7 registros ✅
CRM_Oportunidades_HistorialEtapas: 4 registros ✅
CRM_Contratos: 0 registros (tabla vacía)
CRM_Propuestas: 0 registros (tabla vacía)
```

### 2.3 Catálogos CRM
```
CRM_Cat_EstatusLead: 5 registros ✅
CRM_Cat_EstatusOportunidad: 5 registros ✅
CRM_Cat_OrigenLead: 11 registros ✅
CRM_Cat_MotivosGanada: 8 registros ✅
CRM_Cat_MotivosPerdida: 9 registros ✅
CRM_Cat_Sectores: 9 registros ✅
CRM_Cat_TamanosCliente: 5 registros ✅
CRM_Cat_Prioridades: 4 registros ✅
CRM_Cat_TiposPipeline: 4 registros ✅
CRM_Cat_EstatusContrato: 7 registros ✅
CRM_Cat_EstatusPropuesta: 7 registros ✅
```

### 2.4 Ventas (REUTILIZAR)
```
Venta_Cotizaciones: 0 registros ⚠️
├── CotizacionID (bigint, PK)
├── FolioCotizacion
├── ClienteID (FK → Cliente_Catalogo) ✅
├── EstatusCotizacionID
├── Subtotal, DescuentoTotal, ImpuestoTotal, Total
├── PedidoID (FK → Venta_Pedidos)
└── FALTA: CRM_OportunidadID, CRM_CuentaID, CRM_LeadID

Venta_CotizacionesDetalle: 0 registros
├── ProductoID (FK → Producto_Catalogo)
└── Estructura completa ✅

Venta_Pedidos: 0 registros ⚠️
├── PedidoID (bigint, PK)
├── FolioPedido
├── ClienteID (FK → Cliente_Catalogo) ✅
├── CotizacionID (FK → Venta_Cotizaciones) ✅
└── FALTA: CRM_OportunidadID, CRM_CuentaID

Venta_PedidosDetalle: 0 registros
```

### 2.5 Staging CRM (Integraciones)
```
CRM_Staging_Leads: 2 registros
CRM_Staging_Cuentas: 2 registros
CRM_Staging_Oportunidades: 0 registros
CRM_Integracion_Conectores: 1 registro (VTiger)
CRM_Integracion_SyncLog: 1 registro
```

---

## 3. TABLAS FALTANTES (CREAR)

### 3.1 CRM_Cuentas (CRÍTICO)
```sql
-- Enlace entre Prospectos CRM y Cliente_Catalogo
CRM_Cuentas
├── CuentaID (uniqueidentifier, PK)
├── EmpresaID
├── ClienteID (int, FK → Cliente_Catalogo, NULLABLE)
├── TipoCuenta (prospecto/cliente/partner)
├── NombreCuenta
├── RazonSocialSnapshot
├── RFCSnapshot
├── EjecutivoResponsableUserID
├── Estatus
├── LeadOrigenID
├── Activo
├── CreatedBy, UpdatedBy, CreatedAt, UpdatedAt
```

### 3.2 CRM_ClientesSolicitudesAlta
```sql
-- Flujo de solicitud de alta de cliente
CRM_ClientesSolicitudesAlta
├── SolicitudID (uniqueidentifier, PK)
├── FolioSolicitud
├── CuentaID (FK → CRM_Cuentas)
├── ClienteIDGenerado (FK → Cliente_Catalogo, NULLABLE)
├── DatosFiscales (RFC, RazonSocial, RegimenFiscal...)
├── CondicionesCredito
├── Estatus (borrador/enviada/revision/aprobada/rechazada)
├── SolicitadoPorUserID
├── AutorizadoPorUserID
├── MotivoRechazo
├── Auditoría
```

### 3.3 CRM_ClientesSolicitudesAltaHistorial
```sql
-- Historial de cambios de estatus
```

### 3.4 Venta_Remisiones (NUEVO)
```sql
Venta_Remisiones
├── RemisionID (bigint, PK)
├── FolioRemision
├── PedidoID (FK → Venta_Pedidos)
├── ClienteID (FK → Cliente_Catalogo)
├── FechaRemision
├── EstatusRemisionID
├── Totales
├── Auditoría
```

### 3.5 Venta_RemisionesDetalle

### 3.6 Venta_RemisionesHistorial

### 3.7 CRM_Actividades
```sql
-- Motor de actividades transversal
CRM_Actividades
├── ActividadID (uniqueidentifier, PK)
├── TipoActividad (llamada/reunion/email/tarea)
├── EntidadTipo (lead/cuenta/oportunidad/cotizacion)
├── EntidadID
├── Titulo
├── FechaProgramada
├── FechaRealizada
├── Estatus
├── AsignadoAUserID
├── Auditoría
```

---

## 4. COLUMNAS A AGREGAR (EXTENDER)

### Venta_Cotizaciones
```sql
ALTER TABLE Venta_Cotizaciones ADD
    CRM_OportunidadID uniqueidentifier NULL,
    CRM_CuentaID uniqueidentifier NULL,
    CRM_LeadID uniqueidentifier NULL,
    CreatedByUserID uniqueidentifier NULL,
    UpdatedByUserID uniqueidentifier NULL,
    EstatusComercial varchar(20) NULL;
```

### Venta_Pedidos
```sql
ALTER TABLE Venta_Pedidos ADD
    CRM_OportunidadID uniqueidentifier NULL,
    CRM_CuentaID uniqueidentifier NULL,
    CreatedByUserID uniqueidentifier NULL,
    UpdatedByUserID uniqueidentifier NULL;
```

---

## 5. BACKEND EXISTENTE

### Endpoints Implementados
```
/api/crm/native/
├── POST   /leads                          ✅
├── GET    /leads                          ✅
├── GET    /leads/{id}                     ✅
├── PUT    /leads/{id}                     ✅
├── PUT    /leads/{id}/estatus             ✅
├── POST   /leads/{id}/convertir           ✅
├── POST   /oportunidades                  ✅
├── GET    /oportunidades                  ✅
├── GET    /oportunidades/{id}             ✅
├── POST   /oportunidades/{id}/cambiar-etapa ✅
├── POST   /oportunidades/{id}/cerrar      ✅
├── GET    /pipelines                      ✅
├── GET    /pipelines/{id}/kanban          ✅
├── GET    /catalogos                      ✅
├── GET    /dashboard                      ✅
```

### Endpoints FALTANTES
```
/api/crm/
├── CUENTAS
│   ├── GET    /cuentas                    ❌
│   ├── POST   /cuentas                    ❌
│   ├── GET    /cuentas/{id}               ❌
│   ├── PUT    /cuentas/{id}               ❌
│   └── POST   /cuentas/{id}/ligar-cliente ❌
│
├── CLIENTES
│   ├── GET    /clientes                   ❌
│   └── GET    /clientes/{id}              ❌
│
├── SOLICITUDES ALTA
│   ├── GET    /clientes/solicitudes       ❌
│   ├── POST   /clientes/solicitudes       ❌
│   ├── PUT    /clientes/solicitudes/{id}  ❌
│   ├── POST   /clientes/solicitudes/{id}/enviar    ❌
│   ├── POST   /clientes/solicitudes/{id}/autorizar ❌
│   └── POST   /clientes/solicitudes/{id}/rechazar  ❌
│
├── CONTACTOS
│   ├── GET    /contactos                  ❌
│   ├── POST   /contactos                  ❌
│   └── PUT    /contactos/{id}             ❌
│
├── ACTIVIDADES
│   ├── GET    /actividades                ❌
│   ├── POST   /actividades                ❌
│   ├── PUT    /actividades/{id}           ❌
│   └── POST   /actividades/{id}/cerrar    ❌
│
├── COTIZACIONES (wrapper Venta_*)
│   ├── GET    /cotizaciones               ❌
│   ├── POST   /cotizaciones               ❌
│   ├── GET    /cotizaciones/{id}          ❌
│   ├── PUT    /cotizaciones/{id}          ❌
│   ├── POST   /cotizaciones/{id}/enviar   ❌
│   ├── POST   /cotizaciones/{id}/aprobar  ❌
│   └── POST   /cotizaciones/{id}/convertir-pedido ❌
│
├── PEDIDOS (wrapper Venta_*)
│   ├── GET    /pedidos-venta              ❌
│   ├── POST   /pedidos-venta              ❌
│   ├── GET    /pedidos-venta/{id}         ❌
│   ├── POST   /pedidos-venta/{id}/confirmar ❌
│   └── POST   /pedidos-venta/{id}/generar-remision ❌
│
├── REMISIONES
│   ├── GET    /remisiones-venta           ❌
│   ├── POST   /remisiones-venta           ❌
│   ├── GET    /remisiones-venta/{id}      ❌
│   ├── POST   /remisiones-venta/{id}/emitir ❌
│   └── POST   /remisiones-venta/{id}/entregar ❌
```

---

## 6. FRONTEND EXISTENTE

### Páginas Implementadas
```
/app/frontend/src/pages/crm/
├── CRMDashboard.jsx          ✅
├── LeadsPage.jsx             ✅
├── LeadForm.jsx              ✅
├── OportunidadesPage.jsx     ✅
├── OportunidadForm.jsx       ✅
├── PipelinePage.jsx          ✅
├── ConvertirLeadModal.jsx    ✅
└── CerrarOportunidadModal.jsx ✅
```

### Páginas FALTANTES
```
❌ CuentasPage.jsx
❌ ClientesPage.jsx
❌ SolicitudesAltaClientePage.jsx
❌ ContactosPage.jsx
❌ ActividadesPage.jsx
❌ CotizacionesPage.jsx
❌ PedidosVentaPage.jsx
❌ RemisionesPage.jsx
❌ ContratosPage.jsx
❌ ImplementacionesPage.jsx
❌ PostventaPage.jsx
❌ RenovacionesPage.jsx
❌ KPIsPage.jsx
❌ ConfiguracionCRMPage.jsx
```

---

## 7. RBAC - PERMISOS FALTANTES

### Módulos a Registrar
```sql
-- No existe módulo CRM en Usuario_Modulos
INSERT INTO Usuario_Modulos VALUES
(21, NULL, 'crm', 'CRM', 'Módulo CRM Comercial', 'MODULO', '/crm', 'briefcase', 1, 1, 0, 1, GETDATE(), NULL);
```

### Acciones CRM a Crear
```
crm.menu.ver
crm.dashboard.ver
crm.leads.*
crm.cuentas.*
crm.clientes.ver
crm.clientes.solicitar_alta
crm.clientes.autorizar_alta
crm.clientes.crear_directo
crm.contactos.*
crm.oportunidades.*
crm.actividades.*
crm.cotizaciones.*
crm.pedidos.*
crm.remisiones.*
crm.integraciones.*
crm.kpis.*
```

---

## 8. RIESGOS IDENTIFICADOS

| ID | Riesgo | Severidad | Mitigación |
|----|--------|-----------|------------|
| R1 | CRM_Cuentas no existe - Leads no pueden convertirse correctamente | ALTA | Crear tabla CRM_Cuentas |
| R2 | Venta_Cotizaciones sin enlace a CRM | MEDIA | Extender con columnas CRM_* |
| R3 | No existe tabla de Remisiones | ALTA | Crear Venta_Remisiones |
| R4 | RBAC CRM no registrado | ALTA | Registrar módulo y permisos |
| R5 | Cliente_Catalogo desconectado del CRM | MEDIA | CRM_Cuentas.ClienteID enlaza |

---

## 9. PLAN DE IMPLEMENTACIÓN RECOMENDADO

### Fase 1: DDL SQL (P0)
1. Crear CRM_Cuentas
2. Crear CRM_ClientesSolicitudesAlta + Historial
3. Crear Venta_Remisiones + Detalle + Historial
4. Crear CRM_Actividades
5. Extender Venta_Cotizaciones (columnas CRM_*)
6. Extender Venta_Pedidos (columnas CRM_*)
7. Registrar módulo CRM en Usuario_Modulos
8. Registrar permisos CRM

### Fase 2: Backend Endpoints (P1)
1. CRUD CRM_Cuentas
2. CRUD Clientes (lectura Cliente_Catalogo)
3. Flujo Solicitudes Alta Cliente
4. CRUD Contactos
5. CRUD Actividades
6. Wrapper Cotizaciones
7. Wrapper Pedidos
8. CRUD Remisiones

### Fase 3: Frontend UI (P2)
1. Actualizar menú CRM
2. Páginas faltantes
3. Integración con flujo comercial

---

## 10. CONCLUSIÓN

El CRM actual tiene **40%** de funcionalidad implementada. Para operación comercial enterprise se requiere:

- **6 tablas nuevas**
- **2 tablas extendidas**
- **~35 endpoints nuevos**
- **~12 páginas frontend nuevas**
- **Registro completo RBAC**

**Tiempo estimado**: No aplica (ver prompt maestro)

---

Generado por: E1 Agent
Fecha: 2026-05-23
