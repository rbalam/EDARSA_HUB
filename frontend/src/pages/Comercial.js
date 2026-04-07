import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Checkbox } from '../components/ui/checkbox';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Progress } from '../components/ui/progress';
import { toast } from 'sonner';
import { 
  Loader2, TrendingUp, TrendingDown, DollarSign, Users, Clock, Target,
  AlertTriangle, BarChart3, PieChart, ShoppingBag, Utensils, Coffee,
  Wine, Award, RefreshCw, Calendar, ArrowUpRight, ArrowDownRight,
  Receipt, ChevronLeft, ChevronRight, X, Search, ChevronDown, ChevronUp,
  UserCheck, Download, FileSpreadsheet, FileText, Share2, Mail, Scale
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, 
  ResponsiveContainer, Cell, ReferenceLine 
} from 'recharts';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const formatNumber = (num) => {
  if (num === null || num === undefined) return '-';
  return new Intl.NumberFormat('es-MX', { minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(num);
};

const formatCurrency = (num) => {
  if (num === null || num === undefined) return '-';
  return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(num);
};

const formatPercent = (num) => {
  if (num === null || num === undefined) return '-';
  return `${num >= 0 ? '+' : ''}${num.toFixed(1)}%`;
};

// ============ MODAL DE DETALLE DE MOVIMIENTOS (Drill-down) ============
function DetalleMovimientosModal({ isOpen, onClose, serverId, sucursal, periodo, tipoKpi }) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [page, setPage] = useState(1);

  const titulos = {
    ventas: { titulo: 'Detalle de Ventas', icono: DollarSign, color: 'text-green-600' },
    ticket: { titulo: 'Detalle de Cheques', icono: Receipt, color: 'text-blue-600' },
    pax: { titulo: 'Detalle de Comensales (PAX)', icono: Users, color: 'text-purple-600' },
    rotacion: { titulo: 'Detalle de Mesas', icono: Utensils, color: 'text-orange-600' }
  };

  const config = titulos[tipoKpi] || titulos.ventas;
  const IconComponent = config.icono;

  useEffect(() => {
    if (isOpen && serverId && sucursal) {
      cargarDetalle();
    }
  }, [isOpen, serverId, sucursal, page, periodo]);

  const cargarDetalle = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/comercial/detalle-movimientos/${serverId}`, {
        params: { sucursal, tipo: tipoKpi, periodo, page, limit: 50 },
        headers: { Authorization: `Bearer ${token}` }
      });
      setData(response.data);
    } catch (error) {
      console.error('Error cargando detalle:', error);
      toast.error('Error al cargar detalle de movimientos');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[85vh] overflow-hidden flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="flex items-center gap-2">
            <IconComponent className={`h-5 w-5 ${config.color}`} />
            {config.titulo}
            {data?.servidor && <span className="text-sm font-normal text-zinc-500">• {data.servidor}</span>}
          </DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
          </div>
        ) : data?.movimientos?.length > 0 ? (
          <div className="flex-1 overflow-hidden flex flex-col">
            {/* Info del período */}
            <div className="flex items-center justify-between mb-3 px-1">
              <span className="text-sm text-zinc-500">
                Período: {data.periodo?.inicio} a {data.periodo?.fin}
              </span>
              <span className="text-sm font-medium">
                {data.total} movimientos
              </span>
            </div>

            {/* Tabla de movimientos */}
            <div className="flex-1 overflow-auto border rounded-lg">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-zinc-800 text-white">
                  <tr>
                    <th className="py-2 px-3 text-left">Folio</th>
                    <th className="py-2 px-3 text-left">Fecha/Hora</th>
                    <th className="py-2 px-3 text-right">Importe</th>
                    <th className="py-2 px-3 text-center">PAX</th>
                    <th className="py-2 px-3 text-center">Productos</th>
                    <th className="py-2 px-3 text-left">Tipo</th>
                  </tr>
                </thead>
                <tbody>
                  {data.movimientos.map((mov, idx) => (
                    <tr key={idx} className="border-b hover:bg-zinc-50 transition-colors">
                      <td className="py-2 px-3 font-mono text-xs font-medium">{mov.folio}</td>
                      <td className="py-2 px-3 text-zinc-600">{mov.fecha}</td>
                      <td className="py-2 px-3 text-right font-semibold text-green-600">
                        {formatCurrency(mov.importe)}
                      </td>
                      <td className="py-2 px-3 text-center">
                        {mov.pax > 0 ? (
                          <span className="inline-flex items-center gap-1">
                            <Users className="h-3 w-3 text-purple-500" />
                            {mov.pax}
                          </span>
                        ) : '-'}
                      </td>
                      <td className="py-2 px-3 text-center text-zinc-500">{mov.num_productos}</td>
                      <td className="py-2 px-3">
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          mov.tipo_servicio === 'Comedor' ? 'bg-blue-100 text-blue-700' :
                          mov.tipo_servicio === 'Domicilio' ? 'bg-orange-100 text-orange-700' :
                          mov.tipo_servicio === 'Para llevar' ? 'bg-green-100 text-green-700' :
                          'bg-zinc-100 text-zinc-700'
                        }`}>
                          {mov.tipo_servicio}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Paginación */}
            {data.pages > 1 && (
              <div className="flex items-center justify-between pt-3 border-t mt-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page <= 1}
                >
                  <ChevronLeft className="h-4 w-4 mr-1" /> Anterior
                </Button>
                <span className="text-sm text-zinc-500">
                  Página {page} de {data.pages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => Math.min(data.pages, p + 1))}
                  disabled={page >= data.pages}
                >
                  Siguiente <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-12 text-zinc-500">
            <Receipt className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p>No hay movimientos en este período</p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

// ============ TAB 1: DASHBOARD DE VENTAS ============
// Constantes para meses y años
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
  const years = [];
  for (let y = currentYear; y >= currentYear - 5; y--) {
    years.push({ value: y.toString(), label: y.toString() });
  }
  return years;
};

