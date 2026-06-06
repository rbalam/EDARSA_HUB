# PORTAL DE CLIENTES - ARQUITECTURA Y AUTOFACTURACIÓN
## Documento de Diseño Arquitectónico

**Fecha:** 2026-05-24
**Versión:** 1.0
**Estado:** PROPUESTA ARQUITECTÓNICA

---

## 1. UBICACIÓN ARQUITECTÓNICA

```
EDARSAHUB
├── Comercial / Ventas
│   ├── Clientes (administración interna)
│   ├── Ventas
│   ├── Facturación
│   └── Estado de cuenta
│
├── Finanzas
│   ├── Cuentas por cobrar
│   ├── Cobros
│   ├── Conciliaciones
│   └── EDARSA GO
│
├── Portal de Proveedores (EXISTENTE)
│   └── Acceso externo proveedores
│
└── Portal de Clientes (NUEVO)
    ├── Acceso externo
    ├── Perfil del cliente
    ├── Autofacturación
    ├── Mis facturas
    ├── Mis compras / consumos
    ├── Mis pagos
    ├── Estado de cuenta
    ├── Links de pago (EDARSA GO)
    ├── Solicitudes
    └── Documentos
```

### Clasificación:
- **Tipo:** Portal Externo
- **Categoría:** Satélite de Comercial/Ventas + Finanzas
- **Acceso:** Usuarios externos (clientes)
- **Fuente de verdad:** EDARSAHUB SQL (NO MongoDB, NO conexiones vivas)

---

## 2. RELACIÓN CON MÓDULOS INTERNOS

### 2.1 Comercial / Ventas
- Lectura de ventas/tickets consolidados
- Consulta de historial de compras
- Validación de tickets para autofacturación
- Estado de cuenta comercial

### 2.2 Finanzas
- Cuentas por cobrar
- Pagos realizados
- Saldos pendientes
- Integración con EDARSA GO

### 2.3 Facturación
- Generación de CFDI (autofacturación)
- Consulta de facturas emitidas
- Descarga XML/PDF
- Cancelación/sustitución (con flujo autorizado)

### 2.4 EDARSA GO
- Links de pago para saldos pendientes
- Confirmación de pagos
- Historial de transacciones

---

## 3. MODELO DE ACCESO EXTERNO

### 3.1 Tablas Existentes Reutilizables

| Tabla | Uso |
|-------|-----|
| `Cliente_Catalogo` | Maestro de clientes |
| `Cliente_UsuariosPortal` | Usuarios del portal (YA EXISTE) |
| `Cliente_RolUsuarioPortal` | Roles del portal (YA EXISTE) |
| `Cliente_Contactos` | Contactos del cliente |
| `Cliente_Direcciones` | Direcciones fiscales |
| `Venta_Pagos` | Pagos registrados |
| `Venta_FormaPago` | Catálogo formas de pago |

### 3.2 Tablas Nuevas Propuestas

| Tabla | Propósito |
|-------|-----------|
| `Portal_Clientes_Sesiones` | Control de sesiones activas |
| `Portal_Clientes_Bitacora` | Auditoría de acciones |
| `Portal_Clientes_AutofacturacionSolicitudes` | Solicitudes de autofacturación |
| `Portal_Clientes_DocumentosFiscales` | Facturas emitidas por portal |
| `Portal_Clientes_Solicitudes` | Solicitudes/aclaraciones |

### 3.3 Nomenclatura Consistente

Seguir patrón existente de `Proveedor_UsuariosPortal`:
- Prefijo: `Portal_Clientes_` o `Cliente_Portal_`
- Campos de auditoría: `CreatedAt`, `UpdatedAt`, `CreatedBy`
- Campos de empresa: `EmpresaID`, `UnidadNegocioID`

---

## 4. FLUJO DE AUTOFACTURACIÓN

### 4.1 Datos Capturados por el Cliente

