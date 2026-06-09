/**
 * Ventas por Horario - Desayuno / Comida / Cena (datos reales, sin mock).
 * Fuente: /api/inteligencia/dashboard -> ventas_horario (agregado por ticket).
 */
import React, { useState, useEffect } from 'react';
import { Clock, Sun, Sunset, Moon, Users, DollarSign } from 'lucide-react';
import { apiGet, ESTADO } from '../api/client';
import { EstadoVacio } from '../components/EstadoVacio';

const META = {
  Desayuno: { icon: Sun, horario: '7:00 - 12:59', gradient: 'from-amber-500 to-orange-500', bg: 'bg-amber-500/20 border-amber-500/30 text-amber-400' },
  Comida: { icon: Sunset, horario: '13:00 - 18:59', gradient: 'from-orange-500 to-red-500', bg: 'bg-orange-500/20 border-orange-500/30 text-orange-400' },
  Cena: { icon: Moon, horario: '19:00 - 23:59', gradient: 'from-indigo-500 to-purple-500', bg: 'bg-indigo-500/20 border-indigo-500/30 text-indigo-400' },
};

export default function VentasHorarioPage({ unidadSeleccionada }) {
  const [horarios, setHorarios] = useState([]);
  const [estado, setEstado] = useState(ESTADO.CARGANDO);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    fetchHorarios();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unidadSeleccionada]);

  const fetchHorarios = async () => {
    setEstado(ESTADO.CARGANDO);
    const { estado: est, data } = await apiGet('/inteligencia/dashboard', { unidad: unidadSeleccionada, periodo: 'mes' });
    if (est !== ESTADO.OK || !data || data.success === false) {
      setHorarios([]);
      setEstado(est === ESTADO.OK ? ESTADO.ERROR : est);
      return;
    }
    const lista = (data.ventas_horario || []).map(h => ({
      nombre: h.horario,
      ventas: Number(h.ventas || 0),
      pax: Number(h.pax || 0),
      cheques: Number(h.cheques || 0),
      propinas: Number(h.propinas || 0),
      ticketPromedio: Number(h.ticket_promedio || 0),
    }));
    setHorarios(lista);
    setEstado(lista.length ? ESTADO.OK : ESTADO.SIN_DATOS);
  };

  const formatMoney = (val) => {
    const v = Number(val || 0);
    if (v >= 1000000) return `$${(v / 1000000).toFixed(2)}M`;
    if (v >= 1000) return `$${(v / 1000).toFixed(1)}K`;
    return `$${v.toFixed(0)}`;
  };

  if (estado !== ESTADO.OK) {
    return (
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl" data-testid="ventas-horario-page">
        <EstadoVacio estado={estado} testid="ventas-horario-estado" />
      </div>
    );
  }

  const totalVentas = horarios.reduce((a, b) => a + b.ventas, 0) || 1;
  const sel = horarios.find(h => h.nombre === selected);

  return (
    <div className="space-y-6" data-testid="ventas-horario-page">
      {/* Cards principales por horario */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {horarios.map((periodo) => {
          const meta = META[periodo.nombre] || { icon: Clock, horario: '', gradient: 'from-slate-500 to-slate-600', bg: 'bg-slate-500/20' };
          const Icon = meta.icon;
          const porcentaje = ((periodo.ventas / totalVentas) * 100).toFixed(1);
          const isSelected = selected === periodo.nombre;
          return (
            <div key={periodo.nombre} onClick={() => setSelected(isSelected ? null : periodo.nombre)}
              data-testid={`horario-card-${periodo.nombre.toLowerCase()}`}
              className={`relative overflow-hidden rounded-2xl cursor-pointer transition-all transform hover:scale-[1.02] ${isSelected ? 'ring-2 ring-emerald-400' : ''}`}>
              <div className={`absolute inset-0 bg-gradient-to-br ${meta.gradient} opacity-20`} />
              <div className="relative p-6 bg-slate-800/80 backdrop-blur">
                <div className="flex items-start justify-between mb-4">
                  <div className={`p-3 rounded-xl ${meta.bg}`}><Icon className="h-8 w-8" /></div>
                  <div className="text-right">
                    <span className="text-3xl font-bold text-white">{porcentaje}%</span>
                    <p className="text-xs text-slate-400">del total</p>
                  </div>
                </div>
                <h3 className="text-xl font-bold text-white mb-1">{periodo.nombre}</h3>
                <p className="text-sm text-slate-400 mb-4">{meta.horario}</p>
                <div className="mb-4"><p className="text-3xl font-bold text-emerald-400">{formatMoney(periodo.ventas)}</p></div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-700/50 rounded-lg p-3">
                    <div className="flex items-center gap-2 text-slate-400 mb-1"><Users className="h-4 w-4" /><span className="text-xs">PAX</span></div>
                    <p className="text-lg font-semibold text-white">{periodo.pax.toLocaleString()}</p>
                  </div>
                  <div className="bg-slate-700/50 rounded-lg p-3">
                    <div className="flex items-center gap-2 text-slate-400 mb-1"><DollarSign className="h-4 w-4" /><span className="text-xs">Cheque Prom.</span></div>
                    <p className="text-lg font-semibold text-white">${periodo.ticketPromedio.toLocaleString('es-MX', { maximumFractionDigits: 0 })}</p>
                  </div>
                </div>
                <div className="mt-4 h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div className={`h-full bg-gradient-to-r ${meta.gradient} rounded-full`} style={{ width: `${porcentaje}%` }} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Detalle del periodo seleccionado (estadísticas reales) */}
      {sel && (
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6" data-testid="horario-detalle">
          <h3 className="text-lg font-semibold text-white mb-4">Detalle — {sel.nombre}</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-slate-700/30 rounded-lg">
              <p className="text-2xl font-bold text-white">{sel.cheques.toLocaleString()}</p>
              <p className="text-xs text-slate-400">Cheques Emitidos</p>
            </div>
            <div className="text-center p-4 bg-slate-700/30 rounded-lg">
              <p className="text-2xl font-bold text-white">{sel.pax.toLocaleString()}</p>
              <p className="text-xs text-slate-400">PAX Total</p>
            </div>
            <div className="text-center p-4 bg-slate-700/30 rounded-lg">
              <p className="text-2xl font-bold text-blue-400">{formatMoney(sel.propinas)}</p>
              <p className="text-xs text-slate-400">Propinas</p>
            </div>
            <div className="text-center p-4 bg-slate-700/30 rounded-lg">
              <p className="text-2xl font-bold text-emerald-400">${sel.ticketPromedio.toLocaleString('es-MX', { maximumFractionDigits: 0 })}</p>
              <p className="text-xs text-slate-400">Cheque Promedio</p>
            </div>
          </div>
        </div>
      )}

      {/* Comparativa rápida */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Comparativa de Horarios</h3>
        <div className="space-y-4">
          {horarios.map((periodo) => {
            const meta = META[periodo.nombre] || { gradient: 'from-slate-500 to-slate-600' };
            const porcentaje = (periodo.ventas / totalVentas) * 100;
            return (
              <div key={periodo.nombre} className="flex items-center gap-4">
                <div className="w-24 text-sm text-slate-400">{periodo.nombre}</div>
                <div className="flex-1 h-8 bg-slate-700 rounded-lg overflow-hidden relative">
                  <div className={`h-full bg-gradient-to-r ${meta.gradient} rounded-lg transition-all`} style={{ width: `${porcentaje}%` }} />
                  <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-white font-medium">{formatMoney(periodo.ventas)}</span>
                </div>
                <div className="w-16 text-right text-sm text-slate-400">{porcentaje.toFixed(1)}%</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
