/**
 * Card de Acciones de Gerencia
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { CheckCircle2, XCircle, Settings2 } from 'lucide-react';

export default function AccionesGerenciaCard({
  comentario,
  setComentario,
  onAccion,
  procesando
}) {
  return (
    <Card className="border-purple-200 bg-purple-50/30">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm text-purple-800">Acción Gerencia</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div>
          <Label className="text-xs">Comentario (opcional)</Label>
          <Textarea
            placeholder="Observaciones..."
            value={comentario}
            onChange={(e) => setComentario(e.target.value)}
            className="h-16"
            data-testid="textarea-comentario-gerencia"
          />
        </div>
        <div className="flex justify-end gap-2">
          <Button variant="outline" size="sm" onClick={() => onAccion('rechazar')} disabled={procesando} data-testid="btn-rechazar-gerencia">
            <XCircle className="w-4 h-4 mr-1" />
            Rechazar
          </Button>
          <Button variant="secondary" size="sm" onClick={() => onAccion('ajuste')} disabled={procesando} data-testid="btn-ajuste-gerencia">
            <Settings2 className="w-4 h-4 mr-1" />
            Solicitar Ajuste
          </Button>
          <Button size="sm" onClick={() => onAccion('aprobar')} disabled={procesando} data-testid="btn-aprobar-gerencia">
            <CheckCircle2 className="w-4 h-4 mr-1" />
            Aprobar y Enviar a Tesorería
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
