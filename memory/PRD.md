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
  - ⏸️ Sub-fase 5B-2: Helpers del tablero (pendiente)
  - ⏸️ Sub-fase 5B-3: Endpoints de comercial (pendiente)
- **Fases 6-7**: ⏸️ Pendientes de autorización

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

## Prioritized Backlog

### P0 - Critical
- ~~Scroll horizontal en Pantalla Completa de Auditoría~~ ✅ DONE

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
