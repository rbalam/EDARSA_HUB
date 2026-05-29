import React, { useState, useEffect } from 'react';

export default function ActividadesPanel({ usuarioId = 1 }) { // Por defecto ID 1 para ejecuciones base
    const [actividades, setActividades] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetch(`/api/crm/actividades?usuario_id=${usuarioId}`)
            .then(res => {
                if (!res.ok) throw new Error('Error al consultar la agenda de actividades.');
                return res.json();
            })
            .then(data => {
                setActividades(data);
                setLoading(false);
            })
            .catch(err => {
                setError(err.message);
                setLoading(false);
            });
    }, [usuarioId]);

    const actualizarEstatus = (actividadId, nuevoEstatus) => {
        const comentario = prompt("Escriba un comentario para la auditoría histórica:");
        if (comentario === null) return; // Cancelado por el usuario

        fetch(`/api/crm/actividades/${actividadId}/estatus`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                EstatusNuevo: nuevoEstatus,
                UsuarioModificadorID: usuarioId,
                Comentario: comentario
            })
        })
        .then(res => {
            if (!res.ok) throw new Error('No se pudo actualizar el estatus.');
            return res.json();
        })
        .then(() => {
            // Refrescar estado local reactivamente
            setActividades(prev => prev.map(act => 
                act.ActividadID === actividadId ? { ...act, Estatus: nuevoEstatus } : act
            ));
        })
        .catch(err => alert(err.message));
    };

    if (loading) return <div className="p-4 text-slate-500">Cargando agenda comercial...</div>;
    if (error) return <div className="p-4 text-red-500">Error: {error}</div>;

    return (
        <div className="p-6 bg-slate-900 text-white rounded-lg shadow mt-6">
            <h2 className="text-xl font-bold mb-4">Agenda Comercial - Rastreo de Actividades e Interacciones</h2>
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-700 text-sm">
                    <thead>
                        <tr className="text-left text-slate-400 font-semibold bg-slate-800">
                            <th className="p-3">ID Actividad</th>
                            <th className="p-3">Tipo</th>
                            <th className="p-3">Asunto / Tarea</th>
                            <th className="p-3">Fecha Programada</th>
                            <th className="p-3">Estatus</th>
                            <th className="p-3">Acciones de Control</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                        {actividades.map(act => (
                            <tr key={act.ActividadID} className="hover:bg-slate-800/50">
                                <td className="p-3 font-mono text-emerald-400">{act.ActividadID}</td>
                                <td className="p-3">
                                    <span className="px-2 py-0.5 text-xs rounded bg-slate-700 text-slate-200">
                                        {act.TipoActividad}
                                    </span>
                                </td>
                                <td className="p-3 font-medium">{act.Asunto}</td>
                                <td className="p-3 text-slate-400">{new Date(act.FechaProgramada).toLocaleString()}</td>
                                <td className="p-3">
                                    <span className={`px-2 py-1 text-xs rounded border ${
                                        act.Estatus === 'Completada' ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' :
                                        act.Estatus === 'Cancelada' ? 'bg-rose-500/20 text-rose-400 border-rose-500/30' :
                                        'bg-amber-500/20 text-amber-400 border-amber-500/30'
                                    }`}>
                                        {act.Estatus}
                                    </span>
                                </td>
                                <td className="p-3">
                                    {act.Estatus === 'Pendiente' && (
                                        <div className="flex gap-2">
                                            <button 
                                                onClick={() => actualizarEstatus(act.ActividadID, 'Completada')}
                                                className="px-2 py-1 text-xs bg-emerald-600 hover:bg-emerald-500 rounded text-white font-medium transition"
                                            >
                                                Completar
                                            </button>
                                            <button 
                                                onClick={() => actualizarEstatus(act.ActividadID, 'Cancelada')}
                                                className="px-2 py-1 text-xs bg-rose-600 hover:bg-rose-500 rounded text-white font-medium transition"
                                            >
                                                Cancelar
                                            </button>
                                        </div>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
