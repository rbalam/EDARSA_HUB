import React, { useEffect, useMemo, useState } from 'react';
import api from '../../lib/api';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { Loader2, AlertTriangle, ArrowUpDown } from 'lucide-react';

const money = (value) => new Intl.NumberFormat('es-MX', {
  style: 'currency',
  currency: 'MXN',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
}).format(Number(value || 0));

const toNumber = (value) => Number(value || 0);

const monthRange = (yearValue, monthValue) => {
  const year = Number(yearValue);
  const month = Number(monthValue);

  if (!year || !month) return null;

  const start = `${year}-${String(month).padStart(2, '0')}-01`;
  const lastDay = new Date(year, month, 0).getDate();
  const end = `${year}-${String(month).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`;

  return { start, end };
};

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

export default function KpiDrilldownDialog({
  open,
  onClose,
  tipo,
  unidad,
  modoVentasDia = false,
  mes = null,
  anio = null,
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

  const unidadCodigo = (
    unidad?.unidad_negocio_codigo
    || unidad?.unidad_negocio_id
    || unidad?.id
    || ''
  );

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

      try {
        if (!unidadCodigo) {
          throw new Error('No se pudo identificar la unidad de negocio.');
        }

        if (modoVentasDia && expectedClosed.cheques <= 0) {
          if (active) setRows([]);
          return;
        }

        let range = null;

        if (modoVentasDia) {
          const operationDate = String(unidad?.fecha_operacion || '').slice(0, 10);
          if (!operationDate) {
            throw new Error('No se pudo resolver la fecha operativa de la unidad.');
          }
          range = { start: operationDate, end: operationDate };
        } else {
          range = monthRange(anio, mes);
          if (!range) {
            throw new Error('No se pudo resolver el periodo del detalle.');
          }
        }

        const allRows = [];
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
          allRows.push(...pageRows);
          hasMore = Boolean(payload.has_more);
          page += 1;

          if (page > 100) {
            throw new Error('El detalle excede el límite seguro de paginación.');
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
    unidad?.fecha_operacion,
    modoVentasDia,
    mes,
    anio,
    expectedClosed.cheques,
  ]);

  const closedDetailTotals = useMemo(() => rows.reduce(
    (acc, row) => ({
      cheques: acc.cheques + 1,
      pax: acc.pax + toNumber(row?.pax),
      ventas: acc.ventas + toNumber(row?.ventas),
    }),
    { cheques: 0, pax: 0, ventas: 0 }
  ), [rows]);

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

  const sortedRows = useMemo(() => {
    const next = rows.slice();

    next.sort((a, b) => {
      let result = 0;

      if (sort.key === 'folio') {
        result = compareFolio(a, b);
      } else if (sort.key === 'fecha') {
        const av = `${a?.fecha_operacion || a?.fecha || ''} ${a?.hora || ''}`;
        const bv = `${b?.fecha_operacion || b?.fecha || ''} ${b?.hora || ''}`;
        result = av.localeCompare(bv);
      } else if (sort.key === 'pax') {
        result = toNumber(a?.pax) - toNumber(b?.pax);
      } else if (sort.key === 'importe') {
        result = toNumber(a?.ventas) - toNumber(b?.ventas);
      }

      return sort.direction === 'asc' ? result : -result;
    });

    return next;
  }, [rows, sort]);

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

  const title = tipo === 'pax'
    ? 'Detalle de PAX - cuentas cerradas'
    : tipo === 'cheques'
      ? 'Detalle de Cheques - cuentas cerradas'
      : 'Detalle de Ventas - cuentas cerradas';

  const onlyOpen = (
    modoVentasDia
    && expectedClosed.cheques <= 0
    && openTotals.cheques > 0
  );

  return (
    <Dialog open={open} onOpenChange={(nextOpen) => !nextOpen && onClose()}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>

        <div className="text-sm text-zinc-600 mb-3">
          {unidad?.unidad || unidad?.unidad_negocio_nombre || unidadCodigo}
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
          </div>
        ) : error ? (
          <div className="p-4 rounded border border-red-200 bg-red-50 text-red-700">
            {error}
          </div>
        ) : onlyOpen ? (
          <div className="space-y-4">
            <div className="p-4 rounded border border-amber-200 bg-amber-50 text-amber-800 flex gap-2">
              <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5" />
              <p>
                Las cuentas de la operación todavía no están cerradas, por lo que
                no se puede mostrar el detalle por folio. Se presenta únicamente
                el total agregado de las cuentas no cerradas para cuadrar el KPI.
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="bg-zinc-100">
                    <th className="text-left p-2 border">Concepto</th>
                    <th className="text-right p-2 border">PAX</th>
                    <th className="text-right p-2 border">Importe total</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="bg-amber-50 font-semibold">
                    <td className="p-2 border">
                      Cuentas no cerradas ({openTotals.cheques})
                    </td>
                    <td className="p-2 border text-right">
                      {openTotals.pax.toLocaleString('es-MX')}
                    </td>
                    <td className="p-2 border text-right">
                      {money(openTotals.ventas)}
                    </td>
                  </tr>
                  <tr className="font-bold">
                    <td className="p-2 border">TOTAL KPI</td>
                    <td className="p-2 border text-right">
                      {kpiTotals.pax.toLocaleString('es-MX')}
                    </td>
                    <td className="p-2 border text-right">
                      {money(kpiTotals.ventas)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {modoVentasDia && expectedClosed.cheques > 0 && rows.length === 0 && (
              <div className="p-3 rounded border border-amber-200 bg-amber-50 text-amber-800 flex gap-2">
                <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5" />
                <p>
                  Existen cuentas cerradas en el KPI, pero su detalle por folio
                  todavía no está disponible en la vista de reportes. No se consulta
                  el POS ni se modifica la sincronización; el total cerrado se
                  presenta de forma agregada para mantener la conciliación.
                </p>
              </div>
            )}

            <div className="overflow-x-auto max-h-[55vh] overflow-y-auto border rounded">
              <table className="w-full text-sm border-collapse">
                <thead className="sticky top-0 bg-zinc-100 z-10">
                  <tr>
                    <th
                      className="text-left p-2 border cursor-pointer select-none"
                      onClick={() => toggleSort('folio')}
                    >
                      <span className="inline-flex items-center gap-1">
                        Folio <ArrowUpDown className="h-3 w-3" />
                      </span>
                    </th>
                    <th
                      className="text-left p-2 border cursor-pointer select-none"
                      onClick={() => toggleSort('fecha')}
                    >
                      <span className="inline-flex items-center gap-1">
                        Fecha <ArrowUpDown className="h-3 w-3" />
                      </span>
                    </th>
                    <th
                      className="text-right p-2 border cursor-pointer select-none"
                      onClick={() => toggleSort('pax')}
                    >
                      <span className="inline-flex items-center gap-1 justify-end w-full">
                        PAX <ArrowUpDown className="h-3 w-3" />
                      </span>
                    </th>
                    <th
                      className="text-right p-2 border cursor-pointer select-none"
                      onClick={() => toggleSort('importe')}
                    >
                      <span className="inline-flex items-center gap-1 justify-end w-full">
                        Importe total <ArrowUpDown className="h-3 w-3" />
                      </span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {sortedRows.map((row) => (
                    <tr key={row.ticket_pk || `${row.fecha_operacion}-${row.numero_ticket}`}>
                      <td className="p-2 border">{row.numero_ticket}</td>
                      <td className="p-2 border">
                        {row.fecha_operacion || row.fecha}
                        {row.hora ? ` ${row.hora}` : ''}
                      </td>
                      <td className="p-2 border text-right">
                        {toNumber(row.pax).toLocaleString('es-MX')}
                      </td>
                      <td className="p-2 border text-right">
                        {money(row.ventas)}
                      </td>
                    </tr>
                  ))}

                  <tr className="font-bold bg-zinc-50">
                    <td className="p-2 border">
                      Total detalle cuentas cerradas ({closedDetailTotals.cheques})
                    </td>
                    <td className="p-2 border" />
                    <td className="p-2 border text-right">
                      {closedDetailTotals.pax.toLocaleString('es-MX')}
                    </td>
                    <td className="p-2 border text-right">
                      {money(closedDetailTotals.ventas)}
                    </td>
                  </tr>

                  {hasMissingClosed && (
                    <tr className="font-semibold bg-orange-50">
                      <td className="p-2 border">
                        Cuentas cerradas pendientes de detalle ({missingClosed.cheques})
                      </td>
                      <td className="p-2 border">Sin detalle disponible</td>
                      <td className="p-2 border text-right">
                        {missingClosed.pax.toLocaleString('es-MX')}
                      </td>
                      <td className="p-2 border text-right">
                        {money(missingClosed.ventas)}
                      </td>
                    </tr>
                  )}

                  {modoVentasDia && openTotals.cheques > 0 && (
                    <tr className="font-semibold bg-amber-50">
                      <td className="p-2 border">
                        Cuentas no cerradas ({openTotals.cheques})
                      </td>
                      <td className="p-2 border">Sin detalle por folio</td>
                      <td className="p-2 border text-right">
                        {openTotals.pax.toLocaleString('es-MX')}
                      </td>
                      <td className="p-2 border text-right">
                        {money(openTotals.ventas)}
                      </td>
                    </tr>
                  )}

                  <tr className="font-bold bg-zinc-100">
                    <td className="p-2 border">TOTAL KPI</td>
                    <td className="p-2 border" />
                    <td className="p-2 border text-right">
                      {kpiTotals.pax.toLocaleString('es-MX')}
                    </td>
                    <td className="p-2 border text-right">
                      {money(kpiTotals.ventas)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <p className="text-xs text-zinc-500">
              El detalle individual muestra únicamente cuentas cerradas disponibles
              en las vistas de reporte. Las cuentas no cerradas se muestran solo
              de forma agregada para conservar la conciliación con el KPI.
            </p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
