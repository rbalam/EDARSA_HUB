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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Plus, Trash2, User, Shield, Eye, Settings, Server, Building2, Warehouse, Edit, Key, Lock, CheckCircle2, XCircle, RefreshCw, Layers, X, Check, Mail, Phone, Clock, ExternalLink, Search } from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

const Usuarios = () => {
  // ============= ESTADOS USUARIOS =============
  const [users, setUsers] = useState([]);
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [permissionsDialogOpen, setPermissionsDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [sucursalesMap, setSucursalesMap] = useState({});
  const [departamentosMap, setDepartamentosMap] = useState({});
  
  // ============= ESTADOS ROLES =============
  const [roles, setRoles] = useState([]);
  const [modulos, setModulos] = useState([]);
  const [rolesLoading, setRolesLoading] = useState(true);
  const [roleDialogOpen, setRoleDialogOpen] = useState(false);
  const [editingRole, setEditingRole] = useState(null);
  const [roleFormData, setRoleFormData] = useState({
    nombre: '',
    descripcion: '',
    permisos: []
  });
  
  // ============= ESTADOS PERMISOS CATÁLOGOS =============
  const [usuariosCatalogos, setUsuariosCatalogos] = useState([]);
  const [catalogosDisponibles, setCatalogosDisponibles] = useState([]);
  const [modalPermisosCatalogos, setModalPermisosCatalogos] = useState(false);
  const [usuarioSeleccionadoCat, setUsuarioSeleccionadoCat] = useState(null);
  const [formPermisosCat, setFormPermisosCat] = useState({
    catalogos_permitidos: [],
    puede_solicitar: true
  });
  const [savingPermisosCat, setSavingPermisosCat] = useState(false);
  
  // ============= ESTADOS PROVEEDORES =============
  const [proveedores, setProveedores] = useState([]);
  const [filtroProveedores, setFiltroProveedores] = useState('all');
  const [searchProveedores, setSearchProveedores] = useState('');
  const [modalProveedor, setModalProveedor] = useState(false);
  const [proveedorSeleccionado, setProveedorSeleccionado] = useState(null);
  const [sucursalesProveedor, setSucursalesProveedor] = useState([]);
  const [savingProveedor, setSavingProveedor] = useState(false);
  
  // ============= ESTADOS FORMULARIO USUARIOS =============
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
    loadRoles();
    loadModulos();
    loadUsuariosCatalogos();
    loadCatalogosDisponibles();
    loadProveedores();
  }, [loadUsers, loadServers]);

  // ============= FUNCIONES PROVEEDORES =============
  const loadProveedores = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/portal/admin/all-suppliers`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setProveedores(data || []);
      }
    } catch (error) {
      console.error('Error cargando proveedores:', error);
    }
  };
  
  const proveedoresFiltrados = proveedores
    .filter(s => filtroProveedores === 'all' || s.status === filtroProveedores)
    .filter(s => 
      s.rfc?.toLowerCase().includes(searchProveedores.toLowerCase()) ||
      s.razon_social?.toLowerCase().includes(searchProveedores.toLowerCase()) ||
      s.email?.toLowerCase().includes(searchProveedores.toLowerCase())
    );
  
  const proveedoresPendientesCount = proveedores.filter(s => s.status === 'pending').length;
  
  const handleAprobarProveedor = async () => {
    if (!proveedorSeleccionado) return;
    
    setSavingProveedor(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/portal/admin/approve-supplier`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          supplier_id: proveedorSeleccionado.id,
          action: 'approve',
          sucursales: sucursalesProveedor,
          approved_by: 'admin'
        })
      });
      
      if (response.ok) {
        toast.success(`Proveedor ${proveedorSeleccionado.rfc} aprobado`);
        loadProveedores();
        setModalProveedor(false);
        setProveedorSeleccionado(null);
        setSucursalesProveedor([]);
      } else {
        const err = await response.json();
        toast.error(err.detail || 'Error al aprobar');
      }
    } catch (error) {
      toast.error('Error de conexión');
    } finally {
      setSavingProveedor(false);
    }
  };
  
  const handleRechazarProveedor = async (supplier) => {
    if (!confirm(`¿Rechazar proveedor ${supplier.rfc}?`)) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/portal/admin/approve-supplier`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          supplier_id: supplier.id,
          action: 'reject',
          notes: 'Rechazado por administrador',
          approved_by: 'admin'
        })
      });
      
      if (response.ok) {
        toast.success(`Proveedor ${supplier.rfc} rechazado`);
        loadProveedores();
      } else {
        const err = await response.json();
        toast.error(err.detail || 'Error al rechazar');
      }
    } catch (error) {
      toast.error('Error de conexión');
    }
  };
  
  const openProveedorModal = (supplier) => {
    setProveedorSeleccionado(supplier);
    setSucursalesProveedor(supplier.sucursales_asignadas || []);
    setModalProveedor(true);
  };
  
  const formatDateProv = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('es-MX', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  };
  
  const getProveedorStatusBadge = (status) => {
    const styles = {
      pending: { bg: 'bg-yellow-100', text: 'text-yellow-700', label: 'Pendiente' },
      approved: { bg: 'bg-green-100', text: 'text-green-700', label: 'Aprobado' },
      rejected: { bg: 'bg-red-100', text: 'text-red-700', label: 'Rechazado' },
      suspended: { bg: 'bg-gray-100', text: 'text-gray-700', label: 'Suspendido' }
    };
    const s = styles[status] || styles.pending;
    return <span className={`px-2 py-1 rounded text-xs font-medium ${s.bg} ${s.text}`}>{s.label}</span>;
  };

  // ============= FUNCIONES PERMISOS CATÁLOGOS =============
  const loadUsuariosCatalogos = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/sistema/usuarios-asignables`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setUsuariosCatalogos(data.usuarios || []);
      }
    } catch (error) {
      console.error('Error cargando usuarios para catálogos:', error);
    }
  };

  const loadCatalogosDisponibles = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/sistema/catalogos-disponibles`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setCatalogosDisponibles(data.catalogos || []);
      }
    } catch (error) {
      console.error('Error cargando catálogos:', error);
    }
  };

  const handleAbrirPermisosCatalogos = (usuario) => {
    setUsuarioSeleccionadoCat(usuario);
    setFormPermisosCat({
      catalogos_permitidos: usuario.permisos_catalogos || [],
      puede_solicitar: usuario.puede_solicitar || false
    });
    setModalPermisosCatalogos(true);
  };

  const handleGuardarPermisosCatalogos = async () => {
    setSavingPermisosCat(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/sistema/permisos-catalogos`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: usuarioSeleccionadoCat.id,
          ...formPermisosCat
        })
      });
      
      if (!response.ok) throw new Error('Error al guardar');
      
      toast.success('Permisos asignados correctamente');
      setModalPermisosCatalogos(false);
      loadUsuariosCatalogos();
    } catch (error) {
      toast.error('Error al guardar permisos');
    } finally {
      setSavingPermisosCat(false);
    }
  };

  const handleConfigurarNiveles = async (catalogoId, niveles) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/sistema/catalogos/${catalogoId}/niveles`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ niveles_aprobacion: niveles })
      });
      
      if (!response.ok) throw new Error('Error al configurar');
      
      toast.success(`Niveles de aprobación actualizados a ${niveles}`);
      loadCatalogosDisponibles();
    } catch (error) {
      toast.error('Error al configurar niveles');
    }
  };

  // ============= FUNCIONES ROLES =============
  const loadRoles = async () => {
    setRolesLoading(true);
    try {
      const response = await api.get('/roles');
      setRoles(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Error loading roles:', error);
      setRoles([]);
    } finally {
      setRolesLoading(false);
    }
  };

  const loadModulos = async () => {
    try {
      const response = await api.get('/roles/modulos');
      setModulos(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Error loading modulos:', error);
      setModulos([]);
    }
  };

  const openRoleDialog = (role = null) => {
    if (role) {
      setEditingRole(role);
      setRoleFormData({
        nombre: role.nombre,
        descripcion: role.descripcion || '',
        permisos: role.permisos || []
      });
    } else {
      setEditingRole(null);
      setRoleFormData({
        nombre: '',
        descripcion: '',
        permisos: []
      });
    }
    setRoleDialogOpen(true);
  };

  const handleRoleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingRole) {
        await api.put(`/roles/${editingRole.id}`, roleFormData);
        toast.success('Rol actualizado');
      } else {
        await api.post('/roles', roleFormData);
        toast.success('Rol creado');
      }
      setRoleDialogOpen(false);
      loadRoles();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al guardar rol');
    }
  };

  const handleDeleteRole = async (roleId) => {
    if (!window.confirm('¿Estás seguro de eliminar este rol?')) return;
    try {
      await api.delete(`/roles/${roleId}`);
      toast.success('Rol eliminado');
      loadRoles();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al eliminar rol');
    }
  };

  const togglePermiso = (moduloId) => {
    const current = [...roleFormData.permisos];
    const idx = current.indexOf(moduloId);
    if (idx > -1) {
      current.splice(idx, 1);
    } else {
      current.push(moduloId);
    }
    setRoleFormData({ ...roleFormData, permisos: current });
  };

  // ============= FUNCIONES USUARIOS =============
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
      <div className="text-center">
        <h1 className="text-2xl font-bold text-zinc-800">Usuarios y Roles</h1>
        <p className="text-sm text-zinc-500">Gestiona los usuarios y roles del sistema</p>
      </div>

      <Tabs defaultValue="usuarios" className="w-full">
        <TabsList className="grid w-full max-w-2xl grid-cols-4">
          <TabsTrigger value="usuarios" className="flex items-center gap-2">
            <User className="h-4 w-4" />
            Usuarios
          </TabsTrigger>
          <TabsTrigger value="roles" className="flex items-center gap-2">
            <Key className="h-4 w-4" />
            Roles
          </TabsTrigger>
          <TabsTrigger value="permisos-catalogos" className="flex items-center gap-2">
            <Layers className="h-4 w-4" />
            Permisos Catálogos
          </TabsTrigger>
          <TabsTrigger value="proveedores" className="flex items-center gap-2">
            <Building2 className="h-4 w-4" />
            Proveedores
            {proveedoresPendientesCount > 0 && (
              <span className="ml-1 px-1.5 py-0.5 bg-yellow-500 text-white rounded-full text-xs">{proveedoresPendientesCount}</span>
            )}
          </TabsTrigger>
        </TabsList>

        {/* ============= TAB USUARIOS ============= */}
        <TabsContent value="usuarios" className="mt-6">
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-zinc-600">{users.length} usuario(s) registrado(s)</p>
            <Button onClick={() => { resetForm(); setDialogOpen(true); }} className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800" data-testid="add-user-button">
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
        </TabsContent>

        {/* ============= TAB ROLES ============= */}
        <TabsContent value="roles" className="mt-6">
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-zinc-600">{roles.length} rol(es) configurado(s)</p>
            <Button onClick={() => openRoleDialog()} className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800" data-testid="add-role-button">
              <Plus className="h-4 w-4 mr-2" />
              Nuevo Rol
            </Button>
          </div>

          {rolesLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-zinc-900"></div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {roles.map((role) => (
                <Card key={role.id} className="border border-zinc-200 shadow-sm" data-testid="role-card">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${role.nombre === 'Administrador' ? 'bg-red-100' : role.nombre === 'Supervisor' ? 'bg-blue-100' : 'bg-green-100'}`}>
                          {role.nombre === 'Administrador' ? <Shield className="h-5 w-5 text-red-600" /> : 
                           role.nombre === 'Supervisor' ? <Eye className="h-5 w-5 text-blue-600" /> : 
                           <User className="h-5 w-5 text-green-600" />}
                        </div>
                        <div>
                          <CardTitle className="text-lg font-semibold">{role.nombre}</CardTitle>
                          {role.es_sistema && (
                            <Badge variant="outline" className="text-xs bg-amber-50 text-amber-700 border-amber-200">
                              <Lock className="h-3 w-3 mr-1" />
                              Sistema
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-zinc-600 mb-3">{role.descripcion || 'Sin descripción'}</p>
                    
                    <div className="mb-3">
                      <p className="text-xs font-medium text-zinc-500 mb-1">Permisos ({role.permisos?.length || 0}):</p>
                      <div className="flex flex-wrap gap-1">
                        {(role.permisos || []).slice(0, 5).map(p => {
                          const modulo = modulos.find(m => m.id === p);
                          return (
                            <Badge key={p} variant="outline" className="text-xs">
                              {modulo?.nombre || p}
                            </Badge>
                          );
                        })}
                        {(role.permisos?.length || 0) > 5 && (
                          <Badge variant="outline" className="text-xs bg-zinc-100">
                            +{role.permisos.length - 5} más
                          </Badge>
                        )}
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" className="flex-1" onClick={() => openRoleDialog(role)} data-testid="edit-role-button">
                        <Edit className="h-4 w-4 mr-1" />
                        Editar
                      </Button>
                      {!role.es_sistema && (
                        <Button variant="outline" size="sm" className="flex-1 text-red-600 hover:text-red-700" onClick={() => handleDeleteRole(role.id)} data-testid="delete-role-button">
                          <Trash2 className="h-4 w-4 mr-1" />
                          Eliminar
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* ============= TAB PERMISOS CATÁLOGOS ============= */}
        <TabsContent value="permisos-catalogos" className="mt-6 space-y-6">
          {/* Sección: Configurar Permisos de Catálogos por Usuario */}
          <Card>
            <CardHeader className="py-4">
              <CardTitle className="text-base font-medium flex items-center gap-2">
                <Settings className="h-5 w-5 text-blue-500" />
                Configurar Permisos de Catálogos por Usuario
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-4 font-medium text-zinc-500">Usuario</th>
                      <th className="text-left py-3 px-4 font-medium text-zinc-500">Email</th>
                      <th className="text-left py-3 px-4 font-medium text-zinc-500">Rol</th>
                      <th className="text-left py-3 px-4 font-medium text-zinc-500">Puede Solicitar</th>
                      <th className="text-left py-3 px-4 font-medium text-zinc-500">Catálogos</th>
                      <th className="text-right py-3 px-4 font-medium text-zinc-500">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {usuariosCatalogos.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="py-8 text-center text-zinc-500">
                          No hay usuarios disponibles
                        </td>
                      </tr>
                    ) : (
                      usuariosCatalogos.map((usuario) => (
                        <tr key={usuario.id} className="border-b hover:bg-zinc-50">
                          <td className="py-3 px-4 font-medium">{usuario.name}</td>
                          <td className="py-3 px-4 text-zinc-500">{usuario.email}</td>
                          <td className="py-3 px-4">
                            <Badge className={getRoleBadge(usuario.role)}>
                              {getRoleIcon(usuario.role)}
                              <span className="ml-1">{usuario.role}</span>
                            </Badge>
                          </td>
                          <td className="py-3 px-4">
                            {usuario.puede_solicitar ? (
                              <span className="flex items-center gap-1 text-green-600">
                                <CheckCircle2 className="h-4 w-4" /> Sí
                              </span>
                            ) : (
                              <span className="flex items-center gap-1 text-zinc-400">
                                <XCircle className="h-4 w-4" /> No
                              </span>
                            )}
                          </td>
                          <td className="py-3 px-4">
                            <span className="text-xs text-zinc-500">
                              {(usuario.permisos_catalogos || []).length} catálogo(s)
                            </span>
                          </td>
                          <td className="py-3 px-4 text-right">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleAbrirPermisosCatalogos(usuario)}
                              data-testid={`btn-permisos-cat-${usuario.id}`}
                            >
                              <Settings className="h-4 w-4 mr-1" />
                              Configurar
                            </Button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Sección: Configurar Niveles de Aprobación por Catálogo */}
          <Card>
            <CardHeader className="py-4">
              <CardTitle className="text-base font-medium flex items-center gap-2">
                <Layers className="h-5 w-5 text-purple-500" />
                Configurar Niveles de Aprobación por Catálogo
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {catalogosDisponibles.map((cat) => (
                  <div key={cat.id} className="border rounded-lg p-4 hover:bg-zinc-50">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-sm">{cat.nombre}</p>
                        <p className="text-xs text-zinc-500">{cat.modulo}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <select
                          value={cat.niveles_aprobacion || 1}
                          onChange={(e) => handleConfigurarNiveles(cat.id, parseInt(e.target.value))}
                          className="h-8 px-2 border rounded text-sm bg-white"
                        >
                          <option value={1}>1 Nivel</option>
                          <option value={2}>2 Niveles</option>
                          <option value={3}>3 Niveles</option>
                        </select>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 mt-2">
                      {Array.from({length: cat.niveles_aprobacion || 1}).map((_, i) => (
                        <div key={i} className={`flex-1 h-1 rounded ${
                          i === 0 ? 'bg-green-400' : i === 1 ? 'bg-blue-400' : 'bg-purple-400'
                        }`} />
                      ))}
                    </div>
                    <p className="text-xs text-zinc-400 mt-1">
                      {cat.niveles_aprobacion === 1 ? 'Supervisor o Admin aprueba' :
                       cat.niveles_aprobacion === 2 ? 'Supervisor → Admin' :
                       'Supervisor → Admin → Admin final'}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ============= TAB PROVEEDORES ============= */}
        <TabsContent value="proveedores" className="mt-6">
          <Card>
            <CardHeader className="py-4">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-medium flex items-center gap-2">
                  <Building2 className="h-5 w-5 text-emerald-500" />
                  Administración de Proveedores
                </CardTitle>
                <div className="flex items-center gap-2">
                  <a 
                    href="/portal-proveedores" 
                    target="_blank"
                    className="flex items-center gap-1 px-3 py-1.5 text-sm text-zinc-600 hover:text-zinc-900 border rounded-lg"
                  >
                    <ExternalLink className="h-4 w-4" />
                    Ir al Portal
                  </a>
                  <Button size="sm" variant="outline" onClick={loadProveedores}>
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {/* Filtros */}
              <div className="flex flex-wrap items-center gap-4 mb-4">
                <div className="flex gap-2">
                  {['all', 'pending', 'approved', 'rejected'].map(f => (
                    <Button
                      key={f}
                      onClick={() => setFiltroProveedores(f)}
                      variant={filtroProveedores === f ? 'default' : 'outline'}
                      size="sm"
                    >
                      {f === 'all' ? 'Todos' : f === 'pending' ? 'Pendientes' : f === 'approved' ? 'Aprobados' : 'Rechazados'}
                      {f === 'pending' && proveedoresPendientesCount > 0 && (
                        <span className="ml-1 px-1.5 py-0.5 bg-yellow-500 text-white rounded-full text-xs">
                          {proveedoresPendientesCount}
                        </span>
                      )}
                    </Button>
                  ))}
                </div>
                <div className="relative flex-1 max-w-xs">
                  <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-zinc-400" />
                  <Input
                    type="text"
                    placeholder="Buscar RFC, razón social..."
                    value={searchProveedores}
                    onChange={(e) => setSearchProveedores(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              
              {/* Tabla de proveedores */}
              <div className="overflow-x-auto border rounded-lg">
                <table className="w-full text-sm">
                  <thead className="bg-zinc-50 border-b">
                    <tr>
                      <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 uppercase">RFC</th>
                      <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 uppercase">Razón Social</th>
                      <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 uppercase">Contacto</th>
                      <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 uppercase">Estado</th>
                      <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 uppercase">Sucursales</th>
                      <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 uppercase">Registro</th>
                      <th className="text-right px-4 py-3 text-xs font-medium text-zinc-500 uppercase">Acciones</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {proveedoresFiltrados.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="px-4 py-8 text-center text-zinc-500">
                          <Building2 className="h-10 w-10 mx-auto mb-2 opacity-30" />
                          <p>No se encontraron proveedores</p>
                        </td>
                      </tr>
                    ) : (
                      proveedoresFiltrados.map(supplier => (
                        <tr key={supplier.id} className="hover:bg-zinc-50">
                          <td className="px-4 py-3">
                            <span className="font-mono font-medium text-zinc-900">{supplier.rfc}</span>
                          </td>
                          <td className="px-4 py-3">
                            <div>
                              <p className="font-medium text-zinc-900">{supplier.razon_social || '-'}</p>
                              <p className="text-sm text-zinc-500">{supplier.nombre_contacto}</p>
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <div className="text-sm">
                              <p className="flex items-center gap-1 text-zinc-600">
                                <Mail className="h-3 w-3" /> {supplier.email || '-'}
                              </p>
                              <p className="flex items-center gap-1 text-zinc-500">
                                <Phone className="h-3 w-3" /> {supplier.telefono || '-'}
                              </p>
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            {getProveedorStatusBadge(supplier.status)}
                          </td>
                          <td className="px-4 py-3">
                            {supplier.sucursales_asignadas?.length > 0 ? (
                              <span className="text-sm text-zinc-600">
                                {supplier.sucursales_asignadas.length} asignada{supplier.sucursales_asignadas.length > 1 ? 's' : ''}
                              </span>
                            ) : (
                              <span className="text-sm text-zinc-400">Sin asignar</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-sm text-zinc-500">
                            {formatDateProv(supplier.created_at)}
                          </td>
                          <td className="px-4 py-3 text-right">
                            <div className="flex justify-end gap-1">
                              {supplier.status === 'pending' && (
                                <>
                                  <Button
                                    size="sm"
                                    className="bg-green-600 hover:bg-green-700 text-white"
                                    onClick={() => openProveedorModal(supplier)}
                                  >
                                    <Check className="h-4 w-4 mr-1" />
                                    Aprobar
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    className="text-red-600 hover:bg-red-50"
                                    onClick={() => handleRechazarProveedor(supplier)}
                                  >
                                    <X className="h-4 w-4" />
                                  </Button>
                                </>
                              )}
                              {supplier.status === 'approved' && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => openProveedorModal(supplier)}
                                >
                                  <Eye className="h-4 w-4 mr-1" />
                                  Ver / Editar
                                </Button>
                              )}
                              {supplier.status === 'rejected' && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => openProveedorModal(supplier)}
                                >
                                  <Eye className="h-4 w-4 mr-1" />
                                  Ver
                                </Button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Modal Aprobar/Editar Proveedor */}
      {modalProveedor && proveedorSeleccionado && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-hidden flex flex-col">
            <div className="bg-emerald-600 text-white px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Building2 className="h-5 w-5" />
                {proveedorSeleccionado.status === 'pending' ? 'Aprobar Proveedor' : 'Detalle Proveedor'}
              </h2>
              <button onClick={() => setModalProveedor(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4 overflow-y-auto flex-1">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-zinc-500">RFC</p>
                  <p className="font-mono font-medium">{proveedorSeleccionado.rfc}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Razón Social</p>
                  <p className="font-medium">{proveedorSeleccionado.razon_social || '-'}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Contacto</p>
                  <p className="font-medium">{proveedorSeleccionado.nombre_contacto || '-'}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Email</p>
                  <p className="font-medium">{proveedorSeleccionado.email || '-'}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Teléfono</p>
                  <p className="font-medium">{proveedorSeleccionado.telefono || '-'}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Estado</p>
                  {getProveedorStatusBadge(proveedorSeleccionado.status)}
                </div>
              </div>
              
              {(proveedorSeleccionado.status === 'pending' || proveedorSeleccionado.status === 'approved') && (
                <div className="space-y-2">
                  <Label>Sucursales Asignadas:</Label>
                  <div className="border rounded-lg p-3 max-h-48 overflow-y-auto space-y-2">
                    {servers.map(server => (
                      <div key={server.id}>
                        <p className="font-medium text-sm text-zinc-700 mb-1">{server.name}</p>
                        <div className="grid grid-cols-2 gap-1 ml-4">
                          {(server.sucursales || []).map(suc => (
                            <label key={suc.codigo} className="flex items-center gap-2 text-sm cursor-pointer">
                              <input
                                type="checkbox"
                                checked={sucursalesProveedor.includes(suc.codigo)}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    setSucursalesProveedor([...sucursalesProveedor, suc.codigo]);
                                  } else {
                                    setSucursalesProveedor(sucursalesProveedor.filter(s => s !== suc.codigo));
                                  }
                                }}
                                className="h-4 w-4"
                              />
                              {suc.nombre || suc.codigo}
                            </label>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end gap-2 bg-zinc-50">
              <Button variant="outline" onClick={() => setModalProveedor(false)}>Cerrar</Button>
              {proveedorSeleccionado.status === 'pending' && (
                <Button 
                  onClick={handleAprobarProveedor} 
                  disabled={savingProveedor}
                  className="bg-emerald-600 hover:bg-emerald-700"
                >
                  {savingProveedor ? <RefreshCw className="h-4 w-4 animate-spin mr-1" /> : <Check className="h-4 w-4 mr-1" />}
                  Aprobar Proveedor
                </Button>
              )}
              {proveedorSeleccionado.status === 'approved' && (
                <Button 
                  onClick={handleAprobarProveedor} 
                  disabled={savingProveedor}
                >
                  {savingProveedor ? <RefreshCw className="h-4 w-4 animate-spin mr-1" /> : <Check className="h-4 w-4 mr-1" />}
                  Guardar Cambios
                </Button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal Configurar Permisos Catálogos */}
      {modalPermisosCatalogos && usuarioSeleccionadoCat && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-hidden flex flex-col">
            <div className="bg-zinc-800 text-white px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Permisos de {usuarioSeleccionadoCat.name || usuarioSeleccionadoCat.email}
              </h2>
              <button onClick={() => setModalPermisosCatalogos(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4 overflow-y-auto flex-1">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="puede-solicitar"
                  checked={formPermisosCat.puede_solicitar}
                  onChange={(e) => setFormPermisosCat({...formPermisosCat, puede_solicitar: e.target.checked})}
                  className="h-4 w-4"
                />
                <Label htmlFor="puede-solicitar" className="cursor-pointer">
                  Puede solicitar altas en catálogos
                </Label>
              </div>
              
              <div className="space-y-2">
                <Label>Catálogos Permitidos:</Label>
                <div className="grid grid-cols-2 gap-2 p-3 border rounded-lg max-h-[300px] overflow-y-auto">
                  {catalogosDisponibles.map((cat) => (
                    <label key={cat.id} className="flex items-center gap-2 p-2 hover:bg-zinc-50 rounded cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formPermisosCat.catalogos_permitidos.includes(cat.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFormPermisosCat({...formPermisosCat, catalogos_permitidos: [...formPermisosCat.catalogos_permitidos, cat.id]});
                          } else {
                            setFormPermisosCat({...formPermisosCat, catalogos_permitidos: formPermisosCat.catalogos_permitidos.filter(c => c !== cat.id)});
                          }
                        }}
                        className="h-4 w-4"
                      />
                      <div>
                        <span className="text-sm font-medium">{cat.nombre}</span>
                        <span className="text-xs text-zinc-500 block">{cat.modulo}</span>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end gap-2 bg-zinc-50">
              <Button variant="outline" onClick={() => setModalPermisosCatalogos(false)}>Cancelar</Button>
              <Button onClick={handleGuardarPermisosCatalogos} disabled={savingPermisosCat} data-testid="btn-guardar-permisos-cat">
                {savingPermisosCat ? <RefreshCw className="h-4 w-4 animate-spin mr-1" /> : <Check className="h-4 w-4 mr-1" />}
                Guardar Permisos
              </Button>
            </div>
          </div>
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

      {/* Dialog para crear/editar rol */}
      <Dialog open={roleDialogOpen} onOpenChange={setRoleDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingRole ? 'Editar Rol' : 'Nuevo Rol'}</DialogTitle>
            <DialogDescription>
              {editingRole?.es_sistema 
                ? 'Este es un rol de sistema. Solo puedes modificar la descripción y permisos.'
                : 'Define el nombre, descripción y permisos del rol'}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleRoleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Nombre del Rol</Label>
                <Input 
                  value={roleFormData.nombre} 
                  onChange={(e) => setRoleFormData({...roleFormData, nombre: e.target.value})} 
                  required 
                  disabled={editingRole?.es_sistema}
                  placeholder="Ej: Auditor, Gerente, etc."
                  data-testid="role-name-input" 
                />
              </div>
              <div className="space-y-2">
                <Label>Descripción</Label>
                <Input 
                  value={roleFormData.descripcion} 
                  onChange={(e) => setRoleFormData({...roleFormData, descripcion: e.target.value})} 
                  placeholder="Breve descripción del rol"
                  data-testid="role-desc-input" 
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <Label>Permisos de Módulos</Label>
              <p className="text-xs text-zinc-500 mb-2">Selecciona los módulos a los que tendrá acceso este rol</p>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-64 overflow-y-auto border rounded-lg p-3">
                {modulos.map((modulo) => (
                  <div key={modulo.id} className="flex items-start gap-2 p-2 rounded hover:bg-zinc-50">
                    <Checkbox
                      id={`perm-${modulo.id}`}
                      checked={roleFormData.permisos.includes(modulo.id)}
                      onCheckedChange={() => togglePermiso(modulo.id)}
                    />
                    <label htmlFor={`perm-${modulo.id}`} className="cursor-pointer">
                      <span className="text-sm font-medium">{modulo.nombre}</span>
                      <p className="text-xs text-zinc-500">{modulo.descripcion}</p>
                    </label>
                  </div>
                ))}
              </div>
              <p className="text-xs text-zinc-400 mt-1">
                {roleFormData.permisos.length} módulo(s) seleccionado(s)
              </p>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setRoleDialogOpen(false)}>Cancelar</Button>
              <Button type="submit" className="bg-zinc-900 text-zinc-50" data-testid="submit-role-button">
                {editingRole ? 'Guardar Cambios' : 'Crear Rol'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Usuarios;
