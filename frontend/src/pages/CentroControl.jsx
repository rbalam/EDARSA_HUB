/**
 * CENTRO DE CONTROL EDARSA
 * ========================
 * Módulo central de monitoreo, estabilidad y control técnico.
 * 
 * Tipo: Control Directivo/Técnico (NO Operativo)
 * Wireframe: /app/docs/CENTRO_DE_CONTROL_EDARSA_WIREFRAME.md
 * 
 * Pantallas:
 * 1. Resumen General
 * 2. Salud por Módulo
 * 3. Alertas y Regresiones
 * 4. Conectividad y Fuentes
 * 5. Jobs y Automatizaciones
 * 6. Cambios y Despliegues
 * 7. Bitácora / Historial
 * 8. Configuración y Blindaje
 * 
 * WebSocket: Notificaciones en tiempo real para alertas críticas
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import logger from '../services/logger';
import api from '../lib/api';
// FASE AUTH-SECURITY-01 / FASE 4.2: getToken eliminado permanentemente
import { 
  Activity, AlertTriangle, CheckCircle, XCircle, RefreshCw, 
  Server, Database, Zap, Clock, Shield, Eye, Bell, 
  ChevronRight, Info, Settings, Wifi, WifiOff,
  Play, Pause, FileText, GitBranch, TrendingUp, Calendar,
  AlertCircle, CheckCircle2, Circle, ExternalLink,
  Timer, Cpu, Radio, Lock
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import {
  useWebSocketNotifications,
  useCentroControlData,
  DestinatariosManager,
  SemaforoGlobal,
  KPICard,
  SeverityBadge,
  StatusDot,
  CategoriaSemaforo,
  ModuloCard,
  FuenteCard,
  AlertaRow,
  EventoRow,
  EstadoVacio,
  BannerAlertaCritica
} from '../components/centro-control';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// ============================================================================
// COMPONENTE PRINCIPAL
// ============================================================================

const CentroControl = () => {
  const navigate = useNavigate();
  // Estado de UI
  const [activeTab, setActiveTab] = useState('resumen');
  const [autoRefresh, setAutoRefresh] = useState(false);
  
  // Detalle seleccionado
  const [selectedModulo, setSelectedModulo] = useState(null);
  const [selectedAlerta, setSelectedAlerta] = useState(null);
  
  // Estado de notificaciones (TODO: mover a hook dedicado)
  const [destinatarios, setDestinatarios] = useState([]);
  const [notificacionesConfig, setNotificacionesConfig] = useState(null);
  const [modulosBlindados, setModulosBlindados] = useState([]);
  const [blindajeStatus, setBlindajeStatus] = useState(null);
  
  // Estado para formulario de nuevo destinatario
  const [nuevoDestinatario, setNuevoDestinatario] = useState({
    tipo: 'email',
    destinatario: '',
    nombre: ''
  });
  
  // Estado de loading para lista de destinatarios
  const [loadingDestinatarios, setLoadingDestinatarios] = useState(false);
  
  // Hook para datos (extraído a useCentroControlData)
  const {
    loading,
    refreshing,
    estadoGeneral,
    healthData,
    alertas,
    fuentes,
    jobs,
    bitacora,
    metricas,
    historial,
    matrizResolucion,
    handleRefresh,
    loadAllData,
    addAlerta,
    fetchEstadoGeneral,
    fetchHealthData,
    fetchAlertas
  } = useCentroControlData();

  // ============================================================================
  // WEBSOCKET: Notificaciones en Tiempo Real
  // ============================================================================
  
  const handleAlertaCritica = useCallback((alerta) => {
    addAlerta(alerta);
    setActiveTab('alertas');
  }, [addAlerta]);

  const handleAlertaNueva = useCallback((alerta) => {
    addAlerta(alerta);
  }, [addAlerta]);

  const handleEstadoCambio = useCallback(() => {
    fetchEstadoGeneral();
    fetchHealthData();
  }, [fetchEstadoGeneral, fetchHealthData]);

  const { wsConnected, wsStatus, reconnect } = useWebSocketNotifications(
    handleAlertaCritica,
    handleAlertaNueva,
    handleEstadoCambio
  );

  // ============================================================================
  // ACCIONES
  // ============================================================================

  // Ejecutar checks de regresión
  const runRegressionChecks = async () => {
    try {
      toast.loading('Ejecutando checks...');
      await api.post('/centro-control/regresiones');
      toast.dismiss();
      toast.success('Checks de regresión completados');
      await loadAllData();
    } catch (err) {
      toast.dismiss();
      toast.error('Error de conexión');
    }
  };

  // Reconocer alerta
  const acknowledgeAlert = async (alertId) => {
    try {
      await api.post('/centro-control/alertas/acknowledge', { alert_id: alertId });
      toast.success('Alerta reconocida');
      await fetchAlertas();
    } catch (err) {
      toast.error('Error al reconocer alerta');
    }
  };

  // Auto-refresh
  useEffect(() => {
    let interval;
    if (autoRefresh) {
      interval = setInterval(loadAllData, 60000);
    }
    return () => clearInterval(interval);
  }, [autoRefresh, loadAllData]);

  // Funciones para cargar datos de notificaciones
  const fetchDestinatarios = useCallback(async () => {
    setLoadingDestinatarios(true);
    try {
      const response = await api.get('/centro-control/destinatarios');
      setDestinatarios(response.data.destinatarios || []);
    } catch (err) {
      logger.error('Error cargando destinatarios:', err);
    } finally {
      setLoadingDestinatarios(false);
    }
  }, []);

  const fetchNotificacionesConfig = useCallback(async () => {
    try {
      const response = await api.get('/notificaciones/config');
      setNotificacionesConfig(response.data);
    } catch (err) {
      logger.error('Error cargando config de notificaciones:', err);
    }
  }, []);

  const fetchBlindaje = useCallback(async () => {
    try {
      const response = await api.get('/centro-control/blindaje/modulos');
      setModulosBlindados(response.data.modulos || []);
      setBlindajeStatus(response.data.status || null);
    } catch (err) {
      logger.error('Error cargando blindaje:', err);
      setModulosBlindados([]);
      setBlindajeStatus('ERROR');
    }
  }, []);

  // ============================================================================
  // FUNCIONES DE GESTIÓN DE DESTINATARIOS
  // ============================================================================

  // Agregar destinatario
  const agregarDestinatario = async () => {
    if (!nuevoDestinatario.destinatario) {
      toast.error('Ingrese un destinatario');
      return;
    }
    try {
      await api.post('/centro-control/destinatarios', nuevoDestinatario);
      toast.success('Destinatario agregado');
      setNuevoDestinatario({ tipo: 'email', destinatario: '', nombre: '' });
      fetchDestinatarios();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error de conexión');
    }
  };

  // Toggle activo/inactivo
  const toggleDestinatarioActivo = async (id, activo) => {
    try {
      await api.put(`/centro-control/destinatarios/${id}`, { activo: !activo });
      toast.success(activo ? 'Desactivado' : 'Activado');
      fetchDestinatarios();
    } catch (err) {
      toast.error('Error al actualizar');
    }
  };

  // Eliminar destinatario
  const eliminarDestinatario = async (id) => {
    if (!window.confirm('¿Eliminar destinatario?')) return;
    try {
      await api.delete(`/centro-control/destinatarios/${id}`);
      toast.success('Eliminado');
      fetchDestinatarios();
    } catch (err) {
      toast.error('Error al eliminar');
    }
  };

  // Enviar email de prueba
  const enviarPruebaEmail = async () => {
    const emailActivo = destinatarios.find(d => d.tipo === 'email' && d.activo);
    if (!emailActivo) {
      toast.error('No hay destinatarios de email activos');
      return;
    }
    try {
      toast.loading('Enviando email de prueba...');
      await api.post('/centro-control/notificaciones/email/test', { recipient: emailActivo.destinatario });
      toast.dismiss();
      toast.success('Email de prueba enviado');
    } catch (err) {
      toast.dismiss();
      toast.error(err.response?.data?.detail || 'Error de conexión');
    }
  };

  // Enviar whatsapp de prueba
  const enviarPruebaWhatsApp = async () => {
    const waActivo = destinatarios.find(d => d.tipo === 'whatsapp' && d.activo);
    if (!waActivo) {
      toast.error('No hay destinatarios de WhatsApp activos');
      return;
    }
    try {
      toast.loading('Enviando WhatsApp de prueba...');
      await api.post('/centro-control/notificaciones/whatsapp/test', { recipient: waActivo.destinatario });
      toast.dismiss();
      toast.success('WhatsApp de prueba enviado');
    } catch (err) {
      toast.dismiss();
      toast.error(err.response?.data?.detail || 'Error de conexión');
    }
  };

  // Carga inicial - loading se maneja internamente en useCentroControlData
  useEffect(() => {
    loadAllData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Cargar datos de notificaciones cuando se selecciona esa pestaña
  useEffect(() => {
    if (activeTab === 'notificaciones') {
      fetchDestinatarios();
      fetchNotificacionesConfig();
    }
    if (activeTab === 'blindaje') {
      fetchBlindaje();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  // ============================================================================
  // COMPUTED VALUES
  // ============================================================================
  
  const alertasActivas = alertas.filter(a => !a.reconocida);
  const alertasCriticas = alertasActivas.filter(a => a.severidad === 'critical').length;
  const modulosSanos = healthData?.modules_summary?.filter(m => m.status === 'healthy').length || 0;
  const modulosTotal = healthData?.modules_summary?.length || 0;
  const fuentesOnline = fuentes.filter(f => f.estado === 'healthy').length;
  const fuentesTotal = fuentes.length;

  // Cambios recientes se derivan de la bitácora SQL ya cargada.
  const cambiosRecientes = bitacora.filter(b => ['deploy', 'cambio_codigo', 'hotfix', 'config'].includes(b.tipo));

  // ============================================================================
  // RENDER - LOADING
  // ============================================================================
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96" data-testid="loading">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-zinc-400">Cargando Centro de Control...</p>
        </div>
      </div>
    );
  }

  // ============================================================================
  // RENDER - TABS
  // ============================================================================

  return (
    <div className="space-y-6" data-testid="centro-control">
      {/* ================================================================== */}
      {/* HEADER */}
      {/* ================================================================== */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-zinc-900 border border-zinc-800 rounded-lg shadow-sm">
            <Shield className="w-8 h-8 text-zinc-100" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-zinc-100">Centro de Control EDARSA</h1>
            <p className="text-sm text-zinc-400">Estado actual del sistema</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2 flex-wrap">
          {/* Indicador WebSocket */}
          <div 
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs ${
              wsConnected 
                ? 'bg-green-500/20 border border-green-500/50 text-green-400' 
                : wsStatus === 'reconnecting'
                ? 'bg-yellow-500/20 border border-yellow-500/50 text-yellow-400 animate-pulse'
                : 'bg-red-500/20 border border-red-500/50 text-red-400'
            }`}
            title={`WebSocket: ${wsStatus}`}
          >
            <Radio className={`w-3 h-3 ${wsConnected ? 'animate-pulse' : ''}`} />
            <span>{wsConnected ? 'Live' : wsStatus === 'reconnecting' ? 'Reconectando...' : 'Offline'}</span>
            {!wsConnected && wsStatus !== 'reconnecting' && (
              <button onClick={reconnect} className="ml-1 hover:text-white">↻</button>
            )}
          </div>
          
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={autoRefresh ? 'border-emerald-800 bg-emerald-950/30 text-emerald-300' : 'border-zinc-800 bg-zinc-900 text-zinc-300'}
          >
            <Clock className="w-4 h-4 mr-2" />
            Auto {autoRefresh ? 'ON' : 'OFF'}
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleRefresh}
            disabled={refreshing}
            className="border-zinc-800 bg-zinc-900 text-zinc-300 hover:bg-zinc-800"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refrescar
          </Button>
          <Button onClick={runRegressionChecks} disabled={refreshing} size="sm">
            <Zap className="w-4 h-4 mr-2" />
            Ejecutar Checks
          </Button>
        </div>
      </div>

      {/* ================================================================== */}
      {/* BANNER ALERTAS CRÍTICAS */}
      {/* ================================================================== */}
      {alertasCriticas > 0 && (
        <BannerAlertaCritica 
          count={alertasCriticas} 
          onClick={() => setActiveTab('alertas')} 
        />
      )}

      {/* ================================================================== */}
      {/* TABS */}
      {/* ================================================================== */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-zinc-950/70 border border-zinc-800 rounded-lg flex-wrap h-auto gap-1 p-1 shadow-sm">
          <TabsTrigger value="resumen" className="text-xs">Resumen</TabsTrigger>
          <TabsTrigger value="modulos" className="text-xs">Módulos</TabsTrigger>
          <TabsTrigger value="alertas" className="text-xs relative">
            Alertas
            {alertasActivas.length > 0 && (
              <span className="ml-1 px-1.5 py-0.5 bg-red-500 rounded-full text-[10px]">
                {alertasActivas.length}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="fuentes" className="text-xs">Fuentes</TabsTrigger>
          <TabsTrigger value="jobs" className="text-xs">Jobs</TabsTrigger>
          <TabsTrigger value="cambios" className="text-xs">Cambios</TabsTrigger>
          <TabsTrigger value="bitacora" className="text-xs">Bitácora</TabsTrigger>
          <TabsTrigger value="notificaciones" className="text-xs">
            <Bell className="w-3 h-3 mr-1" />
            Notificaciones
          </TabsTrigger>
          <TabsTrigger value="blindaje" className="text-xs">Blindaje</TabsTrigger>
        </TabsList>

        {/* ================================================================ */}
        {/* TAB 1: RESUMEN GENERAL */}
        {/* ================================================================ */}
        <TabsContent value="resumen" className="mt-6 space-y-6">
          {/* Semáforo Global + KPIs */}
          <div className="grid grid-cols-1 lg:grid-cols-6 gap-4">
            <div className="lg:col-span-2">
              <SemaforoGlobal 
                status={estadoGeneral?.estado_general || healthData?.status || 'unknown'}
                timestamp={estadoGeneral?.timestamp || healthData?.timestamp}
              />
            </div>
            <div className="lg:col-span-4 grid grid-cols-2 md:grid-cols-4 gap-3">
              <KPICard 
                title="Módulos Sanos"
                value={`${modulosSanos}/${modulosTotal}`}
                subtitle={`${modulosTotal > 0 ? Math.round(modulosSanos/modulosTotal*100) : 0}%`}
                icon={Activity}
                status={modulosSanos === modulosTotal ? 'success' : modulosSanos > 0 ? 'warning' : 'danger'}
              />
              <KPICard 
                title="Alertas Activas"
                value={alertasActivas.length}
                subtitle={alertasCriticas > 0 ? `${alertasCriticas} críticas` : 'Sin críticas'}
                icon={Bell}
                status={alertasCriticas > 0 ? 'danger' : alertasActivas.length > 0 ? 'warning' : 'success'}
                onClick={() => setActiveTab('alertas')}
              />
              <KPICard 
                title="Fuentes Online"
                value={`${fuentesOnline}/${fuentesTotal}`}
                icon={Database}
                status={fuentesOnline === fuentesTotal ? 'success' : 'warning'}
                onClick={() => setActiveTab('fuentes')}
              />
              <KPICard 
                title="Score Estabilidad"
                value={metricas?.metricas?.score_estabilidad || 100}
                subtitle={metricas?.interpretacion?.score_estabilidad?.toUpperCase() || 'CALCULANDO'}
                icon={TrendingUp}
                status={
                  (metricas?.metricas?.score_estabilidad || 100) >= 90 ? 'success' :
                  (metricas?.metricas?.score_estabilidad || 100) >= 70 ? 'warning' : 'danger'
                }
              />
            </div>
          </div>

          {/* Semáforos por Categoría */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-zinc-400">Semáforos por Categoría</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex justify-around py-4">
                <CategoriaSemaforo nombre="Sistema" status={estadoGeneral?.estado_general || 'healthy'} />
                <CategoriaSemaforo nombre="Datos" status={fuentesOnline === fuentesTotal ? 'healthy' : 'degraded'} />
                <CategoriaSemaforo nombre="Conexiones" status={fuentesOnline > 0 ? 'healthy' : 'critical'} />
                <CategoriaSemaforo nombre="Jobs" status={jobs?.scheduler_status === 'running' ? 'healthy' : 'degraded'} />
                <CategoriaSemaforo nombre="Blindaje" status="healthy" />
              </div>
            </CardContent>
          </Card>

          {/* Grid: Alertas + Fuentes + Módulos */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Top Alertas */}
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Bell className="w-4 h-4 text-yellow-400" />
                    Top Alertas
                  </CardTitle>
                  <Button variant="ghost" size="sm" onClick={() => setActiveTab('alertas')}>
                    Ver todas <ChevronRight className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                {alertasActivas.length === 0 ? (
                  <div className="text-center py-6">
                    <CheckCircle className="w-10 h-10 mx-auto text-green-400 mb-2" />
                    <p className="text-sm text-zinc-400">Sin alertas activas</p>
                  </div>
                ) : (
                  alertasActivas.slice(0, 3).map((alerta, idx) => (
                    <div key={alerta.id || `alerta-activa-${idx}`} className="flex items-center gap-2 p-2 bg-zinc-800/50 rounded">
                      <SeverityBadge severity={alerta.severidad} />
                      <span className="text-xs text-zinc-300 truncate flex-1">{alerta.titulo || alerta.modulo}</span>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            {/* Resumen Fuentes */}
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Database className="w-4 h-4 text-emerald-400" />
                    Fuentes de Datos
                  </CardTitle>
                  <Button variant="ghost" size="sm" onClick={() => setActiveTab('fuentes')}>
                    Ver todas <ChevronRight className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                {fuentes.slice(0, 4).map((fuente, idx) => (
                  <FuenteCard key={fuente.id || fuente.nombre || `fuente-${idx}`} fuente={fuente} />
                ))}
              </CardContent>
            </Card>

            {/* Eventos Recientes */}
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Clock className="w-4 h-4 text-blue-400" />
                    Eventos Recientes
                  </CardTitle>
                  <Button variant="ghost" size="sm" onClick={() => setActiveTab('bitacora')}>
                    Ver todos <ChevronRight className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {historial.length === 0 ? (
                  <p className="text-sm text-zinc-500 text-center py-4">Sin eventos recientes</p>
                ) : (
                  <div className="divide-y divide-zinc-800">
                    {historial.slice(0, 5).map((evento, idx) => (
                      <EventoRow key={evento.id || evento.timestamp || `evento-${idx}`} evento={evento} />
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Grid de Módulos */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Activity className="w-4 h-4 text-purple-400" />
                  Estado de Módulos
                </CardTitle>
                <Button variant="ghost" size="sm" onClick={() => setActiveTab('modulos')}>
                  Ver detalle <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                {(healthData?.modules_summary || []).map((modulo, idx) => (
                  <ModuloCard 
                    key={modulo.nombre || `modulo-card-${idx}`} 
                    modulo={{
                      ...modulo,
                      blindado: modulosBlindados.some(b => b.nombre === modulo.name)
                    }}
                    onClick={() => {
                      setSelectedModulo(modulo);
                      setActiveTab('modulos');
                    }}
                  />
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ================================================================ */}
        {/* TAB 2: SALUD POR MÓDULO */}
        {/* ================================================================ */}
        <TabsContent value="modulos" className="mt-6 space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {(healthData?.modules_summary || []).map((modulo, idx) => (
              <ModuloCard 
                key={modulo.nombre || `modulo-${idx}`} 
                modulo={{
                  ...modulo,
                  blindado: modulosBlindados.some(b => b.nombre === modulo.name),
                  confiabilidad: modulo.reliability_score || 100,
                  alertas: modulo.recent_regressions || 0
                }}
                onClick={() => setSelectedModulo(modulo)}
              />
            ))}
          </div>

          {selectedModulo && (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="w-5 h-5" />
                    {selectedModulo.name}
                  </CardTitle>
                  <Button variant="ghost" size="sm" onClick={() => setSelectedModulo(null)}>
                    <XCircle className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-3 bg-zinc-800/50 rounded-lg">
                    <p className="text-xs text-zinc-500">Estado</p>
                    <p className="text-lg font-semibold text-white capitalize">{selectedModulo.status}</p>
                  </div>
                  <div className="p-3 bg-zinc-800/50 rounded-lg">
                    <p className="text-xs text-zinc-500">Confiabilidad</p>
                    <p className="text-lg font-semibold text-white">{selectedModulo.reliability_score || 100}%</p>
                  </div>
                  <div className="p-3 bg-zinc-800/50 rounded-lg">
                    <p className="text-xs text-zinc-500">Regresiones 24h</p>
                    <p className="text-lg font-semibold text-white">{selectedModulo.recent_regressions || 0}</p>
                  </div>
                  <div className="p-3 bg-zinc-800/50 rounded-lg">
                    <p className="text-xs text-zinc-500">Blindado</p>
                    <p className="text-lg font-semibold text-white">
                      {modulosBlindados.some(b => b.nombre === selectedModulo.name) ? 'Sí' : 'No'}
                    </p>
                  </div>
                </div>

                {modulosBlindados.some(b => b.nombre === selectedModulo.name) && (
                  <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Shield className="w-5 h-5 text-blue-400" />
                      <span className="font-medium text-blue-400">Módulo Blindado</span>
                    </div>
                    <p className="text-sm text-zinc-400">
                      Este módulo está congelado funcionalmente. Cualquier cambio requiere autorización expresa.
                    </p>
                    <p className="text-xs text-zinc-500 mt-2">
                      Documento: {modulosBlindados.find(b => b.nombre === selectedModulo.name)?.documento}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* ================================================================ */}
        {/* TAB 3: ALERTAS Y REGRESIONES */}
        {/* ================================================================ */}
        <TabsContent value="alertas" className="mt-6 space-y-6">
          {/* KPIs de Alertas */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <KPICard 
              title="Críticas" 
              value={alertasActivas.filter(a => a.severidad === 'critical').length}
              icon={XCircle}
              status="danger"
            />
            <KPICard 
              title="Altas" 
              value={alertasActivas.filter(a => a.severidad === 'high').length}
              icon={AlertTriangle}
              status="warning"
            />
            <KPICard 
              title="Medias" 
              value={alertasActivas.filter(a => a.severidad === 'medium').length}
              icon={AlertCircle}
              status="neutral"
            />
            <KPICard 
              title="Bajas" 
              value={alertasActivas.filter(a => a.severidad === 'low').length}
              icon={Info}
              status="neutral"
            />
            <KPICard 
              title="Total Activas" 
              value={alertasActivas.length}
              icon={Bell}
              status={alertasActivas.length > 0 ? 'warning' : 'success'}
            />
          </div>

          {/* Lista de Alertas */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle>Alertas Activas</CardTitle>
              <CardDescription>Ordenadas por severidad</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {alertasActivas.length === 0 ? (
                <EstadoVacio 
                  icon={CheckCircle}
                  titulo="Sin alertas activas"
                  mensaje="El sistema está funcionando correctamente"
                />
              ) : (
                alertasActivas
                  .sort((a, b) => {
                    const order = { critical: 0, high: 1, medium: 2, low: 3 };
                    return (order[a.severidad] || 4) - (order[b.severidad] || 4);
                  })
                  .map((alerta, idx) => (
                    <AlertaRow 
                      key={alerta.id || `alerta-row-${idx}`}
                      alerta={alerta}
                      onAcknowledge={acknowledgeAlert}
                      onView={setSelectedAlerta}
                    />
                  ))
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ================================================================ */}
        {/* TAB 4: CONECTIVIDAD Y FUENTES */}
        {/* ================================================================ */}
        <TabsContent value="fuentes" className="mt-6 space-y-6">
          {/* KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <KPICard 
              title="Fuentes Activas" 
              value={fuentesOnline}
              icon={Wifi}
              status="success"
            />
            <KPICard 
              title="Con Warning" 
              value={fuentes.filter(f => f.estado === 'degraded').length}
              icon={AlertTriangle}
              status="warning"
            />
            <KPICard 
              title="Caídas" 
              value={fuentes.filter(f => f.estado === 'offline' || f.estado === 'critical').length}
              icon={WifiOff}
              status="danger"
            />
            <KPICard 
              title="Latencia Prom." 
              value={`${Math.round(fuentes.reduce((acc, f) => acc + (f.tiempo_respuesta_ms || 0), 0) / (fuentes.length || 1))}ms`}
              icon={Timer}
              status="neutral"
            />
            <KPICard 
              title="Total Fuentes" 
              value={fuentesTotal}
              icon={Database}
              status="neutral"
            />
          </div>

          {/* Grid de Fuentes */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle>Fuentes de Datos</CardTitle>
              <CardDescription>Estado de todas las conexiones</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {fuentes.map((fuente, idx) => (
                  <div 
                    key={fuente.id || fuente.nombre || `fuente-detail-${idx}`}
                    className={`p-4 rounded-lg border ${
                      fuente.estado === 'healthy' 
                        ? 'bg-green-500/5 border-green-500/30' 
                        : fuente.estado === 'degraded'
                        ? 'bg-yellow-500/5 border-yellow-500/30'
                        : 'bg-red-500/5 border-red-500/30'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {fuente.tipo === 'mongodb' ? (
                          <Database className="w-5 h-5 text-emerald-400" />
                        ) : (
                          <Server className="w-5 h-5 text-blue-400" />
                        )}
                        <span className="font-medium text-white">{fuente.nombre}</span>
                      </div>
                      <StatusDot status={fuente.estado === 'healthy' ? 'online' : 'offline'} size="md" />
                    </div>
                    <div className="text-xs text-zinc-500 space-y-1">
                      <p>Tipo: {fuente.tipo?.toUpperCase()}</p>
                      {fuente.tiempo_respuesta_ms && <p>Latencia: {Math.round(fuente.tiempo_respuesta_ms)}ms</p>}
                      {fuente.ultimo_exito && <p>Último éxito: {new Date(fuente.ultimo_exito).toLocaleString('es-MX')}</p>}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Matriz Fuente ↔ Módulo */}
          {matrizResolucion && (
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  Matriz de Resolución
                </CardTitle>
                <CardDescription>Cómo se resuelven las fuentes de datos</CardDescription>
              </CardHeader>
              <CardContent>
                {matrizResolucion.principios && (
                  <div className="mb-4 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                    <p className="font-medium text-blue-400 mb-2">Principios:</p>
                    <ul className="space-y-1">
                      {matrizResolucion.principios.map((p, idx) => (
                        <li key={`principio-${idx}`} className="text-sm text-zinc-400 flex items-center gap-2">
                          <CheckCircle2 className="w-3 h-3 text-blue-400" />
                          {p}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* ================================================================ */}
        {/* TAB 5: JOBS Y AUTOMATIZACIONES */}
        {/* ================================================================ */}
        <TabsContent value="jobs" className="mt-6 space-y-6">
            <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg flex items-center justify-between gap-4">
              <div>
                <p className="font-medium text-blue-400">Vista ejecutiva de jobs</p>
                <p className="text-sm text-zinc-400">
                  Centro de Control solo monitorea. Ejecutar, pausar, reanudar y re-sincronizar se gestiona en Programación.
                </p>
              </div>
              <Button
                variant="outline"
                className="shrink-0 border-blue-500/40 text-blue-400 hover:bg-blue-500/10"
                onClick={() => navigate('/scheduler')}
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                Abrir Programación
              </Button>
            </div>

          {/* Estado del Scheduler */}
          <Card className={`border-2 ${jobs?.scheduler_status === 'running' ? 'border-green-500/50 bg-green-500/5' : 'border-yellow-500/50 bg-yellow-500/5'}`}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {jobs?.scheduler_status === 'running' ? (
                    <Play className="w-8 h-8 text-green-400" />
                  ) : (
                    <Pause className="w-8 h-8 text-yellow-400" />
                  )}
                  <div>
                    <h3 className="font-semibold text-white">Scheduler EDARSA HUB</h3>
                    <p className="text-sm text-zinc-400">
                      {jobs?.scheduler_status === 'running' ? 'Ejecutándose' : 'Detenido'}
                    </p>
                  </div>
                </div>
                <Badge variant={jobs?.scheduler_status === 'running' ? 'default' : 'secondary'}>
                  {jobs?.jobs_total || 0} Jobs
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KPICard title="Jobs Activos" value={jobs?.jobs_total || 0} icon={Calendar} status="neutral" />
            <KPICard title="Con Error" value={0} icon={XCircle} status="success" />
            <KPICard title="Último Éxito" value={jobs?.timestamp ? new Date(jobs.timestamp).toLocaleTimeString('es-MX', {hour: '2-digit', minute: '2-digit'}) : '--'} icon={CheckCircle} status="success" />
            <KPICard title="Scheduler" value={jobs?.scheduler_status?.toUpperCase() || 'N/A'} icon={Cpu} status={jobs?.scheduler_status === 'running' ? 'success' : 'warning'} />
          </div>

          {/* Lista de Jobs */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle>Jobs Registrados</CardTitle>
            </CardHeader>
            <CardContent>
              {(!jobs?.jobs || jobs.jobs.length === 0) ? (
                <EstadoVacio 
                  icon={Calendar}
                  titulo="Sin jobs registrados"
                  mensaje="Configure automatizaciones en el scheduler"
                />
              ) : (
                <div className="space-y-2">
                  {jobs.jobs.map((job, idx) => (
                    <div key={job.id || job.name || `job-${idx}`} className="flex items-center justify-between p-3 bg-zinc-800/50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <Play className="w-4 h-4 text-green-400" />
                        <div>
                          <p className="font-medium text-white">{job.name || job.id}</p>
                          <p className="text-xs text-zinc-500">{job.trigger}</p>
                        </div>
                      </div>
                      {job.next_run && (
                        <div className="text-right">
                          <p className="text-xs text-zinc-500">Próxima ejecución</p>
                          <p className="text-sm text-blue-400">
                            {new Date(job.next_run).toLocaleString('es-MX')}
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ================================================================ */}
        {/* TAB 6: CAMBIOS Y DESPLIEGUES */}
        {/* ================================================================ */}
        <TabsContent value="cambios" className="mt-6 space-y-6">
          {/* KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KPICard title="Cambios Hoy" value={cambiosRecientes.filter(c => new Date(c.timestamp).toDateString() === new Date().toDateString()).length} icon={GitBranch} status="neutral" />
            <KPICard title="Últimos 7 días" value={cambiosRecientes.length} icon={Calendar} status="neutral" />
            <KPICard title="Deploys" value={cambiosRecientes.filter(c => c.tipo === 'deploy').length} icon={ExternalLink} status="neutral" />
            <KPICard title="Hotfixes" value={cambiosRecientes.filter(c => c.tipo === 'hotfix').length} icon={Zap} status={cambiosRecientes.filter(c => c.tipo === 'hotfix').length > 0 ? 'warning' : 'success'} />
          </div>

          {/* Lista de Cambios */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle>Cambios Recientes</CardTitle>
              <CardDescription>Deploys, hotfixes y cambios de configuración</CardDescription>
            </CardHeader>
            <CardContent>
              {cambiosRecientes.length === 0 ? (
                <EstadoVacio 
                  icon={GitBranch}
                  titulo="Sin cambios recientes"
                  mensaje="Los cambios se registrarán aquí automáticamente"
                />
              ) : (
                <div className="space-y-3">
                  {cambiosRecientes.map((cambio, idx) => {
                    const tipoConfig = {
                      deploy: { bg: 'bg-cyan-500/10', border: 'border-cyan-500/30', icon: '🚀' },
                      hotfix: { bg: 'bg-orange-500/10', border: 'border-orange-500/30', icon: '🩹' },
                      cambio_codigo: { bg: 'bg-blue-500/10', border: 'border-blue-500/30', icon: '📝' },
                      config: { bg: 'bg-purple-500/10', border: 'border-purple-500/30', icon: '⚙️' }
                    };
                    const cfg = tipoConfig[cambio.tipo] || tipoConfig.cambio_codigo;
                    
                    return (
                      <div key={cambio.id || `regresion-${idx}`} className={`p-4 rounded-lg ${cfg.bg} border ${cfg.border}`}>
                        <div className="flex items-start gap-3">
                          <span className="text-xl">{cfg.icon}</span>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <Badge variant="outline" className="text-xs">{cambio.tipo}</Badge>
                              <Badge variant="outline" className="text-xs">{cambio.modulo}</Badge>
                            </div>
                            <p className="text-sm text-white">{cambio.descripcion}</p>
                            {cambio.impacto && (
                              <p className="text-xs text-zinc-400 mt-1">Impacto: {cambio.impacto}</p>
                            )}
                            <p className="text-xs text-zinc-500 mt-2">
                              {cambio.autor} • {new Date(cambio.timestamp).toLocaleString('es-MX')}
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ================================================================ */}
        {/* TAB 7: BITÁCORA / HISTORIAL */}
        {/* ================================================================ */}
        <TabsContent value="bitacora" className="mt-6 space-y-6">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle>Bitácora del Sistema</CardTitle>
              <CardDescription>Historial completo de eventos</CardDescription>
            </CardHeader>
            <CardContent>
              {historial.length === 0 ? (
                <EstadoVacio 
                  icon={FileText}
                  titulo="Sin eventos registrados"
                  mensaje="Los eventos del sistema aparecerán aquí"
                />
              ) : (
                <div className="divide-y divide-zinc-800">
                  {historial.map((evento, idx) => (
                    <EventoRow key={evento.id || evento.timestamp || `hist-${idx}`} evento={evento} />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ================================================================ */}
        {/* TAB: NOTIFICACIONES - GESTIÓN DE DESTINATARIOS */}
        {/* ================================================================ */}
        <TabsContent value="notificaciones" className="mt-6 space-y-6">
          {/* Estado de Canales */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Email Status */}
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${notificacionesConfig?.servicios?.email?.config?.configured ? 'bg-green-500' : 'bg-yellow-500'}`} />
                    <span className="font-medium text-white">Email (SMTP)</span>
                  </div>
                  <Badge variant={notificacionesConfig?.servicios?.email?.config?.enabled ? 'success' : 'secondary'}>
                    {notificacionesConfig?.servicios?.email?.config?.enabled ? 'Habilitado' : 'Deshabilitado'}
                  </Badge>
                </div>
                <p className="text-xs text-zinc-400 mb-2">
                  Host: {notificacionesConfig?.servicios?.email?.config?.smtp_host || 'No configurado'}
                </p>
                <p className="text-xs text-zinc-500">
                  Destinatarios: {destinatarios.filter(d => d.tipo === 'email' && d.activo).length}
                </p>
                <Button 
                  size="sm" 
                  variant="outline" 
                  className="mt-3 w-full text-xs"
                  onClick={enviarPruebaEmail}
                  disabled={destinatarios.filter(d => d.tipo === 'email' && d.activo).length === 0}
                >
                  Enviar Email de Prueba
                </Button>
              </CardContent>
            </Card>

            {/* WhatsApp Status */}
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${notificacionesConfig?.servicios?.whatsapp?.config?.twilio_configured ? 'bg-green-500' : 'bg-red-500'}`} />
                    <span className="font-medium text-white">WhatsApp (Twilio)</span>
                  </div>
                  <Badge variant={notificacionesConfig?.servicios?.whatsapp?.config?.enabled ? 'success' : 'secondary'}>
                    {notificacionesConfig?.servicios?.whatsapp?.config?.enabled ? 'Habilitado' : 'Deshabilitado'}
                  </Badge>
                </div>
                <p className="text-xs text-zinc-400 mb-2">
                  Desde: {notificacionesConfig?.servicios?.whatsapp?.config?.from_number || 'No configurado'}
                </p>
                <p className="text-xs text-zinc-500">
                  Destinatarios: {destinatarios.filter(d => d.tipo === 'whatsapp' && d.activo).length}
                </p>
                <Button 
                  size="sm" 
                  variant="outline" 
                  className="mt-3 w-full text-xs"
                  onClick={enviarPruebaWhatsApp}
                  disabled={destinatarios.filter(d => d.tipo === 'whatsapp' && d.activo).length === 0}
                >
                  Enviar WhatsApp de Prueba
                </Button>
              </CardContent>
            </Card>

            {/* WebSocket Status */}
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${wsConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                    <span className="font-medium text-white">WebSocket (Tiempo Real)</span>
                  </div>
                  <Badge variant={wsConnected ? 'success' : 'destructive'}>
                    {wsConnected ? 'Conectado' : 'Desconectado'}
                  </Badge>
                </div>
                <p className="text-xs text-zinc-400 mb-2">
                  Estado: {wsStatus}
                </p>
                <p className="text-xs text-zinc-500">
                  Conexiones activas: {notificacionesConfig?.servicios?.websocket?.config?.connections || 0}
                </p>
                {!wsConnected && (
                  <Button 
                    size="sm" 
                    variant="outline" 
                    className="mt-3 w-full text-xs"
                    onClick={reconnect}
                  >
                    Reconectar
                  </Button>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Agregar Destinatario */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="w-5 h-5 text-blue-400" />
                Agregar Destinatario de Alertas
              </CardTitle>
              <CardDescription>
                Los destinatarios recibirán notificaciones automáticas cuando se detecten alertas críticas
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col sm:flex-row gap-3">
                <select
                  value={nuevoDestinatario.tipo}
                  onChange={(e) => setNuevoDestinatario(prev => ({ ...prev, tipo: e.target.value }))}
                  className="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm"
                >
                  <option value="email">Email</option>
                  <option value="whatsapp">WhatsApp</option>
                </select>
                <input
                  type={nuevoDestinatario.tipo === 'email' ? 'email' : 'tel'}
                  placeholder={nuevoDestinatario.tipo === 'email' ? 'correo@ejemplo.com' : '+521234567890'}
                  value={nuevoDestinatario.destinatario}
                  onChange={(e) => setNuevoDestinatario(prev => ({ ...prev, destinatario: e.target.value }))}
                  className="flex-1 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm placeholder-zinc-500"
                />
                <input
                  type="text"
                  placeholder="Nombre (opcional)"
                  value={nuevoDestinatario.nombre}
                  onChange={(e) => setNuevoDestinatario(prev => ({ ...prev, nombre: e.target.value }))}
                  className="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm placeholder-zinc-500"
                />
                <Button onClick={agregarDestinatario} className="bg-blue-600 hover:bg-blue-700">
                  Agregar
                </Button>
              </div>
              {nuevoDestinatario.tipo === 'whatsapp' && (
                <p className="mt-2 text-xs text-yellow-500">
                  Para WhatsApp Sandbox: El destinatario debe enviar primero "join &lt;keyword&gt;" al +1 (415) 523-8886
                </p>
              )}
            </CardContent>
          </Card>

          {/* Lista de Destinatarios */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Destinatarios Configurados</CardTitle>
                <CardDescription>
                  {destinatarios.length} destinatario(s) en total
                </CardDescription>
              </div>
              <Button size="sm" variant="outline" onClick={() => { fetchDestinatarios(); fetchNotificacionesConfig(); }}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Actualizar
              </Button>
            </CardHeader>
            <CardContent>
              {loadingDestinatarios ? (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="w-6 h-6 animate-spin text-zinc-500" />
                </div>
              ) : destinatarios.length === 0 ? (
                <div className="text-center py-8 text-zinc-500">
                  <Bell className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>No hay destinatarios configurados</p>
                  <p className="text-sm mt-1">Agregue un email o número de WhatsApp arriba</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {/* Email Recipients */}
                  {destinatarios.filter(d => d.tipo === 'email').length > 0 && (
                    <>
                      <h4 className="text-sm font-medium text-zinc-400 mb-2 flex items-center gap-2">
                        <span className="w-2 h-2 bg-blue-500 rounded-full" />
                        Email ({destinatarios.filter(d => d.tipo === 'email').length})
                      </h4>
                      {destinatarios.filter(d => d.tipo === 'email').map((dest) => (
                        <div 
                          key={dest.id} 
                          className={`flex items-center justify-between p-3 rounded-lg border ${
                            dest.activo 
                              ? 'bg-zinc-800/50 border-zinc-700' 
                              : 'bg-zinc-900/30 border-zinc-800 opacity-60'
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <div className={`w-2 h-2 rounded-full ${dest.activo ? 'bg-green-500' : 'bg-zinc-600'}`} />
                            <div>
                              <p className="text-sm text-white">{dest.destinatario}</p>
                              {dest.nombre && <p className="text-xs text-zinc-500">{dest.nombre}</p>}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => toggleDestinatarioActivo(dest.id, dest.activo)}
                              className="text-xs"
                            >
                              {dest.activo ? 'Desactivar' : 'Activar'}
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => eliminarDestinatario(dest.id)}
                              className="text-red-400 hover:text-red-300 text-xs"
                            >
                              Eliminar
                            </Button>
                          </div>
                        </div>
                      ))}
                    </>
                  )}

                  {/* WhatsApp Recipients */}
                  {destinatarios.filter(d => d.tipo === 'whatsapp').length > 0 && (
                    <>
                      <h4 className="text-sm font-medium text-zinc-400 mt-4 mb-2 flex items-center gap-2">
                        <span className="w-2 h-2 bg-green-500 rounded-full" />
                        WhatsApp ({destinatarios.filter(d => d.tipo === 'whatsapp').length})
                      </h4>
                      {destinatarios.filter(d => d.tipo === 'whatsapp').map((dest) => (
                        <div 
                          key={dest.id} 
                          className={`flex items-center justify-between p-3 rounded-lg border ${
                            dest.activo 
                              ? 'bg-zinc-800/50 border-zinc-700' 
                              : 'bg-zinc-900/30 border-zinc-800 opacity-60'
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <div className={`w-2 h-2 rounded-full ${dest.activo ? 'bg-green-500' : 'bg-zinc-600'}`} />
                            <div>
                              <p className="text-sm text-white">{dest.destinatario}</p>
                              {dest.nombre && <p className="text-xs text-zinc-500">{dest.nombre}</p>}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => toggleDestinatarioActivo(dest.id, dest.activo)}
                              className="text-xs"
                            >
                              {dest.activo ? 'Desactivar' : 'Activar'}
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => eliminarDestinatario(dest.id)}
                              className="text-red-400 hover:text-red-300 text-xs"
                            >
                              Eliminar
                            </Button>
                          </div>
                        </div>
                      ))}
                    </>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Info sobre Flujo de Alertas */}
          <Card className="bg-blue-500/10 border-blue-500/30">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-medium text-white mb-1">Flujo de Alertas Críticas</h4>
                  <p className="text-sm text-zinc-300">
                    Cuando se detecta una alerta con severidad <strong className="text-red-400">CRITICAL</strong>, 
                    el sistema notifica automáticamente por todos los canales configurados:
                  </p>
                  <ul className="mt-2 text-sm text-zinc-400 list-disc list-inside space-y-1">
                    <li>WebSocket: Notificación instantánea en el dashboard</li>
                    <li>Email: Correo a todos los destinatarios de email activos</li>
                    <li>WhatsApp: Mensaje a todos los números de WhatsApp activos</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ================================================================ */}
        {/* TAB 8: CONFIGURACIÓN Y BLINDAJE */}
        {/* ================================================================ */}
        <TabsContent value="blindaje" className="mt-6 space-y-6">
          {/* Módulos Blindados */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-blue-400" />
                Módulos Blindados
              </CardTitle>
              <CardDescription>Módulos congelados funcionalmente - cambios requieren autorización</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {modulosBlindados.length === 0 && (
                <EstadoVacio
                  icon={Lock}
                  titulo="Sin catálogo SQL canónico de blindaje"
                  descripcion={blindajeStatus === 'NO_CANONICAL_SQL_REGISTRY' ? 'No se muestran datos simulados. Falta registrar el catálogo canónico en SQL.' : 'No hay módulos de blindaje disponibles.'}
                />
              )}
              {modulosBlindados.map((modulo, idx) => (
                <div key={modulo.nombre || `blindado-${idx}`} className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Lock className="w-5 h-5 text-blue-400" />
                      <span className="font-semibold text-white">{modulo.nombre}</span>
                    </div>
                    <Badge variant="outline" className="border-blue-500/50 text-blue-400">BLINDADO</Badge>
                  </div>
                  <p className="text-xs text-zinc-400">Fecha de cierre: {modulo.fecha_cierre}</p>
                  <p className="text-xs text-zinc-500">Documento: {modulo.documento}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Protocolo Global */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle>Protocolo Global de Cambios</CardTitle>
              <CardDescription>Checklist obligatorio antes de cualquier cambio</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { paso: '1. Snapshot', desc: 'Crear respaldo del estado actual' },
                  { paso: '2. Documentación', desc: 'Registrar qué se va a cambiar y por qué' },
                  { paso: '3. Aislamiento', desc: 'Implementar cambios en entorno aislado' },
                  { paso: '4. Pruebas', desc: 'Ejecutar pruebas de regresión' },
                  { paso: '5. Validación', desc: 'Verificar con datos reales' },
                  { paso: '6. Autorización', desc: 'Obtener aprobación explícita' },
                  { paso: '7. Monitoreo', desc: 'Vigilar sistema 24h después del cambio' }
                ].map((item, idx) => (
                  <div key={`paso-${idx}`} className="flex items-start gap-3 p-3 bg-zinc-800/50 rounded-lg">
                    <div className="w-6 h-6 rounded-full bg-zinc-700 flex items-center justify-center text-xs text-zinc-400">
                      {idx + 1}
                    </div>
                    <div>
                      <p className="font-medium text-white">{item.paso}</p>
                      <p className="text-xs text-zinc-400">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Documentos Vinculados */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle>Documentos de Referencia</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {[
                  'CIERRE_Y_BLINDAJE_TABLERO_EJECUTIVO.md',
                  'CIERRE_Y_BLINDAJE_AUDITORIA_COMPRAS.md',
                  'CIERRE_Y_BLINDAJE_OPERACIONES_ANALISIS.md',
                  'PROTOCOLO_GLOBAL_CAMBIOS_EDARSA.md',
                  'ARQUITECTURA_CONEXIONES_RESOLVER.md',
                  'CENTRO_CONTROL_EDARSA.md',
                  'CENTRO_DE_CONTROL_EDARSA_WIREFRAME.md'
                ].map((doc, idx) => (
                  <div key={`doc-${doc}`} className="flex items-center gap-2 p-2 hover:bg-zinc-800/50 rounded">
                    <FileText className="w-4 h-4 text-zinc-500" />
                    <span className="text-sm text-zinc-300">{doc}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CentroControl;
