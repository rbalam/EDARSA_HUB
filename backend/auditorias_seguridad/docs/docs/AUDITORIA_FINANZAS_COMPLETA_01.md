# AUDITORIA_FINANZAS_COMPLETA_01

**Fecha**: 2025-12-27  
**Módulo**: Finanzas y Control Presupuestal  
**Alcance**: AUDITORIA-TABLEROS-KPIS-FILTROS-01 / FINANZAS COMPLETA  
**Ampliación**: Incluye validación MPRO ORIGEN / 130° QUERETARO  
**Dictamen Final**: ⚠️ **VALIDACIÓN PARCIAL - NO APROBADO - FALTA COBERTURA MPRO**

---

## 1. RESUMEN EJECUTIVO

El módulo de Finanzas presenta múltiples bloqueadores que impiden su aprobación:

| Categoría | Cantidad | Impacto |
|-----------|----------|---------|
| ✅ Submódulos OK | 1 | Bajo |
| ⚠️ Parcialmente funcionales | 1 | Medio |
| ❌ Bloqueados por tabla | 2 | Alto |
| ❌ Usando datos MOCK/DEMO | 1 | **CRÍTICO** |
| ❌ Pendiente sincronización | 1 | Alto |
| ❌ Falta cobertura MPRO | 1 | Alto |
| ❌ Conexión SQL fallando | 3 | **CRÍTICO** |

### Unidades Auditadas

| # | Unidad | Sistema | Server ID | Sucursales | Estado Cobertura |
|---|--------|---------|-----------|------------|------------------|
| 1 | LA ESTELAR | SoftRestaurant | a5ff0e25-... | 1 | ⚠️ SQL FALLANDO |
| 2 | CIENFUEGOS | SoftRestaurant | 6d053c22-... | 1 | ⚠️ SQL FALLANDO |
| 3 | 130° MERIDA | SoftRestaurant | a5547321-... | 1 | ⚠️ SQL FALLANDO |
| 4 | ManagementPro | MPRO | 1b230a06-... | 2 (ORIGEN, 130° QRO) | ❌ FALTA COBERTURA |

---

## 2. DIAGNÓSTICO POR SUBMÓDULO Y UNIDAD

### 2.1 Dashboard Finanzas

| Submódulo | Unidad/Sucursal | Sistema | Aplica | Endpoint | Filtros | Resultado | Fuente | Estado | Observación |
|-----------|-----------------|---------|--------|----------|---------|----------:|--------|--------|-------------|
| Dashboard | TODAS | - | Sí | /finanzas/dashboard | anio=2026, mes=4 | $0 | N/A | **BLOQUEADO POR TABLA** | Finanzas_Presupuestos no existe |
| Dashboard | LA ESTELAR | SR | Sí | /finanzas/dashboard | server_id=... | $0 | N/A | **BLOQUEADO POR TABLA** | |
| Dashboard | CIENFUEGOS | SR | Sí | /finanzas/dashboard | server_id=... | $0 | N/A | **BLOQUEADO POR TABLA** | |
| Dashboard | 130° MERIDA | SR | Sí | /finanzas/dashboard | server_id=... | $0 | N/A | **BLOQUEADO POR TABLA** | |
| Dashboard | ManagementPro | MPRO | Sí | /finanzas/dashboard | server_id=... | $0 | N/A | **BLOQUEADO POR TABLA** | MPRO no diferenciado |
| Dashboard | ORIGEN | MPRO | Sí | N/A | N/A | N/A | N/A | **FALTA FILTRO SUCURSAL** | Sin soporte sucursal MPRO |
| Dashboard | 130° QRO | MPRO | Sí | N/A | N/A | N/A | N/A | **FALTA FILTRO SUCURSAL** | Sin soporte sucursal MPRO |

**Estado**: ❌ **BLOQUEADO POR TABLA** + **FALTA COBERTURA MPRO SUCURSALES**

---

### 2.2 Cuentas por Pagar

