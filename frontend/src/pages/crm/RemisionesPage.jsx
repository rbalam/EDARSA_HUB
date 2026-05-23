import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Plus, Truck, Check, DollarSign, Calendar, MapPin, User } from 'lucide-react';
import api from '@/lib/api';
import { toast } from 'sonner';

const RemisionesPage = () => {
  const [remisiones, setRemisiones] = useState([]);
  const [clientes, setClientes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    cliente_id: '',
    direccion_entrega: '',
    observaciones: '',
    subtotal: '',
    impuestos_total: '',
    total: ''
  });

  useEffect(() => {
    loadRemisiones();
    loadClientes();
  }, []);

  const loadRemisiones = async () => {
    try {
      setLoading(true);
      const response = await api.get('/crm/remisiones-venta', { params: { limit: 100 } });
      setRemisiones(response.data.remisiones || []);
    } catch (error) {
      toast.error('Error cargando remisiones');
    } finally {
      setLoading(false);
    }
  };

  const loadClientes = async () => {
    try {
      const response = await api.get('/crm/clientes', { params: { limit: 500 } });
      setClientes(response.data.clientes || []);
    } catch (error) {
      console.error('Error cargando clientes:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        empresa_id: '00000000-0000-0000-0000-000000000001',
        cliente_id: parseInt(formData.cliente_id),
        direccion_entrega: formData.direccion_entrega,
        observaciones: formData.observaciones,
        subtotal: parseFloat(formData.subtotal) || 0,
        impuestos_total: parseFloat(formData.impuestos_total) || 0,
        total: parseFloat(formData.total) || 0
      };
      await api.post('/crm/remisiones-venta', payload);
      toast.success('Remisión creada exitosamente');
      setShowForm(false);
      setFormData({
        cliente_id: '',
        direccion_entrega: '',
        observaciones: '',
        subtotal: '',
        impuestos_total: '',
        total: ''
      });
      loadRemisiones();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error creando remisión');
    }
  };

  const handleEntregar = async (remisionId) => {
    const entregadoA = prompt('Nombre de quien entrega:');
    if (!entregadoA) return;
    const recibidoPor = prompt('Nombre de quien recibe:');
    if (!recibidoPor) return;

    try {
      await api.post(`/crm/remisiones-venta/${remisionId}/entregar`, {
        entregado_a: entregadoA,
        recibido_por: recibidoPor
      });
      toast.success('Entrega registrada exitosamente');
      loadRemisiones();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error registrando entrega');
    }
  };

  const getStatusBadge = (estatusId) => {
    const config = {
      1: { label: 'PENDIENTE', color: 'bg-yellow-100 text-yellow-800' },
      2: { label: 'ENTREGADA', color: 'bg-green-100 text-green-800' },
      3: { label: 'CANCELADA', color: 'bg-red-100 text-red-800' }
    };
    const cfg = config[estatusId] || config[1];
    return <Badge className={cfg.color}>{cfg.label}</Badge>;
  };

  const calcularTotal = () => {
    const subtotal = parseFloat(formData.subtotal) || 0;
    const impuesto = subtotal * 0.16;
    setFormData({
      ...formData,
      impuestos_total: impuesto.toFixed(2),
      total: (subtotal + impuesto).toFixed(2)
    });
  };

  return (
    <div className="p-6 space-y-6" data-testid="remisiones-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Remisiones de Venta</h1>
          <p className="text-gray-500">Control de entregas y remisiones</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)} data-testid="nueva-remision-btn">
          <Plus className="w-4 h-4 mr-2" />
          Nueva Remisión
        </Button>
      </div>

      {/* Formulario */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Nueva Remisión</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Cliente *</label>
                <select
                  className="w-full border rounded-md p-2"
                  value={formData.cliente_id}
                  onChange={(e) => setFormData({ ...formData, cliente_id: e.target.value })}
                  required
                >
                  <option value="">Seleccionar cliente</option>
                  {clientes.map((c) => (
                    <option key={c.ClienteID} value={c.ClienteID}>
                      {c.RazonSocial || c.NombreComercial}
                    </option>
                  ))}
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1">Dirección de Entrega</label>
                <Input
                  value={formData.direccion_entrega}
                  onChange={(e) => setFormData({ ...formData, direccion_entrega: e.target.value })}
                  placeholder="Dirección completa"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Subtotal</label>
                <Input
                  type="number"
                  step="0.01"
                  value={formData.subtotal}
                  onChange={(e) => setFormData({ ...formData, subtotal: e.target.value })}
                  onBlur={calcularTotal}
                  placeholder="$0.00"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">IVA (16%)</label>
                <Input
                  type="number"
                  step="0.01"
                  value={formData.impuestos_total}
                  onChange={(e) => setFormData({ ...formData, impuestos_total: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Total</label>
                <Input
                  type="number"
                  step="0.01"
                  value={formData.total}
                  onChange={(e) => setFormData({ ...formData, total: e.target.value })}
                />
              </div>
              <div className="md:col-span-2 lg:col-span-3">
                <label className="block text-sm font-medium mb-1">Observaciones</label>
                <textarea
                  className="w-full border rounded-md p-2"
                  rows={2}
                  value={formData.observaciones}
                  onChange={(e) => setFormData({ ...formData, observaciones: e.target.value })}
                />
              </div>
              <div className="md:col-span-2 lg:col-span-3 flex gap-2 justify-end">
                <Button type="button" variant="outline" onClick={() => setShowForm(false)}>
                  Cancelar
                </Button>
                <Button type="submit">
                  Crear Remisión
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Lista */}
      {loading ? (
        <div className="text-center py-8">Cargando...</div>
      ) : remisiones.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Truck className="w-12 h-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">No hay remisiones</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {remisiones.map((rem) => (
            <Card key={rem.RemisionID} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="font-mono text-sm font-semibold text-purple-600">{rem.FolioRemision}</span>
                      {getStatusBadge(rem.EstatusRemisionID)}
                      {rem.PedidoID && (
                        <span className="text-xs text-gray-500">
                          (De pedido #{rem.PedidoID})
                        </span>
                      )}
                    </div>
                    <h3 className="font-semibold text-gray-900">{rem.ClienteRazonSocial}</h3>
                    <div className="flex flex-wrap items-center gap-4 mt-2 text-sm text-gray-500">
                      <div className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        {new Date(rem.FechaRemision).toLocaleDateString('es-MX')}
                      </div>
                      {rem.DireccionEntrega && (
                        <div className="flex items-center gap-1">
                          <MapPin className="w-4 h-4" />
                          {rem.DireccionEntrega.substring(0, 40)}...
                        </div>
                      )}
                      <div className="flex items-center gap-1 font-semibold text-gray-900">
                        <DollarSign className="w-4 h-4" />
                        ${rem.Total?.toLocaleString('es-MX', { minimumFractionDigits: 2 })}
                      </div>
                    </div>
                    {rem.EstatusRemisionID === 2 && (
                      <div className="mt-2 text-sm text-green-600">
                        <div className="flex items-center gap-1">
                          <Check className="w-4 h-4" />
                          Entregado por: {rem.EntregadoA} | Recibido por: {rem.RecibidoPor}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          Fecha entrega: {rem.FechaEntregaReal ? new Date(rem.FechaEntregaReal).toLocaleString('es-MX') : '-'}
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2">
                    {rem.EstatusRemisionID === 1 && (
                      <Button size="sm" onClick={() => handleEntregar(rem.RemisionID)}>
                        <Truck className="w-4 h-4 mr-1" />
                        Registrar Entrega
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default RemisionesPage;
