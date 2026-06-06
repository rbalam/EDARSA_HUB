# AUDITORÍA PASIVA COMPLETA - EDARSAHUB
## Depuración, Limpieza y Deuda Técnica

**Fecha:** 2026-05-15  
**Autor:** E1 Agent - Arquitecto Senior  
**Clasificación:** Auditoría Pasiva - SIN MODIFICACIONES

---

## 1. RESUMEN EJECUTIVO

### Métricas Globales del Repositorio

| Métrica | Valor | Estado |
|---------|-------|--------|
| **server.py** | 16,408 líneas (692KB) | 🔴 CRÍTICO |
| Endpoints en server.py | 203 | 🔴 ALTO |
| Modelos Pydantic en server.py | 41 | 🔴 ALTO |
| Archivos Python | 393 | ✅ Normal |
| Archivos JS/JSX | 35,787 | ⚠️ (incluye node_modules) |
| Referencias MongoDB | 918 | 🟡 MEDIO |
| Colecciones MongoDB específicas | 235 | 🟡 MEDIO |
| Queries f-string (riesgo SQL injection) | 58 | 🔴 ALTO |
| Usos date.today()/datetime.now() | 60+ | 🔴 ALTO |
| Comentarios TODO/LEGACY/FIXME | 458 | 🟡 MEDIO |
| Archivos backup/old | 7 | 🟢 BAJO |
| Verificaciones RBAC server.py | 156 | ✅ Bueno |
| Tests backend | 57 archivos | ✅ Normal |
| Tests frontend | 0 archivos | 🔴 CRÍTICO |
| Tamaño node_modules | 1.1 GB | 🟡 Normal |

### Conclusión Principal
**server.py es un archivo monolítico de 16,408 líneas que debe refactorizarse urgentemente.** Contiene 203 endpoints, 41 modelos Pydantic y 182 imports. Esto representa un riesgo grave de mantenibilidad, testabilidad y regresión.

---

## 2. MAPA REAL DEL REPOSITORIO

```
/app
├── backend/                    16 MB
│   ├── server.py               692 KB (16,408 líneas) ⚠️ MONOLITO
│   ├── core/                   
│   │   ├── server_registry.py  2,416 líneas
│   │   ├── db.py               1,478 líneas
│   │   ├── security.py         892 líneas
│   │   ├── empresa_resolver.py 740 líneas ✅ NUEVO
│   │   └── ... (17 módulos core)
│   ├── modules/
│   │   ├── comercial/          ✅ Modularizado parcialmente
│   │   ├── comercial_v2/       ✅ Nueva arquitectura
│   │   ├── finanzas/           ✅ Modularizado
│   │   ├── compras/            ✅ Modularizado
│   │   ├── rh/                 ✅ Modularizado
│   │   ├── api_connections/    ✅ SQL-First
│   │   └── ... (20 módulos)
│   ├── catalogo/               484 líneas hardcodeadas
│   ├── scripts/                23 scripts de mantenimiento
│   └── tests/                  57 archivos
├── frontend/                   1.1 GB
│   ├── src/
│   │   ├── pages/              34,327 líneas total
│   │   │   ├── Compras.js      3,582 líneas ⚠️
│   │   │   ├── Reportes.js     3,541 líneas ⚠️
│   │   │   ├── Comercial.js    2,931 líneas ⚠️
│   │   │   └── ...
│   │   └── components/
│   └── node_modules/           1.1 GB
├── docs/                       5.1 MB
│   ├── reports/                132 archivos
│   └── backups/
├── memory/                     1.1 MB
│   └── PRD.md
├── backups/                    3 directorios
├── snapshots/                  1 directorio
└── test_reports/               50+ iteraciones
```

---

## 3. TOP 20 HALLAZGOS CRÍTICOS

