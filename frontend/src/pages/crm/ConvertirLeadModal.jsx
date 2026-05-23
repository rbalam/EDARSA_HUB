import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { 
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue 
} from '@/components/ui/select';
import { X, ArrowRight, Building2, User, Briefcase, Loader2, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/lib/api';

export default function ConvertirLeadModal({ lead, onClose, onConverted }) {
  const [loading, setLoading] = useState(false);
  const [pipelines, setPipelines] = useState([]);
  const [formData, setFormData] = useState({
    crear_cuenta: true,
    crear_contacto: true,
    crear_oportunidad: true,
    nombre_oportunidad: `Oportunidad - ${lead?.nombre_empresa || lead?.nombre_contacto || ''}`,
    monto_estimado: lead?.presupuesto || '',
    pipeline_id: '1',
  });

  useEffect(() => {
    loadPipelines();
  }, []);

  const loadPipelines = async () => {
    try {
      const response = await api.get('/crm/native/pipelines');
      setPipelines(response.data.pipelines || []);
    } catch (err) {
      console.error('Error loading pipelines:', err);
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.crear_cuenta && !formData.crear_contacto && !formData.crear_oportunidad) {
      toast.error('Debes seleccionar al menos una opción');
      return;
    }

    setLoading(true);
    try {
      const response = await api.post(`/crm/native/leads/${lead.lead_id}/convertir`, {
        crear_cuenta: formData.crear_cuenta,
        crear_contacto: formData.crear_contacto,
        crear_oportunidad: formData.crear_oportunidad,
        nombre_oportunidad: formData.nombre_oportunidad || null,
        monto_estimado: formData.monto_estimado ? parseFloat(formData.monto_estimado) : null,
        pipeline_id: formData.pipeline_id ? parseInt(formData.pipeline_id) : null,
      });
      
      toast.success('Lead convertido exitosamente');
      onConverted(response.data);
    } catch (err) {
      console.error('Error converting lead:', err);
      toast.error(err.response?.data?.detail || 'Error al convertir el lead');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-lg">
        <CardHeader className="flex flex-row items-center justify-between border-b">
          <CardTitle className="text-lg flex items-center gap-2">
            <ArrowRight className="h-5 w-5" />
            Convertir Lead
          </CardTitle>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </CardHeader>
        <CardContent className="pt-6">
          {/* Info del Lead */}
          <div className="bg-blue-50 rounded-lg p-4 mb-6">
            <p className="text-sm text-blue-600 font-medium">{lead.folio_lead}</p>
            <p className="font-semibold text-lg">
              {lead.nombre_contacto} {lead.apellido_paterno}
            </p>
            {lead.nombre_empresa && (
              <p className="text-gray-600">{lead.nombre_empresa}</p>
            )}
            {lead.presupuesto && (
              <p className="text-green-600 font-medium mt-1">
                Presupuesto: ${lead.presupuesto.toLocaleString('es-MX')} MXN
              </p>
            )}
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Opciones de conversión */}
            <div className="space-y-4">
              <h3 className="font-medium text-sm text-gray-500 uppercase tracking-wide">
                ¿Qué deseas crear?
              </h3>

              {/* Crear Cuenta */}
              <div className="flex items-start space-x-3 p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                <Checkbox
                  id="crear_cuenta"
                  checked={formData.crear_cuenta}
                  onCheckedChange={(checked) => handleChange('crear_cuenta', checked)}
                />
                <div className="flex-1">
                  <Label 
                    htmlFor="crear_cuenta" 
                    className="flex items-center gap-2 cursor-pointer"
                  >
                    <Building2 className="h-4 w-4 text-blue-600" />
                    Crear Cuenta (Cliente)
                  </Label>
                  <p className="text-sm text-gray-500 mt-1">
                    Se creará una cuenta con el nombre: <strong>{lead.nombre_empresa || 'Sin empresa'}</strong>
                  </p>
                </div>
              </div>

              {/* Crear Contacto */}
              <div className="flex items-start space-x-3 p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                <Checkbox
                  id="crear_contacto"
                  checked={formData.crear_contacto}
                  onCheckedChange={(checked) => handleChange('crear_contacto', checked)}
                  disabled={!formData.crear_cuenta}
                />
                <div className="flex-1">
                  <Label 
                    htmlFor="crear_contacto" 
                    className="flex items-center gap-2 cursor-pointer"
                  >
                    <User className="h-4 w-4 text-green-600" />
                    Crear Contacto
                  </Label>
                  <p className="text-sm text-gray-500 mt-1">
                    Se asociará a la cuenta: <strong>{lead.nombre_contacto} {lead.apellido_paterno}</strong>
                  </p>
                  {!formData.crear_cuenta && (
                    <p className="text-xs text-amber-600 mt-1">
                      Requiere crear cuenta primero
                    </p>
                  )}
                </div>
              </div>

              {/* Crear Oportunidad */}
              <div className="flex items-start space-x-3 p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                <Checkbox
                  id="crear_oportunidad"
                  checked={formData.crear_oportunidad}
                  onCheckedChange={(checked) => handleChange('crear_oportunidad', checked)}
                />
                <div className="flex-1">
                  <Label 
                    htmlFor="crear_oportunidad" 
                    className="flex items-center gap-2 cursor-pointer"
                  >
                    <Briefcase className="h-4 w-4 text-purple-600" />
                    Crear Oportunidad
                  </Label>
                  <p className="text-sm text-gray-500 mt-1">
                    Se creará una oportunidad en el pipeline
                  </p>
                </div>
              </div>
            </div>

            {/* Opciones de oportunidad */}
            {formData.crear_oportunidad && (
              <div className="space-y-4 p-4 bg-purple-50 rounded-lg">
                <h3 className="font-medium text-sm text-purple-700 uppercase tracking-wide">
                  Datos de la Oportunidad
                </h3>
                <div className="space-y-2">
                  <Label htmlFor="nombre_oportunidad">Nombre</Label>
                  <Input
                    id="nombre_oportunidad"
                    value={formData.nombre_oportunidad}
                    onChange={(e) => handleChange('nombre_oportunidad', e.target.value)}
                    placeholder="Nombre de la oportunidad"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="monto_estimado">Monto Estimado</Label>
                    <Input
                      id="monto_estimado"
                      type="number"
                      value={formData.monto_estimado}
                      onChange={(e) => handleChange('monto_estimado', e.target.value)}
                      placeholder="100000"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Pipeline</Label>
                    <Select 
                      value={formData.pipeline_id} 
                      onValueChange={(value) => handleChange('pipeline_id', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Seleccionar" />
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
                </div>
              </div>
            )}

            {/* Resumen */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-medium text-sm mb-2">Resumen de conversión:</h4>
              <ul className="space-y-1 text-sm">
                {formData.crear_cuenta && (
                  <li className="flex items-center gap-2 text-green-600">
                    <CheckCircle className="h-4 w-4" />
                    Se creará una cuenta
                  </li>
                )}
                {formData.crear_contacto && formData.crear_cuenta && (
                  <li className="flex items-center gap-2 text-green-600">
                    <CheckCircle className="h-4 w-4" />
                    Se creará un contacto
                  </li>
                )}
                {formData.crear_oportunidad && (
                  <li className="flex items-center gap-2 text-green-600">
                    <CheckCircle className="h-4 w-4" />
                    Se creará una oportunidad
                  </li>
                )}
                <li className="flex items-center gap-2 text-blue-600">
                  <ArrowRight className="h-4 w-4" />
                  El lead se marcará como convertido
                </li>
              </ul>
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
                    Convirtiendo...
                  </>
                ) : (
                  <>
                    <ArrowRight className="h-4 w-4 mr-2" />
                    Convertir Lead
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
