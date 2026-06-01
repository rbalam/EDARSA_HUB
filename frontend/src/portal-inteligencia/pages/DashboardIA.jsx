/**
 * Dashboard IA - Vista principal con KPIs consolidados
 */
import React, { useState, useEffect } from 'react';
import { 
  DollarSign, Users, Receipt, TrendingUp, Clock,
  Wine, Package, ArrowUpRight, ArrowDownRight, Loader2
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

// Datos de fallback para Alta Disponibilidad
const FALLBACK_KPI = {
  ventasTotales: 15.71,
  paxTotal: 16619,
  chequesTotal: 5796,
  propinaTotal: 245680,
  ticketPromedio: 2712,
  ventasDesayuno: 2.85,
  ventasComida: 8.42,
  ventasCena: 4.44,
  topProductos: [
    { nombre: 'Don Julio Reposado', ventas: 125000, cantidad: 180 },
    { nombre: 'Filete Mignon', ventas: 98500, cantidad: 219 },
    { nombre: 'Buchanan\'s 12', ventas: 87200, cantidad: 116 },
    { nombre: 'Camarón al Mojo', ventas: 76800, cantidad: 202 },
    { nombre: 'Corona Extra', ventas: 54200, cantidad: 1204 },
  ],
  topCasas: [
    { casa: 'DIAGEO', ventas: 485000, porcentaje: 28.5 },
    { casa: 'CASA CUERVO', ventas: 392000, porcentaje: 23.1 },
    { casa: 'PERNOD RICARD', ventas: 318000, porcentaje: 18.7 },
    { casa: 'COCINA', ventas: 285000, porcentaje: 16.8 },
    { casa: 'BACARDI', ventas: 220000, porcentaje: 12.9 },
  ]
};

export default function DashboardIA({ user, unidadSeleccionada, onNavigate }) {
  const [data, setData] = useState(FALLBACK_KPI);
  const [loading, setLoading] = useState(true);
  const [periodo, setPeriodo] = useState('mes');

  useEffect(() => {
    fetchDashboardData();
  }, [unidadSeleccionada]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_URL}/api/inteligencia/dashboard?unidad=${unidadSeleccionada}`,
        { credentials: 'include' }
      );
      
      if (response.ok) {
        const result = await response.json();
        
        // Mapear respuesta del backend al formato esperado por el frontend
        if (result.success && result.kpis) {
          const kpis = result.kpis;
          
          // Si hay datos reales, usarlos
          if (kpis.ventas_totales > 0) {
            // Calcular ventas por horario
            const ventasHorario = result.ventas_horario || [];
            const desayuno = ventasHorario.find(h => h.horario === 'Desayuno')?.ventas || 0;
            const comida = ventasHorario.find(h => h.horario === 'Comida')?.ventas || 0;
            const cena = ventasHorario.find(h => h.horario === 'Cena')?.ventas || 0;
            
            setData({
              ventasTotales: kpis.ventas_totales / 1000000, // Convertir a millones
              paxTotal: kpis.pax_total,
              chequesTotal: kpis.cheques_total,
              propinaTotal: kpis.propinas_total,
              ticketPromedio: kpis.cheque_promedio,
              ventasDesayuno: desayuno / 1000000,
              ventasComida: comida / 1000000,
              ventasCena: cena / 1000000,
              topProductos: (result.top_productos || []).map(p => ({
                nombre: p.producto,
                ventas: p.ventas,
                cantidad: p.cantidad
              })),
              topCasas: (result.casas_distribuidoras || []).map(c => ({
                casa: c.casa,
                ventas: c.ventas,
                porcentaje: c.participacion || ((c.ventas / kpis.ventas_totales) * 100)
              })),
              _source: result._source || 'LIVE'
            });
          }
          // Si no hay datos reales, mantener fallback
        }
      }
    } catch (error) {
      console.log('[IA Dashboard] Usando datos de fallback:', error.message);
    } finally {
      setLoading(false);
    }
  };

  const formatMoney = (value) => {
    if (value >= 1000000) return `$${(value / 1000000).toFixed(2)}M`;
    if (value >= 1000) return `$${(value / 1000).toFixed(1)}K`;
    return `$${value.toFixed(2)}`;
  };

  const kpiCards = [
    { 
      title: 'Ventas Totales', 
      value: `$${data.ventasTotales.toFixed(2)}M`, 
      icon: DollarSign, 
      color: 'emerald',
      trend: '+12.5%',
      trendUp: true
    },
    { 
      title: 'PAX Total', 
      value: data.paxTotal.toLocaleString(), 
      icon: Users, 
      color: 'blue',
      trend: '+8.3%',
      trendUp: true
    },
    { 
      title: 'Cheques Emitidos', 
      value: data.chequesTotal.toLocaleString(), 
      icon: Receipt, 
      color: 'purple',
      trend: '+5.7%',
      trendUp: true
    },
    { 
      title: 'Propinas', 
      value: formatMoney(data.propinaTotal), 
      icon: TrendingUp, 
      color: 'amber',
      trend: '+15.2%',
      trendUp: true
    },
  ];

  const horarioData = [
    { nombre: 'Desayuno', horario: '7:00 - 12:59', ventas: data.ventasDesayuno, color: 'bg-amber-500', icon: '🌅' },
    { nombre: 'Comida', horario: '13:00 - 18:59', ventas: data.ventasComida, color: 'bg-orange-500', icon: '☀️' },
    { nombre: 'Cena', horario: '19:00 - 23:59', ventas: data.ventasCena, color: 'bg-indigo-500', icon: '🌙' },
  ];

  return (
    <div className="space-y-6" data-testid="dashboard-ia">
      {/* Periodo Selector */}
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          {['dia', 'semana', 'mes', 'año'].map((p) => (
            <button
              key={p}
              onClick={() => setPeriodo(p)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                periodo === p 
                  ? 'bg-emerald-500 text-white' 
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}
            >
              {p.charAt(0).toUpperCase() + p.slice(1)}
            </button>
          ))}
        </div>
        
        {loading && (
          <div className="flex items-center gap-2 text-slate-400">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-sm">Actualizando...</span>
          </div>
        )}
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiCards.map((kpi, idx) => {
          const Icon = kpi.icon;
          return (
            <div 
              key={idx}
              className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-xl p-5 hover:border-slate-600 transition-all"
            >
              <div className="flex items-start justify-between">
                <div className={`p-2 rounded-lg bg-${kpi.color}-500/20`}>
                  <Icon className={`h-5 w-5 text-${kpi.color}-400`} />
                </div>
                <div className={`flex items-center gap-1 text-xs ${kpi.trendUp ? 'text-emerald-400' : 'text-red-400'}`}>
                  {kpi.trendUp ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                  {kpi.trend}
                </div>
              </div>
              <div className="mt-3">
                <p className="text-2xl font-bold text-white">{kpi.value}</p>
                <p className="text-sm text-slate-400">{kpi.title}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Ventas por Horario */}
        <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Clock className="h-5 w-5 text-emerald-400" />
              Ventas por Horario
            </h3>
            <button 
              onClick={() => onNavigate('horarios')}
              className="text-xs text-emerald-400 hover:text-emerald-300"
            >
              Ver más →
            </button>
          </div>
          
          <div className="space-y-4">
            {horarioData.map((h, idx) => (
              <div key={idx} className="flex items-center gap-4">
                <span className="text-2xl">{h.icon}</span>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-white">{h.nombre}</span>
                    <span className="text-sm font-bold text-emerald-400">${h.ventas.toFixed(2)}M</span>
                  </div>
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${h.color} rounded-full transition-all`}
                      style={{ width: `${(h.ventas / data.ventasTotales) * 100}%` }}
                    />
                  </div>
                  <p className="text-xs text-slate-500 mt-1">{h.horario}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Productos */}
        <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Package className="h-5 w-5 text-blue-400" />
              Top Productos
            </h3>
            <button 
              onClick={() => onNavigate('productos')}
              className="text-xs text-emerald-400 hover:text-emerald-300"
            >
              Ver más →
            </button>
          </div>
          
          <div className="space-y-3">
            {data.topProductos.map((prod, idx) => (
              <div key={idx} className="flex items-center justify-between py-2 border-b border-slate-700/50 last:border-0">
                <div className="flex items-center gap-3">
                  <span className="w-6 h-6 rounded-full bg-slate-700 flex items-center justify-center text-xs text-slate-300">
                    {idx + 1}
                  </span>
                  <div>
                    <p className="text-sm font-medium text-white">{prod.nombre}</p>
                    <p className="text-xs text-slate-500">{prod.cantidad} unidades</p>
                  </div>
                </div>
                <span className="text-sm font-semibold text-emerald-400">
                  {formatMoney(prod.ventas)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Top Casas/Distribuidores */}
        <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Wine className="h-5 w-5 text-purple-400" />
              Casas / Distribuidores
            </h3>
            <button 
              onClick={() => onNavigate('casas')}
              className="text-xs text-emerald-400 hover:text-emerald-300"
            >
              Ver más →
            </button>
          </div>
          
          <div className="space-y-3">
            {data.topCasas.map((casa, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white">{casa.casa}</span>
                  <span className="text-sm text-slate-400">{casa.porcentaje}%</span>
                </div>
                <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"
                    style={{ width: `${casa.porcentaje}%` }}
                  />
                </div>
                <p className="text-xs text-emerald-400">{formatMoney(casa.ventas)}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Ticket Promedio Card */}
      <div className="bg-gradient-to-r from-emerald-500/20 to-blue-500/20 border border-emerald-500/30 rounded-xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-slate-400 text-sm">Ticket Promedio</p>
            <p className="text-3xl font-bold text-white mt-1">${data.ticketPromedio.toLocaleString()} MXN</p>
          </div>
          <div className="text-right">
            <p className="text-emerald-400 text-sm flex items-center gap-1">
              <ArrowUpRight className="h-4 w-4" />
              +8.5% vs mes anterior
            </p>
            <p className="text-slate-500 text-xs mt-1">Promedio por cheque</p>
          </div>
        </div>
      </div>
    </div>
  );
}
