/**
 * Lista de Bitácora de Automatización
 */

import { Badge } from '@/components/ui/badge';
import { History } from 'lucide-react';

const formatDate = (dateStr) => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString('es-MX', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
};

export default function BitacoraList({ bitacora = [] }) {
  if (bitacora.length === 0) return null;

  return (
    <div className="pt-4 border-t">
      <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
        <History className="w-4 h-4" />
        Bitácora ({bitacora.length})
      </h4>
      <div className="space-y-2 max-h-40 overflow-y-auto">
        {bitacora.map((entry) => (
          <div key={`${entry.fecha}-${entry.evento}`} className="text-xs bg-zinc-50 p-2 rounded flex justify-between items-start">
            <div>
              <span className="text-zinc-400">{formatDate(entry.fecha)}</span>
              <span className="mx-2 font-medium text-zinc-700">{entry.evento}</span>
              {entry.datos?.motivo && <span className="text-zinc-500">- {entry.datos.motivo}</span>}
            </div>
            {entry.datos?.dias_nuevo && (
              <Badge variant="outline" className="text-xs">
                {entry.datos.dias_anterior} → {entry.datos.dias_nuevo} días
              </Badge>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
