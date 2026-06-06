# DIAGNÓSTICO TÉCNICO: ARQUITECTURA DE QUERIES EDARSA HUB

**Fecha:** 2026-04-23  
**Autor:** E1 Agent  
**Estado:** Propuesta pendiente de aprobación

---

## 0. DICTAMEN MACROFASE 2 (CORREGIDO)

### 🟡 DICTAMEN FINAL: APTO CONDICIONAL PARA FASE 2.3

#### Estado por criterio
| Criterio | Descripción | Estado |
|----------|-------------|--------|
| **A** | Schedulers ejecutando automáticamente | ✅ Verificado |
| **B** | UPSERT idempotente sin duplicados | ✅ Verificado |
| **C** | Blindaje del pool SQL | 🟡 Implementado, pendiente validación en producción real |

#### Conclusión ejecutiva
La MACROFASE 2 cuenta con evidencia suficiente para considerar el avance a Fase 2.3 de forma **controlada**.
Sin embargo, el blindaje del pool SQL sigue siendo un **riesgo técnico abierto** hasta validar en producción real el escenario de contaminación cruzada entre módulos.

#### Riesgo abierto explícito
**Riesgo pendiente de validación operativa:**
- Validar que al entrar a Precios Constantes o ejecutar una query inválida/controlada en Compras
- El pool NO quede contaminado
- Y el Dashboard Comercial siga operando correctamente en navegación posterior

Este riesgo **NO puede considerarse cerrado desde preview** porque el ambiente no tiene acceso a los servidores SQL remotos reales.

#### Condición de avance
La Fase 2.3 puede autorizarse únicamente si:
- La carga histórica es controlada
- Es reversible
- No depende del flujo de navegación que originó el incidente
- Y se deja documentado que el blindaje SQL sigue pendiente de validación operativa

---

## 1. RESUMEN EJECUTIVO

### Hallazgos Críticos
- **55 duplicaciones** de queries de métricas de negocio detectadas
- **9 endpoints** con SQL directo en `routes.py` (anti-patrón)
- **44 llamadas a execute_sql_query** en `routes.py` (3,448 líneas)
- **17 llamadas a execute_sql_query** en `service.py` (1,197 líneas)
- El **Tablero Ejecutivo NO lee de `kpis_comercial`** (EDARSA HUB)

### Riesgo Principal
Diferentes tableros pueden devolver cifras distintas para la misma métrica debido a:
1. Queries ligeramente diferentes (ej: con o sin filtro de cancelados)
2. Cálculos de fechas inconsistentes
3. Manejo de NULL diferente
4. Transformaciones de datos no homologadas

---

## 2. MAPA DE DUPLICACIÓN POR MÉTRICA

| Métrica | Ocurrencias | Archivos Afectados | Clasificación |
|---------|-------------|-------------------|---------------|
| **VENTAS_TOTAL** | 27 | routes.py (20), service.py (7) | 🔴 CRÍTICA |
| **PAX_COMENSALES** | 20 | routes.py (14), service.py (6) | 🔴 CRÍTICA |
| **CONTEO_CHEQUES** | 7 | routes.py (4), service.py (3) | 🟡 ALTA |
| **CORTES_TURNOS** | 4 | routes.py (1), service.py (2), repository.py (1) | 🟡 ALTA |
| **TICKET_PROMEDIO** | 2 | routes.py (2) | 🟢 MEDIA |

---

## 3. ENDPOINTS CON SQL DIRECTO (ANTI-PATRÓN)

| Endpoint | Queries SQL | Estado | Acción Requerida |
|----------|-------------|--------|------------------|
| `/comercial/dashboard/{server_id}` | 11 | ❌ | Migrar a Service Layer |
| `/comercial/reporte-pax/{server_id}` | 8 | ❌ | Migrar a Service Layer |
| `/comercial/precios-constantes/{server_id}` | 7 | ❌ | Migrar a Service Layer |
| `/comercial/ventas-tiempo/{server_id}` | 4 | ❌ | Migrar a Service Layer |
| `/comercial/mesas/{server_id}` | 4 | ❌ | Migrar a Service Layer |
| `/comercial/detalle-movimientos/{server_id}` | 4 | ❌ | Migrar a Service Layer |
| `/comercial/ticket-perfecto/{server_id}` | 2 | ❌ | Migrar a Service Layer |
| `/comercial/metas/{server_id}` | 2 | ❌ | Migrar a Service Layer |
| `/comercial/sucursales/{server_id}` | 1 | ❌ | Migrar a Service Layer |
| `/comercial/tablero-ejecutivo` | 0* | ⚠️ | *Usa service.py pero service tiene SQL |

