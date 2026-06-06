# BACKFILL: Sync_Ventas_PorHora para 2026-05-07

**Fecha de Análisis:** 2026-05-17  
**Estado:** ❌ DATOS HORARIOS NO DISPONIBLES EN EDARSAHUB SQL  
**Objetivo:** Completar datos de ventas por hora para el día 2026-05-07  

---

## 1. OBJETIVO

Determinar si es posible reconstruir los registros de `Sync_Ventas_PorHora` para el día **2026-05-07** usando exclusivamente datos existentes en EDARSAHUB SQL.

---

## 2. DECISIÓN DE NO USAR LIVE

**PROHIBIDO por directiva del usuario:**
- NO conectar a servidores LIVE SoftRestaurant
- NO conectar a servidores LIVE MPRO
- NO consultar bases origen remotas
- NO crear datos sintéticos
- NO distribuir totales proporcionalmente por hora

---

## 3. TABLAS EDARSAHUB REVISADAS

### 3.1 Tablas con datos para 2026-05-07

| Tabla | Registros | Tiene Hora | Detalle |
|-------|-----------|------------|---------|
| `Comercial_KPIs_Diarios_v2` | 5 | ❌ | Solo totales diarios |
| `Sync_Ventas_Historicas` | 2 | ⚠️ | Solo ventana operativa (13:00-11:00) |
| `Finanzas_CortesCaja` | 6 | ⚠️ | FechaApertura/Cierre de turno, no ventas |
| `Comercial_Ventas_Dia_Abiertas_v2` | 0 | - | Sin datos para esta fecha |
| `Venta_Encabezado` | 0 | - | Tabla vacía (no usada para restaurantes) |
| `Sync_Ventas_PorHora` | 0 | - | Sin datos para esta fecha |

### 3.2 Tablas sin datos relevantes

| Tabla | Motivo de Descarte |
|-------|-------------------|
| `Comercial_KPIs_Historico` | Solo agregados, sin hora |
| `Comercial_KPIs_Mensuales_v2` | Solo totales mensuales |
| `Finanzas_CortesCaja_DetallePagos` | Sin registros para la fecha |
| `Venta_Detalle` | Tabla vacía |
| `Venta_Pagos` | Tabla vacía |
| `Inventario_*` | No aplica a ventas |

---

## 4. COLUMNAS HORARIAS ENCONTRADAS

### 4.1 Sync_Ventas_Historicas

```
FechaOperacion: date (2026-05-07)
VentanaInicio: time (13:00:00) ← Configuración de horario operativo
VentanaFin: time (11:00:00)    ← Configuración de horario operativo
VentaTotal: decimal (total del día)
```

**Problema:** `VentanaInicio`/`VentanaFin` son parámetros de configuración de la ventana operativa (13:00-11:00), NO horas reales de ventas individuales. NO permiten reconstruir ventas por hora.

### 4.2 Finanzas_CortesCaja

```
FechaApertura: datetime2 (hora de apertura del turno)
FechaCierre: datetime2 (hora de cierre del turno)
TotalVenta: decimal (total del corte)
```

**Problema:** Representan cortes de caja por turno, NO ventas individuales por hora. Un corte puede abarcar varias horas y no tiene desglose interno.

### 4.3 Comercial_Ventas_Dia_Abiertas_v2

```
snapshot_timestamp: datetime2 (momento del snapshot)
ventas_abiertas: decimal
ventas_cerradas_dia: decimal
```

**Problema:** Sin datos para 2026-05-07. Los snapshots empezaron a capturarse después de esa fecha.

---

## 5. EVIDENCIA DE NO DISPONIBILIDAD

### 5.1 SQL de Diagnóstico Ejecutado

```sql
-- Verificar Sync_Ventas_PorHora para 2026-05-07
SELECT * FROM Sync_Ventas_PorHora WHERE FechaOperacion = '2026-05-07'
-- Resultado: 0 registros

-- Verificar rango de fechas en Sync_Ventas_PorHora
SELECT MIN(FechaOperacion) as min, MAX(FechaOperacion) as max FROM Sync_Ventas_PorHora
-- Resultado: min=2026-05-08, max=2026-05-15

-- Verificar Comercial_Ventas_Dia_Abiertas_v2 para 2026-05-07
SELECT * FROM Comercial_Ventas_Dia_Abiertas_v2 WHERE fecha_operacion = '2026-05-07'
-- Resultado: 0 registros

-- Verificar tablas con cheques/tickets individuales
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME LIKE '%Cheque%' OR TABLE_NAME LIKE '%Ticket%'
-- Resultado: Solo tablas de folios de inventario, no de ventas
```