| Submódulo | Unidad/Sucursal | Sistema | Aplica | Endpoint | Filtros | Resultado | Fuente | Estado | Observación |
|-----------|-----------------|---------|--------|----------|---------|----------:|--------|--------|-------------|
| CxP Resumen | TODAS | - | Sí | /cuentas-por-pagar/resumen | ninguno | $11.6M, 634 fact | EDARSAHUB | ✅ OK | Datos reales consolidados |
| CxP Resumen | LA ESTELAR | SR | Sí | /cuentas-por-pagar/resumen | server_id=... | $0 | N/A | **FALLA FILTRO** | Filtro no funciona |
| CxP Resumen | CIENFUEGOS | SR | Sí | /cuentas-por-pagar/resumen | server_id=... | Error | N/A | **FALLA FILTRO** | |
| CxP Resumen | 130° MERIDA | SR | Sí | /cuentas-por-pagar/resumen | server_id=... | $0 | N/A | **FALLA FILTRO** | |
| CxP Resumen | ManagementPro | MPRO | Sí | /cuentas-por-pagar/resumen | server_id=... | $0 | N/A | **FALLA FILTRO** | |
| CxP Resumen | ORIGEN | MPRO | Sí | N/A | N/A | N/A | N/A | **FALTA FILTRO SUCURSAL** | |
| CxP Resumen | 130° QRO | MPRO | Sí | N/A | N/A | N/A | N/A | **FALTA FILTRO SUCURSAL** | |
| CxP Listado | TODAS | - | Sí | /cuentas-por-pagar | ninguno | 0 fact | SQL FALLA | **FALLA SQL** | Error encoding |
| CxP Proveedores | TODAS | - | Sí | /cuentas-por-pagar/proveedores | ninguno | 281 | EDARSAHUB | ✅ OK | |

**Estado**: ⚠️ **PARCIALMENTE FUNCIONAL** - Resumen OK sin filtro, filtros por unidad no funcionan, MPRO sin cobertura de sucursales

---

### 2.3 Control de Ingresos

| Submódulo | Unidad/Sucursal | Sistema | Aplica | Endpoint | Filtros | Resultado | Fuente | Estado | Observación |
|-----------|-----------------|---------|--------|----------|---------|----------:|--------|--------|-------------|
| Cortes Caja | TODAS | - | Sí | /ingresos/cortes-caja | ninguno | 0 | MongoDB | **TABLA VACÍA REAL** | Sin sincronización |
| Cortes Caja | ManagementPro | MPRO | Sí | /ingresos/cortes-caja | server_id=... | 0 | MongoDB | **TABLA VACÍA REAL** | |
| Por Depositar | TODAS | - | Sí | /ingresos/saldos-por-depositar | ninguno | $0 | MongoDB | **TABLA VACÍA REAL** | |
| Comisiones | TODAS | - | Sí | /ingresos/resumen-comisiones | ninguno | $0 | MongoDB | **TABLA VACÍA REAL** | |

**Estado**: ❌ **TABLA VACÍA REAL** - Aplica a SR y MPRO pero sin datos sincronizados

---

### 2.4 Tesorería / Corte Z

| Submódulo | Unidad/Sucursal | Sistema | Aplica | Endpoint | Filtros | Resultado | Fuente | Estado | Observación |
|-----------|-----------------|---------|--------|----------|---------|----------:|--------|--------|-------------|
| Corte Z | TODAS | - | Sí | /tesoreria/cortes-z | ninguno | 4 cortes | **DEMO/MOCK** | ❌ **MOCK/DEMO** | DATOS FALSOS |
| Corte Z | LA ESTELAR | SR | Sí | /tesoreria/cortes-z | server_id=... | 4 cortes | **DEMO/MOCK** | ❌ **FILTRO NO FUNCIONA** | Ignora filtro |
| Corte Z | ManagementPro | MPRO | Sí | /tesoreria/cortes-z | server_id=... | 4 cortes | **DEMO/MOCK** | ❌ **FILTRO NO FUNCIONA** | Ignora filtro |
| Corte Z | ORIGEN | MPRO | Sí | N/A | N/A | N/A | N/A | **NO VERIFICABLE** | Mock incluye MPRO_ORIGEN |
| Corte Z | 130° QRO | MPRO | Sí | N/A | N/A | N/A | N/A | **NO VERIFICABLE** | Sin datos mock |

