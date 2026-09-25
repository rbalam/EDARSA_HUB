import React, { useState, useEffect, useCallback, useMemo } from 'react';
import logger from '../services/logger';
import { useAuth } from '../contexts/AuthContext';
import api from '../lib/api';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { 
  DollarSign, TrendingUp, TrendingDown, Building2, 
  Plus, RefreshCw, Filter, X, Save, Edit, Trash2,
  ChevronUp, ChevronDown, AlertCircle, FileText, Copy,
  PieChart, BarChart3, Calendar, Download, Printer,
  CreditCard, Clock, CheckCircle2, XCircle, Eye,
  FileSpreadsheet, File, ChevronRight, Upload, Banknote, FileCheck2
} from 'lucide-react';
import { toast } from 'sonner';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart as RechartsPie, Pie, Cell, LineChart, Line
} from 'recharts';
import TesoreriaCorteZ from '../components/TesoreriaCorteZ';
import PropinasTPV from '../components/PropinasTPV';
// MIGRACIÓN SQL-FIRST: Removido fetchUnidadesNegocio, ahora usa Corporate Filters
import { CorporateFiltersProvider } from '../filters/CorporateFiltersProvider';
import { useFinanzasCorporateFilters } from '../filters';
import { FinanzasComprobaciones, FinanzasCuentasPorPagar, FinanzasControlIngresos, FinanzasDashboard, FinanzasDecisionPago, FinanzasPresupuestos } from '../components/finanzas';
import { CuentasBancariasPage } from '../components/finanzas/cuentas-bancarias';
import { Landmark } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

// Colores para gráficos
const COLORS = ['#10b981', '#ef4444', '#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899'];

const getApiErrorDetail = (error, fallback) => {
  const detail = error?.response?.data?.detail;
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (Array.isArray(detail) && detail.length > 0) return detail.map(item => item?.msg || item).join('; ');
  if (detail && typeof detail === 'object') return JSON.stringify(detail);
  return error?.message || fallback;
};

export default function Finanzas() {
  return (
    <CorporateFiltersProvider scope="finanzas">
      <FinanzasContent />
    </CorporateFiltersProvider>
  );
}

