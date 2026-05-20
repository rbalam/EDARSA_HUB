# MATRIZ DEFINITIVA — VENTAS DEL DÍA
## SoftRestaurant / MPRO / Turnos / FechaOperacion / EDARSAHUB

**Documento**: MATRIZ_DEFINITIVA_VENTAS_DIA_SOFTRESTAURANT_MPRO_TURNOS.md  
**Fecha**: 2026-05-20  
**Versión**: 1.0  
**Estado**: DISEÑO APROBADO — PENDIENTE IMPLEMENTACIÓN POR FASES

---

## 1. DEFINICIÓN OFICIAL DE VENTAS DEL DÍA

### 1.1 Concepto Operativo

**Ventas del Día** NO significa ventas de 00:00 a 23:59 calendario.

**Ventas del Día** significa:
> Las ventas que pertenecen al **periodo operativo real** de una unidad de negocio, determinado por turno/corte/apertura/captura y validado contra la configuración operativa de EDARSAHUB.

### 1.2 Regla de FechaOperacion

| Criterio | ¿Define FechaOperacion? |
|----------|-------------------------|
| Fecha de turno/corte de apertura | ✅ SÍ (cuando es confiable) |
| Fecha/hora de apertura de cuenta | ✅ SÍ (fallback cuando corte extendido) |
| Fecha/hora de captura de comanda | ✅ SÍ (fallback cuando corte extendido) |
| Configuración operativa por unidad | ✅ SÍ (validación/clasificación) |
| Fecha de cierre/cobro | ❌ NO define FechaOperacion |
| Fecha del servidor local | ❌ NO usar |
| GETDATE() | ❌ NO usar |
| UTC como fecha final | ❌ NO usar |
| datetime.now() sin timezone | ❌ NO usar |

### 1.3 Zona Horaria Oficial

**OBLIGATORIA**: `America/Mexico_City`

```python
from zoneinfo import ZoneInfo
MEXICO_TZ = ZoneInfo("America/Mexico_City")
```

---

## 2. MATRIZ FUNCIONAL — SOFTRESTAURANT

### 2.1 Flujo Operativo

```
1. Abrir turno/corte de caja
2. El turno tiene fecha_turno
3. Se abren mesas
4. Se capturan comandas en comandero
5. Las comandas se acumulan a la mesa
6. Cuenta sin folio definitivo mientras está abierta
7. Folio de cuenta se asigna al cobrar/cerrar
8. Cuentas abiertas en turno deben cerrarse en ese turno (ideal)
9. Operación puede cruzar medianoche
10. Cuentas cobradas en madrugada pertenecen al turno original
```

### 2.2 Reglas de FechaOperacion — SoftRestaurant

**Método recomendado**: `MIXTO_VALIDADO`

| Prioridad | Condición | Acción |
|-----------|-----------|--------|
| 1 | Turno/corte dentro de ventana operativa | Usar fecha del turno/corte |
| 2 | Turno/corte extendido o mezcla periodos | Usar fecha/hora de apertura/captura |
| 3 | Validación adicional | Configuración operativa por unidad |

### 2.3 Tablas Origen — SoftRestaurant

| Tabla | Contenido | Uso |
|-------|-----------|-----|
| `tempcheques` | Cuentas del corte vigente (abiertas y recién cerradas) | Ventas en proceso |
| `cheques` | Cuentas históricas (después del cierre de corte) | Ventas cerradas |

**REGLA CRÍTICA**: NO calcular Ventas del Día ÚNICAMENTE desde `tempcheques`.

### 2.4 Escenarios SoftRestaurant

#### Escenario A: Operación Normal
```
- Corte del día 20
- Cuenta abierta: 20 a las 15:00
- Cuenta cobrada: 21 a la 01:23
- FechaOperacion = 2026-05-20 ✅
```

#### Escenario B: Cuenta cerrada días después
```
- Cuenta abierta en turno/corte del 20
- No se cerró el corte
- Cuenta cobrada/cancelada el 22
- FechaOperacion = 2026-05-20 ✅
- Importe se actualiza con valor final
- NO mover a FechaOperacion 22
```

#### Escenario C: Corte no cerrado con cuentas nuevas
```
- Corte del 20 queda abierto
- El 21 se abren cuentas nuevas dentro del mismo corte
- Cuentas nuevas del 21 NO pertenecen al 20
- FechaOperacion = 2026-05-21 (según apertura/captura)
- Generar alerta: TURNO_EXTENDIDO
```

