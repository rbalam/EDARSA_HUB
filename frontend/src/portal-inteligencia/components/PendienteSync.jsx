/**
 * Estado "Pendiente de sincronización" para páginas del Reporteador BI cuya
 * fuente origen (Compras, Documentos, Capacidad/Mesas, Metas) aún NO está en
 * EDARSAHUB. Regla NO-LIVE: no se consulta POS en vivo ni se inventan datos.
 */
import React from 'react';
import { CloudOff } from 'lucide-react';

export function PendienteSync({ titulo, nota, fuente, medidas = [], proxy = null }) {
  return (
    <div className="bg-slate-800/50 border border-amber-500/30 rounded-xl p-8 text-center" data-testid="pendiente-sync">
      <div className="inline-flex p-4 rounded-full bg-amber-500/10 mb-4">
        <CloudOff className="h-8 w-8 text-amber-400" />
      </div>
      <h3 className="text-lg font-semibold text-white">{titulo || 'Pendiente de sincronización'}</h3>
      <p className="text-sm text-slate-400 max-w-2xl mx-auto mt-2">{nota}</p>
      {fuente && (
        <p className="text-xs text-amber-300/90 mt-3">Fuente requerida: <span className="font-mono">{fuente}</span></p>
      )}
      {medidas.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2 justify-center">
          {medidas.map((m) => (
            <span key={m} className="px-3 py-1 rounded-full bg-slate-700 text-slate-300 text-xs">{m}</span>
          ))}
        </div>
      )}
      {proxy && (proxy.pax != null) && (
        <div className="mt-6 inline-flex gap-6 bg-slate-900/40 rounded-lg px-6 py-3">
          <div><p className="text-2xl font-bold text-white">{Number(proxy.pax).toLocaleString()}</p><p className="text-xs text-slate-500">PAX ({proxy.periodo_label})</p></div>
          <div><p className="text-2xl font-bold text-white">{Number(proxy.cuentas).toLocaleString()}</p><p className="text-xs text-slate-500">Cuentas</p></div>
        </div>
      )}
    </div>
  );
}