| Campo | Obligatorio | Validación |
|-------|-------------|------------|
| RFC | Sí | Formato SAT válido |
| Razón Social | Sí | No vacío |
| Régimen Fiscal | Sí | Catálogo SAT |
| Código Postal Fiscal | Sí | 5 dígitos |
| Uso CFDI | Sí | Catálogo SAT |
| Correo electrónico | Sí | Formato email |
| Ticket / Folio de venta | Sí | Existe en BD |
| Fecha de compra | Sí | Dentro de período permitido |
| Monto | Sí | Coincide con ticket |
| Sucursal | Sí | Corresponde al ticket |
| Método de pago | Condicional | Si aplica PPD/PUE |

### 4.2 Validaciones del Sistema

```
1. Ticket existe en EDARSAHUB SQL
   └── SI: Continuar
   └── NO: Rechazar "Ticket no encontrado"

2. Ticket pertenece a venta válida
   └── SI: Continuar
   └── NO: Rechazar "Ticket inválido"

3. Ticket no cancelado
   └── SI: Continuar
   └── NO: Rechazar "Ticket cancelado"

4. Ticket no facturado previamente
   └── SI: Continuar
   └── FACTURADO: Verificar reglas de refacturación
       └── PERMITIDO: Continuar con sustitución
       └── NO PERMITIDO: Rechazar "Ya facturado"

5. Dentro de período de autofacturación
   └── SI: Continuar
   └── NO: Rechazar "Período expirado"

6. Monto coincide
   └── SI: Continuar
   └── NO: Rechazar "Monto no coincide"

7. Sucursal corresponde
   └── SI: Continuar
   └── NO: Rechazar "Sucursal incorrecta"

8. Datos fiscales válidos
   └── SI: Generar CFDI
   └── NO: Rechazar con detalle
```

### 4.3 Estados de Solicitud

| Estado | Significado |
|--------|-------------|
| `PENDIENTE` | Solicitud recibida, en proceso |
| `VALIDANDO` | Validando ticket y datos |
| `GENERANDO_CFDI` | Conectando con PAC |
| `COMPLETADA` | CFDI generado exitosamente |
| `RECHAZADA` | Falló validación |
| `ERROR_PAC` | Error con proveedor de facturación |
| `CANCELADA` | Cancelada por usuario/admin |

---

## 5. SEGURIDAD

### 5.1 Reglas de Acceso

| Regla | Implementación |
|-------|----------------|
| Cliente solo ve su información | WHERE ClienteID = @ClienteLogueado |
| No acceso a otros clientes | Filtro obligatorio en todas las queries |
| No datos internos | No exponer costos, márgenes, inventarios |
| No modificar ventas | Solo lectura de ventas |
| No cancelar facturas sin flujo | Requiere autorización admin |
| Bitácora obligatoria | Log de todas las acciones |

### 5.2 Campos Sensibles NO Expuestos

- Costos de productos
- Márgenes de ganancia
- Inventarios
- Datos de otros clientes
- Configuración interna
- Credenciales de sistemas
- Datos de empleados

---

## 6. PERMISOS RBAC

### 6.1 Permisos para Clientes Externos

```
portal_clientes.acceso.login
portal_clientes.perfil.ver
portal_clientes.perfil.editar
portal_clientes.compras.ver
portal_clientes.autofacturacion.crear
portal_clientes.autofacturacion.ver_estatus
portal_clientes.facturas.ver
portal_clientes.facturas.descargar_xml
portal_clientes.facturas.descargar_pdf
portal_clientes.estado_cuenta.ver
portal_clientes.pagos.ver
portal_clientes.edarsa_go.pagar
portal_clientes.solicitudes.crear
portal_clientes.solicitudes.ver
portal_clientes.documentos.ver
```

### 6.2 Permisos para Administradores Internos

```
portal_clientes.admin.ver
portal_clientes.admin.configurar
portal_clientes.admin.bloquear_cliente
portal_clientes.admin.desbloquear_cliente
portal_clientes.admin.revisar_solicitudes
portal_clientes.admin.aprobar_refacturacion
portal_clientes.admin.reenviar_factura
portal_clientes.admin.cancelar_cfdi
portal_clientes.admin.auditar
portal_clientes.admin.exportar
```

---

## 7. ENDPOINTS PROPUESTOS

