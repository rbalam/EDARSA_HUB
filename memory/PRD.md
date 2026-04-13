# EDARSA HUB - Product Requirements Document

## Original Problem Statement
ERP modular web para gestionar múltiples sucursales con bases de datos SQL Server externas. Requiere control estricto de créditos, finanzas, RRHH y sistema de solicitudes/flujo de aprobación ("Mis Tareas").

## Core Requirements
1. Módulo de Recursos Humanos integrado con NomiPAQ, MPRO y Excel
2. Control de roles y permisos estrictos
3. Trazabilidad completa y corrección de solicitudes
4. Módulo de Nóminas con flujo Kanban
5. "Mis Tareas" como Bandeja Unificada

## Critical Architecture Rules
- **FROZEN STATE**: Todo lo existente se considera estable y congelado
- **ZERO REFACTORING**: Cero refactorización de lógica global sin permiso explícito
- **MODULE INDEPENDENCE**: Estricta independencia de módulos
- **LOCAL COPIES**: Si se requiere alterar un recurso compartido, hacer copia local/aislada

## Tech Stack
- **Frontend**: React + Tailwind CSS + Shadcn/UI
- **Backend**: FastAPI (Python)
- **Database**: MongoDB (local) + SQL Server (external connections)
- **Integrations**: NomiPAQ, SoftRestaurant, MPRO (SQL Server OnPremise/Cloud), APIs REST locales

---

## What's Been Implemented

### Session: April 13, 2026 (UI CxP REFACTORIZADA + MPRO COMBINADO)

#### ✅ Completado Hoy
- [x] **Corrección UI Agrupación Jerárquica CxP** (Abril 13, 2026)
  - **Problema**: La UI mostraba facturas directamente bajo categorías (A/B/X) sin sub-agrupar por proveedor
  - **Solución**: Nueva función `reagruparCxPPorProveedores()` en frontend para crear estructura jerárquica
  - **Resultado**: Categoría → Proveedor → Facturas (3 niveles)
  - **Archivos modificados**: `/app/frontend/src/pages/Finanzas.js`

- [x] **Botones Expandir/Colapsar Todos** (Abril 13, 2026)
  - Nuevo estado `cxpCategoriasExpandidas` para controlar categorías
  - Funciones `expandirTodos()` y `colapsarTodos()`
  - Colapso/expansión individual de categorías y proveedores

- [x] **Colores de Días Vencidos** (Abril 13, 2026)
  - Verde (`text-green-600`) para facturas no vencidas (días ≤ 0)
  - Rojo (`text-red-600`) para facturas vencidas (días > 0)

- [x] **Combinación SoftRestaurant + MPRO** (Abril 13, 2026)
  - **Antes**: MPRO solo era fallback si SoftRestaurant fallaba
  - **Ahora**: Ambas fuentes se consultan y combinan en la respuesta
  - **Nueva categoría**: M - MPRO (color índigo)
  - **Endpoint modificado**: `/api/finanzas/cuentas-por-pagar`
  - **Respuesta**: `fuente: "SOFTRESTAURANT+MPRO"`

#### Datos Combinados (Abril 13, 2026)
| Categoría | Proveedores | Facturas | Saldo |
|-----------|-------------|----------|-------|
| A - ALIMENTOS | 81 | 490 | $4,705,142 |
| B - BEBIDAS | 61 | 277 | $3,882,966 |
| X - OTROS | 131 | 209 | $11,248,412 |
| M - MPRO | 97 | 500 | $4,317,099 |
| **TOTAL** | **370** | **1,476** | **$24,153,619** |

---

### Session: April 13, 2026 (VALIDACIÓN UI FINANZAS CON DATOS REALES SQL)

#### ✅ Completado Hoy
- [x] **Corrección del Pool de Conexiones SQL Server** (Abril 13, 2026)
  - **Problema**: El endpoint `/api/finanzas/dashboard` consultaba `Finanzas_Presupuestos` (tabla inexistente), corrompiendo el pool de conexiones
  - **Solución**: Desactivados temporalmente los endpoints de presupuestos hasta que la tabla sea creada
  - **Archivos modificados**: `server.py` (endpoints desactivados devuelven estructuras vacías)

- [x] **Migración de Resumen CxP a SQL Real** (Abril 13, 2026)
  - Endpoint `/api/finanzas/cuentas-por-pagar/resumen` ahora consulta SQL Server
  - Antes: Siempre devolvía datos DEMO
  - Ahora: Devuelve datos reales de `Finanzas_CuentasPorPagar`

- [x] **Validación Visual UI Cuentas por Pagar** (Abril 13, 2026)
  - **Totales correctos desde SQL**: Corriente $400,663, 1-30 días $45,124, 31-60 días $54,544
  - **5 Proveedores** con facturas agrupadas visibles
  - **25 facturas** con detalles completos (Folio, Vencimiento, Saldo, etc.)
  - Indicadores de días vencidos funcionando correctamente

- [x] **Validación Visual UI Control de Ingresos** (Abril 13, 2026)
  - **Totales desde SQL**: Total Ventas $5,123,474
  - **70 cortes de caja** de múltiples sucursales
  - Desglose por tipo de pago funcionando

#### Problema Resuelto
- **Error Crítico**: El pool de conexiones SQL se corrompía cuando `/api/finanzas/dashboard` fallaba al consultar `Finanzas_Presupuestos`
- **Impacto**: Todas las peticiones subsiguientes (CxP, Ingresos) devolvían 0 registros
- **Fix**: Endpoints de presupuestos ahora devuelven estructuras vacías sin ejecutar queries

---

### Session: April 2026 (Conexión Módulo Finanzas UI a SQL Real)

#### Completed Work
- [x] **Conexión Ingresos (Cortes de Caja) a SQL Real** (Abril 13, 2026)
  - Tabla: `Finanzas_CortesCaja`
  - Endpoint: `GET /api/finanzas/ingresos/cortes-caja`
  - Estado: ✅ FUNCIONANDO (70 registros de prueba)
  - Tiempo de respuesta: ~750ms

- [x] **Conexión Cuentas por Pagar a SQL Real** (Abril 13, 2026)
  - Tabla: `Finanzas_CuentasPorPagar`
  - Endpoint: `GET /api/finanzas/cuentas-por-pagar`
  - Estado: ✅ FUNCIONANDO (25 registros de prueba)
  - Incluye JOIN con `Proveedor_Catalogo` para nombres y RFC

- [x] **Repositorio Real de Finanzas** (Abril 13, 2026)
  - Archivo: `/app/backend/modules/finanzas/repository_real.py`
  - Funciones: get_cortes_caja, get_cuentas_por_pagar, get_resumen_*
  - Documentación: `/app/memory/INTEGRACION_FINANZAS_SQL.md`

### Session: April 2026 (Validación UI Catálogos - TPV Sucursal)

#### Completed Work
- [x] **Validación CRUD UI Finanzas_ConfiguracionTPV_Sucursal** (Abril 13, 2026)
  - Frontend: `/app/frontend/src/pages/Catalogos.js`
  - Pruebas UI validadas al 100%:
    - Navegación a /catalogos ✅
    - Selección dominio Finanzas ✅
    - Vista de catálogos de Finanzas (6 catálogos) ✅
    - Selección catálogo "Config. TPV por Sucursal" ✅
    - Visualización de 8 registros ✅
    - Edición de ComisionAmex (2.4 → 2.55) ✅
    - Guardado con toast de éxito ✅
    - Persistencia real en SQL Server ✅
    - Restauración de valor original ✅
  - Test Report: `/app/test_reports/iteration_17.json`

