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
  Wine, Award, RefreshCw, Calendar, ArrowUpRight, ArrowDownRight
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

// ============ TAB 1: DASHBOARD DE VENTAS ============
function DashboardVentas({ servers, selectedServer, setSelectedServer, selectedSucursal, setSelectedSucursal, sucursales }) {
  const [loading, setLoading] = useState(false);
  const [kpis, setKpis] = useState(null);
  const [comparativo, setComparativo] = useState(null);
  const [alertas, setAlertas] = useState([]);
  const [periodo, setPeriodo] = useState('mes'); // mes, semana, dia

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
      // Datos de ejemplo mientras se implementa
      setKpis({
        ventas_periodo: 485000,
        ticket_promedio: 385,
        cheques_total: 1260,
        pax_total: 3150,
        pax_promedio: 2.5,
        mesas_atendidas: 890,
        rotacion_mesas: 2.8,
        venta_por_hora: 20208
      });
      setComparativo({
        vs_periodo_anterior: 12.5,
        vs_ano_anterior: 8.3,
        vs_presupuesto: -5.2
      });
      setAlertas([
        { tipo: 'baja_venta', producto: 'Vino Tinto Casa', variacion: -35, mensaje: 'Ventas cayeron 35%' },
        { tipo: 'sobrestock', producto: 'Cerveza Importada', ventas_var: -28, compras_var: 5, mensaje: 'Compras no bajan con ventas' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedServer && selectedSucursal) {
      cargarDashboard();
    }
  }, [selectedServer, selectedSucursal, periodo]);

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

      {/* KPIs principales */}
      {kpis && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Card className="border bg-gradient-to-br from-green-50 to-white">
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

            <Card className="border bg-gradient-to-br from-blue-50 to-white">
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

            <Card className="border bg-gradient-to-br from-purple-50 to-white">
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-zinc-500">PAX Total</p>
                    <p className="text-2xl font-bold text-purple-600">{formatNumber(kpis.pax_total)}</p>
                  </div>
                  <Users className="h-8 w-8 text-purple-200" />
                </div>
                <p className="text-xs text-zinc-500 mt-2">Promedio: {formatNumber(kpis.pax_promedio)} personas/mesa</p>
              </CardContent>
            </Card>

            <Card className="border bg-gradient-to-br from-orange-50 to-white">
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
      // Datos de ejemplo
      setTicketData({
        tickets_totales: 1260,
        tickets_completos: 340,
        pct_completos: 27,
        con_entrada: 680,
        pct_entrada: 54,
        con_plato_fuerte: 1150,
        pct_plato_fuerte: 91,
        con_postre: 420,
        pct_postre: 33,
        con_digestivo: 180,
        pct_digestivo: 14,
        oportunidad_perdida: 125000
      });
      setRentabilidad([
        { codigo: 'P001', producto: 'Filete Mignon', ventas: 45000, costo: 18000, margen: 60, categoria: 'A' },
        { codigo: 'P002', producto: 'Pasta Alfredo', ventas: 32000, costo: 8000, margen: 75, categoria: 'A' },
        { codigo: 'P003', producto: 'Ensalada César', ventas: 28000, costo: 5600, margen: 80, categoria: 'A' },
        { codigo: 'P004', producto: 'Vino Tinto Casa', ventas: 25000, costo: 12500, margen: 50, categoria: 'B' },
        { codigo: 'P005', producto: 'Cerveza Importada', ventas: 18000, costo: 10800, margen: 40, categoria: 'C' },
      ]);
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
      // Datos de ejemplo
      setMetasProducto([
        { producto: 'Filete Mignon', meta: 60000, real: 45000, cumplimiento: 75 },
        { producto: 'Pasta Alfredo', meta: 40000, real: 32000, cumplimiento: 80 },
        { producto: 'Ensalada César', meta: 30000, real: 28000, cumplimiento: 93 },
      ]);
      setMetasVendedor([
        { vendedor: 'Carlos Pérez', meta: 150000, real: 165000, cumplimiento: 110 },
        { vendedor: 'María García', meta: 150000, real: 142000, cumplimiento: 95 },
        { vendedor: 'Juan López', meta: 120000, real: 98000, cumplimiento: 82 },
      ]);
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
      // Datos de ejemplo
      setVentasPorHora([
        { hora: '12:00', ventas: 35000, pax: 85 },
        { hora: '13:00', ventas: 52000, pax: 120 },
        { hora: '14:00', ventas: 48000, pax: 110 },
        { hora: '19:00', ventas: 42000, pax: 95 },
        { hora: '20:00', ventas: 65000, pax: 150 },
        { hora: '21:00', ventas: 58000, pax: 130 },
      ]);
      setVentasPorDia([
        { dia: 'Lunes', ventas: 45000 },
        { dia: 'Martes', ventas: 42000 },
        { dia: 'Miércoles', ventas: 48000 },
        { dia: 'Jueves', ventas: 52000 },
        { dia: 'Viernes', ventas: 78000 },
        { dia: 'Sábado', ventas: 95000 },
        { dia: 'Domingo', ventas: 68000 },
      ]);
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
      // Datos de ejemplo
      setDatosUnidad({
        nombre: selectedSucursal,
        total_mesas: 35,
        capacidad_total: 140,
        mesas_atendidas_mes: 2450,
        comensales_mes: 6125,
        rotacion_promedio: 2.8,
        ticket_promedio: 385,
        cheque_promedio: 962,
        pax_promedio: 2.5,
        vueltas_por_dia: 70,
        vueltas_por_hora_pico: 12
      });
      setRotacionPorMesa([
        { mesa: 'Mesa 1', capacidad: 4, vueltas: 85, ocupacion: 92 },
        { mesa: 'Mesa 2', capacidad: 4, vueltas: 78, ocupacion: 88 },
        { mesa: 'Mesa 3', capacidad: 6, vueltas: 72, ocupacion: 85 },
        { mesa: 'Mesa 4', capacidad: 2, vueltas: 95, ocupacion: 95 },
        { mesa: 'Mesa 5', capacidad: 8, vueltas: 45, ocupacion: 65 },
      ]);
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
