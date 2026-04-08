import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Checkbox } from '../components/ui/checkbox';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { 
  Loader2, TrendingUp, TrendingDown, RefreshCw, Building2, Users, Receipt, 
  DollarSign, ArrowLeft, ChevronRight, Target, Clock, Utensils, X,
  BarChart3, Wallet, UserCircle, Award, ChevronDown
} from 'lucide-react';
import { formatNombreSucursal } from '../lib/formatSucursal';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Constantes para meses y años (homologado con Dashboard Comercial)
const MESES = [
  { value: '01', label: 'Enero' },
  { value: '02', label: 'Febrero' },
  { value: '03', label: 'Marzo' },
  { value: '04', label: 'Abril' },
  { value: '05', label: 'Mayo' },
  { value: '06', label: 'Junio' },
  { value: '07', label: 'Julio' },
  { value: '08', label: 'Agosto' },
  { value: '09', label: 'Septiembre' },
  { value: '10', label: 'Octubre' },
  { value: '11', label: 'Noviembre' },
  { value: '12', label: 'Diciembre' }
];

const getAniosDisponibles = () => {
  const currentYear = new Date().getFullYear();
  const years = [
    { value: '-1', label: '📊 Ventas del Día' }
  ];
  for (let y = currentYear; y >= currentYear - 3; y--) {
    years.push({ value: y.toString(), label: y.toString() });
  }
  return years;
};

const formatCurrency = (num) => {
  if (num === null || num === undefined) return '-';
  if (num >= 1000000) return `$${(num/1000000).toFixed(2)}M`;
  if (num >= 1000) return `$${(num/1000).toFixed(2)}K`;
  return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 0 }).format(num);
};

const formatPercent = (num) => {
  if (num === null || num === undefined) return '0%';
  if (num === 0) return '0%';
  const prefix = num > 0 ? '+' : '';
  return `${prefix}${num.toFixed(1)}%`;
};

