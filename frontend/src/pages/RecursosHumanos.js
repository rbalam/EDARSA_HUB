/**
 * EDARSA HUB - Módulo Recursos Humanos
 * ====================================
 * Gestión del capital humano - Conectado a EDARSA HUB
 * 
 * FASE P1-FETCH-MIGRATION: Migrado a api.js centralizado
 */

import React, { useState, useEffect, useCallback } from 'react';
import logger from '../services/logger';
import api from '../lib/api';
import { getSessionUser } from '../services/authStorage';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { 
  Users, Wallet, Calendar, UserCheck, FileText, AlertTriangle,
  Search, Plus, ChevronRight, Building2, Briefcase, Clock,
  CheckCircle2, XCircle, RefreshCw, Filter, ArrowUpDown,
  X, Save, Upload, Trash2, Eye, Edit, UserPlus, FileSpreadsheet,
  Inbox, Star, Phone, Mail, Copy, ExternalLink, Settings, Lock,
  Tag, DollarSign, Database, Timer, ArrowRight, RotateCcw, Layers,
  Target, ClipboardList, Send, History, Download, Bell
} from 'lucide-react';
import { toast } from 'sonner';
import { GestionSolicitudesCatalogo } from '../components/GestionSolicitudesCatalogo';
import { BotonSolicitarAlta } from '../components/ModalSolicitudCatalogo';
import { getEventoBgClass } from '../utils/styleHelpers';

