/**
 * Análisis PAX - Personas atendidas, propinas, ticket promedio
 */
import React, { useState, useEffect } from 'react';
import { Users, DollarSign, TrendingUp, Receipt, ArrowUpRight, Calendar } from 'lucide-react';

const FALLBACK_PAX_DATA = {
  resumen: {
    paxTotal: 16619,
    propinaTotal: 386800,
    ticketPromedio: 2712,
    chequesTotal: 5796,
    propinaPorPax: 23.28,
    paxPorCheque: 2.87
  },
  porUnidad: [
    { unidad: 'CIENFUEGOS', pax: 4555, propina: 125800, ticketPromedio: 2945, cheques: 1500 },
    { unidad: '130° MÉRIDA', pax: 3890, propina: 98500, ticketPromedio: 2680, cheques: 1320 },
    { unidad: '130° QUERÉTARO', pax: 3210, propina: 78200, ticketPromedio: 2520, cheques: 1180 },
    { unidad: 'LA ESTELAR', pax: 2850, propina: 52300, ticketPromedio: 2890, cheques: 980 },
    { unidad: 'ORIGEN', pax: 2114, propina: 32000, ticketPromedio: 2410, cheques: 816 },
  ],
  tendenciaSemanal: [
    { dia: 'Lunes', pax: 1850, propina: 42500 },
    { dia: 'Martes', pax: 1920, propina: 44800 },
    { dia: 'Miércoles', pax: 2150, propina: 51200 },
    { dia: 'Jueves', pax: 2480, propina: 58900 },
    { dia: 'Viernes', pax: 3250, propina: 82500 },
    { dia: 'Sábado', pax: 3120, propina: 75200 },
    { dia: 'Domingo', pax: 1849, propina: 31700 },
  ]
};

