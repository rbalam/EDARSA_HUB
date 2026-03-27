import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Checkbox } from '../components/ui/checkbox';
import { toast } from 'sonner';
import { Loader2, ShoppingCart, Package, TrendingUp, AlertTriangle, Download, AlertCircle, Calendar, Edit3, FileText, RefreshCw } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const formatNumber = (num) => {
  if (num === null || num === undefined) return '-';
  return new Intl.NumberFormat('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(num);
};

const formatCurrency = (num) => {
  if (num === null || num === undefined) return '-';
  return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(num);
};

export default function AutorizacionCompras() {
  const [servers, setServers] = useState([]);
  const [selectedServer, setSelectedServer] = useState('');
  const [serverData, setServerData] = useState(null);
  const [sucursales, setSucursales] = useState([]);
  const [almacenes, setAlmacenes] = useState([]);
  const [selectedSucursal, setSelectedSucursal] = useState('');
  const [selectedAlmacenes, setSelectedAlmacenes] = useState([]);
  const [todosAlmacenes, setTodosAlmacenes] = useState(false);
  
  // Fechas y período
  const [fechaInvFisico, setFechaInvFisico] = useState('');
  const [fechaFinPeriodo, setFechaFinPeriodo] = useState(new Date().toISOString().split('T')[0]);
  const [diasInventario, setDiasInventario] = useState(10);
  const [metodoCalculo, setMetodoCalculo] = useState('consumo');
  
  // Inventarios físicos disponibles
  const [inventariosFisicos, setInventariosFisicos] = useState([]);
  const [folioInvFisico, setFolioInvFisico] = useState('');
  
  // Pedidos para comparar
  const [pedidosVigentes, setPedidosVigentes] = useState([]);
  const [folioPedidoComparar, setFolioPedidoComparar] = useState('');
  
  // Resultados
  const [loading, setLoading] = useState(false);
  const [pedidoData, setPedidoData] = useState([]);
  const [resumen, setResumen] = useState(null);
  const [infoInventario, setInfoInventario] = useState(null);
  const [editingRow, setEditingRow] = useState(null);

  // Cargar servidores al iniciar
  useEffect(() => {
    const fetchServers = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`${API_URL}/api/servers`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setServers(response.data);
      } catch (error) {
        console.error('Error cargando servidores:', error);
        toast.error('Error al cargar servidores');
      }
    };
    fetchServers();
  }, []);

  // Cargar sucursales cuando cambia el servidor
  useEffect(() => {
    if (selectedServer) {
      const server = servers.find(s => s.id === selectedServer);
      setServerData(server);
      fetchSucursales(selectedServer);
      setSelectedSucursal('');
      setSelectedAlmacenes([]);
      setPedidoData([]);
      setInventariosFisicos([]);
      setPedidosVigentes([]);
    }
  }, [selectedServer, servers]);

  // Cargar almacenes e inventarios cuando cambia la sucursal
  useEffect(() => {
    if (selectedServer && selectedSucursal) {
      fetchAlmacenes(selectedServer, selectedSucursal);
      fetchInventariosFisicos(selectedServer, selectedSucursal);
      fetchPedidosVigentes(selectedServer, selectedSucursal);
      setSelectedAlmacenes([]);
      setPedidoData([]);
    }
  }, [selectedServer, selectedSucursal]);

  const fetchSucursales = async (serverId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/servers/${serverId}/sucursales`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSucursales(response.data);
    } catch (error) {
      console.error('Error cargando sucursales:', error);
      toast.error('Error al cargar sucursales');
    }
  };

  const fetchAlmacenes = async (serverId, sucursal) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/servers/${serverId}/almacenes?sucursal=${encodeURIComponent(sucursal)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      // Eliminar duplicados por nombre
      const unique = [...new Map(response.data.map(a => [a.nombre, a])).values()];
      setAlmacenes(unique);
    } catch (error) {
      console.error('Error cargando almacenes:', error);
      toast.error('Error al cargar almacenes');
    }
  };

  const fetchInventariosFisicos = async (serverId, sucursal) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/compras/inventarios-fisicos/${serverId}?sucursal=${encodeURIComponent(sucursal)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setInventariosFisicos(response.data);
      // Seleccionar el más reciente por defecto
      if (response.data.length > 0) {
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
      setPedidosVigentes(response.data);
    } catch (error) {
      console.error('Error cargando pedidos vigentes:', error);
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
  };

  const handleTodosAlmacenes = (checked) => {
    setTodosAlmacenes(checked);
    if (checked) {
      setSelectedAlmacenes(['TODOS']);
    } else {
      setSelectedAlmacenes([]);
    }
  };

  const calcularPedido = async () => {
    if (!selectedServer || !selectedSucursal || (selectedAlmacenes.length === 0 && !todosAlmacenes)) {
      toast.error('Selecciona servidor, sucursal y al menos un almacén');
      return;
    }

    if (!fechaInvFisico || !fechaFinPeriodo) {
      toast.error('Selecciona las fechas del período de análisis');
      return;
    }

    setLoading(true);
    setPedidoData([]);
    setResumen(null);
    setInfoInventario(null);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API_URL}/api/compras/calculo-pedido`, {
        server_id: selectedServer,
        sucursal: selectedSucursal,
        almacenes: todosAlmacenes ? ['TODOS'] : selectedAlmacenes,
        fecha_inventario_fisico: fechaInvFisico,
        fecha_fin_periodo: fechaFinPeriodo,
        dias_inventario: parseInt(diasInventario),
        metodo_calculo: metodoCalculo,
        folio_inventario_fisico: folioInvFisico || null,
        folio_pedido_comparar: (folioPedidoComparar && folioPedidoComparar !== '__none__') ? folioPedidoComparar : null
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setPedidoData(response.data.data);
      
      // Guardar info del inventario físico
      setInfoInventario({
        tieneInventarioFisico: response.data.tiene_inventario_fisico,
        fechaInventarioFisico: response.data.fecha_inventario_fisico,
        folioInventarioFisico: response.data.folio_inventario_fisico,
        productosSinInventario: response.data.productos_sin_inventario,
        esBodega: response.data.es_bodega,
        almacenes: response.data.almacenes,
        diasPeriodo: response.data.dias_periodo,
        comparandoConPedido: response.data.comparando_con_pedido,
        metodoCalculo: response.data.metodo_calculo
      });
      
      // Calcular resumen
      const data = response.data.data;
      const totalProductos = data.length;
      const productosAPedir = data.filter(p => p.Cantidad_Pedir > 0).length;
      const costoTotalPedido = data.reduce((sum, p) => sum + (p.Costo_Pedido || 0), 0);
      const productosStockBajo = data.filter(p => p.Dias_Inventario < 3 && p.Dias_Inventario !== 999).length;
      const productosSinInvFisico = data.filter(p => p.Sin_Inventario_Fisico).length;
      const productosConDiferencia = data.filter(p => p.Diferencia_Pedido !== null && p.Diferencia_Pedido !== 0).length;

      setResumen({
        totalProductos,
        productosAPedir,
        costoTotalPedido,
        productosStockBajo,
        productosSinInvFisico,
        productosConDiferencia,
        parametros: response.data.parametros
      });

      toast.success(`Cálculo completado: ${response.data.count} productos`);
    } catch (error) {
      console.error('Error calculando pedido:', error);
      toast.error(error.response?.data?.detail || 'Error al calcular pedido');
    } finally {
      setLoading(false);
    }
  };

  // Función para actualizar existencia manual y recalcular
  const actualizarExistenciaManual = (codigo, valor) => {
    const nuevoValor = parseFloat(valor) || 0;
    
    setPedidoData(prev => prev.map(row => {
      if (row.Codigo === codigo) {
        const invTeorico = nuevoValor + row.Movimientos_Periodo - row.Consumos_Periodo;
        let cantidadPedir;
        if (metodoCalculo === 'stock' && row.Stock_Maximo > 0) {
          cantidadPedir = Math.max(0, row.Stock_Maximo - invTeorico);
        } else {
          const consumoEsperado = row.Promedio_Diario * diasInventario;
          cantidadPedir = Math.max(0, consumoEsperado - invTeorico);
        }
        const diasInv = row.Promedio_Diario > 0 ? invTeorico / row.Promedio_Diario : 999;
        return {
          ...row,
          Inventario_Fisico: nuevoValor,
          Inventario_Teorico: invTeorico,
          Cantidad_Pedir: cantidadPedir,
          Costo_Pedido: cantidadPedir * row.Costo_Unitario,
          Dias_Inventario: diasInv < 999 ? diasInv : 999,
          Sin_Inventario_Fisico: false
        };
      }
      return row;
    }));
    
    setEditingRow(null);
  };

  const exportarExcel = () => {
    if (pedidoData.length === 0) {
      toast.error('No hay datos para exportar');
      return;
    }
    // TODO: Implementar exportación
    toast.info('Exportación en desarrollo');
  };

  return (
    <div className="space-y-6" data-testid="compras-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-800">Autorización de Compras</h1>
          <p className="text-sm text-zinc-500">Calcula pedidos sugeridos y compara con requisiciones del sistema</p>
        </div>
      </div>

      {/* Parámetros de Cálculo */}
      <Card className="border border-zinc-200 shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <ShoppingCart className="h-5 w-5 text-blue-600" />
            Parámetros del Cálculo
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Fila 1: Servidor, Sucursal */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Servidor</Label>
              <Select value={selectedServer} onValueChange={setSelectedServer}>
                <SelectTrigger data-testid="server-select">
                  <SelectValue placeholder="Seleccionar servidor" />
                </SelectTrigger>
                <SelectContent>
                  {servers.map(server => (
                    <SelectItem key={server.id} value={server.id}>
                      {server.name} ({server.system_type})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Sucursal</Label>
              <Select value={selectedSucursal} onValueChange={setSelectedSucursal} disabled={!selectedServer}>
                <SelectTrigger data-testid="sucursal-select">
                  <SelectValue placeholder="Seleccionar sucursal" />
                </SelectTrigger>
                <SelectContent>
                  {sucursales.map(suc => (
                    <SelectItem key={suc.codigo || suc.nombre} value={suc.nombre}>
                      {suc.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Fila 2: Almacenes (multi-select) */}
          {almacenes.length > 0 && (
            <div className="space-y-2">
              <Label>Almacenes</Label>
              <div className="flex flex-wrap gap-3 p-3 border rounded-md bg-zinc-50">
                <div className="flex items-center gap-2">
                  <Checkbox 
                    id="todos-almacenes"
                    checked={todosAlmacenes}
                    onCheckedChange={handleTodosAlmacenes}
                  />
                  <label htmlFor="todos-almacenes" className="text-sm font-medium">TODOS</label>
                </div>
                <div className="w-px h-6 bg-zinc-300" />
                {almacenes.map(alm => (
                  <div key={alm.nombre} className="flex items-center gap-2">
                    <Checkbox 
                      id={`alm-${alm.nombre}`}
                      checked={selectedAlmacenes.includes(alm.nombre)}
                      onCheckedChange={() => handleAlmacenToggle(alm.nombre)}
                      disabled={todosAlmacenes}
                    />
                    <label htmlFor={`alm-${alm.nombre}`} className="text-sm">{alm.nombre}</label>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Fila 3: Período de Análisis */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label>Inventario Físico (Folio)</Label>
              <Select value={folioInvFisico} onValueChange={(val) => {
                setFolioInvFisico(val);
                const inv = inventariosFisicos.find(i => i.folio === val);
                if (inv) setFechaInvFisico(inv.fecha.split('T')[0]);
              }} data-testid="folio-inv-select">
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar folio" />
                </SelectTrigger>
                <SelectContent>
                  {inventariosFisicos.map(inv => (
                    <SelectItem key={inv.folio} value={inv.folio}>
                      {inv.folio} - {new Date(inv.fecha).toLocaleDateString('es-MX')} ({inv.almacen})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Fecha Inv. Físico (Inicio)</Label>
              <Input
                type="date"
                value={fechaInvFisico}
                onChange={(e) => setFechaInvFisico(e.target.value)}
                data-testid="fecha-inv-fisico"
              />
            </div>

            <div className="space-y-2">
              <Label>Fecha Fin Período</Label>
              <Input
                type="date"
                value={fechaFinPeriodo}
                onChange={(e) => setFechaFinPeriodo(e.target.value)}
                data-testid="fecha-fin-periodo"
              />
            </div>

            <div className="space-y-2">
              <Label>Días Inventario a Comprar</Label>
              <Input
                type="number"
                min="1"
                max="90"
                value={diasInventario}
                onChange={(e) => setDiasInventario(e.target.value)}
                data-testid="dias-inventario"
              />
            </div>
          </div>

          {/* Fila 4: Método y Pedido a Comparar */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Método de Cálculo</Label>
              <Select value={metodoCalculo} onValueChange={setMetodoCalculo} data-testid="metodo-select">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="consumo">Por Consumo Promedio</SelectItem>
                  <SelectItem value="stock">Por Stock Máx/Mín</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Comparar con Pedido/Requisición</Label>
              <Select value={folioPedidoComparar} onValueChange={setFolioPedidoComparar} data-testid="pedido-comparar-select">
                <SelectTrigger>
                  <SelectValue placeholder="(Opcional) Seleccionar pedido" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__none__">Sin comparar</SelectItem>
                  {pedidosVigentes.map(ped => (
                    <SelectItem key={`${ped.tipo}-${ped.folio}`} value={ped.folio}>
                      [{ped.tipo}] {ped.folio} - {new Date(ped.fecha).toLocaleDateString('es-MX')} - {ped.proveedor || 'Sin proveedor'}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-end gap-2">
              <Button 
                onClick={calcularPedido} 
                disabled={loading || !selectedServer || !selectedSucursal || (selectedAlmacenes.length === 0 && !todosAlmacenes)}
                className="flex-1"
                data-testid="btn-calcular"
              >
                {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
                Calcular Pedido
              </Button>
              <Button variant="outline" onClick={exportarExcel} disabled={pedidoData.length === 0} data-testid="btn-exportar">
                <Download className="h-4 w-4 mr-2" />
                Excel
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Resumen KPIs */}
      {resumen && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
          <Card className="border border-zinc-200">
            <CardContent className="py-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-zinc-500">Total Productos</p>
                  <p className="text-xl font-bold text-zinc-800">{resumen.totalProductos}</p>
                </div>
                <Package className="h-6 w-6 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="border border-zinc-200">
            <CardContent className="py-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-zinc-500">A Pedir</p>
                  <p className="text-xl font-bold text-green-600">{resumen.productosAPedir}</p>
                </div>
                <ShoppingCart className="h-6 w-6 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="border border-zinc-200">
            <CardContent className="py-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-zinc-500">Costo Total</p>
                  <p className="text-lg font-bold text-zinc-800">{formatCurrency(resumen.costoTotalPedido)}</p>
                </div>
                <TrendingUp className="h-6 w-6 text-purple-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="border border-zinc-200">
            <CardContent className="py-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-zinc-500">Stock Bajo</p>
                  <p className="text-xl font-bold text-red-600">{resumen.productosStockBajo}</p>
                </div>
                <AlertTriangle className="h-6 w-6 text-red-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card className={`border ${resumen.productosSinInvFisico > 0 ? 'border-orange-300 bg-orange-50' : 'border-zinc-200'}`}>
            <CardContent className="py-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-zinc-500">Sin Inv. Físico</p>
                  <p className={`text-xl font-bold ${resumen.productosSinInvFisico > 0 ? 'text-orange-600' : 'text-zinc-400'}`}>
                    {resumen.productosSinInvFisico}
                  </p>
                </div>
                <AlertCircle className={`h-6 w-6 ${resumen.productosSinInvFisico > 0 ? 'text-orange-500' : 'text-zinc-300'}`} />
              </div>
            </CardContent>
          </Card>

          {folioPedidoComparar && (
            <Card className={`border ${resumen.productosConDiferencia > 0 ? 'border-blue-300 bg-blue-50' : 'border-zinc-200'}`}>
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-zinc-500">Con Diferencia</p>
                    <p className={`text-xl font-bold ${resumen.productosConDiferencia > 0 ? 'text-blue-600' : 'text-zinc-400'}`}>
                      {resumen.productosConDiferencia}
                    </p>
                  </div>
                  <FileText className={`h-6 w-6 ${resumen.productosConDiferencia > 0 ? 'text-blue-500' : 'text-zinc-300'}`} />
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
      
      {/* Alerta de información del inventario */}
      {infoInventario && (
        <Card className={`border ${infoInventario.tieneInventarioFisico ? 'border-blue-200 bg-blue-50' : 'border-orange-200 bg-orange-50'}`}>
          <CardContent className="py-3">
            <div className="flex items-center gap-3 flex-wrap">
              <Calendar className={`h-5 w-5 ${infoInventario.tieneInventarioFisico ? 'text-blue-600' : 'text-orange-600'}`} />
              <div className="flex-1">
                <p className="text-sm">
                  <span className="font-semibold">Período:</span> {infoInventario.fechaInventarioFisico} al {fechaFinPeriodo} ({infoInventario.diasPeriodo} días)
                  {infoInventario.folioInventarioFisico && <span className="ml-2 text-zinc-600">| Folio: {infoInventario.folioInventarioFisico}</span>}
                  {infoInventario.esBodega && <span className="ml-2 px-2 py-0.5 bg-blue-200 rounded text-xs">BODEGA</span>}
                  {infoInventario.comparandoConPedido && <span className="ml-2 px-2 py-0.5 bg-green-200 rounded text-xs">vs Pedido {infoInventario.comparandoConPedido}</span>}
                  <span className="ml-2 px-2 py-0.5 bg-zinc-200 rounded text-xs">
                    {infoInventario.metodoCalculo === 'stock' ? 'Stock Máx/Mín' : 'Consumo Promedio'}
                  </span>
                </p>
                <p className="text-xs text-zinc-600">Almacenes: {infoInventario.almacenes?.join(', ') || '-'}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabla de Resultados */}
      {pedidoData.length > 0 && (
        <Card className="border border-zinc-200 shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-semibold">Pedido Sugerido</CardTitle>
              <span className="text-sm text-zinc-600">
                {pedidoData.filter(p => p.Cantidad_Pedir > 0).length} productos a pedir
              </span>
            </div>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border border-zinc-200 max-h-[500px] overflow-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 z-10 bg-zinc-200">
                  <tr className="border-b-2 border-zinc-400">
                    <th className="text-xs uppercase font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-left">Código</th>
                    <th className="text-xs uppercase font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-left">Producto</th>
                    <th className="text-xs uppercase font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-left">Familia</th>
                    <th className="text-xs uppercase font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-right">Inv. Físico</th>
                    <th className="text-xs uppercase font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-right">Movimientos</th>
                    <th className="text-xs uppercase font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-right">Consumos</th>
                    <th className="text-xs uppercase font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-right">Inv. Teórico</th>
                    <th className="text-xs uppercase font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-right">Prom. Diario</th>
                    <th className="text-xs uppercase font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-right">Días Inv.</th>
                    <th className="text-xs uppercase font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-right">Cant. Pedir</th>
                    <th className="text-xs uppercase font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-right">Costo Pedido</th>
                    {folioPedidoComparar && (
                      <>
                        <th className="text-xs uppercase font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-right">Pedido Exist.</th>
                        <th className="text-xs uppercase font-semibold text-zinc-700 whitespace-nowrap bg-zinc-200 py-3 px-2 text-right">Diferencia</th>
                      </>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {pedidoData.map((row, idx) => {
                    const necesitaPedir = row.Cantidad_Pedir > 0;
                    const stockCritico = row.Dias_Inventario < 3 && row.Dias_Inventario !== 999;
                    const sinInvFisico = row.Sin_Inventario_Fisico;
                    const isEditing = editingRow === row.Codigo;
                    const tieneDiferencia = row.Diferencia_Pedido !== null && row.Diferencia_Pedido !== 0;
                    
                    return (
                      <tr 
                        key={idx} 
                        className={`border-b hover:bg-zinc-50 
                          ${sinInvFisico ? 'bg-orange-50' : ''} 
                          ${necesitaPedir && !sinInvFisico ? 'bg-yellow-50' : ''} 
                          ${stockCritico && !sinInvFisico ? 'bg-red-50' : ''}`}
                        data-testid={`row-${row.Codigo}`}
                      >
                        <td className="py-2 px-2 font-mono text-xs">{row.Codigo}</td>
                        <td className="py-2 px-2 text-sm max-w-[200px] truncate" title={row.Producto}>{row.Producto}</td>
                        <td className="py-2 px-2 text-sm">{row.Familia}</td>
                        <td className="py-2 px-2 text-right">
                          {sinInvFisico ? (
                            isEditing ? (
                              <Input
                                type="number"
                                step="0.01"
                                className="w-20 h-7 text-xs text-right"
                                autoFocus
                                onBlur={(e) => actualizarExistenciaManual(row.Codigo, e.target.value)}
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter') {
                                    actualizarExistenciaManual(row.Codigo, e.target.value);
                                  } else if (e.key === 'Escape') {
                                    setEditingRow(null);
                                  }
                                }}
                                data-testid={`input-existencia-${row.Codigo}`}
                              />
                            ) : (
                              <button
                                onClick={() => setEditingRow(row.Codigo)}
                                className="flex items-center gap-1 text-orange-600 hover:text-orange-800 font-mono text-xs"
                                title="Clic para ingresar existencia"
                                data-testid={`btn-edit-${row.Codigo}`}
                              >
                                <Edit3 className="h-3 w-3" />
                                Ingresar
                              </button>
                            )
                          ) : (
                            <span className="font-mono">{formatNumber(row.Inventario_Fisico)}</span>
                          )}
                        </td>
                        <td className={`py-2 px-2 text-right font-mono ${row.Movimientos_Periodo > 0 ? 'text-green-700' : row.Movimientos_Periodo < 0 ? 'text-red-600' : ''}`}>
                          {formatNumber(row.Movimientos_Periodo)}
                        </td>
                        <td className="py-2 px-2 text-right font-mono text-red-600">{formatNumber(row.Consumos_Periodo)}</td>
                        <td className="py-2 px-2 text-right font-mono font-semibold">{formatNumber(row.Inventario_Teorico)}</td>
                        <td className="py-2 px-2 text-right font-mono">{formatNumber(row.Promedio_Diario)}</td>
                        <td className={`py-2 px-2 text-right font-mono font-semibold ${stockCritico ? 'text-red-600' : ''}`}>
                          {row.Dias_Inventario >= 999 ? '∞' : formatNumber(row.Dias_Inventario)}
                        </td>
                        <td className={`py-2 px-2 text-right font-mono font-bold ${necesitaPedir ? 'text-green-700' : 'text-zinc-400'}`}>
                          {formatNumber(row.Cantidad_Pedir)}
                        </td>
                        <td className="py-2 px-2 text-right font-mono">{formatCurrency(row.Costo_Pedido)}</td>
                        {folioPedidoComparar && (
                          <>
                            <td className="py-2 px-2 text-right font-mono text-blue-600">
                              {row.Cantidad_Pedido_Existente !== null ? formatNumber(row.Cantidad_Pedido_Existente) : '-'}
                            </td>
                            <td className={`py-2 px-2 text-right font-mono font-semibold ${tieneDiferencia ? (row.Diferencia_Pedido > 0 ? 'text-green-600' : 'text-red-600') : ''}`}>
                              {row.Diferencia_Pedido !== null ? (row.Diferencia_Pedido > 0 ? '+' : '') + formatNumber(row.Diferencia_Pedido) : '-'}
                            </td>
                          </>
                        )}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
