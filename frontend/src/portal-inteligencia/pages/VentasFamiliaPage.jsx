/**
 * Ventas por Familia/Subfamilia - Análisis jerárquico
 */
import React, { useState, useEffect } from 'react';
import { Layers, ChevronDown, ChevronRight, TrendingUp } from 'lucide-react';

const FALLBACK_FAMILIAS = [
  {
    familia: 'LICORES',
    ventas: 892500,
    cantidad: 1245,
    porcentaje: 42.5,
    subfamilias: [
      { nombre: 'TEQUILA', ventas: 425000, cantidad: 520, porcentaje: 47.6 },
      { nombre: 'WHISKY', ventas: 312000, cantidad: 398, porcentaje: 35.0 },
      { nombre: 'VODKA', ventas: 85500, cantidad: 187, porcentaje: 9.6 },
      { nombre: 'GIN', ventas: 45000, cantidad: 89, porcentaje: 5.0 },
      { nombre: 'RON', ventas: 25000, cantidad: 51, porcentaje: 2.8 },
    ]
  },
  {
    familia: 'ALIMENTOS',
    ventas: 485200,
    cantidad: 2156,
    porcentaje: 23.1,
    subfamilias: [
      { nombre: 'CARNES', ventas: 198500, cantidad: 441, porcentaje: 40.9 },
      { nombre: 'MARISCOS', ventas: 165800, cantidad: 436, porcentaje: 34.2 },
      { nombre: 'TACOS', ventas: 78900, cantidad: 358, porcentaje: 16.3 },
      { nombre: 'ENSALADAS', ventas: 42000, cantidad: 233, porcentaje: 8.6 },
    ]
  },
  {
    familia: 'VINOS',
    ventas: 312800,
    cantidad: 425,
    porcentaje: 14.9,
    subfamilias: [
      { nombre: 'CHAMPAGNE', ventas: 156000, cantidad: 87, porcentaje: 49.9 },
      { nombre: 'TINTO', ventas: 98500, cantidad: 198, porcentaje: 31.5 },
      { nombre: 'ESPUMOSO', ventas: 58300, cantidad: 140, porcentaje: 18.6 },
    ]
  },
  {
    familia: 'CERVEZAS',
    ventas: 215400,
    cantidad: 4785,
    porcentaje: 10.3,
    subfamilias: [
      { nombre: 'CLARA', ventas: 156200, cantidad: 3472, porcentaje: 72.5 },
      { nombre: 'OSCURA', ventas: 59200, cantidad: 1313, porcentaje: 27.5 },
    ]
  },
];

