/**
 * Dashboard IA - Vista principal con KPIs canónicos (datos reales, sin mock).
 * KPIs: Ventas, PAX Promedio (ventas÷PAX) y Cheque Promedio (ventas÷cheques)
 * en la fila superior. Drill-down a tickets y export Excel/PDF.
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  DollarSign, Users, Receipt, TrendingUp, Clock,
  Wine, Package, ArrowUpRight, ArrowDownRight, Loader2,
  Sun, Sunset, Moon, Search,
} from 'lucide-react';
import { apiGet, ESTADO } from '../api/client';
import { EstadoVacio } from '../components/EstadoVacio';
import { PeriodoSelector } from '../components/PeriodoSelector';
import { ExportButtons } from '../components/ExportButtons';
import { TicketDrilldownModal } from '../components/TicketDrilldownModal';
import { SyncControlPanel } from '../components/SyncControlPanel';

const fmtTrend = (t) => (t === null || t === undefined) ? null : `${t >= 0 ? '+' : ''}${Number(t).toFixed(1)}%`;

const formatMoney = (value) => {
  const v = Number(value || 0);
  if (v >= 1000000) return `$${(v / 1000000).toFixed(2)}M`;
  if (v >= 1000) return `$${(v / 1000).toFixed(1)}K`;
  return `$${v.toFixed(2)}`;
};
const money2 = (v) => `$${Number(v || 0).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const HORARIO_ICON = { Desayuno: Sun, Comida: Sunset, Cena: Moon };
const HORARIO_COLOR = { Desayuno: 'bg-amber-500', Comida: 'bg-orange-500', Cena: 'bg-indigo-500' };

// Mapa estático de clases (evita el purgado de Tailwind con clases dinámicas).
const COLOR_CLS = {
  emerald: { icon: 'text-emerald-400', iconBg: 'bg-emerald-500/20', bigBorder: 'border-emerald-500/30', bigBg: 'bg-emerald-500/5', hover: 'hover:border-emerald-500/60' },
  cyan: { icon: 'text-cyan-400', iconBg: 'bg-cyan-500/20', bigBorder: 'border-cyan-500/30', bigBg: 'bg-cyan-500/5', hover: 'hover:border-cyan-500/60' },
  violet: { icon: 'text-violet-400', iconBg: 'bg-violet-500/20', bigBorder: 'border-violet-500/30', bigBg: 'bg-violet-500/5', hover: 'hover:border-violet-500/60' },
  blue: { icon: 'text-blue-400', iconBg: 'bg-blue-500/20', bigBorder: 'border-blue-500/30', bigBg: 'bg-blue-500/5', hover: 'hover:border-blue-500/60' },
  purple: { icon: 'text-purple-400', iconBg: 'bg-purple-500/20', bigBorder: 'border-purple-500/30', bigBg: 'bg-purple-500/5', hover: 'hover:border-purple-500/60' },
  amber: { icon: 'text-amber-400', iconBg: 'bg-amber-500/20', bigBorder: 'border-amber-500/30', bigBg: 'bg-amber-500/5', hover: 'hover:border-amber-500/60' },
};

export default function DashboardIA({ unidadSeleccionada, onNavigate, periodo = 'mes', setPeriodo }) {
  const [data, setData] = useState(null);
  const [estado, setEstado] = useState(ESTADO.CARGANDO);
  const [loading, setLoading] = useState(true);
  const [periodoLocal, setPeriodoLocal] = useState(periodo);
  const [drill, setDrill] = useState(false);
  const [drillKpi, setDrillKpi] = useState(null);
  const reqRef = useRef(0);
  const [rangoInicio, setRangoInicio] = useState('');
  const [rangoFin, setRangoFin] = useState('');
  const onRango = (i, f) => { setRangoInicio(i || ''); setRangoFin(f || ''); };

  const periodoActivo = setPeriodo ? periodo : periodoLocal;
  const cambiarPeriodo = setPeriodo || setPeriodoLocal;
  const esCustom = periodoActivo === 'personalizado' && !!rangoInicio && !!rangoFin;
  const periodoParams = esCustom ? { fecha_inicio: rangoInicio, fecha_fin: rangoFin } : { periodo: periodoActivo };
  const listoP = periodoActivo !== 'personalizado' || esCustom;

  useEffect(() => {
    fetchDashboardData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unidadSeleccionada, periodoActivo, rangoInicio, rangoFin]);

  const fetchDashboardData = async () => {
    if (!listoP) return;
    const myReq = ++reqRef.current;
    setLoading(true);
    const { estado: est, data: result } = await apiGet('/inteligencia/dashboard', {
      unidad: unidadSeleccionada, ...periodoParams,
    });
    if (myReq !== reqRef.current) return;  // respuesta obsoleta: ignorar (evita carrera)
    if (est !== ESTADO.OK || !result || result.success === false) {
      setData(null);
      setEstado(est === ESTADO.OK ? ESTADO.ERROR : est);
      setLoading(false);
      return;
    }
    const kpis = result.kpis || {};
    const kpisDia = result.ventas_dia_actual?.kpis || {};
    setData({
      ventasTotales: Number(kpis.ventas_totales || 0),
      paxTotal: Number(kpis.pax_total || 0),
      chequesTotal: Number(kpis.cheques_total || 0),
      propinaTotal: Number(kpis.propinas_total || 0),
      chequePromedio: Number(kpis.cheque_promedio || 0),
      paxPromedio: Number(kpis.pax_promedio || 0),
      ventasDia: {
        ventas: Number(kpisDia.ventas_totales || 0),
        propinas: Number(kpisDia.propinas_total || 0),
        cheques: Number(kpisDia.cheques_total || 0),
        pax: Number(kpisDia.pax_total || 0),
      },
      trends: result.kpis_trends || {},
      periodoLabel: result.filtros?.periodo_label || '',
      fechaInicio: result.filtros?.fecha_inicio || '',
      fechaFin: result.filtros?.fecha_fin || '',
      ventasHorario: result.ventas_horario || [],
      topProductos: (result.top_productos || []).map(p => ({ nombre: p.producto, ventas: p.ventas, cantidad: p.cantidad })),
      topCasas: result.casas_distribuidoras || [],
    });
    setEstado(ESTADO.OK);
    setLoading(false);
  };

  if (estado !== ESTADO.OK && !data) {
    return (
      <div className="space-y-4" data-testid="dashboard-ia">
        <PeriodoSelector periodo={periodoActivo} onChange={cambiarPeriodo}
          rangoInicio={rangoInicio} rangoFin={rangoFin} onRango={onRango} />
        <EstadoVacio estado={estado} testid="dashboard-ia-estado" />
      </div>
    );
  }

  const totalHorario = (data.ventasHorario || []).reduce((a, b) => a + Number(b.ventas || 0), 0) || 1;

  // Fila superior: Ventas + los 2 promedios canónicos (lo que pidió el usuario arriba).
  const kpiPrincipales = [
    { title: 'Acumulado cerrado', value: formatMoney(data.ventasTotales), rawValue: data.ventasTotales, metric: 'ventas', drillTitle: 'Ventas · Tickets del período', icon: DollarSign, color: 'emerald', trend: data.trends?.ventas_totales },
    { title: 'PAX Promedio', sub: 'Ventas ÷ PAX', value: money2(data.paxPromedio), rawValue: data.paxPromedio, metric: 'pax_promedio', drillTitle: 'PAX Promedio · Consumo por persona', icon: Users, color: 'cyan', trend: null },
    { title: 'Cheque Promedio', sub: 'Ventas ÷ cheques', value: money2(data.chequePromedio), rawValue: data.chequePromedio, metric: 'cheque_promedio', drillTitle: 'Cheque Promedio · Distribución por ticket', icon: Receipt, color: 'violet', trend: null },
  ];
  const kpiSecundarios = [
    { title: 'PAX Total', value: data.paxTotal.toLocaleString(), rawValue: data.paxTotal, metric: 'pax_total', drillTitle: 'PAX Total · Comensales por ticket', icon: Users, color: 'blue', trend: data.trends?.pax_total },
    { title: 'Cheques Emitidos', value: data.chequesTotal.toLocaleString(), rawValue: data.chequesTotal, metric: 'cheques', drillTitle: 'Cheques Emitidos · Relación de tickets', icon: Receipt, color: 'purple', trend: data.trends?.cheques_total },
    { title: 'Propinas', value: formatMoney(data.propinaTotal), rawValue: data.propinaTotal, metric: 'propinas', drillTitle: 'Propinas · Detalle por ticket', icon: TrendingUp, color: 'amber', trend: data.trends?.propinas_total },
  ];

  // Datos para export del resumen
  const exportRows = [
    { kpi: 'Ventas Totales', valor: data.ventasTotales },
    { kpi: 'PAX Promedio (ventas/PAX)', valor: data.paxPromedio },
    { kpi: 'Cheque Promedio (ventas/cheques)', valor: data.chequePromedio },
    { kpi: 'PAX Total', valor: data.paxTotal },
    { kpi: 'Cheques Emitidos', valor: data.chequesTotal },
    { kpi: 'Propinas', valor: data.propinaTotal },
  ];
  const meta = `${unidadSeleccionada === 'todas' ? 'Consolidado' : unidadSeleccionada} · ${data.periodoLabel}`;

  const KpiCard = ({ kpi, idx, big }) => {
    const Icon = kpi.icon;
    const c = COLOR_CLS[kpi.color] || COLOR_CLS.emerald;
    const trendStr = fmtTrend(kpi.trend);
    const trendUp = (kpi.trend ?? 0) >= 0;
    return (
      <button onClick={() => { setDrillKpi(kpi); setDrill(true); }} data-testid={`kpi-card-${idx}`}
        className={`text-left w-full bg-slate-800/50 backdrop-blur border rounded-xl p-5 ${c.hover} transition-all ${big ? `${c.bigBorder} ${c.bigBg}` : 'border-slate-700'}`}>
        <div className="flex items-start justify-between">
          <div className={`p-2 rounded-lg ${c.iconBg}`}>
            <Icon className={`h-5 w-5 ${c.icon}`} />
          </div>
          {trendStr && (
            <div className={`flex items-center gap-1 text-xs ${trendUp ? 'text-emerald-400' : 'text-red-400'}`}>
              {trendUp ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
              {trendStr}
            </div>
          )}
        </div>
        <div className="mt-3">
          <p className={`font-bold text-white ${big ? 'text-3xl' : 'text-2xl'}`} data-testid={`kpi-value-${idx}`}>{kpi.value}</p>
          <p className="text-sm text-slate-400">{kpi.title}</p>
          {kpi.sub && <p className="text-xs text-slate-500 mt-0.5">{kpi.sub}</p>}
        </div>
        <p className="text-[10px] text-slate-500 mt-2 flex items-center gap-1"><Search className="h-3 w-3" /> Ver detalle del KPI</p>
      </button>
    );
  };

  return (
    <div className="space-y-6" data-testid="dashboard-ia">
      {/* Período canónico + export + drill */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <PeriodoSelector periodo={periodoActivo} onChange={cambiarPeriodo} periodoLabel={data.periodoLabel}
          rangoInicio={rangoInicio} rangoFin={rangoFin} onRango={onRango} />
        <div className="flex items-center gap-3">
          {loading && (
            <div className="flex items-center gap-2 text-slate-400">
              <Loader2 className="h-4 w-4 animate-spin" /><span className="text-sm">Actualizando...</span>
            </div>
          )}
          <button onClick={() => { setDrillKpi(null); setDrill(true); }} data-testid="dashboard-drilldown-btn"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-700 hover:bg-slate-600 text-white transition-colors">
            <Receipt className="h-3.5 w-3.5" /> Reconstruir Tickets
          </button>
          <ExportButtons filename="dashboard_kpis" title="Resumen KPIs Inteligencia"
            columns={[{ key: 'kpi', label: 'KPI' }, { key: 'valor', label: 'Valor' }]}
            rows={exportRows} meta={meta} testid="dashboard-export" />
        </div>
      </div>

      <SyncControlPanel
        unidad={unidadSeleccionada}
        fechaInicio={data.fechaInicio}
        fechaFin={data.fechaFin}
        onUpdated={fetchDashboardData}
      />

      {/* KPIs principales (Ventas + promedios canónicos arriba) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {kpiPrincipales.map((kpi, idx) => <KpiCard key={idx} kpi={kpi} idx={idx} big />)}
      </div>
      {/* KPIs secundarios */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {kpiSecundarios.map((kpi, idx) => <KpiCard key={idx + 3} kpi={kpi} idx={idx + 3} />)}
      </div>

      <div className="bg-slate-800/50 border border-amber-500/30 rounded-xl p-5" data-testid="dashboard-dia-actual">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-white">Operación del día</h3>
            <p className="text-xs text-slate-400">Separada del acumulado cerrado</p>
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div><p className="text-slate-500">Ventas</p><p className="text-xl font-bold text-amber-400">{money2(data.ventasDia?.ventas)}</p></div>
          <div><p className="text-slate-500">Propinas</p><p className="text-xl font-bold text-white">{money2(data.ventasDia?.propinas)}</p></div>
          <div><p className="text-slate-500">Cheques</p><p className="text-xl font-bold text-white">{Number(data.ventasDia?.cheques || 0).toLocaleString()}</p></div>
          <div><p className="text-slate-500">PAX</p><p className="text-xl font-bold text-white">{Number(data.ventasDia?.pax || 0).toLocaleString()}</p></div>
        </div>
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
              {data.topCasas.slice(0, 8).map((casa, idx) => (
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

      <TicketDrilldownModal open={drill} onClose={() => setDrill(false)}
        unidad={unidadSeleccionada} periodo={periodoActivo}
        fechaInicio={data.fechaInicio || (esCustom ? rangoInicio : undefined)}
        fechaFin={data.fechaFin || (esCustom ? rangoFin : undefined)}
        metric={drillKpi?.metric || 'tickets'}
        kpiValor={drillKpi?.rawValue}
        titulo={drillKpi?.drillTitle || 'Reconstrucción de Tickets'} />
    </div>
  );
}
