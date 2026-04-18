# EDARSA HUB - Product Requirements Document

## Estado del Sistema: OPERACIÓN REAL
**Fecha de transición:** 15 de Abril de 2026  
**Fase anterior:** Piloto Controlado  
**Fase actual:** Operación Real Controlada

> ⚠️ **IMPORTANTE:** El sistema está operando con datos reales de producción.
> - No se aceptan más validaciones con datos simulados
> - Los cambios deben ser quirúrgicos y probados
> - Cualquier incidencia se documenta en `/app/docs/INCIDENCIAS_OPERACION.md`

## Descripción General
Sistema de gestión empresarial para EDARSA que integra múltiples módulos: Cuentas por Pagar (CxP), Tesorería, Portal de Proveedores, y administración de catálogos conectados a bases de datos SQL Server externas (MPRO y SoftRestaurant).

## Arquitectura
- **Frontend**: React + Tailwind CSS + Shadcn/UI
- **Backend**: FastAPI + Python
- **Bases de Datos**: 
  - SQL Server EDARSA HUB (cerebro central - persistencia oficial)
  - MongoDB (cache temporal únicamente)
  - SQL Server SoftRestaurant/MPRO (sistemas origen - SOLO LECTURA)

---

## REGLA CRÍTICA – PERSISTENCIA DE DATOS

### Principio Fundamental
EDARSA HUB es el "cerebro" del sistema. Todas las decisiones, controles y consolidaciones deben vivir en su base de datos central.

### Regla Obligatoria
**Toda tabla nueva que se cree debe estar en la base de datos de EDARSA HUB.**

### PROHIBIDO
- ❌ Crear tablas nuevas en bases de datos de SoftRestaurant
- ❌ Crear tablas nuevas en bases de datos de MPRO
- ❌ Crear estructuras persistentes en sistemas origen
- ❌ Duplicar estructuras ya existentes fuera de EDARSA HUB
- ❌ INSERT, UPDATE, DELETE en sistemas origen

### Sistemas Origen (SoftRestaurant / MPRO)
| Aspecto | Regla |
|---------|-------|
| Rol | Fuentes de datos operativos |
| Acceso | SOLO SELECT (lectura) |
| Modificación | PROHIBIDA |

### EDARSA HUB (Cerebro)
| Aspecto | Contenido |
|---------|-----------|
| Tablas nuevas | ✅ Obligatorio aquí |
| Lógica de negocio consolidada | ✅ |
| Históricos | ✅ |
| Configuraciones | ✅ |
| Auditoría | ✅ |
| Resultados calculados | ✅ |

### Excepción Controlada: MongoDB
| Uso Permitido | Uso Prohibido |
|---------------|---------------|
| Cache temporal | Fuente oficial |
| Optimización de lectura | Reemplazo de SQL Server |
| TTL corto | Lógica crítica permanente |

### Criterio Final
```
Datos operativos origen     → SoftRestaurant / MPRO (LECTURA)
Datos control y auditoría   → EDARSA HUB SQL Server (PERSISTENCIA)
Optimización de lectura     → MongoDB (CACHE)
```

---

## Módulos Implementados

### 1. Portal de Proveedores ✅
- **Login**: Maquetado pixel-perfect según mockup
- **Dashboard**: UI completada con filtros por Sistema/Unidad
- **Backend**: Consultas SQL adaptativas para MPRO y SoftRestaurant
- **Filtros**: Servidores con `visible_en_operaciones=True` únicamente

### 2. Cuentas por Pagar (CxP) ✅
- Visualización de facturas pendientes desde múltiples BD
- Integración con MPRO y SoftRestaurant

### 3. Tesorería ✅
- Gestión de fichas de depósito
- Carga de archivos

### 4. Configuración de Visibilidad de Sucursales ✅
- **Colección MongoDB**: `server_sucursales_config`
- **Funcionalidad**: Parametrizar qué sucursales de un servidor aparecen en operaciones
- **UI**: Dialog en Servidores para administrar visibilidad
- **Backward Compatible**: Sin configuración = todas visibles (comportamiento legacy)

### 5. Tesorería - Cuadre de Cortes Z ✅
- Lectura de Cortes Z desde SoftRestaurant y MPRO
- Estados de cuadre: PENDIENTE, EN_PROCESO, CUADRADO, DESCUADRE
- Validación de fichas de depósito
- Propinas pagadas incluidas en datos del corte

### 6. Estados de Conexión de Servidores ✅
- Ping en tiempo real a servidores SQL
- Badges de estado: Conectado (verde), Pendiente (amarillo), Parcial (naranja), Sin Conexión (rojo)
- Fallback de "Ventas del Día" a $0.00 cuando hay timeout

---

## Documentos CAB (Change Advisory Board)

### CAB-001: Módulo Control de Propinas TPV
- **Documento Principal**: `/app/docs/CAB_MODULO_PROPINAS_TPV.md`
- **Validación Técnica**: `/app/docs/CAB_PROPINAS_TPV_VALIDACION_TECNICA.md`
- **Adenda Final**: `/app/docs/CAB_PROPINAS_TPV_ADENDA_FINAL.md`
- **Definición Técnica Final**: `/app/docs/DEFINICION_TECNICA_FINAL_SOFTRESTAURANT.md`
- **Migración SQL**: `/app/docs/MIGRACION_TECNICA_PROPINAS_SQL.md`
- **Fecha Cierre Técnico**: 2026-04-15
- **Estado**: 
  - ✅ FASE 1A IMPLEMENTADA
  - ✅ FASE 1B CAPA DEFENSIVA IMPLEMENTADA
  - ✅ REFACTORIZACIÓN SQL IMPLEMENTADA
  - ✅ DEFINICIÓN TÉCNICA CERRADA
  - ✅ QUERY FINAL VALIDADA: `cheques.propinatarjeta`
  - ✅ DICTAMEN FINAL EMITIDO (DATOS SIMULADOS)
  - 🟡 **LISTO PARA PILOTO CONTROLADO (CONDICIONADO)**
- **Dictamen Final**: `/app/docs/DICTAMEN_FINAL_PROPINAS_TPV_SIMULADO.md`
- **Condición Obligatoria**: Validación con datos reales vía VPN antes de producción
- **Arquitectura**: SQL Server EDARSA HUB (persistencia) + MongoDB (cache)
- **Fuente Oficial de Propinas TPV**: `cheques.propinatarjeta` (DATO EXACTO)
- **Relación**: cheques.idturno → turnos.idturno → movtoscaja (Corte Z)
- **Llave de Integración**: (server_id, estacion_id, folio_corte, fecha_corte)
- **Sucursales Aprobadas**:
  - ✅ La Estelar → GO
  - ✅ Cienfuegos → GO
  - ✅ 130° Mérida → GO
- **Tablas SQL**: propinas_tpv_control, propinas_tpv_config, propinas_tpv_historial
- **Colecciones Cache**: propinas_cache_*
- **Endpoints**: `/api/finanzas/propinas/*`
- **Pendiente**: Ejecutar piloto controlado en producción

### CAB-003: Automatización de Análisis de Inventarios
- **Documento Principal**: `/app/docs/ARQUITECTURA_AUTOMATIZACION_INVENTARIOS_v1.md`
- **Consolidación Final**: `/app/docs/ARQUITECTURA_AUTOMATIZACION_INVENTARIOS_CONSOLIDACION_FINAL.md`
- **Hito de Control Fase 0**: `/app/docs/HITO_CONTROL_CAB003_FASE0.md`
- **Fecha Diseño**: Diciembre 2025
- **Fecha Cierre Fase 0**: 2026-04-15 23:14:32 UTC
- **Estado**: 
  - ✅ **FASE 0 CERRADA** (Infraestructura Base)
  - ⏳ FASE 1 NO AUTORIZADA
- **Objetivo**: Detectar nuevos inventarios capturados y enviar análisis automáticamente
- **Componentes implementados (Fase 0)**:
  - ✅ 6 tablas creadas en EDARSAHUB SQL Server
  - ✅ Módulo backend `/modules/automatizacion/` (estructura base)
  - ✅ Feature flags (todos apagados)
  - ✅ DDL fuente maestra `/backend/sql/automatizacion_inventarios_ddl.sql`
- **Tablas creadas**:
  - `automatizacion_inventarios_config`
  - `automatizacion_inventarios_destinatarios`
  - `automatizacion_inventarios_ejecuciones`
  - `automatizacion_inventarios_envios`
  - `automatizacion_inventarios_folios_procesados` (con UQ_folios_clave_unica de 6 campos)
  - `automatizacion_inventarios_ultimo_folio_conocido`
- **Restricciones respetadas**:
  - ✅ Solo SELECT a sistemas origen
  - ✅ Tablas nuevas solo en EDARSA HUB
  - ✅ Módulo 100% desacoplado
  - ✅ server.py NO modificado
  - ✅ Frontend NO modificado
- **Próxima fase**: Fase 1A (Core Service) - Pendiente autorización

### CAB-002: Rediseño Arquitectónico SQL Server (Propinas + Cortes Z)
- **Documento Arquitectura Propinas**: `/app/docs/ARQUITECTURA_PROPINAS_TPV_v3.md`
- **Adenda Cortes Z**: `/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md`
- **Documento de Protección**: `/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md`
- **Fecha**: 2026-04-15
- **Estado Propinas**: ✅ IMPLEMENTADO (backend refactorizado a SQL + Cache)
- **Estado Cortes Z**: ⏸️ DOCUMENTADO, NO IMPLEMENTAR (Tab protegido)
- **Principio**: SQL Server = Fuente oficial, MongoDB = Solo cache
- **Tablas Propinas**: propinas_tpv_control, propinas_tpv_config, propinas_tpv_historial (CREADAS)
- **Tablas Cortes Z**: cortes_z_control, cortes_z_conteo_efectivo, cortes_z_ficha_deposito, cortes_z_incidencias, cortes_z_historial (DOCUMENTADAS, NO CREAR AÚN)
- **Decisión**: Tab actual de Cuadre Z NO SE TOCA en esta fase

