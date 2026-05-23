import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { 
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue 
} from '@/components/ui/select';
import { X, Save, Briefcase, Loader2, DollarSign } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/lib/api';

const EMPRESA_ID = '00000000-0000-0000-0000-000000000001';

export default function OportunidadForm({ oportunidad, onClose, onSaved }) {
  const [loading, setLoading] = useState(false);
  const [pipelines, setPipelines] = useState([]);
  const [selectedPipeline, setSelectedPipeline] = useState(null);
  const [formData, setFormData] = useState({
    nombre_oportunidad: '',
    descripcion_oportunidad: '',
    monto_estimado: '',
    pipeline_id: '1',
    etapa_actual_id: '1',
    fecha_estimada_cierre: '',
    observaciones_internas: '',
  });

  useEffect(() => {
    loadPipelines();
    if (oportunidad) {
      setFormData({
        nombre_oportunidad: oportunidad.nombre_oportunidad || '',
        descripcion_oportunidad: oportunidad.descripcion_oportunidad || '',
        monto_estimado: oportunidad.monto_estimado || '',
        pipeline_id: oportunidad.pipeline_id?.toString() || '1',
        etapa_actual_id: oportunidad.etapa_actual_id?.toString() || '1',
        fecha_estimada_cierre: oportunidad.fecha_estimada_cierre 
          ? new Date(oportunidad.fecha_estimada_cierre).toISOString().split('T')[0] 
          : '',
        observaciones_internas: oportunidad.observaciones_internas || '',
      });
    }
  }, [oportunidad]);

  const loadPipelines = async () => {
    try {
      const response = await api.get('/crm/native/pipelines');
      setPipelines(response.data.pipelines || []);
      if (response.data.pipelines?.length > 0) {
        setSelectedPipeline(response.data.pipelines[0]);
      }
    } catch (err) {
      console.error('Error loading pipelines:', err);
    }
  };

  useEffect(() => {
    if (formData.pipeline_id && pipelines.length > 0) {
      const pipeline = pipelines.find(p => p.pipeline_id.toString() === formData.pipeline_id);
      setSelectedPipeline(pipeline || null);
    }
  }, [formData.pipeline_id, pipelines]);

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.nombre_oportunidad.trim()) {
      toast.error('El nombre de la oportunidad es requerido');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        ...formData,
        empresa_id: EMPRESA_ID,
        pipeline_id: parseInt(formData.pipeline_id),
        etapa_actual_id: parseInt(formData.etapa_actual_id),
        monto_estimado: formData.monto_estimado ? parseFloat(formData.monto_estimado) : null,
        fecha_estimada_cierre: formData.fecha_estimada_cierre || null,
      };

      if (oportunidad) {
        // Para actualizar, solo enviamos los campos modificables
        await api.put(`/crm/native/oportunidades/${oportunidad.oportunidad_id}`, {
          nombre_oportunidad: payload.nombre_oportunidad,
          descripcion_oportunidad: payload.descripcion_oportunidad,
          monto_estimado: payload.monto_estimado,
          fecha_estimada_cierre: payload.fecha_estimada_cierre,
          observaciones_internas: payload.observaciones_internas,
        });
        toast.success('Oportunidad actualizada correctamente');
      } else {
        await api.post('/crm/native/oportunidades', payload);
        toast.success('Oportunidad creada correctamente');
      }
      
      onSaved();
    } catch (err) {
      console.error('Error saving oportunidad:', err);
      toast.error(err.response?.data?.detail || 'Error al guardar la oportunidad');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between sticky top-0 bg-white z-10 border-b">
          <CardTitle className="flex items-center gap-2">
            <Briefcase className="h-5 w-5" />
            {oportunidad ? 'Editar Oportunidad' : 'Nueva Oportunidad'}
          </CardTitle>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </CardHeader>
        <CardContent className="pt-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Información Principal */}
            <div className="space-y-4">
              <h3 className="font-medium text-sm text-gray-500 uppercase tracking-wide">
                Información Principal
              </h3>
              <div className="space-y-2">
                <Label htmlFor="nombre_oportunidad">Nombre de la Oportunidad *</Label>
                <Input
                  id="nombre_oportunidad"
                  value={formData.nombre_oportunidad}
                  onChange={(e) => handleChange('nombre_oportunidad', e.target.value)}
                  placeholder="Proyecto ERP para Acme Corp"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="descripcion_oportunidad">Descripción</Label>
                <Textarea
                  id="descripcion_oportunidad"
                  value={formData.descripcion_oportunidad}
                  onChange={(e) => handleChange('descripcion_oportunidad', e.target.value)}
                  placeholder="Descripción detallada de la oportunidad..."
                  rows={3}
                />
              </div>
            </div>

            {/* Valor y Fecha */}
            <div className="space-y-4">
              <h3 className="font-medium text-sm text-gray-500 uppercase tracking-wide">
                Valor y Fecha
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="monto_estimado">Monto Estimado (MXN)</Label>
                  <div className="relative">
                    <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      id="monto_estimado"
                      type="number"
                      value={formData.monto_estimado}
                      onChange={(e) => handleChange('monto_estimado', e.target.value)}
                      placeholder="100000"
                      className="pl-10"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="fecha_estimada_cierre">Fecha Estimada de Cierre</Label>
                  <Input
                    id="fecha_estimada_cierre"
                    type="date"
                    value={formData.fecha_estimada_cierre}
                    onChange={(e) => handleChange('fecha_estimada_cierre', e.target.value)}
                  />
                </div>
              </div>
            </div>

            {/* Pipeline y Etapa (solo para nuevas oportunidades) */}
            {!oportunidad && (
              <div className="space-y-4">
                <h3 className="font-medium text-sm text-gray-500 uppercase tracking-wide">
                  Pipeline y Etapa Inicial
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Pipeline</Label>
                    <Select 
                      value={formData.pipeline_id} 
                      onValueChange={(value) => {
                        handleChange('pipeline_id', value);
                        handleChange('etapa_actual_id', ''); // Reset etapa
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Seleccionar pipeline" />
                      </SelectTrigger>
                      <SelectContent>
                        {pipelines.map((pipeline) => (
                          <SelectItem key={pipeline.pipeline_id} value={pipeline.pipeline_id.toString()}>
                            {pipeline.nombre}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Etapa Inicial</Label>
                    <Select 
                      value={formData.etapa_actual_id} 
                      onValueChange={(value) => handleChange('etapa_actual_id', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Seleccionar etapa" />
                      </SelectTrigger>
                      <SelectContent>
                        {selectedPipeline?.etapas?.map((etapa) => (
                          <SelectItem key={etapa.etapa_id} value={etapa.etapa_id.toString()}>
                            <div className="flex items-center gap-2">
                              <div 
                                className="w-2 h-2 rounded-full" 
                                style={{ backgroundColor: etapa.color_hex }}
                              />
                              {etapa.nombre} ({etapa.probabilidad_default}%)
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            )}

            {/* Notas Internas */}
            <div className="space-y-2">
              <Label htmlFor="observaciones_internas">Notas Internas</Label>
              <Textarea
                id="observaciones_internas"
                value={formData.observaciones_internas}
                onChange={(e) => handleChange('observaciones_internas', e.target.value)}
                placeholder="Notas internas del equipo..."
                rows={2}
              />
            </div>

            {/* Botones */}
            <div className="flex justify-end gap-3 pt-4 border-t">
              <Button type="button" variant="outline" onClick={onClose}>
                Cancelar
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Guardando...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    {oportunidad ? 'Actualizar' : 'Crear Oportunidad'}
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
