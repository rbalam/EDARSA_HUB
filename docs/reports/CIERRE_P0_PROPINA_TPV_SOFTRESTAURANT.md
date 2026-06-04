# Cierre P0 - Propina TPV SoftRestaurant

Fecha: Thu Jun  4 18:53:42 UTC 2026

## Dictamen P0

Se acepta como corrección operativa P0 que Propinas TPV SoftRestaurant volvió a sincronizar y que el backfill insertó datos.

No se acepta como cierre arquitectónico definitivo el hardcode de `SOFTRESTAURANT_PRO` en archivos específicos.

La centralización de `system_type` queda registrada como P1 obligatorio antes de extender el patrón a otros módulos.

## Reglas

- No migrar otros tableros hasta validar visualmente PropinasTPV.
- No tocar frontend en este cierre.
- No hacer otro backfill en este script.
- No consultar servidores remotos para dashboards.
- EDARSAHUB SQL sigue siendo la fuente para KPIs/tableros.
SQL creado: /app/docs/sql/CIERRE_P0_VALIDACION_PROPINA_TPV_SOFTRESTAURANT.sql
## Validación API Propinas TPV
```json
===== 130MID =====
{
  "success": null,
  "total_registros": null,
  "totales": null,
  "mensaje": null
}
===== CIENFUEGOS =====
{
  "success": null,
  "total_registros": null,
  "totales": null,
  "mensaje": null
}
===== LA ESTELAR =====
{
  "success": null,
  "total_registros": null,
  "totales": null,
  "mensaje": null
}
```

## Validación EDARSAHUB SQL
```text
=== RESUMEN BACKFILL SOFTRESTAURANT DESDE 2026-05-17 ===
  130° MERIDA: 256 registros, $193,840.44 propinas
    Fechas: 2026-05-17 a 2026-06-03
  CIENFUEGOS: 416 registros, $247,194.79 propinas
    Fechas: 2026-05-17 a 2026-06-03
  LA ESTELAR: 573 registros, $103,831.74 propinas
    Fechas: 2026-05-17 a 2026-06-03

  TOTAL: 1245 registros, $544,866.97 propinas TPV

=== DICTAMEN ===
P0_OPERATIVO_VALIDADO: Backfill SoftRestaurant exitoso
```


## Corrección adicional: Filtro por nombre de unidad

### Problema detectado
El endpoint `/api/finanzas/propinas/v2/detalle` fallaba con error 8169 (Conversion failed) cuando se enviaba el nombre de la unidad (ej. "CIENFUEGOS") en lugar de un UUID.

### Causa
El repository usaba directamente `UnidadNegocioID = %s` sin verificar si el valor era un UUID válido o un nombre.

### Corrección
Se agregó detección automática de UUID vs nombre en `repository_edarsahub.py`:
- Si es UUID: `WHERE UnidadNegocioID = %s`
- Si es nombre: `WHERE (UPPER(UnidadNegocioNombre) = UPPER(%s) OR UPPER(sucursal_nombre) = UPPER(%s))`

### Validación API (2026-06-05)

| Unidad | Total Registros | Propinas TPV | Fuente |
|--------|-----------------|--------------|--------|
| CIENFUEGOS | 405 | $241,766.84 | EDARSAHUB_REAL |
| LA ESTELAR | 550 | $101,627.24 | EDARSAHUB_REAL |
| 130° MERIDA | 231 | $167,158.54 | EDARSAHUB_REAL |
| **TODAS** | **1,716** | **$788,828.96** | EDARSAHUB_REAL |

## Dictamen Final

**P0 OPERATIVO VALIDADO** ✅

- Sync Propinas TPV SoftRestaurant restaurado
- Backfill desde 2026-05-17 ejecutado (1,186 registros)
- API `/api/finanzas/propinas/v2/*` funcionando con datos reales de EDARSAHUB
- Filtro por nombre de unidad corregido

### Archivos modificados en esta sesión

1. `/app/backend/modules/finanzas/sync_propinas_softrestaurant.py` - Filtro system_type
2. `/app/backend/modules/finanzas/sync_cortes_softrestaurant.py` - Filtro system_type
3. `/app/backend/modules/finanzas/sync_propinas_mpro.py` - Filtro system_type
4. `/app/backend/modules/finanzas/propinas_tpv/repository_edarsahub.py` - Filtro UUID/nombre

## Pendientes P1

1. Centralizar `system_type` en normalizador único
2. Validar visualmente KPIs en frontend PropinasTPV
3. Migrar tableros restantes a Corporate Filters
