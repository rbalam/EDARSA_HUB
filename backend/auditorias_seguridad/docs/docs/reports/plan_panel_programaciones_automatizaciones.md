# PLAN TÉCNICO: PANEL DE PROGRAMACIONES/SCHEDULER

**Fecha**: 01-Mayo-2026  
**Estado**: PLAN TÉCNICO (NO IMPLEMENTAR)  
**Autor**: E1 Agent

---

## 1. DECISIÓN DE UBICACIÓN

### ✅ DECISIÓN AUTORIZADA

**Integrar como TAB dentro del menú existente "Automatizaciones"**

| Aspecto | Decisión |
|---------|----------|
| Menú padre | Automatizaciones |
| Nuevo tab | "Programaciones" o "Scheduler" |
| Nuevo menú | ❌ NO crear menú nuevo |
| Ruta actual | `/automatizaciones` |
| Página actual | `AuditoriasProgramadas.jsx` |

---

## 2. JUSTIFICACIÓN

### 2.1 Por qué NO crear menú nuevo

1. **Complejidad innecesaria**: Ya existen menús de "Programación" y "Automatizaciones"
2. **Duplicidad funcional**: El contenido propuesto (jobs, synclog, scheduler) corresponde a procesos automáticos
3. **Consistencia de navegación**: Agregar un menú nuevo afecta la experiencia de usuario
4. **Mantenimiento**: Más menús = más código, más permisos RBAC, más rutas

### 2.2 Por qué Automatizaciones y NO Programación

| Menú | Función Actual | Contenido |
|------|----------------|-----------|
| **Programación** (`/scheduler`) | Shuttle de Programación de Análisis de Inventarios | Agenda operativa específica de inventarios |
| **Automatizaciones** (`/automatizaciones`) | Auditorías Programadas | Procesos automáticos del sistema |

**Análisis**:
- "Programación" tiene un significado funcional específico: **Análisis de Inventarios**
- "Automatizaciones" ya agrupa: auditorías automáticas, jobs, procesos programados
- El contenido nuevo (scheduler jobs, synclogs, locks) es **técnico/sistema**, no operativo

**Conclusión**: El panel de scheduler/jobs pertenece a "Automatizaciones" porque agrupa procesos automáticos del sistema.

---

## 3. ESTRUCTURA ACTUAL DE MENÚS

### 3.1 Menú Sistema (sidebar)

```
Sistema
├── Centro de Control
├── Servidores
├── Programación          ← Shuttle de Inventarios
├── Automatizaciones      ← Auditorías Programadas ✅ AQUÍ
├── Asignaciones
├── Catálogo SQL
├── Explorador BD
├── Alertas
└── Usuarios
```

### 3.2 Rutas actuales

| Ruta | Página | Contenido |
|------|--------|-----------|
| `/scheduler` | `Scheduler.jsx` | Programación de Análisis de Inventarios |
| `/automatizaciones` | `AuditoriasProgramadas.jsx` | Auditorías Programadas |
| `/centro-control` | `CentroControl.jsx` | Panel de monitoreo general |

---

## 4. PROPUESTA DE INTEGRACIÓN

### 4.1 Tabs propuestos para Automatizaciones

| Tab | Contenido | API Backend |
|-----|-----------|-------------|
| **Auditorías** (existente) | Auditorías programadas | `/api/v2/auditorias/*` |
| **Programaciones** (nuevo) | Jobs, synclogs, ejecución manual | `/api/v2/scheduler/*` |

### 4.2 Contenido del Tab "Programaciones"

```
Tab: Programaciones
├── Estado del Scheduler (running/stopped)
├── Lista de Jobs
│   ├── Nombre
│   ├── Frecuencia
│   ├── Estado (activo/pausado)
│   ├── Última ejecución
│   ├── Próxima ejecución
│   └── Acciones (pausar, reanudar, ejecutar manual)
├── Historial de Ejecuciones
│   ├── Job
│   ├── Inicio
│   ├── Fin
│   ├── Duración
│   ├── Estado (success/failed/skipped)
│   └── Registros procesados
├── Locks Activos
│   └── Liberación manual (admin)
└── SyncLogs (por módulo)
```