**Sucursales en datos DEMO**:
- CIENFUEGOS
- LA_ESTELAR  
- MPRO_ORIGEN (incluido en mock pero datos falsos)

**Estado**: ❌ **MOCK/DEMO - NO APROBADO** - Los filtros no funcionan, datos son inventados

---

### 2.5 Propinas TPV

| Submódulo | Unidad/Sucursal | Sistema | Aplica | Endpoint | Filtros | Resultado | Fuente | Estado | Observación |
|-----------|-----------------|---------|--------|----------|---------|----------:|--------|--------|-------------|
| Propinas | TODAS | - | Sí* | /finanzas/propinas | ninguno | 0 | MongoDB | **PENDIENTE SYNC** | |
| Propinas | LA ESTELAR | SR | Sí | /finanzas/propinas | server_id=... | 0 | MongoDB | **PENDIENTE SYNC** | |
| Propinas | CIENFUEGOS | SR | Sí | /finanzas/propinas | server_id=... | 0 | MongoDB | **PENDIENTE SYNC** | |
| Propinas | 130° MERIDA | SR | Sí | /finanzas/propinas | server_id=... | 0 | MongoDB | **PENDIENTE SYNC** | |
| Propinas | ManagementPro | MPRO | **NO** | N/A | N/A | N/A | N/A | **NO APLICA A MPRO** | Ver alcance |
| Propinas | ORIGEN | MPRO | **NO** | N/A | N/A | N/A | N/A | **NO APLICA A MPRO** | |
| Propinas | 130° QRO | MPRO | **NO** | N/A | N/A | N/A | N/A | **NO APLICA A MPRO** | |

**Alcance documentado del módulo** (health check):
```json
{
  "fase": "MVP FASE 1 - Solo SoftRestaurant",
  "alcance": ["La Estelar", "Cienfuegos", "130 Mérida"]
}
```

**Estado**: ❌ **PENDIENTE SINCRONIZACIÓN** + **NO APLICA A MPRO** (por diseño MVP)

---

### 2.6 Presupuestos

| Submódulo | Unidad/Sucursal | Sistema | Aplica | Endpoint | Filtros | Resultado | Fuente | Estado | Observación |
|-----------|-----------------|---------|--------|----------|---------|----------:|--------|--------|-------------|
| Presupuestos | TODAS | - | Sí | /finanzas/presupuestos | anio=2026 | 0 | N/A | **BLOQUEADO POR TABLA** | |
| Presupuestos | ManagementPro | MPRO | Sí | /finanzas/presupuestos | server_id=... | 0 | N/A | **BLOQUEADO POR TABLA** | |
| Presupuestos | ORIGEN | MPRO | Sí | N/A | N/A | N/A | N/A | **BLOQUEADO POR TABLA** | |
| Presupuestos | 130° QRO | MPRO | Sí | N/A | N/A | N/A | N/A | **BLOQUEADO POR TABLA** | |

**Mensaje del endpoint**: "Tabla Finanzas_Presupuestos pendiente de creación"

**Estado**: ❌ **BLOQUEADO POR TABLA**

---

### 2.7 Conciliación / Comisiones

| Submódulo | Unidad/Sucursal | Sistema | Aplica | Endpoint | Filtros | Resultado | Fuente | Estado | Observación |
|-----------|-----------------|---------|--------|----------|---------|----------:|--------|--------|-------------|
| Conciliación | TODAS | - | ? | N/A | N/A | N/A | N/A | **NO IMPLEMENTADO** | |

**Estado**: ❌ **NO IMPLEMENTADO**

---

## 3. ANÁLISIS DE COBERTURA MPRO

### 3.1 Resumen de Cobertura por Submódulo