---

## 4. CLASIFICACIÓN DE COMPONENTES ACTUALES

### 4.1 COMPARTIDO / BASE (Debe centralizarse)

| Componente | Ubicación Actual | Recomendación |
|------------|------------------|---------------|
| Query ventas totales SoftRestaurant | service.py, routes.py | → `sql_queries/softrestaurant.py` |
| Query ventas totales MPRO | service.py, routes.py | → `sql_queries/mpro.py` |
| Query PAX SoftRestaurant | service.py, routes.py | → `sql_queries/softrestaurant.py` |
| Query PAX MPRO | service.py, routes.py | → `sql_queries/mpro.py` |
| Cálculo ticket promedio | service.py | → `domain/metricas.py` |
| Transformación fechas | Disperso | → `utils/fechas.py` |
| Validación system_type | core/db.py | ✅ Correcto |

### 4.2 ESPECÍFICO DE TABLERO (Permitido separado)

| Componente | Justificación |
|------------|---------------|
| Precios Constantes | Análisis inflacionario exclusivo |
| Ticket Perfecto | Métricas de calidad de servicio |
| Mesas / Ocupación | Reportes específicos de restaurante |
| Detalle Movimientos | Drill-down operativo |

### 4.3 DEBE MIGRARSE A HUB

| Componente | Origen Actual | Destino |
|------------|---------------|---------|
| KPIs diarios consolidados | SQL Live | `kpis_comercial` |
| Tablero Ejecutivo (período cerrado) | SQL Live | `kpis_comercial` |
| Dashboard Comercial (período cerrado) | SQL Live | `kpis_comercial` |
| Histórico para comparativos | SQL Live | `kpis_comercial` |

### 4.4 DEBE ELIMINARSE POR DUPLICIDAD

| Componente | Ubicación | Razón |
|------------|-----------|-------|
| Query ventas en routes.py líneas 744-752 | routes.py | Duplica service.py |
| Query ventas en routes.py líneas 1038-1066 | routes.py | Duplica service.py |
| Query PAX en routes.py líneas 1039, 1221 | routes.py | Duplica service.py |

### 4.5 REQUIERE CACHE

| Componente | Tipo Cache | TTL Recomendado |
|------------|------------|-----------------|
| Sucursales por servidor | MongoDB | 1 hora |
| Metas mensuales | MongoDB | 24 horas |
| KPIs históricos | `kpis_comercial` | Permanente |
| Dashboard tiempo real | MongoDB `dashboard_cache` | 5 min |

### 4.6 REQUIERE REFACTOR URGENTE

| Archivo | Líneas | Acción |
|---------|--------|--------|
| `routes.py` | 3,448 | Dividir en: endpoints.py + dashboard_endpoint.py + reportes_endpoint.py |
| `service.py` | 1,197 | Extraer queries SQL a capa repository |

---

## 5. PROPUESTA DE ARQUITECTURA POR CAPAS

```
/app/backend/modules/comercial/
├── __init__.py
├── schemas.py                    # Pydantic models (sin cambios)
│
├── queries/                      # CAPA A: FUENTE / REPOSITORY
│   ├── __init__.py
│   ├── base.py                   # SourceQueryResult, helpers comunes
│   ├── softrestaurant.py         # Queries SoftRestaurant homologadas
│   ├── mpro.py                   # Queries MPRO homologadas
│   └── hub.py                    # Lecturas de kpis_comercial
│
├── domain/                       # CAPA B: SERVICIO / DOMINIO
│   ├── __init__.py
│   ├── metricas.py               # Cálculos puros: ticket_prom, variaciones
│   ├── transformers.py           # Transformación de datos SQL -> domain
│   └── validators.py             # Validaciones de negocio
│
├── services/                     # CAPA B: SERVICIOS POR TABLERO
│   ├── __init__.py
│   ├── tablero_ejecutivo_service.py
│   ├── dashboard_comercial_service.py
│   ├── precios_constantes_service.py
│   ├── ticket_perfecto_service.py
│   └── reporte_pax_service.py
│
├── endpoints/                    # CAPA C: PRESENTACIÓN
│   ├── __init__.py
│   ├── tablero_ejecutivo.py      # Solo recibe filtros, llama servicio
│   ├── dashboard.py
│   ├── reportes.py               # Endpoints de reportes específicos
│   └── configuracion.py          # Metas, sucursales, etc.
│
├── cache_service.py              # Cache MongoDB (sin cambios mayor)
├── kpis_repository.py            # Repository HUB (sin cambios)
└── adapters.py                   # Adaptadores externos (sin cambios)
```

