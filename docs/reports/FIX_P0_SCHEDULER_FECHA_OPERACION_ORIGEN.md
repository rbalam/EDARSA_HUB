# FIX P0: Scheduler FechaOperacion ORIGEN/130QRO

**Fecha**: 2026-05-15  
**Estado**: COMPLETADO ✅  
**Prioridad**: P0 (Crítico)

---

## 1. Resumen Ejecutivo

Se corrigió el job de sincronización `sync_comercial_abiertas_v2_job.py` para que las unidades MPRO (ORIGEN y 130QRO) calculen correctamente la `FechaOperacion` usando la ventana operativa del restaurante, en lugar de la fecha calendario.

**Resultado**: ORIGEN y 130QRO ahora conservan ventas reales del día operativo correcto, sin sobrescritura con $0.

---

## 2. Causa Raíz

El job de sincronización automática escribía `fecha_operacion` incorrecta durante la madrugada (00:00-03:00), causando:

1. **Fecha calendario vs Fecha operativa**: A las 01:00 AM del día 15, el job consultaba cuentas del día 15 en lugar del día 14 (jornada operativa vigente).
2. **$0 falso**: Las queries no encontraban datos porque buscaban en la fecha incorrecta.
3. **Sobrescritura**: Los datos válidos ($79,988 de ORIGEN) eran reemplazados por $0.

---

## 3. Archivo Modificado

```
/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py
```

---

## 4. Funciones Modificadas

### 4.1 Nueva función: `_get_existing_ventas_dia()`

```python
def _get_existing_ventas_dia(unidad_negocio_id: str, sucursal_id: str) -> Optional[Dict]:
    """
    Consulta el dato existente en Comercial_Ventas_Dia_Abiertas_v2 para una unidad.
    Se usa para verificar si hay un dato válido antes de sobrescribir con $0.
    """
```

### 4.2 Protección anti-$0 extendida a todas las unidades MPRO

**ANTES** (solo 130QRO tenía protección):
```python
if unidad_id == '130QRO':
    if ventas_abiertas_raw is None and ventas_cerradas_raw is None:
        continue  # NO sobrescribir
```

**DESPUÉS** (todas las unidades MPRO protegidas):
```python
# CASO 1: Hay datos válidos (al menos una query tiene valor > 0)
if total_calculado > 0:
    logger.info(f"[SYNC_ABIERTAS_V2] {nombre}: Datos válidos detectados")

# CASO 2: AMBAS son NULL - NO sobrescribir
elif ventas_abiertas_raw is None and ventas_cerradas_raw is None:
    continue  # Conservar último dato válido

# CASO 3: Total es $0 pero hay dato existente válido
elif total_calculado == 0:
    existing_data = _get_existing_ventas_dia(unidad_id, sucursal_id)
    if existing_total > 0:
        continue  # Protección: NO sobrescribir dato válido con $0
```

---

## 5. Antes/Después del Cálculo de FechaOperacion

### ANTES (Problema)
```
Hora actual: 01:00 AM del día 15
fecha_operacion guardada: 2026-05-15 ❌
Resultado: Query busca cuentas del día 15, no encuentra nada, guarda $0
```

### DESPUÉS (Corregido)
```
Hora actual: 01:39 AM del día 15
fecha_operacion calculada: 2026-05-14 ✅
Ventana operativa: 13:00 - 03:00 (cruza medianoche)
Resultado: Query busca cuentas del día 14, encuentra datos válidos
```

---

## 6. Evidencia de uso de get_operational_window()

```python
# Líneas 603-610 del job
fecha_operacion, hora_inicio, hora_fin, cruza_medianoche = get_operational_window(unidad_id)
fecha_operacion_str = fecha_operacion.isoformat()

logger.info(
    f"[SYNC_ABIERTAS_V2] {nombre}: FechaOperacion={fecha_operacion_str} "
    f"(horario={hora_inicio}-{hora_fin}, cruza_medianoche={cruza_medianoche})"
)
```

**Log de ejecución**:
```
[OPERATIONAL_WINDOW] ORIGEN: timestamp=2026-05-15 01:35, fecha_operacion=2026-05-14, 
                     horario=13:00:00-03:00:00, cruza_medianoche=True
```

---

## 7. Evidencia de que NO se usa date.today(), UTC date o fecha calendario simple

**Búsqueda en código**:
```bash
grep -n "date.today()\|datetime.now().date()\|datetime.utcnow()" sync_comercial_abiertas_v2_job.py
# Resultado: 0 coincidencias en lógica MPRO
```

**Confirmación**: El código MPRO usa exclusivamente:
- `get_operational_window(unidad_id)` para calcular FechaOperacion
- Zona horaria México (`America/Mexico_City`)

---

## 8. Evidencia de que NO se sobrescribe dato válido con $0

**Lógica implementada** (líneas 650-700):

```python
# CASO 3: Total es $0 pero hay dato existente válido
elif total_calculado == 0:
    existing_data = _get_existing_ventas_dia(unidad_id, sucursal_id)
    existing_total = float(existing_data.get('total_estimado_dia') or 0) if existing_data else 0
    
    if existing_total > 0:
        logger.warning(
            f"[SYNC_ABIERTAS_V2] {nombre}: Total calculado=$0 pero existe dato válido=${existing_total:,.2f}. "
            f"PROTECCIÓN: Conservando dato existente"
        )
        continue  # NO sobrescribir dato válido con $0
```

---

## 9. Resultado de Sincronización Manual Post-Fix para ORIGEN

```
======================================================================
VALIDACION JOB SYNC COMERCIAL ABIERTAS V2
Hora actual Mexico: 2026-05-15 01:39:17
======================================================================

ORIGEN:
  Sistema: MPRO
  Fecha Operacion: 2026-05-14
  Ventas Abiertas: $0.00
  Ventas Cerradas: $79,988.01
  Total Estimado: $79,988.01
  Status: OK
```

