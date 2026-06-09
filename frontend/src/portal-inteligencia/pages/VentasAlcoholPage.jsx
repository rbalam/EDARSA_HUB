/**
 * Reporte de Bebidas: con/sin alcohol y por grado de alcohol (datos reales).
 * Fuente: /api/inteligencia/alcohol (detalle + Catálogo Enriquecido).
 */
import React, { useState, useEffect } from 'react';
import { Wine, Droplet } from 'lucide-react';
import { apiGet, ESTADO } from '../api/client';
import { EstadoVacio } from '../components/EstadoVacio';
import { PeriodoSelector } from '../components/PeriodoSelector';
import { ExportButtons } from '../components/ExportButtons';
import { usePeriodo } from '../utils/usePeriodo';

const money = (v) => `$${Number(v || 0).toLocaleString('es-MX', { maximumFractionDigits: 0 })}`;

export default function VentasAlcoholPage({ unidadSeleccionada, periodo = 'mes' }) {
  const [data, setData] = useState(null);
  const [estado, setEstado] = useState(ESTADO.CARGANDO);
  const { periodo: periodoLocal, setPeriodo: setPeriodoLocal, rangoInicio, rangoFin, onRango, listo, params } = usePeriodo(periodo);

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unidadSeleccionada, periodoLocal, rangoInicio, rangoFin]);

  const fetchData = async () => {
    if (!listo) return;
    setEstado(ESTADO.CARGANDO);
    const { estado: est, data: d } = await apiGet('/inteligencia/alcohol', { unidad: unidadSeleccionada, ...params });
    if (est !== ESTADO.OK || !d || d.success === false) {
      setData(null); setEstado(est === ESTADO.OK ? ESTADO.ERROR : est); return;
    }
    setData(d);
    const hay = (d.con_alcohol?.ventas || 0) + (d.sin_alcohol?.ventas || 0) > 0;
    setEstado(hay ? ESTADO.OK : ESTADO.SIN_DATOS);
  };

  if (estado !== ESTADO.OK) {
    return (
      <div className="space-y-4" data-testid="ventas-alcohol-page">
        <PeriodoSelector periodo={periodoLocal} onChange={setPeriodoLocal}
          rangoInicio={rangoInicio} rangoFin={rangoFin} onRango={onRango} />
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl">
          <EstadoVacio estado={estado} testid="ventas-alcohol-estado" />
        </div>
      </div>
    );
  }

  const con = data.con_alcohol, sin = data.sin_alcohol, grados = data.por_grado || [];
  const periodoLabel = data.filtros?.periodo_label || '';
  const meta = `${unidadSeleccionada === 'todas' ? 'Consolidado' : unidadSeleccionada} · ${periodoLabel}`;
  const maxGrado = Math.max(...grados.map(g => g.ventas), 1);

  const exportRows = [
    { tipo: 'Con alcohol', ventas: con.ventas, cantidad: con.cantidad, participacion: con.participacion },
    { tipo: 'Sin alcohol', ventas: sin.ventas, cantidad: sin.cantidad, participacion: sin.participacion },
    ...grados.map(g => ({ tipo: `Grado ${g.rango}`, ventas: g.ventas, cantidad: g.cantidad, participacion: g.participacion })),
  ];
  const exportCols = [
    { key: 'tipo', label: 'Tipo' }, { key: 'ventas', label: 'Ventas' },
    { key: 'cantidad', label: 'Cantidad' }, { key: 'participacion', label: '% Part.' },
  ];

  return (
    <div className="space-y-6" data-testid="ventas-alcohol-page">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <PeriodoSelector periodo={periodoLocal} onChange={setPeriodoLocal} periodoLabel={periodoLabel}
          rangoInicio={rangoInicio} rangoFin={rangoFin} onRango={onRango} />
        <ExportButtons filename="reporte_alcohol" title="Reporte de Bebidas (Alcohol)"
          columns={exportCols} rows={exportRows} meta={meta} testid="alcohol-export" />
      </div>

      {/* Con vs Sin alcohol */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-5" data-testid="alcohol-con">
          <div className="flex items-center justify-between mb-2">
            <span className="flex items-center gap-2 text-amber-400 font-semibold"><Wine className="h-5 w-5" /> Con alcohol</span>
            <span className="text-2xl font-bold text-amber-400">{con.participacion}%</span>
          </div>
          <p className="text-3xl font-bold text-white">{money(con.ventas)}</p>
          <p className="text-xs text-slate-400 mt-1">{Number(con.cantidad).toLocaleString()} unidades</p>
        </div>
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-5" data-testid="alcohol-sin">
          <div className="flex items-center justify-between mb-2">
            <span className="flex items-center gap-2 text-blue-400 font-semibold"><Droplet className="h-5 w-5" /> Sin alcohol</span>
            <span className="text-2xl font-bold text-blue-400">{sin.participacion}%</span>
          </div>
          <p className="text-3xl font-bold text-white">{money(sin.ventas)}</p>
          <p className="text-xs text-slate-400 mt-1">{Number(sin.cantidad).toLocaleString()} unidades</p>
        </div>
      </div>

      {/* Por grado */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5" data-testid="alcohol-grados">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Droplet className="h-5 w-5 text-amber-400" /> Ventas por grado de alcohol
        </h3>
        {grados.length === 0 ? (
          <EstadoVacio estado={ESTADO.SIN_DATOS} testid="alcohol-grados-vacio" compacto />
        ) : (
          <div className="space-y-4">
            {grados.map((g, idx) => (
              <div key={idx} className="flex items-center gap-4">
                <span className="text-sm text-slate-300 w-20">{g.rango}</span>
                <div className="flex-1 h-3 bg-slate-700 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-amber-500 to-rose-500 rounded-full" style={{ width: `${(g.ventas / maxGrado) * 100}%` }} />
                </div>
                <span className="text-sm font-semibold text-emerald-400 w-24 text-right">{money(g.ventas)}</span>
                <span className="text-xs text-slate-500 w-16 text-right">{Number(g.cantidad).toLocaleString()} u</span>
                <span className="text-xs text-slate-400 w-14 text-right">{g.participacion}%</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
