import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { 
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue 
} from '@/components/ui/select';
import { X, Save, UserPlus, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/lib/api';

const EMPRESA_ID = '00000000-0000-0000-0000-000000000001';

export default function LeadForm({ lead, onClose, onSaved }) {
  const [loading, setLoading] = useState(false);
  const [catalogos, setCatalogos] = useState({});
  const [formData, setFormData] = useState({
    nombre_contacto: '',
    apellido_paterno: '',
    apellido_materno: '',
    nombre_empresa: '',
    puesto: '',
    email: '',
    telefono: '',
    telefono_movil: '',
    descripcion: '',
    presupuesto: '',
    origen_lead_id: '',
    prioridad_id: '',
  });

  useEffect(() => {
    loadCatalogos();
    if (lead) {
      setFormData({
        nombre_contacto: lead.nombre_contacto || '',
        apellido_paterno: lead.apellido_paterno || '',
        apellido_materno: lead.apellido_materno || '',
        nombre_empresa: lead.nombre_empresa || '',
        puesto: lead.puesto || '',
        email: lead.email || '',
        telefono: lead.telefono || '',
        telefono_movil: lead.telefono_movil || '',
        descripcion: lead.descripcion || '',
        presupuesto: lead.presupuesto || '',
        origen_lead_id: lead.origen_lead_id?.toString() || '',
        prioridad_id: lead.prioridad_id?.toString() || '',
      });
    }
  }, [lead]);

  const loadCatalogos = async () => {
    try {
      const response = await api.get('/crm/native/catalogos');
      setCatalogos(response.data);
    } catch (err) {
      console.error('Error loading catalogos:', err);
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.nombre_contacto.trim()) {
      toast.error('El nombre del contacto es requerido');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        ...formData,
        empresa_id: EMPRESA_ID,
        origen_lead_id: formData.origen_lead_id ? parseInt(formData.origen_lead_id) : null,
        prioridad_id: formData.prioridad_id ? parseInt(formData.prioridad_id) : null,
        presupuesto: formData.presupuesto ? parseFloat(formData.presupuesto) : null,
      };

      if (lead) {
        await api.put(`/crm/native/leads/${lead.lead_id}`, payload);
        toast.success('Lead actualizado correctamente');
      } else {
        await api.post('/crm/native/leads', payload);
        toast.success('Lead creado correctamente');
      }
      
      onSaved();
    } catch (err) {
      console.error('Error saving lead:', err);
      toast.error(err.response?.data?.detail || 'Error al guardar el lead');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between sticky top-0 bg-white z-10 border-b">
          <CardTitle className="flex items-center gap-2">
            <UserPlus className="h-5 w-5" />
            {lead ? 'Editar Lead' : 'Nuevo Lead'}
          </CardTitle>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </CardHeader>
        <CardContent className="pt-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Información de Contacto */}
            <div className="space-y-4">
              <h3 className="font-medium text-sm text-gray-500 uppercase tracking-wide">
                Información de Contacto
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="nombre_contacto">Nombre *</Label>
                  <Input
                    id="nombre_contacto"
                    value={formData.nombre_contacto}
                    onChange={(e) => handleChange('nombre_contacto', e.target.value)}
                    placeholder="Nombre"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="apellido_paterno">Apellido Paterno</Label>
                  <Input
                    id="apellido_paterno"
                    value={formData.apellido_paterno}
                    onChange={(e) => handleChange('apellido_paterno', e.target.value)}
                    placeholder="Apellido paterno"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="apellido_materno">Apellido Materno</Label>
                  <Input
                    id="apellido_materno"
                    value={formData.apellido_materno}
                    onChange={(e) => handleChange('apellido_materno', e.target.value)}
                    placeholder="Apellido materno"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => handleChange('email', e.target.value)}
                    placeholder="email@empresa.com"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="puesto">Puesto</Label>
                  <Input
                    id="puesto"
                    value={formData.puesto}
                    onChange={(e) => handleChange('puesto', e.target.value)}
                    placeholder="Gerente de TI"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="telefono">Teléfono</Label>
                  <Input
                    id="telefono"
                    value={formData.telefono}
                    onChange={(e) => handleChange('telefono', e.target.value)}
                    placeholder="55 1234 5678"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="telefono_movil">Teléfono Móvil</Label>
                  <Input
                    id="telefono_movil"
                    value={formData.telefono_movil}
                    onChange={(e) => handleChange('telefono_movil', e.target.value)}
                    placeholder="55 8765 4321"
                  />
                </div>
              </div>
            </div>

            {/* Información de Empresa */}
            <div className="space-y-4">
              <h3 className="font-medium text-sm text-gray-500 uppercase tracking-wide">
                Información de Empresa
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="nombre_empresa">Nombre de Empresa</Label>
                  <Input
                    id="nombre_empresa"
                    value={formData.nombre_empresa}
                    onChange={(e) => handleChange('nombre_empresa', e.target.value)}
                    placeholder="Acme Corp"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="presupuesto">Presupuesto Estimado</Label>
                  <Input
                    id="presupuesto"
                    type="number"
                    value={formData.presupuesto}
                    onChange={(e) => handleChange('presupuesto', e.target.value)}
                    placeholder="100000"
                  />
                </div>
              </div>
            </div>

            {/* Clasificación */}
            <div className="space-y-4">
              <h3 className="font-medium text-sm text-gray-500 uppercase tracking-wide">
                Clasificación
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Origen del Lead</Label>
                  <Select 
                    value={formData.origen_lead_id} 
                    onValueChange={(value) => handleChange('origen_lead_id', value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccionar origen" />
                    </SelectTrigger>
                    <SelectContent>
                      {catalogos.origenes_lead?.map((item) => (
                        <SelectItem key={item.id} value={item.id.toString()}>
                          {item.nombre}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Prioridad</Label>
                  <Select 
                    value={formData.prioridad_id} 
                    onValueChange={(value) => handleChange('prioridad_id', value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccionar prioridad" />
                    </SelectTrigger>
                    <SelectContent>
                      {catalogos.prioridades?.map((item) => (
                        <SelectItem key={item.id} value={item.id.toString()}>
                          {item.nombre}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            {/* Descripción */}
            <div className="space-y-2">
              <Label htmlFor="descripcion">Descripción / Notas</Label>
              <Textarea
                id="descripcion"
                value={formData.descripcion}
                onChange={(e) => handleChange('descripcion', e.target.value)}
                placeholder="Información adicional sobre el lead..."
                rows={3}
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
                    {lead ? 'Actualizar' : 'Crear Lead'}
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
