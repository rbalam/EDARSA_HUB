/**
 * Drill-down canónico de tickets comerciales.
 *
 * Responsabilidades:
 * - Presentar la lista de tickets de un alcance.
 * - Abrir y presentar el detalle de un ticket.
 * - No conoce rutas HTTP.
 * - No conoce clientes API específicos.
 * - No calcula KPIs.
 * - No reconstruye identidades en frontend.
 *
 * Los consumidores deben proporcionar:
 * - loadTickets(scope)
 * - loadTicketDetail(ticket)
 */
import React, { useEffect, useState } from 'react';
import {
  ArrowLeft,
  Loader2,
  Receipt,
  X,
} from 'lucide-react';

const STATUS = Object.freeze({
  LOADING: 'loading',
  OK: 'ok',
  EMPTY: 'empty',
  ERROR: 'error',
});

const moneyFormatter = new Intl.NumberFormat('es-MX', {
  style: 'currency',
  currency: 'MXN',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const formatMoney = (value) => (
  moneyFormatter.format(Number(value || 0))
);

function EmptyState({ status }) {
  const message = status === STATUS.ERROR
    ? 'No fue posible consultar la información.'
    : 'No existen datos para el alcance seleccionado.';

  return (
    <div className="px-6 py-16 text-center text-slate-400">
      {message}
    </div>
  );
}

export default function CanonicalTicketDrilldown({
  open,
  onClose,
  scope,
  title = 'Reconstrucción de tickets',
  loadTickets,
  loadTicketDetail,
  renderExportActions,
}) {
  const [tickets, setTickets] = useState([]);
  const [filters, setFilters] = useState(null);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [lines, setLines] = useState([]);
  const [ticketsStatus, setTicketsStatus] = useState(STATUS.LOADING);
  const [detailStatus, setDetailStatus] = useState(STATUS.LOADING);
  const [page, setPage] = useState(1);
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 0,
    total: 0,
    returned: 0,
    hasMore: false,
  });

  useEffect(() => {
    if (open) {
      setPage(1);
    }
  }, [open, scope]);

  useEffect(() => {
    let active = true;

    const fetchTickets = async () => {
      if (!open) return;

      setSelectedTicket(null);
      setLines([]);
      setTickets([]);
      setTicketsStatus(STATUS.LOADING);

      try {
        const result = await loadTickets(scope, { page });

        if (!active) return;

        const rows = Array.isArray(result?.tickets)
          ? result.tickets
          : [];

        setTickets(rows);
        setFilters(result?.filters || result?.filtros || null);
        setPagination({
          page: Number(result?.page || page),
          pageSize: Number(
            result?.pageSize
            || result?.page_size
            || 0
          ),
          total: Number(result?.total || 0),
          returned: Number(
            result?.returned ?? rows.length
          ),
          hasMore: Boolean(
            result?.hasMore ?? result?.has_more
          ),
        });
        setTicketsStatus(
          rows.length > 0 ? STATUS.OK : STATUS.EMPTY
        );
      } catch (error) {
        if (!active) return;

        setTickets([]);
        setPagination({
          page,
          pageSize: 0,
          total: 0,
          returned: 0,
          hasMore: false,
        });
        setTicketsStatus(STATUS.ERROR);
      }
    };

    fetchTickets();

    return () => {
      active = false;
    };
  }, [open, scope, page, loadTickets]);

  const openTicket = async (ticket) => {
    setSelectedTicket(ticket);
    setLines([]);
    setDetailStatus(STATUS.LOADING);

    try {
      const result = await loadTicketDetail(ticket, scope);
      const rows = Array.isArray(result?.lines)
        ? result.lines
        : Array.isArray(result?.lineas)
          ? result.lineas
          : [];

      setLines(rows);
      setDetailStatus(
        rows.length > 0 ? STATUS.OK : STATUS.EMPTY
      );
    } catch (error) {
      setLines([]);
      setDetailStatus(STATUS.ERROR);
    }
  };

  if (!open) return null;

  const scopeLabel = (
    scope?.businessUnitLabel
    || scope?.unidad
    || 'Consolidado'
  );

  const periodLabel = (
    filters?.periodo_label
    || scope?.periodLabel
    || ''
  );

  const metadata = [scopeLabel, periodLabel]
    .filter(Boolean)
    .join(' · ');

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
      data-testid="canonical-ticket-drilldown"
    >
      <div className="flex max-h-[88vh] w-full max-w-5xl flex-col overflow-hidden rounded-2xl border border-slate-700 bg-slate-900">
        <div className="flex items-center justify-between border-b border-slate-700 px-5 py-3">
          <div className="flex items-center gap-3">
            {selectedTicket && (
              <button
                type="button"
                onClick={() => setSelectedTicket(null)}
                className="rounded-lg p-1.5 text-slate-300 hover:bg-slate-700"
                aria-label="Regresar a tickets"
              >
                <ArrowLeft className="h-4 w-4" />
              </button>
            )}

            <Receipt className="h-5 w-5 text-emerald-400" />

            <div>
              <h3 className="font-semibold text-white">
                {selectedTicket
                  ? `Ticket ${selectedTicket.numero_ticket || selectedTicket.folio || ''}`
                  : title}
              </h3>
              <p className="text-xs text-slate-400">
                {metadata}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {renderExportActions?.({
              selectedTicket,
              tickets,
              lines,
              metadata,
            })}

            <button
              type="button"
              onClick={onClose}
              className="rounded-lg p-1.5 text-slate-300 hover:bg-slate-700"
              aria-label="Cerrar"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {!selectedTicket ? (
            ticketsStatus === STATUS.LOADING ? (
              <div className="flex justify-center py-16 text-slate-400">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : ticketsStatus !== STATUS.OK ? (
              <EmptyState status={ticketsStatus} />
            ) : (
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-slate-800">
                  <tr className="text-left text-xs text-slate-400">
                    <th className="px-4 py-2">FECHA</th>
                    <th className="px-4 py-2">HORA</th>
                    <th className="px-4 py-2">UNIDAD</th>
                    <th className="px-4 py-2">TICKET</th>
                    <th className="px-4 py-2 text-center">PAX</th>
                    <th className="px-4 py-2 text-center">LÍNEAS</th>
                    <th className="px-4 py-2 text-right">VENTAS</th>
                  </tr>
                </thead>

                <tbody>
                  {tickets.map((ticket) => {
                    const ticketKey = (
                      ticket.ticket_pk
                      || ticket.id
                      || [
                        ticket.unidad,
                        ticket.fecha,
                        ticket.numero_ticket,
                      ].filter(Boolean).join(':')
                    );

                    return (
                      <tr
                        key={ticketKey}
                        onClick={() => openTicket(ticket)}
                        className="cursor-pointer border-t border-slate-700/40 hover:bg-slate-700/40"
                      >
                        <td className="px-4 py-2 text-slate-300">
                          {ticket.fecha}
                        </td>
                        <td className="px-4 py-2 text-slate-400">
                          {ticket.hora}
                        </td>
                        <td className="px-4 py-2 text-slate-300">
                          {ticket.unidad}
                        </td>
                        <td className="px-4 py-2 font-mono text-emerald-400">
                          {ticket.numero_ticket || ticket.folio}
                        </td>
                        <td className="px-4 py-2 text-center text-slate-300">
                          {ticket.pax || 0}
                        </td>
                        <td className="px-4 py-2 text-center text-slate-400">
                          {ticket.lineas || 0}
                        </td>
                        <td className="px-4 py-2 text-right font-semibold text-white">
                          {formatMoney(ticket.ventas)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )
          ) : detailStatus === STATUS.LOADING ? (
            <div className="flex justify-center py-16 text-slate-400">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : detailStatus !== STATUS.OK ? (
            <EmptyState status={detailStatus} />
          ) : (
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-slate-800">
                <tr className="text-left text-xs text-slate-400">
                  <th className="px-4 py-2">PRODUCTO</th>
                  <th className="px-4 py-2">CLASIF.</th>
                  <th className="px-4 py-2">CASA</th>
                  <th className="px-4 py-2 text-center">GRADO</th>
                  <th className="px-4 py-2 text-center">CANT.</th>
                  <th className="px-4 py-2 text-right">P. UNIT.</th>
                  <th className="px-4 py-2 text-right">IMPORTE</th>
                </tr>
              </thead>

              <tbody>
                {lines.map((line, index) => (
                  <tr
                    key={
                      line.linea_pk
                      || line.id
                      || `${line.codigo || 'linea'}:${index}`
                    }
                    className="border-t border-slate-700/40 hover:bg-slate-700/30"
                  >
                    <td className="px-4 py-2 text-white">
                      {line.producto}
                      <span className="block text-xs text-slate-500">
                        {line.familia}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-slate-300">
                      {line.clasificacion || '—'}
                    </td>
                    <td className="px-4 py-2 text-slate-400">
                      {line.casa || '—'}
                    </td>
                    <td className="px-4 py-2 text-center text-amber-400">
                      {line.grado_alcohol != null
                        ? `${line.grado_alcohol}°`
                        : '—'}
                    </td>
                    <td className="px-4 py-2 text-center text-slate-300">
                      {line.cantidad}
                    </td>
                    <td className="px-4 py-2 text-right text-slate-400">
                      {formatMoney(line.precio_unitario)}
                    </td>
                    <td className="px-4 py-2 text-right font-semibold text-emerald-400">
                      {formatMoney(line.importe)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {!selectedTicket && ticketsStatus === STATUS.OK && (
          <div className="flex items-center justify-between border-t border-slate-700 bg-slate-800/60 px-5 py-3">
            <span className="text-sm text-slate-400">
              {pagination.total.toLocaleString('es-MX')} tickets
              {pagination.pageSize > 0 && (
                <>
                  {' · Página '}
                  {pagination.page.toLocaleString('es-MX')}
                </>
              )}
            </span>

            <div className="flex items-center gap-2">
              <button
                type="button"
                disabled={pagination.page <= 1}
                onClick={() => setPage(current => Math.max(1, current - 1))}
                className="rounded-lg border border-slate-600 px-3 py-1.5 text-sm text-slate-200 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Anterior
              </button>

              <button
                type="button"
                disabled={!pagination.hasMore}
                onClick={() => setPage(current => current + 1)}
                className="rounded-lg border border-slate-600 px-3 py-1.5 text-sm text-slate-200 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Siguiente
              </button>
            </div>
          </div>
        )}

        {selectedTicket && detailStatus === STATUS.OK && (
          <div className="flex items-center justify-between border-t border-slate-700 bg-slate-800/60 px-5 py-3">
            <span className="text-sm text-slate-400">
              {lines.length} líneas · PAX {selectedTicket.pax || 0}
            </span>
            <span className="text-lg font-bold text-emerald-400">
              Total: {formatMoney(selectedTicket.ventas)}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