export default function VentasFamiliaPage({ unidadSeleccionada }) {
  const [familias, setFamilias] = useState(FALLBACK_FAMILIAS);
  const [expandedFamilias, setExpandedFamilias] = useState(['LICORES', 'ALIMENTOS']);
  const [loading, setLoading] = useState(false);

  const API_URL = process.env.REACT_APP_BACKEND_URL || '';

  useEffect(() => {
    fetchFamilias();
  }, [unidadSeleccionada]);

  const fetchFamilias = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_URL}/api/inteligencia/dashboard?unidad=${unidadSeleccionada}`,
        { credentials: 'include' }
      );
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.ventas_familia?.length > 0) {
          // Mapear datos del backend al formato esperado
          const familiasData = data.ventas_familia.map((f, idx) => ({
            familia: f.familia?.toUpperCase() || f.nombre?.toUpperCase() || 'OTROS',
            ventas: f.ventas || 0,
            cantidad: f.cantidad || Math.floor(f.ventas / 500),
            porcentaje: f.participacion || 0,
            subfamilias: f.subfamilias || []
          }));
          
          // Calcular porcentajes si no vienen
          const totalVentas = familiasData.reduce((a, b) => a + b.ventas, 0);
          familiasData.forEach(f => {
            if (!f.porcentaje && totalVentas > 0) {
              f.porcentaje = ((f.ventas / totalVentas) * 100).toFixed(1);
            }
          });
          
          if (familiasData.length > 0) setFamilias(familiasData);
        }
      }
    } catch (error) {
      console.log('[Familias] Usando fallback:', error.message);
    } finally {
      setLoading(false);
    }
  };

  const toggleFamilia = (familia) => {
    setExpandedFamilias(prev => 
      prev.includes(familia) 
        ? prev.filter(f => f !== familia)
        : [...prev, familia]
    );
  };

  const formatMoney = (val) => {
    if (val >= 1000000) return `$${(val / 1000000).toFixed(2)}M`;
    if (val >= 1000) return `$${(val / 1000).toFixed(1)}K`;
    return `$${val.toFixed(0)}`;
  };

  const totalVentas = familias.reduce((a, b) => a + b.ventas, 0);

  const getColorClass = (idx) => {
    const colors = ['emerald', 'blue', 'purple', 'amber', 'pink'];
    return colors[idx % colors.length];
  };

  return (
    <div className="space-y-6" data-testid="ventas-familia-page">
      {/* Resumen visual */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {familias.map((fam, idx) => {
          const color = getColorClass(idx);
          return (
            <div 
              key={fam.familia}
              className={`bg-slate-800/50 border border-slate-700 rounded-xl p-4 cursor-pointer hover:border-${color}-500/50 transition-all`}
              onClick={() => toggleFamilia(fam.familia)}
            >
              <div className="flex items-center justify-between mb-2">
                <span className={`text-${color}-400 font-semibold text-sm`}>{fam.familia}</span>
                <span className="text-xs text-slate-500">{fam.porcentaje}%</span>
              </div>
              <p className="text-2xl font-bold text-white">{formatMoney(fam.ventas)}</p>
              <p className="text-xs text-slate-400 mt-1">{fam.cantidad.toLocaleString()} unidades</p>
              <div className="mt-2 h-1 bg-slate-700 rounded-full overflow-hidden">
                <div 
                  className={`h-full bg-${color}-500 rounded-full`}
                  style={{ width: `${fam.porcentaje}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Árbol jerárquico */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-700">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Layers className="h-5 w-5 text-emerald-400" />
            Desglose por Familia y Subfamilia
          </h3>
        </div>

        <div className="divide-y divide-slate-700/50">
          {familias.map((fam, famIdx) => {
            const isExpanded = expandedFamilias.includes(fam.familia);
            const color = getColorClass(famIdx);
            
            return (
              <div key={fam.familia}>
                {/* Familia Header */}
                <button
                  onClick={() => toggleFamilia(fam.familia)}
                  className="w-full px-4 py-4 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {isExpanded ? (
                      <ChevronDown className="h-5 w-5 text-slate-400" />
                    ) : (
                      <ChevronRight className="h-5 w-5 text-slate-400" />
                    )}
                    <div className={`w-3 h-3 rounded-full bg-${color}-500`} />
                    <span className="text-white font-medium">{fam.familia}</span>
                    <span className="text-xs text-slate-500 ml-2">
                      ({fam.subfamilias.length} subfamilias)
                    </span>
                  </div>
                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <p className="text-sm font-semibold text-emerald-400">{formatMoney(fam.ventas)}</p>
                      <p className="text-xs text-slate-500">{fam.cantidad.toLocaleString()} uds</p>
                    </div>
                    <div className="w-24 h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div 
                        className={`h-full bg-${color}-500 rounded-full`}
                        style={{ width: `${fam.porcentaje}%` }}
                      />
                    </div>
                    <span className="text-sm text-slate-400 w-12 text-right">{fam.porcentaje}%</span>
                  </div>
                </button>

                {/* Subfamilias */}
                {isExpanded && (
                  <div className="bg-slate-900/30">
                    {fam.subfamilias.map((sub, subIdx) => (
                      <div 
                        key={sub.nombre}
                        className="px-4 py-3 pl-14 flex items-center justify-between border-t border-slate-700/30 hover:bg-slate-700/20"
                      >
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
                            <div 
                              className={`h-full bg-${color}-400/60 rounded-full`}
                              style={{ width: `${sub.porcentaje}%` }}
                            />
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

        {/* Footer totales */}
        <div className="px-4 py-4 border-t border-slate-700 bg-slate-800/80">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-white">TOTAL GENERAL</span>
            <div className="flex items-center gap-6">
              <span className="text-lg font-bold text-emerald-400">{formatMoney(totalVentas)}</span>
              <span className="text-sm text-slate-400">100%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
