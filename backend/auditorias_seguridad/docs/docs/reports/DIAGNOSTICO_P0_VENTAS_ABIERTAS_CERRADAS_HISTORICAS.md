# DIAGNÓSTICO P0: Ventas Abiertas, Cerradas e Históricas

**Fecha**: 2026-05-15 02:10 AM (México)  
**Estado**: DIAGNÓSTICO COMPLETADO (Sin modificaciones de código)  
**Prioridad**: P0 (Crítico)

---

## 1. Resumen Ejecutivo

Se identificaron **TRES causas raíz** del problema recurrente de $0:

1. **Cálculo incorrecto de FechaOperacion**: El job está escribiendo `fecha_operacion=2026-05-15` cuando debería escribir `fecha_operacion=2026-05-14` (a las 02:04 AM, la jornada del día 14 sigue vigente hasta las 03:00).

2. **HTTP 401 de API Local ORIGEN**: La API local de ORIGEN está rechazando requests con error de autorización, causando que el job no obtenga datos y escriba $0.

3. **Protección anti-$0 tiene brecha**: Cuando la `fecha_operacion` calculada difiere de la existente, la protección permite escribir $0 asumiendo que es "nuevo día", pero el cálculo de fecha es incorrecto.

---

## 2. Causa Raíz de Ruptura de ORIGEN y 130QRO

### Estado actual en EDARSAHUB (02:04 AM México):

| Unidad | fecha_operacion | Total | Snapshot UTC | 
|--------|-----------------|-------|--------------|
| ORIGEN | 2026-05-15 | $0.00 | 08:02:38 |
| 130QRO | 2026-05-15 | $0.00 | 08:02:38 |

### Problema detectado:

```
Hora México: 02:04 AM del día 15
Ventana operativa ORIGEN: 13:00 - 03:00 (cruza medianoche)
FechaOperacion esperada: 2026-05-14 (día anterior)
FechaOperacion escrita: 2026-05-15 ❌ (día calendario)
```

### Evidencia de logs:

```
*** API Local ORIGEN LOCAL: ERROR - HTTP 401 ***
*** API Local ORIGEN LOCAL: ERROR - HTTP 401 ***
(repetido múltiples veces)
```

### Flujo del bug:

1. Job se ejecuta a las 02:02 AM UTC (08:02 México... NO, espera - UTC 08:02 = México 02:02)
2. `get_operational_window('ORIGEN')` **DEBERÍA** devolver `fecha_operacion=2026-05-14`
3. API Local devuelve HTTP 401 (no autorizado)
4. Job no obtiene datos, calcula total=$0
5. Protección anti-$0 verifica dato existente:
   - Dato existente: `fecha_operacion=2026-05-14, total=$79,988`
   - Fecha nueva: `fecha_operacion=2026-05-15` (calculada incorrectamente)
   - Como las fechas son diferentes, la protección dice "nuevo día, permitir"
6. Job escribe $0 para día 15, sobrescribiendo el registro

### Verificación de `get_operational_window()`:

```python
# Ejecutado a las 02:04 AM México
ORIGEN:
  FechaOperacion: 2026-05-14  ✅ (función calcula correctamente)
  Horario: 13:00:00 - 03:00:00
  Cruza medianoche: True
```

**CONTRADICCIÓN**: La función devuelve día 14, pero la BD tiene día 15. Esto indica que el job NO está pasando el timestamp correctamente o hay un bug en el paso del resultado al upsert.

---

## 3. Causa Raíz de Pérdida de Venta SoftRestaurant al Cerrar Turno

### Diagnóstico necesario (sin acceso a BD SoftRestaurant):

El job actual consulta tablas de SoftRestaurant pero solo considera:
- `TempCheques` (cheques abiertos temporales)
- Posiblemente ignora `Cheques` (tabla definitiva)

**Hipótesis**: Al cerrar turno:
1. Cheques pasan de `TempCheques` a `Cheques`
2. Job solo consulta `TempCheques` (0 cheques abiertos)
3. No consulta `Cheques` para ventas cerradas del día
4. EDARSAHUB queda con $0 porque `ventas_abiertas=0` y `ventas_cerradas=0`

