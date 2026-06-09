/**
 * Ventas por Clasificación → Familia → Subfamilia (datos reales, sin mock).
 * Clasificación macro (Alimentos/Bebidas/Otros) CANÓNICA desde Sync_Productos.
 * Fuente: /api/inteligencia/familias (ventas_clasificacion).
 */
import React, { useState, useEffect } from 'react';
import { Layers, ChevronDown, ChevronRight, Loader2 } from 'lucide-react';
import { apiGet, ESTADO } from '../api/client';
import { EstadoVacio } from '../components/EstadoVacio';
import { PeriodoSelector } from '../components/PeriodoSelector';
import { ExportButtons } from '../components/ExportButtons';

const PALETA = ['emerald', 'blue', 'purple', 'amber', 'pink', 'cyan'];
const CLS = {
  emerald: { dot: 'bg-emerald-500', bar: 'bg-emerald-500', text: 'text-emerald-400' },
  blue: { dot: 'bg-blue-500', bar: 'bg-blue-500', text: 'text-blue-400' },
  purple: { dot: 'bg-purple-500', bar: 'bg-purple-500', text: 'text-purple-400' },
  amber: { dot: 'bg-amber-500', bar: 'bg-amber-500', text: 'text-amber-400' },
  pink: { dot: 'bg-pink-500', bar: 'bg-pink-500', text: 'text-pink-400' },
  cyan: { dot: 'bg-cyan-500', bar: 'bg-cyan-500', text: 'text-cyan-400' },
};
const formatMoney = (val) => {
  const v = Number(val || 0);
  if (v >= 1000000) return `$${(v / 1000000).toFixed(2)}M`;
  if (v >= 1000) return `$${(v / 1000).toFixed(1)}K`;
  return `$${v.toFixed(0)}`;
};

