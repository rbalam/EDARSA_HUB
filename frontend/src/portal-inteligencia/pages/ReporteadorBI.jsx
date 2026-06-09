/**
 * Reporteador BI — Informe Gerencial MECA MPRO (9 páginas).
 * Navegación interna + gráficos (recharts) + export Excel/PDF + drill-down.
 * Fuente: /api/reporteador-bi/* (EDARSAHUB SQL, NO-LIVE).
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  BarChart3, CalendarRange, CalendarDays, Music, Wallet, Receipt,
  Armchair, FileText, Gauge, Loader2, DollarSign, Users, ArrowUpRight, ArrowDownRight,
} from 'lucide-react';
import {
  ResponsiveContainer, ComposedChart, BarChart, LineChart, Bar, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Treemap, Cell,
} from 'recharts';
import { apiGet, ESTADO } from '../api/client';
import { EstadoVacio } from '../components/EstadoVacio';
import { PeriodoSelector } from '../components/PeriodoSelector';
import { ExportButtons } from '../components/ExportButtons';
import { PendienteSync } from '../components/PendienteSync';
import { TicketDrilldownModal } from '../components/TicketDrilldownModal';

const ICONS = { BarChart3, CalendarRange, CalendarDays, Music, Wallet, Receipt, Armchair, FileText, Gauge };
const COLORS = ['#10b981', '#3b82f6', '#a855f7', '#f59e0b', '#ec4899', '#06b6d4'];
const money = (v) => `$${Number(v || 0).toLocaleString('es-MX', { maximumFractionDigits: 0 })}`;
const money2 = (v) => `$${Number(v || 0).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const chartTip = { contentStyle: { background: '#0f172a', border: '1px solid #334155', borderRadius: 8, color: '#fff' } };

const KCOLOR = {
  emerald: { bg: 'bg-emerald-500/20', tx: 'text-emerald-400' },
  cyan: { bg: 'bg-cyan-500/20', tx: 'text-cyan-400' },
  violet: { bg: 'bg-violet-500/20', tx: 'text-violet-400' },
  blue: { bg: 'bg-blue-500/20', tx: 'text-blue-400' },
  purple: { bg: 'bg-purple-500/20', tx: 'text-purple-400' },
  amber: { bg: 'bg-amber-500/20', tx: 'text-amber-400' },
};

function Kpi({ label, value, sub, icon: Icon, trend, color = 'emerald' }) {
  const up = (trend ?? 0) >= 0;
  const c = KCOLOR[color] || KCOLOR.emerald;
  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4" data-testid={`bi-kpi-${label}`}>
      <div className="flex items-center justify-between">
        <span className={`p-2 rounded-lg ${c.bg}`}><Icon className={`h-4 w-4 ${c.tx}`} /></span>
        {trend != null && (
          <span className={`text-xs flex items-center gap-0.5 ${up ? 'text-emerald-400' : 'text-red-400'}`}>
            {up ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}{Math.abs(trend)}%
          </span>
        )}
      </div>
      <p className="text-2xl font-bold text-white mt-2">{value}</p>
      <p className="text-xs text-slate-400">{label}</p>
      {sub && <p className="text-[11px] text-slate-500">{sub}</p>}
    </div>
  );
}

export default function ReporteadorBI({ unidadSeleccionada }) {
  const [paginas, setPaginas] = useState([]);
  const [activa, setActiva] = useState('analisis-ventas');
  const [periodo, setPeriodo] = useState('mes');
  const [data, setData] = useState(null);
  const [estado, setEstado] = useState(ESTADO.CARGANDO);
  const [drill, setDrill] = useState(false);
  const reqRef = useRef(0);

  useEffect(() => {
    apiGet('/reporteador-bi/paginas').then(({ data }) => setPaginas(data?.paginas || []));
  }, []);

  useEffect(() => {
    let qp = { unidad: unidadSeleccionada, periodo };
    if (activa === 'ventas-mes') qp = { unidad: unidadSeleccionada, meses: 12 };
    if (activa === 'kpis-mes') qp = { unidad: unidadSeleccionada };
    const myReq = ++reqRef.current;
    setEstado(ESTADO.CARGANDO);
    apiGet(`/reporteador-bi/${activa}`, qp).then(({ estado: est, data: d }) => {
      if (myReq !== reqRef.current) return;  // respuesta obsoleta: ignorar (evita carrera)
      if (est !== ESTADO.OK || !d || d.success === false) { setData(null); setEstado(est === ESTADO.OK ? ESTADO.ERROR : est); return; }
      setData(d); setEstado(ESTADO.OK);
    });
  }, [activa, unidadSeleccionada, periodo]);

  const meta = `${unidadSeleccionada === 'todas' ? 'Consolidado' : unidadSeleccionada} · ${data?.filtros?.periodo_label || ''}`;
  const usaPeriodo = !['ventas-mes', 'kpis-mes', 'gastos', 'analisis-documentos'].includes(activa);

  return (
    <div className="space-y-5" data-testid="reporteador-bi-page">
      {/* Sub-navegación de las 9 páginas */}
      <div className="flex flex-wrap gap-2" data-testid="bi-subnav">
        {paginas.map((p) => {
          const Icon = ICONS[p.icono] || BarChart3;
          return (
            <button key={p.id} onClick={() => setActiva(p.id)} data-testid={`bi-tab-${p.id}`}
              className={`px-3 py-2 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-all ${activa === p.id ? 'bg-emerald-500 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'} ${!p.disponible ? 'opacity-70' : ''}`}>
              <Icon className="h-3.5 w-3.5" /> {p.nombre}
              {!p.disponible && <span className="ml-1 w-1.5 h-1.5 rounded-full bg-amber-400" />}
            </button>
          );
        })}
      </div>

      {/* Barra de período (solo páginas que lo usan) */}
      {usaPeriodo && (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <PeriodoSelector periodo={periodo} onChange={setPeriodo} periodoLabel={data?.filtros?.periodo_label} />
        </div>
      )}

      {estado === ESTADO.CARGANDO ? (
        <div className="flex items-center justify-center py-20 text-slate-400"><Loader2 className="h-6 w-6 animate-spin" /></div>
      ) : estado !== ESTADO.OK ? (
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl"><EstadoVacio estado={estado} testid="bi-estado" /></div>
      ) : !data.disponible ? (
        <PendienteSync titulo={`${paginas.find((p) => p.id === activa)?.nombre || ''} — sin sincronizar`}
          nota={data.nota} fuente={data.fuente_requerida} medidas={data.medidas_pendientes || []} proxy={data.proxy} />
      ) : (
        <RenderPagina activa={activa} data={data} meta={meta} onDrill={() => setDrill(true)} />
      )}

      <TicketDrilldownModal open={drill} onClose={() => setDrill(false)}
        unidad={unidadSeleccionada} periodo={periodo} titulo="Reconstrucción de Tickets" />
    </div>
  );
}

