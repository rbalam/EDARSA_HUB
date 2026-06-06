# MACROFASE 2 — FASE 2.3: Carga Histórica Controlada de 24 Meses

**Fecha Inicio:** 25 Abril 2026  
**Estado:** EN PROGRESO  
**Arquitecto:** E1 Agent

---

## 1. Resumen Ejecutivo

Implementación de carga histórica controlada de 24 meses para los módulos Comercial/KPIs de EDARSA HUB, usando procesos batch con checkpoints, idempotencia, deduplicación, y trazabilidad completa.

**Principios:**
- Idempotente: ejecutable múltiples veces sin duplicar datos
- Incremental: procesamiento por batches con checkpoints
- Seguro: sin modificar fuentes externas, sin exponer secretos
- Reanudable: puede continuar desde el último checkpoint

---

## 2. Diagnóstico Previo

### 2.1 Colecciones MongoDB Existentes

| Colección | Documentos | Uso |
|-----------|------------|-----|
| kpis_comercial | 49 | KPIs consolidados por día/sucursal |
| comercial_cache | 36 | Cache de respuestas |
| kpis_cache | 31 | Cache de KPIs |
| dashboard_cache | 20 | Cache dashboards |
| scheduler_job_log | 4159 | Logs de jobs |

### 2.2 Índices kpis_comercial

| Índice | Campos | Tipo |
|--------|--------|------|
| idx_unique_kpi_diario | (server_id, empresa_id, sucursal_id, fecha) | UNIQUE |
| idx_empresa_fecha | (empresa_id, fecha) | Regular |
| idx_server_fecha | (server_id, fecha) | Regular |
| idx_estado_fecha | (estado_periodo, fecha) | Regular |
| idx_unidad_fecha | (unidad_negocio_id, fecha) | Regular |

### 2.3 Servidores DATA_SOURCE

| Servidor | System Type | Estado |
|----------|-------------|--------|
| ManagmentPro | MPRO | UNKNOWN |
| CIENFUEGOS | SoftRestaurant | UNKNOWN |
| LA ESTELAR | SoftRestaurant | UNKNOWN |
| 130° MERIDA | SoftRestaurant | UNKNOWN |
| MPRO TABLAJERIA | MPRO | UNKNOWN |
| CIENFUEGOS TABLAJERIA | SoftRestaurant | UNKNOWN |
| HR2020 ESCRITURA | MPRO | UNKNOWN |
| PRUEBAS SOFTRESTAURANT | SoftRestaurant | UNKNOWN |

**Total:** 8 servidores (5 SoftRestaurant, 3 MPRO)

### 2.4 Jobs Existentes

| Job | Frecuencia | Ventana |
|-----|------------|---------|
| sync_short_comercial | Cada 15 min | Día actual |
| sync_nightly_comercial | Diario 03:00 | Últimos 7 días |

### 2.5 Sistema de UPSERT Idempotente

El `kpis_repository.py` ya implementa:
- UPSERT con detección de cambios
- Versionado (version=1, 2, 3...)
- Estados de período (ABIERTO, CERRADO, RECONCILIADO)
- Transiciones válidas entre estados
- Historial de versiones embebido (max 10)
- Flags (requiere_reconciliacion, excluir_de_reportes)

---

## 3. Alcance de Carga

### 3.1 Rango de Fechas

| Parámetro | Valor |
|-----------|-------|
| fecha_fin_histórica | 2026-04-25 (hoy) |
| fecha_inicio_histórica | 2024-04-25 (24 meses atrás) |
| zona_horaria | America/Merida |
| granularidad | Diaria por sucursal |

### 3.2 Módulos Incluidos

| Módulo | Prioridad | Estado | Llave Única |
|--------|-----------|--------|-------------|
| Comercial KPIs | P0 | LISTO | (server_id, empresa_id, sucursal_id, fecha) |

### 3.3 Módulos Excluidos (Fase 2.3)

| Módulo | Razón |
|--------|-------|
| Finanzas Cortes | No hay queries históricos implementados |
| Finanzas Propinas TPV | Depende de cortes |
| Compras Históricas | No hay queries históricos implementados |
| Inventarios | Flujo diferente (no diario) |

---

## 4. Diseño de Batches

### 4.1 Parámetros

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| BATCH_DAYS | 7 | Días por batch |
| MAX_ROWS_PER_QUERY | 5000 | Límite de filas |
| TIMEOUT_SECONDS | 120 | Timeout por query |
| SLEEP_BETWEEN_BATCHES | 2 | Segundos entre batches |
| MAX_RETRIES | 2 | Reintentos por batch |

