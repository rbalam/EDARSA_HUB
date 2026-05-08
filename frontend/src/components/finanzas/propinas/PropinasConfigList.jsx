/**
 * Lista de configuraciones de propinas
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Settings, RefreshCw, Edit2, Store, Building, Percent } from 'lucide-react';
import { formatCurrency, formatPercent, formatDate } from './utils';

export default function PropinasConfigList({ 
  configs, 
  loading, 
  onRefresh, 
  onEdit, 
  isAdmin 
}) {
  return (
    <Card>
      <CardHeader className="bg-zinc-800 text-white py-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center">
            <Settings className="h-5 w-5 mr-2" />
            Configuraciones de % Descuento
          </CardTitle>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={onRefresh}
            className="text-white hover:bg-zinc-700"
            data-testid="btn-refrescar-configs"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {loading ? (
          <div className="p-8 text-center text-zinc-500">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2" />
            Cargando...
          </div>
        ) : configs.length === 0 ? (
          <div className="p-8 text-center text-zinc-500">
            <Settings className="h-8 w-8 mx-auto mb-2" />
            No hay configuraciones. Se usará el 2% por defecto.
          </div>
        ) : (
          <div className="divide-y">
            {configs.map((config, idx) => (
              <PropinasConfigItem 
                key={config.id || idx} 
                config={config} 
                onEdit={onEdit} 
                isAdmin={isAdmin} 
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function PropinasConfigItem({ config, onEdit, isAdmin }) {
  const getAlcanceIcon = () => {
    if (config.alcance?.tipo === 'SUCURSAL') return <Store className="h-5 w-5" />;
    if (config.alcance?.tipo === 'EMPRESA') return <Building className="h-5 w-5" />;
    return <Percent className="h-5 w-5" />;
  };

  const getAlcanceStyle = () => {
    if (config.alcance?.tipo === 'SUCURSAL') return 'bg-blue-100 text-blue-600';
    if (config.alcance?.tipo === 'EMPRESA') return 'bg-amber-100 text-amber-600';
    return 'bg-zinc-100 text-zinc-600';
  };

  const getAlcanceLabel = () => {
    if (config.alcance?.tipo === 'SUCURSAL') return config.alcance.sucursal_id || 'Sucursal';
    if (config.alcance?.tipo === 'EMPRESA') return config.alcance.empresa_id || 'Empresa';
    return 'GLOBAL';
  };

  return (
    <div 
      className={`p-4 ${config.vigencia?.activa ? 'bg-white' : 'bg-zinc-50'}`}
      data-testid={`config-item-${config.id}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className={`p-2 rounded-full ${getAlcanceStyle()}`}>
            {getAlcanceIcon()}
          </div>
          
          <div>
            <div className="flex items-center gap-2">
              <span className="font-medium">{getAlcanceLabel()}</span>
              <span className={`px-2 py-0.5 rounded text-xs ${
                config.vigencia?.activa 
                  ? 'bg-green-100 text-green-700' 
                  : 'bg-zinc-200 text-zinc-600'
              }`}>
                {config.vigencia?.activa ? 'Activa' : 'Inactiva'}
              </span>
            </div>
            <p className="text-sm text-zinc-500">
              Desde: {formatDate(config.vigencia?.fecha_inicio)}
              {config.vigencia?.fecha_fin && ` hasta ${formatDate(config.vigencia.fecha_fin)}`}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-6">
          <div className="text-right">
            <p className="text-2xl font-bold text-blue-600">
              {formatPercent(config.parametros?.porcentaje_comision)}
            </p>
            <p className="text-xs text-zinc-500">Descuento</p>
          </div>
          
          <div className="text-right">
            <p className="text-lg font-medium text-zinc-700">
              {formatCurrency(config.parametros?.tolerancia_descuadre)}
            </p>
            <p className="text-xs text-zinc-500">Tolerancia</p>
          </div>
          
          {isAdmin && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onEdit(config)}
              data-testid={`btn-editar-config-${config.id}`}
            >
              <Edit2 className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
      
      {config.motivo_cambio && (
        <p className="mt-2 text-xs text-zinc-500 italic">
          {config.motivo_cambio}
        </p>
      )}
    </div>
  );
}
