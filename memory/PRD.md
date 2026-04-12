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

### Session: April 2026 (Cuentas por Pagar)

#### Completed Work
- [x] **Módulo Cuentas por Pagar en Finanzas** (Abril 12, 2026)
  - Nuevo tab "Cuentas por Pagar" en módulo Finanzas
  - Backend: /api/finanzas/cuentas-por-pagar
  - Columnas: Folio entrada, Folio factura, Fechas, Días vencida, Referencia, Importe, Saldo, Decisión pago, Importe a pagar, Documentos (PDF/XML)
  - Resumen por antigüedad (Corriente, 1-30, 31-60, 61-90, +90 días)
  - Filtros: Sucursal, Proveedor, Fecha corte, Solo vencidas, Con decisión
  - Agrupado por proveedor con subtotales
  - Checkbox interactivo para decisión de pago
  - Exportar a CSV
  - NOTA: Datos demo (pendiente conectar a SQL Server)

- [x] **Sistema de Solicitud de Alta en Catálogos** (Abril 12, 2026)

- [x] **Tablero de Captura Rediseñado - Estilo Excel** (Abril 12, 2026)

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

### P1 - High Priority
- [ ] Drill-down Compras para SoftRestaurant (facturas y detalles)
- [ ] Módulo Catálogos RH (Colaboradores, Incidencias, Períodos)
- [ ] Integración/migración NomiPAQ y Excel hacia EDARSA HUB
- [ ] Módulo Rentabilidad - Integración OpenTable y conciliación PAX
- [ ] Módulo de Seguridad y Monitoreo (Log de logins, alertas IPs)

### P2 - Medium Priority
- [ ] Bug "Rendimiento" códigos duplicados en Insumos
- [ ] Integración QuickBooks / MarginEdge / Toast (BLOCKED: waiting API Keys)
- [ ] Módulo CRM (Captación Leads, estado cuenta)
- [ ] Módulo Comisionistas, Bonificaciones
- [ ] Botones Exportación generales (PDF, WA, Email)

---

## Key Files Reference
- `/app/backend/server.py` - Backend monolito (17,366 líneas, reduciendo)
- `/app/backend/.env` - Credenciales BD y APIs
- `/app/backend/core/db.py` - Conexiones SQL migradas
- `/app/backend/core/security.py` - Seguridad y JWT migrados
- `/app/backend/core/cerebro.py` - **CEREBRO CENTRAL: Modelos, Enums, Constantes (FUENTE DE VERDAD)**
- `/app/backend/modules/auth/` - Módulo de autenticación migrado
- `/app/backend/modules/comercial/adapters.py` - APIs locales MPRO migradas
- `/app/frontend/src/pages/Compras.js` - Módulo compras con cálculos cliente
- `/app/frontend/src/pages/Servidores.js` - Config SQL y APIs
- `/app/frontend/src/pages/ExploradorBD.js` - Exploración agrupada tablas
- `/app/memory/CATALOGO_FILTROS_EDARSAHUB.md` - Reglas UI y filtros
- `/app/memory/MAPA_MIGRACION.md` - Plan de migración modular
- `/app/memory/ESPEJO_BASE_DATOS.md` - **ESPEJO COMPLETO: Toda la estructura MongoDB**
- `/app/memory/DIAGNOSTICO_ARQUITECTURA.md` - Diagnóstico técnico

## Key API Endpoints
- `/api/compras/auditoria-inventario` - Auditoría de inventarios
- `/api/test-api-connection` - Test conexiones REST
- `/api/servers` - CRUD servidores

## Known Issues
- Servidores SQL pueden entrar en "Cooldown" (5 min) con query malformada
  - Mitigation: `sudo supervisorctl restart backend`