#### Escenario D: Corte cerrado, tempcheques vacío
```
- Corte del 20 cerrado
- tempcheques queda en cero
- Cuentas migradas a cheques
- Ventas del Día deben leerse de cheques
- FechaOperacion = 2026-05-20 ✅
```

### 2.5 Reconciliación Posterior — SoftRestaurant

Cuando una cuenta se cierra/cobra/cancela/bonifica DESPUÉS de la FechaOperacion original:

1. FechaOperacion **NO CAMBIA**
2. Importe **SÍ SE ACTUALIZA** al valor final
3. Estado se actualiza (cerrada, cancelada, bonificada)
4. Trazabilidad obligatoria
5. No duplicar, no perder

---

## 3. MATRIZ FUNCIONAL — MPRO

### 3.1 Flujo Operativo

```
1. Abrir turno/corte (si aplica)
2. Se abren mesas → Comanda
3. Se capturan productos → Comanda_Detalle
4. Las comandas activas tienen estado 'AC'
5. Al cerrar, cambia estado o se marca Fecha_Baja
6. Si no se cierra el turno, se mezclan días
```

### 3.2 Reglas de FechaOperacion — MPRO

**Método recomendado**: `MIXTO_VALIDADO`

| Prioridad | Condición | Acción |
|-----------|-----------|--------|
| 1 | Turno cerrado correctamente | Usar fecha del turno |
| 2 | Turno abierto > 1 día o mezcla ventas | Usar fecha/hora de captura (Co_Fecha) |
| 3 | Validación | Configuración de turnos por unidad |

### 3.3 Tablas Origen — MPRO

| Tabla | Columnas Clave | Uso |
|-------|----------------|-----|
| `Comanda` | Co_Folio, Co_Fecha, Co_Personas, Es_Cve_Estado, Sc_Cve_Sucursal | Mesa/cuenta |
| `Comanda_Detalle` | Co_Folio, Cd_Importe, Es_Cve_Estado, Fecha_Baja | Items vendidos |

### 3.4 Escenarios MPRO

#### Escenario ORIGEN — Día Normal
```
Hora: 08:00 → turno=DESAYUNO, FechaOperacion=HOY
Hora: 14:00 → turno=COMIDA, FechaOperacion=HOY
Hora: 20:00 → turno=CENA, FechaOperacion=HOY
Hora: 02:30 (siguiente) → turno=CENA, FechaOperacion=DÍA_ANTERIOR
Hora: 07:10 (siguiente) → turno=DESAYUNO, FechaOperacion=HOY
```

#### Escenario MPRO — Turno Extendido
```
- Turno del 20 no se cerró
- El 21 a las 07:00 inicia desayuno
- MPRO sigue con turno del 20 abierto
- Ventas del 21 07:00-13:00 = FechaOperacion 21 (no 20)
- Generar alerta: TURNO_EXTENDIDO o POSIBLE_MEZCLA_DIAS
```

#### Escenario 130QRO — Sin Desayuno
```
Hora: 12:53 → Desayuno inactivo → FechaOperacion = DÍA_ANTERIOR
Hora: 13:05 → turno=COMIDA → FechaOperacion = HOY
Hora: 02:00 (siguiente) → turno=CENA → FechaOperacion = DÍA_ANTERIOR
```

---

## 4. SEPARACIÓN DE TURNOS — DESAYUNO / COMIDA / CENA

### 4.1 Configuración Inicial

| Turno | Hora Inicio | Hora Fin | Cruza Medianoche |
|-------|-------------|----------|------------------|
| DESAYUNO | 07:00 | 13:00 | NO |
| COMIDA | 13:01 | 18:59 | NO |
| CENA | 19:00 | 05:59 | SÍ |

### 4.2 Configuración por Unidad

| Unidad | DESAYUNO | COMIDA | CENA |
|--------|----------|--------|------|
| ORIGEN | ✅ Activo | ✅ Activo | ✅ Activo |
| 130QRO | ❌ Preparado | ✅ Activo | ✅ Activo |
| 130MID | ❌ Preparado | ✅ Activo | ✅ Activo |
| CIENFUEGOS | ❌ Preparado | ✅ Activo | ✅ Activo |
| ESTELAR | ❌ Preparado | ✅ Activo | ✅ Activo |

### 4.3 Clasificación Sin Corte de Caja

**REGLA**: Si el sistema origen NO genera corte de caja entre comida y cena, EDARSAHUB clasifica internamente por fecha/hora de apertura/captura.

