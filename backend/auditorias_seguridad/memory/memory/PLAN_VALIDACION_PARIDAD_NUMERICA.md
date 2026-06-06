# PLAN DE VALIDACIÓN DE PARIDAD NUMÉRICA
## Riesgos R1, R3, R4

**Versión**: 1.0  
**Fecha**: 2026-04-23  
**Estado**: PLAN EJECUTABLE (pendiente de ambiente con conectividad)  
**Autor**: Arquitectura Senior

---

## 1. RESUMEN EJECUTIVO

Este documento define el plan para validar que el código refactorizado produce **exactamente los mismos resultados numéricos** que el código original cuando se ejecuta contra servidores SQL reales.

**Riesgos a validar:**

| Riesgo | Bloque | Descripción | Estado Actual |
|--------|--------|-------------|---------------|
| **R1** | BLOQUE 4 | Paridad numérica `service.py` vs queries centralizadas | ABIERTO |
| **R3** | SUB-BLOQUE 5.1 | Paridad numérica dashboard SoftRestaurant | ABIERTO |
| **R4** | SUB-BLOQUE 5.2 | Paridad numérica dashboard MPRO | ABIERTO |

**Criterio de éxito:** `Diff = 0.00` en ventas, pax y cheques para todos los casos de prueba.

---

## 2. AMBIENTE REQUERIDO

### 2.1 Requisitos de Conectividad

```
┌─────────────────┐          ┌─────────────────┐
│  Máquina de     │   SQL    │  Servidor SR    │
│  Validación     │ ◄───────▶│  (SoftRestaurant)│
│                 │  1433    │                 │
│  - Python 3.11+ │          └─────────────────┘
│  - pyodbc       │
│  - pymssql      │          ┌─────────────────┐
│                 │   SQL    │  Servidor MPRO  │
│                 │ ◄───────▶│  (ManagementPro)│
│                 │  1433    │                 │
└─────────────────┘          └─────────────────┘
```

### 2.2 Precondiciones Exactas

| Requisito | Verificación | Estado |
|-----------|--------------|--------|
| Conectividad a servidores SQL SR | `telnet <host_sr> 1433` responde | ❓ Pendiente |
| Conectividad a servidores SQL MPRO | `telnet <host_mpro> 1433` responde | ❓ Pendiente |
| Credenciales SQL válidas | Login exitoso | ❓ Pendiente |
| Base de datos con datos del período | Query de prueba retorna > 0 registros | ❓ Pendiente |
| Ambiente con código refactorizado | Branch actual con Bloques 4, 5.1, 5.2 | ✅ Listo |
| Variables de entorno configuradas | `.env` con MONGO_URL, JWT_SECRET | ✅ Listo |

### 2.3 Credenciales Necesarias

```yaml
# Servidores SoftRestaurant (obtener de configuración HUB)
softrestaurant_servers:
  - name: "SERVIDOR_SR_1"
    host: "<IP_PRODUCCION_SR>"
    port: 1433
    database: "<DATABASE_SR>"
    username: "<USER>"
    password: "<PASSWORD>"

# Servidores MPRO (obtener de configuración HUB)
mpro_servers:
  - name: "SERVIDOR_MPRO_1"
    host: "<IP_PRODUCCION_MPRO>"
    port: 1433
    database: "<DATABASE_MPRO>"
    username: "<USER>"
    password: "<PASSWORD>"
```

**NOTA:** Las credenciales están almacenadas en la colección `sql_servers` de MongoDB. El script de validación las lee directamente de ahí.

---

## 3. MATRIZ DE CASOS DE PRUEBA

### 3.1 R1: BLOQUE 4 - service.py vs queries centralizadas

| Caso | Función | Período | Sucursal | Métricas |
|------|---------|---------|----------|----------|
| R1.1 | `get_kpis_softrestaurant_por_sucursal` | Mes actual | Todas | ventas, pax, cheques |
| R1.2 | `get_kpis_softrestaurant_por_sucursal` | Mes anterior | Todas | ventas, pax, cheques |
| R1.3 | `get_kpis_mpro_por_sucursal` | Mes actual | Todas | ventas, pax, cheques |
| R1.4 | `get_kpis_mpro_por_sucursal` | Mes anterior | Todas | ventas, pax, cheques |

