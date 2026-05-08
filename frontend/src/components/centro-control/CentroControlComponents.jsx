/**
 * Componentes UI del Centro de Control
 */

import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { 
  CheckCircle, XCircle, AlertTriangle, Clock, Info, 
  ChevronRight, ExternalLink, Eye, Activity, Server,
  Database, Wifi, WifiOff
} from 'lucide-react';

// ============================================================================
// SEMAFORO GLOBAL
// ============================================================================

export const SemaforoGlobal = ({ status, label, timestamp }) => {
  const statusConfig = {
    ok: { color: 'bg-green-500', glow: 'shadow-green-500/50', icon: CheckCircle, text: 'OPERATIVO' },
    warning: { color: 'bg-yellow-500', glow: 'shadow-yellow-500/50', icon: AlertTriangle, text: 'ATENCIÓN' },
    critical: { color: 'bg-red-500', glow: 'shadow-red-500/50', icon: XCircle, text: 'CRÍTICO' },
    unknown: { color: 'bg-zinc-500', glow: 'shadow-zinc-500/50', icon: Info, text: 'DESCONOCIDO' }
  };

  const config = statusConfig[status] || statusConfig.unknown;
  const Icon = config.icon;

  return (
    <div className="flex items-center gap-4 p-4 bg-zinc-900 rounded-lg">
      <div className={`w-16 h-16 ${config.color} rounded-full flex items-center justify-center shadow-lg ${config.glow}`}>
        <Icon className="w-8 h-8 text-white" />
      </div>
      <div>
        <div className="flex items-center gap-2">
          <span className="text-2xl font-bold text-white">{config.text}</span>
          {label && <Badge variant="outline" className="text-white border-white/30">{label}</Badge>}
        </div>
        {timestamp && (
          <p className="text-sm text-zinc-400 flex items-center gap-1 mt-1">
            <Clock className="w-3 h-3" />
            Última actualización: {new Date(timestamp).toLocaleString('es-MX')}
          </p>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// KPI CARD
// ============================================================================

export const KPICard = ({ title, value, subtitle, icon: Icon, status = 'neutral', onClick }) => {
  const statusColors = {
    ok: 'border-green-200 bg-green-50',
    warning: 'border-yellow-200 bg-yellow-50',
    critical: 'border-red-200 bg-red-50',
    neutral: 'border-zinc-200 bg-white'
  };

  return (
    <Card 
      className={`${statusColors[status]} cursor-pointer hover:shadow-md transition-shadow`}
      onClick={onClick}
    >
      <CardContent className="pt-4">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-zinc-500">{title}</p>
            <p className="text-3xl font-bold text-zinc-900">{value}</p>
            {subtitle && <p className="text-xs text-zinc-400 mt-1">{subtitle}</p>}
          </div>
          {Icon && <Icon className="w-6 h-6 text-zinc-400" />}
        </div>
      </CardContent>
    </Card>
  );
};

// ============================================================================
// SEVERITY BADGE
// ============================================================================

export const SeverityBadge = ({ severity }) => {
  const severityConfig = {
    critical: { className: 'bg-red-100 text-red-700 border-red-300', label: 'CRÍTICO' },
    high: { className: 'bg-orange-100 text-orange-700 border-orange-300', label: 'ALTO' },
    medium: { className: 'bg-yellow-100 text-yellow-700 border-yellow-300', label: 'MEDIO' },
    low: { className: 'bg-blue-100 text-blue-700 border-blue-300', label: 'BAJO' },
    info: { className: 'bg-zinc-100 text-zinc-700 border-zinc-300', label: 'INFO' }
  };

  const config = severityConfig[severity] || severityConfig.info;
  return <Badge className={config.className}>{config.label}</Badge>;
};

// ============================================================================
// STATUS DOT
// ============================================================================

export const StatusDot = ({ status, size = 'sm' }) => {
  const statusColors = {
    ok: 'bg-green-500',
    online: 'bg-green-500',
    warning: 'bg-yellow-500',
    critical: 'bg-red-500',
    error: 'bg-red-500',
    offline: 'bg-zinc-400',
    unknown: 'bg-zinc-400'
  };

  const sizes = { sm: 'w-2 h-2', md: 'w-3 h-3', lg: 'w-4 h-4' };
  const pulse = ['critical', 'error', 'offline'].includes(status) ? 'animate-pulse' : '';

  return <div className={`${sizes[size]} ${statusColors[status] || 'bg-zinc-400'} rounded-full ${pulse}`} />;
};

// ============================================================================
// CATEGORIA SEMAFORO
// ============================================================================

export const CategoriaSemaforo = ({ nombre, status }) => {
  const statusConfig = {
    ok: { color: 'text-green-600', bg: 'bg-green-100', icon: CheckCircle },
    warning: { color: 'text-yellow-600', bg: 'bg-yellow-100', icon: AlertTriangle },
    critical: { color: 'text-red-600', bg: 'bg-red-100', icon: XCircle }
  };

  const config = statusConfig[status] || statusConfig.ok;
  const Icon = config.icon;

  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${config.bg}`}>
      <Icon className={`w-4 h-4 ${config.color}`} />
      <span className={`text-sm font-medium ${config.color}`}>{nombre}</span>
    </div>
  );
};

// ============================================================================
// MODULO CARD
// ============================================================================

export const ModuloCard = ({ modulo, onClick }) => {
  const statusColors = {
    ok: 'border-l-green-500',
    warning: 'border-l-yellow-500',
    critical: 'border-l-red-500'
  };

  return (
    <Card 
      className={`border-l-4 ${statusColors[modulo.status]} cursor-pointer hover:shadow-md transition-shadow`}
      onClick={() => onClick?.(modulo)}
    >
      <CardContent className="pt-4">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <StatusDot status={modulo.status} />
              <h3 className="font-medium">{modulo.nombre}</h3>
            </div>
            <p className="text-sm text-zinc-500 mt-1">{modulo.descripcion}</p>
          </div>
          <ChevronRight className="w-5 h-5 text-zinc-400" />
        </div>
        <div className="flex gap-4 mt-3 text-sm">
          <span className="text-zinc-500">
            <span className="font-medium text-zinc-700">{modulo.alertas_activas || 0}</span> alertas
          </span>
          <span className="text-zinc-500">
            <span className="font-medium text-zinc-700">{modulo.errores_24h || 0}</span> errores/24h
          </span>
        </div>
      </CardContent>
    </Card>
  );
};

// ============================================================================
// FUENTE CARD
// ============================================================================

export const FuenteCard = ({ fuente }) => (
  <Card className={fuente.status === 'online' ? 'border-green-200' : 'border-red-200'}>
    <CardContent className="pt-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {fuente.tipo === 'database' ? <Database className="w-5 h-5 text-zinc-400" /> :
           fuente.tipo === 'api' ? <Server className="w-5 h-5 text-zinc-400" /> :
           <Activity className="w-5 h-5 text-zinc-400" />}
          <div>
            <p className="font-medium">{fuente.nombre}</p>
            <p className="text-xs text-zinc-500">{fuente.tipo}</p>
          </div>
        </div>
        {fuente.status === 'online' ? 
          <Wifi className="w-5 h-5 text-green-500" /> : 
          <WifiOff className="w-5 h-5 text-red-500" />
        }
      </div>
      {fuente.latencia && (
        <p className="text-xs text-zinc-400 mt-2">Latencia: {fuente.latencia}ms</p>
      )}
    </CardContent>
  </Card>
);

// ============================================================================
// ALERTA ROW
// ============================================================================

export const AlertaRow = ({ alerta, onAcknowledge, onView }) => (
  <div className="flex items-center justify-between py-3 border-b last:border-0">
    <div className="flex items-start gap-3">
      <StatusDot status={alerta.severity === 'critical' ? 'critical' : alerta.severity === 'high' ? 'warning' : 'ok'} size="md" />
      <div>
        <p className="font-medium text-zinc-900">{alerta.titulo}</p>
        <p className="text-sm text-zinc-500">{alerta.modulo}</p>
        <p className="text-xs text-zinc-400 mt-1">
          {new Date(alerta.fecha_creacion).toLocaleString('es-MX')}
        </p>
      </div>
    </div>
    <div className="flex items-center gap-2">
      <SeverityBadge severity={alerta.severity} />
      <Button variant="ghost" size="sm" onClick={() => onView?.(alerta)}>
        <Eye className="w-4 h-4" />
      </Button>
      {!alerta.acknowledged && (
        <Button variant="outline" size="sm" onClick={() => onAcknowledge?.(alerta)}>
          ACK
        </Button>
      )}
    </div>
  </div>
);

// ============================================================================
// EVENTO ROW
// ============================================================================

export const EventoRow = ({ evento }) => (
  <div className="flex items-start gap-3 py-2 border-b last:border-0">
    <div className={`w-2 h-2 rounded-full mt-2 ${
      evento.tipo === 'error' ? 'bg-red-500' :
      evento.tipo === 'warning' ? 'bg-yellow-500' :
      evento.tipo === 'success' ? 'bg-green-500' :
      'bg-zinc-400'
    }`} />
    <div className="flex-1">
      <p className="text-sm">{evento.mensaje}</p>
      <div className="flex items-center gap-2 mt-1">
        <span className="text-xs text-zinc-400">
          {new Date(evento.fecha).toLocaleString('es-MX')}
        </span>
        {evento.modulo && (
          <Badge variant="outline" className="text-xs">{evento.modulo}</Badge>
        )}
      </div>
    </div>
  </div>
);

// ============================================================================
// ESTADO VACIO
// ============================================================================

export const EstadoVacio = ({ icon: Icon, titulo, mensaje, accion, onAccion }) => (
  <div className="flex flex-col items-center justify-center py-12 text-center">
    <Icon className="w-12 h-12 text-zinc-300 mb-4" />
    <h3 className="text-lg font-medium text-zinc-600">{titulo}</h3>
    <p className="text-sm text-zinc-400 mt-1">{mensaje}</p>
    {accion && (
      <Button variant="outline" className="mt-4" onClick={onAccion}>
        {accion}
      </Button>
    )}
  </div>
);

// ============================================================================
// BANNER ALERTA CRITICA
// ============================================================================

export const BannerAlertaCritica = ({ count, onClick }) => (
  <div 
    className="bg-red-600 text-white px-4 py-2 rounded-lg flex items-center justify-between cursor-pointer hover:bg-red-700 transition-colors animate-pulse"
    onClick={onClick}
  >
    <div className="flex items-center gap-2">
      <XCircle className="w-5 h-5" />
      <span className="font-medium">
        {count} {count === 1 ? 'Alerta Crítica' : 'Alertas Críticas'} sin atender
      </span>
    </div>
    <ChevronRight className="w-5 h-5" />
  </div>
);
