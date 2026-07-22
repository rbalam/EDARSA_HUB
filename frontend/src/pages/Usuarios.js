import logger from '../services/logger';
// FASE AUTH-SECURITY-01 / FASE 4.1: getToken eliminado, auth viaja en cookie httpOnly
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
import { Plus, Trash2, User, Shield, Eye, Settings, Server, Building2, Warehouse, Edit, Key, Lock, CheckCircle2, XCircle, RefreshCw, Layers, X, Check, Mail, Phone, Clock, ExternalLink, Search, ChevronDown, ChevronUp, FileText } from 'lucide-react';
import { toast } from 'sonner';
// FASE 12: Componente de Bitácora RBAC (solo lectura)
import BitacoraRBAC from '@/components/admin/BitacoraRBAC';
// FASE 6: Utilidades de estilo para evitar ternarios anidados
import { getRoleBgClass, getNivelAprobacionClass, getNivelAprobacionDesc } from '../utils/styleHelpers';
import { PasswordInput, PasswordRules, isPasswordPolicySatisfied } from '@/components/auth/PasswordControls';


const Usuarios = () => {
  // RBAC canónico para visibilidad de tabs: fuente primaria /auth/me/effective-permissions
  const [effectivePermissions, setEffectivePermissions] = useState(null);
  const [effectivePermissionsLoading, setEffectivePermissionsLoading] = useState(true);

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

  // ============= ESTADOS VISTA EXPANDIR/CONTRAER =============
  const [usersExpanded, setUsersExpanded] = useState(true);
  const [rolesExpanded, setRolesExpanded] = useState(true);

  // ============= ESTADOS BÚSQUEDA =============
  const [searchUsers, setSearchUsers] = useState('');
  const [searchRoles, setSearchRoles] = useState('');
  // P0 USUARIOS: mostrar/ocultar inactivos (default: ocultos)
  const [showInactive, setShowInactive] = useState(false);

  // ============= ESTADOS PERMISOS CATÁLOGOS =============
  const [usuariosCatalogos, setUsuariosCatalogos] = useState([]);
  const [catalogosDisponibles, setCatalogosDisponibles] = useState([]);
  const [modalPermisosCatalogos, setModalPermisosCatalogos] = useState(false);
  const [usuarioSeleccionadoCat, setUsuarioSeleccionadoCat] = useState(null);
  const [formPermisosCat, setFormPermisosCat] = useState({
    catalogos_permitidos: [],
    puede_solicitar: true,
    puede_autorizar: false,
    puede_liberar: false
  });
  const [savingPermisosCat, setSavingPermisosCat] = useState(false);

  // ============= ESTADOS ESTRUCTURA =============
  const [estructuraData, setEstructuraData] = useState(null);
  const [mapeoData, setMapeoData] = useState(null);
  const [estructuraLoading, setEstructuraLoading] = useState(false);

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
      // SQL-FIRST: Usuarios desde EDARSAHUB SQL.
      // incluir_inactivos=true para poder mostrar/reactivar usuarios inactivos
      // (el filtrado visual lo controla el checkbox "Mostrar inactivos").
      const response = await api.get('/admin-sql/users?incluir_inactivos=true');
      setUsers(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      toast.error('Error al cargar usuarios');
      setUsers([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // P0 USUARIOS: activar/desactivar usuario (con revocación de sesiones al inactivar)
  const handleToggleActivo = useCallback(async (user) => {
    const accion = user.active ? 'inactivar' : 'activar';
    try {
      const { data } = await api.patch(`/admin-sql/users/${user.id}/toggle-activo`);
      if (data?.active) {
        toast.success(`Usuario activado correctamente`);
      } else {
        const ses = data?.sesiones_revocadas || 0;
        toast.success(`Usuario inactivado${ses ? ` · ${ses} sesión(es) cerrada(s)` : ''}`);
      }
      await loadUsers();
    } catch (error) {
      const msg = error?.response?.data?.detail || `No se pudo ${accion} el usuario`;
      toast.error(msg);
    }
  }, [loadUsers]);

  const loadServers = useCallback(async () => {
    try {
      // SQL-FIRST: Servidores desde EDARSAHUB SQL
      const response = await api.get('/admin-sql/servers');
      const data = Array.isArray(response.data) ? response.data : [];
      setServers(data);
    } catch (error) {
      logger.error('Error loading servers:', error);
      setServers([]);
    }
  }, []);

  // ============= FUNCIONES ESTRUCTURA =============
  const loadEstructura = useCallback(async () => {
    setEstructuraLoading(true);
    try {
      const [estructuraRes, mapeoRes] = await Promise.all([
        api.get('/sistema/estructura-organizacional'),
        api.get('/sistema/mapeo-servidores')
      ]);

      setEstructuraData(estructuraRes.data);
      setMapeoData(mapeoRes.data);
    } catch (error) {
      logger.error('Error cargando estructura organizacional:', error);
    } finally {
      setEstructuraLoading(false);
    }
  }, []);

  useEffect(() => {
    let mounted = true;

    const loadEffectivePermissions = async () => {
      setEffectivePermissionsLoading(true);
      try {
        const response = await api.get('/auth/me/effective-permissions');
        if (mounted) {
          setEffectivePermissions(response.data || {});
        }
      } catch (error) {
        logger.error('Error cargando permisos efectivos:', error);
        if (mounted) {
          setEffectivePermissions({});
        }
      } finally {
        if (mounted) {
          setEffectivePermissionsLoading(false);
        }
      }
    };

    loadEffectivePermissions();

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    loadUsers();
    loadServers();
    loadRoles();
    loadModulos();
    loadUsuariosCatalogos();
    loadCatalogosDisponibles();
    loadProveedores();
    // Las funciones no-memoizadas se llaman solo en mount
    // loadRoles, loadModulos, etc. son estables (no dependen de props/state variables)
  }, [loadUsers, loadServers]);

  // ============= FUNCIONES PROVEEDORES =============
  const loadProveedores = async () => {
    try {
      const response = await api.get('/portal/admin/all-suppliers');
      setProveedores(response.data || []);
    } catch (error) {
      logger.error('Error cargando proveedores:', error);
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
      await api.post('/portal/admin/approve-supplier', {
        supplier_id: proveedorSeleccionado.id,
        action: 'approve',
        sucursales: sucursalesProveedor,
        approved_by: 'admin'
      });

      toast.success(`Proveedor ${proveedorSeleccionado.rfc} aprobado`);
      loadProveedores();
      setModalProveedor(false);
      setProveedorSeleccionado(null);
      setSucursalesProveedor([]);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error de conexión');
    } finally {
      setSavingProveedor(false);
    }
  };

  const handleRechazarProveedor = async (supplier) => {
    if (!confirm(`¿Rechazar proveedor ${supplier.rfc}?`)) return;

    try {
      await api.post('/portal/admin/approve-supplier', {
        supplier_id: supplier.id,
        action: 'reject',
        notes: 'Rechazado por administrador',
        approved_by: 'admin'
      });

      toast.success(`Proveedor ${supplier.rfc} rechazado`);
      loadProveedores();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error de conexión');
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
      // SQL-FIRST: Usuarios asignables desde EDARSAHUB SQL
      const response = await api.get('/admin-sql/usuarios-asignables');
      setUsuariosCatalogos(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      logger.error('Error cargando usuarios para catálogos:', error);
    }
  };

  const loadCatalogosDisponibles = async () => {
    try {
      // SQL-FIRST: Catálogos desde EDARSAHUB SQL
      const response = await api.get('/admin-sql/catalogos-disponibles');
      setCatalogosDisponibles(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      logger.error('Error cargando catálogos:', error);
    }
  };

  const handleAbrirPermisosCatalogos = (usuario) => {
    setUsuarioSeleccionadoCat(usuario);
    setFormPermisosCat({
      catalogos_permitidos: (usuario.permisos_catalogos || []).map(String),
      puede_solicitar: usuario.puede_solicitar || false,
      puede_autorizar: usuario.puede_autorizar || false,
      puede_liberar: usuario.puede_liberar || false
    });
    setModalPermisosCatalogos(true);
  };

  const handleGuardarPermisosCatalogos = async () => {
    setSavingPermisosCat(true);
    try {
      // SQL-FIRST: Guardar permisos en EDARSAHUB SQL
      await api.post('/admin-sql/permisos-catalogos', {
        user_id: usuarioSeleccionadoCat.id,
        ...formPermisosCat
      });

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
      await api.put(`/sistema/catalogos/${catalogoId}/niveles`, { niveles_aprobacion: niveles });

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
      // SQL-FIRST: Roles desde EDARSAHUB SQL
      const response = await api.get('/admin-sql/roles');
      const rolesData = Array.isArray(response.data) ? response.data : [];
      setRoles(rolesData.map(role => ({
        ...role,
        permisos: Array.from(new Set((role.permisos || []).map(String)))
      })));
    } catch (error) {
      logger.error('Error loading roles:', error);
      setRoles([]);
    } finally {
      setRolesLoading(false);
    }
  };

  const loadModulos = async () => {
    try {
      // SQL-FIRST: Módulos desde EDARSAHUB SQL
      const response = await api.get('/admin-sql/roles/modulos');
      const modulosData = Array.isArray(response.data) ? response.data : [];
      const uniqueModulos = Array.from(
        new Map(modulosData.map(modulo => [String(modulo.id), { ...modulo, id: String(modulo.id) }])).values()
      );
      setModulos(uniqueModulos);
    } catch (error) {
      logger.error('Error loading modulos:', error);
      setModulos([]);
    }
  };

  const openRoleDialog = (role = null) => {
    if (role) {
      setEditingRole(role);
      setRoleFormData({
        nombre: role.nombre,
        descripcion: role.descripcion || '',
        permisos: Array.from(new Set((role.permisos || []).map(String)))
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
      if (editingRole && !canEditRoles()) {
        toast.error('No tiene permiso efectivo para editar roles');
        return;
      }
      if (!editingRole && !canCreateRoles()) {
        toast.error('No tiene permiso efectivo para crear roles');
        return;
      }
      if (editingRole) {
        await api.put(`/admin-sql/roles/${editingRole.id}`, roleFormData);
        toast.success('Rol actualizado');
      } else {
        await api.post('/admin-sql/roles', roleFormData);
        toast.success('Rol creado');
      }
      setRoleDialogOpen(false);
      loadRoles();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al guardar rol');
    }
  };

  const handleDeleteRole = async (roleId) => {
    if (!canDeleteRoles()) {
      toast.error('No tiene permiso efectivo para eliminar roles');
      return;
    }
    if (!window.confirm('¿Estás seguro de eliminar este rol?')) return;
    try {
      await api.delete(`/admin-sql/roles/${roleId}`);
      toast.success('Rol eliminado');
      loadRoles();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al eliminar rol');
    }
  };

  const togglePermiso = (moduloId) => {
    const id = String(moduloId);
    const current = Array.from(new Set((roleFormData.permisos || []).map(String)));
    const idx = current.indexOf(id);
    if (idx > -1) {
      current.splice(idx, 1);
    } else {
      current.push(id);
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
      logger.error(`Error loading sucursales for ${serverId}:`, error);
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
      logger.error(`Error loading departamentos for ${serverId}:`, error);
      setDepartamentosMap(prev => ({ ...prev, [serverId]: [] }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const shouldValidatePassword = !editMode || Boolean(formData.password);
    if (!isPasswordPolicySatisfied(formData.password, { required: shouldValidatePassword })) {
      toast.error('La contraseña debe cumplir las reglas de seguridad.');
      return;
    }

    try {
      if (editMode && editUserId) {
        const targetUser = users.find((user) => String(user.id) === String(editUserId));
        if (!canEditUser(targetUser)) {
          toast.error('No tiene permiso efectivo para editar este usuario');
          return;
        }
        // Actualizar usuario existente
        const updateData = { ...formData };
        if (!updateData.password) delete updateData.password; // No enviar password vacío
        await api.put(`/users/${editUserId}`, updateData);
        toast.success('Usuario actualizado exitosamente');
      } else {
        if (!canCreateUsers()) {
          toast.error('No tiene permiso efectivo para crear usuarios');
          return;
        }
        await api.post('/users', formData);
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
    const targetUser = users.find((user) => String(user.id) === String(userId));
    if (!canDeleteUser(targetUser)) {
      toast.error('No tiene permiso efectivo para eliminar este usuario');
      return;
    }
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
    logger.log('Abriendo permisos para:', user.name);
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
    if (!canEditUser(selectedUser)) {
      toast.error('No tiene permiso efectivo para modificar alcance de este usuario');
      return;
    }
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

  // P5-10B: Helper para normalizar comparaciones de rol (SQL usa SUPERADMIN, legacy usa SuperAdministrador)
  const isSuperAdmin = (role) => {
    const normalized = (role || '').toUpperCase().replace(/[^A-Z]/g, '');
    return normalized === 'SUPERADMIN' || normalized === 'SUPERADMINISTRADOR';
  };

  const isAdmin = (role) => {
    const normalized = (role || '').toUpperCase().replace(/[^A-Z]/g, '');
    return normalized === 'ADMIN' || normalized === 'ADMINISTRADOR' || isSuperAdmin(role);
  };

  const getRoleBadge = (role) => {
    const variants = {
      'SuperAdministrador': 'bg-purple-100 text-purple-700 border-purple-200',
      'SUPERADMIN': 'bg-purple-100 text-purple-700 border-purple-200',
      'Administrador': 'bg-red-100 text-red-700 border-red-200',
      'ADMIN': 'bg-red-100 text-red-700 border-red-200',
      'Supervisor': 'bg-blue-100 text-blue-700 border-blue-200',
      'SUPERVISOR': 'bg-blue-100 text-blue-700 border-blue-200',
      'Usuario': 'bg-green-100 text-green-700 border-green-200',
      'USUARIO': 'bg-green-100 text-green-700 border-green-200'
    };
    return variants[role] || 'bg-zinc-100 text-zinc-700';
  };

  const getRoleIcon = (role) => {
    if (isSuperAdmin(role)) return <Shield className="h-4 w-4 text-purple-600" />;
    if (isAdmin(role)) return <Shield className="h-4 w-4" />;
    if ((role || '').toUpperCase().includes('SUPERVISOR')) return <Eye className="h-4 w-4" />;
    return <User className="h-4 w-4" />;
  };

  const getEffectiveRoleLevel = () => {
    const levels = (effectivePermissions?.roles || [])
      .map((role) => Number(role?.nivel_jerarquia ?? role?.nivel ?? role?.NivelJerarquia ?? 0))
      .filter((level) => Number.isFinite(level));
    return levels.length ? Math.max(...levels) : 0;
  };

  const getRoleDefinitionLevel = (role) => {
    const explicit = Number(role?.nivel ?? role?.nivel_jerarquia ?? role?.NivelJerarquia ?? role?.role_level ?? 0);
    if (Number.isFinite(explicit) && explicit > 0) return explicit;
    const roleCode = normalizeRbacCode(role?.codigo || role?.role_code || role?.nombre || role?.name);
    const match = roles.find((item) => {
      const itemCodes = [item?.codigo, item?.role_code, item?.nombre, item?.name].map(normalizeRbacCode);
      return itemCodes.includes(roleCode);
    });
    return Number(match?.nivel ?? match?.nivel_jerarquia ?? match?.NivelJerarquia ?? 0) || 0;
  };

  const getTargetRoleLevel = (targetUser) => getRoleDefinitionLevel({
    nivel: targetUser?.role_level ?? targetUser?.nivel ?? targetUser?.nivel_jerarquia,
    codigo: targetUser?.role_code,
    nombre: targetUser?.role,
  });

  const isTargetSuperAdmin = (targetUser) => (
    getTargetRoleLevel(targetUser) >= 100 || isSuperAdmin(targetUser?.role || targetUser?.role_code)
  );

  const canCreateUsers = () => !effectivePermissionsLoading && (hasPermission('SISTEMA_USUARIOS_CREAR') || isEffectiveSuperAdmin());
  const canEditUsers = () => !effectivePermissionsLoading && (hasPermission('SISTEMA_USUARIOS_EDITAR') || isEffectiveSuperAdmin());
  const canDeleteUsers = () => !effectivePermissionsLoading && (hasPermission('SISTEMA_USUARIOS_ELIMINAR') || isEffectiveSuperAdmin());
  const canCreateRoles = () => !effectivePermissionsLoading && (hasPermission('SISTEMA_ROLES_CREAR') || isEffectiveSuperAdmin());
  const canEditRoles = () => !effectivePermissionsLoading && (hasPermission('SISTEMA_ROLES_EDITAR') || isEffectiveSuperAdmin());
  const canDeleteRoles = () => !effectivePermissionsLoading && (hasPermission('SISTEMA_ROLES_ELIMINAR') || isEffectiveSuperAdmin());

  const canManageByHierarchy = (targetUser) => {
    if (!isTargetSuperAdmin(targetUser)) return true;
    return getEffectiveRoleLevel() >= 100 || isEffectiveSuperAdmin();
  };

  const canEditUser = (targetUser) => canEditUsers() && canManageByHierarchy(targetUser);
  const canDeleteUser = (targetUser) => canDeleteUsers() && canManageByHierarchy(targetUser);
  const canManageUser = (targetUser) => canEditUser(targetUser) || canDeleteUser(targetUser);
  const canAssignSuperAdmin = () => getEffectiveRoleLevel() >= 100 || isEffectiveSuperAdmin();

  // ============= RBAC CANÓNICO: VISIBILIDAD DE TABS =============
  // Fuente primaria: /auth/me/effective-permissions.
  // No usar sec_permisos/sec_roles/role legacy como fuente primaria para tabs.
  const TAB_PERMISSIONS = {
    usuarios: 'SISTEMA_USUARIOS_VER',
    roles: 'SISTEMA_ROLES_VER',
    permisosCatalogos: 'SISTEMA_PERMISOS_CATALOGOS_VER',
    estructura: 'SISTEMA_ESTRUCTURA_VER',
    bitacora: 'SISTEMA_RBAC_BITACORA_VER'
  };

  const getEffectivePermissionCodes = () => {
    const flat = effectivePermissions?.permissions_flat;
    if (Array.isArray(flat)) {
      return flat.filter(Boolean);
    }

    const permissions = effectivePermissions?.permissions;
    if (Array.isArray(permissions)) {
      return permissions
        .map((permission) => {
          if (typeof permission === 'string') return permission;
          return permission?.codigo || permission?.code || permission?.permission || permission?.name;
        })
        .filter(Boolean);
    }

    return [];
  };

  const getEffectiveRoleCodes = () => {
    const rolesEfectivos = effectivePermissions?.roles;
    if (!Array.isArray(rolesEfectivos)) {
      return [];
    }

    return rolesEfectivos
      .map((role) => {
        if (typeof role === 'string') return role;
        return role?.codigo || role?.code || role?.nombre || role?.name;
      })
      .filter(Boolean);
  };

  const normalizeRbacCode = (value) => (
    String(value || '')
      .toUpperCase()
      .replace(/[^A-Z0-9_]/g, '')
  );

  const hasPermission = (permissionCode) => {
    const expected = normalizeRbacCode(permissionCode);
    return getEffectivePermissionCodes()
      .map(normalizeRbacCode)
      .includes(expected);
  };

  const isEffectiveSuperAdmin = () => {
    const rolesEfectivos = getEffectiveRoleCodes().map(normalizeRbacCode);
    return rolesEfectivos.includes('SUPERADMIN') || rolesEfectivos.includes('SUPERADMINISTRADOR') || getEffectiveRoleLevel() >= 100;
  };

  const canViewTab = (tabKey) => {
    const permissionCode = TAB_PERMISSIONS[tabKey];
    if (!permissionCode || effectivePermissionsLoading) {
      return false;
    }

    return hasPermission(permissionCode) || isEffectiveSuperAdmin();
  };

  const canViewUsuarios = () => canViewTab('usuarios');
  const canViewRoles = () => canViewTab('roles');
  const canViewPermisosCatalogos = () => canViewTab('permisosCatalogos');
  const canViewEstructura = () => canViewTab('estructura');
  const canViewBitacora = () => canViewTab('bitacora');

  return (
    <div className="space-y-6" data-testid="usuarios-page">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-zinc-800">Usuarios y Roles</h1>
        <p className="text-sm text-zinc-500">Gestiona los usuarios y roles del sistema</p>
      </div>

      <Tabs defaultValue="usuarios" className="w-full">
        <TabsList className="flex flex-wrap gap-1 w-full max-w-4xl">
          {canViewUsuarios() && (
            <TabsTrigger value="usuarios" className="flex items-center gap-2">
              <User className="h-4 w-4" />
              Usuarios
            </TabsTrigger>
          )}
          {canViewRoles() && (
            <TabsTrigger value="roles" className="flex items-center gap-2">
              <Key className="h-4 w-4" />
              Roles
            </TabsTrigger>
          )}
          {canViewPermisosCatalogos() && (
            <TabsTrigger value="permisos-catalogos" className="flex items-center gap-2">
              <Layers className="h-4 w-4" />
              Permisos Catálogos
            </TabsTrigger>
          )}
          {canViewEstructura() && (
            <TabsTrigger value="estructura" className="flex items-center gap-2" data-testid="tab-estructura">
              <Building2 className="h-4 w-4" />
              Estructura
            </TabsTrigger>
          )}
          {canViewBitacora() && (
            <TabsTrigger value="bitacora" className="flex items-center gap-2" data-testid="tab-bitacora">
              <FileText className="h-4 w-4" />
              Bitácora RBAC
            </TabsTrigger>
          )}
        </TabsList>

        {/* ============= TAB USUARIOS ============= */}
        {canViewTab('usuarios') && (
        <TabsContent value="usuarios" className="mt-6">
          <div className="flex flex-col gap-3 mb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <p className="text-sm text-zinc-600">
                  {users.filter(u => u.active).length} activo(s)
                  {users.filter(u => !u.active).length > 0 && (
                    <span className="text-red-500"> · {users.filter(u => !u.active).length} inactivo(s)</span>
                  )}
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setUsersExpanded(!usersExpanded)}
                  className="flex items-center gap-1"
                  data-testid="toggle-users-view"
                >
                  {usersExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  {usersExpanded ? 'Contraer' : 'Expandir'}
                </Button>
              </div>
              {canCreateUsers() && (
                <Button onClick={() => { resetForm(); setDialogOpen(true); }} className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800" data-testid="add-user-button">
                  <Plus className="h-4 w-4 mr-2" />
                  Agregar Usuario
                </Button>
              )}
            </div>
            {/* Campo de búsqueda + filtro de inactivos */}
            <div className="flex items-center gap-4 flex-wrap">
              <div className="relative max-w-md flex-1 min-w-[240px]">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
                <Input
                  placeholder="Buscar por nombre o email..."
                  value={searchUsers}
                  onChange={(e) => setSearchUsers(e.target.value)}
                  className="pl-9"
                  data-testid="search-users-input"
                />
                {searchUsers && (
                  <button
                    onClick={() => setSearchUsers('')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
              <label className="flex items-center gap-2 text-sm text-zinc-600 cursor-pointer select-none" data-testid="show-inactive-label">
                <Checkbox
                  checked={showInactive}
                  onCheckedChange={(v) => setShowInactive(!!v)}
                  data-testid="show-inactive-checkbox"
                />
                Mostrar inactivos
              </label>
            </div>
          </div>

          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-zinc-900"></div>
            </div>
          ) : usersExpanded ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {users
                .filter(user => showInactive || user.active)
                .filter(user => {
                  if (!searchUsers.trim()) return true;
                  const search = searchUsers.toLowerCase();
                  return user.name?.toLowerCase().includes(search) || user.email?.toLowerCase().includes(search);
                })
                .map((user) => (
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
                      {isSuperAdmin(user.role) && (
                        <div className="text-xs text-purple-600 bg-purple-50 px-2 py-1 rounded font-medium">
                          Rol máximo del sistema
                        </div>
                      )}
                    </div>
                    <div className="flex gap-2 mt-4">
                      {canManageUser(user) ? (
                        <>
                          {canEditUser(user) && (
                            <Button variant="outline" size="sm" className="flex-1" onClick={() => openEditDialog(user)} data-testid="edit-user-button">
                              <Edit className="h-4 w-4 mr-1" />
                              Editar
                            </Button>
                          )}
                          {canEditUser(user) && !isTargetSuperAdmin(user) && (
                            <Button
                              variant="outline"
                              size="sm"
                              className={`flex-1 ${user.active ? 'text-red-600 hover:text-red-700 hover:bg-red-50' : 'text-green-600 hover:text-green-700 hover:bg-green-50'}`}
                              onClick={() => handleToggleActivo(user)}
                              data-testid="toggle-activo-button"
                            >
                              {user.active ? <XCircle className="h-4 w-4 mr-1" /> : <CheckCircle2 className="h-4 w-4 mr-1" />}
                              {user.active ? 'Inactivar' : 'Activar'}
                            </Button>
                          )}
                          {canEditUser(user) && !isTargetSuperAdmin(user) && (
                            <Button variant="outline" size="sm" className="flex-1" onClick={() => openPermissionsDialog(user)} data-testid="permissions-button">
                              <Settings className="h-4 w-4 mr-1" />
                              Permisos
                            </Button>
                          )}
                          {canDeleteUser(user) && (
                            <Button variant="outline" size="sm" className="flex-1" onClick={() => handleDelete(user.id)}
                              disabled={(isAdmin(user.role) && !isSuperAdmin(user.role) && users.filter(u => isAdmin(u.role) && !isSuperAdmin(u.role)).length === 1) ||
                                        (isSuperAdmin(user.role) && users.filter(u => isSuperAdmin(u.role)).length === 1)}
                              data-testid="delete-user-button">
                              <Trash2 className="h-4 w-4 mr-1" />
                              Eliminar
                            </Button>
                          )}
                        </>
                      ) : (
                        <div className="text-xs text-zinc-500 italic w-full text-center py-2">
                          No tiene permisos para gestionar este usuario
                        </div>
                      )}
                    </div>

                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            /* Vista de Lista (Contraída) */
            <div className="bg-white border rounded-lg overflow-hidden">
              <table className="w-full">
                <thead className="bg-zinc-50 border-b">
                  <tr>
                    <th className="text-left py-2 px-4 text-xs font-semibold text-zinc-600">Nombre</th>
                    <th className="text-left py-2 px-4 text-xs font-semibold text-zinc-600">Email</th>
                    <th className="text-left py-2 px-4 text-xs font-semibold text-zinc-600">Rol</th>
                    <th className="text-left py-2 px-4 text-xs font-semibold text-zinc-600">Estado</th>
                    <th className="text-right py-2 px-4 text-xs font-semibold text-zinc-600">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {users
                    .filter(user => showInactive || user.active)
                    .filter(user => {
                      if (!searchUsers.trim()) return true;
                      const search = searchUsers.toLowerCase();
                      return user.name?.toLowerCase().includes(search) || user.email?.toLowerCase().includes(search);
                    })
                    .map((user) => (
                    <tr key={user.id} className="border-b hover:bg-zinc-50">
                      <td className="py-2 px-4 text-sm font-medium">{user.name}</td>
                      <td className="py-2 px-4 text-sm text-zinc-600">{user.email}</td>
                      <td className="py-2 px-4">
                        <Badge className={`${getRoleBadge(user.role)} border text-xs`}>
                          {user.role}
                        </Badge>
                      </td>
                      <td className="py-2 px-4">
                        <span className={`text-xs ${user.active ? 'text-green-600' : 'text-red-600'}`}>
                          {user.active ? 'Activo' : 'Inactivo'}
                        </span>
                      </td>
                      <td className="py-2 px-4 text-right">
                        <div className="flex items-center justify-end gap-1">
                          {canEditUser(user) && (
                            <Button variant="ghost" size="sm" onClick={() => openEditDialog(user)}>
                              <Edit className="h-3 w-3" />
                            </Button>
                          )}
                          {canEditUser(user) && !isTargetSuperAdmin(user) && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className={user.active ? 'text-red-600 hover:text-red-700' : 'text-green-600 hover:text-green-700'}
                              title={user.active ? 'Inactivar usuario' : 'Activar usuario'}
                              onClick={() => handleToggleActivo(user)}
                              data-testid="toggle-activo-button-row"
                            >
                              {user.active ? <XCircle className="h-3 w-3" /> : <CheckCircle2 className="h-3 w-3" />}
                            </Button>
                          )}
                          {canEditUser(user) && !isTargetSuperAdmin(user) && (
                            <Button variant="ghost" size="sm" onClick={() => openPermissionsDialog(user)}>
                              <Settings className="h-3 w-3" />
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </TabsContent>
        )}

        {/* ============= TAB ROLES ============= */}
        {canViewTab('roles') && (
        <TabsContent value="roles" className="mt-6">
          <div className="flex flex-col gap-3 mb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <p className="text-sm text-zinc-600">{roles.length} rol(es) configurado(s)</p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setRolesExpanded(!rolesExpanded)}
                  className="flex items-center gap-1"
                  data-testid="toggle-roles-view"
                >
                  {rolesExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  {rolesExpanded ? 'Contraer' : 'Expandir'}
                </Button>
              </div>
              {canCreateRoles() && (
                <Button onClick={() => openRoleDialog()} className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800" data-testid="add-role-button">
                  <Plus className="h-4 w-4 mr-2" />
                  Nuevo Rol
                </Button>
              )}
            </div>
            {/* Campo de búsqueda */}
            <div className="relative max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
              <Input
                placeholder="Buscar por nombre de rol..."
                value={searchRoles}
                onChange={(e) => setSearchRoles(e.target.value)}
                className="pl-9"
                data-testid="search-roles-input"
              />
              {searchRoles && (
                <button
                  onClick={() => setSearchRoles('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>

          {rolesLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-zinc-900"></div>
            </div>
          ) : rolesExpanded ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {roles
                .filter(role => {
                  if (!searchRoles.trim()) return true;
                  const search = searchRoles.toLowerCase();
                  return role.nombre?.toLowerCase().includes(search) || role.descripcion?.toLowerCase().includes(search);
                })
                .map((role) => (
                <Card key={role.id} className="border border-zinc-200 shadow-sm" data-testid="role-card">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${getRoleBgClass(role.nombre)}`}>
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
                        {(() => {
                          const selectedIds = Array.from(new Set((role.permisos || []).map(String)));
                          const selectedSet = new Set(selectedIds);
                          const childrenByParentId = new Map();

                          modulos.forEach((modulo) => {
                            const parentRaw = modulo.modulo_padre_id ?? modulo.ModuloPadreID ?? modulo.moduloPadreId;
                            const parentId = parentRaw === null || parentRaw === undefined || parentRaw === '' ? null : String(parentRaw);

                            if (parentId) {
                              if (!childrenByParentId.has(parentId)) {
                                childrenByParentId.set(parentId, []);
                              }
                              childrenByParentId.get(parentId).push(modulo);
                            }
                          });

                          const displayPermissions = selectedIds.filter((permId) => {
                            const selectedChildren = childrenByParentId.get(String(permId)) || [];
                            return !selectedChildren.some((child) => selectedSet.has(String(child.id)));
                          });

                          return (
                            <>
                              <p className="text-xs font-medium text-zinc-500 mb-1">
                                Permisos ({displayPermissions.length}):
                              </p>
                              <div className="flex flex-wrap gap-1">
                                {displayPermissions.slice(0, 5).map((p) => {
                                  const modulo = modulos.find((m) => String(m.id) === String(p));
                                  return (
                                    <Badge key={p} variant="outline" className="text-xs">
                                      {modulo?.nombre || p}
                                    </Badge>
                                  );
                                })}
                                {displayPermissions.length > 5 && (
                                  <Badge variant="outline" className="text-xs bg-zinc-100">
                                    +{displayPermissions.length - 5} más
                                  </Badge>
                                )}
                              </div>
                            </>
                          );
                        })()}
                      </div>

                    <div className="flex gap-2">
                      {canEditRoles() && (
                        <Button variant="outline" size="sm" className="flex-1" onClick={() => openRoleDialog(role)} data-testid="edit-role-button">
                          <Edit className="h-4 w-4 mr-1" />
                          Editar
                        </Button>
                      )}
                      {canDeleteRoles() && !role.es_sistema && (
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
          ) : (
            /* Vista de Lista (Contraída) para Roles */
            <div className="bg-white border rounded-lg overflow-hidden">
              <table className="w-full">
                <thead className="bg-zinc-50 border-b">
                  <tr>
                    <th className="text-left py-2 px-4 text-xs font-semibold text-zinc-600">Rol</th>
                    <th className="text-left py-2 px-4 text-xs font-semibold text-zinc-600">Tipo</th>
                    <th className="text-left py-2 px-4 text-xs font-semibold text-zinc-600">Descripción</th>
                    <th className="text-left py-2 px-4 text-xs font-semibold text-zinc-600">Permisos</th>
                    <th className="text-right py-2 px-4 text-xs font-semibold text-zinc-600">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {roles
                    .filter(role => {
                      if (!searchRoles.trim()) return true;
                      const search = searchRoles.toLowerCase();
                      return role.nombre?.toLowerCase().includes(search) || role.descripcion?.toLowerCase().includes(search);
                    })
                    .map((role) => (
                    <tr key={role.id} className="border-b hover:bg-zinc-50">
                      <td className="py-2 px-4 text-sm font-medium">{role.nombre}</td>
                      <td className="py-2 px-4">
                        {role.es_sistema ? (
                          <Badge variant="outline" className="text-xs bg-amber-50 text-amber-700 border-amber-200">
                            <Lock className="h-3 w-3 mr-1" />
                            Sistema
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-xs">Personalizado</Badge>
                        )}
                      </td>
                      <td className="py-2 px-4 text-sm text-zinc-600 max-w-xs truncate">{role.descripcion || 'Sin descripción'}</td>
                      <td className="py-2 px-4">
                        <span className="text-xs text-zinc-500">{role.permisos?.length || 0} permiso(s)</span>
                      </td>
                      <td className="py-2 px-4 text-right">
                        <div className="flex items-center justify-end gap-1">
                          {canEditRoles() && (
                            <Button variant="ghost" size="sm" onClick={() => openRoleDialog(role)}>
                              <Edit className="h-3 w-3" />
                            </Button>
                          )}
                          {canDeleteRoles() && !role.es_sistema && (
                            <Button variant="ghost" size="sm" className="text-red-600" onClick={() => handleDeleteRole(role.id)}>
                              <Trash2 className="h-3 w-3" />
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </TabsContent>
        )}

        {/* ============= TAB PERMISOS CATÁLOGOS ============= */}
        {canViewTab('permisosCatalogos') && (
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
                            {isSuperAdmin(usuario.role) ? (
                              <Badge className="bg-amber-100 text-amber-700">👑 Acceso Total</Badge>
                            ) : (
                              <span className="text-xs text-zinc-500">
                                {(usuario.permisos_catalogos || []).length} catálogo(s)
                              </span>
                            )}
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
                        <div key={`aprobacion-${cat.codigo}-${i}`} className={`flex-1 h-1 rounded ${getNivelAprobacionClass(i)}`} />
                      ))}
                    </div>
                    <p className="text-xs text-zinc-400 mt-1">
                      {getNivelAprobacionDesc(cat.niveles_aprobacion)}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        )}

        {/* ============= TAB ESTRUCTURA ============= */}
        {canViewTab('estructura') && (
        <TabsContent value="estructura" className="mt-6" data-testid="estructura-content">
          <Card>
            <CardHeader className="py-4">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-medium flex items-center gap-2">
                  <Building2 className="h-5 w-5 text-indigo-500" />
                  Estructura Organizacional
                  <Badge variant="outline" className="ml-2 text-xs bg-green-50 text-green-600 border-green-200">
                    RBAC Activo
                  </Badge>
                </CardTitle>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={loadEstructura}
                  disabled={estructuraLoading}
                  data-testid="btn-cargar-estructura"
                >
                  <RefreshCw className={`h-4 w-4 mr-1 ${estructuraLoading ? 'animate-spin' : ''}`} />
                  {estructuraLoading ? 'Cargando...' : 'Cargar Estructura'}
                </Button>
              </div>
              <p className="text-xs text-zinc-500 mt-1">
                Vista informativa de la jerarquía: Empresa → Unidad de Negocio → Sucursal
              </p>
            </CardHeader>
            <CardContent>
              {!estructuraData ? (
                <div className="text-center py-12 text-zinc-500">
                  <Building2 className="h-12 w-12 mx-auto mb-4 opacity-30" />
                  <p>Presione "Cargar Estructura" para visualizar la topología organizacional</p>
                  <p className="text-xs mt-2">Este módulo es de solo lectura y no afecta el sistema actual</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Resumen */}
                  <div className="grid grid-cols-3 gap-4 mb-6">
                    <div className="bg-indigo-50 p-4 rounded-lg text-center">
                      <p className="text-2xl font-bold text-indigo-700">{estructuraData.total_empresas || 0}</p>
                      <p className="text-xs text-indigo-600">Empresas</p>
                    </div>
                    <div className="bg-purple-50 p-4 rounded-lg text-center">
                      <p className="text-2xl font-bold text-purple-700">
                        {estructuraData.empresas?.reduce((acc, e) => acc + (e.unidades_negocio?.length || 0), 0) || 0}
                      </p>
                      <p className="text-xs text-purple-600">Unidades de Negocio</p>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg text-center">
                      <p className="text-2xl font-bold text-green-700">
                        {estructuraData.empresas?.reduce((acc, e) =>
                          acc + (e.unidades_negocio?.reduce((acc2, u) => acc2 + (u.sucursales?.length || 0), 0) || 0), 0) || 0}
                      </p>
                      <p className="text-xs text-green-600">Sucursales</p>
                    </div>
                  </div>

                  {/* Árbol de estructura */}
                  <div className="border rounded-lg divide-y">
                    {(estructuraData.empresas || []).map((empresa) => (
                      <div key={empresa.id} className="p-4">
                        <div className="flex items-center gap-2 mb-3">
                          <div className="bg-indigo-100 p-2 rounded">
                            <Building2 className="h-5 w-5 text-indigo-600" />
                          </div>
                          <div>
                            <p className="font-semibold text-zinc-800">{empresa.nombre}</p>
                            <p className="text-xs text-zinc-500">Código: {empresa.codigo}</p>
                          </div>
                          <Badge variant="outline" className="ml-auto text-xs">
                            {empresa.unidades_negocio?.length || 0} unidades
                          </Badge>
                        </div>

                        {/* Unidades de negocio */}
                        <div className="ml-8 space-y-3">
                          {(empresa.unidades_negocio || []).map((unidad) => (
                            <div key={unidad.id} className="bg-zinc-50 p-3 rounded-lg">
                              <div className="flex items-center gap-2 mb-2">
                                <div className="bg-purple-100 p-1.5 rounded">
                                  <Warehouse className="h-4 w-4 text-purple-600" />
                                </div>
                                <div>
                                  <p className="font-medium text-sm text-zinc-700">{unidad.nombre}</p>
                                  <p className="text-xs text-zinc-500">
                                    {unidad.codigo} • {unidad.tipo_unidad || 'N/A'}
                                  </p>
                                </div>
                                <Badge variant="outline" className="ml-auto text-xs bg-white">
                                  {unidad.sucursales?.length || 0} sucursales
                                </Badge>
                              </div>

                              {/* Sucursales */}
                              {(unidad.sucursales || []).length > 0 && (
                                <div className="ml-6 mt-2 flex flex-wrap gap-2">
                                  {(unidad.sucursales || []).map((sucursal) => (
                                    <span
                                      key={sucursal.id}
                                      className="inline-flex items-center gap-1 px-2 py-1 bg-green-50 text-green-700 rounded text-xs border border-green-200"
                                    >
                                      <Server className="h-3 w-3" />
                                      {sucursal.nombre}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Información de mapeo (si existe) */}
                  {mapeoData && mapeoData.mapeos?.length > 0 && (
                    <div className="mt-6 border-t pt-4">
                      <p className="text-sm font-medium text-zinc-700 mb-3 flex items-center gap-2">
                        <Server className="h-4 w-4" />
                        Mapeo Servidor ↔ Sucursal ({mapeoData.total} registros)
                      </p>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                        {mapeoData.mapeos.slice(0, 9).map((m) => (
                          <div key={`${m.server_id}-${m.sucursal_id}`} className="text-xs bg-zinc-50 p-2 rounded flex items-center gap-2">
                            <Server className="h-3 w-3 text-blue-500" />
                            <span className="font-medium">{m.server_name || m.server_id}</span>
                            <span className="text-zinc-400">→</span>
                            <span className="text-zinc-600">{m.sucursal_id}</span>
                          </div>
                        ))}
                      </div>
                      {mapeoData.total > 9 && (
                        <p className="text-xs text-zinc-400 mt-2">
                          +{mapeoData.total - 9} mapeos adicionales
                        </p>
                      )}
                    </div>
                  )}

                  {/* Nota de estado */}
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3 mt-4">
                    <p className="text-xs text-green-700">
                      <strong>Estructura Organizacional:</strong> Esta información muestra la jerarquía de la empresa.
                      El filtrado de alcance RBAC ya está activo en los módulos piloto (Usuarios).
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        )}

        {/* ============= TAB BITÁCORA RBAC (FASE 12) ============= */}
        {canViewTab('bitacora') && (
          <TabsContent value="bitacora" className="mt-6" data-testid="bitacora-content">
            <BitacoraRBAC />
          </TabsContent>
        )}

      </Tabs>


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
              {/* SuperAdministrador tiene acceso total automático */}
              {isSuperAdmin(usuarioSeleccionadoCat?.role) ? (
                <div className="bg-gradient-to-r from-amber-50 to-yellow-50 border border-amber-200 rounded-lg p-6 text-center">
                  <div className="text-4xl mb-3">👑</div>
                  <h3 className="font-bold text-amber-800 text-lg mb-2">Acceso Total</h3>
                  <p className="text-amber-700 text-sm">
                    El SuperAdministrador tiene acceso completo al 100% de la aplicación
                    sin restricción alguna. No requiere configuración de permisos.
                  </p>
                  <div className="mt-4 flex flex-wrap justify-center gap-2">
                    <Badge className="bg-green-100 text-green-700">✓ Todos los catálogos</Badge>
                    <Badge className="bg-green-100 text-green-700">✓ Solicitar</Badge>
                    <Badge className="bg-green-100 text-green-700">✓ Autorizar</Badge>
                    <Badge className="bg-green-100 text-green-700">✓ Liberar</Badge>
                  </div>
                </div>
              ) : (
              <>
              <div className="space-y-3">
                <p className="text-xs font-semibold text-zinc-600 uppercase tracking-wide">Permisos de Flujo</p>

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

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="puede-autorizar"
                    checked={formPermisosCat.puede_autorizar}
                    onChange={(e) => setFormPermisosCat({...formPermisosCat, puede_autorizar: e.target.checked})}
                    className="h-4 w-4"
                  />
                  <Label htmlFor="puede-autorizar" className="cursor-pointer">
                    Puede autorizar altas (Nivel 1 - Aprobación)
                  </Label>
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="puede-liberar"
                    checked={formPermisosCat.puede_liberar}
                    onChange={(e) => setFormPermisosCat({...formPermisosCat, puede_liberar: e.target.checked})}
                    className="h-4 w-4"
                  />
                  <Label htmlFor="puede-liberar" className="cursor-pointer">
                    Puede liberar/activar altas (Nivel 2 - Sistemas)
                  </Label>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Catálogos Permitidos:</Label>
                <div className="grid grid-cols-2 gap-2 p-3 border rounded-lg max-h-[300px] overflow-y-auto">
                    {Object.entries(
                      catalogosDisponibles.reduce((acc, cat) => {
                        const modulo = cat.modulo || cat.TipoConfiguracion || cat.tipo_configuracion || 'Catálogos Workflow';
                        if (!acc[modulo]) {
                          acc[modulo] = [];
                        }
                        acc[modulo].push(cat);
                        return acc;
                      }, {})
                    ).map(([modulo, catalogos]) => (
                      <div key={modulo} className="col-span-2 rounded-lg border border-zinc-100 bg-zinc-50/60 p-2">
                        <p className="px-2 pb-2 text-sm font-semibold text-zinc-900">{modulo}</p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {catalogos.map((cat) => (
                            <label key={cat.id} className="flex items-center gap-2 p-2 hover:bg-white rounded cursor-pointer">
                              <input
                                type="checkbox"
                                checked={(formPermisosCat.catalogos_permitidos || []).map(String).includes(String(cat.id))}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    setFormPermisosCat({...formPermisosCat, catalogos_permitidos: Array.from(new Set([...(formPermisosCat.catalogos_permitidos || []).map(String), String(cat.id)]))});
                                  } else {
                                    setFormPermisosCat({...formPermisosCat, catalogos_permitidos: (formPermisosCat.catalogos_permitidos || []).filter(c => String(c) !== String(cat.id))});
                                  }
                                }}
                                className="h-4 w-4"
                              />
                              <div>
                                <span className="text-sm font-medium">{cat.nombre}</span>
                                <span className="text-xs text-zinc-500 block">{cat.descripcion || cat.codigo || cat.modulo}</span>
                              </div>
                            </label>
                          ))}
                        </div>
                      </div>
                    ))}
                </div>
              </div>
              </>
              )}
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
            <DialogDescription>
              {editMode
                ? 'Actualiza los datos del usuario. La contraseña solo cambia si capturas una nueva.'
                : 'Crea un nuevo usuario para el sistema.'}
            </DialogDescription>
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
              <PasswordInput
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                required={!editMode}
                maxLength={128}
                placeholder={editMode ? "Dejar vacío para mantener" : "••••••••"}
                data-testid="user-password-input"
              />
              {(!editMode || formData.password) && (
                <PasswordRules password={formData.password} compact />
              )}
            </div>
            <div className="space-y-2">
              <Label>Rol</Label>
              <Select value={formData.role} onValueChange={(v) => setFormData({...formData, role: v})}>
                <SelectTrigger data-testid="user-role-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {roles.length > 0 ? (
                    roles
                      .filter(role => {
                        // Si no es SuperAdministrador, no puede asignar ese rol
                        if (getRoleDefinitionLevel(role) >= 100 && !canAssignSuperAdmin()) {
                          return false;
                        }
                        return true;
                      })
                      .map((role) => (
                        <SelectItem key={role.id || role.nombre} value={role.nombre}>
                          {role.nombre}
                        </SelectItem>
                      ))
                  ) : (
                    <SelectItem value={formData.role || 'SIN_ROLES'} disabled>
                      No hay roles canónicos disponibles
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancelar</Button>
              <Button
                type="submit"
                className="bg-zinc-900 text-zinc-50"
                data-testid="submit-user-button"
              >
                {editMode ? 'Guardar cambios' : 'Crear usuario'}
              </Button>
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
                  {(() => {
                    const byId = new Map(modulos.map((modulo) => [String(modulo.id), modulo]));
                    const childrenByParent = new Map();
                    const roots = [];

                    modulos.forEach((modulo) => {
                      const parentRaw = modulo.modulo_padre_id ?? modulo.ModuloPadreID ?? modulo.moduloPadreId;
                      const parentId = parentRaw === null || parentRaw === undefined || parentRaw === '' ? null : String(parentRaw);

                      if (parentId && byId.has(parentId)) {
                        if (!childrenByParent.has(parentId)) {
                          childrenByParent.set(parentId, []);
                        }
                        childrenByParent.get(parentId).push(modulo);
                      } else {
                        roots.push(modulo);
                      }
                    });

                    const renderPermissionItem = (modulo, compactLabel = null) => (
                      <div key={`perm-item-${modulo.id}`} className="flex items-start gap-2 p-2 rounded hover:bg-zinc-50">
                        <Checkbox
                          id={`perm-${modulo.id}`}
                          checked={roleFormData.permisos.includes(String(modulo.id))}
                          onCheckedChange={() => togglePermiso(String(modulo.id))}
                        />
                        <label htmlFor={`perm-${modulo.id}`} className="cursor-pointer">
                          <span className="text-sm font-medium">{compactLabel || modulo.nombre}</span>
                          <p className="text-xs text-zinc-500">{modulo.descripcion}</p>
                        </label>
                      </div>
                    );

                    return roots.map((grupo) => {
                      const children = childrenByParent.get(String(grupo.id)) || [];
                      const hasOwnAssignablePermission =
                        Boolean(grupo.ruta) ||
                        Boolean(grupo.tiene_permiso_menu_propio) ||
                        Boolean(grupo.tienePermisoMenuPropio) ||
                        roleFormData.permisos.includes(String(grupo.id));

                      if (children.length === 0) {
                        return renderPermissionItem(grupo);
                      }

                      return (
                        <div
                          key={`grupo-${grupo.id}`}
                          className="col-span-2 md:col-span-3 rounded-lg border border-zinc-100 bg-zinc-50/60 p-2"
                        >
                          <div className="px-2 pb-2">
                            <p className="text-sm font-semibold text-zinc-900">{grupo.nombre}</p>
                            <p className="text-xs text-zinc-500">{grupo.descripcion}</p>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                            {hasOwnAssignablePermission && renderPermissionItem(grupo, 'Acceso general')}
                            {children.map((child) => renderPermissionItem(child))}
                          </div>
                        </div>
                      );
                    });
                  })()}
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
