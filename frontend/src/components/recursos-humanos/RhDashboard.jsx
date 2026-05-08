/**
 * EDARSA HUB - RH Dashboard
 * =========================
 * Dashboard del módulo de Recursos Humanos.
 * Muestra KPIs, distribución por departamento, incidencias del mes y flujos pendientes.
 * 
 * FASE 4E: Extraído de RecursosHumanos.js
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import {
  Users,
  Calendar,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Briefcase,
  Clock,
  ChevronRight,
} from 'lucide-react';

/**
 * KPI Card individual
 */
const KpiCard = ({ title, value, icon: Icon, gradient, iconColor }) => (
  <Card className={`${gradient} text-white`}>
    <CardContent className="p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className={`${iconColor} text-xs`}>{title}</p>
          <p className="text-2xl font-bold">{value}</p>
        </div>
        <Icon className={`h-8 w-8 ${iconColor}`} />
      </div>
    </CardContent>
  </Card>
);

/**
 * Dashboard de Recursos Humanos
 */
export default function RhDashboard({ dashboard, onTabChange }) {
  const resumen = dashboard?.resumen || {};
  const porDepto = dashboard?.por_departamento || [];
  const incMes = dashboard?.incidencias_mes || [];
  const flujosPend = dashboard?.flujos_pendientes || [];
  const alertas = dashboard?.alertas_fraude || 0;

  return (
    <div className="space-y-6" data-testid="rh-dashboard">
      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <KpiCard
          title="Total"
          value={resumen.total || 0}
          icon={Users}
          gradient="bg-gradient-to-br from-blue-500 to-blue-600"
          iconColor="text-blue-200"
        />
        <KpiCard
          title="Activos"
          value={resumen.activos || 0}
          icon={CheckCircle2}
          gradient="bg-gradient-to-br from-green-500 to-green-600"
          iconColor="text-green-200"
        />
        <KpiCard
          title="Vacaciones"
          value={resumen.vacaciones || 0}
          icon={Calendar}
          gradient="bg-gradient-to-br from-amber-500 to-amber-600"
          iconColor="text-amber-200"
        />
        <KpiCard
          title="Incapacidad"
          value={resumen.incapacidad || 0}
          icon={FileText}
          gradient="bg-gradient-to-br from-purple-500 to-purple-600"
          iconColor="text-purple-200"
        />
        <Card className={`${alertas > 0 ? 'bg-gradient-to-br from-red-500 to-red-600' : 'bg-gradient-to-br from-zinc-500 to-zinc-600'} text-white`}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-red-100 text-xs">Alertas Fraude</p>
                <p className="text-2xl font-bold">{alertas}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-200" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Por departamento */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Briefcase className="h-4 w-4" />
              Por Departamento
            </CardTitle>
          </CardHeader>
          <CardContent>
            {porDepto.length === 0 ? (
              <p className="text-sm text-zinc-400 text-center py-4">Sin datos</p>
            ) : (
              <div className="space-y-2">
                {porDepto.slice(0, 8).map((d, idx) => (
                  <div key={d.departamento || `dept-${idx}`} className="flex items-center justify-between py-1.5 border-b last:border-0">
                    <span className="text-sm text-zinc-600 truncate">{d.departamento || 'Sin Depto'}</span>
                    <span className="text-sm font-medium bg-zinc-100 px-2 py-0.5 rounded">{d.total}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Incidencias del mes */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              Incidencias del Mes
            </CardTitle>
          </CardHeader>
          <CardContent>
            {incMes.length === 0 ? (
              <p className="text-sm text-zinc-400 text-center py-4">Sin incidencias</p>
            ) : (
              <div className="space-y-2">
                {incMes.slice(0, 6).map((inc, idx) => (
                  <div key={inc.tipo || `inc-${idx}`} className="flex items-center justify-between py-1.5 border-b last:border-0">
                    <span className="text-sm text-zinc-600">{inc.tipo}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{inc.total}</span>
                      {inc.monto_total > 0 && (
                        <span className="text-xs text-zinc-400">
                          ${inc.monto_total.toLocaleString()}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Flujos pendientes */}
      {flujosPend.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Flujos de Nómina Pendientes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {flujosPend.slice(0, 6).map((flujo, idx) => (
                <div 
                  key={flujo.id || `flujo-${idx}`} 
                  className="flex items-center justify-between p-3 bg-amber-50 rounded-lg border border-amber-200 cursor-pointer hover:bg-amber-100 transition-colors"
                  onClick={() => onTabChange && onTabChange('nomina')}
                >
                  <div>
                    <p className="text-sm font-medium text-zinc-800">{flujo.sucursal}</p>
                    <p className="text-xs text-amber-600">{flujo.etapa_actual}</p>
                  </div>
                  <ChevronRight className="h-4 w-4 text-zinc-400" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
