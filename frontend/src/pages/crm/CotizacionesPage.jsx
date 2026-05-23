import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Plus, Search, FileText, Send, Check, DollarSign, Calendar, User } from 'lucide-react';
import api from '@/lib/api';
import { toast } from 'sonner';

const CotizacionesPage = () => {
  const [cotizaciones, setCotizaciones] = useState([]);
  const [clientes, setClientes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    cliente_id: '',
    atencion_a: '',
    email_cliente: '',
    observaciones: '',
    subtotal: '',
    impuesto_total: '',
    total: ''
  });

  useEffect(() => {
    loadCotizaciones();
    loadClientes();
  }, []);

  const loadCotizaciones = async () => {
    try {
      setLoading(true);
      const response = await api.get('/crm/cotizaciones', { params: { limit: 100 } });
      setCotizaciones(response.data.cotizaciones || []);
    } catch (error) {
      toast.error('Error cargando cotizaciones');
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
      await api.post('/crm/cotizaciones', payload);
      toast.success('Cotización creada exitosamente');
      setShowForm(false);
      setFormData({
        cliente_id: '',
        atencion_a: '',
        email_cliente: '',
        observaciones: '',
        subtotal: '',
        impuesto_total: '',
        total: ''
      });
      loadCotizaciones();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error creando cotización');
    }
  };

  const handleEnviar = async (cotizacionId) => {
    try {
      await api.post(`/crm/cotizaciones/${cotizacionId}/enviar`);
      toast.success('Cotización enviada');
      loadCotizaciones();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error enviando cotización');
    }
  };

  const handleAprobar = async (cotizacionId) => {
    try {
      await api.post(`/crm/cotizaciones/${cotizacionId}/aprobar`);
      toast.success('Cotización aprobada');
      loadCotizaciones();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error aprobando cotización');
    }
  };

  const getStatusBadge = (estatus) => {
    const config = {
      'BORRADOR': 'bg-gray-100 text-gray-800',
      'ENVIADA': 'bg-blue-100 text-blue-800',
      'APROBADA': 'bg-green-100 text-green-800',
      'RECHAZADA': 'bg-red-100 text-red-800',
      'VENCIDA': 'bg-yellow-100 text-yellow-800'
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
    <div className="p-6 space-y-6" data-testid="cotizaciones-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Cotizaciones</h1>
          <p className="text-gray-500">Gestión de cotizaciones comerciales</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)} data-testid="nueva-cotizacion-btn">
          <Plus className="w-4 h-4 mr-2" />
          Nueva Cotización
        </Button>
      </div>

      {/* Formulario */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Nueva Cotización</CardTitle>
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
                  placeholder="Nombre del contacto"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Email</label>
                <Input
                  type="email"
                  value={formData.email_cliente}
                  onChange={(e) => setFormData({ ...formData, email_cliente: e.target.value })}
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
                  placeholder="$0.00"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Total</label>
                <Input
                  type="number"
                  step="0.01"
                  value={formData.total}
                  onChange={(e) => setFormData({ ...formData, total: e.target.value })}
                  placeholder="$0.00"
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
                  Crear Cotización
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Lista */}
      {loading ? (
        <div className="text-center py-8">Cargando...</div>
      ) : cotizaciones.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="w-12 h-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">No hay cotizaciones</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {cotizaciones.map((cot) => (
            <Card key={cot.CotizacionID} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="font-mono text-sm font-semibold text-blue-600">{cot.FolioCotizacion}</span>
                      {getStatusBadge(cot.EstatusComercial)}
                    </div>
                    <h3 className="font-semibold text-gray-900">{cot.ClienteRazonSocial}</h3>
                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                      {cot.AtencionA && (
                        <div className="flex items-center gap-1">
                          <User className="w-4 h-4" />
                          {cot.AtencionA}
                        </div>
                      )}
                      <div className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        {new Date(cot.FechaCotizacion).toLocaleDateString('es-MX')}
                      </div>
                      <div className="flex items-center gap-1 font-semibold text-gray-900">
                        <DollarSign className="w-4 h-4" />
                        ${cot.Total?.toLocaleString('es-MX', { minimumFractionDigits: 2 })}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {(!cot.EstatusComercial || cot.EstatusComercial === 'BORRADOR') && (
                      <Button size="sm" onClick={() => handleEnviar(cot.CotizacionID)}>
                        <Send className="w-4 h-4 mr-1" />
                        Enviar
                      </Button>
                    )}
                    {cot.EstatusComercial === 'ENVIADA' && (
                      <Button size="sm" onClick={() => handleAprobar(cot.CotizacionID)}>
                        <Check className="w-4 h-4 mr-1" />
                        Aprobar
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

export default CotizacionesPage;
