/**
 * EDARSA HUB - RH Componentes Compartidos
 * =======================================
 * Componentes reutilizables para el módulo de Recursos Humanos.
 * 
 * FASE 4E: Extraído de RecursosHumanos.js
 */

import React from 'react';
import { RefreshCw, Inbox, Search, Filter } from 'lucide-react';
import { Input } from '@/components/ui/input';

/**
 * Estado de carga
 */
export const RhLoadingState = () => (
  <div className="flex justify-center py-8" data-testid="rh-loading">
    <RefreshCw className="h-6 w-6 animate-spin text-zinc-400" />
  </div>
);

/**
 * Estado vacío genérico
 */
export const RhEmptyState = ({ icon: Icon = Inbox, message = 'Sin datos disponibles' }) => (
  <div className="text-center py-12 text-zinc-500" data-testid="rh-empty-state">
    <Icon className="h-12 w-12 mx-auto mb-3 opacity-50" />
    <p>{message}</p>
  </div>
);

/**
 * Badge de estatus laboral
 */
export const EstatusLaboralBadge = ({ estatus }) => {
  const config = {
    Activo: { bg: 'bg-green-100', text: 'text-green-800', label: 'Activo' },
    ACTIVO: { bg: 'bg-green-100', text: 'text-green-800', label: 'Activo' },
    Inactivo: { bg: 'bg-red-100', text: 'text-red-800', label: 'Inactivo' },
    INACTIVO: { bg: 'bg-red-100', text: 'text-red-800', label: 'Inactivo' },
    Vacaciones: { bg: 'bg-amber-100', text: 'text-amber-800', label: 'Vacaciones' },
    Incapacidad: { bg: 'bg-purple-100', text: 'text-purple-800', label: 'Incapacidad' },
    Baja: { bg: 'bg-zinc-200', text: 'text-zinc-700', label: 'Baja' },
  };

  const { bg, text, label } = config[estatus] || { bg: 'bg-zinc-100', text: 'text-zinc-600', label: estatus };

  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${bg} ${text}`}>
      {label}
    </span>
  );
};

/**
 * Badge de etapa de nómina
 */
export const EtapaNominaBadge = ({ etapa, etapasConfig }) => {
  const config = etapasConfig?.find(e => e.id === etapa);
  if (!config) return <span className="text-xs text-zinc-500">{etapa}</span>;
  
  return (
    <span className={`px-2 py-1 rounded text-xs font-medium text-white ${config.color}`}>
      {config.nombre}
    </span>
  );
};

/**
 * Filtros de RH (sucursal + búsqueda)
 */
export const RhFilters = ({
  sucursales = [],
  filtroSucursal,
  setFiltroSucursal,
  filtroBuscar,
  setFiltroBuscar,
  onRefresh,
  loading,
  showSearch = true,
  placeholder = 'Buscar...'
}) => (
  <div className="flex flex-wrap items-center gap-3 mb-4" data-testid="rh-filters">
    <div className="flex items-center gap-2">
      <Filter className="h-4 w-4 text-zinc-400" />
      <select
        value={filtroSucursal}
        onChange={(e) => setFiltroSucursal(e.target.value)}
        className="border border-zinc-300 rounded-lg px-3 py-2 text-sm bg-white text-zinc-900"
      >
        <option value="">Todas las sucursales</option>
        {sucursales.map(s => (
          <option key={s.SucursalID} value={s.SucursalID}>
            {s.Nombre_Sucursal}
          </option>
        ))}
      </select>
    </div>
    
    {showSearch && (
      <div className="relative flex-1 min-w-[200px]">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
        <Input
          value={filtroBuscar}
          onChange={(e) => setFiltroBuscar(e.target.value)}
          placeholder={placeholder}
          className="pl-9"
        />
      </div>
    )}
    
    {onRefresh && (
      <button
        onClick={onRefresh}
        disabled={loading}
        className="p-2 rounded-lg border border-zinc-300 hover:bg-zinc-100 transition-colors disabled:opacity-50"
      >
        <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
      </button>
    )}
  </div>
);

/**
 * Paginación simple
 */
export const RhPagination = ({ page, totalPages, setPage }) => {
  if (totalPages <= 1) return null;
  
  return (
    <div className="flex items-center justify-center gap-2 mt-4" data-testid="rh-pagination">
      <button
        onClick={() => setPage(Math.max(1, page - 1))}
        disabled={page === 1}
        className="px-3 py-1 border rounded text-sm disabled:opacity-50 hover:bg-zinc-100"
      >
        Anterior
      </button>
      <span className="text-sm text-zinc-500">
        Página {page} de {totalPages}
      </span>
      <button
        onClick={() => setPage(Math.min(totalPages, page + 1))}
        disabled={page === totalPages}
        className="px-3 py-1 border rounded text-sm disabled:opacity-50 hover:bg-zinc-100"
      >
        Siguiente
      </button>
    </div>
  );
};

// Export default con todos los componentes
export default {
  RhLoadingState,
  RhEmptyState,
  EstatusLaboralBadge,
  EtapaNominaBadge,
  RhFilters,
  RhPagination,
};