function FinanzasContent() {
  // MIGRACIÓN SQL-FIRST: Usar adapter useFinanzasCorporateFilters
  const {
    unidadesNegocio,
    selectedUnidad,
    setSelectedUnidad,
    loadingUnidades,
    unidadActual,
    corporateFilters,
    corporateSelected,
    corporateStatus,
    corporateError
  } = useFinanzasCorporateFilters();
  
  // FASE AUTH-FIX: Usar AuthContext para esperar a que el usuario esté autenticado
  const { user, loading: authLoading } = useAuth();
  
  const [activeTab, setActiveTab] = useState('dashboard');
  const [paymentsGroupOpen, setPaymentsGroupOpen] = useState(true);
  const [effectivePermissions, setEffectivePermissions] = useState(null);
  const [effectivePermissionsLoading, setEffectivePermissionsLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const [dashboard, setDashboard] = useState(null);
  const [presupuestos, setPresupuestos] = useState([]);
  const [categorias, setCategorias] = useState([]);
  
  // Filtros
  const [filtroAnio, setFiltroAnio] = useState(new Date().getFullYear());
  const [filtroMes, setFiltroMes] = useState(new Date().getMonth() + 1);
  
  // Modal states
  const [modalPresupuesto, setModalPresupuesto] = useState(false);
  const [modalScript, setModalScript] = useState(false);
  const [editingPresupuesto, setEditingPresupuesto] = useState(null);
  const [savingForm, setSavingForm] = useState(false);
  const [scriptData, setScriptData] = useState(null);
  
  // Estados para Cuentas por Pagar
  const [cxpData, setCxpData] = useState(null);
  const [cxpResumen, setCxpResumen] = useState(null);
  const [cxpProveedores, setCxpProveedores] = useState([]);
  const [cxpSucursales, setCxpSucursales] = useState([]);  // Sucursales de MPRO para CxP
  const [cxpFiltroSucursal, setCxpFiltroSucursal] = useState('');
  const [cxpFiltroProveedor, setCxpFiltroProveedor] = useState('');
  
  useEffect(() => {
    if (authLoading) return undefined;

    let mounted = true;
    setEffectivePermissionsLoading(true);

    api.get('/auth/me/effective-permissions')
      .then((response) => {
        if (mounted) setEffectivePermissions(response.data || {});
      })
      .catch((error) => {
        logger.error(
          'Error cargando permisos efectivos de Tesorería:',
          error
        );
        if (mounted) setEffectivePermissions({});
      })
      .finally(() => {
        if (mounted) setEffectivePermissionsLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [authLoading]);

  const finanzasPermissions = useMemo(() => {
    const normalize = (value) => String(value || '')
      .toUpperCase()
      .replace(/[^A-Z0-9_]/g, '');

    const flat = effectivePermissions?.permissions_flat;
    const structured = effectivePermissions?.permissions;

    const permissionCodes = (
      Array.isArray(flat)
        ? flat
        : Array.isArray(structured)
          ? structured.map((permission) => (
              typeof permission === 'string'
                ? permission
                : permission?.codigo ||
                  permission?.code ||
                  permission?.permission ||
                  permission?.name
            ))
          : []
    ).filter(Boolean).map(normalize);

    const roleCodes = (
      Array.isArray(effectivePermissions?.roles)
        ? effectivePermissions.roles
        : []
    ).map((role) => (
      typeof role === 'string'
        ? role
        : role?.codigo ||
          role?.code ||
          role?.nombre ||
          role?.name
    )).filter(Boolean).map(normalize);

    const isSuperAdmin = [
      'SUPERADMIN',
      'SUPER_ADMIN',
      'SUPERADMINISTRADOR',
      'SUPER_ADMINISTRADOR'
    ].some((roleCode) => roleCodes.includes(roleCode));

    const allowed = (code) => (
      !effectivePermissionsLoading &&
      (
        isSuperAdmin ||
        permissionCodes.includes(normalize(code))
      )
    );

    const canView = allowed('FINANZAS_VER');

    const canWrite = (
      canView &&
      (
        allowed('FINANZAS_EDITAR') ||
        allowed('FINANZAS_ADMINISTRAR')
      )
    );
    const canAdmin = canView && allowed('FINANZAS_ADMINISTRAR');

    return {
      canView,
      canCreate: canWrite,
      canEdit: canWrite,
      canDelete: canWrite,
      canViewScript: canWrite,
      canAdmin
    };
  }, [
    effectivePermissions,
    effectivePermissionsLoading
  ]);

  const [cxpFechaCorte, setCxpFechaCorte] = useState('');
  const [cxpSoloVencidas, setCxpSoloVencidas] = useState(false);
  const [cxpSoloDecision, setCxpSoloDecision] = useState(false);
  const [cxpExpandidos, setCxpExpandidos] = useState({});  // Control de proveedores expandidos
  const [cxpCategoriasExpandidas, setCxpCategoriasExpandidas] = useState({ A: true, B: true, X: true, M: true });  // Control de categorías expandidas
  const [cxpVistaMode, setCxpVistaMode] = useState('categorias'); // 'categorias' o 'proveedores'
  const [savingDecision, setSavingDecision] = useState(null);
  const [cxpBusquedaProveedor, setCxpBusquedaProveedor] = useState(''); // Búsqueda de proveedor por nombre/RFC/clave
  
  // Función para reagrupar datos: Categoría -> Proveedor -> Facturas
  const reagruparCxPPorProveedores = useCallback((proveedoresData) => {
    if (!proveedoresData || proveedoresData.length === 0) return [];
    
    // Estructura: { categoria: { proveedorNombre: [facturas] } }
    const categorias = {};
    
    proveedoresData.forEach(categoria => {
      const tipoCategoria = categoria.proveedor_id; // A, B o X
      const nombreCategoria = categoria.proveedor_nombre; // "A - ALIMENTOS", etc.
      
      if (!categorias[tipoCategoria]) {
        categorias[tipoCategoria] = {
          tipo: tipoCategoria,
          nombre: nombreCategoria,
          subtotal_saldo: 0,
          subtotal_importe: 0,
          subtotal_a_pagar: 0,
          cantidad_facturas: 0,
          cantidad_vencidas: 0,
          proveedores: {}
        };
      }
      
      // Agrupar facturas por proveedor real
      (categoria.facturas || []).forEach(factura => {
        const provNombre = factura.proveedor_nombre || 'Sin Proveedor';
        
        if (!categorias[tipoCategoria].proveedores[provNombre]) {
          categorias[tipoCategoria].proveedores[provNombre] = {
            proveedor_id: factura.proveedor_id || provNombre,
            proveedor_nombre: provNombre,
            sucursal: factura.sucursal_nombre,
            facturas: [],
            subtotal_saldo: 0,
            subtotal_importe: 0,
            subtotal_a_pagar: 0,
            cantidad_facturas: 0,
            cantidad_vencidas: 0
          };
        }
        
        const prov = categorias[tipoCategoria].proveedores[provNombre];
        prov.facturas.push(factura);
        prov.subtotal_saldo += factura.saldo || 0;
        prov.subtotal_importe += factura.importe_original || factura.importe_total || 0;
        prov.subtotal_a_pagar += factura.decision_pago ? (factura.importe_a_pagar || factura.saldo || 0) : 0;
        prov.cantidad_facturas += 1;
        if (factura.dias_vencida > 0) prov.cantidad_vencidas += 1;
        
        // Acumular en categoría
        categorias[tipoCategoria].subtotal_saldo += factura.saldo || 0;
        categorias[tipoCategoria].subtotal_importe += factura.importe_original || factura.importe_total || 0;
        categorias[tipoCategoria].subtotal_a_pagar += factura.decision_pago ? (factura.importe_a_pagar || factura.saldo || 0) : 0;
        categorias[tipoCategoria].cantidad_facturas += 1;
        if (factura.dias_vencida > 0) categorias[tipoCategoria].cantidad_vencidas += 1;
      });
    });
    
    // Convertir a array y ordenar proveedores por saldo desc
    // Ordenar facturas dentro de cada proveedor por folio_entrada (ascendente: más antigua primero)
    const resultado = Object.values(categorias).map(cat => ({
      ...cat,
      proveedores: Object.values(cat.proveedores).map(prov => ({
        ...prov,
        facturas: prov.facturas.sort((a, b) => {
          const folioA = parseInt(a.folio_entrada) || 0;
          const folioB = parseInt(b.folio_entrada) || 0;
          return folioA - folioB; // Ascendente: más antiguo primero
        })
      })).sort((a, b) => b.subtotal_saldo - a.subtotal_saldo)
    }));
    
    // Ordenar categorías: A, B, X, M (MPRO)
    const orden = { A: 1, B: 2, X: 3, M: 4 };
    return resultado.sort((a, b) => (orden[a.tipo] || 99) - (orden[b.tipo] || 99));
  }, []);
  
  // Función para reagrupar datos solo por Proveedor (vista plana)
  const reagruparCxPSoloProveedores = useCallback((proveedoresData) => {
    if (!proveedoresData || proveedoresData.length === 0) return [];
    
    // Agrupar todas las facturas por proveedor (sin importar categoría)
    const proveedores = {};
    
    proveedoresData.forEach(categoria => {
      (categoria.facturas || []).forEach(factura => {
        const provNombre = factura.proveedor_nombre || 'Sin Proveedor';
        const provRFC = factura.proveedor_rfc || '';
        
        if (!proveedores[provNombre]) {
          proveedores[provNombre] = {
            proveedor_id: factura.proveedor_id || provNombre,
            proveedor_nombre: provNombre,
            proveedor_rfc: provRFC,
            facturas: [],
            subtotal_saldo: 0,
            subtotal_importe: 0,
            subtotal_a_pagar: 0,
            cantidad_facturas: 0,
            cantidad_vencidas: 0
          };
        }
        
        proveedores[provNombre].facturas.push(factura);
        proveedores[provNombre].subtotal_saldo += factura.saldo || 0;
        proveedores[provNombre].subtotal_importe += factura.importe_original || factura.importe_total || 0;
        proveedores[provNombre].subtotal_a_pagar += factura.decision_pago ? (factura.importe_a_pagar || factura.saldo || 0) : 0;
        proveedores[provNombre].cantidad_facturas += 1;
        if (factura.dias_vencida > 0) proveedores[provNombre].cantidad_vencidas += 1;
      });
    });
    
    // Ordenar facturas dentro de cada proveedor por folio_entrada (ascendente: más antigua primero)
    // Ordenar proveedores por saldo descendente
    return Object.values(proveedores).map(prov => ({
      ...prov,
      facturas: prov.facturas.sort((a, b) => {
        const folioA = parseInt(a.folio_entrada) || 0;
        const folioB = parseInt(b.folio_entrada) || 0;
        return folioA - folioB; // Ascendente: más antiguo primero
      })
    })).sort((a, b) => b.subtotal_saldo - a.subtotal_saldo);
  }, []);
  
  // Estados para Control de Ingresos
  const [ingresosSubTab, setIngresosSubTab] = useState('cortes');
  const [cortesData, setCortesData] = useState(null);
  const [saldosPendientes, setSaldosPendientes] = useState(null);
  const [resumenComisiones, setResumenComisiones] = useState(null);
  const [configComisiones, setConfigComisiones] = useState(null);
  const [ingresosFechaInicio, setIngresosFechaInicio] = useState('');
  const [ingresosFechaFin, setIngresosFechaFin] = useState('');
  const [ingresosSoloPendientes, setIngresosSoloPendientes] = useState(false);
  
  // Form
  const [formPresupuesto, setFormPresupuesto] = useState({
    unidad_negocio_pk: '',
    categoria: '',
    subcategoria: '',
    tipo: 'Egreso',
    monto: 0,
    anio: new Date().getFullYear(),
    mes: new Date().getMonth() + 1,
    notas: ''
  });
  
  // FASE AUTH-SECURITY-01: Ya no se usa token, la auth viaja en cookie httpOnly
  
  // === MIGRACIÓN SQL-FIRST: Unidades ahora vienen de Corporate Filters ===
  // Auto-seleccionar si el usuario tiene solo una unidad
  useEffect(() => {
    if (!loadingUnidades && unidadesNegocio.length === 1 && !selectedUnidad) {
      const unidad = unidadesNegocio[0];
      setSelectedUnidad(unidad.id);
      logger.log(`[Finanzas] Auto-seleccionada unidad única: ${unidad.nombre}`);
    }
  }, [loadingUnidades, unidadesNegocio, selectedUnidad]);
  
  // Unidad seleccionada (objeto completo)
  const unidadSeleccionada = useMemo(() => {
    return unidadesNegocio.find(u => u.id === selectedUnidad) || null;
  }, [unidadesNegocio, selectedUnidad]);
  
  const meses = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
  ];
  
  // Fetch helpers
  // FASE P1-FETCH-MIGRATION: Migrado a api.js centralizado
  const fetchWithAuth = useCallback(async (endpoint) => {
    const response = await api.get(endpoint);
    return response.data;
  }, []);
  
  // Load dashboard
  const loadDashboard = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        anio: filtroAnio,
        mes: filtroMes,
        ...(selectedUnidad && { unidad_negocio_pk: selectedUnidad })
      });
      const data = await fetchWithAuth(`/finanzas/dashboard?${params}`);
      setDashboard(data);
    } catch (error) {
      logger.error('Error:', error);
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, filtroAnio, filtroMes, selectedUnidad]);
  
  // Load presupuestos
  const loadPresupuestos = useCallback(async () => {
    if (!finanzasPermissions.canView) {
      setPresupuestos([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const params = new URLSearchParams({
        anio: filtroAnio,
        ...(filtroMes && { mes: filtroMes }),
        ...(selectedUnidad && { unidad_negocio_pk: selectedUnidad })
      });
      const data = await fetchWithAuth(`/finanzas/presupuestos?${params}`);
      setPresupuestos(data.presupuestos || []);
    } catch (error) {
      logger.error('Error:', error);
    } finally {
      setLoading(false);
    }
  }, [
    fetchWithAuth,
    filtroAnio,
    filtroMes,
    selectedUnidad,
    finanzasPermissions.canView
  ]);
  
  // Load sucursales CxP (MPRO - para cuentas por pagar)
  const loadCxpSucursales = useCallback(async () => {
    try {
      const data = await fetchWithAuth('/finanzas/cuentas-por-pagar/sucursales');
      setCxpSucursales(data.sucursales || []);
    } catch (error) {
      logger.error('Error loading CxP sucursales:', error);
    }
  }, [fetchWithAuth]);
  
  // Load categorias
  const loadCategorias = useCallback(async () => {
    try {
      const data = await fetchWithAuth('/finanzas/categorias');
      setCategorias(data.categorias || []);
    } catch (error) {
      logger.error('Error:', error);
    }
  }, [fetchWithAuth]);
  
  // Load Cuentas por Pagar
  const loadCuentasPorPagar = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      
      const unidadCxp = selectedUnidad || cxpFiltroSucursal || '';
      if (unidadCxp) params.append('unidad_negocio_pk', unidadCxp);
      if (cxpFiltroProveedor) params.append('proveedor_id', cxpFiltroProveedor);
      if (cxpFechaCorte) params.append('fecha_corte', cxpFechaCorte);
      if (cxpSoloVencidas) params.append('solo_vencidas', 'true');
      if (cxpSoloDecision) params.append('solo_decision_pago', 'true');
      
      logger.log(`[CxP] Request params: ${params.toString()}`);
      
      const [dataFacturas, dataResumen, dataProveedores] = await Promise.all([
        fetchWithAuth(`/finanzas/cuentas-por-pagar?${params}`),
        fetchWithAuth(`/finanzas/cuentas-por-pagar/resumen?${params}`),
        fetchWithAuth(`/finanzas/cuentas-por-pagar/proveedores?${params}`)
      ]);

      setCxpData(dataFacturas);
      setCxpResumen(dataResumen);
      setCxpProveedores(dataProveedores.proveedores || []);
      
      // PRESERVAR estado de expansión existente, solo agregar nuevos si no existen
      setCxpExpandidos(prevExpandidos => {
        const nuevosExpandidos = { ...prevExpandidos };
        (dataFacturas.proveedores || []).forEach(p => {
          // Solo expandir si no existe estado previo (primera carga)
          if (nuevosExpandidos[p.proveedor_id] === undefined) {
            nuevosExpandidos[p.proveedor_id] = true;
          }
        });
        return nuevosExpandidos;
      });
      
      // También preservar categorías expandidas
      setCxpCategoriasExpandidas(prevCategorias => {
        const nuevasCategorias = { ...prevCategorias };
        (dataFacturas.proveedores || []).forEach(p => {
          const tipo = p.proveedor_id; // A, B, X, M
          if (nuevasCategorias[tipo] === undefined) {
            nuevasCategorias[tipo] = true;
          }
        });
        return nuevasCategorias;
      });
      
    } catch (error) {
      logger.error('Error CxP:', error);
      toast.error(getApiErrorDetail(error, 'Error al cargar cuentas por pagar'));
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, selectedUnidad, cxpFiltroSucursal, cxpFiltroProveedor, cxpFechaCorte, cxpSoloVencidas, cxpSoloDecision]);
  
  // Actualizar decisión de pago
  const handleDecisionPago = async (facturaId, decision, importeAPagar = null) => {
    setSavingDecision(facturaId);
    try {
      const response = await api.put(`/finanzas/cuentas-por-pagar/${facturaId}/decision-pago`, {
        decision_pago: decision,
        importe_a_pagar: importeAPagar
      });
      const facturaBackend = response.data?.factura || {};
      
      // Actualizar estado LOCAL sin recargar todo el tablero
      setCxpData(prevData => {
        if (!prevData?.proveedores) return prevData;
        
        const nuevosProveedores = prevData.proveedores.map(proveedor => ({
          ...proveedor,
          facturas: proveedor.facturas.map(factura => {
            if (factura.factura_id === facturaId) {
              const saldo = parseFloat(factura.saldo) || 0;
              const nuevoImporte = decision
                ? (parseFloat(facturaBackend.importe_a_pagar) || parseFloat(importeAPagar) || saldo)
                : 0;
              return {
                ...factura,
                ...facturaBackend,
                decision_pago: decision,
                importe_a_pagar: nuevoImporte,
                estado_autorizacion_pago: decision
                  ? (facturaBackend.estado_autorizacion_pago || 'PENDIENTE_AUTORIZACION')
                  : (facturaBackend.estado_autorizacion_pago || 'CANCELADO'),
                requiere_autorizacion_pago: Boolean(decision)
              };
            }
            return factura;
          })
        }));
        
        return {
          ...prevData,
          proveedores: nuevosProveedores
        };
      });
      
      toast.success(decision ? 'Marcada para pago' : 'Desmarcada');
      // NO recargar - el estado local ya está actualizado
    } catch (error) {
      logger.error('[CxP] Error al actualizar:', error);
      toast.error(getApiErrorDetail(error, 'Error al actualizar decisión de pago'));
      throw error;
    } finally {
      setSavingDecision(null);
    }
  };

  const handleAutorizarDecisionPago = async (facturaId, autorizar, programarEnvioOrigen = true) => {
    setSavingDecision(facturaId);
    try {
      const response = await api.post(`/finanzas/cuentas-por-pagar/${facturaId}/decision-pago/autorizacion`, {
        autorizar,
        programar_envio_origen: programarEnvioOrigen
      });
      const facturaBackend = response.data?.factura || {};

      setCxpData(prevData => {
        if (!prevData?.proveedores) return prevData;

        const nuevosProveedores = prevData.proveedores.map(proveedor => ({
          ...proveedor,
          facturas: proveedor.facturas.map(factura => (
            factura.factura_id === facturaId
              ? {
                  ...factura,
                  ...facturaBackend,
}
              : factura
          ))
        }));

        return {
          ...prevData,
          proveedores: nuevosProveedores
        };
      });

      toast.success(autorizar ? 'Pago autorizado' : 'Pago rechazado');
    } catch (error) {
      logger.error('[CxP] Error al autorizar decisión de pago:', error);
      toast.error(getApiErrorDetail(error, 'Error al autorizar decisión de pago'));
      throw error;
    } finally {
      setSavingDecision(null);
    }
  };
  
  // Toggle proveedor expandido
  const toggleProveedor = (proveedorId) => {
    setCxpExpandidos(prev => ({
      ...prev,
      [proveedorId]: !prev[proveedorId]
    }));
  };
  
  // Toggle categoría expandida (A, B, X)
  const toggleCategoria = (categoriaId) => {
    setCxpCategoriasExpandidas(prev => ({
      ...prev,
      [categoriaId]: !prev[categoriaId]
    }));
  };
  
  // Expandir todos los grupos y proveedores
  const expandirTodos = () => {
    setCxpCategoriasExpandidas({ A: true, B: true, X: true, M: true });
    // Expandir todos los proveedores
    const todosProveedores = {};
    reagruparCxPPorProveedores(cxpData?.proveedores || []).forEach(cat => {
      cat.proveedores.forEach(prov => {
        todosProveedores[`${cat.tipo}_${prov.proveedor_nombre}`] = true;
      });
    });
    setCxpExpandidos(todosProveedores);
  };
  
  // Colapsar todos los grupos y proveedores
  const colapsarTodos = () => {
    setCxpCategoriasExpandidas({ A: false, B: false, X: false, M: false });
    setCxpExpandidos({});
  };
  
  // Marcar todas las facturas vencidas para pago
  const handleMarcarTodasVencidasPago = async () => {
    // Obtener todas las facturas vencidas no marcadas
    const facturasVencidas = [];
    (cxpData?.proveedores || []).forEach(prov => {
      prov.facturas.forEach(f => {
        if (f.dias_vencida > 0 && !f.decision_pago) {
          facturasVencidas.push(f.factura_id);
        }
      });
    });
    
    if (facturasVencidas.length === 0) {
      toast.info('No hay facturas vencidas sin marcar');
      return;
    }
    
    setLoading(true);
    try {
      const response = await api.put('/finanzas/cuentas-por-pagar/decision-pago-masivo', {
        facturas_ids: facturasVencidas,
        decision_pago: true
      });
      
      const data = response.data;
      toast.success(`${data.actualizadas} facturas vencidas marcadas para pago`);
      loadCuentasPorPagar();
    } catch (error) {
      toast.error(getApiErrorDetail(error, 'Error al marcar facturas'));
    } finally {
      setLoading(false);
    }
  };
  
  // Desmarcar todas las facturas
  const handleDesmarcarTodasPago = async () => {
    const facturasMarcadas = [];
    (cxpData?.proveedores || []).forEach(prov => {
      prov.facturas.forEach(f => {
        if (f.decision_pago) {
          facturasMarcadas.push(f.factura_id);
        }
      });
    });
    
    if (facturasMarcadas.length === 0) {
      toast.info('No hay facturas marcadas');
      return;
    }
    
    setLoading(true);
    try {
      const response = await api.put('/finanzas/cuentas-por-pagar/decision-pago-masivo', {
        facturas_ids: facturasMarcadas,
        decision_pago: false
      });
      
      const data = response.data;
      toast.success(`${data.actualizadas} facturas desmarcadas`);
      loadCuentasPorPagar();
    } catch (error) {
      toast.error(getApiErrorDetail(error, 'Error al desmarcar facturas'));
    } finally {
      setLoading(false);
    }
  };
  
  // Toggle pago de todas las facturas de un proveedor (para doble click en header "Pagar")
  // Toggle pago de todas las facturas de un proveedor (para doble click en header "Pagar")
  const handleTogglePagoProveedor = async (proveedor) => {
    if (!proveedor?.facturas?.length) return;
    
    // Determinar si marcar o desmarcar basado en el estado actual
    // Si al menos una está desmarcada, marcar todas. Si todas están marcadas, desmarcar todas.
    const todasMarcadas = proveedor.facturas.every(f => f.decision_pago === true);
    const nuevaDecision = !todasMarcadas;
    
    const cantidadFacturas = proveedor.facturas.length;
    const proveedorNombre = proveedor.proveedor_nombre;
    
    try {
      const facturasIds = proveedor.facturas.map(f => f.factura_id);
      await api.put('/finanzas/cuentas-por-pagar/decision-pago-masivo', {
        facturas_ids: facturasIds,
        decision_pago: nuevaDecision
      });
      toast.success(
        nuevaDecision
          ? `${cantidadFacturas} facturas de ${proveedorNombre} marcadas para pago`
          : `${cantidadFacturas} facturas de ${proveedorNombre} desmarcadas`
      );
      loadCuentasPorPagar();
    } catch (error) {
      logger.warn('[CxP] Decisión de pago bloqueada:', error);
      toast.error(getApiErrorDetail(error, 'No se pudo actualizar la decisión de pago'));
    }
  };
  
  // Exportar CxP a CSV
  const exportarCxPCSV = () => {
    if (!cxpData?.proveedores?.length) {
      toast.error('No hay datos para exportar');
      return;
    }
    
    let csv = 'Proveedor,RFC,Folio Entrada,Folio Factura,Fecha Entrada,Fecha Vencimiento,Días Vencida,Referencia,Importe Total,Saldo,Decisión Pago,Importe a Pagar\n';
    
    cxpData.proveedores.forEach(prov => {
      prov.facturas.forEach(f => {
        csv += `"${prov.proveedor_nombre}","${prov.proveedor_rfc}","${f.folio_entrada}","${f.folio_factura}",`;
        csv += `"${f.fecha_entrada}","${f.fecha_vencimiento}",${f.dias_vencida},"${f.referencia}",`;
        csv += `${f.importe_total},${f.saldo},${f.decision_pago ? 'Sí' : 'No'},${f.importe_a_pagar}\n`;
      });
    });
    
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `cuentas_por_pagar_${cxpFechaCorte || new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    
    toast.success('Archivo CSV exportado');
  };
  
  // ============= FUNCIONES CONTROL DE INGRESOS =============
  
  const loadIngresos = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      // SUBFASE 2.5: Usar unidad_negocio_id en lugar de server_id
      // FIX: el backend /cortes-caja espera 'unidad_negocio_pk' (GUID). Antes se
      // enviaba 'unidad_negocio_id' → no filtraba y mostraba todas las unidades.
      if (selectedUnidad) params.append('unidad_negocio_pk', selectedUnidad);
      if (ingresosFechaInicio) params.append('fecha_inicio', ingresosFechaInicio);
      if (ingresosFechaFin) params.append('fecha_fin', ingresosFechaFin);
      if (ingresosSoloPendientes) params.append('solo_pendientes', 'true');
      
      const [dataCortes, dataSaldos, dataComisiones, dataConfig] = await Promise.all([
        fetchWithAuth(`/finanzas/ingresos/cortes-caja?${params}`),
        fetchWithAuth(`/finanzas/ingresos/saldos-por-depositar?${params}`),
        fetchWithAuth(`/finanzas/ingresos/resumen-comisiones?${params}`),
        fetchWithAuth('/finanzas/ingresos/config-comisiones')
      ]);
      
      setCortesData(dataCortes);
      setSaldosPendientes(dataSaldos);
      setResumenComisiones(dataComisiones);
      setConfigComisiones(dataConfig);
      
    } catch (error) {
      logger.error('Error ingresos:', error);
      toast.error('Error al cargar ingresos');
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, selectedUnidad, ingresosFechaInicio, ingresosFechaFin, ingresosSoloPendientes]);
  
  // Marcar depósito de efectivo
  const handleDepositoEfectivo = async (corteId, referencia) => {
    try {
      await api.put(`/finanzas/ingresos/cortes-caja/${corteId}/deposito-efectivo`, {
        corte_id: corteId,
        referencia_deposito: referencia,
        monto_depositado: 0
      });
      
      toast.success('Depósito de efectivo registrado');
      loadIngresos();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al registrar depósito');
    }
  };
  
  // Marcar depósito de tarjetas
  const handleDepositoTarjetas = async (corteId, referencia) => {
    try {
      await api.put(`/finanzas/ingresos/cortes-caja/${corteId}/deposito-tarjetas?referencia_netpay=${referencia}`);
      
      toast.success('Depósito de tarjetas registrado');
      loadIngresos();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al registrar depósito');
    }
  };
  
  // Los catalogos auxiliares de CxP se cargan solo cuando CxP esta abierto.
  useEffect(() => {
    if (activeTab === 'cxp') {
      loadCategorias();
      loadCxpSucursales();
    }
  }, [activeTab, loadCategorias, loadCxpSucursales]);
  
  // Load data on tab change or filter change
  useEffect(() => {
    if (activeTab === 'dashboard') {
      loadDashboard();
    } else if (activeTab === 'presupuestos') {
      loadPresupuestos();
    } else if (activeTab === 'cxp') {
      loadCuentasPorPagar();
    } else if (activeTab === 'ingresos') {
      loadIngresos();
    }
  }, [activeTab, loadDashboard, loadPresupuestos, loadCuentasPorPagar, loadIngresos]);
  
  // FASE 1 CxP: Recargar CxP cuando cambie la unidad de negocio seleccionada
  useEffect(() => {
    if (
      activeTab === 'cxp' &&
      selectedUnidad !== undefined
    ) {
      logger.log(`[CxP] Unidad cambiada a: ${selectedUnidad || 'Todas'}, recargando...`);
      loadCuentasPorPagar();
    }
  }, [selectedUnidad]); // Solo depende de selectedUnidad
  
  // CRUD handlers
  const handleNuevoPresupuesto = () => {
    if (!finanzasPermissions.canCreate) {
      toast.error('No tiene permiso para crear presupuestos');
      return;
    }

    setEditingPresupuesto(null);
    setFormPresupuesto({
      unidad_negocio_pk: selectedUnidad || '',
      categoria: '',
      subcategoria: '',
      tipo: 'Egreso',
      monto: 0,
      anio: filtroAnio,
      mes: filtroMes,
      notas: ''
    });
    setModalPresupuesto(true);
  };
  
  const handleEditarPresupuesto = (pres) => {
    if (!finanzasPermissions.canEdit) {
      toast.error('No tiene permiso para editar presupuestos');
      return;
    }

    setEditingPresupuesto(pres);
    setFormPresupuesto({
      unidad_negocio_pk: pres.UnidadNegocioID?.toString() || '',
      categoria: pres.Categoria || '',
      subcategoria: pres.SubCategoria || '',
      tipo: pres.Tipo || 'Egreso',
      monto: pres.Monto_Presupuestado || 0,
      anio: pres.Anio,
      mes: pres.Mes,
      notas: pres.Notas || ''
    });
    setModalPresupuesto(true);
  };
  
  const handleGuardarPresupuesto = async () => {
    const canSave = editingPresupuesto
      ? finanzasPermissions.canEdit
      : finanzasPermissions.canCreate;

    if (!canSave) {
      toast.error('No tiene permiso para guardar presupuestos');
      return;
    }

    if (!formPresupuesto.unidad_negocio_pk || !formPresupuesto.categoria) {
      toast.error('Unidad de negocio y categoría son requeridas');
      return;
    }
    
    setSavingForm(true);
    try {
      const endpoint = editingPresupuesto 
        ? `/finanzas/presupuestos/${editingPresupuesto.PresupuestoID}`
        : '/finanzas/presupuestos';
      
      const body = editingPresupuesto 
        ? {
            monto_presupuestado: formPresupuesto.monto,
            categoria: formPresupuesto.categoria,
            subcategoria: formPresupuesto.subcategoria,
            notas: formPresupuesto.notas
          }
        : formPresupuesto;
      
      if (editingPresupuesto) {
        await api.put(endpoint, body);
      } else {
        await api.post(endpoint, body);
      }
      
      toast.success(editingPresupuesto ? 'Presupuesto actualizado' : 'Presupuesto creado');
      setModalPresupuesto(false);
      loadPresupuestos();
      loadDashboard();
    } catch (error) {
      logger.error('Error:', error);
      toast.error('Error al guardar presupuesto');
    } finally {
      setSavingForm(false);
    }
  };
  
  const handleEliminarPresupuesto = async (pres) => {
    if (!finanzasPermissions.canDelete) {
      toast.error('No tiene permiso para eliminar presupuestos');
      return;
    }

    if (!window.confirm(`¿Eliminar presupuesto de ${pres.Categoria}?`)) return;
    
    try {
      await api.delete(`/finanzas/presupuestos/${pres.PresupuestoID}`);
      
      toast.success('Presupuesto eliminado');
      loadPresupuestos();
      loadDashboard();
    } catch (error) {
      toast.error('Error al eliminar');
    }
  };
  
  const handleVerScript = async () => {
    if (!finanzasPermissions.canViewScript) {
      toast.error(
        'No tiene permiso para consultar el script de inicializacion'
      );
      return;
    }

    try {
      const data = await fetchWithAuth('/finanzas/script-inicializacion');
      setScriptData(data);
      setModalScript(true);
    } catch (error) {
      toast.error('Error al obtener script');
    }
  };
  
  const handleCopyScript = () => {
    if (scriptData?.script) {
      navigator.clipboard.writeText(scriptData.script);
      toast.success('Script copiado al portapapeles');
    }
  };
  
  const tesoreriaPermissions = useMemo(() => {
    const normalize = (value) => String(value || '')
      .toUpperCase()
      .replace(/[^A-Z0-9_]/g, '');

    const flat = effectivePermissions?.permissions_flat;
    const structured = effectivePermissions?.permissions;

    const permissionCodes = (
      Array.isArray(flat)
        ? flat
        : Array.isArray(structured)
          ? structured.map((permission) => (
              typeof permission === 'string'
                ? permission
                : permission?.codigo ||
                  permission?.code ||
                  permission?.permission ||
                  permission?.name
            ))
          : []
    ).filter(Boolean).map(normalize);

    const roleCodes = (
      Array.isArray(effectivePermissions?.roles)
        ? effectivePermissions.roles
        : []
    ).map((role) => (
      typeof role === 'string'
        ? role
        : role?.codigo ||
          role?.code ||
          role?.nombre ||
          role?.name
    )).filter(Boolean).map(normalize);

    const isSuperAdmin = (
      roleCodes.includes('SUPERADMIN') ||
      roleCodes.includes('SUPERADMINISTRADOR')
    );

    const allowed = (code) => (
      !effectivePermissionsLoading &&
      (
        isSuperAdmin ||
        permissionCodes.includes(normalize(code))
      )
    );

    return {
      canView: allowed('TES_CUADRES_Z_VER'),
      canCreate: allowed('TES_CUADRES_Z_CREAR'),
      canEdit: allowed('TES_CUADRES_Z_EDITAR'),
      canDelete: allowed('TES_CUADRES_Z_ELIMINAR'),
      canValidate: allowed('TES_CUADRES_Z_VALIDAR')
    };
  }, [
    effectivePermissions,
    effectivePermissionsLoading
  ]);

  useEffect(() => {
    if (
      !effectivePermissionsLoading &&
      activeTab === 'tesoreria' &&
      !tesoreriaPermissions.canView
    ) {
      setActiveTab('dashboard');
    }
  }, [
    activeTab,
    effectivePermissionsLoading,
    tesoreriaPermissions.canView
  ]);

  useEffect(() => {
    if (
      !effectivePermissionsLoading &&
      activeTab === 'presupuestos' &&
      !finanzasPermissions.canView
    ) {
      setActiveTab('dashboard');
    }
  }, [
    activeTab,
    effectivePermissionsLoading,
    finanzasPermissions.canView
  ]);

  // Tabs
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: PieChart },
    { id: 'ingresos', label: 'Control de Ingresos', icon: TrendingUp },
    ...(finanzasPermissions.canView
      ? [{ id: 'comprobaciones', label: 'Comprobaciones', icon: FileCheck2 }]
      : []),
    { id: 'propinas', label: 'Propinas TPV', icon: DollarSign },
    { id: 'tesoreria', label: 'Tesorería', icon: Banknote },
    { id: 'cuentas-bancarias', label: 'Cuentas Bancarias', icon: Landmark },
    ...(finanzasPermissions.canView
      ? [{ id: 'presupuestos', label: 'Presupuestos', icon: DollarSign }]
      : []),
    { id: 'reportes', label: 'Reportes', icon: FileText },
  ].filter(
    (tab) => (
      tab.id !== 'tesoreria' ||
      tesoreriaPermissions.canView
    )
  );
  
  const paymentTabs = [
    ...(finanzasPermissions.canView
      ? [{
          id: 'decision-pago',
          label: 'Decisión de Pago',
          icon: BarChart3
        }]
      : []),
    {
      id: 'cxp',
      label: 'Cuentas por Pagar',
      icon: CreditCard
    },
  ];

  const isPaymentTabActive = paymentTabs.some(
    (tab) => tab.id === activeTab
  );

  // Format currency
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value || 0);
  };
  
  // Render Dashboard
  // Render Dashboard - Delegado a componente externo
  const renderDashboard = () => {
    return (
      <FinanzasDashboard
        dashboard={dashboard}
        unidadesNegocio={unidadesNegocio}
        selectedUnidad={selectedUnidad}
        loadingUnidades={loadingUnidades}
        filtroMes={filtroMes}
        filtroAnio={filtroAnio}
        meses={meses}
        loading={loading}
        onUnidadChange={setSelectedUnidad}
        onMesChange={setFiltroMes}
        onAnioChange={setFiltroAnio}
        onActualizar={loadDashboard}
        onVerScript={handleVerScript}
        formatCurrency={formatCurrency}
      />
    );
  };
  
  // Render Presupuestos - Delegado a componente externo
  const renderPresupuestos = () => (
    <FinanzasPresupuestos
      presupuestos={presupuestos}
      unidadesNegocio={unidadesNegocio}
      selectedUnidad={selectedUnidad}
      loadingUnidades={loadingUnidades}
      meses={meses}
      filtroAnio={filtroAnio}
      filtroMes={filtroMes}
      canCreate={finanzasPermissions.canCreate}
      canEdit={finanzasPermissions.canEdit}
      canDelete={finanzasPermissions.canDelete}
      canViewScript={finanzasPermissions.canViewScript}
      onUnidadChange={setSelectedUnidad}
      onAnioChange={setFiltroAnio}
      onMesChange={setFiltroMes}
      onVerScript={handleVerScript}
      onNuevoPresupuesto={handleNuevoPresupuesto}
      onEditarPresupuesto={handleEditarPresupuesto}
      onEliminarPresupuesto={handleEliminarPresupuesto}
      formatCurrency={formatCurrency}
    />
  );
  
  // Render Control de Ingresos - Delegado a componente externo
  const renderControlIngresos = () => {
    return (
      <FinanzasControlIngresos
        cortesData={cortesData}
        saldosPendientes={saldosPendientes}
        resumenComisiones={resumenComisiones}
        configComisiones={configComisiones}
        unidadesNegocio={unidadesNegocio}
        selectedUnidad={selectedUnidad}
        loadingUnidades={loadingUnidades}
        ingresosSubTab={ingresosSubTab}
        ingresosFechaInicio={ingresosFechaInicio}
        ingresosFechaFin={ingresosFechaFin}
        ingresosSoloPendientes={ingresosSoloPendientes}
        loading={loading}
        onSubTabChange={setIngresosSubTab}
        onFechaInicioChange={setIngresosFechaInicio}
        onFechaFinChange={setIngresosFechaFin}
        onUnidadChange={setSelectedUnidad}
        onSoloPendientesChange={setIngresosSoloPendientes}
        onFiltrar={loadIngresos}
        onDepositoEfectivo={handleDepositoEfectivo}
        onDepositoTarjetas={handleDepositoTarjetas}
        formatCurrency={formatCurrency}
      />
    );
  };
  
  // Render Cuentas por Pagar - Delegado a componente externo
  const renderCuentasPorPagar = () => {
    // Callbacks para el componente externo
    const handleFiltroProveedorSelect = (proveedorId, proveedorNombre) => {
      setCxpFiltroProveedor(proveedorId);
      setCxpBusquedaProveedor(proveedorNombre);
    };
    
    const handleLimpiarFiltroProveedor = () => {
      setCxpFiltroProveedor('');
      setCxpBusquedaProveedor('');
    };
    
    return (
      <FinanzasCuentasPorPagar
        cxpData={cxpData}
        cxpResumen={cxpResumen}
        cxpProveedores={cxpProveedores}
        cxpSucursales={cxpSucursales}
        unidadesNegocio={unidadesNegocio}
        selectedUnidad={selectedUnidad}
        loadingUnidades={loadingUnidades}
        cxpFiltroSucursal={cxpFiltroSucursal}
        cxpFiltroProveedor={cxpFiltroProveedor}
        cxpBusquedaProveedor={cxpBusquedaProveedor}
        cxpFechaCorte={cxpFechaCorte}
        cxpSoloVencidas={cxpSoloVencidas}
        cxpSoloDecision={cxpSoloDecision}
        cxpExpandidos={cxpExpandidos}
        cxpCategoriasExpandidas={cxpCategoriasExpandidas}
        cxpVistaMode={cxpVistaMode}
        savingDecision={savingDecision}
        loading={loading}
        onUnidadChange={setSelectedUnidad}
        onFechaCorteChange={setCxpFechaCorte}
        onFiltroSucursalChange={setCxpFiltroSucursal}
        onBusquedaProveedorChange={setCxpBusquedaProveedor}
        onFiltroProveedorSelect={handleFiltroProveedorSelect}
        onLimpiarFiltroProveedor={handleLimpiarFiltroProveedor}
        onSoloVencidasChange={setCxpSoloVencidas}
        onSoloDecisionChange={setCxpSoloDecision}
        onFiltrar={loadCuentasPorPagar}
        onExportarCSV={exportarCxPCSV}
        onMarcarTodasVencidas={handleMarcarTodasVencidasPago}
        onDesmarcarTodas={handleDesmarcarTodasPago}
        onExpandirTodos={expandirTodos}
        onColapsarTodos={colapsarTodos}
        onVistaModeChange={setCxpVistaMode}
        onToggleCategoria={toggleCategoria}
        onToggleProveedor={toggleProveedor}
        onDecisionPago={handleDecisionPago}
        onAutorizarDecisionPago={handleAutorizarDecisionPago}
        onTogglePagoProveedor={handleTogglePagoProveedor}
        formatCurrency={formatCurrency}
        reagruparCxPPorProveedores={reagruparCxPPorProveedores}
        // FASE 1 CxP: Ocultar filtro Sucursal - CxP opera exclusivamente por Unidad de Negocio
        hideSucursalFilter={true}
      />
    );
  };

  const renderDecisionPago = () => (
    <FinanzasDecisionPago
      unidadesNegocio={unidadesNegocio}
      selectedUnidad={selectedUnidad}
      loadingUnidades={loadingUnidades}
      onUnidadChange={setSelectedUnidad}
      onAbrirCxp={() => setActiveTab('cxp')}
      canApplyPeriodOverride={finanzasPermissions.canAdmin}
      formatCurrency={formatCurrency}
    />
  );

  const renderComprobaciones = () => (
    <FinanzasComprobaciones
      selectedUnidad={selectedUnidad}
      unidadesNegocio={unidadesNegocio}
      loadingUnidades={loadingUnidades}
      onUnidadChange={setSelectedUnidad}
    />
  );
  
  // Render Reportes
  const renderReportes = () => {
    const kpis = dashboard?.kpis || {};
    const porSucursal = dashboard?.por_sucursal || [];
    
    // Preparar datos para el reporte
    const totalIngresos = porSucursal.reduce((acc, s) => acc + (s.Ingresos || 0), 0);
    const totalEgresos = porSucursal.reduce((acc, s) => acc + (s.Egresos || 0), 0);
    const totalUtilidad = totalIngresos - totalEgresos;
    
    return (
      <div className="space-y-6">
        {/* Encabezado del reporte */}
        <Card className="border-2">
          <CardHeader className="bg-zinc-800 text-white rounded-t-lg">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg">Reporte Financiero</CardTitle>
                <p className="text-zinc-300 text-sm">{meses[filtroMes - 1]} {filtroAnio}</p>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="bg-white/10 border-white/20 text-white hover:bg-white/20" onClick={() => window.print()}>
                  <Printer className="h-4 w-4 mr-1" />
                  Imprimir
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-6">
            {/* Resumen Ejecutivo */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-3 border-b pb-2">Resumen Ejecutivo</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <p className="text-xs text-green-600 uppercase">Total Ingresos</p>
                  <p className="text-xl font-bold text-green-700">{formatCurrency(totalIngresos)}</p>
                </div>
                <div className="text-center p-4 bg-red-50 rounded-lg">
                  <p className="text-xs text-red-600 uppercase">Total Egresos</p>
                  <p className="text-xl font-bold text-red-700">{formatCurrency(totalEgresos)}</p>
                </div>
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <p className="text-xs text-blue-600 uppercase">Utilidad Neta</p>
                  <p className={`text-xl font-bold ${totalUtilidad >= 0 ? 'text-blue-700' : 'text-red-700'}`}>
                    {formatCurrency(totalUtilidad)}
                  </p>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <p className="text-xs text-purple-600 uppercase">Margen</p>
                  <p className="text-xl font-bold text-purple-700">
                    {totalIngresos > 0 ? Math.round((totalUtilidad / totalIngresos) * 100) : 0}%
                  </p>
                </div>
              </div>
            </div>
            
            {/* Gráfico de tendencia */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-3 border-b pb-2">Comparativo por Sucursal</h3>
              {porSucursal.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={porSucursal.map(s => ({
                    name: s.Nombre_Sucursal || 'N/A',
                    Ingresos: s.Ingresos || 0,
                    Egresos: s.Egresos || 0,
                    Utilidad: (s.Ingresos || 0) - (s.Egresos || 0)
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-45} textAnchor="end" height={80} />
                    <YAxis tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
                    <Tooltip formatter={(v) => formatCurrency(v)} />
                    <Legend />
                    <Bar dataKey="Ingresos" fill="#10b981" />
                    <Bar dataKey="Egresos" fill="#ef4444" />
                    <Bar dataKey="Utilidad" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-zinc-400">
                  Sin datos para el periodo
                </div>
              )}
            </div>
            
            {/* Tabla detalle */}
            <div>
              <h3 className="text-lg font-semibold mb-3 border-b pb-2">Detalle por Sucursal</h3>
              <table className="w-full text-sm border">
                <thead className="bg-zinc-100">
                  <tr>
                    <th className="text-left p-2 border">Sucursal</th>
                    <th className="text-right p-2 border">Ingresos Pres.</th>
                    <th className="text-right p-2 border">Ingresos Real</th>
                    <th className="text-right p-2 border">Var %</th>
                    <th className="text-right p-2 border">Egresos Pres.</th>
                    <th className="text-right p-2 border">Egresos Real</th>
                    <th className="text-right p-2 border">Var %</th>
                    <th className="text-right p-2 border">Utilidad</th>
                  </tr>
                </thead>
                <tbody>
                {porSucursal.map((s) => {
                    const varIng = s.Ingresos_Pres > 0 ? Math.round(((s.Ingresos - s.Ingresos_Pres) / s.Ingresos_Pres) * 100) : 0;
                    const varEgr = s.Egresos_Pres > 0 ? Math.round(((s.Egresos - s.Egresos_Pres) / s.Egresos_Pres) * 100) : 0;
                    const utilidad = (s.Ingresos || 0) - (s.Egresos || 0);
                    
                    return (
                      <tr key={`presupuesto-${s.Codigo_Sucursal || s.Nombre_Sucursal}`} className="border-b">
                        <td className="p-2 border font-medium">{s.Nombre_Sucursal}</td>
                        <td className="p-2 border text-right">{formatCurrency(s.Ingresos_Pres)}</td>
                        <td className="p-2 border text-right text-green-600">{formatCurrency(s.Ingresos)}</td>
                        <td className={`p-2 border text-right ${varIng >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {varIng >= 0 ? '+' : ''}{varIng}%
                        </td>
                        <td className="p-2 border text-right">{formatCurrency(s.Egresos_Pres)}</td>
                        <td className="p-2 border text-right text-red-600">{formatCurrency(s.Egresos)}</td>
                        <td className={`p-2 border text-right ${varEgr <= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {varEgr >= 0 ? '+' : ''}{varEgr}%
                        </td>
                        <td className={`p-2 border text-right font-bold ${utilidad >= 0 ? 'text-blue-600' : 'text-red-600'}`}>
                          {formatCurrency(utilidad)}
                        </td>
                      </tr>
                    );
                  })}
                  {/* Totales */}
                  <tr className="bg-zinc-100 font-bold">
                    <td className="p-2 border">TOTALES</td>
                    <td className="p-2 border text-right">{formatCurrency(porSucursal.reduce((a, s) => a + (s.Ingresos_Pres || 0), 0))}</td>
                    <td className="p-2 border text-right text-green-600">{formatCurrency(totalIngresos)}</td>
                    <td className="p-2 border"></td>
                    <td className="p-2 border text-right">{formatCurrency(porSucursal.reduce((a, s) => a + (s.Egresos_Pres || 0), 0))}</td>
                    <td className="p-2 border text-right text-red-600">{formatCurrency(totalEgresos)}</td>
                    <td className="p-2 border"></td>
                    <td className={`p-2 border text-right ${totalUtilidad >= 0 ? 'text-blue-600' : 'text-red-600'}`}>
                      {formatCurrency(totalUtilidad)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            {/* Pie de página */}
            <div className="mt-6 pt-4 border-t text-xs text-zinc-400 text-center">
              Reporte generado el {new Date().toLocaleString('es-MX')} | EDARSA HUB - Control Presupuestal
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };
  
  return (
    <div className="p-6" data-testid="finanzas-page">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-zinc-800">Finanzas y Control Presupuestal</h1>
        <p className="text-zinc-500">Gestión de presupuestos e indicadores financieros - Conectado a EDARSA HUB</p>
      </div>
      
      {/* Navegación financiera */}
      <div className="flex flex-wrap items-start gap-2 mb-6 border-b pb-2">
        {tabs.map(tab => {
          const Icon = tab.icon;

          return (
            <React.Fragment key={tab.id}>
              <button
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-zinc-900 text-white'
                    : 'text-zinc-600 hover:bg-zinc-100'
                }`}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </button>

              {tab.id === 'ingresos' && paymentTabs.length > 0 && (
                <div className="relative">
                  <button
                    type="button"
                    onClick={() =>
                      setPaymentsGroupOpen((current) => !current)
                    }
                    aria-expanded={paymentsGroupOpen}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isPaymentTabActive
                        ? 'bg-zinc-900 text-white'
                        : 'text-zinc-600 hover:bg-zinc-100'
                    }`}
                  >
                    <CreditCard className="h-4 w-4" />
                    Pagos y CxP
                    <ChevronDown
                      className={`h-4 w-4 transition-transform ${
                        paymentsGroupOpen ? 'rotate-180' : ''
                      }`}
                    />
                  </button>

                  {paymentsGroupOpen && (
                    <div
                      className="
                        absolute left-0 top-full z-40 mt-1
                        min-w-56 rounded-lg border border-zinc-200
                        bg-white p-1 shadow-lg
                      "
                    >
                      {paymentTabs.map((paymentTab) => {
                        const PaymentIcon = paymentTab.icon;

                        return (
                          <button
                            key={paymentTab.id}
                            type="button"
                            onClick={() => {
                              setActiveTab(paymentTab.id);
                              setPaymentsGroupOpen(false);
                            }}
                            className={`flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm transition-colors ${
                              activeTab === paymentTab.id
                                ? 'bg-zinc-900 text-white'
                                : 'text-zinc-700 hover:bg-zinc-100'
                            }`}
                          >
                            <PaymentIcon className="h-4 w-4" />
                            {paymentTab.label}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
      
      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-zinc-400" />
        </div>
      )}
      
      {/* Content */}
      {!loading && (
        <>
          {activeTab === 'dashboard' && renderDashboard()}
          {activeTab === 'ingresos' && renderControlIngresos()}
          {activeTab === 'cxp' && renderCuentasPorPagar()}
          {activeTab === 'decision-pago' &&
            finanzasPermissions.canView &&
            renderDecisionPago()}
          {activeTab === 'comprobaciones' && finanzasPermissions.canView && renderComprobaciones()}
          {activeTab === 'propinas' && <PropinasTPV />}
          {activeTab === 'tesoreria' &&
            tesoreriaPermissions.canView && (
              <TesoreriaCorteZ
                permissions={tesoreriaPermissions}
              />
            )}
          {activeTab === 'cuentas-bancarias' && <CuentasBancariasPage />}
          {
              activeTab === 'presupuestos' &&
              finanzasPermissions.canView &&
              renderPresupuestos()
            }
          {activeTab === 'reportes' && renderReportes()}
        </>
      )}
      
      {/* Modal Presupuesto */}
      {modalPresupuesto && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
            <div className="bg-zinc-800 text-white px-6 py-4 flex items-center justify-between rounded-t-xl">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <DollarSign className="h-5 w-5" />
                {editingPresupuesto ? 'Editar Presupuesto' : 'Nuevo Presupuesto'}
              </h2>
              <button onClick={() => setModalPresupuesto(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div>
                <Label className="text-sm font-medium">Unidad de Negocio *</Label>
                <select
                  value={formPresupuesto.unidad_negocio_pk}
                  onChange={(e) => setFormPresupuesto({...formPresupuesto, unidad_negocio_pk: e.target.value})}
                  className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
                  disabled={editingPresupuesto}
                >
                  <option value="">Seleccionar...</option>
                  {unidadesNegocio.map(u => (
                    <option key={u.id} value={u.id}>{u.nombre}</option>
                  ))}
                </select>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium">Tipo *</Label>
                  <select
                    value={formPresupuesto.tipo}
                    onChange={(e) => setFormPresupuesto({...formPresupuesto, tipo: e.target.value})}
                    className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
                    disabled={editingPresupuesto}
                  >
                    <option value="Ingreso">Ingreso</option>
                    <option value="Egreso">Egreso</option>
                  </select>
                </div>
                <div>
                  <Label className="text-sm font-medium">Categoría *</Label>
                  <select
                    value={formPresupuesto.categoria}
                    onChange={(e) => setFormPresupuesto({...formPresupuesto, categoria: e.target.value})}
                    className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
                  >
                    <option value="">Seleccionar...</option>
                    {categorias
                      .filter(c => c.Tipo === formPresupuesto.tipo)
                      .map((c) => (
                        <option key={`cat-${c.Categoria}`} value={c.Categoria}>{c.Categoria}</option>
                      ))}
                  </select>
                </div>
              </div>
              
              <div>
                <Label className="text-sm font-medium">Subcategoría</Label>
                <Input
                  value={formPresupuesto.subcategoria}
                  onChange={(e) => setFormPresupuesto({...formPresupuesto, subcategoria: e.target.value})}
                  placeholder="Opcional"
                  className="mt-1"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium">Mes</Label>
                  <select
                    value={formPresupuesto.mes}
                    onChange={(e) => setFormPresupuesto({...formPresupuesto, mes: parseInt(e.target.value)})}
                    className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
                    disabled={editingPresupuesto}
                  >
                    {meses.map((m, i) => (
                      <option key={`form-mes-${i + 1}`} value={i + 1}>{m}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label className="text-sm font-medium">Año</Label>
                  <select
                    value={formPresupuesto.anio}
                    onChange={(e) => setFormPresupuesto({...formPresupuesto, anio: parseInt(e.target.value)})}
                    className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
                    disabled={editingPresupuesto}
                  >
                    {[2024, 2025, 2026, 2027].map(a => (
                      <option key={a} value={a}>{a}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div>
                <Label className="text-sm font-medium">Monto Presupuestado</Label>
                <Input
                  type="number"
                  value={formPresupuesto.monto}
                  onChange={(e) => setFormPresupuesto({...formPresupuesto, monto: parseFloat(e.target.value) || 0})}
                  className="mt-1 font-mono"
                  min="0"
                  step="100"
                />
              </div>
              
              <div>
                <Label className="text-sm font-medium">Notas</Label>
                <textarea
                  value={formPresupuesto.notas}
                  onChange={(e) => setFormPresupuesto({...formPresupuesto, notas: e.target.value})}
                  className="mt-1 w-full px-3 py-2 border rounded-lg text-sm resize-none"
                  rows={2}
                  placeholder="Notas opcionales..."
                />
              </div>
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end gap-3 bg-zinc-50 rounded-b-xl">
              <Button variant="outline" onClick={() => setModalPresupuesto(false)}>
                Cancelar
              </Button>
              <Button onClick={handleGuardarPresupuesto} disabled={savingForm} className="bg-zinc-900 text-white">
                {savingForm ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
                {editingPresupuesto ? 'Actualizar' : 'Guardar'}
              </Button>
            </div>
          </div>
        </div>
      )}
      
      {/* Modal Script SQL */}
      {modalScript && scriptData && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
            <div className="bg-zinc-800 text-white px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Script de Inicialización - Finanzas
              </h2>
              <button onClick={() => setModalScript(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4 overflow-y-auto flex-1">
              {/* Instrucciones */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="font-medium text-blue-800 mb-2">Instrucciones:</p>
                <ol className="list-decimal list-inside text-sm text-blue-700 space-y-1">
                  {scriptData.instrucciones?.map((inst, i) => (
                    <li key={`inst-${i}-${inst.slice(0, 20)}`}>{inst}</li>
                  ))}
                </ol>
              </div>
              
              {/* Script */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label className="font-medium">Script SQL:</Label>
                  <Button variant="outline" size="sm" onClick={handleCopyScript}>
                    <Copy className="h-4 w-4 mr-1" />
                    Copiar
                  </Button>
                </div>
                <pre className="bg-zinc-900 text-green-400 p-4 rounded-lg text-xs overflow-x-auto max-h-[400px] overflow-y-auto font-mono">
                  {scriptData.script}
                </pre>
              </div>
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end bg-zinc-50">
              <Button variant="outline" onClick={() => setModalScript(false)}>
                Cerrar
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