### Session: April 2026 (Resiliencia SQL Server - P0 COMPLETADO)

#### Completed Work
- [x] **Integración Resiliencia SQL Server** (Abril 13, 2026)
  - Backend: Lógica resiliente integrada al sistema base
    - `/app/backend/core/pool.py`: Timeouts resilientes (30s login, 90s query), autocommit
    - `/app/backend/core/db.py`: Reintentos con backoff exponencial, clasificación errores
    - `/app/backend/server.py`: Endpoints de diagnóstico SQL
  - Endpoints de Monitoreo:
    - `GET /api/sistema/sql-health`: Health check con diagnóstico detallado
    - `POST /api/sistema/sql-health/test-query`: Query de prueba configurable
  - Configuración:
    - Login timeout: 30s (antes 15s)
    - Query timeout: 90s (antes 45s)
    - Max retries: 3 con backoff exponencial (2s, 4s, 8s)
    - Autocommit: Habilitado para UPDATEs inmediatos
  - Pruebas Exitosas:
    - ✅ Health check: 160ms latencia, conexión estable
    - ✅ Query lectura: sys.tables OK
    - ✅ CRUD Finanzas_ConfiguracionTPV_Sucursal: Lectura/Edición/Persistencia OK
  - Documentación: `/app/memory/DIAGNOSTICO_RESILIENCIA_SQL.md`

### Session: April 2026 (Módulo Maestro de Catálogos + Tablas Finanzas SQL)

#### Completed Work
- [x] **Módulo Maestro de Catálogos del Sistema** (Abril 13, 2026)
  - Backend: `/app/backend/modules/catalogos/`
    - `__init__.py`: Inicialización del módulo
    - `schemas.py`: Configuración de 10 dominios y 50+ catálogos
    - `repository.py`: Acceso a datos SQL Server con DDL para 9 tablas nuevas
    - `service.py`: Lógica de negocio optimizada
    - `routes.py`: 10 endpoints REST
  - Frontend: `/app/frontend/src/pages/Catalogos.js`
    - Panel de dominios con iconos y conteos
    - Vista de listado con CRUD completo
    - Modal de administración para crear tablas
    - Búsqueda, filtros y acciones masivas
  - Integración:
    - Menú "Catálogos" agregado al Layout
    - Ruta `/catalogos` configurada
  - Arquitectura:
    - 10 dominios (Generales, RH, Nómina, Compras, etc.)
    - 50+ catálogos mapeados
    - Sin duplicidad entre módulos
    - CRUD completo con permisos por rol

- [x] **Tablas de Finanzas en SQL Server EDARSA HUB** (Abril 13, 2026)
  - **CREADAS EN BD SQL SERVER:**
    - `Finanzas_ConfiguracionTPV_Sucursal` - Comisiones TPV por sucursal (8 regs)
      - ComisionDebito: 1.2%
      - ComisionCredito: 1.5%
      - ComisionAmex: 2.4% (2 días depósito) ✅
      - ComisionInternacional: 2.0% (2 días depósito) ✅
      - DiasDepositoEfectivo: 1 día (Fin semana → Lunes)
    - `Finanzas_CuentasPorPagar` - Facturas pendientes de pago
    - `Finanzas_Pagos` - Detalle de pagos realizados
    - `Finanzas_CortesCaja` - Cortes de caja con AMEX e internacional
    - `Finanzas_Depositos` - Control de depósitos bancarios
    - `Finanzas_EstatusPago` - (5 regs: Pendiente, Parcial, Pagado, Cancelado, Vencido)
    - `Finanzas_EstatusCierre` - (3 regs: Abierto, Cerrado, Conciliado)
    - `Global_Cat_Bancos` - (5 regs: BANAMEX, BBVA, SANTANDER, HSBC, BANORTE)
    - `Global_Cat_FormaPagoSAT` - (6 regs: Efectivo, Cheque, Transferencia, etc.)
    - `Finanzas_Cat_CuentasBancarias` - Cuentas bancarias de la empresa

---

### Session: April 2026 (Control de Ingresos)

#### Completed Work
- [x] **Módulo Control de Ingresos en Finanzas** (Abril 12, 2026)
  - Backend: /api/finanzas/ingresos
  - Sub-tabs: Cortes de Caja, Por Depositar, Comisiones, Conciliación
  - Reglas de depósito implementadas:
    - Efectivo: día siguiente (Vie/Sáb/Dom → Lunes)
    - Débito/Crédito: 24 hrs hábiles
    - AMEX/Internacional: 48 hrs hábiles
  - Comisiones NetPay con IVA:
    - Débito: 1.2% + IVA = 1.392%
    - Crédito: 1.5% + IVA = 1.74%
    - AMEX: 2.4% + IVA = 2.784%
    - Internacional: 2% + IVA = 2.32%
  - Control de saldos por depositar (efectivo y tarjetas)
  - NOTA: Datos demo (pendiente conectar a SQL Server)

- [x] **Módulo Cuentas por Pagar en Finanzas** (Abril 12, 2026)

- [x] **Sistema de Solicitud de Alta en Catálogos** (Abril 12, 2026)

- [x] **Tablero de Captura Incidencias Estilo Excel** (Abril 12, 2026)

---

### Session: December 2025 (Refactor Modular)

#### Completed Work
- [x] **Auditoría técnica completa de `server.py`** (18,082 líneas analizadas)
- [x] **Mapa de Migración documentado**: `/app/memory/MAPA_MIGRACION.md`
  - Inventario de 101 endpoints, 214 funciones async, 31 modelos Pydantic
  - Clasificación por dominio y módulo destino
  - Acoplamientos críticos identificados
  - Plan de 7 fases con riesgos y mitigaciones
  - Checklists de validación pre/durante/post migración
  - Reglas de no ruptura documentadas
- [x] **Scaffolding modular creado**: `/app/backend/core/` y `/app/backend/modules/`
  - 36 archivos base inicializados (sin lógica aún)

