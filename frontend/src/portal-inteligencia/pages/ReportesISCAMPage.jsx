/**
 * Reportes ISCAM — Portal de Inteligencia Comercial.
 * Reportes sobre tablas CANÓNICAS (Sync_Sales + Finanzas_CortesCaja[_DetallePagos]).
 * - Selector de periodo por RANGO mes-año (Desde / Hasta).
 * - Agrupación por Año / Mes / Día + "Sin agrupar".
 * - Exportación a Excel y PDF de la vista actual.
 * - Drill-down por DOBLE CLIC.
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  FileBarChart, Loader2, X, Receipt, ClipboardList, CreditCard, ChevronRight,
  FileSpreadsheet, FileText, RefreshCw,
} from 'lucide-react';
import { apiGet, apiPost, ESTADO } from '../api/client';
import { exportToExcel, exportToPDF } from '../utils/exportUtils';

const money = (n) => (n ?? 0).toLocaleString('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 0 });
const money2 = (n) => (n ?? 0).toLocaleString('es-MX', { style: 'currency', currency: 'MXN', minimumFractionDigits: 2, maximumFractionDigits: 2 });
const num = (n) => (n ?? 0).toLocaleString('es-MX', { maximumFractionDigits: 2 });

const MESES = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
const NOW = new Date();
const YEARS = Array.from({ length: 4 }, (_, i) => NOW.getFullYear() - 3 + i);
const parseYmdUtc = (value) => {
  const [y, m, d] = String(value || '').split('-').map(Number);
  return new Date(Date.UTC(y, (m || 1) - 1, d || 1));
};
const ymdUtc = (value) => value.toISOString().slice(0, 10);
const formatDateMx = (value) => {
  if (!value) return 'Sin datos';
  const [y, m, d] = value.split('-');
  return `${d}/${m}/${y}`;
};
const splitDateChunks = (start, end, maxDays = 30) => {
  if (!start || !end) return [];
  const chunks = [];
  let cursor = parseYmdUtc(start);
  const last = parseYmdUtc(end);
  while (cursor <= last) {
    const chunkStart = new Date(cursor);
    const chunkEnd = new Date(cursor);
    chunkEnd.setUTCDate(chunkEnd.getUTCDate() + maxDays - 1);
    if (chunkEnd > last) chunkEnd.setTime(last.getTime());
    chunks.push([ymdUtc(chunkStart), ymdUtc(chunkEnd)]);
    cursor = new Date(chunkEnd);
    cursor.setUTCDate(cursor.getUTCDate() + 1);
  }
  return chunks;
};

const SUBTABS = [
  { id: 'periodos', label: 'Ventas por Periodo', icon: FileBarChart },
  { id: 'cuentas', label: 'Resumen de Cuentas', icon: Receipt },
  { id: 'comandas', label: 'Comandas de Venta', icon: ClipboardList },
  { id: 'formas', label: 'Formas de Pago (Corte)', icon: CreditCard },
  { id: 'pagos-ticket', label: 'Pagos por Ticket', icon: CreditCard },
];

// Opciones de agrupación por reporte
const GROUP_OPTS = {
  periodos: [{ id: 'dia', label: 'Día' }, { id: 'mes', label: 'Mes' }, { id: 'anio', label: 'Año' }],
  cuentas: [{ id: 'none', label: 'Sin agrupar' }, { id: 'dia', label: 'Día' }, { id: 'mes', label: 'Mes' }, { id: 'anio', label: 'Año' }],
  comandas: [{ id: 'none', label: 'Sin agrupar' }, { id: 'dia', label: 'Día' }, { id: 'mes', label: 'Mes' }, { id: 'anio', label: 'Año' }],
  formas: [{ id: 'none', label: 'Sin agrupar' }, { id: 'dia', label: 'Día' }, { id: 'mes', label: 'Mes' }, { id: 'anio', label: 'Año' }],
  'pagos-ticket': [{ id: 'none', label: 'Sin agrupar' }, { id: 'dia', label: 'Día' }, { id: 'mes', label: 'Mes' }, { id: 'anio', label: 'Año' }],
};
const DEFAULT_GROUP = { periodos: 'mes', cuentas: 'mes', comandas: 'mes', 'pagos-ticket': 'mes', formas: 'none' };

function Modal({ title, onClose, headerAction, children }) {
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-slate-800 border border-slate-700 rounded-xl w-full max-w-3xl max-h-[85vh] overflow-auto" onClick={(e) => e.stopPropagation()} data-testid="iscam-drill-modal">
        <div className="sticky top-0 bg-slate-800 border-b border-slate-700 px-5 py-3 flex items-center justify-between">
          <h3 className="text-white font-semibold text-sm">{title}</h3>
          <div className="flex items-center gap-2">
            {headerAction}
            <button onClick={onClose} className="text-slate-400 hover:text-white"><X className="h-4 w-4" /></button>
          </div>
        </div>
        <div className="p-4">{children}</div>
      </div>
    </div>
  );
}

const TH = ({ children, right }) => <th className={`px-3 py-2 text-xs font-medium text-slate-400 uppercase ${right ? 'text-right' : 'text-left'}`}>{children}</th>;
const TD = ({ children, right, mono }) => <td className={`px-3 py-2 text-sm text-slate-200 ${right ? 'text-right' : ''} ${mono ? 'font-mono' : ''}`}>{children}</td>;

// ---- Descriptor de columnas/filas para render genérico + export ----
function buildDescriptor(sub, groupBy, data) {
  const grouped = groupBy && groupBy !== 'none';
  if (sub === 'periodos') {
    return {
      title: 'Ventas por Periodo',
      columns: [
        { key: 'periodo', label: 'Periodo', tipo: 'text' },
        { key: 'venta_total', label: 'Venta Total', tipo: 'money' },
        { key: 'cheques', label: 'Cheques', tipo: 'int' },
        { key: 'cheque_promedio', label: 'Cheque Prom.', tipo: 'money' },
        { key: 'clientes', label: 'Clientes', tipo: 'int' },
        { key: 'consumo_promedio', label: 'Consumo Prom.', tipo: 'money' },
      ],
      rows: data?.periodos || [],
    };
  }
  if (sub === 'cuentas') {
    return grouped ? {
      title: 'Resumen de Cuentas (agrupado)',
      columns: [
        { key: 'periodo', label: 'Periodo', tipo: 'text' },
        { key: 'cuentas', label: 'Cuentas', tipo: 'int' },
        { key: 'personas', label: 'Personas', tipo: 'int' },
        { key: 'importe', label: 'Importe', tipo: 'money' },
        { key: 'cuenta_promedio', label: 'Cuenta Prom.', tipo: 'money' },
        { key: 'consumo_promedio', label: 'Consumo Prom.', tipo: 'money' },
      ],
      rows: data?.agrupado || [],
    } : {
      title: 'Resumen de Cuentas (detalle)',
      columns: [
        { key: 'folio', label: 'Folio', tipo: 'text' },
        { key: 'fecha', label: 'Fecha', tipo: 'text' },
        { key: 'personas', label: 'Personas', tipo: 'int' },
        { key: 'importe', label: 'Importe', tipo: 'money' },
        { key: 'estado', label: 'Estado', tipo: 'text' },
      ],
      rows: data?.cuentas || [],
    };
  }
  if (sub === 'comandas') {
    return grouped ? {
      title: 'Comandas de Venta (agrupado)',
      columns: [
        { key: 'periodo', label: 'Periodo', tipo: 'text' },
        { key: 'lineas', label: 'Líneas', tipo: 'int' },
        { key: 'tickets', label: 'Tickets', tipo: 'int' },
        { key: 'cantidad', label: 'Cantidad', tipo: 'num' },
        { key: 'importe', label: 'Importe', tipo: 'money' },
      ],
      rows: data?.agrupado || [],
    } : {
      title: 'Comandas de Venta (detalle)',
      columns: [
        { key: 'folio_cuenta', label: 'Folio Cuenta', tipo: 'text' },
        { key: 'fecha', label: 'Fecha', tipo: 'text' },
        { key: 'clave', label: 'Clave', tipo: 'text' },
        { key: 'descripcion', label: 'Descripción', tipo: 'text' },
        { key: 'cantidad', label: 'Cantidad', tipo: 'num' },
        { key: 'precio', label: 'Precio', tipo: 'money' },
        { key: 'importe', label: 'Importe', tipo: 'money' },
      ],
      rows: data?.comandas || [],
    };
  }
  if (sub === 'pagos-ticket') {
    return grouped ? {
      title: 'Pagos por Ticket (agrupado)',
      columns: [
        { key: 'periodo', label: 'Periodo', tipo: 'text' },
        { key: 'forma', label: 'Forma de Pago', tipo: 'text' },
        { key: 'tickets', label: 'Tickets', tipo: 'int' },
        { key: 'pagos', label: 'Pagos', tipo: 'int' },
        { key: 'importe', label: 'Importe', tipo: 'money' },
        { key: 'propina', label: 'Propina', tipo: 'money' },
      ],
      rows: data?.agrupado || [],
    } : {
      title: 'Pagos por Ticket (resumen por forma)',
      columns: [
        { key: 'forma', label: 'Forma de Pago', tipo: 'text' },
        { key: 'codigo', label: 'Código', tipo: 'text' },
        { key: 'tickets', label: 'Tickets', tipo: 'int' },
        { key: 'pagos', label: 'Pagos', tipo: 'int' },
        { key: 'importe', label: 'Importe', tipo: 'money' },
        { key: 'propina', label: 'Propina', tipo: 'money' },
      ],
      rows: data?.resumen_formas || [],
    };
  }
  // formas (corte)
  if (grouped) {
    return {
      title: 'Formas de Pago — Corte (agrupado)',
      columns: [
        { key: 'periodo', label: 'Periodo', tipo: 'text' },
        { key: 'cortes', label: 'Cortes', tipo: 'int' },
        { key: 'total', label: 'Total', tipo: 'money' },
        { key: 'efectivo', label: 'Efectivo', tipo: 'money' },
        { key: 'tarjeta', label: 'Tarjeta', tipo: 'money' },
        { key: 'amex', label: 'Amex', tipo: 'money' },
        { key: 'vales', label: 'Vales', tipo: 'money' },
        { key: 'otros', label: 'Otros', tipo: 'money' },
        { key: 'propina', label: 'Propina', tipo: 'money' },
        { key: 'comision', label: 'Comisión', tipo: 'money' },
      ],
      rows: data?.agrupado || [],
    };
  }
  return {
    title: 'Formas de Pago (Corte de Caja)',
    columns: [
      { key: 'folio', label: 'Folio', tipo: 'text' },
      { key: 'fecha', label: 'Fecha', tipo: 'text' },
      { key: 'caja', label: 'Caja', tipo: 'text' },
      { key: 'total', label: 'Total', tipo: 'money' },
      { key: 'efectivo', label: 'Efectivo', tipo: 'money' },
      { key: 'tarjeta', label: 'Tarjeta', tipo: 'money' },
      { key: 'amex', label: 'Amex', tipo: 'money' },
      { key: 'vales', label: 'Vales', tipo: 'money' },
      { key: 'otros', label: 'Otros', tipo: 'money' },
      { key: 'propina', label: 'Propina', tipo: 'money' },
      { key: 'comision', label: 'Comisión', tipo: 'money' },
    ],
    rows: data?.cortes || [],
  };
}

function GenericTable({ columns, rows }) {
  if (!rows?.length) return <div className="px-4 py-10 text-center text-slate-400">Sin datos en el rango.</div>;
  return (
    <table className="w-full" data-testid="iscam-tabla-generica">
      <thead className="bg-slate-700/40"><tr>{columns.map((c) => <TH key={c.key} right={c.tipo !== 'text'}>{c.label}</TH>)}</tr></thead>
      <tbody className="divide-y divide-slate-700">
        {rows.map((r, i) => (
          <tr key={i} className="hover:bg-slate-700/30">
            {columns.map((c) => {
              const v = r[c.key];
              const disp = c.tipo === 'money' ? money(v) : c.tipo === 'num' ? num(v)
                : c.tipo === 'int' ? (v ?? 0) : ((v || '').toString().replace('T', ' ').slice(0, 16) || (v ?? ''));
              return <TD key={c.key} right={c.tipo !== 'text'} mono={c.key === 'folio' || c.key === 'codigo'}>{disp}</TD>;
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function ReportesISCAMPage({ unidadSeleccionada }) {
  const [sub, setSub] = useState('periodos');
  const [groupBy, setGroupBy] = useState(DEFAULT_GROUP.periodos);
  const [loading, setLoading] = useState(false);
  const [estado, setEstado] = useState(ESTADO.OK);
  const [data, setData] = useState(null);
  // Rango mes-año (default: últimos 12 meses)
  const ini = new Date(NOW.getFullYear(), NOW.getMonth() - 11, 1);
  const [desdeAnio, setDesdeAnio] = useState(ini.getFullYear());
  const [desdeMes, setDesdeMes] = useState(ini.getMonth() + 1);
  const [hastaAnio, setHastaAnio] = useState(NOW.getFullYear());
  const [hastaMes, setHastaMes] = useState(NOW.getMonth() + 1);
  const [drill, setDrill] = useState(null);
  const [freshness, setFreshness] = useState(null);
  const [freshnessLoading, setFreshnessLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState(null);

  const unidad = unidadSeleccionada;
  const sinUnidad = !unidad || unidad === 'todas';

  const desdeStr = `${desdeAnio}-${String(desdeMes).padStart(2, '0')}-01`;
  const lastDay = new Date(hastaAnio, hastaMes, 0).getDate();
  const hastaStr = `${hastaAnio}-${String(hastaMes).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`;

  const onChangeSub = (id) => { setSub(id); setGroupBy(DEFAULT_GROUP[id]); setData(null); };

  const getReportRequest = useCallback((extraParams = {}) => {
    let path;
    const params = { unidad, desde: desdeStr, hasta: hastaStr, ...extraParams };
    if (sub === 'periodos') { path = '/inteligencia/iscam/ventas-periodos'; params.group_by = groupBy; }
    else if (sub === 'cuentas') { path = '/inteligencia/iscam/cuentas'; params.group_by = groupBy; }
    else if (sub === 'comandas') { path = '/inteligencia/iscam/comandas'; params.group_by = groupBy; }
    else if (sub === 'pagos-ticket') { path = '/inteligencia/iscam/formas-pago/por-ticket'; params.group_by = groupBy; }
    else { path = '/inteligencia/iscam/formas-pago'; params.group_by = groupBy; }
    return { path, params };
  }, [sub, groupBy, unidad, desdeStr, hastaStr]);

  const fetchReport = useCallback(async () => {
    if (sinUnidad) { setData(null); return; }
    setLoading(true); setEstado(ESTADO.OK);
    const { path, params } = getReportRequest();
    const res = await apiGet(path, params);
    setEstado(res.estado);
    setData(res.estado === ESTADO.OK ? res.data : null);
    setLoading(false);
  }, [getReportRequest, sinUnidad]);

  const fetchFreshness = useCallback(async () => {
    if (sinUnidad) { setFreshness(null); return; }
    setFreshnessLoading(true);
    const res = await apiGet('/inteligencia/iscam/freshness', { unidad, desde: desdeStr, hasta: hastaStr });
    setFreshness(res.estado === ESTADO.OK ? res.data : null);
    setFreshnessLoading(false);
  }, [sinUnidad, unidad, desdeStr, hastaStr]);

  useEffect(() => {
    fetchReport();
    fetchFreshness();
  }, [fetchReport, fetchFreshness]);

  const syncMissingClosedDays = async () => {
    const headerGap = Boolean(freshness?.stale);
    const detailGap = Boolean(freshness?.detail_stale);
    const detailOnly = detailGap && !headerGap;
    const syncFrom = detailOnly
      ? freshness?.detail_missing_from
      : (freshness?.missing_from || freshness?.detail_missing_from);
    const syncTo = detailOnly
      ? freshness?.detail_missing_to
      : (freshness?.missing_to || freshness?.detail_missing_to);
    if (!(headerGap || detailGap) || !syncFrom || !syncTo || syncing) return;
    setSyncing(true);
    setSyncMessage(null);
    try {
      const chunks = splitDateChunks(syncFrom, syncTo, 1);
      for (const [fechaInicio, fechaFin] of chunks) {
        const basePayload = {
          tipo_sync: 'comercial_ventas_cerradas',
          unidad_negocio_id: unidad,
          fecha_inicio: fechaInicio,
          fecha_fin: fechaFin,
          motivo: detailOnly ? 'ISCAM sincronizar detalle faltante' : 'ISCAM sincronizar dias cerrados faltantes',
          detail_only: detailOnly,
        };
        const dry = await apiPost('/admin/scheduler/resync/execute', { ...basePayload, dry_run: true }, { timeout: 120000 });
        if (dry.estado !== ESTADO.OK || dry.data?.success !== true) {
          const dryError = dry.data?.error_message || dry.data?.resultado?.error_message || dry.data?.detail || dry.mensaje;
          throw new Error(dryError || `No se pudo validar la sincronización para ${fechaInicio} a ${fechaFin}`);
        }
        const real = await apiPost('/admin/scheduler/resync/execute', { ...basePayload, dry_run: false }, { timeout: 120000 });
        if (real.estado !== ESTADO.OK || real.data?.success !== true) {
          const realError = real.data?.error_message || real.data?.resultado?.error_message || real.data?.detail || real.mensaje;
          throw new Error(realError || `No se pudo completar la sincronización para ${fechaInicio} a ${fechaFin}`);
        }
      }
      await Promise.all([fetchReport(), fetchFreshness()]);
      setSyncMessage({
        tipo: 'ok',
        texto: detailOnly ? 'Detalle ISCAM sincronizado y validado.' : 'Sincronización de faltantes completada.',
      });
    } catch (error) {
      setSyncMessage({ tipo: 'error', texto: error?.message || 'No se pudo sincronizar el rango faltante.' });
    } finally {
      setSyncing(false);
    }
  };

  // ---- Drill-downs ----
  const drillProductos = async (periodo) => {
    setDrill({ tipo: 'productos', titulo: `Productos vendidos — ${periodo}`, items: [], loading: true, periodo });
    const res = await apiGet('/inteligencia/iscam/ventas-periodos/productos', { unidad, periodo, group_by: groupBy });
    setDrill((d) => ({ ...d, items: res.data?.productos || [], resumen: res.data?.resumen_conciliacion || null, loading: false }));
  };
  const drillTickets = async (periodo, producto, nombre) => {
    setDrill({ tipo: 'tickets', titulo: `Tickets con "${nombre}" — ${periodo}`, items: [], loading: true });
    const res = await apiGet('/inteligencia/iscam/ventas-periodos/tickets', { unidad, periodo, producto, group_by: groupBy });
    setDrill((d) => ({ ...d, items: res.data?.tickets || [], loading: false }));
  };
  const drillCuenta = async (folio) => {
    setDrill({ tipo: 'cuenta', titulo: `Detalle de cuenta — Folio ${folio}`, items: [], loading: true });
    const res = await apiGet('/inteligencia/iscam/cuentas/detalle', { unidad, folio });
    setDrill((d) => ({ ...d, items: res.data?.productos || [], ajustes: res.data?.ajustes || [], resumen: res.data?.resumen_conciliacion || null, loading: false }));
  };
  const drillTiposServicio = async (periodo) => {
    setDrill({ tipo: 'tipos-servicio', titulo: `Tipo de servicio — ${periodo}`, items: [], loading: true });
    const res = await apiGet('/inteligencia/iscam/ventas-periodos/tipos-servicio', { unidad, periodo, group_by: groupBy });
    setDrill((d) => ({ ...d, items: res.data?.tipos_servicio || [], loading: false }));
  };

  const DRILL_COLS = {
    productos: [{ key: 'producto', label: 'Producto' }, { key: 'cantidad', label: 'Cantidad' }, { key: 'importe', label: 'Venta Total' }, { key: 'tickets', label: 'Tickets' }],
    tickets: [{ key: 'folio', label: 'Folio' }, { key: 'fecha', label: 'Fecha' }, { key: 'cantidad', label: 'Cantidad' }, { key: 'importe_producto', label: 'Importe Producto' }, { key: 'ajustes_cheque', label: 'Ajustes Cheque' }, { key: 'importe_ticket', label: 'Importe Ticket' }],
    'tipos-servicio': [{ key: 'tipo', label: 'Tipo de Servicio' }, { key: 'venta_total', label: 'Venta Total' }, { key: 'cheques', label: 'Cheques' }, { key: 'clientes', label: 'Clientes' }, { key: 'cheque_promedio', label: 'Cheque Prom.' }],
    cuenta: [{ key: 'producto', label: 'Producto' }, { key: 'cantidad', label: 'Cantidad' }, { key: 'precio', label: 'Precio' }, { key: 'importe', label: 'Importe' }],
  };
  const exportDrillExcel = () => {
    if (!drill?.items?.length) return;
    const cols = DRILL_COLS[drill.tipo] || DRILL_COLS.cuenta;
    exportToExcel(`ISCAM_${drill.tipo}_${unidad}`, [{ name: 'Detalle', columns: cols, rows: drill.items }]);
  };
  const exportDrillPdf = () => {
    if (!drill?.items?.length) return;
    const cols = DRILL_COLS[drill.tipo] || DRILL_COLS.cuenta;
    exportToPDF(drill.titulo, cols, drill.items, unidad);
  };

  // ---- Exportación ----
  const descriptor = buildDescriptor(sub, groupBy, data);
  const rangoTxt = `${MESES[desdeMes]} ${desdeAnio} — ${MESES[hastaMes]} ${hastaAnio}`;
  const baseName = `ISCAM_${sub}_${unidad}_${desdeAnio}${String(desdeMes).padStart(2, '0')}-${hastaAnio}${String(hastaMes).padStart(2, '0')}`;
  const detalleDependienteIncompleto = Boolean(
    freshness?.detail_stale && ((sub === 'cuentas' && groupBy === 'none') || sub === 'comandas')
  );
  const puedeExportar = (descriptor.rows || []).length > 0 && !detalleDependienteIncompleto;

  const buildExportSheets = (exportData) => {
    const exportDescriptor = buildDescriptor(sub, groupBy, exportData);

    if (sub === 'pagos-ticket' && groupBy === 'none') {
      return [
        {
          name: 'Resumen por forma',
          columns: exportDescriptor.columns,
          rows: exportData?.resumen_formas || [],
        },
        {
          name: 'Detalle pagos',
          columns: [
            { key: 'folio', label: 'Folio' },
            { key: 'fecha', label: 'Fecha' },
            { key: 'forma', label: 'Forma' },
            { key: 'codigo', label: 'Codigo' },
            { key: 'importe', label: 'Importe' },
            { key: 'propina', label: 'Propina' },
            { key: 'referencia', label: 'Referencia' },
            { key: 'sistema', label: 'Sistema' },
          ],
          rows: exportData?.pagos || [],
        },
      ];
    }

    return [{ name: exportDescriptor.title, columns: exportDescriptor.columns, rows: exportDescriptor.rows }];
  };

  const fetchExportData = async () => {
    const { path, params } = getReportRequest({ export_all: true });
    const res = await apiGet(path, params);
    if (res.estado !== ESTADO.OK) {
      setEstado(res.estado);
      return null;
    }
    return res.data;
  };

  const onExcel = async () => {
    const exportData = await fetchExportData();
    if (!exportData) return;
    exportToExcel(baseName, buildExportSheets(exportData));
  };

  const onPdf = async () => {
    const exportData = await fetchExportData();
    if (!exportData) return;
    const exportDescriptor = buildDescriptor(sub, groupBy, exportData);
    exportToPDF(`${exportDescriptor.title} — ${unidad}`, exportDescriptor.columns, exportDescriptor.rows, `${unidad} · ${rangoTxt}`);
  };

  const groupOpts = GROUP_OPTS[sub] || [];

  return (
    <div className="space-y-4" data-testid="reportes-iscam">
      <div className="flex items-center gap-2">
        <FileBarChart className="h-5 w-5 text-emerald-400" />
        <h2 className="text-lg font-semibold text-white">Reportes ISCAM</h2>
      </div>

      {/* Sub-tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-700">
        {SUBTABS.map((t) => (
          <button key={t.id} onClick={() => onChangeSub(t.id)} data-testid={`iscam-tab-${t.id}`}
            className={`px-3 py-2 text-sm font-medium border-b-2 -mb-px inline-flex items-center gap-2 ${sub === t.id ? 'border-emerald-400 text-emerald-300' : 'border-transparent text-slate-400 hover:text-slate-200'}`}>
            <t.icon className="h-4 w-4" /> {t.label}
          </button>
        ))}
      </div>

      {/* Barra de controles: rango mes-año + agrupación + export */}
      <div className="flex flex-wrap items-end gap-3 bg-slate-800/60 border border-slate-700 rounded-lg p-3">
        <div>
          <label className="text-xs text-slate-400 block mb-1">Desde</label>
          <div className="flex gap-1">
            <select value={desdeMes} onChange={(e) => setDesdeMes(+e.target.value)} data-testid="iscam-desde-mes"
              className="bg-slate-700 text-white text-sm rounded px-2 py-1.5 border border-slate-600">
              {MESES.slice(1).map((m, i) => <option key={i + 1} value={i + 1}>{m}</option>)}
            </select>
            <select value={desdeAnio} onChange={(e) => setDesdeAnio(+e.target.value)} data-testid="iscam-desde-anio"
              className="bg-slate-700 text-white text-sm rounded px-2 py-1.5 border border-slate-600">
              {YEARS.map((y) => <option key={y} value={y}>{y}</option>)}
            </select>
          </div>
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1">Hasta</label>
          <div className="flex gap-1">
            <select value={hastaMes} onChange={(e) => setHastaMes(+e.target.value)} data-testid="iscam-hasta-mes"
              className="bg-slate-700 text-white text-sm rounded px-2 py-1.5 border border-slate-600">
              {MESES.slice(1).map((m, i) => <option key={i + 1} value={i + 1}>{m}</option>)}
            </select>
            <select value={hastaAnio} onChange={(e) => setHastaAnio(+e.target.value)} data-testid="iscam-hasta-anio"
              className="bg-slate-700 text-white text-sm rounded px-2 py-1.5 border border-slate-600">
              {YEARS.map((y) => <option key={y} value={y}>{y}</option>)}
            </select>
          </div>
        </div>

        {groupOpts.length > 0 && (
          <div>
            <label className="text-xs text-slate-400 block mb-1">Agrupar por</label>
            <div className="inline-flex rounded-md overflow-hidden border border-slate-600">
              {groupOpts.map((g) => (
                <button key={g.id} onClick={() => setGroupBy(g.id)} data-testid={`iscam-group-${g.id}`}
                  className={`px-3 py-1.5 text-sm ${groupBy === g.id ? 'bg-emerald-500 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'}`}>
                  {g.label}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="ml-auto flex items-end gap-2">
          <div className="self-center text-xs text-slate-400" data-testid="iscam-freshness-status">
            {freshnessLoading
              ? 'Verificando actualización...'
              : freshness?.detail_stale
                ? `Detalle incompleto: ${freshness.detail_problem_dates?.length || 0} día(s) · KPI hasta ${formatDateMx(freshness.latest_canonical_date)}`
                : freshness?.latest_canonical_date
                  ? `Actualizado hasta ${formatDateMx(freshness.latest_canonical_date)}`
                  : 'Sin fecha canónica disponible'}
          </div>
          {(freshness?.stale || freshness?.detail_stale) && (
            <button onClick={syncMissingClosedDays} disabled={syncing} data-testid="iscam-sync-missing"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md bg-sky-600 text-white hover:bg-sky-500 disabled:opacity-40 disabled:cursor-not-allowed">
              <RefreshCw className={`h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
              {syncing ? 'Sincronizando...' : 'Sincronizar faltantes'}
            </button>
          )}
          <button onClick={onExcel} disabled={!puedeExportar} data-testid="iscam-export-excel"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed">
            <FileSpreadsheet className="h-4 w-4" /> Excel
          </button>
          <button onClick={onPdf} disabled={!puedeExportar} data-testid="iscam-export-pdf"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md bg-rose-600 text-white hover:bg-rose-500 disabled:opacity-40 disabled:cursor-not-allowed">
            <FileText className="h-4 w-4" /> PDF
          </button>
        </div>
      </div>

      {freshness?.detail_stale && (
        <div data-testid="iscam-detail-incomplete" className="text-sm rounded-lg px-4 py-3 border bg-amber-500/10 border-amber-500/30 text-amber-300">
          El encabezado canónico está actualizado, pero el detalle histórico no concilia: faltan o difieren {freshness.detail_problem_dates?.length || 0} día(s), {num(freshness.detail_ticket_gap || 0)} cheque(s) y {money(freshness.detail_sales_gap || 0)}. Sincroniza faltantes antes de certificar/exportar vistas de detalle.
        </div>
      )}

      {syncMessage && (
        <div data-testid="iscam-sync-message"
          className={`text-sm rounded-lg px-4 py-3 border ${syncMessage.tipo === 'ok'
            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
            : 'bg-rose-500/10 border-rose-500/30 text-rose-300'}`}>
          {syncMessage.texto}
        </div>
      )}

      {sinUnidad && (
        <div className="bg-amber-500/10 border border-amber-500/30 text-amber-300 text-sm rounded-lg px-4 py-3">
          Selecciona una <strong>unidad de negocio</strong> en el menú superior para ver los reportes ISCAM.
        </div>
      )}

      {!sinUnidad && (
        <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-16"><Loader2 className="h-7 w-7 animate-spin text-emerald-400" /></div>
          ) : estado !== ESTADO.OK ? (
            <div className="px-4 py-10 text-center text-slate-400">No se pudieron cargar los datos ({estado}).</div>
          ) : (
            <div className="overflow-x-auto">
              {sub === 'periodos' && <TablaPeriodos data={data} onDrill={drillProductos} onDrillTipos={drillTiposServicio} />}
              {sub === 'cuentas' && (groupBy !== 'none'
                ? <GenericTable columns={descriptor.columns} rows={descriptor.rows} />
                : <TablaCuentas data={data} onDrill={drillCuenta} />)}
              {sub === 'comandas' && (groupBy !== 'none'
                ? <GenericTable columns={descriptor.columns} rows={descriptor.rows} />
                : <TablaComandas data={data} />)}
              {sub === 'formas' && (groupBy !== 'none'
                ? <GenericTable columns={descriptor.columns} rows={descriptor.rows} />
                : <TablaFormas data={data} />)}
              {sub === 'pagos-ticket' && (groupBy !== 'none'
                ? <GenericTable columns={descriptor.columns} rows={descriptor.rows} />
                : <TablaPagosTicket data={data} />)}
            </div>
          )}
        </div>
      )}

      {/* Modales drill */}
      {drill && (
        <Modal title={drill.titulo} onClose={() => setDrill(null)} headerAction={
          !drill.loading && drill.items?.length ? (
            <>
              <button onClick={exportDrillExcel} data-testid="iscam-drill-export-excel"
                className="inline-flex items-center gap-1 px-2.5 py-1 text-xs rounded bg-emerald-600 text-white hover:bg-emerald-500">
                <FileSpreadsheet className="h-3.5 w-3.5" /> Excel
              </button>
              <button onClick={exportDrillPdf} data-testid="iscam-drill-export-pdf"
                className="inline-flex items-center gap-1 px-2.5 py-1 text-xs rounded bg-rose-600 text-white hover:bg-rose-500">
                <FileText className="h-3.5 w-3.5" /> PDF
              </button>
            </>
          ) : null
        }>
          {drill.loading ? (
            <div className="flex justify-center py-8"><Loader2 className="h-6 w-6 animate-spin text-emerald-400" /></div>
          ) : drill.tipo === 'productos' ? (
            <div className="space-y-4">
              <table className="w-full">
                <thead><tr><TH>Producto</TH><TH right>Cantidad</TH><TH right>Importe</TH><TH right>Tickets</TH></tr></thead>
                <tbody className="divide-y divide-slate-700">
                  {drill.items.map((p, i) => (
                    <tr key={i} className="hover:bg-slate-700/40 cursor-pointer" onDoubleClick={() => drillTickets(drill.periodo, p.codigo, p.producto)} title="Doble clic: ver tickets" data-testid={`drill-prod-${p.codigo}`}>
                      <TD><span className="inline-flex items-center gap-1">{p.producto}<ChevronRight className="h-3 w-3 text-slate-500" /></span></TD>
                      <TD right>{num(p.cantidad)}</TD><TD right>{money2(p.importe)}</TD><TD right>{p.tickets}</TD>
                    </tr>
                  ))}
                </tbody>
              </table>
              {drill.resumen && (
                <div className="border border-slate-600 rounded-lg p-3 bg-slate-900/40" data-testid="iscam-productos-conciliacion">
                  <div className="text-xs uppercase font-semibold text-slate-400 mb-2">Resumen de conciliación</div>
                  <div className="grid grid-cols-3 gap-3 text-sm">
                    <div><div className="text-slate-400">Venta productos</div><div className="text-white font-semibold">{money2(drill.resumen.venta_productos)}</div></div>
                    <div><div className="text-slate-400">Ajustes del cheque</div><div className="text-amber-300 font-semibold">{money2(drill.resumen.ajustes_cheque)}</div></div>
                    <div><div className="text-slate-400">Venta neta conciliada</div><div className="text-emerald-300 font-semibold">{money2(drill.resumen.venta_neta)}</div></div>
                  </div>
                </div>
              )}
            </div>
          ) : drill.tipo === 'tickets' ? (
            <table className="w-full">
              <thead><tr><TH>Folio</TH><TH>Fecha</TH><TH right>Cant.</TH><TH right>Importe prod.</TH><TH right>Ajustes cheque</TH><TH right>Total ticket</TH></tr></thead>
              <tbody className="divide-y divide-slate-700">
                {drill.items.map((t, i) => (
                  <tr key={i}><TD mono>{t.folio}</TD><TD>{(t.fecha || '').replace('T', ' ').slice(0, 16)}</TD><TD right>{num(t.cantidad)}</TD><TD right>{money2(t.importe_producto)}</TD><TD right>{money2(t.ajustes_cheque)}</TD><TD right>{money2(t.importe_ticket)}</TD></tr>
                ))}
              </tbody>
            </table>
          ) : drill.tipo === 'tipos-servicio' ? (
            <table className="w-full">
              <thead><tr><TH>Tipo de servicio</TH><TH right>Venta Total</TH><TH right>Cheques</TH><TH right>Clientes</TH><TH right>Cheque Prom.</TH></tr></thead>
              <tbody className="divide-y divide-slate-700">
                {drill.items.map((t, i) => (
                  <tr key={i}><TD>{t.tipo}</TD><TD right>{money(t.venta_total)}</TD><TD right>{t.cheques}</TD><TD right>{t.clientes}</TD><TD right>{money(t.cheque_promedio)}</TD></tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="space-y-4">
              <table className="w-full">
                <thead><tr><TH>Producto</TH><TH right>Cantidad</TH><TH right>Precio</TH><TH right>Importe</TH></tr></thead>
                <tbody className="divide-y divide-slate-700">
                  {drill.items.map((p, i) => (
                    <tr key={i}><TD>{p.producto}</TD><TD right>{num(p.cantidad)}</TD><TD right>{money2(p.precio)}</TD><TD right>{money2(p.importe)}</TD></tr>
                  ))}
                </tbody>
              </table>
              {!!drill.ajustes?.length && (
                <div>
                  <div className="px-3 py-2 text-xs font-semibold text-amber-300 uppercase">Ajustes del cheque</div>
                  <table className="w-full"><tbody className="divide-y divide-slate-700">
                    {drill.ajustes.map((a, i) => (<tr key={i}><TD>{a.concepto}</TD><TD right>{money2(a.importe)}</TD></tr>))}
                  </tbody></table>
                </div>
              )}
              {drill.resumen && (
                <div className="border border-slate-600 rounded-lg p-3 bg-slate-900/40" data-testid="iscam-ticket-conciliacion">
                  <div className="text-xs uppercase font-semibold text-slate-400 mb-2">Conciliación del ticket</div>
                  <div className="grid grid-cols-4 gap-3 text-sm">
                    <div><div className="text-slate-400">Productos</div><div className="text-white font-semibold">{money2(drill.resumen.venta_productos)}</div></div>
                    <div><div className="text-slate-400">Ajustes</div><div className="text-amber-300 font-semibold">{money2(drill.resumen.ajustes_cheque)}</div></div>
                    <div><div className="text-slate-400">Total ticket</div><div className="text-emerald-300 font-semibold">{money2(drill.resumen.total_ticket)}</div></div>
                    <div><div className="text-slate-400">Diferencias encontradas</div><div className={Math.abs(drill.resumen.diferencia || 0) <= 0.05 ? "text-emerald-300 font-semibold" : "text-rose-300 font-semibold"}>{money2(drill.resumen.diferencia)}</div></div>
                  </div>
                </div>
              )}
            </div>
          )}
        </Modal>
      )}
    </div>
  );
}

function TablaPeriodos({ data, onDrill, onDrillTipos }) {
  const rows = data?.periodos || [];
  if (!rows.length) return <div className="px-4 py-10 text-center text-slate-400">Sin ventas en el rango.</div>;
  return (
    <table className="w-full">
      <thead className="bg-slate-700/40"><tr>
        <TH>Periodo</TH><TH right>Venta Total</TH><TH right>Cheques</TH><TH right>Cheque Prom.</TH><TH right>Clientes</TH><TH right>Consumo Prom.</TH>
      </tr></thead>
      <tbody className="divide-y divide-slate-700">
        {rows.map((r) => (
          <tr key={r.periodo} className="hover:bg-slate-700/30">
            <TD mono>{r.periodo}</TD>
            <td className="px-3 py-2 text-sm text-emerald-300 text-right font-semibold cursor-pointer hover:underline" onDoubleClick={() => onDrill(r.periodo)} title="Doble clic: detalle por producto" data-testid={`periodo-venta-${r.periodo}`}>{money(r.venta_total)}</td>
            <td className="px-3 py-2 text-sm text-sky-300 text-right cursor-pointer hover:underline" onDoubleClick={() => onDrillTipos(r.periodo)} title="Doble clic: por tipo de servicio" data-testid={`periodo-cheques-${r.periodo}`}>{r.cheques}</td>
            <TD right>{money(r.cheque_promedio)}</TD><TD right>{r.clientes}</TD><TD right>{money(r.consumo_promedio)}</TD>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function TablaCuentas({ data, onDrill }) {
  const rows = data?.cuentas || [];
  if (!rows.length) return <div className="px-4 py-10 text-center text-slate-400">Sin cuentas en el rango.</div>;
  return (
    <table className="w-full">
      <thead className="bg-slate-700/40"><tr><TH>Folio</TH><TH>Fecha</TH><TH right>Personas</TH><TH right>Importe</TH><TH>Estado</TH></tr></thead>
      <tbody className="divide-y divide-slate-700">
        {rows.map((r, i) => (
          <tr key={i} className="hover:bg-slate-700/30 cursor-pointer" onDoubleClick={() => onDrill(r.folio)} title="Doble clic: ver productos" data-testid={`cuenta-${r.folio}`}>
            <TD mono><span className="inline-flex items-center gap-1">{r.folio}<ChevronRight className="h-3 w-3 text-slate-500" /></span></TD>
            <TD>{(r.fecha || '').replace('T', ' ').slice(0, 16)}</TD><TD right>{r.personas}</TD><TD right>{money(r.importe)}</TD><TD>{r.estado}</TD>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function TablaComandas({ data }) {
  const rows = data?.comandas || [];
  if (!rows.length) return <div className="px-4 py-10 text-center text-slate-400">Sin comandas en el rango.</div>;
  return (
    <table className="w-full">
      <thead className="bg-slate-700/40"><tr><TH>Folio Cuenta</TH><TH>Fecha</TH><TH>Clave</TH><TH>Descripción</TH><TH right>Cant.</TH><TH right>Precio</TH><TH right>Importe</TH></tr></thead>
      <tbody className="divide-y divide-slate-700">
        {rows.map((r, i) => (
          <tr key={i} className="hover:bg-slate-700/30">
            <TD mono>{r.folio_cuenta}</TD><TD>{(r.fecha || '').replace('T', ' ').slice(0, 16)}</TD><TD mono>{r.clave}</TD>
            <TD>{r.descripcion}</TD><TD right>{num(r.cantidad)}</TD><TD right>{money(r.precio)}</TD><TD right>{money(r.importe)}</TD>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function TablaFormas({ data }) {
  const rows = data?.cortes || [];
  const t = data?.totales || {};
  if (!rows.length) return <div className="px-4 py-10 text-center text-slate-400">Sin cortes de caja en el rango.</div>;
  return (
    <table className="w-full">
      <thead className="bg-slate-700/40"><tr>
        <TH>Folio</TH><TH>Fecha</TH><TH>Caja</TH><TH right>Total</TH><TH right>Efectivo</TH><TH right>Tarjeta</TH><TH right>Amex</TH><TH right>Vales</TH><TH right>Otros</TH><TH right>Propina</TH><TH right>Comisión</TH>
      </tr></thead>
      <tbody className="divide-y divide-slate-700">
        {rows.map((r, i) => (
          <tr key={i} className="hover:bg-slate-700/30">
            <TD mono>{r.folio}</TD><TD>{(r.fecha || '').replace('T', ' ').slice(0, 16)}</TD><TD>{r.caja}</TD>
            <TD right>{money(r.total)}</TD><TD right>{money(r.efectivo)}</TD><TD right>{money(r.tarjeta)}</TD><TD right>{money(r.amex)}</TD>
            <TD right>{money(r.vales)}</TD><TD right>{money(r.otros)}</TD><TD right>{money(r.propina)}</TD><TD right>{money(r.comision)}</TD>
          </tr>
        ))}
      </tbody>
      <tfoot className="bg-slate-700/60 font-semibold">
        <tr>
          <td className="px-3 py-2 text-sm text-white" colSpan={3}>TOTALES</td>
          <TD right>{money(t.total)}</TD><TD right>{money(t.efectivo)}</TD><TD right>{money(t.tarjeta)}</TD><TD right>{money(t.amex)}</TD>
          <TD right>{money(t.vales)}</TD><TD right>{money(t.otros)}</TD><TD right>{money(t.propina)}</TD><TD right>{money(t.comision)}</TD>
        </tr>
      </tfoot>
    </table>
  );
}

function TablaPagosTicket({ data }) {
  const resumen = data?.resumen_formas || [];
  const pagos = data?.pagos || [];
  const t = data?.totales || {};
  if (!resumen.length) return <div className="px-4 py-10 text-center text-slate-400">Sin pagos por ticket en el rango. (Requiere que el job de sync haya enriquecido la unidad/periodo).</div>;
  return (
    <div className="space-y-4" data-testid="iscam-pagos-ticket">
      <div>
        <div className="px-3 py-2 text-xs font-semibold text-emerald-300 uppercase">Resumen por forma de pago</div>
        <table className="w-full">
          <thead className="bg-slate-700/40"><tr>
            <TH>Forma de Pago</TH><TH>Código</TH><TH right>Tickets</TH><TH right>Pagos</TH><TH right>Importe</TH><TH right>Propina</TH>
          </tr></thead>
          <tbody className="divide-y divide-slate-700">
            {resumen.map((r, i) => (
              <tr key={i} className="hover:bg-slate-700/30" data-testid={`pago-forma-${r.codigo}`}>
                <TD>{r.forma}</TD><TD mono>{r.codigo}</TD><TD right>{r.tickets}</TD><TD right>{r.pagos}</TD>
                <TD right>{money(r.importe)}</TD><TD right>{money(r.propina)}</TD>
              </tr>
            ))}
          </tbody>
          <tfoot className="bg-slate-700/60 font-semibold">
            <tr>
              <td className="px-3 py-2 text-sm text-white" colSpan={4}>TOTALES</td>
              <TD right>{money(t.importe)}</TD><TD right>{money(t.propina)}</TD>
            </tr>
          </tfoot>
        </table>
      </div>
      <div>
        <div className="px-3 py-2 text-xs font-semibold text-slate-400 uppercase">Detalle por pago (máx 2000)</div>
        <table className="w-full">
          <thead className="bg-slate-700/40"><tr>
            <TH>Folio</TH><TH>Fecha</TH><TH>Forma</TH><TH right>Importe</TH><TH right>Propina</TH><TH>Referencia</TH>
          </tr></thead>
          <tbody className="divide-y divide-slate-700">
            {pagos.map((p, i) => (
              <tr key={i} className="hover:bg-slate-700/30">
                <TD mono>{p.folio}</TD><TD>{(p.fecha || '').replace('T', ' ').slice(0, 16)}</TD><TD>{p.forma}</TD>
                <TD right>{money(p.importe)}</TD><TD right>{money(p.propina)}</TD><TD mono>{p.referencia}</TD>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
