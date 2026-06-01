/**
 * Ventas por Horario - Desayuno / Comida / Cena
 */
import React, { useState, useEffect } from 'react';
import { Clock, Sun, Sunset, Moon, TrendingUp, Users, DollarSign } from 'lucide-react';

const FALLBACK_HORARIOS = {
  desayuno: {
    nombre: 'Desayuno',
    horario: '7:00 AM - 12:59 PM',
    icon: 'sun',
    ventas: 2850000,
    pax: 4520,
    cheques: 1580,
    ticketPromedio: 1803,
    propinas: 85200,
    topProductos: [
      { nombre: 'Huevos Rancheros', ventas: 145000 },
      { nombre: 'Chilaquiles Verdes', ventas: 128500 },
      { nombre: 'Café Americano', ventas: 98200 },
    ]
  },
  comida: {
    nombre: 'Comida',
    horario: '1:00 PM - 6:59 PM',
    icon: 'sunset',
    ventas: 8420000,
    pax: 8650,
    cheques: 2890,
    ticketPromedio: 2914,
    propinas: 168400,
    topProductos: [
      { nombre: 'Filete Mignon', ventas: 425000 },
      { nombre: 'Don Julio Reposado', ventas: 385000 },
      { nombre: 'Camarón al Mojo', ventas: 312000 },
    ]
  },
  cena: {
    nombre: 'Cena',
    horario: '7:00 PM - 11:59 PM',
    icon: 'moon',
    ventas: 4440000,
    pax: 3449,
    cheques: 1326,
    ticketPromedio: 3348,
    propinas: 133200,
    topProductos: [
      { nombre: 'Buchanan\'s 12 Años', ventas: 298000 },
      { nombre: 'Rib Eye Premium', ventas: 265000 },
      { nombre: 'Moët & Chandon', ventas: 198000 },
    ]
  }
};

