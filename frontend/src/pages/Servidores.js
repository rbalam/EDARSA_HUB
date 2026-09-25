import logger from '../services/logger';
import { useEffect, useState, useCallback, useRef } from 'react';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Plus, Edit, Trash2, Database, Settings, Loader2, Check, Filter, Code, CheckCircle2, AlertCircle, Wifi, WifiOff, Globe, Link2, Clock, Zap, Building2, Eye, EyeOff, RefreshCw, GripVertical, TestTube2, AlertTriangle, Play, Table2, LayoutGrid, List, Minus, Maximize2, X, Move, Mail, History, ScrollText, User } from 'lucide-react';
import { toast } from 'sonner';
import QueryConfigWizard from '@/components/QueryConfigWizard';
import UniversalQueryTester from '@/components/UniversalQueryTester';
import { formatNombreSucursal } from '@/lib/formatSucursal';

// Helper: Renderiza indicador de estado del servidor
const StatusIndicator = ({ pingStatus }) => {
  if (pingStatus?.loading) {
    return <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-yellow-400 animate-pulse border-2 border-white" title="Verificando..." />;
  }
  if (pingStatus?.status === 'connected') {
    return <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-green-500 border-2 border-white" title="Online" />;
  }
  if (pingStatus?.status) {
    return <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-red-500 border-2 border-white" title="Offline" />;
  }
  return <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-zinc-300 border-2 border-white" title="Sin verificar" />;
};

// Helper: Renderiza botón de estado del servidor
const StatusButton = ({ pingStatus, serverId, onPing }) => {
  if (pingStatus?.loading) {
    return (
      <Button variant="outline" size="sm" disabled className="h-7 px-3 text-xs border-blue-200 text-blue-600">
        <Loader2 className="h-3 w-3 mr-1 animate-spin" />
        Probando...
      </Button>
    );
  }
  if (pingStatus?.status === 'connected') {
    return (
      <Button
        variant="outline"
        size="sm"
        onClick={() => onPing(serverId)}
        className="h-7 px-3 text-xs bg-green-50 border-green-300 text-green-700 hover:bg-green-100"
        title={`Conectado en ${pingStatus?.responseTime}ms`}
      >
        <Wifi className="h-3 w-3 mr-1" />
        Online ({pingStatus?.responseTime}ms)
      </Button>
    );
  }
  if (pingStatus?.status) {
    return (
      <Button
        variant="outline"
        size="sm"
        onClick={() => onPing(serverId)}
        className="h-7 px-3 text-xs bg-red-50 border-red-300 text-red-700 hover:bg-red-100"
      >
        <WifiOff className="h-3 w-3 mr-1" />
        Offline
      </Button>
    );
  }
  return (
    <Button
      variant="outline"
      size="sm"
      onClick={() => onPing(serverId)}
      className="h-7 px-3 text-xs border-zinc-200 text-zinc-600 hover:bg-zinc-100"
    >
      <Wifi className="h-3 w-3 mr-1" />
      Probar
    </Button>
  );
};

