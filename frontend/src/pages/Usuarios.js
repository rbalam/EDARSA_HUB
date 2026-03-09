import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Plus, Trash2, User, Shield, Eye } from 'lucide-react';
import { toast } from 'sonner';

const Usuarios = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    role: 'Usuario',
    sucursales: []
  });

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const response = await api.get('/users');
      setUsers(response.data);
    } catch (error) {
      toast.error('Error al cargar usuarios');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      await api.post('/auth/register', formData);
      toast.success('Usuario creado exitosamente');
      setDialogOpen(false);
      resetForm();
      loadUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear usuario');
    }
  };

  const handleDelete = async (userId) => {
    if (!window.confirm('¿Estás seguro de eliminar este usuario?')) return;
    
    try {
      await api.delete(`/users/${userId}`);
      toast.success('Usuario eliminado');
      loadUsers();
    } catch (error) {
      toast.error('Error al eliminar usuario');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      email: '',
      password: '',
      role: 'Usuario',
      sucursales: []
    });
  };

  const getRoleBadge = (role) => {
    const variants = {
      'Administrador': 'bg-red-100 text-red-700 border-red-200',
      'Supervisor': 'bg-blue-100 text-blue-700 border-blue-200',
      'Usuario': 'bg-green-100 text-green-700 border-green-200'
    };
    return variants[role] || 'bg-zinc-100 text-zinc-700';
  };

  const getRoleIcon = (role) => {
    if (role === 'Administrador') return <Shield className="h-4 w-4" />;
    if (role === 'Supervisor') return <Eye className="h-4 w-4" />;
    return <User className="h-4 w-4" />;
  };

  return (
    <div className="space-y-6" data-testid="usuarios-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-zinc-900" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Usuarios
          </h1>
          <p className="text-zinc-600 mt-1">Gestiona los usuarios del sistema</p>
        </div>
        <Button 
          onClick={() => setDialogOpen(true)}
          className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800"
          data-testid="add-user-button"
        >
          <Plus className="h-4 w-4 mr-2" />
          Agregar Usuario
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-zinc-900"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {users.map((user) => (
            <Card key={user.id} className="border border-zinc-200 shadow-sm hover:border-zinc-300 transition-colors" data-testid="user-card">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="bg-zinc-100 p-2 rounded-lg">
                      <User className="h-5 w-5 text-zinc-600" />
                    </div>
                    <div>
                      <CardTitle className="text-lg font-semibold">{user.name}</CardTitle>
                      <p className="text-xs text-zinc-500 mt-1">{user.email}</p>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Badge className={`${getRoleBadge(user.role)} border`}>
                      {getRoleIcon(user.role)}
                      <span className="ml-1">{user.role}</span>
                    </Badge>
                  </div>
                  
                  <div className="text-sm">
                    <span className="text-zinc-600">Estado:</span>
                    <span className={`ml-2 font-medium ${user.active ? 'text-green-600' : 'text-red-600'}`}>
                      {user.active ? 'Activo' : 'Inactivo'}
                    </span>
                  </div>
                  
                  {user.sucursales && user.sucursales.length > 0 && (
                    <div className="text-sm">
                      <span className="text-zinc-600">Sucursales:</span>
                      <p className="font-mono text-xs text-zinc-900 mt-1">
                        {user.sucursales.length} asignadas
                      </p>
                    </div>
                  )}
                </div>
                
                <div className="flex gap-2 mt-4">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="flex-1"
                    onClick={() => handleDelete(user.id)}
                    disabled={user.role === 'Administrador' && users.filter(u => u.role === 'Administrador').length === 1}
                    data-testid="delete-user-button"
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

      {/* Add User Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Agregar Nuevo Usuario</DialogTitle>
            <DialogDescription>Crea un nuevo usuario para el sistema</DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nombre Completo</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  required
                  placeholder="Juan Pérez"
                  data-testid="user-name-input"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="email">Correo Electrónico</Label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  required
                  placeholder="usuario@empresa.com"
                  data-testid="user-email-input"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="password">Contraseña</Label>
                <Input
                  id="password"
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  required
                  placeholder="••••••••"
                  data-testid="user-password-input"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="role">Rol</Label>
                <Select 
                  value={formData.role} 
                  onValueChange={(value) => setFormData({...formData, role: value})}
                >
                  <SelectTrigger data-testid="user-role-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Usuario">Usuario</SelectItem>
                    <SelectItem value="Supervisor">Supervisor</SelectItem>
                    <SelectItem value="Administrador">Administrador</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800" data-testid="submit-user-button">
                Crear Usuario
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Usuarios;