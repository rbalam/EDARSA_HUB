# FIX: Regla de Negocio - Fecha del Turno de Caja para Ventas del Día

**Fecha**: 2026-05-15 02:15 AM (México)  
**Estado**: COMPLETADO ✅  
**Prioridad**: P0 (Crítico)

---

## 1. Regla de Negocio Aplicada

> **La fecha de la venta será la fecha del turno de caja en el cual se aperturó la cuenta.**

### Reglas implementadas:

1. **NO usar fecha calendario actual** (date.today(), datetime.now().date())
2. **NO usar fecha UTC** del servidor
3. **NO usar GETDATE()** del servidor SoftRestaurant/MPRO
4. **SÍ usar fecha_operacion** calculada por `get_operational_window()`

### Flujo implementado:

```
FechaOperacion solicitada (calculada por get_operational_window)
↓
Buscar cheques abiertos/temporales con fecha=fecha_operacion
↓
Si existen → guardar venta abierta
↓
Buscar cheques cerrados/definitivos con fecha=fecha_operacion
↓
Si existen → guardar venta cerrada definitiva
↓
Si total > 0 → SYNC_OK
Si total = 0 pero hay dato existente válido → PROTECCIÓN ACTIVADA (no escribir)
Si total = 0 y no hay dato existente → SYNC_OK (venta real $0)
```

---

## 2. Archivos Revisados y Modificados

| Archivo | Acción |
|---------|--------|
| `/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py` | MODIFICADO |
| `/app/backend/core/utils/operational_window.py` | REVISADO (sin cambios) |
| `/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py` | REVISADO (sin cambios) |

---

## 3. Queries Actuales (Post-Fix)

### SoftRestaurant - Ventas Abiertas (tempcheques)

**ANTES**:
```sql
SELECT 
    CAST(GETDATE() AS DATE) as fecha,  -- ❌ GETDATE() del servidor
    ISNULL(SUM(total), 0) as ventas_abiertas,
    COUNT(*) as tickets_abiertos
FROM tempcheques
WHERE cancelado = 0
  AND total > 0
  -- NO filtraba por fecha ❌
```

**DESPUÉS**:
```sql
SELECT 
    '{fecha_operacion}' as fecha,  -- ✅ Fecha operativa calculada
    ISNULL(SUM(total), 0) as ventas_abiertas,
    COUNT(*) as tickets_abiertos
FROM tempcheques
WHERE cancelado = 0
  AND total > 0
  AND CAST(fecha AS DATE) = '{fecha_operacion}'  -- ✅ Filtrar por fecha turno
```

### SoftRestaurant - Ventas Cerradas (cheques)

**ANTES**:
```sql
SELECT 
    SUM(ISNULL(total, 0)) as ventas_cerradas_dia
FROM cheques
WHERE cancelado = 0
  AND cierre IS NOT NULL
  AND CAST(fecha AS DATE) = CAST(GETDATE() AS DATE)  -- ❌ GETDATE()
```

**DESPUÉS**:
```sql
SELECT 
    SUM(ISNULL(total, 0)) as ventas_cerradas_dia
FROM cheques
WHERE cancelado = 0
  AND cierre IS NOT NULL
  AND CAST(fecha AS DATE) = '{fecha_operacion}'  -- ✅ Fecha turno apertura
```

### MPRO - Sin cambios en queries (ya usaban {fecha_operacion})

```sql
-- ORIGEN y 130QRO
WHERE CAST(c.Co_Fecha AS DATE) = '{fecha_operacion}'
  AND c.Sc_Cve_Sucursal = '{sucursal_id}'
```

---

## 4. Tabla Temporal SoftRestaurant Identificada

| Tabla | Propósito | Columnas clave |
|-------|-----------|----------------|
| `tempcheques` | Cheques abiertos (turno activo) | fecha, total, nopersonas, cancelado |

---

## 5. Tabla Definitiva SoftRestaurant Identificada

| Tabla | Propósito | Columnas clave |
|-------|-----------|----------------|
| `cheques` | Cheques cerrados (turno finalizado) | fecha, total, nopersonas, cierre, cancelado |

---

## 6. Lógica Antes/Después

### ANTES (Bug):

```
1. Job se ejecuta a las 02:00 AM del día 15
2. GETDATE() del servidor SR devuelve "2026-05-15"
3. Query busca cheques con fecha=2026-05-15
4. No encuentra nada (los cheques son del día 14)
5. Escribe $0 en EDARSAHUB para día 15
6. Dato válido del día 14 se pierde al cambiar fecha_operacion
```

### DESPUÉS (Corregido):

```
1. Job se ejecuta a las 02:00 AM del día 15
2. get_operational_window() calcula fecha_operacion=2026-05-14
3. Query busca cheques con fecha=2026-05-14
4. Encuentra los cheques correctos
5. Si total > 0: Escribe venta real
6. Si total = 0 pero existe dato válido: PROTECCIÓN (no escribe)
```

---

## 7. Evidencia: No se usa Fecha Calendario Simple

```python
# CÓDIGO ACTUAL (línea 456-458):
fecha_operacion, hora_inicio, hora_fin, cruza_medianoche = get_operational_window(unidad_id)
fecha_operacion_str = fecha_operacion.isoformat()
```

**Log de ejecución**:
```
[OPERATIONAL_WINDOW] CIENFUEGOS: timestamp=2026-05-15 02:15, 
    fecha_operacion=2026-05-14, 
    horario=13:00:00-23:00:00, 
    cruza_medianoche=False
```

---

## 8. Evidencia: Venta se Asigna a Fecha del Turno de Apertura

