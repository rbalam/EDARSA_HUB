# EDARSA HUB - Product Requirements Document

## MÁXIMAS (Reglas Críticas Inquebrantables)

1. **MONITOREO BACKEND OBLIGATORIO**: Antes de ejecutar cualquier tarea, verificar que el backend esté en línea. Si detecta HTTP 502 o backend caído:
   - INFORMAR INMEDIATAMENTE al usuario
   - NO ACEPTAR ningún prompt hasta que el backend esté restaurado
   - Reiniciar backend automáticamente y esperar confirmación

2. **PROHIBIDO testing_agent_v3_fork**: Testing exclusivamente vía cURL, bash o `python -c`

3. **Autorización Controlada**: No asumir ni refactorizar fuera del alcance solicitado

---

## Problema Original
Sistema de gestión centralizado (EDARSAHUB) con múltiples fuentes de datos (SQL Server, SoftRestaurant, MPRO). El problema principal identificado fue la "sobrescritura incorrecta de FechaOperacion" que inicialmente se atribuía a un "Ejecutor B" externo.

## Diagnóstico Completado
- **NO existe Ejecutor B externo**. El causante era el propio backend (`operational_window.py`) aplicando una regla global hardcodeada (13:00 a 06:00).
- Se requiere configuración dinámica de turnos operativos por unidad de negocio.

## Matriz Definitiva de Ventas del Día
Ver documento completo: `/app/docs/reports/MATRIZ_DEFINITIVA_VENTAS_DIA_SOFTRESTAURANT_MPRO_TURNOS.md`

**Resumen de la Matriz**:
- Ventas del Día = ventas del periodo operativo real (NO 00:00-23:59 calendario)
- FechaOperacion basada en turno/corte/apertura, NO en cierre/cobro
- SoftRestaurant: método MIXTO_VALIDADO (turno + apertura/captura)
- MPRO: método MIXTO_VALIDADO (turno + Co_Fecha)
- Turnos: DESAYUNO (07:00-13:00), COMIDA (13:01-18:59), CENA (19:00-05:59)
- Tableros DEBEN leer únicamente de EDARSAHUB SQL

## Zona Horaria Oficial
**OBLIGATORIA**: `America/Mexico_City` para todos los cálculos de `FechaOperacion`.

## Arquitectura
- **Frontend**: React (`/app/frontend/src/`)
- **Backend**: FastAPI (`/app/backend/`)
- **Base de Datos Primaria**: EDARSAHUB (SQL Server)
- **Legacy**: MongoDB (en proceso de migración)

---

## IMPLEMENTADO P0 (2026-05-20)

### P0.1: Diagnóstico
- ✅ Archivos identificados para modificación
- ✅ Estructura de BD verificada

### P0.2: Configuración Turnos DESAYUNO/COMIDA/CENA
- ✅ `Sistema_TurnosOperativosUnidad` actualizada via API
- ✅ COMIDA_CENA legacy desactivado
- ✅ Turnos separados: DESAYUNO, COMIDA, CENA
- ✅ Configuración por unidad (ORIGEN con desayuno, demás sin)

### P0.3: Refactor operational_window.py
- ✅ Eliminado hardcode 13:00-06:00
- ✅ Nueva estructura `ResultadoVentanaOperativa`
- ✅ Consulta `Sistema_TurnosOperativosUnidad` por unidad
- ✅ Soporte para `cruza_medianoche`
- ✅ Tolerancia de inicio
- ✅ Zona horaria `America/Mexico_City` obligatoria

### P0.4: Refactor sync_comercial_abiertas_v2_job.py
- ✅ Import de `ResultadoVentanaOperativa`
- ✅ Logs incluyen turno operativo detectado
- ✅ Clasificación por turno
- ✅ Mantiene anti-$0 y lock

### P0.5: Eliminar LIVE-C del Tablero Ejecutivo
- ✅ **ELIMINADO** modo LIVE-C para Ventas del Día
- ✅ Nuevo modo `EDARSAHUB_VENTAS_DIA`
- ✅ `live_status=LIVE_NOT_APPLICABLE`
- ✅ `source_period="EDARSAHUB_SQL"`
- ✅ Lee de `Comercial_Ventas_Dia_Abiertas_v2`
- ✅ SoftRestaurant: EDARSAHUB SQL (no tempcheques live)
- ✅ MPRO: EDARSAHUB SQL (no API_LOCAL)
- ✅ Mapeo canónico: ORIGEN→'ORIGEN', QRO→'130QRO' (NO LIKE ni inferencias)

### P0.6: Validación Comparativa
- ✅ Tablero Ejecutivo: EDARSAHUB_SQL ✅
- ✅ Tablero Comercial V2: EDARSAHUB_SQL ✅
- ✅ Sin consultas LIVE en ningún tablero

