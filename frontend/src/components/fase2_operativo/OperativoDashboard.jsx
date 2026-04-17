/**
 * OperativoDashboard.jsx - Contenedor Principal del Dashboard Operativo
 * CAB-003 | Fase 2A - Subfase 2A.8
 * EDARSA HUB
 * 
 * Centraliza filtros y orquesta los componentes hijos.
 * Consume únicamente operativoApi.js para llamadas HTTP.
 */

import { useState, useEffect, useCallback } from 'react';
import { 
  RefreshCw, 
  Search, 
  Filter, 
  X,
  Activity
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import KPICards from './KPICards';
import SLACard from './SLACard';
import ResponsabilidadCard from './ResponsabilidadCard';
import ResponsabilidadPendientesPanel from './ResponsabilidadPendientesPanel';
import AlertasBanner from './AlertasBanner';
import WorkflowList from './WorkflowList';
import TareaList from './TareaList';
import {
  getDashboardResumen,
  getDashboardAlertas,
  getWorkflows,
  getTareas,
} from '@/services/operativoApi';

const OperativoDashboard = () => {
  // ============================================
  // ESTADOS
  // ============================================
  
  // Datos
  const [resumen, setResumen] = useState(null);
  const [alertas, setAlertas] = useState([]);
  const [workflows, setWorkflows] = useState([]);
  const [tareas, setTareas] = useState([]);
  
  // Estados de carga
  const [loadingResumen, setLoadingResumen] = useState(true);
  const [loadingAlertas, setLoadingAlertas] = useState(true);
  const [loadingWorkflows, setLoadingWorkflows] = useState(true);
  const [loadingTareas, setLoadingTareas] = useState(true);
  
  // Errores
  const [errorResumen, setErrorResumen] = useState(null);
  const [errorAlertas, setErrorAlertas] = useState(null);
  const [errorWorkflows, setErrorWorkflows] = useState(null);
  const [errorTareas, setErrorTareas] = useState(null);
  
  // Filtros
  const [filtros, setFiltros] = useState({
    busquedaId: '',
    estadoWorkflow: '',
    usuarioAsignado: '',
    soloVencidas: false,
  });
  
  const [mostrarFiltros, setMostrarFiltros] = useState(false);
  const [ultimaActualizacion, setUltimaActualizacion] = useState(null);

  // ============================================
  // FUNCIONES DE CARGA
  // ============================================

  const cargarResumen = useCallback(async () => {
    setLoadingResumen(true);
    setErrorResumen(null);
    try {
      const data = await getDashboardResumen();
      setResumen(data);
    } catch (err) {
      setErrorResumen(err.message || 'Error desconocido');
    } finally {
      setLoadingResumen(false);
    }
  }, []);

  const cargarAlertas = useCallback(async () => {
    setLoadingAlertas(true);
    setErrorAlertas(null);
    try {
      const data = await getDashboardAlertas();
      setAlertas(Array.isArray(data) ? data : data.alertas || []);
    } catch (err) {
      setErrorAlertas(err.message || 'Error desconocido');
    } finally {
      setLoadingAlertas(false);
    }
  }, []);

  const cargarWorkflows = useCallback(async () => {
    setLoadingWorkflows(true);
    setErrorWorkflows(null);
    try {
      const params = {};
      if (filtros.estadoWorkflow) params.estado = filtros.estadoWorkflow;
      if (filtros.busquedaId) params.procesado_id = filtros.busquedaId;
      params.limit = 50;
      
      const data = await getWorkflows(params);
      setWorkflows(Array.isArray(data) ? data : data.items || data.workflows || []);
    } catch (err) {
      setErrorWorkflows(err.message || 'Error desconocido');
    } finally {
      setLoadingWorkflows(false);
    }
  }, [filtros.estadoWorkflow, filtros.busquedaId]);

  const cargarTareas = useCallback(async () => {
    setLoadingTareas(true);
    setErrorTareas(null);
    try {
      const params = {};
      if (filtros.usuarioAsignado) params.usuario_id = filtros.usuarioAsignado;
      if (filtros.soloVencidas) params.vencidas = true;
      params.limit = 50;
      
      const data = await getTareas(params);
      setTareas(Array.isArray(data) ? data : data.items || data.tareas || []);
    } catch (err) {
      setErrorTareas(err.message || 'Error desconocido');
    } finally {
      setLoadingTareas(false);
    }
  }, [filtros.usuarioAsignado, filtros.soloVencidas]);

  const cargarTodo = useCallback(async () => {
    await Promise.all([
      cargarResumen(),
      cargarAlertas(),
      cargarWorkflows(),
      cargarTareas(),
    ]);
    setUltimaActualizacion(new Date());
  }, [cargarResumen, cargarAlertas, cargarWorkflows, cargarTareas]);

  // ============================================
  // EFECTOS
  // ============================================

  // Carga inicial
  useEffect(() => {
    cargarTodo();
  }, []);

  // Recargar workflows y tareas cuando cambien filtros
  useEffect(() => {
    cargarWorkflows();
  }, [cargarWorkflows]);

  useEffect(() => {
    cargarTareas();
  }, [cargarTareas]);

  // ============================================
  // HANDLERS
  // ============================================

  const handleFiltroChange = (campo, valor) => {
    setFiltros(prev => ({ ...prev, [campo]: valor }));
  };

  const limpiarFiltros = () => {
    setFiltros({
      busquedaId: '',
      estadoWorkflow: '',
      usuarioAsignado: '',
      soloVencidas: false,
    });
  };

  const hayFiltrosActivos = 
    filtros.busquedaId || 
    filtros.estadoWorkflow || 
    filtros.usuarioAsignado || 
    filtros.soloVencidas;

  // ============================================
  // RENDER
  // ============================================

  return (
    <div className="space-y-6" data-testid="operativo-dashboard">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900 flex items-center gap-2">
            <Activity className="h-7 w-7 text-blue-600" />
            Dashboard Operativo
          </h1>
          <p className="text-sm text-zinc-500 mt-1">
            CAB-003 | Gestión de Inventarios - Fase 2A
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          {ultimaActualizacion && (
            <span className="text-xs text-zinc-400">
              Actualizado: {ultimaActualizacion.toLocaleTimeString('es-MX')}
            </span>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setMostrarFiltros(!mostrarFiltros)}
            className={hayFiltrosActivos ? 'border-blue-300 bg-blue-50' : ''}
            data-testid="toggle-filtros"
          >
            <Filter className="h-4 w-4 mr-1" />
            Filtros
            {hayFiltrosActivos && (
              <span className="ml-1 px-1.5 py-0.5 bg-blue-500 text-white text-xs rounded-full">
                !
              </span>
            )}
          </Button>
          <Button
            variant="default"
            size="sm"
            onClick={cargarTodo}
            disabled={loadingResumen || loadingAlertas || loadingWorkflows || loadingTareas}
            data-testid="refresh-all"
          >
            <RefreshCw className={`h-4 w-4 mr-1 ${loadingResumen ? 'animate-spin' : ''}`} />
            Actualizar
          </Button>
        </div>
      </div>

      {/* Panel de Filtros */}
      {mostrarFiltros && (
        <div 
          className="rounded-lg border border-zinc-200 bg-white p-4 space-y-4"
          data-testid="filtros-panel"
        >
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-zinc-700">Filtros</h3>
            {hayFiltrosActivos && (
              <button
                onClick={limpiarFiltros}
                className="text-sm text-red-600 hover:text-red-800 flex items-center gap-1"
                data-testid="limpiar-filtros"
              >
                <X className="h-3 w-3" />
                Limpiar
              </button>
            )}
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Búsqueda por ID */}
            <div>
              <label className="text-xs font-medium text-zinc-600 mb-1 block">
                Buscar por ID
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
                <Input
                  type="text"
                  placeholder="ID workflow o procesado..."
                  value={filtros.busquedaId}
                  onChange={(e) => handleFiltroChange('busquedaId', e.target.value)}
                  className="pl-9"
                  data-testid="filtro-busqueda-id"
                />
              </div>
            </div>

            {/* Estado Workflow */}
            <div>
              <label className="text-xs font-medium text-zinc-600 mb-1 block">
                Estado Workflow
              </label>
              <select
                value={filtros.estadoWorkflow}
                onChange={(e) => handleFiltroChange('estadoWorkflow', e.target.value)}
                className="w-full h-10 px-3 rounded-md border border-zinc-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                data-testid="filtro-estado-workflow"
              >
                <option value="">Todos</option>
                <option value="pendiente">Pendiente</option>
                <option value="en_proceso">En Proceso</option>
                <option value="en_revision">En Revisión</option>
                <option value="completado">Completado</option>
                <option value="escalado">Escalado</option>
                <option value="cancelado">Cancelado</option>
              </select>
            </div>

            {/* Usuario Asignado */}
            <div>
              <label className="text-xs font-medium text-zinc-600 mb-1 block">
                Usuario Asignado
              </label>
              <Input
                type="text"
                placeholder="ID de usuario..."
                value={filtros.usuarioAsignado}
                onChange={(e) => handleFiltroChange('usuarioAsignado', e.target.value)}
                data-testid="filtro-usuario-asignado"
              />
            </div>

            {/* Solo Vencidas */}
            <div className="flex items-end">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filtros.soloVencidas}
                  onChange={(e) => handleFiltroChange('soloVencidas', e.target.checked)}
                  className="h-4 w-4 rounded border-zinc-300 text-blue-600 focus:ring-blue-500"
                  data-testid="filtro-solo-vencidas"
                />
                <span className="text-sm text-zinc-700">Solo tareas vencidas</span>
              </label>
            </div>
          </div>
        </div>
      )}

      {/* KPIs y SLA */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-3">
          <KPICards 
            data={resumen} 
            loading={loadingResumen} 
            error={errorResumen} 
          />
        </div>
        <div className="lg:col-span-1">
          <SLACard />
        </div>
      </div>

      {/* Responsabilidad Económica - Fase 2C.1 y 2C.2 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-1">
          <ResponsabilidadCard />
        </div>
        <div className="lg:col-span-1">
          <ResponsabilidadPendientesPanel />
        </div>
        <div className="lg:col-span-1">
          {/* Alertas */}
          <AlertasBanner 
            alertas={alertas}
            loading={loadingAlertas}
            error={errorAlertas}
            onRefresh={cargarAlertas}
          />
        </div>
      </div>

      {/* Grid de Workflows y Tareas */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <WorkflowList 
          workflows={workflows}
          loading={loadingWorkflows}
          error={errorWorkflows}
          onRefresh={cargarWorkflows}
          emptyMessage={
            hayFiltrosActivos 
              ? 'No hay workflows que coincidan con los filtros' 
              : 'No hay workflows disponibles'
          }
        />
        
        <TareaList 
          tareas={tareas}
          loading={loadingTareas}
          error={errorTareas}
          onRefresh={cargarTareas}
          emptyMessage={
            hayFiltrosActivos 
              ? 'No hay tareas que coincidan con los filtros' 
              : 'No hay tareas disponibles'
          }
        />
      </div>
    </div>
  );
};

export default OperativoDashboard;
