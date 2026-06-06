# AUDITORÍA TABLEROS KPIs FILTROS - LOG
## AUDITORIA-TABLEROS-KPIS-FILTROS-01

**Iniciado:** 2026-04-27  
**Estado:** REPARACIÓN URGENTE COMPLETADA - AUDITORÍA EN PROGRESO

---

## 2025-12-27 - AUDITORIA-FINANZAS-COMPLETA-01 EJECUTADA

### Estado: ⚠️ **VALIDACIÓN PARCIAL - NO APROBADO - FALTA COBERTURA MPRO**

### Ampliación: Incluye validación MPRO ORIGEN / 130° QUERETARO

### Resumen de Hallazgos por Unidad

| Unidad | Sistema | Submódulo | Estado |
|--------|---------|-----------|--------|
| LA ESTELAR | SoftRestaurant | CxP Resumen | ⚠️ FILTRO NO FUNCIONA |
| CIENFUEGOS | SoftRestaurant | CxP Resumen | ⚠️ FILTRO NO FUNCIONA |
| 130° MERIDA | SoftRestaurant | CxP Resumen | ⚠️ FILTRO NO FUNCIONA |
| ManagementPro | MPRO | CxP Resumen | ⚠️ FILTRO NO FUNCIONA |
| ORIGEN | MPRO | Todos | ❌ FALTA FILTRO SUCURSAL |
| 130° QRO | MPRO | Todos | ❌ FALTA FILTRO SUCURSAL |

### Resumen por Submódulo

| Submódulo | Estado | Cobertura MPRO |
|-----------|--------|----------------|
| Dashboard Finanzas | ❌ BLOQUEADO POR TABLA | MPRO sin diferenciar |
| CxP Resumen | ✅ OK (sin filtros) | MPRO sin filtro funcional |
| CxP Listado | ❌ FALLA SQL | Error encoding |
| Control de Ingresos | ❌ TABLA VACÍA | Aplica SR + MPRO |
| Tesorería / Corte Z | ❌ **MOCK/DEMO** | Mock incluye MPRO_ORIGEN |
| Propinas TPV | ❌ PENDIENTE SYNC | **NO APLICA A MPRO** (MVP) |
| Presupuestos | ❌ BLOQUEADO POR TABLA | MPRO sin diferenciar |
| Conciliación | ❌ NO IMPLEMENTADO | N/A |

### Hallazgo: Propinas TPV No Aplica a MPRO

```json
{
  "fase": "MVP FASE 1 - Solo SoftRestaurant",
  "alcance": ["La Estelar", "Cienfuegos", "130 Mérida"]
}
```

### Hallazgo: Filtros por server_id No Funcionan

Los endpoints aceptan `server_id` pero retornan los mismos resultados para cualquier valor.
No existe filtro por sucursal para diferenciar ORIGEN vs 130° QRO dentro de MPRO.

### Dictamen Final

❌ **FINANZAS NO APROBADO - FALTA COBERTURA MPRO**

Motivos:
1. Datos MOCK en Tesorería
2. Tablas faltantes
3. Filtros por unidad no funcionan
4. Sin filtro por sucursal MPRO
5. Propinas excluye MPRO por diseño

### Documentación
- `/app/docs/AUDITORIA_FINANZAS_COMPLETA_01.md` (actualizado con MPRO)

---


## ENTRADA 2026-04-27 05:00 UTC - INICIO AUDITORÍA

### Contexto
Usuario solicita auditoría completa de todos los tableros, KPIs y filtros de EDARSA HUB.

### Hallazgo inicial

**PROBLEMA CRÍTICO:** El Tablero Ejecutivo muestra todos los KPIs en $0 con mensaje "No hay datos disponibles para el periodo seleccionado".

**Causa raíz identificada:** El archivo `TableroEjecutivo.js` usa `import axios from 'axios'` directamente en lugar del cliente API centralizado (`@/lib/api`) que incluye el interceptor con `memoryToken` para autenticación.

