/**
 * ResponsabilidadCard.jsx - Tarjeta de Responsabilidad Económica
 * CAB-003 | Fase 2C.1
 * EDARSA HUB
 * 
 * Muestra métricas de impacto económico calculado.
 */

import { useState, useEffect } from 'react';
import { 
  DollarSign,
  AlertCircle,
  TrendingDown,
  TrendingUp,
  Building2,
  RefreshCw,
  ChevronRight,
  Calculator
} from 'lucide-react';

const API_BASE = process.env.REACT_APP_BACKEND_URL || '';

// Formateador de moneda
const formatMXN = (valor) => {
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
    minimumFractionDigits: 2
  }).format(valor || 0);
};

// Mini tarjeta de métrica
const MetricaMini = ({ label, valor, icon: Icon, color = 'zinc', formato = 'numero' }) => {
  const colorClasses = {
    red: 'text-red-600 bg-red-50',
    amber: 'text-amber-600 bg-amber-50',
    green: 'text-green-600 bg-green-50',
    blue: 'text-blue-600 bg-blue-50',
    purple: 'text-purple-600 bg-purple-50',
    zinc: 'text-zinc-600 bg-zinc-50',
  };

  const valorFormateado = formato === 'moneda' ? formatMXN(valor) : valor;

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg border border-zinc-100 bg-white">
      <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
        <Icon className="h-4 w-4" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-zinc-500 truncate">{label}</p>
        <p className={`text-sm font-semibold ${formato === 'moneda' ? 'text-zinc-900' : 'text-zinc-700'}`}>
          {valorFormateado}
        </p>
      </div>
    </div>
  );
};

// Fila de workflow en la lista
const WorkflowRow = ({ workflow }) => {
  const fechaCalculo = workflow.fecha_calculo 
    ? new Date(workflow.fecha_calculo).toLocaleDateString('es-MX', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
      })
    : '-';

  return (
    <div 
      className="flex items-center justify-between py-2 px-3 hover:bg-zinc-50 rounded-lg transition-colors"
      data-testid={`workflow-row-${workflow.workflow_id}`}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-zinc-700 truncate max-w-[120px]">
            {workflow.sucursal_id}
          </span>
          {workflow.excede_minimo && (
            <span className="px-1.5 py-0.5 text-xs bg-red-100 text-red-700 rounded-full">
              Excede
            </span>
          )}
        </div>
        <p className="text-xs text-zinc-400">{fechaCalculo}</p>
      </div>
      <div className="text-right">
        <p className={`text-sm font-semibold ${
          workflow.monto_propuesto_mxn > 0 ? 'text-red-600' : 'text-zinc-500'
        }`}>
          {formatMXN(workflow.monto_propuesto_mxn)}
        </p>
        <p className="text-xs text-zinc-400">{workflow.estado}</p>
      </div>
    </div>
  );
};

