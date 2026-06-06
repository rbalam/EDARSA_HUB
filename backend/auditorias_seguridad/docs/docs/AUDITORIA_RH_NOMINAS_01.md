# AUDITORIA-TABLEROS-KPIS-FILTROS-01 — RH y Nóminas

**Código:** AUDITORIA-RH-NOMINAS-01  
**Fecha:** 2025-12-27  
**Módulo:** Recursos Humanos / Nóminas  
**Estado:** ✅ CORRECCIÓN APLICADA — Conexión EDARSAHUB directa

---

## Resumen Ejecutivo

El módulo RH/Nóminas estaba bloqueado por una **falla de arquitectura** que fue **corregida**.

### Corrección Aplicada: RH-NOMINAS-EDARSAHUB-CONNECTION-01

Se modificó `/app/backend/modules/rh/repository.py` para usar conexión directa a EDARSAHUB vía `EDARSAHUB_CONFIG` (variables de entorno), eliminando la dependencia incorrecta de MongoDB `servers` con `active=True`.

### Comparación de Arquitecturas

| Componente | Método de Conexión | Depende de `active` | Estado |
|------------|-------------------|---------------------|--------|
| `server_registry.py` | `EDARSAHUB_CONFIG` (directo) | NO | ✅ FUNCIONA |
| `modules/rh/repository.py` | `EDARSAHUB_CONFIG` (directo) | NO | ✅ CORREGIDO |

---

## Tabla de Validación Post-Corrección

| Endpoint | Status HTTP | Registros | Fuente | Estado | Observación |
|----------|-------------|-----------|--------|--------|-------------|
| `/api/rrhh/catalogos/puestos` | 200 | 37 | EDARSAHUB SQL | ✅ OK | Con datos reales |
| `/api/rrhh/catalogos/sucursales` | 200 | 8 | EDARSAHUB SQL | ✅ OK | Con datos reales |
| `/api/rrhh/catalogos/tipos-incidencias` | 200 | 0 | EDARSAHUB SQL | ✅ OK | Tabla vacía |
| `/api/rrhh/colaboradores` | 200 | 0 | EDARSAHUB SQL | ✅ OK | Tabla vacía |
| `/api/rrhh/incidencias` | 200 | 0 | EDARSAHUB SQL | ✅ OK | Tabla vacía |
| `/api/rrhh/asistencia` | 200 | 0 | EDARSAHUB SQL | ✅ OK | Tabla vacía |
| `/api/rrhh/nominas/flujo` | 200 | 0 | EDARSAHUB SQL | ✅ OK | Tabla vacía |
| `/api/rrhh/dashboard` | 200 | — | EDARSAHUB SQL | ✅ OK | Dashboard funciona |
| `/api/rrhh/reclutamiento/dashboard` | 200 | — | EDARSAHUB SQL | ✅ OK | Dashboard funciona |
| `/api/nomina/ciclos` | 200 | 0 | MongoDB | ✅ OK | Colección vacía |

---

## Datos Reales Encontrados

| Tabla | Registros | Estado |
|-------|-----------|--------|
| RH_Cat_Puestos | 37 | ✅ Con datos |
| RH_Cat_Sucursales | 8 | ✅ Con datos |
| Resto de tablas RH | 0 | ⚠️ Tablas vacías (dato real) |

---

## Verificación de No Regresión

| Módulo | Estado |
|--------|--------|
| Auth | ✅ OK |
| Compras | ✅ OK |
| Usuarios | ✅ OK |
| Servidores | ✅ OK (EDARSA HUB no visible) |

---

## Dictamen Final

### ✅ RH/NÓMINAS: VALIDACIÓN COMPLETADA

| Criterio | Resultado |
|----------|-----------|
| Falla arquitectura corregida | ✅ |
| Endpoints responden | ✅ |
| No hay 401 inesperados | ✅ |
| EDARSA HUB no aparece como servidor | ✅ |
| Catálogos con datos reales | ✅ |
| Tablas vacías clasificadas correctamente | ✅ |

---

