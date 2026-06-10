import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Upload, Link2, FileSpreadsheet, RefreshCw, Check, X, Download,
  Trash2, Plus, AlertTriangle, CheckCircle2, Clock, FileText
} from 'lucide-react';
import api from '@/lib/api';

const fmt = (v) => v === null || v === undefined ? '—'
  : new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(v);

const EstadoBadge = ({ estado }) => {
  const map = {
    PENDIENTE: { cls: 'bg-amber-100 text-amber-700', Icon: Clock },
    CONFIRMADO: { cls: 'bg-green-100 text-green-700', Icon: CheckCircle2 },
    RECHAZADO: { cls: 'bg-gray-100 text-gray-500', Icon: X },
    ERROR: { cls: 'bg-red-100 text-red-700', Icon: AlertTriangle },
  };
  const { cls, Icon } = map[estado] || map.ERROR;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${cls}`} data-testid={`estado-${estado}`}>
      <Icon className="w-3 h-3" /> {estado}
    </span>
  );
};

const TabIngestaCompetencia = ({ empresaId }) => {
  const [ingestas, setIngestas] = useState([]);
  const [seleccion, setSeleccion] = useState(null);
  const [loading, setLoading] = useState(false);
  const [subiendo, setSubiendo] = useState(false);
  const [url, setUrl] = useState('');
  const [msg, setMsg] = useState(null);
  const fileRef = useRef(null);

  const cargar = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.get(`/comercial/ingesta-competencia?empresa_id=${empresaId}`);
      setIngestas(r.data.ingestas || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [empresaId]);

  useEffect(() => { cargar(); }, [cargar]);

  const abrirDetalle = async (id) => {
    try {
      const r = await api.get(`/comercial/ingesta-competencia/${id}`);
      setSeleccion(r.data);
    } catch (e) { console.error(e); }
  };

  const subirArchivo = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setSubiendo(true); setMsg(null);
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('empresa_id', empresaId);
      fd.append('unidades_negocio_ids', String(empresaId));
      const r = await api.post('/comercial/ingesta-competencia/upload', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setMsg({ tipo: r.data.estado === 'ERROR' ? 'error' : 'ok', texto: r.data.mensaje || `Extraídas ${r.data.total_filas} filas` });
      await cargar();
      setSeleccion(r.data);
    } catch (err) {
      setMsg({ tipo: 'error', texto: err.response?.data?.detail || 'Error al subir' });
    } finally {
      setSubiendo(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  const ingerirLink = async () => {
    if (!url.trim()) return;
    setSubiendo(true); setMsg(null);
    try {
      const r = await api.post('/comercial/ingesta-competencia/link', {
        empresa_id: empresaId, unidades_negocio_ids: String(empresaId), url: url.trim(),
      });
      setMsg({ tipo: r.data.estado === 'ERROR' ? 'error' : 'ok', texto: r.data.mensaje || `Extraídas ${r.data.total_filas} filas` });
      setUrl('');
      await cargar();
      setSeleccion(r.data);
    } catch (err) {
      setMsg({ tipo: 'error', texto: err.response?.data?.detail || 'Error con el link' });
    } finally { setSubiendo(false); }
  };

  const descargarPlantilla = async () => {
    try {
      const r = await api.get('/comercial/ingesta-competencia/plantilla', { responseType: 'blob' });
      const u = window.URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement('a');
      a.href = u; a.download = 'plantilla_ingesta_competencia.xlsx'; a.click();
      window.URL.revokeObjectURL(u);
    } catch (e) { console.error(e); }
  };

  return (
    <div className="space-y-5" data-testid="tab-ingesta-competencia">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800 flex items-start gap-2">
        <FileText className="w-4 h-4 mt-0.5 flex-shrink-0" />
        <span>Alimenta datos de competencia cuando falten. <strong>Excel/CSV</strong> usa la plantilla directa; <strong>PDF, imagen, Word o link</strong> se procesan con IA (Gemini). Todo queda en revisión antes de insertarse.</span>
      </div>

      {/* Acciones de carga */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="border border-gray-200 rounded-lg p-4 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-gray-700 font-medium text-sm"><Upload className="w-4 h-4 text-purple-600" /> Subir adjunto</div>
          <p className="text-xs text-gray-500">Excel, CSV, PDF, imagen (JPG/PNG) o Word.</p>
          <input ref={fileRef} type="file" accept=".xlsx,.xls,.csv,.pdf,.png,.jpg,.jpeg,.webp,.docx,.txt" onChange={subirArchivo} disabled={subiendo} data-testid="input-archivo" className="text-xs" />
        </div>
        <div className="border border-gray-200 rounded-lg p-4 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-gray-700 font-medium text-sm"><Link2 className="w-4 h-4 text-purple-600" /> Desde un link</div>
          <input type="url" placeholder="https://menu-competidor.com" value={url} onChange={(e) => setUrl(e.target.value)} data-testid="input-link" className="border border-gray-200 rounded px-2 py-1 text-sm" />
          <button onClick={ingerirLink} disabled={subiendo || !url.trim()} data-testid="btn-ingerir-link" className="inline-flex items-center justify-center gap-1 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white text-sm rounded px-3 py-1.5">
            {subiendo ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />} Procesar
          </button>
        </div>
        <div className="border border-gray-200 rounded-lg p-4 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-gray-700 font-medium text-sm"><FileSpreadsheet className="w-4 h-4 text-green-600" /> Plantilla</div>
          <p className="text-xs text-gray-500">Descarga el formato Excel para carga directa.</p>
          <button onClick={descargarPlantilla} data-testid="btn-plantilla" className="inline-flex items-center justify-center gap-1 border border-gray-300 hover:bg-gray-50 text-sm rounded px-3 py-1.5">
            <Download className="w-4 h-4" /> Descargar plantilla
          </button>
        </div>
      </div>

      {subiendo && <div className="text-sm text-purple-600 flex items-center gap-2"><RefreshCw className="w-4 h-4 animate-spin" /> Procesando (la IA puede tardar unos segundos)…</div>}
      {msg && (
        <div className={`text-sm rounded-lg p-3 ${msg.tipo === 'error' ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-green-50 text-green-700 border border-green-200'}`} data-testid="msg-ingesta">
          {msg.texto}
        </div>
      )}

      {/* Detalle / preview de la seleccionada */}
      {seleccion && (
        <PreviewIngesta ingesta={seleccion} onClose={() => setSeleccion(null)} onResuelta={async () => { await cargar(); setSeleccion(null); }} />
      )}

      {/* Historial */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-semibold text-gray-800 text-sm">Historial de ingestas</h4>
          <button onClick={cargar} className="text-sm text-purple-600 hover:text-purple-800 inline-flex items-center gap-1" data-testid="btn-refrescar-ingestas"><RefreshCw className="w-4 h-4" /> Refrescar</button>
        </div>
        <div className="overflow-x-auto border border-gray-200 rounded-lg">
          <table className="min-w-full text-sm" data-testid="tabla-ingestas">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="text-left px-3 py-2">Fuente</th>
                <th className="text-left px-3 py-2">Origen</th>
                <th className="text-center px-3 py-2">Filas</th>
                <th className="text-center px-3 py-2">Estado</th>
                <th className="text-left px-3 py-2">Fecha</th>
                <th className="text-center px-3 py-2"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {ingestas.length === 0 && !loading && (
                <tr><td colSpan={6} className="text-center py-8 text-gray-400">Sin ingestas aún</td></tr>
              )}
              {ingestas.map((i) => (
                <tr key={i.ingesta_id} className="hover:bg-gray-50" data-testid={`fila-ingesta-${i.ingesta_id}`}>
                  <td className="px-3 py-2 text-gray-800 max-w-[220px] truncate">{i.archivo_nombre || i.fuente_url || '—'}</td>
                  <td className="px-3 py-2 text-gray-500">{i.origen} {i.metodo_extraccion === 'IA_GEMINI' && <span className="text-purple-500">· IA</span>}</td>
                  <td className="px-3 py-2 text-center">{i.total_filas}</td>
                  <td className="px-3 py-2 text-center"><EstadoBadge estado={i.estado} /></td>
                  <td className="px-3 py-2 text-gray-500 text-xs">{i.fecha_creacion?.slice(0, 16).replace('T', ' ')}</td>
                  <td className="px-3 py-2 text-center">
                    <button onClick={() => abrirDetalle(i.ingesta_id)} className="text-purple-600 hover:text-purple-800 text-xs" data-testid={`btn-ver-${i.ingesta_id}`}>Ver</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Preview editable + confirmar/rechazar
const PreviewIngesta = ({ ingesta, onClose, onResuelta }) => {
  const [filas, setFilas] = useState(ingesta.filas || []);
  const [busy, setBusy] = useState(false);
  const editable = ingesta.estado === 'PENDIENTE' || ingesta.estado === 'ERROR';

  useEffect(() => { setFilas(ingesta.filas || []); }, [ingesta]);

  const upd = (idx, campo, val) => setFilas((f) => f.map((r, i) => i === idx ? { ...r, [campo]: campo === 'precio' ? val : val } : r));
  const quitar = (idx) => setFilas((f) => f.filter((_, i) => i !== idx));

  const guardarYConfirmar = async () => {
    setBusy(true);
    try {
      await api.put(`/comercial/ingesta-competencia/${ingesta.ingesta_id}/filas`, {
        filas: filas.map((r) => ({ ...r, precio: parseFloat(r.precio) || 0 })),
      });
      await api.post(`/comercial/ingesta-competencia/${ingesta.ingesta_id}/confirmar`);
      await onResuelta();
    } catch (e) { console.error(e); } finally { setBusy(false); }
  };

  const rechazar = async () => {
    setBusy(true);
    try { await api.post(`/comercial/ingesta-competencia/${ingesta.ingesta_id}/rechazar`); await onResuelta(); }
    catch (e) { console.error(e); } finally { setBusy(false); }
  };

  return (
    <div className="border border-purple-200 rounded-lg p-4 bg-purple-50/40" data-testid="preview-ingesta">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h4 className="font-semibold text-gray-800 text-sm">Revisión: {ingesta.archivo_nombre || ingesta.fuente_url || ingesta.origen}</h4>
          <EstadoBadge estado={ingesta.estado} />
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600" data-testid="btn-cerrar-preview"><X className="w-4 h-4" /></button>
      </div>
      {ingesta.mensaje && <div className="text-xs text-amber-700 mb-2">{ingesta.mensaje}</div>}

      <div className="overflow-x-auto bg-white rounded border border-gray-200">
        <table className="min-w-full text-sm" data-testid="tabla-preview-filas">
          <thead className="bg-gray-50 text-gray-600">
            <tr>
              <th className="text-left px-2 py-1.5">Competidor</th>
              <th className="text-left px-2 py-1.5">Categoría</th>
              <th className="text-left px-2 py-1.5">Producto</th>
              <th className="text-right px-2 py-1.5">Precio</th>
              {editable && <th className="px-2 py-1.5"></th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filas.length === 0 && <tr><td colSpan={5} className="text-center py-4 text-gray-400">Sin filas</td></tr>}
            {filas.map((r, idx) => (
              <tr key={idx}>
                <td className="px-2 py-1">{editable ? <input value={r.competidor || ''} onChange={(e) => upd(idx, 'competidor', e.target.value)} className="w-full border border-gray-200 rounded px-1 py-0.5 text-xs" /> : r.competidor}</td>
                <td className="px-2 py-1">{editable ? <input value={r.categoria || ''} onChange={(e) => upd(idx, 'categoria', e.target.value)} className="w-full border border-gray-200 rounded px-1 py-0.5 text-xs" /> : r.categoria}</td>
                <td className="px-2 py-1">{editable ? <input value={r.producto || ''} onChange={(e) => upd(idx, 'producto', e.target.value)} className="w-full border border-gray-200 rounded px-1 py-0.5 text-xs" /> : r.producto}</td>
                <td className="px-2 py-1 text-right">{editable ? <input type="number" value={r.precio} onChange={(e) => upd(idx, 'precio', e.target.value)} className="w-20 border border-gray-200 rounded px-1 py-0.5 text-xs text-right" /> : fmt(r.precio)}</td>
                {editable && <td className="px-2 py-1 text-center"><button onClick={() => quitar(idx)} className="text-red-400 hover:text-red-600"><Trash2 className="w-3.5 h-3.5" /></button></td>}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editable && (
        <div className="flex gap-2 mt-3 justify-end">
          <button onClick={rechazar} disabled={busy} data-testid="btn-rechazar" className="inline-flex items-center gap-1 border border-gray-300 hover:bg-gray-100 text-sm rounded px-3 py-1.5 disabled:opacity-50"><X className="w-4 h-4" /> Rechazar</button>
          <button onClick={guardarYConfirmar} disabled={busy || filas.length === 0} data-testid="btn-confirmar" className="inline-flex items-center gap-1 bg-green-600 hover:bg-green-700 text-white text-sm rounded px-3 py-1.5 disabled:opacity-50">
            {busy ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />} Confirmar e insertar
          </button>
        </div>
      )}
      {ingesta.estado === 'CONFIRMADO' && (
        <div className="text-xs text-green-700 mt-2" data-testid="resumen-confirmado">Insertados: {ingesta.competidores_creados} competidores · {ingesta.items_creados} productos.</div>
      )}
    </div>
  );
};

export default TabIngestaCompetencia;