---

## 6. QUERIES BASE CENTRALIZADAS (PROPUESTA)

### 6.1 SoftRestaurant (`queries/softrestaurant.py`)

```python
# Archivo: /app/backend/modules/comercial/queries/softrestaurant.py

from dataclasses import dataclass
from typing import List, Dict, Optional
from core.db import execute_query_safe, SafeQueryResult

@dataclass
class VentasPeriodo:
    """Resultado homologado de ventas por período."""
    total_venta: float
    pax: int
    cheques: int
    ticket_promedio: float
    source_status: str  # LIVE, FALLBACK, NO_DATA

def query_ventas_periodo_sr(
    server: Dict,
    fecha_ini: str,  # YYYY-MM-DD
    fecha_fin: str,
    sucursal_id: Optional[str] = None
) -> SafeQueryResult:
    """
    Query base de ventas para SoftRestaurant.
    ÚNICA FUENTE DE VERDAD para esta métrica.
    
    Usada por:
    - Tablero Ejecutivo
    - Dashboard Comercial
    - Reporte PAX
    - SYNC-S (schedulers)
    """
    filtro_suc = f"AND cheques.idestacion = '{sucursal_id}'" if sucursal_id else ""
    
    # Formato YYYYMMDD para SoftRestaurant
    f_ini = fecha_ini.replace('-', '')
    f_fin = fecha_fin.replace('-', '')
    
    query = f"""
    SELECT 
        ISNULL(SUM(cheques.total), 0) as total_venta,
        ISNULL(SUM(cheques.nopersonas), 0) as pax,
        COUNT(DISTINCT cheques.folio) as cheques
    FROM cheques
    INNER JOIN turnos ON turnos.idturno = cheques.idturno
    WHERE CONVERT(varchar, turnos.apertura, 112) >= '{f_ini}'
      AND CONVERT(varchar, turnos.apertura, 112) <= '{f_fin}'
      AND cheques.cancelado = 0
      {filtro_suc}
    """
    
    return execute_query_safe(
        server_config=server,
        query=query,
        expected_system_types=['SoftRestaurant'],
        module_name="COMERCIAL_BASE"
    )


def query_ventas_por_sucursal_sr(
    server: Dict,
    fecha_ini: str,
    fecha_fin: str
) -> SafeQueryResult:
    """
    Ventas desglosadas por sucursal/estación.
    """
    f_ini = fecha_ini.replace('-', '')
    f_fin = fecha_fin.replace('-', '')
    
    query = f"""
    SELECT 
        CAST(cheques.idestacion as VARCHAR) as sucursal_id,
        ISNULL(SUM(cheques.total), 0) as total_venta,
        ISNULL(SUM(cheques.nopersonas), 0) as pax,
        COUNT(DISTINCT cheques.folio) as cheques
    FROM cheques
    INNER JOIN turnos ON turnos.idturno = cheques.idturno
    WHERE CONVERT(varchar, turnos.apertura, 112) >= '{f_ini}'
      AND CONVERT(varchar, turnos.apertura, 112) <= '{f_fin}'
      AND cheques.cancelado = 0
    GROUP BY cheques.idestacion
    """
    
    return execute_query_safe(
        server_config=server,
        query=query,
        expected_system_types=['SoftRestaurant'],
        module_name="COMERCIAL_BASE"
    )
```

### 6.2 MPRO (`queries/mpro.py`)

