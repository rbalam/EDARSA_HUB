import React from "react";
import { useCorporateFilters } from "./CorporateFiltersProvider";

export function CorporateFilterSelect({ filterKey, label, placeholder = "Todos", disabled = false }) {
  const { filters, selected, setFilterValue, loading } = useCorporateFilters();

  const options = filters?.[filterKey] || [];
  const value = selected?.[filterKey] || "";

  return (
    <div className="space-y-1">
      {label && (
        <label className="text-sm font-medium text-gray-700">
          {label}
        </label>
      )}

      <select
        className="w-full border rounded px-3 py-2 text-sm"
        value={value}
        disabled={disabled || loading}
        onChange={(event) => setFilterValue(filterKey, event.target.value)}
      >
        <option value="">{placeholder}</option>
        {options.map((item) => (
          <option key={item.id} value={item.id}>
            {item.codigo ? `${item.codigo} - ${item.nombre}` : item.nombre}
          </option>
        ))}
      </select>
    </div>
  );
}