**Evidencia:**
- Endpoint con token (curl): Devuelve datos correctos (3 unidades, ventas $9M+)
- Frontend (axios sin token): Devuelve `{"detail":"Not authenticated"}`

### Archivos afectados

5 archivos usan axios directo:
1. `/app/frontend/src/pages/TableroEjecutivo.js`
2. `/app/frontend/src/pages/Comercial.js`
3. `/app/frontend/src/pages/AutorizacionCompras.js`
4. `/app/frontend/src/pages/ExploradorBD.js`
5. `/app/frontend/src/pages/CatalogoConsultas.js`

### Acción requerida

Migrar estos 5 archivos para usar el cliente API centralizado (`api`) que ya tiene configurado `withCredentials: true` y el interceptor de `memoryToken`.

---

## INVENTARIO COMPLETADO

Se identificaron 25 tableros/módulos para auditar. Ver documento completo:
`/app/docs/AUDITORIA_TABLEROS_KPIS_FILTROS_INVENTARIO.md`

---


## ENTRADA 2026-04-27 05:20 UTC - REPARACIÓN URGENTE COMPLETADA

### Problema solucionado
5 archivos usaban `axios` directo sin autenticación. Migrados a cliente API centralizado (`@/lib/api`).

### Archivos reparados
1. TableroEjecutivo.js (4 llamadas)
2. Comercial.js (9 llamadas)
3. AutorizacionCompras.js (4 llamadas)
4. ExploradorBD.js (10 llamadas)
5. CatalogoConsultas.js (1 llamada)

### Evidencia de éxito
**Tablero Ejecutivo ahora muestra:**
- Ventas: $9.29M ✅
- PAX: 9,453 ✅
- Cheques: 3,327 ✅
- Proyección: $11.05M ✅
- 3 Unidades conectadas ✅

### Validaciones completadas
- [x] npm run build exitoso
- [x] Login funciona
- [x] Tablero Ejecutivo carga datos reales
- [x] Comercial carga correctamente
- [x] No hay errores 403 por falta de auth

### Próximos pasos
Continuar con auditoría completa de los 25 módulos identificados.

## ENTRADA 2026-04-27 14:25 UTC - AUDITORÍA CONTINUADA

### Problemas encontrados y corregidos

**1. Finanzas.js - Rutas /api/api/ duplicadas:**
- Rutas corregidas: 8 endpoints

**2. useCentroControlData.js - fetch() nativo:**
- 9 funciones migradas a api centralizado
- Centro de Control ahora muestra: 6/6 módulos, 4/4 fuentes, Score 70.2

**3. MisTareas, Nominas, RecursosHumanos - Rutas duplicadas:**
- 5 rutas corregidas de /api/xxx a /xxx

### Módulos verificados OK
- Tablero Ejecutivo: $9.29M ventas ✅
- Comercial: Carga OK ✅
- Finanzas: Carga OK (sin presupuestos configurados) ✅
- Compras: Carga OK ✅
- Recursos Humanos: Carga OK (0 colaboradores) ✅
- Operaciones: Carga OK ✅
- Centro de Control: 6/6 módulos, 4/4 fuentes ✅

### Pendientes de auditoría
- Proveedores / Portal
- Usuarios / Roles / Permisos
- Scheduler
- Configuración

---


---

---

## 2025-12-27 - P0-AUTH-COOKIE-FRONTEND-01

### Hallazgo Crítico
Tablero Ejecutivo mostraba $0 por problema de autenticación.

### Causa Raíz
Proxy de Kubernetes/Cloudflare sobrescribe headers CORS con `*`, invalidando cookies con credentials.

### Solución
1. memoryToken funciona correctamente en navegación SPA
2. Corregido manejo de errores para no mostrar $0 falso
3. Si hay error de conexión, muestra mensaje claro

