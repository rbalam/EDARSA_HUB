# AUDITORÍA DE FUENTES DE DATOS EDARSAHUB

**Fecha:** 8 de Mayo 2026  
**Autor:** Arquitectura de Sistemas  
**Versión:** 1.0 - DIAGNÓSTICO  
**Estado:** SOLO LECTURA - NO SE HAN REALIZADO CAMBIOS

---

## 1. RESUMEN EJECUTIVO

Se realizó una auditoría completa del sistema EDARSAHUB para mapear las fuentes de datos reales por módulo. El diagnóstico revela:

| Métrica | Valor |
|---------|-------|
| **Tablas en EDARSAHUB SQL** | 203 |
| **Colecciones en MongoDB** | 72 |
| **Módulos analizados** | 14 |
| **Dependencias MongoDB detectadas** | 15 colecciones críticas |
| **Tablas EDARSAHUB para Auth/RBAC** | 14 tablas completas |

### HALLAZGO PRINCIPAL

**EDARSAHUB SQL Server ya tiene estructura completa para Usuarios, Roles, Permisos, Sesiones, Servidores, Unidades de Negocio, pero el código actual sigue leyendo mayoritariamente de MongoDB para estos módulos.**

Esto constituye **DEUDA TÉCNICA** que debe planificarse para migración progresiva.

---

## 2. MÁXIMA ARQUITECTÓNICA APLICADA

✅ **CONFIRMADO:** EDARSAHUB es el cerebro del sistema.  
✅ **CONFIRMADO:** No se crearon tablas en esta auditoría.  
✅ **CONFIRMADO:** No se modificó código.  
✅ **CONFIRMADO:** Se validó existencia de estructuras antes de proponer nuevas.

---

## 3. INVENTARIO REAL DE EDARSAHUB (203 TABLAS)

### 3.1 Usuarios / Auth / RBAC (14 tablas) ✅ EXISTE
```
Usuario_Catalogo          (31 columnas) - 0 registros
Usuario_Roles             (8 columnas)  - 5 registros
Usuario_RolesAsignacion   (9 columnas)  - 0 registros
Usuario_PermisosRolModulo (14 columnas) - 0 registros
Usuario_Modulos           (14 columnas) - 8 registros
Usuario_Sesiones          (16 columnas) - 0 registros
Usuario_Acciones          (6 columnas)
Usuario_Autorizaciones    (22 columnas)
Usuario_AutorizacionesDetalle (11 columnas)
Usuario_LogAccesos        (9 columnas)
Usuario_LogActividades    (16 columnas)
Usuario_MatrizAutorizacion (12 columnas)
Usuario_PortalConfiguracion (11 columnas)
Usuario_TiposAutorizacion (7 columnas)
```

### 3.2 Servidores / Conexiones (2 tablas) ✅ EXISTE
```
Servidores_Conexiones     (30 columnas) - 17 registros ✅ CON DATOS
Servidores_Conexiones_Log (8 columnas)
```

### 3.3 Unidades de Negocio / Estructura (5 tablas) ✅ EXISTE
```
Unidades_Negocio          (10 columnas) - 5 registros ✅ CON DATOS
RH_Cat_Sucursales         (4 columnas)
RH_Cat_SucursalesFiscal   (10 columnas)
Finanzas_ConfiguracionTPV_Sucursal (21 columnas)
RH_Flujo_Nomina_Sucursal  (12 columnas)
```

### 3.4 Comercial / Ventas (19 tablas) ✅ EXISTE
```
Comercial_KPIs_Diarios_v2      (33 columnas)
Comercial_KPIs_Historico       (22 columnas)
Comercial_KPIs_Mensuales_v2    (30 columnas)
Comercial_SyncLog_v2           (20 columnas)
Comercial_Ventas_Dia_Abiertas_v2 (19 columnas) ✅ USADO COMO FALLBACK
Venta_Encabezado, Venta_Detalle, Venta_Pagos, etc.
```