### 4.2 Cálculo de Batches

- 24 meses = ~730 días
- 730 días / 7 días = ~105 batches por servidor
- 8 servidores × 105 batches = ~840 batches totales

---

## 5. Diseño de Checkpoints

### 5.1 Colección: historical_load_checkpoints

```json
{
  "run_id": "HL_20260425_143000",
  "module": "comercial",
  "server_id": "uuid",
  "server_name": "CIENFUEGOS",
  "system_type": "SoftRestaurant",
  "fecha_inicio": "2024-04-25",
  "fecha_fin": "2026-04-25",
  "fecha_actual_procesada": "2024-05-02",
  "batch_actual": 1,
  "total_batches": 105,
  "status": "RUNNING",
  "processed_count": 7,
  "inserted_count": 5,
  "updated_count": 2,
  "skipped_count": 0,
  "error_count": 0,
  "last_error": null,
  "started_at": "2026-04-25T14:30:00Z",
  "updated_at": "2026-04-25T14:31:00Z",
  "finished_at": null
}
```

### 5.2 Estados de Checkpoint

| Estado | Descripción |
|--------|-------------|
| PENDING | Creado pero no iniciado |
| RUNNING | En ejecución |
| PARTIAL | Parcialmente completado (interrumpido) |
| SUCCESS | Completado sin errores |
| FAILED | Fallido con errores |
| CANCELLED | Cancelado manualmente |

---

## 6. Diseño de Idempotencia

### 6.1 Llave Única KPIs Comerciales

```
(server_id, empresa_id, sucursal_id, fecha)
```

### 6.2 Comportamiento UPSERT

| Escenario | Acción |
|-----------|--------|
| No existe | INSERT (version=1, estado=ABIERTO) |
| Existe + cambios | UPDATE (version+1) |
| Existe + sin cambios | SKIP (idempotente) |
| Estado=RECONCILIADO | REJECT (requiere reapertura) |

---

## 7. Adapters por System Type

| System Type | Adapter | Queries |
|-------------|---------|---------|
| SoftRestaurant | softrestaurant.py | query_ventas_periodo_sr |
| MPRO | mpro.py | query_ventas_periodo_mpro |
| UNKNOWN | N/A | SKIP con advertencia |

---

## 8. Manejo de Errores

| Código | Descripción | Acción |
|--------|-------------|--------|
| SUCCESS | Operación exitosa | Continuar |
| NO_DATA | Sin datos en rango | Continuar |
| SOURCE_UNREACHABLE | Red/VPN falla | Log + Skip servidor |
| AUTH_FAILED | Credenciales inválidas | Log + Skip servidor |
| SECRET_DECRYPTION_ERROR | No descifra | Log + Skip servidor |
| QUERY_ERROR | SQL falla | Log + Skip batch |
| UNSUPPORTED_SYSTEM_TYPE | Tipo no soportado | Log + Skip servidor |

---

## 9. Script de Carga

**Archivo:** `/app/backend/scripts/run_historical_load_24_months.py`

### 9.1 Argumentos

```
--dry-run           Solo simular (default)
--run               Ejecutar realmente
--module            comercial|finanzas|compras|all
--server-id         UUID servidor específico
--start-date        YYYY-MM-DD
--end-date          YYYY-MM-DD
--batch-days        Días por batch (default 7)
--resume            Reanudar desde checkpoint
--force-restart     Reiniciar desde cero
--max-servers       Limitar servidores (safe-mode)
--safe-mode         Solo 1 servidor, 1 batch
```

### 9.2 Ejemplo Safe-Mode

```bash
HISTORICAL_LOAD_CONFIRM=YES python /app/backend/scripts/run_historical_load_24_months.py \
  --run \
  --module comercial \
  --safe-mode
```

---

## 10. Reportes

### 10.1 Dry-Run Report

**Archivo:** `/app/docs/reports/historical_load_24_months_dry_run.json`

### 10.2 Execution Report

**Archivo:** `/app/docs/reports/historical_load_24_months_execution_report.json`

---

## 11. Validación

### 11.1 Criterios

- [ ] Backend compila
- [ ] Backend RUNNING
- [ ] Dry-run exitoso
- [ ] Primera ejecución safe-mode exitosa
- [ ] No duplicados en kpis_comercial
- [ ] Checkpoints guardados
- [ ] Logs sin secretos
- [ ] Tableros principales funcionando

---

## 12. Riesgos Residuales

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| Servidores VPN desconectados | MEDIA | Skip + retry posterior |
| Queries lentas en servidores remotos | MEDIA | Timeout configurable |
| Volumen alto de datos históricos | BAJA | Batches pequeños |