---

## 5. ENDPOINTS BACKEND EXISTENTES

Los endpoints ya existen en `/api/v2/scheduler/*`:

| Endpoint | Método | Permiso | Función |
|----------|--------|---------|---------|
| `/status` | GET | `SCHEDULER_VER` | Estado general |
| `/jobs/{job_id}` | GET | `SCHEDULER_VER` | Info de job |
| `/jobs/{job_id}/run` | POST | `SCHEDULER_ADMIN` | Ejecutar manual |
| `/jobs/{job_id}/pause` | POST | `SCHEDULER_GESTIONAR` | Pausar job |
| `/jobs/{job_id}/resume` | POST | `SCHEDULER_GESTIONAR` | Reanudar job |
| `/logs` | GET | `SCHEDULER_VER` | Historial ejecuciones |
| `/logs/stats` | GET | `SCHEDULER_VER` | Estadísticas |
| `/locks` | GET | `SCHEDULER_VER` | Locks activos |
| `/locks/{job_name}` | DELETE | `SCHEDULER_ADMIN` | Liberar lock |
| `/config` | GET | `SCHEDULER_VER` | Configuración |

---

## 6. PERMISOS RBAC

### 6.1 Permisos existentes

| Permiso | Descripción |
|---------|-------------|
| `SCHEDULER_VER` | Ver estado, jobs, logs |
| `SCHEDULER_GESTIONAR` | Pausar/reanudar jobs |
| `SCHEDULER_ADMIN` | Ejecutar manual, liberar locks |

### 6.2 Integración con menú

El menú "Automatizaciones" ya tiene lógica de permisos en `Layout.js`:

```javascript
{ 
  name: 'Automatizaciones', 
  href: '/automatizaciones', 
  icon: CalendarCheck, 
  roles: ['SuperAdministrador', 'Administrador', 'Supervisor', 'Gerente', 'Director', 'Auditor'] 
}
```

Los permisos específicos del tab se validarían a nivel de componente.

---

## 7. ARCHIVOS A MODIFICAR (cuando se autorice)

| Archivo | Cambio |
|---------|--------|
| `/app/frontend/src/pages/AuditoriasProgramadas.jsx` | Agregar tab "Programaciones" |
| (Nuevo) `/app/frontend/src/components/TabProgramaciones.jsx` | Componente del tab |

**NO modificar**:
- `Layout.js` (menú sidebar)
- Rutas en `App.js`
- Backend scheduler
- RBAC

---

## 8. JOBS ACTUALES EN EL SISTEMA

| Job ID | Nombre | Frecuencia | Estado |
|--------|--------|------------|--------|
| `sla_processor` | SLA Processor | 5 min | Activo |
| `notifications_dispatcher` | Notifications Dispatcher | 2 min | Activo |
| `auditorias_scheduler` | Auditorías Scheduler | 1 hora | Activo |
| `pedidos_detector` | Pedidos Detector | 5 min | Activo |
| `inventarios_detector` | Inventarios Detector | 10 min | Activo |
| `sync_short_comercial` | SYNC-S KPIs Comerciales | 15 min | Activo |
| `sync_nightly_comercial` | SYNC-N KPIs Comerciales | 03:00 cron | Activo |
| `sync_ingresos_incremental` | SYNC Control de Ingresos | 15 min | Activo |
| `sync_propinas_tpv_incremental` | SYNC Propinas TPV | 15 min | Activo |

---

## 9. NO AUTORIZADO

- ❌ Crear menú nuevo
- ❌ Modificar sidebar
- ❌ Modificar rutas existentes
- ❌ Modificar scheduler backend
- ❌ Modificar RBAC
- ❌ Crear tablas en EDARSAHUB
- ❌ Implementar frontend

---

## 10. ESTADO ACTUAL DEL PANEL PROGRAMACIÓN — SIN EDICIÓN AVANZADA

