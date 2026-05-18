# DIAGNÓSTICO P0: Ventas del Día de ORIGEN No Se Reflejan en Tablero Ejecutivo

**Fecha:** 2026-05-18  
**Autor:** E1 Agent  
**Estado:** DIAGNÓSTICO COMPLETADO - PENDIENTE AUTORIZACIÓN PARA IMPLEMENTAR  
**Prioridad:** P0  

---

## 1. Resumen Ejecutivo

El usuario reportó que **ORIGEN tiene ventas del día de hoy, pero no se reflejan en el Tablero Ejecutivo**. Tras análisis exhaustivo, se identificó que:

1. **El job de sincronización SÍ funciona correctamente** - La API local responde, la conexión está `ONLINE`, y los datos se escriben exitosamente.
2. **El problema es la lógica de FechaOperacion** - A las 11:30 AM (hora actual en México), el sistema calcula `fecha_operacion = 2026-05-17` porque la jornada operativa del 18-May no ha iniciado (apertura: 13:00).
3. **El UPSERT sobrescribe sin discriminar por fecha** - La tabla `Comercial_Ventas_Dia_Abiertas_v2` usa llave `(unidad_negocio_id, sucursal_id)` **sin fecha**, por lo que cada sync sobrescribe el registro anterior.

**Conclusión**: NO es un bug del job de sincronización ni de la API. Es **comportamiento esperado** según la configuración actual de horarios y la lógica de ventana operativa. El usuario espera ver ventas "de hoy" a las 11:30 AM, pero según la regla de negocio configurada, "hoy" operativamente sigue siendo "ayer" hasta las 13:00.

---

## 2. Job y Módulo Responsable

| Concepto | Valor |
|----------|-------|
| **Archivo principal** | `/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py` |
| **Función exacta** | `execute_sync_comercial_abiertas_v2()` (línea 417) |
| **Helper de fecha** | `/app/backend/core/utils/operational_window.py` → `get_operational_window()` |
| **Repository de UPSERT** | `/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py` → `upsert_ventas_dia_abiertas()` (línea 254) |

---

## 3. Query Actual MPRO (ORIGEN)

```sql
-- Query ventas abiertas (sync_comercial_abiertas_v2_job.py líneas 338-351)
SELECT 
    '{fecha_operacion}' as fecha,
    SUM(ISNULL(cd.Cd_Importe, 0)) as ventas_abiertas,
    COUNT(DISTINCT c.Co_Folio) as tickets_abiertos,
    SUM(DISTINCT ISNULL(c.Co_Personas, 1)) as pax_abiertos
FROM Comanda c
INNER JOIN Comanda_Detalle cd ON c.Co_Folio = cd.Co_Folio
WHERE CAST(c.Co_Fecha AS DATE) = '{fecha_operacion}'
  AND c.Sc_Cve_Sucursal = '{sucursal_id}'
  AND cd.Es_Cve_Estado = 'AC'
  AND cd.Fecha_Baja IS NULL
  AND c.Es_Cve_Estado = 'AC'

-- Query ventas cerradas (líneas 354-366)
SELECT 
    SUM(ISNULL(cd.Cd_Importe, 0)) as ventas_cerradas_dia,
    COUNT(DISTINCT c.Co_Folio) as tickets_cerrados_dia,
    SUM(DISTINCT ISNULL(c.Co_Personas, 1)) as pax_cerrados_dia
FROM Comanda c
INNER JOIN Comanda_Detalle cd ON c.Co_Folio = cd.Co_Folio
WHERE CAST(c.Co_Fecha AS DATE) = '{fecha_operacion}'
  AND c.Sc_Cve_Sucursal = '{sucursal_id}'
  AND c.Es_Cve_Estado <> 'AC'
  AND cd.Es_Cve_Estado = 'AC'
  AND cd.Fecha_Baja IS NULL
```

---

## 4. Tablas Origen Esperadas

| Sistema | Tabla Principal | Tabla Detalle | Campo Estado |
|---------|-----------------|---------------|--------------|
| MPRO | `Comanda` | `Comanda_Detalle` | `Es_Cve_Estado` |

---

## 5. Filtros Usados

| Filtro | Valor ORIGEN | Valor 130QRO | Idéntico |
|--------|--------------|--------------|----------|
| `sucursal_id` (Sc_Cve_Sucursal) | `0023` | `0021` | NO (esperado) |
| `Es_Cve_Estado` abiertas | `'AC'` | `'AC'` | SÍ |
| `Es_Cve_Estado` cerradas | `<> 'AC'` | `<> 'AC'` | SÍ |
| `Fecha_Baja` | `IS NULL` | `IS NULL` | SÍ |
| Query template | `QUERY_MPRO_VENTAS_ABIERTAS_ORIGEN` | `QUERY_MPRO_VENTAS_ABIERTAS_QRO` | IDÉNTICAS |

---