### 3.2 R3: SUB-BLOQUE 5.1 - Dashboard SoftRestaurant

| Caso | Endpoint | Período | Sucursal | Métricas |
|------|----------|---------|----------|----------|
| R3.1 | `/comercial/dashboard/{server_sr}` | día | default | ventas, pax, cheques |
| R3.2 | `/comercial/dashboard/{server_sr}` | mes | default | ventas, pax, cheques |
| R3.3 | `/comercial/dashboard/{server_sr}` | mes | sucursal_especifica | ventas, pax, cheques |

### 3.3 R4: SUB-BLOQUE 5.2 - Dashboard MPRO

| Caso | Endpoint | Período | Sucursal | Métricas |
|------|----------|---------|----------|----------|
| R4.1 | `/comercial/dashboard/{server_mpro}` | día | default | ventas, pax, cheques |
| R4.2 | `/comercial/dashboard/{server_mpro}` | mes | default | ventas, pax, cheques |
| R4.3 | `/comercial/dashboard/{server_mpro}` | mes | sucursal_especifica | ventas, pax, cheques |
| R4.4 | `/comercial/dashboard/{server_mpro}` | mes | filtro_por_nombre | ventas, pax, cheques |

---

## 4. SCRIPTS DE VALIDACIÓN

### 4.1 Ubicación de Scripts

```
/app/backend/scripts/validacion_paridad/
├── precheck_conectividad.py       # Ya existe, verifica conexión SQL
├── validar_r1_service.py          # Nuevo: Valida BLOQUE 4
├── validar_r3_dashboard_sr.py     # Nuevo: Valida SUB-BLOQUE 5.1
├── validar_r4_dashboard_mpro.py   # Nuevo: Valida SUB-BLOQUE 5.2
├── utils.py                       # Utilidades comunes
└── resultados/                    # Carpeta de output
    └── YYYY-MM-DD_HH-MM/          # Timestamped results
```

### 4.2 Script: validar_r1_service.py