// Fila de sucursal en top
const SucursalRow = ({ sucursal, index }) => {
  return (
    <div className="flex items-center justify-between py-1.5">
      <div className="flex items-center gap-2">
        <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
          index === 0 ? 'bg-red-100 text-red-700' :
          index === 1 ? 'bg-amber-100 text-amber-700' :
          'bg-zinc-100 text-zinc-600'
        }`}>
          {index + 1}
        </span>
        <span className="text-sm text-zinc-700 truncate max-w-[100px]">
          {sucursal.sucursal_id}
        </span>
      </div>
      <span className={`text-sm font-medium ${
        sucursal.monto_total_mxn > 0 ? 'text-red-600' : 'text-zinc-500'
      }`}>
        {formatMXN(sucursal.monto_total_mxn)}
      </span>
    </div>
  );
};

const ResponsabilidadCard = () => {
  const [metricas, setMetricas] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [mostrarLista, setMostrarLista] = useState(false);

  const cargarMetricas = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/v2/responsabilidad/metricas`);
      if (!response.ok) throw new Error('Error al cargar métricas de responsabilidad');
      const data = await response.json();
      setMetricas(data);
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
      <div className="rounded-xl border border-zinc-200 bg-white p-5 animate-pulse" data-testid="responsabilidad-card-loading">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-8 h-8 bg-zinc-200 rounded-lg"></div>
          <div className="h-5 bg-zinc-200 rounded w-48"></div>
        </div>
        <div className="grid grid-cols-2 gap-3 mb-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-16 bg-zinc-100 rounded-lg"></div>
          ))}
        </div>
        <div className="h-24 bg-zinc-100 rounded-lg"></div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-5" data-testid="responsabilidad-card-error">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-red-700">
            <AlertCircle className="h-5 w-5" />
            <span className="text-sm font-medium">Error cargando métricas</span>
          </div>
          <button 
            onClick={cargarMetricas}
            className="p-2 text-red-600 hover:bg-red-100 rounded-lg transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
        <p className="text-xs text-red-600 mt-2">{error}</p>
      </div>
    );
  }

  if (!metricas) return null;

  const { resumen, top_sucursales, ultimos_calculos } = metricas;
  const hayMontosPendientes = resumen.monto_total_propuesto_mxn > 0;

  return (
    <div 
      className={`rounded-xl border ${
        hayMontosPendientes ? 'border-red-200 bg-gradient-to-br from-red-50 to-white' : 'border-zinc-200 bg-white'
      } p-5 transition-all`}
      data-testid="responsabilidad-card"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className={`p-2 rounded-lg ${hayMontosPendientes ? 'bg-red-100' : 'bg-zinc-100'}`}>
            <Calculator className={`h-5 w-5 ${hayMontosPendientes ? 'text-red-600' : 'text-zinc-600'}`} />
          </div>
          <div>
            <h3 className="font-semibold text-zinc-800">Responsabilidad Económica</h3>
            <p className="text-xs text-zinc-500">Fase 2C.1 - Cálculo Base</p>
          </div>
        </div>
        <button 
          onClick={cargarMetricas}
          className="p-2 text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100 rounded-lg transition-colors"
          title="Actualizar"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      {/* Monto Total Principal */}
      <div className={`rounded-xl p-4 mb-4 ${
        hayMontosPendientes ? 'bg-red-100' : 'bg-zinc-100'
      }`}>
        <p className="text-xs font-medium text-zinc-600 mb-1">Monto Total Propuesto</p>
        <p className={`text-3xl font-bold ${
          hayMontosPendientes ? 'text-red-700' : 'text-zinc-700'
        }`}>
          {formatMXN(resumen.monto_total_propuesto_mxn)}
        </p>
        <div className="flex items-center gap-4 mt-2 text-xs">
          <span className="text-zinc-600">
            <strong>{resumen.workflows_en_revision_financiera}</strong> en revisión
          </span>
          <span className={resumen.calculos_exceden_minimo > 0 ? 'text-red-600 font-medium' : 'text-zinc-500'}>
            <strong>{resumen.calculos_exceden_minimo}</strong> exceden mínimo
          </span>
        </div>
      </div>

      {/* Métricas secundarias */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <MetricaMini 
          label="Total Faltantes" 
          valor={resumen.total_faltantes_mxn} 
          icon={TrendingDown} 
          color="red"
          formato="moneda"
        />
        <MetricaMini 
          label="Total Sobrantes" 
          valor={resumen.total_sobrantes_mxn} 
          icon={TrendingUp} 
          color="green"
          formato="moneda"
        />
        <MetricaMini 
          label="Cálculos Totales" 
          valor={resumen.total_calculos} 
          icon={Calculator} 
          color="blue"
        />
        <MetricaMini 
          label="Exceden Mínimo" 
          valor={resumen.calculos_exceden_minimo} 
          icon={AlertCircle} 
          color={resumen.calculos_exceden_minimo > 0 ? 'amber' : 'zinc'}
        />
      </div>

      {/* Top Sucursales */}
      {top_sucursales && top_sucursales.length > 0 && (
        <div className="border-t border-zinc-200 pt-4 mb-4">
          <div className="flex items-center gap-2 mb-3">
            <Building2 className="h-4 w-4 text-zinc-500" />
            <h4 className="text-sm font-medium text-zinc-700">Top Sucursales por Monto</h4>
          </div>
          <div className="space-y-1">
            {top_sucursales.slice(0, 3).map((sucursal, index) => (
              <SucursalRow key={sucursal.sucursal_id} sucursal={sucursal} index={index} />
            ))}
          </div>
        </div>
      )}

      {/* Toggle para lista de workflows */}
      <div className="border-t border-zinc-200 pt-3">
        <button
          onClick={() => setMostrarLista(!mostrarLista)}
          className="w-full flex items-center justify-between py-2 px-1 text-sm text-zinc-600 hover:text-zinc-900 transition-colors"
          data-testid="toggle-lista-workflows"
        >
          <span className="flex items-center gap-2">
            <DollarSign className="h-4 w-4" />
            Últimos cálculos ({ultimos_calculos?.length || 0})
          </span>
          <ChevronRight className={`h-4 w-4 transition-transform ${mostrarLista ? 'rotate-90' : ''}`} />
        </button>

        {/* Lista expandible de workflows */}
        {mostrarLista && ultimos_calculos && ultimos_calculos.length > 0 && (
          <div className="mt-2 space-y-1 max-h-48 overflow-y-auto" data-testid="lista-workflows-responsabilidad">
            {ultimos_calculos.map((workflow) => (
              <WorkflowRow key={workflow.workflow_id} workflow={workflow} />
            ))}
          </div>
        )}

        {mostrarLista && (!ultimos_calculos || ultimos_calculos.length === 0) && (
          <p className="text-xs text-zinc-400 text-center py-4">
            No hay cálculos de responsabilidad registrados
          </p>
        )}
      </div>
    </div>
  );
};

export default ResponsabilidadCard;
