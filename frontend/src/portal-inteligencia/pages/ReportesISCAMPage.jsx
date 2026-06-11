/**
 * Reportes ISCAM — Portal de Inteligencia Comercial.
 * 4 reportes sobre tablas CANÓNICAS (Sync_Sales + Finanzas_CortesCaja).
 * Drill-down por DOBLE CLIC. La unidad activa viene del selector del header.
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  FileBarChart, Loader2, X, Package, Receipt, ClipboardList, CreditCard, ChevronRight,
} from 'lucide-react';
import { apiGet, ESTADO } from '../api/client';

const money = (n) => (n ?? 0).toLocaleString('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 0 });
const num = (n) => (n ?? 0).toLocaleString('es-MX', { maximumFractionDigits: 2 });
const hoy = () => new Date().toISOString().slice(0, 10);
const hace = (d) => new Date(Date.now() - d * 86400000).toISOString().slice(0, 10);

const SUBTABS = [
  { id: 'periodos', label: 'Ventas 12 Periodos', icon: FileBarChart },
  { id: 'cuentas', label: 'Resumen de Cuentas', icon: Receipt },
  { id: 'comandas', label: 'Comandas de Venta', icon: ClipboardList },
  { id: 'formas', label: 'Ventas Formas de Pago', icon: CreditCard },
  { id: 'pagos-ticket', label: 'Pagos por Ticket', icon: CreditCard },
];

function Modal({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-slate-800 border border-slate-700 rounded-xl w-full max-w-3xl max-h-[85vh] overflow-auto" onClick={(e) => e.stopPropagation()} data-testid="iscam-drill-modal">
        <div className="sticky top-0 bg-slate-800 border-b border-slate-700 px-5 py-3 flex items-center justify-between">
          <h3 className="text-white font-semibold text-sm">{title}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white"><X className="h-4 w-4" /></button>
        </div>
        <div className="p-4">{children}</div>
      </div>
    </div>
  );
}

const TH = ({ children, right }) => <th className={`px-3 py-2 text-xs font-medium text-slate-400 uppercase ${right ? 'text-right' : 'text-left'}`}>{children}</th>;
const TD = ({ children, right, mono }) => <td className={`px-3 py-2 text-sm text-slate-200 ${right ? 'text-right' : ''} ${mono ? 'font-mono' : ''}`}>{children}</td>;

export default function ReportesISCAMPage({ unidadSeleccionada }) {
  const [sub, setSub] = useState('periodos');
  const [loading, setLoading] = useState(false);
  const [estado, setEstado] = useState(ESTADO.OK);
  const [data, setData] = useState(null);
  const [desde, setDesde] = useState(hace(30));
  const [hasta, setHasta] = useState(hoy());
  const [drill, setDrill] = useState(null); // {tipo, titulo, items, loading}

  const unidad = unidadSeleccionada;
  const sinUnidad = !unidad || unidad === 'todas';

  const fetchReport = useCallback(async () => {
    if (sinUnidad) { setData(null); return; }
    setLoading(true); setEstado(ESTADO.OK);
    let path, params = { unidad };
    if (sub === 'periodos') { path = '/inteligencia/iscam/ventas-periodos'; params.meses = 12; }
    else if (sub === 'cuentas') { path = '/inteligencia/iscam/cuentas'; params.desde = desde; params.hasta = hasta; }
    else if (sub === 'comandas') { path = '/inteligencia/iscam/comandas'; params.desde = desde; params.hasta = hasta; }
    else if (sub === 'pagos-ticket') { path = '/inteligencia/iscam/formas-pago/por-ticket'; params.desde = desde; params.hasta = hasta; }
    else { path = '/inteligencia/iscam/formas-pago'; params.desde = desde; params.hasta = hasta; }
    const res = await apiGet(path, params);
    setEstado(res.estado);
    setData(res.estado === ESTADO.OK ? res.data : null);
    setLoading(false);
  }, [sub, unidad, desde, hasta, sinUnidad]);

  useEffect(() => { fetchReport(); }, [fetchReport]);

  // ---- Drill-downs ----
  const drillProductos = async (periodo) => {
    setDrill({ tipo: 'productos', titulo: `Productos vendidos — ${periodo}`, items: [], loading: true, periodo });
    const res = await apiGet('/inteligencia/iscam/ventas-periodos/productos', { unidad, periodo });
    setDrill((d) => ({ ...d, items: res.data?.productos || [], loading: false }));
  };
  const drillTickets = async (periodo, producto, nombre) => {
    setDrill({ tipo: 'tickets', titulo: `Tickets con "${nombre}" — ${periodo}`, items: [], loading: true });
    const res = await apiGet('/inteligencia/iscam/ventas-periodos/tickets', { unidad, periodo, producto });
    setDrill((d) => ({ ...d, items: res.data?.tickets || [], loading: false }));
  };
  const drillCuenta = async (folio) => {
    setDrill({ tipo: 'cuenta', titulo: `Detalle de cuenta — Folio ${folio}`, items: [], loading: true });
    const res = await apiGet('/inteligencia/iscam/cuentas/detalle', { unidad, folio });
    setDrill((d) => ({ ...d, items: res.data?.productos || [], loading: false }));
  };
  const drillTiposServicio = async (periodo) => {
    setDrill({ tipo: 'tipos-servicio', titulo: `Tipo de servicio — ${periodo}`, items: [], loading: true });
    const res = await apiGet('/inteligencia/iscam/ventas-periodos/tipos-servicio', { unidad, periodo });
    setDrill((d) => ({ ...d, items: res.data?.tipos_servicio || [], loading: false }));
  };

  return (
    <div className="space-y-4" data-testid="reportes-iscam">
      <div className="flex items-center gap-2">
        <FileBarChart className="h-5 w-5 text-emerald-400" />
        <h2 className="text-lg font-semibold text-white">Reportes ISCAM</h2>
      </div>

      {/* Sub-tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-700">
        {SUBTABS.map((t) => (
          <button key={t.id} onClick={() => setSub(t.id)} data-testid={`iscam-tab-${t.id}`}
            className={`px-3 py-2 text-sm font-medium border-b-2 -mb-px inline-flex items-center gap-2 ${sub === t.id ? 'border-emerald-400 text-emerald-300' : 'border-transparent text-slate-400 hover:text-slate-200'}`}>
            <t.icon className="h-4 w-4" /> {t.label}
          </button>
        ))}
      </div>

      {/* Filtros de fecha (todos menos periodos) */}
      {sub !== 'periodos' && (
        <div className="flex flex-wrap items-end gap-3">
          <div><label className="text-xs text-slate-400 block mb-1">Desde</label>
            <input type="date" value={desde} onChange={(e) => setDesde(e.target.value)} data-testid="iscam-desde"
              className="bg-slate-700 text-white text-sm rounded px-2 py-1.5 border border-slate-600" /></div>
          <div><label className="text-xs text-slate-400 block mb-1">Hasta</label>
            <input type="date" value={hasta} onChange={(e) => setHasta(e.target.value)} data-testid="iscam-hasta"
              className="bg-slate-700 text-white text-sm rounded px-2 py-1.5 border border-slate-600" /></div>
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
              {sub === 'cuentas' && <TablaCuentas data={data} onDrill={drillCuenta} />}
              {sub === 'comandas' && <TablaComandas data={data} />}
              {sub === 'formas' && <TablaFormas data={data} />}
              {sub === 'pagos-ticket' && <TablaPagosTicket data={data} />}
            </div>
          )}
        </div>
      )}

      {/* Modales drill */}
      {drill && (
        <Modal title={drill.titulo} onClose={() => setDrill(null)}>
          {drill.loading ? (
            <div className="flex justify-center py-8"><Loader2 className="h-6 w-6 animate-spin text-emerald-400" /></div>
          ) : drill.tipo === 'productos' ? (
            <table className="w-full">
              <thead><tr><TH>Producto</TH><TH right>Cantidad</TH><TH right>Importe</TH><TH right>Tickets</TH></tr></thead>
              <tbody className="divide-y divide-slate-700">
                {drill.items.map((p, i) => (
                  <tr key={i} className="hover:bg-slate-700/40 cursor-pointer" onDoubleClick={() => drillTickets(drill.periodo, p.codigo, p.producto)} title="Doble clic: ver tickets" data-testid={`drill-prod-${p.codigo}`}>
                    <TD><span className="inline-flex items-center gap-1">{p.producto}<ChevronRight className="h-3 w-3 text-slate-500" /></span></TD>
                    <TD right>{num(p.cantidad)}</TD><TD right>{money(p.importe)}</TD><TD right>{p.tickets}</TD>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : drill.tipo === 'tickets' ? (
            <table className="w-full">
              <thead><tr><TH>Folio</TH><TH>Fecha</TH><TH right>Cant.</TH><TH right>Importe prod.</TH><TH right>Importe ticket</TH></tr></thead>
              <tbody className="divide-y divide-slate-700">
                {drill.items.map((t, i) => (
                  <tr key={i}><TD mono>{t.folio}</TD><TD>{(t.fecha || '').replace('T', ' ').slice(0, 16)}</TD><TD right>{num(t.cantidad)}</TD><TD right>{money(t.importe_producto)}</TD><TD right>{money(t.importe_ticket)}</TD></tr>
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
            <table className="w-full">
              <thead><tr><TH>Producto</TH><TH right>Cantidad</TH><TH right>Precio</TH><TH right>Importe</TH></tr></thead>
              <tbody className="divide-y divide-slate-700">
                {drill.items.map((p, i) => (
                  <tr key={i}><TD>{p.producto}</TD><TD right>{num(p.cantidad)}</TD><TD right>{money(p.precio)}</TD><TD right>{money(p.importe)}</TD></tr>
                ))}
              </tbody>
            </table>
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
        <TH>Mes</TH><TH right>Venta Total</TH><TH right>Cheques</TH><TH right>Cheque Prom.</TH><TH right>Clientes</TH><TH right>Consumo Prom.</TH>
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