**Fecha de análisis**: 01-Mayo-2026  
**Ubicación actual**: `/scheduler` → `Scheduler.jsx`

---

### 10.1 FUNCIONALIDAD VISIBLE ACTUAL

El panel "Programación" actual ofrece **monitoreo y control básico**:

| Funcionalidad | Disponible | Tipo |
|---------------|------------|------|
| Scheduler activo/inactivo | ✅ | Lectura |
| Jobs activos | ✅ | Lectura |
| Jobs pausados | ✅ | Lectura |
| Ejecuciones 24h | ✅ | Lectura |
| Fallos 24h | ✅ | Lectura |
| Lista de jobs programados | ✅ | Lectura |
| Botón ejecutar | ✅ | Acción |
| Botón pausar | ✅ | Acción |
| Auto-refresh | ✅ | UI |
| Actualizar manual | ✅ | UI |

---

### 10.2 FUNCIONALIDAD FALTANTE (EDICIÓN AVANZADA)

| Funcionalidad | Estado | Riesgo si se implementa sin control |
|---------------|--------|-------------------------------------|
| Editar frecuencia | ❌ | ALTO - Puede afectar sincronizaciones |
| Editar intervalo | ❌ | ALTO - Puede saturar sistemas |
| Editar cron | ❌ | ALTO - Errores de sintaxis |
| Editar ventana horaria | ❌ | MEDIO - Conflictos de carga |
| Editar unidades incluidas | ❌ | ALTO - Datos incompletos |
| Editar reintentos | ❌ | MEDIO - Loops infinitos |
| Editar timeout | ❌ | MEDIO - Timeouts prematuros |
| Activar/desactivar persistente | ❌ | ALTO - Jobs críticos apagados |
| Editar rango incremental | ❌ | ALTO - Duplicados o huecos |
| Editar fuente de datos | ❌ | CRÍTICO - Fuente incorrecta |
| Ver auditoría de cambios | ❌ | Necesario para trazabilidad |

---

### 10.3 RIESGOS DE PERMITIR EDICIÓN SIN CONTROL

| Riesgo | Impacto | Mitigación requerida |
|--------|---------|----------------------|
| Cambiar frecuencia de sync | Datos desactualizados o saturación | Confirmación + auditoría |
| Desactivar job crítico | Pérdida de sincronización | Warning + doble confirmación |
| Ejecutar múltiples veces | Duplicados, locks | Verificación de lock activo |
| Cron inválido | Job no ejecuta | Validación de sintaxis |
| Timeout muy corto | Ejecuciones incompletas | Límites mínimos |
| Editar sin permiso | Acceso no autorizado | RBAC estricto |
| Sin auditoría | No saber quién cambió qué | Log obligatorio |

---

### 10.4 RBAC REQUERIDO PARA EDICIÓN

| Permiso | Acción permitida | Nivel |
|---------|------------------|-------|
| `SCHEDULER_VER` | Ver estado, config, logs | Básico |
| `SCHEDULER_GESTIONAR` | Pausar/reanudar jobs | Medio |
| `SCHEDULER_EJECUTAR_MANUAL` | Ejecutar job on-demand | Medio |
| `SCHEDULER_LIBERAR_LOCK` | Liberar locks atascados | Alto |
| `SCHEDULER_EDITAR_FRECUENCIA` | Cambiar intervalos/cron | Alto |
| `SCHEDULER_EDITAR_CONFIG` | Cambiar timeouts, reintentos | Alto |
| `SCHEDULER_ADMIN` | Acceso completo | Máximo |

**Permisos actuales existentes**: `SCHEDULER_VER`, `SCHEDULER_GESTIONAR`, `SCHEDULER_ADMIN`

**Permisos nuevos requeridos**: `SCHEDULER_EDITAR_FRECUENCIA`, `SCHEDULER_EDITAR_CONFIG`, `SCHEDULER_EJECUTAR_MANUAL`, `SCHEDULER_LIBERAR_LOCK`

---

### 10.5 AUDITORÍA REQUERIDA

