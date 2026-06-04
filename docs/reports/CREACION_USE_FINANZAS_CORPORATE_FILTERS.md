# Creación useFinanzasCorporateFilters

Fecha: Thu Jun  4 20:02:09 UTC 2026

## Objetivo

Crear un adapter de compatibilidad para Finanzas.

Este hook centraliza Corporate Filters para Finanzas sin migrar de golpe los componentes hijos.

## Reglas

- No modificar componentes hijos todavía.
- No tocar PropinasTPV.
- No eliminar props actuales.
- No migrar otros módulos.
- Mantener compatibilidad con nombres usados por Finanzas.js.
Backups en: /app/backups/use_finanzas_corporate_filters_20260604_200209
## Archivos creados/actualizados
```text
-rw-r--r-- 1 root root  293 Jun  4 19:58 /app/frontend/src/filters/index.js
-rw-r--r-- 1 root root 1843 Jun  4 20:02 /app/frontend/src/filters/useFinanzasCorporateFilters.js
14:export function useFinanzasCorporateFilters() {
27:  const unidadesNegocio = useMemo(() => {
31:  const selectedUnidad = selected?.unidades_negocio || "";
33:  const unidadActual = useMemo(() => {
34:    if (!selectedUnidad) return null;
36:    return unidadesNegocio.find((unidad) => String(unidad.id) === String(selectedUnidad)) || null;
37:  }, [selectedUnidad, unidadesNegocio]);
39:  const setSelectedUnidad = useCallback(
46:  const hasSingleUnidad = unidadesNegocio.length === 1;
48:  const selectedUnidadNombre = unidadActual?.nombre || "";
49:  const selectedUnidadCodigo = unidadActual?.codigo || "";
53:    unidadesNegocio,
54:    selectedUnidad,
55:    setSelectedUnidad,
57:    unidadActual,
58:    selectedUnidadNombre,
59:    selectedUnidadCodigo,
63:    corporateFilters: filters,
64:    corporateSelected: selected,
75:export default useFinanzasCorporateFilters;
export { CorporateFiltersProvider, useCorporateFilters } from "./CorporateFiltersProvider";
export { CorporateFilterBar } from "./CorporateFilterBar";
export { CorporateFilterSelect } from "./CorporateFilterSelect";
export { useFinanzasCorporateFilters } from "./useFinanzasCorporateFilters";
```
## Validación no tocar hijos
```text
OK existe sin tocar en este script: /app/frontend/src/components/finanzas/FinanzasDashboard.jsx
OK existe sin tocar en este script: /app/frontend/src/components/finanzas/FinanzasPresupuestos.jsx
OK existe sin tocar en este script: /app/frontend/src/components/finanzas/FinanzasCuentasPorPagar.jsx
OK existe sin tocar en este script: /app/frontend/src/components/finanzas/FinanzasControlIngresos.jsx
OK existe sin tocar en este script: /app/frontend/src/components/TesoreriaCorteZ.jsx
OK existe sin tocar en este script: /app/frontend/src/components/PropinasTPV.jsx
```
## Build frontend
```text
  20.67 kB   build/static/css/main.2773ac81.css
  8.73 kB    build/static/js/977.8591a78c.chunk.js

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

Hook creado correctamente:

```text
/app/frontend/src/filters/useFinanzasCorporateFilters.js
```

Export actualizado:

```text
/app/frontend/src/filters/index.js
```

### Backup

```text
/app/backups/use_finanzas_corporate_filters_20260604_200209
```

## Siguiente paso

Usar este hook en Finanzas.js como adapter, sin modificar todavía los componentes hijos.