#### Status
- **Fase 0 (Preparación)**: ✅ COMPLETADA
- **Fase 1 (Core Database)**: ✅ COMPLETADA - `execute_sql_query` migrado a `/core/db.py`
- **Fase 2 (Core Security)**: ✅ COMPLETADA - `get_current_user` y seguridad migrados a `/core/security.py`
- **Fase 3 (Módulo Auth)**: ✅ COMPLETADA - 12 endpoints de auth/users/roles migrados a `/modules/auth/`
- **Fase 4/4B (Módulo Compras)**: ✅ COMPLETADA - Estructura modular lista, endpoints en server.py (~2400 líneas)
- **Fase 5 (Módulo Comercial)**: ✅ COMPLETADA - Estructura modular lista, endpoints en server.py (~3300 líneas)
- **Fase 5B (Migración real Comercial)**: 🔄 EN PROGRESO
  - ✅ Sub-fase 5B-1: Adapters (APIs locales MPRO) migrados a `modules/comercial/adapters.py`
  - ✅ Sub-fase 5B-2: Helpers del tablero migrados a `modules/comercial/service.py` (Abril 10, 2026)
    - `get_kpis_softrestaurant()` (~255 líneas)
    - `get_kpis_mpro()` (~175 líneas)  
    - `get_kpis_mpro_por_sucursal()` (~318 líneas)
    - server.py reducido de ~17,431 a ~16,689 líneas (-742 líneas)
  - ✅ Sub-fase 5B-3: Endpoint `/comercial/tablero-ejecutivo` migrado a `routes.py` (Abril 10, 2026)
    - Endpoint completo migrado a `modules/comercial/routes.py`
    - Funciones de caché migradas a `modules/comercial/repository.py`
    - server.py reducido de ~16,689 a ~16,404 líneas (-285 líneas adicionales)
  - ✅ Sub-fase 5B-4A: Endpoints de bajo riesgo migrados (Abril 10, 2026)
    - `/comercial/sucursales/{server_id}` migrado (~55 líneas)
    - `/comercial/metas/{server_id}` migrado (~95 líneas)
    - server.py reducido de ~16,404 a ~16,262 líneas (-142 líneas adicionales)
  - ✅ Sub-fase 5B-4C: Endpoints de riesgo medio-bajo migrados (Abril 10, 2026)
    - `/comercial/ticket-perfecto/{server_id}` migrado (~120 líneas)
    - `/comercial/ventas-tiempo/{server_id}` migrado (~175 líneas)
    - server.py reducido de ~16,262 a ~15,978 líneas (-284 líneas adicionales)
  - ✅ Sub-fase 5B-4E: Endpoints mesas y detalle-movimientos migrados (Abril 10, 2026)
    - `/comercial/mesas/{server_id}` migrado (~225 líneas)
    - `/comercial/detalle-movimientos/{server_id}` migrado (~208 líneas)
    - server.py reducido de ~15,978 a ~15,551 líneas (-427 líneas adicionales)
  - ✅ Sub-fase 5B-4G: Endpoint precios-constantes migrado (Abril 10, 2026)
    - `/comercial/precios-constantes/{server_id}` migrado (~500 líneas)
    - server.py reducido de ~15,551 a ~15,051 líneas (-500 líneas adicionales)
  - ✅ Sub-fase 5B-4H: Endpoint reporte-pax migrado (Abril 10, 2026)
    - `/comercial/reporte-pax/{server_id}` migrado (~330 líneas)
    - server.py reducido de ~15,051 a ~14,721 líneas (-330 líneas adicionales)
  - ✅ Sub-fase 5B-5B: Endpoint dashboard migrado (Abril 10, 2026) - CIERRE MÓDULO COMERCIAL
    - `/comercial/dashboard/{server_id}` migrado (~820 líneas)
    - server.py reducido de ~14,721 a ~13,902 líneas (-820 líneas adicionales)
    - **Total reducción Fase 5B: ~3,530 líneas**
    - **MÓDULO COMERCIAL 100% MIGRADO**
- **Fase 6A (Análisis RH)**: ✅ COMPLETADA - Diseño de 8 bloques de migración
- **Fase 6B (Catálogos RH)**: ✅ COMPLETADA (Diciembre 2025)
  - 10 endpoints migrados desde `server.py` a `modules/rh/`:
    - `GET /rrhh/catalogos/puestos`
    - `POST /rrhh/catalogos/puestos`
    - `PUT /rrhh/catalogos/puestos/{id}`
    - `DELETE /rrhh/catalogos/puestos/{id}`
    - `GET /rrhh/catalogos/sucursales`
    - `GET /rrhh/catalogos/tipos-incidencias`
    - `POST /rrhh/catalogos/tipos-incidencias`
    - `PUT /rrhh/catalogos/tipos-incidencias/{id}`
    - `DELETE /rrhh/catalogos/tipos-incidencias/{id}`
    - `GET /rrhh/catalogos/script-inicializacion`
  - **Seguridad mejorada**: Queries SQL parametrizados (prevención SQL Injection)
  - **Validación Pydantic** implementada en todos los endpoints
  - **Tablas SQL Server reutilizadas** (NO duplicadas):
    - `RH_Cat_Puestos`
    - `RH_Cat_Sucursales`
    - `RH_Cat_SucursalesFiscal`
    - `RH_Cat_Tipos_Incidencias`
  - **Archivos creados/actualizados**:
    - `modules/rh/schemas.py` (205 líneas) - Modelos Pydantic
    - `modules/rh/repository.py` (495 líneas) - Acceso a datos parametrizado
    - `modules/rh/service.py` (402 líneas) - Lógica de negocio
    - `modules/rh/routes.py` (197 líneas) - Endpoints FastAPI
    - `modules/rh/__init__.py` (73 líneas) - Inicialización
  - **server.py**: Reducido de ~13,902 a ~13,773 líneas (endpoints comentados/marcados como migrados)
  - **127 tests pasando** (regresión completa)
- **Fase 6B-1 (Estabilización tests)**: ✅ COMPLETADA (Diciembre 2025)
  - 4 tests de integración aislados con `pytest.skip()` condicional
  - Suite obligatoria definida: 7 tests (siempre pasan)
  - Suite de integración: 4 tests (skipped sin EDARSA HUB)
- **Fase 6C-B (Colaboradores RH)**: ✅ COMPLETADA (Diciembre 2025)
  - 5 endpoints migrados desde `server.py` a `modules/rh/`:
    - `GET /rrhh/colaboradores`
    - `GET /rrhh/colaboradores/{id}`
    - `POST /rrhh/colaboradores`
    - `PUT /rrhh/colaboradores/{id}`
    - `DELETE /rrhh/colaboradores/{id}`
  - **Queries con parámetros nativos** (`execute_sql_query_params`) - Nueva función en `core/db.py`
  - **Validación Pydantic** para CURP (18 chars, formato), RFC (12-13 chars), CLABE (18 dígitos), estatus_laboral
  - **Tablas SQL Server reutilizadas**:
    - `RH_Colaboradores_Expediente` (principal)
    - `RH_Cat_Sucursales`, `RH_Cat_Puestos` (JOIN)
    - `RH_Incidencias_Nomina`, `RH_Reloj_Checador`, `RH_Auditoria_Fiscal` (solo lectura en detalle)
  - **Archivos actualizados**:
    - `core/db.py` (+170 líneas) - Nueva función `execute_sql_query_params()`
    - `modules/rh/schemas.py` (406 líneas) - +200 líneas Colaboradores
    - `modules/rh/repository.py` (911 líneas) - +415 líneas Colaboradores
    - `modules/rh/service.py` (555 líneas) - +150 líneas Colaboradores
    - `modules/rh/routes.py` (325 líneas) - +125 líneas Colaboradores
  - **server.py**: Reducido de ~13,774 a ~13,557 líneas
  - **Total módulo RH**: 2,297 líneas de código modular
  - **127 tests pasando**, 4 skipped (integración)
