/**
 * Benchmark Interno de Grupo — Reportador comparativo
 * ===================================================
 * Compara cifras de MI unidad vs el grupo (EDARSA), con CONFIDENCIALIDAD aplicada
 * en backend: si el usuario no tiene permiso, ve "Unidad comparable A/B" en lugar
 * de nombres reales. NO hay datos mock: estados vacíos honestos.
 *
 * Fuente: /api/comercial/benchmark/interno/{unidades,productos} (NO-LIVE, SQL-first).
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Building2, TrendingUp, TrendingDown, Trophy, ShieldCheck, ShieldAlert,
  Package, BarChart3, Wine, AlertTriangle,
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

const METRICAS = [
  { id: 'ventas', label: 'Ventas', fmt: (v) => `$${Math.round(v).toLocaleString('es-MX')}` },
  { id: 'cheque_promedio', label: 'Cheque Promedio', fmt: (v) => `$${(v || 0).toLocaleString('es-MX', { maximumFractionDigits: 0 })}` },
  { id: 'venta_por_pax', label: 'Venta / PAX', fmt: (v) => `$${(v || 0).toLocaleString('es-MX', { maximumFractionDigits: 0 })}` },
  { id: 'pax', label: 'PAX', fmt: (v) => Math.round(v).toLocaleString('es-MX') },
  { id: 'cheques', label: 'Cheques', fmt: (v) => Math.round(v).toLocaleString('es-MX') },
];

const fmtNum = (v, fmt) => (v === null || v === undefined ? '—' : fmt(v));

function NivelBadge({ nivel, advertencias }) {
  const real = nivel === 'COMPLETO' || nivel === 'GRUPO_NOMBRES';
  return (
    <div className="flex items-center gap-2 flex-wrap" data-testid="benchmark-nivel-badge">
      <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${
        real ? 'bg-emerald-500/15 text-emerald-300' : 'bg-amber-500/15 text-amber-300'}`}>
        {real ? <ShieldCheck className="h-3.5 w-3.5" /> : <ShieldAlert className="h-3.5 w-3.5" />}
        Confidencialidad: {nivel}
      </span>
      {(advertencias || []).map((a, i) => (
        <span key={i} className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs bg-rose-500/15 text-rose-300">
          <AlertTriangle className="h-3 w-3" /> {a}
        </span>
      ))}
    </div>
  );
}

function KpiCard({ label, value, sub, accent = 'emerald' }) {
  return (
    <div className="bg-slate-800/70 border border-slate-700 rounded-xl p-4">
      <p className="text-xs text-slate-400">{label}</p>
      <p className={`text-2xl font-bold mt-1 text-${accent}-300`}>{value}</p>
      {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
    </div>
  );
}

export default function BenchmarkGrupoPage() {
  const [unidades, setUnidades] = useState([]);
  const [unidad, setUnidad] = useState('');
  const [metrica, setMetrica] = useState('ticket_promedio');
  const [data, setData] = useState(null);
  const [productos, setProductos] = useState(null);
  const [loading, setLoading] = useState(false);
  const [vista, setVista] = useState('unidades'); // unidades | productos

  const metaMetrica = METRICAS.find((m) => m.id === metrica) || METRICAS[0];

  useEffect(() => {
    fetch(`${API_URL}/api/comercial/benchmark/mis-unidades`, { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : { unidades: [] }))
      .then((d) => {
        setUnidades(d.unidades || []);
        if ((d.unidades || []).length) setUnidad(d.unidades[0].codigo);
      })
      .catch(() => setUnidades([]));
  }, []);

  const cargarUnidades = useCallback(async () => {
    if (!unidad) return;
    setLoading(true);
    try {
      const r = await fetch(
        `${API_URL}/api/comercial/benchmark/interno/unidades?unidad=${encodeURIComponent(unidad)}&metrica=${metrica}`,
        { credentials: 'include' });
      setData(r.ok ? await r.json() : null);
    } catch { setData(null); }
    setLoading(false);
  }, [unidad, metrica]);

  const cargarProductos = useCallback(async () => {
    if (!unidad) return;
    setLoading(true);
    const met = metrica === 'ventas' ? 'ventas' : 'ventas';
    try {
      const r = await fetch(
        `${API_URL}/api/comercial/benchmark/interno/productos?unidad=${encodeURIComponent(unidad)}&metrica=${met}&top=20`,
        { credentials: 'include' });
      setProductos(r.ok ? await r.json() : null);
    } catch { setProductos(null); }
    setLoading(false);
  }, [unidad, metrica]);

  useEffect(() => {
    if (vista === 'unidades') cargarUnidades();
    else cargarProductos();
  }, [vista, cargarUnidades, cargarProductos]);

  const b = data?.benchmark;
  const maxValor = data?.unidades?.reduce((m, u) => Math.max(m, u.valor || 0), 0) || 1;

  return (
    <div className="space-y-5" data-testid="benchmark-grupo-page">
      {/* Controles */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 flex flex-wrap items-end gap-4">
        <div>
          <label className="text-xs text-slate-400 block mb-1">Mi unidad</label>
          <select value={unidad} onChange={(e) => setUnidad(e.target.value)}
            data-testid="benchmark-unidad-select"
            className="bg-slate-700 text-white text-sm rounded px-3 py-2 border border-slate-600 focus:border-emerald-400 focus:outline-none min-w-[180px]">
            {unidades.length === 0 && <option value="">— sin unidades —</option>}
            {unidades.map((u) => <option key={u.codigo} value={u.codigo}>{u.nombre}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1">Métrica</label>
          <select value={metrica} onChange={(e) => setMetrica(e.target.value)}
            data-testid="benchmark-metrica-select"
            className="bg-slate-700 text-white text-sm rounded px-3 py-2 border border-slate-600 focus:border-emerald-400 focus:outline-none">
            {METRICAS.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
          </select>
        </div>
        <div className="flex gap-1 bg-slate-700/50 rounded-lg p-1 ml-auto">
          {[{ id: 'unidades', label: 'Vs Grupo', icon: BarChart3 }, { id: 'productos', label: 'Mis Productos', icon: Package }].map((t) => {
            const Icon = t.icon;
            return (
              <button key={t.id} onClick={() => setVista(t.id)} data-testid={`benchmark-tab-${t.id}`}
                className={`flex items-center gap-2 px-3 py-1.5 rounded text-sm transition-all ${
                  vista === t.id ? 'bg-emerald-500/20 text-emerald-300' : 'text-slate-400 hover:text-white'}`}>
                <Icon className="h-4 w-4" /> {t.label}
              </button>
            );
          })}
        </div>
      </div>

      {loading && (
        <div className="text-center py-16 text-slate-400" data-testid="benchmark-loading">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-emerald-400 mx-auto" />
          <p className="mt-3">Calculando benchmark…</p>
        </div>
      )}

      {/* VISTA: VS GRUPO */}
      {!loading && vista === 'unidades' && data && (
        <div className="space-y-5">
          <NivelBadge nivel={data.nivel_anonimizacion_aplicado} advertencias={data.advertencias} />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <KpiCard label={`Mi ${metaMetrica.label}`} value={fmtNum(b?.valor_propio, metaMetrica.fmt)}
              sub={`Posición ${b?.posicion_relativa ?? '—'} de ${b?.cobertura_unidades ?? '—'}`} />            <KpiCard label="Promedio grupo" value={fmtNum(b?.promedio_grupo, metaMetrica.fmt)}
              sub={`Mediana ${fmtNum(b?.mediana_grupo, metaMetrica.fmt)}`} accent="sky" />
            <KpiCard label="Diferencia vs promedio"
              value={b?.diferencia_porcentual != null ? `${b.diferencia_porcentual > 0 ? '+' : ''}${b.diferencia_porcentual}%` : '—'}
              sub={fmtNum(b?.diferencia_absoluta, metaMetrica.fmt)}
              accent={(b?.diferencia_porcentual ?? 0) >= 0 ? 'emerald' : 'rose'} />
            <KpiCard label="Mi percentil" value={b?.percentil_propio != null ? `${b.percentil_propio}` : '—'}
              sub={`Cuartil ${b?.cuartil_propio ?? '—'} · P25 ${fmtNum(b?.percentil_25_grupo, metaMetrica.fmt)} / P75 ${fmtNum(b?.percentil_75_grupo, metaMetrica.fmt)}`}
              accent="violet" />
          </div>

          {/* Ranking de unidades (anónimo si no hay permiso) */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Trophy className="h-4 w-4 text-amber-400" /> Ranking del grupo — {metaMetrica.label}
            </h3>
            <div className="space-y-2" data-testid="benchmark-ranking">
              {(data.unidades || []).map((u, i) => {
                const propia = u.nivel_anonimizacion_aplicado === 'REAL'
                  && u.unidad_nombre && unidades.find((x) => x.nombre === u.unidad_nombre)?.codigo === unidad;
                const pct = ((u.valor || 0) / maxValor) * 100;
                return (
                  <div key={i} className={`flex items-center gap-3 ${propia ? 'bg-emerald-500/10 -mx-2 px-2 py-1 rounded' : ''}`}>
                    <span className="w-6 text-xs text-slate-500 text-right">{i + 1}</span>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className={`text-sm ${propia ? 'text-emerald-300 font-semibold' : 'text-slate-300'} flex items-center gap-1`}>
                          <Building2 className="h-3.5 w-3.5" /> {u.unidad_nombre}
                          {propia && <span className="text-[10px] px-1.5 py-0.5 bg-emerald-500/20 rounded">Mi unidad</span>}
                        </span>
                        <span className="text-sm text-white font-medium">{fmtNum(u.valor, metaMetrica.fmt)}</span>
                      </div>
                      <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                        <div className={`h-full ${propia ? 'bg-emerald-400' : 'bg-sky-500/60'}`} style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
          <p className="text-[11px] text-slate-500">
            Fuente: {data.source_table} · {data.periodo?.desde} → {data.periodo?.hasta} · generado {new Date(data.generated_at).toLocaleString('es-MX')}
          </p>
        </div>
      )}

      {/* VISTA: MIS PRODUCTOS */}
      {!loading && vista === 'productos' && productos && (
        <div className="space-y-4">
          <NivelBadge nivel={productos.nivel_anonimizacion_aplicado} advertencias={productos.advertencias} />
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
            <table className="w-full text-sm" data-testid="benchmark-productos-tabla">
              <thead className="bg-slate-700/40 text-slate-400 text-xs">
                <tr>
                  <th className="text-left px-4 py-2">Producto</th>
                  <th className="text-left px-4 py-2">Casa</th>
                  <th className="text-right px-4 py-2">Mi venta</th>
                  <th className="text-right px-4 py-2">Prom. grupo</th>
                  <th className="text-right px-4 py-2">Dif %</th>
                  <th className="text-center px-4 py-2">Cobertura</th>
                </tr>
              </thead>
              <tbody>
                {(productos.productos || []).length === 0 && (
                  <tr><td colSpan={6} className="text-center text-slate-500 py-8">Sin datos de productos en el período.</td></tr>
                )}
                {(productos.productos || []).map((p, i) => {
                  const bg = p.benchmark_grupo;
                  const dif = bg?.diferencia_porcentual;
                  return (
                    <tr key={i} className="border-t border-slate-700/50 hover:bg-slate-700/20">
                      <td className="px-4 py-2 text-slate-200 flex items-center gap-1">
                        {p.es_alcohol && <Wine className="h-3.5 w-3.5 text-purple-400" />} {p.producto_nombre}
                      </td>
                      <td className="px-4 py-2 text-slate-400">{p.casa || '—'}</td>
                      <td className="px-4 py-2 text-right text-white">${Math.round(p.mi_valor).toLocaleString('es-MX')}</td>
                      <td className="px-4 py-2 text-right text-slate-300">${Math.round(bg?.promedio_grupo || 0).toLocaleString('es-MX')}</td>
                      <td className={`px-4 py-2 text-right font-medium ${(dif ?? 0) >= 0 ? 'text-emerald-300' : 'text-rose-300'}`}>
                        {dif != null ? (
                          <span className="inline-flex items-center gap-0.5">
                            {dif >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}{dif}%
                          </span>) : '—'}
                      </td>
                      <td className="px-4 py-2 text-center text-slate-400">{bg?.cobertura_unidades ?? '—'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="text-[11px] text-slate-500">
            Fuente: {productos.source_table} · {productos.periodo?.desde} → {productos.periodo?.hasta}
          </p>
        </div>
      )}

      {!loading && ((vista === 'unidades' && !data) || (vista === 'productos' && !productos)) && (
        <div className="text-center py-16 text-slate-500" data-testid="benchmark-empty">
          <BarChart3 className="h-10 w-10 mx-auto mb-2 opacity-40" />
          Selecciona tu unidad para ver el benchmark del grupo.
        </div>
      )}
    </div>
  );
}
