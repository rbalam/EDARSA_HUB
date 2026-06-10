import React, { useState, useEffect, useCallback } from 'react';
import * as XLSX from 'xlsx';
import { toast } from 'sonner';
import {
  Package, RefreshCw, Pencil, Upload, Search, AlertTriangle,
  CheckCircle2, XCircle, ChevronLeft, ChevronRight, Filter
} from 'lucide-react';

import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Switch } from '../../components/ui/switch';
import { Textarea } from '../../components/ui/textarea';
import { Badge } from '../../components/ui/badge';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription
} from '../../components/ui/dialog';

import api from '@/lib/api';
import { fetchUnidadesNegocio } from '../../services/unidadesNegocioService';
import { ExportButtons } from '../../portal-inteligencia/components/ExportButtons';

const PAGE_SIZE = 50;

const EDITABLES = [
  { key: 'grupo_comercial', label: 'Grupo Comercial', type: 'text' },
  { key: 'casa_comercial', label: 'Casa Comercial', type: 'text' },
  { key: 'marca', label: 'Marca', type: 'text' },
  { key: 'categoria', label: 'Categoría', type: 'text' },
  { key: 'subcategoria', label: 'Subcategoría', type: 'text' },
  { key: 'tipo_alcohol', label: 'Tipo de Alcohol', type: 'text' },
  { key: 'grado_alcohol', label: 'Grado Alcohol (°)', type: 'number' },
  { key: 'presentacion_ml', label: 'Presentación (ml)', type: 'number' },
  { key: 'presentacion_texto', label: 'Presentación (texto)', type: 'text' },
  { key: 'ean', label: 'EAN', type: 'text' },
  { key: 'imagen_url', label: 'Imagen URL', type: 'text' },
  { key: 'precio_venta', label: 'Precio Venta', type: 'number' },
  { key: 'confianza', label: 'Confianza (0-1)', type: 'number' },
  { key: 'observaciones', label: 'Observaciones', type: 'textarea' },
];

const num = (v) => (v == null || v === '' ? '—' : Number(v).toLocaleString('es-MX'));
const money = (v) => (v == null || v === '' || Number(v) < 0 ? '—' : `$${Number(v).toLocaleString('es-MX', { minimumFractionDigits: 2 })}`);