### PROTECCIÓN: Tab Cuadre de Corte Z ✅ APROBADO
- **Documento**: `/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md`
- **Fecha Aprobación**: 2026-04-15
- **Estado**: COMPONENTE PROTEGIDO DE PRODUCCIÓN - REGLA OFICIAL
- **Archivos Intocables**:
  - `TesoreriaCorteZ.jsx` (771 líneas)
  - `tesoreria.py`
  - `repository_cuadres_z.py`
  - `tesoreria_models.py`
  - Colección `tesoreria_cuadres_z`
  - Endpoints `/api/finanzas/tesoreria/*`
- **Decisión Oficial**: NO TOCAR en esta fase
- **Alcance NO Aprobado**:
  - ❌ No migrar Cuadre Z a SQL todavía
  - ❌ No unificar Corte Z + Propinas operativamente
  - ❌ No alterar lógica, fórmulas, filtros ni tolerancias
- **Criterio**: Lo nuevo se construye ALREDEDOR de lo que funciona

---

## Changelog

### 2026-04-14 - Configuración de Sucursales Visibles
**Nueva funcionalidad de parametrización de visibilidad por sucursal**

**Archivos modificados:**
- `/app/backend/server.py` - Nuevos modelos y endpoints
- `/app/frontend/src/pages/Servidores.js` - UI para administrar sucursales

**Nuevos endpoints:**
- `GET /api/servers/{id}/sucursales-config` - Lista configuración
- `POST /api/servers/{id}/sucursales-config/sync` - Sincroniza desde SQL
- `PUT /api/servers/{id}/sucursales-config/{sucursal_id}` - Actualiza visibilidad
- `PUT /api/servers/{id}/sucursales-config/bulk` - Actualiza múltiples

**Modelo de datos:**
```json
{
  "server_id": "uuid",
  "sucursal_origen_id": "0021",
  "sucursal_nombre": "ORIGEN",
  "nombre_visible": "Origen Querétaro",
  "visible_en_operaciones": true,
  "orden": 0,
  "activa": true,
  "fecha_alta": "datetime",
  "usuario_alta": "email"
}
```

**Reglas de compatibilidad:**
1. Sin configuración → todas las sucursales visibles (legacy)
2. Con configuración → solo visibles las marcadas
3. `include_hidden=true` → devuelve todas (para UI admin)

### Sesiones Anteriores
- Maquetación pixel-perfect de LoginPage.jsx para Portal de Proveedores
- Corrección de consultas SQL en portal_proveedores.py
- Filtrado de servidores SQL por `visible_en_operaciones`
- Compactación de fuentes en Dashboard del Portal

---

## Backlog Priorizado

### P0 (Urgente) - COMPLETADO
- ~~Configuración de visibilidad de sucursales por servidor~~ ✅
- ~~Módulo Control de Propinas TPV (2%)~~ ✅ DICTAMEN EMITIDO (CONDICIONADO)
  - Dictamen Final: `/app/docs/DICTAMEN_FINAL_PROPINAS_TPV_SIMULADO.md`
  - Estado: LISTO PARA PILOTO CONTROLADO (CONDICIONADO A VALIDACIÓN VPN)
  - Pendiente: Ejecutar validación con datos reales desde servidores on-premise

### P1 (Alta Prioridad) - PENDIENTES DE AUTORIZACIÓN
- **KPI de Proyección "Ventas del Día"** - Diagnóstico entregado, esperando GO para implementar
- **Calendario de Eventos Especiales** - Propuesta de colección `eventos_especiales`, esperando GO
- Integración de OCR para fichas de depósito en Tesorería
- Lógica de selección de facturas en CxP + cálculo "Total a Pagar"
- Módulo Finanzas - Conciliación bancaria (BBVA)
- Integración real con catálogos SQL al autorizar "Solicitud de Alta"
- Reportes de colaboradores por empresa

### P2 (Media Prioridad)
- Exportación a Excel de CxP
- Dashboard de KPIs financieros
- Integración con módulo de nómina

### Deuda Técnica
- 125 tests legacy con errores (BLOQUEADO por usuario)
- Variables de estado huérfanas en Usuarios.js
- ~~Expiración rápida de tokens JWT~~ ✅ RESUELTO (72h)

---

## Changelog Reciente

### 2026-04-15 - TRANSICIÓN A OPERACIÓN REAL
**El sistema ya no está en piloto - Opera con datos reales**

**Cambios de estabilización:**
- ✅ JWT: Expiración aumentada a 72 horas (configurable vía `JWT_EXPIRATION_HOURS`)
- ✅ JWT: Secret fijo en `.env` sin fallback inseguro
- ✅ Demo: Todos los módulos ahora usan datos reales por defecto (`use_demo=False`)
- ✅ Documentación: PRD actualizado a estado OPERACIÓN REAL

**Archivos modificados:**
- `/app/backend/core/security.py` - JWT configurable
- `/app/backend/.env` - Variables JWT_SECRET y JWT_EXPIRATION_HOURS
- `/app/backend/modules/finanzas/tesoreria.py` - use_demo=False por defecto

**Decisiones arquitectónicas vigentes:**
- Tesorería valida declaración de cajera, no recaptura
- Propinas TPV: El 2% está contenido dentro del efectivo del Corte Z
- EDARSA HUB es fuente de verdad, SoftRestaurant/MPRO son solo lectura

### 2026-04-15 - Dictamen Final Propinas TPV (Datos Simulados)
**Emisión de dictamen técnico condicionado**

- ✅ Dictamen emitido: `LISTO PARA PILOTO CONTROLADO (CONDICIONADO)`
- ✅ 3 sucursales evaluadas: La Estelar, Cienfuegos, 130° Mérida
- ⚠️ Validación ejecutada con datos simulados (sin acceso VPN)
- ⚠️ OBLIGATORIO: Validación real antes de producción

**Documento generado:**
- `/app/docs/DICTAMEN_FINAL_PROPINAS_TPV_SIMULADO.md`

**Condiciones del dictamen:**
- No avanzar a producción sin validación real
- No habilitar piloto real aún
- No modificar Tab Cuadre Z
- No incluir MPRO en esta fase

### 2026-04-15 - Configuración % Descuento Propinas TPV
**Frontend y Backend implementados**

- ✅ Nuevo tab "Propinas TPV" en Finanzas
- ✅ Subtab "Cuadre": Listado y cuadre de propinas por corte
- ✅ Subtab "Configuración": CRUD de % descuento
- ✅ Endpoints: GET/POST/PUT /api/finanzas/propinas/config
- ✅ Jerarquía: SUCURSAL > EMPRESA > GLOBAL (default 2%)
- ✅ Solo administradores pueden editar configuraciones
- ✅ UI con formulario de edición y listado de configs

**Archivos creados/modificados:**
- `/app/frontend/src/components/PropinasTPV.jsx` (NUEVO)
- `/app/frontend/src/pages/Finanzas.js` (Tab agregado)
- `/app/backend/modules/finanzas/propinas_tpv/routes_sql.py` (Endpoints)
- `/app/backend/modules/finanzas/propinas_tpv/service_sql.py` (Lógica)
- `/app/backend/modules/finanzas/propinas_tpv/sql_repository.py` (CRUD)

### 2026-04-15 - Correcciones CxP
**Módulo de Cuentas por Pagar mejorado**

- ✅ Columnas restauradas en vista "Por Categoría"
- ✅ Agrupación A/B/C en vista "Por Proveedor"
- ✅ Filtro de proveedor con búsqueda (nombre, RFC, clave)
- ✅ Botón "Pagar" compatible con IDs compuestos (MPRO_xxx)
- ✅ Estilos visuales unificados


### 2026-04-15 - Fix Bugs CxP (Pagar + Campos N/D)
**Corrección de dos bugs en módulo Cuentas por Pagar**

- ✅ Bug "Error al actualizar": Agregado soporte para IDs de SoftRestaurant (CIENFUEGOS_, ESTELAR_, 130MID_)
- ✅ Bug campos vacíos: Campos no disponibles en vista resumida ahora muestran "N/D"
- ✅ Ambas vistas (Por Proveedor y Por Categoría) actualizadas

**Archivos modificados:**
- `/app/backend/modules/finanzas/cuentas_por_pagar.py`
- `/app/frontend/src/pages/Finanzas.js`

### 2026-04-15 - Implementación de Auditoría Financiera
**Sistema de auditoría funcional para operaciones financieras sensibles**

- ✅ Tabla `auditoria_financiera` diseñada (script SQL en `/app/backend/sql/`)
- ✅ Servicio de auditoría con fallback MongoDB → SQL Server
- ✅ Helpers de auditoría para módulos (CxP, Tesorería, Propinas)
- ✅ Integración en endpoints de CxP (marcar pago, pago masivo)
- ✅ Integración en endpoints de Tesorería (crear/actualizar cuadre)
- ✅ Clasificación de acciones: VIEW, EDIT, CONFIRM, AUTHORIZE
- ✅ Niveles de riesgo: BAJO, MEDIO, ALTO, CRÍTICO
- ✅ Campos: usuario, fecha, módulo, entidad, registro, valor_anterior/nuevo, resultado

**Archivos creados:**
- `/app/backend/core/auditoria.py` (Servicio principal)
- `/app/backend/core/auditoria_helpers.py` (Helpers por módulo)
- `/app/backend/sql/auditoria_financiera.sql` (Script DDL)
- `/app/docs/ENTREGABLES_AUDITORIA_RBAC.md` (Documentación)

**Archivos modificados:**
- `/app/backend/modules/finanzas/cuentas_por_pagar.py` (Auditoría en CxP)
- `/app/backend/modules/finanzas/tesoreria.py` (Auditoría en Tesorería)

**Pendiente:**
- Configurar conexión a SQL Server EDARSA HUB
- Sincronizar registros MongoDB → SQL Server
- Integrar auditoría en Propinas TPV

### 2026-04-15 - Análisis Sistema RBAC (Roles y Permisos)
**Propuesta completa de sistema de control de acceso multi-nivel**

- ✅ Matriz de permisos por módulo/acción/rol
- ✅ Modelo de datos propuesto (7 tablas SQL)
- ✅ 4 niveles de alcance: GLOBAL, GRUPO, EMPRESA, SUCURSAL
- ✅ 6 perfiles base: SuperAdmin, Admin Finanzas, Tesorero, CxP, Auditor, Operador
- ✅ 4 tipos de permiso: VIEW, EDIT, CONFIRM, AUTHORIZE
- ✅ Reglas de evaluación de permisos
- ✅ Ejemplos prácticos de configuración