### Resultado
- Tablero Ejecutivo muestra $14.35M ventas (datos reales)
- 5 unidades conectadas
- Navegación SPA funciona correctamente

### Documentación
- `/app/docs/P0_AUTH_COOKIE_FRONTEND_01_REPORT.md`

---

---

## 2025-12-27 - AUDITORIA TABLERO EJECUTIVO COMPLETADA

### Escenarios Validados: 13

| # | Escenario | Estado |
|---|-----------|--------|
| 1 | Mes Actual (Abril 2026) | ✅ OK |
| 2 | Mes Anterior (Marzo 2026) | ✅ OK |
| 3 | Multi-Mes 2 meses | ✅ OK |
| 4 | Multi-Mes 3 meses | ✅ OK |
| 5 | Acumulado Anual | ✅ OK |
| 6 | Ventas del Día | ✅ OK |
| 7 | Día Histórico | ⚠️ NO DATA |
| 8 | Comparativo Año Ant | ✅ OK |
| 9 | Una Unidad | ⚠️ NO DATA |
| 10 | ManagementPro | ⚠️ NO DATA |
| 11 | SoftRestaurant | ✅ OK (caché) |
| 12 | Filtro Cambia KPIs | ✅ OK |
| 13 | Error Auth | ✅ OK |

### KPIs Verificados
- Ventas Consolidadas: $9.62M ✅
- PAX Total: 9,663 ✅
- Cheques: 3,396 ✅
- Proyección: $11.10M ✅
- Comparativos: Funcionando ✅

### Hallazgos
1. Caché de Cloudflare puede mostrar datos desactualizados
2. Servidores SQL externos en modo FALLBACK (CONFIG-SECURITY-01)
3. ManagementPro sin datos (verificar configuración)

### Dictamen
**TABLERO EJECUTIVO: APROBADO CON OBSERVACIONES**

---

---

## 2025-12-27 - CORRECCIÓN DIAGNÓSTICO MPRO

### Hallazgo Corregido
ManagementPro **SÍ tiene datos históricos completos**. El error inicial fue por parámetros incorrectos en curl.

### Validación MPRO Completa

| Escenario | Resultado | Estado |
|-----------|-----------|--------|
| Mes actual (Abril) | $4,852,752 | ✅ OK |
| Multi-mes (Mar-Abr) | $11,110,966 | ✅ OK |
| Acumulado anual | $23,437,634 | ✅ OK |
| Ventas día LIVE | $3,039 | ✅ OK |
| Comparativo año ant | +16.7% | ✅ OK |

### Sucursales MPRO Identificadas
- **ORIGEN** = código 0023 ✅
- **QUERETARO** = código 0021 ✅

### Dictamen Actualizado
**TABLERO EJECUTIVO: APROBADO CON OBSERVACIONES MENORES**

### Observaciones Menores
1. SoftRestaurant en FALLBACK (CONFIG-SECURITY-01)
2. Caché de Cloudflare
3. Nomenclatura inconsistente (typos)

---

---

## 2025-12-27 - DASHBOARD COMERCIAL

### Estado: VALIDACIÓN PARCIAL — BLOQUEADO POR CONFIG-SECURITY-01

### Hallazgos

| Servidor | Dashboard Individual | Tablero Ejecutivo | Motivo |
|----------|---------------------|-------------------|--------|
| LA ESTELAR | ✅ OK | ✅ OK | Caché funciona |
| CIENFUEGOS | ⚠️ OFFLINE | ✅ OK | Marcado offline |
| ManagmentPro | ❌ NO_DATA | ✅ OK | Sin fallback a caché |

### Discrepancia MPRO

- **Tablero Ejecutivo:** Muestra $4.85M (usa caché cuando SQL falla)
- **Dashboard Individual:** Muestra $0 (NO tiene fallback a caché)

### Causa Raíz
CONFIG-SECURITY-01: Falta SERVER_SECRET_KEY para descifrar passwords SQL.
El dashboard individual de MPRO no tiene fallback a caché implementado.

