/**
 * Dashboard IA - Vista principal con KPIs consolidados (datos reales, sin mock).
 */
import React, { useState, useEffect } from 'react';
import {
  DollarSign, Users, Receipt, TrendingUp, Clock,
  Wine, Package, ArrowUpRight, ArrowDownRight, Loader2, CalendarDays,
  Sun, Sunset, Moon
} from 'lucide-react';
import { apiGet, ESTADO } from '../api/client';
import { EstadoVacio } from '../components/EstadoVacio';

const PERIODOS = [
  { value: 'dia', label: 'Día' },
  { value: 'semana', label: 'Semana' },
  { value: 'mes', label: 'Mes' },
  { value: 'anio', label: 'Año' },
];

const fmtTrend = (t) => (t === null || t === undefined) ? null : `${t >= 0 ? '+' : ''}${Number(t).toFixed(1)}%`;

const formatMoney = (value) => {
  const v = Number(value || 0);
  if (v >= 1000000) return `$${(v / 1000000).toFixed(2)}M`;
  if (v >= 1000) return `$${(v / 1000).toFixed(1)}K`;
  return `$${v.toFixed(2)}`;
};

const HORARIO_ICON = { Desayuno: Sun, Comida: Sunset, Cena: Moon };
const HORARIO_COLOR = { Desayuno: 'bg-amber-500', Comida: 'bg-orange-500', Cena: 'bg-indigo-500' };