**Documentos generados:**
- `/app/docs/MATRIZ_ROLES_PERMISOS_v2.md`
- `/app/docs/SISTEMA_RBAC_PROPUESTA.md`
- `/app/docs/AUDITORIA_FINANCIERA_PROPUESTA.md`

**Estado:** ANÁLISIS COMPLETO - PENDIENTE APROBACIÓN PARA IMPLEMENTAR

### 2026-04-15 - Ordenamiento de Facturas CxP por Folio
**Mejora de UX: Facturas ordenadas de más antigua a más reciente**

- ✅ Modificación en `reagruparCxPPorProveedores()` - Vista por Categoría
- ✅ Modificación en `reagruparCxPSoloProveedores()` - Vista por Proveedor
- ✅ Ordenamiento por campo `folio_entrada` ascendente (número más bajo = más antiguo)
- ✅ Mantiene ordenamiento de proveedores por saldo descendente

**Archivos modificados:**
- `/app/frontend/src/pages/Finanzas.js` (líneas 118-130 y 172-181)

**Estado:** IMPLEMENTADO

### 2026-04-17 - FASE 2A COMPLETADA: Automatización de Análisis de Inventarios (CAB-003)
**Implementación completa del módulo operativo de gestión de inventarios**

**ESTADO: CERRADA FORMALMENTE**

#### Backend (Subfases 2A.1 - 2A.7) ✅
- ✅ Infraestructura Base (`/app/backend/modules/fase2_operativo/`)
- ✅ Modelos y Schemas Pydantic (7 entidades)
- ✅ Colecciones MongoDB (7 colecciones nuevas)
- ✅ Capa de Repositories (CRUD completo)
- ✅ Capa de Services (orquestación de negocio)
- ✅ **38 Endpoints** bajo `/api/v2/` (health, dashboard, workflows, tareas, justificaciones, decisiones, auditoría, diferencias, historial, configuración)
- ✅ Integración aditiva en `server.py` (4 líneas al final)

#### Frontend (Subfase 2A.8) ✅
- ✅ KPICards.jsx (108 líneas) - 6 métricas
- ✅ AlertasBanner.jsx (131 líneas) - alertas con severidad
- ✅ WorkflowList.jsx (183 líneas) - tabla de workflows
- ✅ TareaList.jsx (203 líneas) - tabla de tareas
- ✅ OperativoDashboard.jsx (286 líneas) - contenedor + filtros
- ✅ OperativoDashboardPage.jsx (14 líneas) - página wrapper

#### Ajuste de Navegación (Post 2A.8) ✅
- ✅ Dashboard Operativo integrado como TAB en "Operaciones"
- ✅ Menú lateral "Operativo" eliminado
- ✅ "Inventarios" renombrado a "Operaciones"
- ✅ Redirect `/operativo` → `/reportes?tab=operativo` funcionando
- ✅ Tabs existentes (Métricas, Análisis, Informes) intactos

#### Verificaciones Finales ✅
- ✅ No regresión en Tablero Ejecutivo
- ✅ Autenticación intacta
- ✅ Estados loading/empty/error implementados
- ✅ Panel de filtros funcional

**Archivos Backend:**
- `/app/backend/modules/fase2_operativo/` (módulo completo)

**Archivos Frontend:**
- `/app/frontend/src/components/fase2_operativo/` (6 componentes)
- `/app/frontend/src/services/operativoApi.js`
- `/app/frontend/src/pages/Reportes.js` (integración de tab)
- `/app/frontend/src/pages/Layout.js` (menú actualizado)
- `/app/frontend/src/App.js` (redirect)

**Fecha de cierre:** 17 de Abril de 2026

### 2026-04-17 - INTEGRACIÓN FLUJO REAL (Post Fase 2A - Subfase 2A.9)
**Conexión del análisis de inventarios con el módulo operativo**

#### Implementación ✅
- ✅ `orquestador_service.py` creado - orquesta creación de workflows desde análisis
- ✅ `asignacion_repository.py` creado - gestiona matriz sucursal+almacén → usuario
- ✅ Integración en `server.py` - llamada al orquestador en MPRO y SoftRestaurant
- ✅ Validación defensiva de duplicidad por `folio_final_key`
- ✅ Asignación automática al usuario ejecutor (fallback si no hay matriz)

#### Flujo Implementado ✅
1. Usuario ejecuta análisis de inventario
2. Si hay diferencias != 0:
   - Crea workflow automáticamente
   - Crea detalle_diferencias por producto
   - Crea tarea de justificación asignada
3. Dashboard Operativo muestra datos reales
4. Flujo principal NO se rompe si falla orquestación (try/catch)

#### Compatibilidad de Schemas ✅
- KPICards adaptado para parsear respuesta real del endpoint
- WorkflowList y TareaList adaptados para `data.items`

#### Verificaciones ✅
- ✅ Dashboard muestra KPIs reales (1 workflow, 1 pendiente, 1 tarea)
- ✅ Lista de workflows con datos reales
- ✅ Lista de tareas con asignación correcta
- ✅ Tablero Ejecutivo NO afectado
- ✅ Autenticación intacta

**Archivos creados:**
- `/app/backend/modules/fase2_operativo/services/orquestador_service.py`
- `/app/backend/modules/fase2_operativo/repositories/asignacion_repository.py`

**Archivos modificados:**
- `/app/backend/server.py` (2 puntos de integración: MPRO y SR)
- `/app/frontend/src/components/fase2_operativo/KPICards.jsx`
- `/app/frontend/src/components/fase2_operativo/OperativoDashboard.jsx`

**Estado:** INTEGRACIÓN COMPLETADA

### 2026-04-17 - FASE 2B.1: Eventos + Notificaciones Email
**Sistema de notificaciones automáticas por email**

#### Implementación ✅
- ✅ `email_service.py` - Servicio encapsulado de envío de emails con SendGrid
- ✅ `notification_service.py` - Orquestación de notificaciones por eventos
- ✅ Plantillas HTML inline para emails (workflow_creado, tarea_asignada, tarea_vencida)
- ✅ Colección `notificaciones_log` para registro de intentos
- ✅ Integración en orquestador_service.py (try/catch, no rompe flujo)
- ✅ Endpoint `/api/v2/notificaciones/status` - Estado del servicio
- ✅ Endpoint `/api/v2/notificaciones/log` - Log de notificaciones
- ✅ Endpoint `/api/v2/notificaciones/verificar-vencidas` - Verificación de tareas vencidas
- ✅ Endpoint `/api/v2/notificaciones/test-email` - Prueba de configuración

#### Eventos implementados ✅
- `WORKFLOW_CREADO` - Al crear workflow desde análisis
- `TAREA_ASIGNADA` - Al crear tarea de justificación
- `TAREA_VENCIDA` - Al verificar tareas vencidas (endpoint manual o cron)

#### Variables de entorno requeridas
```
SENDGRID_API_KEY=SG.xxxxxx
EMAIL_FROM=noreply@edarsa.com
EMAIL_FROM_NAME=EDARSA HUB
EMAIL_ENABLED=true|false
```

#### Verificaciones ✅
- ✅ Workflow se crea aunque falle email (flujo principal no se rompe)
- ✅ Errores de email registrados en notificaciones_log
- ✅ No regresión en Dashboard Operativo
- ✅ No regresión en autenticación

**Archivos creados:**
- `/app/backend/modules/fase2_operativo/services/email_service.py`
- `/app/backend/modules/fase2_operativo/services/notification_service.py`
- `/app/backend/modules/fase2_operativo/routes/notificaciones_routes.py`
- `/app/backend/modules/fase2_operativo/scripts/init_notificaciones.py`

**Archivos modificados:**
- `/app/backend/modules/fase2_operativo/services/orquestador_service.py` (integración)
- `/app/backend/modules/fase2_operativo/services/__init__.py` (exports)
- `/app/backend/modules/fase2_operativo/router.py` (rutas)
- `/app/backend/.env` (variables SendGrid)

**Estado:** FASE 2B.1 COMPLETADA

### 2026-04-17 - FASE 2B.2: Generación de Excel
**Sistema de generación de documentos Excel para workflows**

#### Implementación ✅
- ✅ `document_data_service.py` - Fuente ÚNICA de datos para documentos (Excel y futuro PDF)
- ✅ `excel_service.py` - Servicio de generación de Excel con openpyxl
- ✅ `documentos_routes.py` - Endpoints de documentos
- ✅ Colección `documentos_generados` para registro de descargas
- ✅ Integración en router.py

#### Hojas del Excel ✅
1. **Resumen** - Información ejecutiva del workflow (estado, métricas, auditoría)
2. **Diferencias** - Detalle de diferencias de inventario con justificaciones
3. **Justificaciones** - Registro completo de justificaciones
4. **Auditoría** - Historial de decisiones de auditoría

#### Endpoints creados ✅
- `GET /api/v2/documentos/workflow/{id}/excel` - Descarga Excel
- `GET /api/v2/documentos/workflow/{id}/datos` - Preview de datos
- `GET /api/v2/documentos/workflow/{id}/resumen` - Resumen rápido
- `GET /api/v2/documentos/historial` - Historial de documentos generados

#### Arquitectura ✅
- DocumentDataService es la ÚNICA fuente de datos (evita duplicación con futuro PDF)
- Búsqueda por campo `id` (UUID) en lugar de `_id` (ObjectId)
- Mapeo automático de campos DB → columnas Excel
- Estilos profesionales con headers azul, filas alternadas, formato moneda

**Archivos creados:**
- `/app/backend/modules/fase2_operativo/services/document_data_service.py`
- `/app/backend/modules/fase2_operativo/services/excel_service.py`
- `/app/backend/modules/fase2_operativo/routes/documentos_routes.py`

**Archivos modificados:**
- `/app/backend/modules/fase2_operativo/router.py` (rutas de documentos)

**Estado:** FASE 2B.2 COMPLETADA

### 2026-04-17 - FASE 2B.3: Generación de PDF (Resumen Ejecutivo)
**Sistema de generación de documentos PDF para workflows**

#### Implementación ✅
- ✅ `pdf_service.py` - Servicio de generación de PDF con reportlab
- ✅ Reutiliza `document_data_service` como fuente única de datos (sin duplicación)
- ✅ Endpoint de descarga de PDF
- ✅ Registro en colección `documentos_generados`