---

## 13. Siguiente Paso

1. Crear script `run_historical_load_24_months.py`
2. Crear colección `historical_load_checkpoints`
3. Ejecutar dry-run
4. Ejecutar safe-mode con 1 servidor
5. Validar resultados
6. Ampliar a todos los servidores

---

## 11. CORRECCIÓN OBLIGATORIA: Destino Final en EDARSAHUB SQL

### 11.1 Hallazgo Crítico (2026-04-26)

Durante la ejecución safe-mode se detectó que los KPIs históricos se insertaron en **MongoDB** (`kpis_comercial`), violando la regla maestra de arquitectura:

> **EDARSAHUB SQL es el cerebro. MongoDB NO debe ser destino final de históricos ni KPIs definitivos.**

### 11.2 Estado Actual vs. Correcto

| Tipo de dato | Destino actual | Destino correcto | Acción requerida |
|-------------|----------------|------------------|------------------|
| **KPIs históricos comerciales** | MongoDB `kpis_comercial` | EDARSAHUB SQL | **CORREGIR SCRIPT** |
| Checkpoints | MongoDB | MongoDB permitido | Documentar |
| Logs del job | MongoDB | MongoDB permitido | Documentar |
| Cache dashboard | MongoDB | MongoDB permitido | No fuente final |
| Staging temporal | MongoDB | Promover a SQL | Controlar |

### 11.3 Tabla SQL Requerida

**NO EXISTE** tabla para KPIs comerciales históricos en EDARSAHUB.

**Propuesta de tabla:** `Comercial_KPIs_Historico`

```sql
CREATE TABLE Comercial_KPIs_Historico (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    run_id NVARCHAR(50) NOT NULL,
    server_id NVARCHAR(50) NOT NULL,
    sucursal_id NVARCHAR(20) NOT NULL,
    sucursal_nombre NVARCHAR(100),
    empresa_id NVARCHAR(50),
    unidad_negocio_id NVARCHAR(50),
    system_type_normalized NVARCHAR(20) NOT NULL,
    fecha DATE NOT NULL,
    kpi_tipo NVARCHAR(20) DEFAULT 'DIARIO',
    ventas_total DECIMAL(18,2) DEFAULT 0,
    tickets_total INT DEFAULT 0,
    pax_total INT DEFAULT 0,
    ticket_promedio DECIMAL(18,2) DEFAULT 0,
    propinas_total DECIMAL(18,2) DEFAULT 0,
    source_hash NVARCHAR(64),
    source_batch_start DATE,
    source_batch_end DATE,
    estado_periodo NVARCHAR(20) DEFAULT 'ABIERTO',
    version INT DEFAULT 1,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE(),
    created_by NVARCHAR(50) DEFAULT 'historical_load'
);

-- Índice único para idempotencia
CREATE UNIQUE INDEX idx_unique_kpi_comercial 
ON Comercial_KPIs_Historico (server_id, sucursal_id, system_type_normalized, fecha, kpi_tipo);

-- Índices de consulta
CREATE INDEX idx_fecha ON Comercial_KPIs_Historico (fecha DESC);
CREATE INDEX idx_server_fecha ON Comercial_KPIs_Historico (server_id, fecha DESC);
```

### 11.4 Flujo Corregido

```
Fuente externa SQL/API
    ↓
Extracción segura (server_registry/secret_manager)
    ↓
Transformación
    ↓
UPSERT idempotente en EDARSAHUB SQL  ← DESTINO FINAL
    ↓
Checkpoint/log en MongoDB (permitido)
    ↓
MongoDB cache opcional (NO fuente final)
```

### 11.5 Estado de los 14 Registros de Prueba

Los 14 registros insertados en MongoDB durante safe-mode se clasifican como:

- **Tipo:** STAGING_TEMPORAL_DE_PRUEBA
- **Acción:** NO eliminar todavía
- **Destino final:** Candidatos a migrar a SQL cuando exista tabla
- **Uso actual:** Referencia para validar estructura de datos

### 11.6 Criterios para Continuar

**NO continuar con carga histórica hasta que:**

1. ✅ Tabla `Comercial_KPIs_Historico` creada en EDARSAHUB SQL
2. ✅ Índice único implementado para control anti-duplicados
3. ✅ Script `run_historical_load_24_months.py` modificado para UPSERT en SQL
4. ✅ MongoDB clasificado como cache/log/checkpoint/staging únicamente
5. ✅ Prueba safe-mode exitosa con nuevo destino SQL

---

## 12. Reporte de Auditoría

