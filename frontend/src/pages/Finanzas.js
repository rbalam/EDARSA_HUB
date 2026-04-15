import React, { useState, useEffect, useCallback } from 'react';
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
  FileSpreadsheet, File, ChevronRight, Upload, Banknote
} from 'lucide-react';
import { toast } from 'sonner';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart as RechartsPie, Pie, Cell, LineChart, Line
} from 'recharts';
import TesoreriaCorteZ from '../components/TesoreriaCorteZ';
import PropinasTPV from '../components/PropinasTPV';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

// Colores para gráficos
const COLORS = ['#10b981', '#ef4444', '#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899'];

export default function Finanzas() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  const [dashboard, setDashboard] = useState(null);
  const [presupuestos, setPresupuestos] = useState([]);
  const [sucursales, setSucursales] = useState([]);
  const [categorias, setCategorias] = useState([]);
  
  // Filtros
  const [filtroAnio, setFiltroAnio] = useState(new Date().getFullYear());
  const [filtroMes, setFiltroMes] = useState(new Date().getMonth() + 1);
  const [filtroSucursal, setFiltroSucursal] = useState('');
  
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
            cantidad_facturas: 0,
            cantidad_vencidas: 0
          };
        }
        
        const prov = categorias[tipoCategoria].proveedores[provNombre];
        prov.facturas.push(factura);
        prov.subtotal_saldo += factura.saldo || 0;
        prov.subtotal_importe += factura.importe_original || factura.importe_total || 0;
        prov.cantidad_facturas += 1;
        if (factura.dias_vencida > 0) prov.cantidad_vencidas += 1;
        
        // Acumular en categoría
        categorias[tipoCategoria].subtotal_saldo += factura.saldo || 0;
        categorias[tipoCategoria].subtotal_importe += factura.importe_original || factura.importe_total || 0;
        categorias[tipoCategoria].cantidad_facturas += 1;
        if (factura.dias_vencida > 0) categorias[tipoCategoria].cantidad_vencidas += 1;
      });
    });
    
    // Convertir a array y ordenar proveedores por saldo desc
    const resultado = Object.values(categorias).map(cat => ({
      ...cat,
      proveedores: Object.values(cat.proveedores).sort((a, b) => b.subtotal_saldo - a.subtotal_saldo)
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
    
    // Ordenar por saldo descendente
    return Object.values(proveedores).sort((a, b) => b.subtotal_saldo - a.subtotal_saldo);
  }, []);
  
  // Estados para Control de Ingresos
  const [ingresosSubTab, setIngresosSubTab] = useState('cortes');
  const [cortesData, setCortesData] = useState(null);
  const [saldosPendientes, setSaldosPendientes] = useState(null);
  const [resumenComisiones, setResumenComisiones] = useState(null);
  const [configComisiones, setConfigComisiones] = useState(null);
  const [ingresosFiltroSucursal, setIngresosFiltroSucursal] = useState('');
  const [ingresosFechaInicio, setIngresosFechaInicio] = useState('');
  const [ingresosFechaFin, setIngresosFechaFin] = useState('');
  const [ingresosSoloPendientes, setIngresosSoloPendientes] = useState(false);
  
  // Form
  const [formPresupuesto, setFormPresupuesto] = useState({
    sucursal_id: '',
    categoria: '',
    subcategoria: '',
    tipo: 'Egreso',
    monto: 0,
    anio: new Date().getFullYear(),
    mes: new Date().getMonth() + 1,
    notas: ''
  });
  
  const token = localStorage.getItem('token');
  
  const meses = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
  ];
  
  // Fetch helpers
  const fetchWithAuth = useCallback(async (endpoint) => {
    const response = await fetch(`${API_URL}${endpoint}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error('Error en la petición');
    return response.json();
  }, [token]);
  
  // Load dashboard
  const loadDashboard = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        anio: filtroAnio,
        mes: filtroMes,
        ...(filtroSucursal && { sucursal_id: filtroSucursal })
      });
      const data = await fetchWithAuth(`/api/finanzas/dashboard?${params}`);
      setDashboard(data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, filtroAnio, filtroMes, filtroSucursal]);
  
  // Load presupuestos
  const loadPresupuestos = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        anio: filtroAnio,
        ...(filtroMes && { mes: filtroMes }),
        ...(filtroSucursal && { sucursal_id: filtroSucursal })
      });
      const data = await fetchWithAuth(`/api/finanzas/presupuestos?${params}`);
      setPresupuestos(data.presupuestos || []);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, filtroAnio, filtroMes, filtroSucursal]);
  
  // Load sucursales (RH - para dashboard e ingresos)
  const loadSucursales = useCallback(async () => {
    try {
      const data = await fetchWithAuth('/api/rrhh/catalogos/sucursales');
      setSucursales(data.sucursales || []);
    } catch (error) {
      console.error('Error:', error);
    }
  }, [fetchWithAuth]);
  
  // Load sucursales CxP (MPRO - para cuentas por pagar)
  const loadCxpSucursales = useCallback(async () => {
    try {
      const data = await fetchWithAuth('/api/finanzas/cuentas-por-pagar/sucursales');
      setCxpSucursales(data.sucursales || []);
    } catch (error) {
      console.error('Error loading CxP sucursales:', error);
    }
  }, [fetchWithAuth]);
  
  // Load categorias
  const loadCategorias = useCallback(async () => {
    try {
      const data = await fetchWithAuth('/api/finanzas/categorias');
      setCategorias(data.categorias || []);
    } catch (error) {
      console.error('Error:', error);
    }
  }, [fetchWithAuth]);
  
  // Load Cuentas por Pagar
  const loadCuentasPorPagar = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (cxpFiltroSucursal) params.append('sucursal_id', cxpFiltroSucursal);
      if (cxpFiltroProveedor) params.append('proveedor_id', cxpFiltroProveedor);
      if (cxpFechaCorte) params.append('fecha_corte', cxpFechaCorte);
      if (cxpSoloVencidas) params.append('solo_vencidas', 'true');
      if (cxpSoloDecision) params.append('solo_decision_pago', 'true');
      
      const [dataFacturas, dataResumen, dataProveedores] = await Promise.all([
        fetchWithAuth(`/api/finanzas/cuentas-por-pagar?${params}`),
        fetchWithAuth(`/api/finanzas/cuentas-por-pagar/resumen${cxpFiltroSucursal ? `?sucursal_id=${cxpFiltroSucursal}` : ''}`),
        fetchWithAuth(`/api/finanzas/cuentas-por-pagar/proveedores${cxpFiltroSucursal ? `?sucursal_id=${cxpFiltroSucursal}` : ''}`)
      ]);
      
      setCxpData(dataFacturas);
      setCxpResumen(dataResumen);
      setCxpProveedores(dataProveedores.proveedores || []);
      
      // Expandir todos los proveedores por defecto
      const expandidos = {};
      (dataFacturas.proveedores || []).forEach(p => {
        expandidos[p.proveedor_id] = true;
      });
      setCxpExpandidos(expandidos);
      
    } catch (error) {
      console.error('Error CxP:', error);
      toast.error('Error al cargar cuentas por pagar');
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, cxpFiltroSucursal, cxpFiltroProveedor, cxpFechaCorte, cxpSoloVencidas, cxpSoloDecision]);
  
  // Actualizar decisión de pago
  const handleDecisionPago = async (facturaId, decision, importeAPagar = null) => {
    setSavingDecision(facturaId);
    try {
      const response = await fetch(`${API_URL}/api/finanzas/cuentas-por-pagar/${facturaId}/decision-pago`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          decision_pago: decision,
          importe_a_pagar: importeAPagar
        })
      });
      
      if (!response.ok) throw new Error('Error');
      
      toast.success(decision ? 'Marcada para pago' : 'Desmarcada');
      loadCuentasPorPagar();
    } catch (error) {
      toast.error('Error al actualizar');
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
      const response = await fetch(`${API_URL}/api/finanzas/cuentas-por-pagar/decision-pago-masivo`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          facturas_ids: facturasVencidas,
          decision_pago: true
        })
      });
      
      if (!response.ok) throw new Error('Error');
      
      const data = await response.json();
      toast.success(`${data.actualizadas} facturas vencidas marcadas para pago`);
      loadCuentasPorPagar();
    } catch (error) {
      toast.error('Error al marcar facturas');
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
      const response = await fetch(`${API_URL}/api/finanzas/cuentas-por-pagar/decision-pago-masivo`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          facturas_ids: facturasMarcadas,
          decision_pago: false
        })
      });
      
      if (!response.ok) throw new Error('Error');
      
      const data = await response.json();
      toast.success(`${data.actualizadas} facturas desmarcadas`);
      loadCuentasPorPagar();
    } catch (error) {
      toast.error('Error al desmarcar facturas');
    } finally {
      setLoading(false);
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
      if (ingresosFiltroSucursal) params.append('sucursal_id', ingresosFiltroSucursal);
      if (ingresosFechaInicio) params.append('fecha_inicio', ingresosFechaInicio);
      if (ingresosFechaFin) params.append('fecha_fin', ingresosFechaFin);
      if (ingresosSoloPendientes) params.append('solo_pendientes', 'true');
      
      const [dataCortes, dataSaldos, dataComisiones, dataConfig] = await Promise.all([
        fetchWithAuth(`/api/finanzas/ingresos/cortes-caja?${params}`),
        fetchWithAuth(`/api/finanzas/ingresos/saldos-por-depositar${ingresosFiltroSucursal ? `?sucursal_id=${ingresosFiltroSucursal}` : ''}`),
        fetchWithAuth(`/api/finanzas/ingresos/resumen-comisiones?${params}`),
        fetchWithAuth('/api/finanzas/ingresos/config-comisiones')
      ]);
      
      setCortesData(dataCortes);
      setSaldosPendientes(dataSaldos);
      setResumenComisiones(dataComisiones);
      setConfigComisiones(dataConfig);
      
    } catch (error) {
      console.error('Error ingresos:', error);
      toast.error('Error al cargar ingresos');
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, ingresosFiltroSucursal, ingresosFechaInicio, ingresosFechaFin, ingresosSoloPendientes]);
  
  // Marcar depósito de efectivo
  const handleDepositoEfectivo = async (corteId, referencia) => {
    try {
      const response = await fetch(`${API_URL}/api/finanzas/ingresos/cortes-caja/${corteId}/deposito-efectivo`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          corte_id: corteId,
          referencia_deposito: referencia,
          monto_depositado: 0
        })
      });
      
      if (!response.ok) throw new Error('Error');
      toast.success('Depósito de efectivo registrado');
      loadIngresos();
    } catch (error) {
      toast.error('Error al registrar depósito');
    }
  };
  
  // Marcar depósito de tarjetas
  const handleDepositoTarjetas = async (corteId, referencia) => {
    try {
      const response = await fetch(`${API_URL}/api/finanzas/ingresos/cortes-caja/${corteId}/deposito-tarjetas?referencia_netpay=${referencia}`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) throw new Error('Error');
      toast.success('Depósito de tarjetas registrado');
      loadIngresos();
    } catch (error) {
      toast.error('Error al registrar depósito');
    }
  };
  
  // Initial load
  useEffect(() => {
    loadSucursales();
    loadCategorias();
    loadCxpSucursales();  // Cargar sucursales de MPRO para CxP
  }, [loadSucursales, loadCategorias, loadCxpSucursales]);
  
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
  
  // CRUD handlers
  const handleNuevoPresupuesto = () => {
    setEditingPresupuesto(null);
    setFormPresupuesto({
      sucursal_id: '',
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
    setEditingPresupuesto(pres);
    setFormPresupuesto({
      sucursal_id: pres.SucursalID?.toString() || '',
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
    if (!formPresupuesto.sucursal_id || !formPresupuesto.categoria) {
      toast.error('Sucursal y categoría son requeridos');
      return;
    }
    
    setSavingForm(true);
    try {
      const url = editingPresupuesto 
        ? `${API_URL}/api/finanzas/presupuestos/${editingPresupuesto.PresupuestoID}`
        : `${API_URL}/api/finanzas/presupuestos`;
      
      const method = editingPresupuesto ? 'PUT' : 'POST';
      const body = editingPresupuesto 
        ? {
            monto_presupuestado: formPresupuesto.monto,
            categoria: formPresupuesto.categoria,
            subcategoria: formPresupuesto.subcategoria,
            notas: formPresupuesto.notas
          }
        : formPresupuesto;
      
      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
      });
      
      if (!response.ok) throw new Error('Error al guardar');
      
      toast.success(editingPresupuesto ? 'Presupuesto actualizado' : 'Presupuesto creado');
      setModalPresupuesto(false);
      loadPresupuestos();
      loadDashboard();
    } catch (error) {
      console.error('Error:', error);
      toast.error('Error al guardar presupuesto');
    } finally {
      setSavingForm(false);
    }
  };
  
  const handleEliminarPresupuesto = async (pres) => {
    if (!window.confirm(`¿Eliminar presupuesto de ${pres.Categoria}?`)) return;
    
    try {
      const response = await fetch(`${API_URL}/api/finanzas/presupuestos/${pres.PresupuestoID}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) throw new Error('Error');
      
      toast.success('Presupuesto eliminado');
      loadPresupuestos();
      loadDashboard();
    } catch (error) {
      toast.error('Error al eliminar');
    }
  };
  
  const handleVerScript = async () => {
    try {
      const data = await fetchWithAuth('/api/finanzas/script-inicializacion');
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
  
  // Tabs
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: PieChart },
    { id: 'ingresos', label: 'Control de Ingresos', icon: TrendingUp },
    { id: 'cxp', label: 'Cuentas por Pagar', icon: CreditCard },
    { id: 'propinas', label: 'Propinas TPV', icon: DollarSign },
    { id: 'tesoreria', label: 'Tesorería', icon: Banknote },
    { id: 'presupuestos', label: 'Presupuestos', icon: DollarSign },
    { id: 'reportes', label: 'Reportes', icon: FileText },
  ];
  
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
  const renderDashboard = () => {
    const kpis = dashboard?.kpis || {};
    const porSucursal = dashboard?.por_sucursal || [];
    
    // Check if tables don't exist
    if (dashboard?.nota) {
      return (
        <div className="space-y-6">
          <Card className="border-2 border-dashed border-amber-300 bg-amber-50">
            <CardContent className="py-8 text-center">
              <AlertCircle className="h-16 w-16 text-amber-500 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-amber-700 mb-2">Tablas no configuradas</h2>
              <p className="text-amber-600 mb-4">
                Las tablas de finanzas aún no han sido creadas en la base de datos EDARSA HUB.
              </p>
              <Button onClick={handleVerScript} className="bg-amber-600 hover:bg-amber-700 text-white">
                <FileText className="h-4 w-4 mr-2" />
                Ver Script de Inicialización
              </Button>
            </CardContent>
          </Card>
        </div>
      );
    }
    
    return (
      <div className="space-y-6">
        {/* Filtros */}
        <div className="flex flex-wrap gap-3 items-center">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-zinc-400" />
            <select
              value={filtroMes}
              onChange={(e) => setFiltroMes(parseInt(e.target.value))}
              className="px-3 py-2 border rounded-lg text-sm"
            >
              {meses.map((m, i) => (
                <option key={i} value={i + 1}>{m}</option>
              ))}
            </select>
            <select
              value={filtroAnio}
              onChange={(e) => setFiltroAnio(parseInt(e.target.value))}
              className="px-3 py-2 border rounded-lg text-sm"
            >
              {[2024, 2025, 2026, 2027].map(a => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
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
          <Button variant="outline" size="sm" onClick={loadDashboard} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
            Actualizar
          </Button>
        </div>
        
        {/* KPIs */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Ingresos */}
          <Card className="border-l-4 border-l-green-500">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-zinc-500 uppercase tracking-wide">Ingresos</p>
                  <p className="text-2xl font-bold text-green-600">{formatCurrency(kpis.ingresos_ejecutados)}</p>
                  <p className="text-xs text-zinc-400">de {formatCurrency(kpis.ingresos_presupuestados)}</p>
                </div>
                <div className={`flex items-center gap-1 text-sm ${kpis.ingresos_var_mes_ant >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {kpis.ingresos_var_mes_ant >= 0 ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  {Math.abs(kpis.ingresos_var_mes_ant || 0)}%
                </div>
              </div>
            </CardContent>
          </Card>
          
          {/* Egresos */}
          <Card className="border-l-4 border-l-red-500">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-zinc-500 uppercase tracking-wide">Egresos</p>
                  <p className="text-2xl font-bold text-red-600">{formatCurrency(kpis.egresos_ejecutados)}</p>
                  <p className="text-xs text-zinc-400">de {formatCurrency(kpis.egresos_presupuestados)}</p>
                </div>
                <div className={`flex items-center gap-1 text-sm ${kpis.egresos_var_mes_ant <= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {kpis.egresos_var_mes_ant >= 0 ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  {Math.abs(kpis.egresos_var_mes_ant || 0)}%
                </div>
              </div>
            </CardContent>
          </Card>
          
          {/* Utilidad */}
          <Card className="border-l-4 border-l-blue-500">
            <CardContent className="pt-4">
              <div>
                <p className="text-xs text-zinc-500 uppercase tracking-wide">Utilidad</p>
                <p className={`text-2xl font-bold ${kpis.utilidad_real >= 0 ? 'text-blue-600' : 'text-red-600'}`}>
                  {formatCurrency(kpis.utilidad_real)}
                </p>
                <p className="text-xs text-zinc-400">Presupuestada: {formatCurrency(kpis.utilidad_presupuestada)}</p>
              </div>
            </CardContent>
          </Card>
          
          {/* Margen */}
          <Card className="border-l-4 border-l-purple-500">
            <CardContent className="pt-4">
              <div>
                <p className="text-xs text-zinc-500 uppercase tracking-wide">Margen de Utilidad</p>
                <p className={`text-2xl font-bold ${kpis.margen_utilidad >= 0 ? 'text-purple-600' : 'text-red-600'}`}>
                  {kpis.margen_utilidad || 0}%
                </p>
                <p className="text-xs text-zinc-400">{meses[filtroMes - 1]} {filtroAnio}</p>
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Gráficos */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Gráfico de Barras - Comparativo Presupuesto vs Real */}
          <Card>
            <CardHeader className="py-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                Presupuesto vs Ejecutado por Sucursal
              </CardTitle>
            </CardHeader>
            <CardContent>
              {porSucursal.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={porSucursal.map(s => ({
                    name: s.Nombre_Sucursal?.substring(0, 10) || 'N/A',
                    Presupuesto: (s.Ingresos_Pres || 0) - (s.Egresos_Pres || 0),
                    Ejecutado: (s.Ingresos || 0) - (s.Egresos || 0)
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                    <YAxis tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
                    <Tooltip formatter={(v) => formatCurrency(v)} />
                    <Legend />
                    <Bar dataKey="Presupuesto" fill="#94a3b8" name="Presupuesto" />
                    <Bar dataKey="Ejecutado" fill="#3b82f6" name="Ejecutado" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[250px] flex items-center justify-center text-zinc-400">
                  Sin datos para graficar
                </div>
              )}
            </CardContent>
          </Card>
          
          {/* Gráfico de Pie - Distribución de Egresos */}
          <Card>
            <CardHeader className="py-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <PieChart className="h-4 w-4" />
                Distribución de Egresos por Sucursal
              </CardTitle>
            </CardHeader>
            <CardContent>
              {porSucursal.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <RechartsPie>
                    <Pie
                      data={porSucursal.map(s => ({
                        name: s.Nombre_Sucursal || 'N/A',
                        value: s.Egresos || 0
                      })).filter(d => d.value > 0)}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name.substring(0, 8)} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {porSucursal.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(v) => formatCurrency(v)} />
                  </RechartsPie>
                </ResponsiveContainer>
              ) : (
                <div className="h-[250px] flex items-center justify-center text-zinc-400">
                  Sin datos para graficar
                </div>
              )}
            </CardContent>
          </Card>
        </div>
        
        {/* Alertas de Sobregiro */}
        {porSucursal.some(s => (s.Egresos || 0) > (s.Egresos_Pres || 0)) && (
          <Card className="border-red-200 bg-red-50">
            <CardHeader className="py-2">
              <CardTitle className="text-sm text-red-700 flex items-center gap-2">
                <AlertCircle className="h-4 w-4" />
                Alertas de Sobregiro
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-1">
                {porSucursal
                  .filter(s => (s.Egresos || 0) > (s.Egresos_Pres || 0))
                  .map((s, i) => {
                    const exceso = (s.Egresos || 0) - (s.Egresos_Pres || 0);
                    const porcExceso = s.Egresos_Pres > 0 ? Math.round((exceso / s.Egresos_Pres) * 100) : 0;
                    return (
                      <div key={i} className="flex items-center justify-between text-sm">
                        <span className="text-red-700">{s.Nombre_Sucursal}</span>
                        <span className="font-medium text-red-600">
                          Exceso: {formatCurrency(exceso)} (+{porcExceso}%)
                        </span>
                      </div>
                    );
                  })}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Por Sucursal */}
        <Card>
          <CardHeader className="py-3 bg-zinc-800 text-white rounded-t-lg">
            <CardTitle className="text-base flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Comparativo por Sucursal
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-zinc-100">
                  <tr>
                    <th className="text-left p-3 font-medium">Sucursal</th>
                    <th className="text-right p-3 font-medium">Ingresos Pres.</th>
                    <th className="text-right p-3 font-medium">Ingresos Real</th>
                    <th className="text-right p-3 font-medium">Egresos Pres.</th>
                    <th className="text-right p-3 font-medium">Egresos Real</th>
                    <th className="text-right p-3 font-medium">Utilidad</th>
                    <th className="text-center p-3 font-medium">Cumplimiento</th>
                  </tr>
                </thead>
                <tbody>
                  {porSucursal.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center py-8 text-zinc-400">
                        No hay datos para el periodo seleccionado
                      </td>
                    </tr>
                  ) : (
                    porSucursal.map((suc, i) => {
                      const utilidad = (suc.Ingresos || 0) - (suc.Egresos || 0);
                      const cumplimiento = suc.Ingresos_Pres > 0 
                        ? Math.round((suc.Ingresos / suc.Ingresos_Pres) * 100) 
                        : 0;
                      
                      return (
                        <tr key={suc.SucursalID || i} className="border-b hover:bg-zinc-50">
                          <td className="p-3 font-medium">{suc.Nombre_Sucursal}</td>
                          <td className="p-3 text-right text-zinc-500">{formatCurrency(suc.Ingresos_Pres)}</td>
                          <td className="p-3 text-right text-green-600 font-medium">{formatCurrency(suc.Ingresos)}</td>
                          <td className="p-3 text-right text-zinc-500">{formatCurrency(suc.Egresos_Pres)}</td>
                          <td className="p-3 text-right text-red-600 font-medium">{formatCurrency(suc.Egresos)}</td>
                          <td className={`p-3 text-right font-bold ${utilidad >= 0 ? 'text-blue-600' : 'text-red-600'}`}>
                            {formatCurrency(utilidad)}
                          </td>
                          <td className="p-3 text-center">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              cumplimiento >= 100 ? 'bg-green-100 text-green-700' :
                              cumplimiento >= 80 ? 'bg-amber-100 text-amber-700' :
                              'bg-red-100 text-red-700'
                            }`}>
                              {cumplimiento}%
                            </span>
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
  
  // Render Presupuestos
  const renderPresupuestos = () => (
    <div className="space-y-4">
      {/* Filtros y acciones */}
      <div className="flex flex-wrap gap-3 justify-between">
        <div className="flex flex-wrap gap-2 items-center">
          <select
            value={filtroAnio}
            onChange={(e) => setFiltroAnio(parseInt(e.target.value))}
            className="px-3 py-2 border rounded-lg text-sm"
          >
            {[2024, 2025, 2026, 2027].map(a => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
          <select
            value={filtroMes}
            onChange={(e) => setFiltroMes(parseInt(e.target.value))}
            className="px-3 py-2 border rounded-lg text-sm"
          >
            <option value="">Todos los meses</option>
            {meses.map((m, i) => (
              <option key={i} value={i + 1}>{m}</option>
            ))}
          </select>
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
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleVerScript}>
            <FileText className="h-4 w-4 mr-1" />
            Ver Script SQL
          </Button>
          <Button size="sm" className="bg-zinc-900 text-white" onClick={handleNuevoPresupuesto}>
            <Plus className="h-4 w-4 mr-1" />
            Nuevo Presupuesto
          </Button>
        </div>
      </div>
      
      {/* Tabla */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-zinc-800 text-white">
                <tr>
                  <th className="text-left p-3 font-medium">Sucursal</th>
                  <th className="text-left p-3 font-medium">Categoría</th>
                  <th className="text-center p-3 font-medium">Tipo</th>
                  <th className="text-center p-3 font-medium">Periodo</th>
                  <th className="text-right p-3 font-medium">Presupuestado</th>
                  <th className="text-right p-3 font-medium">Ejecutado</th>
                  <th className="text-center p-3 font-medium">%</th>
                  <th className="text-center p-3 font-medium">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {presupuestos.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="text-center py-8 text-zinc-400">
                      No hay presupuestos registrados para este periodo
                    </td>
                  </tr>
                ) : (
                  presupuestos.map((pres, i) => {
                    const porcentaje = pres.Monto_Presupuestado > 0 
                      ? Math.round((pres.Monto_Ejecutado / pres.Monto_Presupuestado) * 100) 
                      : 0;
                    
                    return (
                      <tr key={pres.PresupuestoID || i} className="border-b hover:bg-zinc-50">
                        <td className="p-3 font-medium">{pres.Nombre_Sucursal}</td>
                        <td className="p-3">
                          <div>
                            <span>{pres.Categoria}</span>
                            {pres.SubCategoria && (
                              <span className="text-xs text-zinc-400 block">{pres.SubCategoria}</span>
                            )}
                          </div>
                        </td>
                        <td className="p-3 text-center">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            pres.Tipo === 'Ingreso' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                          }`}>
                            {pres.Tipo}
                          </span>
                        </td>
                        <td className="p-3 text-center text-zinc-500">
                          {meses[pres.Mes - 1]?.substring(0, 3)} {pres.Anio}
                        </td>
                        <td className="p-3 text-right font-mono">{formatCurrency(pres.Monto_Presupuestado)}</td>
                        <td className="p-3 text-right font-mono font-medium">{formatCurrency(pres.Monto_Ejecutado)}</td>
                        <td className="p-3 text-center">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            porcentaje >= 100 ? 'bg-green-100 text-green-700' :
                            porcentaje >= 80 ? 'bg-amber-100 text-amber-700' :
                            'bg-zinc-100 text-zinc-600'
                          }`}>
                            {porcentaje}%
                          </span>
                        </td>
                        <td className="p-3">
                          <div className="flex items-center justify-center gap-1">
                            <Button variant="ghost" size="sm" onClick={() => handleEditarPresupuesto(pres)} title="Editar">
                              <Edit className="h-4 w-4 text-amber-600" />
                            </Button>
                            <Button variant="ghost" size="sm" onClick={() => handleEliminarPresupuesto(pres)} title="Eliminar">
                              <Trash2 className="h-4 w-4 text-red-600" />
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
    </div>
  );
  
  // Render Control de Ingresos
  const renderControlIngresos = () => {
    const resumen = cortesData?.resumen || {};
    const saldos = saldosPendientes || {};
    const comisiones = configComisiones?.comisiones || {};
    
    return (
      <div className="space-y-4">
        {/* Sub-tabs */}
        <div className="flex gap-2 border-b pb-2">
          {['cortes', 'pendientes', 'comisiones', 'conciliacion'].map(tab => (
            <button
              key={tab}
              onClick={() => setIngresosSubTab(tab)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                ingresosSubTab === tab ? 'bg-zinc-900 text-white' : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200'
              }`}
            >
              {tab === 'cortes' ? 'Cortes de Caja' :
               tab === 'pendientes' ? 'Por Depositar' :
               tab === 'comisiones' ? 'Comisiones' : 'Conciliación'}
            </button>
          ))}
        </div>
        
        {/* Filtros generales */}
        <Card>
          <CardContent className="p-3">
            <div className="grid grid-cols-1 md:grid-cols-6 gap-3 items-end">
              <div>
                <Label className="text-xs text-zinc-500">Fecha Inicio</Label>
                <Input type="date" value={ingresosFechaInicio} onChange={(e) => setIngresosFechaInicio(e.target.value)} className="mt-1" />
              </div>
              <div>
                <Label className="text-xs text-zinc-500">Fecha Fin</Label>
                <Input type="date" value={ingresosFechaFin} onChange={(e) => setIngresosFechaFin(e.target.value)} className="mt-1" />
              </div>
              <div>
                <Label className="text-xs text-zinc-500">Sucursal</Label>
                <select value={ingresosFiltroSucursal} onChange={(e) => setIngresosFiltroSucursal(e.target.value)} className="w-full px-3 py-2 border rounded-lg text-sm mt-1">
                  <option value="">Todas</option>
                  {sucursales.map(s => <option key={s.SucursalID} value={s.SucursalID}>{s.Nombre_Sucursal}</option>)}
                </select>
              </div>
              <div className="flex items-center">
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={ingresosSoloPendientes} onChange={(e) => setIngresosSoloPendientes(e.target.checked)} className="rounded" />
                  Solo pendientes
                </label>
              </div>
              <div>
                <Button onClick={loadIngresos} disabled={loading} className="w-full">
                  <RefreshCw className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} /> Filtrar
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* === TAB: CORTES DE CAJA === */}
        {ingresosSubTab === 'cortes' && (
          <div className="space-y-4">
            {/* Resumen */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <Card className="border-l-4 border-l-green-500">
                <CardContent className="p-3">
                  <p className="text-xs text-zinc-500">Total Efectivo</p>
                  <p className="text-xl font-bold text-green-600">{formatCurrency(resumen.total_efectivo || 0)}</p>
                </CardContent>
              </Card>
              <Card className="border-l-4 border-l-blue-500">
                <CardContent className="p-3">
                  <p className="text-xs text-zinc-500">Tarjetas (Bruto)</p>
                  <p className="text-xl font-bold text-blue-600">{formatCurrency(resumen.total_tarjetas_bruto || 0)}</p>
                </CardContent>
              </Card>
              <Card className="border-l-4 border-l-red-500">
                <CardContent className="p-3">
                  <p className="text-xs text-zinc-500">Comisiones</p>
                  <p className="text-xl font-bold text-red-600">-{formatCurrency(resumen.total_comisiones || 0)}</p>
                </CardContent>
              </Card>
              <Card className="border-l-4 border-l-purple-500">
                <CardContent className="p-3">
                  <p className="text-xs text-zinc-500">Neto Tarjetas</p>
                  <p className="text-xl font-bold text-purple-600">{formatCurrency(resumen.total_neto_tarjetas || 0)}</p>
                </CardContent>
              </Card>
              <Card className="border-l-4 border-l-zinc-800 bg-zinc-800 text-white">
                <CardContent className="p-3">
                  <p className="text-xs text-zinc-300">TOTAL VENTAS</p>
                  <p className="text-xl font-bold">{formatCurrency(resumen.total_ventas || 0)}</p>
                </CardContent>
              </Card>
            </div>
            
            {/* Tabla de cortes */}
            <Card>
              <CardContent className="p-0">
                <div className="overflow-x-auto max-h-[500px]">
                  <table className="w-full text-xs">
                    <thead className="bg-zinc-800 text-white sticky top-0">
                      <tr>
                        <th className="p-2 text-left">Fecha</th>
                        <th className="p-2 text-left">Sucursal</th>
                        <th className="p-2 text-right">Efectivo</th>
                        <th className="p-2 text-right">Débito</th>
                        <th className="p-2 text-right">Crédito</th>
                        <th className="p-2 text-right">AMEX</th>
                        <th className="p-2 text-right">Int'l</th>
                        <th className="p-2 text-right">Comisiones</th>
                        <th className="p-2 text-right">Total</th>
                        <th className="p-2 text-center">Efectivo</th>
                        <th className="p-2 text-center">Tarjetas</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(cortesData?.cortes || []).map(corte => (
                        <tr key={corte.corte_id} className={`border-b hover:bg-zinc-50 ${corte.conciliado ? 'bg-green-50' : ''}`}>
                          <td className="p-2">
                            <div>
                              <p className="font-medium">{corte.fecha_corte}</p>
                              <p className="text-zinc-400">{corte.dia_semana}</p>
                            </div>
                          </td>
                          <td className="p-2 font-medium">{corte.sucursal_nombre}</td>
                          <td className="p-2 text-right font-mono text-green-600">{formatCurrency(corte.efectivo)}</td>
                          <td className="p-2 text-right font-mono">{formatCurrency(corte.debito)}</td>
                          <td className="p-2 text-right font-mono">{formatCurrency(corte.credito)}</td>
                          <td className="p-2 text-right font-mono">{corte.amex > 0 ? formatCurrency(corte.amex) : '-'}</td>
                          <td className="p-2 text-right font-mono">{corte.internacional > 0 ? formatCurrency(corte.internacional) : '-'}</td>
                          <td className="p-2 text-right font-mono text-red-500">-{formatCurrency(corte.total_comisiones)}</td>
                          <td className="p-2 text-right font-mono font-bold">{formatCurrency(corte.total_venta)}</td>
                          <td className="p-2 text-center">
                            {corte.efectivo_depositado ? (
                              <span className="text-green-600 flex items-center justify-center gap-1">
                                <CheckCircle2 className="h-4 w-4" />
                                <span className="text-[10px]">{corte.efectivo_referencia_deposito}</span>
                              </span>
                            ) : (
                              <button
                                onClick={() => {
                                  const ref = prompt('Referencia del depósito:');
                                  if (ref) handleDepositoEfectivo(corte.corte_id, ref);
                                }}
                                className="text-yellow-600 hover:text-yellow-800"
                                title={`Depositar ${corte.fecha_deposito_efectivo}`}
                              >
                                <Clock className="h-4 w-4" />
                              </button>
                            )}
                          </td>
                          <td className="p-2 text-center">
                            {corte.tarjetas_depositadas ? (
                              <span className="text-green-600 flex items-center justify-center gap-1">
                                <CheckCircle2 className="h-4 w-4" />
                                <span className="text-[10px]">{corte.tarjetas_referencia_netpay}</span>
                              </span>
                            ) : (
                              <button
                                onClick={() => {
                                  const ref = prompt('Referencia NetPay:');
                                  if (ref) handleDepositoTarjetas(corte.corte_id, ref);
                                }}
                                className="text-yellow-600 hover:text-yellow-800"
                                title={`Depositar ${corte.fecha_deposito_debito}`}
                              >
                                <Clock className="h-4 w-4" />
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
        
        {/* === TAB: SALDOS PENDIENTES === */}
        {ingresosSubTab === 'pendientes' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Efectivo Pendiente */}
            <Card>
              <CardHeader className="py-3 bg-green-50 border-b">
                <CardTitle className="text-base flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <DollarSign className="h-5 w-5 text-green-600" />
                    Efectivo por Depositar
                  </span>
                  <span className="text-xl font-bold text-green-600">{formatCurrency(saldos.efectivo?.total_pendiente || 0)}</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0 max-h-[400px] overflow-y-auto">
                {(saldos.efectivo?.por_fecha || []).map(grupo => (
                  <div key={grupo.fecha} className="border-b p-3">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-medium text-sm">{grupo.fecha}</span>
                      <span className="font-bold text-green-600">{formatCurrency(grupo.monto)}</span>
                    </div>
                    <div className="space-y-1">
                      {grupo.cortes.map(c => (
                        <div key={c.corte_id} className="flex justify-between text-xs text-zinc-500">
                          <span>{c.sucursal} ({c.fecha_corte})</span>
                          <span>{formatCurrency(c.monto)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
                {(saldos.efectivo?.por_fecha || []).length === 0 && (
                  <div className="p-8 text-center text-zinc-400">
                    <CheckCircle2 className="h-12 w-12 mx-auto mb-2 text-green-300" />
                    <p>Todo el efectivo está depositado</p>
                  </div>
                )}
              </CardContent>
            </Card>
            
            {/* Tarjetas Pendiente */}
            <Card>
              <CardHeader className="py-3 bg-blue-50 border-b">
                <CardTitle className="text-base flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <CreditCard className="h-5 w-5 text-blue-600" />
                    Tarjetas por Depositar (NetPay)
                  </span>
                  <span className="text-xl font-bold text-blue-600">{formatCurrency(saldos.tarjetas?.total_pendiente_neto || 0)}</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0 max-h-[400px] overflow-y-auto">
                {(saldos.tarjetas?.por_fecha || []).map(grupo => (
                  <div key={grupo.fecha} className="border-b p-3">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-medium text-sm">{grupo.fecha}</span>
                      <div className="text-right">
                        <p className="font-bold text-blue-600">{formatCurrency(grupo.monto_neto)}</p>
                        <p className="text-xs text-zinc-400">Bruto: {formatCurrency(grupo.monto_bruto)} | Com: -{formatCurrency(grupo.comisiones)}</p>
                      </div>
                    </div>
                    <div className="space-y-1">
                      {grupo.cortes.map(c => (
                        <div key={c.corte_id} className="flex justify-between text-xs text-zinc-500">
                          <span>{c.sucursal}</span>
                          <span>D:{formatCurrency(c.debito)} C:{formatCurrency(c.credito)} {c.amex > 0 && `A:${formatCurrency(c.amex)}`}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
                {(saldos.tarjetas?.por_fecha || []).length === 0 && (
                  <div className="p-8 text-center text-zinc-400">
                    <CheckCircle2 className="h-12 w-12 mx-auto mb-2 text-blue-300" />
                    <p>Todas las tarjetas están depositadas</p>
                  </div>
                )}
              </CardContent>
            </Card>
            
            {/* Total */}
            <Card className="md:col-span-2 bg-zinc-800 text-white">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <span className="text-lg">TOTAL POR DEPOSITAR</span>
                  <span className="text-3xl font-bold">{formatCurrency(saldos.total_por_depositar || 0)}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
        
        {/* === TAB: COMISIONES === */}
        {ingresosSubTab === 'comisiones' && (
          <div className="space-y-4">
            {/* Configuración de comisiones */}
            <Card>
              <CardHeader className="py-3 border-b">
                <CardTitle className="text-base">Configuración de Comisiones (NetPay)</CardTitle>
              </CardHeader>
              <CardContent className="p-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(comisiones).map(([tipo, config]) => (
                    <div key={tipo} className="p-4 border rounded-lg">
                      <h4 className="font-medium mb-2">{config.nombre}</h4>
                      <div className="space-y-1 text-sm">
                        <p>Comisión: <span className="font-bold">{config.comision_porcentaje}%</span></p>
                        <p>IVA: <span className="font-bold">{config.iva}%</span></p>
                        <p>Total: <span className="font-bold text-red-600">{config.comision_total_porcentaje}%</span></p>
                        <p>Depósito: <span className="font-bold">{config.dias_deposito} día(s) hábil(es)</span></p>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-4 p-3 bg-yellow-50 rounded-lg text-sm">
                  <p className="font-medium text-yellow-800 mb-1">Reglas de Depósito:</p>
                  <ul className="list-disc list-inside text-yellow-700 space-y-1">
                    <li>Efectivo: día siguiente (Vie/Sáb/Dom → Lunes)</li>
                    <li>Débito/Crédito: 24 hrs hábiles</li>
                    <li>AMEX/Internacional: 48 hrs hábiles</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
            
            {/* Resumen de comisiones del período */}
            {resumenComisiones && (
              <Card>
                <CardHeader className="py-3 border-b">
                  <CardTitle className="text-base">Resumen de Comisiones del Período</CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <table className="w-full text-sm">
                    <thead className="bg-zinc-100">
                      <tr>
                        <th className="p-3 text-left">Tipo</th>
                        <th className="p-3 text-right">Ventas</th>
                        <th className="p-3 text-right">Tasa</th>
                        <th className="p-3 text-right">Comisiones</th>
                        <th className="p-3 text-right">Neto</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(resumenComisiones.por_tipo || {}).map(([tipo, data]) => (
                        <tr key={tipo} className="border-b">
                          <td className="p-3 font-medium capitalize">{tipo}</td>
                          <td className="p-3 text-right font-mono">{formatCurrency(data.ventas)}</td>
                          <td className="p-3 text-right">{data.tasa}</td>
                          <td className="p-3 text-right font-mono text-red-600">-{formatCurrency(data.comisiones)}</td>
                          <td className="p-3 text-right font-mono font-bold">{formatCurrency(data.neto)}</td>
                        </tr>
                      ))}
                      <tr className="bg-zinc-800 text-white font-bold">
                        <td className="p-3">TOTAL</td>
                        <td className="p-3 text-right font-mono">{formatCurrency(resumenComisiones.totales?.ventas || 0)}</td>
                        <td className="p-3"></td>
                        <td className="p-3 text-right font-mono text-red-300">-{formatCurrency(resumenComisiones.totales?.comisiones || 0)}</td>
                        <td className="p-3 text-right font-mono">{formatCurrency(resumenComisiones.totales?.neto || 0)}</td>
                      </tr>
                    </tbody>
                  </table>
                </CardContent>
              </Card>
            )}
          </div>
        )}
        
        {/* === TAB: CONCILIACIÓN === */}
        {ingresosSubTab === 'conciliacion' && (
          <Card className="border-2 border-dashed">
            <CardContent className="py-12 text-center">
              <FileSpreadsheet className="h-16 w-16 text-zinc-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-zinc-600 mb-2">Conciliación Bancaria</h3>
              <p className="text-zinc-400 text-sm max-w-md mx-auto mb-4">
                Cargue el estado de cuenta de BBVA u otro banco para conciliar automáticamente los depósitos de efectivo y tarjetas.
              </p>
              <Button variant="outline" className="mt-2">
                <Upload className="h-4 w-4 mr-2" />
                Cargar Estado de Cuenta
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };
  
  // Render Cuentas por Pagar
  const renderCuentasPorPagar = () => {
    const totales = cxpData?.totales || {};
    const antiguedad = cxpResumen?.antiguedad || {};
    
    return (
      <div className="space-y-4">
        {/* Filtros */}
        <Card>
          <CardContent className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-6 gap-3 items-end">
              <div>
                <Label className="text-xs text-zinc-500">Fecha de Corte</Label>
                <Input
                  type="date"
                  value={cxpFechaCorte}
                  onChange={(e) => setCxpFechaCorte(e.target.value)}
                  className="mt-1"
                />
              </div>
              <div>
                <Label className="text-xs text-zinc-500">Sucursal</Label>
                <select
                  value={cxpFiltroSucursal}
                  onChange={(e) => setCxpFiltroSucursal(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg text-sm mt-1"
                >
                  <option value="">Todas</option>
                  {cxpSucursales.map(s => (
                    <option key={s.SucursalID} value={s.SucursalID}>
                      {s.Nombre_Sucursal} ({s.CantidadFacturas || 0} fact.)
                    </option>
                  ))}
                </select>
              </div>
              <div className="relative">
                <Label className="text-xs text-zinc-500">Proveedor</Label>
                <Input
                  type="text"
                  placeholder="Buscar nombre, RFC, clave..."
                  value={cxpBusquedaProveedor}
                  onChange={(e) => setCxpBusquedaProveedor(e.target.value)}
                  className="mt-1"
                  data-testid="cxp-busqueda-proveedor"
                />
                {cxpBusquedaProveedor && (
                  <div className="absolute z-50 w-full mt-1 bg-white border rounded-lg shadow-lg max-h-60 overflow-y-auto">
                    {cxpProveedores
                      .filter(p => {
                        const busqueda = cxpBusquedaProveedor.toLowerCase();
                        return (
                          (p.proveedor_nombre || '').toLowerCase().includes(busqueda) ||
                          (p.proveedor_rfc || '').toLowerCase().includes(busqueda) ||
                          String(p.proveedor_id || '').toLowerCase().includes(busqueda)
                        );
                      })
                      .map(p => (
                        <div
                          key={p.proveedor_id}
                          className="px-3 py-2 hover:bg-zinc-100 cursor-pointer text-sm border-b last:border-b-0"
                          onClick={() => {
                            setCxpFiltroProveedor(p.proveedor_id);
                            setCxpBusquedaProveedor(p.proveedor_nombre);
                          }}
                          data-testid={`cxp-proveedor-option-${p.proveedor_id}`}
                        >
                          <div className="font-medium">{p.proveedor_nombre}</div>
                          <div className="text-xs text-zinc-500 flex justify-between">
                            <span>RFC: {p.proveedor_rfc || 'N/A'}</span>
                            <span className="text-green-600">{p.cantidad_facturas} fact.</span>
                          </div>
                        </div>
                      ))
                    }
                    {cxpProveedores.filter(p => {
                      const busqueda = cxpBusquedaProveedor.toLowerCase();
                      return (
                        (p.proveedor_nombre || '').toLowerCase().includes(busqueda) ||
                        (p.proveedor_rfc || '').toLowerCase().includes(busqueda) ||
                        String(p.proveedor_id || '').toLowerCase().includes(busqueda)
                      );
                    }).length === 0 && (
                      <div className="px-3 py-2 text-sm text-zinc-500 text-center">
                        Sin resultados
                      </div>
                    )}
                  </div>
                )}
                {cxpFiltroProveedor && (
                  <button
                    onClick={() => { setCxpFiltroProveedor(''); setCxpBusquedaProveedor(''); }}
                    className="absolute right-2 top-8 text-zinc-400 hover:text-zinc-600"
                    title="Limpiar filtro"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={cxpSoloVencidas}
                    onChange={(e) => setCxpSoloVencidas(e.target.checked)}
                    className="rounded"
                  />
                  Solo vencidas
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={cxpSoloDecision}
                    onChange={(e) => setCxpSoloDecision(e.target.checked)}
                    className="rounded"
                  />
                  Con decisión
                </label>
              </div>
              <div className="flex gap-2">
                <Button onClick={loadCuentasPorPagar} disabled={loading} className="flex-1">
                  <RefreshCw className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
                  Filtrar
                </Button>
                <Button variant="outline" onClick={exportarCxPCSV}>
                  <Download className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Acciones Masivas */}
        {(cxpData?.proveedores || []).length > 0 && (
          <div className="flex items-center justify-between bg-zinc-100 rounded-lg p-3">
            <div className="flex items-center gap-4 text-sm">
              <span className="text-zinc-600">
                <strong className="text-red-600">{cxpData?.totales?.total_vencidas || 0}</strong> facturas vencidas
              </span>
              <span className="text-zinc-400">|</span>
              <span className="text-zinc-600">
                <strong className="text-green-600">{cxpResumen?.resumen?.facturas_con_decision || 0}</strong> marcadas para pago
              </span>
              <span className="text-zinc-400">|</span>
              <span className="font-bold text-blue-600">
                Total a pagar: {formatCurrency(cxpData?.totales?.total_a_pagar || 0)}
              </span>
            </div>
            <div className="flex gap-2">
              <Button 
                onClick={handleMarcarTodasVencidasPago}
                disabled={loading}
                className="bg-green-600 hover:bg-green-700"
              >
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Marcar Todas las Vencidas
              </Button>
              <Button 
                onClick={handleDesmarcarTodasPago}
                disabled={loading}
                variant="outline"
                className="text-red-600 border-red-300 hover:bg-red-50"
              >
                <XCircle className="h-4 w-4 mr-2" />
                Desmarcar Todas
              </Button>
            </div>
          </div>
        )}
        
        {/* Resumen por Antigüedad */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
          <Card className="border-l-4 border-l-green-500">
            <CardContent className="p-3">
              <p className="text-xs text-zinc-500">Corriente</p>
              <p className="text-lg font-bold text-green-600">{formatCurrency(antiguedad.corriente?.monto || 0)}</p>
              <p className="text-xs text-zinc-400">{antiguedad.corriente?.cantidad || 0} facturas</p>
            </CardContent>
          </Card>
          <Card className="border-l-4 border-l-yellow-500">
            <CardContent className="p-3">
              <p className="text-xs text-zinc-500">1-30 días</p>
              <p className="text-lg font-bold text-yellow-600">{formatCurrency(antiguedad.vencidas_1_30?.monto || 0)}</p>
              <p className="text-xs text-zinc-400">{antiguedad.vencidas_1_30?.cantidad || 0} facturas</p>
            </CardContent>
          </Card>
          <Card className="border-l-4 border-l-orange-500">
            <CardContent className="p-3">
              <p className="text-xs text-zinc-500">31-60 días</p>
              <p className="text-lg font-bold text-orange-600">{formatCurrency(antiguedad.vencidas_31_60?.monto || 0)}</p>
              <p className="text-xs text-zinc-400">{antiguedad.vencidas_31_60?.cantidad || 0} facturas</p>
            </CardContent>
          </Card>
          <Card className="border-l-4 border-l-red-500">
            <CardContent className="p-3">
              <p className="text-xs text-zinc-500">61-90 días</p>
              <p className="text-lg font-bold text-red-600">{formatCurrency(antiguedad.vencidas_61_90?.monto || 0)}</p>
              <p className="text-xs text-zinc-400">{antiguedad.vencidas_61_90?.cantidad || 0} facturas</p>
            </CardContent>
          </Card>
          <Card className="border-l-4 border-l-red-700">
            <CardContent className="p-3">
              <p className="text-xs text-zinc-500">+90 días</p>
              <p className="text-lg font-bold text-red-700">{formatCurrency(antiguedad.vencidas_90_plus?.monto || 0)}</p>
              <p className="text-xs text-zinc-400">{antiguedad.vencidas_90_plus?.cantidad || 0} facturas</p>
            </CardContent>
          </Card>
          <Card className="border-l-4 border-l-blue-600 bg-blue-50">
            <CardContent className="p-3">
              <p className="text-xs text-blue-600 font-medium">TOTAL A PAGAR</p>
              <p className="text-lg font-bold text-blue-700">{formatCurrency(totales.total_a_pagar || 0)}</p>
              <p className="text-xs text-blue-500">{cxpResumen?.resumen?.facturas_con_decision || 0} facturas</p>
            </CardContent>
          </Card>
        </div>
        
        {/* Botones Expandir/Colapsar y Toggle de Vista */}
        {(cxpData?.proveedores || []).length > 0 && (
          <div className="flex items-center justify-between">
            {/* Toggle de Vista */}
            <div className="flex items-center gap-2 bg-zinc-100 rounded-lg p-1">
              <button
                onClick={() => setCxpVistaMode('categorias')}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                  cxpVistaMode === 'categorias' 
                    ? 'bg-white text-zinc-800 shadow-sm' 
                    : 'text-zinc-500 hover:text-zinc-700'
                }`}
              >
                <PieChart className="h-3 w-3 inline mr-1" />
                Por Categoría
              </button>
              <button
                onClick={() => setCxpVistaMode('proveedores')}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                  cxpVistaMode === 'proveedores' 
                    ? 'bg-white text-zinc-800 shadow-sm' 
                    : 'text-zinc-500 hover:text-zinc-700'
                }`}
              >
                <Building2 className="h-3 w-3 inline mr-1" />
                Por Proveedor
              </button>
            </div>
            
            {/* Botones Expandir/Colapsar */}
            <div className="flex items-center gap-2">
              <Button 
                variant="outline" 
                size="sm"
                onClick={expandirTodos}
                className="text-xs"
              >
                <ChevronDown className="h-3 w-3 mr-1" />
                Expandir Todos
              </Button>
              <Button 
                variant="outline" 
                size="sm"
                onClick={colapsarTodos}
                className="text-xs"
              >
                <ChevronUp className="h-3 w-3 mr-1" />
                Colapsar Todos
              </Button>
            </div>
          </div>
        )}
        
        {/* Vista de datos según modo seleccionado */}
        <div className="space-y-4">
          {(cxpData?.proveedores || []).length === 0 ? (
            <Card className="border-2 border-dashed">
              <CardContent className="py-12 text-center">
                <CreditCard className="h-12 w-12 text-zinc-300 mx-auto mb-4" />
                <p className="text-zinc-500">No hay facturas pendientes con los filtros seleccionados</p>
              </CardContent>
            </Card>
          ) : cxpVistaMode === 'categorias' ? (
            /* VISTA POR CATEGORÍAS (A, B, X, M) -> Proveedor -> Facturas */
            reagruparCxPPorProveedores(cxpData?.proveedores || []).map(categoria => (
              <Card key={categoria.tipo} className="overflow-hidden border-2" data-testid={`categoria-${categoria.tipo}`}>
                {/* Header de Categoría (A, B, X, M) */}
                <div
                  className={`px-4 py-3 flex items-center justify-between cursor-pointer transition ${
                    categoria.tipo === 'A' ? 'bg-emerald-600 hover:bg-emerald-700 text-white' :
                    categoria.tipo === 'B' ? 'bg-amber-600 hover:bg-amber-700 text-white' :
                    categoria.tipo === 'M' ? 'bg-indigo-600 hover:bg-indigo-700 text-white' :
                    'bg-slate-600 hover:bg-slate-700 text-white'
                  }`}
                  onClick={() => toggleCategoria(categoria.tipo)}
                >
                  <div className="flex items-center gap-3">
                    <ChevronRight className={`h-6 w-6 transition-transform ${cxpCategoriasExpandidas[categoria.tipo] ? 'rotate-90' : ''}`} />
                    <div>
                      <h2 className="text-lg font-bold">{categoria.nombre}</h2>
                      <p className="text-xs opacity-80">{categoria.proveedores.length} proveedores</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-6 text-sm">
                    <div className="text-right">
                      <p className="text-xs opacity-80">Facturas</p>
                      <p className="font-bold text-lg">{categoria.cantidad_facturas}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs opacity-80">Saldo Total</p>
                      <p className="font-bold text-lg">{formatCurrency(categoria.subtotal_saldo)}</p>
                    </div>
                    {categoria.cantidad_vencidas > 0 && (
                      <span className="px-3 py-1 bg-red-500 rounded-full text-xs font-bold">
                        {categoria.cantidad_vencidas} vencidas
                      </span>
                    )}
                  </div>
                </div>
                
                {/* Proveedores dentro de la categoría */}
                {cxpCategoriasExpandidas[categoria.tipo] && (
                  <div className="divide-y divide-zinc-200">
                    {categoria.proveedores.map(proveedor => {
                      const provKey = `${categoria.tipo}_${proveedor.proveedor_nombre}`;
                      return (
                        <div key={provKey} className="bg-white">
                          {/* Header del Proveedor */}
                          <div
                            className="bg-zinc-100 px-4 py-2 flex items-center justify-between cursor-pointer hover:bg-zinc-200 transition border-l-4 border-l-zinc-400"
                            onClick={() => toggleProveedor(provKey)}
                            data-testid={`proveedor-${provKey}`}
                          >
                            <div className="flex items-center gap-2">
                              <ChevronRight className={`h-4 w-4 transition-transform ${cxpExpandidos[provKey] ? 'rotate-90' : ''}`} />
                              <div>
                                <h3 className="font-medium text-sm text-zinc-800">{proveedor.proveedor_nombre}</h3>
                                {proveedor.sucursal && (
                                  <p className="text-xs text-zinc-500">{proveedor.sucursal}</p>
                                )}
                              </div>
                            </div>
                            <div className="flex items-center gap-4 text-xs">
                              <div className="text-right">
                                <p className="text-zinc-500">Facturas</p>
                                <p className="font-medium">{proveedor.cantidad_facturas}</p>
                              </div>
                              <div className="text-right">
                                <p className="text-zinc-500">Saldo</p>
                                <p className="font-bold text-zinc-800">{formatCurrency(proveedor.subtotal_saldo)}</p>
                              </div>
                              {proveedor.cantidad_vencidas > 0 && (
                                <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs font-medium">
                                  {proveedor.cantidad_vencidas} venc.
                                </span>
                              )}
                            </div>
                          </div>
                          
                          {/* Facturas del proveedor */}
                          {cxpExpandidos[provKey] && (
                            <div className="overflow-x-auto">
                              <table className="w-full text-xs">
                                <thead className="bg-zinc-50">
                                  <tr>
                                    <th className="text-left p-2 font-medium text-zinc-600">Folio Entrada</th>
                                    <th className="text-left p-2 font-medium text-zinc-600">Folio Factura</th>
                                    <th className="text-center p-2 font-medium text-zinc-600">F. Entrada</th>
                                    <th className="text-center p-2 font-medium text-zinc-600">F. Vencimiento</th>
                                    <th className="text-center p-2 font-medium text-zinc-600">Días Venc.</th>
                                    <th className="text-left p-2 font-medium text-zinc-600">Referencia</th>
                                    <th className="text-right p-2 font-medium text-zinc-600">Importe</th>
                                    <th className="text-right p-2 font-medium text-zinc-600">Saldo</th>
                                    <th className="text-center p-2 font-medium text-zinc-600">Pagar</th>
                                    <th className="text-right p-2 font-medium text-zinc-600">Importe a Pagar</th>
                                    <th className="text-center p-2 font-medium text-zinc-600">Docs</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {proveedor.facturas.map((factura, idx) => (
                                    <tr key={factura.factura_id || idx} className={`border-b hover:bg-zinc-50 ${factura.dias_vencida > 0 ? 'bg-red-50' : ''}`}>
                                      <td className="p-2 font-mono text-zinc-700">{factura.folio_entrada || 'N/A'}</td>
                                      <td className="p-2 font-mono text-zinc-700">{factura.folio_factura || '-'}</td>
                                      <td className="p-2 text-center text-zinc-600">{factura.fecha_entrada?.split('T')[0] || '-'}</td>
                                      <td className="p-2 text-center text-zinc-600">{factura.fecha_vencimiento || '-'}</td>
                                      <td className="p-2 text-center">
                                        <span className={`font-bold ${factura.dias_vencida > 0 ? 'text-red-600' : 'text-green-600'}`}>
                                          {factura.dias_vencida > 0 ? factura.dias_vencida : '-'}
                                        </span>
                                      </td>
                                      <td className="p-2 max-w-[150px] truncate text-zinc-600" title={factura.referencia || factura.observaciones}>
                                        {factura.referencia || factura.observaciones || '-'}
                                      </td>
                                      <td className="p-2 text-right font-mono">{formatCurrency(factura.importe_original || factura.importe_total || 0)}</td>
                                      <td className="p-2 text-right font-mono font-bold">{formatCurrency(factura.saldo)}</td>
                                      <td className="p-2 text-center">
                                        <button
                                          onClick={(e) => { e.stopPropagation(); handleDecisionPago(factura.factura_id, !factura.decision_pago); }}
                                          disabled={savingDecision === factura.factura_id}
                                          className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition ${
                                            factura.decision_pago 
                                              ? 'bg-green-500 border-green-500 text-white' 
                                              : 'border-zinc-300 hover:border-green-400'
                                          }`}
                                        >
                                          {savingDecision === factura.factura_id ? (
                                            <RefreshCw className="h-3 w-3 animate-spin" />
                                          ) : factura.decision_pago ? (
                                            <CheckCircle2 className="h-4 w-4" />
                                          ) : null}
                                        </button>
                                      </td>
                                      <td className="p-2 text-right font-mono text-green-600 font-bold">
                                        {factura.decision_pago ? formatCurrency(factura.importe_a_pagar || factura.saldo) : '-'}
                                      </td>
                                      <td className="p-2">
                                        <div className="flex items-center justify-center gap-1">
                                          <button className="p-1 hover:bg-zinc-200 rounded" title="PDF Factura">
                                            <FileText className="h-4 w-4 text-red-500" />
                                          </button>
                                          <button className="p-1 hover:bg-zinc-200 rounded" title="XML">
                                            <File className="h-4 w-4 text-green-600" />
                                          </button>
                                          <button className="p-1 hover:bg-zinc-200 rounded" title="Entrada Sistema">
                                            <FileSpreadsheet className="h-4 w-4 text-blue-500" />
                                          </button>
                                        </div>
                                      </td>
                                    </tr>
                                  ))}
                                  {/* Subtotal del proveedor */}
                                  <tr className="bg-zinc-200 font-bold">
                                    <td colSpan={6} className="p-2 text-right text-xs">SUBTOTAL {proveedor.proveedor_nombre}:</td>
                                    <td className="p-2 text-right font-mono">{formatCurrency(proveedor.subtotal_importe)}</td>
                                    <td className="p-2 text-right font-mono">{formatCurrency(proveedor.subtotal_saldo)}</td>
                                    <td className="p-2"></td>
                                    <td className="p-2 text-right font-mono text-green-700">{formatCurrency(proveedor.facturas.reduce((sum, f) => sum + (f.decision_pago ? (f.importe_a_pagar || f.saldo || 0) : 0), 0))}</td>
                                    <td className="p-2"></td>
                                  </tr>
                                </tbody>
                              </table>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </Card>
            ))
          ) : (
            /* VISTA POR PROVEEDOR CON AGRUPACIÓN A/B/C - Mismo estilo que Por Categoría */
            reagruparCxPPorProveedores(cxpData?.proveedores || []).map(categoria => {
              const colorCategoria = {
                A: { bg: 'bg-blue-600', border: 'border-l-blue-500', text: 'ALIMENTOS' },
                B: { bg: 'bg-amber-600', border: 'border-l-amber-500', text: 'BEBIDAS' },
                X: { bg: 'bg-zinc-600', border: 'border-l-zinc-500', text: 'OTROS' },
                M: { bg: 'bg-purple-600', border: 'border-l-purple-500', text: 'MPRO' }
              }[categoria.tipo] || { bg: 'bg-zinc-600', border: 'border-l-zinc-500', text: 'OTROS' };
              
              return (
                <Card key={categoria.tipo} className={`overflow-hidden ${colorCategoria.border} border-l-4`} data-testid={`categoria-prov-${categoria.tipo}`}>
                  {/* Header de Categoría */}
                  <div
                    className={`${colorCategoria.bg} text-white px-4 py-3 flex items-center justify-between cursor-pointer hover:opacity-90 transition`}
                    onClick={() => toggleCategoria(categoria.tipo)}
                  >
                    <div className="flex items-center gap-3">
                      <ChevronRight className={`h-5 w-5 transition-transform ${cxpCategoriasExpandidas[categoria.tipo] ? 'rotate-90' : ''}`} />
                      <div>
                        <h2 className="font-bold text-lg">{categoria.tipo} - {colorCategoria.text}</h2>
                        <p className="text-xs opacity-80">{categoria.proveedores.length} proveedores | {categoria.cantidad_facturas} facturas</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-6 text-sm">
                      <div className="text-right">
                        <p className="text-xs opacity-80">Saldo Total</p>
                        <p className="font-bold text-lg">{formatCurrency(categoria.subtotal_saldo)}</p>
                      </div>
                      {categoria.cantidad_vencidas > 0 && (
                        <span className="px-3 py-1 bg-red-500 rounded-full text-xs font-bold">
                          {categoria.cantidad_vencidas} vencidas
                        </span>
                      )}
                    </div>
                  </div>
                  
                  {/* Proveedores dentro de la categoría */}
                  {cxpCategoriasExpandidas[categoria.tipo] && (
                    <div className="divide-y divide-zinc-200">
                      {categoria.proveedores.map(proveedor => {
                        const provKey = `prov_${categoria.tipo}_${proveedor.proveedor_nombre}`;
                        return (
                          <div key={provKey} className="bg-white">
                            {/* Header del Proveedor */}
                            <div
                              className="bg-zinc-100 px-4 py-2 flex items-center justify-between cursor-pointer hover:bg-zinc-200 transition border-l-4 border-l-zinc-400"
                              onClick={() => toggleProveedor(provKey)}
                              data-testid={`proveedor-prov-${provKey}`}
                            >
                              <div className="flex items-center gap-2">
                                <ChevronRight className={`h-4 w-4 transition-transform ${cxpExpandidos[provKey] ? 'rotate-90' : ''}`} />
                                <div>
                                  <h3 className="font-medium text-sm text-zinc-800">{proveedor.proveedor_nombre}</h3>
                                  {proveedor.sucursal && (
                                    <p className="text-xs text-zinc-500">{proveedor.sucursal}</p>
                                  )}
                                </div>
                              </div>
                              <div className="flex items-center gap-4 text-xs">
                                <div className="text-right">
                                  <p className="text-zinc-500">Facturas</p>
                                  <p className="font-medium">{proveedor.cantidad_facturas}</p>
                                </div>
                                <div className="text-right">
                                  <p className="text-zinc-500">Saldo</p>
                                  <p className="font-bold text-zinc-800">{formatCurrency(proveedor.subtotal_saldo)}</p>
                                </div>
                                {proveedor.cantidad_vencidas > 0 && (
                                  <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs font-medium">
                                    {proveedor.cantidad_vencidas} venc.
                                  </span>
                                )}
                              </div>
                            </div>
                            
                            {/* Facturas del proveedor */}
                            {cxpExpandidos[provKey] && (
                              <div className="overflow-x-auto">
                                <table className="w-full text-xs">
                                  <thead className="bg-zinc-50">
                                    <tr>
                                      <th className="text-left p-2 font-medium text-zinc-600">Folio Entrada</th>
                                      <th className="text-left p-2 font-medium text-zinc-600">Folio Factura</th>
                                      <th className="text-center p-2 font-medium text-zinc-600">F. Entrada</th>
                                      <th className="text-center p-2 font-medium text-zinc-600">F. Vencimiento</th>
                                      <th className="text-center p-2 font-medium text-zinc-600">Días Venc.</th>
                                      <th className="text-left p-2 font-medium text-zinc-600">Referencia</th>
                                      <th className="text-right p-2 font-medium text-zinc-600">Importe</th>
                                      <th className="text-right p-2 font-medium text-zinc-600">Saldo</th>
                                      <th className="text-center p-2 font-medium text-zinc-600">Pagar</th>
                                      <th className="text-right p-2 font-medium text-zinc-600">Importe a Pagar</th>
                                      <th className="text-center p-2 font-medium text-zinc-600">Docs</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {proveedor.facturas.map((factura, idx) => (
                                      <tr key={factura.factura_id || idx} className={`border-b hover:bg-zinc-50 ${factura.dias_vencida > 0 ? 'bg-red-50' : ''}`}>
                                        <td className="p-2 font-mono text-zinc-700">{factura.folio_entrada || 'N/A'}</td>
                                        <td className="p-2 font-mono text-zinc-700">{factura.folio_factura || '-'}</td>
                                        <td className="p-2 text-center text-zinc-600">{factura.fecha_entrada?.split('T')[0] || '-'}</td>
                                        <td className="p-2 text-center text-zinc-600">{factura.fecha_vencimiento || '-'}</td>
                                        <td className="p-2 text-center">
                                          <span className={`font-bold ${factura.dias_vencida > 0 ? 'text-red-600' : 'text-green-600'}`}>
                                            {factura.dias_vencida > 0 ? factura.dias_vencida : '-'}
                                          </span>
                                        </td>
                                        <td className="p-2 max-w-[150px] truncate text-zinc-600" title={factura.referencia || factura.observaciones}>
                                          {factura.referencia || factura.observaciones || '-'}
                                        </td>
                                        <td className="p-2 text-right font-mono">{formatCurrency(factura.importe_original || factura.importe_total || 0)}</td>
                                        <td className="p-2 text-right font-mono font-bold">{formatCurrency(factura.saldo)}</td>
                                        <td className="p-2 text-center">
                                          <button
                                            onClick={(e) => { e.stopPropagation(); handleDecisionPago(factura.factura_id, !factura.decision_pago); }}
                                            disabled={savingDecision === factura.factura_id}
                                            className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition ${
                                              factura.decision_pago 
                                                ? 'bg-green-500 border-green-500 text-white' 
                                                : 'border-zinc-300 hover:border-green-400'
                                            }`}
                                          >
                                            {savingDecision === factura.factura_id ? (
                                              <RefreshCw className="h-3 w-3 animate-spin" />
                                            ) : factura.decision_pago ? (
                                              <CheckCircle2 className="h-4 w-4" />
                                            ) : null}
                                          </button>
                                        </td>
                                        <td className="p-2 text-right font-mono text-green-600 font-bold">
                                          {factura.decision_pago ? formatCurrency(factura.importe_a_pagar || factura.saldo) : '-'}
                                        </td>
                                        <td className="p-2">
                                          <div className="flex items-center justify-center gap-1">
                                            <button className="p-1 hover:bg-zinc-200 rounded" title="PDF Factura">
                                              <FileText className="h-4 w-4 text-red-500" />
                                            </button>
                                            <button className="p-1 hover:bg-zinc-200 rounded" title="XML">
                                              <File className="h-4 w-4 text-green-600" />
                                            </button>
                                            <button className="p-1 hover:bg-zinc-200 rounded" title="Entrada Sistema">
                                              <FileSpreadsheet className="h-4 w-4 text-blue-500" />
                                            </button>
                                          </div>
                                        </td>
                                      </tr>
                                    ))}
                                    {/* Subtotal del proveedor */}
                                    <tr className="bg-zinc-200 font-bold">
                                      <td colSpan={6} className="p-2 text-right text-xs">SUBTOTAL {proveedor.proveedor_nombre}:</td>
                                      <td className="p-2 text-right font-mono">{formatCurrency(proveedor.subtotal_importe)}</td>
                                      <td className="p-2 text-right font-mono">{formatCurrency(proveedor.subtotal_saldo)}</td>
                                      <td className="p-2"></td>
                                      <td className="p-2 text-right font-mono text-green-700">{formatCurrency(proveedor.facturas.reduce((sum, f) => sum + (f.decision_pago ? (f.importe_a_pagar || f.saldo || 0) : 0), 0))}</td>
                                      <td className="p-2"></td>
                                    </tr>
                                  </tbody>
                                </table>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </Card>
              );
            })
          )}
        </div>
        
        {/* Totales Generales */}
        {(cxpData?.proveedores || []).length > 0 && (
          <Card className="bg-zinc-800 text-white">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-6">
                  <div>
                    <p className="text-xs text-zinc-400">Proveedores</p>
                    <p className="text-xl font-bold">{totales.total_proveedores}</p>
                  </div>
                  <div>
                    <p className="text-xs text-zinc-400">Facturas</p>
                    <p className="text-xl font-bold">{totales.total_facturas}</p>
                  </div>
                  <div>
                    <p className="text-xs text-zinc-400">Vencidas</p>
                    <p className="text-xl font-bold text-red-400">{totales.total_vencidas}</p>
                  </div>
                </div>
                <div className="flex items-center gap-6 text-right">
                  <div>
                    <p className="text-xs text-zinc-400">Total Importe</p>
                    <p className="text-xl font-bold">{formatCurrency(totales.total_importe)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-zinc-400">Total Saldo</p>
                    <p className="text-xl font-bold">{formatCurrency(totales.total_saldo)}</p>
                  </div>
                  <div className="bg-green-600 rounded-lg px-4 py-2">
                    <p className="text-xs text-green-200">TOTAL A PAGAR</p>
                    <p className="text-2xl font-bold">{formatCurrency(totales.total_a_pagar)}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };
  
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
                  {porSucursal.map((s, i) => {
                    const varIng = s.Ingresos_Pres > 0 ? Math.round(((s.Ingresos - s.Ingresos_Pres) / s.Ingresos_Pres) * 100) : 0;
                    const varEgr = s.Egresos_Pres > 0 ? Math.round(((s.Egresos - s.Egresos_Pres) / s.Egresos_Pres) * 100) : 0;
                    const utilidad = (s.Ingresos || 0) - (s.Egresos || 0);
                    
                    return (
                      <tr key={i} className="border-b">
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
      
      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b pb-2">
        {tabs.map(tab => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
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
          {activeTab === 'propinas' && <PropinasTPV />}
          {activeTab === 'tesoreria' && <TesoreriaCorteZ />}
          {activeTab === 'presupuestos' && renderPresupuestos()}
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
                <Label className="text-sm font-medium">Sucursal *</Label>
                <select
                  value={formPresupuesto.sucursal_id}
                  onChange={(e) => setFormPresupuesto({...formPresupuesto, sucursal_id: e.target.value})}
                  className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
                  disabled={editingPresupuesto}
                >
                  <option value="">Seleccionar...</option>
                  {sucursales.map(s => (
                    <option key={s.SucursalID} value={s.SucursalID}>{s.Nombre_Sucursal}</option>
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
                      .map((c, i) => (
                        <option key={i} value={c.Categoria}>{c.Categoria}</option>
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
                      <option key={i} value={i + 1}>{m}</option>
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
                    <li key={i}>{inst}</li>
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
