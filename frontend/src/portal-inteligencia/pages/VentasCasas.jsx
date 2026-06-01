import React, { useState, useEffect } from "react";

export default function VentasCasas() {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('/api/inteligencia/casas')
            .then(res => res.json())
            .then(data => {
                setData(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Error cargando casas:", err);
                setLoading(false);
            });
    }, []);

    if (loading) return <div className="p-4 text-gray-500 animate-pulse">Cargando métricas de Casas...</div>;

    return (
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <h2 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2">
                🏠 Top Casas Comerciales
            </h2>
            <div className="space-y-4">
                {data.map((item, i) => (
                    <div key={i} className="flex justify-between items-center border-b border-gray-50 pb-3">
                        <span className="font-semibold text-gray-700">{item.casa}</span>
                        <div className="text-right">
                            <p className="text-sm font-black text-emerald-600">${item.ingresos.toLocaleString()}</p>
                            <p className="text-xs text-gray-400 font-mono">{item.porcentaje}% de participación</p>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}