| # | Severidad | Hallazgo | Impacto |
|---|-----------|----------|---------|
| 1 | 🔴 CRÍTICO | server.py tiene 16,408 líneas y 203 endpoints | Inmantenible |
| 2 | 🔴 CRÍTICO | 58 queries SQL con f-string interpolation | SQL Injection |
| 3 | 🔴 CRÍTICO | 0 tests de frontend | Sin cobertura |
| 4 | 🔴 CRÍTICO | 60+ usos de datetime.now()/date.today() sin ventana operativa | Fechas incorrectas |
| 5 | 🔴 ALTO | 41 modelos Pydantic dentro de server.py | Desorganizado |
| 6 | 🔴 ALTO | 918 referencias a MongoDB dispersas | Migración incompleta |
| 7 | 🔴 ALTO | Catálogo SQL hardcodeado en Python (20+ consultas) | Sin versionado |
| 8 | 🟡 MEDIO | 458 comentarios TODO/LEGACY/FIXME | Deuda técnica |
| 9 | 🟡 MEDIO | Archivos .backup en frontend (3 archivos) | Limpieza pendiente |
| 10 | 🟡 MEDIO | node_modules de 1.1GB versionado implícitamente | Espacio desperdiciado |
| 11 | 🟡 MEDIO | Compras.js tiene 3,582 líneas | Componente gigante |
| 12 | 🟡 MEDIO | 7 archivos .bak/.backup en repo | Limpieza pendiente |
| 13 | 🟡 MEDIO | 50+ test_reports viejos | Limpieza pendiente |
| 14 | 🟡 MEDIO | __pycache__ en múltiples directorios | .gitignore incompleto |
| 15 | 🟢 BAJO | server_registry.py tiene 2,416 líneas | Candidato a split |
| 16 | 🟢 BAJO | 182 imports en server.py | Simplificar |
| 17 | 🟢 BAJO | Backups manuales en /app/backups | Documentar o limpiar |
| 18 | 🟢 BAJO | Snapshots manuales en /app/snapshots | Documentar o limpiar |
| 19 | 🟢 INFO | @google/generative-ai en frontend | Verificar uso |
| 20 | 🟢 INFO | jspdf/xlsx en frontend | Dependencias pesadas |

---

## 4. TABLA DE HALLAZGOS DETALLADOS

| ID | Severidad | Módulo | Archivo | Hallazgo | Riesgo | Recomendación | Autorización | Fase |
|----|-----------|--------|---------|----------|--------|---------------|--------------|------|
| H001 | 🔴 CRÍTICO | Backend | server.py | 16,408 líneas, 203 endpoints | Regresión, bugs | Migrar endpoints a módulos | Sí | 1 |
| H002 | 🔴 CRÍTICO | Backend | server.py | 41 modelos Pydantic mezclados | Desorganización | Mover a schemas/ | Sí | 1 |
| H003 | 🔴 CRÍTICO | Seguridad | Múltiples | 58 f-string SQL queries | SQL Injection | Usar parámetros | Sí | 2 |
| H004 | 🔴 CRÍTICO | Frontend | - | 0 tests unitarios | Sin cobertura | Implementar Jest | Sí | 3 |
| H005 | 🔴 ALTO | Comercial | routes.py | datetime.now() en 10+ lugares | Fecha incorrecta | Usar get_operational_window | Sí | 2 |
| H006 | 🔴 ALTO | Catálogo | catalogo_consultas.py | 20+ consultas hardcodeadas | Sin versionado | Migrar a SQL | Sí | 3 |
| H007 | 🟡 MEDIO | Backend | Múltiples | 918 refs MongoDB | Migración parcial | Auditar y deprecar | Sí | 4 |
| H008 | 🟡 MEDIO | Backend | server.py | 182 imports | Complejidad | Consolidar | Sí | 1 |
| H009 | 🟡 MEDIO | Frontend | Compras.js | 3,582 líneas | Componente gigante | Dividir | Sí | 5 |
| H010 | 🟡 MEDIO | Frontend | Reportes.js | 3,541 líneas | Componente gigante | Dividir | Sí | 5 |
| H011 | 🟡 MEDIO | Repo | Múltiples | 7 archivos .bak/.backup | Desorden | Eliminar | No | 6 |
| H012 | 🟡 MEDIO | Backend | scripts/ | Scripts legacy no documentados | Riesgo ejecución | Documentar | No | 6 |
| H013 | 🟡 MEDIO | Repo | test_reports/ | 50+ reports viejos | Espacio | Limpiar antiguos | No | 6 |
| H014 | 🟡 MEDIO | Backend | Múltiples | 458 TODO/LEGACY | Deuda técnica | Triagear | No | 7 |
| H015 | 🟢 BAJO | Core | server_registry.py | 2,416 líneas | Complejidad | Considerar split | Sí | 8 |
| H016 | 🟢 BAJO | Core | db.py | 1,478 líneas | Complejidad | Mantener como está | No | - |
| H017 | 🟢 BAJO | Repo | backups/ | 3 carpetas backup | Documentar | Evaluar retención | No | 6 |
| H018 | 🟢 BAJO | Repo | snapshots/ | 1 carpeta snapshot | Documentar | Evaluar retención | No | 6 |
| H019 | 🟢 INFO | Frontend | package.json | @google/generative-ai | Dependencia | Verificar uso | No | - |
| H020 | 🟢 INFO | Frontend | package.json | xlsx + jspdf (pesadas) | Tamaño bundle | Evaluar lazy load | No | - |