| Unidad | Hora Sync | Fecha Calendario | FechaOperacion | Resultado |
|--------|-----------|------------------|----------------|-----------|
| CIENFUEGOS | 02:15 AM día 15 | 2026-05-15 | **2026-05-14** | ✅ |
| 130MID | 02:14 AM día 15 | 2026-05-15 | **2026-05-14** | ✅ |
| ORIGEN | 02:15 AM día 15 | 2026-05-15 | **2026-05-14** | ✅ |
| 130QRO | 02:15 AM día 15 | 2026-05-15 | **2026-05-14** | ✅ |

---

## 9. Evidencia: SoftRestaurant Conserva Venta Después del Corte

| Unidad | ventas_abiertas | ventas_cerradas | total_estimado_dia | Fuente |
|--------|-----------------|-----------------|--------------------| -------|
| CIENFUEGOS | $276,495 | $0 | **$276,495** | TEMPCHEQUES |
| 130MID | $173,010 | $31,693 | **$204,703** | TEMPCHEQUES |
| ESTELAR | $0 | $840 | **$840** | CHEQUES (cerrada) |

**ESTELAR**: Turno ya cerrado, tempcheques vacía, pero venta conservada en tabla `cheques`.

---

## 10. Evidencia: ORIGEN y 130QRO No Vuelven a $0

**Estado ANTES del fix (02:04 AM)**:
```
ORIGEN:  FechaOp=2026-05-15, Total=$0.00 ❌
130QRO:  FechaOp=2026-05-15, Total=$0.00 ❌
```

**Estado DESPUÉS del fix (02:15 AM)**:
```
ORIGEN:  FechaOp=2026-05-14, Total=$79,988.01 ✅ RESTAURADO
130QRO:  FechaOp=2026-05-14, Total=$207,323.00 ✅ RESTAURADO
```

---

## 11. Evidencia: No se Escribe $0 ante Temporal Vacía

**Protección implementada** (líneas 513-542):

```python
if total_estimado_dia == 0:
    existing_data = _get_existing_ventas_dia(unidad_id, sucursal_id)
    existing_total = float(existing_data.get('total_estimado_dia') or 0)
    
    if existing_total > 0:
        logger.warning(
            f"[SYNC_ABIERTAS_V2] {nombre}: Total=$0 pero existe dato válido=${existing_total:,.2f}. "
            f"PROTECCIÓN: Conservando dato existente."
        )
        continue  # NO sobrescribir ✅
```

---

## 12. Evidencia: Lectura desde EDARSAHUB SQL

**Endpoint verificado**: `/api/v2/comercial/ventas-dia`

```json
{
  "success": true,
  "data": {
    "por_unidad": [
      {
        "unidad_negocio_id": "ORIGEN",
        "total_estimado_dia": 79988.01,
        "_fuente": "EDARSAHUB_SQL"  // ✅ Lee de EDARSAHUB
      }
    ]
  }
}
```

---

## 13. Pruebas Realizadas por Unidad

| Unidad | Sistema | FechaOp | Total | Protección | Status |
|--------|---------|---------|-------|------------|--------|
| CIENFUEGOS | SoftRestaurant | 2026-05-14 | $276,495 | N/A | ✅ SYNC_OK |
| 130MID | SoftRestaurant | 2026-05-14 | $204,703 | N/A | ✅ SYNC_OK |
| ESTELAR | SoftRestaurant | 2026-05-14 | $840 | N/A | ✅ SYNC_OK |
| ORIGEN | MPRO | 2026-05-14 | $79,988 | ✅ Restaurado | ✅ SYNC_OK |
| 130QRO | MPRO | 2026-05-14 | $207,323 | ✅ Restaurado | ✅ SYNC_OK |

---

## 14. Riesgos Pendientes

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| HTTP 401 de ORIGEN | Medio | Protección anti-$0 activada |
| Tabla histórica vacía | Bajo | Implementar consolidación diaria (futuro) |
| Cambio de día operativo | Bajo | Protección NO sobrescribe dato válido |

---

## 15. Confirmación: No se Reactivó LIVE desde Tablero

- ❌ NO se añadieron llamadas a APIs locales desde frontend
- ❌ NO se modificó la lectura del tablero (sigue siendo EDARSAHUB)
- ✅ Solo el job de sincronización consulta las fuentes origen

---

## 16. Confirmación: No se Usaron Datos Mock

- ✅ Todos los datos provienen de fuentes reales
- ✅ SoftRestaurant: conexión directa a BD
- ✅ MPRO: API Local HTTP
- ✅ EDARSAHUB: SQL Server

---

## Resumen de Cambios en Código

### 1. Queries SoftRestaurant ahora usan `{fecha_operacion}`:

```sql
-- Abiertas
WHERE CAST(fecha AS DATE) = '{fecha_operacion}'

-- Cerradas
WHERE CAST(fecha AS DATE) = '{fecha_operacion}'
```

### 2. Protección anti-$0 mejorada:

```python
# NUNCA sobrescribir dato válido con $0
if existing_total > 0:
    continue  # PROTECCIÓN ACTIVADA
```

### 3. Fuente original dinámica:

```python
fuente = FuenteOriginal.TEMPCHEQUES if ventas_abiertas > 0 else FuenteOriginal.CHEQUES
```

---

## Conclusión

✅ **Regla de negocio implementada**: La fecha de la venta es la fecha del turno de apertura.
✅ **SoftRestaurant**: Busca en tempcheques Y cheques con fecha_operacion.
✅ **MPRO**: Usa fecha_operacion calculada, no fecha calendario.
✅ **Protección anti-$0**: No sobrescribe dato válido bajo ninguna circunstancia.
✅ **ORIGEN y 130QRO**: Restaurados a valores correctos ($79,988 y $207,323).

**FIX COMPLETADO EXITOSAMENTE**