### Acción Requerida
1. Resolver CONFIG-SECURITY-01
2. O implementar fallback a caché para MPRO en dashboard individual

---


## 2025-12-27 - AUDITORIA-COMPRAS-DASHBOARD-VS-ANALISIS-01 COMPLETADA

### Estado: ✅ CORRECCIÓN APLICADA

### Problema
Dashboard de Compras mostraba $0/$196K mientras Análisis mostraba $11M+ para mismo servidor/período.

### Causa Raíz
Filtro de fechas incompatible:
- Dashboard usaba: `fechaaplicacion >= 'YYYY-MM-DD' AND fechaaplicacion < 'YYYY-MM-DD'`
- Análisis usaba: `MONTH(fechaaplicacion) = X AND YEAR(fechaaplicacion) = Y`

El campo `fechaaplicacion` en SoftRestaurant no responde correctamente a rangos de fecha.

### Corrección
Se modificó `/app/backend/server.py` función `obtener_dashboard_compras()` para usar `MONTH()/YEAR()`.

### Validación

| Servidor | Dashboard ANTES | Dashboard DESPUÉS | Análisis | Estado |
|----------|----------------:|------------------:|---------:|--------|
| LA ESTELAR (Abr) | $0 | $2,340,813 | $2,340,813 | ✅ MATCH |
| 130° MERIDA (Abr) | $0 | $2,597,599 | $2,592,739 | ✅ OK |

### Observación Residual
Diferencia menor en 130° MERIDA ($4,860 = 0.19%) documentada como diferencia residual.
Análisis trunca a TOP 100 proveedores mientras Dashboard suma todos.

---

## 2025-12-27 - AUDITORIA-COMPRAS-AUTORIZACION-01 COMPLETADA

### Estado: ✅ VALIDACIÓN COMPLETA

### Pantallas Validadas

| Pantalla | Registros | Estado |
|----------|----------:|--------|
| Inventarios Físicos (LA ESTELAR) | 181 | ✅ OK |
| Inventarios Físicos (CIENFUEGOS) | 2,421 | ✅ OK |
| Inventarios Físicos (130° MERIDA) | 3,797 | ✅ OK |
| Pedidos Vigentes (LA ESTELAR) | 23 | ✅ OK |
| Pedidos Vigentes (CIENFUEGOS) | 53 | ✅ OK |
| Pedidos Vigentes (130° MERIDA) | 43 | ✅ OK |

### Filtros Validados
- ✅ Servidor (obligatorio)
- ✅ Sucursal (requerido para Dashboard)
- ✅ Mes/Año (multiselección OK)
- ✅ Proveedor (en Análisis)
- ✅ Almacén (RBAC aplicado)
- ✅ Estatus (filtra PXA)

### Permisos
- ✅ SuperAdministrador: acceso total
- ✅ Usuario: acceso según `allowed_servers`

### Criterios Cumplidos
- ✅ No hay $0 falso
- ✅ Filtros funcionando
- ✅ Totales vs filas consistentes
- ✅ Sin datos fuera de alcance


## 2025-12-27 - AUDITORIA-RH-NOMINAS-01

### Estado: ⛔ BLOQUEADO POR CONFIGURACIÓN

### Hallazgo Crítico
Todos los endpoints de RH/Nóminas (`/api/rrhh/*`) retornan error "Servidor EDARSA HUB no configurado".

### Causa Raíz
El servidor `EDARSA HUB` está marcado como `active: False` en MongoDB:
```
ID: bea40259-35f1-4693-bda2-d2d10e13e56a
Host: <REDACTED_EDARSAHUB_SQL_HOST>
Database: EDARSAHUB
active: FALSE  ← PROBLEMA
```

