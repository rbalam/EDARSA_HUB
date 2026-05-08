/**
 * SyncStatusIndicator - Componente para mostrar estado de sincronización
 * Muestra indicador visual del estado de conexión y sincronización
 */

import React from 'react';
import { Wifi, WifiOff, RefreshCw, Check, AlertTriangle } from 'lucide-react';
import { useSyncStatus } from '../hooks/useLocalFirst';

/**
 * Indicador global de estado de sincronización
 * Colocar en el header o footer de la app
 */
const SyncStatusIndicator = ({ className = '' }) => {
  const { isOnline, isSyncing, lastSync, pendingCount } = useSyncStatus();

  const formatLastSync = (isoDate) => {
    if (!isoDate) return '';
    const date = new Date(isoDate);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'ahora';
    if (diffMins < 60) return `hace ${diffMins}m`;
    return date.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
  };

  if (isSyncing) {
    return (
      <div className={`flex items-center gap-1.5 text-xs text-blue-600 ${className}`}>
        <RefreshCw className="h-3.5 w-3.5 animate-spin" />
        <span>Sincronizando...</span>
      </div>
    );
  }

  if (!isOnline) {
    return (
      <div className={`flex items-center gap-1.5 text-xs text-red-600 ${className}`}>
        <WifiOff className="h-3.5 w-3.5" />
        <span>Sin conexión</span>
        {pendingCount > 0 && (
          <span className="text-red-500">({pendingCount} pendientes)</span>
        )}
      </div>
    );
  }

  return (
    <div className={`flex items-center gap-1.5 text-xs text-green-600 ${className}`}>
      <Wifi className="h-3.5 w-3.5" />
      <span>Conectado</span>
      {lastSync && (
        <span className="text-zinc-400">• {formatLastSync(lastSync)}</span>
      )}
    </div>
  );
};

/**
 * Badge de estado para tarjetas individuales
 * Muestra si los datos son online, offline o stale
 */
const DataStatusBadge = ({ status, updatedAt, className = '' }) => {
  const formatTime = (isoDate) => {
    if (!isoDate) return '';
    try {
      const date = new Date(isoDate);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      
      if (diffMins < 1) return 'ahora';
      if (diffMins < 60) return `hace ${diffMins}m`;
      if (diffHours < 24) return `hace ${diffHours}h`;
      
      return date.toLocaleDateString('es-MX', { 
        day: '2-digit', 
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return '';
    }
  };

  const configs = {
    online: {
      icon: Check,
      color: 'text-green-600 bg-green-50',
      dotColor: 'bg-green-500',
      label: 'Actualizado'
    },
    cached: {
      icon: Check,
      color: 'text-green-600 bg-green-50',
      dotColor: 'bg-green-500',
      label: 'En caché'
    },
    offline: {
      icon: WifiOff,
      color: 'text-red-600 bg-red-50',
      dotColor: 'bg-red-500 animate-pulse',
      label: 'Offline'
    },
    stale: {
      icon: AlertTriangle,
      color: 'text-amber-600 bg-amber-50',
      dotColor: 'bg-amber-500',
      label: 'Desactualizado'
    },
    error: {
      icon: AlertTriangle,
      color: 'text-red-600 bg-red-50',
      dotColor: 'bg-red-500',
      label: 'Error'
    }
  };

  const config = configs[status] || configs.cached;
  const Icon = config.icon;
  const timeStr = formatTime(updatedAt);

  return (
    <div className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs ${config.color} ${className}`}>
      <span className={`h-2 w-2 rounded-full ${config.dotColor}`} />
      <span>{config.label}</span>
      {timeStr && <span className="opacity-75">• {timeStr}</span>}
    </div>
  );
};

/**
 * Indicador simple (solo el punto de color)
 */
const StatusDot = ({ status, className = '' }) => {
  const colors = {
    online: 'bg-green-500',
    cached: 'bg-green-500',
    offline: 'bg-red-500 animate-pulse',
    stale: 'bg-amber-500',
    error: 'bg-red-500',
    loading: 'bg-blue-500 animate-pulse'
  };

  const titles = {
    online: 'Datos actualizados',
    cached: 'Datos en caché',
    offline: 'Sin conexión',
    stale: 'Datos desactualizados',
    error: 'Error de conexión',
    loading: 'Cargando...'
  };

  return (
    <span 
      className={`inline-block h-2.5 w-2.5 rounded-full ${colors[status] || colors.cached} ${className}`}
      title={titles[status] || ''}
    />
  );
};

export { SyncStatusIndicator, DataStatusBadge, StatusDot };
export default SyncStatusIndicator;