### 3.5 Compras (19 tablas) ✅ EXISTE
```
Compras                   (40 columnas)
Compras_Detalle           (24 columnas)
Compras_Ordenes           (34 columnas)
Compras_Pedidos           (32 columnas)
Compras_KPIs_Historico    (23 columnas)
Compras_DocumentosFiscales (41 columnas)
... y 13 tablas más
```

### 3.6 Finanzas (19 tablas) ✅ EXISTE
```
Finanzas_Cat_CuentasBancarias  (13 columnas) ✅ USADO
Finanzas_SaldosBancarios       (18 columnas) ✅ USADO
Finanzas_CuentasPorPagar       (18 columnas) ✅ USADO
Finanzas_CortesCaja            (53 columnas)
Finanzas_CuadresZ              (71 columnas)
Finanzas_Presupuestos          (13 columnas)
Finanzas_KPIs_Historico        (30 columnas)
Global_Cat_Bancos              (6 columnas)
... y 11 tablas más
```

### 3.7 RH / Nóminas (47 tablas) ✅ EXISTE
```
RH_Colaboradores_Expediente    (33 columnas)
RH_Nomina                      (31 columnas)
RH_Nomina_Detalle              (11 columnas)
RH_Contratos                   (27 columnas)
RH_Periodos_Nomina             (14 columnas)
RH_Cat_Puestos                 (12 columnas)
RH_Cat_Departamentos           (7 columnas)
RH_Cat_ConceptosNomina         (19 columnas)
... y 39 tablas más
```

### 3.8 Inventarios (5 tablas) ✅ EXISTE
```
Inventario_Almacenes           (11 columnas)
Inventario_Existencias         (12 columnas)
Inventario_Movimientos         (13 columnas)
Inventario_MovimientosDetalle  (12 columnas)
Inventario_TipoMovimiento      (6 columnas)
```

### 3.9 Proveedores (21 tablas) ✅ EXISTE
```
Proveedor_Catalogo             (31 columnas)
Proveedor_CuentasBancarias     (15 columnas)
Proveedor_Contactos            (17 columnas)
... y 18 tablas más
```

### 3.10 Productos / Catálogos (8 tablas) ✅ EXISTE
```
Producto_Catalogo              (36 columnas)
Producto_Familias, Producto_Lineas, Producto_Marcas, etc.
```

### 3.11 Automatización (6 tablas) ✅ EXISTE
```
automatizacion_inventarios_config         (12 columnas)
automatizacion_inventarios_destinatarios  (15 columnas)
automatizacion_inventarios_ejecuciones    (11 columnas)
automatizacion_inventarios_envios         (11 columnas)
automatizacion_inventarios_folios_procesados (19 columnas)
automatizacion_inventarios_ultimo_folio_conocido (12 columnas)
```

### 3.12 Propinas (3 tablas) ✅ EXISTE
```
propinas_tpv_config    (19 columnas)
propinas_tpv_control   (60 columnas)
propinas_tpv_historial (13 columnas)
```

---

## 4. INVENTARIO REAL DE MONGODB (72 COLECCIONES)

### 4.1 Colecciones Críticas con Datos
| Colección | Documentos | Uso Actual |
|-----------|------------|------------|
| `users` | 15 | Auth principal |
| `servers` | 13 | Configuración servidores |
| `roles` | 4 | Roles legacy |
| `empresas` | 5 | Estructura org |
| `rbac_roles` | 6 | RBAC moderno |
| `rbac_permisos` | 43 | Permisos RBAC |
| `rbac_usuarios_roles` | 72 | Asignaciones RBAC |
| `sec_unidades_negocio` | 7 | Unidades negocio |
| `sec_sucursales` | 7 | Sucursales |
| `scheduler_job_log` | 8,979 | Logs de jobs |
| `alert_recipients` | 2 | Destinatarios alertas |
| `auditoria_compras_bitacora` | 1,477 | Bitácora compras |
| `comercial_cache` | 60 | Cache KPIs |
| `dashboard_cache` | 49 | Cache dashboard |