```python
"""
VALIDACIÓN R1: BLOQUE 4 - service.py vs queries centralizadas

PROPÓSITO:
Ejecutar la MISMA query por DOS vías:
1. SQL directo (código original, hardcodeado en este script)
2. Función centralizada (queries/softrestaurant.py, queries/mpro.py)

Comparar resultados y reportar Diff.

EJECUCIÓN:
python validar_r1_service.py --server-id <UUID> --periodo mes_actual
"""

import sys
sys.path.insert(0, '/app/backend')

import argparse
import json
from datetime import datetime, timedelta
from decimal import Decimal

from core.db import execute_sql_query
from modules.comercial.queries.softrestaurant import query_ventas_periodo_sr
from modules.comercial.queries.mpro import query_ventas_periodo_mpro

# =============================================================================
# QUERIES ORIGINALES (copiadas textualmente del código ANTES del refactor)
# =============================================================================

QUERY_ORIGINAL_SR = """
SELECT 
    SUM(c.total) as ventas,
    SUM(c.nopersonas) as pax,
    COUNT(*) as cheques
FROM cheques c
JOIN turnos t ON c.turno = t.turno
WHERE CONVERT(varchar, t.apertura, 112) >= '{fi}'
  AND CONVERT(varchar, t.apertura, 112) <= '{ff}'
  AND c.cancelado = 0
"""

QUERY_ORIGINAL_MPRO = """
SELECT 
    COUNT(DISTINCT VE.Vn_Folio) as cheques,
    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas,
    ISNULL(SUM(C.Co_Personas), 0) as pax
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
WHERE VE.Vn_Fecha >= '{fi}' AND VE.Vn_Fecha <= '{ff}'
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
"""

def ejecutar_query_original(server, fecha_ini, fecha_fin, system_type):
    """Ejecuta query ORIGINAL (hardcodeada)."""
    if system_type == 'SoftRestaurant':
        query = QUERY_ORIGINAL_SR.format(fi=fecha_ini.replace('-', ''), ff=fecha_fin.replace('-', ''))
    else:
        query = QUERY_ORIGINAL_MPRO.format(fi=fecha_ini.replace('-', ''), ff=fecha_fin.replace('-', ''))
    
    result = execute_sql_query(
        server['host'], server['port'], server['database'],
        server['username'], server['password'], query
    )
    
    if result and len(result) > 0:
        return {
            'ventas': float(result[0].get('ventas') or 0),
            'pax': int(result[0].get('pax') or 0),
            'cheques': int(result[0].get('cheques') or 0)
        }
    return {'ventas': 0, 'pax': 0, 'cheques': 0}


def ejecutar_query_centralizada(server, fecha_ini, fecha_fin):
    """Ejecuta query CENTRALIZADA (refactorizada)."""
    system_type = server.get('system_type')
    
    if system_type == 'SoftRestaurant':
        result = query_ventas_periodo_sr(server, fecha_ini, fecha_fin)
    else:
        result = query_ventas_periodo_mpro(server, fecha_ini, fecha_fin)
    
    if result.success:
        return {
            'ventas': result.total_venta,
            'pax': result.pax,
            'cheques': result.cheques
        }
    return {'ventas': 0, 'pax': 0, 'cheques': 0, 'error': result.error}


def calcular_diff(original, centralizada):
    """Calcula diferencia entre resultados."""
    diff = {}
    for key in ['ventas', 'pax', 'cheques']:
        orig = original.get(key, 0)
        cent = centralizada.get(key, 0)
        diff[key] = {
            'original': orig,
            'centralizada': cent,
            'diff_abs': cent - orig,
            'diff_pct': round(((cent - orig) / orig * 100), 4) if orig != 0 else 0
        }
    return diff


def validar_caso(server, fecha_ini, fecha_fin, caso_id):
    """Ejecuta validación de un caso."""
    print(f"\n{'='*60}")
    print(f"CASO {caso_id}: {server['name']} ({server['system_type']})")
    print(f"Período: {fecha_ini} a {fecha_fin}")
    print('='*60)
    
    # Ejecutar ambas vías
    original = ejecutar_query_original(server, fecha_ini, fecha_fin, server['system_type'])
    centralizada = ejecutar_query_centralizada(server, fecha_ini, fecha_fin)
    
    # Calcular diff
    diff = calcular_diff(original, centralizada)
    
    # Evaluar resultado
    paridad_ok = all(d['diff_abs'] == 0 for d in diff.values())
    
    print(f"\nRESULTADO ORIGINAL:     Ventas={original['ventas']:,.2f}, PAX={original['pax']}, Cheques={original['cheques']}")
    print(f"RESULTADO CENTRALIZADO: Ventas={centralizada['ventas']:,.2f}, PAX={centralizada['pax']}, Cheques={centralizada['cheques']}")
    print(f"\nDIFF:")
    for key, d in diff.items():
        status = "✅" if d['diff_abs'] == 0 else "❌"
        print(f"  {status} {key}: {d['diff_abs']} ({d['diff_pct']}%)")
    
    print(f"\n{'✅ PARIDAD OK' if paridad_ok else '❌ PARIDAD FALLIDA'}")
    
    return {
        'caso_id': caso_id,
        'server': server['name'],
        'system_type': server['system_type'],
        'fecha_ini': fecha_ini,
        'fecha_fin': fecha_fin,
        'original': original,
        'centralizada': centralizada,
        'diff': diff,
        'paridad_ok': paridad_ok
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Validación R1: service.py vs queries centralizadas')
    parser.add_argument('--server-id', required=True, help='UUID del servidor')
    parser.add_argument('--periodo', choices=['mes_actual', 'mes_anterior'], default='mes_actual')
    args = parser.parse_args()
    
    # Cargar configuración del servidor desde MongoDB
    # (Implementación real cargaría de BD)
    # Para este ejemplo, usar mock
    print("NOTA: Ejecutar desde ambiente con conectividad SQL")
```

### 4.3 Script: validar_r3_dashboard_sr.py