### Endpoints Afectados (12 total)
- `/rrhh/catalogos/puestos`
- `/rrhh/catalogos/sucursales`
- `/rrhh/catalogos/tipos-incidencias`
- `/rrhh/colaboradores`
- `/rrhh/incidencias`
- `/rrhh/asistencia`
- `/rrhh/nominas/flujo`
- `/rrhh/dashboard`
- `/rrhh/auditoria-fiscal`
- `/rrhh/vacantes`
- `/rrhh/candidatos`
- `/rrhh/reclutamiento/dashboard`

### Endpoint Alternativo OK
- `/nomina/ciclos` - Funciona (MongoDB) pero sin datos (colección vacía)

### Acción Requerida (Usuario)
1. Activar servidor EDARSA HUB en Configuración > Servidores

## 2025-12-27 - AUDITORIA-RH-NOMINAS-FUENTE-DATOS-01 (SUBFASE A)

### Estado: ⚠️ FALLA DE ARQUITECTURA DETECTADA

### Hallazgo Crítico
El módulo RH/Nóminas usa un patrón de conexión **diferente e incorrecto** comparado con otros módulos internos.

### Comparación

| Componente | Método | Depende de active | Estado |
|------------|--------|-------------------|--------|
| `server_registry.py` | `EDARSAHUB_CONFIG` (directo) | NO | ✅ OK |
| `modules/rh/repository.py` | MongoDB `servers` | SÍ | ⛔ FALLA |

### Evidencia
- `server_registry.py` líneas 30-37: usa variables de entorno directas
- `modules/rh/repository.py` líneas 124-129: busca en MongoDB con `active: True`

### Dictamen
**FALLA DE ARQUITECTURA** — RH no debería depender de un registro de servidor externo para acceder a EDARSAHUB interno.

### Opciones de Corrección
A) Refactorizar RH para usar `EDARSAHUB_CONFIG` (RECOMENDADA)
B) Activar servidor con protecciones (NO RECOMENDADA)
C) Documentar como limitación

### Documentación
- `/app/docs/AUDITORIA_RH_NOMINAS_FUENTE_DATOS_01.md`

### Acción Requerida
Decisión del usuario sobre cómo proceder antes de cerrar auditoría.

---

## 2025-12-27 - RH-NOMINAS-EDARSAHUB-CONNECTION-01 COMPLETADA

### Estado: ✅ CORRECCIÓN EXITOSA

### Cambio Realizado
Se modificó `/app/backend/modules/rh/repository.py` para usar conexión directa a EDARSAHUB vía `EDARSAHUB_CONFIG` (variables de entorno), eliminando la dependencia de MongoDB `servers` con `active=True`.

### Endpoints Validados Post-Corrección

| Endpoint | Registros | Estado |
|----------|-----------|--------|
| `/rrhh/catalogos/puestos` | 37 | ✅ OK |
| `/rrhh/catalogos/sucursales` | 8 | ✅ OK |
| `/rrhh/catalogos/tipos-incidencias` | 0 | ✅ OK (vacío) |
| `/rrhh/colaboradores` | 0 | ✅ OK (vacío) |
| `/rrhh/incidencias` | 0 | ✅ OK (vacío) |
| `/rrhh/asistencia` | 0 | ✅ OK (vacío) |
| `/rrhh/nominas/flujo` | 0 | ✅ OK (vacío) |
| `/rrhh/dashboard` | — | ✅ OK |
| `/rrhh/reclutamiento/dashboard` | — | ✅ OK |

### Verificación No Regresión
- ✅ Auth funciona
- ✅ Compras funciona ($2.34M)
- ✅ Usuarios funciona
- ✅ EDARSA HUB no aparece como servidor seleccionable

### Documentación
- `/app/docs/RH_NOMINAS_EDARSAHUB_CONNECTION_01_REPORT.md`

---

## 2025-12-27 - AUDITORIA-RH-NOMINAS-02 COMPLETADA

### Estado: ✅ VALIDACIÓN FUNCIONAL COMPLETADA