**Confirmación pendiente**: Revisar queries SQL del job para SoftRestaurant.

---

## 4. Estado Actual de Comercial_Ventas_Dia_Abiertas_v2

### Estructura:

| Columna | Tipo | Nullable |
|---------|------|----------|
| id | uniqueidentifier | NOT NULL |
| unidad_negocio_id | nvarchar | NOT NULL |
| unidad_negocio_nombre | nvarchar | NOT NULL |
| server_id | nvarchar | NOT NULL |
| sucursal_id | nvarchar | NOT NULL |
| sistema_origen | nvarchar | NOT NULL |
| snapshot_timestamp | datetime2 | NOT NULL |
| **fecha_operacion** | date | NOT NULL |
| ventas_abiertas | decimal | NULL |
| tickets_abiertos | int | NULL |
| pax_abiertos | int | NULL |
| ventas_cerradas_dia | decimal | NULL |
| tickets_cerrados_dia | int | NULL |
| pax_cerrados_dia | int | NULL |
| total_estimado_dia | decimal | NULL |
| fuente_original | nvarchar | NOT NULL |
| sync_run_id | nvarchar | NULL |

### Limitaciones:

1. **Solo 1 registro por unidad**: No mantiene historial, siempre sobrescribe.
2. **Sin source_status**: No registra si la sincronización fue exitosa o fallida.
3. **Sin last_valid_total**: No guarda el último valor válido conocido.
4. **Sin fecha_apertura_cuenta**: No distingue entre venta abierta y cerrada por fecha de apertura.

### Datos actuales (02:04 AM):

| unidad_negocio_id | fecha_operacion | total_estimado_dia |
|-------------------|-----------------|-------------------|
| 130MID | 2026-05-15 | $177,436.00 |
| 130QRO | 2026-05-15 | $0.00 ❌ |
| CIENFUEGOS | 2026-05-15 | $284,145.00 |
| ESTELAR | 2026-05-15 | $840.00 |
| ORIGEN | 2026-05-15 | $0.00 ❌ |

---

## 5. Tablas Históricas Existentes en EDARSAHUB SQL

| Tabla | Propósito |
|-------|-----------|
| Comercial_Ventas_Dia_Abiertas_v2 | Snapshot actual (1 registro por unidad) |
| Comercial_KPIs_Diarios_v2 | **VACÍA** - Debería tener histórico diario |
| Comercial_KPIs_Mensuales_v2 | KPIs mensuales consolidados |
| Comercial_KPIs_Historico | KPIs históricos legacy |
| Comercial_SyncLog_v2 | Log de sincronizaciones |

### Problema detectado:

`Comercial_KPIs_Diarios_v2` está **VACÍA**. No existe histórico de ventas por día. Esto impide:
- Consultar un día específico
- Consultar rango de fechas
- Recuperar datos del día anterior si la jornada actual falla

---

## 6. Jobs Existentes y Qué Llena Cada Uno

### sync_comercial_abiertas_v2_job.py

- **Frecuencia**: Cada 5 minutos (300 segundos)
- **Llena**: `Comercial_Ventas_Dia_Abiertas_v2`
- **Fuente SR**: Conexión directa a BD SoftRestaurant
- **Fuente MPRO**: API Local HTTP
- **Problema**: Usa `get_operational_window()` pero hay bug en paso de fecha
- **Protección anti-$0**: Implementada pero con brecha

### Otros jobs (no encontrados activos):

- **Job de consolidación diaria**: NO EXISTE
- **Job de histórico**: NO EXISTE
- **Job de cierre de turno**: NO EXISTE

### Verificación de uso de fechas:

```
✅ Usa get_operational_window() en líneas 438 y 604
❌ Usa datetime.now(mexico_tz).date() como fecha_hoy (línea 403)
❌ Posible uso de fecha_hoy en fallbacks de error
```

---

## 7. Endpoints Afectados

