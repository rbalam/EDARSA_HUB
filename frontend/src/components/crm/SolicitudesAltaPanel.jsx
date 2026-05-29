import React, { useState, useEffect } from 'react';

export default function SolicitudesAltaPanel() {
    const [solicitudes, setSolicitudes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetch('/api/crm/clientes/solicitudes')
            .then(res => {
                if (!res.ok) throw new Error('Error al consultar las solicitudes de alta.');
                return res.json();
            })
            .then(data => {
                setSolicitudes(data);
                setLoading(false);
            })
            .catch(err => {
                setError(err.message);
                setLoading(false);
            });
    }, []);

    if (loading) return <div className="p-4 text-slate-500">Cargando flujo de aprobación...</div>;
    if (error) return <div className="p-4 text-red-500">Error: {error}</div>;

    return (
        <div className="p-6 bg-slate-900 text-white rounded-lg shadow mt-6">
            <h2 className="text-xl font-bold mb-4">Workflow - Solicitudes de Alta a Cliente Maestro</h2>
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-700 text-sm">
                    <thead>
                        <tr className="text-left text-slate-400 font-semibold bg-slate-800">
                            <th className="p-3">Solicitud ID</th>
                            <th className="p-3">Cuenta / Prospecto</th>
                            <th className="p-3">RFC Solicitado</th>
                            <th className="p-3">Fecha Solicitud</th>
                            <th className="p-3">Estatus Workflow</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                        {solicitudes.map(sol => (
                            <tr key={sol.SolicitudID} className="hover:bg-slate-800/50">
                                <td className="p-3 font-mono text-purple-400">{sol.SolicitudID}</td>
                                <td className="p-3 font-medium">{sol.NombreComercial}</td>
                                <td className="p-3 font-mono text-slate-300">{sol.RFC || 'SIN RFC'}</td>
                                <td className="p-3 text-slate-400">{new Date(sol.FechaSolicitud).toLocaleString()}</td>
                                <td className="p-3">
                                    <span className="px-2 py-1 text-xs rounded bg-amber-500/20 text-amber-400 border border-amber-500/30">
                                        {sol.EstatusSolicitud}
                                    </span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