function RenderPagina({ activa, data, meta, onDrill }) {
  if (activa === 'analisis-ventas') return <AnalisisVentas data={data} meta={meta} />;
  if (activa === 'ventas-semana') return <VentasSemana data={data} meta={meta} />;
  if (activa === 'ventas-mes') return <VentasMes data={data} meta={meta} />;
  if (activa === 'ambientacion') return <Ambientacion data={data} meta={meta} />;
  if (activa === 'revision-tickets') return <RevisionTickets data={data} meta={meta} onDrill={onDrill} />;
  if (activa === 'kpis-mes') return <KpisMes data={data} meta={meta} />;
  return null;
}

// ---- 1) Análisis de Ventas ----
function AnalisisVentas({ data, meta }) {
  const k = data.kpis;
  const treemap = (data.clasificacion || []).map((c, i) => ({ name: c.clasificacion, size: c.ventas, fill: COLORS[i % COLORS.length] }));
  const prodRows = (data.top_productos || []).map((p) => ({ producto: p.producto, familia: p.familia, cantidad: p.cantidad, ventas: p.ventas }));
  return (
    <div className="space-y-5" data-testid="bi-analisis-ventas">
      <div className="flex justify-end">
        <ExportButtons filename="bi_analisis_ventas" title="BI · Análisis de Ventas" meta={meta}
          columns={[{ key: 'producto', label: 'Producto' }, { key: 'familia', label: 'Familia' }, { key: 'cantidad', label: 'Cantidad' }, { key: 'ventas', label: 'Ventas' }]}
          rows={prodRows} testid="bi-av-export" />
      </div>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <Kpi label="Ventas" value={money(k.ventas)} icon={DollarSign} color="emerald" />
        <Kpi label="Ticket Prom." sub="ventas ÷ pax" value={money2(k.ticket_promedio)} icon={Users} color="cyan" />
        <Kpi label="Cheque Prom." sub="ventas ÷ cuentas" value={money2(k.cheque_promedio)} icon={Receipt} color="violet" />
        <Kpi label="PAX" value={k.pax.toLocaleString()} icon={Users} color="blue" />
        <Kpi label="Cuentas" value={k.cuentas.toLocaleString()} icon={Receipt} color="purple" />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
          <h3 className="text-white font-semibold mb-3">Ventas por día</h3>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={data.serie_diaria}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="fecha" tick={{ fill: '#94a3b8', fontSize: 11 }} tickFormatter={(v) => v.slice(5)} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
              <Tooltip {...chartTip} formatter={(v) => money(v)} />
              <Line type="monotone" dataKey="ventas" stroke="#10b981" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
          <h3 className="text-white font-semibold mb-3">Ventas por clasificación</h3>
          <ResponsiveContainer width="100%" height={240}>
            <Treemap data={treemap} dataKey="size" stroke="#0f172a" content={<TreemapCell />} />
          </ResponsiveContainer>
        </div>
      </div>
      <ProductTable rows={prodRows} />
    </div>
  );
}

