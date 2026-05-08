/**
 * Cards de Estado Final (Aprobado/Rechazado)
 */

import { Card, CardContent } from '@/components/ui/card';
import { CheckCircle2, XCircle } from 'lucide-react';

const formatDate = (dateStr) => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString('es-MX', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
};

export function AprobadoCard({ selectedItem }) {
  return (
    <Card className="border-green-200 bg-green-50/30">
      <CardContent className="pt-4 text-sm">
        <div className="flex items-center gap-2 text-green-700">
          <CheckCircle2 className="w-5 h-5" />
          <span className="font-medium">Aprobado</span>
        </div>
        <div className="mt-2 text-xs text-zinc-600">
          <div><strong>Gerencia:</strong> {selectedItem.autorizado_por_gerencia} - {formatDate(selectedItem.fecha_autorizacion_gerencia)}</div>
          <div><strong>Tesorería:</strong> {selectedItem.autorizado_por_tesoreria} - {formatDate(selectedItem.fecha_autorizacion_tesoreria)}</div>
        </div>
      </CardContent>
    </Card>
  );
}

export function RechazadoCard({ selectedItem }) {
  return (
    <Card className="border-red-200 bg-red-50/30">
      <CardContent className="pt-4 text-sm">
        <div className="flex items-center gap-2 text-red-700">
          <XCircle className="w-5 h-5" />
          <span className="font-medium">Rechazado</span>
        </div>
        <div className="mt-2 text-xs text-zinc-600">
          <div><strong>Por:</strong> {selectedItem.rechazado_por}</div>
          <div><strong>Fecha:</strong> {formatDate(selectedItem.fecha_rechazo)}</div>
          {selectedItem.motivo_rechazo && <div><strong>Motivo:</strong> {selectedItem.motivo_rechazo}</div>}
        </div>
      </CardContent>
    </Card>
  );
}
