import React from "react";
import { useCorporateFilters } from "./CorporateFiltersProvider";
import { CorporateFilterSelect } from "./CorporateFilterSelect";

export function CorporateFilterBar({ filters = [], title = "Filtros" }) {
  const {
    status,
    loading,
    error,
    transport,
    clearFilters,
    reload
  } = useCorporateFilters();

  return (
    <div className="bg-white border rounded-lg p-4 mb-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-800">
          {title}
        </h3>

        <div className="flex items-center gap-2">
          <button
            type="button"
            className="border rounded px-3 py-1 text-xs"
            onClick={clearFilters}
          >
            Limpiar
          </button>

          <button
            type="button"
            className="border rounded px-3 py-1 text-xs"
            onClick={reload}
          >
            Recargar
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {filters.map((filter) => (
          <CorporateFilterSelect
            key={filter.key}
            filterKey={filter.key}
            label={filter.label}
            placeholder={filter.placeholder || "Todos"}
            disabled={filter.disabled}
            hideIfSingle={filter.hideIfSingle}
            lockIfSingle={filter.lockIfSingle !== false}
          />
        ))}
      </div>

      <div className="mt-3 text-xs text-gray-500">
        {loading && <span>Cargando filtros...</span>}

        {!loading && (
          <span>
            Estado: {status?.status || "OK"}
            {status?.remote_connections_required === false ? " | Fuente: EDARSAHUB SQL" : ""}
            {transport?.used_base_url ? ` | URL: ${transport.used_base_url}` : ""}
          </span>
        )}

        {error && (
          <span className="ml-2 text-red-600">
            {error}
          </span>
        )}
      </div>
    </div>
  );
}
