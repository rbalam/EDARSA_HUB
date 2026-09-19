import React, { useState, useEffect, useCallback } from 'react';
import { 
  RefreshCw, 
  Server, 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Database,
  Zap,
  XCircle
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

// Colores por estado
const STATUS_CONFIG = {
  SUCCESS: { 
    bg: 'bg-emerald-500/20', 
    border: 'border-emerald-500/50', 
    text: 'text-emerald-400',
    dot: 'bg-emerald-500',
    label: 'OK'
  },
  WARNING: { 
    bg: 'bg-amber-500/20', 
    border: 'border-amber-500/50', 
    text: 'text-amber-400',
    dot: 'bg-amber-500',
    label: 'ADVERTENCIA'
  },
  ERROR: { 
    bg: 'bg-red-500/20', 
    border: 'border-red-500/50', 
    text: 'text-red-400',
    dot: 'bg-red-500',
    label: 'ERROR'
  },
  STALE: { bg: 'bg-zinc-500/10', border: 'border-zinc-500/30', text: 'text-zinc-400', dot: 'bg-zinc-500', label: 'STALE' },
  SIN_SLA_THRESHOLD_CONFIGURADO: { bg: 'bg-amber-500/10', border: 'border-amber-500/30', text: 'text-amber-300', dot: 'bg-amber-400', label: 'SIN SLA' },
  SIN_TELEMETRIA: { bg: 'bg-zinc-800', border: 'border-zinc-700', text: 'text-zinc-400', dot: 'bg-zinc-500', label: 'SIN TELEMETRIA' },
};

const getStatusConfig = (status) => STATUS_CONFIG[status] || STATUS_CONFIG.SIN_TELEMETRIA;

// Formatear duración
const formatDuration = (seconds) => {
  if (!seconds || seconds === 0) return '-';
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
  return `${Math.round(seconds / 3600)}h`;
};

// Formatear timestamp
const formatTimestamp = (isoString) => {
  if (!isoString) return '-';
  try {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Ahora';
    if (diffMins < 60) return `Hace ${diffMins}m`;
    if (diffMins < 1440) return `Hace ${Math.floor(diffMins / 60)}h`;
    return date.toLocaleDateString('es-MX', { 
      day: '2-digit', 
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return '-';
  }
};

// Componente KPI Card
const KpiCard = ({ icon: Icon, label, value, subvalue, color = 'blue' }) => {
  const colors = {
    blue: 'border-zinc-800',
    green: 'border-emerald-900/60',
    amber: 'border-amber-900/60',
    red: 'border-red-900/60',
    gray: 'border-zinc-800',
  };
  
  return (
    <div className={`bg-zinc-950/70 ${colors[color]} border rounded-lg p-4 shadow-sm`}>
      <div className="flex items-center gap-3">
        <div className="p-2 bg-white/5 rounded-lg">
          <Icon className="w-5 h-5 text-white/70" />
        </div>
        <div>
          <p className="text-xs text-white/50 uppercase tracking-wide">{label}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
          {subvalue && <p className="text-xs text-white/40">{subvalue}</p>}
        </div>
      </div>
    </div>
  );
};

// Componente Status Badge
const StatusBadge = ({ status }) => {
  const config = getStatusConfig(status);
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text} border ${config.border}`}>
      <span className={`w-2 h-2 rounded-full ${config.dot} animate-pulse`}></span>
      {config.label}
    </span>
  );
};

// Tabla de Procesos
const ProcesosTable = ({ procesos }) => {
  if (!procesos || procesos.length === 0) {
    return (
      <div className="text-center py-8 text-white/40">
        <Activity className="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p>Sin procesos registrados</p>
      </div>
    );
  }
  
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/10">
            <th className="text-left py-3 px-4 text-white/50 font-medium">Servidor</th>
            <th className="text-left py-3 px-4 text-white/50 font-medium">Proceso</th>
            <th className="text-left py-3 px-4 text-white/50 font-medium">Última Ejecución</th>
            <th className="text-center py-3 px-4 text-white/50 font-medium">Duración</th>
            <th className="text-center py-3 px-4 text-white/50 font-medium">Registros</th>
            <th className="text-center py-3 px-4 text-white/50 font-medium">Errores</th>
            <th className="text-center py-3 px-4 text-white/50 font-medium">Estado</th>
          </tr>
        </thead>
        <tbody>
          {procesos.map((p, idx) => (
            <tr 
              key={`${p.server_id}-${p.sync_type}-${idx}`}
              className="border-b border-white/5 hover:bg-white/5 transition-colors"
            >
              <td className="py-3 px-4">
                <div className="flex items-center gap-2">
                  <Server className="w-4 h-4 text-white/40" />
                  <span className="text-white/80 font-medium truncate max-w-[150px]">
                    {p.server_name}
                  </span>
                </div>
              </td>
              <td className="py-3 px-4">
                <span className="text-white/70 bg-white/5 px-2 py-0.5 rounded text-xs">
                  {p.sync_type}
                </span>
              </td>
              <td className="py-3 px-4 text-white/60">
                {formatTimestamp(p.last_sync)}
              </td>
              <td className="py-3 px-4 text-center text-white/60">
                {formatDuration(p.avg_duration_sec)}
              </td>
              <td className="py-3 px-4 text-center text-white/80 font-mono">
                {(p.total_records_24h || 0).toLocaleString()}
              </td>
              <td className="py-3 px-4 text-center">
                <span className={p.error_count_24h > 0 ? 'text-red-400 font-medium' : 'text-white/40'}>
                  {p.error_count_24h || 0}
                </span>
              </td>
              <td className="py-3 px-4 text-center">
                <StatusBadge status={p.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// Tabla de Errores
const ErroresTable = ({ errores }) => {
  if (!errores || errores.length === 0) {
    return (
      <div className="text-center py-6 text-emerald-400/70">
        <CheckCircle className="w-10 h-10 mx-auto mb-2" />
        <p>Sin errores en las últimas 24 horas</p>
      </div>
    );
  }
  
  return (
    <div className="space-y-2 max-h-[300px] overflow-y-auto">
      {errores.map((e, idx) => (
        <div 
          key={idx}
          className="bg-red-500/10 border border-red-500/20 rounded-lg p-3"
        >
          <div className="flex items-start gap-3">
            <XCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-white/80 font-medium text-sm">{e.server_name}</span>
                <span className="text-white/50 text-xs">•</span>
                <span className="text-white/60 text-xs">{e.sync_type}</span>
              </div>
              <p className="text-red-300/80 text-xs truncate">
                {e.error_message || 'Error sin mensaje'}
              </p>
              <p className="text-white/40 text-xs mt-1">
                {formatTimestamp(e.timestamp)}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

// Timeline de últimos syncs
const SyncTimeline = ({ ultimos }) => {
  if (!ultimos || ultimos.length === 0) {
    return (
      <div className="text-center py-6 text-white/40">
        <Clock className="w-10 h-10 mx-auto mb-2 opacity-50" />
        <p>Sin actividad reciente</p>
      </div>
    );
  }
  
  return (
    <div className="space-y-2 max-h-[400px] overflow-y-auto">
      {ultimos.slice(0, 15).map((s, idx) => {
        const config = getStatusConfig(s.status);
        return (
          <div 
            key={idx}
            className={`flex items-center gap-3 p-2 rounded-lg ${config.bg} border ${config.border}`}
          >
            <div className={`w-2 h-2 rounded-full ${config.dot}`}></div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-white/80 text-sm font-medium truncate max-w-[120px]">
                  {s.server_name}
                </span>
                <span className="text-white/40 text-xs">{s.sync_type}</span>
              </div>
            </div>
            <div className="text-right">
              <p className="text-white/60 text-xs">{formatTimestamp(s.timestamp)}</p>
              <p className="text-white/40 text-xs">
                {s.records || 0} reg • {formatDuration(s.duration_sec)}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
};

// Componente principal
const SyncMonitor = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/admin/sync-monitor`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      setData(result);
      setLastUpdate(new Date());
      setError(null);
    } catch (err) {
      console.error('[SyncMonitor] Error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    
    // Auto-refresh cada 30 segundos
    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchData, 30000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [fetchData, autoRefresh]);

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-blue-400 animate-spin mx-auto mb-4" />
          <p className="text-white/60">Cargando monitor...</p>
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <p className="text-red-400 mb-2">Error cargando datos</p>
          <p className="text-white/40 text-sm mb-4">{error}</p>
          <button 
            onClick={fetchData}
            className="px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/50 rounded-lg text-blue-400 transition-colors"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  const kpis = data?.kpis || {};

  return (
    <div className="space-y-6 p-6 text-zinc-100" data-testid="sync-monitor-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Activity className="w-7 h-7 text-blue-400" />
            Monitor de Sincronización
          </h1>
          <p className="text-white/50 text-sm mt-1">
            Vista NOC • Fuente: EDARSAHUB SQL
          </p>
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-white/60 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-white/20 bg-white/5"
            />
            Auto-refresh
          </label>
          <button 
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 rounded-md text-zinc-200 transition-colors disabled:opacity-50"
            data-testid="refresh-sync-monitor"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Actualizar
          </button>
        </div>
      </div>

      {lastUpdate && (
        <p className="text-white/30 text-xs">
          Última actualización: {lastUpdate.toLocaleTimeString('es-MX')}
        </p>
      )}

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <KpiCard 
          icon={Server} 
          label="Servidores" 
          value={kpis.total_servidores || 0}
          color="blue"
        />
        <KpiCard 
          icon={CheckCircle} 
          label="OK" 
          value={kpis.servidores_ok || 0}
          color="green"
        />
        <KpiCard 
          icon={AlertTriangle} 
          label="Warning" 
          value={kpis.servidores_warning || 0}
          color="amber"
        />
        <KpiCard 
          icon={XCircle} 
          label="Error" 
          value={kpis.servidores_error || 0}
          color="red"
        />
        <KpiCard 
          icon={Clock} 
          label="Inactivos" 
          value={kpis.servidores_stale || 0}
          color="gray"
        />
        <KpiCard 
          icon={Database} 
          label="Registros 24h" 
          value={(kpis.total_records_24h || 0).toLocaleString()}
          subvalue={`${kpis.total_runs_24h || 0} ejecuciones`}
          color="blue"
        />
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Procesos - 2/3 */}
        <div className="lg:col-span-2 bg-white/5 border border-white/10 rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-white/10 flex items-center gap-2">
            <Zap className="w-5 h-5 text-blue-400" />
            <h2 className="text-lg font-semibold text-white">Procesos por Servidor</h2>
            <span className="text-white/40 text-sm ml-auto">
              {data?.procesos?.length || 0} activos
            </span>
          </div>
          <ProcesosTable procesos={data?.procesos} />
        </div>

        {/* Sidebar - 1/3 */}
        <div className="space-y-6">
          {/* Errores */}
          <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
            <div className="px-4 py-3 border-b border-white/10 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-400" />
              <h2 className="text-lg font-semibold text-white">Errores 24h</h2>
              <span className="text-red-400 text-sm ml-auto font-medium">
                {kpis.total_errores_24h || 0}
              </span>
            </div>
            <div className="p-4">
              <ErroresTable errores={data?.errores} />
            </div>
          </div>

          {/* Timeline */}
          <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
            <div className="px-4 py-3 border-b border-white/10 flex items-center gap-2">
              <Clock className="w-5 h-5 text-blue-400" />
              <h2 className="text-lg font-semibold text-white">Actividad Reciente</h2>
            </div>
            <div className="p-4">
              <SyncTimeline ultimos={data?.ultimos_syncs} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SyncMonitor;
