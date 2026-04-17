/**
 * KPICards.jsx - Tarjetas de KPIs para Dashboard Operativo
 * CAB-003 | Fase 2A - Subfase 2A.8
 * EDARSA HUB
 */

import { 
  Activity, 
  Clock, 
  AlertTriangle, 
  CheckCircle2, 
  FileSearch,
  TrendingUp 
} from 'lucide-react';

const KPICard = ({ title, value, icon: Icon, color, subtitle }) => {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
    amber: 'bg-amber-50 text-amber-600 border-amber-200',
    red: 'bg-red-50 text-red-600 border-red-200',
    green: 'bg-green-50 text-green-600 border-green-200',
    purple: 'bg-purple-50 text-purple-600 border-purple-200',
    zinc: 'bg-zinc-50 text-zinc-600 border-zinc-200',
  };

  return (
    <div 
      className={`rounded-lg border p-4 ${colorClasses[color] || colorClasses.zinc}`}
      data-testid={`kpi-card-${title.toLowerCase().replace(/\s+/g, '-')}`}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium opacity-80">{title}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
          {subtitle && (
            <p className="text-xs opacity-60 mt-1">{subtitle}</p>
          )}
        </div>
        <div className="p-3 rounded-full bg-white/50">
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </div>
  );
};

const KPICards = ({ data, loading, error }) => {
  // Estado de carga
  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4" data-testid="kpi-cards-loading">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="rounded-lg border border-zinc-200 p-4 animate-pulse">
            <div className="h-4 bg-zinc-200 rounded w-20 mb-2"></div>
            <div className="h-8 bg-zinc-200 rounded w-12"></div>
          </div>
        ))}
      </div>
    );
  }

  // Estado de error
  if (error) {
    return (
      <div 
        className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700"
        data-testid="kpi-cards-error"
      >
        <p className="font-medium">Error cargando KPIs</p>
        <p className="text-sm">{error}</p>
      </div>
    );
  }

  // Estado vacío
  if (!data) {
    return (
      <div 
        className="rounded-lg border border-zinc-200 bg-zinc-50 p-4 text-zinc-500 text-center"
        data-testid="kpi-cards-empty"
      >
        No hay datos de KPIs disponibles
      </div>
    );
  }

  // Extraer valores de la estructura real del endpoint
  const totalWorkflows = data.workflows?.total ?? data.total_workflows ?? 0;
  const workflowsPendientes = data.workflows?.por_estado?.PENDIENTE_ASIGNACION ?? data.workflows?.por_estado?.pendiente ?? data.workflows_pendientes ?? 0;
  const workflowsEnAuditoria = data.workflows?.por_estado?.EN_AUDITORIA ?? data.workflows?.por_estado?.en_auditoria ?? data.workflows_en_auditoria ?? 0;
  const workflowsCompletados = data.workflows?.por_estado?.COMPLETADO ?? data.workflows?.por_estado?.completado ?? data.workflows_completados ?? 0;
  const tareasVencidas = data.tareas?.vencidas ?? data.alertas?.tareas_vencidas ?? data.tareas_vencidas ?? 0;
  const alertasActivas = (data.alertas?.tareas_vencidas ?? 0) + (data.alertas?.workflows_escalados ?? 0);

  const kpis = [
    {
      title: 'Workflows Totales',
      value: totalWorkflows,
      icon: Activity,
      color: 'blue',
    },
    {
      title: 'Pendientes',
      value: workflowsPendientes,
      icon: Clock,
      color: 'amber',
    },
    {
      title: 'En Auditoría',
      value: workflowsEnAuditoria,
      icon: FileSearch,
      color: 'purple',
    },
    {
      title: 'Tareas Vencidas',
      value: tareasVencidas,
      icon: AlertTriangle,
      color: tareasVencidas > 0 ? 'red' : 'green',
    },
    {
      title: 'Alertas Activas',
      value: alertasActivas,
      icon: AlertTriangle,
      color: alertasActivas > 0 ? 'red' : 'green',
    },
    {
      title: 'Completados',
      value: workflowsCompletados,
      icon: CheckCircle2,
      color: 'green',
    },
  ];

  return (
    <div 
      className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4"
      data-testid="kpi-cards"
    >
      {kpis.map((kpi) => (
        <KPICard key={kpi.title} {...kpi} />
      ))}
    </div>
  );
};

export default KPICards;
