import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Plus, Trash2, User, Shield, Eye, Settings, Server, Warehouse, Building2 } from 'lucide-react';
import { toast } from 'sonner';

const Usuarios = () => {
  const [users, setUsers] = useState([]);
  const [servers, setServers] = useState([]);
  const [companyGroups, setCompanyGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [permissionsDialogOpen, setPermissionsDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [warehousesMap, setWarehousesMap] = useState({}); // server_id -> warehouses[]
  const [sucursalesMap, setSucursalesMap] = useState({}); // server_id -> sucursales[]
  
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    role: 'Usuario',
    sucursales: [],
    company_group: '',
    allowed_servers: [],
    allowed_warehouses: {},
    allowed_sucursales: {}
  });
  
  const [permissionsData, setPermissionsData] = useState({
    company_group: '',
    allowed_servers: [],
    allowed_warehouses: {},
    allowed_sucursales: {}
  });

  useEffect(() => {
    loadUsers();
    loadServers();
    loadCompanyGroups();
  }, []);

  const loadUsers = async () => {
    try {
      const response = await api.get('/users');
      setUsers(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      toast.error('Error al cargar usuarios');
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  const loadServers = async () => {
    try {
      const response = await api.get('/servers');
      const serversData = Array.isArray(response.data) ? response.data : [];
      setServers(serversData);
      
      // Cargar almacenes y sucursales para cada servidor
      for (const server of serversData) {
        loadWarehousesForServer(server.id);
        loadSucursalesForServer(server.id);
      }
    } catch (error) {
      console.error('Error al cargar servidores:', error);
      setServers([]);
    }
  };
  
  const loadCompanyGroups = async () => {
    try {
      const response = await api.get('/company-groups');
      setCompanyGroups(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Error al cargar grupos:', error);
      setCompanyGroups(['Grupo Principal', 'Grupo Norte', 'Grupo Sur', 'Grupo Centro']);
    }
  };

  const loadWarehousesForServer = async (serverId) => {
    try {
      const response = await api.get(`/servers/${serverId}/departamentos`);
      const warehouses = Array.isArray(response.data) ? response.data : [];
      setWarehousesMap(prev => ({
        ...prev,
        [serverId]: warehouses
      }));
    } catch (error) {
      console.error(`Error al cargar almacenes para servidor ${serverId}:`, error);
    }
  };

  const loadSucursalesForServer = async (serverId) => {
    try {
      const response = await api.get(`/servers/${serverId}/sucursales`);
      const sucursales = Array.isArray(response.data) ? response.data : [];
      setSucursalesMap(prev => ({
        ...prev,
        [serverId]: sucursales
      }));
    } catch (error) {
      console.error(`Error al cargar sucursales para servidor ${serverId}:`, error);
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
  
  const handleOpenPermissions = (user) => {
    setSelectedUser(user);
    setPermissionsData({
      company_group: user.company_group || '',
      allowed_servers: user.allowed_servers || [],
      allowed_warehouses: user.allowed_warehouses || {},
      allowed_sucursales: user.allowed_sucursales || {}
    });
    setPermissionsDialogOpen(true);
  };
  
  const handleSavePermissions = async () => {
    if (!selectedUser) return;
    
    try {
      await api.put(`/users/${selectedUser.id}/permissions`, permissionsData);
      toast.success('Permisos actualizados correctamente');
      setPermissionsDialogOpen(false);
      loadUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al actualizar permisos');
    }
  };
  
  const toggleServerAccess = (serverId) => {
    const currentServers = [...permissionsData.allowed_servers];
    const index = currentServers.indexOf(serverId);
    
    if (index > -1) {
      // Quitar servidor, almacenes y sucursales
      currentServers.splice(index, 1);
      const newWarehouses = { ...permissionsData.allowed_warehouses };
      const newSucursales = { ...permissionsData.allowed_sucursales };
      delete newWarehouses[serverId];
      delete newSucursales[serverId];
      setPermissionsData({
        ...permissionsData,
        allowed_servers: currentServers,
        allowed_warehouses: newWarehouses,
        allowed_sucursales: newSucursales
      });
    } else {
      // Agregar servidor
      setPermissionsData({
        ...permissionsData,
        allowed_servers: [...currentServers, serverId]
      });
    }
  };
  
  const toggleWarehouseAccess = (serverId, warehouseId) => {
    const currentWarehouses = permissionsData.allowed_warehouses[serverId] || [];
    const index = currentWarehouses.indexOf(warehouseId);
    
    let newWarehouseList;
    if (index > -1) {
      newWarehouseList = currentWarehouses.filter(w => w !== warehouseId);
    } else {
      newWarehouseList = [...currentWarehouses, warehouseId];
    }
    
    setPermissionsData({
      ...permissionsData,
      allowed_warehouses: {
        ...permissionsData.allowed_warehouses,
        [serverId]: newWarehouseList
      }
    });
  };

  const toggleSucursalAccess = (serverId, sucursalId) => {
    const currentSucursales = permissionsData.allowed_sucursales[serverId] || [];
    const index = currentSucursales.indexOf(sucursalId);
    
    let newSucursalList;
    if (index > -1) {
      newSucursalList = currentSucursales.filter(s => s !== sucursalId);
    } else {
      newSucursalList = [...currentSucursales, sucursalId];
    }
    
    setPermissionsData({
      ...permissionsData,
      allowed_sucursales: {
        ...permissionsData.allowed_sucursales,
        [serverId]: newSucursalList
      }
    });
  };

  const resetForm = () => {
    setFormData({
      name: '',
      email: '',
      password: '',
      role: 'Usuario',
      sucursales: [],
      company_group: '',
      allowed_servers: [],
      allowed_warehouses: {},
      allowed_sucursales: {}
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
          <p className="text-zinc-600 mt-1">Gestiona los usuarios y sus permisos</p>
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
                  
                  {user.company_group && (
                    <div className="text-sm">
                      <span className="text-zinc-600">Grupo:</span>
                      <span className="ml-2 font-medium text-zinc-900">{user.company_group}</span>
                    </div>
                  )}
                  
                  {user.allowed_servers && user.allowed_servers.length > 0 && (
                    <div className="text-sm">
                      <span className="text-zinc-600">Servidores:</span>
                      <span className="ml-2 font-medium text-blue-600">{user.allowed_servers.length} asignados</span>
                    </div>
                  )}
                  
                  {user.role === 'Administrador' && (
                    <div className="text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded">
                      Acceso completo a todos los servidores
                    </div>
                  )}
                </div>
                
                <div className="flex gap-2 mt-4">
                  {user.role !== 'Administrador' && (
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="flex-1"
                      onClick={() => handleOpenPermissions(user)}
                      data-testid="edit-permissions-button"
                    >
                      <Settings className="h-4 w-4 mr-1" />
                      Permisos
                    </Button>
                  )}
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
      
      {/* Permissions Dialog */}
      <Dialog open={permissionsDialogOpen} onOpenChange={setPermissionsDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Configurar Permisos - {selectedUser?.name}</DialogTitle>
            <DialogDescription>
              Define a qué servidores y almacenes puede acceder este usuario
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-6 py-4">
            {/* Company Group */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">Grupo de Empresa</Label>
              <Select 
                value={permissionsData.company_group || "none"} 
                onValueChange={(value) => setPermissionsData({...permissionsData, company_group: value === "none" ? "" : value})}
              >
                <SelectTrigger data-testid="company-group-select">
                  <SelectValue placeholder="Selecciona un grupo" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Sin grupo asignado</SelectItem>
                  {companyGroups.map((group) => (
                    <SelectItem key={group} value={group}>{group}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-zinc-500">
                Los grupos permiten organizar usuarios por empresa o región
              </p>
            </div>
            
            {/* Servers & Warehouses */}
            <div className="space-y-4">
              <Label className="text-sm font-medium flex items-center gap-2">
                <Server className="h-4 w-4" />
                Acceso a Servidores
              </Label>
              
              {servers.length === 0 ? (
                <p className="text-sm text-zinc-500">No hay servidores configurados</p>
              ) : (
                <div className="space-y-4">
                  {servers.map((server) => (
                    <div key={server.id} className="border border-zinc-200 rounded-lg p-4">
                      <div className="flex items-center gap-3 mb-3">
                        <Checkbox
                          id={`server-${server.id}`}
                          checked={permissionsData.allowed_servers.includes(server.id)}
                          onCheckedChange={() => toggleServerAccess(server.id)}
                          data-testid={`server-checkbox-${server.id}`}
                        />
                        <Label htmlFor={`server-${server.id}`} className="cursor-pointer flex items-center gap-2">
                          <Server className="h-4 w-4 text-zinc-600" />
                          <span className="font-medium">{server.name}</span>
                          <Badge variant="outline" className="text-xs">{server.system_type}</Badge>
                        </Label>
                      </div>
                      
                      {/* Sucursales for this server */}
                      {permissionsData.allowed_servers.includes(server.id) && sucursalesMap[server.id] && sucursalesMap[server.id].length > 0 && (
                        <div className="ml-7 mt-3 pt-3 border-t border-zinc-100">
                          <Label className="text-xs text-zinc-600 flex items-center gap-1 mb-2">
                            <Building2 className="h-3 w-3" />
                            Sucursales (deja vacío para acceso a todas)
                          </Label>
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-40 overflow-y-auto bg-purple-50 p-2 rounded">
                            {sucursalesMap[server.id].map((sucursal) => (
                              <div key={sucursal.id} className="flex items-center gap-2">
                                <Checkbox
                                  id={`sucursal-${server.id}-${sucursal.id}`}
                                  checked={(permissionsData.allowed_sucursales[server.id] || []).includes(sucursal.id)}
                                  onCheckedChange={() => toggleSucursalAccess(server.id, sucursal.id)}
                                  data-testid={`sucursal-checkbox-${sucursal.id}`}
                                />
                                <Label 
                                  htmlFor={`sucursal-${server.id}-${sucursal.id}`} 
                                  className="cursor-pointer text-xs text-zinc-700"
                                >
                                  {sucursal.nombre || sucursal.id}
                                </Label>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* Warehouses for this server */}
                      {permissionsData.allowed_servers.includes(server.id) && warehousesMap[server.id] && warehousesMap[server.id].length > 0 && (
                        <div className="ml-7 mt-3 pt-3 border-t border-zinc-100">
                          <Label className="text-xs text-zinc-600 flex items-center gap-1 mb-2">
                            <Warehouse className="h-3 w-3" />
                            Almacenes específicos (deja vacío para acceso a todos)
                          </Label>
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-40 overflow-y-auto">
                            {warehousesMap[server.id].map((warehouse) => (
                              <div key={warehouse.codigo} className="flex items-center gap-2">
                                <Checkbox
                                  id={`warehouse-${server.id}-${warehouse.codigo}`}
                                  checked={(permissionsData.allowed_warehouses[server.id] || []).includes(warehouse.codigo)}
                                  onCheckedChange={() => toggleWarehouseAccess(server.id, warehouse.codigo)}
                                  data-testid={`warehouse-checkbox-${warehouse.codigo}`}
                                />
                                <Label 
                                  htmlFor={`warehouse-${server.id}-${warehouse.codigo}`} 
                                  className="cursor-pointer text-xs text-zinc-700"
                                >
                                  {warehouse.descripcion || warehouse.codigo}
                                </Label>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            {/* Summary */}
            <div className="bg-zinc-50 rounded-lg p-4 space-y-2">
              <h4 className="text-sm font-medium text-zinc-700">Resumen de Permisos</h4>
              <div className="text-sm text-zinc-600">
                <p>
                  <strong>Servidores:</strong> {permissionsData.allowed_servers.length === 0 
                    ? 'Ninguno (sin acceso)' 
                    : `${permissionsData.allowed_servers.length} servidor(es)`}
                </p>
                {Object.keys(permissionsData.allowed_warehouses).filter(k => permissionsData.allowed_warehouses[k]?.length > 0).length > 0 && (
                  <p>
                    <strong>Almacenes específicos:</strong> Configurados para {Object.keys(permissionsData.allowed_warehouses).filter(k => permissionsData.allowed_warehouses[k]?.length > 0).length} servidor(es)
                  </p>
                )}
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setPermissionsDialogOpen(false)}>
              Cancelar
            </Button>
            <Button 
              onClick={handleSavePermissions} 
              className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800"
              data-testid="save-permissions-button"
            >
              Guardar Permisos
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Usuarios;
