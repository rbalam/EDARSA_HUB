import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { 
  ClipboardList, CheckCircle2, Clock, XCircle, Bell, 
  RefreshCw, Eye, Check, X, FileText, Users, Settings,
  Plus, ChevronRight, Lock, AlertTriangle, Filter, History,
  Edit, RotateCcw, Layers, ArrowRight, Building2, Mail, Phone,
  ExternalLink, Search
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function MisTareas() {
  const [loading, setLoading] = useState(true);
  const [tareas, setTareas] = useState({
    pendientes: [],
    en_proceso: [],
    completadas: [],
    total_pendientes: 0,
    total_en_proceso: 0,
    solicitudes_pendientes_aprobar: 0
  });
  const [solicitudesPendientes, setSolicitudesPendientes] = useState([]);
  const [misSolicitudes, setMisSolicitudes] = useState([]); // Solicitudes del usuario actual
  const [misPermisos, setMisPermisos] = useState({ puede_solicitar: false, puede_aprobar: false, catalogos_permitidos: [] });
  const [catalogosDisponibles, setCatalogosDisponibles] = useState([]);
  const [usuarios, setUsuarios] = useState([]);
  
  // Estados BANDEJA UNIFICADA
  const [pendientesUnificados, setPendientesUnificados] = useState({
    urgentes: [],
    catalogos: [],
    proveedores: [],
    nominas: [],
    contadores: { urgentes: 0, catalogos: 0, proveedores: 0, nominas: 0, total: 0 }
  });
  
  // Estados Portal Proveedores
  const [proveedores, setProveedores] = useState([]);
  const [filtroProveedores, setFiltroProveedores] = useState('pending');
  const [searchProveedores, setSearchProveedores] = useState('');
  const [modalProveedor, setModalProveedor] = useState(false);
  const [proveedorSeleccionado, setProveedorSeleccionado] = useState(null);
  const [sucursalesProveedor, setSucursalesProveedor] = useState([]);
  const [serversDisponibles, setServersDisponibles] = useState([]);
  
  // Modales
  const [modalSolicitud, setModalSolicitud] = useState(false);
  const [modalAprobar, setModalAprobar] = useState(false);
  const [modalRechazar, setModalRechazar] = useState(false);
  const [modalPermisos, setModalPermisos] = useState(false);
  const [modalDetalle, setModalDetalle] = useState(false);
  const [modalHistorial, setModalHistorial] = useState(false);
  const [modalCorregir, setModalCorregir] = useState(false);
  const [modalConfigNiveles, setModalConfigNiveles] = useState(false);
  
  const [solicitudSeleccionada, setSolicitudSeleccionada] = useState(null);
  const [historialSolicitud, setHistorialSolicitud] = useState(null);
  const [usuarioSeleccionado, setUsuarioSeleccionado] = useState(null);
  const [savingForm, setSavingForm] = useState(false);
  
  // Form nueva solicitud
  const [formSolicitud, setFormSolicitud] = useState({
    catalogo_id: '',
    datos: {},
    notas: ''
  });
  
  // Form corrección
  const [formCorreccion, setFormCorreccion] = useState({
    datos: {},
    notas: ''
  });
  
  // Form aprobación
  const [passwordAprobacion, setPasswordAprobacion] = useState('');
  const [comentarioAprobacion, setComentarioAprobacion] = useState('');
  const [motivoRechazo, setMotivoRechazo] = useState('');
  
  // Form permisos
  const [formPermisos, setFormPermisos] = useState({
    catalogos_permitidos: [],
    puede_solicitar: true
  });
  
  const token = localStorage.getItem('token');
  const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
  const isAdmin = currentUser?.role === 'Administrador';
  const isSupervisor = currentUser?.role === 'Supervisor';
  const canApprove = isAdmin || isSupervisor;
  
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
      const [tareasData, permisosData, catalogosData, misSolicitudesData, unificadosData] = await Promise.all([
        fetchWithAuth('/api/sistema/mis-tareas'),
        fetchWithAuth('/api/sistema/mis-permisos-catalogos'),
        fetchWithAuth('/api/sistema/catalogos-disponibles'),
        fetchWithAuth('/api/sistema/solicitudes'),  // Mis solicitudes
        fetchWithAuth('/api/sistema/pendientes-unificados')  // NUEVO: Bandeja unificada
      ]);
      
      setTareas(tareasData);
      setMisPermisos(permisosData);
      setCatalogosDisponibles(catalogosData.catalogos || []);
      setMisSolicitudes(misSolicitudesData.solicitudes || []);
      
      // Cargar solicitudes de catálogos RH pendientes
      try {
        const solicitudesCatalogoRH = await fetchWithAuth('/api/rrhh/solicitudes-catalogo/pendientes-notificacion');
        const catalogosPendientes = solicitudesCatalogoRH.pendientes || [];
        
        // Agregar al unificado
        setPendientesUnificados({
          ...unificadosData,
          catalogos: [...(unificadosData.catalogos || []), ...catalogosPendientes.map(s => ({
            id: `rh-${s.id}`,
            tipo: 'solicitud_catalogo_rh',
            titulo: s.nombre_elemento,
            subtitulo: `Catálogo: ${s.nombre_catalogo}`,
            estado: s.estado_nombre,
            fecha: s.fecha_solicitud,
            prioridad: 'media',
            data: s
          }))],
          contadores: {
            ...unificadosData.contadores,
            catalogos: (unificadosData.contadores?.catalogos || 0) + catalogosPendientes.length,
            total: (unificadosData.contadores?.total || 0) + catalogosPendientes.length
          }
        });
      } catch (e) {
        console.log('No se pudieron cargar solicitudes RH:', e);
        setPendientesUnificados(unificadosData);
      }
      
      // Si puede aprobar, cargar solicitudes pendientes de aprobar
      if (canApprove) {
        // Cargar solicitudes en cualquier estado "Pendiente" o "Reenviada"
        const solicitudesData = await fetchWithAuth('/api/sistema/solicitudes');
        const pendientes = (solicitudesData.solicitudes || []).filter(s => 
          s.estatus?.includes('Pendiente') || s.estatus === 'Reenviada'
        );
        setSolicitudesPendientes(pendientes);
      }
    } catch (error) {
      console.error('Error cargando tareas:', error);
      toast.error('Error cargando datos');
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, canApprove]);
  
  // Cargar usuarios (para asignar permisos)
  const loadUsuarios = async () => {
    try {
      const data = await fetchWithAuth('/api/sistema/usuarios-asignables');
      setUsuarios(data.usuarios || []);
    } catch (error) {
      console.error('Error cargando usuarios:', error);
    }
  };
  
  // Cargar proveedores
  const loadProveedores = async () => {
    try {
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
  
  // Cargar servers para sucursales
  const loadServersProveedor = async () => {
    try {
      const response = await fetch(`${API_URL}/api/servers`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setServersDisponibles(data.filter(s => s.active) || []);
      }
    } catch (error) {
      console.error('Error cargando servers:', error);
    }
  };
  
  useEffect(() => {
    loadData();
    if (canApprove) {
      loadUsuarios();
      loadProveedores();
      loadServersProveedor();
    }
  }, [loadData, canApprove]);
  
  // Abrir modal de nueva solicitud
  const handleNuevaSolicitud = () => {
    if (!misPermisos.puede_solicitar && !isAdmin) {
      toast.error('No tiene permiso para crear solicitudes');
      return;
    }
    setFormSolicitud({ catalogo_id: '', datos: {}, notas: '' });
    setModalSolicitud(true);
  };
  
  // Crear solicitud
  const handleCrearSolicitud = async () => {
    if (!formSolicitud.catalogo_id) {
      toast.error('Seleccione un catálogo');
      return;
    }
    
    setSavingForm(true);
    try {
      const response = await fetch(`${API_URL}/api/sistema/solicitudes`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formSolicitud)
      });
      
      if (response.status === 403) {
        toast.error('No tiene permiso para solicitar altas en este catálogo');
        return;
      }
      if (!response.ok) throw new Error('Error al crear solicitud');
      
      toast.success('Solicitud creada correctamente');
      setModalSolicitud(false);
      loadData();
    } catch (error) {
      toast.error('Error al crear solicitud');
    } finally {
      setSavingForm(false);
    }
  };
  
  // Abrir modal de aprobar
  const handleAbrirAprobar = (solicitud) => {
    setSolicitudSeleccionada(solicitud);
    setPasswordAprobacion('');
    setComentarioAprobacion('');
    setModalAprobar(true);
  };
  
  // Aprobar solicitud
  const handleAprobar = async () => {
    if (!passwordAprobacion) {
      toast.error('Ingrese su contraseña para autorizar');
      return;
    }
    
    setSavingForm(true);
    try {
      const response = await fetch(`${API_URL}/api/sistema/solicitudes/${solicitudSeleccionada.id}/aprobar`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ password: passwordAprobacion, comentario: comentarioAprobacion })
      });
      
      if (response.status === 401) {
        toast.error('Contraseña incorrecta');
        return;
      }
      if (!response.ok) throw new Error('Error al aprobar');
      
      const result = await response.json();
      toast.success(result.message || 'Solicitud procesada');
      setModalAprobar(false);
      loadData();
    } catch (error) {
      toast.error('Error al aprobar solicitud');
    } finally {
      setSavingForm(false);
    }
  };
  
  // Abrir modal de rechazar
  const handleAbrirRechazar = (solicitud) => {
    setSolicitudSeleccionada(solicitud);
    setMotivoRechazo('');
    setModalRechazar(true);
  };
  
  // Rechazar solicitud
  const handleRechazar = async () => {
    setSavingForm(true);
    try {
      const response = await fetch(`${API_URL}/api/sistema/solicitudes/${solicitudSeleccionada.id}/rechazar`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ motivo: motivoRechazo })
      });
      
      if (!response.ok) throw new Error('Error al rechazar');
      
      toast.success('Solicitud rechazada. El solicitante puede corregir y reenviar.');
      setModalRechazar(false);
      loadData();
    } catch (error) {
      toast.error('Error al rechazar solicitud');
    } finally {
      setSavingForm(false);
    }
  };
  
  // Abrir modal de permisos
  const handleAbrirPermisos = (usuario) => {
    setUsuarioSeleccionado(usuario);
    setFormPermisos({
      catalogos_permitidos: usuario.permisos_catalogos || [],
      puede_solicitar: usuario.puede_solicitar || false
    });
    setModalPermisos(true);
  };
  
  // Guardar permisos
  const handleGuardarPermisos = async () => {
    setSavingForm(true);
    try {
      const response = await fetch(`${API_URL}/api/sistema/permisos-catalogos`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: usuarioSeleccionado.id,
          ...formPermisos
        })
      });
      
      if (!response.ok) throw new Error('Error al guardar');
      
      toast.success('Permisos asignados correctamente');
      setModalPermisos(false);
      loadUsuarios();
    } catch (error) {
      toast.error('Error al guardar permisos');
    } finally {
      setSavingForm(false);
    }
  };
  
  // Ver detalle de solicitud
  const handleVerDetalle = async (solicitudId) => {
    try {
      const data = await fetchWithAuth(`/api/sistema/solicitudes/${solicitudId}`);
      setSolicitudSeleccionada(data);
      setModalDetalle(true);
    } catch (error) {
      toast.error('Error cargando detalle');
    }
  };
  
  // Ver historial de trazabilidad
  const handleVerHistorial = async (solicitudId) => {
    try {
      const data = await fetchWithAuth(`/api/sistema/solicitudes/${solicitudId}/historial`);
      setHistorialSolicitud(data);
      setModalHistorial(true);
    } catch (error) {
      toast.error('Error cargando historial');
    }
  };
  
  // Abrir modal de corrección (para solicitudes rechazadas)
  const handleAbrirCorregir = (solicitud) => {
    setSolicitudSeleccionada(solicitud);
    setFormCorreccion({
      datos: { ...solicitud.datos },
      notas: solicitud.notas || ''
    });
    setModalCorregir(true);
  };
  
  // Corregir y reenviar solicitud
  const handleCorregirYReenviar = async () => {
    setSavingForm(true);
    try {
      const response = await fetch(`${API_URL}/api/sistema/solicitudes/${solicitudSeleccionada.id}/corregir`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formCorreccion)
      });
      
      if (!response.ok) throw new Error('Error al corregir');
      
      const result = await response.json();
      toast.success(result.message || 'Solicitud corregida y reenviada');
      setModalCorregir(false);
      loadData();
    } catch (error) {
      toast.error('Error al corregir solicitud');
    } finally {
      setSavingForm(false);
    }
  };
  
  // Configurar niveles de aprobación de un catálogo
  const handleConfigurarNiveles = async (catalogoId, niveles) => {
    try {
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
      loadData();  // Recargar catálogos con nueva config
    } catch (error) {
      toast.error('Error al configurar niveles');
    }
  };
  
  // Marcar tarea como leída
  const handleMarcarLeida = async (tareaId) => {
    try {
      await fetch(`${API_URL}/api/sistema/tareas/${tareaId}/marcar-leida`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      loadData();
    } catch (error) {
      console.error('Error:', error);
    }
  };
  
  // Obtener campos del formulario según catálogo seleccionado
  const getCamposCatalogo = () => {
    const catalogo = formSolicitud.catalogo_id;
    switch(catalogo) {
      case 'puestos':
        return (
          <div className="space-y-3">
            <div>
              <Label>Descripción del Puesto *</Label>
              <Input 
                value={formSolicitud.datos.descripcion || ''}
                onChange={(e) => setFormSolicitud({...formSolicitud, datos: {...formSolicitud.datos, descripcion: e.target.value}})}
                placeholder="Ej: Gerente de Operaciones"
              />
            </div>
            <div>
              <Label>Departamento</Label>
              <Input 
                value={formSolicitud.datos.departamento || ''}
                onChange={(e) => setFormSolicitud({...formSolicitud, datos: {...formSolicitud.datos, departamento: e.target.value}})}
                placeholder="Ej: Administración"
              />
            </div>
            <div>
              <Label>Sueldo Base Semanal</Label>
              <Input 
                type="number"
                value={formSolicitud.datos.sueldo_base || ''}
                onChange={(e) => setFormSolicitud({...formSolicitud, datos: {...formSolicitud.datos, sueldo_base: parseFloat(e.target.value) || 0}})}
                placeholder="0.00"
              />
            </div>
          </div>
        );
      case 'tipos_incidencias':
        return (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Código *</Label>
                <Input 
                  value={formSolicitud.datos.codigo || ''}
                  onChange={(e) => setFormSolicitud({...formSolicitud, datos: {...formSolicitud.datos, codigo: e.target.value.toUpperCase()}})}
                  placeholder="Ej: BON"
                  maxLength={10}
                />
              </div>
              <div>
                <Label>Categoría *</Label>
                <select
                  value={formSolicitud.datos.categoria || 'Descuento'}
                  onChange={(e) => setFormSolicitud({...formSolicitud, datos: {...formSolicitud.datos, categoria: e.target.value}})}
                  className="w-full h-10 px-3 border rounded-md bg-white text-sm"
                >
                  <option value="Ingreso">+ Ingreso</option>
                  <option value="Descuento">- Descuento</option>
                </select>
              </div>
            </div>
            <div>
              <Label>Descripción *</Label>
              <Input 
                value={formSolicitud.datos.descripcion || ''}
                onChange={(e) => setFormSolicitud({...formSolicitud, datos: {...formSolicitud.datos, descripcion: e.target.value}})}
                placeholder="Ej: Bono de productividad"
              />
            </div>
          </div>
        );
      default:
        return (
          <div className="space-y-3">
            <div>
              <Label>Descripción/Nombre *</Label>
              <Input 
                value={formSolicitud.datos.descripcion || formSolicitud.datos.nombre || ''}
                onChange={(e) => setFormSolicitud({...formSolicitud, datos: {...formSolicitud.datos, descripcion: e.target.value, nombre: e.target.value}})}
                placeholder="Ingrese el valor a agregar"
              />
            </div>
          </div>
        );
    }
  };
  
  // Obtener campos para corrección (similar pero usa formCorreccion)
  const getCamposCorreccion = () => {
    const catalogo = solicitudSeleccionada?.catalogo_id;
    switch(catalogo) {
      case 'puestos':
        return (
          <div className="space-y-3">
            <div>
              <Label>Descripción del Puesto *</Label>
              <Input 
                value={formCorreccion.datos.descripcion || ''}
                onChange={(e) => setFormCorreccion({...formCorreccion, datos: {...formCorreccion.datos, descripcion: e.target.value}})}
                placeholder="Ej: Gerente de Operaciones"
              />
            </div>
            <div>
              <Label>Departamento</Label>
              <Input 
                value={formCorreccion.datos.departamento || ''}
                onChange={(e) => setFormCorreccion({...formCorreccion, datos: {...formCorreccion.datos, departamento: e.target.value}})}
                placeholder="Ej: Administración"
              />
            </div>
            <div>
              <Label>Sueldo Base Semanal</Label>
              <Input 
                type="number"
                value={formCorreccion.datos.sueldo_base || ''}
                onChange={(e) => setFormCorreccion({...formCorreccion, datos: {...formCorreccion.datos, sueldo_base: parseFloat(e.target.value) || 0}})}
                placeholder="0.00"
              />
            </div>
          </div>
        );
      case 'tipos_incidencias':
        return (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Código *</Label>
                <Input 
                  value={formCorreccion.datos.codigo || ''}
                  onChange={(e) => setFormCorreccion({...formCorreccion, datos: {...formCorreccion.datos, codigo: e.target.value.toUpperCase()}})}
                  placeholder="Ej: BON"
                  maxLength={10}
                />
              </div>
              <div>
                <Label>Categoría *</Label>
                <select
                  value={formCorreccion.datos.categoria || 'Descuento'}
                  onChange={(e) => setFormCorreccion({...formCorreccion, datos: {...formCorreccion.datos, categoria: e.target.value}})}
                  className="w-full h-10 px-3 border rounded-md bg-white text-sm"
                >
                  <option value="Ingreso">+ Ingreso</option>
                  <option value="Descuento">- Descuento</option>
                </select>
              </div>
            </div>
            <div>
              <Label>Descripción *</Label>
              <Input 
                value={formCorreccion.datos.descripcion || ''}
                onChange={(e) => setFormCorreccion({...formCorreccion, datos: {...formCorreccion.datos, descripcion: e.target.value}})}
                placeholder="Ej: Bono de productividad"
              />
            </div>
          </div>
        );
      default:
        return (
          <div className="space-y-3">
            <div>
              <Label>Descripción/Nombre *</Label>
              <Input 
                value={formCorreccion.datos.descripcion || formCorreccion.datos.nombre || ''}
                onChange={(e) => setFormCorreccion({...formCorreccion, datos: {...formCorreccion.datos, descripcion: e.target.value, nombre: e.target.value}})}
                placeholder="Ingrese el valor a agregar"
              />
            </div>
          </div>
        );
    }
  };
  
  // Agrupar catálogos por módulo
  const catalogosPorModulo = catalogosDisponibles.reduce((acc, cat) => {
    if (!acc[cat.modulo]) acc[cat.modulo] = [];
    acc[cat.modulo].push(cat);
    return acc;
  }, {});
  
  // Filtrar proveedores
  const proveedoresFiltrados = proveedores
    .filter(s => filtroProveedores === 'all' || s.status === filtroProveedores)
    .filter(s => 
      s.rfc?.toLowerCase().includes(searchProveedores.toLowerCase()) ||
      s.razon_social?.toLowerCase().includes(searchProveedores.toLowerCase()) ||
      s.email?.toLowerCase().includes(searchProveedores.toLowerCase())
    );
  
  const proveedoresPendientesCount = proveedores.filter(s => s.status === 'pending').length;
  
  // Aprobar proveedor
  const handleAprobarProveedor = async () => {
    if (!proveedorSeleccionado) return;
    
    setSavingForm(true);
    try {
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
          approved_by: currentUser?.email
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
      setSavingForm(false);
    }
  };
  
  // Rechazar proveedor
  const handleRechazarProveedor = async (supplier) => {
    if (!confirm(`¿Rechazar proveedor ${supplier.rfc}?`)) return;
    
    try {
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
          approved_by: currentUser?.email
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
  
  // Abrir modal de aprobación de proveedor
  const openProveedorModal = (supplier) => {
    setProveedorSeleccionado(supplier);
    setSucursalesProveedor(supplier.sucursales_asignadas || []);
    setModalProveedor(true);
  };
  
  // Formatear fecha
  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('es-MX', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  };
  
  // Badge de status proveedor
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-zinc-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="mis-tareas-page">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-zinc-800">Mis Tareas</h1>
          <p className="text-sm text-zinc-500">Panel de actividades y solicitudes pendientes</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={loadData}>
            <RefreshCw className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
            Actualizar
          </Button>
          {(misPermisos.puede_solicitar || isAdmin) && (
            <Button size="sm" onClick={handleNuevaSolicitud} data-testid="btn-nueva-solicitud">
              <Plus className="h-4 w-4 mr-1" />
              Nueva Solicitud
            </Button>
          )}
        </div>
      </div>

      {/* KPIs - BANDEJA UNIFICADA */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card className={`border-2 ${pendientesUnificados.contadores.urgentes > 0 ? 'bg-red-50 border-red-300' : 'bg-zinc-50 border-zinc-200'}`}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm ${pendientesUnificados.contadores.urgentes > 0 ? 'text-red-700' : 'text-zinc-600'}`}>Urgentes</p>
                <p className={`text-2xl font-bold ${pendientesUnificados.contadores.urgentes > 0 ? 'text-red-800' : 'text-zinc-800'}`}>
                  {pendientesUnificados.contadores.urgentes}
                </p>
              </div>
              <AlertTriangle className={`h-8 w-8 ${pendientesUnificados.contadores.urgentes > 0 ? 'text-red-500' : 'text-zinc-400'}`} />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-purple-50 border-purple-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-purple-700">Catálogos</p>
                <p className="text-2xl font-bold text-purple-800">{pendientesUnificados.contadores.catalogos}</p>
              </div>
              <FileText className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-700">Proveedores</p>
                <p className="text-2xl font-bold text-blue-800">{pendientesUnificados.contadores.proveedores}</p>
              </div>
              <Building2 className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-amber-50 border-amber-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-amber-700">Nóminas</p>
                <p className="text-2xl font-bold text-amber-800">{pendientesUnificados.contadores.nominas}</p>
              </div>
              <Users className="h-8 w-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-green-50 border-green-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-700">Total Pendiente</p>
                <p className="text-2xl font-bold text-green-800">{pendientesUnificados.contadores.total}</p>
              </div>
              <ClipboardList className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* SECCIÓN URGENTES/VENCIDOS */}
      {pendientesUnificados.urgentes.length > 0 && (
        <Card className="border-red-300 bg-red-50/50">
          <CardHeader className="py-3 bg-red-100/50">
            <CardTitle className="text-base font-medium flex items-center gap-2 text-red-800">
              <AlertTriangle className="h-5 w-5 text-red-600" />
              Urgentes / Vencidos ({pendientesUnificados.urgentes.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-red-100">
              {pendientesUnificados.urgentes.map((item) => (
                <div key={`${item.tipo}-${item.id}`} className="p-4 hover:bg-red-50 transition-colors">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3 flex-1">
                      <div className={`p-2 rounded-lg ${
                        item.tipo === 'catalogo' ? 'bg-purple-100' :
                        item.tipo === 'proveedor' ? 'bg-blue-100' : 'bg-amber-100'
                      }`}>
                        {item.tipo === 'catalogo' && <FileText className="h-5 w-5 text-purple-600" />}
                        {item.tipo === 'proveedor' && <Building2 className="h-5 w-5 text-blue-600" />}
                        {item.tipo === 'nomina' && <Users className="h-5 w-5 text-amber-600" />}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <p className="font-medium text-zinc-800">{item.titulo}</p>
                          {item.vencido && (
                            <span className="px-2 py-0.5 rounded text-xs font-medium bg-red-600 text-white">VENCIDO</span>
                          )}
                          {item.proximo_vencer && !item.vencido && (
                            <span className="px-2 py-0.5 rounded text-xs font-medium bg-yellow-500 text-white">Próximo a vencer</span>
                          )}
                        </div>
                        <p className="text-sm text-zinc-500">{item.descripcion}</p>
                        <p className="text-xs text-zinc-400 mt-1">
                          {item.tipo === 'nomina' 
                            ? `Deadline: ${item.deadline ? new Date(item.deadline).toLocaleString('es-MX') : 'N/A'}`
                            : `Hace ${item.horas_pendiente}h`
                          }
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {item.tipo === 'catalogo' && (
                        <Button size="sm" variant="outline" onClick={() => {
                          setSolicitudSeleccionada(item.data);
                          setModalAprobar(true);
                        }}>
                          <Eye className="h-4 w-4 mr-1" />
                          Revisar
                        </Button>
                      )}
                      {item.tipo === 'proveedor' && (
                        <Button size="sm" variant="outline" onClick={() => openProveedorModal(item.data)}>
                          <Eye className="h-4 w-4 mr-1" />
                          Revisar
                        </Button>
                      )}
                      {item.tipo === 'nomina' && (
                        <Button size="sm" variant="outline" onClick={() => window.location.href = '/recursos-humanos'}>
                          <ArrowRight className="h-4 w-4 mr-1" />
                          Ir a Nóminas
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Notificaciones/Tareas Pendientes */}
        <Card>
          <CardHeader className="py-4">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <Bell className="h-5 w-5 text-amber-500" />
              Notificaciones Pendientes
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {tareas.pendientes.length === 0 ? (
              <div className="p-6 text-center text-zinc-500">
                <CheckCircle2 className="h-12 w-12 mx-auto mb-2 text-green-300" />
                <p>No tiene notificaciones pendientes</p>
              </div>
            ) : (
              <div className="divide-y max-h-[400px] overflow-y-auto">
                {tareas.pendientes.map((t) => (
                  <div key={t.id} className="p-4 hover:bg-zinc-50 flex items-start gap-3">
                    <div className={`p-2 rounded-full ${
                      t.tipo === 'aprobacion_catalogo' ? 'bg-purple-100' : 'bg-blue-100'
                    }`}>
                      {t.tipo === 'aprobacion_catalogo' ? (
                        <FileText className="h-4 w-4 text-purple-600" />
                      ) : (
                        <Bell className="h-4 w-4 text-blue-600" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-zinc-800 text-sm">{t.titulo}</p>
                      <p className="text-xs text-zinc-500 truncate">{t.descripcion}</p>
                      <p className="text-xs text-zinc-400 mt-1">
                        {new Date(t.fecha_creacion).toLocaleDateString('es-MX')}
                      </p>
                    </div>
                    <div className="flex gap-1">
                      {t.solicitud_id && (
                        <Button variant="ghost" size="sm" onClick={() => handleVerDetalle(t.solicitud_id)}>
                          <Eye className="h-4 w-4" />
                        </Button>
                      )}
                      <Button variant="ghost" size="sm" onClick={() => handleMarcarLeida(t.id)}>
                        <Check className="h-4 w-4 text-green-600" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Solicitudes Pendientes de Aprobar (Solo para Supervisor/Admin) */}
        {canApprove && (
          <Card>
            <CardHeader className="py-4">
              <CardTitle className="text-base font-medium flex items-center gap-2">
                <FileText className="h-5 w-5 text-purple-500" />
                Solicitudes Pendientes de Aprobar ({solicitudesPendientes.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {solicitudesPendientes.length === 0 ? (
                <div className="p-6 text-center text-zinc-500">
                  <CheckCircle2 className="h-12 w-12 mx-auto mb-2 text-green-300" />
                  <p>No hay solicitudes pendientes</p>
                </div>
              ) : (
                <div className="divide-y max-h-[400px] overflow-y-auto">
                  {solicitudesPendientes.map((s) => (
                    <div key={s.id} className="p-4 hover:bg-zinc-50">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="px-2 py-0.5 bg-zinc-100 text-zinc-700 text-xs rounded">{s.catalogo_nombre}</span>
                            <span className="text-xs text-zinc-400">{s.modulo}</span>
                            {/* Indicador de nivel */}
                            <span className={`px-2 py-0.5 text-xs rounded-full flex items-center gap-1 ${
                              s.estatus === 'Reenviada' ? 'bg-blue-100 text-blue-700' :
                              s.nivel_actual > 1 ? 'bg-purple-100 text-purple-700' : 'bg-amber-100 text-amber-700'
                            }`}>
                              <Layers className="h-3 w-3" />
                              {s.estatus === 'Reenviada' ? `v${s.version || 1} - Reenviada` : `Nivel ${s.nivel_actual || 1}/${s.niveles_requeridos || 1}`}
                            </span>
                          </div>
                          <p className="font-medium text-zinc-800 text-sm mt-1">
                            {s.datos?.descripcion || s.datos?.nombre || JSON.stringify(s.datos)}
                          </p>
                          <p className="text-xs text-zinc-500">
                            Solicitado por: {s.solicitante_nombre} • {new Date(s.fecha_solicitud).toLocaleDateString('es-MX')}
                          </p>
                        </div>
                        <div className="flex gap-1">
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            onClick={() => handleVerHistorial(s.id)}
                            className="text-zinc-500 hover:bg-zinc-100"
                            title="Ver historial"
                          >
                            <History className="h-4 w-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            onClick={() => handleAbrirAprobar(s)}
                            className="text-green-600 hover:bg-green-50"
                            data-testid={`btn-aprobar-${s.id}`}
                          >
                            <Check className="h-4 w-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            onClick={() => handleAbrirRechazar(s)}
                            className="text-red-600 hover:bg-red-50"
                            data-testid={`btn-rechazar-${s.id}`}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* ===== SECCIONES AGRUPADAS POR TIPO ===== */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* CATÁLOGOS PENDIENTES */}
        <Card className="border-purple-200">
          <CardHeader className="py-3 bg-purple-50">
            <CardTitle className="text-base font-medium flex items-center gap-2 text-purple-800">
              <FileText className="h-5 w-5 text-purple-600" />
              Catálogos ({pendientesUnificados.contadores.catalogos})
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0 max-h-[350px] overflow-y-auto">
            {pendientesUnificados.catalogos.length === 0 ? (
              <div className="p-6 text-center text-zinc-500">
                <CheckCircle2 className="h-10 w-10 mx-auto mb-2 text-green-300" />
                <p className="text-sm">Sin pendientes</p>
              </div>
            ) : (
              <div className="divide-y">
                {pendientesUnificados.catalogos.map((item) => (
                  <div key={item.id} className="p-3 hover:bg-purple-50/50">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm text-zinc-800 truncate">{item.titulo}</p>
                        <p className="text-xs text-zinc-500 truncate">{item.descripcion}</p>
                        <p className="text-xs text-zinc-400 mt-1">Por: {item.solicitante}</p>
                      </div>
                      <Button size="sm" variant="ghost" onClick={() => {
                        setSolicitudSeleccionada(item.data);
                        setModalAprobar(true);
                      }}>
                        <Eye className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
        
        {/* PROVEEDORES PENDIENTES */}
        <Card className="border-blue-200">
          <CardHeader className="py-3 bg-blue-50">
            <CardTitle className="text-base font-medium flex items-center gap-2 text-blue-800">
              <Building2 className="h-5 w-5 text-blue-600" />
              Proveedores ({pendientesUnificados.contadores.proveedores})
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0 max-h-[350px] overflow-y-auto">
            {pendientesUnificados.proveedores.length === 0 ? (
              <div className="p-6 text-center text-zinc-500">
                <CheckCircle2 className="h-10 w-10 mx-auto mb-2 text-green-300" />
                <p className="text-sm">Sin pendientes</p>
              </div>
            ) : (
              <div className="divide-y">
                {pendientesUnificados.proveedores.map((item) => (
                  <div key={item.id} className="p-3 hover:bg-blue-50/50">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm text-zinc-800 truncate">{item.titulo}</p>
                        <p className="text-xs text-zinc-500 truncate">{item.descripcion}</p>
                        <p className="text-xs text-zinc-400 mt-1">Hace {item.horas_pendiente}h</p>
                      </div>
                      <Button size="sm" variant="ghost" onClick={() => openProveedorModal(item.data)}>
                        <Eye className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
        
        {/* NÓMINAS PENDIENTES */}
        <Card className="border-amber-200">
          <CardHeader className="py-3 bg-amber-50">
            <CardTitle className="text-base font-medium flex items-center gap-2 text-amber-800">
              <Users className="h-5 w-5 text-amber-600" />
              Nóminas ({pendientesUnificados.contadores.nominas})
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0 max-h-[350px] overflow-y-auto">
            {pendientesUnificados.nominas.length === 0 ? (
              <div className="p-6 text-center text-zinc-500">
                <CheckCircle2 className="h-10 w-10 mx-auto mb-2 text-green-300" />
                <p className="text-sm">Sin pendientes</p>
              </div>
            ) : (
              <div className="divide-y">
                {pendientesUnificados.nominas.map((item) => (
                  <div key={item.id} className="p-3 hover:bg-amber-50/50">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm text-zinc-800 truncate">{item.titulo}</p>
                        <p className="text-xs text-zinc-500 truncate">{item.descripcion}</p>
                        <p className="text-xs text-zinc-400 mt-1">
                          {item.deadline ? `Límite: ${new Date(item.deadline).toLocaleString('es-MX', {day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'})}` : ''}
                        </p>
                      </div>
                      <Button size="sm" variant="ghost" onClick={() => window.location.href = '/recursos-humanos'}>
                        <ArrowRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Mis Solicitudes - Para ver estado y corregir rechazadas */}
      <Card>
        <CardHeader className="py-4">
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <ClipboardList className="h-5 w-5 text-blue-500" />
            Mis Solicitudes ({misSolicitudes.length})
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {misSolicitudes.length === 0 ? (
            <div className="p-6 text-center text-zinc-500">
              <FileText className="h-12 w-12 mx-auto mb-2 text-zinc-300" />
              <p>No ha creado solicitudes</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-zinc-50 border-y">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-zinc-600">Catálogo</th>
                    <th className="px-4 py-3 text-left font-medium text-zinc-600">Descripción</th>
                    <th className="px-4 py-3 text-center font-medium text-zinc-600">Versión</th>
                    <th className="px-4 py-3 text-center font-medium text-zinc-600">Nivel</th>
                    <th className="px-4 py-3 text-center font-medium text-zinc-600">Estatus</th>
                    <th className="px-4 py-3 text-left font-medium text-zinc-600">Fecha</th>
                    <th className="px-4 py-3 text-center font-medium text-zinc-600">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {misSolicitudes.map((s) => (
                    <tr key={s.id} className="hover:bg-zinc-50">
                      <td className="px-4 py-3">
                        <span className="px-2 py-0.5 bg-zinc-100 text-zinc-700 text-xs rounded">{s.catalogo_nombre}</span>
                      </td>
                      <td className="px-4 py-3 font-medium text-zinc-800">
                        {s.datos?.descripcion || s.datos?.nombre || '-'}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="px-2 py-0.5 bg-zinc-100 text-zinc-600 text-xs rounded">v{s.version || 1}</span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <div className="flex items-center justify-center gap-1">
                          {Array.from({length: s.niveles_requeridos || 1}).map((_, i) => (
                            <div key={i} className={`w-2 h-2 rounded-full ${
                              i < (s.aprobaciones?.length || 0) ? 'bg-green-500' :
                              i < (s.nivel_actual || 1) ? 'bg-amber-500' : 'bg-zinc-200'
                            }`} title={`Nivel ${i+1}`} />
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          s.estatus === 'Aprobada' ? 'bg-green-100 text-green-700' :
                          s.estatus?.includes('Rechazada') ? 'bg-red-100 text-red-700' :
                          s.estatus === 'Reenviada' ? 'bg-blue-100 text-blue-700' :
                          'bg-amber-100 text-amber-700'
                        }`}>
                          {s.estatus}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-zinc-500 text-xs">
                        {new Date(s.fecha_solicitud).toLocaleDateString('es-MX')}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <div className="flex justify-center gap-1">
                          <Button variant="ghost" size="sm" onClick={() => handleVerHistorial(s.id)} title="Ver historial">
                            <History className="h-4 w-4 text-zinc-500" />
                          </Button>
                          {s.estatus === 'Rechazada - Pendiente Corrección' && (
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              onClick={() => handleAbrirCorregir(s)}
                              className="text-blue-600 hover:bg-blue-50"
                              title="Corregir y reenviar"
                            >
                              <Edit className="h-4 w-4" />
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
        </CardContent>
      </Card>

      {/* Proveedores Pendientes de Aprobación (Solo Supervisor/Admin) */}
      {canApprove && proveedoresPendientesCount > 0 && (
        <Card className="border-yellow-200 bg-yellow-50/50">
          <CardHeader className="py-4">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <Building2 className="h-5 w-5 text-yellow-600" />
              Proveedores Pendientes de Aprobación
              <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded-full text-xs font-medium">
                {proveedoresPendientesCount}
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {proveedores.filter(p => p.status === 'pending').map(supplier => (
                <div key={supplier.id} className="flex items-center justify-between p-3 bg-white rounded-lg border border-yellow-200">
                  <div className="flex items-center gap-4">
                    <div className="bg-yellow-100 p-2 rounded-lg">
                      <Building2 className="h-5 w-5 text-yellow-600" />
                    </div>
                    <div>
                      <p className="font-mono font-medium text-zinc-900">{supplier.rfc}</p>
                      <p className="text-sm text-zinc-600">{supplier.razon_social || supplier.nombre_contacto}</p>
                      <p className="text-xs text-zinc-500">{supplier.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-zinc-500">
                      {formatDate(supplier.created_at)}
                    </span>
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
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Modal Aprobar Proveedor */}
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
              </div>
              
              {proveedorSeleccionado.status === 'pending' && (
                <div className="space-y-2">
                  <Label>Sucursales Asignadas:</Label>
                  <div className="border rounded-lg p-3 max-h-48 overflow-y-auto space-y-2">
                    {serversDisponibles.map(server => (
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
              <Button variant="outline" onClick={() => setModalProveedor(false)}>Cancelar</Button>
              {proveedorSeleccionado.status === 'pending' && (
                <Button 
                  onClick={handleAprobarProveedor} 
                  disabled={savingForm}
                  className="bg-emerald-600 hover:bg-emerald-700"
                >
                  {savingForm ? <RefreshCw className="h-4 w-4 animate-spin mr-1" /> : <Check className="h-4 w-4 mr-1" />}
                  Aprobar Proveedor
                </Button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal Nueva Solicitud */}
      {modalSolicitud && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-hidden flex flex-col">
            <div className="bg-zinc-800 text-white px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Plus className="h-5 w-5" />
                Nueva Solicitud de Alta
              </h2>
              <button onClick={() => setModalSolicitud(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4 overflow-y-auto flex-1">
              <div className="space-y-2">
                <Label>Catálogo *</Label>
                <select
                  value={formSolicitud.catalogo_id}
                  onChange={(e) => setFormSolicitud({...formSolicitud, catalogo_id: e.target.value, datos: {}})}
                  className="w-full h-10 px-3 border rounded-md bg-white text-sm"
                  data-testid="select-catalogo"
                >
                  <option value="">Seleccione un catálogo...</option>
                  {Object.entries(catalogosPorModulo).map(([modulo, cats]) => (
                    <optgroup key={modulo} label={modulo}>
                      {cats.filter(c => isAdmin || misPermisos.catalogos_permitidos.includes(c.id)).map((c) => (
                        <option key={c.id} value={c.id}>{c.nombre}</option>
                      ))}
                    </optgroup>
                  ))}
                </select>
              </div>
              
              {formSolicitud.catalogo_id && getCamposCatalogo()}
              
              <div className="space-y-2">
                <Label>Notas adicionales</Label>
                <textarea
                  value={formSolicitud.notas}
                  onChange={(e) => setFormSolicitud({...formSolicitud, notas: e.target.value})}
                  className="w-full h-20 px-3 py-2 border rounded-md text-sm resize-none"
                  placeholder="Justificación o comentarios..."
                />
              </div>
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end gap-2 bg-zinc-50">
              <Button variant="outline" onClick={() => setModalSolicitud(false)}>Cancelar</Button>
              <Button onClick={handleCrearSolicitud} disabled={savingForm} data-testid="btn-enviar-solicitud">
                {savingForm ? <RefreshCw className="h-4 w-4 animate-spin mr-1" /> : <ChevronRight className="h-4 w-4 mr-1" />}
                Enviar Solicitud
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Aprobar con Firma */}
      {modalAprobar && solicitudSeleccionada && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
            <div className="bg-green-600 text-white px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Check className="h-5 w-5" />
                Aprobar Solicitud
              </h2>
              <button onClick={() => setModalAprobar(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div className="bg-zinc-50 rounded-lg p-4">
                <p className="text-sm text-zinc-600">Catálogo: <strong>{solicitudSeleccionada.catalogo_nombre}</strong></p>
                <p className="text-sm text-zinc-600">Solicitante: <strong>{solicitudSeleccionada.solicitante_nombre}</strong></p>
                <p className="text-sm text-zinc-800 font-medium mt-2">
                  {solicitudSeleccionada.datos?.descripcion || solicitudSeleccionada.datos?.nombre}
                </p>
              </div>
              
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <p className="text-sm text-amber-800 font-medium flex items-center gap-2">
                  <Lock className="h-4 w-4" />
                  Firma de Autorización
                </p>
                <p className="text-xs text-amber-700 mt-1">
                  Ingrese su contraseña para confirmar la aprobación
                </p>
              </div>
              
              <div className="space-y-2">
                <Label>Contraseña *</Label>
                <Input
                  type="password"
                  value={passwordAprobacion}
                  onChange={(e) => setPasswordAprobacion(e.target.value)}
                  placeholder="Ingrese su contraseña"
                  data-testid="input-password-aprobacion"
                />
              </div>
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end gap-2 bg-zinc-50">
              <Button variant="outline" onClick={() => setModalAprobar(false)}>Cancelar</Button>
              <Button onClick={handleAprobar} disabled={savingForm} className="bg-green-600 hover:bg-green-700" data-testid="btn-confirmar-aprobar">
                {savingForm ? <RefreshCw className="h-4 w-4 animate-spin mr-1" /> : <Check className="h-4 w-4 mr-1" />}
                Aprobar
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Rechazar */}
      {modalRechazar && solicitudSeleccionada && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
            <div className="bg-red-600 text-white px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <X className="h-5 w-5" />
                Rechazar Solicitud
              </h2>
              <button onClick={() => setModalRechazar(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div className="bg-zinc-50 rounded-lg p-4">
                <p className="text-sm text-zinc-600">Catálogo: <strong>{solicitudSeleccionada.catalogo_nombre}</strong></p>
                <p className="text-sm text-zinc-600">Solicitante: <strong>{solicitudSeleccionada.solicitante_nombre}</strong></p>
              </div>
              
              <div className="space-y-2">
                <Label>Motivo del Rechazo</Label>
                <textarea
                  value={motivoRechazo}
                  onChange={(e) => setMotivoRechazo(e.target.value)}
                  className="w-full h-24 px-3 py-2 border rounded-md text-sm resize-none"
                  placeholder="Explique el motivo del rechazo..."
                />
              </div>
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end gap-2 bg-zinc-50">
              <Button variant="outline" onClick={() => setModalRechazar(false)}>Cancelar</Button>
              <Button onClick={handleRechazar} disabled={savingForm} variant="destructive" data-testid="btn-confirmar-rechazar">
                {savingForm ? <RefreshCw className="h-4 w-4 animate-spin mr-1" /> : <X className="h-4 w-4 mr-1" />}
                Rechazar
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Detalle Solicitud */}
      {modalDetalle && solicitudSeleccionada && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
            <div className="bg-zinc-800 text-white px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Detalle de Solicitud</h2>
              <button onClick={() => setModalDetalle(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-zinc-500">Catálogo</p>
                  <p className="font-medium">{solicitudSeleccionada.catalogo_nombre}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Módulo</p>
                  <p className="font-medium">{solicitudSeleccionada.modulo}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Estatus</p>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    solicitudSeleccionada.estatus === 'Aprobada' ? 'bg-green-100 text-green-700' :
                    solicitudSeleccionada.estatus === 'Rechazada' ? 'bg-red-100 text-red-700' :
                    'bg-amber-100 text-amber-700'
                  }`}>
                    {solicitudSeleccionada.estatus}
                  </span>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Fecha</p>
                  <p className="font-medium">{new Date(solicitudSeleccionada.fecha_solicitud).toLocaleDateString('es-MX')}</p>
                </div>
              </div>
              
              <div>
                <p className="text-xs text-zinc-500">Solicitante</p>
                <p className="font-medium">{solicitudSeleccionada.solicitante_nombre}</p>
              </div>
              
              <div>
                <p className="text-xs text-zinc-500">Datos</p>
                <pre className="bg-zinc-50 p-3 rounded text-xs overflow-x-auto">
                  {JSON.stringify(solicitudSeleccionada.datos, null, 2)}
                </pre>
              </div>
              
              {solicitudSeleccionada.notas && (
                <div>
                  <p className="text-xs text-zinc-500">Notas</p>
                  <p className="text-sm">{solicitudSeleccionada.notas}</p>
                </div>
              )}
              
              {solicitudSeleccionada.motivo_rechazo && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <p className="text-xs text-red-600">Motivo de Rechazo</p>
                  <p className="text-sm text-red-800">{solicitudSeleccionada.motivo_rechazo}</p>
                </div>
              )}
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end bg-zinc-50">
              <Button variant="outline" onClick={() => setModalDetalle(false)}>Cerrar</Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Historial de Trazabilidad */}
      {modalHistorial && historialSolicitud && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
            <div className="bg-zinc-800 text-white px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <History className="h-5 w-5" />
                Historial de Trazabilidad
              </h2>
              <button onClick={() => setModalHistorial(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4 overflow-y-auto flex-1">
              {/* Info general */}
              <div className="bg-zinc-50 rounded-lg p-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-xs text-zinc-500">Catálogo</p>
                  <p className="font-medium text-sm">{historialSolicitud.catalogo}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Versión Actual</p>
                  <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded">v{historialSolicitud.version_actual}</span>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Estatus</p>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    historialSolicitud.estatus_actual === 'Aprobada' ? 'bg-green-100 text-green-700' :
                    historialSolicitud.estatus_actual?.includes('Rechazada') ? 'bg-red-100 text-red-700' :
                    'bg-amber-100 text-amber-700'
                  }`}>
                    {historialSolicitud.estatus_actual}
                  </span>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Nivel</p>
                  <div className="flex items-center gap-1">
                    {Array.from({length: historialSolicitud.niveles_requeridos}).map((_, i) => (
                      <div key={i} className={`w-3 h-3 rounded-full ${
                        i < (historialSolicitud.aprobaciones?.length || 0) ? 'bg-green-500' :
                        i < historialSolicitud.nivel_actual ? 'bg-amber-500' : 'bg-zinc-200'
                      }`} />
                    ))}
                    <span className="text-xs text-zinc-500 ml-1">
                      ({historialSolicitud.nivel_actual}/{historialSolicitud.niveles_requeridos})
                    </span>
                  </div>
                </div>
              </div>

              {/* Timeline de eventos */}
              <div className="space-y-1">
                <h3 className="font-medium text-sm text-zinc-700 mb-3">Línea de Tiempo ({historialSolicitud.total_eventos} eventos)</h3>
                <div className="relative">
                  {historialSolicitud.historial.map((evento, idx) => (
                    <div key={evento.id} className="flex gap-4 pb-6 relative">
                      {/* Línea vertical */}
                      {idx < historialSolicitud.historial.length - 1 && (
                        <div className="absolute left-4 top-8 w-0.5 h-full bg-zinc-200" />
                      )}
                      
                      {/* Icono del evento */}
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                        evento.accion === 'CREACION' ? 'bg-blue-100 text-blue-600' :
                        evento.accion === 'APROBACION_FINAL' ? 'bg-green-100 text-green-600' :
                        evento.accion === 'APROBACION_NIVEL' ? 'bg-green-50 text-green-500' :
                        evento.accion === 'RECHAZO' ? 'bg-red-100 text-red-600' :
                        evento.accion === 'CORRECCION' ? 'bg-amber-100 text-amber-600' :
                        'bg-zinc-100 text-zinc-600'
                      }`}>
                        {evento.accion === 'CREACION' ? <Plus className="h-4 w-4" /> :
                         evento.accion?.includes('APROBACION') ? <Check className="h-4 w-4" /> :
                         evento.accion === 'RECHAZO' ? <X className="h-4 w-4" /> :
                         evento.accion === 'CORRECCION' ? <Edit className="h-4 w-4" /> :
                         <Clock className="h-4 w-4" />}
                      </div>
                      
                      {/* Contenido del evento */}
                      <div className="flex-1 min-w-0 bg-white border rounded-lg p-3">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <p className="font-medium text-sm text-zinc-800">{evento.descripcion}</p>
                            <p className="text-xs text-zinc-500">
                              {evento.usuario_nombre || evento.usuario_email}
                            </p>
                          </div>
                          <span className="text-xs text-zinc-400 shrink-0">
                            {new Date(evento.timestamp).toLocaleString('es-MX', {
                              day: '2-digit', month: 'short', year: 'numeric',
                              hour: '2-digit', minute: '2-digit'
                            })}
                          </span>
                        </div>
                        
                        {/* Cambio de estatus */}
                        {evento.estatus_anterior && evento.estatus_nuevo && (
                          <div className="flex items-center gap-2 mt-2 text-xs">
                            <span className="text-zinc-500">{evento.estatus_anterior || 'Nuevo'}</span>
                            <ArrowRight className="h-3 w-3 text-zinc-400" />
                            <span className="font-medium text-zinc-700">{evento.estatus_nuevo}</span>
                          </div>
                        )}
                        
                        {/* Motivo de rechazo */}
                        {evento.motivo && (
                          <div className="mt-2 text-xs bg-red-50 text-red-700 p-2 rounded">
                            <strong>Motivo:</strong> {evento.motivo}
                          </div>
                        )}
                        
                        {/* Comentario */}
                        {evento.comentario && (
                          <div className="mt-2 text-xs bg-zinc-50 text-zinc-600 p-2 rounded italic">
                            "{evento.comentario}"
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end bg-zinc-50">
              <Button variant="outline" onClick={() => setModalHistorial(false)}>Cerrar</Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Corregir y Reenviar */}
      {modalCorregir && solicitudSeleccionada && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-hidden flex flex-col">
            <div className="bg-blue-600 text-white px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <RotateCcw className="h-5 w-5" />
                Corregir y Reenviar Solicitud
              </h2>
              <button onClick={() => setModalCorregir(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4 overflow-y-auto flex-1">
              {/* Motivo de rechazo anterior */}
              {solicitudSeleccionada.motivo_rechazo && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="font-medium text-red-800 text-sm flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4" />
                    Motivo del rechazo:
                  </p>
                  <p className="text-sm text-red-700 mt-1">{solicitudSeleccionada.motivo_rechazo}</p>
                </div>
              )}
              
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-sm text-blue-700">
                  <strong>Catálogo:</strong> {solicitudSeleccionada.catalogo_nombre} • 
                  <strong> Versión actual:</strong> {solicitudSeleccionada.version || 1}
                </p>
              </div>
              
              {/* Campos de corrección */}
              {getCamposCorreccion()}
              
              <div className="space-y-2">
                <Label>Notas adicionales</Label>
                <textarea
                  value={formCorreccion.notas}
                  onChange={(e) => setFormCorreccion({...formCorreccion, notas: e.target.value})}
                  className="w-full h-20 px-3 py-2 border rounded-md text-sm resize-none"
                  placeholder="Explique las correcciones realizadas..."
                />
              </div>
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end gap-2 bg-zinc-50">
              <Button variant="outline" onClick={() => setModalCorregir(false)}>Cancelar</Button>
              <Button onClick={handleCorregirYReenviar} disabled={savingForm} className="bg-blue-600 hover:bg-blue-700">
                {savingForm ? <RefreshCw className="h-4 w-4 animate-spin mr-1" /> : <RotateCcw className="h-4 w-4 mr-1" />}
                Corregir y Reenviar
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
