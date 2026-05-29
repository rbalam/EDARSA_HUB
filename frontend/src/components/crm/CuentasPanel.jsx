import React, { useState, useEffect } from 'react';

export default function CuentasPanel() {
    const [cuentas, setCuentas] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetch('/api/crm/cuentas')
            .then(res => {
                if (!res.ok) throw new Error('Error al consultar las cuentas comerciales.');
                return res.json();
            })
            .then(data => {
                setCuentas(data);
                setLoading(false);
            })
            .catch(err => {
                setError(err.message);
                setLoading(false);
            });
    }, []);

    if (loading) return <div className="p-4 text-slate-500">Cargando cuentas desde EDARSAHUB SQL...</div>;
    if (error) return <div className="p-4 text-red-500">Error: {error}</div>;

    return (
        <div className="p-6 bg-slate-900 text-white rounded-lg shadow">
            <h2 className="text-xl font-bold mb-4">CRM - Cuentas Comerciales / Prospectos</h2>
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-700 text-sm">
                    <thead>
                        <tr className="text-left text-slate-400 font-semibold bg-slate-800">
                            <th className="p-3">ID</th>
                            <th className="p-3">Nombre Comercial</th>
                            <th className="p-3">RFC</th>
                            <th className="p-3">Contacto</th>
                            <th className="p-3">Estatus</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                        {cuentas.map(cuenta => (
                            <tr key={cuenta.CuentaID} className="hover:bg-slate-800/50">
                                <td className="p-3 font-mono text-cyan-400">{cuenta.CuentaID}</td>
                                <td className="p-3 font-medium">{cuenta.NombreComercial}</td>
                                <td className="p-3 font-mono">{cuenta.RFC || 'N/A'}</td>
                                <td className="p-3">
                                    <div>{cuenta.EmailContacto}</div>
                                    <div className="text-xs text-slate-400">{cuenta.TelefonoContacto}</div>
                                </td>
                                <td className="p-3">
                                    <span className="px-2 py-1 text-xs rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                                        {cuenta.Estatus}
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
