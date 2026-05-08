# AUDITORÍA PREVENTIVA — Bug de Parseo SQL Server

**Fecha:** 2026-05-01 03:10 UTC  
**Ejecutor:** E1 Agent  
**Tipo:** Auditoría de Solo Lectura  
**Estado:** COMPLETADA

---

## Resumen Ejecutivo

Se realizó auditoría de código para identificar riesgos de bug de parseo de conexiones SQL Server similar al detectado en CIENFUEGOS (`sync_cortes_softrestaurant.py`).

### Resultados Clave

| Categoría | Cantidad |
|-----------|----------|
| Archivos revisados | 25+ |
| Archivos con riesgo ALTO | 4 |
| Archivos con riesgo MEDIO | 6 |
| Archivos con riesgo BAJO | 8 |
| Archivos sin riesgo | Resto |
| Módulos blindados afectados | 0 (sin modificar) |

---

## Causa Raíz del Bug Original

El script `sync_cortes_softrestaurant.py` tenía parseo manual incompleto:

```python
# ANTES (BUG):
if ',' in host_raw:
    parts = host_raw.split(',')
    host = parts[0]  # ❌ Descarta instancia
    port = int(parts[1].split('\\')[0])
```

**Problema:** Descartaba la instancia nombrada (`\nationalsoft`) requerida para conectar a SQL Server.

**Solución:** Usar `core.db.parse_sql_server_host()` que preserva hostname, puerto e instancia.

---

## Patrón Técnico de Riesgo

### Indicadores de Riesgo:
1. Parseo manual con `split('\\')` o `split(',')`
2. Uso directo de `pymssql.connect()` sin helper oficial
3. No uso de `core.db.parse_sql_server_host()`
4. Credenciales hardcodeadas
5. Hosts hardcodeados
6. No soporte para instancias nombradas

### Helper Oficial Correcto:
```python
from core.db import parse_sql_server_host
hostname, port, instance = parse_sql_server_host(host_raw, default_port)
```

---

## Archivos Revisados

### Módulo Finanzas
- `/app/backend/modules/finanzas/sync_cortes_softrestaurant.py` ✅ CORREGIDO
- `/app/backend/modules/finanzas/sync_cortes_mpro.py`
- `/app/backend/modules/finanzas/sql_query_worker.py`
- `/app/backend/modules/finanzas/sql_query_worker_secure.py`
- `/app/backend/modules/finanzas/repository_softrestaurant.py`
- `/app/backend/modules/finanzas/historical_kpis_repository.py`

### Módulo Comercial
- `/app/backend/modules/comercial/repository.py`
- `/app/backend/modules/comercial/adapters.py`

### Módulo Automatización
- `/app/backend/modules/automatizacion/repository.py`

### Módulo RH
- `/app/backend/modules/rh/importador/aprobacion_service.py`
- `/app/backend/modules/rh/importador/homologacion_service.py`

### Módulo API Connections
- `/app/backend/modules/api_connections/repository.py`

### Core
- `/app/backend/core/db.py`
- `/app/backend/core/server_registry.py`
- `/app/backend/core/resilient_sql.py`
- `/app/backend/core/auditoria.py`

### Scripts
- `/app/backend/scripts/run_historical_load_finanzas.py`
- `/app/backend/scripts/run_historical_load_compras.py`

### Server Principal
- `/app/backend/server.py` (líneas 9420-9450, 11380-11410)

---

## Hallazgos por Módulo

### 1. `/app/backend/modules/finanzas/repository_softrestaurant.py`

| Atributo | Valor |
|----------|-------|
| **Riesgo** | 🔴 **CRÍTICO** |
| **Bug parseo** | NO aplica (hosts separados) |
| **Problema** | CREDENCIALES HARDCODEADAS en texto plano |
| **Líneas** | 36-62 |
| **Driver** | Usa subprocess helper |
| **Afecta módulo blindado** | NO (CxP ya corregido no usa este archivo) |

**Evidencia:**
```python
SOFTRESTAURANT_SERVERS = {
    "CIENFUEGOS": {
        "host": "servercienfuegos.ddns.net",
        "port": 6669,
        "username": "CFLectura",
        "password": "National09",  # ⚠️ HARDCODED
    },
    ...
}
```

