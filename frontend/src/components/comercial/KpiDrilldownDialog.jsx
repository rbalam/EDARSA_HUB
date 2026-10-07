import React, { useEffect, useMemo, useState } from 'react';
import api from '../../lib/api';
import TicketVentaModal from './TicketVentaModal';
import IAContextualLauncher from '../ia/IAContextual';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import {
  AlertTriangle,
  ArrowUpDown,
  ChevronDown,
  ChevronRight,
  DollarSign,
  Loader2,
  Receipt,
  Users,
} from 'lucide-react';

const money = (value) => new Intl.NumberFormat('es-MX', {
  style: 'currency',
  currency: 'MXN',
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
}).format(Number(value || 0));

const number = (value) => new Intl.NumberFormat('es-MX', {
  maximumFractionDigits: 0,
}).format(Number(value || 0));

const toNumber = (value) => Number(value || 0);

const MONTHS = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
];

const isoDate = (value) => String(value || '').slice(0, 10);

const monthRange = (yearValue, monthValue) => {
  const year = Number(yearValue);
  const month = Number(monthValue);

  if (!year || !month) return null;

  const start = `${year}-${String(month).padStart(2, '0')}-01`;
  const lastDay = new Date(year, month, 0).getDate();
  const end = `${year}-${String(month).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`;

  return { start, end };
};

const rowDate = (row) => (
  isoDate(row?.fecha_operacion)
  || isoDate(row?.fecha)
  || isoDate(row?.fecha_hora)
);

const compareFolio = (a, b) => {
  const av = String(a?.numero_ticket || '');
  const bv = String(b?.numero_ticket || '');
  const an = Number(av);
  const bn = Number(bv);

  if (Number.isFinite(an) && Number.isFinite(bn)) {
    return an - bn;
  }

  return av.localeCompare(bv, 'es', { numeric: true });
};

const sortDetailRows = (rows, sort) => rows.slice().sort((a, b) => {
  let result = 0;

  if (sort.key === 'folio') {
    result = compareFolio(a, b);
  } else if (sort.key === 'fecha') {
    result = rowDate(a).localeCompare(rowDate(b));
  } else if (sort.key === 'pax') {
    result = toNumber(a?.pax) - toNumber(b?.pax);
  } else if (sort.key === 'importe') {
    result = toNumber(a?.ventas) - toNumber(b?.ventas);
  }

  return sort.direction === 'asc' ? result : -result;
});

const totalsFor = (rows) => rows.reduce(
  (acc, row) => ({
    cheques: acc.cheques + 1,
    pax: acc.pax + toNumber(row?.pax),
    ventas: acc.ventas + toNumber(row?.ventas),
  }),
  { cheques: 0, pax: 0, ventas: 0 }
);

const makeGroup = (nivel, key, label, rows, children, fecha = null) => {
  const totals = totalsFor(rows);
  return {
    nivel,
    key,
    label,
    fecha,
    rows,
    children,
    folios: totals.cheques,
    pax: totals.pax,
    ventas: totals.ventas,
  };
};

const groupByDay = (rows, sort) => {
  const buckets = new Map();

  rows.forEach((row) => {
    const date = rowDate(row);
    if (!date) return;
    if (!buckets.has(date)) buckets.set(date, []);
    buckets.get(date).push(row);
  });

  return [...buckets.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, dayRows]) => makeGroup(
      'dia',
      `day:${date}`,
      date,
      dayRows,
      sortDetailRows(dayRows, sort),
      date
    ));
};

const groupByMonth = (rows, sort, keyPrefix = '') => {
  const buckets = new Map();

  rows.forEach((row) => {
    const date = rowDate(row);
    if (!date) return;
    const [year, month] = date.split('-');
    const key = `${year}-${month}`;
    if (!buckets.has(key)) buckets.set(key, []);
    buckets.get(key).push(row);
  });

  return [...buckets.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, monthRows]) => {
      const [year, month] = key.split('-');
      return makeGroup(
        'mes',
        `${keyPrefix}month:${key}`,
        `${MONTHS[Number(month) - 1]} ${year}`,
        monthRows,
        groupByDay(monthRows, sort)
      );
    });
};