- **Fase 6D-B (Incidencias RH)**: ✅ COMPLETADA (Diciembre 2025)
  - 4 endpoints migrados desde `server.py` a `modules/rh/`:
    - `GET /rrhh/incidencias`
    - `POST /rrhh/incidencias`
    - `POST /rrhh/incidencias/importar-excel`
    - `GET /rrhh/incidencias/plantilla-excel`
  - **Validación de tipos contra catálogo** `RH_Cat_Tipos_Incidencias` (fuente principal)
  - **Fallback**: Lista `TIPOS_INCIDENCIA_FALLBACK` solo cuando catálogo no disponible
  - **Importación Excel**: PARCIAL (NO transaccional) - documentado explícitamente
  - **Queries parametrizados nativos** para INSERT y filtros enteros
  - **Validación Pydantic** para fechas (YYYY-MM-DD), monto, unidades, colaborador_id
  - **Archivos actualizados**:
    - `modules/rh/schemas.py` (522 líneas) - +116 líneas Incidencias
    - `modules/rh/repository.py` (1,174 líneas) - +263 líneas Incidencias
    - `modules/rh/service.py` (843 líneas) - +288 líneas Incidencias
    - `modules/rh/routes.py` (452 líneas) - +127 líneas Incidencias
  - **server.py**: Reducido de ~13,558 a ~13,301 líneas
  - **Total módulo RH**: 3,108 líneas de código modular
  - **127 tests pasando**, 4 skipped (integración)
- **Fase 6E-B (Asistencia RH)**: ✅ COMPLETADA (Diciembre 2025)
  - 3 endpoints migrados desde `server.py` a `modules/rh/`:
    - `GET /rrhh/asistencia`
    - `POST /rrhh/asistencia`
    - `PUT /rrhh/asistencia/{check_id}/validar`
  - **Validación Pydantic** para `tipo_registro` (solo "Entrada" o "Salida")
  - **Queries parametrizados nativos** para INSERT/UPDATE con IDs
  - **Escape SQL** usado SOLO para fechas en cláusulas CAST (documentado - SQL Server limitación)
  - **Geolocalización opcional** sin formato forzado
  - **LÓGICA DE NEGOCIO INTACTA**: NO se validan duplicados entrada/salida por día
  - **Tablas SQL Server reutilizadas** (NO duplicadas):
    - `RH_Reloj_Checador` (principal)
    - `RH_Colaboradores_Expediente` (JOIN)
    - `RH_Cat_Sucursales` (JOIN)
    - `RH_Cat_Puestos` (JOIN)
  - **Archivos actualizados**:
    - `modules/rh/schemas.py` (+109 líneas) - Modelos AsistenciaCreate, AsistenciaResponse
    - `modules/rh/repository.py` (+162 líneas) - Queries asistencia parametrizados
    - `modules/rh/service.py` (+98 líneas) - RHAsistenciaService
    - `modules/rh/routes.py` (+78 líneas) - Endpoints asistencia
  - **server.py**: 3 endpoints comentados (~105 líneas)
  - **127 tests pasando**, 4 skipped (integración)
- **Fase 6F-B (Flujo Nómina RH)**: ✅ COMPLETADA (Diciembre 2025)
  - 7 endpoints migrados desde `server.py` a `modules/rh/`:
    - `GET /rrhh/nominas/flujo`
    - `POST /rrhh/nominas/flujo`
    - `PUT /rrhh/nominas/flujo/{flujo_id}/enviar-rh`
    - `PUT /rrhh/nominas/flujo/{flujo_id}/validar-gerente`
    - `PUT /rrhh/nominas/flujo/{flujo_id}/autorizar-dg`
    - `PUT /rrhh/nominas/flujo/{flujo_id}/enviar-tesoreria`
    - `PUT /rrhh/nominas/flujo/{flujo_id}/marcar-pagado`
  - **Validación Pydantic** para:
    - `sucursal_id` (int > 0)
    - `semana_anio` (formato YYYYWW, semana 01-53)
    - `motivo_rechazo` (obligatorio cuando aprobado=false)
    - `estatus` (lista controlada ESTATUS_FLUJO_NOMINA)
  - **Validación de transiciones de estado** (previene saltos absurdos):
    - Captura → Enviado_RH
    - Enviado_RH → Validacion_Gerente | Rechazado_Gerente
    - Rechazado_Gerente → Enviado_RH (reenvío)
    - Validacion_Gerente → Autorizacion_DG
    - Autorizacion_DG → Enviado_Tesoreria
    - Enviado_Tesoreria → Pagado
  - **Queries parametrizados nativos** para INSERT/SELECT/UPDATE con IDs
  - **Escape SQL** usado para:
    - `estatus` en filtros WHERE (string de lista controlada)
    - `motivo_rechazo` en SET (string libre de usuario)
    Razón: SQL Server no soporta parámetros en SET dinámico con strings
  - **Tablas SQL Server reutilizadas** (NO duplicadas):
    - `RH_Flujo_Nomina_Sucursal` (principal)
    - `RH_Cat_Sucursales` (JOIN)
  - **Archivos actualizados**:
    - `modules/rh/schemas.py` (+120 líneas) - FlujoNominaCreate, ValidacionGerenteRequest, etc.
    - `modules/rh/repository.py` (+200 líneas) - Queries flujo nómina parametrizados
    - `modules/rh/service.py` (+180 líneas) - RHFlujoNominaService con validación transiciones
    - `modules/rh/routes.py` (+120 líneas) - 7 endpoints flujo nómina
  - **server.py**: 7 endpoints comentados (~180 líneas)
  - **127 tests pasando**, 4 skipped (integración)
- **Fase 6G-B (Auditoría + Dashboard RH)**: ✅ COMPLETADA (Diciembre 2025)
  - 2 endpoints migrados desde `server.py` a `modules/rh/`:
    - `GET /rrhh/auditoria-fiscal`
    - `GET /rrhh/dashboard`
  - **Queries con IDs validados como enteros** (casting seguro, sin riesgo inyección)
  - **Tablas SQL Server reutilizadas** (NO duplicadas):
    - `RH_Auditoria_Fiscal`, `RH_Colaboradores_Expediente`, `RH_Cat_Sucursales`
    - `RH_Cat_Puestos`, `RH_Incidencias_Nomina`, `RH_Flujo_Nomina_Sucursal`
  - **Archivos actualizados**:
    - `modules/rh/schemas.py` (+50 líneas) - AuditoriaFiscalFiltros, AuditoriaFiscalResponse
    - `modules/rh/repository.py` (+120 líneas) - query_listar_auditoria_fiscal, query_dashboard_rh
    - `modules/rh/service.py` (+55 líneas) - RHAuditoriaService
    - `modules/rh/routes.py` (+50 líneas) - Endpoints auditoría+dashboard
