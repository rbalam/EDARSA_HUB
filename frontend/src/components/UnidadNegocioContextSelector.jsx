import React from "react";
import { useAccessContext } from "../hooks/useAccessContext";

export default function UnidadNegocioContextSelector() {
  const { context, loading, changeUnit } = useAccessContext();

  if (loading) {
    return <div className="text-sm text-gray-500">Cargando unidades...</div>;
  }

  const unidades = context?.unidades_permitidas || [];
  const unidadActiva = context?.unidad_activa || "";

  if (unidades.length <= 1) {
    return null;
  }

  return (
    <div className="flex items-center gap-2" data-testid="unidad-context-selector">
      <label htmlFor="unidad_contexto" className="text-sm font-medium text-gray-700">
        Unidad:
      </label>
      <select
        id="unidad_contexto"
        value={unidadActiva}
        onChange={(e) => changeUnit(e.target.value)}
        className="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        data-testid="unidad-context-select"
      >
        {unidades.map((u) => (
          <option 
            key={u.UnidadNegocioID || `${u.EmpresaID}-${u.SucursalID}`} 
            value={u.UnidadNegocioID || ""}
          >
            {u.UnidadNegocioNombre || u.NombreEmpresa || "Sin nombre"}
          </option>
        ))}
      </select>
    </div>
  );
}
