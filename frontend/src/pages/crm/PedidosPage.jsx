import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Plus, FileText, Check, DollarSign, Calendar, User, Package } from 'lucide-react';
import api from '@/lib/api';
import { toast } from 'sonner';

const PedidosPage = () => {
  const [pedidos, setPedidos] = useState([]);
  const [clientes, setClientes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    cliente_id: '',
    atencion_a: '',
    observaciones: '',
    instrucciones_entrega: '',
    subtotal: '',
    impuesto_total: '',
    total: ''
  });

  useEffect(() => {
    loadPedidos();
    loadClientes();
  }, []);

  const loadPedidos = async () => {
    try {
      setLoading(true);
      const response = await api.get('/crm/pedidos-venta', { params: { limit: 100 } });
      setPedidos(response.data.pedidos || []);
    } catch (error) {
      toast.error('Error cargando pedidos');
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
        ...formData,
        cliente_id: parseInt(formData.cliente_id),
        subtotal: parseFloat(formData.subtotal) || 0,
        impuesto_total: parseFloat(formData.impuesto_total) || 0,
        total: parseFloat(formData.total) || 0
      };
      await api.post('/crm/pedidos-venta', payload);
      toast.success('Pedido creado exitosamente');
      setShowForm(false);
      setFormData({
        cliente_id: '',
        atencion_a: '',
        observaciones: '',
        instrucciones_entrega: '',
        subtotal: '',
        impuesto_total: '',
        total: ''
      });
      loadPedidos();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error creando pedido');
    }
  };

  const handleConfirmar = async (pedidoId) => {
    try {
      await api.post(`/crm/pedidos-venta/${pedidoId}/confirmar`);
      toast.success('Pedido confirmado');
      loadPedidos();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error confirmando pedido');
    }
  };

  const getStatusBadge = (estatus) => {
    const config = {
      'BORRADOR': 'bg-gray-100 text-gray-800',
      'CONFIRMADO': 'bg-blue-100 text-blue-800',
      'EN_PROCESO': 'bg-yellow-100 text-yellow-800',
      'ENTREGADO': 'bg-green-100 text-green-800',
      'CANCELADO': 'bg-red-100 text-red-800'
    };
    return <Badge className={config[estatus] || 'bg-gray-100 text-gray-800'}>{estatus || 'BORRADOR'}</Badge>;
  };

  const calcularTotal = () => {
    const subtotal = parseFloat(formData.subtotal) || 0;
    const impuesto = subtotal * 0.16;
    setFormData({
      ...formData,
      impuesto_total: impuesto.toFixed(2),
      total: (subtotal + impuesto).toFixed(2)
    });
  };

  return (
    <div className="p-6 space-y-6" data-testid="pedidos-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Pedidos de Venta</h1>
          <p className="text-gray-500">Gestión de pedidos comerciales</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)} data-testid="nuevo-pedido-btn">
          <Plus className="w-4 h-4 mr-2" />
          Nuevo Pedido
        </Button>
      </div>

      {/* Formulario */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Nuevo Pedido de Venta</CardTitle>
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
              <div>
                <label className="block text-sm font-medium mb-1">Atención a</label>
                <Input
                  value={formData.atencion_a}
                  onChange={(e) => setFormData({ ...formData, atencion_a: e.target.value })}
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
                  value={formData.impuesto_total}
                  onChange={(e) => setFormData({ ...formData, impuesto_total: e.target.value })}
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
              <div>
                <label className="block text-sm font-medium mb-1">Instrucciones de Entrega</label>
                <Input
                  value={formData.instrucciones_entrega}
                  onChange={(e) => setFormData({ ...formData, instrucciones_entrega: e.target.value })}
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
                  Crear Pedido
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Lista */}
      {loading ? (
        <div className="text-center py-8">Cargando...</div>
      ) : pedidos.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Package className="w-12 h-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">No hay pedidos</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {pedidos.map((ped) => (
            <Card key={ped.PedidoID} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="font-mono text-sm font-semibold text-green-600">{ped.FolioPedido}</span>
                      {getStatusBadge(ped.EstatusComercial)}
                      {ped.CotizacionID && (
                        <span className="text-xs text-gray-500">
                          (De cotización #{ped.CotizacionID})
                        </span>
                      )}
                    </div>
                    <h3 className="font-semibold text-gray-900">{ped.ClienteRazonSocial}</h3>
                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                      {ped.AtencionA && (
                        <div className="flex items-center gap-1">
                          <User className="w-4 h-4" />
                          {ped.AtencionA}
                        </div>
                      )}
                      <div className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        {new Date(ped.FechaPedido).toLocaleDateString('es-MX')}
                      </div>
                      <div className="flex items-center gap-1 font-semibold text-gray-900">
                        <DollarSign className="w-4 h-4" />
                        ${ped.Total?.toLocaleString('es-MX', { minimumFractionDigits: 2 })}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {(!ped.EstatusComercial || ped.EstatusComercial === 'BORRADOR') && (
                      <Button size="sm" onClick={() => handleConfirmar(ped.PedidoID)}>
                        <Check className="w-4 h-4 mr-1" />
                        Confirmar
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

export default PedidosPage;