---

## 5. MATRIZ MONGODB

### Colecciones Detectadas y Clasificación

| Colección | Referencias | Clasificación | Estado Actual |
|-----------|-------------|---------------|---------------|
| `db.servers` | 235 | FALLBACK_LEGACY_AUTORIZADO | 0 documentos, SQL-First |
| `db.users` | 45 | FUNCIONAL_CRITICO_A_MIGRAR | Auth principal |
| `db.consultas_custom` | 15 | CODIGO_MUERTO_ELIMINABLE | 0 documentos |
| `db.sucursales` | 8 | FALLBACK_LEGACY_AUTORIZADO | SQL-First |
| `db.query_templates` | 12 | CACHE_TEMPORAL_DOCUMENTAR | Histórico |
| `db.alerts` | 6 | CACHE_TEMPORAL_DOCUMENTAR | Notificaciones |
| `db.kpis_comerciales` | 25 | FALLBACK_LEGACY_AUTORIZADO | SQL-First |
| `db.audit_logs` | 18 | CACHE_TEMPORAL_DOCUMENTAR | Bitácora |

### Archivos con Mayor Dependencia MongoDB

| Archivo | Referencias | Prioridad Migración |
|---------|-------------|---------------------|
| server.py | 89 | 🔴 ALTA |
| modules/comercial/repository.py | 45 | 🟡 MEDIA |
| modules/auth/repository.py | 32 | 🔴 ALTA |
| modules/rh/repository.py | 28 | 🟡 MEDIA |
| core/cerebro.py | 22 | 🟢 BAJA |

### Patrones init_*_module(db) Detectados

```python
# 8 módulos requieren inicialización MongoDB:
init_comercial_module(database)      # modules/comercial
init_rh_module(database)             # modules/rh
init_importador_repository(database) # modules/rh/importador
init_catalogos_module(db)            # modules/catalogos
init_api_connections_repository(db)  # modules/api_connections
init_comercial_repository(database)  # modules/comercial
init_kpis_repository(database)       # modules/comercial
init_rh_repository(database)         # modules/rh
```

---

## 6. MATRIZ SERVER.PY

### Análisis del Monolito

| Categoría | Cantidad | Líneas Estimadas | Migración |
|-----------|----------|------------------|-----------|
| Endpoints | 203 | ~8,000 | Migrar a módulos |
| Modelos Pydantic | 41 | ~1,500 | Mover a schemas/ |
| Funciones Helper | ~50 | ~2,500 | Mover a utils/ |
| Imports | 182 | ~200 | Consolidar |
| Comentarios/Docs | - | ~1,500 | Mantener |
| Configuración | - | ~500 | Mover a config/ |