---

## 10. Resultado de Sincronización Manual Post-Fix para 130QRO

```
130QRO:
  Sistema: MPRO
  Fecha Operacion: 2026-05-14
  Ventas Abiertas: $0.00
  Ventas Cerradas: $207,323.00
  Total Estimado: $207,323.00
  Status: OK
```

---

## 11. Consulta SQL Directa a Comercial_Ventas_Dia_Abiertas_v2

```sql
SELECT unidad_negocio_id, fecha_operacion, total_estimado_dia, snapshot_timestamp
FROM Comercial_Ventas_Dia_Abiertas_v2
WHERE unidad_negocio_id IN ('ORIGEN', '130QRO')
```

**Resultado**:
| unidad_negocio_id | fecha_operacion | total_estimado_dia | snapshot_timestamp |
|-------------------|-----------------|--------------------|--------------------|
| 130QRO | 2026-05-14 | $207,323.00 | 2026-05-15T07:39:21 |
| ORIGEN | 2026-05-14 | $79,988.01 | 2026-05-15T07:39:22 |

---

## 12. FechaOperacion Resultante

| Unidad | FechaOperacion | Hora Ejecución | Ventana Operativa |
|--------|----------------|----------------|-------------------|
| ORIGEN | 2026-05-14 | 01:35 AM (día 15) | 13:00 - 03:00 |
| 130QRO | 2026-05-14 | 01:35 AM (día 15) | 13:00 - 03:00 |

✅ **Correcto**: A las 01:35 del día 15, la jornada operativa del día 14 sigue vigente (cierra a las 03:00).

---

## 13. Venta Sincronizada de ORIGEN

| Campo | Valor |
|-------|-------|
| unidad_negocio_id | ORIGEN |
| fecha_operacion | 2026-05-14 |
| ventas_abiertas | $0.00 |
| ventas_cerradas_dia | $79,988.01 |
| **total_estimado_dia** | **$79,988.01** |
| sistema_origen | MPRO |
| fuente_original | API_LOCAL |

---

## 14. Venta Sincronizada de 130QRO

| Campo | Valor |
|-------|-------|
| unidad_negocio_id | 130QRO |
| fecha_operacion | 2026-05-14 |
| ventas_abiertas | $0.00 |
| ventas_cerradas_dia | $207,323.00 |
| **total_estimado_dia** | **$207,323.00** |
| sistema_origen | MPRO |
| fuente_original | API_LOCAL |

---

## 15. Validación de No Regresión

| Unidad | Antes del Fix | Después del Fix | Status |
|--------|---------------|-----------------|--------|
| ORIGEN | $0.00 (fecha=2026-05-15) | $79,988.01 (fecha=2026-05-14) | ✅ |
| 130QRO | $0.00 (fecha=2026-05-15) | $207,323.00 (fecha=2026-05-14) | ✅ |
| CIENFUEGOS | $285,325.00 | $285,325.00 | ✅ |
| ESTELAR | $185,670.00 | $185,670.00 | ✅ |
| 130MID | $177,436.00 | $177,436.00 | ✅ |

---

## 16. Riesgos Pendientes

1. **Caché de horarios**: `operational_window.py` tiene caché de 30 minutos. Si se cambia el horario de una unidad, puede tardar en reflejarse.

2. **Duplicados legacy**: Existen registros duplicados con códigos antiguos (ej: `130-QRO` vs `130QRO`). Requiere limpieza futura.

3. **Conectividad CIENFUEGOS**: Hubo un warning de conexión fallida temporalmente, pero el pool de conexión se recuperó.

---

## 17. Confirmación: NO se tocó Frontend

```bash
git diff --name-only HEAD~1 | grep -E "frontend|\.jsx|\.tsx"
# Resultado: 0 archivos frontend modificados
```

**Archivos modificados**:
- `/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py` (únicamente)

---

## 18. Confirmación: NO se tocaron Módulos Protegidos

| Módulo | Estado |
|--------|--------|
| Tablero Ejecutivo | ❌ No modificado |
| Comercial Frontend | ❌ No modificado |
| Compras | ❌ No modificado |
| Finanzas | ❌ No modificado |
| Operaciones/Inventarios | ❌ No modificado |
| RBAC/Auth | ❌ No modificado |

---

## 19. Confirmación: NO se usaron Datos Mock

Todos los datos provienen de:
- **ORIGEN**: API Local MPRO real (http://54.39.104.176:8000/query)
- **130QRO**: API Local MPRO real (http://54.39.104.176:8001/query)
- **SoftRestaurant**: Conexión SQL Server directa a cada sucursal

---

## 20. Confirmación: El Tablero sigue leyendo EDARSAHUB SQL

**Endpoint verificado**: `/api/v2/comercial/ventas-dia`

```json
{
  "metadata": {
    "fuente": "EDARSAHUB_V2"
  }
}
```

**Código confirmado** (routes.py línea 6):
```python
# Leen EXCLUSIVAMENTE desde EDARSAHUB v2.
```

---

## Resumen Final

| Criterio | Status |
|----------|--------|
| FechaOperacion correcta para MPRO | ✅ |
| Protección anti-$0 implementada | ✅ |
| ORIGEN con venta real | ✅ $79,988.01 |
| 130QRO con venta real | ✅ $207,323.00 |
| Tablero lee EDARSAHUB | ✅ |
| Sin conexiones LIVE desde tablero | ✅ |
| Sin cambios en frontend | ✅ |
| Sin datos mock | ✅ |

**FIX P0 COMPLETADO EXITOSAMENTE**
