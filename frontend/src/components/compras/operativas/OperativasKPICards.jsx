/**
 * KPI Cards para Tab Automatizaciones Operativas de Compras
 */

import { Card } from '@/components/ui/card';

export default function OperativasKPICards({ kpis = {} }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3" data-testid="operativas-kpis">
      <Card className="p-3">
        <div className="text-2xl font-bold text-zinc-900">{kpis.total || 0}</div>
        <div className="text-xs text-zinc-500">Total</div>
      </Card>
      <Card className="p-3 border-amber-200 bg-amber-50/50">
        <div className="text-2xl font-bold text-amber-600">{kpis.pendientes_inventario || 0}</div>
        <div className="text-xs text-amber-700">Pend. Inventario</div>
      </Card>
      <Card className="p-3 border-blue-200 bg-blue-50/50">
        <div className="text-2xl font-bold text-blue-600">{kpis.en_proceso || 0}</div>
        <div className="text-xs text-blue-700">En Proceso</div>
      </Card>
      <Card className="p-3 border-purple-200 bg-purple-50/50">
        <div className="text-2xl font-bold text-purple-600">{kpis.pendientes_revision || 0}</div>
        <div className="text-xs text-purple-700">Rev. Gerencia</div>
      </Card>
      <Card className="p-3 border-cyan-200 bg-cyan-50/50">
        <div className="text-2xl font-bold text-cyan-600">{kpis.pendientes_tesoreria || 0}</div>
        <div className="text-xs text-cyan-700">Pend. Tesorería</div>
      </Card>
      <Card className="p-3 border-green-200 bg-green-50/50">
        <div className="text-2xl font-bold text-green-600">{kpis.aprobados || 0}</div>
        <div className="text-xs text-green-700">Aprobados</div>
      </Card>
      <Card className="p-3 border-red-200 bg-red-50/50">
        <div className="text-2xl font-bold text-red-600">{kpis.rechazados || 0}</div>
        <div className="text-xs text-red-700">Rechazados</div>
      </Card>
    </div>
  );
}
