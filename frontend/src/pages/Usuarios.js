import { useEffect, useState, useCallback } from 'react';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Plus, Trash2, User, Shield, Eye, Settings, Server, Building2, Warehouse, Edit } from 'lucide-react';
import { toast } from 'sonner';

const Usuarios = () => {
  const [users, setUsers] = useState([]);
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [permissionsDialogOpen, setPermissionsDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [sucursalesMap, setSucursalesMap] = useState({});
  const [departamentosMap, setDepartamentosMap] = useState({});
  
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    role: 'Usuario',
    sucursales: []
  });
  
  const [editMode, setEditMode] = useState(false);
  const [editUserId, setEditUserId] = useState(null);
  
  const [permissionsData, setPermissionsData] = useState({
    allowed_servers: [],
    allowed_sucursales: {},
    allowed_warehouses: {}
  });

  const loadUsers = useCallback(async () => {
    try {
      const response = await api.get('/users');
      setUsers(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      toast.error('Error al cargar usuarios');
      setUsers([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadServers = useCallback(async () => {
    try {
      const response = await api.get('/servers');
      const data = Array.isArray(response.data) ? response.data : [];
      setServers(data);
    } catch (error) {
      console.error('Error loading servers:', error);
      setServers([]);
    }
  }, []);

  useEffect(() => {
    loadUsers();
    loadServers();
  }, [loadUsers, loadServers]);

  const loadSucursalesForServer = async (serverId) => {
    if (sucursalesMap[serverId]) return; // Ya cargadas
    try {
      const response = await api.get(`/servers/${serverId}/sucursales`);
      const data = Array.isArray(response.data) ? response.data : [];
      setSucursalesMap(prev => ({ ...prev, [serverId]: data }));
    } catch (error) {
      console.error(`Error loading sucursales for ${serverId}:`, error);
      setSucursalesMap(prev => ({ ...prev, [serverId]: [] }));
    }
  };

  const loadDepartamentosForServer = async (serverId) => {
    if (departamentosMap[serverId]) return;
    try {
      const response = await api.get(`/servers/${serverId}/departamentos`);
      const data = Array.isArray(response.data) ? response.data : [];
      setDepartamentosMap(prev => ({ ...prev, [serverId]: data }));
    } catch (error) {
      console.error(`Error loading departamentos for ${serverId}:`, error);
      setDepartamentosMap(prev => ({ ...prev, [serverId]: [] }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editMode && editUserId) {
        // Actualizar usuario existente
        const updateData = { ...formData };
        if (!updateData.password) delete updateData.password; // No enviar password vacío
        await api.put(`/users/${editUserId}`, updateData);
        toast.success('Usuario actualizado exitosamente');
      } else {
        // Crear nuevo usuario
        await api.post('/auth/register', formData);
        toast.success('Usuario creado exitosamente');
      }
      setDialogOpen(false);
      resetForm();
      loadUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al guardar usuario');
    }
  };

  const openEditDialog = (user) => {
    setEditMode(true);
    setEditUserId(user.id);
    setFormData({
      name: user.name,
      email: user.email,
      password: '', // No mostrar contraseña
      role: user.role,
      sucursales: user.sucursales || []
    });
    setDialogOpen(true);
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

  const openPermissionsDialog = async (user) => {
    console.log('Abriendo permisos para:', user.name);
    setSelectedUser(user);
    setPermissionsData({
      allowed_servers: user.allowed_servers || [],
      allowed_sucursales: user.allowed_sucursales || {},
      allowed_warehouses: user.allowed_warehouses || {}
    });
    
    // Abrir el diálogo primero
    setPermissionsDialogOpen(true);
    
    // Luego cargar sucursales y departamentos en background
    for (const server of servers) {
      loadSucursalesForServer(server.id);
      loadDepartamentosForServer(server.id);
    }
  };

  const savePermissions = async () => {
    if (!selectedUser) return;
    try {
      await api.put(`/users/${selectedUser.id}/permissions`, permissionsData);
      toast.success('Permisos guardados correctamente');
      setPermissionsDialogOpen(false);
      loadUsers();
    } catch (error) {
      toast.error('Error al guardar permisos');
    }
  };

  const toggleServer = (serverId) => {
    const current = [...permissionsData.allowed_servers];
    const idx = current.indexOf(serverId);
    if (idx > -1) {
      current.splice(idx, 1);
      // También quitar sucursales y almacenes de ese servidor
      const newSuc = { ...permissionsData.allowed_sucursales };
      const newWh = { ...permissionsData.allowed_warehouses };
      delete newSuc[serverId];
      delete newWh[serverId];
      setPermissionsData({ ...permissionsData, allowed_servers: current, allowed_sucursales: newSuc, allowed_warehouses: newWh });
    } else {
      current.push(serverId);
      setPermissionsData({ ...permissionsData, allowed_servers: current });
    }
  };

  const toggleSucursal = (serverId, sucursalId) => {
    const currentList = permissionsData.allowed_sucursales[serverId] || [];
    const idx = currentList.indexOf(sucursalId);
    let newList;
    if (idx > -1) {
      newList = currentList.filter(s => s !== sucursalId);
    } else {
      newList = [...currentList, sucursalId];
    }
    setPermissionsData({
      ...permissionsData,
      allowed_sucursales: { ...permissionsData.allowed_sucursales, [serverId]: newList }
    });
  };

  const toggleDepartamento = (serverId, codigo) => {
    const currentList = permissionsData.allowed_warehouses[serverId] || [];
    const idx = currentList.indexOf(codigo);
    let newList;
    if (idx > -1) {
      newList = currentList.filter(d => d !== codigo);
    } else {
      newList = [...currentList, codigo];
    }
    setPermissionsData({
      ...permissionsData,
      allowed_warehouses: { ...permissionsData.allowed_warehouses, [serverId]: newList }
    });
  };

  const resetForm = () => {
    setFormData({
      name: '',
      email: '',
      password: '',
      role: 'Usuario',
      sucursales: []
    });
    setEditMode(false);
    setEditUserId(null);
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
          <h1 className="text-3xl font-extrabold text-zinc-900">Usuarios</h1>
          <p className="text-zinc-600 mt-1">Gestiona los usuarios del sistema</p>
        </div>
        <Button onClick={() => setDialogOpen(true)} className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800" data-testid="add-user-button">
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
            <Card key={user.id} className="border border-zinc-200 shadow-sm" data-testid="user-card">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  <div className="bg-zinc-100 p-2 rounded-lg">
                    <User className="h-5 w-5 text-zinc-600" />
                  </div>
                  <div>
                    <CardTitle className="text-lg font-semibold">{user.name}</CardTitle>
                    <p className="text-xs text-zinc-500">{user.email}</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Badge className={`${getRoleBadge(user.role)} border`}>
                      {getRoleIcon(user.role)}
                      <span className="ml-1">{user.role}</span>
                    </Badge>
                  </div>
                  <div className="text-sm">
                    <span className="text-zinc-600">Estado: </span>
                    <span className={user.active ? 'text-green-600' : 'text-red-600'}>
                      {user.active ? 'Activo' : 'Inactivo'}
                    </span>
                  </div>
                  {user.allowed_servers && user.allowed_servers.length > 0 && (
                    <div className="text-sm text-blue-600">
                      {user.allowed_servers.length} servidor(es) asignado(s)
                    </div>
                  )}
                  {user.role === 'Administrador' && (
                    <div className="text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded">
                      Acceso total
                    </div>
                  )}
                </div>
                <div className="flex gap-2 mt-4">
                  <Button variant="outline" size="sm" className="flex-1" onClick={() => openEditDialog(user)} data-testid="edit-user-button">
                    <Edit className="h-4 w-4 mr-1" />
                    Editar
                  </Button>
                  {user.role !== 'Administrador' && (
                    <Button variant="outline" size="sm" className="flex-1" onClick={() => openPermissionsDialog(user)} data-testid="permissions-button">
                      <Settings className="h-4 w-4 mr-1" />
                      Permisos
                    </Button>
                  )}
                  <Button variant="outline" size="sm" className="flex-1" onClick={() => handleDelete(user.id)} 
                    disabled={user.role === 'Administrador' && users.filter(u => u.role === 'Administrador').length === 1}
                    data-testid="delete-user-button">
                    <Trash2 className="h-4 w-4 mr-1" />
                    Eliminar
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Dialog para crear usuario */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{editMode ? 'Editar Usuario' : 'Nuevo Usuario'}</DialogTitle>
            <DialogDescription>Crea un nuevo usuario para el sistema</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label>Nombre</Label>
              <Input value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} required data-testid="user-name-input" />
            </div>
            <div className="space-y-2">
              <Label>Email</Label>
              <Input type="email" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} required data-testid="user-email-input" />
            </div>
            <div className="space-y-2">
              <Label>{editMode ? 'Nueva Contraseña (dejar vacío para no cambiar)' : 'Contraseña'}</Label>
              <Input type="password" value={formData.password} onChange={(e) => setFormData({...formData, password: e.target.value})} required={!editMode} placeholder={editMode ? "Dejar vacío para mantener" : ""} data-testid="user-password-input" />
            </div>
            <div className="space-y-2">
              <Label>Rol</Label>
              <Select value={formData.role} onValueChange={(v) => setFormData({...formData, role: v})}>
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
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancelar</Button>
              <Button type="submit" className="bg-zinc-900 text-zinc-50" data-testid="submit-user-button">Crear</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Dialog para permisos */}
      <Dialog open={permissionsDialogOpen} onOpenChange={setPermissionsDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Permisos de {selectedUser?.name}</DialogTitle>
            <DialogDescription>Configura los servidores, sucursales y almacenes que puede ver este usuario</DialogDescription>
          </DialogHeader>
          
          <div className="space-y-6 py-4">
            {servers.length === 0 ? (
              <p className="text-zinc-500">No hay servidores configurados</p>
            ) : (
              servers.map((server) => {
                const isServerSelected = permissionsData.allowed_servers.includes(server.id);
                const serverSucursales = sucursalesMap[server.id] || [];
                const serverDepartamentos = departamentosMap[server.id] || [];
                
                return (
                  <div key={server.id} className="border rounded-lg p-4">
                    <div className="flex items-center gap-3 mb-3">
                      <Checkbox
                        id={`srv-${server.id}`}
                        checked={isServerSelected}
                        onCheckedChange={() => toggleServer(server.id)}
                      />
                      <label htmlFor={`srv-${server.id}`} className="cursor-pointer flex items-center gap-2 font-medium">
                        <Server className="h-4 w-4" />
                        {server.name}
                        <Badge variant="outline" className="text-xs">{server.system_type}</Badge>
                      </label>
                    </div>
                    
                    {isServerSelected && (
                      <div className="ml-6 space-y-4">
                        {/* Sucursales */}
                        {serverSucursales.length > 0 && (
                          <div className="bg-purple-50 p-3 rounded">
                            <div className="flex items-center gap-2 mb-2 text-sm font-medium text-purple-700">
                              <Building2 className="h-4 w-4" />
                              Sucursales (vacío = todas)
                            </div>
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-32 overflow-y-auto">
                              {serverSucursales.map((suc) => (
                                <div key={suc.id} className="flex items-center gap-2">
                                  <Checkbox
                                    id={`suc-${server.id}-${suc.id}`}
                                    checked={(permissionsData.allowed_sucursales[server.id] || []).includes(suc.id)}
                                    onCheckedChange={() => toggleSucursal(server.id, suc.id)}
                                  />
                                  <label htmlFor={`suc-${server.id}-${suc.id}`} className="text-xs cursor-pointer">
                                    {suc.nombre || suc.id}
                                  </label>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {/* Departamentos/Almacenes */}
                        {serverDepartamentos.length > 0 && (
                          <div className="bg-blue-50 p-3 rounded">
                            <div className="flex items-center gap-2 mb-2 text-sm font-medium text-blue-700">
                              <Warehouse className="h-4 w-4" />
                              Departamentos (vacío = todos)
                            </div>
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-32 overflow-y-auto">
                              {serverDepartamentos.map((dep) => (
                                <div key={dep.codigo} className="flex items-center gap-2">
                                  <Checkbox
                                    id={`dep-${server.id}-${dep.codigo}`}
                                    checked={(permissionsData.allowed_warehouses[server.id] || []).includes(dep.codigo)}
                                    onCheckedChange={() => toggleDepartamento(server.id, dep.codigo)}
                                  />
                                  <label htmlFor={`dep-${server.id}-${dep.codigo}`} className="text-xs cursor-pointer">
                                    {dep.descripcion || dep.codigo}
                                  </label>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setPermissionsDialogOpen(false)}>Cancelar</Button>
            <Button onClick={savePermissions} className="bg-zinc-900 text-zinc-50" data-testid="save-permissions-button">
              Guardar Permisos
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Usuarios;