- **Fase 6H-B (Reclutamiento RH)**: ✅ COMPLETADA (Diciembre 2025)
  - 10 endpoints migrados desde `server.py` a `modules/rh/`:
    - `GET /rrhh/vacantes`
    - `POST /rrhh/vacantes`
    - `PUT /rrhh/vacantes/{vacante_id}`
    - `DELETE /rrhh/vacantes/{vacante_id}`
    - `GET /rrhh/candidatos`
    - `POST /rrhh/candidatos`
    - `PUT /rrhh/candidatos/{candidato_id}`
    - `DELETE /rrhh/candidatos/{candidato_id}`
    - `GET /rrhh/reclutamiento/dashboard`
    - `GET /rrhh/reclutamiento/script-inicializacion`
  - **Validación Pydantic** para:
    - `sucursal_id`, `puesto_id`, `vacante_id`, `candidato_id` (int > 0)
    - `email` (formato válido)
    - `estatus` vacantes (Abierta, En Proceso, Cerrada, Cancelada)
    - `estatus` candidatos (Recibido, En Revisión, Entrevista, Finalista, Contratado, Rechazado)
    - `tipo_contrato` (Tiempo Completo, Medio Tiempo, Temporal, Por Proyecto, Prácticas)
    - `puntuacion` (0-100)
  - **Queries con IDs validados como enteros** (casting seguro)
  - **Escape SQL** usado para strings de usuario en INSERT/UPDATE:
    - titulo, descripcion, requisitos, estatus, nombre, email, notas, etc.
    Razón: SQL Server no soporta parámetros nativos en INSERT/UPDATE con múltiples columnas dinámicas
  - **Tablas SQL Server reutilizadas** (NO duplicadas):
    - `RH_Vacantes`, `RH_Candidatos`, `RH_Cat_Sucursales`, `RH_Cat_Puestos`
  - **Archivos actualizados**:
    - `modules/rh/schemas.py` (+220 líneas) - VacanteCreate, CandidatoCreate, etc.
    - `modules/rh/repository.py` (+350 líneas) - CRUD vacantes, candidatos, dashboard
    - `modules/rh/service.py` (+200 líneas) - RHReclutamientoService
    - `modules/rh/routes.py` (+190 líneas) - 10 endpoints reclutamiento

### 🎉 MÓDULO RH COMPLETAMENTE MIGRADO (Diciembre 2025)
**Total endpoints RH migrados**: 38 endpoints
**Total líneas código modular RH**: ~5,200 líneas
**Bloques completados**:
- ✅ 6B: Catálogos RH (10 endpoints)
- ✅ 6C: Colaboradores RH (5 endpoints)
- ✅ 6D: Incidencias RH (4 endpoints)
- ✅ 6E: Asistencia RH (3 endpoints)
- ✅ 6F: Flujo Nómina RH (7 endpoints)
- ✅ 6G: Auditoría + Dashboard RH (2 endpoints)
- ✅ 6H: Reclutamiento RH (10 endpoints - incluye script inicialización)

### FASE ENRIQUECIMIENTO-STAGING: Análisis de RFC/CURP (Diciembre 2025)
**Reporte completo**: `/app/memory/REPORTE_ENRIQUECIMIENTO_STAGING.md`
**Estado**: ✅ COMPLETADO - SIN ÉXITO EN ENRIQUECIMIENTO

**Inventario del Excel (14 hojas)**:
- BD Nómina, Nomipaq, Complemento, Métodos de Pago, etc.
- Ninguna hoja contiene RFC ni CURP de empleados
- Solo existe RFC de la empresa (DAP-170822-SE1)

**Resultado de búsqueda exhaustiva**:
- RFCs de empleados encontrados: **0**
- CURPs de empleados encontrados: **0**
- Porcentaje de cruce exitoso: **0%**

**Clasificación final (sin cambios)**:
- Total en staging: 56
- Incompletos: 56 (100%)
- Listos para alta: 0
- Enriquecidos: 0

**🔴 VEREDICTO**: El archivo Excel de Cienfuegos **NO ES VIABLE** como fuente para el catálogo maestro de empleados. Es un cálculo de nómina semanal de CONTPAQi que NO incluye identificadores fiscales.

**Escenario aplicable**: D - El Excel sirve solo para apoyo operativo de prenómina

**Próximo paso requerido**:
- Obtener archivo con RFC/CURP desde CONTPAQi Nóminas
- O explorar base de datos MPro para identificadores

---

### FASE OPERATIVA-IMPORTADOR: Preview Real Excel Cienfuegos (Diciembre 2025)
**Reporte completo**: `/app/memory/REPORTE_FASE_OPERATIVA_IMPORTADOR.md`
**Preview JSON**: `/app/memory/PREVIEW_EXCEL_CIENFUEGOS.json`
**Resultado Staging**: `/app/memory/RESULTADO_CARGA_STAGING.json`
**Estado**: ✅ COMPLETADO

**Conexión establecida**:
- Servidor: EDARSA HUB (ID: bea40259-35f1-4693-bda2-d2d10e13e56a)
- BD: EDARSAHUB
- Usuario: HRLectura (con permisos de escritura confirmados)
- Ping: ✅ EXITOSO

**Tablas creadas en EDARSAHUB**:
- ✅ `RH_Importacion_Staging` (32 columnas, 4 índices)
- ✅ `RH_Importacion_Bitacora` (14 columnas)

**Resultado del Preview y Carga a Staging**:
- Bitácora ID: 1
- Total registros leídos: 56
- Cargados a staging: 56 (100%)
- Duplicados probables: 0 (no hay colaboradores existentes en BD)
- **Incompletos: 56 (100%)** ← Sin CURP ni RFC en el Excel
- Rechazados: 0
- Errores: 0
- Duración: 3 segundos

**🔴 HALLAZGO CONFIRMADO**: El Excel de nómina NO contiene columnas CURP ni RFC.
Todos los registros (100%) permanecen como INCOMPLETOS en staging.

**Próximo paso requerido**:
- Obtener CURP/RFC de fuente alternativa para completar los registros
- O aprobar carga al maestro sin identificadores únicos (no recomendado)

---

### FASE DISEÑO-IMPORTACIÓN: Arquitectura de Importación de Empleados (Diciembre 2025)
**Documento creado**: `/app/memory/DISENO_IMPORTACION_EMPLEADOS.md`
**Estado**: ✅ IMPLEMENTACIÓN BACKEND COMPLETADA

**Fases diseñadas**:
- ✅ Fase 1: Diagnóstico de tablas EDARSA HUB (44 tablas RH confirmadas)
- ✅ Fase 2: Mapeo Excel Cienfuegos → RH_Colaboradores_Expediente
- ✅ Fase 3: Mapeo MPro (COMPLETADO - Abril 2026)
- ✅ Fase 4: Reglas de deduplicación (CURP/RFC como llaves)
- ✅ Fase 5: Tablas staging/bitácora (scripts DDL listos)
- ✅ Fase 6: Importador backend implementado

### FASE CARGA-STAGING: Carga Controlada MPro → Staging (Abril 2026)
**Documentos creados**:
- `/app/memory/DIAGNOSTICO_MPRO_EMPLEADOS.md` - Diagnóstico técnico
- `/app/memory/REPORTE_CARGA_STAGING_FINAL.md` - Reporte ejecutivo (CORREGIDO)
**Estado**: ✅ COMPLETADA (con ajuste de criterio)

**⚠️ AJUSTE DE CRITERIO (Abril 2026)**:
- MPro_HR2020 **EXCLUIDA** del proceso por criterio oficial
- 39 registros marcados como `Estado = 'Excluido'`
- Solo válidas: MPro_CENTRAL2020 (principal) + Excel (complementaria)