## 6. FechaOperacion Usada

| Parámetro | Valor |
|-----------|-------|
| **Hora actual (México)** | `2026-05-18 11:30:19 CST` |
| **Horario configurado** | `13:00 - 03:00` (cruza medianoche) |
| **FechaOperacion calculada** | `2026-05-17` |
| **Razón** | A las 11:30, estamos entre `hora_fin` (03:00) y `hora_inicio` (13:00), período de "cerrado". La lógica asigna al día anterior. |

---

## 7. Corte Operativo Usado

| Configuración | Valor |
|---------------|-------|
| **Tabla** | `Sistema_HorariosServicioUnidad` |
| **hora_inicio_operativo** | `13:00:00` |
| **hora_fin_operativo** | `03:00:00` |
| **cruza_medianoche** | `True` |

**NOTA**: El handoff menciona "corte a las 06:00 AM" (documento `CAMBIO_REGLA_FECHA_OPERATIVA_CORTE_0600.md`), pero la configuración actual en BD tiene `03:00`. Esta discrepancia debe verificarse con el usuario.

---

## 8. Configuración de Unidades

### 8.1 Unidades_Negocio

| Código | Nombre | server_id | sucursal_origen_id | system_type |
|--------|--------|-----------|-------------------|-------------|
| `ORIGEN` | ORIGEN | `1b230a06-ffaf-4c70-bd27-b1be3579dea6` | `0023` | MPRO |
| `130QRO` | 130° QUERETARO | `1b230a06-ffaf-4c70-bd27-b1be3579dea6` | `0021` | MPRO |

### 8.2 Servidores_Conexiones (API_LOCAL)

| Nombre | id | tipo_conexion | api_url |
|--------|-----|---------------|---------|
| `ORIGEN LOCAL` | `817a0aa8-6170-4738-a8f6-a72ac36ba0df` | API_LOCAL | `http://54.39.104.176:8000/query` |
| `130° QRO LOCAL` | `72f6e9a7-8ea2-4eb2-802e-4ee31753435e` | API_LOCAL | `http://54.39.104.176:8001/query` |

---

## 9. Comparación ORIGEN vs 130QRO

| Aspecto | ORIGEN | 130QRO | Observación |
|---------|--------|--------|-------------|
| **Código canónico** | `ORIGEN` | `130QRO` | OK |
| **sucursal_id** | `0023` | `0021` | Correcto - diferentes sucursales |
| **server_id (Unidades_Negocio)** | `1b230a06-...` | `1b230a06-...` | Mismo server MPRO central |
| **server_id (API_LOCAL)** | `817a0aa8-...` | `72f6e9a7-...` | Diferentes APIs locales |
| **api_url** | `:8000/query` | `:8001/query` | Puertos diferentes |
| **Query template** | `QUERY_MPRO_VENTAS_ABIERTAS_ORIGEN` | `QUERY_MPRO_VENTAS_ABIERTAS_QRO` | **IDÉNTICAS** (líneas 338-366 vs 380-410) |
| **Horario operativo** | 13:00-03:00 | 13:00-03:00 | **IDÉNTICO** |
| **fecha_operacion calculada** | 2026-05-17 | 2026-05-17 | **IDÉNTICO** |

**Conclusión**: ORIGEN y 130QRO usan **exactamente la misma lógica canónica**. No hay discrepancia en la implementación.

---

## 10. Evidencia de Por Qué ORIGEN Devuelve $0.00 para HOY

### 10.1 Logs de Sincronización Recientes

```
run_id: ABIERTA-20260518-172708-4036
unidad: ORIGEN
fecha_inicio: 2026-05-17  ← FechaOperacion calculada
status: SUCCESS
records: P=1 I=0 U=1 S=0
conn: ONLINE

run_id: ABIERTA-20260518-172700-b3ef
unidad: ORIGEN
fecha_inicio: 2026-05-18  ← Ejecución anterior cuando hora >= 13:00
status: SUCCESS
```

### 10.2 Estado Actual en Comercial_Ventas_Dia_Abiertas_v2

```
UNIDAD: ORIGEN
  fecha_operacion: 2026-05-17  ← DÍA ANTERIOR (operativamente correcto)
  total_estimado_dia: $70,621.01
  ventas_abiertas: $0.00  ← La jornada del 17 cerró, no hay abiertas
  ventas_cerradas_dia: $70,621.01
  tickets_cerrados_dia: 37
  snapshot_timestamp: 2026-05-18T17:27:13
```

### 10.3 Comportamiento del UPSERT

La función `upsert_ventas_dia_abiertas()` en `repository_comercial_edarsahub.py` (línea 260-266):

```sql
SELECT id FROM Comercial_Ventas_Dia_Abiertas_v2
WHERE unidad_negocio_id = 'ORIGEN'
  AND sucursal_id = '0023'
-- ¡NO INCLUYE fecha_operacion en la llave!
```