### 4.2 Colecciones de Cache/Logs (Uso Legítimo)
```
scheduler_job_log, scheduler_locks
dashboard_cache, comercial_cache, kpis_cache
auditoria_compras_bitacora, auditoria_financiera
inventarios_procesados_auto
notification_config, notificaciones_log
```

### 4.3 Colecciones Legacy/Deuda Técnica
```
users (debería usar Usuario_Catalogo en EDARSAHUB)
servers (debería usar Servidores_Conexiones en EDARSAHUB)
roles (debería usar Usuario_Roles en EDARSAHUB)
empresas (no hay equivalente directo en EDARSAHUB - REQUIERE PROPUESTA)
sec_unidades_negocio (debería usar Unidades_Negocio en EDARSAHUB)
sec_sucursales (debería usar RH_Cat_Sucursales en EDARSAHUB)
```

---

## 5. MAPA ACTUAL DEL CÓDIGO

### 5.1 Uso de MongoDB por Archivo Principal (server.py)
| Colección | Referencias | Criticidad |
|-----------|-------------|------------|
| `db.servers` | 85 | ALTA - Crítico para operación |
| `db.informes_auditoria` | 26 | MEDIA |
| `db.users` | 18 | ALTA - Auth principal |
| `db.nomina_ciclos` | 15 | MEDIA |
| `db.solicitudes_catalogos` | 14 | BAJA |
| `db.server_sucursales_config` | 10 | ALTA |
| `db.sec_bitacora_admin` | 10 | BAJA (logs) |

### 5.2 Uso de SQL/EDARSAHUB por Módulo
| Módulo | Referencias SQL | Estado |
|--------|-----------------|--------|
| `finanzas` | 1,005 | ✅ EDARSAHUB PRIMARIO |
| `comercial` | 424 | ✅ HÍBRIDO CORRECTO |
| `rh` | 212 | ✅ EDARSAHUB PRIMARIO |
| `comercial_v2` | 183 | ✅ HÍBRIDO CORRECTO |
| `api_connections` | 148 | ✅ SQL VIVO |
| `automatizacion` | 67 | ✅ EDARSAHUB PRIMARIO |
| `compras` | 39 | ⚠️ SQL VIVO (debería usar EDARSAHUB para histórico) |

---

## 6. VALIDACIÓN DEL MAPA PROPORCIONADO

| Módulo | Mapa Original | Validación | Corrección |
|--------|---------------|------------|------------|
| USUARIOS/AUTH/RBAC | MongoDB | ❌ INCORRECTO | EDARSAHUB tiene tablas completas pero NO SE USAN |
| SERVIDORES | MongoDB + EDARSAHUB | ⚠️ PARCIAL | EDARSAHUB tiene 17 servidores, MongoDB tiene 13 |
| MIS TAREAS | MongoDB | ✅ CORRECTO | No hay equivalente en EDARSAHUB |
| TABLERO EJECUTIVO | EDARSAHUB + SQL vivo | ✅ CORRECTO | Usa Comercial_Ventas_Dia_Abiertas_v2 como fallback |
| COMERCIAL | SQL vivo + EDARSAHUB | ✅ CORRECTO | Híbrido bien implementado |
| COMPRAS | SQL vivo + MongoDB | ⚠️ PARCIAL | EDARSAHUB tiene 19 tablas de Compras_ |
| OPERACIONES | SQL vivo | ⚠️ PARCIAL | Debería usar EDARSAHUB para histórico |
| FINANZAS | EDARSAHUB | ✅ CORRECTO | 100% EDARSAHUB |
| RH/NÓMINAS | EDARSAHUB | ✅ CORRECTO | 100% EDARSAHUB |
| CATÁLOGOS | EDARSAHUB + SQL | ✅ CORRECTO | Usa Producto_Catalogo |
| CENTRO DE CONTROL | MongoDB | ⚠️ PARCIAL | alert_recipients en MongoDB, no hay equivalente SQL |
| SCHEDULER | MongoDB | ✅ CORRECTO TEMPORAL | scheduler_job_log es efímero |
| ALERTAS | MongoDB | ⚠️ PARCIAL | EDARSAHUB tiene ActivoFijo_Alertas |
| EMPRESAS/UNIDADES | MongoDB | ❌ INCORRECTO | EDARSAHUB tiene Unidades_Negocio |

