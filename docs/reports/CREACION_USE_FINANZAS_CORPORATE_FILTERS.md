# Creación useFinanzasCorporateFilters

Fecha: 2026-06-04

## Objetivo

Crear un adapter de compatibilidad para Finanzas.

Este hook centraliza Corporate Filters para Finanzas sin migrar de golpe los componentes hijos.

## Reglas

- No modificar componentes hijos todavía.
- No tocar PropinasTPV.
- No eliminar props actuales.
- No migrar otros módulos.
- Mantener compatibilidad con nombres usados por Finanzas.js.

## Hook Creado

**Archivo:** `/app/frontend/src/filters/useFinanzasCorporateFilters.js`

### API del Hook

```javascript
const {
  // Compatibilidad con Finanzas.js legacy
  unidadesNegocio,           // Array de unidades de negocio
  selectedUnidad,             // ID de unidad seleccionada
  setSelectedUnidad,          // Función para cambiar unidad
  loadingUnidades,            // Boolean de carga
  unidadActual,               // Objeto de la unidad actual
  selectedUnidadNombre,       // Nombre de la unidad actual
  selectedUnidadCodigo,       // Código de la unidad actual
  hasSingleUnidad,            // Boolean si solo hay una unidad

  // Corporate Filters completo
  corporateFilters,           // Todos los filtros
  corporateSelected,          // Valores seleccionados
  corporateStatus,            // Estado de la conexión
  corporateError,             // Error si existe
  corporateTransport,         // Método de transporte

  // Utilidades
  reloadCorporateFilters,     // Recargar filtros
  clearCorporateFilters       // Limpiar filtros
} = useFinanzasCorporateFilters();
```

## Componentes Hijos Identificados

| Componente | Ubicación | Estado |
|------------|-----------|--------|
| FinanzasDashboard | `/app/frontend/src/components/finanzas/FinanzasDashboard.jsx` | Pendiente migrar |
| FinanzasPresupuestos | `/app/frontend/src/components/finanzas/FinanzasPresupuestos.jsx` | Pendiente migrar |
| FinanzasCuentasPorPagar | `/app/frontend/src/components/finanzas/FinanzasCuentasPorPagar.jsx` | Pendiente migrar |
| FinanzasControlIngresos | `/app/frontend/src/components/finanzas/FinanzasControlIngresos.jsx` | Pendiente migrar |
| TesoreriaCorteZ | `/app/frontend/src/components/TesoreriaCorteZ.jsx` | Existente |
| PropinasTPV | `/app/frontend/src/components/PropinasTPV.jsx` | ✅ Ya usa Corporate Filters |

## Build

**Estado:** ✅ EXITOSO

## Siguiente Paso

Opción 1: Usar este hook en `Finanzas.js` para simplificar el código existente.
Opción 2: Migrar gradualmente cada componente hijo para usar el hook directamente.

## Uso Ejemplo en Finanzas.js

```jsx
import { useFinanzasCorporateFilters } from '../filters';

function FinanzasContent() {
  const {
    unidadesNegocio,
    selectedUnidad,
    setSelectedUnidad,
    loadingUnidades,
    unidadActual
  } = useFinanzasCorporateFilters();

  // Pasa props a componentes hijos sin cambios
  return (
    <FinanzasDashboard 
      unidadesNegocio={unidadesNegocio}
      selectedUnidad={selectedUnidad}
      // ...otros props
    />
  );
}
```