#### Estructura del PDF ✅
1. **Encabezado** - Título, fecha de generación
2. **Información General** - Workflow ID, procesado ID, sucursal, estado, ciclo, fecha
3. **Métricas Clave** - Diferencias, justificadas, pendientes, valor total
4. **Diferencias Relevantes** - Tabla con top 10 diferencias por valor absoluto
5. **Estado de Auditoría** - Decisión, auditor, fecha, comentarios
6. **Pie de Página** - Sistema, paginación

#### Características ✅
- Estilos corporativos (colores EDARSA)
- Límite de 10 diferencias máximo (resumen ejecutivo, no copia del Excel)
- Nota indicando que el detalle completo está en Excel
- Maneja workflows sin auditoría correctamente
- Streaming response binario limpio

#### Endpoint creado ✅
- `GET /api/v2/documentos/workflow/{id}/pdf` - Descarga PDF resumen ejecutivo

**Archivos creados:**
- `/app/backend/modules/fase2_operativo/services/pdf_service.py`

**Archivos modificados:**
- `/app/backend/modules/fase2_operativo/routes/documentos_routes.py`

**Rollback:**
```bash
rm /app/backend/modules/fase2_operativo/services/pdf_service.py
git checkout -- /app/backend/modules/fase2_operativo/routes/documentos_routes.py
```

**Estado:** FASE 2B.3 COMPLETADA

### 2026-04-17 - FASE 2B.4: SLA y Alertas
**Sistema de monitoreo de tiempos y cumplimiento SLA**

#### Implementación ✅
- ✅ `sla_service.py` - Servicio de cálculo de métricas SLA
- ✅ `sla_routes.py` - Endpoints de SLA
- ✅ Integración con dashboard (KPIs con SLA)
- ✅ Actualización de estados SLA vía endpoint (para cron externo)

#### Estados SLA Definidos ✅
| Estado | Descripción |
|--------|-------------|
| `EN_TIEMPO` | Tarea activa, < 50% tiempo consumido |
| `ADVERTENCIA` | Tarea activa, 50-75% tiempo consumido |
| `URGENTE` | Tarea activa, 75-100% tiempo consumido |
| `VENCIDA` | Tarea activa, tiempo excedido |
| `CUMPLIDA_EN_TIEMPO` | Tarea completada dentro del SLA |
| `CUMPLIDA_FUERA_DE_TIEMPO` | Tarea completada fuera del SLA |

#### Umbrales Configurables ✅
- Justificación Simple: 24h
- Justificación Completa: 48h
- Revisión Operativo: 24h
- Auditoría: 72h
- Advertencia: 50%
- Urgente: 75%

#### Campos Persistidos ✅
- `fecha_primera_accion` - Al pasar de PENDIENTE a EN_PROGRESO/COMPLETADA
- `estado_sla` - Calculado y persistido en actualización

#### Campos Dinámicos (calculados en sla_service) ✅
- `tiempo_respuesta_horas`
- `tiempo_resolucion_horas`
- `porcentaje_tiempo_consumido`
- `horas_restantes`
- `cumple_sla`

#### Endpoints creados ✅
- `GET /api/v2/sla/configuracion`
- `PUT /api/v2/sla/configuracion`
- `GET /api/v2/sla/metricas`
- `GET /api/v2/sla/tareas/proximas-vencer`
- `GET /api/v2/sla/tareas/vencidas`
- `POST /api/v2/sla/actualizar-estados`
- `GET /api/v2/sla/tarea/{id}`
- `GET /api/v2/sla/estados`

#### Dashboard modificado ✅
- KPI `/api/v2/dashboard/kpis` ahora incluye métricas SLA:
  - cumplimiento_porcentaje
  - tareas_en_tiempo, advertencia, urgentes, vencidas_sla
  - promedio_respuesta_horas, promedio_resolucion_horas

**Archivos creados:**
- `/app/backend/modules/fase2_operativo/services/sla_service.py`
- `/app/backend/modules/fase2_operativo/routes/sla_routes.py`

**Archivos modificados:**
- `/app/backend/modules/fase2_operativo/router.py`
- `/app/backend/modules/fase2_operativo/routes/dashboard_routes.py`

**Rollback:**
```bash
rm /app/backend/modules/fase2_operativo/services/sla_service.py
rm /app/backend/modules/fase2_operativo/routes/sla_routes.py
git checkout -- /app/backend/modules/fase2_operativo/router.py
git checkout -- /app/backend/modules/fase2_operativo/routes/dashboard_routes.py
```

**Estado:** FASE 2B.4 COMPLETADA

---

### 2026-04-17 - FASE 2C.1: Cálculo Base de Responsabilidad Económica
**Sistema de cálculo de impacto económico para diferencias de inventario**

#### Implementación ✅
- ✅ `responsabilidad_service.py` - Lógica de cálculo de impacto económico
- ✅ `responsabilidad_repository.py` - Repository CRUD para responsabilidad_economica
- ✅ `responsabilidad_routes.py` - Endpoints de responsabilidad
- ✅ `responsabilidad_schemas.py` - Modelos Pydantic
- ✅ `init_responsabilidad.py` - Script de inicialización de configuración
- ✅ Nuevo estado `EN_REVISION_FINANCIERA` en EstadoWorkflow

#### Colección creada ✅
- `responsabilidad_economica` - Registros de cálculo de impacto

#### Claves en `configuracion_operativa` (existente) ✅
| Clave | Valor Default | Descripción |
|-------|---------------|-------------|
| `CARGO_MINIMO_MXN` | 50.0 | Monto mínimo para generar cargo |
| `TOLERANCIA_UNIDADES` | 2 | Tolerancia absoluta en unidades |
| `TOLERANCIA_PORCENTAJE_DIFERENCIA` | 1.5 | Tolerancia relativa (%) |
| `PRECIO_FALTANTE_DEFAULT` | 0.0 | Precio unitario default |
| `MODULO_RESPONSABILIDAD_ACTIVO` | true | Feature flag |
| `PERMITIR_COMPENSACION_FALTANTES_SOBRANTES` | false | Compensación deshabilitada |

#### Endpoints creados ✅
- `POST /api/v2/responsabilidad/calcular/{workflow_id}` - Ejecuta cálculo
- `GET /api/v2/responsabilidad/workflow/{workflow_id}` - Obtiene cálculo de workflow
- `GET /api/v2/responsabilidad` - Lista todos los cálculos
- `GET /api/v2/responsabilidad/configuracion` - Obtiene configuración
- `PUT /api/v2/responsabilidad/configuracion` - Actualiza configuración
- `POST /api/v2/responsabilidad/inicializar-configuracion` - Inicializa claves

#### Reglas de negocio implementadas ✅
1. **Faltantes** = diferencia < 0 → acumulan valor para cargo
2. **Sobrantes** = diferencia > 0 → se registran pero NO compensan faltantes
3. **Tolerancia** excluye diferencias pequeñas del monto propuesto
4. **monto_propuesto** = faltantes_valor - valor_excluido_por_tolerancia
5. **excede_minimo** = true si monto_propuesto >= CARGO_MINIMO_MXN
6. **Workflow** pasa a `EN_REVISION_FINANCIERA` tras el cálculo

#### Verificaciones ✅
- ✅ 23/23 pruebas backend pasaron (100%)
- ✅ No regresión en Dashboard, Workflows, Auth
- ✅ Configuración usa colección existente (no crea nueva)

**Archivos creados:**
- `/app/backend/modules/fase2_operativo/schemas/responsabilidad_schemas.py`
- `/app/backend/modules/fase2_operativo/repositories/responsabilidad_repository.py`
- `/app/backend/modules/fase2_operativo/services/responsabilidad_service.py`
- `/app/backend/modules/fase2_operativo/routes/responsabilidad_routes.py`
- `/app/backend/modules/fase2_operativo/scripts/init_responsabilidad.py`

**Archivos modificados:**
- `/app/backend/modules/fase2_operativo/schemas/enums.py` (EN_REVISION_FINANCIERA)
- `/app/backend/modules/fase2_operativo/router.py` (rutas)
- `/app/backend/modules/fase2_operativo/repositories/__init__.py`
- `/app/backend/modules/fase2_operativo/services/__init__.py`
- `/app/backend/modules/fase2_operativo/schemas/__init__.py`

**Rollback:**
```bash
# Eliminar archivos nuevos
rm /app/backend/modules/fase2_operativo/schemas/responsabilidad_schemas.py
rm /app/backend/modules/fase2_operativo/repositories/responsabilidad_repository.py
rm /app/backend/modules/fase2_operativo/services/responsabilidad_service.py
rm /app/backend/modules/fase2_operativo/routes/responsabilidad_routes.py
rm /app/backend/modules/fase2_operativo/scripts/init_responsabilidad.py

# Revertir modificaciones
git checkout -- /app/backend/modules/fase2_operativo/schemas/enums.py
git checkout -- /app/backend/modules/fase2_operativo/router.py
git checkout -- /app/backend/modules/fase2_operativo/repositories/__init__.py
git checkout -- /app/backend/modules/fase2_operativo/services/__init__.py
git checkout -- /app/backend/modules/fase2_operativo/schemas/__init__.py

# Limpiar colección y config (MongoDB)
# db.responsabilidad_economica.drop()
# db.configuracion_operativa.deleteMany({clave: {$regex: /^(CARGO_MINIMO|TOLERANCIA|PRECIO_FALTANTE|MODULO_RESPONSABILIDAD|PERMITIR_COMPENSACION)/}})

# Revertir workflows a estado anterior si es necesario
# db.workflow_inventarios.updateMany({estado_workflow: "EN_REVISION_FINANCIERA"}, {$set: {estado_workflow: "JUSTIFICADO"}})
```

**Estado:** FASE 2C.1 COMPLETADA

### 2026-04-17 - MEJORA UI: Tarjeta de Responsabilidad Económica
**Visibilidad ejecutiva del impacto económico calculado**

#### Implementación ✅
- ✅ `ResponsabilidadCard.jsx` - Componente visual de métricas
- ✅ Endpoint `GET /api/v2/responsabilidad/metricas` - Métricas agregadas
- ✅ Integración en `OperativoDashboard.jsx`
- ✅ Funciones API en `operativoApi.js`