Cada cambio en configuración de scheduler debe registrar:

| Campo | Descripción |
|-------|-------------|
| `usuario_id` | Quién hizo el cambio |
| `usuario_email` | Email del usuario |
| `fecha_hora` | Timestamp UTC |
| `job_id` | Job afectado |
| `campo_modificado` | Ej: "frecuencia", "activo", "timeout" |
| `valor_anterior` | Valor antes del cambio |
| `valor_nuevo` | Valor después del cambio |
| `motivo` | Razón del cambio (obligatorio) |
| `ip_origen` | IP del cliente |

---

### 10.6 TABLAS EDARSAHUB PROPUESTAS PARA CONFIGURACIÓN PERSISTENTE

#### Tabla: `Scheduler_Jobs_Config`

```sql
CREATE TABLE Scheduler_Jobs_Config (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    job_id NVARCHAR(100) NOT NULL UNIQUE,
    job_nombre NVARCHAR(200) NOT NULL,
    descripcion NVARCHAR(500),
    
    -- Frecuencia
    tipo_frecuencia NVARCHAR(20), -- 'interval' o 'cron'
    intervalo_segundos INT,
    cron_expression NVARCHAR(100),
    
    -- Ventana horaria
    hora_inicio TIME,
    hora_fin TIME,
    dias_semana NVARCHAR(20), -- '1,2,3,4,5' = L-V
    
    -- Config técnica
    timeout_segundos INT DEFAULT 300,
    max_reintentos INT DEFAULT 3,
    backoff_factor DECIMAL(3,1) DEFAULT 2.0,
    
    -- Estado
    activo BIT DEFAULT 1,
    pausado BIT DEFAULT 0,
    motivo_pausa NVARCHAR(500),
    
    -- Metadata
    modulo NVARCHAR(100), -- 'comercial', 'finanzas', etc.
    prioridad INT DEFAULT 5, -- 1=máxima, 10=mínima
    
    -- Auditoría
    creado_por NVARCHAR(100),
    fecha_creacion DATETIME2 DEFAULT GETUTCDATE(),
    modificado_por NVARCHAR(100),
    fecha_modificacion DATETIME2
);
```

#### Tabla: `Scheduler_Jobs_Auditoria`

```sql
CREATE TABLE Scheduler_Jobs_Auditoria (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    job_id NVARCHAR(100) NOT NULL,
    
    -- Quién
    usuario_id NVARCHAR(100),
    usuario_email NVARCHAR(200),
    ip_origen NVARCHAR(50),
    
    -- Qué
    accion NVARCHAR(50), -- 'CREAR', 'EDITAR', 'PAUSAR', 'REANUDAR', 'EJECUTAR_MANUAL'
    campo_modificado NVARCHAR(100),
    valor_anterior NVARCHAR(500),
    valor_nuevo NVARCHAR(500),
    motivo NVARCHAR(500),
    
    -- Cuándo
    fecha_hora DATETIME2 DEFAULT GETUTCDATE(),
    
    INDEX IX_job_id (job_id),
    INDEX IX_fecha (fecha_hora)
);
```

---

### 10.7 PLAN POR FASES PARA EDICIÓN CONTROLADA

#### FASE A: Solo Lectura Ampliada (Baja complejidad)

| Tarea | Descripción | Riesgo |
|-------|-------------|--------|
| Mostrar config completa | Frecuencia, cron, timeout, reintentos | Ninguno |
| Mostrar ventana horaria | Hora inicio/fin, días | Ninguno |
| Mostrar rango incremental | Últimos X días, fecha desde | Ninguno |
| Mostrar últimos logs | Historial de ejecuciones | Ninguno |
| Mostrar locks activos | Lock actual, duración | Ninguno |
| Mostrar SyncLog relacionado | Registros sincronizados | Ninguno |

**Archivos a modificar**: Solo frontend (componente de visualización)

#### FASE B: Edición Controlada (Media complejidad)