const TreemapCell = ({ x, y, width, height, name, size, fill }) => (
  <g>
    <rect x={x} y={y} width={width} height={height} style={{ fill, stroke: '#0f172a', strokeWidth: 2 }} />
    {width > 70 && height > 30 && (
      <text x={x + 6} y={y + 18} fill="#fff" fontSize={12} fontWeight={600}>{name}</text>
    )}
    {width > 70 && height > 46 && (
      <text x={x + 6} y={y + 34} fill="#e2e8f0" fontSize={11}>{money(size)}</text>
    )}
  </g>
);

function ProductTable({ rows }) {
  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-700 text-white font-semibold">Top Productos</div>
      <table className="w-full text-sm">
        <thead className="bg-slate-800 text-xs text-slate-400"><tr><th className="px-4 py-2 text-left">PRODUCTO</th><th className="px-4 py-2 text-left">FAMILIA</th><th className="px-4 py-2 text-center">CANT</th><th className="px-4 py-2 text-right">VENTAS</th></tr></thead>
        <tbody>
          {rows.map((p, i) => (
            <tr key={i} className="border-t border-slate-700/40 hover:bg-slate-700/20">
              <td className="px-4 py-2 text-white">{p.producto}</td>
              <td className="px-4 py-2 text-slate-400">{p.familia}</td>
              <td className="px-4 py-2 text-center text-slate-300">{Number(p.cantidad).toLocaleString()}</td>
              <td className="px-4 py-2 text-right text-emerald-400 font-semibold">{money(p.ventas)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---- 2) Ventas por Semana ----
function VentasSemana({ data, meta }) {
  return (
    <div className="space-y-5" data-testid="bi-ventas-semana">
      <div className="flex justify-end">
        <ExportButtons filename="bi_ventas_semana" title="BI · Ventas por Semana" meta={meta}
          columns={[{ key: 'label', label: 'Semana' }, { key: 'ventas', label: 'Ventas' }, { key: 'pax', label: 'PAX' }, { key: 'cuentas', label: 'Cuentas' }, { key: 'var_vs_anterior', label: '% vs ant.' }]}
          rows={data.series} testid="bi-vs-export" />
      </div>
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
        <h3 className="text-white font-semibold mb-3">Ventas y PAX por semana</h3>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={data.series}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="label" tick={{ fill: '#94a3b8', fontSize: 10 }} angle={-15} textAnchor="end" height={50} />
            <YAxis yAxisId="l" tick={{ fill: '#94a3b8', fontSize: 11 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
            <YAxis yAxisId="r" orientation="right" tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <Tooltip {...chartTip} formatter={(v, n) => (n === 'ventas' ? money(v) : v)} />
            <Bar yAxisId="l" dataKey="ventas" fill="#10b981" radius={[4, 4, 0, 0]} />
            <Line yAxisId="r" type="monotone" dataKey="pax" stroke="#f59e0b" strokeWidth={2} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ---- 3) Ventas por Mes ----
function VentasMes({ data, meta }) {
  const c = data.comparativos || {};
  return (
    <div className="space-y-5" data-testid="bi-ventas-mes">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex gap-3">
          <Kpi label="Mes actual" value={money(c.mes_actual?.ventas)} icon={DollarSign} />
          <Kpi label="vs Mes anterior" value={c.var_mes_anterior != null ? `${c.var_mes_anterior}%` : '—'} icon={CalendarDays} trend={c.var_mes_anterior} color="blue" />
          <Kpi label="vs Año anterior" value={c.var_anio_anterior != null ? `${c.var_anio_anterior}%` : '—'} icon={CalendarRange} trend={c.var_anio_anterior} color="purple" />
        </div>
        <ExportButtons filename="bi_ventas_mes" title="BI · Ventas por Mes" meta={meta}
          columns={[{ key: 'label', label: 'Mes' }, { key: 'ventas', label: 'Ventas' }, { key: 'pax', label: 'PAX' }, { key: 'cuentas', label: 'Cuentas' }, { key: 'ticket_promedio', label: 'Ticket Prom' }]}
          rows={data.series} testid="bi-vm-export" />
      </div>
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
        <h3 className="text-white font-semibold mb-3">Tendencia mensual (ventas + pax)</h3>
        <ResponsiveContainer width="100%" height={320}>
          <ComposedChart data={data.series}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="label" tick={{ fill: '#94a3b8', fontSize: 10 }} angle={-15} textAnchor="end" height={50} />
            <YAxis yAxisId="l" tick={{ fill: '#94a3b8', fontSize: 11 }} tickFormatter={(v) => `$${(v / 1000000).toFixed(1)}M`} />
            <YAxis yAxisId="r" orientation="right" tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <Tooltip {...chartTip} formatter={(v, n) => (n === 'ventas' ? money(v) : v)} />
            <Bar yAxisId="l" dataKey="ventas" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            <Line yAxisId="r" type="monotone" dataKey="pax" stroke="#f59e0b" strokeWidth={2} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ---- 4) Ambientación (ventas por hora real) ----
function Ambientacion({ data, meta }) {
  return (
    <div className="space-y-5" data-testid="bi-ambientacion">
      <div className="flex justify-end">
        <ExportButtons filename="bi_ambientacion" title="BI · Ventas por Hora" meta={meta}
          columns={[{ key: 'hora', label: 'Hora' }, { key: 'ventas', label: 'Ventas' }, { key: 'pax', label: 'PAX' }, { key: 'cuentas', label: 'Cuentas' }]}
          rows={data.ventas_por_hora} testid="bi-amb-export" />
      </div>
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
        <h3 className="text-white font-semibold mb-3">Ventas por hora del día</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data.ventas_por_hora}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="hora" tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
            <Tooltip {...chartTip} formatter={(v) => money(v)} />
            <Bar dataKey="ventas" radius={[4, 4, 0, 0]}>
              {(data.ventas_por_hora || []).map((e, i) => <Cell key={i} fill={e.hora_num >= 18 ? '#6366f1' : e.hora_num >= 13 ? '#f97316' : '#f59e0b'} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 text-sm text-amber-200/90" data-testid="bi-amb-nota">
        {data.ambientacion_evento?.nota}
      </div>
    </div>
  );
}

// ---- 6) Revisión de Tickets ----
function RevisionTickets({ data, meta, onDrill }) {
  const r = data.resumen || {};
  return (
    <div className="space-y-5" data-testid="bi-revision-tickets">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <button onClick={onDrill} data-testid="bi-rt-drill" className="px-4 py-2 rounded-lg text-sm bg-emerald-600 hover:bg-emerald-500 text-white flex items-center gap-2">
          <Receipt className="h-4 w-4" /> Reconstruir tickets (drill-down)
        </button>
        <ExportButtons filename="bi_revision_tickets" title="BI · Revisión de Tickets" meta={meta}
          columns={[{ key: 'fecha', label: 'Fecha' }, { key: 'numero_ticket', label: 'Ticket' }, { key: 'unidad', label: 'Unidad' }, { key: 'pax', label: 'PAX' }, { key: 'lineas', label: 'Líneas' }, { key: 'ventas', label: 'Ventas' }]}
          rows={data.tickets} testid="bi-rt-export" />
      </div>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <Kpi label="Tickets" value={r.num_tickets?.toLocaleString()} icon={Receipt} />
        <Kpi label="Venta total" value={money(r.venta_total)} icon={DollarSign} color="emerald" />
        <Kpi label="PAX total" value={r.pax_total?.toLocaleString()} icon={Users} color="blue" />
        <Kpi label="Ticket máx" value={money(r.ticket_max)} icon={ArrowUpRight} color="purple" />
        <Kpi label="Ticket mín" value={money(r.ticket_min)} icon={ArrowDownRight} color="amber" />
      </div>
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-800 text-xs text-slate-400"><tr><th className="px-4 py-2 text-left">FECHA</th><th className="px-4 py-2 text-left">TICKET</th><th className="px-4 py-2 text-center">PAX</th><th className="px-4 py-2 text-center">LÍNEAS</th><th className="px-4 py-2 text-right">VENTAS</th></tr></thead>
          <tbody>
            {(data.tickets || []).slice(0, 50).map((t, i) => (
              <tr key={i} className="border-t border-slate-700/40 hover:bg-slate-700/20">
                <td className="px-4 py-2 text-slate-300">{t.fecha} {t.hora}</td>
                <td className="px-4 py-2 font-mono text-emerald-400">{t.numero_ticket}</td>
                <td className="px-4 py-2 text-center text-slate-300">{t.pax}</td>
                <td className="px-4 py-2 text-center text-slate-400">{t.lineas}</td>
                <td className="px-4 py-2 text-right text-white font-semibold">{money2(t.ventas)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---- 9) KPIs Mes Actual ----
function KpisMes({ data, meta }) {
  const k = data.kpis; const v = data.variaciones || {};
  return (
    <div className="space-y-5" data-testid="bi-kpis-mes">
      <div className="flex items-center justify-between">
        <span className="text-sm text-slate-400">Mes: <span className="text-white font-semibold">{data.filtros?.periodo_label}</span></span>
        <ExportButtons filename="bi_kpis_mes" title="BI · KPIs Mes Actual" meta={meta}
          columns={[{ key: 'kpi', label: 'KPI' }, { key: 'valor', label: 'Valor' }]}
          rows={[{ kpi: 'Ventas', valor: k.ventas }, { kpi: 'Ticket Promedio', valor: k.ticket_promedio }, { kpi: 'Cheque Promedio', valor: k.cheque_promedio }, { kpi: 'PAX', valor: k.pax }, { kpi: 'Cuentas', valor: k.cuentas }]}
          testid="bi-km-export" />
      </div>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <Kpi label="Ventas" value={money(k.ventas)} icon={DollarSign} color="emerald" trend={v.ventas} />
        <Kpi label="Ticket Prom." sub="ventas ÷ pax" value={money2(k.ticket_promedio)} icon={Users} color="cyan" trend={v.ticket_promedio} />
        <Kpi label="Cheque Prom." sub="ventas ÷ cuentas" value={money2(k.cheque_promedio)} icon={Receipt} color="violet" trend={v.cheque_promedio} />
        <Kpi label="PAX" value={k.pax.toLocaleString()} icon={Users} color="blue" trend={v.pax} />
        <Kpi label="Cuentas" value={k.cuentas.toLocaleString()} icon={Receipt} color="purple" trend={v.cuentas} />
      </div>
      <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 text-sm text-amber-200/90">
        {data.metas?.nota}
      </div>
    </div>
  );
}
