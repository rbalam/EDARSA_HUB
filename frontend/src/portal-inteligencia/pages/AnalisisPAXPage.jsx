/**
 * Análisis PAX - Personas atendidas, propinas, cheque promedio (datos reales, sin mock).
 * Fuente: /api/inteligencia/dashboard -> kpis + ventas_por_unidad.
 */
import React, { useState, useEffect } from 'react';
import { Users, DollarSign, TrendingUp, Receipt } from 'lucide-react';
import { apiGet, ESTADO } from '../api/client';
import { EstadoVacio } from '../components/EstadoVacio';

export default function AnalisisPAXPage({ unidadSeleccionada }) {
  const [resumen, setResumen] = useState(null);
  const [porUnidad, setPorUnidad] = useState([]);
  const [estado, setEstado] = useState(ESTADO.CARGANDO);

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unidadSeleccionada]);

  const fetchData = async () => {
    setEstado(ESTADO.CARGANDO);
    const { estado: est, data } = await apiGet('/inteligencia/dashboard', { unidad: unidadSeleccionada, periodo: 'mes' });
    if (est !== ESTADO.OK || !data || data.success === false || !data.kpis) {
      setResumen(null); setPorUnidad([]);
      setEstado(est === ESTADO.OK ? ESTADO.ERROR : est);
      return;
    }
    const k = data.kpis;
    const pax = Number(k.pax_total || 0), cheques = Number(k.cheques_total || 0), propinas = Number(k.propinas_total || 0);
    setResumen({
      paxTotal: pax,
      propinaTotal: propinas,
      ticketPromedio: Number(k.cheque_promedio || 0),
      chequesTotal: cheques,
      propinaPorPax: pax > 0 ? propinas / pax : 0,
      paxPorCheque: cheques > 0 ? pax / cheques : 0,
    });
    setPorUnidad((data.ventas_por_unidad || []).map(u => ({
      unidad: u.unidad,
      pax: Number(u.pax || 0),
      cheques: Number(u.tickets || 0),
      propina: Number(u.propinas || 0),
      ventas: Number(u.ventas || 0),
      ticketPromedio: Number(u.tickets) > 0 ? Number(u.ventas || 0) / Number(u.tickets) : 0,
    })));
    setEstado(ESTADO.OK);
  };

  const formatMoney = (val) => {
    const v = Number(val || 0);
    if (v >= 1000000) return `$${(v / 1000000).toFixed(2)}M`;
    if (v >= 1000) return `$${(v / 1000).toFixed(1)}K`;
    return `$${v.toFixed(0)}`;
  };

  if (estado !== ESTADO.OK || !resumen) {
    return (
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl" data-testid="analisis-pax-page">
        <EstadoVacio estado={estado} testid="analisis-pax-estado" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="analisis-pax-page">
      {/* KPI Cards principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-500/20 to-blue-600/10 border border-blue-500/30 rounded-xl p-5">
          <Users className="h-8 w-8 text-blue-400 mb-3" />
          <p className="text-3xl font-bold text-white">{resumen.paxTotal.toLocaleString()}</p>
          <p className="text-sm text-slate-400 mt-1">PAX Total</p>
        </div>
        <div className="bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 border border-emerald-500/30 rounded-xl p-5">
          <DollarSign className="h-8 w-8 text-emerald-400 mb-3" />
          <p className="text-3xl font-bold text-white">{formatMoney(resumen.propinaTotal)}</p>
          <p className="text-sm text-slate-400 mt-1">Propinas Totales</p>
        </div>
        <div className="bg-gradient-to-br from-purple-500/20 to-purple-600/10 border border-purple-500/30 rounded-xl p-5">
          <Receipt className="h-8 w-8 text-purple-400 mb-3" />
          <p className="text-3xl font-bold text-white">${resumen.ticketPromedio.toLocaleString('es-MX', { maximumFractionDigits: 0 })}</p>
          <p className="text-sm text-slate-400 mt-1">Cheque Promedio</p>
        </div>
        <div className="bg-gradient-to-br from-amber-500/20 to-amber-600/10 border border-amber-500/30 rounded-xl p-5">
          <TrendingUp className="h-8 w-8 text-amber-400 mb-3" />
          <p className="text-3xl font-bold text-white">${resumen.propinaPorPax.toFixed(2)}</p>
          <p className="text-sm text-slate-400 mt-1">Propina por PAX</p>
        </div>
      </div>

      {/* PAX por Unidad */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Users className="h-5 w-5 text-blue-400" /> PAX por Unidad de Negocio
        </h3>
        {porUnidad.length === 0 ? (
          <EstadoVacio estado={ESTADO.SIN_DATOS} testid="pax-por-unidad-vacio" compacto />
        ) : (
          <div className="space-y-4">
            {porUnidad.map((u) => {
              const porcentaje = ((u.pax / (resumen.paxTotal || 1)) * 100).toFixed(1);
              return (
                <div key={u.unidad}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-white">{u.unidad}</span>
                    <div className="flex items-center gap-4">
                      <span className="text-sm font-semibold text-blue-400">{u.pax.toLocaleString()} PAX</span>
                      <span className="text-xs text-slate-500 w-12 text-right">{porcentaje}%</span>
                    </div>
                  </div>
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-blue-500 to-blue-400 rounded-full" style={{ width: `${porcentaje}%` }} />
                  </div>
                  <div className="flex justify-between mt-1 text-xs text-slate-500">
                    <span>Propina: {formatMoney(u.propina)}</span>
                    <span>Cheque prom.: ${u.ticketPromedio.toLocaleString('es-MX', { maximumFractionDigits: 0 })}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Tabla detallada por unidad */}
      {porUnidad.length > 0 && (
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-700"><h3 className="text-lg font-semibold text-white">Detalle por Unidad</h3></div>
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left text-xs font-medium text-slate-400 px-4 py-3">UNIDAD</th>
                <th className="text-right text-xs font-medium text-slate-400 px-4 py-3">PAX</th>
                <th className="text-right text-xs font-medium text-slate-400 px-4 py-3">CHEQUES</th>
                <th className="text-right text-xs font-medium text-slate-400 px-4 py-3">PAX/CHEQUE</th>
                <th className="text-right text-xs font-medium text-slate-400 px-4 py-3">PROPINAS</th>
                <th className="text-right text-xs font-medium text-slate-400 px-4 py-3">PROPINA/PAX</th>
                <th className="text-right text-xs font-medium text-slate-400 px-4 py-3">CHEQUE PROM.</th>
              </tr>
            </thead>
            <tbody>
              {porUnidad.map((u) => (
                <tr key={u.unidad} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                  <td className="px-4 py-3 text-white font-medium">{u.unidad}</td>
                  <td className="px-4 py-3 text-right text-blue-400">{u.pax.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right text-slate-300">{u.cheques.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right text-slate-300">{u.cheques > 0 ? (u.pax / u.cheques).toFixed(2) : '—'}</td>
                  <td className="px-4 py-3 text-right text-emerald-400">{formatMoney(u.propina)}</td>
                  <td className="px-4 py-3 text-right text-amber-400">${u.pax > 0 ? (u.propina / u.pax).toFixed(2) : '0.00'}</td>
                  <td className="px-4 py-3 text-right text-purple-400">${u.ticketPromedio.toLocaleString('es-MX', { maximumFractionDigits: 0 })}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="bg-slate-800/80">
                <td className="px-4 py-3 text-white font-bold">TOTAL</td>
                <td className="px-4 py-3 text-right text-blue-400 font-bold">{resumen.paxTotal.toLocaleString()}</td>
                <td className="px-4 py-3 text-right text-white font-bold">{resumen.chequesTotal.toLocaleString()}</td>
                <td className="px-4 py-3 text-right text-white font-bold">{resumen.paxPorCheque.toFixed(2)}</td>
                <td className="px-4 py-3 text-right text-emerald-400 font-bold">{formatMoney(resumen.propinaTotal)}</td>
                <td className="px-4 py-3 text-right text-amber-400 font-bold">${resumen.propinaPorPax.toFixed(2)}</td>
                <td className="px-4 py-3 text-right text-purple-400 font-bold">${resumen.ticketPromedio.toLocaleString('es-MX', { maximumFractionDigits: 0 })}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </div>
  );
}
