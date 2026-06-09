/**
 * Admin: Clasificación Comercial de Producto (catálogo canónico).
 * Resuelve los productos PENDIENTE_CLASIFICACION asignando una clasificación
 * MANUAL (por familia en bloque o por producto individual).
 * Fuente: /api/inteligencia/admin/* + /api/inteligencia/clasificaciones
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Tag, Layers, Search, CheckCircle2, Loader2, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import { apiGet, apiPost, ESTADO } from '../api/client';
import { EstadoVacio } from '../components/EstadoVacio';

const BADGE = {
  ALIMENTOS: 'bg-emerald-500/20 text-emerald-300',
  BEBIDAS: 'bg-blue-500/20 text-blue-300',
  OTROS: 'bg-purple-500/20 text-purple-300',
  PENDIENTE_CLASIFICACION: 'bg-amber-500/20 text-amber-300',
};

export default function ClasificacionAdminPage() {
  const [catalogo, setCatalogo] = useState([]);
  const [tab, setTab] = useState('familias'); // 'familias' | 'productos'
  const [familias, setFamilias] = useState([]);
  const [productos, setProductos] = useState([]);
  const [estado, setEstado] = useState(ESTADO.CARGANDO);
  const [busy, setBusy] = useState(false);
  // filtros productos
  const [q, setQ] = useState('');
  const [filtroEstado, setFiltroEstado] = useState('pendientes');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [seleccion, setSeleccion] = useState({}); // familia/producto -> clasificacion_id pendiente

  useEffect(() => {
    apiGet('/inteligencia/clasificaciones').then(({ data }) => setCatalogo(data?.clasificaciones || []));
  }, []);

  const cargarFamilias = useCallback(async () => {
    setEstado(ESTADO.CARGANDO);
    const { estado: est, data } = await apiGet('/inteligencia/admin/familias-pendientes');
    if (est !== ESTADO.OK) { setEstado(est); return; }
    setFamilias(data.familias || []);
    setEstado((data.familias || []).length ? ESTADO.OK : ESTADO.SIN_DATOS);
  }, []);

  const cargarProductos = useCallback(async () => {
    setEstado(ESTADO.CARGANDO);
    const { estado: est, data } = await apiGet('/inteligencia/admin/productos-clasificacion', {
      q: q || undefined, estado: filtroEstado, page, page_size: 50,
    });
    if (est !== ESTADO.OK) { setEstado(est); return; }
    setProductos(data.productos || []);
    setTotal(data.total || 0);
    setEstado((data.productos || []).length ? ESTADO.OK : ESTADO.SIN_DATOS);
  }, [q, filtroEstado, page]);

  useEffect(() => {
    if (tab === 'familias') cargarFamilias();
    else cargarProductos();
  }, [tab, cargarFamilias, cargarProductos]);

  const clasificarFamilia = async (fam) => {
    const cid = seleccion[`f:${fam.system_type}:${fam.familia}`];
    if (!cid) { toast.error('Elige una clasificación'); return; }
    setBusy(true);
    const { estado: est, data } = await apiPost('/inteligencia/admin/clasificar', {
      clasificacion_id: Number(cid), familia_nombre: fam.familia, system_type: fam.system_type,
    });
    setBusy(false);
    if (est === ESTADO.OK && data?.success) {
      toast.success(`${data.actualizados} productos → ${data.clasificacion}`);
      cargarFamilias();
    } else toast.error('No se pudo clasificar');
  };

  const clasificarProducto = async (prod) => {
    const cid = seleccion[`p:${prod.producto_id}`];
    if (!cid) { toast.error('Elige una clasificación'); return; }
    setBusy(true);
    const { estado: est, data } = await apiPost('/inteligencia/admin/clasificar', {
      clasificacion_id: Number(cid), producto_ids: [prod.producto_id],
    });
    setBusy(false);
    if (est === ESTADO.OK && data?.success) {
      toast.success(`${prod.nombre} → ${data.clasificacion}`);
      cargarProductos();
    } else toast.error('No se pudo clasificar');
  };

  const opcionesClasificables = catalogo.filter((c) => c.codigo !== 'PENDIENTE_CLASIFICACION');

  const Selector = ({ keyName }) => (
    <select
      data-testid={`clasif-select-${keyName}`}
      value={seleccion[keyName] || ''}
      onChange={(e) => setSeleccion((s) => ({ ...s, [keyName]: e.target.value }))}
      className="bg-slate-700 text-white text-sm rounded px-2 py-1.5 border border-slate-600 focus:border-emerald-400 focus:outline-none"
    >
      <option value="">— Clasificar como —</option>
      {opcionesClasificables.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
    </select>
  );

  return (
    <div className="space-y-6" data-testid="clasificacion-admin-page">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex gap-2">
          <button onClick={() => setTab('familias')} data-testid="tab-familias"
            className={`px-4 py-2 rounded-lg text-sm flex items-center gap-2 ${tab === 'familias' ? 'bg-emerald-500 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}>
            <Layers className="h-4 w-4" /> Por familia (bloque)
          </button>
          <button onClick={() => setTab('productos')} data-testid="tab-productos"
            className={`px-4 py-2 rounded-lg text-sm flex items-center gap-2 ${tab === 'productos' ? 'bg-emerald-500 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}>
            <Tag className="h-4 w-4" /> Por producto
          </button>
        </div>
        <button onClick={() => (tab === 'familias' ? cargarFamilias() : cargarProductos())}
          data-testid="refresh-btn" className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs bg-slate-700 hover:bg-slate-600 text-white">
          <RefreshCw className="h-3.5 w-3.5" /> Actualizar
        </button>
      </div>

      {tab === 'familias' ? (
        estado !== ESTADO.OK ? (
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl">
            {estado === ESTADO.SIN_DATOS
              ? <div className="p-10 text-center text-emerald-400 flex flex-col items-center gap-2" data-testid="familias-sin-pendientes"><CheckCircle2 className="h-8 w-8" />¡No hay familias pendientes de clasificación!</div>
              : <EstadoVacio estado={estado} testid="clasif-familias-estado" />}
          </div>
        ) : (
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-700 text-sm text-slate-400">
              Familias con productos pendientes — clasifica toda la familia de una vez.
            </div>
            <table className="w-full text-sm">
              <thead className="bg-slate-800 text-xs text-slate-400">
                <tr><th className="px-4 py-2 text-left">FAMILIA</th><th className="px-4 py-2 text-left">SISTEMA</th><th className="px-4 py-2 text-center">PENDIENTES</th><th className="px-4 py-2 text-right">ACCIÓN</th></tr>
              </thead>
              <tbody>
                {familias.map((f, i) => {
                  const keyName = `f:${f.system_type}:${f.familia}`;
                  return (
                    <tr key={keyName} data-testid={`familia-row-${i}`} className="border-t border-slate-700/40 hover:bg-slate-700/20">
                      <td className="px-4 py-2 text-white">{f.familia}</td>
                      <td className="px-4 py-2 text-slate-400">{f.system_type}</td>
                      <td className="px-4 py-2 text-center"><span className="px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 text-xs">{f.pendientes}</span></td>
                      <td className="px-4 py-2">
                        <div className="flex items-center justify-end gap-2">
                          <Selector keyName={keyName} />
                          <button onClick={() => clasificarFamilia(f)} disabled={busy} data-testid={`clasif-familia-btn-${i}`}
                            className="px-3 py-1.5 rounded-lg text-xs bg-emerald-600 hover:bg-emerald-500 text-white disabled:opacity-40">Aplicar</button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )
      ) : (
        <>
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 min-w-[220px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <input data-testid="search-input" value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }}
                placeholder="Buscar producto o familia…" className="w-full bg-slate-800 text-white text-sm rounded-lg pl-9 pr-3 py-2 border border-slate-700 focus:border-emerald-400 focus:outline-none" />
            </div>
            <select data-testid="estado-filter" value={filtroEstado} onChange={(e) => { setFiltroEstado(e.target.value); setPage(1); }}
              className="bg-slate-800 text-white text-sm rounded-lg px-3 py-2 border border-slate-700">
              <option value="pendientes">Pendientes</option>
              <option value="clasificados">Clasificados</option>
              <option value="todos">Todos</option>
            </select>
            <span className="text-sm text-slate-400" data-testid="productos-total">{total.toLocaleString()} productos</span>
          </div>

          {estado !== ESTADO.OK ? (
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl"><EstadoVacio estado={estado} testid="clasif-productos-estado" /></div>
          ) : (
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-slate-800 text-xs text-slate-400">
                  <tr><th className="px-4 py-2 text-left">PRODUCTO</th><th className="px-4 py-2 text-left">FAMILIA</th><th className="px-4 py-2 text-left">ACTUAL</th><th className="px-4 py-2 text-right">CLASIFICAR</th></tr>
                </thead>
                <tbody>
                  {productos.map((p, i) => (
                    <tr key={p.producto_id} data-testid={`producto-row-${i}`} className="border-t border-slate-700/40 hover:bg-slate-700/20">
                      <td className="px-4 py-2 text-white">{p.nombre}<span className="block text-xs text-slate-500">{p.system_type}</span></td>
                      <td className="px-4 py-2 text-slate-400">{p.familia}</td>
                      <td className="px-4 py-2"><span className={`px-2 py-0.5 rounded-full text-xs ${BADGE[p.clasificacion] || 'bg-slate-600 text-slate-200'}`}>{p.clasificacion}</span></td>
                      <td className="px-4 py-2">
                        <div className="flex items-center justify-end gap-2">
                          <Selector keyName={`p:${p.producto_id}`} />
                          <button onClick={() => clasificarProducto(p)} disabled={busy} data-testid={`clasif-producto-btn-${i}`}
                            className="px-3 py-1.5 rounded-lg text-xs bg-emerald-600 hover:bg-emerald-500 text-white disabled:opacity-40">Aplicar</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="px-4 py-3 border-t border-slate-700 flex items-center justify-between">
                <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1} className="px-3 py-1.5 rounded-lg text-xs bg-slate-700 disabled:opacity-40 text-white">Anterior</button>
                <span className="text-xs text-slate-400">Página {page} / {Math.max(1, Math.ceil(total / 50))}</span>
                <button onClick={() => setPage((p) => p + 1)} disabled={page >= Math.ceil(total / 50)} className="px-3 py-1.5 rounded-lg text-xs bg-slate-700 disabled:opacity-40 text-white">Siguiente</button>
              </div>
            </div>
          )}
        </>
      )}
      {busy && <div className="fixed bottom-6 right-6 bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 flex items-center gap-2 text-white text-sm"><Loader2 className="h-4 w-4 animate-spin" /> Guardando…</div>}
    </div>
  );
}
