/**
 * Card de Periodo Estadístico para Consumo (Editable por Gerencia)
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { TrendingUp, Settings2, Save } from 'lucide-react';

const formatDate = (dateStr) => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString('es-MX', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
};

export default function PeriodoEstadisticoCard({
  selectedItem,
  isGerencia,
  editandoConsumo,
  setEditandoConsumo,
  fechaConsumoInicio,
  setFechaConsumoInicio,
  fechaConsumoFin,
  setFechaConsumoFin,
  porcentajeAjuste,
  setPorcentajeAjuste,
  motivoAjuste,
  setMotivoAjuste,
  onGuardar,
  procesando
}) {
  const handleCancelar = () => {
    setEditandoConsumo(false);
    setFechaConsumoInicio(selectedItem.fecha_consumo_inicio?.split('T')[0] || '');
    setFechaConsumoFin(selectedItem.fecha_consumo_fin?.split('T')[0] || '');
    setPorcentajeAjuste(selectedItem.porcentaje_ajuste_consumo || 0);
  };

  return (
    <Card className="bg-purple-50/50 border-purple-200">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2 text-purple-800">
            <TrendingUp className="w-4 h-4" />
            Periodo Estadístico para Consumo
            {isGerencia && !editandoConsumo && (
              <Button 
                size="sm" 
                variant="ghost" 
                className="h-6 px-2 text-purple-600 hover:text-purple-800"
                onClick={() => setEditandoConsumo(true)}
                data-testid="btn-edit-consumo"
              >
                <Settings2 className="w-3 h-3 mr-1" />
                Editar
              </Button>
            )}
          </CardTitle>
          {(selectedItem.porcentaje_ajuste_consumo !== 0 && selectedItem.porcentaje_ajuste_consumo !== undefined) && (
            <Badge className={`text-xs ${selectedItem.porcentaje_ajuste_consumo > 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
              Ajuste: {selectedItem.porcentaje_ajuste_consumo > 0 ? '+' : ''}{selectedItem.porcentaje_ajuste_consumo}%
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        {editandoConsumo && isGerencia ? (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-xs text-purple-700">Fecha Inicio Estadístico</Label>
                <Input
                  type="date"
                  value={fechaConsumoInicio}
                  onChange={(e) => setFechaConsumoInicio(e.target.value)}
                  className="h-8 text-sm"
                  data-testid="input-fecha-consumo-inicio"
                />
                <p className="text-xs text-zinc-500 mt-1">Ej: Semana Santa año anterior</p>
              </div>
              <div>
                <Label className="text-xs text-purple-700">Fecha Fin Estadístico</Label>
                <Input
                  type="date"
                  value={fechaConsumoFin}
                  onChange={(e) => setFechaConsumoFin(e.target.value)}
                  className="h-8 text-sm"
                  data-testid="input-fecha-consumo-fin"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-xs text-purple-700">Ajuste Porcentual (%)</Label>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    min="-100"
                    max="500"
                    step="5"
                    value={porcentajeAjuste}
                    onChange={(e) => setPorcentajeAjuste(e.target.value)}
                    className="h-8 text-sm w-24"
                    data-testid="input-porcentaje-ajuste"
                  />
                  <span className="text-xs text-zinc-500">-100% a +500%</span>
                </div>
                <p className="text-xs text-zinc-500 mt-1">
                  +10% = más consumo esperado, -10% = menos consumo
                </p>
              </div>
              <div>
                <Label className="text-xs text-purple-700">Motivo del Ajuste</Label>
                <Input
                  type="text"
                  value={motivoAjuste}
                  onChange={(e) => setMotivoAjuste(e.target.value)}
                  placeholder="Ej: Más comensales este año"
                  className="h-8 text-sm"
                  data-testid="input-motivo-ajuste"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button size="sm" variant="ghost" onClick={handleCancelar}>
                Cancelar
              </Button>
              <Button 
                size="sm" 
                onClick={onGuardar}
                disabled={procesando}
                data-testid="btn-guardar-consumo"
              >
                <Save className="w-3 h-3 mr-1" />
                Guardar Cambios
              </Button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div>
              <div className="text-purple-600 text-xs font-medium">Fecha Inicio</div>
              <div className="font-medium text-zinc-800">
                {selectedItem.fecha_consumo_inicio 
                  ? formatDate(selectedItem.fecha_consumo_inicio).split(',')[0]
                  : formatDate(selectedItem.fecha_inicio_periodo).split(',')[0]}
              </div>
            </div>
            <div>
              <div className="text-purple-600 text-xs font-medium">Fecha Fin</div>
              <div className="font-medium text-zinc-800">
                {selectedItem.fecha_consumo_fin 
                  ? formatDate(selectedItem.fecha_consumo_fin).split(',')[0]
                  : formatDate(selectedItem.fecha_fin_periodo).split(',')[0]}
              </div>
            </div>
            <div>
              <div className="text-purple-600 text-xs font-medium">Días Estadísticos</div>
              <div className="font-medium text-zinc-800">{selectedItem.dias_periodo_consumo || selectedItem.dias_periodo_analisis || 15}</div>
            </div>
            <div>
              <div className="text-purple-600 text-xs font-medium">Ajuste Aplicado</div>
              <div className={`font-medium ${(selectedItem.porcentaje_ajuste_consumo || 0) > 0 ? 'text-green-600' : (selectedItem.porcentaje_ajuste_consumo || 0) < 0 ? 'text-red-600' : 'text-zinc-800'}`}>
                {(selectedItem.porcentaje_ajuste_consumo || 0) > 0 ? '+' : ''}{selectedItem.porcentaje_ajuste_consumo || 0}%
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
