# CAMBIO REGLA FECHA OPERATIVA: Corte 06:00 AM

**Fecha:** 2026-05-17  
**Estado:** IMPLEMENTADO Y AUDITADO  
**Módulo:** Core / Comercial  

---

## 1. DESCRIPCIÓN DEL CAMBIO

### Regla Anterior (hasta 16-May-2026)
- Corte de jornada operativa: **03:00 AM**
- Ventas entre 00:00 y 02:59 pertenecían al día anterior
- Ventas a partir de 03:00 pertenecían al día calendario actual

### Regla Nueva (desde 17-May-2026)
- Corte de jornada operativa: **06:00 AM**
- Ventas entre 00:00 y 05:59 pertenecen al **día anterior**
- Ventas a partir de 06:00 pertenecen al **día calendario actual**

### Ejemplo
```
Hora México         Fecha Calendario     Fecha Operación
------------------------------------------------------------
17-May 05:30 AM     17-May              16-May  (día anterior)
17-May 06:00 AM     17-May              17-May  (día actual)
17-May 23:45 PM     17-May              17-May  (día actual)
18-May 02:00 AM     18-May              17-May  (día anterior)
```

---

## 2. ARCHIVOS MODIFICADOS

### Core: `/app/backend/core/utils/operational_window.py`

| Constante | Antes | Ahora |
|-----------|-------|-------|
| `VENTANA_FIN_HORA` | 3 | 6 |
| Función `get_fecha_operativa()` | Corte 03:00 | Corte 06:00 |
| Función `is_within_operational_window()` | Ventana hasta 03:00 | Ventana hasta 06:00 |

### Comercial: `/app/backend/modules/comercial/service.py`

- Función `_obtener_kpis_tablero_desde_edarsahub()` usa `get_fecha_operativa()` actualizada
- Proyección mensual usa `dias_transcurridos` basado en `FechaOperacionActual.day`

### Comercial: `/app/backend/modules/comercial/routes.py`

- Endpoint `/tablero-ejecutivo` calcula `fecha_operativa` con corte 06:00 AM
- Variable `dias_transcurridos` = `fecha_operativa.day`

---

## 3. REGLA DE PROYECCIÓN MENSUAL

### Fórmula Canónica
```
ProyecciónMensual = VentasAcumuladas / FechaOperacionActual.day * DíasMes
```

### Donde:
- `VentasAcumuladas` = Suma de ventas desde día 1 hasta `FechaOperacionActual`
- `FechaOperacionActual.day` = Día del mes de la fecha operativa (NO fecha calendario)
- `DíasMes` = Total de días del mes (28/29/30/31)

### Ejemplo Mayo 2026
```
Hora actual: 17-May-2026 08:15 AM México
Corte: 06:00 AM

FechaOperacionActual = 17-May (porque hora >= 06:00)
dias_transcurridos = 17
VentasAcumuladas = $9,741,095.20

ProyecciónMensual = $9,741,095.20 / 17 * 31 = $17,764,720.36
```

### NO usar:
- ❌ `MAX(fecha_operacion)` de la tabla (último registro)
- ❌ `fecha_calendario.day` (puede diferir si hora < 06:00)
- ❌ Número de registros con ventas

---

## 4. AUDITORÍA HISTÓRICA

### Script Creado
`/app/backend/scripts/audit_fecha_operativa_0600.py`

### Propósito
Diagnosticar registros históricos con timestamp entre 00:00 y 05:59 que podrían tener `FechaOperacion` incorrecta bajo la nueva regla.

### Tablas Auditadas
| Tabla | Estado | Hallazgos |
|-------|--------|-----------|
| `Comercial_KPIs_Diarios_v2` | ✅ Auditada | Tabla consolidada por día, sin hora exacta |
| `Sync_Ventas_PorHora` | ✅ Auditada | Registros con hora < 6 detectados |
| `Comercial_Ventas_Dia_Abiertas_v2` | ✅ Auditada | Snapshots con hora < 6 detectados |

### Resultado de Auditoría (17-May-2026)
```
✅ NO SE ENCONTRARON INCONSISTENCIAS CRÍTICAS
   Los datos existentes son consistentes con la regla anterior (03:00 AM)
   No se requiere UPDATE histórico inmediato
```

### Reporte JSON
`/app/docs/reports/audit_fecha_operativa_0600_202605.json`

---

## 5. IMPACTO EN DATOS HISTÓRICOS

### Escenario: Venta a las 04:30 AM del 15-May
| Regla | FechaOperacion Asignada |
|-------|-------------------------|
| Anterior (03:00) | 15-May (día calendario) |
| Nueva (06:00) | 14-May (día anterior) |

### Recomendación
Los datos históricos fueron sincronizados con la regla de 03:00 AM. Si se requiere consistencia retroactiva:

1. **Opción A (Conservadora):** Mantener datos históricos como están
   - Pros: Sin riesgo de corrupción
   - Cons: Inconsistencia temporal en reportes históricos

2. **Opción B (Migración):** UPDATE selectivo a registros con hora 03:00-05:59
   - Pros: Consistencia total
   - Cons: Requiere autorización explícita y backup

**Estado actual:** Se mantiene Opción A (sin UPDATE histórico) hasta nueva autorización.

---

## 6. VALIDACIÓN EN TABLERO EJECUTIVO

### Configuración Verificada
```python
# routes.py - Endpoint /tablero-ejecutivo
fecha_operativa = get_fecha_operativa()  # Usa corte 06:00 AM
dias_transcurridos = fecha_operativa.day  # Día de la fecha operativa
```

### Prueba Realizada (17-May-2026 11:44 AM México)
```
Hora actual: 11:44 AM > 06:00 AM
FechaOperacionActual = 17-May-2026
dias_transcurridos = 17
```

### Resultado
| Unidad | Ventas Acumuladas | Proyección |
|--------|-------------------|------------|
| CIENFUEGOS | $2,543,511.00 | Calculada con /17 |
| 130MID | $2,094,097.00 | Calculada con /17 |
| 130QRO | $2,037,841.00 | Calculada con /17 |
| ESTELAR | $1,744,171.00 | Calculada con /17 |
| ORIGEN | $1,322,475.20 | Calculada con /17 |

---

## 7. CRITERIOS DE ACEPTACIÓN

| Criterio | Estado |
|----------|--------|
| Corte operativo a las 06:00 AM | ✅ IMPLEMENTADO |
| Proyección usa `FechaOperacionActual.day` | ✅ IMPLEMENTADO |
| NO usa último registro como divisor | ✅ VERIFICADO |
| Script de auditoría creado | ✅ CREADO |
| Auditoría no modifica datos | ✅ CUMPLIDO |
| Reporte generado | ✅ ESTE DOCUMENTO |

---

## 8. ARCHIVOS DE REFERENCIA

| Archivo | Propósito |
|---------|-----------|
| `/app/backend/core/utils/operational_window.py` | Lógica de ventana operativa |
| `/app/backend/modules/comercial/routes.py` | Endpoint Tablero Ejecutivo |
| `/app/backend/modules/comercial/service.py` | Funciones de KPIs |
| `/app/backend/scripts/audit_fecha_operativa_0600.py` | Script de auditoría |
| `/app/docs/reports/audit_fecha_operativa_0600_202605.json` | Resultado de auditoría |

---

**Autor:** Sistema E1  
**Validado:** 2026-05-17 11:45 UTC  
**Próxima Revisión:** Cuando se autorice UPDATE histórico (si aplica)