export default function DashboardIA({ unidadSeleccionada, onNavigate }) {
  const [data, setData] = useState(null);
  const [estado, setEstado] = useState(ESTADO.CARGANDO);
  const [loading, setLoading] = useState(true);
  const [periodo, setPeriodo] = useState('mes');

  useEffect(() => {
    fetchDashboardData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unidadSeleccionada, periodo]);

  const fetchDashboardData = async () => {
    setLoading(true);
    const { estado: est, data: result } = await apiGet('/inteligencia/dashboard', {
      unidad: unidadSeleccionada, periodo,
    });
    if (est !== ESTADO.OK || !result || result.success === false) {
      setData(null);
      setEstado(est === ESTADO.OK ? ESTADO.ERROR : est);
      setLoading(false);
      return;
    }
    const kpis = result.kpis || {};
    setData({
      ventasTotales: Number(kpis.ventas_totales || 0),
      paxTotal: Number(kpis.pax_total || 0),
      chequesTotal: Number(kpis.cheques_total || 0),
      propinaTotal: Number(kpis.propinas_total || 0),
      chequePromedio: Number(kpis.cheque_promedio || 0),
      trends: result.kpis_trends || {},
      periodoLabel: result.filtros?.periodo_label || '',
      ventasHorario: result.ventas_horario || [],
      topProductos: (result.top_productos || []).map(p => ({ nombre: p.producto, ventas: p.ventas, cantidad: p.cantidad })),
      topCasas: result.casas_distribuidoras || [],
    });
    setEstado(ESTADO.OK);
    setLoading(false);
  };

  if (estado !== ESTADO.OK && !data) {
    return <EstadoVacio estado={estado} testid="dashboard-ia-estado" />;
  }

  const totalHorario = (data.ventasHorario || []).reduce((a, b) => a + Number(b.ventas || 0), 0) || 1;

  const kpiCards = [
    { title: 'Ventas Totales', value: formatMoney(data.ventasTotales), icon: DollarSign, color: 'emerald', trend: data.trends?.ventas_totales },
    { title: 'PAX Total', value: data.paxTotal.toLocaleString(), icon: Users, color: 'blue', trend: data.trends?.pax_total },
    { title: 'Cheques Emitidos', value: data.chequesTotal.toLocaleString(), icon: Receipt, color: 'purple', trend: data.trends?.cheques_total },
    { title: 'Propinas', value: formatMoney(data.propinaTotal), icon: TrendingUp, color: 'amber', trend: data.trends?.propinas_total },
  ];

  return (
    <div className="space-y-6" data-testid="dashboard-ia">
      {/* Periodo Selector + Etiqueta de fecha */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-col gap-2">
          <div className="flex gap-2" data-testid="periodo-selector">
            {PERIODOS.map((p) => (
              <button
                key={p.value}
                data-testid={`periodo-btn-${p.value}`}
                onClick={() => setPeriodo(p.value)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  periodo === p.value ? 'bg-emerald-500 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
          {data.periodoLabel && (
            <div className="flex items-center gap-2 text-sm text-slate-300" data-testid="periodo-label">
              <CalendarDays className="h-4 w-4 text-emerald-400" />
              <span>Mostrando: <span className="font-semibold text-white">{data.periodoLabel}</span></span>
            </div>
          )}
        </div>
        {loading && (
          <div className="flex items-center gap-2 text-slate-400">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-sm">Actualizando...</span>
          </div>
        )}
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiCards.map((kpi, idx) => {
          const Icon = kpi.icon;
          const trendStr = fmtTrend(kpi.trend);
          const trendUp = (kpi.trend ?? 0) >= 0;
          return (
            <div key={idx} data-testid={`kpi-card-${idx}`}
              className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-xl p-5 hover:border-slate-600 transition-all">
              <div className="flex items-start justify-between">
                <div className={`p-2 rounded-lg bg-${kpi.color}-500/20`}>
                  <Icon className={`h-5 w-5 text-${kpi.color}-400`} />
                </div>
                {trendStr && (
                  <div className={`flex items-center gap-1 text-xs ${trendUp ? 'text-emerald-400' : 'text-red-400'}`}>
                    {trendUp ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                    {trendStr}
                  </div>
                )}
              </div>
              <div className="mt-3">
                <p className="text-2xl font-bold text-white" data-testid={`kpi-value-${idx}`}>{kpi.value}</p>
                <p className="text-sm text-slate-400">{kpi.title}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Ventas por Horario */}
        <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-xl p-5" data-testid="dashboard-horario">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Clock className="h-5 w-5 text-emerald-400" /> Ventas por Horario
            </h3>
            <button onClick={() => onNavigate('horarios')} className="text-xs text-emerald-400 hover:text-emerald-300">Ver más →</button>
          </div>
          {(data.ventasHorario || []).length === 0 ? (
            <EstadoVacio estado={ESTADO.SIN_DATOS} testid="dashboard-horario-vacio" compacto />
          ) : (
            <div className="space-y-4">
              {data.ventasHorario.map((h, idx) => {
                const Icon = HORARIO_ICON[h.horario] || Clock;
                return (
                  <div key={idx} className="flex items-center gap-4">
                    <span className="p-2 rounded-lg bg-slate-700/50"><Icon className="h-5 w-5 text-amber-400" /></span>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-white">{h.horario}</span>
                        <span className="text-sm font-bold text-emerald-400">{formatMoney(h.ventas)}</span>
                      </div>
                      <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                        <div className={`h-full ${HORARIO_COLOR[h.horario] || 'bg-emerald-500'} rounded-full transition-all`}
                          style={{ width: `${(Number(h.ventas) / totalHorario) * 100}%` }} />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Top Productos */}
        <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-xl p-5" data-testid="dashboard-top-productos">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Package className="h-5 w-5 text-blue-400" /> Top Productos
            </h3>
            <button onClick={() => onNavigate('productos')} className="text-xs text-emerald-400 hover:text-emerald-300">Ver más →</button>
          </div>
          {(data.topProductos || []).length === 0 ? (
            <EstadoVacio estado={ESTADO.SIN_DATOS} testid="dashboard-top-productos-vacio" compacto />
          ) : (
            <div className="space-y-3">
              {data.topProductos.map((prod, idx) => (
                <div key={idx} className="flex items-center justify-between py-2 border-b border-slate-700/50 last:border-0">
                  <div className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded-full bg-slate-700 flex items-center justify-center text-xs text-slate-300">{idx + 1}</span>
                    <div>
                      <p className="text-sm font-medium text-white">{prod.nombre}</p>
                      <p className="text-xs text-slate-500">{Number(prod.cantidad || 0).toLocaleString()} unidades</p>
                    </div>
                  </div>
                  <span className="text-sm font-semibold text-emerald-400">{formatMoney(prod.ventas)}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Top Casas/Distribuidores */}
        <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-xl p-5" data-testid="dashboard-casas">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Wine className="h-5 w-5 text-purple-400" /> Casas / Distribuidores
            </h3>
            <button onClick={() => onNavigate('casas')} className="text-xs text-emerald-400 hover:text-emerald-300">Ver más →</button>
          </div>
          {(data.topCasas || []).length === 0 ? (
            <EstadoVacio estado={ESTADO.SIN_DATOS} testid="dashboard-casas-vacio" compacto />
          ) : (
            <div className="space-y-3">
              {data.topCasas.map((casa, idx) => (
                <div key={idx} className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-white">{casa.casa}</span>
                    <span className="text-sm text-slate-400">{Number(casa.participacion || 0).toFixed(1)}%</span>
                  </div>
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"
                      style={{ width: `${casa.participacion}%` }} />
                  </div>
                  <p className="text-xs text-emerald-400">{formatMoney(casa.ventas)}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Cheque Promedio Card */}
      <div className="bg-gradient-to-r from-emerald-500/20 to-blue-500/20 border border-emerald-500/30 rounded-xl p-6" data-testid="dashboard-cheque-promedio">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-slate-400 text-sm">Cheque Promedio</p>
            <p className="text-3xl font-bold text-white mt-1">${data.chequePromedio.toLocaleString('es-MX', { maximumFractionDigits: 2 })} MXN</p>
          </div>
          <div className="text-right">
            <p className="text-emerald-400 text-sm flex items-center gap-1 justify-end">
              <CalendarDays className="h-4 w-4" />
              {data.periodoLabel || 'Periodo actual'}
            </p>
            <p className="text-slate-500 text-xs mt-1">Ventas ÷ cheques</p>
          </div>
        </div>
      </div>
    </div>
  );
}
