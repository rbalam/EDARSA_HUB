/**
 * Modal de Drill-Down / Reconstrucción de Ticket (máxima profundidad).
 * Nivel 1: lista de tickets/cuentas del periodo+unidad (drill nivel cuenta).
 * Nivel 2: líneas (productos) de un ticket — el nivel más bajo.
 * Fuente: /api/inteligencia/tickets y /api/inteligencia/ticket-detalle (NO-LIVE).
 */
import React, { useState, useEffect } from 'react';
import { X, Receipt, ChevronLeft, Loader2, ArrowLeft } from 'lucide-react';
import { apiGet, ESTADO } from '../api/client';
import { EstadoVacio } from './EstadoVacio';
import { ExportButtons } from './ExportButtons';

const fMoney = (v) => `$${Number(v || 0).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export function TicketDrilldownModal({ open, onClose, unidad, periodo, fechaInicio, fechaFin, titulo = 'Reconstrucción de Tickets' }) {
  const [tickets, setTickets] = useState([]);
  const [estado, setEstado] = useState(ESTADO.CARGANDO);
  const [filtros, setFiltros] = useState(null);
  const [sel, setSel] = useState(null);       // ticket seleccionado
  const [lineas, setLineas] = useState([]);
  const [estadoDet, setEstadoDet] = useState(ESTADO.CARGANDO);

  useEffect(() => {
    if (!open) return;
    setSel(null);
    fetchTickets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, unidad, periodo, fechaInicio, fechaFin]);

  const fetchTickets = async () => {
    setEstado(ESTADO.CARGANDO);
    const rango = (fechaInicio && fechaFin) ? { fecha_inicio: fechaInicio, fecha_fin: fechaFin } : { periodo };
    const { estado: est, data } = await apiGet('/inteligencia/tickets', { unidad, limit: 500, ...rango });
    if (est !== ESTADO.OK || !data || data.success === false) {
      setTickets([]); setEstado(est === ESTADO.OK ? ESTADO.ERROR : est); return;
    }
    setTickets(data.tickets || []);
    setFiltros(data.filtros || null);
    setEstado((data.tickets || []).length ? ESTADO.OK : ESTADO.SIN_DATOS);
  };

  const abrirTicket = async (t) => {
    setSel(t); setEstadoDet(ESTADO.CARGANDO); setLineas([]);
    const { estado: est, data } = await apiGet('/inteligencia/ticket-detalle', {
      numero_ticket: t.numero_ticket, unidad: t.unidad, fecha: t.fecha,
    });
    if (est !== ESTADO.OK || !data || data.success === false) {
      setEstadoDet(est === ESTADO.OK ? ESTADO.ERROR : est); return;
    }
    setLineas(data.lineas || []);
    setEstadoDet((data.lineas || []).length ? ESTADO.OK : ESTADO.SIN_DATOS);
  };

  if (!open) return null;

  const meta = `${unidad === 'todas' || !unidad ? 'Consolidado' : unidad} · ${filtros?.periodo_label || ''}`;
  const ticketCols = [
    { key: 'fecha', label: 'Fecha' }, { key: 'hora', label: 'Hora' },
    { key: 'unidad', label: 'Unidad' }, { key: 'numero_ticket', label: 'Ticket' },
    { key: 'pax', label: 'PAX' }, { key: 'lineas', label: 'Líneas' },
    { key: 'ventas', label: 'Ventas' }, { key: 'propina', label: 'Propina' },
  ];
  const lineaCols = [
    { key: 'codigo', label: 'Código' }, { key: 'producto', label: 'Producto' },
    { key: 'clasificacion', label: 'Clasificación' }, { key: 'familia', label: 'Familia' },
    { key: 'casa', label: 'Casa' }, { key: 'grado_alcohol', label: 'Grado' },
    { key: 'cantidad', label: 'Cantidad' }, { key: 'precio_unitario', label: 'P.Unit' },
    { key: 'importe', label: 'Importe' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4" data-testid="drilldown-modal">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-5xl max-h-[88vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-slate-700">
          <div className="flex items-center gap-3">
            {sel && (
              <button onClick={() => setSel(null)} data-testid="drilldown-back-btn"
                className="p-1.5 rounded-lg hover:bg-slate-700 text-slate-300"><ArrowLeft className="h-4 w-4" /></button>
            )}
            <Receipt className="h-5 w-5 text-emerald-400" />
            <div>
              <h3 className="text-white font-semibold">{sel ? `Ticket ${sel.numero_ticket}` : titulo}</h3>
              <p className="text-xs text-slate-400">{meta}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {!sel && estado === ESTADO.OK && (
              <ExportButtons filename="tickets" title="Tickets" columns={ticketCols} rows={tickets} meta={meta} testid="drilldown-tickets-export" />
            )}
            {sel && estadoDet === ESTADO.OK && (
              <ExportButtons filename={`ticket_${sel.numero_ticket}`} title={`Ticket ${sel.numero_ticket}`} columns={lineaCols} rows={lineas} meta={meta} testid="drilldown-lineas-export" />
            )}
            <button onClick={onClose} data-testid="drilldown-close-btn" className="p-1.5 rounded-lg hover:bg-slate-700 text-slate-300"><X className="h-5 w-5" /></button>
          </div>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto">
          {!sel ? (
            estado !== ESTADO.OK ? (
              <EstadoVacio estado={estado} testid="drilldown-tickets-estado" />
            ) : (
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-slate-800">
                  <tr className="text-left text-xs text-slate-400">
                    <th className="px-4 py-2">FECHA</th><th className="px-4 py-2">HORA</th>
                    <th className="px-4 py-2">UNIDAD</th><th className="px-4 py-2">TICKET</th>
                    <th className="px-4 py-2 text-center">PAX</th><th className="px-4 py-2 text-center">LÍNEAS</th>
                    <th className="px-4 py-2 text-right">VENTAS</th>
                  </tr>
                </thead>
                <tbody>
                  {tickets.map((t, i) => (
                    <tr key={`${t.numero_ticket}-${i}`} onClick={() => abrirTicket(t)}
                      data-testid={`drilldown-ticket-row-${i}`}
                      className="border-t border-slate-700/40 hover:bg-slate-700/40 cursor-pointer">
                      <td className="px-4 py-2 text-slate-300">{t.fecha}</td>
                      <td className="px-4 py-2 text-slate-400">{t.hora}</td>
                      <td className="px-4 py-2 text-slate-300">{t.unidad}</td>
                      <td className="px-4 py-2 font-mono text-emerald-400">{t.numero_ticket}</td>
                      <td className="px-4 py-2 text-center text-slate-300">{t.pax}</td>
                      <td className="px-4 py-2 text-center text-slate-400">{t.lineas}</td>
                      <td className="px-4 py-2 text-right font-semibold text-white">{fMoney(t.ventas)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )
          ) : (
            estadoDet === ESTADO.CARGANDO ? (
              <div className="flex items-center justify-center py-16 text-slate-400"><Loader2 className="h-6 w-6 animate-spin" /></div>
            ) : estadoDet !== ESTADO.OK ? (
              <EstadoVacio estado={estadoDet} testid="drilldown-lineas-estado" />
            ) : (
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-slate-800">
                  <tr className="text-left text-xs text-slate-400">
                    <th className="px-4 py-2">PRODUCTO</th><th className="px-4 py-2">CLASIF.</th>
                    <th className="px-4 py-2">CASA</th><th className="px-4 py-2 text-center">GRADO</th>
                    <th className="px-4 py-2 text-center">CANT</th><th className="px-4 py-2 text-right">P.UNIT</th>
                    <th className="px-4 py-2 text-right">IMPORTE</th>
                  </tr>
                </thead>
                <tbody>
                  {lineas.map((l, i) => (
                    <tr key={i} className="border-t border-slate-700/40 hover:bg-slate-700/30">
                      <td className="px-4 py-2 text-white">{l.producto}<span className="block text-xs text-slate-500">{l.familia}</span></td>
                      <td className="px-4 py-2 text-slate-300">{l.clasificacion || '—'}</td>
                      <td className="px-4 py-2 text-slate-400">{l.casa || '—'}</td>
                      <td className="px-4 py-2 text-center text-amber-400">{l.grado_alcohol != null ? `${l.grado_alcohol}°` : '—'}</td>
                      <td className="px-4 py-2 text-center text-slate-300">{l.cantidad}</td>
                      <td className="px-4 py-2 text-right text-slate-400">{fMoney(l.precio_unitario)}</td>
                      <td className="px-4 py-2 text-right font-semibold text-emerald-400">{fMoney(l.importe)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )
          )}
        </div>

        {/* Footer total */}
        {sel && estadoDet === ESTADO.OK && (
          <div className="px-5 py-3 border-t border-slate-700 flex items-center justify-between bg-slate-800/60">
            <span className="text-sm text-slate-400">{lineas.length} líneas · PAX {sel.pax}</span>
            <span className="text-lg font-bold text-emerald-400">Total: {fMoney(sel.ventas)}</span>
          </div>
        )}
      </div>
    </div>
  );
}