const VariacionBadge = ({ valor, size = 'sm' }) => {
  if (valor === 0 || valor === null || valor === undefined) return <span className="text-zinc-400">-</span>;
  const isPositive = valor > 0;
  const sizeClass = size === 'lg' ? 'text-lg font-bold' : 'text-sm font-semibold';
  return (
    <span className={`inline-flex items-center gap-1 ${sizeClass} ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
      {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
      {formatPercent(valor)}
    </span>
  );
};

// Función para formatear fecha de última actualización
const formatLastUpdate = (isoDate) => {
  if (!isoDate) return '';
  try {
    const date = new Date(isoDate);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    
    if (diffMins < 1) return 'hace un momento';
    if (diffMins < 60) return `hace ${diffMins} min`;
    if (diffHours < 24) return `hace ${diffHours}h`;
    
    return date.toLocaleDateString('es-MX', { 
      day: '2-digit', 
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return '';
  }
};

// Tarjeta de Unidad clickeable
const UnidadCard = ({ unidad, onClick }) => {
  const isPositive = unidad.var_vs_mes_ant >= 0;
  const isOnline = unidad.status === 'online';
  const isOffline = unidad.status === 'offline';
  
  return (
    <Card 
      className={`cursor-pointer transition-all duration-200 hover:shadow-lg hover:scale-[1.02] border-2 ${
        isPositive ? 'hover:border-green-400' : 'hover:border-red-400'
      } ${isOffline ? 'bg-zinc-50' : ''}`}
      onClick={() => onClick(unidad)}
      data-testid={`unidad-card-${unidad.server_id}`}
    >
      <CardContent className="p-4">
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center gap-2">
            {/* Indicador de estado */}
            {isOnline ? (
              <span className="h-2.5 w-2.5 rounded-full bg-green-500" title="Online - Datos actualizados" />
            ) : isOffline ? (
              <span className="h-2.5 w-2.5 rounded-full bg-red-500 animate-pulse" title={`Offline - Última sync: ${formatLastUpdate(unidad.updated_at)}`} />
            ) : (
              <span className="h-2.5 w-2.5 rounded-full bg-zinc-300" title="Sin verificar" />
            )}
            <h3 className="font-bold text-zinc-800 text-sm truncate max-w-[160px]">{formatNombreSucursal(unidad.unidad)}</h3>
          </div>
          <ChevronRight className="h-4 w-4 text-zinc-400" />
        </div>
        
        {/* Indicador de última actualización si está offline */}
        {isOffline && (
          <div className="mb-2 px-2 py-1 bg-red-100 rounded text-xs text-red-700 flex items-center gap-1">
            <span className="font-medium">Offline</span>
            <span>• {formatLastUpdate(unidad.updated_at)}</span>
          </div>
        )}
        
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-xs text-zinc-500">Ventas</span>
            <span className="font-bold text-green-600">{formatCurrency(unidad.ventas)}</span>
          </div>
          
          <div className="flex justify-between items-center">
            <span className="text-xs text-zinc-500">vs Mes Ant</span>
            <VariacionBadge valor={unidad.var_vs_mes_ant} />
          </div>
          
          <div className="flex justify-between items-center">
            <span className="text-xs text-zinc-500">vs Año Ant</span>
            <VariacionBadge valor={unidad.var_vs_año_ant} />
          </div>
          
          <div className="border-t pt-2 mt-2 grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-zinc-500">PAX</span>
              <p className="font-semibold">{unidad.pax?.toLocaleString()}</p>
            </div>
            <div>
              <span className="text-zinc-500">Cheques</span>
              <p className="font-semibold">{unidad.cheques?.toLocaleString()}</p>
            </div>
            <div>
              <span className="text-zinc-500">Ticket</span>
              <p className="font-semibold">{formatCurrency(unidad.ticket_prom)}</p>
            </div>
            <div>
              <span className="text-zinc-500">Proyección</span>
              <p className="font-semibold text-orange-600">{formatCurrency(unidad.proyeccion)}</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Detalle de Unidad (Drill-down)
const DetalleUnidad = ({ unidad, onClose, mes, anio }) => {
  const [detalleData, setDetalleData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const cargarDetalle = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem('token');
        const headers = { Authorization: `Bearer ${token}` };
        
        // Parámetros con sucursal (si existe)
        const params = unidad.sucursal ? `?sucursal=${encodeURIComponent(unidad.sucursal)}` : '';
        const periodParams = unidad.sucursal ? `?periodo=mes&sucursal=${encodeURIComponent(unidad.sucursal)}` : '?periodo=mes';
        
        // Cargar datos adicionales de la unidad
        const [dashboard, ventasTiempo, mesas] = await Promise.all([
          axios.get(`${API_URL}/api/comercial/dashboard/${unidad.server_id}${periodParams}`, { headers }),
          axios.get(`${API_URL}/api/comercial/ventas-tiempo/${unidad.server_id}${params}`, { headers }),
          axios.get(`${API_URL}/api/comercial/mesas/${unidad.server_id}${params}`, { headers })
        ]);
        
        setDetalleData({
          dashboard: dashboard.data,
          ventasTiempo: ventasTiempo.data,
          mesas: mesas.data
        });
      } catch (error) {
        console.error('Error cargando detalle:', error);
        toast.error('Error al cargar detalle de unidad');
      } finally {
        setLoading(false);
      }
    };
    
    if (unidad?.server_id) {
      cargarDetalle();
    }
  }, [unidad]);

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            {formatNombreSucursal(unidad.unidad)}
          </DialogTitle>
        </DialogHeader>
        
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
          </div>
        ) : (
          <div className="space-y-4">
            {/* KPIs principales */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <Card className="bg-green-50 border-green-200">
                <CardContent className="p-3 text-center">
                  <div className="flex items-center justify-center gap-2 mb-1">
                    <DollarSign className="h-4 w-4 text-green-600" />
                    <span className="text-xs text-zinc-600">Ventas</span>
                  </div>
                  <p className="text-xl font-bold text-green-600">{formatCurrency(unidad.ventas)}</p>
                  <div className="flex justify-center gap-2 mt-1">
                    <span className="text-xs">Mes: <VariacionBadge valor={unidad.var_vs_mes_ant} /></span>
                    <span className="text-xs">Año: <VariacionBadge valor={unidad.var_vs_año_ant} /></span>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="bg-blue-50 border-blue-200">
                <CardContent className="p-3 text-center">
                  <div className="flex items-center justify-center gap-2 mb-1">
                    <Users className="h-4 w-4 text-blue-600" />
                    <span className="text-xs text-zinc-600">PAX</span>
                  </div>
                  <p className="text-xl font-bold text-blue-600">{unidad.pax?.toLocaleString()}</p>
                  <p className="text-xs text-zinc-500">Ticket: {formatCurrency(unidad.ticket_prom)}</p>
                  <div className="flex justify-center gap-2 mt-1">
                    <span className="text-xs">Mes: <VariacionBadge valor={unidad.pax_ant > 0 ? ((unidad.pax - unidad.pax_ant) / unidad.pax_ant * 100) : 0} /></span>
                    <span className="text-xs">Año: <VariacionBadge valor={unidad.pax_año > 0 ? ((unidad.pax - unidad.pax_año) / unidad.pax_año * 100) : 0} /></span>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="bg-purple-50 border-purple-200">
                <CardContent className="p-3 text-center">
                  <div className="flex items-center justify-center gap-2 mb-1">
                    <Receipt className="h-4 w-4 text-purple-600" />
                    <span className="text-xs text-zinc-600">Cheques</span>
                  </div>
                  <p className="text-xl font-bold text-purple-600">{unidad.cheques?.toLocaleString()}</p>
                  <p className="text-xs text-zinc-500">Promedio: {formatCurrency(unidad.cheque_prom)}</p>
                  <div className="flex justify-center gap-2 mt-1">
                    <span className="text-xs">Mes: <VariacionBadge valor={unidad.cheques_ant > 0 ? ((unidad.cheques - unidad.cheques_ant) / unidad.cheques_ant * 100) : 0} /></span>
                    <span className="text-xs">Año: <VariacionBadge valor={unidad.cheques_año > 0 ? ((unidad.cheques - unidad.cheques_año) / unidad.cheques_año * 100) : 0} /></span>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="bg-orange-50 border-orange-200">
                <CardContent className="p-3 text-center">
                  <div className="flex items-center justify-center gap-2 mb-1">
                    <Target className="h-4 w-4 text-orange-600" />
                    <span className="text-xs text-zinc-600">Proyección</span>
                  </div>
                  <p className="text-xl font-bold text-orange-600">{formatCurrency(unidad.proyeccion)}</p>
                  <p className="text-xs text-zinc-500">Mes completo</p>
                  <div className="flex justify-center gap-2 mt-1">
                    <span className="text-xs">vs Mes: <VariacionBadge valor={unidad.ventas_ant > 0 ? ((unidad.proyeccion - unidad.ventas_ant) / unidad.ventas_ant * 100) : 0} /></span>
                    <span className="text-xs">vs Año: <VariacionBadge valor={unidad.ventas_año > 0 ? ((unidad.proyeccion - unidad.ventas_año) / unidad.ventas_año * 100) : 0} /></span>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Comparativo */}
            <Card>
              <CardHeader className="py-2 bg-zinc-100">
                <CardTitle className="text-sm">Comparativo</CardTitle>
              </CardHeader>
              <CardContent className="p-3">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <p className="text-xs text-zinc-500">Mes Actual</p>
                    <p className="font-bold text-lg">{formatCurrency(unidad.ventas)}</p>
                    <p className="text-xs text-purple-600">{unidad.pax || 0} pax</p>
                    <p className="text-xs">{unidad.cheques} cheques</p>
                  </div>
                  <div>
                    <p className="text-xs text-zinc-500">Mes Anterior</p>
                    <p className="font-bold text-lg">{formatCurrency(unidad.ventas_ant)}</p>
                    <p className="text-xs text-purple-600">{unidad.pax_ant || 0} pax</p>
                    <p className="text-xs">{unidad.cheques_ant} cheques</p>
                  </div>
                  <div>
                    <p className="text-xs text-zinc-500">Año Anterior</p>
                    <p className="font-bold text-lg">{formatCurrency(unidad.ventas_año)}</p>
                    <p className="text-xs text-purple-600">{unidad.pax_año || 0} pax</p>
                    <p className="text-xs">{unidad.cheques_año} cheques</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Ventas por Hora */}
            {detalleData?.ventasTiempo?.por_hora?.length > 0 && (
              <Card>
                <CardHeader className="py-2 bg-zinc-100">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    Ventas por Hora (Top 6)
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-3">
                  <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
                    {detalleData.ventasTiempo.por_hora.slice(0, 6).map((h, i) => (
                      <div key={i} className="text-center p-2 bg-zinc-50 rounded">
                        <p className="font-bold text-sm">{h.hora}</p>
                        <p className="text-xs text-green-600">{formatCurrency(h.ventas)}</p>
                        <p className="text-xs text-zinc-500">{h.pax} pax</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Ventas por Día */}
            {detalleData?.ventasTiempo?.por_dia?.length > 0 && (
              <Card>
                <CardHeader className="py-2 bg-zinc-100">
                  <CardTitle className="text-sm">Ventas por Día de Semana</CardTitle>
                </CardHeader>
                <CardContent className="p-3">
                  <div className="grid grid-cols-7 gap-1">
                    {(() => {
                      // Asegurar que siempre tengamos los 7 días de la semana (Lunes a Domingo)
                      const diasSemana = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];
                      const diasMap = {};
                      detalleData.ventasTiempo.por_dia.forEach(d => {
                        const diaKey = d.dia.substring(0, 3);
                        diasMap[diaKey] = d;
                      });
                      
                      const diasCompletos = diasSemana.map(dia => ({
                        dia: dia,
                        ventas: diasMap[dia]?.ventas || 0,
                        pax: diasMap[dia]?.pax || 0
                      }));
                      
                      const maxVenta = Math.max(...diasCompletos.map(x => x.ventas), 1);
                      
                      return diasCompletos.map((d, i) => {
                        const height = (d.ventas / maxVenta * 60) + 20;
                        return (
                          <div key={i} className="text-center">
                            <div 
                              className={`rounded-t mx-auto w-8 transition-all ${d.ventas > 0 ? 'bg-blue-500' : 'bg-zinc-200'}`}
                              style={{ height: `${height}px` }}
                            />
                            <p className="text-xs font-medium mt-1">{d.dia}</p>
                            <p className="text-xs text-zinc-500">{formatCurrency(d.ventas)}</p>
                          </div>
                        );
                      });
                    })()}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default function TableroEjecutivo() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  
  // Estados para filtros multiselección (homologado con Dashboard Comercial)
  const [selectedMeses, setSelectedMeses] = useState(() => {
    const saved = localStorage.getItem('tablero_filtros_v2');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return parsed.selectedMeses || [String(new Date().getMonth() + 1).padStart(2, '0')];
      } catch (e) { return [String(new Date().getMonth() + 1).padStart(2, '0')]; }
    }
    return [String(new Date().getMonth() + 1).padStart(2, '0')];
  });
  
  const [selectedAnios, setSelectedAnios] = useState(() => {
    const saved = localStorage.getItem('tablero_filtros_v2');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return parsed.selectedAnios || [new Date().getFullYear().toString()];
      } catch (e) { return [new Date().getFullYear().toString()]; }
    }
    return [new Date().getFullYear().toString()];
  });
  
  const [tipoComparacion, setTipoComparacion] = useState('dias_equiv');
  const [showMesesDropdown, setShowMesesDropdown] = useState(false);
  const [showAniosDropdown, setShowAniosDropdown] = useState(false);
  
  const ANIOS = getAniosDisponibles();
  
  const [unidadSeleccionada, setUnidadSeleccionada] = useState(null);

  // Guardar filtros cuando cambien
  useEffect(() => {
    localStorage.setItem('tablero_filtros_v2', JSON.stringify({ selectedMeses, selectedAnios, tipoComparacion }));
  }, [selectedMeses, selectedAnios, tipoComparacion]);

  // Funciones para toggle de selección
  const toggleMes = (mesValue) => {
    if (selectedMeses.includes(mesValue)) {
      if (selectedMeses.length > 1) {
        setSelectedMeses(selectedMeses.filter(m => m !== mesValue));
      }
    } else {
      setSelectedMeses([...selectedMeses, mesValue].sort());
    }
  };

  const toggleAnio = (anioValue) => {
    // Si es "Ventas del Día", selección exclusiva
    if (anioValue === '-1') {
      setSelectedAnios(['-1']);
      return;
    }
    // Si ya está en "Ventas del Día" y selecciona otro año, quitar -1
    if (selectedAnios.includes('-1')) {
      setSelectedAnios([anioValue]);
      return;
    }
    if (selectedAnios.includes(anioValue)) {
      if (selectedAnios.length > 1) {
        setSelectedAnios(selectedAnios.filter(a => a !== anioValue));
      }
    } else {
      setSelectedAnios([...selectedAnios, anioValue].sort().reverse());
    }
  };

  // Labels para los dropdowns
  const getMesesLabel = () => {
    if (selectedMeses.length === 0) return 'Seleccionar';
    if (selectedMeses.length === 1) {
      return MESES.find(m => m.value === selectedMeses[0])?.label || 'Mes';
    }
    if (selectedMeses.length === 12) return 'Todo el año';
    return `${selectedMeses.length} meses`;
  };

  const getAniosLabel = () => {
    if (selectedAnios.includes('-1')) return '📊 Ventas del Día';
    if (selectedAnios.length === 0) return 'Seleccionar';
    if (selectedAnios.length === 1) {
      return selectedAnios[0];
    }
    return `${selectedAnios.length} años`;
  };

  // Detectar si es modo "Ventas del Día"
  const esVentasDelDia = selectedAnios.includes('-1');

  const cargarDatos = async (retry = 0) => {
    const token = localStorage.getItem('token');
    if (!token) {
      window.location.href = '/login';
      return;
    }
    
    if (retry === 0) setLoading(true);
    
    try {
      const response = await axios.get(`${API_URL}/api/comercial/tablero-ejecutivo`, {
        params: { 
          meses: selectedMeses.join(','),
          anios: selectedAnios.join(','),
          tipo_comparacion: tipoComparacion
        },
        headers: { Authorization: `Bearer ${token}` },
        timeout: 30000
      });
      setData(response.data);
      setLoading(false); // Siempre apagar loading al recibir datos
    } catch (error) {
      console.error('Error cargando tablero:', error);
      if (error.response?.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        setLoading(false);
      } else if (retry < 2) {
        console.log(`Reintentando (${retry + 1}/2)...`);
        setTimeout(() => cargarDatos(retry + 1), 1000);
        // No apagar loading durante reintentos
      } else {
        toast.error('Error al cargar datos. Intenta actualizar.');
        setLoading(false); // Apagar loading después de todos los reintentos fallidos
      }
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      window.location.href = '/login';
      return;
    }
    cargarDatos();
  }, []);

  // Cerrar dropdowns cuando se hace click fuera
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (!event.target.closest('[data-dropdown="meses"]') && !event.target.closest('[data-dropdown="anios"]')) {
        setShowMesesDropdown(false);
        setShowAniosDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="space-y-4" data-testid="tablero-ejecutivo">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-2xl font-bold text-zinc-800">Tablero Ejecutivo</h1>
        <p className="text-sm text-zinc-500">Vista consolidada para directivos • Clic en unidad para detalle</p>
      </div>

      {/* Tabs de Sub-tableros */}
      <Tabs defaultValue="comercial" className="w-full">
        <TabsList className="grid w-full max-w-2xl mx-auto grid-cols-4 mb-4">
          <TabsTrigger value="comercial" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Comercial
          </TabsTrigger>
          <TabsTrigger value="finanzas" className="flex items-center gap-2" disabled>
            <Wallet className="h-4 w-4" />
            Finanzas
          </TabsTrigger>
          <TabsTrigger value="rh" className="flex items-center gap-2" disabled>
            <UserCircle className="h-4 w-4" />
            RH
          </TabsTrigger>
          <TabsTrigger value="bsc" className="flex items-center gap-2" disabled>
            <Award className="h-4 w-4" />
            BSC
          </TabsTrigger>
        </TabsList>

        {/* Tab Comercial (Actual) */}
        <TabsContent value="comercial">
          {/* Filtros - Homologados con Dashboard Comercial */}
          <Card className="border bg-white">
            <CardContent className="py-3">
              <div className="flex items-center gap-4 flex-wrap">
                {/* Selector de Meses (multiselección) */}
                <div className="flex-1 min-w-[140px] max-w-[180px] relative" data-dropdown="meses">
                  <Label className="text-xs mb-1 block">Mes(es)</Label>
                  <button
                    type="button"
                    onClick={() => { setShowMesesDropdown(!showMesesDropdown); setShowAniosDropdown(false); }}
                    className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                    disabled={esVentasDelDia}
                  >
                    <span>{esVentasDelDia ? 'N/A' : getMesesLabel()}</span>
                    <ChevronDown className="h-4 w-4 opacity-50" />
                  </button>
                  {showMesesDropdown && !esVentasDelDia && (
                    <div className="absolute z-50 mt-1 w-full rounded-md border bg-white shadow-lg max-h-60 overflow-auto">
                      <div className="p-2 border-b">
                        <button
                          type="button"
                          onClick={() => setSelectedMeses(MESES.map(m => m.value))}
                          className="text-xs text-blue-600 hover:underline mr-3"
                        >
                          Todos
                        </button>
                        <button
                          type="button"
                          onClick={() => setSelectedMeses([String(new Date().getMonth() + 1).padStart(2, '0')])}
                          className="text-xs text-blue-600 hover:underline"
                        >
                          Solo actual
                        </button>
                      </div>
                      {MESES.map(mes => (
                        <label
                          key={mes.value}
                          className="flex items-center gap-2 px-3 py-2 hover:bg-zinc-100 cursor-pointer"
                        >
                          <Checkbox
                            checked={selectedMeses.includes(mes.value)}
                            onCheckedChange={() => toggleMes(mes.value)}
                          />
                          <span className="text-sm">{mes.label}</span>
                        </label>
                      ))}
                      <div className="p-2 border-t">
                        <Button size="sm" onClick={() => setShowMesesDropdown(false)} className="w-full">
                          Aplicar
                        </Button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Selector de Año (multiselección + Ventas del Día) */}
                <div className="flex-1 min-w-[140px] max-w-[180px] relative" data-dropdown="anios">
                  <Label className="text-xs mb-1 block">Año(s)</Label>
                  <button
                    type="button"
                    onClick={() => { setShowAniosDropdown(!showAniosDropdown); setShowMesesDropdown(false); }}
                    className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                  >
                    <span>{getAniosLabel()}</span>
                    <ChevronDown className="h-4 w-4 opacity-50" />
                  </button>
                  {showAniosDropdown && (
                    <div className="absolute z-50 mt-1 w-full rounded-md border bg-white shadow-lg max-h-60 overflow-auto">
                      <div className="p-2 border-b">
                        <button
                          type="button"
                          onClick={() => setSelectedAnios([new Date().getFullYear().toString(), (new Date().getFullYear() - 1).toString()])}
                          className="text-xs text-blue-600 hover:underline mr-3"
                        >
                          Actual + Anterior
                        </button>
                        <button
                          type="button"
                          onClick={() => setSelectedAnios([new Date().getFullYear().toString()])}
                          className="text-xs text-blue-600 hover:underline"
                        >
                          Solo actual
                        </button>
                      </div>
                      {ANIOS.map(anio => (
                        <label
                          key={anio.value}
                          className="flex items-center gap-2 px-3 py-2 hover:bg-zinc-100 cursor-pointer"
                        >
                          <Checkbox
                            checked={selectedAnios.includes(anio.value)}
                            onCheckedChange={() => toggleAnio(anio.value)}
                          />
                          <span className="text-sm">{anio.label}</span>
                        </label>
                      ))}
                      <div className="p-2 border-t">
                        <Button size="sm" onClick={() => setShowAniosDropdown(false)} className="w-full">
                          Aplicar
                        </Button>
                      </div>
                    </div>
                  )}
                </div>

                <Button 
                  onClick={() => {
                    setShowMesesDropdown(false);
                    setShowAniosDropdown(false);
                    cargarDatos();
                  }} 
                  disabled={loading} 
                  size="sm" 
                  className="mt-5"
                >
                  {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
                  Actualizar
                </Button>
                {data?.periodo && (
                  <span className="text-xs text-zinc-500 ml-auto bg-zinc-100 px-2 py-1 rounded mt-5">
                    {data.periodo.modo_ventas_dia 
                      ? <span className="text-amber-600 font-medium">🔴 Ventas del Día (sin corte)</span>
                      : `${data.periodo.mes ? MESES.find(m => m.value === String(data.periodo.mes).padStart(2, '0'))?.label : ''} ${data.periodo.anio} • Día ${data.periodo.dias_transcurridos} de ${data.periodo.dias_mes}`
                    }
                  </span>
                )}
              </div>
            </CardContent>
          </Card>

      {/* TOTALES - Vista Ejecutiva Grande */}
      {data?.totales && (
        <Card className="border-2 border-zinc-300 bg-gradient-to-br from-zinc-900 to-zinc-800 text-white">
          <CardContent className="py-6">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
              {/* Ventas Consolidadas */}
              <div className="col-span-2 md:col-span-1 flex flex-col text-center">
                <p className="text-xs text-zinc-400 uppercase tracking-wide">Ventas Consolidadas</p>
                <p className="text-3xl font-bold text-green-400">{formatCurrency(data.totales.ventas)}</p>
                <p className="text-xs text-zinc-400 mt-1">&nbsp;</p>
                <div className="flex gap-4 mt-auto pt-2 justify-center">
                  <div className="text-center">
                    <span className="text-xs text-zinc-400 block">vs Mes</span>
                    <p className={`font-bold ${data.totales.var_vs_mes_ant >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {formatPercent(data.totales.var_vs_mes_ant)}
                    </p>
                  </div>
                  <div className="text-center">
                    <span className="text-xs text-zinc-400 block">vs Año</span>
                    <p className={`font-bold ${data.totales.var_vs_año_ant >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {formatPercent(data.totales.var_vs_año_ant)}
                    </p>
                  </div>
                </div>
              </div>
              
              {/* PAX Total */}
              <div className="flex flex-col text-center">
                <p className="text-xs text-zinc-400 uppercase tracking-wide">PAX Total</p>
                <p className="text-2xl font-bold">{data.totales.pax?.toLocaleString()}</p>
                <p className="text-xs text-zinc-400 mt-1">Ticket: {formatCurrency(data.totales.ticket_prom)}</p>
                <div className="flex gap-4 mt-auto pt-2 justify-center">
                  <div className="text-center">
                    <span className="text-xs text-zinc-400 block">vs Mes</span>
                    <p className={`text-sm font-bold ${(data.totales.var_pax_mes || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {formatPercent(data.totales.var_pax_mes || 0)}
                    </p>
                  </div>
                  <div className="text-center">
                    <span className="text-xs text-zinc-400 block">vs Año</span>
                    <p className={`text-sm font-bold ${(data.totales.var_pax_año || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {formatPercent(data.totales.var_pax_año || 0)}
                    </p>
                  </div>
                </div>
              </div>
              
              {/* Cheques */}
              <div className="flex flex-col text-center">
                <p className="text-xs text-zinc-400 uppercase tracking-wide">Cheques</p>
                <p className="text-2xl font-bold">{data.totales.cheques?.toLocaleString()}</p>
                <p className="text-xs text-zinc-400 mt-1">Promedio: {formatCurrency(data.totales.cheque_prom)}</p>
                <div className="flex gap-4 mt-auto pt-2 justify-center">
                  <div className="text-center">
                    <span className="text-xs text-zinc-400 block">vs Mes</span>
                    <p className={`text-sm font-bold ${(data.totales.var_cheques_mes || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {formatPercent(data.totales.var_cheques_mes || 0)}
                    </p>
                  </div>
                  <div className="text-center">
                    <span className="text-xs text-zinc-400 block">vs Año</span>
                    <p className={`text-sm font-bold ${(data.totales.var_cheques_año || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {formatPercent(data.totales.var_cheques_año || 0)}
                    </p>
                  </div>
                </div>
              </div>
              
              {/* Proyección Mes */}
              <div className="flex flex-col text-center">
                <p className="text-xs text-zinc-400 uppercase tracking-wide">Proyección Mes</p>
                <p className="text-2xl font-bold text-orange-400">{formatCurrency(data.totales.proyeccion)}</p>
                <p className="text-xs text-zinc-400 mt-1">Si mantiene ritmo</p>
                <div className="flex gap-4 mt-auto pt-2 justify-center">
                  <div className="text-center">
                    <span className="text-xs text-zinc-400 block">vs Año Ant.</span>
                    <p className={`text-sm font-bold ${(data.totales.var_proy_vs_año || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {formatPercent(data.totales.var_proy_vs_año || 0)}
                    </p>
                  </div>
                </div>
              </div>
              
              {/* Unidades */}
              <div className="flex flex-col text-center">
                <p className="text-xs text-zinc-400 uppercase tracking-wide">Unidades</p>
                <p className="text-2xl font-bold">{data.unidades?.length || 0}</p>
                <p className="text-xs text-zinc-400 mt-1">Conectadas</p>
                <div className="flex gap-4 mt-auto pt-2 justify-center">
                  <div className="text-center">
                    <span className="text-xs text-zinc-400 block">Año Ant.</span>
                    <p className="text-sm font-bold text-zinc-300">
                      {data.totales.unidades_año_ant || 0}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Grid de Unidades - Clickeables */}
      {data?.unidades && data.unidades.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            Unidades ({data.unidades.length})
            <span className="text-xs font-normal text-zinc-500">• Clic para ver detalle</span>
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {data.unidades.map((unidad, idx) => (
              <UnidadCard 
                key={idx} 
                unidad={unidad} 
                onClick={setUnidadSeleccionada}
              />
            ))}
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && !data && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
          <span className="ml-2 text-zinc-500">Consultando todas las unidades...</span>
        </div>
      )}
        </TabsContent>

        {/* Tab Finanzas (Próximamente) */}
        <TabsContent value="finanzas">
          <Card className="border bg-zinc-50">
            <CardContent className="py-12 text-center">
              <Wallet className="h-12 w-12 mx-auto text-zinc-300 mb-4" />
              <h3 className="text-lg font-semibold text-zinc-600">Tablero Financiero</h3>
              <p className="text-sm text-zinc-500 mt-2">Próximamente: Flujo de caja, cuentas por cobrar/pagar, indicadores financieros</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab RH (Próximamente) */}
        <TabsContent value="rh">
          <Card className="border bg-zinc-50">
            <CardContent className="py-12 text-center">
              <UserCircle className="h-12 w-12 mx-auto text-zinc-300 mb-4" />
              <h3 className="text-lg font-semibold text-zinc-600">Tablero de Recursos Humanos</h3>
              <p className="text-sm text-zinc-500 mt-2">Próximamente: Plantilla, rotación, productividad, horas extra</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab BSC (Próximamente) */}
        <TabsContent value="bsc">
          <Card className="border bg-zinc-50">
            <CardContent className="py-12 text-center">
              <Award className="h-12 w-12 mx-auto text-zinc-300 mb-4" />
              <h3 className="text-lg font-semibold text-zinc-600">Balance Scorecard</h3>
              <p className="text-sm text-zinc-500 mt-2">Próximamente: Perspectivas financiera, cliente, procesos, aprendizaje</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Modal de Detalle */}
      {unidadSeleccionada && (
        <DetalleUnidad 
          unidad={unidadSeleccionada} 
          onClose={() => setUnidadSeleccionada(null)}
          mes={mes}
          anio={anio}
        />
      )}
    </div>
  );
}