Ver archivo: `/app/docs/reports/historical_load_destination_audit.json`

---

**Estado:** FASE 2.3A COMPLETADA — DESTINO SQL IMPLEMENTADO

---

## 13. FASE 2.3A COMPLETADA — Corrección de Destino a SQL (2026-04-26)

### 13.1 Resumen

Se corrigió exitosamente el destino de escritura de KPIs históricos:

| Antes | Después |
|-------|---------|
| MongoDB `kpis_comercial` | EDARSAHUB SQL `Comercial_KPIs_Historico` |

### 13.2 Componentes Creados/Modificados

| Archivo | Tipo | Descripción |
|---------|------|-------------|
| `/app/backend/db/migrations/create_comercial_kpis_historico.sql` | Nuevo | Script de migración SQL |
| `/app/backend/modules/comercial/historical_kpis_repository.py` | Nuevo | Repository para UPSERT SQL |
| `/app/backend/scripts/run_historical_load_24_months.py` | Modificado | Destino SQL, MongoDB solo checkpoint |

### 13.3 Tabla SQL Creada

```
Comercial_KPIs_Historico (EDARSAHUB)
├── id (UNIQUEIDENTIFIER, PK)
├── run_id (NVARCHAR)
├── server_id (NVARCHAR)
├── sucursal_id (NVARCHAR)
├── sucursal_nombre (NVARCHAR)
├── fecha (DATE)
├── kpi_tipo (NVARCHAR, DEFAULT 'DIARIO')
├── ventas_total (DECIMAL)
├── tickets_total (INT)
├── pax_total (INT)
├── ticket_promedio (DECIMAL)
├── propinas_total (DECIMAL)
├── source_hash (NVARCHAR)
├── created_at / updated_at (DATETIME2)
└── ÍNDICE ÚNICO: (server_id, sucursal_id, system_type_normalized, fecha, kpi_tipo)
```

### 13.4 Resultado Safe-Mode SQL

| Campo | Valor |
|-------|-------|
| Run ID | `HL_20260426_004303` |
| Servidor | ManagmentPro (MPRO) |
| Batch | 2024-05-06 a 2024-05-12 |
| **SQL insertados** | **14** ✅ |
| SQL actualizados | 0 |
| SQL errores | 0 |
| **MongoDB final** | **0** ✅ |
| Duplicados SQL | **0** ✅ |

### 13.5 14 Registros MongoDB de Prueba Anterior

Los 14 registros del run `HL_20260426_003155` en MongoDB `kpis_comercial` quedan:

- **Clasificación**: STAGING_TEMPORAL_DE_PRUEBA
- **Acción**: DOCUMENTADO, NO ELIMINADO
- **Opción futura**: Migrar a SQL usando `migrate_staging_mongo_kpis_to_sql()`

### 13.6 Criterios de Aceptación Cumplidos

| Criterio | Estado |
|----------|--------|
| Tabla SQL existe | ✅ |
| Índice único existe | ✅ |
| Script escribe a SQL | ✅ |
| MongoDB no es destino final | ✅ |
| Safe-mode SQL inserted > 0 | ✅ |
| No duplicados SQL | ✅ |
| Backend compila y corre | ✅ |
| MongoDB staging documentado | ✅ |

### 13.7 Próximos Pasos Autorizados

1. Usuario puede escalar carga histórica a más batches/servidores
2. Evaluar migración de MongoDB staging a SQL
3. Probar servidores SoftRestaurant

---

## 14. MACROFASE 2.3B — Escalamiento Controlado (2026-04-26)

### 14.1 Primer Batch de Escalamiento

| Campo | Valor |
|-------|-------|
| Run ID | `HL_20260426_004649` |
| Servidor | ManagmentPro (MPRO) |
| Rango | 2024-05-13 a 2024-05-19 |
| SQL insertados | **14** ✅ |
| MongoDB final | **0** ✅ |
| Duplicados SQL | **0** ✅ |

### 14.2 Estado Acumulado

| Métrica | Valor |
|---------|-------|
| Batches ejecutados | 2 |
| SQL total insertados | 28 |
| Rango cubierto | 2024-05-06 a 2024-05-19 |
| Días históricos | 14 |
| Sucursales | 2 (130° QUERETARO, ORIGEN) |

### 14.3 Próximo Batch Sugerido

```
Start: 2024-05-20
End:   2024-05-26
```

### 14.4 Criterios de Aceptación 2.3B

| Criterio | Estado |
|----------|--------|
| Batch adicional ejecutado | ✅ |
| SQL recibe insert | ✅ |
| No duplicados | ✅ |
| MongoDB no es destino final | ✅ |
| Checkpoint actualizado | ✅ |
| Backend RUNNING | ✅ |

