# Corrección Auth Corporate Filters Frontend

Fecha: Thu Jun  4 18:01:31 UTC 2026


## Resultado

Corrección aplicada correctamente.

### Cambios

- `corporateFiltersApi.js` ahora envía:
  - Authorization Bearer si existe token
  - credentials: "include" para cookies httpOnly
  - fallback a same-origin si REACT_APP_BACKEND_URL da 502/503/504

- `CorporateFiltersProvider.jsx` ahora:
  - conserva transport/debug de URL usada
  - precarga filtros únicos
  - expone mejor error de carga

- `CorporateFilterBar.jsx` ahora muestra:
  - Estado
  - Fuente EDARSAHUB SQL
  - URL usada para debug

### Backups

```text
/app/backups/correccion_auth_corporate_filters_20260604_180131
```