---

## 7. DICTAMEN POR MÓDULO

| # | Módulo | Fuente Actual | Tablas MongoDB | Tablas EDARSAHUB | SQL Vivo | ¿EDARSAHUB Principal? | Dependencia MongoDB | **DICTAMEN** |
|---|--------|---------------|----------------|------------------|----------|----------------------|--------------------|--------------| 
| 1 | **USUARIOS/AUTH/RBAC** | MongoDB | users, roles, rbac_* | Usuario_* (14 tablas) | NO | SÍ (estructura completa) | CRÍTICA | **MONGO_LEGACY_DEUDA_TÉCNICA** |
| 2 | **SERVIDORES** | MongoDB + EDARSAHUB | servers | Servidores_Conexiones | NO | SÍ (17 registros) | ALTA | **EDARSAHUB_EXISTE_PERO_CÓDIGO_USA_MONGO** |
| 3 | **MIS TAREAS** | MongoDB | fase2_operativo_* | NO EXISTE | NO | NO (workflow local) | LEGÍTIMA | **MONGO_LEGÍTIMO_TEMPORAL** |
| 4 | **TABLERO EJECUTIVO** | EDARSAHUB + SQL vivo | comercial_cache | Comercial_Ventas_Dia_* | SÍ | SÍ | CACHE LEGÍTIMO | **HÍBRIDO_CORRECTO_CON_REGLAS** |
| 5 | **COMERCIAL** | SQL vivo + EDARSAHUB | comercial_cache, kpis_cache | Comercial_KPIs_*, Venta_* | SÍ | SÍ para histórico | CACHE LEGÍTIMO | **HÍBRIDO_CORRECTO_CON_REGLAS** |
| 6 | **COMPRAS** | SQL vivo + MongoDB | compras_params | Compras_* (19 tablas) | SÍ | SÍ para histórico | BAJA | **SQL_VIVO_OPERATIVO_CORRECTO** |
| 7 | **OPERACIONES/INV** | SQL vivo | inventarios_procesados_* | Inventario_* (5 tablas) | SÍ | SÍ para histórico | CACHE LEGÍTIMO | **SQL_VIVO_OPERATIVO_CORRECTO** |
| 8 | **FINANZAS** | EDARSAHUB | finanzas_checkpoints | Finanzas_* (19 tablas) | NO | SÍ (100%) | MÍNIMA | **EDARSAHUB_PRIMARIO_CONFIRMADO** |
| 9 | **RH/NÓMINAS** | EDARSAHUB | NO | RH_* (47 tablas) | NO | SÍ (100%) | NINGUNA | **EDARSAHUB_PRIMARIO_CONFIRMADO** |
| 10 | **CATÁLOGOS** | EDARSAHUB + SQL | catalogos_sql | Producto_*, Proveedor_* | SÍ | SÍ | MÍNIMA | **EDARSAHUB_PRIMARIO_CONFIRMADO** |
| 11 | **CENTRO DE CONTROL** | MongoDB | alert_recipients, notificaciones_log | NO EXISTE | SÍ (monitoreo) | NO | ALTA | **EDARSAHUB_NO_EXISTE_REQUIERE_PROPUESTA** |
| 12 | **SCHEDULER** | MongoDB | scheduler_job_log, scheduler_locks | NO EXISTE | NO | NO (efímero) | LEGÍTIMA | **MONGO_LEGÍTIMO_TEMPORAL** |
| 13 | **ALERTAS** | MongoDB | alertas_sistema | ActivoFijo_Alertas | NO | PARCIAL | MEDIA | **EDARSAHUB_EXISTE_PERO_CÓDIGO_USA_MONGO** |
| 14 | **EMPRESAS/UNIDADES** | MongoDB | empresas, sec_unidades_* | Unidades_Negocio | NO | SÍ | ALTA | **EDARSAHUB_EXISTE_PERO_CÓDIGO_USA_MONGO** |