### P0.8-P0.15: Lock Anti-Concurrencia y Cierre P0 (2026-05-21)
- ✅ **P0.8**: Lock anti-concurrencia implementado con tabla `Sync_Control_Ejecuciones`
- ✅ **P0.9**: Validación sintáctica `py_compile` exitosa
- ✅ **P0.10**: Ejecución manual del job `execute_sync_comercial_abiertas_v2()` exitosa
  - run_id: `ABIERTA-20260521-012819-c02a`
  - 3 unidades sincronizadas (ORIGEN, 130QRO, 130MID)
  - 2 unidades con error esperado (CIENFUEGOS, ESTELAR - red/credenciales)
- ✅ **P0.11**: Datos guardados en `Comercial_Ventas_Dia_Abiertas_v2`
- ✅ **P0.12**: Lock registrado en SQL con Status=PARTIAL, Duration=262s
- ✅ **P0.13**: Tablero Ejecutivo configurado SQL-only (data_type=EDARSAHUB_VENTAS_DIA)
- ✅ **P0.14**: Tablero Comercial V2 SQL-only
- ✅ **P0.15**: Documentación actualizada

### Corrección Regresión Menú Servidores
- **Problema**: `GET /api/servers` retornaba HTTP 500 con `ResponseValidationError`
- **Solución**: Garantizar valores por defecto en `_sql_row_to_server_dict()`

---

## IMPLEMENTADO (2026-05-23)

### P0.16: Campos Auditoría Obligatorios en Tablero Ejecutivo ✅
- **Problema**: El JSON del Tablero Ejecutivo no incluía explícitamente los campos `data_type` requeridos para validación SQL-Only.
- **Solución**: 
  - Agregado parámetro `data_type` a `build_unit_response()` en `service.py`
  - Actualizado todas las llamadas en `routes.py` con `data_type=data_type`
- **Validación**: Endpoint `/comercial/tablero-ejecutivo?anio=-1` retorna:
  - `source_period: EDARSAHUB_SQL` ✅
  - `data_type: EDARSAHUB_VENTAS_DIA` ✅
  - `live_status: LIVE_NOT_APPLICABLE` ✅

### P0.17: Sincronización Offline Compras/Operaciones ✅
- **Problema**: Endpoints `/compras/inventarios-fisicos` y `/compras/pedidos-vigentes` consultaban en vivo a servidores físicos (CIENFUEGOS, etc.) causando timeouts severos.
- **Solución HÍBRIDA implementada**: 
  1. Primero intenta leer de tablas EDARSAHUB Sync
  2. Si Sync está vacío, hace **fallback a consulta LIVE** al servidor físico
  - Esto permite que la UI funcione aunque las tablas Sync no estén pobladas
- **Archivos modificados**:
  - `/app/backend/modules/compras/sync_service.py`
  - `/app/backend/server.py` (endpoints con estrategia híbrida)

### P0.18: Job Background Sync Compras ✅
- **Archivo**: `/app/backend/core/scheduler/jobs/sync_compras_job.py`
- **Función**: Sincroniza inventarios y requisiciones desde servidores físicos hacia EDARSAHUB SQL
- **Frecuencia**: Cada 30 minutos (configurable via `SCHEDULER_SYNC_COMPRAS_INTERVAL_SECONDS`)
- **Lock**: Anti-concurrencia SQL en tabla `Sync_Control_Ejecuciones`
- **Endpoint manual**: `POST /api/admin/sync/compras?dry_run=true|false`
- **NOTA**: Solo funciona en producción donde hay acceso a servidores físicos

### P0.19: Sistema de Detección en Tiempo Real ✅
- **Arquitectura**: Polling Incremental con Checkpoints (Opción A), preparado para Service Broker (Opción C)
- **Archivos**:
  - `/app/backend/modules/compras/eventos_compras.py` (Sistema de eventos desacoplado)
  - `/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py` (Job de detección)
- **Tablas creadas**:
  - `Compras_Sync_Checkpoint` - Guarda último folio/fecha por servidor
  - `Compras_Eventos_Pendientes` - Cola de eventos para informes
  - `Compras_Informes_Config` - Configuración de informes automáticos
- **Endpoints**:
  - `POST /api/admin/detect/compras` - Ejecutar detección manual
  - `GET /api/admin/compras/checkpoints` - Ver estado de checkpoints
  - `GET /api/admin/compras/eventos-pendientes` - Ver cola de eventos
  - `POST /api/admin/compras/procesar-eventos` - Procesar eventos manualmente
- **Frecuencia**: Cada 2 minutos (configurable via `COMPRAS_POLLING_INTERVAL`)
- **Latencia**: 2-3 minutos (migrable a milisegundos con Service Broker)