const Servidores = () => {
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [queryWizardOpen, setQueryWizardOpen] = useState(false);
  const [selectedServer, setSelectedServer] = useState(null);
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionValid, setConnectionValid] = useState(false);
  
  // Estado para UniversalQueryTester
  const [universalTestOpen, setUniversalTestOpen] = useState(false);
  const [serverForUniversalTest, setServerForUniversalTest] = useState(null);
  const [universalTestConnectionType, setUniversalTestConnectionType] = useState('sql');  // 'sql' | 'api'
  
  // Estado para configuración de sucursales
  const [sucursalesConfigOpen, setSucursalesConfigOpen] = useState(false);
  const [sucursalesConfig, setSucursalesConfig] = useState([]);
  const [loadingSucursalesConfig, setLoadingSucursalesConfig] = useState(false);
  const [syncingSucursales, setSyncingSucursales] = useState(false);
  const [serverForSucursales, setServerForSucursales] = useState(null);
  
  // Estado para el tab activo (SQL Servers o Conexiones API)
  const [activeMainTab, setActiveMainTab] = useState('sql');

  // ========== ESTADO BITÁCORA ADMIN CORE ==========
  const [coreAuditLog, setCoreAuditLog] = useState([]);
  const [loadingCoreAudit, setLoadingCoreAudit] = useState(false);

  // Cargar bitácora de acciones CORE (lectura SQL-First de Servidores_Conexiones_Log)
  const loadCoreAuditLog = useCallback(async () => {
    setLoadingCoreAudit(true);
    try {
      const response = await api.get('/admin/core-connections/audit-log', { params: { limit: 100 } });
      setCoreAuditLog(response.data?.data || []);
    } catch (error) {
      console.error('Error cargando bitácora CORE:', error);
      toast.error('Error al cargar la bitácora de conexiones');
      setCoreAuditLog([]);
    } finally {
      setLoadingCoreAudit(false);
    }
  }, []);

  // Cargar bitácora cuando se abre su tab (lazy)
  useEffect(() => {
    if (activeMainTab === 'bitacora') {
      loadCoreAuditLog();
    }
  }, [activeMainTab, loadCoreAuditLog]);
  
  // Estado para Conexiones API
  const [apiConnections, setApiConnections] = useState([]);
  const [loadingApis, setLoadingApis] = useState(false);
  const [apiDialogOpen, setApiDialogOpen] = useState(false);
  const [editingApi, setEditingApi] = useState(null);
  const [apiFormData, setApiFormData] = useState({
    name: '',
    url: '',
    api_key: '',
    tipo: 'MPRO',
    servidor_padre: '',
    servidor_padre_id: '',
    sucursal_destino: '',
    hora_replica: '04:00',
    solo_ventas_dia: true,
    activo: true,
    visible_en_operaciones: false
  });
  
  // Estado para sección de consulta de prueba en el modal de conexión API
  // CONSULTA DEFAULT para nuevas conexiones: prueba técnica básica
  const DEFAULT_SQL_QUERY = 'SELECT TOP 1 name FROM sys.tables ORDER BY name';
  
  const [queryTestData, setQueryTestData] = useState({
    tipo_uso: 'Otro',
    nombre_consulta: '',
    sql_query: DEFAULT_SQL_QUERY,
    timeout: 30
  });
  const [testingQuery, setTestingQuery] = useState(false);
  const [queryTestResult, setQueryTestResult] = useState(null);
  
  // Tipos de uso disponibles
  const TIPOS_USO = ['Ventas del día', 'Inventario', 'Cortes', 'Compras', 'Otro'];
  
  // Estado para vista compacta (APIs y Servidores SQL)
  const [apiViewMode, setApiViewMode] = useState('cards'); // 'cards' | 'list'
  const [sqlViewMode, setSqlViewMode] = useState('cards'); // 'cards' | 'list'
  
  // Estado para modal arrastrable (API y SQL)
  const [apiModalPosition, setApiModalPosition] = useState({ x: 0, y: 0 });
  const [sqlModalPosition, setSqlModalPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [apiModalMinimized, setApiModalMinimized] = useState(false);
  const [sqlModalMinimized, setSqlModalMinimized] = useState(false);
  
  // ========== ESTADO VTIGER CRM ==========
  const [vtigerConnections, setVtigerConnections] = useState([]);
  const [loadingVtiger, setLoadingVtiger] = useState(false);
  const [vtigerDialogOpen, setVtigerDialogOpen] = useState(false);
  const [editingVtiger, setEditingVtiger] = useState(null);
  const [vtigerFormData, setVtigerFormData] = useState({
    name: 'Vtiger CRM',
    base_url: '',
    username: '',
    access_key: '',
    sync_modules: ['Leads', 'Contacts', 'Accounts', 'Potentials'],
    sync_direction: 'bidirectional',
    active: true
  });
  const [testingVtiger, setTestingVtiger] = useState(false);
  const [vtigerTestResult, setVtigerTestResult] = useState(null);
  const [vtigerTestStatus, setVtigerTestStatus] = useState({}); // { connection_id: { status, message, loading } }
  
  // Estado para tipos de sistema (cargados desde catálogo)
  const [tiposSistema, setTiposSistema] = useState([]);
  const [loadingTiposSistema, setLoadingTiposSistema] = useState(false);
  const [permisosSistemas, setPermisosSistemas] = useState({
    puede_crear: false,
    puede_solicitar: false,
    mostrar_nuevo: false
  });
  
  // Estado para modal de nuevo tipo de sistema
  const [nuevoSistemaModalOpen, setNuevoSistemaModalOpen] = useState(false);
  const [nuevoSistemaDescripcion, setNuevoSistemaDescripcion] = useState('');
  const [creandoSistema, setCreandoSistema] = useState(false);
  
  // Cargar tipos de sistema desde catálogo
  // FASE 7: Usa Catálogo Maestro con fallback a catálogo legacy
  const loadTiposSistema = async () => {
    setLoadingTiposSistema(true);
    try {
      // FASE 7: Intentar primero el Catálogo Maestro
      const response = await api.get('/catalogos/sistemas-capacidades');
      
      if (response.data.success && response.data.data) {
        // Transformar respuesta del Catálogo Maestro al formato esperado
        const sistemas = response.data.data.map(s => ({
          Codigo: s.codigo_sistema,
          Descripcion: s.nombre_sistema
        }));
        setTiposSistema(sistemas);
        // Catálogo Maestro no tiene permisos de crear nuevos, usar defaults
        setPermisosSistemas({
          puede_crear: false,
          puede_solicitar: false,
          mostrar_nuevo: false
        });
        return;
      }
    } catch (catalogoMaestroError) {
      console.warn('Catálogo Maestro no disponible, usando legacy:', catalogoMaestroError);
    }
    
    // Fallback: Usar catálogo legacy
    try {
      const response = await api.get('/catalogos/sistemas/activos');
      if (response.data.success && response.data.data) {
        setTiposSistema(response.data.data);
        // Guardar permisos del usuario
        if (response.data.permisos) {
          setPermisosSistemas(response.data.permisos);
        }
      }
    } catch (error) {
      console.error('Error cargando tipos de sistema:', error);
      // Fallback final a valores hardcodeados (último recurso)
      setTiposSistema([
        { Codigo: 'MPRO', Descripcion: 'ManagementPro (MPRO)' },
        { Codigo: 'SOFTRESTAURANT', Descripcion: 'SoftRestaurant' },
        { Codigo: 'API_LOCAL', Descripcion: 'API Local (Enterprise)' },
        { Codigo: 'OTRO', Descripcion: 'Otro' }
      ]);
    } finally {
      setLoadingTiposSistema(false);
    }
  };
  
  // Crear o solicitar nuevo tipo de sistema
  const handleCrearNuevoSistema = async () => {
    if (!nuevoSistemaDescripcion.trim()) {
      toast.error('La descripción es obligatoria');
      return;
    }
    
    setCreandoSistema(true);
    try {
      // Si puede crear, crear directamente. Si solo puede solicitar, solicitar.
      const endpoint = permisosSistemas.puede_crear 
        ? '/catalogos/sistemas' 
        : '/catalogos/sistemas/solicitar';
      
      const response = await api.post(endpoint, {
        datos: {
          Descripcion: nuevoSistemaDescripcion.trim()
        }
      });
      
      if (response.data.success) {
        if (permisosSistemas.puede_crear) {
          // Sistema creado exitosamente, refrescar combo y seleccionar el nuevo
          toast.success('Sistema creado exitosamente');
          await loadTiposSistema();
          // Seleccionar el nuevo sistema en el formulario
          if (response.data.codigo) {
            setFormData(prev => ({ ...prev, system_type: response.data.codigo }));
          }
        } else {
          // Solicitud enviada
          toast.success('Solicitud enviada para autorización');
        }
        setNuevoSistemaModalOpen(false);
        setNuevoSistemaDescripcion('');
      } else {
        toast.error(response.data.message || 'Error al procesar la solicitud');
      }
    } catch (error) {
      console.error('Error creando sistema:', error);
      toast.error(error.response?.data?.detail || 'Error al crear/solicitar sistema');
    } finally {
      setCreandoSistema(false);
    }
  };
  
  // Manejar selección del combo de tipo de sistema
  const handleTipoSistemaChange = (value) => {
    if (value === '__NUEVO__') {
      setNuevoSistemaModalOpen(true);
    } else {
      setFormData({ ...formData, system_type: value });
    }
  };
  
  // Manejar selección del combo de tipo de sistema (para API)
  const handleTipoSistemaApiChange = (value) => {
    if (value === '__NUEVO__') {
      setNuevoSistemaModalOpen(true);
    } else {
      setApiFormData({ ...apiFormData, tipo: value });
    }
  };
  
  // Cargar conexiones API desde backend
  const loadApiConnections = async () => {
    setLoadingApis(true);
    try {
      const response = await api.get('/api-connections');
      if (response.data.success) {
        // Formatear hora_replica a string "HH:00"
        const formatted = response.data.data.map(conn => ({
          ...conn,
          hora_replica: typeof conn.hora_replica === 'number' 
            ? `${String(conn.hora_replica).padStart(2, '0')}:00`
            : conn.hora_replica
        }));
        setApiConnections(formatted);
      }
    } catch (error) {
      console.error('Error cargando conexiones API:', error);
      // SECURITY P0: sin fallback hardcodeado. No inventar conexiones ni exponer IPs reales.
      setApiConnections([]);
      toast.error('No se pudieron cargar las conexiones API locales.');
    } finally {
      setLoadingApis(false);
    }
  };
  
  // ========== FUNCIONES VTIGER CRM ==========
  
  // Cargar conexiones Vtiger desde backend
  const loadVtigerConnections = async () => {
    setLoadingVtiger(true);
    try {
      const response = await api.get('/vtiger/connections');
      if (response.data.connections) {
        setVtigerConnections(response.data.connections);
      }
    } catch (error) {
      console.error('Error cargando conexiones Vtiger:', error);
      setVtigerConnections([]);
    } finally {
      setLoadingVtiger(false);
    }
  };
  
  // Probar conexión Vtiger
  const testVtigerConnection = async (connectionId) => {
    setVtigerTestStatus(prev => ({
      ...prev,
      [connectionId]: { loading: true, status: null, message: 'Probando conexión...' }
    }));
    
    try {
      const response = await api.post(`/vtiger/connections/${connectionId}/test`);
      
      if (response.data.success) {
        setVtigerTestStatus(prev => ({
          ...prev,
          [connectionId]: {
            loading: false,
            status: 'success',
            message: `✅ Conectado (${response.data.response_time_ms}ms)`,
            user: response.data.user_info
          }
        }));
        toast.success('Vtiger: Conexión exitosa');
      } else {
        setVtigerTestStatus(prev => ({
          ...prev,
          [connectionId]: {
            loading: false,
            status: 'error',
            message: `❌ ${response.data.message || 'Error de conexión'}`
          }
        }));
        toast.error(`Vtiger: ${response.data.message}`);
      }
    } catch (error) {
      setVtigerTestStatus(prev => ({
        ...prev,
        [connectionId]: {
          loading: false,
          status: 'error',
          message: `❌ Error: ${error.response?.data?.detail || error.message}`
        }
      }));
      toast.error('Error probando conexión Vtiger');
    }
  };
  
  // Guardar conexión Vtiger (crear o actualizar)
  const saveVtigerConnection = async () => {
    setTestingVtiger(true);
    try {
      if (editingVtiger) {
        // Actualizar
        await api.put(`/vtiger/connections/${editingVtiger.id}`, vtigerFormData);
        toast.success('Conexión Vtiger actualizada');
      } else {
        // Crear nueva
        await api.post('/vtiger/connections', vtigerFormData);
        toast.success('Conexión Vtiger creada');
      }
      
      setVtigerDialogOpen(false);
      setEditingVtiger(null);
      loadVtigerConnections();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error guardando conexión');
    } finally {
      setTestingVtiger(false);
    }
  };
  
  // Eliminar conexión Vtiger
  const deleteVtigerConnection = async (connectionId) => {
    if (!window.confirm('¿Está seguro de eliminar esta conexión?')) return;
    
    try {
      await api.delete(`/vtiger/connections/${connectionId}`);
      toast.success('Conexión eliminada');
      loadVtigerConnections();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error eliminando conexión');
    }
  };
  
  // Abrir modal para editar Vtiger
  const openEditVtiger = (conn) => {
    setEditingVtiger(conn);
    setVtigerFormData({
      name: conn.name || 'Vtiger CRM',
      base_url: conn.base_url || '',
      username: conn.username || '',
      access_key: '', // No mostrar el key existente por seguridad
      sync_modules: conn.sync_modules || ['Leads', 'Contacts', 'Accounts', 'Potentials'],
      sync_direction: conn.sync_direction || 'bidirectional',
      active: conn.active !== false
    });
    setVtigerDialogOpen(true);
  };
  
  // Abrir modal para nueva conexión Vtiger
  const openNewVtiger = () => {
    setEditingVtiger(null);
    setVtigerFormData({
      name: 'Vtiger CRM',
      base_url: '',
      username: '',
      access_key: '',
      sync_modules: ['Leads', 'Contacts', 'Accounts', 'Potentials'],
      sync_direction: 'bidirectional',
      active: true
    });
    setVtigerTestResult(null);
    setVtigerDialogOpen(true);
  };
  
  // Probar conexión desde el formulario (antes de guardar)
  const testVtigerFromForm = async () => {
    setTestingVtiger(true);
    setVtigerTestResult(null);
    
    try {
      const response = await api.post('/vtiger/test', vtigerFormData);
      
      setVtigerTestResult({
        success: response.data.success,
        message: response.data.message,
        user: response.data.user_info,
        responseTime: response.data.response_time_ms
      });
      
      if (response.data.success) {
        toast.success('Conexión verificada correctamente');
      } else {
        toast.error(response.data.message);
      }
    } catch (error) {
      setVtigerTestResult({
        success: false,
        message: error.response?.data?.detail || error.message
      });
      toast.error('Error de conexión');
    } finally {
      setTestingVtiger(false);
    }
  };
  
  // Estado para ping de servidores
  const [pingStatus, setPingStatus] = useState({}); // { server_id: { status, message, loading } }
  
  // Estado para testing de APIs locales
  const [apiTestStatus, setApiTestStatus] = useState({}); // { api_id: { status: 'success'|'warning'|'error', message, loading } }
  
  // Función para probar conexión de API local
  // Usa endpoint /test-connectivity que NO requiere permisos estrictos por EmpresaID
  const testApiConnection = async (apiConn) => {
    setApiTestStatus(prev => ({
      ...prev,
      [apiConn.id]: { loading: true, status: null, message: 'Probando conexión...' }
    }));
    
    try {
      // El backend de test-connectivity puede esperar hasta 30s. Este request usa
      // un margen propio para no heredar el timeout global de 15s y marcar falsos Error.
      const response = await api.post(
        `/api-connections/${apiConn.id}/test-connectivity`,
        {},
        { timeout: 40000 }
      );
      
      if (response.data.success) {
        if (response.data.sql_connected) {
          setApiTestStatus(prev => ({
            ...prev,
            [apiConn.id]: { 
              loading: false, 
              status: 'success', 
              message: `✅ ${response.data.message || 'API y SQL Server conectados'}` 
            }
          }));
          toast.success(`${apiConn.name}: Conexión exitosa`);
        } else {
          setApiTestStatus(prev => ({
            ...prev,
            [apiConn.id]: { 
              loading: false, 
              status: 'warning', 
              message: `⚠️ API responde pero SQL Server no disponible: ${response.data.sql_error || 'Error desconocido'}` 
            }
          }));
          toast.warning(`${apiConn.name}: API OK pero SQL Server no disponible`);
        }
      } else {
        const errorText = response.data.sql_error || response.data.message || 'Error de conexión';
        setApiTestStatus(prev => ({
          ...prev,
          [apiConn.id]: { 
            loading: false, 
            status: 'error', 
            message: `❌ ${errorText.substring(0, 100)}` 
          }
        }));
        toast.error(`${apiConn.name}: ${errorText.substring(0, 100)}`);
      }
    } catch (error) {
      let errorMsg = 'Error de conexión';
      if (error.response?.status === 404) {
        errorMsg = 'Conexión no encontrada';
      } else if (error.response?.status === 400) {
        const detail = error.response?.data?.detail;
        errorMsg = typeof detail === 'string' ? detail : 'Conexión inválida';
      } else if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        errorMsg = typeof detail === 'string' ? detail : JSON.stringify(detail);
      } else if (error.message) {
        errorMsg = error.message;
      }
      setApiTestStatus(prev => ({
        ...prev,
        [apiConn.id]: { 
          loading: false, 
          status: 'error', 
          message: `❌ ${errorMsg.substring(0, 150)}` 
        }
      }));
      toast.error(`${apiConn.name}: ${errorMsg.substring(0, 100)}`);
    }
  };
  
  /**
   * Ejecuta una consulta SQL de prueba contra una conexión API.
   * Si la conexión ya existe (editingApi), usa el endpoint test-query.
   * Si es nueva, usa test-query-draft con URL y API key manuales.
   */
  const executeTestQuery = async () => {
    if (!queryTestData.sql_query.trim()) {
      toast.error('Ingresa una consulta SQL');
      return;
    }
    
    setTestingQuery(true);
    setQueryTestResult(null);
    
    try {
      let response;
      
      if (editingApi?.id) {
        // Conexión existente: usar credenciales guardadas
        response = await api.post(`/api-connections/${editingApi.id}/test-query`, {
          sql_query: queryTestData.sql_query,
          tipo_uso: queryTestData.tipo_uso,
          nombre_consulta: queryTestData.nombre_consulta,
          timeout: queryTestData.timeout
        });
      } else {
        // Conexión nueva: usar URL y API key del formulario
        if (!apiFormData.url) {
          toast.error('Configura primero la URL del endpoint');
          setTestingQuery(false);
          return;
        }
        response = await api.post('/api-connections/test-query-draft', {
          url: apiFormData.url,
          api_key: apiFormData.api_key || undefined,
          sql_query: queryTestData.sql_query,
          timeout: queryTestData.timeout
        });
      }
      
      setQueryTestResult(response.data);
      
      if (response.data.success) {
        toast.success(`Consulta ejecutada: ${response.data.rows_count || 0} filas`);
      } else if (response.data.sql_blocked) {
        toast.error('SQL bloqueado: ' + (response.data.validation_errors?.[0] || 'Consulta no permitida'));
      } else {
        toast.error(response.data.error || 'Error ejecutando consulta');
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message || 'Error de conexión';
      setQueryTestResult({
        success: false,
        error: errorMsg
      });
      toast.error(errorMsg);
    } finally {
      setTestingQuery(false);
    }
  };
  
  // Función para probar todas las APIs
  const testAllApis = async () => {
    for (const apiConn of apiConnections) {
      if (apiConn.activo) {
        await testApiConnection(apiConn);
      }
    }
  };
  
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
    departamentos: [],
    visible_en_operaciones: true
  });

  // Estado para los filtros seleccionados en configuración
  const [selectedFilters, setSelectedFilters] = useState({
    tipos_movimiento: [],
    categorias: [],
    departamentos: []
  });

  useEffect(() => {
    loadServers();
    loadApiConnections();  // Cargar conexiones API desde backend
    loadTiposSistema();    // Cargar tipos de sistema desde catálogo
    loadVtigerConnections(); // Cargar conexiones Vtiger
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
    // Note: pingStatus and pingServerSilent are intentionally omitted to prevent infinite loops
    // This effect runs once when servers load, not on every status update
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [servers]);

  // Probar APIs locales automáticamente al cargar
  useEffect(() => {
    if (apiConnections.length > 0) {
      const testApisWithDelay = async () => {
        for (let i = 0; i < apiConnections.length; i++) {
          const apiConn = apiConnections[i];
          if (!apiTestStatus[apiConn.id] && apiConn.activo) {
            await testApiConnection(apiConn);
            // Esperar 2 segundos entre cada test
            if (i < apiConnections.length - 1) {
              await new Promise(resolve => setTimeout(resolve, 2000));
            }
          }
        }
      };
      
      // Iniciar después de 3 segundos de cargar las APIs
      const timeoutId = setTimeout(testApisWithDelay, 3000);
      return () => clearTimeout(timeoutId);
    }
    // Note: apiTestStatus and testApiConnection are intentionally omitted to prevent infinite loops
    // This effect runs once when apiConnections load, not on every status update
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [apiConnections]);

  // ========== FUNCIONES DE DRAG PARA MODALES ==========
  // Usar refs para almacenar setPosition callback actual
  const currentSetPositionRef = useRef(null);
  
  const handleDragStart = (e, setPosition) => {
    // Solo permitir drag desde el header (no desde inputs, buttons, etc.)
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'BUTTON' || 
        e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT' ||
        e.target.closest('button') || e.target.closest('input')) {
      return;
    }
    e.preventDefault();
    setIsDragging(true);
    currentSetPositionRef.current = setPosition;
    
    // Guardar offset desde donde se hizo click respecto al centro actual del modal
    setDragOffset({
      x: e.clientX,
      y: e.clientY
    });
  };

  // Usar useEffect para manejar drag globalmente
  useEffect(() => {
    const handleGlobalMouseMove = (e) => {
      if (!isDragging || !currentSetPositionRef.current) return;
      
      const deltaX = e.clientX - dragOffset.x;
      const deltaY = e.clientY - dragOffset.y;
      
      currentSetPositionRef.current(prev => ({
        x: prev.x + deltaX,
        y: prev.y + deltaY
      }));
      
      setDragOffset({
        x: e.clientX,
        y: e.clientY
      });
    };

    const handleGlobalMouseUp = () => {
      setIsDragging(false);
      currentSetPositionRef.current = null;
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleGlobalMouseMove);
      document.addEventListener('mouseup', handleGlobalMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleGlobalMouseMove);
      document.removeEventListener('mouseup', handleGlobalMouseUp);
    };
  }, [isDragging, dragOffset]);

  const handleDrag = useCallback((e, setPosition) => {
    // Ya no se usa - el drag se maneja globalmente
  }, []);

  const handleDragEnd = () => {
    setIsDragging(false);
    currentSetPositionRef.current = null;
  };

  // Reset posición cuando se cierra el modal
  const resetApiModalPosition = () => {
    setApiModalPosition({ x: 0, y: 0 });
    setApiModalMinimized(false);
    setApiDialogOpen(false);
  };

  const resetSqlModalPosition = () => {
    setSqlModalPosition({ x: 0, y: 0 });
    setSqlModalMinimized(false);
    setDialogOpen(false);
  };

  // Restaurar al centro
  const centerApiModal = () => {
    setApiModalPosition({ x: 0, y: 0 });
  };

  const centerSqlModal = () => {
    setSqlModalPosition({ x: 0, y: 0 });
  };

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

  // Toggle visibilidad en operaciones
  const toggleVisibilidadOperaciones = async (server) => {
    try {
      const newValue = server.visible_en_operaciones === false ? true : false;
      await api.put(`/servers/${server.id}`, { visible_en_operaciones: newValue });
      toast.success(newValue ? 'Servidor visible en operaciones' : 'Servidor oculto en operaciones');
      loadServers();
    } catch (error) {
      toast.error('Error al cambiar visibilidad');
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
      logger.error('Error cargando opciones de filtros:', error);
      toast.error('Error al cargar opciones de filtros');
    } finally {
      setLoadingOptions(false);
    }
  };

  // ============ FUNCIONES PARA CONFIGURACIÓN DE SUCURSALES ============
  
  const openSucursalesConfig = async (server) => {
    setServerForSucursales(server);
    setSucursalesConfigOpen(true);
    await loadSucursalesConfig(server.id);
  };

  const loadSucursalesConfig = async (serverId) => {
    setLoadingSucursalesConfig(true);
    try {
      const response = await api.get(`/servers/${serverId}/sucursales-config`);
      setSucursalesConfig(response.data.sucursales || []);
    } catch (error) {
      logger.error('Error cargando config de sucursales:', error);
      toast.error('Error al cargar configuración de sucursales');
      setSucursalesConfig([]);
    } finally {
      setLoadingSucursalesConfig(false);
    }
  };

  const syncSucursalesFromSQL = async () => {
    if (!serverForSucursales) return;
    
    setSyncingSucursales(true);
    try {
      const response = await api.post(`/servers/${serverForSucursales.id}/sucursales-config/sync`);
      toast.success(response.data.message || 'Sucursales sincronizadas');
      setSucursalesConfig(response.data.sucursales || []);
    } catch (error) {
      logger.error('Error sincronizando sucursales:', error);
      toast.error('Error al sincronizar sucursales desde SQL Server');
    } finally {
      setSyncingSucursales(false);
    }
  };

  const toggleSucursalVisibility = async (sucursalOrigenId, currentVisible) => {
    if (!serverForSucursales) return;
    
    try {
      await api.put(`/servers/${serverForSucursales.id}/sucursales-config/${sucursalOrigenId}`, {
        visible_en_operaciones: !currentVisible
      });
      
      // Actualizar estado local
      setSucursalesConfig(prev => prev.map(s => 
        s.sucursal_origen_id === sucursalOrigenId 
          ? {...s, visible_en_operaciones: !currentVisible}
          : s
      ));
      
      toast.success(!currentVisible ? 'Sucursal visible en operaciones' : 'Sucursal oculta en operaciones');
    } catch (error) {
      logger.error('Error cambiando visibilidad:', error);
      toast.error('Error al cambiar visibilidad');
    }
  };

  const saveSucursalesOrder = async () => {
    if (!serverForSucursales) return;
    
    try {
      const updates = sucursalesConfig.map((s, idx) => ({
        sucursal_origen_id: s.sucursal_origen_id,
        orden: idx
      }));
      
      await api.put(`/servers/${serverForSucursales.id}/sucursales-config/bulk`, {
        sucursales: updates
      });
      
      toast.success('Orden guardado');
    } catch (error) {
      logger.error('Error guardando orden:', error);
      toast.error('Error al guardar orden');
    }
  };

  // ============ FIN FUNCIONES PARA CONFIGURACIÓN DE SUCURSALES ============

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
            Servidores
          </h1>
          <p className="text-zinc-600 mt-1">Gestiona las conexiones a bases de datos y APIs</p>
        </div>
      </div>

      {/* Tabs principales: SQL Servers | Conexiones API | Vtiger CRM */}
      <Tabs value={activeMainTab} onValueChange={setActiveMainTab} className="w-full">
        <TabsList className="grid w-full max-w-2xl grid-cols-4 mb-6">
          <TabsTrigger value="sql" className="flex items-center gap-2">
            <Database className="h-4 w-4" />
            SQL Servers
          </TabsTrigger>
          <TabsTrigger value="api" className="flex items-center gap-2">
            <Globe className="h-4 w-4" />
            Conexiones API
          </TabsTrigger>
          <TabsTrigger value="vtiger" className="flex items-center gap-2">
            <Link2 className="h-4 w-4" />
            Vtiger CRM
          </TabsTrigger>
          <TabsTrigger value="bitacora" className="flex items-center gap-2" data-testid="tab-bitacora-core">
            <History className="h-4 w-4" />
            Bitácora
          </TabsTrigger>
        </TabsList>

        {/* Tab: SQL Servers */}
        <TabsContent value="sql">
          <div className="flex items-center justify-end mb-4 gap-2">
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

          {/* Selector de vista SQL */}
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm text-zinc-500">
              {servers.length} servidores SQL
            </span>
            <div className="flex items-center gap-1 bg-zinc-100 rounded-lg p-1">
              <Button
                variant={sqlViewMode === 'cards' ? 'default' : 'ghost'}
                size="sm"
                className={`h-7 px-3 ${sqlViewMode === 'cards' ? 'bg-white shadow-sm' : ''}`}
                onClick={() => setSqlViewMode('cards')}
              >
                <LayoutGrid className="h-4 w-4 mr-1" />
                Tarjetas
              </Button>
              <Button
                variant={sqlViewMode === 'list' ? 'default' : 'ghost'}
                size="sm"
                className={`h-7 px-3 ${sqlViewMode === 'list' ? 'bg-white shadow-sm' : ''}`}
                onClick={() => setSqlViewMode('list')}
              >
                <List className="h-4 w-4 mr-1" />
                Lista
              </Button>
            </div>
          </div>

          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-zinc-900"></div>
            </div>
          ) : (
            <>
            {/* VISTA LISTA COMPACTA - SERVIDORES SQL */}
            {sqlViewMode === 'list' && (
              <div className="border border-zinc-200 rounded-lg overflow-hidden mb-4">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-zinc-50 border-b border-zinc-200">
                      <tr>
                        <th className="px-3 py-2 text-left font-medium text-zinc-600">Estado</th>
                        <th className="px-3 py-2 text-left font-medium text-zinc-600">Nombre</th>
                        <th className="px-3 py-2 text-left font-medium text-zinc-600">Sistema</th>
                        <th className="px-3 py-2 text-left font-medium text-zinc-600">Host:Puerto</th>
                        <th className="px-3 py-2 text-left font-medium text-zinc-600">Base de datos</th>
                        <th className="px-3 py-2 text-left font-medium text-zinc-600">Visible Op.</th>
                        <th className="px-3 py-2 text-left font-medium text-zinc-600">Activo</th>
                        <th className="px-3 py-2 text-right font-medium text-zinc-600">Acciones</th>
                      </tr>
                    </thead>
                    <tbody>
                      {servers.map((server) => (
                        <tr key={server.id} className="border-b border-zinc-100 hover:bg-zinc-50">
                          {/* Estado */}
                          <td className="px-3 py-2">
                            {pingStatus[server.id]?.loading ? (
                              <span className="inline-flex items-center gap-1 text-blue-600">
                                <Loader2 className="h-3 w-3 animate-spin" />
                                <span className="text-xs">Ping...</span>
                              </span>
                            ) : pingStatus[server.id]?.online ? (
                              <span className="inline-flex items-center gap-1 text-green-600">
                                <Wifi className="h-3 w-3" />
                                <span className="text-xs">Online</span>
                              </span>
                            ) : pingStatus[server.id]?.error ? (
                              <span className="inline-flex items-center gap-1 text-red-600">
                                <WifiOff className="h-3 w-3" />
                                <span className="text-xs">Offline</span>
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 text-zinc-400">
                                <Clock className="h-3 w-3" />
                                <span className="text-xs">Desconocido</span>
                              </span>
                            )}
                          </td>
                          {/* Nombre */}
                          <td className="px-3 py-2 font-medium text-zinc-800">{formatNombreSucursal(server.name)}</td>
                          {/* Sistema */}
                          <td className="px-3 py-2">
                            <Badge variant="outline" className="text-xs">{server.system_type}</Badge>
                          </td>
                          {/* Host:Puerto */}
                          <td className="px-3 py-2 text-zinc-600 text-xs font-mono max-w-40 truncate" title={`${server.host}:${server.port}`}>
                            {server.host ? `${server.host.substring(0, 25)}${server.host.length > 25 ? '...' : ''}:${server.port}` : '-'}
                          </td>
                          {/* Base de datos */}
                          <td className="px-3 py-2 text-zinc-600 text-xs">{server.database || '-'}</td>
                          {/* Visible Operaciones */}
                          <td className="px-3 py-2">
                            {server.visible_en_operaciones ? (
                              <span className="text-green-600 text-xs">Sí</span>
                            ) : (
                              <span className="text-zinc-400 text-xs">No</span>
                            )}
                          </td>
                          {/* Activo */}
                          <td className="px-3 py-2">
                            {server.activo !== false ? (
                              <span className="text-green-600 text-xs">Sí</span>
                            ) : (
                              <span className="text-zinc-400 text-xs">No</span>
                            )}
                          </td>
                          {/* Acciones */}
                          <td className="px-3 py-2">
                            <div className="flex items-center justify-end gap-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-7 w-7 p-0"
                                onClick={() => pingServer(server.id)}
                                disabled={pingStatus[server.id]?.loading}
                                title="Probar conexión SQL"
                              >
                                {pingStatus[server.id]?.loading ? (
                                  <Loader2 className="h-3 w-3 animate-spin" />
                                ) : (
                                  <Wifi className="h-3 w-3" />
                                )}
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-7 w-7 p-0"
                                onClick={() => {
                                  setEditingServer(server);
                                  setFormData({
                                    name: server.name || '',
                                    host: server.host || '',
                                    port: server.port || 1433,
                                    database: server.database || '',
                                    username: server.username || '',
                                    password: '',
                                    system_type: server.system_type || '',
                                    activo: server.activo !== false,
                                    visible_en_operaciones: server.visible_en_operaciones || false
                                  });
                                  setDialogOpen(true);
                                }}
                                title="Editar servidor"
                              >
                                <Edit className="h-3 w-3" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-7 w-7 p-0"
                                onClick={() => {
                                  setServerForUniversalTest(server);
                                  setUniversalTestConnectionType('sql');
                                  setUniversalTestOpen(true);
                                }}
                                title="Test Universal"
                              >
                                <TestTube2 className="h-3 w-3" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {servers.length === 0 && (
                  <div className="text-center py-8 text-zinc-500">
                    No hay servidores SQL configurados
                  </div>
                )}
              </div>
            )}

            {/* VISTA TARJETAS - SERVIDORES SQL */}
            {sqlViewMode === 'cards' && (
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
                      <StatusIndicator pingStatus={pingStatus[server.id]} />
                    </div>
                    <div>
                      <CardTitle className="text-lg font-semibold">{formatNombreSucursal(server.name)}</CardTitle>
                      <p className="text-xs text-zinc-500 mt-1">{server.system_type}</p>
                    </div>
                  </div>
                  {/* Botón de estado Online/Offline */}
                  <StatusButton 
                    pingStatus={pingStatus[server.id]} 
                    serverId={server.id} 
                    onPing={pingServer} 
                  />
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
                  
                  {/* Mostrar visibilidad en operaciones */}
                  <div className="pt-2 border-t border-zinc-100">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-zinc-500">Visible en Operaciones:</span>
                      <button
                        onClick={() => toggleVisibilidadOperaciones(server)}
                        className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                          server.visible_en_operaciones !== false ? 'bg-green-500' : 'bg-zinc-300'
                        }`}
                        title={server.visible_en_operaciones !== false ? 'Visible en dashboards' : 'Oculto en dashboards'}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                            server.visible_en_operaciones !== false ? 'translate-x-4' : 'translate-x-0.5'
                          }`}
                        />
                      </button>
                    </div>
                    <p className="text-xs text-zinc-400 mt-1">
                      {server.visible_en_operaciones !== false 
                        ? 'Aparece en reportes, compras, comercial, etc.' 
                        : 'Solo visible aquí para administración'}
                    </p>
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
                  
                  {/* Botón Test Universal SQL/API */}
                  <Button 
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setServerForUniversalTest(server);
                      setUniversalTestConnectionType('sql');
                      setUniversalTestOpen(true);
                    }}
                    data-testid="universal-test-button"
                  >
                    <TestTube2 className="h-4 w-4 mr-1" />
                    Test Universal
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
                  
                  {/* Botón para configurar sucursales visibles (solo MPRO) */}
                  {server.system_type === 'MPRO' && (
                    <Button 
                      variant="outline" 
                      size="sm"
                      className="w-full border-blue-200 text-blue-700 hover:bg-blue-50"
                      onClick={() => openSucursalesConfig(server)}
                      data-testid="config-sucursales-button"
                    >
                      <Building2 className="h-4 w-4 mr-1" />
                      Sucursales Visibles
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
        )}
        </>
      )}
        </TabsContent>

        {/* Tab: Conexiones API */}
        <TabsContent value="api">
          <div className="flex items-center justify-end mb-4 gap-2">
            <Button 
              onClick={() => {
                setEditingApi(null);
                setApiFormData({
                  name: '',
                  url: '',
                  api_key: '',
                  tipo: 'MPRO',
                  servidor_padre: '',
                  sucursal_destino: '',
                  hora_replica: '04:00',
                  solo_ventas_dia: true,
                  activo: true,
                  visible_en_operaciones: false
                });
                setQueryTestData({
                  tipo_uso: 'Otro',
                  nombre_consulta: '',
                  sql_query: DEFAULT_SQL_QUERY,
                  timeout: 30
                });
                setQueryTestResult(null);
                setApiDialogOpen(true);
              }}
              className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800"
            >
              <Plus className="h-4 w-4 mr-2" />
              Agregar Conexión API
            </Button>
            <Button 
              onClick={testAllApis}
              variant="outline"
              className="border-purple-200 text-purple-700 hover:bg-purple-50"
            >
              <Zap className="h-4 w-4 mr-2" />
              Probar Todas
            </Button>
          </div>

          {/* Info Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <h4 className="font-semibold text-blue-900">Conexiones API Locales</h4>
                <p className="text-sm text-blue-800 mt-1">
                  Estas conexiones obtienen las <strong>ventas del día en tiempo real</strong> desde servidores locales. 
                  Los datos se replican al servidor en la nube por la noche, evitando duplicación automáticamente.
                </p>
              </div>
            </div>
          </div>

          {/* Selector de vista */}
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm text-zinc-500">
              {apiConnections.length} conexiones API
            </span>
            <div className="flex items-center gap-1 bg-zinc-100 rounded-lg p-1">
              <Button
                variant={apiViewMode === 'cards' ? 'default' : 'ghost'}
                size="sm"
                className={`h-7 px-3 ${apiViewMode === 'cards' ? 'bg-white shadow-sm' : ''}`}
                onClick={() => setApiViewMode('cards')}
              >
                <LayoutGrid className="h-4 w-4 mr-1" />
                Tarjetas
              </Button>
              <Button
                variant={apiViewMode === 'list' ? 'default' : 'ghost'}
                size="sm"
                className={`h-7 px-3 ${apiViewMode === 'list' ? 'bg-white shadow-sm' : ''}`}
                onClick={() => setApiViewMode('list')}
              >
                <List className="h-4 w-4 mr-1" />
                Lista
              </Button>
            </div>
          </div>

          {/* VISTA LISTA COMPACTA - APIs */}
          {apiViewMode === 'list' && (
            <div className="border border-zinc-200 rounded-lg overflow-hidden mb-4">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-zinc-50 border-b border-zinc-200">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium text-zinc-600">Estado</th>
                      <th className="px-3 py-2 text-left font-medium text-zinc-600">Nombre</th>
                      <th className="px-3 py-2 text-left font-medium text-zinc-600">Sistema</th>
                      <th className="px-3 py-2 text-left font-medium text-zinc-600">URL/Host</th>
                      <th className="px-3 py-2 text-left font-medium text-zinc-600">Sucursal</th>
                      <th className="px-3 py-2 text-left font-medium text-zinc-600">Hora Réplica</th>
                      <th className="px-3 py-2 text-left font-medium text-zinc-600">Activo</th>
                      <th className="px-3 py-2 text-right font-medium text-zinc-600">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {apiConnections.map((apiConn) => (
                      <tr key={apiConn.id} className="border-b border-zinc-100 hover:bg-zinc-50">
                        {/* Estado */}
                        <td className="px-3 py-2">
                          {apiTestStatus[apiConn.id]?.loading ? (
                            <span className="inline-flex items-center gap-1 text-blue-600">
                              <Loader2 className="h-3 w-3 animate-spin" />
                              <span className="text-xs">Probando</span>
                            </span>
                          ) : apiTestStatus[apiConn.id]?.status === 'error' ? (
                            <span className="inline-flex items-center gap-1 text-red-600">
                              <WifiOff className="h-3 w-3" />
                              <span className="text-xs">Error</span>
                            </span>
                          ) : apiTestStatus[apiConn.id]?.status === 'warning' ? (
                            <span className="inline-flex items-center gap-1 text-amber-600">
                              <AlertTriangle className="h-3 w-3" />
                              <span className="text-xs">Parcial</span>
                            </span>
                          ) : apiTestStatus[apiConn.id]?.status === 'success' ? (
                            <span className="inline-flex items-center gap-1 text-green-600">
                              <Wifi className="h-3 w-3" />
                              <span className="text-xs">OK</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-zinc-400">
                              <Clock className="h-3 w-3" />
                              <span className="text-xs">Sin probar</span>
                            </span>
                          )}
                        </td>
                        {/* Nombre */}
                        <td className="px-3 py-2 font-medium text-zinc-800">{apiConn.name}</td>
                        {/* Sistema */}
                        <td className="px-3 py-2">
                          <Badge variant="outline" className="text-xs">{apiConn.tipo}</Badge>
                        </td>
                        {/* URL abreviada */}
                        <td className="px-3 py-2 text-zinc-600 text-xs font-mono max-w-40 truncate" title={apiConn.url}>
                          {apiConn.url ? apiConn.url.replace(/^https?:\/\//, '').substring(0, 30) + (apiConn.url.length > 30 ? '...' : '') : '-'}
                        </td>
                        {/* Sucursal */}
                        <td className="px-3 py-2 text-zinc-600">{apiConn.sucursal_destino || '-'}</td>
                        {/* Hora Réplica */}
                        <td className="px-3 py-2 text-zinc-600">{apiConn.hora_replica || '04:00'}</td>
                        {/* Activo */}
                        <td className="px-3 py-2">
                          {apiConn.activo ? (
                            <span className="text-green-600 text-xs">Sí</span>
                          ) : (
                            <span className="text-zinc-400 text-xs">No</span>
                          )}
                        </td>
                        {/* Acciones */}
                        <td className="px-3 py-2">
                          <div className="flex items-center justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 w-7 p-0"
                              onClick={() => testApiConnection(apiConn)}
                              disabled={apiTestStatus[apiConn.id]?.loading}
                              title="Probar conexión"
                            >
                              {apiTestStatus[apiConn.id]?.loading ? (
                                <Loader2 className="h-3 w-3 animate-spin" />
                              ) : (
                                <Zap className="h-3 w-3" />
                              )}
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 w-7 p-0"
                              onClick={() => {
                                setEditingApi(apiConn);
                                setApiFormData({
                                  name: apiConn.name,
                                  url: apiConn.url,
                                  api_key: '',
                                  tipo: apiConn.tipo,
                                  servidor_padre: apiConn.servidor_padre,
                                  sucursal_destino: apiConn.sucursal_destino,
                                  hora_replica: apiConn.hora_replica,
                                  solo_ventas_dia: apiConn.solo_ventas_dia,
                                  activo: apiConn.activo,
                                  visible_en_operaciones: apiConn.visible_en_operaciones
                                });
                                setQueryTestData({
                                  tipo_uso: apiConn.tipo_uso || 'Otro',
                                  nombre_consulta: apiConn.nombre_consulta || '',
                                  sql_query: apiConn.sql_query || DEFAULT_SQL_QUERY,
                                  timeout: 30
                                });
                                setQueryTestResult(null);
                                setApiDialogOpen(true);
                              }}
                              title="Editar conexión"
                            >
                              <Edit className="h-3 w-3" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 w-7 p-0"
                              onClick={() => {
                                setServerForUniversalTest(apiConn);
                                setUniversalTestConnectionType('api');
                                setUniversalTestOpen(true);
                              }}
                              title="Test Universal"
                            >
                              <TestTube2 className="h-3 w-3" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {apiConnections.length === 0 && (
                <div className="text-center py-8 text-zinc-500">
                  No hay conexiones API configuradas
                </div>
              )}
            </div>
          )}

          {/* VISTA TARJETAS - APIs */}
          {apiViewMode === 'cards' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {apiConnections.map((apiConn) => (
              <Card key={apiConn.id} className="border border-zinc-200 shadow-sm hover:border-zinc-300 transition-colors">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="relative">
                        <div className="bg-purple-50 p-2 rounded-lg">
                          <Globe className="h-5 w-5 text-purple-600" />
                        </div>
                        {/* Indicador de estado basado en el test de conexión */}
                        {apiTestStatus[apiConn.id]?.status === 'error' ? (
                          <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-red-500 border-2 border-white" title="Sin Conexión" />
                        ) : apiTestStatus[apiConn.id]?.status === 'warning' ? (
                          <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-amber-500 border-2 border-white" title="Conexión Parcial" />
                        ) : apiTestStatus[apiConn.id]?.status === 'success' ? (
                          <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-green-500 border-2 border-white" title="Conectado" />
                        ) : apiConn.activo ? (
                          <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-blue-500 border-2 border-white" title="Pendiente de verificar" />
                        ) : (
                          <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-zinc-400 border-2 border-white" title="Inactivo" />
                        )}
                      </div>
                      <div>
                        <CardTitle className="text-lg font-semibold">{apiConn.name}</CardTitle>
                        <p className="text-xs text-zinc-500 mt-1">API {apiConn.tipo}</p>
                      </div>
                    </div>
                    {/* Badge de status basado en el resultado del test de conexión */}
                    {apiTestStatus[apiConn.id]?.status === 'error' ? (
                      <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
                        Sin Conexión
                      </Badge>
                    ) : apiTestStatus[apiConn.id]?.status === 'warning' ? (
                      <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">
                        Parcial
                      </Badge>
                    ) : apiTestStatus[apiConn.id]?.status === 'success' ? (
                      <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                        Conectado
                      </Badge>
                    ) : apiConn.activo ? (
                      <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                        Pendiente
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="bg-zinc-100 text-zinc-500">
                        Inactivo
                      </Badge>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-zinc-600">URL:</span>
                      <span className="font-mono text-zinc-900 text-xs truncate max-w-[180px]">{apiConn.url}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-600">Servidor Padre:</span>
                      <span className="text-zinc-900">{apiConn.servidor_padre}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-600">Sucursal Destino:</span>
                      <span className="font-medium text-zinc-900">{apiConn.sucursal_destino}</span>
                    </div>
                    
                    <div className="pt-2 border-t border-zinc-100">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-zinc-500 flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          Hora de Réplica:
                        </span>
                        <span className="text-xs font-mono bg-zinc-100 px-2 py-0.5 rounded">{apiConn.hora_replica}</span>
                      </div>
                    </div>
                    
                    <div className="pt-2 border-t border-zinc-100">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-zinc-500">Solo Ventas del Día:</span>
                        <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-200">
                          {apiConn.solo_ventas_dia ? 'Sí' : 'No'}
                        </Badge>
                      </div>
                    </div>
                    
                    {/* Toggle Visible en Operaciones */}
                    <div className="pt-2 border-t border-zinc-100">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-zinc-500">Visible en Operaciones:</span>
                        <button
                          onClick={async () => {
                            // CORRECCIÓN P0-CHAPUR: Persistir visible_en_operaciones en EDARSAHUB SQL
                            const newValue = !apiConn.visible_en_operaciones;
                            try {
                              await api.put(`/api-connections/${apiConn.id}`, {
                                visible_en_operaciones: newValue
                              });
                              // Actualizar estado local DESPUÉS de éxito del backend
                              setApiConnections(prev => prev.map(a => 
                                a.id === apiConn.id 
                                  ? {...a, visible_en_operaciones: newValue} 
                                  : a
                              ));
                              toast.success(newValue ? 'Visible en operaciones' : 'Oculto en operaciones');
                            } catch (error) {
                              console.error('Error actualizando visible_en_operaciones:', error);
                              toast.error('Error al guardar cambio');
                            }
                          }}
                          className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                            apiConn.visible_en_operaciones ? 'bg-green-500' : 'bg-zinc-300'
                          }`}
                          title={apiConn.visible_en_operaciones ? 'Visible en dashboards' : 'Oculto en dashboards'}
                        >
                          <span
                            className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                              apiConn.visible_en_operaciones ? 'translate-x-4' : 'translate-x-0.5'
                            }`}
                          />
                        </button>
                      </div>
                      <p className="text-xs text-zinc-400 mt-1">
                        {apiConn.visible_en_operaciones 
                          ? 'Aparece en reportes, compras, comercial, etc.' 
                          : 'Solo visible aquí para administración'}
                      </p>
                    </div>
                  </div>
                  
                  {/* Estado del test de conexión */}
                  {apiTestStatus[apiConn.id] && (
                    <div className={`mt-3 p-2 rounded-lg text-xs ${
                      apiTestStatus[apiConn.id].status === 'success' ? 'bg-green-50 text-green-800 border border-green-200' :
                      apiTestStatus[apiConn.id].status === 'warning' ? 'bg-amber-50 text-amber-800 border border-amber-200' :
                      apiTestStatus[apiConn.id].status === 'error' ? 'bg-red-50 text-red-800 border border-red-200' :
                      'bg-zinc-50 text-zinc-600 border border-zinc-200'
                    }`}>
                      {apiTestStatus[apiConn.id].loading ? (
                        <div className="flex items-center gap-2">
                          <Loader2 className="h-3 w-3 animate-spin" />
                          <span>Probando conexión...</span>
                        </div>
                      ) : (
                        <span>{apiTestStatus[apiConn.id].message}</span>
                      )}
                    </div>
                  )}
                  
                  {/* Botones de acciones */}
                  <div className="flex flex-col gap-2 mt-4">
                    {/* Botón Probar Conexión */}
                    <Button 
                      variant="outline"
                      size="sm" 
                      className={`w-full ${
                        apiTestStatus[apiConn.id]?.status === 'success' ? 'border-green-300 text-green-700 hover:bg-green-50' :
                        apiTestStatus[apiConn.id]?.status === 'warning' ? 'border-amber-300 text-amber-700 hover:bg-amber-50' :
                        apiTestStatus[apiConn.id]?.status === 'error' ? 'border-red-300 text-red-700 hover:bg-red-50' :
                        ''
                      }`}
                      onClick={() => testApiConnection(apiConn)}
                      disabled={apiTestStatus[apiConn.id]?.loading}
                    >
                      {apiTestStatus[apiConn.id]?.loading ? (
                        <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                      ) : (
                        <Zap className="h-4 w-4 mr-1" />
                      )}
                      Probar Conexión
                    </Button>
                    
                    {/* Botón: Editar Consultas SQL */}
                    <Button 
                      variant="outline"
                      size="sm" 
                      className="w-full"
                      onClick={() => {
                        // Crear un pseudo-servidor para el wizard de consultas
                        setSelectedServer({
                          id: apiConn.id,
                          name: apiConn.name,
                          system_type: apiConn.tipo,
                          tipo_conexion: 'API_LOCAL',
                          host: apiConn.servidor_padre,
                          port: 0,
                          database: apiConn.sucursal_destino,
                          queries_configured: true,
                          is_api_connection: true
                        });
                        setQueryWizardOpen(true);
                      }}
                    >
                      <Code className="h-4 w-4 mr-1" />
                      Editar Consultas SQL
                    </Button>
                    
                    {/* FASE API-UQT1: Botón Test Universal para Conexiones API */}
                    <Button 
                      variant="outline"
                      size="sm" 
                      className="w-full border-purple-200 text-purple-700 hover:bg-purple-50"
                      onClick={() => {
                        setServerForUniversalTest({
                          id: apiConn.id,
                          name: apiConn.name,
                          system_type: apiConn.tipo
                        });
                        setUniversalTestConnectionType('api');
                        setUniversalTestOpen(true);
                      }}
                      data-testid="api-universal-test-button"
                    >
                      <TestTube2 className="h-4 w-4 mr-1" />
                      Test Universal
                    </Button>
                    
                    <div className="flex gap-2">
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => {
                          setEditingApi(apiConn);
                          setApiFormData({
                            name: apiConn.name,
                            url: apiConn.url,
                            api_key: '',
                            tipo: apiConn.tipo,
                            servidor_padre: apiConn.servidor_padre,
                            sucursal_destino: apiConn.sucursal_destino,
                            hora_replica: apiConn.hora_replica,
                            solo_ventas_dia: apiConn.solo_ventas_dia,
                            activo: apiConn.activo,
                            visible_en_operaciones: apiConn.visible_en_operaciones
                          });
                          // Resetear sección de consulta de prueba
                          // En edición: si tiene consulta guardada, cargarla; si no, sugerir la default
                          setQueryTestData({
                            tipo_uso: apiConn.tipo_uso || 'Otro',
                            nombre_consulta: apiConn.nombre_consulta || '',
                            sql_query: apiConn.sql_query || DEFAULT_SQL_QUERY,
                            timeout: 30
                          });
                          setQueryTestResult(null);
                          setApiDialogOpen(true);
                        }}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                        className="flex-1"
                        onClick={() => {
                          // Crear un pseudo-servidor para el diálogo de filtros
                          const pseudoServer = {
                            id: apiConn.id,
                            name: apiConn.name,
                            system_type: apiConn.tipo,
                            tipo_conexion: 'API_LOCAL',
                            host: apiConn.servidor_padre,
                            port: 0,
                            database: apiConn.sucursal_destino,
                            is_api_connection: true,
                            // Copiar filtros existentes si los hay
                            tipos_movimiento: apiConn.config?.tipos_movimiento || [],
                            categorias: apiConn.config?.categorias || [],
                            departamentos: apiConn.config?.departamentos || []
                          };
                          setSelectedServer(pseudoServer);
                          setConfigDialogOpen(true);
                        }}
                      >
                        <Filter className="h-4 w-4 mr-1" />
                        Filtros
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={async () => {
                          if (window.confirm('¿Eliminar esta conexión API?')) {
                            try {
                              await api.delete(`/api-connections/${apiConn.id}`);
                              await loadApiConnections();  // Recargar lista
                              toast.success('Conexión eliminada');
                            } catch (error) {
                              console.error('Error eliminando conexión:', error);
                              toast.error('Error al eliminar conexión');
                            }
                          }
                        }}
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

          {apiConnections.length === 0 && apiViewMode === 'cards' && (
            <div className="text-center py-12 text-zinc-500">
              <Globe className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No hay conexiones API configuradas</p>
              <p className="text-sm mt-1">Agrega una conexión para obtener datos en tiempo real</p>
            </div>
          )}
        </TabsContent>

        {/* Tab: Vtiger CRM */}
        <TabsContent value="vtiger">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-zinc-800">Conexiones Vtiger CRM</h3>
              <p className="text-sm text-zinc-500">Integración bidireccional con Vtiger CRM</p>
            </div>
            <Button onClick={openNewVtiger} className="bg-purple-600 hover:bg-purple-700">
              <Plus className="h-4 w-4 mr-2" />
              Nueva Conexión
            </Button>
          </div>

          {loadingVtiger ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
            </div>
          ) : vtigerConnections.length === 0 ? (
            <div className="text-center py-12 text-zinc-500">
              <Link2 className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No hay conexiones Vtiger configuradas</p>
              <p className="text-sm mt-1">Conecta tu CRM para sincronizar Leads, Contactos y Oportunidades</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {vtigerConnections.map((conn) => (
                <Card key={conn.id} className="border-purple-100 hover:border-purple-300 transition-colors">
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="relative">
                          <Link2 className="h-5 w-5 text-purple-600" />
                          {vtigerTestStatus[conn.id]?.status === 'success' && (
                            <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-green-500" />
                          )}
                          {vtigerTestStatus[conn.id]?.status === 'error' && (
                            <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-red-500" />
                          )}
                        </div>
                        <CardTitle className="text-base">{conn.name}</CardTitle>
                      </div>
                      <div className="flex gap-1">
                        {conn.source !== 'environment' && (
                          <>
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              onClick={() => openEditVtiger(conn)}
                              className="h-7 w-7 p-0"
                            >
                              <Edit className="h-3.5 w-3.5" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              onClick={() => deleteVtigerConnection(conn.id)}
                              className="h-7 w-7 p-0 text-red-600 hover:text-red-700"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0 space-y-3">
                    <div className="text-xs text-zinc-500 space-y-1">
                      <div className="flex items-center gap-1">
                        <Globe className="h-3 w-3" />
                        <span className="truncate">{conn.base_url}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Mail className="h-3 w-3" />
                        <span>{conn.username}</span>
                      </div>
                    </div>
                    
                    <div className="flex flex-wrap gap-1">
                      {conn.sync_modules?.map((mod) => (
                        <Badge key={mod} variant="secondary" className="text-xs bg-purple-50 text-purple-700">
                          {mod}
                        </Badge>
                      ))}
                    </div>
                    
                    <div className="flex items-center justify-between pt-2 border-t">
                      <div className="flex items-center gap-2">
                        <Badge variant={conn.active ? 'default' : 'secondary'} className={conn.active ? 'bg-green-100 text-green-700' : ''}>
                          {conn.active ? 'Activo' : 'Inactivo'}
                        </Badge>
                        {conn.source === 'environment' && (
                          <Badge variant="outline" className="text-xs">ENV</Badge>
                        )}
                      </div>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => testVtigerConnection(conn.id)}
                        disabled={vtigerTestStatus[conn.id]?.loading}
                        className="h-7 px-2 text-xs"
                      >
                        {vtigerTestStatus[conn.id]?.loading ? (
                          <>
                            <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                            Probando...
                          </>
                        ) : vtigerTestStatus[conn.id]?.status === 'success' ? (
                          <>
                            <CheckCircle2 className="h-3 w-3 mr-1 text-green-600" />
                            Online
                          </>
                        ) : vtigerTestStatus[conn.id]?.status === 'error' ? (
                          <>
                            <AlertCircle className="h-3 w-3 mr-1 text-red-600" />
                            Reintentar
                          </>
                        ) : (
                          <>
                            <Wifi className="h-3 w-3 mr-1" />
                            Probar
                          </>
                        )}
                      </Button>
                    </div>
                    
                    {vtigerTestStatus[conn.id]?.user && (
                      <div className="text-xs bg-green-50 p-2 rounded text-green-700">
                        <p>✓ Usuario: {vtigerTestStatus[conn.id].user.username}</p>
                        <p>✓ Vtiger v{vtigerTestStatus[conn.id].user.vtigerVersion}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Tab: Bitácora Admin CORE */}
        <TabsContent value="bitacora">
          <div className="flex items-center justify-between mb-4" data-testid="bitacora-core-panel">
            <div className="flex items-start gap-3">
              <div className="bg-amber-50 p-2 rounded-lg">
                <ScrollText className="h-5 w-5 text-amber-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-zinc-800" style={{ fontFamily: 'Manrope, sans-serif' }}>
                  Bitácora de Conexiones CORE
                </h3>
                <p className="text-sm text-zinc-500">
                  Registro de pruebas y acciones sobre conexiones del HUB (auditoría EDARSAHUB SQL).
                </p>
              </div>
            </div>
            <Button
              onClick={loadCoreAuditLog}
              variant="outline"
              size="sm"
              disabled={loadingCoreAudit}
              className="border-amber-200 text-amber-700 hover:bg-amber-50"
              data-testid="bitacora-refresh-button"
            >
              {loadingCoreAudit ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4 mr-2" />
              )}
              Actualizar
            </Button>
          </div>

          {loadingCoreAudit ? (
            <div className="flex items-center justify-center h-48">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-amber-500"></div>
            </div>
          ) : coreAuditLog.length === 0 ? (
            <div className="text-center py-12 text-zinc-500 border border-dashed border-zinc-200 rounded-lg" data-testid="bitacora-empty">
              <History className="h-10 w-10 mx-auto mb-3 text-zinc-300" />
              Sin registros de auditoría todavía.
            </div>
          ) : (
            <div className="border border-zinc-200 rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm" data-testid="bitacora-table">
                  <thead className="bg-zinc-50 border-b border-zinc-200">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium text-zinc-600">Fecha</th>
                      <th className="px-3 py-2 text-left font-medium text-zinc-600">Conexión</th>
                      <th className="px-3 py-2 text-left font-medium text-zinc-600">Acción</th>
                      <th className="px-3 py-2 text-left font-medium text-zinc-600">Usuario</th>
                      <th className="px-3 py-2 text-left font-medium text-zinc-600">Estado</th>
                      <th className="px-3 py-2 text-left font-medium text-zinc-600">Origen</th>
                    </tr>
                  </thead>
                  <tbody>
                    {coreAuditLog.map((row) => (
                      <tr key={row.log_id} className="border-b border-zinc-100 hover:bg-zinc-50" data-testid="bitacora-row">
                        <td className="px-3 py-2 text-zinc-700 text-xs whitespace-nowrap font-mono">
                          {row.fecha ? new Date(row.fecha).toLocaleString('es-MX', { dateStyle: 'short', timeStyle: 'short' }) : '—'}
                        </td>
                        <td className="px-3 py-2 font-medium text-zinc-800">{row.servidor_nombre || '—'}</td>
                        <td className="px-3 py-2">
                          <Badge variant="outline" className="text-xs font-mono">{row.accion || '—'}</Badge>
                        </td>
                        <td className="px-3 py-2 text-zinc-600">
                          <span className="inline-flex items-center gap-1">
                            <User className="h-3 w-3 text-zinc-400" />
                            {row.usuario || 'Sistema'}
                          </span>
                        </td>
                        <td className="px-3 py-2">
                          {row.estado ? (
                            <Badge
                              variant="outline"
                              className={`text-xs ${row.estado === 'SUCCESS' ? 'bg-green-50 text-green-700 border-green-200' : 'bg-red-50 text-red-700 border-red-200'}`}
                            >
                              {row.estado}
                            </Badge>
                          ) : (
                            <span className="text-zinc-400 text-xs">—</span>
                          )}
                        </td>
                        <td className="px-3 py-2 text-zinc-500 text-xs font-mono">{row.ip_origen || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="bg-zinc-50 px-3 py-2 text-xs text-zinc-500 border-t border-zinc-200">
                {coreAuditLog.length} registros (más recientes primero)
              </div>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Dialog para agregar/editar Conexión API */}
      <Dialog open={apiDialogOpen} onOpenChange={(open) => { if (!open) resetApiModalPosition(); else setApiDialogOpen(true); }}>
        <DialogContent 
          draggable={true}
          hideCloseButton={true}
          overlayClassName="bg-black/50"
          className={`max-w-lg flex flex-col transition-all duration-200 ${
            apiModalMinimized 
              ? 'max-h-16 overflow-hidden' 
              : 'max-h-[85vh]'
          }`}
          style={{
            transform: `translate(calc(-50% + ${apiModalPosition.x}px), calc(-50% + ${apiModalPosition.y}px))`,
            transition: isDragging ? 'none' : 'transform 0.15s ease-out',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
          }}
        >
          {/* Header arrastrable con controles de ventana */}
          <div 
            className="flex items-center justify-between border-b border-zinc-200 pb-3 cursor-move select-none bg-zinc-50 -mx-6 -mt-6 px-6 pt-4 rounded-t-lg"
            onMouseDown={(e) => handleDragStart(e, setApiModalPosition)}
          >
            <div className="flex items-center gap-2">
              <Move className="h-4 w-4 text-zinc-400" />
              <Globe className="h-5 w-5 text-zinc-700" />
              <span className="font-semibold text-zinc-800">
                {editingApi ? 'Editar Conexión API' : 'Nueva Conexión API'}
              </span>
            </div>
            
            {/* Controles de ventana */}
            <div className="flex items-center gap-1">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0 hover:bg-zinc-200"
                onClick={centerApiModal}
                title="Centrar ventana"
              >
                <Maximize2 className="h-4 w-4" />
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0 hover:bg-zinc-200"
                onClick={() => setApiModalMinimized(!apiModalMinimized)}
                title={apiModalMinimized ? "Restaurar" : "Minimizar"}
              >
                <Minus className="h-4 w-4" />
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0 hover:bg-red-100 hover:text-red-600"
                onClick={resetApiModalPosition}
                title="Cerrar"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
          
          {/* Contenido (oculto cuando minimizado) */}
          {!apiModalMinimized && (
            <>
              <DialogHeader className="pt-3">
                <DialogDescription>
                  Configura la conexión a una API local para obtener ventas en tiempo real
                </DialogDescription>
              </DialogHeader>
              
              {/* Cuerpo con scroll */}
              <div className="flex-1 overflow-y-auto pr-2 space-y-4 min-h-0 max-h-[60vh]">
                <div className="space-y-2">
                  <Label htmlFor="api_name">Nombre</Label>
                  <Input
                    id="api_name"
                    value={apiFormData.name}
                    onChange={(e) => setApiFormData({...apiFormData, name: e.target.value})}
                    placeholder="130° QRO LOCAL"
                  />
                </div>
            
            <div className="space-y-2">
              <Label htmlFor="api_url">URL del Endpoint</Label>
              <Input
                id="api_url"
                value={apiFormData.url}
                onChange={(e) => setApiFormData({...apiFormData, url: e.target.value})}
                placeholder="https://servidor-local/query"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="api_key">API Key</Label>
              <Input
                id="api_key"
                type="password"
                value={apiFormData.api_key}
                onChange={(e) => setApiFormData({...apiFormData, api_key: e.target.value})}
                placeholder={editingApi ? '(sin cambios)' : 'Ingrese API Key'}
                autoComplete="new-password"
              />
              <p className="text-xs text-zinc-500">
                Se almacena cifrada. No se muestra el valor actual por seguridad.
              </p>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="api_tipo">Tipo de Sistema</Label>
                <Select 
                  value={apiFormData.tipo} 
                  onValueChange={handleTipoSistemaApiChange}
                  disabled={loadingTiposSistema}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={loadingTiposSistema ? "Cargando..." : "Seleccionar tipo"} />
                  </SelectTrigger>
                  <SelectContent>
                    {tiposSistema.map((tipo) => (
                      <SelectItem key={tipo.Codigo} value={tipo.Codigo}>
                        {tipo.Descripcion}
                      </SelectItem>
                    ))}
                    {permisosSistemas.mostrar_nuevo && (
                      <SelectItem value="__NUEVO__" className="text-blue-600 font-medium border-t mt-1 pt-1">
                        + Nuevo tipo de sistema
                      </SelectItem>
                    )}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="api_hora">Hora de Réplica</Label>
                <Input
                  id="api_hora"
                  type="time"
                  value={apiFormData.hora_replica}
                  onChange={(e) => setApiFormData({...apiFormData, hora_replica: e.target.value})}
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="api_servidor">Servidor Padre (Nube)</Label>
                <Select 
                  value={apiFormData.servidor_padre} 
                  onValueChange={(value) => setApiFormData({...apiFormData, servidor_padre: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar..." />
                  </SelectTrigger>
                  <SelectContent>
                    {servers.map(s => (
                      <SelectItem key={s.id} value={s.name}>{s.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="api_sucursal">Sucursal Destino</Label>
                <Input
                  id="api_sucursal"
                  value={apiFormData.sucursal_destino}
                  onChange={(e) => setApiFormData({...apiFormData, sucursal_destino: e.target.value})}
                  placeholder="Querétaro"
                />
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Checkbox 
                id="api_solo_ventas"
                checked={apiFormData.solo_ventas_dia}
                onCheckedChange={(checked) => setApiFormData({...apiFormData, solo_ventas_dia: checked})}
              />
              <Label htmlFor="api_solo_ventas" className="text-sm">
                Solo obtener ventas del día actual (evita duplicación)
              </Label>
            </div>
            
            <div className="bg-amber-50 border border-amber-200 rounded-md p-3">
              <p className="text-xs text-amber-900">
                <strong>Nota:</strong> Esta conexión obtiene ventas del día que se suman a las del servidor padre. 
                Por la noche (a las {apiFormData.hora_replica || '04:00'}) los datos se replican al servidor en la nube, 
                momento en que esta API deja de sumar para evitar duplicación.
              </p>
            </div>
            
            {/* ========== SECCIÓN DE CONSULTA DE PRUEBA ========== */}
            <div className="border-t border-zinc-200 pt-4 mt-4">
              <div className="flex items-center gap-2 mb-3">
                <TestTube2 className="h-4 w-4 text-blue-600" />
                <h4 className="text-sm font-medium text-zinc-800">Consulta de prueba / Consulta operativa</h4>
              </div>
              
              <div className="space-y-3">
                {/* Fila 1: Tipo de uso y Nombre */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs">Tipo de uso</Label>
                    <Select 
                      value={queryTestData.tipo_uso} 
                      onValueChange={(v) => setQueryTestData({...queryTestData, tipo_uso: v})}
                    >
                      <SelectTrigger className="h-8">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {TIPOS_USO.map(tipo => (
                          <SelectItem key={tipo} value={tipo}>{tipo}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-1">
                    <Label className="text-xs">Nombre de consulta</Label>
                    <Input
                      className="h-8 text-sm"
                      value={queryTestData.nombre_consulta}
                      onChange={(e) => setQueryTestData({...queryTestData, nombre_consulta: e.target.value})}
                      placeholder="Ej: Ventas diarias"
                    />
                  </div>
                </div>
                
                {/* Fila 2: Consulta SQL */}
                <div className="space-y-1">
                  <Label className="text-xs">Consulta SELECT</Label>
                  <Textarea
                    className="font-mono text-xs min-h-20 resize-none"
                    value={queryTestData.sql_query}
                    onChange={(e) => setQueryTestData({...queryTestData, sql_query: e.target.value})}
                    placeholder="SELECT TOP 10 * FROM cheques WHERE fecha = CAST(GETDATE() AS DATE)"
                    data-testid="api-query-sql-input"
                  />
                  <p className="text-xs text-zinc-500 flex items-center gap-1">
                    <AlertTriangle className="h-3 w-3 text-amber-500" />
                    Solo consultas SELECT. DELETE, UPDATE, INSERT están bloqueados.
                  </p>
                </div>
                
                {/* Fila 3: Timeout y Botón */}
                <div className="flex items-end gap-3">
                  <div className="space-y-1 w-24">
                    <Label className="text-xs">Timeout</Label>
                    <Select 
                      value={String(queryTestData.timeout)} 
                      onValueChange={(v) => setQueryTestData({...queryTestData, timeout: Number(v)})}
                    >
                      <SelectTrigger className="h-8">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="15">15s</SelectItem>
                        <SelectItem value="30">30s</SelectItem>
                        <SelectItem value="60">60s</SelectItem>
                        <SelectItem value="90">90s</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <Button
                    type="button"
                    size="sm"
                    onClick={executeTestQuery}
                    disabled={testingQuery || !queryTestData.sql_query.trim()}
                    className="bg-blue-600 hover:bg-blue-700 text-white h-8"
                    data-testid="api-test-query-btn"
                  >
                    {testingQuery ? (
                      <>
                        <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                        Ejecutando...
                      </>
                    ) : (
                      <>
                        <Play className="h-3 w-3 mr-1" />
                        Probar consulta
                      </>
                    )}
                  </Button>
                </div>
                
                {/* Resultado de la consulta */}
                {queryTestResult && (
                  <div className={`rounded-md p-3 text-sm ${
                    queryTestResult.success 
                      ? 'bg-green-50 border border-green-200' 
                      : 'bg-red-50 border border-red-200'
                  }`}>
                    <div className="flex items-center gap-2 mb-2">
                      {queryTestResult.success ? (
                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-red-600" />
                      )}
                      <span className={queryTestResult.success ? 'text-green-800' : 'text-red-800'}>
                        {queryTestResult.success ? 'Consulta exitosa' : 'Error'}
                      </span>
                      {queryTestResult.response_time_ms && (
                        <span className="text-xs text-zinc-500 ml-auto">
                          {queryTestResult.response_time_ms}ms
                        </span>
                      )}
                    </div>
                    
                    {queryTestResult.success ? (
                      <div className="space-y-2">
                        <div className="flex gap-4 text-xs text-zinc-600">
                          <span><strong>Filas:</strong> {queryTestResult.rows_count || 0}</span>
                          <span><strong>Columnas:</strong> {queryTestResult.columns?.length || 0}</span>
                        </div>
                        
                        {/* Preview de datos */}
                        {queryTestResult.preview_data?.length > 0 && (
                          <div className="max-h-40 overflow-auto border border-zinc-200 rounded bg-white">
                            <table className="w-full text-xs">
                              <thead className="bg-zinc-50 sticky top-0">
                                <tr>
                                  {queryTestResult.columns?.map((col, i) => (
                                    <th key={i} className="px-2 py-1 text-left font-medium text-zinc-700 border-b">
                                      {col}
                                    </th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {queryTestResult.preview_data.slice(0, 5).map((row, rowIdx) => (
                                  <tr key={rowIdx} className="border-b border-zinc-100">
                                    {queryTestResult.columns?.map((col, colIdx) => (
                                      <td key={colIdx} className="px-2 py-1 text-zinc-600 truncate max-w-32">
                                        {String(row[col] ?? '')}
                                      </td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                            {queryTestResult.preview_data.length > 5 && (
                              <div className="px-2 py-1 text-xs text-zinc-500 bg-zinc-50 text-center">
                                +{queryTestResult.preview_data.length - 5} filas más...
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="text-xs text-red-700">
                        {queryTestResult.sql_blocked && queryTestResult.validation_errors?.length > 0 ? (
                          <ul className="list-disc list-inside">
                            {queryTestResult.validation_errors.map((err, i) => (
                              <li key={i}>{err}</li>
                            ))}
                          </ul>
                        ) : (
                          <p>{queryTestResult.error || 'Error desconocido'}</p>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
            {/* ========== FIN SECCIÓN DE CONSULTA DE PRUEBA ========== */}
          </div>
          
          {/* Footer fijo con botones */}
          <DialogFooter className="border-t border-zinc-100 pt-4 mt-2 flex-shrink-0">
            <Button variant="outline" onClick={resetApiModalPosition}>
              Cancelar
            </Button>
            <Button 
              onClick={async () => {
                if (!apiFormData.name || !apiFormData.url) {
                  toast.error('Completa nombre y URL');
                  return;
                }
                
                try {
                  if (editingApi) {
                    // Actualizar conexión existente
                    const response = await api.put(`/api-connections/${editingApi.id}`, apiFormData);
                    if (response.data.success) {
                      await loadApiConnections();  // Recargar lista
                      toast.success('Conexión actualizada');
                    }
                  } else {
                    // Crear nueva conexión
                    const response = await api.post('/api-connections', apiFormData);
                    if (response.data.success) {
                      await loadApiConnections();  // Recargar lista
                      toast.success('Conexión agregada');
                    }
                  }
                  resetApiModalPosition();
                } catch (error) {
                  console.error('Error guardando conexión API:', error);
                  toast.error('Error al guardar conexión');
                }
              }}
              className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800"
            >
              {editingApi ? 'Guardar Cambios' : 'Agregar Conexión'}
            </Button>
          </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Dialog para Vtiger CRM */}
      <Dialog open={vtigerDialogOpen} onOpenChange={setVtigerDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Link2 className="h-5 w-5 text-purple-600" />
              {editingVtiger ? 'Editar Conexión Vtiger' : 'Nueva Conexión Vtiger'}
            </DialogTitle>
            <DialogDescription>
              Configura la conexión con tu instancia de Vtiger CRM
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="vtiger-name">Nombre de la conexión</Label>
              <Input
                id="vtiger-name"
                placeholder="Vtiger CRM - Mi Empresa"
                value={vtigerFormData.name}
                onChange={(e) => setVtigerFormData({...vtigerFormData, name: e.target.value})}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="vtiger-url">URL de Vtiger</Label>
              <Input
                id="vtiger-url"
                placeholder="https://miempresa.vtiger.com"
                value={vtigerFormData.base_url}
                onChange={(e) => setVtigerFormData({...vtigerFormData, base_url: e.target.value})}
              />
              <p className="text-xs text-zinc-500">URL completa de tu instancia Vtiger</p>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="vtiger-user">Usuario</Label>
                <Input
                  id="vtiger-user"
                  placeholder="admin"
                  value={vtigerFormData.username}
                  onChange={(e) => setVtigerFormData({...vtigerFormData, username: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="vtiger-key">Access Key</Label>
                <Input
                  id="vtiger-key"
                  type="password"
                  placeholder="v7Wex2c3Mf9jVlJB"
                  value={vtigerFormData.access_key}
                  onChange={(e) => setVtigerFormData({...vtigerFormData, access_key: e.target.value})}
                />
              </div>
            </div>
            <p className="text-xs text-zinc-500">
              Encuentra el Access Key en Vtiger: Mi Perfil → Mis Preferencias → Access Key
            </p>
            
            <div className="space-y-2">
              <Label>Módulos a sincronizar</Label>
              <div className="flex flex-wrap gap-2">
                {['Leads', 'Contacts', 'Accounts', 'Potentials'].map((mod) => (
                  <Button
                    key={mod}
                    type="button"
                    variant={vtigerFormData.sync_modules.includes(mod) ? 'default' : 'outline'}
                    size="sm"
                    className={vtigerFormData.sync_modules.includes(mod) ? 'bg-purple-600 hover:bg-purple-700' : ''}
                    onClick={() => {
                      const modules = vtigerFormData.sync_modules.includes(mod)
                        ? vtigerFormData.sync_modules.filter(m => m !== mod)
                        : [...vtigerFormData.sync_modules, mod];
                      setVtigerFormData({...vtigerFormData, sync_modules: modules});
                    }}
                  >
                    {mod === 'Potentials' ? 'Oportunidades' : mod === 'Accounts' ? 'Cuentas' : mod === 'Contacts' ? 'Contactos' : mod}
                  </Button>
                ))}
              </div>
            </div>
            
            <div className="space-y-2">
              <Label>Dirección de sincronización</Label>
              <Select 
                value={vtigerFormData.sync_direction} 
                onValueChange={(v) => setVtigerFormData({...vtigerFormData, sync_direction: v})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="read_only">Solo lectura (Vtiger → EDARSA)</SelectItem>
                  <SelectItem value="bidirectional">Bidireccional</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex items-center gap-2">
              <Switch
                checked={vtigerFormData.active}
                onCheckedChange={(checked) => setVtigerFormData({...vtigerFormData, active: checked})}
              />
              <Label>Conexión activa</Label>
            </div>
            
            {/* Resultado del test */}
            {vtigerTestResult && (
              <div className={`p-3 rounded-lg text-sm ${
                vtigerTestResult.success 
                  ? 'bg-green-50 text-green-700 border border-green-200' 
                  : 'bg-red-50 text-red-700 border border-red-200'
              }`}>
                {vtigerTestResult.success ? (
                  <>
                    <p className="font-medium">✓ Conexión exitosa ({vtigerTestResult.responseTime}ms)</p>
                    {vtigerTestResult.user && (
                      <p className="text-xs mt-1">
                        Usuario: {vtigerTestResult.user.username} | Vtiger v{vtigerTestResult.user.vtigerVersion}
                      </p>
                    )}
                  </>
                ) : (
                  <p>✗ {vtigerTestResult.message}</p>
                )}
              </div>
            )}
          </div>
          
          <DialogFooter className="flex gap-2">
            <Button 
              variant="outline" 
              onClick={testVtigerFromForm}
              disabled={testingVtiger || !vtigerFormData.base_url || !vtigerFormData.username || !vtigerFormData.access_key}
            >
              {testingVtiger ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Probando...
                </>
              ) : (
                <>
                  <Wifi className="h-4 w-4 mr-2" />
                  Probar Conexión
                </>
              )}
            </Button>
            <Button 
              onClick={saveVtigerConnection}
              disabled={testingVtiger || !vtigerFormData.base_url || !vtigerFormData.username}
              className="bg-purple-600 hover:bg-purple-700"
            >
              {editingVtiger ? 'Guardar Cambios' : 'Crear Conexión'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add/Edit Server Dialog */}
      <Dialog open={dialogOpen} onOpenChange={(open) => { if (!open) { resetForm(); resetSqlModalPosition(); } else setDialogOpen(true); }}>
        <DialogContent 
          draggable={true}
          hideCloseButton={true}
          overlayClassName="bg-black/50"
          className={`max-w-2xl flex flex-col transition-all duration-200 ${
            sqlModalMinimized 
              ? 'max-h-16 overflow-hidden' 
              : 'max-h-[85vh]'
          }`}
          style={{
            transform: `translate(calc(-50% + ${sqlModalPosition.x}px), calc(-50% + ${sqlModalPosition.y}px))`,
            transition: isDragging ? 'none' : 'transform 0.15s ease-out',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
          }}
        >
          {/* Header arrastrable con controles de ventana */}
          <div 
            className="flex items-center justify-between border-b border-zinc-200 pb-3 cursor-move select-none bg-zinc-50 -mx-6 -mt-6 px-6 pt-4 rounded-t-lg"
            onMouseDown={(e) => handleDragStart(e, setSqlModalPosition)}
          >
            <div className="flex items-center gap-2">
              <Move className="h-4 w-4 text-zinc-400" />
              <Database className="h-5 w-5 text-zinc-700" />
              <span className="font-semibold text-zinc-800">
                {editingServer ? 'Editar Servidor' : 'Agregar Nuevo Servidor'}
              </span>
            </div>
            
            {/* Controles de ventana */}
            <div className="flex items-center gap-1">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0 hover:bg-zinc-200"
                onClick={centerSqlModal}
                title="Centrar ventana"
              >
                <Maximize2 className="h-4 w-4" />
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0 hover:bg-zinc-200"
                onClick={() => setSqlModalMinimized(!sqlModalMinimized)}
                title={sqlModalMinimized ? "Restaurar" : "Minimizar"}
              >
                <Minus className="h-4 w-4" />
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0 hover:bg-red-100 hover:text-red-600"
                onClick={() => { resetForm(); resetSqlModalPosition(); }}
                title="Cerrar"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
          
          {/* Contenido (oculto cuando minimizado) */}
          {!sqlModalMinimized && (
            <>
              <DialogHeader className="pt-3">
                <DialogDescription>
                  {editingServer ? 'Modifica los parámetros de conexión' : 'Configura la conexión a un servidor SQL'}
                </DialogDescription>
              </DialogHeader>
              
              {/* Cuerpo con scroll */}
              <div className="flex-1 overflow-y-auto pr-2 space-y-4 min-h-0 max-h-[55vh]">
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
                  onValueChange={handleTipoSistemaChange}
                  disabled={loadingTiposSistema}
                >
                  <SelectTrigger data-testid="system-type-select">
                    <SelectValue placeholder={loadingTiposSistema ? "Cargando..." : "Seleccionar tipo"} />
                  </SelectTrigger>
                  <SelectContent>
                    {tiposSistema.map((tipo) => (
                      <SelectItem key={tipo.Codigo} value={tipo.Codigo}>
                        {tipo.Descripcion}
                      </SelectItem>
                    ))}
                    {permisosSistemas.mostrar_nuevo && (
                      <SelectItem value="__NUEVO__" className="text-blue-600 font-medium border-t mt-1 pt-1">
                        + Nuevo tipo de sistema
                      </SelectItem>
                    )}
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
          </div>

          {/* Footer fijo con botones */}
          <DialogFooter className="border-t border-zinc-100 pt-4 flex-shrink-0">
              <Button type="button" variant="outline" onClick={() => { resetForm(); resetSqlModalPosition(); }}>
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
            </>
          )}
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

      {/* Dialog de Configuración de Sucursales Visibles */}
      <Dialog open={sucursalesConfigOpen} onOpenChange={setSucursalesConfigOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Building2 className="h-5 w-5" />
              Sucursales Visibles - {serverForSucursales?.name}
            </DialogTitle>
            <DialogDescription>
              Configura qué sucursales aparecerán en tableros, filtros y reportes operativos.
              Las sucursales no marcadas seguirán existiendo pero no aparecerán en operaciones.
            </DialogDescription>
          </DialogHeader>
          
          <div className="flex-1 overflow-auto">
            {/* Botón de sincronizar */}
            <div className="flex items-center justify-between mb-4 pb-4 border-b">
              <div className="text-sm text-zinc-500">
                {sucursalesConfig.length > 0 
                  ? `${sucursalesConfig.filter(s => s.visible_en_operaciones).length} de ${sucursalesConfig.length} sucursales visibles`
                  : 'Sin configuración - Todas las sucursales están visibles'
                }
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={syncSucursalesFromSQL}
                disabled={syncingSucursales}
                className="border-blue-200 text-blue-700 hover:bg-blue-50"
              >
                {syncingSucursales ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4 mr-2" />
                )}
                Sincronizar desde SQL
              </Button>
            </div>
            
            {/* Loading */}
            {loadingSucursalesConfig && (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
              </div>
            )}
            
            {/* Sin configuración */}
            {!loadingSucursalesConfig && sucursalesConfig.length === 0 && (
              <div className="text-center py-12">
                <Building2 className="h-12 w-12 mx-auto text-zinc-300 mb-4" />
                <h3 className="font-medium text-zinc-900 mb-2">Sin configuración de sucursales</h3>
                <p className="text-sm text-zinc-500 mb-4">
                  Actualmente todas las sucursales de este servidor son visibles en operaciones.
                  <br />
                  Haz clic en &quot;Sincronizar desde SQL&quot; para cargar las sucursales y configurar su visibilidad.
                </p>
              </div>
            )}
            
            {/* Lista de sucursales */}
            {!loadingSucursalesConfig && sucursalesConfig.length > 0 && (
              <div className="space-y-2">
                {sucursalesConfig.map((sucursal, index) => (
                  <div 
                    key={sucursal.sucursal_origen_id}
                    className={`flex items-center justify-between p-3 rounded-lg border transition-colors ${
                      sucursal.visible_en_operaciones 
                        ? 'bg-green-50 border-green-200' 
                        : 'bg-zinc-50 border-zinc-200'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="text-zinc-400 cursor-move">
                        <GripVertical className="h-4 w-4" />
                      </div>
                      <div>
                        <div className="font-medium text-sm">
                          {sucursal.nombre_visible || sucursal.sucursal_nombre}
                        </div>
                        <div className="text-xs text-zinc-500">
                          ID: {sucursal.sucursal_origen_id}
                          {sucursal.nombre_visible && (
                            <span className="ml-2 text-zinc-400">
                              (Original: {sucursal.sucursal_nombre})
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      <span className={`text-xs font-medium ${
                        sucursal.visible_en_operaciones ? 'text-green-700' : 'text-zinc-500'
                      }`}>
                        {sucursal.visible_en_operaciones ? 'Visible' : 'Oculta'}
                      </span>
                      <button
                        onClick={() => toggleSucursalVisibility(sucursal.sucursal_origen_id, sucursal.visible_en_operaciones)}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          sucursal.visible_en_operaciones ? 'bg-green-500' : 'bg-zinc-300'
                        }`}
                      >
                        <span
                          className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${
                            sucursal.visible_en_operaciones ? 'translate-x-5' : 'translate-x-0.5'
                          }`}
                        />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <DialogFooter className="border-t pt-4">
            <div className="flex items-center justify-between w-full">
              <div className="text-xs text-zinc-500">
                Los cambios se aplican inmediatamente
              </div>
              <Button variant="outline" onClick={() => setSucursalesConfigOpen(false)}>
                Cerrar
              </Button>
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

      {/* Universal Query Tester - Herramienta agnóstica */}
      {/* FASE API-UQT1: Soporta connectionType 'sql' (servidores SQL) y 'api' (conexiones API) */}
      <UniversalQueryTester
        open={universalTestOpen}
        onClose={() => setUniversalTestOpen(false)}
        server={serverForUniversalTest}
        connectionType={universalTestConnectionType}
      />

      {/* Modal para crear nuevo tipo de sistema */}
      <Dialog open={nuevoSistemaModalOpen} onOpenChange={setNuevoSistemaModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Plus className="h-5 w-5" />
              Nuevo Tipo de Sistema
            </DialogTitle>
            <DialogDescription>
              {permisosSistemas.puede_crear 
                ? "Crear un nuevo tipo de sistema que estará disponible inmediatamente."
                : "Solicitar un nuevo tipo de sistema. Quedará pendiente de autorización."
              }
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="nuevo_sistema_desc">Nombre / Descripción</Label>
              <Input
                id="nuevo_sistema_desc"
                value={nuevoSistemaDescripcion}
                onChange={(e) => setNuevoSistemaDescripcion(e.target.value)}
                placeholder="Ej: SAP Business One"
                disabled={creandoSistema}
                data-testid="nuevo-sistema-input"
              />
            </div>
            
            {!permisosSistemas.puede_crear && (
              <div className="bg-amber-50 border border-amber-200 rounded-md p-3 text-sm text-amber-800">
                <strong>Nota:</strong> No tiene permisos para crear sistemas directamente. 
                Su solicitud será enviada para autorización.
              </div>
            )}
          </div>
          
          <DialogFooter className="gap-2">
            <Button 
              variant="outline" 
              onClick={() => {
                setNuevoSistemaModalOpen(false);
                setNuevoSistemaDescripcion('');
              }}
              disabled={creandoSistema}
            >
              Cancelar
            </Button>
            <Button 
              onClick={handleCrearNuevoSistema}
              disabled={creandoSistema || !nuevoSistemaDescripcion.trim()}
              data-testid="crear-sistema-btn"
            >
              {creandoSistema ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Procesando...
                </>
              ) : permisosSistemas.puede_crear ? (
                'Crear Sistema'
              ) : (
                'Solicitar'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Servidores;
