import React from "react";
import { useCorporateFilters } from "./CorporateFiltersProvider";
import { CorporateFilterSelect } from "./CorporateFilterSelect";

export function CorporateFilterBar({ filters = [] }) {
  const { loading, error, status, clearFilters, reload } = useCorporateFilters();

  return (
    <div className="bg-white border rounded-lg p-4 mb-4">
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {filters.map((filter) => (
          <CorporateFilterSelect
            key={filter.key}
            filterKey={filter.key}
            label={filter.label}
            placeholder={filter.placeholder || "Todos"}
            disabled={filter.disabled}
          />
        ))}
      </div>

      <div className="flex items-center gap-2 mt-4">
        <button type="button" className="border rounded px-3 py-2 text-sm" onClick={clearFilters}>
          Limpiar filtros
        </button>

        <button type="button" className="border rounded px-3 py-2 text-sm" onClick={reload}>
          Recargar filtros
        </button>

        <span className="text-xs text-gray-500">
          {loading ? "Cargando..." : `Estado: ${status?.status || "OK"}`}
        </span>

        {error && (
          <span className="text-xs text-red-600">
            {error}
          </span>
        )}
      </div>
    </div>
  );
}