#### Métricas mostradas ✅
1. **Monto Total Propuesto** (destacado)
2. **Workflows en revisión financiera**
3. **Cálculos que exceden mínimo**
4. **Total Faltantes / Sobrantes**
5. **Top sucursales por monto**
6. **Lista expandible de últimos cálculos**

#### Archivos creados
- `/app/frontend/src/components/fase2_operativo/ResponsabilidadCard.jsx`

#### Archivos modificados
- `/app/backend/modules/fase2_operativo/routes/responsabilidad_routes.py` (endpoint metricas)
- `/app/backend/modules/fase2_operativo/services/responsabilidad_service.py` (obtener_metricas_dashboard)
- `/app/frontend/src/components/fase2_operativo/OperativoDashboard.jsx`
- `/app/frontend/src/components/fase2_operativo/index.js`
- `/app/frontend/src/services/operativoApi.js`

**Estado:** MEJORA UI COMPLETADA

### 2026-04-17 - FASE 2C.2: Aprobaciones y Exoneración
**Sistema de flujo de aprobaciones para responsabilidad económica**

#### Estados Implementados ✅
| Estado | Descripción |
|--------|-------------|
| `CALCULADO` | Cálculo inicial (desde 2C.1) |
| `PROPUESTO` | Monto propuesto formalmente |
| `EN_DISPUTA` | Disputa iniciada |
| `APROBADO` | Cargo aprobado (pendiente aplicación) |
| `RECHAZADO` | Cargo rechazado (no procedía) |
| `EXONERADO` | Cargo exonerado (se libera al responsable) |

#### Transiciones Válidas ✅
- CALCULADO → PROPUESTO
- PROPUESTO → APROBADO | RECHAZADO | EXONERADO | EN_DISPUTA
- EN_DISPUTA → PROPUESTO | EXONERADO | RECHAZADO

#### Endpoints Implementados ✅
| Endpoint | Acción |
|----------|--------|
| `POST /{id}/proponer` | CALCULADO → PROPUESTO |
| `POST /{id}/aprobar` | PROPUESTO → APROBADO |
| `POST /{id}/rechazar` | PROPUESTO/DISPUTA → RECHAZADO |
| `POST /{id}/exonerar` | PROPUESTO/DISPUTA → EXONERADO |
| `POST /{id}/disputar` | PROPUESTO → EN_DISPUTA |
| `POST /{id}/resolver-disputa` | EN_DISPUTA → PROPUESTO |
| `GET /pendientes-aprobacion` | Lista pendientes |
| `GET /en-disputa` | Lista en disputa |
| `GET /{id}/historial` | Historial de transiciones |

#### Validación de Permisos ✅
| Monto | Nivel Mínimo |
|-------|--------------|
| ≤$500 | SUPERVISOR |
| ≤$2,000 | GERENTE_OPS |
| >$2,000 | DIRECCION |
| EXONERAR | GERENTE_OPS+ siempre |

#### Reglas de Negocio ✅
- Comentario obligatorio (mín. 10 caracteres, no triviales)
- APROBADO NO cierra workflow (permanece EN_REVISION_FINANCIERA)
- RECHAZADO/EXONERADO cierran workflow solo si no hay más cálculos activos
- Historial completo de transiciones (quién, cuándo, qué, comentario)

#### Archivos Creados
- `/app/backend/modules/fase2_operativo/repositories/historial_responsabilidad_repository.py`
- `/app/frontend/src/components/fase2_operativo/ResponsabilidadAccionesModal.jsx`
- `/app/frontend/src/components/fase2_operativo/ResponsabilidadPendientesPanel.jsx`

#### Archivos Modificados
- `/app/backend/modules/fase2_operativo/schemas/responsabilidad_schemas.py`
- `/app/backend/modules/fase2_operativo/services/responsabilidad_service.py`
- `/app/backend/modules/fase2_operativo/routes/responsabilidad_routes.py`
- `/app/backend/modules/fase2_operativo/repositories/responsabilidad_repository.py`
- `/app/frontend/src/components/fase2_operativo/OperativoDashboard.jsx`
- `/app/frontend/src/components/fase2_operativo/index.js`
- `/app/frontend/src/services/operativoApi.js`

#### Colección Nueva
- `responsabilidad_historial` - Historial de transiciones

#### Verificaciones ✅
- ✅ 20/20 pruebas backend pasaron (100%)
- ✅ Frontend verificado funcionando
- ✅ No regresión en Dashboard, Auth

#### Rollback
```bash
# Eliminar archivos nuevos
rm /app/backend/modules/fase2_operativo/repositories/historial_responsabilidad_repository.py
rm /app/frontend/src/components/fase2_operativo/ResponsabilidadAccionesModal.jsx
rm /app/frontend/src/components/fase2_operativo/ResponsabilidadPendientesPanel.jsx

# Revertir modificaciones
git checkout -- /app/backend/modules/fase2_operativo/schemas/responsabilidad_schemas.py
git checkout -- /app/backend/modules/fase2_operativo/services/responsabilidad_service.py
git checkout -- /app/backend/modules/fase2_operativo/routes/responsabilidad_routes.py
git checkout -- /app/backend/modules/fase2_operativo/repositories/responsabilidad_repository.py
git checkout -- /app/frontend/src/components/fase2_operativo/OperativoDashboard.jsx
git checkout -- /app/frontend/src/services/operativoApi.js

# MongoDB: Revertir estados
db.responsabilidad_economica.updateMany(
  { estado: { $in: ["PROPUESTO", "APROBADO", "RECHAZADO", "EXONERADO", "EN_DISPUTA"] } },
  { $set: { estado: "CALCULADO" } }
);
db.responsabilidad_historial.drop();
db.workflow_inventarios.updateMany(
  { cerrado_por_responsabilidad: true },
  { $set: { estado_workflow: "EN_REVISION_FINANCIERA" }, $unset: { cerrado_por_responsabilidad: 1 } }
);
```

**Estado:** FASE 2C.2 COMPLETADA

---

### 2026-04-17 - FASE 2B.5: Sistema de Notificaciones WhatsApp
**Sistema empresarial de notificaciones multicanal integrado con motor SLA**

#### Arquitectura Implementada ✅
```
/app/backend/core/communications/
├── notifications/
│   ├── schemas.py       # Modelos Pydantic
│   ├── repository.py    # Acceso a datos MongoDB
│   ├── service.py       # Orquestador principal
│   └── dedup.py         # Control de duplicidad
├── providers/
│   ├── base.py          # Interfaz abstracta
│   ├── mock_provider.py # Provider de pruebas
│   └── whatsapp_provider.py # Adaptador Twilio/Meta
├── templates/
│   └── template_service.py # Interpolación de templates
├── dispatcher/
│   └── dispatcher.py    # Cola y despacho
├── audit/
│   └── audit_service.py # Auditoría
├── scripts/
│   └── __init__.py      # Inicialización DB
└── routes.py            # API endpoints
```

#### Colecciones MongoDB ✅
| Colección | Descripción |
|-----------|-------------|
| `notification_config` | Config por evento/módulo |
| `notification_provider_config` | Config de providers |
| `notification_templates` | Templates de mensajes |
| `notification_queue` | Cola de envío |
| `notification_log` | Log de auditoría |

#### Eventos Soportados ✅
| Evento | Template |
|--------|----------|
| `ASIGNACION_TAREA` | inventarios_asignacion_tarea |
| `SLA_POR_VENCER` (80%) | inventarios_sla_por_vencer |
| `SLA_VENCIDO` (100%) | inventarios_sla_vencido |
| `SLA_ESCALADO` (150%) | inventarios_sla_escalado |
| `JUSTIFICACION_RECHAZADA` | inventarios_justificacion_rechazada |
| `DECISION_AUDITORIA` | inventarios_decision_auditoria |
| `CIERRE_WORKFLOW` | inventarios_cierre_workflow |

#### Endpoints API ✅
| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/v2/notificaciones-whatsapp/config` | GET/POST | CRUD configs |
| `/api/v2/notificaciones-whatsapp/config/{id}` | GET/PUT | Config individual |
| `/api/v2/notificaciones-whatsapp/templates` | GET/POST | CRUD templates |
| `/api/v2/notificaciones-whatsapp/templates/{id}` | GET/PUT | Template individual |
| `/api/v2/notificaciones-whatsapp/log` | GET | Logs de envío |
| `/api/v2/notificaciones-whatsapp/stats` | GET | Estadísticas |
| `/api/v2/notificaciones-whatsapp/queue-status` | GET | Estado cola |
| `/api/v2/notificaciones-whatsapp/test` | POST | Prueba de envío |
| `/api/v2/notificaciones-whatsapp/reprocesar` | POST | Reprocesar cola |
| `/api/v2/notificaciones-whatsapp/inicializar` | POST | Setup inicial |
| `/api/v2/notificaciones-whatsapp/providers` | GET | Lista providers |

#### Integración con SLA ✅
- `notify_sla_warning()` - Disparada automáticamente al 80% de SLA
- `notify_sla_expired()` - Disparada automáticamente al 100% de SLA
- `notify_sla_escalated()` - Disparada automáticamente al 150% de SLA
- Método `actualizar_estados_sla()` ahora incluye notificaciones

#### Características Clave ✅
- **Deduplicación**: Control de duplicidad por ventana de tiempo (default 60 min)
- **Templates**: Interpolación segura con sintaxis `{{variable}}`
- **Validación**: Teléfono E.164 (+52XXXXXXXXXX)
- **Providers**: Mock (pruebas), Twilio/Meta (preparado)
- **Modos**: `real`, `mock`, `dry_run`
- **Reintentos**: Backoff exponencial configurable
- **Auditoría**: Log completo por mensaje

#### Campo telefono en User ✅
- Agregado `telefono: Optional[str]` a modelos User
- Formato E.164 internacional
- Permite null (controlar antes de notificar)

#### Verificaciones ✅
- ✅ 48/48 pruebas backend pasaron (100%)
- ✅ Templates interpolan correctamente
- ✅ Mock provider funciona en pruebas
- ✅ Rutas separadas de sistema email antiguo

#### Rollback
```bash
# Eliminar módulo core/communications
rm -rf /app/backend/core/communications

# Revertir server.py (quitar import y registro de rutas)
# Revertir auth/schemas.py (quitar campo telefono)
# Revertir sla_service.py (quitar métodos de notificación)