| Submódulo | ¿Aplica a MPRO? | ¿Implementado? | ¿Filtro funciona? | Observación |
|-----------|-----------------|----------------|-------------------|-------------|
| Dashboard | Sí | Sí | **NO** | Filtro server_id no diferencia MPRO |
| CxP | Sí | Sí | **NO** | Filtro retorna $0 para MPRO |
| Control Ingresos | Sí | Sí | N/A | Tabla vacía, aplica a ambos |
| Tesorería | Sí | **MOCK** | **NO** | Datos demo incluyen MPRO_ORIGEN |
| Propinas | **NO** | N/A | N/A | Alcance MVP: Solo SoftRestaurant |
| Presupuestos | Sí | **NO** | N/A | Tabla no existe |

### 3.2 Hallazgos de Cobertura MPRO

1. **Los filtros por `server_id` no funcionan correctamente** - Pasan el parámetro pero el resultado no cambia
2. **No hay filtro por sucursal MPRO** - No se puede filtrar por ORIGEN o 130° QRO individualmente
3. **El selector de unidades incluye MPRO** pero los datos no se diferencian
4. **Propinas TPV explícitamente excluye MPRO** - Es diseño del MVP, no es bug

---

## 4. ERRORES DETECTADOS

| # | Error | Ubicación | Momento | Descripción | Dictamen | Impacto | Causa probable | Acción |
|---|-------|-----------|---------|-------------|----------|---------|----------------|--------|
| 1 | Encoding SQL | SoftRestaurant | Query CxP | 'charmap' codec can't decode | FALLA SQL | **ALTO** | Encoding incorrecto | Configurar UTF-8 |
| 2 | Datos DEMO | tesoreria.py | Get Cortes Z | Fallback a datos hardcodeados | **MOCK/DEMO** | **CRÍTICO** | SQL falla, usa demo | Eliminar fallback |
| 3 | Tabla faltante | EDARSAHUB | Dashboard/Presupuestos | Finanzas_Presupuestos no existe | BLOQUEADO | **ALTO** | No creada | Ejecutar DDL |
| 4 | Sin sincronización | propinas_tpv | Get Propinas | Colección vacía | PENDIENTE | **ALTO** | Job no ejecutado | Sincronizar |
| 5 | Filtro server_id | Múltiples endpoints | Filtrar por unidad | Filtro no aplica | **FALLA FILTRO** | **ALTO** | Lógica de query | Revisar queries |
| 6 | Sin filtro sucursal MPRO | Todos | Filtrar ORIGEN/QRO | No existe | **FALLA COBERTURA** | **MEDIO** | No implementado | Agregar soporte |
| **7** | **IPs HARDCODEADAS** | `repository_cortes_z.py` | Conexión SQL | Evade `server_registry.py` | **ARQUITECTURA ROTA** | **CRÍTICO** | Implementación paralela | Refactorizar |

---

## 4.1 CAUSA RAÍZ TÉCNICA: IPs HARDCODEADAS EN TESORERÍA

### Hallazgo Crítico

El archivo `/app/backend/modules/finanzas/repository_cortes_z.py` **NO utiliza** el sistema centralizado de conexiones (`core/server_registry.py` + credenciales cifradas en MongoDB).

**Evidencia (líneas 23-62 del archivo):**
```python
SOFTREST_SERVERS = {
    'CIENFUEGOS': {
        'host': os.environ.get('SOFTREST_CIENFUEGOS_HOST', '187.188.198.241'),
        'port': int(os.environ.get('SOFTREST_CIENFUEGOS_PORT', '51741')),
        # ... IPs y puertos FIJOS con defaults hardcodeados
    },
    'LA_ESTELAR': { 'port': 51742, ... },
    '130_MERIDA': { 'port': 51743, ... }
}
MPRO_SERVERS = {
    'MPRO_ORIGEN': { 'port': 1433, 'database': 'CENTRAL2020', ... },
    'MPRO_QUERETARO': { 'port': 1433, ... }
}
```

### Comparación: Arquitectura Correcta vs Tesorería

| Aspecto | Método Correcto (`core/`) | Método en Tesorería |
|---------|--------------------------|---------------------|
| Conexión SQL | `execute_sql_query(server_id, query)` | `pytds.connect()` directo con IPs fijas |
| Credenciales | Cifradas en MongoDB (`edarsa_hub.servers`) | Hardcodeadas o env vars sin configurar |
| Gestión errores | Pool centralizado con fallback a caché | Fallback silencioso a datos DEMO |
| Filtro `server_id` | Usa UUID del registro en MongoDB | **NO USA** - consulta servidores fijos |

