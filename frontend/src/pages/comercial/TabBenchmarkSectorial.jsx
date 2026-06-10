import React, { useState, useEffect, useCallback } from 'react';
import {
  Layers, RefreshCw, TrendingUp, TrendingDown, Minus, AlertTriangle,
  Building2, Filter, Store, BarChart2, UploadCloud, ArrowRight
} from 'lucide-react';
import api from '@/lib/api';
import TabIngestaCompetencia from './TabIngestaCompetencia';

const fmt = (v) => {
  if (v === null || v === undefined) return '—';
  return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', minimumFractionDigits: 2 }).format(v);
};

const DesviacionBadge = ({ pct }) => {
  if (pct === null || pct === undefined) {
    return <span className="text-gray-400" data-testid="desviacion-sin-dato">—</span>;
  }
  const positivo = pct > 0;
  const neutro = pct === 0;
  const Icon = neutro ? Minus : positivo ? TrendingUp : TrendingDown;
  // Precio propio por ENCIMA del sector (pct>0) = potencialmente caro -> ambar/rojo
  const cls = neutro
    ? 'bg-gray-100 text-gray-600'
    : positivo
      ? 'bg-red-50 text-red-700 border border-red-200'
      : 'bg-green-50 text-green-700 border border-green-200';
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${cls}`} data-testid="desviacion-badge">
      <Icon className="w-3 h-3" />
      {positivo ? '+' : ''}{pct}%
    </span>
  );
};

const SEMAFORO_CFG = {
  rojo: { dot: 'bg-red-500', label: 'Caro', cls: 'text-red-700' },
  ambar: { dot: 'bg-amber-500', label: 'Cerca', cls: 'text-amber-700' },
  verde: { dot: 'bg-green-500', label: 'OK / Oportunidad', cls: 'text-green-700' },
  gris: { dot: 'bg-gray-300', label: '—', cls: 'text-gray-400' },
};

const Semaforo = ({ tipo, oportunidad }) => {
  const cfg = SEMAFORO_CFG[tipo] || SEMAFORO_CFG.gris;
  const txt = oportunidad === 'CARO' ? 'Caro' : oportunidad === 'BARATO' ? 'Oportunidad ↑' : oportunidad === 'ALINEADO' ? 'Alineado' : '—';
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${cfg.cls}`} data-testid={`semaforo-${oportunidad}`}>
      <span className={`w-2.5 h-2.5 rounded-full ${cfg.dot}`} />
      {txt}
    </span>
  );
};

const EstadoVacio = ({ titulo, detalle }) => (
  <div className="text-center py-12 text-gray-500" data-testid="benchmark-sectorial-vacio">
    <BarChart2 className="w-10 h-10 mx-auto mb-3 text-gray-300" />
    <p className="font-medium text-gray-600">{titulo}</p>
    {detalle && <p className="text-sm mt-1 max-w-md mx-auto">{detalle}</p>}
  </div>
);

