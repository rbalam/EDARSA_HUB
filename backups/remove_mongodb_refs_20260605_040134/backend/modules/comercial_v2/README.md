# COMERCIAL V2 - Módulo Aislado

## Estado: SUBFASE 1 - Sync Base (Desarrollo)

Este módulo implementa la sincronización de datos comerciales hacia EDARSAHUB
para el futuro Tablero Ejecutivo Comercial Blindado v2.

## IMPORTANTE - Restricciones

- **NO** está conectado al Tablero Ejecutivo actual
- **NO** modifica el módulo comercial existente (`/app/backend/modules/comercial/`)
- Escribe **SOLO** en tablas con sufijo `_v2` en EDARSAHUB
- **NO** expone endpoints públicos todavía
- **NO** tiene scheduler activo

## Estructura de Archivos

```
/app/backend/modules/comercial_v2/
├── __init__.py                        # Metadata del módulo
├── schemas.py                         # Modelos Pydantic
├── mappers.py                         # Mapeo SR/MPRO → EDARSAHUB
├── repository_comercial_edarsahub.py  # CRUD en tablas v2
├── sync_comercial_edarsahub.py        # Lógica de sincronización
└── README.md                          # Este archivo
```

## Tablas EDARSAHUB Usadas

| Tabla | Propósito |
|-------|-----------|
| `Comercial_KPIs_Diarios_v2` | KPIs diarios por unidad |
| `Comercial_KPIs_Mensuales_v2` | Agregados mensuales |
| `Comercial_Ventas_Dia_Abiertas_v2` | Snapshot de operación en curso |
| `Comercial_SyncLog_v2` | Log de sincronización |

## Sistemas Soportados

### SoftRestaurant
- **Ventas cerradas**: `cheques` + `turnos` (WHERE `t.cierre IS NOT NULL`)
- **Ventas abiertas**: `tempcheques`
- **Unidades**: 130° MÉRIDA, CIENFUEGOS, LA ESTELAR

### MPRO
- **Ventas cerradas**: `Venta_Encabezado` + `Comanda` (WHERE `Vn_Estatus = 'CER'`)
- **Ventas abiertas**: Ventas WHERE `Vn_Estatus != 'CER'`
- **Unidades**: 130° QRO (suc 0021), ORIGEN (suc 0023)

## Uso para Pruebas (Subfase 1)

```python
# Desde /app/backend
cd /app/backend

# Prueba SoftRestaurant (LA ESTELAR)
python3 -c "
from modules.comercial_v2.sync_comercial_edarsahub import test_sync_una_unidad_softrestaurant
from datetime import date
result = test_sync_una_unidad_softrestaurant(date(2026, 4, 30))
print(f'Success: {result.success}')
print(f'Processed: {result.records_processed}')
print(f'Inserted: {result.records_inserted}')
"

# Prueba MPRO (130° QRO)
python3 -c "
from modules.comercial_v2.sync_comercial_edarsahub import test_sync_una_unidad_mpro
from datetime import date
result = test_sync_una_unidad_mpro(date(2026, 4, 30))
print(f'Success: {result.success}')
print(f'Processed: {result.records_processed}')
"
```

## Manejo de Duplicados (HashOrigen)

Cada registro tiene un `hash_origen` calculado con:
- `server_id`
- `sucursal_id`
- `fecha`
- `ventas_total`
- `tickets_total`
- `pax_total`

Lógica de upsert:
1. Si existe con mismo hash → **SKIP**
2. Si existe con hash diferente → **UPDATE** (version++)
3. Si no existe → **INSERT**

## Ventas Cerradas vs Abiertas

| Tipo | Tabla Destino | Descripción |
|------|---------------|-------------|
| Cerradas | `Comercial_KPIs_Diarios_v2` | Cortes consolidados |
| Abiertas | `Comercial_Ventas_Dia_Abiertas_v2` | Snapshot operación en curso |

**Regla anti-duplicado**: Cuando una venta abierta se cierra, entra al corte
y se sincroniza en `KPIs_Diarios_v2`. El snapshot de abiertas se sobrescribe.

## Próximas Subfases

- **Subfase 2**: Ejecutar carga histórica (24 meses)
- **Subfase 3**: Crear endpoints v2
- **Subfase 4**: Integrar con feature flag
- **Subfase 5**: Activar scheduler

## Archivos NO Tocados

```
❌ /app/backend/modules/comercial/routes.py
❌ /app/backend/modules/comercial/service.py
❌ /app/backend/modules/comercial/repository.py
❌ /app/frontend/src/pages/Comercial/*
```

---

Fecha de creación: 01-Mayo-2026
Autor: E1 Agent
Estado: Subfase 1 Completada
