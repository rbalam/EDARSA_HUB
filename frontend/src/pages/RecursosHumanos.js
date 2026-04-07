import React, { useState, useEffect, useCallback } from 'react';
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
  Target, ClipboardList, Send, History
} from 'lucide-react';
import { toast } from 'sonner';

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
  const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
  const isAdmin = currentUser?.role === 'Administrador' || currentUser?.role === 'admin';
  
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

  const token = localStorage.getItem('token');

  const fetchWithAuth = useCallback(async (url) => {
    const response = await fetch(`${API_URL}${url}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error('Error en la petición');
    return response.json();
  }, [token]);

  // Cargar dashboard
  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchWithAuth('/api/rrhh/dashboard');
      setDashboard(data);
    } catch (error) {
      console.error('Error cargando dashboard:', error);
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth]);

  // Cargar catálogos
  const loadCatalogos = useCallback(async () => {
    try {
      const [sucData, puestosData] = await Promise.all([
        fetchWithAuth('/api/rrhh/catalogos/sucursales'),
        fetchWithAuth('/api/rrhh/catalogos/puestos')
      ]);
      setSucursales(sucData.sucursales || []);
      setPuestos(puestosData.puestos || []);
    } catch (error) {
      console.error('Error cargando catálogos:', error);
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
      console.error('Error cargando colaboradores:', error);
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
      console.error('Error cargando incidencias:', error);
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
      console.error('Error cargando flujos:', error);
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
        fetchWithAuth('/api/nomina/ciclos'),
        fetchWithAuth('/api/nomina/configuracion')
      ]);
      setCiclosNomina(ciclosData.ciclos || []);
      setConfigNomina(configData.configuracion);
      if (configData.configuracion) {
        setFormConfigNomina({
          dia_corte: configData.configuracion.dia_corte || 0,
          dia_pago: configData.configuracion.dia_pago || 1,
          horario_headcount: configData.configuracion.horario_headcount || '10:00',
          horario_maquilador: configData.configuracion.horario_maquilador || '12:00',
          horario_tesoreria: configData.configuracion.horario_tesoreria || '14:00'
        });
      }
    } catch (error) {
      console.error('Error cargando nóminas:', error);
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
      const response = await fetch(`${API_URL}/api/nomina/ciclos`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(formNuevoCiclo)
      });
      if (!response.ok) throw new Error('Error al crear ciclo');
      toast.success('Ciclo de nómina creado correctamente');
      setModalNuevoCiclo(false);
      setFormNuevoCiclo({ sucursal_id: '', fecha_corte: '', tipo_nomina: 'quincenal', notas: '' });
      loadCiclosNomina();
    } catch (error) {
      toast.error(error.message);
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
      const response = await fetch(`${API_URL}/api/nomina/ciclos/${cicloSeleccionado.id}/avanzar`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: passwordAprobacion, comentario: comentarioAprobacion })
      });
      if (response.status === 401) { toast.error('Contraseña incorrecta'); return; }
      if (!response.ok) throw new Error('Error al avanzar etapa');
      const data = await response.json();
      toast.success(data.message || 'Etapa avanzada correctamente');
      setModalAprobarCiclo(false);
      setPasswordAprobacion('');
      setComentarioAprobacion('');
      loadCiclosNomina();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setSavingForm(false);
    }
  };
  
  const handleRechazarCiclo = async () => {
    if (!motivoRechazo) { toast.error('Ingrese el motivo del rechazo'); return; }
    setSavingForm(true);
    try {
      const response = await fetch(`${API_URL}/api/nomina/ciclos/${cicloSeleccionado.id}/rechazar`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ motivo: motivoRechazo })
      });
      if (!response.ok) throw new Error('Error al rechazar');
      toast.success('Nómina devuelta para corrección');
      setModalRechazarCiclo(false);
      setMotivoRechazo('');
      loadCiclosNomina();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setSavingForm(false);
    }
  };
  
  const handleVerMovimientosCiclo = async (ciclo) => {
    setCicloSeleccionado(ciclo);
    try {
      const data = await fetchWithAuth(`/api/nomina/ciclos/${ciclo.id}/movimientos`);
      setMovimientosCiclo(data.movimientos || []);
      setModalMovimientos(true);
    } catch (error) {
      toast.error('Error cargando movimientos');
    }
  };
  
  const handleGuardarConfigNomina = async () => {
    setSavingForm(true);
    try {
      const response = await fetch(`${API_URL}/api/nomina/configuracion`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(formConfigNomina)
      });
      if (!response.ok) throw new Error('Error al guardar');
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

  // Cargar datos de reclutamiento
  const loadReclutamiento = useCallback(async () => {
    try {
      setLoading(true);
      const [dashData, vacData, candData] = await Promise.all([
        fetchWithAuth('/api/rrhh/reclutamiento/dashboard'),
        fetchWithAuth('/api/rrhh/vacantes'),
        fetchWithAuth('/api/rrhh/candidatos')
      ]);
      setReclutamientoDash(dashData);
      setVacantes(vacData.vacantes || []);
      setCandidatos(candData.candidatos || []);
    } catch (error) {
      console.error('Error cargando reclutamiento:', error);
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
        fetchWithAuth('/api/rrhh/catalogos/puestos'),
        fetchWithAuth('/api/rrhh/catalogos/tipos-incidencias')
      ]);
      setCatalogoPuestos(puestosData.puestos || []);
      setCatalogoIncidencias(incidenciasData.tipos_incidencias || []);
    } catch (error) {
      console.error('Error cargando catálogos:', error);
      toast.error('Error cargando catálogos');
    } finally {
      setLoadingCatalogos(false);
    }
  }, [fetchWithAuth]);
  
  // Cargar script SQL de catálogos
  const loadScriptCatalogos = async () => {
    try {
      const data = await fetchWithAuth('/api/rrhh/catalogos/script-inicializacion');
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
      const url = editingPuesto 
        ? `${API_URL}/api/rrhh/catalogos/puestos/${editingPuesto.PuestoID}`
        : `${API_URL}/api/rrhh/catalogos/puestos`;
      
      const response = await fetch(url, {
        method: editingPuesto ? 'PUT' : 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formPuesto)
      });
      
      if (response.status === 403) {
        toast.error('Solo administradores pueden realizar esta acción');
        return;
      }
      if (!response.ok) throw new Error('Error al guardar');
      
      toast.success(editingPuesto ? 'Puesto actualizado' : 'Puesto creado');
      setModalPuesto(false);
      loadCatalogosCompleto();
    } catch (error) {
      toast.error('Error al guardar puesto');
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
      const response = await fetch(`${API_URL}/api/rrhh/catalogos/puestos/${puestoId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.status === 403) {
        toast.error('Solo administradores pueden eliminar puestos');
        return;
      }
      if (!response.ok) throw new Error('Error al eliminar');
      
      toast.success('Puesto eliminado');
      loadCatalogosCompleto();
    } catch (error) {
      toast.error('Error al eliminar puesto');
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
      const url = editingTipoIncidencia 
        ? `${API_URL}/api/rrhh/catalogos/tipos-incidencias/${editingTipoIncidencia.TipoIncidenciaID}`
        : `${API_URL}/api/rrhh/catalogos/tipos-incidencias`;
      
      const response = await fetch(url, {
        method: editingTipoIncidencia ? 'PUT' : 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formTipoIncidencia)
      });
      
      if (response.status === 403) {
        toast.error('Solo administradores pueden realizar esta acción');
        return;
      }
      if (!response.ok) throw new Error('Error al guardar');
      
      toast.success(editingTipoIncidencia ? 'Tipo de incidencia actualizado' : 'Tipo de incidencia creado');
      setModalTipoIncidencia(false);
      loadCatalogosCompleto();
    } catch (error) {
      toast.error('Error al guardar tipo de incidencia');
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
      const response = await fetch(`${API_URL}/api/rrhh/catalogos/tipos-incidencias/${tipoId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.status === 403) {
        toast.error('Solo administradores pueden eliminar tipos');
        return;
      }
      if (!response.ok) throw new Error('Error al eliminar');
      
      toast.success('Tipo de incidencia desactivado');
      loadCatalogosCompleto();
    } catch (error) {
      toast.error('Error al eliminar tipo de incidencia');
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
      const url = editingColaborador 
        ? `${API_URL}/api/rrhh/colaboradores/${editingColaborador.ColaboradorID}`
        : `${API_URL}/api/rrhh/colaboradores`;
      
      const method = editingColaborador ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formColaborador)
      });
      
      if (!response.ok) throw new Error('Error al guardar');
      
      toast.success(editingColaborador ? 'Colaborador actualizado' : 'Colaborador creado');
      setModalColaborador(false);
      loadColaboradores();
    } catch (error) {
      console.error('Error:', error);
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
      const data = await fetchWithAuth(`/api/rrhh/colaboradores/${col.ColaboradorID}`);
      setDetalleColaborador(data);
    } catch (error) {
      console.error('Error:', error);
      toast.error('Error al cargar detalle');
    } finally {
      setLoadingDetalle(false);
    }
  };
  
  // Dar de baja colaborador
  const handleDarBaja = async (col) => {
    if (!window.confirm(`¿Seguro que deseas dar de baja a ${col.Nombre_Completo}?`)) return;
    
    try {
      const response = await fetch(`${API_URL}/api/rrhh/colaboradores/${col.ColaboradorID}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) throw new Error('Error al dar de baja');
      
      toast.success('Colaborador dado de baja');
      loadColaboradores();
    } catch (error) {
      console.error('Error:', error);
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
      const response = await fetch(`${API_URL}/api/rrhh/incidencias`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formIncidencia)
      });
      
      if (!response.ok) throw new Error('Error al guardar');
      
      toast.success('Incidencia registrada');
      setModalIncidencia(false);
      loadIncidencias();
    } catch (error) {
      console.error('Error:', error);
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
  
  // Descargar plantilla Excel
  const handleDescargarPlantilla = async () => {
    try {
      const response = await fetch(`${API_URL}/api/rrhh/incidencias/plantilla-excel`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) throw new Error('Error al descargar');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'plantilla_incidencias.xlsx';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('Plantilla descargada');
    } catch (error) {
      console.error('Error:', error);
      toast.error('Error al descargar plantilla');
    }
  };
  
  // Importar archivo Excel
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
      
      const response = await fetch(`${API_URL}/api/rrhh/incidencias/importar-excel`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Error al importar');
      }
      
      setImportResult(data);
      
      if (data.registros_importados > 0) {
        toast.success(`${data.registros_importados} incidencias importadas`);
        loadIncidencias();
      }
      
      if (data.total_errores > 0) {
        toast.warning(`${data.total_errores} errores encontrados`);
      }
      
    } catch (error) {
      console.error('Error:', error);
      toast.error(error.message || 'Error al importar archivo');
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

  // Render Dashboard
  const renderDashboard = () => {
    const resumen = dashboard?.resumen || {};
    const porDepto = dashboard?.por_departamento || [];
    const incMes = dashboard?.incidencias_mes || [];
    const flujosPend = dashboard?.flujos_pendientes || [];
    const alertas = dashboard?.alertas_fraude || 0;

    return (
      <div className="space-y-6">
        {/* KPIs */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-blue-100 text-xs">Total</p>
                  <p className="text-2xl font-bold">{resumen.total || 0}</p>
                </div>
                <Users className="h-8 w-8 text-blue-200" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-green-100 text-xs">Activos</p>
                  <p className="text-2xl font-bold">{resumen.activos || 0}</p>
                </div>
                <CheckCircle2 className="h-8 w-8 text-green-200" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-amber-500 to-amber-600 text-white">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-amber-100 text-xs">Vacaciones</p>
                  <p className="text-2xl font-bold">{resumen.vacaciones || 0}</p>
                </div>
                <Calendar className="h-8 w-8 text-amber-200" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-100 text-xs">Incapacidad</p>
                  <p className="text-2xl font-bold">{resumen.incapacidad || 0}</p>
                </div>
                <FileText className="h-8 w-8 text-purple-200" />
              </div>
            </CardContent>
          </Card>
          
          <Card className={`${alertas > 0 ? 'bg-gradient-to-br from-red-500 to-red-600' : 'bg-gradient-to-br from-zinc-500 to-zinc-600'} text-white`}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-red-100 text-xs">Alertas Fraude</p>
                  <p className="text-2xl font-bold">{alertas}</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-red-200" />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Por departamento */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Briefcase className="h-4 w-4" />
                Por Departamento
              </CardTitle>
            </CardHeader>
            <CardContent>
              {porDepto.length === 0 ? (
                <p className="text-sm text-zinc-400 text-center py-4">Sin datos</p>
              ) : (
                <div className="space-y-2">
                  {porDepto.map((d, i) => (
                    <div key={i} className="flex items-center justify-between py-2 border-b last:border-0">
                      <span className="text-sm">{d.Departamento}</span>
                      <span className="font-medium">{d.total}</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Incidencias del mes */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Incidencias del Mes
              </CardTitle>
            </CardHeader>
            <CardContent>
              {incMes.length === 0 ? (
                <p className="text-sm text-zinc-400 text-center py-4">Sin incidencias este mes</p>
              ) : (
                <div className="space-y-2">
                  {incMes.map((inc, i) => (
                    <div key={i} className="flex items-center justify-between py-2 border-b last:border-0">
                      <span className="text-sm">{inc.Tipo_Incidencia}</span>
                      <div className="text-right">
                        <span className="font-medium">{inc.cantidad}</span>
                        {inc.monto_total > 0 && (
                          <span className="text-xs text-zinc-500 ml-2">
                            ${(inc.monto_total || 0).toLocaleString()}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Flujos pendientes */}
          <Card className="md:col-span-2">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Wallet className="h-4 w-4" />
                Flujos de Nómina Pendientes
              </CardTitle>
            </CardHeader>
            <CardContent>
              {flujosPend.length === 0 ? (
                <p className="text-sm text-zinc-400 text-center py-4">Todos los flujos han sido procesados</p>
              ) : (
                <div className="flex flex-wrap gap-3">
                  {flujosPend.map((f, i) => (
                    <div key={i} className="px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg">
                      <span className="text-sm font-medium text-amber-700">{f.Estatus_Flujo}</span>
                      <span className="ml-2 text-amber-600">({f.cantidad})</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    );
  };

  // Render Colaboradores
  const renderColaboradores = () => (
    <div className="space-y-4">
      {/* Filtros */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
          <Input
            placeholder="Buscar por nombre, RFC o CURP..."
            value={filtroBuscar}
            onChange={(e) => setFiltroBuscar(e.target.value)}
            className="pl-10"
          />
        </div>
        <select
          value={filtroSucursal}
          onChange={(e) => setFiltroSucursal(e.target.value)}
          className="px-3 py-2 border rounded-lg text-sm"
        >
          <option value="">Todas las sucursales</option>
          {sucursales.map(s => (
            <option key={s.SucursalID} value={s.SucursalID}>{s.Nombre_Sucursal}</option>
          ))}
        </select>
        <Button variant="outline" size="sm" onClick={loadColaboradores}>
          <RefreshCw className="h-4 w-4 mr-1" />
          Actualizar
        </Button>
        <Button size="sm" className="bg-zinc-900 text-white" onClick={handleNuevoColaborador}>
          <UserPlus className="h-4 w-4 mr-1" />
          Nuevo Colaborador
        </Button>
      </div>

      {/* Tabla */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-zinc-800 text-white">
                <tr>
                  <th className="text-left p-3 font-medium">Nombre</th>
                  <th className="text-left p-3 font-medium">RFC</th>
                  <th className="text-left p-3 font-medium">Sucursal</th>
                  <th className="text-left p-3 font-medium">Puesto</th>
                  <th className="text-left p-3 font-medium">Estatus</th>
                  <th className="text-center p-3 font-medium">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {colaboradores.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-zinc-400">
                      No hay colaboradores registrados
                    </td>
                  </tr>
                ) : (
                  colaboradores.map((col, i) => (
                    <tr key={col.ColaboradorID || i} className="border-b hover:bg-zinc-50">
                      <td className="p-3 font-medium">{col.Nombre_Completo}</td>
                      <td className="p-3 text-zinc-600 font-mono text-xs">{col.RFC || '-'}</td>
                      <td className="p-3">{col.Nombre_Sucursal || '-'}</td>
                      <td className="p-3">{col.Puesto || '-'}</td>
                      <td className="p-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          col.Estatus_Laboral === 'Activo' ? 'bg-green-100 text-green-700' :
                          col.Estatus_Laboral === 'Baja' ? 'bg-red-100 text-red-700' :
                          'bg-amber-100 text-amber-700'
                        }`}>
                          {col.Estatus_Laboral || 'Sin estatus'}
                        </span>
                      </td>
                      <td className="p-3">
                        <div className="flex items-center justify-center gap-1">
                          <Button variant="ghost" size="sm" onClick={() => handleVerDetalle(col)} title="Ver detalle">
                            <Eye className="h-4 w-4 text-blue-600" />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => handleEditarColaborador(col)} title="Editar">
                            <Edit className="h-4 w-4 text-amber-600" />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => handleNuevaIncidencia(col.ColaboradorID)} title="Nueva incidencia">
                            <AlertTriangle className="h-4 w-4 text-purple-600" />
                          </Button>
                          {col.Estatus_Laboral === 'Activo' && (
                            <Button variant="ghost" size="sm" onClick={() => handleDarBaja(col)} title="Dar de baja">
                              <Trash2 className="h-4 w-4 text-red-600" />
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

      {/* Paginación */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            disabled={page === 1}
            onClick={() => setPage(p => p - 1)}
          >
            Anterior
          </Button>
          <span className="px-3 py-2 text-sm">
            Página {page} de {totalPages}
          </span>
          <Button 
            variant="outline" 
            size="sm" 
            disabled={page === totalPages}
            onClick={() => setPage(p => p + 1)}
          >
            Siguiente
          </Button>
        </div>
      )}
    </div>
  );

  // Render Incidencias
  const renderIncidencias = () => (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3 justify-between">
        <select
          value={filtroSucursal}
          onChange={(e) => setFiltroSucursal(e.target.value)}
          className="px-3 py-2 border rounded-lg text-sm"
        >
          <option value="">Todas las sucursales</option>
          {sucursales.map(s => (
            <option key={s.SucursalID} value={s.SucursalID}>{s.Nombre_Sucursal}</option>
          ))}
        </select>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleAbrirImportExcel}>
            <FileSpreadsheet className="h-4 w-4 mr-1" />
            Importar Excel
          </Button>
          <Button size="sm" className="bg-zinc-900 text-white" onClick={() => handleNuevaIncidencia()}>
            <Plus className="h-4 w-4 mr-1" />
            Nueva Incidencia
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-zinc-800 text-white">
                <tr>
                  <th className="text-left p-3 font-medium">Colaborador</th>
                  <th className="text-left p-3 font-medium">Sucursal</th>
                  <th className="text-left p-3 font-medium">Tipo</th>
                  <th className="text-left p-3 font-medium">Fecha</th>
                  <th className="text-right p-3 font-medium">Monto</th>
                  <th className="text-right p-3 font-medium">Unidades</th>
                </tr>
              </thead>
              <tbody>
                {incidencias.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-zinc-400">
                      No hay incidencias registradas
                    </td>
                  </tr>
                ) : (
                  incidencias.map((inc, i) => {
                    const esIngreso = esIncidenciaIngreso(inc.Tipo_Incidencia);
                    return (
                      <tr key={inc.IncidenciaID || i} className="border-b hover:bg-zinc-50">
                        <td className="p-3 font-medium">{inc.Nombre_Completo}</td>
                        <td className="p-3">{inc.Nombre_Sucursal || '-'}</td>
                        <td className="p-3">
                          <span className={`px-2 py-1 rounded text-xs font-medium flex items-center gap-1 w-fit ${
                            esIngreso ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                          }`}>
                            <span className="font-bold">{esIngreso ? '+' : '-'}</span>
                            {inc.Tipo_Incidencia}
                          </span>
                        </td>
                        <td className="p-3 text-zinc-600">
                          {inc.Fecha_Incidencia ? new Date(inc.Fecha_Incidencia).toLocaleDateString('es-MX') : '-'}
                        </td>
                        <td className={`p-3 text-right font-medium ${esIngreso ? 'text-green-600' : 'text-red-600'}`}>
                          {esIngreso ? '+' : '-'}${(inc.Monto || 0).toLocaleString()}
                        </td>
                        <td className="p-3 text-right">{inc.Unidades || 0}</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  // Render Flujo Nómina (NUEVO MÓDULO KANBAN)
  const renderFlujoNomina = () => {
    if (loadingNominas) {
      return (
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin text-zinc-400" />
        </div>
      );
    }
    
    return (
      <div className="space-y-4">
        {/* Sub-Tabs */}
        <div className="flex items-center justify-between border-b pb-2">
          <div className="flex gap-2">
            {['kanban', 'lista', 'config'].map(tab => (
              <button
                key={tab}
                onClick={() => setNominaSubTab(tab)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  nominaSubTab === tab ? 'bg-zinc-900 text-white' : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200'
                }`}
              >
                {tab === 'kanban' ? 'Tablero Kanban' : tab === 'lista' ? 'Lista' : 'Configuración'}
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={loadCiclosNomina}>
              <RefreshCw className="h-4 w-4" />
            </Button>
            {(isAdmin || isSupervisor) && (
              <Button size="sm" className="bg-zinc-900 text-white" onClick={() => setModalNuevoCiclo(true)}>
                <Plus className="h-4 w-4 mr-1" />
                Nuevo Ciclo
              </Button>
            )}
          </div>
        </div>
        
        {/* Vista Kanban */}
        {nominaSubTab === 'kanban' && (
          <div className="overflow-x-auto pb-4">
            <div className="flex gap-4 min-w-max">
              {ETAPAS_NOMINA.map(etapa => {
                const ciclosEtapa = getCiclosPorEtapa(etapa.id);
                const IconoEtapa = etapa.icon;
                return (
                  <div key={etapa.id} className="w-64 bg-zinc-50 rounded-xl p-3 flex-shrink-0">
                    <div className="flex items-center gap-2 mb-3">
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
                    <div className="space-y-2">
                      {ciclosEtapa.length === 0 ? (
                        <div className="text-center py-6 text-zinc-400 text-xs">Sin nóminas</div>
                      ) : (
                        ciclosEtapa.map(ciclo => {
                          const tiempoRestante = calcularTiempoRestante(ciclo);
                          return (
                            <Card key={ciclo.id} className={`cursor-pointer hover:shadow-md transition-shadow ${
                              tiempoRestante?.vencido ? 'border-red-300 bg-red-50' : ''
                            }`}>
                              <CardContent className="p-3">
                                <div className="flex items-start justify-between mb-2">
                                  <div>
                                    <p className="font-medium text-sm text-zinc-900">{ciclo.sucursal_nombre || 'Sucursal'}</p>
                                    <p className="text-xs text-zinc-500 capitalize">{ciclo.tipo_nomina}</p>
                                  </div>
                                  {tiempoRestante && (
                                    <div className={`flex items-center gap-1 text-xs ${tiempoRestante.color}`}>
                                      <Timer className="h-3 w-3" />{tiempoRestante.texto}
                                    </div>
                                  )}
                                </div>
                                <div className="text-xs text-zinc-500 mb-2">
                                  <Calendar className="h-3 w-3 inline mr-1" />
                                  Corte: {new Date(ciclo.fecha_corte).toLocaleDateString()}
                                </div>
                                <div className="flex items-center justify-between text-xs text-zinc-500 mb-2">
                                  <span>{ciclo.total_colaboradores || 0} colab.</span>
                                  <span>{ciclo.total_movimientos || 0} mov.</span>
                                </div>
                                {etapa.id !== 'pagada' && (
                                  <div className="flex gap-1 pt-2 border-t">
                                    <Button size="sm" variant="outline" className="flex-1 text-xs h-7"
                                      onClick={() => handleVerMovimientosCiclo(ciclo)}>
                                      <Eye className="h-3 w-3 mr-1" />Ver
                                    </Button>
                                    <Button size="sm" className="flex-1 text-xs h-7 bg-green-600 hover:bg-green-700"
                                      onClick={() => { setCicloSeleccionado(ciclo); setPasswordAprobacion(''); setComentarioAprobacion(''); setModalAprobarCiclo(true); }}>
                                      <ArrowRight className="h-3 w-3 mr-1" />Avanzar
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
          </div>
        )}
        
        {/* Vista Lista */}
        {nominaSubTab === 'lista' && (
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-zinc-50 border-b">
                    <tr>
                      <th className="text-left p-3 font-medium">Sucursal</th>
                      <th className="text-left p-3 font-medium">Tipo</th>
                      <th className="text-left p-3 font-medium">Fecha Corte</th>
                      <th className="text-left p-3 font-medium">Etapa</th>
                      <th className="text-left p-3 font-medium">Deadline</th>
                      <th className="text-left p-3 font-medium">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ciclosNomina.length === 0 ? (
                      <tr><td colSpan={6} className="text-center py-8 text-zinc-400">No hay ciclos de nómina</td></tr>
                    ) : (
                      ciclosNomina.map(ciclo => {
                        const etapa = ETAPAS_NOMINA.find(e => e.id === ciclo.etapa_actual);
                        const tiempoRestante = calcularTiempoRestante(ciclo);
                        return (
                          <tr key={ciclo.id} className="border-b hover:bg-zinc-50">
                            <td className="p-3 font-medium">{ciclo.sucursal_nombre}</td>
                            <td className="p-3 capitalize">{ciclo.tipo_nomina}</td>
                            <td className="p-3">{new Date(ciclo.fecha_corte).toLocaleDateString()}</td>
                            <td className="p-3">
                              {etapa && <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium text-white ${etapa.color}`}>
                                <etapa.icon className="h-3 w-3" />{etapa.nombre}
                              </span>}
                            </td>
                            <td className="p-3">{tiempoRestante && <span className={`${tiempoRestante.color} font-medium`}>{tiempoRestante.texto}</span>}</td>
                            <td className="p-3">
                              <div className="flex gap-1">
                                <Button variant="ghost" size="sm" onClick={() => { setCicloSeleccionado(ciclo); setModalHistorialCiclo(true); }}>
                                  <History className="h-4 w-4" />
                                </Button>
                                <Button variant="ghost" size="sm" onClick={() => handleVerMovimientosCiclo(ciclo)}>
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
        
        {/* Vista Configuración */}
        {nominaSubTab === 'config' && isAdmin && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader className="py-4">
                <CardTitle className="text-base flex items-center gap-2"><Clock className="h-5 w-5" />Configuración de Tiempos</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Día de Corte</Label>
                    <select value={formConfigNomina.dia_corte} onChange={(e) => setFormConfigNomina({...formConfigNomina, dia_corte: parseInt(e.target.value)})} className="w-full border rounded-lg px-3 py-2 mt-1">
                      {diasSemana.map((dia, idx) => <option key={idx} value={idx}>{dia}</option>)}
                    </select>
                  </div>
                  <div>
                    <Label>Día de Pago</Label>
                    <select value={formConfigNomina.dia_pago} onChange={(e) => setFormConfigNomina({...formConfigNomina, dia_pago: parseInt(e.target.value)})} className="w-full border rounded-lg px-3 py-2 mt-1">
                      {diasSemana.map((dia, idx) => <option key={idx} value={idx}>{dia}</option>)}
                    </select>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>Horario Headcount</Label>
                    <Input type="time" value={formConfigNomina.horario_headcount} onChange={(e) => setFormConfigNomina({...formConfigNomina, horario_headcount: e.target.value})} className="mt-1" />
                  </div>
                  <div>
                    <Label>Horario Maquilador</Label>
                    <Input type="time" value={formConfigNomina.horario_maquilador} onChange={(e) => setFormConfigNomina({...formConfigNomina, horario_maquilador: e.target.value})} className="mt-1" />
                  </div>
                  <div>
                    <Label>Horario Tesorería</Label>
                    <Input type="time" value={formConfigNomina.horario_tesoreria} onChange={(e) => setFormConfigNomina({...formConfigNomina, horario_tesoreria: e.target.value})} className="mt-1" />
                  </div>
                </div>
                <Button onClick={handleGuardarConfigNomina} disabled={savingForm} className="w-full">
                  {savingForm ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}Guardar Configuración
                </Button>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="py-4">
                <CardTitle className="text-base flex items-center gap-2"><ArrowRight className="h-5 w-5" />Flujo de Nómina</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {ETAPAS_NOMINA.map((etapa, idx) => {
                    const IconoEtapa = etapa.icon;
                    return (
                      <div key={etapa.id} className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${etapa.color}`}><IconoEtapa className="h-4 w-4 text-white" /></div>
                        <div className="flex-1">
                          <p className="font-medium text-sm">{idx + 1}. {etapa.nombre}</p>
                          <p className="text-xs text-zinc-500">Responsable: {etapa.responsable}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
        {nominaSubTab === 'config' && !isAdmin && (
          <Card className="border-2 border-dashed border-zinc-300">
            <CardContent className="py-12 text-center">
              <Lock className="h-12 w-12 text-zinc-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-zinc-600 mb-2">Acceso Restringido</h3>
              <p className="text-zinc-400 text-sm">Solo Administradores pueden modificar la configuración.</p>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  // Render Asistencia (placeholder)
  const renderAsistencia = () => (
    <Card className="border-2 border-dashed border-zinc-300">
      <CardContent className="py-12 text-center">
        <Clock className="h-12 w-12 text-zinc-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-zinc-600 mb-2">Control de Asistencia</h3>
        <p className="text-zinc-400 text-sm">
          Módulo de reloj checador en desarrollo.<br />
          Conectará con RH_Reloj_Checador de EDARSA HUB.
        </p>
      </CardContent>
    </Card>
  );

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
      const url = editingVacante 
        ? `${API_URL}/api/rrhh/vacantes/${editingVacante.VacanteID}`
        : `${API_URL}/api/rrhh/vacantes`;
      
      const response = await fetch(url, {
        method: editingVacante ? 'PUT' : 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formVacante)
      });
      
      if (!response.ok) throw new Error('Error al guardar');
      
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
      const response = await fetch(`${API_URL}/api/rrhh/candidatos`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formCandidato)
      });
      
      if (!response.ok) throw new Error('Error al guardar');
      
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
      const response = await fetch(`${API_URL}/api/rrhh/candidatos/${candidatoId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ estatus: nuevoEstatus })
      });
      
      if (!response.ok) throw new Error('Error');
      toast.success('Estatus actualizado');
      loadReclutamiento();
    } catch (error) {
      toast.error('Error al actualizar');
    }
  };

  const handleVerScriptRecl = async () => {
    try {
      const data = await fetchWithAuth('/api/rrhh/reclutamiento/script-inicializacion');
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

  // Render Reclutamiento
  const renderReclutamiento = () => {
    const vacAbiertas = vacantes.filter(v => v.Estatus === 'Abierta').length;
    const candPendientes = candidatos.filter(c => c.Estatus === 'Recibido' || c.Estatus === 'En Revision').length;
    
    return (
      <div className="space-y-6">
        {/* KPIs */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="border-l-4 border-l-blue-500">
            <CardContent className="pt-4">
              <p className="text-xs text-zinc-500 uppercase">Vacantes Abiertas</p>
              <p className="text-2xl font-bold text-blue-600">{vacAbiertas}</p>
            </CardContent>
          </Card>
          <Card className="border-l-4 border-l-purple-500">
            <CardContent className="pt-4">
              <p className="text-xs text-zinc-500 uppercase">Total Candidatos</p>
              <p className="text-2xl font-bold text-purple-600">{candidatos.length}</p>
            </CardContent>
          </Card>
          <Card className="border-l-4 border-l-amber-500">
            <CardContent className="pt-4">
              <p className="text-xs text-zinc-500 uppercase">Pendientes Revisión</p>
              <p className="text-2xl font-bold text-amber-600">{candPendientes}</p>
            </CardContent>
          </Card>
          <Card className="border-l-4 border-l-green-500">
            <CardContent className="pt-4">
              <p className="text-xs text-zinc-500 uppercase">Contratados</p>
              <p className="text-2xl font-bold text-green-600">
                {candidatos.filter(c => c.Estatus === 'Contratado').length}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Acciones */}
        <div className="flex flex-wrap gap-3 justify-between">
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleVerScriptRecl}>
              <FileText className="h-4 w-4 mr-1" />
              Ver Script SQL
            </Button>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => handleNuevoCandidato()}>
              <UserPlus className="h-4 w-4 mr-1" />
              Nuevo Candidato
            </Button>
            <Button size="sm" className="bg-zinc-900 text-white" onClick={handleNuevaVacante}>
              <Plus className="h-4 w-4 mr-1" />
              Nueva Vacante
            </Button>
          </div>
        </div>

        {/* Vacantes */}
        <Card>
          <CardHeader className="py-3 bg-zinc-800 text-white rounded-t-lg">
            <CardTitle className="text-base flex items-center gap-2">
              <Briefcase className="h-5 w-5" />
              Vacantes ({vacantes.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {vacantes.length === 0 ? (
              <div className="text-center py-8 text-zinc-400">
                <Inbox className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No hay vacantes registradas</p>
                <p className="text-xs">Ejecuta el script SQL para crear las tablas</p>
              </div>
            ) : (
              <div className="divide-y">
                {vacantes.map((vac, i) => (
                  <div key={vac.VacanteID || i} className="p-4 hover:bg-zinc-50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-medium">{vac.Titulo}</h4>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                            vac.Estatus === 'Abierta' ? 'bg-green-100 text-green-700' :
                            vac.Estatus === 'En Proceso' ? 'bg-blue-100 text-blue-700' :
                            'bg-zinc-100 text-zinc-700'
                          }`}>
                            {vac.Estatus}
                          </span>
                        </div>
                        <div className="text-sm text-zinc-500 flex flex-wrap gap-3">
                          <span className="flex items-center gap-1">
                            <Building2 className="h-3 w-3" />
                            {vac.Nombre_Sucursal}
                          </span>
                          <span className="flex items-center gap-1">
                            <Briefcase className="h-3 w-3" />
                            {vac.Nombre_Puesto}
                          </span>
                          {vac.Salario_Max > 0 && (
                            <span className="text-green-600">
                              ${vac.Salario_Min?.toLocaleString()} - ${vac.Salario_Max?.toLocaleString()}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs font-medium">
                          {vac.Total_Candidatos || 0} candidatos
                        </span>
                        <Button variant="ghost" size="sm" onClick={() => {
                          setSelectedVacante(vac);
                          handleNuevoCandidato(vac.VacanteID);
                        }}>
                          <UserPlus className="h-4 w-4 text-blue-600" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Candidatos */}
        <Card>
          <CardHeader className="py-3 bg-zinc-800 text-white rounded-t-lg">
            <CardTitle className="text-base flex items-center gap-2">
              <Users className="h-5 w-5" />
              Candidatos ({candidatos.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-zinc-100">
                  <tr>
                    <th className="text-left p-3 font-medium">Candidato</th>
                    <th className="text-left p-3 font-medium">Vacante</th>
                    <th className="text-left p-3 font-medium">Contacto</th>
                    <th className="text-left p-3 font-medium">Fecha</th>
                    <th className="text-left p-3 font-medium">Estatus</th>
                    <th className="text-center p-3 font-medium">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {candidatos.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="text-center py-8 text-zinc-400">
                        No hay candidatos registrados
                      </td>
                    </tr>
                  ) : (
                    candidatos.map((cand, i) => {
                      const estatusInfo = estatusCandidato.find(e => e.value === cand.Estatus) || estatusCandidato[0];
                      return (
                        <tr key={cand.CandidatoID || i} className="border-b hover:bg-zinc-50">
                          <td className="p-3">
                            <div className="font-medium">{cand.Nombre_Completo}</div>
                            {cand.Puntuacion && (
                              <div className="flex items-center gap-1 text-xs text-amber-600">
                                <Star className="h-3 w-3 fill-amber-400" />
                                {cand.Puntuacion}/100
                              </div>
                            )}
                          </td>
                          <td className="p-3 text-zinc-600">{cand.Vacante_Titulo}</td>
                          <td className="p-3">
                            <div className="flex flex-col gap-1 text-xs">
                              <span className="flex items-center gap-1">
                                <Mail className="h-3 w-3 text-zinc-400" />
                                {cand.Email}
                              </span>
                              {cand.Telefono && (
                                <span className="flex items-center gap-1">
                                  <Phone className="h-3 w-3 text-zinc-400" />
                                  {cand.Telefono}
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="p-3 text-xs text-zinc-500">
                            {cand.Fecha_Aplicacion ? new Date(cand.Fecha_Aplicacion).toLocaleDateString('es-MX') : '-'}
                          </td>
                          <td className="p-3">
                            <select
                              value={cand.Estatus}
                              onChange={(e) => handleCambiarEstatusCandidato(cand.CandidatoID, e.target.value)}
                              className={`px-2 py-1 rounded text-xs font-medium border-0 cursor-pointer ${estatusInfo.color}`}
                            >
                              {estatusCandidato.map(e => (
                                <option key={e.value} value={e.value}>{e.value}</option>
                              ))}
                            </select>
                          </td>
                          <td className="p-3 text-center">
                            {cand.CV_URL && (
                              <Button variant="ghost" size="sm" onClick={() => window.open(cand.CV_URL, '_blank')}>
                                <ExternalLink className="h-4 w-4 text-blue-600" />
                              </Button>
                            )}
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
      </div>
    );
  };

  // ===================== RENDER CATÁLOGOS =====================
  const renderCatalogos = () => {
    return (
      <div className="space-y-6" data-testid="catalogos-section">
        {/* Header con aviso de permisos */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-zinc-800">Catálogos de RRHH</h2>
            <p className="text-sm text-zinc-500">Administración de Puestos y Tipos de Incidencias</p>
          </div>
          <div className="flex items-center gap-2">
            {!isAdmin && (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-50 border border-amber-200 rounded-lg text-amber-700 text-sm">
                <Lock className="h-4 w-4" />
                <span>Solo lectura (requiere rol Administrador para editar)</span>
              </div>
            )}
            <Button variant="outline" size="sm" onClick={loadCatalogosCompleto}>
              <RefreshCw className={`h-4 w-4 mr-1 ${loadingCatalogos ? 'animate-spin' : ''}`} />
              Actualizar
            </Button>
            <Button variant="outline" size="sm" onClick={loadScriptCatalogos}>
              <Database className="h-4 w-4 mr-1" />
              Script SQL
            </Button>
          </div>
        </div>

        {/* Sub-pestañas: Puestos | Incidencias */}
        <div className="flex gap-2 border-b border-zinc-200">
          <button
            onClick={() => setCatalogoSubTab('puestos')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-all ${
              catalogoSubTab === 'puestos'
                ? 'border-zinc-900 text-zinc-900'
                : 'border-transparent text-zinc-500 hover:text-zinc-700'
            }`}
          >
            <Briefcase className="h-4 w-4 inline mr-2" />
            Puestos
          </button>
          <button
            onClick={() => setCatalogoSubTab('incidencias')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-all ${
              catalogoSubTab === 'incidencias'
                ? 'border-zinc-900 text-zinc-900'
                : 'border-transparent text-zinc-500 hover:text-zinc-700'
            }`}
          >
            <Tag className="h-4 w-4 inline mr-2" />
            Tipos de Incidencias
          </button>
        </div>

        {/* Contenido según sub-pestaña */}
        {catalogoSubTab === 'puestos' && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between py-4">
              <CardTitle className="text-base font-medium flex items-center gap-2">
                <Briefcase className="h-5 w-5 text-zinc-600" />
                Catálogo de Puestos ({catalogoPuestos.length})
              </CardTitle>
              {isAdmin && (
                <Button size="sm" onClick={handleNuevoPuesto} data-testid="btn-nuevo-puesto">
                  <Plus className="h-4 w-4 mr-1" />
                  Nuevo Puesto
                </Button>
              )}
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-zinc-50 border-y">
                    <tr>
                      <th className="px-4 py-3 text-left font-medium text-zinc-600">ID</th>
                      <th className="px-4 py-3 text-left font-medium text-zinc-600">Descripción</th>
                      <th className="px-4 py-3 text-left font-medium text-zinc-600">Departamento</th>
                      <th className="px-4 py-3 text-right font-medium text-zinc-600">Sueldo Base</th>
                      <th className="px-4 py-3 text-center font-medium text-zinc-600">NomiPAQ</th>
                      <th className="px-4 py-3 text-center font-medium text-zinc-600">MPRO</th>
                      {isAdmin && <th className="px-4 py-3 text-center font-medium text-zinc-600">Acciones</th>}
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {loadingCatalogos ? (
                      <tr>
                        <td colSpan={isAdmin ? 7 : 6} className="px-4 py-8 text-center text-zinc-500">
                          <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2" />
                          Cargando...
                        </td>
                      </tr>
                    ) : catalogoPuestos.length === 0 ? (
                      <tr>
                        <td colSpan={isAdmin ? 7 : 6} className="px-4 py-8 text-center text-zinc-500">
                          No hay puestos registrados. Ejecute el script SQL si la tabla no existe.
                        </td>
                      </tr>
                    ) : (
                      catalogoPuestos.map((p) => (
                        <tr key={p.PuestoID} className="hover:bg-zinc-50">
                          <td className="px-4 py-3 text-zinc-600">{p.PuestoID}</td>
                          <td className="px-4 py-3 font-medium text-zinc-800">{p.Descripcion}</td>
                          <td className="px-4 py-3 text-zinc-600">{p.Departamento || '-'}</td>
                          <td className="px-4 py-3 text-right text-zinc-800">
                            ${(p.Sueldo_Base_Seman_SBC || 0).toLocaleString('es-MX', { minimumFractionDigits: 2 })}
                          </td>
                          <td className="px-4 py-3 text-center">
                            {p.NomiPAQ_ID ? (
                              <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded">{p.NomiPAQ_ID}</span>
                            ) : (
                              <span className="text-zinc-400">-</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-center">
                            {p.MPRO_ID ? (
                              <span className="px-2 py-0.5 bg-green-50 text-green-700 text-xs rounded">{p.MPRO_ID}</span>
                            ) : (
                              <span className="text-zinc-400">-</span>
                            )}
                          </td>
                          {isAdmin && (
                            <td className="px-4 py-3 text-center">
                              <div className="flex justify-center gap-1">
                                <Button variant="ghost" size="sm" onClick={() => handleEditarPuesto(p)} data-testid={`btn-edit-puesto-${p.PuestoID}`}>
                                  <Edit className="h-4 w-4 text-blue-600" />
                                </Button>
                                <Button variant="ghost" size="sm" onClick={() => handleEliminarPuesto(p.PuestoID)} data-testid={`btn-delete-puesto-${p.PuestoID}`}>
                                  <Trash2 className="h-4 w-4 text-red-600" />
                                </Button>
                              </div>
                            </td>
                          )}
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}

        {catalogoSubTab === 'incidencias' && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between py-4">
              <CardTitle className="text-base font-medium flex items-center gap-2">
                <Tag className="h-5 w-5 text-zinc-600" />
                Tipos de Incidencias ({catalogoIncidencias.length})
              </CardTitle>
              {isAdmin && (
                <Button size="sm" onClick={handleNuevoTipoIncidencia} data-testid="btn-nuevo-tipo-incidencia">
                  <Plus className="h-4 w-4 mr-1" />
                  Nuevo Tipo
                </Button>
              )}
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-zinc-50 border-y">
                    <tr>
                      <th className="px-4 py-3 text-left font-medium text-zinc-600">Código</th>
                      <th className="px-4 py-3 text-left font-medium text-zinc-600">Descripción</th>
                      <th className="px-4 py-3 text-center font-medium text-zinc-600">Categoría</th>
                      <th className="px-4 py-3 text-center font-medium text-zinc-600">Cálculo</th>
                      <th className="px-4 py-3 text-center font-medium text-zinc-600">NomiPAQ</th>
                      <th className="px-4 py-3 text-center font-medium text-zinc-600">MPRO</th>
                      {isAdmin && <th className="px-4 py-3 text-center font-medium text-zinc-600">Acciones</th>}
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {loadingCatalogos ? (
                      <tr>
                        <td colSpan={isAdmin ? 7 : 6} className="px-4 py-8 text-center text-zinc-500">
                          <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2" />
                          Cargando...
                        </td>
                      </tr>
                    ) : catalogoIncidencias.length === 0 ? (
                      <tr>
                        <td colSpan={isAdmin ? 7 : 6} className="px-4 py-8 text-center text-zinc-500">
                          No hay tipos de incidencia registrados. Ejecute el script SQL para crear la tabla.
                        </td>
                      </tr>
                    ) : (
                      catalogoIncidencias.map((t) => (
                        <tr key={t.TipoIncidenciaID} className="hover:bg-zinc-50">
                          <td className="px-4 py-3">
                            <span className="px-2 py-1 bg-zinc-100 text-zinc-700 font-mono text-xs rounded">{t.Codigo}</span>
                          </td>
                          <td className="px-4 py-3 font-medium text-zinc-800">{t.Descripcion}</td>
                          <td className="px-4 py-3 text-center">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              t.Categoria === 'Ingreso' 
                                ? 'bg-green-100 text-green-700' 
                                : 'bg-red-100 text-red-700'
                            }`}>
                              {t.Categoria === 'Ingreso' ? '+ Ingreso' : '- Descuento'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-center text-zinc-600 text-xs">
                            {t.Calculo_Monto || 'Manual'}
                          </td>
                          <td className="px-4 py-3 text-center">
                            {t.NomiPAQ_ID ? (
                              <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded">{t.NomiPAQ_ID}</span>
                            ) : (
                              <span className="text-zinc-400">-</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-center">
                            {t.MPRO_ID ? (
                              <span className="px-2 py-0.5 bg-green-50 text-green-700 text-xs rounded">{t.MPRO_ID}</span>
                            ) : (
                              <span className="text-zinc-400">-</span>
                            )}
                          </td>
                          {isAdmin && (
                            <td className="px-4 py-3 text-center">
                              <div className="flex justify-center gap-1">
                                <Button variant="ghost" size="sm" onClick={() => handleEditarTipoIncidencia(t)} data-testid={`btn-edit-tipo-${t.TipoIncidenciaID}`}>
                                  <Edit className="h-4 w-4 text-blue-600" />
                                </Button>
                                <Button variant="ghost" size="sm" onClick={() => handleEliminarTipoIncidencia(t.TipoIncidenciaID)} data-testid={`btn-delete-tipo-${t.TipoIncidenciaID}`}>
                                  <Trash2 className="h-4 w-4 text-red-600" />
                                </Button>
                              </div>
                            </td>
                          )}
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Nota informativa */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-medium text-blue-800 mb-2 flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Integración con Sistemas Externos
          </h4>
          <ul className="text-sm text-blue-700 space-y-1 list-disc list-inside">
            <li><strong>NomiPAQ:</strong> Use el campo NomiPAQ_ID para mapear con conceptos de nómina.</li>
            <li><strong>MPRO:</strong> Use el campo MPRO_ID para sincronizar con el sistema MPRO.</li>
            <li><strong>Excel:</strong> Los códigos se usan como referencia en las importaciones de nómina.</li>
          </ul>
        </div>
      </div>
    );
  };

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
                            {detalleColaborador.incidencias?.slice(0, 5).map((inc, i) => (
                              <tr key={i} className="border-t">
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
                            {detalleColaborador.asistencias?.slice(0, 5).map((a, i) => (
                              <tr key={i} className="border-t">
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
                          <li key={i}>{err}</li>
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
                    <li key={i}>{inst}</li>
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
                <select value={formNuevoCiclo.sucursal_id} onChange={(e) => setFormNuevoCiclo({...formNuevoCiclo, sucursal_id: e.target.value})} className="w-full border rounded-lg px-3 py-2 mt-1">
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
                <select value={formNuevoCiclo.tipo_nomina} onChange={(e) => setFormNuevoCiclo({...formNuevoCiclo, tipo_nomina: e.target.value})} className="w-full border rounded-lg px-3 py-2 mt-1">
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
                <textarea value={comentarioAprobacion} onChange={(e) => setComentarioAprobacion(e.target.value)} className="w-full border rounded-lg px-3 py-2 mt-1" placeholder="Observaciones..." />
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
                        <div className={`absolute left-2 w-4 h-4 rounded-full ${evento.tipo === 'creacion' ? 'bg-blue-500' : evento.tipo === 'avance' ? 'bg-green-500' : evento.tipo === 'rechazo' ? 'bg-red-500' : 'bg-zinc-400'}`}></div>
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
