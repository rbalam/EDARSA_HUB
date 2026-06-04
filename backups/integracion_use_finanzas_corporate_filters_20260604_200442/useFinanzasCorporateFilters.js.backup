import { useMemo, useCallback } from "react";
import { useCorporateFilters } from "./CorporateFiltersProvider";

/**
 * Adapter de compatibilidad para Finanzas.
 *
 * Objetivo:
 * Permitir que Finanzas.js y sus tabs hijos migren gradualmente
 * sin romper props actuales.
 *
 * Fuente de verdad:
 * CorporateFiltersProvider / EDARSAHUB SQL
 */
export function useFinanzasCorporateFilters() {
  const {
    filters,
    selected,
    setFilterValue,
    loading,
    error,
    status,
    transport,
    reload,
    clearFilters
  } = useCorporateFilters();

  const unidadesNegocio = useMemo(() => {
    return filters?.unidades_negocio || [];
  }, [filters]);

  const selectedUnidad = selected?.unidades_negocio || "";

  const unidadActual = useMemo(() => {
    if (!selectedUnidad) return null;

    return unidadesNegocio.find((unidad) => String(unidad.id) === String(selectedUnidad)) || null;
  }, [selectedUnidad, unidadesNegocio]);

  const setSelectedUnidad = useCallback(
    (value) => {
      setFilterValue("unidades_negocio", value || "");
    },
    [setFilterValue]
  );

  const hasSingleUnidad = unidadesNegocio.length === 1;

  const selectedUnidadNombre = unidadActual?.nombre || "";
  const selectedUnidadCodigo = unidadActual?.codigo || "";

  return {
    // Compatibilidad con Finanzas.js legacy
    unidadesNegocio,
    selectedUnidad,
    setSelectedUnidad,
    loadingUnidades: loading,
    unidadActual,
    selectedUnidadNombre,
    selectedUnidadCodigo,
    hasSingleUnidad,

    // Corporate Filters completo
    corporateFilters: filters,
    corporateSelected: selected,
    corporateStatus: status,
    corporateError: error,
    corporateTransport: transport,

    // Utilidades
    reloadCorporateFilters: reload,
    clearCorporateFilters: clearFilters
  };
}

export default useFinanzasCorporateFilters;
