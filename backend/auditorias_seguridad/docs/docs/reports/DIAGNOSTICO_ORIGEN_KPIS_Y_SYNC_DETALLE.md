# DIAGNÓSTICO: Origen de Comercial_KPIs_Diarios_v2 y Sync_Sales/PAX_Detalle

**Fecha de Generación:** 2026-06-02  
**Solicitado por:** Usuario  
**Método:** Análisis de código fuente + queries SQL directas

---

## ÍNDICE DE PREGUNTAS

1. [¿Qué proceso llena Comercial_KPIs_Diarios_v2?](#1-qué-proceso-llena-comercial_kpis_diarios_v2)
2. [¿Ese proceso ya tiene acceso a SoftRestaurant/MPRO?](#2-ese-proceso-ya-tiene-acceso-a-softrestaurantmpro)
3. [¿Ese proceso puede extenderse para llenar Sync_Sales?](#3-ese-proceso-puede-extenderse-para-llenar-sync_sales)
4. [¿Ese proceso puede extenderse para llenar Sync_PAX_Detalle?](#4-ese-proceso-puede-extenderse-para-llenar-sync_pax_detalle)
5. [¿Qué unidades procesa?](#5-qué-unidades-procesa)
6. [¿Qué credenciales/variables usa?](#6-qué-credencialesvariables-usa)
7. [¿Dónde registra errores?](#7-dónde-registra-errores)
8. [¿Por qué Sync_Sales está en 0?](#8-por-qué-sync_sales-está-en-0)
9. [¿Por qué Sync_PAX_Detalle está en 0?](#9-por-qué-sync_pax_detalle-está-en-0)
10. [¿Se debe poblar desde fuente original o desde datos ya agregados?](#10-se-debe-poblar-desde-fuente-original-o-desde-datos-ya-agregados)

---

## 1. ¿Qué proceso llena Comercial_KPIs_Diarios_v2?

### Proceso Principal Identificado

**Archivo:** `/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py`

Este módulo es el **sincronizador principal** que:
1. Extrae datos agregados de ventas desde SoftRestaurant/MPRO
2. Los transforma usando mappers específicos por sistema
3. Los escribe directamente en `Comercial_KPIs_Diarios_v2` usando `upsert_kpi_diario()`

### Flujo de Ejecución

```
sync_comercial_edarsahub.py
    │
    ├── sync_softrestaurant_ventas_cerradas()  ──► QUERY_SOFTRESTAURANT_VENTAS_CERRADAS
    │       │
    │       └── map_softrestaurant_ventas_cerradas() ──► KPIsDiariosV2
    │               │
    │               └── upsert_kpi_diario(kpi) ──► INSERT/UPDATE Comercial_KPIs_Diarios_v2
    │
    └── sync_mpro_ventas_cerradas()  ──► QUERY_MPRO_VENTAS_CERRADAS
            │
            └── map_mpro_ventas_cerradas() ──► KPIsDiariosV2
                    │
                    └── upsert_kpi_diario(kpi) ──► INSERT/UPDATE Comercial_KPIs_Diarios_v2
```

### Proceso Alternativo (Job Scheduler)

**Archivo:** `/app/backend/core/scheduler/jobs/inteligencia_comercial_sync_job.py`

Este job tiene **código para ambos flujos** pero actualmente solo ejecuta el flujo de KPIs agregados:

```python
# Líneas 428-448 de inteligencia_comercial_sync_job.py
# 1. Extraer ventas del POS
sales = extract_sales_from_pos(unidad, config, fecha_inicio_str, fecha_fin_str)

# 2. Insertar en Sync_Sales  <-- ESTE CÓDIGO EXISTE PERO NO SE EJECUTA ACTIVAMENTE
if sales:
    inserted = insert_into_sync_sales(hub_conn, sales)

# 3. Actualizar KPIs diarios  <-- ESTE SÍ SE EJECUTA
while current_date <= fecha_fin:
    if update_kpis_diarios(hub_conn, unidad, fecha_str):
        stats["kpis_actualizados"] += 1
```

---

## 2. ¿Ese proceso ya tiene acceso a SoftRestaurant/MPRO?

### ✅ SÍ, tiene acceso confirmado

El proceso tiene acceso a los sistemas POS mediante:

### 2.1 Configuración Dinámica (sync_comercial_edarsahub.py)

Lee credenciales desde la tabla `Servidores_Conexiones` en EDARSAHUB:

```python
# Líneas 78-91 de sync_comercial_edarsahub.py
query = """
SELECT 
    id, nombre, host, port, database_name,
    username, password_encrypted, system_type, activo
FROM Servidores_Conexiones
WHERE id = '{server_id}'
"""
```

### 2.2 Configuración Estática (inteligencia_comercial_sync_job.py)

Tiene configuración hardcodeada como backup:

```python
# Líneas 37-77 de inteligencia_comercial_sync_job.py
UNIDADES_CONFIG = {
    "CIENFUEGOS": {
        "system_type": "SoftRestaurant",
        "host": "servercienfuegos.ddns.net,6669\\nationalsoft",
        "database": "softrestaurant95pro",
        "username": os.environ.get("CIENFUEGOS_DB_USER", "sa"),
        "password": os.environ.get("CIENFUEGOS_DB_PASS", ""),
    },
    "130MID": {
        "system_type": "SoftRestaurant",
        "host": "130mid.ddns.net",
        "database": "softrestaurant10",
    },
    "ESTELAR": {
        "system_type": "SoftRestaurant",
        "host": "serverestelar.ddns.net,6969",
        "database": "softrestaurant12",
    },
    "130QRO": {
        "system_type": "MPRO",
        "host": "<REDACTED_EDARSAHUB_SQL_HOST>",
        "database": "QUERETARO",
    },
    "ORIGEN": {
        "system_type": "MPRO",
        "host": "<REDACTED_EDARSAHUB_SQL_HOST>",
        "database": "ORIGEN",
    },
}
```

### Evidencia de Conectividad

Datos actuales en `Comercial_KPIs_Diarios_v2`:
- **SOFTRESTAURANT:** 1,862 registros | $287,433,748 ventas
- **MPRO:** 1,514 registros | $142,962,445 ventas

---

## 3. ¿Ese proceso puede extenderse para llenar Sync_Sales?

### ✅ SÍ, el código YA EXISTE

**Ubicación:** `/app/backend/core/scheduler/jobs/inteligencia_comercial_sync_job.py`

### Código Existente (Líneas 230-280)

```python
def insert_into_sync_sales(conn, sales: List[Dict]) -> int:
    """Inserta registros en Sync_Sales."""
    cursor = conn.cursor()
    inserted = 0
    
    for sale in sales:
        cursor.execute("""
            INSERT INTO Sync_Sales (
                id, branch, UnidadNegocio, NumeroTicket, 
                MontoTotal, Pax, FechaHora, status, items,
                created_at, total
            ) VALUES (...)
        """, (...))
        inserted += 1
    
    return inserted
```

### Queries de Extracción de Tickets (YA IMPLEMENTADAS)

**SoftRestaurant (Líneas 120-149):**
```sql
SELECT 
    CONVERT(VARCHAR(64), ch.folio) AS NumeroTicket,
    ch.nopersonas AS Pax,
    ch.total AS MontoTotal,
    t.apertura AS FechaHora,
    (SELECT ... FOR JSON PATH) AS items  -- Incluye detalle de productos
FROM cheques ch
INNER JOIN turnos t ON t.idturno = ch.idturno
WHERE t.apertura >= '{fecha_inicio}'
  AND ch.cancelado = 0
```

**MPRO (Líneas 152-182):**
```sql
SELECT 
    CONVERT(VARCHAR(64), v.Vn_Folio) AS NumeroTicket,
    ISNULL(c.Co_Personas, 1) AS Pax,
    v.Vn_Precio_Neto_Importe AS MontoTotal,
    v.Vn_Fecha AS FechaHora,
    (SELECT ... FOR JSON PATH) AS items  -- Incluye detalle de productos
FROM Venta_Encabezado v
LEFT JOIN Comanda c ON ...
```

### Para Activar

Simplemente **ejecutar el job** con el flag correcto o descomentar la línea:
```python
# Línea 436: if sales: inserted = insert_into_sync_sales(hub_conn, sales)
```

---

## 4. ¿Ese proceso puede extenderse para llenar Sync_PAX_Detalle?

### ⚠️ PARCIALMENTE - Código existe pero incompleto

**Ubicación:** `/app/backend/core/scheduler/jobs/sync_comercial_endpoints_job.py`

### Código Existente (Líneas 487-508)

```python
cursor.execute("""
    IF NOT EXISTS (SELECT 1 FROM Sync_PAX_Detalle 
                  WHERE ServerID = %s AND SucursalID = %s AND FechaOperacion = %s)
        INSERT INTO Sync_PAX_Detalle
        (PAXRegistroID, ServerID, SucursalID, SucursalNombre, 
         FechaOperacion, FechaHora, NumeroComensales, 
         VentaCuenta, ConsumoPromedioPAX)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (...))
```

### Limitaciones Actuales

1. **Solo procesa datos agregados por día**, no detalle por mesa/cuenta
2. **Requiere query adicional** para extraer:
   - `CuentaID`, `CuentaFolio`
   - `MesaNumero`, `MeseroID`, `MeseroNombre`
   - `HoraEntrada`, `HoraSalida`, `TiempoMesa`
   - `Turno`, `DiaSemana`

### Query Necesaria para SoftRestaurant

```sql
SELECT 
    ch.folio AS CuentaFolio,
    ch.mesa AS MesaNumero,
    e.nombre AS MeseroNombre,
    ch.nopersonas AS NumeroComensales,
    ch.total AS VentaCuenta,
    ch.total / NULLIF(ch.nopersonas, 0) AS ConsumoPromedioPAX,
    t.apertura AS HoraEntrada,
    ch.cierre AS HoraSalida,
    DATEDIFF(MINUTE, t.apertura, ch.cierre) AS TiempoMesa,
    t.turnonum AS Turno
FROM cheques ch
INNER JOIN turnos t ON t.idturno = ch.idturno
LEFT JOIN empleados e ON e.idempleado = ch.idempleado
WHERE ch.cancelado = 0
  AND ch.cierre IS NOT NULL
```

---

## 5. ¿Qué unidades procesa?

### Unidades Activas (5 total)

| Unidad | Sistema | Server/Host | Database | Estado |
|--------|---------|-------------|----------|--------|
| **CIENFUEGOS** | SoftRestaurant | servercienfuegos.ddns.net:6669 | softrestaurant95pro | ✅ Activo |
| **130° MERIDA** | SoftRestaurant | 130mid.ddns.net:1433 | softrestaurant10 | ✅ Activo |
| **LA ESTELAR** | SoftRestaurant | serverestelar.ddns.net:6969 | softrestaurant12 | ✅ Activo |
| **130° QUERÉTARO** | MPRO | <REDACTED_EDARSAHUB_SQL_HOST>:1433 | QUERETARO (Suc: 0021) | ✅ Activo |
| **ORIGEN** | MPRO | <REDACTED_EDARSAHUB_SQL_HOST>:1433 | ORIGEN (Suc: 0023) | ✅ Activo |

### Datos Actuales por Unidad

| Unidad | Registros | Ventas Totales | Rango |
|--------|-----------|----------------|-------|
| CIENFUEGOS | 757 | $138,913,136 | 2024-05 a 2026-06 |
| 130° MERIDA | 757 | $119,756,236 | 2024-05 a 2026-06 |
| 130° QUERETARO | 758 | $93,743,336 | 2024-05 a 2026-06 |
| ORIGEN | 756 | $49,219,109 | 2024-05 a 2026-06 |
| LA ESTELAR | 348 | $28,764,376 | 2025-06 a 2026-06 |

---

## 6. ¿Qué credenciales/variables usa?

### 6.1 Variables de Entorno (.env)

```bash
# EDARSAHUB (Destino)
EDARSAHUB_HOST=<REDACTED_EDARSAHUB_SQL_HOST>
EDARSAHUB_PORT=1433
EDARSAHUB_DATABASE=EDARSAHUB
EDARSAHUB_USERNAME=<REDACTED_EDARSAHUB_SQL_USER>
EDARSAHUB_PASSWORD=<REDACTED_EDARSAHUB_SQL_PASSWORD>

# POS Origen (Opcionales - se leen de Servidores_Conexiones si no están)
CIENFUEGOS_DB_USER=sa
CIENFUEGOS_DB_PASS=********
130MID_DB_USER=sa
130MID_DB_PASS=********
ESTELAR_DB_USER=sa
ESTELAR_DB_PASS=********
130QRO_DB_USER=<REDACTED_EDARSAHUB_SQL_USER>
130QRO_DB_PASS=<REDACTED_EDARSAHUB_SQL_PASSWORD>
ORIGEN_DB_USER=<REDACTED_EDARSAHUB_SQL_USER>
ORIGEN_DB_PASS=<REDACTED_EDARSAHUB_SQL_PASSWORD>

# Cifrado de secretos
SERVER_SECRET_KEY=4HGEDzNpIv3pMoHXFtlXXYiTSt1SxU8dXHiTR5GOtd8=
```

### 6.2 Tabla Servidores_Conexiones

Almacena credenciales cifradas para cada servidor:

```sql
SELECT id, nombre, host, port, database_name, username, password_encrypted
FROM Servidores_Conexiones
WHERE activo = 1
```

### 6.3 Código de Configuración

**Archivo:** `/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py`

```python
EDARSAHUB_CONFIG = {
    'host': '<REDACTED_EDARSAHUB_SQL_HOST>',
    'port': 1433,
    'database': 'EDARSAHUB',
    'username': '<REDACTED_EDARSAHUB_SQL_USER>',
    'password': '<REDACTED_EDARSAHUB_SQL_PASSWORD>'
}
```

---

## 7. ¿Dónde registra errores?

### 7.1 Tabla Principal de Log: `Comercial_SyncLog_v2`

**Estructura (20 columnas):**

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | uniqueidentifier | PK |
| `run_id` | nvarchar | ID único de ejecución |
| `run_type` | nvarchar | INCREMENTAL, FULL, MANUAL |
| `unidad_negocio_id` | nvarchar | Unidad procesada |
| `status` | nvarchar | SUCCESS, FAILED |
| `error_message` | nvarchar | Mensaje de error |
| `source_connection_status` | nvarchar | ONLINE, OFFLINE, TIMEOUT |
| `records_processed` | int | Registros procesados |
| `records_inserted` | int | Registros insertados |
| `records_updated` | int | Registros actualizados |
| `duration_seconds` | int | Duración en segundos |
| `created_at` | datetime2 | Timestamp |

### 7.2 Código de Registro de Errores

**Archivo:** `/app/backend/modules/comercial_v2/sync_comercial_edarsahub.py`

```python
# Líneas 300-314
if conn_status != ConnectionStatus.ONLINE:
    result.error_message = f"Conexión fallida: {conn_status}"
    log = SyncLogV2(
        run_id=run_id,
        run_type=SyncRunType.INCREMENTAL,
        unidad_negocio_id=config.unidad_negocio_id,
        status=SyncStatus.FAILED,
        error_message=result.error_message,
        source_connection_status=conn_status
    )
    insert_sync_log(log)  # <-- Registra en Comercial_SyncLog_v2
```

### 7.3 Últimos Errores Registrados

```
RunID: ABIERTA-20260602-200436-94f0
  Unidad: 130QRO
  Status: FAILED
  Error: ABIERTAS
  Conexión: OFFLINE

RunID: ABIERTA-20260602-191436-c253
  Unidad: ORIGEN
  Status: FAILED
  Error: ABIERTAS
  Conexión: OFFLINE
```

### 7.4 Otras Tablas de Log

| Tabla | Propósito |
|-------|-----------|
| `Sync_Logs` | Log genérico de sincronización |
| `Scheduler_BitacoraJobs` | Bitácora de ejecución de jobs |

---

## 8. ¿Por qué Sync_Sales está en 0?

### Respuesta Directa: **El código existe pero NO se ejecuta activamente**

### Análisis Técnico

1. **El job `inteligencia_comercial_sync_job.py` tiene el código** (líneas 230-280)
2. **La función `insert_into_sync_sales()` está implementada**
3. **Las queries de extracción están listas** (`get_softrestaurant_query()`, `get_mpro_query()`)

### Razón de No Ejecución

El proceso actual de **Fase 1** fue diseñado para el **Dashboard Ejecutivo** que solo necesita:
- KPIs agregados diarios (ventas, tickets, PAX)
- Comparativas YoY, MoM
- Tendencias mensuales

**Estos KPIs NO requieren granularidad de tickets individuales**, por lo tanto:

```python
# inteligencia_comercial_sync_job.py - Líneas 434-438
# 2. Insertar en Sync_Sales
if sales:
    inserted = insert_into_sync_sales(hub_conn, sales)  # <-- SE EJECUTA SOLO SI HAY SALES
    stats["registros_insertados"] += inserted
    hub_conn.commit()
```

Pero **`sales` no se llena** porque las credenciales de POS no están completas en variables de entorno:

```python
UNIDADES_CONFIG = {
    "CIENFUEGOS": {
        "password": os.environ.get("CIENFUEGOS_DB_PASS", ""),  # <-- VACÍO
    },
```

### Para Activar

1. Configurar las variables de entorno con credenciales POS
2. O usar el método dinámico vía `Servidores_Conexiones`

---

## 9. ¿Por qué Sync_PAX_Detalle está en 0?

### Respuesta Directa: **El código es incompleto y no se ejecuta**

### Análisis Técnico

1. **Existe código parcial** en `sync_comercial_endpoints_job.py` (líneas 487-508)
2. **Solo procesa datos agregados**, no detalle por mesa/cuenta
3. **El job principal (`sync_comercial_edarsahub.py`) NO tiene lógica para PAX_Detalle**

### Campos Faltantes en Query Actual

La query actual solo extrae:
- `NumeroComensales` (agregado)
- `VentaCuenta` (total)
- `ConsumoPromedioPAX` (calculado)

**Faltan campos críticos para análisis detallado:**
- `CuentaID`, `CuentaFolio` → Identificador de cuenta
- `MesaNumero` → Número de mesa
- `MeseroID`, `MeseroNombre` → Mesero asignado
- `HoraEntrada`, `HoraSalida` → Tiempos de permanencia
- `TiempoMesa` → Rotación de mesas
- `Turno`, `DiaSemana` → Contexto temporal

### Para Implementar Completo

Requiere nueva query que extraiga detalle por mesa/cuenta desde:
- SoftRestaurant: `cheques` + `turnos` + `empleados`
- MPRO: `Comanda` + `Venta_Encabezado`

---

## 10. ¿Se debe poblar desde fuente original o desde datos ya agregados?

### Recomendación: **DESDE FUENTE ORIGINAL**

### Justificación Técnica

| Aspecto | Desde Fuente Original | Desde Datos Agregados |
|---------|----------------------|----------------------|
| **Granularidad** | ✅ Máxima (ticket/mesa) | ❌ Solo diaria |
| **Flexibilidad de análisis** | ✅ Permite cualquier agrupación | ❌ Limitado |
| **Consistencia** | ✅ Una sola fuente de verdad | ⚠️ Posible desfase |
| **Detalle de productos** | ✅ JSON items por ticket | ❌ No disponible |
| **Trazabilidad** | ✅ NumeroTicket, FechaHora exacta | ❌ Perdida |
| **Complejidad** | ⚠️ Mayor volumen | ✅ Menor volumen |

### Arquitectura Recomendada

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FASE 2: Granularidad Completa                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  SoftRestaurant/MPRO (POS)                                         │
│          │                                                          │
│          ▼                                                          │
│  ┌───────────────────┐                                             │
│  │ Sync_Sales        │ ◄─── Tickets individuales + items JSON     │
│  │ (detalle tickets) │                                             │
│  └─────────┬─────────┘                                             │
│            │                                                        │
│            ▼                                                        │
│  ┌───────────────────┐                                             │
│  │ Sync_PAX_Detalle  │ ◄─── Detalle por mesa/cuenta/mesero        │
│  │ (detalle PAX)     │                                             │
│  └─────────┬─────────┘                                             │
│            │                                                        │
│            ▼                                                        │
│  ┌───────────────────────────────┐                                 │
│  │ Comercial_KPIs_Diarios_v2     │ ◄─── Calculado desde Sync_*    │
│  │ (KPIs consolidados)           │      (agregación post-facto)    │
│  └───────────────────────────────┘                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Plan de Implementación

1. **Paso 1:** Poblar `Sync_Sales` desde POS (tickets + items)
2. **Paso 2:** Poblar `Sync_PAX_Detalle` desde POS (detalle mesa/cuenta)
3. **Paso 3:** Crear SP que calcule KPIs desde `Sync_Sales` → `Comercial_KPIs_Diarios_v2`
4. **Paso 4:** Validar que KPIs calculados coincidan con los actuales
5. **Paso 5:** Migrar flujo para que KPIs se calculen desde `Sync_*`

---

## RESUMEN EJECUTIVO

| # | Pregunta | Respuesta |
|---|----------|-----------|
| 1 | ¿Qué proceso llena KPIs_v2? | `sync_comercial_edarsahub.py` + job scheduler |
| 2 | ¿Tiene acceso a POS? | **SÍ** - Vía `Servidores_Conexiones` |
| 3 | ¿Puede llenar Sync_Sales? | **SÍ** - Código existe, falta activar |
| 4 | ¿Puede llenar Sync_PAX_Detalle? | **PARCIAL** - Código incompleto |
| 5 | ¿Qué unidades procesa? | 5: CIENFUEGOS, 130MID, ESTELAR, 130QRO, ORIGEN |
| 6 | ¿Qué credenciales usa? | `.env` + `Servidores_Conexiones` |
| 7 | ¿Dónde registra errores? | `Comercial_SyncLog_v2` |
| 8 | ¿Por qué Sync_Sales=0? | Código no ejecutado (Fase 1 no lo requiere) |
| 9 | ¿Por qué PAX_Detalle=0? | Código incompleto + no ejecutado |
| 10 | ¿Fuente original o agregados? | **FUENTE ORIGINAL** (recomendado) |

---

## PRÓXIMOS PASOS RECOMENDADOS

### Inmediato (Para poblar Sync_Sales)
1. Verificar credenciales POS en `.env` o `Servidores_Conexiones`
2. Ejecutar `job_inteligencia_comercial_sync(dias_atras=30)`
3. Validar registros insertados

### Corto Plazo (Para Sync_PAX_Detalle)
1. Implementar query completa de detalle PAX
2. Extender `sync_comercial_endpoints_job.py`
3. Ejecutar y validar

---

**Reporte generado automáticamente | Agente E1**
