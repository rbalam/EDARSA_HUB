/**
 * SLACard.jsx - Tarjeta de Estado SLA con Semáforo
 * CAB-003 | Fase 2B.4
 * EDARSA HUB
 * 
 * Muestra métricas de cumplimiento SLA con indicadores de color.
 */

import { useState, useEffect } from 'react';
// FASE AUTH-SECURITY-01 / FASE 4.1: getToken eliminado, auth viaja en cookie httpOnly
import { 
  Gauge,
  Clock,
  AlertTriangle,
  XCircle,
  RefreshCw,
  TrendingUp
} from 'lucide-react';

const API_BASE = process.env.REACT_APP_BACKEND_URL || '';

// Indicador circular de semáforo
const SemaforoIndicador = ({ valor, label, color, icon: Icon }) => {
  const colorClasses = {
    green: 'bg-green-500 text-white',
    yellow: 'bg-yellow-500 text-white',
    orange: 'bg-orange-500 text-white',
    red: 'bg-red-500 text-white',
    zinc: 'bg-zinc-300 text-zinc-600',
  };

  return (
    <div className="flex flex-col items-center">
      <div className={`w-12 h-12 rounded-full flex items-center justify-center ${colorClasses[color]}`}>
        {Icon && <Icon className="h-5 w-5" />}
        {!Icon && <span className="text-lg font-bold">{valor}</span>}
      </div>
      <span className="text-xs text-zinc-500 mt-1 text-center">{label}</span>
    </div>
  );
};

// Barra de progreso de cumplimiento
const CumplimientoBarra = ({ porcentaje }) => {
  const getColor = (p) => {
    if (p >= 80) return 'bg-green-500';
    if (p >= 60) return 'bg-yellow-500';
    if (p >= 40) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <div className="w-full">
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm font-medium text-zinc-700">Cumplimiento SLA</span>
        <span className={`text-lg font-bold ${
          porcentaje >= 80 ? 'text-green-600' : 
          porcentaje >= 60 ? 'text-yellow-600' : 
          porcentaje >= 40 ? 'text-orange-600' : 'text-red-600'
        }`}>
          {porcentaje}%
        </span>
      </div>
      <div className="w-full bg-zinc-200 rounded-full h-2.5">
        <div 
          className={`h-2.5 rounded-full transition-all duration-500 ${getColor(porcentaje)}`}
          style={{ width: `${Math.min(100, porcentaje)}%` }}
        ></div>
      </div>
    </div>
  );
};

const SLACard = () => {
  const [metricas, setMetricas] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const cargarMetricas = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/v2/sla/metricas`, {
        credentials: 'include'
      });
      if (!response.ok) throw new Error('Error al cargar métricas SLA');
      const data = await response.json();
      setMetricas(data.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    cargarMetricas();
  }, []);

  // Loading state
  if (loading) {
    return (
      <div className="rounded-lg border border-zinc-200 bg-white p-4 animate-pulse" data-testid="sla-card-loading">
        <div className="h-5 bg-zinc-200 rounded w-32 mb-4"></div>
        <div className="h-3 bg-zinc-200 rounded w-full mb-2"></div>
        <div className="flex justify-around mt-4">
          <div className="w-12 h-12 bg-zinc-200 rounded-full"></div>
          <div className="w-12 h-12 bg-zinc-200 rounded-full"></div>
          <div className="w-12 h-12 bg-zinc-200 rounded-full"></div>
          <div className="w-12 h-12 bg-zinc-200 rounded-full"></div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4" data-testid="sla-card-error">
        <div className="flex items-center justify-between">
          <p className="text-red-700 text-sm">{error}</p>
          <button 
            onClick={cargarMetricas}
            className="text-red-600 hover:text-red-800"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>
    );
  }

  if (!metricas) return null;

  const { cumplimiento, activas } = metricas;
  const porEstado = activas?.por_estado || {};
  
  // Determinar color del header según estado general
  const totalProblemas = (porEstado.ADVERTENCIA || 0) + (porEstado.URGENTE || 0) + (porEstado.VENCIDA || 0);
  const headerColor = totalProblemas === 0 
    ? 'border-green-200 bg-green-50' 
    : porEstado.VENCIDA > 0 
      ? 'border-red-200 bg-red-50'
      : porEstado.URGENTE > 0
        ? 'border-orange-200 bg-orange-50'
        : 'border-yellow-200 bg-yellow-50';

  return (
    <div 
      className={`rounded-lg border ${headerColor} p-4 transition-colors`}
      data-testid="sla-card"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Gauge className="h-5 w-5 text-zinc-600" />
          <h3 className="font-semibold text-zinc-800">Estado SLA</h3>
        </div>
        <button 
          onClick={cargarMetricas}
          className="p-1 text-zinc-400 hover:text-zinc-600 transition-colors"
          title="Actualizar"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      {/* Barra de cumplimiento */}
      <CumplimientoBarra porcentaje={cumplimiento?.porcentaje || 0} />

      {/* Estadísticas de completadas */}
      <div className="flex justify-between text-xs text-zinc-500 mt-2 mb-4">
        <span>Completadas en tiempo: {cumplimiento?.cumplidas_en_tiempo || 0}</span>
        <span>Fuera de tiempo: {cumplimiento?.cumplidas_fuera_tiempo || 0}</span>
      </div>

      {/* Semáforo de estados activos */}
      <div className="border-t border-zinc-200 pt-4 mt-2">
        <p className="text-xs font-medium text-zinc-600 mb-3 text-center">
          Tareas Activas por Estado SLA
        </p>
        <div className="flex justify-around">
          <SemaforoIndicador 
            valor={porEstado.EN_TIEMPO || 0}
            label="En Tiempo"
            color="green"
            icon={TrendingUp}
          />
          <SemaforoIndicador 
            valor={porEstado.ADVERTENCIA || 0}
            label="Advertencia"
            color={porEstado.ADVERTENCIA > 0 ? 'yellow' : 'zinc'}
            icon={Clock}
          />
          <SemaforoIndicador 
            valor={porEstado.URGENTE || 0}
            label="Urgente"
            color={porEstado.URGENTE > 0 ? 'orange' : 'zinc'}
            icon={AlertTriangle}
          />
          <SemaforoIndicador 
            valor={porEstado.VENCIDA || 0}
            label="Vencidas"
            color={porEstado.VENCIDA > 0 ? 'red' : 'zinc'}
            icon={XCircle}
          />
        </div>
      </div>

      {/* Total activas */}
      <div className="text-center mt-3 pt-2 border-t border-zinc-200">
        <span className="text-xs text-zinc-500">
          Total tareas activas: <strong>{activas?.total || 0}</strong>
        </span>
      </div>
    </div>
  );
};

export default SLACard;