```python
"""
VALIDACIÓN R3: SUB-BLOQUE 5.1 - Dashboard SoftRestaurant

PROPÓSITO:
Comparar respuesta del endpoint /comercial/dashboard/{server_id}
ejecutando en paralelo:
1. Código ORIGINAL (queries SQL directas en routes.py snapshot)
2. Código REFACTORIZADO (usando query_ventas_periodo_sr)

EJECUCIÓN:
python validar_r3_dashboard_sr.py --server-id <UUID> --periodo mes
"""

# Similar estructura al R1, pero llama al endpoint completo
# y compara el JSON de respuesta
```

### 4.4 Script: validar_r4_dashboard_mpro.py

```python
"""
VALIDACIÓN R4: SUB-BLOQUE 5.2 - Dashboard MPRO

PROPÓSITO:
Comparar respuesta del endpoint /comercial/dashboard/{server_id}
para servidores MPRO, incluyendo:
- Filtro por código de sucursal
- Filtro por nombre de sucursal
- Sin filtro (todas las sucursales)

EJECUCIÓN:
python validar_r4_dashboard_mpro.py --server-id <UUID> --periodo mes --sucursal "PRINCIPAL"
"""

# Similar estructura, con casos adicionales de filtro
```

---

## 5. DATOS A CAPTURAR

### 5.1 Antes de Ejecutar Validación

| Dato | Cómo Obtenerlo | Propósito |
|------|----------------|-----------|
| Fecha/hora de ejecución | `datetime.now()` | Timestamp del reporte |
| Versión del código | `git log -1 --format=%H` | Trazabilidad |
| Servidor(es) objetivo | Configuración HUB | Contexto |
| Estado de conectividad | `precheck_conectividad.py` | Confirmar ambiente |

### 5.2 Durante la Ejecución

| Dato | Fuente | Propósito |
|------|--------|-----------|
| Query original ejecutada | Script hardcodeado | Referencia |
| Resultado query original | SQL directo | Baseline |
| Resultado query centralizada | Función refactorizada | Comparación |
| Duración query (ms) | Timestamp delta | Performance |
| Errores capturados | Try/except | Diagnóstico |

### 5.3 Después de Ejecutar

| Dato | Formato | Ubicación |
|------|---------|-----------|
| Reporte completo | JSON | `/app/backend/scripts/validacion_paridad/resultados/{timestamp}/` |
| Resumen ejecutivo | Markdown | Mismo directorio |
| Diff detallado | JSON | Por caso de prueba |

---

## 6. CRITERIOS DE ACEPTACIÓN

### 6.1 Criterio de Paridad Validada ✅

```
CONDICIONES (TODAS deben cumplirse):

1. CONECTIVIDAD:
   - precheck_conectividad.py retorna 100% servidores alcanzables

2. EJECUCIÓN:
   - Todos los scripts ejecutan sin errores de runtime
   - Todas las queries (original y centralizada) retornan resultados

3. PARIDAD NUMÉRICA:
   - Para CADA caso de prueba:
     - Diff_ventas == 0.00
     - Diff_pax == 0
     - Diff_cheques == 0

4. COBERTURA:
   - Al menos 1 servidor SoftRestaurant validado
   - Al menos 1 servidor MPRO validado
   - Casos de mes actual y mes anterior ejecutados
```

**Si todas las condiciones se cumplen → Riesgo CERRADO**

### 6.2 Criterio de Rechazo ❌

```
CUALQUIERA de las siguientes condiciones:

1. FALLO DE CONECTIVIDAD:
   - No se puede alcanzar ningún servidor → Riesgo SIGUE ABIERTO (bloqueado)

2. ERROR DE EJECUCIÓN:
   - Script falla con excepción → Riesgo SIGUE ABIERTO (bug en script)

3. DIFERENCIA NUMÉRICA:
   - Diff_ventas != 0.00 → Riesgo SIGUE ABIERTO (regresión)
   - Diff_pax != 0 → Riesgo SIGUE ABIERTO (regresión)
   - Diff_cheques != 0 → Riesgo SIGUE ABIERTO (regresión)

4. COBERTURA INSUFICIENTE:
   - No se validó ningún servidor SR → R3 SIGUE ABIERTO
   - No se validó ningún servidor MPRO → R4 SIGUE ABIERTO
```

