import React, { useState, useEffect } from 'react';

export default function KPIDashboardIA() {
  const [kpis, setKpis] = useState(null);
  const [iaSalud, setIaSalud] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch('/api/crm/kpis?mes=5&anio=2026').then(res => res.json()),
      fetch('/api/crm/ia/salud-comercial?usuario_id=1&mes=5&anio=2026').then(res => res.json())
    ])
    .then(([dataKpi, dataIa]) => {
      setKpis(dataKpi);
      setIaSalud(dataIa);
      setLoading(false);
    })
    .catch(err => console.error("Error al procesar la capa de analítica local de IA:", err));
  }, []);

  if (loading) return <div className="p-6 text-white text-center font-mono">Invocando Algoritmos Analíticos Locales...</div>;

  return (
    <div className="p-6 bg-slate-900 min-h-screen text-slate-100 space-y-6">
      <h1 className="text-2xl font-bold tracking-tight text-white">📊 Inteligencia de Negocio y Forecast Predictivo</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-800 p-5 rounded-xl border border-slate-700 shadow-sm font-mono">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider font-sans">Monto Cerrado Ganado</div>
          <div className="text-2xl font-bold text-emerald-400 mt-2">${kpis?.TotalOportunidadesMonto?.toLocaleString()}</div>
        </div>
        <div className="bg-slate-800 p-5 rounded-xl border border-slate-700 shadow-sm font-mono">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider font-sans">Efectividad Conversión</div>
          <div className="text-2xl font-bold text-slate-100 mt-2">{kpis?.TasaConversiónLeads}%</div>
        </div>
        <div className="bg-slate-800 p-5 rounded-xl border border-slate-700 shadow-sm font-mono">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider font-sans">Interacciones Registradas</div>
          <div className="text-2xl font-bold text-slate-100 mt-2">{kpis?.TotalActividadesEjecutadas}</div>
        </div>
        <div className="bg-slate-800 p-5 rounded-xl border border-slate-700 shadow-sm font-mono">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider font-sans">Índice Satisfacción (CSAT)</div>
          <div className="text-2xl font-bold text-amber-400 mt-2">{kpis?.IndiceSatisfaccionCSAT} / 5.0</div>
        </div>
      </div>

      <div className="bg-slate-850 p-6 rounded-xl border border-slate-750 shadow-2xl">
        <div className="flex items-center gap-2.5 mb-4 pb-2 border-b border-slate-800">
          <span className="text-xl">🧠</span>
          <h3 className="font-bold text-lg text-white tracking-tight">Dictamen Técnico del Agente de IA Centralizado</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 space-y-2">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400">Recomendación Ejecutiva Local</div>
            <div className="bg-slate-900 p-4 rounded-lg border border-slate-800 text-sm text-slate-300 font-mono whitespace-pre-line leading-relaxed">
              {iaSalud?.RecomendacionAgente ?? "Sin anomalías métricas detectadas en el periodo actual."}
            </div>
          </div>
          
          <div className="bg-slate-900 p-4 rounded-lg border border-slate-800 flex flex-col justify-center items-center text-center font-mono">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 font-sans">Alerta de Desviación Financiera</div>
            <span className={`px-4 py-1.5 rounded-full text-xs font-bold border ${
              iaSalud?.AlertaDesviacionMeta ? 'bg-rose-500/10 text-rose-400 border-rose-900' : 'bg-emerald-500/10 text-emerald-400 border-emerald-900'
            }`}>
              {iaSalud?.AlertaDesviacionMeta ? "⚠️ CRÍTICA DETECTADA" : "✅ FLUJO NOMINAL"}
            </span>
            <div className="text-xs text-slate-500 mt-3">
              Cumplimiento Cuota: <span className="text-slate-300 font-bold">{iaSalud?.MetasAlcanzadasPorcentaje}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