**Fuentes VÁLIDAS (Totales Oficiales)**:
| Fuente | Base de Datos | Registros | Con CURP | Listos |
|--------|---------------|-----------|----------|--------|
| MPro_CENTRAL2020 | CENTRAL2020 | 476 | 100% | **466** |
| Excel_Cienfuegos | N/A | 56 | 0% | 0 |
| **TOTAL VÁLIDO** | | **532** | **90%** | **466** |

**Fuente EXCLUIDA**:
| Fuente | Registros | Estado | Motivo |
|--------|-----------|--------|--------|
| MPro_HR2020 | 39 | Excluido | Criterio oficial |

**Empresas identificadas en CENTRAL2020**:
- 130° QUERETARO (QUEYUKA): 208 empleados (206 listos)
- ORIGEN (SIBARITAS RESTAURANTEROS): 156 empleados (150 listos)
- 130° TULUM: 40 empleados (39 listos)
- CIEN FUEGOS (DESARROLLOS AMARILLOS): 28 empleados (28 listos)
- XCANATUN (CERVEZA PATITO): 16 empleados (15 listos)
- MECA: 14 empleados (14 listos)
- GARCIA LAVIN: 11 empleados (11 listos)
- EDARSA: 3 empleados (3 listos)

**Trazabilidad implementada**:
- Campo `Fuente`: Identifica origen exacto
- Campo `Sucursal_Nombre`: Identifica empresa/sucursal
- Campo `Estado`: 'Excluido' para fuentes no válidas
- Campo `Observaciones`: Contiene Razón Social + motivo exclusión si aplica

### FASE APROBACIÓN: Lógica de Aprobación Colaboradores (Abril 2026)
**Documentos creados**:
- `/app/memory/DISENO_APROBACION_COLABORADORES.md` - Diseño funcional y técnico
**Estado**: ✅ COMPLETADA

**Componentes implementados**:

1. **Backend - Servicio de Aprobación** (`/modules/rh/importador/aprobacion_service.py`):
   - `obtener_estadisticas_staging()` - Resumen por estado/fuente/empresa
   - `obtener_pendientes_aprobacion()` - Candidatos a aprobar con filtro empresa
   - `obtener_incompletos()` - Registros sin CURP/RFC
   - `obtener_excluidos()` - Registros de fuente no autorizada
   - `aprobar_registro()` - INSERT/UPDATE individual en maestro
   - `rechazar_registro()` - Rechazo con motivo obligatorio
   - `observar_registro()` - Marcar para revisión
   - `aprobar_lote()` - Aprobación masiva por empresa

2. **Endpoints API** (8 nuevos endpoints):
   - `GET /api/rrhh/importar/staging/estadisticas`
   - `GET /api/rrhh/importar/staging/pendientes`
   - `GET /api/rrhh/importar/staging/incompletos`
   - `GET /api/rrhh/importar/staging/excluidos`
   - `GET /api/rrhh/importar/staging/{id}`
   - `POST /api/rrhh/importar/staging/aprobar/{id}`
   - `POST /api/rrhh/importar/staging/rechazar/{id}`
   - `POST /api/rrhh/importar/staging/observar/{id}`
   - `POST /api/rrhh/importar/staging/aprobar-lote`

3. **Frontend - UI de Aprobación** (`/pages/ImportadorRH.js`):
   - Dashboard con estadísticas en tiempo real
   - Distribución por empresa con filtros clicables
   - Tabla de pendientes con acciones (aprobar/ver/rechazar)
   - Modal de detalle con opciones de observar/rechazar
   - Aprobación en lote por empresa
   - Pestañas: Pendientes | Incompletos | Excluidos

4. **Reglas de Negocio Implementadas**:
   - Solo MPro_CENTRAL2020 como fuente válida
   - Estado != 'Excluido' para ser candidato
   - Clasificacion != 'incompleto' para aprobar
   - CURP/RFC únicos en maestro (o UPDATE si existe)
   - Trazabilidad completa en staging y bitácora

**Pruebas ejecutadas**:
- ✅ Aprobación individual (StagingID 333 → ColaboradorID 1)
- ✅ Aprobación en lote (3 de EDARSA → 2 INSERT + 1 UPDATE)
- ✅ Detección de duplicados por RFC (CURP match → UPDATE)
- ✅ UI funcional con todas las pestañas

### FASE HOMOLOGACIÓN: Homologación de Catálogos (Abril 2026)
**Documentos creados**:
- `/app/memory/DISENO_HOMOLOGACION_CATALOGOS.md` - Diseño funcional y técnico
**Estado**: ✅ COMPLETADA

**Diagnóstico realizado**:
- Catálogos `RH_Cat_Sucursales`, `RH_Cat_Puestos`, `RH_Cat_Departamentos` existían pero VACÍOS
- Valores únicos en staging: 8 sucursales, 37 puestos, 11 departamentos

**Componentes implementados**:

1. **Backend - Servicio de Homologación** (`/modules/rh/importador/homologacion_service.py`):
   - `crear_tabla_equivalencias()` - Tabla RH_Homologacion_Equivalencias
   - `poblar_catalogo_sucursales/puestos/departamentos()` - Poblar catálogos desde staging
   - `actualizar_staging_con_ids()` - Asignar IDs de catálogo a staging
   - `verificar_homologacion_completa()` - Validar antes de aprobación masiva
   - `ejecutar_homologacion_completa()` - Proceso end-to-end

2. **Endpoints API** (4 nuevos endpoints):
   - `POST /api/rrhh/importar/homologacion/ejecutar` - Ejecutar homologación completa
   - `GET /api/rrhh/importar/homologacion/estadisticas` - Estado de homologación
   - `GET /api/rrhh/importar/homologacion/equivalencias` - Listar equivalencias
   - `GET /api/rrhh/importar/homologacion/verificar` - Verificar completitud

3. **Frontend - UI de Homologación** (pestaña en ImportadorRH.js):
   - Dashboard con contadores de catálogos poblados
   - Indicador de estado: "Homologación Completa" / "Pendiente"
   - Tabla de equivalencias (Tipo, Valor Origen, Valor Normalizado, ID, Estado)
   - Botón "Ejecutar Homologación"

**Resultados de Homologación**:
| Catálogo | Registros Creados |
|----------|-------------------|
| Sucursales | 8 |
| Departamentos | 11 |
| Puestos | 37 |
| **Total equivalencias** | **56** |
| **Staging actualizado** | **462 registros** |
| **Pendientes homologación** | **0** |

**Regla obligatoria implementada**:
- ✅ Solo se permite aprobación masiva si `verificar_homologacion_completa()` retorna `true`

### FASE APROBACIÓN MASIVA: Carga al Maestro (Abril 2026)
**Documentos creados**:
- `/app/memory/REPORTE_APROBACION_MASIVA_FINAL.md` - Reporte ejecutivo completo
- `/app/memory/RESULTADO_APROBACION_MASIVA.json` - Detalle técnico JSON
**Estado**: ✅ COMPLETADA (97% éxito)

**Resultados de Aprobación Masiva**:
| Métrica | Cantidad |
|---------|----------|
| **Total candidatos iniciales** | 462 |
| **Total procesados exitosamente** | 449 |
| **Insertados (nuevos)** | 437 |
| **Actualizados (existentes)** | 12 |
| **Observados (sin RFC)** | 17 |
| **Incompletos (sin CURP/RFC)** | 10 |

