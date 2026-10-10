import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Bot, Loader2, Send, Sparkles, X } from 'lucide-react';
import {
  crearSesion,
  enviarMensaje,
  iaHealth,
} from '../../services/iaAssistantApi';
import {
  exportActionDataset,
  resolveActionDataset,
} from './iaContextualData';
import { IAAnalysisModal } from './visualization/IAVisualizationRenderer';
import { IA_VIEW_TYPES } from './visualization/visualizationContract';

/**
 * IAContextual conserva exclusivamente la orquestacion conversacional.
 * La presentacion visual es canonica y transversal: tabla, KPI y graficos
 * se delegan al renderer compartido, sin logica especifica por modulo.
 */

const stripVisualCodeBlocks = (text) => String(text || '')
  .replace(/```(?:mermaid|xychart-beta)\s*[\s\S]*?```/gi, '')
  .replace(/```[\s\S]*?xychart-beta[\s\S]*?```/gi, '')
  .replace(/\|\s*\|/g, '|\n|')
  .replace(/\n{3,}/g, '\n\n')
  .trim();

const parseTableRow = (line) => String(line || '')
  .trim()
  .replace(/^\|/, '')
  .replace(/\|$/, '')
  .split('|')
  .map((cell) => cell.trim());

const isTableLine = (line) => (
  String(line || '').includes('|') && parseTableRow(line).length > 1
);

const isTableSeparator = (line) => {
  const cells = parseTableRow(line);
  return cells.length > 1 && cells.every((cell) => (
    /^:?-{3,}:?$/.test(cell.replace(/\s/g, ''))
  ));
};

function IAInlineMarkdown({ text }) {
  const parts = String(text ?? '').split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, index) => (
    part.startsWith('**') && part.endsWith('**')
      ? <strong key={index} className="font-semibold text-white">{part.slice(2, -2)}</strong>
      : <React.Fragment key={index}>{part}</React.Fragment>
  ));
}