const groupByYear = (rows, sort) => {
  const buckets = new Map();

  rows.forEach((row) => {
    const date = rowDate(row);
    if (!date) return;
    const year = date.slice(0, 4);
    if (!buckets.has(year)) buckets.set(year, []);
    buckets.get(year).push(row);
  });

  return [...buckets.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([year, yearRows]) => makeGroup(
      'anio',
      `year:${year}`,
      year,
      yearRows,
      groupByMonth(yearRows, sort, `year:${year}:`)
    ));
};

const selectedHistoricalMonths = (temporalSelection) => (
  Array.isArray(temporalSelection?.periods)
    ? temporalSelection.periods.reduce(
      (total, entry) => total + (Array.isArray(entry?.months) ? entry.months.length : 0),
      0
    )
    : 0
);

const deriveRanges = ({
  temporalSelection,
  modoVentasDia,
  unidad,
  anio,
  mes,
}) => {
  if (modoVentasDia) {
    const operationDate = isoDate(unidad?.fecha_operacion);
    return operationDate ? [{ start: operationDate, end: operationDate }] : [];
  }

  if (temporalSelection?.mode === 'date_range') {
    const start = isoDate(temporalSelection?.startDate);
    const end = isoDate(temporalSelection?.endDate || temporalSelection?.startDate);
    return start && end ? [{ start, end }] : [];
  }

  if (temporalSelection?.mode === 'historical_periods') {
    const ranges = [];

    (temporalSelection.periods || []).forEach((entry) => {
      const year = Number(entry?.year);
      (entry?.months || []).forEach((month) => {
        const range = monthRange(year, month);
        if (range) ranges.push(range);
      });
    });

    return ranges;
  }

  const fallback = monthRange(anio, mes);
  return fallback ? [fallback] : [];
};

const hierarchyMode = ({ rows, ranges, temporalSelection, modoVentasDia }) => {
  if (modoVentasDia) return 'detail';

  if (temporalSelection?.mode === 'historical_periods') {
    const years = new Set((temporalSelection.periods || []).map((entry) => Number(entry?.year)));
    const months = selectedHistoricalMonths(temporalSelection);

    if (years.size > 1) return 'year';
    if (months > 1) return 'month';
    return 'day';
  }

  if (temporalSelection?.mode === 'date_range') {
    const start = ranges[0]?.start;
    const end = ranges[0]?.end;
    if (!start || !end || start === end) return 'detail';
    if (start.slice(0, 7) === end.slice(0, 7)) return 'day';
    if (start.slice(0, 4) === end.slice(0, 4)) return 'month';
    return 'year';
  }

  const dates = rows.map(rowDate).filter(Boolean);
  if (dates.length === 0) return 'detail';
  const first = dates[0];
  const last = dates[dates.length - 1];
  if (first === last) return 'detail';
  if (first.slice(0, 7) === last.slice(0, 7)) return 'day';
  if (first.slice(0, 4) === last.slice(0, 4)) return 'month';
  return 'year';
};

const rangeLabel = (ranges, temporalSelection, modoVentasDia) => {
  if (ranges.length === 0) return '-';
  if (ranges.length === 1) {
    return ranges[0].start === ranges[0].end
      ? ranges[0].start
      : `${ranges[0].start} a ${ranges[0].end}`;
  }

  const starts = ranges.map((range) => range.start).sort();
  const ends = ranges.map((range) => range.end).sort();
  const suffix = temporalSelection?.mode === 'historical_periods'
    ? ` · ${ranges.length} mes(es) seleccionado(s)`
    : '';

  return `${starts[0]} a ${ends[ends.length - 1]}${suffix}`;
};