export default function VentasHorarioPage({ unidadSeleccionada }) {
  const [data, setData] = useState(FALLBACK_HORARIOS);
  const [selectedPeriodo, setSelectedPeriodo] = useState(null);

  const formatMoney = (val) => {
    if (val >= 1000000) return `$${(val / 1000000).toFixed(2)}M`;
    if (val >= 1000) return `$${(val / 1000).toFixed(1)}K`;
    return `$${val.toFixed(0)}`;
  };

  const totalVentas = Object.values(data).reduce((a, b) => a + b.ventas, 0);

  const getIcon = (iconName) => {
    switch (iconName) {
      case 'sun': return <Sun className="h-8 w-8" />;
      case 'sunset': return <Sunset className="h-8 w-8" />;
      case 'moon': return <Moon className="h-8 w-8" />;
      default: return <Clock className="h-8 w-8" />;
    }
  };

  const getGradient = (periodo) => {
    switch (periodo) {
      case 'desayuno': return 'from-amber-500 to-orange-500';
      case 'comida': return 'from-orange-500 to-red-500';
      case 'cena': return 'from-indigo-500 to-purple-500';
      default: return 'from-slate-500 to-slate-600';
    }
  };

  const getBgColor = (periodo) => {
    switch (periodo) {
      case 'desayuno': return 'bg-amber-500/20 border-amber-500/30 text-amber-400';
      case 'comida': return 'bg-orange-500/20 border-orange-500/30 text-orange-400';
      case 'cena': return 'bg-indigo-500/20 border-indigo-500/30 text-indigo-400';
      default: return 'bg-slate-500/20';
    }
  };

  return (
    <div className="space-y-6" data-testid="ventas-horario-page">
      {/* Cards principales por horario */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {Object.entries(data).map(([key, periodo]) => {
          const porcentaje = ((periodo.ventas / totalVentas) * 100).toFixed(1);
          const isSelected = selectedPeriodo === key;
          
          return (
            <div
              key={key}
              onClick={() => setSelectedPeriodo(isSelected ? null : key)}
              className={`relative overflow-hidden rounded-2xl cursor-pointer transition-all transform hover:scale-[1.02] ${
                isSelected ? 'ring-2 ring-emerald-400' : ''
              }`}
            >
              {/* Gradient Background */}
              <div className={`absolute inset-0 bg-gradient-to-br ${getGradient(key)} opacity-20`} />
              
              <div className="relative p-6 bg-slate-800/80 backdrop-blur">
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className={`p-3 rounded-xl ${getBgColor(key)}`}>
                    {getIcon(periodo.icon)}
                  </div>
                  <div className="text-right">
                    <span className="text-3xl font-bold text-white">{porcentaje}%</span>
                    <p className="text-xs text-slate-400">del total</p>
                  </div>
                </div>

                {/* Info */}
                <h3 className="text-xl font-bold text-white mb-1">{periodo.nombre}</h3>
                <p className="text-sm text-slate-400 mb-4">{periodo.horario}</p>

                {/* Ventas */}
                <div className="mb-4">
                  <p className="text-3xl font-bold text-emerald-400">{formatMoney(periodo.ventas)}</p>
                </div>

                {/* Stats grid */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-700/50 rounded-lg p-3">
                    <div className="flex items-center gap-2 text-slate-400 mb-1">
                      <Users className="h-4 w-4" />
                      <span className="text-xs">PAX</span>
                    </div>
                    <p className="text-lg font-semibold text-white">{periodo.pax.toLocaleString()}</p>
                  </div>
                  <div className="bg-slate-700/50 rounded-lg p-3">
                    <div className="flex items-center gap-2 text-slate-400 mb-1">
                      <DollarSign className="h-4 w-4" />
                      <span className="text-xs">Ticket Prom.</span>
                    </div>
                    <p className="text-lg font-semibold text-white">${periodo.ticketPromedio.toLocaleString()}</p>
                  </div>
                </div>

                {/* Barra de progreso */}
                <div className="mt-4">
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div 
                      className={`h-full bg-gradient-to-r ${getGradient(key)} rounded-full`}
                      style={{ width: `${porcentaje}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Detalle del periodo seleccionado */}
      {selectedPeriodo && (
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 animate-in slide-in-from-top-4">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-emerald-400" />
            Top Productos - {data[selectedPeriodo].nombre}
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {data[selectedPeriodo].topProductos.map((prod, idx) => (
              <div 
                key={idx}
                className="flex items-center gap-4 bg-slate-700/30 rounded-lg p-4"
              >
                <span className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                  idx === 0 ? 'bg-amber-500 text-black' :
                  idx === 1 ? 'bg-slate-400 text-black' :
                  'bg-orange-700 text-white'
                }`}>
                  {idx + 1}
                </span>
                <div className="flex-1">
                  <p className="text-sm font-medium text-white">{prod.nombre}</p>
                  <p className="text-lg font-bold text-emerald-400">{formatMoney(prod.ventas)}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Estadísticas adicionales */}
          <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-slate-700/30 rounded-lg">
              <p className="text-2xl font-bold text-white">{data[selectedPeriodo].cheques.toLocaleString()}</p>
              <p className="text-xs text-slate-400">Cheques Emitidos</p>
            </div>
            <div className="text-center p-4 bg-slate-700/30 rounded-lg">
              <p className="text-2xl font-bold text-white">{data[selectedPeriodo].pax.toLocaleString()}</p>
              <p className="text-xs text-slate-400">PAX Total</p>
            </div>
            <div className="text-center p-4 bg-slate-700/30 rounded-lg">
              <p className="text-2xl font-bold text-blue-400">{formatMoney(data[selectedPeriodo].propinas)}</p>
              <p className="text-xs text-slate-400">Propinas</p>
            </div>
            <div className="text-center p-4 bg-slate-700/30 rounded-lg">
              <p className="text-2xl font-bold text-emerald-400">${data[selectedPeriodo].ticketPromedio.toLocaleString()}</p>
              <p className="text-xs text-slate-400">Ticket Promedio</p>
            </div>
          </div>
        </div>
      )}

      {/* Comparativa rápida */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Comparativa de Horarios</h3>
        <div className="space-y-4">
          {Object.entries(data).map(([key, periodo]) => {
            const porcentaje = ((periodo.ventas / totalVentas) * 100);
            return (
              <div key={key} className="flex items-center gap-4">
                <div className="w-24 text-sm text-slate-400">{periodo.nombre}</div>
                <div className="flex-1 h-8 bg-slate-700 rounded-lg overflow-hidden relative">
                  <div 
                    className={`h-full bg-gradient-to-r ${getGradient(key)} rounded-lg transition-all`}
                    style={{ width: `${porcentaje}%` }}
                  />
                  <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-white font-medium">
                    {formatMoney(periodo.ventas)}
                  </span>
                </div>
                <div className="w-16 text-right text-sm text-slate-400">{porcentaje.toFixed(1)}%</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