**Si cualquier condición de rechazo se cumple → Documentar motivo y mantener riesgo ABIERTO**

---

## 7. MANEJO DE SERVIDORES QUE NO RESPONDEN

### 7.1 Protocolo de Timeout

```python
TIMEOUT_CONEXION = 30  # segundos
MAX_REINTENTOS = 3
ESPERA_ENTRE_REINTENTOS = 10  # segundos
```

### 7.2 Clasificación de Fallas

| Tipo de Falla | Acción | Impacto en Validación |
|---------------|--------|----------------------|
| Timeout de conexión | Reintentar 3 veces | Si persiste, excluir servidor |
| Credenciales inválidas | NO reintentar | Excluir servidor, alertar |
| Base de datos no existe | NO reintentar | Excluir servidor, alertar |
| Query sin resultados | Válido (0 registros) | Incluir en reporte |
| Error SQL en query | Capturar, NO reintentar | Excluir caso, alertar |

### 7.3 Reporte de Servidores Excluidos

```json
{
  "servidores_excluidos": [
    {
      "server_id": "uuid-1",
      "name": "Servidor X",
      "motivo": "Timeout después de 3 reintentos",
      "timestamp": "2026-04-23T10:15:00Z"
    }
  ],
  "impacto": "Riesgo R3 no puede cerrarse sin validar al menos 1 servidor SR"
}
```

---

## 8. DOCUMENTACIÓN DEL DIFF

### 8.1 Formato de Reporte por Caso

```json
{
  "caso_id": "R4.2",
  "descripcion": "Dashboard MPRO - Mes - Default",
  "servidor": {
    "id": "6d053c22-...",
    "name": "CIENFUEGOS MPRO",
    "system_type": "MPRO"
  },
  "periodo": {
    "fecha_ini": "2026-04-01",
    "fecha_fin": "2026-04-23"
  },
  "resultados": {
    "original": {
      "ventas": 1250000.00,
      "pax": 4500,
      "cheques": 1200
    },
    "centralizada": {
      "ventas": 1250000.00,
      "pax": 4500,
      "cheques": 1200
    }
  },
  "diff": {
    "ventas": { "abs": 0.00, "pct": 0.00 },
    "pax": { "abs": 0, "pct": 0.00 },
    "cheques": { "abs": 0, "pct": 0.00 }
  },
  "veredicto": "PARIDAD_OK",
  "duracion_ms": {
    "original": 1200,
    "centralizada": 1150
  },
  "timestamp": "2026-04-23T10:15:30Z"
}
```

### 8.2 Resumen Ejecutivo (Markdown)

```markdown
# REPORTE DE VALIDACIÓN DE PARIDAD NUMÉRICA
**Fecha:** 2026-04-23 10:15:00 UTC
**Versión código:** abc123def

## RESUMEN

| Riesgo | Casos OK | Casos FAIL | Estado |
|--------|----------|------------|--------|
| R1 | 4/4 | 0 | ✅ CERRADO |
| R3 | 3/3 | 0 | ✅ CERRADO |
| R4 | 4/4 | 0 | ✅ CERRADO |

## DETALLE POR RIESGO

### R1: BLOQUE 4 - service.py
- [x] R1.1 SR Mes Actual: Diff=0
- [x] R1.2 SR Mes Anterior: Diff=0
- [x] R1.3 MPRO Mes Actual: Diff=0
- [x] R1.4 MPRO Mes Anterior: Diff=0

...

## CONCLUSIÓN

Todos los riesgos de paridad numérica han sido validados con Diff=0.00.
Los riesgos R1, R3 y R4 pueden declararse **CERRADOS**.
```

---

## 9. DICTÁMENES POSIBLES

