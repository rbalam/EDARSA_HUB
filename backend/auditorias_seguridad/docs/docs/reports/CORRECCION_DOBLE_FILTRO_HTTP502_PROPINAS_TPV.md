# Corrección doble filtro y HTTP 502 Corporate Filters

Fecha: Thu Jun  4 17:33:19 UTC 2026


## Resultado

Corrección aplicada correctamente.

### Cambios

- `corporateFiltersApi.js` ahora usa fallback:
  1. REACT_APP_BACKEND_URL
  2. same-origin relativo

- PropinasTPV muestra solo una Unidad de Negocio en Corporate Filters.
- Se agregó `getUnidadNegocioParaConsulta()` para derivar la unidad efectiva.
- No se restauraron `/api/servers` ni `/api/sucursales`.

### Validación Backend

```json
curl http://localhost:8001/api/corporate-filters/bootstrap?scope=finanzas.propinas_tpv

Success: true
Empresas: 5
Unidades: 5
Servidores: 14
```

### Backups

```text
/app/backups/correccion_doble_filtro_http502_20260604_173319
```