export function IAMessageContent({ text }) {
  const lines = stripVisualCodeBlocks(text).split('\n');
  const blocks = [];

  for (let index = 0; index < lines.length;) {
    if (
      isTableLine(lines[index])
      && index + 1 < lines.length
      && isTableSeparator(lines[index + 1])
    ) {
      const headers = parseTableRow(lines[index]);
      const rows = [];
      index += 2;

      while (index < lines.length && isTableLine(lines[index])) {
        const cells = parseTableRow(lines[index]);
        if (cells.length !== headers.length) break;
        rows.push(cells);
        index += 1;
      }

      blocks.push(
        <div key={`table-${index}`} className="my-3 max-w-full overflow-x-auto rounded-lg border border-slate-700">
          <table className="min-w-full text-left text-xs">
            <thead className="bg-slate-800/80 text-slate-300">
              <tr>
                {headers.map((header, headerIndex) => (
                  <th key={headerIndex} className="whitespace-nowrap px-3 py-2 font-semibold">
                    <IAInlineMarkdown text={header} />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, rowIndex) => (
                <tr key={rowIndex} className="border-t border-slate-800 text-slate-200">
                  {row.map((cell, cellIndex) => (
                    <td key={cellIndex} className="whitespace-nowrap px-3 py-2">
                      <IAInlineMarkdown text={cell} />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      continue;
    }

    const line = lines[index];
    blocks.push(
      line.trim()
        ? (
          <div key={`line-${index}`} className="leading-6">
            <IAInlineMarkdown text={line} />
          </div>
        )
        : <div key={`space-${index}`} className="h-2" />
    );
    index += 1;
  }

  return <div className="min-w-0">{blocks}</div>;
}

const datasetNumericValue = (value) => {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  const cleaned = String(value ?? '').replace(/[$,%\s,]/g, '');
  const numeric = Number(cleaned);
  return Number.isFinite(numeric) ? numeric : null;
};

const metricKey = (value) => String(value || '')
  .normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '')
  .toLowerCase()
  .replace(/[^a-z0-9]+/g, '_')
  .replace(/^_+|_+$/g, '');

const extractMarkdownTables = (text) => {
  const lines = stripVisualCodeBlocks(text).split('\n');
  const tables = [];

  for (let index = 0; index < lines.length - 1;) {
    if (!isTableLine(lines[index]) || !isTableSeparator(lines[index + 1])) {
      index += 1;
      continue;
    }

    const headers = parseTableRow(lines[index]);
    const rows = [];
    index += 2;

    while (index < lines.length && isTableLine(lines[index])) {
      const cells = parseTableRow(lines[index]);
      if (cells.length !== headers.length) break;
      rows.push(cells);
      index += 1;
    }

    if (headers.length > 1 && rows.length) {
      tables.push({ headers, rows });
    }
  }

  return tables;
};

const buildPresentationDatasets = (text) => {
  const datasets = [];

  extractMarkdownTables(text).forEach((table, tableIndex) => {
    const tableRows = table.rows.map((cells) => (
      table.headers.reduce((row, header, headerIndex) => {
        row[header] = cells[headerIndex] ?? '';
        return row;
      }, {})
    ));

    datasets.push({
      dataset_id: `answer_table_${tableIndex + 1}`,
      title: 'Tabla solicitada',
      columns: table.headers,
      rows: tableRows,
      row_count: tableRows.length,
      presentation_kind: 'answer_table',
      source_policy: 'EDARSAHUB_ONLY',
    });

    const firstHeader = String(table.headers[0] || '').toLowerCase();
    if (!/(indicador|m[eé]trica|concepto)/i.test(firstHeader)) return;

    const periodColumns = table.headers.slice(1).filter((header) => (
      !/(variaci[oó]n|cambio|delta|diferencia|%)/i.test(String(header || ''))
    ));

    if (periodColumns.length < 2) return;

    const metricRows = table.rows
      .map((cells) => ({
        key: metricKey(cells[0]),
        label: cells[0],
        cells,
      }))
      .filter((row) => row.key);

    const comparisonRows = periodColumns.map((period) => {
      const periodIndex = table.headers.indexOf(period);
      const row = { periodo: period };

      metricRows.forEach((metric) => {
        const numeric = datasetNumericValue(metric.cells[periodIndex]);
        if (numeric !== null) row[metric.key] = numeric;
      });

      return row;
    });

    const comparisonColumns = [
      'periodo',
      ...metricRows
        .map((row) => row.key)
        .filter((key, index, all) => all.indexOf(key) === index),
    ];

    datasets.push({
      dataset_id: `answer_comparison_${tableIndex + 1}`,
      title: 'Comparativo solicitado',
      columns: comparisonColumns,
      rows: comparisonRows,
      row_count: comparisonRows.length,
      presentation_kind: 'comparison',
      source_policy: 'EDARSAHUB_ONLY',
    });
  });

  return datasets;
};

const formatDisplayValue = (value) => {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value.toLocaleString('es-MX', { maximumFractionDigits: 2 });
  }
  return String(value ?? '—');
};

const inferVisualAction = (userText, datasets = []) => {
  const normalized = String(userText || '').toLowerCase();
  const wantsChart = /gr[aá]fic|chart|barras?|l[ií]nea/.test(normalized);
  const wantsTable = /tabla|tabular|cuadro/.test(normalized);
  if (!wantsChart && !wantsTable) return null;

  const all = (datasets || []).filter(
    (item) => item?.dataset_id && Array.isArray(item?.rows) && item.rows.length
  );

  let dataset;
  if (wantsChart) {
    dataset = all.find((item) => item?.presentation_kind === 'comparison');
  } else {
    dataset = all.find((item) => item?.presentation_kind === 'answer_table');
  }

  if (!dataset) {
    dataset = [...all].sort(
      (a, b) => (b?.row_count || b?.rows?.length || 0) - (a?.row_count || a?.rows?.length || 0)
    )[0];
  }

  if (!dataset) return null;

  const rows = dataset.rows || [];
  const columns = Array.isArray(dataset.columns) && dataset.columns.length
    ? dataset.columns
    : Object.keys(rows[0] || {});

  const numericColumns = columns.filter((key) => (
    rows.some((row) => datasetNumericValue(row?.[key]) !== null)
  ));
  const yKey = numericColumns.find((key) => /^ventas?$|ventas_total|total_venta/i.test(key))
    || numericColumns.find((key) => /venta|total|importe|monto|valor|ingreso/i.test(key))
    || numericColumns[0];
  const xKey = columns.find((key) => (
    key !== yKey && /periodo|fecha|mes|a[nñ]o|sucursal|nombre|unidad/i.test(key)
  )) || columns.find((key) => key !== yKey);

  const requestedSeries = numericColumns.filter((key) => {
    const tokens = metricKey(key).split('_').filter((token) => token.length >= 3);
    return tokens.some((token) => normalized.includes(token));
  });
  const seriesKeys = (requestedSeries.length > 1 ? requestedSeries : (yKey ? [yKey] : []))
    .slice(0, 10);

  const viewType = wantsChart
    ? (/l[ií]nea/.test(normalized) ? 'line_chart' : 'bar_chart')
    : 'table';

  return {
    type: 'OPEN_VIEW',
    label: wantsChart ? 'Ver gráfica' : 'Ver tabla',
    payload: {
      dataset_id: dataset.dataset_id,
      view_type: viewType,
      title: wantsChart ? 'Comparativo solicitado' : 'Tabla solicitada',
      ...(xKey ? { x_key: xKey } : {}),
      ...(yKey ? { y_key: yKey } : {}),
      ...(seriesKeys.length ? {
        series: seriesKeys.map((key) => ({ key, label: key })),
      } : {}),
    },
  };
};

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
      && IA_VIEW_TYPES.has(action.payload?.view_type)
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
      const previousDatasets = [...messages]
        .reverse()
        .find((message) => message?.role === 'assistant' && (message?.datasets || []).length)
        ?.datasets || [];

      const response = await enviarMensaje(sid, text, contextoVista);
      const responseDatasets = Array.isArray(response?.datasets) ? response.datasets : [];
      const presentationDatasets = buildPresentationDatasets(response?.respuesta || '');
      const currentDatasets = [
        ...presentationDatasets,
        ...responseDatasets,
      ];
      const datasets = currentDatasets.length ? currentDatasets : previousDatasets;
      let actions = Array.isArray(response?.acciones_ui) ? [...response.acciones_ui] : [];

      const localVisualAction = inferVisualAction(text, datasets);
      if (localVisualAction) {
        actions = actions.filter((action) => action?.type !== 'OPEN_VIEW');
        actions.unshift(localVisualAction);
      }

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: response?.respuesta || '',
          actions,
          datasets,
        },
      ]);

      const autoVisual = actions.find((action) => (
        action?.type === 'OPEN_VIEW'
        && ['bar_chart', 'line_chart', 'kpi_cards'].includes(action?.payload?.view_type)
      ));
      if (autoVisual) {
        executeAction(autoVisual, datasets);
      }
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
              <div className={`rounded-2xl px-4 py-3 text-sm ${
                message.role === 'user'
                  ? 'inline-block max-w-[90%] whitespace-pre-wrap bg-indigo-600 text-white'
                  : 'block w-full max-w-full border border-slate-800 bg-slate-900 text-slate-200'
              }`}>
                {message.role === 'assistant'
                  ? <IAMessageContent text={message.text} />
                  : message.text}
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