```
Captura entre 13:01 y 18:59 → COMIDA
Captura entre 19:00 y 05:59 → CENA
```

### 4.4 Tolerancia de Horarios

```sql
-- Campos en Sistema_TurnosOperativosUnidad
tolerancia_inicio_minutos INT DEFAULT 5
tolerancia_fin_minutos INT DEFAULT 30
```

Ejemplo: Cuenta abierta a las 12:58 con tolerancia de 5 min → se clasifica como COMIDA (no falla).

---

## 5. ESTRUCTURA DE DATOS EXISTENTE

### 5.1 Tablas Existentes en EDARSAHUB

| Tabla | Estado | Uso |
|-------|--------|-----|
| `Sistema_TurnosOperativosUnidad` | ✅ EXISTE | Configuración turnos por unidad |
| `Sistema_HorariosServicioUnidad` | ✅ EXISTE | Horarios por día de semana |
| `Unidades_Negocio` | ✅ EXISTE | Catálogo de unidades |
| `Comercial_Ventas_Dia_Abiertas_v2` | ✅ EXISTE | Snapshot de ventas del día |
| `Servidores_Conexiones` | ✅ EXISTE | Conexiones SQL/API |

### 5.2 Sistema_TurnosOperativosUnidad (Existente)

```sql
-- Estructura actual
turno_operativo_id UNIQUEIDENTIFIER
unidad_negocio_id NVARCHAR(50)
turno_codigo NVARCHAR(50)        -- 'DESAYUNO', 'COMIDA_CENA', etc.
turno_nombre NVARCHAR(100)
hora_inicio TIME
hora_fin TIME
cruza_medianoche BIT
aplica_ventas_dia BIT
es_turno_principal BIT
orden INT
activo BIT
fecha_creacion DATETIME2
creado_por NVARCHAR(100)
fecha_modificacion DATETIME2
modificado_por NVARCHAR(100)
```

**Datos actuales**:
- ORIGEN: DESAYUNO ✅ activo, COMIDA_CENA ✅ activo
- 130QRO: DESAYUNO ❌ inactivo, COMIDA_CENA ✅ activo
- CIENFUEGOS: DESAYUNO ❌ inactivo, COMIDA_CENA ✅ activo
- ESTELAR: DESAYUNO ❌ inactivo, COMIDA_CENA ✅ activo

### 5.3 Comercial_Ventas_Dia_Abiertas_v2 (Existente)

```sql
-- Estructura actual
id UNIQUEIDENTIFIER
unidad_negocio_id NVARCHAR(50)
unidad_negocio_nombre NVARCHAR(200)
server_id NVARCHAR(100)
sucursal_id NVARCHAR(100)
sucursal_nombre NVARCHAR(200)
sistema_origen NVARCHAR(50)
snapshot_timestamp DATETIME2
fecha_operacion DATE
ventas_abiertas DECIMAL(18,2)
tickets_abiertos INT
pax_abiertos INT
ventas_cerradas_dia DECIMAL(18,2)
tickets_cerrados_dia INT
pax_cerrados_dia INT
total_estimado_dia DECIMAL(18,2)
fuente_original NVARCHAR(50)
sync_run_id NVARCHAR(100)
fecha_ultima_actualizacion DATETIME2
```

### 5.4 Propuesta de Campos Adicionales (SIN CREAR)

Para soportar la clasificación por turno, se propone agregar:

```sql
-- Campos propuestos para Sistema_TurnosOperativosUnidad
tolerancia_inicio_minutos INT DEFAULT 5
tolerancia_fin_minutos INT DEFAULT 30

-- Campos propuestos para Comercial_Ventas_Dia_Abiertas_v2
turno_operativo_codigo NVARCHAR(50)  -- 'DESAYUNO', 'COMIDA', 'CENA'
alerta_codigo NVARCHAR(50)           -- 'TURNO_EXTENDIDO', 'MEZCLA_DIAS'
```

**NOTA**: NO crear sin autorización adicional.

---

## 6. ARCHIVOS DE CÓDIGO A REFACTORIZAR

### 6.1 operational_window.py

**Ubicación**: `/app/backend/core/utils/operational_window.py`

**Estado actual**:
- ✅ Ya usa `America/Mexico_City`
- ✅ Ya consulta `Sistema_HorariosServicioUnidad`
- ⚠️ NO consulta `Sistema_TurnosOperativosUnidad`
- ⚠️ Fallback hardcodeado a 13:00-06:00

