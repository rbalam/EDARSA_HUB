/**
 * Ventas por Casa/Distribuidor (datos reales, sin mock).
 * Fuente: /api/inteligencia/dashboard -> casas_distribuidoras.
 * Nota: si la casa no está sincronizada en el detalle, el bloque queda vacío (SIN_DATOS_SYNC).
 */
import React, { useState, useEffect } from 'react';
import { Building2, Percent } from 'lucide-react';
import { apiGet, ESTADO } from '../api/client';
import { EstadoVacio } from '../components/EstadoVacio';

const COLORES = ['emerald', 'amber', 'blue', 'orange', 'purple', 'yellow', 'pink'];
const CLS = {
  emerald: { bg: 'bg-emerald-500/20', border: 'border-emerald-500/30', text: 'text-emerald-400', bar: 'bg-emerald-500' },
  amber: { bg: 'bg-amber-500/20', border: 'border-amber-500/30', text: 'text-amber-400', bar: 'bg-amber-500' },
  blue: { bg: 'bg-blue-500/20', border: 'border-blue-500/30', text: 'text-blue-400', bar: 'bg-blue-500' },
  orange: { bg: 'bg-orange-500/20', border: 'border-orange-500/30', text: 'text-orange-400', bar: 'bg-orange-500' },
  purple: { bg: 'bg-purple-500/20', border: 'border-purple-500/30', text: 'text-purple-400', bar: 'bg-purple-500' },
  yellow: { bg: 'bg-yellow-500/20', border: 'border-yellow-500/30', text: 'text-yellow-400', bar: 'bg-yellow-500' },
  pink: { bg: 'bg-pink-500/20', border: 'border-pink-500/30', text: 'text-pink-400', bar: 'bg-pink-500' },
};

export default function VentasCasaPage({ unidadSeleccionada }) {
  const [casas, setCasas] = useState([]);
  const [estado, setEstado] = useState(ESTADO.CARGANDO);
  const [vista, setVista] = useState('cards');

  useEffect(() => {
    fetchCasas();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unidadSeleccionada]);

  const fetchCasas = async () => {
    setEstado(ESTADO.CARGANDO);
    const { estado: est, data } = await apiGet('/inteligencia/dashboard', { unidad: unidadSeleccionada, periodo: 'mes' });
    if (est !== ESTADO.OK || !data || data.success === false) {
      setCasas([]);
      setEstado(est === ESTADO.OK ? ESTADO.ERROR : est);
      return;
    }
    const lista = (data.casas_distribuidoras || []).map((c, idx) => ({
      casa: c.casa,
      ventas: Number(c.ventas || 0),
      porcentaje: Number(c.participacion || 0),
      color: COLORES[idx % COLORES.length],
    }));
    setCasas(lista);
    setEstado(lista.length ? ESTADO.OK : ESTADO.SIN_DATOS);
  };

  const formatMoney = (val) => {
    const v = Number(val || 0);
    if (v >= 1000000) return `$${(v / 1000000).toFixed(2)}M`;
    if (v >= 1000) return `$${(v / 1000).toFixed(1)}K`;
    return `$${v.toFixed(0)}`;
  };

  const totalVentas = casas.reduce((a, b) => a + b.ventas, 0);

  if (estado !== ESTADO.OK) {
    return (
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl" data-testid="ventas-casa-page">
        <EstadoVacio estado={estado} testid="ventas-casa-estado" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="ventas-casa-page">
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <button onClick={() => setVista('cards')} className={`px-4 py-2 rounded-lg text-sm ${vista === 'cards' ? 'bg-emerald-500 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}>Vista Cards</button>
          <button onClick={() => setVista('tabla')} className={`px-4 py-2 rounded-lg text-sm ${vista === 'tabla' ? 'bg-emerald-500 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}>Vista Tabla</button>
        </div>
        <div className="text-sm text-slate-400">Total: <span className="text-emerald-400 font-semibold">{formatMoney(totalVentas)}</span></div>
      </div>

      {vista === 'cards' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {casas.map((casa) => {
            const colors = CLS[casa.color] || CLS.emerald;
            return (
              <div key={casa.casa} className={`${colors.bg} border ${colors.border} rounded-xl p-5`}>
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <Building2 className={`h-6 w-6 ${colors.text}`} />
                    <h3 className="font-bold text-white">{casa.casa}</h3>
                  </div>
                  <span className={`text-2xl font-bold ${colors.text}`}>{casa.porcentaje.toFixed(1)}%</span>
                </div>
                <p className="text-2xl font-bold text-white mb-3">{formatMoney(casa.ventas)}</p>
                <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div className={`h-full ${colors.bar} rounded-full transition-all`} style={{ width: `${casa.porcentaje}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left text-xs font-medium text-slate-400 px-4 py-3">CASA / DISTRIBUIDOR</th>
                <th className="text-right text-xs font-medium text-slate-400 px-4 py-3">VENTAS</th>
                <th className="text-center text-xs font-medium text-slate-400 px-4 py-3">% PART.</th>
              </tr>
            </thead>
            <tbody>
              {casas.map((casa) => {
                const colors = CLS[casa.color] || CLS.emerald;
                return (
                  <tr key={casa.casa} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${colors.bar}`} />
                        <span className="font-medium text-white">{casa.casa}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right"><span className="font-semibold text-emerald-400">{formatMoney(casa.ventas)}</span></td>
                    <td className="px-4 py-3 text-center"><span className={`px-2 py-1 rounded text-xs ${colors.bg} ${colors.text}`}>{casa.porcentaje.toFixed(1)}%</span></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Gráfica de distribución */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Percent className="h-5 w-5 text-emerald-400" /> Distribución de Ventas por Casa
        </h3>
        <div className="flex h-8 rounded-lg overflow-hidden">
          {casas.map((casa) => {
            const colors = CLS[casa.color] || CLS.emerald;
            return (
              <div key={casa.casa} className={`${colors.bar} flex items-center justify-center transition-all hover:opacity-80`}
                style={{ width: `${casa.porcentaje}%` }} title={`${casa.casa}: ${casa.porcentaje.toFixed(1)}%`}>
                {casa.porcentaje > 8 && <span className="text-xs text-white font-medium">{casa.porcentaje.toFixed(0)}%</span>}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