### 7.1 Autenticación

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/portal-clientes/auth/login` | Login cliente externo |
| POST | `/api/portal-clientes/auth/logout` | Cerrar sesión |
| POST | `/api/portal-clientes/auth/recuperar-password` | Recuperar contraseña |
| GET | `/api/portal-clientes/auth/validar-sesion` | Validar token activo |

### 7.2 Perfil

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/portal-clientes/perfil` | Obtener perfil |
| PUT | `/api/portal-clientes/perfil` | Actualizar perfil |
| GET | `/api/portal-clientes/perfil/datos-fiscales` | Datos fiscales guardados |
| PUT | `/api/portal-clientes/perfil/datos-fiscales` | Actualizar datos fiscales |

### 7.3 Compras y Tickets

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/portal-clientes/compras` | Historial de compras |
| GET | `/api/portal-clientes/compras/{id}` | Detalle de compra |
| POST | `/api/portal-clientes/tickets/validar` | Validar ticket para autofacturación |

### 7.4 Autofacturación

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/portal-clientes/autofacturacion/solicitar` | Crear solicitud |
| GET | `/api/portal-clientes/autofacturacion/solicitudes` | Mis solicitudes |
| GET | `/api/portal-clientes/autofacturacion/solicitudes/{id}` | Detalle solicitud |
| GET | `/api/portal-clientes/autofacturacion/estatus/{id}` | Estado de solicitud |

### 7.5 Facturas

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/portal-clientes/facturas` | Mis facturas |
| GET | `/api/portal-clientes/facturas/{id}` | Detalle factura |
| GET | `/api/portal-clientes/facturas/{id}/xml` | Descargar XML |
| GET | `/api/portal-clientes/facturas/{id}/pdf` | Descargar PDF |

### 7.6 Estado de Cuenta y Pagos

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/portal-clientes/estado-cuenta` | Estado de cuenta |
| GET | `/api/portal-clientes/pagos` | Historial de pagos |
| GET | `/api/portal-clientes/saldos` | Saldos pendientes |
| POST | `/api/portal-clientes/edarsa-go/link-pago` | Generar link de pago |

