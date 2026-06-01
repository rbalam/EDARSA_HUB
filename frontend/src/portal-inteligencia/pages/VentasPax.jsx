import React, { useState, useEffect } from "react";

export default function VentasPax() {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('/api/inteligencia/pax')
            .then(res => res.json())
            .then(data => {
                setData(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Error cargando PAX:", err);
                setLoading(false);
            });
    }, []);

    if (loading) return <div className="p-4 text-gray-500 animate-pulse">Cargando afluencias...</div>;

    return (
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <h2 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2">
                👥 Tendencia de PAX (Afluencia)
            </h2>
            <div className="space-y-4">
                {data.map((item, i) => (
                    <div key={i} className="flex justify-between items-center border-b border-gray-50 pb-3">
                        <span className="text-gray-600 font-mono text-sm">{item.periodo}</span>
                        <span className="font-bold text-gray-800 bg-gray-100 px-3 py-1 rounded-full text-sm">
                            {item.pax.toLocaleString()} PAX
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
}