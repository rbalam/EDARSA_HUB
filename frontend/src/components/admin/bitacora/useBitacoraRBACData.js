/**
 * useBitacoraRBACData - Hook para datos de Bitácora RBAC
 * Extrae la lógica de estado y fetching del componente principal.
 */
import { useState, useEffect, useCallback } from 'react';
// FASE AUTH-SECURITY-01 / FASE 4.1: getToken eliminado, auth viaja en cookie httpOnly

const API_URL = process.env.REACT_APP_BACKEND_URL || '';
const LIMIT = 50;

export function useBitacoraRBACData() {
  // Estado de datos
  const [eventos, setEventos] = useState([]);
  const [total, setTotal] = useState(0);
  const [pagina, setPagina] = useState(1);
  const [paginasTotal, setPaginasTotal] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Estado de filtros
  const [filtros, setFiltros] = useState({
    fecha_inicio: '',
    fecha_fin: '',
    email: '',
    resultado: '',
    tipo: ''
  });
  const [filtrosAplicados, setFiltrosAplicados] = useState({});

  // Estado de modal de detalle
  const [detalleOpen, setDetalleOpen] = useState(false);
  const [eventoDetalle, setEventoDetalle] = useState(null);

  // Cargar eventos
  const cargarEventos = useCallback(async (paginaNum = 1, filtrosActuales = {}) => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      
      params.append('skip', ((paginaNum - 1) * LIMIT).toString());
      params.append('limit', LIMIT.toString());

      // Agregar filtros
      if (filtrosActuales.fecha_inicio) params.append('fecha_inicio', filtrosActuales.fecha_inicio);
      if (filtrosActuales.fecha_fin) params.append('fecha_fin', filtrosActuales.fecha_fin);
      if (filtrosActuales.email) params.append('email', filtrosActuales.email);
      if (filtrosActuales.resultado) params.append('resultado', filtrosActuales.resultado);
      if (filtrosActuales.tipo) params.append('tipo', filtrosActuales.tipo);

      const response = await fetch(`${API_URL}/api/admin/bitacora?${params.toString()}`, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('Acceso denegado. Solo SuperAdministrador puede ver la bitácora.');
        }
        throw new Error('Error al cargar la bitácora');
      }

      const data = await response.json();
      setEventos(data.eventos || []);
      setTotal(data.total || 0);
      setPagina(data.pagina || 1);
      setPaginasTotal(data.paginas_total || 1);
    } catch (err) {
      setError(err.message);
      setEventos([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Cargar al montar
  useEffect(() => {
    cargarEventos(1, {});
  }, [cargarEventos]);

  // Aplicar filtros
  const handleAplicarFiltros = useCallback(() => {
    setFiltrosAplicados({ ...filtros });
    setPagina(1);
    cargarEventos(1, filtros);
  }, [filtros, cargarEventos]);

  // Limpiar filtros
  const handleLimpiarFiltros = useCallback(() => {
    const filtrosVacios = {
      fecha_inicio: '',
      fecha_fin: '',
      email: '',
      resultado: '',
      tipo: ''
    };
    setFiltros(filtrosVacios);
    setFiltrosAplicados({});
    setPagina(1);
    cargarEventos(1, {});
  }, [cargarEventos]);

  // Paginación
  const handlePaginaAnterior = useCallback(() => {
    if (pagina > 1) {
      const nuevaPagina = pagina - 1;
      setPagina(nuevaPagina);
      cargarEventos(nuevaPagina, filtrosAplicados);
    }
  }, [pagina, filtrosAplicados, cargarEventos]);

  const handlePaginaSiguiente = useCallback(() => {
    if (pagina < paginasTotal) {
      const nuevaPagina = pagina + 1;
      setPagina(nuevaPagina);
      cargarEventos(nuevaPagina, filtrosAplicados);
    }
  }, [pagina, paginasTotal, filtrosAplicados, cargarEventos]);

  // Ver detalle de evento
  const handleVerDetalle = useCallback((evento) => {
    setEventoDetalle(evento);
    setDetalleOpen(true);
  }, []);

  // Cerrar modal
  const handleCerrarDetalle = useCallback(() => {
    setDetalleOpen(false);
    setEventoDetalle(null);
  }, []);

  // Actualizar filtro individual
  const updateFiltro = useCallback((key, value) => {
    setFiltros(prev => ({ ...prev, [key]: value }));
  }, []);

  return {
    // Estado
    eventos,
    total,
    pagina,
    paginasTotal,
    loading,
    error,
    filtros,
    filtrosAplicados,
    detalleOpen,
    eventoDetalle,
    LIMIT,
    
    // Acciones
    cargarEventos,
    handleAplicarFiltros,
    handleLimpiarFiltros,
    handlePaginaAnterior,
    handlePaginaSiguiente,
    handleVerDetalle,
    handleCerrarDetalle,
    updateFiltro,
    setDetalleOpen
  };
}

export default useBitacoraRBACData;
