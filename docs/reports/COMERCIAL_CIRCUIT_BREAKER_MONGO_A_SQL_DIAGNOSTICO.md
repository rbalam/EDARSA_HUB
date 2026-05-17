# DIAGNÓSTICO: Migración Circuit Breaker de MongoDB a EDARSAHUB SQL

**Fecha:** 2026-05-17  
**Módulo:** Comercial (Tablero Ejecutivo V1)  
**Estado:** DIAGNÓSTICO COMPLETADO  
**Prioridad:** P0 - CRÍTICO  

---

## 1. RESUMEN EJECUTIVO

Se identificó que el módulo Comercial depende de MongoDB para:
- Estado de conexión de servidores (`server_status`)
- Circuit breaker (`is_server_recently_offline`)
- Decisión de intentar query live (`should_attempt_live_query`)
- Caché de KPIs (`kpis_cache`)
- Caché de Dashboard (`dashboard_cache`)

**VIOLACIÓN ARQUITECTÓNICA:** EDARSAHUB SQL debe ser el cerebro del sistema. MongoDB NO debe usarse para decisiones operativas.

---

## 2. DEPENDENCIAS MONGODB IDENTIFICADAS

### 2.1 Colección: `server_status`

| Archivo | Función | Línea | Uso |
|---------|---------|-------|-----|
| `repository.py` | `save_server_connection_status()` | 571-584 | Guarda estado online/offline |
| `repository.py` | `get_server_connection_status()` | 587-589 | Lee estado de conexión |
| `repository.py` | `is_server_recently_offline()` | 596-637 | Circuit breaker |
| `repository.py` | `should_attempt_live_query()` | 640-664 | Decide si intentar query live |
| `routes.py` | `tablero_ejecutivo` | 765 | Usa `should_attempt_live_query` |
| `routes.py` | `tablero_ejecutivo` | 783, 786 | Guarda estado tras consulta |

**Decisión que toma:** Si el servidor fue marcado offline en los últimos 10 minutos, NO intenta consultar y usa caché directamente.

**Módulo afectado:** Tablero Ejecutivo V1 (`/api/comercial/tablero-ejecutivo`)

### 2.2 Colección: `kpis_cache`

| Archivo | Función | Línea | Uso |
|---------|---------|-------|-----|
| `repository.py` | `get_cached_kpis()` | 537-543 | Lee caché de KPIs |
| `repository.py` | `save_kpis_cache()` | 545-560 | Guarda caché de KPIs |
| `repository.py` | `get_cached_kpis_by_prefix()` | 562-569 | Lee caché por prefijo (MPRO) |
| `routes.py` | Múltiples | ~939, 985, 1095 | Fallback cuando falla conexión |

**Decisión que toma:** Si el circuit breaker está activo, retorna datos de esta caché en lugar de consultar EDARSAHUB.

### 2.3 Colección: `dashboard_cache`

| Archivo | Función | Línea | Uso |
|---------|---------|-------|-----|
| `repository.py` | `save_dashboard_cache()` | 671-684 | Guarda caché de Dashboard |
| `repository.py` | `get_dashboard_cache()` | 687-693 | Lee caché de Dashboard |

**Módulo afectado:** Dashboard Comercial individual por servidor.

---

## 3. FLUJO ACTUAL (INCORRECTO)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FLUJO ACTUAL (CON MONGODB)                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Request: GET /api/comercial/tablero-ejecutivo                   │
│                           │                                         │
│                           ▼                                         │
│  2. should_attempt_live_query(server_id, "HUB")                     │
│                           │                                         │
│                           ▼                                         │
│  3. is_server_recently_offline() ───► MongoDB: server_status        │
│                           │                     ▲                   │
│              ┌────────────┴────────────┐        │                   │
│              │                         │        │                   │
│         should_try=True          should_try=False                   │
│              │                         │        │                   │
│              ▼                         ▼        │                   │
│  4a. get_kpis_softrestaurant()  4b. get_cached_kpis()               │
│      (Lee de EDARSAHUB!)             (MongoDB: kpis_cache)          │
│              │                         │                            │
│              ▼                         ▼                            │
│  5. Retorna DATA_OK             Retorna DATA_FROM_CACHE             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