### 9.1 Dictamen: PARIDAD VALIDADA

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  VALIDACIÓN DE PARIDAD NUMÉRICA - DICTAMEN FINAL                             ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  Riesgo R1 (BLOQUE 4):     ✅ CERRADO - Diff=0.00 en todos los casos        ║
║  Riesgo R3 (SUB-BLOQUE 5.1): ✅ CERRADO - Diff=0.00 en todos los casos      ║
║  Riesgo R4 (SUB-BLOQUE 5.2): ✅ CERRADO - Diff=0.00 en todos los casos      ║
║                                                                               ║
║  CONCLUSIÓN: Refactorización validada numéricamente.                         ║
║  No hay regresiones detectadas.                                              ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### 9.2 Dictamen: RIESGO SIGUE ABIERTO (por falta de ambiente)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  VALIDACIÓN DE PARIDAD NUMÉRICA - DICTAMEN PARCIAL                           ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  AMBIENTE: Sin conectividad SQL a servidores de producción                   ║
║                                                                               ║
║  Riesgo R1 (BLOQUE 4):     ⚠️ ABIERTO - No ejecutado                        ║
║  Riesgo R3 (SUB-BLOQUE 5.1): ⚠️ ABIERTO - No ejecutado                      ║
║  Riesgo R4 (SUB-BLOQUE 5.2): ⚠️ ABIERTO - No ejecutado                      ║
║                                                                               ║
║  PRÓXIMOS PASOS:                                                             ║
║  1. Obtener acceso a ambiente con conectividad (VPN o red local)            ║
║  2. Ejecutar scripts de validación                                           ║
║  3. Emitir dictamen final                                                    ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### 9.3 Dictamen: REGRESIÓN DETECTADA

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  VALIDACIÓN DE PARIDAD NUMÉRICA - REGRESIÓN DETECTADA                        ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  Riesgo R1: ✅ CERRADO                                                       ║
║  Riesgo R3: ✅ CERRADO                                                       ║
║  Riesgo R4: ❌ REGRESIÓN DETECTADA                                           ║
║                                                                               ║
║  CASO FALLIDO: R4.3 - Dashboard MPRO con filtro por sucursal                ║
║  DIFF: Ventas=-15000.00 (-1.2%)                                             ║
║                                                                               ║
║  ACCIÓN REQUERIDA:                                                           ║
║  1. Analizar query centralizada vs original                                  ║
║  2. Identificar diferencia en lógica de filtro                              ║
║  3. Corregir y re-validar                                                    ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 10. CHECKLIST DE EJECUCIÓN

### Antes de iniciar validación:

- [ ] Confirmar ambiente con conectividad SQL (VPN activa o red local)
- [ ] Ejecutar `precheck_conectividad.py` y verificar 100% OK
- [ ] Tener credenciales de al menos 1 servidor SR y 1 MPRO
- [ ] Código actualizado (git pull) con Bloques 4, 5.1, 5.2
- [ ] Variables de entorno configuradas

### Durante la validación:

- [ ] Ejecutar `validar_r1_service.py` para cada servidor
- [ ] Ejecutar `validar_r3_dashboard_sr.py` para servidores SR
- [ ] Ejecutar `validar_r4_dashboard_mpro.py` para servidores MPRO
- [ ] Capturar output completo de cada script
- [ ] Guardar reportes en `/app/backend/scripts/validacion_paridad/resultados/`

### Después de la validación:

- [ ] Generar resumen ejecutivo (Markdown)
- [ ] Actualizar PRD.md con estado de riesgos
- [ ] Si hay regresiones, abrir issue con detalle del diff
- [ ] Emitir dictamen final

---

## APROBACIÓN

| Aspecto | Estado |
|---------|--------|
| Riesgos identificados y mapeados | ✅ |
| Ambiente requerido definido | ✅ |
| Precondiciones listadas | ✅ |
| Matriz de casos completa | ✅ |
| Scripts de referencia incluidos | ✅ |
| Criterios de aceptación claros | ✅ |
| Criterios de rechazo claros | ✅ |
| Manejo de errores definido | ✅ |
| Formato de reporte definido | ✅ |
| Dictámenes posibles documentados | ✅ |

---

**PLAN DE VALIDACIÓN COMPLETADO**

Este documento está listo para ejecutarse cuando exista un ambiente con conectividad SQL a los servidores de producción.
