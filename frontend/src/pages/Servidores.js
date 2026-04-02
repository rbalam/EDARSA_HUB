import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Plus, Edit, Trash2, Database, Settings, Loader2, Check, Filter, Code, CheckCircle2, AlertCircle, Wifi, WifiOff } from 'lucide-react';
import { toast } from 'sonner';
import QueryConfigWizard from '@/components/QueryConfigWizard';
import { formatNombreSucursal } from '@/lib/formatSucursal';

const Servidores = () => {
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [queryWizardOpen, setQueryWizardOpen] = useState(false);
  const [selectedServer, setSelectedServer] = useState(null);
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionValid, setConnectionValid] = useState(false);
  
  // Estado para ping de servidores
  const [pingStatus, setPingStatus] = useState({}); // { server_id: { status, message, loading } }
  
  // Estado para modo edición
  const [editingServer, setEditingServer] = useState(null);
  
  // Listas de opciones desde SQL Server
  const [tiposMovimiento, setTiposMovimiento] = useState([]);
  const [categorias, setCategorias] = useState([]);
  const [departamentos, setDepartamentos] = useState([]);
  const [loadingOptions, setLoadingOptions] = useState(false);
  
  const [formData, setFormData] = useState({
    name: '',
    host: '',
    port: 1433,
    database: '',
    username: '',
    password: '',
    system_type: 'MPRO',
    date_calculation_method: 'inventory_dates',
    sucursales: [],
    tipos_movimiento: [],
    categorias: [],
    departamentos: []
  });

  // Estado para los filtros seleccionados en configuración
  const [selectedFilters, setSelectedFilters] = useState({
    tipos_movimiento: [],
    categorias: [],
    departamentos: []
  });

  useEffect(() => {
    loadServers();
  }, []);

  // Ping automático cuando se cargan los servidores (silencioso, con delay entre cada uno)
  useEffect(() => {
    if (servers.length > 0) {
      // Hacer ping silencioso con delay para no parecer ataque
      const pingWithDelay = async () => {
        for (let i = 0; i < servers.length; i++) {
          const server = servers[i];
          if (!pingStatus[server.id]) {
            pingServerSilent(server.id);
            // Esperar 4 segundos entre cada ping (excepto el último)
            if (i < servers.length - 1) {
              await new Promise(resolve => setTimeout(resolve, 4000));
            }
          }
        }
      };
      
      // Iniciar después de 2 segundos de cargar la página
      const timeoutId = setTimeout(pingWithDelay, 2000);
      return () => clearTimeout(timeoutId);
    }
  }, [servers]);

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

  // Ping silencioso (para auto-ping al cargar, sin toasts ni errores que rompan la UI)
  const pingServerSilent = async (serverId) => {
    setPingStatus(prev => ({
      ...prev,
      [serverId]: { loading: true, status: null, message: 'Verificando...' }
    }));
    
    try {
      const response = await api.get(`/servers/${serverId}/ping`, { timeout: 10000 }); // 10s timeout
      const data = response.data;
      
      setPingStatus(prev => ({
        ...prev,
        [serverId]: {
          loading: false,
          status: data.status,
          message: data.message,
          responseTime: data.response_time_ms,
          serverTime: data.server_time
        }
      }));
    } catch (error) {
      // Silencioso - no mostrar toast, solo actualizar estado
      setPingStatus(prev => ({
        ...prev,
        [serverId]: {
          loading: false,
          status: 'error',
          message: 'Sin conexión'
        }
      }));
    }
  };

  // Función para hacer ping a un servidor (con toasts para acción manual)
  const pingServer = async (serverId) => {
    setPingStatus(prev => ({
      ...prev,
      [serverId]: { loading: true, status: null, message: 'Probando conexión...' }
    }));
    
    try {
      const response = await api.get(`/servers/${serverId}/ping`);
      const data = response.data;
      
      setPingStatus(prev => ({
        ...prev,
        [serverId]: {
          loading: false,
          status: data.status,
          message: data.message,
          responseTime: data.response_time_ms,
          serverTime: data.server_time
        }
      }));
      
      if (data.status === 'connected') {
        toast.success(`${data.server_name}: Conectado en ${data.response_time_ms}ms`);
      } else {
        toast.error(`${data.server_name}: ${data.message}`);
      }
    } catch (error) {
      setPingStatus(prev => ({
        ...prev,
        [serverId]: {
          loading: false,
          status: 'error',
          message: error.response?.data?.detail || 'Error de conexión'
        }
      }));
      toast.error('Error al probar conexión');
    }
  };

  // Función para hacer ping a todos los servidores
  const pingAllServers = async () => {
    for (const server of servers) {
      await pingServer(server.id);
    }
  };

  const testConnection = async () => {
    if (!formData.host || !formData.database || !formData.username || !formData.password) {
      toast.error('Completa todos los campos de conexión');
      return;
    }
    
    setTestingConnection(true);
    setConnectionValid(false);
    
    try {
      let response;
      
      if (editingServer) {
        // Modo edición: actualizar servidor existente
        const updateData = { ...formData };
        // Si la contraseña está vacía, no actualizarla (mantener la existente)
        if (!updateData.password) {
          delete updateData.password;
        }
        response = await api.put(`/servers/${editingServer.id}`, updateData);
        toast.success('Servidor actualizado correctamente');
        setDialogOpen(false);
        loadServers();
        resetForm();
      } else {
        // Modo creación: crear nuevo servidor
        response = await api.post('/servers', formData);
        setConnectionValid(true);
        toast.success('Conexión exitosa');
        
        // Guardar el servidor creado
        const newServerId = response.data.id;
        setSelectedServer({ ...response.data, id: newServerId });
        
        // Cargar las opciones de filtros
        await loadFilterOptions(newServerId);
        
        setDialogOpen(false);
        loadServers();
        
        // Abrir el diálogo de configuración
        setConfigDialogOpen(true);
      }
      
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error de conexión');
      setConnectionValid(false);
    } finally {
      setTestingConnection(false);
    }
  };

  const loadFilterOptions = async (serverId) => {
    setLoadingOptions(true);
    try {
      const [tiposRes, categoriasRes, departamentosRes] = await Promise.all([
        api.get(`/servers/${serverId}/tipos-movimiento`),
        api.get(`/servers/${serverId}/categorias`),
        api.get(`/servers/${serverId}/departamentos`)
      ]);
      
      setTiposMovimiento(tiposRes.data);
      setCategorias(categoriasRes.data);
      setDepartamentos(departamentosRes.data);
      
      // Si el servidor ya tiene filtros configurados, cargarlos
      const server = servers.find(s => s.id === serverId) || selectedServer;
      if (server) {
        setSelectedFilters({
          tipos_movimiento: server.tipos_movimiento || [],
          categorias: server.categorias || [],
          departamentos: server.departamentos || []
        });
      }
      
    } catch (error) {
      console.error('Error cargando opciones de filtros:', error);
      toast.error('Error al cargar opciones de filtros');
    } finally {
      setLoadingOptions(false);
    }
  };

  const openConfigDialog = async (server) => {
    setSelectedServer(server);
    setSelectedFilters({
      tipos_movimiento: server.tipos_movimiento || [],
      categorias: server.categorias || [],
      departamentos: server.departamentos || []
    });
    setConfigDialogOpen(true);
    await loadFilterOptions(server.id);
  };

  const saveFilters = async () => {
    if (!selectedServer) return;
    
    try {
      await api.put(`/servers/${selectedServer.id}`, {
        tipos_movimiento: selectedFilters.tipos_movimiento,
        categorias: selectedFilters.categorias,
        departamentos: selectedFilters.departamentos
      });
      
      toast.success('Filtros guardados correctamente');
      setConfigDialogOpen(false);
      loadServers();
    } catch (error) {
      toast.error('Error al guardar filtros');
    }
  };

  const toggleFilter = (type, codigo) => {
    setSelectedFilters(prev => {
      const current = prev[type] || [];
      const isSelected = current.includes(codigo);
      
      return {
        ...prev,
        [type]: isSelected 
          ? current.filter(c => c !== codigo)
          : [...current, codigo]
      };
    });
  };

  const selectAll = (type, items) => {
    setSelectedFilters(prev => ({
      ...prev,
      [type]: items.map(item => item.codigo)
    }));
  };

  const deselectAll = (type) => {
    setSelectedFilters(prev => ({
      ...prev,
      [type]: []
    }));
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
      date_calculation_method: 'inventory_dates',
      sucursales: [],
      tipos_movimiento: [],
      categorias: [],
      departamentos: []
    });
    setConnectionValid(false);
    setEditingServer(null);
  };

  // Función para abrir el diálogo de edición con los datos del servidor
  const openEditDialog = (server) => {
    setFormData({
      name: server.name || '',
      host: server.host || '',
      port: server.port || 1433,
      database: server.database || '',
      username: server.username || '',
      password: '', // No mostramos la contraseña por seguridad
      system_type: server.system_type || 'MPRO',
      date_calculation_method: server.date_calculation_method || 'inventory_dates',
      sucursales: server.sucursales || [],
      tipos_movimiento: server.tipos_movimiento || [],
      categorias: server.categorias || [],
      departamentos: server.departamentos || []
    });
    setEditingServer(server);
    setConnectionValid(false);
    setDialogOpen(true);
  };

  const getFilterCount = (server) => {
    const tiposCount = server.tipos_movimiento?.length || 0;
    const catCount = server.categorias?.length || 0;
    const deptCount = server.departamentos?.length || 0;
    return tiposCount + catCount + deptCount;
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
        <div className="flex gap-2">
          <Button 
            onClick={pingAllServers}
            variant="outline"
            className="border-blue-200 text-blue-700 hover:bg-blue-50"
          >
            <Wifi className="h-4 w-4 mr-2" />
            Ping Todos
          </Button>
          <Button 
            onClick={() => {
              resetForm();
              setDialogOpen(true);
            }}
            className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800"
            data-testid="add-server-button"
          >
            <Plus className="h-4 w-4 mr-2" />
            Agregar Servidor
          </Button>
        </div>
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
                    <div className="relative">
                      <div className="bg-blue-50 p-2 rounded-lg">
                        <Database className="h-5 w-5 text-blue-600" />
                      </div>
                      {/* Indicador de estado Online/Offline */}
                      {pingStatus[server.id]?.loading ? (
                        <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-yellow-400 animate-pulse border-2 border-white" title="Verificando..." />
                      ) : pingStatus[server.id]?.status === 'connected' ? (
                        <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-green-500 border-2 border-white" title="Online" />
                      ) : pingStatus[server.id]?.status ? (
                        <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-red-500 border-2 border-white" title="Offline" />
                      ) : (
                        <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-zinc-300 border-2 border-white" title="Sin verificar" />
                      )}
                    </div>
                    <div>
                      <CardTitle className="text-lg font-semibold">{formatNombreSucursal(server.name)}</CardTitle>
                      <p className="text-xs text-zinc-500 mt-1">{server.system_type}</p>
                    </div>
                  </div>
                  {/* Botón de estado Online/Offline */}
                  {pingStatus[server.id]?.loading ? (
                    <Button
                      variant="outline"
                      size="sm"
                      disabled
                      className="h-7 px-3 text-xs border-blue-200 text-blue-600"
                    >
                      <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                      Probando...
                    </Button>
                  ) : pingStatus[server.id]?.status === 'connected' ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => pingServer(server.id)}
                      className="h-7 px-3 text-xs bg-green-50 border-green-300 text-green-700 hover:bg-green-100"
                      title={`Conectado en ${pingStatus[server.id]?.responseTime}ms`}
                    >
                      <Wifi className="h-3 w-3 mr-1" />
                      Online ({pingStatus[server.id]?.responseTime}ms)
                    </Button>
                  ) : pingStatus[server.id]?.status ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => pingServer(server.id)}
                      className="h-7 px-3 text-xs bg-red-50 border-red-300 text-red-700 hover:bg-red-100"
                      title={pingStatus[server.id]?.message}
                    >
                      <WifiOff className="h-3 w-3 mr-1" />
                      Offline
                    </Button>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => pingServer(server.id)}
                      className="h-7 px-3 text-xs border-zinc-200 text-zinc-500 hover:bg-zinc-50"
                    >
                      <Wifi className="h-3 w-3 mr-1" />
                      Ping
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-zinc-600">Host:</span>
                    <span className="font-mono text-zinc-900 text-xs truncate max-w-[180px]">{server.host}</span>
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
                  
                  {/* Mostrar estado de consultas SQL */}
                  <div className="pt-2 border-t border-zinc-100">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-zinc-500">Consultas SQL:</span>
                      {server.queries_configured ? (
                        <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 text-xs">
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                          Configuradas
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="bg-orange-50 text-orange-700 border-orange-200 text-xs">
                          <AlertCircle className="h-3 w-3 mr-1" />
                          Pendientes
                        </Badge>
                      )}
                    </div>
                  </div>
                  
                  {/* Mostrar estado de filtros */}
                  <div className="pt-2 border-t border-zinc-100">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-zinc-500">Filtros configurados:</span>
                      <span className={`text-xs font-medium ${getFilterCount(server) > 0 ? 'text-green-600' : 'text-orange-500'}`}>
                        {getFilterCount(server) > 0 ? `${getFilterCount(server)} activos` : 'Sin configurar'}
                      </span>
                    </div>
                    {getFilterCount(server) > 0 && (
                      <div className="mt-1 text-xs text-zinc-600">
                        <span className="inline-block bg-zinc-100 rounded px-1.5 py-0.5 mr-1">
                          Mov: {server.tipos_movimiento?.length || 0}
                        </span>
                        <span className="inline-block bg-zinc-100 rounded px-1.5 py-0.5 mr-1">
                          Cat: {server.categorias?.length || 0}
                        </span>
                        <span className="inline-block bg-zinc-100 rounded px-1.5 py-0.5">
                          Dept: {server.departamentos?.length || 0}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="flex flex-col gap-2 mt-4">
                  {/* Botón principal: Configurar Consultas SQL */}
                  <Button 
                    variant={server.queries_configured ? "outline" : "default"}
                    size="sm" 
                    className={server.queries_configured ? "" : "bg-blue-600 hover:bg-blue-700 text-white"}
                    onClick={() => {
                      setSelectedServer(server);
                      setQueryWizardOpen(true);
                    }}
                    data-testid="config-queries-button"
                  >
                    <Code className="h-4 w-4 mr-1" />
                    {server.queries_configured ? 'Editar Consultas SQL' : 'Configurar Consultas SQL'}
                  </Button>
                  
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => openEditDialog(server)}
                      data-testid="edit-server-button"
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="flex-1"
                      onClick={() => openConfigDialog(server)}
                      data-testid="config-server-button"
                    >
                      <Filter className="h-4 w-4 mr-1" />
                      Filtros
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleDelete(server.id)}
                      data-testid="delete-server-button"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Add/Edit Server Dialog */}
      <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{editingServer ? 'Editar Servidor' : 'Agregar Nuevo Servidor'}</DialogTitle>
            <DialogDescription>
              {editingServer ? 'Modifica los parámetros de conexión' : 'Configura la conexión a un servidor SQL'}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
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
                <Label htmlFor="password">
                  Contraseña
                  {editingServer && <span className="text-xs text-zinc-400 ml-2">(dejar vacío para mantener)</span>}
                </Label>
                <Input
                  id="password"
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  required={!editingServer}
                  placeholder={editingServer ? '••••••••' : ''}
                  data-testid="server-password-input"
                />
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
              <p className="text-xs text-blue-900 font-medium mb-1">Cálculo automático de fechas:</p>
              <ul className="text-xs text-blue-800 space-y-1">
                <li>• <strong>MPRO:</strong> Usa fechas exactas de inventarios inicial y final</li>
                <li>• <strong>SoftRestaurant:</strong> Fecha inicial +1 seg, fecha final -1 seg</li>
              </ul>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancelar
              </Button>
              <Button 
                onClick={testConnection}
                disabled={testingConnection}
                className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800" 
                data-testid="submit-server-button"
              >
                {testingConnection ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    {editingServer ? 'Guardando...' : 'Conectando...'}
                  </>
                ) : (
                  <>
                    <Database className="h-4 w-4 mr-2" />
                    {editingServer ? 'Guardar Cambios' : 'Conectar y Configurar'}
                  </>
                )}
              </Button>
            </DialogFooter>
          </div>
        </DialogContent>
      </Dialog>

      {/* Configuration Dialog */}
      <Dialog open={configDialogOpen} onOpenChange={setConfigDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Configurar Filtros - {selectedServer?.name}
            </DialogTitle>
            <DialogDescription>
              Selecciona los tipos de movimiento, categorías y departamentos que deseas incluir en los análisis de inventario
            </DialogDescription>
          </DialogHeader>
          
          {loadingOptions ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
              <span className="ml-2 text-zinc-600">Cargando opciones...</span>
            </div>
          ) : (
            <Tabs defaultValue="tipos" className="flex-1 overflow-hidden flex flex-col">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="tipos" className="flex items-center gap-2">
                  Tipos de Movimiento
                  <span className="bg-zinc-200 text-zinc-700 text-xs px-1.5 py-0.5 rounded">
                    {selectedFilters.tipos_movimiento.length}/{tiposMovimiento.length}
                  </span>
                </TabsTrigger>
                <TabsTrigger value="categorias" className="flex items-center gap-2">
                  Categorías
                  <span className="bg-zinc-200 text-zinc-700 text-xs px-1.5 py-0.5 rounded">
                    {selectedFilters.categorias.length}/{categorias.length}
                  </span>
                </TabsTrigger>
                <TabsTrigger value="departamentos" className="flex items-center gap-2">
                  Departamentos
                  <span className="bg-zinc-200 text-zinc-700 text-xs px-1.5 py-0.5 rounded">
                    {selectedFilters.departamentos.length}/{departamentos.length}
                  </span>
                </TabsTrigger>
              </TabsList>
              
              <TabsContent value="tipos" className="flex-1 overflow-auto mt-4">
                <div className="flex gap-2 mb-4">
                  <Button size="sm" variant="outline" onClick={() => selectAll('tipos_movimiento', tiposMovimiento)}>
                    Seleccionar todos
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => deselectAll('tipos_movimiento')}>
                    Deseleccionar todos
                  </Button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-[400px] overflow-y-auto pr-2">
                  {tiposMovimiento.map((tipo) => (
                    <div 
                      key={tipo.codigo} 
                      className={`flex items-center space-x-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedFilters.tipos_movimiento.includes(tipo.codigo)
                          ? 'bg-blue-50 border-blue-300'
                          : 'bg-white border-zinc-200 hover:border-zinc-300'
                      }`}
                      onClick={() => toggleFilter('tipos_movimiento', tipo.codigo)}
                    >
                      <Checkbox 
                        checked={selectedFilters.tipos_movimiento.includes(tipo.codigo)}
                        onCheckedChange={() => toggleFilter('tipos_movimiento', tipo.codigo)}
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm bg-zinc-100 px-2 py-0.5 rounded">
                            {tipo.codigo}
                          </span>
                          <span className={`text-xs px-1.5 py-0.5 rounded ${
                            (tipo.tipo === '+' || tipo.tipo === 'EN') ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                          }`}>
                            {(tipo.tipo === '+' || tipo.tipo === 'EN') ? 'Entrada' : 'Salida'}
                          </span>
                        </div>
                        <p className="text-sm text-zinc-700 mt-1">{tipo.descripcion}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </TabsContent>
              
              <TabsContent value="categorias" className="flex-1 overflow-auto mt-4">
                <div className="flex gap-2 mb-4">
                  <Button size="sm" variant="outline" onClick={() => selectAll('categorias', categorias)}>
                    Seleccionar todos
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => deselectAll('categorias')}>
                    Deseleccionar todos
                  </Button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 max-h-[400px] overflow-y-auto pr-2">
                  {categorias.map((cat) => (
                    <div 
                      key={cat.codigo} 
                      className={`flex items-center space-x-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedFilters.categorias.includes(cat.codigo)
                          ? 'bg-green-50 border-green-300'
                          : 'bg-white border-zinc-200 hover:border-zinc-300'
                      }`}
                      onClick={() => toggleFilter('categorias', cat.codigo)}
                    >
                      <Checkbox 
                        checked={selectedFilters.categorias.includes(cat.codigo)}
                        onCheckedChange={() => toggleFilter('categorias', cat.codigo)}
                      />
                      <div className="flex-1">
                        <span className="font-mono text-xs bg-zinc-100 px-2 py-0.5 rounded">
                          {cat.codigo}
                        </span>
                        <p className="text-sm text-zinc-700 mt-1">{cat.descripcion}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </TabsContent>
              
              <TabsContent value="departamentos" className="flex-1 overflow-auto mt-4">
                <div className="flex gap-2 mb-4">
                  <Button size="sm" variant="outline" onClick={() => selectAll('departamentos', departamentos)}>
                    Seleccionar todos
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => deselectAll('departamentos')}>
                    Deseleccionar todos
                  </Button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 max-h-[400px] overflow-y-auto pr-2">
                  {departamentos.map((dept) => (
                    <div 
                      key={dept.codigo} 
                      className={`flex items-center space-x-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedFilters.departamentos.includes(dept.codigo)
                          ? 'bg-purple-50 border-purple-300'
                          : 'bg-white border-zinc-200 hover:border-zinc-300'
                      }`}
                      onClick={() => toggleFilter('departamentos', dept.codigo)}
                    >
                      <Checkbox 
                        checked={selectedFilters.departamentos.includes(dept.codigo)}
                        onCheckedChange={() => toggleFilter('departamentos', dept.codigo)}
                      />
                      <div className="flex-1">
                        <span className="font-mono text-xs bg-zinc-100 px-2 py-0.5 rounded">
                          {dept.codigo}
                        </span>
                        <p className="text-sm text-zinc-700 mt-1">{dept.descripcion}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </TabsContent>
            </Tabs>
          )}

          <DialogFooter className="mt-4 pt-4 border-t">
            <div className="flex items-center justify-between w-full">
              <div className="text-sm text-zinc-600">
                <span className="font-medium">Resumen:</span>
                <span className="ml-2">{selectedFilters.tipos_movimiento.length} tipos</span>
                <span className="mx-1">•</span>
                <span>{selectedFilters.categorias.length} categorías</span>
                <span className="mx-1">•</span>
                <span>{selectedFilters.departamentos.length} departamentos</span>
              </div>
              <div className="flex gap-2">
                <Button type="button" variant="outline" onClick={() => setConfigDialogOpen(false)}>
                  Cancelar
                </Button>
                <Button 
                  onClick={saveFilters}
                  className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800"
                  data-testid="save-filters-button"
                >
                  <Check className="h-4 w-4 mr-2" />
                  Guardar Configuración
                </Button>
              </div>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Query Configuration Wizard */}
      <QueryConfigWizard
        open={queryWizardOpen}
        onClose={() => setQueryWizardOpen(false)}
        server={selectedServer}
        onComplete={() => loadServers()}
      />
    </div>
  );
};

export default Servidores;
