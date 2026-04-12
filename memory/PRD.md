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
- **Fases 6C-6H, 7**: ⏸️ Pendientes de autorización

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