### Endpoints Candidatos a Migrar (Top 20)

| Endpoint | Líneas | Módulo Destino |
|----------|--------|----------------|
| `/servers/*` | ~600 | modules/servers/routes.py |
| `/catalogo/*` | ~400 | modules/catalogo/routes.py |
| `/auditoria/*` | ~350 | modules/auditoria/routes.py |
| `/dashboard/*` | ~300 | modules/dashboard/routes.py |
| `/usuarios/*` | ~250 | modules/usuarios/routes.py |
| `/alertas/*` | ~200 | modules/alertas/routes.py |
| `/sucursales/*` | ~200 | modules/sucursales/routes.py |
| `/email/*` | ~150 | modules/email/routes.py |
| `/export/*` | ~150 | modules/export/routes.py |
| `/rbac/*` | ~500 | modules/rbac/routes.py |

### Modelos a Extraer

```python
# server.py líneas 476-747: 15 modelos de servidor
TestApiRequest, UserRole, User, UserCreate, UserLogin
ServerQueryConfig, Server, ServerCreate
QueryValidationRequest, QueryValidationResponse
QueryTemplate, QueryTemplateCreate
InventoryReport, Alert, AlertCreate

# server.py líneas 5145-5150: Modelos inventario
AlmacenComparativo, ComparativoInventariosRequest

# server.py líneas 6579-8668: Modelos operativos
ParametrosCompra, CalculoPedidoRequest
AuditoriaOperativaRequest, ProductosParaCapturaRequest
DetalleMovimientosRequest, DetalleConsumosRequest
AnalisisComprasRequest

# server.py líneas 15142-16139: Modelos RBAC
PermisoAsignacionRequest, RolAsignacionRequest
AsignarPerfilRequest, RetirarPerfilRequest
AsignarAlcanceRequest, RetirarAlcanceRequest
```

---

## 7. MATRIZ FECHA OPERATIVA

### Usos Peligrosos Detectados

| Archivo | Línea | Uso | Riesgo | Acción |
|---------|-------|-----|--------|--------|
| comercial/routes.py | 383 | `datetime.now()` | Fecha calendario | Migrar |
| comercial/routes.py | 457 | `datetime.now()` | Fecha calendario | Migrar |
| comercial/routes.py | 494 | `datetime.now()` | Fecha calendario | Migrar |
| comercial/routes.py | 1515 | `datetime.now()` | Fecha calendario | Migrar |
| comercial/routes.py | 1788 | `datetime.now()` | Fecha calendario | Migrar |
| comercial/routes.py | 1994 | `datetime.now()` | Fecha calendario | Migrar |
| comercial/routes.py | 2320 | `datetime.now()` | Fecha calendario | Migrar |
| comercial/routes.py | 2593 | `datetime.now()` | Fecha calendario | Migrar |
| comercial/routes.py | 3437 | `datetime.now()` | Fecha calendario | Migrar |
| comercial/routes.py | 3882 | `datetime.now()` | Fecha calendario | Migrar |
| adapters.py | 261-264 | `GETDATE()` | Fecha SQL Server | Evaluar |
| rh/repository.py | 1779-1780 | `GETDATE()` | Fecha SQL Server | OK (RH) |

### Usos Correctos de Ventana Operativa

| Archivo | Estado |
|---------|--------|
| core/utils/operational_window.py | ✅ Helper central |
| comercial/service.py | ✅ Usa helper |
| scheduler/jobs/sync_comercial_abiertas_v2_job.py | ✅ Usa helper |
| comercial_v2/routes.py | ✅ Usa helper |

### Módulos Pendientes de Migración