// FASE 4E: Componentes extraídos
import { 
  RhDashboard, 
  RhColaboradores, 
  RhIncidencias,
  RhNominas,
  RhCatalogos,
  RhReclutamiento,
  RhAsistencia,
  EstatusLaboralBadge, 
  RhEmptyState 
} from '../components/recursos-humanos';
import { isAdminRole } from '../lib/roleUtils';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function RecursosHumanos() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  
  // Data states
  const [dashboard, setDashboard] = useState(null);
  const [colaboradores, setColaboradores] = useState([]);
  const [incidencias, setIncidencias] = useState([]);
  const [flujos, setFlujos] = useState([]);
  const [sucursales, setSucursales] = useState([]);
  const [puestos, setPuestos] = useState([]);
  
  // Estados para Reclutamiento (Fase 5)
  const [vacantes, setVacantes] = useState([]);
  const [candidatos, setCandidatos] = useState([]);
  const [reclutamientoDash, setReclutamientoDash] = useState(null);
  
  // Estados para Catálogos (Puestos e Incidencias)
  const [catalogoPuestos, setCatalogoPuestos] = useState([]);
  const [catalogoIncidencias, setCatalogoIncidencias] = useState([]);
  const [catalogoSubTab, setCatalogoSubTab] = useState('puestos');
  const [loadingCatalogos, setLoadingCatalogos] = useState(false);
  
  // Verificar si es Administrador
  const currentUser = getSessionUser() || {};
  const isAdmin = isAdminRole(currentUser);
  const isSupervisor = currentUser?.role === 'Supervisor';
  
  // Filters
  const [filtroSucursal, setFiltroSucursal] = useState('');
  const [filtroBuscar, setFiltroBuscar] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  // Modal states - FASE 2
  const [modalColaborador, setModalColaborador] = useState(false);
  const [modalIncidencia, setModalIncidencia] = useState(false);
  const [modalDetalle, setModalDetalle] = useState(false);
  const [modalImportExcel, setModalImportExcel] = useState(false);
  const [editingColaborador, setEditingColaborador] = useState(null);
  const [detalleColaborador, setDetalleColaborador] = useState(null);
  const [loadingDetalle, setLoadingDetalle] = useState(false);
  const [savingForm, setSavingForm] = useState(false);
  
  // Estados para importar Excel
  const [importFile, setImportFile] = useState(null);
  const [importLoading, setImportLoading] = useState(false);
  const [importResult, setImportResult] = useState(null);
  
  // Estados para Reclutamiento (Fase 5)
  const [modalVacante, setModalVacante] = useState(false);
  const [modalCandidato, setModalCandidato] = useState(false);
  const [modalScriptRecl, setModalScriptRecl] = useState(false);
  const [editingVacante, setEditingVacante] = useState(null);
  const [selectedVacante, setSelectedVacante] = useState(null);
  const [scriptRecl, setScriptRecl] = useState(null);
  
  // Estados para Catálogos RRHH
  const [modalPuesto, setModalPuesto] = useState(false);
  const [modalTipoIncidencia, setModalTipoIncidencia] = useState(false);
  const [modalScriptCatalogos, setModalScriptCatalogos] = useState(false);
  const [editingPuesto, setEditingPuesto] = useState(null);
  const [editingTipoIncidencia, setEditingTipoIncidencia] = useState(null);
  const [scriptCatalogos, setScriptCatalogos] = useState(null);
  
  // ============= ESTADOS MÓDULO NÓMINAS =============
  const [ciclosNomina, setCiclosNomina] = useState([]);
  const [configNomina, setConfigNomina] = useState(null);
  const [loadingNominas, setLoadingNominas] = useState(false);
  const [modalNuevoCiclo, setModalNuevoCiclo] = useState(false);
  const [modalAprobarCiclo, setModalAprobarCiclo] = useState(false);
  const [modalRechazarCiclo, setModalRechazarCiclo] = useState(false);
  const [modalHistorialCiclo, setModalHistorialCiclo] = useState(false);
  const [modalMovimientos, setModalMovimientos] = useState(false);
  const [modalConfigNomina, setModalConfigNomina] = useState(false);
  const [cicloSeleccionado, setCicloSeleccionado] = useState(null);
  const [movimientosCiclo, setMovimientosCiclo] = useState([]);
  const [passwordAprobacion, setPasswordAprobacion] = useState('');
  const [comentarioAprobacion, setComentarioAprobacion] = useState('');
  const [motivoRechazo, setMotivoRechazo] = useState('');
  const [nominaSubTab, setNominaSubTab] = useState('kanban');
  
  // ============= ESTADOS CAPTURA MASIVA INCIDENCIAS =============
  const [capturaSemana, setCapturaSemana] = useState('');
  const [capturaFiltroSucursal, setCapturaFiltroSucursal] = useState('');
  const [capturaFiltroDepartamento, setCapturaFiltroDepartamento] = useState('');
  const [colaboradoresCaptura, setColaboradoresCaptura] = useState([]);
  const [loadingCaptura, setLoadingCaptura] = useState(false);
  const [capturaData, setCapturaData] = useState({}); // {colaboradorId: {lunes: '1', martes: 'R', ...}}
  const [savingCaptura, setSavingCaptura] = useState(false);
  const [departamentos, setDepartamentos] = useState([]);
  
  // Catálogo de símbolos de incidencias (basado en Excel del usuario)
  const SIMBOLOS_INCIDENCIA = [
    { codigo: '1', nombre: 'Laboró un turno', turnos: 1, esRetardo: false, esFalta: false, afectaDescanso: true, color: 'bg-green-100 text-green-800' },
    { codigo: '1.5', nombre: 'Turno y medio', turnos: 1.5, esRetardo: false, esFalta: false, afectaDescanso: true, color: 'bg-green-200 text-green-800' },
    { codigo: '2', nombre: 'Dos turnos', turnos: 2, esRetardo: false, esFalta: false, afectaDescanso: true, color: 'bg-green-300 text-green-900' },
    { codigo: 'R', nombre: 'Retardo turno normal', turnos: 1, esRetardo: true, esFalta: false, afectaDescanso: true, color: 'bg-yellow-100 text-yellow-800' },
    { codigo: 'R+', nombre: 'Retardo turno y medio', turnos: 1.5, esRetardo: true, esFalta: false, afectaDescanso: true, color: 'bg-yellow-200 text-yellow-800' },
    { codigo: 'R*', nombre: 'Retardo turno doble', turnos: 2, esRetardo: true, esFalta: false, afectaDescanso: true, color: 'bg-yellow-300 text-yellow-900' },
    { codigo: 'F', nombre: 'Falta', turnos: 0, esRetardo: false, esFalta: true, afectaDescanso: false, color: 'bg-red-100 text-red-800' },
    { codigo: 'P', nombre: 'Permiso sin goce', turnos: 0, esRetardo: false, esFalta: false, afectaDescanso: false, color: 'bg-orange-100 text-orange-800' },
    { codigo: 'PG', nombre: 'Permiso con goce', turnos: 1, esRetardo: false, esFalta: false, afectaDescanso: true, color: 'bg-blue-100 text-blue-800' },
    { codigo: 'IN', nombre: 'Incapacidad no pagada', turnos: 0, esRetardo: false, esFalta: false, afectaDescanso: false, color: 'bg-purple-100 text-purple-800' },
    { codigo: 'V', nombre: 'Vacaciones', turnos: 1, esRetardo: false, esFalta: false, afectaDescanso: true, color: 'bg-cyan-100 text-cyan-800' },
    { codigo: 'D', nombre: 'Descanso', turnos: 0, esRetardo: false, esFalta: false, afectaDescanso: true, color: 'bg-gray-200 text-gray-700' },
    { codigo: 'S', nombre: 'Suspensión', turnos: 0, esRetardo: false, esFalta: false, afectaDescanso: false, color: 'bg-red-200 text-red-800' },
    { codigo: 'NF', nombre: 'No Firmó', turnos: 0, esRetardo: false, esFalta: false, afectaDescanso: true, color: 'bg-amber-100 text-amber-800' },
    { codigo: 'B', nombre: 'Baja', turnos: 0, esRetardo: false, esFalta: false, afectaDescanso: false, color: 'bg-gray-400 text-gray-900' },
    { codigo: '0', nombre: 'Nuevo ingreso', turnos: 0, esRetardo: false, esFalta: false, afectaDescanso: false, color: 'bg-slate-100 text-slate-600' },
  ];
  
  // Días de la semana para captura
  const DIAS_SEMANA_CAPTURA = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo'];
  const DIAS_SEMANA_LABELS = ['L', 'M', 'Mi', 'J', 'V', 'S', 'D'];
  const [formNuevoCiclo, setFormNuevoCiclo] = useState({
    sucursal_id: '',
    fecha_corte: '',
    tipo_nomina: 'quincenal',
    notas: ''
  });
  const [formConfigNomina, setFormConfigNomina] = useState({
    dia_corte: 0,
    dia_pago: 1,
    horario_headcount: '10:00',
    horario_autorizacion: '11:00',
    horario_maquilador: '12:00',
    horario_tesoreria: '14:00'
  });
  
  // Form states
  const [formColaborador, setFormColaborador] = useState({
    nombre_completo: '',
    curp: '',
    rfc: '',
    clabe_bancaria: '',
    sucursal_id: '',
    puesto_id: '',
    estatus_laboral: 'Activo'
  });
  
  const [formIncidencia, setFormIncidencia] = useState({
    colaborador_id: '',
    tipo_incidencia: '',
    monto: 0,
    unidades: 0,
    fecha_incidencia: new Date().toISOString().split('T')[0]
  });
  
  const [formVacante, setFormVacante] = useState({
    sucursal_id: '',
    puesto_id: '',
    titulo: '',
    descripcion: '',
    requisitos: '',
    salario_min: 0,
    salario_max: 0,
    tipo_contrato: 'Tiempo Completo'
  });
  
  const [formCandidato, setFormCandidato] = useState({
    vacante_id: '',
    nombre: '',
    email: '',
    telefono: '',
    cv_url: ''
  });

  // Formularios para Catálogos
  const [formPuesto, setFormPuesto] = useState({
    descripcion: '',
    departamento: '',
    sueldo_base: 0,
    nomipaq_id: '',
    mpro_id: ''
  });

  const [formTipoIncidencia, setFormTipoIncidencia] = useState({
    codigo: '',
    descripcion: '',
    categoria: 'Descuento',
    calculo_monto: 'Manual',
    nomipaq_id: '',
    mpro_id: ''
  });

  // FASE P1-FETCH-MIGRATION: Migrado a api.js centralizado
  const fetchWithAuth = useCallback(async (url) => {
    const response = await api.get(url);
    return response.data;
  }, []);

  // Cargar dashboard
  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchWithAuth('/rrhh/dashboard');
      setDashboard(data);
    } catch (error) {
      logger.error('Error cargando dashboard:', error);
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth]);

  // Cargar catálogos
  const loadCatalogos = useCallback(async () => {
    try {
      const [sucData, puestosData] = await Promise.all([
        fetchWithAuth('/rrhh/catalogos/sucursales'),
        fetchWithAuth('/rrhh/catalogos/puestos')
      ]);
      setSucursales(sucData.sucursales || []);
      setPuestos(puestosData.puestos || []);
    } catch (error) {
      logger.error('Error cargando catálogos:', error);
    }
  }, [fetchWithAuth]);

  // Cargar colaboradores
  const loadColaboradores = useCallback(async () => {
    try {
      setLoading(true);
      let url = `/api/rrhh/colaboradores?page=${page}&limit=50`;
      if (filtroSucursal) url += `&sucursal_id=${filtroSucursal}`;
      if (filtroBuscar) url += `&buscar=${encodeURIComponent(filtroBuscar)}`;
      
      const data = await fetchWithAuth(url);
      setColaboradores(data.colaboradores || []);
      setTotalPages(data.pages || 1);
    } catch (error) {
      logger.error('Error cargando colaboradores:', error);
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, page, filtroSucursal, filtroBuscar]);

  // Cargar incidencias
  const loadIncidencias = useCallback(async () => {
    try {
      setLoading(true);
      let url = `/api/rrhh/incidencias?page=1&limit=100`;
      if (filtroSucursal) url += `&sucursal_id=${filtroSucursal}`;
      
      const data = await fetchWithAuth(url);
      setIncidencias(data.incidencias || []);
    } catch (error) {
      logger.error('Error cargando incidencias:', error);
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, filtroSucursal]);

  // Cargar flujos de nómina
  const loadFlujos = useCallback(async () => {
    try {
      setLoading(true);
      let url = `/api/rrhh/nominas/flujo`;
      if (filtroSucursal) url += `?sucursal_id=${filtroSucursal}`;
      
      const data = await fetchWithAuth(url);
      setFlujos(data.flujos || []);
    } catch (error) {
      logger.error('Error cargando flujos:', error);
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, filtroSucursal]);

  // Initial load
  useEffect(() => {
    loadDashboard();
    loadCatalogos();
  }, [loadDashboard, loadCatalogos]);

  // Load data based on tab
  useEffect(() => {
    if (activeTab === 'colaboradores') loadColaboradores();
    if (activeTab === 'incidencias') loadIncidencias();
    if (activeTab === 'nomina') loadCiclosNomina();
    if (activeTab === 'reclutamiento') loadReclutamiento();
    if (activeTab === 'catalogos') loadCatalogosCompleto();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, loadColaboradores, loadIncidencias, loadFlujos]);

  // ============= FUNCIONES MÓDULO NÓMINAS =============
  const ETAPAS_NOMINA = [
    { id: 'headcount', nombre: 'Headcount', icon: Users, color: 'bg-blue-500', responsable: 'Gerencia' },
    { id: 'incidencias', nombre: 'Incidencias', icon: ClipboardList, color: 'bg-purple-500', responsable: 'Gerencia' },
    { id: 'validacion_rh', nombre: 'Validación RH', icon: UserCheck, color: 'bg-amber-500', responsable: 'RH' },
    { id: 'maquilador', nombre: 'Maquilador', icon: FileSpreadsheet, color: 'bg-cyan-500', responsable: 'Maquilador' },
    { id: 'autorizacion', nombre: 'Autorización', icon: CheckCircle2, color: 'bg-green-500', responsable: 'Gerencia' },
    { id: 'tesoreria', nombre: 'Tesorería', icon: Wallet, color: 'bg-emerald-500', responsable: 'Tesorería' },
    { id: 'pagada', nombre: 'Pagada', icon: DollarSign, color: 'bg-zinc-500', responsable: 'Sistema' }
  ];
  
  const loadCiclosNomina = async () => {
    try {
      setLoadingNominas(true);
      const [ciclosData, configData] = await Promise.all([
        fetchWithAuth('/nomina/ciclos'),
        fetchWithAuth('/nomina/configuracion')
      ]);
      setCiclosNomina(ciclosData.ciclos || []);
      setConfigNomina(configData.configuracion);
      if (configData.configuracion) {
        setFormConfigNomina({
          dia_corte: configData.configuracion.dia_corte || 0,
          dia_pago: configData.configuracion.dia_pago || 1,
          horario_headcount: configData.configuracion.horario_headcount || '10:00',
          horario_autorizacion: configData.configuracion.horario_autorizacion || '11:00',
          horario_maquilador: configData.configuracion.horario_maquilador || '12:00',
          horario_tesoreria: configData.configuracion.horario_tesoreria || '14:00'
        });
      }
    } catch (error) {
      logger.error('Error cargando nóminas:', error);
    } finally {
      setLoadingNominas(false);
    }
  };
  
  const getCiclosPorEtapa = (etapaId) => ciclosNomina.filter(c => c.etapa_actual === etapaId);
  
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
  
  const handleCrearCicloNomina = async () => {
    if (!formNuevoCiclo.sucursal_id || !formNuevoCiclo.fecha_corte) {
      toast.error('Complete todos los campos requeridos');
      return;
    }
    setSavingForm(true);
    try {
      await api.post('/nomina/ciclos', formNuevoCiclo);
      toast.success('Ciclo de nómina creado correctamente');
      setModalNuevoCiclo(false);
      setFormNuevoCiclo({ sucursal_id: '', fecha_corte: '', tipo_nomina: 'quincenal', notas: '' });
      loadCiclosNomina();
    } catch (error) {
      toast.error(error.response?.data?.detail || error.message);
    } finally {
      setSavingForm(false);
    }
  };
  
  const handleAvanzarCiclo = async () => {
    if (!passwordAprobacion) {
      toast.error('Ingrese su contraseña para autorizar');
      return;
    }
    setSavingForm(true);
    try {
      const response = await api.post(`/nomina/ciclos/${cicloSeleccionado.id}/avanzar`, {
        password: passwordAprobacion,
        comentario: comentarioAprobacion
      });
      toast.success(response.data.message || 'Etapa avanzada correctamente');
      setModalAprobarCiclo(false);
      setPasswordAprobacion('');
      setComentarioAprobacion('');
      loadCiclosNomina();
    } catch (error) {
      if (error.response?.status === 401) { toast.error('Contraseña incorrecta'); return; }
      toast.error(error.response?.data?.detail || error.message);
    } finally {
      setSavingForm(false);
    }
  };
  
  const handleRechazarCiclo = async () => {
    if (!motivoRechazo) { toast.error('Ingrese el motivo del rechazo'); return; }
    setSavingForm(true);
    try {
      await api.post(`/nomina/ciclos/${cicloSeleccionado.id}/rechazar`, { motivo: motivoRechazo });
      toast.success('Nómina devuelta para corrección');
      setModalRechazarCiclo(false);
      setMotivoRechazo('');
      loadCiclosNomina();
    } catch (error) {
      toast.error(error.response?.data?.detail || error.message);
    } finally {
      setSavingForm(false);
    }
  };
  
  const handleVerMovimientosCiclo = async (ciclo) => {
    setCicloSeleccionado(ciclo);
    try {
      const data = await fetchWithAuth(`/nomina/ciclos/${ciclo.id}/movimientos`);
      setMovimientosCiclo(data.movimientos || []);
      setModalMovimientos(true);
    } catch (error) {
      toast.error('Error cargando movimientos');
    }
  };
  
  const handleGuardarConfigNomina = async () => {
    setSavingForm(true);
    try {
      await api.post('/nomina/configuracion', formConfigNomina);
      toast.success('Configuración guardada correctamente');
      setModalConfigNomina(false);
      loadCiclosNomina();
    } catch (error) {
      toast.error('Error al guardar configuración');
    } finally {
      setSavingForm(false);
    }
  };
  
  const diasSemana = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];

  // ============= FUNCIONES CAPTURA MASIVA INCIDENCIAS =============
  
  // Obtener inicio de semana actual (Lunes)
  const getInicioSemanaActual = () => {
    const hoy = new Date();
    const dia = hoy.getDay();
    const diff = hoy.getDate() - dia + (dia === 0 ? -6 : 1);
    const lunes = new Date(hoy.setDate(diff));
    return lunes.toISOString().split('T')[0];
  };

  // Cargar colaboradores activos para captura
  const loadColaboradoresCaptura = async () => {
    if (!capturaFiltroSucursal) {
      toast.error('Seleccione una sucursal');
      return;
    }
    
    setLoadingCaptura(true);
    try {
      let allColaboradores = [];
      let currentPage = 1;
      let hasMore = true;
      
      while (hasMore) {
        const url = `/rrhh/colaboradores?page=${currentPage}&limit=200&sucursal_id=${capturaFiltroSucursal}`;
        
        const response = await api.get(url);
        const data = response.data;
        
        allColaboradores = [...allColaboradores, ...(data.colaboradores || [])];
        hasMore = currentPage < (data.pages || 1);
        currentPage++;
        if (currentPage > 10) hasMore = false;
      }
      
      const activos = allColaboradores.filter(c => 
        c.Estatus_Laboral?.toUpperCase() === 'ACTIVO'
      );
      setColaboradoresCaptura(activos);
      
      // Inicializar capturaData con días por defecto (todos trabajan 1 turno L-S, descanso D)
      const initialData = {};
      activos.forEach(col => {
        initialData[col.ColaboradorID] = {
          lunes: '1',
          martes: '1',
          miercoles: '1',
          jueves: '1',
          viernes: '1',
          sabado: '1',
          domingo: 'D'
        };
      });
      setCapturaData(initialData);
      
      const deptosUnicos = [...new Set(activos.map(c => c.Departamento).filter(Boolean))];
      setDepartamentos(deptosUnicos);
      
      toast.success(`${activos.length} colaboradores cargados`);
      
    } catch (error) {
      logger.error('Error cargando colaboradores:', error);
      toast.error('Error al cargar colaboradores');
    } finally {
      setLoadingCaptura(false);
    }
  };

  // Actualizar símbolo de un día específico
  const handleCapturaDiaChange = (colaboradorId, dia, valor) => {
    setCapturaData(prev => ({
      ...prev,
      [colaboradorId]: {
        ...prev[colaboradorId],
        [dia]: valor
      }
    }));
  };

  // Calcular totales de un colaborador
  const calcularTotalesColaborador = (colaboradorId) => {
    const datos = capturaData[colaboradorId] || {};
    let turnos = 0;
    let retardos = 0;
    let faltas = 0;
    let diasLaborados = 0;
    
    DIAS_SEMANA_CAPTURA.forEach(dia => {
      const simbolo = datos[dia];
      const config = SIMBOLOS_INCIDENCIA.find(s => s.codigo === simbolo);
      if (config) {
        turnos += config.turnos;
        if (config.esRetardo) retardos++;
        if (config.esFalta) faltas++;
        if (config.afectaDescanso && config.turnos > 0) diasLaborados++;
      }
    });
    
    // Faltas por retardos (cada 3 retardos = 1 falta)
    const faltasPorRetardos = Math.floor(retardos / 3);
    
    // Proporcional descanso: 6 días laborados = 1 día descanso
    const proporcionalDescanso = (diasLaborados / 6).toFixed(2);
    
    // Proporcional aguinaldo: 365 días = 15 días (semanal = 15/52)
    const proporcionalAguinaldoSemanal = ((diasLaborados / 6) * (15 / 52)).toFixed(3);
    
    return {
      turnos: turnos.toFixed(1),
      retardos,
      faltas,
      faltasPorRetardos,
      faltasTotal: faltas + faltasPorRetardos,
      diasLaborados,
      proporcionalDescanso,
      proporcionalAguinaldoSemanal
    };
  };

  // Obtener color del símbolo
  const getSimboloColor = (codigo) => {
    const config = SIMBOLOS_INCIDENCIA.find(s => s.codigo === codigo);
    return config?.color || 'bg-white';
  };

  // Guardar captura masiva
  const handleGuardarCapturaMasiva = async () => {
    if (!capturaSemana) {
      toast.error('Seleccione la semana de captura');
      return;
    }
    
    setSavingCaptura(true);
    let exitosos = 0;
    let errores = 0;
    
    try {
      for (const [colaboradorId, dias] of Object.entries(capturaData)) {
        const totales = calcularTotalesColaborador(colaboradorId);
        
        // Solo guardar si hay incidencias relevantes (faltas, retardos, etc.)
        if (totales.faltas > 0 || totales.retardos > 0 || totales.faltasPorRetardos > 0) {
          try {
            // Guardar resumen de incidencias
            const incidencias = [];
            
            if (totales.faltas > 0) {
              incidencias.push({
                colaborador_id: colaboradorId.toString(),
                tipo_incidencia: 'Falta',
                unidades: totales.faltas,
                fecha_incidencia: capturaSemana
              });
            }
            
            if (totales.retardos > 0) {
              incidencias.push({
                colaborador_id: colaboradorId.toString(),
                tipo_incidencia: 'Retardo',
                unidades: totales.retardos,
                fecha_incidencia: capturaSemana
              });
            }
            
            for (const inc of incidencias) {
              await api.post('/rrhh/incidencias', { ...inc, monto: 0 });
            }
            
            exitosos++;
          } catch (e) {
            errores++;
          }
        }
      }
      
      if (exitosos > 0) toast.success(`${exitosos} registros guardados`);
      if (errores > 0) toast.error(`${errores} errores`);
      
    } catch (error) {
      toast.error('Error en la captura masiva');
    } finally {
      setSavingCaptura(false);
    }
  };

  // Exportar captura a Excel
  const handleExportarCapturaExcel = () => {
    if (colaboradoresCaptura.length === 0) {
      toast.error('No hay datos para exportar');
      return;
    }
    
    // Crear CSV
    let csv = 'No.,Colaborador,Puesto,L,M,Mi,J,V,S,D,Turnos,Retardos,Faltas,F.xRetardos,Prop.Descanso,Prop.Aguinaldo\n';
    
    colaboradoresCaptura.forEach((col, idx) => {
      const datos = capturaData[col.ColaboradorID] || {};
      const totales = calcularTotalesColaborador(col.ColaboradorID);
      
      csv += `${idx + 1},"${col.Nombre_Completo}","${col.Puesto || ''}",`;
      csv += `${datos.lunes || ''},${datos.martes || ''},${datos.miercoles || ''},`;
      csv += `${datos.jueves || ''},${datos.viernes || ''},${datos.sabado || ''},${datos.domingo || ''},`;
      csv += `${totales.turnos},${totales.retardos},${totales.faltas},${totales.faltasPorRetardos},`;
      csv += `${totales.proporcionalDescanso},${totales.proporcionalAguinaldoSemanal}\n`;
    });
    
    // Descargar
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `captura_incidencias_${capturaSemana || 'sin_fecha'}.csv`;
    link.click();
    
    toast.success('Excel exportado');
  };


  const loadReclutamiento = useCallback(async () => {
    try {
      setLoading(true);
      const [dashData, vacData, candData] = await Promise.all([
        fetchWithAuth('/rrhh/reclutamiento/dashboard'),
        fetchWithAuth('/rrhh/vacantes'),
        fetchWithAuth('/rrhh/candidatos')
      ]);
      setReclutamientoDash(dashData);
      setVacantes(vacData.vacantes || []);
      setCandidatos(candData.candidatos || []);
    } catch (error) {
      logger.error('Error cargando reclutamiento:', error);
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth]);

  // ===================== FUNCIONES CATÁLOGOS RRHH =====================
  
  // Cargar catálogos completos (Puestos e Incidencias)
  const loadCatalogosCompleto = useCallback(async () => {
    try {
      setLoadingCatalogos(true);
      const [puestosData, incidenciasData] = await Promise.all([
        fetchWithAuth('/rrhh/catalogos/puestos'),
        fetchWithAuth('/rrhh/catalogos/tipos-incidencias')
      ]);
      setCatalogoPuestos(puestosData.puestos || []);
      setCatalogoIncidencias(incidenciasData.tipos_incidencias || []);
    } catch (error) {
      logger.error('Error cargando catálogos:', error);
      toast.error('Error cargando catálogos');
    } finally {
      setLoadingCatalogos(false);
    }
  }, [fetchWithAuth]);
  
  // Cargar script SQL de catálogos
  const loadScriptCatalogos = async () => {
    try {
      const data = await fetchWithAuth('/rrhh/catalogos/script-inicializacion');
      setScriptCatalogos(data);
      setModalScriptCatalogos(true);
    } catch (error) {
      toast.error('Error cargando script SQL');
    }
  };
  
  // Abrir modal para nuevo puesto
  const handleNuevoPuesto = () => {
    if (!isAdmin) {
      toast.error('Solo administradores pueden crear puestos');
      return;
    }
    setEditingPuesto(null);
    setFormPuesto({
      descripcion: '',
      departamento: '',
      sueldo_base: 0,
      nomipaq_id: '',
      mpro_id: ''
    });
    setModalPuesto(true);
  };
  
  // Abrir modal para editar puesto
  const handleEditarPuesto = (puesto) => {
    if (!isAdmin) {
      toast.error('Solo administradores pueden editar puestos');
      return;
    }
    setEditingPuesto(puesto);
    setFormPuesto({
      descripcion: puesto.Descripcion || '',
      departamento: puesto.Departamento || '',
      sueldo_base: puesto.Sueldo_Base_Seman_SBC || 0,
      nomipaq_id: puesto.NomiPAQ_ID || '',
      mpro_id: puesto.MPRO_ID || ''
    });
    setModalPuesto(true);
  };
  
  // Guardar puesto
  const handleGuardarPuesto = async () => {
    if (!formPuesto.descripcion.trim()) {
      toast.error('La descripción del puesto es requerida');
      return;
    }
    
    setSavingForm(true);
    try {
      const endpoint = editingPuesto 
        ? `/rrhh/catalogos/puestos/${editingPuesto.PuestoID}`
        : '/rrhh/catalogos/puestos';
      
      if (editingPuesto) {
        await api.put(endpoint, formPuesto);
      } else {
        await api.post(endpoint, formPuesto);
      }
      
      toast.success(editingPuesto ? 'Puesto actualizado' : 'Puesto creado');
      setModalPuesto(false);
      loadCatalogosCompleto();
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error('Solo administradores pueden realizar esta acción');
      } else {
        toast.error('Error al guardar puesto');
      }
    } finally {
      setSavingForm(false);
    }
  };
  
  // Eliminar puesto
  const handleEliminarPuesto = async (puestoId) => {
    if (!isAdmin) {
      toast.error('Solo administradores pueden eliminar puestos');
      return;
    }
    if (!window.confirm('¿Está seguro de eliminar este puesto?')) return;
    
    try {
      await api.delete(`/rrhh/catalogos/puestos/${puestoId}`);
      
      toast.success('Puesto eliminado');
      loadCatalogosCompleto();
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error('Solo administradores pueden eliminar puestos');
      } else {
        toast.error('Error al eliminar puesto');
      }
    }
  };
  
  // Abrir modal para nuevo tipo de incidencia
  const handleNuevoTipoIncidencia = () => {
    if (!isAdmin) {
      toast.error('Solo administradores pueden crear tipos de incidencia');
      return;
    }
    setEditingTipoIncidencia(null);
    setFormTipoIncidencia({
      codigo: '',
      descripcion: '',
      categoria: 'Descuento',
      calculo_monto: 'Manual',
      nomipaq_id: '',
      mpro_id: ''
    });
    setModalTipoIncidencia(true);
  };
  
  // Abrir modal para editar tipo de incidencia
  const handleEditarTipoIncidencia = (tipo) => {
    if (!isAdmin) {
      toast.error('Solo administradores pueden editar tipos de incidencia');
      return;
    }
    setEditingTipoIncidencia(tipo);
    setFormTipoIncidencia({
      codigo: tipo.Codigo || '',
      descripcion: tipo.Descripcion || '',
      categoria: tipo.Categoria || 'Descuento',
      calculo_monto: tipo.Calculo_Monto || 'Manual',
      nomipaq_id: tipo.NomiPAQ_ID || '',
      mpro_id: tipo.MPRO_ID || ''
    });
    setModalTipoIncidencia(true);
  };
  
  // Guardar tipo de incidencia
  const handleGuardarTipoIncidencia = async () => {
    if (!formTipoIncidencia.codigo.trim() || !formTipoIncidencia.descripcion.trim()) {
      toast.error('Código y descripción son requeridos');
      return;
    }
    
    setSavingForm(true);
    try {
      const endpoint = editingTipoIncidencia 
        ? `/rrhh/catalogos/tipos-incidencias/${editingTipoIncidencia.TipoIncidenciaID}`
        : '/rrhh/catalogos/tipos-incidencias';
      
      if (editingTipoIncidencia) {
        await api.put(endpoint, formTipoIncidencia);
      } else {
        await api.post(endpoint, formTipoIncidencia);
      }
      
      toast.success(editingTipoIncidencia ? 'Tipo de incidencia actualizado' : 'Tipo de incidencia creado');
      setModalTipoIncidencia(false);
      loadCatalogosCompleto();
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error('Solo administradores pueden realizar esta acción');
      } else {
        toast.error('Error al guardar tipo de incidencia');
      }
    } finally {
      setSavingForm(false);
    }
  };
  
  // Eliminar tipo de incidencia (desactivar)
  const handleEliminarTipoIncidencia = async (tipoId) => {
    if (!isAdmin) {
      toast.error('Solo administradores pueden eliminar tipos de incidencia');
      return;
    }
    if (!window.confirm('¿Está seguro de desactivar este tipo de incidencia?')) return;
    
    try {
      await api.delete(`/rrhh/catalogos/tipos-incidencias/${tipoId}`);
      
      toast.success('Tipo de incidencia desactivado');
      loadCatalogosCompleto();
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error('Solo administradores pueden eliminar tipos');
      } else {
        toast.error('Error al eliminar tipo de incidencia');
      }
    }
  };

  // ===================== FUNCIONES CRUD - FASE 2 =====================
  
  // Abrir modal para nuevo colaborador
  const handleNuevoColaborador = () => {
    setEditingColaborador(null);
    setFormColaborador({
      nombre_completo: '',
      curp: '',
      rfc: '',
      clabe_bancaria: '',
      sucursal_id: '',
      puesto_id: '',
      estatus_laboral: 'Activo'
    });
    setModalColaborador(true);
  };
  
  // Abrir modal para editar colaborador
  const handleEditarColaborador = (col) => {
    setEditingColaborador(col);
    setFormColaborador({
      nombre_completo: col.Nombre_Completo || '',
      curp: col.CURP || '',
      rfc: col.RFC || '',
      clabe_bancaria: col.CLABE_Bancaria || '',
      sucursal_id: col.SucursalID?.toString() || '',
      puesto_id: col.PuestoID?.toString() || '',
      estatus_laboral: col.Estatus_Laboral || 'Activo'
    });
    setModalColaborador(true);
  };
  
  // Guardar colaborador (crear o actualizar)
  const handleGuardarColaborador = async () => {
    if (!formColaborador.nombre_completo || !formColaborador.sucursal_id || !formColaborador.puesto_id) {
      toast.error('Nombre, sucursal y puesto son requeridos');
      return;
    }
    
    setSavingForm(true);
    try {
      const endpoint = editingColaborador 
        ? `/rrhh/colaboradores/${editingColaborador.ColaboradorID}`
        : '/rrhh/colaboradores';
      
      if (editingColaborador) {
        await api.put(endpoint, formColaborador);
      } else {
        await api.post(endpoint, formColaborador);
      }
      
      toast.success(editingColaborador ? 'Colaborador actualizado' : 'Colaborador creado');
      setModalColaborador(false);
      loadColaboradores();
    } catch (error) {
      logger.error('Error:', error);
      toast.error('Error al guardar colaborador');
    } finally {
      setSavingForm(false);
    }
  };
  
  // Ver detalle de colaborador
  const handleVerDetalle = async (col) => {
    setLoadingDetalle(true);
    setModalDetalle(true);
    try {
      const data = await fetchWithAuth(`/rrhh/colaboradores/${col.ColaboradorID}`);
      setDetalleColaborador(data);
    } catch (error) {
      logger.error('Error:', error);
      toast.error('Error al cargar detalle');
    } finally {
      setLoadingDetalle(false);
    }
  };
  
  // Dar de baja colaborador
  const handleDarBaja = async (col) => {
    if (!window.confirm(`¿Seguro que deseas dar de baja a ${col.Nombre_Completo}?`)) return;
    
    try {
      await api.delete(`/rrhh/colaboradores/${col.ColaboradorID}`);
      
      toast.success('Colaborador dado de baja');
      loadColaboradores();
    } catch (error) {
      logger.error('Error:', error);
      toast.error('Error al dar de baja');
    }
  };
  
  // Abrir modal nueva incidencia
  const handleNuevaIncidencia = (colaboradorId = '') => {
    setFormIncidencia({
      colaborador_id: colaboradorId?.toString() || '',
      tipo_incidencia: '',
      monto: 0,
      unidades: 0,
      fecha_incidencia: new Date().toISOString().split('T')[0]
    });
    setModalIncidencia(true);
  };
  
  // Guardar incidencia
  const handleGuardarIncidencia = async () => {
    if (!formIncidencia.colaborador_id || !formIncidencia.tipo_incidencia || !formIncidencia.fecha_incidencia) {
      toast.error('Colaborador, tipo y fecha son requeridos');
      return;
    }
    
    setSavingForm(true);
    try {
      await api.post('/rrhh/incidencias', formIncidencia);
      
      toast.success('Incidencia registrada');
      setModalIncidencia(false);
      loadIncidencias();
    } catch (error) {
      logger.error('Error:', error);
      toast.error('Error al guardar incidencia');
    } finally {
      setSavingForm(false);
    }
  };

  // Tipos de incidencia clasificados por categoría
  const tiposIncidenciaIngresos = [
    { value: 'Bono', label: 'Bono' },
    { value: 'Horas Extra', label: 'Horas Extra' },
    { value: 'Comision', label: 'Comisión' },
    { value: 'Incentivo', label: 'Incentivo' },
    { value: 'Gratificacion', label: 'Gratificación' },
  ];
  
  const tiposIncidenciaDescuentos = [
    { value: 'Falta', label: 'Falta' },
    { value: 'Retardo', label: 'Retardo' },
    { value: 'Descuento', label: 'Descuento' },
    { value: 'Vacaciones', label: 'Vacaciones' },
    { value: 'Incapacidad', label: 'Incapacidad' },
    { value: 'Permiso', label: 'Permiso' },
    { value: 'Prestamo', label: 'Préstamo' },
    { value: 'Otro', label: 'Otro Descuento' },
  ];
  
  // Lista combinada para validación
  const tiposIncidencia = [
    ...tiposIncidenciaIngresos.map(t => t.value), 
    ...tiposIncidenciaDescuentos.map(t => t.value)
  ];
  
  // Función para determinar si es ingreso o descuento
  const esIncidenciaIngreso = (tipo) => tiposIncidenciaIngresos.some(t => t.value === tipo);

  // ===================== FUNCIONES IMPORTAR EXCEL =====================
  
  // Abrir modal importar Excel
  const handleAbrirImportExcel = () => {
    setImportFile(null);
    setImportResult(null);
    setModalImportExcel(true);
  };
  
  // Descargar plantilla Excel - CASO ESPECIAL: Usa api con responseType blob
  const handleDescargarPlantilla = async () => {
    try {
      const response = await api.get('/rrhh/incidencias/plantilla-excel', {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'plantilla_incidencias.xlsx';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('Plantilla descargada');
    } catch (error) {
      logger.error('Error:', error);
      toast.error('Error al descargar plantilla');
    }
  };
  
  // Importar archivo Excel - CASO ESPECIAL: Usa api con FormData
  const handleImportarExcel = async () => {
    if (!importFile) {
      toast.error('Selecciona un archivo Excel');
      return;
    }
    
    setImportLoading(true);
    setImportResult(null);
    
    try {
      const formData = new FormData();
      formData.append('file', importFile);
      
      const response = await api.post('/rrhh/incidencias/importar-excel', formData);
      const data = response.data;
      
      setImportResult(data);
      
      if (data.registros_importados > 0) {
        toast.success(`${data.registros_importados} incidencias importadas`);
        loadIncidencias();
      }
      
      if (data.total_errores > 0) {
        toast.warning(`${data.total_errores} errores encontrados`);
      }
      
    } catch (error) {
      logger.error('Error:', error);
      toast.error(error.response?.data?.detail || error.message || 'Error al importar archivo');
    } finally {
      setImportLoading(false);
    }
  };

  // ===================== FIN FUNCIONES CRUD =====================

  // Tabs config
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: Building2 },
    { id: 'colaboradores', label: 'Colaboradores', icon: Users },
    { id: 'incidencias', label: 'Incidencias', icon: AlertTriangle },
    { id: 'nomina', label: 'Gestión Nóminas', icon: Wallet },
    { id: 'asistencia', label: 'Asistencia', icon: Clock },
    { id: 'reclutamiento', label: 'Reclutamiento', icon: Inbox },
    { id: 'catalogos', label: 'Catálogos', icon: Settings },
  ];

  // FASE 4E: Dashboard extraído a componente separado
  const renderDashboard = () => (
    <RhDashboard 
      dashboard={dashboard} 
      onTabChange={setActiveTab}
    />
  );

  // FASE 4E: Colaboradores extraído a componente separado
  const renderColaboradores = () => (
    <RhColaboradores
      colaboradores={colaboradores}
      sucursales={sucursales}
      filtroBuscar={filtroBuscar}
      setFiltroBuscar={setFiltroBuscar}
      filtroSucursal={filtroSucursal}
      setFiltroSucursal={setFiltroSucursal}
      page={page}
      setPage={setPage}
      totalPages={totalPages}
      loading={loading}
      onRefresh={loadColaboradores}
      onNuevoColaborador={handleNuevoColaborador}
      onVerDetalle={handleVerDetalle}
      onEditarColaborador={handleEditarColaborador}
      onNuevaIncidencia={handleNuevaIncidencia}
      onDarBaja={handleDarBaja}
    />
  );

  // FASE 4E: Incidencias extraído a componente separado
  const renderIncidencias = () => (
    <RhIncidencias
      incidencias={incidencias}
      sucursales={sucursales}
      filtroSucursal={filtroSucursal}
      setFiltroSucursal={setFiltroSucursal}
      esIncidenciaIngreso={esIncidenciaIngreso}
      onAbrirImportExcel={handleAbrirImportExcel}
      onNuevaIncidencia={handleNuevaIncidencia}
    />
  );

  // FASE 4E: Nóminas extraído a componente separado
  const renderFlujoNomina = () => (
    <RhNominas
      // Loading states
      loadingNominas={loadingNominas}
      loadingCaptura={loadingCaptura}
      savingCaptura={savingCaptura}
      savingForm={savingForm}
      // Data
      ciclosNomina={ciclosNomina}
      sucursales={sucursales}
      departamentos={departamentos}
      colaboradoresCaptura={colaboradoresCaptura}
      capturaData={capturaData}
      // Sub-tabs
      nominaSubTab={nominaSubTab}
      setNominaSubTab={setNominaSubTab}
      // Filtros captura
      capturaSemana={capturaSemana}
      setCapturaSemana={setCapturaSemana}
      capturaFiltroSucursal={capturaFiltroSucursal}
      setCapturaFiltroSucursal={setCapturaFiltroSucursal}
      capturaFiltroDepartamento={capturaFiltroDepartamento}
      setCapturaFiltroDepartamento={setCapturaFiltroDepartamento}
      // Config form
      formConfigNomina={formConfigNomina}
      setFormConfigNomina={setFormConfigNomina}
      diasSemana={diasSemana}
      // Constantes
      ETAPAS_NOMINA={ETAPAS_NOMINA}
      SIMBOLOS_INCIDENCIA={SIMBOLOS_INCIDENCIA}
      DIAS_SEMANA_LABELS={DIAS_SEMANA_LABELS}
      DIAS_SEMANA_CAPTURA={DIAS_SEMANA_CAPTURA}
      // Permisos
      isAdmin={isAdmin}
      isSupervisor={isSupervisor}
      // Helpers
      getCiclosPorEtapa={getCiclosPorEtapa}
      calcularTiempoRestante={calcularTiempoRestante}
      calcularTotalesColaborador={calcularTotalesColaborador}
      getSimboloColor={getSimboloColor}
      // Handlers
      loadCiclosNomina={loadCiclosNomina}
      loadColaboradoresCaptura={loadColaboradoresCaptura}
      handleCapturaDiaChange={handleCapturaDiaChange}
      handleGuardarCapturaMasiva={handleGuardarCapturaMasiva}
      handleExportarCapturaExcel={handleExportarCapturaExcel}
      handleGuardarConfigNomina={handleGuardarConfigNomina}
      handleVerMovimientosCiclo={handleVerMovimientosCiclo}
      // Modal handlers
      setModalNuevoCiclo={setModalNuevoCiclo}
      setCicloSeleccionado={setCicloSeleccionado}
      setPasswordAprobacion={setPasswordAprobacion}
      setComentarioAprobacion={setComentarioAprobacion}
      setModalAprobarCiclo={setModalAprobarCiclo}
      setModalHistorialCiclo={setModalHistorialCiclo}
    />
  );

  // FASE 4E: Asistencia extraído a componente separado
  const renderAsistencia = () => <RhAsistencia />;

  // ===================== FUNCIONES RECLUTAMIENTO - FASE 5 =====================
  
  const handleNuevaVacante = () => {
    setEditingVacante(null);
    setFormVacante({
      sucursal_id: '',
      puesto_id: '',
      titulo: '',
      descripcion: '',
      requisitos: '',
      salario_min: 0,
      salario_max: 0,
      tipo_contrato: 'Tiempo Completo'
    });
    setModalVacante(true);
  };

  const handleGuardarVacante = async () => {
    if (!formVacante.sucursal_id || !formVacante.puesto_id || !formVacante.titulo) {
      toast.error('Sucursal, puesto y título son requeridos');
      return;
    }
    
    setSavingForm(true);
    try {
      const endpoint = editingVacante 
        ? `/rrhh/vacantes/${editingVacante.VacanteID}`
        : '/rrhh/vacantes';
      
      if (editingVacante) {
        await api.put(endpoint, formVacante);
      } else {
        await api.post(endpoint, formVacante);
      }
      
      toast.success(editingVacante ? 'Vacante actualizada' : 'Vacante creada');
      setModalVacante(false);
      loadReclutamiento();
    } catch (error) {
      toast.error('Error al guardar vacante');
    } finally {
      setSavingForm(false);
    }
  };

  const handleNuevoCandidato = (vacanteId = '') => {
    setFormCandidato({
      vacante_id: vacanteId?.toString() || '',
      nombre: '',
      email: '',
      telefono: '',
      cv_url: ''
    });
    setModalCandidato(true);
  };

  const handleGuardarCandidato = async () => {
    if (!formCandidato.vacante_id || !formCandidato.nombre || !formCandidato.email) {
      toast.error('Vacante, nombre y email son requeridos');
      return;
    }
    
    setSavingForm(true);
    try {
      await api.post('/rrhh/candidatos', formCandidato);
      
      toast.success('Candidato registrado');
      setModalCandidato(false);
      loadReclutamiento();
    } catch (error) {
      toast.error('Error al guardar candidato');
    } finally {
      setSavingForm(false);
    }
  };

  const handleCambiarEstatusCandidato = async (candidatoId, nuevoEstatus) => {
    try {
      await api.put(`/rrhh/candidatos/${candidatoId}`, { estatus: nuevoEstatus });
      toast.success('Estatus actualizado');
      loadReclutamiento();
    } catch (error) {
      toast.error('Error al actualizar');
    }
  };

  const handleVerScriptRecl = async () => {
    try {
      const data = await fetchWithAuth('/rrhh/reclutamiento/script-inicializacion');
      setScriptRecl(data);
      setModalScriptRecl(true);
    } catch (error) {
      toast.error('Error al obtener script');
    }
  };

  const estatusCandidato = [
    { value: 'Recibido', color: 'bg-zinc-100 text-zinc-700' },
    { value: 'En Revision', color: 'bg-blue-100 text-blue-700' },
    { value: 'Entrevista Programada', color: 'bg-purple-100 text-purple-700' },
    { value: 'Entrevistado', color: 'bg-amber-100 text-amber-700' },
    { value: 'Seleccionado', color: 'bg-green-100 text-green-700' },
    { value: 'Rechazado', color: 'bg-red-100 text-red-700' },
    { value: 'Contratado', color: 'bg-emerald-100 text-emerald-700' },
  ];

  // FASE 4E: Reclutamiento extraído a componente separado
  const renderReclutamiento = () => (
    <RhReclutamiento
      vacantes={vacantes}
      candidatos={candidatos}
      handleVerScriptRecl={handleVerScriptRecl}
      handleNuevoCandidato={handleNuevoCandidato}
      handleNuevaVacante={handleNuevaVacante}
      handleCambiarEstatusCandidato={handleCambiarEstatusCandidato}
      setSelectedVacante={setSelectedVacante}
    />
  );

  // FASE 4E: Catálogos extraído a componente separado
  const renderCatalogos = () => (
    <RhCatalogos
      loadingCatalogos={loadingCatalogos}
      catalogoPuestos={catalogoPuestos}
      catalogoIncidencias={catalogoIncidencias}
      catalogoSubTab={catalogoSubTab}
      setCatalogoSubTab={setCatalogoSubTab}
      isAdmin={isAdmin}
      loadCatalogosCompleto={loadCatalogosCompleto}
      loadScriptCatalogos={loadScriptCatalogos}
      handleNuevoPuesto={handleNuevoPuesto}
      handleEditarPuesto={handleEditarPuesto}
      handleEliminarPuesto={handleEliminarPuesto}
      handleNuevoTipoIncidencia={handleNuevoTipoIncidencia}
      handleEditarTipoIncidencia={handleEditarTipoIncidencia}
      handleEliminarTipoIncidencia={handleEliminarTipoIncidencia}
    />
  );

  return (
    <div className="p-6" data-testid="rrhh-page">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-zinc-800">Recursos Humanos</h1>
        <p className="text-zinc-500">Gestión del capital humano - Conectado a EDARSA HUB</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 overflow-x-auto pb-2">
        {tabs.map(tab => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                activeTab === tab.id 
                  ? 'bg-zinc-900 text-white' 
                  : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200'
              }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Content */}
      {loading && (
        <div className="flex justify-center py-8">
          <RefreshCw className="h-6 w-6 animate-spin text-zinc-400" />
        </div>
      )}

      {!loading && (
        <>
          {activeTab === 'dashboard' && renderDashboard()}
          {activeTab === 'colaboradores' && renderColaboradores()}
          {activeTab === 'incidencias' && renderIncidencias()}
          {activeTab === 'nomina' && renderFlujoNomina()}
          {activeTab === 'asistencia' && renderAsistencia()}
          {activeTab === 'reclutamiento' && renderReclutamiento()}
          {activeTab === 'catalogos' && renderCatalogos()}
        </>
      )}

      {/* ==================== MODALES FASE 2 ==================== */}
      
      {/* Modal Nuevo/Editar Colaborador */}
      {modalColaborador && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-hidden flex flex-col">
            <div className="bg-zinc-800 text-white px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <UserPlus className="h-5 w-5" />
                {editingColaborador ? 'Editar Colaborador' : 'Nuevo Colaborador'}
              </h2>
              <button onClick={() => setModalColaborador(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4 overflow-y-auto">
              <div>
                <Label className="text-sm font-medium">Nombre Completo *</Label>
                <Input
                  value={formColaborador.nombre_completo}
                  onChange={(e) => setFormColaborador({...formColaborador, nombre_completo: e.target.value})}
                  placeholder="Nombre completo del colaborador"
                  className="mt-1"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium">CURP</Label>
                  <Input
                    value={formColaborador.curp}
                    onChange={(e) => setFormColaborador({...formColaborador, curp: e.target.value.toUpperCase()})}
                    placeholder="CURP"
                    maxLength={18}
                    className="mt-1 font-mono"
                  />
                </div>
                <div>
                  <Label className="text-sm font-medium">RFC</Label>
                  <Input
                    value={formColaborador.rfc}
                    onChange={(e) => setFormColaborador({...formColaborador, rfc: e.target.value.toUpperCase()})}
                    placeholder="RFC"
                    maxLength={13}
                    className="mt-1 font-mono"
                  />
                </div>
              </div>
              
              <div>
                <Label className="text-sm font-medium">CLABE Bancaria</Label>
                <Input
                  value={formColaborador.clabe_bancaria}
                  onChange={(e) => setFormColaborador({...formColaborador, clabe_bancaria: e.target.value.replace(/\D/g, '')})}
                  placeholder="18 dígitos"
                  maxLength={18}
                  className="mt-1 font-mono"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium">Sucursal *</Label>
                  <select
                    value={formColaborador.sucursal_id}
                    onChange={(e) => setFormColaborador({...formColaborador, sucursal_id: e.target.value})}
                    className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
                  >
                    <option value="">Seleccionar...</option>
                    {sucursales.map(s => (
                      <option key={s.SucursalID} value={s.SucursalID}>{s.Nombre_Sucursal}</option>
                    ))}
                  </select>
                  <BotonSolicitarAlta tipoCatalogo="sucursales" className="mt-1" />
                </div>
                <div>
                  <Label className="text-sm font-medium">Puesto *</Label>
                  <select
                    value={formColaborador.puesto_id}
                    onChange={(e) => setFormColaborador({...formColaborador, puesto_id: e.target.value})}
                    className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
                  >
                    <option value="">Seleccionar...</option>
                    {puestos.map(p => (
                      <option key={p.PuestoID} value={p.PuestoID}>{p.Nombre_Puesto}</option>
                    ))}
                  </select>
                  <BotonSolicitarAlta tipoCatalogo="puestos" className="mt-1" />
                </div>
              </div>
              
              <div>
                <Label className="text-sm font-medium">Estatus Laboral</Label>
                <select
                  value={formColaborador.estatus_laboral}
                  onChange={(e) => setFormColaborador({...formColaborador, estatus_laboral: e.target.value})}
                  className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
                >
                  <option value="Activo">Activo</option>
                  <option value="Vacaciones">Vacaciones</option>
                  <option value="Incapacidad">Incapacidad</option>
                  <option value="Permiso">Permiso</option>
                  <option value="Baja">Baja</option>
                </select>
              </div>
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end gap-3 bg-zinc-50">
              <Button variant="outline" onClick={() => setModalColaborador(false)}>
                Cancelar
              </Button>
              <Button onClick={handleGuardarColaborador} disabled={savingForm} className="bg-zinc-900 text-white">
                {savingForm ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
                {editingColaborador ? 'Actualizar' : 'Guardar'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Nueva Incidencia */}
      {modalIncidencia && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
            <div className="bg-zinc-800 text-white px-6 py-4 flex items-center justify-between rounded-t-xl">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" />
                Nueva Incidencia
              </h2>
              <button onClick={() => setModalIncidencia(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div>
                <Label className="text-sm font-medium">Colaborador *</Label>
                <select
                  value={formIncidencia.colaborador_id}
                  onChange={(e) => setFormIncidencia({...formIncidencia, colaborador_id: e.target.value})}
                  className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
                >
                  <option value="">Seleccionar colaborador...</option>
                  {colaboradores.map(c => (
                    <option key={c.ColaboradorID} value={c.ColaboradorID}>{c.Nombre_Completo}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <Label className="text-sm font-medium">Tipo de Incidencia *</Label>
                <select
                  value={formIncidencia.tipo_incidencia}
                  onChange={(e) => setFormIncidencia({...formIncidencia, tipo_incidencia: e.target.value})}
                  className={`mt-1 w-full px-3 py-2 border rounded-lg text-sm ${
                    formIncidencia.tipo_incidencia 
                      ? esIncidenciaIngreso(formIncidencia.tipo_incidencia)
                        ? 'border-green-300 bg-green-50'
                        : 'border-red-300 bg-red-50'
                      : ''
                  }`}
                >
                  <option value="">Seleccionar tipo...</option>
                  <optgroup label="➕ INGRESOS (+)" className="font-semibold text-green-700">
                    {tiposIncidenciaIngresos.map(t => (
                      <option key={t.value} value={t.value} className="text-green-700">+ {t.label}</option>
                    ))}
                  </optgroup>
                  <optgroup label="➖ DESCUENTOS (-)" className="font-semibold text-red-700">
                    {tiposIncidenciaDescuentos.map(t => (
                      <option key={t.value} value={t.value} className="text-red-700">- {t.label}</option>
                    ))}
                  </optgroup>
                </select>
                {formIncidencia.tipo_incidencia && (
                  <p className={`mt-1 text-xs font-medium ${esIncidenciaIngreso(formIncidencia.tipo_incidencia) ? 'text-green-600' : 'text-red-600'}`}>
                    {esIncidenciaIngreso(formIncidencia.tipo_incidencia) 
                      ? '✓ Este tipo SUMA al salario del colaborador'
                      : '✓ Este tipo RESTA del salario del colaborador'}
                  </p>
                )}
              </div>
              
              <div>
                <Label className="text-sm font-medium">Fecha *</Label>
                <Input
                  type="date"
                  value={formIncidencia.fecha_incidencia}
                  onChange={(e) => setFormIncidencia({...formIncidencia, fecha_incidencia: e.target.value})}
                  className="mt-1"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium">
                    Monto ($) {formIncidencia.tipo_incidencia && (
                      <span className={esIncidenciaIngreso(formIncidencia.tipo_incidencia) ? 'text-green-600' : 'text-red-600'}>
                        {esIncidenciaIngreso(formIncidencia.tipo_incidencia) ? '(+)' : '(-)'}
                      </span>
                    )}
                  </Label>
                  <Input
                    type="number"
                    value={formIncidencia.monto}
                    onChange={(e) => setFormIncidencia({...formIncidencia, monto: parseFloat(e.target.value) || 0})}
                    className={`mt-1 ${formIncidencia.tipo_incidencia && (esIncidenciaIngreso(formIncidencia.tipo_incidencia) ? 'border-green-300' : 'border-red-300')}`}
                    min="0"
                    step="0.01"
                  />
                </div>
                <div>
                  <Label className="text-sm font-medium">Unidades</Label>
                  <Input
                    type="number"
                    value={formIncidencia.unidades}
                    onChange={(e) => setFormIncidencia({...formIncidencia, unidades: parseFloat(e.target.value) || 0})}
                    className="mt-1"
                    min="0"
                    step="0.5"
                  />
                </div>
              </div>
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end gap-3 bg-zinc-50 rounded-b-xl">
              <Button variant="outline" onClick={() => setModalIncidencia(false)}>
                Cancelar
              </Button>
              <Button onClick={handleGuardarIncidencia} disabled={savingForm} className="bg-zinc-900 text-white">
                {savingForm ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
                Registrar
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Detalle Colaborador */}
      {modalDetalle && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
            <div className="bg-zinc-800 text-white px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Users className="h-5 w-5" />
                Detalle del Colaborador
              </h2>
              <button onClick={() => setModalDetalle(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto flex-1">
              {loadingDetalle ? (
                <div className="flex justify-center py-8">
                  <RefreshCw className="h-8 w-8 animate-spin text-zinc-400" />
                </div>
              ) : detalleColaborador ? (
                <div className="space-y-6">
                  {/* Datos básicos */}
                  <div>
                    <h3 className="text-lg font-semibold mb-3">{detalleColaborador.colaborador?.Nombre_Completo}</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-zinc-500">RFC:</span>
                        <span className="ml-2 font-mono">{detalleColaborador.colaborador?.RFC || '-'}</span>
                      </div>
                      <div>
                        <span className="text-zinc-500">CURP:</span>
                        <span className="ml-2 font-mono">{detalleColaborador.colaborador?.CURP || '-'}</span>
                      </div>
                      <div>
                        <span className="text-zinc-500">Sucursal:</span>
                        <span className="ml-2">{detalleColaborador.colaborador?.Nombre_Sucursal || '-'}</span>
                      </div>
                      <div>
                        <span className="text-zinc-500">Puesto:</span>
                        <span className="ml-2">{detalleColaborador.colaborador?.Puesto || '-'}</span>
                      </div>
                      <div>
                        <span className="text-zinc-500">Estatus:</span>
                        <span className={`ml-2 px-2 py-0.5 rounded text-xs font-medium ${
                          detalleColaborador.colaborador?.Estatus_Laboral === 'Activo' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
                        }`}>
                          {detalleColaborador.colaborador?.Estatus_Laboral}
                        </span>
                      </div>
                      <div>
                        <span className="text-zinc-500">CLABE:</span>
                        <span className="ml-2 font-mono text-xs">{detalleColaborador.colaborador?.CLABE_Bancaria || '-'}</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Incidencias recientes */}
                  <div>
                    <h4 className="font-medium mb-2 flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4" />
                      Últimas Incidencias
                    </h4>
                    {detalleColaborador.incidencias?.length === 0 ? (
                      <p className="text-sm text-zinc-400">Sin incidencias registradas</p>
                    ) : (
                      <div className="border rounded-lg overflow-hidden">
                        <table className="w-full text-sm">
                          <thead className="bg-zinc-50">
                            <tr>
                              <th className="text-left p-2">Tipo</th>
                              <th className="text-left p-2">Fecha</th>
                              <th className="text-right p-2">Monto</th>
                            </tr>
                          </thead>
                          <tbody>
                            {detalleColaborador.incidencias?.slice(0, 5).map((inc) => (
                              <tr key={`det-inc-${inc.Tipo_Incidencia}-${inc.Fecha_Incidencia}`} className="border-t">
                                <td className="p-2">{inc.Tipo_Incidencia}</td>
                                <td className="p-2 text-zinc-500">{inc.Fecha_Incidencia ? new Date(inc.Fecha_Incidencia).toLocaleDateString('es-MX') : '-'}</td>
                                <td className="p-2 text-right">${(inc.Monto || 0).toLocaleString()}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                  
                  {/* Asistencias recientes */}
                  <div>
                    <h4 className="font-medium mb-2 flex items-center gap-2">
                      <Clock className="h-4 w-4" />
                      Últimas Asistencias
                    </h4>
                    {detalleColaborador.asistencias?.length === 0 ? (
                      <p className="text-sm text-zinc-400">Sin registros de asistencia</p>
                    ) : (
                      <div className="border rounded-lg overflow-hidden">
                        <table className="w-full text-sm">
                          <thead className="bg-zinc-50">
                            <tr>
                              <th className="text-left p-2">Fecha/Hora</th>
                              <th className="text-left p-2">Tipo</th>
                            </tr>
                          </thead>
                          <tbody>
                            {detalleColaborador.asistencias?.slice(0, 5).map((a) => (
                              <tr key={`det-asist-${a.FechaHora}-${a.Tipo_Registro}`} className="border-t">
                                <td className="p-2 font-mono text-xs">{a.FechaHora ? new Date(a.FechaHora).toLocaleString('es-MX') : '-'}</td>
                                <td className="p-2">
                                  <span className={`px-2 py-0.5 rounded text-xs ${a.Tipo_Registro === 'Entrada' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                    {a.Tipo_Registro}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <p className="text-center text-zinc-400">No se encontró información</p>
              )}
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end bg-zinc-50">
              <Button variant="outline" onClick={() => setModalDetalle(false)}>
                Cerrar
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Importar Excel */}
      {modalImportExcel && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg">
            <div className="bg-zinc-800 text-white px-6 py-4 flex items-center justify-between rounded-t-xl">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <FileSpreadsheet className="h-5 w-5" />
                Importar Incidencias desde Excel
              </h2>
              <button onClick={() => setModalImportExcel(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              {/* Instrucciones */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm">
                <p className="font-medium text-blue-800 mb-2">Formato del archivo Excel:</p>
                <ul className="list-disc list-inside text-blue-700 space-y-1">
                  <li><strong>Columna A:</strong> RFC o ID del Colaborador</li>
                  <li><strong>Columna B:</strong> Tipo de Incidencia</li>
                  <li><strong>Columna C:</strong> Fecha (DD/MM/YYYY)</li>
                  <li><strong>Columna D:</strong> Monto (opcional)</li>
                  <li><strong>Columna E:</strong> Unidades (opcional)</li>
                </ul>
              </div>
              
              {/* Descargar plantilla */}
              <div className="flex items-center justify-between py-3 border-b">
                <span className="text-sm text-zinc-600">¿No tienes el formato?</span>
                <Button variant="outline" size="sm" onClick={handleDescargarPlantilla}>
                  <FileText className="h-4 w-4 mr-1" />
                  Descargar Plantilla
                </Button>
              </div>
              
              {/* Selección de archivo */}
              <div>
                <Label className="text-sm font-medium">Seleccionar archivo Excel</Label>
                <div className="mt-2">
                  <input
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                    className="block w-full text-sm text-zinc-500
                      file:mr-4 file:py-2 file:px-4
                      file:rounded-lg file:border-0
                      file:text-sm file:font-medium
                      file:bg-zinc-100 file:text-zinc-700
                      hover:file:bg-zinc-200
                      cursor-pointer"
                  />
                </div>
                {importFile && (
                  <p className="mt-2 text-sm text-green-600 flex items-center gap-1">
                    <CheckCircle2 className="h-4 w-4" />
                    {importFile.name}
                  </p>
                )}
              </div>
              
              {/* Resultado de importación */}
              {importResult && (
                <div className={`rounded-lg p-4 ${importResult.total_errores > 0 ? 'bg-amber-50 border border-amber-200' : 'bg-green-50 border border-green-200'}`}>
                  <p className="font-medium text-green-700 mb-2">
                    ✓ {importResult.registros_importados} incidencias importadas
                  </p>
                  
                  {importResult.total_errores > 0 && (
                    <div className="mt-2">
                      <p className="text-amber-700 font-medium text-sm mb-1">
                        ⚠ {importResult.total_errores} errores encontrados:
                      </p>
                      <ul className="text-xs text-amber-600 space-y-1 max-h-32 overflow-y-auto">
                        {importResult.errores.map((err, i) => (
                          <li key={`err-${i}-${err.slice(0, 20)}`}>{err}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end gap-3 bg-zinc-50 rounded-b-xl">
              <Button variant="outline" onClick={() => setModalImportExcel(false)}>
                {importResult ? 'Cerrar' : 'Cancelar'}
              </Button>
              {!importResult && (
                <Button 
                  onClick={handleImportarExcel} 
                  disabled={!importFile || importLoading}
                  className="bg-zinc-900 text-white"
                >
                  {importLoading ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin mr-2" />
                      Procesando...
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4 mr-2" />
                      Importar
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ==================== MODALES RECLUTAMIENTO - FASE 5 ==================== */}
      
      {/* Modal Nueva Vacante */}
      {modalVacante && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-hidden flex flex-col">
            <div className="bg-zinc-800 text-white px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Briefcase className="h-5 w-5" />
                {editingVacante ? 'Editar Vacante' : 'Nueva Vacante'}
              </h2>
              <button onClick={() => setModalVacante(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4 overflow-y-auto">
              <div>
                <Label className="text-sm font-medium">Título del Puesto *</Label>
                <Input
                  value={formVacante.titulo}
                  onChange={(e) => setFormVacante({...formVacante, titulo: e.target.value})}
                  placeholder="Ej: Chef de Partida"
                  className="mt-1"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium">Sucursal *</Label>
                  <select
                    value={formVacante.sucursal_id}
                    onChange={(e) => setFormVacante({...formVacante, sucursal_id: e.target.value})}
                    className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
                  >
                    <option value="">Seleccionar...</option>
                    {sucursales.map(s => (
                      <option key={s.SucursalID} value={s.SucursalID}>{s.Nombre_Sucursal}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label className="text-sm font-medium">Puesto *</Label>
                  <select
                    value={formVacante.puesto_id}
                    onChange={(e) => setFormVacante({...formVacante, puesto_id: e.target.value})}
                    className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
                  >
                    <option value="">Seleccionar...</option>
                    {puestos.map(p => (
                      <option key={p.PuestoID} value={p.PuestoID}>{p.Nombre_Puesto}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div>
                <Label className="text-sm font-medium">Descripción</Label>
                <textarea
                  value={formVacante.descripcion}
                  onChange={(e) => setFormVacante({...formVacante, descripcion: e.target.value})}
                  className="mt-1 w-full px-3 py-2 border rounded-lg text-sm resize-none"
                  rows={3}
                  placeholder="Descripción de las funciones..."
                />
              </div>
              
              <div>
                <Label className="text-sm font-medium">Requisitos</Label>
                <textarea
                  value={formVacante.requisitos}
                  onChange={(e) => setFormVacante({...formVacante, requisitos: e.target.value})}
                  className="mt-1 w-full px-3 py-2 border rounded-lg text-sm resize-none"
                  rows={2}
                  placeholder="Experiencia, habilidades..."
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium">Salario Mínimo</Label>
                  <Input
                    type="number"
                    value={formVacante.salario_min}
                    onChange={(e) => setFormVacante({...formVacante, salario_min: parseFloat(e.target.value) || 0})}
                    className="mt-1"
                    min="0"
                  />
                </div>
                <div>
                  <Label className="text-sm font-medium">Salario Máximo</Label>
                  <Input
                    type="number"
                    value={formVacante.salario_max}
                    onChange={(e) => setFormVacante({...formVacante, salario_max: parseFloat(e.target.value) || 0})}
                    className="mt-1"
                    min="0"
                  />
                </div>
              </div>
              
              <div>
                <Label className="text-sm font-medium">Tipo de Contrato</Label>
                <select
                  value={formVacante.tipo_contrato}
                  onChange={(e) => setFormVacante({...formVacante, tipo_contrato: e.target.value})}
                  className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
                >
                  <option value="Tiempo Completo">Tiempo Completo</option>
                  <option value="Medio Tiempo">Medio Tiempo</option>
                  <option value="Temporal">Temporal</option>
                  <option value="Por Proyecto">Por Proyecto</option>
                </select>
              </div>
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end gap-3 bg-zinc-50">
              <Button variant="outline" onClick={() => setModalVacante(false)}>Cancelar</Button>
              <Button onClick={handleGuardarVacante} disabled={savingForm} className="bg-zinc-900 text-white">
                {savingForm ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
                {editingVacante ? 'Actualizar' : 'Publicar'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Nuevo Candidato */}
      {modalCandidato && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
            <div className="bg-zinc-800 text-white px-6 py-4 flex items-center justify-between rounded-t-xl">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <UserPlus className="h-5 w-5" />
                Nuevo Candidato
              </h2>
              <button onClick={() => setModalCandidato(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div>
                <Label className="text-sm font-medium">Vacante *</Label>
                <select
                  value={formCandidato.vacante_id}
                  onChange={(e) => setFormCandidato({...formCandidato, vacante_id: e.target.value})}
                  className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
                >
                  <option value="">Seleccionar vacante...</option>
                  {vacantes.filter(v => v.Estatus === 'Abierta').map(v => (
                    <option key={v.VacanteID} value={v.VacanteID}>{v.Titulo} - {v.Nombre_Sucursal}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <Label className="text-sm font-medium">Nombre Completo *</Label>
                <Input
                  value={formCandidato.nombre}
                  onChange={(e) => setFormCandidato({...formCandidato, nombre: e.target.value})}
                  placeholder="Nombre del candidato"
                  className="mt-1"
                />
              </div>
              
              <div>
                <Label className="text-sm font-medium">Email *</Label>
                <Input
                  type="email"
                  value={formCandidato.email}
                  onChange={(e) => setFormCandidato({...formCandidato, email: e.target.value})}
                  placeholder="correo@ejemplo.com"
                  className="mt-1"
                />
              </div>
              
              <div>
                <Label className="text-sm font-medium">Teléfono</Label>
                <Input
                  value={formCandidato.telefono}
                  onChange={(e) => setFormCandidato({...formCandidato, telefono: e.target.value})}
                  placeholder="10 dígitos"
                  className="mt-1"
                />
              </div>
              
              <div>
                <Label className="text-sm font-medium">URL del CV</Label>
                <Input
                  value={formCandidato.cv_url}
                  onChange={(e) => setFormCandidato({...formCandidato, cv_url: e.target.value})}
                  placeholder="https://drive.google.com/..."
                  className="mt-1"
                />
              </div>
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end gap-3 bg-zinc-50 rounded-b-xl">
              <Button variant="outline" onClick={() => setModalCandidato(false)}>Cancelar</Button>
              <Button onClick={handleGuardarCandidato} disabled={savingForm} className="bg-zinc-900 text-white">
                {savingForm ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
                Registrar
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Script SQL Reclutamiento */}
      {modalScriptRecl && scriptRecl && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
            <div className="bg-zinc-800 text-white px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Script de Inicialización - Reclutamiento
              </h2>
              <button onClick={() => setModalScriptRecl(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4 overflow-y-auto flex-1">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="font-medium text-blue-800 mb-2">Instrucciones:</p>
                <ol className="list-decimal list-inside text-sm text-blue-700 space-y-1">
                  {scriptRecl.instrucciones?.map((inst, i) => (
                    <li key={`inst-${i}-${inst.slice(0, 15)}`}>{inst}</li>
                  ))}
                </ol>
              </div>
              
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label className="font-medium">Script SQL:</Label>
                  <Button variant="outline" size="sm" onClick={() => {
                    navigator.clipboard.writeText(scriptRecl.script);
                    toast.success('Script copiado');
                  }}>
                    <Copy className="h-4 w-4 mr-1" />
                    Copiar
                  </Button>
                </div>
                <pre className="bg-zinc-900 text-green-400 p-4 rounded-lg text-xs overflow-x-auto max-h-[400px] overflow-y-auto font-mono">
                  {scriptRecl.script}
                </pre>
              </div>
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end bg-zinc-50">
              <Button variant="outline" onClick={() => setModalScriptRecl(false)}>Cerrar</Button>
            </div>
          </div>
        </div>
      )}

      {/* ==================== MODALES CATÁLOGOS RRHH ==================== */}
      
      {/* Modal Nuevo/Editar Puesto */}
      {modalPuesto && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-hidden flex flex-col">
            <div className="bg-zinc-800 text-white px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Briefcase className="h-5 w-5" />
                {editingPuesto ? 'Editar Puesto' : 'Nuevo Puesto'}
              </h2>
              <button onClick={() => setModalPuesto(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4 overflow-y-auto flex-1">
              <div className="space-y-2">
                <Label htmlFor="puesto-descripcion">Descripción del Puesto *</Label>
                <Input
                  id="puesto-descripcion"
                  value={formPuesto.descripcion}
                  onChange={(e) => setFormPuesto({...formPuesto, descripcion: e.target.value})}
                  placeholder="Ej: Gerente de Operaciones"
                  data-testid="input-puesto-descripcion"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="puesto-departamento">Departamento</Label>
                <Input
                  id="puesto-departamento"
                  value={formPuesto.departamento}
                  onChange={(e) => setFormPuesto({...formPuesto, departamento: e.target.value})}
                  placeholder="Ej: Administración, Cocina, Servicio"
                  data-testid="input-puesto-departamento"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="puesto-sueldo">Sueldo Base Semanal (SBC)</Label>
                <Input
                  id="puesto-sueldo"
                  type="number"
                  value={formPuesto.sueldo_base}
                  onChange={(e) => setFormPuesto({...formPuesto, sueldo_base: parseFloat(e.target.value) || 0})}
                  placeholder="0.00"
                  data-testid="input-puesto-sueldo"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="puesto-nomipaq">ID NomiPAQ</Label>
                  <Input
                    id="puesto-nomipaq"
                    value={formPuesto.nomipaq_id}
                    onChange={(e) => setFormPuesto({...formPuesto, nomipaq_id: e.target.value})}
                    placeholder="Código NomiPAQ"
                    data-testid="input-puesto-nomipaq"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="puesto-mpro">ID MPRO</Label>
                  <Input
                    id="puesto-mpro"
                    value={formPuesto.mpro_id}
                    onChange={(e) => setFormPuesto({...formPuesto, mpro_id: e.target.value})}
                    placeholder="Código MPRO"
                    data-testid="input-puesto-mpro"
                  />
                </div>
              </div>
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end gap-2 bg-zinc-50">
              <Button variant="outline" onClick={() => setModalPuesto(false)}>Cancelar</Button>
              <Button onClick={handleGuardarPuesto} disabled={savingForm} data-testid="btn-guardar-puesto">
                {savingForm ? <RefreshCw className="h-4 w-4 animate-spin mr-1" /> : <Save className="h-4 w-4 mr-1" />}
                {editingPuesto ? 'Actualizar' : 'Guardar'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Nuevo/Editar Tipo de Incidencia */}
      {modalTipoIncidencia && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-hidden flex flex-col">
            <div className="bg-zinc-800 text-white px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Tag className="h-5 w-5" />
                {editingTipoIncidencia ? 'Editar Tipo de Incidencia' : 'Nuevo Tipo de Incidencia'}
              </h2>
              <button onClick={() => setModalTipoIncidencia(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4 overflow-y-auto flex-1">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="tipo-codigo">Código *</Label>
                  <Input
                    id="tipo-codigo"
                    value={formTipoIncidencia.codigo}
                    onChange={(e) => setFormTipoIncidencia({...formTipoIncidencia, codigo: e.target.value.toUpperCase()})}
                    placeholder="Ej: BON, FAL, HEX"
                    maxLength={10}
                    data-testid="input-tipo-codigo"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="tipo-categoria">Categoría *</Label>
                  <select
                    id="tipo-categoria"
                    value={formTipoIncidencia.categoria}
                    onChange={(e) => setFormTipoIncidencia({...formTipoIncidencia, categoria: e.target.value})}
                    className="w-full h-10 px-3 border rounded-md bg-white text-sm"
                    data-testid="select-tipo-categoria"
                  >
                    <option value="Ingreso">+ Ingreso</option>
                    <option value="Descuento">- Descuento</option>
                  </select>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="tipo-descripcion">Descripción *</Label>
                <Input
                  id="tipo-descripcion"
                  value={formTipoIncidencia.descripcion}
                  onChange={(e) => setFormTipoIncidencia({...formTipoIncidencia, descripcion: e.target.value})}
                  placeholder="Ej: Bono de productividad"
                  data-testid="input-tipo-descripcion"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="tipo-calculo">Tipo de Cálculo</Label>
                <select
                  id="tipo-calculo"
                  value={formTipoIncidencia.calculo_monto}
                  onChange={(e) => setFormTipoIncidencia({...formTipoIncidencia, calculo_monto: e.target.value})}
                  className="w-full h-10 px-3 border rounded-md bg-white text-sm"
                  data-testid="select-tipo-calculo"
                >
                  <option value="Manual">Manual</option>
                  <option value="Porcentaje">Porcentaje</option>
                  <option value="Formula">Fórmula</option>
                </select>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="tipo-nomipaq">ID NomiPAQ</Label>
                  <Input
                    id="tipo-nomipaq"
                    value={formTipoIncidencia.nomipaq_id}
                    onChange={(e) => setFormTipoIncidencia({...formTipoIncidencia, nomipaq_id: e.target.value})}
                    placeholder="Concepto NomiPAQ"
                    data-testid="input-tipo-nomipaq"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="tipo-mpro">ID MPRO</Label>
                  <Input
                    id="tipo-mpro"
                    value={formTipoIncidencia.mpro_id}
                    onChange={(e) => setFormTipoIncidencia({...formTipoIncidencia, mpro_id: e.target.value})}
                    placeholder="Código MPRO"
                    data-testid="input-tipo-mpro"
                  />
                </div>
              </div>
              
              {/* Preview de la categoría */}
              <div className={`p-3 rounded-lg border ${
                formTipoIncidencia.categoria === 'Ingreso' 
                  ? 'bg-green-50 border-green-200' 
                  : 'bg-red-50 border-red-200'
              }`}>
                <p className={`text-sm font-medium ${
                  formTipoIncidencia.categoria === 'Ingreso' ? 'text-green-700' : 'text-red-700'
                }`}>
                  {formTipoIncidencia.categoria === 'Ingreso' 
                    ? '✓ Esta incidencia SUMA al sueldo del colaborador' 
                    : '✗ Esta incidencia RESTA al sueldo del colaborador'}
                </p>
              </div>
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end gap-2 bg-zinc-50">
              <Button variant="outline" onClick={() => setModalTipoIncidencia(false)}>Cancelar</Button>
              <Button onClick={handleGuardarTipoIncidencia} disabled={savingForm} data-testid="btn-guardar-tipo">
                {savingForm ? <RefreshCw className="h-4 w-4 animate-spin mr-1" /> : <Save className="h-4 w-4 mr-1" />}
                {editingTipoIncidencia ? 'Actualizar' : 'Guardar'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Script SQL Catálogos RRHH */}
      {modalScriptCatalogos && scriptCatalogos && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
            <div className="bg-zinc-800 text-white px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Database className="h-5 w-5" />
                Script de Inicialización - Catálogos RRHH
              </h2>
              <button onClick={() => setModalScriptCatalogos(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4 overflow-y-auto flex-1">
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <p className="font-medium text-amber-800 mb-2">Instrucciones importantes:</p>
                <ol className="list-decimal list-inside text-sm text-amber-700 space-y-1">
                  <li>Ejecute este script en la base de datos <strong>EDARSA HUB</strong></li>
                  <li>El script verifica si las tablas/columnas ya existen antes de crearlas</li>
                  <li>Crea columnas de mapeo para NomiPAQ y MPRO</li>
                  <li>Inserta tipos de incidencias por defecto si la tabla está vacía</li>
                </ol>
              </div>
              
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label className="font-medium">Script SQL:</Label>
                  <Button variant="outline" size="sm" onClick={() => {
                    navigator.clipboard.writeText(scriptCatalogos.script);
                    toast.success('Script copiado al portapapeles');
                  }}>
                    <Copy className="h-4 w-4 mr-1" />
                    Copiar Script
                  </Button>
                </div>
                <pre className="bg-zinc-900 text-green-400 p-4 rounded-lg text-xs overflow-x-auto max-h-[400px] overflow-y-auto font-mono whitespace-pre-wrap">
                  {scriptCatalogos.script}
                </pre>
              </div>
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end bg-zinc-50">
              <Button variant="outline" onClick={() => setModalScriptCatalogos(false)}>Cerrar</Button>
            </div>
          </div>
        </div>
      )}

      {/* ============= MODALES MÓDULO NÓMINAS ============= */}
      
      {/* Modal Nuevo Ciclo */}
      {modalNuevoCiclo && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
            <div className="bg-zinc-800 text-white px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Nuevo Ciclo de Nómina</h2>
              <button onClick={() => setModalNuevoCiclo(false)} className="p-1 hover:bg-white/20 rounded"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <Label>Sucursal *</Label>
                <select value={formNuevoCiclo.sucursal_id} onChange={(e) => setFormNuevoCiclo({...formNuevoCiclo, sucursal_id: e.target.value})} className="w-full border border-zinc-300 rounded-lg px-3 py-2 mt-1 bg-white text-zinc-900">
                  <option value="">Seleccione sucursal</option>
                  {sucursales.map(s => <option key={s.SucursalID} value={s.SucursalID}>{s.Nombre_Sucursal}</option>)}
                </select>
              </div>
              <div>
                <Label>Fecha de Corte *</Label>
                <Input type="date" value={formNuevoCiclo.fecha_corte} onChange={(e) => setFormNuevoCiclo({...formNuevoCiclo, fecha_corte: e.target.value})} className="mt-1" />
              </div>
              <div>
                <Label>Tipo de Nómina</Label>
                <select value={formNuevoCiclo.tipo_nomina} onChange={(e) => setFormNuevoCiclo({...formNuevoCiclo, tipo_nomina: e.target.value})} className="w-full border border-zinc-300 rounded-lg px-3 py-2 mt-1 bg-white text-zinc-900">
                  <option value="quincenal">Quincenal</option>
                  <option value="semanal">Semanal</option>
                  <option value="mensual">Mensual</option>
                </select>
              </div>
              <div>
                <Label>Notas</Label>
                <textarea value={formNuevoCiclo.notas} onChange={(e) => setFormNuevoCiclo({...formNuevoCiclo, notas: e.target.value})} className="w-full border rounded-lg px-3 py-2 mt-1 min-h-[60px]" placeholder="Observaciones..." />
              </div>
            </div>
            <div className="border-t px-6 py-4 flex justify-end gap-2 bg-zinc-50">
              <Button variant="outline" onClick={() => setModalNuevoCiclo(false)}>Cancelar</Button>
              <Button onClick={handleCrearCicloNomina} disabled={savingForm}>
                {savingForm ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <Plus className="h-4 w-4 mr-2" />}Crear
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Aprobar/Avanzar */}
      {modalAprobarCiclo && cicloSeleccionado && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
            <div className="bg-green-600 text-white px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2"><Lock className="h-5 w-5" />Autorizar Avance</h2>
              <button onClick={() => setModalAprobarCiclo(false)} className="p-1 hover:bg-white/20 rounded"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-6 space-y-4">
              <div className="p-4 bg-zinc-100 rounded-lg">
                <p className="text-sm"><strong>Sucursal:</strong> {cicloSeleccionado.sucursal_nombre}</p>
                <p className="text-sm"><strong>Etapa actual:</strong> {ETAPAS_NOMINA.find(e => e.id === cicloSeleccionado.etapa_actual)?.nombre}</p>
              </div>
              <div>
                <Label className="flex items-center gap-2"><Lock className="h-4 w-4" />Contraseña de Autorización *</Label>
                <Input type="password" value={passwordAprobacion} onChange={(e) => setPasswordAprobacion(e.target.value)} placeholder="Ingrese su contraseña" className="mt-1" />
              </div>
              <div>
                <Label>Comentario (opcional)</Label>
                <textarea value={comentarioAprobacion} onChange={(e) => setComentarioAprobacion(e.target.value)} className="w-full border border-zinc-300 rounded-lg px-3 py-2 mt-1 bg-white text-zinc-900" placeholder="Observaciones..." />
              </div>
            </div>
            <div className="border-t px-6 py-4 flex justify-end gap-2 bg-zinc-50">
              <Button variant="outline" className="text-red-600 border-red-200 hover:bg-red-50" onClick={() => { setModalAprobarCiclo(false); setMotivoRechazo(''); setModalRechazarCiclo(true); }}>
                <RotateCcw className="h-4 w-4 mr-1" />Devolver
              </Button>
              <Button onClick={handleAvanzarCiclo} disabled={savingForm || !passwordAprobacion} className="bg-green-600 hover:bg-green-700">
                {savingForm ? <RefreshCw className="h-4 w-4 animate-spin mr-1" /> : <ArrowRight className="h-4 w-4 mr-1" />}Avanzar
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Rechazar */}
      {modalRechazarCiclo && cicloSeleccionado && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
            <div className="bg-red-600 text-white px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2"><RotateCcw className="h-5 w-5" />Devolver para Corrección</h2>
              <button onClick={() => setModalRechazarCiclo(false)} className="p-1 hover:bg-white/20 rounded"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-6 space-y-4">
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-800">La nómina será devuelta a <strong>Validación RH</strong> para correcciones.</p>
              </div>
              <div>
                <Label>Motivo del Rechazo *</Label>
                <textarea value={motivoRechazo} onChange={(e) => setMotivoRechazo(e.target.value)} className="w-full border border-red-200 rounded-lg px-3 py-2 mt-1 min-h-[80px]" placeholder="Describa el motivo..." />
              </div>
            </div>
            <div className="border-t px-6 py-4 flex justify-end gap-2 bg-zinc-50">
              <Button variant="outline" onClick={() => setModalRechazarCiclo(false)}>Cancelar</Button>
              <Button onClick={handleRechazarCiclo} disabled={savingForm || !motivoRechazo} className="bg-red-600 hover:bg-red-700">
                {savingForm ? <RefreshCw className="h-4 w-4 animate-spin mr-1" /> : <RotateCcw className="h-4 w-4 mr-1" />}Devolver
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Historial */}
      {modalHistorialCiclo && cicloSeleccionado && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
            <div className="bg-zinc-800 text-white px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2"><History className="h-5 w-5" />Historial de Trazabilidad</h2>
              <button onClick={() => setModalHistorialCiclo(false)} className="p-1 hover:bg-white/20 rounded"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-6 overflow-y-auto flex-1">
              <div className="mb-4 p-3 bg-zinc-100 rounded-lg">
                <p className="text-sm"><strong>Sucursal:</strong> {cicloSeleccionado.sucursal_nombre}</p>
                <p className="text-sm"><strong>Fecha Corte:</strong> {new Date(cicloSeleccionado.fecha_corte).toLocaleDateString()}</p>
              </div>
              {(cicloSeleccionado.historial || []).length === 0 ? (
                <div className="text-center py-8 text-zinc-500"><History className="h-12 w-12 mx-auto mb-2 opacity-50" /><p>Sin eventos registrados</p></div>
              ) : (
                <div className="relative">
                  <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-zinc-200"></div>
                  <div className="space-y-4">
                    {(cicloSeleccionado.historial || []).map((evento, idx) => (
                      <div key={evento.id || idx} className="relative pl-10">
                        <div className={`absolute left-2 w-4 h-4 rounded-full ${getEventoBgClass(evento.tipo)}`}></div>
                        <div className="bg-white border rounded-lg p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-medium text-sm">{evento.accion}</span>
                            <span className="text-xs text-zinc-500">{new Date(evento.timestamp).toLocaleString()}</span>
                          </div>
                          <p className="text-sm text-zinc-600">{evento.descripcion}</p>
                          <p className="text-xs text-zinc-400 mt-1">Por: {evento.usuario_nombre || evento.usuario_email}</p>
                          {evento.comentario && <p className="text-xs text-zinc-500 mt-1 italic">"{evento.comentario}"</p>}
                          {evento.motivo && <p className="text-xs text-red-500 mt-1">Motivo: {evento.motivo}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal Movimientos */}
      {modalMovimientos && cicloSeleccionado && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
            <div className="bg-zinc-800 text-white px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2"><FileText className="h-5 w-5" />Movimientos de Nómina</h2>
              <button onClick={() => setModalMovimientos(false)} className="p-1 hover:bg-white/20 rounded"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-6 overflow-y-auto flex-1">
              <div className="mb-4 p-3 bg-zinc-100 rounded-lg">
                <p className="text-sm"><strong>Sucursal:</strong> {cicloSeleccionado.sucursal_nombre}</p>
                <p className="text-sm"><strong>Etapa:</strong> {ETAPAS_NOMINA.find(e => e.id === cicloSeleccionado.etapa_actual)?.nombre}</p>
              </div>
              {movimientosCiclo.length === 0 ? (
                <div className="text-center py-8 text-zinc-500"><FileText className="h-12 w-12 mx-auto mb-2 opacity-50" /><p>Sin movimientos registrados</p></div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-zinc-50 border-b">
                      <tr>
                        <th className="text-left py-2 px-3 font-medium text-zinc-500">Colaborador</th>
                        <th className="text-left py-2 px-3 font-medium text-zinc-500">Tipo</th>
                        <th className="text-right py-2 px-3 font-medium text-zinc-500">Monto</th>
                        <th className="text-right py-2 px-3 font-medium text-zinc-500">Unidades</th>
                        <th className="text-left py-2 px-3 font-medium text-zinc-500">Notas</th>
                      </tr>
                    </thead>
                    <tbody>
                      {movimientosCiclo.map((mov, idx) => (
                        <tr key={mov.id || idx} className="border-b hover:bg-zinc-50">
                          <td className="py-2 px-3 font-medium">{mov.colaborador_nombre}</td>
                          <td className="py-2 px-3"><span className={`px-2 py-1 rounded text-xs ${mov.categoria === 'Ingreso' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>{mov.tipo_incidencia}</span></td>
                          <td className="py-2 px-3 text-right font-mono">${(mov.monto || 0).toLocaleString()}</td>
                          <td className="py-2 px-3 text-right">{mov.unidades || '-'}</td>
                          <td className="py-2 px-3 text-zinc-500 text-xs">{mov.notas || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