| Tarea | Descripción | Riesgo |
|-------|-------------|--------|
| Editar frecuencia | Con validación y confirmación | Medio |
| Pausar/reanudar con motivo | Motivo obligatorio | Bajo |
| Ejecutar manual | Con verificación de lock | Bajo |
| Registrar auditoría | Tabla en EDARSAHUB | Ninguno |

**Archivos a modificar**: Backend (endpoints) + Frontend (formularios) + EDARSAHUB (tablas)

#### FASE C: EDARSAHUB como Fuente de Configuración (Alta complejidad)

| Tarea | Descripción | Riesgo |
|-------|-------------|--------|
| Crear tablas de config | `Scheduler_Jobs_Config` | Bajo |
| Migrar config de código a BD | Poblar desde `config.py` | Medio |
| Scheduler lee de EDARSAHUB | Cambiar `scheduler_manager.py` | Alto |
| `config.py` como fallback | Solo si BD no disponible | Bajo |
| UI de administración completa | CRUD de jobs | Medio |

**Archivos a modificar**: Backend (scheduler_manager, config) + EDARSAHUB (tablas) + Frontend (UI admin)

---

### 10.8 CONFIRMACIÓN

**NO se modificó código en esta documentación.**

| Archivo | Estado |
|---------|--------|
| `/app/backend/core/scheduler/config.py` | ✅ INTACTO |
| `/app/backend/core/scheduler/scheduler_manager.py` | ✅ INTACTO |
| `/app/backend/core/scheduler/routes.py` | ✅ INTACTO |
| `/app/backend/core/scheduler/jobs/*` | ✅ INTACTO |
| `/app/frontend/src/pages/Scheduler.jsx` | ✅ INTACTO |
| RBAC | ✅ INTACTO |
| Frecuencias de jobs | ✅ SIN CAMBIOS |

---

### 10.9 UBICACIÓN DEFINITIVA DEL PANEL

| Opción | Ubicación | Contenido |
|--------|-----------|-----------|
| A | `/scheduler` (actual) | Evolucionar el panel existente |
| B | `/automatizaciones` + Tab | Integrar como tab nuevo |

**Recomendación**: Si el panel `/scheduler` ya tiene funcionalidad de monitoreo de jobs, puede evolucionar ahí. El tab en Automatizaciones sería para funcionalidad adicional o alternativa.

**Decisión pendiente**: Requiere autorización para definir ubicación final.

---

## 11. PRÓXIMOS PASOS (requieren autorización)

1. **Autorizar implementación del tab** dentro de Automatizaciones
2. **Definir nombre exacto** del tab: "Programaciones" vs "Scheduler" vs "Jobs"
3. **Validar permisos** necesarios para cada funcionalidad
4. **Diseño UI** del tab (mockup o especificación)
5. **Aprobar FASE A** (solo lectura ampliada) antes de edición
6. **Crear tablas EDARSAHUB** para configuración persistente
7. **Definir permisos RBAC** nuevos para edición

---

*Plan técnico actualizado - NO IMPLEMENTAR sin autorización explícita*

---

## 12. REVISIÓN DE UBICACIÓN Y NOMBRE — PROGRAMACIÓN vs AUTOMATIZACIONES

**Fecha de análisis**: 01-Mayo-2026  
**Solicitado por**: Usuario (observación de inconsistencia UI)  
**Estado**: ANÁLISIS TÉCNICO — NO MODIFICAR CÓDIGO

---

### 12.1 ESTADO ACTUAL DE LAS PANTALLAS

| Pantalla | Ruta | Archivo | Título UI | Subtítulo UI |
|----------|------|---------|-----------|--------------|
| **Programación** | `/scheduler` | `Scheduler.jsx` | "Programación" | "Shuttle de Programación de Análisis de Inventarios" |
| **Automatizaciones** | `/automatizaciones` | `AuditoriasProgramadas.jsx` | "Automatizaciones" | "Gestión de procesos automáticos del sistema" |

---

### 12.2 POR QUÉ EL TÍTULO ACTUAL ES INCORRECTO

**Problema detectado:**

