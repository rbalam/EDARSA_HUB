/**
 * AlertasBanner.jsx - Banner de Alertas para Dashboard Operativo
 * CAB-003 | Fase 2A - Subfase 2A.8
 * EDARSA HUB
 */

import { AlertTriangle, AlertCircle, Info, X } from 'lucide-react';
import { useState } from 'react';

const severityConfig = {
  alta: {
    icon: AlertTriangle,
    bgColor: 'bg-red-50',
    borderColor: 'border-red-300',
    textColor: 'text-red-800',
    iconColor: 'text-red-500',
  },
  media: {
    icon: AlertCircle,
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-300',
    textColor: 'text-amber-800',
    iconColor: 'text-amber-500',
  },
  baja: {
    icon: Info,
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-300',
    textColor: 'text-blue-800',
    iconColor: 'text-blue-500',
  },
};

const AlertaItem = ({ alerta, onDismiss }) => {
  const config = severityConfig[alerta.severidad] || severityConfig.baja;
  const Icon = config.icon;

  return (
    <div 
      className={`flex items-start gap-3 p-3 rounded-lg border ${config.bgColor} ${config.borderColor}`}
      data-testid={`alerta-item-${alerta.id || alerta._id}`}
    >
      <Icon className={`h-5 w-5 mt-0.5 flex-shrink-0 ${config.iconColor}`} />
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-medium ${config.textColor}`}>
          {alerta.mensaje || alerta.descripcion || 'Alerta sin mensaje'}
        </p>
        <div className="flex items-center gap-2 mt-1 text-xs opacity-70">
          {alerta.tipo && (
            <span className="uppercase font-semibold">{alerta.tipo}</span>
          )}
          {alerta.referencia_tipo && alerta.referencia_id && (
            <span>
              {alerta.referencia_tipo}: {String(alerta.referencia_id ?? '').substring(0, 8)}...
            </span>
          )}
          {alerta.fecha_creacion && (
            <span>
              {new Date(alerta.fecha_creacion).toLocaleString('es-MX', {
                day: '2-digit',
                month: 'short',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </span>
          )}
        </div>
      </div>
      {onDismiss && (
        <button
          onClick={() => onDismiss(alerta.id || alerta._id)}
          className={`p-1 rounded hover:bg-white/50 ${config.textColor}`}
          data-testid={`dismiss-alerta-${alerta.id || alerta._id}`}
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
};

const AlertasBanner = ({ alertas, loading, error, onRefresh }) => {
  const [dismissed, setDismissed] = useState(new Set());

  const handleDismiss = (id) => {
    setDismissed(prev => new Set([...prev, id]));
  };

  // Estado de carga
  if (loading) {
    return (
      <div 
        className="rounded-lg border border-zinc-200 bg-zinc-50 p-4"
        data-testid="alertas-banner-loading"
      >
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-zinc-200 rounded w-32"></div>
          <div className="h-12 bg-zinc-200 rounded"></div>
          <div className="h-12 bg-zinc-200 rounded"></div>
        </div>
      </div>
    );
  }

  // Estado de error
  if (error) {
    return (
      <div 
        className="rounded-lg border border-red-200 bg-red-50 p-4"
        data-testid="alertas-banner-error"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-red-700">
            <AlertTriangle className="h-5 w-5" />
            <span className="font-medium">Error cargando alertas</span>
          </div>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="text-sm text-red-600 hover:text-red-800 underline"
            >
              Reintentar
            </button>
          )}
        </div>
        <p className="text-sm text-red-600 mt-1">{error}</p>
      </div>
    );
  }

  // Filtrar alertas descartadas
  const visibleAlertas = (alertas || []).filter(
    a => !dismissed.has(a.id || a._id)
  );

  // Estado vacío
  if (!visibleAlertas || visibleAlertas.length === 0) {
    return (
      <div 
        className="rounded-lg border border-green-200 bg-green-50 p-4 flex items-center gap-3"
        data-testid="alertas-banner-empty"
      >
        <div className="p-2 rounded-full bg-green-100">
          <Info className="h-5 w-5 text-green-600" />
        </div>
        <div>
          <p className="font-medium text-green-800">Sin alertas activas</p>
          <p className="text-sm text-green-600">El sistema opera con normalidad</p>
        </div>
      </div>
    );
  }

  // Ordenar por severidad (alta primero)
  const sortedAlertas = [...visibleAlertas].sort((a, b) => {
    const order = { alta: 0, media: 1, baja: 2 };
    return (order[a.severidad] ?? 3) - (order[b.severidad] ?? 3);
  });

  return (
    <div 
      className="rounded-lg border border-zinc-200 bg-white p-4"
      data-testid="alertas-banner"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-zinc-900 flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-amber-500" />
          Alertas Activas ({visibleAlertas.length})
        </h3>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="text-sm text-zinc-500 hover:text-zinc-700"
            data-testid="refresh-alertas"
          >
            Actualizar
          </button>
        )}
      </div>
      <div className="space-y-2 max-h-60 overflow-y-auto">
        {sortedAlertas.map((alerta, idx) => (
          <AlertaItem 
            key={alerta.id || alerta._id || idx} 
            alerta={alerta} 
            onDismiss={handleDismiss}
          />
        ))}
      </div>
    </div>
  );
};

export default AlertasBanner;
