import React from 'react';
import { X } from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { iaChartColor } from './chartPalette';
import { IA_VIEW_TYPES, MAX_IA_CHART_SERIES } from './visualizationContract';

const numericValue = (value) => {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  const cleaned = String(value ?? '').replace(/[$,%\s,]/g, '');
  const parsed = Number(cleaned);
  return Number.isFinite(parsed) ? parsed : null;
};

const numberValue = (value) => numericValue(value) ?? 0;

const formatDisplayValue = (value) => (
  typeof value === 'number' && Number.isFinite(value)
    ? value.toLocaleString('es-MX', { maximumFractionDigits: 2 })
    : String(value ?? '—')
);

const normalizeSeries = (config, rows, keys, xKey) => {
  const allowed = new Set(keys);
  const requested = Array.isArray(config?.series) ? config.series : [];
  const safeRequested = requested
    .filter((item) => item && allowed.has(String(item.key || '')))
    .map((item) => ({
      key: String(item.key),
      label: String(item.label || item.key),
    }))
    .slice(0, MAX_IA_CHART_SERIES);

  if (safeRequested.length) return safeRequested;

  if (allowed.has(config?.y_key)) {
    return [{ key: config.y_key, label: config.y_key }];
  }

  const fallback = keys.find((key) => (
    key !== xKey && rows.some((row) => numericValue(row?.[key]) !== null)
  ));
  return fallback ? [{ key: fallback, label: fallback }] : [];
};

export function IAVisualizationRenderer({ config, rows }) {
  if (!config || !IA_VIEW_TYPES.has(config.view_type)) return null;

  const safeRows = Array.isArray(rows) ? rows.slice(0, 100) : [];
  const keys = safeRows.length ? Object.keys(safeRows[0]).slice(0, 32) : [];
  const tableKeys = keys.slice(0, 8);
  const xKey = keys.includes(config.x_key) ? config.x_key : keys[0];
  const series = normalizeSeries(config, safeRows, keys, xKey);
  const primarySeries = series[0];
  const chartRows = safeRows.slice(0, 40).map((row) => {
    const normalized = { ...row };
    series.forEach((item) => {
      normalized[item.key] = numberValue(row?.[item.key]);
    });
    return normalized;
  });

  if (config.view_type === 'table') {
    return (
      <div className="max-w-full overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-400">
              {tableKeys.map((key) => <th key={key} className="px-3 py-2">{key}</th>)}
            </tr>
          </thead>
          <tbody>
            {safeRows.map((row, index) => (
              <tr key={index} className="border-t border-slate-800 text-slate-200">
                {tableKeys.map((key) => (
                  <td key={key} className="px-3 py-2">{formatDisplayValue(row?.[key])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (config.view_type === 'kpi_cards') {
    const yKey = primarySeries?.key;
    return (
      <div className="grid gap-3 md:grid-cols-3">
        <div className="rounded-xl border border-slate-700 p-4">
          <p className="text-xs text-slate-400">Registros visibles</p>
          <p className="mt-1 text-2xl font-bold text-white">{safeRows.length}</p>
        </div>
        {yKey && (
          <>
            <div className="rounded-xl border border-slate-700 p-4">
              <p className="text-xs text-slate-400">Suma {yKey}</p>
              <p className="mt-1 text-2xl font-bold text-white">
                {safeRows.reduce((sum, row) => sum + numberValue(row?.[yKey]), 0).toLocaleString('es-MX')}
              </p>
            </div>
            <div className="rounded-xl border border-slate-700 p-4">
              <p className="text-xs text-slate-400">Promedio {yKey}</p>
              <p className="mt-1 text-2xl font-bold text-white">
                {(safeRows.length
                  ? safeRows.reduce((sum, row) => sum + numberValue(row?.[yKey]), 0) / safeRows.length
                  : 0).toLocaleString('es-MX', { maximumFractionDigits: 2 })}
              </p>
            </div>
          </>
        )}
      </div>
    );
  }

  if (config.view_type === 'bar_chart') {
    return (
      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartRows} margin={{ top: 12, right: 18, left: 12, bottom: 12 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.16} />
            <XAxis dataKey={xKey} tick={{ fill: '#cbd5e1', fontSize: 12 }} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} tickFormatter={(value) => Number(value).toLocaleString('es-MX', { notation: 'compact' })} />
            <Tooltip formatter={(value) => Number(value).toLocaleString('es-MX', { maximumFractionDigits: 2 })} labelStyle={{ color: '#0f172a' }} />
            <Legend />
            {series.length <= 1 && primarySeries && (
              <Bar dataKey={primarySeries.key} name={primarySeries.label} fill={iaChartColor(0)} radius={[6, 6, 0, 0]}>
                {chartRows.map((_row, index) => (
                  <Cell key={`ia-bar-cell-${index}`} fill={iaChartColor(index)} />
                ))}
              </Bar>
            )}
            {series.length > 1 && series.map((item, index) => (
              <Bar key={item.key} dataKey={item.key} name={item.label} fill={iaChartColor(index)} radius={[6, 6, 0, 0]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (config.view_type === 'line_chart') {
    return (
      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartRows} margin={{ top: 12, right: 18, left: 12, bottom: 12 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.16} />
            <XAxis dataKey={xKey} tick={{ fill: '#cbd5e1', fontSize: 12 }} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} tickFormatter={(value) => Number(value).toLocaleString('es-MX', { notation: 'compact' })} />
            <Tooltip formatter={(value) => Number(value).toLocaleString('es-MX', { maximumFractionDigits: 2 })} labelStyle={{ color: '#0f172a' }} />
            <Legend />
            {series.map((item, index) => (
              <Line
                key={item.key}
                type="monotone"
                dataKey={item.key}
                name={item.label}
                stroke={iaChartColor(index)}
                strokeWidth={3}
                dot={{ r: 4, fill: iaChartColor(index) }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return null;
}

export function IAAnalysisModal({ config, rows, onClose }) {
  if (!config || !IA_VIEW_TYPES.has(config.view_type)) return null;

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/70 p-6">
      <div className="max-h-[82vh] w-full max-w-4xl overflow-hidden rounded-2xl border border-slate-600 bg-slate-900 shadow-2xl">
        <header className="flex items-center justify-between border-b border-slate-700 px-5 py-3">
          <div>
            <h3 className="font-semibold text-white">{config.title || 'Análisis IA'}</h3>
            <p className="text-xs text-slate-400">Vista temporal · no modifica datos</p>
          </div>
          <button type="button" onClick={onClose} className="rounded-lg p-2 text-slate-300 hover:bg-slate-800">
            <X className="h-4 w-4" />
          </button>
        </header>
        <div className="max-h-[70vh] overflow-auto p-5">
          <IAVisualizationRenderer config={config} rows={rows} />
        </div>
      </div>
    </div>
  );
}