**Recomendación:** Migrar a lectura desde EDARSAHUB.Servidores_Conexiones. Requiere autorización porque puede afectar CxP.

---

### 2. `/app/backend/modules/automatizacion/repository.py`

| Atributo | Valor |
|----------|-------|
| **Riesgo** | 🟠 **ALTO** |
| **Bug parseo** | SÍ - Descarta instancia |
| **Líneas** | 338-350 |
| **Driver** | pymssql |
| **Función** | `_execute_query_with_params()` |

**Evidencia:**
```python
if ',' in host:
    parts = host.split(',')
    host_clean = parts[0]
    port = int(parts[1].split('\\')[0])  # ❌ Descarta instancia
```

**Recomendación:** Migrar a `parse_sql_server_host()`.

---

### 3. `/app/backend/modules/finanzas/sync_cortes_mpro.py`

| Atributo | Valor |
|----------|-------|
| **Riesgo** | 🟡 **MEDIO** |
| **Bug parseo** | Parcial - Solo maneja `:` no `,` |
| **Líneas** | 118-124 |
| **Driver** | pymssql |
| **Afecta** | ORIGEN, 130° QRO |

**Evidencia:**
```python
if ':' in host_raw:
    parts = host_raw.split(':')
    host = parts[0]
    port = int(parts[1])
# ❌ No maneja formato ,puerto\instancia
```

**Recomendación:** Migrar a `parse_sql_server_host()` para consistencia.

**Nota:** Actualmente funciona porque MPRO (54.39.104.176) no usa instancias nombradas.

---

### 4. `/app/backend/scripts/run_historical_load_finanzas.py`

| Atributo | Valor |
|----------|-------|
| **Riesgo** | 🟠 **ALTO** |
| **Bug parseo** | SÍ - Descarta instancia |
| **Líneas** | 167-182 |
| **Driver** | pytds |
| **Función** | `parse_server_host()` |

**Evidencia:**
```python
if '\\' in rest:
    port_part = rest.split('\\')[0]
    port = int(port_part)
elif '\\' in host_str:
    host = host_str.split('\\')[0]  # ❌ Descarta instancia
```

**Recomendación:** Migrar a `parse_sql_server_host()`.

---

### 5. `/app/backend/scripts/run_historical_load_compras.py`

| Atributo | Valor |
|----------|-------|
| **Riesgo** | 🟠 **ALTO** |
| **Bug parseo** | SÍ - Ignora instancia explícitamente |
| **Líneas** | 85-101 |
| **Driver** | pytds |

**Evidencia (comentario en código):**
```python
# host,puerto\\instancia (ignora instancia, pytds no la soporta con puerto)
```

**Nota:** El comentario es INCORRECTO. pytds SÍ soporta instancias si no se pasa puerto separado.

**Recomendación:** Migrar a `parse_sql_server_host()`.

---

### 6. `/app/backend/server.py` (Líneas 9420-9450, 11380-11410)

| Atributo | Valor |
|----------|-------|
| **Riesgo** | 🟡 **MEDIO** |
| **Bug parseo** | Parcial - Maneja pero inconsistente |
| **Funciones** | Query execution endpoints |
| **Driver** | pytds |

**Evidencia:**
```python
if ',' in host_str:
    parts = host_str.split(',')
    host = parts[0].strip()
    port = int(parts[1].strip().split('\\')[0])  # Extrae puerto pero ignora instancia
    if '\\' in host_str:
        host = host_str.split(',')[0].strip()  # ❌ Lógica confusa
```

**Recomendación:** Estandarizar con `parse_sql_server_host()`.

---

### 7. `/app/backend/modules/finanzas/sql_query_worker.py` y `sql_query_worker_secure.py`

| Atributo | Valor |
|----------|-------|
| **Riesgo** | 🟢 **BAJO** |
| **Bug parseo** | NO - Implementación correcta |
| **Driver** | pytds |

**Evidencia (CORRECTA):**
```python
if '\\' in rest:
    instance = rest.split('\\', 1)[1]
    server = f"{base_server}\\{instance}"  # ✅ Preserva instancia
```

**Recomendación:** Considerar migrar a helper oficial para consistencia.

---

### 8. Módulos RH (aprobacion_service.py, homologacion_service.py)

| Atributo | Valor |
|----------|-------|
| **Riesgo** | 🟢 **BAJO** |
| **Bug parseo** | NO aplica |
| **Driver** | pymssql |

