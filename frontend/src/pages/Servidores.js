import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Edit, Trash2, Database } from 'lucide-react';
import { toast } from 'sonner';

const Servidores = () => {
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    host: '',
    port: 1433,
    database: '',
    username: '',
    password: '',
    system_type: 'MPRO',
    sucursales: []
  });

  useEffect(() => {
    loadServers();
  }, []);

  const loadServers = async () => {
    try {
      const response = await api.get('/servers');
      setServers(response.data);
    } catch (error) {
      toast.error('Error al cargar servidores');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      await api.post('/servers', formData);
      toast.success('Servidor agregado exitosamente');
      setDialogOpen(false);
      resetForm();
      loadServers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al agregar servidor');
    }
  };

  const handleDelete = async (serverId) => {
    if (!window.confirm('¿Estás seguro de eliminar este servidor?')) return;
    
    try {
      await api.delete(`/servers/${serverId}`);
      toast.success('Servidor eliminado');
      loadServers();
    } catch (error) {
      toast.error('Error al eliminar servidor');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      host: '',
      port: 1433,
      database: '',
      username: '',
      password: '',
      system_type: 'MPRO',
      sucursales: []
    });
  };

  return (
    <div className="space-y-6" data-testid="servidores-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-zinc-900" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Servidores SQL
          </h1>
          <p className="text-zinc-600 mt-1">Gestiona las conexiones a bases de datos</p>
        </div>
        <Button 
          onClick={() => setDialogOpen(true)}
          className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800"
          data-testid="add-server-button"
        >
          <Plus className="h-4 w-4 mr-2" />
          Agregar Servidor
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-zinc-900"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {servers.map((server) => (
            <Card key={server.id} className="border border-zinc-200 shadow-sm hover:border-zinc-300 transition-colors" data-testid="server-card">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="bg-blue-50 p-2 rounded-lg">
                      <Database className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <CardTitle className="text-lg font-semibold">{server.name}</CardTitle>
                      <p className="text-xs text-zinc-500 mt-1">{server.system_type}</p>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-zinc-600">Host:</span>
                    <span className="font-mono text-zinc-900">{server.host}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-600">Puerto:</span>
                    <span className="font-mono text-zinc-900">{server.port}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-600">Base de Datos:</span>
                    <span className="font-mono text-zinc-900">{server.database}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-600">Usuario:</span>
                    <span className="font-mono text-zinc-900">{server.username}</span>
                  </div>
                </div>
                
                <div className="flex gap-2 mt-4">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="flex-1"
                    onClick={() => handleDelete(server.id)}
                    data-testid="delete-server-button"
                  >
                    <Trash2 className="h-4 w-4 mr-1" />
                    Eliminar
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Add Server Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Agregar Nuevo Servidor</DialogTitle>
            <DialogDescription>Configura la conexión a un servidor SQL</DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nombre</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  required
                  placeholder="Mi Servidor"
                  data-testid="server-name-input"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="system_type">Tipo de Sistema</Label>
                <Select 
                  value={formData.system_type} 
                  onValueChange={(value) => setFormData({...formData, system_type: value})}
                >
                  <SelectTrigger data-testid="system-type-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MPRO">ManagementPro (MPRO)</SelectItem>
                    <SelectItem value="SoftRestaurant">SoftRestaurant</SelectItem>
                    <SelectItem value="Otro">Otro</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="host">Host/IP</Label>
                <Input
                  id="host"
                  value={formData.host}
                  onChange={(e) => setFormData({...formData, host: e.target.value})}
                  required
                  placeholder="192.168.1.100"
                  data-testid="server-host-input"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="port">Puerto</Label>
                <Input
                  id="port"
                  type="number"
                  value={formData.port}
                  onChange={(e) => setFormData({...formData, port: parseInt(e.target.value)})}
                  required
                  data-testid="server-port-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="database">Base de Datos</Label>
              <Input
                id="database"
                value={formData.database}
                onChange={(e) => setFormData({...formData, database: e.target.value})}
                required
                placeholder="CENTRAL2020"
                data-testid="server-database-input"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="username">Usuario</Label>
                <Input
                  id="username"
                  value={formData.username}
                  onChange={(e) => setFormData({...formData, username: e.target.value})}
                  required
                  placeholder="sa"
                  data-testid="server-username-input"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="password">Contraseña</Label>
                <Input
                  id="password"
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  required
                  data-testid="server-password-input"
                />
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800" data-testid="submit-server-button">
                Agregar Servidor
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Servidores;