### P1.1: Reset Contraseña Usuario Ricardo ✅
- **Usuario**: `ricardo@edarsa.com.mx`
- **Tabla**: `Usuario_Catalogo` (EDARSAHUB)
- **Nueva contraseña**: `Asdf1478@@`
- **Validación**: Login exitoso via API

---

## IMPLEMENTADO (2026-05-22)

### Integración VTiger CRM - Backend Completo ✅
- **URL**: https://saligula.hostw3b.com
- **Auth**: Challenge-Response via webservice.php (MD5 token)
- **Módulos VTiger disponibles**: 39 (Contacts, Leads, Accounts, Products, Invoice, etc.)
- **Archivos creados/modificados**:
  - `/app/backend/modules/crm/vtiger_client.py` - Cliente con autenticación challenge-response
  - `/app/backend/modules/crm/service.py` - Lógica de negocio con auto-asignación de user_id
  - `/app/backend/modules/crm/routes.py` - Endpoints REST
  - `/app/backend/server.py` - Registro del router CRM
- **Testing**: Contacto y Lead creados exitosamente via API

### Bug Fix: Captura de Inventario Físico en MPRO
- **Problema**: "No se encontraron productos en las requisiciones seleccionadas" al intentar capturar inventario físico en Auditoría Operativa.
- **Causa Raíz**: 
  1. `validate_server_access_by_empresa` buscaba usuarios en MongoDB (`db.users`) en lugar de EDARSAHUB SQL
  2. El endpoint `productos-para-captura` no soportaba el esquema MPRO donde los productos están directamente en `Orden_Compra` (no en tabla de detalles)
  3. `SOFTRESTAURANT_PRO` no estaba en el mapa de normalización de system_type
- **Solución**:
  1. ✅ Actualizado `validate_server_access_by_empresa` para usar `get_current_user` (SQL-only)
  2. ✅ Agregado soporte para consultar `Orden_Compra` directamente en MPRO
  3. ✅ Agregado `SOFTRESTAURANT_PRO` y variantes al mapa de normalización
- **Archivos modificados**:
  - `/app/backend/server.py` (endpoint `productos-para-captura` y `validate_server_access_by_empresa`)
  - `/app/backend/core/system_type_utils.py` (normalización de system_type)

---

## CRM ENTERPRISE - PROGRESO

### Fase 1: Infraestructura SQL ✅ (2026-05-23)
- [x] 20 tablas CRM creadas en EDARSAHUB (transaccionales, catálogos, configuración)
- [x] 13 columnas CRM agregadas a `Cliente_Catalogo` (extensión sin duplicar)
- [x] 11 catálogos poblados con datos seed
- [x] Pipeline de Ventas Default configurado (7 etapas con probabilidades)
- [x] Scripts idempotentes: `01_create_crm_tables.sql`, `02_seed_crm_catalogs.sql`

### Fase 2: Backend CRM Nativo ✅ (2026-05-23)
- [x] `repository.py` - CRUD Leads, Oportunidades, Pipeline, Catálogos, Dashboard
- [x] `schemas.py` - 20+ modelos Pydantic para validación
- [x] `native_service.py` - Lógica de negocio CRM
- [x] `native_routes.py` - 13 endpoints REST validados:
  - Leads: CRUD + descalificar + convertir
  - Oportunidades: CRUD + cambiar etapa + cerrar
  - Pipelines: listar + vista Kanban
  - Catálogos: todos + por nombre
  - Dashboard: KPIs y métricas
- [x] Integración con tablas Usuario_Catalogo (via PublicUUID)

### Fase 3: Menú y Rutas Frontend ✅ (2026-05-23)
- [x] Sección CRM agregada a `Layout.js` con submenús
- [x] Rutas CRM registradas en `App.js`
- [x] Páginas implementadas:
  - `CRMDashboard.jsx` - KPIs, gráficos, actividad reciente
  - `LeadsPage.jsx` - Tabla con filtros y paginación
  - `OportunidadesPage.jsx` - Lista con barras de probabilidad
  - `PipelinePage.jsx` - Vista Kanban drag-and-drop
- [x] Columna `PublicUUID` agregada a `Cliente_Catalogo` para relación Oportunidad-Cuenta

### Fase 4: Formularios CRUD ✅ (2026-05-23)
- [x] `LeadForm.jsx` - Formulario completo de creación/edición de leads
- [x] `OportunidadForm.jsx` - Formulario de oportunidades con selección de pipeline/etapa
- [x] `CerrarOportunidadModal.jsx` - Modal para cerrar oportunidades (ganada/perdida)
- [x] `ConvertirLeadModal.jsx` - Wizard de conversión de lead a cuenta/contacto/oportunidad
- [x] Integración de formularios en `LeadsPage.jsx` y `OportunidadesPage.jsx`
- [x] Menús contextuales con acciones (editar, convertir, descalificar, eliminar, cerrar)

