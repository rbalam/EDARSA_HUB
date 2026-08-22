import React, { useState } from 'react';
import { AlertTriangle, CheckCircle2, RefreshCw, Wrench } from 'lucide-react';
import { apiPost, ESTADO } from '../api/client';

export function SyncControlPanel({ unidad, fechaInicio, fechaFin, onUpdated }) {
  const [loading, setLoading] = useState(false);
  const [repairing, setRepairing] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState('');

  const payload = {
    unidad: unidad || 'todas',
    fecha_inicio: fechaInicio,
    fecha_fin: fechaFin,
  };

  const verificar = async () => {
    if (!fechaInicio || !fechaFin) return;
    setLoading(true);
    setError('');
    const res = await apiPost('/inteligencia/sync/verificar', payload);
    if (res.estado !== ESTADO.OK || !res.data) {
      setError('No fue posible verificar la sincronización. Revisa permisos o conectividad del Preview.');
      setResultado(null);
    } else {
      setResultado(res.data);
    }
    setLoading(false);
  };

  const reparar = async () => {
    if (!fechaInicio || !fechaFin) return;
    setRepairing(true);
    setError('');
    const res = await apiPost(
      '/inteligencia/sync/sincronizar-pendientes',
      payload,
      { timeout: 300000 },
    );
    if (res.estado !== ESTADO.OK || !res.data) {
      setError('La sincronización no pudo completarse. Ninguna fecha que no concilie debe escribirse.');
    } else {
      setResultado(res.data.validacion_posterior || null);
      if (onUpdated) await onUpdated();
    }
    setRepairing(false);
  };

  const problemas = Number(resultado?.problemas || 0);
  const ok = resultado?.estado_global === 'SINCRONIZADO';
  const hayResultado = !!resultado;

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4" data-testid="sync-control-panel">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-white">Integridad de sincronización</h3>
          <p className="text-xs text-slate-400">
            Verifica KPI vs detalle por fecha · {fechaInicio || '—'} a {fechaFin || '—'}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={verificar}
            disabled={loading || repairing || !fechaInicio || !fechaFin}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-white"
            data-testid="sync-verificar-btn"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Verificando...' : 'Verificar sincronización'}
          </button>
          {hayResultado && problemas > 0 && (
            <button
              type="button"
              onClick={reparar}
              disabled={repairing || loading}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-950"
              data-testid="sync-reparar-btn"
            >
              <Wrench className={`h-3.5 w-3.5 ${repairing ? 'animate-pulse' : ''}`} />
              {repairing ? 'Sincronizando...' : 'Sincronizar pendientes'}
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="mt-3 flex items-start gap-2 text-xs text-red-300 bg-red-500/10 border border-red-500/30 rounded-lg p-3">
          <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {hayResultado && (
        <div className={`mt-3 rounded-lg border p-3 ${ok ? 'border-emerald-500/30 bg-emerald-500/10' : 'border-amber-500/30 bg-amber-500/10'}`}>
          <div className="flex items-center gap-2">
            {ok ? <CheckCircle2 className="h-4 w-4 text-emerald-400" /> : <AlertTriangle className="h-4 w-4 text-amber-400" />}
            <span className={`text-sm font-semibold ${ok ? 'text-emerald-300' : 'text-amber-300'}`}>
              {ok ? 'Todas las fechas están sincronizadas' : `${problemas} fecha(s) requieren atención`}
            </span>
          </div>
          {(resultado.resumen || []).length > 0 && (
            <div className="mt-3 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2">
              {resultado.resumen.map((r) => (
                <div key={r.sucursal} className="text-xs bg-slate-950/30 rounded-md p-2 border border-slate-700/60">
                  <p className="font-medium text-white">{r.sucursal}</p>
                  <p className="text-slate-400">
                    OK {r.sincronizados} · Pendientes {r.pendientes} · No cuadra {r.no_cuadra}
                  </p>
                </div>
              ))}
            </div>
          )}
          {(resultado.detalle || []).filter((d) => d.estado !== 'SINCRONIZADO').length > 0 && (
            <div className="mt-3 max-h-44 overflow-auto border-t border-slate-700/60 pt-2 space-y-1">
              {resultado.detalle.filter((d) => d.estado !== 'SINCRONIZADO').map((d) => (
                <div key={`${d.unidad_codigo}-${d.fecha}`} className="flex flex-wrap justify-between gap-2 text-xs text-slate-300">
                  <span>{d.sucursal} · {d.fecha}</span>
                  <span>{d.estado} · Δ venta ${Number(d.delta_venta || 0).toLocaleString('es-MX', { minimumFractionDigits: 2 })} · Δ tickets {d.delta_tickets}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
