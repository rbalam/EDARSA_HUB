/**
 * Modal CANÓNICO de Detalle de Movimientos / Consumos.
 * ====================================================
 * Regla de centralización: presentación única usada por Análisis (Reportes.js)
 * y Auditoría (Compras.js). Recibe el estado del hook `useDetalleProducto`.
 *
 * Props:
 *  - detalle: { open, loading, tipo, codigo, producto, movimientos, totales, error }
 *  - onClose: () => void
 *  - formatNumber: (n) => string  (formateador de la página anfitriona)
 */
import React from 'react';
import { X, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

const _fmtFecha = (fecha) => {
  if (!fecha) return '';
  const d = new Date(fecha);
  return isNaN(d.getTime()) ? String(fecha) : d.toLocaleDateString();
};

export const DetalleProductoModal = ({ detalle, onClose, formatNumber }) => {
  if (!detalle?.open) return null;

  const fmt = formatNumber || ((n) => Number(n || 0).toLocaleString());
  const { loading, tipo, codigo, producto, movimientos = [], totales = {}, error } = detalle;
  const esConsumos = tipo === 'consumos';

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      data-testid="detalle-producto-modal"
    >
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="px-4 py-3 border-b flex items-center justify-between bg-zinc-50">
          <div>
            <h3 className="font-semibold">
              {esConsumos ? 'Detalle de Consumos' : 'Detalle de Movimientos'}
            </h3>
            {(codigo || producto) && (
              <p className="text-sm text-zinc-500" data-testid="detalle-producto-titulo">
                {codigo} - {producto}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-zinc-200 rounded"
            data-testid="detalle-producto-cerrar-x"
            aria-label="Cerrar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-4 overflow-auto max-h-[60vh]">
          {loading ? (
            <div className="flex items-center justify-center py-8" data-testid="detalle-producto-loading">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            </div>
          ) : error ? (
            <p className="text-red-600 text-center py-4" data-testid="detalle-producto-error">{error}</p>
          ) : movimientos.length > 0 ? (
            <>
              <table className="w-full text-sm">
                <thead className="bg-zinc-100">
                  <tr>
                    <th className="py-2 px-3 text-left">Fecha</th>
                    <th className="py-2 px-3 text-left">Concepto</th>
                    <th className="py-2 px-3 text-left">Descripción</th>
                    <th className="py-2 px-3 text-right">Cantidad</th>
                    <th className="py-2 px-3 text-left">Almacén</th>
                    <th className="py-2 px-3 text-left">Referencia</th>
                  </tr>
                </thead>
                <tbody>
                  {movimientos.map((m, idx) => (
                    <tr
                      key={`mov-${m.fecha}-${m.concepto}-${idx}`}
                      className={`border-b ${m.tipo === 'E' ? 'bg-green-50' : 'bg-red-50'}`}
                    >
                      <td className="py-1.5 px-3">{_fmtFecha(m.fecha)}</td>
                      <td className="py-1.5 px-3">
                        <span className={`px-2 py-0.5 rounded text-xs ${m.tipo === 'E' ? 'bg-green-200' : 'bg-red-200'}`}>
                          {m.concepto}
                        </span>
                      </td>
                      <td className="py-1.5 px-3">{m.descripcion}</td>
                      <td className={`py-1.5 px-3 text-right font-medium ${m.cantidad >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {m.cantidad >= 0 ? '+' : ''}{fmt(m.cantidad)}
                      </td>
                      <td className="py-1.5 px-3">{m.almacen}</td>
                      <td className="py-1.5 px-3 text-zinc-500">{m.referencia}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {totales && (
                <div className="mt-4 p-3 bg-zinc-100 rounded flex gap-6">
                  <div>
                    <span className="text-xs text-zinc-500">Total Entradas:</span>
                    <span className="ml-2 font-bold text-green-600">+{fmt(totales.entradas || 0)}</span>
                  </div>
                  <div>
                    <span className="text-xs text-zinc-500">Total Salidas:</span>
                    <span className="ml-2 font-bold text-red-600">-{fmt(totales.salidas || 0)}</span>
                  </div>
                  <div>
                    <span className="text-xs text-zinc-500">Neto:</span>
                    <span className={`ml-2 font-bold ${totales.neto >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {fmt(totales.neto || 0)}
                    </span>
                  </div>
                </div>
              )}
            </>
          ) : (
            <p className="text-center text-zinc-500 py-8" data-testid="detalle-producto-vacio">
              No se encontraron {esConsumos ? 'consumos' : 'movimientos'} para este producto en el período seleccionado
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-3 border-t bg-zinc-50 flex justify-end">
          <Button variant="outline" onClick={onClose} data-testid="detalle-producto-cerrar-btn">
            Cerrar
          </Button>
        </div>
      </div>
    </div>
  );
};

export default DetalleProductoModal;
