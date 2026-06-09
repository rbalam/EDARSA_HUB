/**
 * Ventas por Familia/Subfamilia - Análisis jerárquico (datos reales, sin mock).
 * Fuente: /api/inteligencia/familias (Comercial_Inteligencia_VentasDetalleProducto).
 */
import React, { useState, useEffect } from 'react';
import { Layers, ChevronDown, ChevronRight } from 'lucide-react';
import { apiGet, ESTADO } from '../api/client';
import { EstadoVacio } from '../components/EstadoVacio';

export default function VentasFamiliaPage({ unidadSeleccionada }) {
  const [familias, setFamilias] = useState([]);
  const [estado, setEstado] = useState(ESTADO.CARGANDO);
  const [expandedFamilias, setExpandedFamilias] = useState([]);

  useEffect(() => {
    fetchFamilias();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unidadSeleccionada]);

  const fetchFamilias = async () => {
    setEstado(ESTADO.CARGANDO);
    const { estado: est, data } = await apiGet('/inteligencia/familias', { unidad: unidadSeleccionada });
    if (est !== ESTADO.OK || !data || data.success === false) {
      setFamilias([]);
      setEstado(est === ESTADO.OK ? ESTADO.ERROR : est);
      return;
    }
    const lista = (data.ventas_familia || []).map(f => ({
      familia: (f.familia || 'OTROS').toUpperCase(),
      ventas: Number(f.ventas || 0),
      cantidad: Number(f.cantidad || 0),
      porcentaje: Number(f.porcentaje || 0),
      subfamilias: (f.subfamilias || []).map(s => ({
        nombre: s.nombre, ventas: Number(s.ventas || 0),
        cantidad: Number(s.cantidad || 0), porcentaje: Number(s.porcentaje || 0),
      })),
    }));
    setFamilias(lista);
    setExpandedFamilias(lista.slice(0, 2).map(f => f.familia));
    setEstado(lista.length ? ESTADO.OK : ESTADO.SIN_DATOS);
  };

  const toggleFamilia = (familia) => {
    setExpandedFamilias(prev => prev.includes(familia) ? prev.filter(f => f !== familia) : [...prev, familia]);
  };

  const formatMoney = (val) => {
    const v = Number(val || 0);
    if (v >= 1000000) return `$${(v / 1000000).toFixed(2)}M`;
    if (v >= 1000) return `$${(v / 1000).toFixed(1)}K`;
    return `$${v.toFixed(0)}`;
  };

  const totalVentas = familias.reduce((a, b) => a + b.ventas, 0);
  const getColorClass = (idx) => ['emerald', 'blue', 'purple', 'amber', 'pink'][idx % 5];

  if (estado !== ESTADO.OK) {
    return (
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl" data-testid="ventas-familia-page">
        <EstadoVacio estado={estado} testid="ventas-familia-estado" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="ventas-familia-page">
      {/* Resumen visual (top 4) */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {familias.slice(0, 4).map((fam, idx) => {
          const color = getColorClass(idx);
          return (
            <div key={fam.familia}
              className={`bg-slate-800/50 border border-slate-700 rounded-xl p-4 cursor-pointer hover:border-${color}-500/50 transition-all`}
              onClick={() => toggleFamilia(fam.familia)}>
              <div className="flex items-center justify-between mb-2">
                <span className={`text-${color}-400 font-semibold text-sm`}>{fam.familia}</span>
                <span className="text-xs text-slate-500">{fam.porcentaje}%</span>
              </div>
              <p className="text-2xl font-bold text-white">{formatMoney(fam.ventas)}</p>
              <p className="text-xs text-slate-400 mt-1">{fam.cantidad.toLocaleString()} unidades</p>
              <div className="mt-2 h-1 bg-slate-700 rounded-full overflow-hidden">
                <div className={`h-full bg-${color}-500 rounded-full`} style={{ width: `${fam.porcentaje}%` }} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Árbol jerárquico */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-700">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Layers className="h-5 w-5 text-emerald-400" /> Desglose por Familia y Subfamilia
          </h3>
        </div>
        <div className="divide-y divide-slate-700/50">
          {familias.map((fam, famIdx) => {
            const isExpanded = expandedFamilias.includes(fam.familia);
            const color = getColorClass(famIdx);
            return (
              <div key={fam.familia}>
                <button onClick={() => toggleFamilia(fam.familia)}
                  className="w-full px-4 py-4 flex items-center justify-between hover:bg-slate-700/30 transition-colors">
                  <div className="flex items-center gap-3">
                    {isExpanded ? <ChevronDown className="h-5 w-5 text-slate-400" /> : <ChevronRight className="h-5 w-5 text-slate-400" />}
                    <div className={`w-3 h-3 rounded-full bg-${color}-500`} />
                    <span className="text-white font-medium">{fam.familia}</span>
                    <span className="text-xs text-slate-500 ml-2">({fam.subfamilias.length} subfamilias)</span>
                  </div>
                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <p className="text-sm font-semibold text-emerald-400">{formatMoney(fam.ventas)}</p>
                      <p className="text-xs text-slate-500">{fam.cantidad.toLocaleString()} uds</p>
                    </div>
                    <div className="w-24 h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div className={`h-full bg-${color}-500 rounded-full`} style={{ width: `${fam.porcentaje}%` }} />
                    </div>
                    <span className="text-sm text-slate-400 w-12 text-right">{fam.porcentaje}%</span>
                  </div>
                </button>
                {isExpanded && (
                  <div className="bg-slate-900/30">
                    {fam.subfamilias.map((sub) => (
                      <div key={sub.nombre} className="px-4 py-3 pl-14 flex items-center justify-between border-t border-slate-700/30 hover:bg-slate-700/20">
                        <div className="flex items-center gap-3">
                          <div className={`w-2 h-2 rounded-full bg-${color}-400/60`} />
                          <span className="text-sm text-slate-300">{sub.nombre}</span>
                        </div>
                        <div className="flex items-center gap-6">
                          <div className="text-right">
                            <p className="text-sm text-white">{formatMoney(sub.ventas)}</p>
                            <p className="text-xs text-slate-500">{sub.cantidad.toLocaleString()} uds</p>
                          </div>
                          <div className="w-24 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                            <div className={`h-full bg-${color}-400/60 rounded-full`} style={{ width: `${sub.porcentaje}%` }} />
                          </div>
                          <span className="text-xs text-slate-500 w-12 text-right">{sub.porcentaje}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
        <div className="px-4 py-4 border-t border-slate-700 bg-slate-800/80">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-white">TOTAL GENERAL</span>
            <span className="text-lg font-bold text-emerald-400">{formatMoney(totalVentas)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
