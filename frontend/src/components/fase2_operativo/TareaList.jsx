/**
 * TareaList.jsx - Lista de Tareas para Dashboard Operativo
 * CAB-003 | Fase 2A - Subfase 2A.8
 * EDARSA HUB
 */

import { 
  ClipboardList, 
  Clock, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle,
  User,
  RefreshCw,
  ChevronRight
} from 'lucide-react';

const estadoConfig = {
  pendiente: {
    label: 'Pendiente',
    icon: Clock,
    bgColor: 'bg-amber-100',
    textColor: 'text-amber-800',
  },
  en_proceso: {
    label: 'En Proceso',
    icon: ClipboardList,
    bgColor: 'bg-blue-100',
    textColor: 'text-blue-800',
  },
  completada: {
    label: 'Completada',
    icon: CheckCircle2,
    bgColor: 'bg-green-100',
    textColor: 'text-green-800',
  },
  cancelada: {
    label: 'Cancelada',
    icon: XCircle,
    bgColor: 'bg-red-100',
    textColor: 'text-red-800',
  },
  vencida: {
    label: 'Vencida',
    icon: AlertTriangle,
    bgColor: 'bg-red-100',
    textColor: 'text-red-800',
  },
};

const tipoConfig = {
  justificacion: { label: 'Justificación', color: 'text-purple-600' },
  revision: { label: 'Revisión', color: 'text-blue-600' },
  aprobacion: { label: 'Aprobación', color: 'text-green-600' },
  auditoria: { label: 'Auditoría', color: 'text-orange-600' },
};