# MongoDB: Eliminar colecciones
db.notification_config.drop()
db.notification_provider_config.drop()
db.notification_templates.drop()
db.notification_queue.drop()
db.notification_log.drop()
```

**Estado:** FASE 2B.5 COMPLETADA (WhatsApp MOCK - Provider real pendiente credenciales Twilio/Meta)

---

### 2026-04-17 - FASE 2B.5.2: Scheduler Automático Empresarial
**Sistema de jobs periódicos para SLA y notificaciones**

#### Arquitectura Implementada ✅
```
/app/backend/core/scheduler/
├── __init__.py
├── config.py              # Configuración central
├── scheduler_manager.py   # Manager con APScheduler
├── job_logger.py          # Logging de ejecuciones
├── routes.py              # API de administración
├── jobs/
│   ├── base_job.py        # Clase base abstracta
│   ├── sla_job.py         # Procesador SLA
│   └── notifications_job.py # Despacho notificaciones
└── locks/
    └── distributed_lock.py # Locks MongoDB
```

#### Jobs Configurados ✅
| Job | Intervalo | Descripción |
|-----|-----------|-------------|
| `sla_processor` | 5 min | Procesa estados SLA, alertas 80%/100%/150% |
| `notifications_dispatcher` | 2 min | Despacha cola de notificaciones |

#### Colecciones MongoDB ✅
| Colección | Descripción |
|-----------|-------------|
| `scheduler_job_log` | Historial de ejecuciones |
| `scheduler_locks` | Locks distribuidos |

#### Endpoints API ✅
| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/v2/scheduler/status` | GET | Estado del scheduler |
| `/api/v2/scheduler/jobs/{id}` | GET | Info de job específico |
| `/api/v2/scheduler/jobs/{id}/run` | POST | Ejecutar manualmente |
| `/api/v2/scheduler/jobs/{id}/pause` | POST | Pausar job |
| `/api/v2/scheduler/jobs/{id}/resume` | POST | Reanudar job |
| `/api/v2/scheduler/logs` | GET | Historial ejecuciones |
| `/api/v2/scheduler/logs/stats` | GET | Estadísticas |
| `/api/v2/scheduler/locks` | GET | Locks activos |
| `/api/v2/scheduler/locks/{name}` | DELETE | Forzar liberación |
| `/api/v2/scheduler/config` | GET | Configuración |

#### Características Clave ✅
- **APScheduler AsyncIOScheduler**: Compatible con FastAPI async
- **Locks distribuidos**: Evita ejecución duplicada en multi-worker
- **Heartbeat**: Extensión automática de locks en jobs largos
- **Logging completo**: Duración, métricas, errores por ejecución
- **Integración lifecycle**: startup/shutdown de FastAPI
- **Horarios permitidos**: Notificaciones solo 08:00-20:00 hora México
- **Variables de entorno**: Configuración sin hardcodear

#### Variables de Entorno
```bash
SCHEDULER_ENABLED=true
SCHEDULER_TIMEZONE=America/Mexico_City
SCHEDULER_SLA_INTERVAL_SECONDS=300
SCHEDULER_SLA_ENABLED=true
SCHEDULER_NOTIFICATIONS_INTERVAL_SECONDS=120
SCHEDULER_NOTIFICATIONS_ENABLED=true
```

#### Verificaciones ✅
- ✅ Scheduler inicia con la app (una sola vez)
- ✅ Jobs se ejecutan en intervalos correctos
- ✅ Locks previenen ejecuciones duplicadas
- ✅ Errores se registran sin tumbar el job
- ✅ Shutdown limpia correctamente

**Estado:** FASE 2B.5.2 COMPLETADA

---

### 2026-04-17 - FASE 2B.5.1: Integración Twilio WhatsApp Real
**Provider real para envío de mensajes WhatsApp via Twilio SDK**

#### Implementación ✅
```
/app/backend/core/communications/providers/
├── base.py              # Interfaz abstracta
├── mock_provider.py     # Provider de pruebas
├── whatsapp_provider.py # Provider HTTP genérico
└── twilio_provider.py   # ← NUEVO: SDK oficial Twilio
```

#### Características del Provider Twilio ✅
- **SDK oficial**: `twilio==9.10.5` (más robusto que HTTP directo)
- **Validación E.164**: Normalización automática de teléfonos
- **Formato WhatsApp**: Conversión a `whatsapp:+XXXXXXXXXXXX`
- **Sin hardcodeo**: Credenciales via variables de entorno
- **Fallback seguro**: Si no hay credenciales, no falla
- **Logging seguro**: No expone credenciales en logs

#### Variables de Entorno Requeridas
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_FROM=+14155238886
```

#### Endpoints API Nuevos ✅
| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/v2/notificaciones-whatsapp/provider-status` | GET | Estado de providers |
| `/api/v2/notificaciones-whatsapp/test-real` | POST | Prueba con Twilio real |
| `/api/v2/notificaciones-whatsapp/config/set-twilio` | POST | Configurar provider Twilio |
| `/api/v2/notificaciones-whatsapp/config/{id}/set-provider` | PUT | Cambiar provider de evento |

#### Verificaciones ✅
- ✅ Mock provider sigue funcionando (no regresión)
- ✅ Scheduler sigue corriendo normalmente
- ✅ Selección de provider por configuración
- ✅ Validación de teléfonos E.164
- ✅ Manejo de errores sin exponer credenciales
- ✅ Preparado para Meta Cloud API (misma interfaz)

#### Cómo Activar Envío Real
```bash
# 1. Configurar variables de entorno en el servidor
export TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export TWILIO_WHATSAPP_FROM=+14155238886

# 2. Reiniciar backend
sudo supervisorctl restart backend

# 3. Verificar disponibilidad
curl /api/v2/notificaciones-whatsapp/provider-status

# 4. Cambiar eventos para usar Twilio
curl -X PUT /api/v2/notificaciones-whatsapp/config/cfg_sla_vencido/set-provider?provider=twilio&modo=real
```

**Estado:** FASE 2B.5.1 COMPLETADA (Pendiente: Credenciales Twilio de producción)

---

## Próximas Fases (Backlog)

### Fase 2B.5.1.1 - Activación Twilio Producción (P0)
- Obtener credenciales Twilio de producción
- Configurar variables de entorno en servidor
- Cambiar eventos críticos a provider Twilio
- Validar envío real con usuarios piloto

### Fase 2B.5.3 - Meta Cloud API (P2)
- Implementar provider para Meta WhatsApp Business API
- Alternativa a Twilio si es necesario
- Misma interfaz, diferente adaptador

### Fase 2C.3 - Aplicación de Cargos ✅ COMPLETADA
- ✅ Estados: PENDIENTE, AUTORIZADO, APLICADO, RECHAZADO, REVERTIDO, CANCELADO
- ✅ Registro formal de cargos con auditoría completa
- ✅ Integración con flujo de responsabilidad económica
- ⏳ Pendiente: Integración futura con Nómina/ERP

### Fase 2D - RBAC Avanzado (P3)
- Matriz de Roles y Permisos (4 niveles)
- Integración con módulo operativo

### Módulo de Finanzas (P3)
- Conciliación bancaria
- Reportes financieros

---

## Credenciales de Prueba
- **Sistema Principal**: `admin@inventario.com` / `admin123`
- **Portal Proveedores**: RFC `EAR201118NG2` / `Proveedor123!`

## Notas Técnicas Importantes
- El cliente evalúa basándose estrictamente en capturas de pantalla (pixel-perfect)
- Timeouts de SQL Server esperados en ambiente Preview
- No modificar lógica de otras páginas sin solicitud explícita
- Nueva colección `server_sucursales_config` para configuración de sucursales
- Fase 2C.1: Colección `responsabilidad_economica` para cálculos de impacto económico
- Fase 2C.3: Colecciones `cargos_economicos` y `cargos_economicos_log` para aplicación formal de cargos

---

### 2026-04-18 - FASE 2B.5.1: Twilio WhatsApp Real - VALIDADA ✅

**Envío real de WhatsApp via Twilio SDK validado en producción**

#### Prueba Exitosa
- **Message SID**: `SM1ff583486b9c44fa2328f13d559ddd6c`
- **Status**: `delivered` ✅
- **Destino**: +5219992692369 (México)
- **Provider**: Twilio Sandbox

#### Correcciones Aplicadas
1. **Manejo de excepciones Twilio**: Clasificación por código de error (63007, 63015, 20003, etc.)
2. **Sanitización de mensajes de error**: No exponer información sensible
3. **Normalización de números México**: Agregar `1` después de `52` para móviles (+521XXXXXXXXXX)

