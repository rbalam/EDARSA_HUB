import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import api from '../lib/api';
import logger from '../services/logger';
import { getSessionUser } from '../services/authStorage';
import { useAuth } from '../contexts/AuthContext';
import { fetchUnidadesNegocio, getServerIdFromUnidad, getSucursalOrigenIdFromUnidad } from '../services/unidadesNegocioService';
import { 
  generateUnidadKey, 
  generateRequestId, 
  isLatestRequest, 
  validateResponse,
  normalizeComprasFilters,
  COMPRAS_STATUS,
  COMPRAS_STATUS_MESSAGES,
  getStatusFromResponse,
  logComprasEvent
} from '../services/comprasUtils';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Checkbox } from '../components/ui/checkbox';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
// Componentes/lógica CANÓNICOS compartidos con Análisis (Reportes.js) — regla de centralización
import DetalleProductoModal from '../components/compras/DetalleProductoModal';
import { useDetalleProducto } from '../hooks/useDetalleProducto';
import { fechaMinimaInventarios, filtrarInventariosFinales } from '../lib/inventarioSelectorUtils';
import { ExportButtons } from '../portal-inteligencia/components/ExportButtons';
import { 
  Loader2, ShoppingCart, Package, TrendingUp, AlertTriangle, Download, 
  AlertCircle, Calendar, Edit3, RefreshCw, Search, BarChart3, FileText,
  ChevronRight, ChevronDown, ExternalLink, FileWarning, CheckCircle2, XCircle, X,
  Calculator, Check, Plus, Trash2, Maximize2, Minimize2, Building2
} from 'lucide-react';
import PortalProveedoresTab from '../components/PortalProveedoresTab';
import { isAdminRole } from '../lib/roleUtils';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const STORAGE_KEY = 'compras_params';

// Helper: Placeholder para selectores según estado
const getSelectPlaceholder = (items, loadingText, emptyText, defaultText) => {
  if (items.length === 0) return emptyText || loadingText;
  return defaultText;
};

