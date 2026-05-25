/**
 * useTesoreriaCorteZData - Hook para datos de Tesorería Corte Z
 * Extrae toda la lógica de estado y fetching del componente principal.
 * 
 * ACTUALIZADO: Filtro de sucursal reemplazado por Unidad de Negocio (server_id)
 * FIX BUG 2026-05-26: Usa fetchUnidadesNegocio centralizado en lugar de /api/servers
 * FIX BUG 2026-05-26: Usa api.js centralizado para autenticación correcta
 */
import { useState, useEffect, useCallback } from 'react';
import logger from '../../services/logger';
import { fetchUnidadesNegocio } from '../../services/unidadesNegocioService';
import api from '../../lib/api';

export function useTesoreriaCorteZData() {
  const [loading, setLoading] = useState(false);
  const [cortesZ, setCortesZ] = useState([]);
  const [cuadres, setCuadres] = useState([]);
  const [resumen, setResumen] = useState(null);
  const [selectedCorte, setSelectedCorte] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [conteoEfectivo, setConteoEfectivo] = useState({ billetes: {}, monedas: {} });
  const [fichaDeposito, setFichaDeposito] = useState({});
  const [filtros, setFiltros] = useState({
    fechaInicio: '',
    fechaFin: '',
    server_id: '',  // Cambiado de 'sucursal' a 'server_id'
    estado: ''
  });
  const [vistaActiva, setVistaActiva] = useState('pendientes');
  
  // Estado para unidades de negocio
  const [unidadesNegocio, setUnidadesNegocio] = useState([]);
  const [loadingUnidades, setLoadingUnidades] = useState(false);
  
  // Cargar unidades de negocio
  // FIX BUG 2026-05-26: Usa servicio centralizado que maneja auth correctamente
  const loadUnidadesNegocio = useCallback(async () => {
    setLoadingUnidades(true);
    try {
      const unidadesData = await fetchUnidadesNegocio();
      const unidades = (unidadesData || [])
        .filter(s => s.active !== false)
        .map(s => ({ 
          id: s.server_id || s.id,  // Usar server_id para filtrar
          nombre: s.nombre || s.name || s.id 
        }));
      setUnidadesNegocio(unidades);
      
      // Si solo hay 1 unidad, seleccionarla automáticamente
      if (unidades.length === 1) {
        setFiltros(prev => ({ ...prev, server_id: unidades[0].id }));
      }
      
      logger.info(`[Tesoreria] Cargadas ${unidades.length} unidades de negocio`);
    } catch (error) {
      logger.error('Error cargando unidades:', error);
    } finally {
      setLoadingUnidades(false);
    }
  }, []);

  // Cargar Cortes Z disponibles
  const loadCortesZ = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filtros.fechaInicio) params.append('fecha_inicio', filtros.fechaInicio);
      if (filtros.fechaFin) params.append('fecha_fin', filtros.fechaFin);
      if (filtros.server_id) params.append('server_id', filtros.server_id);
      
      // FIX BUG 2026-05-26: Usar api.js centralizado para auth correcta
      const response = await api.get(`/finanzas/tesoreria/cortes-z?${params}`);
      setCortesZ(response.data?.cortes || []);
    } catch (error) {
      logger.error('Error cargando cortes Z:', error);
      setCortesZ([]);
    } finally {
      setLoading(false);
    }
  }, [filtros]);

  // Cargar cuadres registrados
  const loadCuadres = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (filtros.estado) params.append('estado', filtros.estado);
      if (filtros.fechaInicio) params.append('fecha_inicio', filtros.fechaInicio);
      if (filtros.fechaFin) params.append('fecha_fin', filtros.fechaFin);
      // FIX BUG: Agregar filtro de unidad de negocio
      if (filtros.server_id) params.append('server_id', filtros.server_id);
      
      // FIX BUG 2026-05-26: Usar api.js centralizado para auth correcta
      const response = await api.get(`/finanzas/tesoreria/cuadres?${params}`);
      setCuadres(response.data?.cuadres || []);
    } catch (error) {
      logger.error('Error cargando cuadres:', error);
      setCuadres([]);
    }
  }, [filtros]);

  // Cargar resumen
  const loadResumen = useCallback(async () => {
    try {
      // FIX BUG: Agregar filtro de unidad de negocio al resumen
      const params = new URLSearchParams();
      if (filtros.server_id) params.append('server_id', filtros.server_id);
      
      // FIX BUG 2026-05-26: Usar api.js centralizado para auth correcta
      const response = await api.get(`/finanzas/tesoreria/cuadres/resumen?${params}`);
      setResumen(response.data?.resumen);
    } catch (error) {
      logger.error('Error cargando resumen:', error);
      setResumen(null);
    }
  }, [filtros.server_id]);

  // Cargar datos iniciales
  useEffect(() => {
    loadUnidadesNegocio();
    loadCortesZ();
    loadCuadres();
    loadResumen();
  }, [loadCortesZ, loadCuadres, loadResumen, loadUnidadesNegocio]);

  // Abrir modal de cuadre
  const handleIniciarCuadre = useCallback((corte) => {
    setSelectedCorte(corte);
    setConteoEfectivo({ billetes: {}, monedas: {} });
    setFichaDeposito({});
    setModalOpen(true);
  }, []);

  // Guardar cuadre
  const handleGuardarCuadre = useCallback(async () => {
    if (!selectedCorte) return;
    
    setLoading(true);
    try {
      const cuadreData = {
        corte_z: selectedCorte,
        conteo_efectivo: conteoEfectivo,
        ficha_deposito: fichaDeposito,
        observaciones: ''
      };
      
      // FIX BUG 2026-05-26: Usar api.js centralizado para auth correcta
      await api.post('/finanzas/tesoreria/cuadres', cuadreData);
      
      setModalOpen(false);
      loadCortesZ();
      loadCuadres();
      loadResumen();
    } catch (error) {
      logger.error('Error guardando cuadre:', error);
      alert(error.response?.data?.detail || 'Error al guardar cuadre');
    } finally {
      setLoading(false);
    }
  }, [selectedCorte, conteoEfectivo, fichaDeposito, loadCortesZ, loadCuadres, loadResumen]);

  // Calcular total contado
  const calcularTotalContado = useCallback(() => {
    const billetes = conteoEfectivo?.billetes || {};
    const monedas = conteoEfectivo?.monedas || {};
    return (
      (billetes.b1000 || 0) * 1000 +
      (billetes.b500 || 0) * 500 +
      (billetes.b200 || 0) * 200 +
      (billetes.b100 || 0) * 100 +
      (billetes.b50 || 0) * 50 +
      (billetes.b20 || 0) * 20 +
      (monedas.m20 || 0) * 20 +
      (monedas.m10 || 0) * 10 +
      (monedas.m5 || 0) * 5 +
      (monedas.m2 || 0) * 2 +
      (monedas.m1 || 0) * 1 +
      (monedas.m050 || 0) * 0.50
    );
  }, [conteoEfectivo]);

  // Actualizar todos los datos
  const refetchAll = useCallback(() => {
    loadCortesZ();
    loadCuadres();
    loadResumen();
  }, [loadCortesZ, loadCuadres, loadResumen]);

  // Actualizar filtros
  const updateFiltros = useCallback((key, value) => {
    setFiltros(prev => ({ ...prev, [key]: value }));
  }, []);

  // Actualizar ficha de depósito
  const updateFichaDeposito = useCallback((key, value) => {
    setFichaDeposito(prev => ({ ...prev, [key]: value }));
  }, []);

  return {
    // Estado
    loading,
    cortesZ,
    cuadres,
    resumen,
    selectedCorte,
    modalOpen,
    conteoEfectivo,
    fichaDeposito,
    filtros,
    vistaActiva,
    
    // Unidades de negocio
    unidadesNegocio,
    loadingUnidades,
    
    // Setters
    setModalOpen,
    setConteoEfectivo,
    setVistaActiva,
    
    // Acciones
    loadCortesZ,
    loadCuadres,
    loadResumen,
    refetchAll,
    handleIniciarCuadre,
    handleGuardarCuadre,
    calcularTotalContado,
    updateFiltros,
    updateFichaDeposito
  };
}

export default useTesoreriaCorteZData;