**Reporte de corrección:** `/app/docs/RH_NOMINAS_EDARSAHUB_CONNECTION_01_REPORT.md`  
**Diagnóstico fuente datos:** `/app/docs/AUDITORIA_RH_NOMINAS_FUENTE_DATOS_01.md`

*Validado: 2025-12-27*  
*Corrección aplicada: 2025-12-27*

---

## Tabla de Validación

| Módulo | Pantalla | KPI/Tabla/Filtro | Filtros usados | Endpoint | Valor mostrado | Fuente | Estado | Observación |
|--------|----------|------------------|----------------|----------|---------------:|--------|--------|-------------|
| RH | Catálogo Puestos | Lista puestos | — | `/rrhh/catalogos/puestos` | Error | EDARSA HUB | ⛔ BLOQUEADO | Servidor inactive |
| RH | Catálogo Sucursales | Lista sucursales | — | `/rrhh/catalogos/sucursales` | Error | EDARSA HUB | ⛔ BLOQUEADO | Servidor inactive |
| RH | Tipos Incidencias | Lista tipos | — | `/rrhh/catalogos/tipos-incidencias` | Error | EDARSA HUB | ⛔ BLOQUEADO | Servidor inactive |
| RH | Colaboradores | Lista colaboradores | — | `/rrhh/colaboradores` | Error | EDARSA HUB | ⛔ BLOQUEADO | Servidor inactive |
| RH | Incidencias | Lista incidencias | — | `/rrhh/incidencias` | Error | EDARSA HUB | ⛔ BLOQUEADO | Servidor inactive |
| RH | Asistencia | Registros asistencia | — | `/rrhh/asistencia` | Error | EDARSA HUB | ⛔ BLOQUEADO | Servidor inactive |
| Nóminas | Flujo Nómina | Lista flujos | — | `/rrhh/nominas/flujo` | Error | EDARSA HUB | ⛔ BLOQUEADO | Servidor inactive |
| Nóminas | Dashboard RH | KPIs | — | `/rrhh/dashboard` | Error | EDARSA HUB | ⛔ BLOQUEADO | Servidor inactive |
| Nóminas | Auditoría Fiscal | Reportes | — | `/rrhh/auditoria-fiscal` | Error | EDARSA HUB | ⛔ BLOQUEADO | Servidor inactive |
| Reclutamiento | Vacantes | Lista vacantes | — | `/rrhh/vacantes` | Error | EDARSA HUB | ⛔ BLOQUEADO | Servidor inactive |
| Reclutamiento | Candidatos | Lista candidatos | — | `/rrhh/candidatos` | Error | EDARSA HUB | ⛔ BLOQUEADO | Servidor inactive |
| Reclutamiento | Dashboard | KPIs reclutamiento | — | `/rrhh/reclutamiento/dashboard` | Error | EDARSA HUB | ⛔ BLOQUEADO | Servidor inactive |
| Nóminas | Ciclos Nómina | Lista ciclos | — | `/nomina/ciclos` | 0 ciclos | MongoDB | ⚠️ SIN DATOS REAL | Colección vacía |

---

## Endpoints Probados

| Endpoint | Método | Status HTTP | Respuesta | Estado |
|----------|--------|-------------|-----------|--------|
| `/api/rrhh/catalogos/puestos` | GET | 200 | `"Servidor EDARSA HUB no configurado"` | ⛔ BLOQUEADO |
| `/api/rrhh/catalogos/sucursales` | GET | 200 | `"Servidor EDARSA HUB no configurado"` | ⛔ BLOQUEADO |
| `/api/rrhh/catalogos/tipos-incidencias` | GET | 200 | `"Servidor EDARSA HUB no configurado"` | ⛔ BLOQUEADO |
| `/api/rrhh/colaboradores` | GET | 200 | `"Servidor EDARSA HUB no configurado"` | ⛔ BLOQUEADO |
| `/api/rrhh/incidencias` | GET | 200 | `"Servidor EDARSA HUB no configurado"` | ⛔ BLOQUEADO |
| `/api/rrhh/asistencia` | GET | 200 | `"Servidor EDARSA HUB no configurado"` | ⛔ BLOQUEADO |
| `/api/rrhh/nominas/flujo` | GET | 200 | `"Servidor EDARSA HUB no configurado"` | ⛔ BLOQUEADO |
| `/api/rrhh/dashboard` | GET | 200 | `"Servidor EDARSA HUB no configurado"` | ⛔ BLOQUEADO |
| `/api/rrhh/reclutamiento/dashboard` | GET | 200 | `"Servidor EDARSA HUB no configurado"` | ⛔ BLOQUEADO |
| `/api/nomina/ciclos` | GET | 200 | `{"ciclos": [], "total": 0}` | ⚠️ SIN DATOS |