### Fase 5: Integración Universal Externa ✅ (2026-05-23)
- [x] **Tablas de Staging SQL** creadas:
  - `CRM_Staging_Leads` - Buffer para leads externos
  - `CRM_Staging_Oportunidades` - Buffer para oportunidades externas
  - `CRM_Staging_Cuentas` - Buffer para cuentas externas
  - `CRM_Integracion_Conectores` - Configuración de conectores
  - `CRM_Integracion_SyncLog` - Historial de sincronizaciones
  - `CRM_Integracion_MapeoEtapas` - Mapeo de etapas entre sistemas
- [x] **Framework de Conectores** implementado:
  - `base_connector.py` - Clase abstracta para todos los conectores
  - `vtiger_connector.py` - Conector VTiger completo (pull leads/opps/cuentas)
  - `staging_service.py` - Servicio CRUD para tablas staging
  - `sync_engine.py` - Motor de sincronización orquestador
- [x] **API REST de Integración** (`/api/crm/integration/`):
  - CRUD Conectores: `GET/POST/PUT/DELETE /conectores`
  - Test conexión: `POST /conectores/{id}/test`
  - Ejecutar sync: `POST /conectores/{id}/sync`
  - Estadísticas staging: `GET /conectores/{id}/staging/stats`
  - Listar staging: `GET /conectores/{id}/staging/leads|oportunidades|cuentas`
  - Historial sync: `GET /conectores/{id}/sync-log`
- [x] **Validación exitosa**:
  - Conexión VTiger verificada ✅
  - Sync ejecutado: 2 leads + 2 cuentas importadas a staging ✅
  - Estado "PENDIENTE" para procesamiento posterior

### Fase 6: Sync Staging → Producción (PRÓXIMA)
- [ ] Job de procesamiento que mueva datos staging → tablas CRM nativas
- [ ] Lógica de deduplicación y matching
- [ ] Resolución de conflictos automática/manual
- [ ] Conectores adicionales: Salesforce, HubSpot, Zoho

---

## PENDIENTE (Otros módulos)

### P0 (Crítico) - CERRADO ✅
- [x] `SERVER_SECRET_KEY` accesible para scheduler
- [x] Lock anti-concurrencia implementado
- [x] Sincronización offline Compras (P0.17-P0.19)
- [x] Campos auditoría en Tablero Ejecutivo (P0.16)

### P1
- [ ] Conectar módulo VTiger CRM con Frontend (backend completado)
- [ ] Errores conexión SoftRestaurant (CIENFUEGOS, ESTELAR) - infraestructura origen
- [ ] Implementar detección de TURNO_EXTENDIDO

### Backlog (P2)
- [ ] Documentación final
- [ ] Migración final para retirar MongoDB

---

## Restricciones Críticas
1. **PROHIBIDO** usar `testing_agent_v3_fork` - solo bash/curl/python
2. Toda fecha de negocio se calcula con `ZoneInfo("America/Mexico_City")`
3. EDARSAHUB SQL es la fuente de verdad
4. **NO LIVE** en tableros - solo EDARSAHUB SQL

## Archivos de Referencia
- `/app/backend/core/utils/operational_window.py` (✅ REFACTORIZADO P0.3)
- `/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py` (✅ REFACTORIZADO P0.4)
- `/app/backend/core/scheduler/jobs/sync_compras_job.py` (✅ NUEVO P0.18 - Job Sync Compras)
- `/app/backend/core/scheduler/jobs/detect_nuevos_compras_job.py` (✅ NUEVO P0.19 - Detección Tiempo Real)
- `/app/backend/modules/compras/eventos_compras.py` (✅ NUEVO P0.19 - Sistema Eventos)
- `/app/backend/modules/comercial/routes.py` (✅ MODIFICADO P0.5 - Sin LIVE-C)
- `/app/backend/modules/comercial/service.py` (✅ MODIFICADO P0.16 - data_type)
- `/app/backend/modules/compras/sync_service.py` (✅ NUEVO P0.17 - Sync Compras)
- `/app/backend/server.py` (✅ MODIFICADO P0.17/P0.18/P0.19 - Endpoints SQL-Only + Admin)
- `/app/backend/core/server_registry.py` (✅ CORREGIDO)
- `/app/backend/api/configuracion_operativa_unidades.py`
- `/app/frontend/src/pages/ConfiguracionOperativaUnidades.jsx`
- `/app/backend/modules/crm/integration/` (✅ NUEVO Fase 5 - Framework Conectores)
- `/app/backend/modules/crm/integration_routes.py` (✅ NUEVO Fase 5 - API Integración)

## Documentos Generados
- `/app/docs/reports/MATRIZ_DEFINITIVA_VENTAS_DIA_SOFTRESTAURANT_MPRO_TURNOS.md`
- `/app/docs/reports/P0_IMPLEMENTACION_VENTAS_DIA_TURNOS_SQLONLY.md`
