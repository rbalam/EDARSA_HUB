# EDARSA HUB - Sync Históricos
## Módulo de Sincronización de Históricos a EDARSAHUB

**FASE:** SYNC-1  
**Fecha:** 2026-05-15  
**Estado:** Infraestructura Base

---

## Descripción

Este módulo implementa la sincronización de datos históricos desde las fuentes
operativas (SoftRestaurant, MPRO) hacia EDARSAHUB SQL Server.

## Ventana Operativa

**Default:** 13:00 - 11:00 (cruza medianoche)

- La jornada operativa de un restaurante inicia a las 13:00 del día D
- Continúa hasta las 11:00 del día D+1
- Todos los tickets entre 13:00 y 11:00 pertenecen al día operativo D

**Preparación para Módulo Futuro:**
- Los campos `ventana_inicio_hora_config` y `ventana_fin_hora_config` permiten
  configuración por unidad cuando se implemente el módulo de Horarios de Operación

## Tablas

### Sync_Ventas_Historicas
Ventas diarias consolidadas por unidad.

**Clave única:** `(ServerID, EmpresaID, FechaOperacion)`

### Sync_Ventas_PorHora
Distribución de ventas por hora del día.

**Clave única:** `(ServerID, EmpresaID, FechaOperacion, Hora)`

### Sync_Ventas_PorDiaSemana
Análisis agregado por día de la semana.

**Clave única:** `(ServerID, EmpresaID, FechaInicioPeriodo, FechaFinPeriodo, DiaSemana)`

### Sync_Control_Ejecuciones
Bitácora de ejecuciones de sincronización.

## Uso

### Inicializar Infraestructura

```python
from modules.sync_historicos import SyncHistoricosService

service = SyncHistoricosService()
result = service.inicializar_infraestructura()
print(result)  # {'Sync_Ventas_Historicas': True, ...}
```

### Dry-Run (Obligatorio)

```python
from modules.sync_historicos.sync_ventas import ejecutar_sync_ventas_dry_run

# Dry-run para todos los servidores, últimos 7 días
result = ejecutar_sync_ventas_dry_run(dias_atras=7)
print(f"Servidores OK: {result.servidores_exitosos}/{result.total_servidores}")
```

### Escritura Real (Solo después de dry-run)

```python
from modules.sync_historicos.sync_ventas import ejecutar_sync_ventas_real

# Escritura real para servidores específicos
result = ejecutar_sync_ventas_real(
    server_ids=['server-uuid-1', 'server-uuid-2'],
    dias_atras=7
)
```

## Campos de Control

Todas las tablas incluyen:

| Campo | Descripción |
|-------|-------------|
| `ServerID` | ID del servidor fuente |
| `EmpresaID` | ID de empresa |
| `SucursalID` | ID de sucursal (opcional) |
| `FechaOperacion` | Fecha operativa (NO calendario) |
| `VentanaInicioHoraConfig` | Hora inicio de jornada (13) |
| `VentanaFinHoraConfig` | Hora fin de jornada (11) |
| `SyncRunID` | ID único del run de sincronización |
| `SourceStatus` | SUCCESS, ERROR, SOURCE_FAILED, NO_DATA |
| `SourceType` | SOFTRESTAURANT, MPRO |
| `SyncedAtMexico` | Timestamp de sincronización (México) |
| `RowHash` | Hash para UPSERT idempotente |

## Protección Anti-$0 Falso

- Si falla la conexión a la fuente: NO se guarda venta $0
- Se registra `SourceStatus = SOURCE_FAILED`
- El error se documenta en la bitácora
- No se sobrescriben datos válidos con valores falsos

## Arquitectura

```
modules/sync_historicos/
├── __init__.py          # Exports públicos
├── models.py            # Dataclasses y tipos
├── repository.py        # DDL y UPSERT
├── service.py           # Lógica de negocio
├── sync_ventas.py       # Helpers de ejecución
└── README.md            # Esta documentación
```

## Restricciones FASE SYNC-1

- ✅ Solo lectura de fuentes
- ✅ Dry-run obligatorio antes de escritura
- ✅ Máximo 1 servidor SR + 1 servidor MPRO de prueba
- ✅ Rango máximo: 7 días
- ❌ NO ejecutar sync masivo para todos los servidores
- ❌ NO crear endpoints públicos
- ❌ NO modificar frontend
