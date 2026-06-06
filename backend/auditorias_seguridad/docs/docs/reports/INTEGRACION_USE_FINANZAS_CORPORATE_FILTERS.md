# Integración useFinanzasCorporateFilters en Finanzas.js

Fecha: Thu Jun  4 20:04:42 UTC 2026

Backups en: /app/backups/integracion_use_finanzas_corporate_filters_20260604_200442

## Reglas de este script

- Solo modifica Finanzas.js.
- No modifica componentes hijos.
- No toca PropinasTPV.
- No restaura fetchUnidadesNegocio.
- No restaura /api/servers.
- No restaura /api/sucursales.
- Mantiene props compatibles hacia hijos.
## Diagnóstico previo
```text
25:// MIGRACIÓN SQL-FIRST: Removido fetchUnidadesNegocio, ahora usa Corporate Filters
26:import { useCorporateFilters, CorporateFiltersProvider } from '../filters/CorporateFiltersProvider';
38:    <CorporateFiltersProvider scope="finanzas">
40:    </CorporateFiltersProvider>
45:  // MIGRACIÓN SQL-FIRST: Obtener unidades desde Corporate Filters en lugar de fetchUnidadesNegocio
51:  } = useCorporateFilters();
54:  const unidadesNegocio = useMemo(() => {
66:  const loadingUnidades = loadingCorporateFilters;
79:  const [selectedUnidad, setSelectedUnidad] = useState('');
101:  // userPermissions ahora se deriva de unidadesNegocio (contexto RBAC)
109:    unidadesNegocio.forEach(unidad => {
125:      canSeeAll: isAdmin || unidadesNegocio.length > 1,
128:  }, [unidadesNegocio]);
290:    if (!loadingUnidades && unidadesNegocio.length === 1 && !selectedUnidad) {
291:      const unidad = unidadesNegocio[0];
292:      setSelectedUnidad(unidad.id);
295:  }, [loadingUnidades, unidadesNegocio, selectedUnidad]);
299:    return unidadesNegocio.find(u => u.id === selectedUnidad) || null;
300:  }, [unidadesNegocio, selectedUnidad]);
328:        ...(selectedUnidad && { server_id: selectedUnidad })
337:  }, [fetchWithAuth, filtroAnio, filtroMes, selectedUnidad]);
346:        ...(selectedUnidad && { server_id: selectedUnidad })
355:  }, [fetchWithAuth, filtroAnio, filtroMes, selectedUnidad]);
393:      // === FASE 1 CxP: Usar selectedUnidad como filtro principal ===
394:      // DOCUMENTACIÓN: selectedUnidad contiene el UUID de la unidad de negocio
396:      // Mapeamos selectedUnidad → código de unidad para compatibilidad legacy
401:      if (selectedUnidad) {
402:        const unidadObj = unidadesNegocio.find(u => u.id === selectedUnidad);
510:  }, [fetchWithAuth, selectedUnidad, unidadesNegocio, cxpFiltroSucursal, cxpFiltroProveedor, cxpFechaCorte, cxpSoloVencidas, cxpSoloDecision, userPermissions]);
756:      if (selectedUnidad) params.append('unidad_negocio_id', selectedUnidad);
763:        fetchWithAuth(`/finanzas/ingresos/saldos-por-depositar${selectedUnidad ? `?unidad_negocio_id=${selectedUnidad}` : ''}`),
779:  }, [fetchWithAuth, selectedUnidad, ingresosFechaInicio, ingresosFechaFin, ingresosSoloPendientes]);
831:    if (activeTab === 'cxp' && selectedUnidad !== undefined) {
832:      logger.log(`[CxP] Unidad cambiada a: ${selectedUnidad || 'Todas'}, recargando...`);
835:  }, [selectedUnidad]); // Solo depende de selectedUnidad
966:        unidadesNegocio={unidadesNegocio}
967:        selectedUnidad={selectedUnidad}
968:        loadingUnidades={loadingUnidades}
973:        onUnidadChange={setSelectedUnidad}
987:      unidadesNegocio={unidadesNegocio}
988:      selectedUnidad={selectedUnidad}
989:      loadingUnidades={loadingUnidades}
993:      onUnidadChange={setSelectedUnidad}
1012:        unidadesNegocio={unidadesNegocio}
1013:        selectedUnidad={selectedUnidad}
1014:        loadingUnidades={loadingUnidades}
1023:        onUnidadChange={setSelectedUnidad}
1052:        unidadesNegocio={unidadesNegocio}
1053:        selectedUnidad={selectedUnidad}
1054:        loadingUnidades={loadingUnidades}
1067:        onUnidadChange={setSelectedUnidad}
```

## Resultado de Integración

### Cambios aplicados en Finanzas.js

1. **Import actualizado:**
   - Antes: `import { useCorporateFilters, CorporateFiltersProvider } from '../filters/CorporateFiltersProvider'`
   - Después: `import { useFinanzasCorporateFilters } from '../filters'` + `import { CorporateFiltersProvider } from '../filters/CorporateFiltersProvider'`

2. **Hook reemplazado:**
   - Antes: `useCorporateFilters()` con mapeo manual de unidadesNegocio
   - Después: `useFinanzasCorporateFilters()` que provee directamente:
     - `unidadesNegocio`
     - `selectedUnidad`
     - `setSelectedUnidad`
     - `loadingUnidades`
     - `unidadActual`

3. **Props hacia hijos mantenidos:**
   - `unidadesNegocio={unidadesNegocio}` ✅
   - `selectedUnidad={selectedUnidad}` ✅
   - `loadingUnidades={loadingUnidades}` ✅
   - `onUnidadChange={setSelectedUnidad}` ✅

### Hijos NO modificados

| Componente | Estado |
|------------|--------|
| FinanzasDashboard.jsx | ✅ Sin cambios |
| FinanzasPresupuestos.jsx | ✅ Sin cambios |
| FinanzasCuentasPorPagar.jsx | ✅ Sin cambios |
| FinanzasControlIngresos.jsx | ✅ Sin cambios |
| TesoreriaCorteZ.jsx | ✅ Sin cambios |
| CuentasBancariasPage.jsx | ✅ Sin cambios |
| PropinasTPV.jsx | ✅ Sin cambios |

### Build

**Estado:** ✅ EXITOSO

### Validación

- Login API local: ✅ Funcionando
- Corporate Filters Bootstrap: ✅ 5 unidades de negocio cargadas

## Backups

```text
/app/backups/integracion_use_finanzas_corporate_filters_20260604_200442/
```
