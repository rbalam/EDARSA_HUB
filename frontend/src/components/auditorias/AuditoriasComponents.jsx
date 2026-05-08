/**
 * Componentes de Auditorías Programadas
 */
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import {
  Calendar, Activity, CheckCircle2, XCircle, Clock, RefreshCw,
  Play, Pause, Power, PowerOff, ChevronLeft, ChevronRight
} from 'lucide-react';

// ============================================================================
// KPIs Cards
// ============================================================================

export function KPIsGrid({ kpis, loading }) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {[...Array(6)].map((_, i) => (
          <Card key={`kpi-skeleton-${i}`} className="animate-pulse">
            <CardContent className="p-4">
              <div className="h-4 bg-zinc-200 rounded w-20 mb-2"></div>
              <div className="h-8 bg-zinc-200 rounded w-12"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!kpis) return null;

  const items = [
    { label: 'Total', value: kpis.total || 0, icon: Calendar, color: 'text-blue-500' },
    { label: 'Activas', value: kpis.activas || 0, icon: Activity, color: 'text-green-500' },
    { label: 'Inactivas', value: kpis.inactivas || 0, icon: Pause, color: 'text-zinc-400' },
    { label: 'Pendientes Hoy', value: kpis.pendientes_hoy || 0, icon: Clock, color: 'text-amber-500' },
    { label: 'Completadas', value: kpis.completadas_mes || 0, icon: CheckCircle2, color: 'text-emerald-500' },
    { label: 'Fallidas', value: kpis.fallidas_mes || 0, icon: XCircle, color: 'text-red-500' },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {items.map((item) => (
        <Card key={item.label}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-zinc-500">{item.label}</span>
              <item.icon className={`w-4 h-4 ${item.color}`} />
            </div>
            <p className="text-2xl font-bold">{item.value}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// ============================================================================
// Calendario Visual
// ============================================================================

const MESES = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
               'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];

export function CalendarioAuditorias({ calendario, onCambiarMes }) {
  const { eventos, mes, anio } = calendario;
  
  // Generar días del mes
  const primerDia = new Date(anio, mes - 1, 1).getDay();
  const diasEnMes = new Date(anio, mes, 0).getDate();
  const dias = [];
  
  // Días vacíos al inicio
  for (let i = 0; i < primerDia; i++) {
    dias.push({ dia: null, eventos: [] });
  }
  
  // Días del mes
  for (let d = 1; d <= diasEnMes; d++) {
    const fechaStr = `${anio}-${String(mes).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    const eventosDelDia = eventos.filter(e => e.fecha === fechaStr);
    dias.push({ dia: d, eventos: eventosDelDia });
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            Calendario de Auditorías
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => onCambiarMes(-1)}>
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <span className="text-sm font-medium min-w-[120px] text-center">
              {MESES[mes]} {anio}
            </span>
            <Button variant="ghost" size="sm" onClick={() => onCambiarMes(1)}>
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="grid grid-cols-7 gap-1">
          {['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'].map(d => (
            <div key={d} className="text-center text-xs text-zinc-500 py-1 font-medium">
              {d}
            </div>
          ))}
          {dias.map((d, idx) => (
            <div
              key={`dia-${idx}`}
              className={`min-h-[60px] p-1 border rounded text-xs ${
                d.dia ? 'bg-white' : 'bg-zinc-50'
              } ${d.eventos.length > 0 ? 'border-blue-200' : 'border-zinc-100'}`}
            >
              {d.dia && (
                <>
                  <span className="font-medium">{d.dia}</span>
                  {d.eventos.slice(0, 2).map((e, i) => (
                    <div
                      key={`evento-${d.dia}-${i}`}
                      className={`mt-1 px-1 rounded truncate ${
                        e.estado === 'COMPLETADO' ? 'bg-green-100 text-green-700' :
                        e.estado === 'FALLIDO' ? 'bg-red-100 text-red-700' :
                        'bg-blue-100 text-blue-700'
                      }`}
                      title={e.nombre}
                    >
                      {e.nombre?.substring(0, 10)}
                    </div>
                  ))}
                  {d.eventos.length > 2 && (
                    <div className="text-zinc-400 text-center">+{d.eventos.length - 2}</div>
                  )}
                </>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Estado Badge
// ============================================================================

const ESTADO_CONFIG = {
  PENDIENTE: { class: 'bg-amber-100 text-amber-800', text: 'Pendiente', icon: Clock },
  EN_PROGRESO: { class: 'bg-blue-100 text-blue-800', text: 'En Progreso', icon: RefreshCw },
  COMPLETADO: { class: 'bg-green-100 text-green-800', text: 'Completado', icon: CheckCircle2 },
  FALLIDO: { class: 'bg-red-100 text-red-800', text: 'Fallido', icon: XCircle },
  CANCELADO: { class: 'bg-zinc-100 text-zinc-600', text: 'Cancelado', icon: XCircle },
};

export function EstadoBadge({ estado }) {
  const config = ESTADO_CONFIG[estado] || ESTADO_CONFIG.PENDIENTE;
  const Icon = config.icon;
  
  return (
    <Badge className={`${config.class} hover:${config.class}`}>
      <Icon className={`w-3 h-3 mr-1 ${estado === 'EN_PROGRESO' ? 'animate-spin' : ''}`} />
      {config.text}
    </Badge>
  );
}

// ============================================================================
// Acciones de Auditoría
// ============================================================================

export function AccionesAuditoria({ auditoria, permisos, onEjecutar, onToggleActivo, onEditar }) {
  return (
    <div className="flex items-center gap-1">
      {permisos.gestionar && (
        <>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onEjecutar(auditoria)}
            title="Ejecutar ahora"
          >
            <Play className="w-4 h-4 text-green-600" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onToggleActivo(auditoria)}
            title={auditoria.activo ? 'Desactivar' : 'Activar'}
          >
            {auditoria.activo ? (
              <PowerOff className="w-4 h-4 text-amber-600" />
            ) : (
              <Power className="w-4 h-4 text-zinc-400" />
            )}
          </Button>
        </>
      )}
      {permisos.programar && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onEditar(auditoria)}
          title="Editar"
        >
          <Activity className="w-4 h-4" />
        </Button>
      )}
    </div>
  );
}

// ============================================================================
// Empty State
// ============================================================================

export function EmptyState({ message, icon: Icon = Calendar }) {
  return (
    <div className="text-center py-12">
      <Icon className="w-12 h-12 mx-auto text-zinc-300 mb-4" />
      <p className="text-zinc-500">{message}</p>
    </div>
  );
}