**Cambios requeridos**:
1. Integrar consulta a `Sistema_TurnosOperativosUnidad`
2. Calcular FechaOperacion basada en turnos configurados por unidad
3. Eliminar fallback hardcodeado
4. Agregar función para detectar turno activo (DESAYUNO/COMIDA/CENA)

### 6.2 sync_comercial_abiertas_v2_job.py

**Ubicación**: `/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py`

**Estado actual**:
- ✅ Ya usa `get_operational_window()` de México
- ✅ Ya consulta `tempcheques` y `cheques`
- ⚠️ NO detecta turnos extendidos
- ⚠️ NO clasifica por turno operativo
- ⚠️ NO maneja reconciliación de cuentas cerradas posteriormente

**Cambios requeridos**:
1. Integrar clasificación por turno (DESAYUNO/COMIDA/CENA)
2. Detectar turnos extendidos y mezcla de días
3. Generar alertas cuando corresponda
4. Para SoftRestaurant: reconciliar `tempcheques` + `cheques`
5. Para MPRO: validar Co_Fecha vs turno esperado

---

## 7. APLICACIÓN A TABLERO EJECUTIVO Y COMERCIAL

### 7.1 Estado Actual de Endpoints

| Endpoint | Fuente | Estado |
|----------|--------|--------|
| `GET /api/comercial/tablero-ejecutivo` | EDARSAHUB SQL (HUB) + Fallback EDARSAHUB (LIVE-C) | ✅ AUDITADO |
| `GET /api/v2/comercial/dashboard` | EDARSAHUB SQL | ✅ OK |
| `GET /api/v2/comercial/ventas-dia` | EDARSAHUB SQL | ✅ OK |

### 7.2 Verificación de Fuentes (COMPLETADA)

**`/api/v2/comercial/ventas-dia`** (línea 1133):
```python
# Lee desde Comercial_Ventas_Dia_Abiertas_v2 (EDARSAHUB SQL) ✅
datos = get_ventas_dia_abiertas(fecha, unidades_permitidas)
```

**`/api/comercial/tablero-ejecutivo`** (línea 428):
```python
# AUDITORÍA COMPLETADA (2026-05-20):
# - Modo HUB (acumulado): Lee de EDARSAHUB SQL via get_kpis_softrestaurant() ✅
# - Modo LIVE-C (ventas del día): 
#   - Intenta conexión live (tempcheques)
#   - Fallback a EDARSAHUB snapshot (get_ventas_dia_snapshot_from_edarsahub)
# - source_period = "EDARSAHUB_SQL" para modo HUB ✅
# - FechaOperacion calculada con America/Mexico_City y corte 06:00 ✅
```

### 7.3 Hallazgos de la Auditoría

**Tablero Ejecutivo - Arquitectura Actual**:

| Modo | Fuente Primaria | Fallback | FechaOperacion |
|------|-----------------|----------|----------------|
| HUB (acumulado) | EDARSAHUB SQL | N/A | Por unidad ✅ |
| LIVE-C (ventas día) | tempcheques (live) | EDARSAHUB snapshot | Corte 06:00 ✅ |

**OBSERVACIÓN CRÍTICA**:
El modo LIVE-C (ventas del día) aún intenta conexión live a `tempcheques` antes de usar el fallback EDARSAHUB. Esto podría causar discrepancias con el Tablero Comercial V2 que SIEMPRE lee de EDARSAHUB.

### 7.4 Regla Obligatoria

> **El Tablero Ejecutivo y el Tablero Comercial DEBEN usar la MISMA fuente (EDARSAHUB SQL) y la MISMA lógica de FechaOperacion.**

| Requisito | Tablero Ejecutivo | Tablero Comercial V2 |
|-----------|-------------------|----------------------|
| Lee EDARSAHUB SQL | ✅ SÍ (modo HUB) | ✅ SÍ |
| No consulta live | ⚠️ Aún consulta live en modo LIVE-C | ✅ SÍ |
| No usa MongoDB | ⚠️ Usa para caché/circuit breaker | ✅ SÍ |
| Usa FechaOperacion por unidad | ✅ SÍ (corte 06:00) | ✅ SÍ |
| Usa America/Mexico_City | ✅ SÍ | ✅ SÍ |

### 7.5 Recomendación de Unificación

**PROPUESTA**: Eliminar la consulta live en modo LIVE-C del Tablero Ejecutivo para que AMBOS tableros lean EXCLUSIVAMENTE de EDARSAHUB SQL.