export default function AnalisisPAXPage({ unidadSeleccionada }) {
  const [data, setData] = useState(FALLBACK_PAX_DATA);

  const formatMoney = (val) => {
    if (val >= 1000000) return `$${(val / 1000000).toFixed(2)}M`;
    if (val >= 1000) return `$${(val / 1000).toFixed(1)}K`;
    return `$${val.toFixed(0)}`;
  };

  const maxPaxDia = Math.max(...data.tendenciaSemanal.map(d => d.pax));

  return (
    <div className="space-y-6" data-testid="analisis-pax-page">
      {/* KPI Cards principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-500/20 to-blue-600/10 border border-blue-500/30 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <Users className="h-8 w-8 text-blue-400" />
            <span className="flex items-center gap-1 text-xs text-emerald-400">
              <ArrowUpRight className="h-3 w-3" /> +8.3%
            </span>
          </div>
          <p className="text-3xl font-bold text-white">{data.resumen.paxTotal.toLocaleString()}</p>
          <p className="text-sm text-slate-400 mt-1">PAX Total</p>
        </div>

        <div className="bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 border border-emerald-500/30 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <DollarSign className="h-8 w-8 text-emerald-400" />
            <span className="flex items-center gap-1 text-xs text-emerald-400">
              <ArrowUpRight className="h-3 w-3" /> +15.2%
            </span>
          </div>
          <p className="text-3xl font-bold text-white">{formatMoney(data.resumen.propinaTotal)}</p>
          <p className="text-sm text-slate-400 mt-1">Propinas Totales</p>
        </div>

        <div className="bg-gradient-to-br from-purple-500/20 to-purple-600/10 border border-purple-500/30 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <Receipt className="h-8 w-8 text-purple-400" />
            <span className="flex items-center gap-1 text-xs text-emerald-400">
              <ArrowUpRight className="h-3 w-3" /> +5.7%
            </span>
          </div>
          <p className="text-3xl font-bold text-white">${data.resumen.ticketPromedio.toLocaleString()}</p>
          <p className="text-sm text-slate-400 mt-1">Ticket Promedio</p>
        </div>

        <div className="bg-gradient-to-br from-amber-500/20 to-amber-600/10 border border-amber-500/30 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <TrendingUp className="h-8 w-8 text-amber-400" />
          </div>
          <p className="text-3xl font-bold text-white">${data.resumen.propinaPorPax.toFixed(2)}</p>
          <p className="text-sm text-slate-400 mt-1">Propina por PAX</p>
        </div>
      </div>

      {/* Grid principal */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* PAX por Unidad */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Users className="h-5 w-5 text-blue-400" />
            PAX por Unidad de Negocio
          </h3>
          
          <div className="space-y-4">
            {data.porUnidad.map((unidad, idx) => {
              const porcentaje = ((unidad.pax / data.resumen.paxTotal) * 100).toFixed(1);
              return (
                <div key={unidad.unidad}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-white">{unidad.unidad}</span>
                    <div className="flex items-center gap-4">
                      <span className="text-sm font-semibold text-blue-400">
                        {unidad.pax.toLocaleString()} PAX
                      </span>
                      <span className="text-xs text-slate-500 w-12 text-right">{porcentaje}%</span>
                    </div>
                  </div>
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-blue-500 to-blue-400 rounded-full"
                      style={{ width: `${porcentaje}%` }}
                    />
                  </div>
                  <div className="flex justify-between mt-1 text-xs text-slate-500">
                    <span>Propina: {formatMoney(unidad.propina)}</span>
                    <span>Ticket: ${unidad.ticketPromedio.toLocaleString()}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Tendencia Semanal */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Calendar className="h-5 w-5 text-emerald-400" />
            Tendencia Semanal
          </h3>
          
          <div className="flex items-end justify-between h-48 gap-2">
            {data.tendenciaSemanal.map((dia, idx) => {
              const altura = (dia.pax / maxPaxDia) * 100;
              const esFinDeSemana = dia.dia === 'Viernes' || dia.dia === 'Sábado';
              
              return (
                <div key={dia.dia} className="flex-1 flex flex-col items-center">
                  <div className="w-full flex flex-col items-center justify-end h-40">
                    <span className="text-xs text-emerald-400 mb-1">{formatMoney(dia.propina)}</span>
                    <div 
                      className={`w-full rounded-t-lg transition-all ${
                        esFinDeSemana ? 'bg-gradient-to-t from-emerald-600 to-emerald-400' : 'bg-gradient-to-t from-blue-600 to-blue-400'
                      }`}
                      style={{ height: `${altura}%` }}
                    />
                  </div>
                  <div className="text-center mt-2">
                    <p className="text-xs text-white font-medium">{dia.pax.toLocaleString()}</p>
                    <p className="text-xs text-slate-500">{dia.dia.substring(0, 3)}</p>
                  </div>
                </div>
              );
            })}
          </div>
          
          {/* Leyenda */}
          <div className="flex justify-center gap-6 mt-4 pt-4 border-t border-slate-700">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-blue-500" />
              <span className="text-xs text-slate-400">Entre semana</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-emerald-500" />
              <span className="text-xs text-slate-400">Fin de semana</span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabla detallada */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-700">
          <h3 className="text-lg font-semibold text-white">Detalle por Unidad</h3>
        </div>
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-700">
              <th className="text-left text-xs font-medium text-slate-400 px-4 py-3">UNIDAD</th>
              <th className="text-right text-xs font-medium text-slate-400 px-4 py-3">PAX</th>
              <th className="text-right text-xs font-medium text-slate-400 px-4 py-3">CHEQUES</th>
              <th className="text-right text-xs font-medium text-slate-400 px-4 py-3">PAX/CHEQUE</th>
              <th className="text-right text-xs font-medium text-slate-400 px-4 py-3">PROPINAS</th>
              <th className="text-right text-xs font-medium text-slate-400 px-4 py-3">PROPINA/PAX</th>
              <th className="text-right text-xs font-medium text-slate-400 px-4 py-3">TICKET PROM.</th>
            </tr>
          </thead>
          <tbody>
            {data.porUnidad.map((unidad) => {
              const paxPorCheque = (unidad.pax / unidad.cheques).toFixed(2);
              const propinaPorPax = (unidad.propina / unidad.pax).toFixed(2);
              
              return (
                <tr key={unidad.unidad} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                  <td className="px-4 py-3 text-white font-medium">{unidad.unidad}</td>
                  <td className="px-4 py-3 text-right text-blue-400">{unidad.pax.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right text-slate-300">{unidad.cheques.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right text-slate-300">{paxPorCheque}</td>
                  <td className="px-4 py-3 text-right text-emerald-400">{formatMoney(unidad.propina)}</td>
                  <td className="px-4 py-3 text-right text-amber-400">${propinaPorPax}</td>
                  <td className="px-4 py-3 text-right text-purple-400">${unidad.ticketPromedio.toLocaleString()}</td>
                </tr>
              );
            })}
          </tbody>
          <tfoot>
            <tr className="bg-slate-800/80">
              <td className="px-4 py-3 text-white font-bold">TOTAL</td>
              <td className="px-4 py-3 text-right text-blue-400 font-bold">{data.resumen.paxTotal.toLocaleString()}</td>
              <td className="px-4 py-3 text-right text-white font-bold">{data.resumen.chequesTotal.toLocaleString()}</td>
              <td className="px-4 py-3 text-right text-white font-bold">{data.resumen.paxPorCheque.toFixed(2)}</td>
              <td className="px-4 py-3 text-right text-emerald-400 font-bold">{formatMoney(data.resumen.propinaTotal)}</td>
              <td className="px-4 py-3 text-right text-amber-400 font-bold">${data.resumen.propinaPorPax.toFixed(2)}</td>
              <td className="px-4 py-3 text-right text-purple-400 font-bold">${data.resumen.ticketPromedio.toLocaleString()}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