const EstadoBadge = ({ estado, vencida }) => {
  // Si está vencida, mostrar estado especial
  const efectivo = vencida && estado !== 'completada' && estado !== 'cancelada' 
    ? 'vencida' 
    : estado;
  
  const config = estadoConfig[efectivo] || {
    label: efectivo,
    icon: ClipboardList,
    bgColor: 'bg-zinc-100',
    textColor: 'text-zinc-800',
  };
  const Icon = config.icon;

  return (
    <span 
      className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.bgColor} ${config.textColor}`}
      data-testid={`tarea-estado-${efectivo}`}
    >
      <Icon className="h-3 w-3" />
      {config.label}
    </span>
  );
};

const TareaRow = ({ tarea, onClick }) => {
  const fechaLimite = tarea.fecha_limite 
    ? new Date(tarea.fecha_limite)
    : null;
  
  const fechaFormateada = fechaLimite 
    ? fechaLimite.toLocaleDateString('es-MX', {
        day: '2-digit',
        month: 'short',
      })
    : '-';

  const isVencida = tarea.vencida || (fechaLimite && fechaLimite < new Date() && tarea.estado === 'pendiente');
  const tipoInfo = tipoConfig[tarea.tipo] || { label: tarea.tipo, color: 'text-zinc-600' };

  return (
    <tr 
      className={`hover:bg-zinc-50 cursor-pointer transition-colors ${isVencida ? 'bg-red-50/50' : ''}`}
      onClick={() => onClick?.(tarea)}
      data-testid={`tarea-row-${tarea.id || tarea._id}`}
    >
      <td className="px-4 py-3 text-sm font-mono text-zinc-600">
        {(tarea.id || tarea._id || '').substring(0, 8)}...
      </td>
      <td className="px-4 py-3">
        <span className={`text-sm font-medium ${tipoInfo.color}`}>
          {tipoInfo.label}
        </span>
      </td>
      <td className="px-4 py-3">
        <EstadoBadge estado={tarea.estado} vencida={isVencida} />
      </td>
      <td className="px-4 py-3 text-sm text-zinc-600">
        {tarea.usuario_asignado_nombre || tarea.usuario_asignado_id ? (
          <span className="flex items-center gap-1">
            <User className="h-3 w-3" />
            {tarea.usuario_asignado_nombre || tarea.usuario_asignado_id?.substring(0, 8)}
          </span>
        ) : (
          <span className="text-zinc-400">Sin asignar</span>
        )}
      </td>
      <td className={`px-4 py-3 text-sm ${isVencida ? 'text-red-600 font-medium' : 'text-zinc-500'}`}>
        {fechaFormateada}
        {isVencida && <AlertTriangle className="h-3 w-3 inline ml-1" />}
      </td>
      <td className="px-4 py-3 text-right">
        <ChevronRight className="h-4 w-4 text-zinc-400 inline-block" />
      </td>
    </tr>
  );
};

const TareaList = ({ 
  tareas, 
  loading, 
  error, 
  onRefresh, 
  onTareaClick,
  emptyMessage = 'No hay tareas disponibles'
}) => {
  // Estado de carga
  if (loading) {
    return (
      <div 
        className="rounded-lg border border-zinc-200 bg-white overflow-hidden"
        data-testid="tarea-list-loading"
      >
        <div className="p-4 border-b border-zinc-200 bg-zinc-50">
          <div className="h-5 bg-zinc-200 rounded w-32 animate-pulse"></div>
        </div>
        <div className="p-4 space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-12 bg-zinc-100 rounded animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  // Estado de error
  if (error) {
    return (
      <div 
        className="rounded-lg border border-red-200 bg-red-50 p-6 text-center"
        data-testid="tarea-list-error"
      >
        <XCircle className="h-8 w-8 text-red-400 mx-auto mb-2" />
        <p className="font-medium text-red-800">Error cargando tareas</p>
        <p className="text-sm text-red-600 mt-1">{error}</p>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="mt-3 inline-flex items-center gap-2 px-4 py-2 bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors"
            data-testid="tarea-list-retry"
          >
            <RefreshCw className="h-4 w-4" />
            Reintentar
          </button>
        )}
      </div>
    );
  }

  // Estado vacío
  if (!tareas || tareas.length === 0) {
    return (
      <div 
        className="rounded-lg border border-zinc-200 bg-zinc-50 p-6 text-center"
        data-testid="tarea-list-empty"
      >
        <ClipboardList className="h-8 w-8 text-zinc-300 mx-auto mb-2" />
        <p className="text-zinc-500">{emptyMessage}</p>
      </div>
    );
  }

  // Ordenar: vencidas primero, luego pendientes
  const sortedTareas = [...tareas].sort((a, b) => {
    const aVencida = a.vencida || (a.fecha_limite && new Date(a.fecha_limite) < new Date() && a.estado === 'pendiente');
    const bVencida = b.vencida || (b.fecha_limite && new Date(b.fecha_limite) < new Date() && b.estado === 'pendiente');
    
    if (aVencida && !bVencida) return -1;
    if (!aVencida && bVencida) return 1;
    
    const order = { pendiente: 0, en_proceso: 1, completada: 2, cancelada: 3 };
    return (order[a.estado] ?? 4) - (order[b.estado] ?? 4);
  });

  const vencidasCount = tareas.filter(t => 
    t.vencida || (t.fecha_limite && new Date(t.fecha_limite) < new Date() && t.estado === 'pendiente')
  ).length;

  return (
    <div 
      className="rounded-lg border border-zinc-200 bg-white overflow-hidden"
      data-testid="tarea-list"
    >
      <div className="flex items-center justify-between p-4 border-b border-zinc-200 bg-zinc-50">
        <h3 className="font-semibold text-zinc-900 flex items-center gap-2">
          <ClipboardList className="h-5 w-5 text-purple-500" />
          Tareas ({tareas.length})
          {vencidasCount > 0 && (
            <span className="ml-2 px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded-full">
              {vencidasCount} vencida{vencidasCount > 1 ? 's' : ''}
            </span>
          )}
        </h3>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="p-2 text-zinc-500 hover:text-zinc-700 hover:bg-zinc-100 rounded-md transition-colors"
            data-testid="tarea-list-refresh"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        )}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-zinc-50 border-b border-zinc-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-600 uppercase tracking-wider">
                ID
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-600 uppercase tracking-wider">
                Tipo
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-600 uppercase tracking-wider">
                Estado
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-600 uppercase tracking-wider">
                Asignado
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-600 uppercase tracking-wider">
                Límite
              </th>
              <th className="px-4 py-3 w-10"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100">
            {sortedTareas.map((tarea, idx) => (
              <TareaRow 
                key={tarea.id || tarea._id || idx} 
                tarea={tarea}
                onClick={onTareaClick}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TareaList;
