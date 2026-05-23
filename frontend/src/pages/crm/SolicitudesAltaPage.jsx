import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Plus, Search, FileText, Send, Check, X, Clock, Building2 } from 'lucide-react';
import api from '@/lib/api';
import { toast } from 'sonner';

const SolicitudesAltaPage = () => {
  const [solicitudes, setSolicitudes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    nombre_comercial: '',
    razon_social: '',
    rfc: '',
    email_facturacion: '',
    telefono_facturacion: '',
    calle: '',
    numero_exterior: '',
    colonia: '',
    ciudad: '',
    estado: '',
    codigo_postal: '',
    contacto_principal_nombre: '',
    contacto_principal_email: '',
    requiere_credito: false,
    limite_credito_solicitado: '',
    dias_credito_solicitados: ''
  });

  useEffect(() => {
    loadSolicitudes();
  }, []);

  const loadSolicitudes = async () => {
    try {
      setLoading(true);
      const response = await api.get('/crm/clientes/solicitudes', { params: { limit: 100 } });
      setSolicitudes(response.data.solicitudes || []);
    } catch (error) {
      toast.error('Error cargando solicitudes');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        empresa_id: '00000000-0000-0000-0000-000000000001',
        limite_credito_solicitado: formData.limite_credito_solicitado ? parseFloat(formData.limite_credito_solicitado) : null,
        dias_credito_solicitados: formData.dias_credito_solicitados ? parseInt(formData.dias_credito_solicitados) : null
      };
      await api.post('/crm/clientes/solicitudes', payload);
      toast.success('Solicitud creada exitosamente');
      setShowForm(false);
      setFormData({
        nombre_comercial: '',
        razon_social: '',
        rfc: '',
        email_facturacion: '',
        telefono_facturacion: '',
        calle: '',
        numero_exterior: '',
        colonia: '',
        ciudad: '',
        estado: '',
        codigo_postal: '',
        contacto_principal_nombre: '',
        contacto_principal_email: '',
        requiere_credito: false,
        limite_credito_solicitado: '',
        dias_credito_solicitados: ''
      });
      loadSolicitudes();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error creando solicitud');
    }
  };

  const handleEnviar = async (solicitudId) => {
    try {
      await api.post(`/crm/clientes/solicitudes/${solicitudId}/enviar`);
      toast.success('Solicitud enviada para revisión');
      loadSolicitudes();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error enviando solicitud');
    }
  };

  const handleAutorizar = async (solicitudId) => {
    try {
      await api.post(`/crm/clientes/solicitudes/${solicitudId}/autorizar`, { comentarios: 'Aprobada' });
      toast.success('Solicitud autorizada - Cliente creado');
      loadSolicitudes();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error autorizando solicitud');
    }
  };

  const handleRechazar = async (solicitudId) => {
    const motivo = prompt('Ingrese el motivo del rechazo:');
    if (!motivo) return;
    try {
      await api.post(`/crm/clientes/solicitudes/${solicitudId}/rechazar`, { motivo });
      toast.success('Solicitud rechazada');
      loadSolicitudes();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error rechazando solicitud');
    }
  };

  const getStatusBadge = (estatus) => {
    const config = {
      'BORRADOR': { color: 'bg-gray-100 text-gray-800', icon: Clock },
      'ENVIADA': { color: 'bg-blue-100 text-blue-800', icon: Send },
      'EN_REVISION': { color: 'bg-yellow-100 text-yellow-800', icon: Clock },
      'APROBADA': { color: 'bg-green-100 text-green-800', icon: Check },
      'RECHAZADA': { color: 'bg-red-100 text-red-800', icon: X }
    };
    const cfg = config[estatus] || config['BORRADOR'];
    const Icon = cfg.icon;
    return (
      <Badge className={`${cfg.color} flex items-center gap-1`}>
        <Icon className="w-3 h-3" />
        {estatus}
      </Badge>
    );
  };

  return (
    <div className="p-6 space-y-6" data-testid="solicitudes-alta-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Solicitudes de Alta</h1>
          <p className="text-gray-500">Gestión de solicitudes para dar de alta nuevos clientes</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)} data-testid="nueva-solicitud-btn">
          <Plus className="w-4 h-4 mr-2" />
          Nueva Solicitud
        </Button>
      </div>

      {/* Formulario */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Nueva Solicitud de Alta de Cliente</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Datos Fiscales */}
              <div>
                <h3 className="font-medium text-gray-900 mb-3">Datos Fiscales</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Nombre Comercial *</label>
                    <Input
                      value={formData.nombre_comercial}
                      onChange={(e) => setFormData({ ...formData, nombre_comercial: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Razón Social *</label>
                    <Input
                      value={formData.razon_social}
                      onChange={(e) => setFormData({ ...formData, razon_social: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">RFC *</label>
                    <Input
                      value={formData.rfc}
                      onChange={(e) => setFormData({ ...formData, rfc: e.target.value.toUpperCase() })}
                      required
                      maxLength={13}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Email Facturación</label>
                    <Input
                      type="email"
                      value={formData.email_facturacion}
                      onChange={(e) => setFormData({ ...formData, email_facturacion: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Teléfono</label>
                    <Input
                      value={formData.telefono_facturacion}
                      onChange={(e) => setFormData({ ...formData, telefono_facturacion: e.target.value })}
                    />
                  </div>
                </div>
              </div>

              {/* Dirección */}
              <div>
                <h3 className="font-medium text-gray-900 mb-3">Dirección</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium mb-1">Calle</label>
                    <Input
                      value={formData.calle}
                      onChange={(e) => setFormData({ ...formData, calle: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">No. Exterior</label>
                    <Input
                      value={formData.numero_exterior}
                      onChange={(e) => setFormData({ ...formData, numero_exterior: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Colonia</label>
                    <Input
                      value={formData.colonia}
                      onChange={(e) => setFormData({ ...formData, colonia: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Ciudad</label>
                    <Input
                      value={formData.ciudad}
                      onChange={(e) => setFormData({ ...formData, ciudad: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Estado</label>
                    <Input
                      value={formData.estado}
                      onChange={(e) => setFormData({ ...formData, estado: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">C.P.</label>
                    <Input
                      value={formData.codigo_postal}
                      onChange={(e) => setFormData({ ...formData, codigo_postal: e.target.value })}
                      maxLength={5}
                    />
                  </div>
                </div>
              </div>

              {/* Contacto */}
              <div>
                <h3 className="font-medium text-gray-900 mb-3">Contacto Principal</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Nombre</label>
                    <Input
                      value={formData.contacto_principal_nombre}
                      onChange={(e) => setFormData({ ...formData, contacto_principal_nombre: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Email</label>
                    <Input
                      type="email"
                      value={formData.contacto_principal_email}
                      onChange={(e) => setFormData({ ...formData, contacto_principal_email: e.target.value })}
                    />
                  </div>
                </div>
              </div>

              {/* Crédito */}
              <div>
                <h3 className="font-medium text-gray-900 mb-3">Condiciones de Crédito</h3>
                <div className="flex items-center gap-4 mb-4">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={formData.requiere_credito}
                      onChange={(e) => setFormData({ ...formData, requiere_credito: e.target.checked })}
                      className="w-4 h-4"
                    />
                    <span className="text-sm">Requiere línea de crédito</span>
                  </label>
                </div>
                {formData.requiere_credito && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Límite Solicitado</label>
                      <Input
                        type="number"
                        value={formData.limite_credito_solicitado}
                        onChange={(e) => setFormData({ ...formData, limite_credito_solicitado: e.target.value })}
                        placeholder="$0.00"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Días de Crédito</label>
                      <Input
                        type="number"
                        value={formData.dias_credito_solicitados}
                        onChange={(e) => setFormData({ ...formData, dias_credito_solicitados: e.target.value })}
                        placeholder="30"
                      />
                    </div>
                  </div>
                )}
              </div>

              <div className="flex gap-2 justify-end">
                <Button type="button" variant="outline" onClick={() => setShowForm(false)}>
                  Cancelar
                </Button>
                <Button type="submit">
                  Crear Solicitud
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Lista de solicitudes */}
      {loading ? (
        <div className="text-center py-8">Cargando...</div>
      ) : solicitudes.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="w-12 h-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">No hay solicitudes de alta</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {solicitudes.map((sol) => (
            <Card key={sol.SolicitudID} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="font-mono text-sm text-gray-500">{sol.FolioSolicitud}</span>
                      {getStatusBadge(sol.EstatusSolicitud)}
                    </div>
                    <h3 className="font-semibold text-gray-900">{sol.RazonSocial}</h3>
                    <p className="text-sm text-gray-600">{sol.NombreComercial}</p>
                    <p className="text-sm text-gray-500 mt-1">RFC: {sol.RFC}</p>
                    {sol.RequiereCredito && (
                      <p className="text-sm text-blue-600 mt-1">
                        Crédito solicitado: ${sol.LimiteCreditoSolicitado?.toLocaleString()} / {sol.DiasCreditoSolicitados} días
                      </p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    {sol.EstatusSolicitud === 'BORRADOR' && (
                      <Button size="sm" onClick={() => handleEnviar(sol.SolicitudID)}>
                        <Send className="w-4 h-4 mr-1" />
                        Enviar
                      </Button>
                    )}
                    {(sol.EstatusSolicitud === 'ENVIADA' || sol.EstatusSolicitud === 'EN_REVISION') && (
                      <>
                        <Button size="sm" variant="outline" onClick={() => handleRechazar(sol.SolicitudID)}>
                          <X className="w-4 h-4 mr-1" />
                          Rechazar
                        </Button>
                        <Button size="sm" onClick={() => handleAutorizar(sol.SolicitudID)}>
                          <Check className="w-4 h-4 mr-1" />
                          Autorizar
                        </Button>
                      </>
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

export default SolicitudesAltaPage;