const formatNumber = (num) => {
  if (num === null || num === undefined) return '-';
  return new Intl.NumberFormat('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(num);
};

const formatCurrency = (num) => {
  if (num === null || num === undefined) return '-';
  return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(num);
};

// Constantes para meses y años
const MESES = [
  { value: '01', label: 'Enero' },
  { value: '02', label: 'Febrero' },
  { value: '03', label: 'Marzo' },
  { value: '04', label: 'Abril' },
  { value: '05', label: 'Mayo' },
  { value: '06', label: 'Junio' },
  { value: '07', label: 'Julio' },
  { value: '08', label: 'Agosto' },
  { value: '09', label: 'Septiembre' },
  { value: '10', label: 'Octubre' },
  { value: '11', label: 'Noviembre' },
  { value: '12', label: 'Diciembre' }
];

const getAniosDisponibles = () => {
  const currentYear = new Date().getFullYear();
  const years = [];
  for (let y = currentYear; y >= currentYear - 5; y--) {
    years.push({ value: y.toString(), label: y.toString() });
  }
  return years;
};

// ============ TAB 1: DASHBOARD DE COMPRAS ============
function DashboardCompras({ servers, unidadesNegocio, selectedUnidad, setSelectedUnidad, selectedServer, setSelectedServer, selectedSucursal, setSelectedSucursal, sucursales, loadingUnidades }) {
  const [kpis, setKpis] = useState(null);
  const [error, setError] = useState(null);
  const [alertas, setAlertas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [topProveedores, setTopProveedores] = useState([]);
  const [selectedMeses, setSelectedMeses] = useState([String(new Date().getMonth() + 1).padStart(2, '0')]);
  const [selectedAnios, setSelectedAnios] = useState([new Date().getFullYear().toString()]);
  const [showMesesDropdown, setShowMesesDropdown] = useState(false);
  const [showAniosDropdown, setShowAniosDropdown] = useState(false);
  const [status, setStatus] = useState(null); // Estado: SUCCESS, NO_DATA, ERROR_*
  const [errorMessage, setErrorMessage] = useState(null);
  
  // Ref para controlar race conditions
  const lastRequestRef = useRef({ unidadKey: null, requestId: 0 });
  
  const ANIOS = getAniosDisponibles();
  const selectedUnidadInfo = useMemo(
    () => unidadesNegocio.find(u => u.id === selectedUnidad) || null,
    [unidadesNegocio, selectedUnidad]
  );

  const cargarDashboard = useCallback(async () => {
    if (!selectedSucursal || !selectedUnidadInfo) return;
    
    // Generar unidad_key canónica para aislamiento
    const unidadKey = generateUnidadKey(selectedUnidadInfo);
    const requestId = generateRequestId(unidadKey, 'dashboard');
    
    // Guardar referencia para validar respuesta
    lastRequestRef.current = { unidadKey, requestId };
    
    logComprasEvent('compras_fetch_start', {
      unidad_key: unidadKey,
      tab: 'dashboard',
      request_id: requestId,
      server_id: selectedServer,
      sucursal_id: selectedSucursal,
      system_type: selectedUnidadInfo?.system_type,
      mes: selectedMeses.join(','),
      anio: selectedAnios.join(',')
    });
    
    setLoading(true);
    setStatus(COMPRAS_STATUS.LOADING);
    setErrorMessage(null);
    
    const startTime = Date.now();
    
    try {
      const response = await api.get(`/compras/dashboard/${selectedServer}?sucursal=${encodeURIComponent(selectedSucursal)}&meses=${selectedMeses.join(',')}&anios=${selectedAnios.join(',')}`);
      
      // Validar que la respuesta corresponde al request actual (evitar race conditions)
      if (!isLatestRequest(unidadKey, 'dashboard', requestId)) {
        logComprasEvent('compras_fetch_ignored_stale', {
          unidad_key: unidadKey,
          tab: 'dashboard',
          request_id: requestId,
          result: 'IGNORED_STALE'
        });
        return; // Ignorar respuesta tardía
      }
      
      const duration = Date.now() - startTime;
      
      // Verificar si hay error de conexión o servidor inaccesible
      if (response.data?.meta?.status === 'SERVER_UNREACHABLE' || 
          response.data?.meta?.status === 'COMPRAS_QUERY_ERROR') {
        setStatus(COMPRAS_STATUS.ERROR);
        setError(response.data.meta.mensaje || response.data.alertas?.[0]?.mensaje || 'Error de conexión');
        setKpis(null);
        setAlertas(response.data.alertas || []);
        setTopProveedores([]);
        logComprasEvent('compras_fetch_server_error', {
          unidad_key: unidadKey,
          tab: 'dashboard',
          request_id: requestId,
          duration_ms: duration,
          error_status: response.data.meta.status
        });
      }
      // Verificar si hay datos reales
      else if (!response.data?.kpis || (response.data.kpis.total_compras_mes === 0 && response.data.kpis.proveedores_activos === 0)) {
        setStatus(COMPRAS_STATUS.NO_DATA);
        setKpis(null);
        setAlertas([]);
        setTopProveedores([]);
        logComprasEvent('compras_fetch_no_data', {
          unidad_key: unidadKey,
          tab: 'dashboard',
          request_id: requestId,
          duration_ms: duration
        });
      } else {
        setKpis(response.data.kpis);
        setAlertas(response.data.alertas || []);
        setTopProveedores(response.data.top_proveedores || []);
        setStatus(COMPRAS_STATUS.SUCCESS);
        logComprasEvent('compras_fetch_success', {
          unidad_key: unidadKey,
          tab: 'dashboard',
          request_id: requestId,
          duration_ms: duration
        });
      }
    } catch (error) {
      // Solo procesar error si es el request actual
      if (!isLatestRequest(unidadKey, 'dashboard', requestId)) {
        return;
      }
      
      logger.error('Error cargando dashboard:', error);
      
      const errorStatus = getStatusFromResponse(null, error);
      setStatus(errorStatus);
      setErrorMessage(COMPRAS_STATUS_MESSAGES[errorStatus] || 'Error inesperado');
      
      // NO poner $0 en caso de error - dejar kpis en null para mostrar mensaje
      setKpis(null);
      setAlertas([]);
      setTopProveedores([]);
      
      logComprasEvent('compras_fetch_error', {
        unidad_key: unidadKey,
        tab: 'dashboard',
        request_id: requestId,
        error_code: errorStatus,
        duration_ms: Date.now() - startTime
      });
    } finally {
      // Solo cambiar loading si es el request actual
      if (isLatestRequest(unidadKey, 'dashboard', requestId)) {
        setLoading(false);
      }
    }
  }, [selectedServer, selectedSucursal, selectedMeses, selectedAnios, selectedUnidadInfo]);

  useEffect(() => {
    if (selectedServer && selectedSucursal) {
      cargarDashboard();
    }
  }, [selectedServer, selectedSucursal, selectedMeses, selectedAnios, cargarDashboard]);

  const toggleMes = (mes) => {
    setSelectedMeses(prev => {
      if (prev.includes(mes)) {
        if (prev.length === 1) return prev;
        return prev.filter(m => m !== mes);
      }
      return [...prev, mes].sort();
    });
  };

  const toggleAnio = (anio) => {
    setSelectedAnios(prev => {
      if (prev.includes(anio)) {
        if (prev.length === 1) return prev;
        return prev.filter(a => a !== anio);
      }
      return [...prev, anio].sort().reverse();
    });
  };

  const getMesesLabel = () => {
    if (selectedMeses.length === 0) return 'Seleccionar';
    if (selectedMeses.length === 1) {
      return MESES.find(m => m.value === selectedMeses[0])?.label || 'Mes';
    }
    if (selectedMeses.length === 12) return 'Todo el año';
    return `${selectedMeses.length} meses`;
  };

  const getAniosLabel = () => {
    if (selectedAnios.length === 0) return 'Seleccionar';
    if (selectedAnios.length === 1) {
      return selectedAnios[0];
    }
    return `${selectedAnios.length} años`;
  };

  return (
    <div className="space-y-4">
      {/* FASE 3.2: Selector de Unidad de Negocio (reemplaza Servidor) */}
      <Card className="border">
        <CardContent className="py-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex-1 min-w-[180px] max-w-xs">
              <Label className="text-xs mb-1 block">Unidad de Negocio</Label>
              {unidadesNegocio?.length === 1 ? (
                // Si solo hay una unidad, mostrar como texto (ya auto-seleccionada)
                <div className="flex h-10 w-full items-center rounded-md border border-input bg-zinc-50 px-3 py-2 text-sm">
                  <Building2 className="h-4 w-4 mr-2 text-zinc-500" />
                  {unidadesNegocio[0].nombre}
                </div>
              ) : (
                <Select value={selectedUnidad} onValueChange={setSelectedUnidad} disabled={loadingUnidades}>
                  <SelectTrigger data-testid="unidad-negocio-selector">
                    <SelectValue placeholder={loadingUnidades ? "Cargando..." : "Seleccionar unidad"} />
                  </SelectTrigger>
                  <SelectContent>
                    {unidadesNegocio?.map(u => (
                      <SelectItem key={u.id} value={u.id}>
                        <span className="flex items-center gap-2">
                          <Building2 className="h-3 w-3" />
                          {u.nombre}
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>
            {/* BLINDAJE DEFINITIVO: Selector de Sucursal ELIMINADO - Backend resuelve contexto */}
            {/* Selector de Meses (multiselección) */}
            <div className="flex-1 min-w-[150px] max-w-[200px] relative">
              <Label className="text-xs mb-1 block">Mes(es)</Label>
              <button
                type="button"
                onClick={() => setShowMesesDropdown(!showMesesDropdown)}
                className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                <span>{getMesesLabel()}</span>
                <ChevronDown className="h-4 w-4 opacity-50" />
              </button>
              {showMesesDropdown && (
                <div className="absolute z-50 mt-1 w-full rounded-md border bg-white shadow-lg max-h-60 overflow-auto">
                  <div className="p-2 border-b">
                    <button
                      type="button"
                      onClick={() => setSelectedMeses(MESES.map(m => m.value))}
                      className="text-xs text-blue-600 hover:underline mr-3"
                    >
                      Todos
                    </button>
                    <button
                      type="button"
                      onClick={() => setSelectedMeses([String(new Date().getMonth() + 1).padStart(2, '0')])}
                      className="text-xs text-blue-600 hover:underline"
                    >
                      Solo actual
                    </button>
                  </div>
                  {MESES.map(mes => (
                    <label
                      key={mes.value}
                      className="flex items-center gap-2 px-3 py-2 hover:bg-zinc-100 cursor-pointer"
                    >
                      <Checkbox
                        checked={selectedMeses.includes(mes.value)}
                        onCheckedChange={() => toggleMes(mes.value)}
                      />
                      <span className="text-sm">{mes.label}</span>
                    </label>
                  ))}
                  <div className="p-2 border-t">
                    <Button size="sm" onClick={() => setShowMesesDropdown(false)} className="w-full">
                      Aplicar
                    </Button>
                  </div>
                </div>
              )}
            </div>
            {/* Selector de Año (multiselección) */}
            <div className="flex-1 min-w-[120px] max-w-[160px] relative">
              <Label className="text-xs mb-1 block">Año(s)</Label>
              <button
                type="button"
                onClick={() => setShowAniosDropdown(!showAniosDropdown)}
                className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                <span>{getAniosLabel()}</span>
                <ChevronDown className="h-4 w-4 opacity-50" />
              </button>
              {showAniosDropdown && (
                <div className="absolute z-50 mt-1 w-full rounded-md border bg-white shadow-lg max-h-60 overflow-auto">
                  <div className="p-2 border-b">
                    <button
                      type="button"
                      onClick={() => setSelectedAnios([new Date().getFullYear().toString(), (new Date().getFullYear() - 1).toString()])}
                      className="text-xs text-blue-600 hover:underline mr-3"
                    >
                      Actual + Anterior
                    </button>
                    <button
                      type="button"
                      onClick={() => setSelectedAnios([new Date().getFullYear().toString()])}
                      className="text-xs text-blue-600 hover:underline"
                    >
                      Solo actual
                    </button>
                  </div>
                  {ANIOS.map(anio => (
                    <label
                      key={anio.value}
                      className="flex items-center gap-2 px-3 py-2 hover:bg-zinc-100 cursor-pointer"
                    >
                      <Checkbox
                        checked={selectedAnios.includes(anio.value)}
                        onCheckedChange={() => toggleAnio(anio.value)}
                      />
                      <span className="text-sm">{anio.label}</span>
                    </label>
                  ))}
                  <div className="p-2 border-t">
                    <Button size="sm" onClick={() => setShowAniosDropdown(false)} className="w-full">
                      Aplicar
                    </Button>
                  </div>
                </div>
              )}
            </div>
            <Button onClick={cargarDashboard} disabled={!selectedServer || !selectedSucursal || loading} className="mt-5">
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Actualizar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* KPIs */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
          <span className="ml-3 text-zinc-500">Cargando datos...</span>
        </div>
      )}
      
      {!loading && status === COMPRAS_STATUS.NO_DATA && (
        <Card className="border border-amber-200 bg-amber-50">
          <CardContent className="py-8 text-center">
            <AlertCircle className="h-12 w-12 mx-auto text-amber-500 mb-3" />
            <p className="text-amber-700 font-medium">{COMPRAS_STATUS_MESSAGES[COMPRAS_STATUS.NO_DATA]}</p>
            <p className="text-sm text-amber-600 mt-1">Intente con otro período o verifique la configuración</p>
          </CardContent>
        </Card>
      )}
      
      {!loading && status === COMPRAS_STATUS.ERROR && error && (
        <Card className="border border-orange-200 bg-orange-50">
          <CardContent className="py-8 text-center">
            <AlertTriangle className="h-12 w-12 mx-auto text-orange-500 mb-3" />
            <p className="text-orange-700 font-medium">Servidor no accesible</p>
            <p className="text-sm text-orange-600 mt-2">{error}</p>
            <p className="text-xs text-orange-500 mt-2">Este servidor requiere conexión VPN o estar en la red local</p>
            <Button variant="outline" onClick={cargarDashboard} className="mt-4">
              <RefreshCw className="h-4 w-4 mr-2" />
              Reintentar
            </Button>
          </CardContent>
        </Card>
      )}
      
      {!loading && errorMessage && status !== COMPRAS_STATUS.ERROR && (
        <Card className="border border-red-200 bg-red-50">
          <CardContent className="py-8 text-center">
            <AlertTriangle className="h-12 w-12 mx-auto text-red-500 mb-3" />
            <p className="text-red-700 font-medium">{errorMessage}</p>
            <Button variant="outline" onClick={cargarDashboard} className="mt-4">
              <RefreshCw className="h-4 w-4 mr-2" />
              Reintentar
            </Button>
          </CardContent>
        </Card>
      )}
      
      {!loading && kpis && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="border bg-gradient-to-br from-blue-50 to-white">
            <CardContent className="py-4">
              <p className="text-xs text-zinc-500">Compras del Mes</p>
              <p className="text-2xl font-bold text-blue-600">{formatCurrency(kpis.total_compras_mes)}</p>
            </CardContent>
          </Card>
          <Card className="border bg-gradient-to-br from-orange-50 to-white">
            <CardContent className="py-4">
              <p className="text-xs text-zinc-500">Requisiciones Pendientes</p>
              <p className="text-2xl font-bold text-orange-600">{kpis.requisiciones_pendientes}</p>
            </CardContent>
          </Card>
          <Card className="border bg-gradient-to-br from-green-50 to-white">
            <CardContent className="py-4">
              <p className="text-xs text-zinc-500">Proveedores Activos</p>
              <p className="text-2xl font-bold text-green-600">{kpis.proveedores_activos}</p>
            </CardContent>
          </Card>
          <Card className="border bg-gradient-to-br from-red-50 to-white">
            <CardContent className="py-4">
              <p className="text-xs text-zinc-500">Alertas Activas</p>
              <p className="text-2xl font-bold text-red-600">{kpis.alertas_activas}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Alertas de desviación */}
      {alertas.length > 0 && (
        <Card className="border border-red-200 bg-red-50">
          <CardHeader className="py-3">
            <CardTitle className="text-base flex items-center gap-2 text-red-700">
              <AlertTriangle className="h-5 w-5" />
              Alertas de Desviación Compras vs Consumos
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {alertas.map((alerta, idx) => (
              <div key={alerta.codigo || `alerta-${idx}`} className="flex items-center gap-3 p-2 bg-white rounded border border-red-200">
                <span className={`px-2 py-1 rounded text-xs font-semibold ${
                  alerta.tipo === 'sobrecompra' ? 'bg-red-100 text-red-700' : 'bg-orange-100 text-orange-700'
                }`}>
                  {alerta.tipo === 'sobrecompra' ? 'SOBRECOMPRA' : 'DESABASTO'}
                </span>
                <span className="font-medium">{alerta.producto}</span>
                <span className="text-sm text-zinc-500">
                  Ventas: <span className={alerta.variacion_ventas > 0 ? 'text-green-600' : 'text-red-600'}>
                    {alerta.variacion_ventas > 0 ? '+' : ''}{alerta.variacion_ventas}%
                  </span>
                </span>
                <span className="text-sm text-zinc-500">
                  Compras: <span className={alerta.variacion_compras > 0 ? 'text-green-600' : 'text-red-600'}>
                    {alerta.variacion_compras > 0 ? '+' : ''}{alerta.variacion_compras}%
                  </span>
                </span>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Top Proveedores */}
      {topProveedores.length > 0 && (
        <Card className="border">
          <CardHeader className="py-3">
            <CardTitle className="text-base">Top Proveedores del Mes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {topProveedores.map((prov, idx) => (
                <div key={prov.nombre || `prov-${idx}`} className="flex items-center justify-between p-2 bg-zinc-50 rounded">
                  <span className="font-medium">{prov.nombre}</span>
                  <span className="text-green-600 font-semibold">{formatCurrency(prov.total)}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ============ TAB 2: AUTORIZACIÓN (Código existente simplificado) ============
function AutorizacionComprasTab({ servers, unidadesNegocio, selectedUnidad, setSelectedUnidad, selectedServer, setSelectedServer, selectedSucursal: parentSucursal, setSelectedSucursal: setParentSucursal, sucursales: parentSucursales }) {
  // Este componente usa las sucursales del padre para mantener sincronización
  const [serverData, setServerData] = useState(null);
  const [almacenes, setAlmacenes] = useState([]);
  const [selectedAlmacenes, setSelectedAlmacenes] = useState([]);
  const [todosAlmacenes, setTodosAlmacenes] = useState(false);
  const [fechaInvFisico, setFechaInvFisico] = useState('');
  const [fechaFinPeriodo, setFechaFinPeriodo] = useState(new Date().toISOString().split('T')[0]);
  const [diasInventario, setDiasInventario] = useState(10);
  const [metodoCalculo, setMetodoCalculo] = useState('consumo');
  const [inventariosFisicos, setInventariosFisicos] = useState([]);
  const [inventariosFiltrados, setInventariosFiltrados] = useState([]);
  const [folioInvFisico, setFolioInvFisico] = useState('');
  const [pedidosVigentes, setPedidosVigentes] = useState([]);
  const [folioPedidoComparar, setFolioPedidoComparar] = useState('');
  const [folioManual, setFolioManual] = useState('');
  const [usarFolioManual, setUsarFolioManual] = useState(false);
  const [loading, setLoading] = useState(false);
  const [pedidoData, setPedidoData] = useState([]);
  const [resumen, setResumen] = useState(null);
  const [infoInventario, setInfoInventario] = useState(null);

  useEffect(() => {
    if (selectedServer) {
      const server = servers.find(s => s.id === selectedServer);
      setServerData(server);
    }
  }, [selectedServer, servers]);

  // Definir las funciones ANTES de usarlas en useEffect
  const fetchAlmacenes = useCallback(async (serverId, sucursal) => {
    try {
      const response = await api.get(`/servers/${serverId}/almacenes?sucursal=${encodeURIComponent(sucursal)}`);
      const unique = [...new Map(response.data.map(a => [a.nombre, a])).values()];
      setAlmacenes(unique);
    } catch (error) {
      logger.error('Error cargando almacenes:', error);
    }
  }, []);

  const fetchInventariosFisicos = useCallback(async (serverId, sucursal) => {
    try {
      const response = await api.get(`/compras/inventarios-fisicos/${serverId}?sucursal=${encodeURIComponent(sucursal)}`);
      setInventariosFisicos(response.data);
      if (response.data.length > 0) {
        setFolioInvFisico(response.data[0].folio);
        setFechaInvFisico(response.data[0].fecha.split('T')[0]);
      }
    } catch (error) {
      logger.error('Error cargando inventarios físicos:', error);
    }
  }, []);

  const fetchPedidosVigentes = useCallback(async (serverId, sucursal) => {
    try {
      const response = await api.get(`/compras/pedidos-vigentes/${serverId}?sucursal=${encodeURIComponent(sucursal)}`);
      setPedidosVigentes(response.data || []);
    } catch (error) {
      logger.error('Error cargando pedidos vigentes:', error);
      setPedidosVigentes([]);
    }
  }, []);

  useEffect(() => {
    if (selectedServer && parentSucursal) {
      fetchAlmacenes(selectedServer, parentSucursal);
      fetchInventariosFisicos(selectedServer, parentSucursal);
      fetchPedidosVigentes(selectedServer, parentSucursal);
    }
  }, [selectedServer, parentSucursal, fetchAlmacenes, fetchInventariosFisicos, fetchPedidosVigentes]);

  useEffect(() => {
    if (todosAlmacenes || selectedAlmacenes.includes('TODOS')) {
      const grouped = {};
      inventariosFisicos.forEach(inv => {
        const key = inv.fecha.split('T')[0];
        if (!grouped[key]) grouped[key] = { fecha: inv.fecha, almacenes: [], comentario: inv.comentario };
        grouped[key].almacenes.push(inv.almacen);
      });
      const consolidated = Object.entries(grouped).map(([fecha, data]) => ({
        folio: `TODOS-${fecha}`,
        fecha: data.fecha,
        almacen: `${data.almacenes.length} almacenes`,
        comentario: data.comentario || '',
        isTodos: true
      }));
      setInventariosFiltrados(consolidated.slice(0, 30));
    } else if (selectedAlmacenes.length >= 1) {
      const filtered = inventariosFisicos.filter(inv => 
        selectedAlmacenes.some(a => inv.almacen.toLowerCase().includes(a.toLowerCase()))
      );
      setInventariosFiltrados(filtered.slice(0, 50));
    } else {
      setInventariosFiltrados(inventariosFisicos.slice(0, 50));
    }
  }, [selectedAlmacenes, todosAlmacenes, inventariosFisicos]);

  const handleAlmacenToggle = (almacenNombre) => {
    setSelectedAlmacenes(prev => {
      if (prev.includes(almacenNombre)) {
        return prev.filter(a => a !== almacenNombre);
      }
      return [...prev, almacenNombre];
    });
    setTodosAlmacenes(false);
    setFolioInvFisico('');
  };

  const handleTodosAlmacenes = (checked) => {
    setTodosAlmacenes(checked);
    if (checked) {
      setSelectedAlmacenes(['TODOS']);
      setFolioInvFisico('');
    } else {
      setSelectedAlmacenes([]);
    }
  };

  const calcularPedido = async () => {
    if (!selectedServer || !parentSucursal || (selectedAlmacenes.length === 0 && !todosAlmacenes)) {
      toast.error('Selecciona unidad de negocio, sucursal y al menos un almacén');
      return;
    }
    if (!fechaInvFisico || !fechaFinPeriodo) {
      toast.error('Selecciona las fechas del período de análisis');
      return;
    }
    if (!folioPedidoComparar && !usarFolioManual) {
      toast.error('Selecciona una requisición para comparar');
      return;
    }

    setLoading(true);
    setPedidoData([]);
    setResumen(null);

    try {
      const folioComparar = usarFolioManual ? folioManual : folioPedidoComparar;
      const folioEnviar = (todosAlmacenes || folioInvFisico?.startsWith('TODOS-')) ? null : folioInvFisico;
      
      const response = await api.post(`/compras/calculo-pedido`, {
        server_id: selectedServer,
        sucursal: parentSucursal,
        almacenes: todosAlmacenes ? ['TODOS'] : selectedAlmacenes,
        fecha_inventario_fisico: fechaInvFisico,
        fecha_fin_periodo: fechaFinPeriodo,
        dias_inventario: parseInt(diasInventario),
        metodo_calculo: metodoCalculo,
        folio_inventario_fisico: folioEnviar,
        folio_pedido_comparar: folioComparar
      });

      setPedidoData(response.data.data);
      setInfoInventario(response.data);
      
      const data = response.data.data;
      setResumen({
        totalProductos: data.length,
        productosAPedir: data.filter(p => p.Cantidad_Pedir > 0).length,
        costoTotalPedido: data.reduce((sum, p) => sum + (p.Costo_Pedido || 0), 0),
        productosStockBajo: data.filter(p => p.Dias_Inventario < 3 && p.Dias_Inventario !== 999).length,
      });

      toast.success(`Cálculo completado: ${response.data.count} productos`);
    } catch (error) {
      logger.error('Error calculando pedido:', error);
      const errorDetail = error.response?.data?.detail;
      let errorMsg = 'Error al calcular pedido';
      if (typeof errorDetail === 'string') {
        errorMsg = errorDetail;
      } else if (Array.isArray(errorDetail)) {
        errorMsg = errorDetail.map(e => e.msg || e.message || JSON.stringify(e)).join(', ');
      }
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Parámetros */}
      <Card className="border">
        <CardHeader className="py-3">
          <CardTitle className="text-base flex items-center gap-2">
            <ShoppingCart className="h-5 w-5 text-blue-600" />
            Parámetros del Cálculo
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="space-y-1">
              <Label className="text-xs">Unidad de Negocio</Label>
              {unidadesNegocio?.length === 1 ? (
                <div className="flex h-9 w-full items-center rounded-md border border-input bg-zinc-50 px-3 py-2 text-sm">
                  <Building2 className="h-3 w-3 mr-1 text-zinc-500" />
                  <span className="text-xs">{unidadesNegocio[0].nombre}</span>
                </div>
              ) : (
                <Select value={selectedUnidad} onValueChange={setSelectedUnidad}>
                  <SelectTrigger className="h-9">
                    <SelectValue placeholder="Seleccionar" />
                  </SelectTrigger>
                  <SelectContent>
                    {unidadesNegocio?.map(u => (
                      <SelectItem key={u.id} value={u.id}>
                        <span className="flex items-center gap-1">
                          <Building2 className="h-3 w-3" />
                          {u.nombre}
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>
            {/* BLINDAJE DEFINITIVO: Selector de Sucursal ELIMINADO - Backend resuelve contexto */}
            <div className="space-y-1">
              <Label className="text-xs">Folio Inv. Inicial</Label>
              <Select value={folioInvFisico} onValueChange={(val) => { 
                setFolioInvFisico(val); 
                const inv = inventariosFiltrados.find(i => i.folio === val); 
                if (inv) setFechaInvFisico(inv.fecha.split('T')[0]); 
              }} disabled={todosAlmacenes}>
                <SelectTrigger className="h-9">
                  <SelectValue placeholder={todosAlmacenes ? "Consolidado" : "Seleccionar"} />
                </SelectTrigger>
                <SelectContent className="max-h-72 overflow-y-auto">
                  {inventariosFiltrados.map(inv => (
                    <SelectItem key={inv.folio} value={inv.folio}>
                      {inv.folio} ({new Date(inv.fecha).toLocaleDateString('es-MX')}) - {inv.comentario || inv.almacen || ''}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Método Cálculo</Label>
              <Select value={metodoCalculo} onValueChange={setMetodoCalculo}>
                <SelectTrigger className="h-9">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="consumo">Por Consumo</SelectItem>
                  <SelectItem value="stock">Por Stock Máx</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {almacenes.length > 0 && (
            <div className="space-y-1">
              <Label className="text-xs">Almacenes</Label>
              <div className="flex flex-wrap gap-2 p-2 border rounded-md bg-zinc-50 text-sm max-h-20 overflow-y-auto">
                <div className="flex items-center gap-1">
                  <Checkbox id="todos" checked={todosAlmacenes} onCheckedChange={handleTodosAlmacenes} />
                  <label htmlFor="todos" className="font-medium">TODOS</label>
                </div>
                <div className="w-px h-5 bg-zinc-300" />
                {almacenes.map(alm => (
                  <div key={alm.nombre} className="flex items-center gap-1">
                    <Checkbox id={`a-${alm.nombre}`} checked={selectedAlmacenes.includes(alm.nombre)} onCheckedChange={() => handleAlmacenToggle(alm.nombre)} disabled={todosAlmacenes} />
                    <label htmlFor={`a-${alm.nombre}`}>{alm.nombre}</label>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="space-y-1">
              <Label className="text-xs">Fecha Inv. Inicial</Label>
              <Input type="date" value={fechaInvFisico} onChange={(e) => setFechaInvFisico(e.target.value)} className="h-9" />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Fecha Fin Período</Label>
              <Input type="date" value={fechaFinPeriodo} onChange={(e) => setFechaFinPeriodo(e.target.value)} className="h-9" />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Días Inv. a Comprar</Label>
              <Input type="number" min="1" max="90" value={diasInventario} onChange={(e) => setDiasInventario(e.target.value)} className="h-9" />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Comparar con Requisición</Label>
              <Select value={folioPedidoComparar} onValueChange={setFolioPedidoComparar}>
                <SelectTrigger className="h-9">
                  <SelectValue placeholder="Seleccionar requisición" />
                </SelectTrigger>
                <SelectContent className="max-h-60 overflow-y-auto">
                  {pedidosVigentes.map(p => (
                    <SelectItem key={`${p.tipo}-${p.folio}`} value={p.folio}>
                      {p.folio} - {p.comentario || p.comprador || 'Sin desc.'}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex gap-2 pt-2">
            <Button onClick={calcularPedido} disabled={loading || !selectedServer || !parentSucursal}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
              Calcular Pedido
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* KPIs */}
      {resumen && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          <Card className="border"><CardContent className="py-3"><p className="text-xs text-zinc-500">Total</p><p className="text-lg font-bold">{resumen.totalProductos}</p></CardContent></Card>
          <Card className="border"><CardContent className="py-3"><p className="text-xs text-zinc-500">A Pedir</p><p className="text-lg font-bold text-green-600">{resumen.productosAPedir}</p></CardContent></Card>
          <Card className="border"><CardContent className="py-3"><p className="text-xs text-zinc-500">Costo</p><p className="text-base font-bold">{formatCurrency(resumen.costoTotalPedido)}</p></CardContent></Card>
          <Card className="border"><CardContent className="py-3"><p className="text-xs text-zinc-500">Stock Bajo</p><p className="text-lg font-bold text-red-600">{resumen.productosStockBajo}</p></CardContent></Card>
        </div>
      )}

      {/* Tabla de resultados */}
      {pedidoData.length > 0 && (
        <Card className="border">
          <CardHeader className="py-2">
            <CardTitle className="text-base">Pedido Sugerido ({pedidoData.filter(p => p.Cantidad_Pedir > 0).length} a pedir)</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="max-h-[400px] overflow-auto">
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-zinc-200">
                  <tr>
                    <th className="py-2 px-2 text-left">Código</th>
                    <th className="py-2 px-2 text-left">Producto</th>
                    <th className="py-2 px-2 text-right">Inv.Ini</th>
                    <th className="py-2 px-2 text-right">Movim.</th>
                    <th className="py-2 px-2 text-right">Consumos</th>
                    <th className="py-2 px-2 text-right">Teórico</th>
                    <th className="py-2 px-2 text-right">Días</th>
                    <th className="py-2 px-2 text-right text-green-700">Pedir</th>
                    <th className="py-2 px-2 text-right">Costo</th>
                  </tr>
                </thead>
                <tbody>
                  {pedidoData.slice(0, 100).map((row, idx) => (
                    <tr key={row.Codigo || `pedido-${idx}`} className="border-b hover:bg-zinc-50">
                      <td className="py-1 px-2 font-mono">{row.Codigo}</td>
                      <td className="py-1 px-2 max-w-[150px] truncate">{row.Producto}</td>
                      <td className="py-1 px-2 text-right">{formatNumber(row.Inventario_Inicial)}</td>
                      <td className="py-1 px-2 text-right">{formatNumber(row.Movimientos_Periodo)}</td>
                      <td className="py-1 px-2 text-right text-red-600">{formatNumber(row.Consumos_Periodo)}</td>
                      <td className="py-1 px-2 text-right font-semibold">{formatNumber(row.Inventario_Teorico)}</td>
                      <td className="py-1 px-2 text-right">{row.Dias_Inventario >= 999 ? '∞' : formatNumber(row.Dias_Inventario)}</td>
                      <td className="py-1 px-2 text-right font-bold text-green-700">{formatNumber(row.Cantidad_Pedir)}</td>
                      <td className="py-1 px-2 text-right">{formatCurrency(row.Costo_Pedido)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ============ TAB 3: ANÁLISIS DE COMPRAS (MultiAnálisis) ============
function AnalisisCompras({ servers, unidadesNegocio, selectedUnidad, setSelectedUnidad, selectedServer, setSelectedServer, selectedSucursal, setSelectedSucursal, sucursales }) {
  const [loading, setLoading] = useState(false);
  const [loadingFacturas, setLoadingFacturas] = useState(false);
  const [loadingProductos, setLoadingProductos] = useState(false);
  const [aniosSeleccionados, setAniosSeleccionados] = useState([new Date().getFullYear().toString()]);
  const [mesesSeleccionados, setMesesSeleccionados] = useState([String(new Date().getMonth() + 1).padStart(2, '0')]);
  const [comprasPorProveedor, setComprasPorProveedor] = useState([]);
  const [expandedProveedor, setExpandedProveedor] = useState(null);
  const [detalleFacturas, setDetalleFacturas] = useState([]);
  const [expandedFactura, setExpandedFactura] = useState(null);
  const [detalleProductos, setDetalleProductos] = useState([]);
  const [alertasDesviacion, setAlertasDesviacion] = useState([]);
  const [modalDocumento, setModalDocumento] = useState({ open: false, tipo: '', url: '', data: null });
  
  // Nuevos estados para KPIs
  const [kpis, setKpis] = useState({ totalCompras: 0, numProveedores: 0, numFacturas: 0, promedioFactura: 0 });

  const meses = [
    { value: '01', label: 'Ene' }, { value: '02', label: 'Feb' }, { value: '03', label: 'Mar' },
    { value: '04', label: 'Abr' }, { value: '05', label: 'May' }, { value: '06', label: 'Jun' },
    { value: '07', label: 'Jul' }, { value: '08', label: 'Ago' }, { value: '09', label: 'Sep' },
    { value: '10', label: 'Oct' }, { value: '11', label: 'Nov' }, { value: '12', label: 'Dic' },
  ];

  const aniosDisponibles = getAniosDisponibles();

  const cargarAnalisis = useCallback(async () => {
    if (!selectedServer || !selectedSucursal) {
      return;
    }
    setLoading(true);
    setExpandedProveedor(null);
    setExpandedFactura(null);
    try {
      const response = await api.post(`/compras/analisis`, {
        server_id: selectedServer,
        sucursal: selectedSucursal,
        anios: aniosSeleccionados,
        meses: mesesSeleccionados
      });
      const proveedores = response.data.proveedores || [];
      const kpisBackend = response.data.kpis || {};
      setComprasPorProveedor(proveedores);
      setAlertasDesviacion(response.data.alertas || []);
      setKpis({
        totalCompras: kpisBackend.totalCompras ?? kpisBackend.total_compras ?? 0,
        numProveedores: kpisBackend.numProveedores ?? kpisBackend.num_proveedores ?? 0,
        numFacturas: kpisBackend.numFacturas ?? kpisBackend.num_facturas ?? 0,
        promedioFactura: kpisBackend.promedioFactura ?? kpisBackend.promedio_factura ?? 0
      });
    } catch (error) {
      logger.error('Error:', error);
      setComprasPorProveedor([]);
      setAlertasDesviacion([]);
      setKpis({ totalCompras: 0, numProveedores: 0, numFacturas: 0, promedioFactura: 0 });
    } finally {
      setLoading(false);
    }
  }, [selectedServer, selectedSucursal, aniosSeleccionados, mesesSeleccionados]);

  // Auto-analizar cuando cambian los filtros
  useEffect(() => {
    if (selectedServer && selectedSucursal && mesesSeleccionados.length > 0 && aniosSeleccionados.length > 0) {
      cargarAnalisis();
    }
  }, [selectedServer, selectedSucursal, mesesSeleccionados, aniosSeleccionados, cargarAnalisis]);

  const toggleMes = (mes) => {
    setMesesSeleccionados(prev => {
      if (prev.includes(mes)) {
        if (prev.length === 1) return prev;
        return prev.filter(m => m !== mes);
      }
      return [...prev, mes].sort();
    });
  };

  const toggleAnio = (anio) => {
    setAniosSeleccionados(prev => {
      if (prev.includes(anio)) {
        if (prev.length === 1) return prev;
        return prev.filter(a => a !== anio);
      }
      return [...prev, anio].sort();
    });
  };

  // Cargar facturas reales del backend
  const verDetalleProveedor = async (proveedor) => {
    if (expandedProveedor === proveedor.codigo) {
      setExpandedProveedor(null);
      setDetalleFacturas([]);
      return;
    }
    setExpandedProveedor(proveedor.codigo);
    setExpandedFactura(null);
    setDetalleFacturas([]);
    setLoadingFacturas(true);
    
    try {
      const anioPrincipal = Math.max(...aniosSeleccionados.map(a => parseInt(a)));
      const response = await api.get(`/compras/facturas-proveedor/${selectedServer}`, {
        params: {
          proveedor_codigo: proveedor.codigo,
          anio: anioPrincipal,
          meses: mesesSeleccionados.join(','),
          sucursal: selectedSucursal
        },
      });
      setDetalleFacturas(response.data || []);
    } catch (error) {
      logger.error('Error cargando facturas:', error);
      toast.error('Error al cargar facturas del proveedor');
      setDetalleFacturas([]);
    } finally {
      setLoadingFacturas(false);
    }
  };

  // Cargar productos reales del backend
  const verDetalleFactura = async (factura) => {
    if (expandedFactura === factura.folio) {
      setExpandedFactura(null);
      setDetalleProductos([]);
      return;
    }
    setExpandedFactura(factura.folio);
    setDetalleProductos([]);
    setLoadingProductos(true);
    
    try {
      const response = await api.get(`/compras/detalle-factura/${selectedServer}/${encodeURIComponent(factura.folio)}`, {
        params: { sucursal: selectedSucursal },
      });
      setDetalleProductos(response.data || []);
    } catch (error) {
      logger.error('Error cargando detalle:', error);
      toast.error('Error al cargar detalle de factura');
      setDetalleProductos([]);
    } finally {
      setLoadingProductos(false);
    }
  };

  const totalGeneral = comprasPorProveedor.reduce((sum, p) => sum + (p.total || 0), 0);

  return (
    <div className="space-y-4">
      {/* Filtros compactos - FASE 3.2: Unidad de Negocio */}
      <Card className="border">
        <CardContent className="py-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex-1 min-w-[160px] max-w-[200px] space-y-1">
              <Label className="text-xs">Unidad de Negocio</Label>
              {unidadesNegocio?.length === 1 ? (
                <div className="flex h-9 w-full items-center rounded-md border border-input bg-zinc-50 px-3 py-2 text-sm">
                  <Building2 className="h-3 w-3 mr-1 text-zinc-500" />
                  <span className="text-xs">{unidadesNegocio[0].nombre}</span>
                </div>
              ) : (
                <Select value={selectedUnidad} onValueChange={setSelectedUnidad}>
                  <SelectTrigger className="h-9">
                    <SelectValue placeholder="Seleccionar" />
                  </SelectTrigger>
                  <SelectContent>
                    {unidadesNegocio?.map(u => (
                      <SelectItem key={u.id} value={u.id}>
                        <span className="flex items-center gap-1">
                          <Building2 className="h-3 w-3" />
                          {u.nombre}
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>
            {/* BLINDAJE DEFINITIVO: Selector de Sucursal ELIMINADO - Backend resuelve contexto */}
            
            {/* Años inline */}
            <div className="space-y-1">
              <Label className="text-xs">Año(s)</Label>
              <div className="flex gap-1">
                {aniosDisponibles.slice(0, 4).map(a => (
                  <Button
                    key={a.value}
                    variant={aniosSeleccionados.includes(a.value) ? "default" : "outline"}
                    size="sm"
                    className="h-9 px-3"
                    onClick={() => toggleAnio(a.value)}
                  >
                    {a.label}
                  </Button>
                ))}
              </div>
            </div>
            
            {/* Meses inline */}
            <div className="flex-1 space-y-1">
              <Label className="text-xs">Meses</Label>
              <div className="flex flex-wrap gap-1">
                {meses.map(m => (
                  <Button
                    key={m.value}
                    variant={mesesSeleccionados.includes(m.value) ? "default" : "outline"}
                    size="sm"
                    className="h-9 px-2 text-xs"
                    onClick={() => toggleMes(m.value)}
                  >
                    {m.label}
                  </Button>
                ))}
              </div>
            </div>
            
            {loading && (
              <div className="flex items-center text-sm text-zinc-500">
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Cargando...
              </div>
            )}
          </div>
        </CardContent>
      </Card>
      
      {/* KPIs */}
      {comprasPorProveedor.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Card className="border bg-gradient-to-br from-green-50 to-white" data-testid="kpi-total-compras">
            <CardContent className="py-3">
              <p className="text-xs text-zinc-500">Total Compras</p>
              <p className="text-xl font-bold text-green-600">{formatCurrency(kpis.totalCompras)}</p>
            </CardContent>
          </Card>
          <Card className="border bg-gradient-to-br from-blue-50 to-white" data-testid="kpi-proveedores">
            <CardContent className="py-3">
              <p className="text-xs text-zinc-500">Proveedores</p>
              <p className="text-xl font-bold text-blue-600">{kpis.numProveedores}</p>
            </CardContent>
          </Card>
          <Card className="border bg-gradient-to-br from-purple-50 to-white" data-testid="kpi-promedio">
            <CardContent className="py-3">
              <p className="text-xs text-zinc-500">Promedio x Factura</p>
              <p className="text-xl font-bold text-purple-600">{formatCurrency(kpis.promedioFactura)}</p>
            </CardContent>
          </Card>
          <Card className="border bg-gradient-to-br from-orange-50 to-white" data-testid="kpi-meses">
            <CardContent className="py-3">
              <p className="text-xs text-zinc-500">Meses Seleccionados</p>
              <p className="text-xl font-bold text-orange-600">{mesesSeleccionados.length}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Alertas de desviación */}
      {alertasDesviacion.length > 0 && (
        <Card className="border border-red-200 bg-red-50">
          <CardHeader className="py-2">
            <CardTitle className="text-sm flex items-center gap-2 text-red-700">
              <AlertTriangle className="h-4 w-4" />
              Alertas: Compras vs Consumos
            </CardTitle>
          </CardHeader>
          <CardContent className="py-2">
            <div className="space-y-1">
              {alertasDesviacion.map((a, idx) => (
                <div key={a.producto || `desv-${idx}`} className="flex items-center gap-2 text-sm">
                  {a.tipo === 'sobrecompra' ? (
                    <XCircle className="h-4 w-4 text-red-600" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-orange-600" />
                  )}
                  <span className="font-medium">{a.producto}:</span>
                  <span>Ventas {a.var_ventas > 0 ? '+' : ''}{a.var_ventas}%</span>
                  <span>Compras {a.var_compras > 0 ? '+' : ''}{a.var_compras}%</span>
                  <span className={`px-2 py-0.5 rounded text-xs ${a.tipo === 'sobrecompra' ? 'bg-red-200 text-red-800' : 'bg-orange-200 text-orange-800'}`}>
                    {a.tipo === 'sobrecompra' ? 'SOBRECOMPRA' : 'DESABASTO'}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabla de compras por proveedor */}
      {comprasPorProveedor.length > 0 && (
        <Card className="border">
          <CardHeader className="py-2">
            <CardTitle className="text-base flex items-center justify-between">
              <span className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-blue-600" />
                Compras por Proveedor
              </span>
              <span className="text-green-600 font-bold">{formatCurrency(totalGeneral)}</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="max-h-[500px] overflow-auto">
              <table className="w-full text-sm" data-testid="tabla-proveedores">
                <thead className="sticky top-0 bg-zinc-800 text-white">
                  <tr>
                    <th className="py-2 px-3 text-left w-8"></th>
                    <th className="py-2 px-3 text-left">Proveedor</th>
                    {mesesSeleccionados.map(m => (
                      <th key={m} className="py-2 px-3 text-right">{meses.find(x => x.value === m)?.label}</th>
                    ))}
                    <th className="py-2 px-3 text-right font-bold">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {comprasPorProveedor.map((prov, idx) => (
                    <React.Fragment key={prov.proveedor || `compra-prov-${idx}`}>
                      <tr 
                        className="border-b hover:bg-zinc-50 cursor-pointer transition-colors"
                        onClick={() => verDetalleProveedor(prov)}
                        data-testid={`proveedor-row-${idx}`}
                      >
                        <td className="py-2 px-3">
                          {expandedProveedor === prov.codigo ? (
                            <ChevronDown className="h-4 w-4 text-blue-600" />
                          ) : (
                            <ChevronRight className="h-4 w-4" />
                          )}
                        </td>
                        <td className="py-2 px-3">
                          <span className="font-mono text-xs text-zinc-400 mr-2">{prov.codigo}</span>
                          <span className="font-medium">{prov.nombre}</span>
                        </td>
                        {mesesSeleccionados.map(m => (
                          <td key={m} className="py-2 px-3 text-right">
                            {prov[m] ? formatCurrency(prov[m]) : <span className="text-zinc-300">-</span>}
                          </td>
                        ))}
                        <td className="py-2 px-3 text-right font-bold text-green-600">{formatCurrency(prov.total)}</td>
                      </tr>
                      
                      {/* Detalle de facturas (drill-down nivel 1) */}
                      {expandedProveedor === prov.codigo && (
                        <tr>
                          <td colSpan={mesesSeleccionados.length + 3} className="bg-zinc-100 p-0">
                            <div className="p-3">
                              <div className="flex items-center justify-between mb-2">
                                <p className="text-xs font-semibold text-zinc-600 flex items-center gap-2">
                                  <FileText className="h-4 w-4" />
                                  FACTURAS / ENTRADAS DE {prov.nombre}
                                </p>
                                {loadingFacturas && <Loader2 className="h-4 w-4 animate-spin text-blue-600" />}
                              </div>
                              
                              {loadingFacturas ? (
                                <div className="py-4 text-center text-zinc-500">
                                  <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2" />
                                  Cargando facturas...
                                </div>
                              ) : detalleFacturas.length === 0 ? (
                                <div className="py-4 text-center text-zinc-500">
                                  No se encontraron facturas en el período seleccionado
                                </div>
                              ) : (
                                <table className="w-full text-xs">
                                  <thead className="bg-zinc-200">
                                    <tr>
                                      <th className="py-1 px-2 text-left w-6"></th>
                                      <th className="py-1 px-2 text-left">Folio</th>
                                      <th className="py-1 px-2 text-left">Fecha</th>
                                      <th className="py-1 px-2 text-right">Productos</th>
                                      <th className="py-1 px-2 text-right">Importe</th>
                                      <th className="py-1 px-2 text-center">Status</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {detalleFacturas.map((fac, fidx) => (
                                      <React.Fragment key={fidx}>
                                        <tr 
                                          className="border-b hover:bg-white cursor-pointer transition-colors"
                                          onClick={(e) => { e.stopPropagation(); verDetalleFactura(fac); }}
                                          data-testid={`factura-row-${fidx}`}
                                        >
                                          <td className="py-1 px-2">
                                            {expandedFactura === fac.folio ? (
                                              <ChevronDown className="h-3 w-3 text-blue-600" />
                                            ) : (
                                              <ChevronRight className="h-3 w-3" />
                                            )}
                                          </td>
                                          <td className="py-1 px-2 font-mono font-medium">{fac.folio}</td>
                                          <td className="py-1 px-2">{fac.fecha?.split('T')[0] || fac.fecha}</td>
                                          <td className="py-1 px-2 text-right">{fac.productos}</td>
                                          <td className="py-1 px-2 text-right font-semibold">{formatCurrency(fac.importe)}</td>
                                          <td className="py-1 px-2 text-center">
                                            <span className={`px-2 py-0.5 rounded text-xs ${
                                              fac.status === 'pagada' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                                            }`}>
                                              {fac.status || 'pendiente'}
                                            </span>
                                          </td>
                                        </tr>
                                        
                                        {/* Detalle de productos (drill-down nivel 2) */}
                                        {expandedFactura === fac.folio && (
                                          <tr>
                                            <td colSpan={6} className="bg-white p-2">
                                              {loadingProductos ? (
                                                <div className="py-4 text-center text-zinc-500">
                                                  <Loader2 className="h-5 w-5 animate-spin mx-auto mb-2" />
                                                  Cargando productos...
                                                </div>
                                              ) : detalleProductos.length === 0 ? (
                                                <div className="py-3 text-center text-zinc-500 text-xs">
                                                  No se encontraron productos
                                                </div>
                                              ) : (
                                                <table className="w-full text-xs">
                                                  <thead className="bg-blue-50">
                                                    <tr>
                                                      <th className="py-1 px-2 text-left">Código</th>
                                                      <th className="py-1 px-2 text-left">Producto</th>
                                                      <th className="py-1 px-2 text-right">Cantidad</th>
                                                      <th className="py-1 px-2 text-right">Costo Unit.</th>
                                                      <th className="py-1 px-2 text-right">Importe</th>
                                                    </tr>
                                                  </thead>
                                                  <tbody>
                                                    {detalleProductos.map((prod, pidx) => (
                                                      <tr key={pidx} className="border-b hover:bg-blue-50/50">
                                                        <td className="py-1 px-2 font-mono text-zinc-500">{prod.codigo}</td>
                                                        <td className="py-1 px-2">{prod.producto}</td>
                                                        <td className="py-1 px-2 text-right">{formatNumber(prod.cantidad)}</td>
                                                        <td className="py-1 px-2 text-right">{formatCurrency(prod.costo)}</td>
                                                        <td className="py-1 px-2 text-right font-semibold text-green-600">{formatCurrency(prod.importe)}</td>
                                                      </tr>
                                                    ))}
                                                  </tbody>
                                                  <tfoot className="bg-zinc-100">
                                                    <tr>
                                                      <td colSpan={4} className="py-1 px-2 text-right font-semibold">Total:</td>
                                                      <td className="py-1 px-2 text-right font-bold text-green-600">
                                                        {formatCurrency(detalleProductos.reduce((sum, p) => sum + (p.importe || 0), 0))}
                                                      </td>
                                                    </tr>
                                                  </tfoot>
                                                </table>
                                              )}
                                            </td>
                                          </tr>
                                        )}
                                      </React.Fragment>
                                    ))}
                                  </tbody>
                                  <tfoot className="bg-zinc-200">
                                    <tr>
                                      <td colSpan={4} className="py-1 px-2 text-right font-semibold">Total Facturas:</td>
                                      <td className="py-1 px-2 text-right font-bold text-green-700">
                                        {formatCurrency(detalleFacturas.reduce((sum, f) => sum + (f.importe || 0), 0))}
                                      </td>
                                      <td></td>
                                    </tr>
                                  </tfoot>
                                </table>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
                <tfoot className="bg-zinc-800 text-white">
                  <tr>
                    <td colSpan={2} className="py-2 px-3 font-bold">TOTAL GENERAL</td>
                    {mesesSeleccionados.map(m => {
                      const totalMes = comprasPorProveedor.reduce((sum, p) => sum + (p[m] || 0), 0);
                      return (
                        <td key={m} className="py-2 px-3 text-right font-semibold">
                          {formatCurrency(totalMes)}
                        </td>
                      );
                    })}
                    <td className="py-2 px-3 text-right font-bold text-green-400">{formatCurrency(totalGeneral)}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Estado vacío */}
      {!loading && comprasPorProveedor.length === 0 && selectedServer && selectedSucursal && (
        <Card className="border">
          <CardContent className="py-12 text-center text-zinc-500">
            <Package className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p className="font-medium">No hay compras registradas</p>
            <p className="text-sm">en el período seleccionado</p>
          </CardContent>
        </Card>
      )}

      {/* Modal para ver documentos */}
      <Dialog open={modalDocumento.open} onOpenChange={(open) => setModalDocumento({ ...modalDocumento, open })}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {modalDocumento.tipo === 'pdf' ? (
                <><FileText className="h-5 w-5 text-red-600" /> Factura PDF</>
              ) : (
                <><FileText className="h-5 w-5 text-green-600" /> XML (CFDI)</>
              )}
            </DialogTitle>
          </DialogHeader>
          
          {modalDocumento.tipo === 'xml' && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4 p-4 bg-zinc-50 rounded">
                <div>
                  <p className="text-xs text-zinc-500">UUID</p>
                  <p className="font-mono text-sm">8A5F2B3C-4D5E-6F7A-8B9C-0D1E2F3A4B5C</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Fecha Timbrado</p>
                  <p className="text-sm">15/Ene/2026 14:32:05</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">RFC Emisor</p>
                  <p className="font-mono text-sm flex items-center gap-2">
                    VPT850101ABC
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  </p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">RFC Receptor</p>
                  <p className="font-mono text-sm flex items-center gap-2">
                    EDA900101XYZ
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  </p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Subtotal</p>
                  <p className="text-sm">{formatCurrency(2801.72)}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">IVA</p>
                  <p className="text-sm">{formatCurrency(448.28)}</p>
                </div>
                <div className="col-span-2">
                  <p className="text-xs text-zinc-500">Total</p>
                  <p className="text-xl font-bold text-green-600">{formatCurrency(3250)}</p>
                </div>
              </div>
              
              <div className="flex items-center gap-2 p-3 bg-green-50 rounded border border-green-200">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                <span className="text-sm text-green-700">Validaciones OK: RFC Emisor, RFC Receptor, Importe</span>
              </div>
              
              <div className="flex gap-2">
                <Button variant="outline" className="flex-1">
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Ver XML completo
                </Button>
                <Button variant="outline" className="flex-1">
                  <Download className="h-4 w-4 mr-2" />
                  Descargar
                </Button>
              </div>
            </div>
          )}
          
          {modalDocumento.tipo === 'pdf' && (
            <div className="space-y-3">
              <div className="h-96 bg-zinc-100 rounded flex items-center justify-center">
                <p className="text-zinc-500">Visor PDF se mostrará aquí</p>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" className="flex-1">
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Abrir en nueva pestaña
                </Button>
                <Button variant="outline" className="flex-1">
                  <Download className="h-4 w-4 mr-2" />
                  Descargar
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ============ COMPONENTE PRINCIPAL CON TABS ============
// ============ TAB 4: AUDITORÍA OPERATIVA ============
function AuditoriaOperativaTab({ servers, unidadesNegocio, selectedUnidad, setSelectedUnidad, selectedServer, setSelectedServer, selectedSucursal: parentSucursal, setSelectedSucursal: setParentSucursal, sucursales: parentSucursales }) {
  const [loading, setLoading] = useState(false);
const [inventariosFisicos, setInventariosFisicos] = useState([]);
  const [pedidosVigentes, setPedidosVigentes] = useState([]);
  
  const [folioInvInicial, setFolioInvInicial] = useState('');
  const [folioInvFinal, setFolioInvFinal] = useState('');
  const [folioPedido, setFolioPedido] = useState([]);  // Cambiado a array para multi-selección
  const [fechaInicial, setFechaInicial] = useState('');
  const [fechaAuditoria, setFechaAuditoria] = useState(new Date().toISOString().split('T')[0]);
  const [usarCapturaManual, setUsarCapturaManual] = useState(false);
  const [inventarioManual, setInventarioManual] = useState([]);
  
  // Estados de carga para diagnóstico
  const [loadingPedidos, setLoadingPedidos] = useState(false);
  const [loadingInventarios, setLoadingInventarios] = useState(false);
  const [errorConexion, setErrorConexion] = useState(null);  // NUEVO: Estado para errores de conexión
  
  // Estados para selección múltiple de inventarios
  const [selectedInvIniciales, setSelectedInvIniciales] = useState([]);
  const [selectedInvFinales, setSelectedInvFinales] = useState([]);
  const [busquedaInvIni, setBusquedaInvIni] = useState('');
  const [busquedaInvFin, setBusquedaInvFin] = useState('');
  const [showDropdownInvIni, setShowDropdownInvIni] = useState(false);
  const [showDropdownInvFin, setShowDropdownInvFin] = useState(false);
  
  // Estados para captura manual de inventario final
  const [mostrarCapturaManual, setMostrarCapturaManual] = useState(false);
  const [inventarioManualCaptura, setInventarioManualCaptura] = useState([]);
  const [calculadoraAbierta, setCalculadoraAbierta] = useState(null); // código del producto
  const [calculadoraInsumos, setCalculadoraInsumos] = useState('');
  const [calculadoraPresentaciones, setCalculadoraPresentaciones] = useState('');
  
  // Estados para modal arrastrable de captura
  const [modalPosition, setModalPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  
  // Ref para auto-scroll en modal de captura
  const capturaScrollRef = useRef(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  
  // Función para limpiar inventario capturado
  const limpiarInventarioCaptura = () => {
    if (window.confirm('¿Está seguro de eliminar TODO el inventario manual capturado?')) {
      setInventarioManualCaptura([]);
      setInventarioManual([]);
      localStorage.removeItem('inventarioManualCaptura_backup');
    }
  };
  
  // Eliminar un producto individual del inventario capturado
  const eliminarProductoCaptura = (codigo) => {
    setInventarioManualCaptura(prev => prev.filter(item => item.codigo !== codigo));
  };
  
  // Guardar inventario en localStorage cuando cambia
  useEffect(() => {
    if (inventarioManualCaptura.length > 0 && inventarioManualCaptura.some(i => i.totalInsumos > 0)) {
      localStorage.setItem('inventarioManualCaptura_backup', JSON.stringify(inventarioManualCaptura));
    }
  }, [inventarioManualCaptura]);
  
  // Handlers para arrastrar modal
  const handleMouseDown = (e) => {
    if (e.target.closest('.modal-header-drag')) {
      setIsDragging(true);
      setDragOffset({
        x: e.clientX - modalPosition.x,
        y: e.clientY - modalPosition.y
      });
    }
  };
  
  const handleMouseMove = useCallback((e) => {
    if (isDragging) {
      setModalPosition({
        x: e.clientX - dragOffset.x,
        y: e.clientY - dragOffset.y
      });
    }
  }, [isDragging, dragOffset]);
  
  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);
  
  // Efecto para listeners de mouse
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    } else {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    }
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, handleMouseMove, handleMouseUp]);
  
  // Estados para días objetivo de inventario
  const [diasObjetivoDefault, setDiasObjetivoDefault] = useState(10);
  const [diasObjetivoPorSku, setDiasObjetivoPorSku] = useState({}); // {codigo: dias}
  
  // Obtener usuario del localStorage para verificar permisos
  const currentUser = getSessionUser() || {};
  
  // Verificar si el usuario puede editar días objetivo (admin o roles autorizados)
  const puedeEditarDiasObjetivo = isAdminRole(currentUser) || currentUser?.role === 'gerente' || currentUser?.permisos?.includes('editar_dias_inventario');
  
  // Calcular fecha mínima de inventarios iniciales para filtrar finales (util CANÓNICO)
  const fechaMinimaInvInicial = useMemo(
    () => fechaMinimaInventarios(selectedInvIniciales),
    [selectedInvIniciales]
  );

  // Filtrar inventarios finales: solo fecha >= fecha del inicial (util CANÓNICO)
  const inventariosFinalesFiltrados = useMemo(
    () => filtrarInventariosFinales(inventariosFisicos, fechaMinimaInvInicial),
    [inventariosFisicos, fechaMinimaInvInicial]
  );
  
  const [resultados, setResultados] = useState(null);
  const [resumen, setResumen] = useState(null);
  const [agruparPorProveedor, setAgruparPorProveedor] = useState(false);
  
  // Selector de unidad de análisis: 'presentaciones' o 'insumos'
  const [unidadAnalisis, setUnidadAnalisis] = useState('presentaciones');
  
  // Modal detalle de movimientos / consumos (hook + componente CANÓNICO compartido con Análisis)
  const {
    detalle: detalleProducto,
    abrirMovimientos,
    abrirConsumos,
    cerrar: cerrarDetalleProducto,
  } = useDetalleProducto();
  
  // Modal pantalla completa para detalle de auditoría
  const [showFullscreenAuditoria, setShowFullscreenAuditoria] = useState(false);

  // Export Excel/PDF del reporte de Auditoría (inventarios + movimientos + consumos + delta)
  // Costo unitario según unidad de análisis. Definido ANTES de `auditoriaExport`
  // para evitar TDZ (ReferenceError "Cannot access 'getCostoSegunUnidad' before
  // initialization"): el useMemo lo invoca al poblarse `resultados` tras la auditoría.
  const getCostoSegunUnidad = useCallback((row) => {
    if (unidadAnalisis === 'presentaciones') {
      // Costo de la presentación (del backend)
      return row.costo_presentacion || row.costo || 0;
    }
    // Costo del insumo directamente de la tabla insumos
    return row.costo_insumo || row.costo || 0;
  }, [unidadAnalisis]);

  const auditoriaExport = useMemo(() => {
    const rows = (resultados || []).map(r => ({
      producto: r.producto,
      proveedor: r.proveedor || '',
      folio_pedido: r.folio_pedido || '',
      inv_inicial: Number(r.inv_inicial) || 0,
      movimientos: Number(r.movimientos ?? r.entradas ?? 0) || 0,
      consumos: Math.abs(Number(r.consumos) || 0),
      existencia_teorica: Number(r.existencia_teorica) || 0,
      inv_fisico: Number(r.inv_fisico) || 0,
      diferencia: Number(r.diferencia) || 0,
      costo_unit: Number(getCostoSegunUnidad(r)) || 0,
      importe_diferencia: Math.round((Number(r.importe_diferencia) || 0) * 100) / 100,
      dias_inventario: r.dias_inventario,
    }));
    const columns = [
      { key: 'producto', label: 'Producto' },
      { key: 'proveedor', label: 'Proveedor' },
      { key: 'folio_pedido', label: 'Folio Pedido' },
      { key: 'inv_inicial', label: 'Inv. Inicial' },
      { key: 'movimientos', label: '+ Movimientos' },
      { key: 'consumos', label: '- Consumos' },
      { key: 'existencia_teorica', label: 'Teórico (Delta)' },
      { key: 'inv_fisico', label: 'Físico' },
      { key: 'diferencia', label: 'Diferencia' },
      { key: 'costo_unit', label: 'Costo Unit.' },
      { key: 'importe_diferencia', label: 'Importe' },
      { key: 'dias_inventario', label: 'Días Inv.' },
    ];
    const resumenRows = resumen ? [
      { concepto: 'Total Teórico', valor: Number(resumen.total_teorico || 0) },
      { concepto: 'Total Físico', valor: Number(resumen.total_fisico || 0) },
      { concepto: 'Importe A Favor', valor: Number(resumen.importe_favor || 0) },
      { concepto: 'Importe En Contra', valor: -Math.abs(Number(resumen.importe_contra || 0)) },
      { concepto: 'Diferencia Total', valor: Number(resumen.total_diferencia || 0) },
      { concepto: 'Requiere Acta', valor: resumen.requiere_acta ? 'SÍ' : 'NO' },
    ] : [];
    const unidadNombre = (unidadesNegocio || []).find(u => String(u.id) === String(selectedUnidad) || u.codigo === selectedUnidad)?.nombre || selectedUnidad || '';
    const meta = `Unidad: ${unidadNombre} · Fecha: ${fechaAuditoria}`;

    const sheets = [
      { name: 'Auditoria Detalle', columns, rows },
      { name: 'Resumen', columns: [{ key: 'concepto', label: 'Concepto' }, { key: 'valor', label: 'Valor' }], rows: resumenRows },
    ];

    // Hoja agrupada por proveedor (solo si el toggle "Agrupar por Proveedor" está activo)
    if (agruparPorProveedor) {
      const provColumns = [
        { key: 'proveedor', label: 'Proveedor' },
        { key: 'folio_pedido', label: 'Folio Pedido' },
        { key: 'producto', label: 'Producto' },
        { key: 'inv_inicial', label: 'Inv. Inicial' },
        { key: 'movimientos', label: '+ Movimientos' },
        { key: 'consumos', label: '- Consumos' },
        { key: 'existencia_teorica', label: 'Teórico (Delta)' },
        { key: 'inv_fisico', label: 'Físico' },
        { key: 'diferencia', label: 'Diferencia' },
        { key: 'costo_unit', label: 'Costo Unit.' },
        { key: 'importe_diferencia', label: 'Importe' },
      ];
      const sorted = [...rows].sort((a, b) =>
        (a.proveedor || '').localeCompare(b.proveedor || '') ||
        (a.folio_pedido || '').localeCompare(b.folio_pedido || ''));
      const groups = {};
      sorted.forEach(r => { const key = r.proveedor || '(Sin proveedor)'; (groups[key] = groups[key] || []).push(r); });
      const provRows = [];
      Object.entries(groups).forEach(([prov, gr]) => {
        gr.forEach(r => provRows.push({ ...r }));
        const subImporte = gr.reduce((s, r) => s + (Number(r.importe_diferencia) || 0), 0);
        provRows.push({ proveedor: `SUBTOTAL ${prov}`, folio_pedido: '', producto: '', importe_diferencia: Math.round(subImporte * 100) / 100 });
      });
      if (provRows.length) sheets.push({ name: 'Por Proveedor', columns: provColumns, rows: provRows });
    }

    return { columns, rows, meta, sheets };
  }, [resultados, resumen, unidadesNegocio, selectedUnidad, fechaAuditoria, agruparPorProveedor, getCostoSegunUnidad]);

  // Cargar filtros guardados al montar
  useEffect(() => {
    const savedFilters = localStorage.getItem(
      `auditoria_filters_${selectedServer}_${selectedUnidad || 'unidad'}`
    );
    if (savedFilters) {
      try {
        const filters = JSON.parse(savedFilters);
        if (filters.folioPedido) setFolioPedido(filters.folioPedido);
        if (filters.fechaInicial) setFechaInicial(filters.fechaInicial);
        if (filters.fechaAuditoria) setFechaAuditoria(filters.fechaAuditoria);
        if (filters.selectedInvIniciales) setSelectedInvIniciales(filters.selectedInvIniciales);
        if (filters.selectedInvFinales) setSelectedInvFinales(filters.selectedInvFinales);
        if (filters.usarCapturaManual !== undefined) setUsarCapturaManual(filters.usarCapturaManual);
      } catch (e) {
        logger.warn('Error loading saved filters:', e);
      }
    }
  }, [selectedServer, selectedUnidad]);

  // Guardar filtros cuando cambien
  useEffect(() => {
    if (selectedServer && selectedUnidad) {
      const filters = {
        folioPedido,
        fechaInicial,
        fechaAuditoria,
        selectedInvIniciales,
        selectedInvFinales,
        usarCapturaManual
      };

      localStorage.setItem(
        `auditoria_filters_${selectedServer}_${selectedUnidad}`,
        JSON.stringify(filters)
      );
    }
  }, [
    selectedServer,
    selectedUnidad,
    folioPedido,
    fechaInicial,
    fechaAuditoria,
    selectedInvIniciales,
    selectedInvFinales,
    usarCapturaManual
  ]);

  // Auditoría se gobierna por Unidad de Negocio.
  // Sucursal queda como contexto técnico opcional para contratos
  // backend que todavía conservan el parámetro por compatibilidad.
  useEffect(() => {
    if (selectedServer) {
      fetchInventariosFisicosLocal();
      fetchPedidosVigentesLocal();
    }
    // Auditoría opera por Unidad de Negocio.
    // El backend resuelve el contexto canónico de sucursal cuando aplique.
    // No se expone ni se exige selector de almacén/sucursal en esta pantalla.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedServer, selectedUnidad]);

  const fetchInventariosFisicosLocal = async () => {
    setLoadingInventarios(true);
    setErrorConexion(null);  // Reset error
    try {
      const params = {};
      if (parentSucursal) {
        params.sucursal = parentSucursal;
      }

      const response = await api.get(`/compras/inventarios-fisicos/${selectedUnidad}`, {
        params,
        timeout: 30000
      });
      logger.log(
        `[Auditoría] Inventarios cargados para unidad "${selectedUnidad}":`,
        response.data.length
      );
      setInventariosFisicos(response.data);
      if (response.data.length === 0) {
        // Verificar si es un error de conexión o simplemente no hay datos
        logger.log('[Auditoría] No se encontraron inventarios - verificar conexión al servidor');
      }
    } catch (error) {
      logger.error('Error cargando inventarios físicos:', error);
      setInventariosFisicos([]);
      // Detectar errores de conexión/timeout
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout') || error.response?.status >= 500) {
        setErrorConexion('Error de conexión al servicio canónico de inventarios.');
      }
    } finally {
      setLoadingInventarios(false);
    }
  };

  const fetchPedidosVigentesLocal = async () => {
    setLoadingPedidos(true);
    try {
      const params = {};
      if (parentSucursal) {
        params.sucursal = parentSucursal;
      }

      const response = await api.get(`/compras/pedidos-vigentes/${selectedUnidad}`, {
        params,
        timeout: 30000
      });
      logger.log(
        `[Auditoría] Documentos de compra cargados para unidad "${selectedUnidad}":`,
        response.data.length
      );
      setPedidosVigentes(response.data);
    } catch (error) {
      logger.error('Error cargando pedidos:', error);
      setPedidosVigentes([]);
      // Detectar errores de conexión/timeout
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout') || error.response?.status >= 500) {
        setErrorConexion('Error de conexión al servicio canónico de pedidos.');
      }
    } finally {
      setLoadingPedidos(false);
    }
  };

  // Función ÚNICA para convertir cantidades
  // TODOS los datos (inventarios, movimientos, consumos) vienen NORMALIZADOS en INSUMOS del backend
  const getConversionValues = (cantidad, rendimiento) => {
    if (!cantidad || cantidad === 0) return { principal: '0.00', alternativo: '0.00' };
    
    const cantidadNum = parseFloat(cantidad) || 0;
    const rendimientoNum = parseFloat(rendimiento) || 1;
    
    if (unidadAnalisis === 'presentaciones') {
      // Datos en insumos → convertir a presentaciones (÷ rendimiento)
      const enPresentaciones = rendimientoNum > 0 ? cantidadNum / rendimientoNum : cantidadNum;
      return {
        principal: formatNumber(enPresentaciones),
        alternativo: formatNumber(cantidadNum)
      };
    } else {
      // Datos en insumos → mostrar tal cual
      const enPresentaciones = rendimientoNum > 0 ? cantidadNum / rendimientoNum : cantidadNum;
      return {
        principal: formatNumber(cantidadNum),
        alternativo: formatNumber(enPresentaciones)
      };
    }
  };
  
  // Alias para compatibilidad
  const getConversionValuesInventario = getConversionValues;
  const getConversionValuesMovimientos = getConversionValues;
  const getConversionValuesConsumo = getConversionValues;
  
  // Función para inicializar captura manual desde los resultados de auditoría o inventarios iniciales
  const iniciarCapturaManual = async () => {
    // Si ya hay resultados de auditoría, usar esos
    if (resultados && resultados.length > 0) {
      const capturaInicial = resultados.map(r => ({
        codigo: r.codigo,
        producto: r.producto,
        rendimiento: r.rendimiento || 1,
        cantidadInsumos: 0,
        cantidadPresentaciones: 0,
        totalInsumos: 0
      }));
      setInventarioManualCaptura(capturaInicial);
      setMostrarCapturaManual(true);
      return;
    }
    
    // REGLA CRÍTICA: Solo mostrar productos de las REQUISICIONES SELECCIONADAS
    // Si hay requisiciones seleccionadas, ignorar inventarios iniciales
    if (folioPedido.length > 0) {
      try {
        
        // Obtener SOLO productos de las requisiciones seleccionadas
        // Fuente canónica EDARSAHUB; timeout extendido para evitar falsos abortos
        // cuando la consulta agrupa varios folios.
        const response = await api.post(`/compras/productos-para-captura`, {
          server_id: selectedUnidad,
          sucursal: null,
          folios_inv_inicial: [],  // Ignorar inventarios iniciales cuando hay requisiciones
          folios_requisiciones: folioPedido
        }, { timeout: 30000 });
        
        logger.log('Productos de requisiciones:', response.data);
        
        if (response.data.productos && response.data.productos.length > 0) {
          const capturaInicial = response.data.productos.map(p => ({
            codigo: p.codigo,
            producto: p.producto,
            rendimiento: p.rendimiento || 1,
            cantidadInsumos: 0,
            cantidadPresentaciones: 0,
            totalInsumos: 0
          }));
          setInventarioManualCaptura(capturaInicial);
          setMostrarCapturaManual(true);
        } else {
          alert('No se encontraron productos en las requisiciones seleccionadas');
        }
      } catch (error) {
        logger.error('Error obteniendo productos de requisiciones:', error);
        const esTimeout = error.code === 'ECONNABORTED' || error.message?.includes('timeout');
        alert(esTimeout
          ? 'La consulta de productos canónicos tardó demasiado. Intenta de nuevo en unos segundos.'
          : 'Error al obtener productos de las requisiciones.');
      }
      return;
    }
    
    // Si no hay requisiciones pero sí inventarios iniciales, usar esos
    if (selectedInvIniciales.length > 0) {
      try {
        const foliosIni = selectedInvIniciales.map(inv => String(inv.folio));
        
        const response = await api.post(`/compras/productos-para-captura`, {
          server_id: selectedUnidad,
          sucursal: null,
          folios_inv_inicial: foliosIni,
          folios_requisiciones: []
        }, { timeout: 30000 });
        
        if (response.data.productos && response.data.productos.length > 0) {
          const capturaInicial = response.data.productos.map(p => ({
            codigo: p.codigo,
            producto: p.producto,
            rendimiento: p.rendimiento || 1,
            cantidadInsumos: 0,
            cantidadPresentaciones: 0,
            totalInsumos: 0
          }));
          setInventarioManualCaptura(capturaInicial);
          setMostrarCapturaManual(true);
        } else {
          alert('No se encontraron productos en los inventarios iniciales seleccionados');
        }
      } catch (error) {
        logger.error('Error obteniendo productos:', error);
        const esTimeout = error.code === 'ECONNABORTED' || error.message?.includes('timeout');
        alert(esTimeout
          ? 'La consulta de productos canónicos tardó demasiado. Intenta de nuevo en unos segundos.'
          : 'Error al obtener productos de inventarios iniciales.');
      }
      return;
    }
    
    alert('Seleccione primero requisiciones o inventarios iniciales para obtener la lista de productos');
  };
  
  // Función para abrir calculadora de un producto específico
  const abrirCalculadora = (codigo) => {
    const item = inventarioManualCaptura.find(i => i.codigo === codigo);
    if (item) {
      setCalculadoraInsumos(item.cantidadInsumos?.toString() || '0');
      setCalculadoraPresentaciones(item.cantidadPresentaciones?.toString() || '0');
    } else {
      setCalculadoraInsumos('0');
      setCalculadoraPresentaciones('0');
    }
    setCalculadoraAbierta(codigo);
  };
  
  // Función para guardar el valor de la calculadora
  const guardarCalculadora = () => {
    if (!calculadoraAbierta) return;
    
    const insumos = parseFloat(calculadoraInsumos) || 0;
    const presentaciones = parseFloat(calculadoraPresentaciones) || 0;
    
    setInventarioManualCaptura(prev => prev.map(item => {
      if (item.codigo === calculadoraAbierta) {
        const rendimiento = item.rendimiento || 1;
        // Convertir presentaciones a insumos y sumar
        const totalInsumos = insumos + (presentaciones * rendimiento);
        return {
          ...item,
          cantidadInsumos: insumos,
          cantidadPresentaciones: presentaciones,
          totalInsumos: totalInsumos
        };
      }
      return item;
    }));
    
    setCalculadoraAbierta(null);
    setCalculadoraInsumos('');
    setCalculadoraPresentaciones('');
  };
  
  // Función para aplicar inventario manual a la auditoría
  const aplicarInventarioManual = async () => {
    // Crear el array de inventario manual para enviar al backend
    const inventarioParaBackend = inventarioManualCaptura
      .filter(item => item.totalInsumos > 0)
      .map(item => ({
        codigo: item.codigo,
        producto: item.producto,
        cantidad: item.totalInsumos, // Ya normalizado en insumos
        costo: 0
      }));
    
    setInventarioManual(inventarioParaBackend);
    
    // FASE PROVISIONAL: Guardar en EDARSAHUB para historial
    if (inventarioParaBackend.length > 0 && selectedUnidad) {
      try {
        const unidadInfo = unidadesNegocio.find(u => u.id === selectedUnidad);
        await api.post('/compras/inventarios-provisionales', {
          unidad_negocio_id: selectedUnidad,
          unidad_negocio_nombre: unidadInfo?.nombre || '',
          server_id: selectedServer,
          sucursal: parentSucursal,
          fecha_auditoria: fechaAuditoria,
          items: inventarioParaBackend.map(item => ({
            codigo_producto: item.codigo,
            nombre_producto: item.producto,
            cantidad: item.cantidad,
            costo_unitario: item.costo || 0
          }))
        });
        logger.log(`[Compras] Inventario provisional guardado: ${inventarioParaBackend.length} productos`);
      } catch (error) {
        logger.error('[Compras] Error guardando inventario provisional:', error);
        // No bloquear el flujo, el inventario local sigue disponible
      }
    }
    
    setMostrarCapturaManual(false);
    
    // Mostrar mensaje de confirmación
    alert(`Inventario manual capturado: ${inventarioParaBackend.length} productos. Ahora puede ejecutar la auditoría.`);
  };
  
  // Función para obtener el costo según unidad seleccionada
  // Usa directamente costo_insumo o costo_presentacion del backend
  // Función para formatear cantidad con conversión (formato legible)
  const formatConversion = (cantidad, rendimiento, unidadPrincipal) => {
    const values = getConversionValues(cantidad, rendimiento);
    return `${values.principal} (${values.alternativo})`;
  };

  // Doble clic: detalle CANÓNICO de movimientos (hook + componente compartido con Análisis)
  const fetchDetalleMovimientos = (codigo, producto) => {
    abrirMovimientos({
      serverId: selectedServer,
      sucursal: parentSucursal,
      codigo,
      producto,
      fechaInicio: fechaInicial || selectedInvIniciales[0]?.fecha?.split('T')[0] || fechaAuditoria,
      fechaFin: fechaAuditoria,
      almacenes: [],
    });
  };

  // Doble clic: detalle CANÓNICO de consumos (hook + componente compartido con Análisis)
  const fetchDetalleConsumos = (codigo, producto) => {
    abrirConsumos({
      serverId: selectedServer,
      sucursal: parentSucursal,
      codigo,
      producto,
      fechaInicio: fechaInicial || selectedInvIniciales[0]?.fecha?.split('T')[0] || fechaAuditoria,
      fechaFin: fechaAuditoria,
      almacenes: [],
    });
  };

  const handleInvInicialChange = (folio) => {
    setFolioInvInicial(folio);
    const inv = inventariosFisicos.find(i => String(i.folio) === String(folio));
    if (inv) {
      setFechaInicial(inv.fecha?.split('T')[0] || '');
    }
  };

  const realizarAuditoria = async () => {
    if (!selectedUnidad) {
      toast.error('Selecciona una unidad de negocio');
      return;
    }
    
    // Usar selectedInvIniciales si hay elementos, sino folioInvInicial
    const tieneInvInicial = selectedInvIniciales.length > 0 || folioInvInicial;
    

const fechaInvInicialEfectiva =
  selectedInvIniciales[0]?.fecha?.split('T')[0]
  || fechaInicial
  || null;

if (!tieneInvInicial || !fechaInvInicialEfectiva || !fechaAuditoria) {
      toast.error('Completa las fechas y el inventario inicial');
      return;
    }
    if (folioPedido.length === 0) {
      toast.error('Selecciona al menos una requisición para comparar');
      return;
    }
    if (!usarCapturaManual && !folioInvFinal && selectedInvFinales.length === 0) {
      toast.error('Selecciona un inventario final o activa captura manual');
      return;
    }

    setLoading(true);
    try {
      
      // Determinar los folios de inventario inicial a usar (TODOS los seleccionados)
      const foliosInvInicialToUse = selectedInvIniciales.length > 0 
        ? selectedInvIniciales.map(inv => String(inv.folio))
        : (folioInvInicial ? [String(folioInvInicial)] : []);
      
      // Determinar los folios de inventario final a usar (TODOS los seleccionados)
      const foliosInvFinalToUse = selectedInvFinales.length > 0 
        ? selectedInvFinales.map(inv => String(inv.folio))
        : (folioInvFinal ? [String(folioInvFinal)] : []);
      
      const response = await api.post(`/compras/auditoria-operativa`, {
        // Contrato canónico: enviar Unidad de Negocio.
        // Backend resuelve server_id internamente.
        server_id: selectedUnidad,
        sucursal: null,
        // Auditoría no expone selector de almacenes.
        // TODOS se restringe por el scope autorizado en backend.
        almacenes: ['TODOS'],
        folio_inv_inicial: foliosInvInicialToUse[0] || null,  // Legacy: primer folio
        folios_inv_inicial: foliosInvInicialToUse,  // Nuevo: todos los folios
        fecha_inv_inicial: fechaInvInicialEfectiva,
        fecha_auditoria: fechaAuditoria,
        folio_inv_final: usarCapturaManual ? null : (foliosInvFinalToUse[0] || null),  // Legacy
        folios_inv_final: usarCapturaManual ? null : foliosInvFinalToUse,  // Nuevo: todos los folios
        folio_requisicion: folioPedido[0] || '',  // Siempre string (el primero)
        folios_requisiciones: folioPedido,  // Array completo
        inventario_manual: usarCapturaManual ? inventarioManual : null,
        dias_objetivo_default: diasObjetivoDefault,
        dias_objetivo_por_sku: Object.keys(diasObjetivoPorSku).length > 0 ? diasObjetivoPorSku : null
      });
      
      // Backend authoritative: resultados y resumen provienen
  // exclusivamente del cálculo canónico del servidor.
  const resultadosBackend = Array.isArray(response.data?.resultados)
    ? response.data.resultados
    : [];
  const resumenBackend = response.data?.resumen || {};

  setResultados(resultadosBackend);
  setResumen(resumenBackend);

  if (resumenBackend?.requiere_acta) {
        toast.warning('Se detectaron diferencias en contra. Se requiere Acta de Auditoría.');
      } else {
        toast.success('Auditoría completada sin diferencias significativas');
      }
    } catch (error) {
      logger.error('Error en auditoría:', error);
      const errorDetail = error.response?.data?.detail;
      let errorMsg = 'Error al realizar auditoría';
      if (typeof errorDetail === 'string') {
        errorMsg = errorDetail;
      } else if (Array.isArray(errorDetail)) {
        errorMsg = errorDetail.map(e => e.msg || e.message || JSON.stringify(e)).join(', ');
      }
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Mensaje de error de conexión */}
      {errorConexion && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-center gap-2">
          <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-red-800">Problema de conexión</p>
            <p className="text-xs text-red-600">{errorConexion}</p>
          </div>
        </div>
      )}
      <Card className="border">
        <CardHeader className="py-3 bg-amber-50 border-b">
          <CardTitle className="text-base flex items-center gap-2">
            <FileWarning className="h-5 w-5 text-amber-600" />
            Auditoría Operativa de Inventarios
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 space-y-3">
          {/* Fila 1: Unidad de Negocio, Sucursal, Requisición - FASE 3.2 */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <div className="space-y-1">
              <Label className="text-xs">Unidad de Negocio</Label>
              {unidadesNegocio?.length === 1 ? (
                <div className="flex h-8 w-full items-center rounded-md border border-input bg-zinc-50 px-2 py-1 text-sm">
                  <Building2 className="h-3 w-3 mr-1 text-zinc-500" />
                  <span className="text-xs">{unidadesNegocio[0].nombre}</span>
                </div>
              ) : (
                <Select value={selectedUnidad} onValueChange={setSelectedUnidad}>
                  <SelectTrigger className="h-8" data-testid="auditoria-unidad-selector">
                    <SelectValue placeholder="Seleccionar unidad" />
                  </SelectTrigger>
                  <SelectContent>
                    {unidadesNegocio?.map(u => (
                      <SelectItem key={u.id} value={u.id}>
                        <span className="flex items-center gap-1">
                          <Building2 className="h-3 w-3" />
                          {u.nombre}
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>
            {/* BLINDAJE DEFINITIVO: Selector de Sucursal ELIMINADO - Backend resuelve contexto */}
            <div className="space-y-1">
              <Label className="text-xs">Requisición(es) / Orden(es) de Compra *</Label>
              <details className="relative">
                <summary className="flex h-8 w-full items-center justify-between rounded-md border border-input bg-background px-2 py-1 text-sm cursor-pointer">
                  <span className="truncate text-left text-xs">
                    {loadingPedidos 
                      ? "Cargando..." 
                      : folioPedido.length === 0 
                        ? getSelectPlaceholder(
                            pedidosVigentes,
                            "Cargando...",
                            "Sin requisiciones / órdenes",
                            "Seleccionar folio(s)"
                          )
                        : `${folioPedido.length} seleccionada(s)`}
                  </span>
                  {loadingPedidos ? (
                    <Loader2 className="h-3 w-3 animate-spin opacity-50" />
                  ) : (
                    <ChevronDown className="h-3 w-3 opacity-50" />
                  )}
                </summary>
                <div className="absolute z-50 w-full mt-1 bg-white border rounded-md shadow-lg max-h-64 overflow-hidden">
                  {folioPedido.length > 0 && (
                    <button
                      type="button"
                      className="w-full px-3 py-2 text-xs text-left hover:bg-zinc-100 border-b flex items-center text-red-600"
                      onClick={() => setFolioPedido([])}
                    >
                      <X className="h-3 w-3 mr-1" /> Limpiar ({folioPedido.length})
                    </button>
                  )}
                  <div className="max-h-52 overflow-y-auto">
                    {loadingPedidos ? (
                      <div className="flex items-center justify-center py-4 text-zinc-500">
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                        <span className="text-xs">Cargando requisiciones...</span>
                      </div>
                    ) : pedidosVigentes.length === 0 ? (
                      <div className="py-4 px-3 text-center text-zinc-500">
                        <p className="text-xs font-medium">
                          No hay requisiciones u órdenes de compra disponibles
                        </p>
                        <p className="text-xs mt-1">
                          Unidad: {
                            unidadesNegocio?.find(
                              u => String(u.id) === String(selectedUnidad)
                            )?.nombre || 'No seleccionada'
                          }
                        </p>
                      </div>
                    ) : (
                      pedidosVigentes.map(p => (
                        <label key={`${p.tipo}-${p.folio}`} className="flex items-center space-x-2 py-2 px-3 hover:bg-zinc-50 cursor-pointer">
                          <input
                            type="checkbox"
                            className="rounded border-zinc-300"
                            checked={folioPedido.includes(p.folio)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setFolioPedido([...folioPedido, p.folio]);
                              } else {
                                setFolioPedido(folioPedido.filter(f => f !== p.folio));
                              }
                            }}
                          />
                          <span className="text-sm">{p.folio} - {p.comprador || 'Sin proveedor'}</span>
                        </label>
                      ))
                    )}
                  </div>
                </div>
              </details>
              {/* Badges de requisiciones seleccionadas */}
              {folioPedido.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {folioPedido.map(folio => (
                    <span 
                      key={folio}
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-amber-100 text-amber-800 border border-amber-200"
                    >
                      {folio}
                      <button 
                        type="button"
                        onClick={() => setFolioPedido(folioPedido.filter(f => f !== folio))}
                        className="hover:text-amber-600"
                      >
                        <X className="h-2.5 w-2.5" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Fecha Inicial</Label>
              <Input type="date" value={fechaInicial} onChange={e => setFechaInicial(e.target.value)} className="h-8 text-xs" />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Fecha Auditoría</Label>
              <Input type="date" value={fechaAuditoria} onChange={e => setFechaAuditoria(e.target.value)} className="h-8 text-xs" />
            </div>
          </div>

          {/* Fila 2: Inventarios Inicial y Final */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label className="text-xs">Inventario(s) Inicial(es)</Label>
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setShowDropdownInvIni(!showDropdownInvIni)}
                  className="flex h-8 w-full items-center justify-between rounded-md border border-input bg-background px-2 py-1 text-sm cursor-pointer hover:border-zinc-400"
                >
                  <span className="truncate text-left text-xs">
                    {loadingInventarios 
                      ? "Cargando..." 
                      : selectedInvIniciales.length === 0 
                        ? getSelectPlaceholder(inventariosFisicos, "Cargando...", "Sin inventarios", "Seleccionar inventario(s)")
                        : `${selectedInvIniciales.length} seleccionado(s)`}
                  </span>
                  {loadingInventarios ? (
                    <Loader2 className="h-3 w-3 animate-spin opacity-50" />
                  ) : (
                    <ChevronDown className={`h-3 w-3 opacity-50 transition-transform ${showDropdownInvIni ? 'rotate-180' : ''}`} />
                  )}
                </button>
                {showDropdownInvIni && (
                  <>
                    <div className="fixed inset-0 z-40" onClick={() => setShowDropdownInvIni(false)} />
                    <div className="absolute z-50 w-[350px] mt-1 bg-white border rounded-md shadow-xl">
                      <div className="p-2 border-b bg-zinc-50">
                        <Input
                          placeholder="Buscar por folio o almacén..."
                          value={busquedaInvIni}
                          onChange={(e) => setBusquedaInvIni(e.target.value)}
                          className="h-7 text-xs"
                        />
                      </div>
                      <div className="flex items-center justify-between px-2 py-1 border-b bg-zinc-50">
                        {selectedInvIniciales.length > 0 && (
                          <button
                            type="button"
                            className="text-xs text-red-600 hover:text-red-700 flex items-center"
                            onClick={() => {
                              setSelectedInvIniciales([]);
                              setFolioInvInicial('');
                              setFechaInicial('');
                            }}
                          >
                            <X className="h-3 w-3 mr-1" /> Limpiar ({selectedInvIniciales.length})
                          </button>
                        )}
                        <span className="text-xs text-zinc-400 ml-auto">
                          {inventariosFisicos.filter(inv => 
                            !busquedaInvIni || 
                            String(inv.folio).includes(busquedaInvIni) ||
                            (inv.almacen || '').toLowerCase().includes(busquedaInvIni.toLowerCase())
                          ).length} inv.
                        </span>
                      </div>
                      <div className="max-h-60 overflow-y-auto">
                        {loadingInventarios ? (
                          <div className="flex items-center justify-center py-4 text-zinc-500">
                            <Loader2 className="h-4 w-4 animate-spin mr-2" />
                            <span className="text-xs">Cargando inventarios...</span>
                          </div>
                        ) : inventariosFisicos.length === 0 ? (
                          <div className="py-4 px-3 text-center text-zinc-500">
                            <p className="text-xs font-medium">No hay inventarios físicos</p>
                            <p className="text-xs mt-1">
                              Unidad: {
                                unidadesNegocio?.find(
                                  u => String(u.id) === String(selectedUnidad)
                                )?.nombre || 'No seleccionada'
                              }
                            </p>
                          </div>
                        ) : (
                          inventariosFisicos
                            .filter(inv => 
                              !busquedaInvIni || 
                              String(inv.folio).includes(busquedaInvIni) ||
                              (inv.almacen || '').toLowerCase().includes(busquedaInvIni.toLowerCase())
                            )
                            .map(inv => (
                              <label 
                                key={inv.folio} 
                                className={`flex items-center space-x-2 py-2 px-3 hover:bg-blue-50 cursor-pointer border-b border-zinc-100 ${
                                  selectedInvIniciales.some(i => i.folio === inv.folio) ? 'bg-blue-50' : ''
                                }`}
                              >
                                <input
                                  type="checkbox"
                                  className="rounded border-zinc-300 h-3 w-3"
                                  checked={selectedInvIniciales.some(i => i.folio === inv.folio)}
                                  onChange={(e) => {
                                    if (e.target.checked) {
                                      const newSelected = [...selectedInvIniciales, inv];
                                      setSelectedInvIniciales(newSelected);
                                      if (newSelected.length === 1) {
                                        setFolioInvInicial(String(inv.folio));
                                        if (inv.fecha) {
                                          setFechaInicial(inv.fecha.split('T')[0]);
                                        }
                                      }
                                    } else {
                                    const newSelected = selectedInvIniciales.filter(i => i.folio !== inv.folio);
                                    setSelectedInvIniciales(newSelected);
                                    if (newSelected.length === 0) {
                                      setFolioInvInicial('');
                                      setFechaInicial('');
                                    }
                                  }
                                }}
                              />
                              <div className="flex-1 min-w-0">
                                <div className="font-medium text-xs">{inv.folio} - {inv.fecha?.split('T')[0]}</div>
                                <div className="text-xs text-zinc-500 truncate">{inv.almacen}</div>
                              </div>
                            </label>
                          ))
                        )}
                      </div>
                    </div>
                  </>
                )}
              </div>
              {selectedInvIniciales.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {selectedInvIniciales.slice(0, 3).map(inv => (
                    <span key={inv.folio} className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs bg-blue-100 text-blue-800">
                      {inv.folio}
                      <button type="button" onClick={() => {
                        const newSelected = selectedInvIniciales.filter(i => i.folio !== inv.folio);
                        setSelectedInvIniciales(newSelected);
                      }}>
                        <X className="h-2.5 w-2.5" />
                      </button>
                    </span>
                  ))}
                  {selectedInvIniciales.length > 3 && (
                    <span className="text-xs text-zinc-500">+{selectedInvIniciales.length - 3} más</span>
                  )}
                </div>
              )}
            </div>
            
            <div className="space-y-1">
              <Label className="text-xs">Inventario(s) Final(es)</Label>
              {!usarCapturaManual ? (
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setShowDropdownInvFin(!showDropdownInvFin)}
                    className="flex h-8 w-full items-center justify-between rounded-md border border-input bg-background px-2 py-1 text-sm cursor-pointer hover:border-zinc-400"
                  >
                    <span className="truncate text-left text-xs">
                      {loadingInventarios 
                        ? "Cargando..." 
                        : selectedInvFinales.length === 0 
                          ? getSelectPlaceholder(inventariosFinalesFiltrados, "Cargando...", "Sin inventarios", "Seleccionar inventario(s)")
                          : `${selectedInvFinales.length} seleccionado(s)`}
                    </span>
                    {loadingInventarios ? (
                      <Loader2 className="h-3 w-3 animate-spin opacity-50" />
                    ) : (
                      <ChevronDown className={`h-3 w-3 opacity-50 transition-transform ${showDropdownInvFin ? 'rotate-180' : ''}`} />
                    )}
                  </button>
                  {showDropdownInvFin && (
                    <>
                      <div className="fixed inset-0 z-40" onClick={() => setShowDropdownInvFin(false)} />
                      <div className="absolute z-50 w-[350px] right-0 mt-1 bg-white border rounded-md shadow-xl">
                        <div className="p-2 border-b bg-zinc-50">
                          <Input
                            placeholder="Buscar por folio o almacén..."
                            value={busquedaInvFin}
                            onChange={(e) => setBusquedaInvFin(e.target.value)}
                            className="h-7 text-xs"
                          />
                        </div>
                        <div className="flex items-center justify-between px-2 py-1 border-b bg-zinc-50">
                          {selectedInvFinales.length > 0 && (
                            <button
                              type="button"
                              className="text-xs text-red-600 hover:text-red-700 flex items-center"
                              onClick={() => {
                                setSelectedInvFinales([]);
                                setFolioInvFinal('');
                              }}
                            >
                              <X className="h-3 w-3 mr-1" /> Limpiar ({selectedInvFinales.length})
                            </button>
                          )}
                          <span className="text-xs text-zinc-400 ml-auto">
                            {inventariosFinalesFiltrados.filter(inv => 
                              !busquedaInvFin || 
                              String(inv.folio).includes(busquedaInvFin) ||
                              (inv.almacen || '').toLowerCase().includes(busquedaInvFin.toLowerCase())
                            ).length} inv.
                            {fechaMinimaInvInicial && <span className="ml-1">(≥{fechaMinimaInvInicial})</span>}
                          </span>
                        </div>
                        <div className="max-h-60 overflow-y-auto">
                          {loadingInventarios ? (
                            <div className="flex items-center justify-center py-4 text-zinc-500">
                              <Loader2 className="h-4 w-4 animate-spin mr-2" />
                              <span className="text-xs">Cargando inventarios...</span>
                            </div>
                          ) : inventariosFinalesFiltrados.length === 0 ? (
                            <div className="py-4 px-3 text-center text-zinc-500">
                              <p className="text-xs font-medium">No hay inventarios finales</p>
                              <p className="text-xs mt-1">
                              Unidad: {
                                unidadesNegocio?.find(
                                  u => String(u.id) === String(selectedUnidad)
                                )?.nombre || 'No seleccionada'
                              }
                            </p>
                            </div>
                          ) : (
                            inventariosFinalesFiltrados
                              .filter(inv => 
                                !busquedaInvFin || 
                                String(inv.folio).includes(busquedaInvFin) ||
                                (inv.almacen || '').toLowerCase().includes(busquedaInvFin.toLowerCase())
                              )
                              .map(inv => (
                                <label 
                                  key={inv.folio} 
                                  className={`flex items-center space-x-2 py-2 px-3 hover:bg-green-50 cursor-pointer border-b border-zinc-100 ${
                                    selectedInvFinales.some(i => i.folio === inv.folio) ? 'bg-green-50' : ''
                                  }`}
                                >
                                  <input
                                  type="checkbox"
                                  className="rounded border-zinc-300 h-3 w-3"
                                  checked={selectedInvFinales.some(i => i.folio === inv.folio)}
                                  onChange={(e) => {
                                    if (e.target.checked) {
                                      const newSelected = [...selectedInvFinales, inv];
                                      setSelectedInvFinales(newSelected);
                                      if (newSelected.length === 1) {
                                        setFolioInvFinal(String(inv.folio));
                                      }
                                    } else {
                                      const newSelected = selectedInvFinales.filter(i => i.folio !== inv.folio);
                                      setSelectedInvFinales(newSelected);
                                      if (newSelected.length === 0) {
                                        setFolioInvFinal('');
                                      }
                                    }
                                  }}
                                />
                                <div className="flex-1 min-w-0">
                                  <div className="font-medium text-xs">{inv.folio} - {inv.fecha?.split('T')[0]}</div>
                                  <div className="text-xs text-zinc-500 truncate">{inv.almacen}</div>
                                </div>
                              </label>
                            ))
                          )}
                        </div>
                      </div>
                    </>
                  )}
                </div>
              ) : (
                <div className="text-xs text-amber-600 font-medium p-1.5 bg-amber-50 rounded h-8 flex items-center">
                  Captura Manual Activa
                </div>
              )}
              {!usarCapturaManual && selectedInvFinales.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {selectedInvFinales.slice(0, 3).map(inv => (
                    <span key={inv.folio} className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs bg-green-100 text-green-800">
                      {inv.folio}
                      <button type="button" onClick={() => {
                        const newSelected = selectedInvFinales.filter(i => i.folio !== inv.folio);
                        setSelectedInvFinales(newSelected);
                      }}>
                        <X className="h-2.5 w-2.5" />
                      </button>
                    </span>
                  ))}
                  {selectedInvFinales.length > 3 && (
                    <span className="text-xs text-zinc-500">+{selectedInvFinales.length - 3} más</span>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Fila 3: Captura manual y botón ejecutar */}
          <div className="flex flex-wrap items-center gap-3 pt-1 border-t">
            <div className="flex items-center gap-2">
              <Checkbox 
                id="captura-manual" 
                checked={usarCapturaManual} 
                onCheckedChange={setUsarCapturaManual} 
              />
              <Label htmlFor="captura-manual" className="text-xs">
                Sin inventario final
              </Label>
            </div>
            
            {usarCapturaManual && (selectedInvIniciales.length > 0 || folioPedido.length > 0 || (resultados && resultados.length > 0)) && (
              <Button 
                variant="outline" 
                size="sm" 
                onClick={iniciarCapturaManual}
                className="h-7 text-xs"
              >
                <Calculator className="h-3 w-3 mr-1" />
                Capturar Inv. Físico
              </Button>
            )}
            
            {usarCapturaManual && inventarioManual.length > 0 && (
              <span className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded flex items-center gap-1">
                <Check className="h-3 w-3" />
                {inventarioManual.length} productos capturados
              </span>
            )}
            
            <div className="ml-auto">
              <Button
                onClick={realizarAuditoria}
                disabled={loading || !selectedUnidad}
                size="sm"
                className="h-8"
              >
                {loading ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <FileWarning className="h-4 w-4 mr-1" />}
                Realizar Auditoría
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Resumen de Auditoría */}
      {resumen && (
        <Card className={`border-2 ${resumen.requiere_acta ? 'border-red-300 bg-red-50' : 'border-green-300 bg-green-50'}`}>
          <CardHeader className="py-3">
            <CardTitle className="text-base flex items-center gap-2">
              {resumen.requiere_acta ? (
                <><XCircle className="h-5 w-5 text-red-600" /> Requiere Acta de Auditoría</>
              ) : (
                <><CheckCircle2 className="h-5 w-5 text-green-600" /> Auditoría Sin Observaciones</>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-white rounded border">
                <p className="text-xs text-zinc-500">Existencia Teórica</p>
                <p className="text-lg font-bold text-blue-600">{formatCurrency(resumen.total_teorico)}</p>
              </div>
              <div className="text-center p-3 bg-white rounded border">
                <p className="text-xs text-zinc-500">Existencia Física</p>
                <p className="text-lg font-bold text-purple-600">{formatCurrency(resumen.total_fisico)}</p>
              </div>
              <div className="text-center p-3 bg-white rounded border">
                <p className="text-xs text-zinc-500">A Favor ({resumen.productos_favor})</p>
                <p className="text-lg font-bold text-green-600">+{formatCurrency(resumen.importe_favor)}</p>
              </div>
              <div className="text-center p-3 bg-white rounded border">
                <p className="text-xs text-zinc-500">En Contra ({resumen.productos_contra})</p>
                <p className="text-lg font-bold text-red-600">-{formatCurrency(resumen.importe_contra)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabla de resultados */}
      {resultados && resultados.length > 0 && (
        <Card className="border">
          <CardHeader className="py-2 flex flex-row items-center justify-between gap-4">
            <CardTitle className="text-sm">Detalle de Auditoría ({resultados.length} productos)</CardTitle>
            <div className="flex items-center gap-4">
              {/* Selector de unidad de análisis */}
              <div className="flex items-center gap-2 bg-zinc-100 rounded-lg p-1">
                <button
                  className={`px-3 py-1 text-xs rounded ${unidadAnalisis === 'presentaciones' ? 'bg-white shadow font-medium' : 'text-zinc-600'}`}
                  onClick={() => setUnidadAnalisis('presentaciones')}
                >
                  Presentaciones
                </button>
                <button
                  className={`px-3 py-1 text-xs rounded ${unidadAnalisis === 'insumos' ? 'bg-white shadow font-medium' : 'text-zinc-600'}`}
                  onClick={() => setUnidadAnalisis('insumos')}
                >
                  Insumos
                </button>
              </div>
              <label className="flex items-center gap-2 text-xs cursor-pointer">
                <input
                  type="checkbox"
                  className="rounded border-zinc-300"
                  checked={agruparPorProveedor}
                  onChange={(e) => setAgruparPorProveedor(e.target.checked)}
                />
                <span>Agrupar por Proveedor</span>
              </label>
              <ExportButtons
                filename="auditoria_operativa"
                title="Reporte de Auditoría Operativa"
                columns={auditoriaExport.columns}
                rows={auditoriaExport.rows}
                meta={auditoriaExport.meta}
                sheets={auditoriaExport.sheets}
                testid="auditoria-export"
              />
              {/* Botón pantalla completa */}
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowFullscreenAuditoria(true)}
                className="h-7 px-2"
                title="Ver en pantalla completa"
              >
                <Maximize2 className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="max-h-[400px] overflow-auto overflow-x-auto">
              <table className="w-full min-w-max text-xs">
                <thead className="sticky top-0 bg-zinc-800 text-white">
                  <tr>
                    {agruparPorProveedor && <th className="py-2 px-2 text-left">Proveedor</th>}
                    {agruparPorProveedor && <th className="py-2 px-2 text-left">Folio Pedido</th>}
                    <th className="py-2 px-2 text-left">Producto</th>
                    <th className="py-2 px-2 text-right">{unidadAnalisis === 'presentaciones' ? 'Inv.Ini (Pres)' : 'Inv.Ini (Ins)'}</th>
                    <th className="py-2 px-2 text-right text-zinc-400">{unidadAnalisis === 'presentaciones' ? '(Ins)' : '(Pres)'}</th>
                    <th className="py-2 px-2 text-right">{unidadAnalisis === 'presentaciones' ? '+Mov (Pres)' : '+Mov (Ins)'}</th>
                    <th className="py-2 px-2 text-right text-zinc-400">{unidadAnalisis === 'presentaciones' ? '(Ins)' : '(Pres)'}</th>
                    <th className="py-2 px-2 text-right">{unidadAnalisis === 'presentaciones' ? '-Cons (Pres)' : '-Cons (Ins)'}</th>
                    <th className="py-2 px-2 text-right text-zinc-400">{unidadAnalisis === 'presentaciones' ? '(Ins)' : '(Pres)'}</th>
                    <th className="py-2 px-2 text-right">{unidadAnalisis === 'presentaciones' ? 'Teórico (Pres)' : 'Teórico (Ins)'}</th>
                    <th className="py-2 px-2 text-right text-zinc-400">{unidadAnalisis === 'presentaciones' ? '(Ins)' : '(Pres)'}</th>
                    <th className="py-2 px-2 text-right">Físico</th>
                    <th className="py-2 px-2 text-right">Diferencia</th>
                    <th className="py-2 px-2 text-right">Costo Unit</th>
                    <th className="py-2 px-2 text-right">Importe</th>
                    <th className="py-2 px-2 text-center">Días Inv</th>
                    <th className="py-2 px-2 text-center" title="Días objetivo de inventario">
                      Días Obj
                      {puedeEditarDiasObjetivo && (
                        <Input 
                          type="number"
                          value={diasObjetivoDefault}
                          onChange={(e) => setDiasObjetivoDefault(parseInt(e.target.value) || 10)}
                          onFocus={(e) => e.target.select()}
                          className="h-5 w-12 text-xs text-center mt-1 bg-zinc-700 border-zinc-600"
                          title="Días objetivo por defecto"
                        />
                      )}
                    </th>
                    <th className="py-2 px-2 text-right">Pedido</th>
                    <th className="py-2 px-2 text-center">Ajuste</th>
                    <th className="py-2 px-2 text-center">Recomendar</th>
                  </tr>
                </thead>
                <tbody>
                  {(() => {
                    let lastProveedor = '';
                    let lastFolio = '';
                    return resultados.map((r, idx) => {
                      const rendimiento = r.rendimiento || 1;
                      const isNewProveedor = agruparPorProveedor && r.proveedor !== lastProveedor;
                      const isNewFolio = agruparPorProveedor && r.folio_pedido !== lastFolio;
                      
                      // Obtener valores convertidos para cada columna
                      const invIniValues = getConversionValuesInventario(r.inv_inicial, rendimiento);
                      const movValues = getConversionValuesMovimientos(r.movimientos || r.entradas || 0, rendimiento);
                      const consValues = getConversionValuesConsumo(Math.abs(r.consumos || 0), rendimiento);
                      const teoricoValues = getConversionValuesInventario(r.existencia_teorica, rendimiento);
                      const fisicoValues = getConversionValuesInventario(r.inv_fisico, rendimiento);
                      const difValues = getConversionValuesInventario(r.diferencia, rendimiento);
                      const costoUnit = getCostoSegunUnidad(r);
                      
                      if (agruparPorProveedor) {
                        lastProveedor = r.proveedor;
                        lastFolio = r.folio_pedido;
                      }
                      
                      return (
                        <tr key={`${r.codigo}-${r.folio_pedido || idx}`} className={`border-b ${r.tipo_diferencia === 'contra' ? 'bg-red-50' : ''} ${isNewProveedor ? 'border-t-2 border-t-zinc-400' : ''}`}>
                          {agruparPorProveedor && (
                            <td className={`py-1.5 px-2 ${isNewProveedor ? 'font-bold text-zinc-800' : 'text-zinc-400'}`}>
                              {isNewProveedor ? r.proveedor : ''}
                            </td>
                          )}
                          {agruparPorProveedor && (
                            <td className={`py-1.5 px-2 ${isNewFolio ? 'font-medium text-blue-600' : 'text-zinc-400'}`}>
                              {isNewFolio ? r.folio_pedido : ''}
                            </td>
                          )}
                          <td className="py-1.5 px-2 font-medium">{r.producto}</td>
                          {/* Inv Inicial - Principal */}
                          <td className="py-1.5 px-2 text-right">{invIniValues.principal}</td>
                          {/* Inv Inicial - Alternativo */}
                          <td className="py-1.5 px-2 text-right text-zinc-400">{invIniValues.alternativo}</td>
                          {/* Movimientos - Principal */}
                          <td 
                            className="py-1.5 px-2 text-right text-green-600 cursor-pointer hover:bg-green-100 transition-colors"
                            onDoubleClick={() => fetchDetalleMovimientos(r.codigo, r.producto)}
                            title="Doble click para ver detalle de movimientos"
                          >
                            +{movValues.principal}
                          </td>
                          {/* Movimientos - Alternativo */}
                          <td className="py-1.5 px-2 text-right text-green-400">{movValues.alternativo}</td>
                          {/* Consumos - Principal */}
                          <td 
                            className="py-1.5 px-2 text-right text-orange-600 cursor-pointer hover:bg-orange-100 transition-colors"
                            onDoubleClick={() => fetchDetalleConsumos(r.codigo, r.producto)}
                            title="Doble click para ver detalle de consumos"
                          >
                            -{consValues.principal}
                          </td>
                          {/* Consumos - Alternativo */}
                          <td className="py-1.5 px-2 text-right text-orange-400">{consValues.alternativo}</td>
                          {/* Teórico - Principal */}
                          <td className="py-1.5 px-2 text-right font-medium">{teoricoValues.principal}</td>
                          {/* Teórico - Alternativo */}
                          <td className="py-1.5 px-2 text-right text-zinc-400">{teoricoValues.alternativo}</td>
                          {/* Físico */}
                          <td className="py-1.5 px-2 text-right font-medium">{fisicoValues.principal}</td>
                          {/* Diferencia */}
                          <td className={`py-1.5 px-2 text-right font-bold ${r.diferencia >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {r.diferencia >= 0 ? '+' : ''}{difValues.principal}
                          </td>
                          {/* Costo Unitario */}
                          <td className="py-1.5 px-2 text-right text-zinc-500">
                            {formatCurrency(costoUnit)}
                          </td>
                          {/* Importe Diferencia */}
                          <td className={`py-1.5 px-2 text-right ${r.importe_diferencia >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {formatCurrency(r.importe_diferencia)}
                          </td>
                          {/* Días de Inventario */}
                          {(() => {
                            const diasObj = diasObjetivoPorSku[r.codigo] !== undefined 
                              ? diasObjetivoPorSku[r.codigo] 
                              : (r.dias_objetivo || diasObjetivoDefault);
                            const diasInv = r.dias_inventario === 'N/A' ? 999 : parseFloat(r.dias_inventario);
                            
                            return (
                              <td className="py-1.5 px-2 text-center">
                                <span className={`px-1.5 py-0.5 rounded text-xs ${
                                  r.dias_inventario === 'N/A' ? 'bg-zinc-100' :
                                  diasInv < diasObj * 0.5 ? 'bg-red-100 text-red-700' :
                                  diasInv < diasObj ? 'bg-yellow-100 text-yellow-700' :
                                  'bg-green-100 text-green-700'
                                }`}>
                                  {r.dias_inventario}
                                </span>
                              </td>
                            );
                          })()}
                          {/* Días Objetivo */}
                          <td className="py-1 px-1 text-center">
                            {puedeEditarDiasObjetivo ? (
                              <Input 
                                type="number"
                                value={diasObjetivoPorSku[r.codigo] !== undefined ? diasObjetivoPorSku[r.codigo] : (r.dias_objetivo || diasObjetivoDefault)}
                                onChange={(e) => {
                                  const valor = parseInt(e.target.value) || diasObjetivoDefault;
                                  setDiasObjetivoPorSku(prev => ({...prev, [r.codigo]: valor}));
                                }}
                                onFocus={(e) => e.target.select()}
                                className="h-6 w-14 text-xs text-center"
                              />
                            ) : (
                              <span className="text-xs text-zinc-500">
                                {r.dias_objetivo || diasObjetivoDefault}
                              </span>
                            )}
                          </td>
                          <td className="py-1.5 px-2 text-right">{formatNumber(r.cantidad_pedido)}</td>
                          {/* Ajuste y Recomendación - Calculados dinámicamente */}
                          {(() => {
                            const diasObj = diasObjetivoPorSku[r.codigo] !== undefined 
                              ? diasObjetivoPorSku[r.codigo] 
                              : (r.dias_objetivo || diasObjetivoDefault);
                            const diasInv = r.dias_inventario === 'N/A' ? 999 : parseFloat(r.dias_inventario);
                            const consumoDiario = r.consumo_diario || 0;
                            const invFisico = r.inv_fisico || 0;
                            const cantidadPedido = r.cantidad_pedido || 0;
                            const rendimiento = r.rendimiento || 1;
                            
                            // Calcular necesidad en insumos para alcanzar días objetivo
                            const necesidadInsumos = consumoDiario * diasObj;
                            // Lo que falta para llegar a la necesidad
                            const faltanteInsumos = necesidadInsumos - invFisico;
                            // Ajuste = faltante - lo ya pedido (convertido a insumos si es presentación)
                            const pedidoEnInsumos = cantidadPedido * rendimiento;
                            const ajusteInsumos = faltanteInsumos - pedidoEnInsumos;
                            
                            // Convertir ajuste a la unidad de análisis
                            const ajusteMostrar = unidadAnalisis === 'presentaciones' 
                              ? (rendimiento > 0 ? ajusteInsumos / rendimiento : ajusteInsumos)
                              : ajusteInsumos;
                            
                            const debeComprar = diasInv < diasObj;
                            let recomendacion = 'OK';
                            let ajusteTexto = 'OK';
                            let ajusteColor = 'text-green-600';
                            
                            if (Math.abs(ajusteMostrar) < 0.01) {
                              ajusteTexto = 'OK';
                              ajusteColor = 'text-green-600';
                              recomendacion = 'OK';
                            } else if (ajusteMostrar > 0) {
                              // Falta pedir más
                              ajusteTexto = `+${formatNumber(ajusteMostrar)}`;
                              ajusteColor = 'text-red-600 font-bold';
                              recomendacion = cantidadPedido > 0 ? 'AUMENTAR' : 'COMPRAR';
                            } else {
                              // Sobra, puede reducir
                              ajusteTexto = formatNumber(ajusteMostrar);
                              ajusteColor = 'text-blue-600';
                              recomendacion = 'REDUCIR';
                            }
                            
                            // Si no hay consumo, no se puede calcular
                            if (consumoDiario === 0 || r.dias_inventario === 'N/A') {
                              ajusteTexto = '-';
                              ajusteColor = 'text-zinc-400';
                              recomendacion = cantidadPedido > 0 ? 'REVISAR' : 'SIN DATOS';
                            }
                            
                            return (
                              <>
                                <td className={`py-1.5 px-2 text-center ${ajusteColor}`}>
                                  {ajusteTexto}
                                </td>
                                <td className="py-1.5 px-2 text-center">
                                  <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                                    recomendacion === 'COMPRAR' || recomendacion === 'AUMENTAR' ? 'bg-red-100 text-red-700' :
                                    recomendacion === 'OK' ? 'bg-green-100 text-green-700' :
                                    recomendacion === 'REDUCIR' ? 'bg-blue-100 text-blue-700' :
                                    'bg-zinc-100 text-zinc-600'
                                  }`}>
                                    {recomendacion}
                                  </span>
                                </td>
                              </>
                            );
                          })()}
                        </tr>
                      );
                    });
                  })()}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Modal Detalle de Movimientos/Consumos (componente CANÓNICO compartido con Análisis) */}
      <DetalleProductoModal
        detalle={detalleProducto}
        onClose={cerrarDetalleProducto}
        formatNumber={formatNumber}
      />
      
      {/* Modal Pantalla Completa - Detalle de Auditoría */}
      <Dialog open={showFullscreenAuditoria} onOpenChange={setShowFullscreenAuditoria}>
        <DialogContent className="max-w-[95vw] w-[95vw] max-h-[95vh] h-[95vh] p-0 overflow-hidden">
          <DialogHeader className="px-4 py-3 border-b bg-zinc-100 flex flex-row items-center justify-between">
            <DialogTitle className="text-lg font-semibold">
              Detalle de Auditoría ({resultados?.length || 0} productos)
            </DialogTitle>
            <div className="flex items-center gap-4">
              {/* Selector de unidad de análisis */}
              <div className="flex items-center gap-2 bg-white rounded-lg p-1 shadow-sm">
                <button
                  className={`px-3 py-1 text-xs rounded ${unidadAnalisis === 'presentaciones' ? 'bg-blue-100 text-blue-700 font-medium' : 'text-zinc-600 hover:bg-zinc-100'}`}
                  onClick={() => setUnidadAnalisis('presentaciones')}
                >
                  Presentaciones
                </button>
                <button
                  className={`px-3 py-1 text-xs rounded ${unidadAnalisis === 'insumos' ? 'bg-blue-100 text-blue-700 font-medium' : 'text-zinc-600 hover:bg-zinc-100'}`}
                  onClick={() => setUnidadAnalisis('insumos')}
                >
                  Insumos
                </button>
              </div>
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input
                  type="checkbox"
                  className="rounded border-zinc-300"
                  checked={agruparPorProveedor}
                  onChange={(e) => setAgruparPorProveedor(e.target.checked)}
                />
                <span>Agrupar por Proveedor</span>
              </label>
              <ExportButtons
                filename="auditoria_operativa"
                title="Reporte de Auditoría Operativa"
                columns={auditoriaExport.columns}
                rows={auditoriaExport.rows}
                meta={auditoriaExport.meta}
                sheets={auditoriaExport.sheets}
                testid="auditoria-export-fs"
              />
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowFullscreenAuditoria(false)}
                className="h-8 px-2"
              >
                <Minimize2 className="h-4 w-4 mr-1" />
                Minimizar
              </Button>
            </div>
          </DialogHeader>
          <div className="flex-1 overflow-auto p-0" style={{ height: 'calc(95vh - 70px)' }}>
            <div className="overflow-x-auto min-w-full">
              <table className="w-max min-w-full text-sm">
                <thead className="sticky top-0 bg-zinc-800 text-white z-10">
                  <tr>
                    {agruparPorProveedor && <th className="py-3 px-3 text-left whitespace-nowrap">Proveedor</th>}
                    {agruparPorProveedor && <th className="py-3 px-3 text-left whitespace-nowrap">Folio Pedido</th>}
                    <th className="py-3 px-3 text-left whitespace-nowrap">Producto</th>
                    <th className="py-3 px-3 text-right whitespace-nowrap">{unidadAnalisis === 'presentaciones' ? 'Inv.Ini (Pres)' : 'Inv.Ini (Ins)'}</th>
                    <th className="py-3 px-3 text-right text-zinc-400 whitespace-nowrap">{unidadAnalisis === 'presentaciones' ? '(Ins)' : '(Pres)'}</th>
                    <th className="py-3 px-3 text-right whitespace-nowrap">{unidadAnalisis === 'presentaciones' ? '+Mov (Pres)' : '+Mov (Ins)'}</th>
                    <th className="py-3 px-3 text-right text-zinc-400 whitespace-nowrap">{unidadAnalisis === 'presentaciones' ? '(Ins)' : '(Pres)'}</th>
                    <th className="py-3 px-3 text-right whitespace-nowrap">{unidadAnalisis === 'presentaciones' ? '-Cons (Pres)' : '-Cons (Ins)'}</th>
                    <th className="py-3 px-3 text-right text-zinc-400 whitespace-nowrap">{unidadAnalisis === 'presentaciones' ? '(Ins)' : '(Pres)'}</th>
                    <th className="py-3 px-3 text-right whitespace-nowrap">{unidadAnalisis === 'presentaciones' ? 'Teórico (Pres)' : 'Teórico (Ins)'}</th>
                    <th className="py-3 px-3 text-right text-zinc-400 whitespace-nowrap">{unidadAnalisis === 'presentaciones' ? '(Ins)' : '(Pres)'}</th>
                    <th className="py-3 px-3 text-right whitespace-nowrap">Físico</th>
                    <th className="py-3 px-3 text-right whitespace-nowrap">Diferencia</th>
                    <th className="py-3 px-3 text-right whitespace-nowrap">Costo Unit</th>
                    <th className="py-3 px-3 text-right whitespace-nowrap">Importe</th>
                    <th className="py-3 px-3 text-center whitespace-nowrap">Días Inv</th>
                    <th className="py-3 px-3 text-center whitespace-nowrap">Días Obj</th>
                    <th className="py-3 px-3 text-right whitespace-nowrap">Pedido</th>
                    <th className="py-3 px-3 text-right whitespace-nowrap">Ajuste</th>
                    <th className="py-3 px-3 text-center whitespace-nowrap">Recomendar</th>
                  </tr>
                </thead>
              <tbody>
                {resultados && (() => {
                  let lastProveedor = null;
                  let lastFolio = null;
                  
                  return resultados.map((r, idx) => {
                    const rendimiento = parseFloat(r.rendimiento) || 1;
                    
                    const invIniValues = getConversionValues(r.inv_inicial, rendimiento);
                    const movValues = getConversionValuesMovimientos(r.movimientos || r.entradas || 0, rendimiento);
                    const consValues = getConversionValuesConsumo(Math.abs(r.consumos || 0), rendimiento);
                    const teoricoValues = getConversionValuesInventario(r.existencia_teorica, rendimiento);
                    const fisicoValues = getConversionValuesInventario(r.inv_fisico, rendimiento);
                    const difValues = getConversionValuesInventario(r.diferencia, rendimiento);
                    const costoUnit = getCostoSegunUnidad(r);
                    
                    const isNewProveedor = agruparPorProveedor && r.proveedor !== lastProveedor;
                    const isNewFolio = agruparPorProveedor && r.folio_pedido !== lastFolio;
                    
                    if (agruparPorProveedor) {
                      lastProveedor = r.proveedor;
                      lastFolio = r.folio_pedido;
                    }
                    
                    const diasObj = diasObjetivoPorSku[r.codigo] !== undefined 
                      ? diasObjetivoPorSku[r.codigo] 
                      : (r.dias_objetivo || diasObjetivoDefault);
                    const diasInv = r.dias_inventario === 'N/A' ? 999 : parseFloat(r.dias_inventario);
                    const esBajo = diasInv < diasObj;
                    
                    return (
                      <tr key={`${r.codigo}-${r.folio_pedido || ''}-${idx}`} className={`border-b hover:bg-zinc-50 ${r.tipo_diferencia === 'contra' ? 'bg-red-50' : ''} ${isNewProveedor ? 'border-t-2 border-t-zinc-400' : ''}`}>
                        {agruparPorProveedor && (
                          <td className={`py-2 px-3 ${isNewProveedor ? 'font-semibold text-blue-700' : 'text-zinc-400'}`}>
                            {isNewProveedor ? r.proveedor || 'Sin proveedor' : ''}
                          </td>
                        )}
                        {agruparPorProveedor && (
                          <td className={`py-2 px-3 ${isNewFolio ? 'font-medium' : 'text-zinc-400'}`}>
                            {isNewFolio ? r.folio_pedido || '-' : ''}
                          </td>
                        )}
                        <td className="py-2 px-3 font-medium">{r.producto}</td>
                        <td className="py-2 px-3 text-right">{invIniValues.principal}</td>
                        <td className="py-2 px-3 text-right text-zinc-400">{invIniValues.alternativo}</td>
                        <td className="py-2 px-3 text-right text-green-600">+{movValues.principal}</td>
                        <td className="py-2 px-3 text-right text-zinc-400">{movValues.alternativo}</td>
                        <td className="py-2 px-3 text-right text-red-600">-{consValues.principal}</td>
                        <td className="py-2 px-3 text-right text-zinc-400">{consValues.alternativo}</td>
                        <td className="py-2 px-3 text-right font-medium">{teoricoValues.principal}</td>
                        <td className="py-2 px-3 text-right text-zinc-400">{teoricoValues.alternativo}</td>
                        <td className="py-2 px-3 text-right">{fisicoValues.principal}</td>
                        <td className={`py-2 px-3 text-right font-bold ${r.diferencia >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {r.diferencia >= 0 ? '+' : ''}{difValues.principal}
                        </td>
                        <td className="py-2 px-3 text-right text-zinc-500">{formatCurrency(costoUnit)}</td>
                        <td className={`py-2 px-3 text-right font-semibold ${r.importe_diferencia >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {formatCurrency(r.importe_diferencia)}
                        </td>
                        <td className="py-2 px-3 text-center">
                          <span className={`px-2 py-0.5 rounded text-xs ${
                            r.dias_inventario === 'N/A' ? 'bg-zinc-100' :
                            esBajo ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                          }`}>
                            {r.dias_inventario}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-center">{diasObj}</td>
                        <td className="py-2 px-3 text-right">{r.cantidad_pedido || '-'}</td>
                        <td className="py-2 px-3 text-right">
                          {r.ajuste_sugerido ? formatNumber(r.ajuste_sugerido) : '-'}
                        </td>
                        <td className="py-2 px-3 text-center">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            r.recomendacion === 'COMPRAR' ? 'bg-orange-100 text-orange-700' :
                            r.recomendacion === 'OK' ? 'bg-green-100 text-green-700' :
                            r.recomendacion === 'REDUCIR' ? 'bg-blue-100 text-blue-700' :
                            'bg-zinc-100 text-zinc-600'
                          }`}>
                            {r.recomendacion || '-'}
                          </span>
                        </td>
                      </tr>
                    );
                  });
                })()}
              </tbody>
            </table>
          </div>
        </div>
        </DialogContent>
      </Dialog>
      
      {/* Modal de Captura Manual de Inventario Físico - ARRASTRABLE */}
      {mostrarCapturaManual && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
          <div 
            className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden"
            style={{
              transform: `translate(${modalPosition.x}px, ${modalPosition.y}px)`,
              cursor: isDragging ? 'grabbing' : 'default'
            }}
          >
            <div 
              className="modal-header-drag px-4 py-3 border-b flex items-center justify-between bg-blue-50 cursor-grab"
              onMouseDown={handleMouseDown}
            >
              <div>
                <h3 className="font-semibold text-blue-800">Captura Manual de Inventario Físico</h3>
                <p className="text-xs text-blue-600">Arrastre esta barra para mover • Ingrese cantidades en insumos y/o presentaciones</p>
              </div>
              <button 
                onClick={() => setMostrarCapturaManual(false)}
                className="p-1 hover:bg-blue-200 rounded"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div ref={capturaScrollRef} className="overflow-y-auto max-h-[65vh]">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-zinc-100">
                  <tr>
                    <th className="py-2 px-3 text-left">Código</th>
                    <th className="py-2 px-3 text-left">Producto</th>
                    <th className="py-2 px-3 text-center">Rend.</th>
                    <th className="py-2 px-3 text-right">Insumos (pz)</th>
                    <th className="py-2 px-3 text-right">Presentaciones</th>
                    <th className="py-2 px-3 text-right font-bold">Total (Insumos)</th>
                    <th className="py-2 px-3 text-right text-zinc-500">(Presentaciones)</th>
                    <th className="py-2 px-1 text-center w-10">X</th>
                  </tr>
                </thead>
                <tbody>
                  {inventarioManualCaptura.map((item, idx) => {
                    const rendimiento = item.rendimiento || 1;
                    const totalPresentaciones = rendimiento > 0 ? item.totalInsumos / rendimiento : 0;
                    
                    return (
                      <tr key={item.codigo} className={`border-b ${idx % 2 === 0 ? 'bg-white' : 'bg-zinc-50'}`} data-row-index={idx}>
                        <td className="py-2 px-3 font-mono text-xs">{item.codigo}</td>
                        <td className="py-2 px-3">{item.producto}</td>
                        <td className="py-2 px-3 text-center text-zinc-500">{rendimiento}</td>
                        <td className="py-1 px-2">
                          <Input 
                            type="number"
                            value={item.cantidadInsumos || 0}
                            onChange={(e) => {
                              const insumos = parseFloat(e.target.value) || 0;
                              setInventarioManualCaptura(prev => prev.map(i => {
                                if (i.codigo === item.codigo) {
                                  const totalInsumos = insumos + ((i.cantidadPresentaciones || 0) * rendimiento);
                                  return { ...i, cantidadInsumos: insumos, totalInsumos };
                                }
                                return i;
                              }));
                            }}
                            onFocus={(e) => {
                              e.target.select();
                              // Auto-scroll para mantener la fila visible
                              const row = e.target.closest('tr');
                              if (row && capturaScrollRef.current) {
                                const container = capturaScrollRef.current;
                                const rowRect = row.getBoundingClientRect();
                                const containerRect = container.getBoundingClientRect();
                                
                                // Si la fila está cerca del borde inferior, hacer scroll
                                if (rowRect.bottom > containerRect.bottom - 50) {
                                  container.scrollTop += rowRect.bottom - containerRect.bottom + 100;
                                }
                                // Si la fila está cerca del borde superior, hacer scroll hacia arriba
                                if (rowRect.top < containerRect.top + 50) {
                                  container.scrollTop -= containerRect.top - rowRect.top + 100;
                                }
                              }
                            }}
                            className="h-8 w-24 text-right"
                          />
                        </td>
                        <td className="py-1 px-2">
                          <Input 
                            type="number"
                            value={item.cantidadPresentaciones || 0}
                            onChange={(e) => {
                              const presentaciones = parseFloat(e.target.value) || 0;
                              setInventarioManualCaptura(prev => prev.map(i => {
                                if (i.codigo === item.codigo) {
                                  const totalInsumos = (i.cantidadInsumos || 0) + (presentaciones * rendimiento);
                                  return { ...i, cantidadPresentaciones: presentaciones, totalInsumos };
                                }
                                return i;
                              }));
                            }}
                            onFocus={(e) => {
                              e.target.select();
                              // Auto-scroll para mantener la fila visible
                              const row = e.target.closest('tr');
                              if (row && capturaScrollRef.current) {
                                const container = capturaScrollRef.current;
                                const rowRect = row.getBoundingClientRect();
                                const containerRect = container.getBoundingClientRect();
                                
                                // Si la fila está cerca del borde inferior, hacer scroll
                                if (rowRect.bottom > containerRect.bottom - 50) {
                                  container.scrollTop += rowRect.bottom - containerRect.bottom + 100;
                                }
                                // Si la fila está cerca del borde superior, hacer scroll hacia arriba
                                if (rowRect.top < containerRect.top + 50) {
                                  container.scrollTop -= containerRect.top - rowRect.top + 100;
                                }
                              }
                            }}
                            className="h-8 w-24 text-right"
                          />
                        </td>
                        <td className="py-2 px-3 text-right font-bold text-blue-600">{formatNumber(item.totalInsumos || 0)}</td>
                        <td className="py-2 px-3 text-right text-zinc-500">({formatNumber(totalPresentaciones)})</td>
                        <td className="py-1 px-1 text-center">
                          <button
                            onClick={() => eliminarProductoCaptura(item.codigo)}
                            className="p-1 text-red-500 hover:bg-red-100 rounded"
                            title="Eliminar producto"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            
            <div className="px-4 py-3 border-t bg-zinc-50 flex justify-between items-center">
              <div className="flex items-center gap-4">
                <div className="text-sm text-zinc-600">
                  Total productos con inventario: {inventarioManualCaptura.filter(i => i.totalInsumos > 0).length} de {inventarioManualCaptura.length}
                </div>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={limpiarInventarioCaptura}
                  className="text-red-600 border-red-300 hover:bg-red-50"
                >
                  <Trash2 className="h-4 w-4 mr-1" />
                  Limpiar Todo
                </Button>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setMostrarCapturaManual(false)}>
                  Cancelar
                </Button>
                <Button onClick={aplicarInventarioManual}>
                  <Check className="h-4 w-4 mr-1" />
                  Aplicar Inventario
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
      
    </div>
  );
}

export default function Compras() {
  // FASE 3.2: Usar AuthContext para esperar a que el usuario esté autenticado
  const { user, loading: authLoading } = useAuth();
  
  // FASE 3.2: Unidades de negocio reemplazan servidores como filtro visible
  const [unidadesNegocio, setUnidadesNegocio] = useState([]);
  const [selectedUnidad, setSelectedUnidad] = useState('');
  const [selectedSucursal, setSelectedSucursal] = useState('');
  const [sucursales, setSucursales] = useState([]);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loadingUnidades, setLoadingUnidades] = useState(true);
  
  // Derivar server_id desde la unidad seleccionada (dato interno, no visible)
  const selectedServer = useMemo(() => {
    return getServerIdFromUnidad(unidadesNegocio, selectedUnidad);
  }, [unidadesNegocio, selectedUnidad]);
  
  // Para compatibilidad con componentes hijos que esperan "servers"
  // Transformamos unidades a un formato compatible
  const servers = useMemo(() => {
    return unidadesNegocio.map(u => ({
      id: u.server_id,
      name: u.nombre,
      system_type: u.system_type,
      // Metadata adicional de la unidad
      unidad_id: u.id,
      sucursal_origen_id: u.sucursal_origen_id
    }));
  }, [unidadesNegocio]);

  useEffect(() => {
    // FASE 3.2: Esperar a que el usuario esté autenticado antes de cargar unidades
    logger.log(`[Compras] useEffect triggered - authLoading: ${authLoading}, user: ${user?.email || 'null'}`);
    
    if (authLoading) {
      logger.log('[Compras] Esperando autenticación...');
      return; // Aún cargando auth
    }
    
    if (!user) {
      logger.log('[Compras] No hay usuario autenticado');
      return; // No autenticado
    }
    
    logger.log(`[Compras] Usuario autenticado: ${user.email}, procediendo a cargar unidades`);
    
    // FASE 3.2: Cargar unidades de negocio según RBAC
    const loadUnidades = async () => {
      logger.log('[Compras] Iniciando carga de unidades...');
      setLoadingUnidades(true);
      try {
        logger.log('[Compras] Llamando a fetchUnidadesNegocio()...');
        const unidades = await fetchUnidadesNegocio();
        logger.log(`[Compras] Unidades recibidas: ${unidades?.length || 0}`);
        setUnidadesNegocio(unidades);
        
        // Auto-seleccionar si el usuario tiene solo una unidad
        if (unidades.length === 1) {
          setSelectedUnidad(unidades[0].id);
          logger.log(`[Compras] Auto-seleccionada unidad única: ${unidades[0].nombre}`);
          
          // FASE 3.2 FIX: Si la unidad tiene solo 1 sucursal, auto-seleccionarla también
          const sucursalesUnidad = unidades[0].sucursales || [];
          if (sucursalesUnidad.length === 1) {
            const sucNombre = sucursalesUnidad[0].nombre || sucursalesUnidad[0].codigo || sucursalesUnidad[0].id;
            setSelectedSucursal(sucNombre);
            logger.log(`[Compras] Auto-seleccionada sucursal única: ${sucNombre}`);
          }
        } else {
          // Restaurar unidad guardada
          const saved = localStorage.getItem(STORAGE_KEY);
          if (saved) {
            const params = JSON.parse(saved);
            if (params.unidad && unidades.find(u => u.id === params.unidad)) {
              setSelectedUnidad(params.unidad);
              // FASE 3.2 FIX: Auto-seleccionar sucursal si solo hay una
              const unidadRestaurada = unidades.find(u => u.id === params.unidad);
              if (unidadRestaurada?.sucursales?.length === 1) {
                const sucNombre = unidadRestaurada.sucursales[0].nombre || unidadRestaurada.sucursales[0].codigo || unidadRestaurada.sucursales[0].id;
                setSelectedSucursal(sucNombre);
                logger.log(`[Compras] Auto-seleccionada sucursal de unidad restaurada: ${sucNombre}`);
              }
            } else if (params.server) {
              // Compatibilidad: si había server guardado, buscar unidad correspondiente
              const unidadPorServer = unidades.find(u => u.server_id === params.server);
              if (unidadPorServer) {
                setSelectedUnidad(unidadPorServer.id);
                // FASE 3.2 FIX: Auto-seleccionar sucursal si solo hay una
                if (unidadPorServer.sucursales?.length === 1) {
                  const sucNombre = unidadPorServer.sucursales[0].nombre || unidadPorServer.sucursales[0].codigo || unidadPorServer.sucursales[0].id;
                  setSelectedSucursal(sucNombre);
                  logger.log(`[Compras] Auto-seleccionada sucursal de unidad por server: ${sucNombre}`);
                }
              }
            }
          }
        }
      } catch (error) {
        logger.error('Error cargando unidades de negocio:', error);
      } finally {
        setLoadingUnidades(false);
      }
    };
    loadUnidades();
  }, [user, authLoading]);

  // Cargar sucursales cuando cambia la unidad seleccionada.
  // Auditoría opera exclusivamente por Unidad de Negocio canónica y no
  // necesita consultar /servers/{server_id}/sucursales.
  useEffect(() => {
    if (activeTab === 'auditoria') {
      setSucursales([]);
      setSelectedSucursal('');
      return;
    }

    if (selectedUnidad && selectedServer) {
      const fetchSucursales = async () => {
        try {
          const response = await api.get(`/servers/${selectedServer}/sucursales`);
          const sucursalesData = response.data;
          setSucursales(sucursalesData);
          
          // Para unidades con sucursal_origen_id definida (MPRO), preseleccionar
          const unidad = unidadesNegocio.find(u => u.id === selectedUnidad);
          if (unidad?.sucursal_origen_id) {
            // CORRECCIÓN AUDITORIA-COMPRAS-FRONTEND-01 (2026-04-29):
            // Para MPRO, usar el código de sucursal (id) directamente, no el nombre.
            // El endpoint /api/compras/dashboard requiere Sc_Cve_Sucursal exacto (ej: "0021", "0023")
            const sucursalMatch = sucursalesData.find(s => 
              s.id === unidad.sucursal_origen_id || 
              s.codigo === unidad.sucursal_origen_id
            );
            if (sucursalMatch) {
              // Usar el ID/código exacto para MPRO
              setSelectedSucursal(sucursalMatch.id || sucursalMatch.codigo || sucursalMatch.nombre);
            } else if (sucursalesData.length === 1) {
              setSelectedSucursal(sucursalesData[0].id || sucursalesData[0].codigo || sucursalesData[0].nombre);
            }
          } else if (sucursalesData.length === 1) {
            // SoftRestaurant: usar nombre ya que es single-tenant
            setSelectedSucursal(sucursalesData[0].nombre || sucursalesData[0].codigo || sucursalesData[0].id);
          } else {
            setSelectedSucursal(''); // Reset si hay múltiples
          }
          
          // Guardar unidad seleccionada
          localStorage.setItem(STORAGE_KEY, JSON.stringify({ unidad: selectedUnidad, server: selectedServer }));
        } catch (error) {
          logger.error('Error cargando sucursales:', error);
          setSucursales([]);
        }
      };
      fetchSucursales();
    } else {
      setSucursales([]);
      setSelectedSucursal('');
    }
  }, [selectedUnidad, selectedServer, unidadesNegocio, activeTab]);
  
  // Handler para cambio de unidad (usado en componentes hijos)
  const handleUnidadChange = (unidadId) => {
    setSelectedUnidad(unidadId);
  };
  
  // Handler para cambio de server (compatibilidad con componentes hijos)
  // Traduce server_id a unidad_id
  const handleServerChange = (serverId) => {
    const unidad = unidadesNegocio.find(u => u.server_id === serverId);
    if (unidad) {
      setSelectedUnidad(unidad.id);
    }
  };

  return (
    <div className="space-y-4" data-testid="compras-module">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-zinc-800">Compras</h1>
        <p className="text-sm text-zinc-500">Gestión y análisis de compras</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5 mb-4">
          <TabsTrigger value="dashboard" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Dashboard
          </TabsTrigger>
          <TabsTrigger value="autorizacion" className="flex items-center gap-2">
            <ShoppingCart className="h-4 w-4" />
            Autorización
          </TabsTrigger>
          <TabsTrigger value="analisis" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Análisis
          </TabsTrigger>
          <TabsTrigger value="auditoria" className="flex items-center gap-2">
            <FileWarning className="h-4 w-4" />
            Auditoría
          </TabsTrigger>
          <TabsTrigger value="proveedores" className="flex items-center gap-2">
            <Building2 className="h-4 w-4" />
            Portal Proveedores
          </TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard">
          <DashboardCompras 
            servers={servers}
            unidadesNegocio={unidadesNegocio}
            selectedUnidad={selectedUnidad}
            setSelectedUnidad={handleUnidadChange}
            selectedServer={selectedServer} 
            setSelectedServer={handleServerChange}
            selectedSucursal={selectedSucursal}
            setSelectedSucursal={setSelectedSucursal}
            sucursales={sucursales}
            loadingUnidades={loadingUnidades}
          />
        </TabsContent>

        <TabsContent value="autorizacion">
          <AutorizacionComprasTab 
            servers={servers}
            unidadesNegocio={unidadesNegocio}
            selectedUnidad={selectedUnidad}
            setSelectedUnidad={handleUnidadChange}
            selectedServer={selectedServer} 
            setSelectedServer={handleServerChange}
            selectedSucursal={selectedSucursal}
            setSelectedSucursal={setSelectedSucursal}
            sucursales={sucursales}
          />
        </TabsContent>

        <TabsContent value="analisis">
          <AnalisisCompras 
            servers={servers}
            unidadesNegocio={unidadesNegocio}
            selectedUnidad={selectedUnidad}
            setSelectedUnidad={handleUnidadChange}
            selectedServer={selectedServer} 
            setSelectedServer={handleServerChange}
            selectedSucursal={selectedSucursal}
            setSelectedSucursal={setSelectedSucursal}
            sucursales={sucursales}
          />
        </TabsContent>

        <TabsContent value="auditoria">
          <AuditoriaOperativaTab 
            servers={servers}
            unidadesNegocio={unidadesNegocio}
            selectedUnidad={selectedUnidad}
            setSelectedUnidad={handleUnidadChange}
            selectedServer={selectedServer} 
            setSelectedServer={handleServerChange}
            selectedSucursal={selectedSucursal}
            setSelectedSucursal={setSelectedSucursal}
            sucursales={sucursales}
          />
        </TabsContent>

        <TabsContent value="proveedores">
          <PortalProveedoresTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