```python
# Archivo: /app/backend/modules/comercial/queries/mpro.py

def query_ventas_periodo_mpro(
    server: Dict,
    fecha_ini: str,
    fecha_fin: str,
    sucursal_id: Optional[str] = None
) -> SafeQueryResult:
    """
    Query base de ventas para MPRO.
    ÚNICA FUENTE DE VERDAD para esta métrica.
    """
    filtro_suc = f"AND VE.Sc_Cve_Sucursal = '{sucursal_id}'" if sucursal_id else ""
    
    query = f"""
    SELECT 
        ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as total_venta,
        ISNULL(SUM(C.Co_Personas), 0) as pax,
        COUNT(DISTINCT VE.Vn_Folio) as cheques
    FROM Venta_Encabezado VE
    LEFT JOIN Comanda C ON C.Vn_Folio = VE.Vn_Folio
    WHERE CONVERT(varchar, VE.Vn_Fecha, 112) >= '{fecha_ini.replace('-', '')}'
      AND CONVERT(varchar, VE.Vn_Fecha, 112) <= '{fecha_fin.replace('-', '')}'
      AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
      {filtro_suc}
    """
    
    return execute_query_safe(
        server_config=server,
        query=query,
        expected_system_types=['MPRO'],
        module_name="COMERCIAL_BASE"
    )
```

---

## 7. SERVICIO DE TABLERO (PROPUESTA)

```python
# Archivo: /app/backend/modules/comercial/services/tablero_ejecutivo_service.py

from typing import List, Dict
from ..queries.softrestaurant import query_ventas_periodo_sr
from ..queries.mpro import query_ventas_periodo_mpro
from ..queries.hub import get_kpis_from_hub
from ..domain.metricas import calcular_variaciones, calcular_ticket_promedio
from ..domain.transformers import transform_to_tablero_response

async def get_tablero_ejecutivo(
    servers: List[Dict],
    fecha_ini: str,
    fecha_fin: str,
    fecha_ini_ant: str,
    fecha_fin_ant: str,
    solo_ventas_dia: bool = False
) -> Dict:
    """
    Servicio del Tablero Ejecutivo.
    
    Estrategia de fuente:
    - solo_ventas_dia=True: LIVE-C (queries directas, no cache)
    - Período cerrado: Leer de HUB (kpis_comercial)
    - HUB sin datos: Fallback a LIVE + guardar en HUB
    """
    resultados = []
    totales = {"ventas": 0, "pax": 0, "cheques": 0}
    
    for server in servers:
        kpis = None
        source_status = "NO_DATA"
        
        if solo_ventas_dia:
            # LIVE-C: Siempre consulta directa
            kpis = await _get_kpis_live(server, fecha_ini, fecha_fin)
            source_status = "LIVE" if kpis else "LIVE_FAILED"
        else:
            # Intentar leer de HUB primero
            kpis = await get_kpis_from_hub(server['id'], fecha_ini, fecha_fin)
            if kpis:
                source_status = "HUB"
            else:
                # Fallback a LIVE
                kpis = await _get_kpis_live(server, fecha_ini, fecha_fin)
                source_status = "LIVE" if kpis else "NO_DATA"
        
        if kpis:
            kpis['source_status'] = source_status
            kpis['unidad'] = server['name']
            resultados.append(kpis)
            # Acumular totales
            for k in ['ventas', 'pax', 'cheques']:
                totales[k] += kpis.get(k, 0)
    
    # Calcular métricas derivadas
    totales['ticket_promedio'] = calcular_ticket_promedio(
        totales['ventas'], totales['pax']
    )
    
    return {
        "unidades": resultados,
        "totales": totales,
        "source_status": "MIXED" if any(r.get('source_status') != 'HUB' for r in resultados) else "HUB"
    }


async def _get_kpis_live(server: Dict, fecha_ini: str, fecha_fin: str) -> Optional[Dict]:
    """Obtiene KPIs directamente de la fuente SQL."""
    if server['system_type'] == 'SoftRestaurant':
        result = query_ventas_periodo_sr(server, fecha_ini, fecha_fin)
    elif server['system_type'] == 'MPRO':
        result = query_ventas_periodo_mpro(server, fecha_ini, fecha_fin)
    else:
        return None
    
    if result.success and result.data:
        row = result.data[0]
        return {
            "ventas": float(row.get('total_venta', 0)),
            "pax": int(row.get('pax', 0)),
            "cheques": int(row.get('cheques', 0)),
        }
    return None
```

---

## 8. PLAN DE MIGRACIÓN QUIRÚRGICO

### Fase 1: Preparación (Sin romper nada)
1. Crear directorio `queries/` con archivos vacíos
2. Crear directorio `services/` con archivos vacíos
3. Crear directorio `endpoints/` con archivos vacíos
4. Agregar imports condicionales para backward compatibility