### Consecuencias Directas

1. **Las conexiones SQL fallan** → IPs/puertos hardcodeados no coinciden con configuración real
2. **Fallback silencioso a DEMO** → Oculta el error, muestra datos falsos como si fueran reales
3. **Filtros por `server_id` inoperantes** → No consulta MongoDB para obtener servidor seleccionado
4. **MPRO ORIGEN / 130° QRO indistinguibles** → No hay mapeo entre `server_id` y configuración MPRO

### Solución Propuesta (Pendiente Autorización)

Refactorizar `repository_cortes_z.py` para:
1. Obtener configuración desde `get_server_connection_info(server_id)`
2. Usar `execute_sql_query()` de `core/db.py`
3. Eliminar fallback a datos DEMO
4. Implementar filtro por sucursal MPRO usando `codigo_sucursal`

---

## 5. RESUMEN DE FUENTES DE DATOS

| Submódulo | Fuente Esperada SR | Fuente Esperada MPRO | Fuente Actual | Estado |
|-----------|--------------------|--------------------|---------------|--------|
| Dashboard | EDARSAHUB.Finanzas_Presupuestos | EDARSAHUB | N/A | ❌ BLOQUEADO |
| CxP Resumen | EDARSAHUB | EDARSAHUB | EDARSAHUB | ✅ OK (sin filtro) |
| CxP Listado | SoftRestaurant.CxP | MPRO.CxP | SQL FALLANDO | ❌ FALLA |
| Control Ingresos | EDARSAHUB.CortesCaja | EDARSAHUB.CortesCaja | MongoDB vacío | ❌ VACÍO |
| Tesorería | SR.movtoscaja | MPRO.? | **DATOS DEMO** | ❌ MOCK |
| Propinas | SR.movtoscajadetalles | **N/A (excluido)** | MongoDB vacío | ❌ N/A MPRO |
| Presupuestos | EDARSAHUB | EDARSAHUB | N/A | ❌ BLOQUEADO |

---

## 6. DICTAMEN FINAL

### Finanzas: ⚠️ **VALIDACIÓN PARCIAL - NO APROBADO**

**Motivos de rechazo:**

1. ❌ **Tesorería/Corte Z usa DATOS DEMO/MOCK** - INACEPTABLE
2. ❌ **Dashboard y Presupuestos bloqueados** por tabla faltante
3. ❌ **Filtros por server_id no funcionan** - No diferencia unidades
4. ❌ **Sin filtro por sucursal MPRO** - No se puede filtrar ORIGEN ni 130° QRO
5. ❌ **Propinas TPV sin sincronización** y excluye MPRO por diseño
6. ⚠️ **CxP parcialmente funcional** - Solo resumen sin filtros

**Submódulos donde MPRO NO APLICA (por diseño):**
- Propinas TPV: MVP Fase 1 solo incluye SoftRestaurant

**Único endpoint operativo:**
- ✅ CxP Resumen (sin filtros) - $11.6M datos reales de EDARSAHUB

### Condiciones para aprobación:
1. Eliminar todos los datos MOCK/DEMO de producción
2. Crear tabla Finanzas_Presupuestos
3. Corregir filtros por server_id en todos los endpoints
4. Implementar filtro por sucursal MPRO (ORIGEN, 130° QRO)
5. Corregir conexión SQL a SoftRestaurant
6. Sincronizar datos de Propinas y Cortes de Caja
7. Re-ejecutar auditoría completa

---

## 8. ESTADO DE CORRECCIONES (Actualizado 2025-12-27)

