// P2_2B_FRONT_HARDENING
import logger from '../services/logger';
/**
 * ConfigAsignaciones.jsx
 * =====================
 * UI para gestión de asignaciones de responsables.
 * 
 * MODELO FUNCIONAL: UNIDAD DE NEGOCIO + ALMACÉN → USUARIO RESPONSABLE
 * 
 * Principios:
 * - Solo conceptos de negocio (NO server_id, NO sucursal_id)
 * - Almacenes desde catálogo local
 * - RBAC: Usuario solo opera en su alcance
 */

import React, { useState, useEffect, useCallback } from 'react';
import api, { getToken } from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Switch } from '../components/ui/switch';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../components/ui/alert-dialog';
import { useToast } from '../hooks/use-toast';
import { Toaster } from '../components/ui/toaster';
import {
  Plus,
  Pencil,
  Trash2,
  Search,
  Settings,
  Building2,
  User,
  Package,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Check,
  ChevronRight,
  ChevronDown,
  CloudDownload,
  Clock,
  Loader2,
} from 'lucide-react';
import { Checkbox } from '../components/ui/checkbox';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function ConfigAsignaciones() {
  const { toast } = useToast();
  
  const ensureArray = (value) => Array.isArray(value) ? value : [];
  const asString = (value) => value === null || value === undefined ? '' : String(value);
  // Extrae un mensaje legible de un error de API. Maneja `detail` como string,
  // como array de validación FastAPI [{msg, loc}], o como objeto (evita "[object Object]").
  const getErrorMsg = (err) => {
    const detail = err?.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail.map(d => (d?.msg ? `${d.msg}${d?.loc ? ` (${d.loc.join('.')})` : ''}` : asString(d))).join('; ');
    }
    if (detail && typeof detail === 'object') return detail.msg || JSON.stringify(detail);
    return err?.message || 'Error de conexión';
  };
  
  // Estado principal
  const [asignaciones, setAsignaciones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalAsignaciones, setTotalAsignaciones] = useState(0);
  
  // Filtros
  const [filtroUnidad, setFiltroUnidad] = useState('');
  const [filtroEstado, setFiltroEstado] = useState('');
  const [busqueda, setBusqueda] = useState('');
  
  // Catálogos
  const [unidadesNegocio, setUnidadesNegocio] = useState([]);
  const [almacenesPorUnidad, setAlmacenesPorUnidad] = useState({}); // {unidad_id: [{id, nombre}]}
  const [usuarios, setUsuarios] = useState([]);
  const [cargandoAlmacenes, setCargandoAlmacenes] = useState(false);
  
  // Búsqueda de usuarios
  const [busquedaUsuario, setBusquedaUsuario] = useState('');
  
  // Control de expansión de unidades en el árbol
  const [unidadesExpandidas, setUnidadesExpandidas] = useState({});
  
  // Modal crear/editar
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    unidades_negocio_ids: [],      // Múltiples unidades
    unidad_negocio_id: '',         // Para edición (single)
    almacenes_seleccionados: {},   // {unidad_id: [almacen_ids]} o {unidad_id: 'todos'}
    almacen_id: '',                // Para edición (single)
    usuarios_responsables_ids: [], // Múltiples usuarios (responsabilidad mancomunada)
    usuario_responsable_id: '',    // Para edición (single)
    activa: true,
  });
  const [formErrors, setFormErrors] = useState({});
  const [saving, setSaving] = useState(false);
  
  // Modal eliminar
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deletingItem, setDeletingItem] = useState(null);
  
  // Sincronización de almacenes (solo SuperAdministrador)
  const [syncDialogOpen, setSyncDialogOpen] = useState(false);
  const [syncingUnidad, setSyncingUnidad] = useState(null); // unidad_id que se está sincronizando
  const [syncStatus, setSyncStatus] = useState({}); // {unidad_id: {status, message, count, timestamp}}
  const [userRole, setUserRole] = useState('');
  
  // Obtener rol del usuario del token JWT
  const getUserRole = () => {
    try {
      const token = typeof getToken === 'function' ? getToken() : '';
      if (!token) return '';
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.role || '';
    } catch {
      return '';
    }
  };
  
  const isSuperAdmin = userRole === 'SuperAdministrador';
  
  // =========================================================================
  // FETCH DATA
  // =========================================================================
  
  // Cargar rol del usuario al montar
  useEffect(() => {
    setUserRole(getUserRole());
  }, []);
  
  const fetchAsignaciones = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filtroUnidad) params.append('unidad_negocio_id', filtroUnidad);
      if (filtroEstado !== '') params.append('activa', filtroEstado);
      
      const response = await api.get(`/config-asignaciones?${params.toString()}`);
      
      setAsignaciones(ensureArray(response.data?.data));
      setTotalAsignaciones(response.data?.total || 0);
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || error.message,
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [filtroUnidad, filtroEstado, toast]);
  
  const fetchUnidadesNegocio = async () => {
    try {
      const response = await api.get('/config-asignaciones/unidades-negocio');
      setUnidadesNegocio(ensureArray(response.data?.data));
    } catch (error) {
      logger.error('Error cargando unidades:', error);
    }
  };
  
  // Cargar almacenes para una unidad específica
  const fetchAlmacenesUnidad = async (unidadId) => {
    try {
      const response = await api.get(`/config-asignaciones/almacenes/${unidadId}`);
      // Filtrar la opción "todos" del backend, solo queremos almacenes reales
      return ensureArray(response.data?.data).filter(a => a?.id !== undefined && a?.id !== null && a?.id !== '');
    } catch (error) {
      logger.error('Error cargando almacenes:', error);
      return [];
    }
  };
  
  // Cargar almacenes para todas las unidades seleccionadas
  const cargarAlmacenesParaUnidades = async (unidadIds) => {
    if (!unidadIds || unidadIds.length === 0) {
      setAlmacenesPorUnidad({});
      return;
    }
    
    setCargandoAlmacenes(true);
    const nuevoAlmacenes = {};
    
    for (const unidadId of unidadIds) {
      // Solo cargar si no lo tenemos ya
      if (!almacenesPorUnidad[unidadId]) {
        nuevoAlmacenes[unidadId] = await fetchAlmacenesUnidad(unidadId);
      } else {
        nuevoAlmacenes[unidadId] = almacenesPorUnidad[unidadId];
      }
    }
    
    setAlmacenesPorUnidad(nuevoAlmacenes);
    setCargandoAlmacenes(false);
  };
  
  // Legacy: para edición individual
  const fetchAlmacenes = async (unidadId) => {
    if (!unidadId) return;
    const almacenes = await fetchAlmacenesUnidad(unidadId);
    setAlmacenesPorUnidad({ [unidadId]: almacenes });
  };
  
  const fetchUsuarios = async () => {
    try {
      const response = await api.get('/users');
      // Filtrar usuarios activos
      const rawUsers = ensureArray(response.data?.users || (Array.isArray(response.data) ? response.data : []));
      const activos = rawUsers.filter(u => u?.activo !== false);
      setUsuarios(activos);
    } catch (error) {
      logger.error('Error cargando usuarios:', error);
    }
  };
  
  // Obtener info de sincronización de almacenes
  const fetchSyncInfo = async (unidadId) => {
    try {
      const response = await api.get(`/config-asignaciones/almacenes/${unidadId}/sync-info`);
      if (response.data.data?.ultima_sincronizacion) {
        setSyncStatus(prev => ({
          ...prev,
          [unidadId]: {
            status: 'synced',
            timestamp: response.data.data.ultima_sincronizacion,
            count: response.data.data.total_almacenes,
            usuario: response.data.data.usuario_sync
          }
        }));
      }
    } catch (error) {
      logger.error('Error obteniendo info sync:', error);
    }
  };
  
  // Sincronizar almacenes (solo SuperAdministrador)
  const handleSyncAlmacenes = async (unidadId) => {
    if (!isSuperAdmin) return;
    
    setSyncingUnidad(unidadId);
    setSyncStatus(prev => ({ ...prev, [unidadId]: { status: 'syncing', message: 'Sincronizando...' } }));
    
    try {
      const response = await api.post(`/config-asignaciones/almacenes/sincronizar/${unidadId}`);
      const data = response.data;
      
      setSyncStatus(prev => ({
        ...prev,
        [unidadId]: {
          status: 'success',
          message: data.message,
          count: data.sincronizados,
          timestamp: data.timestamp
        }
      }));
      
      // Refrescar almacenes de esta unidad
      const almacenes = await fetchAlmacenesUnidad(unidadId);
      setAlmacenesPorUnidad(prev => ({ ...prev, [unidadId]: almacenes }));
      
      toast({
        title: 'Sincronización completada',
        description: `${data.sincronizados} almacenes sincronizados para ${data.unidad_negocio_nombre || unidadId}`,
      });
      
    } catch (error) {
      setSyncStatus(prev => ({
        ...prev,
        [unidadId]: { status: 'error', message: error.response?.data?.detail || error.message }
      }));
      
      toast({
        title: 'Error de sincronización',
        description: error.response?.data?.detail || error.message,
        variant: 'destructive',
      });
    } finally {
      setSyncingUnidad(null);
      setSyncDialogOpen(false);
    }
  };
  
  // Abrir diálogo de confirmación de sincronización
  const handleOpenSyncDialog = (unidadId) => {
    setSyncingUnidad(unidadId);
    setSyncDialogOpen(true);
  };
  
  useEffect(() => {
    fetchAsignaciones();
    fetchUnidadesNegocio();
    fetchUsuarios();
  }, [fetchAsignaciones]);
  
  // Cargar almacenes para edición individual
  useEffect(() => {
    if (formData.unidad_negocio_id && editingId) {
      fetchAlmacenes(formData.unidad_negocio_id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formData.unidad_negocio_id, editingId]);
  
  // =========================================================================
  // HANDLERS
  // =========================================================================
  
  const handleOpenCreate = () => {
    setEditingId(null);
    setFormData({
      unidades_negocio_ids: [],
      unidad_negocio_id: '',
      almacenes_seleccionados: {}, // {unidad_id: [almacen_ids]} o {unidad_id: 'todos'}
      almacen_id: '',
      usuarios_responsables_ids: [],
      usuario_responsable_id: '',
      activa: true,
    });
    setFormErrors({});
    setBusquedaUsuario('');
    setAlmacenesPorUnidad({});
    setUnidadesExpandidas({});
    setModalOpen(true);
  };
  
  const handleOpenEdit = (asignacion) => {
    setEditingId(asignacion.id);
    // Usar la misma estructura que creación para el árbol expandible
    const almacenesConfig = {};
    if (asignacion.almacen_id) {
      almacenesConfig[asignacion.unidad_negocio_id] = [asignacion.almacen_id];
    } else {
      almacenesConfig[asignacion.unidad_negocio_id] = 'todos';
    }
    
    setFormData({
      unidades_negocio_ids: [asignacion.unidad_negocio_id],
      unidad_negocio_id: asignacion.unidad_negocio_id,
      almacenes_seleccionados: almacenesConfig,
      almacen_id: asignacion.almacen_id,
      usuarios_responsables_ids: [asignacion.usuario_responsable_id],
      usuario_responsable_id: asignacion.usuario_responsable_id,
      activa: asignacion.activa,
    });
    setFormErrors({});
    setBusquedaUsuario('');
    // Expandir automáticamente la unidad y cargar sus almacenes
    setUnidadesExpandidas({ [asignacion.unidad_negocio_id]: true });
    fetchAlmacenesUnidad(asignacion.unidad_negocio_id).then(almacenes => {
      setAlmacenesPorUnidad(prev => ({ ...prev, [asignacion.unidad_negocio_id]: almacenes }));
    });
    setModalOpen(true);
  };
  
  const handleOpenDelete = (asignacion) => {
    setDeletingItem(asignacion);
    setDeleteDialogOpen(true);
  };
  
  // Toggle selección de unidad de negocio (multiselect en creación, single en edición)
  const handleToggleUnidad = (unidadId) => {
    setFormData(prev => {
      // En modo edición, solo permitir una unidad seleccionada
      if (editingId) {
        const wasSelected = prev.unidades_negocio_ids?.includes(unidadId);
        if (wasSelected) {
          // No permitir deseleccionar en edición - debe haber siempre una unidad
          return prev;
        }
        // Seleccionar la nueva unidad y deseleccionar la anterior
        return {
          ...prev,
          unidades_negocio_ids: [unidadId],
          unidad_negocio_id: unidadId,
          almacenes_seleccionados: { [unidadId]: 'todos' },
          almacen_id: ''
        };
      }
      
      // En modo creación, permitir multiselect
      const current = prev.unidades_negocio_ids || [];
      const isSelected = current.includes(unidadId);
      const nuevasUnidades = isSelected
        ? current.filter(id => id !== unidadId)
        : [...current, unidadId];
      
      // Limpiar almacenes de unidades deseleccionadas
      const nuevosAlmacenes = { ...prev.almacenes_seleccionados };
      if (isSelected) {
        delete nuevosAlmacenes[unidadId];
      } else {
        // Por defecto, seleccionar "todos" para la nueva unidad
        nuevosAlmacenes[unidadId] = 'todos';
      }
      
      return {
        ...prev,
        unidades_negocio_ids: nuevasUnidades,
        almacenes_seleccionados: nuevosAlmacenes
      };
    });
    setFormErrors(prev => ({ ...prev, unidades_negocio_ids: null }));
  };
  
  // Toggle expandir/colapsar unidad para ver almacenes
  const handleToggleExpandirUnidad = async (unidadId, e) => {
    e.stopPropagation(); // Evitar que se dispare el checkbox
    
    const nuevasExpandidas = { ...unidadesExpandidas };
    if (nuevasExpandidas[unidadId]) {
      delete nuevasExpandidas[unidadId];
    } else {
      nuevasExpandidas[unidadId] = true;
      // Cargar almacenes si no los tenemos
      if (!almacenesPorUnidad[unidadId]) {
        setCargandoAlmacenes(true);
        const almacenes = await fetchAlmacenesUnidad(unidadId);
        setAlmacenesPorUnidad(prev => ({ ...prev, [unidadId]: almacenes }));
        setCargandoAlmacenes(false);
      }
    }
    setUnidadesExpandidas(nuevasExpandidas);
  };
  
  // Seleccionar todas las unidades
  const handleSelectAllUnidades = () => {
    const allIds = unidadesNegocio.map(u => u.id);
    const allSelected = formData.unidades_negocio_ids?.length === allIds.length;
    
    if (allSelected) {
      setFormData(prev => ({
        ...prev,
        unidades_negocio_ids: [],
        almacenes_seleccionados: {}
      }));
    } else {
      // Seleccionar todas con "todos" los almacenes
      const todosAlmacenes = {};
      allIds.forEach(id => { todosAlmacenes[id] = 'todos'; });
      setFormData(prev => ({
        ...prev,
        unidades_negocio_ids: allIds,
        almacenes_seleccionados: todosAlmacenes
      }));
    }
    setFormErrors(prev => ({ ...prev, unidades_negocio_ids: null }));
  };
  
  // Toggle "todos los almacenes" para una unidad
  const handleToggleTodosAlmacenes = (unidadId) => {
    setFormData(prev => {
      const nuevosAlmacenes = { ...prev.almacenes_seleccionados };
      nuevosAlmacenes[unidadId] = 'todos';
      // En edición, también actualizar almacen_id
      const updates = { ...prev, almacenes_seleccionados: nuevosAlmacenes };
      if (editingId) {
        updates.almacen_id = '';
      }
      return updates;
    });
  };
  
  // Toggle selección de almacén específico para una unidad
  const handleToggleAlmacenUnidad = (unidadId, almacenId) => {
    setFormData(prev => {
      const nuevosAlmacenes = { ...prev.almacenes_seleccionados };
      const actual = nuevosAlmacenes[unidadId];
      
      if (editingId) {
        // En edición, solo un almacén a la vez (radio button behavior)
        const wasSelected = Array.isArray(actual) && actual.includes(almacenId);
        if (wasSelected) {
          // Deseleccionar = volver a "todos"
          nuevosAlmacenes[unidadId] = 'todos';
          return { ...prev, almacenes_seleccionados: nuevosAlmacenes, almacen_id: '' };
        } else {
          // Seleccionar este almacén
          nuevosAlmacenes[unidadId] = [almacenId];
          return { ...prev, almacenes_seleccionados: nuevosAlmacenes, almacen_id: almacenId };
        }
      }
      
      // En creación, permitir multiselect
      if (actual === 'todos') {
        // Cambiar de "todos" a solo este almacén
        nuevosAlmacenes[unidadId] = [almacenId];
      } else if (Array.isArray(actual)) {
        const isSelected = actual.includes(almacenId);
        if (isSelected) {
          const nuevo = actual.filter(id => id !== almacenId);
          nuevosAlmacenes[unidadId] = nuevo.length > 0 ? nuevo : 'todos';
        } else {
          nuevosAlmacenes[unidadId] = [...actual, almacenId];
        }
      } else {
        nuevosAlmacenes[unidadId] = [almacenId];
      }
      
      return { ...prev, almacenes_seleccionados: nuevosAlmacenes };
    });
  };
  
  // Seleccionar todos los almacenes de una unidad (individualmente)
  const handleSelectAllAlmacenesUnidad = (unidadId) => {
    const almacenesUnidad = almacenesPorUnidad[unidadId] || [];
    if (almacenesUnidad.length === 0) return;
    
    const allIds = almacenesUnidad.map(a => a.id);
    
    setFormData(prev => {
      const nuevosAlmacenes = { ...prev.almacenes_seleccionados };
      const actual = nuevosAlmacenes[unidadId];
      
      // Si ya están todos seleccionados individualmente, cambiar a "todos"
      if (Array.isArray(actual) && actual.length === allIds.length) {
        nuevosAlmacenes[unidadId] = 'todos';
      } else {
        nuevosAlmacenes[unidadId] = allIds;
      }
      
      return { ...prev, almacenes_seleccionados: nuevosAlmacenes };
    });
  };
  
  // Toggle selección de usuario (multiselect)
  const handleToggleUsuario = (usuarioId) => {
    setFormData(prev => {
      const current = prev.usuarios_responsables_ids || [];
      const isSelected = current.includes(usuarioId);
      
      return {
        ...prev,
        usuarios_responsables_ids: isSelected
          ? current.filter(id => id !== usuarioId)
          : [...current, usuarioId]
      };
    });
    setFormErrors(prev => ({ ...prev, usuarios_responsables_ids: null }));
  };
  
  // Seleccionar todos los usuarios filtrados
  const handleSelectAllUsuarios = () => {
    const filteredIds = usuariosFiltrados.map(u => u.id);
    const allSelected = filteredIds.every(id => formData.usuarios_responsables_ids?.includes(id));
    
    setFormData(prev => ({
      ...prev,
      usuarios_responsables_ids: allSelected 
        ? prev.usuarios_responsables_ids.filter(id => !filteredIds.includes(id))
        : [...new Set([...(prev.usuarios_responsables_ids || []), ...filteredIds])]
    }));
    setFormErrors(prev => ({ ...prev, usuarios_responsables_ids: null }));
  };
  
  // Filtrar usuarios por búsqueda
  const usuariosFiltrados = usuarios.filter(u => {
    if (!busquedaUsuario) return true;
    const term = busquedaUsuario.toLowerCase();
    const nombre = (u.name || '').toLowerCase();
    const email = (u.email || '').toLowerCase();
    return nombre.includes(term) || email.includes(term);
  });
  
  const validateForm = () => {
    const errors = {};
    
    if (editingId) {
      // Edición: solo validar usuario
      if (!formData.usuario_responsable_id) {
        errors.usuario_responsable_id = 'Seleccione un usuario responsable';
      }
    } else {
      // Creación: validar unidades y usuarios múltiples
      if (!formData.unidades_negocio_ids || formData.unidades_negocio_ids.length === 0) {
        errors.unidades_negocio_ids = 'Seleccione al menos una unidad de negocio';
      }
      if (!formData.usuarios_responsables_ids || formData.usuarios_responsables_ids.length === 0) {
        errors.usuarios_responsables_ids = 'Seleccione al menos un usuario responsable';
      }
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };
  
  const handleSave = async () => {
    if (!validateForm()) return;
    
    setSaving(true);
    try {
      if (editingId) {
        // Edición: un solo registro
        await api.put(`/config-asignaciones/${editingId}`, {
          usuario_responsable_id: formData.usuario_responsable_id,
          activa: formData.activa,
        });
        
        toast({
          title: 'Éxito',
          description: 'Asignación actualizada correctamente',
        });
      } else {
        // Creación: múltiples combinaciones (unidades x almacenes x usuarios)
        const unidades = formData.unidades_negocio_ids || [];
        const usuariosSeleccionados = formData.usuarios_responsables_ids || [];
        
        let creadas = 0;
        let errores = [];
        
        // Crear todas las combinaciones
        for (const unidadId of unidades) {
          // Obtener almacenes para esta unidad
          const almacenesConfig = formData.almacenes_seleccionados[unidadId];
          let almacenesParaUnidad = [''];  // Por defecto "todos"
          
          if (almacenesConfig && almacenesConfig !== 'todos' && Array.isArray(almacenesConfig)) {
            almacenesParaUnidad = almacenesConfig;
          }
          
          for (const almacenId of almacenesParaUnidad) {
            for (const usuarioId of usuariosSeleccionados) {
              try {
                await api.post('/config-asignaciones', {
                  unidad_negocio_pk: unidadId,
                  almacen_id: almacenId,
                  usuario_responsable_id: usuarioId,
                });
                creadas++;
              } catch (err) {
                const unidadNombre = unidadesNegocio.find(u => asString(u.id) === asString(unidadId))?.nombre || unidadId;
                const usuarioNombre = usuarios.find(u => asString(u.id) === asString(usuarioId))?.name || usuarioId;
                const errorMsg = getErrorMsg(err);
                errores.push(`${unidadNombre} → ${usuarioNombre}: ${errorMsg}`);
              }
            }
          }
        }
        
        if (creadas > 0) {
          toast({
            title: 'Éxito',
            description: `${creadas} asignación(es) creada(s) correctamente`,
          });
        }
        
        if (errores.length > 0) {
          toast({
            title: 'Algunas asignaciones no se crearon',
            description: errores.join('; '),
            variant: 'destructive',
          });
        }
      }
      
      setModalOpen(false);
      fetchAsignaciones();
    } catch (error) {
      toast({
        title: 'Error',
        description: getErrorMsg(error),
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };
  
  const handleDelete = async () => {
    if (!deletingItem) return;
    
    try {
      await api.delete(`/config-asignaciones/${deletingItem.id}`);
      
      toast({
        title: 'Eliminado',
        description: 'La asignación ha sido eliminada',
      });
      
      setDeleteDialogOpen(false);
      setDeletingItem(null);
      fetchAsignaciones();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || error.message,
        variant: 'destructive',
      });
    }
  };
  
  // =========================================================================
  // FILTRADO LOCAL
  // =========================================================================
  
  const asignacionesFiltradas = asignaciones.filter((a) => {
    if (busqueda) {
      const term = busqueda.toLowerCase();
      const matchUnidad = a.unidad_negocio_nombre?.toLowerCase().includes(term);
      const matchAlmacen = a.almacen_nombre?.toLowerCase().includes(term);
      const matchUsuario = a.usuario_responsable_nombre?.toLowerCase().includes(term);
      if (!matchUnidad && !matchAlmacen && !matchUsuario) return false;
    }
    return true;
  });
  
  // =========================================================================
  // RENDER
  // =========================================================================
  
  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <Toaster />
      
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <Settings className="h-8 w-8 text-emerald-400" />
          <h1 className="text-2xl font-bold">Asignaciones de Inventarios</h1>
        </div>
        <p className="text-slate-400">
          Define quién es responsable de justificar diferencias de inventario por unidad de negocio
        </p>
      </div>
      
      {/* Acciones y filtros */}
      <Card className="bg-slate-900 border-slate-800 mb-6">
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-center gap-4">
            <Button
              onClick={handleOpenCreate}
              className="bg-emerald-600 hover:bg-emerald-700"
              data-testid="btn-nueva-asignacion"
            >
              <Plus className="h-4 w-4 mr-2" />
              Nueva Asignación
            </Button>
            
            <div className="flex-1 flex flex-wrap items-center gap-3">
              {/* Búsqueda */}
              <div className="relative flex-1 min-w-[200px] max-w-xs">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Buscar..."
                  value={busqueda}
                  onChange={(e) => setBusqueda(e.target.value)}
                  className="pl-10 bg-slate-800 border-slate-700 text-white"
                  data-testid="input-busqueda"
                />
              </div>
              
              {/* Filtro unidad */}
              <Select value={asString(filtroUnidad || '__todas__')} onValueChange={(v) => setFiltroUnidad(v === '__todas__' ? '' : asString(v))}>
                <SelectTrigger
                  className="w-[180px] bg-slate-800 border-slate-700"
                  data-testid="filtro-unidad"
                >
                  <SelectValue placeholder="Todas las unidades" />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-700">
                  <SelectItem value="__todas__">Todas las unidades</SelectItem>
                  {unidadesNegocio.map((u) => (
                    <SelectItem key={asString(u.id)} value={asString(u.id)}>
                      {u.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              {/* Filtro estado */}
              <Select value={filtroEstado || '__todos__'} onValueChange={(v) => setFiltroEstado(v === '__todos__' ? '' : v)}>
                <SelectTrigger
                  className="w-[140px] bg-slate-800 border-slate-700"
                  data-testid="filtro-estado"
                >
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-700">
                  <SelectItem value="__todos__">Todos</SelectItem>
                  <SelectItem value="true">Activas</SelectItem>
                  <SelectItem value="false">Inactivas</SelectItem>
                </SelectContent>
              </Select>
              
              {/* Refresh */}
              <Button
                variant="outline"
                size="icon"
                onClick={fetchAsignaciones}
                className="border-slate-700"
                data-testid="btn-refresh"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Tabla */}
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Building2 className="h-5 w-5 text-emerald-400" />
            Configuraciones ({totalAsignaciones})
          </CardTitle>
          <CardDescription>
            Matriz de responsables para workflows de inventario
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-slate-400">
              <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2" />
              Cargando...
            </div>
          ) : asignacionesFiltradas.length === 0 ? (
            <div className="text-center py-8 text-slate-400">
              <AlertCircle className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No hay configuraciones de asignación</p>
              <p className="text-sm mt-1">
                Crea una nueva asignación para definir responsables
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-slate-700 hover:bg-slate-800/50">
                  <TableHead className="text-slate-300">Unidad de Negocio</TableHead>
                  <TableHead className="text-slate-300">Almacén</TableHead>
                  <TableHead className="text-slate-300">Responsable</TableHead>
                  <TableHead className="text-slate-300 text-center">Estado</TableHead>
                  <TableHead className="text-slate-300 text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {asignacionesFiltradas.map((a) => (
                  <TableRow
                    key={a.id}
                    className="border-slate-700 hover:bg-slate-800/50"
                    data-testid={`row-asignacion-${a.id}`}
                  >
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Building2 className="h-4 w-4 text-emerald-400" />
                        <span className="font-medium">{a.unidad_negocio_nombre}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Package className="h-4 w-4 text-slate-400" />
                        <span className={a.almacen_nombre ? '' : 'text-slate-500 italic'}>
                          {a.almacen_nombre || '(Todos los almacenes)'}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4 text-blue-400" />
                        <div>
                          <div className="font-medium">{a.usuario_responsable_nombre}</div>
                          <div className="text-xs text-slate-500">
                            {a.usuario_responsable_email}
                          </div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      {a.activa ? (
                        <Badge className="bg-emerald-600/20 text-emerald-400 border-emerald-600/30">
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                          Activa
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-slate-400 border-slate-600">
                          Inactiva
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleOpenEdit(a)}
                          className="h-8 w-8 hover:bg-slate-700 text-slate-400 hover:text-emerald-400"
                          data-testid={`btn-edit-${a.id}`}
                          title="Editar asignación"
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleOpenDelete(a)}
                          className="h-8 w-8 hover:bg-red-900/50 text-red-400"
                          data-testid={`btn-delete-${a.id}`}
                          title="Eliminar asignación"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
      
      {/* Modal Crear/Editar */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="bg-slate-900 border-slate-700 text-white sm:max-w-md">
          <DialogHeader>
            <DialogTitle>
              {editingId ? 'Editar Asignación' : 'Nueva Asignación'}
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              {editingId
                ? 'Modifica el responsable o el estado de la asignación'
                : 'Define quién será responsable de justificar diferencias'}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {/* Unidad de Negocio - Árbol expandible con almacenes */}
            <div className="space-y-2">
              <Label>Unidad(es) de Negocio *</Label>
              <div className={`bg-slate-800 border rounded-md p-3 space-y-1 max-h-64 overflow-y-auto ${
                formErrors.unidades_negocio_ids ? 'border-red-500' : 'border-slate-700'
              }`}>
                {/* Opción Todas - solo en creación */}
                {!editingId && (
                  <div 
                    className="flex items-center gap-2 pb-2 border-b border-slate-700 cursor-pointer hover:bg-slate-700/50 rounded px-2 py-1"
                    onClick={handleSelectAllUnidades}
                  >
                    <Checkbox
                      checked={formData.unidades_negocio_ids?.length === unidadesNegocio.length && unidadesNegocio.length > 0}
                      className="border-slate-600 data-[state=checked]:bg-emerald-600"
                    />
                    <span className="text-sm font-medium text-emerald-400">Todas las unidades</span>
                    <span className="text-xs text-slate-500 ml-auto">
                      ({formData.unidades_negocio_ids?.length || 0}/{unidadesNegocio.length})
                    </span>
                  </div>
                )}
                
                {/* Lista de unidades con árbol expandible */}
                {unidadesNegocio.map((u) => {
                    const isSelected = formData.unidades_negocio_ids?.includes(u.id);
                    const isExpanded = unidadesExpandidas[u.id];
                    const almacenesUnidad = almacenesPorUnidad[u.id] || [];
                    const configAlmacen = formData.almacenes_seleccionados[u.id];
                    const esTodos = configAlmacen === 'todos' || !configAlmacen;
                    
                    return (
                      <div key={u.id} className="border-b border-slate-700/50 last:border-b-0">
                        {/* Fila de la unidad */}
                        <div className="flex items-center gap-1">
                          {/* Botón expandir */}
                          <button
                            type="button"
                            onClick={(e) => handleToggleExpandirUnidad(u.id, e)}
                            className="p-1 hover:bg-slate-700 rounded text-slate-400 hover:text-white transition-colors"
                            title={isExpanded ? 'Colapsar' : 'Ver almacenes'}
                          >
                            {isExpanded ? (
                              <ChevronDown className="h-4 w-4" />
                            ) : (
                              <ChevronRight className="h-4 w-4" />
                            )}
                          </button>
                          
                          {/* Checkbox y nombre */}
                          <div 
                            className="flex-1 flex items-center gap-2 cursor-pointer hover:bg-slate-700/50 rounded px-2 py-1"
                            onClick={() => handleToggleUnidad(u.id)}
                          >
                            <Checkbox
                              checked={isSelected}
                              className="border-slate-600 data-[state=checked]:bg-emerald-600"
                            />
                            <Building2 className="h-4 w-4 text-emerald-400" />
                            <span className="text-sm text-slate-300">{u.nombre}</span>
                            {isSelected && (
                              <span className="text-xs text-slate-500 ml-auto">
                                {esTodos ? '(Todos)' : `(${Array.isArray(configAlmacen) ? configAlmacen.length : 0} alm.)`}
                              </span>
                            )}
                          </div>
                        </div>
                        
                        {/* Almacenes expandidos */}
                        {isExpanded && (
                          <div className="ml-6 pl-3 border-l border-slate-700 py-1 space-y-1">
                            {/* Botón de sincronización - Solo SuperAdministrador */}
                            {isSuperAdmin && (
                              <div className="flex items-center justify-between py-1 px-2 mb-1 bg-slate-900/50 rounded">
                                <div className="flex items-center gap-2">
                                  {syncStatus[u.id]?.status === 'syncing' ? (
                                    <>
                                      <Loader2 className="h-3 w-3 animate-spin text-blue-400" />
                                      <span className="text-xs text-blue-400">Sincronizando...</span>
                                    </>
                                  ) : syncStatus[u.id]?.status === 'success' ? (
                                    <>
                                      <CheckCircle2 className="h-3 w-3 text-emerald-400" />
                                      <span className="text-xs text-emerald-400">
                                        {syncStatus[u.id].count} almacenes
                                      </span>
                                    </>
                                  ) : syncStatus[u.id]?.status === 'error' ? (
                                    <>
                                      <AlertCircle className="h-3 w-3 text-red-400" />
                                      <span className="text-xs text-red-400">Error</span>
                                    </>
                                  ) : almacenesUnidad.length === 0 ? (
                                    <span className="text-xs text-amber-400">Sin sincronizar</span>
                                  ) : (
                                    <span className="text-xs text-slate-500">
                                      {almacenesUnidad.length} en catálogo
                                    </span>
                                  )}
                                </div>
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleOpenSyncDialog(u.id);
                                  }}
                                  disabled={syncingUnidad === u.id}
                                  className="flex items-center gap-1 px-2 py-0.5 text-xs bg-blue-600/20 hover:bg-blue-600/40 text-blue-400 rounded transition-colors disabled:opacity-50"
                                  title="Sincronizar almacenes desde servidor externo"
                                >
                                  <CloudDownload className="h-3 w-3" />
                                  Sync
                                </button>
                              </div>
                            )}
                            
                            {cargandoAlmacenes && !almacenesUnidad.length ? (
                              <div className="text-xs text-slate-500 py-1 flex items-center gap-2">
                                <RefreshCw className="h-3 w-3 animate-spin" />
                                Cargando almacenes...
                              </div>
                            ) : almacenesUnidad.length > 0 ? (
                              <>
                                {/* Opción Todos los almacenes */}
                                <div 
                                  className="flex items-center gap-2 cursor-pointer hover:bg-slate-700/50 rounded px-2 py-1"
                                  onClick={() => {
                                    if (!isSelected) handleToggleUnidad(u.id);
                                    handleToggleTodosAlmacenes(u.id);
                                  }}
                                >
                                  <Checkbox
                                    checked={isSelected && esTodos}
                                    className="border-slate-600 data-[state=checked]:bg-emerald-600"
                                  />
                                  <Package className="h-3 w-3 text-emerald-400" />
                                  <span className="text-xs text-emerald-400 font-medium">(Todos los almacenes)</span>
                                </div>
                                
                                {/* Almacenes individuales */}
                                {almacenesUnidad.map((alm) => {
                                  const almSelected = isSelected && !esTodos && Array.isArray(configAlmacen) && configAlmacen.includes(alm.id);
                                  return (
                                    <div 
                                      key={alm.id}
                                      className="flex items-center gap-2 cursor-pointer hover:bg-slate-700/50 rounded px-2 py-1"
                                      onClick={() => {
                                        if (!isSelected) handleToggleUnidad(u.id);
                                        handleToggleAlmacenUnidad(u.id, alm.id);
                                      }}
                                    >
                                      <Checkbox
                                        checked={almSelected}
                                        className="border-slate-600 data-[state=checked]:bg-emerald-600"
                                      />
                                      <Package className="h-3 w-3 text-slate-500" />
                                      <span className="text-xs text-slate-400">{alm.nombre}</span>
                                    </div>
                                  );
                                })}
                              </>
                            ) : (
                              <div className="text-xs text-slate-500 italic py-1">
                                {isSuperAdmin 
                                  ? 'Sin almacenes. Usa "Sync" para importar desde el servidor.'
                                  : 'Sin almacenes configurados'
                                }
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              {formErrors.unidades_negocio_ids && (
                <p className="text-xs text-red-400">{formErrors.unidades_negocio_ids}</p>
              )}
              {!editingId && (formData.unidades_negocio_ids?.length > 0 || formData.usuarios_responsables_ids?.length > 0) && (
                <p className="text-xs text-emerald-400">
                  Se crearán {(formData.unidades_negocio_ids?.length || 1) * (formData.usuarios_responsables_ids?.length || 1)} asignación(es)
                </p>
              )}
            </div>
            
            
            {/* Usuario(s) Responsable(s) - Multiselect con búsqueda */}
            <div className="space-y-2">
              <Label>Usuario(s) Responsable(s) *</Label>
              <div className={`bg-slate-800 border rounded-md ${
                formErrors.usuarios_responsables_ids || formErrors.usuario_responsable_id ? 'border-red-500' : 'border-slate-700'
              }`}>
                {/* Buscador */}
                <div className="p-2 border-b border-slate-700">
                  <div className="relative">
                    <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input
                      placeholder="Buscar por nombre o email..."
                      value={busquedaUsuario}
                      onChange={(e) => setBusquedaUsuario(e.target.value)}
                      className="pl-8 h-8 bg-slate-900 border-slate-600 text-sm"
                    />
                  </div>
                </div>
                {/* Lista de usuarios */}
                <div className="p-2 space-y-1 max-h-40 overflow-y-auto">
                  {/* Seleccionar todos filtrados - solo en creación */}
                  {!editingId && usuariosFiltrados.length > 0 && (
                    <div 
                      className="flex items-center gap-2 pb-2 mb-2 border-b border-slate-700 cursor-pointer hover:bg-slate-700/50 rounded px-2 py-1"
                      onClick={handleSelectAllUsuarios}
                    >
                      <Checkbox
                        checked={usuariosFiltrados.every(u => formData.usuarios_responsables_ids?.includes(u.id))}
                        className="border-slate-600 data-[state=checked]:bg-emerald-600"
                      />
                      <span className="text-sm font-medium text-emerald-400">
                        Seleccionar todos ({usuariosFiltrados.length})
                      </span>
                    </div>
                  )}
                  {usuariosFiltrados.map((u) => (
                    <div 
                      key={u.id}
                      className="flex items-center gap-2 cursor-pointer hover:bg-slate-700/50 rounded px-2 py-1"
                      onClick={() => {
                        if (editingId) {
                          // En edición: selección única
                          setFormData(prev => ({
                            ...prev,
                            usuarios_responsables_ids: [u.id],
                            usuario_responsable_id: u.id
                          }));
                        } else {
                          handleToggleUsuario(u.id);
                        }
                      }}
                    >
                      <Checkbox
                        checked={editingId 
                          ? formData.usuario_responsable_id === u.id
                          : formData.usuarios_responsables_ids?.includes(u.id)
                        }
                        className="border-slate-600 data-[state=checked]:bg-emerald-600"
                      />
                      <div className="flex flex-col">
                        <span className="text-sm text-slate-300">{u.name || u.email}</span>
                        {u.name && <span className="text-xs text-slate-500">{u.email}</span>}
                      </div>
                    </div>
                  ))}
                  {usuariosFiltrados.length === 0 && (
                    <p className="text-xs text-slate-500 italic text-center py-2">
                      No se encontraron usuarios
                    </p>
                  )}
                </div>
                {/* Contador de seleccionados */}
                {!editingId && formData.usuarios_responsables_ids?.length > 0 && (
                  <div className="px-3 py-2 border-t border-slate-700 text-xs text-emerald-400">
                    {formData.usuarios_responsables_ids.length} usuario(s) seleccionado(s) - Responsabilidad mancomunada
                  </div>
                )}
              </div>
              {formErrors.usuarios_responsables_ids && (
                <p className="text-xs text-red-400">{formErrors.usuarios_responsables_ids}</p>
              )}
              {formErrors.usuario_responsable_id && (
                <p className="text-xs text-red-400">{formErrors.usuario_responsable_id}</p>
              )}
            </div>
            
            {/* Estado (solo en edición) */}
            {editingId && (
              <div className="flex items-center justify-between">
                <div>
                  <Label>Estado</Label>
                  <p className="text-xs text-slate-500">
                    Activa o desactiva esta asignación
                  </p>
                </div>
                <Switch
                  checked={formData.activa}
                  onCheckedChange={(v) => setFormData({ ...formData, activa: v })}
                  data-testid="switch-activa"
                />
              </div>
            )}
          </div>
          
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setModalOpen(false)}
              className="border-slate-700"
            >
              Cancelar
            </Button>
            <Button
              onClick={handleSave}
              disabled={saving}
              className="bg-emerald-600 hover:bg-emerald-700"
              data-testid="btn-guardar"
            >
              {saving ? 'Guardando...' : 'Guardar'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Dialog Confirmar Eliminación */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent className="bg-slate-900 border-slate-700">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-white">
              ¿Eliminar esta asignación?
            </AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="text-slate-400">
                {deletingItem && (
                  <>
                    <div className="mb-2">
                      <strong>{deletingItem.unidad_negocio_nombre}</strong>
                      {deletingItem.almacen_nombre
                        ? ` / ${deletingItem.almacen_nombre}`
                        : ' / (Todos los almacenes)'}
                      <br />
                      → {deletingItem.usuario_responsable_nombre}
                    </div>
                    <div className="text-amber-400">
                      ⚠️ Los inventarios futuros de esta combinación no tendrán
                      responsable asignado automáticamente.
                    </div>
                  </>
                )}
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="bg-slate-800 border-slate-700 text-white hover:bg-slate-700">
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-red-600 hover:bg-red-700"
              data-testid="btn-confirmar-eliminar"
            >
              Sí, eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      
      {/* Dialog Confirmar Sincronización */}
      <AlertDialog open={syncDialogOpen} onOpenChange={setSyncDialogOpen}>
        <AlertDialogContent className="bg-slate-900 border-slate-700">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-white flex items-center gap-2">
              <CloudDownload className="h-5 w-5 text-blue-400" />
              Sincronizar Almacenes
            </AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="text-slate-400 space-y-3">
                <p>
                  ¿Deseas sincronizar los almacenes de{' '}
                  <strong className="text-white">
                    {unidadesNegocio.find(u => u.id === syncingUnidad)?.nombre || syncingUnidad}
                  </strong>
                  ?
                </p>
                <div className="bg-slate-800 rounded p-3 text-sm space-y-2">
                  <p className="text-slate-300">Este proceso:</p>
                  <ul className="list-disc list-inside text-slate-400 space-y-1">
                    <li>Consultará el servidor SQL externo</li>
                    <li>Importará almacenes activos al catálogo local</li>
                    <li>Actualizará nombres si han cambiado</li>
                  </ul>
                </div>
                {syncStatus[syncingUnidad]?.timestamp && (
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <Clock className="h-3 w-3" />
                    Última sync: {new Date(syncStatus[syncingUnidad].timestamp).toLocaleString('es-MX')}
                  </div>
                )}
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="bg-slate-800 border-slate-700 text-white hover:bg-slate-700">
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={() => handleSyncAlmacenes(syncingUnidad)}
              className="bg-blue-600 hover:bg-blue-700"
              data-testid="btn-confirmar-sync"
            >
              <CloudDownload className="h-4 w-4 mr-2" />
              Sincronizar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