---

## 8. CLASIFICACIÓN DE DEPENDENCIAS MONGODB

### 8.1 LEGÍTIMAS (Mantener)
| Colección | Razón | Riesgo de Eliminar |
|-----------|-------|-------------------|
| `scheduler_job_log` | Logs efímeros de jobs | BAJO - Solo monitoreo |
| `scheduler_locks` | Locks distribuidos | MEDIO - Concurrencia |
| `dashboard_cache` | Cache temporal | BAJO - Se regenera |
| `comercial_cache` | Cache KPIs | BAJO - Se regenera |
| `kpis_cache` | Cache métricas | BAJO - Se regenera |

### 8.2 TEMPORALES (Evaluar migración futura)
| Colección | Razón | Riesgo de Eliminar |
|-----------|-------|-------------------|
| `alert_recipients` | No hay tabla equivalente en EDARSAHUB | MEDIO |
| `notificaciones_log` | Logs de notificaciones | BAJO |
| `fase2_operativo_*` | Workflows locales | MEDIO |

### 8.3 LEGACY / DEUDA TÉCNICA (Migrar a EDARSAHUB)
| Colección | Tabla EDARSAHUB Equivalente | Prioridad Migración |
|-----------|----------------------------|---------------------|
| `users` | `Usuario_Catalogo` | **P0 CRÍTICO** |
| `roles` | `Usuario_Roles` | **P0 CRÍTICO** |
| `rbac_roles` | `Usuario_Roles` | **P0 CRÍTICO** |
| `rbac_permisos` | `Usuario_PermisosRolModulo` | **P0 CRÍTICO** |
| `rbac_usuarios_roles` | `Usuario_RolesAsignacion` | **P0 CRÍTICO** |
| `servers` | `Servidores_Conexiones` | **P1 ALTO** |
| `empresas` | NO EXISTE - Requiere propuesta | **P2 MEDIO** |
| `sec_unidades_negocio` | `Unidades_Negocio` | **P1 ALTO** |
| `sec_sucursales` | `RH_Cat_Sucursales` | **P1 ALTO** |

---

## 9. TABLAS QUE NO DEBEN DUPLICARSE

⛔ **PROHIBIDO CREAR** las siguientes tablas porque ya existen en EDARSAHUB:

| Propuesta Potencial | Tabla Existente en EDARSAHUB |
|--------------------|------------------------------|
| Tabla de usuarios nueva | `Usuario_Catalogo` |
| Tabla de roles nueva | `Usuario_Roles` |
| Tabla de permisos nueva | `Usuario_PermisosRolModulo` |
| Tabla de sesiones nueva | `Usuario_Sesiones` |
| Tabla de servidores nueva | `Servidores_Conexiones` |
| Tabla de sucursales nueva | `RH_Cat_Sucursales` |
| Tabla de unidades de negocio | `Unidades_Negocio` |
| Tabla de bancos nueva | `Global_Cat_Bancos` |
| Tabla de cuentas bancarias | `Finanzas_Cat_CuentasBancarias` |
| Tabla de proveedores nueva | `Proveedor_Catalogo` |
| Tabla de productos nueva | `Producto_Catalogo` |
| Tabla de empleados nueva | `RH_Colaboradores_Expediente` |
| Tabla de nóminas nueva | `RH_Nomina` |
| Tabla de inventarios nueva | `Inventario_Existencias` |

---

## 10. TABLAS QUE PODRÍAN REQUERIRSE (PROPUESTA FUTURA)

Las siguientes tablas **NO EXISTEN** en EDARSAHUB y podrían requerirse:

