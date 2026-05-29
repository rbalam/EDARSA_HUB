import React, { useState, useEffect } from 'react';

export default function OperacionesFlujoPanel() {
  const [cotizaciones, setCotizaciones] = useState([]);
  const [proyectos, setProyectos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Orquestación de lectura paralela local al Pool central (NO-LIVE)
    Promise.all([
      fetch('/api/crm/cotizaciones?cuenta_id=1').then(res => res.json()),
      fetch('/api/crm/implementaciones').then(res => res.json())
    ])
    .then(([dataCot, dataProy]) => {
      setCotizaciones(dataCot);
      setProyectos(dataProy);
      setLoading(false);
    })
    .catch(err => console.error("Error en flujo de operaciones local:", err));
  }, []);

  const procesarCotizacionAPedido = (cotizacionId) => {
    // Conversión transaccional síncrona sin micro-caídas de red
    fetch('/api/crm/pedidos-venta/convertir', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ CotizacionID: cotizacionId, UsuarioProcesadorID: 1 })
    })
    .then(res => res.json())
    .then(() => {
      alert("Conversión completada. Pedido Maestro Inyectado en Módulo Blindado.");
      window.location.reload();
    })
    .catch(err => console.error("Error al convertir cotización:", err));
  };

  if (loading) return <div className="p-6 text-white text-center font-mono">Cargando Módulos de Venta e Implementaciones...</div>;

  return (
    <div className="p-6 bg-slate-900 min-h-screen text-slate-100 space-y-8">
      {/* SECCIÓN DE COTIZACIONES EN MÓDULO BLINDADO */}
      <div>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold tracking-tight text-slate-200">🧾 Cotizaciones Oficiales de Venta (Fase 8 y 9)</h2>
          <span className="text-xs bg-slate-800 px-3 py-1 rounded border border-slate-700 text-slate-400 font-mono">Máxima 9: Módulo Blindado</span>
        </div>
        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden shadow-xl">
          <table className="w-full text-left">
            <thead className="bg-slate-850 text-slate-400 text-xs font-bold tracking-wider uppercase border-b border-slate-700">
              <tr>
                <th className="p-4">Folio Oficial</th>
                <th className="p-4">Total Comercial</th>
                <th className="p-4">Estatus Hub</th>
                <th className="p-4 text-right">Acción Transaccional</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700 text-sm font-mono">
              {cotizaciones.length === 0 ? (
                <tr>
                  <td colSpan="4" className="p-6 text-center text-slate-500">No se encontraron cotizaciones maestras en este registro.</td>
                </tr>
              ) : (
                cotizaciones.map(cot => (
                  <tr key={cot.CotizacionID} className="hover:bg-slate-750 transition-colors">
                    <td className="p-4 font-bold text-emerald-400">{cot.FolioCotizacion} <span className="text-slate-500 text-xs">(v{cot.Version})</span></td>
                    <td className="p-4 text-slate-200">${parseFloat(cot.Total).toLocaleString()} {cot.Moneda}</td>
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded text-xs font-bold ${cot.Estatus === 'Convertida' ? 'bg-blue-950 text-blue-400' : 'bg-slate-900 text-amber-400'}`}>
                        {cot.Estatus}
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      {cot.Estatus === 'Borrador' && (
                        <button 
                          onClick={() => procesarCotizacionAPedido(cot.CotizacionID)}
                          className="bg-blue-600 hover:bg-blue-500 text-white text-xs px-3 py-1.5 rounded font-bold transition-colors shadow-md"
                        >
                          Generar Pedido Maestro
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* SECCIÓN DE IMPLEMENTACIONES DE PROYECTO */}
      <div>
        <h2 className="text-xl font-bold mb-4 tracking-tight text-slate-200">🚀 Control de Proyectos e Implementaciones (Fase 10)</h2>
        {proyectos.length === 0 ? (
          <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 text-center text-slate-500 font-mono text-sm">
            Cero proyectos en cola de kickoff local.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {proyectos.map(proy => (
              <div key={proy.ImplementacionID} className="bg-slate-800 p-5 rounded-xl border border-slate-700 shadow-lg hover:border-slate-600 transition-all">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="font-bold text-base text-slate-100 tracking-tight">{proy.NombreProyecto}</h3>
                    <p className="text-xs text-slate-400 mt-1 font-mono">Pedido ID Vincular: {proy.PedidoID}</p>
                  </div>
                  <span className="bg-blue-950 text-blue-400 text-xs font-bold px-2.5 py-1 rounded-lg border border-blue-900 uppercase tracking-wider font-mono">
                    {proy.Estatus}
                  </span>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-xs font-semibold text-slate-400">
                    <span>Progreso Físico de Entregables</span>
                    <span className="font-mono text-slate-200">{proy.ProgresoPorcentaje}%</span>
                  </div>
                  <div className="w-full bg-slate-900 h-2.5 rounded-full overflow-hidden border border-slate-800">
                    <div className="bg-blue-500 h-full transition-all duration-500 rounded-full" style={{ width: `${proy.ProgresoPorcentaje}%` }}></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