### 5.2 Datos en Sync_Ventas_Historicas

```
ServerID                              Sistema         VentaTotal   Ventana
1b230a06-ffaf-4c70-bd27-b1be3579dea6  MPRO           $98,938.00   13:00-11:00
a5547321-1139-4d2b-9d53-182ca737b6b6  SoftRestaurant $87,372.00   13:00-11:00
```

**Observación:** Solo 2 registros con totales diarios, sin desglose por hora.

---

## 6. TOTALES POR UNIDAD (Comercial_KPIs_Diarios_v2)

| Unidad | Ventas 2026-05-07 |
|--------|-------------------|
| 130MID | $87,372.00 |
| 130QRO | $108,698.00 |
| CIENFUEGOS | $110,108.00 |
| ESTELAR | $157,920.00 |
| ORIGEN | $61,820.31 |
| **TOTAL** | **$525,918.31** |

**Nota:** Estos totales son correctos pero NO tienen desglose por hora.

---

## 7. COMPARACIÓN CON Sync_Ventas_PorHora

| Fuente | Total 2026-05-07 | Horas |
|--------|------------------|-------|
| `Comercial_KPIs_Diarios_v2` | $525,918.31 | No aplica |
| `Sync_Ventas_PorHora` | $0.00 | 0 horas |

**Diferencia:** El día 2026-05-07 nunca fue sincronizado a `Sync_Ventas_PorHora`.

---

## 8. CAUSA RAÍZ DEL FALTANTE

El job de sincronización de ventas por hora (`Sync_Ventas_PorHora`) **comenzó a ejecutarse desde 2026-05-08**. El día 2026-05-07 y anteriores nunca tuvieron captura de datos por hora.

**Evidencia:**
```
Rango de Sync_Ventas_PorHora: 2026-05-08 a 2026-05-15
Días con datos: 8
2026-05-07: NO EXISTE
```

---

## 9. RECOMENDACIÓN FINAL

### Veredicto: ❌ NO ES POSIBLE RECONSTRUIR

**Razón:** No existe ninguna fuente de datos en EDARSAHUB SQL que contenga el desglose de ventas por hora para el día 2026-05-07.

**Opciones descartadas:**
| Opción | Motivo de Descarte |
|--------|-------------------|
| Extraer de SoftRestaurant/MPRO origen | Prohibido por directiva |
| Crear datos sintéticos | Prohibido - violaría integridad |
| Distribuir total diario en horas | Prohibido - datos falsos |

### Acción Tomada

1. **Documentado** como "DATOS HORARIOS NO DISPONIBLES"
2. **Sin impacto** en Tablero Ejecutivo (usa `Comercial_KPIs_Diarios_v2` que SÍ tiene datos)
3. **Sin impacto** en proyección mensual (totales diarios correctos)

---

## 10. VALIDACIÓN DE NO REGRESIÓN

| Validación | Resultado |
|------------|-----------|
| Tablero Ejecutivo carga | ✅ |
| 5 unidades con DATA_OK | ✅ |
| source_period = EDARSAHUB_SQL | ✅ |
| Proyección mensual correcta | ✅ |
| Comercial V2 HTTP 200 | ✅ |
| Totales diarios correctos | ✅ |

---

## 11. CRITERIOS DE ACEPTACIÓN

| Criterio | Estado |
|----------|--------|
| No se usaron conexiones LIVE | ✅ CUMPLIDO |
| No se usó MongoDB como fuente | ✅ CUMPLIDO |
| Se revisaron tablas internas EDARSAHUB | ✅ CUMPLIDO (240 tablas) |
| Si existe detalle horario → proponer backfill | ❌ NO EXISTE |
| Si no existe → documentar | ✅ CUMPLIDO |
| No se modificó ningún dato | ✅ CUMPLIDO |

---

## 12. CONCLUSIÓN

El día **2026-05-07** queda documentado como:

```
DATOS HORARIOS NO DISPONIBLES EN EDARSAHUB SQL
- Totales diarios: ✅ DISPONIBLES en Comercial_KPIs_Diarios_v2
- Desglose por hora: ❌ NO DISPONIBLE (nunca fue sincronizado)
- Impacto operativo: NINGUNO (Tablero Ejecutivo no requiere datos por hora)
```

---

**Autor:** Sistema E1  
**Validado:** 2026-05-17 12:00 UTC  
**Próxima Acción:** Ninguna requerida. El backfill no es posible sin conexión LIVE.