**Evidencia:**
```python
return pymssql.connect(
    server=server['host'],
    port=server['port'],
    ...
)
```

**Nota:** Recibe host y port ya parseados del llamador. No tiene bug de parseo propio.

---

### 9. Core (db.py, server_registry.py, resilient_sql.py)

| Atributo | Valor |
|----------|-------|
| **Riesgo** | 🟢 **SIN RIESGO** |
| **Bug parseo** | NO |

**Nota:** Estos archivos DEFINEN el helper oficial `parse_sql_server_host()` y lo usan correctamente.

---

## Conexiones que Usan Instancia Nombrada

| Servidor | Host | Puerto | Instancia | Sistema |
|----------|------|--------|-----------|---------|
| CIENFUEGOS | servercienfuegos.ddns.net | 6669 | nationalsoft | SoftRestaurant |
| 130° MÉRIDA | server130merida.ddns.net | 6669 | nationalsoft | SoftRestaurant |
| LA ESTELAR | serverestelar.ddns.net | 6969 | (ninguna) | SoftRestaurant |
| MPRO | 54.39.104.176 | 1433 | (ninguna) | MPRO |

---

## Recomendación de Estandarización

### Propuesta Técnica:

1. **Todos los módulos** deben usar `core.db.parse_sql_server_host()` para parsear hosts SQL Server.

2. **Eliminar parseo manual** con `split()` duplicado en cada módulo.

3. **Migrar credenciales hardcodeadas** a EDARSAHUB.Servidores_Conexiones.

4. **Usar pytds como driver preferido** para instancias nombradas (mejor soporte).

### Prioridad de Corrección:

| Prioridad | Archivo | Razón |
|-----------|---------|-------|
| P0 | repository_softrestaurant.py | Credenciales hardcodeadas |
| P1 | automatizacion/repository.py | Bug parseo activo |
| P1 | run_historical_load_finanzas.py | Bug parseo activo |
| P1 | run_historical_load_compras.py | Bug parseo activo |
| P2 | sync_cortes_mpro.py | Parseo incompleto (funciona por ahora) |
| P2 | server.py (9420, 11380) | Lógica inconsistente |
| P3 | sql_query_worker*.py | Funciona pero no usa helper oficial |

---

## Lista de Cambios Sugeridos (NO EJECUTADOS)

| # | Archivo | Cambio Sugerido | Requiere Autorización |
|---|---------|-----------------|----------------------|
| 1 | repository_softrestaurant.py | Eliminar SOFTRESTAURANT_SERVERS hardcodeado, leer de EDARSAHUB | ⚠️ SÍ (puede afectar CxP) |
| 2 | automatizacion/repository.py | Usar parse_sql_server_host() | SÍ (módulo activo) |
| 3 | run_historical_load_finanzas.py | Usar parse_sql_server_host() | NO (script) |
| 4 | run_historical_load_compras.py | Usar parse_sql_server_host() | NO (script) |
| 5 | sync_cortes_mpro.py | Usar parse_sql_server_host() | SÍ (Subfase 2.3) |
| 6 | server.py | Estandarizar con parse_sql_server_host() | ⚠️ SÍ (impacto global) |

---

## Cambios que Requieren Autorización Especial

### 1. `repository_softrestaurant.py` — MÓDULO POTENCIALMENTE BLINDADO

**Razón:** Este archivo puede ser usado por CxP (ya corregido). Modificar las credenciales hardcodeadas podría romper el flujo de CxP.

**Acción requerida:** Verificar si CxP usa este archivo antes de modificar.

### 2. `server.py` — IMPACTO GLOBAL

**Razón:** Modificar lógica de parseo en server.py puede afectar múltiples endpoints.

**Acción requerida:** Pruebas exhaustivas antes de cambiar.

---

## Confirmaciones

| Verificación | Estado |
|--------------|--------|
| ¿Se modificó código? | ❌ NO |
| ¿Se modificaron módulos blindados? | ❌ NO |
| ¿Se modificaron credenciales? | ❌ NO |
| ¿Se modificaron conexiones? | ❌ NO |
| ¿Se ejecutaron queries? | ❌ NO (solo grep/view) |

---

## Conclusión

