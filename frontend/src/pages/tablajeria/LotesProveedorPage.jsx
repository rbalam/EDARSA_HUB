import React, { useEffect, useMemo, useState } from 'react';
import api from '@/lib/api';

const SEMAFOROS = ['', 'VERDE', 'AMARILLO', 'ROJO'];
const PRIORIDADES = ['BAJA', 'MEDIA', 'ALTA', 'CRITICA'];

const card = { border: '1px solid #e5e7eb', borderRadius: 12, padding: 16, background: '#fff' };
const input = { width: '100%', border: '1px solid #d1d5db', borderRadius: 8, padding: '8px 10px' };
const button = { border: '1px solid #111827', borderRadius: 8, padding: '8px 12px', background: '#111827', color: '#fff', fontWeight: 600, cursor: 'pointer' };
const secondary = { ...button, background: '#fff', color: '#111827' };
const th = { textAlign: 'left', padding: 8, borderBottom: '1px solid #e5e7eb', whiteSpace: 'nowrap' };
const td = { padding: 8, borderBottom: '1px solid #f3f4f6', verticalAlign: 'top' };

function asMoney(value) {
  return Number(value || 0).toLocaleString('es-MX', { style: 'currency', currency: 'MXN' });
}

function asNumber(value, decimals = 2) {
  if (value === null || value === undefined || value === '') return '-';
  const parsed = Number(value);
  return Number.isNaN(parsed) ? '-' : parsed.toLocaleString('es-MX', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

function asDate(value) {
  if (!value) return '-';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleDateString('es-MX');
}

function badgeStyle(value) {
  const normalized = String(value || '').toUpperCase();
  if (normalized === 'ROJO') return { background: '#fee2e2', color: '#991b1b' };
  if (normalized === 'AMARILLO') return { background: '#fef3c7', color: '#92400e' };
  if (normalized === 'VERDE') return { background: '#dcfce7', color: '#166534' };
  return { background: '#f3f4f6', color: '#374151' };
}

function Badge({ value }) {
  return <span style={{ ...badgeStyle(value), borderRadius: 999, padding: '3px 8px', fontSize: 12, fontWeight: 700 }}>{value || 'SIN_DATOS'}</span>;
}

export default function LotesProveedorPage() {
  const [rows, setRows] = useState([]);
  const [claims, setClaims] = useState([]);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState({ lote: '', proveedor_id: '', semaforo: '' });
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [claimForm, setClaimForm] = useState({ motivo: '', descripcion: '', prioridad: 'MEDIA' });
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [savingClaim, setSavingClaim] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const kpis = useMemo(function calculateKpis() {
    const impacto = rows.reduce(function sum(acc, row) { return acc + Number(row.ImpactoEconomico || 0); }, 0);
    const rojos = rows.filter(function red(row) { return String(row.Semaforo || '').toUpperCase() === 'ROJO'; }).length;
    const amarillos = rows.filter(function yellow(row) { return String(row.Semaforo || '').toUpperCase() === 'AMARILLO'; }).length;
    const abiertos = claims.filter(function open(claim) { return String(claim.Estatus || '').toUpperCase() === 'ABIERTO'; }).length;
    const kgBase = rows.reduce(function sumKg(acc, row) { return acc + Number(row.CantidadBaseKg || 0); }, 0);
    const rendimientoRows = rows.filter(function hasRendimiento(row) { return row.RendimientoRealPorcentaje !== null && row.RendimientoRealPorcentaje !== undefined && row.RendimientoRealPorcentaje !== ''; });
    const rendimientoPromedio = rendimientoRows.length
      ? rendimientoRows.reduce(function sumRendimiento(acc, row) { return acc + Number(row.RendimientoRealPorcentaje || 0); }, 0) / rendimientoRows.length
      : 0;
    const critico = rows.slice().sort(function sortByRisk(a, b) {
      const riskA = (String(a.Semaforo || '').toUpperCase() === 'ROJO' ? 1000000 : 0) + Math.abs(Number(a.ImpactoEconomico || 0));
      const riskB = (String(b.Semaforo || '').toUpperCase() === 'ROJO' ? 1000000 : 0) + Math.abs(Number(b.ImpactoEconomico || 0));
      return riskB - riskA;
    })[0] || null;
    return { impacto, rojos, amarillos, abiertos, kgBase, rendimientoPromedio, critico };
  }, [rows, claims]);

  function setFilter(name, value) {
    setFilters(function update(current) { return { ...current, [name]: value }; });
  }

  function setClaim(name, value) {
    setClaimForm(function update(current) { return { ...current, [name]: value }; });
  }

  function buildUrl() {
    const query = new URLSearchParams();
    query.set('limit', '100');
    query.set('offset', '0');
    if (filters.lote.trim()) query.set('lote', filters.lote.trim());
    if (filters.proveedor_id.trim()) query.set('proveedor_id', filters.proveedor_id.trim());
    if (filters.semaforo) query.set('semaforo', filters.semaforo);
    return '/tablajeria/lotes-proveedor/rendimientos?' + query.toString();
  }

  async function refresh() {
    setLoading(true);
    setError('');
    setNotice('');
    try {
      const lotesRes = await api.get(buildUrl());
      const claimsRes = await api.get('/tablajeria/reclamos-proveedor?limit=100');
      const nextRows = lotesRes.data && lotesRes.data.rendimientos ? lotesRes.data.rendimientos : [];
      const nextClaims = claimsRes.data && claimsRes.data.reclamos ? claimsRes.data.reclamos : [];
      setRows(nextRows);
      setClaims(nextClaims);
      setTotal(lotesRes.data && lotesRes.data.total ? lotesRes.data.total : nextRows.length);
    } catch (err) {
      setError('No fue posible cargar lotes proveedor. Valida permisos, conexión o disponibilidad del backend.');
    } finally {
      setLoading(false);
    }
  }

  async function openDetail(row) {
    if (!row || !row.LoteRendimientoID) {
      setError('El lote seleccionado no tiene identificador.');
      return;
    }
    setSelected(row);
    setDetail(null);
    setDetailLoading(true);
    setError('');
    setNotice('');
    try {
      const res = await api.get('/tablajeria/lotes-proveedor/' + encodeURIComponent(row.LoteRendimientoID) + '/drilldown');
      setDetail(res.data || null);
    } catch (err) {
      setError('No fue posible cargar el drilldown del lote proveedor.');
    } finally {
      setDetailLoading(false);
    }
  }

  async function createClaim(event) {
    event.preventDefault();
    if (!selected || !selected.LoteRendimientoID) {
      setError('Selecciona un lote antes de abrir reclamo.');
      return;
    }
    if (!claimForm.motivo.trim()) {
      setError('Captura el motivo del reclamo.');
      return;
    }
    setSavingClaim(true);
    setError('');
    setNotice('');
    try {
      const payload = {
        motivo: claimForm.motivo.trim(),
        descripcion: claimForm.descripcion.trim() || null,
        prioridad: claimForm.prioridad,
        evidencia: {
          origen: 'EDARSAHUB_TABLAJERIA_LOTES_PROVEEDOR',
          loteProveedor: selected.LoteProveedor || null,
          loteInterno: selected.LoteInterno || null,
          semaforo: selected.Semaforo || null,
          impactoEconomico: selected.ImpactoEconomico || null
        }
      };
      const res = await api.post('/tablajeria/lotes-proveedor/' + encodeURIComponent(selected.LoteRendimientoID) + '/reclamos', payload);
      setNotice('Reclamo creado' + (res.data && res.data.folio_reclamo ? ': ' + res.data.folio_reclamo : '.'));
      setClaimForm({ motivo: '', descripcion: '', prioridad: 'MEDIA' });
      await refresh();
      await openDetail(selected);
    } catch (err) {
      setError('No fue posible crear el reclamo proveedor.');
    } finally {
      setSavingClaim(false);
    }
  }

  useEffect(function init() {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const lote = detail && detail.lote ? detail.lote : selected;
  const detailClaims = detail && detail.reclamos ? detail.reclamos : [];
  const notifications = detail && detail.notificaciones ? detail.notificaciones : [];

  return (
    <div data-testid="tablajeria-lotes-proveedor" style={{ padding: 24, display: 'grid', gap: 16 }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'flex-start' }}>
        <div>
          <h1 style={{ margin: 0 }}>Lotes proveedor</h1>
          <p style={{ margin: '6px 0 0', color: '#4b5563' }}>Rendimiento, desviaciones, impacto económico y reclamos por lote de compra; prioriza qué revisar primero en operación de sitio.</p>
        </div>
        <button type="button" onClick={refresh} disabled={loading} style={button}>{loading ? 'Cargando...' : 'Actualizar'}</button>
      </header>

      {error ? <div role="alert" style={{ ...card, borderColor: '#fecaca', color: '#991b1b' }}>{error}</div> : null}
      {notice ? <div role="status" style={{ ...card, borderColor: '#bbf7d0', color: '#166534' }}>{notice}</div> : null}

      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(5, minmax(0, 1fr))', gap: 12 }}>
        <div style={card}><small>Lotes visibles</small><strong style={{ display: 'block', fontSize: 24 }}>{asNumber(rows.length, 0)}</strong><small>Total: {asNumber(total, 0)}</small></div>
        <div style={card}><small>Impacto económico</small><strong style={{ display: 'block', fontSize: 24 }}>{asMoney(kpis.impacto)}</strong></div>
        <div style={card}><small>Alertas</small><strong style={{ display: 'block', fontSize: 24 }}>{asNumber(kpis.rojos + kpis.amarillos, 0)}</strong><small>Rojas: {kpis.rojos} · Amarillas: {kpis.amarillos}</small></div>
        <div style={card}><small>Reclamos abiertos</small><strong style={{ display: 'block', fontSize: 24 }}>{asNumber(kpis.abiertos, 0)}</strong></div>
        <div style={card}><small>Rendimiento prom.</small><strong style={{ display: 'block', fontSize: 24 }}>{asNumber(kpis.rendimientoPromedio)}%</strong><small>Kg base: {asNumber(kpis.kgBase)}</small></div>
      </section>

      <section style={card}>
        <h2 style={{ marginTop: 0 }}>Filtros</h2>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1.5fr 1fr auto', gap: 12, alignItems: 'end' }}>
          <label><span>Lote proveedor / interno</span><input style={input} value={filters.lote} onChange={function handle(e) { setFilter('lote', e.target.value); }} /></label>
          <label><span>Proveedor ID</span><input style={input} value={filters.proveedor_id} onChange={function handle(e) { setFilter('proveedor_id', e.target.value); }} /></label>
          <label><span>Semáforo</span><select style={input} value={filters.semaforo} onChange={function handle(e) { setFilter('semaforo', e.target.value); }}>{SEMAFOROS.map(function map(value) { return <option key={value || 'TODOS'} value={value}>{value || 'TODOS'}</option>; })}</select></label>
          <button type="button" onClick={refresh} disabled={loading} style={secondary}>Aplicar</button>
        </div>
      </section>

      <section style={{ ...card, display: 'grid', gap: 8 }}>
        <h2 style={{ margin: 0 }}>Prioridad operativa</h2>
        {kpis.critico ? (
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr auto', gap: 12, alignItems: 'center' }}>
            <div>
              <strong>{kpis.critico.LoteProveedor || kpis.critico.LoteInterno || 'Lote crítico'}</strong>
              <div style={{ color: '#6b7280', fontSize: 13 }}>{kpis.critico.ProveedorNombre || 'Sin proveedor'} · {kpis.critico.FolioOrdenTablaje || 'Sin orden'}</div>
            </div>
            <div><small>Semáforo</small><div><Badge value={kpis.critico.Semaforo} /></div></div>
            <div><small>Impacto</small><strong style={{ display: 'block' }}>{asMoney(kpis.critico.ImpactoEconomico)}</strong></div>
            <button type="button" style={secondary} onClick={function click() { openDetail(kpis.critico); }}>Abrir prioridad</button>
          </div>
        ) : <p style={{ margin: 0 }}>Sin lotes cargados para priorizar.</p>}
        <small style={{ color: '#6b7280' }}>Criterio: primero semáforo rojo y después mayor impacto económico absoluto. El backend conserva RBAC y fuente canónica SQL Server.</small>
      </section>

      <section style={card}>
        <h2 style={{ marginTop: 0 }}>Rendimientos por lote</h2>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead><tr><th style={th}>Lote</th><th style={th}>Proveedor</th><th style={th}>Orden</th><th style={th}>Kg base</th><th style={th}>Rend. esp.</th><th style={th}>Rend. real</th><th style={th}>Desv.</th><th style={th}>Merma kg</th><th style={th}>Impacto</th><th style={th}>Semáforo</th><th style={th}>Acción</th></tr></thead>
            <tbody>
              {rows.map(function render(row, index) {
                const isSelected = selected && selected.LoteRendimientoID === row.LoteRendimientoID;
                return (
                  <tr key={row.LoteRendimientoID || row.LoteProveedor || index} style={{ background: isSelected ? '#f9fafb' : '#fff' }}>
                    <td style={td}><strong>{row.LoteProveedor || row.LoteInterno || 'Sin lote'}</strong><div style={{ color: '#6b7280', fontSize: 12 }}>{asDate(row.FechaOperacionMexico)}</div></td>
                    <td style={td}>{row.ProveedorNombre || 'Sin proveedor'}</td>
                    <td style={td}>{row.FolioOrdenTablaje || '-'}</td>
                    <td style={td}>{asNumber(row.CantidadBaseKg)}</td>
                    <td style={td}>{asNumber(row.RendimientoEsperadoPorcentaje)}%</td>
                    <td style={td}>{asNumber(row.RendimientoRealPorcentaje)}%</td>
                    <td style={td}>{asNumber(row.DesviacionPorcentaje)}%</td>
                    <td style={td}>{asNumber(row.MermaRealKg)}</td>
                    <td style={td}>{asMoney(row.ImpactoEconomico)}</td>
                    <td style={td}><Badge value={row.Semaforo} /></td>
                    <td style={td}><button type="button" style={secondary} onClick={function click() { openDetail(row); }}>Ver detalle</button></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {!rows.length && !loading ? <p>Sin registros con los filtros actuales. Limpia filtros o actualiza para volver a consultar el backend.</p> : null}
      </section>

      <section style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16 }}>
        <div style={card}>
          <h2 style={{ marginTop: 0 }}>Drilldown del lote</h2>
          {!lote ? <p>Selecciona un lote para ver proveedor, compra, recepción, tablajería y reclamos.</p> : null}
          {detailLoading ? <p>Cargando detalle...</p> : null}
          {lote && !detailLoading ? (
            <div style={{ display: 'grid', gap: 8 }}>
              <div><strong>Lote proveedor:</strong> {lote.LoteProveedor || '-'}</div>
              <div><strong>Lote interno:</strong> {lote.LoteInterno || '-'}</div>
              <div><strong>Proveedor:</strong> {lote.ProveedorNombre || '-'}</div>
              <div><strong>Orden compra:</strong> {lote.OrdenCompraFolio || '-'}</div>
              <div><strong>Recepción:</strong> {lote.RecepcionFolio || '-'}</div>
              <div><strong>Factura:</strong> {lote.FacturaFolio || '-'}</div>
              <div><strong>Orden tablaje:</strong> {lote.FolioOrdenTablaje || '-'}</div>
              <div><strong>Insumo base:</strong> {lote.InsumoBaseCodigo || '-'} · {lote.InsumoBaseNombre || '-'}</div>
              <div><strong>Impacto:</strong> {asMoney(lote.ImpactoEconomico)}</div>
              <div><strong>Semáforo:</strong> <Badge value={lote.Semaforo} /></div>
            </div>
          ) : null}
          {detailClaims.length ? <div><h3>Reclamos del lote</h3><ul>{detailClaims.map(function item(claim, index) { return <li key={claim.ReclamoProveedorID || index}>{claim.FolioReclamo || 'Sin folio'} · {claim.Estatus || 'SIN_ESTATUS'} · {claim.Prioridad || 'SIN_PRIORIDAD'}</li>; })}</ul></div> : null}
          {notifications.length ? <div><h3>Notificaciones</h3><ul>{notifications.map(function item(n, index) { return <li key={n.NotificacionLoteID || index}>{n.TipoNotificacion || 'Notificación'} · {n.Estatus || 'SIN_ESTATUS'}</li>; })}</ul></div> : null}
        </div>

        <div style={card}>
          <h2 style={{ marginTop: 0 }}>Abrir reclamo</h2>
          {!selected ? <p>Primero selecciona un lote.</p> : null}
          <form onSubmit={createClaim} style={{ display: 'grid', gap: 10 }}>
            <label><span>Motivo</span><input style={input} disabled={!selected || savingClaim} value={claimForm.motivo} onChange={function handle(e) { setClaim('motivo', e.target.value); }} /></label>
            <label><span>Prioridad</span><select style={input} disabled={!selected || savingClaim} value={claimForm.prioridad} onChange={function handle(e) { setClaim('prioridad', e.target.value); }}>{PRIORIDADES.map(function map(value) { return <option key={value} value={value}>{value}</option>; })}</select></label>
            <label><span>Descripción</span><textarea style={{ ...input, minHeight: 90 }} disabled={!selected || savingClaim} value={claimForm.descripcion} onChange={function handle(e) { setClaim('descripcion', e.target.value); }} /></label>
            <button type="submit" style={button} disabled={!selected || savingClaim}>{savingClaim ? 'Enviando...' : 'Crear reclamo'}</button>
          </form>
        </div>
      </section>

      <section style={card}>
        <h2 style={{ marginTop: 0 }}>Reclamos proveedor recientes</h2>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead><tr><th style={th}>Folio</th><th style={th}>Proveedor</th><th style={th}>Motivo</th><th style={th}>Prioridad</th><th style={th}>Estatus</th><th style={th}>Impacto</th></tr></thead>
          <tbody>{claims.map(function render(claim, index) { return <tr key={claim.ReclamoProveedorID || claim.FolioReclamo || index}><td style={td}><strong>{claim.FolioReclamo || 'Sin folio'}</strong></td><td style={td}>{claim.ProveedorNombre || 'Sin proveedor'}</td><td style={td}>{claim.Motivo || '-'}</td><td style={td}>{claim.Prioridad || '-'}</td><td style={td}>{claim.Estatus || 'SIN_ESTATUS'}</td><td style={td}>{asMoney(claim.ImpactoEconomico)}</td></tr>; })}</tbody>
        </table>
        {!claims.length && !loading ? <p>Sin reclamos.</p> : null}
      </section>
    </div>
  );
}
