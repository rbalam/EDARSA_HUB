import React, { useState, useEffect } from 'react';

const ETAPAS_KANBAN = ['Nuevo', 'Calificado', 'Diagnóstico', 'Propuesta', 'Negociación', 'Ganado', 'Perdido'];

export default function PipelineKanban() {
  const [oportunidades, setOportunidades] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Lectura directa al endpoint local de la Fase 4/6
    fetch('/api/crm/pipeline')
      .then(res => res.json())
      .then(data => {
        setOportunidades(data);
        setLoading(false);
      })
      .catch(err => console.error("Error al recuperar el pipeline:", err));
  }, []);

  const moverTarjeta = (oportunidadId, nuevaEtapa) => {
    // Actualización transaccional síncrona con traza de auditoría
    fetch(`/api/crm/oportunidades/${oportunidadId}/etapa`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ EtapaNueva: nuevaEtapa, UsuarioModificadorID: 1, Comentario: "Cambio desde tablero Kanban UI" })
    })
    .then(res => res.json())
    .then(() => {
      setOportunidades(prev => prev.map(op => op.OportunidadID === oportunidadId ? { ...op, Etapa: nuevaEtapa } : op));
    });
  };

  if (loading) return <div className="p-6 text-white text-center">Cargando tablero transaccional EDARSAHUB...</div>;

  return (
    <div className="p-6 bg-slate-900 min-h-screen text-slate-100">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold tracking-tight">🏛️ Pipeline Enterprise (Kanban)</h1>
        <div className="text-sm bg-slate-800 px-4 py-2 rounded-lg border border-slate-700">
          Fuente de verdad: <span className="text-emerald-400 font-mono">EDARSAHUB SQL</span>
        </div>
      </div>

      <div className="grid grid-cols-7 gap-4 overflow-x-auto pb-4">
        {ETAPAS_KANBAN.map(etapa => (
          <div key={etapa} className="bg-slate-850 p-3 rounded-xl border border-slate-800 min-w-[250px] flex flex-col">
            <div className="flex justify-between items-center mb-3 pb-2 border-b border-slate-800">
              <span className="font-semibold text-sm tracking-wide uppercase text-slate-400">{etapa}</span>
              <span className="bg-slate-800 px-2 py-0.5 rounded text-xs font-bold text-slate-300">
                {oportunidades.filter(o => o.Etapa === etapa).length}
              </span>
            </div>

            <div className="flex-1 space-y-3 min-h-[500px]">
              {oportunidades.filter(o => o.Etapa === etapa).map(op => (
                <div 
                  key={op.OportunidadID}
                  className="bg-slate-800 p-4 rounded-lg border border-slate-700 shadow-md hover:border-slate-500 transition-all cursor-grab active:cursor-grabbing"
                  draggable
                  onDragEnd={() => {
                    const etapasClase = ['Nuevo', 'Calificado', 'Diagnóstico', 'Propuesta', 'Negociación', 'Ganado', 'Perdido'];
                    // Lógica de simulación de drop rápido para el agente síncrono
                  }}
                >
                  <h4 className="font-bold text-sm text-slate-200 mb-1">{op.NombreOportunidad}</h4>
                  <div className="text-xs text-slate-400 mb-2 font-mono">ID: {op.OportunidadID.substring(0,8)}...</div>
                  <div className="flex justify-between items-center mt-3 pt-2 border-t border-slate-705">
                    <span className="text-xs font-semibold text-emerald-400">${parseFloat(op.MontoEstimado).toLocaleString()}</span>
                    <span className="bg-slate-900 text-[10px] px-2 py-0.5 rounded text-slate-400 font-bold">{op.Probabilidad}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
