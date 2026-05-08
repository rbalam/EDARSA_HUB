/**
 * Card de Acciones de Tesorería
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { CheckCircle2, XCircle } from 'lucide-react';

const formatDate = (dateStr) => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString('es-MX', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
};

export default function AccionesTesoreriaCard({
  selectedItem,
  comentario,
  setComentario,
  onAccion,
  procesando
}) {
  return (
    <Card className="border-cyan-200 bg-cyan-50/30">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm text-cyan-800">Autorización Final - Tesorería</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="text-xs text-zinc-600 bg-white p-2 rounded border">
          <strong>Autorizado por Gerencia:</strong> {selectedItem.autorizado_por_gerencia || 'N/A'}<br/>
          <strong>Fecha:</strong> {formatDate(selectedItem.fecha_autorizacion_gerencia)}<br/>
          {selectedItem.comentario_gerencia && <><strong>Comentario:</strong> {selectedItem.comentario_gerencia}</>}
        </div>
        <div>
          <Label className="text-xs">Comentario (opcional)</Label>
          <Textarea
            placeholder="Observaciones..."
            value={comentario}
            onChange={(e) => setComentario(e.target.value)}
            className="h-16"
            data-testid="textarea-comentario-tesoreria"
          />
        </div>
        <div className="flex justify-end gap-2">
          <Button variant="outline" size="sm" onClick={() => onAccion('rechazar')} disabled={procesando} data-testid="btn-rechazar-tesoreria">
            <XCircle className="w-4 h-4 mr-1" />
            Rechazar
          </Button>
          <Button size="sm" className="bg-green-600 hover:bg-green-700" onClick={() => onAccion('aprobar')} disabled={procesando} data-testid="btn-aprobar-tesoreria">
            <CheckCircle2 className="w-4 h-4 mr-1" />
            Aprobar Final
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