#### Configuración Requerida
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_FROM=+14155238886  # Sandbox o número aprobado
```

#### Formatos de Número Soportados (México)
| Input | Output |
|-------|--------|
| `9991234567` | `whatsapp:+5219991234567` |
| `529991234567` | `whatsapp:+5219991234567` |
| `+529991234567` | `whatsapp:+5219991234567` |
| `+5219991234567` | `whatsapp:+5219991234567` |

**Estado:** FASE 2B.5.1 COMPLETADA Y VALIDADA

---

### 2026-04-18 - FASE 2B.5 CERRADA: Sistema de Notificaciones Completo ✅

**Eventos DECISION_AUDITORIA y CIERRE_WORKFLOW validados con envío real**

#### Pruebas Exitosas
| Evento | Message SID | Status |
|--------|-------------|--------|
| DECISION_AUDITORIA | `SM0aeeb1ef479432b6825e3411403d43fc` | delivered ✅ |
| CIERRE_WORKFLOW | `SMc1dfc8b3f7da79723bb46fadeb57065a` | delivered ✅ |

#### Configuración Sembrada (11 eventos)
| Evento | Provider | Modo |
|--------|----------|------|
| ASIGNACION_TAREA | twilio_whatsapp | real |
| DIFERENCIA_DETECTADA | twilio_whatsapp | real |
| SLA_POR_VENCER | twilio_whatsapp | real |
| SLA_VENCIDO | twilio_whatsapp | real |
| SLA_ESCALADO | twilio_whatsapp | real |
| JUSTIFICACION_RECHAZADA | twilio_whatsapp | real |
| DECISION_AUDITORIA | twilio_whatsapp | real |
| CIERRE_WORKFLOW | twilio_whatsapp | real |
| RESPONSABILIDAD_PROPUESTA | twilio_whatsapp | real |
| RESPONSABILIDAD_APROBADA | twilio_whatsapp | real |
| RESPONSABILIDAD_EN_DISPUTA | twilio_whatsapp | real |

#### Templates Sembrados (11 templates)
- inventarios_asignacion_tarea
- inventarios_diferencia_detectada
- inventarios_sla_por_vencer
- inventarios_sla_vencido
- inventarios_sla_escalado
- inventarios_justificacion_rechazada
- inventarios_decision_auditoria
- inventarios_cierre_workflow
- inventarios_responsabilidad_propuesta
- inventarios_responsabilidad_aprobada
- inventarios_responsabilidad_en_disputa

#### Colecciones MongoDB
- `notification_config` - 11 eventos configurados
- `notification_templates` - 11 templates
- `notification_queue` - Cola de mensajes
- `notification_log` - Auditoría de envíos

**Estado: FASE 2B.5 COMPLETAMENTE CERRADA** ✅
**Sistema de gestión formal de cargos económicos derivados de responsabilidades de inventario**

#### Arquitectura Implementada ✅
```
/app/backend/modules/fase2_operativo/
├── schemas/cargos_schemas.py      # Modelos Pydantic (EstatusCargo, AccionCargo, etc.)
├── repositories/cargos_repository.py  # CRUD cargos_economicos y cargos_economicos_log
├── services/cargos_service.py     # Lógica de negocio completa
└── routes/cargos_routes.py        # 12 endpoints REST
```

#### Estados de Cargo ✅
| Estado | Descripción |
|--------|-------------|
| `PENDIENTE` | Propuesta creada, pendiente autorización |
| `AUTORIZADO` | Autorizado, pendiente aplicación |
| `APLICADO` | Cargo aplicado formalmente |
| `RECHAZADO` | Cargo rechazado (no procedía) |
| `REVERTIDO` | Cargo revertido post-aplicación |
| `CANCELADO` | Cargo cancelado antes de aplicar |

#### Transiciones Válidas ✅
- PENDIENTE → AUTORIZADO | RECHAZADO | CANCELADO
- AUTORIZADO → APLICADO | CANCELADO
- APLICADO → REVERTIDO (requiere GERENTE_OPS+)

#### Colecciones MongoDB ✅
| Colección | Descripción |
|-----------|-------------|
| `cargos_economicos` | Registro formal de cargos |
| `cargos_economicos_log` | Auditoría de todas las transiciones |

#### Endpoints API ✅
| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/v2/cargos` | POST | Crear propuesta de cargo |
| `/api/v2/cargos` | GET | Listar con filtros |
| `/api/v2/cargos/pendientes` | GET | Pendientes de autorización |
| `/api/v2/cargos/aplicados` | GET | Cargos aplicados |
| `/api/v2/cargos/metricas` | GET | Métricas agregadas |
| `/api/v2/cargos/elegibilidad/{id}` | GET | Evaluar elegibilidad |
| `/api/v2/cargos/{id}` | GET | Detalle de cargo |
| `/api/v2/cargos/{id}/log` | GET | Historial de auditoría |
| `/api/v2/cargos/{id}/autorizar` | POST | PENDIENTE → AUTORIZADO |
| `/api/v2/cargos/{id}/aplicar` | POST | AUTORIZADO → APLICADO |
| `/api/v2/cargos/{id}/rechazar` | POST | PENDIENTE → RECHAZADO |
| `/api/v2/cargos/{id}/revertir` | POST | APLICADO → REVERTIDO |
| `/api/v2/cargos/{id}/cancelar` | POST | PENDIENTE/AUTORIZADO → CANCELADO |

#### Reglas de Negocio Implementadas ✅
1. **Elegibilidad**: Solo responsabilidades en estado APROBADO pueden generar cargo
2. **Bloqueos**: No se permite cargo si existe controversia activa o exoneración
3. **Permisos por monto**:
   - ≤$500 MXN: SUPERVISOR
   - ≤$2,000 MXN: GERENTE_OPS
   - >$2,000 MXN: DIRECCION
4. **Reversa**: Requiere rol GERENTE_OPS+ y motivo detallado (mín. 20 caracteres)
5. **Auditoría**: Toda acción genera registro en cargos_economicos_log
6. **Índice único**: Solo un cargo activo por responsabilidad

#### Verificaciones ✅
- ✅ 21/21 pruebas backend pasaron (100%)
- ✅ Ciclo completo PENDIENTE→AUTORIZADO→APLICADO→REVERTIDO verificado
- ✅ Validaciones de transiciones funcionando
- ✅ Permisos por monto/rol funcionando
- ✅ Auditoría completa en cada acción
- ✅ No regresión en módulos existentes

#### Archivos Creados
- `/app/backend/modules/fase2_operativo/schemas/cargos_schemas.py`
- `/app/backend/modules/fase2_operativo/repositories/cargos_repository.py`
- `/app/backend/modules/fase2_operativo/services/cargos_service.py`
- `/app/backend/modules/fase2_operativo/routes/cargos_routes.py`

#### Archivos Modificados
- `/app/backend/modules/fase2_operativo/router.py` (agregar cargos_router)
- `/app/backend/modules/fase2_operativo/repositories/__init__.py`
- `/app/backend/modules/fase2_operativo/services/__init__.py`
- `/app/backend/modules/fase2_operativo/schemas/__init__.py`

#### Rollback
```bash
# Eliminar archivos nuevos
rm /app/backend/modules/fase2_operativo/schemas/cargos_schemas.py
rm /app/backend/modules/fase2_operativo/repositories/cargos_repository.py
rm /app/backend/modules/fase2_operativo/services/cargos_service.py
rm /app/backend/modules/fase2_operativo/routes/cargos_routes.py

# Revertir modificaciones
git checkout -- /app/backend/modules/fase2_operativo/router.py
git checkout -- /app/backend/modules/fase2_operativo/repositories/__init__.py
git checkout -- /app/backend/modules/fase2_operativo/services/__init__.py
git checkout -- /app/backend/modules/fase2_operativo/schemas/__init__.py

# MongoDB: Eliminar colecciones
db.cargos_economicos.drop()
db.cargos_economicos_log.drop()
```

**Estado:** FASE 2C.3 COMPLETADA


---

### 2026-04-19 - FASE 2D: RBAC Avanzado - COMPLETADA ✅

**Sistema de Control de Acceso Basado en Roles implementado en todos los módulos críticos**

#### Arquitectura RBAC ✅
```
/app/backend/core/rbac/
├── schemas.py      # PERMISOS_SISTEMA (40+), ROLES_SISTEMA (6)
├── repository.py   # CRUD MongoDB (rbac_permisos, rbac_roles, etc.)
├── service.py      # RBACService - Motor de autorización
├── middleware.py   # require_permission() dependency
└── routes.py       # Endpoints de administración RBAC
```

#### Roles del Sistema ✅
| Rol | Nivel | Descripción |
|-----|-------|-------------|
| ADMIN | 100 | Administrador total |
| DIRECCION | 80 | Autoriza montos altos y reversas |
| GERENTE_OPS | 60 | Autoriza y aplica cargos |
| SUPERVISOR | 40 | Crea propuestas y gestiona tareas |
| AUDITOR | 30 | Solo lectura para fiscalización |
| OPERADOR | 20 | Ejecuta tareas, registra información |

#### Permisos por Módulo ✅
| Módulo | Permisos |
|--------|----------|
| Cargos | CARGOS_VER, CARGOS_CREAR, CARGOS_AUTORIZAR, CARGOS_APLICAR, CARGOS_RECHAZAR, CARGOS_REVERTIR, CARGOS_CANCELAR |
| Responsabilidad | RESPONSABILIDAD_VER, RESPONSABILIDAD_CALCULAR, RESPONSABILIDAD_PROPONER, RESPONSABILIDAD_APROBAR, RESPONSABILIDAD_RECHAZAR, RESPONSABILIDAD_EXONERAR, RESPONSABILIDAD_DISPUTAR, RESPONSABILIDAD_GESTIONAR |
| SLA | SLA_VER, SLA_CONFIGURAR |
| Notificaciones | NOTIFICACIONES_VER, NOTIFICACIONES_ENVIAR, NOTIFICACIONES_CONFIGURAR |
| RBAC | ROLES_VER, ROLES_GESTIONAR, USUARIOS_VER, USUARIOS_GESTIONAR, RBAC_ADMIN |

#### Módulos Protegidos ✅
| Módulo | Archivo | Estado |
|--------|---------|--------|
| Cargos Económicos | `cargos_routes.py` | ✅ 13 endpoints protegidos |
| Responsabilidad Económica | `responsabilidad_routes.py` | ✅ 14 endpoints protegidos |
| SLA | `sla_routes.py` | ✅ 7 endpoints protegidos |
| Notificaciones | `communications/routes.py` | ✅ 16 endpoints protegidos |

#### Colecciones MongoDB ✅
| Colección | Descripción |
|-----------|-------------|
| `rbac_permisos` | Catálogo de permisos del sistema |
| `rbac_roles` | Roles con permisos asignados |
| `rbac_usuarios_roles` | Asignación de roles a usuarios |
| `rbac_audit_log` | Auditoría de verificaciones |

#### Endpoints API RBAC ✅
| Endpoint | Método | Permiso Requerido |
|----------|--------|-------------------|
| `/api/v2/rbac/roles` | GET | ROLES_VER |
| `/api/v2/rbac/roles` | POST | ROLES_GESTIONAR |
| `/api/v2/rbac/permisos` | GET | ROLES_VER |
| `/api/v2/rbac/asignar` | POST | ROLES_GESTIONAR |
| `/api/v2/rbac/revocar` | POST | ROLES_GESTIONAR |
| `/api/v2/rbac/usuario/{id}/permisos` | GET | USUARIOS_VER |
| `/api/v2/rbac/mis-permisos` | GET | (autenticado) |
| `/api/v2/rbac/audit` | GET | RBAC_ADMIN |

#### Mapeo Legacy a RBAC ✅
| Rol Legacy | Rol RBAC |
|------------|----------|
| Administrador | ADMIN |
| Supervisor | SUPERVISOR |
| Usuario | OPERADOR |
| Gerente | GERENTE_OPS |
| Director | DIRECCION |
| Auditor | AUDITOR |

