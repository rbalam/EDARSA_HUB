import React, { useEffect, useMemo, useRef, useState } from 'react';
import { BarChart3, Bot, Loader2, Send, Sparkles, X } from 'lucide-react';
import {
  crearSesion,
  enviarMensaje,
  iaHealth,
} from '../../services/iaAssistantApi';
import {
  exportActionDataset,
  resolveActionDataset,
} from './iaContextualData';

const VIEW_TYPES = new Set(['table', 'bar_chart', 'line_chart', 'kpi_cards']);

const numberValue = (value) => {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
};

export function IAAnalysisModal({ config, rows, onClose }) {
  if (!config || !VIEW_TYPES.has(config.view_type)) return null;
  const safeRows = Array.isArray(rows) ? rows.slice(0, 100) : [];
  const keys = safeRows.length ? Object.keys(safeRows[0]).slice(0, 8) : [];
  const xKey = keys.includes(config.x_key) ? config.x_key : keys[0];
  const yKey = keys.includes(config.y_key) ? config.y_key : keys.find(
    (key) => safeRows.some((row) => Number.isFinite(Number(row?.[key])))
  );
  const maxValue = Math.max(1, ...safeRows.map((row) => numberValue(row?.[yKey])));

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
          {config.view_type === 'table' && (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-slate-400">
                  {keys.map((key) => <th key={key} className="px-3 py-2">{key}</th>)}
                </tr>
              </thead>
              <tbody>
                {safeRows.map((row, index) => (
                  <tr key={index} className="border-t border-slate-800 text-slate-200">
                    {keys.map((key) => <td key={key} className="px-3 py-2">{String(row?.[key] ?? '—')}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {config.view_type === 'kpi_cards' && (
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
          )}

          {config.view_type === 'bar_chart' && (
            <div className="space-y-2">
              {safeRows.slice(0, 25).map((row, index) => {
                const value = numberValue(row?.[yKey]);
                return (
                  <div key={index} className="grid grid-cols-[180px_1fr_100px] items-center gap-3 text-sm">
                    <span className="truncate text-slate-300">{String(row?.[xKey] ?? index + 1)}</span>
                    <div className="h-3 rounded-full bg-slate-800">
                      <div className="h-3 rounded-full bg-indigo-500" style={{ width: `${Math.max(1, (value / maxValue) * 100)}%` }} />
                    </div>
                    <span className="text-right text-slate-300">{value.toLocaleString('es-MX')}</span>
                  </div>
                );
              })}
            </div>
          )}

          {config.view_type === 'line_chart' && (
            <div>
              <svg viewBox="0 0 800 260" className="h-72 w-full rounded-xl bg-slate-950/40 p-4">
                <polyline
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="3"
                  className="text-indigo-400"
                  points={safeRows.slice(0, 40).map((row, index, arr) => {
                    const x = arr.length <= 1 ? 20 : 20 + (760 * index / (arr.length - 1));
                    const y = 235 - (210 * numberValue(row?.[yKey]) / maxValue);
                    return `${x},${y}`;
                  }).join(' ')}
                />
              </svg>
              <p className="mt-2 text-xs text-slate-500">
                {xKey || 'índice'} · {yKey || 'valor'}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function IAContextualPanel({
  open,
  onClose,
  contextoVista,
  viewData,
  onApplyFilters,
  onClearFilters,
}) {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, sending]);

  if (!open) return null;

  const executeAction = (action, systemDatasets = []) => {
    if (action?.type === 'APPLY_FILTERS') {
      onApplyFilters?.(action.payload?.filters || {});
      return;
    }
    if (action?.type === 'CLEAR_FILTERS') {
      onClearFilters?.();
      return;
    }

    const resolved = resolveActionDataset(action, viewData, systemDatasets);

    if (
      action?.type === 'OPEN_VIEW'
      && VIEW_TYPES.has(action.payload?.view_type)
      && resolved
    ) {
      setAnalysis({
        config: action.payload,
        rows: resolved.rows,
      });
      return;
    }

    if (action?.type === 'EXPORT_FILE' && resolved) {
      exportActionDataset(action, resolved);
    }
  };

  const send = async () => {
    const text = input.trim();
    if (!text || sending) return;
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', text }]);
    setSending(true);
    try {
      let sid = sessionId;
      if (!sid) {
        const created = await crearSesion('Asistente IA contextual EDARSAHUB');
        sid = created?.sesion?.sesion_id;
        setSessionId(sid);
      }
      const response = await enviarMensaje(sid, text, contextoVista);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: response?.respuesta || '',
          actions: Array.isArray(response?.acciones_ui) ? response.acciones_ui : [],
          datasets: Array.isArray(response?.datasets) ? response.datasets : [],
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: 'No fue posible obtener una respuesta del Asistente IA.' },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <>
      <div className="absolute inset-y-0 right-0 z-[70] flex w-full max-w-md flex-col border-l border-slate-700 bg-slate-950 shadow-2xl">
        <header className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-indigo-400" />
            <div>
              <p className="text-sm font-semibold text-white">Asistente IA</p>
              <p className="text-[11px] text-slate-500">
                Contexto: {contextoVista?.modulo || 'EDARSAHUB'} / {contextoVista?.view_id || 'vista'}
              </p>
            </div>
          </div>
          <button type="button" onClick={onClose} className="rounded-lg p-2 text-slate-400 hover:bg-slate-800">
            <X className="h-4 w-4" />
          </button>
        </header>

        <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-4">
          {messages.length === 0 && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-300">
              <Bot className="mb-2 h-5 w-5 text-indigo-400" />
              Pregunta sobre cualquier información autorizada de EDARSAHUB. La vista actual aporta contexto, pero no limita periodos ni módulos permitidos por tu RBAC.
            </div>
          )}
          {messages.map((message, index) => (
            <div key={index} className={message.role === 'user' ? 'text-right' : 'text-left'}>
              <div className={`inline-block max-w-[90%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm ${
                message.role === 'user'
                  ? 'bg-indigo-600 text-white'
                  : 'border border-slate-800 bg-slate-900 text-slate-200'
              }`}>
                {message.text}
              </div>
              {message.role === 'assistant' && (message.actions || []).length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {message.actions.map((action, actionIndex) => (
                    <button
                      key={`${action.type}:${actionIndex}`}
                      type="button"
                      onClick={() => executeAction(action, message.datasets || [])}
                      className="rounded-lg border border-indigo-500/50 bg-indigo-500/10 px-3 py-1.5 text-xs font-medium text-indigo-300 hover:bg-indigo-500/20"
                    >
                      {action.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
          {sending && (
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <Loader2 className="h-4 w-4 animate-spin" /> Analizando…
            </div>
          )}
        </div>

        <div className="border-t border-slate-800 p-4">
          <div className="flex items-end gap-2 rounded-xl border border-slate-700 bg-slate-900 p-2">
            <textarea
              rows={2}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  send();
                }
              }}
              placeholder="Pregunta sobre EDARSAHUB…"
              className="flex-1 resize-none bg-transparent px-2 py-1 text-sm text-white outline-none placeholder:text-slate-500"
            />
            <button
              type="button"
              disabled={!input.trim() || sending}
              onClick={send}
              className="rounded-lg bg-indigo-600 p-2 text-white disabled:opacity-40"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      <IAAnalysisModal
        config={analysis?.config}
        rows={analysis?.rows || []}
        onClose={() => setAnalysis(null)}
      />
    </>
  );
}

export function IAContextualLauncher(props) {
  const [allowed, setAllowed] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    let active = true;
    iaHealth()
      .then(() => {
        if (active) setAllowed(true);
      })
      .catch(() => {
        if (active) setAllowed(false);
      });
    return () => {
      active = false;
    };
  }, []);

  if (!allowed) return null;

  return (
    <>
      <button
        type="button"
        data-testid="ia-contextual-launcher"
        onClick={() => setOpen(true)}
        className="flex items-center gap-1.5 rounded-lg border border-indigo-500/40 bg-indigo-500/10 px-3 py-1.5 text-sm font-medium text-indigo-300 hover:bg-indigo-500/20"
      >
        <Sparkles className="h-4 w-4" />
        Asistente IA
      </button>
      <IAContextualPanel {...props} open={open} onClose={() => setOpen(false)} />
    </>
  );
}

export default IAContextualLauncher;
