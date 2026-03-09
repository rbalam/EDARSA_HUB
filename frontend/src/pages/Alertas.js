import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Plus, Trash2, Bell, BellOff } from 'lucide-react';
import { toast } from 'sonner';

const Alertas = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    product_codes: '',
    categoria: '',
    familia: '',
    threshold_percentage: 5.0,
    notify_emails: ''
  });

  useEffect(() => {
    loadAlerts();
  }, []);

  const loadAlerts = async () => {
    try {
      const response = await api.get('/alerts');
      setAlerts(response.data);
    } catch (error) {
      toast.error('Error al cargar alertas');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const alertData = {
      name: formData.name,
      product_codes: formData.product_codes ? formData.product_codes.split(',').map(s => s.trim()) : [],
      categoria: formData.categoria || null,
      familia: formData.familia || null,
      threshold_percentage: parseFloat(formData.threshold_percentage),
      notify_emails: formData.notify_emails.split(',').map(s => s.trim())
    };

    try {
      await api.post('/alerts', alertData);
      toast.success('Alerta creada exitosamente');
      setDialogOpen(false);
      resetForm();
      loadAlerts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear alerta');
    }
  };

  const handleDelete = async (alertId) => {
    if (!window.confirm('¿Estás seguro de eliminar esta alerta?')) return;
    
    try {
      await api.delete(`/alerts/${alertId}`);
      toast.success('Alerta eliminada');
      loadAlerts();
    } catch (error) {
      toast.error('Error al eliminar alerta');
    }
  };

  const handleToggleActive = async (alertId, currentStatus) => {
    try {
      await api.put(`/alerts/${alertId}`, { active: !currentStatus });
      toast.success('Alerta actualizada');
      loadAlerts();
    } catch (error) {
      toast.error('Error al actualizar alerta');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      product_codes: '',
      categoria: '',
      familia: '',
      threshold_percentage: 5.0,
      notify_emails: ''
    });
  };

  return (
    <div className="space-y-6" data-testid="alertas-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-zinc-900" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Alertas
          </h1>
          <p className="text-zinc-600 mt-1">Configura notificaciones automáticas para diferencias de inventario</p>
        </div>
        <Button 
          onClick={() => setDialogOpen(true)}
          className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800"
          data-testid="add-alert-button"
        >
          <Plus className="h-4 w-4 mr-2" />
          Nueva Alerta
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-zinc-900"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {alerts.map((alert) => (
            <Card key={alert.id} className="border border-zinc-200 shadow-sm hover:border-zinc-300 transition-colors" data-testid="alert-card">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`${alert.active ? 'bg-green-50' : 'bg-zinc-100'} p-2 rounded-lg`}>
                      {alert.active ? (
                        <Bell className="h-5 w-5 text-green-600" />
                      ) : (
                        <BellOff className="h-5 w-5 text-zinc-400" />
                      )}
                    </div>
                    <div>
                      <CardTitle className="text-lg font-semibold">{alert.name}</CardTitle>
                      <p className="text-xs text-zinc-500 mt-1">
                        {alert.active ? 'Activa' : 'Inactiva'}
                      </p>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-zinc-600">Umbral:</span>
                    <span className="font-data font-semibold text-zinc-900">{alert.threshold_percentage}%</span>
                  </div>
                  
                  {alert.categoria && (
                    <div className="flex justify-between">
                      <span className="text-zinc-600">Categoría:</span>
                      <span className="font-mono text-zinc-900">{alert.categoria}</span>
                    </div>
                  )}
                  
                  {alert.familia && (
                    <div className="flex justify-between">
                      <span className="text-zinc-600">Familia:</span>
                      <span className="font-mono text-zinc-900">{alert.familia}</span>
                    </div>
                  )}
                  
                  {alert.product_codes && alert.product_codes.length > 0 && (
                    <div>
                      <span className="text-zinc-600">Productos:</span>
                      <p className="font-mono text-xs text-zinc-900 mt-1">
                        {alert.product_codes.join(', ')}
                      </p>
                    </div>
                  )}
                  
                  <div>
                    <span className="text-zinc-600">Notificar a:</span>
                    <p className="text-xs text-zinc-900 mt-1">
                      {alert.notify_emails.join(', ')}
                    </p>
                  </div>
                </div>
                
                <div className="flex gap-2 mt-4">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="flex-1"
                    onClick={() => handleToggleActive(alert.id, alert.active)}
                    data-testid="toggle-alert-button"
                  >
                    {alert.active ? 'Desactivar' : 'Activar'}
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => handleDelete(alert.id)}
                    data-testid="delete-alert-button"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Add Alert Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Nueva Alerta</DialogTitle>
            <DialogDescription>Configura una alerta para notificaciones automáticas</DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Nombre de la Alerta</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                required
                placeholder="Alerta de diferencias altas"
                data-testid="alert-name-input"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="threshold">Umbral de Diferencia (%)</Label>
              <Input
                id="threshold"
                type="number"
                step="0.1"
                value={formData.threshold_percentage}
                onChange={(e) => setFormData({...formData, threshold_percentage: e.target.value})}
                required
                data-testid="alert-threshold-input"
              />
              <p className="text-xs text-zinc-500">Notificar cuando la diferencia supere este porcentaje</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="categoria">Categoría (opcional)</Label>
                <Input
                  id="categoria"
                  value={formData.categoria}
                  onChange={(e) => setFormData({...formData, categoria: e.target.value})}
                  placeholder="Alimentos"
                  data-testid="alert-categoria-input"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="familia">Familia (opcional)</Label>
                <Input
                  id="familia"
                  value={formData.familia}
                  onChange={(e) => setFormData({...formData, familia: e.target.value})}
                  placeholder="Carnes"
                  data-testid="alert-familia-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="products">Códigos de Productos (opcional)</Label>
              <Input
                id="products"
                value={formData.product_codes}
                onChange={(e) => setFormData({...formData, product_codes: e.target.value})}
                placeholder="0001, 0002, 0003 (separados por coma)"
                data-testid="alert-products-input"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="emails">Correos de Notificación</Label>
              <Input
                id="emails"
                type="text"
                value={formData.notify_emails}
                onChange={(e) => setFormData({...formData, notify_emails: e.target.value})}
                required
                placeholder="usuario1@empresa.com, usuario2@empresa.com"
                data-testid="alert-emails-input"
              />
              <p className="text-xs text-zinc-500">Separa múltiples correos con coma</p>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800" data-testid="submit-alert-button">
                Crear Alerta
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Alertas;