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

---

## Credenciales de Prueba
- **Sistema Principal**: `admin@inventario.com` / `admin123`
- **Portal Proveedores**: RFC `EAR201118NG2` / `Proveedor123!`

## Notas Técnicas Importantes
- El cliente evalúa basándose estrictamente en capturas de pantalla (pixel-perfect)
- Timeouts de SQL Server esperados en ambiente Preview
- No modificar lógica de otras páginas sin solicitud explícita
- Nueva colección `server_sucursales_config` para configuración de sucursales
