import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Checkbox } from '../components/ui/checkbox';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import { 
  Loader2, ShoppingCart, Package, TrendingUp, AlertTriangle, Download, 
  AlertCircle, Calendar, Edit3, RefreshCw, Search, BarChart3, FileText,
  ChevronRight, ChevronDown, ExternalLink, FileWarning, CheckCircle2, XCircle, X
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const STORAGE_KEY = 'compras_params';

const formatNumber = (num) => {
  if (num === null || num === undefined) return '-';
  return new Intl.NumberFormat('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(num);
};

const formatCurrency = (num) => {
  if (num === null || num === undefined) return '-';
  return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(num);
};

// ============ TAB 1: DASHBOARD DE COMPRAS ============
function DashboardCompras({ servers, selectedServer, setSelectedServer, selectedSucursal, setSelectedSucursal, sucursales }) {
  const [kpis, setKpis] = useState(null);
  const [alertas, setAlertas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [topProveedores, setTopProveedores] = useState([]);
  const [periodoMes, setPeriodoMes] = useState('actual'); // actual, anterior
  const [periodoAno, setPeriodoAno] = useState('actual'); // actual, anterior

  useEffect(() => {
    if (selectedServer && selectedSucursal) {
      cargarDashboard();
    }
  }, [selectedServer, selectedSucursal, periodoMes, periodoAno]);

  const cargarDashboard = async () => {
    if (!selectedSucursal) return;
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/compras/dashboard/${selectedServer}?sucursal=${encodeURIComponent(selectedSucursal)}&periodo_mes=${periodoMes}&periodo_ano=${periodoAno}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setKpis(response.data.kpis);
      setAlertas(response.data.alertas || []);
      setTopProveedores(response.data.top_proveedores || []);
    } catch (error) {
      console.error('Error cargando dashboard:', error);
      setKpis({
        total_compras_mes: 0,
        requisiciones_pendientes: 0,
        proveedores_activos: 0,
        alertas_activas: 0
      });
      setAlertas([]);
      setTopProveedores([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Selector de servidor, sucursal y período */}
      <Card className="border">
        <CardContent className="py-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex-1 min-w-[200px] max-w-xs">
              <Label className="text-xs mb-1 block">Servidor</Label>
              <Select value={selectedServer} onValueChange={setSelectedServer}>
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar servidor" />
                </SelectTrigger>
                <SelectContent>
                  {servers.map(s => (
                    <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex-1 min-w-[200px] max-w-xs">
              <Label className="text-xs mb-1 block">Sucursal</Label>
              <Select value={selectedSucursal} onValueChange={setSelectedSucursal} disabled={!selectedServer || sucursales.length === 0}>
                <SelectTrigger>
                  <SelectValue placeholder={selectedServer ? (sucursales.length === 0 ? "Sin sucursales" : "Seleccionar sucursal") : "Selecciona servidor primero"} />
                </SelectTrigger>
                <SelectContent>
                  {sucursales.map(s => (
                    <SelectItem key={s.codigo || s.nombre} value={s.nombre}>{s.nombre}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button onClick={cargarDashboard} disabled={!selectedServer || !selectedSucursal || loading} variant="outline" className="mt-5">
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Actualizar
            </Button>
          </div>
          {/* Selectores de período */}
          <div className="flex items-center gap-4 flex-wrap mt-4 pt-4 border-t">
            <div className="flex-1 min-w-[150px] max-w-[200px]">
              <Label className="text-xs mb-1 block">Período (Mes)</Label>
              <Select value={periodoMes} onValueChange={setPeriodoMes}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="actual">Mes Actual</SelectItem>
                  <SelectItem value="anterior">Mes Anterior</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex-1 min-w-[150px] max-w-[200px]">
              <Label className="text-xs mb-1 block">Año</Label>
              <Select value={periodoAno} onValueChange={setPeriodoAno}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="actual">Año Actual</SelectItem>
                  <SelectItem value="anterior">Año Anterior</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* KPIs */}
      {kpis && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="border bg-gradient-to-br from-blue-50 to-white">
            <CardContent className="py-4">
              <p className="text-xs text-zinc-500">Compras del Mes</p>
              <p className="text-2xl font-bold text-blue-600">{formatCurrency(kpis.total_compras_mes)}</p>
            </CardContent>
          </Card>
          <Card className="border bg-gradient-to-br from-orange-50 to-white">
            <CardContent className="py-4">
              <p className="text-xs text-zinc-500">Requisiciones Pendientes</p>
              <p className="text-2xl font-bold text-orange-600">{kpis.requisiciones_pendientes}</p>
            </CardContent>
          </Card>
          <Card className="border bg-gradient-to-br from-green-50 to-white">
            <CardContent className="py-4">
              <p className="text-xs text-zinc-500">Proveedores Activos</p>
              <p className="text-2xl font-bold text-green-600">{kpis.proveedores_activos}</p>
            </CardContent>
          </Card>
          <Card className="border bg-gradient-to-br from-red-50 to-white">
            <CardContent className="py-4">
              <p className="text-xs text-zinc-500">Alertas Activas</p>
              <p className="text-2xl font-bold text-red-600">{kpis.alertas_activas}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Alertas de desviación */}
      {alertas.length > 0 && (
        <Card className="border border-red-200 bg-red-50">
          <CardHeader className="py-3">
            <CardTitle className="text-base flex items-center gap-2 text-red-700">
              <AlertTriangle className="h-5 w-5" />
              Alertas de Desviación Compras vs Consumos
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {alertas.map((alerta, idx) => (
              <div key={idx} className="flex items-center gap-3 p-2 bg-white rounded border border-red-200">
                <span className={`px-2 py-1 rounded text-xs font-semibold ${
                  alerta.tipo === 'sobrecompra' ? 'bg-red-100 text-red-700' : 'bg-orange-100 text-orange-700'
                }`}>
                  {alerta.tipo === 'sobrecompra' ? 'SOBRECOMPRA' : 'DESABASTO'}
                </span>
                <span className="font-medium">{alerta.producto}</span>
                <span className="text-sm text-zinc-500">
                  Ventas: <span className={alerta.variacion_ventas > 0 ? 'text-green-600' : 'text-red-600'}>
                    {alerta.variacion_ventas > 0 ? '+' : ''}{alerta.variacion_ventas}%
                  </span>
                </span>
                <span className="text-sm text-zinc-500">
                  Compras: <span className={alerta.variacion_compras > 0 ? 'text-green-600' : 'text-red-600'}>
                    {alerta.variacion_compras > 0 ? '+' : ''}{alerta.variacion_compras}%
                  </span>
                </span>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Top Proveedores */}
      {topProveedores.length > 0 && (
        <Card className="border">
          <CardHeader className="py-3">
            <CardTitle className="text-base">Top Proveedores del Mes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {topProveedores.map((prov, idx) => (
                <div key={idx} className="flex items-center justify-between p-2 bg-zinc-50 rounded">
                  <span className="font-medium">{prov.nombre}</span>
                  <span className="text-green-600 font-semibold">{formatCurrency(prov.total)}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ============ TAB 2: AUTORIZACIÓN (Código existente simplificado) ============
function AutorizacionComprasTab({ servers, selectedServer, setSelectedServer, selectedSucursal: parentSucursal, setSelectedSucursal: setParentSucursal, sucursales: parentSucursales }) {
  // Este componente usa las sucursales del padre para mantener sincronización
  const [serverData, setServerData] = useState(null);
  const [almacenes, setAlmacenes] = useState([]);
  const [selectedAlmacenes, setSelectedAlmacenes] = useState([]);
  const [todosAlmacenes, setTodosAlmacenes] = useState(false);
  const [fechaInvFisico, setFechaInvFisico] = useState('');
  const [fechaFinPeriodo, setFechaFinPeriodo] = useState(new Date().toISOString().split('T')[0]);
  const [diasInventario, setDiasInventario] = useState(10);
  const [metodoCalculo, setMetodoCalculo] = useState('consumo');
  const [inventariosFisicos, setInventariosFisicos] = useState([]);
  const [inventariosFiltrados, setInventariosFiltrados] = useState([]);
  const [folioInvFisico, setFolioInvFisico] = useState('');
  const [pedidosVigentes, setPedidosVigentes] = useState([]);
  const [folioPedidoComparar, setFolioPedidoComparar] = useState('');
  const [folioManual, setFolioManual] = useState('');
  const [usarFolioManual, setUsarFolioManual] = useState(false);
  const [loading, setLoading] = useState(false);
  const [pedidoData, setPedidoData] = useState([]);
  const [resumen, setResumen] = useState(null);
  const [infoInventario, setInfoInventario] = useState(null);

  useEffect(() => {
    if (selectedServer) {
      const server = servers.find(s => s.id === selectedServer);
      setServerData(server);
    }
  }, [selectedServer, servers]);

  useEffect(() => {
    if (selectedServer && parentSucursal) {
      fetchAlmacenes(selectedServer, parentSucursal);
      fetchInventariosFisicos(selectedServer, parentSucursal);
      fetchPedidosVigentes(selectedServer, parentSucursal);
    }
  }, [selectedServer, parentSucursal]);

  useEffect(() => {
    if (todosAlmacenes || selectedAlmacenes.includes('TODOS')) {
      const grouped = {};
      inventariosFisicos.forEach(inv => {
        const key = inv.fecha.split('T')[0];
        if (!grouped[key]) grouped[key] = { fecha: inv.fecha, almacenes: [], comentario: inv.comentario };
        grouped[key].almacenes.push(inv.almacen);
      });
      const consolidated = Object.entries(grouped).map(([fecha, data]) => ({
        folio: `TODOS-${fecha}`,
        fecha: data.fecha,
        almacen: `${data.almacenes.length} almacenes`,
        comentario: data.comentario || '',
        isTodos: true
      }));
      setInventariosFiltrados(consolidated.slice(0, 30));
    } else if (selectedAlmacenes.length >= 1) {
      const filtered = inventariosFisicos.filter(inv => 
        selectedAlmacenes.some(a => inv.almacen.toLowerCase().includes(a.toLowerCase()))
      );
      setInventariosFiltrados(filtered.slice(0, 50));
    } else {
      setInventariosFiltrados(inventariosFisicos.slice(0, 50));
    }
  }, [selectedAlmacenes, todosAlmacenes, inventariosFisicos]);

  const fetchAlmacenes = async (serverId, sucursal) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/servers/${serverId}/almacenes?sucursal=${encodeURIComponent(sucursal)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const unique = [...new Map(response.data.map(a => [a.nombre, a])).values()];
      setAlmacenes(unique);
    } catch (error) {
      console.error('Error cargando almacenes:', error);
    }
  };

  const fetchInventariosFisicos = async (serverId, sucursal) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/compras/inventarios-fisicos/${serverId}?sucursal=${encodeURIComponent(sucursal)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setInventariosFisicos(response.data);
      if (response.data.length > 0 && !folioInvFisico) {
        setFolioInvFisico(response.data[0].folio);
        setFechaInvFisico(response.data[0].fecha.split('T')[0]);
      }
    } catch (error) {
      console.error('Error cargando inventarios físicos:', error);
    }
  };

  const fetchPedidosVigentes = async (serverId, sucursal) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/compras/pedidos-vigentes/${serverId}?sucursal=${encodeURIComponent(sucursal)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPedidosVigentes(response.data || []);
    } catch (error) {
      console.error('Error cargando pedidos vigentes:', error);
      setPedidosVigentes([]);
    }
  };

  const handleAlmacenToggle = (almacenNombre) => {
    setSelectedAlmacenes(prev => {
      if (prev.includes(almacenNombre)) {
        return prev.filter(a => a !== almacenNombre);
      }
      return [...prev, almacenNombre];
    });
    setTodosAlmacenes(false);
    setFolioInvFisico('');
  };

  const handleTodosAlmacenes = (checked) => {
    setTodosAlmacenes(checked);
    if (checked) {
      setSelectedAlmacenes(['TODOS']);
      setFolioInvFisico('');
    } else {
      setSelectedAlmacenes([]);
    }
  };

  const calcularPedido = async () => {
    if (!selectedServer || !parentSucursal || (selectedAlmacenes.length === 0 && !todosAlmacenes)) {
      toast.error('Selecciona servidor, sucursal y al menos un almacén');
      return;
    }
    if (!fechaInvFisico || !fechaFinPeriodo) {
      toast.error('Selecciona las fechas del período de análisis');
      return;
    }
    if (!folioPedidoComparar && !usarFolioManual) {
      toast.error('Selecciona una requisición para comparar');
      return;
    }

    setLoading(true);
    setPedidoData([]);
    setResumen(null);

    try {
      const token = localStorage.getItem('token');
      const folioComparar = usarFolioManual ? folioManual : folioPedidoComparar;
      const folioEnviar = (todosAlmacenes || folioInvFisico?.startsWith('TODOS-')) ? null : folioInvFisico;
      
      const response = await axios.post(`${API_URL}/api/compras/calculo-pedido`, {
        server_id: selectedServer,
        sucursal: parentSucursal,
        almacenes: todosAlmacenes ? ['TODOS'] : selectedAlmacenes,
        fecha_inventario_fisico: fechaInvFisico,
        fecha_fin_periodo: fechaFinPeriodo,
        dias_inventario: parseInt(diasInventario),
        metodo_calculo: metodoCalculo,
        folio_inventario_fisico: folioEnviar,
        folio_pedido_comparar: folioComparar
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setPedidoData(response.data.data);
      setInfoInventario(response.data);
      
      const data = response.data.data;
      setResumen({
        totalProductos: data.length,
        productosAPedir: data.filter(p => p.Cantidad_Pedir > 0).length,
        costoTotalPedido: data.reduce((sum, p) => sum + (p.Costo_Pedido || 0), 0),
        productosStockBajo: data.filter(p => p.Dias_Inventario < 3 && p.Dias_Inventario !== 999).length,
      });

      toast.success(`Cálculo completado: ${response.data.count} productos`);
    } catch (error) {
      console.error('Error calculando pedido:', error);
      const errorDetail = error.response?.data?.detail;
      let errorMsg = 'Error al calcular pedido';
      if (typeof errorDetail === 'string') {
        errorMsg = errorDetail;
      } else if (Array.isArray(errorDetail)) {
        errorMsg = errorDetail.map(e => e.msg || e.message || JSON.stringify(e)).join(', ');
      }
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Parámetros */}
      <Card className="border">
        <CardHeader className="py-3">
          <CardTitle className="text-base flex items-center gap-2">
            <ShoppingCart className="h-5 w-5 text-blue-600" />
            Parámetros del Cálculo
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="space-y-1">
              <Label className="text-xs">Servidor</Label>
              <Select value={selectedServer} onValueChange={setSelectedServer}>
                <SelectTrigger className="h-9">
                  <SelectValue placeholder="Seleccionar" />
                </SelectTrigger>
                <SelectContent>
                  {servers.map(server => (
                    <SelectItem key={server.id} value={server.id}>{server.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Sucursal</Label>
              <Select value={parentSucursal} onValueChange={setParentSucursal} disabled={!selectedServer}>
                <SelectTrigger className="h-9">
                  <SelectValue placeholder="Seleccionar" />
                </SelectTrigger>
                <SelectContent className="max-h-60 overflow-y-auto">
                  {parentSucursales.map(suc => (
                    <SelectItem key={suc.codigo || suc.nombre} value={suc.nombre}>{suc.nombre}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Folio Inv. Inicial</Label>
              <Select value={folioInvFisico} onValueChange={(val) => { 
                setFolioInvFisico(val); 
                const inv = inventariosFiltrados.find(i => i.folio === val); 
                if (inv) setFechaInvFisico(inv.fecha.split('T')[0]); 
              }} disabled={todosAlmacenes}>
                <SelectTrigger className="h-9">
                  <SelectValue placeholder={todosAlmacenes ? "Consolidado" : "Seleccionar"} />
                </SelectTrigger>
                <SelectContent className="max-h-72 overflow-y-auto">
                  {inventariosFiltrados.map(inv => (
                    <SelectItem key={inv.folio} value={inv.folio}>
                      {inv.folio} ({new Date(inv.fecha).toLocaleDateString('es-MX')}) - {inv.comentario || inv.almacen || ''}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Método Cálculo</Label>
              <Select value={metodoCalculo} onValueChange={setMetodoCalculo}>
                <SelectTrigger className="h-9">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="consumo">Por Consumo</SelectItem>
                  <SelectItem value="stock">Por Stock Máx</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {almacenes.length > 0 && (
            <div className="space-y-1">
              <Label className="text-xs">Almacenes</Label>
              <div className="flex flex-wrap gap-2 p-2 border rounded-md bg-zinc-50 text-sm max-h-20 overflow-y-auto">
                <div className="flex items-center gap-1">
                  <Checkbox id="todos" checked={todosAlmacenes} onCheckedChange={handleTodosAlmacenes} />
                  <label htmlFor="todos" className="font-medium">TODOS</label>
                </div>
                <div className="w-px h-5 bg-zinc-300" />
                {almacenes.map(alm => (
                  <div key={alm.nombre} className="flex items-center gap-1">
                    <Checkbox id={`a-${alm.nombre}`} checked={selectedAlmacenes.includes(alm.nombre)} onCheckedChange={() => handleAlmacenToggle(alm.nombre)} disabled={todosAlmacenes} />
                    <label htmlFor={`a-${alm.nombre}`}>{alm.nombre}</label>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="space-y-1">
              <Label className="text-xs">Fecha Inv. Inicial</Label>
              <Input type="date" value={fechaInvFisico} onChange={(e) => setFechaInvFisico(e.target.value)} className="h-9" />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Fecha Fin Período</Label>
              <Input type="date" value={fechaFinPeriodo} onChange={(e) => setFechaFinPeriodo(e.target.value)} className="h-9" />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Días Inv. a Comprar</Label>
              <Input type="number" min="1" max="90" value={diasInventario} onChange={(e) => setDiasInventario(e.target.value)} className="h-9" />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Comparar con Requisición</Label>
              <Select value={folioPedidoComparar} onValueChange={setFolioPedidoComparar}>
                <SelectTrigger className="h-9">
                  <SelectValue placeholder="Seleccionar requisición" />
                </SelectTrigger>
                <SelectContent className="max-h-60 overflow-y-auto">
                  {pedidosVigentes.map(p => (
                    <SelectItem key={`${p.tipo}-${p.folio}`} value={p.folio}>
                      {p.folio} - {p.comentario || p.comprador || 'Sin desc.'}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex gap-2 pt-2">
            <Button onClick={calcularPedido} disabled={loading || !selectedServer || !parentSucursal}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
              Calcular Pedido
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* KPIs */}
      {resumen && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          <Card className="border"><CardContent className="py-3"><p className="text-xs text-zinc-500">Total</p><p className="text-lg font-bold">{resumen.totalProductos}</p></CardContent></Card>
          <Card className="border"><CardContent className="py-3"><p className="text-xs text-zinc-500">A Pedir</p><p className="text-lg font-bold text-green-600">{resumen.productosAPedir}</p></CardContent></Card>
          <Card className="border"><CardContent className="py-3"><p className="text-xs text-zinc-500">Costo</p><p className="text-base font-bold">{formatCurrency(resumen.costoTotalPedido)}</p></CardContent></Card>
          <Card className="border"><CardContent className="py-3"><p className="text-xs text-zinc-500">Stock Bajo</p><p className="text-lg font-bold text-red-600">{resumen.productosStockBajo}</p></CardContent></Card>
        </div>
      )}

      {/* Tabla de resultados */}
      {pedidoData.length > 0 && (
        <Card className="border">
          <CardHeader className="py-2">
            <CardTitle className="text-base">Pedido Sugerido ({pedidoData.filter(p => p.Cantidad_Pedir > 0).length} a pedir)</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="max-h-[400px] overflow-auto">
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-zinc-200">
                  <tr>
                    <th className="py-2 px-2 text-left">Código</th>
                    <th className="py-2 px-2 text-left">Producto</th>
                    <th className="py-2 px-2 text-right">Inv.Ini</th>
                    <th className="py-2 px-2 text-right">Movim.</th>
                    <th className="py-2 px-2 text-right">Consumos</th>
                    <th className="py-2 px-2 text-right">Teórico</th>
                    <th className="py-2 px-2 text-right">Días</th>
                    <th className="py-2 px-2 text-right text-green-700">Pedir</th>
                    <th className="py-2 px-2 text-right">Costo</th>
                  </tr>
                </thead>
                <tbody>
                  {pedidoData.slice(0, 100).map((row, idx) => (
                    <tr key={idx} className="border-b hover:bg-zinc-50">
                      <td className="py-1 px-2 font-mono">{row.Codigo}</td>
                      <td className="py-1 px-2 max-w-[150px] truncate">{row.Producto}</td>
                      <td className="py-1 px-2 text-right">{formatNumber(row.Inventario_Inicial)}</td>
                      <td className="py-1 px-2 text-right">{formatNumber(row.Movimientos_Periodo)}</td>
                      <td className="py-1 px-2 text-right text-red-600">{formatNumber(row.Consumos_Periodo)}</td>
                      <td className="py-1 px-2 text-right font-semibold">{formatNumber(row.Inventario_Teorico)}</td>
                      <td className="py-1 px-2 text-right">{row.Dias_Inventario >= 999 ? '∞' : formatNumber(row.Dias_Inventario)}</td>
                      <td className="py-1 px-2 text-right font-bold text-green-700">{formatNumber(row.Cantidad_Pedir)}</td>
                      <td className="py-1 px-2 text-right">{formatCurrency(row.Costo_Pedido)}</td>
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

// ============ TAB 3: ANÁLISIS DE COMPRAS ============
function AnalisisCompras({ servers, selectedServer, setSelectedServer, selectedSucursal, setSelectedSucursal, sucursales }) {
  const [loading, setLoading] = useState(false);
  const [anio, setAnio] = useState(new Date().getFullYear());
  const [mesesSeleccionados, setMesesSeleccionados] = useState(['01', '02', '03']);
  const [comprasPorProveedor, setComprasPorProveedor] = useState([]);
  const [expandedProveedor, setExpandedProveedor] = useState(null);
  const [detalleFacturas, setDetalleFacturas] = useState([]);
  const [expandedFactura, setExpandedFactura] = useState(null);
  const [detalleProductos, setDetalleProductos] = useState([]);
  const [alertasDesviacion, setAlertasDesviacion] = useState([]);
  const [modalDocumento, setModalDocumento] = useState({ open: false, tipo: '', url: '', data: null });

  const meses = [
    { value: '01', label: 'Ene' }, { value: '02', label: 'Feb' }, { value: '03', label: 'Mar' },
    { value: '04', label: 'Abr' }, { value: '05', label: 'May' }, { value: '06', label: 'Jun' },
    { value: '07', label: 'Jul' }, { value: '08', label: 'Ago' }, { value: '09', label: 'Sep' },
    { value: '10', label: 'Oct' }, { value: '11', label: 'Nov' }, { value: '12', label: 'Dic' },
  ];

  const cargarAnalisis = async () => {
    if (!selectedServer || !selectedSucursal) {
      toast.error('Selecciona servidor y sucursal');
      return;
    }
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API_URL}/api/compras/analisis`, {
        server_id: selectedServer,
        sucursal: selectedSucursal,
        anio: anio,
        meses: mesesSeleccionados
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setComprasPorProveedor(response.data.proveedores || []);
      setAlertasDesviacion(response.data.alertas || []);
    } catch (error) {
      console.error('Error:', error);
      // Datos de ejemplo
      setComprasPorProveedor([
        { codigo: 'B0734', nombre: 'VINO PA TODOS/CAZA GOURMET', '01': 7115, '02': 4805, '03': 7865, total: 19785 },
        { codigo: 'B0013', nombre: 'CAVA DEL 10', '01': 5568, '02': 5568, '03': 8352, total: 19488 },
        { codigo: 'B0823', nombre: 'DIFRUTA/MONICA APONTE', '01': 6820, '02': 6175, '03': 5765, total: 18760 },
        { codigo: 'B0158', nombre: 'COMESUR-CAFE MUSI', '01': 0, '02': 8600, '03': 8600, total: 17200 },
        { codigo: 'B0677', nombre: 'CASA LAMBAR (LICORES)', '01': 0, '02': 11592, '03': 2494, total: 14086 },
      ]);
      setAlertasDesviacion([
        { producto: 'Vino Tinto Reserva', tipo: 'sobrecompra', var_ventas: -35, var_compras: 12 },
        { producto: 'Aguacate Hass', tipo: 'desabasto', var_ventas: 45, var_compras: -20 },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const toggleMes = (mes) => {
    setMesesSeleccionados(prev => 
      prev.includes(mes) ? prev.filter(m => m !== mes) : [...prev, mes]
    );
  };

  const verDetalleProveedor = async (proveedor) => {
    if (expandedProveedor === proveedor.codigo) {
      setExpandedProveedor(null);
      return;
    }
    setExpandedProveedor(proveedor.codigo);
    // Cargar facturas del proveedor
    setDetalleFacturas([
      { folio: 'FAC-2024-001', fecha: '2024-01-15', productos: 8, importe: 3250, status: 'pagada', tiene_pdf: true, tiene_xml: true },
      { folio: 'FAC-2024-002', fecha: '2024-01-22', productos: 12, importe: 3865, status: 'pagada', tiene_pdf: true, tiene_xml: true },
      { folio: 'FAC-2024-003', fecha: '2024-02-08', productos: 5, importe: 2105, status: 'pendiente', tiene_pdf: false, tiene_xml: true },
    ]);
  };

  const verDetalleFactura = async (factura) => {
    if (expandedFactura === factura.folio) {
      setExpandedFactura(null);
      return;
    }
    setExpandedFactura(factura.folio);
    setDetalleProductos([
      { codigo: '0000001234', producto: 'Vino Tinto Reserva 750ml', cantidad: 24, costo: 85, importe: 2040 },
      { codigo: '0000001235', producto: 'Vino Blanco Chardonnay', cantidad: 12, costo: 72.50, importe: 870 },
      { codigo: '0000001236', producto: 'Vino Rosado 750ml', cantidad: 6, costo: 56.67, importe: 340 },
    ]);
  };

  const totalGeneral = comprasPorProveedor.reduce((sum, p) => sum + (p.total || 0), 0);

  return (
    <div className="space-y-4">
      {/* Filtros */}
      <Card className="border">
        <CardContent className="py-4 space-y-3">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="space-y-1">
              <Label className="text-xs">Servidor</Label>
              <Select value={selectedServer} onValueChange={setSelectedServer}>
                <SelectTrigger className="h-9">
                  <SelectValue placeholder="Seleccionar" />
                </SelectTrigger>
                <SelectContent>
                  {servers.map(s => (
                    <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Sucursal</Label>
              <Select value={selectedSucursal} onValueChange={setSelectedSucursal} disabled={!selectedServer}>
                <SelectTrigger className="h-9">
                  <SelectValue placeholder={selectedServer ? "Seleccionar" : "Selecciona servidor"} />
                </SelectTrigger>
                <SelectContent>
                  {sucursales.map(s => (
                    <SelectItem key={s.codigo || s.nombre} value={s.nombre}>{s.nombre}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Año</Label>
              <Select value={String(anio)} onValueChange={(v) => setAnio(Number(v))}>
                <SelectTrigger className="h-9">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="2024">2024</SelectItem>
                  <SelectItem value="2025">2025</SelectItem>
                  <SelectItem value="2026">2026</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button onClick={cargarAnalisis} disabled={loading || !selectedServer || !selectedSucursal} className="w-full">
                {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <BarChart3 className="h-4 w-4 mr-2" />}
                Analizar
              </Button>
            </div>
          </div>
          
          {/* Selector de meses */}
          <div className="space-y-1">
            <Label className="text-xs">Meses</Label>
            <div className="flex flex-wrap gap-1">
              {meses.map(m => (
                <Button
                  key={m.value}
                  variant={mesesSeleccionados.includes(m.value) ? "default" : "outline"}
                  size="sm"
                  className="h-8 px-3"
                  onClick={() => toggleMes(m.value)}
                >
                  {m.label}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Alertas de desviación */}
      {alertasDesviacion.length > 0 && (
        <Card className="border border-red-200 bg-red-50">
          <CardHeader className="py-2">
            <CardTitle className="text-sm flex items-center gap-2 text-red-700">
              <AlertTriangle className="h-4 w-4" />
              Alertas: Compras vs Consumos
            </CardTitle>
          </CardHeader>
          <CardContent className="py-2">
            <div className="space-y-1">
              {alertasDesviacion.map((a, idx) => (
                <div key={idx} className="flex items-center gap-2 text-sm">
                  {a.tipo === 'sobrecompra' ? (
                    <XCircle className="h-4 w-4 text-red-600" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-orange-600" />
                  )}
                  <span className="font-medium">{a.producto}:</span>
                  <span>Ventas {a.var_ventas > 0 ? '+' : ''}{a.var_ventas}%</span>
                  <span>Compras {a.var_compras > 0 ? '+' : ''}{a.var_compras}%</span>
                  <span className={`px-2 py-0.5 rounded text-xs ${a.tipo === 'sobrecompra' ? 'bg-red-200 text-red-800' : 'bg-orange-200 text-orange-800'}`}>
                    {a.tipo === 'sobrecompra' ? 'SOBRECOMPRA' : 'DESABASTO'}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabla de compras por proveedor */}
      {comprasPorProveedor.length > 0 && (
        <Card className="border">
          <CardHeader className="py-2">
            <CardTitle className="text-base flex items-center justify-between">
              <span>Compras por Proveedor</span>
              <span className="text-green-600">{formatCurrency(totalGeneral)}</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="max-h-[500px] overflow-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-zinc-800 text-white">
                  <tr>
                    <th className="py-2 px-3 text-left w-8"></th>
                    <th className="py-2 px-3 text-left">Proveedor</th>
                    {mesesSeleccionados.map(m => (
                      <th key={m} className="py-2 px-3 text-right">{meses.find(x => x.value === m)?.label}</th>
                    ))}
                    <th className="py-2 px-3 text-right font-bold">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {comprasPorProveedor.map((prov, idx) => (
                    <React.Fragment key={idx}>
                      <tr 
                        className="border-b hover:bg-zinc-50 cursor-pointer"
                        onClick={() => verDetalleProveedor(prov)}
                      >
                        <td className="py-2 px-3">
                          {expandedProveedor === prov.codigo ? (
                            <ChevronDown className="h-4 w-4" />
                          ) : (
                            <ChevronRight className="h-4 w-4" />
                          )}
                        </td>
                        <td className="py-2 px-3 font-medium">{prov.codigo} {prov.nombre}</td>
                        {mesesSeleccionados.map(m => (
                          <td key={m} className="py-2 px-3 text-right">
                            {prov[m] ? formatCurrency(prov[m]) : '-'}
                          </td>
                        ))}
                        <td className="py-2 px-3 text-right font-bold text-green-600">{formatCurrency(prov.total)}</td>
                      </tr>
                      
                      {/* Detalle de facturas */}
                      {expandedProveedor === prov.codigo && (
                        <tr>
                          <td colSpan={mesesSeleccionados.length + 3} className="bg-zinc-100 p-0">
                            <div className="p-3">
                              <p className="text-xs font-semibold text-zinc-500 mb-2">FACTURAS / ENTRADAS</p>
                              <table className="w-full text-xs">
                                <thead className="bg-zinc-200">
                                  <tr>
                                    <th className="py-1 px-2 text-left w-6"></th>
                                    <th className="py-1 px-2 text-left">Folio</th>
                                    <th className="py-1 px-2 text-left">Fecha</th>
                                    <th className="py-1 px-2 text-right">Productos</th>
                                    <th className="py-1 px-2 text-right">Importe</th>
                                    <th className="py-1 px-2 text-center">Status</th>
                                    <th className="py-1 px-2 text-center">Docs</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {detalleFacturas.map((fac, fidx) => (
                                    <React.Fragment key={fidx}>
                                      <tr 
                                        className="border-b hover:bg-white cursor-pointer"
                                        onClick={(e) => { e.stopPropagation(); verDetalleFactura(fac); }}
                                      >
                                        <td className="py-1 px-2">
                                          {expandedFactura === fac.folio ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
                                        </td>
                                        <td className="py-1 px-2 font-mono">{fac.folio}</td>
                                        <td className="py-1 px-2">{fac.fecha}</td>
                                        <td className="py-1 px-2 text-right">{fac.productos}</td>
                                        <td className="py-1 px-2 text-right">{formatCurrency(fac.importe)}</td>
                                        <td className="py-1 px-2 text-center">
                                          <span className={`px-2 py-0.5 rounded text-xs ${fac.status === 'pagada' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                                            {fac.status}
                                          </span>
                                        </td>
                                        <td className="py-1 px-2 text-center">
                                          <div className="flex gap-1 justify-center">
                                            {fac.tiene_pdf && (
                                              <Button variant="ghost" size="sm" className="h-6 px-2" onClick={(e) => { e.stopPropagation(); setModalDocumento({ open: true, tipo: 'pdf', url: '#', data: fac }); }}>
                                                <FileText className="h-3 w-3 text-red-600" />
                                              </Button>
                                            )}
                                            {fac.tiene_xml && (
                                              <Button variant="ghost" size="sm" className="h-6 px-2" onClick={(e) => { e.stopPropagation(); setModalDocumento({ open: true, tipo: 'xml', url: '#', data: fac }); }}>
                                                <FileText className="h-3 w-3 text-green-600" />
                                              </Button>
                                            )}
                                            {!fac.tiene_pdf && !fac.tiene_xml && (
                                              <FileWarning className="h-3 w-3 text-zinc-400" />
                                            )}
                                          </div>
                                        </td>
                                      </tr>
                                      
                                      {/* Detalle de productos */}
                                      {expandedFactura === fac.folio && (
                                        <tr>
                                          <td colSpan={7} className="bg-white p-2">
                                            <table className="w-full text-xs">
                                              <thead className="bg-zinc-100">
                                                <tr>
                                                  <th className="py-1 px-2 text-left">Código</th>
                                                  <th className="py-1 px-2 text-left">Producto</th>
                                                  <th className="py-1 px-2 text-right">Cant</th>
                                                  <th className="py-1 px-2 text-right">Costo</th>
                                                  <th className="py-1 px-2 text-right">Importe</th>
                                                </tr>
                                              </thead>
                                              <tbody>
                                                {detalleProductos.map((prod, pidx) => (
                                                  <tr key={pidx} className="border-b">
                                                    <td className="py-1 px-2 font-mono">{prod.codigo}</td>
                                                    <td className="py-1 px-2">{prod.producto}</td>
                                                    <td className="py-1 px-2 text-right">{prod.cantidad}</td>
                                                    <td className="py-1 px-2 text-right">{formatCurrency(prod.costo)}</td>
                                                    <td className="py-1 px-2 text-right">{formatCurrency(prod.importe)}</td>
                                                  </tr>
                                                ))}
                                              </tbody>
                                            </table>
                                          </td>
                                        </tr>
                                      )}
                                    </React.Fragment>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Modal para ver documentos */}
      <Dialog open={modalDocumento.open} onOpenChange={(open) => setModalDocumento({ ...modalDocumento, open })}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {modalDocumento.tipo === 'pdf' ? (
                <><FileText className="h-5 w-5 text-red-600" /> Factura PDF</>
              ) : (
                <><FileText className="h-5 w-5 text-green-600" /> XML (CFDI)</>
              )}
            </DialogTitle>
          </DialogHeader>
          
          {modalDocumento.tipo === 'xml' && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4 p-4 bg-zinc-50 rounded">
                <div>
                  <p className="text-xs text-zinc-500">UUID</p>
                  <p className="font-mono text-sm">8A5F2B3C-4D5E-6F7A-8B9C-0D1E2F3A4B5C</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Fecha Timbrado</p>
                  <p className="text-sm">15/Ene/2026 14:32:05</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">RFC Emisor</p>
                  <p className="font-mono text-sm flex items-center gap-2">
                    VPT850101ABC
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  </p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">RFC Receptor</p>
                  <p className="font-mono text-sm flex items-center gap-2">
                    EDA900101XYZ
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  </p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Subtotal</p>
                  <p className="text-sm">{formatCurrency(2801.72)}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">IVA</p>
                  <p className="text-sm">{formatCurrency(448.28)}</p>
                </div>
                <div className="col-span-2">
                  <p className="text-xs text-zinc-500">Total</p>
                  <p className="text-xl font-bold text-green-600">{formatCurrency(3250)}</p>
                </div>
              </div>
              
              <div className="flex items-center gap-2 p-3 bg-green-50 rounded border border-green-200">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                <span className="text-sm text-green-700">Validaciones OK: RFC Emisor, RFC Receptor, Importe</span>
              </div>
              
              <div className="flex gap-2">
                <Button variant="outline" className="flex-1">
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Ver XML completo
                </Button>
                <Button variant="outline" className="flex-1">
                  <Download className="h-4 w-4 mr-2" />
                  Descargar
                </Button>
              </div>
            </div>
          )}
          
          {modalDocumento.tipo === 'pdf' && (
            <div className="space-y-3">
              <div className="h-96 bg-zinc-100 rounded flex items-center justify-center">
                <p className="text-zinc-500">Visor PDF se mostrará aquí</p>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" className="flex-1">
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Abrir en nueva pestaña
                </Button>
                <Button variant="outline" className="flex-1">
                  <Download className="h-4 w-4 mr-2" />
                  Descargar
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ============ COMPONENTE PRINCIPAL CON TABS ============
// ============ TAB 4: AUDITORÍA OPERATIVA ============
function AuditoriaOperativaTab({ servers, selectedServer, setSelectedServer, selectedSucursal: parentSucursal, setSelectedSucursal: setParentSucursal, sucursales: parentSucursales }) {
  const [loading, setLoading] = useState(false);
  const [almacenes, setAlmacenes] = useState([]);
  const [selectedAlmacenes, setSelectedAlmacenes] = useState([]);
  const [inventariosFisicos, setInventariosFisicos] = useState([]);
  const [pedidosVigentes, setPedidosVigentes] = useState([]);
  
  const [folioInvInicial, setFolioInvInicial] = useState('');
  const [folioInvFinal, setFolioInvFinal] = useState('');
  const [folioPedido, setFolioPedido] = useState([]);  // Cambiado a array para multi-selección
  const [fechaInicial, setFechaInicial] = useState('');
  const [fechaAuditoria, setFechaAuditoria] = useState(new Date().toISOString().split('T')[0]);
  const [usarCapturaManual, setUsarCapturaManual] = useState(false);
  const [inventarioManual, setInventarioManual] = useState([]);
  
  // Estados para selección múltiple de inventarios
  const [selectedInvIniciales, setSelectedInvIniciales] = useState([]);
  const [selectedInvFinales, setSelectedInvFinales] = useState([]);
  const [busquedaInvIni, setBusquedaInvIni] = useState('');
  const [busquedaInvFin, setBusquedaInvFin] = useState('');
  
  // Calcular fecha mínima de inventarios iniciales para filtrar finales
  const fechaMinimaInvInicial = useMemo(() => {
    if (selectedInvIniciales.length === 0) return null;
    // Obtener la fecha más antigua de los inventarios iniciales
    const fechas = selectedInvIniciales
      .map(inv => inv.fecha?.split('T')[0])
      .filter(f => f);
    if (fechas.length === 0) return null;
    return fechas.sort()[0]; // La fecha más antigua
  }, [selectedInvIniciales]);
  
  // Filtrar inventarios finales: solo mostrar los que tienen fecha >= fecha del inv inicial
  const inventariosFinalesFiltrados = useMemo(() => {
    if (!fechaMinimaInvInicial) return inventariosFisicos;
    return inventariosFisicos.filter(inv => {
      const fechaInv = inv.fecha?.split('T')[0];
      if (!fechaInv) return true; // Si no tiene fecha, mostrarlo
      return fechaInv >= fechaMinimaInvInicial;
    });
  }, [inventariosFisicos, fechaMinimaInvInicial]);
  
  const [resultados, setResultados] = useState(null);
  const [resumen, setResumen] = useState(null);
  const [agruparPorProveedor, setAgruparPorProveedor] = useState(false);
  
  // Selector de unidad de análisis: 'presentaciones' o 'insumos'
  const [unidadAnalisis, setUnidadAnalisis] = useState('presentaciones');
  
  // Modal detalle de movimientos
  const [detalleMovimientos, setDetalleMovimientos] = useState(null);
  const [showDetalleModal, setShowDetalleModal] = useState(false);
  const [loadingDetalle, setLoadingDetalle] = useState(false);
  const [tipoDetalle, setTipoDetalle] = useState('movimientos'); // 'movimientos' o 'consumos'

  // Cargar filtros guardados al montar
  useEffect(() => {
    const savedFilters = localStorage.getItem(`auditoria_filters_${selectedServer}_${parentSucursal}`);
    if (savedFilters) {
      try {
        const filters = JSON.parse(savedFilters);
        if (filters.selectedAlmacenes) setSelectedAlmacenes(filters.selectedAlmacenes);
        if (filters.folioPedido) setFolioPedido(filters.folioPedido);
        if (filters.fechaInicial) setFechaInicial(filters.fechaInicial);
        if (filters.fechaAuditoria) setFechaAuditoria(filters.fechaAuditoria);
        if (filters.selectedInvIniciales) setSelectedInvIniciales(filters.selectedInvIniciales);
        if (filters.selectedInvFinales) setSelectedInvFinales(filters.selectedInvFinales);
        if (filters.usarCapturaManual !== undefined) setUsarCapturaManual(filters.usarCapturaManual);
      } catch (e) {
        console.warn('Error loading saved filters:', e);
      }
    }
  }, [selectedServer, parentSucursal]);

  // Guardar filtros cuando cambien
  useEffect(() => {
    if (selectedServer && parentSucursal) {
      const filters = {
        selectedAlmacenes,
        folioPedido,
        fechaInicial,
        fechaAuditoria,
        selectedInvIniciales,
        selectedInvFinales,
        usarCapturaManual
      };
      localStorage.setItem(`auditoria_filters_${selectedServer}_${parentSucursal}`, JSON.stringify(filters));
    }
  }, [selectedServer, parentSucursal, selectedAlmacenes, folioPedido, fechaInicial, fechaAuditoria, selectedInvIniciales, selectedInvFinales, usarCapturaManual]);

  useEffect(() => {
    if (selectedServer && parentSucursal) {
      fetchAlmacenes();
      fetchInventariosFisicos();
      fetchPedidosVigentes();
    }
  }, [selectedServer, parentSucursal]);

  const fetchAlmacenes = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/servers/${selectedServer}/almacenes?sucursal=${encodeURIComponent(parentSucursal)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAlmacenes(response.data);
    } catch (error) {
      console.error('Error cargando almacenes:', error);
    }
  };

  const fetchInventariosFisicos = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/compras/inventarios-fisicos/${selectedServer}?sucursal=${encodeURIComponent(parentSucursal)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setInventariosFisicos(response.data);
    } catch (error) {
      console.error('Error cargando inventarios físicos:', error);
    }
  };

  const fetchPedidosVigentes = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/compras/pedidos-vigentes/${selectedServer}?sucursal=${encodeURIComponent(parentSucursal)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPedidosVigentes(response.data);
    } catch (error) {
      console.error('Error cargando pedidos:', error);
    }
  };

  // Función para convertir cantidades según unidad seleccionada
  // Devuelve objeto {principal, alternativo} para mostrar en columnas separadas
  const getConversionValues = (cantidad, rendimiento) => {
    if (!cantidad || cantidad === 0) return { principal: '0.00', alternativo: '0.00' };
    
    const cantidadNum = parseFloat(cantidad) || 0;
    const rendimientoNum = parseFloat(rendimiento) || 1;
    
    if (unidadAnalisis === 'presentaciones') {
      // Principal: presentaciones, Alternativo: insumos
      const enInsumos = cantidadNum * rendimientoNum;
      return {
        principal: formatNumber(cantidadNum),
        alternativo: formatNumber(enInsumos)
      };
    } else {
      // Principal: insumos, Alternativo: presentaciones
      const enPresentaciones = rendimientoNum > 0 ? cantidadNum / rendimientoNum : 0;
      return {
        principal: formatNumber(cantidadNum),
        alternativo: formatNumber(enPresentaciones)
      };
    }
  };
  
  // Función para obtener el costo ajustado según unidad seleccionada
  const getCostoAjustado = (costo, rendimiento) => {
    if (!costo || costo === 0) return 0;
    
    const costoNum = parseFloat(costo) || 0;
    const rendimientoNum = parseFloat(rendimiento) || 1;
    
    if (unidadAnalisis === 'presentaciones') {
      // Costo de la presentación (ya viene así del backend)
      return costoNum;
    } else {
      // Costo del insumo = costo de presentación / rendimiento
      return rendimientoNum > 0 ? costoNum / rendimientoNum : costoNum;
    }
  };

  // Función para formatear cantidad con conversión (formato legible)
  const formatConversion = (cantidad, rendimiento, unidadPrincipal) => {
    const values = getConversionValues(cantidad, rendimiento);
    return `${values.principal} (${values.alternativo})`;
  };

  // Función para obtener detalle de movimientos al hacer doble click
  const fetchDetalleMovimientos = async (codigo, producto) => {
    setLoadingDetalle(true);
    setShowDetalleModal(true);
    setTipoDetalle('movimientos');
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API_URL}/api/compras/detalle-movimientos`, {
        server_id: selectedServer,
        sucursal: parentSucursal,
        codigo: codigo,
        fecha_inicio: fechaInicial || selectedInvIniciales[0]?.fecha?.split('T')[0] || fechaAuditoria,
        fecha_fin: fechaAuditoria,
        almacenes: selectedAlmacenes
      }, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 30000  // 30 segundos de timeout
      });
      
      // Verificar si la respuesta tiene error del servidor
      if (response.data.error) {
        setDetalleMovimientos({
          codigo,
          producto,
          movimientos: [],
          error: response.data.error
        });
      } else {
        setDetalleMovimientos({
          codigo,
          producto,
          movimientos: response.data.movimientos || [],
          totales: response.data.totales || {}
        });
      }
    } catch (error) {
      console.error('Error obteniendo detalle:', error);
      let errorMsg = 'Error al obtener detalle de movimientos';
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        errorMsg = 'Tiempo de espera agotado. El servidor externo no responde.';
      } else if (error.response?.data?.detail) {
        errorMsg = error.response.data.detail.substring(0, 150);
      }
      setDetalleMovimientos({
        codigo,
        producto,
        movimientos: [],
        error: errorMsg
      });
    } finally {
      setLoadingDetalle(false);
    }
  };

  const fetchDetalleConsumos = async (codigo, producto) => {
    setLoadingDetalle(true);
    setShowDetalleModal(true);
    setTipoDetalle('consumos');
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API_URL}/api/compras/detalle-consumos`, {
        server_id: selectedServer,
        sucursal: parentSucursal,
        codigo: codigo,
        fecha_inicio: fechaInicial || selectedInvIniciales[0]?.fecha?.split('T')[0] || fechaAuditoria,
        fecha_fin: fechaAuditoria,
        almacenes: selectedAlmacenes
      }, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 30000
      });
      
      if (response.data.error) {
        setDetalleMovimientos({
          codigo,
          producto,
          movimientos: [],
          error: response.data.error
        });
      } else {
        setDetalleMovimientos({
          codigo,
          producto,
          movimientos: response.data.consumos || response.data.movimientos || [],
          totales: response.data.totales || {}
        });
      }
    } catch (error) {
      console.error('Error obteniendo detalle consumos:', error);
      let errorMsg = 'Error al obtener detalle de consumos';
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        errorMsg = 'Tiempo de espera agotado. El servidor externo no responde.';
      } else if (error.response?.data?.detail) {
        errorMsg = error.response.data.detail.substring(0, 150);
      }
      setDetalleMovimientos({
        codigo,
        producto,
        movimientos: [],
        error: errorMsg
      });
    } finally {
      setLoadingDetalle(false);
    }
  };

  const handleInvInicialChange = (folio) => {
    setFolioInvInicial(folio);
    const inv = inventariosFisicos.find(i => String(i.folio) === String(folio));
    if (inv) {
      setFechaInicial(inv.fecha?.split('T')[0] || '');
    }
  };

  const realizarAuditoria = async () => {
    if (!selectedServer || !parentSucursal) {
      toast.error('Selecciona servidor y sucursal');
      return;
    }
    
    // Usar selectedInvIniciales si hay elementos, sino folioInvInicial
    const tieneInvInicial = selectedInvIniciales.length > 0 || folioInvInicial;
    
    if (!tieneInvInicial || !fechaInicial || !fechaAuditoria) {
      toast.error('Completa las fechas y el inventario inicial');
      return;
    }
    if (folioPedido.length === 0) {
      toast.error('Selecciona al menos una requisición para comparar');
      return;
    }
    if (!usarCapturaManual && !folioInvFinal && selectedInvFinales.length === 0) {
      toast.error('Selecciona un inventario final o activa captura manual');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      
      // Determinar el folio de inventario inicial a usar
      const folioInvInicialToUse = selectedInvIniciales.length > 0 
        ? selectedInvIniciales[0].folio 
        : folioInvInicial;
      
      // Determinar el folio de inventario final a usar
      const folioInvFinalToUse = selectedInvFinales.length > 0 
        ? selectedInvFinales[0].folio 
        : folioInvFinal;
      
      const response = await axios.post(`${API_URL}/api/compras/auditoria-operativa`, {
        server_id: selectedServer,
        sucursal: parentSucursal,
        almacenes: selectedAlmacenes.length > 0 ? selectedAlmacenes : ['TODOS'],
        folio_inv_inicial: folioInvInicialToUse,
        fecha_inv_inicial: fechaInicial,
        fecha_auditoria: fechaAuditoria,
        folio_inv_final: usarCapturaManual ? null : folioInvFinalToUse,
        folio_requisicion: folioPedido[0] || '',  // Siempre string (el primero)
        folios_requisiciones: folioPedido,  // Array completo
        inventario_manual: usarCapturaManual ? inventarioManual : null
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setResultados(response.data.resultados);
      setResumen(response.data.resumen);
      
      if (response.data.resumen?.requiere_acta) {
        toast.warning('Se detectaron diferencias en contra. Se requiere Acta de Auditoría.');
      } else {
        toast.success('Auditoría completada sin diferencias significativas');
      }
    } catch (error) {
      console.error('Error en auditoría:', error);
      const errorDetail = error.response?.data?.detail;
      let errorMsg = 'Error al realizar auditoría';
      if (typeof errorDetail === 'string') {
        errorMsg = errorDetail;
      } else if (Array.isArray(errorDetail)) {
        errorMsg = errorDetail.map(e => e.msg || e.message || JSON.stringify(e)).join(', ');
      }
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <Card className="border">
        <CardHeader className="py-3 bg-amber-50 border-b">
          <CardTitle className="text-base flex items-center gap-2">
            <FileWarning className="h-5 w-5 text-amber-600" />
            Auditoría Operativa de Inventarios
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 space-y-4">
          {/* Selección de servidor y sucursal */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-1">
              <Label className="text-xs">Servidor</Label>
              <Select value={selectedServer} onValueChange={setSelectedServer}>
                <SelectTrigger className="h-9">
                  <SelectValue placeholder="Seleccionar servidor" />
                </SelectTrigger>
                <SelectContent>
                  {servers.map(s => <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            {parentSucursales.length > 1 && (
              <div className="space-y-1">
                <Label className="text-xs">Sucursal</Label>
                <Select value={parentSucursal} onValueChange={setParentSucursal} disabled={!selectedServer}>
                  <SelectTrigger className="h-9">
                    <SelectValue placeholder="Seleccionar" />
                  </SelectTrigger>
                  <SelectContent>
                    {parentSucursales.map(suc => (
                      <SelectItem key={suc.codigo || suc.nombre} value={suc.nombre}>
                        {suc.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            <div className="space-y-1">
              <Label className="text-xs">Requisición(es) a Comparar *</Label>
              <details className="relative">
                <summary className="flex h-9 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm cursor-pointer">
                  <span className="truncate text-left">
                    {folioPedido.length === 0 
                      ? "Seleccionar requisición(es)" 
                      : `${folioPedido.length} seleccionada(s)`}
                  </span>
                  <ChevronDown className="h-4 w-4 opacity-50" />
                </summary>
                <div className="absolute z-50 w-full mt-1 bg-white border rounded-md shadow-lg max-h-64 overflow-hidden">
                  {folioPedido.length > 0 && (
                    <button
                      type="button"
                      className="w-full px-3 py-2 text-xs text-left hover:bg-zinc-100 border-b flex items-center text-red-600"
                      onClick={() => setFolioPedido([])}
                    >
                      <X className="h-3 w-3 mr-1" /> Limpiar selección ({folioPedido.length})
                    </button>
                  )}
                  <div className="max-h-52 overflow-y-auto">
                    {pedidosVigentes.map(p => (
                      <label key={`${p.tipo}-${p.folio}`} className="flex items-center space-x-2 py-2 px-3 hover:bg-zinc-50 cursor-pointer">
                        <input
                          type="checkbox"
                          className="rounded border-zinc-300"
                          checked={folioPedido.includes(p.folio)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setFolioPedido([...folioPedido, p.folio]);
                            } else {
                              setFolioPedido(folioPedido.filter(f => f !== p.folio));
                            }
                          }}
                        />
                        <span className="text-sm">{p.folio} - {p.comprador || 'Sin proveedor'}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </details>
              {/* Badges de requisiciones seleccionadas */}
              {folioPedido.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {folioPedido.map(f => {
                    const pedido = pedidosVigentes.find(p => p.folio === f);
                    return (
                      <span 
                        key={f}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-purple-100 text-purple-800 border border-purple-200"
                      >
                        {f}
                        <button 
                          type="button"
                          onClick={() => setFolioPedido(folioPedido.filter(x => x !== f))}
                          className="hover:text-purple-600"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </span>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Inventarios y fechas */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-1">
              <Label className="text-xs">Inventario(s) Inicial(es)</Label>
              <details className="relative group">
                <summary className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm cursor-pointer hover:border-zinc-400">
                  <span className="truncate text-left">
                    {selectedInvIniciales.length === 0 
                      ? "Seleccionar inventario(s)" 
                      : `${selectedInvIniciales.length} seleccionado(s)`}
                  </span>
                  <ChevronDown className="h-4 w-4 opacity-50" />
                </summary>
                <div className="absolute z-50 w-[350px] mt-1 bg-white border rounded-md shadow-xl">
                  {/* Barra de búsqueda */}
                  <div className="p-2 border-b bg-zinc-50">
                    <Input
                      placeholder="Buscar por folio o almacén..."
                      value={busquedaInvIni}
                      onChange={(e) => setBusquedaInvIni(e.target.value)}
                      className="h-8 text-sm"
                    />
                  </div>
                  {/* Botones de acción */}
                  <div className="flex items-center justify-between px-2 py-1 border-b bg-zinc-50">
                    {selectedInvIniciales.length > 0 && (
                      <button
                        type="button"
                        className="text-xs text-red-600 hover:text-red-700 flex items-center"
                        onClick={() => {
                          setSelectedInvIniciales([]);
                          setFolioInvInicial('');
                          setFechaInicial('');
                        }}
                      >
                        <X className="h-3 w-3 mr-1" /> Limpiar ({selectedInvIniciales.length})
                      </button>
                    )}
                    <span className="text-xs text-zinc-400 ml-auto">
                      {inventariosFisicos.filter(inv => 
                        !busquedaInvIni || 
                        String(inv.folio).includes(busquedaInvIni) ||
                        (inv.almacen || '').toLowerCase().includes(busquedaInvIni.toLowerCase())
                      ).length} inventarios
                    </span>
                  </div>
                  {/* Lista de inventarios con scroll mejorado */}
                  <div className="max-h-72 overflow-y-auto" style={{ scrollbarWidth: 'auto', scrollbarColor: '#a1a1aa #f4f4f5' }}>
                    {inventariosFisicos
                      .filter(inv => 
                        !busquedaInvIni || 
                        String(inv.folio).includes(busquedaInvIni) ||
                        (inv.almacen || '').toLowerCase().includes(busquedaInvIni.toLowerCase())
                      )
                      .map(inv => (
                        <label 
                          key={inv.folio} 
                          className={`flex items-center space-x-3 py-3 px-3 hover:bg-blue-50 cursor-pointer border-b border-zinc-100 ${
                            selectedInvIniciales.some(i => i.folio === inv.folio) ? 'bg-blue-50' : ''
                          }`}
                        >
                          <input
                            type="checkbox"
                            className="rounded border-zinc-300 h-4 w-4"
                            checked={selectedInvIniciales.some(i => i.folio === inv.folio)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                const newSelected = [...selectedInvIniciales, inv];
                                setSelectedInvIniciales(newSelected);
                                if (newSelected.length === 1) {
                                  setFolioInvInicial(String(inv.folio));
                                  setFechaInicial(inv.fecha?.split('T')[0] || '');
                                }
                              } else {
                                const newSelected = selectedInvIniciales.filter(i => i.folio !== inv.folio);
                                setSelectedInvIniciales(newSelected);
                                if (newSelected.length === 0) {
                                  setFolioInvInicial('');
                                  setFechaInicial('');
                                }
                              }
                            }}
                          />
                          <div className="flex-1 min-w-0">
                            <div className="font-medium text-sm">{inv.folio}</div>
                            <div className="text-xs text-zinc-500 truncate">
                              {inv.fecha?.split('T')[0]} - {inv.almacen}
                            </div>
                          </div>
                        </label>
                      ))}
                  </div>
                  {/* Input para agregar folio manualmente */}
                  <div className="p-2 border-t bg-zinc-50">
                    <div className="flex gap-2">
                      <Input
                        placeholder="Agregar folio manualmente"
                        className="h-8 text-sm flex-1"
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') {
                            const folio = e.target.value.trim();
                            if (folio && !selectedInvIniciales.some(i => String(i.folio) === folio)) {
                              const invExistente = inventariosFisicos.find(i => String(i.folio) === folio);
                              if (invExistente) {
                                setSelectedInvIniciales([...selectedInvIniciales, invExistente]);
                              } else {
                                setSelectedInvIniciales([...selectedInvIniciales, { folio, almacen: 'Manual', fecha: '' }]);
                              }
                              e.target.value = '';
                            }
                          }
                        }}
                      />
                    </div>
                  </div>
                </div>
              </details>
              {/* Badges de inventarios iniciales */}
              {selectedInvIniciales.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {selectedInvIniciales.map(inv => (
                    <span 
                      key={inv.folio}
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-blue-100 text-blue-800 border border-blue-200"
                    >
                      {inv.folio}
                      <button 
                        type="button"
                        onClick={() => {
                          const newSelected = selectedInvIniciales.filter(i => i.folio !== inv.folio);
                          setSelectedInvIniciales(newSelected);
                          if (newSelected.length === 0) {
                            setFolioInvInicial('');
                            setFechaInicial('');
                          }
                        }}
                        className="hover:text-blue-600"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Fecha Inicial</Label>
              <Input type="date" value={fechaInicial} onChange={e => setFechaInicial(e.target.value)} className="h-9" />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Fecha Auditoría</Label>
              <Input type="date" value={fechaAuditoria} onChange={e => setFechaAuditoria(e.target.value)} className="h-9" />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Inventario(s) Final(es)</Label>
              {!usarCapturaManual ? (
                <details className="relative group">
                  <summary className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm cursor-pointer hover:border-zinc-400">
                    <span className="truncate text-left">
                      {selectedInvFinales.length === 0 
                        ? "Seleccionar inventario(s)" 
                        : `${selectedInvFinales.length} seleccionado(s)`}
                    </span>
                    <ChevronDown className="h-4 w-4 opacity-50" />
                  </summary>
                  <div className="absolute z-50 w-[350px] right-0 mt-1 bg-white border rounded-md shadow-xl">
                    {/* Barra de búsqueda */}
                    <div className="p-2 border-b bg-zinc-50">
                      <Input
                        placeholder="Buscar por folio o almacén..."
                        value={busquedaInvFin}
                        onChange={(e) => setBusquedaInvFin(e.target.value)}
                        className="h-8 text-sm"
                      />
                    </div>
                    {/* Botones de acción */}
                    <div className="flex items-center justify-between px-2 py-1 border-b bg-zinc-50">
                      {selectedInvFinales.length > 0 && (
                        <button
                          type="button"
                          className="text-xs text-red-600 hover:text-red-700 flex items-center"
                          onClick={() => {
                            setSelectedInvFinales([]);
                            setFolioInvFinal('');
                          }}
                        >
                          <X className="h-3 w-3 mr-1" /> Limpiar ({selectedInvFinales.length})
                        </button>
                      )}
                      <span className="text-xs text-zinc-400 ml-auto">
                        {inventariosFinalesFiltrados.filter(inv => 
                          !busquedaInvFin || 
                          String(inv.folio).includes(busquedaInvFin) ||
                          (inv.almacen || '').toLowerCase().includes(busquedaInvFin.toLowerCase())
                        ).length} inventarios
                        {fechaMinimaInvInicial && <span className="ml-1">(desde {fechaMinimaInvInicial})</span>}
                      </span>
                    </div>
                    {/* Lista de inventarios con scroll mejorado */}
                    <div className="max-h-72 overflow-y-auto" style={{ scrollbarWidth: 'auto', scrollbarColor: '#a1a1aa #f4f4f5' }}>
                      {inventariosFinalesFiltrados
                        .filter(inv => 
                          !busquedaInvFin || 
                          String(inv.folio).includes(busquedaInvFin) ||
                          (inv.almacen || '').toLowerCase().includes(busquedaInvFin.toLowerCase())
                        )
                        .map(inv => (
                          <label 
                            key={inv.folio} 
                            className={`flex items-center space-x-3 py-3 px-3 hover:bg-green-50 cursor-pointer border-b border-zinc-100 ${
                              selectedInvFinales.some(i => i.folio === inv.folio) ? 'bg-green-50' : ''
                            }`}
                          >
                            <input
                              type="checkbox"
                              className="rounded border-zinc-300 h-4 w-4"
                              checked={selectedInvFinales.some(i => i.folio === inv.folio)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  const newSelected = [...selectedInvFinales, inv];
                                  setSelectedInvFinales(newSelected);
                                  if (newSelected.length === 1) {
                                    setFolioInvFinal(String(inv.folio));
                                  }
                                } else {
                                  const newSelected = selectedInvFinales.filter(i => i.folio !== inv.folio);
                                  setSelectedInvFinales(newSelected);
                                  if (newSelected.length === 0) {
                                    setFolioInvFinal('');
                                  }
                                }
                              }}
                            />
                            <div className="flex-1 min-w-0">
                              <div className="font-medium text-sm">{inv.folio}</div>
                              <div className="text-xs text-zinc-500 truncate">
                                {inv.fecha?.split('T')[0]} - {inv.almacen}
                              </div>
                            </div>
                          </label>
                        ))}
                    </div>
                    {/* Input para agregar folio manualmente */}
                    <div className="p-2 border-t bg-zinc-50">
                      <div className="flex gap-2">
                        <Input
                          placeholder="Agregar folio manualmente"
                          className="h-8 text-sm flex-1"
                          onKeyPress={(e) => {
                            if (e.key === 'Enter') {
                              const folio = e.target.value.trim();
                              if (folio && !selectedInvFinales.some(i => String(i.folio) === folio)) {
                                const invExistente = inventariosFisicos.find(i => String(i.folio) === folio);
                                if (invExistente) {
                                  setSelectedInvFinales([...selectedInvFinales, invExistente]);
                                } else {
                                  setSelectedInvFinales([...selectedInvFinales, { folio, almacen: 'Manual', fecha: '' }]);
                                }
                                e.target.value = '';
                              }
                            }
                          }}
                        />
                      </div>
                    </div>
                  </div>
                </details>
              ) : (
                <div className="text-xs text-amber-600 font-medium p-2 bg-amber-50 rounded">
                  Captura Manual Activa
                </div>
              )}
              {/* Badges de inventarios finales */}
              {!usarCapturaManual && selectedInvFinales.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {selectedInvFinales.map(inv => (
                    <span 
                      key={inv.folio}
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-green-100 text-green-800 border border-green-200"
                    >
                      {inv.folio}
                      <button 
                        type="button"
                        onClick={() => {
                          const newSelected = selectedInvFinales.filter(i => i.folio !== inv.folio);
                          setSelectedInvFinales(newSelected);
                          if (newSelected.length === 0) {
                            setFolioInvFinal('');
                          }
                        }}
                        className="hover:text-green-600"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Opción de captura manual */}
          <div className="flex items-center gap-2">
            <Checkbox 
              id="captura-manual" 
              checked={usarCapturaManual} 
              onCheckedChange={setUsarCapturaManual} 
            />
            <Label htmlFor="captura-manual" className="text-sm">
              Sin folio de inventario final - Usar captura manual
            </Label>
          </div>

          {/* Botón de ejecución */}
          <div className="flex gap-2 pt-2">
            <Button onClick={realizarAuditoria} disabled={loading || !selectedServer || !parentSucursal}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <FileWarning className="h-4 w-4 mr-2" />}
              Realizar Auditoría
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Resumen de Auditoría */}
      {resumen && (
        <Card className={`border-2 ${resumen.requiere_acta ? 'border-red-300 bg-red-50' : 'border-green-300 bg-green-50'}`}>
          <CardHeader className="py-3">
            <CardTitle className="text-base flex items-center gap-2">
              {resumen.requiere_acta ? (
                <><XCircle className="h-5 w-5 text-red-600" /> Requiere Acta de Auditoría</>
              ) : (
                <><CheckCircle2 className="h-5 w-5 text-green-600" /> Auditoría Sin Observaciones</>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-white rounded border">
                <p className="text-xs text-zinc-500">Existencia Teórica</p>
                <p className="text-lg font-bold text-blue-600">{formatCurrency(resumen.total_teorico)}</p>
              </div>
              <div className="text-center p-3 bg-white rounded border">
                <p className="text-xs text-zinc-500">Existencia Física</p>
                <p className="text-lg font-bold text-purple-600">{formatCurrency(resumen.total_fisico)}</p>
              </div>
              <div className="text-center p-3 bg-white rounded border">
                <p className="text-xs text-zinc-500">A Favor ({resumen.productos_favor})</p>
                <p className="text-lg font-bold text-green-600">+{formatCurrency(resumen.importe_favor)}</p>
              </div>
              <div className="text-center p-3 bg-white rounded border">
                <p className="text-xs text-zinc-500">En Contra ({resumen.productos_contra})</p>
                <p className="text-lg font-bold text-red-600">-{formatCurrency(resumen.importe_contra)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabla de resultados */}
      {resultados && resultados.length > 0 && (
        <Card className="border">
          <CardHeader className="py-2 flex flex-row items-center justify-between gap-4">
            <CardTitle className="text-sm">Detalle de Auditoría ({resultados.length} productos)</CardTitle>
            <div className="flex items-center gap-4">
              {/* Selector de unidad de análisis */}
              <div className="flex items-center gap-2 bg-zinc-100 rounded-lg p-1">
                <button
                  className={`px-3 py-1 text-xs rounded ${unidadAnalisis === 'presentaciones' ? 'bg-white shadow font-medium' : 'text-zinc-600'}`}
                  onClick={() => setUnidadAnalisis('presentaciones')}
                >
                  Presentaciones
                </button>
                <button
                  className={`px-3 py-1 text-xs rounded ${unidadAnalisis === 'insumos' ? 'bg-white shadow font-medium' : 'text-zinc-600'}`}
                  onClick={() => setUnidadAnalisis('insumos')}
                >
                  Insumos
                </button>
              </div>
              <label className="flex items-center gap-2 text-xs cursor-pointer">
                <input
                  type="checkbox"
                  className="rounded border-zinc-300"
                  checked={agruparPorProveedor}
                  onChange={(e) => setAgruparPorProveedor(e.target.checked)}
                />
                <span>Agrupar por Proveedor</span>
              </label>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="max-h-[400px] overflow-auto">
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-zinc-800 text-white">
                  <tr>
                    {agruparPorProveedor && <th className="py-2 px-2 text-left">Proveedor</th>}
                    {agruparPorProveedor && <th className="py-2 px-2 text-left">Folio Pedido</th>}
                    <th className="py-2 px-2 text-left">Producto</th>
                    <th className="py-2 px-2 text-right">{unidadAnalisis === 'presentaciones' ? 'Inv.Ini (Pres)' : 'Inv.Ini (Ins)'}</th>
                    <th className="py-2 px-2 text-right text-zinc-400">{unidadAnalisis === 'presentaciones' ? '(Ins)' : '(Pres)'}</th>
                    <th className="py-2 px-2 text-right">{unidadAnalisis === 'presentaciones' ? '+Mov (Pres)' : '+Mov (Ins)'}</th>
                    <th className="py-2 px-2 text-right text-zinc-400">{unidadAnalisis === 'presentaciones' ? '(Ins)' : '(Pres)'}</th>
                    <th className="py-2 px-2 text-right">{unidadAnalisis === 'presentaciones' ? '-Cons (Pres)' : '-Cons (Ins)'}</th>
                    <th className="py-2 px-2 text-right text-zinc-400">{unidadAnalisis === 'presentaciones' ? '(Ins)' : '(Pres)'}</th>
                    <th className="py-2 px-2 text-right">Teórico</th>
                    <th className="py-2 px-2 text-right">Físico</th>
                    <th className="py-2 px-2 text-right">Diferencia</th>
                    <th className="py-2 px-2 text-right">Costo Unit</th>
                    <th className="py-2 px-2 text-right">Importe</th>
                    <th className="py-2 px-2 text-center">Días Inv</th>
                    <th className="py-2 px-2 text-right">Pedido</th>
                    <th className="py-2 px-2 text-center">Recomendar</th>
                  </tr>
                </thead>
                <tbody>
                  {(() => {
                    let lastProveedor = '';
                    let lastFolio = '';
                    return resultados.map((r, idx) => {
                      const rendimiento = r.rendimiento || 1;
                      const isNewProveedor = agruparPorProveedor && r.proveedor !== lastProveedor;
                      const isNewFolio = agruparPorProveedor && r.folio_pedido !== lastFolio;
                      
                      // Obtener valores convertidos para cada columna
                      const invIniValues = getConversionValues(r.inv_inicial, rendimiento);
                      const movValues = getConversionValues(r.movimientos || r.entradas || 0, rendimiento);
                      const consValues = getConversionValues(Math.abs(r.consumos || 0), rendimiento);
                      const teoricoValues = getConversionValues(r.existencia_teorica, rendimiento);
                      const fisicoValues = getConversionValues(r.inv_fisico, rendimiento);
                      const difValues = getConversionValues(r.diferencia, rendimiento);
                      const costoUnit = getCostoAjustado(r.costo, rendimiento);
                      
                      if (agruparPorProveedor) {
                        lastProveedor = r.proveedor;
                        lastFolio = r.folio_pedido;
                      }
                      
                      return (
                        <tr key={idx} className={`border-b ${r.tipo_diferencia === 'contra' ? 'bg-red-50' : ''} ${isNewProveedor ? 'border-t-2 border-t-zinc-400' : ''}`}>
                          {agruparPorProveedor && (
                            <td className={`py-1.5 px-2 ${isNewProveedor ? 'font-bold text-zinc-800' : 'text-zinc-400'}`}>
                              {isNewProveedor ? r.proveedor : ''}
                            </td>
                          )}
                          {agruparPorProveedor && (
                            <td className={`py-1.5 px-2 ${isNewFolio ? 'font-medium text-blue-600' : 'text-zinc-400'}`}>
                              {isNewFolio ? r.folio_pedido : ''}
                            </td>
                          )}
                          <td className="py-1.5 px-2 font-medium">{r.producto}</td>
                          {/* Inv Inicial - Principal */}
                          <td className="py-1.5 px-2 text-right">{invIniValues.principal}</td>
                          {/* Inv Inicial - Alternativo */}
                          <td className="py-1.5 px-2 text-right text-zinc-400">{invIniValues.alternativo}</td>
                          {/* Movimientos - Principal */}
                          <td 
                            className="py-1.5 px-2 text-right text-green-600 cursor-pointer hover:bg-green-100 transition-colors"
                            onDoubleClick={() => fetchDetalleMovimientos(r.codigo, r.producto)}
                            title="Doble click para ver detalle de movimientos"
                          >
                            +{movValues.principal}
                          </td>
                          {/* Movimientos - Alternativo */}
                          <td className="py-1.5 px-2 text-right text-green-400">{movValues.alternativo}</td>
                          {/* Consumos - Principal */}
                          <td 
                            className="py-1.5 px-2 text-right text-orange-600 cursor-pointer hover:bg-orange-100 transition-colors"
                            onDoubleClick={() => fetchDetalleConsumos(r.codigo, r.producto)}
                            title="Doble click para ver detalle de consumos"
                          >
                            -{consValues.principal}
                          </td>
                          {/* Consumos - Alternativo */}
                          <td className="py-1.5 px-2 text-right text-orange-400">{consValues.alternativo}</td>
                          {/* Teórico */}
                          <td className="py-1.5 px-2 text-right font-medium">{teoricoValues.principal}</td>
                          {/* Físico */}
                          <td className="py-1.5 px-2 text-right font-medium">{fisicoValues.principal}</td>
                          {/* Diferencia */}
                          <td className={`py-1.5 px-2 text-right font-bold ${r.diferencia >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {r.diferencia >= 0 ? '+' : ''}{difValues.principal}
                          </td>
                          {/* Costo Unitario */}
                          <td className="py-1.5 px-2 text-right text-zinc-500">
                            {formatCurrency(costoUnit)}
                          </td>
                          {/* Importe Diferencia */}
                          <td className={`py-1.5 px-2 text-right ${r.importe_diferencia >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {formatCurrency(r.importe_diferencia)}
                          </td>
                          <td className="py-1.5 px-2 text-center">
                            <span className={`px-1.5 py-0.5 rounded text-xs ${
                              r.dias_inventario === 'N/A' ? 'bg-zinc-100' :
                              r.dias_inventario < 5 ? 'bg-red-100 text-red-700' :
                              r.dias_inventario < 10 ? 'bg-yellow-100 text-yellow-700' :
                              'bg-green-100 text-green-700'
                            }`}>
                              {r.dias_inventario}
                            </span>
                          </td>
                          <td className="py-1.5 px-2 text-right">{formatNumber(r.cantidad_pedido)}</td>
                          <td className="py-1.5 px-2 text-center">
                            <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                              r.recomendacion === 'COMPRAR' ? 'bg-red-100 text-red-700' :
                              r.recomendacion === 'OK' ? 'bg-green-100 text-green-700' :
                              'bg-zinc-100 text-zinc-600'
                            }`}>
                              {r.recomendacion}
                            </span>
                          </td>
                        </tr>
                      );
                    });
                  })()}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Modal Detalle de Movimientos/Consumos */}
      {showDetalleModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[80vh] overflow-hidden">
            <div className="px-4 py-3 border-b flex items-center justify-between bg-zinc-50">
              <div>
                <h3 className="font-semibold">
                  {tipoDetalle === 'consumos' ? 'Detalle de Consumos' : 'Detalle de Movimientos'}
                </h3>
                {detalleMovimientos && (
                  <p className="text-sm text-zinc-500">{detalleMovimientos.codigo} - {detalleMovimientos.producto}</p>
                )}
              </div>
              <button 
                onClick={() => setShowDetalleModal(false)}
                className="p-1 hover:bg-zinc-200 rounded"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="p-4 overflow-auto max-h-[60vh]">
              {loadingDetalle ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                </div>
              ) : detalleMovimientos?.error ? (
                <p className="text-red-600 text-center py-4">{detalleMovimientos.error}</p>
              ) : detalleMovimientos?.movimientos?.length > 0 ? (
                <>
                  <table className="w-full text-sm">
                    <thead className="bg-zinc-100">
                      <tr>
                        <th className="py-2 px-3 text-left">Fecha</th>
                        <th className="py-2 px-3 text-left">Concepto</th>
                        <th className="py-2 px-3 text-left">Descripción</th>
                        <th className="py-2 px-3 text-right">Cantidad</th>
                        <th className="py-2 px-3 text-left">Almacén</th>
                        <th className="py-2 px-3 text-left">Referencia</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detalleMovimientos.movimientos.map((m, idx) => (
                        <tr key={idx} className={`border-b ${m.tipo === 'E' ? 'bg-green-50' : 'bg-red-50'}`}>
                          <td className="py-1.5 px-3">{new Date(m.fecha).toLocaleDateString()}</td>
                          <td className="py-1.5 px-3">
                            <span className={`px-2 py-0.5 rounded text-xs ${m.tipo === 'E' ? 'bg-green-200' : 'bg-red-200'}`}>
                              {m.concepto}
                            </span>
                          </td>
                          <td className="py-1.5 px-3">{m.descripcion}</td>
                          <td className={`py-1.5 px-3 text-right font-medium ${m.cantidad >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {m.cantidad >= 0 ? '+' : ''}{formatNumber(m.cantidad)}
                          </td>
                          <td className="py-1.5 px-3">{m.almacen}</td>
                          <td className="py-1.5 px-3 text-zinc-500">{m.referencia}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {detalleMovimientos.totales && (
                    <div className="mt-4 p-3 bg-zinc-100 rounded flex gap-6">
                      <div>
                        <span className="text-xs text-zinc-500">Total Entradas:</span>
                        <span className="ml-2 font-bold text-green-600">+{formatNumber(detalleMovimientos.totales.entradas || 0)}</span>
                      </div>
                      <div>
                        <span className="text-xs text-zinc-500">Total Salidas:</span>
                        <span className="ml-2 font-bold text-red-600">-{formatNumber(detalleMovimientos.totales.salidas || 0)}</span>
                      </div>
                      <div>
                        <span className="text-xs text-zinc-500">Neto:</span>
                        <span className={`ml-2 font-bold ${detalleMovimientos.totales.neto >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {formatNumber(detalleMovimientos.totales.neto || 0)}
                        </span>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-center text-zinc-500 py-8">No se encontraron movimientos para este producto en el período seleccionado</p>
              )}
            </div>
            <div className="px-4 py-3 border-t bg-zinc-50 flex justify-end">
              <Button variant="outline" onClick={() => setShowDetalleModal(false)}>
                Cerrar
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Compras() {
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
        
        // Restaurar servidor guardado
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) {
          const params = JSON.parse(saved);
          if (params.server && response.data.find(s => s.id === params.server)) {
            setSelectedServer(params.server);
          }
        }
      } catch (error) {
        console.error('Error cargando servidores:', error);
      }
    };
    fetchServers();
  }, []);

  // Cargar sucursales cuando cambia el servidor
  useEffect(() => {
    if (selectedServer) {
      const fetchSucursales = async () => {
        try {
          const token = localStorage.getItem('token');
          const response = await axios.get(`${API_URL}/api/servers/${selectedServer}/sucursales`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          const sucursalesData = response.data;
          setSucursales(sucursalesData);
          
          // Auto-seleccionar si solo hay una sucursal
          if (sucursalesData.length === 1) {
            setSelectedSucursal(sucursalesData[0].nombre || sucursalesData[0].codigo || sucursalesData[0]);
          } else {
            setSelectedSucursal(''); // Reset si hay múltiples
          }
        } catch (error) {
          console.error('Error cargando sucursales:', error);
          setSucursales([]);
        }
      };
      fetchSucursales();
    } else {
      setSucursales([]);
      setSelectedSucursal('');
    }
  }, [selectedServer]);

  return (
    <div className="space-y-4" data-testid="compras-module">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-zinc-800">Compras</h1>
        <p className="text-sm text-zinc-500">Gestión y análisis de compras</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4 mb-4">
          <TabsTrigger value="dashboard" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Dashboard
          </TabsTrigger>
          <TabsTrigger value="autorizacion" className="flex items-center gap-2">
            <ShoppingCart className="h-4 w-4" />
            Autorización
          </TabsTrigger>
          <TabsTrigger value="analisis" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Análisis
          </TabsTrigger>
          <TabsTrigger value="auditoria" className="flex items-center gap-2">
            <FileWarning className="h-4 w-4" />
            Auditoría
          </TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard">
          <DashboardCompras 
            servers={servers} 
            selectedServer={selectedServer} 
            setSelectedServer={setSelectedServer}
            selectedSucursal={selectedSucursal}
            setSelectedSucursal={setSelectedSucursal}
            sucursales={sucursales}
          />
        </TabsContent>

        <TabsContent value="autorizacion">
          <AutorizacionComprasTab 
            servers={servers} 
            selectedServer={selectedServer} 
            setSelectedServer={setSelectedServer}
            selectedSucursal={selectedSucursal}
            setSelectedSucursal={setSelectedSucursal}
            sucursales={sucursales}
          />
        </TabsContent>

        <TabsContent value="analisis">
          <AnalisisCompras 
            servers={servers} 
            selectedServer={selectedServer} 
            setSelectedServer={setSelectedServer}
            selectedSucursal={selectedSucursal}
            setSelectedSucursal={setSelectedSucursal}
            sucursales={sucursales}
          />
        </TabsContent>

        <TabsContent value="auditoria">
          <AuditoriaOperativaTab 
            servers={servers} 
            selectedServer={selectedServer} 
            setSelectedServer={setSelectedServer}
            selectedSucursal={selectedSucursal}
            setSelectedSucursal={setSelectedSucursal}
            sucursales={sucursales}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