PROBLEMA CRÍTICO:
- get_kpis_softrestaurant() YA lee de EDARSAHUB SQL
- El circuit breaker bloquea una consulta que SIEMPRE funciona
- El resultado es DATA_FROM_CACHE con datos viejos de MongoDB
```

---

## 4. FLUJO CORRECTO (PROPUESTO)

```
┌─────────────────────────────────────────────────────────────────────┐
│                 FLUJO CORRECTO (SQL-FIRST)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Request: GET /api/comercial/tablero-ejecutivo                   │
│                           │                                         │
│                           ▼                                         │
│  2. Para modo HUB (datos consolidados):                             │
│     SIEMPRE leer de EDARSAHUB SQL                                   │
│     (No circuit breaker, no MongoDB)                                │
│                           │                                         │
│                           ▼                                         │
│  3. get_kpis_softrestaurant() → EDARSAHUB SQL                       │
│                           │                                         │
│              ┌────────────┴────────────┐                            │
│              │                         │                            │
│         SUCCESS                    ERROR CONEXIÓN                   │
│              │                         │                            │
│              ▼                         ▼                            │
│  4a. Retorna DATA_OK           4b. Registrar error en SQL           │
│                                    Retornar DATA_ERROR              │
│                                    (NO usar caché MongoDB)          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

MÁXIMA: EDARSAHUB es el cerebro. Si EDARSAHUB falla, es un error crítico.
        NO hay fallback a MongoDB.
```

---

## 5. TABLA SQL EQUIVALENTE EXISTENTE

### 5.1 Tablas Existentes Relevantes

| Tabla | Propósito | Campos Relevantes |
|-------|-----------|-------------------|
| `Servidores_Conexiones` | Catálogo de servidores | `source_status`, `fecha_ultima_sincronizacion`, `ultimo_error_sync` |
| `Servidores_Conexiones_Log` | Bitácora de cambios | `accion`, `fecha` |
| `Comercial_SyncLog_v2` | Log de sincronizaciones | `source_connection_status`, `status`, `error_message` |
| `Sync_Control_Ejecuciones` | Control de jobs de sync | `Status`, `ErrorMessage`, `FinishedAtMexico` |

### 5.2 Campos en `Servidores_Conexiones` (YA EXISTENTES)

```sql
-- Campos existentes pero NO poblados:
source_status VARCHAR            -- Estado actual: NULL en todos los registros
fecha_ultima_sincronizacion DATETIME2  -- Última sync: NULL en todos
ultimo_error_sync NVARCHAR       -- Último error: NULL en todos
```

### 5.3 Campos en `Comercial_SyncLog_v2` (POBLADOS Y FUNCIONALES)

```sql
-- Campos funcionales (última sincronización 2026-05-17 17:06):
source_connection_status NVARCHAR  -- Valores: 'ONLINE', 'OFFLINE'
status NVARCHAR                    -- Valores: 'SUCCESS', 'ERROR'
error_message NVARCHAR             -- Detalle del error
created_at DATETIME2               -- Timestamp de la operación
```

---

## 6. PROPUESTA DE SOLUCIÓN

### 6.1 Opción A: Usar `Comercial_SyncLog_v2` (RECOMENDADA)

**Ventaja:** Ya está poblada con datos de sync cada 5 minutos.

**Lógica propuesta:**
```sql
-- Para determinar estado de conexión de una unidad:
SELECT TOP 1 
    source_connection_status,
    status,
    created_at
FROM Comercial_SyncLog_v2
WHERE unidad_negocio_id = @unidad
ORDER BY created_at DESC

-- Si status='SUCCESS' y created_at < 15 min: ONLINE
-- Si status='ERROR' o created_at > 15 min: verificar EDARSAHUB directamente
```

### 6.2 Opción B: Crear tabla `Servidores_EstadoConexion` (SI SE REQUIERE DEDICADA)

**DDL Propuesto (siguiendo patrón EDARSAHUB):**

```sql
CREATE TABLE Servidores_EstadoConexion (
    EstadoConexionID INT IDENTITY(1,1) PRIMARY KEY,
    ServidorID UNIQUEIDENTIFIER NOT NULL,
    UnidadNegocioID NVARCHAR(50) NULL,
    FuenteProceso NVARCHAR(100) NOT NULL,  -- 'TABLERO_V1', 'SYNC_JOB', 'MANUAL'
    Estado NVARCHAR(20) NOT NULL,          -- 'ONLINE', 'OFFLINE', 'DEGRADED', 'ERROR'
    UltimoIntento DATETIME2 NOT NULL,
    UltimoExito DATETIME2 NULL,
    UltimoFallo DATETIME2 NULL,
    FallosConsecutivos INT DEFAULT 0,
    CircuitAbierto BIT DEFAULT 0,
    CircuitAbiertoHasta DATETIME2 NULL,
    MensajeErrorSeguro NVARCHAR(500) NULL,
    FechaCreacion DATETIME2 DEFAULT GETUTCDATE(),
    FechaModificacion DATETIME2 DEFAULT GETUTCDATE(),
    Activo BIT DEFAULT 1,
    
    CONSTRAINT FK_EstadoConexion_Servidor 
        FOREIGN KEY (ServidorID) REFERENCES Servidores_Conexiones(id)
);