export default function VentasFamiliaPage({ unidadSeleccionada, periodo = 'mes' }) {
  const [clasif, setClasif] = useState([]);
  const [estado, setEstado] = useState(ESTADO.CARGANDO);
  const [periodoLabel, setPeriodoLabel] = useState('');
  const [periodoLocal, setPeriodoLocal] = useState(periodo);
  const [openClas, setOpenClas] = useState([]);
  const [openFam, setOpenFam] = useState([]);
  const [openSub, setOpenSub] = useState([]);      // subfamilias expandidas
  const [prodMap, setProdMap] = useState({});       // key sub -> {loading, productos}

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unidadSeleccionada, periodoLocal]);

  const fetchData = async () => {
    setEstado(ESTADO.CARGANDO);
    const { estado: est, data } = await apiGet('/inteligencia/familias', { unidad: unidadSeleccionada, periodo: periodoLocal });
    if (est !== ESTADO.OK || !data || data.success === false) {
      setClasif([]); setEstado(est === ESTADO.OK ? ESTADO.ERROR : est); return;
    }
    const lista = data.ventas_clasificacion || [];
    setClasif(lista);
    setPeriodoLabel(data.filtros?.periodo_label || '');
    setOpenClas(lista.slice(0, 2).map(c => c.clasificacion));
    setOpenSub([]); setProdMap({});
    setEstado(lista.length ? ESTADO.OK : ESTADO.SIN_DATOS);
  };

  const toggle = (arr, setArr, key) => setArr(arr.includes(key) ? arr.filter(k => k !== key) : [...arr, key]);

  const toggleSub = async (familia, subfamilia) => {
    const skey = `${familia}>${subfamilia}`;
    const abierto = openSub.includes(skey);
    setOpenSub(abierto ? openSub.filter(k => k !== skey) : [...openSub, skey]);
    if (abierto || prodMap[skey]) return;  // ya cargado o cerrando
    setProdMap(m => ({ ...m, [skey]: { loading: true, productos: [] } }));
    const { estado: est, data } = await apiGet('/inteligencia/productos-subfamilia', {
      familia, subfamilia, unidad: unidadSeleccionada, periodo: periodoLocal,
    });
    setProdMap(m => ({ ...m, [skey]: { loading: false, productos: (est === ESTADO.OK && data?.productos) ? data.productos : [] } }));
  };

  const total = clasif.reduce((a, c) => a + Number(c.ventas || 0), 0);
  const meta = `${unidadSeleccionada === 'todas' ? 'Consolidado' : unidadSeleccionada} · ${periodoLabel}`;

  // Filas planas para export
  const exportRows = [];
  clasif.forEach(c => c.familias.forEach(f => {
    if (f.subfamilias.length) f.subfamilias.forEach(s => exportRows.push({
      clasificacion: c.clasificacion, familia: f.familia, subfamilia: s.nombre, ventas: s.ventas, cantidad: s.cantidad,
    }));
    else exportRows.push({ clasificacion: c.clasificacion, familia: f.familia, subfamilia: '', ventas: f.ventas, cantidad: f.cantidad });
  }));
  const exportCols = [
    { key: 'clasificacion', label: 'Clasificación' }, { key: 'familia', label: 'Familia' },
    { key: 'subfamilia', label: 'Subfamilia' }, { key: 'ventas', label: 'Ventas' }, { key: 'cantidad', label: 'Cantidad' },
  ];

  return (
    <div className="space-y-6" data-testid="ventas-familia-page">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <PeriodoSelector periodo={periodoLocal} onChange={setPeriodoLocal} periodoLabel={periodoLabel} />
        <ExportButtons filename="ventas_clasificacion" title="Ventas por Clasificación y Familia"
          columns={exportCols} rows={exportRows} meta={meta} testid="familia-export" />
      </div>

      {estado !== ESTADO.OK ? (
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl">
          <EstadoVacio estado={estado} testid="ventas-familia-estado" />
        </div>
      ) : (
        <>
          {/* Tarjetas macro: Alimentos / Bebidas / Otros */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4" data-testid="clasificacion-cards">
            {clasif.slice(0, 3).map((c, idx) => {
              const col = CLS[PALETA[idx % PALETA.length]];
              return (
                <div key={c.clasificacion} className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 cursor-pointer hover:border-slate-600"
                  onClick={() => toggle(openClas, setOpenClas, c.clasificacion)}>
                  <div className="flex items-center justify-between mb-2">
                    <span className={`${col.text} font-semibold text-sm`}>{c.clasificacion}</span>
                    <span className="text-xs text-slate-500">{c.porcentaje}%</span>
                  </div>
                  <p className="text-2xl font-bold text-white">{formatMoney(c.ventas)}</p>
                  <p className="text-xs text-slate-400 mt-1">{Number(c.cantidad).toLocaleString()} unidades · {c.familias.length} familias</p>
                  <div className="mt-2 h-1 bg-slate-700 rounded-full overflow-hidden">
                    <div className={`h-full ${col.bar} rounded-full`} style={{ width: `${c.porcentaje}%` }} />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Árbol jerárquico 3 niveles */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-700">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <Layers className="h-5 w-5 text-emerald-400" /> Clasificación → Familia → Subfamilia
              </h3>
            </div>
            <div className="divide-y divide-slate-700/50">
              {clasif.map((c, ci) => {
                const col = CLS[PALETA[ci % PALETA.length]];
                const cOpen = openClas.includes(c.clasificacion);
                return (
                  <div key={c.clasificacion}>
                    <button onClick={() => toggle(openClas, setOpenClas, c.clasificacion)}
                      data-testid={`clasif-row-${ci}`}
                      className="w-full px-4 py-4 flex items-center justify-between hover:bg-slate-700/30">
                      <div className="flex items-center gap-3">
                        {cOpen ? <ChevronDown className="h-5 w-5 text-slate-400" /> : <ChevronRight className="h-5 w-5 text-slate-400" />}
                        <div className={`w-3 h-3 rounded-full ${col.dot}`} />
                        <span className="text-white font-semibold">{c.clasificacion}</span>
                        <span className="text-xs text-slate-500 ml-2">({c.familias.length} familias)</span>
                      </div>
                      <div className="flex items-center gap-6">
                        <span className={`text-sm font-semibold ${col.text}`}>{formatMoney(c.ventas)}</span>
                        <span className="text-sm text-slate-400 w-12 text-right">{c.porcentaje}%</span>
                      </div>
                    </button>
                    {cOpen && c.familias.map((f) => {
                      const fkey = `${c.clasificacion}>${f.familia}`;
                      const fOpen = openFam.includes(fkey);
                      return (
                        <div key={fkey} className="bg-slate-900/20">
                          <button onClick={() => toggle(openFam, setOpenFam, fkey)}
                            className="w-full px-4 py-3 pl-12 flex items-center justify-between hover:bg-slate-700/20 border-t border-slate-700/30">
                            <div className="flex items-center gap-3">
                              {f.subfamilias.length ? (fOpen ? <ChevronDown className="h-4 w-4 text-slate-500" /> : <ChevronRight className="h-4 w-4 text-slate-500" />) : <span className="w-4" />}
                              <span className="text-sm text-slate-200">{f.familia}</span>
                              <span className="text-xs text-slate-600">({f.subfamilias.length} subf.)</span>
                            </div>
                            <div className="flex items-center gap-6">
                              <span className="text-sm text-white">{formatMoney(f.ventas)}</span>
                              <span className="text-xs text-slate-500 w-12 text-right">{f.porcentaje}%</span>
                            </div>
                          </button>
                          {fOpen && f.subfamilias.map((s) => {
                            const skey = `${f.familia}>${s.nombre}`;
                            const sOpen = openSub.includes(skey);
                            const prod = prodMap[skey];
                            return (
                              <div key={s.nombre} className="bg-slate-900/30">
                                <button onClick={() => toggleSub(f.familia, s.nombre)}
                                  data-testid={`subfamilia-row-${ci}`}
                                  className="w-full px-4 py-2 pl-20 flex items-center justify-between border-t border-slate-700/20 hover:bg-slate-700/10">
                                  <div className="flex items-center gap-3">
                                    {sOpen ? <ChevronDown className="h-3.5 w-3.5 text-slate-500" /> : <ChevronRight className="h-3.5 w-3.5 text-slate-500" />}
                                    <div className={`w-2 h-2 rounded-full ${col.dot} opacity-60`} />
                                    <span className="text-sm text-slate-400">{s.nombre}</span>
                                  </div>
                                  <div className="flex items-center gap-6">
                                    <span className="text-sm text-slate-300">{formatMoney(s.ventas)}</span>
                                    <span className="text-xs text-slate-600 w-12 text-right">{s.porcentaje}%</span>
                                  </div>
                                </button>
                                {sOpen && (
                                  prod?.loading ? (
                                    <div className="px-4 py-3 pl-28 flex items-center gap-2 text-slate-500 text-xs"><Loader2 className="h-3.5 w-3.5 animate-spin" /> Cargando productos…</div>
                                  ) : (prod?.productos?.length ? (
                                    <>
                                      <div className="px-4 py-1.5 pl-28 flex items-center justify-between text-[10px] uppercase tracking-wide text-slate-600 bg-slate-900/40">
                                        <span>Producto de venta</span><span>Cant · Ventas · %</span>
                                      </div>
                                      {prod.productos.map((p, pi) => (
                                        <div key={pi} className="px-4 py-1.5 pl-28 flex items-center justify-between border-t border-slate-700/10 hover:bg-slate-700/10">
                                          <span className="text-sm text-slate-300">{p.producto}</span>
                                          <div className="flex items-center gap-5">
                                            <span className="text-xs text-slate-500 w-14 text-right">{Number(p.cantidad).toLocaleString()} u</span>
                                            <span className="text-sm text-emerald-400 w-20 text-right">{formatMoney(p.ventas)}</span>
                                            <span className="text-xs text-slate-600 w-10 text-right">{p.porcentaje}%</span>
                                          </div>
                                        </div>
                                      ))}
                                    </>
                                  ) : (
                                    <div className="px-4 py-3 pl-28 text-xs text-slate-600">Sin productos en el período.</div>
                                  ))
                                )}
                              </div>
                            );
                          })}
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            </div>
            <div className="px-4 py-4 border-t border-slate-700 bg-slate-800/80 flex items-center justify-between">
              <span className="text-sm font-medium text-white">TOTAL GENERAL</span>
              <span className="text-lg font-bold text-emerald-400">{formatMoney(total)}</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