**Colaboradores en Maestro por Empresa**:
| Empresa | Nuevos | Actualizados | Total |
|---------|--------|--------------|-------|
| 130° QUERETARO | 185 | 6 | 191 |
| ORIGEN | 137 | 3 | 140 |
| 130° TULUM | 36 | 1 | 37 |
| CIEN FUEGOS | 27 | 0 | 27 |
| XCANATUN | 15 | 0 | 15 |
| MECA | 12 | 1 | 13 |
| GARCIA LAVIN | 11 | 0 | 11 |
| **TOTAL EN MAESTRO** | | | **437** |

**Incidencia detectada**:
- ~~17 empleados sin RFC no pudieron insertarse (constraint UNIQUE no permite NULLs duplicados)~~
- ✅ **RESUELTO**: Constraints modificados a índices filtrados

### FASE CORRECCIÓN CONSTRAINTS: Índices Únicos Filtrados (Abril 2026)
**Documentos creados**:
- `/app/memory/REPORTE_CORRECCION_CONSTRAINTS.md` - Reporte técnico completo
**Estado**: ✅ COMPLETADA

**Problema resuelto**:
- Constraints UNIQUE originales no permitían múltiples NULLs
- 17 empleados sin RFC quedaron bloqueados

**Solución aplicada**:
```sql
-- Índices únicos FILTRADOS (permiten NULLs duplicados)
CREATE UNIQUE INDEX IX_RFC_Unique_NotNull ON ... WHERE RFC IS NOT NULL AND RFC != '';
CREATE UNIQUE INDEX IX_CURP_Unique_NotNull ON ... WHERE CURP IS NOT NULL AND CURP != '';
```

**Resultado del reprocesamiento**:
| Métrica | Cantidad |
|---------|----------|
| Observados reprocesados | 17 |
| Insertados exitosamente | **17** |
| Duplicados por CURP | 0 |
| Errores | 0 |

**Estado Final del Maestro**:
| Métrica | Cantidad |
|---------|----------|
| **Total en RH_Colaboradores_Expediente** | **454** |
| Con RFC informado | 437 |
| Sin RFC | 17 |
| Procesados en staging | 466 |
| Pendientes (incompletos Excel) | 10 |

### FASE IMPLEMENTACIÓN-IMPORTADOR: Backend y API (Diciembre 2025)
**Archivos creados**:
- `modules/rh/importador/__init__.py` (66 líneas)
- `modules/rh/importador/schemas.py` (290 líneas) - Modelos Pydantic
- `modules/rh/importador/repository.py` (698 líneas) - SQL y DDL
- `modules/rh/importador/service.py` (691 líneas) - Lógica de negocio
- `modules/rh/importador/routes.py` (467 líneas) - Endpoints FastAPI

**Endpoints implementados**:
- `GET /api/rrhh/importar/tablas/script` - Obtener scripts DDL
- `POST /api/rrhh/importar/tablas/crear` - Crear tablas (admin)
- `POST /api/rrhh/importar/excel/preview` - Preview sin insertar
- `POST /api/rrhh/importar/excel/staging` - Cargar a staging
- `GET /api/rrhh/importar/staging` - Listar registros
- `PUT /api/rrhh/importar/staging/{id}` - Actualizar registro
- `POST /api/rrhh/importar/staging/aprobar` - Aprobar y cargar al maestro
- `GET /api/rrhh/importar/bitacora` - Ver historial

**Flujo implementado (CONTROLADO)**:
1. Upload Excel → Extraer datos
2. Validar cada registro (CURP, RFC, nombre)
3. Detectar duplicados con niveles de confianza
4. Clasificar: nuevo / actualizar / duplicado_probable / incompleto / rechazado
5. Cargar a staging (NO directo al maestro)
6. Usuario revisa y aprueba
7. Carga controlada al maestro
8. Registro en bitácora

**Documento de entregables**: `/app/memory/ENTREGABLES_IMPORTADOR_RH.md`

---

### FASE RH-POST-1: Estabilización y Cobertura (Diciembre 2025)
**Archivo de tests creado**: `tests/test_rh_modular.py`
**Cobertura**:
- Suite Obligatoria: 21 tests (siempre pasan, no requieren SQL)
  - 1 test autenticación
  - 9 tests requieren auth (403)
  - 8 tests validación Pydantic (422)
  - 3 tests scripts estáticos
- Suite Integración: 9 tests (skip si no hay EDARSA HUB)
  - Colaboradores, Incidencias, Asistencia, Flujo Nómina, Auditoría, Reclutamiento

**Comandos de ejecución**:
```bash
# Suite RH completa:
python -m pytest tests/test_catalogos_rrhh.py tests/test_rh_modular.py -v

# Suite obligatoria solamente (siempre pasa):
python -m pytest tests/test_rh_modular.py -v -k "Auth or RequireAuth or Pydantic or Estaticos"
```

**Resultado**: 28 passed, 13 skipped

---

### Session: April 9, 2026

#### Completed Features
- [x] Recálculo frontend de importe diferencias inventario (`Compras.js`)
- [x] Recálculo KPIs inventario (A favor, En contra, Existencia Física/Teórica)
- [x] Modal "Pantalla Completa" para Auditoría en `Compras.js`
- [x] Modal "Pantalla Completa" para Resultados en `Reportes.js`
- [x] Actualización `CATALOGO_FILTROS_EDARSAHUB.md` con lineamientos modales
- [x] Integración APIs locales MPRO: ventas en tiempo real con zona horaria UTC-6
- [x] Endpoint `/api/test-api-connection` para pruebas de conexión REST
- [x] UI "Conexiones API" en `Servidores.js`
- [x] Explorador BD: carga servidores desde modal, agrupación por categoría
- [x] Auto-scroll en Captura Manual inventarios con tecla Tab
- [x] **FIX: Scroll horizontal modal Pantalla Completa Auditoría** (fixed JSX syntax error)

---

### Session: April 10, 2026 - Continuation

#### PRIORIDAD 1 COMPLETADA: Connection Pooling SQL Server

**Problema resuelto**: Cada request SQL creaba una nueva conexión (100-500ms overhead)

**Solución implementada**:
- Nuevo módulo `/app/backend/core/pool.py` (400+ líneas)
- Connection pooling con DBUtils PooledDB
- Pool por servidor (4 pools activos)
- Fallback automático pytds → pymssql
- Reutilización de conexiones

**Resultados de performance**:
- Primera llamada: 4532ms (crea pools)
- Segunda llamada: 2199ms (52% más rápido)
- Tercera llamada: 2151ms (53% más rápido)

**Endpoints de diagnóstico añadidos**:
- `GET /api/sistema/pool-stats` - Ver estadísticas del pool
- `POST /api/sistema/pool-reset` - Resetear todos los pools

**Archivos modificados**:
- `/app/backend/core/pool.py` (NUEVO)
- `/app/backend/core/db.py` (execute_sql_query usa pool)
- `/app/backend/server.py` (endpoints de diagnóstico)
- `/app/backend/requirements.txt` (DBUtils==3.1.2)

#### PRIORIDAD 2 COMPLETADA: Tests de Regresión