### Bug Corregido: POOL_POISON_FIX_01
Se detectó y corrigió un bug crítico donde errores de query (tabla no existe) envenenaban el pool de conexiones, marcando el servidor como offline y causando que queries posteriores retornaran vacío.

**Archivo corregido:** `/app/backend/core/db.py`  
**Cambio:** Errores de query ya NO marcan el servidor como offline.

### Resultados de Validación

| Área | Registros | Estado |
|------|-----------|--------|
| Puestos | 37 | ✅ OK |
| Sucursales | 8 | ✅ OK |
| Colaboradores | 510 | ✅ OK |
| Tipos Incidencias | 0 | ⛔ TABLA FALTANTE |
| Incidencias | 0 | ⚠️ TABLA VACÍA |
| Asistencia | 0 | ⚠️ TABLA VACÍA |
| Flujo Nómina | 0 | ⚠️ TABLA VACÍA |

### Filtros Validados
- ✅ Sucursal ID (200 de 510)
- ✅ Búsqueda texto (19 resultados para "JUAN")
- ✅ Paginación

### Documentación
- `/app/docs/AUDITORIA_RH_NOMINAS_02.md`

---

## 2025-12-27 - POOL_POISON_FIX_01 DOCUMENTADO

### Estado: ✅ CORREGIDO Y VALIDADO

### Causa Raíz
Errores de query (tabla no existe) marcaban todo el servidor como offline en `core/db.py`, causando que queries posteriores retornaran vacío.

### Corrección
Errores de tipo QUERY ya NO marcan el servidor offline. Solo errores de AUTH/TIMEOUT/NETWORK marcan offline.

### Validación No Regresión
| Módulo | Estado |
|--------|--------|
| Auth | ✅ OK |
| Comercial | ✅ OK |
| Compras | ✅ OK ($2.34M) |
| Finanzas | ✅ OK |
| RH | ✅ OK (510) |
| Usuarios | ✅ OK |

### Test de Pool
- Error "tabla no existe" → Pool NO envenenado ✅
- Servidor EDARSAHUB → Permanece ONLINE ✅

### Documentación
- `/app/docs/POOL_POISON_FIX_01_REPORT.md`

---


## 2025-12-27 - AUDITORIA-OPERACIONES-INVENTARIOS-01 COMPLETADA

### Estado: ✅ VALIDACIÓN COMPLETADA

### Endpoints Validados

| Área | Registros | Fuente | Estado |
|------|-----------|--------|--------|
| Inventarios servidor | 2 | SQL Server | ✅ OK |
| Inventarios físicos | 181 | SQL Server | ✅ OK |
| Informes auditoría | 35 | MongoDB | ✅ OK |
| Workflows | 18 | MongoDB | ✅ OK |
| Tareas | 18 | MongoDB | ✅ OK |
| Configuración | — | MongoDB | ✅ OK |

### Colecciones MongoDB
- workflow_inventarios: 18 docs
- tareas_inventario: 18 docs
- auditoria_compras_bitacora: 969 docs
- detalle_diferencias: 1960 docs

### Endpoints No Disponibles
- `/v2/dashboard` → Not Found
- `/v2/sla` → Not Found
- `/v2/automatizaciones-compras` → Not Found

### Documentación
- `/app/docs/AUDITORIA_OPERACIONES_INVENTARIOS_01.md`

---


## 2025-12-27 - AUDITORIA-PROVEEDORES-PORTAL-01 COMPLETADA

### Estado: ✅ AUDITORÍA COMPLETADA - ✅ VULNERABILIDAD P0 CORREGIDA

### Arquitectura del Portal

El Portal de Proveedores implementa **DOS sistemas de autenticación separados**:

| Tipo | Método Auth | Cookie | Alcance |
|------|-------------|--------|---------|
| Usuario Interno EDARSA | Email + Password | `edarsa_access_token` | Endpoints `/admin/*` |
| Proveedor Externo | RFC + Password | `edarsa_portal_access_token` | Endpoints de proveedor |