// ---------------- Vista A: vs Sector ----------------
const VistaVsSector = ({ empresaId, unidadId, onNavigateTab }) => {
  const [data, setData] = useState(null);
  const [sectores, setSectores] = useState(null);
  const [segmento, setSegmento] = useState('');
  const [giro, setGiro] = useState('');
  const [loading, setLoading] = useState(true);

  const cargar = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ empresa_id: empresaId, unidad_negocio_pk: unidadId });
      if (segmento) params.append('segmento', segmento);
      if (giro) params.append('giro', giro);
      const [r, s] = await Promise.all([
        api.get(`/comercial/benchmark-sectorial/vs-sector?${params.toString()}`),
        api.get(`/comercial/benchmark-sectorial/sectores?empresa_id=${empresaId}`),
      ]);
      setData(r.data);
      setSectores(s.data);
    } catch (e) {
      console.error('vs-sector', e);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [empresaId, unidadId, segmento, giro]);

  useEffect(() => { cargar(); }, [cargar]);

  if (loading) return <div className="py-12 text-center text-gray-400"><RefreshCw className="w-6 h-6 animate-spin mx-auto" /></div>;
  if (!data) return <EstadoVacio titulo="No se pudo cargar el benchmark" />;

  const comparables = data.filas.filter((f) => f.estado === 'COMPARABLE');

  return (
    <div className="space-y-4" data-testid="vista-vs-sector">
      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex items-center gap-2 text-sm">
          <Filter className="w-4 h-4 text-gray-500" />
          <select
            data-testid="filtro-segmento"
            className="border border-gray-200 rounded-md px-2 py-1 text-sm"
            value={segmento}
            onChange={(e) => setSegmento(e.target.value)}
          >
            <option value="">Todos los segmentos</option>
            {(sectores?.segmentos || []).map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <select
            data-testid="filtro-giro"
            className="border border-gray-200 rounded-md px-2 py-1 text-sm"
            value={giro}
            onChange={(e) => setGiro(e.target.value)}
          >
            <option value="">Todos los giros</option>
            {(sectores?.giros || []).map((g) => <option key={g} value={g}>{g}</option>)}
          </select>
        </div>
        <button onClick={cargar} className="ml-auto inline-flex items-center gap-1 text-sm text-purple-600 hover:text-purple-800" data-testid="btn-refrescar-vs-sector">
          <RefreshCw className="w-4 h-4" /> Refrescar
        </button>
      </div>

      <div className="grid grid-cols-3 gap-3 text-sm">
        <div className="bg-blue-50 rounded-lg p-3"><div className="text-gray-500">Categorías</div><div className="text-xl font-bold text-blue-700">{data.total_categorias}</div></div>
        <div className="bg-green-50 rounded-lg p-3"><div className="text-gray-500">Comparables</div><div className="text-xl font-bold text-green-700">{data.categorias_comparables}</div></div>
        <div className="bg-gray-50 rounded-lg p-3"><div className="text-gray-500">Competidores</div><div className="text-xl font-bold text-gray-700">{sectores?.total_competidores ?? 0}</div></div>
      </div>

      {data.oportunidades && data.categorias_comparables > 0 && (
        <div className="flex flex-wrap items-center gap-3 bg-white border border-gray-200 rounded-lg p-3" data-testid="resumen-oportunidades">
          <span className="text-sm font-medium text-gray-700">Semáforo de oportunidad (±{data.umbral_pct}%):</span>
          <span className="inline-flex items-center gap-1.5 text-sm text-red-700"><span className="w-2.5 h-2.5 rounded-full bg-red-500" /> {data.oportunidades.caro} caro(s)</span>
          <span className="inline-flex items-center gap-1.5 text-sm text-green-700"><span className="w-2.5 h-2.5 rounded-full bg-green-500" /> {data.oportunidades.barato} oportunidad(es) ↑</span>
          <span className="inline-flex items-center gap-1.5 text-sm text-gray-600"><span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> {data.oportunidades.alineado} alineado(s)</span>
          {(data.oportunidades.caro + data.oportunidades.barato) > 0 && onNavigateTab && (
            <button
              data-testid="cta-precios-sugeridos"
              onClick={() => onNavigateTab('analisis')}
              className="ml-auto inline-flex items-center gap-1 text-sm bg-purple-600 hover:bg-purple-700 text-white rounded-full px-3 py-1.5"
            >
              Ajustar en Análisis IA <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>
      )}

      {comparables.length === 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start gap-2 text-sm text-amber-800" data-testid="aviso-sin-comparables">
          <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>No hay categorías comparables aún (las categorías de competencia no coinciden con las propias, o falta capturar precios de competencia). Captura competidores/precios o alimenta datos del sector para habilitar la comparación.</span>
        </div>
      )}

      <div className="overflow-x-auto border border-gray-200 rounded-lg">
        <table className="min-w-full text-sm" data-testid="tabla-vs-sector">
          <thead className="bg-gray-50 text-gray-600">
            <tr>
              <th className="text-left px-3 py-2">Categoría</th>
              <th className="text-right px-3 py-2">Mi precio prom.</th>
              <th className="text-right px-3 py-2">Prom. sector</th>
              <th className="text-right px-3 py-2">Rango sector</th>
              <th className="text-center px-3 py-2">Items comp.</th>
              <th className="text-center px-3 py-2">Desviación</th>
              <th className="text-center px-3 py-2">Oportunidad</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.filas.map((f) => (
              <tr key={f.categoria} className="hover:bg-gray-50" data-testid={`fila-cat-${f.categoria}`}>
                <td className="px-3 py-2 font-medium text-gray-800">{f.categoria}</td>
                <td className="px-3 py-2 text-right">{fmt(f.mi_precio_prom)}<span className="text-gray-400 text-xs"> ({f.n_productos_propios})</span></td>
                <td className="px-3 py-2 text-right">{fmt(f.sector_precio_prom)}</td>
                <td className="px-3 py-2 text-right text-gray-500 text-xs">{f.sector_precio_min !== null ? `${fmt(f.sector_precio_min)} – ${fmt(f.sector_precio_max)}` : '—'}</td>
                <td className="px-3 py-2 text-center text-gray-500">{f.n_items_competencia}</td>
                <td className="px-3 py-2 text-center"><DesviacionBadge pct={f.desviacion_pct} /></td>
                <td className="px-3 py-2 text-center"><Semaforo tipo={f.semaforo} oportunidad={f.oportunidad} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ---------------- Vista B: Interno ----------------
const VistaInterno = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const cargar = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.get('/comercial/benchmark-sectorial/interno');
      setData(r.data);
    } catch (e) { console.error('interno', e); setData(null); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { cargar(); }, [cargar]);

  if (loading) return <div className="py-12 text-center text-gray-400"><RefreshCw className="w-6 h-6 animate-spin mx-auto" /></div>;
  if (!data || data.estado === 'SIN_DATOS') return <EstadoVacio titulo="Sin datos internos" detalle="No hay precios de venta cargados por unidad." />;

  return (
    <div className="space-y-4" data-testid="vista-interno">
      <div className="flex items-center gap-2 text-sm text-gray-600 flex-wrap">
        <Building2 className="w-4 h-4" />
        <span>Unidades evaluadas:</span>
        {data.unidades_evaluadas.map((u) => (
          <span key={u.empresa_id} className="px-2 py-0.5 bg-gray-100 rounded-full text-xs">{u.unidad}</span>
        ))}
        <button onClick={cargar} className="ml-auto inline-flex items-center gap-1 text-purple-600 hover:text-purple-800" data-testid="btn-refrescar-interno"><RefreshCw className="w-4 h-4" /> Refrescar</button>
      </div>
      <div className="space-y-3">
        {data.filas.map((f) => (
          <div key={f.categoria} className="border border-gray-200 rounded-lg p-3" data-testid={`interno-cat-${f.categoria}`}>
            <div className="flex justify-between items-center mb-2">
              <h4 className="font-semibold text-gray-800">{f.categoria}</h4>
              <div className="text-xs text-gray-500">Prom. interno: <span className="font-medium text-gray-700">{fmt(f.promedio_interno)}</span> · {f.n_unidades} unidades</div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
              {f.unidades.map((u) => (
                <div key={u.empresa_id} className="flex justify-between items-center bg-gray-50 rounded px-2 py-1 text-sm">
                  <span className="text-gray-700">{u.unidad}</span>
                  <span className="flex items-center gap-2">
                    <span className="text-gray-600">{fmt(u.precio_prom)}</span>
                    <DesviacionBadge pct={u.desviacion_vs_interno_pct} />
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ---------------- Vista C: Por Segmento ----------------
const VistaPorSegmento = ({ empresaId, unidadId }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const cargar = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.get(`/comercial/benchmark-sectorial/por-segmento?empresa_id=${empresaId}&unidad_negocio_pk=${unidadId}`);
      setData(r.data);
    } catch (e) { console.error('por-segmento', e); setData(null); }
    finally { setLoading(false); }
  }, [empresaId, unidadId]);

  useEffect(() => { cargar(); }, [cargar]);

  if (loading) return <div className="py-12 text-center text-gray-400"><RefreshCw className="w-6 h-6 animate-spin mx-auto" /></div>;
  if (!data || data.estado === 'SIN_DATOS') return <EstadoVacio titulo="Sin segmentos de competencia" detalle="No hay competidores con SegmentoPrecio definido para esta unidad." />;

  const segmentos = data.segmentos || [];
  return (
    <div className="space-y-4" data-testid="vista-por-segmento">
      <div className="flex items-center gap-2 text-sm text-gray-600 flex-wrap">
        <Store className="w-4 h-4" />
        <span>Segmentos:</span>
        {segmentos.map((s) => <span key={s} className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full text-xs">{s}</span>)}
        <button onClick={cargar} className="ml-auto inline-flex items-center gap-1 text-purple-600 hover:text-purple-800" data-testid="btn-refrescar-segmento"><RefreshCw className="w-4 h-4" /> Refrescar</button>
      </div>
      <div className="overflow-x-auto border border-gray-200 rounded-lg">
        <table className="min-w-full text-sm" data-testid="tabla-por-segmento">
          <thead className="bg-gray-50 text-gray-600">
            <tr>
              <th className="text-left px-3 py-2">Categoría</th>
              <th className="text-right px-3 py-2">Mi precio</th>
              {segmentos.map((s) => <th key={s} className="text-center px-3 py-2">{s}</th>)}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.filas.map((f) => (
              <tr key={f.categoria} className="hover:bg-gray-50">
                <td className="px-3 py-2 font-medium text-gray-800">{f.categoria}</td>
                <td className="px-3 py-2 text-right">{fmt(f.mi_precio_prom)}</td>
                {f.por_segmento.map((ps) => (
                  <td key={ps.segmento} className="px-3 py-2 text-center">
                    <div className="text-gray-600">{fmt(ps.sector_precio_prom)}</div>
                    <DesviacionBadge pct={ps.desviacion_pct} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ---------------- Tab principal ----------------
const SUBTABS = [
  { id: 'vs-sector', label: 'vs Sector', icon: BarChart2 },
  { id: 'interno', label: 'Entre Unidades', icon: Building2 },
  { id: 'por-segmento', label: 'Por Segmento', icon: Store },
  { id: 'ingesta', label: 'Ingesta de Datos', icon: UploadCloud },
];

const TabBenchmarkSectorial = ({ empresaId, unidadId, onNavigateTab }) => {
  const [sub, setSub] = useState('vs-sector');
  return (
    <div className="space-y-4" data-testid="tab-benchmark-sectorial">
      <div className="flex items-center gap-2">
        <Layers className="w-5 h-5 text-purple-600" />
        <div>
          <h3 className="font-semibold text-gray-800">Benchmark Sectorial</h3>
          <p className="text-xs text-gray-500">% de desviación de tus precios vs. el promedio del sector por categoría · Fuente: EDARSAHUB SQL (NO-LIVE)</p>
        </div>
      </div>

      <div className="flex gap-1 border-b border-gray-200">
        {SUBTABS.map((t) => {
          const Icon = t.icon;
          const active = sub === t.id;
          return (
            <button
              key={t.id}
              data-testid={`subtab-${t.id}`}
              onClick={() => setSub(t.id)}
              className={`inline-flex items-center gap-1.5 px-3 py-2 text-sm border-b-2 -mb-px transition-colors ${active ? 'border-purple-600 text-purple-700 font-medium' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
            >
              <Icon className="w-4 h-4" /> {t.label}
            </button>
          );
        })}
      </div>

      {sub === 'vs-sector' && <VistaVsSector empresaId={empresaId} unidadId={unidadId} onNavigateTab={onNavigateTab} />}
      {sub === 'interno' && <VistaInterno />}
      {sub === 'por-segmento' && <VistaPorSegmento empresaId={empresaId} unidadId={unidadId} />}
      {sub === 'ingesta' && <TabIngestaCompetencia empresaId={empresaId} />}
    </div>
  );
};

export default TabBenchmarkSectorial;
