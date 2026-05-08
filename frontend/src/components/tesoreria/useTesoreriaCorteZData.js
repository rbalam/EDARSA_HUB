/**
 * useTesoreriaCorteZData - Hook para datos de Tesorería Corte Z
 * Extrae toda la lógica de estado y fetching del componente principal.
 * 
 * ACTUALIZADO: Filtro de sucursal reemplazado por Unidad de Negocio (server_id)
 */
import { useState, useEffect, useCallback } from 'react';
// FASE AUTH-SECURITY-01 / FASE 4.1: getToken eliminado, auth viaja en cookie httpOnly
import logger from '../../services/logger';

const API_URL = process.env.REACT_APP_BACKEND_URL;

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
  const loadUnidadesNegocio = useCallback(async () => {
    setLoadingUnidades(true);
    try {
      const response = await fetch(`${API_URL}/api/servers`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        const unidades = (data || [])
          .filter(s => s.active !== false)
          .map(s => ({ id: s.id, nombre: s.name || s.nombre || s.id }));
        setUnidadesNegocio(unidades);
        
        // Si solo hay 1 unidad, seleccionarla automáticamente
        if (unidades.length === 1) {
          setFiltros(prev => ({ ...prev, server_id: unidades[0].id }));
        }
      }
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
      
      const response = await fetch(`${API_URL}/api/finanzas/tesoreria/cortes-z?${params}`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setCortesZ(data.cortes || []);
      }
    } catch (error) {
      logger.error('Error cargando cortes Z:', error);
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
      
      const response = await fetch(`${API_URL}/api/finanzas/tesoreria/cuadres?${params}`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setCuadres(data.cuadres || []);
      }
    } catch (error) {
      logger.error('Error cargando cuadres:', error);
    }
  }, [filtros]);

  // Cargar resumen
  const loadResumen = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/finanzas/tesoreria/cuadres/resumen`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setResumen(data.resumen);
      }
    } catch (error) {
      logger.error('Error cargando resumen:', error);
    }
  }, []);

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
      
      const response = await fetch(`${API_URL}/api/finanzas/tesoreria/cuadres`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(cuadreData)
      });
      
      if (response.ok) {
        setModalOpen(false);
        loadCortesZ();
        loadCuadres();
        loadResumen();
      } else {
        const error = await response.json();
        alert(error.detail || 'Error al guardar cuadre');
      }
    } catch (error) {
      logger.error('Error guardando cuadre:', error);
      alert('Error al guardar cuadre');
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