### Corrección Aplicada: P0-PORTAL-PROVEEDORES-AUTH-01

Se implementó helper `require_portal_admin()` que:
1. Verifica token JWT válido
2. Rechaza tokens de proveedor externo (type=portal_supplier) → 401
3. Valida rol SuperAdministrador o Administrador → 403 si no cumple
4. Permite acceso a admin autorizado → 200

### Resultados de Validación Post-Fix

| Escenario | Código | Estado |
|-----------|--------|--------|
| Sin token | 403 | ✅ RECHAZADO |
| Token proveedor | 401 | ✅ RECHAZADO |
| Usuario sin permiso | 403 | ✅ RECHAZADO |
| Admin autorizado | 200 | ✅ PERMITIDO |
| Portal proveedor | 200 | ✅ SIN REGRESIÓN |
| Auth interna | 200 | ✅ SIN REGRESIÓN |

### Endpoints Protegidos

| # | Endpoint | Estado |
|---|----------|--------|
| 1 | GET /admin/all-suppliers | ✅ PROTEGIDO |
| 2 | GET /admin/pending-suppliers | ✅ PROTEGIDO |
| 3 | POST /admin/approve-supplier | ✅ PROTEGIDO |
| 4 | POST /admin/reset-password | ✅ PROTEGIDO |
| 5 | GET /admin/supplier/{id} | ✅ PROTEGIDO |
| 6 | GET /admin/invoices | ✅ PROTEGIDO |
| 7 | DELETE /admin/supplier/{id} | ✅ PROTEGIDO |
| 8 | GET /servers | ✅ PROTEGIDO |

### Documentación
- `/app/docs/AUDITORIA_PROVEEDORES_PORTAL_01.md`
- `/app/docs/P0_PORTAL_PROVEEDORES_AUTH_01_REPORT.md`

---






2. Verificar conectividad al SQL Server
3. Agregar a allowed_servers del usuario si es necesario

### Documentación
- `/app/docs/AUDITORIA_RH_NOMINAS_01.md`

---

### Documentación
- `/app/docs/AUDITORIA_COMPRAS_AUTORIZACION_01.md`

---

---

## 2025-12-28: Diagnóstico Sucursales MPRO en Finanzas

### Contexto
Usuario reportó que las sucursales MPRO (ORIGEN y 130° QRO) no aparecen en Finanzas.

### Diagnóstico Realizado

1. **Verificación EDARSAHUB**: Sucursales ORIGEN (0023) y 130° QRO (0021) existen y están activas
2. **Verificación CENTRAL2020**: Hay 1,597 facturas CxP con ~$20.5M de saldo para estas sucursales
3. **Verificación Frontend**: Endpoint `/api/unidades-negocio` devuelve correctamente las 5 unidades (incluyendo MPRO)

### Causa Identificada

El módulo CxP usa lógica de **fallback** en lugar de **combinación**:
```python
# Lógica actual (incorrecta)
if softrest_repo.get_datos():
    return datos_sr  # MPRO nunca se consulta
else:
    return mpro_repo.get_datos()  # Solo si SR falla
```

### Archivos Afectados
- `/app/backend/modules/finanzas/cuentas_por_pagar.py`

### Documentos Generados
- `/app/docs/DIAGNOSTICO_SUCURSALES_MPRO_FINANZAS.md`

### Estado
**PENDIENTE CORRECCIÓN**: Cambiar lógica de fallback a combinación


---

## 2025-12-28: FINANZAS-CXP-MPRO-COMBINE-01 - COMPLETADO

### Resumen
Corrección implementada para combinar SR + MPRO en CxP (no fallback).

### Validaciones exitosas:
- ORIGEN: 1,073 facturas, $11,501,659.82 ✅
- 130° QRO: 524 facturas, $8,984,825.24 ✅
- Total combinado: 2,850 facturas, $48.8M ✅

