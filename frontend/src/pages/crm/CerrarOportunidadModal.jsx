import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { 
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue 
} from '@/components/ui/select';
import { X, Trophy, XCircle, Loader2, DollarSign } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/lib/api';

export default function CerrarOportunidadModal({ oportunidad, onClose, onClosed }) {
  const [loading, setLoading] = useState(false);
  const [esGanada, setEsGanada] = useState(null);
  const [catalogos, setCatalogos] = useState({});
  const [formData, setFormData] = useState({
    motivo_id: '',
    razon_texto: '',
    monto_final: oportunidad?.monto_estimado || '',
  });

  useEffect(() => {
    loadCatalogos();
  }, []);

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
    
    if (esGanada === null) {
      toast.error('Selecciona si la oportunidad fue ganada o perdida');
      return;
    }

    setLoading(true);
    try {
      await api.post(`/crm/native/oportunidades/${oportunidad.oportunidad_id}/cerrar`, {
        es_ganada: esGanada,
        motivo_id: formData.motivo_id ? parseInt(formData.motivo_id) : null,
        razon_texto: formData.razon_texto || null,
        monto_final: formData.monto_final ? parseFloat(formData.monto_final) : null,
      });
      
      toast.success(`Oportunidad cerrada como ${esGanada ? 'GANADA' : 'PERDIDA'}`);
      onClosed();
    } catch (err) {
      console.error('Error closing oportunidad:', err);
      toast.error(err.response?.data?.detail || 'Error al cerrar la oportunidad');
    } finally {
      setLoading(false);
    }
  };

  const motivos = esGanada 
    ? catalogos.motivos_ganada || []
    : catalogos.motivos_perdida || [];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-lg">
        <CardHeader className="flex flex-row items-center justify-between border-b">
          <CardTitle className="text-lg">Cerrar Oportunidad</CardTitle>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </CardHeader>
        <CardContent className="pt-6">
          {/* Info de la oportunidad */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <p className="font-medium">{oportunidad.nombre_oportunidad}</p>
            <p className="text-sm text-gray-500">{oportunidad.folio_oportunidad}</p>
            <p className="text-lg font-semibold text-green-600 mt-2">
              ${(oportunidad.monto_estimado || 0).toLocaleString('es-MX')} MXN
            </p>
          </div>

          {/* Selección Ganada/Perdida */}
          {esGanada === null ? (
            <div className="space-y-4">
              <p className="text-center text-gray-600 mb-4">
                ¿Cómo se cierra esta oportunidad?
              </p>
              <div className="grid grid-cols-2 gap-4">
                <Button
                  type="button"
                  variant="outline"
                  className="h-24 flex flex-col items-center justify-center gap-2 hover:bg-green-50 hover:border-green-500 hover:text-green-700"
                  onClick={() => setEsGanada(true)}
                >
                  <Trophy className="h-8 w-8 text-green-600" />
                  <span className="font-semibold">GANADA</span>
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  className="h-24 flex flex-col items-center justify-center gap-2 hover:bg-red-50 hover:border-red-500 hover:text-red-700"
                  onClick={() => setEsGanada(false)}
                >
                  <XCircle className="h-8 w-8 text-red-600" />
                  <span className="font-semibold">PERDIDA</span>
                </Button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Header de estado */}
              <div className={`flex items-center gap-2 p-3 rounded-lg ${
                esGanada ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
              }`}>
                {esGanada ? (
                  <Trophy className="h-5 w-5" />
                ) : (
                  <XCircle className="h-5 w-5" />
                )}
                <span className="font-semibold">
                  {esGanada ? 'Cierre GANADO' : 'Cierre PERDIDO'}
                </span>
                <Button 
                  type="button" 
                  variant="ghost" 
                  size="sm" 
                  className="ml-auto"
                  onClick={() => setEsGanada(null)}
                >
                  Cambiar
                </Button>
              </div>

              {/* Monto final (solo para ganadas) */}
              {esGanada && (
                <div className="space-y-2">
                  <Label>Monto Final</Label>
                  <div className="relative">
                    <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      type="number"
                      value={formData.monto_final}
                      onChange={(e) => handleChange('monto_final', e.target.value)}
                      placeholder="Monto de cierre"
                      className="pl-10"
                    />
                  </div>
                </div>
              )}

              {/* Motivo */}
              <div className="space-y-2">
                <Label>{esGanada ? 'Motivo de Éxito' : 'Motivo de Pérdida'}</Label>
                <Select 
                  value={formData.motivo_id} 
                  onValueChange={(value) => handleChange('motivo_id', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar motivo (opcional)" />
                  </SelectTrigger>
                  <SelectContent>
                    {motivos.map((item) => (
                      <SelectItem key={item.id} value={item.id.toString()}>
                        {item.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Razón / Notas */}
              <div className="space-y-2">
                <Label>{esGanada ? 'Notas de Cierre' : 'Razón de Pérdida'}</Label>
                <Textarea
                  value={formData.razon_texto}
                  onChange={(e) => handleChange('razon_texto', e.target.value)}
                  placeholder={esGanada 
                    ? 'Notas sobre el cierre exitoso...' 
                    : '¿Por qué se perdió esta oportunidad?'
                  }
                  rows={3}
                />
              </div>

              {/* Botones */}
              <div className="flex justify-end gap-3 pt-4 border-t">
                <Button type="button" variant="outline" onClick={onClose}>
                  Cancelar
                </Button>
                <Button 
                  type="submit" 
                  disabled={loading}
                  className={esGanada ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Procesando...
                    </>
                  ) : (
                    <>
                      {esGanada ? <Trophy className="h-4 w-4 mr-2" /> : <XCircle className="h-4 w-4 mr-2" />}
                      Cerrar como {esGanada ? 'Ganada' : 'Perdida'}
                    </>
                  )}
                </Button>
              </div>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