---

## 15. Validación SoftRestaurant — 130° MERIDA (2026-04-26)

### 15.1 Objetivo
Validar que el flujo de carga histórica funciona correctamente con servidores SoftRestaurant, usando:
- system_type_normalized = SOFTRESTAURANT
- Adapter SoftRestaurant
- UPSERT en EDARSAHUB SQL

### 15.2 Servidor Probado

| Campo | Valor |
|-------|-------|
| Server ID | `a5547321-1139-4d2b-9d53-182ca737b6b6` |
| Nombre | 130° MERIDA |
| system_type | SoftRestaurant |
| Host | 130mid.ddns.net |
| Database | softrestaurant10 |

### 15.3 Resultado

| Métrica | Valor |
|---------|-------|
| Run ID | `HL_20260426_005005` |
| Batch | 2024-05-06 a 2024-05-12 |
| **SQL insertados** | **7** ✅ |
| **MongoDB final** | **0** ✅ |
| **Duplicados SQL** | **0** ✅ |
| Adapter usado | SoftRestaurant ✅ |

### 15.4 Comparativa MPRO vs SoftRestaurant

| system_type | Servidores | Sucursales | Registros SQL |
|-------------|------------|------------|---------------|
| MANAGEMENTPRO | 1 | 2 | 28 |
| SOFTRESTAURANT | 1 | 1 | 7 |
| **Total** | **2** | **3** | **35** |

### 15.5 Criterios de Aceptación SoftRestaurant

| Criterio | Estado |
|----------|--------|
| Proceso sin crash | ✅ |
| Usa adapter SoftRestaurant | ✅ |
| SQL recibe insert | ✅ |
| MongoDB final = 0 | ✅ |
| No duplicados | ✅ |
| Checkpoint creado | ✅ |
| No secretos expuestos | ✅ |

---

## 16. MACROFASE 2.3C — Mayo 2024 Completo (2026-04-26)

### 16.1 Objetivo
Completar el mes de mayo 2024 para los dos servidores validados.

### 16.2 Resultado por Servidor

| Servidor | system_type | Rango | Días | Registros SQL |
|----------|-------------|-------|------|---------------|
| ManagmentPro | MANAGEMENTPRO | 2024-05-06 a 2024-05-31 | 26 | **53** |
| 130° MERIDA | SOFTRESTAURANT | 2024-05-06 a 2024-05-31 | 26 | **26** |
| **Total** | — | — | — | **79** |

### 16.3 Validación

| Verificación | Resultado |
|--------------|-----------|
| Duplicados SQL mayo 2024 | **0** ✅ |
| MongoDB final insertados | **0** ✅ |
| Backend RUNNING | ✅ |
| Comercial funcionando | ✅ |

### 16.4 Criterios de Aceptación

| Criterio | Estado |
|----------|--------|
| Mayo completo ManagmentPro | ✅ |
| Mayo completo 130° MERIDA | ✅ |
| MongoDB final = 0 | ✅ |
| SQL duplicates = 0 | ✅ |
| Checkpoints actualizados | ✅ |
| No se tocaron otros servidores | ✅ |

### 16.5 Siguiente Paso
Continuar con **junio 2024** para ambos servidores.

---

## 17. Junio 2024 Completo (2026-04-26)

### 17.1 Resultado por Servidor

| Servidor | system_type | Rango | Registros SQL |
|----------|-------------|-------|---------------|
| ManagmentPro | MANAGEMENTPRO | 2024-06-01 a 2024-06-30 | **63** |
| 130° MERIDA | SOFTRESTAURANT | 2024-06-01 a 2024-06-30 | **30** |
| **Total junio** | — | — | **93** |

### 17.2 Acumulado Total (Mayo + Junio)

| system_type | Rango | Registros |
|-------------|-------|-----------|
| MANAGEMENTPRO | 2024-05-06 a 2024-06-30 | 116 |
| SOFTRESTAURANT | 2024-05-06 a 2024-06-30 | 56 |
| **TOTAL** | — | **172** |

### 17.3 Validación

| Verificación | Resultado |
|--------------|-----------|
| Duplicados SQL junio 2024 | **0** ✅ |
| MongoDB final | **0** ✅ |
| Backend RUNNING | ✅ |

### 17.4 Progreso Carga Histórica

| Meses cargados | 2 de 24 (8.3%) |
|----------------|----------------|
| Mayo 2024 | ✅ |
| Junio 2024 | ✅ |
| Pendientes | Jul 2024 → Abr 2026 |

