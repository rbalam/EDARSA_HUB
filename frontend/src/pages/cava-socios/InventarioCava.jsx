/**
 * EDARSA HUB - Inventario Global, Kardex y Auditoría Física de Cavas
 * ===================================================================
 * Portal integral de gestión de botellas en resguardo:
 * 1. Botellas en Custodia (PZ)
 * 2. Carga de Inventario Inicial (PZ)
 * 3. Kardex Canónico de Cavas (PZ)
 * 4. Auditoría e Inventario Físico vs Stock Teórico
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Wine, Search, Filter, RefreshCw, AlertCircle, 
  ChevronLeft, ChevronRight, QrCode, Eye, Package,
  Layers, DollarSign, Printer, Plus, Trash2, CheckCircle2,
  ArrowRightLeft, ClipboardCheck, ArrowUpRight, Save, User
} from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import api from '@/lib/api';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from '@/components/ui/label';
import {
  CorporateFiltersProvider,
  useCorporateFilters,
} from '../../filters';
import { useAccessContext } from '../../hooks/useAccessContext';
import CavaNavHeader from './CavaNavHeader';

const PAGE_SIZE = 15;

const TIPOS_BEBIDA = [
  { value: 'todos', label: 'Todos los tipos' },
  { value: 'VINO_TINTO', label: 'Vino Tinto' },
  { value: 'VINO_BLANCO', label: 'Vino Blanco' },
  { value: 'VINO_ROSADO', label: 'Vino Rosado' },
  { value: 'CHAMPAGNE', label: 'Champagne / Espumoso' },
  { value: 'WHISKY', label: 'Whisky' },
  { value: 'TEQUILA', label: 'Tequila' },
  { value: 'MEZCAL', label: 'Mezcal' },
  { value: 'COGNAC', label: 'Cognac / Brandy' },
  { value: 'VODKA', label: 'Vodka' },
  { value: 'RON', label: 'Ron' },
  { value: 'GIN', label: 'Ginebra' },
  { value: 'OTRO', label: 'Otro' }
];

const TIPOS_MOVIMIENTO_KARDEX = [
  { value: 'todos', label: 'Todos los movimientos' },
  { value: 'INVENTARIO_INICIAL', label: 'Inventario Inicial' },
  { value: 'ENTRADA', label: 'Entrada / Custodia' },
  { value: 'CONSUMO_PARCIAL', label: 'Consumo Parcial' },
  { value: 'CONSUMO_TOTAL', label: 'Consumo Total' },
  { value: 'AJUSTE_FISICO_SOBRANTE', label: 'Ajuste Físico (Sobrante)' },
  { value: 'AJUSTE_FISICO_FALTANTE', label: 'Ajuste Físico (Faltante)' },
  { value: 'RETIRO', label: 'Retiro por Socio' }
];

function InventarioCavaContent() {
  const navigate = useNavigate();
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const activeTab = searchParams.get('tab') || 'custodia';

  const { selected, loading: filtersLoading } = useCorporateFilters();
  const { context, loading: contextLoading, error: contextError } = useAccessContext();
  const unidadNegocioPk = selected?.unidades_negocio || context?.unidad_activa || '';

  // Tab 1: Botellas en Custodia
  const [botellas, setBotellas] = useState([]);
  const [totalBotellas, setTotalBotellas] = useState(0);
  const [valorTotalCustodia, setValorTotalCustodia] = useState(0);
  const [loadingCustodia, setLoadingCustodia] = useState(false);
  const [pageCustodia, setPageCustodia] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [tipoBebidaFilter, setTipoBebidaFilter] = useState('todos');
  const [estatusFilter, setEstatusFilter] = useState('todos');
  const [ubicacionFilter, setUbicacionFilter] = useState('');

  // Modal QR / Etiqueta
  const [selectedEtiqueta, setSelectedEtiqueta] = useState(null);
  const [showEtiquetaDialog, setShowEtiquetaDialog] = useState(false);

  // Modal Consumo Rápido
  const [selectedBotellaConsumo, setSelectedBotellaConsumo] = useState(null);
  const [showConsumoDialog, setShowConsumoDialog] = useState(false);
  const [consumoForm, setConsumoForm] = useState({
    porcentaje_consumido: 100,
    motivo: '',
    monto_descorche: 350
  });
  const [savingConsumo, setSavingConsumo] = useState(false);

  // Tab 2: Carga de Inventario Inicial
  const [sociosOptions, setSociosOptions] = useState([]);
  const [selectedSocioInicial, setSelectedSocioInicial] = useState('');
  const [socioInfoInicial, setSocioInfoInicial] = useState(null);
  const [botellasInicialList, setBotellasInicialList] = useState([
    {
      producto_nombre: '',
      producto_codigo: '',
      marca: '',
      tipo_bebida: 'VINO_TINTO',
      añada: '',
      ubicacion: '',
      valor_declarado: 0,
      puntaje_inicial_pct: 100,
      cantidad_piezas: 1,
      observaciones: 'Inventario inicial'
    }
  ]);
  const [savingInicial, setSavingInicial] = useState(false);
  const [inicialSuccess, setInicialSuccess] = useState(null);
  const [inicialError, setInicialError] = useState(null);

  // Tab 3: Kardex General
  const [kardexMovimientos, setKardexMovimientos] = useState([]);
  const [kardexResumen, setKardexResumen] = useState(null);
  const [totalKardex, setTotalKardex] = useState(0);
  const [pageKardex, setPageKardex] = useState(0);
  const [loadingKardex, setLoadingKardex] = useState(false);
  const [kardexTipoFilter, setKardexTipoFilter] = useState('todos');
  const [kardexFechaInicio, setKardexFechaInicio] = useState('');
  const [kardexFechaFin, setKardexFechaFin] = useState('');

  // Tab 4: Auditoría e Inventario Físico
  const [hojaFisico, setHojaFisico] = useState([]);
  const [conteosFisicos, setConteosFisicos] = useState({});
  const [loadingFisico, setLoadingFisico] = useState(false);
  const [savingFisico, setSavingFisico] = useState(false);
  const [fisicoSuccess, setFisicoSuccess] = useState(null);
  const [observacionesAuditoria, setObservacionesAuditoria] = useState('Auditoría física quincenal de cavas');

  const [globalError, setGlobalError] = useState(null);

  // ==================== FETCH DATA ====================

  const fetchCustodia = useCallback(async () => {
    if (!unidadNegocioPk) return;
    setLoadingCustodia(true);
    try {
      const params = new URLSearchParams({
        unidad_negocio_pk: unidadNegocioPk,
        skip: pageCustodia * PAGE_SIZE,
        limit: PAGE_SIZE
      });
      if (tipoBebidaFilter !== 'todos') params.append('tipo_bebida', tipoBebidaFilter);
      if (estatusFilter !== 'todos') params.append('estatus', estatusFilter);
      if (ubicacionFilter.trim()) params.append('ubicacion', ubicacionFilter.trim());

      const res = await api.get(`/cava-socios/inventario?${params}`);
      setBotellas(res.data?.botellas || []);
      setTotalBotellas(res.data?.total || 0);
      setValorTotalCustodia(res.data?.valor_custodia_total || 0);
      setGlobalError(null);
    } catch (err) {
      console.error('Error cargando inventario:', err);
      setGlobalError('Error consultando botellas en custodia');
    } finally {
      setLoadingCustodia(false);
    }
  }, [unidadNegocioPk, pageCustodia, tipoBebidaFilter, estatusFilter, ubicacionFilter]);

  const fetchSociosOptions = useCallback(async () => {
    if (!unidadNegocioPk) return;
    try {
      const res = await api.get(`/cava-socios/socios?unidad_negocio_pk=${encodeURIComponent(unidadNegocioPk)}&limit=100&estatus=ACTIVO`);
      setSociosOptions(res.data?.socios || []);
    } catch (err) {
      console.error('Error cargando socios:', err);
    }
  }, [unidadNegocioPk]);

  const fetchKardex = useCallback(async () => {
    if (!unidadNegocioPk) return;
    setLoadingKardex(true);
    try {
      const params = new URLSearchParams({
        unidad_negocio_pk: unidadNegocioPk,
        skip: pageKardex * PAGE_SIZE,
        limit: PAGE_SIZE
      });
      if (kardexTipoFilter !== 'todos') params.append('tipo_movimiento', kardexTipoFilter);
      if (kardexFechaInicio) params.append('fecha_inicio', kardexFechaInicio);
      if (kardexFechaFin) params.append('fecha_fin', kardexFechaFin);

      const res = await api.get(`/cava-socios/kardex?${params}`);
      setKardexMovimientos(res.data?.movimientos || []);
      setKardexResumen(res.data?.resumen || null);
      setTotalKardex(res.data?.total || 0);
      setGlobalError(null);
    } catch (err) {
      console.error('Error cargando kardex:', err);
      setGlobalError('Error consultando balance Kardex');
    } finally {
      setLoadingKardex(false);
    }
  }, [unidadNegocioPk, pageKardex, kardexTipoFilter, kardexFechaInicio, kardexFechaFin]);

  const fetchHojaFisico = useCallback(async () => {
    if (!unidadNegocioPk) return;
    setLoadingFisico(true);
    try {
      const res = await api.get(`/cava-socios/inventario-fisico/hoja?unidad_negocio_pk=${encodeURIComponent(unidadNegocioPk)}`);
      const items = res.data?.hoja_conteo || [];
      setHojaFisico(items);
      
      // Inicializar conteos con el nivel teórico
      const initialMap = {};
      items.forEach(item => {
        initialMap[item.botella_id] = {
          botella_id: item.botella_id,
          nivel_fisico_pct: item.nivel_teorico_pct || 100,
          encontrada: true,
          observaciones: ''
        };
      });
      setConteosFisicos(initialMap);
      setGlobalError(null);
    } catch (err) {
      console.error('Error generando hoja física:', err);
      setGlobalError('Error generando hoja de inventario físico');
    } finally {
      setLoadingFisico(false);
    }
  }, [unidadNegocioPk]);

  useEffect(() => {
    if (filtersLoading || contextLoading || !unidadNegocioPk) return;
    if (activeTab === 'custodia') fetchCustodia();
    if (activeTab === 'inicial') fetchSociosOptions();
    if (activeTab === 'kardex') fetchKardex();
    if (activeTab === 'fisico') fetchHojaFisico();
  }, [activeTab, unidadNegocioPk, filtersLoading, contextLoading, fetchCustodia, fetchSociosOptions, fetchKardex, fetchHojaFisico]);

  // Handle Socio Inicial Change
  const handleSelectSocioInicial = async (socioId) => {
    setSelectedSocioInicial(socioId);
    if (!socioId) {
      setSocioInfoInicial(null);
      return;
    }
    try {
      const res = await api.get(`/cava-socios/socios/${socioId}?unidad_negocio_pk=${encodeURIComponent(unidadNegocioPk)}`);
      setSocioInfoInicial(res.data);
    } catch (err) {
      console.error('Error cargando detalle socio:', err);
    }
  };

  // Add/Remove Botella Item in Inicial
  const handleAddBotellaInicialRow = () => {
    setBotellasInicialList(prev => [
      ...prev,
      {
        producto_nombre: '',
        producto_codigo: '',
        marca: '',
        tipo_bebida: 'VINO_TINTO',
        añada: '',
        ubicacion: socioInfoInicial?.ubicacion_cava || '',
        valor_declarado: 0,
        puntaje_inicial_pct: 100,
        cantidad_piezas: 1,
        observaciones: 'Inventario inicial'
      }
    ]);
  };

  const handleRemoveBotellaInicialRow = (idx) => {
    if (botellasInicialList.length <= 1) return;
    setBotellasInicialList(prev => prev.filter((_, i) => i !== idx));
  };

  const handleUpdateBotellaInicialRow = (idx, field, value) => {
    setBotellasInicialList(prev => {
      const next = [...prev];
      next[idx] = { ...next[idx], [field]: value };
      return next;
    });
  };

  const handleGuardarInventarioInicial = async () => {
    if (!selectedSocioInicial) {
      setInicialError('Por favor selecciona un socio de cava.');
      return;
    }
    for (let b of botellasInicialList) {
      if (!b.producto_nombre.trim()) {
        setInicialError('Todos los registros de botella deben tener un nombre de producto.');
        return;
      }
    }

    setSavingInicial(true);
    setInicialError(null);
    try {
      const res = await api.post(`/cava-socios/inventario-inicial?unidad_negocio_pk=${encodeURIComponent(unidadNegocioPk)}`, {
        socio_id: selectedSocioInicial,
        botellas: botellasInicialList
      });
      setInicialSuccess(res.data?.mensaje || 'Inventario inicial guardado exitosamente.');
      setBotellasInicialList([
        {
          producto_nombre: '',
          producto_codigo: '',
          marca: '',
          tipo_bebida: 'VINO_TINTO',
          añada: '',
          ubicacion: '',
          valor_declarado: 0,
          puntaje_inicial_pct: 100,
          cantidad_piezas: 1,
          observaciones: 'Inventario inicial'
        }
      ]);
      fetchSociosOptions();
    } catch (err) {
      console.error('Error guardando inventario inicial:', err);
      setInicialError(err?.response?.data?.detail || 'Error registrando inventario inicial.');
    } finally {
      setSavingInicial(false);
    }
  };

  // Handle Auditoría Física
  const handleUpdateConteoItem = (botellaId, field, value) => {
    setConteosFisicos(prev => ({
      ...prev,
      [botellaId]: {
        ...prev[botellaId],
        [field]: value
      }
    }));
  };

  const handleAplicarAuditoriaFisica = async () => {
    const list = Object.values(conteosFisicos);
    if (!list.length) return;

    setSavingFisico(true);
    setFisicoSuccess(null);
    try {
      const res = await api.post(`/cava-socios/inventario-fisico/aplicar?unidad_negocio_pk=${encodeURIComponent(unidadNegocioPk)}`, {
        conteos: list,
        observaciones_generales: observacionesAuditoria
      });
      setFisicoSuccess(res.data?.mensaje || 'Ajustes físicos conciliados y aplicados al Kardex exitosamente.');
      fetchHojaFisico();
    } catch (err) {
      console.error('Error aplicando ajustes físicos:', err);
      alert(err?.response?.data?.detail || 'Error aplicando auditoría física');
    } finally {
      setSavingFisico(false);
    }
  };

  // Handlers Consumo y Etiqueta
  const handleOpenConsumo = (botella) => {
    setSelectedBotellaConsumo(botella);
    setConsumoForm({
      porcentaje_consumido: 100,
      motivo: 'Consumo en restaurante / servicio de mesa',
      monto_descorche: 350
    });
    setShowConsumoDialog(true);
  };

  const handleConfirmarConsumo = async () => {
    if (!selectedBotellaConsumo) return;
    setSavingConsumo(true);
    try {
      await api.post(`/cava-socios/botellas/${selectedBotellaConsumo.botella_id}/consumo?unidad_negocio_pk=${encodeURIComponent(unidadNegocioPk)}`, consumoForm);
      setShowConsumoDialog(false);
      fetchCustodia();
    } catch (err) {
      console.error('Error registrando consumo:', err);
      alert('Error al registrar consumo');
    } finally {
      setSavingConsumo(false);
    }
  };

  const handleVerEtiqueta = (botella) => {
    setSelectedEtiqueta(botella);
    setShowEtiquetaDialog(true);
  };

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(val || 0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('es-MX', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  };

  const filteredBotellas = botellas.filter(b => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return (
      b.producto_nombre?.toLowerCase().includes(term) ||
      b.socio_nombre?.toLowerCase().includes(term) ||
      b.numero_socio?.toLowerCase().includes(term) ||
      b.ubicacion?.toLowerCase().includes(term) ||
      b.marca?.toLowerCase().includes(term)
    );
  });

  const totalPagesCustodia = Math.ceil(totalBotellas / PAGE_SIZE);
  const totalPagesKardex = Math.ceil(totalKardex / PAGE_SIZE);

  return (
    <div className="p-6 space-y-6" data-testid="inventario-cava-page">
      {/* Shared Cava Header */}
      <CavaNavHeader
        title="Inventario, Kardex y Auditoría de Cavas"
        subtitle="Control físico de botellas en resguardo, cargas iniciales, balance Kardex y conciliaciones"
        onRefresh={() => {
          if (activeTab === 'custodia') fetchCustodia();
          if (activeTab === 'kardex') fetchKardex();
          if (activeTab === 'fisico') fetchHojaFisico();
        }}
        loading={loadingCustodia || loadingKardex || loadingFisico}
      />

      {(globalError || contextError) && (
        <div className="p-4 rounded-xl bg-red-50 text-red-700 flex items-center gap-2 border border-red-200">
          <AlertCircle className="h-5 w-5 flex-shrink-0" />
          <span>{globalError || contextError?.message || 'No se pudo resolver el contexto de acceso.'}</span>
        </div>
      )}

      {/* ========================================================================= */}
      {/* PESTAÑA 1: BOTELLAS EN CUSTODIA (PZ) */}
      {/* ========================================================================= */}
      {activeTab === 'custodia' && (
        <div className="space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="border-l-4 border-l-purple-600 shadow-sm">
              <CardContent className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase font-semibold text-muted-foreground">Botellas Activas en Resguardo</p>
                  <p className="text-3xl font-bold text-purple-700 mt-1">{totalBotellas}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">En casilleros y cavas</p>
                </div>
                <div className="p-3 bg-purple-100 rounded-xl text-purple-700">
                  <Wine className="h-7 w-7" />
                </div>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-emerald-600 shadow-sm">
              <CardContent className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase font-semibold text-muted-foreground">Valor Total en Custodia</p>
                  <p className="text-3xl font-bold text-emerald-700 mt-1">{formatCurrency(valorTotalCustodia)}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">Valor declarado acumulado</p>
                </div>
                <div className="p-3 bg-emerald-100 rounded-xl text-emerald-700">
                  <DollarSign className="h-7 w-7" />
                </div>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-blue-600 shadow-sm">
              <CardContent className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase font-semibold text-muted-foreground">Acceso Rápido Operativo</p>
                  <div className="flex gap-2 mt-2">
                    <Button size="sm" variant="outline" onClick={() => navigate('/cava-socios/inventario?tab=inicial')} className="text-xs">
                      <Plus className="h-3.5 w-3.5 mr-1 text-purple-600" /> Carga Inicial
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => navigate('/cava-socios/inventario?tab=fisico')} className="text-xs">
                      <ClipboardCheck className="h-3.5 w-3.5 mr-1 text-amber-600" /> Auditoría
                    </Button>
                  </div>
                </div>
                <div className="p-3 bg-blue-100 rounded-xl text-blue-700">
                  <Layers className="h-7 w-7" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Filtros */}
          <Card className="shadow-sm">
            <CardContent className="p-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Buscar por botella, socio o marca..."
                    className="pl-9"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
                <div>
                  <Input
                    placeholder="Filtrar por casillero / ubicación..."
                    value={ubicacionFilter}
                    onChange={(e) => setUbicacionFilter(e.target.value)}
                  />
                </div>
                <div>
                  <Select value={tipoBebidaFilter} onValueChange={setTipoBebidaFilter}>
                    <SelectTrigger>
                      <SelectValue placeholder="Tipo de Bebida" />
                    </SelectTrigger>
                    <SelectContent>
                      {TIPOS_BEBIDA.map(t => (
                        <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Select value={estatusFilter} onValueChange={setEstatusFilter}>
                    <SelectTrigger>
                      <SelectValue placeholder="Estatus" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="todos">Todos los estatus</SelectItem>
                      <SelectItem value="EN_CAVA">En Cava / Custodia</SelectItem>
                      <SelectItem value="CONSUMIDA">Consumida</SelectItem>
                      <SelectItem value="RETIRADA">Retirada por socio</SelectItem>
                      <SelectItem value="EXTRAVIADA">Extraviada</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Tabla de Botellas */}
          <Card className="shadow-sm">
            <CardHeader className="py-4 px-6 border-b">
              <CardTitle className="text-base font-bold flex items-center justify-between">
                <span>Botellas en Resguardo ({filteredBotellas.length} de {totalBotellas})</span>
                <span className="text-xs font-normal text-muted-foreground">Unidades en Piezas / Puntaje (PZ)</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {loadingCustodia ? (
                <div className="flex items-center justify-center py-16">
                  <RefreshCw className="h-8 w-8 animate-spin text-purple-600" />
                </div>
              ) : filteredBotellas.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow className="bg-zinc-50">
                      <TableHead>Botella / Producto</TableHead>
                      <TableHead>Socio Propietario</TableHead>
                      <TableHead>Tipo / Añada</TableHead>
                      <TableHead>Casillero / Ubicación</TableHead>
                      <TableHead className="text-center">Nivel (PZ)</TableHead>
                      <TableHead className="text-right">Valor Declarado</TableHead>
                      <TableHead>Estatus</TableHead>
                      <TableHead className="text-right">Acciones</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredBotellas.map((b) => (
                      <TableRow key={b.botella_id} className="hover:bg-zinc-50/80">
                        <TableCell>
                          <div className="font-semibold text-zinc-900">{b.producto_nombre}</div>
                          {b.marca && <div className="text-xs text-muted-foreground">{b.marca}</div>}
                        </TableCell>
                        <TableCell>
                          <div 
                            className="font-medium text-purple-700 hover:underline cursor-pointer flex items-center gap-1"
                            onClick={() => navigate(`/cava-socios/socios/${b.socio_id}`)}
                          >
                            <User className="h-3.5 w-3.5" />
                            {b.socio_nombre}
                          </div>
                          <div className="text-xs text-muted-foreground">#{b.numero_socio}</div>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">{b.tipo_bebida || '-'}</div>
                          {b.añada && <div className="text-xs text-muted-foreground">Añada {b.añada}</div>}
                        </TableCell>
                        <TableCell>
                          <span className="px-2.5 py-1 bg-zinc-100 rounded-md text-xs font-mono font-medium text-zinc-800">
                            {b.ubicacion || 'Sin asignar'}
                          </span>
                        </TableCell>
                        <TableCell className="text-center">
                          <div className="inline-flex flex-col items-center">
                            <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-purple-100 text-purple-800">
                              {b.nivel_actual_pz != null ? `${b.nivel_actual_pz} PZ` : `${b.nivel_actual || 100}%`}
                            </span>
                            <span className="text-[10px] text-muted-foreground mt-0.5">
                              {b.nivel_actual || 100}%
                            </span>
                          </div>
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          {formatCurrency(b.valor_declarado)}
                        </TableCell>
                        <TableCell>
                          <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                            b.estatus === 'EN_CAVA' || b.estatus === 'GUARDADA' ? 'bg-green-100 text-green-800' :
                            b.estatus === 'ABIERTA' ? 'bg-amber-100 text-amber-800' :
                            'bg-zinc-100 text-zinc-700'
                          }`}>
                            {b.estatus || 'EN_CAVA'}
                          </span>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              title="Ficha / Etiqueta QR"
                              onClick={() => handleVerEtiqueta(b)}
                              className="h-8 w-8 p-0"
                            >
                              <QrCode className="h-4 w-4 text-purple-700" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              title="Registrar Consumo"
                              onClick={() => handleOpenConsumo(b)}
                              className="h-8 w-8 p-0"
                            >
                              <Package className="h-4 w-4 text-amber-600" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              title="Ver Socio"
                              onClick={() => navigate(`/cava-socios/socios/${b.socio_id}`)}
                              className="h-8 w-8 p-0"
                            >
                              <Eye className="h-4 w-4 text-zinc-600" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-16 text-muted-foreground">
                  <Wine className="h-12 w-12 mx-auto mb-3 opacity-20" />
                  <p className="text-base font-medium">No se encontraron botellas en resguardo</p>
                  <p className="text-xs mt-1">Registra botellas mediante Carga Inicial o el Detalle del Socio</p>
                </div>
              )}

              {/* Paginación */}
              {totalPagesCustodia > 1 && (
                <div className="flex items-center justify-between p-4 border-t">
                  <div className="text-xs text-muted-foreground">
                    Mostrando {pageCustodia * PAGE_SIZE + 1} - {Math.min((pageCustodia + 1) * PAGE_SIZE, totalBotellas)} de {totalBotellas} botellas
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" disabled={pageCustodia === 0} onClick={() => setPageCustodia(p => p - 1)}>
                      <ChevronLeft className="h-4 w-4" /> Anterior
                    </Button>
                    <Button variant="outline" size="sm" disabled={pageCustodia >= totalPagesCustodia - 1} onClick={() => setPageCustodia(p => p + 1)}>
                      Siguiente <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* ========================================================================= */}
      {/* PESTAÑA 2: CARGA DE INVENTARIO INICIAL (PZ) */}
      {/* ========================================================================= */}
      {activeTab === 'inicial' && (
        <div className="space-y-6">
          <Card className="shadow-sm">
            <CardHeader className="border-b bg-zinc-50/50">
              <CardTitle className="text-lg font-bold flex items-center gap-2">
                <Plus className="h-5 w-5 text-purple-600" />
                Carga Masiva de Inventario Inicial (PZ)
              </CardTitle>
              <CardDescription>
                Registra la apertura de custodia de botellas por socio en unidades de pieza/puntaje (1.0 PZ = 100%).
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6 space-y-6">
              {inicialSuccess && (
                <div className="p-4 rounded-xl bg-green-50 text-green-800 border border-green-200 flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0" />
                  <span>{inicialSuccess}</span>
                </div>
              )}
              {inicialError && (
                <div className="p-4 rounded-xl bg-red-50 text-red-800 border border-red-200 flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0" />
                  <span>{inicialError}</span>
                </div>
              )}

              {/* Selector de Socio */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-purple-50/60 p-4 rounded-xl border border-purple-200">
                <div>
                  <Label className="font-semibold text-purple-900">Seleccionar Socio Propietario *</Label>
                  <Select value={selectedSocioInicial} onValueChange={handleSelectSocioInicial}>
                    <SelectTrigger className="bg-white mt-1">
                      <SelectValue placeholder="-- Selecciona un Socio de Cava --" />
                    </SelectTrigger>
                    <SelectContent>
                      {sociosOptions.map(s => (
                        <SelectItem key={s.socio_id} value={s.socio_id}>
                          #{s.numero_socio} • {s.nombre_completo} ({s.tipo_membresia})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {socioInfoInicial && (
                  <div className="flex flex-col justify-center text-xs text-purple-900 space-y-1">
                    <div><span className="font-bold">Membresía:</span> {socioInfoInicial.tipo_membresia} • <span className="font-bold">Capacidad Máxima:</span> {socioInfoInicial.maximo_botellas} botellas</div>
                    <div><span className="font-bold">Botellas Actuales en Cava:</span> {socioInfoInicial.botellas_actuales || 0} / {socioInfoInicial.maximo_botellas}</div>
                    <div><span className="font-bold">Casillero Asignado:</span> {socioInfoInicial.observaciones || socioInfoInicial.ubicacion_cava || 'Cava General'}</div>
                  </div>
                )}
              </div>

              {/* Grid de Botellas a Registrar */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-bold text-sm text-zinc-900">Detalle de Botellas a Ingresar (PZ)</h3>
                  <Button type="button" size="sm" variant="outline" onClick={handleAddBotellaInicialRow} className="gap-1 text-xs">
                    <Plus className="h-3.5 w-3.5" /> Agregar Otra Botella
                  </Button>
                </div>

                <div className="space-y-3">
                  {botellasInicialList.map((row, idx) => (
                    <div key={idx} className="p-4 rounded-xl border border-zinc-200 bg-white shadow-sm grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
                      <div className="md:col-span-3">
                        <Label className="text-xs">Nombre de la Botella / Vino *</Label>
                        <Input
                          placeholder="Ej: Tequila Don Julio 1942"
                          value={row.producto_nombre}
                          onChange={(e) => handleUpdateBotellaInicialRow(idx, 'producto_nombre', e.target.value)}
                          className="mt-1"
                        />
                      </div>
                      <div className="md:col-span-2">
                        <Label className="text-xs">Marca / Bodega</Label>
                        <Input
                          placeholder="Don Julio"
                          value={row.marca}
                          onChange={(e) => handleUpdateBotellaInicialRow(idx, 'marca', e.target.value)}
                          className="mt-1"
                        />
                      </div>
                      <div className="md:col-span-2">
                        <Label className="text-xs">Tipo de Bebida</Label>
                        <Select value={row.tipo_bebida} onValueChange={(v) => handleUpdateBotellaInicialRow(idx, 'tipo_bebida', v)}>
                          <SelectTrigger className="mt-1">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {TIPOS_BEBIDA.filter(t => t.value !== 'todos').map(t => (
                              <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="md:col-span-1">
                        <Label className="text-xs">Piezas</Label>
                        <Input
                          type="number"
                          min="1"
                          max="24"
                          value={row.cantidad_piezas}
                          onChange={(e) => handleUpdateBotellaInicialRow(idx, 'cantidad_piezas', parseInt(e.target.value) || 1)}
                          className="mt-1"
                        />
                      </div>
                      <div className="md:col-span-2">
                        <Label className="text-xs">Puntaje / Nivel (%)</Label>
                        <Input
                          type="number"
                          min="1"
                          max="100"
                          value={row.puntaje_inicial_pct}
                          onChange={(e) => handleUpdateBotellaInicialRow(idx, 'puntaje_inicial_pct', parseFloat(e.target.value) || 100)}
                          className="mt-1"
                        />
                      </div>
                      <div className="md:col-span-1">
                        <Label className="text-xs">Valor ($)</Label>
                        <Input
                          type="number"
                          min="0"
                          value={row.valor_declarado}
                          onChange={(e) => handleUpdateBotellaInicialRow(idx, 'valor_declarado', parseFloat(e.target.value) || 0)}
                          className="mt-1"
                        />
                      </div>
                      <div className="md:col-span-1 flex justify-end">
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          disabled={botellasInicialList.length <= 1}
                          onClick={() => handleRemoveBotellaInicialRow(idx)}
                          className="text-red-500 hover:text-red-700"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between pt-4 border-t">
                <div className="text-xs text-muted-foreground">
                  Total a ingresar: {botellasInicialList.reduce((acc, r) => acc + (parseInt(r.cantidad_piezas) || 1), 0)} botellas en PZ
                </div>
                <Button onClick={handleGuardarInventarioInicial} disabled={savingInicial} className="bg-purple-700 hover:bg-purple-800 text-white gap-2">
                  <Save className="h-4 w-4" />
                  {savingInicial ? 'Guardando Inventario...' : 'Guardar Inventario Inicial'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* ========================================================================= */}
      {/* PESTAÑA 3: KARDEX CANÓNICO DE CAVAS (PZ) */}
      {/* ========================================================================= */}
      {activeTab === 'kardex' && (
        <div className="space-y-6">
          {/* Ecuación de Balance Canónico */}
          <Card className="border-2 border-purple-200 bg-gradient-to-r from-purple-50 via-white to-purple-50 shadow-sm">
            <CardHeader className="pb-2">
              <CardTitle className="text-base font-bold text-purple-900 flex items-center gap-2">
                <ArrowRightLeft className="h-5 w-5 text-purple-700" />
                Ecuación Canónica de Balance Kardex (PZ)
              </CardTitle>
              <CardDescription className="text-xs text-purple-700">
                Stock Teórico (PZ) = Inv. Inicial + Entradas − Consumos ± Ajustes Físicos
              </CardDescription>
            </CardHeader>
            <CardContent className="p-4">
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-center">
                <div className="p-3 bg-white rounded-lg border border-purple-100 shadow-xs">
                  <span className="text-[11px] font-semibold text-zinc-500 block">Inv. Inicial</span>
                  <span className="text-xl font-bold text-zinc-800">{kardexResumen?.inv_inicial_pz || 0} PZ</span>
                </div>
                <div className="p-3 bg-white rounded-lg border border-purple-100 shadow-xs">
                  <span className="text-[11px] font-semibold text-green-600 block">(+) Entradas</span>
                  <span className="text-xl font-bold text-green-700">{kardexResumen?.entradas_pz || 0} PZ</span>
                </div>
                <div className="p-3 bg-white rounded-lg border border-purple-100 shadow-xs">
                  <span className="text-[11px] font-semibold text-amber-600 block">(−) Consumos</span>
                  <span className="text-xl font-bold text-amber-700">{kardexResumen?.consumos_pz || 0} PZ</span>
                </div>
                <div className="p-3 bg-white rounded-lg border border-purple-100 shadow-xs">
                  <span className="text-[11px] font-semibold text-blue-600 block">(±) Ajustes Físicos</span>
                  <span className="text-xl font-bold text-blue-700">{kardexResumen?.ajustes_pz || 0} PZ</span>
                </div>
                <div className="p-3 bg-purple-700 text-white rounded-lg shadow-sm">
                  <span className="text-[11px] font-semibold text-purple-200 block">(=) Stock Teórico</span>
                  <span className="text-xl font-bold">{kardexResumen?.stock_teorico_pz || 0} PZ</span>
                </div>
                <div className="p-3 bg-emerald-700 text-white rounded-lg shadow-sm">
                  <span className="text-[11px] font-semibold text-emerald-200 block">Stock Real Activo</span>
                  <span className="text-xl font-bold">{kardexResumen?.stock_real_pz || 0} PZ</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Filtros Kardex */}
          <Card className="shadow-sm">
            <CardContent className="p-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
                <div>
                  <Label className="text-xs mb-1 block">Tipo de Movimiento</Label>
                  <Select value={kardexTipoFilter} onValueChange={setKardexTipoFilter}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {TIPOS_MOVIMIENTO_KARDEX.map(t => (
                        <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-xs mb-1 block">Fecha Desde</Label>
                  <Input type="date" value={kardexFechaInicio} onChange={(e) => setKardexFechaInicio(e.target.value)} />
                </div>
                <div>
                  <Label className="text-xs mb-1 block">Fecha Hasta</Label>
                  <Input type="date" value={kardexFechaFin} onChange={(e) => setKardexFechaFin(e.target.value)} />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Tabla de Movimientos del Kardex */}
          <Card className="shadow-sm">
            <CardHeader className="py-4 px-6 border-b">
              <CardTitle className="text-base font-bold flex items-center justify-between">
                <span>Bitácora General de Movimientos Kardex ({totalKardex})</span>
                <span className="text-xs text-muted-foreground font-normal">Trazabilidad completa en PZ</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {loadingKardex ? (
                <div className="flex items-center justify-center py-16">
                  <RefreshCw className="h-8 w-8 animate-spin text-purple-600" />
                </div>
              ) : kardexMovimientos.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow className="bg-zinc-50">
                      <TableHead>Fecha / Hora</TableHead>
                      <TableHead>Tipo Movimiento</TableHead>
                      <TableHead>Socio</TableHead>
                      <TableHead>Botella / Producto</TableHead>
                      <TableHead className="text-center">Nivel Ant. (PZ)</TableHead>
                      <TableHead className="text-center">Nivel Nuevo (PZ)</TableHead>
                      <TableHead className="text-center">Movimiento (PZ)</TableHead>
                      <TableHead className="text-right">Descorche ($)</TableHead>
                      <TableHead>Motivo / Observaciones</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {kardexMovimientos.map((m) => (
                      <TableRow key={m.movimiento_id} className="hover:bg-zinc-50/80">
                        <TableCell className="font-mono text-xs text-zinc-600">
                          {formatDate(m.fecha)}
                        </TableCell>
                        <TableCell>
                          <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                            m.tipo_movimiento === 'INVENTARIO_INICIAL' ? 'bg-blue-100 text-blue-800' :
                            m.tipo_movimiento === 'ENTRADA' ? 'bg-green-100 text-green-800' :
                            m.tipo_movimiento.startsWith('CONSUMO') ? 'bg-amber-100 text-amber-800' :
                            m.tipo_movimiento.startsWith('AJUSTE') ? 'bg-purple-100 text-purple-800' :
                            'bg-zinc-100 text-zinc-700'
                          }`}>
                            {m.tipo_movimiento}
                          </span>
                        </TableCell>
                        <TableCell className="font-medium text-zinc-800">
                          {m.socio_nombre} <span className="text-xs text-muted-foreground">#{m.numero_socio}</span>
                        </TableCell>
                        <TableCell className="text-zinc-900 font-medium">
                          {m.producto_nombre}
                        </TableCell>
                        <TableCell className="text-center font-mono text-xs text-zinc-600">
                          {m.nivel_anterior_pz} PZ ({m.nivel_anterior_pct}%)
                        </TableCell>
                        <TableCell className="text-center font-mono text-xs font-semibold text-purple-700">
                          {m.nivel_nuevo_pz} PZ ({m.nivel_nuevo_pct}%)
                        </TableCell>
                        <TableCell className="text-center font-mono text-xs font-bold text-zinc-800">
                          {m.cantidad_consumida_pz ? `-${m.cantidad_consumida_pz} PZ` : '0 PZ'}
                        </TableCell>
                        <TableCell className="text-right font-semibold text-zinc-800">
                          {m.monto_descorche ? formatCurrency(m.monto_descorche) : '-'}
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground max-w-[200px] truncate" title={m.motivo || m.observaciones}>
                          {m.motivo || m.observaciones || '-'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-16 text-muted-foreground">
                  <ArrowRightLeft className="h-12 w-12 mx-auto mb-3 opacity-20" />
                  <p className="text-base font-medium">No se encontraron movimientos de Kardex</p>
                </div>
              )}

              {/* Paginación */}
              {totalPagesKardex > 1 && (
                <div className="flex items-center justify-between p-4 border-t">
                  <div className="text-xs text-muted-foreground">
                    Mostrando {pageKardex * PAGE_SIZE + 1} - {Math.min((pageKardex + 1) * PAGE_SIZE, totalKardex)} de {totalKardex} movimientos
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" disabled={pageKardex === 0} onClick={() => setPageKardex(p => p - 1)}>
                      <ChevronLeft className="h-4 w-4" /> Anterior
                    </Button>
                    <Button variant="outline" size="sm" disabled={pageKardex >= totalPagesKardex - 1} onClick={() => setPageKardex(p => p + 1)}>
                      Siguiente <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* ========================================================================= */}
      {/* PESTAÑA 4: AUDITORÍA E INVENTARIO FÍSICO VS TEÓRICO */}
      {/* ========================================================================= */}
      {activeTab === 'fisico' && (
        <div className="space-y-6">
          <Card className="shadow-sm">
            <CardHeader className="border-b bg-zinc-50/50">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <CardTitle className="text-lg font-bold flex items-center gap-2">
                    <ClipboardCheck className="h-5 w-5 text-amber-600" />
                    Auditoría e Inventario Físico de Cavas
                  </CardTitle>
                  <CardDescription>
                    Compara el conteo físico real en casillero contra el stock teórico esperado y genera ajustes automáticos al Kardex.
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={() => window.print()} className="gap-1.5">
                    <Printer className="h-4 w-4" /> Imprimir Hoja de Conteo
                  </Button>
                  <Button size="sm" onClick={handleAplicarAuditoriaFisica} disabled={savingFisico || !hojaFisico.length} className="bg-amber-600 hover:bg-amber-700 text-white gap-1.5">
                    <Save className="h-4 w-4" />
                    {savingFisico ? 'Conciliando...' : 'Conciliar y Aplicar Ajustes'}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-6 space-y-6">
              {fisicoSuccess && (
                <div className="p-4 rounded-xl bg-green-50 text-green-800 border border-green-200 flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0" />
                  <span>{fisicoSuccess}</span>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label className="text-xs">Observaciones Generales de la Auditoría</Label>
                  <Input
                    value={observacionesAuditoria}
                    onChange={(e) => setObservacionesAuditoria(e.target.value)}
                    placeholder="Ej: Auditoría quincenal con sommelier y capitán de meseros"
                    className="mt-1"
                  />
                </div>
                <div className="flex items-center justify-end text-xs text-muted-foreground">
                  <span>Total botellas a auditar: <strong>{hojaFisico.length}</strong></span>
                </div>
              </div>

              {/* Grid / Tabla de Auditoría Física */}
              {loadingFisico ? (
                <div className="flex items-center justify-center py-16">
                  <RefreshCw className="h-8 w-8 animate-spin text-amber-600" />
                </div>
              ) : hojaFisico.length > 0 ? (
                <div className="border rounded-xl overflow-hidden shadow-sm">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-zinc-50">
                        <TableHead>Casillero / Ubicación</TableHead>
                        <TableHead>Socio Propietario</TableHead>
                        <TableHead>Botella / Producto</TableHead>
                        <TableHead className="text-center">Nivel Teórico Esperado</TableHead>
                        <TableHead className="text-center w-[160px]">Nivel Físico Real (%)</TableHead>
                        <TableHead className="text-center">Discrepancia (PZ)</TableHead>
                        <TableHead className="text-center">Encontrada</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {hojaFisico.map((row) => {
                        const conteo = conteosFisicos[row.botella_id] || {};
                        const nivelFisico = conteo.encontrada ? (parseFloat(conteo.nivel_fisico_pct) || 0) : 0;
                        const nivelTeorico = parseFloat(row.nivel_teorico_pct) || 100;
                        const diffPct = nivelFisico - nivelTeorico;
                        const diffPz = (diffPct / 100.0).toFixed(2);

                        return (
                          <TableRow key={row.botella_id} className="hover:bg-zinc-50/80">
                            <TableCell className="font-mono text-xs font-bold text-zinc-900">
                              {row.ubicacion || 'Sin asignar'}
                            </TableCell>
                            <TableCell>
                              <div className="font-medium text-zinc-900">{row.socio_nombre}</div>
                              <div className="text-xs text-muted-foreground">#{row.numero_socio}</div>
                            </TableCell>
                            <TableCell className="font-medium text-zinc-900">
                              {row.producto_nombre}
                            </TableCell>
                            <TableCell className="text-center font-mono text-xs">
                              <span className="px-2 py-0.5 rounded bg-zinc-100 text-zinc-800 font-semibold">
                                {row.nivel_teorico_pz} PZ ({row.nivel_teorico_pct}%)
                              </span>
                            </TableCell>
                            <TableCell className="text-center">
                              <Input
                                type="number"
                                min="0"
                                max="100"
                                step="5"
                                value={conteo.nivel_fisico_pct ?? 100}
                                disabled={!conteo.encontrada}
                                onChange={(e) => handleUpdateConteoItem(row.botella_id, 'nivel_fisico_pct', parseFloat(e.target.value) || 0)}
                                className="h-8 text-center font-bold text-sm w-24 mx-auto"
                              />
                            </TableCell>
                            <TableCell className="text-center">
                              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                                diffPct === 0 ? 'bg-green-100 text-green-800' :
                                diffPct > 0 ? 'bg-blue-100 text-blue-800' :
                                'bg-red-100 text-red-800'
                              }`}>
                                {diffPct > 0 ? `+${diffPz} PZ` : `${diffPz} PZ`}
                              </span>
                            </TableCell>
                            <TableCell className="text-center">
                              <input
                                type="checkbox"
                                checked={conteo.encontrada !== false}
                                onChange={(e) => handleUpdateConteoItem(row.botella_id, 'encontrada', e.target.checked)}
                                className="h-4 w-4 text-purple-600 rounded"
                              />
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="text-center py-16 text-muted-foreground">
                  <ClipboardCheck className="h-12 w-12 mx-auto mb-3 opacity-20" />
                  <p className="text-base font-medium">No hay botellas en resguardo para auditar</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL ETIQUETA QR */}
      {/* ========================================================================= */}
      <Dialog open={showEtiquetaDialog} onOpenChange={setShowEtiquetaDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <QrCode className="h-5 w-5 text-purple-600" />
              Etiqueta de Resguardo / QR Cava
            </DialogTitle>
            <DialogDescription>
              Ficha para identificación física de la botella en el casillero
            </DialogDescription>
          </DialogHeader>
          {selectedEtiqueta && (
            <div className="border-2 border-dashed border-zinc-300 p-6 rounded-xl bg-zinc-50 space-y-4 text-center">
              <div className="text-xs uppercase font-bold tracking-wider text-purple-800">
                EDARSA HUB • CONTROL DE CAVA
              </div>
              <div className="font-bold text-lg text-zinc-900">
                {selectedEtiqueta.producto_nombre}
              </div>
              <div className="text-sm text-zinc-600">
                {selectedEtiqueta.marca} {selectedEtiqueta.añada ? `• Añada ${selectedEtiqueta.añada}` : ''}
              </div>
              <div className="inline-block p-4 bg-white rounded-xl shadow-sm border border-zinc-200">
                <div className="w-32 h-32 flex flex-col items-center justify-center bg-zinc-900 text-white rounded-lg font-mono text-[10px] p-2 leading-tight">
                  <QrCode className="h-16 w-16 mb-1 text-white" />
                  <span>ID: {selectedEtiqueta.botella_id?.slice(0, 8)}</span>
                  <span>SOCIO: #{selectedEtiqueta.numero_socio}</span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-left text-xs pt-2 border-t">
                <div>
                  <span className="text-zinc-500">Socio:</span>
                  <p className="font-semibold text-zinc-800">{selectedEtiqueta.socio_nombre}</p>
                </div>
                <div>
                  <span className="text-zinc-500">Casillero / Ubicación:</span>
                  <p className="font-semibold text-zinc-800">{selectedEtiqueta.ubicacion || 'Sin asignar'}</p>
                </div>
                <div>
                  <span className="text-zinc-500">Nivel Actual:</span>
                  <p className="font-semibold text-purple-700">{selectedEtiqueta.nivel_actual_pz != null ? `${selectedEtiqueta.nivel_actual_pz} PZ` : `${selectedEtiqueta.nivel_actual || 100}%`}</p>
                </div>
                <div>
                  <span className="text-zinc-500">Valor Declarado:</span>
                  <p className="font-semibold text-zinc-800">{formatCurrency(selectedEtiqueta.valor_declarado)}</p>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEtiquetaDialog(false)}>Cerrar</Button>
            <Button onClick={() => window.print()} className="bg-purple-700 hover:bg-purple-800 text-white">
              <Printer className="h-4 w-4 mr-2" /> Imprimir Etiqueta
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ========================================================================= */}
      {/* MODAL CONSUMO RÁPIDO */}
      {/* ========================================================================= */}
      <Dialog open={showConsumoDialog} onOpenChange={setShowConsumoDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Registrar Consumo de Botella</DialogTitle>
            <DialogDescription>
              {selectedBotellaConsumo?.producto_nombre} • Socio: {selectedBotellaConsumo?.socio_nombre}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Porcentaje / Puntaje a Consumir</Label>
              <Select 
                value={String(consumoForm.porcentaje_consumido)}
                onValueChange={(v) => setConsumoForm(f => ({...f, porcentaje_consumido: parseInt(v)}))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="25">25% (0.25 PZ - Copa / Degustación)</SelectItem>
                  <SelectItem value="50">50% (0.50 PZ - Media Botella)</SelectItem>
                  <SelectItem value="75">75% (0.75 PZ - Tres Cuartos)</SelectItem>
                  <SelectItem value="100">100% (1.00 PZ - Botella Completa)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Motivo / Ocasión</Label>
              <Input
                value={consumoForm.motivo}
                onChange={(e) => setConsumoForm(f => ({...f, motivo: e.target.value}))}
                placeholder="Consumo en mesa, evento privado..."
              />
            </div>
            <div className="space-y-2">
              <Label>Cargo de Descorche ($ MXN)</Label>
              <Input
                type="number"
                value={consumoForm.monto_descorche}
                onChange={(e) => setConsumoForm(f => ({...f, monto_descorche: parseFloat(e.target.value) || 0}))}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConsumoDialog(false)}>Cancelar</Button>
            <Button onClick={handleConfirmarConsumo} disabled={savingConsumo} className="bg-purple-700 hover:bg-purple-800 text-white">
              {savingConsumo ? 'Guardando...' : 'Confirmar Consumo (PZ)'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default function InventarioCava() {
  return (
    <CorporateFiltersProvider scope="cava_socios">
      <InventarioCavaContent />
    </CorporateFiltersProvider>
  );
}
