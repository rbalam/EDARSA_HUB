import React, { useState, useEffect } from 'react';

export default function ActividadesPanel() {
  const [actividades, setActividades] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Consumo síncrono local al pool de EDARSAHUB SQL
    fetch('/api/crm/actividades')
      .then(res => res.json())
      .then(data => {
        setActividades(data);
        setLoading(false);
      })
      .catch(err => console.error("Error al recuperar la agenda de actividades:", err));
  }, []);

  const cambiarEstatusActividad = (actividadId, nuevoEstatus) => {
    // Mutación transaccional con auditoría forzada nativa
    fetch(`/api/crm/actividades/${actividadId}/estatus`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ EstatusNuevo: nuevoEstatus, ComentarioAuditoria: "Actualizado desde panel de agenda UI" })
    })
    .then(res => res.json())
    .then(() => {
      setActividades(prev => prev.map(act => act.ActividadID === actividadId ? { ...act, Estatus: nuevoEstatus } : act));
    })
    .catch(err => console.error("Error al actualizar estatus de actividad:", err));
  };

  if (loading) return <div className="p-6 text-white text-center font-mono">Cargando Agenda de Actividades locales...</div>;

  return (
    <div className="p-6 bg-slate-900 min-h-screen text-slate-100">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">📅 Agenda e Interacciones Comerciales</h1>
          <p className="text-xs text-slate-400 mt-1">Módulo de auditoría de llamadas, WhatsApp, correos y demostraciones</p>
        </div>
        <div className="text-xs bg-slate-800 px-4 py-2 rounded-lg border border-slate-700 font-mono">
          Estatus: <span className="text-emerald-400">SQL-First (NO-LIVE)</span>
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden shadow-2xl">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-850 text-slate-400 uppercase text-[11px] font-bold tracking-wider border-b border-slate-700">
              <th className="p-4">Tipo</th>
              <th className="p-4">Asunto / Interacción</th>
              <th className="p-4">Fecha Programada</th>
              <th className="p-4">Estatus</th>
              <th className="p-4 text-right">Acciones de Auditoría</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700 text-sm">
            {actividades.length === 0 ? (
              <tr>
                <td colSpan="5" className="p-8 text-center text-slate-500 font-mono">No hay actividades registradas en el Hub local para este periodo.</td>
              </tr>
            ) : (
              actividades.map(act => (
                <tr key={act.ActividadID} className="hover:bg-slate-750 transition-colors">
                  <td className="p-4 font-semibold">
                    <span className={`px-2.5 py-1 rounded text-xs font-bold ${
                      act.TipoActividad === 'WhatsApp' ? 'bg-emerald-950 text-emerald-400 border border-emerald-900' :
                      act.TipoActividad === 'Llamada' ? 'bg-blue-950 text-blue-400 border border-blue-900' : 
                      act.TipoActividad === 'Demo' ? 'bg-purple-950 text-purple-400 border border-purple-900' : 'bg-slate-900 text-slate-400'
                    }`}>
                      {act.TipoActividad}
                    </span>
                  </td>
                  <td className="p-4">
                    <div className="font-bold text-slate-200">{act.Asunto}</div>
                    <div className="text-xs text-slate-400 mt-1">{act.NotasInteraccion}</div>
                  </td>
                  <td className="p-4 font-mono text-xs text-slate-300">{act.FechaProgramada}</td>
                  <td className="p-4">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      act.Estatus === 'Completada' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                      act.Estatus === 'Vencida' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                    }`}>
                      {act.Estatus}
                    </span>
                  </td>
                  <td className="p-4 text-right">
                    {act.Estatus === 'Pendiente' && (
                      <div className="flex justify-end gap-2">
                        <button 
                          onClick={() => cambiarEstatusActividad(act.ActividadID, 'Completada')}
                          className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs px-3 py-1.5 rounded font-bold transition-colors shadow-md"
                        >
                          Completar
                        </button>
                        <button 
                          onClick={() => cambiarEstatusActividad(act.ActividadID, 'Cancelada')}
                          className="bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs px-3 py-1.5 rounded font-bold transition-colors border border-slate-600"
                        >
                          Cancelar
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