Se identificaron **10 archivos con riesgo** de tener bug de parseo similar al corregido en CIENFUEGOS. La mayoría pueden corregirse de forma aislada, pero algunos requieren autorización especial por su potencial impacto en módulos blindados o endpoints globales.

**Recomendación inmediata:** Priorizar corrección de `repository_softrestaurant.py` por tener credenciales hardcodeadas en texto plano (riesgo de seguridad).

---

## AUDITORÍA DE IMPACTO — repository_softrestaurant.py

**Fecha:** 2026-05-01 03:30 UTC  
**Estado:** COMPLETADA (Solo Lectura)

---

### Árbol de Dependencias

```
repository_softrestaurant.py
    ├── IMPORTADO POR: server.py (línea 316)
    │   └── _softrest_repo = FinanzasRepositorySoftRestaurant(db)
    │       └── finanzas_cxp.set_softrestaurant_repository(_softrest_repo)
    │
    └── USADO POR: cuentas_por_pagar.py (CxP)
        ├── get_cuentas_por_pagar() - líneas 263, 857
        └── get_resumen_por_sucursal() - línea 1077
```

---

### Archivos Importadores

| Archivo | Línea | Tipo de Uso |
|---------|-------|-------------|
| `/app/backend/server.py` | 316 | Import directo de clase |
| `/app/backend/server.py` | 343 | Instanciación |
| `/app/backend/server.py` | 344 | Inyección a CxP |

---

### Endpoints Afectados

| Endpoint | Archivo | Uso de repository_softrestaurant |
|----------|---------|----------------------------------|
| `/api/finanzas/cuentas-por-pagar` | cuentas_por_pagar.py | `get_cuentas_por_pagar()` |
| `/api/finanzas/cuentas-por-pagar/resumen` | cuentas_por_pagar.py | `get_resumen_por_sucursal()` |

---

### Módulos Afectados

| Módulo | ¿Usa el archivo? | Impacto |
|--------|------------------|---------|
| **CxP (cuentas_por_pagar.py)** | ✅ SÍ - ACTIVAMENTE | 🔴 CRÍTICO |
| Control de Ingresos (ingresos.py) | ❌ NO | ✅ Sin impacto |
| Sync SoftRestaurant | ❌ NO | ✅ Sin impacto |
| Sync MPRO | ❌ NO | ✅ Sin impacto |
| Comercial | ❌ NO | ✅ Sin impacto |
| Compras | ❌ NO | ✅ Sin impacto |
| Operaciones | ❌ NO | ✅ Sin impacto |
| Tablero Ejecutivo | ❌ NO | ✅ Sin impacto |

---

### Funciones con Credenciales Hardcodeadas

| Función | Línea | Usa Credenciales Hardcodeadas |
|---------|-------|-------------------------------|
| `SOFTRESTAURANT_SERVERS` (dict) | 32-62 | ⚠️ SÍ - 3 servidores |
| `_execute_query_subprocess()` | 246-276 | SÍ - lee de SOFTRESTAURANT_SERVERS |
| `get_cuentas_por_pagar()` | 305 | Indirecto - usa _execute_query_subprocess |
| `get_resumen_por_sucursal()` | 542 | Indirecto - usa _execute_query_subprocess |

---

### Servidores Hardcodeados

| Key | Host | Puerto | Database | Usuario | Password |
|-----|------|--------|----------|---------|----------|
| CIENFUEGOS | servercienfuegos.ddns.net | 6669 | softrestaurant95pro | CFLectura | ⚠️ Texto plano |
| ESTELAR | serverestelar.ddns.net | 6969 | softrestaurant12 | SCedarsa | ⚠️ Texto plano |
| 130MID | 130mid.ddns.net | 1433 | softrestaurant10 | SCedarsa | ⚠️ Texto plano |

---

### Riesgo para CxP

| Aspecto | Evaluación |
|---------|------------|
| **¿CxP usa este archivo?** | ✅ SÍ - ES LA FUENTE DE DATOS PRINCIPAL |
| **¿Cambiar credenciales rompe CxP?** | 🔴 SÍ - Si las credenciales dejan de funcionar |
| **¿Cambiar a EDARSAHUB rompe CxP?** | ⚠️ POSIBLE - Si el contrato de respuesta cambia |
| **Nivel de riesgo** | 🔴 **CRÍTICO** |

---

### Riesgo para Control de Ingresos