| Módulo | Archivos | Prioridad |
|--------|----------|-----------|
| Comercial | routes.py (10 usos) | 🔴 ALTA |
| Compras | routes.py (2 usos) | 🟡 MEDIA |
| Finanzas | service.py (1 uso) | 🟢 BAJA |

---

## 8. MATRIZ LIVE vs EDARSAHUB SQL

### Estado por Módulo

| Módulo | Fuente Principal | LIVE | EDARSAHUB | Snapshot |
|--------|------------------|------|-----------|----------|
| Tablero Ejecutivo | EDARSAHUB SQL | ❌ | ✅ | ✅ |
| Comercial | EDARSAHUB SQL | ❌ | ✅ | ✅ |
| Compras | EDARSAHUB SQL | ⚠️ Parcial | ✅ | ⚠️ |
| Finanzas | EDARSAHUB SQL | ⚠️ Parcial | ✅ | ⚠️ |
| Propinas TPV | EDARSAHUB SQL | ❌ | ✅ | ✅ |
| Inventarios | Mixto | ✅ LIVE | ⚠️ | ❌ |
| RH | EDARSAHUB SQL | ❌ | ✅ | ❌ |
| Servidores | EDARSAHUB SQL | ❌ | ✅ | N/A |

### Riesgos $0 Falso

| Escenario | Módulo | Estado | Mitigación |
|-----------|--------|--------|------------|
| Turno cerrado Soft | Comercial | ✅ Mitigado | Protección anti-$0 |
| API Local offline | Comercial | ✅ Mitigado | Fallback snapshot |
| SQL Server timeout | Comercial | ✅ Mitigado | Conserva último dato |
| MPRO sin datos | Comercial | ✅ Mitigado | get_operational_window |

---

## 9. MATRIZ FRONTEND

### Archivos Más Grandes (Candidatos a Split)

| Archivo | Líneas | Recomendación |
|---------|--------|---------------|
| Compras.js | 3,582 | Dividir en 3-4 componentes |
| Reportes.js | 3,541 | Dividir por tipo de reporte |
| Comercial.js | 2,931 | Dividir tabs en componentes |
| RecursosHumanos.js | 2,636 | Dividir secciones |
| Servidores.js | 2,155 | Dividir CRUD/Config |

### Patrones de Autenticación

| Patrón | Usos | Estado |
|--------|------|--------|
| `credentials: 'include'` | 45 | ✅ Correcto (cookie httpOnly) |
| `Authorization: Bearer` | 0 | ✅ Deprecado correctamente |
| `api.get/post` (centralizado) | 500+ | ✅ Correcto |
| `fetch` directo | 150+ | ⚠️ Evaluar migración a api.js |

### Dependencias Pesadas

| Dependencia | Tamaño Est. | Uso |
|-------------|-------------|-----|
| xlsx | ~500KB | Export Excel |
| jspdf + autotable | ~300KB | Export PDF |
| recharts | ~200KB | Gráficos |
| @google/generative-ai | ~100KB | IA (verificar uso) |

---

## 10. MATRIZ SEGURIDAD

### Riesgos Detectados

| ID | Categoría | Hallazgo | Severidad | Estado |
|----|-----------|----------|-----------|--------|
| S01 | SQL Injection | 58 f-string queries | 🔴 CRÍTICO | Pendiente |
| S02 | Secrets | Passwords cifrados AES | ✅ | Implementado |
| S03 | CORS | Configurado por ENV | ✅ | OK |
| S04 | Cookies | httpOnly habilitado | ✅ | OK |
| S05 | RBAC | 156 verificaciones en server.py | ✅ | OK |
| S06 | API Keys | Enmascaradas en respuestas | ✅ | OK |

### Archivos con Riesgo SQL Injection

```
modules/comercial/historical_kpis_repository.py (20 queries)
modules/rh/repository.py (15 queries)
modules/api_connections/repository.py (8 queries)
core/server_registry.py (10 queries)
server.py (5 queries)
```

---

## 11. MATRIZ BACKUPS/SNAPSHOTS

