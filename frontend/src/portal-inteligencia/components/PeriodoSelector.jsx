/**
 * Selector de período CANÓNICO del Portal Inteligencia.
 * Día / Semana / Mes / Año — anclado en backend al último día con datos.
 */
import React from 'react';
import { CalendarDays } from 'lucide-react';

export const PERIODOS = [
  { value: 'dia', label: 'Día' },
  { value: 'semana', label: 'Semana' },
  { value: 'mes', label: 'Mes' },
  { value: 'anio', label: 'Año' },
];

export function PeriodoSelector({ periodo, onChange, periodoLabel }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex gap-2" data-testid="periodo-selector">
        {PERIODOS.map((p) => (
          <button
            key={p.value}
            data-testid={`periodo-btn-${p.value}`}
            onClick={() => onChange(p.value)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              periodo === p.value ? 'bg-emerald-500 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>
      {periodoLabel && (
        <div className="flex items-center gap-2 text-sm text-slate-300" data-testid="periodo-label">
          <CalendarDays className="h-4 w-4 text-emerald-400" />
          <span>Mostrando: <span className="font-semibold text-white">{periodoLabel}</span></span>
        </div>
      )}
    </div>
  );
}
