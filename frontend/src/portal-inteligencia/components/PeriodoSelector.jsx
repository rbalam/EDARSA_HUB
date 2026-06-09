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

export function PeriodoSelector({ periodo, onChange, periodoLabel, rangoInicio = '', rangoFin = '', onRango }) {
  const esPersonalizado = periodo === 'personalizado';
  return (
    <div className="flex flex-col gap-2">
      <div className="flex gap-2 flex-wrap items-center" data-testid="periodo-selector">
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
        {onRango && (
          <button
            data-testid="periodo-btn-personalizado"
            onClick={() => onChange('personalizado')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              esPersonalizado ? 'bg-emerald-500 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            Personalizado
          </button>
        )}
        {onRango && esPersonalizado && (
          <div className="flex items-center gap-2" data-testid="periodo-rango-inputs">
            <input
              type="date"
              data-testid="periodo-fecha-inicio"
              value={rangoInicio}
              max={rangoFin || undefined}
              onChange={(e) => onRango(e.target.value, rangoFin)}
              className="bg-slate-800 text-white text-sm rounded-lg px-2 py-1.5 border border-slate-600 focus:border-emerald-400 focus:outline-none"
            />
            <span className="text-slate-400 text-sm">a</span>
            <input
              type="date"
              data-testid="periodo-fecha-fin"
              value={rangoFin}
              min={rangoInicio || undefined}
              onChange={(e) => onRango(rangoInicio, e.target.value)}
              className="bg-slate-800 text-white text-sm rounded-lg px-2 py-1.5 border border-slate-600 focus:border-emerald-400 focus:outline-none"
            />
          </div>
        )}
      </div>
      {onRango && esPersonalizado && (!rangoInicio || !rangoFin) && (
        <div className="text-xs text-amber-400" data-testid="periodo-rango-hint">
          Selecciona fecha de inicio y fin para aplicar el rango.
        </div>
      )}
      {periodoLabel && (
        <div className="flex items-center gap-2 text-sm text-slate-300" data-testid="periodo-label">
          <CalendarDays className="h-4 w-4 text-emerald-400" />
          <span>Mostrando: <span className="font-semibold text-white">{periodoLabel}</span></span>
        </div>
      )}
    </div>
  );
}