Beneficios:
1. Consistencia de datos entre tableros
2. Sin discrepancias por conexiones fallidas
3. Única fuente de verdad: EDARSAHUB
4. Menor complejidad de código

**ESTADO**: Pendiente autorización para unificar.

---

## 8. PLAN DE IMPLEMENTACIÓN POR FASES

### FASE 1: Consolidar Estructura (DONE)
- [x] Tabla `Sistema_TurnosOperativosUnidad` creada
- [x] Datos iniciales de turnos insertados
- [x] API backend para configuración operativa
- [x] UI frontend en Catálogos/Unidades

### FASE 2: Separar COMIDA y CENA
- [ ] Modificar `Sistema_TurnosOperativosUnidad` para tener COMIDA y CENA separados
- [ ] Actualizar configuración por unidad
- [ ] UI para editar horarios de cada turno

### FASE 3: Refactorizar operational_window.py
- [ ] Integrar consulta a turnos por unidad
- [ ] Eliminar hardcode 13:00-06:00
- [ ] Función para detectar turno activo
- [ ] Pruebas unitarias

### FASE 4: Refactorizar sync_comercial_abiertas_v2_job.py
- [ ] Clasificación por turno operativo
- [ ] Detección de turnos extendidos
- [ ] Alertas (TURNO_EXTENDIDO, MEZCLA_DIAS)
- [ ] Para SoftRestaurant: reconciliar tempcheques + cheques

### FASE 5: Auditar Tablero Ejecutivo
- [ ] Verificar fuentes de datos
- [ ] Eliminar consultas live si existen
- [ ] Unificar con lógica de V2

### FASE 6: Validación E2E
- [ ] Escenarios SoftRestaurant
- [ ] Escenarios MPRO
- [ ] Comparativo Tablero Ejecutivo vs Comercial V2

### FASE 7: Tabla de Detalle (OPCIONAL)
- [ ] Si se requiere reconciliación a nivel cuenta
- [ ] Diseñar `Comercial_Ventas_Dia_Detalle_v2`
- [ ] NO crear sin autorización

---

## 9. RIESGOS Y MITIGACIÓN

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Turnos no cerrados en origen | Alta | Alto | Detección automática + alertas |
| Mezcla de días en un corte | Media | Alto | Clasificación por apertura/captura |
| Cuentas cerradas días después | Alta | Medio | Reconciliación sin mover FechaOperacion |
| tempcheques vacío después del corte | Alta | Alto | Consultar también cheques |
| Diferencia entre tableros | Media | Alto | Auditoría y unificación de fuentes |
| Horarios no configurados | Baja | Medio | Fallback inteligente + alerta |

---

## 10. CRITERIOS DE ACEPTACIÓN

1. **FechaOperacion** calculada SIEMPRE con `America/Mexico_City`
2. **Turnos configurables** desde UI sin tocar código
3. **Clasificación interna** por turno aunque no haya corte de caja
4. **Sin $0 falso** si falla conexión al origen
5. **Reconciliación** de cuentas cerradas posteriormente
6. **Alertas** para turnos extendidos
7. **Tableros alineados**: misma fuente, misma lógica
8. **Documentación completa** de cada cambio

---

## 11. AUTORIZACIÓN REQUERIDA

Para proceder con cada fase, se requiere autorización explícita del usuario.

| Fase | Estado |
|------|--------|
| FASE 1 | ✅ COMPLETADA |
| FASE 2 | ⏳ PENDIENTE AUTORIZACIÓN |
| FASE 3 | ⏳ PENDIENTE AUTORIZACIÓN |
| FASE 4 | ⏳ PENDIENTE AUTORIZACIÓN |
| FASE 5 | ⏳ PENDIENTE AUTORIZACIÓN |
| FASE 6 | ⏳ PENDIENTE AUTORIZACIÓN |
| FASE 7 | ⏳ PENDIENTE AUTORIZACIÓN |

---

## 12. REFERENCIAS

- `/app/backend/core/utils/operational_window.py`
- `/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py`
- `/app/backend/modules/comercial_v2/routes.py`
- `/app/backend/modules/comercial/routes.py`
- `/app/backend/api/configuracion_operativa_unidades.py`
- `/app/frontend/src/pages/ConfiguracionOperativaUnidades.jsx`

---

**FIN DEL DOCUMENTO**

*Generado por E1 Agent — 2026-05-20*
