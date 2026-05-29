import React, { useState, useEffect } from 'react';

export default function OperacionesFlujoPanel() {
  const [cotizaciones, setCotizaciones] = useState([]);
  const [proyectos, setProyectos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch('/api/crm/cotizaciones?cuenta_id=1').then(res => res.json()),
      fetch('/api/crm/implementaciones').then(res => res.json())
    ])
    .then(([dataCot, dataProy]) => {
      setCotizaciones(dataCot);
      setProyectos(dataProy);
      setLoading(false);
    })
    .catch(err => console.error("Error al procesar el flujo transaccional:", err));
  }, []);

  const transformarCotizacionAPedido = (cotizacionId) => {
    fetch('/api/crm/pedidos-venta/convertir', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ CotizacionID: cotizacionId, UsuarioProcesadorID: 1 })
    })
    .then(res => res.json())
    .then(() => {
      alert("Operación completada exitosamente. Pedido Maestro Inyectado.");
      window.location.reload();
    })
    .catch(err => console.error("Error en la conversión a pedido:", err));
  };

  if (loading) return <div className="p-6 text-white text-center font-mono">Consultando Catálogos Maestros locales...</div>;

  return (
    <div className="p-6 bg-slate-900 min-h-screen text-slate-100 space-y-8">
      <div>
        <h2 className="text-xl font-bold mb-4 tracking-tight text-white">🧾 Cotizaciones del Núcleo Blindado (Fase 8 y 9)</h2>
        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden shadow-xl">
          <table className="w-full text-left font-mono text-sm">
            <thead className="bg-slate-850 text-slate-400 text-xs uppercase font-bold border-b border-slate-700">
              <tr>
                <th className="p-4">Folio Sistema</th>
                <th className="p-4">Importe Total</th>
                <th className="p-4">Estatus Interno</th>
                <th className="p-4 text-right">Acción Comercial</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {cotizaciones.map(cot => (
                <tr key={cot.CotizacionID} className="hover:bg-slate-750 transition-colors">
                  <td className="p-4 font-bold text-emerald-400">{cot.FolioCotizacion} <span className="text-slate-500 font-normal text-xs">(v{cot.Version})</span></td>
                  <td className="p-4 text-slate-300">${parseFloat(cot.Total).toLocaleString()} {cot.Moneda}</td>
                  <td className="p-4"><span className="px-2 py-0.5 bg-slate-900 rounded text-xs text-slate-400 border border-slate-800">{cot.Estatus}</span></td>
                  <td className="p-4 text-right">
                    {cot.Estatus === 'Borrador' && (
                      <button 
                        onClick={() => transformarCotizacionAPedido(cot.CotizacionID)}
                        className="bg-blue-600 hover:bg-blue-500 text-white text-xs px-3 py-1.5 rounded font-bold transition-colors shadow-md"
                      >
                        Convertir a Pedido
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div>
        <h2 className="text-xl font-bold mb-4 tracking-tight text-white">🚀 Cronograma de Implementación de Proyectos (Fase 10)</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {proyectos.map(proy => (
            <div key={proy.ImplementacionID} className="bg-slate-800 p-5 rounded-xl border border-slate-700 shadow-md">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="font-bold text-base text-slate-200 tracking-tight">{proy.NombreProyecto}</h3>
                  <p className="text-xs text-slate-500 font-mono mt-0.5">ID Pedido: {proy.PedidoID}</p>
                </div>
                <span className="bg-blue-950 text-blue-400 text-xs font-bold px-2.5 py-1 rounded-lg border border-blue-900 uppercase font-mono">
                  {proy.Estatus}
                </span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-xs font-semibold text-slate-400">
                  <span>Progreso de Entregables</span>
                  <span className="font-mono text-slate-200">{proy.ProgresoPorcentaje}%</span>
                </div>
                <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden border border-slate-800">
                  <div className="bg-blue-500 h-full rounded-full transition-all duration-500" style={{ width: `${proy.ProgresoPorcentaje}%` }}></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
