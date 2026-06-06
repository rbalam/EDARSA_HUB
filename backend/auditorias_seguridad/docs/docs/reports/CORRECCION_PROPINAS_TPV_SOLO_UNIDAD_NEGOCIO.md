# Corrección PropinasTPV - Solo Unidad de Negocio

Fecha: Thu Jun  4 17:07:39 UTC 2026

## Referencias clave
```text
25:import { CorporateFiltersProvider, CorporateFilterBar, useCorporateFilters } from '../filters';
90:      const resV2 = await fetch(`${API_URL}/api/finanzas/propinas/v2/unidades`, {
114:      const unidadesCF = corporateFilters?.unidades_negocio || [];
138:      const res = await fetch(`${API_URL}/api/finanzas/propinas/config/all`, {
170:      const res = await fetch(`${API_URL}/api/finanzas/propinas/v2/detalle?${params.toString()}`, {
236:        ? `${API_URL}/api/finanzas/propinas/config`
237:        : `${API_URL}/api/finanzas/propinas/config/${configData.id}`;
478:    <CorporateFiltersProvider scope="finanzas.propinas_tpv">
479:      <CorporateFilterBar
483:            key: "unidades_negocio",
491:    </CorporateFiltersProvider>
```
## Build frontend
```text
  20.67 kB (+15 B)    build/static/css/main.2773ac81.css
  8.73 kB             build/static/js/977.8591a78c.chunk.js

The bundle size is significantly larger than recommended.
Consider reducing it with code splitting: https://goo.gl/9VhYWB
You can also analyze the project dependencies: https://goo.gl/LeUzfb

The project was built assuming it is hosted at /.
You can control this with the homepage field in your package.json.

The build folder is ready to be deployed.
You may serve it with a static server:

  yarn global add serve
  serve -s build

Find out more about deployment here:

  https://cra.link/deployment

```

## Resultado

Corrección aplicada correctamente.

### Cambio de UX

PropinasTPV ahora muestra solo:

- Unidad de Negocio

No muestra en Corporate Filters:

- Empresa
- Sucursal
- Servidor

### Regla de usuario con una sola unidad

Si Corporate Filters devuelve una sola opción para `unidades_negocio`:

- Se precarga automáticamente.
- El filtro queda bloqueado.
- El usuario no tiene que seleccionarlo manualmente.

### Pendiente funcional

Validar visualmente que el KPI vuelva a mostrar información.  
Si sigue en cero, el siguiente ajuste debe conectar `corporateSelected.unidades_negocio` con el payload real de búsqueda de `/api/finanzas/propinas/*`.

### Backup

```text
/app/backups/propinas_tpv_unidad_negocio_20260604_170739
```