export default function KpiDrilldownDialog({
  open,
  onClose,
  tipo,
  unidad,
  modoVentasDia = false,
  mes = null,
  anio = null,
  temporalSelection = null,
}) {
  const initialSort = tipo === 'pax'
    ? { key: 'pax', direction: 'desc' }
    : tipo === 'cheques'
      ? { key: 'importe', direction: 'desc' }
      : { key: 'folio', direction: 'asc' };

  const [sort, setSort] = useState(initialSort);
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState(() => new Set());
  const [ticketSeleccionado, setTicketSeleccionado] = useState(null);

  const unidadCodigo = (
    unidad?.unidad_negocio_codigo
    || unidad?.unidad_negocio_id
    || unidad?.id
    || ''
  );

  const ranges = useMemo(() => deriveRanges({
    temporalSelection,
    modoVentasDia,
    unidad,
    anio,
    mes,
  }), [
    temporalSelection,
    modoVentasDia,
    unidad,
    anio,
    mes,
  ]);

  const expectedClosed = useMemo(() => ({
    cheques: modoVentasDia
      ? toNumber(unidad?.cheques_cerrados)
      : toNumber(unidad?.cheques),
    pax: modoVentasDia
      ? toNumber(unidad?.pax_cerrados)
      : toNumber(unidad?.pax),
    ventas: modoVentasDia
      ? toNumber(unidad?.ventas_cerradas)
      : toNumber(unidad?.ventas),
  }), [modoVentasDia, unidad]);

  const openTotals = useMemo(() => ({
    cheques: modoVentasDia ? toNumber(unidad?.cheques_abiertos) : 0,
    pax: modoVentasDia ? toNumber(unidad?.pax_abiertos) : 0,
    ventas: modoVentasDia ? toNumber(unidad?.ventas_abiertas) : 0,
  }), [modoVentasDia, unidad]);

  const kpiTotals = useMemo(() => ({
    cheques: toNumber(unidad?.cheques),
    pax: toNumber(unidad?.pax),
    ventas: toNumber(unidad?.ventas),
  }), [unidad]);

  useEffect(() => {
    setSort(
      tipo === 'pax'
        ? { key: 'pax', direction: 'desc' }
        : tipo === 'cheques'
          ? { key: 'importe', direction: 'desc' }
          : { key: 'folio', direction: 'asc' }
    );
  }, [tipo]);

  useEffect(() => {
    if (!open) return;

    let active = true;

    const load = async () => {
      setLoading(true);
      setError('');
      setRows([]);
      setExpanded(new Set());

      try {
        if (!unidadCodigo) {
          throw new Error('No se pudo identificar la unidad de negocio.');
        }

        if (ranges.length === 0) {
          throw new Error('No se pudo resolver el período del detalle.');
        }

        const allRows = [];
        const seen = new Set();

        for (const range of ranges) {
          let page = 1;
          let hasMore = true;

          while (hasMore) {
            const response = await api.get('/v2/comercial/analytics/tickets', {
              params: {
                fecha_inicio: range.start,
                fecha_fin: range.end,
                unidad_negocio_id: unidadCodigo,
                page,
                page_size: 200,
              },
              timeout: 30000,
            });

            const payload = response.data?.data || {};
            const pageRows = Array.isArray(payload.items) ? payload.items : [];

            pageRows.forEach((row) => {
              const key = row?.ticket_pk || `${rowDate(row)}:${row?.numero_ticket}`;
              if (!seen.has(key)) {
                seen.add(key);
                allRows.push(row);
              }
            });

            hasMore = Boolean(payload.has_more);
            page += 1;

            if (page > 100) {
              throw new Error('El detalle excede el límite seguro de paginación.');
            }
          }
        }

        if (active) {
          setRows(allRows);
        }
      } catch (err) {
        if (active) {
          setError(
            err?.response?.data?.detail
            || err?.message
            || 'No fue posible cargar el detalle.'
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    };

    load();

    return () => {
      active = false;
    };
  }, [
    open,
    unidadCodigo,
    modoVentasDia,
    expectedClosed.cheques,
    ranges,
  ]);

  const detailedClosedRows = useMemo(
    () => (
      modoVentasDia
        ? rows.filter((row) => row?.fuente_ticket !== 'ABIERTA')
        : rows
    ),
    [modoVentasDia, rows]
  );

  const detailedOpenRows = useMemo(
    () => (
      modoVentasDia
        ? rows.filter((row) => row?.fuente_ticket === 'ABIERTA')
        : []
    ),
    [modoVentasDia, rows]
  );

  const closedDetailTotals = useMemo(
    () => totalsFor(detailedClosedRows),
    [detailedClosedRows]
  );

  const openDetailTotals = useMemo(
    () => totalsFor(detailedOpenRows),
    [detailedOpenRows]
  );

  const missingClosed = useMemo(() => ({
    cheques: Math.max(0, expectedClosed.cheques - closedDetailTotals.cheques),
    pax: Math.max(0, expectedClosed.pax - closedDetailTotals.pax),
    ventas: Math.max(0, expectedClosed.ventas - closedDetailTotals.ventas),
  }), [expectedClosed, closedDetailTotals]);

  const hasMissingClosed = (
    missingClosed.cheques > 0
    || missingClosed.pax > 0
    || missingClosed.ventas > 0.01
  );

  const missingOpen = useMemo(() => ({
    cheques: Math.max(0, openTotals.cheques - openDetailTotals.cheques),
    pax: Math.max(0, openTotals.pax - openDetailTotals.pax),
    ventas: Math.max(0, openTotals.ventas - openDetailTotals.ventas),
  }), [openTotals, openDetailTotals]);

  const hasMissingOpen = (
    missingOpen.cheques > 0
    || missingOpen.pax > 0
    || missingOpen.ventas > 0.01
  );

  const mode = useMemo(
    () => hierarchyMode({ rows, ranges, temporalSelection, modoVentasDia }),
    [rows, ranges, temporalSelection, modoVentasDia]
  );

  const hierarchy = useMemo(() => {
    if (mode === 'year') return groupByYear(rows, sort);
    if (mode === 'month') return groupByMonth(rows, sort);
    if (mode === 'day') return groupByDay(rows, sort);
    return sortDetailRows(rows, sort);
  }, [mode, rows, sort]);

  useEffect(() => {
    if (hierarchy.length > 0 && mode !== 'detail') {
      setExpanded(new Set([hierarchy[0].key]));
    }
  }, [mode, rows.length]);

  const toggleExpanded = (key) => {
    setExpanded((current) => {
      const next = new Set(current);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const toggleSort = (key) => {
    setSort((current) => (
      current.key === key
        ? {
          key,
          direction: current.direction === 'asc' ? 'desc' : 'asc',
        }
        : { key, direction: key === 'folio' || key === 'fecha' ? 'asc' : 'desc' }
    ));
  };

  const renderRows = (items, depth = 0) => (items || []).map((item, idx) => {
    const isGroup = Boolean(item?.nivel);

    if (!isGroup) {
      const date = rowDate(item);
      return (
        <tr
          key={item.ticket_pk || `${date}-${item.numero_ticket}-${idx}`}
          className="border-b hover:bg-zinc-50 transition-colors"
        >
          <td className="py-2 px-3">
            <div
              className="flex items-center gap-1"
              style={{ paddingLeft: `${depth * 18}px` }}
            >
              <Receipt className="h-4 w-4 text-zinc-400 flex-shrink-0" />
              <span
                className="font-mono text-xs font-medium underline decoration-dotted underline-offset-2 cursor-pointer"
                onClick={() => {
                  if (modoVentasDia && item.ticket_pk) {
                    setTicketSeleccionado({
                      ticketPk: item.ticket_pk,
                    });
                  }
                }}
                onDoubleClick={() => {
                  if (!modoVentasDia && item.ticket_pk) {
                    setTicketSeleccionado({
                      ticketPk: item.ticket_pk,
                    });
                  }
                }}
                title="Doble clic para abrir el ticket de venta"
              >
                {item.numero_ticket}
              </span>
            </div>
          </td>
          <td className="py-2 px-3 text-zinc-600">{date}</td>
          <td className="py-2 px-3 text-right">-</td>
          <td className="py-2 px-3 text-center">
            {toNumber(item.pax) > 0 ? (
              <span className="inline-flex items-center gap-1">
                <Users className="h-3 w-3 text-purple-500" />
                {number(item.pax)}
              </span>
            ) : '-'}
          </td>
          <td className="py-2 px-3 text-right font-semibold text-green-600">
            {money(item.ventas)}
          </td>
        </tr>
      );
    }

    const isOpen = expanded.has(item.key);

    return (
      <React.Fragment key={item.key}>
        <tr
          className="border-b hover:bg-zinc-50 cursor-pointer transition-colors"
          onClick={() => toggleExpanded(item.key)}
        >
          <td className="py-2 px-3">
            <div
              className="flex items-center gap-1"
              style={{ paddingLeft: `${depth * 18}px` }}
            >
              {isOpen ? (
                <ChevronDown className="h-4 w-4 text-zinc-500 flex-shrink-0" />
              ) : (
                <ChevronRight className="h-4 w-4 text-zinc-500 flex-shrink-0" />
              )}
              <span className="font-semibold">{item.label}</span>
            </div>
          </td>
          <td className="py-2 px-3 text-zinc-600">
            {item.nivel === 'dia' ? item.fecha : '-'}
          </td>
          <td className="py-2 px-3 text-right">{number(item.folios)}</td>
          <td className="py-2 px-3 text-center">
            {item.pax > 0 ? (
              <span className="inline-flex items-center gap-1">
                <Users className="h-3 w-3 text-purple-500" />
                {number(item.pax)}
              </span>
            ) : '-'}
          </td>
          <td className="py-2 px-3 text-right font-semibold text-green-600">
            {money(item.ventas)}
          </td>
        </tr>
        {isOpen && renderRows(item.children, depth + 1)}
      </React.Fragment>
    );
  });

  const titleConfig = tipo === 'pax'
    ? {
      title: 'Detalle de PAX',
      Icon: Users,
      color: 'text-purple-600',
    }
    : tipo === 'cheques'
      ? {
        title: 'Detalle de Cheques',
        Icon: Receipt,
        color: 'text-blue-600',
      }
      : {
        title: 'Detalle de Ventas',
        Icon: DollarSign,
        color: 'text-green-600',
      };

  const { Icon } = titleConfig;

  const onlyOpen = (
    modoVentasDia
    && expectedClosed.cheques <= 0
    && openTotals.cheques > 0
    && detailedOpenRows.length === 0
  );

  const footerTotals = modoVentasDia
    ? totalsFor(rows)
    : expectedClosed;

  return (
    <>
      <Dialog open={open} onOpenChange={(nextOpen) => !nextOpen && onClose()}>
      <DialogContent className="max-w-5xl max-h-[88vh] overflow-hidden flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="flex items-center gap-2">
            <Icon className={`h-5 w-5 ${titleConfig.color}`} />
            {titleConfig.title}
            <span className="text-sm font-normal text-zinc-500">
              • {unidad?.unidad || unidad?.unidad_negocio_nombre || unidadCodigo}
            </span>
          </DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
          </div>
        ) : error ? (
          <div className="p-4 rounded border border-red-200 bg-red-50 text-red-700">
            {error}
          </div>
        ) : (
          <div className="flex-1 overflow-hidden flex flex-col">
            <div className="flex items-center justify-between mb-3 px-1">
              <span className="text-sm text-zinc-500">
                Período: {rangeLabel(ranges, temporalSelection, modoVentasDia)}
              </span>
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium">{number(footerTotals.cheques)} folio(s)</span>
                <IAContextualLauncher
                  contextoVista={{
                    modulo: 'comercial', view_id: 'comercial_detalle_ventas', titulo: titleConfig.title,
                    scope: { server_id: unidad?.server_id || null, unidad: unidadCodigo, metric: tipo },
                    filtros: { rangos: ranges },
                    periodo: { fecha_inicio: ranges[0]?.start, fecha_fin: ranges[ranges.length - 1]?.end },
                    unidad_negocio: unidadCodigo,
                    seleccion: ticketSeleccionado ? { ticket_pk: ticketSeleccionado.ticketPk } : null,
                    columnas_visibles: [{ key: 'numero_ticket', label: 'Folio' }, { key: 'fecha', label: 'Fecha' }, { key: 'pax', label: 'PAX' }, { key: 'ventas', label: 'Total Venta' }],
                    estado_vista: { total_folios: footerTotals.cheques, total_pax: footerTotals.pax, total_venta: footerTotals.ventas }
                  }}
                  viewData={{ tickets: rows, lines: [] }}
                />
              </div>
            </div>

            {onlyOpen && (
              <div className="mb-3 p-3 rounded border border-amber-200 bg-amber-50 text-amber-800 flex gap-2">
                <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5" />
                <p>
                  Las cuentas de la operación todavía no están cerradas. No existe
                  detalle por folio para mostrar; se conserva únicamente el agregado
                  de cuentas no cerradas para conciliar contra el KPI.
                </p>
              </div>
            )}

            {!onlyOpen
              && modoVentasDia
              && expectedClosed.cheques > 0
              && detailedClosedRows.length === 0
              && (
              <div className="mb-3 p-3 rounded border border-amber-200 bg-amber-50 text-amber-800 flex gap-2">
                <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5" />
                <p>
                  Existen cuentas cerradas en el KPI, pero su detalle por folio
                  todavía no está disponible. El faltante se muestra únicamente
                  como agregado de conciliación.
                </p>
              </div>
            )}

            <p className="text-xs text-zinc-500 mb-2 px-1">
              {modoVentasDia
                ? 'Selecciona un folio para abrir el ticket de venta.'
                : 'Doble clic en un folio para abrir el ticket de venta.'}
            </p>

            <div className="flex-1 overflow-auto border rounded-lg">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-zinc-800 text-white z-10">
                  <tr>
                    <th
                      className="py-2 px-3 text-left cursor-pointer select-none"
                      onClick={() => toggleSort('folio')}
                    >
                      <span className="inline-flex items-center gap-1">
                        Período / Folio {!modoVentasDia && <ArrowUpDown className="h-3 w-3" />}
                      </span>
                    </th>
                    <th
                      className="py-2 px-3 text-left cursor-pointer select-none"
                      onClick={() => toggleSort('fecha')}
                    >
                      <span className="inline-flex items-center gap-1">
                        Fecha {!modoVentasDia && <ArrowUpDown className="h-3 w-3" />}
                      </span>
                    </th>
                    <th className="py-2 px-3 text-right">Folios</th>
                    <th
                      className="py-2 px-3 text-center cursor-pointer select-none"
                      onClick={() => toggleSort('pax')}
                    >
                      <span className="inline-flex items-center gap-1">
                        PAX {!modoVentasDia && <ArrowUpDown className="h-3 w-3" />}
                      </span>
                    </th>
                    <th
                      className="py-2 px-3 text-right cursor-pointer select-none"
                      onClick={() => toggleSort('importe')}
                    >
                      <span className="inline-flex items-center gap-1 justify-end w-full">
                        Total Venta {!modoVentasDia && <ArrowUpDown className="h-3 w-3" />}
                      </span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {renderRows(hierarchy)}

                  {hasMissingClosed && (
                    <tr className="border-b bg-orange-50 font-semibold">
                      <td className="py-2 px-3 text-orange-800">
                        Cuentas cerradas pendientes de detalle
                      </td>
                      <td className="py-2 px-3 text-zinc-600">
                        Sin detalle disponible
                      </td>
                      <td className="py-2 px-3 text-right">
                        {number(missingClosed.cheques)}
                      </td>
                      <td className="py-2 px-3 text-center">
                        {number(missingClosed.pax)}
                      </td>
                      <td className="py-2 px-3 text-right font-semibold text-green-600">
                        {money(missingClosed.ventas)}
                      </td>
                    </tr>
                  )}

                  {modoVentasDia && hasMissingOpen && (
                    <tr className="border-b bg-amber-50 font-semibold">
                      <td className="py-2 px-3 text-amber-800">
                        Cuentas no cerradas
                      </td>
                      <td className="py-2 px-3 text-zinc-600">
                        Sin detalle por folio
                      </td>
                      <td className="py-2 px-3 text-right">
                        {number(missingOpen.cheques)}
                      </td>
                      <td className="py-2 px-3 text-center">
                        {number(missingOpen.pax)}
                      </td>
                      <td className="py-2 px-3 text-right font-semibold text-green-600">
                        {money(missingOpen.ventas)}
                      </td>
                    </tr>
                  )}

                  {rows.length === 0 && !hasMissingClosed && !(modoVentasDia && openTotals.cheques > 0) && (
                    <tr>
                      <td colSpan={5} className="py-10 text-center text-zinc-500">
                        No hay movimientos cerrados en este período.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="mt-3 rounded-lg border bg-zinc-50 px-4 py-3 flex items-center justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-wide text-zinc-500">
                  Total del período seleccionado
                </p>
                <p className="text-xs text-zinc-500">
                  {number(footerTotals.cheques)} folio(s) • {number(footerTotals.pax)} PAX
                </p>
              </div>
              <p className="text-xl font-bold text-green-600">
                {money(footerTotals.ventas)}
              </p>
            </div>

            {!modoVentasDia && (
              <p className="mt-2 text-xs text-zinc-500">
                El detalle utiliza la información sincronizada en EDARSAHUB. Los
                folios pendientes de detalle se identifican para su conciliación.
              </p>
            )}
          </div>
        )}
      </DialogContent>
      </Dialog>

      {ticketSeleccionado && (
        <TicketVentaModal
          open={true}
          onClose={() => setTicketSeleccionado(null)}
          ticketPk={ticketSeleccionado.ticketPk || null}
        />
      )}
    </>
  );
}
