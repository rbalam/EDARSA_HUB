import React, { useState, useEffect } from 'react';

const ETAPAS_MAESTRAS = ['Nuevo', 'Calificado', 'Diagnóstico', 'Propuesta', 'Negociación', 'Ganado', 'Perdido'];

export default function PipelineKanban() {
  const [oportunidades, setOportunidades] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/crm/pipeline')
      .then(res => res.json())
      .then(data => {
        setOportunidades(data);
        setLoading(false);
      })
      .catch(err => console.error("Error local al recuperar el pipeline SQL:", err));
  }, []);

  const ejecutarMovimientoKanban = (oportunidadId, etapaDestino) => {
    fetch(`/api/crm/oportunidades/${oportunidadId}/etapa`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ EtapaNueva: etapaDestino, UsuarioModificadorID: "1", Comentario: "Transición desde Tablero Kanban UI" })
    })
    .then(res => res.json())
    .then(() => {
      setOportunidades(prev => prev.map(op => op.OportunidadID === oportunidadId ? { ...op, Etapa: etapaDestino } : op));
    })
    .catch(err => console.error("Error en la mutación síncrona de la etapa:", err));
  };

  if (loading) return <div className="p-6 text-white text-center font-mono">Consultando Pipeline en EDARSAHUB SQL...</div>;

  return (
    <div className="p-6 bg-slate-900 min-h-screen text-slate-100">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">🏛️ Pipeline Enterprise - Tablero Kanban</h1>
          <p className="text-xs text-slate-400 mt-1">Gobernanza centralizada de leads y forecast determinista</p>
        </div>
        <div className="text-xs bg-slate-800 px-4 py-2 rounded-lg border border-slate-700 font-mono text-emerald-400">
          Fuente de Verdad: SQL Server Central
        </div>
      </div>

      <div className="grid grid-cols-7 gap-4 overflow-x-auto pb-4">
        {ETAPAS_MAESTRAS.map(etapa => (
          <div key={etapa} className="bg-slate-850 p-3 rounded-xl border border-slate-800 min-w-[260px] flex flex-col shadow-lg">
            <div className="flex justify-between items-center mb-4 pb-2 border-b border-slate-800">
              <span className="font-bold text-xs tracking-wider uppercase text-slate-400">{etapa}</span>
              <span className="bg-slate-800 px-2.5 py-0.5 rounded text-xs font-mono font-bold text-slate-200">
                {oportunidades.filter(o => o.Etapa === etapa).length}
              </span>
            </div>

            <div className="flex-1 space-y-3 min-h-[550px]" onDragOver={(e) => e.preventDefault()}>
              {oportunidades.filter(o => o.Etapa === etapa).map(op => (
                <div 
                  key={op.OportunidadID}
                  className="bg-slate-800 p-4 rounded-lg border border-slate-700 shadow-md hover:border-slate-500 transition-all cursor-grab active:cursor-grabbing"
                  draggable
                  onDragStart={(e) => e.dataTransfer.setData("text/plain", op.OportunidadID)}
                  onDrop={(e) => {
                    const id = e.dataTransfer.getData("text/plain");
                    ejecutarMovimientoKanban(id, etapa);
                  }}
                >
                  <h4 className="font-bold text-sm text-slate-200 line-clamp-1">{op.NombreOportunidad}</h4>
                  <p className="text-[11px] text-slate-500 font-mono mt-0.5">ID: {op.OportunidadID.substring(0,8)}</p>
                  <div className="flex justify-between items-center mt-4 pt-2 border-t border-slate-750">
                    <span className="text-xs font-mono font-bold text-emerald-400">${parseFloat(op.MontoEstimado).toLocaleString()}</span>
                    <span className="bg-slate-900 text-[10px] px-2 py-0.5 rounded font-bold font-mono text-slate-400">{op.Probabilidad}%</span>
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