### Archivos modificados:
- `/app/backend/modules/finanzas/cuentas_por_pagar.py`
- `/app/backend/modules/finanzas/repository_mpro.py`

### Documentos generados:
- `/app/docs/FINANZAS_CXP_MPRO_COMBINE_01_REPORT.md`


---

## 2025-12-28: Seguridad Credenciales MPRO - Documentado

### Verificación de seguridad para FINANZAS-CXP-MPRO-COMBINE-01

| Punto | Resultado |
|-------|-----------|
| Fuente credenciales | MongoDB (db.servers) |
| Password en logs | NO |
| Connection string en logs | NO |
| Subprocess expone secretos | SÍ (argumentos CLI) - riesgo MEDIO |
| Descifrado | core/secret_manager.py + SERVER_SECRET_KEY |

### Riesgo aceptado
Password visible temporalmente en argumentos de proceso.
Mitigación: subprocess corto + Kubernetes aislado.

### Recomendación
Migrar a stdin para credenciales en futuras versiones.


---

## 2025-12-28: FINANZAS-CXP-MPRO-CREDENTIALS-SECURITY-01 - COMPLETADO

### Corrección de seguridad aplicada

| Punto | Antes | Después |
|-------|-------|---------|
| Fuente credenciales | MongoDB | EDARSAHUB SQL (server_registry.py) |
| config_origin | N/A | EDARSAHUB_SQL |
| Password en argv | SÍ (riesgo) | NO (usa stdin) |
| Worker | sql_query_worker.py | sql_query_worker_secure.py |

### Archivos modificados
- `/app/backend/modules/finanzas/repository_mpro.py`
- `/app/backend/modules/finanzas/sql_subprocess_helper.py`
- `/app/backend/modules/finanzas/sql_query_worker_secure.py` (NUEVO)

### CxP sigue funcionando
- ORIGEN: 1,073 facturas, $11,501,659.82 ✅
- 130 QRO: 524 facturas, $8,984,825.24 ✅
- Todas: 2,851 facturas, $48,897,056.58 ✅

### Reporte
`/app/docs/FINANZAS_CXP_MPRO_CREDENTIALS_SECURITY_01_REPORT.md`


---

## 2025-12-28: P0-COMERCIAL-PRECIOS-CONSTANTES-NO-DATA-01 - COMPLETADO

### Problema
Precios Constantes sin datos podía romper tabs/menú de Comercial.

### Corrección
- Agregado estado "sin datos" con mensaje claro
- Verificación `data && data.kpis && (...)` antes de renderizar KPIs
- Reset de estado en caso de error

### Archivos modificados
- `/app/frontend/src/pages/Comercial.js`

### Validaciones
- Build exitoso ✅
- Backend responde correctamente con/sin datos ✅

### Reporte
`/app/docs/P0_COMERCIAL_PRECIOS_CONSTANTES_NO_DATA_01_REPORT.md`


---

## 2025-12-28: P0-COMERCIAL-PRECIOS-CONSTANTES-NO-DATA-01 - EVIDENCIA CASO ORIGINAL

### Caso original validado
- Unidad: ORIGEN
- Comparativo: Feb 2025 vs Feb 2026
- Resultado: $2,398,128.02, 443 productos (HAY DATOS)

### Validación navegación tabs
| Tab | Estado |
|-----|--------|
| Dashboard | ✅ Funciona (estado independiente) |
| Reportes Pax | ✅ Funciona (estado independiente) |
| Ticket Perfecto | ✅ Funciona (estado independiente) |
| Metas | ✅ Funciona (estado independiente) |
| Precios Const. | ✅ Funciona (reset con setData(null)) |

### Justificación técnica
La navegación entre tabs funciona porque:
1. useState local por componente
2. catch hace setData(null) evitando estado corrupto
3. Condición robusta `data && data.kpis && (...)` protege render

