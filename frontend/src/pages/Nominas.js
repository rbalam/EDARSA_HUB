import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { 
  DollarSign, Calendar, Users, Clock, CheckCircle2, XCircle, 
  AlertTriangle, RefreshCw, Plus, ChevronRight, Eye, Edit,
  FileText, Settings, Bell, ArrowRight, RotateCcw, Layers,
  Building2, UserCheck, Wallet, FileSpreadsheet, Upload,
  Send, Check, X, Lock, History, Filter, Play, Pause,
  Timer, Target, TrendingUp, ClipboardList
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Etapas del flujo de nómina
const ETAPAS_NOMINA = [
  { id: 'headcount', nombre: 'Headcount', icon: Users, color: 'bg-blue-500', responsable: 'Gerencia' },
  { id: 'incidencias', nombre: 'Incidencias', icon: ClipboardList, color: 'bg-purple-500', responsable: 'Gerencia' },
  { id: 'validacion_rh', nombre: 'Validación RH', icon: UserCheck, color: 'bg-amber-500', responsable: 'RH' },
  { id: 'maquilador', nombre: 'Maquilador', icon: FileSpreadsheet, color: 'bg-cyan-500', responsable: 'Maquilador' },
  { id: 'autorizacion', nombre: 'Autorización', icon: CheckCircle2, color: 'bg-green-500', responsable: 'Gerencia' },
  { id: 'tesoreria', nombre: 'Tesorería', icon: Wallet, color: 'bg-emerald-500', responsable: 'Tesorería' },
  { id: 'pagada', nombre: 'Pagada', icon: DollarSign, color: 'bg-zinc-500', responsable: 'Sistema' }
];

const ROLES_RESPONSABLES = {
  'Gerencia': ['Administrador', 'Supervisor'],
  'RH': ['Administrador', 'Supervisor'],
  'Maquilador': ['Administrador', 'Supervisor', 'Maquilador'],
  'Tesorería': ['Administrador', 'Tesoreria'],
  'Sistema': ['Administrador']
};

export default function Nominas() {
  const [activeTab, setActiveTab] = useState('kanban');
  const [loading, setLoading] = useState(true);
  const [ciclos, setCiclos] = useState([]);
  const [configuracion, setConfiguracion] = useState(null);
  const [sucursales, setSucursales] = useState([]);
  const [movimientos, setMovimientos] = useState([]);
  const [kpis, setKpis] = useState([]);
  
  // Filtros
  const [filtroSucursal, setFiltroSucursal] = useState('');
  const [filtroPeriodo, setFiltroPeriodo] = useState('actual');
  
  // Modales
  const [modalNuevoCiclo, setModalNuevoCiclo] = useState(false);
  const [modalDetalleCiclo, setModalDetalleCiclo] = useState(false);
  const [modalMovimientos, setModalMovimientos] = useState(false);
  const [modalConfiguracion, setModalConfiguracion] = useState(false);
  const [modalAprobar, setModalAprobar] = useState(false);
  const [modalRechazar, setModalRechazar] = useState(false);
  const [modalHistorial, setModalHistorial] = useState(false);
  const [modalSubirArchivo, setModalSubirArchivo] = useState(false);
  const [modalKPIs, setModalKPIs] = useState(false);
  
  const [cicloSeleccionado, setCicloSeleccionado] = useState(null);
  const [historialCiclo, setHistorialCiclo] = useState([]);
  const [savingForm, setSavingForm] = useState(false);
  
  // Forms
  const [formNuevoCiclo, setFormNuevoCiclo] = useState({
    sucursal_id: '',
    fecha_corte: '',
    tipo_nomina: 'quincenal',
    notas: ''
  });
  
  const [formConfiguracion, setFormConfiguracion] = useState({
    dia_corte: 0, // 0 = Domingo
    dias_inhabiles: [],
    horario_headcount: '10:00',
    horario_autorizacion: '11:00',
    horario_maquilador: '12:00',
    horario_tesoreria: '14:00',
    dia_pago: 1 // 1 = Lunes
  });
  
  const [passwordAprobacion, setPasswordAprobacion] = useState('');
  const [comentarioAprobacion, setComentarioAprobacion] = useState('');
  const [motivoRechazo, setMotivoRechazo] = useState('');
  
  // Form movimientos
  const [formMovimiento, setFormMovimiento] = useState({
    colaborador_id: '',
    tipo_incidencia: '',
    monto: 0,
    unidades: 0,
    notas: ''
  });
  
  const token = localStorage.getItem('token');
  const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
  const isAdmin = currentUser?.role === 'Administrador';
  const isSupervisor = currentUser?.role === 'Supervisor';
  const userRole = currentUser?.role;
  
  const fetchWithAuth = useCallback(async (url) => {
    const response = await fetch(`${API_URL}${url}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error('Error en petición');
    return response.json();
  }, [token]);
  
  // Cargar datos
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [ciclosData, configData, sucursalesData] = await Promise.all([
        fetchWithAuth('/api/nomina/ciclos'),
        fetchWithAuth('/api/nomina/configuracion'),
        fetchWithAuth('/api/rrhh/catalogos/sucursales')
      ]);
      
      setCiclos(ciclosData.ciclos || []);
      setConfiguracion(configData.configuracion);
      setSucursales(sucursalesData.sucursales || []);
      
      if (configData.configuracion) {
        setFormConfiguracion({
          dia_corte: configData.configuracion.dia_corte || 0,
          dias_inhabiles: configData.configuracion.dias_inhabiles || [],
          horario_headcount: configData.configuracion.horario_headcount || '10:00',
          horario_autorizacion: configData.configuracion.horario_autorizacion || '11:00',
          horario_maquilador: configData.configuracion.horario_maquilador || '12:00',
          horario_tesoreria: configData.configuracion.horario_tesoreria || '14:00',
          dia_pago: configData.configuracion.dia_pago || 1
        });
      }
    } catch (error) {
      console.error('Error cargando datos:', error);
      toast.error('Error cargando datos de nómina');
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth]);
  
  useEffect(() => {
    loadData();
  }, [loadData]);
  
  // Verificar si el usuario puede actuar en una etapa
  const puedeActuarEnEtapa = (etapa) => {
    const rolesPermitidos = ROLES_RESPONSABLES[etapa.responsable] || [];
    return rolesPermitidos.includes(userRole);
  };
  
  // Obtener ciclos por etapa
  const getCiclosPorEtapa = (etapaId) => {
    return ciclos.filter(c => c.etapa_actual === etapaId);
  };
  
  // Calcular tiempo restante
  const calcularTiempoRestante = (ciclo) => {
    if (!ciclo.deadline_actual) return null;
    const deadline = new Date(ciclo.deadline_actual);
    const ahora = new Date();
    const diff = deadline - ahora;
    
    if (diff < 0) return { texto: 'Vencido', color: 'text-red-600', vencido: true };
    
    const horas = Math.floor(diff / (1000 * 60 * 60));
    const minutos = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (horas < 2) return { texto: `${horas}h ${minutos}m`, color: 'text-red-500', vencido: false };
    if (horas < 6) return { texto: `${horas}h ${minutos}m`, color: 'text-amber-500', vencido: false };
    return { texto: `${horas}h ${minutos}m`, color: 'text-green-500', vencido: false };
  };
  
  // Crear nuevo ciclo de nómina
  const handleCrearCiclo = async () => {
    if (!formNuevoCiclo.sucursal_id || !formNuevoCiclo.fecha_corte) {
      toast.error('Complete todos los campos requeridos');
      return;
    }
    
    setSavingForm(true);
    try {
      const response = await fetch(`${API_URL}/api/nomina/ciclos`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formNuevoCiclo)
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al crear ciclo');
      }
      
      toast.success('Ciclo de nómina creado correctamente');
      setModalNuevoCiclo(false);
      setFormNuevoCiclo({ sucursal_id: '', fecha_corte: '', tipo_nomina: 'quincenal', notas: '' });
      loadData();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setSavingForm(false);
    }
  };
  
  // Avanzar etapa
  const handleAvanzarEtapa = async (ciclo) => {
    setCicloSeleccionado(ciclo);
    setPasswordAprobacion('');
    setComentarioAprobacion('');
    setModalAprobar(true);
  };
  
  // Confirmar avance
  const handleConfirmarAvance = async () => {
    if (!passwordAprobacion) {
      toast.error('Ingrese su contraseña para autorizar');
      return;
    }
    
    setSavingForm(true);
    try {
      const response = await fetch(`${API_URL}/api/nomina/ciclos/${cicloSeleccionado.id}/avanzar`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          password: passwordAprobacion, 
          comentario: comentarioAprobacion 
        })
      });
      
      if (response.status === 401) {
        toast.error('Contraseña incorrecta');
        return;
      }
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al avanzar etapa');
      }
      
      const data = await response.json();
      toast.success(data.message || 'Etapa avanzada correctamente');
      setModalAprobar(false);
      loadData();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setSavingForm(false);
    }
  };
  
  // Rechazar/Devolver
  const handleRechazar = async () => {
    if (!motivoRechazo) {
      toast.error('Ingrese el motivo del rechazo');
      return;
    }
    
    setSavingForm(true);
    try {
      const response = await fetch(`${API_URL}/api/nomina/ciclos/${cicloSeleccionado.id}/rechazar`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ motivo: motivoRechazo })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al rechazar');
      }
      
      toast.success('Nómina devuelta para corrección');
      setModalRechazar(false);
      setMotivoRechazo('');
      loadData();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setSavingForm(false);
    }
  };
  
  // Ver historial
  const handleVerHistorial = async (ciclo) => {
    setCicloSeleccionado(ciclo);
    setHistorialCiclo(ciclo.historial || []);
    setModalHistorial(true);
  };
  
  // Guardar configuración
  const handleGuardarConfiguracion = async () => {
    setSavingForm(true);
    try {
      const response = await fetch(`${API_URL}/api/nomina/configuracion`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formConfiguracion)
      });
      
      if (!response.ok) throw new Error('Error al guardar configuración');
      
      toast.success('Configuración guardada correctamente');
      setModalConfiguracion(false);
      loadData();
    } catch (error) {
      toast.error('Error al guardar configuración');
    } finally {
      setSavingForm(false);
    }
  };
  
  // Cargar movimientos de un ciclo
  const handleVerMovimientos = async (ciclo) => {
    setCicloSeleccionado(ciclo);
    try {
      const data = await fetchWithAuth(`/api/nomina/ciclos/${ciclo.id}/movimientos`);
      setMovimientos(data.movimientos || []);
      setModalMovimientos(true);
    } catch (error) {
      toast.error('Error cargando movimientos');
    }
  };
  
  // Agregar movimiento
  const handleAgregarMovimiento = async () => {
    if (!formMovimiento.colaborador_id || !formMovimiento.tipo_incidencia) {
      toast.error('Complete los campos requeridos');
      return;
    }
    
    setSavingForm(true);
    try {
      const response = await fetch(`${API_URL}/api/nomina/ciclos/${cicloSeleccionado.id}/movimientos`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formMovimiento)
      });
      
      if (!response.ok) throw new Error('Error al agregar movimiento');
      
      toast.success('Movimiento agregado');
      setFormMovimiento({ colaborador_id: '', tipo_incidencia: '', monto: 0, unidades: 0, notas: '' });
      
      // Recargar movimientos
      const data = await fetchWithAuth(`/api/nomina/ciclos/${cicloSeleccionado.id}/movimientos`);
      setMovimientos(data.movimientos || []);
    } catch (error) {
      toast.error('Error al agregar movimiento');
    } finally {
      setSavingForm(false);
    }
  };
  
  // Tabs
  const tabs = [
    { id: 'kanban', nombre: 'Tablero Kanban', icon: Layers },
    { id: 'lista', nombre: 'Lista de Ciclos', icon: ClipboardList },
    { id: 'configuracion', nombre: 'Configuración', icon: Settings, adminOnly: true }
  ];
  
  const diasSemana = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="h-8 w-8 animate-spin text-zinc-400" />
      </div>
    );
  }
  
  return (
    <div className="space-y-6" data-testid="nominas-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Gestión de Nóminas</h1>
          <p className="text-zinc-500 text-sm mt-1">
            Control del ciclo completo de nómina
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={loadData}
            className="gap-2"
            data-testid="btn-refresh"
          >
            <RefreshCw className="h-4 w-4" />
            Actualizar
          </Button>
          {(isAdmin || isSupervisor) && (
            <Button
              onClick={() => setModalNuevoCiclo(true)}
              className="gap-2 bg-zinc-900 hover:bg-zinc-800"
              data-testid="btn-nuevo-ciclo"
            >
              <Plus className="h-4 w-4" />
              Nuevo Ciclo
            </Button>
          )}
        </div>
      </div>
      
      {/* Tabs */}
      <div className="border-b border-zinc-200">
        <nav className="flex gap-4">
          {tabs.filter(t => !t.adminOnly || isAdmin).map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                activeTab === tab.id 
                  ? 'border-zinc-900 text-zinc-900' 
                  : 'border-transparent text-zinc-500 hover:text-zinc-700'
              }`}
              data-testid={`tab-${tab.id}`}
            >
              <tab.icon className="h-4 w-4" />
              {tab.nombre}
            </button>
          ))}
        </nav>
      </div>
      
      {/* Tab Content */}
      {activeTab === 'kanban' && (
        <div className="space-y-4">
          {/* Filtros */}
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-zinc-400" />
              <select
                value={filtroSucursal}
                onChange={(e) => setFiltroSucursal(e.target.value)}
                className="border rounded-lg px-3 py-2 text-sm"
                data-testid="filtro-sucursal"
              >
                <option value="">Todas las sucursales</option>
                {sucursales.map(s => (
                  <option key={s.SucursalID || s.id} value={s.SucursalID || s.id}>
                    {s.Nombre || s.nombre}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-zinc-400" />
              <select
                value={filtroPeriodo}
                onChange={(e) => setFiltroPeriodo(e.target.value)}
                className="border rounded-lg px-3 py-2 text-sm"
                data-testid="filtro-periodo"
              >
                <option value="actual">Periodo Actual</option>
                <option value="anterior">Periodo Anterior</option>
                <option value="todos">Todos</option>
              </select>
            </div>
          </div>
          
          {/* Kanban Board */}
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-7 gap-4 overflow-x-auto pb-4">
            {ETAPAS_NOMINA.map(etapa => {
              const ciclosEtapa = getCiclosPorEtapa(etapa.id);
              const IconoEtapa = etapa.icon;
              
              return (
                <div 
                  key={etapa.id} 
                  className="min-w-[250px] bg-zinc-50 rounded-xl p-4"
                  data-testid={`columna-${etapa.id}`}
                >
                  {/* Header de columna */}
                  <div className="flex items-center gap-2 mb-4">
                    <div className={`p-2 rounded-lg ${etapa.color}`}>
                      <IconoEtapa className="h-4 w-4 text-white" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-zinc-900 text-sm">{etapa.nombre}</h3>
                      <p className="text-xs text-zinc-500">{etapa.responsable}</p>
                    </div>
                    <span className="bg-zinc-200 text-zinc-700 text-xs font-medium px-2 py-1 rounded-full">
                      {ciclosEtapa.length}
                    </span>
                  </div>
                  
                  {/* Cards de ciclos */}
                  <div className="space-y-3">
                    {ciclosEtapa.length === 0 ? (
                      <div className="text-center py-8 text-zinc-400 text-sm">
                        Sin nóminas
                      </div>
                    ) : (
                      ciclosEtapa.map(ciclo => {
                        const tiempoRestante = calcularTiempoRestante(ciclo);
                        const puedeActuar = puedeActuarEnEtapa(etapa);
                        
                        return (
                          <Card 
                            key={ciclo.id} 
                            className={`cursor-pointer hover:shadow-md transition-shadow ${
                              tiempoRestante?.vencido ? 'border-red-300 bg-red-50' : ''
                            }`}
                            onClick={() => {
                              setCicloSeleccionado(ciclo);
                              setModalDetalleCiclo(true);
                            }}
                            data-testid={`ciclo-card-${ciclo.id}`}
                          >
                            <CardContent className="p-3">
                              <div className="flex items-start justify-between mb-2">
                                <div>
                                  <p className="font-medium text-sm text-zinc-900">
                                    {ciclo.sucursal_nombre || 'Sucursal'}
                                  </p>
                                  <p className="text-xs text-zinc-500">
                                    {ciclo.tipo_nomina === 'quincenal' ? 'Quincenal' : 'Semanal'}
                                  </p>
                                </div>
                                {tiempoRestante && (
                                  <div className={`flex items-center gap-1 text-xs ${tiempoRestante.color}`}>
                                    <Timer className="h-3 w-3" />
                                    {tiempoRestante.texto}
                                  </div>
                                )}
                              </div>
                              
                              <div className="text-xs text-zinc-500 mb-3">
                                <div className="flex items-center gap-1">
                                  <Calendar className="h-3 w-3" />
                                  Corte: {new Date(ciclo.fecha_corte).toLocaleDateString()}
                                </div>
                              </div>
                              
                              {/* Info adicional */}
                              <div className="flex items-center justify-between text-xs">
                                <span className="text-zinc-500">
                                  {ciclo.total_colaboradores || 0} colaboradores
                                </span>
                                <span className="text-zinc-500">
                                  {ciclo.total_movimientos || 0} mov.
                                </span>
                              </div>
                              
                              {/* Acciones rápidas */}
                              {puedeActuar && etapa.id !== 'pagada' && (
                                <div className="flex gap-2 mt-3 pt-3 border-t">
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    className="flex-1 text-xs h-7"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleVerMovimientos(ciclo);
                                    }}
                                  >
                                    <Eye className="h-3 w-3 mr-1" />
                                    Ver
                                  </Button>
                                  <Button
                                    size="sm"
                                    className="flex-1 text-xs h-7 bg-green-600 hover:bg-green-700"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleAvanzarEtapa(ciclo);
                                    }}
                                  >
                                    <ArrowRight className="h-3 w-3 mr-1" />
                                    Avanzar
                                  </Button>
                                </div>
                              )}
                            </CardContent>
                          </Card>
                        );
                      })
                    )}
                  </div>
                </div>
              );
            })}
          </div>
          
          {/* Leyenda */}
          <div className="flex flex-wrap gap-4 text-xs text-zinc-500 mt-4">
            <span className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-green-500"></div>
              En tiempo
            </span>
            <span className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-amber-500"></div>
              Próximo a vencer
            </span>
            <span className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-red-500"></div>
              Vencido
            </span>
          </div>
        </div>
      )}
      
      {activeTab === 'lista' && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Historial de Ciclos de Nómina</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-medium text-zinc-500">Sucursal</th>
                    <th className="text-left py-3 px-4 font-medium text-zinc-500">Tipo</th>
                    <th className="text-left py-3 px-4 font-medium text-zinc-500">Fecha Corte</th>
                    <th className="text-left py-3 px-4 font-medium text-zinc-500">Etapa</th>
                    <th className="text-left py-3 px-4 font-medium text-zinc-500">Colaboradores</th>
                    <th className="text-left py-3 px-4 font-medium text-zinc-500">Deadline</th>
                    <th className="text-left py-3 px-4 font-medium text-zinc-500">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {ciclos.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center py-8 text-zinc-500">
                        No hay ciclos de nómina registrados
                      </td>
                    </tr>
                  ) : (
                    ciclos.map(ciclo => {
                      const etapa = ETAPAS_NOMINA.find(e => e.id === ciclo.etapa_actual);
                      const tiempoRestante = calcularTiempoRestante(ciclo);
                      
                      return (
                        <tr key={ciclo.id} className="border-b hover:bg-zinc-50">
                          <td className="py-3 px-4 font-medium">
                            {ciclo.sucursal_nombre || '-'}
                          </td>
                          <td className="py-3 px-4 capitalize">
                            {ciclo.tipo_nomina}
                          </td>
                          <td className="py-3 px-4">
                            {new Date(ciclo.fecha_corte).toLocaleDateString()}
                          </td>
                          <td className="py-3 px-4">
                            {etapa && (
                              <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium text-white ${etapa.color}`}>
                                <etapa.icon className="h-3 w-3" />
                                {etapa.nombre}
                              </span>
                            )}
                          </td>
                          <td className="py-3 px-4">
                            {ciclo.total_colaboradores || 0}
                          </td>
                          <td className="py-3 px-4">
                            {tiempoRestante && (
                              <span className={`${tiempoRestante.color} font-medium`}>
                                {tiempoRestante.texto}
                              </span>
                            )}
                          </td>
                          <td className="py-3 px-4">
                            <div className="flex gap-2">
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleVerHistorial(ciclo)}
                                data-testid={`btn-historial-${ciclo.id}`}
                              >
                                <History className="h-4 w-4" />
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleVerMovimientos(ciclo)}
                                data-testid={`btn-movimientos-${ciclo.id}`}
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
      
      {activeTab === 'configuracion' && isAdmin && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Configuración de Tiempos */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Configuración de Tiempos
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Día de Corte de Nómina</Label>
                <select
                  value={formConfiguracion.dia_corte}
                  onChange={(e) => setFormConfiguracion({...formConfiguracion, dia_corte: parseInt(e.target.value)})}
                  className="w-full border rounded-lg px-3 py-2 mt-1"
                  data-testid="config-dia-corte"
                >
                  {diasSemana.map((dia, idx) => (
                    <option key={idx} value={idx}>{dia}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <Label>Día de Pago</Label>
                <select
                  value={formConfiguracion.dia_pago}
                  onChange={(e) => setFormConfiguracion({...formConfiguracion, dia_pago: parseInt(e.target.value)})}
                  className="w-full border rounded-lg px-3 py-2 mt-1"
                  data-testid="config-dia-pago"
                >
                  {diasSemana.map((dia, idx) => (
                    <option key={idx} value={idx}>{dia}</option>
                  ))}
                </select>
              </div>
              
              <div className="grid grid-cols-4 gap-4">
                <div>
                  <Label>Horario Headcount</Label>
                  <Input
                    type="time"
                    value={formConfiguracion.horario_headcount}
                    onChange={(e) => setFormConfiguracion({...formConfiguracion, horario_headcount: e.target.value})}
                    className="mt-1"
                    data-testid="config-horario-headcount"
                  />
                  <p className="text-xs text-zinc-500 mt-1">Límite para Gerencia</p>
                </div>
                <div>
                  <Label>Horario Autorización</Label>
                  <Input
                    type="time"
                    value={formConfiguracion.horario_autorizacion}
                    onChange={(e) => setFormConfiguracion({...formConfiguracion, horario_autorizacion: e.target.value})}
                    className="mt-1"
                    data-testid="config-horario-autorizacion"
                  />
                  <p className="text-xs text-zinc-500 mt-1">Límite Gerente/Autorizador</p>
                </div>
                <div>
                  <Label>Horario Maquilador</Label>
                  <Input
                    type="time"
                    value={formConfiguracion.horario_maquilador}
                    onChange={(e) => setFormConfiguracion({...formConfiguracion, horario_maquilador: e.target.value})}
                    className="mt-1"
                    data-testid="config-horario-maquilador"
                  />
                  <p className="text-xs text-zinc-500 mt-1">Límite para RH</p>
                </div>
                <div>
                  <Label>Horario Tesorería</Label>
                  <Input
                    type="time"
                    value={formConfiguracion.horario_tesoreria}
                    onChange={(e) => setFormConfiguracion({...formConfiguracion, horario_tesoreria: e.target.value})}
                    className="mt-1"
                    data-testid="config-horario-tesoreria"
                  />
                  <p className="text-xs text-zinc-500 mt-1">Límite para pago</p>
                </div>
              </div>
              
              <Button
                onClick={handleGuardarConfiguracion}
                disabled={savingForm}
                className="w-full mt-4"
                data-testid="btn-guardar-config"
              >
                {savingForm ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <Check className="h-4 w-4 mr-2" />}
                Guardar Configuración
              </Button>
            </CardContent>
          </Card>
          
          {/* Resumen de Flujo */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <ArrowRight className="h-5 w-5" />
                Flujo de Nómina
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {ETAPAS_NOMINA.map((etapa, idx) => {
                  const IconoEtapa = etapa.icon;
                  return (
                    <div key={etapa.id} className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${etapa.color}`}>
                        <IconoEtapa className="h-4 w-4 text-white" />
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-sm">{idx + 1}. {etapa.nombre}</p>
                        <p className="text-xs text-zinc-500">Responsable: {etapa.responsable}</p>
                      </div>
                      {idx < ETAPAS_NOMINA.length - 1 && (
                        <ArrowRight className="h-4 w-4 text-zinc-300" />
                      )}
                    </div>
                  );
                })}
              </div>
              
              <div className="mt-6 p-4 bg-zinc-100 rounded-lg">
                <h4 className="font-medium text-sm mb-2">Resumen del Proceso:</h4>
                <ul className="text-xs text-zinc-600 space-y-1">
                  <li>• <strong>Gerencia propone</strong> - Headcount e incidencias</li>
                  <li>• <strong>RH dispone</strong> - Valida movimientos</li>
                  <li>• <strong>Maquilador procesa</strong> - Calcula nómina</li>
                  <li>• <strong>Tesorería paga</strong> - Ejecuta dispersión</li>
                </ul>
              </div>
            </CardContent>
          </Card>
          
          {/* KPIs por Puesto */}
          <Card className="lg:col-span-2">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2">
                <Target className="h-5 w-5" />
                KPIs para Bonos por Puesto
              </CardTitle>
              <Button
                size="sm"
                onClick={() => setModalKPIs(true)}
                className="gap-2"
                data-testid="btn-configurar-kpis"
              >
                <Settings className="h-4 w-4" />
                Configurar KPIs
              </Button>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-zinc-500">
                Configure los indicadores de desempeño por puesto para calcular bonos automáticamente.
              </p>
              {kpis.length === 0 ? (
                <div className="text-center py-8 text-zinc-400">
                  <Target className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>No hay KPIs configurados</p>
                </div>
              ) : (
                <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {kpis.map(kpi => (
                    <div key={kpi.id} className="p-3 border rounded-lg">
                      <p className="font-medium">{kpi.puesto_nombre}</p>
                      <p className="text-sm text-zinc-500">{kpi.indicadores?.length || 0} indicadores</p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
      
      {/* Modal: Nuevo Ciclo */}
      {modalNuevoCiclo && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Nuevo Ciclo de Nómina</CardTitle>
              <Button variant="ghost" size="icon" onClick={() => setModalNuevoCiclo(false)}>
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Sucursal *</Label>
                <select
                  value={formNuevoCiclo.sucursal_id}
                  onChange={(e) => setFormNuevoCiclo({...formNuevoCiclo, sucursal_id: e.target.value})}
                  className="w-full border rounded-lg px-3 py-2 mt-1"
                  data-testid="form-sucursal"
                >
                  <option value="">Seleccione sucursal</option>
                  {sucursales.map(s => (
                    <option key={s.SucursalID || s.id} value={s.SucursalID || s.id}>
                      {s.Nombre || s.nombre}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <Label>Fecha de Corte *</Label>
                <Input
                  type="date"
                  value={formNuevoCiclo.fecha_corte}
                  onChange={(e) => setFormNuevoCiclo({...formNuevoCiclo, fecha_corte: e.target.value})}
                  className="mt-1"
                  data-testid="form-fecha-corte"
                />
              </div>
              
              <div>
                <Label>Tipo de Nómina</Label>
                <select
                  value={formNuevoCiclo.tipo_nomina}
                  onChange={(e) => setFormNuevoCiclo({...formNuevoCiclo, tipo_nomina: e.target.value})}
                  className="w-full border rounded-lg px-3 py-2 mt-1"
                  data-testid="form-tipo-nomina"
                >
                  <option value="quincenal">Quincenal</option>
                  <option value="semanal">Semanal</option>
                  <option value="mensual">Mensual</option>
                </select>
              </div>
              
              <div>
                <Label>Notas (opcional)</Label>
                <textarea
                  value={formNuevoCiclo.notas}
                  onChange={(e) => setFormNuevoCiclo({...formNuevoCiclo, notas: e.target.value})}
                  className="w-full border rounded-lg px-3 py-2 mt-1 min-h-[80px]"
                  placeholder="Observaciones del ciclo..."
                  data-testid="form-notas"
                />
              </div>
              
              <div className="flex gap-2 pt-4">
                <Button
                  variant="outline"
                  onClick={() => setModalNuevoCiclo(false)}
                  className="flex-1"
                >
                  Cancelar
                </Button>
                <Button
                  onClick={handleCrearCiclo}
                  disabled={savingForm}
                  className="flex-1"
                  data-testid="btn-crear-ciclo"
                >
                  {savingForm ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <Plus className="h-4 w-4 mr-2" />}
                  Crear Ciclo
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      
      {/* Modal: Aprobar/Avanzar */}
      {modalAprobar && cicloSeleccionado && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Lock className="h-5 w-5" />
                Autorizar Avance
              </CardTitle>
              <Button variant="ghost" size="icon" onClick={() => setModalAprobar(false)}>
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 bg-zinc-100 rounded-lg">
                <p className="text-sm"><strong>Sucursal:</strong> {cicloSeleccionado.sucursal_nombre}</p>
                <p className="text-sm"><strong>Etapa actual:</strong> {ETAPAS_NOMINA.find(e => e.id === cicloSeleccionado.etapa_actual)?.nombre}</p>
                <p className="text-sm"><strong>Siguiente etapa:</strong> {
                  ETAPAS_NOMINA[ETAPAS_NOMINA.findIndex(e => e.id === cicloSeleccionado.etapa_actual) + 1]?.nombre || 'Finalizado'
                }</p>
              </div>
              
              <div>
                <Label className="flex items-center gap-2">
                  <Lock className="h-4 w-4" />
                  Contraseña de Autorización *
                </Label>
                <Input
                  type="password"
                  value={passwordAprobacion}
                  onChange={(e) => setPasswordAprobacion(e.target.value)}
                  placeholder="Ingrese su contraseña"
                  className="mt-1"
                  data-testid="input-password-aprobar"
                />
              </div>
              
              <div>
                <Label>Comentario (opcional)</Label>
                <textarea
                  value={comentarioAprobacion}
                  onChange={(e) => setComentarioAprobacion(e.target.value)}
                  className="w-full border rounded-lg px-3 py-2 mt-1"
                  placeholder="Observaciones..."
                  data-testid="input-comentario-aprobar"
                />
              </div>
              
              <div className="flex gap-2 pt-4">
                <Button
                  variant="outline"
                  onClick={() => {
                    setCicloSeleccionado(cicloSeleccionado);
                    setMotivoRechazo('');
                    setModalAprobar(false);
                    setModalRechazar(true);
                  }}
                  className="flex-1 text-red-600 border-red-200 hover:bg-red-50"
                >
                  <RotateCcw className="h-4 w-4 mr-2" />
                  Devolver
                </Button>
                <Button
                  onClick={handleConfirmarAvance}
                  disabled={savingForm || !passwordAprobacion}
                  className="flex-1 bg-green-600 hover:bg-green-700"
                  data-testid="btn-confirmar-avance"
                >
                  {savingForm ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <ArrowRight className="h-4 w-4 mr-2" />}
                  Avanzar
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      
      {/* Modal: Rechazar/Devolver */}
      {modalRechazar && cicloSeleccionado && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-red-600">
                <RotateCcw className="h-5 w-5" />
                Devolver para Corrección
              </CardTitle>
              <Button variant="ghost" size="icon" onClick={() => setModalRechazar(false)}>
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-800">
                  La nómina será devuelta a la etapa de <strong>Validación RH</strong> para correcciones.
                </p>
              </div>
              
              <div>
                <Label>Motivo del Rechazo *</Label>
                <textarea
                  value={motivoRechazo}
                  onChange={(e) => setMotivoRechazo(e.target.value)}
                  className="w-full border border-red-200 rounded-lg px-3 py-2 mt-1 min-h-[100px]"
                  placeholder="Describa el motivo del rechazo..."
                  data-testid="input-motivo-rechazo"
                />
              </div>
              
              <div className="flex gap-2 pt-4">
                <Button
                  variant="outline"
                  onClick={() => setModalRechazar(false)}
                  className="flex-1"
                >
                  Cancelar
                </Button>
                <Button
                  onClick={handleRechazar}
                  disabled={savingForm || !motivoRechazo}
                  className="flex-1 bg-red-600 hover:bg-red-700"
                  data-testid="btn-confirmar-rechazo"
                >
                  {savingForm ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <RotateCcw className="h-4 w-4 mr-2" />}
                  Devolver
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      
      {/* Modal: Historial */}
      {modalHistorial && cicloSeleccionado && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <History className="h-5 w-5" />
                Historial de Trazabilidad
              </CardTitle>
              <Button variant="ghost" size="icon" onClick={() => setModalHistorial(false)}>
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="overflow-y-auto flex-1">
              <div className="mb-4 p-3 bg-zinc-100 rounded-lg">
                <p className="text-sm"><strong>Sucursal:</strong> {cicloSeleccionado.sucursal_nombre}</p>
                <p className="text-sm"><strong>Fecha Corte:</strong> {new Date(cicloSeleccionado.fecha_corte).toLocaleDateString()}</p>
              </div>
              
              {historialCiclo.length === 0 ? (
                <div className="text-center py-8 text-zinc-500">
                  <History className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>Sin eventos registrados</p>
                </div>
              ) : (
                <div className="relative">
                  <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-zinc-200"></div>
                  <div className="space-y-4">
                    {historialCiclo.map((evento, idx) => (
                      <div key={evento.id || idx} className="relative pl-10">
                        <div className={`absolute left-2 w-4 h-4 rounded-full ${
                          evento.tipo === 'creacion' ? 'bg-blue-500' :
                          evento.tipo === 'avance' ? 'bg-green-500' :
                          evento.tipo === 'rechazo' ? 'bg-red-500' :
                          'bg-zinc-400'
                        }`}></div>
                        <div className="bg-white border rounded-lg p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-medium text-sm">{evento.accion}</span>
                            <span className="text-xs text-zinc-500">
                              {new Date(evento.timestamp).toLocaleString()}
                            </span>
                          </div>
                          <p className="text-sm text-zinc-600">{evento.descripcion}</p>
                          <p className="text-xs text-zinc-400 mt-1">
                            Por: {evento.usuario_nombre || evento.usuario_email}
                          </p>
                          {evento.comentario && (
                            <p className="text-xs text-zinc-500 mt-1 italic">
                              "{evento.comentario}"
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
      
      {/* Modal: Movimientos */}
      {modalMovimientos && cicloSeleccionado && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Movimientos de Nómina
              </CardTitle>
              <Button variant="ghost" size="icon" onClick={() => setModalMovimientos(false)}>
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="overflow-y-auto flex-1">
              <div className="mb-4 p-3 bg-zinc-100 rounded-lg flex items-center justify-between">
                <div>
                  <p className="text-sm"><strong>Sucursal:</strong> {cicloSeleccionado.sucursal_nombre}</p>
                  <p className="text-sm"><strong>Etapa:</strong> {ETAPAS_NOMINA.find(e => e.id === cicloSeleccionado.etapa_actual)?.nombre}</p>
                </div>
                {['headcount', 'incidencias'].includes(cicloSeleccionado.etapa_actual) && (
                  <Button
                    size="sm"
                    className="gap-2"
                    onClick={() => {
                      // Aquí se podría abrir un modal para agregar movimiento
                      toast.info('Funcionalidad de agregar movimiento próximamente');
                    }}
                  >
                    <Plus className="h-4 w-4" />
                    Agregar
                  </Button>
                )}
              </div>
              
              {movimientos.length === 0 ? (
                <div className="text-center py-8 text-zinc-500">
                  <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>Sin movimientos registrados</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-2 px-3 font-medium text-zinc-500">Colaborador</th>
                        <th className="text-left py-2 px-3 font-medium text-zinc-500">Tipo</th>
                        <th className="text-right py-2 px-3 font-medium text-zinc-500">Monto</th>
                        <th className="text-right py-2 px-3 font-medium text-zinc-500">Unidades</th>
                        <th className="text-left py-2 px-3 font-medium text-zinc-500">Notas</th>
                        <th className="text-left py-2 px-3 font-medium text-zinc-500">Registrado Por</th>
                      </tr>
                    </thead>
                    <tbody>
                      {movimientos.map((mov, idx) => (
                        <tr key={mov.id || idx} className="border-b hover:bg-zinc-50">
                          <td className="py-2 px-3 font-medium">{mov.colaborador_nombre}</td>
                          <td className="py-2 px-3">
                            <span className={`px-2 py-1 rounded text-xs ${
                              mov.categoria === 'Ingreso' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                            }`}>
                              {mov.tipo_incidencia}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-right font-mono">
                            ${(mov.monto || 0).toLocaleString()}
                          </td>
                          <td className="py-2 px-3 text-right">{mov.unidades || '-'}</td>
                          <td className="py-2 px-3 text-zinc-500 text-xs">{mov.notas || '-'}</td>
                          <td className="py-2 px-3 text-xs text-zinc-500">{mov.registrado_por}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
      
      {/* Modal: Detalle Ciclo */}
      {modalDetalleCiclo && cicloSeleccionado && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-lg">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Detalle del Ciclo</CardTitle>
              <Button variant="ghost" size="icon" onClick={() => setModalDetalleCiclo(false)}>
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-zinc-500 text-xs">Sucursal</Label>
                  <p className="font-medium">{cicloSeleccionado.sucursal_nombre}</p>
                </div>
                <div>
                  <Label className="text-zinc-500 text-xs">Tipo</Label>
                  <p className="font-medium capitalize">{cicloSeleccionado.tipo_nomina}</p>
                </div>
                <div>
                  <Label className="text-zinc-500 text-xs">Fecha de Corte</Label>
                  <p className="font-medium">{new Date(cicloSeleccionado.fecha_corte).toLocaleDateString()}</p>
                </div>
                <div>
                  <Label className="text-zinc-500 text-xs">Etapa Actual</Label>
                  <p className="font-medium">{ETAPAS_NOMINA.find(e => e.id === cicloSeleccionado.etapa_actual)?.nombre}</p>
                </div>
                <div>
                  <Label className="text-zinc-500 text-xs">Colaboradores</Label>
                  <p className="font-medium">{cicloSeleccionado.total_colaboradores || 0}</p>
                </div>
                <div>
                  <Label className="text-zinc-500 text-xs">Movimientos</Label>
                  <p className="font-medium">{cicloSeleccionado.total_movimientos || 0}</p>
                </div>
              </div>
              
              {cicloSeleccionado.notas && (
                <div>
                  <Label className="text-zinc-500 text-xs">Notas</Label>
                  <p className="text-sm">{cicloSeleccionado.notas}</p>
                </div>
              )}
              
              <div className="flex gap-2 pt-4">
                <Button
                  variant="outline"
                  onClick={() => {
                    setModalDetalleCiclo(false);
                    handleVerHistorial(cicloSeleccionado);
                  }}
                  className="flex-1"
                >
                  <History className="h-4 w-4 mr-2" />
                  Ver Historial
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setModalDetalleCiclo(false);
                    handleVerMovimientos(cicloSeleccionado);
                  }}
                  className="flex-1"
                >
                  <FileText className="h-4 w-4 mr-2" />
                  Ver Movimientos
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