---

## Validación de Filtros

| Filtro | Endpoint | Estado | Observación |
|--------|----------|--------|-------------|
| Sucursal | — | ⛔ NO VERIFICABLE | Servidor bloqueado |
| Departamento | — | ⛔ NO VERIFICABLE | Servidor bloqueado |
| Puesto | — | ⛔ NO VERIFICABLE | Servidor bloqueado |
| Empleado | — | ⛔ NO VERIFICABLE | Servidor bloqueado |
| Fecha | — | ⛔ NO VERIFICABLE | Servidor bloqueado |
| Estatus | — | ⛔ NO VERIFICABLE | Servidor bloqueado |
| Periodo | `/nomina/ciclos` | ✅ OK | Acepta `actual`, `anterior` |

---

## Validación de Permisos

| Usuario | Endpoint | Resultado | Estado |
|---------|----------|-----------|--------|
| admin@inventario.com | `/rrhh/catalogos/puestos` | Error servidor | ⛔ NO VERIFICABLE |
| admin@inventario.com | `/nomina/ciclos` | `{"ciclos": [], "total": 0}` | ✅ 200 OK |

**Nota:** Los permisos RBAC no pueden verificarse porque el servidor está inactivo.

---

## Colecciones MongoDB

No existen colecciones de RH/Nóminas en MongoDB. Todos los datos residen en EDARSA HUB (SQL Server):

| Colección esperada | Existe | Documentos |
|--------------------|--------|------------|
| `nomina_ciclos` | No | 0 |
| `rh_colaboradores` | No | 0 |
| `rh_incidencias` | No | 0 |

---

## Dictamen

### ⛔ RH/NÓMINAS: BLOQUEADO POR CONFIGURACIÓN

| Criterio | Resultado |
|----------|-----------|
| Carga inicial RH | ⛔ BLOQUEADO |
| Carga inicial Nóminas | ⛔ BLOQUEADO |
| Colaboradores | ⛔ BLOQUEADO |
| Catálogos RH | ⛔ BLOQUEADO |
| Incidencias | ⛔ BLOQUEADO |
| Asistencia | ⛔ BLOQUEADO |
| Reclutamiento | ⛔ BLOQUEADO |
| Flujo Nómina | ⛔ BLOQUEADO |
| KPIs principales | ⛔ NO VERIFICABLE |
| Filtros | ⛔ NO VERIFICABLE |
| Permisos RBAC | ⛔ NO VERIFICABLE |
| No hay 401 inesperados | ✅ Correcto (errores son configuración) |
| No hay listas vacías falsas | ✅ Error es explícito |

---

## Acción Requerida (Usuario)

Para habilitar el módulo RH/Nóminas, el usuario debe:

1. **Activar el servidor EDARSA HUB** en la configuración de servidores:
   - Ir a Configuración > Servidores
   - Buscar "EDARSA HUB"
   - Marcar como `activo = true`

2. **Verificar conectividad** al servidor SQL:
   - Host: `<REDACTED_EDARSAHUB_SQL_HOST>`
   - Database: `EDARSAHUB`

3. **Agregar EDARSA HUB a `allowed_servers`** del usuario administrador si es necesario.

---

## Clasificación de Estados

| Estado | Significado | Cantidad |
|--------|-------------|----------|
| ⛔ BLOQUEADO | Servidor EDARSA HUB inactivo | 12 endpoints |
| ⚠️ SIN DATOS REAL | Endpoint funciona pero sin datos | 1 endpoint |
| ✅ OK | Funciona correctamente | 0 endpoints |

---

*Auditoría: 2025-12-27*  
*Agente: E1*  
*Requiere acción del usuario para desbloquear*