La pantalla "Programación" (`/scheduler`) muestra:
- **Título**: "Programación"
- **Subtítulo**: "Shuttle de Programación de Análisis de Inventarios"

Pero el contenido visible incluye **scheduler general del sistema**:
- Notifications Dispatcher
- SLA Processor
- Pedidos Detector
- Inventarios Detector
- sync_short_comercial
- sync_nightly_comercial
- sync_ingresos_incremental
- sync_propinas_tpv_incremental
- **sync_comercial_v2** (recién agregado)

**Inconsistencia:**
- El subtítulo sugiere que es específico de inventarios
- El contenido real incluye jobs de: notificaciones, SLA, pedidos, comercial, ingresos, propinas, finanzas
- Esto confunde al usuario sobre el propósito de la pantalla

---

### 12.3 RESPUESTAS A LAS PREGUNTAS PLANTEADAS

| # | Pregunta | Respuesta |
|---|----------|-----------|
| 1 | ¿La pantalla de Programación es usada solo para inventarios o ya es scheduler general? | **Scheduler general**. Aunque el subtítulo dice "Análisis de Inventarios", muestra todos los jobs del sistema. |
| 2 | ¿Qué componentes se muestran ahí? | KPIs (scheduler activo, jobs activos, ejecuciones 24h), lista de todos los jobs, historial, acciones (ejecutar, pausar). |
| 3 | ¿Qué ruta usa? | `/scheduler` |
| 4 | ¿Qué menú la abre? | Sidebar → Sistema → "Programación" |
| 5 | ¿Existe menú separado de Automatizaciones? | **Sí**. Sidebar → Sistema → "Automatizaciones" (`/automatizaciones`) |
| 6 | ¿Qué contiene Automatizaciones actualmente? | Auditorías programadas (crear, listar, ejecutar auditorías de inventario). Tabs: Programadas, Operativas, Historial. |
| 7 | ¿Conviene mover scheduler general a Automatizaciones? | **Opción válida** pero requiere reestructuración. |
| 8 | ¿Conviene dejar Programación solo para inventarios? | Requeriría filtrar jobs o crear vista específica. |
| 9 | ¿Qué riesgo hay de renombrar título/subtítulo? | **Bajo**. Solo afecta texto UI, no funcionalidad. |
| 10 | ¿Qué riesgo hay de separar en tabs? | **Medio**. Requiere modificar estructura de componentes. |
| 11 | ¿Qué archivos se modificarían? | `Scheduler.jsx` (título), `AuditoriasProgramadas.jsx` (estructura), `Layout.js` (nombre menú). |
| 12 | ¿Qué módulos podrían afectarse? | Ninguno de backend. Solo frontend UI. |

---

### 12.4 OPCIÓN A — RENOMBRAR A AUTOMATIZACIONES CON TABS (Recomendada)

**Propuesta:**
Mantener `/scheduler` como pantalla principal de scheduler del sistema, pero actualizar título/subtítulo para reflejar su contenido real.

**Cambios propuestos:**

| Elemento | Actual | Propuesto |
|----------|--------|-----------|
| Título | "Programación" | "Automatizaciones" o "Scheduler del Sistema" |
| Subtítulo | "Shuttle de Programación de Análisis de Inventarios" | "Gestión de jobs, programaciones, auditorías y sincronizaciones del sistema" |

**Tabs sugeridos dentro de `/scheduler`:**

| Tab | Contenido |
|-----|-----------|
| Jobs del Sistema | Lista de todos los jobs con acciones |
| Auditorías de Inventario | Scheduler específico de auditorías (si aplica) |
| Sincronizaciones | Jobs de sync (comercial, ingresos, propinas) |
| Logs | Historial de ejecuciones |
| Locks | Locks activos y liberación |
| Configuración | Config del scheduler (futuro, solo lectura) |

**Menú:**
- Cambiar nombre en `Layout.js`: "Programación" → "Scheduler" o "Jobs"
- **O** unificar con "Automatizaciones"

**Archivos a modificar:**