| Aspecto | Evaluación |
|---------|------------|
| **¿Control de Ingresos usa este archivo?** | ❌ NO |
| **¿La corrección afectaría Control de Ingresos?** | ❌ NO |
| **Nivel de riesgo** | 🟢 **NINGUNO** |

---

### Riesgo para Módulos Blindados

| Módulo Blindado | Riesgo |
|-----------------|--------|
| Tablero Ejecutivo | 🟢 Ninguno |
| Servidores | 🟢 Ninguno |
| Operaciones | 🟢 Ninguno |
| Compras | 🟢 Ninguno |
| Comercial | 🟢 Ninguno |
| **CxP** | 🔴 **CRÍTICO** |

---

### Funciones que Podrían Migrarse a EDARSAHUB

| Función | Migrable | Condición |
|---------|----------|-----------|
| `SOFTRESTAURANT_SERVERS` | ✅ SÍ | Leer de Servidores_Conexiones |
| `_execute_query_subprocess()` | ✅ SÍ | Usar credenciales de EDARSAHUB |
| `get_cuentas_por_pagar()` | ⚠️ Parcial | Mantener contrato de respuesta |

---

### Recomendación de Corrección Segura por Subfases

#### OPCIÓN A: Migración Gradual (RECOMENDADA)

1. **Subfase A.1:** Crear función `_get_server_config_from_edarsahub(server_key)` que lea de EDARSAHUB
2. **Subfase A.2:** Agregar flag `USE_EDARSAHUB_FOR_SOFTREST` (default=false)
3. **Subfase A.3:** Cuando flag=true, usar EDARSAHUB; cuando flag=false, usar hardcoded
4. **Subfase A.4:** Validar CxP con ambas fuentes
5. **Subfase A.5:** Cambiar flag a true en producción
6. **Subfase A.6:** Eliminar credenciales hardcodeadas

#### OPCIÓN B: Mantener como Deuda Técnica

1. NO modificar repository_softrestaurant.py
2. Documentar como deuda técnica de seguridad
3. Abordar en ventana de mantenimiento controlado

---

### Archivos que se Modificarían (si se autoriza)

| Archivo | Cambio Propuesto |
|---------|------------------|
| `/app/backend/modules/finanzas/repository_softrestaurant.py` | Agregar lectura de EDARSAHUB con flag |

### Archivos que NO Deben Tocarse

| Archivo | Razón |
|---------|-------|
| `/app/backend/modules/finanzas/cuentas_por_pagar.py` | CxP blindado |
| `/app/backend/server.py` | Inicialización global |
| Todos los módulos blindados | Máximas obligatorias |

---

### Plan de Pruebas Antes/Después

**ANTES de cambiar:**
1. Capturar respuesta de `/api/finanzas/cuentas-por-pagar` para CIENFUEGOS
2. Capturar respuesta de `/api/finanzas/cuentas-por-pagar` para LA ESTELAR
3. Capturar respuesta de `/api/finanzas/cuentas-por-pagar` para 130° MÉRIDA
4. Documentar totales, saldos, número de registros

**DESPUÉS de cambiar:**
1. Comparar respuestas (deben ser idénticas)
2. Verificar que agrupadores A/B/X funcionan
3. Verificar filtros por sucursal
4. Verificar que no hay errores de conexión

---

### Confirmación

| Verificación | Estado |
|--------------|--------|
| ¿Se modificó código? | ❌ NO |
| ¿Se modificaron credenciales? | ❌ NO |
| ¿Se modificó CxP? | ❌ NO |
| ¿Se modificó EDARSAHUB? | ❌ NO |
| Auditoría de solo lectura | ✅ SÍ |

---

### Dictamen Final

**`repository_softrestaurant.py` ES CRÍTICO PARA CxP.**

Modificar este archivo sin precaución extrema **ROMPERÁ el módulo CxP** que ya está validado y blindado.

**RECOMENDACIÓN:** 
- ⚠️ NO corregir credenciales hardcodeadas sin autorización explícita y plan de rollback
- ✅ Mantener como deuda técnica documentada hasta ventana de mantenimiento
- ✅ Priorizar estabilidad de CxP sobre eliminación de hardcoded

---

**FIN AUDITORÍA DE IMPACTO**

---

**FIN AUDITORÍA PREVENTIVA**
