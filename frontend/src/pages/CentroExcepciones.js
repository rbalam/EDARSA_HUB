import React, { useEffect, useState } from 'react';

const API_BASE = process.env.REACT_APP_BACKEND_URL || '';

function getToken() {
  return sessionStorage.getItem('edarsa_memory_token') || localStorage.getItem('token') || '';
}

export default function CentroExcepciones() {
  const [data, setData] = useState(null);
  const [limite, setLimite] = useState(200);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filtroSeveridad, setFiltroSeveridad] = useState('TODAS');

  const fetchData = async () => {
    setLoading(true);
    setError('');

    try {
      const token = getToken();
      const res = await fetch(`${API_BASE}/api/alertas-estrategicas/resumen?limite=${limite}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const json = await res.json();
      if (!json.success) throw new Error(json.error || 'Error centro de excepciones');

      setData(json);
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
  const pct = (v) => v === null || v === undefined ? 'N/D' : `${Number(v).toFixed(2)}%`;

  const alertas = (data?.alertas || []).filter(a =>
    filtroSeveridad === 'TODAS' ? true : a.severidad === filtroSeveridad
  );

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Centro de Excepciones</h1>
          <p className="text-sm text-gray-600">
            Balanced Scorecard · Alertas Estratégicas · Rentabilidad · Compras · Inventarios
          </p>
        </div>

        <div className="flex gap-2 items-end">
          <div>
            <label className="text-xs text-gray-600">Severidad</label>
            <select
              className="border rounded px-3 py-2 block"
              value={filtroSeveridad}
              onChange={e => setFiltroSeveridad(e.target.value)}
            >
              <option value="TODAS">Todas</option>
              <option value="CRITICA">Crítica</option>
              <option value="ALTA">Alta</option>
              <option value="MEDIA">Media</option>
            </select>
          </div>

          <div>
            <label className="text-xs text-gray-600">Límite</label>
            <input
              className="border rounded px-3 py-2 block w-24"
              type="number"
              value={limite}
              onChange={e => setLimite(e.target.value)}
            />
          </div>

          <button onClick={fetchData} className="bg-blue-600 text-white px-4 py-2 rounded">
            Actualizar
          </button>
        </div>
      </div>

      {loading && <div className="bg-white rounded shadow p-4">Cargando...</div>}
      {error && <div className="bg-red-50 border border-red-200 text-red-700 rounded p-4">{error}</div>}

      {data && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Kpi title="Alertas Totales" value={data.resumen?.total || 0} />
            <Kpi title="Críticas" value={data.resumen?.criticas || 0} tone="red" />
            <Kpi title="Altas" value={data.resumen?.altas || 0} tone="orange" />
            <Kpi title="Medias" value={data.resumen?.medias || 0} tone="yellow" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Panel title="Por Perspectiva BSC">
              {Object.entries(data.resumen?.por_perspectiva || {}).map(([k, v]) => (
                <Metric key={k} label={k} value={v} />
              ))}
            </Panel>

            <Panel title="Por Tipo de Excepción">
              {Object.entries(data.resumen?.por_tipo || {}).map(([k, v]) => (
                <Metric key={k} label={k} value={v} />
              ))}
            </Panel>
          </div>

          <Panel title={`Detalle de Excepciones (${alertas.length})`}>
            <div className="overflow-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left border-b">
                    <th className="py-2">Severidad</th>
                    <th className="py-2">Perspectiva</th>
                    <th className="py-2">Tipo</th>
                    <th className="py-2">Unidad</th>
                    <th className="py-2">Producto / Entidad</th>
                    <th className="py-2 text-right">Precio</th>
                    <th className="py-2 text-right">Costo</th>
                    <th className="py-2 text-right">Margen</th>
                    <th className="py-2">Acción sugerida</th>
                  </tr>
                </thead>
                <tbody>
                  {alertas.map((a, i) => (
                    <tr key={i} className="border-b hover:bg-gray-50">
                      <td className="py-2"><Badge value={a.severidad} /></td>
                      <td className="py-2">{a.perspectiva_bsc}</td>
                      <td className="py-2">{a.tipo_alerta}</td>
                      <td className="py-2">{a.unidad}</td>
                      <td className="py-2">
                        <div className="font-medium">{a.descripcion}</div>
                        <div className="text-xs text-gray-500">{a.entidad_codigo}</div>
                      </td>
                      <td className="py-2 text-right">{a.precio !== undefined ? money(a.precio) : '-'}</td>
                      <td className="py-2 text-right">{a.costo !== undefined ? money(a.costo) : '-'}</td>
                      <td className="py-2 text-right">{pct(a.margen_pct)}</td>
                      <td className="py-2">{a.accion_sugerida}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>
        </>
      )}
    </div>
  );
}

function Kpi({ title, value, tone }) {
  const cls = tone === 'red' ? 'text-red-700' : tone === 'orange' ? 'text-orange-700' : tone === 'yellow' ? 'text-yellow-700' : 'text-gray-900';
  return (
    <div className="bg-white rounded shadow p-4">
      <p className="text-xs text-gray-500 uppercase">{title}</p>
      <p className={`text-2xl font-bold mt-1 ${cls}`}>{Number(value || 0).toLocaleString('es-MX')}</p>
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
      <span className="font-semibold">{Number(value || 0).toLocaleString('es-MX')}</span>
    </div>
  );
}

function Badge({ value }) {
  const color =
    value === 'CRITICA' ? 'bg-red-100 text-red-800' :
    value === 'ALTA' ? 'bg-orange-100 text-orange-800' :
    value === 'MEDIA' ? 'bg-yellow-100 text-yellow-800' :
    'bg-gray-100 text-gray-800';

  return (
    <span className={`px-2 py-1 rounded text-xs font-semibold ${color}`}>
      {value}
    </span>
  );
}