CREATE INDEX IX_EstadoConexion_Servidor ON Servidores_EstadoConexion(ServidorID);
CREATE INDEX IX_EstadoConexion_Unidad ON Servidores_EstadoConexion(UnidadNegocioID);
```

---

## 7. CAMBIOS REQUERIDOS EN CÓDIGO

### 7.1 Archivo: `/app/backend/modules/comercial/repository.py`

| Función | Cambio Requerido |
|---------|------------------|
| `save_server_connection_status()` | ELIMINAR o migrar a SQL (Opción B) |
| `get_server_connection_status()` | ELIMINAR o migrar a SQL (Opción B) |
| `is_server_recently_offline()` | ELIMINAR - No aplica para tableros |
| `should_attempt_live_query()` | MODIFICAR: Siempre retornar `True` para modo HUB |

### 7.2 Archivo: `/app/backend/modules/comercial/routes.py`

| Línea | Cambio Requerido |
|-------|------------------|
| 765 | Eliminar llamada a `should_attempt_live_query` para modo HUB |
| 783, 786 | Eliminar llamadas a `save_server_connection_status` |
| ~939, 985, 1095 | Eliminar lógica de fallback a `kpis_cache` MongoDB |

---

## 8. RIESGOS Y MITIGACIÓN

| Riesgo | Mitigación |
|--------|------------|
| Romper Tablero Ejecutivo | Pruebas incrementales, rollback disponible |
| Romper Comercial V2 | No tocar módulo V2 |
| Romper Auth/RBAC | No tocar módulos de auth |
| EDARSAHUB no disponible | Registrar error crítico, NO usar MongoDB |

---

## 9. FASES DE MIGRACIÓN

### Fase 1: Tablero Ejecutivo V1 - Eliminar Circuit Breaker (PRIORIDAD)
1. Modificar `should_attempt_live_query()` para siempre retornar `True` en modo HUB
2. Eliminar guardado de estado en MongoDB tras consultas exitosas
3. Eliminar lógica de fallback a `kpis_cache`
4. Validar que todas las unidades muestren `DATA_OK`

### Fase 2: Evaluar necesidad de tabla SQL dedicada
1. Analizar si `Comercial_SyncLog_v2` es suficiente
2. Si se requiere tabla dedicada, ejecutar DDL
3. Migrar funciones de estado a SQL

### Fase 3: Limpieza de código
1. Eliminar funciones MongoDB obsoletas
2. Eliminar colecciones MongoDB: `server_status`, `kpis_cache`
3. Actualizar documentación

---

## 10. VALIDACIÓN

### Criterios de Aceptación

- [ ] Tablero Ejecutivo V1 NO consulta MongoDB para circuit breaker
- [ ] Tablero Ejecutivo V1 NO usa MongoDB `server_status`
- [ ] Tablero Ejecutivo V1 siempre lee de EDARSAHUB
- [ ] Todas las unidades muestran `DATA_OK` (no `DATA_FROM_CACHE`)
- [ ] Comercial V2 NO afectado
- [ ] Auth/RBAC NO afectado
- [ ] No hay live queries a servidores locales desde tableros

### Comando de Validación Post-Migración

```bash
# Verificar que no hay DATA_FROM_CACHE:
curl -s "$API_URL/api/comercial/tablero-ejecutivo" -H "Authorization: Bearer $TOKEN" | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print('PASS' if all(u.get('data_status')=='DATA_OK' for u in d.get('unidades',[])) else 'FAIL')"
```

---

## 11. CONFIRMACIÓN

**Código productivo NO modificado en este diagnóstico.**

El presente documento es un diagnóstico. La implementación requiere autorización explícita.

---

**Autor:** Sistema E1  
**Validado por:** Pendiente autorización  
**Próximo paso:** Autorizar Fase 1 para eliminar circuit breaker MongoDB del Tablero Ejecutivo V1