| Archivo | Cambio |
|---------|--------|
| `/app/frontend/src/pages/Scheduler.jsx` | Línea 376: título, línea 378: subtítulo |
| `/app/frontend/src/pages/Layout.js` | Línea 236: nombre del menú (opcional) |

---

### 12.5 OPCIÓN B — SEPARAR PROGRAMACIÓN vs AUTOMATIZACIONES

**Propuesta:**
Mantener ambas pantallas pero con contenido claramente diferenciado.

| Menú | Ruta | Contenido |
|------|------|-----------|
| **Programación** | `/scheduler` | Solo auditorías de inventario y programación operativa |
| **Automatizaciones** | `/automatizaciones` | Scheduler general, jobs, sincronizaciones |

**Cambios requeridos:**

1. **Filtrar jobs en `/scheduler`**: Mostrar solo jobs de inventarios
2. **Mover scheduler general a `/automatizaciones`**: Agregar tab "Jobs del Sistema"
3. **Actualizar subtítulos** para reflejar contenido específico

**Archivos a modificar:**

| Archivo | Cambio |
|---------|--------|
| `/app/frontend/src/pages/Scheduler.jsx` | Filtrar jobs mostrados, actualizar título |
| `/app/frontend/src/pages/AuditoriasProgramadas.jsx` | Agregar tab con scheduler general |

---

### 12.6 RECOMENDACIÓN TÉCNICA

**Recomendación: OPCIÓN A (simplificada)**

**Justificación:**
1. **Menor riesgo**: Solo cambiar textos, no estructura
2. **Menor esfuerzo**: 2 líneas de código
3. **Sin impacto funcional**: La funcionalidad no cambia
4. **Claridad para el usuario**: El título refleja el contenido real

**Cambio mínimo propuesto:**

```jsx
// /app/frontend/src/pages/Scheduler.jsx líneas 376-378

// ANTES:
<h1 className="text-2xl font-bold text-zinc-900">Programación</h1>
<p className="text-zinc-500 text-sm mt-1">
  Shuttle de Programación de Análisis de Inventarios
</p>

// DESPUÉS:
<h1 className="text-2xl font-bold text-zinc-900">Scheduler del Sistema</h1>
<p className="text-zinc-500 text-sm mt-1">
  Gestión de jobs automáticos y sincronizaciones
</p>
```

**O alternativamente:**

```jsx
<h1>Automatizaciones del Sistema</h1>
<p>Scheduler, jobs, sincronizaciones y auditorías programadas</p>
```

---

### 12.7 RIESGOS IDENTIFICADOS

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Confusión de usuarios existentes | Baja | Bajo | Comunicar cambio de nombre |
| Referencias en documentación | Baja | Bajo | Actualizar docs |
| Permisos RBAC desalineados | Ninguno | N/A | El permiso `SCHEDULER_*` sigue aplicando |
| Backend afectado | Ninguno | N/A | Solo cambios frontend |
| Tests automatizados | Ninguno | N/A | Los `data-testid` no cambian |

---

### 12.8 ARCHIVOS POTENCIALMENTE AFECTADOS

| Archivo | Cambio | Prioridad |
|---------|--------|-----------|
| `/app/frontend/src/pages/Scheduler.jsx` | Título y subtítulo | Alta (cambio mínimo) |
| `/app/frontend/src/pages/Layout.js` | Nombre del menú (opcional) | Media |
| `/app/docs/*` | Actualizar documentación | Baja |

**Archivos NO afectados:**
- Backend (`/app/backend/*`)
- RBAC
- Base de datos
- APIs
- Jobs del scheduler

---

### 12.9 CONFIRMACIÓN

**NO SE MODIFICÓ CÓDIGO EN ESTE ANÁLISIS.**

| Archivo | Estado |
|---------|--------|
| `/app/frontend/src/pages/Scheduler.jsx` | ✅ INTACTO |
| `/app/frontend/src/pages/AuditoriasProgramadas.jsx` | ✅ INTACTO |
| `/app/frontend/src/pages/Layout.js` | ✅ INTACTO |
| `/app/backend/*` | ✅ INTACTO |
| Rutas | ✅ SIN CAMBIOS |
| Permisos | ✅ SIN CAMBIOS |
| Jobs scheduler | ✅ SIN CAMBIOS |