| Tabla Propuesta | Módulo | Justificación | Prioridad |
|-----------------|--------|---------------|-----------|
| `Sistema_Empresas` | Empresas | No hay catálogo de empresas holding | P2 |
| `Sistema_Alertas` | Centro Control | Solo existe ActivoFijo_Alertas | P3 |
| `Sistema_NotificacionesConfig` | Centro Control | Configuración de canales | P3 |
| `Sistema_NotificacionesLog` | Centro Control | Historial de envíos | P3 |
| `Operativo_Tareas` | Mis Tareas | Workflows operativos | P2 |
| `Operativo_Cargos` | Mis Tareas | Cargos/responsabilidades | P2 |

**NOTA:** Estas propuestas requieren autorización expresa antes de implementarse.

---

## 11. RIESGOS DETECTADOS

### 11.1 Riesgo CRÍTICO
| Riesgo | Impacto | Módulos Afectados |
|--------|---------|-------------------|
| Auth/RBAC en MongoDB mientras EDARSAHUB tiene estructura vacía | Inconsistencia de datos maestros | TODOS |
| Servidores duplicados (13 en MongoDB, 17 en EDARSAHUB) | Configuraciones desincronizadas | Comercial, Compras, Operaciones |

### 11.2 Riesgo ALTO
| Riesgo | Impacto | Módulos Afectados |
|--------|---------|-------------------|
| Unidades de negocio en MongoDB sin sincronía con EDARSAHUB | Filtros RBAC incorrectos | Todos los dashboards |
| Sucursales en MongoDB vs RH_Cat_Sucursales | Inconsistencia en reportes | RH, Finanzas |

### 11.3 Riesgo MEDIO
| Riesgo | Impacto | Módulos Afectados |
|--------|---------|-------------------|
| Cache MongoDB sin TTL definido | Datos obsoletos | Comercial, Dashboard |
| Logs scheduler sin purga automática | Crecimiento sin límite | Sistema |

---

## 12. RECOMENDACIÓN DE SIGUIENTE FASE

### DIAGNÓSTICO CERRADO ✅
Este documento constituye el diagnóstico completo. No se realizaron cambios.

### PROPUESTA FUTURA (Requiere Autorización)

**FASE A - P0 CRÍTICO: Migración Auth/RBAC**
1. Poblar `Usuario_Catalogo` desde MongoDB `users`
2. Sincronizar `Usuario_Roles` con `rbac_roles`
3. Migrar `rbac_permisos` a `Usuario_PermisosRolModulo`
4. Migrar `rbac_usuarios_roles` a `Usuario_RolesAsignacion`
5. Actualizar código para leer de EDARSAHUB
6. Mantener MongoDB como fallback temporal

**FASE B - P1 ALTO: Consolidación Servidores**
1. Validar paridad entre MongoDB `servers` y `Servidores_Conexiones`
2. Migrar configuraciones faltantes
3. Actualizar server_registry.py para eliminar fallback MongoDB

**FASE C - P1 ALTO: Estructura Organizacional**
1. Sincronizar `sec_unidades_negocio` con `Unidades_Negocio`
2. Sincronizar `sec_sucursales` con `RH_Cat_Sucursales`
3. Proponer tabla `Sistema_Empresas` si se justifica

**FASE D - P2 MEDIO: Centro de Control**
1. Proponer nuevas tablas para alertas y notificaciones
2. Migrar `alert_recipients` a EDARSAHUB

### IMPLEMENTACIÓN FUTURA
❌ **NO AUTORIZADA** - Requiere dictamen expreso del usuario.

---

## ANEXO: COMANDOS DE VALIDACIÓN USADOS

```sql
-- Inventario de tablas EDARSAHUB
SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME;

-- Estructura de tabla específica
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Usuario_Catalogo';

-- Conteo de registros
SELECT COUNT(*) FROM Servidores_Conexiones;
```

```bash
# Dependencias MongoDB en código
grep -o "db\.\w*" /app/backend/server.py | sort | uniq -c | sort -rn

# Referencias SQL por módulo
grep -ri "EDARSAHUB" /app/backend/modules/ --include="*.py" | wc -l
```

---

**FIN DEL DIAGNÓSTICO**

*Este documento es de solo lectura. Cualquier modificación al sistema requiere autorización expresa.*