### Fase 2: Centralizar Queries Base
1. Migrar `query_ventas_periodo_sr` (extraer de service.py líneas 340-410)
2. Migrar `query_ventas_periodo_mpro` (extraer de service.py líneas 870-920)
3. Crear tests unitarios para queries base
4. Verificar que devuelven exactamente los mismos valores

### Fase 3: Migrar Tablero Ejecutivo a HUB
1. Modificar endpoint para leer de `kpis_comercial` cuando período cerrado
2. Mantener fallback a LIVE si HUB no tiene datos
3. Verificar paridad de cifras con versión anterior

### Fase 4: Migrar Dashboard Comercial
1. Extraer queries SQL a `queries/`
2. Crear `dashboard_comercial_service.py`
3. Refactorizar endpoint para usar servicio
4. Verificar paridad

### Fase 5: Migrar Reportes Específicos
1. Precios Constantes → `precios_constantes_service.py`
2. Reporte PAX → `reporte_pax_service.py`
3. Ticket Perfecto → `ticket_perfecto_service.py`

### Fase 6: Limpieza
1. Eliminar código duplicado de routes.py
2. Eliminar código duplicado de service.py
3. Dividir routes.py en archivos menores
4. Actualizar imports

---

## 9. PRUEBAS OBLIGATORIAS

### 9.1 Paridad de Métricas
```bash
# Comparar misma métrica entre tableros
curl /api/comercial/tablero-ejecutivo?mes=4&anio=2026 > tablero.json
curl /api/comercial/dashboard/{server_id} > dashboard.json
# Verificar que totales.ventas sean iguales
```

### 9.2 Consistencia HUB vs LIVE
```bash
# Verificar que lectura de HUB = lectura LIVE para período cerrado
python -c "
from modules.comercial.queries.hub import get_kpis_from_hub
from modules.comercial.queries.softrestaurant import query_ventas_periodo_sr
# Comparar resultados
"
```

### 9.3 No Regresión
- [ ] Filtros RBAC funcionan igual
- [ ] Cache funciona igual
- [ ] Fechas se calculan igual
- [ ] NULL handling igual

---

## 10. RIESGOS DE REGRESIÓN

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Cálculo de fechas diferente | Alta | Alto | Tests de paridad antes/después |
| Filtro de sucursal omitido | Media | Alto | Revisar todos los filtros |
| Manejo de NULL diferente | Media | Medio | ISNULL/COALESCE consistente |
| Performance degradada | Baja | Medio | Benchmarks antes/después |
| RBAC bypass accidental | Baja | Crítico | Tests de acceso por rol |

---

## 11. DICTAMEN FINAL SOLICITADO

### Componentes que DEBEN ser COMPARTIDOS:
- ✅ `query_ventas_periodo_sr()` - Query base de ventas SoftRestaurant
- ✅ `query_ventas_periodo_mpro()` - Query base de ventas MPRO
- ✅ `query_pax_periodo_sr/mpro()` - Query base de PAX
- ✅ `calcular_ticket_promedio()` - Fórmula de ticket
- ✅ `calcular_variaciones()` - Fórmulas de variación %
- ✅ `execute_query_safe()` - Ya está en core/db.py

### Componentes ESPECÍFICOS (permitido separado):
- ✅ Precios Constantes - Análisis inflacionario único
- ✅ Ticket Perfecto - Métricas de calidad
- ✅ Mesas - Reportes de ocupación

### DEBE MIGRARSE A HUB:
- 🔴 Tablero Ejecutivo (períodos cerrados) → Leer de `kpis_comercial`
- 🔴 Dashboard Comercial (períodos cerrados) → Leer de `kpis_comercial`
- 🔴 Comparativos año anterior → Leer de `kpis_comercial`

### DEBE ELIMINARSE:
- 🔴 Queries duplicadas en routes.py (55 instancias)
- 🔴 SQL directo en endpoints

### REQUIERE CACHE:
- ✅ `dashboard_cache` - Ya implementado
- ✅ `kpis_comercial` - Ya implementado como HUB

### REQUIERE REFACTOR:
- 🔴 routes.py (3,448 líneas) → Dividir en 4+ archivos
- 🔴 service.py (1,197 líneas) → Extraer queries a capa repository

---

**ESTADO:** Pendiente aprobación del usuario para proceder con implementación.
