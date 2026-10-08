import React, { useEffect, useState } from 'react';
import api from '../../lib/api';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { Receipt, Loader2 } from 'lucide-react';
const money = value => new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(value || 0));

export default function TicketVentaModal({
  open,
  onClose,
  ticketPk,
  serverId,
  sucursal,
  seleccion,
  isOpen,
}) {
  open = open ?? isOpen;
  const [loading, setLoading] = useState(false);
  const [ticket, setTicket] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!open || (!ticketPk && !(serverId && seleccion?.folio && seleccion?.fecha))) return;

    let active = true;

    const cargarTicket = async () => {
      setLoading(true);
      setTicket(null);
      setError('');

      try {
        const response = ticketPk
          ? await api.get(`/v2/comercial/analytics/tickets/${encodeURIComponent(ticketPk)}`, { timeout: 30000 })
          : await api.get('/comercial/ticket-venta/' + serverId, {
              params: { sucursal, folio: seleccion.folio, fecha: seleccion.fecha }, timeout: 30000
            });
        if (!ticketPk) {
          if (active) setTicket(response.data?.ticket || null);
          return;
        }

        const payload = response.data?.data || {};
        const header = payload.ticket || null;
        const lines = Array.isArray(payload.lines)
          ? payload.lines
          : (Array.isArray(payload.lineas) ? payload.lineas : []);

        if (!header) {
          throw new Error('No se encontró información para este folio.');
        }

        if (active) {
          setTicket({
            ...header,
            unidad: header.unidad,
            folio: header.numero_ticket,
            fecha_hora: (
              header.fecha_hora
              || header.fecha
              || header.fecha_operacion
            ),
            pax: header.pax,
            vendedor: header.vendedor || null,
            sistema_origen: header.sistema_origen || null,
            estado: header.estado || 'CERRADA',
            items: lines.map((line) => ({
              ...line,
              cantidad: line.cantidad,
              descripcion: line.producto || line.descripcion,
              precio_unitario: line.precio_unitario,
              importe: line.importe_bruto ?? line.importe,
              descuento_pct: line.descuento_pct ?? 0,
              descuento_importe: (
                line.descuento_importe
                ?? line.descuento
                ?? 0
              ),
              importe_neto: (
                line.importe_neto
                ?? line.importe
                ?? line.importe_bruto
                ?? 0
              ),
            })),
            subtotal: header.subtotal ?? header.total ?? header.ventas,
            descuento_productos: header.descuento_productos ?? 0,
            descuento_cuenta: header.descuento_cuenta ?? 0,
            descuento: header.descuento ?? 0,
            impuesto: header.impuesto ?? null,
            total: header.total ?? header.ventas,
            propina: header.propina ?? 0,
          });
        }
      } catch (err) {
        if (active) {
          setError(
            err?.response?.data?.detail
            || err?.message
            || 'No fue posible cargar el ticket de venta.'
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    };

    cargarTicket();

    return () => {
      active = false;
    };
  }, [
    open,
    ticketPk, serverId, sucursal, seleccion,
  ]);

  if (!open) return null;

  return (
    <Dialog open={open} onOpenChange={(nextOpen) => !nextOpen && onClose()}>
      <DialogContent className="max-w-xl max-h-[92vh] overflow-auto bg-zinc-100">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Receipt className="h-5 w-5 text-zinc-700" />
            Ticket de Venta
          </DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="flex justify-center py-14">
            <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
          </div>
        ) : ticket ? (
          <div className="mx-auto w-full max-w-md bg-white border border-zinc-300 shadow-sm px-6 py-7 font-mono text-[13px] text-zinc-900">
            <div className="text-center">
              <p className="text-lg font-bold tracking-wide">{ticket.unidad}</p>
              <p className="font-semibold mt-1">TICKET DE SERVICIO</p>
              <p className="text-xs mt-1">
                {ticket.estado === 'ABIERTA' ? 'VENTA EN CURSO' : 'VENTA CERRADA'}
              </p>
            </div>

            <div className="border-t border-dashed border-zinc-500 mt-4 pt-3 space-y-1">
              <div className="flex justify-between gap-3">
                <span>FOLIO:</span>
                <span className="font-bold">{ticket.folio}</span>
              </div>
              {ticket.mesa && (
                <div className="flex justify-between gap-3">
                  <span>MESA:</span>
                  <span className="text-right uppercase">{ticket.mesa}</span>
                </div>
              )}
              <div className="flex justify-between gap-3">
                <span>FECHA:</span>
                <span className="text-right">{String(ticket.fecha_hora || '').replace('T', ' ').slice(0, 19)}</span>
              </div>
              {ticket.vendedor && (
                <div className="flex justify-between gap-3">
                  <span>VENDEDOR:</span>
                  <span className="text-right uppercase">{ticket.vendedor}</span>
                </div>
              )}
              {Number(ticket.pax || 0) > 0 && (
                <div className="flex justify-between gap-3">
                  <span>PAX:</span>
                  <span>{ticket.pax}</span>
                </div>
              )}
            </div>

            <div className="border-t border-dashed border-zinc-500 mt-3 pt-3 space-y-1 break-words">
              {ticket.cliente_nombre && <p><strong>CLIENTE:</strong> {ticket.cliente_nombre}</p>}
              {ticket.cliente_rfc && <p><strong>RFC:</strong> {ticket.cliente_rfc}</p>}
              {ticket.cliente_direccion && <p><strong>DIRECCIÓN:</strong> {ticket.cliente_direccion}</p>}
            </div>
            <div className="border-t border-dashed border-zinc-500 mt-3 pt-3">
              <div className="grid grid-cols-[44px_1fr_76px_88px] gap-2 font-bold pb-2">
                <span>CANT</span>
                <span>DESCRIPCIÓN</span>
                <span className="text-right">P.UNIT.</span>
                <span className="text-right">IMPORTE</span>
              </div>

              <div className="space-y-2">
                {(ticket.items || []).map((item, idx) => (
                  <div key={item.partida_origen_id || idx} className="grid grid-cols-[44px_1fr_76px_88px] gap-2 items-start">
                    <span>
                      {Number(item.cantidad || 0).toLocaleString(
                        'es-MX',
                        { maximumFractionDigits: 3 }
                      )}
                    </span>
                    <div>
                      <p className="uppercase leading-tight">{item.descripcion}</p>
                      {item.partida_comentario && <p className="text-xs whitespace-pre-wrap break-words">{item.partida_comentario}</p>}
                      {item.comentario_descuento && <p className="text-xs whitespace-pre-wrap break-words">DESC.: {item.comentario_descuento}</p>}
                    </div>
                    <span className="text-right">
                      {money(item.precio_unitario)}
                    </span>
                    <div className="text-right">
                      <span>{money(item.importe)}</span>
                      {Number(item.descuento_importe || 0) > 0.005 && (
                        <div className="text-[11px] mt-1">
                          <p className="text-zinc-500">
                            DESC. {Number(item.descuento_pct || 0).toLocaleString('es-MX', { maximumFractionDigits: 2 })}%:
                            {' '}
                            <span className="text-red-600 font-semibold">
                              -{money(item.descuento_importe)}
                            </span>
                          </p>
                          <p className="font-semibold">
                            TOTAL PROD. {money(item.importe_neto ?? 0)}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="border-t border-dashed border-zinc-500 mt-4 pt-3 space-y-1">
              <div className="flex justify-between">
                <span>SUBTOTAL</span>
                <span>{money(ticket.subtotal)}</span>
              </div>
              {Number(ticket.descuento_productos || 0) > 0.005 && (
                <div className="flex justify-between">
                  <span>DESC. PRODUCTOS</span>
                  <span className="text-red-600 font-semibold">-{money(ticket.descuento_productos)}</span>
                </div>
              )}
              {Number(ticket.descuento_cuenta || 0) > 0.005 && (
                <div className="flex justify-between">
                  <span>DESC. CUENTA</span>
                  <span className="text-red-600 font-semibold">-{money(ticket.descuento_cuenta)}</span>
                </div>
              )}
              {Number(ticket.descuento || 0) > 0.005 &&
               Number(ticket.descuento_productos || 0) <= 0.005 &&
               Number(ticket.descuento_cuenta || 0) <= 0.005 && (
                <div className="flex justify-between">
                  <span>DESCUENTO</span>
                  <span className="text-red-600 font-semibold">-{money(ticket.descuento)}</span>
                </div>
              )}
              {ticket.impuesto != null && (
                <div className="flex justify-between">
                  <span>IMPUESTO</span>
                  <span>{money(ticket.impuesto)}</span>
                </div>
              )}
              <div className="flex justify-between text-base font-bold border-t border-zinc-900 mt-2 pt-2">
                <span>TOTAL VENTA</span>
                <span>{money(ticket.total)}</span>
              </div>
              {Number(ticket.propina || 0) > 0.005 && (
                <div className="flex justify-between">
                  <span>PROPINA</span>
                  <span>{money(ticket.propina)}</span>
                </div>
              )}
            </div>

            <div className="border-t border-dashed border-zinc-500 mt-5 pt-4 text-center text-[11px] text-zinc-500">
              {ticket.ticket_comentario_descuento && <p className="text-left whitespace-pre-wrap break-words mb-2">COMENTARIO DESCUENTO: {ticket.ticket_comentario_descuento}</p>}
              {ticket.ticket_comentario && <p className="text-left whitespace-pre-wrap break-words mb-2">COMENTARIO DEL TICKET: {ticket.ticket_comentario}</p>}
              <p>EDARSA HUB · CONSULTA DE VENTA</p>
            </div>
          </div>
        ) : (
          <div className="text-center py-12 text-zinc-500">
            <Receipt className="h-10 w-10 mx-auto mb-3 opacity-30" />
            <p>{error || 'No se encontró información para este folio.'}</p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

