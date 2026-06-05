# P3-03 — Backfill Corporativo SQL-First

## Estado
**COMPLETADO** (Base segura)

## Fecha
2026-06-05

## Descripción
Módulo de re-sincronización histórica corporativa que opera en modo DRY_RUN por defecto.

## Arquitectura
- **NO** crea nuevas conexiones LIVE
- **NO** usa MongoDB
- **Modo DRY_RUN** por defecto (solo valida tablas/conteos)
- **COMMIT** requiere flag explícito

## Endpoints

### GET /api/admin/backfill/modulos
Retorna módulos disponibles:
```json
{
  "success": true,
  "modulos": ["COMPRAS", "INVENTARIOS", "PRECIOS", "PRODUCTOS", "RECETAS", "VENTAS", "VENTAS_HORA"]
}
```

### POST /api/admin/backfill
Request:
```json
{
  "server_id": "a5547321-...",
  "fecha_inicio": "2026-06-01",
  "fecha_fin": "2026-06-05",
  "modulo": "VENTAS",
  "dry_run": true
}
```

Response:
```json
{
  "success": true,
  "source": "EDARSAHUB_SQL",
  "mode": "DRY_RUN",
  "resultados": [
    {
      "tabla": "Comercial_KPIs_Diarios_v2",
      "existe": true,
      "total_actual": 3385
    }
  ]
}
```

## Tablas por Módulo

| Módulo | Tablas Destino |
|--------|---------------|
| VENTAS | Comercial_KPIs_Diarios_v2 |
| VENTAS_HORA | Sync_Ventas_PorHora |
| PRODUCTOS | Sync_Productos |
| PRECIOS | Sync_Precios_Historicos |
| RECETAS | Sync_Recetas |
| COMPRAS | Compras_Pedidos, Compras_PedidosDetalle, Compras_Ordenes, Compras_Recepciones |
| INVENTARIOS | Inventarios, Inventarios_Detalle, Inventarios_Fisicos |

## Archivos Creados
- `/app/backend/modules/backfill_corporativo/__init__.py`
- `/app/backend/modules/backfill_corporativo/service.py`
- `/app/backend/modules/backfill_corporativo/routes.py`

## Dictamen
✅ APROBADO - Base segura creada. Siguiente paso: implementar ejecución COMMIT por módulo.