### Contenido Detectado

| Ruta | Contenido | Fecha | Acción |
|------|-----------|-------|--------|
| /app/backups/server.py.pre_fase1a_* | Backup server.py | 2026-04-16 | Conservar 90 días |
| /app/backups/comercial_diagnosis_20260420/ | Diagnóstico | 2026-04-20 | Documentar |
| /app/backups/20260508_1934_auth_rbac_mongodb/ | Auth migration | 2026-05-08 | Conservar |
| /app/snapshots/20260419_tablero_fix/ | Fix tablero | 2026-04-19 | Conservar |
| /app/frontend/src/pages/*.backup | 3 archivos | Varios | Eliminar |

### Archivos .gitignore Faltantes

```gitignore
# Agregar a .gitignore:
*.bak
*.backup
*.old
__pycache__/
*.pyc
.coverage
test_reports/iteration_*.json  # Conservar solo últimos 10
```

---

## 12. PLAN DE LIMPIEZA POR FASES

### FASE 1: Refactor server.py (ALTA PRIORIDAD)
- Extraer 15 modelos Pydantic a `backend/schemas/`
- Migrar endpoints `/servers/*` a `modules/servers/routes.py`
- Migrar endpoints `/catalogo/*` a `modules/catalogo/routes.py`
- Migrar endpoints `/auditoria/*` a `modules/auditoria/routes.py`
- **Riesgo:** ALTO - Requiere pruebas exhaustivas
- **Estimación:** 3-5 sesiones

### FASE 2: Sanitización SQL (CRÍTICA)
- Auditar 58 f-string queries
- Implementar `_escape_sql` o parámetros
- Priorizar módulos con input de usuario
- **Riesgo:** MEDIO - Cambios quirúrgicos
- **Estimación:** 2-3 sesiones

### FASE 3: Ventana Operativa (MEDIA)
- Migrar 10 usos de `datetime.now()` en comercial/routes.py
- Documentar regla de negocio
- **Riesgo:** BAJO - Helper ya existe
- **Estimación:** 1 sesión

### FASE 4: MongoDB Cleanup (BAJA)
- Auditar 918 referencias
- Marcar como MONGODB_LEGACY
- Documentar migración pendiente
- **Riesgo:** BAJO - No funcional
- **Estimación:** 2 sesiones

### FASE 5: Frontend Components (MEDIA)
- Dividir Compras.js (3,582 → 3-4 archivos)
- Dividir Reportes.js (3,541 → 3-4 archivos)
- **Riesgo:** MEDIO - UI testing requerido
- **Estimación:** 3-4 sesiones

### FASE 6: Limpieza Archivos (BAJA)
- Eliminar .backup files
- Limpiar test_reports antiguos
- Actualizar .gitignore
- **Riesgo:** MUY BAJO
- **Estimación:** 1 sesión

---

## 13. ORDEN RECOMENDADO DE EJECUCIÓN

1. 🔴 **FASE 2** - Sanitización SQL (Seguridad primero)
2. 🔴 **FASE 3** - Ventana Operativa (Bug de fechas)
3. 🟡 **FASE 1** - Refactor server.py (Mantenibilidad)
4. 🟡 **FASE 6** - Limpieza archivos (Quick win)
5. 🟢 **FASE 4** - MongoDB cleanup (Deuda técnica)
6. 🟢 **FASE 5** - Frontend components (Opcional)

---

## 14. VALIDACIONES OBLIGATORIAS DE NO REGRESIÓN

### Tests Mínimos Antes de Cada Fase

```bash
# 1. Login/Logout
curl -X POST /api/auth/login -d '{"email":"admin@...", "password":"..."}'

# 2. Tablero Ejecutivo
curl /api/comercial/tablero-ejecutivo

# 3. Servidores
curl /api/servers

# 4. Comercial
curl /api/comercial/ventas-dia?unidad=ORIGEN

# 5. Compras
curl /api/compras/ordenes

# 6. Finanzas
curl /api/finanzas/cuentas

# 7. RBAC
curl /api/usuarios
curl /api/roles
```

### Módulos Protegidos (NO TOCAR sin autorización)

- Tablero Ejecutivo
- Comercial (ventas del día, KPIs)
- Auth/Login
- RBAC/Permisos
- Scheduler Jobs

---

## 15. LISTA DE ARCHIVOS QUE NO DEBEN TOCARSE TODAVÍA

```
/app/backend/modules/comercial/service.py        # Lógica de negocio crítica
/app/backend/modules/comercial/routes.py         # Solo fase 3 (fechas)
/app/backend/core/utils/operational_window.py    # Helper estable
/app/backend/core/empresa_resolver.py            # Recién implementado
/app/backend/modules/auth/                       # Auth funcional
/app/backend/core/security.py                    # Seguridad estable
/app/backend/core/db.py                          # Conexiones estables
/app/frontend/src/pages/TableroEjecutivo.js      # UI estable
```

---

## 16. LISTA DE ARCHIVOS CANDIDATOS A REFACTOR

```
# PRIORIDAD ALTA
/app/backend/server.py                           # 16,408 líneas - Dividir
/app/backend/core/server_registry.py             # 2,416 líneas - Considerar

# PRIORIDAD MEDIA
/app/frontend/src/pages/Compras.js               # 3,582 líneas - Dividir
/app/frontend/src/pages/Reportes.js              # 3,541 líneas - Dividir
/app/frontend/src/pages/Comercial.js             # 2,931 líneas - Dividir

# PRIORIDAD BAJA
/app/backend/catalogo/catalogo_consultas.py      # Migrar a SQL
/app/backend/modules/comercial/routes.py         # Solo fechas
```

---

## 17. LISTA DE ARCHIVOS CANDIDATOS A ELIMINACIÓN

```
# ELIMINAR (seguros)
/app/frontend/src/pages/Finanzas.js.backup
/app/frontend/src/pages/Dashboard.js.backup
/app/frontend/src/pages/AutorizacionCompras.js.backup
/app/snapshots/20260419_tablero_fix/*.bak

# EVALUAR ANTES DE ELIMINAR
/app/test_reports/iteration_1.json .. iteration_30.json  # Conservar últimos 10
/app/backups/comercial_diagnosis_20260420/              # Documentar primero

# NO ELIMINAR SIN CONFIRMACIÓN
/app/backups/server.py.pre_fase1a_*                     # Backup de seguridad
/app/backups/20260508_1934_auth_rbac_mongodb/           # Migración auth
```

---

## 18. CONCLUSIÓN EJECUTIVA

### Estado General: 🟡 ESTABLE CON DEUDA TÉCNICA SIGNIFICATIVA

**Fortalezas:**
- ✅ EDARSAHUB SQL implementado como fuente autoritativa
- ✅ EmpresaResolver funcionando correctamente
- ✅ Ventana operativa implementada en scheduler
- ✅ MongoDB desacoplado para servidores (0 documentos)
- ✅ Seguridad de secrets (AES encryption, httpOnly cookies)
- ✅ RBAC implementado con 156+ verificaciones

**Debilidades Críticas:**
- 🔴 server.py es un monolito de 16K líneas
- 🔴 58 queries SQL vulnerables a injection
- 🔴 10+ usos de datetime.now() sin ventana operativa
- 🔴 0 tests de frontend
- 🟡 458 comentarios de deuda técnica sin resolver

**Recomendación:**
Priorizar **FASE 2 (SQL Sanitization)** y **FASE 3 (Ventana Operativa)** antes del refactor de server.py, ya que representan riesgos de seguridad y bugs funcionales activos.

---

*Documento generado como auditoría pasiva. NO se realizaron modificaciones al código.*  
*Siguiente paso: Solicitar autorización para FASE 2 (Sanitización SQL)*
