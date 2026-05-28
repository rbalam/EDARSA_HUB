import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Plus, Search, Building2, Users, Phone, Mail, MapPin, Link2 } from 'lucide-react';
import api from '@/lib/api';
import { toast } from 'sonner';

const CuentasPage = () => {
  const [cuentas, setCuentas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    nombre_cuenta: '',
    tipo_cuenta: 'PROSPECTO',
    razon_social: '',
    rfc: '',
    contacto_principal_nombre: '',
    contacto_principal_email: '',
    contacto_principal_telefono: '',
    ciudad: '',
    estado: ''
  });

  useEffect(() => {
    loadCuentas();
  }, []);

  const loadCuentas = async () => {
    try {
      setLoading(true);
      const response = await api.get('/crm/cuentas', { 
        params: { 
          limit: 100, 
          search: search || undefined,
          source: 'vtiger'  // Leer desde Vtiger sincronizado
        } 
      });
      setCuentas(response.data.items || response.data.cuentas || []);
    } catch (error) {
      toast.error('Error cargando cuentas');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    loadCuentas();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        empresa_id: '00000000-0000-0000-0000-000000000001'
      };
      await api.post('/crm/cuentas', payload);
      toast.success('Cuenta creada exitosamente');
      setShowForm(false);
      setFormData({
        nombre_cuenta: '',
        tipo_cuenta: 'PROSPECTO',
        razon_social: '',
        rfc: '',
        contacto_principal_nombre: '',
        contacto_principal_email: '',
        contacto_principal_telefono: '',
        ciudad: '',
        estado: ''
      });
      loadCuentas();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error creando cuenta');
    }
  };

  const getTipoBadgeColor = (tipo) => {
    const colors = {
      'PROSPECTO': 'bg-blue-100 text-blue-800',
      'CLIENTE': 'bg-green-100 text-green-800',
      'LEAD': 'bg-yellow-100 text-yellow-800',
      'INACTIVA': 'bg-gray-100 text-gray-800'
    };
    return colors[tipo] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="p-6 space-y-6" data-testid="cuentas-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Cuentas CRM</h1>
          <p className="text-gray-500">Gestión de cuentas comerciales</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)} data-testid="nueva-cuenta-btn">
          <Plus className="w-4 h-4 mr-2" />
          Nueva Cuenta
        </Button>
      </div>

      {/* Formulario de nueva cuenta */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Nueva Cuenta</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Nombre de Cuenta *</label>
                <Input
                  value={formData.nombre_cuenta}
                  onChange={(e) => setFormData({ ...formData, nombre_cuenta: e.target.value })}
                  required
                  placeholder="Nombre comercial"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Tipo</label>
                <select
                  className="w-full border rounded-md p-2"
                  value={formData.tipo_cuenta}
                  onChange={(e) => setFormData({ ...formData, tipo_cuenta: e.target.value })}
                >
                  <option value="PROSPECTO">Prospecto</option>
                  <option value="LEAD">Lead</option>
                  <option value="CLIENTE">Cliente</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Razón Social</label>
                <Input
                  value={formData.razon_social}
                  onChange={(e) => setFormData({ ...formData, razon_social: e.target.value })}
                  placeholder="Razón social"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">RFC</label>
                <Input
                  value={formData.rfc}
                  onChange={(e) => setFormData({ ...formData, rfc: e.target.value.toUpperCase() })}
                  placeholder="RFC"
                  maxLength={13}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Contacto Principal</label>
                <Input
                  value={formData.contacto_principal_nombre}
                  onChange={(e) => setFormData({ ...formData, contacto_principal_nombre: e.target.value })}
                  placeholder="Nombre del contacto"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Email</label>
                <Input
                  type="email"
                  value={formData.contacto_principal_email}
                  onChange={(e) => setFormData({ ...formData, contacto_principal_email: e.target.value })}
                  placeholder="correo@empresa.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Teléfono</label>
                <Input
                  value={formData.contacto_principal_telefono}
                  onChange={(e) => setFormData({ ...formData, contacto_principal_telefono: e.target.value })}
                  placeholder="(55) 1234-5678"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Ciudad</label>
                <Input
                  value={formData.ciudad}
                  onChange={(e) => setFormData({ ...formData, ciudad: e.target.value })}
                  placeholder="Ciudad"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Estado</label>
                <Input
                  value={formData.estado}
                  onChange={(e) => setFormData({ ...formData, estado: e.target.value })}
                  placeholder="Estado"
                />
              </div>
              <div className="md:col-span-2 lg:col-span-3 flex gap-2 justify-end">
                <Button type="button" variant="outline" onClick={() => setShowForm(false)}>
                  Cancelar
                </Button>
                <Button type="submit" data-testid="guardar-cuenta-btn">
                  Guardar Cuenta
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Buscador */}
      <form onSubmit={handleSearch} className="flex gap-2">
        <Input
          placeholder="Buscar por nombre, RFC o email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-md"
        />
        <Button type="submit" variant="outline">
          <Search className="w-4 h-4" />
        </Button>
      </form>

      {/* Lista de cuentas */}
      {loading ? (
        <div className="text-center py-8">Cargando...</div>
      ) : cuentas.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Building2 className="w-12 h-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">No hay cuentas registradas</p>
            <p className="text-sm text-gray-400 mt-1">Crea tu primera cuenta para comenzar</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {cuentas.map((cuenta) => (
            <Card key={cuenta.CuentaID} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Building2 className="w-5 h-5 text-gray-400" />
                    <span className="text-xs text-gray-500">{cuenta.CodigoCuenta}</span>
                  </div>
                  <Badge className={getTipoBadgeColor(cuenta.TipoCuenta)}>
                    {cuenta.TipoCuenta}
                  </Badge>
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{cuenta.NombreCuenta}</h3>
                {cuenta.RFCSnapshot && (
                  <p className="text-sm text-gray-600 mb-2">RFC: {cuenta.RFCSnapshot}</p>
                )}
                {cuenta.ContactoPrincipalNombre && (
                  <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                    <Users className="w-4 h-4" />
                    {cuenta.ContactoPrincipalNombre}
                  </div>
                )}
                {cuenta.ContactoPrincipalEmail && (
                  <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                    <Mail className="w-4 h-4" />
                    {cuenta.ContactoPrincipalEmail}
                  </div>
                )}
                {(cuenta.Ciudad || cuenta.Estado) && (
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <MapPin className="w-4 h-4" />
                    {[cuenta.Ciudad, cuenta.Estado].filter(Boolean).join(', ')}
                  </div>
                )}
                {cuenta.ClienteID && (
                  <div className="mt-3 pt-3 border-t">
                    <div className="flex items-center gap-2 text-sm text-green-600">
                      <Link2 className="w-4 h-4" />
                      Vinculada a Cliente #{cuenta.ClienteID}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default CuentasPage;