**Suite de tests creada**:
- 28 tests nuevos, 100% pasando
- Cobertura: Auth, Comercial, Pool, Servers
- Markers: smoke (22), regression (4), slow (2)

**Archivos creados**:
- `/app/backend/tests/conftest.py` - Fixtures
- `/app/backend/tests/test_auth.py` - 6 tests
- `/app/backend/tests/test_comercial.py` - 9 tests
- `/app/backend/tests/test_pool.py` - 10 tests
- `/app/backend/tests/test_servers.py` - 4 tests
- `/app/backend/pytest.ini` - Configuración

**Comandos**:
```bash
pytest tests/ -m smoke      # 22 tests en ~12s
pytest tests/ -m regression # 4 tests en ~6s
```

---

### Session: April 10, 2026

#### Fase 5B-1: Migración Adapters (APIs Locales MPRO)

**Archivos creados**:
- `/app/backend/modules/comercial/adapters.py` - Lógica de APIs locales MPRO (310 líneas)

**Funciones migradas**:
- `APIS_MPRO_LOCALES` - Configuración hardcodeada de APIs locales
- `query_api_mpro_local()` - Consulta REST a API local MPRO
- `obtener_ventas_dia_api_local()` - Ventas del día en tiempo real
- `sumar_ventas_api_local_a_sucursal()` - Homologación multi-origen

**Resultado**:
- `server.py`: 17,672 → 17,366 líneas (-306 líneas)
- Performance: **0% degradación** (import directo, sin wrappers)
- Todos los endpoints de comercial siguen funcionando

---

### Session: April 10, 2026 (Continuation) - PASO 5: Ampliación Cobertura Tests

#### PASO 5 COMPLETADO: Ampliación Cobertura de Tests con MOCKS

**Objetivo**: Ampliar cobertura de tests para 4 módulos críticos usando EXCLUSIVAMENTE mocks (sin conexiones reales).

**Archivos de tests creados/ampliados**:
| Archivo | Tests | Cobertura Módulo |
|---------|-------|------------------|
| `tests/test_core_db.py` | 27 tests | 46% (de 47% inicial) |
| `tests/test_core_security.py` | 25 tests | 77% (de 41% inicial) ↑36pts |
| `tests/test_auth_service.py` | 23 tests (NUEVO) | 80% (de 0% inicial) |
| `tests/test_comercial_adapters.py` | 23 tests (NUEVO) | 89% (de 0% inicial) |

**Resumen de resultados**:
- **98 tests nuevos/ampliados** pasando al 100%
- **166 tests totales** en la suite modular (pasando)
- **68% cobertura combinada** de core + modules
- **0 cambios a código productivo** (solo archivos de test)
- **0 conexiones reales** (100% mockeado)

**Funcionalidades cubiertas**:
- `core/db.py`: Parseo SQL Server, cooldown servers, execute_sql_query (mock)
- `core/security.py`: Hashing bcrypt, JWT create/verify, permisos, filtros
- `modules/auth/service.py`: Register, login, CRUD usuarios, CRUD roles
- `modules/comercial/adapters.py`: APIs MPRO locales, ventas día, fallbacks

**Huecos pendientes de cobertura** (para futuras sesiones):
- `core/db.py` líneas 258-294, 334-378 (conexiones reales SQL - requieren integración)
- `core/pool.py` (58% - requiere tests de integración con BD real)
- `modules/auth/repository.py` (39% - acceso directo MongoDB)
- `modules/compras/service.py` (14% - lógica de negocio compleja)

---

## Prioritized Backlog

### P0 - Critical
- ~~Scroll horizontal en Pantalla Completa de Auditoría~~ ✅ DONE
- ~~PASO 5: Ampliación Cobertura Tests~~ ✅ DONE (Abril 10, 2026)
- ~~Módulo Maestro de Catálogos del Sistema~~ ✅ DONE (Abril 13, 2026)

### P1 - High Priority
- [ ] **Ejecutar DDL** en SQL Server para crear las 9 tablas globales nuevas (desde Administración de Catálogos)
- [ ] **Conexión Finanzas a SQL Server** (pausado temporalmente por módulo Catálogos)
- [ ] **Accesos contextuales** desde módulos hacia Catálogos (RH→Catálogos RH, etc.)
- [ ] Drill-down Compras para SoftRestaurant (facturas y detalles)
- [ ] Integración/migración NomiPAQ y Excel hacia EDARSA HUB
- [ ] Módulo Rentabilidad - Integración OpenTable y conciliación PAX
- [ ] Módulo de Seguridad y Monitoreo (Log de logins, alertas IPs)

### P2 - Medium Priority
- [ ] Bug "Rendimiento" códigos duplicados en Insumos
- [ ] Integración QuickBooks / MarginEdge / Toast (BLOCKED: waiting API Keys)
- [ ] Módulo CRM (Captación Leads, estado cuenta)
- [ ] Módulo Comisionistas, Bonificaciones
- [ ] Botones Exportación generales (PDF, WA, Email)
- [ ] UI para gestión directa de colaboradores en catálogo maestro

---

## Key Files Reference
- `/app/backend/server.py` - Backend monolito (17,366 líneas, reduciendo)
- `/app/backend/.env` - Credenciales BD y APIs
- `/app/backend/core/db.py` - Conexiones SQL migradas
- `/app/backend/core/security.py` - Seguridad y JWT migrados
- `/app/backend/core/cerebro.py` - **CEREBRO CENTRAL: Modelos, Enums, Constantes (FUENTE DE VERDAD)**
- `/app/backend/modules/auth/` - Módulo de autenticación migrado
- `/app/backend/modules/catalogos/` - **NUEVO: Módulo maestro de catálogos**
- `/app/backend/modules/comercial/adapters.py` - APIs locales MPRO migradas
- `/app/frontend/src/pages/Compras.js` - Módulo compras con cálculos cliente
- `/app/frontend/src/pages/Catalogos.js` - **NUEVO: UI módulo catálogos**
- `/app/frontend/src/pages/Servidores.js` - Config SQL y APIs
- `/app/frontend/src/pages/ExploradorBD.js` - Exploración agrupada tablas
- `/app/memory/CATALOGO_FILTROS_EDARSAHUB.md` - Reglas UI y filtros
- `/app/memory/MAPA_MIGRACION.md` - Plan de migración modular
- `/app/memory/ESPEJO_BASE_DATOS.md` - **ESPEJO COMPLETO: Toda la estructura MongoDB**
- `/app/memory/DIAGNOSTICO_ARQUITECTURA.md` - Diagnóstico técnico
- `/app/memory/DISENO_MODULO_CATALOGOS.md` - **NUEVO: Diseño técnico módulo catálogos**
- `/app/memory/DIAGNOSTICO_CATALOGOS_EDARSA_HUB.md` - **NUEVO: Diagnóstico catálogos SQL**

## Key API Endpoints
- `/api/compras/auditoria-inventario` - Auditoría de inventarios
- `/api/test-api-connection` - Test conexiones REST
- `/api/servers` - CRUD servidores

## Known Issues
- Servidores SQL pueden entrar en "Cooldown" (5 min) con query malformada
  - Mitigation: `sudo supervisorctl restart backend`