### 7.7 Solicitudes

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/portal-clientes/solicitudes` | Crear solicitud/aclaración |
| GET | `/api/portal-clientes/solicitudes` | Mis solicitudes |
| GET | `/api/portal-clientes/solicitudes/{id}` | Detalle solicitud |

---

## 8. FRONTEND PROPUESTO

### 8.1 Rutas del Portal

```
/portal/clientes                    → Redirect a login o dashboard
/portal/clientes/login              → Página de login
/portal/clientes/recuperar-password → Recuperar contraseña
/portal/clientes/dashboard          → Dashboard principal
/portal/clientes/autofacturacion    → Flujo de autofacturación
/portal/clientes/facturas           → Lista de facturas
/portal/clientes/facturas/:id       → Detalle factura
/portal/clientes/compras            → Historial de compras
/portal/clientes/estado-cuenta      → Estado de cuenta
/portal/clientes/pagos              → Historial de pagos
/portal/clientes/pagar              → Realizar pago (EDARSA GO)
/portal/clientes/solicitudes        → Solicitudes/aclaraciones
/portal/clientes/perfil             → Perfil y datos fiscales
```

### 8.2 Componentes Principales

| Componente | Propósito |
|------------|-----------|
| `PortalClientesLayout` | Layout específico del portal |
| `PortalClientesLogin` | Página de login |
| `PortalClientesDashboard` | Dashboard con resumen |
| `AutofacturacionWizard` | Flujo paso a paso |
| `FacturasList` | Lista de facturas |
| `FacturaDetail` | Detalle con descarga XML/PDF |
| `EstadoCuenta` | Estado de cuenta y saldos |
| `PagoEDARSAGO` | Integración con EDARSA GO |

### 8.3 Separación de Experiencia

El Portal de Clientes debe ser una experiencia **completamente separada** del ERP interno:
- Layout propio sin menú lateral del ERP
- Autenticación separada (usuarios externos)
- Sin acceso a módulos internos
- Sin navegación a Comercial/Ventas interno

---

## 9. AUDITORÍA

### 9.1 Eventos a Registrar

| Evento | Prioridad |
|--------|-----------|
| Login exitoso | ALTA |
| Login fallido | ALTA |
| Intento de acceso denegado | ALTA |
| Validación de ticket | MEDIA |
| Solicitud de autofacturación | ALTA |
| Generación de CFDI | ALTA |
| Descarga de XML | MEDIA |
| Descarga de PDF | MEDIA |
| Actualización de datos fiscales | ALTA |
| Pago iniciado | ALTA |
| Pago confirmado | ALTA |
| Pago fallido | ALTA |
| Solicitud/aclaración creada | MEDIA |
| Error de sistema | ALTA |
| Acceso sospechoso | ALTA |

### 9.2 Estructura de Bitácora

```sql
CREATE TABLE Portal_Clientes_Bitacora (
    BitacoraID INT IDENTITY PRIMARY KEY,
    ClienteID NVARCHAR(50),
    UsuarioPortalID INT,
    Evento NVARCHAR(100),
    Descripcion NVARCHAR(MAX),
    IP NVARCHAR(50),
    UserAgent NVARCHAR(500),
    Parametros NVARCHAR(MAX),  -- JSON
    Resultado NVARCHAR(50),    -- EXITO, ERROR, DENEGADO
    FechaEvento DATETIME2 DEFAULT GETDATE(),
    EmpresaID INT,
    UnidadNegocioID NVARCHAR(50)
)
```

---

## 10. RIESGOS IDENTIFICADOS

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Cliente accede a datos de otro | BAJA | CRÍTICO | Filtro obligatorio por ClienteID |
| Doble facturación | MEDIA | ALTO | Validación de ticket ya facturado |
| Factura fuera de período | MEDIA | MEDIO | Validación de fecha límite |
| Datos fiscales inválidos | ALTA | MEDIO | Validación contra catálogos SAT |
| Falla de PAC | MEDIA | ALTO | Reintentos y notificación |
| Ticket inexistente | ALTA | BAJO | Validación previa |

---

## 11. FASES DE IMPLEMENTACIÓN

### Fase PC-1: Estructura Base
- Tablas nuevas
- Endpoints de autenticación
- Login del portal
- Auditoría básica

### Fase PC-2: Perfil y Compras
- Perfil del cliente
- Historial de compras
- Datos fiscales

### Fase PC-3: Autofacturación
- Validación de tickets
- Flujo de autofacturación
- Integración con PAC
- Descarga XML/PDF

### Fase PC-4: Estado de Cuenta
- Estado de cuenta
- Saldos pendientes
- Historial de pagos

### Fase PC-5: EDARSA GO
- Integración con EDARSA GO
- Links de pago
- Confirmación de pagos

### Fase PC-6: Solicitudes
- Solicitudes/aclaraciones
- Seguimiento

---

## 12. CRITERIOS DE PARO

Detenerse y reportar si:
- No existe fuente confiable de ventas/tickets en EDARSAHUB SQL
- Se requiere consultar en vivo SoftRestaurant/MPRO/Enterprise
- No existe modelo seguro de usuario externo
- Riesgo de que un cliente vea datos de otro
- Se pretende usar MongoDB como fuente de verdad
- No existe trazabilidad de facturas
- No existe control para evitar doble facturación
- No existe validación fiscal mínima
- Se requiere exponer secretos de facturación

---

## 13. CONCLUSIÓN

El Portal de Clientes es arquitectónicamente viable dado que:
- ✅ Ya existen tablas `Cliente_UsuariosPortal` y `Cliente_RolUsuarioPortal`
- ✅ Existe modelo de portal externo (Portal de Proveedores)
- ✅ Existen tablas de pagos y formas de pago
- ✅ EDARSAHUB SQL tiene estructura para clientes y ventas
- ⚠️ Requiere tablas nuevas para autofacturación y bitácora
- ⚠️ Requiere integración con PAC para CFDI

**Próximo paso:** Autorización para iniciar Fase PC-1 (Estructura Base).

---

*Documento generado: 2026-05-24*