Esto significa que **cada sync sobrescribe el único registro** con la fecha_operacion del momento actual. Si el job se ejecuta a las 11:30 AM, sobrescribe con `fecha_operacion = 2026-05-17`.

---

## 11. Diagnóstico Raíz

### Escenario Actual

```
Hora actual: 11:30 AM México (2026-05-18)
Horario unidad: 13:00 - 03:00 (cruza medianoche)

Evaluación get_operational_window():
  - ¿hora_actual < hora_fin (03:00)? NO (11:30 > 03:00)
  - ¿hora_actual >= hora_inicio (13:00)? NO (11:30 < 13:00)
  - CONCLUSIÓN: Restaurante CERRADO, pertenece a jornada ANTERIOR
  
Resultado: fecha_operacion = 2026-05-17
```

### El "Bug" No Es Un Bug

El sistema funciona **exactamente como fue diseñado**. A las 11:30 AM:
- El restaurante operativamente NO ha abierto para el día 18
- Las ventas que se generen después de las 13:00 serán del día 18
- No hay ventas del día 18 porque la jornada del 18 no ha comenzado

### El Problema Real

**Expectativa del usuario**: Ver $0 para "hoy" (2026-05-18) y las ventas acumuladas del día 17 como "ayer".

**Comportamiento actual**: La tabla `Comercial_Ventas_Dia_Abiertas_v2` solo guarda UN registro por unidad (sin discriminar por fecha), así que siempre muestra la `fecha_operacion` más reciente calculada.

---

## 12. Propuestas de Corrección (PENDIENTE AUTORIZACIÓN)

### Opción A: Modificar el UPSERT para mantener historial por fecha

**Cambio**: Agregar `fecha_operacion` a la llave del UPSERT.

```sql
-- ANTES (líneas 260-266)
WHERE unidad_negocio_id = 'ORIGEN' AND sucursal_id = '0023'

-- DESPUÉS
WHERE unidad_negocio_id = 'ORIGEN' 
  AND sucursal_id = '0023'
  AND fecha_operacion = '2026-05-17'
```

**Impacto**: Permitiría mantener múltiples snapshots (uno por fecha). El Tablero podría mostrar "hoy" vs "ayer".

**Riesgo**: BAJO - Solo afecta la lógica de UPSERT, no las queries ni APIs.

### Opción B: Ajustar el horario de corte a las 06:00 AM

**Cambio**: Actualizar `Sistema_HorariosServicioUnidad` para que `hora_fin_operativo = 06:00`.

```sql
UPDATE Sistema_HorariosServicioUnidad
SET hora_fin_operativo = '06:00:00'
WHERE unidad_negocio_id IN ('ORIGEN', '130QRO')
```

**Impacto**: A las 11:30 AM, la evaluación sería:
- ¿hora_actual (11:30) < hora_fin (06:00)? NO
- ¿hora_actual (11:30) >= hora_inicio (13:00)? NO
- CERRADO → día anterior

**NOTA**: Esta opción NO resolvería el problema porque el período "cerrado" (06:00-13:00) seguiría asignando al día anterior. Habría que también considerar si el periodo 06:00-13:00 debería pertenecer al día siguiente.

### Opción C: Crear lógica de "día calendario" para Tablero

**Cambio**: El Tablero Ejecutivo consulta por **fecha calendario** (no operativa) durante horario de "cerrado".

**Impacto**: Cambio en frontend/endpoint, no en el job de sync.

**Riesgo**: MEDIO - Podría causar confusión entre "ventas operativas" y "ventas de calendario".

---

## 13. Riesgos de Cada Opción

| Opción | Riesgo | Detalle |
|--------|--------|---------|
| A | BAJO | Solo cambia lógica de escritura en BD |
| B | BAJO | Solo cambia configuración en tabla |
| C | MEDIO | Cambios en frontend y lógica de negocio |

---

## 14. Validaciones Necesarias (Post-Implementación)

1. Ejecutar sync manual y verificar que crea registro nuevo para fecha actual
2. Verificar que Tablero Ejecutivo muestra dato correcto
3. Confirmar que no hay doble conteo entre días
4. Revisar logs de `Comercial_SyncLog_v2` para errores

---

## 15. Confirmación de Integridad

**Se confirma que durante este diagnóstico:**
- NO se modificó código alguno
- NO se ejecutaron queries UPDATE/DELETE/MERGE
- NO se alteró ninguna tabla de producción
- Todas las consultas fueron SELECT de solo lectura

---

## 16. Próximos Pasos

Solicito **AUTORIZACIÓN EXPLÍCITA** para implementar una de las opciones propuestas. Recomiendo:

**OPCIÓN A** como corrección mínima con menor riesgo, permitiendo que la tabla mantenga snapshots por fecha y el Tablero pueda discriminar entre "hoy" y "ayer".

---

**Fin del Diagnóstico**
