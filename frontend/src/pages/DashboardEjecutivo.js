import React, { useEffect, useState } from 'react';

const API_BASE = process.env.REACT_APP_BACKEND_URL || '';

function getToken() {
  return sessionStorage.getItem('edarsa_memory_token') || localStorage.getItem('token') || '';
}

export default function DashboardEjecutivo() {
  const [data, setData] = useState(null);
  const [rentabilidad, setRentabilidad] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [fechaInicio, setFechaInicio] = useState('2026-06-01');
  const [fechaFin, setFechaFin] = useState('2026-06-30');

  const fetchData = async () => {
    setLoading(true);
    setError('');

    try {
      const token = getToken();

      const [resDash, resRent] = await Promise.all([
        fetch(`${API_BASE}/api/dashboard-ejecutivo/resumen?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`${API_BASE}/api/rentabilidad/resumen`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      const dashJson = await resDash.json();
      const rentJson = await resRent.json();

      if (!dashJson.success) throw new Error(dashJson.error || 'Error dashboard ejecutivo');

      setData(dashJson);
      setRentabilidad(rentJson);
    } catch (e) {
      setError(e.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const money = (v) => Number(v || 0).toLocaleString('es-MX', { style: 'currency', currency: 'MXN' });
  const num = (v) => Number(v || 0).toLocaleString('es-MX');

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard Ejecutivo</h1>
          <p className="text-sm text-gray-600">SQL-First · Consolidado corporativo · Sin MongoDB · Sin Live visual</p>
        </div>

        <div className="flex gap-2 items-end">
          <div>
            <label className="text-xs text-gray-600">Inicio</label>
            <input className="border rounded px-3 py-2 block" type="date" value={fechaInicio} onChange={e => setFechaInicio(e.target.value)} />
          </div>
          <div>
            <label className="text-xs text-gray-600">Fin</label>
            <input className="border rounded px-3 py-2 block" type="date" value={fechaFin} onChange={e => setFechaFin(e.target.value)} />
          </div>
          <button onClick={fetchData} className="bg-blue-600 text-white px-4 py-2 rounded">Actualizar</button>
        </div>
      </div>

      {loading && <div className="bg-white rounded shadow p-4">Cargando...</div>}
      {error && <div className="bg-red-50 border border-red-200 text-red-700 rounded p-4">{error}</div>}

      {data && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <Kpi title="Ventas (neto)" value={money(data.kpis?.ventas)} />
            <Kpi title="Cheques" value={num(data.kpis?.cheques ?? data.kpis?.tickets)} />
            <Kpi title="PAX" value={num(data.kpis?.pax)} />
            <Kpi title="Cheque Prom." value={money(data.kpis?.cheque_promedio)} />
            <Kpi title="Consumo/PAX" value={money(data.kpis?.ticket_promedio ?? data.kpis?.consumo_promedio_pax)} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <Panel title="Ventas por Unidad">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left border-b">
                    <th className="py-2">Unidad</th>
                    <th className="py-2 text-right">Ventas (neto)</th>
                    <th className="py-2 text-right">Cheques</th>
                    <th className="py-2 text-right">PAX</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.ventas_por_unidad || []).map((r, i) => (
                    <tr key={i} className="border-b hover:bg-gray-50">
                      <td className="py-2">{r.unidad}</td>
                      <td className="py-2 text-right">{money(r.ventas)}</td>
                      <td className="py-2 text-right">{num(r.cheques ?? r.tickets)}</td>
                      <td className="py-2 text-right">{num(r.pax)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Panel>

            <Panel title="Catálogos Comerciales">
              <Metric label="Productos" value={num(data.productos?.productos)} />
              <Metric label="Servidores producto" value={num(data.productos?.servidores_producto)} />
              <Metric label="Productos con precio" value={num(data.precios?.productos_con_precio)} />
              <Metric label="Servidores precio" value={num(data.precios?.servidores_precio)} />
              <Metric label="Precio promedio" value={money(data.precios?.precio_promedio)} />
            </Panel>

            <Panel title="Compras / Sync">
              <Metric label="Pedidos" value={num(data.compras?.pedidos)} />
              <Metric label="Detalles" value={num(data.compras?.detalles)} />
              <Metric label="Órdenes" value={num(data.compras?.ordenes)} />
              <Metric label="Recepciones" value={num(data.compras?.recepciones)} />
            </Panel>
          </div>

          <Panel title="Rentabilidad Base">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b">
                  <th className="py-2">Servidor</th>
                  <th className="py-2 text-right">Productos</th>
                  <th className="py-2 text-right">Sin Costo</th>
                  <th className="py-2 text-right">Margen Prom.</th>
                  <th className="py-2 text-right">Precio Prom.</th>
                </tr>
              </thead>
              <tbody>
                {(rentabilidad?.data || []).map((r, i) => (
                  <tr key={i} className="border-b hover:bg-gray-50">
                    <td className="py-2">{r.servidor}</td>
                    <td className="py-2 text-right">{num(r.productos)}</td>
                    <td className="py-2 text-right">{num(r.sin_costo)}</td>
                    <td className="py-2 text-right">{r.margen_promedio_pct ? `${Number(r.margen_promedio_pct).toFixed(2)}%` : 'N/D'}</td>
                    <td className="py-2 text-right">{money(r.precio_promedio)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>

          <Panel title="Sync últimas 24h">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b">
                  <th className="py-2">Proceso</th>
                  <th className="py-2">Estado</th>
                  <th className="py-2 text-right">Eventos</th>
                  <th className="py-2 text-right">Registros</th>
                </tr>
              </thead>
              <tbody>
                {(data.sync_24h || []).map((r, i) => (
                  <tr key={i} className="border-b hover:bg-gray-50">
                    <td className="py-2">{r.sync_type}</td>
                    <td className="py-2">{r.status}</td>
                    <td className="py-2 text-right">{num(r.eventos)}</td>
                    <td className="py-2 text-right">{num(r.registros)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
        </>
      )}
    </div>
  );
}

function Kpi({ title, value }) {
  return (
    <div className="bg-white rounded shadow p-4">
      <p className="text-xs text-gray-500 uppercase">{title}</p>
      <p className="text-xl font-bold text-gray-900 mt-1">{value}</p>
    </div>
  );
}

function Panel({ title, children }) {
  return (
    <div className="bg-white rounded shadow p-4 overflow-auto">
      <h2 className="font-semibold text-gray-900 mb-3">{title}</h2>
      {children}
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="flex justify-between border-b py-2 text-sm">
      <span className="text-gray-600">{label}</span>
      <span className="font-semibold">{value}</span>
    </div>
  );
}