| # | Problema | Estado | Fecha | Acción |
|---|----------|--------|-------|--------|
| 1 | IPs hardcodeadas en `repository_cortes_z.py` | ✅ **CORREGIDO** | 2025-12-27 | Refactorizado para usar `server_registry.py` |
| 2 | Fallback silencioso a datos DEMO en `tesoreria.py` | ✅ **CORREGIDO** | 2025-12-27 | Eliminado fallback, ahora reporta error real |
| 3 | Endpoint `/sucursales` con datos estáticos | ✅ **CORREGIDO** | 2025-12-27 | Usa `list_servers()` del registry |
| 4 | Encoding SQL en SoftRestaurant | ⚠️ BLOQUEADO | - | Requiere config ambiente |
| 5 | Tabla `Finanzas_Presupuestos` inexistente | ✅ **CREADA** | 2025-12-27 | DDL ejecutado |
| 6 | Filtros `server_id` en CxP | ⚠️ PARCIAL | 2025-12-27 | Matching flexible implementado, bloqueado por encoding |
| 7 | MPRO excluido de Propinas TPV | ⏳ PENDIENTE (P2) | - | Implementar soporte MPRO |

---

*Documento generado por auditoría automatizada - 2025-12-27*
*Ampliación MPRO ORIGEN / 130° QRO incluida*
*ACTUALIZACIÓN: Correcciones P0 aplicadas (IPs hardcodeadas, fallback DEMO)*

---

## AUDITORÍA SUCURSALES MPRO (2025-12-28)

### Hallazgo Crítico

Las sucursales MPRO (**ORIGEN** y **130° QRO**) NO aparecen en los reportes de Finanzas CxP a pesar de:
- Estar correctamente configuradas en EDARSAHUB (tabla `Unidades_Negocio`)
- Tener datos reales en CENTRAL2020 (1,597 facturas, ~$20.5M)
- Aparecer correctamente en el endpoint `/api/unidades-negocio`

### Causa Raíz

La lógica de CxP usa **fallback** en lugar de **combinación**:
- Si SoftRestaurant retorna datos → NO se consulta MPRO
- MPRO solo se consulta si SoftRestaurant falla completamente

### Datos MPRO Disponibles (verificados en CENTRAL2020)

| Sucursal | Facturas | Saldo |
|----------|----------|-------|
| ORIGEN (0023) | 1,073 | $11,501,659.82 |
| 130° QUERETARO (0021) | 524 | $8,984,825.24 |

### Acción Requerida

Modificar `/app/backend/modules/finanzas/cuentas_por_pagar.py` para:
1. Consultar **siempre** ambas fuentes (SR + MPRO)
2. Combinar resultados etiquetando la fuente de cada factura
3. Actualizar endpoint `/resumen` para sumar totales de ambas fuentes

### Submódulos que NO aplican a MPRO

| Submódulo | Razón |
|-----------|-------|
| Control de Ingresos | Usa `movtoscaja` (SoftRestaurant) |
| Tesorería | Usa `movtoscajadetalles` (SoftRestaurant) |
| Propinas TPV | Usa `cheques.propinatarjeta` (SoftRestaurant) |


---

## CORRECCIÓN FINANZAS-CXP-MPRO-COMBINE-01 (2025-12-28)

### Estado: ✅ COMPLETADO

El módulo CxP ahora combina correctamente SoftRestaurant + ManagementPro.

### Resultados validados:
- **Total combinado**: 2,850 facturas, $48.8M
- **ORIGEN**: 1,073 facturas, $11,501,659.82 ✅
- **130° QRO**: 524 facturas, $8,984,825.24 ✅

### Archivos modificados:
- `cuentas_por_pagar.py`: Endpoints `/resumen`, `/sucursales`, listado
- `repository_mpro.py`: Migrado a subprocess, descifrado de contraseña

### Reporte:
`/app/docs/FINANZAS_CXP_MPRO_COMBINE_01_REPORT.md`


---

## SEGURIDAD CREDENCIALES MPRO (2025-12-28)

### FINANZAS-CXP-MPRO-CREDENTIALS-SECURITY-01: ✅ COMPLETADO

| Verificación | Resultado |
|--------------|-----------|
| Fuente credenciales | EDARSAHUB_SQL ✅ |
| MongoDB usado para password | NO ✅ |
| Password en argv | NO ✅ |
| Password en logs | NO ✅ |
| CxP funciona | SÍ ✅ |

### Reporte
`/app/docs/FINANZAS_CXP_MPRO_CREDENTIALS_SECURITY_01_REPORT.md`