function DashboardVentas({ servers, selectedServer, setSelectedServer, selectedSucursal, setSelectedSucursal, sucursales, showSucursalSelector }) {
  const [loading, setLoading] = useState(false);
  const [kpis, setKpis] = useState(null);
  const [comparativo, setComparativo] = useState(null);
  const [alertas, setAlertas] = useState([]);
  const [periodo, setPeriodo] = useState('mes'); // mes, semana, dia
  const [selectedMeses, setSelectedMeses] = useState([String(new Date().getMonth() + 1).padStart(2, '0')]);
  const [selectedAnios, setSelectedAnios] = useState([new Date().getFullYear().toString()]);
  const [showMesesDropdown, setShowMesesDropdown] = useState(false);
  const [showAniosDropdown, setShowAniosDropdown] = useState(false);
  const [detalleModal, setDetalleModal] = useState({ open: false, tipo: null });
  const [tipoComparacion, setTipoComparacion] = useState('dias_equiv'); // dias_equiv o mes_completo
  
  const ANIOS = getAniosDisponibles();

  const cargarDashboard = async () => {
    if (!selectedServer || !selectedSucursal) {
      toast.error('Selecciona servidor y sucursal');
      return;
    }
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/comercial/dashboard/${selectedServer}`, {
        params: { 
          sucursal: selectedSucursal, 
          periodo,
          meses: selectedMeses.join(','),
          anios: selectedAnios.join(','),
          tipo_comparacion: tipoComparacion
        },
        headers: { Authorization: `Bearer ${token}` }
      });
      setKpis(response.data.kpis);
      setComparativo(response.data.comparativo);
      setAlertas(response.data.alertas || []);
    } catch (error) {
      console.error('Error cargando dashboard:', error);
      toast.error('Error al cargar datos de ventas');
      setKpis(null);
      setComparativo(null);
      setAlertas([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedServer && selectedSucursal) {
      cargarDashboard();
    }
  }, [selectedServer, selectedSucursal, periodo, selectedMeses, selectedAnios, tipoComparacion]);

  const toggleMes = (mes) => {
    setSelectedMeses(prev => {
      if (prev.includes(mes)) {
        if (prev.length === 1) return prev; // Al menos un mes debe estar seleccionado
        return prev.filter(m => m !== mes);
      }
      return [...prev, mes].sort();
    });
  };

  const toggleAnio = (anio) => {
    setSelectedAnios(prev => {
      if (prev.includes(anio)) {
        if (prev.length === 1) return prev; // Al menos un año debe estar seleccionado
        return prev.filter(a => a !== anio);
      }
      return [...prev, anio].sort().reverse(); // Ordenar descendente
    });
  };

  const getMesesLabel = () => {
    if (selectedMeses.length === 0) return 'Seleccionar';
    if (selectedMeses.length === 1) {
      return MESES.find(m => m.value === selectedMeses[0])?.label || 'Mes';
    }
    if (selectedMeses.length === 12) return 'Todo el año';
    return `${selectedMeses.length} meses`;
  };

  const getAniosLabel = () => {
    if (selectedAnios.length === 0) return 'Seleccionar';
    if (selectedAnios.length === 1) {
      return selectedAnios[0];
    }
    return `${selectedAnios.length} años`;
  };

  const handleDoubleClick = (tipoKpi) => {
    if (!selectedServer || !selectedSucursal) {
      toast.error('Selecciona servidor y sucursal primero');
      return;
    }
    setDetalleModal({ open: true, tipo: tipoKpi });
  };

  return (
    <div className="space-y-4">
      {/* Filtros */}
      <Card className="border">
        <CardContent className="py-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex-1 min-w-[180px] max-w-xs">
              <Label className="text-xs mb-1 block">Servidor</Label>
              <Select value={selectedServer} onValueChange={setSelectedServer}>
                <SelectTrigger><SelectValue placeholder="Seleccionar" /></SelectTrigger>
                <SelectContent>
                  {servers.map(s => <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="flex-1 min-w-[180px] max-w-xs">
              <Label className="text-xs mb-1 block">Sucursal</Label>
              <Select value={selectedSucursal} onValueChange={setSelectedSucursal} disabled={!selectedServer}>
                <SelectTrigger><SelectValue placeholder={selectedServer ? "Seleccionar" : "Selecciona servidor"} /></SelectTrigger>
                <SelectContent>
                  {sucursales.map(s => <SelectItem key={s.codigo || s.nombre} value={s.nombre}>{s.nombre}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="flex-1 min-w-[120px] max-w-[150px]">
              <Label className="text-xs mb-1 block">Período</Label>
              <Select value={periodo} onValueChange={setPeriodo}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="dia">Hoy</SelectItem>
                  <SelectItem value="semana">Semana</SelectItem>
                  <SelectItem value="mes">Mes(es)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {/* Selector de Meses (multiselección) */}
            <div className="flex-1 min-w-[150px] max-w-[200px] relative">
              <Label className="text-xs mb-1 block">Mes(es)</Label>
              <button
                type="button"
                onClick={() => setShowMesesDropdown(!showMesesDropdown)}
                className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                <span>{getMesesLabel()}</span>
                <ChevronDown className="h-4 w-4 opacity-50" />
              </button>
              {showMesesDropdown && (
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
            {/* Selector de Año (multiselección) */}
            <div className="flex-1 min-w-[120px] max-w-[160px] relative">
              <Label className="text-xs mb-1 block">Año(s)</Label>
              <button
                type="button"
                onClick={() => setShowAniosDropdown(!showAniosDropdown)}
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
            <Button onClick={cargarDashboard} disabled={loading || !selectedServer || !selectedSucursal} className="mt-5">
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
              Actualizar
            </Button>
            {/* Selector de Tipo de Comparación */}
            <div className="flex-1 min-w-[180px] max-w-[220px]">
              <Label className="text-xs mb-1 block">Comparar con:</Label>
              <div className="flex rounded-md border border-input overflow-hidden">
                <button
                  type="button"
                  onClick={() => setTipoComparacion('dias_equiv')}
                  className={`flex-1 px-3 py-2 text-xs font-medium transition-colors ${
                    tipoComparacion === 'dias_equiv' 
                      ? 'bg-primary text-primary-foreground' 
                      : 'bg-background hover:bg-zinc-100'
                  }`}
                >
                  Días Equiv.
                </button>
                <button
                  type="button"
                  onClick={() => setTipoComparacion('mes_completo')}
                  className={`flex-1 px-3 py-2 text-xs font-medium transition-colors border-l ${
                    tipoComparacion === 'mes_completo' 
                      ? 'bg-primary text-primary-foreground' 
                      : 'bg-background hover:bg-zinc-100'
                  }`}
                >
                  Mes Completo
                </button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Alertas */}
      {alertas.length > 0 && (
        <Card className="border border-red-200 bg-red-50">
          <CardHeader className="py-2">
            <CardTitle className="text-sm flex items-center gap-2 text-red-700">
              <AlertTriangle className="h-4 w-4" /> Alertas Comerciales
            </CardTitle>
          </CardHeader>
          <CardContent className="py-2 space-y-1">
            {alertas.map((a, idx) => (
              <div key={idx} className="flex items-center gap-2 text-sm p-2 bg-white rounded border border-red-200">
                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${a.tipo === 'sobrestock' ? 'bg-orange-100 text-orange-700' : 'bg-red-100 text-red-700'}`}>
                  {a.tipo === 'sobrestock' ? 'SOBRESTOCK' : 'BAJA VENTA'}
                </span>
                <span className="font-medium">{a.producto}</span>
                <span className="text-zinc-500">{a.mensaje}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Instrucción de drill-down */}
      {kpis && (
        <p className="text-xs text-zinc-500 italic text-center">
          💡 Doble clic en cualquier tarjeta para ver el detalle de movimientos
        </p>
      )}

      {/* KPIs principales - CON DOBLE CLICK DRILL-DOWN */}
      {kpis && (
        <>
          {/* FILA 1: Ventas, Pax Promedio, Cheque Promedio */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Ventas del Período (VERDE) */}
            <Card 
              className="border bg-gradient-to-br from-green-50 to-white cursor-pointer hover:shadow-lg hover:scale-[1.02] transition-all"
              onDoubleClick={() => handleDoubleClick('ventas')}
              data-testid="kpi-ventas"
            >
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-zinc-500">Ventas del Período</p>
                    <p className="text-2xl font-bold text-green-600">{formatCurrency(kpis.ventas_periodo)}</p>
                  </div>
                  <DollarSign className="h-8 w-8 text-green-200" />
                </div>
                <div className="flex gap-3 mt-2 text-xs">
                  <span className={comparativo?.vs_periodo_anterior >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {formatPercent(comparativo?.vs_periodo_anterior || 0)} vs mes
                  </span>
                  <span className={comparativo?.vs_ano_anterior >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {formatPercent(comparativo?.vs_ano_anterior || 0)} vs año
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* Pax Promedio (MORADO) */}
            <Card 
              className="border bg-gradient-to-br from-purple-50 to-white cursor-pointer hover:shadow-lg hover:scale-[1.02] transition-all"
              onDoubleClick={() => handleDoubleClick('pax')}
              data-testid="kpi-pax-promedio"
            >
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-zinc-500">Pax Promedio</p>
                    <p className="text-2xl font-bold text-purple-600">
                      {formatCurrency(kpis.pax_total > 0 ? (kpis.ventas_periodo / kpis.pax_total) : 0)}
                    </p>
                    <p className="text-xs text-zinc-400">Ventas ÷ PAX</p>
                  </div>
                  <Users className="h-8 w-8 text-purple-200" />
                </div>
                <div className="flex gap-3 mt-2 text-xs">
                  <span className={comparativo?.pax_vs_mes_anterior >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {formatPercent(comparativo?.pax_vs_mes_anterior || 0)} vs mes
                  </span>
                  <span className={comparativo?.pax_vs_ano_anterior >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {formatPercent(comparativo?.pax_vs_ano_anterior || 0)} vs año
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* Cheque Promedio (AZUL) */}
            <Card 
              className="border bg-gradient-to-br from-blue-50 to-white cursor-pointer hover:shadow-lg hover:scale-[1.02] transition-all"
              onDoubleClick={() => handleDoubleClick('ticket')}
              data-testid="kpi-cheque-promedio"
            >
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-zinc-500">Cheque Promedio</p>
                    <p className="text-2xl font-bold text-blue-600">{formatCurrency(kpis.ticket_promedio)}</p>
                    <p className="text-xs text-zinc-400">Ventas ÷ Cheques</p>
                  </div>
                  <Receipt className="h-8 w-8 text-blue-200" />
                </div>
                <div className="flex gap-3 mt-2 text-xs">
                  <span className={comparativo?.cheque_vs_mes_anterior >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {formatPercent(comparativo?.cheque_vs_mes_anterior || 0)} vs mes
                  </span>
                  <span className={comparativo?.cheque_vs_ano_anterior >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {formatPercent(comparativo?.cheque_vs_ano_anterior || 0)} vs año
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* FILA 2: Rotación, PAX Total, Cheques Total (mismas columnas de color) */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Rotación Mesas (VERDE - debajo de Ventas) */}
            <Card 
              className="border bg-gradient-to-br from-green-50/50 to-white cursor-pointer hover:shadow-lg hover:scale-[1.02] transition-all"
              onDoubleClick={() => handleDoubleClick('rotacion')}
              data-testid="kpi-rotacion"
            >
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-zinc-500">Rotación Mesas</p>
                    <p className="text-2xl font-bold text-green-600">{formatNumber(kpis.rotacion_mesas)}x</p>
                    <p className="text-xs text-zinc-400">{kpis.mesas_atendidas} mesas atendidas</p>
                  </div>
                  <Utensils className="h-8 w-8 text-green-200" />
                </div>
                <div className="flex gap-3 mt-2 text-xs">
                  <span className={comparativo?.rotacion_vs_mes >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {formatPercent(comparativo?.rotacion_vs_mes || 0)} vs mes
                  </span>
                  <span className={comparativo?.rotacion_vs_ano >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {formatPercent(comparativo?.rotacion_vs_ano || 0)} vs año
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* PAX Total (MORADO) */}
            <Card 
              className="border bg-gradient-to-br from-purple-50/50 to-white cursor-pointer hover:shadow-lg hover:scale-[1.02] transition-all"
              onDoubleClick={() => handleDoubleClick('pax')}
              data-testid="kpi-pax-total"
            >
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-zinc-500">PAX Total</p>
                    <p className="text-2xl font-bold text-purple-600">{formatNumber(kpis.pax_total)}</p>
                  </div>
                  <Users className="h-8 w-8 text-purple-200" />
                </div>
                <div className="flex gap-3 mt-2 text-xs">
                  <span className={comparativo?.pax_total_vs_mes >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {formatPercent(comparativo?.pax_total_vs_mes || 0)} vs mes
                  </span>
                  <span className={comparativo?.pax_total_vs_ano >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {formatPercent(comparativo?.pax_total_vs_ano || 0)} vs año
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* Cheques Total (AZUL) */}
            <Card 
              className="border bg-gradient-to-br from-blue-50/50 to-white cursor-pointer hover:shadow-lg hover:scale-[1.02] transition-all"
              onDoubleClick={() => handleDoubleClick('ticket')}
              data-testid="kpi-cheques-total"
            >
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-zinc-500">Cheques Total</p>
                    <p className="text-2xl font-bold text-blue-600">{formatNumber(kpis.cheques_total)}</p>
                  </div>
                  <Receipt className="h-8 w-8 text-blue-200" />
                </div>
                <div className="flex gap-3 mt-2 text-xs">
                  <span className={comparativo?.cheques_total_vs_mes >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {formatPercent(comparativo?.cheques_total_vs_mes || 0)} vs mes
                  </span>
                  <span className={comparativo?.cheques_total_vs_ano >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {formatPercent(comparativo?.cheques_total_vs_ano || 0)} vs año
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Comparativos */}
          {comparativo && (
            <Card className="border">
              <CardHeader className="py-3">
                <CardTitle className="text-base">Comparativo de Ventas</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-zinc-50 rounded">
                    <p className="text-xs text-zinc-500 mb-1">vs Período Anterior</p>
                    <p className={`text-xl font-bold ${comparativo.vs_periodo_anterior >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatPercent(comparativo.vs_periodo_anterior)}
                    </p>
                  </div>
                  <div className="text-center p-4 bg-zinc-50 rounded">
                    <p className="text-xs text-zinc-500 mb-1">vs Año Anterior</p>
                    <p className={`text-xl font-bold ${comparativo.vs_ano_anterior >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatPercent(comparativo.vs_ano_anterior)}
                    </p>
                  </div>
                  <div className="text-center p-4 bg-zinc-50 rounded">
                    <p className="text-xs text-zinc-500 mb-1">vs Presupuesto</p>
                    <p className={`text-xl font-bold ${comparativo.vs_presupuesto >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatPercent(comparativo.vs_presupuesto)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Modal de Detalle de Movimientos */}
      <DetalleMovimientosModal
        isOpen={detalleModal.open}
        onClose={() => setDetalleModal({ open: false, tipo: null })}
        serverId={selectedServer}
        sucursal={selectedSucursal}
        periodo={periodo}
        tipoKpi={detalleModal.tipo}
      />
    </div>
  );
}

// ============ TAB 2: TICKET PERFECTO Y RENTABILIDAD ============
function TicketPerfecto({ servers, selectedServer, setSelectedServer, selectedSucursal, setSelectedSucursal, sucursales }) {
  const [loading, setLoading] = useState(false);
  const [ticketData, setTicketData] = useState(null);
  const [rentabilidad, setRentabilidad] = useState([]);

  const cargarDatos = async () => {
    if (!selectedServer || !selectedSucursal) return;
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/comercial/ticket-perfecto/${selectedServer}`, {
        params: { sucursal: selectedSucursal },
        headers: { Authorization: `Bearer ${token}` }
      });
      setTicketData(response.data.ticket);
      setRentabilidad(response.data.rentabilidad || []);
    } catch (error) {
      console.error('Error cargando ticket perfecto:', error);
      toast.error('Error al cargar datos de ticket perfecto');
      setTicketData(null);
      setRentabilidad([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedServer && selectedSucursal) cargarDatos();
  }, [selectedServer, selectedSucursal]);

  return (
    <div className="space-y-4">
      {/* Filtros */}
      <Card className="border">
        <CardContent className="py-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex-1 min-w-[180px] max-w-xs">
              <Label className="text-xs mb-1 block">Servidor</Label>
              <Select value={selectedServer} onValueChange={setSelectedServer}>
                <SelectTrigger><SelectValue placeholder="Seleccionar" /></SelectTrigger>
                <SelectContent>{servers.map(s => <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="flex-1 min-w-[180px] max-w-xs">
              <Label className="text-xs mb-1 block">Sucursal</Label>
              <Select value={selectedSucursal} onValueChange={setSelectedSucursal} disabled={!selectedServer}>
                <SelectTrigger><SelectValue placeholder={selectedServer ? "Seleccionar" : "Selecciona servidor"} /></SelectTrigger>
                <SelectContent>{sucursales.map(s => <SelectItem key={s.codigo || s.nombre} value={s.nombre}>{s.nombre}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <Button onClick={cargarDatos} disabled={loading} className="mt-5">
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
              Actualizar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Ticket Perfecto */}
      {ticketData && (
        <Card className="border">
          <CardHeader className="py-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Award className="h-5 w-5 text-yellow-500" />
              Ticket Perfecto (Entrada + Plato Fuerte + Postre + Digestivo)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <div className="text-center p-3 bg-yellow-50 rounded border border-yellow-200">
                <p className="text-xs text-zinc-500">Tickets Completos</p>
                <p className="text-2xl font-bold text-yellow-600">{ticketData.pct_completos}%</p>
                <p className="text-xs text-zinc-500">{ticketData.tickets_completos} de {ticketData.tickets_totales}</p>
              </div>
              <div className="text-center p-3 bg-zinc-50 rounded">
                <Coffee className="h-5 w-5 mx-auto mb-1 text-orange-500" />
                <p className="text-xs text-zinc-500">Con Entrada</p>
                <p className="text-lg font-bold">{ticketData.pct_entrada}%</p>
              </div>
              <div className="text-center p-3 bg-zinc-50 rounded">
                <Utensils className="h-5 w-5 mx-auto mb-1 text-red-500" />
                <p className="text-xs text-zinc-500">Con Plato Fuerte</p>
                <p className="text-lg font-bold">{ticketData.pct_plato_fuerte}%</p>
              </div>
              <div className="text-center p-3 bg-zinc-50 rounded">
                <PieChart className="h-5 w-5 mx-auto mb-1 text-pink-500" />
                <p className="text-xs text-zinc-500">Con Postre</p>
                <p className="text-lg font-bold">{ticketData.pct_postre}%</p>
              </div>
              <div className="text-center p-3 bg-zinc-50 rounded">
                <Wine className="h-5 w-5 mx-auto mb-1 text-purple-500" />
                <p className="text-xs text-zinc-500">Con Digestivo</p>
                <p className="text-lg font-bold">{ticketData.pct_digestivo}%</p>
              </div>
            </div>
            
            <div className="p-4 bg-red-50 rounded border border-red-200">
              <p className="text-sm text-red-700">
                <AlertTriangle className="h-4 w-4 inline mr-1" />
                <strong>Oportunidad Perdida:</strong> {formatCurrency(ticketData.oportunidad_perdida)} en ventas potenciales por tickets incompletos
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Rentabilidad por Producto */}
      {rentabilidad.length > 0 && (
        <Card className="border">
          <CardHeader className="py-3">
            <CardTitle className="text-base">Productos por Rentabilidad (Margen de Utilidad)</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="max-h-[400px] overflow-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-zinc-800 text-white">
                  <tr>
                    <th className="py-2 px-3 text-left">Categoría</th>
                    <th className="py-2 px-3 text-left">Código</th>
                    <th className="py-2 px-3 text-left">Producto</th>
                    <th className="py-2 px-3 text-right">Ventas</th>
                    <th className="py-2 px-3 text-right">Costo</th>
                    <th className="py-2 px-3 text-right">Margen %</th>
                  </tr>
                </thead>
                <tbody>
                  {rentabilidad.map((prod, idx) => (
                    <tr key={idx} className="border-b hover:bg-zinc-50">
                      <td className="py-2 px-3">
                        <span className={`px-2 py-1 rounded text-xs font-bold ${
                          prod.categoria === 'A' ? 'bg-green-100 text-green-700' :
                          prod.categoria === 'B' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-red-100 text-red-700'
                        }`}>{prod.categoria}</span>
                      </td>
                      <td className="py-2 px-3 font-mono text-xs">{prod.codigo}</td>
                      <td className="py-2 px-3">{prod.producto}</td>
                      <td className="py-2 px-3 text-right text-green-600">{formatCurrency(prod.ventas)}</td>
                      <td className="py-2 px-3 text-right text-red-600">{formatCurrency(prod.costo)}</td>
                      <td className="py-2 px-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Progress value={prod.margen} className="w-16 h-2" />
                          <span className="font-bold">{prod.margen}%</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ============ TAB 3: METAS DE VENTAS ============
function MetasVentas({ servers, selectedServer, setSelectedServer, selectedSucursal, setSelectedSucursal, sucursales }) {
  const [loading, setLoading] = useState(false);
  const [metasProducto, setMetasProducto] = useState([]);
  const [metasVendedor, setMetasVendedor] = useState([]);

  const cargarMetas = async () => {
    if (!selectedServer || !selectedSucursal) return;
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/comercial/metas/${selectedServer}`, {
        params: { sucursal: selectedSucursal },
        headers: { Authorization: `Bearer ${token}` }
      });
      setMetasProducto(response.data.por_producto || []);
      setMetasVendedor(response.data.por_vendedor || []);
    } catch (error) {
      console.error('Error cargando metas:', error);
      toast.error('Error al cargar metas');
      setMetasProducto([]);
      setMetasVendedor([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedServer && selectedSucursal) cargarMetas();
  }, [selectedServer, selectedSucursal]);

  return (
    <div className="space-y-4">
      {/* Filtros */}
      <Card className="border">
        <CardContent className="py-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex-1 min-w-[180px] max-w-xs">
              <Label className="text-xs mb-1 block">Servidor</Label>
              <Select value={selectedServer} onValueChange={setSelectedServer}>
                <SelectTrigger><SelectValue placeholder="Seleccionar" /></SelectTrigger>
                <SelectContent>{servers.map(s => <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="flex-1 min-w-[180px] max-w-xs">
              <Label className="text-xs mb-1 block">Sucursal</Label>
              <Select value={selectedSucursal} onValueChange={setSelectedSucursal} disabled={!selectedServer}>
                <SelectTrigger><SelectValue placeholder={selectedServer ? "Seleccionar" : "Selecciona servidor"} /></SelectTrigger>
                <SelectContent>{sucursales.map(s => <SelectItem key={s.codigo || s.nombre} value={s.nombre}>{s.nombre}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <Button onClick={cargarMetas} disabled={loading} className="mt-5">
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Target className="h-4 w-4 mr-2" />}
              Cargar Metas
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid md:grid-cols-2 gap-4">
        {/* Metas por Producto */}
        <Card className="border">
          <CardHeader className="py-3">
            <CardTitle className="text-base">Metas por Producto</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {metasProducto.map((m, idx) => (
              <div key={idx} className="p-3 bg-zinc-50 rounded">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium">{m.producto}</span>
                  <span className={`font-bold ${m.cumplimiento >= 100 ? 'text-green-600' : m.cumplimiento >= 80 ? 'text-yellow-600' : 'text-red-600'}`}>
                    {m.cumplimiento}%
                  </span>
                </div>
                <Progress value={Math.min(m.cumplimiento, 100)} className="h-2 mb-1" />
                <div className="flex justify-between text-xs text-zinc-500">
                  <span>Real: {formatCurrency(m.real)}</span>
                  <span>Meta: {formatCurrency(m.meta)}</span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Metas por Vendedor */}
        <Card className="border">
          <CardHeader className="py-3">
            <CardTitle className="text-base">Metas por Vendedor</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {metasVendedor.map((m, idx) => (
              <div key={idx} className="p-3 bg-zinc-50 rounded">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium">{m.vendedor}</span>
                  <span className={`font-bold ${m.cumplimiento >= 100 ? 'text-green-600' : m.cumplimiento >= 80 ? 'text-yellow-600' : 'text-red-600'}`}>
                    {m.cumplimiento}%
                  </span>
                </div>
                <Progress value={Math.min(m.cumplimiento, 100)} className="h-2 mb-1" />
                <div className="flex justify-between text-xs text-zinc-500">
                  <span>Real: {formatCurrency(m.real)}</span>
                  <span>Meta: {formatCurrency(m.meta)}</span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// ============ TAB 4: VENTAS POR HORA/DÍA ============
function VentasPorTiempo({ servers, selectedServer, setSelectedServer, selectedSucursal, setSelectedSucursal, sucursales }) {
  const [loading, setLoading] = useState(false);
  const [ventasPorHora, setVentasPorHora] = useState([]);
  const [ventasPorDia, setVentasPorDia] = useState([]);

  const cargarDatos = async () => {
    if (!selectedServer || !selectedSucursal) return;
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/comercial/ventas-tiempo/${selectedServer}`, {
        params: { sucursal: selectedSucursal },
        headers: { Authorization: `Bearer ${token}` }
      });
      setVentasPorHora(response.data.por_hora || []);
      setVentasPorDia(response.data.por_dia || []);
    } catch (error) {
      console.error('Error cargando ventas por tiempo:', error);
      toast.error('Error al cargar datos por hora/día');
      setVentasPorHora([]);
      setVentasPorDia([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedServer && selectedSucursal) cargarDatos();
  }, [selectedServer, selectedSucursal]);

  const maxVentaHora = Math.max(...ventasPorHora.map(v => v.ventas), 1);
  const maxVentaDia = Math.max(...ventasPorDia.map(v => v.ventas), 1);

  return (
    <div className="space-y-4">
      {/* Filtros */}
      <Card className="border">
        <CardContent className="py-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex-1 min-w-[180px] max-w-xs">
              <Label className="text-xs mb-1 block">Servidor</Label>
              <Select value={selectedServer} onValueChange={setSelectedServer}>
                <SelectTrigger><SelectValue placeholder="Seleccionar" /></SelectTrigger>
                <SelectContent>{servers.map(s => <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="flex-1 min-w-[180px] max-w-xs">
              <Label className="text-xs mb-1 block">Sucursal</Label>
              <Select value={selectedSucursal} onValueChange={setSelectedSucursal} disabled={!selectedServer}>
                <SelectTrigger><SelectValue placeholder={selectedServer ? "Seleccionar" : "Selecciona servidor"} /></SelectTrigger>
                <SelectContent>{sucursales.map(s => <SelectItem key={s.codigo || s.nombre} value={s.nombre}>{s.nombre}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <Button onClick={cargarDatos} disabled={loading} className="mt-5">
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Clock className="h-4 w-4 mr-2" />}
              Actualizar
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid md:grid-cols-2 gap-4">
        {/* Ventas por Hora */}
        <Card className="border">
          <CardHeader className="py-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Clock className="h-5 w-5" /> Ventas por Hora (Horarios Pico)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {ventasPorHora.map((v, idx) => (
              <div key={idx} className="flex items-center gap-3">
                <span className="w-14 text-sm font-medium">{v.hora}</span>
                <div className="flex-1 h-6 bg-zinc-100 rounded overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-blue-500 to-blue-600 flex items-center justify-end pr-2"
                    style={{ width: `${(v.ventas / maxVentaHora) * 100}%` }}
                  >
                    <span className="text-xs text-white font-medium">{formatCurrency(v.ventas)}</span>
                  </div>
                </div>
                <span className="w-16 text-xs text-zinc-500">{v.pax} pax</span>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Ventas por Día */}
        <Card className="border">
          <CardHeader className="py-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Calendar className="h-5 w-5" /> Ventas por Día de la Semana
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {ventasPorDia.map((v, idx) => (
              <div key={idx} className="flex items-center gap-3">
                <span className="w-20 text-sm font-medium">{v.dia}</span>
                <div className="flex-1 h-6 bg-zinc-100 rounded overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-green-500 to-green-600 flex items-center justify-end pr-2"
                    style={{ width: `${(v.ventas / maxVentaDia) * 100}%` }}
                  >
                    <span className="text-xs text-white font-medium">{formatCurrency(v.ventas)}</span>
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// ============ TAB 5: MESAS Y COMENSALES ============
function MesasComensales({ servers, selectedServer, setSelectedServer, selectedSucursal, setSelectedSucursal, sucursales }) {
  const [loading, setLoading] = useState(false);
  const [datosUnidad, setDatosUnidad] = useState(null);
  const [rotacionPorMesa, setRotacionPorMesa] = useState([]);

  const cargarDatos = async () => {
    if (!selectedServer || !selectedSucursal) return;
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/comercial/mesas/${selectedServer}`, {
        params: { sucursal: selectedSucursal },
        headers: { Authorization: `Bearer ${token}` }
      });
      setDatosUnidad(response.data.unidad);
      setRotacionPorMesa(response.data.rotacion || []);
    } catch (error) {
      console.error('Error cargando mesas:', error);
      toast.error('Error al cargar datos de mesas');
      setDatosUnidad(null);
      setRotacionPorMesa([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedServer && selectedSucursal) cargarDatos();
  }, [selectedServer, selectedSucursal]);

  return (
    <div className="space-y-4">
      {/* Filtros */}
      <Card className="border">
        <CardContent className="py-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex-1 min-w-[180px] max-w-xs">
              <Label className="text-xs mb-1 block">Servidor</Label>
              <Select value={selectedServer} onValueChange={setSelectedServer}>
                <SelectTrigger><SelectValue placeholder="Seleccionar" /></SelectTrigger>
                <SelectContent>{servers.map(s => <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="flex-1 min-w-[180px] max-w-xs">
              <Label className="text-xs mb-1 block">Sucursal</Label>
              <Select value={selectedSucursal} onValueChange={setSelectedSucursal} disabled={!selectedServer}>
                <SelectTrigger><SelectValue placeholder={selectedServer ? "Seleccionar" : "Selecciona servidor"} /></SelectTrigger>
                <SelectContent>{sucursales.map(s => <SelectItem key={s.codigo || s.nombre} value={s.nombre}>{s.nombre}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <Button onClick={cargarDatos} disabled={loading} className="mt-5">
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Utensils className="h-4 w-4 mr-2" />}
              Actualizar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* KPIs de la Unidad */}
      {datosUnidad && (
        <>
          <Card className="border bg-gradient-to-r from-zinc-800 to-zinc-900 text-white">
            <CardHeader className="py-3">
              <CardTitle className="text-lg">{datosUnidad.nombre}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="text-center">
                  <p className="text-3xl font-bold">{datosUnidad.total_mesas}</p>
                  <p className="text-xs text-zinc-400">Mesas</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold">{datosUnidad.capacidad_total}</p>
                  <p className="text-xs text-zinc-400">Capacidad</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-green-400">{datosUnidad.rotacion_promedio}x</p>
                  <p className="text-xs text-zinc-400">Rotación</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-blue-400">{formatCurrency(datosUnidad.ticket_promedio)}</p>
                  <p className="text-xs text-zinc-400">Ticket Prom.</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-purple-400">{datosUnidad.pax_promedio}</p>
                  <p className="text-xs text-zinc-400">PAX Prom.</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="grid md:grid-cols-3 gap-4">
            <Card className="border">
              <CardContent className="py-4 text-center">
                <p className="text-xs text-zinc-500">Cheque Promedio</p>
                <p className="text-2xl font-bold text-green-600">{formatCurrency(datosUnidad.cheque_promedio)}</p>
              </CardContent>
            </Card>
            <Card className="border">
              <CardContent className="py-4 text-center">
                <p className="text-xs text-zinc-500">Vueltas por Día</p>
                <p className="text-2xl font-bold text-blue-600">{datosUnidad.vueltas_por_dia}</p>
              </CardContent>
            </Card>
            <Card className="border">
              <CardContent className="py-4 text-center">
                <p className="text-xs text-zinc-500">Vueltas Hora Pico</p>
                <p className="text-2xl font-bold text-orange-600">{datosUnidad.vueltas_por_hora_pico}</p>
              </CardContent>
            </Card>
          </div>
        </>
      )}

      {/* Rotación por Mesa */}
      {rotacionPorMesa.length > 0 && (
        <Card className="border">
          <CardHeader className="py-3">
            <CardTitle className="text-base">Rotación por Mesa (Mes Actual)</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="max-h-[300px] overflow-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-zinc-200">
                  <tr>
                    <th className="py-2 px-3 text-left">Mesa</th>
                    <th className="py-2 px-3 text-center">Capacidad</th>
                    <th className="py-2 px-3 text-center">Vueltas</th>
                    <th className="py-2 px-3 text-center">% Ocupación</th>
                  </tr>
                </thead>
                <tbody>
                  {rotacionPorMesa.map((m, idx) => (
                    <tr key={idx} className="border-b">
                      <td className="py-2 px-3 font-medium">{m.mesa}</td>
                      <td className="py-2 px-3 text-center">{m.capacidad} personas</td>
                      <td className="py-2 px-3 text-center font-bold">{m.vueltas}</td>
                      <td className="py-2 px-3">
                        <div className="flex items-center justify-center gap-2">
                          <Progress value={m.ocupacion} className="w-20 h-2" />
                          <span className={`text-sm ${m.ocupacion >= 80 ? 'text-green-600' : m.ocupacion >= 60 ? 'text-yellow-600' : 'text-red-600'}`}>
                            {m.ocupacion}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ============ TAB 6: REPORTE DE PAX (Nuevo) ============
function ReportePax({ servers, selectedServer, setSelectedServer, selectedSucursal, setSelectedSucursal, sucursales }) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [viewMode, setViewMode] = useState('vendedor'); // 'vendedor' o 'ticket'
  const [expandedRows, setExpandedRows] = useState(new Set());
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: 'total', direction: 'desc' });

  const cargarDatos = async () => {
    if (!selectedServer || !selectedSucursal) {
      toast.error('Selecciona servidor y sucursal');
      return;
    }
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/comercial/reporte-pax/${selectedServer}`, {
        params: { sucursal: selectedSucursal, fecha: selectedDate, agrupacion: viewMode },
        headers: { Authorization: `Bearer ${token}` }
      });
      setData(response.data);
      setExpandedRows(new Set());
    } catch (error) {
      console.error('Error cargando reporte PAX:', error);
      toast.error('Error al cargar reporte de PAX');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedServer && selectedSucursal) {
      cargarDatos();
    }
  }, [selectedServer, selectedSucursal, selectedDate, viewMode]);

  const toggleRow = (id) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedRows(newExpanded);
  };

  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  // Filtrar y ordenar datos
  const filteredData = React.useMemo(() => {
    if (!data?.items) return [];
    let items = [...data.items];
    
    // Filtrar por búsqueda
    if (searchTerm) {
      items = items.filter(item => 
        item.nombre?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.folio?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    // Ordenar
    items.sort((a, b) => {
      const aVal = a[sortConfig.key] || 0;
      const bVal = b[sortConfig.key] || 0;
      return sortConfig.direction === 'asc' ? aVal - bVal : bVal - aVal;
    });
    
    return items;
  }, [data, searchTerm, sortConfig]);

  const SortableHeader = ({ label, sortKey, className = '' }) => (
    <th 
      className={`py-2 px-3 cursor-pointer hover:bg-zinc-700 transition-colors ${className}`}
      onClick={() => handleSort(sortKey)}
    >
      <div className="flex items-center gap-1">
        {label}
        {sortConfig.key === sortKey && (
          sortConfig.direction === 'asc' ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />
        )}
      </div>
    </th>
  );

  return (
    <div className="space-y-4">
      {/* Filtros */}
      <Card className="border">
        <CardContent className="py-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex-1 min-w-[180px] max-w-xs">
              <Label className="text-xs mb-1 block">Servidor</Label>
              <Select value={selectedServer} onValueChange={setSelectedServer}>
                <SelectTrigger><SelectValue placeholder="Seleccionar" /></SelectTrigger>
                <SelectContent>
                  {servers.map(s => <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="flex-1 min-w-[180px] max-w-xs">
              <Label className="text-xs mb-1 block">Sucursal</Label>
              <Select value={selectedSucursal} onValueChange={setSelectedSucursal} disabled={!selectedServer}>
                <SelectTrigger><SelectValue placeholder={selectedServer ? "Seleccionar" : "Selecciona servidor"} /></SelectTrigger>
                <SelectContent>
                  {sucursales.map(s => <SelectItem key={s.codigo || s.nombre} value={s.nombre}>{s.nombre}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="min-w-[150px]">
              <Label className="text-xs mb-1 block">Fecha</Label>
              <Input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="w-full"
              />
            </div>
            <div className="min-w-[150px]">
              <Label className="text-xs mb-1 block">Agrupar por</Label>
              <Select value={viewMode} onValueChange={setViewMode}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="vendedor">
                    <div className="flex items-center gap-2">
                      <UserCheck className="h-4 w-4" /> Vendedor
                    </div>
                  </SelectItem>
                  <SelectItem value="ticket">
                    <div className="flex items-center gap-2">
                      <Receipt className="h-4 w-4" /> Cheque/Ticket
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={cargarDatos} disabled={loading || !selectedServer || !selectedSucursal} className="mt-5">
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
              Actualizar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Resumen KPIs */}
      {data?.resumen && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <Card className="border bg-gradient-to-br from-purple-50 to-white">
            <CardContent className="py-3 text-center">
              <p className="text-xs text-zinc-500">PAX Total</p>
              <p className="text-2xl font-bold text-purple-600">{formatNumber(data.resumen.pax_total)}</p>
            </CardContent>
          </Card>
          <Card className="border bg-gradient-to-br from-green-50 to-white">
            <CardContent className="py-3 text-center">
              <p className="text-xs text-zinc-500">Ventas Total</p>
              <p className="text-xl font-bold text-green-600">{formatCurrency(data.resumen.ventas_total)}</p>
            </CardContent>
          </Card>
          <Card className="border bg-gradient-to-br from-blue-50 to-white">
            <CardContent className="py-3 text-center">
              <p className="text-xs text-zinc-500">Pax Promedio</p>
              <p className="text-xl font-bold text-blue-600">{formatCurrency(data.resumen.pax_promedio)}</p>
            </CardContent>
          </Card>
          <Card className="border bg-gradient-to-br from-yellow-50 to-white">
            <CardContent className="py-3 text-center">
              <p className="text-xs text-zinc-500">Cheque Promedio</p>
              <p className="text-xl font-bold text-yellow-600">{formatCurrency(data.resumen.cheque_promedio)}</p>
            </CardContent>
          </Card>
          <Card className="border bg-gradient-to-br from-zinc-50 to-white">
            <CardContent className="py-3 text-center">
              <p className="text-xs text-zinc-500">Total Cheques</p>
              <p className="text-xl font-bold text-zinc-600">{data.resumen.total_cheques}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Comparativo vs Mes/Año anterior */}
      {data?.comparativo && (
        <Card className="border">
          <CardHeader className="py-2">
            <CardTitle className="text-sm">Comparativo PAX</CardTitle>
          </CardHeader>
          <CardContent className="py-2">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="p-3 bg-zinc-50 rounded">
                <p className="text-xs text-zinc-500 mb-1">vs Día Anterior</p>
                <p className={`text-lg font-bold ${data.comparativo.vs_dia_anterior >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatPercent(data.comparativo.vs_dia_anterior)}
                </p>
              </div>
              <div className="p-3 bg-zinc-50 rounded">
                <p className="text-xs text-zinc-500 mb-1">vs Mes Anterior (mismo día)</p>
                <p className={`text-lg font-bold ${data.comparativo.vs_mes_anterior >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatPercent(data.comparativo.vs_mes_anterior)}
                </p>
              </div>
              <div className="p-3 bg-zinc-50 rounded">
                <p className="text-xs text-zinc-500 mb-1">vs Año Anterior (mismo día)</p>
                <p className={`text-lg font-bold ${data.comparativo.vs_ano_anterior >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatPercent(data.comparativo.vs_ano_anterior)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Barra de búsqueda y acciones */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
          <Input
            placeholder={`Buscar ${viewMode === 'vendedor' ? 'vendedor' : 'folio'}...`}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => toast.info('Exportación a Excel próximamente')}>
            <FileSpreadsheet className="h-4 w-4 mr-1" /> Excel
          </Button>
          <Button variant="outline" size="sm" onClick={() => toast.info('Exportación a PDF próximamente')}>
            <FileText className="h-4 w-4 mr-1" /> PDF
          </Button>
        </div>
      </div>

      {/* Tabla con drill-down */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
        </div>
      ) : filteredData.length > 0 ? (
        <Card className="border">
          <CardContent className="p-0">
            <div className="max-h-[500px] overflow-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-zinc-800 text-white z-10">
                  <tr>
                    <th className="py-2 px-3 text-left w-8"></th>
                    <SortableHeader label={viewMode === 'vendedor' ? 'Vendedor' : 'Folio'} sortKey="nombre" className="text-left" />
                    <SortableHeader label="PAX" sortKey="pax" className="text-center" />
                    <SortableHeader label="Total" sortKey="total" className="text-right" />
                    <SortableHeader label="Pax Promedio" sortKey="pax_promedio" className="text-right" />
                    {viewMode === 'vendedor' && <SortableHeader label="Cheques" sortKey="num_cheques" className="text-center" />}
                  </tr>
                </thead>
                <tbody>
                  {filteredData.map((item, idx) => (
                    <React.Fragment key={item.id || idx}>
                      {/* Fila principal */}
                      <tr 
                        className={`border-b cursor-pointer hover:bg-zinc-50 transition-colors ${expandedRows.has(item.id) ? 'bg-blue-50' : ''}`}
                        onClick={() => item.detalle?.length > 0 && toggleRow(item.id)}
                      >
                        <td className="py-2 px-3">
                          {item.detalle?.length > 0 && (
                            <button className="p-1 hover:bg-zinc-200 rounded">
                              {expandedRows.has(item.id) ? 
                                <ChevronDown className="h-4 w-4 text-blue-600" /> : 
                                <ChevronRight className="h-4 w-4 text-zinc-400" />
                              }
                            </button>
                          )}
                        </td>
                        <td className="py-2 px-3 font-medium">
                          {viewMode === 'vendedor' ? (
                            <div className="flex items-center gap-2">
                              <UserCheck className="h-4 w-4 text-zinc-400" />
                              {item.nombre}
                            </div>
                          ) : (
                            <span className="font-mono">{item.folio}</span>
                          )}
                        </td>
                        <td className="py-2 px-3 text-center">
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-semibold">
                            <Users className="h-3 w-3" /> {item.pax}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-right font-semibold text-green-600">
                          {formatCurrency(item.total)}
                        </td>
                        <td className="py-2 px-3 text-right font-semibold text-blue-600">
                          {formatCurrency(item.pax_promedio)}
                        </td>
                        {viewMode === 'vendedor' && (
                          <td className="py-2 px-3 text-center text-zinc-500">
                            {item.num_cheques}
                          </td>
                        )}
                      </tr>
                      
                      {/* Filas expandidas (detalle) */}
                      {expandedRows.has(item.id) && item.detalle?.map((det, detIdx) => (
                        <tr key={`${item.id}-${detIdx}`} className="bg-zinc-50 border-b border-zinc-100">
                          <td className="py-1 px-3"></td>
                          <td className="py-1 px-3 pl-10 text-sm text-zinc-600">
                            {viewMode === 'vendedor' ? (
                              <span className="font-mono text-xs">{det.folio}</span>
                            ) : (
                              <span>{det.vendedor}</span>
                            )}
                          </td>
                          <td className="py-1 px-3 text-center text-sm">{det.pax}</td>
                          <td className="py-1 px-3 text-right text-sm text-green-600">{formatCurrency(det.total)}</td>
                          <td className="py-1 px-3 text-right text-sm text-blue-600">{formatCurrency(det.pax_promedio)}</td>
                          {viewMode === 'vendedor' && <td className="py-1 px-3"></td>}
                        </tr>
                      ))}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      ) : data && (
        <div className="text-center py-12 text-zinc-500">
          <Users className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p>No hay datos de PAX para esta fecha</p>
        </div>
      )}

      {/* Tip de uso */}
      {filteredData.length > 0 && (
        <p className="text-xs text-zinc-500 italic text-center">
          💡 Haz clic en una fila para expandir/contraer el detalle. Usa los botones de ordenamiento en las cabeceras.
        </p>
      )}
    </div>
  );
}

// ============ VENTAS A PRECIOS CONSTANTES ============
function VentasPreciosConstantes({ servers, selectedServer, setSelectedServer, selectedSucursal, setSelectedSucursal, sucursales }) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  
  // Estado local para sucursales del servidor seleccionado
  const [localSucursales, setLocalSucursales] = useState([]);
  const [localSucursal, setLocalSucursal] = useState('all');
  const [loadingSucursales, setLoadingSucursales] = useState(false);
  
  // Estado para comparación con año anterior y serie histórica
  const [dataAnioAnterior, setDataAnioAnterior] = useState(null);
  const [serieHistorica, setSerieHistorica] = useState([]);
  const [loadingHistorico, setLoadingHistorico] = useState(false);
  
  // Filtros
  const [periodoActual, setPeriodoActual] = useState(() => {
    // Por defecto usar Enero 2026 (datos más recientes confirmados)
    return '2026-01';
  });
  const [periodoBase, setPeriodoBase] = useState(() => {
    return '2025-01';
  });
  const [modoComparacion, setModoComparacion] = useState('manual'); // manual, auto (año anterior)
  const [granularidad, setGranularidad] = useState('categoria');
  
  // Multiselección de meses
  const [mesesActual, setMesesActual] = useState([1]); // Enero por defecto
  const [mesesBase, setMesesBase] = useState([1]);
  const [anioActual, setAnioActual] = useState(2026); // Año con datos recientes
  const [anioBase, setAnioBase] = useState(2025);

  const meses = [
    { num: 1, nombre: 'Ene' }, { num: 2, nombre: 'Feb' }, { num: 3, nombre: 'Mar' },
    { num: 4, nombre: 'Abr' }, { num: 5, nombre: 'May' }, { num: 6, nombre: 'Jun' },
    { num: 7, nombre: 'Jul' }, { num: 8, nombre: 'Ago' }, { num: 9, nombre: 'Sep' },
    { num: 10, nombre: 'Oct' }, { num: 11, nombre: 'Nov' }, { num: 12, nombre: 'Dic' }
  ];

  const aniosDisponibles = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i);

  // Cargar sucursales cuando cambia el servidor
  useEffect(() => {
    if (selectedServer) {
      cargarSucursales();
    }
  }, [selectedServer]);

  // Auto-cargar análisis cuando cambia la sucursal
  useEffect(() => {
    if (selectedServer && localSucursal) {
      cargarAnalisis();
    }
  }, [localSucursal]);

  const cargarSucursales = async () => {
    setLoadingSucursales(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/comercial/sucursales/${selectedServer}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setLocalSucursales(response.data.sucursales || []);
      setLocalSucursal('all'); // Reset a "todas"
    } catch (err) {
      console.error('Error cargando sucursales:', err);
      setLocalSucursales([{ id: 'all', nombre: 'Todas' }]);
    } finally {
      setLoadingSucursales(false);
    }
  };

  const toggleMes = (mes, tipo) => {
    if (tipo === 'actual') {
      if (mesesActual.includes(mes)) {
        if (mesesActual.length > 1) {
          setMesesActual(mesesActual.filter(m => m !== mes));
        }
      } else {
        setMesesActual([...mesesActual, mes].sort((a, b) => a - b));
      }
    } else {
      if (mesesBase.includes(mes)) {
        if (mesesBase.length > 1) {
          setMesesBase(mesesBase.filter(m => m !== mes));
        }
      } else {
        setMesesBase([...mesesBase, mes].sort((a, b) => a - b));
      }
    }
  };

  const cargarAnalisis = async () => {
    if (!selectedServer) {
      return; // No mostrar error, simplemente no cargar si no hay servidor
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('token');
      
      // Construir períodos
      let pActual, pBase;
      if (modoComparacion === 'auto') {
        // Automático: mismo mes del año anterior
        pActual = mesesActual.map(m => `${anioActual}-${String(m).padStart(2, '0')}`).join(',');
        pBase = mesesActual.map(m => `${anioActual - 1}-${String(m).padStart(2, '0')}`).join(',');
      } else {
        // Manual: selección libre
        pActual = mesesActual.map(m => `${anioActual}-${String(m).padStart(2, '0')}`).join(',');
        pBase = mesesBase.map(m => `${anioBase}-${String(m).padStart(2, '0')}`).join(',');
      }
      
      const response = await axios.get(`${API_URL}/api/comercial/precios-constantes/${selectedServer}`, {
        params: {
          periodo_actual: pActual,
          periodo_base: pBase,
          granularidad: granularidad,
          sucursal: localSucursal
        },
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setData(response.data);
      
      // Cargar datos del año anterior para comparar crecimiento real
      const pAnioAnterior = mesesActual.map(m => `${anioActual - 1}-${String(m).padStart(2, '0')}`).join(',');
      const pBaseAnterior = mesesActual.map(m => `${anioActual - 2}-${String(m).padStart(2, '0')}`).join(',');
      
      try {
        const responseAnterior = await axios.get(`${API_URL}/api/comercial/precios-constantes/${selectedServer}`, {
          params: {
            periodo_actual: pAnioAnterior,
            periodo_base: pBaseAnterior,
            granularidad: 'categoria',
            sucursal: localSucursal
          },
          headers: { Authorization: `Bearer ${token}` }
        });
        setDataAnioAnterior(responseAnterior.data);
      } catch (e) {
        console.log('No hay datos del año anterior');
        setDataAnioAnterior(null);
      }
      
      // Cargar serie histórica de 5 años
      cargarSerieHistorica(token);
      
    } catch (err) {
      console.error('Error:', err);
      setError(err.response?.data?.detail || 'Error al cargar análisis');
      toast.error('Error al cargar análisis de precios constantes');
    } finally {
      setLoading(false);
    }
  };

  const cargarSerieHistorica = async (token) => {
    setLoadingHistorico(true);
    const serie = [];
    const anioBase = anioActual - 5; // Año más antiguo como referencia
    
    try {
      // Cargar datos de los últimos 5 años usando el año -5 como base de precios
      for (let i = 0; i < 5; i++) {
        const anio = anioActual - 4 + i; // Del -4 al actual
        const pPeriodo = mesesActual.map(m => `${anio}-${String(m).padStart(2, '0')}`).join(',');
        const pRef = mesesActual.map(m => `${anioBase}-${String(m).padStart(2, '0')}`).join(',');
        
        try {
          const res = await axios.get(`${API_URL}/api/comercial/precios-constantes/${selectedServer}`, {
            params: {
              periodo_actual: pPeriodo,
              periodo_base: pRef,
              granularidad: 'categoria',
              sucursal: localSucursal
            },
            headers: { Authorization: `Bearer ${token}` }
          });
          
          serie.push({
            anio: anio,
            ventas_actuales: res.data.kpis?.ventas_actuales || 0,
            ventas_constantes: res.data.kpis?.ventas_constantes || 0,
            efecto_precio: res.data.kpis?.efecto_precio || 0
          });
        } catch (e) {
          serie.push({
            anio: anio,
            ventas_actuales: 0,
            ventas_constantes: 0,
            efecto_precio: 0
          });
        }
      }
      
      setSerieHistorica(serie);
    } catch (err) {
      console.error('Error cargando serie histórica:', err);
    } finally {
      setLoadingHistorico(false);
    }
  };

  const getVariacionClass = (valor) => {
    if (valor > 0) return 'text-red-600';
    if (valor < 0) return 'text-green-600';
    return 'text-zinc-600';
  };

  return (
    <div className="space-y-4" data-testid="precios-constantes">
      {/* Filtros */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <Scale className="h-5 w-5 text-blue-600" />
            Análisis de Ventas a Precios Constantes
          </CardTitle>
          <p className="text-sm text-zinc-500">
            Compara ventas eliminando el efecto inflacionario de los cambios de precios
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Selectores de servidor y sucursal */}
          <div className="flex gap-4 items-end flex-wrap">
            <div className="w-56">
              <Label className="text-xs">Servidor</Label>
              <Select value={selectedServer} onValueChange={setSelectedServer}>
                <SelectTrigger><SelectValue placeholder="Seleccionar servidor" /></SelectTrigger>
                <SelectContent>
                  {servers.filter(s => s.active).map(s => (
                    <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            {/* Selector de sucursal (solo visible si hay servidor seleccionado y es MPRO) */}
            {selectedServer && localSucursales.length > 1 && (
              <div className="w-56">
                <Label className="text-xs">Sucursal</Label>
                <Select 
                  value={localSucursal} 
                  onValueChange={setLocalSucursal}
                  disabled={loadingSucursales}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={loadingSucursales ? "Cargando..." : "Seleccionar sucursal"} />
                  </SelectTrigger>
                  <SelectContent>
                    {localSucursales.map(s => (
                      <SelectItem key={s.id} value={s.id}>{s.nombre}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            
            <div className="w-48">
              <Label className="text-xs">Modo de Comparación</Label>
              <Select value={modoComparacion} onValueChange={setModoComparacion}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="manual">Selección Manual</SelectItem>
                  <SelectItem value="auto">Año Anterior (auto)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="w-48">
              <Label className="text-xs">Granularidad</Label>
              <Select value={granularidad} onValueChange={setGranularidad}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="categoria">Por Categoría</SelectItem>
                  <SelectItem value="familia">Por Familia</SelectItem>
                  <SelectItem value="producto">Por Producto</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Período Actual */}
          <div className="border rounded-lg p-4 bg-blue-50/50">
            <div className="flex items-center gap-3 mb-3">
              <Label className="text-sm font-medium">Período Actual (Ventas a Analizar)</Label>
              <Select value={String(anioActual)} onValueChange={(v) => setAnioActual(Number(v))}>
                <SelectTrigger className="w-24 h-8"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {aniosDisponibles.map(a => <SelectItem key={a} value={String(a)}>{a}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="flex gap-1 flex-wrap">
              {meses.map(m => (
                <Button
                  key={m.num}
                  size="sm"
                  variant={mesesActual.includes(m.num) ? 'default' : 'outline'}
                  className="w-12 h-8 text-xs"
                  onClick={() => toggleMes(m.num, 'actual')}
                >
                  {m.nombre}
                </Button>
              ))}
            </div>
          </div>

          {/* Período Base (solo si es manual) */}
          {modoComparacion === 'manual' && (
            <div className="border rounded-lg p-4 bg-orange-50/50">
              <div className="flex items-center gap-3 mb-3">
                <Label className="text-sm font-medium">Período Base (Precios de Referencia)</Label>
                <Select value={String(anioBase)} onValueChange={(v) => setAnioBase(Number(v))}>
                  <SelectTrigger className="w-24 h-8"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {aniosDisponibles.map(a => <SelectItem key={a} value={String(a)}>{a}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex gap-1 flex-wrap">
                {meses.map(m => (
                  <Button
                    key={m.num}
                    size="sm"
                    variant={mesesBase.includes(m.num) ? 'default' : 'outline'}
                    className="w-12 h-8 text-xs"
                    onClick={() => toggleMes(m.num, 'base')}
                  >
                    {m.nombre}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {modoComparacion === 'auto' && (
            <div className="bg-zinc-100 rounded-lg p-3 text-sm text-zinc-600">
              <strong>Modo Automático:</strong> Se compararán las ventas de {mesesActual.map(m => meses[m-1].nombre).join(', ')} {anioActual} 
              {' '}usando precios de {mesesActual.map(m => meses[m-1].nombre).join(', ')} {anioActual - 1}
            </div>
          )}

          <div className="flex justify-end">
            <Button onClick={cargarAnalisis} disabled={loading || !selectedServer}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
              Analizar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Error */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="py-4">
            <p className="text-red-600 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              {error}
            </p>
          </CardContent>
        </Card>
      )}

      {/* KPIs */}
      {data && (
        <>
          <div className="grid grid-cols-5 gap-4">
            <Card>
              <CardContent className="pt-4">
                <p className="text-xs text-zinc-500">Ventas Actuales</p>
                <p className="text-xl font-bold text-zinc-900">{formatCurrency(data.kpis.ventas_actuales)}</p>
                <p className="text-xs text-zinc-400">Precios del período seleccionado</p>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="pt-4">
                <p className="text-xs text-zinc-500">Ventas a Precios Constantes</p>
                <p className="text-xl font-bold text-blue-600">{formatCurrency(data.kpis.ventas_constantes)}</p>
                <p className="text-xs text-zinc-400">Valuadas con precios base</p>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="pt-4">
                <p className="text-xs text-zinc-500">Efecto Precio (Inflación)</p>
                <p className={`text-xl font-bold ${getVariacionClass(data.kpis.efecto_precio)}`}>
                  {formatCurrency(data.kpis.efecto_precio)}
                </p>
                <p className="text-xs text-zinc-400">
                  {data.kpis.efecto_inflacion_pct >= 0 ? '+' : ''}{data.kpis.efecto_inflacion_pct}%
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="pt-4">
                <p className="text-xs text-zinc-500">Productos Nuevos</p>
                <p className="text-xl font-bold text-green-600">{data.kpis.productos_nuevos}</p>
                <p className="text-xs text-zinc-400">No existían en período base</p>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="pt-4">
                <p className="text-xs text-zinc-500">Productos Descontinuados</p>
                <p className="text-xl font-bold text-orange-600">{data.kpis.productos_descontinuados}</p>
                <p className="text-xs text-zinc-400">Ya no se venden</p>
              </CardContent>
            </Card>
          </div>

          {/* Interpretación */}
          <Card className="bg-gradient-to-r from-blue-50 to-indigo-50">
            <CardContent className="py-4">
              <div className="flex items-start gap-3">
                <Scale className="h-6 w-6 text-blue-600 mt-1" />
                <div>
                  <h4 className="font-medium text-zinc-900">Interpretación del Análisis</h4>
                  <p className="text-sm text-zinc-600 mt-1">
                    {data.kpis.efecto_precio > 0 ? (
                      <>
                        Las ventas actuales incluyen <strong>{formatCurrency(data.kpis.efecto_precio)}</strong> ({data.kpis.efecto_inflacion_pct}%) 
                        por efecto de incremento de precios. Sin este efecto inflacionario, las ventas reales serían{' '}
                        <strong>{formatCurrency(data.kpis.ventas_constantes)}</strong>.
                      </>
                    ) : data.kpis.efecto_precio < 0 ? (
                      <>
                        Los precios han disminuido respecto al período base. Las ventas a precios constantes serían{' '}
                        <strong>{formatCurrency(data.kpis.ventas_constantes)}</strong>, {Math.abs(data.kpis.efecto_inflacion_pct)}% más que el importe actual.
                      </>
                    ) : (
                      <>No hay diferencia significativa en precios entre ambos períodos.</>
                    )}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Crecimiento Real vs Año Anterior */}
          {dataAnioAnterior && (
            <Card className="border-2 border-indigo-200">
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-indigo-600" />
                  Crecimiento Real (vs Año Anterior)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-4 gap-4">
                  {/* Crecimiento Nominal */}
                  <div className="text-center p-4 bg-zinc-50 rounded-lg">
                    <p className="text-xs text-zinc-500 mb-1">Crecimiento Nominal</p>
                    <p className={`text-2xl font-bold ${
                      ((data.kpis.ventas_actuales - dataAnioAnterior.kpis?.ventas_actuales) / (dataAnioAnterior.kpis?.ventas_actuales || 1) * 100) >= 0 
                        ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {dataAnioAnterior.kpis?.ventas_actuales > 0 
                        ? `${((data.kpis.ventas_actuales - dataAnioAnterior.kpis.ventas_actuales) / dataAnioAnterior.kpis.ventas_actuales * 100).toFixed(1)}%`
                        : 'N/A'
                      }
                    </p>
                    <p className="text-xs text-zinc-400">Incluye efecto precio</p>
                  </div>

                  {/* Crecimiento Real (Precios Constantes) */}
                  <div className="text-center p-4 bg-indigo-50 rounded-lg border-2 border-indigo-300">
                    <p className="text-xs text-indigo-700 mb-1 font-medium">Crecimiento Real</p>
                    <p className={`text-2xl font-bold ${
                      ((data.kpis.ventas_constantes - dataAnioAnterior.kpis?.ventas_constantes) / (dataAnioAnterior.kpis?.ventas_constantes || 1) * 100) >= 0 
                        ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {dataAnioAnterior.kpis?.ventas_constantes > 0 
                        ? `${((data.kpis.ventas_constantes - dataAnioAnterior.kpis.ventas_constantes) / dataAnioAnterior.kpis.ventas_constantes * 100).toFixed(1)}%`
                        : 'N/A'
                      }
                    </p>
                    <p className="text-xs text-indigo-500">Sin efecto inflacionario</p>
                  </div>

                  {/* Ventas Año Anterior */}
                  <div className="text-center p-4 bg-zinc-50 rounded-lg">
                    <p className="text-xs text-zinc-500 mb-1">Ventas {anioActual - 1}</p>
                    <p className="text-xl font-bold text-zinc-700">
                      {formatCurrency(dataAnioAnterior.kpis?.ventas_actuales || 0)}
                    </p>
                    <p className="text-xs text-zinc-400">Año anterior</p>
                  </div>

                  {/* Diferencia en $ */}
                  <div className="text-center p-4 bg-zinc-50 rounded-lg">
                    <p className="text-xs text-zinc-500 mb-1">Diferencia Real</p>
                    <p className={`text-xl font-bold ${
                      (data.kpis.ventas_constantes - (dataAnioAnterior.kpis?.ventas_constantes || 0)) >= 0 
                        ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatCurrency(data.kpis.ventas_constantes - (dataAnioAnterior.kpis?.ventas_constantes || 0))}
                    </p>
                    <p className="text-xs text-zinc-400">A precios constantes</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Gráfico Histórico de 5 Años */}
          {serieHistorica.length > 0 && serieHistorica.some(s => s.ventas_actuales > 0) && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-purple-600" />
                  Histórico de 5 Años: Ventas Actuales vs Precios Constantes
                  {loadingHistorico && <Loader2 className="h-4 w-4 animate-spin ml-2" />}
                </CardTitle>
                <p className="text-xs text-zinc-500">
                  Comparación usando precios base del año {anioActual - 5} para eliminar el efecto inflacionario acumulado
                </p>
              </CardHeader>
              <CardContent>
                <div style={{ width: '100%', height: 350, minHeight: 350 }}>
                  <ResponsiveContainer width="100%" height={350}>
                    <BarChart
                      data={serieHistorica}
                      margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis 
                        dataKey="anio" 
                        tick={{ fontSize: 12 }}
                        tickFormatter={(value) => value.toString()}
                      />
                      <YAxis 
                        tick={{ fontSize: 11 }}
                        tickFormatter={(value) => {
                          if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
                          if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`;
                          return `$${value}`;
                        }}
                      />
                      <Tooltip 
                        formatter={(value, name) => [
                          formatCurrency(value),
                          name === 'ventas_actuales' ? 'Ventas Actuales' : 
                          name === 'ventas_constantes' ? 'Precios Constantes' : 'Efecto Precio'
                        ]}
                        labelFormatter={(label) => `Año ${label}`}
                        contentStyle={{ 
                          backgroundColor: 'white', 
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                        }}
                      />
                      <Legend 
                        formatter={(value) => 
                          value === 'ventas_actuales' ? 'Ventas Actuales' : 
                          value === 'ventas_constantes' ? 'Precios Constantes' : 'Efecto Precio'
                        }
                      />
                      <Bar 
                        dataKey="ventas_actuales" 
                        fill="#3b82f6" 
                        name="ventas_actuales"
                        radius={[4, 4, 0, 0]}
                      />
                      <Bar 
                        dataKey="ventas_constantes" 
                        fill="#8b5cf6" 
                        name="ventas_constantes"
                        radius={[4, 4, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Leyenda de interpretación */}
                <div className="mt-4 grid grid-cols-3 gap-3 text-center">
                  {serieHistorica.filter(s => s.ventas_actuales > 0).slice(-3).map((item, idx) => (
                    <div key={idx} className="p-3 bg-zinc-50 rounded-lg">
                      <p className="text-sm font-medium text-zinc-700">{item.anio}</p>
                      <p className="text-xs text-zinc-500">
                        Efecto Inflación: <span className={item.efecto_precio > 0 ? 'text-red-600 font-medium' : 'text-green-600 font-medium'}>
                          {formatCurrency(item.efecto_precio)}
                        </span>
                      </p>
                      <p className="text-xs text-zinc-400">
                        {item.ventas_actuales > 0 && item.ventas_constantes > 0 
                          ? `${((item.efecto_precio / item.ventas_constantes) * 100).toFixed(1)}% del total`
                          : '-'
                        }
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Tabla de resultados */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">
                Detalle por {granularidad === 'categoria' ? 'Categoría' : granularidad === 'familia' ? 'Familia' : 'Producto'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto max-h-[500px]">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-zinc-100">
                    <tr>
                      <th className="text-left p-2">{granularidad === 'producto' ? 'Producto' : 'Nombre'}</th>
                      <th className="text-right p-2">Cantidad</th>
                      <th className="text-right p-2">Importe Actual</th>
                      <th className="text-right p-2">Importe Constante</th>
                      <th className="text-right p-2">Efecto Precio</th>
                      {granularidad !== 'producto' && (
                        <>
                          <th className="text-right p-2">Nuevos</th>
                          <th className="text-right p-2">Desc.</th>
                        </>
                      )}
                      {granularidad === 'producto' && (
                        <>
                          <th className="text-right p-2">Precio Actual</th>
                          <th className="text-right p-2">Precio Base</th>
                          <th className="text-right p-2">Var. %</th>
                        </>
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {data.datos?.map((item, idx) => (
                      <tr key={idx} className="border-b hover:bg-zinc-50">
                        <td className="p-2">
                          {item.nombre || item.producto}
                          {item.es_nuevo && <span className="ml-2 px-1 py-0.5 bg-green-100 text-green-700 text-xs rounded">NUEVO</span>}
                          {item.es_descontinuado && <span className="ml-2 px-1 py-0.5 bg-orange-100 text-orange-700 text-xs rounded">DESC.</span>}
                        </td>
                        <td className="text-right p-2">{formatNumber(item.cantidad)}</td>
                        <td className="text-right p-2">{formatCurrency(item.importe_actual)}</td>
                        <td className="text-right p-2">{formatCurrency(item.importe_constante)}</td>
                        <td className={`text-right p-2 font-medium ${getVariacionClass(item.efecto_precio)}`}>
                          {formatCurrency(item.efecto_precio)}
                        </td>
                        {granularidad !== 'producto' && (
                          <>
                            <td className="text-right p-2 text-green-600">{item.productos_nuevos || 0}</td>
                            <td className="text-right p-2 text-orange-600">{item.productos_descontinuados || 0}</td>
                          </>
                        )}
                        {granularidad === 'producto' && (
                          <>
                            <td className="text-right p-2">{formatCurrency(item.precio_actual)}</td>
                            <td className="text-right p-2">{formatCurrency(item.precio_base)}</td>
                            <td className={`text-right p-2 ${getVariacionClass(item.variacion_precio_pct)}`}>
                              {item.variacion_precio_pct >= 0 ? '+' : ''}{item.variacion_precio_pct}%
                            </td>
                          </>
                        )}
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-zinc-100 font-medium">
                    <tr>
                      <td className="p-2">TOTAL</td>
                      <td className="text-right p-2">-</td>
                      <td className="text-right p-2">{formatCurrency(data.kpis.ventas_actuales)}</td>
                      <td className="text-right p-2">{formatCurrency(data.kpis.ventas_constantes)}</td>
                      <td className={`text-right p-2 ${getVariacionClass(data.kpis.efecto_precio)}`}>
                        {formatCurrency(data.kpis.efecto_precio)}
                      </td>
                      {granularidad !== 'producto' && (
                        <>
                          <td className="text-right p-2 text-green-600">{data.kpis.productos_nuevos}</td>
                          <td className="text-right p-2 text-orange-600">{data.kpis.productos_descontinuados}</td>
                        </>
                      )}
                      {granularidad === 'producto' && <td colSpan={3}></td>}
                    </tr>
                  </tfoot>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* Estado inicial */}
      {!data && !loading && !error && (
        <Card>
          <CardContent className="py-12 text-center text-zinc-500">
            <Scale className="h-16 w-16 mx-auto mb-4 opacity-30" />
            <h3 className="text-lg font-medium text-zinc-700 mb-2">Análisis de Precios Constantes</h3>
            <p className="text-sm max-w-md mx-auto">
              Selecciona un servidor, configura los períodos a comparar y haz clic en "Analizar" 
              para ver las ventas valuadas sin efecto inflacionario.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}



// ============ COMPONENTE PRINCIPAL ============
export default function Comercial() {
  const [servers, setServers] = useState([]);
  const [selectedServer, setSelectedServer] = useState('');
  const [selectedSucursal, setSelectedSucursal] = useState('');
  const [sucursales, setSucursales] = useState([]);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [showSucursalSelector, setShowSucursalSelector] = useState(true);

  // Cargar filtros guardados al inicio
  useEffect(() => {
    const savedFilters = localStorage.getItem('comercial_filters');
    if (savedFilters) {
      try {
        const filters = JSON.parse(savedFilters);
        if (filters.server) setSelectedServer(filters.server);
        if (filters.tab) setActiveTab(filters.tab);
      } catch (e) {}
    }
  }, []);

  // Guardar filtros cuando cambien
  useEffect(() => {
    if (selectedServer) {
      localStorage.setItem('comercial_filters', JSON.stringify({
        server: selectedServer,
        sucursal: selectedSucursal,
        tab: activeTab
      }));
    }
  }, [selectedServer, selectedSucursal, activeTab]);

  useEffect(() => {
    const fetchServers = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`${API_URL}/api/servers`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setServers(response.data);
      } catch (error) {
        console.error('Error:', error);
      }
    };
    fetchServers();
  }, []);

  useEffect(() => {
    if (selectedServer) {
      // Limpiar sucursal al cambiar de servidor para forzar re-carga
      setSelectedSucursal('');
      
      const fetchSucursales = async () => {
        try {
          const token = localStorage.getItem('token');
          const response = await axios.get(`${API_URL}/api/servers/${selectedServer}/sucursales`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          const sucursalesData = response.data || [];
          setSucursales(sucursalesData);
          
          // Auto-seleccionar si solo hay una sucursal (CIENFUEGOS, LA ESTELAR)
          if (sucursalesData.length === 1) {
            // Usar setTimeout para asegurar que el estado se actualice después del clear
            setTimeout(() => {
              setSelectedSucursal(sucursalesData[0].nombre);
            }, 50);
            setShowSucursalSelector(false);
          } else if (sucursalesData.length > 1) {
            setShowSucursalSelector(true);
            // Restaurar sucursal guardada si existe
            const savedFilters = localStorage.getItem('comercial_filters');
            if (savedFilters) {
              try {
                const filters = JSON.parse(savedFilters);
                if (filters.sucursal && sucursalesData.some(s => s.nombre === filters.sucursal)) {
                  setTimeout(() => {
                    setSelectedSucursal(filters.sucursal);
                  }, 50);
                }
              } catch (e) {
                // mantener vacío
              }
            }
          } else {
            setShowSucursalSelector(false);
          }
        } catch (error) {
          console.error('Error:', error);
          setSucursales([]);
          setShowSucursalSelector(false);
        }
      };
      fetchSucursales();
    } else {
      setSucursales([]);
      setShowSucursalSelector(false);
      setSelectedSucursal('');
    }
  }, [selectedServer]);

  const commonProps = { servers, selectedServer, setSelectedServer, selectedSucursal, setSelectedSucursal, sucursales, showSucursalSelector };

  return (
    <div className="space-y-4" data-testid="comercial-module">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-zinc-800">Comercial</h1>
        <p className="text-sm text-zinc-500">Análisis de ventas, rentabilidad y metas</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-7 mb-4">
          <TabsTrigger value="dashboard" className="text-xs"><BarChart3 className="h-4 w-4 mr-1" />Dashboard</TabsTrigger>
          <TabsTrigger value="constantes" className="text-xs"><Scale className="h-4 w-4 mr-1" />Precios Const.</TabsTrigger>
          <TabsTrigger value="pax" className="text-xs"><Users className="h-4 w-4 mr-1" />Reporte PAX</TabsTrigger>
          <TabsTrigger value="ticket" className="text-xs"><Award className="h-4 w-4 mr-1" />Ticket Perfecto</TabsTrigger>
          <TabsTrigger value="metas" className="text-xs"><Target className="h-4 w-4 mr-1" />Metas</TabsTrigger>
          <TabsTrigger value="tiempo" className="text-xs"><Clock className="h-4 w-4 mr-1" />Por Hora/Día</TabsTrigger>
          <TabsTrigger value="mesas" className="text-xs"><Utensils className="h-4 w-4 mr-1" />Mesas</TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard"><DashboardVentas {...commonProps} /></TabsContent>
        <TabsContent value="constantes"><VentasPreciosConstantes {...commonProps} /></TabsContent>
        <TabsContent value="pax"><ReportePax {...commonProps} /></TabsContent>
        <TabsContent value="ticket"><TicketPerfecto {...commonProps} /></TabsContent>
        <TabsContent value="metas"><MetasVentas {...commonProps} /></TabsContent>
        <TabsContent value="tiempo"><VentasPorTiempo {...commonProps} /></TabsContent>
        <TabsContent value="mesas"><MesasComensales {...commonProps} /></TabsContent>
      </Tabs>
    </div>
  );
}
