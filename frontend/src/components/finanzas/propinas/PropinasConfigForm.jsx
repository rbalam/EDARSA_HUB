/**
 * Formulario de configuración de propinas
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Save, X, RefreshCw } from 'lucide-react';

export default function PropinasConfigForm({
  config,
  setConfig,
  empresas,
  sucursales,
  onGuardar,
  onCancelar,
  saving,
  isEditing
}) {
  const handleAlcanceTipoChange = (tipo) => {
    setConfig(prev => ({
      ...prev,
      alcance: {
        ...prev.alcance,
        tipo,
        empresa_id: tipo === 'GLOBAL' ? null : prev.alcance.empresa_id,
        sucursal_id: tipo !== 'SUCURSAL' ? null : prev.alcance.sucursal_id
      }
    }));
  };

  const handleAlcanceChange = (field, value) => {
    setConfig(prev => ({
      ...prev,
      alcance: { ...prev.alcance, [field]: value || null }
    }));
  };

  const handleParametroChange = (field, value) => {
    setConfig(prev => ({
      ...prev,
      parametros: { ...prev.parametros, [field]: value }
    }));
  };

  const handleVigenciaChange = (field, value) => {
    setConfig(prev => ({
      ...prev,
      vigencia: { ...prev.vigencia, [field]: value }
    }));
  };

  return (
    <Card className="border-2 border-blue-200 bg-blue-50">
      <CardHeader className="bg-blue-600 text-white py-3">
        <CardTitle className="text-base">
          {isEditing ? 'Editar Configuración' : 'Nueva Configuración de % Descuento'}
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-4 space-y-4">
        <div className="grid grid-cols-3 gap-4">
          {/* Tipo de Alcance */}
          <div>
            <Label className="text-xs text-zinc-500">Tipo de Alcance</Label>
            <select
              value={config.alcance.tipo}
              onChange={(e) => handleAlcanceTipoChange(e.target.value)}
              className="w-full h-10 px-3 border rounded-md text-sm"
              data-testid="config-alcance-tipo"
            >
              <option value="GLOBAL">GLOBAL (Toda la empresa)</option>
              <option value="EMPRESA">Por Empresa</option>
              <option value="SUCURSAL">Por Sucursal</option>
            </select>
          </div>
          
          {/* Empresa (si aplica) */}
          {config.alcance.tipo !== 'GLOBAL' && (
            <div>
              <Label className="text-xs text-zinc-500">Empresa</Label>
              <select
                value={config.alcance.empresa_id || ''}
                onChange={(e) => handleAlcanceChange('empresa_id', e.target.value)}
                className="w-full h-10 px-3 border rounded-md text-sm"
                data-testid="config-empresa"
              >
                <option value="">Seleccionar...</option>
                {empresas.map(emp => (
                  <option key={emp} value={emp}>{emp}</option>
                ))}
              </select>
            </div>
          )}
          
          {/* Sucursal (si aplica) */}
          {config.alcance.tipo === 'SUCURSAL' && (
            <div>
              <Label className="text-xs text-zinc-500">Sucursal</Label>
              <select
                value={config.alcance.sucursal_id || ''}
                onChange={(e) => handleAlcanceChange('sucursal_id', e.target.value)}
                className="w-full h-10 px-3 border rounded-md text-sm"
                data-testid="config-sucursal"
              >
                <option value="">Seleccionar...</option>
                {sucursales.map(suc => (
                  <option key={suc.id || suc.name} value={suc.id || suc.name}>
                    {suc.name || suc.nombre}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
        
        <div className="grid grid-cols-4 gap-4">
          {/* Porcentaje */}
          <div>
            <Label className="text-xs text-zinc-500">% Descuento</Label>
            <div className="relative">
              <Input
                type="number"
                step="0.01"
                min="0"
                max="100"
                value={(config.parametros.porcentaje_comision * 100).toFixed(2)}
                onChange={(e) => handleParametroChange('porcentaje_comision', parseFloat(e.target.value) / 100)}
                className="pr-8"
                data-testid="config-porcentaje"
              />
              <span className="absolute right-3 top-2.5 text-zinc-400">%</span>
            </div>
          </div>
          
          {/* Tolerancia */}
          <div>
            <Label className="text-xs text-zinc-500">Tolerancia Descuadre ($)</Label>
            <Input
              type="number"
              step="0.01"
              min="0"
              value={config.parametros.tolerancia_descuadre}
              onChange={(e) => handleParametroChange('tolerancia_descuadre', parseFloat(e.target.value))}
              data-testid="config-tolerancia"
            />
          </div>
          
          {/* Vigencia inicio */}
          <div>
            <Label className="text-xs text-zinc-500">Vigencia Desde</Label>
            <Input
              type="date"
              value={config.vigencia.fecha_inicio?.split('T')[0] || ''}
              onChange={(e) => handleVigenciaChange('fecha_inicio', e.target.value)}
              data-testid="config-vigencia-inicio"
            />
          </div>
          
          {/* Vigencia fin */}
          <div>
            <Label className="text-xs text-zinc-500">Vigencia Hasta (opcional)</Label>
            <Input
              type="date"
              value={config.vigencia.fecha_fin?.split('T')[0] || ''}
              onChange={(e) => handleVigenciaChange('fecha_fin', e.target.value || null)}
              data-testid="config-vigencia-fin"
            />
          </div>
        </div>
        
        {/* Motivo */}
        <div>
          <Label className="text-xs text-zinc-500">Motivo del Cambio</Label>
          <Input
            type="text"
            placeholder="Ej: Ajuste por devaluación, nuevo acuerdo con personal..."
            value={config.motivo_cambio || ''}
            onChange={(e) => setConfig(prev => ({ ...prev, motivo_cambio: e.target.value }))}
            data-testid="config-motivo"
          />
        </div>
        
        {/* Activo */}
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="config-activa"
            checked={config.vigencia.activa}
            onChange={(e) => handleVigenciaChange('activa', e.target.checked)}
            className="w-4 h-4"
            data-testid="config-activa"
          />
          <Label htmlFor="config-activa" className="text-sm">Configuración Activa</Label>
        </div>
        
        {/* Botones */}
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="outline" onClick={onCancelar} data-testid="btn-cancelar-config">
            <X className="h-4 w-4 mr-2" />
            Cancelar
          </Button>
          <Button onClick={onGuardar} disabled={saving} data-testid="btn-guardar-config">
            {saving ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
            Guardar
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