export default function CatalogoEnriquecido() {
  const [unidades, setUnidades] = useState([]);
  const [catalogos, setCatalogos] = useState({ grupos_comerciales: [], marcas: [], categorias: [], tipos_alcohol: [], indicadores: {} });

  const [filtros, setFiltros] = useState({
    unidad: '', grupo_comercial: '', marca: '', categoria: '', tipo_alcohol: '',
    es_alcoholico: '', requiere_validacion: '', activo: '', texto_busqueda: '',
  });

  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);

  const [editItem, setEditItem] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [saving, setSaving] = useState(false);

  const [importOpen, setImportOpen] = useState(false);
  const [importRows, setImportRows] = useState([]);
  const [importName, setImportName] = useState('');
  const [importing, setImporting] = useState(false);

  useEffect(() => {
    fetchUnidadesNegocio().then(d => setUnidades(d || [])).catch(() => setUnidades([]));
    api.get('/comercial/productos-enriquecidos/catalogos/filtros')
      .then(r => setCatalogos(r.data || {}))
      .catch(() => {});
  }, []);

  const loadItems = useCallback(async (off = 0) => {
    setLoading(true);
    try {
      const params = { limit: PAGE_SIZE, offset: off };
      if (filtros.unidad) params.unidad = filtros.unidad;
      if (filtros.grupo_comercial) params.grupo_comercial = filtros.grupo_comercial;
      if (filtros.marca) params.marca = filtros.marca;
      if (filtros.categoria) params.categoria = filtros.categoria;
      if (filtros.tipo_alcohol) params.tipo_alcohol = filtros.tipo_alcohol;
      if (filtros.es_alcoholico !== '') params.es_alcoholico = filtros.es_alcoholico;
      if (filtros.requiere_validacion !== '') params.requiere_validacion = filtros.requiere_validacion;
      if (filtros.activo !== '') params.activo = filtros.activo;
      if (filtros.texto_busqueda) params.texto_busqueda = filtros.texto_busqueda;

      const { data } = await api.get('/comercial/productos-enriquecidos', { params });
      setItems(data.items || []);
      setTotal(data.total || 0);
      setOffset(off);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error al cargar el catálogo enriquecido');
    } finally {
      setLoading(false);
    }
  }, [filtros]);

  useEffect(() => { loadItems(0); }, [loadItems]);

  const openEdit = (item) => {
    setEditItem(item);
    const f = {};
    EDITABLES.forEach(({ key }) => { f[key] = item[key] ?? ''; });
    f.es_alcoholico = !!item.es_alcoholico;
    f.requiere_validacion = !!item.requiere_validacion;
    setEditForm(f);
  };

  const saveEdit = async () => {
    setSaving(true);
    try {
      const payload = {};
      EDITABLES.forEach(({ key, type }) => {
        let v = editForm[key];
        if (v === '' ) v = null;
        else if (type === 'number' && v != null) v = Number(v);
        payload[key] = v;
      });
      payload.es_alcoholico = !!editForm.es_alcoholico;
      payload.requiere_validacion = !!editForm.requiere_validacion;
      await api.put(`/comercial/productos-enriquecidos/${editItem.id}`, payload);
      toast.success('Producto actualizado');
      setEditItem(null);
      loadItems(offset);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'No autorizado o error al guardar');
    } finally {
      setSaving(false);
    }
  };

  const toggleActivo = async (item) => {
    try {
      const action = item.activo ? 'desactivar' : 'activar';
      await api.patch(`/comercial/productos-enriquecidos/${item.id}/${action}`);
      toast.success(`Producto ${item.activo ? 'desactivado' : 'activado'}`);
      loadItems(offset);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'No autorizado');
    }
  };

  const handleImportFile = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImportName(file.name);
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const wb = XLSX.read(ev.target.result, { type: 'array' });
        const ws = wb.Sheets[wb.SheetNames[0]];
        const rows = XLSX.utils.sheet_to_json(ws, { defval: null });
        setImportRows(rows);
        toast.success(`${rows.length} filas leídas de ${file.name}`);
      } catch (err) {
        toast.error('No se pudo leer el archivo Excel');
        setImportRows([]);
      }
    };
    reader.readAsArrayBuffer(file);
  };

  const submitImport = async () => {
    if (!importRows.length) { toast.error('No hay filas para importar'); return; }
    setImporting(true);
    try {
      const { data } = await api.post('/comercial/productos-enriquecidos/importar', importRows);
      toast.success(`Importación OK: ${data.insertadas ?? 0} nuevas, ${data.actualizadas ?? 0} actualizadas, ${data.omitidas ?? 0} omitidas`);
      setImportOpen(false);
      setImportRows([]);
      setImportName('');
      loadItems(0);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error al importar');
    } finally {
      setImporting(false);
    }
  };

  const setF = (k, v) => setFiltros(prev => ({ ...prev, [k]: v }));

  const ind = catalogos.indicadores || {};
  const exportColumns = [
    { key: 'nombre_producto', label: 'Producto' },
    { key: 'codigo_producto_origen', label: 'Código' },
    { key: 'unidad_codigo', label: 'Unidad' },
    { key: 'familia_origen', label: 'Familia Origen' },
    { key: 'grupo_comercial', label: 'Grupo Comercial' },
    { key: 'marca', label: 'Marca' },
    { key: 'categoria', label: 'Categoría' },
    { key: 'tipo_alcohol', label: 'Tipo Alcohol' },
    { key: 'grado_alcohol', label: 'Grado' },
    { key: 'presentacion_ml', label: 'Pres. (ml)' },
    { key: 'precio_venta', label: 'Precio Venta' },
    { key: 'requiere_validacion', label: 'Requiere Validación' },
    { key: 'activo', label: 'Activo' },
  ];

  const pageStart = total ? offset + 1 : 0;
  const pageEnd = Math.min(offset + PAGE_SIZE, total);

  return (
    <div className="p-6 space-y-5" data-testid="catalogo-enriquecido-page">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2 text-slate-800">
            <Package className="w-6 h-6 text-emerald-600" /> Catálogo Enriquecido
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Catálogo comercial de productos · SQL-First · {total.toLocaleString('es-MX')} registros
          </p>
        </div>
        <div className="flex flex-wrap gap-2 items-center">
          <ExportButtons
            filename="catalogo_enriquecido"
            title="Catálogo Enriquecido de Productos"
            testid="catalogo-export"
            columns={exportColumns}
            rows={items.map(i => ({
              ...i,
              requiere_validacion: i.requiere_validacion ? 'SÍ' : 'NO',
              activo: i.activo ? 'SÍ' : 'NO',
            }))}
          />
          <Button variant="outline" size="sm" onClick={() => setImportOpen(true)} data-testid="btn-importar">
            <Upload className="w-4 h-4 mr-1" /> Importar
          </Button>
          <Button variant="outline" size="sm" onClick={() => loadItems(offset)} disabled={loading} data-testid="btn-refrescar">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* Indicadores */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <IndCard label="Total productos" value={ind.total} icon={<Package className="w-4 h-4 text-slate-400" />} />
        <IndCard label="Requieren validación" value={ind.requiere_validacion} icon={<AlertTriangle className="w-4 h-4 text-amber-500" />} accent="amber" />
        <IndCard label="Sin marca" value={ind.sin_marca} icon={<XCircle className="w-4 h-4 text-rose-400" />} />
        <IndCard label="Sin presentación" value={ind.sin_presentacion} icon={<XCircle className="w-4 h-4 text-rose-400" />} />
      </div>

      {/* Filtros */}
      <div className="bg-white border rounded-xl p-4 shadow-sm">
        <div className="flex items-center gap-2 mb-3 text-slate-600 text-sm font-medium">
          <Filter className="w-4 h-4" /> Filtros
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-3">
          <div className="relative md:col-span-2 lg:col-span-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <Input
              placeholder="Buscar producto / código..."
              value={filtros.texto_busqueda}
              onChange={(e) => setF('texto_busqueda', e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && loadItems(0)}
              className="pl-9"
              data-testid="filtro-busqueda"
            />
          </div>
          <Sel label="Unidad" value={filtros.unidad} onChange={(v) => setF('unidad', v)} testid="filtro-unidad"
            options={[{ v: '', t: 'Todas las unidades' }, ...unidades.map(u => ({ v: u.codigo, t: u.nombre }))]} />
          <Sel label="Grupo Comercial" value={filtros.grupo_comercial} onChange={(v) => setF('grupo_comercial', v)} testid="filtro-grupo"
            options={[{ v: '', t: 'Todos' }, ...(catalogos.grupos_comerciales || []).map(x => ({ v: x, t: x }))]} />
          <Sel label="Marca" value={filtros.marca} onChange={(v) => setF('marca', v)} testid="filtro-marca"
            options={[{ v: '', t: 'Todas' }, ...(catalogos.marcas || []).map(x => ({ v: x, t: x }))]} />
          <Sel label="Categoría" value={filtros.categoria} onChange={(v) => setF('categoria', v)} testid="filtro-categoria"
            options={[{ v: '', t: 'Todas' }, ...(catalogos.categorias || []).map(x => ({ v: x, t: x }))]} />
          <Sel label="Tipo Alcohol" value={filtros.tipo_alcohol} onChange={(v) => setF('tipo_alcohol', v)} testid="filtro-tipo-alcohol"
            options={[{ v: '', t: 'Todos' }, ...(catalogos.tipos_alcohol || []).map(x => ({ v: x, t: x }))]} />
          <Sel label="Requiere Validación" value={filtros.requiere_validacion} onChange={(v) => setF('requiere_validacion', v)} testid="filtro-validacion"
            options={[{ v: '', t: 'Todos' }, { v: 'true', t: 'Sí' }, { v: 'false', t: 'No' }]} />
          <Sel label="Estado" value={filtros.activo} onChange={(v) => setF('activo', v)} testid="filtro-activo"
            options={[{ v: '', t: 'Todos' }, { v: 'true', t: 'Activos' }, { v: 'false', t: 'Inactivos' }]} />
          <div className="flex items-end">
            <Button onClick={() => loadItems(0)} className="w-full" data-testid="btn-aplicar-filtros">
              Aplicar
            </Button>
          </div>
        </div>
      </div>

      {/* Tabla */}
      <div className="bg-white border rounded-xl shadow-sm overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b">
            <tr className="text-left text-slate-600">
              <th className="px-3 py-2 font-medium">Producto</th>
              <th className="px-3 py-2 font-medium">Código</th>
              <th className="px-3 py-2 font-medium">Unidad</th>
              <th className="px-3 py-2 font-medium">Grupo Comercial</th>
              <th className="px-3 py-2 font-medium">Marca</th>
              <th className="px-3 py-2 font-medium">Tipo Alcohol</th>
              <th className="px-3 py-2 font-medium text-right">Grado</th>
              <th className="px-3 py-2 font-medium text-right">ml</th>
              <th className="px-3 py-2 font-medium text-right">Precio</th>
              <th className="px-3 py-2 font-medium text-center">Validar</th>
              <th className="px-3 py-2 font-medium text-center">Estado</th>
              <th className="px-3 py-2 font-medium text-center">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={12} className="px-3 py-10 text-center text-slate-400">Cargando...</td></tr>
            ) : items.length === 0 ? (
              <tr><td colSpan={12} className="px-3 py-10 text-center text-slate-400">Sin resultados</td></tr>
            ) : items.map((it) => (
              <tr key={it.id} className="border-b hover:bg-slate-50" data-testid={`producto-row-${it.id}`}>
                <td className="px-3 py-2 max-w-[260px] truncate" title={it.nombre_producto}>{it.nombre_producto}</td>
                <td className="px-3 py-2 text-slate-500">{it.codigo_producto_origen || '—'}</td>
                <td className="px-3 py-2 text-slate-500">{it.unidad_codigo || '—'}</td>
                <td className="px-3 py-2">{it.grupo_comercial || <span className="text-rose-400">—</span>}</td>
                <td className="px-3 py-2">{it.marca || <span className="text-rose-400">—</span>}</td>
                <td className="px-3 py-2">{it.tipo_alcohol || '—'}</td>
                <td className="px-3 py-2 text-right">{it.grado_alcohol != null ? `${it.grado_alcohol}°` : '—'}</td>
                <td className="px-3 py-2 text-right">{num(it.presentacion_ml)}</td>
                <td className="px-3 py-2 text-right">{money(it.precio_venta)}</td>
                <td className="px-3 py-2 text-center">
                  {it.requiere_validacion
                    ? <Badge className="bg-amber-100 text-amber-700 hover:bg-amber-100">Sí</Badge>
                    : <span className="text-slate-300">—</span>}
                </td>
                <td className="px-3 py-2 text-center">
                  {it.activo
                    ? <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100">Activo</Badge>
                    : <Badge variant="secondary">Inactivo</Badge>}
                </td>
                <td className="px-3 py-2">
                  <div className="flex items-center justify-center gap-1">
                    <Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => openEdit(it)} data-testid={`btn-editar-${it.id}`}>
                      <Pencil className="w-3.5 h-3.5" />
                    </Button>
                    <Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => toggleActivo(it)} data-testid={`btn-toggle-${it.id}`}>
                      {it.activo ? <XCircle className="w-3.5 h-3.5 text-rose-500" /> : <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />}
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Paginación */}
      <div className="flex items-center justify-between text-sm text-slate-500">
        <span data-testid="paginacion-info">{pageStart}–{pageEnd} de {total.toLocaleString('es-MX')}</span>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" disabled={offset === 0 || loading} onClick={() => loadItems(Math.max(0, offset - PAGE_SIZE))} data-testid="btn-prev">
            <ChevronLeft className="w-4 h-4" /> Anterior
          </Button>
          <Button variant="outline" size="sm" disabled={pageEnd >= total || loading} onClick={() => loadItems(offset + PAGE_SIZE)} data-testid="btn-next">
            Siguiente <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Dialog Editar */}
      <Dialog open={!!editItem} onOpenChange={(o) => !o && setEditItem(null)}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto" data-testid="dialog-editar">
          <DialogHeader>
            <DialogTitle>Editar enriquecimiento</DialogTitle>
            <DialogDescription className="truncate">{editItem?.nombre_producto}</DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 py-2">
            {EDITABLES.map(({ key, label, type }) => (
              <div key={key} className={type === 'textarea' ? 'md:col-span-2' : ''}>
                <Label className="text-xs text-slate-500">{label}</Label>
                {type === 'textarea' ? (
                  <Textarea value={editForm[key] ?? ''} onChange={(e) => setEditForm(p => ({ ...p, [key]: e.target.value }))} rows={2} />
                ) : (
                  <Input type={type === 'number' ? 'number' : 'text'} value={editForm[key] ?? ''} onChange={(e) => setEditForm(p => ({ ...p, [key]: e.target.value }))} data-testid={`edit-${key}`} />
                )}
              </div>
            ))}
            <div className="flex items-center justify-between border rounded-lg px-3 py-2">
              <Label className="text-sm">Es alcohólico</Label>
              <Switch checked={!!editForm.es_alcoholico} onCheckedChange={(v) => setEditForm(p => ({ ...p, es_alcoholico: v }))} data-testid="edit-es-alcoholico" />
            </div>
            <div className="flex items-center justify-between border rounded-lg px-3 py-2">
              <Label className="text-sm">Requiere validación</Label>
              <Switch checked={!!editForm.requiere_validacion} onCheckedChange={(v) => setEditForm(p => ({ ...p, requiere_validacion: v }))} data-testid="edit-requiere-validacion" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditItem(null)}>Cancelar</Button>
            <Button onClick={saveEdit} disabled={saving} data-testid="btn-guardar-edicion">
              {saving ? 'Guardando...' : 'Guardar'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog Importar */}
      <Dialog open={importOpen} onOpenChange={setImportOpen}>
        <DialogContent data-testid="dialog-importar">
          <DialogHeader>
            <DialogTitle>Importación masiva (UPSERT por producto_id)</DialogTitle>
            <DialogDescription>
              Sube un Excel (.xlsx) con columnas que coincidan con los campos del catálogo
              (ej: producto_id, grupo_comercial, marca, categoria, tipo_alcohol, presentacion_ml...).
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <input type="file" accept=".xlsx,.xls" onChange={handleImportFile} data-testid="import-file" className="block w-full text-sm text-slate-600 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100" />
            {importName && (
              <div className="text-sm text-slate-600 bg-slate-50 border rounded-lg px-3 py-2">
                <strong>{importName}</strong> — {importRows.length} filas listas para importar
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setImportOpen(false)}>Cancelar</Button>
            <Button onClick={submitImport} disabled={importing || !importRows.length} data-testid="btn-confirmar-importar">
              {importing ? 'Importando...' : `Importar ${importRows.length || ''}`}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function IndCard({ label, value, icon, accent }) {
  return (
    <div className={`bg-white border rounded-xl p-3 shadow-sm ${accent === 'amber' ? 'border-amber-200' : ''}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs text-slate-500">{label}</span>
        {icon}
      </div>
      <div className="text-xl font-bold text-slate-800 mt-1">{value != null ? Number(value).toLocaleString('es-MX') : '—'}</div>
    </div>
  );
}

function Sel({ label, value, onChange, options, testid }) {
  return (
    <div>
      <Label className="text-xs text-slate-500">{label}</Label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        data-testid={testid}
        className="h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
      >
        {options.map((o, i) => <option key={i} value={o.v}>{o.t}</option>)}
      </select>
    </div>
  );
}
