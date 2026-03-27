import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Progress } from '../components/ui/progress';
import { toast } from 'sonner';
import { 
  Loader2, TrendingUp, TrendingDown, DollarSign, Users, Clock, Target,
  AlertTriangle, BarChart3, PieChart, ShoppingBag, Utensils, Coffee,
  Wine, Award, RefreshCw, Calendar, ArrowUpRight, ArrowDownRight,
  Receipt, ChevronLeft, ChevronRight, X, Search
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const formatNumber = (num) => {
  if (num === null || num === undefined) return '-';
  return new Intl.NumberFormat('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(num);
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
    pax: { titulo: 'Detalle de Comensales', icono: Users, color: 'text-purple-600' },
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
function DashboardVentas({ servers, selectedServer, setSelectedServer, selectedSucursal, setSelectedSucursal, sucursales }) {
  const [loading, setLoading] = useState(false);
  const [kpis, setKpis] = useState(null);
  const [comparativo, setComparativo] = useState(null);
  const [alertas, setAlertas] = useState([]);
  const [periodo, setPeriodo] = useState('mes'); // mes, semana, dia
  const [detalleModal, setDetalleModal] = useState({ open: false, tipo: null });

  const cargarDashboard = async () => {
    if (!selectedServer || !selectedSucursal) {
      toast.error('Selecciona servidor y sucursal');
      return;
    }
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/comercial/dashboard/${selectedServer}`, {
        params: { sucursal: selectedSucursal, periodo },
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
  }, [selectedServer, selectedSucursal, periodo]);

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
                  <SelectItem value="mes">Mes</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={cargarDashboard} disabled={loading || !selectedServer || !selectedSucursal} className="mt-5">
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
              Actualizar
            </Button>
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
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
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
                {comparativo && (
                  <div className="flex items-center gap-1 mt-2">
                    {comparativo.vs_periodo_anterior >= 0 ? 
                      <ArrowUpRight className="h-4 w-4 text-green-600" /> : 
                      <ArrowDownRight className="h-4 w-4 text-red-600" />}
                    <span className={`text-xs ${comparativo.vs_periodo_anterior >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatPercent(comparativo.vs_periodo_anterior)} vs período anterior
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card 
              className="border bg-gradient-to-br from-blue-50 to-white cursor-pointer hover:shadow-lg hover:scale-[1.02] transition-all"
              onDoubleClick={() => handleDoubleClick('ticket')}
              data-testid="kpi-ticket"
            >
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-zinc-500">Ticket Promedio</p>
                    <p className="text-2xl font-bold text-blue-600">{formatCurrency(kpis.ticket_promedio)}</p>
                  </div>
                  <ShoppingBag className="h-8 w-8 text-blue-200" />
                </div>
                <p className="text-xs text-zinc-500 mt-2">{kpis.cheques_total} cheques</p>
              </CardContent>
            </Card>

            <Card 
              className="border bg-gradient-to-br from-purple-50 to-white cursor-pointer hover:shadow-lg hover:scale-[1.02] transition-all"
              onDoubleClick={() => handleDoubleClick('pax')}
              data-testid="kpi-pax"
            >
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-zinc-500">PAX Total</p>
                    <p className="text-2xl font-bold text-purple-600">{formatNumber(kpis.pax_total)}</p>
                  </div>
                  <Users className="h-8 w-8 text-purple-200" />
                </div>
                <p className="text-xs text-zinc-500 mt-2">
                  {kpis.consumo_persona ? `$${formatNumber(kpis.consumo_persona)}/persona` : `Promedio: ${formatNumber(kpis.pax_promedio)} personas/mesa`}
                </p>
              </CardContent>
            </Card>

            <Card 
              className="border bg-gradient-to-br from-orange-50 to-white cursor-pointer hover:shadow-lg hover:scale-[1.02] transition-all"
              onDoubleClick={() => handleDoubleClick('rotacion')}
              data-testid="kpi-rotacion"
            >
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-zinc-500">Rotación Mesas</p>
                    <p className="text-2xl font-bold text-orange-600">{formatNumber(kpis.rotacion_mesas)}x</p>
                  </div>
                  <Utensils className="h-8 w-8 text-orange-200" />
                </div>
                <p className="text-xs text-zinc-500 mt-2">{kpis.mesas_atendidas} mesas atendidas</p>
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

// ============ COMPONENTE PRINCIPAL ============
export default function Comercial() {
  const [servers, setServers] = useState([]);
  const [selectedServer, setSelectedServer] = useState('');
  const [selectedSucursal, setSelectedSucursal] = useState('');
  const [sucursales, setSucursales] = useState([]);
  const [activeTab, setActiveTab] = useState('dashboard');

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
      const fetchSucursales = async () => {
        try {
          const token = localStorage.getItem('token');
          const response = await axios.get(`${API_URL}/api/servers/${selectedServer}/sucursales`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          setSucursales(response.data);
          setSelectedSucursal('');
        } catch (error) {
          console.error('Error:', error);
          setSucursales([]);
        }
      };
      fetchSucursales();
    }
  }, [selectedServer]);

  const commonProps = { servers, selectedServer, setSelectedServer, selectedSucursal, setSelectedSucursal, sucursales };

  return (
    <div className="space-y-4" data-testid="comercial-module">
      <div>
        <h1 className="text-2xl font-bold text-zinc-800">Comercial</h1>
        <p className="text-sm text-zinc-500">Análisis de ventas, rentabilidad y metas</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5 mb-4">
          <TabsTrigger value="dashboard" className="text-xs"><BarChart3 className="h-4 w-4 mr-1" />Dashboard</TabsTrigger>
          <TabsTrigger value="ticket" className="text-xs"><Award className="h-4 w-4 mr-1" />Ticket Perfecto</TabsTrigger>
          <TabsTrigger value="metas" className="text-xs"><Target className="h-4 w-4 mr-1" />Metas</TabsTrigger>
          <TabsTrigger value="tiempo" className="text-xs"><Clock className="h-4 w-4 mr-1" />Por Hora/Día</TabsTrigger>
          <TabsTrigger value="mesas" className="text-xs"><Utensils className="h-4 w-4 mr-1" />Mesas</TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard"><DashboardVentas {...commonProps} /></TabsContent>
        <TabsContent value="ticket"><TicketPerfecto {...commonProps} /></TabsContent>
        <TabsContent value="metas"><MetasVentas {...commonProps} /></TabsContent>
        <TabsContent value="tiempo"><VentasPorTiempo {...commonProps} /></TabsContent>
        <TabsContent value="mesas"><MesasComensales {...commonProps} /></TabsContent>
      </Tabs>
    </div>
  );
}