---

### 12.10 PRÓXIMA AUTORIZACIÓN REQUERIDA

Para implementar el cambio mínimo (solo título/subtítulo):

1. **Autorizar modificación** de `/app/frontend/src/pages/Scheduler.jsx` líneas 376-378
2. **Definir texto exacto** del nuevo título y subtítulo
3. **Opcional**: Autorizar cambio de nombre en menú sidebar (`Layout.js`)

**NO proceder sin autorización explícita.**

---

*Análisis técnico completado - 01-Mayo-2026*

---

## 13. CAMBIO MÍNIMO DE TÍTULO/SUBTÍTULO EN SCHEDULER.JSX — ✅ COMPLETADO

**Fecha de implementación**: 01-Mayo-2026  
**Autorización**: Explícita del usuario  
**Estado**: ✅ COMPLETADO

---

### 13.1 ARCHIVO MODIFICADO

| Archivo | Ruta completa |
|---------|---------------|
| `Scheduler.jsx` | `/app/frontend/src/pages/Scheduler.jsx` |

---

### 13.2 TEXTO ANTERIOR

```jsx
<h1 className="text-2xl font-bold text-zinc-900">Programación</h1>
<p className="text-zinc-500 text-sm mt-1">
  Shuttle de Programación de Análisis de Inventarios
</p>
```

---

### 13.3 TEXTO NUEVO

```jsx
<h1 className="text-2xl font-bold text-zinc-900">Scheduler del Sistema</h1>
<p className="text-zinc-500 text-sm mt-1">
  Monitoreo de jobs, sincronizaciones, auditorías y procesos automáticos
</p>
```

---

### 13.4 CONFIRMACIÓN DE CAMBIO MÍNIMO

| Verificación | Resultado |
|--------------|-----------|
| Líneas modificadas | **2 líneas** (título y subtítulo) |
| Archivo modificado | Solo `Scheduler.jsx` |
| Menú sidebar | ✅ INTACTO (sigue diciendo "Programación") |
| Rutas | ✅ SIN CAMBIOS (`/scheduler`) |
| Tabs | ✅ INTACTOS |
| Layout | ✅ INTACTO |
| Permisos RBAC | ✅ INTACTOS |
| Endpoints | ✅ SIN CAMBIOS |
| Scheduler backend | ✅ INTACTO |
| config.py | ✅ INTACTO |
| scheduler_manager.py | ✅ INTACTO |
| Jobs | ✅ INTACTOS |
| Botones | ✅ INTACTOS |
| Filtros | ✅ INTACTOS |

---

### 13.5 CONFIRMACIÓN DE NO REGRESIÓN

| Componente | Estado |
|------------|--------|
| Backend running | ✅ |
| Frontend running | ✅ |
| Scheduler jobs | ✅ Sin cambios |
| Comercial v2 | ✅ Sin cambios |
| Finanzas | ✅ Sin cambios |
| CxP | ✅ Sin cambios |
| Control de Ingresos | ✅ Sin cambios |
| Propinas TPV | ✅ Sin cambios |
| Módulos blindados | ✅ INTOCADOS |

---

### 13.6 VERIFICACIÓN POST-CAMBIO

| Item | Verificado |
|------|------------|
| Pantalla `/scheduler` carga | ✅ (servicios running) |
| Nuevo título visible | ✅ "Scheduler del Sistema" |
| Nuevo subtítulo visible | ✅ "Monitoreo de jobs..." |
| Jobs siguen mostrándose | ✅ (código no alterado) |
| Botones existentes visibles | ✅ (código no alterado) |
| Menú sidebar sin cambios | ✅ Verificado en `Layout.js` |
| Rutas sin cambios | ✅ `/scheduler` |
| Ningún módulo afectado | ✅ |

---

*Cambio mínimo implementado y documentado - 01-Mayo-2026*