| Endpoint | Comportamiento |
|----------|----------------|
| `/api/v2/comercial/ventas-dia` | Lee de EDARSAHUB ✅ |
| `/api/comercial/tablero-ejecutivo` | Lee de EDARSAHUB ✅ |
| `/api/v2/comercial/dashboard` | Error 500 |

### Frontend:

- Tablero Ejecutivo: Lee EDARSAHUB correctamente ✅
- Comercial: Lee EDARSAHUB correctamente ✅
- No hay conexiones LIVE desde frontend ✅

---

## 8. Filtros Actuales y Limitaciones

### Limitaciones detectadas:

1. **No permite consultar día específico**: Solo muestra "Ventas del Día" (jornada actual) o mes.
2. **No permite rango de fechas**: No hay parámetros `fecha_inicio` / `fecha_fin` para histórico.
3. **Histórico vacío**: `Comercial_KPIs_Diarios_v2` no tiene datos.
4. **Sin modo "jornada cerrada"**: Si la jornada cerró, no hay forma de ver la venta definitiva.

### Filtros en frontend:

- Selector de Mes(es)
- Selector de Año(s)
- Toggle "Ventas del Día" (jornada actual)

### Filtros en backend:

- `/api/v2/comercial/ventas-dia`: Solo fecha actual (no parámetros)
- `/api/comercial/tablero-ejecutivo`: Meses y años seleccionados

---

## 9. Propuesta de Flujo Correcto

### VENTA_ABIERTA_ACTUAL

```
Fuente: API Local / BD SoftRestaurant
Tabla temporal: TempCheques (SR) / Comanda (MPRO)
Sync: Cada 5 minutos
Destino: Comercial_Ventas_Dia_Abiertas_v2
FechaOperacion: Calculada por get_operational_window()
```

### VENTA_CERRADA_DEFINITIVA

```
Fuente: Cheques (SR) / Comanda cerrada (MPRO)
Tabla definitiva: Cheques (SR) / Similar MPRO
Sync: Al detectar cierre de turno O diariamente
Destino: Comercial_KPIs_Diarios_v2 (una fila por unidad/día)
FechaOperacion: Fecha de la jornada cerrada
```

### VENTA_HISTORICA_RANGO

```
Fuente: Comercial_KPIs_Diarios_v2 (EDARSAHUB)
Sync: No requiere (ya consolidado)
Query: WHERE fecha_operacion BETWEEN @inicio AND @fin
Destino: Respuesta API
```

---

## 10. Propuesta de Prioridad de Lectura

Para mostrar ventas del día en tablero:

```
1. Si existe venta_abierta vigente en Comercial_Ventas_Dia_Abiertas_v2
   Y fecha_operacion = fecha_operacion_actual
   Y total > 0
   → Mostrar venta_abierta

2. Si existe venta_cerrada en Comercial_KPIs_Diarios_v2
   Y fecha = fecha_operacion_actual
   → Mostrar venta_cerrada (jornada ya cerró)

3. Si sync_status = FAILED o STALE
   Y existe last_valid_total > 0
   → Mostrar last_valid_total con indicador ⚠️ SYNC_STALE

4. Si no hay dato
   → Mostrar "Sin datos" o "-" (NO $0)
```

---

## 11. Propuesta para Filtros

### Día específico:

```
GET /api/v2/comercial/ventas-historico?fecha=2026-05-10
Fuente: Comercial_KPIs_Diarios_v2
```

### Rango de fechas:

```
GET /api/v2/comercial/ventas-historico?fecha_inicio=2026-05-05&fecha_fin=2026-05-09
Fuente: Comercial_KPIs_Diarios_v2
Respuesta: Desglose por unidad y día
```

### Cualquier mes/año (ya existe):

```
GET /api/comercial/tablero-ejecutivo?meses=04,05&anios=2025,2026
Fuente: Comercial_KPIs_Mensuales_v2 + agregación
```

---

## 12. Riesgos

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| HTTP 401 de ORIGEN | Alto | Verificar API Key / credenciales |
| Bug de fecha_operacion | Alto | Corregir paso de fecha al upsert |
| Tabla histórica vacía | Alto | Implementar job de consolidación |
| Protección anti-$0 con brecha | Alto | Mejorar lógica de protección |
| SoftRestaurant pierde al cerrar | Medio | Query dual (temporal + definitiva) |