#### Verificaciones ✅
- ✅ 27/27 pruebas backend pasaron (100%)
- ✅ Admin (Administrador) accede a todos los endpoints
- ✅ Operador (Usuario) puede VER pero no CREAR/APLICAR/AUTORIZAR/CONFIGURAR
- ✅ Respuestas 403 Forbidden con detalle del permiso requerido
- ✅ Respuestas 401 Unauthorized sin token
- ✅ Auditoría de todas las verificaciones de permisos
- ✅ No regresión en módulos existentes

#### Usuarios de Prueba
| Usuario | Password | Rol Legacy | Rol RBAC |
|---------|----------|------------|----------|
| admin.rbac.test@edarsa.com | AdminRBAC2024! | Administrador | ADMIN |
| operador.test@edarsa.com | OperadorTest2024! | Usuario | OPERADOR |

#### Archivos Creados
- `/app/backend/core/rbac/schemas.py`
- `/app/backend/core/rbac/repository.py`
- `/app/backend/core/rbac/service.py`
- `/app/backend/core/rbac/middleware.py`
- `/app/backend/core/rbac/routes.py`
- `/app/backend/core/rbac/__init__.py`
- `/app/backend/tests/test_rbac_fase2d.py`

#### Archivos Modificados
- `/app/backend/modules/fase2_operativo/routes/cargos_routes.py` (decoradores RBAC)
- `/app/backend/modules/fase2_operativo/routes/responsabilidad_routes.py` (decoradores RBAC)
- `/app/backend/modules/fase2_operativo/routes/sla_routes.py` (decoradores RBAC)
- `/app/backend/core/communications/routes.py` (decoradores RBAC)
- `/app/backend/server.py` (incluir rbac_router)

**Estado:** FASE 2D COMPLETADA ✅

---

### 2026-04-18 - UI Scheduler (Shuttle de Programación) - COMPLETADA ✅

**Interfaz completa para gestión de jobs automatizados del sistema**

#### Funcionalidades Implementadas ✅
| Feature | Descripción |
|---------|-------------|
| KPIs | Scheduler activo/inactivo, jobs activos, jobs pausados, ejecuciones 24h, fallos 24h |
| Lista de Jobs | Estado visual (activo/pausado/error), intervalo, próxima y última ejecución |
| Acciones | Ejecutar manualmente, pausar, reanudar con confirmación |
| Historial | Tabla con job, estado, duración, procesados, éxito/fallo, fecha, mensaje |
| Filtros | Por job, estado, período (1h-168h), búsqueda por texto/error |
| Auto-refresh | Toggle con intervalo configurable (30s) y botón manual |
| RBAC | Acciones habilitadas/deshabilitadas según permisos del usuario |


---

### 2026-04-18 - Módulo Auditorías Programadas - COMPLETADO ✅

**Módulo completo para gestión de auditorías de inventario automatizadas**

#### Backend ✅
| Componente | Archivo |
|------------|---------|
| Schemas | `auditoria_programada_schemas.py` |
| Repository | `auditoria_programada_repository.py` |
| Service | `auditoria_programada_service.py` |
| Routes | `auditoria_programada_routes.py` |
| Job Scheduler | `core/scheduler/jobs/auditorias_job.py` |

#### Colecciones MongoDB ✅
- `auditorias_programadas` - Configuración de programaciones
- `auditorias_programadas_log` - Bitácora de ejecuciones

#### Endpoints API ✅
| Endpoint | Método | Permiso |
|----------|--------|---------|
| `/api/v2/auditorias-programadas` | GET | AUDITORIA_VER |
| `/api/v2/auditorias-programadas` | POST | AUDITORIA_PROGRAMAR |
| `/api/v2/auditorias-programadas/{id}` | GET/PUT/DELETE | AUDITORIA_* |
| `/api/v2/auditorias-programadas/{id}/ejecutar` | POST | AUDITORIA_GESTIONAR |
| `/api/v2/auditorias-programadas/{id}/activar` | POST | AUDITORIA_PROGRAMAR |
| `/api/v2/auditorias-programadas/{id}/desactivar` | POST | AUDITORIA_PROGRAMAR |
| `/api/v2/auditorias-programadas/kpis` | GET | AUDITORIA_VER |
| `/api/v2/auditorias-programadas/calendario` | GET | AUDITORIA_VER |
| `/api/v2/auditorias-programadas/historial` | GET | AUDITORIA_VER |

#### Frontend ✅
- Página `/auditorias-programadas` con:
  - KPIs: Total, Activas, Inactivas, Hoy, En Curso, Mes, Fallidas, Cumplimiento
  - Lista de programaciones con estado visual
  - Calendario mensual
  - Historial de ejecuciones
  - Formulario crear/editar
  - Acciones con confirmación: Ejecutar, Activar, Desactivar
  - Auto-refresh

#### Job Scheduler ✅
- `auditorias_scheduler` - Ejecuta cada hora
- Idempotente (no duplica ejecuciones)
- Crea workflows de inventario automáticamente
- Registra cada ejecución en log

#### Permisos RBAC ✅
| Permiso | Roles |
|---------|-------|
| AUDITORIA_VER | ADMIN, DIRECCION, GERENTE_OPS, SUPERVISOR, AUDITOR |
| AUDITORIA_PROGRAMAR | ADMIN, DIRECCION, GERENTE_OPS |
| AUDITORIA_GESTIONAR | ADMIN, DIRECCION |

**Estado:** MÓDULO AUDITORÍAS PROGRAMADAS COMPLETADO ✅

#### Permisos RBAC Scheduler ✅
| Permiso | Acción | Roles |
|---------|--------|-------|
| SCHEDULER_VER | Ver status, config, logs, stats | ADMIN, DIRECCION, GERENTE_OPS, SUPERVISOR, AUDITOR |
| SCHEDULER_GESTIONAR | Pausar/Reanudar jobs | ADMIN, DIRECCION, GERENTE_OPS |
| SCHEDULER_ADMIN | Ejecutar manualmente, forzar locks | ADMIN, DIRECCION |

#### Endpoints Protegidos ✅
| Endpoint | Método | Permiso |
|----------|--------|---------|
| `/api/v2/scheduler/status` | GET | SCHEDULER_VER |
| `/api/v2/scheduler/config` | GET | SCHEDULER_VER |
| `/api/v2/scheduler/logs` | GET | SCHEDULER_VER |
| `/api/v2/scheduler/logs/stats` | GET | SCHEDULER_VER |
| `/api/v2/scheduler/jobs/{id}/run` | POST | SCHEDULER_ADMIN |
| `/api/v2/scheduler/jobs/{id}/pause` | POST | SCHEDULER_GESTIONAR |
| `/api/v2/scheduler/jobs/{id}/resume` | POST | SCHEDULER_GESTIONAR |
| `/api/v2/scheduler/locks` | GET | SCHEDULER_VER |
| `/api/v2/scheduler/locks/{name}` | DELETE | SCHEDULER_ADMIN |

#### Archivos Creados ✅
- `/app/frontend/src/pages/Scheduler.jsx` - UI completa (~815 líneas)

#### Archivos Modificados ✅
- `/app/frontend/src/App.js` - Ruta `/scheduler`
- `/app/frontend/src/pages/Layout.js` - Menú "Programación" en sección Sistema
- `/app/backend/core/scheduler/routes.py` - Decoradores RBAC en todos los endpoints
- `/app/backend/core/rbac/schemas.py` - SCHEDULER_VER agregado a SUPERVISOR

#### Testing ✅
- Backend: 22/22 tests pasaron (100%)
- Frontend: 95% funcional (issue menor corregido)
- RBAC: Operador recibe 403 en todos los endpoints

**Estado:** UI SCHEDULER COMPLETADA ✅

---

### 2025-12 - Validación E2E Flujo Completo ✅

**Validación automatizada del flujo End-to-End:**
1. ✅ Auditoría programada → crea workflow
2. ✅ Workflow → cierra correctamente
3. ✅ Cierre → genera responsabilidad económica
4. ✅ Responsabilidad → permite autorización/aplicación de cargo
5. ✅ Cargo → dispara notificaciones
6. ✅ Todo queda registrado y auditado

**GAPS Corregidos:**
1. `notification_service.py`: Agregado método `notificar_cargo_aplicado()` 
2. `cargos_service.py`: Integrada llamada a notificaciones en `aplicar_cargo()`
3. `auditoria_programada_service.py`: Corregido problema async/sync en `_crear_workflow_inventario()`

**Archivos Modificados:**
- `/app/backend/modules/fase2_operativo/services/notification_service.py`
  - Nuevo evento: `EVENTO_CARGO_APLICADO`
  - Nuevo método: `notificar_cargo_aplicado()`
  - Nuevo template HTML: `_generar_html_cargo_aplicado()`
- `/app/backend/modules/fase2_operativo/services/cargos_service.py`
  - Nuevo método: `_notificar_cargo_aplicado()`
  - Modificado: `aplicar_cargo()` ahora dispara notificación automática
- `/app/backend/modules/fase2_operativo/services/auditoria_programada_service.py`
  - Corregido: `_crear_workflow_inventario()` ahora usa PyMongo sync directamente

**Test Script Creado:**
- `/app/backend/tests/test_e2e_flujo_completo.py`
  - Ejecuta validación completa en 6 pasos
  - Detecta GAPS automáticamente
  - Limpia datos de prueba al finalizar

**Resultado:** 6/6 PASOS EXITOSOS - FLUJO E2E COMPLETO Y FUNCIONAL ✅

---

## Backlog Actualizado

### P0 (Urgente) - COMPLETADO
- ✅ FASE 2C.3: Cargos Económicos
- ✅ FASE 2B.5: Notificaciones WhatsApp (Twilio SDK)
- ✅ FASE 2D: RBAC Avanzado
- ✅ UI Scheduler (Shuttle de Programación)
- ✅ Módulo Auditorías Programadas
- ✅ Validación E2E Flujo Completo (Auditoría → Cargo → Notificación)

### P1 (Alta Prioridad) - PENDIENTES
- 🔴 Integración real con nómina/ERP (PRERREQUISITO E2E VALIDADO ✅)

### P2 (Media Prioridad)
- Reportes financieros avanzados
- Meta Cloud API para WhatsApp
- Panel de administración RBAC en frontend
- Alertas en tiempo real por fallo de job