import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Kanban, DollarSign, Building2, User, GripVertical, Plus, ChevronDown 
} from 'lucide-react';
import api from '@/lib/api';

const EMPRESA_ID = '00000000-0000-0000-0000-000000000001';
const PIPELINE_ID = 1;

export default function PipelinePage() {
  const [kanban, setKanban] = useState(null);
  const [loading, setLoading] = useState(true);
  const [draggedOpp, setDraggedOpp] = useState(null);

  useEffect(() => {
    loadKanban();
  }, []);

  const loadKanban = async () => {
    try {
      setLoading(true);
      const response = await api.get(
        `/crm/native/pipelines/${PIPELINE_ID}/kanban?empresa_id=${EMPRESA_ID}`
      );
      setKanban(response.data);
    } catch (err) {
      console.error('Error loading kanban:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatMoney = (amount) => {
    if (!amount) return '$0';
    if (amount >= 1000000) {
      return `$${(amount / 1000000).toFixed(1)}M`;
    }
    if (amount >= 1000) {
      return `$${(amount / 1000).toFixed(0)}K`;
    }
    return `$${amount.toFixed(0)}`;
  };

  const handleDragStart = (e, opp, fromEtapaId) => {
    setDraggedOpp({ opp, fromEtapaId });
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = async (e, toEtapaId) => {
    e.preventDefault();
    if (!draggedOpp || draggedOpp.fromEtapaId === toEtapaId) {
      setDraggedOpp(null);
      return;
    }

    try {
      await api.post(`/crm/native/oportunidades/${draggedOpp.opp.oportunidad_id}/cambiar-etapa`, {
        etapa_nueva_id: toEtapaId,
        comentario: 'Movido desde tablero Kanban'
      });
      loadKanban();
    } catch (err) {
      console.error('Error moving opportunity:', err);
    } finally {
      setDraggedOpp(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="pipeline-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Kanban className="h-6 w-6 text-indigo-600" />
            Pipeline de Ventas
          </h1>
          <p className="text-gray-500">
            {kanban?.pipeline?.nombre} - Vista Kanban
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-sm text-gray-500">Total Pipeline</p>
            <p className="text-xl font-bold text-green-600">
              {formatMoney(kanban?.totales?.total_monto)}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">Ponderado</p>
            <p className="text-xl font-bold text-blue-600">
              {formatMoney(kanban?.totales?.monto_ponderado)}
            </p>
          </div>
        </div>
      </div>

      {/* Kanban Board */}
      <div className="flex gap-4 overflow-x-auto pb-4">
        {kanban?.columnas?.map((columna) => (
          <div 
            key={columna.etapa.etapa_id}
            className="flex-shrink-0 w-72"
            onDragOver={handleDragOver}
            onDrop={(e) => handleDrop(e, columna.etapa.etapa_id)}
          >
            {/* Header de columna */}
            <div 
              className="rounded-t-lg p-3 flex items-center justify-between"
              style={{ backgroundColor: `${columna.etapa.color_hex}20` }}
            >
              <div className="flex items-center gap-2">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: columna.etapa.color_hex }}
                ></div>
                <span className="font-medium text-sm">{columna.etapa.nombre}</span>
                <Badge variant="secondary" className="text-xs">
                  {columna.count}
                </Badge>
              </div>
              <span className="text-xs font-medium text-gray-500">
                {columna.etapa.probabilidad_default}%
              </span>
            </div>

            {/* Contenido de columna */}
            <div 
              className="bg-gray-50 rounded-b-lg min-h-[400px] p-2 space-y-2"
              style={{ borderTop: `3px solid ${columna.etapa.color_hex}` }}
            >
              {/* Total de la columna */}
              {columna.total_monto > 0 && (
                <div className="text-center py-1 text-xs text-gray-500 border-b mb-2">
                  {formatMoney(columna.total_monto)}
                </div>
              )}

              {/* Cards de oportunidades */}
              {columna.oportunidades?.map((opp) => (
                <Card 
                  key={opp.oportunidad_id}
                  className="cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow"
                  draggable
                  onDragStart={(e) => handleDragStart(e, opp, columna.etapa.etapa_id)}
                  data-testid={`kanban-card-${opp.oportunidad_id}`}
                >
                  <CardContent className="p-3">
                    <div className="flex items-start gap-2">
                      <GripVertical className="h-4 w-4 text-gray-300 flex-shrink-0 mt-1" />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm truncate">
                          {opp.nombre_oportunidad}
                        </p>
                        <p className="text-xs text-gray-500 font-mono">
                          {opp.folio_oportunidad}
                        </p>
                        
                        {opp.cuenta_nombre && (
                          <div className="flex items-center gap-1 mt-2 text-xs text-gray-600">
                            <Building2 className="h-3 w-3" />
                            <span className="truncate">{opp.cuenta_nombre}</span>
                          </div>
                        )}

                        <div className="flex items-center justify-between mt-2">
                          <div className="flex items-center gap-1 text-green-700 font-semibold text-sm">
                            <DollarSign className="h-3 w-3" />
                            {formatMoney(opp.monto_estimado)}
                          </div>
                          {opp.ejecutivo_nombre && (
                            <div className="flex items-center gap-1 text-xs text-gray-500">
                              <User className="h-3 w-3" />
                              <span className="truncate max-w-[60px]">
                                {opp.ejecutivo_nombre.split(' ')[0]}
                              </span>
                            </div>
                          )}
                        </div>

                        {opp.dias_en_etapa_actual > 0 && (
                          <div className="mt-2 text-xs text-gray-400">
                            {opp.dias_en_etapa_actual} días en etapa
                          </div>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {/* Área vacía para drop */}
              {columna.oportunidades?.length === 0 && (
                <div className="flex items-center justify-center h-32 border-2 border-dashed border-gray-200 rounded-lg text-gray-400 text-sm">
                  Sin oportunidades
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Leyenda */}
      <div className="flex items-center gap-6 text-sm text-gray-500">
        <span>Arrastra las tarjetas para mover oportunidades entre etapas</span>
        <span className="flex items-center gap-2">
          <span className="font-medium">Total:</span>
          {kanban?.totales?.total_oportunidades || 0} oportunidades
        </span>
      </div>
    </div>
  );
}