---

## 13. Plan de Implementación por Fases

### FASE 1: FIX CRÍTICO (Inmediato)

1. Corregir bug de fecha_operacion en job MPRO
2. Mejorar protección anti-$0:
   - Comparar fecha SOLO con `get_operational_window()` actual
   - Si total=$0 y API falló, NO escribir
3. Verificar credenciales API Local ORIGEN

### FASE 2: Consolidación Histórica (Siguiente)

1. Crear job de consolidación diaria
2. Llenar `Comercial_KPIs_Diarios_v2` con datos históricos
3. Implementar query dual SR (temporal + definitiva)

### FASE 3: Filtros (Posterior)

1. Añadir endpoint `/api/v2/comercial/ventas-historico`
2. Implementar selector de fecha en frontend
3. Implementar selector de rango

### FASE 4: Monitoreo (Final)

1. Alertas cuando sync falla
2. Dashboard de salud de sincronización
3. Indicadores visuales de datos stale

---

## 14. Rollback

Si los cambios causan problemas:

1. Revertir job a versión anterior (git)
2. Restaurar backup de `Comercial_Ventas_Dia_Abiertas_v2_backup_*`
3. Desactivar scheduler: `SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_ENABLED=false`

---

## 15. Validaciones Necesarias

Antes de implementar cualquier fix:

1. ✅ Confirmar que `get_operational_window()` calcula correctamente (VERIFICADO)
2. ⬜ Verificar por qué el job escribe fecha diferente a la calculada
3. ⬜ Verificar credenciales API Local ORIGEN
4. ⬜ Verificar query SQL del job para SoftRestaurant (temporal vs definitiva)
5. ⬜ Confirmar estructura de `Comercial_KPIs_Diarios_v2`

---

## 16. Confirmación: NO se Modificó Código

✅ Este diagnóstico es **PASIVO**.  
✅ No se modificaron archivos de código.  
✅ No se ejecutaron cambios en el job.

---

## 17. Confirmación: NO se Modificó Base de Datos

✅ No se ejecutó DDL.  
✅ No se ejecutó DML.  
✅ No se crearon tablas.  
✅ Solo se ejecutaron SELECT para diagnóstico.

---

## 18. Confirmación: NO se Reactivaron Conexiones LIVE

✅ El frontend sigue leyendo EDARSAHUB SQL.  
✅ No se añadieron llamadas a APIs locales desde tablero.  
✅ No se modificó la arquitectura de lectura.

---

## 19. Confirmación: Solo Fue Diagnóstico

✅ Este documento es resultado de análisis de código y datos.  
✅ No se implementó ningún cambio.  
✅ Esperando autorización para proceder con FASE 1.

---

## Apéndice: Código del Bug Identificado

### Bug en protección anti-$0 (líneas 746-755):

```python
# CÓDIGO ACTUAL CON BUG:
if existing_total > 0:
    if existing_fecha and str(existing_fecha) == fecha_operacion_str:
        continue  # Protección activada
    else:
        # Día diferente - posible inicio de nueva jornada
        logger.info(f"Permitiendo actualización.")  # ❌ PERMITE $0
```

### Problema:
- `existing_fecha = 2026-05-14` (dato válido)
- `fecha_operacion_str = 2026-05-15` (calculada INCORRECTAMENTE)
- Como son diferentes, la protección NO se activa
- Se permite escribir $0

### Fix propuesto:
```python
# PROPUESTA DE FIX:
if total_calculado == 0 and existing_total > 0:
    # NUNCA sobrescribir dato válido con $0, independiente de la fecha
    # Solo permitir $0 si la API respondió correctamente con venta=0 confirmada
    if api_response_status != "SYNC_OK_CONFIRMED_ZERO":
        continue  # NO sobrescribir
```

---

**FIN DEL DIAGNÓSTICO**

Esperando autorización para proceder con FASE 1.
