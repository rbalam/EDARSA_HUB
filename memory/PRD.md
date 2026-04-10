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
- `/app/backend/server.py` - Backend monolito (18,082 líneas)
- `/app/backend/.env` - Credenciales BD y APIs
- `/app/backend/core/` - Módulos core (scaffolding)
- `/app/backend/modules/` - Módulos de negocio (scaffolding)
- `/app/frontend/src/pages/Compras.js` - Módulo compras con cálculos cliente
- `/app/frontend/src/pages/Servidores.js` - Config SQL y APIs
- `/app/frontend/src/pages/ExploradorBD.js` - Exploración agrupada tablas
- `/app/memory/CATALOGO_FILTROS_EDARSAHUB.md` - Reglas UI y filtros
- `/app/memory/MAPA_MIGRACION.md` - **Plan de migración modular**

## Key API Endpoints
- `/api/compras/auditoria-inventario` - Auditoría de inventarios
- `/api/test-api-connection` - Test conexiones REST
- `/api/servers` - CRUD servidores

## Known Issues
- Servidores SQL pueden entrar en "Cooldown" (5 min) con query malformada
  - Mitigation: `sudo supervisorctl restart backend`
